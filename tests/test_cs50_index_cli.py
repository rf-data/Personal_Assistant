import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_cs50_ingestion import context as context
from test_cs50_ingestion import index_case as index_case

from scripts.cs50_transcript_index import client_for
from src.tools_rag.cs50_orchestration import prepare_sources
from tests.qdrant_support import qdrant_client as qdrant_client


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "scripts.cs50_transcript_index", *map(str, args)],
        text=True,
        capture_output=True,
        timeout=120,
        env=os.environ.copy(),
        cwd=Path(__file__).resolve().parents[1],
    )


def test_explicit_scope_preview_has_no_writes(context, tmp_path):
    _, _, _, adapter = context
    preview, inputs = prepare_sources(
        adapter, workspace=tmp_path, course="cs50_python", section="0"
    )
    assert preview["dry_run"] and preview["tasks"] == 2 and not inputs
    assert not list(tmp_path.iterdir())
    result = cli(
        "download", "--workspace", tmp_path, "--course", "cs50_python", "--section", "0"
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["tasks"] == 2
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="license"):
        prepare_sources(
            adapter,
            workspace=tmp_path,
            course="cs50_python",
            section="0",
            execute_download=True,
        )


def test_cli_flags_cannot_chain_download_and_upload(tmp_path):
    result = cli(
        "upload", "--workspace", tmp_path, "--execute-download", "--execute-upload"
    )
    assert result.returncode == 2 and "separate commands" in result.stderr
    assert not list(tmp_path.iterdir())


def test_remote_credentials_and_tls_checked_before_connection():
    from argparse import Namespace

    args = Namespace(
        qdrant_url="http://example.invalid", allow_remote=True, qdrant_local=None
    )
    with pytest.raises(ValueError, match="HTTPS"):
        client_for(args)
    args.qdrant_url = "https://secret:password@example.invalid"
    with pytest.raises(ValueError):
        client_for(args)


def test_isolated_cli_embed_upload_status_search(index_case, tmp_path):
    adapter, workspace, _, _, plan, _ = index_case
    plan_file = tmp_path / "index-plan.json"
    plan_file.write_text(plan.model_dump_json())
    vectors = tmp_path / "cli-vectors.json"
    common = ("--workspace", workspace, "--index-plan", plan_file)
    preview = cli("embed", *common, "--vectors", vectors)
    assert preview.returncode == 0 and json.loads(preview.stdout)["dry_run"]
    assert not vectors.exists()
    embed = cli(
        "embed",
        *common,
        "--vectors",
        vectors,
        "--execute-embedding",
        "--course",
        "cs50_python",
        "--section",
        "0",
    )
    assert embed.returncode == 0, embed.stderr
    location, state = tmp_path / "qdrant", tmp_path / "state"
    upload_args = (
        *common,
        "--vectors",
        vectors,
        "--state-root",
        state,
        "--qdrant-local",
        location,
    )
    preview = cli("upload", *upload_args)
    assert preview.returncode == 0 and not location.exists() and not state.exists()
    upload = cli(
        "upload",
        *upload_args,
        "--execute-upload",
        "--create-collection",
        "--course",
        "cs50_python",
        "--section",
        "0",
    )
    assert upload.returncode == 0, upload.stderr
    assert json.loads(upload.stdout)["status"] == "done"
    status = cli("status", *upload_args)
    assert status.returncode == 0 and json.loads(status.stdout)["complete"]
    search = cli(
        "search",
        *common,
        "--qdrant-local",
        location,
        "--query",
        "Python function",
        "--top-k",
        "2",
    )
    assert search.returncode == 0, search.stderr
    hits = json.loads(search.stdout)["hits"]
    assert len(hits) == 2 and all(h["original_source_checked"] for h in hits)
