"""Hash, provenance, schema and exact configuration checks before any skip."""

import hashlib
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.model_materials.materials import (
    ArtifactReceipt,
    MaterialPlan,
    NormalizedDocument,
)
from src.tools_lecture.material_handoff import (
    LectureMaterialHandoff,
    MaterialReview,
    prepare_material_handoff,
)
from src.workflows.models import Output


def checked_output(root, output):
    if not output.path.startswith("jobs/") or "/results/stages/" not in output.path:
        raise ValueError("Output outside controlled C16 stage workspace")
    data = read_file(safe_path(root, output.path))
    if (
        len(data) != output.size_bytes
        or hashlib.sha256(data).hexdigest() != output.sha256
    ):
        raise ValueError("Output hash/size mismatch")
    return data


def output(root, path, kind, identity):
    path = safe_path(root, path.relative_to(root))
    data = read_file(path)
    return Output(
        kind=kind,
        identity=identity,
        path=str(path.relative_to(root)),
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def hashes(prepared, stage, results):
    inputs = {}
    for dep in stage.dependencies:
        for item in results[dep].output_refs:
            inputs[f"{dep}:{item.kind}:{item.identity}"] = item.sha256
    if stage.process_id == "material_planning":
        inputs.update(prepared.planning_hashes)
    elif stage.process_id == "local_material_import":
        binding = prepared.bindings[stage.material_id]
        name = prepared.definition.sources.get(
            binding.source_id
        ) or prepared.definition.sources.get(binding.material_id)
        if name in prepared.files:
            inputs["local_source"] = hashlib.sha256(prepared.files[name]).hexdigest()
        inputs["binding"] = fingerprint(binding.model_dump(mode="json"))
    return inputs


def material_paths(root, stage, results):
    parsed = next(
        s
        for s in results.values()
        if s.material_id == stage.material_id and s.process_id == "material_parsing"
    )
    plan = next(s for s in results.values() if s.process_id == "material_planning")
    names = {
        o.kind: safe_path(root, o.path)
        for o in parsed.output_refs
        if o.kind in {"raw", "receipt", "normalized"}
    }
    receipt = ArtifactReceipt.model_validate_json(read_file(names["receipt"]))
    # Material receipt path is <workspace>/<material hash>/receipt.v1.json.
    return dict(
        normalized_path=names["normalized"],
        receipt_path=names["receipt"],
        raw_path=names["raw"],
        plan_path=safe_path(root, plan.output_refs[0].path),
        workspace=names["receipt"].parent.parent,
    ), receipt


def valid_outputs(root, stage, prepared, results):
    if not stage.output_refs:
        raise ValueError("Missing output manifest")
    data = {o.path: checked_output(root, o) for o in stage.output_refs}
    kinds = {o.kind for o in stage.output_refs}
    if not set(stage.expected_outputs) <= kinds:
        raise ValueError("Incomplete output roles")
    binding = prepared.bindings.get(stage.material_id)
    if stage.process_id == "material_planning":
        if MaterialPlan.model_validate_json(next(iter(data.values()))) != prepared.plan:
            raise ValueError("Plan graph/provenance mismatch")
    elif stage.process_id in {"local_material_import", "material_parsing"}:
        (receipt_ref,) = [o for o in stage.output_refs if o.kind == "receipt"]
        receipt = ArtifactReceipt.model_validate_json(data[receipt_ref.path])
        (raw_ref,) = [o for o in stage.output_refs if o.kind == "raw"]
        if (
            receipt.binding != binding
            or receipt.raw_sha256 != raw_ref.sha256
            or receipt.origin != "local_import"
        ):
            raise ValueError("Receipt/source provenance mismatch")
        if stage.process_id == "local_material_import":
            if receipt.status != "verified" or receipt.parser is not None:
                raise ValueError("Import receipt version/status mismatch")
        else:
            (normalized,) = [o for o in stage.output_refs if o.kind == "normalized"]
            doc = NormalizedDocument.model_validate_json(data[normalized.path])
            if (
                doc.binding != binding
                or doc.parser != prepared.parsers[stage.material_id]
                or receipt.parser != doc.parser
                or receipt.normalized_sha256 != normalized.sha256
                or receipt.raw_sha256 != doc.raw_sha256
                or receipt.status != "completed"
            ):
                raise ValueError("Parser/schema/provenance mismatch")
            if normalized.path != str(
                Path(receipt_ref.path).parent.parent / receipt.normalized_path
            ):
                raise ValueError("Normalized receipt path mismatch")
            for image in doc.images:
                if image.artifact_path:
                    path = str(Path(normalized.path).parent / image.artifact_path)
                    if (
                        path not in data
                        or hashlib.sha256(data[path]).hexdigest() != image.sha256
                    ):
                        raise ValueError("Missing image proof")
            from src.tools_materials.processing import MaterialProcessor

            MaterialProcessor(
                safe_path(root, str(Path(receipt_ref.path).parent.parent))
            ).inspect(binding, prepared.parsers[stage.material_id])
    else:
        paths, _receipt = material_paths(root, stage, results)
        reviewed = prepare_material_handoff(**paths)
        if not reviewed.report.passed:
            raise ValueError("Current quality gate failed")
        stored = next(iter(data.values()))
        if stage.process_id == "quality_evaluation":
            if MaterialReview.model_validate_json(stored) != reviewed:
                raise ValueError("Quality snapshot/provenance mismatch")
        elif stage.process_id == "lecture_material_handoff":
            if LectureMaterialHandoff.model_validate_json(stored) != reviewed.handoff:
                raise ValueError("Handoff/evidence mismatch")
        else:
            raise ValueError("Unapproved stage process")
