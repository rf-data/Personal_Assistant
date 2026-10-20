"""Synthetic framework contracts, never independent real-CS50 gold judgments."""

import json
import socket
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.cs50_material_evaluation import main
from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.inventory import InventorySelection
from src.content_store.models import sha256
from src.content_store.store import ContentStore
from src.model_evaluation.material_evaluation import (
    CorpusEntry,
    CorpusManifest,
    EvaluationReport,
    GoldDataset,
    GoldReference,
)
from src.tools_evaluation.evaluate_materials import evaluate, load_inputs, publish
from tests.content_adapter_support import REVISION, material, srt
from tests.content_store_support import OWNER


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in corpus evaluation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def example(tmp_path):
    bundle, document = material(tmp_path / "input")
    selection = InventorySelection(
        entry_id="notes",
        kind="material",
        source_id=document.binding.source_id,
        course_id="cs50_python",
        expected_implementation_revision=REVISION,
        bundle=bundle,
    )
    entry = CorpusEntry(
        entry_id="notes",
        origin="synthetic",
        course_id="cs50_python",
        source_id=selection.source_id,
        format="html",
        root_key="fixture",
        permission="evaluation",
        permission_reference="synthetic test fixture only",
        selection=selection,
    )
    corpus = CorpusManifest(
        schema_version=1, dataset_version="test-v1", entries=(entry,)
    )
    empty = GoldDataset(schema_version=1, dataset_version="test-v1", references=())
    roots = {"fixture": bundle.workspace}
    observed = evaluate(corpus, empty, roots=roots, actor=OWNER).report["inventory"][0]
    return corpus, empty, roots, observed, document, bundle


def reference(example, **updates):
    corpus, _, _, observed, document, _ = example
    heading = next(
        (b for b in document.blocks if b.type == "heading"), document.blocks[0]
    )
    values = dict(
        gold_id="heading",
        entry_id="notes",
        source_id=corpus.entries[0].source_id,
        source_version_id=observed["source_version_id"],
        original_sha256=document.raw_sha256,
        dimension="text",
        source_reference="hand-authored fixture heading, not parser output",
        created_date=date(2026, 10, 18),
        target_pointer=f"/blocks/{heading.order}",
        expected_content="Hello",
        expected_occurrences=1,
        reference_status="confirmed",
        method="synthetic_reference",
        reviewer="synthetic_fixture_author",
        review_reference="synthetic test specification",
        review_date=date(2026, 10, 18),
    )
    return GoldReference(**(values | updates))


def run(example, references=(), **options):
    corpus, _, roots, _, _, _ = example
    gold = GoldDataset(
        schema_version=1, dataset_version="test-v1", references=tuple(references)
    )
    return evaluate(corpus, gold, roots=roots, actor=OWNER, **options)


def group(report, origin="synthetic", format_="html", dimension="text"):
    return next(
        r
        for r in report.report["metrics"]
        if (r["origin"], r["format"], r["dimension"]) == (origin, format_, dimension)
    )


def test_complete_bundle_independent_constants_and_denominators(example):
    report = run(example, [reference(example)])
    assert report.report["inventory"][0]["binding_verified"]
    assert report.report["inventory"][0]["classification"] == "synthetic_fixture"
    assert report.report["results"][0]["status"] == "passed"
    assert group(report)["metrics"]["exact_content"] == dict(
        numerator=1, denominator=1, rate=1.0
    )
    assert group(report, origin="real")["metrics"]["exact_content"]["rate"] is None
    assert group(report, format_="pdf")["reference_count"] == 0
    assert EvaluationReport.model_validate_json(report.model_dump_json()) == report


@pytest.mark.parametrize("status", ["pending_review", "rejected"])
def test_unreviewed_gold_excluded(example, status):
    report = run(example, [reference(example, reference_status=status)])
    assert report.report["results"][0]["status"] == "not_evaluable"
    assert group(report)["metrics"]["exact_content"]["denominator"] == 0
    assert group(report)["metrics"]["exact_content"]["rate"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer", None),
        ("review_reference", None),
        ("review_date", None),
        ("source_version_id", None),
        ("method", "parser_preannotation"),
    ],
)
def test_confirmed_gold_requires_review_evidence(example, field, value):
    with pytest.raises(ValidationError):
        reference(example, **{field: value})


