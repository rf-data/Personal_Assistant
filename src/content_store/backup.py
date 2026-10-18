"""Isolated manifest-last snapshots via SQLite backup API. Never activation."""

import hashlib
import os
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.artifacts import (
    FILE_FLAGS,
    _Artifacts,
    _open_directory,
    _private,
    _sync,
    create_layout,
    explicit_root,
)
from src.content_store.errors import (
    ContentStoreError,
    IntegrityError,
    InvalidInput,
    Unavailable,
)
from src.content_store.limits import (
    MAX_FILES,
    MAX_STORE_BYTES,
    capacity,
    directory_entries,
)
from src.content_store.models import canonical, sha256
from src.content_store.operations import authorize_all, exclusive, scan
from src.content_store.store import ContentStore
from src.job_control.models import Contract, Sha
from src.tools_materials.quality import _json

PATH = re.compile(
    r"(?:content\.sqlite3|blobs/sha256/[a-f0-9]{2}/[a-f0-9]{64}|staging/[a-f0-9]{32}/[a-f0-9]{64}|incidents/[a-f0-9]{32}\.json)"
)


class SnapshotFile(Contract):
    path: str
    sha256: Sha
    size_bytes: int = Field(strict=True, ge=0, le=MAX_STORE_BYTES)

    @model_validator(mode="after")
    def safe(self):
        if not PATH.fullmatch(self.path):
            raise ValueError("Unsupported snapshot path")
        if self.path.startswith("blobs/") and (
            self.path.rsplit("/", 1)[1] != self.sha256
            or self.path.split("/")[2] != self.sha256[:2]
        ):
            raise ValueError("Snapshot blob identity mismatch")
        return self


