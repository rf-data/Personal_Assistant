"""Fake-only authenticated collector contract; no sockets or real credentials."""

import copy
import hashlib
import ssl
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from test_coolify_observer import NOW
from test_coolify_observer import fixture as observer_fixture
from test_job_control import offline as offline

from src.job_control.coolify_observer import (
    ObserverBinding,
    OperationPlan,
    RuntimeScope,
    fingerprint,
)
from src.job_control.coolify_readiness import Refused
from src.job_control.deployment_scope import ObservationV2
from src.job_control.models import canonical
from src.job_control.runtime_collector import (
    BuildReceipt,
    Capture,
    Credential,
    PinnedHTTPS,
    RuntimeCollector,
    SimulatedHTTPS,
    Target,
    _Session,
)

TOKEN = "synthetic_read_token_0123456789"


class Credentials:
    def __init__(self):
        self.calls = []
        self.change = None

    def acquire(self, target_id):
        self.calls.append(target_id)
        value = Credential(target_id, NOW + 60, SecretStr(TOKEN))
        return self.change(value) if self.change else value


class Server:
    def __init__(self, target, raw, receipts):
        self.target, self.raw, self.receipts = target, raw, receipts
        self.requests = []
        self.envelopes = []
        self.inventory_calls = 0
        self.change = None
        self.fail = None
        self.http_status = 200
        self.headers = {}

    def handle(self, request):
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer " + TOKEN
        self.requests.append(request)  # Authorization must be erased on return.
        if self.fail:
            raise self.fail
        path = request.url.path
        if self.target.purpose == "coolify":
            if path == "/api/v1/applications/backend":
                payload = copy.deepcopy(self.raw["application"])
            else:
                assert path == "/api/v1/deployments/applications/backend"
                assert request.url.query == b"skip=0&take=16"
                payload = {"deployments": [copy.deepcopy(self.raw["deployment"])]}
        else:
            if self.target.purpose == "build":
                data = self.receipts[path.rsplit("/", 1)[1]]
            elif path.endswith("/inventory"):
                self.inventory_calls += 1
                data = self.raw["inventory"]
            elif "/containers/" in path:
                data = self.raw["containers"][path.rsplit("/", 1)[1]]
            elif "/images/" in path:
                data = self.raw["images"][path.rsplit("/", 1)[1]]
            else:
                assert path.endswith("/boundary/backend")
                data = self.raw["boundary"]
            payload = dict(
                schema_version=1,
                mode="simulated",
                target_id=self.target.target_id,
                subject_id=self.target.subject_id,
                adapter_id=self.target.adapter_id,
                batch_id=request.headers["X-C26-Batch-ID"],
                request_id=request.headers["X-C26-Request-ID"],
                request_sha256=request.headers["X-C26-Request-SHA256"],
                binding_sha256=request.headers["X-C26-Binding-SHA256"],
                runtime_scope_sha256=request.headers["X-C26-Scope-SHA256"],
                capture_id="capture_" + str(self.inventory_calls)
                if self.target.purpose == "metadata"
                else "build_batch",
                observed_at=NOW,
                expires_at=NOW + 5,
                payload=copy.deepcopy(data),
            )
        if self.change:
            self.change(request, payload)
        self.envelopes.append(copy.deepcopy(payload))
        return httpx.Response(self.http_status, json=payload, headers=self.headers)