@pytest.mark.parametrize(
    "permission,origin,classification",
    [
        ("inventory_only", "real", "real_incomplete_bundle"),
        ("denied", "real", "permission_restricted"),
        ("evaluation", "unknown", "unknown_origin"),
    ],
)
def test_access_and_origin_no_semantic_credit(
    tmp_path, permission, origin, classification
):
    raw = tmp_path / "source.html"
    raw.write_bytes(b"<p>Real declaration is not real gold.</p>")
    entry = CorpusEntry(
        entry_id="incomplete",
        origin=origin,
        course_id="cs50_python",
        source_id="source-declared",
        format="html",
        root_key="repo",
        artifacts={
            "raw": "source.html",
            "receipt": "missing.json",
            "parsed": "missing-parsed.json",
        },
        permission=permission,
        permission_reference="test permission declaration",
    )
    report = evaluate(
        CorpusManifest(schema_version=1, dataset_version="v1", entries=(entry,)),
        GoldDataset(schema_version=1, dataset_version="v1", references=()),
        roots={"repo": tmp_path},
        actor=OWNER,
    )
    observed = report.report["inventory"][0]
    assert observed["classification"] == classification
    assert not observed["binding_verified"] and not observed["receipt_verified"]
    assert observed["available"]["raw"] and not observed["available"]["receipt"]
    assert ("raw" in observed["hashes"]) == (permission == "inventory_only")
    assert "missing_gold_reference" in observed["issues"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_version_id", "foreign"),
        ("original_sha256", "0" * 64),
        ("source_id", "foreign"),
    ],
)
def test_source_version_conflicts_never_count(example, field, value):
    report = run(example, [reference(example, **{field: value})])
    assert report.report["results"][0]["issues"] == ["source_version_conflict"]
    assert group(report)["metrics"]["exact_content"]["denominator"] == 0


def test_unicode_whitespace_is_separate_from_exact_code(example):
    normalized = run(example, [reference(example, expected_content="  Hello\n")])
    assert normalized.report["results"][0]["scores"]["normalized_text"]
    assert not normalized.report["results"][0]["scores"]["exact_content"]
    code = next(b for b in example[4].blocks if b.type == "code")
    report = run(
        example,
        [
            reference(
                example,
                dimension="code",
                target_pointer=f"/blocks/{code.order}",
                expected_content='def hello():\n    print("hi")\n',
                expected_occurrences=None,
            )
        ],
    )
    assert report.report["results"][0]["scores"]["exact_content"]
    assert "normalized_text" not in report.report["results"][0]["scores"]


def test_locator_and_structure_mismatches(example):
    from src.content_store.models import ContentLocator

    locator = ContentLocator(
        raw_artifact_sha256=example[4].raw_sha256,
        origin_pointer="/blocks/0",
        page=9,
        time_status="not_applicable",
    )
    report = run(
        example,
        [
            reference(
                example, expected_locator=locator, expected_structure={"type": "table"}
            )
        ],
    )
    assert {"wrong_locator", "structure_mismatch"}.issubset(
        report.report["results"][0]["issues"]
    )


def test_missing_target_and_explicit_duplicate_expectation(example):
    absent = run(example, [reference(example, target_pointer="/blocks/9999")])
    assert "missing_text" in absent.report["results"][0]["issues"]
    duplicate = run(example, [reference(example, expected_occurrences=0)])
    assert "duplicated_text" in duplicate.report["results"][0]["issues"]


