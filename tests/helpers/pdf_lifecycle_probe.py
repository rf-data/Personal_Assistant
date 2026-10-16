"""Trusted fault injection only; never registered or reachable from an API input."""

import json
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main():
    mode, directory, *args = sys.argv[1:]
    directory = Path(directory)
    if mode == "pdf":
        (directory / "pdf-pid.json").write_text(
            json.dumps(dict(pid=os.getpid(), group=os.getpgrp(), parent=os.getppid()))
        )
        # Simulate a stuck native parse, without changing the real PDF parser.
        time.sleep(60)
        runpy.run_path(args[0], run_name="__main__")
        return
    if mode == "adapter":
        from src.job_control import adapter_worker
        from src.tools_materials import parse_pdf

        original = parse_pdf.run_worker

        def stuck(command, request, timeout):
            return original(
                [sys.executable, "-I", __file__, "pdf", str(directory), command[-1]],
                request,
                1.5 if (directory / "worker-timeout").exists() else timeout,
            )

        parse_pdf.run_worker = stuck
        raise SystemExit(adapter_worker.main(args))
    if mode == "guardian":
        from src.job_control import guardian

        original = guardian.supervise

        def supervised(command, **kwargs):
            if (directory / "job-timeout").exists():
                kwargs["timeout"] = float(
                    (directory / "job-timeout").read_text() or "1.5"
                )
            command = [
                sys.executable,
                __file__,
                "adapter",
                str(directory),
                *command[3:],
            ]
            return original(command, **kwargs)

        guardian.supervise = supervised
        guardian.main(args)
        return
    if mode == "executor":
        from src.job_control import executor as module
        from src.job_control.controller import Controller
        from src.job_control.models import load_settings

        settings = load_settings(directory / "config.json")
        original = subprocess.Popen

        def launch(command, **kwargs):
            if command[1:3] == ["-m", "src.job_control.guardian"]:
                command = [
                    sys.executable,
                    __file__,
                    "guardian",
                    str(directory),
                    *command[3:],
                ]
            return original(command, **kwargs)

        module.subprocess.Popen = launch
        controller = Controller(settings)
        worker = module.Executor(settings)
        job = next(j for j in controller.store.all() if j.status == "queued")
        worker.step()
        (directory / "guardian-pid.json").write_text(
            json.dumps(worker.children[job.job_id].pid)
        )
        # No signal handler on purpose: parent death exercises the real chain.
        while True:
            worker.step()
            time.sleep(0.03)
    raise ValueError("Unknown trusted test mode")


if __name__ == "__main__":
    main()
