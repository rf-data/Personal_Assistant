## generate_sop.py
# import
from collections import Counter
import marvin

from src.core.memory import app_session
from src.model_rag.classes_chunk_fact import (
                                        ConsolidatedFact,
                                        IngestedChunk,
                                        )
from src.model_rag.classes_sop import CoreChapterPlan


def get_supporting_chunks(
        facts: list[ConsolidatedFact],
        chunks: dict[str, IngestedChunk],
    ) -> list[IngestedChunk]:

    chunk_ids = {
        source.chunk_id
        for fact in facts
        for source in fact.sources
    }

    return [
        chunks[chunk_id]
        for chunk_id in chunk_ids
        if chunk_id in chunks
    ]

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

    Rules:
    - Use only the supplied facts.
    - Group facts by operational purpose, not merely by wording.
    - Create between min_subchapters and max_subchapters.
    - Assign every relevant fact to exactly one primary subchapter.
    - Do not invent procedures, roles, frequencies or requirements.
    - Do not create a subchapter for isolated irrelevant fragments.
    - Use concise operational German headings.
    - Order subchapters in the sequence in which the work is planned,
      performed, monitored, documented and assessed.
    """


def evaluate_chapter_plan(knowledge_pool, chapter_plan):

    all_fact_ids = {
            fact.fact_id
            for facts in knowledge_pool.facts.values()
            for fact in facts
        }

    assigned_fact_ids = {
            fact_id
            for subchapter in chapter_plan.subchapters
            for fact_id in subchapter.fact_ids
        }

    unassigned = all_fact_ids - assigned_fact_ids
    unknown = assigned_fact_ids - all_fact_ids

    duplicates = [
            fact_id
            for fact_id, count in Counter(
                fact_id
                for subchapter in chapter_plan.subchapters
                for fact_id in subchapter.fact_ids
            ).items()
            if count > 1
        ]

    app_session.logger.info(
                    "%s EVALUATION RESULTS %s \n"
                    "Assigned facts (n=%s):\n-> %s\n"
                    "Unassigned facts (n=%s):\n-> %s\n"
                    "Unknown facts (n=%s):\n-> %s\n"
                    "Multiple used facts (n=%s):\n-> %s\n",
                    '='*15,
                    '='*15,
                    len(assigned_fact_ids),
                    assigned_fact_ids,
                    len(unassigned),
                    unassigned,
                    len(unknown),
                    unknown,
                    len(duplicates),
                    duplicates
                    )

    return 

#                   "Number of  and non-unique facts:\t %s | %s",

def generate_chapter_plan(knowledge_pool, template):

    # ,
    # primary_fact_ids: list[str]
    # supporting_fact_ids: list[str]
    # fact_ids: list[str]

    core_chapters = [
        chapter
        for chapter in template.chapters
        if chapter.kind == "core"
        and chapter.knowledge_source == "retrieval"
        and chapter.allow_subchapters
        ]

    total = len(core_chapters)

    chapter_plans = {}
    for idx, chap in enumerate(core_chapters):
        app_session.logger.info(
                        "Start 'plan_core_chapter' on chapter '%s' (%s of %s total)",
                        chap.name,
                        idx,
                        total
                                )

        chapter_plan = plan_core_chapter(
                                chapter_name=chap.name,
                                facts=knowledge_pool.facts,     # : list[FactForPlanning],
                                min_subchapters=chap.min_subchapters,   # : int,
                                max_subchapters=chap.min_subchapters    # : int,
                                )

        chapter_plans[chap.name] = chapter_plan

        evaluate_chapter_plan(knowledge_pool, chapter_plan)

    return chapter_plans