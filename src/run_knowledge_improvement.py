## run_visual_enrichment.py
# imports
from pathlib import Path
from datetime import datetime
import gc

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_lecture import LectureContext

from src.tools_lecture.prepare_loviscach import extract_media_id
from src.tools_knowledge.rebuild_knowledge import (
    # clean_frame_times,
    # add_frame_timestamps,
    analyze_visual_with_retry,
    analyze_visual_batch_locally,
    apply_local_visual_verification,
    build_visual_batches,
    compile_download_windows,
    finalize_visual_result,
    select_visual_verification_targets,
    # image_text_conversion,
)
from src.tools_transcribe.extract_video import (
    download_sections_with_retry,
    extract_additional_frames,
    extract_all_frames,
    prepare_local_visual_sections,
    select_distinct_frames,
)
from src.model_knowledge.data_knowledge import (
    LocalVisualBatchResult,
    LectureKnowledgeDocument,
    TranscriptKnowledgeDocument,
    VisualCandidate,
    VisualKnowledgeResult,
)
# from src.model_transcribe.data_transcribe import TranscriptDocument
# from src.utils.llm_helper import configure_marvin

# from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict, save_dict
from src.utils.path_helper import shorten_path


def validate_knowledge_context(
    context: LectureContext,
) -> None:

    cfg = context.cfg_knowledge

    if cfg.visual_api_fallback and not cfg.visual_model.strip():
        raise ValueError("visual_model is required when visual_api_fallback=True.")

    if cfg.visual_batch_size <= 0:
        raise ValueError("visual_batch_size must be > 0.")

    if cfg.visual_batch_overlap >= cfg.visual_batch_size:
        raise ValueError("visual_batch_overlap must be smaller than visual_batch_size.")


def run_visual_enrichment():

    import sys

    context_name = "lecture_compile"
    # input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(path=context_path, cls=LectureContext)

    validate_knowledge_context(context)

    context.cfg_knowledge.cfg_download.cookie_file = folder_env_vars.yt_cookies

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_f_name,
        file_name=f"{context.logger_f_name}_{app_session.timestamp}",
    )

    context.lecture_root = (
        folder_env_vars.data_lectures / f"{context.provider}" / f"{context.course_id}"
    )

    yt_urls = load_dict(
        path="/home/robfra/0_Portfolio_Projekte/gmp_compliance/src/mathe_vorkurs_2013_urls.json"
    )

    know_folder = context.lecture_root / "knowledge"
    know_files = [file for file in know_folder.rglob("*_know_consol.json")]

    app_session.logger.info(
        "Found %s 'consolidated knowledge' files in in '%s'",
        len(know_files),
        shorten_path(know_folder),
    )

    for f_path in sorted(know_files):
        # ["003_003_004_erste_zweite_kubische_binomische_Formel;_
        # minus_mal_minus_know_consol"]:

        # know_path = (
        #     context.lecture_root
        #     / f"knowledge/{know_name}.json"
        #     )

        # if Path(str(f_path).replace("_consol", "_visual")).exists():
        #     # .stem.startswith("003_003"):
        #     app_session.logger.info(
        #         "[SKIPPING] File '%s' already processed", f_path.name
        #     )
        #     continue

        doc = load_dict(
            path=f_path,
            # Path(f"{context.save_folder}/{context.know_extract_file}.json"),
            cls=LectureKnowledgeDocument,
            # TranscriptKnowledgeDocument
        )

        if doc.transcript_url is None and context.course_id == "mathe_vorkurs":
            url_new = yt_urls.get(f_path.stem.split("_")[0], []).get("url", None)

            if not url_new:
                app_session.logger.error(
                    "No url available --> skipping visual enrichment of file '%s'",
                    f_path.stem,
                )
                continue

            doc.transcript_url = url_new

        if doc.media_id is None:
            # not getattr(doc, "media_id") or
            doc.media_id = extract_media_id(doc.transcript_url)

            # "https://www.youtube.com/watch?v=KeCd7fs7rtc"
        #     "003": {
        # "lesson_code": "003_004",
        # "title": "003_004 erste, zweite, kubische binomische Formel; minus mal minus",
        # "video_id": "KeCd7fs7rtc",
        # "url": """
        src_id = "_".join(f_path.name.split("_")[:-2])

        print("'Source_id': ", src_id)

        # media_path = find_local_media_path(
        #     source_id=src_id,
        #     search_root=(
        #         folder_env_vars.data_lectures
        #         / f"loviscach/mathe_vorkurs/audio"
        #         )
        #     )
        # (
        #         folder_env_vars.data_lectures
        #         / f"loviscach/mathe_vorkurs/audio"
        #         / "003_003_004 erste, zweite, kubische binomische Formel; minus mal minus.webm"
        # )
        #

        app_session.logger.info(
            "Knowledge file: %s",
            f_path.name,
        )

        # app_session.logger.info(
        #     "Local media: %s",
        #     media_path,
        # )
        # (
        #     /{}.webm"
        #     )
        # url = know_extract.transcript_url

        # visual_candidates: set = set()

        # for res in results.values():
        #     visual_candidates.add(res["visual_candidate"])

        # visual_candidates = know_extract.visual_candidates
        # app_session.logger.info(
        #     "Found %s visual candidates in media '%s'", len(visual_candidates), url
        # )

        # sys.exit(0)

        # if media_path:
        visual_enrichment(document=doc, context=context)
        # , media_path=media_path)

        # del result
        gc.collect()

    return None


