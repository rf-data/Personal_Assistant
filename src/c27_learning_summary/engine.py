"""Bounded section calls and deterministic consolidation; no ingestion execution."""

import ast
import json
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass

from src.c27_learning_summary.adapter import source_slices, validate_input
from src.c27_learning_summary.models import (
    MAX_CLAIM_REFS,
    Claim,
    SectionResponse,
    SectionResult,
    SummaryConfig,
    SummaryResult,
)
from src.content_store.models import fingerprint, sha256
from src.tools_evaluation.math_syntax import FormulaSyntaxError, parse_formula


@dataclass
class Outcome:
    result: SummaryResult
    from_cache: bool


class SummaryRunError(RuntimeError):
    def __init__(self, run_id, code):
        self.run_id, self.code = run_id, code
        super().__init__(
            f"Run {run_id}: {code}; inspect saved state and partial sections"
        )


def messages_for(ref, config):
    return [
        {"role": "system", "content": config.prompt},
        {
            "role": "user",
            "content": json.dumps(
                dict(
                    summary_type=config.summary_type,
                    excerpt=ref.model_dump(mode="json"),
                    schema=SectionResponse.model_json_schema(),
                ),
                ensure_ascii=False,
            ),
        },
    ]


def bind_section(response, ref):
    claims, rejected = [], []
    for candidate in response.claims:
        # A section may only cite its own source, never another selected chunk.
        reason = None
        if set(candidate.refs) != {ref.ref_id}:
            reason = "missing_or_foreign_source_reference"
        elif candidate.text not in ref.text:
            reason = "unsupported_claim_not_verbatim"
        elif candidate.category == "formula":
            try:
                parse_formula(candidate.text)
            except FormulaSyntaxError:
                reason = "invalid_or_unsupported_formula_syntax"
        elif candidate.category == "code":
            try:
                ast.parse(candidate.text)
            except (SyntaxError, ValueError, RecursionError):
                reason = "invalid_python_code_syntax"
        if reason:
            rejected.append(reason)
        else:
            data = candidate.model_dump(mode="json")
            data["refs"] = sorted(set(data["refs"]))
            claims.append(Claim(claim_id=fingerprint(data), **data))
    return SectionResult(
        title=f"{ref.material_id} / {ref.block_id} [{ref.offset_start}:{ref.offset_end}]",
        ref_id=ref.ref_id,
        claims=claims,
        rejected=rejected,
        uncertainties=response.uncertainties,
    )


def consolidate(
    sections: Sequence[SectionResult],
) -> tuple[tuple[Claim, ...], list[str]]:
    merged: dict[tuple[str, str], tuple[Claim, set[str]]] = {}
    warnings = []
    for section in sections:
        warnings += list(section.rejected)
        warnings += [f"Source uncertainty: {u}" for u in section.uncertainties]
        for claim in section.claims:
            # Case/whitespace can change code and formulas; merge exact excerpts only.
            key = (claim.category, claim.text)
            if key not in merged:
                merged[key] = (claim, set())
            merged[key][1].update(claim.refs)
    groups = []
    for first, references in merged.values():
        ordered = sorted(references)
        for offset in range(0, len(ordered), MAX_CLAIM_REFS):
            data = first.model_dump(mode="json", exclude={"claim_id"})
            data["refs"] = ordered[offset : offset + MAX_CLAIM_REFS]
            groups.append(Claim(claim_id=fingerprint(data), **data))
    claims = tuple(groups)
    for i, left in enumerate(claims):
        for right in claims[i + 1 :]:
            ltext, rtext = left.text.casefold(), right.text.casefold()
            negation = re.sub(r"\bnot\s+|\bnicht\s+", "", ltext) == re.sub(
                r"\bnot\s+|\bnicht\s+", "", rtext
            )
            same_topic = (
                left.topic.strip() and left.topic.casefold() == right.topic.casefold()
            )
            if left.text != right.text and (negation or same_topic):
                warnings.append(
                    f"Possible contradiction / alternative explanation: {left.claim_id} <> {right.claim_id}; human review required"
                )
    return claims, list(dict.fromkeys(warnings))


def input_snapshot(catalog, unit, course_id, week_id, lecture_id, selected, config):
    return dict(
        result_schema_version=2,
        course_id=course_id,
        week_id=week_id,
        lecture_id=lecture_id,
        origin=catalog.origin,
        # Include the inventory to invalidate stale missing-material warnings too.
        inventory=[m.model_dump(mode="json") for m in unit.materials],
        selected=sorted(selected),
        config=config.model_dump(mode="json"),
        title=unit.title or unit.section_id,
    )


