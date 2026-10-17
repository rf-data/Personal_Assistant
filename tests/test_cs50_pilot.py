"""Pilot preparation needs no Qdrant SDK, model, network or server."""

import importlib.metadata
import json
import socket
import sys
from argparse import Namespace
from types import SimpleNamespace

import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported

from scripts.cs50_transcript_index import client_for, main
from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_knowledge.cs50_checkpoint import fingerprint
from src.tools_rag.cs50_embeddings import FakeEmbedder
from src.tools_rag.cs50_pilot import (
    candidate_inventory,
    embedding_environment,
    pilot_review,
    source_inventory,
)


def inventory(adapter, workspace):
    return source_inventory(
        adapter, workspace=workspace, course="cs50_python", section="0"
    )


def test_inventory_preserves_identity_times_hashes_and_sources(context, tmp_path):
    _, _, _, adapter = context
    binding, source = imported(context, tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    first = inventory(adapter, tmp_path)
    assert first == inventory(adapter, tmp_path)
    assert first["report_sha256"] == fingerprint(
        {k: v for k, v in first.items() if k != "report_sha256"}
    )
    entry = first["sources"][0]
    assert entry["source_id"] == binding.source_id
    assert entry["raw_sha256"] == source.raw_sha256
    assert entry["transcript_sha256"] == source.transcript_sha256
    assert entry["segment_ids"] == [0, 1, 2]
    assert (entry["start"], entry["end"], entry["timed_chunks"]) == (1, 6, 1)
    assert entry["embedding_units"] is None
    assert entry["warnings"] == ["empty_cues_excluded_by_existing_chunker"]
    assert str(tmp_path) not in json.dumps(first)
    assert "Another value" not in json.dumps(first)
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(
    "failure", ["missing", "raw", "transcript", "receipt", "symlink"]
)
def test_inventory_never_adopts_invalid_sources(context, tmp_path, failure):
    _, _, _, adapter = context
    if failure != "missing":
        _, source = imported(context, tmp_path)
        target = {
            "raw": source.raw_srt_path,
            "transcript": source.transcript_json_path,
            "receipt": source.receipt_path,
            "symlink": source.raw_srt_path,
        }[failure]
        if failure == "symlink":
            target.unlink()
            target.symlink_to(tmp_path / "not-read")
        else:
            target.write_bytes(b"corrupt")
    report = inventory(adapter, tmp_path)
    assert report["validated_sources"] == 0
    entry = report["sources"][0]
    assert entry["import_status"] == "unverified"
    assert entry["warnings"] == ["source_binding_or_timing_validation_failed"]
    assert str(tmp_path) not in json.dumps(report)


def test_environment_checks_metadata_only_and_requires_bound_revision(
    tmp_path, monkeypatch
):
    def no_network(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)

    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    revision = "a" * 40
    snapshots = tmp_path / "models--intfloat--multilingual-e5-base" / "snapshots"
    (snapshots / revision).mkdir(parents=True)
    (snapshots / "main").mkdir()
    probe = embedding_environment(cache=tmp_path)
    assert probe["cached_revision_names"] == [revision]
    assert "immutable_model_revision_not_selected" in probe["blockers"]
    assert not probe["weights_integrity_verified"]
    assert not probe["real_inference_executed"]
    assert not probe["downloads_performed"]
    assert str(tmp_path) not in json.dumps(probe)
    with pytest.raises(ValueError, match="immutable"):
        embedding_environment(cache=tmp_path, revision="main")
    assert (
        "selected_model_revision_not_cached"
        in embedding_environment(cache=tmp_path, revision="b" * 40)["blockers"]
    )


def test_preparation_never_claims_executable_plan_or_approval(context, tmp_path):
    _, _, _, adapter = context
    imported(context, tmp_path)
    report = pilot_review(inventory(adapter, tmp_path), {"blockers": []})
    assert report["status"] == "blocked" and report["ingestion_plan"] is None
    assert report["phase_b"] == {"status": "blocked", "approval_received": False}
    assert len(report["selected_sources"]) == 1
    assert report["remote_payload_policy"]["includes_text"] == [
        "text",
        "original_chunk_text",
    ]
    assert report["report_sha256"] == fingerprint(
        {k: v for k, v in report.items() if k != "report_sha256"}
    )


def test_explicit_candidate_does_not_become_validated_source(context, tmp_path):
    from test_cs50_knowledge_input import SRT

    _, _, _, adapter = context
    candidate = tmp_path / "moved-source.srt.txt"
    candidate.write_bytes(SRT)
    rows = candidate_inventory([candidate], workspace=tmp_path)
    assert rows[0]["import_status"] == "unbound_candidate"
    assert rows[0]["segment_ids"] == [0, 1, 2]
    assert (rows[0]["start"], rows[0]["end"]) == (1, 6)
    report = pilot_review(
        inventory(adapter, tmp_path), {"blockers": []}, candidates=rows
    )
    assert report["selected_sources"] == []
    assert len(report["unverified_sources"]) == 1
    assert report["unbound_candidates"] == rows
    candidate.write_text("timeless words")
    assert (
        candidate_inventory([candidate], workspace=tmp_path)[0]["import_status"]
        == "invalid_candidate"
    )
    txt = tmp_path / "timeless.txt"
    txt.write_text("No fabricated start/end")
    assert (
        candidate_inventory([txt], workspace=tmp_path)[0]["import_status"]
        == "invalid_candidate"
    )
    link = tmp_path / "linked.srt"
    link.symlink_to(candidate)
    with pytest.raises(ValueError, match="Symlink"):
        candidate_inventory([link], workspace=tmp_path)
    with pytest.raises(ValueError, match="outside"):
        candidate_inventory([tmp_path.parent / "other.srt"], workspace=tmp_path)
    with pytest.raises(ValueError, match="16"):
        candidate_inventory([candidate] * 17, workspace=tmp_path)


@pytest.mark.parametrize(
    "alias,canonical,flag",
    [
        ("resume", "upload", "--execute-upload"),
        ("verify", "status", None),
        ("retrieve", "search", None),
    ],
)
def test_cli_aliases_preserve_existing_implementation(
    tmp_path, monkeypatch, capsys, alias, canonical, flag
):
    import scripts.cs50_transcript_index as cli

    calls = []
    monkeypatch.setattr(cli, "run_command", lambda args: calls.append(args.command))
    args = [alias, "--workspace", str(tmp_path)]
    assert main(args + ([flag] if flag else [])) == 0
    assert calls == [canonical]
    capsys.readouterr()
    if flag is None:
        with pytest.raises(SystemExit) as error:
            main([*args, "--execute-upload"])
        assert error.value.code == 2


def test_inventory_cli_no_overwrite_and_safe_errors(context, tmp_path, capsys):
    _, _, _, adapter = context
    workspace = tmp_path / "sources"
    imported(context, workspace)
    output = tmp_path / "review.json"
    args = [
        "inventory",
        "--workspace",
        str(workspace),
        "--course",
        "cs50_python",
        "--section",
        "0",
        "--output",
        str(output),
    ]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == json.loads(output.read_bytes())
    original = output.read_bytes()
    assert main(args) == 1
    error = json.loads(capsys.readouterr().err)
    assert error == {
        "status": "failed",
        "stage": "inventory",
        "error_class": "FileExistsError",
    }
    assert output.read_bytes() == original
    with pytest.raises(SystemExit) as error:
        main([*args[:-2], "--execute-upload"])
    assert error.value.code == 2


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid",
        "https://secret:secret@example.invalid",
        "https://example.invalid/path",
        "https://example.invalid?api_key=secret",
        "https://example.invalid#secret",
    ],
)
def test_remote_rejected_before_optional_sdk_or_network(url, monkeypatch):
    monkeypatch.setenv("QDRANT_API_KEY", "synthetic-secret")
    args = Namespace(qdrant_url=url, allow_remote=True, qdrant_local=None)
    with pytest.raises(ValueError):
        client_for(args)


