from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st
from tiktoken import encoding_for_model

from src.core.config import ChunkSettings, folder_env_vars
from src.core.memory import ParseContext, app_session
from src.core.memory_lecture import LectureContext
from src.core.memory_parsing import PARSER_BACKEND
from src.model_lecture.data_resources import (
    LectureMedia,
    ResourceAction,
)
from src.run_knowledge_extraction import knowledge_extraction
from src.tools_lecture.process_lecture import (
    build_document_parse_context,
    execute_media_action,
)
from src.tools_parsing.parse_document import parse_document
from src.tools_rag.chunk import chunk_text
from src.tools_rag.create_embeds import embed_text
from src.utils.df_helper import save_df_to_parquet
from src.utils.dict_helper import load_dict, save_dict
from src.utils.path_helper import shorten_path
from src.utils.streamlit_helper import st_file_preview


DOCUMENT_SUFFIXES = {".pdf", ".docx", ".md", ".txt"}
MEDIA_SUFFIXES = {".wav", ".mp3", ".m4a", ".mp4", ".mkv", ".webm"}


def _context_files() -> list[Path]:
    return sorted(folder_env_vars.config_dir.glob("context_*.json"))


def _load_lecture_context(path: Path) -> LectureContext:
    return load_dict(path=path, cls=LectureContext)


def _lecture_root(context: LectureContext) -> Path:
    return folder_env_vars.data_lectures / context.provider / context.course_id


def _files(
    root: Path,
    *,
    suffixes: set[str] | None = None,
    pattern: str = "*",
) -> list[Path]:
    if not root.exists():
        return []

    paths = [path for path in root.rglob(pattern) if path.is_file()]

    if suffixes is not None:
        paths = [path for path in paths if path.suffix.lower() in suffixes]

    return sorted(paths)


def _artifact_inventory(root: Path) -> pd.DataFrame:
    groups = {
        "Documents": _files(root / "documents", suffixes=DOCUMENT_SUFFIXES),
        "Media": _files(root, suffixes=MEDIA_SUFFIXES),
        "Transcripts": _files(root / "transcripts", suffixes={".json"}),
        "Parsed JSON": _files(root / "parsed", suffixes={".json"}),
        "Parsed Markdown": _files(root / "parsed", suffixes={".md"}),
        "Knowledge": _files(root / "knowledge", suffixes={".json"}),
        "Chunks": _files(root, pattern="*_chunked.parquet"),
        "Embeddings": _files(root, pattern="*_embed.parquet"),
    }

    return pd.DataFrame(
        [
            {
                "stage": name,
                "count": len(paths),
                "latest": (
                    max(paths, key=lambda p: p.stat().st_mtime).name if paths else None
                ),
            }
            for name, paths in groups.items()
        ]
    )


def _ensure_encoder() -> None:
    if app_session.encoder is None:
        app_session.encoder = encoding_for_model("gpt-4o-mini")


def _default_chunk_context() -> ParseContext:
    _ensure_encoder()

    context = ParseContext(
        chunk_settings=ChunkSettings(
            container_types=[
                "heading",
                "paragraph",
                "code",
                "line_group",
                "bullet_list",
            ],
            spacy_language="de_core_news_sm",
            max_tokens=180,
            overlap_sentences=1,
            transformer_model="intfloat/multilingual-e5-base",
            batch_size=16,
        )
    )
    context.encoder = app_session.encoder
    return context


def _parse_documents(
    files: Iterable[Path],
    *,
    lecture_context: LectureContext,
    parser_backend: PARSER_BACKEND,
) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []

    for file_path in files:
        try:
            parse_context = build_document_parse_context(
                resource=type(
                    "_Resource",
                    (),
                    {
                        "local_path": file_path,
                        "title": file_path.stem,
                    },
                )(),
                course_root=_lecture_root(lecture_context),
            )
            parse_context.parser_backend = parser_backend

            parse_document(
                file_path=file_path,
                parse_context=parse_context,
            )
            results.append((file_path, "done"))

        except Exception as exc:
            results.append((file_path, f"failed: {exc}"))

    return results