class Snapshot(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["content-snapshot-v1"] = "content-snapshot-v1"
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    database_identity: Literal["content-v1"] = "content-v1"
    database_version: Literal[1] = 1
    purpose: Literal["content", "synthetic_test"]
    publication_seq: int = Field(ge=0)
    collection_revision: int = Field(ge=0)
    files: tuple[SnapshotFile, ...] = Field(min_length=1, max_length=MAX_FILES)

    @model_validator(mode="after")
    def bounded(self):
        names = [f.path for f in self.files]
        if (
            names != sorted(set(names))
            or "content.sqlite3" not in names
            or sum(f.size_bytes for f in self.files) > MAX_STORE_BYTES
        ):
            raise ValueError("Snapshot identity or size limit")
        return self


class SnapshotManifest(Contract):
    snapshot: Snapshot
    sha256: Sha

    @model_validator(mode="after")
    def digest(self):
        if sha256(canonical(self.snapshot.model_dump(mode="json"))) != self.sha256:
            raise ValueError("Snapshot manifest digest mismatch")
        return self


def _read_file(artifacts, name, output=None):
    parent, _, leaf = name.rpartition("/")
    with artifacts.directory(parent) as directory:
        fd = os.open(leaf, FILE_FLAGS, dir_fd=directory)
        try:
            meta = _private(fd)
            if meta.st_size > MAX_STORE_BYTES:
                raise Unavailable("snapshot file size limit")
            value = hashlib.sha256()
            size = 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > meta.st_size:
                    raise IntegrityError("snapshot input changed")
                value.update(chunk)
                if output is not None:
                    output.write(chunk)
            if size != meta.st_size:
                raise IntegrityError("snapshot input size mismatch")
            return SnapshotFile(path=name, sha256=value.hexdigest(), size_bytes=size)
        finally:
            os.close(fd)


def _new_file(artifacts, name, source):
    parent, _, leaf = name.rpartition("/")
    with artifacts.directory(parent, create=True) as directory:
        fd = os.open(
            leaf,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        try:
            with os.fdopen(fd, "wb", closefd=False) as output:
                result = _read_file(source, name, output)
                output.flush()
                _sync(fd)
            _sync(directory)
            return result
        finally:
            os.close(fd)


def _separate(source, target):
    target = explicit_root(target)
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise InvalidInput("separate explicit snapshot root required")
    return target


def _empty(root):
    parent = _open_directory(root.parent)
    try:
        try:
            os.mkdir(root.name, 0o700, dir_fd=parent)
            _sync(parent)
        except FileExistsError:
            pass
    finally:
        os.close(parent)
    artifacts = _Artifacts(root)
    with artifacts.directory() as fd:
        if next(directory_entries(fd), None) is not None:
            raise Unavailable("new empty destination required")
    return artifacts


def _selection(store, db):
    names = {"content.sqlite3"}
    for row in db.execute("SELECT sha256 FROM artifacts"):
        digest = row[0]
        names.add(f"blobs/sha256/{digest[:2]}/{digest}")
    for row in db.execute("SELECT id FROM processing_runs"):
        relative = f"staging/{row[0]}"
        try:
            with store._artifacts.directory(relative) as fd:
                for name in directory_entries(fd):
                    if not re.fullmatch(r"[a-f0-9]{64}", name):
                        raise IntegrityError("unknown run staging entry")
                    names.add(relative + "/" + name)
        except FileNotFoundError:
            pass
    try:
        with store._artifacts.directory("incidents") as fd:
            for name in directory_entries(fd):
                if not re.fullmatch(r"[a-f0-9]{32}\.json", name):
                    raise IntegrityError("unknown incident entry")
                names.add("incidents/" + name)
    except FileNotFoundError:
        pass
    if len(names) > MAX_FILES:
        raise Unavailable("snapshot entry limit")
    return sorted(names)


def backup(store, destination, *, actor, snapshot_id=None):
    """Nonblocking exclusive maintenance; all Sources must belong to actor."""
    target = _separate(store.root, Path(destination))
    try:
        with (
            exclusive(store, actor, writable=False) as actor,
            store._connection() as db,
        ):
            authorize_all(store, db, actor)
            findings, _ = scan(store, db)
            if findings:
                raise IntegrityError("inconsistent store cannot be backed up")
            names = _selection(store, db)
            before = [_read_file(store._artifacts, name) for name in names]
            if sum(f.size_bytes for f in before) > MAX_STORE_BYTES:
                raise Unavailable("snapshot size limit")
            output = _empty(target)
            with output.directory("staging", create=True):
                pass
            with output.directory() as directory:
                capacity(directory, sum(f.size_bytes for f in before))
                fd = os.open(
                    "content.sqlite3",
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                os.close(fd)
            deadline = time.monotonic() + 15

            def progress(status, remaining, total):
                if time.monotonic() > deadline:
                    raise Unavailable("SQLite snapshot time limit")

            copy = sqlite3.connect(target / "content.sqlite3", timeout=2)
            copy.row_factory = sqlite3.Row
            copy.execute("PRAGMA synchronous=FULL")
            try:
                db.backup(copy, pages=256, progress=progress, sleep=0.01)
                copy.execute("PRAGMA journal_mode=DELETE")
                ContentStore._validate(copy)
            finally:
                copy.close()
            files = [_read_file(output, "content.sqlite3")]
            for name in names:
                if name != "content.sqlite3":
                    files.append(_new_file(output, name, store._artifacts))
            meta = db.execute(
                "SELECT purpose,publication_seq,collection_revision FROM metadata WHERE id=1"
            ).fetchone()
            payload = Snapshot(
                snapshot_id=snapshot_id or uuid.uuid4().hex,
                purpose=meta[0],
                publication_seq=meta[1],
                collection_revision=meta[2],
                files=tuple(sorted(files, key=lambda f: f.path)),
            )
            manifest = SnapshotManifest(
                snapshot=payload,
                sha256=sha256(canonical(payload.model_dump(mode="json"))),
            )
            data = canonical(manifest.model_dump(mode="json"))
            with output.directory() as directory:
                fd = os.open(
                    "manifest.partial",
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                try:
                    with os.fdopen(fd, "wb", closefd=False) as stream:
                        stream.write(data)
                        stream.flush()
                        _sync(fd)
                finally:
                    os.close(fd)
                os.link(
                    "manifest.partial",
                    "manifest.json",
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                    follow_symlinks=False,
                )
                os.unlink("manifest.partial", dir_fd=directory)
                _sync(directory)
            return manifest
    except ContentStoreError:
        raise
    except (OSError, sqlite3.Error, ValueError):
        raise Unavailable("content snapshot could not be completed") from None


def _snapshot(snapshot, actor):
    artifacts = _Artifacts(snapshot)
    with artifacts.directory() as fd:
        file = os.open("manifest.json", FILE_FLAGS, dir_fd=fd)
        try:
            if _private(file).st_size > 8 * 1024**2:
                raise IntegrityError("snapshot manifest size limit")
            data = os.read(file, 8 * 1024**2 + 1)
        finally:
            os.close(file)
    value = _json(data)
    canonical(value)
    manifest = SnapshotManifest.model_validate(value)
    actual = set()
    entries = 0
    pending = [""]
    while pending:
        parent = pending.pop()
        with artifacts.directory(parent) as fd:
            for name in directory_entries(fd):
                entries += 1
                if entries > MAX_FILES + 1000:
                    raise IntegrityError("snapshot directory limit")
                relative = (parent + "/" if parent else "") + name
                meta = os.stat(name, dir_fd=fd, follow_symlinks=False)
                import stat

                if stat.S_ISDIR(meta.st_mode):
                    pending.append(relative)
                elif stat.S_ISREG(meta.st_mode):
                    actual.add(relative)
                else:
                    raise IntegrityError("unsafe snapshot entry")
                if len(actual) + len(pending) > MAX_FILES + 1:
                    raise IntegrityError("snapshot entry limit")
    if actual != {f.path for f in manifest.snapshot.files} | {"manifest.json"}:
        raise IntegrityError("snapshot file inventory mismatch")
    for reference in manifest.snapshot.files:
        if _read_file(artifacts, reference.path) != reference:
            raise IntegrityError("snapshot hash mismatch")
    db = sqlite3.connect(
        (artifacts.root / "content.sqlite3").as_uri() + "?mode=ro&immutable=1",
        uri=True,
        timeout=2,
    )
    try:
        db.row_factory = sqlite3.Row
        ContentStore._validate(db)
        temporary = object.__new__(ContentStore)
        temporary._artifacts, temporary.root = artifacts, artifacts.root
        authorize_all(temporary, db, actor)
        findings, _ = scan(temporary, db)
        if findings:
            raise IntegrityError("snapshot reference integrity failure")
        meta = db.execute(
            "SELECT purpose,publication_seq,collection_revision FROM metadata WHERE id=1"
        ).fetchone()
        if tuple(meta) != (
            manifest.snapshot.purpose,
            manifest.snapshot.publication_seq,
            manifest.snapshot.collection_revision,
        ):
            raise IntegrityError("snapshot database identity mismatch")
        runs = tuple(r[0] for r in db.execute("SELECT id FROM processing_runs"))
    finally:
        db.close()
    return artifacts, manifest, runs


def restore(snapshot, destination, *, actor):
    """Verify first; private empty new root only. No adoption or writer restart."""
    from src.content_store.models import checked_actor

    actor = checked_actor(actor)
    if actor.role != "operator":
        from src.content_store.errors import Forbidden

        raise Forbidden("operator restore required")
    try:
        source, manifest, runs = _snapshot(Path(snapshot), actor)
        target = _separate(source.root, Path(destination))
        # create_layout also rejects existing data; no destination touched before verification.
        output = create_layout(target)
        with output.directory() as fd:
            capacity(fd, sum(f.size_bytes for f in manifest.snapshot.files))
            marker = os.open(
                ".content-recovery-required",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=fd,
            )
            os.close(marker)
            _sync(fd)
        for ref in manifest.snapshot.files:
            if _new_file(output, ref.path, source) != ref:
                raise IntegrityError("snapshot changed during restore")
        for run_id in runs:
            output.create_run_lock(run_id)
        restored = object.__new__(ContentStore)
        restored._artifacts, restored.root, restored.read_only = output, target, False
        db = sqlite3.connect(
            (target / "content.sqlite3").as_uri() + "?mode=rw",
            uri=True,
            timeout=2,
        )
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            ContentStore._validate(db)
            findings, _ = scan(restored, db)
            if findings:
                raise IntegrityError("restored content integrity failure")
            db.commit()
            if db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
                raise Unavailable("restored database checkpoint busy")
        finally:
            db.close()
        with output.directory() as fd:
            os.unlink(".content-recovery-required", dir_fd=fd)
            _sync(fd)
        return manifest
    except ContentStoreError:
        raise
    except (OSError, sqlite3.Error, ValueError):
        raise IntegrityError("snapshot could not be verified or restored") from None
