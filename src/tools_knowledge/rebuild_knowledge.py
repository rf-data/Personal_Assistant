## rebuild_knowledge.py
# import
import gc
import json
from pathlib import Path
import base64
import mimetypes
import hashlib
from openai import OpenAI

from docling_core.types.doc import (
    DocItemLabel,
)

from src.agent.prompts.prompt_know_extract import (
    build_visual_verification_prompt,
    extract_visual_knowledge_prompt,
)
from src.core.config import agentic_env_vars
from src.core.memory import app_session
from src.core.memory_lecture import LectureContext
from src.model_knowledge.data_knowledge import (
    DownloadedVideoSection,
    DoclingFrameResult,
    ExtractedFrame,
    FrameTimestamp,
    TranscriptKnowledgeDocument,
    LectureKnowledgeDocument,
    LocalVisualBatchResult,
    VisualAnalysisBatch,
    VisualCandidate,
    VisualExpression,
    VisualKnowledgeResult,
    VisualKnowledgeResultLLM,
    VisualVerificationItem,
    VisualVerificationTarget,
)
from src.utils.general_helper import (
    hash_text,
    load_from_cache,
    make_cache_key,
    save_to_cache,
)
from src.utils.llm_helper import log_openai_usage
from src.utils.latex_helper import normalize_math_text
from src.utils.docling_helper import get_docling_image_converter

VISUAL_REASON_TERMS = (
    "visual verification",
    "visual context",
    "visuell",
    "ambiguous",
    "unclear",
    "unklar",
    "uneindeutig",
    "incomplete",
    "unvollständig",
    "not fully reconstruct",
    "not reliably reconstruct",
    "nicht vollständig rekonstru",
    "nicht zuverlässig rekonstru",
    "transcriptfragment",
    "transkriptfragment",
    "deictic",
    "deiktisch",
)


def evidence_overlaps_interval(
    evidence: list,
    start: float,
    end: float,
) -> bool:

    return any(
        intervals_overlap(
            item.start,
            item.end,
            start,
            end,
        )
        for item in evidence
    )


def evidence_time_range(
    evidence: list,
) -> tuple[float, float] | None:

    if not evidence:
        return None

    return (
        min(item.start for item in evidence),
        max(item.end for item in evidence),
    )


def evidence_time_windows(
    evidence: list,
    *,
    merge_gap: float = 2.0,
) -> list[tuple[float, float]]:

    if not evidence:
        return []

    windows = sorted(
        (
            item.start,
            item.end,
        )
        for item in evidence
    )

    merged: list[list[float]] = []

    for start, end in windows:
        if not merged:
            merged.append([start, end])
            continue

        last_start, last_end = merged[-1]

        if start <= last_end + merge_gap:
            merged[-1][1] = max(
                last_end,
                end,
            )

        else:
            merged.append([start, end])

    return [(start, end) for start, end in merged]


def formula_requires_visual_verification(
    formula,
) -> bool:

    if formula.verification_status == "verified":
        return False

    reasons = " ".join(formula.verification_reasons).casefold()

    if not reasons:
        return False

    return any(term in reasons for term in VISUAL_REASON_TERMS)


