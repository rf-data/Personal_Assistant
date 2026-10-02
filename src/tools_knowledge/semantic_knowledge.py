## semantic_knowledge.py
# import
import json
# from typing import Literal

import marvin
# from pydantic import BaseModel, ConfigDict, Field

from src.agent.prompts.prompts_know_consolidate import (
    ENTITY_EXTRACTION_PROMPT,
    SEMANTIC_CONSOLIDATION_PROMPT,
)
from src.core.memory import app_session
from src.model_knowledge.data_knowledge import (
    CanonicalStatement,
    ConsolidatedEvidence,
    ConsolidatedKnowledgeDocument,
    ConsolidatedStatement,
    DiscardedStatement,
    Domain,
    EntityExtractionLLMResult,
    KnowledgeEntity,
    LectureEntityLLM,
    LectureKnowledgeDocument,
    SemanticBatchLLMResult,
    SemanticConsolidationStats,
)
from src.utils.general_helper import (
    hash_text,
    load_from_cache,
    make_cache_key,
    save_to_cache,
)
from src.utils.text_helper import normalize_label, normalize_text_for_matching


# ============================================================
# SEMANTIC CONSOLIDATION
# ============================================================


def get_statement_time_range(
    statement: ConsolidatedStatement,
) -> tuple[float, float]:

    if not statement.evidence:
        return (
            float("inf"),
            float("inf"),
        )

    start = min(item.start for item in statement.evidence)

    end = max(item.end for item in statement.evidence)

    return start, end


def build_semantic_statement_batches(
    statements: list[ConsolidatedStatement],
    *,
    max_statements: int = 16,
    max_span_seconds: float = 180.0,
) -> list[list[ConsolidatedStatement]]:

    ordered = sorted(
        statements,
        key=lambda item: get_statement_time_range(item)[0],
    )

    batches: list[list[ConsolidatedStatement]] = []

    current: list[ConsolidatedStatement] = []

    batch_start: float | None = None

    for statement in ordered:
        start, _ = get_statement_time_range(statement)

        if batch_start is None:
            batch_start = start

        exceeds_size = len(current) >= max_statements

        exceeds_span = (
            current
            and start != float("inf")
            and batch_start != float("inf")
            and (start - batch_start > max_span_seconds)
        )

        if current and (exceeds_size or exceeds_span):
            batches.append(current)

            current = []
            batch_start = start

        current.append(statement)

    if current:
        batches.append(current)

    return batches


def statement_to_llm_payload(
    statement: ConsolidatedStatement,
) -> dict:

    start, end = get_statement_time_range(statement)

    return {
        "statement_id": statement.statement_id,
        "text": statement.text,
        "semantic_type": statement.semantic_type.value,
        "topic": statement.topic,
        "start": (None if start == float("inf") else start),
        "end": (None if end == float("inf") else end),
    }


def consolidate_semantic_batch(
    statements: list[ConsolidatedStatement],
    *,
    batch_id: str,
    model_name: str,
    agent: marvin.Agent,
) -> SemanticBatchLLMResult:

    payload = [statement_to_llm_payload(statement) for statement in statements]

    serialized_input = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    prompt_hash = hash_text(SEMANTIC_CONSOLIDATION_PROMPT)

    input_hash = hash_text(serialized_input)

    cache_key = make_cache_key(
        params={
            "task": "semantic_consolidation_v1",
            "batch_id": batch_id,
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "model": model_name,
            "schema": "SemanticBatchLLMResult_v1",
        }
    )

    cached = load_from_cache(
        key=cache_key,
        folder=("knowledge_semantic_consolidation"),
        cls=SemanticBatchLLMResult,
    )

    if cached is not None:
        # if app_session.logger:
        app_session.logger.info(
            "CACHE HIT | semantic batch=%s",
            batch_id,
        )
        # app_session.logger.info(
        #         "Loading semantic "
        #         "consolidation cache "
        #         "(batch=%s)",
        #         batch_id,
        #     )

        return cached

    task = marvin.Task(
        instructions=(
            "Consolidate the supplied "
            "lecture statements according "
            "to your instructions."
        ),
        result_type=(SemanticBatchLLMResult),
        agents=[agent],
        context={
            "input_statements": payload,
        },
    )

    result = task.run()

    validate_semantic_batch_result(
        statements=statements,
        result=result,
    )

    save_to_cache(
        key=cache_key,
        folder=("knowledge_semantic_consolidation"),
        data=result.model_dump(mode="json"),
        metadata={
            "batch_id": batch_id,
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "model": model_name,
            "schema": "SemanticBatchLLMResult_v1",
        },
    )

    return result


