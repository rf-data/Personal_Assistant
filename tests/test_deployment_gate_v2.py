"""Synthetic v2 integration over real disposable C16 locks/SQLite, no live driver."""

import copy
import hashlib
import json
import threading
import time
import uuid

import pytest
from pydantic import ValidationError
from test_coolify_observer import fixture as observer_fixture
from test_job_control import offline as offline
from test_job_control import setup as setup

from src.job_control.coolify_observer import RuntimeScope, bind_gate_plan
from src.job_control.deployment_gate import (
    JOURNAL,
    JOURNAL_V2,
    Approval,
    Blocked,
    Gate,
    Plan,
    _read,
    admission,
    dispatch,
    settings_digest,
)
from src.job_control.deployment_scope import ApprovalV2, ObservationV2, PlanV2
from src.job_control.executor import Executor
from src.job_control.models import Settings, canonical


def make_plan(current, target):
    legacy = Plan(
        resource_id=current.application_uuid,
        role="api",
        current_sha=current.roles[0].revision,
        target_sha=target.roles[0].revision,
        current_image=current.roles[0].image,
        target_image=target.roles[0].image,
        settings_sha256=current.settings_sha256,
        persistence_sha256=current.persistence_sha256,
        protected_resources_sha256=current.protected_resources_sha256,
    )
    return PlanV2(
        **legacy.model_dump(), operation=bind_gate_plan(legacy, current, target)
    )


def approve(plan, action="deploy", **updates):
    values = dict(
        approval_id="fixture_" + uuid.uuid4().hex,
        approved_by="offline_operator",
        action=action,
        plan_sha256=plan.digest,
        runtime_scope_sha256=plan.operation.runtime_scope_sha256,
        approved_at=time.time() - 1,
        expires_at=time.time() + 300,
        confirmed=True,
    )
    return ApprovalV2(**(values | updates))


class FixtureDriver:
    def __init__(self, scope):
        self.scope = scope
        self.generation = 0
        self.calls = 0
        self.observations = 0
        self.mutate = None
        self.callback = None
        self.fail_after = False
        self.saved = None

    def observe(self, plan):
        self.observations += 1
        scope = self.scope
        _, _, raw = observer_fixture()
        now = time.time()
        ids = {
            role.role: f"{i + 1 + self.generation * 10:064x}"
            for i, role in enumerate(scope.roles)
        }
        containers = []
        images = {}
        members = []
        for i, role in enumerate(scope.roles):
            template = list(raw["containers"].values())[i]
            item = dict(
                template,
                container_id=ids[role.role],
                image_id=role.image_id,
                command_sha256=role.command_sha256,
                mounts=[m.model_dump() for m in role.mounts],
                jobroot=scope.jobroot.model_dump() if i != 1 else None,
                settings_sha256=scope.settings_sha256 if i != 1 else None,
                health_contract_sha256=role.health_contract_sha256,
                readiness_contract_sha256=role.readiness_contract_sha256,
                network_mode="container:" + ids["api-gateway"]
                if i == 0
                else scope.private_network_name
                if i == 1
                else "none",
                network_namespace="shared" + str(self.generation)
                if i != 2
                else "worker" + str(self.generation),
                network_ids=[scope.private_network_id] if i == 1 else [],
                heartbeat_at=now if i == 2 else None,
            )
            containers.append(item)
            images[role.image_id] = dict(
                image_id=role.image_id,
                repo_digests=[role.image],
                repository=scope.repository,
                revision=role.revision,
                provenance="verified_build_receipt",
                build_receipt_sha256=role.build_receipt_sha256,
            )
            members.append(
                dict(
                    container_id=ids[role.role],
                    application_uuid=scope.application_uuid,
                    compose_project=scope.compose_project,
                    writable_sources=[m.source for m in role.mounts if not m.read_only],
                )
            )
        boundary = raw["boundary"] | {
            key: getattr(scope, key)
            for key in raw["boundary"]
            if key in RuntimeScope.model_fields
        }
        boundary["jobroot_writer_ids"] = [ids["api"], ids["capacity-worker"]]
        deployment = "deployment_" + str(self.generation)
        payload = dict(
            binding=dict(
                scope=scope.model_dump(),
                phase="target" if scope == plan.operation.target else "current",
                deployment_uuid=deployment,
                host_id="host",
                adapter_id="synthetic",
            ),
            evidence=dict(
                provenance=dict(
                    host_id="host", adapter_id="synthetic", observed_at=now
                ),
                inventory=dict(complete=True, members=members),
                boundary=boundary,
                containers=containers,
                images=list(images.values()),
            ),
            application=dict(
                uuid=scope.application_uuid,
                build_pack="dockercompose",
                git_repository=scope.repository,
                git_branch=scope.branch,
                git_commit_sha=scope.roles[0].revision,
                base_directory="/",
                docker_compose_location=scope.compose_location,
                auto_deploy_enabled=False,
                preview_deployments_enabled=False,
            ),
            deployment=dict(
                deployment_uuid=deployment,
                commit=scope.roles[0].revision,
                status="finished",
                pull_request_id=0,
            ),
        )
        if self.mutate:
            self.mutate(payload)
        return ObservationV2.model_validate(payload)

    def deploy(self, plan, permit):
        self.saved = permit
        if self.callback:
            self.callback(plan, permit)
        permit.claim()
        self.calls += 1
        self.scope = plan.operation.target
        self.generation += 1
        if self.fail_after:
            raise RuntimeError("synthetic interrupted operation")


