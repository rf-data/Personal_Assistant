"""Only hand-written synthetic originals; never a Loviscach quality rate."""

import copy
import csv
import io
import json
from datetime import date

import pytest
from pydantic import ValidationError

from src.content_store.models import canonical, sha256
from src.model_evaluation.gold_candidates import GoldCandidatePool, candidate_id
from src.tools_evaluation.gold_candidates import (
    OriginalGrant,
    main,
    review_csv,
    validate_originals,
)


@pytest.fixture
def sample(tmp_path):
    root = tmp_path / "originals"
    root.mkdir()
    raw = b"1\n00:00:00,000 --> 00:00:02,000\nSynthetic definition: a square has four equal sides.\n"
    (root / "original.txt").write_bytes(raw)
    question = "How many sides does this synthetic square have?"
    source = dict(
        entry_id="synthetic_square",
        source_id="synthetic_square",
        source_version_id="synthetic_v1",
        course_identity="synthetic_math",
        lecture_identity="shapes",
        root_key="originals",
        original_file="original.txt",
        original_sha256=sha256(raw),
        document_type="srt",
        language="en",
        origin="synthetic",
        permission_reference="synthetic_test_permission",
        parsing_status="not_checked",
    )
    ref = dict(
        gold_id="square_reference",
        entry_id=source["entry_id"],
        source_id=source["source_id"],
        source_version_id=source["source_version_id"],
        original_sha256=sha256(raw),
        dimension="text",
        source_reference="Original line 3",
        created_date=date(2026, 10, 26).isoformat(),
        target_pointer="/lines/3",
        expected_content="four equal sides",
        reference_status="pending_review",
        method="synthetic_reference",
        expected_locator=dict(
            raw_artifact_sha256=sha256(raw),
            origin_pointer="/lines/3",
            line_start=3,
            line_end=3,
            time_status="not_applicable",
        ),
    )
    candidate = dict(
        schema_version=1,
        query=dict(
            schema_version=1,
            query_id=candidate_id(source["entry_id"], question),
            text=question,
        ),
        entry_id=source["entry_id"],
        expected_answer="Four.",
        question_type="fact",
        difficulty="easy",
        generation_method="synthetic_reference",
        review_status="pending_human_review",
        references=[ref],
        needs_visual_context=False,
        visual_context_complete=True,
        evaluability="pending_review",
        revision=1,
        change_note="Synthetic test creation",
    )
    value = dict(
        schema_version=1,
        dataset_version="synthetic-v1",
        origin="synthetic",
        sources=[source],
        candidates=[candidate],
    )
    grants = {
        "originals": OriginalGrant(
            root=root,
            permission_reference=source["permission_reference"],
            origin="synthetic",
            permission="evaluation",
            entry_ids=(source["entry_id"],),
        )
    }
    return value, grants


def test_pending_schema_hashes_review_export_and_stable_ids(sample):
    value, grants = sample
    pool = validate_originals(GoldCandidatePool.model_validate(value), grants)
    assert pool.real_acceptance == "blocked"
    assert pool.candidates[0].references[0].reference_status == "pending_review"
    rows = list(csv.DictReader(io.StringIO(review_csv(pool))))
    assert (
        rows[0]["decision"] == ""
        and rows[0]["sha256"] == pool.sources[0].original_sha256
    )
    edited = copy.deepcopy(value)
    edited["candidates"][0].update(
        expected_answer="Four equal sides.", revision=2, change_note="Clarify answer"
    )
    assert (
        GoldCandidatePool.model_validate(edited).candidates[0].query
        == pool.candidates[0].query
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_id",
        "wrong_id",
        "duplicate_question",
        "hash",
        "version",
        "missing_evidence",
        "missing_source",
        "confirmed",
        "auto_approve",
        "mixed_origin",
        "parser_evidence",
        "absolute_path",
        "traversal",
        "missing_visual",
        "ambiguous",
        "bad_unanswerable",
    ],
)
def test_invalid_candidate_contracts(sample, mutation):
    value, _ = sample
    c, s = value["candidates"][0], value["sources"][0]
    if mutation in {"duplicate_id", "duplicate_question"}:
        value["candidates"].append(copy.deepcopy(c))
        if mutation == "duplicate_question":
            value["sources"].append({**s, "entry_id": "another_source"})
            d = value["candidates"][1]
            d["entry_id"] = "another_source"
            d["query"]["query_id"] = candidate_id("another_source", d["query"]["text"])
            d["references"][0]["entry_id"] = "another_source"
    elif mutation == "wrong_id":
        c["query"]["query_id"] = "wrong"
    elif mutation == "hash":
        c["references"][0]["original_sha256"] = "0" * 64
    elif mutation == "version":
        c["references"][0]["source_version_id"] = "wrong"
    elif mutation == "missing_evidence":
        c["references"] = []
    elif mutation == "missing_source":
        value["sources"] = []
    elif mutation == "confirmed":
        c["references"][0]["reference_status"] = "confirmed"
    elif mutation == "auto_approve":
        c["review_status"] = "approved"
    elif mutation == "mixed_origin":
        s["origin"] = "real"
    elif mutation == "parser_evidence":
        c["references"][0]["method"] = "parser_preannotation"
    elif mutation == "absolute_path":
        s["original_file"] = "/private/original.txt"
    elif mutation == "traversal":
        s["original_file"] = "../original.txt"
    elif mutation == "missing_visual":
        c.update(needs_visual_context=True, visual_context_complete=False)
    elif mutation == "ambiguous":
        c["ambiguity_note"] = "Unclear sign"
    elif mutation == "bad_unanswerable":
        c["question_type"] = "unanswerable"
    with pytest.raises(ValidationError):
        GoldCandidatePool.model_validate(value)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "tampered",
        "symlink",
        "ancestor_symlink",
        "denied",
        "wrong_grant",
        "origin",
    ],
)
def test_explicit_original_provenance(sample, tmp_path, fault):
    value, grants = sample
    original = grants["originals"].root / "original.txt"
    if fault == "missing":
        original.unlink()
    elif fault == "tampered":
        original.write_text("Changed")
    elif fault == "symlink":
        original.unlink()
        original.symlink_to(tmp_path / "elsewhere")
    elif fault == "ancestor_symlink":
        link = tmp_path / "link"
        link.symlink_to(grants["originals"].root, target_is_directory=True)
        grants["originals"] = grants["originals"].model_copy(update={"root": link})
    elif fault == "denied":
        grants = {}
    elif fault == "wrong_grant":
        grants["originals"] = grants["originals"].model_copy(
            update={"entry_ids": ("foreign",)}
        )
    elif fault == "origin":
        grants["originals"] = grants["originals"].model_copy(update={"origin": "real"})
    with pytest.raises((ValueError, OSError)):
        validate_originals(GoldCandidatePool.model_validate(value), grants)


