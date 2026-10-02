## consolidate_knowledge.py
# import
from __future__ import annotations

from typing import Literal

# from pydantic import BaseModel, Field

from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.config import folder_env_vars
from src.model_knowledge.data_knowledge import (
    ConsolidatedEvidence,
    ConsolidatedMathExpression,
    ConsolidatedStatement,
    ConsolidationStats,
    # KnowledgeSemanticType,
    # MathExpressionType,
    ConsolidatedKnowledgeDocument,  # LectureKnowledgeDocument,
    MathExpression,
    KnowledgeStatement,
    TranscriptKnowledgeDocument,
    # VisualCandidate,
)

from src.utils.path_helper import shorten_path
from src.utils.dict_helper import save_dict, load_dict
from src.utils.text_helper import (
    normalize_math_text,
    normalize_text_for_matching,
    text_similarity,
)


# ============================================================
# EVIDENCE HELPERS
# ============================================================


def build_statement_evidence(
    chunk_id: str,
    statement: KnowledgeStatement,
) -> ConsolidatedEvidence:

    return ConsolidatedEvidence(
        chunk_id=chunk_id,
        item_id=statement.statement_id,
        segment_ids=sorted(set(statement.segment_ids)),
        start=statement.start,
        end=statement.end,
        source=statement.source,
        llm_confidence=statement.llm_confidence,
    )


def build_formula_evidence(
    chunk_id: str,
    expression: MathExpression,
) -> ConsolidatedEvidence:

    return ConsolidatedEvidence(
        chunk_id=chunk_id,
        item_id=expression.expression_id,
        segment_ids=sorted(set(expression.segment_ids)),
        start=expression.start,
        end=expression.end,
        source=expression.source,
        llm_confidence=expression.llm_confidence,
    )


def evidence_overlaps(
    left: ConsolidatedEvidence,
    right: ConsolidatedEvidence,
) -> bool:
    """
    Only merge near-duplicates when their source evidence overlaps.

    This prevents a statement repeated several minutes later in the
    lecture from automatically being treated as the same occurrence.
    """

    left_segments = set(left.segment_ids)
    right_segments = set(right.segment_ids)

    if left_segments & right_segments:
        return True

    return left.start <= right.end and right.start <= left.end


# ============================================================
# REPRESENTATIVE SELECTION
# ============================================================


def statement_score(
    statement: KnowledgeStatement,
) -> tuple[float, int]:

    return (
        statement.llm_confidence or 0.0,
        len(statement.text),
    )


def expression_score(
    expression: MathExpression,
) -> tuple[int, float, int]:

    verified = int(expression.verification_status == "verified")

    return (
        verified,
        expression.llm_confidence or 0.0,
        len(expression.plain_text),
    )


def merged_verification_status(
    statuses: list[str | None],
) -> str | None:

    status_set = {status for status in statuses if status is not None}

    if "verified" in status_set:
        return "verified"

    if "pending" in status_set:
        return "pending"

    if status_set == {"rejected"}:
        return "rejected"

    return None


# ============================================================
# DUPLICATE MATCHING
# ============================================================


def find_statement_group(
    groups: list[dict],
    statement: KnowledgeStatement,
    evidence: ConsolidatedEvidence,
    threshold: float,
) -> dict | None:

    normalized = normalize_text_for_matching(statement.text)

    for group in groups:
        representative = group["representative"]

        if not any(
            evidence_overlaps(
                evidence,
                old_evidence,
            )
            for old_evidence in group["evidence"]
        ):
            continue

        representative_normalized = normalize_text_for_matching(representative.text)

        # Exact same statement:
        # merge even if semantic type differs.
        if normalized == representative_normalized:
            return group

        # Near-duplicates remain conservative.
        if representative.semantic_type != statement.semantic_type:
            continue

        group_similarity = max(
            text_similarity(
                normalized,
                normalize_text_for_matching(variant),
            )
            for variant in group["variants"]
        )

        if group_similarity >= threshold:
            return group

    return None


