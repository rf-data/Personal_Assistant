"""Owned loopback API + separate managed worker; synthetic inputs, no internet."""

import hashlib
import http.client
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from scripts.job_control_demo import DEMO_TOKEN, build_inputs
from src.job_control.models import Identity, Settings
from src.job_control.operations import backup, health, restore


def until(call, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            value = call()
            if value:
                return value
        except (OSError, ValueError, AssertionError):
            pass
        time.sleep(0.05)
    raise AssertionError("Owned synthetic role did not become ready")


def test_managed_api_worker_restart_idempotence_and_restore(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    settings = Settings(
        root=root,
        catalog=build_inputs(tmp_path),
        execution_enabled=True,
        identities=(
            Identity(
                subject="synthetic",
                role="operator",
                courses=("cs50_python",),
                token_sha256=hashlib.sha256(DEMO_TOKEN.encode()).hexdigest(),
            ),
        ),
    )
    config = tmp_path / "controller.json"
    config.write_text(settings.model_dump_json())
    config.chmod(0o600)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    repo = Path(__file__).resolve().parents[1]
    children = []

    def launch(role):
        args = [
            sys.executable,
            "-m",
            "scripts.deployment",
            role,
            "--config",
            str(config),
        ]
        if role == "api":
            args += ["--port", str(port)]
        child = subprocess.Popen(
            args,
            cwd=repo,
            env={
                "PATH": os.defpath,
                "PYTHONPATH": str(repo),
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        children.append(child)
        return child

    def stop(child):
        child.terminate()
        assert child.wait(timeout=15) == 0

    def request(method, path, value=None, key=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            headers = {
                "Authorization": "Bearer " + DEMO_TOKEN,
                "Content-Type": "application/json",
            }
            if key:
                headers["Idempotency-Key"] = key
            connection.request(
                method,
                path,
                body=json.dumps(value) if value is not None else None,
                headers=headers,
            )
            response = connection.getresponse()
            assert response.status in (200, 202)
            return json.loads(response.read(524288))
        finally:
            connection.close()

    try:
        api = launch("api")
        until(lambda: request("GET", "/v1/processes"))
        health(settings, "api", port=port)
        preview = request(
            "POST",
            "/v1/previews",
            {
                "process_id": "material_planning",
                "parameters": {
                    "source_ref": "demo_snapshots",
                    "course_id": "cs50_python",
                    "section": "0",
                },
            },
        )
        body = {"preview": preview, "confirmed": True, "start": False}
        job = request("POST", "/v1/jobs", body, "synthetic_c22_tcp_0001")
        stop(api)
        api = launch("api")
        until(lambda: request("GET", "/v1/jobs/" + job["job_id"]))
        assert (
            request("POST", "/v1/jobs", body, "synthetic_c22_tcp_0001")["job_id"]
            == job["job_id"]
        )
        worker = launch("worker")
        until(lambda: (health(settings, "worker"), True)[1])
        stop(worker)
        worker = launch("worker")
        until(lambda: (health(settings, "worker"), True)[1])
        request("POST", "/v1/jobs/" + job["job_id"] + "/start", {})
        done = until(
            lambda: (
                value
                if (value := request("GET", "/v1/jobs/" + job["job_id"]))["status"]
                == "completed"
                else None
            )
        )
        assert done["artifact_refs"][0]["sha256"]
        stop(worker)
        stop(api)
        backup(config, tmp_path / "snapshot")
        assert restore(tmp_path / "snapshot", tmp_path / "restored")["jobs"] == 1
        # Full result integrity is checked against C16's stored Artifact SHA.
        with (
            tmp_path / "restored/jobs" / job["job_id"] / "results/material-plan.json"
        ).open("rb") as stream:
            assert (
                hashlib.file_digest(stream, "sha256").hexdigest()
                == done["artifact_refs"][0]["sha256"]
            )
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=15)
