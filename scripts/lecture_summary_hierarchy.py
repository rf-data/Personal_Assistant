"""C27-C reproducible offline setup, budget comparison and three real-source demos."""

import argparse
import json
from pathlib import Path

from scripts.lecture_summary_acceptance import CASES, selection
from scripts.lecture_summary_legacy import publish, workspace
from src.content_store.models import sha256
from src.lecture_summary.exports import filename, render
from src.lecture_summary.hierarchy import bound, make_plan, public_plan
from src.lecture_summary.local import load_service
from src.lecture_summary.models import HierarchyPolicy
from src.lecture_summary.providers import MockProvider, SummaryProvider
from src.lecture_summary.service import SummaryService
from src.lecture_summary.sources import collect


def prepare(config_path, target):
    service = load_service(config_path, offline_only=True)
    policy = HierarchyPolicy()
    for ids in CASES.values():
        chosen = selection(ids)
        evidence, _ = collect(service.catalog, chosen, service.storage)
        make_plan(evidence, chosen, service.provider.model, policy, offline=True)
    source_ids = {
        a.storage_id for lecture in service.catalog.lectures for a in lecture.sources
    }
    if "hierarchy_workspace" in source_ids or any(
        not service.storage.roots[k][1] for k in source_ids
    ):
        raise ValueError(
            "Explicit read-only source roots required; reserved workspace ID"
        )
    roots = {
        k: {"path": str(service.storage.roots[k][0]), "readonly": True}
        for k in source_ids
    }
    output = workspace(target)
    output.create(
        "output", "catalog.json", service.catalog.model_dump_json(indent=2).encode()
    )
    output.path("output", "cache", write=True).mkdir(mode=0o700)
    roots["hierarchy_workspace"] = dict(path=str(target), readonly=False)
    settings = dict(
        schema_version=1,
        catalog="catalog.json",
        storage_roots=roots,
        model="mock-extractive-v1",
        allow_source_upload=False,
        cache=["hierarchy_workspace", "cache"],
    )
    publish(output, "summary.simple.json", settings)
    publish(
        output,
        "summary.json",
        settings
        | dict(strategy="hierarchical", hierarchy=policy.model_dump(mode="json")),
    )
    return target / "summary.json"


def demo(config_path, target, model_label):
    service = load_service(config_path, offline_only=True)
    if service.hierarchy is None:
        raise ValueError("Explicit hierarchical offline configuration required")
    if not model_label.strip() or len(model_label) > 200:
        raise ValueError("Bounded nonempty model label required (no client is created)")

    class Recording(MockProvider):
        def __init__(self):
            self.calls = []

        def hierarchical(self, req, result_type):
            self.calls.append(
                dict(
                    input_upper_bound=bound(req),
                    output_limit=req["max_completion_tokens"],
                )
            )
            return super().hierarchical(req, result_type)

    service.provider = Recording()
    simple = SummaryService(service.catalog, service.storage, MockProvider())
    sources = [a for lecture in service.catalog.lectures for a in lecture.sources]
    before = {
        a.artifact_id: sha256(service.storage.read(a.storage_id, a.relative_path))
        for a in sources
    }
    output = workspace(target)
    report = dict(
        schema_version=1,
        model_label_for_budget_only=model_label,
        paid_api_calls=0,
        cases={},
    )
    for case, ids in CASES.items():
        chosen = selection(ids)
        evidence, _ = collect(service.catalog, chosen, service.storage)
        single = SummaryProvider.request_payload(evidence, chosen, model=model_label)
        prospective = make_plan(
            evidence, chosen, model_label, service.hierarchy, offline=True
        )
        start = len(service.provider.calls)
        results = dict(
            simple=simple.generate(chosen), hierarchical=service.generate(chosen)
        )
        sizes = {}
        for mode, result in results.items():
            folder = f"{case}-{mode}"
            output.path("output", folder, write=True).mkdir(mode=0o700)
            sizes[mode] = {}
            for extension in ("md", "tex", "json"):
                data = (
                    result.model_dump_json(indent=2)
                    if extension == "json"
                    else render(result, latex=extension == "tex")
                ).encode()
                output.create(
                    "output", folder + "/" + filename(result, extension), data
                )
                sizes[mode][extension] = len(data)
        processing = results["hierarchical"].processing
        report["cases"][case] = dict(
            lecture_ids=ids,
            source_blocks=len(evidence),
            simple_request_input_bound=bound(single),
            simple_request_fits=bound(single) <= 30000,
            simple_mock_status=results["simple"].validation_status,
            hierarchy_plan_for_label=public_plan(prospective),
            hierarchy_status=results["hierarchical"].validation_status,
            hierarchy_processing=processing.model_dump(mode="json"),
            actual_mock_dispatches=service.provider.calls[start:],
            export_bytes=sizes,
        )
    after = {
        a.artifact_id: sha256(service.storage.read(a.storage_id, a.relative_path))
        for a in sources
    }
    if before != after or any(before[a.artifact_id] != a.sha256 for a in sources):
        raise ValueError("Source changed during offline demonstration")
    report["all_source_fingerprints_unchanged"] = True
    publish(output, "comparison.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "demo"):
        p = sub.add_parser(command)
        p.add_argument("--config", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        if command == "demo":
            p.add_argument("--model-label", default="offline-budget-probe")
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.config, args.output))
    else:
        report = demo(args.config, args.output, args.model_label)
        print(
            json.dumps(
                dict(
                    paid_api_calls=0,
                    sources_unchanged=report["all_source_fingerprints_unchanged"],
                    cases={
                        key: dict(
                            simple_input=v["simple_request_input_bound"],
                            hierarchy_reservation=v["hierarchy_plan_for_label"][
                                "token_upper_bound"
                            ],
                            requests=v["hierarchy_plan_for_label"]["max_requests"],
                            status=v["hierarchy_status"],
                        )
                        for key, v in report["cases"].items()
                    },
                ),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
