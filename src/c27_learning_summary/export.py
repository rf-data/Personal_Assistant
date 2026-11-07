"""Human-readable, source-complete views over a single immutable result."""

import json
from typing import Any

from src.c27_learning_summary.export_policy import exportable_source_url, metadata
from src.c27_learning_summary.models import Review, SourceRef, SummaryResult


def public_result(result: SummaryResult) -> SummaryResult:
    """Project metadata at the last boundary without changing private results.

    Only SourceRef.text and Claim.text (including section claims) are learning
    prose. Everything else in the strict result schema is structured metadata.
    Revalidation also checks constructed/mutated models and upgrades v1 in memory.
    """
    try:
        data = json.loads(result.model_dump_json(warnings=False))

        def excerpt(item: dict[str, Any]) -> dict[str, Any]:
            return dict(
                metadata({k: v for k, v in item.items() if k != "text"}),
                text=item["text"],
            )

        public = metadata(
            {k: v for k, v in data.items() if k not in {"refs", "sections", "claims"}}
        )
        public["refs"] = [excerpt(ref) for ref in data["refs"]]
        public["claims"] = [excerpt(claim) for claim in data["claims"]]
        public["sections"] = [
            dict(
                metadata({k: v for k, v in section.items() if k != "claims"}),
                claims=[excerpt(claim) for claim in section["claims"]],
            )
            for section in data["sections"]
        ]
        return SummaryResult.model_validate_json(json.dumps(public))
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise ValueError("Public export validation failed") from None


def public_reviews(reviews: Any) -> list[dict[str, Any]]:
    events = []
    try:
        for event in reviews:
            # Unknown event/provider metadata is never copied into the export.
            review = event["review"]
            if isinstance(review, Review):
                review = review.model_dump(mode="json", warnings=False)
            events.append(
                dict(
                    metadata(
                        {
                            k: event[k]
                            for k in ("review_id", "saved_ns", "result_sha256")
                        }
                    ),
                    review=Review.model_validate_json(
                        json.dumps(metadata(review))
                    ).model_dump(mode="json"),
                )
            )
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ValueError("Public review export validation failed") from None
    return events


def public_processing_report(report: dict[str, Any]) -> dict[str, Any]:
    """CLI stdout is an export; local processing records remain private."""
    fields = (
        "version",
        "course_id",
        "week_id",
        "evidence_kind",
        "full_week_acceptance",
        "license_approval",
        "llm_calls",
        "downloads",
        "processing_reused",
        "summary_selection",
    )
    public: dict[str, Any] = metadata({k: report[k] for k in fields if k in report})
    public["materials"] = []
    for row in report.get("materials", []):
        record = metadata(
            {
                k: row[k]
                for k in (
                    "filename",
                    "material_id",
                    "unit_id",
                    "raw_sha256",
                    "status",
                    "blocks",
                    "summary_status",
                    "members",
                )
                if k in row
            }
        )
        url = row.get("source_url")
        allowed = exportable_source_url(url)
        record.update(
            source_url=allowed,
            source_url_status=(
                "missing" if url is None else "available" if allowed else "withheld"
            ),
        )
        public["materials"].append(record)
    public["summaries"] = [
        metadata(
            {
                k: row[k]
                for k in (
                    "unit_id",
                    "run_id",
                    "claims",
                    "sections",
                    "fake_calls",
                    "cache_verified",
                    "state",
                    "reason",
                    "selected_material_ids",
                    "exports",
                    "cache_verification_error",
                )
                if k in row
            }
        )
        for row in report.get("summaries", [])
    ]
    return public


def visible_claims(result):
    kind = result.config.summary_type
    claims = result.claims
    if kind == "overview":
        priority = [
            "learning_objective",
            "key_point",
            "concept",
            "definition",
            "explanation",
            "formula",
            "code",
        ]
        return tuple(sorted(claims, key=lambda c: priority.index(c.category)))[:3]
    if kind == "glossary":
        return tuple(c for c in claims if c.category in {"definition", "concept"})
    if kind == "code":
        return tuple(c for c in claims if c.category in {"code", "explanation"})
    return claims


