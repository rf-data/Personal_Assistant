## config_knowledge.py
# imports
from pydantic import BaseModel, Field, field_validator
from src.core.config_transcribe import DownloadSettings, ScreenshotSettings


class KnowledgeSettings(BaseModel):
    know_extract_file: str = Field(default_factory=str)

    llm_model: str = Field(default_factory=str)
    visual_model: str = Field(
        min_length=1,
        default_factory=str,
    )

    transcript_names: list[str] = Field(default_factory=list)

    # @field_validator("visual_model")
    # @classmethod
    # def validate_visual_model(
    #     cls,
    #     value: str,
    #     visual_api_fallback: bool
    # ) -> str:
    #     value = value.strip()

    #     if (
    #         visual_api_fallback
    #         and not value
    #         ):
    #         raise ValueError("visual_model must not be empty.")

    #     return value

    # chunking
    target_duration: float = 45
    max_duration: float = 75
    overlap_segments: int = 2

    # visual enrichment
    visual_use_local_ocr: bool = True
    visual_formula_enrichment: bool = True
    visual_api_fallback: bool = True

    visual_batch_size: int = 10
    visual_batch_overlap: int = 1
    visual_context_margin: float = 5.0

    # configurations
    cfg_screenshot: ScreenshotSettings | None = None
    cfg_download: DownloadSettings | None = None
