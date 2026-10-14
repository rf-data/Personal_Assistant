"""Offline HTTP transport and real official SRT import; no inference."""

import importlib
import json
import socket
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRT = b"1\n00:00:00,000 --> 00:00:01,000\nHello\n\n2\n00:00:02,000 --> 00:00:03,000\nWorld\n"


@pytest.fixture(scope="module")
def environment(tmp_path_factory):
    directory = tmp_path_factory.mktemp("executor-settings")
    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(directory)
        for key, value in {
            "ROOT": str(directory),
            "CHROMA_DIR": str(directory / "chroma"),
            "DATA_DIR": str(directory / "data"),
            "WIKI_EN_API": "https://example.invalid",
            "HEADER_AGENT": "offline",
            "HF_API_KEY": "offline",
            "OPENAI_API_KEY": "offline",
        }.items():
            patch.setenv(key, value)

        def forbidden(*args, **kwargs):
            raise AssertionError("Real network forbidden")

        patch.setattr(socket.socket, "connect", forbidden)
        patch.setattr(socket, "getaddrinfo", forbidden)
        module = importlib.import_module("src.tools_lecture.execute_cs50")
        plan = module.CS50AdapterPlan.model_validate_json(
            (ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json").read_bytes()
        )
        yield module, plan
    import sys

    for name in (
        "src.tools_lecture.execute_cs50",
        "src.tools_lecture.adapt_cs50",
        "src.model_lecture.data_resources",
        "src.core.config",
    ):
        sys.modules.pop(name, None)


def setup_executor(environment, tmp_path, body=SRT, codes=(200,), **options):
    module, plan = environment
    calls = []

    def request(req):
        calls.append(str(req.url))
        code = codes[min(len(calls) - 1, len(codes) - 1)]
        if isinstance(code, Exception):
            raise code
        return httpx.Response(code, content=body)

    executor = module.CS50Executor(
        plan,
        workspace=tmp_path,
        transport=httpx.MockTransport(request),
        sleep=lambda _: None,
        **options,
    )
    binding = executor.select(course="cs50_python", section="0")[0]
    return module, executor, binding, calls


def test_all_100_tasks(environment, tmp_path):
    module, plan = environment
    executor = module.CS50Executor(plan, workspace=tmp_path)
    assert len(executor.tasks) == 100 and len(executor.bindings) == 50
    assert all(t.resource_id in executor.bindings for t in executor.tasks.values())
    assert len({t.output_path for t in executor.tasks.values()}) == 100


@pytest.mark.parametrize("body", [SRT, b"\xef\xbb\xbf" + SRT])
def test_success_and_verified_resume(environment, tmp_path, body):
    module, executor, binding, calls = setup_executor(environment, tmp_path, body)
    state = executor.run(binding)
    assert len(calls) == 1
    assert all(v["status"] == "done" for v in state["actions"].values())
    raw = tmp_path / binding.raw_srt_path
    normalized = tmp_path / binding.transcript_json_path
    assert raw.read_bytes() == body
    document = module.validate_document(normalized, binding, raw)
    assert document.provenance.source_url == binding.transcript_url
    assert document.segments[1].start == 2.0
    assert executor.run(binding) == state and len(calls) == 1
    assert not list(raw.parent.glob(".cs50-*"))


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"invalid",
        SRT.replace(b"00:00:01,000", b"broken"),
        b"1\n00:00:00,000 --> 00:00:01,000\n",
        b"\xff",
        SRT.replace(b"00:00:02,000", b"00:00:00,000").replace(
            b"00:00:00,000", b"00:00:04,000", 1
        ),
    ],
)
def test_invalid_srt(environment, tmp_path, body):
    module, executor, binding, calls = setup_executor(environment, tmp_path, body)
    with pytest.raises((ValueError, UnicodeError)):
        executor.run(binding)
    assert (tmp_path / binding.raw_srt_path).exists()
    assert not (tmp_path / binding.transcript_json_path).exists()
    state = json.loads(
        (tmp_path / binding.raw_srt_path).with_name("execution.v1.json").read_text()
    )
    assert [a["status"] for a in state["actions"].values()] == ["done", "failed"]


