"""Opt-in authenticated read-only collector. No launcher, listener or credentials.

The only network implementation trusts one reviewed non-CA leaf certificate,
with ordinary chain/expiry/hostname checks. Injected transports are always
simulation. Capture never issues an Approval/Permit or a live Gate observation.
"""

import hashlib
import json
import re
import secrets
import ssl
import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Literal, Protocol

import httpx
from pydantic import Field, SecretStr, model_validator

from src.job_control.coolify_observer import (
    HostCollector,
    HostEvidence,
    ObserverBinding,
    ObserverReport,
    OperationPlan,
    Provenance,
    fingerprint,
    observe_runtime,
)
from src.job_control.coolify_readiness import (
    ApplicationRead,
    CoolifyReadClient,
    DeploymentRead,
    GitSha,
    ImageId,
    ImageRef,
    Model,
    ReadScope,
    Refused,
    _unique,
)
from src.job_control.deployment_scope import ObservationV2, VersionedV2
from src.job_control.models import Identifier, Sha, canonical

GROUPS = (
    "roles_processes",
    "images_instances",
    "health_readiness",
    "network_namespaces",
    "mounts_jobroot",
    "runtime_settings",
    "trigger_claims",
)
MAX_REQUESTS = 24
MAX_BYTES = 2 * 1024 * 1024
MAX_SECONDS = 8


class Target(Model):
    """Trusted private configuration; never constructed from lecture/API input."""

    target_id: Identifier
    purpose: Literal["metadata", "coolify", "build"]
    origin: str = Field(max_length=256)
    subject_id: Identifier
    adapter_id: Identifier | None = None
    trust_domain: Identifier
    certificate_sha256: Sha

    @model_validator(mode="after")
    def https_origin(self):
        url = httpx.URL(self.origin)
        if (self.purpose == "metadata") != (self.adapter_id is not None):
            raise ValueError("Metadata requires a reviewed adapter identity")
        if (
            url.scheme != "https"
            or not url.host
            or url.userinfo
            or url.query
            or url.fragment
            or url.path != "/"
            or str(url) != self.origin
        ):
            raise ValueError("Canonical pre-reviewed HTTPS origin required")
        return self


@dataclass(frozen=True, repr=False)
class Credential:
    target_id: str
    expires_at: float
    token: SecretStr = field(repr=False)


class CredentialProvider(Protocol):
    def acquire(self, target_id: str) -> Credential:
        """Return an audience-bound short-lived read-only runtime credential."""
        ...


class PinnedHTTPS:
    """Real transport, no injection point and no request at construction.

    A leaf-only trust store pins the certificate BEFORE Authorization is sent.
    A post-response fingerprint check alone would disclose credentials on a
    valid-PKI but unapproved certificate. No system CA fallback is loaded here.
    """

    def __init__(self, target: Target, *, certificate_pem: str):
        try:
            if (
                certificate_pem.count("-----BEGIN CERTIFICATE-----") != 1
                or len(certificate_pem) > 16384
            ):
                raise ValueError()
            der = ssl.PEM_cert_to_DER_cert(certificate_pem)
            if hashlib.sha256(der).hexdigest() != target.certificate_sha256:
                raise ValueError()
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True
            context.verify_flags |= (
                ssl.VERIFY_X509_PARTIAL_CHAIN | ssl.VERIFY_X509_STRICT
            )
            context.load_verify_locations(cadata=certificate_pem)
            if context.cert_store_stats() != {"x509": 1, "crl": 0, "x509_ca": 0}:
                raise ValueError()
            self.target = Target.model_validate_json(target.model_dump_json())
            self._context = context
            self._transport = httpx.HTTPTransport(
                verify=context, retries=0, trust_env=False
            )
        except Exception:
            raise Refused("collector_tls_policy_invalid") from None


class SimulatedHTTPS:
    """Injected fake transports can never create authenticated_capture status."""

    def __init__(self, target: Target, *, transport: httpx.BaseTransport):
        if not isinstance(transport, httpx.BaseTransport):
            raise Refused("collector_fake_transport_required")
        self.target = Target.model_validate_json(target.model_dump_json())
        self._transport = transport