def generate(
    store,
    catalog,
    course_id,
    week_id,
    lecture_id,
    selected,
    config,
    model,
    *,
    progress=None,
    force=False,
):
    config = SummaryConfig.model_validate_json(config.model_dump_json())
    if model.model != config.model or model.provider != config.provider:
        raise ValueError("Adapter identity does not match configured model/provider")
    catalog, course, week, unit, materials, warnings = validate_input(
        catalog,
        course_id,
        week_id,
        lecture_id,
        selected,
    )
    refs = source_slices(course_id, week_id, lecture_id, materials, config)
    inputs = input_snapshot(
        catalog, unit, course_id, week_id, lecture_id, selected, config
    )
    key = fingerprint(inputs)
    messages = [messages_for(ref, config) for ref in refs]
    if any(
        len(json.dumps(m, ensure_ascii=False).encode()) > config.max_input_bytes
        for m in messages
    ):
        raise ValueError("Maximum serialized request input size exceeded")
    with store.exclusive():
        if not force:
            cached = store.cached(key)
            if cached:
                return Outcome(cached, True)
        run_id = store.begin(key, inputs)
        started = time.monotonic()
        sections = []
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "calls": 0,
            "usage_missing_calls": 0,
            "known_input_tokens": 0,
            "known_output_tokens": 0,
            "input_usage_missing_calls": 0,
            "output_usage_missing_calls": 0,
        }
        try:
            for index, (ref, request) in enumerate(zip(refs, messages, strict=True)):
                response = None
                for attempt in range(config.retries + 1):
                    remaining = config.wall_seconds - (time.monotonic() - started)
                    if remaining <= 0:
                        raise TimeoutError("Local run deadline exceeded")
                    usage["calls"] += 1
                    usage["usage_missing_calls"] += 1
                    for direction in ("input", "output"):
                        usage[f"{direction}_usage_missing_calls"] += 1
                        usage.pop(f"{direction}_tokens", None)
                    try:
                        reply = model.complete(
                            request,
                            config=config,
                            timeout=min(config.request_timeout, remaining),
                        )
                        if (
                            not isinstance(reply.raw, str)
                            or len(reply.raw.encode()) > 128000
                        ):
                            raise ValueError("Raw output byte limit exceeded")
                        # Preserve successful raw replies even if structural validation fails.
                        store.write(
                            run_id,
                            f"raw/{index:03}-{attempt}.json",
                            dict(
                                raw=reply.raw,
                                usage={
                                    k: v
                                    for k, v in reply.usage.items()
                                    if k in {"input_tokens", "output_tokens"}
                                },
                            ),
                        )
                        reported = {
                            name: value
                            for name, value in reply.usage.items()
                            if name in {"input_tokens", "output_tokens"}
                            and type(value) is int
                            and value >= 0
                        }
                        for direction in ("input", "output"):
                            name = f"{direction}_tokens"
                            if name in reported:
                                usage[f"known_{name}"] += reported[name]
                                usage[f"{direction}_usage_missing_calls"] -= 1
                            if usage[f"{direction}_usage_missing_calls"] == 0:
                                usage[name] = usage[f"known_{name}"]
                        if {"input_tokens", "output_tokens"} <= reported.keys():
                            usage["usage_missing_calls"] -= 1
                        response = SectionResponse.model_validate_json(reply.raw)
                        if time.monotonic() - started > config.wall_seconds:
                            raise TimeoutError("Local run deadline exceeded")
                        break
                    except Exception as exc:
                        # Exception strings can contain provider headers/keys; persist only class.
                        store.write(
                            run_id,
                            f"raw/{index:03}-{attempt}-error.json",
                            dict(error=type(exc).__name__),
                        )
                        if attempt >= config.retries or isinstance(exc, TimeoutError):
                            raise
                section = bind_section(response, ref)
                sections.append(section)
                store.write(
                    run_id,
                    f"sections/{index:03}.json",
                    section.model_dump(mode="json"),
                )
                if progress:
                    progress(index + 1, len(refs))
            claims, issues = consolidate(sections)
            if not claims:
                issues.append("No validated claims; output is incomplete")
            cost = None
            if (
                config.input_usd_per_million is not None
                and config.output_usd_per_million is not None
                and not usage["usage_missing_calls"]
            ):
                cost = (
                    usage["input_tokens"] * config.input_usd_per_million
                    + usage["output_tokens"] * config.output_usd_per_million
                ) / 1_000_000
            result = SummaryResult(
                run_id=run_id,
                cache_key=key,
                title=unit.title or unit.section_id,
                config=config,
                refs=refs,
                sections=sections,
                claims=claims,
                state="needs_attention" if issues else "ready_for_review",
                warnings=list(dict.fromkeys(warnings + issues)),
                usage=usage,
                estimated_cost_usd=cost,
            )
            store.write(run_id, "result.json", result.model_dump(mode="json"))
            store.finish(
                run_id,
                "completed",
                result_sha256=sha256(store.read(run_id, "result.json")),
                result_state=result.state,
            )
            return Outcome(result, False)
        except BaseException as exc:
            store.finish(
                run_id,
                "interrupted"
                if isinstance(exc, (KeyboardInterrupt, SystemExit))
                else "failed",
                error=type(exc).__name__,
                completed_sections=len(sections),
                usage=usage,
            )
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise SummaryRunError(run_id, type(exc).__name__) from None
