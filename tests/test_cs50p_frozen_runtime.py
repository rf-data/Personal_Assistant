"""Artifact checks are real; synthetic wheels never count as production evidence."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "deployment/cs50p-download-only"


def load(name):
    spec = importlib.util.spec_from_file_location(name, PACKAGE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wheelhouse = load("wheelhouse")


def synthetic(tmp_path):
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    data = b"not a production wheel"
    wheel = wheels / "example-1.0-py3-none-any.whl"
    wheel.write_bytes(data)
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "example==1.0 --hash=sha256:" + hashlib.sha256(data).hexdigest() + "\n"
    )
    return wheels, wheel, requirements


@pytest.mark.parametrize(
    "case", ["missing", "corrupt", "extra", "duplicate", "symlink"]
)
def test_wheelhouse_refuses_invalid_artifact_sets(tmp_path, case):
    wheels, wheel, requirements = synthetic(tmp_path)
    assert len(wheelhouse.check(wheels, requirements)) == 1
    if case == "missing":
        wheel.unlink()
    elif case == "corrupt":
        wheel.write_bytes(b"changed")
    elif case == "extra":
        (wheels / "unreviewed-1.0-py3-none-any.whl").write_bytes(b"unknown")
    elif case == "duplicate":
        (wheels / "example-1.0-py2.py3-none-any.whl").write_bytes(wheel.read_bytes())
    else:
        wheel.rename(tmp_path / "external.whl")
        wheel.symlink_to(tmp_path / "external.whl")
    with pytest.raises(ValueError):
        wheelhouse.check(wheels, requirements)


def test_production_closure_and_no_development_requirements():
    production = wheelhouse.requirements(wheelhouse.REQUIREMENTS)
    assert set(production) == {
        "annotated-types",
        "anyio",
        "beautifulsoup4",
        "certifi",
        "h11",
        "httpcore",
        "httpx",
        "idna",
        "pydantic",
        "pydantic-core",
        "soupsieve",
        "typing-extensions",
        "typing-inspection",
    }


@pytest.mark.parametrize("case", ["missing", "corrupt"])
def test_real_pip_rejects_invalid_wheelhouse_offline(tmp_path, case):
    # pip is provisioned by ensurepip in a NEW venv; no package cache/index is used.
    import venv

    venv.EnvBuilder(with_pip=True).create(tmp_path / "venv")
    python = tmp_path / "venv/bin/python"
    wheels, wheel, requirements = synthetic(tmp_path)
    if case == "missing":
        wheel.unlink()
        requirements = wheelhouse.REQUIREMENTS
    else:
        wheel.write_bytes(b"corrupted bytes")
    result = subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "install",
            "--no-index",
            "--only-binary=:all:",
            "--require-hashes",
            "--find-links=" + str(wheels),
            "-r",
            str(requirements),
        ],
        capture_output=True,
        text=True,
        env=wheelhouse.environment(),
    )
    assert result.returncode != 0
    assert (
        "DO NOT MATCH THE HASHES"
        if case == "corrupt"
        else "No matching distribution found"
    ) in result.stderr


def test_preflight_commands_are_observational(monkeypatch, tmp_path):
    host = load("host_preflight")
    calls = []
    monkeypatch.setattr(host, "PATHS", (str(tmp_path / "absent"),))
    monkeypatch.setattr(
        host, "command", lambda argv: calls.append(argv) or {"argv": argv}
    )
    before = list(tmp_path.iterdir())
    result = host.collect()
    assert result["read_only"] and result["status"] == "HOLD"
    assert before == list(tmp_path.iterdir())
    assert all(
        a[0] in {"systemctl", "ss", "tailscale", "python3.12", "stat", "cat", "findmnt"}
        for a in calls
    )
    assert all(
        "start" not in a and "stop" not in a and "install" not in a for a in calls
    )


def test_synthetic_smoke_without_worker_dependencies():
    result = subprocess.run(
        [
            sys.executable,
            str(PACKAGE / "runtime_smoke.py"),
            "--source",
            str(ROOT),
        ],
        capture_output=True,
        text=True,
        env=wheelhouse.environment(),
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == dict(
        status="checked",
        synthetic=True,
        transfers=1,
        reused=True,
        processing_enabled=False,
    )
