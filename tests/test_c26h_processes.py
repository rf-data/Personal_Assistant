"""Deterministic slow-start probes preserve the real cancellation guarantees."""

import json
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from src.job_control.guardian import REPOSITORY, clean_environment

BOOTSTRAP = """
import json, os, runpy, sys, time
from pathlib import Path
namespace = runpy.run_path(sys.argv[1])
original = namespace['supervise']
signals = []
killpg = os.killpg
def record_signal(group, signum):
    signals.append([group, signum])
    return killpg(group, signum)
os.killpg = record_signal
def delayed(command, **kwargs):
    command = [*command[:-1], 'import time; time.sleep(0.6);' + command[-1]]
    return original(command, **kwargs)
main = namespace['main']
main.__globals__['supervise'] = delayed
sys.argv = sys.argv[1:]
main()
Path(sys.argv[2], 'signals.json').write_text(json.dumps(signals))
"""


@pytest.mark.parametrize(
    "mode,reason", [("cancel", "cancelled"), ("timeout", "timeout")]
)
def test_slow_bootstrap_waits_for_term_ignoring_process_group(tmp_path, mode, reason):
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True
    )
    try:
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                BOOTSTRAP,
                str(REPOSITORY / "tests/helpers/job_control_probe.py"),
                mode,
                str(tmp_path),
            ],
            cwd=REPOSITORY,
            env=clean_environment(),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert child.returncode == 0, child.stderr
        code, observed, duration = json.loads(
            (tmp_path / "probe-result.json").read_text()
        )
        assert code == -signal.SIGKILL and observed == reason and duration < 5
        pids = json.loads((tmp_path / "pids.json").read_text())
        assert all(not Path(f"/proc/{pid}").exists() for pid in pids)
        assert json.loads((tmp_path / "signals.json").read_text()) == [
            [pids[0], signal.SIGTERM],
            [pids[0], signal.SIGKILL],
        ]
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=3)
