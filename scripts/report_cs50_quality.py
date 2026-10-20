"""Read an existing pilot, report deterministic diagnostics; no inference."""

import argparse
import json
from pathlib import Path

from src.model_knowledge.data_knowledge import (
    TranscriptChunk,
    TranscriptKnowledgeDocument,
)
from src.tools_knowledge.cs50_quality import quality_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--worker-report", type=Path)
    parser.add_argument("--evidence-bindings", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    document = TranscriptKnowledgeDocument.model_validate_json(
        args.extraction.read_bytes()
    )
    chunks = [
        TranscriptChunk.model_validate(value)
        for value in json.loads(args.chunks.read_text())
    ]
    worker = json.loads(args.worker_report.read_text()) if args.worker_report else None
    audit = None
    if args.evidence_bindings:
        bindings = json.loads(args.evidence_bindings.read_text())
        if (
            not document.source_id
            or bindings.get("schema_version") != 1
            or bindings.get("source_id") != document.source_id
            or bindings.get("resource_id") != document.source_id
        ):
            raise ValueError("Evidence audit version/source mismatch")
        audit = bindings.get("items", [])
    report = quality_report(
        document, chunks, worker_report=worker, evidence_audit=audit
    )
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
