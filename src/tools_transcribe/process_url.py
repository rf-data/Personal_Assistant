## process_url.py
# imports
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.model_transcribe.data_transcribe import (
    DownloadResult,
    DownloadStrategy,
    TranscriptSource,
)
from src.tools_transcribe.extract_subtitle import download_subtitles
from src.tools_transcribe.extract_audio import download_audio


def process_youtube_video(context: AudioContext) -> DownloadResult:

    info = inspect_yt_file(context)

    if info is not None:
        manual = info.get("subtitles", {})
        automatic = info.get("automatic_captions", {})
    else:
        manual = {}
        automatic = {}

    # --------------------------------------------------
    # 1. Manual subtitles
    # --------------------------------------------------
    lang = select_subtitle_language(
        manual,
        preferred_languages=("de", "en"),
    )
    if lang is not None:
        paths = download_subtitles(context, automatic=False, language=lang)

        if paths:
            return DownloadResult(
                success=True,
                strategy=DownloadStrategy.SUBTITLES,
                transcript_source=TranscriptSource.MANUAL_SUBTITLE,
                language=lang,
                paths=paths,
            )

    # --------------------------------------------------
    # 2. Automatic subtitles
    # --------------------------------------------------
    lang = select_subtitle_language(
        automatic,
        preferred_languages=("de", "en"),
    )
    if lang is not None:
        paths = download_subtitles(context, automatic=True, language=lang)

        if paths:
            return DownloadResult(
                success=True,
                strategy=DownloadStrategy.SUBTITLES,
                transcript_source=TranscriptSource.AUTO_SUBTITLE,
                paths=paths,
                language=lang,
            )

    if context.subtitle_only:
        return DownloadResult(
            success=False,
            error="No usable subtitles found. Skipped search for audio files.",
        )
    # --------------------------------------------------
    # 3. Preferred audio
    # --------------------------------------------------
    files = download_audio(
        context,
        format_override="bestaudio[ext=m4a]/bestaudio/best",
        extra_ydl_opts={
            # "cookiefile": str(cookie_file),
            "extractor_args": {
                "youtube": {
                    "player_client": ["default", "web_embedded"],
                },
            },
        },
    )

    if files:
        return DownloadResult(
            success=True,
            strategy=DownloadStrategy.AUDIO_DEFAULT,
            transcript_source=TranscriptSource.WHISPER,
            paths=files,
            media_format="bestaudio[ext=m4a]/bestaudio/best",
        )

    # --------------------------------------------------
    # 4. Smaller audio fallback
    # --------------------------------------------------
    files = download_audio(
        context,
        format_override="bestaudio[abr<=96]/bestaudio[abr<=128]/worstaudio",
        extra_ydl_opts={
            # "cookiefile": str(cookie_file),
            "extractor_args": {
                "youtube": {
                    "player_client": ["default", "web_embedded"],
                },
            },
        },
    )

    if files:
        return DownloadResult(
            success=True,
            strategy=DownloadStrategy.AUDIO_FALLBACK,
            transcript_source=TranscriptSource.WHISPER,
            paths=files,
        )

    # --------------------------------------------------
    # 5. Authenticated web fallback
    # --------------------------------------------------

    files = []

    cookie_file = context.cookie_file

    if cookie_file and cookie_file.exists():
        files = download_audio(
            context,
            format_override="18",
            extra_ydl_opts={
                # "cookiefile": str(cookie_file),
                "extractor_args": {
                    "youtube": {
                        "player_client": ["default", "web_embedded"],
                    },
                },
            },
        )

    if files:
        return DownloadResult(
            success=True,
            strategy=DownloadStrategy.AUDIO_WEB_FALLBACK,
            transcript_source=TranscriptSource.WHISPER,
            paths=files,
            media_format="18",
        )

    return DownloadResult(
        success=False,
        error="No usable subtitles or audio found.",
    )


def select_subtitle_language(
    subtitles: dict,
    preferred_languages: tuple[str, ...] = ("de", "en"),
) -> str | None:
    """
    Select the best available subtitle language.

    Priority:
        de
        de-*
        en
        en-*
    """

    available = subtitles.keys()

    for preferred in preferred_languages:
        # Exact match first
        if preferred in available:
            return preferred

        # Then variants, e.g. de-DE, en-US, en-GB
        variants = sorted(
            lang for lang in available if lang.startswith(f"{preferred}-")
        )

        if variants:
            return variants[0]

    return None


def inspect_yt_file(context: AudioContext) -> dict | None:
    if context.url is None:
        raise ValueError("No URL provided.")

    try:
        with YoutubeDL({"skip_download": True}) as ydl:
            info = ydl.extract_info(context.url, download=False)

            if info is None:
                raise RuntimeError(f"Could not extract info from {context.url}")

        return info

    except DownloadError as exc:
        app_session.logger.error(
            "Audio download failed for %s: %s",
            context.url,
            exc,
        )
        return None


# def process_local_file(context):


#     return DownloadResult(
#                     success=True,
#                     strategy=DownloadStrategy.SUBTITLES,
#                     transcript_source=TranscriptSource.MANUAL_SUBTITLE,
#                     language=lang,
#                     paths=paths,
#                 )


def acquire_transcript_source(context: AudioContext) -> DownloadResult:
    # list[Path]:
    # f_path: str = None, url: str = None) -> str:

    match context.source:
        case "local":
            app_session.logger.info("Start getting audio file from 'local' source")

            file_paths = context.local_path

            if file_paths is None:
                raise ValueError("source='local' requires local_path.")

                # app_session.logger.error("[AUDIO_TRANSCRIPT] No local file path provided")
                #         raise

            path_list: list = []

            for path in file_paths:
                path_list.append(Path(folder_env_vars.data_audio / path))

            # path_list = [Path("/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/test_900s.wav")]

            if not any(path.exists() for path in path_list):
                raise FileNotFoundError(path_list)

            # return process_local_file(context)
            return DownloadResult(
                success=True,
                strategy=None,
                transcript_source=TranscriptSource.WHISPER,
                language=None,
                paths=path_list,
            )

        case "youtube" | "url":
            app_session.logger.info(
                "Start getting audio file from 'youtube' or other 'url' source"
            )

            return process_youtube_video(context)
            # inspect_audio_file(context)
        # download_audio(context)

        case _:
            raise ValueError(f"Unsupported audio source: {context.source}")