VIDEO_SUFFIXES = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
}


def find_local_media_path(
    source_id: str,
    search_root: Path,
) -> Path:

    search_root = Path(search_root)

    app_session.logger.info(
        "Start looking for '%s' in folder '%s'", source_id, search_root
    )

    if not search_root.is_dir():
        raise NotADirectoryError(f"Media search root does not exist: {search_root}")

    candidates: list[Path] = []

    for path in search_root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in VIDEO_SUFFIXES:
            continue

        if path.stem == source_id:
            candidates.append(path)

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        raise ValueError(
            "Multiple media files found for "
            f"source_id='{source_id}':\n" + "\n".join(str(path) for path in candidates)
        )

    # fallback: filenames sometimes contain
    # additional suffixes / prefixes
    loose_matches: list[Path] = []

    source_normalized = source_id.casefold().replace(" ", "_")

    for path in search_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in VIDEO_SUFFIXES:
            continue

        stem_normalized = path.stem.casefold().replace(" ", "_").replace(",", "")

        if source_normalized in stem_normalized or stem_normalized in source_normalized:
            loose_matches.append(path)

    if len(loose_matches) == 1:
        return loose_matches[0]

    # save_dict(
    #     data=[f for f in search_root.rglob("*")],
    #     path="/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/loviscach/know/audio_files"
    #     )

    raise FileNotFoundError(
        "Could not uniquely determine local media "
        f"for source_id='{source_id}'.\n"
        f"Search root: {search_root}\n"
        f"Matches: {loose_matches}"
    )


# source_id='003_003_004_erste_zweite_kubische_binomische_
# Formel;_minus_mal_minus'


