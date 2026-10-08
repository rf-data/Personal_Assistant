from __future__ import annotations

import os
from typing import Any

import streamlit as st


@st.cache_resource(show_spinner=False)
def _get_chroma_client():
    # Lazy import: chromadb is not imported when the app first starts.
    from src.utils.chroma_helper import get_chroma_client

    return get_chroma_client()


def list_chroma_collections() -> list[str]:
    client = _get_chroma_client()
    return sorted(collection.name for collection in client.list_collections())


@st.cache_resource(show_spinner="Loading embedding model…")
def _load_embedding_model(model_name: str):
    # SentenceTransformers/Torch load only on the first real retrieval request.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _normalise_chroma_result(result: dict[str, Any]) -> list[dict]:
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    chunks: list[dict] = []
    for idx, text in enumerate(documents):
        if not text or not str(text).strip():
            continue

        metadata = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}
        distance = distances[idx] if idx < len(distances) else None
        source = (
            metadata.get("source")
            or metadata.get("doc_name")
            or metadata.get("file_name")
            or ""
        )

        chunks.append(
            {
                "chunk_id": str(ids[idx]) if idx < len(ids) else str(idx),
                "text": str(text),
                "source": source,
                "distance": distance,
                "similarity": (1.0 - float(distance) if distance is not None else None),
                "metadata": metadata,
            }
        )

    return chunks


def retrieve_chunks(
    *,
    collection_name: str,
    query: str,
    embedding_model_name: str,
    n_results: int = 5,
) -> list[dict]:
    client = _get_chroma_client()
    collection = client.get_collection(
        name=collection_name,
        embedding_function=None,
    )

    model = _load_embedding_model(embedding_model_name)
    query_embedding = model.encode(query, normalize_embeddings=True)

    result = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return _normalise_chroma_result(result)


def _get_openai_api_key() -> str:
    try:
        key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        key = None

    key = key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in Streamlit secrets or "
            "the process environment."
        )
    return key


@st.cache_resource(show_spinner=False)
def _get_openai_client(api_key: str):
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _build_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant indexed context was retrieved."

    parts: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata") or {}
        source = chunk.get("source") or "unknown"
        section = metadata.get("section") or metadata.get("heading_context") or ""
        page = metadata.get("page")

        reference = f"[Source {idx}] {source}"
        if section:
            reference += f" | {section}"
        if page is not None:
            reference += f" | page {page}"

        parts.append(f"{reference}\n{chunk['text']}")

    return "\n\n".join(parts)


def answer_question(
    *,
    question: str,
    chunks: list[dict],
    model: str,
    previous_messages: list[dict] | None = None,
) -> str:
    client = _get_openai_client(_get_openai_api_key())
    context = _build_context(chunks)

    messages = [
        {
            "role": "system",
            "content": (
                "Answer only from the supplied retrieved context. If the context "
                "does not support an answer, say so explicitly. Do not invent "
                "missing facts. Cite supporting context inline as [Source 1], "
                "[Source 2], etc."
            ),
        }
    ]

    for message in previous_messages or []:
        if message.get("role") in {"user", "assistant"}:
            messages.append(
                {
                    "role": message["role"],
                    "content": message.get("content", ""),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": f"Retrieved context:\n\n{context}\n\nQuestion:\n{question}",
        }
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    content = response.choices[0].message.content
    return content.strip() if content else "No answer returned."
