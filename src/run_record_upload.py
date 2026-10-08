## run_record_upload.py
# import
from datetime import datetime

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_lecture import LectureContext

from src.model_rag.data_records import RAGRecord
from src.model_transcribe.data_transcribe import (
    # TranscriptSegment,
    TranscriptDocument,
)

from src.tools_knowledge.find_knowledge import build_transcript_chunks

from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict

"""
                  INPUT
                    │
        ┌───────────┴───────────┐
        │                       │
 TranscriptDocument     LectureKnowledgeDocument
        │                       │
build_transcript_chunks()       │
        │                       │
        ▼                       ▼
 TranscriptChunk        CanonicalStatement
        │                       │
        └───────────┬───────────┘
                    ▼
             build_rag_records()
                    │
                    ▼
                embed_texts()
                    │
                    ▼
              QdrantPoint[]
                    │
                    ▼
            upload_to_qdrant()
"""


def run_record_upload():
    dict_name = input("Enter name of context_file (no suffix): ")
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(
        path=dict_path,
        cls=LectureContext,
        # TranscriptDocument
    )

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name="record_upload",
        # context.logger_name,
        file_name=f"record_upload_{app_session.timestamp}",
        # context.logger_f_name
    )

    # audio_dir = Path(folder_env_vars.data_audio)
    context.lecture_root = (
        folder_env_vars.data_lectures
        / context.provider  # loviscach"
        / context.course_id  # "mathe_1"
    )

    # transcripts = context.cfg_knowledge.transcript_names
    # if not transcripts:
    transcript_folder = (
        context.lecture_root  # "mathe_1"
        / "transcripts"
    )

    transcripts = sorted(
        path
        for path in transcript_folder.rglob("*.json")
        # if is_regular_lecture(path)
    )

    n_paths = len(transcripts)

    for idx, t_path in enumerate(transcripts):
        # t_path = audio_dir / t_name

        # if f"{t_path.stem}_know_extract" in extract_files:
        #     app_session.logger.info(
        #         "[SKIP EXTRACTION] Knowledge from transcript '%s' has already been extracted",
        #         shorten_path(t_path),
        #     )
        #     continue

        app_session.logger.info(
            "[File #%s / %s] Start building RAG records from '%s'",
            idx,
            n_paths,
            shorten_path(t_path),
        )

        record_upload(t_path, context)

    return None


def build_rag_records_from_transcript(
    transcript: TranscriptDocument,
    # path: Path,
    context: LectureContext,
) -> list[RAGRecord]:

    records: list[RAGRecord] = []

    # transcript = load_dict(transcript_path, cls=TranscriptDocument)
    transcript_chunks = build_transcript_chunks(context.cfg_know, transcript)

    for chunk in transcript_chunks:
        records.append(
            RAGRecord(
                record_id="",  # course_id::course_part_id::statement_id
                text=chunk.text,
                record_type="transcript_chunk",
                source="",  # source_meta
                metadata={
                    "statement_id": "",
                    "semantic_type": "",
                    "start": "",
                    "end": "",
                    "confidence": "",
                    "verification": "",
                },
            )
        )

    return records


def build_rag_records_from_knowledge(
    document: LectureKnowledgeDocument,
    source_metadata: KnowledgeSourceMetadata,
) -> list[RAGRecord]:

    records: list[RAGRecord] = []

    # source_id = transcript_path.name.removesuffix(".json")

    # know_path = context.lecture_root / f"knowledge/{source_id}_know_canonical.json"
    # know_canonical = load_dict(know_path, cls=LectureKnowledgeDocument)

    for statement in document.statements:
        starts = [evidence.start for evidence in statement.evidence]

        ends = [evidence.end for evidence in statement.evidence]

        record = RAGRecord(
            record_id=(f"{source_metadata.source_id}::{statement.statement_id}"),
            text=statement.text,
            record_type="knowledge_statement",
            source=source_metadata,
            metadata={
                "statement_id": statement.statement_id,
                "semantic_type": statement.semantic_type.value,
                "topic": statement.topic,
                "start": min(starts) if starts else None,
                "end": max(ends) if ends else None,
                "needs_review": statement.needs_review,
                "review_reason": statement.review_reason,
                "llm_confidence": statement.llm_confidence,
                "source_statement_ids": (statement.source_statement_ids),
            },
        )

        records.append(record)

    return records


def build_formula_rag_records(
    document: LectureKnowledgeDocument,
    source_metadata: KnowledgeSourceMetadata,
) -> list[RAGRecord]:

    records: list[RAGRecord] = []

    for formula in document.formulas:
        starts = [evidence.start for evidence in formula.evidence]

        ends = [evidence.end for evidence in formula.evidence]

        if formula.latex:
            text = (
                f"{formula.name + ': ' if formula.name else ''}"
                f"{formula.plain_text}\n"
                f"LaTeX: {formula.latex}"
            )
        else:
            text = formula.plain_text

        records.append(
            RAGRecord(
                record_id=(f"{source_metadata.source_id}::{formula.expression_id}"),
                text=text,
                record_type="formula",
                source=source_metadata,
                metadata={
                    "expression_id": (formula.expression_id),
                    "expression_type": (formula.expression_type.value),
                    "name": formula.name,
                    "latex": formula.latex,
                    "verification_status": (formula.verification_status),
                    "verification_reasons": (formula.verification_reasons),
                    "start": (min(starts) if starts else None),
                    "end": (max(ends) if ends else None),
                    "llm_confidence": (formula.llm_confidence),
                },
            )
        )

    return records


def build_knowledge_rag_records(
    document: LectureKnowledgeDocument,
    source_metadata: KnowledgeSourceMetadata,
) -> list[RAGRecord]:

    records = []

    records.extend(
        build_statement_rag_records(
            document=document,
            source_metadata=source_metadata,
        )
    )

    records.extend(
        build_formula_rag_records(
            document=document,
            source_metadata=source_metadata,
        )
    )

    return records


def rag_record_to_payload(
    record: RAGRecord,
) -> dict:

    source = record.source

    return {
        "text": record.text,
        "record_type": record.record_type,
        # wichtige Filterfelder flach
        "source_id": source.source_id,
        "course_id": source.course_id,
        "resource_kind": source.resource_kind.value,
        "resource_type": source.resource_type,
        "lecture_no": source.lecture_no,
        "topic": source.topic,
        "title": source.title,
        # komplette Provenance trotzdem erhalten
        "source": source.model_dump(
            mode="json",
            exclude_none=True,
        ),
        **{key: value for key, value in record.metadata.items() if value is not None},
    }


def record_upload(transcript_path, context):

    source_meta = build_knowledge_source_metadata(
        resource=resource,
        source_id=knowledge_document.source_id,
        course_id="mathe_1",
    )

    know_records = build_knowledge_rag_records()

    transcript_records = build_transcript_rag_records()

    rag_record_to_payload()

    return
