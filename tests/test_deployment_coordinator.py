"""C26-F synthetic independent coordinator; no production identities or drivers."""

import fcntl
import hashlib
import hmac
import os
import threading
import time
import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from test_coolify_observer import fixture as observer_fixture
from test_deployment_gate_v2 import FixtureDriver, approve, make_plan
from test_job_control import offline as offline
from test_job_control import setup as setup

from src.job_control.controller import Controller
from src.job_control.coolify_observer import RuntimeScope
from src.job_control.coordinator_state import ENROLLMENT, LocalTestWitness, Refused
from src.job_control.deployment_coordinator import (
    InertDriver,
    OfflineCoordinator,
    OperatorGrant,
    SignedGrant,
)
from src.job_control.deployment_gate import (
    JOURNAL_V2,
    Blocked,
    Gate,
    admission,
    dispatch,
    settings_digest,
)
from src.job_control.executor import Executor
from src.job_control.models import canonical
from src.job_control.runtime_collector import BuildReceipt


class FixtureIssuer:
    """Only tests have this issuing API/key. Coordinator receives only verify()."""

    def __init__(self):
        self.key = b"synthetic_test_authority_key_not_a_real_credential"
        self.verifier = SimpleNamespace(verify=self.verify)

    def issue(self, challenge, **updates):
        grant = OperatorGrant(
            grant_id="grant_" + uuid.uuid4().hex,
            issuer="fixture_authority",
            subject="fixture_operator",
            role="operator",
            challenge=challenge,
            issued_at=float(time.time()),
            expires_at=challenge.expires_at,
        )
        grant = OperatorGrant.model_validate(grant.model_dump() | updates)
        return SignedGrant(
            grant=grant,
            signature=hmac.new(
                self.key, canonical(grant.model_dump(mode="json")), hashlib.sha256
            ).hexdigest(),
        )

    def verify(self, envelope):
        expected = hmac.new(
            self.key, canonical(envelope.grant.model_dump(mode="json")), hashlib.sha256
        ).hexdigest()
        if (
            not hmac.compare_digest(expected, envelope.signature)
            or envelope.grant.issuer != "fixture_authority"
            or envelope.grant.subject != "fixture_operator"
        ):
            raise ValueError("synthetic authority refused")
        return envelope.grant


@pytest.fixture
def coordinated(setup, tmp_path):
    settings = setup.settings.model_copy(
        update=dict(
            deployment_gate_required=True,
            deployment_gate_protocol="c26-gate-v2",
            coordinator_test_required=True,
            worker_ttl=30,
        )
    )
    gate = Gate(settings)
    gate.initialize()
    witness_root = tmp_path / "witness"
    witness_root.mkdir(mode=0o700)
    witness = LocalTestWitness.create(witness_root / "anchor.sqlite3")
    OfflineCoordinator.enroll(settings, witness)
    worker = Executor(settings)
    binding, _, _ = observer_fixture()
    data = binding.scope.model_dump(mode="json")
    data["settings_sha256"] = settings_digest(settings)
    info = settings.root.stat()
    data["jobroot"].update(
        source=str(settings.root),
        destination=str(settings.root),
        device=info.st_dev,
        inode=info.st_ino,
    )

    def receipts_for_scope(values):
        for role in values["roles"]:
            receipt = BuildReceipt(
                authority_id="build_authority",
                repository=values["repository"],
                revision=role["revision"],
                image_id=role["image_id"],
                repo_digest=role["image"],
                verification="registry_digest_and_build_attestation_verified",
            )
            role["build_receipt_sha256"] = hashlib.sha256(
                canonical(receipt.model_dump(mode="json"))
            ).hexdigest()
        return values

    current = RuntimeScope.model_validate(receipts_for_scope(data))
    data = current.model_dump(mode="json")
    for i in (0, 2):
        data["roles"][i].update(
            revision="b" * 40,
            image="registry.invalid/backend@sha256:" + "3" * 64,
            image_id="sha256:" + "4" * 64,
            build_receipt_sha256="5" * 64,
        )
    target = RuntimeScope.model_validate(receipts_for_scope(data))
    issuer = FixtureIssuer()
    driver = InertDriver(current)

    def evidence(plan, scope, generation):
        source = FixtureDriver(scope)
        source.generation = generation
        return source.observe(plan)

    coordinator = OfflineCoordinator(
        settings,
        witness=witness,
        verifier=issuer.verifier,
        evidence=evidence,
        driver=driver,
    )
    bootstrap = make_plan(current, current)
    with coordinator.session(bootstrap, "resume") as session:
        session.execute(issuer.issue(session.request()))
    try:
        yield SimpleNamespace(
            settings=settings,
            gate=gate,
            controller=Controller(settings),
            actor=setup.actor,
            tmp=tmp_path,
            witness=witness,
            worker=worker,
            issuer=issuer,
            driver=driver,
            coordinator=coordinator,
            plan=make_plan(current, target),
        )
    finally:
        worker.close()


