## chunks_retrieval.py
# import
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
class IngestedChunk(RetrievedChunk):
    pass


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]
    n_results: int

