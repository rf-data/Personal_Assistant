"""M2.1: own synthetic bytes, real Reader and shared M1 engine; no live sources."""

import json
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_batch as batch
from src import cs50_summary_mvp as m1
from src.c27_learning_summary.llm import Reply
from src.c27_learning_summary.models import SummaryConfig
from src.content_store.models import canonical
from tests.test_cs50_learning_mvp import HTML, make_case


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def invoke(argv, capsys, expected=0):
    assert batch.main(argv) == expected
    captured = capsys.readouterr()
    return json.loads(captured.out if expected == 0 else captured.err)


def prepare(tmp_path, capsys, raw=HTML, config=None, limits=None):
    case = make_case(tmp_path, raw)
    assert mvp.main(case.argv) == 0
    publication = json.loads(capsys.readouterr().out)["publication"]
    common = [
        "--source-root",
        str(case.root),
        "--source-id",
        case.binding.source_id,
        "--parsed-version-id",
        publication["parsed_version_id"],
        "--actor",
        "synthetic-operator",
    ]
    config = config or SummaryConfig(max_chunks=32)
    limits = limits or batch.BatchLimits()
    for name, model in (("config", config), ("limits", limits)):
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical(model.model_dump(mode="json")))
        path.chmod(0o600)
    proposed = invoke(
        [
            "plan",
            *common,
            "--config",
            str(tmp_path / "config.json"),
            "--limits",
            str(tmp_path / "limits.json"),
        ],
        capsys,
    )
    assert proposed["status"] == "approval_required" and "approved_by" not in proposed
    plan = batch.BatchPlan.model_validate(proposed["plan"])
    # Explicit fixture approval for this test's newly authored synthetic source only.
    approval = batch.BatchApproval(
        schema_version=2,
        status="approved",
        approved_by="synthetic-operator",
        evidence_reference="M2.1 task explicitly authorizes this synthetic test fixture only",
        valid_until=datetime.now(UTC) + timedelta(hours=1),
        actions=m1.ACTIONS,
        implementation_revision=proposed["implementation_revision"],
        implementation_sha256=proposed["implementation_sha256"],
        adapter_version=batch.ADAPTER_VERSION,
        config=config,
        limits=limits,
        plan=plan,
        **plan.source,
    )
    path = tmp_path / "batch-approval.json"
    path.write_bytes(canonical(approval.model_dump(mode="json")))
    path.chmod(0o600)
    target = tmp_path / "new-batch-summary"
    return SimpleNamespace(
        case=case,
        plan=plan,
        approval=path,
        target=target,
        argv=["run", *common, "--approval", str(path), "--output-root", str(target)],
    )


def change(test, **updates):
    value = json.loads(test.approval.read_bytes())
    value.update(updates)
    test.approval.write_bytes(canonical(value))


def records(test):
    return [
        dict(mvp.load(test.target, f"batch-{b.ordinal:03}.json"), status="checked")
        for b in test.plan.batches
    ]


def own_171():
    # HTML baseline contains 5 primary blocks; these 166 paragraphs give 171.
    return HTML.replace(
        b"</main>",
        b"".join(
            f"<p>Synthetic lecture passage {i:03}.</p>".encode() for i in range(166)
        )
        + b"</main>",
    )


