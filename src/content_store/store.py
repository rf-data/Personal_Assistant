"""Independent content-v1 register. No implicit initialization or bundle import."""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager

from pydantic import ValidationError

from src.content_store import schema
from src.content_store.artifacts import (
    FILE_FLAGS,
    _Artifacts,
    _private,
    _sync,
    create_layout,
)
from src.content_store.errors import (
    Busy,
    Conflict,
    ContentStoreError,
    Forbidden,
    IntegrityError,
    InvalidInput,
    NotFound,
    Unavailable,
)
from src.content_store.models import (
    ArtifactReference,
    BlockPage,
    ContentBlock,
    ParsedDocumentVersion,
    ParsedDocumentView,
    ProcessingRun,
    RetryAttempt,
    Source,
    SourceGrant,
    SourceRegistration,
    SourceVersion,
    SourceView,
    canonical,
    checked_actor,
    fingerprint,
    sha256,
    snapshot,
)
from src.model_discovery.cs50 import deterministic_id


def _encoded(model):
    value = model.model_dump(mode="json")
    # Keep ordinary runs byte-compatible with the pre-retry JSON shape.
    if isinstance(model, ProcessingRun) and model.retry_of is None:
        value.pop("retry_of")
    return canonical(value).decode("utf-8")


def _retry_parent(db, run, manifest=None):
    """Validate persisted lineage without changing the terminal predecessor."""
    row = db.execute(
        "SELECT data FROM processing_runs WHERE id=?", (run.retry_of,)
    ).fetchone()
    if row is None:
        raise Conflict("retry predecessor required")
    parent = ProcessingRun.model_validate_json(row[0])
    manifest = run.manifest if manifest is None else manifest
    if (
        parent.state != "rejected"
        or parent.error_code != "operator_abandoned"
        or parent.run_id == run.run_id
        or parent.request_key == run.request_key
        or (
            parent.source_id,
            parent.actor,
            parent.kind,
            parent.slot_id,
            parent.request_fingerprint,
        )
        != (run.source_id, run.actor, run.kind, run.slot_id, run.request_fingerprint)
        or run.kind != "raw"
        or not run.slot_id.startswith(
            ("content_raw_slot_v1:", "content_binding_slot_v1:")
        )
        or (parent.manifest and manifest and parent.manifest != manifest)
    ):
        raise Conflict("retry contradicts abandoned attempt")
    return parent


