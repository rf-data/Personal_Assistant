# memory_transcribe.py
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal

from pydantic import Field


from src.core.config_transcribe import (
    DownloadSettings,
    RecordingSettings,
    TranscribeSettings,
)


class AudioContext(BaseModel):
    source: Literal[
        "local",
        "url",
        "youtube",
    ] = "local"

    logger_name: str | None = None
    logger_f_name: str | None = None
    memory_f_name: str | None = None

    lecture_files: list = []

    url: str | None = None
    local_path: list[Path] | None = None
    f_name: str = Field(default_factory=str)

    subtitle_only: bool = False
    kind: list[Literal["foundation", "supplement"]] = ["foundation"]
    model_transcribe: Literal["FasterWhisper", "WhisperLive", "Cloud_STT"] = (
        "FasterWhisper"
    )

    cfg_transcribe: TranscribeSettings = Field(default_factory=TranscribeSettings)

    cfg_download: DownloadSettings = Field(default_factory=DownloadSettings)

    cfg_recording: RecordingSettings = Field(default_factory=RecordingSettings)

    save_file: str = Field(default_factory=str)
