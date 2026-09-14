## data_knowledge.py
# imports
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

# ? TODO: implement "theorem", "lemma", "proof",  "corollary,
# ? "algorithm", "inequality", "function", "expression",
# ? "constraint", ""assumption"


class KnowledgeSemanticType(Enum):
    DEFINITION = (
        "definition",
        "Specifies the meaning of a term, concept, or mathematical object.",
        (
            "Use only when the content states what something is or means. "
            "Do not classify every statement about a concept as a definition."
            "Use only when the target chunk establishes what a term, concept, "
            "operation, or object means."
            "A property, consequence, explanation, or motivation of a concept"
            "is not a definition merely because it mentions the concept."
        ),
    )
    STATEMENT = (
        "statement",
        "A factual or mathematical claim about properties or relationships.",
        (
            "Use as the default for relevant claims that do not fit a more "
            "specific semantic category. Do not infer theorem status merely "
            "because a mathematical statement appears generally valid."
        ),
    )
    RULE = (
        "rule",
        # "A general procedure, calculation rule, or decision rule."
        "A general procedure for calculating, deciding, checking, or performing a task.",
        (
            "Use when the primary information describes what to do or how to "
            "perform a procedure. Do not use for statements that merely describe "
            "a property."
        ),
    )
    # THEOREM = (
    #     "theorem",
    #     "A general mathematical proposition that can in principle be proved.",
    #     "Do not use for ordinary mathematical observations or calculation procedures.",
    # )
    EXPLANATION = (
        "explanation",
        "An interpretation, justification, or intuitive explanation of other knowledge.",
        (
            "Use when the primary information explains why or how something "
            "works or provides an interpretation. Do not use for mere repetition "
            "of another statement."
        ),
    )
    EXAMPLE = (
        "example",
        # "A concrete instance used to illustrate general knowledge."
        "A concrete instance or application used to illustrate general knowledge.",
        (
            "Use for specific values, objects, situations, or applications. "
            "Do not use for general claims."
            "Use for a concrete instance that illustrates or applies general "
            "knowledge. "
            "Do not classify a general rule as an example merely because it"
            "mentions vectors, variables, or a hypothetical situation."
        ),
    )
    # FORMULA = (
    #     "formula",
    #     "A mathematical expression representing a relation or calculation.",
    # )
    # IDENTITY = (
    #     "identity",
    #     "An equality that holds for all admissible values of its variables.",
    # )
    DERIVATION_STEP = (
        "derivation_step",
        # "An individual mathematical or logical step within a derivation."
        "An individual logical or computational step within a derivation or proof.",
        (
            "Use only for an actual intermediate reasoning or calculation step. "
            "Do not use for a general calculation rule or final result."
        ),
    )

    def __init__(
        self,
        value: str,
        description: str,
        guidance: str | None = None,
    ):
        self._value_ = value
        self.description = description
        self.guidance = guidance

    @classmethod
    def prompt_description(cls) -> str:
        return "\n".join(
            f"""
- {item.value}:
  Description {item.description}
  Guidance: {item.guidance}
"""
            for item in cls
        )


class MathExpressionType(Enum):
    DERIVATION_STEP = (
        "derivation_step",
        (
            "A mathematical expression representing one intermediate "
            "step of a calculation or derivation."
        ),
        (
            "Use when the expression derives its meaning from being part "
            "of a sequence of transformations or calculations."
        ),
    )
    EQUATION = (
        "equation",
        (
            "An equality whose validity depends on particular unknown "
            "or given quantities."
        ),
        (
            "Use for equations that are solved, tested, or applied to a "
            "specific situation. Do not use for universally valid identities."
        ),
    )

    CALCULATION = (
        "calculation",
        "A concrete mathematical computation using specific values or objects.",
        (
            "Use for evaluated numerical or symbolic calculations. "
            "Do not use for general formulas or individual intermediate "
            "steps within a longer derivation."
        ),
    )

    FORMULA = (
        "formula",
        (
            "A mathematical expression representing a relationship, "
            "calculation rule, or mathematical statement."
        ),
        (
            "Use as the default category for relevant mathematical expressions "
            "when no more specific expression type applies."
        ),
    )
    IDENTITY = (
        "identity",
        "An equality that holds for all admissible values of its variables.",
        (
            "Use only when the context supports that the equality is generally "
            "valid. Do not classify an arbitrary equation as an identity."
        ),
    )

    def __init__(
        self,
        value: str,
        definition: str,
        guidance: str,
    ):
        self._value_ = value
        self.definition = definition
        self.guidance = guidance

    @classmethod
    def prompt_description(cls) -> str:
        return "\n".join(
            f"""
- {item.value}:
  Definition: {item.definition}
  Guidance: {item.guidance}
"""
            for item in cls
        )


