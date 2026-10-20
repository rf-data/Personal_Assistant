# Lightweight Streamlit Chat App

This app intentionally excludes parsing, chunking, bulk embedding, ChromaDB upload/admin, lecture processing and visual enrichment. Those remain offline/admin pipeline responsibilities.

The runtime app only loads an existing Chroma collection, loads the query embedding model on the first retrieval request, and creates the OpenAI client on the first answer request.

## Historical entrypoint status

The former command referenced `frontend/chat_app/streamlit_app.py`, which is
absent. The actual page functions live in `chat_page.py`; root `st_chat_app.py`
imports `chat_page` without a package-qualified path. A working standalone start
has not been established by this audit. No replacement launch command is
advertised as tested. The canonical UI owner is
[personal-assistant-ui](https://github.com/rf-data/personal-assistant-ui).
These backend files remain intact because the root runner still references them.

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
