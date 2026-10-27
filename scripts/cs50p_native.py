"""Manual SSH-only native admission into the existing C16 worker; no server loop."""

import argparse
import fcntl
import hashlib
import json
import os
import signal
import sqlite3
import time
from pathlib import Path

from scripts.cs50_worker import CapacityExecutor
from src.job_control import native_admission as gate
from src.job_control.catalog import read_file, safe_path
from src.job_control.controller import Controller
from src.job_control.models import TERMINAL, Job, load_settings
from src.job_control.operations import database, fence, private
from src.tools_materials.capacity import load_limits


def status(settings, job_id):
    # SQL read-only, no Controller/Store startup, WAL initialization or heartbeat.
    gate.actor(settings)
    with database(settings.root) as db:
        job = Job.model_validate_json(
            db.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()[0]
        )
    if job.initiated_by != gate.actor(settings).subject:
        raise PermissionError("Native job owner required")
    return job


def result(settings, job_id):
    job = status(settings, job_id)
    if job.status != "completed" or len(job.artifact_refs) != 1:
        raise ValueError("Completed C16 result required")
    if safe_path(settings.root, "quarantine").exists():
        raise PermissionError("Quarantined result requires operator investigation")
    artifact = job.artifact_refs[0]
    data = read_file(
        safe_path(
            settings.root,
            "jobs/"
            + job.job_id
            + "/results/"
            + job.parameters["output_name"]
            + ".json",
        )
    )
    if (
        len(data) != artifact.size_bytes
        or hashlib.sha256(data).hexdigest() != artifact.sha256
    ):
        raise ValueError("Result integrity failure")
    report = json.loads(data)
    for item in report["output_refs"]:
        payload = read_file(safe_path(settings.root, item["path"]))
        if (
            len(payload) != item["size_bytes"]
            or hashlib.sha256(payload).hexdigest() != item["sha256"]
        ):
            raise ValueError("Workflow output integrity failure")
    return dict(artifact=artifact.model_dump(mode="json"), report=report)


def cancel(settings, job_id):
    job = status(settings, job_id)
    if job.status in TERMINAL:
        return job
    controller = Controller(settings)
    if job.status == "created":
        controller.store.transition(
            job_id,
            "cancel_requested",
            "cancel_requested",
            "Operator cancelled undispatched native approval",
        )
        return controller.store.transition(
            job_id,
            "cancelled",
            "cancelled",
            "Operator cancelled undispatched native approval",
        )
    return controller.cancel(gate.actor(settings), job_id)