class Domain(Enum):
    MATHEMATICS = "mathematics"
    COMPUTER_SCIENCE = "computer_science"
    CHEMISTRY = "chemistry"
    PHARMACY = "pharmacy"
    MEDICINE = "medicine"


##################################
# KNOWLEDGE_TYPES
##################################
class KnowledgeEntity(BaseModel):
    entity_id: str  # ="math_cosine_rule",
    canonical_name: str  # ="Cosinussatz",
    aliases: list = Field(default_factory=list)
    #     "Cosinus-Satz",
    #     "Kosinussatz",
    # ],
    entity_type: Literal["theorem"] = "theorem"
    domain: Literal["mathematics"] = "mathematics"


class KnowledgeRelation(BaseModel):
    source_entity_id: str
    relation_type: str
    target_entity_id: str

    source_ids: list[str] = Field(default_factory=list)
    segment_ids: list[int] = Field(default_factory=list)

    llm_confidence: float | None = None


# class KnowledgeExtraction(BaseModel):
#     entities: list[KnowledgeEntity]
#     relations: list[KnowledgeRelation]

#     # definitions: list[...]
#     # formulas: list[...]
#     # examples: list[...]

#     summary: str | None = None

# class TranscriptKnowledge(BaseModel):
#     summary: str
#     concepts: list[str]
#     formulas: list[MathExpression]
#     laws: list[str]
#     examples: list[str]


class ExtractedStatement(BaseModel):
    statement_id: str
    text: str
    semantic_type: KnowledgeSemanticType
    topic: str | None = None
    llm_confidence: float | None = None


class ExtractedMathExpression(BaseModel):
    expression_id: str
    name: str | None = None
    latex: str | None = None
    plain_text: str
    expression_type: MathExpressionType
    llm_confidence: float | None = None


class KnowledgeEvidence(BaseModel):
    segment_ids: list[int] = Field(default_factory=list)

    start: float
    end: float

    source: Literal[
        "transcript",
        "visual",
        "transcript+visual",
    ] = "transcript"

    llm_confidence: float | None = None


class KnowledgeStatement(KnowledgeEvidence):
    statement_id: str  # =item.statement_id,
    text: str  # =item.text,
    semantic_type: KnowledgeSemanticType  # =item.semantic_type,
    topic: str  # =item.topic,


class MathExpression(KnowledgeEvidence):
    expression_id: str
    name: str | None = None
    latex: str | None = None
    plain_text: str
    expression_type: MathExpressionType

    verification_status: (
        Literal[
            "pending",
            "verified",
            # "corrected",
            "rejected",
        ]
        | None
    ) = None
    verification_reason: str | None = None


class VisualCandidate(BaseModel):
    chunk_id: str
    segment_ids: list[int]
    start: float
    end: float
    reason: str | None = None

    # frame_times: list[float] = Field(default_factory=list)


class ChunkAnalysis(BaseModel):
    chunk_id: str

    relevant: bool

    domains: list[Domain] = Field(default_factory=list)

    knowledge_types: list[KnowledgeSemanticType] = Field(default_factory=list)
    math_expression_types: list[MathExpressionType] = Field(default_factory=list)

    topic: str | None = None

    needs_visual_context: bool = False
    visual_reason: str | None = None

    llm_confidence: float | None = None


class KnowledgeExtract(BaseModel):
    chunk_id: str

    entities: list[KnowledgeEntity] = Field(default_factory=list)
    relations: list[KnowledgeRelation] = Field(default_factory=list)

    statements: list[KnowledgeStatement] = Field(default_factory=list)
    formulas: list[MathExpression] = Field(default_factory=list)

    # definition: list[str] = Field(default_factory=list)
    # examples: list[str] = Field(default_factory=list)

    summary: str | None = None


class FrameTimestamp(BaseModel):
    source_time: float
    local_time: float


class ExtractedFrame(BaseModel):
    section_id: str
    path: Path

    source_time: float
    local_time: float = Field(default_factory=float)


