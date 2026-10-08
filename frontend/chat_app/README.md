# Lightweight Streamlit Chat App

This app intentionally excludes parsing, chunking, bulk embedding, ChromaDB upload/admin, lecture processing and visual enrichment. Those remain offline/admin pipeline responsibilities.

The runtime app only loads an existing Chroma collection, loads the query embedding model on the first retrieval request, and creates the OpenAI client on the first answer request.

## Start

From the repository root:

```bash
streamlit run frontend/chat_app/streamlit_app.py
```

Keeping the entrypoint below `frontend/chat_app/` is intentional. If the entrypoint lived directly in `frontend/`, Streamlit could discover the existing large `frontend/pages/` multipage application again.

## Required configuration

- Existing ChromaDB collection
- The same embedding model used to build that collection
- `OPENAI_API_KEY` in Streamlit secrets or environment

## Planned next integrations

- CanonicalKnowledgeItem retrieval
- Evidence explorer
- Lecture timestamp links
- Eval dataset / Recall@k / MRR
- Quiz / flashcard generation
- Answer grounding evaluation
