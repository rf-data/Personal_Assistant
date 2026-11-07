"""Own synthetic HTML through real retrieval MVP and read-only M1 summary."""

import json
import socket
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_mvp as summary
from src.c27_learning_summary.models import SummaryConfig
from src.content_store.models import canonical
from tests.test_cs50_learning_mvp import HTML, make_case


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def prepare(
    tmp_path, capsys, raw=HTML, config=None, historical=False, monkeypatch=None
):
    if historical:
        with monkeypatch.context() as old:
            old.setattr(mvp, "implementation_identity", lambda: ("a" * 40, "b" * 64))
            case = make_case(tmp_path, raw)
            assert mvp.main(case.argv) == 0
    else:
        case = make_case(tmp_path, raw)
        assert mvp.main(case.argv) == 0
    publication = json.loads(capsys.readouterr().out)["publication"]
    source_id = case.binding.source_id
    parsed_id = publication["parsed_version_id"]
    with mvp.output_root(case.root):
        identity, _, _ = summary.read_source(
            case.root, source_id, parsed_id, "synthetic-operator"
        )
    revision, code_hash = mvp.implementation_identity()
    approval = summary.SummaryApproval(
        schema_version=1,
        status="approved",
        approved_by="synthetic-operator",
        evidence_reference="M1 authorizes these newly authored synthetic HTML bytes only",
        valid_until=datetime.now(UTC) + timedelta(hours=1),
        actions=summary.ACTIONS,
        implementation_revision=revision,
        implementation_sha256=code_hash,
        adapter_version=summary.ADAPTER_VERSION,
        config=config or SummaryConfig(),
        **identity,
    )
    approval_path = tmp_path / "new-summary-approval.json"
    approval_path.write_bytes(canonical(approval.model_dump(mode="json")))
    approval_path.chmod(0o600)
    return SimpleNamespace(
        case=case,
        approval=approval_path,
        target=tmp_path / "new-private-summary",
        argv=[
            "--source-root",
            str(case.root),
            "--source-id",
            source_id,
            "--parsed-version-id",
            parsed_id,
            "--approval",
            str(approval_path),
            "--output-root",
            str(tmp_path / "new-private-summary"),
            "--actor",
            "synthetic-operator",
        ],
    )


def invoke(test, capsys, expected=0):
    assert summary.main(test.argv) == expected
    captured = capsys.readouterr()
    return json.loads(captured.out if expected == 0 else captured.err)


def change_approval(test, **updates):
    approval = json.loads(test.approval.read_bytes())
    approval.update(updates)
    test.approval.write_bytes(canonical(approval))


