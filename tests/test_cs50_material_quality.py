"""Deterministic offline audits of genuine v2 output and corrupt local inputs."""

import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.cs50_material_quality import main
from src.model_discovery.cs50 import (
    CourseDiscovery,
    Provenance,
    ResourceCandidate,
    SectionDiscovery,
)
from src.model_materials.materials import ArtifactReceipt, MaterialResource
from src.tools_lecture.material_handoff import MaterialReview, prepare_material_handoff
from src.tools_materials.parse_html import parse_html
from src.tools_materials.parse_pdf import parse_pdf
from src.tools_materials.processing import MaterialPlan
from src.tools_materials.quality import validate_material

FIXTURES = Path(__file__).parent / "fixtures/material_quality"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path.write_bytes(raw)
    return raw


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("C10 is offline")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture(scope="module")
def sources():
    result = {}
    lecture = ResourceCandidate(
        course_id="cs50_python",
        role="lecture_video",
        original_url="https://cs50.harvard.edu/python/lectures/0/",
        section_keys=("0",),
    )
    for kind, filename, role in (
        ("html", "notes.html", "notes"),
        ("pdf", "source.pdf", "source_code"),
    ):
        provenance = Provenance(
            original_url="https://cs50.harvard.edu/python/weeks/0/",
            fixture_file=filename,
            locator="synthetic material reference",
        )
        resource = ResourceCandidate(
            course_id="cs50_python",
            role=role,
            original_url=f"https://cs50.harvard.edu/python/notes/0/{filename}",
            section_keys=("0",),
            provenance=(provenance,),
        )
        binding = MaterialResource(
            resource=resource,
            lecture_ids=(lecture.resource_id,),
            original_url=str(resource.original_url),
            format=kind,
            role=role,
            source_origin="synthetic",
        )
        course = CourseDiscovery(
            course_id="cs50_python",
            original_url="https://cs50.harvard.edu/python/",
            sections=(
                SectionDiscovery(
                    course_id="cs50_python",
                    key="0",
                    original_url="https://cs50.harvard.edu/python/weeks/0/",
                ),
            ),
            resources=(lecture, resource),
        )
        plan = MaterialPlan(courses=(course,), materials=(binding,))
        raw = (FIXTURES / filename).read_bytes()
        document, blobs = (parse_html if kind == "html" else parse_pdf)(binding, raw)
        result[kind] = (plan, raw, document, blobs)
    return result


@pytest.fixture
def case(tmp_path, sources):
    def build(kind="html"):
        plan, raw, doc, blobs = sources[kind]
        root = tmp_path / kind
        directory = root / doc.binding.material_id.split(":")[1]
        normalized = directory / doc.document_id.split(":")[1] / "normalized.v1.json"
        normalized.parent.mkdir(parents=True)
        raw_path = directory / "raw/source"
        raw_path.parent.mkdir()
        raw_path.write_bytes(raw)
        data = (doc.model_dump_json(indent=2) + "\n").encode()
        normalized.write_bytes(data)
        for relative, content in blobs.items():
            image = normalized.parent / relative
            image.parent.mkdir(exist_ok=True)
            image.write_bytes(content)
        receipt = ArtifactReceipt(
            binding=doc.binding,
            status="completed",
            raw_sha256=doc.raw_sha256,
            origin="local_import",
            parser=doc.parser,
            normalized_path=normalized.relative_to(root).as_posix(),
            normalized_sha256=sha(data),
            image_hashes={p: sha(b) for p, b in blobs.items()},
            history=("verified", "parsed", "normalized", "completed"),
        )
        receipt_path = directory / "receipt.v1.json"
        receipt_path.write_text(receipt.model_dump_json(indent=2))
        plan_path = tmp_path / f"{kind}-plan.json"
        plan_path.write_text(plan.model_dump_json(indent=2))
        return dict(
            normalized_path=normalized,
            receipt_path=receipt_path,
            raw_path=raw_path,
            plan_path=plan_path,
            workspace=root,
        )

    return build


def edit(paths, callback, *, target="normalized", rehash=True):
    path = paths[f"{target}_path"]
    value = json.loads(path.read_bytes())
    callback(value)
    raw = dump(path, value)
    if target == "normalized" and rehash:
        receipt = json.loads(paths["receipt_path"].read_bytes())
        receipt["normalized_sha256"] = sha(raw)
        dump(paths["receipt_path"], receipt)