@pytest.mark.parametrize(
    "dimension,expected",
    [
        ("table", "A B"),
        ("formula", "x² + y² = z²"),
        ("code", "1  x = 1\n2  print(x)\n3  # Ä"),
    ],
)
def test_pdf_contract_fixture_without_native_parser(tmp_path, dimension, expected):
    bundle, document = material(tmp_path / "pdf", kind="pdf")
    selection = InventorySelection(
        entry_id="pdf",
        kind="material",
        source_id=document.binding.source_id,
        course_id="cs50_python",
        expected_implementation_revision=REVISION,
        bundle=bundle,
    )
    entry = CorpusEntry(
        entry_id="pdf",
        origin="synthetic",
        course_id="cs50_python",
        source_id=selection.source_id,
        format="pdf",
        root_key="pdf",
        permission="evaluation",
        permission_reference="synthetic PDF model contract, no native extraction",
        selection=selection,
    )
    corpus = CorpusManifest(
        schema_version=1, dataset_version="test-v1", entries=(entry,)
    )
    empty = GoldDataset(schema_version=1, dataset_version="test-v1", references=())
    observed = evaluate(
        corpus, empty, roots={"pdf": bundle.workspace}, actor=OWNER
    ).report["inventory"][0]
    block = next(
        b
        for b in document.blocks
        if b.type == ("math" if dimension == "formula" else dimension)
    )
    gold = reference(
        (corpus, empty, None, observed, document, None),
        entry_id="pdf",
        dimension=dimension,
        target_pointer=f"/blocks/{block.order}",
        expected_content=expected,
        expected_occurrences=None,
    )
    report = evaluate(
        corpus,
        GoldDataset(schema_version=1, dataset_version="test-v1", references=(gold,)),
        roots={"pdf": bundle.workspace},
        actor=OWNER,
    )
    assert report.report["results"][0]["scores"]["exact_content"]
    assert report.report["inventory"][0]["classification"] == "synthetic_fixture"


def test_read_only_store_roundtrip_idempotence_and_inputs(example, tmp_path):
    bundle = example[5]
    before = {
        p: p.read_bytes()
        for p in [bundle.raw_path, bundle.normalized_path, bundle.receipt_path]
    }
    store = ContentStore.initialize(tmp_path / "store")
    first = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="test"
    )
    assert not import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="test"
    ).created
    report = run(example, [reference(example)], store=ContentStore(store.root))
    assert report.report["inventory"][0]["content_store_publication"] == "present"
    assert (
        store.read_parsed_payload(first.version.parsed_version_id, actor=OWNER)
        == before[bundle.normalized_path]
    )
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_existing_c13_html_inventory_is_technical_only(example):
    from src.tools_materials.visual_inventory import inventory

    bundle = example[5]
    report = inventory(
        bundle.normalized_path,
        input_root=bundle.workspace,
        raw_path=bundle.raw_path,
        receipt_path=bundle.receipt_path,
    )
    assert report.raw_scan == "complete"
    assert report.assets
    assert all(
        a.review_status in {"requires_visual_review", "uncertain"}
        for a in report.assets
    )


def test_srt_cue_text_and_known_locator(tmp_path):
    from src.content_store.models import ContentLocator

    bundle, document = srt(tmp_path / "srt")
    selection = InventorySelection(
        entry_id="srt",
        kind="srt",
        source_id=bundle.source_id,
        course_id="cs50_python",
        expected_implementation_revision=REVISION,
        bundle=bundle,
    )
    entry = CorpusEntry(
        entry_id="srt",
        origin="synthetic",
        source_id=bundle.source_id,
        course_id="cs50_python",
        format="srt",
        root_key="fixture",
        permission="evaluation",
        permission_reference="synthetic SRT fixture",
        selection=selection,
    )
    corpus = CorpusManifest(
        schema_version=1, dataset_version="test-v1", entries=(entry,)
    )
    empty = GoldDataset(schema_version=1, dataset_version="test-v1", references=())
    observed = evaluate(
        corpus, empty, roots={"fixture": bundle.workspace}, actor=OWNER
    ).report["inventory"][0]
    locator = ContentLocator(
        raw_artifact_sha256=observed["hashes"]["raw"],
        origin_pointer="/segments/0",
        original_segment_id=0,
        time_status="known",
        start=0.1,
        end=3,
    )
    gold = GoldReference(
        gold_id="cue",
        entry_id="srt",
        source_id=bundle.source_id,
        source_version_id=observed["source_version_id"],
        original_sha256=observed["hashes"]["raw"],
        dimension="transcript",
        source_reference="synthetic first cue",
        created_date=date(2026, 10, 18),
        target_pointer="/segments/0",
        expected_content="Hallo Ä\nMehrzeilig",
        expected_locator=locator,
        reference_status="confirmed",
        method="synthetic_reference",
        reviewer="synthetic_fixture_author",
        review_reference="test SRT literal",
        review_date=date(2026, 10, 18),
    )
    report = evaluate(
        corpus,
        GoldDataset(schema_version=1, dataset_version="test-v1", references=(gold,)),
        roots={"fixture": bundle.workspace},
        actor=OWNER,
    )
    assert report.report["results"][0]["status"] == "passed"
    assert document.segments[1].start < document.segments[0].end  # Original overlap.