@pytest.fixture
def v2(setup):
    settings = setup.settings.model_copy(
        update=dict(
            deployment_gate_required=True,
            deployment_gate_protocol="c26-gate-v2",
            worker_ttl=30,
        )
    )
    gate = Gate(settings)
    gate.initialize()
    worker = Executor(settings)
    original, _, _ = observer_fixture()
    values = original.scope.model_dump(mode="json")
    values["settings_sha256"] = settings_digest(settings)
    info = settings.root.stat()
    values["jobroot"].update(
        source=str(settings.root),
        destination=str(settings.root),
        device=info.st_dev,
        inode=info.st_ino,
    )
    current = RuntimeScope.model_validate(values)
    target_data = copy.deepcopy(values)
    for i in (0, 2):
        target_data["roles"][i].update(
            revision="b" * 40,
            image="registry.invalid/backend@sha256:" + "3" * 64,
            image_id="sha256:" + "4" * 64,
            build_receipt_sha256="5" * 64,
        )
    target = RuntimeScope.model_validate(target_data)
    plan = make_plan(current, target)
    driver = FixtureDriver(current)
    bootstrap = make_plan(current, current)
    gate.release(bootstrap, approve(bootstrap, "resume"), driver)
    try:
        yield gate, plan, driver, settings, worker
    finally:
        worker.close()


def test_positive_operation_then_explicit_resume_stays_offline(v2):
    gate, plan, driver, settings, _ = v2
    result = gate.run(plan, approve(plan), driver)
    assert (
        result["status"] == "verified_offline"
        and result["production_release"] == "blocked"
    )
    assert result["deployment_permitted"] is False and driver.calls == 1
    assert gate.status()["phase"] == "verified"
    with pytest.raises(Blocked):
        driver.saved.claim()
    assert gate.release(plan, approve(plan, "resume"), driver)["phase"] == "open"
    with admission(settings):
        pass
    rows = _read(settings.root, version=2)
    assert all(
        r["schema_version"] == 2 and r["protocol"] == "c26-gate-v2" for r in rows
    )
    assert rows[-1]["runtime_scope_sha256"] == plan.operation.runtime_scope_sha256
    assert not (settings.root / JOURNAL).exists()


