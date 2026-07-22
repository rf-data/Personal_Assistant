## chunks_retrieval.py
# import
from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source: str = ""
    section: str = ""
    page: int | None = None
    distance: float | None = None
    similarity: float | None = None
    metric: Literal["cosine"] = "cosine"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestedChunk: # (RetrievedChunk):
    chunk_id: str
    text: str
    # fact: str
    topic: str
    source: str
    section: str
    page: int | None
    similarity: float
    metric: Literal["cosine"] = "cosine"


# @dataclass
# class ExtractedFact:
#     fact: str
#     topic: str
#     source_chunk_id: str
#     source: str
#     page: int | None


class ExtractedFact(BaseModel):
    fact: str
    topic: str


@dataclass
class IngestedFact:
    fact: str
    topic: str

    chunk_id: str
    source: str
    section: str
    page: int | None
    similarity: float | None#


@dataclass
class SourceReference:
    chunk_id: str
    source: str
    section: str
    page: int | None


@dataclass
class ChunkSummary:
    content: str
    sources: list[SourceReference]


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]
    n_results: int
