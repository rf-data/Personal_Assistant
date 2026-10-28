"""Rebuild the conservative Week-0 review artifact from existing evidence, offline.

Browser observations are metadata, never counterfeit downloaded HTML snapshots.
Unknown hrefs are preserved as null and block full discovery/acquisition.
"""

import json
from pathlib import Path

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.acquisition import WeekMaterial
from src.tools_materials import week_acquisition as api

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/course_sources/cs50p_week0_review/evidence.json"


def build():
    evidence = json.loads(EVIDENCE.read_bytes())
    inventory = api.discover(
        {
            evidence["week_url"]: (
                ROOT / "docs/course_sources/cs50/cs50_python/week_0.html"
            ).read_bytes()
        }
    )
    rows = {r.material_id: r for r in inventory.materials}
    expected = list(inventory.expected_ids)
    parents, kinds = dict(inventory.expected_parents), dict(inventory.expected_types)
    observed_shorts = {s["source_url"] for s in evidence["shorts"]}
    assert observed_shorts == {
        r.source_url for r in rows.values() if r.material_type == "short"
    }

    def add(parent, kind, title, url=None, fmt="html", required=False, **extra):
        mid = deterministic_id(
            "week_material",
            inventory.course_id,
            inventory.week_id,
            parent.material_id,
            kind,
            url or title,
        )
        row = WeekMaterial(
            course_id=inventory.course_id,
            week_id=inventory.week_id,
            section_id=parent.section_id,
            material_id=mid,
            parent_material_id=parent.material_id,
            material_type=kind,
            title=title,
            source_url=url,
            source_format=fmt,
            discovered_from=(parent.source_url,),
            required=required,
            **extra,
        )
        if url and api.official(url):
            row = row.model_copy(
                update={"expected_local_path": api.archive_path(row, inventory)}
            )
        elif row.manual_action_required:
            row = row.model_copy(
                update={
                    "expected_local_path": "manual-unresolved/"
                    + mid.split(":")[1]
                    + "/source.zip"
                }
            )
        rows[mid] = row
        if required:
            expected.append(mid)
            parents[mid], kinds[mid] = parent.material_id, kind
        return row

    for short in evidence["shorts"]:
        container = next(
            r
            for r in rows.values()
            if r.material_type == "short" and r.source_url == short["source_url"]
        )
        rows[container.material_id] = container.model_copy(
            update={
                "discovery_examined": True,
                "acquisition_status": "DISCOVERED",
                "error_reason": None,
                "metadata": {
                    "evidence_kind": evidence["evidence_kind"],
                    "id": short["id"],
                },
            }
        )
        if not short["source_code_offered"]:
            add(
                container,
                "source_code",
                "Source Code: not offered",
                acquisition_status="NOT_APPLICABLE",
                discovery_examined=True,
                review_status="NOT_REQUIRED",
                acquisition_strategy="manual_only",
            )
        for kind in short["offered"]:
            formats = {
                "audio": ["mp3"],
                "video": ["mp4"],
                "transcript": ["txt"],
                "subtitles": ["srt"],
                "slides": ["pdf", "google_slides"],
                "source_code": ["html", "pdf", "zip"],
            }[kind]
            for fmt in formats:
                url = (
                    short.get("source_index_url")
                    if kind == "source_code" and fmt == "html"
                    else None
                )
                manual = kind == "source_code" and fmt == "zip"
                add(
                    container,
                    kind,
                    f"{short['title']}: {kind} ({fmt}; exact href pending)"
                    if not url
                    else "Source Code index",
                    url,
                    fmt,
                    manual or (kind == "slides" and fmt == "pdf"),
                    manual_action_required=manual,
                    acquisition_status="MANUAL_PENDING"
                    if manual
                    else "REFERENCED_ONLY"
                    if url
                    else "BLOCKED",
                    acquisition_strategy="manual_only"
                    if kind == "source_code"
                    else "text_first"
                    if kind in api.CONTENT
                    else "approved_file",
                    acquisition_priority=api.CONTENT.get(kind, 0),
                    alternative_group=container.material_id
                    if kind in api.CONTENT
                    else None,
                    error_reason=None
                    if url
                    else "Official link label observed; exact href requires operator HTML export",
                    metadata={
                        "availability": "LINKED_UNPROBED",
                        "evidence_kind": evidence["evidence_kind"],
                        "index_files": short.get("index_observed_files", []),
                        "observed_video_variants": short.get(
                            "observed_video_variants", []
                        )
                        if kind == "video"
                        else [],
                    },
                )
    pset = next(r for r in rows.values() if r.material_type == "problem_set")
    rows[pset.material_id] = pset.model_copy(
        update={
            "discovery_examined": True,
            "acquisition_status": "DISCOVERED",
            "error_reason": None,
            "metadata": {"evidence_kind": evidence["evidence_kind"]},
        }
    )
    for task in evidence["tasks"]:
        container = add(
            pset,
            "task",
            task["title"],
            task["source_url"],
            required=True,
            acquisition_status="DISCOVERED",
            discovery_examined=True,
            description=task["description"],
            metadata={
                "task_id": task["id"],
                "attachments_offered": task["attachments_offered"],
                "inline_starter_code": task.get("inline_starter_code", False),
                "reference_links_pending_html_export": True,
                "evidence_kind": evidence["evidence_kind"],
            },
        )
        add(
            container,
            "page",
            task["title"],
            task["source_url"],
            required=True,
            acquisition_status="APPROVAL_PENDING",
            acquisition_strategy="approved_html",
        )
    return inventory.model_copy(
        update={
            "materials": tuple(rows.values()),
            "expected_ids": tuple(dict.fromkeys(expected)),
            "expected_parents": parents,
            "expected_types": kinds,
        }
    )


if __name__ == "__main__":
    inventory = build()
    target = ROOT / "docs/course_sources/cs50p_week0_review"
    (target / "manifest.json").write_text(inventory.model_dump_json(indent=2) + "\n")
    (target / "download-plan.json").write_text(
        json.dumps(api.plan(inventory), indent=2) + "\n"
    )
    (target / "completeness.json").write_text(
        json.dumps(api.completeness(inventory), indent=2) + "\n"
    )