@pytest.fixture
def prepared():
    binding, plan, raw = observer_fixture()
    receipts = {}
    scope = binding.scope.model_dump(mode="json")
    for role in scope["roles"]:
        proof = BuildReceipt(
            authority_id="build_authority",
            repository=scope["repository"],
            revision=role["revision"],
            image_id=role["image_id"],
            repo_digest=role["image"],
            verification="registry_digest_and_build_attestation_verified",
        )
        key = fingerprint(proof)
        receipts[key] = proof.model_dump(mode="json")
        role["build_receipt_sha256"] = key
        raw["images"][role["image_id"]]["build_receipt_sha256"] = key
    scope = RuntimeScope.model_validate(scope)
    binding = ObserverBinding(**(binding.model_dump() | {"scope": scope}))
    plan = OperationPlan(
        gate_plan_sha256=plan.gate_plan_sha256, current=scope, target=scope
    )
    targets = [
        Target(
            target_id=purpose,
            purpose=purpose,
            origin="https://" + purpose + ".example.test/",
            subject_id=subject,
            adapter_id="synthetic" if purpose == "metadata" else None,
            trust_domain=purpose,
            certificate_sha256=str(i + 1) * 64,
        )
        for i, (purpose, subject) in enumerate(
            [("metadata", "host"), ("coolify", "backend"), ("build", "build_authority")]
        )
    ]
    servers = {t.purpose: Server(t, raw, receipts) for t in targets}
    channels = {
        t.purpose: SimulatedHTTPS(
            t, transport=httpx.MockTransport(servers[t.purpose].handle)
        )
        for t in targets
    }
    credentials = Credentials()
    return binding, plan, raw, receipts, servers, channels, credentials


def collector(prepared, **kwargs):
    *_, channels, credentials = prepared
    return RuntimeCollector(
        **channels, credentials=credentials, clock=lambda: NOW, **kwargs
    )


def run(prepared):
    return collector(prepared).capture(*prepared[:2])


def test_positive_fake_capture_is_canonical_bounded_and_never_live(prepared):
    result = run(prepared)
    assert result.status == "simulated_consistent"
    assert result.mode == "simulated" and result.live_accepted is False
    assert (
        result.deployment_permitted is False and result.production_release == "blocked"
    )
    assert not result.independently_verified and not result.directly_observed
    assert result.simulated and result.operator_reported and result.unverified
    assert len(result.receipts) == 20 and len(result.build_receipts) == 2
    assert result.observer.status == "verified_offline"
    assert (
        Capture.model_validate_json(canonical(result.model_dump(mode="json"))) == result
    )
    assert TOKEN not in result.model_dump_json()
    for server in prepared[4].values():
        assert all("Authorization" not in r.headers for r in server.requests)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "wrong",
        Credential("other", NOW + 60, SecretStr(TOKEN)),
        Credential("metadata", NOW - 1, SecretStr(TOKEN)),
        Credential("metadata", NOW + 60, SecretStr("bad\r\nHeader")),
    ],
)
def test_missing_invalid_expired_or_wrong_audience_credentials_fail_before_request(
    prepared, value
):
    prepared[-1].change = lambda old: value
    with pytest.raises(Refused, match="collector_capture_unverified"):
        run(prepared)
    assert not any(server.requests for server in prepared[4].values())


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("bad TLS " + TOKEN),
        httpx.ReadTimeout(TOKEN),
        ssl.SSLCertVerificationError(TOKEN),
        RuntimeError(TOKEN),
    ],
)
def test_tls_timeout_transport_failures_are_sanitized_without_retry(
    prepared, error, caplog
):
    prepared[4]["coolify"].fail = error
    with pytest.raises(Refused) as caught:
        run(prepared)
    assert TOKEN not in str(caught.value) and TOKEN not in caplog.text
    assert len(prepared[4]["coolify"].requests) == 1
    assert "Authorization" not in prepared[4]["coolify"].requests[0].headers


