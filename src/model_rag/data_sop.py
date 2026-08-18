## classes_sop.py
# importencoding_for_model
# from dataclasses import dataclass, field
from enum import Enum
from typing import Literal  # Any,

from pydantic import BaseModel, Field


class SOPType(Enum):
    GENERAL = "general"
    MANUFACTURING = "manufacturing"
    CLEANING = "cleaning"
    QC = "quality_control"


# @dataclass
class SOPChapter(BaseModel):
    name: str
    kind: Literal["core", "support"] = "core"
    text: str = Field(default_factory=str)
    order: int = Field(default_factory=int)
    level: int = Field(default_factory=int)
    required: bool = False
    condition: str | None = None
    depends_on: list = Field(default_factory=list)
    knowledge_source: Literal[
        "retrieval", "template", "core_chapters", "existing_document", "human_system"
    ] = "retrieval"
    allow_subchapters: bool = False  # =True,
    min_subchapters: int | None = None  # =3,
    max_subchapters: int | None = None  # =8,
    # llm_generation: bool


# @dataclass
# class FactForPlanning:  # (BaseModel):
#     fact_id: str
#     topic: str
#     fact: str


# @dataclass
class AssignedFact(BaseModel):
    fact_id: str
    fact_text: str
    source: str | None = None
    # topic: str | None = None
    # assigned_subchapter: str | None = None

    # @classmethod
    # def from_dict(cls, data: dict) -> "AssignedFact":
    #     return cls(**data)


class UnassignedFact(BaseModel):
    fact_id: str
    fact_text: str
    reason: str


class FactEvaluationItem(BaseModel):
    fact_id: str
    fact_text: str
    topic: str | None = None
    assigned_subchapter: str | None = None


# @dataclass
class ProposedSubchapter(BaseModel):
    order: int
    name: str
    rationale: str
    primary_facts: list[AssignedFact]
    referenced_facts: list[AssignedFact] = []

    # @classmethod
    # def from_dict(cls, data: dict) -> "ProposedSubchapter":
    #     return cls(
    #         order=data["order"],
    #         name=data["name"],
    #         rationale=data["rationale"],
    #         facts=[
    #             AssignedFact.from_dict(fact)
    #             for fact in data.get("facts", [])
    #         ],
    #     )


# @dataclass
class CoreChapterPlan(BaseModel):
    chapter_name: str
    subchapters: list[ProposedSubchapter]
    unassigned_facts: list[UnassignedFact] = Field(default_factory=list)
    # @classmethod
    # def from_dict(cls, data: dict) -> "CoreChapterPlan":
    #     return cls(
    #         chapter_name=data["chapter_name"],
    #         subchapters=[
    #             ProposedSubchapter.from_dict(subchapter)
    #             for subchapter in data.get("subchapters", [])
    #         ],
    #     )


class ChapterPlanEvaluation(BaseModel):
    chapter_name: str
    total_facts: int
    assigned_count: int
    unassigned_count: int
    unknown_count: int
    duplicate_count: int
    coverage_percent: float

    assigned: list[FactEvaluationItem] = Field(default_factory=list)
    unassigned: list[FactEvaluationItem] = Field(default_factory=list)
    unknown_fact_ids: list[str] = Field(default_factory=list)
    duplicate_fact_ids: list[str] = Field(default_factory=list)


# @dataclass
class SOPTemplate(BaseModel):
    sop_type: SOPType = Field(default=SOPType.GENERAL)  # GENERAL     #  "general"
    version: str = "1.0"
    # core_chapter: List[SOPChapter] = field(default_factory=list)
    chapters: list[SOPChapter] = Field(default_factory=list)