def execute(ctx, plan=None, action="deploy", **kwargs):
    with ctx.coordinator.session(plan or ctx.plan, action, **kwargs) as session:
        return session.execute(ctx.issuer.issue(session.request()))


def test_success_separate_resume_and_no_coordinator_signing_api(coordinated):
    c = coordinated
    assert not hasattr(c.coordinator, "issue")
    result = execute(c)
    assert result["phase"] == "verified" and result["admissions"] == "closed"
    assert (
        result["production_release"] == "blocked"
        and result["deployment_permitted"] is False
    )
    assert c.driver.calls == 1
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    execute(c, action="resume")
    with admission(c.settings):
        pass
    with dispatch(c.settings) as permitted:
        assert permitted


@pytest.mark.parametrize(
    "update",
    [
        {"role": "observer"},
        {"expires_at": 1.0},
        {"issued_at": time.time() + 500},
        {"subject": "untrusted"},
        {"issuer": "other"},
    ],
)
def test_external_authorization_required_and_time_identity_role_checked(
    coordinated, update
):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        challenge = session.request()
        with pytest.raises(Refused):
            session.execute(c.issuer.issue(challenge, **update))
    assert c.driver.calls == 0
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_scope_sha256", "0" * 64),
        ("plan_sha256", "0" * 64),
        ("session_id", "0" * 64),
        ("epoch", 999),
        ("resource_id", "other"),
        ("server_id", "other"),
        ("action", "resume"),
        ("journal_sha256", "0" * 64),
    ],
)
def test_signed_but_mismatched_grant_rejected(coordinated, field, value):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        challenge = session.request()
        changed = challenge.model_copy(update={field: value})
        with pytest.raises(Refused):
            session.execute(c.issuer.issue(changed))
    assert c.driver.calls == 0