@pytest.mark.parametrize("status", [301, 302, 307, 308, 401, 403, 500])
def test_redirect_and_http_failures_stop_without_followup(prepared, status):
    prepared[4]["coolify"].http_status = status
    prepared[4]["coolify"].headers = {"Location": "https://foreign.example.test/steal"}
    with pytest.raises(Refused):
        run(prepared)
    assert len(prepared[4]["coolify"].requests) == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda q, p: p.update(target_id="wrong"),
        lambda q, p: p.update(subject_id="wrong"),
        lambda q, p: p.update(batch_id="0" * 64),
        lambda q, p: p.update(request_id="0" * 64),
        lambda q, p: p.update(request_sha256="0" * 64),
        lambda q, p: p.update(binding_sha256="0" * 64),
        lambda q, p: p.update(runtime_scope_sha256="0" * 64),
        lambda q, p: p.update(observed_at=NOW - 1),
        lambda q, p: p.update(observed_at=NOW + 1),
        lambda q, p: p.update(expires_at=NOW),
        lambda q, p: p.update(expires_at=NOW + 31),
        lambda q, p: p.update(mode="authenticated_read_only"),
        lambda q, p: p.update(schema_version=2),
        lambda q, p: p.update(schema_version=True),
    ],
)
def test_wrong_replayed_stale_or_synthetic_authentication_envelopes(prepared, change):
    prepared[4]["metadata"].change = change
    with pytest.raises(Refused):
        run(prepared)


def test_capture_id_cannot_change_mid_scan(prepared):
    prepared[4]["metadata"].change = lambda q, p: (
        p.update(capture_id="changed") if "/containers/" in q.url.path else None
    )
    with pytest.raises(Refused):
        run(prepared)


@pytest.mark.parametrize(
    "mutation",
    ["instance", "namespace", "role", "settings", "mount", "trigger", "health"],
)
def test_missing_conflicting_or_changed_runtime_data_fail_closed(prepared, mutation):
    def change(q, p):
        if "/containers/" not in q.url.path:
            return
        data = p["payload"]
        if mutation == "instance":
            data["container_id"] = "f" * 64
        elif mutation == "namespace":
            data["network_namespace"] = "foreign"
        elif mutation == "role":
            data["role"] = "api"
        elif mutation == "settings":
            data["settings_sha256"] = "0" * 64
        elif mutation == "mount":
            data["mounts"] = []
        elif mutation == "trigger":
            prepared[2]["boundary"]["trigger_inventory_complete"] = False
        else:
            data["healthy"] = None

    prepared[4]["metadata"].change = change
    with pytest.raises(Refused):
        run(prepared)


@pytest.mark.parametrize(
    "change",
    ["missing", "wrong_hash", "wrong_revision", "host_label", "same_authority"],
)
def test_build_provenance_requires_independent_pinned_receipt(prepared, change):
    if change == "same_authority":
        prepared[5]["build"].target = prepared[5]["build"].target.model_copy(
            update={"trust_domain": "metadata"}
        )
    elif change == "host_label":
        for image in prepared[2]["images"].values():
            image["provenance"] = "label_only"
    else:

        def mutate(q, p):
            if change == "missing":
                p["payload"] = {}
            elif change == "wrong_revision":
                p["payload"]["revision"] = "f" * 40
            else:
                p["payload"]["authority_id"] = "foreign"

        prepared[4]["build"].change = mutate
    with pytest.raises(Refused):
        run(prepared)


def test_first_response_replayed_into_new_batch_is_rejected(prepared):
    first = run(prepared)
    saved = prepared[4]["metadata"].envelopes[0]
    prepared[4]["metadata"].change = lambda q, p: (p.clear(), p.update(saved))
    with pytest.raises(Refused):
        run(prepared)
    assert first.mode == "simulated"


def test_collector_instance_cannot_reuse_completed_capture(prepared):
    service = collector(prepared)
    service.capture(*prepared[:2])
    count = len(prepared[-1].calls)
    with pytest.raises(Refused, match="single_capture"):
        service.capture(*prepared[:2])
    assert len(prepared[-1].calls) == count


def test_second_scan_identity_change_is_rejected(prepared):
    server = prepared[4]["metadata"]

    def change(q, p):
        if server.inventory_calls > 1 and "/containers/" in q.url.path:
            p["payload"]["network_namespace"] = "changed"

    server.change = change
    with pytest.raises(Refused):
        run(prepared)