@pytest.mark.parametrize(
    "change",
    [
        {"plan_sha256": "0" * 64},
        {"runtime_scope_sha256": "0" * 64},
        {"expires_at": 1.0},
        {"confirmed": False},
        {"action": "resume"},
    ],
)
def test_approval_mismatch_never_dispatches(v2, change):
    gate, plan, driver, _, _ = v2
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan, **change), driver)
    assert driver.calls == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["evidence"]["boundary"].update(trigger_inventory_complete=False),
        lambda p: p["evidence"]["containers"][0].update(settings_sha256="0" * 64),
        lambda p: p["evidence"]["containers"][0].update(image_id="sha256:" + "0" * 64),
        lambda p: p["evidence"]["images"][0].update(build_receipt_sha256="0" * 64),
        lambda p: p["evidence"]["provenance"].update(observed_at=time.time() - 31),
        lambda p: p["evidence"]["containers"][2].update(heartbeat_at=time.time() - 11),
        lambda p: p["evidence"]["boundary"].update(writer_inventory_complete=None),
        lambda p: p["evidence"]["boundary"].update(tls_verified=False),
        lambda p: p["evidence"]["containers"][0].update(ready=False),
    ],
)
def test_runtime_evidence_failures(v2, mutate):
    gate, plan, driver, _, _ = v2
    driver.mutate = mutate
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert driver.calls == 0


def test_missing_scope_wrong_version_and_forged_gate_anchor(v2):
    _, plan, _, _, _ = v2
    raw = plan.model_dump(mode="json")
    for field, value in [
        ("operation", None),
        ("schema_version", 1),
        ("protocol", "c26-gate-v1"),
    ]:
        with pytest.raises(ValidationError):
            PlanV2.model_validate(raw | {field: value})
    raw["operation"]["gate_plan_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        PlanV2.model_validate(raw)


def test_scope_changed_after_approval_and_live_mode_refused(v2):
    gate, plan, driver, _, _ = v2
    approval = approve(plan)
    raw = plan.operation.target.model_dump(mode="json")
    raw["caddy_sha256"] = "0" * 64
    changed = make_plan(plan.operation.current, RuntimeScope.model_validate(raw))
    with pytest.raises(Blocked):
        gate.run(changed, approval, driver)
    with pytest.raises(ValidationError):
        PlanV2.model_validate(plan.model_dump(mode="json") | {"mode": "live"})
    assert driver.calls == 0


def test_replayed_approval_and_copied_or_reactivated_permit(v2):
    gate, plan, driver, _, _ = v2
    approval = approve(plan)

    def callback(plan, permit):
        with pytest.raises(Blocked):
            copy.copy(permit).check()

    driver.callback = callback
    gate.run(plan, approval, driver)
    driver.saved.active = True
    with pytest.raises(Blocked):
        driver.saved.check()
    gate.release(plan, approve(plan, "resume"), driver)
    with pytest.raises(Blocked):
        gate.run(plan, approval, driver)
    assert driver.calls == 1


def test_permit_scope_tampering_and_evidence_drift_abort(v2):
    gate, plan, driver, _, _ = v2

    def callback(plan, permit):
        permit.operation = "foreign"
        permit.check()

    driver.callback = callback
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert driver.calls == 0 and gate.status()["phase"] == "recovery"


@pytest.mark.parametrize(
    "damage", ["torn", "hash", "scope_rehashed", "version_rehashed", "both"]
)
def test_journal_damage_closes_admission_and_dispatch(v2, damage):
    gate, plan, driver, settings, _ = v2
    path = settings.root / JOURNAL_V2
    data = path.read_bytes()
    if damage == "both":
        (settings.root / JOURNAL).write_bytes(data)
        (settings.root / JOURNAL).chmod(0o600)
    elif damage == "torn":
        path.write_bytes(data + b"{")
    elif damage == "hash":
        path.write_bytes(data.replace(b"initialized_closed", b"changed_reason"))
    else:
        rows = [json.loads(line) for line in data.splitlines()]
        row = rows[-1]
        row[
            "runtime_scope_sha256" if damage == "scope_rehashed" else "schema_version"
        ] = "0" * 64 if damage == "scope_rehashed" else 1
        row.pop("sha256")
        row["sha256"] = hashlib.sha256(canonical(row)).hexdigest()
        path.write_bytes(b"".join(canonical(r) + b"\n" for r in rows))
    assert gate.status()["status"] == "blocked"
    with pytest.raises(Blocked):
        with admission(settings):
            pass
    with dispatch(settings) as allowed:
        assert not allowed
    with pytest.raises((Blocked, ValueError)):
        gate.run(plan, approve(plan), driver)
    assert driver.calls == 0


def test_no_v1_downgrade_even_with_gate_flag_disabled(v2):
    gate, plan, driver, settings, _ = v2
    old = settings.model_copy(
        update={
            "deployment_gate_protocol": "c26-gate-v1",
            "deployment_gate_required": False,
        }
    )
    with pytest.raises(Blocked):
        with admission(old):
            pass
    with dispatch(old) as allowed:
        assert not allowed
    legacy = plan.legacy()
    old_gate = Gate(old.model_copy(update={"deployment_gate_required": True}))
    old_approval = Approval(
        **{key: getattr(approve(plan), key) for key in Approval.model_fields}
    )
    with pytest.raises(Blocked):
        old_gate.run(legacy, old_approval, driver)
    assert driver.calls == 0
    with pytest.raises(ValidationError):
        Settings.model_validate(
            settings.model_dump() | {"deployment_gate_required": False}
        )


def test_interruption_recovery_rollback_and_separate_resume(v2):
    gate, plan, driver, _, _ = v2
    driver.fail_after = True
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert gate.status()["phase"] == "recovery"
    driver.fail_after = False
    assert (
        gate.release(plan, approve(plan, "recover"), driver, recovery=True)["phase"]
        == "verified"
    )
    reverse = make_plan(plan.operation.target, plan.operation.current)
    gate.run(reverse, approve(reverse, "rollback"), driver)
    assert gate.status()["phase"] == "verified" and driver.calls == 2
    assert gate.release(reverse, approve(reverse, "resume"), driver)["phase"] == "open"


def test_single_claim_and_concurrent_owner_operations(v2):
    gate, plan, driver, _, _ = v2

    def callback(plan, permit):
        result = []

        def concurrent():
            try:
                gate.run(plan, approve(plan), driver)
            except Blocked:
                result.append("blocked")

        thread = threading.Thread(target=concurrent)
        thread.start()
        thread.join(2)
        assert not thread.is_alive() and result == ["blocked"]
        permit.claim()
        with pytest.raises(Blocked):
            permit.claim()

    driver.callback = callback
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)  # Driver's second claim is rejected.
    assert driver.calls == 0 and gate.status()["phase"] == "recovery"


