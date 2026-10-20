"""Catalog existing discovery nodes, variants and every snapshot link/image.

This is snapshot coverage, never a claim about live reachability or completeness.
"""

from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from src.model_discovery.cs50 import deterministic_id
from src.tools_lecture.cs50_manifest import load_fixture_manifest
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_lecture.select_cs50 import preview_course

HOSTS = frozenset({"cs50.harvard.edu", "cdn.cs50.net"})
CODE = frozenset({"py", "sql", "js", "css", "c", "h", "txt", "md"})
FORMATS = CODE | {"html", "pdf", "png", "jpg", "jpeg", "gif", "webp", "svg"}


def format_of(url, hint=None):
    suffix = Path(urlsplit(url).path).suffix.lower().lstrip(".")
    return hint or suffix or ("html" if urlsplit(url).path.endswith("/") else "unknown")


def official(url):
    p = urlsplit(url)
    return (
        p.scheme == "https"
        and p.hostname in HOSTS
        and not p.username
        and not p.password
        and p.port in (None, 443)
        and not p.query
    )


def capability(url, fmt):
    if not official(url):
        return "blocked", "external/unreviewed URL or non-HTTPS source"
    if fmt not in FORMATS:
        return (
            "unsupported",
            f"format {fmt}; media, archives and subtitle path remain separate",
        )
    return "supported", "direct official URL; reachability and license not checked"


def catalog(manifest):
    manifest = Path(manifest)
    fixtures = load_fixture_manifest(manifest)
    courses = discover_fixture_courses(manifest)
    rows = []
    for course, fixture in zip(courses, fixtures.courses, strict=True):
        lectures = preview_course(course).lectures
        by_section = {
            s.key: tuple(
                lecture.resource_id
                for lecture in lectures
                if s.key in lecture.section_keys
            )
            for s in course.sections
        }

        def append(
            resource_id,
            url,
            role,
            *,
            sections=(),
            parent=None,
            language=None,
            fmt=None,
            provenance=(),
            kind="candidate",
            variant_id=None,
            course=course,
            by_section=by_section,
        ):
            fmt = format_of(url, fmt)
            support, reason = capability(url, fmt)
            rows.append(
                dict(
                    course_id=course.course_id,
                    section_keys=list(sections),
                    lecture_ids=sorted(
                        {lecture for s in sections for lecture in by_section.get(s, ())}
                    ),
                    resource_id=resource_id,
                    parent_resource_id=parent,
                    role=role,
                    format=fmt,
                    original_url=url,
                    language=language,
                    reference_kind=kind,
                    variant_id=variant_id,
                    download_capability=support,
                    parse_capability=(
                        "partial"
                        if support == "supported" and fmt in {"html", "pdf", "svg"}
                        else support
                    ),
                    reason=reason,
                    content_dependencies=[],
                    license_status="not_assessed",
                    provenance=list(provenance),
                )
            )

        for resource in course.resources:
            append(
                resource.resource_id,
                str(resource.original_url),
                resource.role.value,
                sections=resource.section_keys,
                parent=resource.parent_resource_id,
                language=resource.language,
                fmt=resource.format,
                provenance=[p.model_dump(mode="json") for p in resource.provenance],
            )
            for v in resource.variants:
                append(
                    resource.resource_id,
                    str(v.original_url),
                    resource.role.value,
                    sections=resource.section_keys,
                    parent=resource.parent_resource_id,
                    language=v.language,
                    fmt=v.format,
                    kind="variant",
                    variant_id=v.variant_id,
                    provenance=[p.model_dump(mode="json") for p in v.provenance],
                )
        for page in fixture.pages:
            soup = BeautifulSoup(
                (manifest.parent / page.file).read_bytes(), "html.parser"
            )
            sections = tuple(
                s.key for s in course.sections if str(s.original_url) == str(page.url)
            )
            # Notes/assignments use already proven discovery URL->section bindings.
            if not sections:
                sections = tuple(
                    sorted(
                        {
                            s
                            for r in course.resources
                            if str(r.original_url) == str(page.url)
                            for s in r.section_keys
                        }
                    )
                )
            for order, tag in enumerate(soup.select("a[href], img[src]")):
                raw_reference = tag.get("href", tag.get("src"))
                url = urljoin(str(page.url), raw_reference)
                append(
                    deterministic_id(
                        "snapshot_ref", course.course_id, page.file, str(order)
                    ),
                    url,
                    "image_reference"
                    if tag.name == "img"
                    else "unclassified_reference",
                    sections=sections,
                    kind="snapshot_reference",
                    provenance=[
                        dict(
                            original_url=str(page.url),
                            fixture_file=page.file,
                            locator=f"{tag.name}[reference-order={order}]",
                            fixture_sha256=page.sha256,
                        )
                    ],
                )
                rows[-1]["raw_reference"] = raw_reference
                if "_files/" in raw_reference or raw_reference.startswith(
                    ("file:", "blob:", "data:")
                ):
                    rows[-1]["download_capability"] = "blocked"
                    rows[-1]["parse_capability"] = (
                        "partial" if raw_reference.startswith("data:") else "blocked"
                    )
                    rows[-1]["reason"] = (
                        "Browser-local/inline reference; no proven remote URL"
                    )
    candidates = {}
    for row in rows:
        if row["reference_kind"] == "candidate":
            candidates.setdefault((row["course_id"], row["original_url"]), []).append(
                row
            )
    for row in rows:
        if row["reference_kind"] != "snapshot_reference":
            continue
        parents = candidates.get(
            (row["course_id"], row["provenance"][0]["original_url"]), []
        )
        if len(parents) == 1:
            row["parent_resource_id"] = parents[0]["resource_id"]
            if row["role"] == "image_reference":
                parents[0]["content_dependencies"].append(row["resource_id"])
    return dict(
        schema_version=1,
        coverage="local_snapshot_only",
        courses=[c.model_dump(mode="json") for c in courses],
        references=rows,
    )


def coverage_report(data):
    lines = [
        "# CS50 materials: Snapshot inventory and gaps",
        "",
        "No live crawl, material downloads or license clearance. Raw anchor/image references include",
        "navigation, external tools and fragments; they are references, not unique downloadable files.",
        "",
        "| Course | Sections | Candidates | Media variants | Raw link/image occurrences | Eligible references |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    role_details = []
    for course in data["courses"]:
        rows = [r for r in data["references"] if r["course_id"] == course["course_id"]]
        counts = Counter(r["reference_kind"] for r in rows)
        lines.append(
            f"| {course['course_id']} | {len(course['sections'])} | {counts['candidate']} | "
            f"{counts['variant']} | {counts['snapshot_reference']} | "
            f"{sum(r['download_capability'] == 'supported' for r in rows)} |"
        )
        roles = Counter(r["role"] for r in rows if r["reference_kind"] == "candidate")
        role_details += [
            "",
            f"{course['course_id']} discovered roles: "
            + ", ".join(f"{k}={v}" for k, v in sorted(roles.items())),
            "",
        ]
    return "\n".join(lines + role_details) + "\n"
