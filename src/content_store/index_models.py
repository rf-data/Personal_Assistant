"""C24 projection contracts. No index backend, generation activation or I/O."""

from typing import Literal

from pydantic import Field, model_validator

from src.content_store.models import (
    ContentLocator,
    Name,
    canonical,
    fingerprint,
    sha256,
)
from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import CourseId, deterministic_id

MAX_RECORDS = 200_000
MAX_RESULT_BYTES = 64 * 1024**2


class _Versioned(Contract):
    @model_validator(mode="before")
    @classmethod
    def explicit_schema(cls, value):
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("explicit integer schema_version required")
        return value


class IndexProjectionConfig(_Versioned):
    schema_version: Literal[1]
    selection: Literal["content_primary_v1"] = "content_primary_v1"
    max_codepoints: int = Field(default=2000, strict=True, ge=1, le=2000)
    overlap_codepoints: Literal[0, 128] = 0
    boundary: Literal["block"] = "block"
    normalization: Literal["none"] = "none"
    chapter_context: Literal["metadata_only"] = "metadata_only"
    empty_text: Literal["reference_only"] = "reference_only"

    @model_validator(mode="after")
    def progress(self):
        if type(self.overlap_codepoints) is not int or (
            self.overlap_codepoints >= self.max_codepoints
        ):
            raise ValueError("overlap must be smaller than the window")
        return self

    @property
    def policy_id(self):
        return deterministic_id(
            "content_index_policy_v1", fingerprint(self.model_dump(mode="json"))
        )


class IndexRecordBody(_Versioned):
    schema_version: Literal[1]
    index_schema: Literal["content_index_record_v1"]
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    course_id: CourseId
    block_id: Name
    block_order: int = Field(strict=True, ge=0)
    content_type: Literal["heading", "paragraph", "code", "table", "formula", "list"]
    original_type: Name
    aggregation_role: Literal["primary"]
    origin_pointer: str = Field(pattern=r"^/(?:blocks|segments)/[0-9]+$")
    text_sha256: Sha
    text_length: int = Field(strict=True, ge=1)
    start: int = Field(strict=True, ge=0)
    end: int = Field(strict=True, ge=1)
    offset_unit: Literal["unicode_codepoint"]
    search_text: str = Field(min_length=1, max_length=2000)
    search_text_sha256: Sha
    locators: tuple[ContentLocator, ...] = Field(min_length=1, max_length=501)
    parser_config_id: Name
    parser_fingerprint: Sha
    payload_sha256: Sha
    projection_sha256: Sha
    projection_policy_id: Name

    @model_validator(mode="after")
    def window(self):
        if (
            not self.start < self.end <= self.text_length
            or len(self.search_text) != self.end - self.start
            or sha256(self.search_text.encode("utf-8")) != self.search_text_sha256
            or any(loc.origin_pointer != self.origin_pointer for loc in self.locators)
        ):
            raise ValueError("index window/hash/locator mismatch")
        return self

    @property
    def record_id(self):
        return deterministic_id(
            "content_index_record_v1", fingerprint(self.model_dump(mode="json"))
        )


class IndexRecord(_Versioned):
    schema_version: Literal[1]
    body: IndexRecordBody
    index_record_id: Name
    # Projection-only output has no build, and must not pretend to be active.
    generation_id: Name | None = None
    build_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")

    @model_validator(mode="after")
    def identity(self):
        if self.index_record_id != self.body.record_id:
            raise ValueError("index record identity mismatch")
        if (self.generation_id is None) != (self.build_id is None):
            raise ValueError("generation and build must be bound together")
        return self


def record_set_sha256(records):
    """C24 length-framed canonical bodies; build context is deliberately excluded."""
    import hashlib

    digest = hashlib.sha256()
    ids = set()
    for record in sorted(records, key=lambda r: r.index_record_id):
        if record.index_record_id in ids:
            raise ValueError("duplicate index record identity")
        ids.add(record.index_record_id)
        data = canonical(
            dict(
                index_record_id=record.index_record_id,
                body=record.body.model_dump(mode="json"),
            )
        )
        digest.update(str(len(data)).encode("ascii") + b":" + data)
    return digest.hexdigest()


class ProjectionExclusion(Contract):
    block_id: Name
    block_order: int = Field(strict=True, ge=0)
    reason: Literal[
        "table_of_contents",
        "reference_projection",
        "geometric_table_projection",
        "list_structure",
        "non_text_reference",
        "alternative_view",
        "empty_text",
        "whitespace_window",
    ]
    start: int | None = Field(default=None, strict=True, ge=0)
    end: int | None = Field(default=None, strict=True, ge=0)

    @model_validator(mode="after")
    def interval(self):
        if (self.start is None) != (self.end is None) or (
            self.start is not None and self.start > self.end
        ):
            raise ValueError("invalid excluded interval")
        return self


class IndexProjectionBody(_Versioned):
    schema_version: Literal[1]
    projection_version: Literal["content_index_projection_v1"]
    status: Literal["projected"]
    usage: Literal["verified_content", "synthetic_test_only"]
    source_origin: Literal["official", "synthetic"]
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    parser_config_id: Name
    payload_sha256: Sha
    projection_sha256: Sha
    config: IndexProjectionConfig
    config_fingerprint: Sha
    record_count: int = Field(strict=True, ge=0, le=MAX_RECORDS)
    exclusion_count: int = Field(strict=True, ge=0)
    error_count: Literal[0]
    record_set_sha256: Sha
    records: tuple[IndexRecord, ...] = Field(max_length=MAX_RECORDS)
    exclusions: tuple[ProjectionExclusion, ...]

    @model_validator(mode="after")
    def consistent(self):
        if (
            self.record_count != len(self.records)
            or self.exclusion_count != len(self.exclusions)
            or self.config_fingerprint
            != fingerprint(self.config.model_dump(mode="json"))
            or self.record_set_sha256 != record_set_sha256(self.records)
        ):
            raise ValueError("projection manifest mismatch")
        keys = []
        for record in self.records:
            b = record.body
            if (
                (b.source_id, b.source_version_id, b.parsed_version_id)
                != (self.source_id, self.source_version_id, self.parsed_version_id)
                or b.parser_config_id != self.parser_config_id
                or b.payload_sha256 != self.payload_sha256
                or b.projection_sha256 != self.projection_sha256
                or b.projection_policy_id != self.config.policy_id
                or b.end - b.start > self.config.max_codepoints
                or record.generation_id is not None
                or record.build_id is not None
            ):
                raise ValueError("cross-version/config/build projection")
            keys.append((b.block_order, b.start, record.index_record_id))
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("projection order/identity mismatch")
        return self


class IndexProjectionResult(_Versioned):
    schema_version: Literal[1]
    body: IndexProjectionBody
    digest: Sha

    @model_validator(mode="after")
    def checksum(self):
        if self.digest != fingerprint(self.body.model_dump(mode="json")):
            raise ValueError("projection digest mismatch")
        canonical(self.model_dump(mode="json"))
        return self