def test_unanswerable_and_incomplete_formula_stay_pending(sample):
    value, _ = sample
    c = value["candidates"][0]
    c.update(
        question_type="unanswerable",
        expected_answer=None,
        unanswerable_scope_note="Only original line 1 examined; human verification pending",
    )
    c["references"][0].update(expected_content="", expected_occurrences=0)
    pool = GoldCandidatePool.model_validate(value)
    assert pool.candidates[0].review_status == "pending_human_review"
    c.update(
        question_type="formula",
        expected_answer="Insufficient visual evidence",
        unanswerable_scope_note=None,
        needs_visual_context=True,
        visual_context_complete=False,
        evaluability="not_evaluable",
    )
    c["references"][0].update(
        expected_content=None, expected_occurrences=None, dimension="formula"
    )
    assert (
        GoldCandidatePool.model_validate(value).candidates[0].formula_original_notation
        is None
    )


def test_export_is_exclusive_outside_original_roots_and_no_promotion(sample, tmp_path):
    value, grants = sample
    dataset, config = tmp_path / "dataset.json", tmp_path / "grants.json"
    dataset.write_bytes(canonical(value))
    config.write_text(
        json.dumps({k: v.model_dump(mode="json") for k, v in grants.items()})
    )
    output = tmp_path / "review.csv"
    argv = [
        "--dataset",
        str(dataset),
        "--grants",
        str(config),
        "--review-csv",
        str(output),
    ]
    assert main(argv) == 0
    before = dataset.read_bytes()
    with pytest.raises(SystemExit):
        main(argv)
    with pytest.raises(SystemExit):
        main(argv[:-1] + [str(grants["originals"].root / "overwrite.csv")])
    assert dataset.read_bytes() == before
    assert not (grants["originals"].root / "overwrite.csv").exists()


def test_csv_formula_injection_is_escaped(sample):
    value, _ = sample
    value["candidates"][0]["expected_answer"] = '=HYPERLINK("bad")'
    rows = list(
        csv.DictReader(io.StringIO(review_csv(GoldCandidatePool.model_validate(value))))
    )
    assert rows[0]["expected_answer"].startswith("'=")


def test_empty_blocked_real_pool_needs_no_material_access():
    pool = GoldCandidatePool(
        schema_version=1,
        dataset_version="loviscach-candidates-v1",
        origin="real",
        sources=(),
        candidates=(),
    )
    assert validate_originals(pool, {}).candidates == ()


def test_nonexistent_original_line_and_contradictory_pointer(sample):
    value, grants = sample
    value["candidates"][0]["references"][0]["expected_locator"]["line_end"] = 20
    with pytest.raises(ValueError, match="line reference"):
        validate_originals(GoldCandidatePool.model_validate(value), grants)
    value["candidates"][0]["references"][0]["expected_locator"]["origin_pointer"] = (
        "/other"
    )
    with pytest.raises(ValidationError):
        GoldCandidatePool.model_validate(value)


def test_invalid_private_grant_config_fails_without_traceback(sample, tmp_path, capsys):
    value, _ = sample
    dataset, grants = tmp_path / "pool.json", tmp_path / "grants.json"
    dataset.write_bytes(canonical(value))
    grants.write_text("[]")
    with pytest.raises(SystemExit) as error:
        main(["--dataset", str(dataset), "--grants", str(grants)])
    assert error.value.code == 2
    assert "candidate validation failed" in capsys.readouterr().err
