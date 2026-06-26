## transcribe_models.py
# import
from dataclasses import dataclass 


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None
    confidence: float | None = None


@dataclass
class TranscriptDocument:
    source: str
    language: str
    duration: float | None
    segments: list[TranscriptSegment]
    text: str