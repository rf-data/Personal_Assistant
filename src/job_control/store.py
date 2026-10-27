"""Private SQLite v1 state. Atomic requests and bounded durable structured events."""

import fcntl
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime

from src.job_control.catalog import safe_path
from src.job_control.models import TERMINAL, Job, canonical


def now():
    return datetime.now(UTC).isoformat()


class Conflict(ValueError):
    pass


class Unavailable(RuntimeError):
    pass


class Store:
    def __init__(
        self,
        root,
        *,
        deployment_gate_required=False,
        deployment_gate_protocol="c26-gate-v1",
        coordinator_test_required=False,
        gate_settings_sha256=None,
    ):
        self.gate_settings_sha256 = gate_settings_sha256
        self.coordinator_test_required = coordinator_test_required
        self.deployment_gate_required = deployment_gate_required
        self.deployment_gate_protocol = deployment_gate_protocol
        self.root = safe_path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_mode & 0o077:
            raise ValueError("Private workspace requires mode 0700")
        for name in (
            "jobs.sqlite3",
            "jobs.sqlite3-wal",
            "jobs.sqlite3-shm",
            "worker.lock",
            "jobs",
        ):
            safe_path(self.root, name)
        bootstrap = os.open(
            safe_path(self.root, ".bootstrap.lock"),
            os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
            0o600,
        )
        try:
            until = time.monotonic() + 5
            while True:
                try:
                    fcntl.flock(bootstrap, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= until:
                        raise Unavailable("Job database initialization busy") from None
                    time.sleep(0.01)
            self._initialize()
        finally:
            os.close(bootstrap)

    def _initialize(self):
        self.path = self.root / "jobs.sqlite3"
        # Reserve our database exclusively before sqlite opens it, avoiding loose defaults.
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            fd = None
        if fd is not None:
            os.close(fd)
        with self.connection(write=True) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported Job DB version; no migration")
            tables = {
                r[0]
                for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if version == 0 and tables:
                raise ValueError("Foreign database; adoption forbidden")
            if version == 1 and tables != {"jobs", "events", "worker"}:
                raise ValueError("Corrupt database schema; no automatic repair")
            if version == 1:
                layouts = {
                    "jobs": ("id", "owner", "request_key", "intent", "data", "catalog"),
                    "events": ("seq", "job_id", "at", "status", "phase", "message"),
                    "worker": ("id", "heartbeat"),
                }
                for table, names in layouts.items():
                    if (
                        tuple(
                            r[1] for r in db.execute("PRAGMA table_info(" + table + ")")
                        )
                        != names
                    ):
                        raise ValueError(
                            "Corrupt database columns; no automatic repair"
                        )
            schema = """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, request_key TEXT NOT NULL,
                    intent TEXT NOT NULL, data TEXT NOT NULL, catalog TEXT NOT NULL,
                    UNIQUE(owner, request_key));
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, job_id TEXT NOT NULL, at TEXT NOT NULL,
                    status TEXT NOT NULL, phase TEXT NOT NULL, message TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS worker (id INTEGER PRIMARY KEY CHECK(id=1), heartbeat REAL NOT NULL);
                PRAGMA user_version=1;
            """
            if version == 0:
                for statement in schema.split(";"):
                    if statement.strip():
                        db.execute(statement)
        # Only after identity/schema checks: never switch a foreign database's journal.
        # Controller readers must not starve guardian result/heartbeat commits.
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
        (self.root / "jobs").mkdir(exist_ok=True, mode=0o700)

    @contextmanager
    def connection(self, write=False):
        safe_path(self.root, "jobs.sqlite3")
        # A last-connection WAL cleanup can briefly return SQLITE_BUSY even to
        # connection-local PRAGMAs, sometimes without invoking the busy handler.
        # Reopen only before any transaction/body, within the existing 2s bound.
        # Never replay a transaction, commit or job after a locking error.
        deadline = time.monotonic() + 2
        while True:
            db = sqlite3.connect(self.path, timeout=max(0, deadline - time.monotonic()))
            try:
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA synchronous=FULL")
            except sqlite3.OperationalError as error:
                db.close()
                remaining = deadline - time.monotonic()
                if (
                    getattr(error, "sqlite_errorcode", 0) & 0xFF != sqlite3.SQLITE_BUSY
                    or remaining <= 0
                ):
                    raise
                time.sleep(min(0.01, remaining))
            except BaseException:
                db.close()
                raise
            else:
                break
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def get_db(db, job_id):
        row = db.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError("Unknown job")
        return Job.model_validate_json(row[0])

    def get(self, job_id):
        with self.connection() as db:
            return self.get_db(db, job_id)

    def all(self):
        with self.connection() as db:
            return tuple(
                Job.model_validate_json(r[0])
                for r in db.execute("SELECT data FROM jobs ORDER BY rowid DESC")
            )

    @staticmethod
    def put_db(db, job, message):
        db.execute(
            "UPDATE jobs SET data=? WHERE id=?", (job.model_dump_json(), job.job_id)
        )
        db.execute(
            "INSERT INTO events(job_id,at,status,phase,message) VALUES(?,?,?,?,?)",
            (job.job_id, now(), job.status, job.phase, message),
        )

    def transition(self, job_id, status, phase, message, **updates):
        if status == "queued":
            from src.job_control.deployment_gate import admission

            with admission(self):
                return self._transition(job_id, status, phase, message, **updates)
        return self._transition(job_id, status, phase, message, **updates)

    def _transition(self, job_id, status, phase, message, **updates):
        with self.connection(write=True) as db:
            old = self.get_db(db, job_id)
            if old.status in TERMINAL:
                return old
            if old.status == "cancel_requested" and status == "running":
                if updates.get("started_at"):
                    changed = old.model_copy(
                        update={"started_at": updates["started_at"]}
                    )
                    self.put_db(db, changed, message)
                    return changed
                return old
            if old.status != "created" and status == "queued":
                return old
            if old.status == "cancel_requested" and status in {"completed", "failed"}:
                status, phase = "cancelled", "cancelled"
                updates.update(
                    error=None, error_class=None, artifact_refs=(), output_refs=()
                )
            allowed = {
                "created": {"queued", "cancel_requested", "interrupted"},
                "queued": {"running", "cancel_requested", "failed", "interrupted"},
                "running": {
                    "running",
                    "completed",
                    "failed",
                    "cancel_requested",
                    "interrupted",
                },
                "cancel_requested": {"cancelled", "failed", "interrupted"},
            }
            if status not in allowed[old.status]:
                raise Conflict("Invalid state transition")
            changed = Job.model_validate(
                {
                    **old.model_dump(),
                    "status": status,
                    "phase": phase,
                    "cancellable": status in {"queued", "running"},
                    **updates,
                    **({"finished_at": now()} if status in TERMINAL else {}),
                }
            )
            self.put_db(db, changed, message)
            return changed

    def heartbeat(self, value=None):
        with self.connection(write=True) as db:
            db.execute(
                "INSERT OR REPLACE INTO worker VALUES(1,?)",
                (time.time() if value is None else value,),
            )

    def worker_available(self, ttl):
        if safe_path(self.root, "quarantine").exists():
            return False
        with self.connection() as db:
            row = db.execute("SELECT heartbeat FROM worker WHERE id=1").fetchone()
        return bool(row and 0 <= time.time() - row[0] < ttl)

    def quarantine(self, job_id):
        path = safe_path(self.root, "quarantine")
        try:
            with path.open("x") as stream:
                stream.write(job_id + "\n")
        except FileExistsError:
            pass
        self.heartbeat(0)

    def entry(self, job_id):
        from src.job_control.models import CatalogEntry

        with self.connection() as db:
            row = db.execute(
                "SELECT catalog FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError("Unknown job")
        return CatalogEntry.model_validate_json(row[0])

    def directory(self, job_id):
        # Validation never accepts directory separators, even for internal callers.
        from pydantic import TypeAdapter

        from src.job_control.models import Identifier

        TypeAdapter(Identifier).validate_python(job_id)
        return safe_path(self.root / "jobs", job_id)

    def logs(self, job_id, *, cursor=0, limit=100, query=""):
        if not 0 <= cursor or not 1 <= limit <= 200 or len(query) > 100:
            raise ValueError("Log bounds")
        with self.connection() as db:
            rows = db.execute(
                "SELECT seq,at,status,phase,message FROM events WHERE job_id=? AND seq>? ORDER BY seq LIMIT 201",
                (job_id, cursor),
            ).fetchall()
            job = self.get_db(db, job_id)
        # Structured events have fixed safe messages; no arbitrary runner stdout is stored.
        # Reserve the bounded response envelope and one comma per event.
        lines, size, position = [], 200, cursor
        for seq, at, status, phase, message in rows:
            line = dict(
                sequence=seq,
                at=at,
                job_id=job_id,
                status=status,
                phase=phase,
                message=message,
                process_id=job.process_id,
                exit_code=job.exit_code if status in TERMINAL else None,
                duration_seconds=job.duration_seconds if status in TERMINAL else None,
                error=job.error if status in TERMINAL else None,
                artifact_refs=list(job.output_refs) if status in TERMINAL else [],
            )
            length = len(canonical(line)) + 1
            if size + length > 16000 or len(lines) >= limit:
                break
            position = seq
            if query.casefold() in canonical(line).decode().casefold():
                lines.append(line)
                size += length
        return dict(
            schema_version=1,
            events=lines,
            next_cursor=position,
            truncated=bool(len(rows) == 201 or (rows and position < rows[-1][0])),
        )