def test_oversize_response_and_compression_are_rejected(prepared):
    prepared[4]["coolify"].change = lambda q, p: p.update(raw_env="x" * 131073)
    with pytest.raises(Refused):
        run(prepared)
    assert len(prepared[4]["coolify"].requests) == 1


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Encoding": "gzip"},
        {"Content-Length": "999999999"},
        {"Content-Type": "text/html"},
    ],
)
def test_unsafe_response_headers_fail_closed(prepared, headers):
    prepared[4]["coolify"].headers = headers
    with pytest.raises(Refused):
        run(prepared)


def test_secret_fields_are_projected_out_and_echoed_token_is_refused(prepared, caplog):
    prepared[2]["application"]["envs"] = [{"secret": "synthetic_other_secret"}]
    prepared[2]["inventory"]["raw_secret"] = "synthetic_other_secret"
    result = run(prepared)
    assert "synthetic_other_secret" not in result.model_dump_json()
    assert "raw_secret" not in result.model_dump_json()
    prepared[4]["coolify"].change = lambda q, p: p.update(envs=TOKEN)
    with pytest.raises(Refused) as caught:
        run(prepared)
    assert TOKEN not in str(caught.value) and TOKEN not in caplog.text


def test_timeout_and_total_request_budget_stop_before_more_requests(prepared):
    ticks = iter([0.0, 9.0])
    with pytest.raises(Refused):
        collector(prepared, monotonic=lambda: next(ticks)).capture(*prepared[:2])
    assert not any(s.requests for s in prepared[4].values())
    binding, plan, *_ = prepared
    session = _Session(
        prepared[5], prepared[-1], binding, plan, lambda: NOW, lambda: 0.0
    )
    try:
        session.calls = 24
        with pytest.raises(Refused):
            session.get("application")
        assert not any(s.requests for s in prepared[4].values())
    finally:
        session.close()


@pytest.mark.parametrize(
    "query,identity",
    [
        ("DELETE", None),
        ("inventory", "../"),
        ("container", "../../secret"),
        ("boundary", "other"),
        ("image", "https://foreign/"),
        ("build", "0" * 64),
        ("application", "other"),
    ],
)
def test_unapproved_endpoints_never_reach_transport(prepared, query, identity):
    binding, plan, *_ = prepared
    session = _Session(
        prepared[5], prepared[-1], binding, plan, lambda: NOW, lambda: 0.0
    )
    try:
        with pytest.raises(Refused):
            session.get(query, identity)
        assert not any(s.requests for s in prepared[4].values())
    finally:
        session.close()


@pytest.mark.parametrize(
    "origin",
    [
        "http://metadata.example.test/",
        "https://u:p@metadata.example.test/",
        "https://metadata.example.test/arbitrary",
        "https://metadata.example.test/?query=1",
        "https://metadata.example.test/#fragment",
    ],
)
def test_target_policy_rejects_noncanonical_or_untrusted_origins(prepared, origin):
    with pytest.raises(ValidationError):
        Target.model_validate(
            prepared[5]["metadata"].target.model_dump() | {"origin": origin}
        )


def test_real_https_pins_nonca_leaf_before_authentication_and_has_no_fake_injection():
    pem = (Path(__file__).parent / "fixtures/c26e/public-test-leaf.pem").read_text()
    target = Target(
        target_id="metadata",
        purpose="metadata",
        origin="https://collector.example.test/",
        subject_id="host",
        adapter_id="synthetic",
        trust_domain="host",
        certificate_sha256=hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest(),
    )
    channel = PinnedHTTPS(target, certificate_pem=pem)
    try:
        context = channel._context
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        assert context.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN
        assert context.verify_flags & ssl.VERIFY_X509_STRICT
        assert context.cert_store_stats() == {"x509": 1, "crl": 0, "x509_ca": 0}
    finally:
        channel._transport.close()
    with pytest.raises(Refused):
        PinnedHTTPS(
            target.model_copy(update={"certificate_sha256": "0" * 64}),
            certificate_pem=pem,
        )
    with pytest.raises(Refused):
        PinnedHTTPS(target, certificate_pem="untrusted")
    with pytest.raises(TypeError):
        PinnedHTTPS(
            target,
            certificate_pem=pem,
            transport=httpx.MockTransport(lambda r: httpx.Response(200)),
        )


