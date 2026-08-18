## data_transcribe.py
# import
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


class TranscriptSource(str, Enum):
    MANUAL_SUBTITLE = "manual_subtitle"
    AUTO_SUBTITLE = "auto_subtitle"
    WHISPER = "whisper"


class DownloadStrategy(str, Enum):
    AUDIO_DEFAULT = "audio_default"
    AUDIO_FALLBACK = "audio_fallback"
    SUBTITLES = "subtitles"


class DownloadResult(BaseModel):
    success: bool
    strategy: DownloadStrategy | None = None
    transcript_source: TranscriptSource | None = None
    paths: list[Path] = Field(default_factory=list)
    error: str | None = None