def test_import_summary_every_claim_original_restart_idempotency(
    tmp_path, capsys, monkeypatch
):
    test = prepare(tmp_path, capsys)
    before = mvp.inventory(test.case.root)

    def forbidden(*args, **kwargs):
        raise AssertionError("parsing, download, FTS or source publication forbidden")

    from src.content_store.store import ContentStore
    from src.tools_materials.download import MaterialDownloader
    from src.tools_materials.processing import MaterialProcessor
    from src.tools_rag.content_index import ContentIndex

    monkeypatch.setattr(MaterialProcessor, "parse", forbidden)
    monkeypatch.setattr(MaterialDownloader, "obtain", forbidden)
    monkeypatch.setattr(ContentIndex, "search_lexical", forbidden)
    monkeypatch.setattr(ContentIndex, "build", forbidden)
    monkeypatch.setattr(ContentStore, "initialize", forbidden)
    first = invoke(test, capsys)
    assert first["status"] == "completed" and first["review_status"] == "unreviewed"
    assert first["provider"] == "fake"
    assert first["coverage"]["input_refs"] == first["coverage"]["processed_refs"]
    assert first["coverage"]["complete_input"] and not first["coverage"]["uncited_refs"]
    evidence = json.loads((test.target / "evidence.json").read_bytes())
    refs = {r["ref_id"]: r for r in first["summary"]["refs"]}
    originals = {b["block_id"]: b for b in evidence["blocks"]}
    native_refs = {r["ref_id"]: r for r in evidence["refs"]}
    for claim in first["summary"]["claims"]:
        assert claim["refs"]
        for ref_id in claim["refs"]:
            ref = refs[ref_id]
            native = native_refs[ref_id]
            block = originals[ref["block_id"]]
            assert claim["text"] in ref["text"]
            assert ref["text"] == block["text"][ref["offset_start"] : ref["offset_end"]]
            assert native["original_locators"] == block["locators"]
            assert native["parsed_version_id"] == first["source"]["parsed_version_id"]
            assert all(
                loc["raw_artifact_sha256"] == first["source"]["raw_sha256"]
                for loc in native["original_locators"]
            )
    target_before = mvp.inventory(test.target)
    monkeypatch.setattr(summary.FakeLLM, "complete", forbidden)
    assert invoke(test, capsys) == first
    assert mvp.inventory(test.target) == target_before
    process = subprocess.run(
        [sys.executable, "-m", "src.cs50_summary_mvp", *test.argv],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == first
    assert mvp.inventory(test.case.root) == before
    assert mvp.inventory(test.target) == target_before
    assert (test.target.stat().st_mode & 0o777) == 0o700


def test_separate_current_approval_preserves_historical_code_identity(
    tmp_path, capsys, monkeypatch
):
    test = prepare(tmp_path, capsys, historical=True, monkeypatch=monkeypatch)
    before = mvp.inventory(test.case.root)
    assert (
        mvp.main(
            [
                "search",
                "--output-root",
                str(test.case.root),
                "--actor",
                "synthetic-operator",
                "--query",
                "input",
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().err)["status"] == "HOLD"
    assert invoke(test, capsys)["status"] == "completed"
    assert mvp.inventory(test.case.root) == before
    assert (
        mvp.load(test.case.root, "approval.json")["implementation_sha256"] == "b" * 64
    )


@pytest.mark.parametrize(
    "updates",
    [
        {"approved_by": "foreign"},
        {"actions": []},
        {"status": "rejected"},
        {"valid_until": "2000-01-01T00:00:00Z"},
        {"implementation_revision": "0" * 40},
        {"implementation_sha256": "0" * 64},
        {"raw_sha256": "0" * 64},
        {"source_id": "foreign"},
        {"source_version_id": "foreign"},
        {"parsed_version_id": "foreign"},
        {"payload_sha256": "0" * 64},
        {"projection_sha256": "0" * 64},
        {"processing_approval_sha256": "0" * 64},
        {"mvp_intent_sha256": "0" * 64},
        {"mvp_state_sha256": "0" * 64},
        {"schema_version": True},
        {"evidence_reference": " "},
        {"config": {"provider": "litellm", "model": "some-model"}},
        {"config": {"retries": 1}},
    ],
)
def test_wrong_approval_no_root_no_source_change(tmp_path, capsys, updates):
    test = prepare(tmp_path, capsys)
    change_approval(test, **updates)
    before = mvp.inventory(test.case.root)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists()
    assert mvp.inventory(test.case.root) == before


@pytest.mark.parametrize(
    "kind", ["input", "raw", "version", "historical_approval", "historical_intent"]
)
def test_changed_source_rejected(tmp_path, capsys, kind):
    test = prepare(tmp_path, capsys)
    if kind == "input":
        (test.case.root / "input.html").write_bytes(b"changed")
    elif kind == "raw":
        # Locate the selected raw blob by the approved hash.
        digest = json.loads(test.approval.read_bytes())["raw_sha256"]
        (
            test.case.root / "store" / "blobs" / "sha256" / digest[:2] / digest
        ).write_bytes(b"changed")
    elif kind == "version":
        test.argv[test.argv.index("--parsed-version-id") + 1] = "foreign-version"
    else:
        path = test.case.root / (
            "approval.json" if kind == "historical_approval" else "intent.json"
        )
        value = json.loads(path.read_bytes())
        value["implementation_sha256"] = "0" * 64
        path.write_bytes(canonical(value))
    before = mvp.inventory(test.case.root)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists() and mvp.inventory(test.case.root) == before


def test_all_pages_over_100_blocks_hold_before_truncation(
    tmp_path, capsys, monkeypatch
):
    raw = HTML.replace(
        b"</main>",
        b"".join(f"<p>Additional block {i}.</p>".encode() for i in range(110))
        + b"</main>",
    )
    test = prepare(tmp_path, capsys, raw=raw)
    pages = []
    original = summary.ContentReader.page

    def record(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        pages.append(len(result.items))
        return result

    monkeypatch.setattr(summary.ContentReader, "page", record)
    before = mvp.inventory(test.case.root)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert len(pages) >= 2 and sum(pages) > 100
    assert not test.target.exists() and mvp.inventory(test.case.root) == before


def test_long_block_all_windows_and_slices(tmp_path, capsys, monkeypatch):
    raw = HTML.replace(
        b"</main>", b"<p>" + b"Unbroken source statement. " * 800 + b"</p></main>"
    )
    test = prepare(tmp_path, capsys, raw=raw)
    offsets = []
    original = summary.ContentReader.block

    def record(self, version, block, actor, query, **kwargs):
        if "start" in query:
            offsets.append(int(query["start"]))
        return original(self, version, block, actor, query, **kwargs)

    monkeypatch.setattr(summary.ContentReader, "block", record)
    report = invoke(test, capsys)
    assert 16384 in offsets and report["coverage"]["complete_input"]
    evidence = mvp.load(test.target, "evidence.json")
    longest = max(evidence["blocks"], key=lambda b: len(b["text"]))
    refs = [
        r for r in report["summary"]["refs"] if r["block_id"] == longest["block_id"]
    ]
    assert "".join(r["text"] for r in refs) == longest["text"]


@pytest.mark.parametrize(
    "kind", ["empty", "unknown", "symlink", "public", "tampered", "pending"]
)
def test_output_protection_and_no_automatic_recovery(tmp_path, capsys, kind):
    test = prepare(tmp_path, capsys)
    if kind in {"tampered", "pending"}:
        invoke(test, capsys)
        path = test.target / ("summary.json" if kind == "tampered" else "state.json")
        path.write_bytes(b"{}")
    elif kind == "symlink":
        test.target.symlink_to(test.case.root, target_is_directory=True)
    else:
        test.target.mkdir(mode=0o700 if kind != "public" else 0o755)
        if kind == "unknown":
            (test.target / "valuable.txt").write_text("retain this")
    before = mvp.inventory(test.case.root)
    files_before = (
        {p: p.read_bytes() for p in test.target.rglob("*") if p.is_file()}
        if kind != "symlink"
        else {}
    )
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert mvp.inventory(test.case.root) == before
    assert all(p.read_bytes() == content for p, content in files_before.items())


def test_source_change_during_generation_is_incomplete(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    original = summary.FakeLLM.complete

    def changed(self, *args, **kwargs):
        (test.case.root / "input.html").write_bytes(
            b"changed by simulated other process"
        )
        return original(self, *args, **kwargs)

    monkeypatch.setattr(summary.FakeLLM, "complete", changed)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert not (test.target / "manifest.json").exists()
    assert mvp.load(test.target, "state.json")["phase"] == "pending"
    assert not (test.target / "summary.json").exists()


def test_omitted_slice_is_rejected_before_dispatch(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    original = summary.source_slices
    monkeypatch.setattr(summary, "source_slices", lambda *args: original(*args)[:-1])
    before = mvp.inventory(test.case.root)
    assert (
        invoke(test, capsys, 2)["reason"]
        == "source slices omit, duplicate or truncate eligible content"
    )
    assert not test.target.exists() and mvp.inventory(test.case.root) == before


def test_unsupported_claim_retains_pending_without_retry(tmp_path, capsys, monkeypatch):
    from src.c27_learning_summary.llm import Reply

    test = prepare(tmp_path, capsys)
    before = mvp.inventory(test.case.root)
    calls = []

    def unsupported(self, messages, **kwargs):
        ref = json.loads(messages[-1]["content"])["excerpt"]["ref_id"]
        calls.append(ref)
        return Reply(
            json.dumps(
                {
                    "claims": [
                        {
                            "category": "concept",
                            "text": "Invented unsupported knowledge",
                            "refs": [ref],
                        }
                    ]
                }
            )
        )

    monkeypatch.setattr(summary.FakeLLM, "complete", unsupported)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert calls and not (test.target / "summary.json").exists()
    assert mvp.load(test.target, "state.json")["phase"] == "pending"
    saved = mvp.inventory(test.target)
    called = len(calls)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert len(calls) == called and mvp.inventory(test.target) == saved
    assert mvp.inventory(test.case.root) == before


@pytest.mark.parametrize(
    "updates",
    [
        {"valid_until": "2000-01-01T00:00:00Z"},
        {"config": {"chunk_chars": 64}},
        {"implementation_sha256": "0" * 64},
    ],
)
def test_repeat_rechecks_current_approval_and_cache_intent(tmp_path, capsys, updates):
    test = prepare(tmp_path, capsys)
    invoke(test, capsys)
    before, saved = mvp.inventory(test.case.root), mvp.inventory(test.target)
    change_approval(test, **updates)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert (
        mvp.inventory(test.case.root) == before and mvp.inventory(test.target) == saved
    )


def test_whitespace_only_slices_are_accounted_for():
    block = SimpleNamespace(
        block_id="b", text="A" * 64 + " " * 64 + "B", aggregation_role="primary"
    )
    refs = [
        SimpleNamespace(
            ref_id="a", block_id="b", text="A" * 64, offset_start=0, offset_end=64
        ),
        SimpleNamespace(
            ref_id="b", block_id="b", text="B", offset_start=128, offset_end=129
        ),
    ]
    assert summary.checked_refs(refs, [block], SummaryConfig(chunk_chars=64)) == [
        {"block_id": "b", "start": 64, "end": 128}
    ]


def test_duplicate_approval_fields_are_rejected(tmp_path, capsys):
    test = prepare(tmp_path, capsys)
    test.approval.write_bytes(
        test.approval.read_bytes()[:-1] + b',"status":"approved"}'
    )
    before = mvp.inventory(test.case.root)
    assert invoke(test, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists() and mvp.inventory(test.case.root) == before
