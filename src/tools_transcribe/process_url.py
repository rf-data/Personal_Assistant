## process_url.py
# imports 
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.model_transcribe.data_transcribe import (
                                            DownloadResult,
                                            DownloadStrategy,
                                            TranscriptSource
                                            )
from src.tools_transcribe.extract_subtitle import download_subtitles
from src.tools_transcribe.extract_audio import download_audio


def process_youtube_video(context: AudioContext) -> DownloadResult:

    info = inspect_audio_file(context)

    if info is not None:
        manual = info.get("subtitles", {})
        automatic = info.get("automatic_captions", {})
    else:
        manual = {}
        automatic = {}

    if "de" in manual:
        paths = download_subtitles(
            context,
            automatic=False,
            )

        if paths:
            return DownloadResult(
                success=True,
                strategy=DownloadStrategy.SUBTITLES,
                transcript_source=TranscriptSource.MANUAL_SUBTITLE,
                paths=paths,
                )

    if "de" in automatic:
        paths = download_subtitles(
            context,
            automatic=True,
            )

        if paths:
            return DownloadResult(
                success=True,
                strategy=DownloadStrategy.SUBTITLES,
                transcript_source=TranscriptSource.AUTO_SUBTITLE,
                paths=paths,
            )

    files = download_audio(
        context,
        format_override="bestaudio[ext=m4a]/bestaudio/best",     # "bestaudio/best",
        )

    if files:
        return DownloadResult(
            success=True,
            strategy=DownloadStrategy.AUDIO_DEFAULT,
            transcript_source=TranscriptSource.WHISPER,
            paths=files,
        )

    files = download_audio(
        context,
        format_override="bestaudio/best",
        )

    if files:
        return DownloadResult(
            success=True,
            strategy=DownloadStrategy.AUDIO_FALLBACK,
            transcript_source=TranscriptSource.WHISPER,
            paths=files,
        )

    return DownloadResult(
        success=False,
        error="No usable subtitles or audio found.",
        )



def inspect_audio_file(context: AudioContext) -> dict | None: 
    if context.url is None:
        raise ValueError("No URL provided.")

    try: 
        with YoutubeDL({"skip_download": True}) as ydl:
            info = ydl.extract_info(context.url, download=False)

            if info is None:
                raise RuntimeError(
                        f"Could not extract info from {context.url}"
                        )

        return info

    except DownloadError as exc:
        app_session.logger.error(
                        "Audio download failed for %s: %s",
                        context.url,
                        exc,
                        )
        return None


def acquire_transcript_source(context: AudioContext) -> DownloadResult: 
    # list[Path]:
    # f_path: str = None, url: str = None) -> str:
    
    match context.source:

        case "local":
            app_session.logger.info("Start getting audio file from 'local' source")

            if context.local_path is None:
                raise ValueError(
                    "source='local' requires local_path."
                )
            
                # app_session.logger.error("[AUDIO_TRANSCRIPT] No local file path provided")
                #         raise 
            
            path = context.local_path

            if not path.exists():
                raise FileNotFoundError(path)

            return DownloadResult(
                        success=True,
                        transcript_source=TranscriptSource.WHISPER,
                        paths=[path],
                        )
            
        case "youtube" | "url": 
            app_session.logger.info("Start getting audio file from 'youtube' or other 'url' source")

            return process_youtube_video(context)
            # inspect_audio_file(context)
        # download_audio(context)
    
        case _:
            raise ValueError(
                f"Unsupported audio source: {context.source}"
                )
