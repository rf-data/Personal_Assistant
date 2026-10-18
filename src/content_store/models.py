"""content-v1 identity domains; original payloads are always opaque exact bytes."""

import hashlib
import json
import math
from typing import Annotated, Literal, Self

from pydantic import Field, JsonValue, model_validator

from src.content_store.errors import Forbidden, InvalidInput
from src.job_control.models import Contract, Identifier, Principal, Sha
from src.model_discovery.cs50 import CourseId, deterministic_id

MAX_BYTES = 64 * 1024 * 1024
MAX_BLOCKS = 50_000
Name = Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[^\x00-\x1f]+$")]
Size = Annotated[int, Field(strict=True, ge=0, le=MAX_BYTES)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    """C23 J(v): sorted keys, compact UTF-8, no LF, no normalization/NaN."""
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 64:
            raise InvalidInput("JSON depth limit")
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise InvalidInput("JSON object keys")
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, (tuple, list)):
            pending.extend((v, depth + 1) for v in item)
        elif item is not None and type(item) not in (str, int, float, bool):
            raise InvalidInput("JSON value type")
        elif isinstance(item, float) and not math.isfinite(item):
            raise InvalidInput("non-finite JSON number")
    try:
        result = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise InvalidInput("JSON encoding") from None
    if len(result) > MAX_BYTES:
        raise InvalidInput("JSON size limit")
    return result


def fingerprint(value) -> str:
    return sha256(canonical(value))


def snapshot(model):
    """Take a validated copy even when a caller mutated a nested Pydantic mapping."""
    return type(model).model_validate_json(canonical(model.model_dump(mode="json")))


class SourceRegistration(Contract):
    identity_namespace: Name
    external_identity: Name
    source_id: Name | None = None
    course_id: CourseId
    source_type: Literal["material", "transcript", "synthetic"]
    source_origin: Literal["official", "synthetic"]
    original_url: str | None = Field(default=None, max_length=4096)

    @model_validator(mode="after")
    def identity(self) -> Self:
        if self.identity_namespace == "cs50":
            # Discovery owns these IDs. Validate the alias, never rederive it here.
            if not self.source_id or self.source_id != self.external_identity:
                raise ValueError("CS50 registration requires its unchanged source ID")
            if not self.source_id.startswith("resource:"):
                raise ValueError("CS50 source ID must identify a resource")
        elif self.source_id is not None and self.source_id != self.resolved_id:
            raise ValueError("Generic source identity conflict")
        return self

    @property
    def resolved_id(self) -> str:
        if self.identity_namespace == "cs50":
            return self.source_id
        return deterministic_id(
            "content_source_v1", self.identity_namespace, self.external_identity
        )


class Source(Contract):
    schema_version: Literal[1] = 1
    source_id: Name
    registration: SourceRegistration
    owner_subject: Identifier
    acl_revision: int = Field(default=0, ge=0)
    state: Literal["registered", "tombstoned"] = "registered"
    publication_seq: int = Field(ge=1)

    @model_validator(mode="after")
    def identity(self) -> Self:
        if self.source_id != self.registration.resolved_id:
            raise ValueError("Source identity differs from registration")
        return self


class SourceView(Contract):
    """Redacted scalar projection, not a serialized internal Source/receipt."""

    schema_version: Literal[1] = 1
    source_id: Name
    course_id: CourseId
    source_type: str
    source_origin: str
    acl_revision: int


class SourceGrant(Contract):
    subject: Identifier
    permission: Literal["read"] = "read"


class ArtifactReference(Contract):
    sha256: Sha
    size_bytes: Size
    mime_type: Name

    @property
    def store_key(self) -> str:
        return f"blobs/sha256/{self.sha256[:2]}/{self.sha256}"


class RawArtifact(ArtifactReference):
    role: Name = "primary"
    ordinal: int = Field(default=0, strict=True, ge=0)


class RawManifest(Contract):
    artifacts: tuple[RawArtifact, ...] = Field(min_length=1, max_length=501)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        keys = [(a.role, a.ordinal) for a in self.artifacts]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise ValueError("Manifest must be sorted with unique role/ordinal")
        if sum(a.role == "primary" for a in self.artifacts) != 1:
            raise ValueError("Exactly one primary raw artifact required")
        return self

    @property
    def digest(self) -> str:
        return fingerprint([a.model_dump(mode="json") for a in self.artifacts])


class SourceVersion(Contract):
    schema_version: Literal[1] = 1
    source_version_id: Name
    source_id: Name
    variant_key: Name
    manifest: RawManifest
    binding_sha256: Sha
    state: Literal["verified", "quarantined"] = "verified"
    publication_seq: int = Field(ge=1)

    @model_validator(mode="after")
    def identity(self) -> Self:
        expected = deterministic_id(
            "content_source_version_v1",
            self.source_id,
            self.variant_key,
            self.manifest.digest,
        )
        if self.source_version_id != expected:
            raise ValueError("Source version identity mismatch")
        return self


