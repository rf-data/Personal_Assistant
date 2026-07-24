## generate.py
# import
import os
import re
from collections import defaultdict
from dataclasses import asdict
from typing import List

import numpy as np
import marvin
from pydantic_ai import Agent

from src.core.memory import SOPGenContext, app_session
from src.core.config import env_variables
from src.tools_rag.create_embeds import load_embedding_model
from src.model_rag.chunks_retrieval import (
                                        # MergedFact,
                                        MergeDecision,
                                        ExtractedFact,
                                        IngestedFact,
                                        IngestedChunk,
                                        RetrievedChunk,
                                        ConsolidatedFact,
                                        SourceReference
                                        )
from src.utils.general_helper import (
                                # load_env_vars,
                                make_cache_key,
                                load_from_cache,
                                save_to_cache
                                )

# from src.agent.templates.sop_template import CHAPTER_TEMPLATE   # , SOP_TEMPLATE

# SCOPE_DICT = {"sop_allg": "Erstelle eine allgemeine SOP zu folgendem Thema:"}


# task_scope = "Erstelle eine allgemeine SOP zu folgendem Thema:"


def _ingest_chunk(chunk: RetrievedChunk):
    """= Post-retrieval;
    - add infos / metadata / sources to each chunk
    """
    # topics = sop_context.topics
    # POST_RETRIEVAL_PROMPT = ""

    return IngestedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                # fact="",
                topic="",
                source=chunk.source,
                section=(
                    chunk.section
                    or chunk.metadata.get("heading_context", "")
                    ),
                page=chunk.page,
                similarity=chunk.similarity,
            )

# marvin.defaults.model = f"openai:gpt-4o-mini"
# model_marvin.py

# python - <<'PY'
# import os
# import marvin
# from src.utils.general_helper import load_env_vars

# marvin.defaults.model = "openai-chat:gpt-4o-mini"

# load_env_vars()

# api_key = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_KEY"] = api_key

# @marvin.fn
# def extract_test(text: str) -> list[str]:
#     """Extract the main factual statements."""

# print(extract_test("Environmental monitoring shall be performed regularly."))
# PY

def configure_marvin(
    context
    # model: str = "openai:gpt-4o-mini",
    ) -> None:

    api_key = env_variables.openai_api_key

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment."
        )

    os.environ["OPENAI_API_KEY"] = api_key

    marvin.defaults.model = context.llm_context.extraction_model

    Agent.instrument_all()

    return


@marvin.fn
def extract_chunk_facts(
        chunk_text: str,
        allowed_topics: list[str],
        ) -> list[ExtractedFact]:
    """
    Extract all SOP-relevant factual statements from the source text.

    Assign each fact to exactly one of the provided allowed_topics.

    Rules:
    - Preserve the factual meaning of the source.
    - Do not add information not present in the source.
    - Split independent requirements or statements into separate facts.
    - Ignore irrelevant text such as headers, footers and document titles.
    - Use only topics from allowed_topics.
    """


def extract_facts(
            chunk: IngestedChunk,
            sop_context: SOPGenContext,
            ) -> List[IngestedFact]:
    cache_folder = "fact_extraction"
    cache_key = make_cache_key(params={
                        "id": chunk.chunk_id,
                        "run_name": "fact_extraction_v1",
                        "prompt_version": "prompt_v1",
                        "model": "marvin_gpt-4o"
                        # topics_hash
                        })

    cached = load_from_cache(key=cache_key, folder=cache_folder)

    if cached is not None:
        app_session.logger.info("Loading cached facts (key=%s)", cache_key)
        print(f"Loading cached facts (key={cache_key})")
        return [
            IngestedFact(**chunk_dict)
            for chunk_dict in cached["facts"]
            ]

    app_session.logger.info("Start extracting facts by 'marvin'")
    print("Start extracting facts by 'marvin'")

    extracted = extract_chunk_facts(
        chunk_text=chunk.text,
        allowed_topics=sop_context.topics,
    )

    fact_list = [
            IngestedFact(
                fact=item.fact,
                topic=item.topic,
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                section=chunk.section,
                page=chunk.page,
                similarity=chunk.similarity,
            )
            for item in extracted
            ]

    save_to_cache(
                key=cache_key,
                folder=cache_folder,
                data={"facts": [asdict(fact) for fact in fact_list]}
                )
            # chunks_serialized =
    return fact_list


def build_chunk_fact_pool(
                chunks_ret: list[RetrievedChunk],
                sop_context: SOPGenContext
                ) -> dict:
    """
    ingest and summarize retrieved chunks
    """

    app_session.logger.info("Start 'summarize_chunks'")
    print("Start 'summarize_chunks'")

    chunks = []
    facts = []
    for chunk in chunks_ret:
        chunk_ing = _ingest_chunk(chunk)
        # chunk_fact =
        chunks.append(chunk_ing)
        facts.append(
                extract_facts(
                    chunk=chunk_ing,
                    sop_context=sop_context
                    # allowed_topics=sop_context.topics,
                    )
                )

    return {
        "chunks": chunks,
        "facts": facts
        }


