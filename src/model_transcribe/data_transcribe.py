## data_transcribe.py
# import
from datetime import datetime

# from typing import Protocol
from enum import Enum
from math import isfinite
from pathlib import Path

from pydantic import BaseModel, Field, model_validator  # dataclass


# @dataclass
class TranscriptSegment(BaseModel):
    """Seconds from the source, or two explicit nulls for an unlocated segment."""

    seg_id: int
    start: float | None = Field(ge=0, allow_inf_nan=False)
    end: float | None = Field(ge=0, allow_inf_nan=False)
    text: str
    speaker: str | None = None
    confidence: float | None = None

    @model_validator(mode="after")
    def valid_interval(self):
        if (self.start is None) != (self.end is None):
            raise ValueError("Transcript times must both be known or both null")
        if self.start is not None and self.end < self.start:
            raise ValueError("Transcript end precedes start")
        return self

    def require_timestamps(self) -> tuple[float, float]:
        """Guard timed adapters, including models copied without validation."""
        if self.start is None or self.end is None:
            raise ValueError(
                "unknown_transcript_time: known segment timestamps required; "
                "plain-text transcripts need a text-based chunking strategy."
            )
        if not (
            isfinite(self.start) and isfinite(self.end) and 0 <= self.start <= self.end
        ):
            raise ValueError("invalid_transcript_time: invalid segment interval")
        return self.start, self.end


class TranscriptSource(str, Enum):  # noqa: UP042 - preserve legacy Enum string behavior
    MANUAL_SUBTITLE = "manual_subtitle"
    AUTO_SUBTITLE = "auto_subtitle"
    WHISPER = "whisper"
    OFFICIAL_TRANSCRIPT = "official_transcript"
    OFFICIAL_SUBTITLE = "official_subtitle"


class DownloadStrategy(str, Enum):  # noqa: UP042 - preserve legacy Enum string behavior
    SUBTITLES = "subtitles"

    AUDIO_DEFAULT = "audio_default"
    AUDIO_FALLBACK = "audio_fallback"

    AUDIO_WEB_FALLBACK = "audio_web_fallback"
    # AUDIO_POT = "audio_po_token"
    # BROWSER_CAPTURE = "browser_capture"


class DownloadResult(BaseModel):
    success: bool

    strategy: DownloadStrategy | None = None
    transcript_source: TranscriptSource | None = None

    paths: list[Path] = Field(default_factory=list)

    language: str | None = None
    media_format: str | None = None

    error: str | None = None


class TranscriptProvenance(BaseModel):
    transcript_source: TranscriptSource
    download_strategy: DownloadStrategy | None = None

    source_url: str | None = None
    source_file: str | None = None

    language: str | None = None
    media_id: str | None = None

    media_format: str | None = None

    transcription_provider: str | None = None
    transcription_model: str | None = None

    acquired_at: datetime = Field(default_factory=datetime.now)


# @dataclass
class TranscriptDocument(BaseModel):
    source: str
    language: str | None = None
    language_probability: float | None = None

    duration: float | None = None
    duration_after_vad: float | None = None

    runtime: float | None = None
    realtime_factor: float | None = None

    segments: list[TranscriptSegment]
    text: str

    provenance: TranscriptProvenance | None = None

    @model_validator(mode="after")
    def unknown_duration(self):
        if self.duration is not None and any(s.start is None for s in self.segments):
            raise ValueError(
                "Transcript duration must be null with unknown segment times"
            )
        return self

    def require_timestamps(self) -> None:
        """No serialization fields or invented timestamps are added by this check."""
        for segment in self.segments:
            segment.require_timestamps()


"""
├── source
│   ├── source_id
│   ├── course_id
│   ├── resource_kind
│   ├── resource_type
│   ├── lecture_no
│   ├── topic
│   ├── title
│   ├── source_url
│   └── license
│
└── metadata
    ├── statement_id / expression_id
    ├── semantic_type
    ├── start
    ├── end
    ├── confidence
    ├── verification
    └── ...
"""
