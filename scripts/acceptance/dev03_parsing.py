"""Synthetic acceptance recipe composing existing C23/C10/C11/C13 evaluators.

No input path/URL option: only the repository's authored synthetic fixtures.
Private generated bundles stay separate from public, existing-model reports.
"""

import argparse
import base64
from datetime import date
from pathlib import Path

from src.content_store.inventory import InventorySelection
from src.content_store.models import ContentLocator, canonical, sha256
from src.model_evaluation.material_evaluation import (
    CorpusEntry,
    CorpusManifest,
    GoldDataset,
    GoldReference,
)
from src.model_materials.materials import ArtifactReceipt
from src.model_materials.visual_inventory import VisualInventory
from src.tools_evaluation.evaluate_materials import evaluate, publish
from src.tools_evaluation.evaluate_math import evaluate_dataset
from src.tools_evaluation.math_reports import publish_report
from src.tools_lecture.execute_cs50 import safe_path
from src.tools_materials.parse_pdf import parse_pdf
from src.tools_materials.visual_inventory import inventory, json_bytes, markdown
from tests.content_adapter_support import REVISION, attest, dump, material, srt
from tests.content_store_support import OWNER

ROOT = Path(__file__).resolve().parents[2]
VERSION = "dev03-synthetic-parsing-v1"
DAY = date(2026, 10, 20)  # Authored synthetic test marker, not a human review.


def native_pdf(folder):
    bundle, old = material(folder, "pdf")
    raw = base64.b64decode(
        (ROOT / "tests/fixtures/visual_inventory/source.pdf.b64").read_bytes()
    )
    doc, blobs = parse_pdf(old.binding, raw)
    # Actual native parser repeat, before any hand-authored expected observations.
    again, again_blobs = parse_pdf(old.binding, raw)
    if doc != again or blobs != again_blobs:
        raise ValueError("Native PDF extraction is not deterministic")
    target = (
        bundle.raw_path.parent.parent
        / doc.document_id.split(":")[1]
        / "normalized.v1.json"
    )
    dump(target, doc.model_dump(mode="json"))
    bundle.raw_path.write_bytes(raw)
    for relative, data in blobs.items():
        path = target.parent / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    receipt = ArtifactReceipt.model_validate_json(
        bundle.receipt_path.read_bytes()
    ).model_copy(
        update=dict(
            raw_sha256=sha256(raw),
            normalized_path=target.relative_to(bundle.workspace).as_posix(),
            normalized_sha256=sha256(target.read_bytes()),
            image_hashes={p: sha256(b) for p, b in blobs.items()},
        )
    )
    dump(bundle.receipt_path, receipt.model_dump(mode="json"))
    bundle = bundle.model_copy(update={"normalized_path": target})
    attest(bundle)
    return bundle, doc


def corpus_inputs(workspace):
    bundles = {}
    documents = {}
    entries = []
    roots = {}
    for key, kind in [
        ("html", "html"),
        ("code", "code"),
        ("pdf-contract", "pdf"),
        ("pdf-native", "pdf"),
        ("srt", "srt"),
    ]:
        bundle, doc = (
            native_pdf(workspace / key)
            if key == "pdf-native"
            else srt(workspace / key)
            if kind == "srt"
            else material(workspace / key, kind)
        )
        sid = bundle.source_id if kind == "srt" else doc.binding.source_id
        # Native and contract PDF use the same source identity but different raw
        # versions. They are evaluated separately; no synthetic registry mutation.
        selection = InventorySelection(
            entry_id=key,
            kind="srt" if kind == "srt" else "material",
            source_id=sid,
            course_id="cs50_python",
            expected_implementation_revision=REVISION,
            bundle=bundle,
        )
        entries.append(
            CorpusEntry(
                entry_id=key,
                origin="synthetic",
                course_id="cs50_python",
                source_id=sid,
                format=kind,
                root_key=key,
                permission="evaluation",
                permission_reference="DEV-03 synthetic fixture-only acceptance recipe",
                selection=selection,
            )
        )
        bundles[key] = bundle
        documents[key] = doc
        roots[key] = bundle.workspace
    return (
        CorpusManifest(schema_version=1, dataset_version=VERSION, entries=entries),
        bundles,
        documents,
        roots,
    )


