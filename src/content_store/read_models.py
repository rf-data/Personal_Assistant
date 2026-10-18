"""Versioned opt-in configuration and redacted content wire contracts."""

from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue, model_validator

from src.content_store.models import ContentLocator, Name
from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import CourseId

MAX_PAGE = 256 * 1024
MAX_ATTACHMENT = 64 * 1024 * 1024


class ContentReadSettings(Contract):
    schema_version: Literal[1] = 1
    root: Path
    cursor_key_file: Path

    @model_validator(mode="after")
    def explicit_paths(self):
        from src.content_store.artifacts import explicit_root

        explicit_root(self.root)
        if not self.cursor_key_file.is_absolute() or ".." in self.cursor_key_file.parts:
            raise ValueError("Explicit private cursor key required")
        if self.cursor_key_file.is_relative_to(self.root):
            raise ValueError("Cursor key must be outside content data")
        return self


class SourceDTO(Contract):
    schema_version: Literal[1] = 1
    source_id: Name
    course_id: CourseId
    source_type: Literal["material", "transcript", "synthetic"]
    source_origin: Literal["official", "synthetic"]
    original_url: str | None
    versions_route: str


class RawDTO(Contract):
    source_id: Name
    source_version_id: Name
    role: Name
    ordinal: int
    sha256: Sha
    size_bytes: int
    download_route: str


class SourceVersionDTO(Contract):
    schema_version: Literal[1] = 1
    source_id: Name
    source_version_id: Name
    artifacts: tuple[RawDTO, ...]
    parsed_versions_route: str


class ParsedRef(Contract):
    parsed_version_id: Name
    route: str


class WarningDTO(Contract):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]{0,95}$")
    severity: Literal["warning", "info"]
    category: Literal["technical", "semantic_review"]
    occurrences: int = Field(ge=1)


class ParsedDTO(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    source_id: Name
    source_version_id: Name
    parser_config_id: Name
    parser_name: str
    parser_version: str
    implementation_revision: str
    payload_schema: str
    payload_sha256: Sha
    projection_sha256: Sha
    quality_status: Literal["passed", "passed_with_warnings"]
    block_count: int
    warnings: tuple[WarningDTO, ...]
    blocks_route: str


class LocatorDTO(ContentLocator):
    """Only existing typed locator fields; raw references remain source-bound."""

    raw_reference: RawDTO


class BlockDTO(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    block_id: Name
    order: int
    type: str
    original_type: str
    aggregation_role: str
    quality_status: Literal["passed", "passed_with_warnings"]
    warnings: tuple[WarningDTO, ...]
    text: str | None
    text_length: int
    text_sha256: Sha
    text_route: str
    structure_route: str
    locators: tuple[LocatorDTO, ...] | None
    locators_in_structure: bool


class TextWindow(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    block_id: Name
    start: int
    end: int
    text_length: int
    text_sha256: Sha
    text: str


class StructureDTO(Contract):
    schema_version: Literal[1] = 1
    parsed_version_id: Name
    block_id: Name
    data: dict[str, JsonValue]
    locators: tuple[LocatorDTO, ...]
    redacted: bool
    projection_sha256: Sha


class ContentPage(Contract):
    schema_version: Literal[1] = 1
    items: tuple[SourceDTO | SourceVersionDTO | ParsedRef | BlockDTO, ...]
    next_cursor: str | None


class ContentCapabilities(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_content_read_v1"] = (
        "personal_assistant_content_read_v1"
    )
    enabled: bool
    capabilities: tuple[Literal["content_read_v1"], ...]
    max_page_bytes: Literal[262144] = MAX_PAGE
    max_text_codepoints: Literal[16384] = 16384
    max_attachment_bytes: Literal[67108864] = MAX_ATTACHMENT
