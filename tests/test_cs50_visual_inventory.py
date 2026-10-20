"""Real HTML-v2/PDF-v2 outputs and bounded observations, entirely synthetic/offline."""

import base64
import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.cs50_visual_inventory import main
from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import MaterialResource, NormalizedDocument
from src.model_materials.visual_inventory import InventoryLimits, VisualInventory
from src.tools_materials.parse_html import parse_html
from src.tools_materials.parse_pdf import parse_pdf
from src.tools_materials.visual_inventory import inventory, json_bytes, markdown, sha

FIXTURES = Path(__file__).parent / "fixtures/visual_inventory"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden in visual inventory")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def binding(kind):
    resource = ResourceCandidate(
        course_id="cs50_python",
        role="notes" if kind == "html" else "slides",
        original_url=f"https://example.invalid/synthetic/source.{kind}",
        section_keys=("synthetic",),
    )
    return MaterialResource(
        resource=resource,
        original_url=str(resource.original_url),
        lecture_ids=("synthetic-lecture",),
        format=kind,
        role=resource.role.value,
        source_origin="synthetic",
    )


@pytest.fixture(scope="module")
def parsed():
    result = {}
    for kind, parser in (("html", parse_html), ("pdf", parse_pdf)):
        raw = (
            (FIXTURES / "source.html").read_bytes()
            if kind == "html"
            else base64.b64decode((FIXTURES / "source.pdf.b64").read_bytes())
        )
        doc, blobs = parser(binding(kind), raw)
        result[kind] = raw, doc, blobs
    return result


@pytest.fixture
def workspace(tmp_path, parsed):
    def create(kind="html", *, images=True):
        root = tmp_path / kind
        root.mkdir(exist_ok=True)
        raw, doc, blobs = parsed[kind]
        raw_path = root / f"source.{kind}"
        raw_path.write_bytes(raw)
        normalized = root / "normalized.v1.json"
        normalized.write_text(doc.model_dump_json(indent=2) + "\n")
        if images:
            for relative, content in blobs.items():
                target = root / relative
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(content)
        return root, normalized, raw_path, doc

    return create


def run(source, **kwargs):
    root, normalized, raw, _ = source
    return inventory(normalized, input_root=root, raw_path=raw, **kwargs)


def find_codes(report):
    return [w.code for w in report.warnings] + [
        w.code for a in report.assets for w in a.warnings
    ]


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_hashes_identity_read_only_and_determinism(workspace, kind):
    source = workspace(kind)
    root, normalized, raw, doc = source
    before = {
        p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }
    report = run(source)
    assert report == run(source)
    assert report.raw_scan == "complete"
    assert report.counts["errors"] == 0
    assert report.document_id == doc.document_id
    assert report.binding == doc.binding
    assert (
        report.raw_sha256
        == report.observed_raw_sha256
        == hashlib.sha256(raw.read_bytes()).hexdigest()
    )
    assert report.normalized_sha256 == sha(normalized.read_bytes())
    assert VisualInventory.model_validate_json(report.model_dump_json()) == report
    assert report.report_sha256 == sha(
        json_bytes(report.model_dump(mode="json", exclude={"report_sha256"}))
    )
    assert before == {
        p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }
    assert len({a.asset_id for a in report.assets}) == len(report.assets)
    assert all(a.material_id == doc.binding.material_id for a in report.assets)
    assert all(
        a.location.dom if kind == "html" else a.location.page for a in report.assets
    )


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_identical_bytes_have_distinct_occurrence_ids(workspace, kind):
    report = run(workspace(kind))
    available = [a for a in report.assets if a.extraction_status == "available"]
    assert len(available) == 2
    assert available[0].observed_sha256 == available[1].observed_sha256
    assert available[0].asset_id != available[1].asset_id
    assert available[0].location != available[1].location
    assert report.counts["available_artifacts"] == 2
    assert report.counts["unique_artifacts"] == 1


