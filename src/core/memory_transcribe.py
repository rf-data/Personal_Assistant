# memory.py
import logging
from logging import Logger
# from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Literal  # , Annotated

from pydantic import Field

# from openai import OpenAI
from tiktoken import Encoding       # , encoding_for_model

from src.core.config import (
    ChunkSettings,
    DownloadSettings,
    GeneralSettings,
    # NIRSettings,
    ParseSettings,
    TranscribeSettings
)


AudioSource = Literal[
    "local",
    "url",
    "youtube",
]

# @dataclass
class AudioContext(BaseModel):
    source: AudioSource = "local"

    url: str|None = None
    local_path: Path|None = None
    f_name: str|None = None

    model_transcribe: Literal[
                        "FasterWhisper",
                        "WhisperLive",
                        "Cloud_STT"
                        ] = "FasterWhisper"

    cfg_transcribe: TranscribeSettings = Field(
                default_factory=TranscribeSettings
                )

    cfg_download: DownloadSettings = Field(
                default_factory=DownloadSettings
                )

    save_file: str = Field(default_factory=str)

