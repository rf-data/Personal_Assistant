"""Offline corpus/review evaluation with explicit roots and exclusive reports."""

import argparse
import sys
from pathlib import Path

from src.content_store.errors import ContentStoreError
from src.content_store.inventory import _paths
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.tools_evaluation.evaluate_materials import evaluate, load_inputs, publish


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument(
        "--root",
        action="append",
        required=True,
        help="Explicit key=/absolute/root; no scan",
    )
    parser.add_argument("--actor", required=True)
    parser.add_argument("--course", action="append", required=True)
    parser.add_argument(
        "--store", type=Path, help="Optional existing read-only ContentStore"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New output directory outside all inputs",
    )
    args = parser.parse_args(argv)
    try:
        roots = {}
        for item in args.root:
            key, value = item.split("=", 1)
            if key in roots or not key or not Path(value).is_absolute():
                raise ValueError("Duplicate or nonabsolute root")
            roots[key] = Path(value)
        corpus, gold = load_inputs(args.corpus, args.gold)
        if set(roots) != {e.root_key for e in corpus.entries}:
            raise ValueError("Provide exactly the roots referenced by the corpus")
        actor = Principal(
            subject=args.actor, role="operator", courses=tuple(args.course)
        )
        store = ContentStore(args.store) if args.store else None
        report = evaluate(corpus, gold, roots=roots, actor=actor, store=store)
        publish(
            report,
            args.output,
            input_roots=[*roots.values(), *([store.root] if store else [])],
            input_files=[
                args.corpus,
                args.gold,
                *[
                    path
                    for entry in corpus.entries
                    if entry.selection is not None
                    for path in _paths(entry.selection).values()
                ],
            ],
        )
        body = report.report
        print(
            f"Technical corpus report: {len(body['inventory'])} entries; gold={body['gold_counts']}; real acceptance requires review"
        )
        for row in body["inventory"]:
            print(
                f"{row['entry_id']}: {row['classification']} course={row['course_id']} lectures={row['lecture_ids']} issues={','.join(row['issues'])}"
            )
        return 1 if any(r["status"] == "failed" for r in body["results"]) else 0
    except (OSError, ValueError, KeyError, RecursionError, ContentStoreError):
        print("Corpus input, access or report publication rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