class ParserConfiguration(Contract):
    parser_name: Name
    parser_version: Name
    parameters: dict[str, JsonValue]
    implementation_revision: Name
    payload_schema: Name
    projection_schema: Literal["projection.v1"] = "projection.v1"
    adapter_version: Name

    @model_validator(mode="after")
    def checked_json(self) -> Self:
        canonical(self.parameters)
        return self

    @property
    def config_id(self) -> str:
        return deterministic_id(
            "content_parser_v1", fingerprint(self.model_dump(mode="json"))
        )


class ParsedDocument(Contract):
    source_id: Name
    representation_key: Name

    @property
    def parsed_document_id(self) -> str:
        return deterministic_id(
            "content_document_v1", self.source_id, self.representation_key
        )


class ContentLocator(Contract):
    raw_artifact_sha256: Sha
    origin_pointer: str = Field(min_length=1, max_length=2000, pattern=r"^/")
    page: int | None = Field(default=None, strict=True, ge=1)
    dom: str | None = Field(default=None, max_length=2000)
    line_start: int | None = Field(default=None, strict=True, ge=1)
    line_end: int | None = Field(default=None, strict=True, ge=1)
    bbox: tuple[float, float, float, float] | None = None
    coordinate_system: Name = "unknown"
    chapter_path: tuple[Name, ...] = ()
    original_segment_id: int | None = Field(default=None, strict=True, ge=0)
    time_status: Literal["known", "unknown", "not_applicable"]
    start: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    end: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def intervals(self) -> Self:
        if self.time_status == "known":
            if self.start is None or self.end is None or self.end < self.start:
                raise ValueError("Known time requires ordered finite endpoints")
        elif self.start is not None or self.end is not None:
            raise ValueError("Unknown/not applicable time requires null endpoints")
        if self.line_end is not None and (
            self.line_start is None or self.line_end < self.line_start
        ):
            raise ValueError("Invalid line interval")
        if self.bbox is not None and (
            not all(math.isfinite(v) for v in self.bbox)
            or self.bbox[2] < self.bbox[0]
            or self.bbox[3] < self.bbox[1]
        ):
            raise ValueError("Invalid bounding box")
        return self


class ContentBlock(Contract):
    block_id: Name
    order: int = Field(strict=True, ge=0)
    type: Literal[
        "heading",
        "paragraph",
        "code",
        "table",
        "formula",
        "image_reference",
        "list",
        "link",
        "unknown_block",
    ]
    original_type: Name
    payload_pointer: str = Field(pattern=r"^/", max_length=2000)
    text: str
    data: dict[str, JsonValue] = Field(default_factory=dict)
    aggregation_role: Literal[
        "primary",
        "structure",
        "reference_projection",
        "alternative_view",
        "non_text_reference",
    ] = "primary"
    locators: tuple[ContentLocator, ...] = Field(min_length=1, max_length=501)

    @property
    def text_sha256(self) -> str:
        return sha256(self.text.encode("utf-8"))


class ParsedDocumentVersion(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    parsed_document_id: Name
    source_version_id: Name
    source_id: Name
    slot_id: Name
    parser_config_id: Name
    payload: ArtifactReference
    projection: ArtifactReference
    payload_schema: Name
    original_document_id: Name | None = None
    state: Literal["published", "quarantined", "tombstoned"] = "published"
    quality_status: Literal["synthetic_test_only", "passed", "passed_with_warnings"]
    publication_seq: int = Field(ge=1)

    @model_validator(mode="after")
    def identity(self) -> Self:
        slot = deterministic_id(
            "content_slot_v1",
            self.source_version_id,
            self.parsed_document_id,
            self.parser_config_id,
        )
        expected = deterministic_id(
            "content_version_v1", slot, self.payload.sha256, self.projection.sha256
        )
        if self.slot_id != slot or self.parsed_version_id != expected:
            raise ValueError("Parsed version identity mismatch")
        return self


class ParsedDocumentView(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    source_id: Name
    source_version_id: Name
    parser_config_id: Name
    payload_sha256: Sha
    projection_sha256: Sha
    quality_status: Literal["synthetic_test_only", "passed", "passed_with_warnings"]


class PublishedVersion(Contract):
    version: ParsedDocumentVersion
    created: bool


class BlockPage(Contract):
    """Internal trusted read projection; an HTTP redaction adapter is still required."""

    items: tuple[ContentBlock, ...]
    next_cursor: None = None


class RetryAttempt(Contract):
    """Explicit v1 attempt after operator abandonment; never a slot override."""

    schema_version: Literal[1] = 1
    rejected_run_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    request_key: Name


class ProcessingRun(Contract):
    run_id: Identifier
    source_id: Name
    actor: Identifier
    kind: Literal["raw", "synthetic"]
    slot_id: Name
    request_key: Name
    request_fingerprint: Sha
    acl_revision: int = Field(ge=0)
    state: Literal["preparing", "prepared", "committed", "blocked", "rejected"]
    manifest: tuple[ArtifactReference, ...] = ()
    parsed_version_id: Name | None = None
    recovery: ArtifactReference | None = None
    retry_of: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    error_code: str | None = None


def checked_actor(actor) -> Principal:
    if not isinstance(actor, Principal):
        raise Forbidden("authenticated Principal required")
    return snapshot(actor)
