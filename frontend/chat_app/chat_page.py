from __future__ import annotations

import streamlit as st

from services import answer_question, list_chroma_collections, retrieve_chunks

DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"


def _init_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


def _render_chunk(chunk: dict, idx: int) -> None:
    metadata = chunk.get("metadata") or {}
    source = (
        chunk.get("source")
        or metadata.get("source")
        or metadata.get("doc_name")
        or metadata.get("file_name")
        or "unknown"
    )
    section = (
        metadata.get("section")
        or metadata.get("heading_context")
        or metadata.get("heading")
        or ""
    )
    page = metadata.get("page")
    similarity = chunk.get("similarity")

    title_parts = [f"#{idx}", str(source)]
    if section:
        title_parts.append(str(section))
    if page is not None:
        title_parts.append(f"page {page}")
    if similarity is not None:
        title_parts.append(f"sim={similarity:.3f}")

    with st.expander(" | ".join(title_parts)):
        st.write(chunk.get("text", ""))
        if metadata:
            st.json(metadata)


def render_upload_chat_page() -> None:

    st.title("💬 Chat with an uploaded file")

    st.write("UNDER CONSTRUCTION")

    return None


def render_db_chat_page() -> None:
    _init_state()

    st.title("💬 Chat with database files")
    st.caption(
        "Retrieval-only frontend. Chunking, parsing, embedding and Chroma upload "
        "are intentionally handled outside Streamlit."
    )

    with st.sidebar:
        st.subheader("Chat settings")
        try:
            collections = list_chroma_collections()
        except Exception as exc:
            collections = []
            st.error(f"Could not connect to ChromaDB: {exc}")

        collection = st.selectbox(
            "Chroma collection",
            options=collections,
            index=0 if collections else None,
            placeholder="No collection available",
        )
        embedding_model = st.text_input(
            "Embedding model",
            value=DEFAULT_EMBEDDING_MODEL,
            help=(
                "Must match the model used to build the collection. The model "
                "is loaded lazily only when a query is submitted."
            ),
        )
        chat_model = st.text_input("Chat model", value=DEFAULT_CHAT_MODEL)
        top_k = st.slider("Retrieved contexts", min_value=1, max_value=10, value=5)
        show_context = st.toggle("Show retrieved context", value=True)

        if st.button("Clear chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    if not collections:
        st.warning(
            "No Chroma collection is available. Retrieval needs an already "
            "prepared collection."
        )
        return

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if (
                message["role"] == "assistant"
                and show_context
                and message.get("chunks")
            ):
                st.caption("Retrieved evidence")
                for idx, chunk in enumerate(message["chunks"], start=1):
                    _render_chunk(chunk, idx)

    prompt = st.chat_input(
        "Ask a question about the indexed files…",
        disabled=collection is None,
    )
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant context…"):
            try:
                chunks = retrieve_chunks(
                    collection_name=collection,
                    query=prompt,
                    embedding_model_name=embedding_model,
                    n_results=top_k,
                )
            except Exception as exc:
                st.error(f"Retrieval failed: {exc}")
                return

        if show_context:
            with st.expander(
                f"Retrieved evidence ({len(chunks)} chunks)", expanded=False
            ):
                for idx, chunk in enumerate(chunks, start=1):
                    _render_chunk(chunk, idx)

        with st.spinner("Generating grounded answer…"):
            try:
                response = answer_question(
                    question=prompt,
                    chunks=chunks,
                    model=chat_model,
                    previous_messages=st.session_state.chat_messages[-6:],
                )
            except Exception as exc:
                st.error(f"Answer generation failed: {exc}")
                return

        st.markdown(response)

    st.session_state.chat_messages.append(
        {"role": "assistant", "content": response, "chunks": chunks}
    )
