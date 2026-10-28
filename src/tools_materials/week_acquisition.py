"""Week orchestration over existing CS50 discovery, downloader and receipts.

Discovery reads an explicit bounded snapshot set. Acquisition has a separate,
hash-bound operator grant. No processing, transcriber, controller or queue starts.
"""

import hashlib
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote, urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup

from src.job_control.catalog import read_file
from src.job_control.models import fingerprint
from src.model_discovery.cs50 import ResourceCandidate, deterministic_id
from src.model_materials.acquisition import WeekInventory, WeekMaterial
from src.model_materials.materials import MaterialResource
from src.tools_lecture.cs50_manifest import COURSE_PATHS
from src.tools_lecture.prepare_cs50 import parse_week_page
from src.tools_materials.assignments import children
from src.tools_materials.capacity import check_capacity
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.inventory import format_of, official
from src.tools_materials.storage import artifact_root, locate, publish_bytes
from src.tools_materials.text_validation import validate_text_source

CONTENT = {"transcript": 1, "subtitles": 2, "audio": 3, "video": 4}
CONTAINERS = {"course", "week", "lecture", "shorts", "short", "problem_set", "task"}
SUCCESS = {"VERIFIED", "MANUAL_VERIFIED"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_url(url):
    p = urlsplit(url)
    decoded = unquote(unquote(p.path))
    if (
        not official(url)
        or p.fragment
        or "%" in decoded
        or "\\" in decoded
        or any(part in {".", ".."} for part in decoded.split("/"))
    ):
        raise PermissionError(
            "Official credential-free nontraversing HTTPS source required"
        )
    return url


def binding(row, inventory):
    checked_url(row.source_url)
    role = {
        "page": "reference",
        "task": "problem_set",
        "attachment": "starter_files",
        "video": "lecture_video",
    }.get(row.material_type, row.material_type)
    resource = ResourceCandidate(
        course_id=row.course_id,
        role=role,
        original_url=row.source_url,
        title=Path(urlsplit(row.source_url).path).name
        if inventory.schema_version == 2 and row.material_type == "source_code"
        else row.title,
        section_keys=(row.week_id,),
        language="en" if row.material_type in {"transcript", "subtitles"} else None,
    )
    return MaterialResource(
        resource=resource,
        original_url=row.source_url,
        role=role,
        format=row.source_format,
        language=resource.language,
        source_origin=inventory.source_origin,
        license_status="reviewed",
    )


def archive_path(row, inventory):
    return binding(row, inventory).material_id.split(":")[1] + "/raw/source"


def _offers(raw, url, course, week):
    """Normalize a Short detail page for the existing week/list role parser."""
    soup = BeautifulSoup(raw, "html.parser")
    main = soup.find("main")
    if main is None or main.find("h1") is None:
        raise ValueError("Discovery page requires main/h1")
    for tag in main.select("a[href], iframe[src]"):
        attr = "href" if tag.name == "a" else "src"
        tag[attr] = urljoin(url, tag[attr])
    if "/weeks/" in urlsplit(url).path:
        normalized, parser_url = str(soup), url
    else:
        heading = main.find("h1")
        heading.extract()
        normalized = (
            f"<main><h1>Week {week}</h1><ul><li>Lecture<ul>"
            + "".join(str(x) for x in main.contents)
            + "</ul></li></ul></main>"
        )
        parser_url = f"https://cs50.harvard.edu/{COURSE_PATHS[course]}/weeks/{week}/"
    return parse_week_page(normalized, parser_url, course_id=course)


def discover(
    pages,
    *,
    course_id="cs50_python",
    week_id="0",
    source_origin="official",
    limits=None,
    completion=False,
):
    """pages: URL -> bytes, already exported by the operator, never fetched here.

    completion=True opts into C08 automatic source files and index inspection.
    """
    from src.model_materials.acquisition import AcquisitionLimits

    limits = limits or AcquisitionLimits()
    if not pages or len(pages) > 64:
        raise ValueError("One to 64 explicit discovery pages required")
    for url, raw in pages.items():
        checked_url(url)
        if len(raw) > limits.html_bytes:
            raise ValueError("Discovery page exceeds HTML budget")
    root_url = f"https://cs50.harvard.edu/{COURSE_PATHS[course_id]}/weeks/{week_id}/"
    if root_url not in pages:
        raise ValueError("Week overview snapshot required")
    rows, expected, snapshots = {}, [], []

    def add(kind, title, parent=None, url=None, required=False, **extra):
        mid = deterministic_id(
            "week_material", course_id, week_id, parent or "", kind, url or title
        )
        if mid in rows:
            return rows[mid]
        if len(rows) >= limits.max_materials:
            raise ValueError("Week material count exceeds budget")
        row = WeekMaterial(
            course_id=course_id,
            week_id=week_id,
            section_id=f"{course_id}:week:{week_id}",
            material_id=mid,
            parent_material_id=parent,
            material_type=kind,
            title=title,
            source_url=url,
            required=required,
            **extra,
        )
        rows[mid] = row
        if required:
            expected.append(mid)
        return row

    def update(row, **extra):
        result = row.model_copy(update=extra)
        rows[row.material_id] = result
        return result

    def examine(container):
        page = add(
            "page",
            container.title,
            container.material_id,
            container.source_url,
            True,
            discovered_from=container.discovered_from or (container.source_url,),
            acquisition_status="APPROVAL_PENDING",
            acquisition_strategy="approved_html",
        )
        raw = pages.get(container.source_url)
        if raw is None:
            update(
                container,
                acquisition_status="MISSING",
                error_reason="Detail page snapshot missing",
            )
            return None
        soup = BeautifulSoup(raw, "html.parser")
        main = soup.find("main")
        if main is None or not main.find("h1"):
            update(
                container,
                acquisition_status="BLOCKED",
                error_reason="Missing main/h1; cannot prove discovery",
            )
            return None
        update(container, discovery_examined=True)
        snapshots.append(
            dict(url=container.source_url, sha256=sha(raw), bytes=len(raw))
        )
        update(
            page,
            title=main.h1.get_text(" ", strip=True),
            discovery_examined=True,
            description=main.get_text(" ", strip=True)[:4000],
        )
        return main

    course = add("course", course_id, discovery_examined=True)
    week = add("week", f"Week {week_id}", course.material_id, root_url, True)
    examine(week)
    lecture = add("lecture", f"Lecture {week_id}", week.material_id, root_url, True)
    shorts = add("shorts", "Shorts", week.material_id, discovery_examined=True)

    def assets(container, fragment):
        counts = {}
        for resource in fragment.resources:
            role = resource.role.value
            if role in {"short", "problem_set"}:
                continue
            if role == "lecture_video":
                offers = [
                    (
                        "video",
                        str(v.original_url),
                        v.format or format_of(str(v.original_url)),
                    )
                    for v in resource.variants
                ]
            else:
                offers = [
                    (
                        role,
                        str(resource.original_url),
                        resource.format or format_of(str(resource.original_url)),
                    )
                ]
            for kind, url, fmt in offers:
                if kind not in {
                    "transcript",
                    "subtitles",
                    "audio",
                    "video",
                    "slides",
                    "notes",
                    "source_code",
                }:
                    kind = "reference"
                counts[kind] = counts.get(kind, 0) + 1
                is_content = kind in CONTENT
                external = not official(url)
                row = add(
                    kind,
                    resource.title or kind,
                    container.material_id,
                    url,
                    False,
                    source_format=fmt,
                    discovered_from=(container.source_url,),
                    acquisition_status="REFERENCED_ONLY"
                    if external or kind in {"reference", "audio", "video"}
                    else "APPROVAL_PENDING",
                    acquisition_strategy="text_first"
                    if is_content
                    else "manual_only"
                    if kind == "source_code"
                    else "approved_file",
                    acquisition_priority=CONTENT.get(kind, 0),
                    alternative_group=container.material_id if is_content else None,
                    metadata={
                        "availability": "LINKED_UNPROBED",
                        "filename": Path(urlsplit(url).path).name,
                        "context": [list(p.context_path) for p in resource.provenance],
                    },
                )
                if kind == "source_code":
                    update(row, acquisition_status="REFERENCED_ONLY")
        for kind, priority in CONTENT.items():
            if not counts.get(kind):
                add(
                    kind,
                    kind + ": not offered",
                    container.material_id,
                    acquisition_status="NOT_APPLICABLE",
                    discovery_examined=True,
                    review_status="NOT_REQUIRED",
                    acquisition_strategy="text_first",
                    acquisition_priority=priority,
                    alternative_group=container.material_id,
                )
        for kind in ("notes", "slides"):
            offers = [
                r
                for r in rows.values()
                if r.parent_material_id == container.material_id
                and r.material_type == kind
            ]
            if not offers:
                add(
                    kind,
                    kind + ": not offered",
                    container.material_id,
                    acquisition_status="NOT_APPLICABLE",
                    discovery_examined=True,
                    review_status="NOT_REQUIRED",
                )
                continue
            canonical = min(
                offers,
                key=lambda r: (
                    not official(r.source_url),
                    r.source_format != ("pdf" if kind == "slides" else "html"),
                    r.source_url,
                ),
            )
            update(
                canonical,
                required=True,
                acquisition_status="APPROVAL_PENDING"
                if official(canonical.source_url)
                else "BLOCKED",
                error_reason=None
                if official(canonical.source_url)
                else "Offered only by external host; reviewed export required",
            )
            expected.append(canonical.material_id)
        code = [
            r
            for r in rows.values()
            if r.parent_material_id == container.material_id
            and r.material_type == "source_code"
        ]
        # One canonical manual package; all other official formats remain visible.
        if code and not completion:
            canonical = min(
                code,
                key=lambda r: (
                    {"zip": 0, "pdf": 1}.get(r.source_format, 2),
                    r.source_url,
                ),
            )
            if canonical.source_format in {"zip", "pdf", "py", "c", "sql"}:
                update(
                    canonical,
                    required=True,
                    manual_action_required=True,
                    selected=True,
                    acquisition_status="MANUAL_PENDING",
                )
                expected.append(canonical.material_id)
            else:
                update(
                    canonical,
                    required=True,
                    manual_action_required=True,
                    acquisition_status="BLOCKED",
                    error_reason="Source index needs explicit file selection",
                )
                expected.append(canonical.material_id)
        elif not code:
            add(
                "source_code",
                "Source Code: not offered",
                container.material_id,
                acquisition_status="NOT_APPLICABLE",
                discovery_examined=True,
                review_status="NOT_REQUIRED",
                acquisition_strategy="manual_only",
            )
        if completion:
            from src.tools_materials.source_acquisition import SOURCE_FORMATS, links

            main = BeautifulSoup(pages[container.source_url], "html.parser").find(
                "main"
            )
            for url, fmt, title in links(main, container.source_url):
                # Explicit source suffixes augment the existing role parser.
                if fmt == "txt" and any(r.source_url == url for r in rows.values()):
                    continue
                add(
                    "source_code",
                    title,
                    container.material_id,
                    url,
                    source_format=fmt,
                    discovered_from=(container.source_url,),
                )
            code = [
                r
                for r in rows.values()
                if r.parent_material_id == container.material_id
                and r.material_type == "source_code"
                and r.source_url
            ]
            for index in [r for r in code if r.source_format == "html"]:
                raw = pages.get(index.source_url)
                if raw is None:
                    update(
                        index,
                        error_reason="Source index not exported; package alternatives retained",
                    )
                    continue
                snapshots.append(
                    dict(url=index.source_url, sha256=sha(raw), bytes=len(raw))
                )
                for url, fmt, title in links(
                    BeautifulSoup(raw, "html.parser"), index.source_url
                ):
                    # Reject parent-directory/navigation links and all recursive index traversal.
                    if not url.startswith(index.source_url.rstrip("/") + "/"):
                        continue
                    add(
                        "source_code",
                        title,
                        container.material_id,
                        url,
                        source_format=fmt,
                        discovered_from=(index.source_url,),
                    )
            code = [
                r
                for r in rows.values()
                if r.parent_material_id == container.material_id
                and r.material_type == "source_code"
                and r.source_url
            ]
            supported = [
                r
                for r in code
                if official(r.source_url) and r.source_format in SOURCE_FORMATS
            ]
            packages = [r for r in supported if r.source_format == "zip"]
            required_code = (
                [min(packages, key=lambda r: r.source_url)] if packages else supported
            )
            for row in code:
                needed = row in required_code or (not supported and row == code[0])
                update(
                    row,
                    required=needed,
                    selected=needed,
                    manual_action_required=needed and not supported,
                    acquisition_strategy="approved_source_code"
                    if row in supported
                    else "manual_only",
                    acquisition_status="APPROVAL_PENDING"
                    if row in supported
                    else "MANUAL_PENDING"
                    if needed
                    else "REFERENCED_ONLY",
                    error_reason=None
                    if row in supported
                    else "No supported official direct source file; select indexed files or supply reviewed manual export",
                )
                if needed:
                    expected.append(row.material_id)
            # A source heading with no href is unresolved, not 'not offered'.
            if not code and "source code" in main.get_text(" ", strip=True).lower():
                absent = next(
                    r
                    for r in rows.values()
                    if r.parent_material_id == container.material_id
                    and r.material_type == "source_code"
                )
                update(
                    absent,
                    required=True,
                    acquisition_status="MISSING",
                    error_reason="Source Code advertised without a download href",
                )
                expected.append(absent.material_id)
        if not any(counts.get(k) for k in CONTENT):
            add(
                "transcript",
                "No language content source found",
                container.material_id,
                required=True,
                acquisition_status="MISSING",
                alternative_group=container.material_id,
                acquisition_strategy="text_first",
                error_reason="No transcript, subtitles or media linked",
            )

    fragment = _offers(pages[root_url], root_url, course_id, week_id)
    if not any(r.role.value == "lecture_video" for r in fragment.resources):
        update(
            lecture, acquisition_status="MISSING", error_reason="Lecture branch absent"
        )
    else:
        examine(lecture)
        assets(lecture, fragment)
    for resource in fragment.resources:
        if resource.role.value != "short":
            continue
        short = add(
            "short",
            resource.title or str(resource.original_url),
            shorts.material_id,
            str(resource.original_url),
            True,
            discovered_from=(root_url,),
        )
        if examine(short) is not None:
            assets(
                short,
                _offers(pages[short.source_url], short.source_url, course_id, week_id),
            )
    for resource in fragment.resources:
        if resource.role.value != "problem_set":
            continue
        pset = add(
            "problem_set",
            resource.title or "Problem Set",
            week.material_id,
            str(resource.original_url),
            True,
            discovered_from=(root_url,),
        )
        main = examine(pset)
        if main is None:
            continue
        parent = MaterialResource(
            resource=resource,
            original_url=str(resource.original_url),
            role="problem_set",
            format="html",
            source_origin=source_origin,
        )
        page = SimpleNamespace(
            url=pset.source_url, role="assignment", file="operator-export"
        )
        derived, _, _ = children(
            [parent], [parent], [(page, pages[pset.source_url])], week_id
        )
        tasks = [b for b in derived if b.material_id != parent.material_id]
        if not tasks:
            update(
                pset,
                acquisition_status="BLOCKED",
                error_reason="No task links found; review required",
            )
        for child in tasks:
            task = add(
                "task",
                child.resource.title or child.original_url,
                pset.material_id,
                child.original_url,
                True,
                discovered_from=(pset.source_url,),
                metadata={
                    "task_id": urlsplit(child.original_url)
                    .path.rstrip("/")
                    .split("/")[-1]
                },
            )
            task_main = examine(task)
            if task_main is None:
                continue
            for a in task_main.select("a[href]"):
                url = urldefrag(urljoin(task.source_url, a["href"]))[0]
                if url == task.source_url or urlsplit(url).scheme not in {
                    "http",
                    "https",
                }:
                    continue
                fmt = format_of(url)
                attachment = fmt not in {"html", "unknown"}
                from src.tools_materials.source_acquisition import SOURCE_FORMATS

                source = completion and fmt in SOURCE_FORMATS - {"txt"}
                add(
                    "source_code"
                    if source
                    else "attachment"
                    if attachment
                    else "reference",
                    a.get_text(" ", strip=True) or url,
                    task.material_id,
                    url,
                    attachment,
                    source_format=fmt,
                    discovered_from=(task.source_url,),
                    acquisition_status="APPROVAL_PENDING"
                    if attachment
                    else "REFERENCED_ONLY",
                    acquisition_strategy="explicit_type_size_source_review"
                    if attachment
                    else "reference",
                    metadata={
                        "availability": "LINKED_UNPROBED",
                        "original_href": urljoin(task.source_url, a["href"]),
                        "reason": "Provided file requires individual grant"
                        if attachment
                        else "Reference retained; no recursive acquisition or repository clone",
                    },
                )
    if not any(r.material_type == "problem_set" for r in rows.values()):
        add(
            "problem_set",
            "Problem Set link missing",
            week.material_id,
            required=True,
            acquisition_status="MISSING",
            error_reason="No problem set linked by overview",
        )
    inventory = WeekInventory(
        schema_version=2 if completion else 1,
        course_id=course_id,
        week_id=week_id,
        source_origin=source_origin,
        materials=tuple(rows.values()),
        expected_ids=tuple(dict.fromkeys(expected)),
        expected_parents={mid: rows[mid].parent_material_id for mid in expected},
        expected_types={mid: rows[mid].material_type for mid in expected},
        snapshots=tuple(snapshots),
        limits=limits,
    )
    output = []
    for row in inventory.materials:
        if (
            row.material_type not in CONTAINERS
            and row.source_url
            and official(row.source_url)
        ):
            row = row.model_copy(
                update={"expected_local_path": archive_path(row, inventory)}
            )
        output.append(row)
    if len(output) > limits.max_materials:
        raise ValueError("Week material count exceeds budget")
    return select_fallbacks(inventory.model_copy(update={"materials": tuple(output)}))


def select_fallbacks(inventory):
    rows = list(inventory.materials)
    for container in [r for r in rows if r.material_type in {"lecture", "short"}]:
        alternatives = [r for r in rows if r.alternative_group == container.material_id]
        viable = [
            r
            for r in alternatives
            if r.source_url
            and r.acquisition_status not in {"FAILED", "BLOCKED", "MISSING"}
        ]
        verified = [
            r
            for r in viable
            if r.acquisition_status == "VERIFIED"
            and r.material_type in {"transcript", "subtitles"}
        ]
        chosen = (
            min(
                verified or viable,
                key=lambda r: (CONTENT[r.material_type], r.source_url),
            )
            if viable
            else None
        )
        for row in alternatives:
            selected = chosen is not None and row.material_id == chosen.material_id
            changes = dict(selected=selected, required=False)
            if row.acquisition_status not in SUCCESS | {
                "FAILED",
                "BLOCKED",
                "MISSING",
                "NOT_APPLICABLE",
            }:
                changes["acquisition_status"] = (
                    "FALLBACK_SELECTED"
                    if selected and row.material_type != "transcript"
                    else "APPROVAL_PENDING"
                    if selected
                    else "REFERENCED_ONLY"
                )
            changes["metadata"] = {
                **row.metadata,
                "selection_reason": (
                    "Validated text fulfills this content group"
                    if verified
                    else "First usable candidate: transcript > subtitles > audio > video; validation pending"
                )
                if selected
                else "Alternative retained; higher-priority candidate selected or source unusable",
            }
            rows[rows.index(row)] = row.model_copy(update=changes)
    return inventory.model_copy(update={"materials": tuple(rows)})


def plan(inventory):
    candidates = [
        r
        for r in inventory.materials
        if (r.required or r.selected or r.acquisition_status == "FAILED")
        and r.material_type not in CONTAINERS
    ]
    rows = []
    for r in candidates:
        allowed = (
            not r.manual_action_required
            and r.material_type not in {"audio", "video", "reference"}
            and (r.material_type != "source_code" or inventory.schema_version == 2)
            and r.source_url is not None
            and official(r.source_url)
            and r.source_format
            in {
                "html",
                "pdf",
                "txt",
                "srt",
                "vtt",
                "csv",
                "json",
                "png",
                "jpg",
                "jpeg",
                "py",
                *(
                    {"zip", "c", "h", "sql", "js", "css", "md"}
                    if inventory.schema_version == 2
                    else set()
                ),
            }
        )
        rows.append(
            dict(
                material_id=r.material_id,
                source_url=r.source_url,
                source_format=r.source_format,
                purpose="download",
                max_bytes=inventory.limits.ceiling(r),
                license_reviewed=False,
                eligible=allowed,
                status=r.acquisition_status,
                known_bytes=r.file_size,
                separate_media_review=r.material_type in {"audio", "video"},
            )
        )
    return dict(
        schema_version=1,
        inventory_sha256=fingerprint(inventory.model_dump(mode="json")),
        source_origin=inventory.source_origin,
        reviewed_by="",
        review_reference="",
        transfer_bytes=inventory.limits.transfer_bytes,
        grants=rows,
        source_limits=dict(
            code_bytes=inventory.limits.code_bytes,
            zip_bytes=inventory.limits.zip_bytes,
            zip_unpacked_bytes=8 * 1024**2,
            zip_members=64,
            zip_member_bytes=1024**2,
            zip_max_ratio=100,
        ),
        automatic_media_supported=False,
        processing_enabled=False,
        upper_bytes=sum(r["max_bytes"] for r in rows if r["eligible"]),
        archive_bytes=inventory.limits.archive_bytes,
        report_bytes=inventory.limits.report_bytes,
        manual_upper_bytes=sum(
            inventory.limits.ceiling(r)
            for r in inventory.materials
            if r.manual_action_required and r.acquisition_status not in SUCCESS
        ),
        unresolved_hrefs=[
            r.material_id
            for r in inventory.materials
            if r.source_url is None
            and r.acquisition_status not in {"DISCOVERED", "NOT_APPLICABLE"}
        ],
        remote_sizes_unknown=any(r.file_size is None for r in candidates),
        reserve_bytes=inventory.limits.reserve_bytes,
        note="Review each row, retain only approved eligible rows and remove planning-only fields; no approval is implied",
    )


def _downloader(root, inventory, maximum, transport=None):
    return MaterialDownloader(
        root,
        max_bytes=maximum,
        transport=transport,
        retries=0,
        text_tracks=True,
        manual_archive=True,
        approved_attachments=True,
        approved_source_code=inventory.schema_version == 2,
    )


def verify_row(row, inventory, root):
    downloader = _downloader(root, inventory, inventory.limits.ceiling(row))
    receipt = downloader.validate(binding(row, inventory))
    raw, receipt_path = downloader.paths(binding(row, inventory))
    size = raw.stat().st_size
    if size > inventory.limits.ceiling(row):
        raise ValueError("Existing file exceeds material budget")
    if inventory.schema_version == 2 and row.material_type == "source_code":
        from src.tools_materials.source_acquisition import validate_source

        validate_source(
            read_file(raw, inventory.limits.ceiling(row)), row.source_format
        )
    if row.material_type in {"transcript", "subtitles"}:
        validate_text_source(raw, binding(row, inventory))
    elif row.source_format == "html":
        from src.tools_materials.text_validation import validate_html_page

        validate_html_page(raw)
    if row.expected_local_path != str(raw.relative_to(root)):
        raise ValueError("Archive location differs from inventory")
    return row.model_copy(
        update=dict(
            acquisition_status="MANUAL_VERIFIED"
            if receipt.origin == "local_import" and row.manual_action_required
            else "VERIFIED",
            file_size=size,
            sha256=receipt.raw_sha256,
            receipt_id=str(receipt_path.relative_to(root)),
            error_reason=None,
        )
    )


def validate_approval(inventory, approval, *, purpose="download", retry_failed=False):
    if (
        approval.inventory_sha256 != fingerprint(inventory.model_dump(mode="json"))
        or approval.source_origin != inventory.source_origin
    ):
        raise PermissionError("Approval does not bind this inventory")
    by_id = {r.material_id: r for r in inventory.materials}
    eligible = {g["material_id"] for g in plan(inventory)["grants"] if g["eligible"]}
    if sum(g.max_bytes for g in approval.grants) > min(
        approval.transfer_bytes, inventory.limits.transfer_bytes
    ):
        raise ValueError(
            "Approval worst-case transfer exceeds run budget; select a smaller batch"
        )
    for grant in approval.grants:
        row = by_id.get(grant.material_id)
        if (
            row is None
            or grant.purpose != purpose
            or (purpose == "download" and row.material_id not in eligible)
            or (purpose == "discovery" and row.material_type != "page")
            or (row.source_url, row.source_format)
            != (grant.source_url, grant.source_format)
            or grant.max_bytes > inventory.limits.ceiling(row)
        ):
            raise PermissionError(
                "Unselected, manual, media or mismatched source grant"
            )
        checked_url(grant.source_url)
        if row.acquisition_status == "FAILED" and not retry_failed:
            raise PermissionError("Failed source requires explicit retry")
    return {r.material_id: r for r in inventory.materials}


def acquire(
    inventory,
    approval,
    root,
    *,
    transport=None,
    offline_test=False,
    retry_failed=False,
    checkpoint=None,
    purpose="download",
):
    """One serialized, bounded run; grants bind exact immutable inventory input."""
    from src.tools_materials.capacity import TransferBudget
    from src.tools_materials.https_transport import PublicHTTPSTransport

    if offline_test:
        if inventory.source_origin != "synthetic" or transport is None:
            raise PermissionError("Explicit synthetic mock transport required")
    elif inventory.source_origin != "official" or transport is not None:
        raise PermissionError(
            "Production rejects synthetic origins and injected transports"
        )
    by_id = validate_approval(
        inventory, approval, purpose=purpose, retry_failed=retry_failed
    )
    root = artifact_root(root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Same outer lock as the existing download-only CLI; inner downloader keeps its own lock.
    import fcntl
    import os

    fd = os.open(
        locate(root, ".mvp-download.lock"),
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o600,
    )
    rows, started = list(inventory.materials), time.monotonic()
    budget = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Manual imports use the same outer lock. Existing partial bytes are never adopted.
        if any(root.rglob(".download-*")):
            raise ValueError("Unknown partial bytes require operator investigation")
        budget = TransferBudget(
            transport or PublicHTTPSTransport(),
            min(approval.transfer_bytes, inventory.limits.transfer_bytes),
        )
        for grant in approval.grants:
            row = by_id[grant.material_id]
            if time.monotonic() - started > inventory.limits.wall_seconds:
                raise TimeoutError("Week run wall budget exceeded")
            check_capacity(
                root,
                inventory.limits.archive_bytes,
                inventory.limits.reserve_bytes,
                grant.max_bytes + 65536,
            )
            try:
                from src.tools_materials.capacity import (
                    CapacityLimits,
                    CapacityTransport,
                )

                capacity = CapacityLimits(
                    archive_bytes=inventory.limits.archive_bytes,
                    reserve_bytes=inventory.limits.reserve_bytes,
                )
                guarded = CapacityTransport(budget, root, capacity)
                downloader = _downloader(root, inventory, grant.max_bytes, guarded)
                downloader.total_timeout = min(
                    downloader.total_timeout,
                    inventory.limits.wall_seconds - (time.monotonic() - started),
                )
                _raw, receipt_path = downloader.paths(binding(row, inventory))
                if receipt_path.exists() and not retry_failed:
                    from src.model_materials.materials import ArtifactReceipt

                    previous = ArtifactReceipt.model_validate_json(
                        read_file(receipt_path)
                    )
                    if previous.status in {"selected", "failed", "conflict"}:
                        raise PermissionError(
                            "Interrupted/failed receipt requires explicit retry"
                        )
                downloader.obtain(
                    binding(row, inventory), execute=True, license_reviewed=True
                )
                result = verify_row(row, inventory, root).model_copy(
                    update={
                        "review_status": "APPROVED",
                        "metadata": {
                            **row.metadata,
                            "approval_sha256": fingerprint(
                                approval.model_dump(mode="json")
                            ),
                            "reviewed_by": approval.reviewed_by,
                            "review_reference": approval.review_reference,
                        },
                    }
                )
                if result.file_size > grant.max_bytes:
                    raise ValueError(
                        "Verified existing file exceeds approved size limit"
                    )
            except (ValueError, OSError, RuntimeError) as error:
                result = row.model_copy(
                    update=dict(
                        acquisition_status="FAILED",
                        error_reason=f"{type(error).__name__}: {error}",
                    )
                )
            except Exception as error:
                # HTTPX transport/status failures stay per-material and cannot mark text successful.
                import httpx

                if not isinstance(error, httpx.HTTPError):
                    raise
                result = row.model_copy(
                    update=dict(
                        acquisition_status="FAILED",
                        error_reason=f"{type(error).__name__}: {error}",
                    )
                )
            rows[rows.index(row)] = result
            inventory_result = select_fallbacks(
                inventory.model_copy(update={"materials": tuple(rows)})
            )
            if checkpoint is not None:
                checkpoint(inventory_result)
            if budget.remaining < 0:
                break
        return select_fallbacks(inventory.model_copy(update={"materials": tuple(rows)}))
    finally:
        if budget is not None:
            budget.close()
        os.close(fd)


def import_manual(inventory, material_id, source, expected_sha256, root, *, provenance):
    """Bounded no-extract local import. Raw and receipt never overwrite existing data."""
    import fcntl
    import os

    row = next(r for r in inventory.materials if r.material_id == material_id)
    if (
        not row.manual_action_required
        or row.material_type != "source_code"
        or not provenance.strip()
    ):
        raise PermissionError(
            "Explicit manual source-code material and provenance required"
        )
    if len(expected_sha256) != 64:
        raise ValueError("Expected SHA-256 required")
    if sha(read_file(Path(source), inventory.limits.manual_bytes)) != expected_sha256:
        raise ValueError("Manual input differs from expected SHA-256")
    root = artifact_root(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(
        locate(root, ".mvp-download.lock"),
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o600,
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_capacity(
            root,
            inventory.limits.archive_bytes,
            inventory.limits.reserve_bytes,
            inventory.limits.manual_bytes + 65536,
        )
        downloader = _downloader(root, inventory, inventory.limits.manual_bytes)
        downloader.obtain(
            binding(row, inventory),
            execute=True,
            local_file=source,
            expected_sha256=expected_sha256,
        )
        result = verify_row(row, inventory, root)
        provenance_path = locate(root, result.receipt_id + ".provenance.json")
        record = dict(
            source_url=row.source_url,
            material_id=row.material_id,
            sha256=result.sha256,
            file_size=result.file_size,
            supplied_file=str(Path(source).absolute()),
            provenance=provenance,
        )
        from src.tools_materials.quality import _json

        if provenance_path.exists():
            if _json(read_file(provenance_path)) != record:
                raise ValueError("Manual provenance conflicts with retained import")
        else:
            import json

            publish_bytes(
                provenance_path, (json.dumps(record, indent=2) + "\n").encode()
            )
        result = result.model_copy(
            update={"metadata": {**result.metadata, "manual_provenance": record}}
        )
        return inventory.model_copy(
            update={
                "materials": tuple(
                    result if r.material_id == material_id else r
                    for r in inventory.materials
                )
            }
        )
    finally:
        os.close(fd)


def completeness(inventory, root=None, processing_root=None):
    """Reports never trust success labels without checking receipts and raw bytes."""
    rows, integrity = list(inventory.materials), []
    for row in list(rows):
        if row.acquisition_status not in SUCCESS:
            continue
        try:
            if root is None:
                raise ValueError("Archive not supplied; success is unverified")
            checked = verify_row(row, inventory, Path(root))
            if (checked.sha256, checked.file_size, checked.receipt_id) != (
                row.sha256,
                row.file_size,
                row.receipt_id,
            ):
                raise ValueError("Receipt differs from inventory integrity fields")
            if row.manual_action_required:
                from src.tools_materials.quality import _json

                proof = _json(
                    read_file(locate(Path(root), row.receipt_id + ".provenance.json"))
                )
                if (
                    proof != row.metadata.get("manual_provenance")
                    or proof["sha256"] != row.sha256
                ):
                    raise ValueError("Manual provenance missing or changed")
        except (ValueError, OSError, KeyError) as error:
            rows[rows.index(row)] = row.model_copy(
                update={"acquisition_status": "FAILED", "error_reason": str(error)}
            )
            integrity.append(row.material_id)
    processing = {}
    for row in rows:
        if row.material_type in CONTAINERS or not (
            row.required
            or row.material_id in inventory.expected_ids
            or (row.selected and row.alternative_group)
        ):
            continue
        state = dict(
            status="PENDING",
            reason="Validated processing result required",
            next_action="Run isolated processing after acquisition",
        )
        if row.acquisition_status not in SUCCESS:
            state.update(
                status="BLOCKED",
                reason="Verified acquisition missing",
                next_action="Review source grant and acquire material",
            )
        elif processing_root is not None and root is not None:
            try:
                from src.tools_materials.week_processing import inspect

                inspect(row, inventory, root, processing_root)
                state.update(status="COMPLETED", reason=None, next_action=None)
            except (ValueError, OSError, RuntimeError, KeyError) as error:
                state.update(
                    status="FAILED",
                    reason=str(error),
                    next_action="Inspect parser failure/artifact integrity; reprocess in a new versioned output",
                )
        processing[row.material_id] = state
    by_id = {r.material_id: r for r in rows}
    missing_ids = sorted(
        mid
        for mid in inventory.expected_ids
        if mid not in by_id
        or (
            mid in inventory.expected_parents
            and by_id[mid].parent_material_id != inventory.expected_parents[mid]
        )
        or (
            mid in inventory.expected_types
            and by_id[mid].material_type != inventory.expected_types[mid]
        )
    )

    def assess(scope):
        scope_ids = {r.material_id for r in scope}
        absent = [
            mid
            for mid in missing_ids
            if inventory.expected_parents.get(mid) in scope_ids
        ]
        discovery_missing = [
            r.material_id
            for r in scope
            if (r.required or r.material_id in inventory.expected_ids)
            and (
                r.acquisition_status in {"MISSING", "BLOCKED"}
                or (r.material_type not in CONTAINERS and r.source_url is None)
                or r.metadata.get("reference_links_pending_html_export", False)
                or (r.material_type in CONTAINERS and not r.discovery_examined)
            )
        ]
        acquisition_missing = [
            r.material_id
            for r in scope
            if (r.required or r.material_id in inventory.expected_ids)
            and r.material_type not in CONTAINERS
            and (not r.manual_action_required or inventory.schema_version == 2)
            and r.acquisition_status not in SUCCESS
        ]
        groups = []
        for container in [r for r in scope if r.material_type in {"lecture", "short"}]:
            alternatives = [
                r for r in scope if r.alternative_group == container.material_id
            ]
            satisfied = any(
                r.material_type in {"transcript", "subtitles"}
                and r.acquisition_status == "VERIFIED"
                for r in alternatives
            )
            groups.append(
                dict(
                    parent_material_id=container.material_id,
                    fulfilled=satisfied,
                    processed=any(
                        r.acquisition_status in SUCCESS
                        and processing.get(r.material_id, {}).get("status")
                        == "COMPLETED"
                        for r in alternatives
                    ),
                    selected=[r.material_id for r in alternatives if r.selected],
                    reason=None
                    if satisfied
                    else "Validated text missing; media needs separate review and later transcription",
                )
            )
            if not alternatives or not any(r.source_url for r in alternatives):
                discovery_missing.append(container.material_id)
        manual_pending = [
            r.material_id
            for r in scope
            if r.manual_action_required and r.acquisition_status not in SUCCESS
        ]
        processing_missing = [
            r.material_id
            for r in scope
            if r.material_id in processing
            and processing[r.material_id]["status"] != "COMPLETED"
        ]
        return dict(
            processing_complete=not processing_missing
            and not absent
            and all(g["processed"] for g in groups),
            processing_missing=processing_missing,
            discovery_complete=not discovery_missing and not absent,
            missing_expected_ids=absent,
            acquisition_complete=not acquisition_missing
            and not absent
            and all(g["fulfilled"] for g in groups),
            manual_complete=not manual_pending
            and not any(
                inventory.expected_types.get(mid) == "source_code" for mid in absent
            ),
            discovery_missing=discovery_missing,
            acquisition_missing=acquisition_missing,
            manual_pending=manual_pending,
            content_groups=groups,
        )

    def descendants(parent):
        ids = {parent}
        while True:
            expanded = ids | {
                r.material_id for r in rows if r.parent_material_id in ids
            }
            if expanded == ids:
                return [r for r in rows if r.material_id in ids]
            ids = expanded

    overall = assess(rows)
    if missing_ids:
        overall["discovery_complete"] = overall["acquisition_complete"] = overall[
            "processing_complete"
        ] = False
    overall["missing_expected_ids"] = missing_ids
    sections = {
        r.material_id: {
            "title": r.title,
            "material_type": r.material_type,
            **assess(descendants(r.material_id)),
        }
        for r in rows
        if r.material_type
        in {"week", "lecture", "shorts", "short", "problem_set", "task"}
    }
    return dict(
        schema_version=1,
        course_id=inventory.course_id,
        week_id=inventory.week_id,
        status="FULLY_COMPLETE"
        if all(
            overall[k]
            for k in (
                "discovery_complete",
                "acquisition_complete",
                "processing_complete",
                "manual_complete",
            )
        )
        and not integrity
        else "HOLD",
        c26_status="HOLD",
        processing_enabled=False,
        integrity_failures=integrity,
        materials=[
            dict(
                material_id=r.material_id,
                parent_material_id=r.parent_material_id,
                title=r.title,
                material_type=r.material_type,
                source_url=r.source_url,
                acquisition_status=r.acquisition_status,
                required=r.required,
                selected=r.selected,
                reason=r.error_reason,
                next_action=(
                    "Resolve official href/export"
                    if not r.source_url
                    else "Review exact source/type/size grant and acquire"
                )
                if r.acquisition_status not in SUCCESS | {"NOT_APPLICABLE"}
                else None,
                processing=processing.get(r.material_id, {"status": "NOT_REQUIRED"}),
            )
            for r in rows
        ],
        counts={
            kind: sum(r.material_type == kind for r in rows)
            for kind in ("lecture", "short", "task")
        },
        overall=overall,
        sections=sections,
    )


def resume_discovery(current, previous, root):
    """Carry only revalidated immutable acquisition evidence across rediscovery.

    Removed rows with evidence require operator reconciliation, never silent loss.
    New inventories always need fresh hash-bound source grants.
    """
    if (current.course_id, current.week_id, current.source_origin) != (
        previous.course_id,
        previous.week_id,
        previous.source_origin,
    ):
        raise ValueError("Rediscovery scope mismatch")
    old = {
        r.material_id: r for r in previous.materials if r.acquisition_status in SUCCESS
    }
    if set(old) - {r.material_id for r in current.materials}:
        raise ValueError(
            "Rediscovery removed acquired rows; retain previous inventory and reconcile explicitly"
        )
    rows = []
    for row in current.materials:
        prior = old.get(row.material_id)
        if prior:
            if (prior.source_url, prior.source_format, prior.parent_material_id) != (
                row.source_url,
                row.source_format,
                row.parent_material_id,
            ):
                raise ValueError("Rediscovery changes acquired identity")
            verified = verify_row(prior, previous, Path(root))
            row = row.model_copy(
                update=dict(
                    acquisition_status=verified.acquisition_status,
                    file_size=verified.file_size,
                    sha256=verified.sha256,
                    receipt_id=verified.receipt_id,
                    review_status=prior.review_status,
                    metadata={**row.metadata, **prior.metadata},
                    error_reason=None,
                )
            )
        rows.append(row)
    return select_fallbacks(current.model_copy(update={"materials": tuple(rows)}))


def manual_fallback(inventory, material_id, *, source_format, filename, provenance):
    """Operator records a reviewed local export against an actual context page.

    Context URLs are never represented as downloadable file hrefs or granted HTTP
    permission. The original unresolved offer and reason remain in metadata.
    """
    from src.tools_materials.source_acquisition import SOURCE_FORMATS

    row = next(r for r in inventory.materials if r.material_id == material_id)
    if (
        inventory.schema_version != 2
        or row.material_type != "source_code"
        or row.acquisition_status
        not in {"MISSING", "FAILED", "BLOCKED", "MANUAL_PENDING"}
        or source_format not in SOURCE_FORMATS
        or not provenance.strip()
        or Path(filename).name != filename
        or filename in {"", ".", ".."}
        or "\\" in filename
        or Path(filename).suffix.lower() != "." + source_format
    ):
        raise ValueError(
            "Explicit failed/unresolved source, supported filename/format and provenance required"
        )
    parent = next(
        r for r in inventory.materials if r.material_id == row.parent_material_id
    )
    context = next(
        (
            url
            for url in (*row.discovered_from, parent.source_url)
            if url and official(url)
        ),
        None,
    )
    if context is None:
        raise ValueError("Actual official context page required for manual provenance")
    replacement = row.model_copy(
        update=dict(
            source_url=context,
            source_format=source_format,
            acquisition_strategy="manual_only",
            manual_action_required=True,
            selected=True,
            required=True,
            acquisition_status="MANUAL_PENDING",
            review_status="PENDING",
            sha256=None,
            file_size=None,
            receipt_id=None,
            metadata={
                **row.metadata,
                "original_offer_url": row.source_url,
                "original_offer_format": row.source_format,
                "original_error": row.error_reason,
                "source_url_is_context": True,
                "manual_filename": filename,
                "manual_fallback_reason": provenance,
            },
        )
    )
    replacement = replacement.model_copy(
        update={"expected_local_path": archive_path(replacement, inventory)}
    )
    return inventory.model_copy(
        update={
            "materials": tuple(
                replacement if r.material_id == material_id else r
                for r in inventory.materials
            )
        }
    )
