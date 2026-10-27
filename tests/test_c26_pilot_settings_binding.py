"""A resumed v2 gate never authorizes a different loaded writer configuration."""

from types import SimpleNamespace

import pytest
import test_job_control as jobs
from test_deployment_gate_v2 import v2 as v2
from test_job_control import offline as offline
from test_job_control import setup as setup

from src.job_control.controller import Controller
from src.job_control.deployment_gate import Blocked, Gate, admission, dispatch
from src.job_control.executor import Executor
from src.job_control.models import Settings
from src.job_control.store import Store, Unavailable


@pytest.mark.parametrize(
    "change",
    [
        {"execution_enabled": False},
        {"max_jobs": 1},
        {"max_queued": 1},
        {"max_parallel": 2},
        {"worker_ttl": 10},
        {"pdf_enabled": True},
        {"workflows_enabled": True},
    ],
)
def test_settings_drift_blocks_api_store_dispatch_and_readiness(v2, setup, change):
    _, _, _, settings, _ = v2
    changed = Settings.model_validate(settings.model_dump() | change)
    with admission(settings):
        pass
    with pytest.raises(Blocked):
        with admission(changed):
            pytest.fail("Drifted writer admitted")
    with dispatch(changed) as allowed:
        assert allowed is False
    assert Gate(changed).status()["status"] == "blocked"
    controller = Controller(changed)
    env = SimpleNamespace(controller=controller, actor=setup.actor)
    body = jobs.request_data(env)
    with pytest.raises(Unavailable):
        controller.create(env.actor, body, "drifted_writer_request_denied")
    with pytest.raises(Blocked):
        with admission(controller.store):
            pytest.fail("Drifted queued transition admitted")
    assert not controller.store.all()


def test_unbound_store_cannot_reuse_an_open_v2_journal(v2):
    _, _, _, settings, _ = v2
    bare = Store(
        settings.root,
        deployment_gate_required=True,
        deployment_gate_protocol="c26-gate-v2",
    )
    with pytest.raises(Blocked):
        with admission(bare):
            pytest.fail("Bare store inferred approval from journal")


def test_execution_false_to_true_alone_never_opens_initialized_gate(setup):
    disabled = Settings.model_validate(
        setup.settings.model_dump()
        | {
            "execution_enabled": False,
            "deployment_gate_required": True,
            "deployment_gate_protocol": "c26-gate-v2",
            "max_jobs": 1,
        }
    )
    gate = Gate(disabled)
    gate.initialize()
    assert gate.status()["status"] == "blocked"
    with pytest.raises(Unavailable):
        Executor(disabled)
    enabled = Settings.model_validate(
        disabled.model_dump() | {"execution_enabled": True}
    )
    worker = Executor(enabled)
    try:
        controller = Controller(enabled)
        env = SimpleNamespace(controller=controller, actor=setup.actor)
        with pytest.raises(Blocked):
            controller.create(
                setup.actor, jobs.request_data(env), "explicit_resume_still_required"
            )
        with dispatch(enabled) as allowed:
            assert allowed is False
        assert gate.status()["phase"] == "held"
        assert not controller.store.all()
    finally:
        worker.close()
