"""Deterministic report serialization and explicit exclusive bundle publication."""

import hashlib
import json
from pathlib import Path

from src.tools_lecture.execute_cs50 import safe_path
from src.tools_materials.storage import publish_bytes


def _cell(value):
    return (
        str(value)
        .replace("|", r"\|")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("`", "'")
    )


def markdown_report(report):
    lines = [
        "# Formula reconstruction evaluation v1",
        "",
        "Offline evaluation harness; synthetic examples are not model quality measurements.",
        "",
        f"Input SHA-256: `{report.input_sha256}`",
        f"Equivalence backend: `{report.equivalence_backend}`",
        "",
        "Exact/normalized rates use paired_count: confirmed gold and a present prediction, neither marked ambiguous; includes unsupported notation. Null means a zero denominator.",
        "Evaluable means a decided reconstruction status; it includes missing/extra formulas and explicit partial reconstructions. Symbolic identity is separate from notation identity.",
        "",
        "| Gold origin | Cases | Evaluable | Paired | Exact rate | Normalized rate | Structural matches/comparable | Equivalent | Via SymPy | Undetermined |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for origin, m in report.metrics.items():

        def rate(v):
            return "n/a" if v is None else f"{v:.4f}"

        lines.append(
            f"| {origin} | {m.case_count} | {m.evaluable_count} | {m.paired_count} | {rate(m.exact_match_rate)} | {rate(m.normalized_match_rate)} | {m.structural_matches}/{m.structure_comparable_count} | {m.equivalent_count} | {m.symbolic_equivalent_count} | {m.undetermined_count} |"
        )
    lines += [
        "",
        "## Error category counts",
        "",
        "| Gold origin | Category | Count |",
        "|---|---|---:|",
    ]
    for origin, m in report.metrics.items():
        for category, count in m.error_frequencies.items():
            lines.append(f"| {origin} | {category} | {count} |")
    lines += [
        "",
        "## Cases requiring review",
        "",
        "| Case | Status | Source | Categories | Decision |",
        "|---|---|---|---|---|",
    ]
    for result in report.results:
        if result.case.case_id in report.failed_case_ids:
            source = f"{result.case.source_reference}; page={result.case.page}; section={result.case.section}"
            lines.append(
                "| "
                + " | ".join(
                    _cell(v)
                    for v in (
                        result.case.case_id,
                        result.evaluation_status,
                        source,
                        ", ".join(result.error_categories),
                        result.equivalence.reason,
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def publish_report(report, output):
    output = Path(output).absolute()
    safe_path(output.parent, output)
    # The directory reservation is exclusive; a completion manifest is written
    # last. Never replace even an existing empty directory or incomplete bundle.
    output.mkdir(parents=True, exist_ok=False)
    raw = (report.model_dump_json(indent=2) + "\n").encode()
    markdown = markdown_report(report).encode()
    files = {"report.json": raw, "summary.md": markdown}
    for name, content in files.items():
        publish_bytes(output / name, content)
    manifest = {
        "schema_version": 1,
        "input_sha256": report.input_sha256,
        "files": {
            name: hashlib.sha256(content).hexdigest() for name, content in files.items()
        },
    }
    publish_bytes(
        output / "manifest.json",
        (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode(),
    )
    return manifest