def test_gate_v2_receives_only_explicitly_marked_offline_fixture(prepared, monkeypatch):
    from test_deployment_gate_v2 import make_plan

    result = run(prepared)
    fixture = result.gate_fixture()
    gate_plan = make_plan(prepared[0].scope, prepared[0].scope)
    monkeypatch.setattr("src.job_control.deployment_scope.time.time", lambda: NOW)
    assert fixture.check(gate_plan, target=False) == fixture
    assert fixture.mode == "offline_fixture"
    raw = fixture.model_dump(mode="json")
    raw["evidence"] = result.evidence.model_dump(mode="json")
    with pytest.raises(ValidationError):
        ObservationV2.model_validate(raw)
    forged = result.model_copy(update={"mode": "authenticated_read_only"})
    with pytest.raises(Refused):
        forged.gate_fixture()


def test_capture_mode_and_trust_tiers_cannot_be_promoted_from_json(prepared):
    result = run(prepared)
    raw = result.model_dump(mode="json")
    for updates in [
        {"mode": "authenticated_read_only"},
        {"status": "authenticated_capture"},
        {"independently_verified": ["claimed"]},
        {"directly_observed": ["claimed"]},
    ]:
        with pytest.raises(ValidationError):
            Capture.model_validate(raw | updates)
    assert all(
        r.observed_at is not None and r.expires_at is not None
        for r in result.receipts
        if r.query not in {"application", "deployment"}
    )


def test_fake_transports_cannot_be_smuggled_through_real_channel_type(prepared):
    fake = object.__new__(PinnedHTTPS)
    fake.target = prepared[5]["metadata"].target
    fake._transport = prepared[5]["metadata"]._transport
    with pytest.raises(Refused):
        RuntimeCollector(
            metadata=fake,
            coolify=prepared[5]["coolify"],
            build=prepared[5]["build"],
            credentials=prepared[-1],
        )


def test_response_cookies_never_become_credentials(prepared):
    prepared[4]["coolify"].headers = {"Set-Cookie": "session=synthetic_cookie; Path=/"}
    result = run(prepared)
    assert result.status == "simulated_consistent"
    assert all("Cookie" not in r.headers for r in prepared[4]["coolify"].requests)
    assert "synthetic_cookie" not in result.model_dump_json()


def test_credential_provider_exception_cannot_leak(prepared, caplog):
    def bad_provider(target):
        raise RuntimeError(TOKEN)

    prepared[-1].acquire = bad_provider
    with pytest.raises(Refused) as caught:
        run(prepared)
    assert TOKEN not in str(caught.value) and TOKEN not in caplog.text
    assert not any(s.requests for s in prepared[4].values())


def test_cleanup_errors_are_sanitized_and_never_return_capture(prepared, caplog):
    class BrokenClose(httpx.MockTransport):
        def close(self):
            raise RuntimeError(TOKEN)

    server = prepared[4]["metadata"]
    prepared[5]["metadata"] = SimulatedHTTPS(
        server.target, transport=BrokenClose(server.handle)
    )
    with pytest.raises(Refused, match="collector_close_unverified") as caught:
        run(prepared)
    assert TOKEN not in str(caught.value) and TOKEN not in caplog.text


def test_expired_build_proof_at_capture_end_is_rejected(prepared):
    advanced = False

    def build(q, p):
        p["expires_at"] = NOW + 0.2

    prepared[4]["build"].change = build

    def metadata(q, p):
        nonlocal advanced
        if (
            q.url.path.endswith("/boundary/backend")
            and prepared[4]["metadata"].inventory_calls == 2
        ):
            advanced = True

    prepared[4]["metadata"].change = metadata
    with pytest.raises(Refused):
        RuntimeCollector(
            **prepared[5],
            credentials=prepared[-1],
            clock=lambda: NOW + 1 if advanced else NOW,
        ).capture(*prepared[:2])
    assert sum(len(s.requests) for s in prepared[4].values()) == 20


