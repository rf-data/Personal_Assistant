## find_knowledge.py
# imports
import json

# from pathlib import Path
import marvin

from src.core.memory import app_session
from src.model_knowledge.data_knowledge import (
    ChunkKnowledgeResult,
    # KnowledgeSemanticType,
    # MathExpressionType,
    TranscriptChunk,
    VisualCandidate,
)
from src.model_transcribe.data_transcribe import TranscriptSegment, TranscriptDocument
from src.core.memory_lecture import LectureContext
from src.core.retry import retry_llm_call
from src.agent.prompts.prompt_know_extract import build_knowledge_extraction_prompt
from src.core.config_knowledge import KnowledgeSettings
from src.utils.general_helper import (
    hash_text,
    load_from_cache,
    make_cache_key,
    save_to_cache,
)
# from src.utils.dict_helper import load_dict


from src.model_lecture.data_resources import (
    LectureResource,
    LectureResourceType,
    KnowledgeSourceMetadata,
    ResourceKind,
)


def build_knowledge_source_metadata(
    resource: LectureResource,
    *,
    source_id: str,
    course_id: str | None = None,
) -> KnowledgeSourceMetadata:

    resource_type = resource.resource_type

    if isinstance(resource_type, LectureResourceType):
        resource_type = resource_type.value

    return KnowledgeSourceMetadata(
        source_id=source_id,
        resource_kind=ResourceKind(resource.resource_kind),
        resource_type=resource_type,
        course_id=course_id,
        lecture_no=resource.lecture_no,
        topic=resource.topic,
        title=resource.title,
        source_url=resource.source_url,
        license=resource.license,
    )


def make_knowledge_source_metadata(
    *,
    source_id: str,
    resource_kind: ResourceKind | str,
    resource_type: str | None = None,
    course_id: str | None = None,
    lecture_no: str | None = None,
    topic: str | None = None,
    title: str | None = None,
    source_url: str | None = None,
    license: str | None = None,
) -> KnowledgeSourceMetadata:

    return KnowledgeSourceMetadata(
        source_id=source_id,
        resource_kind=ResourceKind(resource_kind),
        resource_type=resource_type,
        course_id=course_id,
        lecture_no=lecture_no,
        topic=topic,
        title=title,
        source_url=source_url,
        license=license,
    )


def build_transcript_chunks(
    cfg_know: KnowledgeSettings, transcript: TranscriptDocument
) -> list[TranscriptChunk]:

    dur_target = cfg_know.target_duration  # float = 45,
    # dur_max = context.max_duration         # float = 75
    seg_overlap = cfg_know.overlap_segments  # : int = 2

    current: list[TranscriptSegment] = []
    final: list[TranscriptChunk] = []

    for seg in transcript.segments:
        current.append(seg)

        current_dur = current[-1].end - current[0].start

        # if current_dur >= dur_max:
        #     # harter Cut

        # elif current_dur >= dur_target:
        if current_dur >= dur_target:
            # bevorzugter Cut, ggf. auf Themenwechsel warten
            final.append(
                TranscriptChunk(
                    chunk_id=f"chunk_{len(final):04d}",
                    segment_ids=[s.seg_id for s in current],
                    start=current[0].start,
                    end=current[-1].end,
                    text="\n".join(s.text for s in current),
                    n_words=sum(len(s.text.split()) for s in current),
                )
            )

            current = current[-seg_overlap:]

    if current:
        existing_ids = set(final[-1].segment_ids if final else [])
        new_ids = {s.seg_id for s in current}

        if not new_ids.issubset(existing_ids):
            final.append(
                TranscriptChunk(
                    chunk_id=f"chunk_{len(final):04d}",
                    segment_ids=[s.seg_id for s in current],
                    start=current[0].start,
                    end=current[-1].end,
                    text="\n".join(s.text for s in current),
                    n_words=sum(len(s.text.split()) for s in current),
                )
            )

    return final


