"""Receipt, crash and fake-provider tests; no productive artifacts or SDKs."""

import json
from pathlib import Path

import httpx
import pytest
from test_cs50_knowledge_pilot import controlled_settings as controlled_settings

from scripts import cs50_knowledge_pilot as cli
from src.model_knowledge.data_knowledge import ChunkKnowledgeResult, TranscriptChunk
from src.tools_knowledge import cs50_checkpoint as contract
from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    CheckpointStore,
    JobIdentity,
    fingerprint,
)


def sample():
    chunk = TranscriptChunk(
        chunk_id="chunk_0000",
        segment_ids=[0],
        start=0,
        end=5,
        text="Python input accepts a prompt.",
        n_words=6,
    )
    identity = JobIdentity(
        course_id="cs50_python",
        section_key="0",
        lecture_id="lecture",
        resource_id="srt",
        source_id="srt",
        raw_sha256="a" * 64,
        transcript_sha256="b" * 64,
        input_binding_sha256="c" * 64,
        chunking={"target_duration": 45, "max_duration": 75, "overlap_segments": 2},
        chunk_plan_sha256=fingerprint([chunk.model_dump(mode="json")]),
        selected_chunks=(chunk.chunk_id,),
        prompt_version="knowledge_extraction_v1",
        prompt_sha256="d" * 64,
        result_schema_sha256="e" * 64,
        evidence_mode="chunk",
        evidence_version="chunk_v1",
        provider="fake",
        model="fake",
        execution_mode="llm",
        request_limits={"max_chunks": 1},
    )
    result = ChunkKnowledgeResult.model_validate(
        {
            "analysis": {"chunk_id": chunk.chunk_id, "relevant": False},
            "extraction": None,
        }
    )
    values = {
        "provider": result.model_dump(mode="json"),
        "result": result.model_dump(mode="json"),
        "evidence": {"source_id": "srt", "items": []},
    }
    return identity, chunk, values


def validate(values):
    return ChunkKnowledgeResult.model_validate(values["result"])


def test_success_roundtrip_and_reuse(tmp_path):
    identity, chunk, values = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        assert store.reuse(chunk.chunk_id, validate) is None
        store.reserve(chunk.chunk_id, {"attempt": 1, "reserved_tokens": 100})
        store.complete(chunk.chunk_id, values, {"validated": True}, validate)
        assert store.state.chunks[chunk.chunk_id].status == "done"
        assert (
            type(store.state).model_validate_json(store.state.model_dump_json())
            == store.state
        )
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        assert store.reuse(chunk.chunk_id, validate)[0] == validate(values)
        assert store.state.chunks[chunk.chunk_id].reservation["attempt"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("transcript_sha256", "f" * 64),
        ("raw_sha256", "f" * 64),
        ("prompt_version", "v2"),
        ("prompt_sha256", "f" * 64),
        ("evidence_version", "v2"),
        ("evidence_mode", "segment_v1"),
        ("source_id", "other"),
        ("lecture_id", "other"),
        ("provider", "other"),
        ("model", "other"),
        ("chunk_plan_sha256", "f" * 64),
        ("chunking", {"target_duration": 20}),
        ("execution_mode", "offline"),
    ],
)
def test_identity_conflict(tmp_path, field, value):
    identity, chunk, _ = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked():
        pass
    altered = JobIdentity.model_validate({**identity.model_dump(), field: value})
    with pytest.raises(CheckpointConflict, match="identity conflict"):
        with CheckpointStore(tmp_path, altered, [chunk]).locked():
            pass


@pytest.mark.parametrize("state", ["request_reserved", "in_flight", "unknown"])
def test_unknown_never_retries(tmp_path, state):
    identity, chunk, _ = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        store.transition(chunk.chunk_id, "request_reserved", reservation={"attempt": 1})
        if state != "request_reserved":
            store.transition(chunk.chunk_id, "in_flight")
        if state == "unknown":
            store.transition(chunk.chunk_id, "unknown")
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        assert store.state.chunks[chunk.chunk_id].status == "unknown"
        with pytest.raises(CheckpointConflict, match="automatic retry forbidden"):
            store.reuse(chunk.chunk_id, validate)
        with pytest.raises(CheckpointConflict, match="Forbidden"):
            store.transition(chunk.chunk_id, "pending")