def select_visual_verification_targets(
    document: LectureKnowledgeDocument,
) -> list[VisualVerificationTarget]:

    targets: list[VisualVerificationTarget] = []

    # ========================================================
    # 1. Original visual candidates
    # ========================================================

    for candidate in document.visual_candidates:
        statement_ids = [
            statement.statement_id
            for statement in document.statements
            if evidence_overlaps_interval(
                statement.evidence,
                candidate.start,
                candidate.end,
            )
        ]

        expression_ids = [
            formula.expression_id
            for formula in document.formulas
            if evidence_overlaps_interval(
                formula.evidence,
                candidate.start,
                candidate.end,
            )
        ]

        targets.append(
            VisualVerificationTarget(
                target_id=(f"candidate_{candidate.chunk_id}"),
                start=candidate.start,
                end=candidate.end,
                reasons=([candidate.reason] if candidate.reason else []),
                statement_ids=statement_ids,
                expression_ids=expression_ids,
                chunk_ids=[candidate.chunk_id],
                triggers=["visual_candidate"],
            )
        )

    # ========================================================
    # 2. Canonical statements marked needs_review
    # ========================================================

    for statement in document.statements:
        if not statement.needs_review:
            continue

        time_range = evidence_time_windows(statement.evidence)

        if time_range is None:
            continue

        for start, end in time_range:
            expression_ids = [
                formula.expression_id
                for formula in document.formulas
                if evidence_overlaps_interval(
                    formula.evidence,
                    start,
                    end,
                )
            ]

            targets.append(
                VisualVerificationTarget(
                    target_id=(f"review_{statement.statement_id}"),
                    start=start,
                    end=end,
                    reasons=(
                        [statement.review_reason] if statement.review_reason else []
                    ),
                    statement_ids=[statement.statement_id],
                    expression_ids=expression_ids,
                    chunk_ids=list(
                        dict.fromkeys(
                            evidence.chunk_id for evidence in statement.evidence
                        )
                    ),
                    triggers=["statement_review"],
                )
            )

    # ========================================================
    # 3. Formulas with explicit visual ambiguity
    # ========================================================

    for formula in document.formulas:
        if not formula_requires_visual_verification(formula):
            continue

        time_range = evidence_time_windows(formula.evidence)

        if time_range is None:
            continue

        for start, end in time_range:
            targets.append(
                VisualVerificationTarget(
                    target_id=(f"formula_{formula.expression_id}"),
                    start=start,
                    end=end,
                    reasons=(formula.verification_reasons.copy()),
                    expression_ids=[formula.expression_id],
                    chunk_ids=list(
                        dict.fromkeys(
                            evidence.chunk_id for evidence in formula.evidence
                        )
                    ),
                    triggers=["formula_reason"],
                )
            )

    return merge_visual_verification_targets(targets)


def merge_visual_verification_targets(
    targets: list[VisualVerificationTarget],
    merge_gap: float = 2.0,
    max_window_seconds: float = 75.0,
) -> list[VisualVerificationTarget]:

    if not targets:
        return []

    ordered = sorted(
        targets,
        key=lambda item: (
            item.start,
            item.end,
        ),
    )

    merged: list[VisualVerificationTarget] = []

    for target in ordered:
        if not merged:
            merged.append(target.model_copy(deep=True))
            continue

        previous = merged[-1]

        if target.start <= previous.end + merge_gap:
            candidate_start = min(
                previous.start,
                target.start,
            )

            candidate_end = max(
                previous.end,
                target.end,
            )

            candidate_duration = candidate_end - candidate_start

            can_merge = (
                target.start <= previous.end + merge_gap
                and candidate_duration <= max_window_seconds
            )

            if can_merge:
                previous.start = candidate_start

                previous.end = candidate_end

                previous.reasons = list(
                    dict.fromkeys(previous.reasons + target.reasons)
                )

                previous.statement_ids = list(
                    dict.fromkeys(previous.statement_ids + target.statement_ids)
                )

                previous.expression_ids = list(
                    dict.fromkeys(previous.expression_ids + target.expression_ids)
                )

            previous.chunk_ids = list(
                dict.fromkeys(previous.chunk_ids + target.chunk_ids)
            )

            previous.triggers = list(dict.fromkeys(previous.triggers + target.triggers))

        else:
            merged.append(target.model_copy(deep=True))

    for idx, item in enumerate(
        merged,
        start=1,
    ):
        item.target_id = f"visual_target_{idx:03d}"

    return merged


def hash_file(
    path: Path,
) -> str:

    h = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()


