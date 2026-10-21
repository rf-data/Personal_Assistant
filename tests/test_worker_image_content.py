"""Worker CLI checks in a runtime-only tree; optional check of a real built image."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.worker_image_smoke import MODULES, RUNTIME_SCRIPTS, check

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def runtime_tree(tmp_path_factory):
    root = tmp_path_factory.mktemp("worker-runtime")
    for directory in ("src", "configuration"):
        for path in (REPO / directory).rglob("*"):
            if (
                path.is_file()
                and path.suffix in {".py", ".yaml"}
                and not path.name.startswith("_dev")
                and "__pycache__" not in path.parts
            ):
                target = root / path.relative_to(REPO)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    for module in (*RUNTIME_SCRIPTS, "scripts.worker_image_smoke"):
        relative = Path(module.replace(".", "/") + ".py")
        (root / relative).parent.mkdir(exist_ok=True)
        shutil.copyfile(REPO / relative, root / relative)
    return root


def test_actual_cli_imports_in_runtime_only_tree(runtime_tree, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/nonexistent-host-code")
    monkeypatch.setenv("C26_LIMITS_FILE", "/nonexistent-production-config")
    before = sorted(p.relative_to(runtime_tree) for p in runtime_tree.rglob("*"))
    result = check(runtime_tree)
    assert result == {
        "status": "passed",
        "checks": [{"module": m, "status": "passed"} for m in MODULES],
    }
    assert before == sorted(
        p.relative_to(runtime_tree) for p in runtime_tree.rglob("*")
    )
    assert not (runtime_tree / "docs").exists()
    assert not (runtime_tree / "data").exists()


@pytest.mark.parametrize("command", ["bootstrap", "verify-bootstrap", "init"])
def test_pilot_bootstrap_cli_in_runtime_tree(runtime_tree, command):
    result = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.cs50_pilot", command, "--help"],
        cwd=runtime_tree,
        env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"},
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"usage:" in result.stdout
    if command == "bootstrap":
        assert b"--worker-uid" in result.stdout and b"--worker-gid" in result.stdout
    if command == "init":
        assert b"--prepared" in result.stdout
    assert not (runtime_tree / "data").exists()


def test_actual_smoke_module_entrypoint(runtime_tree):
    result = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.worker_image_smoke"],
        cwd=runtime_tree,
        env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"},
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert json.loads(result.stdout)["status"] == "passed"


@pytest.fixture
def small_tree(tmp_path):
    (tmp_path / "scripts").mkdir()
    for module in RUNTIME_SCRIPTS:
        (tmp_path / (module.replace(".", "/") + ".py")).write_text(
            "import os\n"
            "assert 'C26_SMOKE_TEST_SECRET' not in os.environ\n"
            "assert 'PYTHONPATH' not in os.environ\n"
            "assert 'C26_LIMITS_FILE' not in os.environ\n"
            "print('usage: synthetic CLI')\n"
        )
    return tmp_path


@pytest.mark.parametrize("module", RUNTIME_SCRIPTS)
def test_missing_transitive_runtime_script_fails(small_tree, module):
    (small_tree / (module.replace(".", "/") + ".py")).unlink()
    assert check(small_tree) == {
        "status": "failed",
        "checks": [{"module": module, "status": "missing_runtime_script"}],
    }


def test_symlinked_runtime_script_rejected(small_tree):
    path = small_tree / "scripts/cs50_batch.py"
    path.unlink()
    path.symlink_to(small_tree / "scripts/cs50_worker.py")
    assert check(small_tree)["checks"][0]["status"] == "missing_runtime_script"


def test_private_environment_not_forwarded(small_tree, monkeypatch):
    monkeypatch.setenv("C26_SMOKE_TEST_SECRET", "synthetic-token-canary")
    monkeypatch.setenv("PYTHONPATH", "/nonexistent")
    monkeypatch.setenv("C26_LIMITS_FILE", "/nonexistent")
    assert check(small_tree)["status"] == "passed"


@pytest.mark.parametrize(
    "program",
    [
        "import dependency_that_is_not_installed\n",
        "raise RuntimeError('synthetic-token-canary')\n",
        "print('synthetic-token-canary')\n",  # Exit 0 without argparse is insufficient.
    ],
)
def test_broken_cli_fails_without_leaking_output(small_tree, program):
    (small_tree / "scripts/cs50_batch.py").write_text(program)
    result = check(small_tree)
    assert result["status"] == "failed"
    assert result["checks"][0]["status"] == "cli_failed"
    assert "synthetic-token-canary" not in json.dumps(result)


def test_timeout_fails_closed(small_tree, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)
    result = check(small_tree)
    assert result["status"] == "failed"
    assert {row["status"] for row in result["checks"]} == {"timeout"}


def local_docker_only():
    context = subprocess.check_output(["docker", "context", "show"], text=True).strip()
    endpoint = json.loads(
        subprocess.check_output(["docker", "context", "inspect", context], text=True)
    )[0]["Endpoints"]["docker"]["Host"]
    if not os.environ.get("DOCKER_CONTEXT"):
        endpoint = os.environ.get("DOCKER_HOST", endpoint)
    assert endpoint.startswith("unix://"), "Only a local Docker socket is allowed"


@pytest.mark.skipif(
    os.environ.get("C26_WORKER_CONTEXT_AUDIT") != "1",
    reason="Set C26_WORKER_CONTEXT_AUDIT=1 for a native local Docker ignore check",
)
def test_native_docker_context_excludes_private_files(tmp_path):
    """A tiny scratch export tests Docker's own ignore matcher, not the worker image."""
    local_docker_only()
    context, output = tmp_path / "context", tmp_path / "export"
    allowed = {
        "pyproject.toml",
        "uv.lock",
        "src/runtime.py",
        "src/nested/runtime.py",
        "configuration/cfg_general.yaml",
        "configuration/cfg_parsing.yaml",
        "configuration/streamlit_general.yaml",
        "configuration/streamlit_run.yaml",
        *(module.replace(".", "/") + ".py" for module in RUNTIME_SCRIPTS),
        "scripts/worker_image_smoke.py",
    }
    excluded = {
        ".env",
        ".env.agentic",
        ".git/config",
        ".venv/private.py",
        "data/source.pdf",
        "logs/private.log",
        "docs/private.md",
        "src/.env",
        "src/.venv/private.py",
        "src/nested/.private/secret.py",
        "src/mathe_vorkurs.html",
        "src/__pycache__/runtime.pyc",
        "src/_dev_private.py",
        "src/nested/token.key",
        "configuration/private.yaml",
        "scripts/backup_hetzner.sh",
        "scripts/private.py",
    }
    for name in allowed | excluded:
        path = context / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic-context-canary\n")
    (context / "docker").mkdir()
    (context / "docker/DockerFile.worker").write_text(
        "FROM scratch\nCOPY . /context/\n"
    )
    shutil.copyfile(
        REPO / "docker/DockerFile.worker.dockerignore",
        context / "docker/DockerFile.worker.dockerignore",
    )
    subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "--network=none",
            "--progress=plain",
            "--file",
            str(context / "docker/DockerFile.worker"),
            "--output",
            f"type=local,dest={output}",
            str(context),
        ],
        check=True,
        capture_output=True,
        timeout=90,
    )
    files = {
        p.relative_to(output / "context").as_posix()
        for p in (output / "context").rglob("*")
        if p.is_file()
    }
    assert allowed <= files
    assert not excluded & files
    assert files <= allowed | {
        "docker/DockerFile.worker",
        "docker/DockerFile.worker.dockerignore",
    }


@pytest.mark.skipif(
    not os.environ.get("C26_WORKER_TEST_IMAGE"),
    reason="No built worker image supplied; set C26_WORKER_TEST_IMAGE on a local Docker host",
)
def test_built_worker_image():
    """No mounts, credentials, network, pull or access to an existing container."""
    local_docker_only()
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=128",
            "--memory=1g",
            "--memory-swap=1g",
            "--cpus=1",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
            "--entrypoint=/app/.venv/bin/python",
            os.environ["C26_WORKER_TEST_IMAGE"],
            "-B",
            "-m",
            "scripts.worker_image_smoke",
        ],
        capture_output=True,
        timeout=150,
        check=False,
    )
    assert result.returncode == 0, "Built worker CLI smoke failed"
    assert json.loads(result.stdout)["status"] == "passed"
