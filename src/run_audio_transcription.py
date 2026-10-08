## run_audio_transcription.py
# imports
from pathlib import Path
from datetime import datetime
# from yt_dlp.utils import DownloadError

from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.core.logger import create_logger
from src.model_transcribe.provider_transcript import get_transcription_provider
from src.tools_transcribe.process_subtitle import transcribe_files
# from src.model_transcribe.data_transcribe import (
#     DownloadResult,
#     TranscriptDocument,
#     TranscriptProvenance,
#     TranscriptSource,
# )

# from src.model_knowledge.data_resources import (
#     # LectureVideo,
#     LectureResource_old,
# )
from src.tools_transcribe.process_url import acquire_transcript_source
# from src.tools_transcribe.extract_subtitle import parse_subtitle


from src.utils.dict_helper import save_dict, load_dict
from src.utils.path_helper import shorten_path, ensure_dir


# ! TODO: change LectureResource_old -> new data models


def run_audio_transcription():

    dict_name = input("Enter name of context_file (no suffix): ")
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(dict_path, cls=AudioContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d_%H-%M")
    app_session.logger = create_logger(
        name=context.logger_name, file_name=context.logger_f_name
    )

    cache_dir = folder_env_vars.cache_dir
    memory_f_path = Path(cache_dir) / f"audio_processed/{context.memory_f_name}"

    if memory_f_path.exists():
        memory_file = load_dict(memory_f_path)

        audio_list = memory_file if isinstance(memory_file, dict) else {}

    else:
        ensure_dir(memory_f_path)
        audio_list: dict[str, dict] = {}

    audio_list_clean = {
        audio_id
        for audio_id, meta in audio_list.items()
        if meta.get("result") == "success"
    }

    app_session.logger.info(
        "Found %s already processed audio files in memory, %s successful",
        len(audio_list),
        len(audio_list_clean),
    )

    audio_transcription(context)


def audio_transcription(context: AudioContext) -> list[Path] | None:
    if app_session.logger is None:
        app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
        app_session.logger = create_logger(
            name="Audio_Transcript",
            file_name=f"{app_session.timestamp}_audio_transcript",
        )

    source_result = acquire_transcript_source(context)

    if not source_result.success:
        app_session.logger.error(
            "Transcript source acquisition failed: %s",
            source_result.error,
        )
        return None

    source_files = source_result.paths

    if not source_files or not any(src.exists() for src in source_files):
        app_session.logger.error("Source file download failed: %s", context.url)
        return None

    app_session.logger.info("Initializing transcription provider...")

    provider = get_transcription_provider(
        context=context,
        logger=app_session.logger,
    )

    app_session.logger.info("Transcription provider initialized.")

    return transcribe_files(source_result, provider, context)


if __name__ == "__main__":
    run_audio_transcription()
