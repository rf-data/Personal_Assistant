"""Local single-host operations for C22-managed roles; no remote deployment.

The maintenance lock supplements, never replaces, the C16 worker/execution locks.
All writers must be stopped; only managed roles participate in this fence.
"""

import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
import time
from contextlib import closing, contextmanager
from pathlib import Path

from src.job_control.catalog import safe_path, verified_files
from src.job_control.models import TERMINAL, Job, load_settings

MAX_FILES = 20000
MAX_BYTES = 2 * 1024**3
OMIT = {
    ".operations.lock",
    ".bootstrap.lock",
    "worker.lock",
    ".deployment-admission.lock",
    ".deployment-owner.lock",
    ".deployment-worker.lock",
    ".coordinator-session.lock",
}


def private(path, *, directory=False):
    path = safe_path(Path(path))
    mode = path.stat()
    if (
        mode.st_uid != os.getuid()
        or stat.S_IMODE(mode.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(mode.st_mode) if directory else stat.S_ISREG(mode.st_mode))
    ):
        raise ValueError("Private owned directory 0700/file 0600 required")
    return path


@contextmanager
def fence(root, *, exclusive=False):
    root = private(root, directory=True)
    fd = os.open(
        root / ".operations.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        private(root / ".operations.lock")
        fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def preflight(config, *, min_free_bytes=512 * 1024**2, allow_quarantine=False):
    """Read-only checks; never creates the workspace or adopts an existing DB."""
    config = private(config)
    settings = load_settings(config)
    private(settings.root, directory=True)
    if shutil.disk_usage(settings.root).free < min_free_bytes:
        raise ValueError("Insufficient workspace capacity")
    if not os.access(settings.root, os.W_OK | os.X_OK):
        raise PermissionError("Workspace not writable")
    for entry in settings.catalog.values():
        verified_files(entry)
    if not allow_quarantine and (settings.root / "quarantine").exists():
        raise ValueError("Quarantine requires manual investigation")
    return settings


def volume_probe(root):
    """Explicit disposable local filesystem probe; no existing paths replaced."""
    root = private(root, directory=True)
    with tempfile.TemporaryDirectory(prefix=".c22-probe-", dir=root) as name:
        directory = Path(name)
        first, second = directory / "first", directory / "second"
        with first.open("xb") as stream:
            stream.write(b"synthetic C22 volume probe\n")
            stream.flush()
            os.fsync(stream.fileno())
        first.replace(second)
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        with second.open("rb") as a, second.open("rb") as b:
            fcntl.flock(a, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                fcntl.flock(b, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise ValueError("Filesystem does not enforce independent flock")
        with closing(sqlite3.connect(directory / "probe.sqlite3")) as db:
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise ValueError("WAL unavailable")
            db.execute("CREATE TABLE probe (value TEXT)")
            db.execute("INSERT INTO probe VALUES ('synthetic')")
            db.commit()
            with closing(sqlite3.connect(directory / "probe.sqlite3")) as reader:
                if reader.execute("SELECT value FROM probe").fetchone() != (
                    "synthetic",
                ):
                    raise ValueError("Shared SQLite visibility failed")
    return {
        "schema_version": 1,
        "rename_fsync": True,
        "flock": True,
        "sqlite_wal": True,
    }


@contextmanager
def database(root):
    path = safe_path(root, "jobs.sqlite3")
    private(path)
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("Unsupported database; no migration")
        if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("Database integrity failure")
        yield db
    finally:
        db.close()


def health(settings, role, *, port=8016):
    """No Store initialization or heartbeat write during health checks."""
    with database(settings.root) as db:
        if role == "worker":
            row = db.execute("SELECT heartbeat FROM worker WHERE id=1").fetchone()
            if not row or not 0 <= time.time() - row[0] < settings.worker_ttl:
                raise ValueError("Worker heartbeat unavailable")
        elif role == "api":
            import http.client

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                connection.request(
                    "GET",
                    "/v1/processes",
                    headers={"Authorization": "Bearer health-probe-invalid"},
                )
                response = connection.getresponse()
                if response.status != 401:
                    raise ValueError("API authentication boundary unavailable")
                response.read(2048)
            finally:
                connection.close()
        else:
            raise ValueError("Unknown role")


def inventory(root):
    """Bounded regular-file tree only; symlinks/devices/hard links rejected."""
    result, total, entries = {}, 0, 0
    for base, directories, files in os.walk(root, followlinks=False):
        entries += len(directories) + len(files)
        if entries > MAX_FILES:
            raise ValueError("Snapshot entry limit")
        for name in directories:
            if not stat.S_ISDIR((Path(base) / name).lstat().st_mode):
                raise ValueError("Non-directory in archive")
        for name in sorted(files):
            path = Path(base) / name
            meta = path.lstat()
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise ValueError("Only unlinked regular files supported")
            total += meta.st_size
            if len(result) >= MAX_FILES or total > MAX_BYTES:
                raise ValueError("Snapshot bounds exceeded")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            result[path.relative_to(root).as_posix()] = {
                "sha256": digest,
                "bytes": meta.st_size,
            }
    return dict(sorted(result.items()))


def copy_files(source, destination, *, workspace=False):
    files = inventory(source)
    destination.mkdir(mode=0o700)
    for name in files:
        path = Path(name)
        execution_lock = (
            len(path.parts) == 3
            and path.parts[0] == "jobs"
            and path.name == "execution.lock"
        )
        if workspace and (
            name in OMIT
            or execution_lock
            or name in {"jobs.sqlite3", "jobs.sqlite3-wal", "jobs.sqlite3-shm"}
        ):
            continue
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (source / path).open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        target.chmod(0o600)


def durable_tree(root):
    """Flush completed private copies and directory entries before returning."""
    for base, _directories, files in os.walk(root, topdown=False, followlinks=False):
        for name in files:
            fd = os.open(Path(base) / name, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def quiescent(root):
    with database(root) as db:
        jobs = [
            Job.model_validate_json(row[0])
            for row in db.execute("SELECT data FROM jobs")
        ]
        if any(job.status not in TERMINAL for job in jobs):
            raise ValueError("All jobs must be terminal before backup/restore")
        row = db.execute("SELECT heartbeat FROM worker WHERE id=1").fetchone()
        if row and row[0] != 0:
            raise ValueError("Worker must have shut down cleanly before backup")
    for job in jobs:
        for artifact in job.artifact_refs:
            path = safe_path(
                root,
                "jobs/"
                + job.job_id
                + "/results/"
                + job.parameters["output_name"]
                + ".json",
            )
            if path.stat().st_size != artifact.size_bytes:
                raise ValueError("Artifact size mismatch")
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != artifact.sha256:
                    raise ValueError("Artifact hash mismatch")
    return jobs


def backup(config, output):
    """Stopped managed writers + terminal jobs; SQLite backup API, then whole tree."""
    settings = preflight(config, allow_quarantine=True)
    output = safe_path(Path(output))
    if (
        output.exists()
        or output.is_relative_to(settings.root)
        or settings.root.is_relative_to(output)
    ):
        raise ValueError("New separate snapshot destination required")
    for entry in settings.catalog.values():
        if output.is_relative_to(entry.root) or entry.root.is_relative_to(output):
            raise ValueError("Snapshot and catalog must be separate")
    with fence(settings.root, exclusive=True):
        quiescent(settings.root)
        output.mkdir(mode=0o700)
        # Incomplete snapshots have no manifest and cannot be restored.
        copy_files(settings.root, output / "workspace", workspace=True)
        with database(settings.root) as source:
            path = output / "workspace/jobs.sqlite3"
            path.touch(mode=0o600, exist_ok=False)
            with closing(sqlite3.connect(path)) as target:
                source.backup(target)
                target.execute("PRAGMA journal_mode=DELETE")
        (output / "configuration.json").write_bytes(Path(config).read_bytes())
        (output / "configuration.json").chmod(0o600)
        (output / "catalog").mkdir(mode=0o700)
        # Copy declared inputs only; never unrelated files or adjacent secrets.
        for key, entry in settings.catalog.items():
            directory = output / "catalog" / key
            directory.mkdir(mode=0o700)
            for name, data in verified_files(entry).items():
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                path.write_bytes(data)
                path.chmod(0o600)
        manifest = {
            "schema_version": 1,
            "kind": "c22-stopped-workspace",
            "files": inventory(output),
        }
        with (output / "manifest.json").open("x") as stream:
            json.dump(manifest, stream, sort_keys=True, indent=2)
            stream.write("\n")
        (output / "manifest.json").chmod(0o600)
        durable_tree(output)
    return manifest


def restore(snapshot, destination):
    """Verify entire private bundle first; restore into an absent, isolated root.

    Configuration/catalog remain in the snapshot for deliberate operator binding.
    No services started, identity rewritten, quarantine cleared or jobs resumed.
    """
    snapshot = private(snapshot, directory=True)
    destination = safe_path(Path(destination))
    if (
        destination.exists()
        or destination.is_relative_to(snapshot)
        or snapshot.is_relative_to(destination)
    ):
        raise ValueError("Absent separate restore destination required")
    manifest_path = private(snapshot / "manifest.json")
    if manifest_path.stat().st_size > 8 * 1024**2:
        raise ValueError("Manifest limit")
    manifest = json.loads(manifest_path.read_bytes())
    if not isinstance(manifest, dict):
        raise ValueError("Snapshot manifest object required")
    actual = inventory(snapshot)
    del actual["manifest.json"]
    if (
        set(manifest) != {"schema_version", "kind", "files"}
        or manifest["schema_version"] != 1
        or manifest["kind"] != "c22-stopped-workspace"
        or manifest["files"] != actual
    ):
        raise ValueError("Snapshot manifest/hash mismatch")
    settings = load_settings(snapshot / "configuration.json")
    for key, entry in settings.catalog.items():
        verified_files(entry.model_copy(update={"root": snapshot / "catalog" / key}))
    jobs = quiescent(snapshot / "workspace")
    copy_files(snapshot / "workspace", destination)
    if any(
        (destination / name).exists()
        for name in ("deployment-gate.v1.jsonl", "deployment-gate.v2.jsonl")
    ):
        from src.job_control.deployment_gate import hold_restored_root

        hold_restored_root(destination)
    # Copy is not an activation: the original absolute catalog bindings are retained.
    quiescent(destination)
    durable_tree(destination)
    return {
        "schema_version": 1,
        "jobs": len(jobs),
        "files": len(inventory(destination)),
        "activated": False,
    }
