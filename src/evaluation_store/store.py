"""Bounded append-only ledger with transactional materialized heads, no migration."""

import fcntl
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime

from src.content_store.artifacts import (
    FILE_FLAGS,
    _open_directory,
    _private,
    explicit_root,
)
from src.content_store.errors import Busy, Conflict, IntegrityError, Unavailable
from src.content_store.models import canonical, fingerprint
from src.evaluation_store.models import ReviewRevision

APPLICATION_ID = 0x45564131
MAX_DATABASE = 64 * 1024**2
MAX_EVENTS = 1000
DDL = {
    (
        "table",
        "events",
    ): "CREATE TABLE events (seq INTEGER PRIMARY KEY, digest TEXT NOT NULL UNIQUE, body TEXT NOT NULL)",
    (
        "table",
        "heads",
    ): "CREATE TABLE heads (entity TEXT PRIMARY KEY, revision TEXT NOT NULL, value TEXT NOT NULL)",
}


class EvaluationStore:
    def __init__(self, root):
        self.root = explicit_root(root)
        try:
            fd = _open_directory(self.root)
            try:
                info = _private(fd, directory=True)
                self.identity = (info.st_dev, info.st_ino)
            finally:
                os.close(fd)
            with self.connection():
                pass
        except OSError:
            raise Unavailable("review store unavailable") from None

    @classmethod
    def initialize(cls, root):
        root = explicit_root(root)
        parent = _open_directory(root.parent)
        try:
            os.mkdir(root.name, 0o700, dir_fd=parent)
            os.fsync(parent)
        except FileExistsError:
            raise Conflict("new review root required") from None
        finally:
            os.close(parent)
        directory = _open_directory(root)
        try:
            for name in (".review.lock", "evaluation.sqlite3"):
                fd = os.open(
                    name,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                os.close(fd)
            db = sqlite3.connect(f"/proc/self/fd/{directory}/evaluation.sqlite3")
            try:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
                for statement in DDL.values():
                    db.execute(statement)
                db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                db.execute("PRAGMA user_version=1")
                db.commit()
            finally:
                db.close()
            os.fsync(directory)
        finally:
            os.close(directory)
        return cls(root)

    @contextmanager
    def connection(self, *, write=False):
        """Content locks, if needed, must precede this nonblocking ledger lock.

        Exclusive even for reads: SQLite may recover its own hot DELETE journal
        after a killed process. No custom replay or application-level retries.
        """
        directory = lock = db = None
        try:
            directory = _open_directory(self.root)
            info = _private(directory, directory=True)
            if (info.st_dev, info.st_ino) != self.identity:
                raise IntegrityError("review root identity changed")
            lock = os.open(".review.lock", FILE_FLAGS, dir_fd=directory)
            _private(lock)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy("review store busy") from None
            for name in os.listdir(directory):
                if name not in {
                    ".review.lock",
                    "evaluation.sqlite3",
                    "evaluation.sqlite3-journal",
                }:
                    raise IntegrityError("unknown review root entry")
                fd = os.open(name, FILE_FLAGS, dir_fd=directory)
                try:
                    if _private(fd).st_size > MAX_DATABASE:
                        raise Unavailable("review capacity exceeded")
                finally:
                    os.close(fd)
            db = sqlite3.connect(
                f"file:/proc/self/fd/{directory}/evaluation.sqlite3?mode=rw",
                uri=True,
                timeout=0,
            )
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA max_page_count=16384")
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != 1
                or {
                    (r[0], r[1]): r[2]
                    for r in db.execute(
                        "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                    )
                }
                != DDL
                or db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
            ):
                raise IntegrityError("unknown or damaged review schema")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            self.verify(db)
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
        except sqlite3.OperationalError:
            raise Unavailable("review database unavailable") from None
        except (sqlite3.Error, OSError, ValueError, KeyError, TypeError):
            raise IntegrityError("review ledger invalid") from None
        finally:
            if db is not None:
                db.close()
            if lock is not None:
                os.close(lock)
            if directory is not None:
                os.close(directory)

    @staticmethod
    def verify(db):
        rows = db.execute(
            "SELECT * FROM events ORDER BY seq LIMIT ?", (MAX_EVENTS + 1,)
        ).fetchall()
        if len(rows) > MAX_EVENTS:
            raise Unavailable("review event limit")
        previous = None
        heads = {}
        keys = set()
        for seq, row in enumerate(rows, 1):
            body = json.loads(row["body"])
            ReviewRevision.model_validate(body)
            key = (body["actor"], body["entity"], body["idempotency_key"])
            if (
                len(row["body"].encode()) > 524288
                or row["seq"] != seq
                or body["previous"] != previous
                or body["previous_revision"] != heads.get(body["entity"], (None,))[0]
                or row["digest"] != fingerprint(body)
                or key in keys
            ):
                raise IntegrityError("review revision chain mismatch")
            keys.add(key)
            previous = row["digest"]
            heads[body["entity"]] = (row["digest"], canonical(body["value"]).decode())
        actual = {
            r["entity"]: (r["revision"], r["value"])
            for r in db.execute("SELECT * FROM heads")
        }
        if heads != actual:
            raise IntegrityError("review heads mismatch")

    @staticmethod
    def get(db, entity):
        row = db.execute("SELECT * FROM heads WHERE entity=?", (entity,)).fetchone()
        return (
            None
            if row is None
            else dict(revision=row["revision"], value=json.loads(row["value"]))
        )

    @staticmethod
    def history(db, entity):
        return [
            dict(revision=r["digest"], **json.loads(r["body"]))
            for r in db.execute("SELECT * FROM events ORDER BY seq")
            if json.loads(r["body"])["entity"] == entity
        ]

    @classmethod
    def replay(cls, db, entity, actor, request):
        intent = fingerprint(request.model_dump(mode="json"))
        for event in cls.history(db, entity):
            if (
                event["actor"] == actor.subject
                and event["idempotency_key"] == request.idempotency_key
            ):
                if event["intent"] != intent:
                    raise Conflict("idempotency intent changed")
                return dict(revision=event["revision"], value=event["value"])
        return None

    @classmethod
    def append(cls, db, entity, actor, request, value, binding):
        old = cls.get(db, entity)
        if request.expected_revision != (old["revision"] if old else None):
            raise Conflict("review revision changed")
        count = db.execute("SELECT count(*) FROM events").fetchone()[0]
        if count >= MAX_EVENTS:
            raise Unavailable("review event limit")
        prior = db.execute(
            "SELECT digest FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        body = dict(
            schema_version=1,
            entity=entity,
            previous=prior[0] if prior else None,
            previous_revision=old["revision"] if old else None,
            actor=actor.subject,
            time=datetime.now(UTC).isoformat(),
            reason=request.reason,
            idempotency_key=request.idempotency_key,
            intent=fingerprint(request.model_dump(mode="json")),
            binding=binding,
            value=value,
        )
        if len(canonical(body)) > 524288:
            raise Unavailable("review revision limit")
        digest = fingerprint(body)
        db.execute(
            "INSERT INTO events VALUES (?,?,?)",
            (count + 1, digest, canonical(body).decode()),
        )
        db.execute(
            "INSERT INTO heads VALUES (?,?,?) ON CONFLICT(entity) DO UPDATE SET revision=excluded.revision,value=excluded.value",
            (entity, digest, canonical(value).decode()),
        )
        return dict(revision=digest, value=value)
