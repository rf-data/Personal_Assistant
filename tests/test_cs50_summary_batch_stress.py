"""Synthetic M2.1 release review; existing limits and original source bytes only."""

import json
import math
import resource
import socket
import subprocess
import sys
import time
from collections import Counter

import pytest

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_batch as batch
from src import cs50_summary_mvp as m1
from src.c27_learning_summary.adapter import iter_source_slices
from src.c27_learning_summary.llm import Reply
from src.c27_learning_summary.models import SummaryConfig
from src.content_store.models import (
    ContentBlock,
    ContentLocator,
    canonical,
    fingerprint,
    sha256,
)
from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import ParserConfig
from src.tools_materials.parse_html import parse_html
from tests.test_cs50_learning_mvp import HTML, make_case
from tests.test_cs50_summary_batch import invoke, prepare


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Synthetic release review forbids network access")

    for name in ("connect", "connect_ex", "bind", "listen"):
        monkeypatch.setattr(socket.socket, name, forbidden)
    for name in ("getaddrinfo", "create_connection"):
        monkeypatch.setattr(socket, name, forbidden)


def passage(index, length, *, emoji=False):
    sentence = (
        f"Passage {index:03}: Learners trace variables, compare inputs, follow loops "
        "and explain function calls using Größen, Wörter and λ examples. "
    )
    if emoji:
        sentence = f"Passage {index:03}: " + "🧪" * 100
    return (sentence * math.ceil(length / len(sentence)))[: length - 1] + "."


def source(lengths, *, emoji=False):
    paragraphs = "".join(
        f"<p>{passage(i, length, emoji=emoji)}</p>" for i, length in enumerate(lengths)
    ).encode()
    return HTML.replace(b"</head>", b'<meta charset="utf-8"></head>').replace(
        b"</main>", paragraphs + b"</main>"
    )


def save_metrics(tmp_path, **values):
    values["pytest_process_peak_rss_kib_cumulative"] = resource.getrusage(
        resource.RUSAGE_SELF
    ).ru_maxrss
    (tmp_path / "stress-metrics.json").write_bytes(canonical(values))


def assert_original_slices(refs, identity, blocks):
    """Independently reconstruct every primary original, including UTF-8 bytes."""
    assert len({ref.ref_id for ref in refs}) == len(refs)
    original = {
        block.block_id: block
        for block in blocks
        if block.aggregation_role == "primary" and block.text.strip()
    }
    seen = []
    for block in original.values():
        slices = [ref for ref in refs if ref.block_id == block.block_id]
        cursor = 0
        for ref in slices:
            assert ref.offset_start == cursor
            assert ref.offset_end == cursor + len(ref.text)
            assert ref.locators == block.locators
            assert ref.content_hash == identity["raw_sha256"]
            assert ref.source_id == identity["source_id"]
            assert ref.text == block.text[ref.offset_start : ref.offset_end]
            assert ref.ref_id == fingerprint(
                ref.model_dump(mode="json", exclude={"ref_id"})
            )
            cursor = ref.offset_end
            seen.append(ref.ref_id)
        assert cursor == len(block.text)
        assert "".join(ref.text for ref in slices) == block.text
        assert b"".join(ref.text.encode() for ref in slices) == block.text.encode()
    assert seen == [ref.ref_id for ref in refs]


def assert_coverage(plan, report, blocks):
    refs = [ref for planned in plan.batches for ref in planned.refs]
    assert report["refs"] == [ref.model_dump(mode="json") for ref in refs]
    assert_original_slices(refs, plan.source, blocks)
    original = {
        block.block_id: block
        for block in blocks
        if block.aggregation_role == "primary" and block.text.strip()
    }
    coverage = report["coverage"]
    assert coverage["complete_input"]
    assert coverage["input_refs"] == coverage["processed_refs"] == len(refs)
    assert (
        coverage["input_chars"]
        == coverage["processed_chars"]
        == sum(len(block.text) for block in original.values())
    )
    assert coverage["input_coverage"] == coverage["citation_coverage"] == 1
    assert not coverage["uncited_refs"]
    assert report["status"] == "completed" and report["review_status"] == "unreviewed"
    return refs


