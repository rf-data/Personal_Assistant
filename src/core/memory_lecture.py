## lecture_knowledge.py
# import
from pathlib import Path
from pydantic import BaseModel, Field, field_validator  # , ConfigDict

from src.core.config_transcribe import DownloadSettings, ScreenshotSettings
# from src.model_transcribe.data_transcribe import TranscriptDocument


class LectureContext(BaseModel):
    logger_name: str
    logger_f_name: str
    memory_f_name: str = Field(default_factory=str)
    # save_folder: str = Field(default_factory=str)
    provider: str = Field(default_factory=str)
    course_id: str = Field(default_factory=str)
    course_title: str = Field(default_factory=str)
    source_url: str = Field(default_factory=str)

    # lecture processing
    prepare_lecture: bool = False

    # Parsed HTML / RawDocument inputs
    # info_path: list[Path] = Field(default_factory=list)

    # Prepared *_lectures_new.json files
    # lecture_paths: list[Path] = Field(default_factory=list)
    extract_elements: list[str] = Field(default_factory=list)
    know_extract_file: str = Field(default_factory=str)

    llm_model: str = Field(default_factory=str)
    visual_model: str = Field(
        min_length=1,
        default_factory=str,
    )

    transcript_names: list[str] = Field(default_factory=list)

    @field_validator("visual_model")
    @classmethod
    def validate_visual_model(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError("visual_model must not be empty.")

        return value

    # TranscriptDocument

    # chunking
    target_duration: float = 45
    max_duration: float = 75
    overlap_segments: int = 2

    # knowledge imporvement
    visual_batch_size: int = 10
    visual_batch_overlap: int = 1
    visual_context_margin: float = 5.0

    # configurations
    cfg_screenshot: ScreenshotSettings | None = None
    cfg_download: DownloadSettings | None = None
