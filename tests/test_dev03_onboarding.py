"""Real candidate metadata cannot become source access or synthetic gold."""

from pathlib import Path

import pytest

from src.content_store.models import sha256
from src.model_evaluation.material_evaluation import EvaluationReport
from src.tools_evaluation import evaluate_materials as evaluator
from tests.content_store_support import OWNER

ROOT = Path(__file__).resolve().parents[1] / "docs/cs50/evaluation/dev03/onboarding"


def test_denied_candidates_have_no_source_io_and_no_metrics(tmp_path, monkeypatch):
    corpus, gold = evaluator.load_inputs(
        ROOT / "corpus_manifest.v1.json", ROOT / "gold_references.v1.json"
    )
    assert len(corpus.entries) == 3 and not gold.references
    assert all(
        e.origin == "real"
        and e.permission == "denied"
        and not e.artifacts
        and e.selection is None
        for e in corpus.entries
    )

    def forbidden(*a, **kw):
        raise AssertionError("Real file access forbidden")

    monkeypatch.setattr(evaluator, "_read", forbidden)
    report = evaluator.evaluate(
        corpus, gold, roots={"unapproved": tmp_path / "never-created"}, actor=OWNER
    )
    assert report == evaluator.evaluate(
        corpus,
        gold,
        roots={"unapproved": tmp_path / "another-absent-root"},
        actor=OWNER,
    )
    assert EvaluationReport.model_validate_json(report.model_dump_json()) == report
    assert all(
        not r["hashes"] and not r["binding_verified"]
        for r in report.report["inventory"]
    )
    assert all(
        m["denominator"] == 0 and m["rate"] is None
        for group in report.report["metrics"]
        for m in group["metrics"].values()
    )
    output = tmp_path / "reports"
    evaluator.publish(report, output, input_roots=[tmp_path / "never-created"])
    before = {p.name: sha256(p.read_bytes()) for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        evaluator.publish(report, output, input_roots=[tmp_path / "never-created"])
    assert before == {p.name: sha256(p.read_bytes()) for p in output.iterdir()}
