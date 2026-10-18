"""Explicit offline inputs, exclusive deterministic reports; no retrieval execution."""

import argparse
import os
import stat
import sys
from pathlib import Path

from src.content_store.errors import ContentStoreError
from src.content_store.models import canonical, sha256
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet,
    EvaluationConfig,
    RetrievalResults,
)
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_materials.quality import _json

LIMIT = 32 * 1024**2


def read_input(path, model):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or path.resolve() != path:
        raise ValueError("explicit regular input path required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
            raise ValueError("input type or size limit")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("input size limit")
    value = _json(data)
    canonical(value)  # Enforces depth, Unicode and finite-number bounds.
    return model.model_validate(value)


def publish(report, output, *, input_files=()):
    output = Path(output)
    if (
        not output.is_absolute()
        or ".." in output.parts
        or output.parent.resolve() != output.parent
    ):
        raise ValueError("explicit new output required")
    if any(p == output or p.is_relative_to(output) for p in map(Path, input_files)):
        raise ValueError("output overlaps inputs")
    output.mkdir(mode=0o700, exist_ok=False)
    body = report.report
    markdown = (
        f"# Retrieval evaluation: {body.origin}\n\n"
        f"Dataset `{body.dataset_version}`; digest `{report.digest}`.\n\n"
        f"Queries: {body.query_count}; evaluable: {body.evaluable_queries}; excluded: {body.excluded_queries}.\n\n"
        "| Metric | Macro value | Included queries | Excluded queries |\n"
        "| --- | ---: | ---: | ---: |\n"
    )
    for name in ("precision_at_k", "recall_at_k", "mrr_at_k", "ndcg_at_k"):
        m = getattr(body, name)
        markdown += f"| {name} | {m.value if m.value is not None else 'not_evaluable'} | {m.denominator} | {m.excluded} |\n"
    markdown += (
        f"\nRelease blocker: {body.release_blocker}. Real acceptance: **blocked**.\n\n"
    )
    markdown += "Synthetic metrics validate arithmetic only. Live authorization is not rechecked by this offline runner.\n\n"
    for q in body.queries:
        markdown += f"- Query `{q.query_key}`: {q.status}; reasons={','.join(q.reasons) or 'none'}; technical={','.join(q.technical_failures) or 'none'}.\n"
    data = {
        "report.v1.json": canonical(report.model_dump(mode="json")) + b"\n",
        "summary.md": markdown.encode(),
    }
    data["manifest.json"] = (
        canonical(
            {
                "schema_version": 1,
                "files": {name: sha256(raw) for name, raw in sorted(data.items())},
            }
        )
        + b"\n"
    )
    for name, raw in data.items():
        fd = os.open(
            output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        dataset = read_input(args.dataset, ContentRetrievalEvaluationSet)
        results = read_input(args.results, RetrievalResults)
        report = evaluate_retrieval(
            dataset, results, evaluation_config=EvaluationConfig(schema_version=1)
        )
        publish(report, args.output, input_files=(args.dataset, args.results))
        print(
            f"{report.report.origin}: {report.report.evaluable_queries}/{report.report.query_count} evaluable; real acceptance blocked; digest={report.digest}"
        )
        return 1 if report.report.release_blocker else 0
    except (OSError, ValueError, RecursionError, ContentStoreError):
        print("Retrieval evaluation input or report rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