def mode(channel):
    if type(channel) is PinnedHTTPS and type(channel._transport) is httpx.HTTPTransport:
        return "authenticated_read_only"
    if type(channel) is SimulatedHTTPS:
        return "simulated"
    raise Refused("collector_transport_type_refused")


class RequestReceipt(VersionedV2, Model):
    target_id: Identifier
    query: Literal[
        "inventory",
        "container",
        "image",
        "boundary",
        "application",
        "deployment",
        "build",
    ]
    request_id: Sha
    started_at: float = Field(strict=True, allow_inf_nan=False)
    finished_at: float = Field(strict=True, allow_inf_nan=False)
    certificate_sha256: Sha
    mode: Literal["simulated", "authenticated_read_only"]
    capture_id: Identifier | None
    observed_at: float | None = Field(strict=True, allow_inf_nan=False)
    expires_at: float | None = Field(strict=True, allow_inf_nan=False)


class Envelope(VersionedV2, Model):
    schema_version: Literal[1] = 1
    mode: Literal["simulated", "authenticated_read_only"]
    target_id: Identifier
    subject_id: Identifier
    adapter_id: Identifier | None
    batch_id: Sha
    request_id: Sha
    request_sha256: Sha
    binding_sha256: Sha
    runtime_scope_sha256: Sha
    capture_id: Identifier
    observed_at: float = Field(strict=True, allow_inf_nan=False)
    expires_at: float = Field(strict=True, allow_inf_nan=False)
    payload: dict


class BuildReceipt(VersionedV2, Model):
    """Canonical receipt whose hash was independently approved in RoleScope.

    Its assertion needs a separate trusted registry/build verifier. A host label
    or its self-declared 'verified_build_receipt' flag cannot satisfy this check.
    """

    schema_version: Literal[1] = 1
    authority_id: Identifier
    repository: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    revision: GitSha
    image_id: ImageId
    repo_digest: ImageRef
    verification: Literal["registry_digest_and_build_attestation_verified"]


class CaptureProvenance(VersionedV2, Model):
    schema_version: Literal[2] = 2
    collector_version: Literal["c26-authenticated-collector/1"] = (
        "c26-authenticated-collector/1"
    )
    mode: Literal["simulated", "authenticated_read_only"]
    host_id: Identifier
    adapter_id: Identifier
    observed_at: float = Field(strict=True, allow_inf_nan=False)
    batch_id: Sha
    binding_sha256: Sha
    runtime_scope_sha256: Sha
    transport_policy_sha256: Sha


class CapturedHostEvidence(HostEvidence):
    provenance: CaptureProvenance


