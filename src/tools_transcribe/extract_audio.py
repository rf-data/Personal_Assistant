## extract_audio.py
# import
# import sounddevice as sd
# from pydub import AudioSegment
# from scipy.io import wavfile
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.core.config import parsing_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.utils.path_helper import ensure_dir
from src.utils.yt_helper import yt_progress_hook


def download_audio(
            context: AudioContext, 
            format_override: str | None = None,
            extra_ydl_opts: dict | None = None,
            ) -> list[Path]:
    # if context.url is None:
    #     raise ValueError("No URL provided.")
    
    save_folder = Path(parsing_env_vars.data_audio)
    ensure_dir(save_folder)

    cfg = context.cfg_download

    # if cfg.no_playlist is True:
    outtmpl = str(
                save_folder
                / f"{cfg.playlist_name or 'single'}"
                / f"{'%(title)s.%(ext)s' 
                     if cfg.no_playlist is True 
                     else '%(playlist_index)03d_%(title)s.%(ext)s'}"
                )
    # else:
    #     outtmpl = str(
    #                 save_folder
    #                 / f"{context.cfg_download.playlist_name or 'single'}"
    #                 / "%(playlist_index)03d_%(title)s.%(ext)s"
    #                 )

    # "playlist_items": cfg.playlist_items,
    ydl_opts = {
        "format": format_override or cfg.format,
        "outtmpl": outtmpl,
        "noplaylist": cfg.no_playlist,
        "restrictfilenames": True,          # -> no whitespaces in file names

        "noprogress": True,         # yt-dlp-eigene Progress-Ausgabe 
        "quiet": cfg.quiet,         # normale Info-Ausgaben
        "progress_hooks": [yt_progress_hook] if cfg.show_progress is True else [],
        # "logger": YTDLPLogger(),

        "playlist_items": cfg.playlist_items,
        "socket_timeout": cfg.socket_timeout,
        "retries": cfg.retries,
        "fragment_retries": cfg.fragment_retries,
        "continuedl": cfg.continue_download,
        # "ignoreerrors": cfg.ignore_errors,
        }

    if extra_ydl_opts:
        ydl_opts.update(extra_ydl_opts)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                            context.url, 
                            download=True
                            )

            if info is None:
                raise RuntimeError(
                            f"Could not extract media from {context.url}"
                        )
            
    except DownloadError as exc:
        app_session.logger.error(
                    "Audio/media download failed for %s: %s",
                    context.url,
                    exc,
                    )
        return []

    requested_downloads = info.get("requested_downloads", [])

    # if not filepath:
    #     raise RuntimeError(
    #         "yt-dlp returned no filepath after download"
    #     )

    if "entries" in info:
        downloaded_files = [
                Path(ydl.prepare_filename(entry))
                for entry in info["entries"]
                if entry is not None
            ]

    # Einzelvideo
    elif requested_downloads:
        filepath = requested_downloads[0].get("filepath")
            # downloaded_files = [Path(requested_downloads[0]["filepath"])]

        if not filepath:
            raise RuntimeError(
                        f"yt-dlp did not create an output file for {context.url}"
                        )

        if not Path(filepath).exists():
            raise FileNotFoundError(filepath)

        downloaded_files = [Path(filepath)]

    else:
        downloaded_files = [
                Path(ydl.prepare_filename(info))
            ]

    return downloaded_files



# strategies = [
    #     (
    #         DownloadStrategy.AUDIO_DEFAULT,
    #         {
    #             "format": "bestaudio[ext=m4a]/bestaudio/best",
    #         },
    #     ),
    #     (
    #         DownloadStrategy.AUDIO_FALLBACK,
    #         {
    #             "format": "bestaudio/best",
    #         },
    #     ),
    # ]



    # for strategy, audio_format in strategies:
    #     files = download_audio(
    #         context,
    #         format_override=audio_format,
    #         )

    #     if files: 
    #         return DownloadResult(
    #             success=True,
    #             strategy=strategy,
    #             path=files[0]
    #         )

    # # Audio nicht verfügbar → Subtitle-Fallback
    # if download_subtitles(url):
    #     return DownloadResult(
    #         success=True,
    #         strategy=DownloadStrategy.SUBTITLES,
    #     )

    # return DownloadResult(
    #     success=False,
    #     error="All download strategies failed.",
    # )


#     manual = info.get("subtitles", {})
#     automatic = info.get("automatic_captions", {})

#     if "de" in manual:
#         return download_subtitles(
#                             context,
#                             source=TranscriptSource.MANUAL_SUBTITLE,
#                             )

#     elif "de" in automatic:
#         return download_subtitles(
#                                 context,
#                                 source=TranscriptSource.AUTO_SUBTITLE,
#                                 )

#     else:
#         return download_audio(context)



    # return path

# def extract_audio_from_video(video_path: str, save_path):
#     # Pfad zu Ihrer aufgenommenen WebM-Videodatei
#     #  = "aufnahme.webm"

#     # Audio aus dem Video extrahieren
#     audio = AudioSegment.from_file(video_path, format="webm")

#     # Als reine MP3-Audiodatei lokal abspeichern
#     audio.export(save_path, format="mp3", bitrate="192k")

#     print("Konvertierung erfolgreich abgeschlossen!")