@pytest.mark.parametrize("after_publication", [False, True])
def test_crash_before_done(tmp_path, monkeypatch, after_publication):
    identity, chunk, values = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        store.reserve(chunk.chunk_id, {"attempt": 1})
        if after_publication:
            original = store.transition

            def crash(cid, status, **fields):
                if status == "done":
                    raise RuntimeError("crash before marker")
                original(cid, status, **fields)

            monkeypatch.setattr(store, "transition", crash)
        else:
            original = contract.atomic_json

            def crash(path, value, **kwargs):
                if Path(path).name == "provider.json":
                    raise RuntimeError("crash before publication")
                original(path, value, **kwargs)

            monkeypatch.setattr(contract, "atomic_json", crash)
        with pytest.raises(RuntimeError):
            store.complete(chunk.chunk_id, values, {}, validate)
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        assert store.state.chunks[chunk.chunk_id].status == "prepared"
        if after_publication:
            assert store.reuse(chunk.chunk_id, validate)[0] == validate(values)
            assert store.state.chunks[chunk.chunk_id].status == "done"
        else:
            with pytest.raises(CheckpointConflict, match="Missing/corrupt"):
                store.reuse(chunk.chunk_id, validate)
            assert store.state.chunks[chunk.chunk_id].status != "done"


@pytest.mark.parametrize(
    "kind", ["receipt", "hash", "invalid_json", "invalid_model", "missing"]
)
def test_corruption_conflicts_preserve_files(tmp_path, kind):
    identity, chunk, values = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        store.reserve(chunk.chunk_id, {"attempt": 1})
        store.complete(chunk.chunk_id, values, {}, validate)
    receipt = tmp_path / "checkpoint.v1.json"
    result = tmp_path / fingerprint(chunk.chunk_id) / "result.json"
    if kind == "receipt":
        receipt.write_text("{bad")
    elif kind == "missing":
        result.unlink()
    else:
        result.write_text("{bad" if kind == "invalid_json" else "{}")
        if kind in ("invalid_json", "invalid_model"):
            import hashlib

            state = json.loads(receipt.read_text())
            state["chunks"][chunk.chunk_id]["artifacts"]["result"] = hashlib.sha256(
                result.read_bytes()
            ).hexdigest()
            receipt.write_text(json.dumps(state))
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
    with pytest.raises(CheckpointConflict):
        with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
            store.reuse(chunk.chunk_id, validate)
    assert all(p.read_bytes() == body for p, body in before.items())


def test_concurrent_lock_and_exclusive_publication(tmp_path):
    identity, chunk, values = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        with pytest.raises(CheckpointConflict, match="already locked"):
            with CheckpointStore(tmp_path, identity, [chunk]).locked():
                pytest.fail("two writers")
        store.reserve(chunk.chunk_id, {"attempt": 1})
        store.complete(chunk.chunk_id, values, {}, validate)
        with pytest.raises(CheckpointConflict, match="Forbidden"):
            store.complete(chunk.chunk_id, values, {}, validate)
    target = tmp_path / "exclusive.json"
    contract.atomic_json(target, {"one": 1})
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        contract.atomic_json(target, {"two": 2})
    assert target.read_bytes() == original


def test_unreceipted_files_and_symlinks(tmp_path):
    identity, chunk, _ = sample()
    (tmp_path / "unreceipted.json").write_text("{}")
    with pytest.raises(CheckpointConflict, match="without checkpoint"):
        with CheckpointStore(tmp_path, identity, [chunk]).locked():
            pass
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(CheckpointConflict, match="Symlink"):
        with CheckpointStore(alias, identity, [chunk]).locked():
            pass


@pytest.fixture
def pilot_input(controlled_settings, tmp_path):
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        CS50KnowledgeInputManifest,
        bind_cs50_knowledge_input,
        save_knowledge_manifest,
    )
    from src.tools_lecture.execute_cs50 import CS50Executor

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plan_path = (
        Path(__file__).resolve().parents[1]
        / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"
    )
    plan = CS50AdapterPlan.model_validate_json(plan_path.read_bytes())
    body = b"1\n00:00:00,000 --> 00:00:05,000\nPython input accepts a prompt.\n\n2\n00:00:05,000 --> 00:00:10,000\nThe print function displays a message.\n\n3\n00:00:10,000 --> 00:00:11,000\n\n"
    executor = CS50Executor(
        plan,
        workspace=workspace,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=body)
        ),
    )
    binding = executor.select(course="cs50_python", section="0")[0]
    executor.run(binding)
    input = bind_cs50_knowledge_input(plan, binding, workspace=workspace)
    manifest = workspace / "input.json"
    save_knowledge_manifest(CS50KnowledgeInputManifest(inputs=(input,)), manifest)
    return {
        "plan": str(plan_path),
        "manifest": str(manifest),
        "workspace": str(workspace),
        "execute_llm": True,
        "probe_marvin": False,
        "provider": "openai_http",
        "model": "fake",
        "max_chunks": 1,
        "token_budget": 60000,
        "input_limit": 28000,
        "output_limit": 1200,
        "checkpoint_dir": str(tmp_path / "checkpoint"),
    }


