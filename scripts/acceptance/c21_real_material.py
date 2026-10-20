"""Separate explicit local-original profile using existing C10/C13 contracts.

No source discovery outside the supplied reviewed manifest, no network, no edits
to originals. Retains a new private workspace for subsequent human review.
"""

import argparse
import hashlib
import json
import socket
from collections import Counter
from pathlib import Path

from src.model_materials.materials import NormalizedDocument
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials.processing import MaterialProcessor, make_plan
from src.tools_materials.visual_inventory import inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        parser.error("Output already exists")
    output = output.resolve()
    repository = Path(__file__).resolve().parents[2]
    if output.is_relative_to(repository) or repository.is_relative_to(output):
        parser.error("Real-material workspace must be external to the checkout")
    if any(p.resolve().is_relative_to(output) for p in (args.manifest, args.source)):
        parser.error("Output must not contain an input")

    def forbidden(*args, **kwargs):
        raise RuntimeError("Local original profile forbids network")

    socket.socket.connect = forbidden
    socket.getaddrinfo = forbidden
    # Bind original bytes to the existing manifest URL and its declared SHA.
    manifest = json.loads(args.manifest.read_bytes())
    matches = [
        p
        for c in manifest["courses"]
        for p in c["pages"]
        if p["url"] == args.source_url
    ]
    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if len(matches) != 1 or matches[0]["sha256"] != digest:
        parser.error("Original bytes/URL do not match the reviewed snapshot manifest")
    plan = make_plan(args.manifest)
    selected = [b for b in plan.materials if b.original_url == args.source_url]
    if len(selected) != 1 or not selected[0].lecture_ids:
        parser.error("Exactly one existing Course/Lecture material binding required")
    binding = selected[0]
    output.mkdir(mode=0o700)
    workspace = output / "artifacts"
    processor = MaterialProcessor(workspace)
    processor.downloader.obtain(binding, execute=True, local_file=args.source)
    receipt = processor.parse(binding, execute=True)
    raw_path, receipt_path = processor.downloader.paths(binding)
    normalized = workspace / receipt.normalized_path
    plan_path = workspace / "plan.json"
    plan_path.write_text(plan.model_dump_json(indent=2))
    review = prepare_material_handoff(
        normalized_path=normalized,
        receipt_path=receipt_path,
        raw_path=raw_path,
        plan_path=plan_path,
        workspace=workspace,
    )
    visual = inventory(
        normalized,
        input_root=workspace,
        raw_path=raw_path,
        receipt_path=receipt_path,
        plan_path=plan_path,
    )
    document = NormalizedDocument.model_validate_json(normalized.read_bytes())
    # Full existing contracts remain local; only the compact observations need publishing.
    for name, value in (("review.json", review), ("visual.json", visual)):
        with (output / name).open("x", encoding="utf-8") as stream:
            stream.write(value.model_dump_json(indent=2) + "\n")
    summary = dict(
        schema_version=1,
        source_origin="real_local_snapshot",
        source_url=args.source_url,
        source_sha256=digest,
        document_id=document.document_id,
        binding=binding.model_dump(mode="json"),
        parser=document.parser.model_dump(mode="json"),
        normalized_sha256=receipt.normalized_sha256,
        quality_status=review.report.status,
        findings=[f.model_dump(mode="json") for f in review.report.findings],
        handoff_available=review.handoff is not None,
        block_types=dict(Counter(b.type for b in document.blocks)),
        visual_counts=visual.counts,
        visual_warnings=[w.model_dump(mode="json") for w in visual.warnings],
        visual_assets=[
            dict(
                asset_id=a.asset_id,
                type=a.asset_type,
                artifact_status=a.artifact_status,
                extraction_status=a.extraction_status,
                warnings=[w.model_dump(mode="json") for w in a.warnings],
            )
            for a in visual.assets
        ],
        raw_scan=visual.raw_scan,
        binding_verification=visual.binding_verification,
        semantic_review="not tested",
        formula_gold_evaluation="blocked: independent real gold not supplied",
        original_preserved=hashlib.sha256(args.source.read_bytes()).hexdigest()
        == digest,
    )
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            dict(
                quality_status=review.report.status,
                handoff_available=review.handoff is not None,
            )
        )
    )
    return 0 if review.report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
