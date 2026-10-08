## retrieve.py
# imports
# import numpy as np
# import pandas as pd
# from tiktoken import
from typing import Any  # , Literal

from src.core.memory import SOPGenContext, app_session
from src.model_rag.data_records import RetrievalResult, RetrievedChunk
from src.model_rag.templates_sop import SOP_BASE_TEMPLATE, SOPTemplate
from src.tools_rag.create_embeds import load_embedding_model

# import src.utils.dict_helper as dh
# import src.utils.general_helper as gh
from src.utils.chroma_helper import get_chroma_collection

# TEST_QUERIES = [
#     "Was ist GMP?",
#     "Wie werden Wirkstoffe geprüft?",
#     "Was sind Anforderungen an Hersteller?",
#     "Was steht in Kapitel %?",
# ]

# def normalise_chroma_results(results: dict) -> list[dict]:

#     chunks_norm = results

#     return chunks_norm


# def build_retrieval_queries(
#                         topic: str,
#                         template_chapters: list[str] | None = None,
#                     ) -> list[str]:
#     """
#     Erstmal simple Query-Expansion.
#     Später kann hier ein LLM oder Regelset rein.
#     """

#     queries = [topic]

#     if template_chapters:
#         for chapter in template_chapters:
#             queries.append(f"{topic} {chapter}")

#     return queries


# @dataclass
# class SOPChapter:
#     ch_title: str
#
#     ch_
#
#     #
#     # table: List = []


# @dataclass
# class SOPTemplate:
#     general_sop: bool=True
#     core_chapter: List[SOPChapter] = field(default_factory=list)
#     support_chapter: List[SOPChapter] = field(default_factory=list)


def get_templates(sop_context: SOPGenContext):
    f_type = sop_context.q_doc_type
    work_mode = sop_context.work_mode

    #     # : Literal[
    #             #         "SOP_general",
    #             #         "SOP_specific",
    #             #         "record",
    #             #         "risk_analysis"
    #             #         ] = "SOP_general",
    #             # chapters: List[int] | str = "all"
    #             # ):

    app_session.logger.info("Start 'get_templates'")
    # print("Start 'get_templates'")

    match f_type:
        case "SOP":
            if work_mode == "create":
                return SOP_BASE_TEMPLATE

            else:
                # return SOP_BASE_TEMPLATE
                raise NotImplementedError("SOP update not yet implemented.")

        # case "SOP_specific":
        #     hi = ""

        case "risk_analysis":
            raise NotImplementedError("SOP update not yet implemented.")

        case _:
            raise ValueError(f"Unknown document type: {f_type}")

    # return templates


def build_retrieval_queries(
    sop_context: SOPGenContext,
) -> list[str]:

    queries = []

    # Allgemeine Query
    queries.append(sop_context.title)

    # Spezifische Topics
    for topic in sop_context.topics:
        queries.append(f"{sop_context.title}: {topic}")

    return queries


def retrieve_for_sop(
    # collection,
    sop_context: SOPGenContext,
    # topic: str,
    template_chapters: SOPTemplate,  # list[str],
    # n_results_per_query: int = 5,
) -> dict[str, RetrievalResult]:
    """
    Kapitelweises Retrieval.
    Das passt zu eurer neuen Template-getriebenen Pipeline.
    """

    app_session.logger.info("Start 'retrieve_for_sop'")
    # print("Start 'retrieve_for_sop'")

    # "paraphrase-multilingual-MiniLM-L12-v2" oder "intfloat/multilingual-e5-base"
    embed_model = load_embedding_model(
        sop_context.transformer_model
    )  # SentenceTransformer(transformer_model)

    #     chunk_settings = sop_context.chunk_settings
    # transformer_model = sop_context.transformer_model

    # title_embed = create_embed_from_query(sop_context.title, sop_context.transformer_model)
    # topics_embed = [create_embed_from_query(top, sop_context.transformer_model)
    #                 for top in sop_context.topics]

    # collection = sop_context.collection
    # topic_text = "; ".join(sop_context.topics)
    # n_results =  sop_context.n_results
    queries = build_retrieval_queries(sop_context)

    templates_sorted = sorted(template_chapters.chapters, key=lambda c: c.order)

    retrieval_results = {}

    for chapter in templates_sorted:
        if chapter.knowledge_source != "retrieval":
            continue

        for query in queries:  # chapter in templates_sorted:
            retrieval_results[query] = retrieve_chunks(
                context=sop_context,
                query=query,
                embed_model=embed_model,
            )

    return retrieval_results


#         query = f"""
# SOP-Kapitel: {chapter.name}. {chapter.text}
# title: {sop_context.title}
# topics: {sop_context.topics}
# """
# {chapter.name}"

# context = SOPGenContext(
#                 collection=collection,
#                 query=query,
#                 n_results=n_results,
#                 )

# chapter_results[chapter.name] = retrieve_chunks(
#                                         context=sop_context,
#                                         query=query,
#                                         embed_model=embed_model
#                                         )

# return chapter_results


def retrieve_chunks(
    context,
    # collection: List[str], # : Collection,
    query: str,
    embed_model,
    # n_results: int = 8,
    # where: dict | None = None,
) -> RetrievalResult:
    """
    Minimaler Retrieval-Wrapper für Chroma.
    """

    query_embedding = embed_model.encode(query, normalize_embeddings=True)
    kwargs = {
        # "query_texts": [query],
        "query_embeddings": [query_embedding],
        "n_results": context.n_results,
        "include": ["documents", "metadatas", "distances"],
    }

    if context.where:
        kwargs["where"] = context.where

    results = []

    for coll in context.collection:
        chroma_coll = get_chroma_collection(coll)
        results.append(chroma_coll.query(**kwargs))

    return normalise_chroma_results(
        context=context,
        results=results,
        query=query,
    )