def analyze_frame_with_docling(
    frame: ExtractedFrame,
    *,
    formula_enrichment: bool,
) -> DoclingFrameResult:

    mode = "formula" if formula_enrichment else "ocr"

    frame_hash = hash_file(frame.path)

    cache_key = make_cache_key(
        params={
            "task": "docling_visual_frame_v1",
            "frame_hash": frame_hash,
            "source_time": frame.source_time,
            "mode": mode,
        }
    )

    cached = load_from_cache(
        key=cache_key,
        folder="visual_docling",
        cls=DoclingFrameResult,
    )

    if cached is not None:
        return cached

    converter = None
    conversion = None
    document = None

    try:
        converter = get_docling_image_converter(formula_enrichment)

        conversion = converter.convert(frame.path)

        document = conversion.document

        text = document.export_to_text().strip()

        formulas: list[str] = []

        for item in document.texts:
            label = getattr(
                item.label,
                "value",
                item.label,
            )

            if label != (DocItemLabel.FORMULA.value):
                continue

            value = (
                getattr(item, "text", None) or getattr(item, "orig", None) or ""
            ).strip()

            if value:
                formulas.append(value)

        result = DoclingFrameResult(
            section_id=frame.section_id,
            source_time=frame.source_time,
            path=frame.path,
            mode=mode,
            text=text,
            formulas=list(dict.fromkeys(formulas)),
        )

        save_to_cache(
            key=cache_key,
            folder="visual_docling",
            data=result.model_dump(mode="json"),
            metadata={
                "task": "docling_visual_frame_v1",
                "mode": mode,
                "source_time": frame.source_time,
            },
        )

        return result

    finally:
        del document
        del conversion
        del converter

        gc.collect()


def analyze_frames_with_docling(
    frames: list[ExtractedFrame],
    *,
    formula_enrichment: bool,
) -> list[DoclingFrameResult]:

    return [
        analyze_frame_with_docling(
            frame,
            formula_enrichment=(formula_enrichment),
        )
        for frame in frames
    ]


def formula_variants(
    formula,
) -> set[str]:

    values = [
        formula.latex,
        formula.plain_text,
        *formula.latex_variants,
        *formula.text_variants,
    ]

    return {normalize_math_text(value) for value in values if value}


def docling_result_variants(
    result: DoclingFrameResult,
) -> set[str]:

    values: list[str] = []

    values.extend(result.formulas)

    values.extend(line.strip() for line in result.text.splitlines() if line.strip())

    return {normalize_math_text(value) for value in values if value}


def match_formulas_against_docling(
    formulas: list,
    results: list[DoclingFrameResult],
    *,
    min_frame_matches: int,
) -> set[str]:

    matched: set[str] = set()

    frame_variants = [docling_result_variants(result) for result in results]

    for formula in formulas:
        target_variants = formula_variants(formula)

        n_matches = 0

        for variants in frame_variants:
            if target_variants & variants:
                n_matches += 1

        if n_matches >= min_frame_matches:
            matched.add(formula.expression_id)

    return matched


def get_batch_target_ids(
    targets: list[VisualVerificationTarget],
    start: float,
    end: float,
) -> tuple[
    set[str],
    set[str],
]:

    statement_ids: set[str] = set()
    expression_ids: set[str] = set()

    for target in targets:
        if not intervals_overlap(
            target.start,
            target.end,
            start,
            end,
        ):
            continue

        statement_ids.update(target.statement_ids)

        expression_ids.update(target.expression_ids)

    return (
        statement_ids,
        expression_ids,
    )


