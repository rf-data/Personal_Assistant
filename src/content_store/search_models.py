"""Opt-in lexical HTTP contract; hits/pages remain the existing C24 DTOs."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.artifacts import explicit_root
from src.content_store.models import Name
from src.job_control.models import Contract
from src.model_discovery.cs50 import CourseId

ContentType = Literal[
    "heading",
    "paragraph",
    "code",
    "table",
    "formula",
    "list",
    "link",
    "image_reference",
    "unknown_block",
]


class SearchSettings(Contract):
    schema_version: Literal[1]
    index_root: Path

    @model_validator(mode="after")
    def explicit_index(self):
        explicit_root(self.index_root)
        return self


class SearchRequest(Contract):
    schema_version: Literal[1]
    query: str = Field(min_length=1, max_length=512)
    course_id: CourseId | None = None
    source_ids: tuple[Name, ...] | None = Field(
        default=None, min_length=1, max_length=32
    )
    content_types: tuple[ContentType, ...] | None = Field(
        default=None, min_length=1, max_length=9
    )
    limit: int = Field(default=20, strict=True, ge=1, le=100)
    cursor: str | None = Field(
        default=None, min_length=20, max_length=1600, pattern=r"^[A-Za-z0-9_-]+$"
    )

    @model_validator(mode="before")
    @classmethod
    def explicit_version(cls, value):
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("explicit integer schema_version required")
        return value

    @model_validator(mode="after")
    def bounded_query(self):
        terms = self.query.split()
        if not terms or len(terms) > 8 or any(len(t) > 64 for t in terms):
            raise ValueError("bounded literal terms required")
        if len(self.query.encode("utf-8")) > 2048:
            raise ValueError("query byte limit")
        for values in (self.source_ids, self.content_types):
            if values is not None and len(set(values)) != len(values):
                raise ValueError("unique filters required")
        return self


class SearchCapabilities(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_content_search_v1"] = (
        "personal_assistant_content_search_v1"
    )
    enabled: bool
    capabilities: tuple[Literal["content_search_lexical_v1"], ...]
    method: Literal["lexical"] = "lexical"
    max_query_codepoints: Literal[512] = 512
    max_query_bytes: Literal[2048] = 2048
    max_terms: Literal[8] = 8
    max_term_codepoints: Literal[64] = 64
    max_sources: Literal[32] = 32
    max_limit: Literal[100] = 100
    max_page_bytes: Literal[262144] = 262144
    cursor_ttl_seconds: Literal[300] = 300
