"""Technical gates and conservative evidence states, not semantic verification."""

import re

from src.lecture_summary.models import Formula
from src.tools_evaluation.math_syntax import FormulaSyntaxError, parse_formula

MAX_OUTPUT_BYTES = 70000


def claims(draft):
    yield from draft.learning_objectives
    yield from draft.prerequisites
    for topic in draft.topics:
        for group in (
            topic.explanations,
            topic.definitions,
            topic.formulas,
            topic.examples,
            topic.misconceptions,
            topic.questions,
        ):
            yield from group
    yield from draft.takeaways


def safe_formula(latex):
    if any(c in latex for c in ("%", "$", "&", "#", "\x00")):
        return False
    try:
        parse_formula(latex, "latex")
        return True
    except (FormulaSyntaxError, ValueError):
        return False


def validate(draft, evidence, selection):
    errors, review = (
        [],
        [
            "Automatische technische Prüfung; Inhalt und Mathematik sind nicht fachlich bewiesen."
        ],
    )
    sources = {e.source_id: e for e in evidence}
    if len(sources) != len(evidence):
        errors.append("Duplicate evidence identity")
    if not draft.title.strip() or any(
        not topic.title.strip() for topic in draft.topics
    ):
        errors.append("Empty thematic title")
    selected = set(selection.lecture_ids)
    processed, missing = (
        set(draft.processed_lecture_ids),
        set(draft.missing_lecture_ids),
    )
    if (
        processed & missing
        or processed | missing != selected
        or len(processed) != len(draft.processed_lecture_ids)
        or len(missing) != len(draft.missing_lecture_ids)
    ):
        errors.append("Lecture coverage contradicts explicit selection")
    if missing:
        review.append("Explicitly missing lectures: " + ", ".join(sorted(missing)))
    if len(draft.model_dump_json().encode()) > MAX_OUTPUT_BYTES:
        errors.append("Output exceeds byte limit")
    seen, covered = set(), set()
    for claim in claims(draft):
        if not claim.text.strip():
            errors.append("Empty substantive statement")
        if len(claim.source_ids) != len(set(claim.source_ids)):
            errors.append("Duplicate evidence reference")
        if not set(claim.source_ids) <= sources.keys():
            errors.append("Unknown evidence reference")
            continue
        cited = [sources[key] for key in claim.source_ids]
        if claim.kind == "external":
            errors.append("External enrichment is disabled")
        if claim.kind == "derived" and not cited:
            errors.append("Derived statement without source")
        if not cited and claim.quality != "unsupported":
            errors.append("Unsourced explanation must be explicitly unsupported")
        if claim.evidence_quote and any(
            claim.evidence_quote not in s.text for s in cited
        ):
            errors.append("Evidence quote absent from cited source")
        if claim.quality == "verified_from_source":
            if (
                not cited
                or claim.evidence_quote != claim.text
                or any(
                    claim.text not in s.text
                    or s.artifact_role != "original"
                    or s.warnings
                    for s in cited
                )
            ):
                errors.append(
                    "Verified claim lacks an exact unambiguous original excerpt"
                )
        else:
            review.append("Generated or uncertain content requires review")
        covered.update(s.lecture_id for s in cited)
        if isinstance(claim, Formula):
            if not claim.notation.strip() or not claim.assumptions.strip():
                errors.append("Formula notation or assumptions missing")
            if not safe_formula(claim.latex):
                review.append("Formula syntax unsupported; export as escaped text")
            if claim.quality == "verified_from_source" and (
                not safe_formula(claim.latex)
                or any(claim.latex not in s.text for s in cited)
            ):
                errors.append(
                    "Verified formula not present literally in original source"
                )
        # Duplicated objectives/takeaways can be legitimate; large copies cannot.
        normalized = re.sub(r"\s+", " ", claim.text).strip().casefold()
        if len(normalized) >= 220:
            if normalized in seen:
                errors.append("Duplicated large content block")
            seen.add(normalized)
    if not processed <= covered:
        errors.append("Processed lecture missing from evidence citations")
    if len({t.title.strip().casefold() for t in draft.topics}) != len(draft.topics):
        errors.append("Duplicate topic headings")
    return ("failed" if errors else "needs_review"), tuple(
        dict.fromkeys(errors + review)
    )