def recover(settings, job_id):
    """Explicit stopped-worker reconciliation; no saved PID is ever signalled."""
    gate.enrolled(settings)
    with fence(settings.root), gate.lock(settings.root):
        fd = os.open(
            safe_path(settings.root, "worker.lock"),
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
            0o600,
        )
        execution = None
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            job = status(settings, job_id)
            if job.status in TERMINAL:
                return job
            directory = safe_path(settings.root, "jobs/" + job.job_id)
            if directory.exists():
                # Unknown directory without the guardian's lifecycle proof is HOLD.
                execution = os.open(
                    safe_path(directory, "execution.lock"), os.O_RDWR | os.O_NOFOLLOW
                )
                deadline = time.monotonic() + 8
                while True:
                    try:
                        fcntl.flock(execution, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError(
                                "Previous guardian cleanup unconfirmed"
                            ) from None
                        time.sleep(0.03)
            store = Controller(settings).store
            if job.status in {"created", "queued"}:
                store.transition(
                    job_id,
                    "cancel_requested",
                    "cancel_requested",
                    "Operator recovery confirmed no active worker/payload",
                )
                return store.transition(
                    job_id,
                    "cancelled",
                    "cancelled",
                    "Undispatched native job cancelled; grant remains consumed",
                )
            return store.transition(
                job_id,
                "interrupted",
                "interrupted",
                "Stopped-worker lifecycle lock verified; fresh review and grant required",
            )
        finally:
            if execution is not None:
                os.close(execution)
            os.close(fd)


def run(settings, limits_path, job_id, *, offline_test=False):
    expected_mode = "offline-test" if offline_test else "ssh-runtime"
    if settings.native_mode != expected_mode:
        raise PermissionError(
            "Runtime start rejects offline grants; offline-test requires explicit test invocation"
        )
    record = gate.enrolled(settings)
    if (
        private(limits_path) != record.limits
        or gate.digest(limits_path) != record.limits_sha256
    ):
        raise PermissionError("Enrolled limits required")
    with fence(settings.root):
        with gate.lock(settings.root):
            grant = gate.load_grant(settings, job_id)
            job = status(settings, job_id)
            if job.status != "created":
                raise PermissionError("Only a newly manually approved job can start")
            gate.write_new(
                settings.root / "native-grants" / (job_id + ".used.json"),
                dict(
                    grant_sha256=gate.fingerprint(grant.model_dump(mode="json")),
                    worker_pid=os.getpid(),
                ),
            )
        # Persisted consumption precedes all executor activity. A crash consumes the
        # grant too; never rerun it. Operator cancels the orphan and approves resume.
        worker_token = gate.WORKER.set(grant)
        auth_token = gate.AUTHORITY.set(
            dict(
                settings=settings,
                preview=grant.preview,
                key="native_" + grant.nonce[:48],
            )
        )
        executor = None
        stopping = {"value": False}

        def stop(*_):
            stopping["value"] = True

        previous = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
        try:
            executor = CapacityExecutor(settings, load_limits(limits_path))
            Controller(settings).start(gate.actor(settings), job_id)
            deadline = time.monotonic() + 120
            while not stopping["value"]:
                executor.step()
                job = executor.store.get(job_id)
                if job.status in TERMINAL:
                    return job
                if time.monotonic() >= deadline:
                    raise TimeoutError("Native worker total runtime exceeded")
                time.sleep(0.05)
            return executor.store.get(job_id)
        finally:
            try:
                if executor is not None:
                    executor.close()
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
                gate.AUTHORITY.reset(auth_token)
                gate.WORKER.reset(worker_token)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in (
        "init",
        "preflight",
        "review",
        "approve",
        "run",
        "status",
        "result",
        "cancel",
        "recover",
    ):
        p = sub.add_parser(command)
        p.add_argument("--config", required=True, type=Path)
        p.add_argument("--limits", required=True, type=Path)
        if command == "run":
            p.add_argument(
                "--offline-test",
                action="store_true",
                help="Explicit synthetic test invocation; never use for host runtime",
            )
        if command in {"review", "approve"}:
            p.add_argument("--source-ref", required=True)
            p.add_argument("--workflow-id", required=True)
            p.add_argument("--resume", action="store_true")
        if command in {"approve"}:
            p.add_argument("--review-id", required=True)
            p.add_argument("--ttl", type=int, default=300)
        if command in {"run", "status", "result", "cancel", "recover"}:
            p.add_argument("--job-id", required=True)
        if command in {"init", "approve", "recover"}:
            p.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        settings = load_settings(private(args.config))
        gate.actor(settings)
        if args.command == "init":
            value = gate.initialize(args.config, args.limits)
        elif args.command in {"status", "result"}:
            value = globals()[args.command](settings, args.job_id)
        else:
            if (
                args.command == "preflight"
                and not (settings.root / gate.MARKER).exists()
            ):
                from src.job_control.operations import preflight

                limits = load_limits(args.limits)
                preflight(args.config, min_free_bytes=limits.reserve_bytes)
                gate.policy(settings, limits)
                print(
                    json.dumps(
                        dict(
                            status="not_enrolled",
                            protocol=gate.PROTOCOL,
                            uid=os.getuid(),
                        )
                    )
                )
                return 0
            enrolled = gate.enrolled(settings, verify_queue=args.command != "preflight")
            if (
                private(args.limits) != enrolled.limits
                or gate.digest(args.limits) != enrolled.limits_sha256
            ):
                raise PermissionError("Enrolled capacity policy required")
            if args.command == "preflight":
                value = dict(
                    status="checked",
                    protocol=gate.PROTOCOL,
                    mode=settings.native_mode,
                    uid=os.getuid(),
                )
            elif args.command in {"review", "approve"}:
                kwargs = dict(resume=args.resume)
                if args.command == "approve":
                    kwargs.update(review_id=args.review_id, ttl=args.ttl)
                if args.command == "approve":
                    with fence(settings.root):
                        value = gate.approve(
                            settings, args.source_ref, args.workflow_id, **kwargs
                        )
                else:
                    value = gate.review(
                        settings, args.source_ref, args.workflow_id, **kwargs
                    )
            elif args.command == "run":
                value = run(
                    settings, args.limits, args.job_id, offline_test=args.offline_test
                )
            else:
                value = globals()[args.command](settings, args.job_id)
        output = (
            value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        )
        print(json.dumps(output, ensure_ascii=False))
        if args.command == "run":
            return 0 if status(settings, args.job_id).status == "completed" else 1
        return 0
    except (
        ValueError,
        OSError,
        RuntimeError,
        KeyError,
        TypeError,
        sqlite3.Error,
    ) as error:
        print(
            json.dumps(
                dict(
                    status="blocked",
                    error_class=type(error).__name__,
                    reason=str(error),
                )
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