@pytest.mark.parametrize("mode", ["chunk", "segment_v1"])
def test_worker_fake_provider_resume(pilot_input, tmp_path, monkeypatch, mode):
    from src.tools_knowledge import cs50_extraction_provider as providers

    calls = []
    original = providers.OpenAIHTTPProvider

    def handle(request):
        calls.append(request)
        assert (
            json.loads(
                (Path(pilot_input["checkpoint_dir"]) / "checkpoint.v1.json").read_text()
            )["chunks"]["chunk_0000"]["status"]
            == "in_flight"
        )
        raw = {
            "analysis": {"chunk_id": "chunk_0000", "relevant": True},
            "extraction": {
                "chunk_id": "chunk_0000",
                "statements": [
                    {
                        "statement_id": "S1",
                        "text": "Python input accepts a prompt.",
                        "semantic_type": "statement",
                        "segment_ids": [0],
                        "start": 999,
                        "end": 1000,
                    }
                ],
                "formulas": [],
            },
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(raw)}}
                ]
            },
        )

    monkeypatch.setattr(
        providers,
        "OpenAIHTTPProvider",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(handle)),
    )
    monkeypatch.setenv("CS50_KNOWLEDGE_EXECUTE_LLM", "1")
    configuration = {**pilot_input, "evidence_mode": mode}
    outputs = []
    for i in range(2):
        run = tmp_path / f"run-{i}"
        run.mkdir()
        cli.save(run / "configuration.json", configuration)
        assert cli.worker(run / "configuration.json") == 0
        outputs.append(json.loads((run / "extraction.json").read_text()))
    assert len(calls) == 1
    assert outputs[0] == outputs[1]
    report = json.loads((run / "worker_result.json").read_text())
    assert report["requests"] == 0 and report["results"][0]["reused"]
    assert report["result_origin"] == "LLM"
    statement = outputs[1]["chunks"][0]["extraction"]["statements"][0]
    assert statement["start"] == 0
    assert statement["segment_ids"] == ([0] if mode == "segment_v1" else [0, 1])
    assert (
        json.loads((run / "consolidated.json").read_text())["source_id"]
        == outputs[1]["source_id"]
    )


def test_fake_dispatch_failure_no_retry(pilot_input, tmp_path, monkeypatch):
    from src.tools_knowledge import cs50_extraction_provider as providers

    original = providers.OpenAIHTTPProvider
    calls = []

    def handle(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic")

    monkeypatch.setattr(
        providers,
        "OpenAIHTTPProvider",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(handle)),
    )
    monkeypatch.setenv("CS50_KNOWLEDGE_EXECUTE_LLM", "1")
    for i in range(2):
        run = tmp_path / f"run-{i}"
        run.mkdir()
        cli.save(run / "configuration.json", pilot_input)
        assert cli.worker(run / "configuration.json") == 1
    assert len(calls) == 1
    assert (
        json.loads((run / "worker_result.json").read_text())["checkpoint_status"]
        == "unknown"
    )


def test_same_chunk_id_changed_content(tmp_path):
    identity, chunk, _ = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked():
        pass
    changed = chunk.model_copy(update={"text": "different input"})
    with pytest.raises(CheckpointConflict, match="identity conflict"):
        with CheckpointStore(tmp_path, identity, [changed]).locked():
            pass


def test_no_dispatch_if_durable_reservation_fails(monkeypatch):
    from src.tools_knowledge.cs50_extraction_provider import (
        OpenAIHTTPProvider,
        RequestBudget,
    )

    budget = RequestBudget()

    def fail(reservation):
        raise OSError("fsync failure")

    budget.before_dispatch = fail
    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=budget,
        transport=httpx.MockTransport(lambda request: pytest.fail("unsafe dispatch")),
    )
    _, chunk, _ = sample()
    with pytest.raises(OSError, match="fsync failure"):
        provider.extract(chunk, {})
    provider.close()