def test_html_sources_svg_caption_and_missing_src(workspace):
    report = run(workspace())
    assert len(report.assets) == 12
    assert report.by_type == {
        "raster_image": 2,
        "external_image_reference": 5,
        "inline_svg": 1,
        "unknown_visual": 4,
    }
    assert report.counts["reference_only"] >= 4
    assert "missing_image_source" in find_codes(report)
    assert "unsafe_reference" in find_codes(report)
    inline = next(a for a in report.assets if a.asset_type == "inline_svg")
    assert inline.location.dom.endswith("/svg[1]")
    assert inline.artifact_status == "not_declared" and inline.observed_sha256 is None
    assert inline.context["svg_references"] == ["#shape"]
    assert (
        report.assets[0].image.caption
        == "Synthetic gray square, no scientific meaning."
    )
    assert any(a.original_reference == "plots/local.png" for a in report.assets)
    assert any(
        a.original_reference == "https://example.invalid/plot.svg"
        for a in report.assets
    )
    assert "srcset_not_selected" in find_codes(report)


def test_pdf_vector_grouping_does_not_drop_decorations(workspace):
    report = run(workspace("pdf"))
    vectors = [a for a in report.assets if a.asset_type == "vector_graphics_candidate"]
    assert len(vectors) == 6
    assert sum(a.context["path_count"] for a in vectors) == 8
    complex_group = next(a for a in vectors if a.context["path_count"] == 3)
    assert complex_group.location.bbox == (40.0, 110.0, 160.0, 180.0)
    assert complex_group.context["operation_count"] == 6
    backgrounds = [a for a in vectors if a.context["page_background_candidate"]]
    assert len(backgrounds) == 2
    assert all(a.context["single_path"] for a in backgrounds)
    assert sum(a.context["repeated_layout_candidate"] for a in vectors) == 4
    assert report.by_page == {"1": 6, "2": 2}
    assert report.by_type == {"raster_image": 2, "vector_graphics_candidate": 6}
    assert report.counts["review_candidates"] == 8
    assert all(
        "geometric_candidate_only" in [w.code for w in a.warnings] for a in vectors
    )
    normalized = NormalizedDocument.model_validate_json(
        (workspace("pdf")[1]).read_bytes()
    )
    assert any(b.type in {"paragraph", "heading"} for b in normalized.blocks)


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_missing_image_artifacts_are_reference_only(workspace, kind):
    report = run(workspace(kind, images=False))
    claimed = [a for a in report.assets if a.image and a.image.artifact_path]
    assert len(claimed) == 2
    assert all(
        a.artifact_status == "missing" and a.observed_sha256 is None for a in claimed
    )
    assert all(a.extraction_status == "reference_only" for a in claimed)
    assert report.counts["available_artifacts"] == 0
    assert "missing_image_bytes" in find_codes(report)


def test_normalized_only_marks_uninspected_raw(workspace):
    root, normalized, _, doc = workspace()
    report = inventory(normalized, input_root=root)
    assert report.raw_scan == "not_supplied"
    assert len(report.assets) == len(doc.images)
    assert "raw_not_supplied" in find_codes(report)
    assert "inline_svg" not in report.by_type


def test_wrong_raw_is_never_scanned_as_bound_document(workspace):
    source = workspace()
    source[2].write_text('<main><img src="wrong.png"></main>')
    report = run(source)
    assert report.raw_scan == "failed" and report.counts["errors"] == 1
    assert report.observed_raw_sha256 != report.raw_sha256
    assert not any(a.original_reference == "wrong.png" for a in report.assets)


def test_corrupt_artifact_is_not_available(workspace):
    source = workspace()
    path = source[0] / source[3].images[0].artifact_path
    path.write_bytes(b"not the original bytes")
    report = run(source)
    assert report.counts["available_artifacts"] == 0
    assert sum(a.artifact_status == "hash_mismatch" for a in report.assets) == 2
    assert all(
        a.observed_sha256 == sha(path.read_bytes())
        for a in report.assets
        if a.image and a.image.artifact_path
    )


@pytest.mark.parametrize(
    "field", ["max_pages", "max_paths", "max_operations", "max_assets"]
)
def test_pdf_native_limits_report_incomplete_scan(workspace, field):
    report = run(
        workspace("pdf"),
        limits=InventoryLimits(**{field: 1 if field != "max_assets" else 4}),
    )
    assert report.raw_scan == "failed"
    assert "raw_scan_failed" in find_codes(report)
    assert report.counts["errors"] >= 1
    assert "vector_graphics_candidate" not in report.by_type


