## process_subtitle.py
# import
import html
import re
from pathlib import Path

from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session

from src.model_transcribe.data_transcribe import (
    DownloadResult,
    TranscriptDocument,
    TranscriptProvenance,
    TranscriptSource,
    TranscriptSegment,
)

from src.utils.dict_helper import save_dict


def transcribe_files(
    source_result: DownloadResult, provider, context: AudioContext
) -> list[Path]:

    f_paths = source_result.paths
    n_files = len(f_paths)

    trans_all: list = []
    for idx, file in enumerate(f_paths, start=1):
        app_session.logger.info(
            "[File %s / %s] Start processing source file.", idx, n_files
        )

        transcript = provider.transcribe(file)

        if transcript is None:
            raise RuntimeError(f"No transcript generated for '{file}'")

        transcript = add_transcript_provenance(
            transcript=transcript,
            source_result=source_result,
            context=context,
            src_file=file,
        )

        trans_path = Path(f"{file.parent.parent}/transcripts/{file.name}")
        trans_all.append(trans_path)

        save_dict(
            data=transcript.model_dump(mode="json"),
            path=trans_path,
        )

    return trans_all


def add_transcript_provenance(
    transcript,
    source_result: DownloadResult,
    context: AudioContext,
    src_file: Path,
):
    transcript.provenance = TranscriptProvenance(
        transcript_source=source_result.transcript_source,
        download_strategy=source_result.strategy,
        source_url=context.url,
        source_file=str(src_file),
        language=source_result.language,
        media_format=source_result.media_format,
        transcription_provider=(
            "faster-whisper"
            if source_result.transcript_source == TranscriptSource.WHISPER
            else None
        ),
        transcription_model=(
            context.cfg_transcribe.model_size
            if source_result.transcript_source == TranscriptSource.WHISPER
            else None
        ),
    )

    return transcript


def parse_subtitle(
    f_path: Path,
    language: str = "de",
) -> list[Path]:
    # TranscriptDocument:

    if not f_path.exists():
        raise FileNotFoundError(f_path)

    if f_path.suffix.lower() != ".vtt":
        raise ValueError(f"Unsupported subtitle format: {f_path.suffix}")

    content = f_path.read_text(
        encoding="utf-8",
    )

    blocks = re.split(
        r"\n\s*\n",
        content.strip(),
    )

    segments: list[TranscriptSegment] = []
    text_parts: list[str] = []

    previous_text = ""
    duration = 0.0

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]

        if not lines:
            continue

        # WEBVTT header / metadata
        if lines[0].startswith("WEBVTT"):
            continue

        timestamp_idx = next(
            (idx for idx, line in enumerate(lines) if "-->" in line),
            None,
        )

        if timestamp_idx is None:
            continue

        match = _TIMESTAMP_RE.search(lines[timestamp_idx])

        if match is None:
            continue

        start = _timestamp_to_seconds(match.group("start"))
        end = _timestamp_to_seconds(match.group("end"))

        raw_text = " ".join(lines[timestamp_idx + 1 :])

        text = _clean_vtt_text(raw_text)

        if not text:
            continue

        text = _remove_prefix_overlap(
            previous_text,
            text,
        )

        if not text:
            continue

        segments.append(
            TranscriptSegment(
                seg_id=len(segments),
                start=start,
                end=end,
                text=text,
            )
        )

        text_parts.append(text)

        # Important:
        # use the complete original cue for overlap detection,
        # not only the newly extracted suffix.
        previous_text = _clean_vtt_text(raw_text)

        duration = max(
            duration,
            end,
        )

    if not segments:
        raise ValueError(f"No subtitle segments found in {f_path}")

    # text_final =
    # save_text_file(
    #         data=text_final,
    #         file_name=path.stem,
    #         folder="/home/robfra/0_Portfolio_Projekte/gmp_compliance/data"
    #         )

    transcript = TranscriptDocument(
        source=str(f_path),
        language=language,
        language_probability=None,
        duration=duration,
        duration_after_vad=None,
        runtime=None,
        realtime_factor=None,
        segments=segments,
        text="\n\n".join(text_parts),
    )

    trans_path = Path(f"{f_path.parent.parent}/transcripts/{f_path.name}_trans")
    save_dict(
        data=transcript.model_dump(mode="json"),
        path=trans_path,
    )
    return [trans_path]


###############################################

_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})"
    r"\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})"
)

_INLINE_TIMESTAMP_RE = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>")

_TAG_RE = re.compile(r"<[^>]+>")


def _timestamp_to_seconds(value: str) -> float:
    hours, minutes, seconds = value.split(":")

    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _clean_vtt_text(text: str) -> str:
    text = _INLINE_TIMESTAMP_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)

    return " ".join(text.split())


def _remove_prefix_overlap(
    previous: str,
    current: str,
) -> str:
    """
    Removes words from the beginning of `current` that are already
    present at the end of `previous`.

    Example:
        previous = "Kombinatorik nach den komplexen Zahlen"
        current = "Kombinatorik nach den komplexen Zahlen das nächste Thema"

    returns:
        "das nächste Thema"
    """
    previous_words = previous.split()
    current_words = current.split()

    max_overlap = min(
        len(previous_words),
        len(current_words),
    )

    for overlap in range(max_overlap, 0, -1):
        if previous_words[-overlap:] == current_words[:overlap]:
            return " ".join(current_words[overlap:])

    return current

    # video_id = info.get("id")

    # subtitle_files = list(
    #             save_folder.glob("*.de.vtt")
    #             )

    # after = set(save_folder.glob("*.vtt"))
    # new_files = list(after - before)

    # if not new_files:
    #     app_session.logger.error(
    #         "No subtitle file found after download: %s",
    #         context.url,
    #     )
    #     return []

    # return new_files
