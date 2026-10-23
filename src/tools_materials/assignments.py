"""Shared one-level assignment derivation; no URL acquisition or execution."""

from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup

from src.job_control.catalog import read_file, safe_path
from src.model_discovery.cs50 import Provenance, ResourceCandidate
from src.model_materials.assignments import AssignmentSnapshot
from src.model_materials.materials import MaterialResource
from src.tools_materials.parse_html import dom_path


def children(selected, parents, pages, week):
    """The original B5 identity/DOM contract, including first-occurrence order."""
    selected, parent_ids, observed = list(selected), {}, []
    for parent in parents:
        base_path = urlsplit(parent.original_url).path
        for page, raw in pages:
            url = str(page.url)
            if page.role != "assignment" or not url.startswith(parent.original_url):
                continue
            soup = BeautifulSoup(raw, "html.parser")
            main = soup.find("main")
            if main is None:
                continue
            observed.append(page.file)
            candidates = []
            # The manifest URL itself proves the existence of a supplied child page.
            if url != parent.original_url:
                candidates.append((url, main.find("h1") or main))
            candidates.extend(
                (urldefrag(urljoin(url, str(a["href"])))[0], a)
                for a in main.select("a[href]")
            )
            for child_url, node in candidates:
                parsed = urlsplit(child_url)
                tail = parsed.path.removeprefix(base_path).strip("/")
                if (
                    (parsed.scheme, parsed.netloc) != ("https", "cs50.harvard.edu")
                    or parsed.query
                    or not parsed.path.startswith(base_path)
                    or not tail
                    or "/" in tail
                    or not parsed.path.endswith("/")
                ):
                    continue
                if node.find_parent(["nav", "aside", "footer"]) is not None:
                    continue
                evidence = Provenance(
                    original_url=url,
                    fixture_file=page.file,
                    locator=dom_path(node),
                    context_path=(
                        f"Week {week}",
                        "Problem Set",
                        node.get_text(" ", strip=True),
                    ),
                )
                matches = [
                    b
                    for b in selected
                    if b.original_url == child_url
                    and b.role == "problem_set"
                    and b.variant_id is None
                ]
                if matches:
                    binding = matches[0]
                    resource = binding.resource.model_copy(
                        update={
                            "provenance": tuple(
                                dict.fromkeys((*binding.resource.provenance, evidence))
                            )
                        }
                    )
                    # Provenance models contain no mutable data; de-duplicate by value below.
                    selected[selected.index(binding)] = binding.model_copy(
                        update={"resource": resource}
                    )
                else:
                    resource = ResourceCandidate(
                        course_id=parent.resource.course_id,
                        role="problem_set",
                        original_url=child_url,
                        title=node.get_text(" ", strip=True) or child_url,
                        section_keys=(week,),
                        parent_resource_id=parent.source_id,
                        format="html",
                        provenance=(evidence,),
                    )
                    binding = MaterialResource(
                        resource=resource,
                        lecture_ids=parent.lecture_ids,
                        original_url=child_url,
                        format="html",
                        role="problem_set",
                        source_origin=parent.source_origin,
                    )
                    selected.append(binding)
                parent_ids.setdefault(binding.material_id, set()).add(parent.source_id)
    return selected, parent_ids, observed


