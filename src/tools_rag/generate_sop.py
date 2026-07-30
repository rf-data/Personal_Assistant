## generate_sop.py
# import
# from dataclasses import asdict
# from __future__ import annotations
import hashlib
import inspect
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import marvin

from src.core.config import parsing_env_vars
from src.core.memory import app_session
from src.model_rag.classes_chunk_fact import (
    ConsolidatedFact,
    IngestedChunk,
    KnowledgePool,
)
from src.model_rag.classes_sop import (
    ChapterPlanEvaluation,
    CoreChapterPlan,
    FactEvaluationItem,
    SOPTemplate,
)  # , FactForPlanning
from src.utils.dict_helper import append_json
from src.utils.general_helper import (
    load_from_cache,
    # load_env_vars,
    make_cache_key,
    save_to_cache,
)


def get_supporting_chunks(
    facts: list[ConsolidatedFact],
    chunks: dict[str, IngestedChunk],
) -> list[IngestedChunk]:

    chunk_ids = {source.chunk_id for fact in facts for source in fact.sources}

    return [chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks]


########


@marvin.fn
def plan_core_chapter(
    chapter_name: str,
    facts: list[ConsolidatedFact],
    min_subchapters: int,
    max_subchapters: int,
) -> CoreChapterPlan:
    """
    Create a logical subdivision for the core SOP chapter.

    Goal:
    Design a clear SOP structure by organizing the supplied facts into coherent
    operational subchapters. The objective is not merely to cluster similar facts,
    but to build a logical procedure that can later be expanded into a complete SOP.

    General rules:
    - Use only the supplied facts.
    - Do not invent procedures, activities, responsibilities, frequencies,
    acceptance criteria or regulatory requirements.
    - Create between min_subchapters and max_subchapters.
    - Prefer as few subchapters as necessary, but never at the expense of completeness.
    - Completeness is more important than minimizing the number of subchapters.
    - Think of each subchapter as one coherent operational activity,
    process step or procedural building block.
    - Group facts according to their operational purpose rather than wording.
    - Facts within one subchapter should describe the same operational activity.
    - Use concise German headings describing the activity.
    - Avoid generic headings such as "Sonstiges", "Allgemeines" or "Weitere Aspekte".
    - Order the subchapters according to the logical workflow of the procedure.

    Fact assignment:
    - Every supplied fact must receive exactly one PRIMARY assignment.
    - A fact may additionally be referenced by other subchapters if it is genuinely
    required there for completeness.
    - Use such additional references sparingly.
    - Do not omit facts merely because they appear redundant,
    highly specific, poorly phrased or only indirectly related.
    - Do not create artificial subchapters solely to accommodate a single isolated fact.
    - Instead, assign such facts to the closest related existing subchapter whenever reasonable.
    - Only place a fact into unassigned_facts when no reasonable assignment exists.

    Coverage requirements:
    - Every supplied fact_id must appear exactly once as a primary assignment.
    - Every supplied fact_id must therefore appear either
        - once as a primary fact in a subchapter, or
        - once in unassigned_facts.
    - A fact may additionally appear as a reference in other subchapters.
    - Do not silently omit facts.
    - Do not select representative examples.
    - Use the complete supplied fact set.

    Output requirements:
    For every subchapter provide:
    - order
    - name
    - rationale (1–2 sentences explaining why the facts belong together)
    - primary_facts
    - referenced_facts (optional)

    For every assigned fact provide:
    - fact_id
    - original fact text (or a very close one-sentence paraphrase without adding information)

    For every unassigned fact provide:
    - fact_id
    - original fact text
    - short reason why no reasonable assignment was possible.
    """

    # Coverage requirements:
    # - Every supplied fact_id must have exactly one primary assignment.
    # - A fact may additionally be referenced in other subchapters if it is essential there.
    # - Additional references must be used sparingly and only when they improve the logical completeness of the SOP.
    # """
    # """
    # Create a logical subdivision for the core SOP chapter.

    # Rules:
    # - Use only the supplied facts.
    # - Create between min_subchapters and max_subchapters.
    # - Prefer as few subchapters as necessary.
    # - Each subchapter should represent one coherent operational activity or process step.
    # - Group facts by operational purpose, not merely by wording.
    # - Facts within one subchapter should describe the same activity.
    # - Supplied facts can be assigned multiple times if there are relevant
    # - Do not omit a fact merely because it appears redundant, overly detailed, poorly phrased or only indirectly related.
    # - If a fact cannot reasonably be assigned, return it explicitly in unassigned_facts together with a short reason.
    # - Do not invent procedures, roles, frequencies or requirements.
    # - Do not create subchapters for isolated or irrelevant fragments.
    # - Use concise German operational headings describing the activity.
    # - Order subchapters according to the logical workflow of the procedure.
    # - For each subchapter provide a short rationale explaining the grouping.
    # - For each assigned fact return its fact_id together with the original fact text (or a very close one-sentence paraphrase without adding new information).

    # Coverage requirements:
    # - Every supplied fact_id must appear exactly once:
    # either in one subchapter or in unassigned_facts.
    # - Use unassigned_facts only when a fact is genuinely unrelated,
    # unusable or too fragmentary to support the chapter.
    # - For every unassigned fact, provide a concise reason.
    # - Do not omit facts silently.
    # """


