## extract_resources.py
# import
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.core.memory import app_session
from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext

from src.utils.yt_helper import build_base_ydl_opts

from src.utils.path_helper import ensure_dir
# from src.utils.text_file_helper import save_text_file
# from src.utils.dict_helper import save_dict

# TODO: requests.Session()

# TODO:
# seen_urls: set[str] = set()

# for material in materials:
#     if material.source_url in seen_urls:
#         continue

#     seen_urls.add(material.source_url)


def download_lecture_resource(
    url: str,
    output_dir: str | Path,
    timeout: float = 30.0,
) -> Path:

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        url,
        stream=True,
        timeout=timeout,
        allow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    response.raise_for_status()

    filename = unquote(Path(urlparse(response.url).path).name)

    if not filename:
        raise ValueError(f"Could not determine filename from URL: {url}")

    output_path = output_dir / filename

    with output_path.open("wb") as f:
        for chunk in response.iter_content(
            chunk_size=1024 * 1024,
        ):
            if chunk:
                f.write(chunk)

    return output_path


def download_subtitles(
    context: AudioContext, automatic: bool, language: str
) -> list[Path]:
    # url: str, output_dir: str)

    save_folder = Path(folder_env_vars.data_audio)
    ensure_dir(save_folder)

    cfg = context.cfg_download

    # if cfg.no_playlist is True:
    outtmpl = str(
        save_folder
        / f"{cfg.playlist_name or 'single'}"
        / f"{'%(title)s.%(ext)s' if cfg.no_playlist is True else '%(playlist_index)03d_%(title)s.%(ext)s'}"
    )
    yt_opts = {
        **build_base_ydl_opts(context),
        "skip_download": True,
        "writesubtitles": not automatic,
        "writeautomaticsub": automatic,
        "subtitleslangs": [language],
        "subtitlesformat": "vtt",
        "noplaylist": cfg.no_playlist,
        "restrictfilenames": True,
        "quiet": cfg.quiet,
        "socket_timeout": cfg.socket_timeout,
        "retries": cfg.retries,
        "outtmpl": outtmpl,  # f"{output_dir}/%(id)s.%(ext)s",
    }

    try:
        with YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(context.url, download=True)

            if info is None:
                raise RuntimeError(f"Could not download subtitles from {context.url}")

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


def extract_section_no(value: str) -> str | None:
    match = re.search(
        r"(?<!\d)(\d{2})",
        value,
    )

    return match.group(1) if match else None


# def extract_semester(url: str) -> str | None:
#     match = re.search(
#         r"/(\d{4}(?:ws|ss))/",
#         url,
#         flags=re.IGNORECASE,
#     )

#     return match.group(1) if match else None
