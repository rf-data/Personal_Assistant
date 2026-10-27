"""Offline H composite: configuration, trust boundary, gate and inert rollback."""

import copy
import json
from pathlib import Path

import pytest
import yaml
from test_c26g_readiness import OPTIONS
from test_c26g_readiness import candidate as candidate
from test_deployment_coordinator import coordinated as coordinated
from test_deployment_coordinator import execute
from test_deployment_gate_v2 import make_plan
from test_job_control import offline as offline
from test_job_control import setup as setup
from test_runtime_collector import collector
from test_runtime_collector import prepared as prepared

from scripts.c26h_preflight import check, main
from src.job_control.coolify_readiness import Refused
from src.job_control.deployment_gate import Blocked, admission

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def staging(candidate):
    backend, ui, controller = copy.deepcopy(candidate)
    overlay = yaml.safe_load(
        (ROOT / "deployment/c26h.staging.compose.yaml").read_bytes()
    )
    backend["name"] = overlay["name"]
    backend["services"]["api"]["command"] = overlay["services"]["api"]["command"]
    backend["services"]["api"]["healthcheck"]["test"] = overlay["services"]["api"][
        "healthcheck"
    ]["test"]
    ui_overlay = yaml.safe_load(
        (ROOT / "deployment/c26h.staging.ui.compose.yaml").read_bytes()
    )
    ui["name"] = ui_overlay["name"]
    ui["services"]["ui"].update(ui_overlay["services"]["ui"])
    values = [
        json.loads(
            (ROOT / ("deployment/c26h.staging." + name + ".json.example")).read_bytes()
        )
        for name in ("content", "review", "search")
    ]
    return [backend, ui, controller, *values]


def test_disabled_staging_contract_and_no_input_mutation(staging):
    before = copy.deepcopy(staging)
    result = check(*staging, **OPTIONS)
    assert result["production_release"] == "HOLD"
    assert result["deployment_permitted"] is False
    assert result["configuration_bindings"] == "checked_without_opening_stores"
    assert "versioned_live_gate_and_mutating_driver" in result["live_blockers"]
    assert before == staging


@pytest.mark.parametrize(
    "damage",
    [
        "v1",
        "enabled",
        "missing_binding",
        "wrong_config_path",
        "health_binding",
        "review_write",
        "real_review",
        "review_content",
        "search_root",
        "key_in_data",
        "extra_mount",
        "duplicate_mount",
        "nested_source",
        "zero_cpu",
        "unlimited_memory",
        "unlimited_pids",
        "unbounded_logs",
        "gateway_writable",
        "persistent_policy",
        "production_name",
    ],
)
def test_h_refuses_incomplete_or_unsafe_staging(staging, damage):
    backend, _, controller, content, review, search = staging
    api = backend["services"]["api"]
    if damage == "v1":
        controller["deployment_gate_protocol"] = "c26-gate-v1"
    elif damage == "enabled":
        controller["execution_enabled"] = True
    elif damage == "missing_binding":
        api["command"] = api["command"][:-2]
    elif damage == "wrong_config_path":
        api["command"][-1] = "/tmp/unreviewed.json"
    elif damage == "health_binding":
        api["healthcheck"]["test"] = ["CMD", "true"]
    elif damage == "review_write":
        review["writes_enabled"] = True
    elif damage == "real_review":
        review["real_reviews_enabled"] = True
    elif damage == "review_content":
        review["content"]["root"] = "/app/runtime-state/foreign"
    elif damage == "search_root":
        search["index_root"] = content["root"]
    elif damage == "key_in_data":
        content["cursor_key_file"] = content["root"] + "/key"
    elif damage == "extra_mount":
        api["volumes"].append(
            dict(
                type="bind",
                source="/synthetic/extra",
                target="/extra",
                bind=dict(create_host_path=False),
            )
        )
    elif damage == "duplicate_mount":
        api["volumes"].append(api["volumes"][0])
    elif damage == "nested_source":
        api["volumes"][1]["source"] = api["volumes"][0]["source"] + "/nested"
    elif damage == "zero_cpu":
        api["cpus"] = 0
    elif damage == "unlimited_memory":
        api["mem_limit"] = 0
    elif damage == "unlimited_pids":
        api["pids_limit"] = -1
    elif damage == "unbounded_logs":
        api["logging"]["options"] = {}
    elif damage == "gateway_writable":
        backend["services"]["api-gateway"]["volumes"][0]["read_only"] = False
    elif damage == "persistent_policy":
        api["environment"] = {}
    elif damage == "production_name":
        backend["name"] = "personal-assistant-production"
    with pytest.raises((ValueError, KeyError)):
        check(*staging, **OPTIONS)


def test_h_cli_refusal_is_fixed_and_secret_free(staging, tmp_path, capsys):
    staging[4]["secret"] = "synthetic_private_marker"
    args = []
    for name, value in zip(
        (
            "backend-compose-json",
            "ui-compose-json",
            "controller",
            "content",
            "review",
            "search",
        ),
        staging,
        strict=True,
    ):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(value))
        args.extend(["--" + name, str(path)])
    for name, value in OPTIONS.items():
        args.extend(["--" + name.replace("_", "-"), value])
    assert main(args) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == dict(
        status="refused", production_release="HOLD", deployment_permitted=False
    )
    assert "synthetic_private_marker" not in output.out + output.err


def test_collector_coordinator_gate_and_rollback_remain_separate_offline_contracts(
    staging, prepared, coordinated
):
    assert check(*staging, **OPTIONS)["deployment_permitted"] is False
    captured = collector(prepared).capture(*prepared[:2])
    assert captured.simulated and not captured.live_accepted
    assert captured.gate_fixture().mode == "offline_fixture"
    # The authenticated-read-only tier is deliberately not an input to D/F.
    with pytest.raises(Refused):
        captured.model_copy(update={"mode": "authenticated_read_only"}).gate_fixture()
    ctx = coordinated
    result = execute(ctx)
    assert result["phase"] == "verified"
    assert result["production_release"] == "blocked"
    assert result["deployment_permitted"] is False
    with pytest.raises(Blocked):
        with admission(ctx.settings):
            pass
    reverse = make_plan(ctx.plan.operation.target, ctx.plan.operation.current)
    rollback = execute(ctx, plan=reverse, action="rollback")
    assert rollback["deployment_permitted"] is False
    assert ctx.driver.scope == ctx.plan.operation.current
    assert ctx.driver.calls == 2
    assert ctx.witness.kind == "local_test_only"
