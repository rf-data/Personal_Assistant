from __future__ import annotations

import streamlit as st

from chat_page import render_db_chat_page, render_upload_chat_page

st.set_page_config(
    page_title="Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROADMAP = [
    ("Canonical Knowledge", "done"),
    ("Provenance / Evidence", "done"),
    ("Complete course processing", "in_progress"),
    ("Eval dataset", "planned"),
    ("Semantic Search", "planned"),
    ("Ask the Lecture / Chat", "prototype"),
    ("Quiz / Flashcards", "planned"),
    ("Evaluation Dashboard", "planned"),
    ("Graph / Relations", "later"),
    ("Agents", "later"),
]


def render_roadmap() -> None:
    st.title("📚 Knowledge Assistant")
    st.caption(
        "Lightweight Streamlit frontend. Heavy ingestion, chunking, embedding "
        "and database upload stay outside the UI runtime."
    )

    labels = {
        "done": "✅",
        "in_progress": "🔄",
        "prototype": "🧪",
        "planned": "⬜",
        "later": "⏳",
    }

    st.subheader("Roadmap")
    for name, status in ROADMAP:
        st.markdown(f"{labels[status]} **{name}**")

    st.divider()
    st.info(
        "Planned architecture: Canonical Knowledge → Retrieval → "
        "Grounded QA / Evidence → Quiz → Evaluation."
    )


def render_placeholder(title: str, description: str, next_steps: list[str]) -> None:
    st.title(title)
    st.info(description)
    st.subheader("Planned integration")
    for item in next_steps:
        st.markdown(f"- {item}")


page = st.sidebar.radio(
    "Navigation",
    options=[
        "Chat with files",
        "Semantic search",
        "Evidence",
        "Quiz",
        "Evaluation",
        "Roadmap",
    ],
    index=0,
)

st.sidebar.caption("The processing pipeline is intentionally not part of this app.")

if page == "Chat with database files":
    render_db_chat_page()

if page == "Chat with an uploaded file":
    render_upload_chat_page()

elif page == "Semantic search":
    render_placeholder(
        "🔎 Semantic Search",
        "Placeholder for retrieval over CanonicalKnowledgeItem objects.",
        [
            "Index canonical knowledge instead of raw transcript chunks.",
            "Return knowledge_id, source_id, timestamps and evidence metadata.",
            "Add filters for course, lecture, kind and verification status.",
            "Evaluate Recall@k and MRR against the curated eval set.",
        ],
    )
elif page == "Evidence":
    render_placeholder(
        "🔗 Evidence Explorer",
        "Placeholder for inspecting the evidence behind an answer.",
        [
            "Show transcript evidence.",
            "Show visual / OCR evidence.",
            "Display support, conflict and insufficient_evidence states.",
            "Link source timestamps back to the lecture video.",
        ],
    )
elif page == "Quiz":
    render_placeholder(
        "🧠 Quiz / Flashcards",
        "Placeholder for quiz generation from canonical knowledge.",
        [
            "Generate questions only from usable knowledge.",
            "Prefer verified evidence for factual answer keys.",
            "Store knowledge_id and evidence IDs with every generated question.",
            "Add difficulty and topic filters.",
        ],
    )
elif page == "Evaluation":
    render_placeholder(
        "📊 Evaluation",
        "Placeholder for retrieval and answer-quality evaluation.",
        [
            "Load the 30–50 case gold eval set.",
            "Measure Recall@k / MRR for retrieval.",
            "Measure answer correctness and evidence grounding.",
            "Track visual correction success and transcript conflict resolution.",
        ],
    )
else:
    render_roadmap()
