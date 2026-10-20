"""Offline contracts and actual POSIX process-tree termination."""

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/cs50_llm_smoke.py"
spec = importlib.util.spec_from_file_location("cs50_smoke", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def test_request_budget_disables_repeat_and_failed_requests():
    budget = smoke.RequestBudget(2)
    budget.begin_chunk()
    budget.claim()
    with pytest.raises(RuntimeError, match="retries are disabled"):
        budget.claim()
    budget.begin_chunk()
    budget.claim()
    budget.begin_chunk()
    with pytest.raises(RuntimeError):
        budget.claim()
    failed = smoke.RequestBudget(2)
    failed.failed = True
    with pytest.raises(RuntimeError):
        failed.claim()


def test_cli_offline_default_and_isolated_configuration(tmp_path, monkeypatch):
    transcript = tmp_path / "source.json"
    transcript.write_text("{}")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-must-not-leak")

    def supervise(command, directory, env, timeout):
        plan = json.loads((directory / "plan.json").read_text())
        assert not plan["enable_api"]
        assert plan["max_chunks"] == 1
        assert env["OPENAI_API_KEY"] == "offline-placeholder"
        assert "CS50_SMOKE_ENABLE_API" not in env
        assert str(directory) in env["MARVIN_DATABASE_URL"]
        assert "-I" in command and timeout == 30
        return dict(timed_out=False, returncode=0, runtime_seconds=0)

    monkeypatch.setattr(smoke, "supervise", supervise)
    output = tmp_path / "run"
    assert smoke.main(["--transcript", str(transcript), "--output", str(output)]) == 0
    assert "secret-must-not-leak" not in (output / "report.json").read_text()
    with pytest.raises(FileExistsError):
        smoke.main(["--transcript", str(transcript), "--output", str(output)])


@pytest.mark.parametrize("option,value", [("--max-chunks", "3"), ("--timeout", "0")])
def test_cli_rejects_unbounded_run(tmp_path, option, value):
    with pytest.raises(SystemExit):
        smoke.main(
            [
                "--transcript",
                str(tmp_path / "input"),
                "--output",
                str(tmp_path / "run"),
                option,
                value,
            ]
        )


def test_api_requires_explicit_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    transcript = tmp_path / "source.json"
    transcript.write_text("{}")
    with pytest.raises(SystemExit):
        smoke.main(
            [
                "--transcript",
                str(transcript),
                "--output",
                str(tmp_path / "run"),
                "--enable-api",
            ]
        )
    assert not (tmp_path / "run").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups")
def test_timeout_kills_grandchild_even_when_leader_exits(tmp_path):
    code = """
import subprocess, sys, time
from pathlib import Path
p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path('grandchild.pid').write_text(str(p.pid))
time.sleep(60)
"""
    report = smoke.supervise([sys.executable, "-I", "-c", code], tmp_path, {}, 1)
    assert report["timed_out"] and report["runtime_seconds"] < 6
    pid = int((tmp_path / "grandchild.pid").read_text())
    for _ in range(30):
        stat = Path(f"/proc/{pid}/stat")
        if not stat.exists() or stat.read_text().split()[2] == "Z":
            break  # killed; orphan zombies may await the container's init reaper
        time.sleep(0.02)
    else:
        pytest.fail("Grandchild remained running after timeout")


def test_worker_api_cannot_be_enabled_by_editing_plan(tmp_path, monkeypatch):
    monkeypatch.delenv("CS50_SMOKE_ENABLE_API", raising=False)
    path = tmp_path / "plan.json"
    path.write_text('{"enable_api":true}')
    with pytest.raises(ValueError, match="explicit --enable-api"):
        smoke.worker(path)


def test_real_offline_worker_prepares_schema_before_initialization(
    tmp_path, monkeypatch
):
    transcript = tmp_path / "source.json"
    transcript.write_text(
        json.dumps(
            {
                "source": "synthetic.srt",
                "language": "en",
                "text": "Hello Python",
                "segments": [
                    {"seg_id": 17, "start": 2.0, "end": 12.0, "text": "Hello Python"}
                ],
            }
        )
    )
    real_supervise = smoke.supervise
    code = """
import runpy, sys
from pathlib import Path
class NoMarvin:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'marvin':
            raise RuntimeError('Controlled offline initialization failure')
sys.meta_path.insert(0, NoMarvin())
module = runpy.run_path(sys.argv[1])
sys.exit(module['worker'](Path(sys.argv[2])))
"""

    def supervise(command, directory, env, timeout):
        return real_supervise(
            [
                sys.executable,
                "-I",
                "-c",
                code,
                str(SCRIPT),
                str(directory / "plan.json"),
            ],
            directory,
            env,
            timeout,
        )

    monkeypatch.setattr(smoke, "supervise", supervise)
    output = tmp_path / "run"
    assert smoke.main(["--transcript", str(transcript), "--output", str(output)]) == 1
    report = json.loads((output / "worker.json").read_text())
    assert report["offline_contract_validated"]
    assert report["api_requests"] == 0 and report["phase"] == "failed"
    assert "Controlled offline" in report["error_detail"]
    chunk = json.loads((output / "chunks.json").read_text())[0]
    assert chunk["segment_ids"] == [17] and chunk["start"] == 2 and chunk["end"] == 12


@pytest.mark.optional_sdk
def test_installed_provider_configuration_without_api(tmp_path):
    profile = os.environ.get("CS50_TEST_PROFILE", "offline")
    if profile not in ("offline", "sdk"):
        pytest.fail("CS50_TEST_PROFILE must be offline or sdk")
    if profile == "offline":
        pytest.skip("Explicit default SDK-free CS50 profile; use CS50_TEST_PROFILE=sdk")
    missing = [
        name
        for name in ("openai", "pydantic_ai")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        pytest.fail("SDK profile requires installed packages: " + ", ".join(missing))
    code = """
import asyncio, socket
def forbidden(*args, **kwargs):
    raise AssertionError('Network forbidden')
socket.socket.connect = forbidden
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
import httpx
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
client = AsyncOpenAI(api_key='offline-placeholder', max_retries=0,
    http_client=httpx.AsyncClient(transport=httpx.MockTransport(forbidden), trust_env=False))
model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(openai_client=client))
assert model.model_name == 'gpt-4o-mini' and client.max_retries == 0
asyncio.run(client.close())
"""
    report = smoke.supervise([sys.executable, "-I", "-c", code], tmp_path, {}, 15)
    assert not report["timed_out"] and report["returncode"] == 0, (
        tmp_path / "stderr.log"
    ).read_text()
