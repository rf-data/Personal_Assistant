## generate_sop.py
# import
# from dataclasses import asdict
from collections import Counter
import marvin

from src.core.memory import app_session
from src.model_rag.classes_chunk_fact import (
                                        ConsolidatedFact,
                                        IngestedChunk,
                                        KnowledgePool
                                        )
from src.model_rag.classes_sop import CoreChapterPlan, SOPTemplate   # , FactForPlanning

from src.utils.general_helper import (
                                # load_env_vars,
                                make_cache_key,
                                load_from_cache,
                                save_to_cache
                                )

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
    - Create between min_subchapters and max_subchapters.
    - Prefer as few subchapters as necessary.
    - Each subchapter should represent one coherent operational activity or process step.
    - Group facts by operational purpose, not merely by wording.
    - Facts within one subchapter should describe the same activity.
    - Assign every relevant fact to exactly one primary subchapter.
    - Do not invent procedures, roles, frequencies or requirements.
    - Do not create subchapters for isolated or irrelevant fragments.
    - Use concise German operational headings describing the activity.
    - Order subchapters according to the logical workflow of the procedure.
    - For each subchapter provide a short rationale explaining the grouping.
    - For each assigned fact return its fact_id together with the original fact text (or a very close one-sentence paraphrase without adding new information).

    """


def evaluate_chapter_plan(
                    knowledge_pool,
                    chapter_plan: dict[str, CoreChapterPlan]
                    ):

    for c_name, plan in chapter_plan.items():
        all_fact_ids = {
                fact.fact_id
                for facts in knowledge_pool.facts.values()
                for fact in facts
            }

        assigned_fact_ids = {
                fact.fact_id
                for subchapter in plan.subchapters
                for fact in subchapter.facts
            }

        unassigned = all_fact_ids - assigned_fact_ids
        unknown = assigned_fact_ids - all_fact_ids

        duplicates = [
                fact_id
                for fact_id, count in Counter(
                    fact.fact_id
                    for subchapter in plan.subchapters
                    for fact in subchapter.facts
                ).items()
                if count > 1
            ]

        app_session.logger.info(
                        "%s EVALUATION RESULTS '%s' %s \n"
                        "Assigned facts (n=%s):\n-> %s\n"
                        "Unassigned facts (n=%s):\n-> %s\n"
                        "Unknown facts (n=%s):\n-> %s\n"
                        "Multiple used facts (n=%s):\n-> %s\n",
                        '='*15,
                        c_name.upper(),
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

def generate_chapter_plan(knowledge_pool: KnowledgePool, template: SOPTemplate):

    # ,
    # primary_fact_ids: list[str]
    # supporting_fact_ids: list[str]
    # fact_ids: list[str]

    facts_for_planning = [
                fact
                for fact_list in knowledge_pool.facts.values()
                for fact in fact_list
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
    for idx, chap in enumerate(core_chapters):
        cache_key = make_cache_key(params={
                        "chapter_names": chap.name,
                        "run_name": "chapter_planning_v2",
                        "prompt_version": "prompt_v1",
                        "model": "marvin_gpt-4o"
                        # topics_hash
                        })

        cached = load_from_cache(
                            key=cache_key,
                            folder=cache_folder,
                            cls=CoreChapterPlan
                            )
        if cached is not None:
            app_session.logger.info("Loading cached facts (key=%s)", cache_key)
            # print(f"Loading cached facts (key={cache_key})")
            chapter_plan = cached   # .copy()

        else:
            app_session.logger.info(
                            "Start 'plan_core_chapter' on chapter '%s' (%s of %s total)",
                            chap.name,
                            idx,
                            total
                            )

            chapter_plan = plan_core_chapter(
                                    chapter_name=chap.name,
                                    facts=facts_for_planning,     # : list[FactForPlanning],
                                    min_subchapters=chap.min_subchapters,   # : int,
                                    max_subchapters=chap.max_subchapters    # : int,
                                    )

            save_to_cache(
                key=cache_key,
                folder=cache_folder,
                data={"result": chapter_plan.model_dump()}
                 #  for fact in fact_list]}
                )

        chapter_plans[chap.name] = chapter_plan

        evaluate_chapter_plan(knowledge_pool, chapter_plans)

    return chapter_plans
