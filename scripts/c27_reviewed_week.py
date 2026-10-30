"""Explicit offline C27 review processing, with optional fake summary smoke."""

import argparse
from pathlib import Path

from src.c27_learning_summary.engine import SummaryRunError, generate
from src.c27_learning_summary.export import markdown, public_processing_report
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import SummaryConfig
from src.c27_learning_summary.reviewed_week import process_review
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import canonical


def run(review_root, output, *, fake_summary=False, material_ids=None):
    output = Path(output).absolute()
    catalog, report, reused = process_review(review_root, output / "processing")
    result = dict(report, processing_reused=reused, summaries=[])
    available = {
        m.material_id
        for c in catalog.courses
        for w in c.weeks
        for u in w.units
        for m in u.materials
    }
    if material_ids is not None and (
        not material_ids
        or len(set(material_ids)) != len(material_ids)
        or not set(material_ids) <= available
    ):
        raise ValueError("Explicit unique processed material IDs required")
    result["summary_selection"] = sorted(
        available if material_ids is None else material_ids
    )
    if fake_summary:
        store = SummaryStore(output / "summaries")
        course = catalog.courses[0]
        week = course.weeks[0]
        for unit in week.units:
            # Omitted sources remain visible in the processing report and catalog.
            selected = [
                m.material_id
                for m in unit.materials
                if material_ids is None or m.material_id in material_ids
            ]
            if not selected:
                continue
            model = FakeLLM()
            try:
                outcome = generate(
                    store,
                    catalog,
                    course.course_id,
                    week.section_id,
                    unit.section_id,
                    selected,
                    SummaryConfig(),
                    model,
                )
            except (ValueError, SummaryRunError) as error:
                result["summaries"].append(
                    dict(
                        unit_id=unit.section_id,
                        state="blocked",
                        reason=str(error),
                        cache_verified=False,
                        fake_calls=model.calls,
                    )
                )
                continue
            cache_verified = False
            if outcome.result.state == "ready_for_review":
                cached = store.cached(outcome.result.cache_key)
                cache_verified = (
                    cached is not None and cached.run_id == outcome.result.run_id
                )
            result["summaries"].append(
                dict(
                    unit_id=unit.section_id,
                    run_id=outcome.result.run_id,
                    claims=len(outcome.result.claims),
                    sections=len(outcome.result.sections),
                    fake_calls=model.calls,
                    cache_verified=cache_verified,
                    state=outcome.result.state,
                    selected_material_ids=selected,
                )
            )
            if outcome.result.state == "ready_for_review" and not cache_verified:
                result["summaries"][-1]["cache_verification_error"] = (
                    "completed_result_not_cached"
                )
            reviews = store.reviews(outcome.result.run_id)
            # Preserve earlier exports while recording the current review snapshot.
            basename = (
                f"export-review-{reviews[-1]['review_id']}" if reviews else "export"
            )
            result["summaries"][-1]["exports"] = dict(
                markdown=basename + ".md", json=basename + ".json"
            )
            store.publish(
                outcome.result.run_id,
                basename + ".md",
                markdown(outcome.result, reviews).encode(),
            )
            store.publish(
                outcome.result.run_id,
                basename + ".json",
                store.export_json(outcome.result.run_id).encode(),
            )
    return public_processing_report(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fake-summary", action="store_true")
    parser.add_argument(
        "--material-id",
        action="append",
        default=None,
        help="Explicit subset for summary; repeat for multiple materials",
    )
    args = parser.parse_args(argv)
    # No option enables a provider, download or publication.
    result = run(
        args.review_root,
        args.output,
        fake_summary=args.fake_summary,
        material_ids=args.material_id,
    )
    print(canonical(result).decode())


if __name__ == "__main__":
    main()
