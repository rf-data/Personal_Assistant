# import
from __future__ import annotations
import re
from copy import deepcopy
from pydantic import BaseModel, Field
from typing import Literal, Any

from src.model_knowledge.data_knowledge import (
    LectureKnowledgeDocument,
    # VisualAnalysisDocument
    VisualKnowledgeResult,
)

from src.utils.text_helper import (
    find_illegal_control_chars,
    remove_illegal_control_chars,
)
from src.utils.latex_helper import normalize_latex, validate_latex_basic


VisualProcessingStatus = Literal[
    "not_required",
    "processed",
    "unavailable",
]


KnowledgeType = Literal[
    "statement",
    "formula",
    "definition",
    "example",
    "rule",
    "concept",
]

EvidenceSource = Literal[
    "transcript",
    "visual",
    "ocr",
    "derived",
]

EvidenceStatus = Literal[
    "support",
    "conflict",
    "insufficient_evidence",
    "unverified",
]

EvidenceType = Literal[
    "direct_transcript",
    "direct_visual",
    "derived_from_visual",
    "contextual_inference",
    "ocr",
    "unknown",
]

KnowledgeStatus = Literal[
    "verified",
    "usable_with_warning",
    "requires_review",
    "rejected",
]


# EvidenceType = Literal[
#         "verified",
#         "usable_with_warning",
#         "requires_review",
#         "invalid"
# ]

ExpressionQuality = Literal[
    "verified",
    "usable_with_warning",
    "requires_review",
    "invalid",
]


class EvidenceItem(BaseModel):
    evidence_id: str

    source_type: EvidenceSource
    source_id: str | None = None

    section_id: str | None = None
    chunk_id: str | None = None
    batch_id: str | None = None

    start: float | None = None
    end: float | None = None

    text: str | None = None
    latex: str | None = None

    evidence_type: EvidenceType = "unknown"
    status: EvidenceStatus = "unverified"

    confidence: float | None = None

    reason: str | None = None


class CanonicalKnowledgeItem(BaseModel):
    knowledge_id: str

    kind: KnowledgeType

    canonical_text: str | None = None
    canonical_latex: str | None = None

    title: str | None = None

    evidence: list[EvidenceItem] = Field(default_factory=list)

    source_start: float | None = None
    source_end: float | None = None

    confidence: float | None = None

    status: KnowledgeStatus = "requires_review"

    needs_review: bool = False
    review_reason: str | None = None

    source_statement_ids: list[str] = Field(default_factory=list)

    source_expression_ids: list[str] = Field(default_factory=list)

    relations: list["KnowledgeRelation"] = Field(default_factory=list)


RelationType = Literal[
    "related_to",
    "derived_from",
    "uses",
    "requires",
    "example_of",
    "defines",
    "equivalent_to",
    "contrasts_with",
]


class KnowledgeRelation(BaseModel):
    relation_type: RelationType

    target_knowledge_id: str

    confidence: float | None = None

    evidence_ids: list[str] = Field(default_factory=list)


class CanonicalKnowledgeDocument(BaseModel):
    source_id: str

    knowledge_items: list[CanonicalKnowledgeItem] = Field(default_factory=list)

    unmatched_visual_evidence: list[EvidenceItem] = Field(default_factory=list)

    version: str = "canonical_v1"


def deduplicate_evidence(
    evidence: list[EvidenceItem],
) -> list[EvidenceItem]:

    unique = {}

    for item in evidence:
        key = (
            item.source_type,
            item.source_id,
            item.chunk_id,
            item.batch_id,
            item.start,
            item.end,
            item.text,
            item.latex,
        )

        unique.setdefault(
            key,
            item,
        )

    return list(unique.values())


INCOMPLETE_ENDINGS = (
    r"\cdot",
    "+",
    "-",
    "=",
    "/",
)


def looks_incomplete_latex(
    latex: str | None,
) -> bool:

    if not latex:
        return False

    cleaned = latex.strip()

    return any(cleaned.endswith(ending) for ending in INCOMPLETE_ENDINGS)


