"""Durable post-verification commit intentions, not caller publication authority."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from src.content_store.models import (
    MAX_BLOCKS,
    ArtifactReference,
    ContentBlock,
    ParsedDocument,
    ParsedDocumentVersion,
    ParserConfiguration,
    SourceRegistration,
    SourceVersion,
)
from src.job_control.models import Contract, Identifier, Sha


class RawIntent(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["raw"] = "raw"
    run_id: Identifier
    reference: ArtifactReference


class BindingIntent(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["binding"] = "binding"
    run_id: Identifier
    registration: SourceRegistration
    version: SourceVersion
    reference: ArtifactReference


class NamedArtifact(Contract):
    role: str = Field(min_length=1, max_length=200)
    reference: ArtifactReference


class PublicationIntent(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["parsed"] = "parsed"
    run_id: Identifier
    registration: SourceRegistration
    source_version: SourceVersion
    stream: ParsedDocument
    config: ParserConfiguration
    version: ParsedDocumentVersion
    blocks: tuple[ContentBlock, ...] = Field(max_length=MAX_BLOCKS)
    artifacts: tuple[NamedArtifact, ...] = Field(min_length=7, max_length=510)

    @model_validator(mode="after")
    def identities(self):
        v = self.version
        if (
            v.source_id != self.registration.resolved_id
            or self.stream.source_id != v.source_id
            or self.source_version.source_id != v.source_id
            or v.source_version_id != self.source_version.source_version_id
            or self.stream.parsed_document_id != v.parsed_document_id
            or self.config.config_id != v.parser_config_id
            or v.payload_schema != self.config.payload_schema
            or v.quality_status == "synthetic_test_only"
            or len({a.role for a in self.artifacts}) != len(self.artifacts)
        ):
            raise ValueError("Prepared publication identity conflict")
        named = {a.role: a.reference for a in self.artifacts}
        if (
            named.get("payload") != v.payload
            or named.get("projection") != v.projection
            or named.get("binding") is None
            or named["binding"].sha256 != self.source_version.binding_sha256
            or not {"receipt", "plan", "implementation", "quality"} <= named.keys()
        ):
            raise ValueError("Prepared publication reference conflict")
        if [b.order for b in self.blocks] != list(range(len(self.blocks))) or len(
            {b.block_id for b in self.blocks}
        ) != len(self.blocks):
            raise ValueError("Prepared block identity/order conflict")
        hashes = {a.sha256 for a in self.source_version.manifest.artifacts}
        if any(
            loc.raw_artifact_sha256 not in hashes
            for b in self.blocks
            for loc in b.locators
        ):
            raise ValueError("Prepared locator outside source version")
        return self


Intent = Annotated[
    RawIntent | BindingIntent | PublicationIntent, Field(discriminator="kind")
]


class IntegrityFinding(Contract):
    code: str
    artifact_sha256: Sha | None = None
    source_version_ids: tuple[str, ...] = ()
    parsed_version_ids: tuple[str, ...] = ()
    run_ids: tuple[str, ...] = ()


class IntegrityReport(Contract):
    schema_version: Literal[1] = 1
    findings: tuple[IntegrityFinding, ...]
    checked_artifacts: int
    quarantined_artifacts: int
    quarantined_source_versions: int
    quarantined_parsed_versions: int
    incident_id: str | None = None

    @property
    def healthy(self):
        return not self.findings and not (
            self.quarantined_artifacts
            or self.quarantined_source_versions
            or self.quarantined_parsed_versions
        )


class RecoveryResult(Contract):
    run_id: Identifier
    outcome: Literal["committed", "already_committed", "blocked", "rejected"]
    parsed_version_id: str | None = None
    reason: str | None = None