def format_fact_ids(
    fact_ids: set[str] | list[str],
    *,
    max_items: int = 12,
) -> str:
    sorted_ids = sorted(fact_ids)

    if not sorted_ids:
        return "—"

    visible = sorted_ids[:max_items]
    result = ", ".join(visible)

    remaining = len(sorted_ids) - len(visible)
    if remaining > 0:
        result += f", … (+{remaining})"

    return result


def build_fact_lookup(knowledge_pool) -> dict[str, object]:
    return {
        fact.fact_id: fact
        for fact_list in knowledge_pool.facts.values()
        for fact in fact_list
    }


def filter_chapter_facts(plan: CoreChapterPlan, fact_lookup: dict):

    all_fact_ids = set(fact_lookup)

    assignment_lookup = {
        assigned_fact.fact_id: subchapter.name
        for subchapter in plan.subchapters
        for assigned_fact in subchapter.facts
    }

    assigned_sequence = assignment_lookup.keys()  # tolist()
    # [
    #     assigned_fact.fact_id
    #     for subchapter in plan.subchapters
    #     for assigned_fact in subchapter.facts
    #     ]

    assigned_fact_ids = set(assigned_sequence)

    # all_fact_ids = {
    #         fact.fact_id
    #         for facts in knowledge_pool.facts.values()
    #         for fact in facts
    #     }

    # assigned_fact_ids = {
    #         fact.fact_id
    #         for subchapter in plan.subchapters
    #         for fact in subchapter.facts
    #     }

    unassigned_ids = all_fact_ids - assigned_fact_ids
    unknown_ids = assigned_fact_ids - all_fact_ids

    duplicates = sorted(
        fact_id for fact_id, count in Counter(assigned_sequence).items() if count > 1
    )
    # [
    #         fact_id
    #         for fact_id, count in Counter(
    #             fact.fact_id
    #             for subchapter in plan.subchapters
    #             for fact in subchapter.facts
    #         ).items()
    #         if count > 1
    #     ]

    assigned_items = [
        FactEvaluationItem(
            fact_id=fact_id,
            fact_text=fact_lookup[fact_id].fact,
            topic=fact_lookup[fact_id].topic,
            assigned_subchapter=assignment_lookup[fact_id],
        )
        for fact_id in sorted(assigned_fact_ids & all_fact_ids)
    ]

    unassigned_items = [
        FactEvaluationItem(
            fact_id=fact_id,
            fact_text=fact_lookup[fact_id].fact,
            topic=fact_lookup[fact_id].topic,
        )
        for fact_id in sorted(unassigned_ids)
    ]

    return assigned_items, unassigned_items, unknown_ids, duplicates


