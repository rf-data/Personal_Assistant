"""Actual B6 artifacts reused by B7 without another import, process or write."""

import json
import socket
import subprocess

import pytest
from test_cs50_code_zip import env as code_env  # noqa: F401
from test_cs50_code_zip import run, snapshot

from scripts import cs50_batch as cli
from src.model_materials.media_plan import Adequacy, EvidenceRef, MediaRequest
from src.tools_materials import batch as api
from src.tools_materials import media_plan


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def integrated(request, monkeypatch):
    env = request.getfixturevalue("code_env")
    assert run(env)["processed_materials"] == 4
    env.batch_path = env.root.parent / "batch.json"
    env.batch_path.write_text(
        json.dumps(
            dict(
                batch=env.batch.model_dump(mode="json"),
                sha256=api.fingerprint(env.batch.model_dump(mode="json")),
            )
        )
    )

    def forbidden(*args, **kwargs):
        pytest.fail("B7 must not run a process or reimport B6 artifacts")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr("src.tools_materials.code_import.run", forbidden)
    return env


def request(env, index=0, *, adequate=True, container=None):
    binding = env.code[index] if index is not None else env.archive
    parent = env.archive if index in (None, 0, 1) else binding
    receipt = env.root / parent.material_id.split(":")[-1] / "import.v1.json"
    ref = EvidenceRef(
        material_id=binding.material_id,
        kind="code",
        workspace=env.root,
        batch=env.batch_path,
        receipt_sha256=api.sha(receipt.read_bytes()),
        container_material_id=container or parent.material_id,
    )
    return MediaRequest(
        manifest=env.manifest,
        course_id="cs50_python",
        lecture_id=binding.lecture_ids[0],
        source_origin="synthetic",
        include_code_indexes=True,
        purpose="synthetic code review",
        resource_probe_root=env.root.parent,
        evidence=(ref,),
        adequacy=(
            Adequacy(
                material_id=binding.material_id,
                raw_sha256=api.sha(env.raw_by_id[binding.source_id]),
                purpose="synthetic code review",
                text="adequate",
                decision_reference="synthetic operator purpose decision",
            ),
        )
        if adequate
        else (),
    )


@pytest.mark.parametrize("index", [0, 1, 2])
def test_code_handoff_satisfies_f0_without_reparse_writes_or_execution(
    integrated, index
):
    env = integrated
    before = snapshot(env.root)
    req = request(env, index)
    first = media_plan.plan(req, env.approvals)
    assert first == media_plan.plan(req, env.approvals)
    media_plan.check_previous(first, first)
    report = first["report"]
    assert report["selected_strategy"] == "F0" and not report["blocked"]
    row = next(
        r
        for r in report["materials"]
        if r["material_id"] == env.code[index].material_id
    )
    assert row["verified"] and row["processed"]
    assert row["adapter"] == "b6_code_handoff"
    assert row["technical_quality"] in {"passed", "passed_with_warnings"}
    assert row["raw_sha256"] == api.sha(env.raw_by_id[env.code[index].source_id])
    assert not report["execution_supported"] and not report["knowledge_fact_verified"]
    assert report["network_requests"] == report["media_operations"] == 0
    assert str(env.root) not in json.dumps(report)
    assert snapshot(env.root) == before


def test_archive_is_provenance_and_not_text_adequacy(integrated):
    report = media_plan.plan(request(integrated, None), integrated.approvals)["report"]
    assert report["selected_strategy"] != "F0"
    row = next(
        r
        for r in report["materials"]
        if r["material_id"] == integrated.archive.material_id
    )
    assert row["verified"] and not row["processed"]
    assert row["adapter"] == "b6_code_archive"
    assert "text" in report["missing_content"]


@pytest.mark.parametrize("index", [0, 1, None])
def test_revoked_member_sibling_or_container_blocks_entire_import_group(
    integrated, index
):
    env = integrated
    req = request(env, adequate=False)
    source = env.code[index] if index is not None else env.archive
    grants = api.Approvals(
        sources=tuple(
            g for g in env.approvals.sources if g.source_id != source.source_id
        )
    )
    report = media_plan.plan(req, grants)["report"]
    assert report["blocked"] and report["selected_strategy"] is None


@pytest.mark.parametrize(
    "target",
    ["raw", "receipt", "normalized", "marker", "extra", "structure", "handoff"],
)
def test_tamper_never_repaired_or_escalated(integrated, target):
    env = integrated
    req = request(env, adequate=False)
    folder = env.root / env.archive.material_id.split(":")[-1]
    if target == "raw":
        path = folder / "raw/source"
    elif target == "receipt":
        path = folder / "import.v1.json"
    elif target == "marker":
        path = env.root / "selection.v1.json"
    elif target == "extra":
        path = folder / "unexpected"
    else:
        suffix = {
            "normalized": "normalized.v1.json",
            "structure": "structure.v1.json",
            "handoff": "handoff.v1.json",
        }[target]
        path = next(folder.rglob(suffix))
    path.write_bytes(b"{}")
    before = snapshot(env.root)
    report = media_plan.plan(req, env.approvals)["report"]
    assert report["blocked"] and report["selected_strategy"] is None
    assert snapshot(env.root) == before


def test_wrong_container_and_pinned_receipt_fail_closed(integrated):
    env = integrated
    req = request(env, adequate=False, container=env.code[2].material_id)
    assert media_plan.plan(req, env.approvals)["report"]["blocked"]
    req = request(env, adequate=False)
    req = req.model_copy(
        update={
            "evidence": (
                req.evidence[0].model_copy(update={"receipt_sha256": "0" * 64}),
            )
        }
    )
    assert media_plan.plan(req, env.approvals)["report"]["blocked"]


def test_malformed_repinned_receipt_is_blocker(integrated):
    env = integrated
    req = request(env, adequate=False)
    folder = env.root / env.archive.material_id.split(":")[-1]
    path = folder / "import.v1.json"
    body = json.loads(path.read_bytes())["receipt"]
    body["members"] = [None]
    path.write_text(json.dumps(dict(receipt=body, sha256=api.fingerprint(body))))
    req = req.model_copy(
        update={
            "evidence": (
                req.evidence[0].model_copy(
                    update={"receipt_sha256": api.sha(path.read_bytes())}
                ),
            )
        }
    )
    assert media_plan.plan(req, env.approvals)["report"]["blocked"]


@pytest.mark.parametrize(
    "command",
    [
        "plan",
        "code",
        "code-inventory",
        "media-plan",
        "transcripts",
        "inventory",
        "download",
        "seal",
        "workflow",
    ],
)
def test_merged_cli_retains_both_lanes(command, capsys):
    with pytest.raises(SystemExit) as error:
        cli.main([command, "--help"])
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "--limits" in help_text
    if command == "plan":
        assert "--include-code-indexes" in help_text


def test_no_implicit_code_index_expansion(integrated):
    req = request(integrated, adequate=False)
    expanded = media_plan.bindings(req)
    legacy = media_plan.bindings(req.model_copy(update={"include_code_indexes": False}))
    assert {b.material_id for b in legacy} <= {b.material_id for b in expanded}
    assert all(
        b.material_id in {v.material_id for v in expanded} for b in integrated.code
    )
    assert len(expanded) > len(legacy)