def test_complete_171_reader_pagination_once_boundaries_restart(
    tmp_path, capsys, monkeypatch
):
    test = prepare(tmp_path, capsys, own_171())
    assert test.plan.total_slices == 171
    assert [len(b.refs) for b in test.plan.batches] == [32, 32, 32, 32, 32, 11]
    assert test.plan == batch.BatchPlan.model_validate_json(test.plan.model_dump_json())
    source_before = mvp.inventory(test.case.root)
    pages, reads = [], []
    original_page, original_read = m1.ContentReader.page, m1.read_source

    def page(self, *args, **kwargs):
        result = original_page(self, *args, **kwargs)
        pages.append(len(result.items))
        return result

    def read(*a, **kw):
        reads.append(1)
        return original_read(*a, **kw)

    monkeypatch.setattr(m1.ContentReader, "page", page)
    monkeypatch.setattr(m1, "read_source", read)
    from src.content_store.store import ContentStore
    from src.tools_materials.download import MaterialDownloader
    from src.tools_materials.processing import MaterialProcessor
    from src.tools_rag.content_index import ContentIndex

    def forbidden(*a, **kw):
        raise AssertionError("summary may not parse, download, publish or index")

    for cls, method in (
        (MaterialProcessor, "parse"),
        (MaterialDownloader, "obtain"),
        (ContentStore, "initialize"),
        (ContentIndex, "build"),
        (ContentIndex, "search_lexical"),
    ):
        monkeypatch.setattr(cls, method, forbidden)
    started = time.perf_counter()
    report = invoke(test.argv, capsys)
    processing_seconds = time.perf_counter() - started
    assert reads == [1] and len(pages) == 2 and sum(pages) == 171
    assert report["status"] == "completed" and report["review_status"] == "unreviewed"
    assert (
        report["coverage"]["input_coverage"]
        == report["coverage"]["citation_coverage"]
        == 1
    )
    assert len(report["batch_ids"]) == 6 and len(report["claims"]) == 171
    assert (
        report["coverage"]["input_refs"] == report["coverage"]["processed_refs"] == 171
    )
    refs = {r["ref_id"]: r for r in report["refs"]}
    blocks = {
        b["block_id"]: b for b in mvp.load(test.target, "evidence.json")["blocks"]
    }
    for ref in refs.values():
        block = blocks[ref["block_id"]]
        assert ref["source_id"] == test.plan.source["source_id"]
        assert ref["locators"] == block["locators"]
        assert ref["text"] == block["text"][ref["offset_start"] : ref["offset_end"]]
    for claim in report["claims"]:
        assert all(claim["text"] in refs[r]["text"] for r in claim["refs"])
    saved = mvp.inventory(test.target)
    monkeypatch.setattr(batch.FakeLLM, "complete", forbidden)
    started = time.perf_counter()
    assert invoke(test.argv, capsys) == report
    cache_seconds = time.perf_counter() - started
    started = time.perf_counter()
    child = subprocess.run(
        [sys.executable, "-B", "-m", "src.cs50_summary_batch", *test.argv],
        capture_output=True,
        text=True,
        timeout=90,
    )
    restart_seconds = time.perf_counter() - started
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == report
    assert mvp.inventory(test.target) == saved
    assert mvp.inventory(test.case.root) == source_before
    (tmp_path / "benchmark.json").write_bytes(
        canonical(
            dict(
                processing_seconds=processing_seconds,
                cache_seconds=cache_seconds,
                restart_seconds=restart_seconds,
                stored_output_bytes=sum(
                    p.stat().st_size for p in test.target.rglob("*") if p.is_file()
                ),
                coverage=report["coverage"],
                state=mvp.load(test.target, "state.json"),
                batch_sizes=[len(b.refs) for b in test.plan.batches],
            )
        )
    )