def test_v1_settings_hash_and_defaults_preserved(v2):
    _, _, _, settings, _ = v2
    legacy = settings.model_copy(update={"deployment_gate_protocol": "c26-gate-v1"})
    before = legacy.model_dump(mode="json")
    before.pop("deployment_gate_protocol")
    assert settings_digest(legacy) == hashlib.sha256(canonical(before)).hexdigest()
    assert Settings.model_fields["deployment_gate_protocol"].default == "c26-gate-v1"


@pytest.mark.parametrize("version", [True, 2.0, "2", None, 1, 3])
def test_versions_are_strict_in_all_v2_documents(v2, version):
    _, plan, driver, _, _ = v2
    for model, instance in [
        (PlanV2, plan),
        (ApprovalV2, approve(plan)),
        (ObservationV2, driver.observe(plan)),
    ]:
        with pytest.raises(ValidationError):
            model.model_validate(
                instance.model_dump(mode="json") | {"schema_version": version}
            )
    raw = plan.model_dump(mode="json")
    raw["operation"]["current"]["schema_version"] = version
    if type(version) is int and version == 1:
        assert PlanV2.model_validate(raw) == plan  # Existing scope schema stays v1.
    else:
        with pytest.raises(ValidationError):
            PlanV2.model_validate(raw)


@pytest.mark.parametrize(
    "field",
    [
        "roles",
        "jobroot",
        "settings_sha256",
        "trigger_policy_sha256",
        "private_network_id",
    ],
)
def test_incomplete_scope_is_not_a_plan(v2, field):
    gate, plan, driver, _, _ = v2
    raw = plan.model_dump(mode="json")
    del raw["operation"]["target"][field]
    forged = plan.model_copy(update={"operation": raw["operation"]})
    with pytest.raises(Blocked):
        gate.run(forged, approve(plan), driver)
    assert driver.calls == 0


