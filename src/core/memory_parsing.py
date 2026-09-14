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
from tiktoken import Encoding  # , encoding_for_model

from src.core.config import (
    ChunkSettings,
    # DownloadSettings,
    GeneralSettings,
    # NIRSettings,
    ParseSettings,
    # TranscribeSettings
)


# @dataclass
class ParseContext(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    chunk_settings: ChunkSettings = Field(default_factory=ChunkSettings)
    encoder: Encoding | None = None  #  = encoding_for_model
    general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
    parse_settings: ParseSettings = Field(
        default_factory=ParseSettings  # _all
    )
    text_type: Literal[
        "txt", "md", "pdf", "json_nb", "wiki", "docx", "html", "url", None
    ] = Field(default=None)
    save_folder: str | Path = Field(default_factory=str)
    save_name: str | Path = Field(default_factory=str)
    doc_id: str = Field(default_factory=str)
    doc_kind: Literal["regulatory", "commentSOP"] = Field(default="regulatory")
    timestamp: datetime | str | None = Field(default=None)
    run_id: str = Field(default_factory=str)
    logger: ClassVar = logging.getLogger(__name__)
    header: dict = Field(default_factory=dict)
