## chunks_retrieval.py
# import
# from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


# @dataclass
class SourceReference(BaseModel):
    chunk_id: str
    source: str
    section: str
    page: int | None


# @dataclass
class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    source: str = ""
    section: str = ""
    page: int | None = None
    distance: float | None = None
    similarity: float | None = None
    metric: Literal["cosine"] = "cosine"
    metadata: dict[str, Any] = Field(default_factory=dict)


# @dataclass
class IngestedChunk(BaseModel):  # (RetrievedChunk):
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


# @dataclass
class IngestedFact(BaseModel):
    fact: str
    topic: str

    chunk_id: str
    source: str
    section: str
    page: int | None
    similarity: float | None  #


# @dataclass
class ConsolidatedFact(BaseModel):
    fact: str = Field(default_factory=str)
    fact_id: int = Field(default_factory=int)
    topic: str = Field(default_factory=str)
    sources: list[SourceReference] = Field(default_factory=list)
    quality: Literal["usable", "fragmentary", "irrelevant", "duplicate", "tba"] = "tba"


# @dataclass
class MergedFact(BaseModel):  # (BaseModel):
    fact: str


# @dataclass
class MergeDecision(BaseModel):  # (BaseModel):
    mergeable: bool
    fact: str | None


# @dataclass
class KnowledgePool(BaseModel):
    chunks: dict[str, IngestedChunk]
    facts: dict[str, list[ConsolidatedFact]]


# @dataclass
class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    n_results: int

    # cache_folder = "fact_extraction"
    # cache_key = make_cache_key(params={
    #                     "topic": [
    #                         item.topic
    #                         for item in cluster
    #                         ],
    #                     "n_facts": len(cluster),
    #                     "run_name": "cluster_merge_v1",
    #                     "prompt_version": "prompt_v1",
    #                     "model": "marvin_gpt-4o"
    #                     # topics_hash
    #                     })

    # cached = load_from_cache(key=cache_key, folder=cache_folder)

    # if cached is not None:
    #     app_session.logger.info("Loading cached facts (key=%s)", cache_key)
    #     print(f"Loading cached facts (key={cache_key})")
    #     return [
    #         IngestedFact(**chunk_dict)
    #         for chunk_dict in cached["facts"]
    #         ]

    # save_to_cache(
    #             key=cache_key,
    #             folder=cache_folder,
    #             data={"facts": [asdict(fact) for fact in fact_list]}
    #             )


# @dataclass
# class KnowledgeSummary:
#     content: str
#     sources: list[SourceReference]


# @dataclass
# class ChunkSummary:
#     content: str
#     sources: list[SourceReference]