def test_contradictory_role_revisions_and_wrong_jobroot_refused(v2):
    gate, plan, driver, _, _ = v2
    raw = plan.operation.current.model_dump(mode="json")
    raw["roles"][2]["revision"] = "c" * 40
    with pytest.raises(ValidationError):
        RuntimeScope.model_validate(raw)
    raw = plan.operation.current.model_dump(mode="json")
    raw["jobroot"]["inode"] += 1
    changed = RuntimeScope.model_validate(raw)
    wrong_root = make_plan(changed, changed)
    with pytest.raises(Blocked, match="jobroot"):
        gate.run(wrong_root, approve(wrong_root), driver)
    assert driver.calls == 0


@pytest.mark.parametrize(
    "mutation", ["before", "plan", "approval", "instance", "trigger", "expiry", "mode"]
)
def test_mutations_after_permit_issue_stop_the_side_effect(v2, mutation):
    gate, plan, driver, _, _ = v2

    def callback(plan, permit):
        if mutation == "mode":
            permit.mode = "live"
        elif mutation == "before":
            driver.generation += 1
            permit.before = driver.observe(plan)
        elif mutation == "plan":
            permit.plan = plan.model_copy(
                update={"protected_resources_sha256": "0" * 64}
            )
        elif mutation == "approval":
            permit.approval = permit.approval.model_copy(
                update={"approval_id": "foreign"}
            )
        elif mutation == "instance":
            driver.generation += 1
        elif mutation == "trigger":
            driver.mutate = lambda p: p["application"].update(auto_deploy_enabled=True)
        else:
            permit.approval = permit.approval.model_copy(update={"expires_at": 1.0})

    driver.callback = callback
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert driver.calls == 0 and gate.status()["phase"] == "recovery"


@pytest.mark.parametrize(
    "failure", ["unclaimed", "old_receipt", "same_instance", "target_unhealthy"]
)
def test_incomplete_postchange_evidence_never_verifies(v2, failure):
    gate, plan, driver, _, _ = v2
    deploy = driver.deploy

    def changed(plan, permit):
        if failure == "unclaimed":
            driver.scope = plan.operation.target
            driver.generation += 1
            return
        deploy(plan, permit)
        if failure == "old_receipt":
            driver.mutate = lambda p: p["binding"].update(
                deployment_uuid="deployment_0"
            )

            # Keep the response bound to its declared deployment receipt.
            def mutate(p):
                p["binding"]["deployment_uuid"] = "deployment_0"
                p["deployment"]["deployment_uuid"] = "deployment_0"

            driver.mutate = mutate
        elif failure == "same_instance":
            driver.generation = 0
        else:
            driver.mutate = lambda p: p["evidence"]["containers"][0].update(
                healthy=False
            )

    driver.deploy = changed
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert gate.status()["phase"] == "recovery"


def test_unhealthy_current_runtime_only_allows_explicit_rollback(v2):
    gate, plan, driver, _, _ = v2
    gate.run(plan, approve(plan), driver)
    reverse = make_plan(plan.operation.target, plan.operation.current)

    def unhealthy_current(p):
        if p["binding"]["phase"] == "current":
            p["evidence"]["containers"][0].update(healthy=False, ready=False)

    driver.mutate = unhealthy_current
    assert (
        gate.run(reverse, approve(reverse, "rollback"), driver)["status"]
        == "verified_offline"
    )
    assert driver.calls == 2 and gate.status()["phase"] == "verified"