def _transcribe_media(
    files: Iterable[Path],
    *,
    lecture_context: LectureContext,
) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []
    root = _lecture_root(lecture_context)

    for file_path in files:
        try:
            media_type = (
                "audio"
                if file_path.suffix.lower()
                in {
                    ".wav",
                    ".mp3",
                    ".m4a",
                }
                else "video"
            )

            resource = LectureMedia(
                title=file_path.stem,
                source_url=None,
                local_path=file_path,
                downloaded=True,
                media_type=media_type,
                lecture_blocks=[],
            )

            execute_media_action(
                resource=resource,
                action=ResourceAction.TRANSCRIBE,
                course_root=root,
            )
            results.append((file_path, "done"))

        except Exception as exc:
            results.append((file_path, f"failed: {exc}"))

    return results


def _extract_knowledge(
    transcript_paths: Iterable[Path],
    *,
    lecture_context: LectureContext,
) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []
    root = _lecture_root(lecture_context)
    knowledge_dir = root / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    for transcript_path in transcript_paths:
        try:
            document = knowledge_extraction(
                context=lecture_context,
                transcript_path=transcript_path,
            )

            save_dict(
                data=document.model_dump(mode="json"),
                path=knowledge_dir / f"{transcript_path.stem}_know_extract",
            )

            results.append((transcript_path, "done"))

        except Exception as exc:
            results.append((transcript_path, f"failed: {exc}"))

    return results


def _chunk_and_embed_info_files(
    info_paths: Iterable[Path],
    *,
    save_embeddings: bool,
) -> list[tuple[Path, str, int | None]]:
    results: list[tuple[Path, str, int | None]] = []
    chunk_context = _default_chunk_context()

    for info_path in info_paths:
        try:
            df_chunk = chunk_text(
                f_path=str(info_path),
                parse_context=chunk_context,
            )

            save_df_to_parquet(
                df=df_chunk,
                f_name=info_path.stem.replace("_info", "_chunked"),
                folder=info_path.parent,
            )

            if save_embeddings:
                df_embed = embed_text(
                    df_embed=df_chunk.copy(),
                    chunk_context=chunk_context,
                )

                save_df_to_parquet(
                    df=df_embed,
                    f_name=info_path.stem.replace("_info", "_embed"),
                    folder=info_path.parent,
                )

            results.append((info_path, "done", len(df_chunk)))

        except Exception as exc:
            results.append((info_path, f"failed: {exc}", None))

    return results


def _result_table(rows: list[tuple]) -> None:
    if not rows:
        return

    n_cols = len(rows[0])

    if n_cols == 2:
        df = pd.DataFrame(rows, columns=["file", "status"])
    elif n_cols == 3:
        df = pd.DataFrame(rows, columns=["file", "status", "n_chunks"])
    else:
        df = pd.DataFrame(rows)

    if "file" in df:
        df["file"] = df["file"].map(str)

    st.dataframe(df, width="stretch", hide_index=True)