def initialize_canonical_knowledge(
    document,
) -> CanonicalKnowledgeDocument:

    items: list[CanonicalKnowledgeItem] = []

    for statement in document.statements:
        knowledge_id = make_stable_knowledge_id(
            source_id=document.source_id,
            source_object_id=(statement.statement_id),
            kind="statement",
        )

        items.append(
            canonical_from_statement(
                statement,
                knowledge_id=knowledge_id,
            )
        )

    for formula in document.formulas:
        knowledge_id = make_stable_knowledge_id(
            source_id=document.source_id,
            source_object_id=(formula.expression_id),
            kind="formula",
        )

        items.append(
            canonical_from_formula(
                formula,
                knowledge_id=knowledge_id,
            )
        )

    return CanonicalKnowledgeDocument(
        source_id=document.source_id,
        knowledge_items=items,
    )


def merge_visual_results(
    canonical: CanonicalKnowledgeDocument,
    visual_results: list,
) -> None:

    expression_lookup = build_expression_lookup(canonical.knowledge_items)

    for visual_result in visual_results:
        for verification in visual_result.verifications:
            expression_id = verification.expression_id

            if not expression_id:
                continue

            item = expression_lookup.get(expression_id)

            if item is None:
                continue

            apply_visual_verification(
                item,
                verification,
            )


def add_unmatched_visual_expressions(
    canonical: CanonicalKnowledgeDocument,
    visual_results: list,
) -> None:

    known_visual_ids = {
        evidence.source_id
        for item in canonical.knowledge_items
        for evidence in item.evidence
        if evidence.source_type == "visual"
    }

    for result in visual_results:
        for expression in result.expressions:
            if expression.expression_id in known_visual_ids:
                continue

            if expression.ambiguous:
                continue

            evidence = evidence_from_visual_expression(expression)

            # knowledge_id = (
            #     make_stable_knowledge_id(
            #         source_id=canonical.source_id,
            #         source_object_id=(
            #             expression.expression_id
            #         ),
            #         kind="formula",
            #     )
            # )

            canonical.unmatched_visual_evidence.append(evidence)
            #     EvidenceItem(
            #         knowledge_id=knowledge_id,
            #         kind="formula",

            #         canonical_text=(
            #             expression
            #             .visual_plain_text
            #         ),

            #         canonical_latex=(
            #             expression
            #             .visual_latex
            #         ),

            #         evidence=[
            #             evidence
            #         ],

            #         source_start=(
            #             expression.start
            #         ),

            #         source_end=(
            #             expression.end
            #         ),

            #         confidence=(
            #             expression
            #             .llm_confidence
            #         ),

            #         status=(
            #             "verified"
            #             if (
            #                 expression
            #                 .evidence_type
            #                 == "direct_visual"
            #             )
            #             else
            #             "usable_with_warning"
            #         ),
            #     )
            # )


def derive_item_confidence(
    item: CanonicalKnowledgeItem,
) -> float | None:

    supporting = [
        evidence.confidence
        for evidence in item.evidence
        if (evidence.status == "support" and evidence.confidence is not None)
    ]

    if not supporting:
        return None

    return max(supporting)


def validate_canonical_item(
    item: CanonicalKnowledgeItem,
) -> list[str]:

    issues: list[str] = []

    if not item.canonical_text and not item.canonical_latex:
        issues.append("missing_canonical_content")

    if not item.evidence:
        issues.append("missing_evidence")

    if item.status == "verified" and not any(
        evidence.status == "support" for evidence in item.evidence
    ):
        issues.append("verified_without_support")

    if item.status == "verified" and item.needs_review:
        issues.append("verified_but_needs_review")

    if item.status == "requires_review" and not item.needs_review:
        issues.append("requires_review_but_flag_false")

    if (
        item.source_start is not None
        and item.source_end is not None
        and item.source_start > item.source_end
    ):
        issues.append("invalid_source_time_range")

    if len({evidence.evidence_id for evidence in item.evidence}) != len(item.evidence):
        issues.append("duplicate_evidence_ids")

    semantic_keys = [
        (
            ev.source_type,
            ev.source_id,
            ev.chunk_id,
            ev.batch_id,
            ev.start,
            ev.end,
            ev.text,
            ev.latex,
        )
        for ev in item.evidence
    ]

    if len(set(semantic_keys)) != len(semantic_keys):
        issues.append("duplicate_evidence_content")

    return issues


