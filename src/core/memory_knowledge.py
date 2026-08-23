## memory_knowledge.py
# import
# from pathlib import Path
from pydantic import BaseModel, Field   # , ConfigDict

from src.core.config_transcribe import (
                                DownloadSettings,
                                ScreenshotSettings
                                )
# from src.model_transcribe.data_transcribe import TranscriptDocument

class KnowledgeContext(BaseModel):
    logger_name: str
    logger_f_name: str
    memory_f_name: str = Field(default_factory=str)
    save_folder: str = Field(default_factory=str)
    know_extract_file: str = Field(default_factory=str)

    llm_model: str = Field(default_factory=str)

    transcript_names: list[str] = Field(default_factory=list)
    # TranscriptDocument

    # chunking
    target_duration: float = 45
    max_duration: float = 75
    overlap_segments: int = 2

    cfg_screenshot: ScreenshotSettings|None = None

    cfg_download: DownloadSettings|None = None
    