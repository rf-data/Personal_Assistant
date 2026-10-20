"""External acceptance driver; run with the existing UI Python environment.

The UI uses its real urllib transport, an actual loopback HTTP server and the
existing synthetic worker harness. Only test setup/fault injection uses stdin.
No production configuration, generic commands or new HTTP routes are added.
"""

import argparse
import hashlib
import json
import os
import select
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui-repo", required=True, type=Path)
    parser.add_argument("--backend-repo", required=True, type=Path)
    parser.add_argument("--backend-python", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output already exists")
    sys.path.insert(0, str(args.ui_repo))
    from admin_ui_package.c16_client import BackendError
    from admin_ui_package.live_state import Poller
    from admin_ui_package.security import client_for, principal_for
    from core.environment import AppSettings
    from scripts.demo_job_backend import Harness, widget
    from streamlit.testing.v1 import AppTest

    backend = args.backend_repo
    records, calls = [], []
    server = None
    original_connect = socket.socket.connect
    original_open = urllib.request.OpenerDirector.open
    lose_response = [False]
    port = [0]

    def record(name, **evidence):
        records.append(dict(requirement=name, status="passed", evidence=evidence))

    def loopback_only(sock, address):
        if address != ("127.0.0.1", port[0]):
            raise AssertionError("Only the owned acceptance HTTP endpoint is allowed")
        return original_connect(sock, address)

    def transport(opener, request, *a, **kw):
        response = original_open(opener, request, *a, **kw)
        route = urlsplit(request.full_url).path
        calls.append(
            dict(method=request.get_method(), route=route, status=response.status)
        )
        if lose_response[0] and route == "/v1/workflows/execute":
            lose_response[0] = False
            # The real handler has committed and sent 202; only receipt is lost.
            response.read()
            response.close()
            raise TimeoutError("Synthetic response loss after actual HTTP acceptance")
        return response

    with tempfile.TemporaryDirectory(prefix="c21-tcp-") as directory:
        root = Path(directory) / "backend"
        harness = Harness(backend, args.backend_python, root, workflows=True)

        def start_server():
            child = subprocess.Popen(
                [
                    str(args.backend_python),
                    "-m",
                    "scripts.acceptance.c21_server",
                    "--config",
                    str(root / "config.json"),
                    "--port",
                    str(port[0]),
                ],
                cwd=backend,
                env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if not select.select([child.stdout], [], [], 15)[0]:
                child.terminate()
                child.wait(timeout=10)
                raise RuntimeError("Acceptance HTTP server readiness timeout")
            line = child.stdout.readline()
            require(bool(line), "Acceptance HTTP server failed to bind")
            port[0] = json.loads(line)["port"]
            return child

        def stop_server(child):
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)
            child.stdout.close()

        try:
            server = start_server()
            origin = "http://127.0.0.1:" + str(port[0])
            now = [time.monotonic()]
            env = dict(
                APP_ENV="local",
                APP_ROOT=directory,
                ADMIN_AUTH_MODE="demo",
                ADMIN_DEMO_ROLE="operator",
                JOB_BACKEND="http",
                JOB_API_MODE="test",
                JOB_API_URL=origin,
                JOB_API_IDENTITIES=json.dumps(
                    [
                        dict(
                            ui_subject="local-demo",
                            backend_subject="synthetic-operator",
                            role="operator",
                            token_file=harness.ready["token_file"],
                        )
                    ]
                ),
                STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
            )
            with (
                patch.dict(os.environ, env, clear=True),
                patch.object(socket.socket, "connect", loopback_only),
                patch.object(urllib.request.OpenerDirector, "open", transport),
                patch(
                    "admin_ui_package.live_app.shared_poller",
                    return_value=Poller(lambda: now[0]),
                ),
            ):
                settings = AppSettings(_env_file=None)
                client = client_for(settings, principal_for(settings))

                def rerun(app):
                    now[0] += 5
                    app.run()
                    require(not app.exception, "Streamlit AppTest exception")

                def click(app, label):
                    for _ in range(30):
                        matches = [w for w in app.button if w.label == label]
                        if matches and not matches[0].disabled:
                            matches[0].click()
                            rerun(app)
                            return
                        rerun(app)
                    raise AssertionError("UI action unavailable: " + label)

                def finish(job_id):
                    until = time.monotonic() + 50
                    while time.monotonic() < until:
                        job = client.get(job_id)
                        if job.status in {
                            "completed",
                            "failed",
                            "cancelled",
                            "interrupted",
                        }:
                            require(
                                job.status == "completed", "Workflow did not complete"
                            )
                            return job
                        time.sleep(0.05)
                    raise TimeoutError("Acceptance workflow deadline")

                caps = client.workflow_capabilities()
                require(caps.enabled and caps.execution_enabled, "Workflow disabled")
                app = AppTest.from_file(
                    str(args.ui_repo / "app_admin.py"), default_timeout=30
                )
                rerun(app)
                widget(app, "radio", "Admin-Ansicht").set_value("Workflows")
                rerun(app)
                widget(app, "text_input", "workflow_id").set_value("c21_acceptance")
                click(app, "Workflow inspizieren")
                preview = app.session_state["live_workflow_preview"]
                require(len(preview["workflow"]["stages"]) == 5, "Five stages required")
                require(bool(app.get("graphviz_chart")), "Stage graph missing")
                require(
                    widget(app, "button", "Workflow starten").disabled,
                    "Missing confirmation gate",
                )
                widget(
                    app, "checkbox", "Ich bestätige den angezeigten Workflow-Stufenplan"
                ).check()
                rerun(app)
                lose_response[0] = True
                click(app, "Workflow starten")
                saved = dict(app.query_params)
                require("wf_key" in saved and "wf_body" in saved, "Pending intent lost")
                # Full new AppTest session: recover from URL, not copied session state.
                app = AppTest.from_file(
                    str(args.ui_repo / "app_admin.py"), default_timeout=30
                )
                app.query_params.update(saved)
                rerun(app)
                widget(app, "radio", "Admin-Ansicht").set_value("Workflows")
                rerun(app)
                widget(
                    app, "checkbox", "Unveränderten Workflowauftrag erneut bestätigen"
                ).check()
                rerun(app)
                click(app, "Unbestätigten Workflowauftrag erneut senden")
                require(
                    app.query_params["wf_key"] == saved["wf_key"]
                    and app.query_params["wf_body"] == saved["wf_body"],
                    "Replay intent changed",
                )
                job = finish(app.query_params["job"])
                inspection = client.workflow_status(
                    "synthetic_workflow", "c21_acceptance"
                )
                require(
                    inspection.history_total == 1,
                    "Duplicate execution after response loss",
                )
                require(
                    all(
                        s.status == "skipped" and s.decision == "verified_reuse"
                        for s in inspection.workflow.stages
                    ),
                    "Reuse not verified",
                )
                original = client.workflow_run(
                    "synthetic_workflow", "c21_acceptance", job.job_id
                )
                require(
                    all(s.status == "completed" for s in original.report.stages),
                    "Original stage report changed",
                )
                require(bool(client.artifacts(job.job_id)), "Artifact metadata missing")
                record(
                    "tcp_ui_execute_refresh_replay",
                    job_id=job.job_id,
                    stages=5,
                    history_total=1,
                    report_sha256=original.report.report_sha256,
                )
                record("tcp_artifact_metadata", artifacts=len(job.artifact_refs))

                # Actual HTTP process death/restart, preserving the same SQLite and port.
                stop_server(server)
                try:
                    client.workflow_status("synthetic_workflow", "c21_acceptance")
                except BackendError:
                    record("tcp_backend_unreachable")
                else:
                    raise AssertionError("Unavailable server reported success")
                server = start_server()
                restored = client.workflow_status(
                    "synthetic_workflow", "c21_acceptance"
                )
                require(
                    restored.current_job.job_id == job.job_id,
                    "Backend restart lost job",
                )
                record(
                    "tcp_backend_process_restart",
                    same_job=True,
                    history_total=restored.history_total,
                )

                click(app, "Resume prüfen")
                widget(
                    app, "checkbox", "Ich bestätige den angezeigten Workflow-Stufenplan"
                ).check()
                rerun(app)
                click(app, "Resume Workflow")
                require(app.query_params["job"] == job.job_id, "Resume created new job")
                require(
                    client.workflow_status(
                        "synthetic_workflow", "c21_acceptance"
                    ).history_total
                    == 1,
                    "Resume executed again",
                )
                record(
                    "tcp_ui_verified_resume",
                    same_job=True,
                    skipped=5,
                    decision="verified_reuse",
                )

                # External test-only damage, then stale confirmation and explicit partial resume.
                click(app, "Resume prüfen")
                harness.call(
                    dict(action="workflow_damage", workflow_id="c21_acceptance")
                )
                widget(
                    app, "checkbox", "Ich bestätige den angezeigten Workflow-Stufenplan"
                ).check()
                rerun(app)
                click(app, "Resume Workflow")
                require(
                    "live_workflow_preview" not in app.session_state,
                    "Stale preview retained",
                )
                require(bool(app.error), "Stale conflict not visible")
                click(app, "Resume prüfen")
                stale = app.session_state["live_workflow_preview"]["workflow"]["stages"]
                require(
                    [s["status"] for s in stale]
                    == ["skipped", "skipped", "stale", "stale", "stale"],
                    "Stale propagation changed",
                )
                widget(
                    app, "checkbox", "Ich bestätige den angezeigten Workflow-Stufenplan"
                ).check()
                rerun(app)
                click(app, "Resume Workflow")
                second = finish(app.query_params["job"])
                require(
                    second.job_id != job.job_id, "Partial resume did not create attempt"
                )
                require(
                    harness.call(dict(action="verify_preserved"))["preserved"],
                    "Previous artifacts overwritten",
                )
                record(
                    "tcp_ui_stale_partial_resume",
                    previous_job=job.job_id,
                    resumed_job=second.job_id,
                    prior_bytes_preserved=True,
                )

                # Metrics travel through the same real HTTP handler; credentials stay local.
                token = Path(harness.ready["token_file"]).read_text()
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

                def rejected(
                    selector, expected, credential=token, route="inspect", key=None
                ):
                    request = urllib.request.Request(
                        origin + "/v1/workflows/" + route,
                        data=json.dumps(selector).encode(),
                        headers={
                            "Authorization": "Bearer " + credential,
                            "Content-Type": "application/json",
                            **({"Idempotency-Key": key} if key else {}),
                        },
                        method="POST",
                    )
                    try:
                        with opener.open(request, timeout=2):
                            raise AssertionError("Invalid input/access accepted")
                    except urllib.error.HTTPError as error:
                        require(
                            error.code == expected,
                            "Unexpected rejection status: " + str(error.code),
                        )
                        error.close()
                        return error.code

                selector = dict(
                    source_ref="synthetic_workflow", workflow_id="c21_acceptance"
                )
                rejected(dict(selector, source_ref="unknown_source"), 422)
                for binding in harness.ready["test_identities"]:
                    rejected(selector, 403, Path(binding["token_file"]).read_text())
                record(
                    "tcp_invalid_source_owner_course",
                    invalid_source_status=422,
                    denied_identities=3,
                )
                source = root / "workflow-inputs/raw_0.source"
                raw = source.read_bytes()

                def blocked_input(suffix, status):
                    invalid = client.workflow_inspect(
                        "synthetic_workflow", "c21_acceptance"
                    )
                    require(
                        any(s.status == "blocked" for s in invalid.workflow.stages),
                        "Invalid input not reflected in preview",
                    )
                    rejected(
                        dict(
                            selector,
                            preview_id=invalid.preview_id,
                            current_run_id=second.job_id,
                            confirmed=True,
                        ),
                        status,
                        route="resume",
                        key="c21_invalid_input_" + suffix,
                    )

                try:
                    source.write_bytes(b"synthetic input hash corruption")
                    blocked_input("changed", 422)
                    source.unlink()
                    blocked_input("missing", 503)
                finally:
                    source.write_bytes(raw)
                require(
                    client.workflow_status(
                        "synthetic_workflow", "c21_acceptance"
                    ).history_total
                    == 2,
                    "Invalid input created job",
                )
                record(
                    "tcp_changed_hash_missing_input",
                    changed_hash_status=422,
                    missing_file_status=503,
                    source_restored=True,
                    no_additional_job=True,
                )
                request = urllib.request.Request(
                    origin + "/v1/metrics", headers={"Authorization": "Bearer " + token}
                )
                with opener.open(request, timeout=2) as response:
                    metrics = response.read(524289).decode()
                lines = [
                    line for line in metrics.splitlines() if not line.startswith("#")
                ]
                require(
                    any('process="cs50_offline_workflow"' in line for line in lines),
                    "Workflow process metrics missing",
                )
                require(
                    not any(
                        label + "=" in metrics
                        for label in ("job_id", "stage_id", "workflow_id", "run_id")
                    ),
                    "High cardinality metric identity",
                )
                require(
                    any(
                        "jobs_completed_total" in line
                        and 'outcome="success"' in line
                        and float(line.rsplit(" ", 1)[1]) >= 2
                        for line in lines
                    ),
                    "Success count missing",
                )
                record(
                    "tcp_c15_metrics",
                    sha256=hashlib.sha256(metrics.encode()).hexdigest(),
                    text=metrics,
                    identity_labels=False,
                )

            report = dict(
                schema_version=1,
                synthetic=True,
                test_type="Streamlit AppTest + actual loopback HTTP + native subprocesses",
                browser_test="not tested",
                checks=records,
                http_calls=calls,
                external_setup_actions=harness.test_actions,
            )
        finally:
            if server:
                stop_server(server)
            harness.close()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
