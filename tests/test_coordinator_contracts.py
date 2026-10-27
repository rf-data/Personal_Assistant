"""Pure private-producer fixtures: no listener, keys, registry or host access."""

import time
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from test_deployment_coordinator import coordinated as coordinated
from test_deployment_coordinator import execute
from test_deployment_gate_v2 import FixtureDriver
from test_job_control import offline as offline
from test_job_control import setup as setup
from test_runtime_collector import TOKEN, Server
from test_runtime_collector import prepared as prepared

from src.job_control.coolify_observer import fingerprint
from src.job_control.coordinator_contracts import (
    BuildAuthorityContract,
    IntegrationContract,
    ProducerContract,
)
from src.job_control.runtime_collector import (
    BuildReceipt,
    Credential,
    RuntimeCollector,
    SimulatedHTTPS,
)


class PrivateProducerFixture(Server):
    """Only in-process MockTransport; enforces the proposed server-side boundary."""

    def __init__(self, target, raw, receipts, binding, operation):
        super().__init__(target, raw, receipts)
        self.binding, self.operation = binding, operation
        self.seen = set()
        self.change = self.fresh

    @staticmethod
    def fresh(request, payload):
        if "payload" in payload:
            payload["observed_at"] = float(time.time())
            payload["expires_at"] = float(time.time() + 20)

    def handle(self, request):
        if request.method != "GET":
            return httpx.Response(405)
        if request.headers.get("Authorization") != "Bearer " + TOKEN:
            return httpx.Response(401)
        if (
            request.headers.get("X-C26-Binding-SHA256") != fingerprint(self.binding)
            or request.headers.get("X-C26-Scope-SHA256")
            != self.operation.runtime_scope_sha256
        ):
            return httpx.Response(403)
        nonce = request.headers.get("X-C26-Request-ID")
        if not nonce or nonce in self.seen:
            return httpx.Response(409)
        self.seen.add(nonce)
        return super().handle(request)


def test_producer_build_and_integration_are_explicitly_offline(prepared):
    channels = prepared[5]
    producer = ProducerContract(target=channels["metadata"].target)
    build = BuildAuthorityContract(target=channels["build"].target)
    contract = IntegrationContract(producer=producer, build_authority=build)
    assert not contract.live_gate_enabled and not contract.deployment_permitted
    assert not build.independent_verification_executed and not producer.live_accepted
    for update in [
        {"live_gate_enabled": True},
        {"mode": "live"},
        {"driver": "coolify"},
        {"witness": "cloud"},
    ]:
        with pytest.raises(ValidationError):
            IntegrationContract.model_validate(contract.model_dump() | update)


@pytest.mark.parametrize(
    "change",
    [
        {"max_response_bytes": 65537},
        {"max_validity_seconds": 31},
        {"max_validity_seconds": True},
        {"authorization": "unauthenticated"},
        {"secret_policy": "raw_docker_inspect"},
    ],
)
def test_producer_contract_cannot_widen_limits_or_disclose_raw_metadata(
    prepared, change
):
    raw = ProducerContract(target=prepared[5]["metadata"].target).model_dump()
    with pytest.raises(ValidationError):
        ProducerContract.model_validate(raw | change)


def test_build_authority_requires_separate_identity_and_no_label_proof(
    prepared,
):
    targets = prepared[5]
    producer = ProducerContract(target=targets["metadata"].target)
    target = targets["build"].target.model_copy(
        update={"trust_domain": producer.target.trust_domain}
    )
    with pytest.raises(ValidationError):
        IntegrationContract(
            producer=producer, build_authority=BuildAuthorityContract(target=target)
        )
    with pytest.raises(ValidationError):
        BuildAuthorityContract(target=targets["build"].target, label_only_accepted=True)


def test_full_c26e_capture_drives_only_inert_coordinator(coordinated, prepared):
    c = coordinated
    captures = []
    targets = {key: value.target for key, value in prepared[5].items()}

    def source(plan, scope, generation):
        driver = FixtureDriver(scope)
        driver.generation = generation
        observation = driver.observe(plan)
        evidence = observation.evidence
        raw = {
            "inventory": evidence.inventory.model_dump(mode="json"),
            "boundary": evidence.boundary.model_dump(mode="json"),
            "containers": {
                v.container_id: v.model_dump(mode="json") for v in evidence.containers
            },
            "images": {v.image_id: v.model_dump(mode="json") for v in evidence.images},
            "deployment": observation.deployment.model_dump(mode="json"),
            "application": observation.application.model_dump(mode="json"),
        }
        raw["application"]["settings"] = {
            "is_auto_deploy_enabled": False,
            "is_preview_deployments_enabled": False,
        }
        receipts = {}
        for role in scope.roles:
            receipt = BuildReceipt(
                authority_id="build_authority",
                repository=scope.repository,
                revision=role.revision,
                image_id=role.image_id,
                repo_digest=role.image,
                verification="registry_digest_and_build_attestation_verified",
            )
            assert fingerprint(receipt) == role.build_receipt_sha256
            receipts[fingerprint(receipt)] = receipt.model_dump(mode="json")
        servers = {
            key: PrivateProducerFixture(
                target, raw, receipts, observation.binding, plan.operation
            )
            for key, target in targets.items()
        }
        channels = {
            key: SimulatedHTTPS(
                target, transport=httpx.MockTransport(servers[key].handle)
            )
            for key, target in targets.items()
        }
        credentials = SimpleNamespace(
            acquire=lambda target: Credential(
                target, float(time.time() + 120), SecretStr(TOKEN)
            )
        )
        result = RuntimeCollector(**channels, credentials=credentials).capture(
            observation.binding, plan.operation
        )
        captures.append(result)
        return result

    c.coordinator.evidence = source
    execute(c)
    assert c.driver.calls == 1 and 1 <= len(captures) <= 8
    assert all(
        v.mode == "simulated" and v.live_accepted is False and len(v.receipts) == 20
        for v in captures
    )
    assert all(not v.independently_verified and v.unverified for v in captures)


def test_server_fixture_rejects_replayed_nonce_and_missing_authorization(
    prepared,
):
    binding, operation, raw, receipts, _, channels, _ = prepared
    server = PrivateProducerFixture(
        channels["metadata"].target, raw, receipts, binding, operation
    )
    # Rejection occurs before projection; no endpoint/listener is opened.
    bare = httpx.Request(
        "GET", "https://metadata.example.test/v1/runtime/metadata/inventory"
    )
    assert server.handle(bare).status_code == 401
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "X-C26-Binding-SHA256": fingerprint(binding),
        "X-C26-Scope-SHA256": operation.runtime_scope_sha256,
        "X-C26-Request-ID": "1" * 64,
    }
    server.seen.add("1" * 64)
    assert (
        server.handle(httpx.Request("GET", bare.url, headers=headers)).status_code
        == 409
    )
    headers["X-C26-Scope-SHA256"] = "0" * 64
    assert (
        server.handle(httpx.Request("GET", bare.url, headers=headers)).status_code
        == 403
    )
    assert (
        server.handle(httpx.Request("POST", bare.url, headers=headers)).status_code
        == 405
    )


@pytest.mark.parametrize("name", ["Anchor", "Enrollment"])
def test_witness_contract_version_is_not_boolean(name):
    from src.job_control import coordinator_state

    model = getattr(coordinator_state, name)
    with pytest.raises(ValidationError, match="Integer schema versions required"):
        model.model_validate({"schema_version": True})
