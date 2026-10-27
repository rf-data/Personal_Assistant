"""Read the separate UI's actual C16 client; no UI source is copied or changed."""

import io
import os
import urllib.error
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from test_c26_pilot_workflow import offline as offline
from test_c26_pilot_workflow import pilot as pilot
from test_job_control import DEMO_TOKEN, finish, request_data

pytestmark = pytest.mark.external_integration


def test_actual_ui_client_reads_gated_single_job_and_verified_plan(
    pilot, monkeypatch, tmp_path
):
    repository = os.environ.get("C26_UI_REPO")
    if not repository:
        pytest.skip("C26_UI_REPO must identify the verified separate UI checkout")
    assert (Path(repository) / "admin_ui_package/c16_client.py").is_file()
    monkeypatch.syspath_prepend(repository)
    from admin_ui_package.c16_client import BackendError, Client

    env, gate, plan, driver, worker = pilot
    token = tmp_path / "ui.token"
    token.write_text(DEMO_TOKEN)
    token.chmod(0o600)
    binding = SimpleNamespace(
        ui_subject="ui-operator",
        backend_subject="operator",
        role="operator",
        token_file=token,
    )
    settings = SimpleNamespace(
        job_api_identities=[binding],
        job_api_url="http://127.0.0.1:8016",
        job_api_timeout=2,
    )
    actor = SimpleNamespace(subject="ui-operator", role="operator")

    def opening(request, timeout):
        target = urlsplit(request.full_url)
        code, raw, mime = env.app.request(
            request.method,
            target.path,
            {k.title(): v for k, v in request.header_items()},
            request.data or b"",
        )
        headers = Message()
        headers["Content-Type"] = mime
        if code >= 400:
            raise urllib.error.HTTPError(
                request.full_url,
                code,
                "Synthetic IPC response",
                headers,
                io.BytesIO(raw),
            )
        response = io.BytesIO(raw)
        response.headers = headers
        return response

    def client():
        result = Client(settings, actor)
        result._open = opening  # Only socket transport is replaced.
        return result

    first = client()
    parameters = request_data(env)["preview"]["parameters"]
    preview = first.preview("material_planning", parameters)
    job = first.create(preview, "explicit_pilot_ui_authorization")
    del first
    assert finish(env, worker, job).status == "completed"
    second = client()
    assert second.get(job.job_id).status == "completed"
    assert second.artifacts(job.job_id)
    # Existing generic client supports the additive route; the actual Streamlit
    # result panel still needs a separate persistent UI workspace/branch change.
    result = second.request("GET", second.job_path(job.job_id) + "/result", dict)
    assert result["plan"]["materials"]
    assert result["artifact"]["job_id"] == job.job_id
    with pytest.raises(BackendError):
        second.create(preview, "reject_second_pilot_ui_job")
    gate.run(plan, __import__("test_deployment_gate_v2").approve(plan), driver)
    with pytest.raises(BackendError):
        second.create(preview, "reject_closed_pilot_ui_job")
