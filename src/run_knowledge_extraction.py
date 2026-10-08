## run_knowledge_extraction.py
# imports
from pathlib import Path
from datetime import datetime
import typer

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_lecture import LectureContext
from src.tools_knowledge.find_knowledge import (
    analyze_chunk_with_retry,
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
from src.tools_lecture.prepare_loviscach import extract_media_id
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.utils.llm_helper import configure_marvin

from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict, save_dict


app = typer.Typer()


@app.command()
def main(context_name: str = typer.Option(..., "--context", "-c")):
    run_knowledge_extraction(
        context_name=context_name,
    )


def run_knowledge_extraction(context_name: str) -> None:

    dict_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(
        path=dict_path,
        cls=LectureContext,
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
        name="know_extract",
        # context.logger_name,
        file_name=f"know_extract_{app_session.timestamp}",
        # context.logger_f_name
    )

    # audio_dir = Path(folder_env_vars.data_audio)
    lecture_root = (
        folder_env_vars.data_lectures
        / context.provider  # loviscach"
        / context.course_id  # "mathe_1"
    )

    # transcripts = context.cfg_knowledge.transcript_names
    # if not transcripts:
    transcript_folder = (
        lecture_root  # "mathe_1"
        / "transcripts"
    )

    transcripts = sorted(
        path
        for path in transcript_folder.rglob("*.json")
        # if is_regular_lecture(path)
    )

    extract_folder = lecture_root / "knowledge"
    extract_files = [
        ext.stem
        for ext in extract_folder.rglob("*.json")
        if ext.name.rstrip(".json").endswith("_know_extract")
        # stem.endswith("_know_extract")
    ]
    n_paths = len(transcripts)

    app_session.logger.info(
        "Found %s transcripts and %s knowledge extracts", n_paths, len(extract_files)
    )

    for idx, t_path in enumerate(transcripts):
        # t_path = audio_dir / t_name

        if f"{t_path.stem}_know_extract" in extract_files:
            app_session.logger.info(
                "[SKIP EXTRACTION] Knowledge from transcript '%s' has already been extracted",
                shorten_path(t_path),
            )
            continue

        app_session.logger.info(
            "[File #%s / %s] Start extracting knowledge from '%s'",
            idx,
            n_paths,
            shorten_path(t_path),
        )

        try:
            extract = knowledge_extraction(context, t_path)
            save_dict(
                data=extract.model_dump(mode="json"),
                path=(
                    lecture_root
                    / f"knowledge/{t_path.name.removesuffix('.json')}_know_extract"
                    # _{context.course_id}
                ),  # str(datetime.now().isoformat()).replace(':', '-').replace('T', '_')
            )

        except:
            app_session.logger.exception(
                "Knowledge extraction finally failed for '%s'",
                t_path,
            )
            continue

    return None


import re


def is_regular_lecture(
    path: Path,
) -> bool:

    index = path.stem.split("_", 1)[0]

    return bool(
        re.fullmatch(
            r"\d+(?:\.\d+)*",
            index,
        )
    )


def knowledge_extraction(
    context: LectureContext, transcript_path: Path
) -> TranscriptKnowledgeDocument:

    cfg_know = context.cfg_knowledge
    # list[ChunkKnowledgeResult]:
    configure_marvin(cfg_know)

    transcript = load_dict(path=transcript_path, cls=TranscriptDocument)

    media_id = None
    transcript_url = None

    transcript_url = transcript.provenance.source_url if transcript.provenance else None

    media_id = extract_media_id(transcript_url)

    source_id = transcript_path.name.removesuffix(".json")

    chunks = build_transcript_chunks(cfg_know, transcript)
    chunks = enrich_chunks(chunks)

    # results: dict ={}
    results: list = []
    # str, dict[str, str | ChunkKnowledgeResult]
    # chunks
    # dict = {}

    visual_candidates: list = []

    # lecture_compile

    for _, chunk in enumerate(chunks):
        result = analyze_chunk_with_retry(
            chunk,
            cfg_know.llm_model,
        )

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
        source_id=source_id,
        transcript_url=transcript_url,
        media_id=media_id,
        chunks=results,  # _all,
        visual_candidates=visual_candidates,
    )
    # results


if __name__ == "__main__":
    app()
    # typer.run(run_knowledge_extraction)