@pytest.mark.parametrize(
    "codes,count,success",
    [
        ((404,), 1, False),
        ((429, 200), 2, True),
        ((500, 200), 2, True),
        ((503,), 3, False),
        ((httpx.ReadTimeout("timeout"), 200), 2, True),
        ((httpx.ConnectError("interrupted"),), 3, False),
        ((302,), 1, False),
    ],
)
def test_http_retry_limits(environment, tmp_path, codes, count, success):
    module, executor, binding, calls = setup_executor(
        environment, tmp_path, codes=codes
    )
    if success:
        executor.run(binding)
    else:
        with pytest.raises((ValueError, httpx.HTTPError)):
            executor.run(binding)
        assert not (tmp_path / binding.raw_srt_path).exists()
    assert len(calls) == count
    assert not list((tmp_path / binding.raw_srt_path).parent.glob(".cs50-*"))


def test_size_limit(environment, tmp_path):
    module, executor, binding, calls = setup_executor(
        environment, tmp_path, max_bytes=10
    )
    with pytest.raises(ValueError, match="size limit"):
        executor.run(binding)
    assert len(calls) == 1 and not (tmp_path / binding.raw_srt_path).exists()


@pytest.mark.parametrize("kind", ["untracked", "hash", "identity", "provenance"])
def test_conflicts(environment, tmp_path, kind):
    module, executor, binding, calls = setup_executor(environment, tmp_path)
    raw = tmp_path / binding.raw_srt_path
    if kind == "untracked":
        raw.parent.mkdir(parents=True)
        raw.write_bytes(SRT)
    else:
        executor.run(binding)
        if kind == "hash":
            raw.write_bytes(b"altered")
        elif kind == "identity":
            receipt = raw.with_name("execution.v1.json")
            state = json.loads(receipt.read_text())
            state["binding"]["language"] = "fr"
            receipt.write_text(json.dumps(state))
        else:
            normalized = tmp_path / binding.transcript_json_path
            document = json.loads(normalized.read_text())
            document["provenance"]["source_url"] = "https://example.invalid"
            normalized.write_text(json.dumps(document))
            receipt = raw.with_name("execution.v1.json")
            state = json.loads(receipt.read_text())
            for record in state["actions"].values():
                if record["action"] == "parse_subtitle":
                    record["sha256"] = module.digest(normalized)
            receipt.write_text(json.dumps(state))
    with pytest.raises(module.ExecutionConflict):
        executor.run(binding)


def test_crash_after_publication(environment, tmp_path, monkeypatch):
    module, executor, binding, calls = setup_executor(environment, tmp_path)
    original = module.sync_directory
    count = 0

    def crash(directory):
        nonlocal count
        count += 1
        # running receipt, prepared receipt, then publication directory fsync
        if count == 3:
            raise RuntimeError("simulated crash")
        original(directory)

    monkeypatch.setattr(module, "sync_directory", crash)
    with pytest.raises(RuntimeError):
        executor.run(binding)
    monkeypatch.setattr(module, "sync_directory", original)
    executor.run(binding)
    assert len(calls) == 1


def test_failed_download_resume(environment, tmp_path):
    module, executor, binding, calls = setup_executor(
        environment, tmp_path, codes=(httpx.ReadTimeout("timeout"), 200), retries=0
    )
    with pytest.raises(httpx.ReadTimeout):
        executor.run(binding)
    executor.run(binding)
    assert len(calls) == 2


def test_paths_and_symlinks(environment, tmp_path):
    module, executor, binding, calls = setup_executor(environment, tmp_path)
    with pytest.raises(module.ExecutionConflict):
        module.safe_path(tmp_path, tmp_path / ".." / "escape")
    (tmp_path / "data").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(module.ExecutionConflict):
        executor.run(binding)
    assert not calls


def test_real_python0_pilot(environment, tmp_path):
    source = ROOT / "data/lectures/cs50_python/lecture0.srt.txt"
    if not source.exists():
        pytest.skip("Original local CS50 Python0 SRT unavailable")
    module, executor, binding, calls = setup_executor(
        environment, tmp_path, source.read_bytes()
    )
    original_hash = module.digest(source)
    executor.run(binding)
    document = module.validate_document(
        tmp_path / binding.transcript_json_path,
        binding,
        tmp_path / binding.raw_srt_path,
    )
    assert len(document.segments) > 100 and any(not s.text for s in document.segments)
    assert module.digest(source) == original_hash
    assert len(calls) == 1