def expression_variants(
    expression: MathExpression,
) -> list[str]:

    values: list[str] = []

    if expression.latex:
        values.append(normalize_math_text(expression.latex))

    if expression.plain_text:
        values.append(normalize_math_text(expression.plain_text))

    return [value for value in values if value]


def find_expression_group(
    groups: list[dict],
    expression: MathExpression,
    evidence: ConsolidatedEvidence,
    threshold: float,
) -> dict | None:

    current_variants = expression_variants(expression)

    if not current_variants:
        return None

    for group in groups:
        if not any(
            evidence_overlaps(
                evidence,
                old_evidence,
            )
            for old_evidence in group["evidence"]
        ):
            continue

        existing_variants = group["normalized_variants"]

        best_similarity = max(
            text_similarity(
                current,
                existing,
            )
            for current in current_variants
            for existing in existing_variants
        )

        if best_similarity >= threshold:
            return group

    return None


# ============================================================
# MAIN CONSOLIDATION
# ============================================================


def consolidate_knowledge(
    document: TranscriptKnowledgeDocument,
    *,
    statement_similarity: float = 0.94,
    expression_similarity: float = 0.96,
) -> ConsolidatedKnowledgeDocument:

    statement_groups: list[dict] = []
    expression_groups: list[dict] = []

    topics: list[str] = []

    n_relevant_chunks = 0
    n_raw_statements = 0
    n_raw_formulas = 0

    # --------------------------------------------------------
    # COLLECT + GROUP
    # --------------------------------------------------------

    for chunk_result in document.chunks:
        analysis = chunk_result.analysis

        if not analysis.relevant:
            continue

        n_relevant_chunks += 1

        if analysis.topic and analysis.topic not in topics:
            topics.append(analysis.topic)

        extraction = chunk_result.extraction

        if extraction is None:
            continue

        chunk_id = extraction.chunk_id

        # ------------------------------
        # Statements
        # ------------------------------

        for statement in extraction.statements:
            if not statement.text.strip():
                continue

            n_raw_statements += 1

            evidence = build_statement_evidence(
                chunk_id=chunk_id,
                statement=statement,
            )

            group = find_statement_group(
                groups=statement_groups,
                statement=statement,
                evidence=evidence,
                threshold=statement_similarity,
            )

            if group is None:
                statement_groups.append(
                    {
                        "representative": statement.model_copy(deep=True),
                        "variants": [statement.text],
                        "evidence": [evidence],
                    }
                )

                continue

            if statement.text not in group["variants"]:
                group["variants"].append(statement.text)

            evidence_key = (
                evidence.chunk_id,
                evidence.item_id,
            )

            known_evidence = {
                (
                    item.chunk_id,
                    item.item_id,
                )
                for item in group["evidence"]
            }

            if evidence_key not in known_evidence:
                group["evidence"].append(evidence)

            if statement_score(statement) > statement_score(group["representative"]):
                group["representative"] = statement.model_copy(deep=True)

        # ------------------------------
        # Formulas / Expressions
        # ------------------------------

        for expression in extraction.formulas:
            if not expression.plain_text.strip():
                continue

            n_raw_formulas += 1

            evidence = build_formula_evidence(
                chunk_id=chunk_id,
                expression=expression,
            )

            group = find_expression_group(
                groups=expression_groups,
                expression=expression,
                evidence=evidence,
                threshold=expression_similarity,
            )

            if group is None:
                expression_groups.append(
                    {
                        "representative": expression.model_copy(deep=True),
                        "plain_variants": [expression.plain_text],
                        "latex_variants": (
                            [expression.latex] if expression.latex else []
                        ),
                        "normalized_variants": expression_variants(expression),
                        "evidence": [evidence],
                        "statuses": [expression.verification_status],
                        "reasons": (
                            [expression.verification_reason]
                            if expression.verification_reason
                            else []
                        ),
                    }
                )

                continue

            if expression.plain_text not in group["plain_variants"]:
                group["plain_variants"].append(expression.plain_text)

            if expression.latex and expression.latex not in group["latex_variants"]:
                group["latex_variants"].append(expression.latex)

            for normalized in expression_variants(expression):
                if normalized not in group["normalized_variants"]:
                    group["normalized_variants"].append(normalized)

            evidence_key = (
                evidence.chunk_id,
                evidence.item_id,
            )

            known_evidence = {
                (
                    item.chunk_id,
                    item.item_id,
                )
                for item in group["evidence"]
            }

            if evidence_key not in known_evidence:
                group["evidence"].append(evidence)

            group["statuses"].append(expression.verification_status)

            if (
                expression.verification_reason
                and expression.verification_reason not in group["reasons"]
            ):
                group["reasons"].append(expression.verification_reason)

            if expression_score(expression) > expression_score(group["representative"]):
                group["representative"] = expression.model_copy(deep=True)

    # --------------------------------------------------------
    # CREATE GLOBAL KNOWLEDGE ITEMS
    # --------------------------------------------------------

    statements: list[ConsolidatedStatement] = []

    for idx, group in enumerate(
        statement_groups,
        start=1,
    ):
        representative = group["representative"]

        statements.append(
            ConsolidatedStatement(
                statement_id=(f"KS{idx:04d}"),
                text=representative.text,
                semantic_type=(representative.semantic_type),
                topic=representative.topic,
                text_variants=group["variants"],
                evidence=group["evidence"],
                llm_confidence=(representative.llm_confidence),
            )
        )

    formulas: list[ConsolidatedMathExpression] = []

    for idx, group in enumerate(
        expression_groups,
        start=1,
    ):
        representative = group["representative"]

        formulas.append(
            ConsolidatedMathExpression(
                expression_id=(f"KF{idx:04d}"),
                name=representative.name,
                latex=representative.latex,
                plain_text=(representative.plain_text),
                expression_type=(representative.expression_type),
                text_variants=group["plain_variants"],
                latex_variants=group["latex_variants"],
                evidence=group["evidence"],
                verification_status=(merged_verification_status(group["statuses"])),
                verification_reasons=group["reasons"],
                llm_confidence=(representative.llm_confidence),
            )
        )

    stats = ConsolidationStats(
        chunks_total=len(document.chunks),
        chunks_relevant=(n_relevant_chunks),
        statements_raw=(n_raw_statements),
        statements_consolidated=(len(statements)),
        formulas_raw=(n_raw_formulas),
        formulas_consolidated=(len(formulas)),
    )

    return ConsolidatedKnowledgeDocument(
        source_id=document.source_id,
        transcript_url=(document.transcript_url),
        topics=topics,
        statements=statements,
        formulas=formulas,
        visual_candidates=(document.visual_candidates),
        stats=stats,
    )


