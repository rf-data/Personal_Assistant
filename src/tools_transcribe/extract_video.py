## extract_video.py
# import
from pathlib import Path
import statistics
import subprocess
from PIL import Image
import imagehash

import yt_dlp
from yt_dlp.utils import download_range_func

from src.core.retry import retry_download
from src.core.memory import app_session
from src.core.memory_lecture import LectureContext
from src.model_knowledge.data_knowledge import (
    DownloadedVideoSection,
    ExtractedFrame,
    FrameSelectionResult,
    FrameTimestamp,
)
from src.tools_knowledge.rebuild_knowledge import add_frame_timestamps
from src.core.config_transcribe import DownloadSettings
from src.utils.path_helper import ensure_dir, shorten_path


def expand_download_window(
    start: float,
    end: float,
    padding: float = 2.0,
) -> tuple[float, float]:

    return (
        max(0.0, start - padding),
        end + padding,
    )


VIDEO_SUFFIXES = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
}


def prepare_local_visual_sections(
    media_path: str | Path,
    download_windows: list[tuple[float, float]],
) -> list[DownloadedVideoSection]:

    media_path = Path(media_path)

    if not media_path.is_file():
        raise FileNotFoundError(media_path)

    if media_path.suffix.lower() not in VIDEO_SUFFIXES:
        raise ValueError(
            f"Expected a video file for visual verification, but got:\n{media_path}"
        )
    sections: list[DownloadedVideoSection] = []

    for idx, (
        start,
        end,
    ) in enumerate(download_windows):
        sections.append(
            DownloadedVideoSection(
                section_id=(f"section_{idx:03d}"),
                source_start=start,
                source_end=end,
                # Important:
                # timestamps are relative to
                # the complete local video.
                download_start=0.0,
                download_end=end,
                path=media_path,
            )
        )

    return sections


@retry_download
def download_sections_with_retry(**kwargs):
    return download_visual_sections(**kwargs)


def download_visual_sections(
    url: str,
    download_windows: list[tuple[float, float]],
    output_dir: str | Path,
    cfg_download: DownloadSettings,
) -> list[DownloadedVideoSection]:

    sections: list[DownloadedVideoSection] = []

    for idx, (start, end) in enumerate(download_windows):
        start_expand, end_expand = expand_download_window(
            start=start, end=end, padding=cfg_download.padding
        )

        path = download_video_section(
            url=url,
            start=start_expand,
            end=end_expand,
            output_dir=output_dir,
            section_id=f"section_{idx:03d}",
            cfg_download=cfg_download,
        )

        sections.append(
            DownloadedVideoSection(
                section_id=f"section_{idx:03d}",
                source_start=start,
                source_end=end,
                download_start=start_expand,
                download_end=end_expand,
                path=path,
            )
        )

    return sections


def download_video_section(
    url: str,
    start: float,
    end: float,
    output_dir: str | Path,
    section_id: str,
    cfg_download: DownloadSettings,
) -> Path:
    """
    Download one video section for later frame extraction.

    start/end are absolute timestamps in seconds relative to the source video.
    """

    ensure_dir(output_dir)
    output_template = (
        Path(output_dir)
        # / f"{cfg_download.playlist_name or 'single'}
        / f"{section_id}.%(ext)s"
    )

    app_session.logger.info(
        "section=%s | path=%s", section_id, shorten_path(output_template)
    )
    ydl_opts = {
        # Video only; audio is unnecessary for screenshots.
        "format": cfg_download.video_format,  # "bv/b",
        "outtmpl": str(output_template),
        # Equivalent to --download-sections.
        "download_ranges": download_range_func(
            [],
            [[start, end]],
        ),
        # More accurate boundaries, although this requires ffmpeg work.
        "force_keyframes_at_cuts": cfg_download.force_keyframes_at_cuts,  # True,
        "noplaylist": cfg_download.no_playlist,  # True,
        "quiet": cfg_download.quiet,  # False,
    }

    if cfg_download.cookie_file is not None:
        ydl_opts["cookiefile"] = str(cfg_download.cookie_file)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            url,
            download=True,
        )

        prepared_path = Path(ydl.prepare_filename(info))

    if prepared_path.exists():
        return prepared_path

    matches = list(Path(output_dir).glob(f"{section_id}.*"))

    if len(matches) == 1:
        return matches[0]

    raise FileNotFoundError(
        f"Could not determine downloaded file for section '{section_id}'."
    )


# def extract_frame(
#         section: DownloadedVideoSection,
#         frame_time: FrameTimestamp,
#         context: KnowledgeContext,
#         frame_id: str,
#         ) -> ExtractedFrame:

#     output_path = (
#         Path(context.save_folder)
#         / f"{context.cfg_download.playlist_name or 'single'}"
#         / "frames"
#         / (
#             f"{section.section_id}_{frame_id}"
#             f"_t{frame_time.source_time:.2f}."
#             f"{context.cfg_screenshot.image_format}"
#         )
#     )

#     ensure_dir(output_path)

