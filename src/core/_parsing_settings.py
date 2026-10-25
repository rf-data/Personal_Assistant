"""Shared field declarations for the two unversioned parsing contracts.

Public classes and nested factories stay in their historical modules so sibling
families retain independent Python/Pydantic identities. No settings, SDKs or IO.
Do not import these implementation bases as an application configuration API.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FileFields(BaseModel):
    save: list[Literal[False, "html", "info", "md", True, "txt"]] = [False]
    assemble: list[Literal["md", "txt"]] | None = None
    scrape_images: bool = False


class DOCXFields(BaseModel):
    tbl_text_mode: Literal["long", "brief"] = "brief"


class HTMLFields(BaseModel):
    apollo: bool = Field(default_factory=bool)
    parser: str = Field(default_factory=str)


class NotebookFields(BaseModel):
    parser: str = Field(default_factory=str)


class WikiFields(BaseModel):
    query: str | None = None
    query_time: str | None = None
    query_param: Literal["page_title", "page_id"] = Field(default="page_id")
    page_id: list[int] = Field(default_factory=list)
    page_title: list[str] = Field(default_factory=list)
    language: Literal["en", "de"] = Field(default="en")
    max_retries: int = Field(default=3)


class GeneralFileFields(BaseModel):
    extraction_tags: list[str] = Field(default_factory=list)


class PDFGeneralFields(BaseModel):
    y_gap_words: int = Field(default_factory=int)
    x_gap_words: int = Field(default_factory=int)
    width_thresh: float = Field(default_factory=float)
    y_gap_line: int = Field(default_factory=int)
    up_down_thresh: float = Field(default_factory=float)
    left_right_thresh: float = Field(default_factory=float)
    heading_threshold: int = Field(default_factory=int)
    foot_note_thresh: int = Field(default_factory=int)
    start_tol: int = Field(default_factory=int)


class WikiGeneralFields(BaseModel):
    header_referer: str = ""
    header_accept: str = ""


class ChunkFields(BaseModel):
    container_types: list = Field(default_factory=list)
    spacy_language: Literal["de_core_news_sm", None] = Field(default=None)
    max_tokens: int = Field(default_factory=int)
    overlap_sentences: int = Field(default_factory=int)
    batch_size: int = Field(default_factory=int)
    transformer_model: Literal[
        "all-MiniLM-L6-v2",
        "paraphrase-multilingual-MiniLM-L12-v2",
        "intfloat/multilingual-e5-base",
        None,
    ] = Field(default=None)
    model_config = ConfigDict(extra="forbid")


class GeneralFields(BaseModel):
    txt_elements: list[str] = Field(default_factory=list)
    md_elements: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="forbid")
