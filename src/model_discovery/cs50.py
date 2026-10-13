"""Offline discovery contracts; independent of lecture execution models."""

import hashlib
import json
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

CourseId = Literal[
    "cs50x", "cs50_python", "cs50_sql", "cs50_ai", "cs50_web", "cs50_cybersecurity"
]
NonEmpty = Annotated[str, Field(min_length=1, pattern=r"\S")]


class DiscoveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DiscoveryStatus(StrEnum):
    REFERENCED = "referenced"
    PARSED = "parsed"


class ResourceRole(StrEnum):
    LECTURE_VIDEO = "lecture_video"
    AUDIO = "audio"
    NOTES = "notes"
    SLIDES = "slides"
    SOURCE_CODE = "source_code"
    SUBTITLES = "subtitles"
    TRANSCRIPT = "transcript"
    SHORT = "short"
    SECTION = "section"
    DEMO = "demo"
    PROBLEM_SET = "problem_set"
    QUIZ = "quiz"
    PROJECT = "project"
    PRACTICE = "practice"
    STARTER_FILES = "starter_files"
    REFERENCE = "reference"
    OTHER = "other"


def deterministic_id(kind: str, *parts: str) -> str:
    """Hash an unambiguous, ordered identity tuple; never use Python hash()."""
    payload = json.dumps([kind, *parts], ensure_ascii=False, separators=(",", ":"))
    return f"{kind}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


class Provenance(DiscoveryModel):
    original_url: HttpUrl
    fixture_file: NonEmpty | None = None
    locator: NonEmpty | None = None
    context_path: tuple[NonEmpty, ...] = ()


class DiscoveryWarning(DiscoveryModel):
    code: NonEmpty
    message: NonEmpty
    course_id: CourseId
    section_key: NonEmpty | None = None
    provenance: tuple[Provenance, ...] = ()


class MediaVariant(DiscoveryModel):
    original_url: HttpUrl
    media_type: Literal["audio", "video"]
    language: NonEmpty | None = None
    format: NonEmpty | None = None
    resolution: NonEmpty | None = None
    dynamic_range: Literal["hdr", "sdr"] | None = None
    media_id: NonEmpty | None = None
    provenance: tuple[Provenance, ...] = ()

    @property
    def variant_id(self) -> str:
        return deterministic_id("variant", self.media_type, str(self.original_url))


class ResourceCandidate(DiscoveryModel):
    course_id: CourseId
    role: ResourceRole
    original_url: HttpUrl
    title: NonEmpty | None = None
    section_keys: tuple[NonEmpty, ...] = ()
    parent_resource_id: NonEmpty | None = None
    language: NonEmpty | None = None
    format: NonEmpty | None = None
    status: DiscoveryStatus = DiscoveryStatus.REFERENCED
    variants: tuple[MediaVariant, ...] = ()
    provenance: tuple[Provenance, ...] = ()

    @property
    def resource_id(self) -> str:
        return deterministic_id(
            "resource",
            self.course_id,
            self.role.value,
            str(self.original_url),
            self.language or "",
            self.parent_resource_id or "",
        )

    @model_validator(mode="after")
    def unique_variants(self) -> Self:
        ids = [variant.variant_id for variant in self.variants]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate media variant URL/type in resource")
        if len(self.section_keys) != len(set(self.section_keys)):
            raise ValueError("Duplicate section key in resource")
        return self


class SectionDiscovery(DiscoveryModel):
    course_id: CourseId
    key: NonEmpty
    original_url: HttpUrl
    title: NonEmpty | None = None
    order: int = Field(default=0, ge=0)
    parent_key: NonEmpty | None = None
    status: DiscoveryStatus = DiscoveryStatus.REFERENCED
    provenance: tuple[Provenance, ...] = ()

    @property
    def section_id(self) -> str:
        return deterministic_id("section", self.course_id, self.key)


class CourseDiscovery(DiscoveryModel):
    course_id: CourseId
    original_url: HttpUrl
    title: NonEmpty | None = None
    provider: Literal["Harvard"] = "Harvard"
    platform: Literal["CS50"] = "CS50"
    status: DiscoveryStatus = DiscoveryStatus.REFERENCED
    sections: tuple[SectionDiscovery, ...] = ()
    resources: tuple[ResourceCandidate, ...] = ()
    warnings: tuple[DiscoveryWarning, ...] = ()
    provenance: tuple[Provenance, ...] = ()

    @property
    def discovery_id(self) -> str:
        return deterministic_id("course", self.course_id)

    @model_validator(mode="after")
    def validate_hierarchy(self) -> Self:
        children = (*self.sections, *self.resources, *self.warnings)
        if any(child.course_id != self.course_id for child in children):
            raise ValueError("Child course_id contradicts CourseDiscovery.course_id")
        sections = {section.key: section for section in self.sections}
        resources = {resource.resource_id: resource for resource in self.resources}
        if len(sections) != len(self.sections) or len(resources) != len(self.resources):
            raise ValueError("Duplicate section or resource identity")
        for section in self.sections:
            visited = {section.key}
            parent = section.parent_key
            while parent is not None:
                if parent not in sections:
                    raise ValueError(f"Unknown parent section: {parent}")
                if parent in visited:
                    raise ValueError(f"Section hierarchy cycle: {parent}")
                visited.add(parent)
                parent = sections[parent].parent_key
        for resource in self.resources:
            if set(resource.section_keys) - sections.keys():
                raise ValueError(
                    f"Unknown section key in resource: {resource.section_keys}"
                )
            visited_resources = {resource.resource_id}
            parent_id = resource.parent_resource_id
            while parent_id is not None:
                if parent_id not in resources:
                    raise ValueError(f"Unknown parent resource: {parent_id}")
                if parent_id in visited_resources:
                    raise ValueError("Resource hierarchy cycle")
                visited_resources.add(parent_id)
                parent_id = resources[parent_id].parent_resource_id
        for warning in self.warnings:
            if warning.section_key is not None and warning.section_key not in sections:
                raise ValueError(f"Unknown warning section: {warning.section_key}")
        return self