def test_unsigned_cli_assertion_and_corrupt_signature_rejected(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        signed = c.issuer.issue(session.request())
        with pytest.raises(Blocked):
            session.execute(signed.grant)
    # Failed attempt has no automatic retry or release.
    with pytest.raises(Refused):
        execute(c)
    assert c.driver.calls == 0


def test_double_coordinator_and_lock_loss_leave_closed(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        with pytest.raises(Blocked):
            with c.coordinator.session(c.plan, "deploy"):
                pass
        grant = c.issuer.issue(session.request())
        fcntl.flock(session.fd, fcntl.LOCK_UN)
        with pytest.raises(Refused):
            session.execute(grant)
    assert c.driver.calls == 0
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_approval_replay_and_double_permit_claim_are_blocked(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        grant = c.issuer.issue(session.request())
        session.execute(grant)
        with pytest.raises(Refused):
            session.execute(grant)
    execute(c, action="resume")
    with c.coordinator.session(c.plan, "deploy") as session:
        session.request()
        with pytest.raises(Refused):
            session.execute(grant)
    assert c.driver.calls == 1


@pytest.mark.parametrize("stage", ["before_claim", "after_claim", "after_change"])
def test_interruption_never_automatically_repeats_driver_or_resumes(coordinated, stage):
    c = coordinated

    def fail(actual):
        if stage == actual:
            raise RuntimeError("synthetic interrupted operation")

    c.driver.hook = fail
    with pytest.raises(Blocked):
        execute(c)
    assert c.gate.status()["phase"] == "recovery"
    assert c.driver.calls == (1 if stage == "after_change" else 0)
    with pytest.raises(Refused):
        execute(c)
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_recover_after_change_then_explicit_rollback_and_resume(coordinated):
    c = coordinated
    c.driver.hook = lambda stage: (
        (_ for _ in ()).throw(RuntimeError("synthetic"))
        if stage == "after_change"
        else None
    )
    with pytest.raises(Blocked):
        execute(c)
    c.driver.hook = lambda stage: None
    execute(c, action="recover", recover=True)
    assert c.gate.status()["phase"] == "verified"
    reverse = make_plan(c.plan.operation.target, c.plan.operation.current)
    execute(c, plan=reverse, action="rollback")
    assert c.driver.calls == 2
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    execute(c, plan=reverse, action="resume")
    with admission(c.settings):
        pass


def test_whole_valid_journal_rollback_detected_by_test_witness(coordinated):
    c = coordinated
    old = (c.settings.root / JOURNAL_V2).read_bytes()
    execute(c)
    (c.settings.root / JOURNAL_V2).write_bytes(old)
    assert c.gate.status()["status"] == "blocked"
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    with dispatch(c.settings) as allowed:
        assert not allowed
    with pytest.raises(Refused):
        execute(c, action="resume")


def test_missing_external_state_or_enrollment_blocks_even_open_gate(coordinated):
    c = coordinated
    with c.witness.connection(write=True) as db:
        db.execute("DELETE FROM anchors")
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    with dispatch(c.settings) as allowed:
        assert not allowed
    assert c.gate.status()["status"] == "blocked"
    # Fixture corruption, no deletion of pre-existing project files.
    (c.settings.root / ENROLLMENT).write_bytes(b"{}")
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_direct_gate_cannot_bypass_coordinator_authorization(coordinated):
    c = coordinated

    class Driver:
        def observe(self, plan):
            raise AssertionError("must not observe")

        def deploy(self, plan, permit):
            raise AssertionError("must not deploy")

    with pytest.raises(Blocked, match="coordinator_session_required"):
        c.gate.run(c.plan, approve(c.plan), Driver())
    assert c.driver.calls == 0


@pytest.mark.parametrize(
    "corruption",
    [
        "signature",
        "challenge_expired",
        "scope",
        "missing_heartbeat",
        "late_heartbeat",
        "identity",
        "stale_evidence",
    ],
)
def test_trust_failures_prevent_claim_and_keep_queue_closed(coordinated, corruption):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        grant = c.issuer.issue(session.request())
        if corruption == "signature":
            grant = grant.model_copy(update={"signature": "0" * 64})
        elif corruption == "challenge_expired":
            c.coordinator.clock = lambda: session.challenge.expires_at + 1
        elif corruption == "scope":
            session.plan = session.plan.model_copy(
                update={"protected_resources_sha256": "0" * 64}
            )
        elif corruption in {"missing_heartbeat", "late_heartbeat"}:
            with c.worker.store.connection(write=True) as db:
                if corruption == "missing_heartbeat":
                    db.execute("DELETE FROM worker")
                else:
                    db.execute("UPDATE worker SET heartbeat=1 WHERE id=1")
        elif corruption == "identity":
            c.driver.generation += 1
        else:
            original = c.coordinator.evidence

            def stale(plan, scope, generation):
                value = original(plan, scope, generation)
                raw = value.model_dump(mode="json")
                raw["evidence"]["provenance"]["observed_at"] = time.time() - 31
                return type(value).model_validate(raw)

            c.coordinator.evidence = stale
        with pytest.raises((Blocked, Refused)):
            session.execute(grant, drain_timeout=0)
    assert c.driver.calls == 0
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_real_synthetic_queue_drains_and_rejects_new_intake(coordinated):
    from test_job_control import create, finish

    c = coordinated
    job = create(c)
    outcome = []

    def deploy():
        try:
            outcome.append(execute(c))
        except BaseException as error:
            outcome.append(error)

    thread = threading.Thread(target=deploy)
    thread.start()
    until = time.monotonic() + 5
    while c.gate.status().get("phase") != "draining":
        if outcome and isinstance(outcome[0], BaseException):
            raise outcome[0]
        if time.monotonic() > until:
            pytest.fail("drain did not start")
        time.sleep(0.01)
    with pytest.raises(Blocked):
        create(c, key="coordinator_rejected_new_job")
    result = finish(c, c.worker, job)
    assert result.status == "completed"
    thread.join(5)
    assert not thread.is_alive() and isinstance(outcome[0], dict)
    assert c.driver.calls == 1 and c.gate.status()["phase"] == "verified"


def test_aborted_drain_does_not_cancel_or_deploy(coordinated):
    from test_job_control import create

    c = coordinated
    job = create(c)
    with c.coordinator.session(c.plan, "deploy") as session:
        grant = c.issuer.issue(session.request())
        with pytest.raises(Blocked, match="drain_timeout"):
            session.execute(grant, drain_timeout=0)
    assert c.driver.calls == 0
    assert c.controller.get(c.actor, job.job_id).status == "queued"
    assert c.gate.status()["phase"] == "recovery"


@pytest.mark.parametrize(
    "fault", ["missing", "uncertain", "wrong_session", "partial_rollback"]
)
def test_driver_receipt_and_incomplete_rollback_never_resume(
    coordinated, monkeypatch, fault
):

    c = coordinated
    if fault == "partial_rollback":
        execute(c)
        plan = make_plan(c.plan.operation.target, c.plan.operation.current)
        action = "rollback"
    else:
        plan, action = c.plan, "deploy"
    change = c.driver.change

    def altered(plan, permit):
        receipt = change(plan, permit)
        if fault == "missing":
            return None
        if fault == "uncertain":
            return receipt.model_copy(update={"status": "uncertain"})
        if fault == "wrong_session":
            return receipt.model_copy(update={"session_id": "0" * 64})
        c.driver.scope = (
            plan.operation.current
        )  # Synthetic rollback did not reach target.
        return receipt

    monkeypatch.setattr(c.driver, "change", altered)
    with pytest.raises((Blocked, Refused)):
        execute(c, plan=plan, action=action)
    assert c.gate.status()["phase"] == "recovery"
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_durable_grant_id_is_single_use_across_fresh_challenges(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        first = c.issuer.issue(session.request())
        session.execute(first)
    with c.coordinator.session(c.plan, "resume") as session:
        token = c.issuer.issue(session.request(), grant_id=first.grant.grant_id)
        with pytest.raises(Refused, match="grant_replay"):
            session.execute(token)
    assert c.driver.calls == 1


def test_external_compare_and_swap_has_one_winner(coordinated):
    c = coordinated
    from src.job_control.coordinator_state import root_identity

    before = c.witness.read(root_identity(c.settings.root))
    changed = before.model_copy(update={"revision": before.revision + 1})
    c.witness.cas(before, changed)
    with pytest.raises(Refused, match="cas_conflict"):
        c.witness.cas(before, changed)
    assert c.witness.read(before.root_id) == changed


def test_no_default_activation_and_legacy_hashes_unchanged(coordinated):
    from src.job_control.models import Settings

    c = coordinated
    assert Settings.model_fields["coordinator_test_required"].default is False
    legacy = c.settings.model_copy(update={"coordinator_test_required": False})
    raw = legacy.model_dump(mode="json")
    raw.pop("coordinator_test_required")
    assert settings_digest(legacy) == hashlib.sha256(canonical(raw)).hexdigest()
    with pytest.raises(ValidationError):
        Settings.model_validate(
            c.settings.model_dump() | {"deployment_gate_required": False}
        )
    with pytest.raises(ValidationError):
        Settings.model_validate(
            c.settings.model_dump() | {"deployment_gate_protocol": "c26-gate-v1"}
        )
    with pytest.raises(Refused):
        OfflineCoordinator(
            legacy,
            witness=c.witness,
            verifier=c.issuer.verifier,
            evidence=c.coordinator.evidence,
            driver=c.driver,
        )


def test_required_enrollment_missing_cannot_fall_back_to_v2(coordinated):
    c = coordinated
    (c.settings.root / ENROLLMENT).rename(c.tmp / "owned_enrollment_fixture_saved")
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    with dispatch(c.settings) as allowed:
        assert not allowed
    assert c.gate.status()["status"] == "blocked"


def _wait_child(pid):
    import signal

    until = time.monotonic() + 5
    while time.monotonic() < until:
        ended, status = os.waitpid(pid, os.WNOHANG)
        if ended:
            return os.waitstatus_to_exitcode(status)
        time.sleep(0.01)
    os.kill(pid, signal.SIGKILL)  # Only this test's own timed-out disposable child.
    os.waitpid(pid, 0)
    pytest.fail("bounded fixture child timed out")


def test_second_coordinator_process_is_excluded(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy"):
        pid = os.fork()
        if pid == 0:
            try:
                with c.coordinator.session(c.plan, "deploy"):
                    os._exit(2)
            except Blocked:
                os._exit(0)
            except BaseException:
                os._exit(3)
        assert _wait_child(pid) == 0
    assert c.driver.calls == 0


@pytest.mark.parametrize(
    "stage", ["before_authorization", "before_claim", "after_claim", "after_change"]
)
def test_abrupt_own_process_crash_retains_fence_and_requires_new_grant(
    coordinated, stage
):
    c = coordinated
    pid = os.fork()
    if pid == 0:

        def crash(actual):
            if actual == stage:
                os._exit(91)

        c.driver.hook = crash
        try:
            with c.coordinator.session(c.plan, "deploy") as session:
                challenge = session.request()
                if stage == "before_authorization":
                    os._exit(91)
                session.execute(c.issuer.issue(challenge))
        except BaseException:
            os._exit(92)
        os._exit(93)
    assert _wait_child(pid) == 91
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    with pytest.raises(Refused):
        execute(c)
    if stage == "after_change":
        # Reconstruct only the known synthetic fixture runtime state, not a retry.
        c.driver.scope = c.plan.operation.target
        c.driver.generation = 1
        c.driver.calls = 1
        execute(c, action="recover", recover=True)
        assert c.driver.calls == 1 and c.gate.status()["phase"] == "verified"
        execute(c, action="resume")
        with admission(c.settings):
            pass
    elif stage == "before_authorization":
        current = make_plan(c.plan.operation.current, c.plan.operation.current)
        execute(c, plan=current, action="recover", recover=True)
        execute(c, plan=current, action="resume")
        assert c.driver.calls == 0
    else:
        # Unclear/prechange deployment never gets an automatic replay or resume.
        with pytest.raises((Refused, Blocked)):
            execute(c, action="recover", recover=True)
        assert c.driver.calls == 0


def test_lock_lost_after_claim_prevents_inert_change(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        grant = c.issuer.issue(session.request())

        def lose(stage):
            if stage == "after_claim":
                fcntl.flock(session.fd, fcntl.LOCK_UN)

        c.driver.hook = lose
        with pytest.raises((Blocked, Refused)):
            session.execute(grant)
    assert c.driver.calls == 0
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass


def test_external_failure_after_gate_open_still_blocks_queue(coordinated, monkeypatch):
    c = coordinated
    execute(c)
    cas = c.witness.cas

    def fail(previous, replacement, **kwargs):
        if replacement.status == "released":
            raise Refused("synthetic witness unavailable")
        return cas(previous, replacement, **kwargs)

    monkeypatch.setattr(c.witness, "cas", fail)
    with pytest.raises(Refused):
        execute(c, action="resume")
    assert c.gate.status()["phase"] == "open" and c.gate.status()["status"] == "blocked"
    with pytest.raises(Blocked):
        with admission(c.settings):
            pass
    with dispatch(c.settings) as allowed:
        assert not allowed
    monkeypatch.setattr(c.witness, "cas", cas)
    execute(c, action="recover", recover=True)
    execute(c, action="resume")
    with admission(c.settings):
        pass


def test_c22_copy_of_enrolled_root_cannot_reuse_external_identity(coordinated):
    from src.job_control.operations import backup, restore

    c = coordinated
    config = c.tmp / "profile.json"
    config.write_text(c.settings.model_dump_json())
    config.chmod(0o600)
    original = (c.settings.root / JOURNAL_V2).read_bytes()
    c.worker.close()
    try:
        backup(config, c.tmp / "snapshot")
        target = c.tmp / "restored"
        result = restore(c.tmp / "snapshot", target)
        assert result["activated"] is False
        assert not (target / ".coordinator-session.lock").exists()
        copied = c.settings.model_copy(update={"root": target})
        with pytest.raises(Blocked):
            with admission(copied):
                pass
        assert (c.settings.root / JOURNAL_V2).read_bytes() == original
    finally:
        c.worker.__init__(c.settings)


def test_published_coordinator_schemas_match_models():
    import json
    from pathlib import Path

    from src.job_control.coordinator_contracts import IntegrationContract
    from src.job_control.coordinator_state import Anchor, Enrollment
    from src.job_control.deployment_coordinator import Challenge, DriverReceipt

    folder = Path(__file__).resolve().parents[1] / "docs/deployment/c26_runtime"
    for model, name in [
        (Challenge, "coordinator_challenge.v1.schema.json"),
        (SignedGrant, "coordinator_grant.v1.schema.json"),
        (Anchor, "coordinator_anchor.v1.schema.json"),
        (Enrollment, "coordinator_enrollment.v1.schema.json"),
        (IntegrationContract, "coordinator_integration.v1.schema.json"),
        (DriverReceipt, "coordinator_driver_receipt.v1.schema.json"),
    ]:
        assert json.loads((folder / name).read_text()) == model.model_json_schema()


def test_saved_or_copied_permit_cannot_be_reused(coordinated, monkeypatch):
    import copy

    c = coordinated
    saved = []
    change = c.driver.change

    def retain(plan, permit):
        saved.append(permit)
        return change(plan, permit)

    monkeypatch.setattr(c.driver, "change", retain)
    execute(c)
    for permit in [saved[0], copy.copy(saved[0])]:
        with pytest.raises(Refused):
            permit.claim()
        with pytest.raises(Refused):
            permit.check()
    assert c.driver.calls == 1


def test_lock_file_replacement_invalidates_session(coordinated):
    from src.job_control.coordinator_state import SESSION_LOCK

    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        token = c.issuer.issue(session.request())
        path = c.settings.root / SESSION_LOCK
        path.rename(c.tmp / "owned_original_lock_fixture")
        path.write_bytes(b"")
        path.chmod(0o600)
        with pytest.raises(Refused):
            session.execute(token)
    assert c.driver.calls == 0


def test_driver_counter_cannot_authorize_unapproved_instance_change(coordinated):
    c = coordinated
    with c.coordinator.session(c.plan, "deploy") as session:
        token = c.issuer.issue(session.request())
        c.driver.generation += 1
        c.driver.calls += (
            1  # Untrusted progress metadata cannot waive baseline binding.
        )
        with pytest.raises((Blocked, Refused)):
            session.execute(token)
    assert c.gate.status()["status"] == "blocked"


def test_driver_refuses_a_caller_claiming_to_be_a_permit(coordinated):
    c = coordinated
    impostor = SimpleNamespace(claim=lambda: None, check=lambda: None)
    with pytest.raises(Refused, match="bound_permit_required"):
        c.driver.change(c.plan, impostor)
    assert c.driver.calls == 0 and c.driver.scope == c.plan.operation.current