def test_small_source_shared_engine_cache(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    report = invoke(test.argv, capsys)
    assert len(test.plan.batches) == 1 and report["coverage"]["complete_input"]
    from src.c27_learning_summary.store import SummaryStore

    store = SummaryStore(test.target / "engine-000")
    planned = test.plan.batches[0]
    inputs = batch.engine_input(test.plan, planned)
    model = batch.FakeLLM()
    outcome = batch.generate_refs(
        store,
        planned.refs,
        inputs,
        test.plan.config,
        model,
        title="One verified lecture batch",
    )
    assert outcome.from_cache and model.calls == 0


def test_long_blocks_whitespace_exact_coverage_and_determinism(tmp_path, capsys):
    raw = HTML.replace(
        b"</main>", b"<p>" + b"Synthetic statement. " * 1000 + b"</p></main>"
    )
    test = prepare(
        tmp_path, capsys, raw, config=SummaryConfig(max_chunks=4, chunk_chars=1000)
    )
    report = invoke(test.argv, capsys)
    identity, blocks, doc = m1.read_source(
        test.case.root,
        test.plan.source["source_id"],
        test.plan.source["parsed_version_id"],
        "synthetic-operator",
    )
    assert (
        batch.make_plan(identity, blocks, doc, test.plan.config, test.plan.limits)
        == test.plan
    )
    for block in blocks:
        if block.aggregation_role == "primary" and block.text.strip():
            refs = [r for r in report["refs"] if r["block_id"] == block.block_id]
            assert "".join(r["text"] for r in refs) == block.text
    assert len(test.plan.batches) > 1


@pytest.mark.parametrize(
    "kind", ["middle_failure", "unsupported", "uncertainty", "malformed"]
)
def test_partial_failure_holds_without_retry_or_restart(
    tmp_path, capsys, monkeypatch, kind
):
    test = prepare(tmp_path, capsys, config=SummaryConfig(max_chunks=2))
    original = batch.FakeLLM.complete
    calls = []

    def complete(self, messages, **kw):
        calls.append(1)
        if len(calls) == 3:
            if kind == "middle_failure":
                raise RuntimeError("synthetic failure")
            if kind == "malformed":
                return Reply("{malformed")
            reply = original(self, messages, **kw)
            data = json.loads(reply.raw)
            if kind == "unsupported":
                data["claims"][0]["text"] = "Invented statement"
            else:
                data["uncertainties"] = ["Synthetic unresolved issue"]
            return Reply(json.dumps(data))
        return original(self, messages, **kw)

    monkeypatch.setattr(batch.FakeLLM, "complete", complete)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
    assert (test.target / "batch-000.json").exists()
    assert (
        not (test.target / "manifest.json").exists()
        and not (test.target / "summary.json").exists()
    )
    assert len(calls) == 3
    saved, count = mvp.inventory(test.target), len(calls)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert mvp.inventory(test.target) == saved and len(calls) == count


@pytest.mark.parametrize(
    "kind",
    ["missing", "duplicate", "reorder", "refs", "claim", "locator", "review", "hash"],
)
def test_consolidation_rejects_incomplete_or_tampered_batches(tmp_path, capsys, kind):
    test = prepare(tmp_path, capsys, config=SummaryConfig(max_chunks=2))
    invoke(test.argv, capsys)
    items = records(test)
    if kind == "missing":
        items.pop()
    elif kind == "duplicate":
        items[1] = items[0]
    elif kind == "reorder":
        items.reverse()
    elif kind == "refs":
        items[0]["summary"]["refs"].pop()
    elif kind == "claim":
        items[0]["summary"]["sections"][0]["claims"][0]["refs"] = ["0" * 64]
    elif kind == "locator":
        items[0]["summary"]["refs"][0]["locators"][0]["dom"] = "/changed"
    elif kind == "review":
        items[0]["review_status"] = "approved"
    elif kind == "hash":
        items[0]["summary"]["cache_key"] = "0" * 64
    with pytest.raises((batch.Hold, ValueError)):
        batch.consolidate_batches(test.plan, items)


@pytest.mark.parametrize(
    "updates",
    [
        {"schema_version": 1},
        {"adapter_version": m1.ADAPTER_VERSION},
        {"valid_until": "2000-01-01T00:00:00Z"},
        {"approved_by": "foreign"},
        {"implementation_sha256": "0" * 64},
        {"parsed_version_id": "foreign"},
        {"processing_approval_sha256": "0" * 64},
        {"actions": []},
        {"config": {"max_chunks": 1}},
        {"limits": {"requests": 1}},
    ],
)
def test_stale_or_wrong_approval_before_dispatch(
    tmp_path, capsys, monkeypatch, updates
):
    test = prepare(tmp_path, capsys)
    change(test, **updates)

    def forbidden(*a, **kw):
        raise AssertionError("no dispatch without current approval")

    monkeypatch.setattr(batch.FakeLLM, "complete", forbidden)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists()


@pytest.mark.parametrize(
    "kind", ["expired_processing", "changed_processing", "raw", "parsed"]
)
def test_processing_chain_and_original_tampering(tmp_path, capsys, kind):
    test = prepare(tmp_path, capsys)
    if kind in {"expired_processing", "changed_processing"}:
        path = test.case.root / "approval.json"
        data = mvp.load(test.case.root, "approval.json")
        data[
            "valid_until" if kind == "expired_processing" else "implementation_sha256"
        ] = "2000-01-01T00:00:00Z" if kind == "expired_processing" else "0" * 64
        path.write_bytes(canonical(data))
    elif kind == "parsed":
        test.argv[test.argv.index("--parsed-version-id") + 1] = "foreign"
    else:
        digest = test.plan.source["raw_sha256"]
        (
            test.case.root / "store" / "blobs" / "sha256" / digest[:2] / digest
        ).write_bytes(b"tampered")
    before = mvp.inventory(test.case.root)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists() and mvp.inventory(test.case.root) == before


@pytest.mark.parametrize(
    "limit,value",
    [
        ("total_slices", 1),
        ("requests", 1),
        ("batches", 1),
        ("raw_output_bytes", 1),
        ("evidence_bytes", 1),
        ("stored_output_bytes", 1),
    ],
)
def test_total_limits_hold_without_truncation(tmp_path, capsys, limit, value):
    test = prepare(tmp_path, capsys, config=SummaryConfig(max_chunks=2))
    data = json.loads(test.approval.read_bytes())
    data["limits"][limit] = value
    data["plan"]["limits"][limit] = value
    test.approval.write_bytes(canonical(data))
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists()


def test_source_change_during_run_and_deadline(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    original = batch.FakeLLM.complete

    def changed(self, *args, **kwargs):
        (test.case.root / "input.html").write_bytes(b"changed")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(batch.FakeLLM, "complete", changed)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
    assert not (test.target / "summary.json").exists()


def test_global_deadline_exceeded_retains_evidence(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    now = [0]
    monkeypatch.setattr(batch.time, "monotonic", lambda: now[0])
    original = batch.FakeLLM.complete

    def late(self, *a, **kw):
        now[0] = 601
        return original(self, *a, **kw)

    monkeypatch.setattr(batch.FakeLLM, "complete", late)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
    assert list(test.target.glob("engine-*/runs/*/raw/*.json"))


def test_m1_limit_still_32():
    with pytest.raises(ValueError):
        SummaryConfig(max_chunks=33)
    for kwargs in (
        {"total_slices": 513},
        {"batches": 33},
        {"requests": 513},
        {"wall_seconds": 601},
        {"raw_output_bytes": 64_000_001},
    ):
        with pytest.raises(ValueError):
            batch.BatchLimits(**kwargs)


def test_plan_approval_tampering_and_missing_approval(tmp_path, capsys):
    test = prepare(tmp_path, capsys)
    value = json.loads(test.approval.read_bytes())
    value["plan"]["batches"][0]["refs"][0]["text"] = "altered"
    test.approval.write_bytes(canonical(value))
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert not test.target.exists()
    test.approval.unlink()
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"


@pytest.mark.parametrize(
    "kind", ["missing_batch", "changed_batch", "pending", "empty", "unknown", "public"]
)
def test_cache_output_protection(tmp_path, capsys, kind):
    test = prepare(tmp_path, capsys, config=SummaryConfig(max_chunks=2))
    if kind in {"missing_batch", "changed_batch", "pending"}:
        invoke(test.argv, capsys)
        if kind == "missing_batch":
            (test.target / "batch-001.json").unlink()
        else:
            (
                test.target
                / ("batch-001.json" if kind == "changed_batch" else "state.json")
            ).write_bytes(b"{}")
    else:
        test.target.mkdir(mode=0o755 if kind == "public" else 0o700)
        if kind == "unknown":
            (test.target / "valuable.txt").write_text("keep")
            (test.target / "valuable.txt").chmod(0o600)
    saved = {p: p.read_bytes() for p in test.target.rglob("*") if p.is_file()}
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert all(p.read_bytes() == content for p, content in saved.items())


def test_global_cross_batch_contradiction_is_hold(tmp_path, capsys):
    raw = HTML.replace(
        b"</main>", b"<p>Choice is enabled.</p><p>Choice is not enabled.</p></main>"
    )
    test = prepare(tmp_path, capsys, raw, config=SummaryConfig(max_chunks=1))
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert mvp.load(test.target, "state.json")["completed_batches"] == len(
        test.plan.batches
    )
    assert not (test.target / "summary.json").exists()
    assert all(
        mvp.load(test.target, f"batch-{b.ordinal:03}-state.json")["phase"] == "checked"
        for b in test.plan.batches
    )


def test_whitespace_and_aggregation_exclusions(tmp_path, capsys):
    test = prepare(tmp_path, capsys)
    identity, blocks, doc = m1.read_source(
        test.case.root,
        test.plan.source["source_id"],
        test.plan.source["parsed_version_id"],
        "synthetic-operator",
    )
    # Author altered synthetic projections in memory only, never mutate a source root.
    first = blocks[0].model_copy(update={"text": "A" * 64 + " " * 64 + "B"})
    excluded = blocks[1].model_copy(update={"aggregation_role": "reference_projection"})
    blank = blocks[2].model_copy(update={"text": " "})
    new_blocks = (first, excluded, blank, *blocks[3:])
    plan = batch.make_plan(
        identity,
        new_blocks,
        doc,
        SummaryConfig(chunk_chars=64, max_chunks=2),
        batch.BatchLimits(),
    )
    refs = [r for b in plan.batches for r in b.refs if r.block_id == first.block_id]
    assert [r.offset_start for r in refs] == [0, 64, 128]
    assert "".join(r.text for r in refs) == first.text
    assert {b["reason"] for b in plan.excluded_blocks} == {
        "reference_projection",
        "blank_text",
    }


def test_input_and_citation_coverage_have_distinct_units(tmp_path, capsys, monkeypatch):
    test = prepare(tmp_path, capsys)
    original = batch.FakeLLM.complete

    def shorter(self, *args, **kwargs):
        response = json.loads(original(self, *args, **kwargs).raw)
        candidate = response["claims"][0]
        if candidate["category"] not in {"formula", "code"}:
            candidate["text"] = candidate["text"][:3]
        return Reply(json.dumps(response))

    monkeypatch.setattr(batch.FakeLLM, "complete", shorter)
    report = invoke(test.argv, capsys)
    assert report["coverage"]["input_chars"] > sum(
        len(c["text"]) for c in report["claims"]
    )
    assert (
        report["coverage"]["input_coverage"]
        == report["coverage"]["citation_coverage"]
        == 1
    )
    # Slice citation coverage does not assert that every input character is quoted.


@pytest.mark.parametrize("which", ["summary", "processing"])
def test_approval_chain_expiry_between_requests(tmp_path, capsys, monkeypatch, which):
    test = prepare(tmp_path, capsys)
    real_now = datetime.now(UTC)
    latest = (
        real_now + timedelta(hours=2)
        if which == "processing"
        else real_now + timedelta(minutes=45)
    )
    calls = []

    class Clock:
        @classmethod
        def now(cls, zone):
            return real_now if not calls else latest

    original = batch.FakeLLM.complete

    def complete(self, *a, **kw):
        calls.append(1)
        return original(self, *a, **kw)

    # Both approvals are checked before every request; no attestation is modified.
    # The other approval remains valid beyond the simulated expiry.
    if which == "processing":
        change(test, valid_until=(real_now + timedelta(hours=3)).isoformat())
    else:
        change(test, valid_until=(real_now + timedelta(minutes=30)).isoformat())
    monkeypatch.setattr(batch, "datetime", Clock)
    monkeypatch.setattr(batch.FakeLLM, "complete", complete)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert len(calls) == 1
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"


def test_runtime_stored_output_quota_holds_before_global_publication(tmp_path, capsys):
    test = prepare(tmp_path, capsys)
    data = json.loads(test.approval.read_bytes())
    # Enough for initial immutable evidence; intentionally too small for all
    # duplicated Engine/raw/section/result evidence, candidates and global report.
    identity, blocks, doc = m1.read_source(
        test.case.root,
        test.plan.source["source_id"],
        test.plan.source["parsed_version_id"],
        "synthetic-operator",
    )
    size = (
        len(
            canonical(
                dict(
                    plan=test.plan.model_dump(mode="json"),
                    blocks=[b.model_dump(mode="json") for b in blocks],
                )
            )
        )
        + len(test.approval.read_bytes())
        + 4096
    )
    data["limits"]["stored_output_bytes"] = size
    data["plan"]["limits"]["stored_output_bytes"] = size
    # IDs also bind limits, so a genuine new plan is required.
    identity, blocks, doc = m1.read_source(
        test.case.root,
        test.plan.source["source_id"],
        test.plan.source["parsed_version_id"],
        "synthetic-operator",
    )
    limits = batch.BatchLimits.model_validate(data["limits"])
    plan = batch.make_plan(identity, blocks, doc, test.plan.config, limits)
    data["plan"] = plan.model_dump(mode="json")
    test.approval.write_bytes(canonical(data))
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert test.target.exists()
    assert not (test.target / "summary.json").exists()
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