if __name__ == "__main__":
    from src.core.memory_lecture import LectureContext
    from src.utils.llm_helper import configure_marvin

    app_session.logger = create_logger(name="test", file_name="test")

    dict_name = input("Enter name of context_file (no suffix): ")
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(
        path=dict_path,
        cls=LectureContext,
        # TranscriptDocument
    )

    configure_marvin(context)
    # =LectureContext(

    folder = folder_env_vars.data_lectures / "loviscach/mathe_vorkurs/knowledge"

    know_extracts = [ext for ext in folder.rglob("*.json")]

    print(
        f"Found {len(know_extracts)} knowledge_extracts in '{shorten_path(folder)}'. "
    )

    for f_path in know_extracts[:2]:
        extract = load_dict(f_path, cls=TranscriptKnowledgeDocument)
        deterministic = consolidate_knowledge(extract)

        semantic = consolidate_semantic_knowledge(
            document=deterministic,
            model_name="openai:gpt-5.4-mini",
            # context.llm_model,
        )

        save_name = f"/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/loviscach/know/{
            f_path.stem.replace('_extract', '_consol')
        }"
        save_dict(
            data=semantic.model_dump(mode="json"),
            path=save_name,
        )
        # print(f"Result '{f_path.stem}':\n", know)

        # try:

    # {f_path.stem}_cons"
    # save_dict(know_extracts, save_name)

    # except:
    #     pass
