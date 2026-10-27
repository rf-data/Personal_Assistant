"""Trusted fault probes for Linux supervision. Not registered or API-callable."""

import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

from src.job_control.guardian import (
    arm_parent_death,
    clean_environment,
    prctl,
    supervise,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=[
            "timeout",
            "cancel",
            "exit",
            "limits",
            "parent_death",
            "crash_executor",
            "crash_parent",
            "orphan_exit",
        ],
    )
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.mode == "crash_parent":
        parent = os.getpid()
        child = subprocess.Popen(
            [sys.executable, __file__, "parent_death", str(args.directory)],
            env={**clean_environment(), "PROBE_PARENT": str(parent)},
            start_new_session=True,
            preexec_fn=lambda: arm_parent_death(parent),
        )
        (args.directory / "guardian.json").write_text(json.dumps(child.pid))
        until = time.monotonic() + 5
        while not (args.directory / "pids.json").exists():
            if time.monotonic() >= until:
                raise RuntimeError("Probe child did not start")
            time.sleep(0.01)
        os.kill(parent, signal.SIGKILL)
    if args.mode == "crash_executor":
        from scripts.job_control_demo import DEMO_TOKEN
        from src.job_control.controller import Controller
        from src.job_control.executor import Executor
        from src.job_control.models import load_settings

        settings = load_settings(args.directory / "config.json")
        controller = Controller(settings)
        executor = Executor(settings)
        actor = controller.authenticate("Bearer " + DEMO_TOKEN)
        preview = controller.preview(
            actor,
            dict(
                process_id="material_planning",
                parameters=dict(
                    source_ref="demo_snapshots", course_id="cs50_python", section="0"
                ),
            ),
        )
        job = controller.create(
            actor,
            dict(preview=preview.model_dump(mode="json"), confirmed=True),
            "crash_executor_request_0001",
        )
        executor.step()
        (args.directory / "crash.json").write_text(
            json.dumps(
                dict(job_id=job.job_id, guardian=executor.children[job.job_id].pid)
            )
        )
        os.kill(os.getpid(), signal.SIGKILL)
    if args.mode == "limits":
        from src.job_control.adapter_worker import apply_limits
        from src.job_control.registry import REGISTRY

        process = REGISTRY["material_planning"]
        apply_limits(process)
        print(
            json.dumps(
                {
                    str(k): resource.getrlimit(k)
                    for k in (
                        resource.RLIMIT_AS,
                        resource.RLIMIT_CPU,
                        resource.RLIMIT_FSIZE,
                        resource.RLIMIT_NOFILE,
                        resource.RLIMIT_NPROC,
                        resource.RLIMIT_CORE,
                    )
                }
            )
        )
        return
    stopped = {"value": False}
    if args.mode == "parent_death":
        signal.signal(signal.SIGTERM, lambda *_: stopped.update(value=True))
        prctl(1, signal.SIGTERM)
        expected = int(os.environ["PROBE_PARENT"])
        if os.getppid() != expected:
            stopped["value"] = True
    # Both root and child deliberately ignore TERM; group cleanup must escalate.
    body = """
import json, os, signal, subprocess, sys, time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c',
    "import signal,time; from pathlib import Path; "
    "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
    "Path('child-ready').touch(); time.sleep(60)"])
while not Path('child-ready').exists():
    time.sleep(0.005)
temporary = Path('.pids.json.tmp')
temporary.write_text(json.dumps([os.getpid(), child.pid]))
temporary.replace('pids.json')
time.sleep(60)
"""
    if args.mode == "exit":
        body = "raise SystemExit(7)"
    if args.mode == "orphan_exit":
        body = body.rsplit("time.sleep(60)", 1)[0] + "raise SystemExit(0)"
    started = time.monotonic()

    def should_stop():
        if stopped["value"]:
            return "interrupted"
        if args.mode == "cancel" and time.monotonic() - started > 0.3:
            return "cancelled"
        return None

    def wait_for_ready_group():
        if args.mode == "exit":
            return
        deadline = time.monotonic() + 3
        while not (args.directory / "pids.json").exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Probe process group readiness not confirmed")
            time.sleep(0.005)

    result = supervise(
        [sys.executable, "-c", body],
        directory=args.directory,
        timeout=0.3 if args.mode == "timeout" else 10,
        should_stop=should_stop,
        on_started=wait_for_ready_group,
    )
    (args.directory / "probe-result.json").write_text(json.dumps(result))


if __name__ == "__main__":
    main()