def codes(report):
    return {f.code for f in report.findings}


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_valid_v2_preserves_sources_and_is_deterministic(case, kind):
    paths = case(kind)
    before = {p: p.read_bytes() for p in paths["workspace"].rglob("*") if p.is_file()}
    first = prepare_material_handoff(**paths)
    assert first.report.passed, first.report.model_dump_json(indent=2)
    assert first.handoff.course_id == "cs50_python"
    assert first.handoff.lecture_ids == first.handoff.document.binding.lecture_ids
    assert first.handoff.document.binding.resource.provenance
    assert first.handoff.receipt.origin == "local_import"
    assert not first.handoff.execution_supported
    assert not first.handoff.knowledge_fact_verified
    assert first == MaterialReview.model_validate_json(first.model_dump_json())
    assert (
        first.model_dump_json() == prepare_material_handoff(**paths).model_dump_json()
    )
    assert validate_material(**paths) == first.report
    assert before == {
        p: p.read_bytes() for p in paths["workspace"].rglob("*") if p.is_file()
    }


def test_handoff_counts_canonical_body_once(case):
    review = prepare_material_handoff(**case())
    handoff = review.handoff
    units = handoff.aggregation_units
    assert [u.text for u in units] == [
        "Hello",
        "Use print(x).",
        "Nested item",
        'def hello():\n    print("hi")\n',
    ]
    assert {u.block.block_id for u in units}.isdisjoint(handoff.excluded_blocks)
    assert "table_of_contents" in handoff.excluded_blocks.values()
    assert "reference_projection" in handoff.excluded_blocks.values()
    assert "image_reference_only" in codes(review.report)
    assert all(u.text == u.block.text[u.char_start : u.char_end] for u in units)
    assert len({u.unit_id for u in units}) == len(units)


def test_code_view_is_reversible_and_not_aggregated_twice(case):
    review = prepare_material_handoff(**case("pdf"))
    codesource = next(b for b in review.handoff.document.blocks if b.type == "code")
    assert " 1  # Example" in codesource.text
    assert codesource.data["code_view"].startswith("# Example\ndef hello():\n    print")
    assert [
        u.text for u in review.handoff.aggregation_units if u.block.type == "code"
    ] == [codesource.text]
    assert review.handoff.alternative_views == (
        f"blocks.{codesource.order}.data.code_view",
    )
    assert "derived_code_view" in codes(review.report)


@pytest.mark.parametrize(
    "change,expected",
    [
        (lambda d: d.pop("schema_version"), "version_missing"),
        (lambda d: d["parser"].pop("version"), "version_missing"),
        (lambda d: d["binding"].pop("schema_version"), "version_missing"),
        (lambda d: d.update(schema_version=2), "schema_invalid"),
        (lambda d: d["parser"].update(version="99"), "schema_invalid"),
        (lambda d: d.pop("raw_sha256"), "schema_invalid"),
        (
            lambda d: d["blocks"][1].update(block_id=d["blocks"][0]["block_id"]),
            "block_identity",
        ),
        (lambda d: d["blocks"][1].update(order=0), "block_identity"),
        (lambda d: d["blocks"][1].update(order=40), "block_identity"),
        (lambda d: d["metadata"].update(course_id="cs50_sql"), "metadata_conflict"),
        (
            lambda d: d["binding"].update(lecture_ids=["resource:unknown"]),
            "plan_binding_conflict",
        ),
        (
            lambda d: d["binding"]["resource"].update(provenance=[]),
            "provenance_missing",
        ),
        (lambda d: d["blocks"][0]["location"].update(dom=None), "dom_missing"),
    ],
)
def test_technical_corruption_blocks_handoff(case, change, expected):
    paths = case()
    edit(paths, change)
    result = prepare_material_handoff(**paths)
    assert not result.report.passed and result.handoff is None
    assert expected in codes(result.report)
    assert any(
        f.category == "technical" and f.severity == "error"
        for f in result.report.findings
    )
    if expected == "block_identity":
        finding = next(f for f in result.report.findings if f.code == expected)
        assert finding.block_id and finding.block_order == 1 and finding.location.dom


def test_missing_optional_metadata_is_reported_not_invented(case):
    paths = case()
    edit(paths, lambda d: d.update(title=None, metadata={}))
    report = validate_material(**paths)
    assert report.passed and {"metadata_missing", "title_missing"} <= codes(report)


@pytest.mark.parametrize(
    "which,expected",
    [
        ("raw", "raw_hash_mismatch"),
        ("normalized", "normalized_hash_mismatch"),
        ("receipt", "normalized_hash_mismatch"),
    ],
)
def test_false_hashes(case, which, expected):
    paths = case()
    if which == "receipt":
        edit(paths, lambda r: r.update(normalized_sha256="0" * 64), target="receipt")
    else:
        with paths[f"{which}_path"].open("ab") as stream:
            stream.write(b" ")
    assert expected in codes(validate_material(**paths))