class Capture(Model):
    schema_version: Literal[1] = 1
    mode: Literal["simulated", "authenticated_read_only"]
    status: Literal["simulated_consistent", "authenticated_capture"]
    binding: ObserverBinding
    evidence: CapturedHostEvidence
    application: ApplicationRead
    deployment: DeploymentRead
    observer: ObserverReport
    receipts: tuple[RequestReceipt, ...] = Field(min_length=1, max_length=MAX_REQUESTS)
    build_receipts: tuple[BuildReceipt, ...] = Field(min_length=1, max_length=3)
    directly_observed: tuple[str, ...]
    independently_verified: tuple[str, ...]
    operator_reported: tuple[str, ...] = ("approved_scope", "target_and_trust_policy")
    simulated: tuple[str, ...]
    unverified: tuple[str, ...] = (
        "live_collector_implementation",
        "registry_verifier_implementation",
        "operator_acceptance",
        "trigger_inventory_completeness",
        "coolify_server_side_freshness",
    )
    live_accepted: Literal[False] = False
    deployment_permitted: Literal[False] = False
    production_release: Literal["blocked"] = "blocked"

    @model_validator(mode="after")
    def consistent_mode(self):
        authenticated = all(r.mode == "authenticated_read_only" for r in self.receipts)
        expected = "authenticated_read_only" if authenticated else "simulated"
        if (
            self.mode != expected
            or self.evidence.provenance.mode != expected
            or self.status
            != ("authenticated_capture" if authenticated else "simulated_consistent")
        ):
            raise ValueError("Capture mode must reflect every transport receipt")
        if (
            self.evidence.provenance.binding_sha256 != fingerprint(self.binding)
            or self.observer.runtime_scope_sha256
            != self.evidence.provenance.runtime_scope_sha256
            or len({r.request_id for r in self.receipts}) != len(self.receipts)
        ):
            raise ValueError("Capture binding or request IDs inconsistent")
        if (self.directly_observed, self.independently_verified, self.simulated) != (
            GROUPS if authenticated else (),
            ("receipt_identity_and_content_hash",) if authenticated else (),
            () if authenticated else GROUPS + ("pinned_build_receipts",),
        ):
            raise ValueError("Trust classification mismatch")
        normalized = self.evidence.model_dump(mode="json")
        normalized["provenance"] = Provenance(
            host_id=self.binding.host_id,
            adapter_id=self.binding.adapter_id,
            observed_at=self.evidence.provenance.observed_at,
        ).model_dump(mode="json")
        if (
            self.observer.status != "verified_offline"
            or self.observer.binding_sha256 != fingerprint(self.binding)
            or self.observer.evidence_sha256
            != fingerprint(HostEvidence.model_validate(normalized))
        ):
            raise ValueError("Normalized observer evidence mismatch")
        return self

    @property
    def digest(self):
        return fingerprint(self)

    def gate_fixture(self):
        """Explicit offline test bridge only, never a live Gate adapter."""
        if self.mode != "simulated":
            raise Refused("collector_live_gate_bridge_forbidden")
        data = self.evidence.model_dump(mode="json")
        data["provenance"] = Provenance(
            host_id=self.binding.host_id,
            adapter_id=self.binding.adapter_id,
            observed_at=self.evidence.provenance.observed_at,
        ).model_dump(mode="json")
        return ObservationV2(
            binding=self.binding,
            evidence=HostEvidence.model_validate(data),
            application=self.application,
            deployment=self.deployment,
        )


