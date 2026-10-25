"""Negative coverage for profile boundaries and optional dependency handling."""

import importlib
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.test_profiles import command
from tests.offline_guard import pytest_configure as configure_guard
from tests.optional_dependencies import require_qdrant


def test_external_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="--run-external"):
        command("external")
    assert "--run-external" in command("external", run_external=True)
    for profile in ("core", "extended"):
        assert "tests.offline_guard" in command(profile)
        assert "not external_integration" in command(profile)


def test_missing_sdk_has_actionable_skip(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    with pytest.raises(pytest.skip.Exception, match="test-qdrant"):
        require_qdrant()


def test_broken_installed_sdk_is_an_error(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())

    def broken(name):
        raise ModuleNotFoundError("broken installed SDK dependency", name="grpc")

    monkeypatch.setattr(importlib, "import_module", broken)
    with pytest.raises(ModuleNotFoundError, match="broken installed SDK"):
        require_qdrant()


def test_external_fixture_never_runs_without_opt_in(tmp_path):
    sample = tmp_path / "test_external_boundary.py"
    sample.write_text(
        """
import pytest
@pytest.fixture
def forbidden_fixture():
    raise AssertionError('external fixture executed')
def test_real_python0_pilot(forbidden_fixture):
    pass
def test_local_control():
    pass
"""
    )
    sdk_sample = tmp_path / "test_cs50_ingestion.py"
    sdk_sample.write_text(
        """
import pytest
@pytest.fixture
def forbidden_sdk_fixture():
    raise AssertionError('SDK fixture executed without explicit opt-in')
def test_installed_sdk_still_requires_opt_in(forbidden_sdk_fixture):
    pass
"""
    )
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys,pytest;sys.path.insert(0,sys.argv[1]);"
            "raise SystemExit(pytest.main(['-q','-o','addopts=',"
            "'-c',sys.argv[1]+'/pyproject.toml',"
            "'-p','no:cacheprovider','-p','tests.profile_policy',*sys.argv[2:]]))",
            str(root),
            str(sample),
            str(sdk_sample),
        ],
        cwd=tmp_path,
        env={
            "PATH": os.defpath,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed, 2 skipped" in result.stdout


@pytest.mark.parametrize("operation", ["dns", "listener", "docker", "ssh", "shell"])
def test_offline_guard_rejects_external_actions(operation):
    cleanup = []
    configure_guard(SimpleNamespace(add_cleanup=cleanup.append))
    try:
        with pytest.raises(AssertionError, match="Offline profile"):
            if operation == "dns":
                socket.getaddrinfo("example.invalid", 443)
            elif operation == "listener":
                # Call the patched boundary without allocating a real socket.
                socket.socket.bind(None, ("127.0.0.1", 0))
            elif operation == "shell":
                subprocess.Popen("true", shell=True)
            else:
                subprocess.Popen([operation, "--version"])
    finally:
        for undo in reversed(cleanup):
            undo()
