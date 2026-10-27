"""Export pinned sources into a NEW /tmp copy and run offline checks.

No checkout, ref/index write, merge, network, Docker or production access.
Requires a preinstalled Python 3.12/3.13 with the documented test dependencies.
"""

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BASE = "778367396cd52526eca59edd41c2367f5e43b897"
ANCESTOR = "e68275205fefb7a5f6db42bc45060e505bfcefb5"
DRAFT = "7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d"
OVERLAY = (
    "scripts/c26g_preflight.py",
    "deployment/c26g.staging.controller.json.example",
    "tests/test_c26g_readiness.py",
    "tests/test_c26g_restore.py",
)
TESTS = (
    "c26g_readiness",
    "c26g_restore",
    "deployment_gate",
    "deployment_gate_v2",
    "coolify_observer",
    "coolify_readiness",
    "runtime_collector",
    "deployment_coordinator",
    "coordinator_contracts",
    "c26_runtime_preflight",
    "c26_runtime_bootstrap",
    "deployment_operations",
    "runtime_paths",
    "job_control",
    "job_executor",
    "job_store_contention",
)


def prepare(repo):
    target = Path(tempfile.mkdtemp(prefix="c26g-offline-"))
    archive = subprocess.check_output(["git", "archive", BASE], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(target, filter="data")
    patch = subprocess.check_output(
        ["git", "diff", "--binary", ANCESTOR, DRAFT], cwd=repo
    )
    subprocess.run(
        ["git", "apply", "--check", "-"], cwd=target, input=patch, check=True
    )
    subprocess.run(["git", "apply", "-"], cwd=target, input=patch, check=True)
    for name in OVERLAY:
        shutil.copyfile(repo / name, target / name)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration-only", action="store_true")
    args = parser.parse_args()
    root = prepare(Path(__file__).resolve().parents[1])
    selected = TESTS[:2] if args.configuration_only else TESTS
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "-p",
        "tests.offline_guard",
        "-m",
        "not external_integration",
        "--tb=short",
        "--basetemp=" + str(root.parent / (root.name + "-data")),
        "--junitxml=" + str(root / "result.xml"),
    ]
    command.extend("tests/test_" + name + ".py" for name in selected)
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    # Do not inherit a module search path that could select the caller's sources.
    env.pop("PYTHONPATH", None)
    print(
        json.dumps(
            dict(snapshot=str(root), base=BASE, drafts=DRAFT, production_release="HOLD")
        ),
        flush=True,
    )
    return subprocess.run(command, cwd=root, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