def filter_facts(
            facts: list[IngestedFact],
        ) -> list[IngestedFact]:

    cleaned = []

    if len(facts) == 0:
        app_session.logger.error("Provided 'facts' is empty.")
        raise ValueError("Provided 'facts' is empty.")

    for fact in facts:
        text = fact.fact.strip()

        if len(text) < 20:
            continue

        if text.lower().startswith(
            (
                "kommentar",
                "leitlinie"
            )
        ):
            continue

        cleaned.append(fact)

    return cleaned


def group_filtered_facts(
    facts: list[IngestedFact],
) -> dict[str, list[IngestedFact]]:

    grouped = defaultdict(list)

    facts_clean = filter_facts(facts)

    for fact in facts_clean:
        grouped[fact.topic].append(fact)

    return dict(grouped)


def normalize_fact_text(text: str) -> str:
    text = text.lower().strip()

    # Whitespace vereinheitlichen
    text = re.sub(r"\s+", " ", text)

    # einfache Satzzeichen am Ende entfernen
    text = text.rstrip(".;:")

    return text


def deduplicate_facts(
                facts: list[IngestedFact],
            ) -> list[IngestedFact]:

    fact_map: dict[
                tuple[str, str],
                ConsolidatedFact,
                ] = {}

    # seen: set[tuple[str, str]] = set()
    # deduplicated: list[IngestedFact] = []

    for item in facts:
        key = (
            item.topic,
            normalize_fact_text(item.fact),
        )

        source_ref = SourceReference(
                        chunk_id=item.chunk_id,
                        source=item.source,
                        section=item.section,
                        page=item.page,
                        )

        if key not in fact_map:
            fact_map[key] = ConsolidatedFact(
                                    fact=item.fact,
                                    topic=item.topic,
                                    sources=[source_ref],
                                    )
            # continue
        else:
            fact_map[key].sources.append(
                                    source_ref
                                    )

        # seen.add(key)
        # deduplicated.append(fact)


    return list(fact_map.values())  # deduplicated



def cosine_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:

    return float(
        np.dot(a, b)
        / (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )
    )


def cluster_similar_facts(
    facts: list[ConsolidatedFact],
    transformer_model: str,
    threshold: float = 0.90,
) -> list[list[ConsolidatedFact]]:

    """
    Für den ersten Prototyp reicht es aber.

    Später wäre sauberer:
    Agglomerative Clustering
    DBSCAN
    Union-Find auf Similarity-Kanten
    """

    if not facts:
        return []

    texts = [
        fact.fact
        for fact in facts
    ]

    model = load_embedding_model(transformer_model)
    embeddings = model.encode(
                        texts,
                        normalize_embeddings=True,
                        )

    clusters: list[
        list[ConsolidatedFact]
    ] = []

    used = set()

    for i, fact in enumerate(facts):

        if i in used:
            continue

        cluster = [fact]
        used.add(i)

        for j in range(
            i + 1,
            len(facts),
        ):

            if j in used:
                continue

            similarity = float(
                np.dot(
                    embeddings[i],
                    embeddings[j],
                )
            )

            if similarity >= threshold:
                cluster.append(
                    facts[j]
                )
                used.add(j)

        clusters.append(cluster)

    return clusters


@marvin.fn
def assess_and_merge_facts(
                    facts: list[str],
                    ) -> MergeDecision:
    """
    Determine whether these statements describe
    the same factual requirement.

    Only merge if they are compatible and refer
    to the same requirement.

    Never combine different scopes,
    frequencies, conditions or regulatory levels.

    If they should remain separate,
    return mergeable=False.

    Consolidate semantically overlapping factual
    statements into one precise factual statement.

    Rules:
    - Preserve all supported information.
    - Do not introduce new information.
    - Do not weaken mandatory requirements.
    - Do not invent frequencies, thresholds,
      responsibilities or procedures.
    - If the statements are not actually
      compatible, do not merge them.
    """


