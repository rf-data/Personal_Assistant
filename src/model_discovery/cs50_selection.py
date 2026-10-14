"""Immutable dry-run contracts; action names do not import execution configuration."""

from typing import Literal

from pydantic import Field, HttpUrl

from src.model_discovery.cs50 import (
    CourseDiscovery,
    DiscoveryModel,
    NonEmpty,
    ResourceRole,
)

# Exact ResourceAction values; importing that enum initializes environment settings.
ProposedAction = Literal["download", "parse_subtitle", "transcribe"]


class SelectionPolicy(DiscoveryModel):
    preferred_language: NonEmpty = "en"
    preferred_video_resolution: Literal["360p", "720p", "1080p", "4k"] = "720p"
    prefer_sdr: bool = True
    require_video: bool = False
    allow_unknown_language: bool = False
    allow_transcription: bool = False


class SelectionOption(DiscoveryModel):
    resource_id: str
    role: ResourceRole
    original_url: HttpUrl
    variant_id: str | None = None
    language: str | None = None
    format: str | None = None
    resolution: str | None = None
    dynamic_range: str | None = None


class SelectionDecision(DiscoveryModel):
    purpose: Literal["text", "video"]
    selected: SelectionOption | None = None
    alternatives: tuple[SelectionOption, ...] = ()
    actions: tuple[ProposedAction, ...] = ()
    reason: str
    warnings: tuple[str, ...] = ()


class LecturePreview(DiscoveryModel):
    resource_id: str
    section_keys: tuple[str, ...]
    decisions: tuple[SelectionDecision, ...]


class CoursePreview(DiscoveryModel):
    discovery: CourseDiscovery
    policy: SelectionPolicy
    lectures: tuple[LecturePreview, ...] = Field(default=())