def enrich_chunks(chunks: list[TranscriptChunk]) -> list[TranscriptChunk]:

    n_chunks = len(chunks)

    for idx, chunk in enumerate(chunks):
        # previous_context = (
        #                 chunks[idx-1].text
        #                 if idx > 0
        #                 else None
        #                 )
        # next_context = (
        #                 chunks[idx+1].text
        #                 if idx < n_chunks -1
        #                 else None
        #                 )

        chunk.previous_context = (
            "\n".join(chunks[idx - 1].text.splitlines()[-3:]) if idx > 0 else None
        )

        chunk.next_context = (
            "\n".join(chunks[idx + 1].text.splitlines()[:3])
            if idx < n_chunks - 1
            else None
        )

    return chunks


KNOWLEDGE_EXTRACTION_PROMPT = build_knowledge_extraction_prompt()


@marvin.fn(instructions=KNOWLEDGE_EXTRACTION_PROMPT)
def extract_knowledge(
    target_chunk: str,
    previous_context: str | None,
    next_context: str | None,
    # start: float,
    # end: float
) -> ChunkKnowledgeResult:
    ""


@retry_llm_call
def analyze_chunk_with_retry(
    chunk,
    model_name: str,
):
    return analyze_and_extract_chunk(
        chunk,
        model_name,
    )


def analyze_and_extract_chunk(
    chunk: TranscriptChunk, model_name: str
) -> ChunkKnowledgeResult:

    chunk_info = {
        "chunk_id": chunk.chunk_id,
        "segment_ids": chunk.segment_ids,
        "start": chunk.start,
        "end": chunk.end,
        "previous_context": chunk.previous_context,
        "chunk": chunk.text,
        "next_context": chunk.next_context,
    }

    # model_name = context.llm_model  # marvin_gpt-4o
    prompt_hash = hash_text(KNOWLEDGE_EXTRACTION_PROMPT)

    serialized_input = json.dumps(
        chunk_info,
        #       {
        # "previous_context": chunk.previous_context,
        # "target_chunk": chunk.text,
        # "next_context": chunk.next_context,
        # },
        sort_keys=True,
        ensure_ascii=False,
    )

    input_hash = hash_text(text=serialized_input)

    cache_key = make_cache_key(
        params={
            "task": "knowledge_extraction_v1",
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "chunk_id": chunk.chunk_id,
            # "run_name": "chapter_planning_v2",
            # "prompt_version": "prompt_v1",
            "model": model_name,
            "schema": "ChunkKnowledgeResult_v1",
            # topics_hash
        }
    )

    cache_folder = "knowledge_extraction"

    cached = load_from_cache(
        key=cache_key, folder=cache_folder, cls=ChunkKnowledgeResult
    )

    if cached is not None:
        app_session.logger.info(
            "Loading cached knowledge extraction (chunk=%s, key=%s)",
            chunk.chunk_id,
            cache_key[:12],
        )
        return cached

    result = extract_knowledge(
        target_chunk=chunk_info.get("chunk"),
        previous_context=chunk_info.get("previous_context"),
        next_context=chunk_info.get("next_context"),
        # start=chunk_info["start"],
        # end=chunk_info["end"],
    )

    save_to_cache(
        key=cache_key,
        folder=cache_folder,
        data=result.model_dump(mode="json"),
        metadata={
            "chunk_id": chunk.chunk_id,
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "model": model_name,
            "schema": "ChunkKnowledgeResult_v1",
        },
    )

    return result


def attach_chunk_provenance(
    result: ChunkKnowledgeResult,
    chunk: TranscriptChunk,
) -> ChunkKnowledgeResult:

    result.analysis.chunk_id = chunk.chunk_id

    if result.extraction is None:
        return result

    result.extraction.chunk_id = chunk.chunk_id

    for statement in result.extraction.statements:
        # if not statement.segment_ids:
        statement.segment_ids = chunk.segment_ids.copy()
        statement.start = chunk.start
        statement.end = chunk.end
        statement.source = "transcript"

    for formula in result.extraction.formulas:
        # if not formula.segment_ids:
        formula.segment_ids = chunk.segment_ids.copy()
        formula.start = chunk.start
        formula.end = chunk.end
        formula.source = "transcript"

    return result