#     cmd = [
#         "ffmpeg",
#         "-y",
#         "-ss",
#         str(frame_time.local_time),
#         "-i",
#         str(section.path),
#         "-frames:v",
#         "1",
#         str(output_path),
#         ]

#     try:
#         subprocess.run(
#             cmd,
#             check=True,
#             capture_output=True,
#             text=True,
#             )

#     except subprocess.CalledProcessError as exc:
#         app_session.logger.error(
#             "FFmpeg failed extracting frame "
#             "(section=%s, source_time=%.2f, local_time=%.2f):\n%s",
#             section.section_id,
#             frame_time.source_time,
#             frame_time.local_time,
#             exc.stderr,
#         )
#         raise

#     return ExtractedFrame(
#         section_id=section.section_id,
#         source_time=frame_time.source_time,
#         local_time=frame_time.local_time,
#         path=output_path,
#         )


def extract_frame(
    section_id: str,  # DownloadedVideoSection,
    src_path: Path,
    frame_time: FrameTimestamp,
    context: LectureContext,
    frame_id: str,
    section_name: str,
) -> ExtractedFrame | None:

    output_path = (
        # Path(context.save_folder)
        (context.lecture_root / "knowledge")  # src_path.parent
        # / f"{context.cfg_knowledge.cfg_download.playlist_name or 'single'}"
        / "frames"
        / section_name
        / (
            f"{section_id}_{frame_id}"
            f"_t{frame_time.source_time:.2f}."
            f"{context.cfg_knowledge.cfg_screenshot.image_format}"
        )
    )

    ensure_dir(output_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(frame_time.local_time),
        "-i",
        str(src_path),  # ection.path),
        "-frames:v",
        "1",
        str(output_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as exc:
        app_session.logger.error(
            "FFmpeg failed extracting frame "
            "(section=%s, source_time=%.2f, local_time=%.2f):\n%s",
            section_id,
            frame_time.source_time,
            frame_time.local_time,
            exc.stderr,
        )
        return None

    app_session.logger.info(
        "Frame extraction result | exists=%s | size=%s",
        output_path.exists(),
        (output_path.stat().st_size if output_path.exists() else None),
    )

    if not output_path.is_file():
        app_session.logger.warning(
            "Frame extraction produced no file: section=%s | time=%.2f | path=%s",
            section_id,
            frame_time.source_time,
            output_path,
        )

        return None

    return ExtractedFrame(
        section_id=section_id,
        source_time=frame_time.source_time,
        local_time=frame_time.local_time,
        path=output_path,
    )


def extract_section_frames(
    section: DownloadedVideoSection,
    context: LectureContext,
    section_name: str,
    # image_format: str = "png",
) -> DownloadedVideoSection:
    """
    Extract screenshots from a downloaded video section.

    Uses FrameTimestamp.local_time for seeking inside the local clip.
    """

    # output_dir = context.save_folder
    # Path(output_dir)  / section.section_id
    # ensure_dir(output_dir)

    section.frames = []

    for idx, frame_time in enumerate(section.frame_times):
        app_session.logger.info(
            (
                "Extract frame | "
                "section=%s | "
                "source=%.3f | "
                "download_start=%.3f | "
                "download_end=%.3f | "
                "local=%.3f | "
                # "output=%s"
            ),
            section.section_id,
            frame_time.source_time,
            section.download_start,
            section.download_end,
            frame_time.local_time,
            # output_path,
        )

        frame = extract_frame(
            section_id=section.section_id,
            src_path=section.path,
            frame_time=frame_time,
            context=context,
            frame_id=f"{idx:03d}_regular",
            section_name=section_name,
        )

        if frame:
            section.frames.append(frame)

    return section

    # output_path = (
    #     Path(output_dir)
    #     / f"{context.cfg_download.playlist_name or 'single'}"
    #     / "frames"
    #     / f"{section.section_id}_{idx:03d}"
    #       f"_t{frame_time.source_time:.2f}.
    #       {context.cfg_screenshot.image_format}"
    # )

    # cmd = [
    #     "ffmpeg",
    #     "-y",
    #     "-ss",
    #     str(frame_time.local_time),
    #     "-i",
    #     str(section.path),
    #     "-frames:v",
    #     "1",
    #     "-q:v",
    #     "2",
    #     str(output_path),
    # ]

    # try:
    #     subprocess.run(
    #         cmd,
    #         check=True,
    #         capture_output=True,
    #         text=True,
    #     )

    # except subprocess.CalledProcessError as exc:
    #     app_session.logger.error(
    #         "FFmpeg failed extracting frame "
    #         "(section=%s, source_time=%.2f, local_time=%.2f):\n%s",
    #         section.section_id,
    #         frame_time.source_time,
    #         frame_time.local_time,
    #         exc.stderr,
    #         )
    #     raise


def extract_all_frames(
    sections: list[DownloadedVideoSection], context: LectureContext, section_name: str
) -> list[DownloadedVideoSection]:

    for section in sections:
        add_frame_timestamps(
            section, interval=context.cfg_knowledge.cfg_screenshot.f_times_interval
        )

        extract_section_frames(
            section=section, context=context, section_name=section_name
        )

    return sections


def log_distance_stats(
    name: str,
    distances: list[int],
) -> None:

    if not distances:
        return

    app_session.logger.info(
        "%s | n=%d min=%d median=%.1f mean=%.1f max=%d",
        name,
        len(distances),
        min(distances),
        statistics.median(distances),
        statistics.mean(distances),
        max(distances),
    )


def select_distinct_frames(
    frames: list[ExtractedFrame],
    min_hash_distance: int = 5,
    max_hash_distance: int = 20,
    max_time_gap: float = 15.0,
) -> FrameSelectionResult:
    """
    Returns:
        selected_frames:
            Frames that should be kept.

        additional_frame_times:
            Absolute timestamps where an additional frame should
            be extracted because adjacent frames differ strongly.
    """

    valid_frames = []

    for frame in frames:
        path = Path(frame.path)

        if not path.is_file():
            app_session.logger.warning(
                "Frame file missing -> skipping: section=%s | time=%.2f | path=%s",
                frame.section_id,
                frame.source_time,
                path,
            )
            continue

        valid_frames.append(frame)

    if not valid_frames:
        app_session.logger.warning("No valid frame files available.")
        return FrameSelectionResult(
            selected_frames=[],
            additional_frame_times=[],
        )

    frames = sorted(
        valid_frames,
        key=lambda frame: frame.source_time,
    )

    selected = [frames[0]]
    additional_frame_times: list[float] = []
    # FrameTimestamp

    last_selected = frames[0]
    last_selected_hash = imagehash.phash(Image.open(last_selected.path))

    previous_frame = frames[0]
    # previous_hash = last_selected_hash
    with Image.open(frames[0].path) as img:
        previous_hash = imagehash.phash(img)

    distances_adjacent = []
    distances_selected = []

    for frame in frames[1:]:
        # current_hash = imagehash.phash(Image.open(frame.path))
        with Image.open(frame.path) as img:
            current_hash = imagehash.phash(img)

        # Compare adjacent sampled frames.
        adjacent_distance = current_hash - previous_hash
        distances_adjacent.append(adjacent_distance)

        if adjacent_distance >= max_hash_distance:
            mid_source = (previous_frame.source_time + frame.source_time) / 2

            # download_start = (
            #             frame.source_time
            #             - frame.local_time
            #             )
            # mid_local = (
            #         mid_source - download_start
            #         )

            additional_frame_times.append(
                round(mid_source, 2)
                # FrameTimestamp(
                #     source_time = round(mid_source, 2),
                #     local_time = round(mid_local, 2)
                #     )
            )

        # Compare against last frame that was actually retained.
        selected_distance = current_hash - last_selected_hash
        distances_selected.append(selected_distance)

        time_gap = frame.source_time - last_selected.source_time

        if selected_distance >= min_hash_distance or time_gap >= max_time_gap:
            selected.append(frame)

            last_selected = frame
            last_selected_hash = current_hash

        previous_frame = frame
        previous_hash = current_hash

    for name, distances in [
        ("distances adjacent", distances_adjacent),
        ("distances selected", distances_selected),
    ]:
        log_distance_stats(name, distances)

    return FrameSelectionResult(
        selected_frames=selected, additional_frame_times=additional_frame_times
    )


def extract_additional_frames(
    section: DownloadedVideoSection,
    add_frames: list[float],
    section_name: str,
    # FrameTimestamp
    context: LectureContext,
) -> list[ExtractedFrame]:

    new_frames: list[ExtractedFrame] = []

    existing_times = {round(frame.source_time, 3) for frame in section.frames}

    # new_source_times = [f.source_time for f in add_frames]

    for idx, source_time in enumerate(sorted(set(add_frames))):
        # sorted(set(additional_frame_times))
        # ):

        source_time = round(source_time, 3)

        if source_time in existing_times:
            continue

        # frame_time = source_time_to_frame_timestamp(
        #     section=section,
        #     source_time=source_time,
        # )

        local_time = source_time - section.download_start

        frame_time = FrameTimestamp(
            source_time=source_time, local_time=round(local_time, 3)
        )

        src_time = frame_time.local_time
        app_session.logger.info(
            (
                "Extract frame | "
                "section=%s | "
                "source=%.3f | "
                "download_start=%.3f | "
                "download_end=%.3f | "
                "local=%.3f | "
                # "output=%s"
            ),
            section.section_id,
            src_time,
            section.download_start,
            section.download_end,
            src_time - section.download_start,
            # output_path,
        )

        frame = extract_frame(
            section_id=section.section_id,
            src_path=section.path,
            frame_time=frame_time,
            context=context,
            frame_id=f"additional_{idx:03d}",
            section_name=section_name,
        )

        # defensive check
        if not frame:
            app_session.logger.info(
                "No additional frame #%s added from '%s'", idx, section.path
            )
            continue

        if not frame.path.is_file():
            raise FileNotFoundError(f"Additional frame was not created: {frame.path}")

        new_frames.append(frame)

    return new_frames