def test_byte_and_pixel_limits(workspace):
    source = workspace("pdf")
    with pytest.raises(ValueError, match="byte limit"):
        run(source, limits=InventoryLimits(max_bytes=10))
    report = run(source, limits=InventoryLimits(max_image_pixels=1))
    assert "image_pixel_limit" in find_codes(report)
    assert report.counts["available_artifacts"] == 2  # No image decoder invoked.


@pytest.mark.parametrize(
    "reference",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "blob:123",
        "ftp://example.invalid/x",
        "https://user:pass@example.invalid/x",
        "data:invalid",
        "\\\\host\\image",
        "",
        "\nimage.png",
    ],
)
def test_reference_safety_without_dereferencing(reference):
    from src.tools_materials.visual_inventory import reference_warnings

    status, warnings = reference_warnings(reference, "https://example.invalid/base/")
    assert status in {"unsupported", "reference_only"}
    assert warnings


@pytest.mark.parametrize(
    "kind",
    [
        "input_symlink",
        "artifact_symlink",
        "parent_symlink",
        "outside_root",
        "traversal",
    ],
)
def test_path_safety(workspace, tmp_path, kind):
    source = workspace()
    root, normalized, raw, doc = source
    if kind == "input_symlink":
        link = root / "linked.json"
        link.symlink_to(normalized)
        with pytest.raises(ValueError, match="Symlink"):
            inventory(link, input_root=root)
    elif kind == "artifact_symlink":
        path = root / doc.images[0].artifact_path
        path.rename(path.with_suffix(".saved"))
        path.symlink_to(raw)
        report = run(source)
        assert any(a.artifact_status == "unsafe" for a in report.assets)
    elif kind == "parent_symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        with pytest.raises(ValueError, match="Symlink"):
            inventory(alias / normalized.name, input_root=tmp_path)
    elif kind == "outside_root":
        with pytest.raises(ValueError, match="outside"):
            inventory(normalized, input_root=root / "nested")
    else:
        with pytest.raises(ValueError, match="outside"):
            inventory(root / ".." / "html" / normalized.name, input_root=root)


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b'{"schema_version":1,"schema_version":1}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b'{"schema_version":1,"binding":[]}',
    ],
)
def test_invalid_json_fails_without_writes(workspace, raw):
    source = workspace()
    source[1].write_bytes(raw)
    with pytest.raises(ValueError):
        run(source)


def test_cli_json_markdown_and_no_overwrite(workspace, tmp_path, capsys):
    root, normalized, raw, _ = workspace("pdf")
    output, summary = tmp_path / "report.json", tmp_path / "report.md"
    args = [
        "--normalized",
        str(normalized),
        "--input-root",
        str(root),
        "--raw",
        str(raw),
        "--json-report",
        str(output),
        "--markdown-report",
        str(summary),
    ]
    assert main(args) == 0
    report = VisualInventory.model_validate_json(output.read_bytes())
    assert summary.read_text() == markdown(report)
    assert "vector_graphics_candidate" in summary.read_text()
    assert "Visual assets=8" in capsys.readouterr().err
    original = output.read_bytes(), summary.read_bytes()
    assert main(args) == 2
    assert (output.read_bytes(), summary.read_bytes()) == original
    assert main(args[:-4] + ["--json-report", str(root / "forbidden.json")]) == 2
    assert not (root / "forbidden.json").exists()


def test_cli_stdout_and_partial_exit_status(workspace, capsys):
    root, normalized, raw, _ = workspace()
    args = ["--normalized", str(normalized), "--input-root", str(root)]
    assert main(args) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["raw_scan"] == "not_supplied"
    assert "# Visual inventory" in output.err
    raw.write_bytes(b"wrong")
    assert main(args + ["--raw", str(raw)]) == 1


def test_asset_ids_are_scoped_by_document(workspace):
    source = workspace()
    first = run(source)
    value = json.loads(source[1].read_bytes())
    value["binding"]["lecture_ids"] = ["other-lecture"]  # binding metadata is preserved
    source[1].write_bytes(json_bytes(value))
    other = run(source)
    assert other.binding.lecture_ids == ("other-lecture",)
    assert [a.asset_id for a in first.assets] == [
        a.asset_id for a in other.assets
    ]  # existing document_id does not bind lecture list


