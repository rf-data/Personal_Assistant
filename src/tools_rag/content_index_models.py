"""Versioned derived-index, receipt and redacted lexical-search contracts."""

from typing import Literal

from pydantic import Field, model_validator

from src.content_store.index_models import IndexProjectionConfig
from src.content_store.models import Name
from src.content_store.read_models import LocatorDTO, TextWindow
from src.job_control.models import Contract, Sha

GEN_PATTERN = r"^content_index_generation_v1:[0-9a-f]{64}$"


class IndexSelection(Contract):
    schema_version: Literal[1] = 1
    parsed_version_ids: tuple[Name, ...] = Field(max_length=128)
    config: IndexProjectionConfig = Field(
        default_factory=lambda: IndexProjectionConfig(schema_version=1)
    )

    @model_validator(mode="after")
    def unique(self):
        if self.parsed_version_ids != tuple(sorted(set(self.parsed_version_ids))):
            raise ValueError("selection must be sorted and unique")
        return self


class VersionBinding(Contract):
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    parser_config_id: Name
    payload_sha256: Sha
    projection_sha256: Sha


class FileProof(Contract):
    name: str = Field(pattern=r"^source-[0-9a-f]{64}\.sqlite3$")
    sha256: Sha
    size_bytes: int = Field(strict=True, ge=0, le=64 * 1024**2)
    source_id: Name
    record_count: int = Field(strict=True, ge=0, le=200000)
    record_set_sha256: Sha


class GenerationBasis(Contract):
    schema_version: Literal[1] = 1
    selection: IndexSelection
    versions: tuple[VersionBinding, ...] = Field(max_length=128)
    record_set_sha256: Sha
    policy_id: Name
    backend: dict[str, str]


class GenerationManifest(Contract):
    schema_version: Literal[1] = 1
    generation_id: str = Field(pattern=GEN_PATTERN)
    build_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    purpose: Literal["content", "synthetic_test"]
    state: Literal["ready"] = "ready"
    basis: GenerationBasis
    files: tuple[FileProof, ...] = Field(max_length=128)
    record_count: int = Field(strict=True, ge=0, le=200000)
    digest: Sha


class ActiveGeneration(Contract):
    schema_version: Literal[1] = 1
    generation_id: str = Field(pattern=GEN_PATTERN)
    build_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    manifest_sha256: Sha


class BuildReceipt(Contract):
    schema_version: Literal[1] = 1
    build_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    actor: Name
    source_ids: tuple[Name, ...]
    selection: IndexSelection
    state: Literal[
        "preparing",
        "building",
        "verifying",
        "ready",
        "active",
        "failed",
        "interrupted",
        "retired",
        "discarded",
    ]
    generation_id: str | None = Field(default=None, pattern=GEN_PATTERN)
    error_code: str | None = None
    record_count: int = 0
    record_set_sha256: Sha | None = None
    snapshot: tuple[int, int] | None = None
    acl_revisions: dict[str, int] = Field(default_factory=dict)
    started_at: str
    finished_at: str | None = None
    implementation_version: Literal["content_fts5_v1"] = "content_fts5_v1"


class ScoreComponent(Contract):
    backend: Literal["sqlite_fts5"] = "sqlite_fts5"
    source_id: Name
    raw_score: float = Field(allow_inf_nan=False)
    score_schema: Literal["sqlite_fts5_bm25_v1"] = "sqlite_fts5_bm25_v1"
    direction: Literal["lower_is_better"] = "lower_is_better"


class RecordAnchor(Contract):
    parsed_version_id: Name
    block_id: Name
    text_sha256: Sha
    start: int = Field(strict=True, ge=0)
    end: int = Field(strict=True, ge=1)
    offset_unit: Literal["unicode_codepoint"] = "unicode_codepoint"


class SearchHit(Contract):
    schema_version: Literal[1] = 1
    index_record_id: Name
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    block_id: Name
    content_type: str
    anchor: RecordAnchor
    excerpt: TextWindow
    locators: tuple[LocatorDTO, ...] | None
    locators_in_structure: bool
    structure_route: str
    text_route: str
    method: Literal["lexical"] = "lexical"
    components: tuple[ScoreComponent, ...]
    ranking_score: float = Field(allow_inf_nan=False)
    ranking_schema: Literal["source_rrf_v1"] = "source_rrf_v1"
    index_generation: Sha
    projection_fingerprint: Sha


class SearchResultPage(Contract):
    schema_version: Literal[1] = 1
    items: tuple[SearchHit, ...]
    next_cursor: str | None
    index_generation: Sha | None
    ranking_schema: Literal["source_rrf_v1"] = "source_rrf_v1"
    selection_scope: Literal["explicit_active_selection"] = "explicit_active_selection"


class SearchCursor(Contract):
    schema_version: Literal[1] = 1
    actor: Sha
    request: Sha
    generation: Sha
    snapshot: Sha
    results: Sha
    last: Name
    expires: int = Field(strict=True, ge=0)
