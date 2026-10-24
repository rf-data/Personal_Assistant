"""C26-F trust contracts only; no producer listener or registry implementation."""

from typing import Literal

from pydantic import Field, model_validator

from src.job_control.deployment_scope import VersionedV2
from src.job_control.models import Contract
from src.job_control.runtime_collector import Target


class ProducerContract(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["offline_contract"] = "offline_contract"
    target: Target
    envelope_schema: Literal["collector_envelope/1"] = "collector_envelope/1"
    query_kinds: tuple[
        Literal["inventory"],
        Literal["container"],
        Literal["image"],
        Literal["boundary"],
    ] = ("inventory", "container", "image", "boundary")
    max_response_bytes: int = Field(strict=True, gt=0, le=65536, default=65536)
    max_validity_seconds: int = Field(strict=True, gt=0, le=30, default=30)
    capture_semantics: Literal[
        "fresh_observation_per_nonce;stable_snapshot_id_per_scan"
    ] = "fresh_observation_per_nonce;stable_snapshot_id_per_scan"
    authorization: Literal["audience_bound_read_only;resource_and_query_allowlist"] = (
        "audience_bound_read_only;resource_and_query_allowlist"
    )
    secret_policy: Literal["typed_projection_only;no_env_logs_commands_tokens"] = (
        "typed_projection_only;no_env_logs_commands_tokens"
    )
    replay_policy: Literal[
        "single_use_request_nonce;reject_reuse_and_cross_binding"
    ] = "single_use_request_nonce;reject_reuse_and_cross_binding"
    failure_policy: Literal["no_partial_success;no_unknown_to_true;no_retry"] = (
        "no_partial_success;no_unknown_to_true;no_retry"
    )
    live_accepted: Literal[False] = False

    @model_validator(mode="after")
    def purpose(self):
        if self.target.purpose != "metadata":
            raise ValueError("Metadata producer identity required")
        return self


class BuildAuthorityContract(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["offline_contract"] = "offline_contract"
    target: Target
    source_independence: Literal[
        "separate_administration_and_signing_trust_from_host"
    ] = "separate_administration_and_signing_trust_from_host"
    receipt_schema: Literal["collector_build_receipt/1"] = "collector_build_receipt/1"
    identity_checks: Literal[
        "issuer_repository_revision_platform_image_digest_attestation"
    ] = "issuer_repository_revision_platform_image_digest_attestation"
    receipt_hash: Literal["preapproved_canonical_sha256;never_adopt_host_hash"] = (
        "preapproved_canonical_sha256;never_adopt_host_hash"
    )
    label_only_accepted: Literal[False] = False
    independent_verification_executed: Literal[False] = False
    live_accepted: Literal[False] = False

    @model_validator(mode="after")
    def purpose(self):
        if self.target.purpose != "build":
            raise ValueError("Separate build authority required")
        return self


class IntegrationContract(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["c26-coordinator-integration/1"] = "c26-coordinator-integration/1"
    mode: Literal["offline_fixture"] = "offline_fixture"
    producer: ProducerContract
    build_authority: BuildAuthorityContract
    gate_protocol: Literal["c26-gate-v2"] = "c26-gate-v2"
    authorization: Literal["external_fixture_verifier;operator_grant/1"] = (
        "external_fixture_verifier;operator_grant/1"
    )
    witness: Literal["local_test_only;cas_anchor/1"] = "local_test_only;cas_anchor/1"
    driver: Literal["inert"] = "inert"
    live_gate_enabled: Literal[False] = False
    deployment_permitted: Literal[False] = False

    @model_validator(mode="after")
    def separate(self):
        host, build = self.producer.target, self.build_authority.target
        if any(
            getattr(host, key) == getattr(build, key)
            for key in ("origin", "subject_id", "trust_domain", "certificate_sha256")
        ):
            raise ValueError("Build trust must be separate from metadata trust")
        return self
