"""Rebuild C08 review metadata offline; never counterfeit browser HTML exports."""

import json
from pathlib import Path

from artifacts.c26_cs50p_07.build_review_inventory import build as previous_review
from src.model_discovery.cs50 import deterministic_id
from src.model_materials.acquisition import WeekMaterial
from src.tools_materials import week_acquisition as api
from src.tools_materials.week_processing import plan as processing_plan

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs/course_sources/cs50p_week0_completion"


def build():
    inventory = previous_review().model_copy(update={"schema_version": 2})
    rows = []
    for row in inventory.materials:
        if row.material_type == "source_code" and row.required:
            direct = bool(
                row.source_url
                and api.official(row.source_url)
                and row.source_format
                in {"zip", "py", "txt", "md", "c", "h", "sql", "js", "css"}
            )
            row = row.model_copy(
                update=dict(
                    manual_action_required=False,
                    acquisition_status="APPROVAL_PENDING" if direct else "MISSING",
                    acquisition_strategy="approved_source_code",
                    error_reason=None
                    if direct
                    else "Official package offered; exact download href requires bounded operator HTML export",
                )
            )
        rows.append(row)

    def add(parent, kind, title, url=None, fmt="html", **extra):
        mid = deterministic_id(
            "week_material",
            inventory.course_id,
            inventory.week_id,
            parent.material_id,
            kind,
            url or title,
        )
        rows.append(
            WeekMaterial(
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
                **extra,
            )
        )

    functions = "https://docs.python.org/3/library/functions.html"
    strings = "https://docs.python.org/3/library/stdtypes.html#string-methods"
    refs = {
        "indoor": [functions + "#input", strings],
        "playback": [functions + "#input", strings],
        "faces": [
            "https://en.wikipedia.org/wiki/List_of_emoticons",
            "https://emojipedia.org/slightly-smiling-face/",
            "https://emojipedia.org/slightly-frowning-face/",
            functions + "#input",
            strings,
        ],
        "einstein": [
            "https://en.wikipedia.org/wiki/Albert_Einstein",
            functions + "#input",
            functions + "#int",
            functions,
        ],
        "tip": [functions + "#input", functions + "#float", strings],
    }
    for task in [r for r in rows if r.material_type == "task"]:
        name = task.metadata["task_id"]
        for url in refs[name]:
            add(
                task,
                "reference",
                url,
                url,
                acquisition_status="REFERENCED_ONLY",
                error_reason="External reference retained; no automatic external retrieval",
                metadata={
                    "evidence_kind": "official_browser_link_observations",
                    "observed_on": "2026-10-28",
                },
            )
        add(
            task,
            "source_code",
            "Starter code embedded in task HTML"
            if name == "tip"
            else "No starter-code download offered",
            acquisition_status="NOT_APPLICABLE",
            review_status="NOT_REQUIRED",
            discovery_examined=True,
            error_reason="Inline example is processed with task HTML; no standalone href"
            if name == "tip"
            else "Task requires learner-created Python file; filename is not a download URL",
            metadata={
                "inline_starter_code": name == "tip",
                "html_parent": task.material_id,
            },
        )
        add(
            task,
            "attachment",
            "No supplied file download observed",
            acquisition_status="NOT_APPLICABLE",
            review_status="NOT_REQUIRED",
            discovery_examined=True,
            error_reason="No downloadable attachment linked on examined official task page",
        )
    inv = api.select_fallbacks(inventory.model_copy(update={"materials": tuple(rows)}))
    # Snapshot-only rows retain actual historic provenance. Browser observations do not create raw receipts.
    return inv


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    inv = build()
    report = api.completeness(inv)
    ledger = dict(
        observed_on="2026-10-28",
        evidence_kind="historical_snapshot_plus_official_browser_observations",
        controls=dict(
            expected={"lecture": 1, "short": 5, "task": 5}, observed=report["counts"]
        ),
        materials=[
            dict(
                material_id=r.material_id,
                parent_material_id=r.parent_material_id,
                type=r.material_type,
                format=r.source_format,
                url=r.source_url,
                discovered_from=r.discovered_from,
                reason=r.error_reason
                or (
                    "Exact href preserved from historical official snapshot; availability/size unprobed"
                    if r.source_url
                    else "Structural identity; not a download URL"
                ),
                next_action="Export official detail HTML, resolve exact href, rediscover and review"
                if not r.source_url and r.acquisition_status in {"MISSING", "BLOCKED"}
                else "No transfer; review reference/variant"
                if not r.required and not r.selected
                else "Review source, type, size and rights before acquiring",
            )
            for r in inv.materials
        ],
    )
    for name, value in {
        "manifest.json": inv.model_dump(mode="json"),
        "download-plan.json": api.plan(inv),
        "completeness.json": report,
        "processing-plan.json": processing_plan(inv),
        "url-ledger.json": ledger,
    }.items():
        (TARGET / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        )
    assert report["counts"] == {"lecture": 1, "short": 5, "task": 5}
    assert report["status"] == "HOLD"


if __name__ == "__main__":
    main()
