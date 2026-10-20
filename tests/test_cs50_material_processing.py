import pytest

from src.model_materials.materials import ParserConfig
from src.tools_lecture.execute_cs50 import ExecutionConflict
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import (
    MaterialPlan,
    MaterialProcessor,
    make_plan,
    plan_steps,
)
from tests.test_cs50_material_download import binding
from tests.test_cs50_material_html import HTML


def imported(tmp_path):
    b = binding()
    workspace = tmp_path / "workspace"
    source = tmp_path / "local"
    source.write_bytes(HTML)
    MaterialDownloader(workspace).obtain(b, execute=True, local_file=source)
    return b, workspace


def test_plan_full_graph_roundtrip_and_task_bindings():
    plan = make_plan("docs/course_sources/cs50/manifest.json")
    assert len(plan.materials) == 653 and len(plan.courses) == 6
    assert MaterialPlan.model_validate_json(plan.model_dump_json()) == plan
    assert any("ai" in b.resource.section_keys for b in plan.materials)
    steps = [s for b in plan.materials for s in plan_steps(b)["tasks"]]
    assert len({s["task_id"] for s in steps}) == len(steps)
    for b in plan.materials:
        s = plan_steps(b)
        if s["tasks"]:
            assert s["tasks"][1]["depends_on"] == [s["tasks"][0]["task_id"]]
    assert all(
        b.resource.course_id == "cs50_python" for b in plan.select(course="cs50_python")
    )


def test_import_parse_resume_and_corruption(tmp_path):
    b, w = imported(tmp_path)
    p = MaterialProcessor(w)
    assert p.parse(b)["status"] == "selected"
    receipt = p.parse(b, execute=True)
    assert receipt.status == "completed"
    assert p.parse(b, execute=True) == receipt
    assert receipt.history[-3:] == ("parsed", "normalized", "completed")
    output = w / receipt.normalized_path
    output.write_bytes(b"corrupt")
    with pytest.raises(ExecutionConflict, match="hash"):
        p.inspect(b)


def test_parser_change_cannot_resume(tmp_path):
    b, w = imported(tmp_path)
    p = MaterialProcessor(w)
    p.parse(b, execute=True)
    with pytest.raises(ExecutionConflict, match="configuration"):
        p.parse(b, execute=True, config=ParserConfig(name="html", max_blocks=100))


def test_missing_dependency(tmp_path):
    p = MaterialProcessor(tmp_path / "workspace")
    with pytest.raises(ExecutionConflict, match="receipt"):
        p.parse(binding(), execute=True)


def test_partial_publication_resume(tmp_path, monkeypatch):
    b, w = imported(tmp_path)
    p = MaterialProcessor(w)
    import src.tools_materials.processing as module

    original = module.publish_bytes

    def publish_then_crash(path, data):
        original(path, data)
        raise RuntimeError("lost publication acknowledgement")

    monkeypatch.setattr(module, "publish_bytes", publish_then_crash)
    with pytest.raises(RuntimeError):
        p.parse(b, execute=True)
    monkeypatch.setattr(module, "publish_bytes", original)
    assert p.parse(b, execute=True).status == "completed"


def test_image_hash_revalidation(tmp_path):
    b, w = imported(tmp_path)
    p = MaterialProcessor(w)
    # HTML has remote references only; no invented locally downloaded images.
    r = p.parse(b, execute=True)
    from src.model_materials.materials import NormalizedDocument

    doc = NormalizedDocument.model_validate_json((w / r.normalized_path).read_bytes())
    assert doc.images[0].artifact_path is None


def test_unsupported_no_writes(tmp_path):
    p = MaterialProcessor(tmp_path / "workspace")
    assert p.parse(binding("pptx", "slides"), execute=True)["status"] == "unsupported"
    assert not p.workspace.exists()


def test_parse_failure_persisted_and_no_download_retry(tmp_path):
    b = binding()
    workspace = tmp_path / "workspace"
    source = tmp_path / "invalid"
    source.write_bytes(b"not html")
    MaterialDownloader(workspace).obtain(b, execute=True, local_file=source)
    p = MaterialProcessor(workspace)
    with pytest.raises(ValueError):
        p.parse(b, execute=True)
    receipt = p.inspect(b)
    assert receipt.status == "failed" and "ValueError" in receipt.error
    assert "verified" in receipt.history
    assert (
        MaterialDownloader(workspace).obtain(b, execute=True, local_file=source)
        == receipt
    )
