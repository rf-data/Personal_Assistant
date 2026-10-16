"""Deterministic decisions and sequential execution inside one bounded C16 job."""

import time

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import TERMINAL, fingerprint
from src.job_control.store import now
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import MaterialProcessor
from src.tools_materials.storage import publish_bytes, save_model
from src.workflows.definition import ACTIVE
from src.workflows.models import VALID, State, Workflow
from src.workflows.state import archive, load, locked, save
from src.workflows.validation import hashes, material_paths, output, valid_outputs


class StageFailure(ValueError):
    def __init__(self, code, refs=()):
        self.code, self.refs = code, refs
        super().__init__(code)


def sealed(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", exclude={"report_sha256"})
    return Workflow(**value, report_sha256=fingerprint(value))


def aggregate(stages):
    unique = {}
    for stage in stages:
        if stage.status in VALID:
            for item in stage.output_refs:
                unique.setdefault((item.kind, item.identity, item.sha256), item)
    return tuple(unique[k] for k in sorted(unique))


def preview(prepared, root, workflow_id, source_ref, actor, previous=None):
    old = {s.stage_id: s for s in previous.report.stages} if previous else {}
    results = {}
    for stage in prepared.stages:
        if stage.process_id not in ACTIVE:
            raise ValueError("Unapproved stage process")
        reasons = []
        missing = []
        if stage.process_id == "material_planning":
            missing = [
                name
                for name in prepared.input_errors
                if name in prepared.planning_hashes
            ]
        elif stage.process_id == "local_material_import":
            binding = prepared.bindings[stage.material_id]
            path = prepared.definition.sources.get(
                binding.source_id
            ) or prepared.definition.sources.get(binding.material_id)
            if path not in prepared.files or path in prepared.input_errors:
                missing = [path]
            elif len(prepared.files[path]) > prepared.definition.max_bytes:
                missing = ["source_exceeds_byte_limit:" + path]
        if (
            stage.process_id == "material_parsing"
            and prepared.parsers[stage.material_id] is None
        ):
            missing.append("unsupported_parser_lifecycle")
        deps_valid = all(results[d].status in VALID for d in stage.dependencies)
        inputs = hashes(prepared, stage, results)
        prior = old.get(stage.stage_id)
        if prior:
            if prior.configuration_hash != stage.configuration_hash:
                reasons.append("configuration_changed")
            if prior.input_hashes != inputs:
                reasons.append("inputs_or_dependencies_changed")
            if any(
                results[d].status == "stale" or results[d].stale_reasons
                for d in stage.dependencies
            ):
                reasons.append("upstream_stale")
            if prior.status in VALID and not reasons and deps_valid and not missing:
                try:
                    valid_outputs(root, prior, prepared, results)
                except (ValueError, OSError, KeyError, StopIteration):
                    reasons.append("output_missing_corrupt_or_incompatible")
                else:
                    results[stage.stage_id] = prior.model_copy(
                        update=dict(
                            status="skipped",
                            decision="verified_reuse",
                            stale_reasons=(),
                        )
                    )
                    continue
        status = (
            "blocked"
            if missing
            else "stale"
            if prior and prior.status in VALID and reasons
            else "blocked"
            if not deps_valid
            else "ready"
        )
        results[stage.stage_id] = stage.model_copy(
            update=dict(
                status=status,
                decision="missing_input:" + ",".join(map(str, missing))
                if missing
                else "blocked_dependency"
                if not deps_valid
                else "new_stage_workspace",
                input_hashes=inputs,
                missing_inputs=tuple(map(str, missing)),
                output_refs=prior.output_refs if prior else (),
                stale_reasons=tuple(reasons),
                error=None,
            )
        )
    stages = tuple(results.values())
    status = (
        "completed"
        if all(s.status in VALID for s in stages)
        else "stale"
        if any(s.status == "stale" for s in stages)
        else "ready"
        if any(s.status == "ready" for s in stages)
        else "blocked"
    )
    definition = prepared.definition
    lectures = tuple(
        sorted(
            {lecture for b in prepared.bindings.values() for lecture in b.lecture_ids}
        )
    )
    value = dict(
        schema_version=1,
        workflow_id=workflow_id,
        workflow_type=definition.workflow_type,
        course_id=definition.course_id,
        lecture_ids=lectures,
        created_at=previous.report.created_at if previous else None,
        status=status,
        stages=stages,
        dependencies={s.stage_id: s.dependencies for s in stages},
        input_refs=(source_ref,),
        output_refs=aggregate(stages),
        configuration_hash=fingerprint(definition.model_dump(mode="json")),
        run_id=previous.report.run_id if previous else None,
        initiated_by=actor.subject,
        started_at=previous.report.started_at if previous else None,
        finished_at=previous.report.finished_at if previous else None,
        expected_changes=tuple(
            s.stage_id + ":new_workspace" for s in stages if s.status not in VALID
        ),
    )
    return sealed(Workflow.model_validate({**value, "report_sha256": "0" * 64}))


def execute_stage(prepared, stage, results, directory, root):
    directory.parent.mkdir(mode=0o700, exist_ok=True)
    directory.mkdir(mode=0o700)
    process = stage.process_id
    binding = prepared.bindings.get(stage.material_id)
    if process == "material_planning":
        path = directory / "plan.v1.json"
        save_model(path, prepared.plan)
        return (output(root, path, "plan", prepared.definition.course_id),)
    if process == "local_material_import":
        name = prepared.definition.sources.get(
            binding.source_id
        ) or prepared.definition.sources.get(binding.material_id)
        source = directory / "import.source"
        publish_bytes(source, prepared.files[name])
        downloader = MaterialDownloader(
            directory / "materials", max_bytes=prepared.definition.max_bytes
        )
        downloader.obtain(binding, execute=True, local_file=source)
        raw, receipt = downloader.paths(binding)
        return (
            output(root, raw, "raw", binding.material_id),
            output(root, receipt, "receipt", binding.material_id),
        )
    if process == "material_parsing":
        imported = results[stage.dependencies[0]]
        workspace = directory / "materials"
        material = binding.material_id.split(":")[1]
        for item in imported.output_refs:
            name = f"{material}/" + (
                "raw/source" if item.kind == "raw" else "receipt.v1.json"
            )
            publish_bytes(
                safe_path(workspace, name), read_file(safe_path(root, item.path))
            )
        processor = MaterialProcessor(workspace)
        receipt = processor.parse(
            binding, execute=True, config=prepared.parsers[stage.material_id]
        )
        raw, receipt_path = processor.downloader.paths(binding)
        normalized = safe_path(workspace, receipt.normalized_path)
        refs = [
            output(root, raw, "raw", binding.material_id),
            output(root, receipt_path, "receipt", binding.material_id),
            output(root, normalized, "normalized", normalized_document_id(normalized)),
        ]
        for name in sorted(receipt.image_hashes):
            refs.append(output(root, safe_path(normalized.parent, name), "image", name))
        return tuple(refs)
    paths, _receipt = material_paths(root, stage, results)
    review = prepare_material_handoff(**paths)
    if process == "quality_evaluation":
        path = directory / "quality.v1.json"
        save_model(path, review)
        if not review.report.passed:
            raise StageFailure(
                "quality_gate_failed",
                (output(root, path, "quality", binding.material_id),),
            )
        return (output(root, path, "quality", binding.material_id),)
    if process != "lecture_material_handoff" or review.handoff is None:
        raise ValueError("Handoff requires a passing current quality gate")
    path = directory / "handoff.v1.json"
    save_model(path, review.handoff)
    return (output(root, path, "handoff", review.handoff.document.document_id),)


def normalized_document_id(path):
    from src.model_materials.materials import NormalizedDocument

    return NormalizedDocument.model_validate_json(read_file(path)).document_id


def run(store, job, prepared, actor):
    workflow_id = job.parameters["workflow_id"]
    with locked(store.root, workflow_id):
        previous = load(store.root, workflow_id, actor)
        if previous:
            if previous.report.input_refs != job.input_refs:
                raise ValueError("Workflow source reference changed")
            ancestor = job.parameters["previous_run_id"]
            for _ in range(100):
                if ancestor == previous.report.run_id:
                    break
                if ancestor is None:
                    raise ValueError(
                        "Workflow changed since the explicit resume request"
                    )
                parent = store.get(ancestor)
                if (
                    parent.status not in TERMINAL
                    or parent.process_id != job.process_id
                    or parent.initiated_by != job.initiated_by
                    or parent.parameters["workflow_id"] != workflow_id
                    or parent.parameters["course_id"] != job.parameters["course_id"]
                ):
                    raise ValueError("Resume lineage identity mismatch")
                ancestor = parent.parameters["previous_run_id"]
            else:
                raise ValueError("Resume lineage limit reached")
        attempts = previous.attempts if previous else ()
        if len(attempts) >= 10:
            raise ValueError("Workflow attempt limit reached")
        archive(store.root, previous)
        report = preview(
            prepared, store.root, workflow_id, job.input_refs[0], actor, previous
        )
        report = sealed(
            report.model_copy(
                update=dict(
                    run_id=job.job_id,
                    created_at=report.created_at or now(),
                    started_at=now(),
                    status="running",
                )
            )
        )
        attempts = (*attempts, job.job_id)
        results = {}
        failed = False
        for stage in report.stages:
            if stage.status in VALID:
                results[stage.stage_id] = stage
                continue
            if (
                (failed and not prepared.definition.continue_independent)
                or any(results[d].status not in VALID for d in stage.dependencies)
                or stage.decision.startswith("missing_input:")
            ):
                results[stage.stage_id] = stage.model_copy(
                    update=dict(
                        status="blocked",
                        output_refs=(),
                        decision="blocked_dependency_or_policy",
                    )
                )
            else:
                inputs = hashes(prepared, stage, results)
                stage = stage.model_copy(
                    update=dict(
                        status="running",
                        input_hashes=inputs,
                        output_refs=(),
                        started_at=now(),
                        finished_at=None,
                        duration_seconds=None,
                        job_id=job.job_id,
                        decision="execute_new_workspace",
                    )
                )
                results[stage.stage_id] = stage
                interim = tuple(results.get(s.stage_id, s) for s in report.stages)
                save(
                    store.root,
                    State(
                        report=sealed(
                            report.model_copy(
                                update=dict(
                                    stages=interim, output_refs=aggregate(interim)
                                )
                            )
                        ),
                        attempts=attempts,
                    ),
                )
                started = time.monotonic()
                directory = safe_path(
                    store.directory(job.job_id),
                    "results/stages/" + fingerprint(stage.stage_id)[:32],
                )
                try:
                    refs = execute_stage(
                        prepared, stage, results, directory, store.root
                    )
                    finished = stage.model_copy(
                        update=dict(
                            output_refs=refs,
                            status="completed",
                            finished_at=now(),
                            duration_seconds=time.monotonic() - started,
                            error=None,
                            stale_reasons=(),
                        )
                    )
                    valid_outputs(store.root, finished, prepared, results)
                    results[stage.stage_id] = finished
                except Exception as error:
                    failed = True
                    results[stage.stage_id] = stage.model_copy(
                        update=dict(
                            status="failed",
                            output_refs=error.refs
                            if isinstance(error, StageFailure)
                            else (),
                            error="Stage failed (" + type(error).__name__[:60] + ")",
                            finished_at=now(),
                            duration_seconds=time.monotonic() - started,
                        )
                    )
            interim = tuple(results.get(s.stage_id, s) for s in report.stages)
            save(
                store.root,
                State(
                    report=sealed(
                        report.model_copy(
                            update=dict(stages=interim, output_refs=aggregate(interim))
                        )
                    ),
                    attempts=attempts,
                ),
            )
        stages = tuple(results.values())
        report = sealed(
            report.model_copy(
                update=dict(
                    stages=stages,
                    output_refs=aggregate(stages),
                    status="completed"
                    if all(s.status in VALID for s in stages)
                    else "failed"
                    if failed
                    else "blocked",
                    finished_at=now(),
                    expected_changes=(),
                )
            )
        )
        save(store.root, State(report=report, attempts=attempts))
        return report
