## rebuild_knowledge.py
# import
import json
from pathlib import Path
import base64
import mimetypes
from openai import OpenAI
from PIL import Image

from src.agent.prompts.prompt_know_extract import (
    build_visual_verification_prompt,
    extract_visual_knowledge_prompt,
)
from src.core.config import agentic_env_vars
from src.core.memory import app_session
from src.core.memory_knowledge import KnowledgeContext  # context
from src.model_knowledge.data_knowledge import (
    DownloadedVideoSection,
    ExtractedFrame,
    FrameTimestamp,
    TranscriptKnowledgeDocument,
    VisualAnalysisBatch,
    VisualCandidate,
    VisualExpression,
    VisualKnowledgeResult,
    VisualKnowledgeResultLLM,
    VisualVerificationItem,
)
from src.utils.general_helper import (
    hash_text,
    load_from_cache,
    make_cache_key,
    save_to_cache,
)
from src.utils.llm_helper import log_openai_usage


def add_frame_timestamps(
    section: DownloadedVideoSection,
    interval: float = 5.0,
    edge_offset: float = 1.0,
) -> DownloadedVideoSection:

    section.frame_times = []

    source_time = section.source_start + edge_offset
    end = section.source_end - edge_offset

    while source_time <= end:
        section.frame_times.append(
            FrameTimestamp(
                source_time=round(source_time, 3),
                local_time=round(
                    source_time - section.download_start,
                    3,
                ),
            )
        )

        source_time += interval

    return section


def compile_download_windows(
    candidates: list[VisualCandidate],
    merge_gap: float = 2.0,
) -> list[tuple[float, float]]:

    if not candidates:
        return []

    windows = sorted((cand.start, cand.end) for cand in candidates)

    merged: list[list[float]] = []

    for start, end in windows:
        if not merged:
            merged.append([start, end])
            continue

        _, last_end = merged[-1]

        if start <= last_end + merge_gap:
            merged[-1][1] = max(last_end, end)
        else:
            merged.append([start, end])

    return [(start, end) for start, end in merged]


OCR_SUFFIXES = [
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    # ".bmp",
    # ".webp"
]


def validate_ocr_file(path: str | Path) -> Path:
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    if path.suffix.lower() not in OCR_SUFFIXES:
        raise ValueError(
            f"Unsupported OCR file type: {path.suffix}. "
            f"Supported: {sorted(OCR_SUFFIXES)}"
        )

    return path


def image_to_data_url(path: str | Path, format: str = "utf-8") -> str:
    path = Path(path)

    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        raise ValueError(f"Could not determine MIME type for '{path.name}'.")

    image_b64 = base64.b64encode(path.read_bytes()).decode(format)

    return f"data:{mime_type};base64,{image_b64}"


# OCR
# def image_text_conversion(
#                     frames: list[ExtractedFrame],
#                     # f_paths: list[Path],
#                     context: KnowledgeContext
#                     # mode: str
#                     ) -> list[VisualKnowledgeResult]:

#     results: list[VisualKnowledgeResult] = []
#     # model = LatexOCR()
#     for idx, frame in enumerate(frames):
#     # for idx, path in enumerate(f_paths):
#         path = frame.path

#         app_session.logger.info(
#                         "Start converting file #%s: '%s' ",
#                         idx,
#                         path.name
#                         )


#         with Image.open(path) as img:
#             app_session.logger.info("Format: %s", img.format)
#             app_session.logger.info("Size:  %s", img.size)
#             app_session.logger.info("Mode:  %s", img.mode)

#         # if path.suffix not in ALLOWED_OCR_SUFFIXES:
#         #     print(f"[ERROR] File '{path.name}' is not suitable; wrong suffix\n")
#         #     continue


#             # match mode:
#             #     case "tesseract":
#             #         text = pytesseract.image_to_string(
#             #                 img,
#             #                 lang="deu",
#             #                 )

#             #     case "pic2tex":
#             #         text = model(img)

#                 # case "open_ai":
#         results.append(
#                 analyze_math_image(
#                                 frame,
#                                 model_name=context.visual_model
#                                 )
#                 )

#                 # case _:
#                 #     print(f"[ERROR] Unknown mode: {mode}")

