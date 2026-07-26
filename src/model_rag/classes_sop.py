## classes_sop.py
# importencoding_for_model
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal  # Any,



class SOPType(Enum):
    GENERAL = "general"
    MANUFACTURING = "manufacturing"
    CLEANING = "cleaning"
    QC = "quality_control"


@dataclass
class SOPChapter:
    name: str
    kind: Literal["core", "support"] = "core"
    text: str = field(default_factory=str)
    order: int = field(default_factory=int)
    level: int = field(default_factory=int)
    required: bool = False
    condition: str | None = None
    depends_on: list = field(default_factory=list)
    knowledge_source: Literal[
                "retrieval",
                "template",
                "core_chapters",
                "existing_document",
                "human_system"
            ] = "retrieval"
    allow_subchapters: bool = False # =True,
    min_subchapters: int | None = None    # =3,
    max_subchapters: int | None = None   #=8,
    # llm_generation: bool


@dataclass
class ProposedSubchapter:
    order: int
    name: str
    fact_ids: list[str]


@dataclass
class CoreChapterPlan:
    chapter_name: str
    subchapters: list[ProposedSubchapter]


@dataclass
class SOPTemplate:
    sop_type: SOPType = field(default=SOPType.GENERAL)  # GENERAL     #  "general"
    version: str = "1.0"
    # core_chapter: List[SOPChapter] = field(default_factory=list)
    chapters: list[SOPChapter] = field(default_factory=list)