@pytest.mark.parametrize("fault", ["short_write", "fsync"])
def test_incomplete_journal_io_never_issues_permit(v2, monkeypatch, fault):
    from src.job_control import deployment_gate as module

    gate, plan, driver, settings, _ = v2
    write, fsync = module.os.write, module.os.fsync
    failed = False

    def short(fd, data):
        nonlocal failed
        if not failed:
            failed = True
            return write(fd, data[: len(data) // 2])
        return write(fd, data)

    def sync(fd):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("synthetic fsync failure")
        return fsync(fd)

    monkeypatch.setattr(
        module.os,
        "write" if fault == "short_write" else "fsync",
        short if fault == "short_write" else sync,
    )
    with pytest.raises((Blocked, OSError)):
        gate.run(plan, approve(plan), driver)
    assert failed and driver.calls == 0
    assert gate.status()["status"] == "blocked"
    with pytest.raises(Blocked):
        with admission(settings):
            pass


def test_concurrent_resume_cannot_open_or_mint_a_permit(v2):
    gate, plan, driver, _, _ = v2
    result = []

    def callback(plan, permit):
        def attempt():
            try:
                gate.release(plan, approve(plan, "resume"), driver)
            except Blocked:
                result.append("blocked")

        thread = threading.Thread(target=attempt)
        thread.start()
        thread.join(2)
        assert not thread.is_alive() and result == ["blocked"]

    driver.callback = callback
    with pytest.raises(Blocked):
        gate.run(plan, approve(plan), driver)
    assert driver.calls == 0 and gate.status()["phase"] == "recovery"


def test_v2_cli_checks_scope_without_returning_permit(v2, tmp_path, capsys):
    from scripts.deployment_gate import main

    _, plan, driver, settings, _ = v2
    files = []
    for name, model in [
        ("config", settings),
        ("plan", plan),
        ("approval", approve(plan)),
    ]:
        path = tmp_path / (name + ".json")
        path.write_text(model.model_dump_json())
        path.chmod(0o600)
        files.append(str(path))
    args = [
        "check-plan",
        "--config",
        files[0],
        "--plan",
        files[1],
        "--approval",
        files[2],
        "--action",
        "deploy",
    ]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out) == dict(
        status="plan_valid_only",
        deployment_permitted=False,
        production_release="blocked",
    )
    assert driver.calls == 0
    raw = plan.model_dump(mode="json")
    raw.pop("operation")
    (tmp_path / "plan.json").write_text(json.dumps(raw))
    assert main(args) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"


def test_v2_c22_backup_restore_is_held_and_retains_original_journal(v2, tmp_path):
    from src.job_control.operations import backup, restore

    gate, plan, driver, settings, worker = v2
    config = tmp_path / "controller.json"
    config.write_text(settings.model_dump_json())
    config.chmod(0o600)
    before = (settings.root / JOURNAL_V2).read_bytes()
    worker.close()
    try:
        snapshot, restored = tmp_path / "snapshot", tmp_path / "restored"
        backup(config, snapshot)
        result = restore(snapshot, restored)
        assert result["activated"] is False
        assert (restored / JOURNAL_V2).read_bytes().startswith(before)
        assert (settings.root / JOURNAL_V2).read_bytes() == before
        target_settings = settings.model_copy(update={"root": restored})
        restored_gate = Gate(target_settings)
        assert restored_gate.status()["phase"] == "held"
        with pytest.raises(Blocked):
            with admission(target_settings):
                pass
        with pytest.raises(Blocked, match="jobroot"):
            restored_gate.release(plan, approve(plan, "resume"), driver)
    finally:
        worker.__init__(settings)  # Restore this fixture's lifetime leases.


def test_duplicate_json_keys_in_journal_are_rejected(v2):
    gate, _, _, settings, _ = v2
    path = settings.root / JOURNAL_V2
    data = path.read_bytes()
    path.write_bytes(
        data.replace(b'"schema_version":2', b'"schema_version":1,"schema_version":2', 1)
    )
    assert gate.status()["phase"] == "unknown"


def test_published_v2_schemas_match_models():
    from pathlib import Path

    from src.job_control.deployment_scope import JournalEventV2

    folder = Path(__file__).resolve().parents[1] / "docs/deployment/c26_runtime"
    for model, filename in [
        (PlanV2, "gate_plan.v2.schema.json"),
        (ApprovalV2, "gate_approval.v2.schema.json"),
        (ObservationV2, "gate_observation.v2.schema.json"),
        (JournalEventV2, "gate_journal_event.v2.schema.json"),
    ]:
        assert json.loads((folder / filename).read_text()) == model.model_json_schema()


@pytest.mark.parametrize("field", ["healthy", "ready"])
def test_rollback_never_waives_unknown_health(v2, field):
    gate, plan, driver, _, _ = v2
    gate.run(plan, approve(plan), driver)
    reverse = make_plan(plan.operation.target, plan.operation.current)
    driver.mutate = lambda p: p["evidence"]["containers"][0].update({field: None})
    with pytest.raises(Blocked, match="health_state_unknown"):
        gate.run(reverse, approve(reverse, "rollback"), driver)
    assert driver.calls == 1 and gate.status()["phase"] == "verified"
