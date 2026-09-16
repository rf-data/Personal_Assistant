## run_knowledge_extraction.py
# imports
from pathlib import Path
from datetime import datetime

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_lecture import LectureContext
from src.tools_knowledge.find_knowledge import (
    analyze_and_extract_chunk,
    attach_chunk_provenance,
    build_transcript_chunks,
    enrich_chunks,
    make_visual_candidate,
    validate_extraction,
)
from src.model_knowledge.data_knowledge import (
    # ChunkKnowledgeResult,
    TranscriptKnowledgeDocument,
)
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.utils.llm_helper import configure_marvin

from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict, save_dict


def run_knowledge_extraction():

    dict_name = input("Enter name of context_file (no suffix): ")
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(
        path=dict_path,
        cls=KnowledgeContext,
        # TranscriptDocument
    )
    # context = KnowledgeContext(
    #     text = transcript,     # TranscriptDocument,
    #     target_duration = 45, # context.   # float = 45,
    #     # dur_max = context.max_duration         # float = 75
    #     overlap_segments = 2
    #     # context.overlap_segments  # : int = 2
    # )

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name, file_name=context.logger_f_name
    )

    audio_dir = Path(folder_env_vars.data_audio)

    n_paths = len(context.transcript_names)
    for idx, t_name in enumerate(context.transcript_names):
        t_path = audio_dir / t_name
        app_session.logger.info(
            "[File #%s / %s] Start extracting knowledge from '%s'",
            idx,
            n_paths,
            shorten_path(t_path),
        )

        extract = knowledge_extraction(context, t_path)
        save_dict(
            data=extract.model_dump(mode="json"),
            path=(
                audio_dir
                / f"{str(datetime.now().isoformat()).replace(':', '-').replace('T', '_')}_know_extract_results"
            ),
        )

    return None


def knowledge_extraction(
    context: KnowledgeContext, transcript_path: Path
) -> TranscriptKnowledgeDocument:
    # list[ChunkKnowledgeResult]:
    configure_marvin(context)

    transcript = load_dict(path=transcript_path, cls=TranscriptDocument)
    transcript_id = transcript.provenance.youtube_id or "tba"

    chunks = build_transcript_chunks(context, transcript)
    chunks = enrich_chunks(chunks)

    # results: dict ={}
    results: list = []
    # str, dict[str, str | ChunkKnowledgeResult]
    # chunks
    # dict = {}

    visual_candidates: list = []

    for idx, chunk in enumerate(chunks):
        result = analyze_and_extract_chunk(chunk, context.llm_model)

        if not result.analysis.relevant:
            continue

        result = attach_chunk_provenance(
            result=result,
            chunk=chunk,
        )

        result = validate_extraction(result)

        # if (
        #     result.extraction is None
        #     or not result.analysis.needs_visual_context
        #     ):
        #     result

        # else:
        #     return None

        visual_candidate = make_visual_candidate(
            result=result,
            chunk=chunk,
        )

        if visual_candidate is not None:
            visual_candidates.append(visual_candidate)

            # for expression in result.extraction.formulas:
            #     expression.verification_status = "pending"
            #     expression.verification_reason = (
            #         "Visual context required for reliable reconstruction."
            #         )

        results.append(result)
        # results.update({
        #         f"chunk_{idx:03d}": {
        #             "chunk": chunk,
        #             # .model_dump(mode="json"),
        #             "result": result,
        #             "visual_candidate": visual_candidate or []
        #             }
        #         })

    # save_dict(data=results,
    #           path=Path(f"data/{app_session.timestamp}_know_extract_results"))

    # results_all = [
    #             value for key, value in results.items()
    #             if key == result
    #             ]
    # attach_chunk_provenance
    # validate_extraction
    return TranscriptKnowledgeDocument(
        source_id=transcript_id,
        chunks=results,  # _all,
        visual_candidates=visual_candidates,
        transcript_url=transcript.provenance.source_url,
    )
    # results


if __name__ == "__main__":
    run_knowledge_extraction()
    # is True:
    #     chunk = ""
    #     hi = !

    # if doc_rep: # BaseModel subclass =
    #     hi = !

    # for chunk in chunkdoc_rep.segments:


"""
Skizze Pipeline:
JSON transcript
      ↓
LLM extraction
      ↓
Math candidates + timestamps
      ↓
ffmpeg
      ↓
frames
      ↓
formula OCR
      ↓
LLM validation / fusion
      ↓
structured knowledge JSON


1. RAW
   TranscriptSegment

2. EXTRACTION
   erkannte Begriffe, Formeln, Reaktionen, Aussagen

(
2.5 PREPARATION NORMALIZATION
    Chemical OCR / structure recognition / SMILES normalization
    Math OCR / LaTeX normalization
)

3. NORMALIZATION
   canonical entities + relations

4. KNOWLEDGE
   VectorDB + optional GraphDB

####

Bsp.-Knowledge-JSON:
{
  "name": "Cosinussatz",
  "kind": "formula",
  "latex": "b^2 = a^2 + c^2 - 2ac\\cos(\\beta)",
  "plain_text": "Quadrat von b gleich a² plus c² minus 2ac mal Cosinus beta",
  "segment_ids": [92, 93],
  "start": 245.16,
  "end": 256.16,
  "source": "transcript+visual"
}
"""