@pytest.mark.parametrize("scenario", ["long_block", "lecture_171"])
def test_long_source_run_cache_and_guarded_process_restart(
    tmp_path, capsys, monkeypatch, scenario
):
    lengths = (
        [50_013]
        if scenario == "long_block"
        else [(1200, 1800, 2800)[i % 3] for i in range(166)]
    )
    raw = source(lengths)
    config = SummaryConfig(max_chunks=8 if scenario == "long_block" else 32)
    test = prepare(tmp_path, capsys, raw, config=config)
    assert test.plan.limits == batch.BatchLimits()
    identity, blocks, doc = m1.read_source(
        test.case.root,
        test.plan.source["source_id"],
        test.plan.source["parsed_version_id"],
        "synthetic-operator",
    )
    assert (
        batch.make_plan(identity, blocks, doc, config, batch.BatchLimits()) == test.plan
    )
    expected_blocks = 6 if scenario == "long_block" else 171
    expected_slices = 31 if scenario == "long_block" else 226
    assert len(blocks) == expected_blocks
    assert test.plan.total_slices == test.plan.total_requests == expected_slices
    assert len(test.plan.batches) <= test.plan.limits.batches
    assert expected_slices * 128000 <= test.plan.limits.raw_output_bytes
    requests = [
        batch.request_bytes(r, config) for b in test.plan.batches for r in b.refs
    ]
    assert max(map(len, requests)) <= config.max_input_bytes
    source_before = mvp.inventory(test.case.root)
    old_complete = batch.FakeLLM.complete
    sent, timeouts, raw_bytes = [], [], []

    def complete(self, messages, **kwargs):
        excerpt = json.loads(messages[-1]["content"])["excerpt"]
        sent.append(excerpt)
        timeouts.append(kwargs["timeout"])
        assert kwargs["timeout"] <= min(config.request_timeout, config.wall_seconds)
        assert kwargs["timeout"] <= test.plan.limits.wall_seconds
        result = old_complete(self, messages, **kwargs)
        raw_bytes.append(len(result.raw.encode()))
        return result

    def forbidden(*args, **kwargs):
        raise AssertionError("No dispatch, ingestion or search on this path")

    from src.content_store.store import ContentStore
    from src.tools_materials.download import MaterialDownloader
    from src.tools_materials.processing import MaterialProcessor
    from src.tools_rag.content_index import ContentIndex

    for cls, name in (
        (MaterialProcessor, "parse"),
        (MaterialDownloader, "obtain"),
        (ContentStore, "initialize"),
        (ContentIndex, "build"),
        (ContentIndex, "search_lexical"),
    ):
        monkeypatch.setattr(cls, name, forbidden)
    monkeypatch.setattr(batch.FakeLLM, "complete", complete)
    started = time.perf_counter()
    report = invoke(test.argv, capsys)
    run_seconds = time.perf_counter() - started
    refs = assert_coverage(test.plan, report, blocks)
    assert sent == [ref.model_dump(mode="json") for ref in refs]
    assert len(sent) == expected_slices
    assert sum(len(item["text"].encode()) for item in sent) == sum(
        len(block.text.encode()) for block in blocks
    )
    saved = mvp.inventory(test.target)
    monkeypatch.setattr(batch.FakeLLM, "complete", forbidden)
    started = time.perf_counter()
    assert invoke(test.argv, capsys) == report
    cache_seconds = time.perf_counter() - started
    # Install guards in the child too: the pytest plugin alone does not propagate.
    child_script = """
import json, socket, sys
def forbidden(*a, **kw):
    raise AssertionError('Restart must be offline and have zero FakeLLM calls')
for name in ('connect', 'connect_ex', 'bind', 'listen'):
    setattr(socket.socket, name, forbidden)
socket.getaddrinfo = socket.create_connection = forbidden
from src import cs50_summary_batch as batch
batch.FakeLLM.complete = forbidden
raise SystemExit(batch.main(sys.argv[1:]))
"""
    started = time.perf_counter()
    child = subprocess.run(
        [sys.executable, "-B", "-c", child_script, *test.argv],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    restart_seconds = time.perf_counter() - started
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == report
    assert mvp.inventory(test.target) == saved
    assert mvp.inventory(test.case.root) == source_before
    stored = sum(p.stat().st_size for p in test.target.rglob("*") if p.is_file())
    assert stored <= test.plan.limits.stored_output_bytes
    assert len(canonical(report)) <= test.plan.limits.evidence_bytes
    assert len(test.approval.read_bytes()) <= 8 * 1024 * 1024
    state = mvp.load(test.target, "state.json")
    assert state["phase"] == "ready" and state["requests"] == len(sent)
    assert state["raw_output_bytes"] == sum(raw_bytes)
    assert sum(raw_bytes) <= test.plan.limits.raw_output_bytes
    save_metrics(
        tmp_path,
        scenario=scenario,
        blocks=len(blocks),
        eligible_blocks=expected_blocks,
        slices=expected_slices,
        batch_sizes=[len(b.refs) for b in test.plan.batches],
        raw_html_bytes=len(raw),
        input_chars=sum(len(ref.text) for ref in refs),
        input_text_bytes=sum(len(ref.text.encode()) for ref in refs),
        serialized_request_bytes=sum(map(len, requests)),
        largest_request_bytes=max(map(len, requests)),
        processed_chars=sum(len(item["text"]) for item in sent),
        processed_text_bytes=sum(len(item["text"].encode()) for item in sent),
        coverage=report["coverage"],
        calls=len(sent),
        cache_calls=0,
        restart_calls=0,
        run_seconds=run_seconds,
        cache_seconds=cache_seconds,
        restart_seconds=restart_seconds,
        raw_output_bytes=sum(raw_bytes),
        summary_json_bytes=(test.target / "summary.json").stat().st_size,
        approval_bytes=test.approval.stat().st_size,
        evidence_bytes=(test.target / "evidence.json").stat().st_size,
        stored_output_bytes=stored,
        exit_codes=[0, 0, child.returncode],
        state=state,
        source_unchanged=True,
        output_unchanged_on_restart=True,
        plan_sha256=fingerprint(test.plan.model_dump(mode="json")),
        block_slice_counts=dict(Counter(ref.block_id for ref in refs)),
    )


@pytest.mark.parametrize(
    "scenario,lengths,config,reason",
    [
        (
            "raw_reservation",
            [50_013] * 3,
            SummaryConfig(max_chunks=32, chunk_chars=512),
            "planned worst-case raw output exceeds total budget",
        ),
        (
            "hard_slice_limit",
            [50_013] * 3,
            SummaryConfig(max_chunks=32, chunk_chars=256),
            "total slice/request limit exceeded; no truncation",
        ),
        (
            "utf8_request_limit",
            [8000],
            SummaryConfig(max_chunks=32, chunk_chars=8000),
            "serialized request byte limit exceeded",
        ),
    ],
)
def test_synthetic_planner_oversize_holds_before_dispatch(
    tmp_path, monkeypatch, scenario, lengths, config, reason
):
    raw = source(lengths, emoji=scenario == "utf8_request_limit")
    case = make_case(tmp_path, raw)
    for path in (case.source, case.plan):
        path.chmod(0o600)
    # Planner contract test, not MVP import/retrieval acceptance. Parse our own
    # bytes for real block IDs/DOM locations; construct only typed planner input.
    doc, _ = parse_html(case.binding, raw, ParserConfig(name="html", version="2"))
    blocks = tuple(
        ContentBlock(
            block_id=b.block_id,
            order=b.order,
            type=b.type,
            original_type=b.type,
            payload_pointer=f"/blocks/{b.order}",
            text=b.text,
            data=b.data,
            locators=(
                ContentLocator(
                    raw_artifact_sha256=doc.raw_sha256,
                    origin_pointer=f"/blocks/{b.order}",
                    time_status="not_applicable",
                    **b.location.model_dump(),
                ),
            ),
        )
        for b in doc.blocks
    )
    identity = dict(
        source_id=case.binding.source_id,
        source_version_id=deterministic_id(
            "content_source_version_v1", case.binding.source_id, doc.raw_sha256
        ),
        parsed_version_id=deterministic_id("content_version_v1", doc.document_id),
        raw_sha256=sha256(raw),
        payload_sha256=fingerprint(doc.model_dump(mode="json")),
        projection_sha256=fingerprint([b.model_dump(mode="json") for b in blocks]),
    )
    assert doc.binding == case.binding and doc.raw_sha256 == identity["raw_sha256"]
    catalog, scope, _ = m1.catalog_for(identity, blocks, doc)
    refs = list(
        iter_source_slices(
            *scope,
            catalog.courses[0].weeks[0].units[0].materials,
            config,
            include_whitespace=True,
        )
    )
    assert_original_slices(refs, identity, blocks)
    assert len(blocks) == (6 if scenario == "utf8_request_limit" else 8)
    assert (
        len(refs)
        == {
            "raw_reservation": 299,
            "hard_slice_limit": 593,
            "utf8_request_limit": 6,
        }[scenario]
    )
    assert all(len(ref.text) <= config.chunk_chars for ref in refs)
    before = mvp.inventory(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError("Oversize source must never be dispatched")

    monkeypatch.setattr(batch.FakeLLM, "complete", forbidden)

    # Guard the architectural boundary: this fixture must not depend on a store,
    # Reader, index or the MVP report. make_plan and slicing remain production code.
    def no_import_or_retrieval(*args, **kwargs):
        raise AssertionError("Planner-only fixture must not import or retrieve")

    from src.content_store.reader import ContentReader
    from src.content_store.store import ContentStore
    from src.tools_rag.content_index import ContentIndex

    for cls, name in (
        (mvp, "main"),
        (mvp, "report"),
        (m1, "read_source"),
        (ContentStore, "initialize"),
        (ContentReader, "page"),
        (ContentReader, "block"),
        (ContentIndex, "build"),
        (ContentIndex, "search_lexical"),
    ):
        monkeypatch.setattr(cls, name, no_import_or_retrieval)
    limits = batch.BatchLimits()
    started = time.perf_counter()
    for _ in range(2):
        with pytest.raises(batch.Hold) as error:
            batch.make_plan(identity, blocks, doc, config, limits)
        assert str(error.value) == reason
    duration = time.perf_counter() - started
    assert not calls and mvp.inventory(tmp_path) == before
    assert not case.root.exists()
    assert not (tmp_path / "new-batch-summary").exists()
    assert not list(tmp_path.glob("*batch-approval*"))
    save_metrics(
        tmp_path,
        scenario=scenario,
        blocks=len(blocks),
        eligible_blocks=len(blocks),
        required_slices=len(refs),
        required_batches=math.ceil(len(refs) / config.max_chunks),
        executed_batches=0,
        input_chars=sum(len(ref.text) for ref in refs),
        input_text_bytes=sum(len(ref.text.encode()) for ref in refs),
        raw_html_bytes=len(raw),
        largest_request_bytes=max(len(batch.request_bytes(r, config)) for r in refs),
        raw_reservation_bytes=len(refs) * 128000,
        chunk_chars=config.chunk_chars,
        processed_chars=0,
        processed_text_bytes=0,
        input_coverage=0,
        citation_coverage=0,
        calls=0,
        stored_summary_bytes=0,
        plan_seconds=duration,
        planner_outcomes=["HOLD", "HOLD"],
        cli_exit_codes=None,
        test_boundary="parsed synthetic blocks to production make_plan",
        source_identity=identity,
        config_sha256=fingerprint(config.model_dump(mode="json")),
        limits=limits.model_dump(mode="json"),
        hold_reason=reason,
        source_unchanged=True,
    )


def test_long_source_partial_failure_retains_evidence_without_continuation(
    tmp_path, capsys, monkeypatch
):
    test = prepare(
        tmp_path,
        capsys,
        source([50_013]),
        config=SummaryConfig(max_chunks=8),
    )
    source_before = mvp.inventory(test.case.root)
    original = batch.FakeLLM.complete
    calls = []

    def unsupported(self, *args, **kwargs):
        calls.append(1)
        reply = original(self, *args, **kwargs)
        if len(calls) == 10:
            value = json.loads(reply.raw)
            value["claims"][0]["text"] = "Invented release-review statement."
            return Reply(json.dumps(value))
        return reply

    monkeypatch.setattr(batch.FakeLLM, "complete", unsupported)
    started = time.perf_counter()
    result = invoke(test.argv, capsys, 2)
    duration = time.perf_counter() - started
    assert result["status"] == "HOLD" and len(calls) == 10
    state = mvp.load(test.target, "state.json")
    assert state["phase"] == "HOLD" and state["completed_batches"] == 1
    assert state["requests"] == 10
    assert mvp.load(test.target, "batch-000-state.json")["phase"] == "checked"
    assert mvp.load(test.target, "batch-001-state.json")["phase"] == "HOLD"
    assert not (test.target / "summary.json").exists()
    assert not (test.target / "manifest.json").exists()
    assert not (test.target / "batch-002-state.json").exists()
    raws = list(test.target.glob("engine-*/runs/*/raw/*.json"))
    sections = list(test.target.glob("engine-*/runs/*/sections/*.json"))
    assert len(raws) == len(sections) == 10
    rejected = [
        reason
        for path in sections
        for reason in json.loads(path.read_bytes())["rejected"]
    ]
    assert rejected == ["unsupported_claim_not_verbatim"]
    saved = mvp.inventory(test.target)
    assert invoke(test.argv, capsys, 2)["status"] == "HOLD"
    assert len(calls) == 10 and mvp.inventory(test.target) == saved
    assert mvp.inventory(test.case.root) == source_before
    refs = [ref for b in test.plan.batches for ref in b.refs]
    # The rejected tenth slice was sent, but only nine sections have accepted claims.
    save_metrics(
        tmp_path,
        scenario="long_source_partial_failure",
        blocks=6,
        required_slices=len(refs),
        planned_batch_sizes=[len(b.refs) for b in test.plan.batches],
        input_chars=test.plan.eligible_chars,
        input_text_bytes=sum(len(ref.text.encode()) for ref in refs),
        sent_chars=sum(len(ref.text) for ref in refs[:10]),
        sent_text_bytes=sum(len(ref.text.encode()) for ref in refs[:10]),
        accepted_cited_slices=9,
        raw_files=len(raws),
        section_files=len(sections),
        requests=10,
        run_seconds=duration,
        stored_output_bytes=sum(
            p.stat().st_size for p in test.target.rglob("*") if p.is_file()
        ),
        state=state,
        exit_codes=[2, 2],
        initial_hold_reason=result["reason"],
        underlying_rejection=rejected,
        source_unchanged=True,
        output_unchanged_on_repetition=True,
        complete_input=False,
    )
