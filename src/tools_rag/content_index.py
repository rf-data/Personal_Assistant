"""Explicit private FTS generations and live-authorized lexical retrieval."""

import base64
import hashlib
import hmac
import os
import re
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from src.content_store.artifacts import explicit_root
from src.content_store.errors import (
    Busy,
    ContentStoreError,
    Forbidden,
    IntegrityError,
    InvalidInput,
    NotFound,
    Unavailable,
)
from src.content_store.index_models import record_set_sha256
from src.content_store.index_projection import _project_locked
from src.content_store.limits import directory_entries
from src.content_store.models import (
    ContentBlock,
    SourceVersion,
    canonical,
    checked_actor,
    fingerprint,
    sha256,
    snapshot,
)
from src.content_store.read_models import TextWindow
from src.content_store.read_views import locators, route
from src.content_store.reader import private_bytes
from src.content_store.store import ContentStore
from src.model_course import ContentCourseId as CourseId
from src.model_discovery.cs50 import deterministic_id
from src.tools_materials.quality import _json
from src.tools_rag import content_fts
from src.tools_rag.content_index_files import IndexFiles, initialize_root
from src.tools_rag.content_index_models import (
    ActiveGeneration,
    BuildReceipt,
    FileProof,
    GenerationBasis,
    GenerationManifest,
    IndexSelection,
    RecordAnchor,
    ScoreComponent,
    SearchCursor,
    SearchHit,
    SearchResultPage,
    VersionBinding,
)

MAX_IO = 128 * 1024**2
MAX_MATCHES = 1000
MAX_INDEX_BYTES = 1024**3
MAX_ROOT_BYTES = 2 * 1024**3
MAX_ROOT_FILES = 20000
MAX_RECORDS = 200000
QUERY_SECONDS = 2.0
BUILD_SECONDS = 900.0
SLOTS = threading.BoundedSemaphore(2)


class RetrievalFault(ContentStoreError):
    def __init__(self, reason):
        if reason not in {
            "invalid_parameter",
            "invalid_cursor",
            "snapshot_changed",
            "scope_required",
            "query_too_broad",
            "stale_index",
        }:
            raise ValueError("unknown retrieval fault")
        self.code = reason
        super().__init__("request rejected")


def _utc():
    return datetime.now(UTC).isoformat()


def _meta(db):
    return tuple(
        db.execute(
            "SELECT publication_seq,collection_revision FROM metadata WHERE id=1"
        ).fetchone()
    )


def _version_binding(result):
    b = result.body
    return VersionBinding(
        source_id=b.source_id,
        source_version_id=b.source_version_id,
        parsed_version_id=b.parsed_version_id,
        parser_config_id=b.parser_config_id,
        payload_sha256=b.payload_sha256,
        projection_sha256=b.projection_sha256,
    )


def _gen_path(pointer):
    return "generations/" + pointer.generation_id.split(":")[1] + "/" + pointer.build_id


def _manifest_digest(manifest):
    return fingerprint(manifest.model_dump(mode="json", exclude={"digest"}))


def _versioned(data):
    value = _json(data)
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
    ):
        raise Unavailable("index schema unavailable")
    return value