def test_unicode_normalization_is_never_code_equivalence(tmp_path):
    bundle, document = material(tmp_path / "code", kind="code")
    selection = InventorySelection(
        entry_id="code",
        kind="material",
        source_id=document.binding.source_id,
        course_id="cs50_python",
        expected_implementation_revision=REVISION,
        bundle=bundle,
    )
    entry = CorpusEntry(
        entry_id="code",
        origin="synthetic",
        source_id=selection.source_id,
        course_id="cs50_python",
        format="code",
        root_key="fixture",
        permission="evaluation",
        permission_reference="synthetic code literal",
        selection=selection,
    )
    corpus = CorpusManifest(
        schema_version=1, dataset_version="test-v1", entries=(entry,)
    )
    empty = GoldDataset(schema_version=1, dataset_version="test-v1", references=())
    observed = evaluate(
        corpus, empty, roots={"fixture": bundle.workspace}, actor=OWNER
    ).report["inventory"][0]
    metadata = dict(
        gold_id="unicode",
        entry_id="code",
        source_id=selection.source_id,
        source_version_id=observed["source_version_id"],
        original_sha256=document.raw_sha256,
        dimension="text",
        source_reference="synthetic literal",
        created_date=date(2026, 10, 18),
        target_pointer="/blocks/0",
        expected_content="# A\u0308\n",
        reference_status="confirmed",
        method="synthetic_reference",
        reviewer="synthetic_fixture_author",
        review_reference="test code literal",
        review_date=date(2026, 10, 18),
    )
    text = GoldReference(**metadata)
    code = GoldReference(**(metadata | dict(gold_id="code-unicode", dimension="code")))
    report = evaluate(
        corpus,
        GoldDataset(
            schema_version=1, dataset_version="test-v1", references=(text, code)
        ),
        roots={"fixture": bundle.workspace},
        actor=OWNER,
    )
    assert report.report["results"][0]["scores"]["normalized_text"]
    assert not report.report["results"][1]["scores"]["exact_content"]
    assert "normalized_text" not in report.report["results"][1]["scores"]


def test_cli_reproducible_hashes_and_no_overwrite(example, tmp_path):
    corpus, empty, roots, *_ = example
    corpus_path, gold_path = tmp_path / "corpus.json", tmp_path / "gold.json"
    corpus_path.write_text(corpus.model_dump_json())
    gold_path.write_text(empty.model_dump_json())
    assert load_inputs(corpus_path, gold_path) == (corpus, empty)
    output = tmp_path / "report"
    args = [
        "--corpus",
        str(corpus_path),
        "--gold",
        str(gold_path),
        "--root",
        f"fixture={roots['fixture']}",
        "--actor",
        "owner",
        "--course",
        "cs50_python",
        "--output",
        str(output),
    ]
    assert main(args) == 0
    assert main(args) == 2
    report = run(example)
    assert run(example) == report
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert all(
        sha256((output / name).read_bytes()) == digest
        for name, digest in manifest["files"].items()
    )
    with pytest.raises(ValueError, match="overlaps"):
        publish(report, roots["fixture"] / "bad", input_roots=roots.values())
    with pytest.raises(ValidationError):
        EvaluationReport(report=report.report, sha256="0" * 64)