#         # print(text)
#         # print("-" * 80)

#         return results


def intervals_overlap(
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
) -> bool:
    return start_a <= end_b and start_b <= end_a


# ! TODO: transform get_section_knowledge() to
# ! get_visual_context(
#     start=batch_start,
#     end=batch_end,
#     ...
#       )


def get_batch_knowledge(
    document: TranscriptKnowledgeDocument,  # =document,
    start: float,  #  =frames[0].source_time,
    end: float,  # =frames[-1].source_time,
    margin: float = 5.0,
) -> tuple[list[str], list[str], list[str]]:

    if end < start:
        raise ValueError(f"Batch end ({end}) must be >= start ({start}).")

    if margin < 0:
        raise ValueError("margin must be >= 0.")

    context_start = max(
        0.0,
        start - margin,
    )
    context_end = end + margin

    statements: list[str] = []
    formulas: list[str] = []
    reasons: list[str] = []

    for result in document.chunks:
        extraction = result.extraction

        if extraction is None:
            continue

        for statement in extraction.statements:
            if intervals_overlap(
                statement.start,
                statement.end,
                context_start,
                context_end,
            ):
                if statement.text:
                    statements.append(statement.text)

        for formula in extraction.formulas:
            if intervals_overlap(
                formula.start,
                formula.end,
                context_start,
                context_end,
            ):
                formula_text = formula.latex or formula.plain_text

                if formula_text:
                    formulas.append(formula_text)

        for candidate in document.visual_candidates:
            if intervals_overlap(
                candidate.start,
                candidate.end,
                context_start,
                context_end,
            ):
                if candidate.reason:
                    reasons.append(candidate.reason)

    return (
        list(dict.fromkeys(statements)),
        list(dict.fromkeys(formulas)),
        list(dict.fromkeys(reasons)),
    )


# def get_section_knowledge(
#     section: DownloadedVideoSection,
#     document: TranscriptKnowledgeDocument,
# ) -> tuple[list[str], list[str], list[str]]:

#     statements: list[str] = []
#     formulas: list[str] = []
#     reasons: list[str] = []

#     for result in document.chunks:
#         extraction = result.extraction

#         if extraction is None:
#             continue

#         for statement in extraction.statements:
#             if intervals_overlap(
#                 statement.start,
#                 statement.end,
#                 section.source_start,
#                 section.source_end,
#             ):
#                 statements.append(
#                     statement.text
#                 )

#         for formula in extraction.formulas:
#             if intervals_overlap(
#                 formula.start,
#                 formula.end,
#                 section.source_start,
#                 section.source_end,
#             ):
#                 formulas.append(
#                     formula.latex
#                     or formula.plain_text
#                 )

#     for candidate in document.visual_candidates:
#         if intervals_overlap(
#             candidate.start,
#             candidate.end,
#             section.source_start,
#             section.source_end,
#         ):
#             if candidate.reason:
#                 reasons.append(
#                     candidate.reason
#                 )

#     return (
#         list(dict.fromkeys(statements)),
#         list(dict.fromkeys(formulas)),
#         list(dict.fromkeys(reasons)),
#     )


def split_frames_into_batches(
    frames: list[ExtractedFrame],
    batch_size: int = 8,
    overlap: int = 1,
) -> list[list[ExtractedFrame]]:

    if not frames:
        return []

    if batch_size <= overlap:
        raise ValueError("batch_size must be greater than overlap.")

    frames = sorted(
        frames,
        key=lambda x: x.source_time,
    )

    batches: list[list[ExtractedFrame]] = []

    step = batch_size - overlap

    for start in range(
        0,
        len(frames),
        step,
    ):
        batch = frames[start : start + batch_size]

        if not batch:
            break

        batches.append(batch)

        if start + batch_size >= len(frames):
            break

    return batches