@pytest.mark.parametrize("target", ["normalized", "receipt", "plan", "raw"])
def test_missing_files(case, target):
    paths = case()
    paths[f"{target}_path"].unlink()
    result = prepare_material_handoff(**paths)
    assert result.handoff is None and "input_invalid" in codes(result.report)


@pytest.mark.parametrize(
    "bad",
    [
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b'{"schema_version":1,"schema_version":1}',
        b'{"metadata":NaN}',
        b'{"metadata":1e400}',
    ],
)
@pytest.mark.parametrize("target", ["normalized", "receipt", "plan"])
def test_malformed_json_is_a_report(case, bad, target):
    paths = case()
    paths[f"{target}_path"].write_bytes(bad)
    result = prepare_material_handoff(**paths)
    assert result.handoff is None and "input_invalid" in codes(result.report)
    json.dumps(result.model_dump(mode="json"), allow_nan=False)


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("item_doms", ["/missing"], "list_invalid"),
        ("item_doms", [[], []], "list_invalid"),
        ("ordered", "false", "list_invalid"),
    ],
)
def test_list_structure_invalid(case, field, value, expected):
    paths = case()
    edit(
        paths,
        lambda d: next(b for b in d["blocks"] if b["type"] == "list")["data"].update(
            {field: value}
        ),
    )
    assert expected in codes(validate_material(**paths))


def test_toc_context_must_resolve_and_keep_projection(case):
    paths = case()

    def change(d):
        next(b for b in d["blocks"] if b["data"].get("list_context"))["data"].pop(
            "content_role"
        )

    edit(paths, change)
    assert "toc_projection_invalid" in codes(validate_material(**paths))


@pytest.mark.parametrize(
    "change,expected",
    [
        (lambda b: b["data"].update(reference_only=False), "link_projection_invalid"),
        (lambda b: b["data"].pop("original_url"), "link_projection_invalid"),
        (lambda b: b["data"].update(reference_only="true"), "projection_invalid"),
        (
            lambda b: b["data"].update(
                list_context=[{"list_dom": [], "item_index": 0}]
            ),
            "list_context_invalid",
        ),
        (
            lambda b: b["data"].update(
                inline_code=[{"start": -1, "end": 500, "text": "x"}]
            ),
            "inline_code_invalid",
        ),
    ],
)
def test_reference_projection_corruption(case, change, expected):
    paths = case()
    edit(paths, lambda d: change(next(b for b in d["blocks"] if b["type"] == "link")))
    assert expected in codes(validate_material(**paths))


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b["data"].update(code_view="changed"),
        lambda b: b["data"].update(line_numbers="bad"),
        lambda b: b["data"]["line_numbers"][0].update(prefix="wrong"),
        lambda b: b["data"]["line_numbers"][0].update(line_index=2),
        lambda b: b["data"]["line_numbers"][0].update(number=99),
        lambda b: b["data"].pop("line_number_strategy"),
    ],
)
def test_invalid_reconstructed_code(case, change):
    paths = case("pdf")
    edit(paths, lambda d: change(next(b for b in d["blocks"] if b["type"] == "code")))
    result = prepare_material_handoff(**paths)
    assert result.handoff is None
    finding = next(f for f in result.report.findings if f.code == "code_view_invalid")
    assert finding.block_id and finding.location.page == 1


@pytest.mark.parametrize(
    "change,expected,passed",
    [
        (lambda d: d["metadata"].update(page_count=3), "page_uncovered", True),
        (lambda d: d["metadata"].update(page_count=1), "page_invalid", False),
        (lambda d: d["metadata"].update(page_count="2"), "page_count_invalid", False),
        (lambda d: d["metadata"].pop("page_count"), "page_count_invalid", False),
        (lambda d: d["blocks"][0]["location"].update(page=None), "page_invalid", False),
        (
            lambda d: d["blocks"][0]["location"].update(bbox=[10, 0, 0, 10]),
            "bbox_invalid",
            False,
        ),
        (
            lambda d: d["blocks"][0].update(uncertainty=["Possible ambiguous code"]),
            "parser_uncertainty",
            True,
        ),
        (
            lambda d: d.update(warnings=["Page 2: no extractable text"]),
            "parser_warning",
            True,
        ),
    ],
)
def test_pages_and_semantic_review(case, change, expected, passed):
    paths = case("pdf")
    edit(paths, change)
    report = validate_material(**paths)
    assert report.passed is passed and expected in codes(report)
    finding = next(f for f in report.findings if f.code == expected)
    if expected == "page_uncovered":
        assert finding.category == "semantic_review" and finding.location.page == 3


