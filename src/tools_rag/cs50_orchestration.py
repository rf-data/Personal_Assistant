"""Source orchestration reuses CS50Executor; no index/LLM operation here."""

from pathlib import Path

from src.tools_rag.cs50_ingestion import selected_bindings


def prepare_sources(
    adapter,
    *,
    workspace,
    course=None,
    section=None,
    all_six=False,
    execute_download=False,
    license_reviewed=False,
    transport=None,
):
    from src.tools_knowledge.bind_cs50_transcript import bind_cs50_knowledge_input
    from src.tools_lecture.execute_cs50 import CS50Executor

    bindings = selected_bindings(
        adapter, course=course, section=section, all_six=all_six
    )
    if not execute_download:
        return {
            "dry_run": True,
            "lectures": len(bindings),
            "tasks": 2 * len(bindings),
            "sources": [b.model_dump(mode="json") for b in bindings],
        }, ()
    if not license_reviewed:
        raise ValueError(
            "Review the concrete course/source license before enabling downloads"
        )
    worker = CS50Executor(adapter, workspace=Path(workspace), transport=transport)
    inputs = []
    for binding in bindings:
        worker.run(binding)  # Actual verified resume; no media/TXT fallback.
        inputs.append(bind_cs50_knowledge_input(adapter, binding, workspace=workspace))
    return {
        "dry_run": False,
        "lectures": len(inputs),
        "tasks": 2 * len(bindings),
    }, tuple(inputs)


def existing_inputs(adapter, *, workspace, course=None, section=None, all_six=False):
    from src.tools_knowledge.bind_cs50_transcript import bind_cs50_knowledge_input

    return tuple(
        bind_cs50_knowledge_input(adapter, b, workspace=workspace)
        for b in selected_bindings(
            adapter, course=course, section=section, all_six=all_six
        )
    )


def index_status(client, plan, artifact, adapter, *, workspace, state_root):
    from src.tools_rag.cs50_ingestion import (
        UploadState,
        checked_existing,
        revalidate_plan,
        validate_vectors,
    )

    revalidate_plan(plan, adapter, workspace=workspace)
    validate_vectors(artifact, plan)
    present = checked_existing(client, plan, artifact)
    path = Path(state_root) / plan.collection.name / (plan.plan_id + ".json")
    state = (
        UploadState.model_validate_json(path.read_bytes()) if path.exists() else None
    )
    if state and (
        state.plan_id != plan.plan_id or state.artifact_id != artifact.artifact_id
    ):
        raise ValueError("Status receipt identity conflict")
    return {
        "plan_id": plan.plan_id,
        "expected_points": len(plan.units),
        "verified_points": len(present),
        "missing_point_ids": [
            p.point_id for p in plan.units if p.point_id not in present
        ],
        "receipt_status": state.status if state else "missing",
        "complete": len(present) == len(plan.units)
        and state is not None
        and state.status == "done",
    }
