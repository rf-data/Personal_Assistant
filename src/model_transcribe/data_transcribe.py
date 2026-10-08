## data_transcribe.py
# import
from datetime import datetime
from pydantic import BaseModel, Field  # dataclass
from pathlib import Path

# from typing import Protocol
from enum import Enum


# @dataclass
class TranscriptSegment(BaseModel):
    seg_id: int
    start: float
    end: float
    text: str
    speaker: str | None = None
    confidence: float | None = None


class TranscriptSource(str, Enum):
    MANUAL_SUBTITLE = "manual_subtitle"
    AUTO_SUBTITLE = "auto_subtitle"
    WHISPER = "whisper"


class DownloadStrategy(str, Enum):
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