def visual_enrichment(
    document: LectureKnowledgeDocument,
    context: LectureContext,
    *,
    media_path: Path | None = None,
) -> LectureKnowledgeDocument:
    # -> TranscriptKnowledgeDocument:
    # list[ChunkKnowledgeResult]:

    cfg_knowledge = context.cfg_knowledge
    cfg_download = cfg_knowledge.cfg_download
    cfg_screenshot = cfg_knowledge.cfg_screenshot

    # ========================================================
    # SELECT TARGETS
    # ========================================================
    targets = select_visual_verification_targets(document)

    app_session.logger.info(
        "Selected %d visual verification targets",
        len(targets),
    )

    if not targets:
        app_session.logger.info("No visual verification needed.")

        save_dict(
            data=document.model_dump(mode="json"),
            path=(
                Path(context.lecture_root)
                / (f"knowledge/{document.source_id}_know_enriched")
            ),
        )

        return document

    # candidates = know_extract.visual_candidates
    # if candidates:
    #     app_session.logger.info(
    #         "Visual candidate range: %.2f - %.2f s (%s candidates)",
    #         min(c.start for c in candidates),
    #         max(c.end for c in candidates),
    #         len(candidates),
    #     )

    app_session.logger.info(
        ("VISUAL MEDIA SOURCE | source_id=%s | url=%s | media_id=%s"),
        document.source_id,
        document.transcript_url,
        document.media_id,
    )

    for target in targets:
        app_session.logger.info(
            ("Visual target: %s | %.2f - %.2f | statement=%s | formulas=%s"),
            target.target_id,
            target.start,
            target.end,
            target.statement_ids,
            target.expression_ids,
        )

    down_windows = compile_download_windows(
        candidates=targets, merge_gap=cfg_screenshot.merge_gap
    )

    app_session.logger.info(
        "Compiled %s download_windows:\n%s", len(down_windows), down_windows
    )
    # ========================================================
    # MEDIA SOURCE
    # ========================================================
    if media_path is not None:
        sections = prepare_local_visual_sections(
            media_path=media_path,
            download_windows=(down_windows),
        )

    elif document.transcript_url:
        # cfg_download.playlist_name = document.source_id
        output_dir = (
            context.lecture_root
            / "knowledge"
            / "frames"
            / document.source_id
            / "sections"
        )

        app_session.logger.info(
            "Video section | source_id=%s | media_id=%s | ",
            document.source_id,
            document.media_id,
        )

        sections = download_sections_with_retry(
            url=document.transcript_url,
            download_windows=down_windows,
            output_dir=output_dir,
            # context.save_folder,
            cfg_download=cfg_download,
        )

    else:
        raise ValueError(
            "Visual verification requires "
            "either a local media_path or "
            "document.transcript_url."
        )

    # ========================================================
    # EXISTING FRAME PIPELINE
    # ========================================================

    app_session.logger.info("Start extracting frames from %s sections", len(sections))

    sections = extract_all_frames(
        sections=sections, context=context, section_name=document.source_id
    )

    local_results: list[LocalVisualBatchResult] = []

    api_results: list[VisualKnowledgeResult] = []

    # ========================================================
    # SECTIONS
    # ========================================================
    for idx, section in enumerate(sections, start=1):
        if not section.frames:
            continue

        app_session.logger.info(
            "Start selecting frames from section '%s' [total: %s]", idx, len(sections)
        )

        select_result = select_distinct_frames(
            frames=section.frames,
            min_hash_distance=(cfg_screenshot.min_hash_distance),
            max_hash_distance=(cfg_screenshot.max_hash_distance),
            max_time_gap=(cfg_screenshot.max_time_gap),
        )

        app_session.logger.info("Start extracting additional frames")

        section.additional_frames = extract_additional_frames(
            section=section,
            add_frames=(select_result.additional_frame_times),
            section_name=document.source_id,
            context=context,
        )

        frames = sorted(
            [
                *select_result.selected_frames,
                *section.additional_frames,
            ],
            key=lambda item: item.source_time,
        )

        batches = build_visual_batches(
            section=section,
            selected_frames=frames,
            document=document,
            targets=targets,
            context=cfg_knowledge,
        )

        # ====================================================
        # BATCHES
        # ====================================================

        for idx, batch in enumerate(batches, start=1):
            app_session.logger.info(
                "Start analyzing batch #%s [total: %s]", idx, len(batches)
            )

            local_result = None
            result_llm = None
            result = None

            # ----------------------------------------------
            # LOCAL FIRST
            # ----------------------------------------------

            try:
                local_result = analyze_visual_batch_locally(
                    batch=batch,
                    document=document,
                    targets=targets,
                    use_formula_enrichment=(cfg_knowledge.visual_formula_enrichment),
                )

                local_results.append(local_result)

                apply_local_visual_verification(
                    document=document,
                    result=local_result,
                )

                if not local_result.requires_api_fallback:
                    app_session.logger.info(
                        ("Batch %s resolved locally; skipping API."),
                        batch.batch_id,
                    )
                    continue

                # ----------------------------------------------
                # API FALLBACK
                # ----------------------------------------------

                if not cfg_knowledge.visual_api_fallback:
                    app_session.logger.warning(
                        ("Batch %s remains unresolved; API fallback disabled."),
                        batch.batch_id,
                    )
                    continue

                app_session.logger.info(
                    ("Batch %s unresolved locally -> API fallback"),
                    batch.batch_id,
                )

                result_llm = analyze_visual_with_retry(
                    batch=batch,
                    model_name=(cfg_knowledge.visual_model),
                )

                result = finalize_visual_result(
                    result_llm,
                    batch,
                )

                api_results.append(result)

            finally:
                del result_llm
                del result
                del local_result

                gc.collect()

    # ========================================================
    # SAVE
    # ========================================================

    # now = datetime.now().strftime(
    #     "%Y-%m-%d_%Hh-%MM"
    # )

    save_dict(
        data={
            "source_id": document.source_id,
            "transcript_url": document.transcript_url,
            "media_id": document.media_id,
            "local_results": [item.model_dump(mode="json") for item in local_results],
            "api_results": [item.model_dump(mode="json") for item in api_results],
        },
        path=Path(context.lecture_root)
        / f"knowledge/visual_analysis/{document.source_id}_visual",
    )

    save_dict(
        data=document.model_dump(mode="json"),
        path=(
            Path(context.lecture_root)
            / (f"knowledge/{document.source_id}_know_enriched")
        ),
    )

    del local_results, api_results

    return document

    # visual_results.append(
    #         image_text_conversion(
    #                 frames=frames_all,
    #                 context=context
    #             )
    #         )

    # s_paths_clean = [sec.model_dump(mode="json")
    #                  for sec in section_paths]
    # save_dict(
    #     data={
    #         "paths": s_paths_clean,
    #         "windows": down_windows
    #         },
    #     path=Path(f"{context.save_folder}/second_sections_paths")
    #     # f"{know_extract.source_id}_visual_sections"
    #     )

    # for section in down_sections:
    #     section = add_frame_timestamps(
    #                             section=section,
    #                             interval=context.f_times_interval
    #                             )