def show() -> None:
    st.title("🛠️ Ingestion Admin")
    st.caption(
        "Prepare lecture resources for retrieval: parsing, transcription, "
        "knowledge extraction, chunking and embeddings."
    )

    context_files = _context_files()

    if not context_files:
        st.error(f"No context_*.json found in {folder_env_vars.config_dir}.")
        return

    selected_context_path = st.selectbox(
        "Lecture context",
        options=context_files,
        format_func=lambda path: path.name,
    )

    context = _load_lecture_context(selected_context_path)
    root = _lecture_root(context)

    st.session_state["ingestion_context_path"] = str(selected_context_path)
    st.session_state["ingestion_course_root"] = str(root)

    top_left, top_mid, top_right = st.columns(3)
    top_left.metric("Provider", context.provider or "—")
    top_mid.metric("Course", context.course_id or "—")
    top_right.metric("Root exists", "yes" if root.exists() else "no")

    st.code(str(root), language=None)

    tab_overview, tab_parse, tab_transcribe, tab_knowledge, tab_rag, tab_db = st.tabs(
        [
            "Overview",
            "Parse",
            "Transcribe",
            "Knowledge",
            "Chunk & Embed",
            "DB Upload",
        ]
    )

    with tab_overview:
        st.subheader("Pipeline inventory")
        st.dataframe(
            _artifact_inventory(root),
            width="stretch",
            hide_index=True,
        )

        with st.expander("Course folders"):
            for folder_name in [
                "documents",
                "transcripts",
                "parsed",
                "knowledge",
            ]:
                path = root / folder_name
                st.write(
                    f"**{folder_name}:** "
                    f"{shorten_path(path, n=4) if path.exists() else 'missing'}"
                )

    with tab_parse:
        st.subheader("Parse documents")

        documents = _files(
            root / "documents",
            suffixes=DOCUMENT_SUFFIXES,
        )

        selected_docs = st.multiselect(
            "Documents",
            options=documents,
            format_func=lambda path: shorten_path(path, n=3),
            key="admin_parse_documents",
        )

        parser_backend = st.selectbox(
            "Parser backend",
            options=list(PARSER_BACKEND),
            format_func=lambda value: value.value,
            index=(
                list(PARSER_BACKEND).index(context.parser_backend)
                if context.parser_backend in list(PARSER_BACKEND)
                else 0
            ),
        )

        if len(selected_docs) == 1:
            with st.expander("Preview"):
                st_file_preview(selected_docs[0])

        st.warning(
            "Parsing can be CPU/RAM intensive. Start with a single document "
            "when testing a new parser configuration."
        )

        if st.button(
            "Parse selected documents",
            disabled=not selected_docs,
            type="primary",
        ):
            with st.status("Parsing documents...", expanded=True) as status:
                rows = _parse_documents(
                    selected_docs,
                    lecture_context=context,
                    parser_backend=parser_backend,
                )
                _result_table(rows)

                failed = [row for row in rows if row[1] != "done"]
                status.update(
                    label=(
                        "Parsing finished"
                        if not failed
                        else f"Parsing finished with {len(failed)} failure(s)"
                    ),
                    state="complete" if not failed else "error",
                )

    with tab_transcribe:
        st.subheader("Transcribe local media")

        media_files = _files(root, suffixes=MEDIA_SUFFIXES)

        # Avoid offering already generated fragments from common output folders.
        media_files = [
            path
            for path in media_files
            if "transcripts" not in path.parts and "frames" not in path.parts
        ]

        selected_media = st.multiselect(
            "Audio / video files",
            options=media_files,
            format_func=lambda path: shorten_path(path, n=3),
            key="admin_transcribe_media",
        )

        st.info(
            "This uses the existing transcription configuration from "
            "`cfg_lecture_transcribe`."
        )

        if st.button(
            "Transcribe selected media",
            disabled=not selected_media,
            type="primary",
        ):
            with st.status("Transcribing...", expanded=True) as status:
                rows = _transcribe_media(
                    selected_media,
                    lecture_context=context,
                )
                _result_table(rows)

                failed = [row for row in rows if row[1] != "done"]
                status.update(
                    label=(
                        "Transcription finished"
                        if not failed
                        else f"Transcription finished with {len(failed)} failure(s)"
                    ),
                    state="complete" if not failed else "error",
                )

    with tab_knowledge:
        st.subheader("Extract knowledge from transcripts")

        transcripts = _files(
            root / "transcripts",
            suffixes={".json"},
        )

        knowledge_stems = {
            path.name.replace("_know_extract.json", "")
            for path in _files(
                root / "knowledge",
                suffixes={".json"},
            )
            if path.name.endswith("_know_extract.json")
        }

        only_missing = st.toggle(
            "Show only transcripts without knowledge extract",
            value=True,
        )

        if only_missing:
            transcripts = [
                path for path in transcripts if path.stem not in knowledge_stems
            ]

        selected_transcripts = st.multiselect(
            "Transcripts",
            options=transcripts,
            format_func=lambda path: shorten_path(path, n=3),
            key="admin_knowledge_transcripts",
        )

        if context.cfg_knowledge is None:
            st.error(
                "The selected LectureContext has no cfg_knowledge. "
                "Knowledge extraction cannot run."
            )
        else:
            st.write(
                {
                    "model": context.cfg_knowledge.llm_model,
                    "target_duration": context.cfg_knowledge.target_duration,
                    "overlap_segments": context.cfg_knowledge.overlap_segments,
                }
            )

        if st.button(
            "Extract knowledge",
            disabled=(not selected_transcripts or context.cfg_knowledge is None),
            type="primary",
        ):
            with st.status(
                "Extracting knowledge...",
                expanded=True,
            ) as status:
                rows = _extract_knowledge(
                    selected_transcripts,
                    lecture_context=context,
                )
                _result_table(rows)

                failed = [row for row in rows if row[1] != "done"]
                status.update(
                    label=(
                        "Knowledge extraction finished"
                        if not failed
                        else (
                            "Knowledge extraction finished with "
                            f"{len(failed)} failure(s)"
                        )
                    ),
                    state="complete" if not failed else "error",
                )

    with tab_rag:
        st.subheader("Chunk & embed parsed documents")

        st.caption(
            "This step intentionally does not call `run_chunk_and_embed()`, "
            "because that runner still uploads to ChromaDB."
        )

        info_files = _files(
            root,
            suffixes={".json"},
            pattern="*_info.json",
        )

        selected_info = st.multiselect(
            "Parsed *_info.json files",
            options=info_files,
            format_func=lambda path: shorten_path(path, n=4),
            key="admin_chunk_info",
        )

        chunk_context = _default_chunk_context()

        c1, c2, c3 = st.columns(3)
        chunk_context.chunk_settings.max_tokens = c1.number_input(
            "Max tokens",
            min_value=32,
            max_value=2048,
            value=180,
            step=16,
        )
        chunk_context.chunk_settings.overlap_sentences = c2.number_input(
            "Sentence overlap",
            min_value=0,
            max_value=10,
            value=1,
        )
        chunk_context.chunk_settings.batch_size = c3.number_input(
            "Embedding batch size",
            min_value=1,
            max_value=256,
            value=16,
        )

        create_embeddings = st.toggle(
            "Create embeddings",
            value=True,
        )

        st.code(
            chunk_context.chunk_settings.transformer_model,
            language=None,
        )

        if st.button(
            "Chunk selected files",
            disabled=not selected_info,
            type="primary",
        ):
            # Pass the UI settings into the helper's default context.
            # The helper itself constructs an equivalent context, so persist
            # the selected values in app_session for this run.
            original_chunk_settings = app_session.chunk_settings
            app_session.chunk_settings = chunk_context.chunk_settings

            try:
                with st.status(
                    "Chunking / embedding...",
                    expanded=True,
                ) as status:
                    rows = []
                    # Use the configured context directly here so the UI values
                    # are honored.
                    for info_path in selected_info:
                        try:
                            chunk_context.save_name = info_path.stem
                            chunk_context.save_folder = info_path.parent

                            df_chunk = chunk_text(
                                f_path=str(info_path),
                                parse_context=chunk_context,
                            )

                            save_df_to_parquet(
                                df=df_chunk,
                                f_name=info_path.stem.replace(
                                    "_info",
                                    "_chunked",
                                ),
                                folder=info_path.parent,
                            )

                            if create_embeddings:
                                df_embed = embed_text(
                                    df_embed=df_chunk.copy(),
                                    chunk_context=chunk_context,
                                )

                                save_df_to_parquet(
                                    df=df_embed,
                                    f_name=info_path.stem.replace(
                                        "_info",
                                        "_embed",
                                    ),
                                    folder=info_path.parent,
                                )

                            rows.append((info_path, "done", len(df_chunk)))

                        except Exception as exc:
                            rows.append(
                                (
                                    info_path,
                                    f"failed: {exc}",
                                    None,
                                )
                            )

                    _result_table(rows)
                    failed = [row for row in rows if row[1] != "done"]
                    status.update(
                        label=(
                            "Chunking / embedding finished"
                            if not failed
                            else (
                                "Chunking / embedding finished with "
                                f"{len(failed)} failure(s)"
                            )
                        ),
                        state=("complete" if not failed else "error"),
                    )
            finally:
                app_session.chunk_settings = original_chunk_settings

        with st.expander("Prepared embedding files"):
            embed_files = _files(
                root,
                pattern="*_embed.parquet",
            )
            for path in embed_files:
                st.write(shorten_path(path, n=4))

    with tab_db:
        st.subheader("Qdrant upload")

        st.info(
            "The UI endpoint is intentionally not wired yet. "
            "The next implementation step should consume DB-independent "
            "`RAGRecord` objects and hand them to a Qdrant adapter."
        )

        prepared_embeddings = _files(
            root,
            pattern="*_embed.parquet",
        )
        knowledge_files = _files(
            root / "knowledge",
            suffixes={".json"},
        )

        c1, c2 = st.columns(2)
        c1.metric(
            "Embedding artifacts",
            len(prepared_embeddings),
        )
        c2.metric(
            "Knowledge artifacts",
            len(knowledge_files),
        )

        st.button(
            "Upload to Qdrant",
            disabled=True,
            help=("Enable after the RAGRecord/Qdrant adapter has been implemented."),
        )
