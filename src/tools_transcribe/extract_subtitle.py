## extract_subtitle.py
# import 
import html
import re
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.core.memory import app_session
from src.core.config import parsing_env_vars
from src.core.memory_transcribe import AudioContext
from src.model_transcribe.data_transcribe import (
                                        TranscriptDocument,
                                        TranscriptSegment,
                                        )
from src.utils.path_helper import ensure_dir
from src.utils.text_file_helper import save_text_file
from src.utils.dict_helper import save_dict


def download_subtitles(context: AudioContext, automatic: bool) -> list[Path]:
    # url: str, output_dir: str)

    save_folder = Path(parsing_env_vars.data_audio)
    ensure_dir(save_folder)
    
    cfg = context.cfg_download
    
    # if cfg.no_playlist is True:
    outtmpl = str(
                save_folder
                / f"{context.cfg_download.playlist_name or 'single'}"
                / f"{'%(title)s.%(ext)s' if cfg.no_playlist is True else '%(playlist_index)03d_%(title)s.%(ext)s'}"
                )
    opts = {
        "skip_download": True,
        "writesubtitles": not automatic,
        "writeautomaticsub": automatic,
        "subtitleslangs": ["de"],

        "subtitlesformat": "vtt",
        
        "noplaylist": cfg.no_playlist,
        "restrictfilenames": True,
        "quiet": cfg.quiet,
        
        "socket_timeout": cfg.socket_timeout,
        "retries": cfg.retries,
        "outtmpl": outtmpl,              # f"{output_dir}/%(id)s.%(ext)s",
    }

    try: 
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(context.url, download=True)

            if info is None:
                raise RuntimeError(
                        f"Could not download subtitles from {context.url}"
                        )


    except DownloadError as exc:
            app_session.logger.error(
                        "Subtitle download failed for %s: %s",
                        context.url,
                        exc,
                        )
            return []

    requested_subtitles = info.get("requested_subtitles", {})
    # print(requested_subtitles)

    subtitle = requested_subtitles.get("de", {})

    filepath = subtitle.get("filepath")

    if filepath and Path(filepath).exists():
        return [Path(filepath)]

    return []


def parse_subtitle(
            path: Path,
            language: str = "de",
        ) -> TranscriptDocument:

    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() != ".vtt":
        raise ValueError(
            f"Unsupported subtitle format: {path.suffix}"
        )

    content = path.read_text(
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
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if not lines:
            continue

        # WEBVTT header / metadata
        if lines[0].startswith("WEBVTT"):
            continue

        timestamp_idx = next(
            (
                idx
                for idx, line in enumerate(lines)
                if "-->" in line
            ),
            None,
        )

        if timestamp_idx is None:
            continue

        match = _TIMESTAMP_RE.search(
            lines[timestamp_idx]
        )

        if match is None:
            continue

        start = _timestamp_to_seconds(
            match.group("start")
        )
        end = _timestamp_to_seconds(
            match.group("end")
        )

        raw_text = " ".join(
            lines[timestamp_idx + 1:]
        )

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
        raise ValueError(
            f"No subtitle segments found in {path}"
        )

    # text_final = 
    # save_text_file(
    #         data=text_final, 
    #         file_name=path.stem, 
    #         folder="/home/robfra/0_Portfolio_Projekte/gmp_compliance/data"
    #         )

    trans_doc = TranscriptDocument(
                    source=str(path),
                    language=language,
                    language_probability=None,
                    duration=duration,
                    duration_after_vad=None,
                    runtime=None,
                    realtime_factor=None,
                    segments=segments,
                    text="\n\n".join(text_parts),
                    )

    return trans_doc


###############################################

_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})"
    r"\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})"
)

_INLINE_TIMESTAMP_RE = re.compile(
    r"<\d{2}:\d{2}:\d{2}\.\d{3}>"
)

_TAG_RE = re.compile(r"<[^>]+>")


def _timestamp_to_seconds(value: str) -> float:
    hours, minutes, seconds = value.split(":")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + float(seconds)
    )


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