def extend(plan, manifest, snapshots):
    """Opt-in only: add children proved by at most eight pinned root overviews."""
    import hashlib
    import json

    manifest = safe_path(Path(manifest))
    snapshots = tuple(
        AssignmentSnapshot.model_validate_json(s.model_dump_json())
        if isinstance(s, AssignmentSnapshot)
        else AssignmentSnapshot.model_validate(s)
        for s in snapshots
    )
    if not 1 <= len(snapshots) <= 8 or any(
        len({getattr(s, name) for s in snapshots}) != len(snapshots)
        for name in ("file", "path", "url")
    ):
        raise ValueError("Explicit unique bounded assignment snapshots required")
    data = json.loads(read_file(manifest, 1048576))
    declared = {p["file"]: p for c in data["courses"] for p in c["pages"]}
    selected = list(plan.materials)
    for snapshot in snapshots:
        if not snapshot.path.is_absolute() or snapshot.file == manifest.name:
            raise ValueError(
                "Explicit absolute overview path and distinct label required"
            )
        if snapshot.file in declared:
            page = declared[snapshot.file]
            if (
                snapshot.path != safe_path(manifest.parent, snapshot.file)
                or str(snapshot.url) != page["url"]
                or page["role"] != "assignment"
                or snapshot.sha256 != page.get("sha256")
            ):
                raise ValueError("Assignment label collides with declared snapshot")
        parents = [
            b
            for b in plan.materials
            if b.role == "problem_set"
            and b.original_url == str(snapshot.url)
            and b.resource.parent_resource_id is None
            and b.variant_id is None
        ]
        if len(parents) != 1 or len(parents[0].resource.section_keys) != 1:
            raise ValueError("Overview must match one proven course/week parent")
        raw = read_file(safe_path(snapshot.path), 1048576)
        if hashlib.sha256(raw).hexdigest() != snapshot.sha256:
            raise ValueError("Assignment snapshot hash mismatch")
        # B5 visits already declared detail fixtures before external exports.
        # Preserve that provenance ordering in the worker's reconstruction too.
        pages = []
        for name, page in declared.items():
            if page["role"] != "assignment" or not page["url"].startswith(
                parents[0].original_url
            ):
                continue
            content = read_file(safe_path(manifest.parent, name), 1048576)
            if hashlib.sha256(content).hexdigest() != page.get("sha256"):
                raise ValueError("Declared assignment snapshot hash mismatch")
            ref = AssignmentSnapshot(
                file=name,
                url=page["url"],
                sha256=page["sha256"],
                path=safe_path(manifest.parent, name),
            )
            pages.append((ref, content))
        if snapshot.file not in declared:
            pages.append((snapshot, raw))
        selected, _, _ = children(
            selected, parents, pages, parents[0].resource.section_keys[0]
        )
    courses = []
    for course in plan.courses:
        resources = {r.resource_id: r for r in course.resources}
        resources.update(
            {
                b.source_id: b.resource
                for b in selected
                if b.resource.course_id == course.course_id
            }
        )
        courses.append(
            course.model_copy(update=dict(resources=tuple(resources.values())))
        )
    return plan.model_copy(
        update=dict(materials=tuple(selected), courses=tuple(courses))
    )


def for_week(request):
    """Resolve only explicit supplied/manifest root snapshots; no reads of links."""
    from src.tools_lecture.cs50_manifest import load_fixture_manifest
    from src.tools_materials.processing import make_plan

    if not request.assignment_discovery:
        return ()
    manifest = load_fixture_manifest(request.manifest)
    graph = make_plan(request.manifest)
    parents = {
        b.original_url
        for b in graph.materials
        if b.resource.course_id == request.course_id
        and request.week in b.resource.section_keys
        and b.role == "problem_set"
        and b.resource.parent_resource_id is None
    }
    if hasattr(request, "profile"):
        section = next(s for s in request.profile.sections if s.key == request.week)
        parents &= {str(u) for u in section.assignment_roots}
    else:
        parents = {
            u for u in parents if urlsplit(u).path == f"/python/psets/{request.week}/"
        }
    refs = []
    for course in manifest.courses:
        if course.course_id != request.course_id:
            continue
        for page in course.pages:
            if page.role == "assignment" and str(page.url) in parents:
                if not page.sha256:
                    raise ValueError("Assignment overview must declare its hash")
                refs.append(
                    AssignmentSnapshot(
                        **page.model_dump(),
                        path=safe_path(request.manifest.parent, page.file),
                    )
                )
    for item in request.discovery_exports:
        if item.role == "assignment" and str(item.original_url) in parents:
            refs.append(
                AssignmentSnapshot(
                    file=item.label,
                    url=item.original_url,
                    path=item.path,
                    sha256=item.sha256,
                )
            )
    if not refs:
        raise ValueError("Assignment opt-in requires a pinned root overview")
    return tuple(refs)