def gold_references(corpus, documents, observations):
    refs = []
    expected = [
        ("html", "text", "Hello", "heading"),
        ("html", "code", 'def hello():\n    print("hi")\n', "code"),
        ("code", "code", "# Ä\r\n", "code"),
        ("pdf-contract", "table", "A B", "table"),
        ("pdf-contract", "formula", "x² + y² = z²", "math"),
        ("pdf-native", "text", "Synthetic page 1", 1),
        ("pdf-native", "text", "Synthetic page 2", 2),
        ("srt", "transcript", "Hallo Ä\nMehrzeilig", None),
    ]
    for n, (key, dimension, text, selector) in enumerate(expected):
        doc = documents[key]
        observed = observations[key]
        if key == "srt":
            pointer = "/segments/0"
        else:
            block = (
                next(
                    b
                    for b in doc.blocks
                    if (b.location.page == selector and b.text is not None)
                )
                if key == "pdf-native"
                else next(b for b in doc.blocks if b.type == selector)
            )
            pointer = f"/blocks/{block.order}"
        locator = (
            ContentLocator(
                raw_artifact_sha256=observed["hashes"]["raw"],
                origin_pointer=pointer,
                original_segment_id=0,
                time_status="known",
                start=0.1,
                end=3,
            )
            if key == "srt"
            else None
        )
        refs.append(
            GoldReference(
                gold_id=f"synthetic-{n}",
                entry_id=key,
                source_id=observed["source_id"],
                source_version_id=observed["source_version_id"],
                original_sha256=observed["hashes"]["raw"],
                dimension=dimension,
                source_reference="Hand-authored fixture constants/build_fixture.py; not inferred from predictions",
                created_date=DAY,
                target_pointer=pointer,
                expected_content=text,
                expected_locator=locator,
                reference_status="confirmed",
                method="synthetic_reference",
                reviewer="synthetic_test_marker",
                review_reference="DEV-03 authored fixture specification; no human real review",
                review_date=DAY,
            )
        )
    return GoldDataset(schema_version=1, dataset_version=VERSION, references=refs)


def public_visual(report, workspace):
    """Existing C13 DTO with explicit path aliases, and a recomputed DTO digest."""
    value = report.model_dump(mode="json")
    value["inputs"] = {
        k: "synthetic/" + Path(v).relative_to(workspace).as_posix()
        for k, v in value["inputs"].items()
    }
    value.pop("report_sha256")
    value["report_sha256"] = sha256(json_bytes(value))
    return VisualInventory.model_validate(value)


def run(workspace, output):
    workspace, output = Path(workspace).absolute(), Path(output).absolute()
    for p in (workspace, output):
        safe_path(p.parent, p)
        if p.exists() or p.is_relative_to(ROOT) or ROOT.is_relative_to(p):
            raise ValueError("New external paths required")
    if workspace.is_relative_to(output) or output.is_relative_to(workspace):
        raise ValueError("Separate inputs and reports required")
    workspace.mkdir(mode=0o700, parents=True)
    corpus, bundles, documents, roots = corpus_inputs(workspace)
    empty = GoldDataset(schema_version=1, dataset_version=VERSION, references=())
    observation = evaluate(corpus, empty, roots=roots, actor=OWNER)
    observations = {r["entry_id"]: r for r in observation.report["inventory"]}
    if not all(r["binding_verified"] for r in observations.values()):
        raise ValueError("Synthetic bundle failed existing C23 gate")
    gold = gold_references(corpus, documents, observations)
    before = {p: sha256(p.read_bytes()) for p in workspace.rglob("*") if p.is_file()}
    report = evaluate(corpus, gold, roots=roots, actor=OWNER)
    if report != evaluate(corpus, gold, roots=roots, actor=OWNER):
        raise ValueError("Corpus report not deterministic")
    output.mkdir(mode=0o700, parents=True)
    publish(report, output / "materials", input_roots=roots.values())
    for key in ("html", "pdf-native"):
        b = bundles[key]
        visual = inventory(
            b.normalized_path,
            input_root=b.workspace,
            raw_path=b.raw_path,
            receipt_path=b.receipt_path,
        )
        public = public_visual(visual, workspace)
        if public != public_visual(
            inventory(
                b.normalized_path,
                input_root=b.workspace,
                raw_path=b.raw_path,
                receipt_path=b.receipt_path,
            ),
            workspace,
        ):
            raise ValueError("Visual report not deterministic")
        (output / (key + "-visual.json")).write_bytes(
            json_bytes(public.model_dump(mode="json"))
        )
        (output / (key + "-visual.md")).write_text(markdown(public))
    for backend in ("none", "sympy"):
        math = evaluate_dataset(
            ROOT / "docs/math_evaluation/formula_cases.v1.json",
            equivalence_backend=backend,
        )
        if any(r.case.gold_origin != "synthetic" for r in math.results):
            raise ValueError("Only authored synthetic formula cases permitted")
        math = math.model_copy(
            update={"input_path": "docs/math_evaluation/formula_cases.v1.json"}
        )
        publish_report(math, output / ("math-" + backend))
    if before != {
        p: sha256(p.read_bytes()) for p in workspace.rglob("*") if p.is_file()
    }:
        raise ValueError("Synthetic input bytes changed")
    # Freeze actual existing corpus/gold privately for exact same-input replay.
    dump(workspace / "corpus.v1.json", corpus.model_dump(mode="json"))
    dump(workspace / "gold.v1.json", gold.model_dump(mode="json"))
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
        print("Synthetic recipe rejected or failed; no real inputs permitted")
        return 2
    print(
        "Synthetic only; results="
        + str(len(report.report["results"]))
        + "; real_acceptance=blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