def build_visual_batches(
    section: DownloadedVideoSection,
    selected_frames: list[ExtractedFrame],
    document: TranscriptKnowledgeDocument,
    context: KnowledgeContext,
    # batch_size: int = 8,
    # overlap: int = 1,
) -> list[VisualAnalysisBatch]:

    frame_batches = split_frames_into_batches(
        frames=selected_frames,
        batch_size=context.visual_batch_size,
        overlap=context.visual_batch_overlap,
    )

    batches: list[VisualAnalysisBatch] = []

    for idx, frames in enumerate(frame_batches):
        batch_start = frames[0].source_time
        batch_end = frames[-1].source_time

        statements, formulas, reasons = get_batch_knowledge(
            # batch=frame,
            document=document,
            start=batch_start,
            end=batch_end,
            margin=context.visual_context_margin,
        )

        batches.append(
            VisualAnalysisBatch(
                batch_id=(f"{section.section_id}_batch_{idx:03d}"),
                section_id=section.section_id,
                source_start=batch_start,
                source_end=batch_end,
                frames=frames,
                # [f.model_copy(deep=True) for f in frames],
                visual_reasons=reasons,
                transcript_statements=statements,
                transcript_formulas=formulas,
            )
        )

    return batches


def build_visual_batch_input_hash(
    batch: VisualAnalysisBatch,
) -> str:

    payload = {
        "batch_id": batch.batch_id,
        "section_id": batch.section_id,
        "source_times": [f.source_time for f in batch.frames],
        "frame_hashes": [
            hash_text(base64.b64encode(Path(f.path).read_bytes()).decode("ascii"))
            for f in batch.frames
        ],
        "statements": batch.transcript_statements,
        "formulas": batch.transcript_formulas,
        "visual_reasons": batch.visual_reasons,
    }

    return hash_text(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
        )
    )

    # schema = VisualKnowledgeResult.model_json_schema()

    # assert schema.get("additionalProperties") is False

    # for name, definition in schema.get("$defs", {}).items():
    #     if definition.get("type") == "object":
    #         assert (
    #             definition.get("additionalProperties")
    #             is False
    #         ), name

    # print("Schema looks strict.")


def validate_openai_strict_schema(
    schema: dict,
) -> None:

    def check_object(
        obj: dict,
        path: str,
    ) -> None:

        if obj.get("type") == "object":
            if obj.get("additionalProperties") is not False:
                raise ValueError(f"{path}: additionalProperties must be false")

            properties = obj.get(
                "properties",
                {},
            )

            required = set(obj.get("required", []))

            missing = set(properties) - required

            if missing:
                raise ValueError(
                    f"{path}: properties missing from required: {sorted(missing)}"
                )

        for key, value in obj.items():
            if isinstance(value, dict):
                check_object(
                    value,
                    f"{path}.{key}",
                )

            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        check_object(
                            item,
                            f"{path}.{key}[{idx}]",
                        )

    check_object(
        schema,
        "$",
    )


def analyze_visual_batch(
    batch: VisualAnalysisBatch,
    model_name: str = "gpt-5.6-terra",
) -> VisualKnowledgeResultLLM:

    if not model_name or not model_name.strip():
        raise ValueError("No visual model configured. context.visual_model is empty.")

    model_name = model_name.strip()

    client = OpenAI(api_key=agentic_env_vars.openai_api_key)

    schema = VisualKnowledgeResultLLM.model_json_schema()

    validate_openai_strict_schema(schema)
    app_session.logger.info("Schema is OpenAI-strict compatible.")

    VISUAL_VERIFICATION_PROMPT = build_visual_verification_prompt(batch)
    prompt_hash = hash_text(VISUAL_VERIFICATION_PROMPT)
    input_hash = build_visual_batch_input_hash(batch)

    metadata = {
        "batch_id": batch.batch_id,
        "input_hash": input_hash,
        "model": model_name,
        "prompt_hash": prompt_hash,
        "schema": "VisualKnowledgeResultLLM_v1",
        # "run_name": "chapter_planning_v2",
        # "prompt_version": "prompt_v1",
        "task": "visual_knowledge_v1",
        # topics_hash
    }

    cache_key = make_cache_key(params=metadata)

    cache_folder = "visual_verification"
    cached = load_from_cache(
        key=cache_key, folder=cache_folder, cls=VisualKnowledgeResultLLM
    )

    if cached is not None:
        app_session.logger.info(
            "Loading cached 'Visual knowledge result'(batch=%s, key=%s)",
            batch.batch_id,
            cache_key[:12],
        )
        return cached

    content: list[dict] = [
        {
            "type": "input_text",
            "text": VISUAL_VERIFICATION_PROMPT,
        }
    ]

    for frame in batch.frames:
        path = validate_ocr_file(frame.path)

        content.append(
            {
                "type": "input_text",
                "text": (f"Frame source_time={frame.source_time:.2f}s"),
            }
        )

        content.append(
            {
                "type": "input_image",
                "image_url": image_to_data_url(path),
            }
        )

    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "visual_knowledge_result",
                "schema": schema,
                "strict": True,
            }
        },
    )

    log_openai_usage(
        response.usage,
        model_name,
        "analyze_visual_batch",
    )

    if response.status != "completed":
        raise RuntimeError(
            f"Visual analysis did not complete: "
            f"status={response.status}, "
            f"error={response.error}"
        )

    if not response.output_text:
        raise ValueError(f"No output returned for batch '{batch.batch_id}'.")

    response_text = response.output_text
    result = VisualKnowledgeResultLLM.model_validate_json(response_text)

    save_to_cache(
        key=cache_key,
        folder=cache_folder,
        data=result.model_dump(mode="json"),
        metadata=metadata,
    )

    return result

    # return VisualKnowledgeResultLLM.model_validate_json(
    #     response.output_text
    # )


