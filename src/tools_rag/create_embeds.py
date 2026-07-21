from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

# import streamlit as st
from src.core.memory import ParseContext, app_session
from src.utils.chroma_helper import add_chroma_data, get_chroma_collection


def _to_chroma_scalar(value: Any) -> str | int | float | bool | None:
    """Konvertiert Werte in Chroma-kompatible Metadata-Typen."""

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, pd.Series):
        raise TypeError(
            "Chroma metadata received a pandas Series. "
            f"Series name: {value.name!r}. "
            "Use the value from the current row instead."
        )

    if isinstance(value, (list, tuple, set, dict, np.ndarray)):
        return str(value)

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return str(value)


def _create_or_update_metadata(
    data: pd.DataFrame, excluded_columns: set[str], meta_data: dict | None = None
):
    meta_data = meta_data or {}

    # if len(meta_data) == 0:
    #     meta_data = _create_metadata(data)

    metadata_columns = [
        column for column in data.columns if column not in excluded_columns
    ]

    metadatas = []
    for _, row in data.iterrows():
        chunk_metadata = {}

        for key, value in meta_data.items():
            if key == "meta":
                continue

            if isinstance(value, pd.Series):
                raise TypeError(
                    f"meta_data[{key!r}] is a pandas Series. "
                    "Pass a global scalar or read the value from row[key]."
                )

            converted = _to_chroma_scalar(value)

            if converted is not None:
                chunk_metadata[key] = converted

        shared_meta = meta_data.get("meta", {})

        if shared_meta:
            if not isinstance(shared_meta, dict):
                raise TypeError("meta_data['meta'] must be a dictionary.")

            for key, value in shared_meta.items():
                converted = _to_chroma_scalar(value)

                if converted is not None:
                    chunk_metadata[key] = converted

        for column in metadata_columns:
            converted = _to_chroma_scalar(row[column])

            if converted is not None:
                chunk_metadata[column] = converted

        # Praktisch für Filter und Debugging
        chunk_metadata["chunk_global_id"] = str(row["chunk_global_id"])

        # None-Werte entfernen, da Chroma je nach Version
        # damit Probleme machen kann.
        chunk_metadata = {
            key: value for key, value in chunk_metadata.items() if value is not None
        }

        metadatas.append(chunk_metadata)

    return metadatas


@lru_cache(maxsize=2)
def load_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def create_embed_from_query(query: str, transformer_model: str):
    model = load_embedding_model(transformer_model)

    return model.encode(
        query,
        # batch_size=chunk_settings.batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        # show_progress_bar=True
    )


def embed_text(df_embed: pd.DataFrame, chunk_context: ParseContext):
    logger = app_session.logger

    # from sentence_transformers import SentenceTransformer

    logger.info("Start creating embeddings from 'text' chunks")

    ## using SBERT for text embeddings

    chunk_settings = chunk_context.chunk_settings
    transformer_model = chunk_settings.transformer_model

    model = load_embedding_model(transformer_model)
    texts = df_embed["embed_text"].tolist()

    embeddings = []
    batch_size = 16  # chunk_settings.batch_size  # 256

    logger.info("Start embedding with %s texts...", len(texts))

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        emb = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        embeddings.append(emb)

    embeddings = np.vstack(embeddings)

    logger.info(
        "Finished creating embeddings", "--> embeddings shape:\t%s", embeddings.shape
    )

    embeddings = np.asarray(embeddings)

    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected a 2D embedding matrix, got shape {embeddings.shape}"
        )

    if len(embeddings) != len(df_embed):
        raise ValueError(
            f"Embedding count ({len(embeddings)}) does not match "
            f"DataFrame rows ({len(df_embed)})"
        )

    df_embed["embed_text"] = [row.astype(float).tolist() for row in embeddings]

    del embeddings

    # load_chunks_to_chroma(df, coll_name="apo_qms")

    # save_path = f"{f_directory}/{f_stem.replace("chunked", "embed")}{f_suffix}"

    # df_embed.to_parquet(save_path, index=False)

    return df_embed


def load_chunks_to_chroma(
    coll_name: str,
    data: pd.DataFrame,  #  | str,
    required_columns: dict,
    meta_data: dict = {},
):
    logger = app_session.logger

    chroma_coll = get_chroma_collection(coll_name=coll_name)

    real_dim = len(data["text_embed"].iloc[0])
    expected_dim = chroma_coll.metadata.get("embedding_dim")

    if expected_dim != real_dim:
        raise ValueError(
            f"Embedding dimension mismatch: "
            f"collection expects {expected_dim}, "
            f"model produces {real_dim}"
        )
    meta_data = meta_data or {}

    metadatas = _create_or_update_metadata(data, required_columns, meta_data)
    # required_columns = {
    #     "chunk_text",
    #     "chunk_global_id",
    #     # "f_name",
    #     "embed_text",
    #     }

    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        logger.error(
            f"df_name: {data.loc[:, 'doc_name'][0]}\n"
            f"Missing required columns: {sorted(missing_columns)}\n"
            f"Available columns:\n {data.columns}"
        )

        if (
            len(missing_columns) == 1
            and "embed_text" in missing_columns
            and "text_embed" in data.columns
        ):
            data.rename(columns={"embed_text": "text_embed"})

        # print(
        #   f"df_name: {data.loc[:, 'doc_name'][0]}\n"
        # f"Missing required columns: {sorted(missing_columns)}\n"
        # f"Available columns:\n {data.columns}")

        return

    if data.empty:
        raise ValueError("No chunk data supplied.")

    add_chroma_data(coll_name=coll_name, data=data, meta_data=meta_data)

    return