class ContentIndex:
    IDENTITY = "content-fts5-v1"
    METHOD = "lexical"
    RANKING = "source_rrf_v1"
    CURSOR_DOMAIN = b"lexical-cursor-v1\0"

    def _backend_spec(self):
        return content_fts.backend_spec()

    def _partition_name(self, source_id):
        return "source-" + fingerprint(source_id) + ".sqlite3"

    def _build_partition(self, records, *, source_id, generation_id, deadline):
        return content_fts.build_database(records, deadline=deadline)

    def _verify_partition(self, data, records, deadline, *, source_id, generation_id):
        content_fts.search_database(
            data, records, '"__verification_no_match__"', None, deadline
        )

    def _query_value(self, query, match):
        return match

    def _search_partition(
        self, data, records, query, content_types, deadline, *, source_id, generation_id
    ):
        return content_fts.search_database(
            data, records, query, content_types, deadline
        )

    def _rank_scores(self, hits):
        return [
            (1 / (60 + rank), rid, score) for rank, (rid, score) in enumerate(hits, 1)
        ]

    def _score_component(self, source_id, score):
        return ScoreComponent(source_id=source_id, raw_score=score)

    def __init__(self, store, index_root, *, cursor_key_file, _synthetic=False):
        if not isinstance(store, ContentStore):
            raise InvalidInput("typed ContentStore required")
        self.store = store
        self.synthetic = _synthetic
        self.purpose = "synthetic_test" if _synthetic else "content"
        if store._purpose != self.purpose:
            raise Forbidden("index store purpose denied")
        self.root = explicit_root(index_root)
        if self.root.is_relative_to(store.root) or store.root.is_relative_to(self.root):
            raise InvalidInput("separate index/content roots required")
        self.files = IndexFiles(self.root)
        identity = _versioned(self.files.read("identity.json", maximum=8192))
        if identity != dict(
            schema_version=1, identity=self.IDENTITY, purpose=self.purpose
        ):
            raise Unavailable("index identity/schema unavailable")
        keypath = Path(cursor_key_file)
        repo = Path(__file__).resolve().parents[2]
        if (
            not keypath.is_absolute()
            or ".." in keypath.parts
            or any(keypath.is_relative_to(p) for p in [self.root, store.root, repo])
        ):
            raise InvalidInput("explicit separate private cursor key required")
        self.key = private_bytes(keypath, 64)
        if not 32 <= len(self.key) <= 64:
            raise InvalidInput("cursor key length")
        self._backend_spec()

    @classmethod
    def initialize(cls, store, index_root, *, cursor_key_file, _synthetic=False):
        content_fts.backend_spec()
        if not isinstance(store, ContentStore) or store._purpose != (
            "synthetic_test" if _synthetic else "content"
        ):
            raise Forbidden("index store purpose denied")
        # Validate key BEFORE creating any index data.
        keypath = Path(cursor_key_file)
        if (
            not keypath.is_absolute()
            or ".." in keypath.parts
            or any(
                keypath.is_relative_to(p)
                for p in [
                    Path(index_root),
                    store.root,
                    Path(__file__).resolve().parents[2],
                ]
            )
        ):
            raise InvalidInput("explicit separate private cursor key required")
        if not 32 <= len(private_bytes(keypath, 64)) <= 64:
            raise InvalidInput("cursor key length")
        initialize_root(index_root, store.root, store._purpose)
        return cls(store, index_root, cursor_key_file=keypath, _synthetic=_synthetic)

    def _hmac(self, domain, value):
        return hmac.new(
            self.key, domain.encode() + b"\0" + canonical(value), hashlib.sha256
        ).hexdigest()

    def _active(self):
        raw = self.files.read("active.json", maximum=8192, missing=True)
        if raw is None:
            return None, None, None
        try:
            pointer = ActiveGeneration.model_validate(_versioned(raw))
            data = self.files.read(
                _gen_path(pointer) + "/manifest.json", maximum=8 * 1024**2
            )
            if sha256(data) != pointer.manifest_sha256:
                raise ValueError()
            obj = _versioned(data)
            basis = obj.get("basis")
            if not isinstance(basis, dict):
                raise ValueError()
            for nested in (basis, basis.get("selection")):
                if (
                    not isinstance(nested, dict)
                    or type(nested.get("schema_version")) is not int
                    or nested["schema_version"] != 1
                ):
                    raise ValueError()
            manifest = GenerationManifest.model_validate(obj)
            if (manifest.generation_id, manifest.build_id, manifest.purpose) != (
                pointer.generation_id,
                pointer.build_id,
                self.purpose,
            ):
                raise ValueError()
            if (
                manifest.digest != _manifest_digest(manifest)
                or manifest.generation_id
                != deterministic_id(
                    "content_index_generation_v1",
                    fingerprint(manifest.basis.model_dump(mode="json")),
                )
                or manifest.basis.backend != self._backend_spec()
                or manifest.basis.policy_id != manifest.basis.selection.config.policy_id
            ):
                raise ValueError()
            if len({x.source_id for x in manifest.files}) != len(manifest.files):
                raise ValueError()
            if {x.source_id for x in manifest.files} != {
                v.source_id for v in manifest.basis.versions
            }:
                raise ValueError()
            if (
                tuple(v.parsed_version_id for v in manifest.basis.versions)
                != manifest.basis.selection.parsed_version_ids
            ):
                raise ValueError()
            if any(f.name != self._partition_name(f.source_id) for f in manifest.files):
                raise ValueError()
            if manifest.record_count != sum(f.record_count for f in manifest.files):
                raise ValueError()
            return raw, pointer, manifest
        except (ValueError, TypeError, KeyError, ValidationError):
            raise Unavailable("active index manifest unavailable") from None

    def _capacity(self, needed=0):
        total = count = 0
        # Only own explicit index root; never scan content or personal directories.
        pending = [""]
        while pending:
            rel = pending.pop()
            with self.files.directory(rel) as fd:
                for name in directory_entries(fd, limit=MAX_ROOT_FILES):
                    count += 1
                    if count > MAX_ROOT_FILES:
                        raise Unavailable("index file capacity")
                    stat = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    import stat as mode

                    if mode.S_ISDIR(stat.st_mode):
                        pending.append((rel + "/" if rel else "") + name)
                    elif mode.S_ISREG(stat.st_mode) and stat.st_nlink == 1:
                        total += stat.st_size
                    else:
                        raise IntegrityError("unsafe index inventory")
        with self.files.directory() as fd:
            fs = os.fstatvfs(fd)
            if (
                total + needed > MAX_ROOT_BYTES
                or fs.f_bavail * fs.f_frsize < needed + 1024**2
            ):
                raise Unavailable("index byte capacity")

    def _ownership(self, db, sources, actor):
        if actor.role != "operator":
            raise Forbidden("operator index operation required")
        for sid in sources:
            row = db.execute(
                "SELECT owner,course_id FROM sources WHERE id=?", (sid,)
            ).fetchone()
            if row is None or row[0] != actor.subject or row[1] not in actor.courses:
                raise Forbidden("complete source ownership and scope required")

    def _export(
        self, db, selection, actor, *, owner=False, budget=None, record_budget=None
    ):
        if budget is None:
            budget = [0]
        if record_budget is None:
            record_budget = [0]
        results = []
        records = []
        sources = set()
        acl = {}
        for vid in selection.parsed_version_ids:
            row = db.execute(
                "SELECT source_id FROM parsed_versions WHERE id=?", (vid,)
            ).fetchone()
            if row is None:
                raise NotFound("selected version unavailable")
            if owner:
                self.store._authorize(db, row[0], actor, write=True)
            result = _project_locked(
                self.store,
                db,
                vid,
                actor,
                selection.config,
                synthetic=self.synthetic,
                budget=budget,
            )
            results.append(result)
            for record in result.body.records:
                record_budget[0] += len(canonical(record.model_dump(mode="json")))
                if record_budget[0] > 64 * 1024**2:
                    raise Unavailable("index record byte capacity")
                records.append(record)
            sources.add(result.body.source_id)
            acl[result.body.source_id] = self.store._authorize(
                db, result.body.source_id, actor
            ).acl_revision
            if len(records) > MAX_RECORDS:
                raise Unavailable("index record capacity")
        return results, records, tuple(sorted(sources)), acl

    def _receipt(self, receipt):
        self.files.json(
            "attempts/" + receipt.build_id + "/status.json",
            receipt.model_dump(mode="json"),
            replace=True,
        )

    def build(self, selection, *, actor, build_id=None):
        actor = checked_actor(actor)
        if actor.role != "operator":
            raise Forbidden("operator build required")
        if not isinstance(selection, IndexSelection):
            raise InvalidInput("typed index selection required")
        selection = snapshot(selection)
        started = time.monotonic()
        bid = uuid.uuid4().hex if build_id is None else build_id
        if not isinstance(bid, str) or not re.fullmatch(r"[0-9a-f]{32}", bid):
            raise InvalidInput("build identity")
        with self.files.lock(".content-index-build.lock", exclusive=True):
            if (
                self.files.read("attempts/" + bid + "/status.json", missing=True)
                is not None
            ):
                raise InvalidInput(
                    "build identity already used; explicit new request required"
                )
            self._capacity()
            receipt = BuildReceipt(
                build_id=bid,
                actor=actor.subject,
                source_ids=(),
                selection=selection,
                state="preparing",
                started_at=_utc(),
            )
            self._receipt(receipt)
            try:
                with self.files.lock(".content-index-catalog.lock"):
                    original, _, previous = self._active()
                    with self.store._maintenance(), self.store._connection() as db:
                        if previous is not None:
                            self._ownership(
                                db, tuple(f.source_id for f in previous.files), actor
                            )
                        before = _meta(db)
                        results, records, sources, acl = self._export(
                            db, selection, actor, owner=True
                        )
                basis = GenerationBasis(
                    selection=selection,
                    versions=tuple(_version_binding(r) for r in results),
                    record_set_sha256=record_set_sha256(records),
                    policy_id=selection.config.policy_id,
                    backend=self._backend_spec(),
                )
                gid = deterministic_id(
                    "content_index_generation_v1",
                    fingerprint(basis.model_dump(mode="json")),
                )
                receipt = receipt.model_copy(
                    update=dict(
                        state="building",
                        source_ids=sources,
                        generation_id=gid,
                        snapshot=before,
                        acl_revisions=acl,
                        record_count=len(records),
                        record_set_sha256=basis.record_set_sha256,
                    )
                )
                self._receipt(receipt)
                proofs = []
                total = 0
                for sid in sources:
                    data = self._build_partition(
                        [r for r in records if r.body.source_id == sid],
                        source_id=sid,
                        generation_id=gid,
                        deadline=started + BUILD_SECONDS,
                    )
                    total += len(data)
                    if (
                        total > MAX_INDEX_BYTES
                        or time.monotonic() - started > BUILD_SECONDS
                    ):
                        raise Unavailable("build resource limit")
                    self._capacity(len(data))
                    proof = FileProof(
                        name=self._partition_name(sid),
                        sha256=sha256(data),
                        size_bytes=len(data),
                        source_id=sid,
                        record_count=sum(r.body.source_id == sid for r in records),
                        record_set_sha256=record_set_sha256(
                            [r for r in records if r.body.source_id == sid]
                        ),
                    )
                    self.files.write("staging/" + bid + "/" + proof.name, data)
                    proofs.append(proof)
                receipt = receipt.model_copy(update={"state": "verifying"})
                self._receipt(receipt)
                manifest = GenerationManifest(
                    generation_id=gid,
                    build_id=bid,
                    purpose=self.purpose,
                    basis=basis,
                    files=tuple(proofs),
                    record_count=len(records),
                    digest="0" * 64,
                )
                manifest = manifest.model_copy(
                    update={"digest": _manifest_digest(manifest)}
                )
                # Reopen the actual staged bytes, verify metadata, FTS and hashes before publishing.
                for proof in proofs:
                    data = self.files.read("staging/" + bid + "/" + proof.name)
                    if len(data) != proof.size_bytes or sha256(data) != proof.sha256:
                        raise IntegrityError("staged index bytes")
                    self._verify_partition(
                        data,
                        [r for r in records if r.body.source_id == proof.source_id],
                        started + BUILD_SECONDS,
                        source_id=proof.source_id,
                        generation_id=gid,
                    )
                raw_manifest = canonical(manifest.model_dump(mode="json"))
                self.files.write("staging/" + bid + "/manifest.json", raw_manifest)
                receipt = receipt.model_copy(update={"state": "ready"})
                self._receipt(receipt)
                with self.files.lock(".content-index-catalog.lock", exclusive=True):
                    current, _, previous = self._active()
                    if current != original:
                        raise Unavailable("index activation conflict")
                    with self.store._maintenance(), self.store._connection() as db:
                        if previous is not None:
                            self._ownership(
                                db, tuple(f.source_id for f in previous.files), actor
                            )
                        if _meta(db) != before:
                            raise Unavailable("content snapshot changed during build")
                        _, fresh, _, _ = self._export(db, selection, actor, owner=True)
                        if record_set_sha256(fresh) != basis.record_set_sha256:
                            raise IntegrityError("build projection changed")
                        if time.monotonic() - started > BUILD_SECONDS:
                            raise Unavailable("build deadline")
                        self.files.publish(bid, gid)
                        pointer = ActiveGeneration(
                            generation_id=gid,
                            build_id=bid,
                            manifest_sha256=sha256(raw_manifest),
                        )
                        self.files.json(
                            "active.json", pointer.model_dump(mode="json"), replace=True
                        )
                receipt = receipt.model_copy(
                    update={"state": "active", "finished_at": _utc()}
                )
                self._receipt(receipt)
                return receipt
            except BaseException:
                # A response loss after active swap may leave a complete active generation.
                active = self.files.read("active.json", maximum=8192, missing=True)
                committed = bool(active and _json(active).get("build_id") == bid)
                receipt = receipt.model_copy(
                    update={
                        "state": "active" if committed else "failed",
                        "error_code": "build_interrupted",
                        "finished_at": _utc(),
                    }
                )
                try:
                    self._receipt(receipt)
                except (OSError, ContentStoreError):
                    pass
                raise

    def inspect_builds(self, *, actor):
        actor = checked_actor(actor)
        with (
            self.files.lock(".content-index-build.lock", exclusive=True),
            self.files.lock(".content-index-catalog.lock"),
        ):
            _, active, _ = self._active()
            items = []
            try:
                with self.files.directory("attempts") as fd:
                    names = tuple(directory_entries(fd, limit=MAX_ROOT_FILES))
            except FileNotFoundError:
                return ()
            with self.store._maintenance(), self.store._connection() as db:
                for bid in sorted(names):
                    if not re.fullmatch("[0-9a-f]{32}", bid):
                        raise IntegrityError("attempt inventory")
                    receipt = BuildReceipt.model_validate(
                        _versioned(self.files.read("attempts/" + bid + "/status.json"))
                    )
                    if receipt.actor != actor.subject:
                        continue
                    self._ownership(db, receipt.source_ids, actor)
                    if active and active.build_id == bid:
                        receipt = receipt.model_copy(update={"state": "active"})
                    elif receipt.state in {
                        "preparing",
                        "building",
                        "verifying",
                        "ready",
                    }:
                        receipt = receipt.model_copy(update={"state": "interrupted"})
                    elif receipt.state == "active":
                        receipt = receipt.model_copy(update={"state": "retired"})
                    items.append(receipt)
            return tuple(items)

    def discard_build(self, build_id, *, actor):
        actor = checked_actor(actor)
        if not re.fullmatch("[0-9a-f]{32}", build_id):
            raise InvalidInput("build identity")
        with (
            self.files.lock(".content-index-build.lock", exclusive=True),
            self.files.lock(".content-index-catalog.lock", exclusive=True),
        ):
            _, active, _ = self._active()
            if active and active.build_id == build_id:
                raise InvalidInput("active generation cannot be removed")
            receipt = BuildReceipt.model_validate(
                _versioned(self.files.read("attempts/" + build_id + "/status.json"))
            )
            if receipt.actor != actor.subject:
                raise Forbidden("attempt ownership denied")
            with self.store._maintenance(), self.store._connection() as db:
                self._ownership(db, receipt.source_ids, actor)
            if receipt.generation_id:
                relative = (
                    "generations/"
                    + receipt.generation_id.split(":")[1]
                    + "/"
                    + build_id
                )
                try:
                    with self.files.directory(relative):
                        exists = True
                except FileNotFoundError:
                    exists = False
            else:
                exists = False
            relative = relative if exists else "staging/" + build_id
            try:
                with self.files.directory(relative) as fd:
                    names = tuple(directory_entries(fd, limit=129))
                if any(
                    not re.fullmatch(
                        r"(?:source-[0-9a-f]{64}\.(?:sqlite3|vectors\.json)|manifest\.json)",
                        n,
                    )
                    for n in names
                ):
                    raise IntegrityError("unexpected derivative files")
                self.files.remove_directory(relative, names)
            except FileNotFoundError:
                pass
            self._receipt(receipt.model_copy(update={"state": "discarded"}))

    def _cursor_encode(self, value):
        data = canonical(value.model_dump(mode="json"))
        sig = hmac.digest(self.key, self.CURSOR_DOMAIN + data, "sha256")
        return base64.urlsafe_b64encode(data + sig).decode().rstrip("=")

    def _cursor_decode(self, value):
        try:
            if not isinstance(value, str) or not re.fullmatch(
                "[A-Za-z0-9_-]{20,1600}", value
            ):
                raise ValueError()
            data = base64.b64decode(
                value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
            )
            raw, sig = data[:-32], data[-32:]
            if not hmac.compare_digest(
                sig, hmac.digest(self.key, self.CURSOR_DOMAIN + raw, "sha256")
            ):
                raise ValueError()
            cursor = SearchCursor.model_validate(_versioned(raw))
            if self._cursor_encode(cursor) != value or cursor.expires < int(
                time.time()
            ):
                raise ValueError()
            return cursor
        except (ValueError, TypeError, ValidationError, Unavailable):
            raise RetrievalFault("invalid_cursor") from None

    @contextmanager
    def search_lexical(
        self,
        query,
        *,
        actor,
        course_id=None,
        source_ids=None,
        content_types=None,
        limit=20,
        cursor=None,
    ):
        actor = checked_actor(actor)
        try:
            query_bytes = len(query.encode("utf-8")) if isinstance(query, str) else 0
        except UnicodeError:
            raise RetrievalFault("invalid_parameter") from None
        if (
            not isinstance(query, str)
            or not query.strip()
            or len(query) > 512
            or query_bytes > 2048
            or type(limit) is not int
            or not 1 <= limit <= 100
            or course_id is not None
            and course_id not in CourseId.__args__
        ):
            raise RetrievalFault("invalid_parameter")
        terms = query.split()
        if len(terms) > 8 or any(len(t) > 64 for t in terms):
            raise RetrievalFault("invalid_parameter")
        for values, maximum in [(source_ids, 32), (content_types, 9)]:
            if values is not None and (
                not isinstance(values, tuple)
                or not 1 <= len(values) <= maximum
                or any(not isinstance(x, str) or not x or len(x) > 200 for x in values)
                or len(values) != len(set(values))
            ):
                raise RetrievalFault("invalid_parameter")
            if values:
                try:
                    for value in values:
                        value.encode("utf-8")
                except UnicodeError:
                    raise RetrievalFault("invalid_parameter") from None
        allowed_types = {
            "heading",
            "paragraph",
            "code",
            "table",
            "formula",
            "list",
            "link",
            "image_reference",
            "unknown_block",
        }
        if content_types and not set(content_types) <= allowed_types:
            raise RetrievalFault("invalid_parameter")
        match = " AND ".join('"' + term.replace('"', '""') + '"' for term in terms)
        actor_fp = fingerprint(
            dict(subject=actor.subject, role=actor.role, courses=sorted(actor.courses))
        )
        request_fp = fingerprint(
            dict(
                query=query,
                course_id=course_id,
                source_ids=sorted(source_ids) if source_ids else None,
                content_types=sorted(content_types) if content_types else None,
                limit=limit,
                method=self.METHOD,
            )
        )
        decoded = self._cursor_decode(cursor) if cursor is not None else None
        if decoded and (decoded.actor != actor_fp or decoded.request != request_fp):
            raise RetrievalFault("invalid_cursor")
        if not SLOTS.acquire(blocking=False):
            raise Busy("query capacity")
        try:
            with (
                self.files.lock(".content-index-catalog.lock"),
                self.store._maintenance(),
                self.store._connection() as db,
            ):
                deadline = time.monotonic() + QUERY_SECONDS
                page = self._search(
                    db,
                    query,
                    match,
                    actor,
                    course_id,
                    source_ids,
                    content_types,
                    limit,
                    decoded,
                    actor_fp,
                    request_fp,
                    deadline,
                )
                yield page
                if time.monotonic() > deadline + 3:
                    raise Unavailable("search response deadline")
        finally:
            SLOTS.release()

    def _search(
        self,
        db,
        query,
        match,
        actor,
        course_id,
        source_ids,
        content_types,
        limit,
        cursor,
        actor_fp,
        request_fp,
        deadline,
    ):
        _, active, manifest = self._active()
        generation = (
            self._hmac("index-generation-v1", active.generation_id) if active else None
        )
        snap = self._hmac("index-content-snapshot-v1", list(_meta(db)))
        if cursor and (cursor.generation != generation or cursor.snapshot != snap):
            raise RetrievalFault("snapshot_changed")
        if not active:
            return SearchResultPage(
                items=(),
                next_cursor=None,
                index_generation=None,
                ranking_schema=self.RANKING,
            )
        selected = {v.source_id for v in manifest.basis.versions}
        visible = []
        for sid in sorted(selected):
            row = db.execute(
                "SELECT course_id FROM sources WHERE id=?", (sid,)
            ).fetchone()
            if (
                source_ids is not None
                and sid not in source_ids
                or course_id is not None
                and (row is None or row[0] != course_id)
            ):
                continue
            try:
                self.store._authorize(db, sid, actor)
            except (Forbidden, NotFound):
                continue
            visible.append(sid)
        if len(visible) > 32:
            raise RetrievalFault("scope_required")
        query_value = self._query_value(query, match) if visible else None
        budget = [0]
        record_budget = [0]
        ranked = []
        live = {}
        versions = {}
        for sid in visible:
            bindings = [v for v in manifest.basis.versions if v.source_id == sid]
            sel = IndexSelection(
                parsed_version_ids=tuple(v.parsed_version_id for v in bindings),
                config=manifest.basis.selection.config,
            )
            try:
                projections, records, _, _ = self._export(
                    db, sel, actor, budget=budget, record_budget=record_budget
                )
                if tuple(_version_binding(p) for p in projections) != tuple(bindings):
                    raise IntegrityError("stale projection binding")
                proof = next(f for f in manifest.files if f.source_id == sid)
                if (
                    record_set_sha256(records) != proof.record_set_sha256
                    or len(records) != proof.record_count
                ):
                    raise IntegrityError("stale recordset")
            except (
                ContentStoreError,
                ValidationError,
                ValueError,
                KeyError,
                TypeError,
            ):
                raise RetrievalFault("stale_index") from None
            budget[0] += proof.size_bytes
            if budget[0] > MAX_IO:
                raise Unavailable("query snapshot byte limit")
            data = self.files.read(_gen_path(active) + "/" + proof.name)
            if len(data) != proof.size_bytes or sha256(data) != proof.sha256:
                raise Unavailable("source index unavailable")
            hits = self._search_partition(
                data,
                records,
                query_value,
                content_types,
                deadline,
                source_id=sid,
                generation_id=active.generation_id,
            )
            if len(hits) > MAX_MATCHES or len(ranked) + len(hits) > MAX_MATCHES:
                raise RetrievalFault("query_too_broad")
            ranked.extend(self._rank_scores(hits))
            live.update({r.index_record_id: r for r in records})
        if time.monotonic() > deadline:
            raise Unavailable("query deadline")
        ranked.sort(key=lambda x: (-x[0], x[1]))
        result_fp = fingerprint(ranked)
        start = 0
        if cursor:
            if cursor.results != result_fp:
                raise RetrievalFault("snapshot_changed")
            ids = [r[1] for r in ranked]
            if cursor.last not in ids:
                raise RetrievalFault("invalid_cursor")
            start = ids.index(cursor.last) + 1
        items = []
        next_cursor = None
        for rank_score, rid, raw_score in ranked[start:]:
            record = live[rid]
            b = record.body
            if b.source_version_id not in versions:
                row = db.execute(
                    "SELECT data FROM source_versions WHERE id=?",
                    (b.source_version_id,),
                ).fetchone()
                versions[b.source_version_id] = SourceVersion.model_validate_json(
                    row[0]
                )
            block = ContentBlock.model_validate_json(
                db.execute(
                    "SELECT data FROM content_blocks WHERE version_id=? AND id=?",
                    (b.parsed_version_id, b.block_id),
                ).fetchone()[0]
            )
            locations = locators(block, versions[b.source_version_id])
            external = (
                len(
                    canonical(
                        [location.model_dump(mode="json") for location in locations]
                    )
                )
                > 32768
            )
            end = min(b.end, b.start + 512)
            hit = SearchHit(
                index_record_id=rid,
                source_id=b.source_id,
                source_version_id=b.source_version_id,
                parsed_version_id=b.parsed_version_id,
                block_id=b.block_id,
                content_type=b.content_type,
                anchor=RecordAnchor(
                    parsed_version_id=b.parsed_version_id,
                    block_id=b.block_id,
                    text_sha256=b.text_sha256,
                    start=b.start,
                    end=b.end,
                ),
                excerpt=TextWindow(
                    parsed_version_id=b.parsed_version_id,
                    block_id=b.block_id,
                    start=b.start,
                    end=end,
                    text_length=b.text_length,
                    text_sha256=b.text_sha256,
                    text=block.text[b.start : end],
                ),
                locators=None if external else locations,
                locators_in_structure=external,
                structure_route=route(
                    "parsed", b.parsed_version_id, "blocks", b.block_id, "structure"
                ),
                text_route=route(
                    "parsed", b.parsed_version_id, "blocks", b.block_id, "text"
                ),
                method=self.METHOD,
                components=(self._score_component(b.source_id, raw_score),),
                ranking_score=rank_score,
                ranking_schema=self.RANKING,
                index_generation=generation,
                projection_fingerprint=b.projection_sha256,
            )
            prospective = items + [hit]
            if (
                len(canonical([h.model_dump(mode="json") for h in prospective]))
                > 240 * 1024
            ):
                if not items:
                    raise Unavailable("search item exceeds page")
                break
            items = prospective
            if len(items) >= limit:
                break
        if start + len(items) < len(ranked) and items:
            next_cursor = self._cursor_encode(
                SearchCursor(
                    actor=actor_fp,
                    request=request_fp,
                    generation=generation,
                    snapshot=snap,
                    results=result_fp,
                    last=items[-1].index_record_id,
                    expires=cursor.expires if cursor else int(time.time()) + 300,
                )
            )
        if time.monotonic() > deadline:
            raise Unavailable("query hydration deadline")
        return SearchResultPage(
            items=tuple(items),
            next_cursor=next_cursor,
            index_generation=generation,
            ranking_schema=self.RANKING,
        )