def local_image(paths):
    data = b"own synthetic image bytes"
    path = paths["normalized_path"].parent / "images/local.bin"
    path.parent.mkdir()
    path.write_bytes(data)
    edit(
        paths,
        lambda d: d["images"][0].update(
            artifact_path="images/local.bin", sha256=sha(data)
        ),
    )
    edit(
        paths,
        lambda r: r.update(image_hashes={"images/local.bin": sha(data)}),
        target="receipt",
    )
    return path


@pytest.mark.parametrize(
    "failure,expected",
    [
        (None, None),
        ("missing", "image_artifact_missing"),
        ("hash", "image_hash_mismatch"),
        ("manifest", "image_manifest_conflict"),
        ("escape", "schema_invalid"),
    ],
)
def test_image_artifacts(case, failure, expected):
    paths = case()
    image = local_image(paths)
    if failure == "missing":
        image.unlink()
    elif failure == "hash":
        image.write_bytes(b"corrupt")
    elif failure == "manifest":
        edit(paths, lambda r: r.update(image_hashes={}), target="receipt")
    elif failure == "escape":
        edit(paths, lambda d: d["images"][0].update(artifact_path="../outside.bin"))
    report = validate_material(**paths)
    assert report.passed is (failure is None)
    if expected:
        assert expected in codes(report)


def test_invalid_lecture_in_plan_is_rejected(case):
    paths = case()
    edit(
        paths,
        lambda p: p["materials"][0].update(lecture_ids=["resource:foreign"]),
        target="plan",
    )
    result = prepare_material_handoff(**paths)
    assert result.handoff is None and "schema_invalid" in codes(result.report)


def test_symlinks_and_receipt_path_binding(case, tmp_path):
    paths = case()
    original = paths["normalized_path"]
    copy = original.with_name("copy.json")
    copy.write_bytes(original.read_bytes())
    assert "receipt_path_conflict" in codes(
        validate_material(**{**paths, "normalized_path": copy})
    )
    link = original.with_name("link.json")
    link.symlink_to(original)
    assert "path_invalid" in codes(
        validate_material(**{**paths, "normalized_path": link})
    )
    outside = tmp_path / "outside"
    outside.write_bytes(paths["raw_path"].read_bytes())
    assert "path_invalid" in codes(validate_material(**{**paths, "raw_path": outside}))


def args_for(paths):
    return [
        arg
        for key in (
            "workspace",
            "plan_path",
            "normalized_path",
            "receipt_path",
            "raw_path",
        )
        for arg in ("--" + key.removesuffix("_path"), str(paths[key]))
    ]


def test_cli_default_read_only_json_and_origin_summary(case, capsys):
    paths = case()
    before = sorted(paths["workspace"].rglob("*"))
    assert main(args_for(paths)) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["reviews"][0]["handoff"]["course_id"] == "cs50_python"
    assert "course=cs50_python" in output.err and "image_reference_only" in output.err
    assert before == sorted(paths["workspace"].rglob("*"))


def test_cli_exclusive_reports_and_failed_exit(case, tmp_path, capsys):
    paths = case()
    report = tmp_path / "quality.json"
    args = args_for(paths) + ["--output", str(report)]
    assert main(args) == 0
    before = report.read_bytes()
    assert main(args) == 2 and report.read_bytes() == before
    assert (
        main(args_for(paths) + ["--output", str(paths["workspace"] / "new.json")]) == 2
    )
    paths["raw_path"].write_bytes(b"corrupt")
    assert main(args_for(paths)) == 1
    assert "raw_hash_mismatch" in capsys.readouterr().err


def test_cli_batch_and_duplicate_inputs(case, capsys):
    html, pdf = case(), case("pdf")
    args = args_for(html) + [
        arg
        for key in ("normalized_path", "receipt_path", "raw_path")
        for arg in ("--" + key.removesuffix("_path"), str(pdf[key]))
    ]
    # Different workspace/plan deliberately cannot be silently merged.
    assert main(args) == 1
    capsys.readouterr()
    duplicates = args_for(html) + [
        arg
        for key in ("normalized_path", "receipt_path", "raw_path")
        for arg in ("--" + key.removesuffix("_path"), str(html[key]))
    ]
    with pytest.raises(SystemExit, match="2"):
        main(duplicates)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("classification", None, "classification_invalid"),
        (
            "classification",
            {"strategy": "python_math_v2", "signals": [[], []]},
            "classification_invalid",
        ),
        ("line_bboxes", None, "line_geometry_invalid"),
        ("line_bboxes", [[0, 0, 1]], "line_geometry_invalid"),
        ("line_bboxes", [[10, 0, 0, 10]], "line_geometry_invalid"),
    ],
)
def test_pdf_classification_and_line_evidence(case, field, value, code):
    paths = case("pdf")
    edit(paths, lambda d: d["blocks"][0]["data"].update({field: value}))
    result = prepare_material_handoff(**paths)
    assert result.handoff is None and code in codes(result.report)