def test_partial_stream_and_cleanup(environment, tmp_path):
    module, plan = environment

    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            yield SRT * 1000
            raise httpx.ReadError("connection lost after partial write")

    calls = []

    def request(req):
        calls.append(req)
        return httpx.Response(200, stream=Interrupted())

    executor = module.CS50Executor(
        plan,
        workspace=tmp_path,
        transport=httpx.MockTransport(request),
        retries=1,
        sleep=lambda _: None,
    )
    binding = executor.select(course="cs50_python", section="0")[0]
    with pytest.raises(httpx.ReadError):
        executor.run(binding)
    raw = tmp_path / binding.raw_srt_path
    assert not raw.exists() and not list(raw.parent.glob(".cs50-*"))
    assert len(calls) == 2


def test_dependency_contract_rejected(environment):
    module, plan = environment
    value = plan.model_dump(mode="json")
    value["courses"][0]["tasks"][1]["depends_on"] = []
    with pytest.raises(ValueError, match="dependency"):
        module.CS50AdapterPlan.model_validate(value)


def test_cli_default_dry_run(environment, tmp_path, monkeypatch, capsys):
    module, plan = environment
    monkeypatch.chdir(tmp_path)
    module.main(
        [
            "--plan",
            str(ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"),
            "--course",
            "cs50_python",
            "--section",
            "0",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert result["dry_run"] and result["execution_supported"]
    assert not list(tmp_path.iterdir())


def test_total_deadline(environment, tmp_path, monkeypatch):
    module, executor, binding, calls = setup_executor(environment, tmp_path)
    times = iter([0.0, 0.0, 100.0, 100.0])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(times, 100.0))
    with pytest.raises(TimeoutError):
        executor.run(binding)
    assert not (tmp_path / binding.raw_srt_path).exists()


def test_fresh_sync_import(environment, tmp_path):
    import os
    import subprocess
    import sys

    variables = dict(os.environ)
    variables.update(
        {
            "ROOT": str(tmp_path),
            "CHROMA_DIR": str(tmp_path / "chroma"),
            "DATA_DIR": str(tmp_path / "data"),
            "WIKI_EN_API": "https://example.invalid",
            "HEADER_AGENT": "offline",
            "HF_API_KEY": "offline",
            "OPENAI_API_KEY": "offline",
        }
    )
    code = f"""
import sys, socket
sys.path.insert(0, {str(ROOT)!r})
def forbidden(*args, **kwargs):
    raise AssertionError("Network forbidden")
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
socket.socket.connect = forbidden
import src.tools_lecture.execute_cs50
assert not any(name.split(".")[0] in ("marvin", "faster_whisper", "yt_dlp") for name in sys.modules)
print("offline import passed")
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=tmp_path,
        env=variables,
        timeout=20,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "offline import passed" in result.stdout


def test_execute_all_100_with_fake_http(environment, tmp_path):
    module, plan = environment
    calls = []

    def request(req):
        calls.append(str(req.url))
        return httpx.Response(200, content=SRT)

    executor = module.CS50Executor(
        plan, workspace=tmp_path, transport=httpx.MockTransport(request)
    )
    states = [executor.run(binding) for binding in executor.bindings.values()]
    assert len(calls) == 50
    assert sum(len(state["actions"]) for state in states) == 100
    assert all(
        record["status"] == "done"
        for state in states
        for record in state["actions"].values()
    )
    assert len(list(tmp_path.rglob("source.srt"))) == 50
    assert len(list(tmp_path.rglob("transcript.json"))) == 50


def test_concurrent_executor_lock(environment, tmp_path):
    import fcntl

    module, executor, binding, calls = setup_executor(environment, tmp_path)
    raw = tmp_path / binding.raw_srt_path
    raw.parent.mkdir(parents=True)
    with raw.with_name("execution.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with pytest.raises(BlockingIOError):
            executor.run(binding)
    assert not calls


def test_resume_missing_completed_artifact(environment, tmp_path):
    module, executor, binding, calls = setup_executor(environment, tmp_path)
    executor.run(binding)
    (tmp_path / binding.transcript_json_path).unlink()
    with pytest.raises(module.ExecutionConflict, match="missing-file"):
        executor.run(binding)
    assert len(calls) == 1
