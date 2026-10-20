"""Capture complete synthetic C20-B HTTP messages through the real local router.

No HTTP server, downloads, providers or production configuration. New files only.
"""

import argparse
import json
import socket
import tempfile
import time
from pathlib import Path

from scripts.cs50_workflow_demo import inputs, sha
from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.http import Application
from src.job_control.models import TERMINAL, Identity, Settings


def capture(workspace):
    entry = inputs(workspace / "inputs", pdf=True)
    settings = Settings(
        root=workspace / "private",
        catalog=dict(synthetic_pdf=entry),
        identities=(
            Identity(
                subject="synthetic_operator",
                role="operator",
                courses=("cs50_python",),
                token_sha256=sha(DEMO_TOKEN.encode()),
            ),
        ),
        execution_enabled=True,
        workflows_enabled=True,
    )
    controller = Controller(settings)
    application = Application(controller)
    messages = []

    def request(method, path, body=None, key=None):
        headers = {"Authorization": "Bearer " + DEMO_TOKEN}
        if key:
            headers["Idempotency-Key"] = key
        status, raw, _mime = application.request(
            method, path, headers, json.dumps(body).encode() if body else b""
        )
        response = json.loads(raw)
        messages.append(
            dict(
                method=method,
                path=path,
                body=body,
                idempotency_key=key,
                status=status,
                response=response,
            )
        )
        if status not in {200, 202}:
            raise ValueError("Synthetic HTTP demo failed")
        return response

    selector = dict(source_ref="synthetic_pdf", workflow_id="synthetic_http_workflow")
    executor = Executor(settings)
    try:
        request("GET", "/v1/workflows/capabilities")
        preview = request("POST", "/v1/workflows/inspect", selector)
        execute = dict(
            **selector,
            preview_id=preview["preview_id"],
            current_run_id=None,
            confirmed=True,
        )
        accepted = request(
            "POST", "/v1/workflows/execute", execute, "synthetic_http_demo_execute_001"
        )
        job_id = accepted["run_id"]
        until = time.monotonic() + 40
        while controller.store.get(job_id).status not in TERMINAL:
            if time.monotonic() >= until:
                raise TimeoutError("Synthetic HTTP demo deadline")
            executor.step()
            time.sleep(0.02)
        if controller.store.get(job_id).status != "completed":
            raise ValueError("Synthetic PDF workflow failed")
        status = request(
            "GET", f"/v1/workflows/{selector['workflow_id']}?source_ref=synthetic_pdf"
        )
        request(
            "GET",
            f"/v1/workflows/{selector['workflow_id']}/runs/{job_id}?source_ref=synthetic_pdf",
        )
        stages = status["workflow"]["stages"]
        if len(stages) != 5 or any(
            s["status"] != "skipped" or s["decision"] != "verified_reuse"
            for s in stages
        ):
            raise ValueError("Expected five verified reuses")
        resumed = request(
            "POST",
            "/v1/workflows/resume",
            dict(
                **selector,
                preview_id=status["preview_id"],
                current_run_id=job_id,
                confirmed=True,
            ),
            "synthetic_http_demo_resume_001",
        )
        if resumed["run_id"] != job_id or len(controller.store.all()) != 1:
            raise ValueError("Expected original job without a new attempt")
        request(
            "POST", "/v1/workflows/execute", execute, "synthetic_http_demo_execute_001"
        )
    finally:
        executor.close()
    return dict(
        schema_version=1,
        synthetic=True,
        transport="real Application router; no socket",
        authentication="existing C16 Bearer verifier; token omitted",
        workflow_engine="existing C18 service/engine via C16 queue and C19 PDF-v2",
        resume_same_job=True,
        stage_count=5,
        job_count=1,
        messages=messages,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output already exists")

    def forbidden(*args, **kwargs):
        raise RuntimeError("Synthetic demo is offline")

    socket.socket.connect = forbidden
    socket.getaddrinfo = forbidden
    with tempfile.TemporaryDirectory(prefix="c20b-http-demo-") as directory:
        report = capture(Path(directory))
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(status="completed", stages=5, jobs=1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