@pytest.mark.parametrize(
    "change,expected",
    [
        (lambda r: r.update(status="failed"), "receipt_incomplete"),
        (lambda r: r["parser"].update(max_blocks=100), "receipt_binding_conflict"),
        (lambda r: r.update(raw_sha256="0" * 64), "receipt_binding_conflict"),
        (lambda r: r.update(normalized_path="../outside"), "receipt_path_conflict"),
        (lambda r: r["parser"].pop("version"), "version_missing"),
    ],
)
def test_receipt_contract(case, change, expected):
    paths = case()
    edit(paths, change, target="receipt")
    assert expected in codes(validate_material(**paths))


def test_image_location_and_unknown_reference(case):
    paths = case()
    edit(paths, lambda d: d["images"][0]["source_location"].update(dom="/elsewhere"))
    assert "image_location_conflict" in codes(validate_material(**paths))
    edit(
        paths,
        lambda d: next(b for b in d["blocks"] if b["type"] == "image_reference")[
            "data"
        ].update(image_id=[]),
    )
    assert not validate_material(**paths).passed


def test_cli_valid_multiple_materials(case, sources, tmp_path, capsys):
    import shutil

    html, pdf = case(), case("pdf")
    # Merge the two small, explicit discovery graphs into one reviewed snapshot.
    hp, pp = sources["html"][0], sources["pdf"][0]
    course = hp.courses[0].model_copy(
        update={"resources": hp.courses[0].resources + (pp.courses[0].resources[1],)}
    )
    plan = MaterialPlan(courses=(course,), materials=hp.materials + pp.materials)
    html["plan_path"].write_text(plan.model_dump_json(indent=2))
    for child in pdf["workspace"].iterdir():
        shutil.move(child, html["workspace"] / child.name)
    args = args_for(html)
    for key in ("normalized_path", "receipt_path", "raw_path"):
        relocated = html["workspace"] / pdf[key].relative_to(pdf["workspace"])
        args.extend(["--" + key.removesuffix("_path"), str(relocated)])
    assert main(args) == 0
    reviews = json.loads(capsys.readouterr().out)["reviews"]
    assert len(reviews) == 2 and all(r["handoff"] for r in reviews)


def test_snapshot_models_reject_aggregation_tampering(case):
    review = prepare_material_handoff(**case())
    payload = review.model_dump(mode="json")
    payload["handoff"]["aggregation_units"].append(
        payload["handoff"]["aggregation_units"][0]
    )
    with pytest.raises(ValueError, match="canonical aggregation"):
        MaterialReview.model_validate(payload)
    payload = review.model_dump(mode="json")
    payload["report"]["course_id"] = "cs50_sql"
    with pytest.raises(ValueError, match="snapshot"):
        MaterialReview.model_validate(payload)


def test_cli_help_and_validation_need_no_sdks_or_settings(case, tmp_path):
    import os
    import subprocess
    import sys

    paths = case()
    script = """import importlib.abc, sys, runpy, socket
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, name, *args):
  if name.split('.')[0] in {'marvin', 'openai', 'pydantic_ai', 'torch', 'docling', 'pymupdf', 'fitz', 'bs4', 'pydantic_settings'}: raise AssertionError(name)
def forbidden(*a, **k): raise AssertionError('Network forbidden')
socket.socket.connect = forbidden
socket.getaddrinfo = forbidden
sys.meta_path.insert(0, Guard())
sys.argv = ['cs50_material_quality', *sys.argv[1:]]
runpy.run_module('scripts.cs50_material_quality', run_name='__main__')
"""
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
    }
    for args in (["--help"], args_for(paths)):
        result = subprocess.run(
            [sys.executable, "-c", script, *args],
            env=env,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr


def test_cli_rejects_output_parent_symlink(case, tmp_path):
    paths = case()
    alias = tmp_path / "workspace-alias"
    alias.symlink_to(paths["workspace"], target_is_directory=True)
    assert main(args_for(paths) + ["--output", str(alias / "new-report.json")]) == 2
    assert not (paths["workspace"] / "new-report.json").exists()
