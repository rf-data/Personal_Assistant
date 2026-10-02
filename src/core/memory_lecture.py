## lecture_knowledge.py
# import
from pathlib import Path
from pydantic import BaseModel, Field  # , ConfigDict
from typing import Literal

# from src.model_transcribe.data_transcribe import TranscriptDocument
from src.core.memory_parsing import PARSER_BACKEND
from src.core.config_knowledge import KnowledgeSettings


class LectureContext(BaseModel):
    logger_name: str
    logger_f_name: str

    lecture_root: Path = Field(default_factory=Path)
    memory_f_name: str = Field(default_factory=str)
    # save_folder: str = Field(default_factory=str)
    provider: str = Field(default_factory=str)
    course_id: str = Field(default_factory=str)
    course_title: str = Field(default_factory=str)
    source_url: str = Field(default_factory=str)

    # lecture processing
    parser_backend: PARSER_BACKEND | None = None
    prepare_lecture: Literal["from_info", "from_folder"] | None = None

    extract_elements: list[str] = Field(default_factory=list)

    # knowledge extraction + visual enrichment
    cfg_knowledge: KnowledgeSettings | None = None
