"""Replay the integrated C2 synthetic review/FTS5 experiment, with real Search HTTP.

Test fixtures are the only inputs; no real corpus or alternative gold models.
"""

import argparse
import json
from pathlib import Path

from scripts.content_retrieval_evaluation import publish
from src.content_store.models import canonical, sha256
from src.content_store.search_models import SearchSettings
from src.content_store.store import ContentStore
from src.job_control.http import Application
from src.model_evaluation.content_retrieval import EvaluationConfig
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_lecture.execute_cs50 import safe_path
from src.tools_rag.content_index import ContentIndex
from tests.content_store_support import OWNER
from tests.review_support import api, token
from tests.test_content_fts import inventory
from tests.test_review_fts_pilot import evaluate, export, pilot, review_all, search

ROOT = Path(__file__).resolve().parents[2]


def application(env):
    from src.job_control.controller import Controller

    return Application(
        Controller(env.app.controller.settings),
        content_settings=env.settings.content,
        review_settings=env.settings,
        search_settings=SearchSettings(schema_version=1, index_root=env.index.root),
    )


def http_pages(env, dataset, results):
    for q, expected in zip(dataset.queries, results.queries, strict=True):
        response = env.app.request(
            "POST",
            "/v1/content/search",
            {"Authorization": "Bearer " + token(OWNER.subject)},
            canonical(
                dict(
                    schema_version=1,
                    query=q.text,
                    source_ids=[env.pv.source_id],
                    course_id="cs50_python",
                    limit=dataset.retrieval.k,
                )
            ),
        )
        try:
            code, raw, _ = response
            if code != 200 or json.loads(raw) != expected.page.model_dump(mode="json"):
                raise ValueError("Search HTTP differs from scoped FTS5 result")
        finally:
            if hasattr(response, "close"):
                response.close()


def run(workspace, output):
    workspace, output = Path(workspace).absolute(), Path(output).absolute()
    for p in (workspace, output):
        safe_path(p.parent, p)
        if p.exists() or p.is_relative_to(ROOT) or ROOT.is_relative_to(p):
            raise ValueError("New external synthetic paths required")
    if output.is_relative_to(workspace) or workspace.is_relative_to(output):
        raise ValueError("Separate input/output roots required")
    workspace.mkdir(mode=0o700, parents=True)
    # Existing integrated C2 fixture implementation, not a parallel pipeline.
    env = pilot.__wrapped__(workspace)
    env.app = application(env)
    before, raw_before = inventory(env.content.root), inventory(env.bundle.workspace)
    review_all(env)  # Authored synthetic actions, never actual human confirmation.
    dataset, exported = export(env)
    if dataset.origin != "synthetic" or len(dataset.queries) != 5:
        raise ValueError("Unexpected synthetic input scope")
    results = search(env, dataset)
    http_pages(env, dataset, results)
    report = evaluate_retrieval(
        dataset, results, evaluation_config=EvaluationConfig(schema_version=1)
    )
    persisted = evaluate(env, results)
    if persisted["value"]["report"]["digest"] != report.digest:
        raise ValueError("Persisted/standalone evaluation mismatch")
    # Reopen all read paths; never rebuild the index or reimport source data.
    env.index = ContentIndex(
        ContentStore(env.content.root), env.index.root, cursor_key_file=env.key
    )
    env.app = application(env)
    repeated = search(env, dataset)
    if canonical(repeated.model_dump(mode="json")) != canonical(
        results.model_dump(mode="json")
    ):
        raise ValueError("Search replay changed after reopen")
    http_pages(env, dataset, repeated)
    if (
        api(env, "GET", "/exports/gold") != exported
        or api(env, "GET", "/reports/report")["value"] != persisted["value"]
    ):
        raise ValueError("Review/report replay changed after reopen")
    if (
        inventory(env.content.root) != before
        or inventory(env.bundle.workspace) != raw_before
    ):
        raise ValueError("Original/source store changed during evaluation")
    output.mkdir(mode=0o700, parents=True)
    data = output / "data"
    data.mkdir(mode=0o700)
    for name, value in [
        ("dataset.v1.json", dataset.model_dump(mode="json")),
        ("results.v1.json", results.model_dump(mode="json")),
        ("parsing-gold.v1.json", exported["parsing"]),
    ]:
        with (data / name).open("xb") as stream:
            stream.write(canonical(value) + b"\n")
    publish(report, output / "evaluation", input_files=tuple(data.iterdir()))
    files = {
        p.relative_to(output).as_posix(): sha256(p.read_bytes())
        for p in output.rglob("*")
        if p.is_file()
    }
    (output / "manifest.json").write_bytes(
        canonical(dict(schema_version=1, origin="synthetic", files=files)) + b"\n"
    )
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        report = run(a.workspace, a.output)
    except (ValueError, OSError):
        print("Synthetic retrieval recipe rejected or failed; real inputs forbidden")
        return 2
    print(
        "Synthetic queries="
        + str(report.report.query_count)
        + "; real_acceptance=blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
