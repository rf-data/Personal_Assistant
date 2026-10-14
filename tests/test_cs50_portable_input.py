"""Relocation is explicit, source hashes/receipts remain mandatory."""

import shutil

import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported


def test_relocated_workspace_roundtrip(context, tmp_path):
    module, _, _, plan = context
    first = tmp_path / "first"
    first.mkdir()
    _, input = imported(context, first)
    manifest = module.save_portable_manifest(
        (input,), first / "manifest.json", workspace=first
    )
    assert not manifest.inputs[0].raw_srt_path.is_absolute()
    assert str(first) not in (first / "manifest.json").read_text()
    second = tmp_path / "second"
    shutil.copytree(first, second)
    loaded = module.load_knowledge_manifest(second / "manifest.json")
    assert loaded == manifest
    from src.core.config_knowledge import KnowledgeSettings

    chunks = module.build_cs50_knowledge_chunks(
        plan, loaded.inputs[0], KnowledgeSettings(), workspace=second
    )
    assert chunks[0].segment_ids == [0, 2]
    module.load_knowledge_transcript(plan, loaded.inputs[0], workspace=second)
    with pytest.raises(ValueError):
        module.load_knowledge_transcript(
            plan, loaded.inputs[0], workspace=tmp_path / "absent"
        )


@pytest.mark.parametrize("path", ["../escape", "/absolute"])
def test_unsafe_references_rejected(context, tmp_path, path):
    module, _, _, _ = context
    _, input = imported(context, tmp_path)
    portable = module.portable_input(input, workspace=tmp_path)
    with pytest.raises(ValueError, match="relative paths"):
        module.CS50PortableInput.model_validate(
            {**portable.model_dump(), "raw_srt_path": path}
        )


def test_symlink_hash_and_legacy(context, tmp_path):
    module, _, _, plan = context
    _, input = imported(context, tmp_path)
    module.save_knowledge_manifest(
        module.CS50KnowledgeInputManifest(inputs=(input,)), tmp_path / "v1.json"
    )
    legacy = module.load_knowledge_manifest(tmp_path / "v1.json").inputs[0]
    assert module.load_knowledge_transcript(plan, legacy, workspace=tmp_path)
    portable = module.portable_input(input, workspace=tmp_path)
    saved = input.raw_srt_path.read_bytes()
    external = tmp_path / "elsewhere.srt"
    external.write_bytes(saved)
    input.raw_srt_path.unlink()
    input.raw_srt_path.symlink_to(external)
    with pytest.raises(ValueError, match="Symlink"):
        module.load_knowledge_transcript(plan, portable, workspace=tmp_path)
    input.raw_srt_path.unlink()
    input.raw_srt_path.write_bytes(saved + b"changed")
    with pytest.raises(ValueError, match="hash conflict"):
        module.load_knowledge_transcript(plan, portable, workspace=tmp_path)