def merge_clusters(
    clusters: list[
        list[ConsolidatedFact]
    ],
) -> list[ConsolidatedFact]:

    cache_folder = "cluster_merge"

    merged_results = []

    for cluster in clusters:

        if len(cluster) == 1:
            merged_results.append(
                cluster[0]
            )
            continue

        cache_key = make_cache_key(params={
                        "topic": [
                            item.topic
                            for item in cluster
                            ],
                        "n_facts": len(cluster),
                        "run_name": "cluster_merge_v1",
                        "prompt_version": "prompt_v1",
                        "model": "marvin_gpt-4o"
                        # topics_hash
                        })

        cached = load_from_cache(key=cache_key, folder=cache_folder)
        if cached is None:
            result = assess_and_merge_facts(
                                        facts=[
                                            item.fact
                                            for item in cluster
                                            ]
                                        )

            save_to_cache(
                key=cache_key,
                folder=cache_folder,
                data={"result": asdict(result)}    #  for res in ]}
                )

        else:
            result = cached.get("result")
            app_session.logger.info("Loading cached results (key=%s)", cache_key)
            print(f"Loading cached results (key={cache_key})")


            # return [
            #     IngestedFact(**chunk_dict)
            #     for chunk_dict in cached["facts"]
            #     ]

        if not result.mergeable:
            merged_results.extend(
                cluster
            )
        else:
            sources = []

            for item in cluster:
                sources.extend(
                    item.sources
                )

            merged_results.append(
                ConsolidatedFact(
                    fact=result.fact,
                    topic=cluster[0].topic,
                    sources=sources,
                )
            )

    return merged_results


# def merge_fact_group() -> KnowledgeSummary:

#     return


def consolidate_facts(
            facts: list[IngestedFact],
            embed_model,
            similarity_threshold: float = 0.90,
            ) -> dict[str, list[ConsolidatedFact]]:

    # 1. Exakte Dubletten
    deduplicated = deduplicate_facts(
        facts
    )

    # 2. Nach Topic gruppieren
    grouped = group_filtered_facts(
                            deduplicated
                            )

    result = {}

    for topic, topic_facts in grouped.items():

        # 3. Semantisch ähnliche Facts clustern
        clusters = cluster_similar_facts(
            facts=topic_facts,
            embed_model=embed_model,
            threshold=similarity_threshold,
        )

        # 4. LLM-gestützter Merge
        merged = merge_clusters(
            clusters
        )

        result[topic] = merged

    return result

    # chunks_ing = []
    # for chunk in chunks:
    #     chunks_ing.append(_ingest_chunk(chunk, context))

    # return ChunkSummary(
    #     content="",
    #     sources=[(source, section), (...)],
    # )


# def summarize_chunks(
#     chunks: list[IngestedChunk],
#     context: SOPGenContext,
#     llm_client,
# ) -> ChunkSummary:
#     ...


# def build_context(
#     topic: str, chapter_name: str, chunk_summary: ChunkSummary
# ) -> PromptContext:
#     # parts = []

#     # for i, chunk in enumerate(chunks, start=1):
#     #     parts.append(
#     #         f"[Quelle {i}]\n"
#     #         f"{chunk['text']}\n"
#     #     )

#     return PromptContext(
#         chunk_summary="\n\n".join(parts),
#         task_scope=SCOPE_DICT[""],
#         chapter="",
#         mode="",  # ["new", "update"]
#         template=CHAPTER_TEMPLATE[""],
#     )


# GMP-orientierter .
# Berücksichtige, dass die SOPs zu einer
# gehören und man sich an GMP orientiert aber nicht daran gebunden ist.


def build_sop_gen_prompt(context: SOPGenContext) -> str:
    # return
    """
    Du bist GMP-Experte.
    Erstelle aus dem bereitgestellten Wissenspool eine SOP.

    Regeln:
    - keine neuen Inhalte
    - keine Halluzinationen
    - nichts weglassen
    - fachlich konsistent
    - logisch strukturieren
    - Quellen zitieren
    - professioneller SOP-Stil
    - Markdown
    """

    return f"""
Du bist ein SOP-Autor, der GMP-relevante SOPs für eine
herstellende Apotheke schreibt. Man ist nicht an GMP gebunden,
will sich aber daran orientieren.

Aufgabe:
{context.task_scope}

{user_request}

Verwende ausschließlich den folgenden Kontext, soweit er passt.
Wenn Informationen fehlen, schreibe allgemeine, vorsichtige Platzhalter.

Kontext:
{context.chunks}

Vorlage:
{context.template}

Überarbeite die SOP kapitelweise und gibt den Inhalt als Markdown aus.
Du kannst auch neue Unterkapitel erstellen, um den Inhalt besser zu strukturieren.
"""


# def generate_sop(prompt: str, client) -> str:
#     response = client.responses.create(
#         model="gpt-4.1-mini",
#         input=prompt,
#     )
#     return response.output_text


# - Zweck
# - Geltungsbereich
# - Verantwortlichkeiten
# - Durchführung
# - Dokumentation
# - Abweichungen
# - Referenzen
'''
def generate_report(data):
prompt = f"""
    Analyze this business data.
    Provide:
    - Key Metrics
    - Growth Analysis
    - Risks
    - Opportunities
    - Recommendations
    Data:
    {data}
    """
    return llm(prompt)
'''

"""
import pandas as pd

def generate_report():
    data = pd.read_csv("data.csv")
    summary = data.describe()
    summary.to_csv("report.csv")

generate_report()
"""
