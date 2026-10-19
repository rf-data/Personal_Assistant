"""C16 index job input and redacted status; existing C24 index formats unchanged."""

from typing import Literal

from pydantic import Field, model_validator

from src.content_store.models import Name, fingerprint
from src.content_store.read_models import ContentReadSettings
from src.content_store.search_models import SearchSettings
from src.job_control.models import Contract, Identifier, Job, Sha
from src.model_discovery.cs50 import CourseId
from src.tools_rag.content_index_models import IndexSelection, VersionBinding


class IndexJobPlan(Contract):
    schema_version: Literal[1]
    course_id: CourseId
    content: ContentReadSettings
    search: SearchSettings
    selection: IndexSelection
    versions: tuple[VersionBinding, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="before")
    @classmethod
    def version(cls, value):
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("explicit integer version required")
        return value

    @model_validator(mode="after")
    def pinned_selection(self):
        if (
            tuple(v.parsed_version_id for v in self.versions)
            != self.selection.parsed_version_ids
        ):
            raise ValueError("complete ordered version bindings required")
        if self.content.root.is_relative_to(
            self.search.index_root
        ) or self.search.index_root.is_relative_to(self.content.root):
            raise ValueError("separate content and index roots required")
        if self.content.cursor_key_file.is_relative_to(self.search.index_root):
            raise ValueError("separate cursor key required")
        return self

    @property
    def source_ids(self):
        return tuple(sorted({v.source_id for v in self.versions}))

    @property
    def selection_sha256(self):
        return fingerprint(
            dict(
                selection=self.selection.model_dump(mode="json"),
                versions=[v.model_dump(mode="json") for v in self.versions],
            )
        )


class IndexInput(Contract):
    schema_version: Literal[1] = 1
    input_ref: Identifier
    course_id: CourseId
    source_ids: tuple[Name, ...]
    parsed_version_ids: tuple[Name, ...]
    selection_sha256: Sha
    can_build: bool


class IndexJobReceipt(Contract):
    schema_version: Literal[1] = 1
    job_id: Identifier
    build_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    outcome: Literal["activated", "already_active"]
    index_generation: Sha
    source_ids: tuple[Name, ...]
    parsed_version_ids: tuple[Name, ...]
    selection_sha256: Sha
    record_set_sha256: Sha
    record_count: int = Field(strict=True, ge=0, le=200000)


class IndexStatus(Contract):
    schema_version: Literal[1] = 1
    input: IndexInput
    state: Literal["not_indexed", "active", "stale", "blocked", "failed", "building"]
    index_generation: Sha | None = None
    jobs: tuple[Job, ...] = Field(max_length=20)
    next_offset: int | None = None
    receipt: IndexJobReceipt | None = None
    # Job cancellation/failure never asserts rollback of an already atomic index swap.
    latest_activation: Literal["committed", "not_committed", "undetermined"] = (
        "undetermined"
    )
    retry_policy: Literal["explicit_new_request_only"] = "explicit_new_request_only"