def evaluate_chapter_plan(
    knowledge_pool, chapter_plan: dict[str, CoreChapterPlan]
) -> dict[str, ChapterPlanEvaluation]:

    fact_lookup = {
        fact.fact_id: fact
        for fact_list in knowledge_pool.facts.values()
        for fact in fact_list
    }

    all_fact_ids = set(fact_lookup)
    evaluations = {}

    for c_name, plan in chapter_plan.items():
        (assigned_items, unassigned_items, unknown_ids, duplicates) = (
            filter_chapter_facts(plan, fact_lookup)
        )

        assigned_ids = set([item.fact_id for item in assigned_items])
        unassigned_ids = set([item.fact_id for item in unassigned_items])

        n_facts = len(all_fact_ids)
        assigned_count = len(assigned_ids & all_fact_ids)
        coverage = round(assigned_count / n_facts * 100, 2) if n_facts else 0.0

        app_session.logger.info(
            "\n"
            "%s\n"
            "Chapter-Plan-Evaluation: %s\n"
            "%s\n"
            "Facts gesamt:       %3d\n"
            "Zugeordnet:         %3d  (%5.1f %%)\n"
            "Nicht zugeordnet:   %3d\n"
            "Unbekannt:          %3d\n"
            "Mehrfach verwendet: %3d\n"
            "\n"
            "Nicht zugeordnet:\n"
            "%s\n"
            "%s",
            "═" * 72,
            c_name,
            "─" * 72,
            n_facts,
            assigned_count,
            coverage,
            len(unassigned_ids),
            len(unknown_ids),
            len(duplicates),
            format_fact_ids(unassigned_ids),
            "═" * 72,
        )
        # "Assigned facts (n=%s):\n-> %s\n"
        # "Unassigned facts (n=%s):\n-> %s\n"
        # "Unknown facts (n=%s):\n-> %s\n"
        # "Multiple used facts (n=%s):\n-> %s\n",
        # '='*15,
        # c_name.upper(),
        # '='*15,
        # len(assigned_fact_ids),
        # assigned_fact_ids,
        # len(unassigned),
        # unassigned,
        # len(unknown),
        # unknown,
        # len(duplicates),
        # duplicates
        # )

        evaluation = ChapterPlanEvaluation(
            chapter_name=c_name,
            total_facts=n_facts,
            assigned_count=assigned_count,
            unassigned_count=len(unassigned_ids),
            unknown_count=len(unknown_ids),
            duplicate_count=len(duplicates),
            coverage_percent=coverage,
            assigned=assigned_items,
            unassigned=unassigned_items,
            unknown_fact_ids=sorted(unknown_ids),
            duplicate_fact_ids=duplicates,
        )
        evaluations[c_name] = evaluation

    return evaluations


#                   "Number of  and non-unique facts:\t %s | %s",


def save_prompt(fn: Callable, prompt: str | None = None) -> None:
    """
    Save a prompt or the docstring of a prompt function.
    """

    prompt_text = prompt if prompt is not None else inspect.getdoc(fn)

    # elif fn is not None:
    save_path = Path(parsing_env_vars.data_dir) / "prompts" / f"prompts_{fn.__name__}"

    # with open(save_path, "a", encoding="utf-8") as f:
    prompt_data = {
        "prompt": prompt_text,
        "created at": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "function": fn.__name__,
        "module": fn.__module__,
        "hash": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
    }
    append_json(prompt_data, save_path)

    return


def generate_chapter_plan(knowledge_pool: KnowledgePool, template: SOPTemplate):

    # ,
    # primary_fact_ids: list[str]
    # supporting_fact_ids: list[str]
    # fact_ids: list[str]

    facts_for_planning = [
        fact for fact_list in knowledge_pool.facts.values() for fact in fact_list
    ]

    core_chapters = [
        chapter
        for chapter in template.chapters
        if chapter.kind == "core"
        and chapter.knowledge_source == "retrieval"
        and chapter.allow_subchapters
    ]

    total = len(core_chapters)

    cache_folder = "chapter_planning"

    chapter_plans = {}
    plan_evals = {}
    for idx, chap in enumerate(core_chapters):
        cache_key = make_cache_key(
            params={
                "chapter_names": chap.name,
                "run_name": "chapter_planning_v2",
                "prompt_version": "prompt_v1",
                "model": "marvin_gpt-4o",
                # topics_hash
            }
        )

        cached = load_from_cache(
            key=cache_key, folder=cache_folder, cls=CoreChapterPlan
        )
        if cached is not None:
            app_session.logger.info("Loading cached facts (key=%s)", cache_key)
            # print(f"Loading cached facts (key={cache_key})")
            chapter_plan = cached  # .copy()

        else:
            app_session.logger.info(
                "Start 'plan_core_chapter' on chapter '%s' (%s of %s total)",
                chap.name,
                idx,
                total,
            )

            chapter_plan = plan_core_chapter(
                chapter_name=chap.name,
                facts=facts_for_planning,  # : list[FactForPlanning],
                min_subchapters=chap.min_subchapters,  # : int,
                max_subchapters=chap.max_subchapters,  # : int,
            )

            save_to_cache(
                key=cache_key,
                folder=cache_folder,
                data={"result": chapter_plan.model_dump()},
                #  for fact in fact_list]}
            )

        chapter_plans[chap.name] = chapter_plan

        plan_evals[chap.name] = evaluate_chapter_plan(knowledge_pool, chapter_plans)

    save_prompt(plan_core_chapter)

    return chapter_plans, plan_evals