def test_offline_cli_checkpoint_resume(pilot_input, tmp_path, monkeypatch):
    monkeypatch.chdir(pilot_input["workspace"])
    for i in range(2):
        run = tmp_path / f"offline-{i}"
        assert (
            cli.main(
                [
                    "--plan",
                    pilot_input["plan"],
                    "--manifest",
                    pilot_input["manifest"],
                    "--output",
                    str(run),
                    "--checkpoint-dir",
                    pilot_input["checkpoint_dir"],
                ]
            )
            == 0
        )
    report = json.loads((run / "worker_result.json").read_text())
    assert report["requests"] == 0 and report["results"][0]["reused"]
    assert report["result_origin"] == "synthetic"


def test_cli_checkpoint_output_separation(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--plan",
                "unused",
                "--manifest",
                "unused",
                "--output",
                str(tmp_path / "run"),
                "--checkpoint-dir",
                str(tmp_path / "run" / "checkpoint"),
            ]
        )
    assert not (tmp_path / "run").exists()


def test_concurrent_process_lock(tmp_path):
    import subprocess
    import sys

    identity, chunk, _ = sample()
    bootstrap = """import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from src.tools_knowledge.cs50_checkpoint import CheckpointStore, JobIdentity, CheckpointConflict
from src.model_knowledge.data_knowledge import TranscriptChunk
import json
payload=json.loads(sys.argv[3])
try:
    with CheckpointStore(sys.argv[2], JobIdentity.model_validate(payload['identity']),
                         [TranscriptChunk.model_validate(payload['chunk'])]).locked():
        raise SystemExit(2)
except CheckpointConflict:
    raise SystemExit(0)
"""
    with CheckpointStore(tmp_path, identity, [chunk]).locked():
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                bootstrap,
                str(Path(__file__).resolve().parents[1]),
                str(tmp_path),
                json.dumps(
                    {
                        "identity": identity.model_dump(mode="json"),
                        "chunk": chunk.model_dump(mode="json"),
                    }
                ),
            ],
            timeout=15,
            capture_output=True,
        )
    assert completed.returncode == 0, completed.stderr.decode()


def test_abrupt_process_exit_preserves_reservation(tmp_path):
    import subprocess
    import sys

    identity, chunk, _ = sample()
    bootstrap = """import sys, json, os
sys.path.insert(0, sys.argv[1])
from src.tools_knowledge.cs50_checkpoint import CheckpointStore, JobIdentity
from src.model_knowledge.data_knowledge import TranscriptChunk
payload=json.loads(sys.argv[3])
chunk=TranscriptChunk.model_validate(payload['chunk'])
with CheckpointStore(sys.argv[2], JobIdentity.model_validate(payload['identity']), [chunk]).locked() as store:
    store.reserve(chunk.chunk_id, {'attempt': 1, 'reserved_tokens': 100})
    os._exit(23)
"""
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            bootstrap,
            str(Path(__file__).resolve().parents[1]),
            str(tmp_path),
            json.dumps(
                {
                    "identity": identity.model_dump(mode="json"),
                    "chunk": chunk.model_dump(mode="json"),
                }
            ),
        ],
        timeout=15,
        capture_output=True,
    )
    assert completed.returncode == 23, completed.stderr.decode()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        assert store.state.status == "blocked"
        assert store.state.chunks[chunk.chunk_id].reservation["reserved_tokens"] == 100
        with pytest.raises(CheckpointConflict, match="unknown"):
            store.reuse(chunk.chunk_id, validate)


def test_llm_completion_requires_reservation(tmp_path):
    identity, chunk, values = sample()
    with CheckpointStore(tmp_path, identity, [chunk]).locked() as store:
        with pytest.raises(CheckpointConflict, match="durable request reservation"):
            store.complete(chunk.chunk_id, values, {}, validate)
        assert store.state.chunks[chunk.chunk_id].status == "pending"


def test_worker_checkpoint_inside_source_rejected(pilot_input, tmp_path):
    configuration = dict(pilot_input, execute_llm=False)
    input = json.loads(Path(configuration["manifest"]).read_text())["inputs"][0]
    checkpoint = Path(input["raw_srt_path"]).parent / "checkpoint"
    configuration["checkpoint_dir"] = str(checkpoint)
    run = tmp_path / "unsafe-run"
    run.mkdir()
    cli.save(run / "configuration.json", configuration)
    assert cli.worker(run / "configuration.json") == 1
    assert not checkpoint.exists()
