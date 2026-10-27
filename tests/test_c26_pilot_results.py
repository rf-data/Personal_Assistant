"""Authenticated bounded result reads over real synthetic planning output."""

import json

import pytest
from test_c26_pilot_workflow import offline as offline
from test_c26_pilot_workflow import pilot as pilot
from test_job_control import DEMO_TOKEN, api, create, finish


@pytest.fixture
def completed(pilot):
    env, _, _, _, worker = pilot
    job = create(env)
    assert finish(env, worker, job).status == "completed"
    return env, job.job_id


def test_result_reads_verified_plan_and_rechecks_course_authorization(
    completed, monkeypatch
):
    env, job_id = completed
    route = f"/v1/jobs/{job_id}/result"
    code, result = api(env, "GET", route)
    assert code == 200
    assert result["protocol"] == "personal_assistant_material_plan_v1"
    assert result["artifact"]["job_id"] == job_id
    assert result["plan"]["materials"]
    assert (
        api(
            env,
            "GET",
            route,
            headers={
                "Authorization": "Bearer synthetic_viewer_token_000000000000000000"
            },
        )[0]
        == 200
    )
    before = {
        str(p): p.read_bytes() for p in env.settings.root.rglob("*") if p.is_file()
    }
    assert api(env, "GET", route)[0] == 200
    assert before == {
        str(p): p.read_bytes() for p in env.settings.root.rglob("*") if p.is_file()
    }

    def forbidden(*args):
        pytest.fail("Unauthorized caller read result bytes")

    monkeypatch.setattr("src.job_control.controller.read_file", forbidden)
    assert (
        api(
            env,
            "GET",
            route,
            headers={
                "Authorization": "Bearer unknown_synthetic_token_0000000000000000"
            },
        )[0]
        == 401
    )
    assert (
        api(
            env,
            "GET",
            route,
            headers={
                "Authorization": "Bearer synthetic_foreign_token_00000000000000000"
            },
        )[0]
        == 403
    )
    assert api(env, "GET", route + "?path=/etc/passwd")[0] == 422


@pytest.mark.parametrize("damage", ["missing", "bytes", "oversized", "symlink"])
def test_missing_or_changed_result_fails_closed_without_exposing_paths(
    completed, damage
):
    env, job_id = completed
    job = env.controller.get(env.actor, job_id)
    path = env.controller.store.directory(job_id) / "results/material-plan.json"
    if damage == "missing":
        path.unlink()
    elif damage == "bytes":
        path.write_text("synthetic_private_result_marker")
    elif damage == "oversized":
        path.write_bytes(b"x" * (256 * 1024 + 1))
    else:
        target = path.rename(path.with_suffix(".original"))
        path.symlink_to(target)
    code, body = api(env, "GET", f"/v1/jobs/{job_id}/result")
    assert code == 503
    assert body["error"]["code"] == "unavailable"
    assert "synthetic_private_result_marker" not in json.dumps(body)
    assert str(path) not in json.dumps(body)
    assert env.controller.get(env.actor, job_id) == job


def test_result_before_completed_job_is_conflict(pilot):
    env, _, _, _, _ = pilot
    job = create(env)
    assert api(env, "GET", f"/v1/jobs/{job.job_id}/result")[0] == 409


def test_result_authentication_is_required_even_without_a_known_job(pilot):
    env, _, _, _, _ = pilot
    code, _, _ = env.app.request("GET", "/v1/jobs/unknown/result", {})
    assert code == 401
    assert (
        api(
            env,
            "GET",
            "/v1/jobs/unknown/result",
            headers={"Authorization": "Bearer " + DEMO_TOKEN},
        )[0]
        == 404
    )