def source_label(ref):
    try:
        data = json.loads(ref.model_dump_json(warnings=False))
        text = data.pop("text")
        ref = SourceRef.model_validate_json(json.dumps(dict(metadata(data), text=text)))
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ValueError("Public source label validation failed") from None
    positions = []
    for loc in ref.locators:
        position = loc.origin_pointer
        if loc.original_segment_id is not None:
            position += f" segment={loc.original_segment_id}"
        if loc.time_status == "known":
            position += f" t={loc.start:g}–{loc.end:g}s"
        elif loc.time_status == "unknown":
            position += " time=unknown"
        if loc.page:
            position += f" page={loc.page}"
        if loc.dom:
            position += f" DOM={loc.dom}"
        if loc.line_start:
            position += f" lines={loc.line_start}–{loc.line_end or loc.line_start}"
        positions.append(position)
    return f"{ref.source_path} | {ref.block_id} | chars={ref.offset_start}:{ref.offset_end} | {'; '.join(positions)}"


def markdown(result, reviews=()):
    result = public_result(result)
    reviews = public_reviews(reviews)
    numbers = {r.ref_id: i + 1 for i, r in enumerate(result.refs)}
    lines = [
        f"# {result.title}",
        "",
        f"Run: `{result.run_id}`",
        "",
        f"Type: {result.config.summary_type}; status: {result.state}",
        "",
        "Extractive draft; human source review required.",
        "",
    ]
    for warning in result.warnings:
        lines += [f"> {warning}", ""]
    claims = visible_claims(result)
    if not claims:
        lines += ["No source-supported items for this view.", ""]
    for claim in claims:
        citations = " ".join(
            f"[source {numbers[r]}](#source-{numbers[r]})" for r in claim.refs
        )
        lines += [f"## {claim.category}", "", claim.text, "", citations, ""]
    lines += ["## Sources", ""]
    for i, ref in enumerate(result.refs, 1):
        lines += [
            f"### Source {i}",
            "",
            source_label(ref),
            "",
            f"Course: {ref.course_id}; week: {ref.week_id}; lecture/short: {ref.lecture_id}",
            "",
            f"Material: {ref.material_id}; source: {ref.source_id}; parser: {ref.parser_version}; artifact: {ref.artifact_id}",
            "",
            f"Original SHA-256: `{ref.content_hash}`; reference: `{ref.ref_id}`",
            "",
            "Content locators:",
            "",
            "```json",
            json.dumps(
                [loc.model_dump(mode="json") for loc in ref.locators],
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            f"Original URL: {ref.provenance.source_url or ref.provenance.source_url_status}"
            if ref.provenance
            else "Original provenance: unknown (legacy result)",
            "",
            *(
                [f"Source title: {ref.provenance.title}", ""]
                if ref.provenance and ref.provenance.title is not None
                else []
            ),
            *(
                [f"License: {ref.provenance.license}", ""]
                if ref.provenance and ref.provenance.license is not None
                else []
            ),
            *(
                [f"Attribution: {ref.provenance.attribution}", ""]
                if ref.provenance and ref.provenance.attribution is not None
                else []
            ),
            "Exact stored excerpt (local-file jump unavailable):",
            "",
            *[f"> {line}" for line in ref.text.splitlines()],
            "",
        ]
    lines += [
        "Review status: "
        + (reviews[-1]["review"]["decision"] if reviews else "unreviewed"),
        "",
    ]
    if reviews:
        latest = reviews[-1]["review"]
        lines += [
            "## Review",
            "",
            f"Decision: {latest['decision']}; reviewer: {latest['reviewer']}",
            "",
            latest["comment"],
            "",
        ]
        for item in latest["claims"]:
            lines += [
                f"- `{item['claim_id']}`: {item['rating']}; recheck={item['recheck']}; {item['comment']}"
            ]
    return "\n".join(lines)
