"""Reproducible offline acceptance: fixture → fake → sources → review → exports."""

import argparse
import json
from pathlib import Path

from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import generate
from src.c27_learning_summary.export import markdown
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import ClaimReview, Review, SummaryConfig
from src.c27_learning_summary.store import SummaryStore


def run(output: Path):
    catalog = load_catalog(
        Path(__file__).resolve().parents[1]
        / "tests/fixtures/lecture_summary/catalog.json"
    )
    store = SummaryStore(output / "store")
    backend = FakeLLM()
    result = generate(
        store,
        catalog,
        "synthetic_cs50p",
        "0",
        "lecture-0",
        ["transcript", "notes", "code"],
        SummaryConfig(),
        backend,
    ).result
    refs = {r.ref_id: r for r in result.refs}
    assert result.state == "ready_for_review"
    assert all(c.text in refs[ref].text for c in result.claims for ref in c.refs)
    store.save_review(
        Review(
            run_id=result.run_id,
            decision="approved",
            reviewer="synthetic-offline-check",
            comment="Synthetic fixture review; not a real course content approval.",
            claims=[
                ClaimReview(claim_id=c.claim_id, rating="correct")
                for c in result.claims
            ],
        )
    )
    calls = backend.calls
    cached = generate(
        store,
        catalog,
        "synthetic_cs50p",
        "0",
        "lecture-0",
        ["transcript", "notes", "code"],
        SummaryConfig(),
        backend,
    )
    assert (
        cached.from_cache
        and cached.result.run_id == result.run_id
        and backend.calls == calls
    )
    (output / "summary.md").write_text(
        markdown(result, store.reviews(result.run_id)), encoding="utf-8"
    )
    (output / "summary.json").write_text(
        store.export_json(result.run_id), encoding="utf-8"
    )
    report = dict(
        run_id=result.run_id,
        sections=len(result.sections),
        claims=len(result.claims),
        cache_reused=True,
        review="approved",
        exports=["summary.md", "summary.json"],
        network_calls=0,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output), indent=2))