class _Session:
    def __init__(self, channels, credentials, binding, plan, clock, monotonic):
        self.channels = dict(channels)
        self.policy = {key: value.target for key, value in channels.items()}
        self.valid_until = float("inf")
        self.credentials = credentials
        self.binding, self.plan = binding, plan
        self.clock, self.monotonic = clock, monotonic
        self.started = monotonic()
        self.batch_id = secrets.token_hex(32)
        self.calls, self.bytes = 0, 0
        self.receipts = []
        self.capture_ids = {}
        self.clients = {
            key: httpx.Client(
                transport=c._transport,
                timeout=httpx.Timeout(3),
                follow_redirects=False,
                trust_env=False,
            )
            for key, c in channels.items()
        }

    def close(self):
        failed = False
        for client in self.clients.values():
            try:
                client.close()
            except Exception:
                failed = True
        if failed:
            raise Refused("collector_close_unverified")

    def bounded(self, *, next_request=True):
        if (
            self.calls + int(next_request) > MAX_REQUESTS
            or self.bytes > MAX_BYTES
            or not 0 <= self.monotonic() - self.started < MAX_SECONDS
        ):
            raise Refused("collector_total_budget_exceeded")

    def _path(self, query, identity):
        if query in {"inventory", "container", "image", "boundary"}:
            if query == "inventory" and identity is None:
                return "metadata", "/v1/runtime/metadata/inventory"
            if query == "container" and re.fullmatch(r"[a-f0-9]{64}", identity or ""):
                return "metadata", "/v1/runtime/metadata/containers/" + identity
            if query == "image" and re.fullmatch(
                r"sha256:[a-f0-9]{64}", identity or ""
            ):
                return "metadata", "/v1/runtime/metadata/images/" + identity
            if query == "boundary" and identity == self.binding.scope.application_uuid:
                return "metadata", "/v1/runtime/metadata/boundary/" + identity
        if query == "build" and identity in {
            r.build_receipt_sha256 for r in self.binding.scope.roles
        }:
            return "build", "/v1/runtime/build-receipts/" + identity
        if query == "application" and identity is None:
            return (
                "coolify",
                "/api/v1/applications/" + self.binding.scope.application_uuid,
            )
        if query == "deployment" and identity is None:
            return (
                "coolify",
                "/api/v1/deployments/applications/"
                + self.binding.scope.application_uuid
                + "?skip=0&take=16",
            )
        raise Refused("collector_endpoint_refused")

    def get(self, query, identity=None):
        try:
            purpose, path = self._path(query, identity)
            self.bounded()
            channel = self.channels[purpose]
            target = self.policy[purpose]
            if channel.target != target:
                raise ValueError()
            credential = self.credentials.acquire(target.target_id)
            now = self.clock()
            if (
                type(credential) is not Credential
                or credential.target_id != target.target_id
                or type(credential.token) is not SecretStr
                or not now < credential.expires_at <= now + 3600
            ):
                raise ValueError()
            token = credential.token.get_secret_value()
            if re.fullmatch(r"[A-Za-z0-9._~+/-]{16,4096}={0,2}", token) is None:
                raise ValueError()
            request_id = secrets.token_hex(32)
            bound = dict(
                batch_id=self.batch_id,
                request_id=request_id,
                query=query,
                identity=identity,
                binding_sha256=fingerprint(self.binding),
                runtime_scope_sha256=self.plan.runtime_scope_sha256,
            )
            request_hash = hashlib.sha256(canonical(bound)).hexdigest()
            self.clients[purpose].cookies.clear()
            request = self.clients[purpose].build_request(
                "GET",
                target.origin.rstrip("/") + path,
                headers={
                    "Authorization": "Bearer " + token,
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "no-store, no-cache",
                    "Pragma": "no-cache",
                    "X-C26-Batch-ID": self.batch_id,
                    "X-C26-Request-ID": request_id,
                    "X-C26-Request-SHA256": request_hash,
                    "X-C26-Binding-SHA256": bound["binding_sha256"],
                    "X-C26-Scope-SHA256": bound["runtime_scope_sha256"],
                },
            )
            if purpose in self.capture_ids:
                request.headers["X-C26-Capture-ID"] = self.capture_ids[purpose]
            self.calls += 1
            maximum = 131072 if purpose == "coolify" else 65536
            try:
                response = self.clients[purpose].send(request, stream=True)
                try:
                    if mode(channel) == "authenticated_read_only":
                        stream = response.extensions.get("network_stream")
                        ssl_object = (
                            stream.get_extra_info("ssl_object") if stream else None
                        )
                        if (
                            ssl_object is None
                            or hashlib.sha256(
                                ssl_object.getpeercert(binary_form=True)
                            ).hexdigest()
                            != target.certificate_sha256
                        ):
                            raise ValueError()
                    if (
                        response.status_code != 200
                        or response.headers.get("content-encoding", "identity")
                        != "identity"
                        or response.headers.get("content-type", "").split(";")[0]
                        != "application/json"
                    ):
                        raise ValueError()
                    if (
                        response.headers.get("age", "0") != "0"
                        or "warning" in response.headers
                    ):
                        raise ValueError()
                    length = response.headers.get("content-length")
                    if length is not None and (
                        not length.isdecimal() or int(length) > maximum
                    ):
                        raise ValueError()
                    body = bytearray()
                    chunks = (
                        (response.content,)
                        if response.is_stream_consumed
                        else response.iter_raw()
                    )
                    for chunk in chunks:
                        body.extend(chunk)
                        self.bytes += len(chunk)
                        if (
                            len(body) > maximum
                            or self.bytes > MAX_BYTES
                            or self.monotonic() - self.started >= MAX_SECONDS
                        ):
                            raise ValueError()
                    if length is not None and int(length) != len(body):
                        raise ValueError()
                    if token.encode() in body:
                        raise ValueError()
                    raw = json.loads(body, object_pairs_hook=_unique)
                    if not isinstance(raw, dict):
                        raise ValueError()
                finally:
                    response.close()
            finally:
                request.headers.pop("Authorization", None)
                self.clients[purpose].cookies.clear()
            ended = self.clock()
            if not now <= ended < credential.expires_at:
                raise ValueError()
            if purpose != "coolify":
                envelope = Envelope.model_validate(raw)
                if (
                    envelope.mode != mode(channel)
                    or envelope.target_id != target.target_id
                    or envelope.subject_id != target.subject_id
                    or envelope.adapter_id != target.adapter_id
                    or envelope.batch_id != self.batch_id
                    or envelope.request_id != request_id
                    or envelope.request_sha256 != request_hash
                    or envelope.binding_sha256 != bound["binding_sha256"]
                    or envelope.runtime_scope_sha256 != bound["runtime_scope_sha256"]
                    or not now
                    <= envelope.observed_at
                    <= ended
                    < envelope.expires_at
                    <= envelope.observed_at + 30
                ):
                    raise ValueError()
                if (
                    purpose in self.capture_ids
                    and self.capture_ids[purpose] != envelope.capture_id
                ):
                    raise ValueError()
                self.capture_ids[purpose] = envelope.capture_id
                self.valid_until = min(self.valid_until, envelope.expires_at)
            self.receipts.append(
                RequestReceipt(
                    target_id=target.target_id,
                    query=query,
                    request_id=request_id,
                    started_at=now,
                    finished_at=ended,
                    certificate_sha256=target.certificate_sha256,
                    mode=mode(channel),
                    capture_id=envelope.capture_id if purpose != "coolify" else None,
                    observed_at=envelope.observed_at if purpose != "coolify" else None,
                    expires_at=envelope.expires_at if purpose != "coolify" else None,
                )
            )
            return envelope.payload if purpose != "coolify" else raw
        except Exception:
            raise Refused("collector_read_unverified") from None