# ! TODO: development metric's calculation
# def calculate_verification_score(
#     llm_confidence: float,
#     n_supporting_frames: int,
#     transcript_match: bool,
#     ambiguous: bool,
# ) -> float:

# direct visual evidence
# +
# number of supporting frames
# +
# same expression in multiple frames/batches
# +
# agreement with transcript
# +
# ambiguity
# +
# LLM confidence

# Du kannst später daraus eine Art cross-batch consensus ableiten:

# Expression A
#    Batch 1: observed
#    Batch 2: observed
#    Batch 3: observed
#          ↓
# very strong visual evidence


def finalize_visual_result(
    llm_result: VisualKnowledgeResultLLM,
    batch: VisualAnalysisBatch,
) -> VisualKnowledgeResult:

    expressions = [
        VisualExpression(
            start=(min(expr.source_times) if expr.source_times else batch.source_start),
            end=(max(expr.source_times) if expr.source_times else batch.source_end),
            expression_id=(f"{batch.batch_id}_expr_{idx:03d}"),
            section_id=batch.section_id,
            batch_id=batch.batch_id,
            visual_latex=expr.visual_latex,
            visual_plain_text=expr.visual_plain_text,
            visual_labels=expr.visual_labels,
            ambiguous=expr.ambiguous,
            ambiguity_reason=expr.ambiguity_reason,
            source_times=expr.source_times,
            source="visual",
            llm_confidence=expr.llm_confidence,
        )
        for idx, expr in enumerate(llm_result.expressions)
    ]

    verifications = [
        VisualVerificationItem(
            source="transcript+visual",
            evidence_type=item.evidence_type,
            start=(min(item.source_times) if item.source_times else batch.source_start),
            end=(max(item.source_times) if item.source_times else batch.source_end),
            verification_id=(f"{batch.batch_id}_ver_{idx:03d}"),
            expression_id=(f"{batch.batch_id}_expr_{idx:03d}"),
            section_id=batch.section_id,
            batch_id=batch.batch_id,
            transcript_latex=item.transcript_latex,
            transcript_plain_text=item.transcript_plain_text,
            visual_latex=item.visual_latex,
            visual_plain_text=item.visual_plain_text,
            review_status=item.status,
            reason=item.reason,
            source_times=item.source_times,
            llm_confidence=item.llm_confidence,
        )
        for idx, item in enumerate(llm_result.verifications)
    ]

    return VisualKnowledgeResult(
        start=batch.source_start,
        end=batch.source_end,
        batch_id=batch.batch_id,
        section_id=batch.section_id,
        expressions=expressions,
        verifications=verifications,
        unresolved_content=(llm_result.unresolved_content),
        summary=llm_result.summary,
        llm_confidence=llm_result.llm_confidence,
        source="transcript+visual",
    )