@pytest.mark.parametrize(
    "content",
    [b"broken", b'{"schema_version":1,"schema_version":1}', b'{"schema_version":NaN}'],
)
def test_malformed_files_rejected(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_bytes(content)
    assert (
        main(
            [
                "--corpus",
                str(path),
                "--gold",
                str(path),
                "--root",
                f"repo={tmp_path}",
                "--actor",
                "owner",
                "--course",
                "cs50_python",
                "--output",
                str(tmp_path / "out"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "out").exists()


def test_versioned_inventory_has_no_confirmed_real_gold():
    from src.job_control.models import Principal

    root = Path(__file__).resolve().parents[1]
    data = root / "docs/cs50/evaluation/c23_06"
    corpus, gold = load_inputs(
        data / "corpus_manifest.v1.json", data / "gold_references.v1.json"
    )
    paths = [root / e.artifacts["raw"] for e in corpus.entries if "raw" in e.artifacts]
    before = {p: sha256(p.read_bytes()) for p in paths}
    report = evaluate(
        corpus,
        gold,
        roots={"repository": root},
        actor=Principal(
            subject="evaluation_operator",
            role="operator",
            courses=("cs50x", "cs50_python", "cs50_ai"),
        ),
    )
    assert len(report.report["inventory"]) == 15
    assert report.report["gold_counts"]["confirmed"] == 0
    assert report.report["gold_counts"]["pending_review"] == 5
    assert report.report["gold_counts"]["entries_without_confirmed"] == 15
    assert (
        sum(row["available"].get("raw") is True for row in report.report["inventory"])
        == 9
    )
    assert all(
        metric["denominator"] == 0 and metric["rate"] is None
        for row in report.report["metrics"]
        for metric in row["metrics"].values()
    )
    assert all(
        p.read_bytes() and sha256(p.read_bytes()) == digest
        for p, digest in before.items()
    )
    assert all(
        row["classification"] != "verified_bundle" for row in report.report["inventory"]
    )


@pytest.mark.parametrize("path", ["../private", "/absolute", "a/../b", "a\\b"])
def test_path_declarations_are_explicit(path):
    with pytest.raises(ValidationError):
        CorpusEntry(
            entry_id="bad",
            origin="real",
            course_id="cs50_python",
            format="html",
            root_key="repo",
            artifacts={"raw": path},
            permission="inventory_only",
            permission_reference="test",
        )


def test_incomplete_bundle_and_wrong_declared_hash(example):
    corpus, empty, roots, _, _, bundle = example
    entry = corpus.entries[0].model_copy(update={"raw_sha256": "0" * 64})
    report = evaluate(
        corpus.model_copy(update={"entries": (entry,)}), empty, roots=roots, actor=OWNER
    )
    assert "raw_hash_conflict" in report.report["inventory"][0]["issues"]
    assert not report.report["inventory"][0]["binding_verified"]
    bundle.receipt_path.unlink()  # Only this test's synthetic bundle.
    report = run(example, [reference(example)])
    assert not report.report["inventory"][0]["binding_verified"]
    assert report.report["results"][0]["status"] == "not_evaluable"


def test_corpus_origin_cannot_promote_synthetic_gold(example):
    corpus, empty, roots, *_ = example
    real = corpus.model_copy(
        update={"entries": (corpus.entries[0].model_copy(update={"origin": "real"}),)}
    )
    with pytest.raises(ValueError, match="independent"):
        evaluate(
            real,
            GoldDataset(
                schema_version=1,
                dataset_version="test-v1",
                references=(reference(example),),
            ),
            roots=roots,
            actor=OWNER,
        )


@pytest.mark.parametrize(
    "field,value",
    [("material_id", "wrong"), ("format", "code"), ("section_keys", ("foreign",))],
)
def test_complete_bundle_conflicting_metadata_is_not_verified(example, field, value):
    corpus, empty, roots, *_ = example
    changed = corpus.model_copy(
        update={"entries": (corpus.entries[0].model_copy(update={field: value}),)}
    )
    report = evaluate(changed, empty, roots=roots, actor=OWNER)
    assert not report.report["inventory"][0]["binding_verified"]
    assert "bundle_snapshot_conflict" in report.report["inventory"][0]["issues"]
