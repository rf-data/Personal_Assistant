## run_knowledge_improvement.py
# imports
from pathlib import Path
from datetime import datetime

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_knowledge import KnowledgeContext
from src.tools_knowledge.rebuild_knowledge import (
    # clean_frame_times,
    # add_frame_timestamps,
    analyze_visual_batch,
    build_visual_batches,
    compile_download_windows,
    finalize_visual_result,
    # image_text_conversion,
)
from src.tools_transcribe.extract_video import (
    download_visual_sections,
    extract_additional_frames,
    extract_all_frames,
    select_distinct_frames,
)
from src.model_knowledge.data_knowledge import (
    TranscriptKnowledgeDocument,
    VisualCandidate,
    VisualKnowledgeResult,
)
# from src.model_transcribe.data_transcribe import TranscriptDocument
# from src.utils.llm_helper import configure_marvin

# from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict, save_dict


def validate_knowledge_context(
    context: KnowledgeContext,
) -> None:

    if not context.visual_model.strip():
        raise ValueError("context.visual_model is not configured.")

    if context.visual_batch_size <= 0:
        raise ValueError("visual_batch_size must be > 0.")

    if context.visual_batch_overlap >= context.visual_batch_size:
        raise ValueError("visual_batch_overlap must be smaller than visual_batch_size.")


def run_knowledge_improvement():

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(path=context_path, cls=KnowledgeContext)

    validate_knowledge_context(context)

    context.cfg_download.cookie_file = folder_env_vars.yt_cookies

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name, file_name=context.logger_f_name
    )

    know_extract = load_dict(
        path=Path(f"{context.save_folder}/{context.know_extract_file}.json"),
        cls=TranscriptKnowledgeDocument,
    )

    url = know_extract.transcript_url

    # visual_candidates: set = set()

    # for res in results.values():
    #     visual_candidates.add(res["visual_candidate"])

    visual_candidates = know_extract.visual_candidates
    app_session.logger.info(
        "Found %s visual candidates in media '%s'", len(visual_candidates), url
    )
    # for cand in visual_candidates:
    # f_times_raw = compile_frame_times(
    #         candidates=visual_candidates,
    #         interval=context.f_times_interval,
    #         )

    # f_times = clean_frame_times(
    #         f_times_raw,
    #         min_distance=context.min_distance,
    #         )

    # n_paths = len(context.transcript_names)
    # for idx, t_name in enumerate(context.transcript_names):

    #     t_path = Path(folder_env_vars.data_audio) / t_name
    #     app_session.logger.info(
    #                 "[File #%s / %s] Start extracting knowledge from '%s'",
    #                 idx,
    #                 n_paths,
    #                 shorten_path(t_path)
    #                 )

    #     knowledge_improvement(context, t_path)

    return knowledge_improvement(url, context, know_extract)


def knowledge_improvement(
    url: str,
    context: KnowledgeContext,
    know_extract: TranscriptKnowledgeDocument,
    # list[VisualCandidate]
):
    # -> TranscriptKnowledgeDocument:
    # list[ChunkKnowledgeResult]:

    cfg_download = context.cfg_download
    cfg_screenshot = context.cfg_screenshot

    candidates = know_extract.visual_candidates
    if candidates:
        app_session.logger.info(
            "Visual candidate range: %.2f - %.2f s (%s candidates)",
            min(c.start for c in candidates),
            max(c.end for c in candidates),
            len(candidates),
        )

        for cand in candidates:
            app_session.logger.info(
                "\nVisual candidate: %s | %.2f - %.2f | %s",
                cand.chunk_id,
                cand.start,
                cand.end,
                cand.reason,
            )

    down_windows = compile_download_windows(
        candidates=candidates, merge_gap=cfg_screenshot.merge_gap
    )
    app_session.logger.info(
        "Compiled %s download_windows:\n%s", len(down_windows), down_windows
    )

    down_sections = download_visual_sections(
        url=url,
        download_windows=down_windows,
        output_dir=context.save_folder,
        cfg_download=cfg_download,
    )
    app_session.logger.info("Downloaded %s sections", len(down_sections))

    down_sections = extract_all_frames(sections=down_sections, context=context)
    app_session.logger.info("Extracted frames...")

    visual_results: list[VisualKnowledgeResult] = []

    for section in down_sections:
        frames = section.frames

        if not frames:
            app_session.logger.warning(
                "No frames found for section '%s'",
                section.section_id,
            )
            continue

        app_session.logger.info(
            "Processing download section '%s'\ncount: %s | min: %s | max: %s",
            section.section_id,
            len(frames),
            min([f.source_time for f in frames]),
            max([f.source_time for f in frames]),
        )

        select_result = select_distinct_frames(
            frames=frames,
            min_hash_distance=cfg_screenshot.min_hash_distance,
            max_hash_distance=cfg_screenshot.max_hash_distance,
            max_time_gap=cfg_screenshot.max_time_gap,
        )

        select_frames = select_result.selected_frames
        app_session.logger.info(
            "Selected frames (n=%s):\t%s",
            len(select_frames),
            sorted([sel.source_time for sel in select_frames]),
        )

        add_frames = select_result.additional_frame_times
        app_session.logger.info(
            "Additional frames are needed (n=%s):\t%s",
            len(add_frames),
            sorted(add_frames),
        )

        section.additional_frames = extract_additional_frames(
            section=section,
            add_frames=add_frames,
            # list[float],
            context=context,
        )

        frames_for_llm = sorted(
            [*select_frames, *section.additional_frames],
            key=lambda frame: frame.source_time,
        )

        for frame in frames_for_llm:
            if not frame.path.is_file():
                raise FileNotFoundError(
                    f"Frame referenced but missing on disk: {frame.path}"
                )

        batches = build_visual_batches(
            section=section,
            selected_frames=frames_for_llm,
            document=know_extract,
            context=context,
            # batch_size=context.visual_batch_size,
            # overlap=context.visual_batch_overlap,
        )

        for batch in batches:
            result_llm = analyze_visual_batch(
                batch=batch,
                model_name=context.visual_model,
            )

            # # ! temporary to correct cached data
            # result_llm.batch_id = batch.batch_id
            # result_llm.section_id = batch.batch_id

            result = finalize_visual_result(
                result_llm,
                batch,
                # .source_start,
                # batch.source_end
            )
            visual_results.append(
                # result.model_dump(mode="json")
                result
            )

    now = datetime.now().strftime("%Y-%m-%d_%Hh-%MM")
    save_dict(
        data={"results": [res.model_dump(mode="json") for res in visual_results]},
        path=Path(f"{context.save_folder}/{now}_visual_analysis"),
        # f"{know_extract.source_id}_visual_sections"
    )

    return visual_results

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

# transcript = load_dict(
#                     path=transcript_path,
#                     cls=TranscriptDocument
#                         )
# transcript_id = (transcript.provenance.youtube_id or "tba")

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
    run_knowledge_improvement()

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