def analyze_visual_batch_locally(
    batch: VisualAnalysisBatch,
    document: LectureKnowledgeDocument,
    targets: list[VisualVerificationTarget],
    *,
    use_formula_enrichment: bool = True,
) -> LocalVisualBatchResult:

    (
        target_statement_ids,
        target_expression_ids,
    ) = get_batch_target_ids(
        targets=targets,
        start=batch.source_start,
        end=batch.source_end,
    )

    target_formulas = [
        formula
        for formula in document.formulas
        if formula.expression_id in target_expression_ids
    ]

    # ========================================================
    # Stage 1: cheap OCR
    # ========================================================

    ocr_results = analyze_frames_with_docling(
        batch.frames,
        formula_enrichment=False,
    )

    # OCR alone gets accepted only if the same
    # expression is found in >= 2 distinct frames.
    matched = match_formulas_against_docling(
        formulas=target_formulas,
        results=ocr_results,
        min_frame_matches=2,
    )

    match_method = {expression_id: "ocr_consensus" for expression_id in matched}

    unresolved = target_expression_ids - matched

    formula_results: list[DoclingFrameResult] = []

    # ========================================================
    # Stage 2: local formula model
    # ========================================================

    if unresolved and use_formula_enrichment:
        unresolved_formulas = [
            formula
            for formula in target_formulas
            if formula.expression_id in unresolved
        ]

        formula_results = analyze_frames_with_docling(
            batch.frames,
            formula_enrichment=True,
        )

        formula_matches = match_formulas_against_docling(
            formulas=(unresolved_formulas),
            results=formula_results,
            min_frame_matches=1,
        )

        matched.update(formula_matches)

        for expression_id in formula_matches:
            match_method[expression_id] = "docling_formula"

        unresolved = target_expression_ids - matched

    # A review statement without a formula cannot
    # safely be declared verified by OCR alone.
    statement_only_review = bool(target_statement_ids and not target_expression_ids)

    requires_api_fallback = bool(unresolved) or statement_only_review

    return LocalVisualBatchResult(
        batch_id=batch.batch_id,
        section_id=batch.section_id,
        target_expression_ids=sorted(target_expression_ids),
        matched_expression_ids=sorted(matched),
        unresolved_expression_ids=sorted(unresolved),
        match_method=match_method,
        ocr_results=ocr_results,
        formula_results=(formula_results),
        requires_api_fallback=(requires_api_fallback),
    )


def apply_local_visual_verification(
    document: LectureKnowledgeDocument,
    result: LocalVisualBatchResult,
) -> None:

    matched = set(result.matched_expression_ids)

    for formula in document.formulas:
        if formula.expression_id not in matched:
            continue

        method = result.match_method.get(
            formula.expression_id,
            "docling",
        )

        formula.verification_status = "verified"

        reason = (
            "Matched against visual "
            "evidence using local "
            f"Docling processing "
            f"({method})."
        )

        if reason not in formula.verification_reasons:
            formula.verification_reasons.append(reason)


#########################################
#
#########################################


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
    document: LectureKnowledgeDocument,
    targets: list[VisualVerificationTarget],
    start: float,
    end: float,
    margin: float = 5.0,
) -> tuple[
    list[str],
    list[str],
    list[str],
]:

    if end < start:
        raise ValueError(f"Batch end ({end}) must be >= start ({start}).")

    context_start = max(
        0.0,
        start - margin,
    )

    context_end = end + margin

    statements: list[str] = []
    formulas: list[str] = []
    reasons: list[str] = []

    # ========================================================
    # Canonical statements
    # ========================================================

    for statement in document.statements:
        if not evidence_overlaps_interval(
            statement.evidence,
            context_start,
            context_end,
        ):
            continue

        statements.append((f"{statement.statement_id} | {statement.text}"))

    # ========================================================
    # Consolidated formulas
    # ========================================================

    for formula in document.formulas:
        if not evidence_overlaps_interval(
            formula.evidence,
            context_start,
            context_end,
        ):
            continue

        formulas.append(
            (
                f"{formula.expression_id}"
                f" | latex="
                f"{formula.latex or '-'}"
                f" | plain="
                f"{formula.plain_text}"
            )
        )

    # ========================================================
    # Reasons
    # ========================================================

    for target in targets:
        if intervals_overlap(
            target.start,
            target.end,
            context_start,
            context_end,
        ):
            reasons.extend(target.reasons)

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
    targets: list[VisualVerificationTarget],
    context: LectureContext,
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
            targets=targets,
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
        "frame_hashes": [hash_file(Path(frame.path)) for frame in batch.frames],
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
            # target_expression_id="",
            evidence_type=item.evidence_type,
            start=(min(item.source_times) if item.source_times else batch.source_start),
            end=(max(item.source_times) if item.source_times else batch.source_end),
            verification_id=(f"{batch.batch_id}_ver_{idx:03d}"),
            expression_id=item.target_expression_id,
            # (f"{batch.batch_id}_expr_{idx:03d}"),
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
