## data_knowledge.py
# imports
from pydantic import BaseModel, Field
from typing import Literal 


# TODO: 
# class LectureBook(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None

# TODO: 
# class LectureChapter(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None


class LectureScript(BaseModel):
    title: str | None = None
    source_url: str
    section: str | None = None


class LectureVideo(BaseModel):
    title: str
    kind: Literal["foundation", "supplement"]   #  = "foundation"

    lecture_no: str | None = None
    topic: str | None = None
    section: str | None = None

    source_url: str
    youtube_url: str | None #  = None
    youtube_id: str | None  #  = None

    # duration: str | None = None
    duration: int | None = None


class LectureMaterial(BaseModel):
    title: str | None = None
    source_url: str
    section: str | None = None
    file_type: str | None = None


class LectureResources(BaseModel):
    videos: list[LectureVideo]
    scripts: list[LectureScript] 
    material: dict = Field(default_factory=dict)  # [str, LectureMaterial]
    other_links: dict[str, dict] = Field(default_factory=dict)

    

class LectureSection(BaseModel):
    title: str
    script_url: str | None = None
    videos: list[LectureVideo]


class LectureCourse(BaseModel):
    title: str
    source_url: str
    sections: list[LectureSection]


class TranscriptChunk(BaseModel):
    chunk_id: str

    segment_ids: list[int]

    start: float
    end: float

    text: str
    n_words: int

    previous_context: str | None = None
    next_context: str | None = None


class ExtractedKnowledge(BaseModel):
        chunk_id: str

        # entities: list[KnowledgeEntity]
        # relations: list[KnowledgeRelation]
        # formulas: list[MathExpression]
        # definition: list[str]

        domains: Literal["mathematics"] = "mathematics"
        knowledge_types: Literal[
                    "formula",
                    "law",
                    "theorem",
                    "concept",
                    "derivation",
                ] = "law"

        needs_visual_context: bool = False

        confidence: float | None = None


class KnowledgeEntity(BaseModel):
    entity_id: str  # ="math_cosine_rule",
    canonical_name: str # ="Cosinussatz",
    aliases: list = []
    #     "Cosinus-Satz",
    #     "Kosinussatz",
    # ],
    entity_type: Literal["theorem"] = "theorem"
    domain: Literal["mathematics"] = "mathematics"



class KnowledgeRelation(BaseModel):
    source_entity_id: str
    relation_type: str
    target_entity_id: str

    source_ids: list[str] = []
    segment_ids: list[int] = []

    confidence: float | None = None


class KnowledgeExtraction(BaseModel):
    entities: list[KnowledgeEntity]
    relations: list[KnowledgeRelation]

    # definitions: list[...]
    # formulas: list[...]
    # examples: list[...]

    summary: str | None = None

# class TranscriptKnowledge(BaseModel):
#     summary: str
#     concepts: list[str]
#     formulas: list[MathExpression]
#     laws: list[str]
#     examples: list[str]


class MathExpression(BaseModel):
    expression_id: str
    name: str | None = None

    latex: str
    plain_text: str

    kind: Literal[
        "formula",
        "identity",
        "rule",
        "definition",
        "derivation_step",
        "example",
    ]

    segment_ids: list[int]
    start: float
    end: float

    source: Literal[
        "transcript",
        "visual",
        "transcript+visual",
    ]

    confidence: float | None = None