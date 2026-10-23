"""Read-only preparation with existing discovery, selection and parser contracts."""

import hashlib
from dataclasses import dataclass

from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.models import fingerprint
from src.job_control.pdf_adapter import PDF_CONFIG
from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import MaterialPlan, ParserConfig
from src.tools_materials.processing import make_plan, parser_for, plan_steps
from src.workflows.graph import topological
from src.workflows.models import Definition, Stage

ACTIVE = {
    "material_planning": ("src.tools_materials.processing.make_plan", (), ("plan",)),
    "local_material_import": (
        "src.tools_materials.download.MaterialDownloader.obtain(local_file)",
        ("plan", "local_raw"),
        ("raw", "receipt"),
    ),
    "material_parsing": (
        "src.tools_materials.processing.MaterialProcessor.parse",
        ("raw", "receipt"),
        ("raw", "receipt", "normalized"),
    ),
    "quality_evaluation": (
        "src.tools_lecture.material_handoff.prepare_material_handoff",
        ("plan", "normalized", "receipt", "raw"),
        ("quality",),
    ),
    "lecture_material_handoff": (
        "src.tools_lecture.material_handoff.prepare_material_handoff",
        ("quality", "plan", "normalized", "receipt", "raw"),
        ("handoff",),
    ),
}
DEFERRED = {
    "audio_transcription": dict(
        inputs=["audio", "language"],
        outputs=["TranscriptDocument"],
        runner="src.tools_transcribe",
        reason="No approved offline workflow execution",
    ),
    "visual_enrichment": dict(
        inputs=["visual_inventory", "source_evidence"],
        outputs=["visual_enrichment"],
        runner="src.tools_knowledge.postprocess_visual.postprocess_visual_enrichment",
        reason="Provider and evidence approval required",
    ),
    "knowledge_extraction": dict(
        inputs=["transcript", "provenance"],
        outputs=["LectureKnowledgeDocument"],
        runner="src.tools_knowledge.run_cs50_lecture",
        reason="Explicit later LLM approval required",
    ),
    "knowledge_consolidation": dict(
        inputs=["knowledge", "evidence"],
        outputs=["ConsolidatedKnowledgeDocument"],
        runner="src.tools_knowledge.consolidation_run",
        reason="Separate bounded offline contract exists; not activated here",
    ),
    "formula_evaluation": dict(
        inputs=["independent_gold", "predictions"],
        outputs=["MathEvaluationReport"],
        runner="scripts.evaluate_math_formulas",
        reason="No material-to-gold binding; not automatically activated",
    ),
}


@dataclass(frozen=True)
class Prepared:
    definition: Definition
    plan: MaterialPlan
    stages: tuple[Stage, ...]
    bindings: dict
    parsers: dict
    files: dict
    planning_hashes: dict
    input_errors: dict


def catalog_plan(entry, definition=None):
    """Reconstruct the same versioned discovery at admission and in the worker."""
    if definition is None:
        files = verified_files(entry)
        definition = Definition.model_validate_json(files[entry.roles["workflow"]])
    if definition.course_id not in entry.course_ids:
        raise ValueError("Workflow course contradicts approved catalog")
    refs = []
    for snapshot in definition.assignment_snapshots:
        name = snapshot.path.as_posix()
        if entry.files.get(name) != snapshot.sha256:
            raise ValueError(
                "Overview is absent from the approved catalog hash closure"
            )
        refs.append(snapshot.model_copy(update=dict(path=safe_path(entry.root, name))))
    plan = make_plan(
        entry.root / entry.roles["manifest"], assignment_snapshots=tuple(refs)
    )
    if any(
        not any(
            b.role == "problem_set"
            and b.original_url == str(s.url)
            and b.resource.course_id == definition.course_id
            and (
                definition.section is None
                or definition.section in b.resource.section_keys
            )
            for b in plan.materials
        )
        for s in refs
    ):
        raise ValueError("Overview contradicts workflow course/section")
    return plan