class _Metadata:
    def __init__(self, session):
        self.session = session

    def query(self, query, identity):
        return canonical(self.session.get(query, identity))


def _stable(evidence):
    value = evidence.model_dump(mode="json")
    value.pop("provenance")
    for container in value["containers"]:
        container.pop("heartbeat_at")
    # Inventory ordering is not identity; canonicalize all keyed collections.
    value["containers"].sort(key=lambda c: c["role"])
    value["images"].sort(key=lambda i: i["image_id"])
    value["inventory"]["members"].sort(key=lambda m: m["container_id"])
    return canonical(value)


class RuntimeCollector:
    """Two bracketed scans, one bounded session; no state or credential persistence."""

    def __init__(
        self,
        *,
        metadata,
        coolify,
        build,
        credentials: CredentialProvider,
        clock=time.time,
        monotonic=time.monotonic,
    ):
        self.channels = dict(metadata=metadata, coolify=coolify, build=build)
        for purpose, channel in self.channels.items():
            mode(channel)
            if channel.target.purpose != purpose:
                raise Refused("collector_target_purpose_mismatch")
        targets = [c.target for c in self.channels.values()]
        if (
            len({t.target_id for t in targets}) != 3
            or any(
                getattr(build.target, key) == getattr(channel.target, key)
                for channel in (metadata, coolify)
                for key in (
                    "origin",
                    "subject_id",
                    "trust_domain",
                    "certificate_sha256",
                )
            )
            or any(
                httpx.URL(build.target.origin).host == httpx.URL(c.target.origin).host
                for c in (metadata, coolify)
            )
        ):
            raise Refused("collector_independent_build_authority_required")
        self.credentials, self.clock, self.monotonic = credentials, clock, monotonic
        self._used = False

    def capture(self, binding: ObserverBinding, plan: OperationPlan):
        if self._used:
            raise Refused("collector_single_capture_session_required")
        self._used = True
        session = None
        client = None
        try:
            binding = ObserverBinding.model_validate_json(binding.model_dump_json())
            plan = OperationPlan.model_validate_json(plan.model_dump_json())
            if (
                getattr(plan, binding.phase) != binding.scope
                or self.channels["metadata"].target.subject_id != binding.host_id
                or self.channels["metadata"].target.adapter_id != binding.adapter_id
                or self.channels["coolify"].target.subject_id
                != binding.scope.application_uuid
            ):
                raise ValueError()
            session = _Session(
                self.channels,
                self.credentials,
                binding,
                plan,
                self.clock,
                self.monotonic,
            )

            def read(request):
                allowed = {
                    "/api/v1/applications/"
                    + binding.scope.application_uuid: "application",
                    "/api/v1/deployments/applications/"
                    + binding.scope.application_uuid
                    + "?skip=0&take=16": "deployment",
                }
                if request.method != "GET" or request.url.copy_with(
                    path="/", query=None, fragment=None
                ) != httpx.URL(self.channels["coolify"].target.origin):
                    raise Refused("collector_endpoint_refused")
                path = request.url.raw_path.decode()
                if path not in allowed:
                    raise Refused("collector_endpoint_refused")
                return httpx.Response(200, json=session.get(allowed[path]))

            client = CoolifyReadClient(
                self.channels["coolify"].target.origin,
                ReadScope(
                    application_uuid=binding.scope.application_uuid,
                    deployment_uuid=binding.deployment_uuid,
                ),
                transport=httpx.MockTransport(read),
            )
            collector = HostCollector(
                adapter=_Metadata(session),
                host_id=binding.host_id,
                adapter_id=binding.adapter_id,
                clock=self.clock,
            )
            proofs = []
            scans = []
            for index in range(2):
                app, deployment = client.application(), client.deployment()
                session.capture_ids.pop("metadata", None)
                evidence = collector.collect(binding)
                if index == 0:
                    for expected in sorted(
                        {r.build_receipt_sha256 for r in binding.scope.roles}
                    ):
                        receipt = BuildReceipt.model_validate(
                            session.get("build", expected)
                        )
                        if (
                            fingerprint(receipt) != expected
                            or receipt.authority_id
                            != self.channels["build"].target.subject_id
                        ):
                            raise ValueError()
                        proofs.append(receipt)
                for role in binding.scope.roles:
                    matches = [
                        p
                        for p in proofs
                        if fingerprint(p) == role.build_receipt_sha256
                        and (p.repository, p.revision, p.image_id, p.repo_digest)
                        == (
                            binding.scope.repository,
                            role.revision,
                            role.image_id,
                            role.image,
                        )
                    ]
                    if len(matches) != 1:
                        raise ValueError()
                projected = SimpleNamespace(
                    scope=client.scope,
                    application=lambda value=app: value,
                    deployment=lambda value=deployment: value,
                )
                report = observe_runtime(
                    binding,
                    plan,
                    collector=SimpleNamespace(collect=lambda b, value=evidence: value),
                    client=projected,
                    now=self.clock(),
                )
                if report.status != "verified_offline" or any(
                    type(c.healthy) is not bool or type(c.ready) is not bool
                    for c in evidence.containers
                ):
                    raise ValueError()
                scans.append((app, deployment, evidence, report))
            first, second = scans
            if (
                first[:2] != second[:2]
                or _stable(first[2]) != _stable(second[2])
                or first[3].instance_sha256 != second[3].instance_sha256
            ):
                raise ValueError()
            session.bounded(next_request=False)
            if not self.clock() < session.valid_until:
                raise ValueError()
            capture_mode = (
                "authenticated_read_only"
                if all(
                    mode(c) == "authenticated_read_only" for c in self.channels.values()
                )
                else "simulated"
            )
            provenance = CaptureProvenance(
                mode=capture_mode,
                host_id=binding.host_id,
                adapter_id=binding.adapter_id,
                observed_at=second[2].provenance.observed_at,
                batch_id=session.batch_id,
                binding_sha256=fingerprint(binding),
                runtime_scope_sha256=plan.runtime_scope_sha256,
                transport_policy_sha256=hashlib.sha256(
                    canonical(
                        {
                            key: target.model_dump(mode="json")
                            for key, target in sorted(session.policy.items())
                        }
                    )
                ).hexdigest(),
            )
            evidence = CapturedHostEvidence(
                **(second[2].model_dump() | {"provenance": provenance})
            )
            return Capture(
                mode=capture_mode,
                status="authenticated_capture"
                if capture_mode == "authenticated_read_only"
                else "simulated_consistent",
                binding=binding,
                evidence=evidence,
                application=second[0],
                deployment=second[1],
                observer=second[3],
                receipts=tuple(session.receipts),
                build_receipts=tuple(proofs),
                directly_observed=GROUPS
                if capture_mode == "authenticated_read_only"
                else (),
                independently_verified=("receipt_identity_and_content_hash",)
                if capture_mode == "authenticated_read_only"
                else (),
                simulated=GROUPS + ("pinned_build_receipts",)
                if capture_mode == "simulated"
                else (),
            )
        except Exception:
            raise Refused("collector_capture_unverified") from None
        finally:
            failed = False
            for resource in (client, session):
                if resource is not None:
                    try:
                        resource.close()
                    except Exception:
                        failed = True
            if failed:
                raise Refused("collector_close_unverified") from None