def validate_semantic_batch_result(
    statements: list[ConsolidatedStatement],
    result: SemanticBatchLLMResult,
) -> None:

    allowed_ids = {statement.statement_id for statement in statements}

    returned_ids: set[str] = set()

    for item in result.canonical_statements:
        returned_ids.update(item.source_statement_ids)

    for item in result.discarded_statements:
        returned_ids.add(item.statement_id)

    invalid_ids = returned_ids - allowed_ids

    if invalid_ids:
        raise ValueError(
            f"Semantic consolidation invented statement IDs: {sorted(invalid_ids)}"
        )


def merge_statement_evidence(
    statements: list[ConsolidatedStatement],
) -> list[ConsolidatedEvidence]:

    result: list[ConsolidatedEvidence] = []

    known: set[tuple[str, str]] = set()

    for statement in statements:
        for evidence in statement.evidence:
            key = (
                evidence.chunk_id,
                evidence.item_id,
            )

            if key in known:
                continue

            known.add(key)

            result.append(evidence.model_copy(deep=True))

    result.sort(
        key=lambda item: (
            item.start,
            item.end,
        )
    )

    return result


def materialize_semantic_batch(
    statements: list[ConsolidatedStatement],
    result: SemanticBatchLLMResult,
) -> tuple[
    list[CanonicalStatement],
    list[DiscardedStatement],
]:

    statement_map = {statement.statement_id: statement for statement in statements}

    canonical: list[CanonicalStatement] = []

    used_ids: set[str] = set()

    # --------------------------------
    # Canonical statements
    # --------------------------------

    for item in result.canonical_statements:
        source_ids = list(dict.fromkeys(item.source_statement_ids))

        source_statements = [statement_map[statement_id] for statement_id in source_ids]

        used_ids.update(source_ids)

        canonical.append(
            CanonicalStatement(
                statement_id="",
                text=item.text.strip(),
                semantic_type=(item.semantic_type),
                topic=item.topic,
                needs_review=item.needs_review,
                review_reason=item.review_reason,
                source_statement_ids=(source_ids),
                evidence=(merge_statement_evidence(source_statements)),
                llm_confidence=(item.llm_confidence),
            )
        )

    # --------------------------------
    # Explicit discarded statements
    # --------------------------------

    discarded: list[DiscardedStatement] = []

    discarded_map = {
        item.statement_id: item.reason for item in result.discarded_statements
    }

    for statement_id, reason in discarded_map.items():
        # canonical wins if the LLM
        # accidentally lists the same
        # statement in both groups
        if statement_id in used_ids:
            continue

        statement = statement_map[statement_id]

        discarded.append(
            DiscardedStatement(
                source_statement_id=(statement_id),
                text=statement.text,
                reason=reason,
                evidence=[item.model_copy(deep=True) for item in statement.evidence],
            )
        )

        used_ids.add(statement_id)

    # --------------------------------
    # Safety fallback
    # --------------------------------

    for statement in statements:
        if statement.statement_id in used_ids:
            continue

        # If the LLM forgot the item,
        # preserve it instead of losing it.
        canonical.append(
            CanonicalStatement(
                statement_id="",
                text=statement.text,
                semantic_type=(statement.semantic_type),
                topic=statement.topic,
                source_statement_ids=[statement.statement_id],
                evidence=[item.model_copy(deep=True) for item in statement.evidence],
                llm_confidence=(statement.llm_confidence),
            )
        )

    return canonical, discarded


