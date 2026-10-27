"""C26-F local TEST witness and opt-in enrollment guard, never a remote service.

A separate file models an external CAS boundary. Its owner can roll back both
files, so this is explicitly NOT independent protection against that owner.
"""

import hashlib
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import Field

from src.job_control.catalog import safe_path
from src.job_control.deployment_scope import VersionedV2
from src.job_control.models import Contract, Identifier, Sha, canonical
from src.job_control.operations import private
from src.job_control.store import Unavailable

ENROLLMENT = "coordinator-test-enrollment.v1.json"
SESSION_LOCK = ".coordinator-session.lock"


class Refused(Unavailable):
    pass


class Enrollment(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["local_test_only"] = "local_test_only"
    witness_path: Path
    witness_id: Sha
    root_id: Sha


def root_identity(root):
    root = private(root, directory=True)
    info = root.stat()
    return hashlib.sha256(
        canonical(dict(path=str(root), device=info.st_dev, inode=info.st_ino))
    ).hexdigest()


class Anchor(VersionedV2, Contract):
    schema_version: Literal[1] = 1
    mode: Literal["local_test_only"] = "local_test_only"
    root_id: Sha
    revision: int = Field(strict=True, ge=0)
    epoch: int = Field(strict=True, ge=0)
    sequence: int = Field(strict=True, ge=1)
    journal_sha256: Sha
    status: Literal["held", "active", "claimed", "released"]
    session_id: Sha | None = None
    expires_at: float = Field(strict=True, allow_inf_nan=False, default=0.0)
    grant_id: Identifier | None = None
    grant_sha256: Sha | None = None

    def check_journal(self, rows, *, exact=False):
        if (
            self.sequence > len(rows)
            or rows[self.sequence - 1]["sha256"] != self.journal_sha256
        ):
            raise Refused("coordinator_journal_rollback_or_fork")
        if exact and self.sequence != len(rows):
            raise Refused("coordinator_unanchored_journal")


class LocalTestWitness:
    kind = "local_test_only"

    def __init__(self, path, witness_id):
        self.path = private(path)
        if self.path.stat().st_nlink != 1 or self.path.stat().st_size > 4 * 1024 * 1024:
            raise Refused("coordinator_private_bounded_witness_required")
        self.witness_id = witness_id
        with self.connection() as db:
            if db.execute(
                "SELECT value FROM metadata WHERE key='identity'"
            ).fetchone() != (witness_id,):
                raise Refused("coordinator_witness_identity_mismatch")

    @classmethod
    def create(cls, path):
        """Explicit empty fixture creation only; never adopts/migrates an existing DB."""
        path = Path(path)
        private(path.parent, directory=True)
        fd = os.open(
            safe_path(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        os.close(fd)
        identity = secrets.token_hex(32)
        with sqlite3.connect(path) as db:
            db.executescript(
                "CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE anchors(root TEXT PRIMARY KEY,data TEXT NOT NULL); CREATE TABLE grants(root TEXT NOT NULL,id TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(root,id));"
            )
            db.execute("INSERT INTO metadata VALUES('identity',?)", (identity,))
            db.execute("INSERT INTO metadata VALUES('schema','c26f-test-witness/1')")
        return cls(path, identity)

    @contextmanager
    def connection(self, *, write=False):
        private(self.path)
        if self.path.stat().st_nlink != 1:
            raise Refused("coordinator_witness_file_invalid")
        db = sqlite3.connect(
            self.path.as_uri() + ("?mode=rw" if write else "?mode=ro"),
            uri=True,
            timeout=0.2,
        )
        try:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA synchronous=FULL")
            if db.execute(
                "SELECT value FROM metadata WHERE key='schema'"
            ).fetchone() != ("c26f-test-witness/1",) or db.execute(
                "SELECT value FROM metadata WHERE key='identity'"
            ).fetchone() != (self.witness_id,):
                raise Refused("coordinator_witness_contract_invalid")
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        finally:
            db.close()

    def provision(self, root_id, rows):
        last = rows[-1]
        anchor = Anchor(
            root_id=root_id,
            revision=0,
            epoch=0,
            sequence=len(rows),
            journal_sha256=last["sha256"],
            status="held",
        )
        with self.connection(write=True) as db:
            db.execute(
                "INSERT INTO anchors VALUES(?,?)", (root_id, anchor.model_dump_json())
            )
        return anchor

    def read(self, root_id):
        with self.connection() as db:
            row = db.execute(
                "SELECT data FROM anchors WHERE root=?", (root_id,)
            ).fetchone()
        if row is None:
            raise Refused("coordinator_external_state_missing")
        return Anchor.model_validate_json(row[0])

    def cas(self, previous, replacement, *, consume=None):
        if (
            replacement.root_id != previous.root_id
            or replacement.revision != previous.revision + 1
            or replacement.epoch < previous.epoch
        ):
            raise Refused("coordinator_nonmonotonic_cas")
        with self.connection(write=True) as db:
            row = db.execute(
                "SELECT data FROM anchors WHERE root=?", (previous.root_id,)
            ).fetchone()
            if row is None or Anchor.model_validate_json(row[0]) != previous:
                raise Refused("coordinator_external_cas_conflict")
            if consume:
                grant_id, digest = consume
                try:
                    db.execute(
                        "INSERT INTO grants VALUES(?,?,?)",
                        (previous.root_id, grant_id, digest),
                    )
                except sqlite3.IntegrityError:
                    raise Refused("coordinator_grant_replay") from None
            db.execute(
                "UPDATE anchors SET data=? WHERE root=?",
                (replacement.model_dump_json(), previous.root_id),
            )
        return replacement


def enrollment(root):
    path = safe_path(root, ENROLLMENT)
    if not path.exists():
        return None
    path = private(path)
    if path.stat().st_size > 4096:
        raise Refused("coordinator_enrollment_invalid")
    doc = Enrollment.model_validate_json(path.read_bytes())
    if root_identity(root) != doc.root_id or doc.witness_path.is_relative_to(
        Path(root)
    ):
        raise Refused("coordinator_enrollment_identity_mismatch")
    return doc


def guard(root, rows, *, dispatch=False, required=False):
    """Explicit enrolled test roots only. Called under existing admission lock."""
    doc = enrollment(root)
    if doc is None:
        if required:
            raise Refused("coordinator_required_enrollment_missing")
        return True
    anchor = LocalTestWitness(doc.witness_path, doc.witness_id).read(doc.root_id)
    anchor.check_journal(rows)
    if anchor.status == "released" and anchor.session_id is None:
        anchor.check_journal(rows, exact=True)
        return rows[-1]["phase"] == "open"
    if (
        dispatch
        and anchor.status == "active"
        and anchor.grant_id is not None
        and time.time() < anchor.expires_at
    ):
        from src.job_control.deployment_gate import Busy, _lock

        try:
            with _lock(root, SESSION_LOCK):
                return False
        except Busy:
            return rows[-1]["phase"] == "draining"
    return False