class ContentStore:
    def __init__(self, root, *, read_only=True):
        self._artifacts = _Artifacts(root)
        self.root = self._artifacts.root
        self.read_only = read_only
        with self._maintenance(), self._connection() as db:
            self._purpose = db.execute(
                "SELECT purpose FROM metadata WHERE id=1"
            ).fetchone()[0]

    @classmethod
    def initialize(cls, root):
        return cls._initialize(root, purpose="content")

    @classmethod
    def _initialize(cls, root, *, purpose):
        if purpose not in {"content", "synthetic_test"}:
            raise InvalidInput("store purpose")
        try:
            artifacts = create_layout(root)
            with artifacts.lock(".content-maintenance.lock", exclusive=True):
                with artifacts.directory() as directory:
                    fd = os.open(
                        "content.sqlite3",
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=directory,
                    )
                    os.close(fd)
                    _sync(directory)
                db = sqlite3.connect(artifacts.root / "content.sqlite3", timeout=2)
                try:
                    db.execute("PRAGMA foreign_keys=ON")
                    db.execute("PRAGMA journal_mode=WAL")
                    db.execute("PRAGMA synchronous=FULL")
                    db.execute("BEGIN IMMEDIATE")
                    for ddl in schema.expected_schema().values():
                        db.execute(ddl)
                    db.execute(
                        "INSERT INTO metadata VALUES (1,'content-v1',?,0,0)", (purpose,)
                    )
                    db.execute(f"PRAGMA application_id={schema.APPLICATION_ID}")
                    db.execute(f"PRAGMA user_version={schema.VERSION}")
                    db.commit()
                    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                finally:
                    db.close()
                with artifacts.directory() as directory:
                    _sync(directory)
            return cls(root, read_only=False)
        except ContentStoreError:
            raise
        except (OSError, sqlite3.Error):
            raise Unavailable("content initialization failed") from None

    @contextmanager
    def _maintenance(self):
        try:
            with self._artifacts.lock(".content-maintenance.lock"):
                yield
        except OSError:
            raise Unavailable("content filesystem operation failed") from None

    def _database_file(self):
        with self._artifacts.directory() as directory:
            if ".content-recovery-required" in os.listdir(directory):
                raise Unavailable("explicit database recovery required")
            fd = os.open("content.sqlite3", FILE_FLAGS, dir_fd=directory)
            try:
                info = _private(fd)
                if info.st_size == 0:
                    raise Unavailable("uninitialized content database")
            finally:
                os.close(fd)
            for suffix in ("-wal", "-shm", "-journal"):
                try:
                    fd = os.open(
                        "content.sqlite3" + suffix, FILE_FLAGS, dir_fd=directory
                    )
                except FileNotFoundError:
                    continue
                try:
                    sidecar = _private(fd)
                    if suffix in {"-wal", "-journal"} and sidecar.st_size:
                        raise Unavailable(
                            "uncheckpointed database requires explicit recovery"
                        )
                finally:
                    os.close(fd)

    @staticmethod
    def _validate(db):
        if (
            db.execute("PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != schema.VERSION
        ):
            raise Unavailable("unknown content schema identity or version")
        actual = {
            (row[0], row[1]): row[2]
            for row in db.execute(
                "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            )
        }
        if actual != schema.expected_schema():
            raise Unavailable("content schema layout mismatch")
        meta = db.execute("SELECT * FROM metadata WHERE id=1").fetchone()
        if (
            meta is None
            or meta["identity"] != "content-v1"
            or meta["purpose"] not in {"content", "synthetic_test"}
        ):
            raise Unavailable("content metadata mismatch")
        if (
            db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
            or db.execute("PRAGMA foreign_key_check").fetchone() is not None
        ):
            raise IntegrityError("database integrity check failed")

    @contextmanager
    def _connection(self, *, write=False):
        if write and self.read_only:
            raise Forbidden("read-only content handle")
        db = None
        try:
            with self._artifacts.lock(".content-db.lock", exclusive=write):
                self._database_file()
                uri = (self.root / "content.sqlite3").as_uri() + (
                    "?mode=rw" if write else "?mode=ro&immutable=1"
                )
                db = sqlite3.connect(uri, uri=True, timeout=2)
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA synchronous=FULL")
                self._validate(db)
                db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                try:
                    yield db
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
                finally:
                    if write:
                        # immutable readers must never ignore an outstanding WAL.
                        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    db.close()
                    db = None
        except sqlite3.IntegrityError:
            raise IntegrityError("database constraint rejected operation") from None
        except sqlite3.OperationalError as error:
            if getattr(error, "sqlite_errorcode", None) in {
                sqlite3.SQLITE_BUSY,
                sqlite3.SQLITE_LOCKED,
            }:
                raise Busy("database write contention") from None
            raise Unavailable("database operation failed") from None
        except sqlite3.Error:
            raise Unavailable("database cannot be read") from None
        except OSError:
            raise Unavailable("database filesystem operation failed") from None
        except (ValidationError, json.JSONDecodeError):
            raise IntegrityError("stored content model invalid") from None
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def _sequence(db):
        db.execute(
            "UPDATE metadata SET publication_seq=publication_seq+1,collection_revision=collection_revision+1 WHERE id=1"
        )
        return db.execute("SELECT publication_seq FROM metadata WHERE id=1").fetchone()[
            0
        ]

    @staticmethod
    def _authorize(db, source_id, actor, *, write=False):
        actor = checked_actor(actor)
        row = db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if row is None:
            raise NotFound("source unavailable")
        allowed = row["owner"] == actor.subject
        if not write and not allowed:
            allowed = (
                db.execute(
                    "SELECT 1 FROM source_grants WHERE source_id=? AND subject=? AND permission='read'",
                    (source_id, actor.subject),
                ).fetchone()
                is not None
            )
        if (
            row["state"] != "registered"
            or row["course_id"] not in actor.courses
            or not allowed
            or (write and actor.role != "operator")
        ):
            raise Forbidden("source scope denied")
        return Source.model_validate_json(row["data"]).model_copy(
            update={"state": row["state"], "acl_revision": row["acl_revision"]}
        )

    def register_source(self, source: SourceRegistration, *, actor):
        actor = checked_actor(actor)
        if not isinstance(source, SourceRegistration):
            raise InvalidInput("typed source registration required")
        source = snapshot(source)
        if actor.role != "operator" or source.course_id not in actor.courses:
            raise Forbidden("source registration scope denied")
        with self._maintenance(), self._connection(write=True) as db:
            existing = db.execute(
                "SELECT id FROM sources WHERE namespace=? AND external_id=?",
                (source.identity_namespace, source.external_identity),
            ).fetchone()
            if existing:
                current = self._authorize(db, existing["id"], actor, write=True)
                if current.registration != source:
                    raise Conflict("source identity already registered differently")
                return current
            if db.execute(
                "SELECT 1 FROM sources WHERE id=?", (source.resolved_id,)
            ).fetchone():
                raise Conflict("source ID collision")
            from src.content_store.limits import MAX_FILES

            if db.execute("SELECT count(*) FROM sources").fetchone()[0] >= MAX_FILES:
                raise Unavailable("content source capacity exceeded")
            result = Source(
                source_id=source.resolved_id,
                registration=source,
                owner_subject=actor.subject,
                publication_seq=self._sequence(db),
            )
            db.execute(
                "INSERT INTO sources VALUES (?,?,?,?,?,?,0,'registered',?)",
                (
                    result.source_id,
                    source.identity_namespace,
                    source.external_identity,
                    source.course_id,
                    actor.subject,
                    _encoded(result),
                    result.publication_seq,
                ),
            )
            return result

    def get_source(self, source_id, *, actor):
        with self._maintenance(), self._connection() as db:
            source = self._authorize(db, source_id, actor)
            return SourceView(
                source_id=source.source_id,
                course_id=source.registration.course_id,
                source_type=source.registration.source_type,
                source_origin=source.registration.source_origin,
                acl_revision=source.acl_revision,
            )

    @staticmethod
    def _page_limit(cursor, limit):
        if cursor is not None:
            raise Unavailable("signed pagination deferred to C23-04")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidInput("page limit")

    def list_sources(self, *, actor, course_id=None, cursor=None, limit=50):
        actor = checked_actor(actor)
        self._page_limit(cursor, limit)
        courses = tuple(c for c in actor.courses if course_id is None or c == course_id)
        if not courses:
            return ()
        placeholders = ",".join("?" for _ in courses)
        with self._maintenance(), self._connection() as db:
            rows = db.execute(
                "SELECT s.id FROM sources s WHERE s.state='registered' AND s.course_id IN ("
                + placeholders
                + ") "
                "AND (s.owner=? OR EXISTS (SELECT 1 FROM source_grants g WHERE g.source_id=s.id AND g.subject=? AND g.permission='read')) ORDER BY s.id LIMIT ?",
                (*courses, actor.subject, actor.subject, limit + 1),
            ).fetchall()
            if len(rows) > limit:
                raise Unavailable("complete source page requires later pagination")
            result = []
            for row in rows:
                source = self._authorize(db, row[0], actor)
                result.append(
                    SourceView(
                        source_id=source.source_id,
                        course_id=source.registration.course_id,
                        source_type=source.registration.source_type,
                        source_origin=source.registration.source_origin,
                        acl_revision=source.acl_revision,
                    )
                )
            return tuple(result)

    def list_source_versions(self, source_id, *, actor, cursor=None, limit=50):
        self._page_limit(cursor, limit)
        with self._maintenance(), self._connection() as db:
            self._authorize(db, source_id, actor)
            rows = db.execute(
                "SELECT data FROM source_versions WHERE source_id=? AND state='verified' ORDER BY id LIMIT ?",
                (source_id, limit + 1),
            ).fetchall()
            if len(rows) > limit:
                raise Unavailable("complete version page requires later pagination")
            return tuple(SourceVersion.model_validate_json(row[0]) for row in rows)

    def set_source_grants(self, source_id, grants, *, expected_acl_revision, actor):
        if (
            not isinstance(grants, tuple)
            or len(grants) > 1000
            or any(not isinstance(g, SourceGrant) for g in grants)
            or len({g.subject for g in grants}) != len(grants)
        ):
            raise InvalidInput("typed unique source grants required")
        with self._maintenance(), self._connection(write=True) as db:
            source = self._authorize(db, source_id, actor, write=True)
            if expected_acl_revision != source.acl_revision:
                raise Conflict("ACL revision changed")
            db.execute("DELETE FROM source_grants WHERE source_id=?", (source_id,))
            db.executemany(
                "INSERT INTO source_grants VALUES (?,?,'read')",
                [(source_id, g.subject) for g in grants],
            )
            db.execute(
                "UPDATE sources SET acl_revision=acl_revision+1 WHERE id=?",
                (source_id,),
            )
            db.execute(
                "UPDATE metadata SET collection_revision=collection_revision+1 WHERE id=1"
            )
            return source.model_copy(update={"acl_revision": source.acl_revision + 1})

    def _reserve(
        self,
        source_id,
        actor,
        *,
        kind,
        slot_id,
        request_key,
        request_fingerprint,
        retry=None,
        retry_manifest=None,
    ):
        with self._connection(write=True) as db:
            source = self._authorize(db, source_id, actor, write=True)
            retry_of = None
            if retry is not None:
                if type(retry) is not RetryAttempt:
                    raise InvalidInput("typed v1 retry attempt required")
                try:
                    retry = snapshot(retry)
                except ValidationError:
                    raise InvalidInput("invalid retry attempt") from None
                retry_of = retry.rejected_run_id
                request_key = retry.request_key
                parent = _retry_parent(
                    db,
                    ProcessingRun(
                        run_id=uuid.uuid4().hex,
                        source_id=source_id,
                        actor=actor.subject,
                        kind=kind,
                        slot_id=slot_id,
                        request_key=request_key,
                        request_fingerprint=request_fingerprint,
                        acl_revision=source.acl_revision,
                        state="preparing",
                        retry_of=retry_of,
                    ),
                    manifest=retry_manifest,
                )
                if parent.recovery is not None:
                    self._read_blob(parent.recovery, db)
            old = db.execute(
                "SELECT data FROM processing_runs WHERE actor=? AND request_key=?",
                (actor.subject, request_key),
            ).fetchone()
            if old:
                run = ProcessingRun.model_validate_json(old[0])
                if (
                    run.request_fingerprint != request_fingerprint
                    or run.source_id != source_id
                    or run.slot_id != slot_id
                    or run.kind != kind
                    or run.retry_of != retry_of
                ):
                    raise Conflict("request key already bound")
                if run.state != "committed":
                    raise Unavailable("incomplete run requires explicit recovery")
                return run
            if db.execute(
                "SELECT 1 FROM processing_runs WHERE slot_id=? AND state IN ('preparing','prepared','blocked')",
                (slot_id,),
            ).fetchone():
                raise Busy("import slot reserved; recovery required")
            from src.content_store.limits import MAX_ACTIVE_RUNS

            if (
                db.execute(
                    "SELECT count(*) FROM processing_runs WHERE state IN ('preparing','prepared','blocked')"
                ).fetchone()[0]
                >= MAX_ACTIVE_RUNS
            ):
                raise Busy("active run limit requires explicit recovery")
            from src.content_store.limits import MAX_METADATA_ROWS

            rows = sum(
                db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
                for table in schema.TABLES
            )
            if rows > MAX_METADATA_ROWS:
                raise Unavailable("content metadata capacity exceeded")
            run = ProcessingRun(
                run_id=uuid.uuid4().hex,
                source_id=source_id,
                actor=actor.subject,
                kind=kind,
                slot_id=slot_id,
                request_key=request_key,
                request_fingerprint=request_fingerprint,
                acl_revision=source.acl_revision,
                state="preparing",
                retry_of=retry_of,
            )
            self._artifacts.create_run_lock(run.run_id)
            db.execute(
                "INSERT INTO processing_runs VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    run.run_id,
                    source_id,
                    actor.subject,
                    request_key,
                    request_fingerprint,
                    slot_id,
                    kind,
                    run.state,
                    _encoded(run),
                ),
            )
            return run

    @staticmethod
    def _update_run(db, run, **updates):
        row = db.execute(
            "SELECT data FROM processing_runs WHERE id=?", (run.run_id,)
        ).fetchone()
        current = ProcessingRun.model_validate_json(row[0]) if row else run
        run = current.model_copy(update=updates)
        db.execute(
            "UPDATE processing_runs SET state=?,data=? WHERE id=?",
            (run.state, _encoded(run), run.run_id),
        )
        return run

    @contextmanager
    def _running(self, run):
        with self._artifacts.lock(f"locks/{run.run_id}.lock", exclusive=True):
            try:
                yield
            except BaseException as error:
                # Never resume automatically; preserve staged bytes and committed manifest.
                try:
                    with self._connection(write=True) as db:
                        row = db.execute(
                            "SELECT data FROM processing_runs WHERE id=?", (run.run_id,)
                        ).fetchone()
                        current = ProcessingRun.model_validate_json(row[0])
                        if current.state != "committed":
                            self._update_run(
                                db,
                                current,
                                state="rejected"
                                if isinstance(error, Conflict)
                                else "blocked",
                                error_code=error.code
                                if isinstance(error, ContentStoreError)
                                else "operation_failed",
                            )
                except ContentStoreError:
                    pass  # Original preparation remains durable if the disk is unavailable.
                if isinstance(error, OSError):
                    raise Unavailable("artifact write failed; run blocked") from None
                raise

    def _prepared(self, run, references, actor):
        with self._connection(write=True) as db:
            source = self._authorize(db, run.source_id, actor, write=True)
            if source.acl_revision != run.acl_revision:
                raise Forbidden("source permissions changed during import")
            self._update_run(db, run, state="prepared", manifest=references)

    def _record_blob(self, db, reference):
        old = db.execute(
            "SELECT size_bytes,state FROM artifacts WHERE sha256=?", (reference.sha256,)
        ).fetchone()
        if old:
            if old[0] != reference.size_bytes or old[1] != "available":
                raise IntegrityError("blob metadata conflict")
        else:
            from src.content_store.limits import MAX_FILES, MAX_STORE_BYTES

            count, size = db.execute(
                "SELECT count(*),coalesce(sum(size_bytes),0) FROM artifacts"
            ).fetchone()
            if count >= MAX_FILES or size + reference.size_bytes > MAX_STORE_BYTES:
                raise Unavailable("content artifact catalog capacity exceeded")
            db.execute(
                "INSERT INTO artifacts VALUES (?,?,'available')",
                (reference.sha256, reference.size_bytes),
            )

    def store_raw_artifact(
        self,
        source_id,
        stream,
        *,
        expected_sha256,
        expected_size,
        mime_type,
        actor,
        retry: RetryAttempt | None = None,
    ):
        actor = checked_actor(actor)
        try:
            ref = ArtifactReference(
                sha256=expected_sha256, size_bytes=expected_size, mime_type=mime_type
            )
        except ValidationError:
            raise InvalidInput("invalid raw artifact declaration") from None
        with self._maintenance():
            with self._connection() as db:
                self._authorize(db, source_id, actor, write=True)
            slot = deterministic_id("content_raw_slot_v1", source_id, ref.sha256)
            run = self._reserve(
                source_id,
                actor,
                kind="raw",
                slot_id=slot,
                request_key=slot,
                request_fingerprint=fingerprint(ref.model_dump(mode="json")),
                retry=retry,
                retry_manifest=(ref,),
            )
            if run.state == "committed":
                # Reimports validate supplied bytes too, not only the existing blob.
                data = bytearray()
                while True:
                    block = stream.read(min(65536, ref.size_bytes - len(data) + 1))
                    if not isinstance(block, bytes):
                        raise InvalidInput("binary stream required")
                    if not block:
                        break
                    data.extend(block)
                    if len(data) > ref.size_bytes:
                        raise IntegrityError("raw reimport size mismatch")
                if len(data) != ref.size_bytes or sha256(data) != ref.sha256:
                    raise IntegrityError("raw reimport bytes mismatch")
                self._read_blob(ref)
                return ref
            with self._running(run):
                self._artifacts.stage(run.run_id, stream, ref)
                from src.content_store.operations import record_intent
                from src.content_store.operations_models import RawIntent

                record_intent(
                    self, run, RawIntent(run_id=run.run_id, reference=ref), actor
                )
                self._prepared(run, (ref,), actor)
                self._artifacts.install(run.run_id, ref)
                with self._connection(write=True) as db:
                    self._commit_raw(db, run, ref, actor)

                return ref

    def _commit_raw(self, db, run, ref, actor):
        current = self._authorize(db, run.source_id, actor, write=True)
        if current.acl_revision != run.acl_revision:
            raise Forbidden("source permissions changed during import")
        self._record_blob(db, ref)
        old = db.execute(
            "SELECT data FROM raw_reservations WHERE source_id=? AND sha256=?",
            (run.source_id, ref.sha256),
        ).fetchone()
        if old:
            if ArtifactReference.model_validate_json(old[0]) != ref:
                raise Conflict("raw reservation metadata conflict")
            self._read_blob(ref, db)
        else:
            db.execute(
                "INSERT INTO raw_reservations VALUES (?,?,?,?)",
                (run.source_id, ref.sha256, run.run_id, _encoded(ref)),
            )
        self._update_run(db, run, state="committed", manifest=(ref,))

    def register_source_version(
        self,
        source_id,
        manifest,
        *,
        variant_key,
        binding,
        actor,
        retry: RetryAttempt | None = None,
    ):
        if self.read_only:
            raise Forbidden("read-only content handle")
        from src.content_store.publication import register

        with self._maintenance():
            with self._connection() as db:
                self._authorize(db, source_id, actor, write=True)
            return register(
                self,
                source_id,
                manifest,
                variant_key=variant_key,
                binding=binding,
                actor=actor,
                retry=retry,
            )

    def publish_parsed_document(
        self, source_version_id, candidate, *, actor, request_key, job_ref=None
    ):
        checked_actor(actor)
        if self.read_only:
            raise Forbidden("read-only content handle")
        from src.content_store.adapters import VerifiedPublicationCandidate
        from src.content_store.publication import publish

        if type(candidate) is not VerifiedPublicationCandidate:
            raise Unavailable("verified bundle publication candidate required")
        if job_ref is not None:
            raise InvalidInput("job linkage is not supported by content adapters")
        with self._maintenance():
            return publish(
                self, source_version_id, candidate, actor=actor, request_key=request_key
            )

    def read_version_artifact(
        self, parsed_version_id, role, *, actor, request_key=None
    ):
        from src.content_store.publication import read_artifact

        return read_artifact(
            self, parsed_version_id, role, actor=actor, request_key=request_key
        )

    def inspect_recovery(self, *, actor):
        from src.content_store.operations import inspect_recovery

        return inspect_recovery(self, actor=actor)

    def recover_run(self, run_id, *, actor, action="resume"):
        from src.content_store.operations import recover_run

        return recover_run(self, run_id, actor=actor, action=action)

    @classmethod
    def recover_database(cls, root, *, actor):
        from src.content_store.operations import recover_database

        return recover_database(root, actor=actor)

    def verify_integrity(self, *, actor):
        from src.content_store.operations import verify_integrity

        return verify_integrity(self, actor=actor)

    def _read_blob(self, reference, db=None):
        if db is None:
            with self._connection() as connection:
                return self._read_blob(reference, connection)
        row = db.execute(
            "SELECT size_bytes,state FROM artifacts WHERE sha256=?", (reference.sha256,)
        ).fetchone()
        if row is None or row[0] != reference.size_bytes or row[1] != "available":
            raise IntegrityError("artifact catalog unavailable or quarantined")
        try:
            return self._artifacts.read(reference)
        except (OSError, IntegrityError):
            # No byte replacement, path fallback, reparse or read-time DB mutation.
            raise IntegrityError("referenced artifact unavailable or corrupt") from None

    def read_raw_artifact(self, source_id, sha256_value, *, actor):
        with self._maintenance(), self._connection() as db:
            self._authorize(db, source_id, actor)
            row = db.execute(
                "SELECT data FROM raw_reservations WHERE source_id=? AND sha256=?",
                (source_id, sha256_value),
            ).fetchone()
            if row is None:
                raise NotFound("source artifact unavailable")
            reference = ArtifactReference.model_validate_json(row[0])
            return self._read_blob(reference, db)

    def _parsed(self, db, version_id, actor):
        row = db.execute(
            "SELECT * FROM parsed_versions WHERE id=? AND state='published'",
            (version_id,),
        ).fetchone()
        if row is None:
            raise NotFound("parsed version unavailable")
        self._authorize(db, row["source_id"], actor)
        version = ParsedDocumentVersion.model_validate_json(row["data"])
        source_version = db.execute(
            "SELECT state,data FROM source_versions WHERE id=?",
            (version.source_version_id,),
        ).fetchone()
        if source_version is None or source_version[0] != "verified":
            raise IntegrityError("source version unavailable or quarantined")
        self._read_blob(version.payload, db)
        self._read_blob(version.projection, db)
        if version.quality_status != "synthetic_test_only":
            original = SourceVersion.model_validate_json(source_version[1])
            for ref in original.manifest.artifacts:
                self._read_blob(ref, db)
            binding = db.execute(
                "SELECT size_bytes FROM artifacts WHERE sha256=?",
                (original.binding_sha256,),
            ).fetchone()
            if binding is None:
                raise IntegrityError("source binding artifact unavailable")
            self._read_blob(
                ArtifactReference(
                    sha256=original.binding_sha256,
                    size_bytes=binding[0],
                    mime_type="application/json",
                ),
                db,
            )
        return version

    def get_parsed_document(self, parsed_version_id, *, actor):
        with self._maintenance(), self._connection() as db:
            version = self._parsed(db, parsed_version_id, actor)
            return ParsedDocumentView(
                parsed_version_id=version.parsed_version_id,
                source_id=version.source_id,
                source_version_id=version.source_version_id,
                parser_config_id=version.parser_config_id,
                payload_sha256=version.payload.sha256,
                projection_sha256=version.projection.sha256,
                quality_status=version.quality_status,
            )

    def read_parsed_payload(self, parsed_version_id, *, actor):
        with self._maintenance(), self._connection() as db:
            version = self._parsed(db, parsed_version_id, actor)
            return self._read_blob(version.payload, db)

    def list_content_blocks(self, parsed_version_id, *, actor, cursor=None, limit=50):
        if cursor is not None:
            raise Unavailable("signed pagination deferred to C23-04")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidInput("block page limit")
        with self._maintenance(), self._connection() as db:
            self._parsed(db, parsed_version_id, actor)
            rows = db.execute(
                "SELECT data FROM content_blocks WHERE version_id=? ORDER BY block_order LIMIT ?",
                (parsed_version_id, limit + 1),
            ).fetchall()
            if len(rows) > limit:
                raise Unavailable("complete block page requires later pagination")
            return BlockPage(
                items=tuple(ContentBlock.model_validate_json(row[0]) for row in rows)
            )

    def project_content_for_index(self, parsed_version_id, *, actor, config=None):
        """Scoped read-only projection; no index build or lasting read authorization."""
        from src.content_store.index_projection import project_content_for_index

        return project_content_for_index(
            self, parsed_version_id, actor=actor, config=config
        )