def merge_exact_canonical_statements(
    statements: list[CanonicalStatement],
) -> list[CanonicalStatement]:

    groups: dict[str, CanonicalStatement] = {}

    for statement in statements:
        key = normalize_text_for_matching(statement.text)

        if key not in groups:
            groups[key] = statement.model_copy(deep=True)

            continue

        target = groups[key]

        target.source_statement_ids = list(
            dict.fromkeys(
                (target.source_statement_ids + statement.source_statement_ids)
            )
        )

        target.evidence = merge_statement_evidence_from_canonical(
            [
                target,
                statement,
            ]
        )

        old_conf = target.llm_confidence or 0.0

        new_conf = statement.llm_confidence or 0.0

        if new_conf > old_conf:
            target.semantic_type = statement.semantic_type

            if statement.topic:
                target.topic = statement.topic

            target.llm_confidence = statement.llm_confidence

    result = list(groups.values())

    result.sort(
        key=lambda item: min(
            (evidence.start for evidence in item.evidence),
            default=float("inf"),
        )
    )

    for idx, item in enumerate(
        result,
        start=1,
    ):
        item.statement_id = f"CS{idx:04d}"

    return result


def merge_statement_evidence_from_canonical(
    statements: list[CanonicalStatement],
) -> list[ConsolidatedEvidence]:

    result: list[ConsolidatedEvidence] = []

    known: set[tuple[str, str]] = set()

    for statement in statements:
        for evidence in statement.evidence:
            key = (
                evidence.chunk_id,
                evidence.item_id,
            )

            if key in known:
                continue

            known.add(key)

            result.append(evidence.model_copy(deep=True))

    result.sort(
        key=lambda item: (
            item.start,
            item.end,
        )
    )

    return result


def canonical_statement_to_payload(
    statement: CanonicalStatement,
) -> dict:

    return {
        "statement_id": statement.statement_id,
        "text": statement.text,
        "semantic_type": statement.semantic_type.value,
        "topic": statement.topic,
    }


def extract_entity_batch(
    statements: list[CanonicalStatement],
    *,
    batch_id: str,
    model_name: str,
    agent: marvin.Agent,
) -> EntityExtractionLLMResult:

    payload = [canonical_statement_to_payload(statement) for statement in statements]

    serialized_input = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    prompt_hash = hash_text(ENTITY_EXTRACTION_PROMPT)

    input_hash = hash_text(serialized_input)

    cache_key = make_cache_key(
        params={
            "task": "lecture_entity_extraction_v1",
            "batch_id": batch_id,
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "model": model_name,
            "schema": "EntityExtractionLLMResult_v1",
        }
    )

    cached = load_from_cache(
        key=cache_key,
        folder=("knowledge_entity_extraction"),
        cls=EntityExtractionLLMResult,
    )

    if cached is not None:
        return cached

    task = marvin.Task(
        instructions=(
            "Extract the important "
            "lecture-level entities from "
            "the supplied canonical "
            "knowledge statements."
        ),
        result_type=(EntityExtractionLLMResult),
        agents=[agent],
        context={
            "canonical_statements": payload,
        },
    )

    result = task.run()

    allowed_ids = {statement.statement_id for statement in statements}

    returned_ids = {
        source_id
        for entity in result.entities
        for source_id in entity.source_statement_ids
    }

    invalid_ids = returned_ids - allowed_ids

    if invalid_ids:
        raise ValueError(
            f"Entity extraction invented statement IDs: {sorted(invalid_ids)}"
        )

    save_to_cache(
        key=cache_key,
        folder=("knowledge_entity_extraction"),
        data=result.model_dump(mode="json"),
        metadata={
            "batch_id": batch_id,
            "model": model_name,
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "schema": "EntityExtractionLLMResult_v1",
        },
    )

    return result


def merge_lecture_entities(
    entity_results: list[EntityExtractionLLMResult],
) -> list[KnowledgeEntity]:

    groups: dict[str, LectureEntityLLM] = {}

    for result in entity_results:
        for entity in result.entities:
            key = normalize_label(entity.canonical_name)

            if not key:
                continue

            if key not in groups:
                groups[key] = entity.model_copy(deep=True)

                continue

            target = groups[key]

            target.aliases = list(dict.fromkeys(target.aliases + entity.aliases))

            target.source_statement_ids = list(
                dict.fromkeys(
                    (target.source_statement_ids + entity.source_statement_ids)
                )
            )

            if entity.llm_confidence > target.llm_confidence:
                target.llm_confidence = entity.llm_confidence

                target.entity_type = entity.entity_type

    entities: list[KnowledgeEntity] = []

    for idx, item in enumerate(
        groups.values(),
        start=1,
    ):
        aliases = [
            alias
            for alias in item.aliases
            if (normalize_label(alias) != normalize_label(item.canonical_name))
        ]

        entities.append(
            KnowledgeEntity(
                entity_id=(f"KE{idx:04d}"),
                canonical_name=(item.canonical_name),
                aliases=list(dict.fromkeys(aliases)),
                entity_type=(item.entity_type),
                source_statement_ids=(item.source_statement_ids),
                llm_confidence=(item.llm_confidence),
                domain=Domain.MATHEMATICS,
            )
        )

    return entities