def normalise_chroma_results(
    context, results: list[dict], query: str = ""
) -> RetrievalResult:
    """
    Normalisiert Chroma-Query-Output in eine flache Chunk-Liste.
    Erwartet typischen Chroma-Output:
    {
        "ids": [[...]],
        "documents": [[...]],
        "metadatas": [[...]],
        "distances": [[...]]
    }
    """

    chunks: list[RetrievedChunk] = []

    for coll_results in results:
        ids = _first_result_list(coll_results.get("ids"))
        docs = _first_result_list(coll_results.get("documents"))
        metas = _first_result_list(coll_results.get("metadatas"))
        distances = _first_result_list(coll_results.get("distances"))

        for idx, text in enumerate(docs):
            if not text or not text.strip():
                continue

            meta = metas[idx] if idx < len(metas) and metas[idx] else {}
            chunk_id = ids[idx] if idx < len(ids) else str(idx)
            distance = distances[idx] if idx < len(distances) else None
            # cosine_dist = _distance_to_score(distance)

            chunks.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    text=text or "",
                    source=(
                        meta.get("source")
                        or meta.get("doc_name")
                        or meta.get("file_name")
                        or ""
                    ),
                    section=(
                        meta.get("section")
                        or meta.get("heading_context")
                        or meta.get("heading")
                        or meta.get("context")
                        or ""
                    ),
                    page=meta.get("page"),
                    distance=distance,
                    similarity=1 - distance if distance is not None else None,
                    metric="cosine",
                    metadata=meta,
                )
            )

    chunks.sort(
        key=lambda chunk: (
            # chunk.distance is not None,
            chunk.distance if chunk.distance is not None else float("inf")
        )
    )
    # try:
    #     st.json(retrieved_chunk.model_dump())
    # except:
    #     pass
    chunks = chunks[: context.n_results]

    # context.results
    return RetrievalResult(
        query=query,
        chunks=chunks,  # [c for c in chunks if c.text.strip()],
        n_results=len(chunks),
    )


def _first_result_list(value: Any) -> list:
    """
    Chroma liefert meist verschachtelte Listen:
    [["a", "b", "c"]]

    Diese Funktion macht daraus:
    ["a", "b", "c"]
    """
    if value is None:
        return []

    if value and isinstance(value, list) and isinstance(value[0], list):
        return value[0]

    if value and isinstance(value, list):
        return value

    return []


def _distance_to_score(
    distance: float | None,
    # dist_mode: ""
) -> float | None:
    """
    Chroma gibt oft Distanzen zurück.
    Kleinere Distanz = besser.
    Für die Pipeline reicht zunächst eine einfache Umrechnung.
    """
    if distance is None:
        return None

    try:
        return 1 / (1 + float(distance))
    except Exception:
        return None


def flatten_retrieval_results(
    retrieval_results: dict[str, RetrievalResult],
) -> list[RetrievedChunk]:
    """
    Macht aus kapitelweisen Ergebnissen eine deduplizierte Chunk-Liste.
    """

    app_session.logger.info("Start 'flatten_retrieval_results'")
    # print("Start 'flatten_retrieval_results'")

    seen = set()
    chunks_flat: list[RetrievedChunk] = []

    for result in retrieval_results.values():
        for chunk in result.chunks:
            chunk_key = chunk.metadata.get(
                "chunk_global_id",
                chunk.chunk_id,
            )

            if chunk_key in seen:
                continue

            seen.add(chunk_key)
            chunks_flat.append(chunk)

    chunks_flat.sort(
        key=lambda chunk: chunk.distance if chunk.distance is not None else float("inf")
    )

    return chunks_flat


'''
def retrieve():
    # load env variables and config
    gh.load_env_vars()

    config_name = input("Enter 'config_file' name (no suffix): ")
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    return run_retrieve()  # configs


def run_retrieve():
    config = session.model_config
    n_retrieve = config["n_retrieve"]

    # load df
    file_path = ""
    df = pd.read_parquet(file_path)

    #
    q_emb = _embed_query()

    df["score"] = df["text_embed"].apply(lambda x: _cosine_sim(q_emb, a))

    top_k = df.sort_values("score", ascending=False).head(n_retrieve)
    context = "\n\n".join(top_k["text"])

    context_exp = _expand_context(df, top_k)
    return


def _embed_query(query=None):
    config = session.model_config

    general_config = config.get("general", {})
    model_name = general_config["llm_model"]

    encoder = encoding_for_model(model_name)

    if not query:
        query = input("Please, enter your query.")

    q_emb = encoder.encode(query)

    return q_emb


def _cosine_sim(a, b):

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def _expand_context(df, top_k):

    expanded = []

    for _, row in top_k.iterrows():
        prev_id = row["prev_chunk_id"]
        next_id = row["next_chunk_id"]

        expanded.append(row)

        if prev_id in df.index:
            expanded.append(df.loc[prev_id])

        if next_id in df.index:
            expanded.append(df.loc[next_id])

    return pd.DataFrame(expanded).drop_duplicates()


""" CHROMA * FAISS INTEGRATION """


def _evaluate_rag():
    """
    Recall@k
    Precision@k
    qualitative Bewertung
    """
    return
'''
