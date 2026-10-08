## yt_helper.py
# imports
from pathlib import Path

from src.core.memory import app_session
# from src.core.memory_transcribe import KnowledgeContext


def build_base_ydl_opts(context) -> dict:
    cfg = context.cfg_download

    opts = {
        "noplaylist": cfg.no_playlist,
        "socket_timeout": cfg.socket_timeout,
        "retries": cfg.retries,
        "extractor_args": {
            "youtube": {
                "player_client": [cfg.player_client],
            },
            "youtubepot-bgutilhttp": {
                "base_url": [cfg.pot_provider_url],
            },
        },
    }

    if cfg.cookie_file and cfg.cookie_file.exists():
        opts["cookiefile"] = str(cfg.cookie_file)

    return opts


def format_speed(speed: float | None) -> str:
    if not speed:
        return "N/A"

    if speed >= 1024**2:
        return f"{speed / 1024**2:.2f} MiB/s"

    if speed >= 1024:
        return f"{speed / 1024:.2f} KiB/s"

    return f"{speed:.0f} B/s"


def yt_progress_hook(d):
    status = d.get("status")

    filename = Path(d.get("filename", "unknown")).name

    if status == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        # speed = d.get("speed")
        # filename = Path(d["filename"]).name
        # percent = d.get("_percent_str", "").strip()
        speed = d.get("speed")  # .strip()

        percent = downloaded / total * 100 if total else None

        if percent is not None:
            percent_str = f"{percent:5.1f}%"
        else:
            percent_str = "N/A"

        speed_str = format_speed(speed)

        app_session.logger.info(
            "Downloading %s | %s | %s",
            filename,
            percent_str,
            speed_str,
        )

    elif status == "finished":
        filename = Path(d["filename"]).name
        app_session.logger.info(
            "Download finished: %s",
            filename,
        )


# class YTDLPLogger:
#     def debug(self, msg):
#         self._log(logging.DEBUG, msg)

#     def info(self, msg):
#         self._log(logging.INFO, msg)

#     def warning(self, msg):
#         self._log(logging.WARNING, msg)

#     def error(self, msg):
#         self._log(logging.ERROR, msg)

#     def _log(self, level, msg):
#         msg = shorten_yt_paths(msg)

#         app_session.logger.log(
#             level,
#             "yt-dlp | %s",
#             msg,
#         )