def validate_canonical_document(
    document: CanonicalKnowledgeDocument,
) -> dict[str, list[str]]:

    problems = {}

    for item in document.knowledge_items:
        issues = validate_canonical_item(item)

        if issues:
            problems[item.knowledge_id] = issues

    return problems


def postprocess_visual_expression(
    expression: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(expression)

    raw_latex = result.get("visual_latex")

    # 1. Rohwert unbedingt behalten
    result["visual_latex_raw"] = raw_latex

    # 2. Bekannte kaputte Escape-Sequenzen reparieren
    repaired_latex, repairs = repair_broken_latex_escapes(raw_latex)

    # 3. Erst jetzt Control-Characters prüfen
    remaining_control_chars = find_illegal_control_chars(repaired_latex)
    # 4. Verbleibende Control-Characters entfernen
    cleaned_latex = remove_illegal_control_chars(repaired_latex)

    # 5. LaTeX normalisieren
    cleaned_latex = normalize_latex(cleaned_latex)

    # 6. Final validieren
    validation_issues = validate_latex_basic(cleaned_latex)

    if remaining_control_chars:
        validation_issues.append("unrepaired_control_characters")

    result["visual_latex"] = cleaned_latex

    # cleaned_latex = remove_illegal_control_chars(
    #     raw_latex
    # )

    # cleaned_latex = normalize_latex(
    #     cleaned_latex
    # )

    result["evidence_type"] = infer_evidence_type(result)

    result["postprocessing"] = {
        "latex_valid": len(validation_issues) == 0,
        "issues": validation_issues,
        "repairs": repairs,
        "latex_repaired": bool(repairs),
        "plain_text_fallback_available": has_plain_text_fallback(result),
    }

    result["quality"] = determine_expression_quality(result)

    result["postprocessing"]["plain_text_fallback_available"] = has_plain_text_fallback(
        result
    )

    return result


def has_plain_text_fallback(
    expression: dict[str, Any],
) -> bool:

    return bool(
        expression.get("visual_plain_text")
        and not expression.get("postprocessing", {}).get("latex_valid", True)
    )


def repair_broken_latex_escapes(
    text: str | None,
) -> tuple[str | None, list[str]]:
    """
    Repariert bekannte Fälle, bei denen LaTeX-Kommandos durch
    JSON/Python-Escape-Sequenzen beschädigt wurden.

    Gibt zurück:
        repaired_text
        repairs
    """
    if text is None:
        return None, []

    repaired = text
    repairs: list[str] = []

    replacements = {
        "\x08oldsymbol": r"\boldsymbol",
        "\x08ullet": r"\bullet",
    }

    for broken, fixed in replacements.items():
        if broken in repaired:
            repaired = repaired.replace(
                broken,
                fixed,
            )
            repairs.append(f"{repr(broken)} -> {fixed}")

    return repaired, repairs


def infer_evidence_type(
    expression: dict[str, Any],
) -> EvidenceType:
    """
    Bestimmt, wie unmittelbar eine Formel aus dem Bild stammt.

    Erwartet vorhandene Felder wie:
    - ambiguity_reason
    - ambiguous
    - evidence
    - source_description
    etc.

    Diese Funktion ist bewusst konservativ.
    """

    reason = (expression.get("ambiguity_reason") or "").lower()

    evidence = (expression.get("evidence") or "").lower()

    description = (expression.get("description") or "").lower()

    text = " ".join(
        [
            reason,
            evidence,
            description,
        ]
    )

    derived_keywords = [
        r"aus.*den.*termen",
        r"nicht.*als.*einzelne.*zeile",
        r"nicht.*vollständig.*geschrieben",
        r"aus.*beschrift",
        r"unter.*beschrift",
        r"terme.*beschrift",
        r"zusammengesetzt",
        r"derived from",
        r"not.*written.*as.*single.*line",
    ]

    inference_patterns = [
        r"\binferred\b",
        r"\bvermutlich\b",
        r"\bwahrscheinlich\b",
        r"context suggests",
        r"aus dem kontext",
    ]

    if any(
        re.search(pattern, text)
        for pattern in inference_patterns
        # keyword in text for keyword in inference_keywords
    ):
        return "contextual_inference"

    if any(re.search(pattern, text) for pattern in derived_keywords):
        return "derived_from_visual"

    if expression.get("ambiguous") is True:
        return "unknown"

    if expression.get("visual_latex") or expression.get("visual_plain_text"):
        return "direct_visual"

    return "unknown"


def postprocess_api_batch(
    batch: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(batch)

    expressions = result.get("expressions", [])

    result["expressions"] = [
        postprocess_visual_expression(expr) for expr in expressions
    ]

    return result


def postprocess_visual_enrichment(
    data: dict[str, Any],
) -> dict[str, Any]:

    result = deepcopy(data)

    api_results = result.get("api_results", [])

    result["api_results"] = [postprocess_api_batch(batch) for batch in api_results]

    return result


def determine_expression_quality(
    expression: dict[str, Any],
) -> str:

    issues = expression.get("postprocessing", {}).get("issues", [])

    if issues:
        return "requires_review"

    if expression.get("ambiguous"):
        return "requires_review"

    if looks_incomplete_latex(expression.get("visual_latex")):
        return "requires_review"

    evidence_type = expression.get("evidence_type")

    if evidence_type == "direct_visual":
        return "verified"

    if evidence_type in {"contextual_inference", "derived_from_visual", "unknown"}:
        return "usable_with_warning"

    return "requires_review"


def collect_problematic_expressions(
    data: dict[str, Any],
) -> list[dict[str, Any]]:

    problems = []

    for batch in data.get("api_results", []):
        batch_id = batch.get("batch_id") or batch.get("section_id")

        for expression in batch.get("expressions", []):
            postprocessing = expression.get("postprocessing", {})

            issues = postprocessing.get("issues", [])

            if issues:
                problems.append(
                    {
                        "batch_id": batch_id,
                        "expression_id": expression.get("expression_id"),
                        "visual_latex": expression.get("visual_latex"),
                        "issues": issues,
                    }
                )

    return problems


def evidence_from_statement(
    statement,
) -> list[EvidenceItem]:

    evidence_items: list[EvidenceItem] = []

    for idx, evidence in enumerate(statement.evidence):
        evidence_items.append(
            EvidenceItem(
                evidence_id=(f"EV_{statement.statement_id}_T_{idx:03d}"),
                source_type="transcript",
                source_id=statement.statement_id,
                chunk_id=getattr(
                    evidence,
                    "chunk_id",
                    None,
                ),
                start=getattr(
                    evidence,
                    "start",
                    None,
                ),
                end=getattr(
                    evidence,
                    "end",
                    None,
                ),
                text=statement.text,
                evidence_type=("direct_transcript"),
                status="support",
            )
        )

    return evidence_items


def evidence_from_formula(
    formula,
) -> list[EvidenceItem]:

    result: list[EvidenceItem] = []

    for idx, evidence in enumerate(formula.evidence):
        result.append(
            EvidenceItem(
                evidence_id=(f"EV_{formula.expression_id}_T_{idx:03d}"),
                source_type="transcript",
                source_id=formula.expression_id,
                chunk_id=getattr(
                    evidence,
                    "chunk_id",
                    None,
                ),
                start=getattr(
                    evidence,
                    "start",
                    None,
                ),
                end=getattr(
                    evidence,
                    "end",
                    None,
                ),
                text=formula.plain_text,
                latex=formula.latex,
                evidence_type=("direct_transcript"),
                status=(
                    "support"
                    if formula.verification_status == "verified"
                    else "unverified"
                ),
            )
        )

    return result


def evidence_from_visual_verification(
    verification,
) -> EvidenceItem:

    status_map = {
        "confirmed": "support",
        "conflict": "conflict",
        "insufficient_evidence": "insufficient_evidence",
    }

    return EvidenceItem(
        evidence_id=(f"EV_{verification.verification_id}"),
        source_type="visual",
        source_id=verification.expression_id,
        section_id=verification.section_id,
        batch_id=verification.batch_id,
        start=verification.start,
        end=verification.end,
        text=verification.visual_plain_text,
        latex=verification.visual_latex,
        evidence_type=(verification.evidence_type or "unknown"),
        status=status_map.get(
            verification.review_status,
            "unverified",
        ),
        confidence=(verification.llm_confidence),
        reason=verification.reason,
    )


def evidence_from_visual_expression(
    expression,
) -> EvidenceItem:

    return EvidenceItem(
        evidence_id=(f"EV_{expression.expression_id}"),
        source_type="visual",
        source_id=expression.expression_id,
        section_id=expression.section_id,
        batch_id=expression.batch_id,
        start=expression.start,
        end=expression.end,
        text=expression.visual_plain_text,
        latex=expression.visual_latex,
        evidence_type=(
            getattr(
                expression,
                "evidence_type",
                None,
            )
            or "unknown"
        ),
        status=("unverified" if expression.ambiguous else "support"),
        confidence=expression.llm_confidence,
        reason=expression.ambiguity_reason,
    )


def evidence_time_range(
    evidence: list[EvidenceItem],
) -> tuple[
    float | None,
    float | None,
]:

    starts = [item.start for item in evidence if item.start is not None]

    ends = [item.end for item in evidence if item.end is not None]

    return (
        min(starts) if starts else None,
        max(ends) if ends else None,
    )


def canonical_from_statement(
    statement,
    *,
    knowledge_id: str,
) -> CanonicalKnowledgeItem:

    evidence = evidence_from_statement(statement)

    start, end = evidence_time_range(evidence)

    return CanonicalKnowledgeItem(
        knowledge_id=knowledge_id,
        kind="statement",
        canonical_text=statement.text,
        evidence=evidence,
        source_start=start,
        source_end=end,
        confidence=getattr(
            statement,
            "confidence",
            None,
        ),
        status=("requires_review" if statement.needs_review else "usable_with_warning"),
        needs_review=statement.needs_review,
        review_reason=getattr(
            statement,
            "review_reason",
            None,
        ),
        source_statement_ids=[statement.statement_id],
    )


def canonical_from_formula(
    formula,
    *,
    knowledge_id: str,
) -> CanonicalKnowledgeItem:

    evidence = evidence_from_formula(formula)

    start, end = evidence_time_range(evidence)

    status = (
        "verified" if formula.verification_status == "verified" else "requires_review"
    )

    return CanonicalKnowledgeItem(
        knowledge_id=knowledge_id,
        kind="formula",
        canonical_text=formula.plain_text,
        canonical_latex=formula.latex,
        evidence=evidence,
        source_start=start,
        source_end=end,
        status=status,
        needs_review=(status == "requires_review"),
        source_expression_ids=[formula.expression_id],
    )


def apply_confirmed_visual_evidence(
    item: CanonicalKnowledgeItem,
    verification,
) -> None:

    evidence = evidence_from_visual_verification(verification)

    item.evidence.append(evidence)

    if verification.evidence_type == "direct_visual":
        item.status = "verified"

    elif verification.evidence_type in {
        "derived_from_visual",
        "contextual_inference",
    }:
        item.status = "usable_with_warning"

    else:
        item.status = "usable_with_warning"
    # item.status = "verified"
    item.needs_review = False
    item.review_reason = None

    return None


def apply_visual_conflict(
    item: CanonicalKnowledgeItem,
    verification,
    *,
    min_confidence: float = 0.85,
) -> None:

    confidence = verification.llm_confidence or 0.0

    evidence_type = verification.evidence_type or "unknown"

    trustworthy_visual = confidence >= min_confidence and evidence_type in {
        "direct_visual",
        "derived_from_visual",
    }

    visual_evidence = evidence_from_visual_verification(verification)

    if not trustworthy_visual:
        visual_evidence.status = "conflict"

        item.evidence.append(visual_evidence)

        item.status = "requires_review"
        item.needs_review = True
        item.review_reason = (
            "Transcript and visual evidence "
            "conflict, but visual evidence is "
            "not strong enough for automatic "
            "canonical replacement."
        )

        return

    # Transcript becomes conflicting evidence
    for evidence in item.evidence:
        if evidence.source_type == "transcript":
            evidence.status = "conflict"

    # Visual evidence supports the new canonical form
    visual_evidence.status = "support"

    item.evidence.append(visual_evidence)

    if verification.visual_plain_text:
        item.canonical_text = verification.visual_plain_text

    if verification.visual_latex:
        item.canonical_latex = verification.visual_latex

    if evidence_type == "direct_visual":
        item.status = "verified"
        item.needs_review = False
        item.review_reason = None

    else:
        item.status = "usable_with_warning"
        item.needs_review = False
        item.review_reason = (
            "Canonical value derived from "
            "visual evidence rather than "
            "directly written as a complete "
            "expression."
        )


def apply_insufficient_visual_evidence(
    item: CanonicalKnowledgeItem,
    verification,
) -> None:

    item.evidence.append(evidence_from_visual_verification(verification))

    if item.status == "usable_with_warning":
        item.needs_review = False

    if item.status == "requires_review":
        item.needs_review = True

    if item.review_reason is None:
        item.review_reason = (
            "Visual evidence was insufficient to independently verify this item."
        )


def apply_visual_verification(
    item: CanonicalKnowledgeItem,
    verification,
) -> None:

    status = verification.review_status

    if status == "confirmed":
        apply_confirmed_visual_evidence(
            item,
            verification,
        )

    elif status == "conflict":
        apply_visual_conflict(
            item,
            verification,
        )

    elif status == "insufficient_evidence":
        apply_insufficient_visual_evidence(
            item,
            verification,
        )

    else:
        item.evidence.append(evidence_from_visual_verification(verification))

        item.status = "requires_review"
        item.needs_review = True

        item.review_reason = f"Unknown visual verification status: {status}"


def build_expression_lookup(
    items: list[CanonicalKnowledgeItem],
) -> dict[
    str,
    CanonicalKnowledgeItem,
]:

    lookup = {}

    for item in items:
        for expression_id in item.source_expression_ids:
            lookup[expression_id] = item

    return lookup


def build_statement_lookup(
    items: list[CanonicalKnowledgeItem],
) -> dict[
    str,
    CanonicalKnowledgeItem,
]:

    lookup = {}

    for item in items:
        for statement_id in item.source_statement_ids:
            lookup[statement_id] = item

    return lookup


def make_knowledge_id(
    source_id: str,
    index: int,
) -> str:

    safe_source = source_id.replace(" ", "_").replace("/", "_")

    return f"K_{safe_source}_{index:05d}"


import hashlib


def make_stable_knowledge_id(
    *,
    source_id: str,
    source_object_id: str,
    kind: str,
) -> str:

    payload = f"{source_id}|{source_object_id}|{kind}"

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]

    return f"K_{digest}"


def build_canonical_knowledge(
    document,
    visual_results: list,
) -> CanonicalKnowledgeDocument:

    canonical = initialize_canonical_knowledge(document)

    merge_visual_results(
        canonical=canonical,
        visual_results=visual_results,
    )

    add_unmatched_visual_expressions(
        canonical=canonical,
        visual_results=visual_results,
    )

    for item in canonical.knowledge_items:
        item.evidence = deduplicate_evidence(item.evidence)
        item.confidence = derive_item_confidence(item)

    problems = validate_canonical_document(canonical)

    if problems:
        app_session.logger.warning(
            "Canonical knowledge validation found %d problematic items.",
            len(problems),
        )

    return canonical


if __name__ == "__main__":
    from pathlib import Path
    from src.core.config import folder_env_vars
    from src.core.memory import app_session
    from src.core.logger import create_logger
    from src.core.memory_lecture import LectureContext
    from src.utils.dict_helper import load_dict, save_dict

    from src.tools_lecture.prepare_loviscach import extract_media_id

    context_name = "lecture_compile"
    # input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(path=context_path, cls=LectureContext)

    app_session.logger = create_logger(
        name="visual_enrich",
        # context.logger_name,
        file_name=f"visual_enrich_{app_session.timestamp}",
        # context.logger_f_name
    )

    know_folder = (
        folder_env_vars.data_lectures
        / f"{context.provider}"
        / f"{context.course_id}"
        / "knowledge"
    )
    analysis_folder = know_folder / "visual_analysis"

    analysis = [
        file
        for file in analysis_folder.rglob("*.json")
        if not file.stem.startswith("post_")
    ]

    app_session.logger.info("Found %s RAW 'visual_analysis' files", len(analysis))

    # for f_path in analysis:
    #     data = load_dict(f_path)

    #     save_path = (
    #             analysis_folder
    #             / f"post_{f_path.name.removesuffix('.json')}"
    #             )

    #     result = postprocess_visual_enrichment(data)
    #     result["problems"] = collect_problematic_expressions(result)

    #     for idx, prob in enumerate(result["problems"]):
    #         app_session.logger.warning(
    #                         "[Problem #%s]: %s",
    #                         idx,
    #                         prob
    #                         )

    #     save_dict(result, save_path)

    visual_files = [file for file in analysis_folder.rglob("post_*_visual.json")]

    know_files = [file for file in know_folder.rglob("*know_consol.json")]

    app_session.logger.info(
        "Found %s knowledge files and %s visual results",
        len(know_files),
        len(visual_files),
    )
    # for know_path in sorted(know_files)[:5]:
    # for visual in visual_files:

    # source_name = know_path.name.removesuffix("_know_visual.json")

    # matching_visuals = [
    #                 path
    #                 for path in visual_files
    #                 if source_name in know_path.name
    #             ]

    yt_urls = load_dict(
        path="/home/robfra/0_Portfolio_Projekte/gmp_compliance/src/mathe_vorkurs_2013_urls.json"
    )

    visual_by_source: dict[str, Path] = {}

    for visual_path in sorted(visual_files):
        visual_data = load_dict(visual_path)

        source_id = visual_data.get("source_id")

        if source_id in visual_by_source:
            raise ValueError(f"Duplicate visual source_id: {source_id}")

        visual_by_source[source_id] = visual_path

    for know_path in sorted(know_files):
        document = load_dict(know_path, cls=LectureKnowledgeDocument)

        if document.transcript_url is None and context.course_id == "mathe_vorkurs":
            url_new = yt_urls.get(know_path.stem.split("_")[0], []).get("url", None)

            if not url_new:
                app_session.logger.error(
                    "No url available --> skipping visual enrichment of file '%s'",
                    know_path.stem,
                )
                continue

            document.transcript_url = url_new

        if not getattr(document, "media_id") or document.media_id is None:
            document.media_id = extract_media_id(document.transcript_url)
            # document.pop("source_id")
            #

        app_session.logger.info(
            ("Visual source check | source_id=%s | url=%s | video_id=%s"),
            document.source_id,
            document.transcript_url,
            document.media_id,
        )

        visual_path = visual_by_source.get(document.source_id)

        api_results = []

        if visual_path is not None:
            visual_data = load_dict(visual_path)

            assert document.source_id and document.transcript_url

            assert visual_data.get("source_id") == document.source_id
            # assert document.media_id == visual_data["source_id"]

            # assert document.transcript_url == visual_data.get("transcript_url")]

            # validate_source_identity(
            #     document=document,
            #     visual_data=visual_data,
            # )

            visual_results = [
                VisualKnowledgeResult.model_validate(item)
                for item in visual_data.get(
                    "api_results",
                    [],
                )
            ]

        else:
            app_session.logger.info(
                "No visual evidence for %s; "
                "building transcript-only "
                "canonical knowledge.",
                document.source_id,
            )

            visual_results = []

        canonical = build_canonical_knowledge(
            document=document,
            visual_results=visual_results,
        )

        save_dict(
            data=canonical.model_dump(mode="json"),
            path=(know_folder / (f"{document.source_id}_know_canonical")),
        )

        app_session.logger.info(
            "Canonical knowledge created: %s items | %s",
            len(canonical.knowledge_items),
            document.source_id,
        )
        # -> CanonicalKnowledgeDocument:
        # postprocess_visual_enrichment