def test_target_configuration_drift_during_capture_is_refused(prepared):
    server = prepared[4]["coolify"]

    def mutate(q, p):
        target = prepared[5]["metadata"].target
        prepared[5]["metadata"].target = target.model_copy(
            update={"origin": "https://foreign.example.test/"}
        )

    server.change = mutate
    with pytest.raises(Refused):
        run(prepared)
    assert not prepared[4]["metadata"].requests


def test_duplicate_keys_and_nonobject_responses_are_rejected(prepared):
    for raw in [b'{"uuid":"wrong","uuid":"backend"}', b"[]", b"NaN"]:
        server = prepared[4]["coolify"]
        prepared[5]["coolify"] = SimulatedHTTPS(
            server.target,
            transport=httpx.MockTransport(
                lambda q, value=raw: httpx.Response(
                    200, content=value, headers={"content-type": "application/json"}
                )
            ),
        )
        with pytest.raises(Refused):
            run(prepared)


def test_byte_budget_is_enforced_even_across_small_responses(prepared):
    binding, plan, *_ = prepared
    session = _Session(
        prepared[5], prepared[-1], binding, plan, lambda: NOW, lambda: 0.0
    )
    try:
        session.bytes = 2 * 1024 * 1024
        with pytest.raises(Refused):
            session.get("application")
    finally:
        session.close()


def test_normalized_observer_hash_is_bound_to_captured_evidence(prepared):
    result = run(prepared)
    assert result.digest == fingerprint(result)
    raw = result.model_dump(mode="json")
    raw["evidence"]["containers"][0]["command_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        Capture.model_validate(raw)


def test_truncated_or_inconsistent_content_length_is_refused(prepared):
    prepared[4]["coolify"].headers = {"Content-Length": "1"}
    with pytest.raises(Refused):
        run(prepared)


def test_published_collector_schemas_match_models():
    from src.job_control.runtime_collector import Envelope

    folder = Path(__file__).resolve().parents[1] / "docs/deployment/c26_runtime"
    for model, name in [
        (Capture, "collector_capture.v1.schema.json"),
        (Envelope, "collector_envelope.v1.schema.json"),
        (BuildReceipt, "collector_build_receipt.v1.schema.json"),
        (Target, "collector_target.v1.schema.json"),
    ]:
        import json

        assert json.loads((folder / name).read_text()) == model.model_json_schema()


def test_metadata_adapter_identity_must_be_prebound(prepared):
    binding, plan = prepared[:2]
    changed = binding.model_copy(update={"adapter_id": "foreign"})
    with pytest.raises(Refused):
        collector(prepared).capture(changed, plan)
    assert not any(s.requests for s in prepared[4].values())


def test_remote_adapter_identity_must_match_pinned_policy(prepared):
    prepared[4]["metadata"].change = lambda q, p: p.update(adapter_id="foreign")
    with pytest.raises(Refused):
        run(prepared)


def test_streaming_deadline_checks_each_network_chunk_without_buffering(prepared):
    elapsed = 0.0
    chunks = 0

    class Drip(httpx.SyncByteStream):
        def __iter__(self):
            nonlocal elapsed, chunks
            for _ in range(30):
                elapsed += 1.0
                chunks += 1
                yield b" "

    target = prepared[5]["coolify"].target
    prepared[5]["coolify"] = SimulatedHTTPS(
        target,
        transport=httpx.MockTransport(
            lambda q: httpx.Response(
                200, stream=Drip(), headers={"Content-Type": "application/json"}
            )
        ),
    )
    with pytest.raises(Refused):
        collector(prepared, monotonic=lambda: elapsed).capture(*prepared[:2])
    assert chunks == 8