def test_remote_client_tls_no_redirects_no_environment_proxy(monkeypatch):
    calls = []
    monkeypatch.setenv("QDRANT_API_KEY", "synthetic-secret")
    monkeypatch.setitem(
        sys.modules,
        "qdrant_client",
        SimpleNamespace(QdrantClient=lambda **kwargs: calls.append(kwargs)),
    )
    args = Namespace(
        qdrant_url="https://qdrant.example.invalid",
        allow_remote=False,
        qdrant_local=None,
    )
    with pytest.raises(ValueError):
        client_for(args)
    args.allow_remote = True
    client_for(args)
    assert calls == [
        {
            "url": args.qdrant_url,
            "api_key": "synthetic-secret",
            "timeout": 10,
            "cloud_inference": False,
            "prefer_grpc": False,
            "check_compatibility": False,
            "trust_env": False,
            "follow_redirects": False,
        }
    ]


def test_validate_cli_reuses_plan_and_vectors_without_database(
    context, tmp_path, capsys
):
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_rag.cs50_ingestion import build_ingestion_plan, embed_plan

    _, _, _, adapter = context
    workspace = tmp_path / "sources"
    _, source = imported(context, workspace)
    engine = FakeEmbedder(EmbeddingConfig.fake())
    plan = build_ingestion_plan(
        adapter,
        [source],
        KnowledgeSettings(),
        engine,
        workspace=workspace,
        course="cs50_python",
        section="0",
        source_origin="synthetic",
    )
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(plan.model_dump_json())
    vectors = tmp_path / "vectors.json"
    artifact = embed_plan(
        plan, adapter, engine, workspace=workspace, destination=vectors
    )
    args = [
        "validate",
        "--workspace",
        str(workspace),
        "--index-plan",
        str(plan_file),
        "--vectors",
        str(vectors),
    ]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["vector_artifact_id"] == artifact.artifact_id
    assert not result["remote_connected"]
    source.raw_srt_path.write_bytes(b"changed source")
    assert main(args) == 1
    assert str(workspace) not in capsys.readouterr().err
