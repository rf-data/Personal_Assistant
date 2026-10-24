"""Explicit local C27 acceptance catalog. Never downloads or calls a provider."""

import argparse
import json
from pathlib import Path

from scripts.lecture_summary import registered_lecture, write_catalog
from src.lecture_summary.models import Catalog, Selection
from src.lecture_summary.providers import SummaryProvider
from src.lecture_summary.sources import collect
from src.tools_knowledge.cs50_extraction_provider import RequestBudget
from src.tools_materials.storage import RegisteredStorage

# Observed filenames and explicit local bindings, not a historical data migration.
SOURCES = (
    ("01.01.2", "weiter_drei_Arten_Mathematik", "Weiter: Drei Arten Mathematik"),
    ("01.06.1", "Skalarprodukt", "Skalarprodukt"),
    ("01.05.1", "Rechnen_mit_Pfeilen", "Rechnen mit Pfeilen"),
    ("01.05.2", "von_Pfeilen_zu_Vektoren", "Von Pfeilen zu Vektoren"),
)
CASES = {
    "text": ("01.01.2",),
    "formulas": ("01.06.1",),
    "group": ("01.05.1", "01.05.2"),
}


def prepare(root, workspace):
    catalog = Catalog(
        lectures=tuple(
            registered_lecture(
                root,
                f"loviscach/mathe_1/transcripts/{lecture}_{stem}.json",
                "loviscach",
                "mathe_1",
                lecture,
                title,
                "transcript_json",
            )
            for lecture, stem, title in SOURCES
        )
    )
    storage = RegisteredStorage({"source": {"path": str(root), "readonly": True}})
    # Validate every proposed selection before creating the output directory.
    for ids in CASES.values():
        collect(catalog, selection(ids), storage)
    return write_catalog(workspace, root, catalog, cache=True)


def selection(ids):
    return Selection(provider_id="loviscach", course_id="mathe_1", lecture_ids=ids)


def inspect(config_path, *, model):
    """Read/hash selected sources and check the actual prompt budget, without a client."""
    from src.lecture_summary.local import load_service

    if not model.strip():
        raise ValueError("Explicit model name required for preflight")
    service = load_service(config_path, offline_only=True)
    try:
        report = {}
        for case, ids in CASES.items():
            chosen = selection(ids)
            evidence, _ = collect(service.catalog, chosen, service.storage)
            payload = SummaryProvider.request_payload(evidence, chosen, model=model)
            budget = RequestBudget(
                maximum=1, token_budget=64000, input_limit=30000, output_limit=2000
            )
            bound = len(json.dumps(payload, ensure_ascii=False).encode()) + 2048
            try:
                budget.claim(payload)
                error = None
            except ValueError as exc:
                error = str(exc)
            report[case] = {
                "lecture_ids": ids,
                "source_blocks": len(evidence),
                "input_upper_bound": bound,
                "output_limit": budget.output_limit,
                "live_budget_ok": error is None,
                "error": error,
            }
        return report
    finally:
        if hasattr(service.provider, "close"):
            service.provider.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("prepare")
    setup.add_argument("--root", type=Path, required=True)
    setup.add_argument("--workspace", type=Path, required=True)
    check = commands.add_parser("inspect")
    check.add_argument("--config", type=Path, required=True)
    check.add_argument("--model", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        print(prepare(args.root, args.workspace))
    else:
        print(json.dumps(inspect(args.config, model=args.model), indent=2))


if __name__ == "__main__":
    main()
