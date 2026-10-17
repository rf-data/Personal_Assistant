"""Reproduce C21-Q's relocated source bundle without changing original data."""

from pathlib import Path

import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported


def contents(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def relocated(context, root):
    binding, source = imported(context, root)
    (root / "data/lectures/Harvard").rename(root / "data/Harvard")
    return binding, source


def test_ingestion_uses_explicit_plan_paths_not_data_dir(
    context, tmp_path, monkeypatch
):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "different-config-root"))
    binding, source = imported(context, tmp_path)
    assert binding.raw_srt_path.is_relative_to(Path("data/lectures/Harvard"))
    assert source.raw_srt_path == tmp_path / binding.raw_srt_path
    assert not (tmp_path / "different-config-root").exists()
    module, _, _, _ = context
    document = module.TranscriptDocument.model_validate_json(
        source.transcript_json_path.read_bytes()
    )
    assert (
        document.source == document.provenance.source_file == str(binding.raw_srt_path)
    )


def test_relocated_bundle_is_not_silently_adopted(context, tmp_path, monkeypatch):
    from src.tools_rag.cs50_pilot import source_inventory

    module, executor, _, plan = context
    binding, _ = relocated(context, tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    before = contents(tmp_path)
    with pytest.raises(executor.ExecutionConflict, match="receipt"):
        module.bind_cs50_knowledge_input(plan, binding, workspace=tmp_path)
    report = source_inventory(
        plan, workspace=tmp_path, course="cs50_python", section="0"
    )
    assert report["validated_sources"] == 0
    assert report["sources"][0]["import_status"] == "unverified"
    assert report["sources"][0]["source_id"] == binding.source_id
    assert not report["sources"][0]["artifacts"]["raw"]["present"]
    assert contents(tmp_path) == before


def test_changing_plan_root_cannot_rebind_existing_receipt(context, tmp_path):
    from src.tools_lecture.adapt_cs50 import build_cs50_course_plan

    module, executor, _, plan = context
    binding, _ = relocated(context, tmp_path)
    course = next(
        c for c in plan.courses if c.lecture_course.course_id == "cs50_python"
    )
    replacement = build_cs50_course_plan(course.preview, artifact_root=Path("data"))
    rebound = next(b for b in replacement.bindings if b.source_id == binding.source_id)
    changed = plan.model_copy(
        update={
            "courses": tuple(replacement if c == course else c for c in plan.courses)
        }
    )
    before = contents(tmp_path)
    with pytest.raises(
        executor.ExecutionConflict, match="Receipt version/identity/provenance conflict"
    ):
        module.bind_cs50_knowledge_input(changed, rebound, workspace=tmp_path)
    assert contents(tmp_path) == before


@pytest.mark.parametrize("corrupt_copy", [False, True])
def test_explicit_copy_proposal_preserves_identity_and_hash_checks(
    context, tmp_path, corrupt_copy
):
    # Only synthetic fixtures are copied here; production migration remains manual.
    original, candidate = tmp_path / "original", tmp_path / "candidate"
    original.mkdir()
    candidate.mkdir()
    module, executor, _, plan = context
    binding, source = relocated(context, original)
    before = contents(original)
    for reference in (
        binding.raw_srt_path,
        binding.transcript_json_path,
        binding.raw_srt_path.parent / "execution.v1.json",
    ):
        relative = Path("data") / reference.relative_to("data/lectures")
        target = candidate / reference
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write((original / relative).read_bytes())
    raw = candidate / binding.raw_srt_path
    if corrupt_copy:
        raw.write_bytes(raw.read_bytes() + b"tampering")
        with pytest.raises(executor.ExecutionConflict, match="hash conflict"):
            module.bind_cs50_knowledge_input(plan, binding, workspace=candidate)
    else:
        checked = module.bind_cs50_knowledge_input(plan, binding, workspace=candidate)
        assert checked.binding == binding
        assert checked.source_id == source.source_id
        assert checked.raw_sha256 == source.raw_sha256
        assert checked.transcript_sha256 == source.transcript_sha256
        assert checked.transcript_provenance == source.transcript_provenance
    assert contents(original) == before