def validate_extraction(
    result: ChunkKnowledgeResult,
) -> ChunkKnowledgeResult:

    if result.extraction is None:
        return result

    result.extraction.statements = [
        item for item in result.extraction.statements if item.text.strip()
    ]

    result.extraction.formulas = [
        item for item in result.extraction.formulas if item.plain_text.strip()
    ]

    if result.analysis.needs_visual_context:
        for formula in result.extraction.formulas:
            # formula.confidence = min(
            #     formula.confidence or 1.0,
            #     0.5,
            # )
            formula.verification_status = "pending"
            formula.verification_reason = (
                "Transcript-based reconstruction requires visual verification."
            )
    # ? TODO:
    # confidence < threshold
    # leere/absurde Formel
    # Duplikat im selben Chunk
    # Meta-Aussage statt Fachwissen

    return result


def make_visual_candidate(
    result: ChunkKnowledgeResult,
    chunk: TranscriptChunk,
) -> VisualCandidate | None:

    if result.extraction is None or not result.analysis.needs_visual_context:
        return None

    # for expression in result.extraction.formulas:
    #     expression.verification_status = "pending"
    #     expression.verification_reason = (
    #             "Visual context required for reliable reconstruction."
    #             )

    return VisualCandidate(
        chunk_id=chunk.chunk_id,
        segment_ids=chunk.segment_ids.copy(),
        start=chunk.start,
        end=chunk.end,
        reason=result.analysis.visual_reason,
    )


# def collect_visual_candidates(
#                         results: list[ChunkKnowledgeResult]
#                         ) -> TranscriptKnowledgeDocument:


#     visual_candidates: list = []

#     for result in results:
#         if result.analysis.needs_visual_context:
#             visual_candidates.append(
#                         VisualCandidate(
#                             chunk_id=result.analysis.chunk_id,
#                             segment_ids: list[int]
#                             start: float
#                             end: float
#                             reason=result.analysis.visual_reason
#                             )
#                         )

#     return TranscriptKnowledgeDocument(
#                     source_id="",
#                     chunks=results,  # : list[ChunkKnowledgeResult]
#                     visual_candidates=visual_candidates        # : list[VisualCandidate]
#                     )


def classify_chunk_knowledge(
    text_chunks: dict[str, str],
    # ) -> KnowledgeCandidate:
):
    # TODO:
    """
    TranscriptChunk
        ↓
    KnowledgeCandidate
        ↓
    relevant?
    ┌────┴────┐
    no       yes
    ↓         ↓
    skip    Extractor


    KnowledgeCandidate(
        has_knowledge=True,
        domains=["mathematics"],
        knowledge_types=[
            "formula",
            "law",
            "derivation",
        ],
        needs_visual_context=True,
        confidence=0.98,
        )

    class ChunkAnalysis(BaseModel):
        contains_math: bool
        contains_formula: bool
        formula_reconstruction_needed: bool
        visual_context_likely_needed: bool
        topic: str | None

    LLM enrichment
      ├─ sprachliche Bereinigung
      ├─ mathematischer Inhalt?
      ├─ Formeln / Symbole?
      ├─ visueller Kontext nötig?
      └─ Wissensextraktion
    """

    return


"""

"""

# def extract_chunk_knowledge() -> ExtractedKnowledge:


#     return

#         # else:
#         #     hi = !
#         start_segs = transcript.segments[idx-seg_overlap-1:idx-1]
#         current.extend(start_segs)

#         min_time = 1e5
#         max_time = 0
#         for start_s in start_segs:
#             min_time = min(min_time, start_s.start)
#             max_time = max(max_time, start_s.end)

#         current_dur = max_time - min_time
#         # (start_s.end - start_s.start)
#         continue

#     current.append(seg.text)
#     current_dur += (seg.end - seg.start)


# return