class DownloadedVideoSection(BaseModel):
    section_id: str

    source_start: float
    source_end: float

    download_start: float
    download_end: float

    path: Path

    frame_times: list[FrameTimestamp] = Field(default_factory=list)
    frames: list[ExtractedFrame] = Field(default_factory=list)
    additional_frames: list[ExtractedFrame] = Field(default_factory=list)


class FrameSelectionResult(BaseModel):
    selected_frames: list[ExtractedFrame] = Field(default_factory=list)

    additional_frame_times: list[float] = Field(
        default_factory=list
        # FrameTimestamp
    )


class ChunkKnowledgeResult(BaseModel):
    analysis: ChunkAnalysis
    extraction: KnowledgeExtract | None = None


class TranscriptKnowledgeDocument(BaseModel):
    transcript_url: str
    source_id: str
    chunks: list[ChunkKnowledgeResult]
    visual_candidates: list[VisualCandidate]


class VisualAnalysisBatch(BaseModel):
    batch_id: str
    section_id: str

    source_start: float
    source_end: float

    frames: list[ExtractedFrame]

    visual_reasons: list[str] = Field(default_factory=list)

    transcript_statements: list[str] = Field(default_factory=list)
    transcript_formulas: list[str] = Field(default_factory=list)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ============================================================
# LLM OUTPUT MODELS
# ============================================================


class VisualExpressionLLM(StrictBaseModel):
    visual_expressions: str | None
    visual_labels: str | None

    visual_latex: str | None  # = None
    visual_plain_text: str

    ambiguous: bool  # = False
    ambiguity_reason: str | None  # = None

    llm_confidence: float
    source_times: list[float]


class VisualVerificationItemLLM(StrictBaseModel):
    transcript_plain_text: str | None
    transcript_latex: str | None

    visual_plain_text: str | None
    visual_latex: str | None

    status: Literal[
        "confirmed",
        # "corrected",
        # "rejected",
        "conflict",
        "new",
        "insufficient_evidence",
    ]

    evidence_type: (
        Literal[
            "direct_visual",
            "derived_from_visual",
        ]
        | None
    )

    llm_confidence: float
    reason: str | None
    source_times: list[float]


class VisualKnowledgeResultLLM(StrictBaseModel):
    expressions: list[VisualExpressionLLM]
    verifications: list[VisualVerificationItemLLM]
    unresolved_content: list[str]
    summary: str | None

    llm_confidence: float
    # reason: str | None
    # source_times: list[float]


class VisualExpression(KnowledgeEvidence):
    expression_id: str

    visual_labels: str | None
    visual_plain_text: str | None
    visual_latex: str | None

    ambiguous: bool = False
    ambiguity_reason: str | None = None

    section_id: str
    batch_id: str
    source_times: list[float] = Field(default_factory=list)

    source: Literal[
        "transcript",
        "visual",
        "transcript+visual",
    ] = "visual"


class VisualVerificationItem(KnowledgeEvidence):
    verification_id: str

    expression_id: str | None

    transcript_plain_text: str | None
    transcript_latex: str | None

    visual_plain_text: str | None
    visual_latex: str | None

    review_status: Literal[  # ! TODO: as EnumClass
        # "pending",
        # "auto_accepted",
        # "manual_review",
        # "manually_verified",
        "confirmed",
        # "corrected",
        "conflict",
        "rejected",
        "new",
        "insufficient_evidence",
    ]

    reason: str | None  # = None

    evidence_type: (
        Literal[
            "direct_visual",
            "derived_from_visual",
        ]
        | None
    )

    section_id: str
    batch_id: str
    source_times: list[float] = Field(default_factory=list)


class VisualKnowledgeResult(KnowledgeEvidence):
    batch_id: str
    section_id: str

    expressions: list[VisualExpression] = Field(default_factory=list)
    verifications: list[VisualVerificationItem] = Field(default_factory=list)
    unresolved_content: list[str] = Field(default_factory=list)

    summary: str | None = None


##################################
# CHUNKING / EXTRACTION
##################################
class TranscriptChunk(BaseModel):
    chunk_id: str

    segment_ids: list[int] = Field(default_factory=list)

    start: float
    end: float

    text: str
    n_words: int

    previous_context: str | None = None
    next_context: str | None = None

    # domains: Literal["mathematics"] = "mathematics"
    # knowledge_types: list[KnowledgeSemanticType] = Field(default_factory=list)

    # needs_visual_context: bool = False

    llm_confidence: float | None = None