def test_changed_raw_document_identity_changes_assets(workspace):
    root, normalized, raw, doc = workspace()
    first = inventory(normalized, input_root=root)
    changed, _ = parse_html(
        doc.binding, raw.read_bytes() + b"<!-- new source bytes -->"
    )
    normalized.write_text(changed.model_dump_json())
    second = inventory(normalized, input_root=root)
    assert first.document_id != second.document_id
    assert not {a.asset_id for a in first.assets} & {a.asset_id for a in second.assets}


def test_pdf_aliases_preserve_all_normalized_ids_and_blocks(workspace):
    source = workspace("pdf")
    report = run(source)
    images = [a for a in report.assets if a.image]
    assert len(source[3].images) == 4  # Demonstrated existing PDF-v2 duplication.
    assert len(images) == 2 and report.counts["normalized_image_aliases"] == 2
    ids = {i.image_id for a in images for i in (a.image, *a.image_aliases)}
    assert ids == {i.image_id for i in source[3].images}
    assert {b for a in images for b in a.block_ids} == {
        b.block_id for b in source[3].blocks if b.type == "image_reference"
    }
    assert "duplicate_normalized_image_reference" in find_codes(report)


def test_relative_file_is_not_implicitly_adopted(workspace):
    source = workspace()
    target = source[0] / "plots/local.png"
    target.parent.mkdir()
    target.write_bytes(b"unreviewed local bytes")
    report = run(source)
    relative = next(
        a for a in report.assets if a.original_reference == "plots/local.png"
    )
    assert relative.extraction_status == "reference_only"
    assert relative.observed_sha256 is None and relative.image.artifact_path is None


@pytest.mark.parametrize(
    "defect",
    [
        "none",
        "normalized_sha",
        "raw_sha",
        "binding",
        "images",
        "path",
        "status",
        "json",
    ],
)
def test_optional_existing_receipt_contract(workspace, defect):
    from src.model_materials.materials import ArtifactReceipt

    source = workspace("pdf")
    root, normalized, _, doc = source
    value = ArtifactReceipt(
        binding=doc.binding,
        status="completed",
        origin="local_import",
        parser=doc.parser,
        raw_sha256=doc.raw_sha256,
        normalized_sha256=sha(normalized.read_bytes()),
        normalized_path=normalized.name,
        image_hashes={i.artifact_path: i.sha256 for i in doc.images if i.artifact_path},
    ).model_dump(mode="json")
    if defect == "normalized_sha":
        value["normalized_sha256"] = "0" * 64
    elif defect == "raw_sha":
        value["raw_sha256"] = "0" * 64
    elif defect == "binding":
        value["binding"]["lecture_ids"] = ["foreign"]
    elif defect == "images":
        value["image_hashes"] = {}
    elif defect == "path":
        value["normalized_path"] = "foreign.json"
    elif defect == "status":
        value["status"] = "parsed"
    receipt = root / "receipt.json"
    receipt.write_bytes(b"{" if defect == "json" else json_bytes(value))
    report = run(source, receipt_path=receipt)
    assert ("receipt_conflict" in find_codes(report)) == (defect != "none")


def test_raw_only_image_occurrence_is_retained_without_extraction(workspace):
    from src.tools_materials.parse_html import build_document

    source = workspace("pdf")
    root, normalized, raw, doc = source
    parts = [
        b.model_dump(exclude={"block_id", "order"})
        for b in doc.blocks
        if b.type != "image_reference"
    ]
    limited = build_document(
        doc.binding, raw.read_bytes(), doc.parser, parts, metadata=doc.metadata
    )
    normalized.write_text(limited.model_dump_json())
    before = set(root.rglob("*"))
    report = run(source)
    rasters = [a for a in report.assets if a.asset_type == "raster_image"]
    assert len(rasters) == 2 and all(a.image is None for a in rasters)
    assert all(a.observed_sha256 is None for a in rasters)
    assert report.counts["available_artifacts"] == 0
    assert set(root.rglob("*")) == before