#     download_video_section(
#     url: str,
#     start: float,
#     end: float,

#     # cookie_file: str | Path | None = None,
# ) -> Path:
# configure_marvin(context)

# chunks = build_transcript_chunks(context, transcript)
# chunks = enrich_chunks(chunks)

# results: dict ={}
# # results: list = []
# # str, dict[str, str | ChunkKnowledgeResult]
# # chunks
# # dict = {}

# visual_candidates: list = []

# for idx, chunk in enumerate(chunks):
#     result = analyze_and_extract_chunk(chunk, context.llm_model)

#     if not result.analysis.relevant:
#         continue

#     result = attach_chunk_provenance(
#                             result=result,
#                             chunk=chunk,
#                             )

#     result = validate_extraction(result)

#     # if (
#     #     result.extraction is None
#     #     or not result.analysis.needs_visual_context
#     #     ):
#     #     result

#     # else:
#     #     return None

#     visual_candidate = make_visual_candidate(
#                                     result=result,
#                                     chunk=chunk,
#                                     )

#     if visual_candidate is not None:
#         visual_candidates.append(visual_candidate)

#         for expression in result.extraction.formulas:
#             expression.verification_status = "pending"
#             expression.verification_reason = (
#                 "Visual context required for reliable reconstruction."
#                 )

#     # results.append(result)
#     results.update({
#             f"chunk_{idx:03d}": {
#                 "chunk": chunk,
#                 # .model_dump(mode="json"),
#                 "result": result,
#                 "visual_candidate": visual_candidate or []
#                 }
#             })

# save_dict(data=results,
#           path=Path(f"data/{app_session.timestamp}_know_extract_results"))

# results_all = [
#             value for key, value in results.items()
#             if key == result
#             ]
# # attach_chunk_provenance
# # validate_extraction
# return TranscriptKnowledgeDocument(
#                     source_id=transcript_id,
#                     chunks=results_all,
#                     visual_candidates=visual_candidates,
#                 )
# results


if __name__ == "__main__":
    run_visual_enrichment()

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
