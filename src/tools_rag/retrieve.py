## retrieve.py
# imports
import numpy as np
import pandas as pd
from tiktoken import encoding_for_model

import src.utils.dict_helper as dh
import src.utils.general_helper as gh
from src.core.memory import session

TEST_QUERIES = [
    "Was isr GMP?",
    "Wie werden Wirkstoffe geprüft?",
    "Was sind Anforderungen an Hersteller?",
    "Was steht in Kapitel %?",
]


def retrieve():
    # load env variables and config
    gh.load_env_vars()

    config_name = input("Enter 'config_file' name (no suffix): ")
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    return run_retrieve()  # configs


def run_retrieve():
    config = session.model_config
    n_retrieve = config["n_retireve"]

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