def test_inline_svg_external_and_active_content_are_inert(tmp_path):
    raw = b'<main><p>Synthetic SVG safety case</p><svg><script>throw Error("never execute")</script><foreignObject/><image href="https://example.invalid/never-fetch.png"/><use href="javascript:never"/></svg></main>'
    doc, _ = parse_html(binding("html"), raw)
    normalized = tmp_path / "normalized.json"
    normalized.write_text(doc.model_dump_json())
    path = tmp_path / "source.html"
    path.write_bytes(raw)
    report = inventory(normalized, input_root=tmp_path, raw_path=path)
    svg = next(a for a in report.assets if a.asset_type == "inline_svg")
    assert svg.context["active_svg"] is True
    assert svg.context["svg_references"] == [
        "https://example.invalid/never-fetch.png",
        "javascript:never",
    ]
    assert {"unsafe_reference", "active_svg_not_executed", "svg_not_rendered"} <= set(
        find_codes(report)
    )


@pytest.mark.parametrize("mode", ["rotated", "overlap"])
def test_pdf_geometry_and_true_overlapping_occurrences(tmp_path, mode):
    import pymupdf

    native = pymupdf.open()
    page = native.new_page(width=300, height=200)
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 2, 2), False)
    image.clear_with(80)
    page.insert_text((20, 20), "Synthetic")
    page.insert_image(pymupdf.Rect(20, 40, 60, 80), stream=image.tobytes("png"))
    if mode == "rotated":
        page.set_rotation(90)
    else:
        page.insert_image(pymupdf.Rect(20, 40, 60, 80), stream=image.tobytes("png"))
    raw = native.tobytes(no_new_id=True)
    native.close()
    doc, blobs = parse_pdf(binding("pdf"), raw)
    normalized = tmp_path / "normalized.json"
    normalized.write_text(doc.model_dump_json())
    path = tmp_path / "source.pdf"
    path.write_bytes(raw)
    for relative, content in blobs.items():
        target = tmp_path / relative
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(content)
    report = inventory(normalized, input_root=tmp_path, raw_path=path)
    assert report.counts["errors"] == 0
    assert len(report.assets) == (1 if mode == "rotated" else 2)
    assert all(a.location.bbox == (20, 40, 60, 80) for a in report.assets)
    assert all(
        a.context["rotation"] == (90 if mode == "rotated" else 0) for a in report.assets
    )
    assert len({a.asset_id for a in report.assets}) == len(report.assets)


def test_unmatched_image_and_block_location_conflicts(workspace):
    source = workspace("pdf")
    value = json.loads(source[1].read_bytes())
    value["images"][0]["source_location"]["bbox"] = [1, 2, 3, 4]
    source[1].write_bytes(json_bytes(value))
    report = run(source)
    assert {"source_position_unmatched", "image_location_conflict"} <= set(
        find_codes(report)
    )
    assert report.counts["errors"] >= 2


def test_artifact_byte_budget_without_image_decode(workspace):
    source = workspace()
    path = source[0] / source[3].images[0].artifact_path
    path.write_bytes(b"x" * 200000)
    report = run(source, limits=InventoryLimits(max_bytes=100000))
    assert any(a.artifact_status == "limit_exceeded" for a in report.assets)
    assert report.counts["available_artifacts"] == 0


def test_worker_timeout_is_visible_and_does_not_modify_sources(workspace, monkeypatch):
    import subprocess

    import src.tools_materials.parse_pdf as module

    source = workspace("pdf")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("bounded worker", 0.01)

    monkeypatch.setattr(module, "run_worker", timeout)
    report = run(source)
    assert report.raw_scan == "failed"
    assert any(
        w.code == "raw_scan_failed" and "timed out" in w.message
        for w in report.warnings
    )


