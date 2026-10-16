"""Fixed offline adapter entry point. Never takes commands or source host paths."""

import argparse
import json
import resource
import socket
import subprocess

from src.job_control.catalog import safe_path, snapshot
from src.job_control.registry import process_for
from src.job_control.store import Store


def apply_limits(process):
    for kind, value in (
        (resource.RLIMIT_CPU, process.cpu_seconds),
        (resource.RLIMIT_AS, process.memory_bytes),
        (resource.RLIMIT_FSIZE, process.file_bytes),
        (resource.RLIMIT_NOFILE, process.file_descriptors),
        (resource.RLIMIT_NPROC, process.subprocesses),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(kind, (value, value))


def execute(store, job_id):
    from src.tools_materials.parse_pdf import job_worker_scope

    with job_worker_scope():
        return execute_scoped(store, job_id)


def execute_scoped(store, job_id):
    job = store.get(job_id)
    process = process_for(job.process_id)
    apply_limits(process)

    def forbidden(*args, **kwargs):
        raise RuntimeError("Offline adapter forbids network access")

    socket.create_connection = forbidden
    socket.socket.connect = forbidden
    socket.getaddrinfo = forbidden
    directory = store.directory(job_id)
    inputs = directory / "inputs"
    entry = store.entry(job_id)
    snapshot(entry, inputs)
    results = safe_path(directory, "results")
    results.mkdir(mode=0o700)
    output = results / (job.parameters["output_name"] + ".json")
    if job.process_id == "material_parsing":
        from src.job_control.pdf_adapter import run

        run(entry.model_copy(update={"root": inputs}), job, results, output)
        return 0
    if job.process_id == "cs50_offline_workflow":
        from src.job_control.models import Principal
        from src.tools_materials.storage import save_model
        from src.workflows.definition import prepare
        from src.workflows.engine import run

        if job.parameters["previous_run_id"]:
            prior = store.get(job.parameters["previous_run_id"])
            from src.job_control.models import TERMINAL

            if (
                prior.status not in TERMINAL
                or prior.process_id != job.process_id
                or prior.initiated_by != job.initiated_by
                or prior.parameters["workflow_id"] != job.parameters["workflow_id"]
                or prior.parameters["course_id"] != job.parameters["course_id"]
            ):
                raise ValueError("Resume parent identity/status mismatch")
        pinned = entry.model_copy(update={"root": inputs})
        prepared = prepare(pinned)
        report = run(
            store,
            job,
            prepared,
            Principal(
                subject=job.initiated_by,
                role="operator",
                courses=(job.parameters["course_id"],),
            ),
        )
        save_model(output, report)
        if any(s.error == "Stage failed (TimeoutExpired)" for s in report.stages):
            return 4
        return 0 if report.status == "completed" else 1
    if job.process_id == "material_planning":
        from src.tools_materials.processing import MaterialPlan, make_plan
        from src.tools_materials.storage import save_model

        params = job.parameters
        plan = make_plan(inputs / entry.roles["manifest"])
        rows = plan.select(
            course=params["course_id"],
            section=params["section"],
            resource=params["resource_id"],
        )
        if len(rows) > 100:
            raise ValueError("Material limit")
        save_model(
            output,
            MaterialPlan(
                courses=tuple(
                    c for c in plan.courses if c.course_id == params["course_id"]
                ),
                materials=rows,
            ),
        )
        return 0
    from scripts.cs50_material_quality import main

    arguments = ["--workspace", str(inputs), "--output", str(output)]
    for role in ("plan", "normalized", "receipt", "raw"):
        arguments.extend(["--" + role, str(inputs / entry.roles[role])])
    # Existing C10 CLI publishes its existing structured report, outside inputs.
    return main(arguments)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--parent", type=int, required=True)
    args = parser.parse_args(argv)
    from src.job_control.guardian import arm_parent_death

    arm_parent_death(args.parent)
    try:
        return execute(Store(args.root), args.job_id)
    except subprocess.TimeoutExpired:
        return 4
    except (ValueError, OSError, KeyError, json.JSONDecodeError):
        return 2
    except Exception:
        # No exception payload/traceback may expose source bytes or credentials.
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
