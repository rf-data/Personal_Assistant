"""Single bounded Linux supervisor, independent from the HTTP lifecycle."""

import fcntl
import os
import signal
import subprocess
import sys
import time

from src.job_control.catalog import safe_path
from src.job_control.guardian import arm_parent_death, clean_environment
from src.job_control.models import TERMINAL
from src.job_control.store import Store, Unavailable


class Executor:
    def __init__(self, settings):
        if sys.platform != "linux" or not settings.execution_enabled:
            raise Unavailable("Explicitly enabled Linux executor required")
        self.settings = settings
        if settings.deployment_gate_required:
            from src.job_control.deployment_gate import require_existing_queue

            require_existing_queue(settings)
        self.store = Store(
            settings.root, deployment_gate_required=settings.deployment_gate_required
        )
        if safe_path(settings.root, "quarantine").exists():
            raise Unavailable("Unconfirmed cleanup requires operator review")
        self.children = {}
        self.deployment_lease = None
        self.lock = os.open(
            safe_path(settings.root, "worker.lock"),
            os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
            0o600,
        )
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            from src.job_control.deployment_gate import register_worker

            self.deployment_lease = register_worker(settings)
            self.reconcile()
            self.store.heartbeat()
        except BaseException:
            if self.deployment_lease is not None:
                os.close(self.deployment_lease)
            os.close(self.lock)
            raise

    def reconcile(self):
        # No stored PID is trusted. A new owner waits for the old guardian's
        # parent-death cleanup, proved by its per-job lifecycle lock release.
        for job in self.store.all():
            if job.status not in {"running", "cancel_requested"}:
                continue
            directory = self.store.directory(job.job_id)
            if directory.exists():
                fd = os.open(
                    safe_path(directory, "execution.lock"),
                    os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
                    0o600,
                )
                try:
                    until = time.monotonic() + 8
                    while True:
                        try:
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except BlockingIOError:
                            if time.monotonic() > until:
                                raise Unavailable(
                                    "Previous execution cleanup remains unconfirmed"
                                ) from None
                            time.sleep(0.03)
                finally:
                    os.close(fd)
            current = self.store.get(job.job_id)
            if current.status not in TERMINAL:
                # A cancellation which never dispatched has no process to stop.
                status = (
                    "cancelled"
                    if current.status == "cancel_requested" and not directory.exists()
                    else "interrupted"
                )
                self.store.transition(
                    job.job_id,
                    status,
                    status,
                    "Restart reconciliation; no automatic rerun",
                    error=None
                    if status == "cancelled"
                    else "Interrupted execution; explicit new request required",
                )

    def step(self):
        if safe_path(self.settings.root, "quarantine").exists():
            self.store.heartbeat(0)
            raise Unavailable("Unconfirmed cleanup; dispatch quarantined")
        self.store.heartbeat()
        for job_id, child in list(self.children.items()):
            if child.poll() is not None:
                current = self.store.get(job_id)
                if current.status not in TERMINAL:
                    # Guardian's normal path always records terminal state.
                    # Unexpected loss is quarantined, never silently resumed.
                    self.store.transition(
                        job_id,
                        "interrupted",
                        "interrupted",
                        "Guardian ended without a confirmed result",
                        error="Guardian unavailable; manual workspace review required",
                    )
                    self.store.quarantine(job_id)
                    raise Unavailable("Guardian lost; dispatch quarantined")
                del self.children[job_id]
        active_processes = {
            self.store.get(job_id).process_id for job_id in self.children
        }
        from src.job_control.deployment_gate import dispatch

        with dispatch(self.settings) as permitted:
            self._dispatch(active_processes, permitted)

    def _dispatch(self, active_processes, permitted):
        for job in reversed(self.store.all()):
            if job.status == "cancel_requested" and job.job_id not in self.children:
                self.store.transition(
                    job.job_id,
                    "cancelled",
                    "cancelled",
                    "Cancelled before dispatch; no child existed",
                )
                continue
            if (
                not permitted
                or job.status != "queued"
                or len(self.children) >= self.settings.max_parallel
                or job.process_id in active_processes
            ):
                continue
            identity = next(
                (i for i in self.settings.identities if i.subject == job.initiated_by),
                None,
            )
            entry = self.settings.catalog.get(job.input_refs[0])
            if (
                identity is None
                or (
                    job.process_id == "cs50_offline_workflow"
                    and not self.settings.workflows_enabled
                )
                or (
                    job.process_id == "material_parsing"
                    and not self.settings.pdf_enabled
                )
                or (
                    job.process_id == "content_index_build"
                    and not self.settings.index_jobs_enabled
                )
                or (
                    job.process_id == "content_import"
                    and not self.settings.import_jobs_enabled
                )
                or identity.role != "operator"
                or job.parameters["course_id"] not in identity.courses
                or entry != self.store.entry(job.job_id)
            ):
                self.store.transition(
                    job.job_id,
                    "failed",
                    "failed",
                    "Current authorization or input approval revoked before dispatch",
                    error="Dispatch authorization or approved inputs changed",
                    error_class="input",
                )
                continue
            self.store.transition(
                job.job_id,
                "running",
                "dispatching",
                "Claimed by the single local executor",
            )
            try:
                directory = self.store.directory(job.job_id)
                directory.mkdir(mode=0o700)
                parent = os.getpid()
                child = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "src.job_control.guardian",
                        "--root",
                        str(self.settings.root),
                        "--job-id",
                        job.job_id,
                        "--parent",
                        str(parent),
                    ],
                    cwd=directory,
                    env=clean_environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                    preexec_fn=lambda parent=parent: arm_parent_death(parent),
                )
                self.children[job.job_id] = child
                active_processes.add(job.process_id)
            except (OSError, ValueError):
                self.store.transition(
                    job.job_id,
                    "failed",
                    "failed",
                    "Dispatch failed; no automatic retry",
                    error="Workspace conflict or local worker launch failed",
                    error_class="internal",
                )

    def close(self):
        for child in self.children.values():
            if child.poll() is None:
                child.terminate()  # Direct, unreaped child identity only.
        deadline = time.monotonic() + 8
        for child in self.children.values():
            child.wait(timeout=max(0.1, deadline - time.monotonic()))
        self.children.clear()
        self.store.heartbeat(0)
        os.close(self.lock)
        if self.deployment_lease is not None:
            os.close(self.deployment_lease)
            self.deployment_lease = None

    def serve(self):
        stopping = {"value": False}

        def stop(*args):
            stopping["value"] = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            while not stopping["value"]:
                self.step()
                time.sleep(0.1)
        finally:
            self.close()
