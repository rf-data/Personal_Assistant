"""Real offline C18/PDF-v2 provenance survives an isolated synthetic restore."""

import hashlib
import json

from scripts.cs50_workflow_demo import demo
from src.job_control.models import fingerprint
from src.job_control.operations import backup, restore
from src.model_materials.materials import ArtifactReceipt
from src.workflows.models import State


def test_completed_pdf_workflow_restore_retains_all_output_hashes_and_origin(tmp_path):
    source = tmp_path / "synthetic"
    result = demo(source, pdf=True)
    config = source / "config.json"
    config.chmod(0o600)
    backup(config, tmp_path / "snapshot")
    restored = tmp_path / "restored"
    assert restore(tmp_path / "snapshot", restored)["activated"] is False
    state = State.model_validate_json(
        (restored / "workflows/synthetic_workflow/state.v1.json").read_bytes()
    )
    report = state.report
    assert report.status == "completed" and report.run_id == result["job"]["job_id"]
    assert report.report_sha256 == fingerprint(
        report.model_dump(mode="json", exclude={"report_sha256"})
    )
    receipts = []
    for stage in report.stages:
        for ref in stage.output_refs:
            data = (restored / ref.path).read_bytes()
            assert len(data) == ref.size_bytes
            assert hashlib.sha256(data).hexdigest() == ref.sha256
            if ref.kind == "receipt":
                receipt = ArtifactReceipt.model_validate_json(data)
                assert receipt.binding.source_origin == "synthetic"
                receipts.append(receipt)
    assert len(receipts) >= 1
    with (tmp_path / "snapshot/manifest.json").open() as stream:
        assert "configuration.json" in json.load(stream)["files"]
