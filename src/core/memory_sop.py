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
    DownloadSettings,
    GeneralSettings,
    # NIRSettings,
    ParseSettings,
    TranscribeSettings,
)

# from chromadb.api.models.Collection import Collection

"""
LLMClient = Annotated[
                OpenAI,
                Field(discriminator="meta_type")
                ]
"""


# @dataclass
class LLMContext(BaseModel):
    name_logger: str
    name_logfile: str
    path_tracker_file: str
    temperature: float
    callbacks: list = Field(default_factory=["_track_costs"])
    # model: Literal["gpt-4o"]
    generation_model: Literal["openai/gpt-4o-mini"] = "openai/gpt-4o-mini"  # LiteLLM
    extraction_model: Literal["openai-chat:gpt-4o-mini"] = "openai-chat:gpt-4o-mini"


# @dataclass
class SOPGenContext(BaseModel):
    llm_context: LLMContext = Field(default_factory=LLMContext)
    title: str = Field(default_factory=str)
    topics: list = Field(default_factory=list)
    transformer_model: Literal[
        "all-MiniLM-L6-v2",
        "paraphrase-multilingual-MiniLM-L12-v2",
        "intfloat/multilingual-e5-base",
        None,
    ] = Field(default=None)
    similarity_threshold: float = Field(default_factory=float)
    q_doc_type: Literal[
        "SOP",
        # "SOP_specific",
        "record",
        "risk_analysis",
    ] = Field(default="SOP")
    work_mode: Literal["create", "revise", "merge"] = "create"
    template_id: int = Field(default_factory=int)
    style: Literal["gmp_oriented"] = "gmp_oriented"
    output_format: Literal["markdown"] = "markdown"
    where: str | None = None
    allowed_sources: Literal["retrieved_context_only"] = "retrieved_context_only"
    # # "merge", "split"
    chapter_mode: Literal["full", "chapterwise"] = "chapterwise"
    chapters: list[str] | str | Literal["n.a."] = "n.a."
    collection: list[str] = Field(default_factory=list)
    # | Collection
    # results: Dict = field(default_factory=dict)
    n_results: int = Field(default_factory=int)
    save_folder: str = Field(default_factory=str)
    save_name: str = Field(default_factory=str)
