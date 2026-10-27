"""Local synthetic follow-up only. Run from this worktree, never on a live DB."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
env = dict(
    os.environ,
    PYTHONDONTWRITEBYTECODE="1",
    PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
)
common = [
    sys.executable,
    "-m",
    "pytest",
    "-q",
    "-o",
    "addopts=",
    "-p",
    "no:cacheprovider",
    "-p",
    "tests.offline_guard",
]
groups = [("sqlite-final", ["tests/test_cs50p_sqlite_stability.py"])]
groups += [
    (
        f"resume-{i:02d}",
        [
            "tests/test_cs50_workflows.py::test_resume_after_interrupted_attempt_before_state_write"
        ],
    )
    for i in range(1, 11)
]
groups += [
    (
        f"native-{i:02d}",
        [
            "tests/test_cs50p_native_admission.py::test_exact_cli_review_approve_run_result_and_recover_parser"
        ],
    )
    for i in range(1, 6)
]
results = []
for name, tests in groups:
    command = common + tests + ["--junitxml=" + str(ROOT / (name + ".xml"))]
    with (ROOT / (name + ".log")).open("w") as stream:
        result = subprocess.run(
            command, env=env, stdout=stream, stderr=subprocess.STDOUT
        )
    results.append(dict(name=name, exit=result.returncode, command=command))
    (ROOT / "followup-commands.json").write_text(json.dumps(results, indent=2) + "\n")
    print(name, result.returncode, flush=True)