def test_clean_normalized_only_import_without_c10_or_sdks(workspace, tmp_path):
    import subprocess
    import sys

    source = workspace()
    repository = Path(__file__).resolve().parents[1]
    script = r"""
import sys, socket
sys.path.insert(0, sys.argv[1])
class Block:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'openai','marvin','docling','bs4','pymupdf'} or fullname in {'src.tools_materials.quality','src.model_materials.quality','src.tools_lecture.material_handoff','src.core.config','src.core.memory'}:
            raise AssertionError('Forbidden import: '+fullname)
sys.meta_path.insert(0,Block())
def forbidden(*a,**kw): raise AssertionError('No network')
socket.socket.connect=forbidden;socket.create_connection=forbidden;socket.getaddrinfo=forbidden
from src.tools_materials.visual_inventory import inventory
result=inventory(sys.argv[2],input_root=sys.argv[3])
assert result.raw_scan=='not_supplied'
print('offline independent import passed')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(repository),
            str(source[1]),
            str(source[0]),
        ],
        cwd=tmp_path,
        env={},
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "independent import passed" in result.stdout


def test_alias_block_location_conflict_is_not_hidden(workspace):
    source = workspace("pdf")
    value = json.loads(source[1].read_bytes())
    last = next(b for b in reversed(value["blocks"]) if b["type"] == "image_reference")
    last["location"]["bbox"] = [1, 2, 3, 4]
    source[1].write_bytes(json_bytes(value))
    report = run(source)
    assert "image_location_conflict" in find_codes(report)
    assert report.counts["errors"] >= 1


def test_markdown_does_not_emit_untrusted_binding_markup(workspace):
    source = workspace()
    value = json.loads(source[1].read_bytes())
    value["binding"]["lecture_ids"] = ["<script>alert(1)</script>"]
    source[1].write_bytes(json_bytes(value))
    rendered = markdown(run(source))
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


@pytest.mark.parametrize("bbox", [[4, 3, 2, 1], [0, 0, float("inf"), 1]])
def test_inventory_model_rejects_invalid_geometry(workspace, bbox):
    from src.model_materials.visual_inventory import VisualAsset

    source = workspace("pdf")
    asset = run(source).assets[0].model_dump()
    asset["location"] = {"page": 1, "bbox": bbox}
    with pytest.raises(ValueError):
        VisualAsset.model_validate(asset)


@pytest.mark.parametrize("defect", ["none", "lecture", "course", "material", "json"])
def test_optional_existing_discovery_plan_verifies_bindings(workspace, defect):
    from src.model_discovery.cs50 import CourseDiscovery, SectionDiscovery
    from src.model_materials.materials import MaterialPlan

    source = workspace()
    root, normalized, _, doc = source
    lecture = ResourceCandidate(
        course_id="cs50_python",
        role="lecture_video",
        original_url="https://example.invalid/synthetic/lecture",
        section_keys=("synthetic",),
    )
    good = doc.binding.model_copy(update={"lecture_ids": (lecture.resource_id,)})
    course = CourseDiscovery(
        course_id="cs50_python",
        original_url="https://example.invalid/",
        sections=(
            SectionDiscovery(
                course_id="cs50_python",
                key="synthetic",
                original_url="https://example.invalid/section",
            ),
        ),
        resources=(doc.binding.resource, lecture),
    )
    plan = MaterialPlan(courses=(course,), materials=(good,))
    value = doc.model_dump(mode="json")
    value["binding"] = good.model_dump(mode="json")
    if defect == "lecture":
        value["binding"]["lecture_ids"] = ["foreign"]
    normalized.write_bytes(json_bytes(value))
    plan_value = plan.model_dump(mode="json")
    if defect == "course":
        plan_value["courses"][0]["course_id"] = "cs50_sql"
    elif defect == "material":
        plan_value["materials"] = []
    path = root / "plan.json"
    path.write_bytes(b"{" if defect == "json" else json_bytes(plan_value))
    report = run(source, plan_path=path)
    assert report.binding_verification == (
        "plan_verified" if defect == "none" else "conflict"
    )
    assert ("binding_conflict" in find_codes(report)) == (defect != "none")


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_checked_in_example_reports_are_real_reproducible_observations(workspace, kind):
    report = run(workspace(kind))
    value = report.model_dump(mode="json", exclude={"report_sha256"})
    value["inputs"] = {
        key: "synthetic-inputs/" + kind + "/" + Path(name).name
        if key != "artifact_root"
        else "synthetic-inputs/" + kind
        for key, name in value["inputs"].items()
    }
    portable = VisualInventory(**value, report_sha256=sha(json_bytes(value)))
    examples = Path(__file__).resolve().parents[1] / "docs/examples/visual_inventory"
    saved = VisualInventory.model_validate_json(
        (examples / f"{kind}.inventory.v1.json").read_bytes()
    )
    assert saved.counts == portable.counts
    assert [a.asset_id for a in saved.assets] == [a.asset_id for a in portable.assets]
    # Native/library upgrades may change extraction metadata. Exact reproducibility
    # is asserted for the recorded backend version, never assumed across versions.
    if saved.scan_backend == portable.scan_backend:
        assert saved == portable
    assert (examples / f"{kind}.inventory.v1.md").read_text() == markdown(saved)
