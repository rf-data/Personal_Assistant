"""Linux guardian: confirmed process-group cleanup before terminal status.

The direct child remains unreaped until its process group has been terminated;
its reserved PID prevents signalling a reused unrelated group. No persisted PID
is used for signalling. The local supervisor is single-threaded when it forks.
"""

import argparse
import ctypes
import fcntl
import hashlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import Artifact
from src.job_control.registry import process_for
from src.job_control.store import Store, now

REPOSITORY = Path(__file__).resolve().parents[2]


def prctl(option, value):
    if sys.platform != "linux":
        raise RuntimeError("Linux process supervision required")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(option, value, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl failed")


def arm_parent_death(parent, death_signal=signal.SIGTERM):
    prctl(
        1, death_signal
    )  # PR_SET_PDEATHSIG; default terminates during exec bootstrap.
    if os.getppid() != parent:
        os._exit(125)


def clean_environment():
    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(REPOSITORY),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
        "LANG": "C.UTF-8",
    }
    # Explicit operator policy only; descendants revalidate file, grant and mount.
    from src.runtime_paths import POLICY_ENV

    if POLICY_ENV in os.environ:
        environment[POLICY_ENV] = os.environ[POLICY_ENV]
    return environment


def exited_without_reaping(child):
    return (
        os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    )


def cleanup_group(child, grace=0.4):
    # Never child.poll()/wait() before killpg: its PID must remain reserved.
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    until = time.monotonic() + grace
    while time.monotonic() < until and not exited_without_reaping(child):
        time.sleep(0.02)
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    code = child.wait(timeout=3)
    # As subreaper, collect the same trusted adapter's orphaned descendants.
    until = time.monotonic() + 3
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return code
        if pid == 0:
            if time.monotonic() >= until:
                raise RuntimeError("Descendant cleanup unconfirmed")
            time.sleep(0.02)


def supervise(command, *, directory, timeout, should_stop, on_started=lambda: None):
    """Internal subprocess primitive; HTTP/registry never accepts this command."""
    prctl(36, 1)  # PR_SET_CHILD_SUBREAPER
    parent = os.getpid()
    child = subprocess.Popen(
        command,
        cwd=directory,
        env=clean_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        preexec_fn=lambda: arm_parent_death(parent),
    )
    reason = None
    started = time.monotonic()
    try:
        on_started()
        while not exited_without_reaping(child):
            reason = should_stop()
            if reason:
                break
            if time.monotonic() - started >= timeout:
                reason = "timeout"
                break
            time.sleep(0.03)
    finally:
        code = cleanup_group(child)
    return code, reason, time.monotonic() - started


def execute(root, job_id, parent):
    stopping = {"value": False}

    def stopped(*args):
        stopping["value"] = True

    signal.signal(signal.SIGTERM, stopped)
    signal.signal(signal.SIGINT, stopped)
    prctl(1, signal.SIGTERM)
    if os.getppid() != parent:
        stopping["value"] = True
    store = Store(root)
    directory = store.directory(job_id)
    lock_path = safe_path(directory, "execution.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        job = store.get(job_id)
        process = process_for(job.process_id)

        def should_stop():
            if stopping["value"]:
                return "interrupted"
            if store.get(job_id).status == "cancel_requested":
                return "cancelled"
            return None

        if should_stop():
            status = should_stop()
            store.transition(
                job_id, status, status, "Execution stopped before payload dispatch"
            )
            return
        code, reason, duration = supervise(
            [
                sys.executable,
                "-m",
                "src.job_control.adapter_worker",
                "--root",
                str(root),
                "--job-id",
                job_id,
                "--parent",
                str(os.getpid()),
            ],
            directory=directory,
            timeout=process.timeout_seconds,
            should_stop=should_stop,
            on_started=lambda: store.transition(
                job_id,
                "running",
                "offline_adapter",
                "Known offline adapter launched",
                started_at=now(),
            ),
        )
        status = (
            reason
            if reason in {"interrupted", "cancelled"}
            else "failed"
            if reason == "timeout" or code != 0
            else "completed"
        )
        if store.get(job_id).status == "cancel_requested":
            status = "cancelled"
        artifacts = []
        result = directory / "results" / (job.parameters["output_name"] + ".json")
        if status in {"completed", "failed"} and result.exists():
            data = read_file(
                safe_path(directory, result.relative_to(directory)), process.file_bytes
            )
            artifacts.append(
                Artifact(
                    artifact_id="art_" + job_id[4:],
                    job_id=job_id,
                    kind=process.artifact_kind,
                    size_bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                    created_at=now(),
                    input_refs=job.input_refs,
                )
            )
        if status == "completed" and not artifacts:
            status = "failed"
        error = (
            "Execution timeout"
            if reason == "timeout"
            else "PDF worker timeout"
            if code == 4
            else "Offline adapter returned non-zero or missing output"
            if status == "failed"
            else "Supervisor interrupted"
            if status == "interrupted"
            else None
        )
        store.transition(
            job_id,
            status,
            status,
            "Payload and descendants ended; final result recorded",
            exit_code=code,
            duration_seconds=duration,
            error=error,
            error_class="timeout"
            if reason == "timeout" or code == 4
            else "input"
            if status == "failed" and code in {1, 2}
            else "internal"
            if status == "failed"
            else None,
            artifact_refs=tuple(artifacts),
            output_refs=tuple(a.artifact_id for a in artifacts),
        )
    except Exception as error:
        # Cleanup was attempted; an exception is never proof of process end.
        store.quarantine(job_id)
        store.transition(
            job_id,
            "interrupted",
            "interrupted",
            "Execution could not be confirmed",
            error="Execution interrupted ("
            + type(error).__name__[:60]
            + "); no automatic retry",
        )
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--parent", type=int, required=True)
    args = parser.parse_args(argv)
    execute(args.root, args.job_id, args.parent)


if __name__ == "__main__":
    main()