def consolidate_semantic_knowledge(
    document: ConsolidatedKnowledgeDocument,
    *,
    model_name: str,
    max_statements_per_batch: int = 16,
    max_batch_span_seconds: float = 180.0,
    entity_batch_size: int = 50,
) -> LectureKnowledgeDocument:

    if not document.statements:
        return LectureKnowledgeDocument(
            source_id=document.source_id,
            transcript_url=(document.transcript_url),
            formulas=document.formulas,
            visual_candidates=(document.visual_candidates),
            stats=(
                SemanticConsolidationStats(formulas_preserved=len(document.formulas))
            ),
        )

    # ========================================================
    # AGENTS
    # ========================================================

    semantic_agent = marvin.Agent(
        name="Knowledge Consolidator",
        model=model_name,
        instructions=(SEMANTIC_CONSOLIDATION_PROMPT),
    )

    entity_agent = marvin.Agent(
        name="Knowledge Entity Extractor",
        model=model_name,
        instructions=(ENTITY_EXTRACTION_PROMPT),
    )

    # ========================================================
    # STATEMENT BATCHES
    # ========================================================

    batches = build_semantic_statement_batches(
        document.statements,
        max_statements=(max_statements_per_batch),
        max_span_seconds=(max_batch_span_seconds),
    )

    canonical_all: list[CanonicalStatement] = []

    discarded_all: list[DiscardedStatement] = []

    for idx, batch in enumerate(
        batches,
        start=1,
    ):
        batch_id = f"semantic_{idx:04d}"

        if app_session.logger:
            app_session.logger.info(
                "Semantic consolidation %s (%d statements)",
                batch_id,
                len(batch),
            )

        llm_result = consolidate_semantic_batch(
            statements=batch,
            batch_id=batch_id,
            model_name=model_name,
            agent=semantic_agent,
        )

        canonical, discarded = materialize_semantic_batch(
            statements=batch,
            result=llm_result,
        )

        canonical_all.extend(canonical)

        discarded_all.extend(discarded)

    # Exact duplicates that arose
    # independently in different batches.
    canonical_all = merge_exact_canonical_statements(canonical_all)

    # ========================================================
    # ENTITY EXTRACTION
    # ========================================================

    entity_results: list[EntityExtractionLLMResult] = []

    for start in range(
        0,
        len(canonical_all),
        entity_batch_size,
    ):
        batch = canonical_all[start : start + entity_batch_size]

        batch_id = f"entities_{start // entity_batch_size + 1:04d}"

        result = extract_entity_batch(
            statements=batch,
            batch_id=batch_id,
            model_name=model_name,
            agent=entity_agent,
        )

        entity_results.append(result)

    entities = merge_lecture_entities(entity_results)

    # ========================================================
    # TOPICS
    # ========================================================

    topics: list[str] = []

    for statement in canonical_all:
        if statement.topic and statement.topic not in topics:
            topics.append(statement.topic)

    # ========================================================
    # RESULT
    # ========================================================

    stats = SemanticConsolidationStats(
        statements_input=len(document.statements),
        statements_canonical=len(canonical_all),
        statements_discarded=len(discarded_all),
        formulas_preserved=len(document.formulas),
        entities=len(entities),
        semantic_batches=len(batches),
        entity_batches=len(entity_results),
    )

    return LectureKnowledgeDocument(
        source_id=document.source_id,
        transcript_url=(document.transcript_url),
        topics=topics,
        statements=canonical_all,
        formulas=[item.model_copy(deep=True) for item in document.formulas],
        entities=entities,
        discarded_statements=(discarded_all),
        visual_candidates=[
            item.model_copy(deep=True) for item in document.visual_candidates
        ],
        stats=stats,
    )
