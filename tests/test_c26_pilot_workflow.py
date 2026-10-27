"""Single synthetic planning job through C16, mandatory v2 and the real executor."""

import json
from types import SimpleNamespace

import pytest
import test_deployment_gate_v2 as gate_tests
import test_job_control as jobs

from src.job_control.controller import Controller
from src.job_control.deployment_gate import Blocked, Gate
from src.job_control.http import Application
from src.job_control.models import Settings
from src.job_control.store import Unavailable

offline = jobs.offline


@pytest.fixture
def pilot(tmp_path):
    initial = jobs.setup.__wrapped__(tmp_path)
    settings = initial.settings.model_copy(
        update={
            "max_jobs": 1,
            "max_queued": 1,
            "max_parallel": 1,
            "catalog": {"demo_snapshots": initial.settings.catalog["demo_snapshots"]},
        }
    )
    initial.settings = settings
    # Reuse the existing v2 scope/approval fixture, explicitly synthetic only.
    context = gate_tests.v2.__wrapped__(initial)
    gate, plan, driver, settings, worker = next(context)
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + jobs.DEMO_TOKEN)
    env = SimpleNamespace(
        settings=settings,
        controller=controller,
        actor=actor,
        app=Application(controller),
        tmp=tmp_path,
    )
    try:
        yield env, gate, plan, driver, worker
    finally:
        context.close()


def test_one_authorized_plan_survives_client_replacement_and_blocks_second_job(pilot):
    env, gate, plan, driver, worker = pilot
    body = jobs.request_data(env)
    assert env.controller.store.all() == ()
    status, _ = jobs.api(env, "POST", "/v1/jobs", body | {"confirmed": False})
    assert status == 422
    job = jobs.create(env)
    # An independent server-side caller observes the same persistent queue.
    replacement = Controller(env.settings)
    completed = jobs.finish(env, worker, job)
    assert completed.status == "completed"
    assert replacement.get(env.actor, job.job_id).status == "completed"
    assert replacement.get(env.actor, job.job_id).artifact_refs
    with pytest.raises(Unavailable):
        jobs.create(env, key="second_pilot_job_rejected")
    # Deployment is inert, leaves intake closed and needs a new resume approval.
    result = gate.run(plan, gate_tests.approve(plan), driver)
    assert result["status"] == "verified_offline"
    assert gate.status()["phase"] == "verified"
    assert result["deployment_permitted"] is False
    with pytest.raises(Blocked):
        jobs.create(env, key="closed_pilot_job_rejected")


@pytest.mark.parametrize("damage", ["missing", "corrupt", "locked", "disabled"])
def test_missing_gate_or_execution_configuration_cannot_authorize_a_job(pilot, damage):
    env, _, _, _, _ = pilot
    from src.job_control.deployment_gate import JOURNAL_V2, LOCK, _lock

    if damage == "disabled":
        settings = Settings.model_validate(
            env.settings.model_dump() | {"execution_enabled": False}
        )
        env.controller = Controller(settings)
        with pytest.raises(Unavailable):
            jobs.create(env)
    elif damage == "locked":
        with _lock(env.settings.root, LOCK):
            with pytest.raises(Blocked):
                jobs.create(env)
    else:
        journal = env.settings.root / JOURNAL_V2
        if damage == "missing":
            journal.unlink()
        else:
            journal.write_text(json.dumps({"phase": "open"}) + "\n")
        assert Gate(env.settings).status()["status"] == "blocked"
        with pytest.raises(Blocked):
            jobs.create(env)
    assert env.controller.store.all() == ()
