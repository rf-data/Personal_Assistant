"""Reproduce the C18 admission blocker with the operator's real overview.

This test proves rejection, not successful task processing. It never supplies
invented task contents or submits a job.
"""

import json
import os
from pathlib import Path

import pytest

from src.job_control.models import CatalogEntry
from src.model_materials.week import DiscoverySnapshot, WeekRequest
from src.tools_materials.batch import sha
from src.tools_materials.processing import make_plan
from src.tools_materials.week import plan_week
from src.workflows.definition import prepare
from src.workflows.models import Definition


def test_real_children_rejected_even_with_hash_bound_overview_in_bundle(tmp_path):
    export = os.environ.get("CS50_WEEK0_QUALITY_EXPORT")
    if not export:
        pytest.skip("Explicit operator export root required")
    export = Path(export)
    before = {
        export / directory / name: (export / directory / name).read_bytes()
        for directory in ("material_01", "material_02")
        for name in ("original.html", "normalized.v1.json", "quality.v1.json")
    }
    raw_path = export / "material_02/original.html"
    manifest = Path("docs/course_sources/cs50/manifest.json").absolute()
    report = plan_week(
        WeekRequest(
            manifest=manifest,
            discovery_exports=(
                DiscoverySnapshot(
                    label="operator_export/pset0.html",
                    path=raw_path,
                    original_url="https://cs50.harvard.edu/python/psets/0/",
                    sha256=sha(before[raw_path]),
                ),
            ),
        )
    )
    children = [r for r in report.resources if r.parent_resource_ids]
    baseline = json.loads(
        Path("docs/deployment/c26a/week0_resources.v1.json").read_bytes()
    )
    expected = {
        r["resource_id"] for r in baseline["resources"] if r["parent_resource_ids"]
    }
    assert len(children) == 5 and {r.resource_id for r in children} == expected
    assert all(r.binding.resource.provenance[0].locator for r in children)

    # Supply the real, pinned overview through the existing manifest contract.
    # Even this alone cannot opt the C18 discovery adapter into reading it.
    data = json.loads(manifest.read_bytes())
    data["courses"] = [c for c in data["courses"] if c["course_id"] == "cs50_python"]
    files = {}
    for page in data["courses"][0]["pages"]:
        content = (manifest.parent / page["file"]).read_bytes()
        target = tmp_path / page["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        page["sha256"] = sha(content)
        files[page["file"]] = sha(content)
    overview = "cs50_python/final_acceptance_pset0.html"
    (tmp_path / overview).write_bytes(before[raw_path])
    files[overview] = sha(before[raw_path])
    data["courses"][0]["pages"].append(
        dict(
            file=overview,
            role="assignment",
            sha256=files[overview],
            url="https://cs50.harvard.edu/python/psets/0/",
        )
    )
    bundled = tmp_path / "manifest.json"
    bundled.write_text(json.dumps(data))
    files["manifest.json"] = sha(bundled.read_bytes())
    worker = make_plan(bundled)
    assert not expected & {b.source_id for b in worker.materials}
    assert children[0].parent_resource_ids[0] in {b.source_id for b in worker.materials}

    # The empty placeholder is deliberately unavailable task content. Selection
    # must fail before any import/parse or worker execution can use it.
    (tmp_path / "unavailable-task.placeholder").write_bytes(b"")
    files["unavailable-task.placeholder"] = sha(b"")
    for child in children:
        definition = Definition(
            course_id="cs50_python",
            sources={
                child.resource_id: "unavailable-task.placeholder",
            },
        )
        payload = definition.model_dump_json().encode()
        (tmp_path / "workflow.json").write_bytes(payload)
        files["workflow.json"] = sha(payload)
        entry = CatalogEntry(
            kind="workflow_bundle",
            root=tmp_path,
            files=files,
            roles=dict(manifest="manifest.json", workflow="workflow.json"),
            course_ids=("cs50_python",),
        )
        with pytest.raises(ValueError, match="No resources match explicit scope"):
            prepare(entry)
    assert {p: p.read_bytes() for p in before} == before
