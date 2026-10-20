"""Existing evaluation contracts exercised by the fixed synthetic acceptance recipe."""

import json
import socket

import pytest

from scripts.acceptance.dev03_retrieval import run
from scripts.content_retrieval_evaluation import main
from src.content_store.models import sha256


def test_real_http_reviews_fts5_reopen_frozen_metrics_and_no_overwrite(
    tmp_path, monkeypatch
):
    def forbidden(*a, **kw):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    output = tmp_path / "reports"
    report = run(tmp_path / "fixture", output)
    assert (
        report.report.origin == "synthetic"
        and report.report.real_acceptance == "blocked"
    )
    assert report.report.query_count == 5 and report.report.evaluable_queries == 5
    assert (
        report.report.recall_at_k.denominator
        == report.report.mrr_at_k.denominator
        == report.report.ndcg_at_k.denominator
        == 4
    )
    assert (
        report.report.recall_at_k.value
        == report.report.mrr_at_k.value
        == report.report.ndcg_at_k.value
        == 1
    )
    args = [
        "--dataset",
        str(output / "data/dataset.v1.json"),
        "--results",
        str(output / "data/results.v1.json"),
        "--output",
        str(tmp_path / "replay"),
    ]
    assert main(args) == 0
    assert (tmp_path / "replay/report.v1.json").read_bytes() == (
        output / "evaluation/report.v1.json"
    ).read_bytes()
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert all(
        sha256((output / p).read_bytes()) == h for p, h in manifest["files"].items()
    )
    assert main(args) == 2
    with pytest.raises(ValueError):
        run(tmp_path / "fixture", tmp_path / "other-report")
    assert not (tmp_path / "other-report").exists()
    assert str(tmp_path) not in (output / "evaluation/report.v1.json").read_text()
