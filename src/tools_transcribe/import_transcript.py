"""Import official local transcripts without inference, downloads or execution config."""

import html
import re
from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, TypeAdapter

from src.model_transcribe.data_transcribe import (
    TranscriptDocument,
    TranscriptProvenance,
    TranscriptSegment,
    TranscriptSource,
)

_TIMESTAMP = re.compile(r"(?:(\d{2,}):)?(\d{2}):(\d{2})[.,](\d{3})")
# Remove subtitle presentation tags, not arbitrary text inside angle brackets.
_VTT_TAG = re.compile(
    r"</?(?:b|i|u|ruby|rt|c(?:\.[\w-]+)*|v|lang)(?:\s+[^>]*)?>"
    r"|<(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}>"
)


def _seconds(value: str, *, kind: str, cue: int) -> float:
    match = _TIMESTAMP.fullmatch(value)
    if not match or (kind == "srt" and (match[1] is None or "," not in value)):
        raise ValueError(f"{kind.upper()} cue {cue}: invalid timestamp {value!r}")
    if kind == "vtt" and "." not in value:
        raise ValueError(f"VTT cue {cue}: timestamps require a decimal point")
    hours, minutes, seconds, milliseconds = match.groups()
    if int(minutes) >= 60 or int(seconds) >= 60:
        raise ValueError(f"{kind.upper()} cue {cue}: timestamp out of range {value!r}")
    return (
        int(hours or 0) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )


def _subtitle_segments(content: str, kind: str) -> list[TranscriptSegment]:
    blocks = re.split(r"\n[ \t]*\n", content.strip())
    if kind == "vtt":
        header = blocks.pop(0).splitlines()
        if not header or not re.fullmatch(r"WEBVTT(?:[ \t].*)?", header[0]):
            raise ValueError(
                "VTT requires a WEBVTT header and a blank line before cues"
            )
        if any("-->" in line for line in header):
            raise ValueError("VTT requires a blank line after its header")
    segments = []
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        if kind == "vtt" and (
            re.match(r"NOTE(?:[ \t]|$)", lines[0]) or lines[0] in {"STYLE", "REGION"}
        ):
            continue
        cue = len(segments) + 1
        if kind == "srt":
            if not lines[0].isdigit():
                raise ValueError(f"SRT cue {cue}: missing numeric cue identifier")
            lines = lines[1:]
        elif "-->" not in lines[0]:
            lines = lines[1:]  # optional VTT cue identifier
        if not lines or "-->" not in lines[0]:
            raise ValueError(f"{kind.upper()} cue {cue}: missing timing line")
        timing = re.fullmatch(r"(\S+)\s+-->\s+(\S+)(?:[ \t]+(.*))?", lines[0])
        if not timing or (kind == "srt" and timing[3]):
            raise ValueError(f"{kind.upper()} cue {cue}: malformed timing line")
        start = _seconds(timing[1], kind=kind, cue=cue)
        end = _seconds(timing[2], kind=kind, cue=cue)
        if end < start:
            raise ValueError(f"{kind.upper()} cue {cue}: end precedes start")
        text = html.unescape(_VTT_TAG.sub("", "\n".join(lines[1:]))).strip()
        if not text:
            raise ValueError(f"{kind.upper()} cue {cue}: empty cue text")
        # Preserve source order, repeated cues and multiline boundaries. No deduplication.
        segments.append(
            TranscriptSegment(seg_id=len(segments), start=start, end=end, text=text)
        )
    if not segments:
        raise ValueError(f"No subtitle cues found in {kind.upper()} input")
    return segments


def import_transcript(
    path: Path,
    *,
    language: str,
    original_url: str,
    encoding: str = "utf-8-sig",
    format: Literal["txt", "srt", "vtt"] | None = None,
) -> TranscriptDocument:
    """Read one local file. Unknown TXT timestamps/duration remain None.

    UTF-8 (including BOM) is the default; other encodings must be explicit.
    Malformed/empty input fails rather than silently dropping cues. No file is written.
    """
    path = Path(path)
    kind = format or path.suffix.lower().lstrip(".")
    if kind not in {"txt", "srt", "vtt"}:
        raise ValueError(f"Unsupported transcript format: {kind!r}")
    if not language.strip():
        raise ValueError("Transcript language must be explicitly provided")
    TypeAdapter(HttpUrl).validate_python(original_url)
    content = (
        path.read_text(encoding=encoding).replace("\r\n", "\n").replace("\r", "\n")
    )
    if not content.strip():
        raise ValueError(f"Empty transcript file: {path}")
    if kind == "txt":
        paragraphs = re.split(r"\n[ \t]*\n", content.strip())
        segments = [
            TranscriptSegment(seg_id=idx, start=None, end=None, text=text.strip())
            for idx, text in enumerate(paragraphs)
            if text.strip()
        ]
        duration = None
    else:
        segments = _subtitle_segments(content, kind)
        # Last known cue end, not a claim about the complete lecture/media duration.
        duration = max(segment.end for segment in segments)
    return TranscriptDocument(
        source=str(path),
        language=language,
        duration=duration,
        segments=segments,
        text="\n\n".join(segment.text for segment in segments),
        provenance=TranscriptProvenance(
            transcript_source=(
                TranscriptSource.OFFICIAL_TRANSCRIPT
                if kind == "txt"
                else TranscriptSource.OFFICIAL_SUBTITLE
            ),
            source_url=original_url,
            source_file=str(path),
            language=language,
            media_format=kind,
        ),
    )


def import_txt(path: Path, **metadata) -> TranscriptDocument:
    return import_transcript(path, format="txt", **metadata)


def import_srt(path: Path, **metadata) -> TranscriptDocument:
    return import_transcript(path, format="srt", **metadata)


def import_vtt(path: Path, **metadata) -> TranscriptDocument:
    return import_transcript(path, format="vtt", **metadata)


def save_imported_transcript(document: TranscriptDocument, destination: Path) -> Path:
    """Explicit exclusive JSON creation; never overwrite an existing file/symlink.

    The parent directory must exist. Serialize/validate before opening the destination.
    """
    destination = Path(destination)
    if destination.suffix.lower() != ".json":
        raise ValueError("Normalized transcript destination must end in .json")
    payload = TranscriptDocument.model_validate(document.model_dump()).model_dump_json(
        indent=2
    )
    with destination.open("x", encoding="utf-8") as output:
        output.write(payload + "\n")
    return destination