def prepare(entry, *, plan=None, strict=True):
    errors = {}
    if strict:
        files = verified_files(entry)
    else:
        files = {}
        for name, expected in entry.files.items():
            try:
                files[name] = read_file(safe_path(entry.root, name))
                if hashlib.sha256(files[name]).hexdigest() != expected:
                    errors[name] = "input_hash_mismatch"
            except (OSError, ValueError):
                errors[name] = "missing_or_unsafe_input"
    definition = Definition.model_validate_json(files[entry.roles["workflow"]])
    if definition.course_id not in entry.course_ids:
        raise ValueError("Workflow course contradicts approved catalog")
    if definition.assignment_snapshots:
        reconstructed = catalog_plan(entry, definition)
        if plan is not None and plan != reconstructed:
            raise ValueError(
                "Cached discovery contradicts pinned overview reconstruction"
            )
        plan = reconstructed
    else:
        plan = plan or make_plan(entry.root / entry.roles["manifest"])
    bindings = {}
    for resource, path in sorted(definition.sources.items()):
        (binding,) = plan.select(
            course=definition.course_id, section=definition.section, resource=resource
        )
        if definition.assignment_snapshots:
            from src.model_materials.week import WeekLimits
            from src.tools_materials.week import routing

            if routing(binding, WeekLimits())[1:3] != (
                "approval_required",
                "c18_material",
            ):
                raise PermissionError(
                    "Overview proof cannot authorize manual code/media"
                )
        if definition.lecture_ids and not set(binding.lecture_ids) & set(
            definition.lecture_ids
        ):
            raise ValueError("Selected lecture does not contain material")
        if binding.material_id in bindings:
            raise ValueError("Duplicate logical material")
        if path not in entry.files:
            raise ValueError("Local import is not declared in approved catalog")
        bindings[binding.material_id] = binding.model_copy(
            update={"source_origin": definition.source_origin}
        )
    selected = MaterialPlan(
        courses=tuple(c for c in plan.courses if c.course_id == definition.course_id),
        materials=tuple(bindings.values()),
    )
    known_lectures = {
        r.resource_id
        for c in selected.courses
        for r in c.resources
        if r.role == "lecture_video"
    }
    if set(definition.lecture_ids) - known_lectures:
        raise ValueError("Unknown selected lecture")
    stages, parsers = [], {}
    plan_id = deterministic_id("material_task", "workflow_material_plan")
    scope = dict(
        course_id=definition.course_id,
        section=definition.section,
        resources=sorted(definition.sources),
        source_origin=definition.source_origin,
    )
    if definition.assignment_snapshots:
        scope["assignment_snapshots"] = [
            s.model_dump(mode="json") for s in definition.assignment_snapshots
        ]
    stages.append(
        Stage(
            stage_id=plan_id,
            process_id="material_planning",
            expected_inputs=("manifest",),
            expected_outputs=("plan",),
            configuration_hash=fingerprint(scope),
        )
    )
    for mid, binding in bindings.items():
        config, _, _ = parser_for(binding)
        if config is not None and config.name == "pdf" and config.version == "2":
            # C19: the fixed C16 adapter scope keeps the worker in its owned group.
            config = PDF_CONFIG.model_copy(
                update=dict(
                    max_bytes=definition.max_bytes,
                    max_blocks=definition.max_blocks,
                )
            )
        elif config is not None and config.name in {"html", "code"}:
            config = ParserConfig(
                name=config.name,
                version=config.version,
                max_bytes=definition.max_bytes,
                max_blocks=definition.max_blocks,
                memory_mb=512,
                timeout=10,
            )
        else:
            config = None
        parsers[mid] = config
        previous = plan_id
        for process in (
            "local_material_import",
            "material_parsing",
            "quality_evaluation",
            "lecture_material_handoff",
        ):
            stage_id = (
                plan_steps(binding)["tasks"][-1]["task_id"]
                if process == "material_parsing" and config
                else deterministic_id("material_task", mid, process)
            )
            stage_config = (
                config.model_dump()
                if process == "material_parsing" and config
                else dict(max_bytes=definition.max_bytes)
                if process == "local_material_import"
                else dict(contract=process, version=1)
            )
            _, inputs, outputs = ACTIVE[process]
            stages.append(
                Stage(
                    stage_id=stage_id,
                    process_id=process,
                    material_id=mid,
                    dependencies=(previous,),
                    expected_inputs=inputs,
                    expected_outputs=outputs,
                    configuration_hash=fingerprint(stage_config),
                )
            )
            previous = stage_id
    import_paths = set(definition.sources.values()) | {entry.roles["workflow"]}
    hashes = {
        p: hashlib.sha256(raw).hexdigest()
        for p, raw in files.items()
        if p not in import_paths
    }
    return Prepared(
        definition,
        selected,
        topological(stages),
        bindings,
        parsers,
        files,
        hashes,
        errors,
    )
