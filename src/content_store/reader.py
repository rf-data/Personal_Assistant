"""Authorized keyset projections over the existing content-v1 register."""

import base64
import hashlib
import hmac
import os
import re
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from src.content_store.artifacts import FILE_FLAGS, _open_directory, _private
from src.content_store.errors import IntegrityError, NotFound, Unavailable
from src.content_store.models import (
    ArtifactReference,
    ContentBlock,
    ParserConfiguration,
    SourceVersion,
    canonical,
    checked_actor,
    fingerprint,
)
from src.content_store.read_files import anonymous_file, check_support, seal
from src.content_store.read_models import (
    MAX_PAGE,
    ContentPage,
    ContentReadSettings,
    ParsedDTO,
    ParsedRef,
    SourceDTO,
    SourceVersionDTO,
    StructureDTO,
    TextWindow,
)
from src.content_store.read_views import (
    block_view,
    locators,
    public_url,
    raw_view,
    route,
    structure,
    structure_hash,
    warnings,
)
from src.content_store.store import ContentStore
from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import CourseId
from src.tools_materials.quality import _json


class ReadFault(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


class Cursor(Contract):
    schema_version: Literal[1] = 1
    actor: Sha
    request: Sha
    snapshot: Sha
    acl_revision: int | None = Field(default=None, ge=0)
    last: tuple[str | int, ...] = Field(min_length=1, max_length=2)


def private_bytes(path, limit):
    parent = _open_directory(path.parent)
    try:
        fd = os.open(path.name, FILE_FLAGS, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            info = _private(stream.fileno())
            if info.st_size > limit:
                raise ValueError("Private configuration limit")
            data = stream.read(limit + 1)
            if len(data) != info.st_size:
                raise ValueError("Private configuration changed")
            return data
    finally:
        os.close(parent)


def load_content_settings(path):
    from pathlib import Path

    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Explicit content configuration required")
    return ContentReadSettings.model_validate(_json(private_bytes(path, 8192)))


@dataclass
class Download:
    stack: ExitStack
    stream: object
    size: int
    mime: str
    filename: str

    def close(self):
        self.stack.close()


class ContentReader:
    def __init__(self, settings: ContentReadSettings):
        check_support()
        settings = ContentReadSettings.model_validate_json(settings.model_dump_json())
        self.store = ContentStore(settings.root)
        if self.store._purpose != "content":
            raise Unavailable("Test stores are not HTTP content")
        self.key = private_bytes(settings.cursor_key_file, 64)
        if not 32 <= len(self.key) <= 64:
            raise ValueError("Private signing key must contain 32 to 64 bytes")

    def _encode_cursor(self, cursor):
        data = canonical(cursor.model_dump(mode="json"))
        sig = hmac.digest(self.key, data, "sha256")
        return base64.urlsafe_b64encode(data + sig).decode().rstrip("=")

    def _snapshot(self, meta):
        # Bind internal revisions without exposing cross-source publication counts.
        return hmac.new(
            self.key, b"content-snapshot-v1\0" + canonical(list(meta)), hashlib.sha256
        ).hexdigest()

    def _decode_cursor(self, value):
        try:
            if not re.fullmatch(r"[A-Za-z0-9_-]{20,1600}", value):
                raise ValueError
            data = base64.b64decode(
                value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
            )
            raw, sig = data[:-32], data[-32:]
            if not hmac.compare_digest(sig, hmac.digest(self.key, raw, "sha256")):
                raise ValueError
            cursor = Cursor.model_validate(_json(raw))
            if self._encode_cursor(cursor) != value:
                raise ValueError
            return cursor
        except (ValueError, TypeError):
            raise ReadFault(400, "invalid_cursor") from None

    def _source(self, db, source_id, actor):
        return self.store._authorize(db, source_id, actor)

    def _sv(self, db, source_id, version_id, actor):
        self._source(db, source_id, actor)
        row = db.execute(
            "SELECT data FROM source_versions WHERE id=? AND source_id=? AND state='verified'",
            (version_id, source_id),
        ).fetchone()
        if row is None:
            raise NotFound()
        version = SourceVersion.model_validate_json(row[0])
        hashes = [
            version.binding_sha256,
            *[r.sha256 for r in version.manifest.artifacts],
        ]
        for digest in hashes:
            ref = db.execute(
                "SELECT size_bytes,state FROM artifacts WHERE sha256=?", (digest,)
            ).fetchone()
            if ref is None:
                raise IntegrityError()
            if ref[1] != "available":
                raise NotFound()
            if digest == version.binding_sha256:
                self.store._read_blob(
                    ArtifactReference(
                        sha256=digest, size_bytes=ref[0], mime_type="application/json"
                    ),
                    db,
                )
        return version

    def _parsed(self, db, version_id, actor):
        row = db.execute(
            "SELECT source_id,source_version_id FROM parsed_versions WHERE id=? AND state='published'",
            (version_id,),
        ).fetchone()
        if row is None:
            raise NotFound()
        source_version = self._sv(db, row[0], row[1], actor)
        if db.execute(
            "SELECT 1 FROM artifact_references r JOIN artifacts a ON a.sha256=r.sha256 WHERE r.version_id=? AND a.state='quarantined'",
            (version_id,),
        ).fetchone():
            raise NotFound()
        version = self.store._parsed(db, version_id, actor)
        if version.quality_status == "synthetic_test_only":
            raise NotFound()
        return version, source_version

    @staticmethod
    def _source_view(source):
        r = source.registration
        return SourceDTO(
            source_id=source.source_id,
            course_id=r.course_id,
            source_type=r.source_type,
            source_origin=r.source_origin,
            original_url=public_url(r.original_url),
            versions_route=route("sources", source.source_id, "versions"),
        )

    def source(self, source_id, actor):
        with self.store._maintenance(), self.store._connection() as db:
            return self._source_view(self._source(db, source_id, actor))

    def parsed(self, version_id, actor):
        with self.store._maintenance(), self.store._connection() as db:
            v, _ = self._parsed(db, version_id, actor)
            config = ParserConfiguration.model_validate_json(
                db.execute(
                    "SELECT data FROM parser_configs WHERE id=?", (v.parser_config_id,)
                ).fetchone()[0]
            )
            quality = self._quality(db, version_id)
            return ParsedDTO(
                parsed_version_id=version_id,
                source_id=v.source_id,
                source_version_id=v.source_version_id,
                parser_config_id=v.parser_config_id,
                parser_name=config.parser_name,
                parser_version=config.parser_version,
                implementation_revision=config.implementation_revision,
                payload_schema=v.payload_schema,
                payload_sha256=v.payload.sha256,
                projection_sha256=v.projection.sha256,
                quality_status=v.quality_status,
                block_count=db.execute(
                    "SELECT count(*) FROM content_blocks WHERE version_id=?",
                    (version_id,),
                ).fetchone()[0],
                warnings=warnings(quality),
                blocks_route=route("parsed", version_id, "blocks"),
            )

    def _quality(self, db, version_id):
        row = db.execute(
            "SELECT r.data FROM artifact_references r JOIN processing_runs p ON p.id=r.run_id WHERE r.version_id=? AND r.role='quality' AND p.state='committed' ORDER BY r.run_id LIMIT 1",
            (version_id,),
        ).fetchone()
        if row is None:
            raise IntegrityError()
        return _json(
            self.store._read_blob(ArtifactReference.model_validate_json(row[0]), db)
        )

    def page(self, kind, ids, query, actor):
        actor = checked_actor(actor)
        allowed = {"limit", "cursor"} | (
            {"course_id", "source_type", "q"} if kind == "sources" else set()
        )
        if set(query) - allowed:
            raise ReadFault(400, "invalid_parameter")
        try:
            raw_limit = query.get("limit", "50")
            if not re.fullmatch(r"[0-9]{1,3}", raw_limit):
                raise ValueError
            limit = int(raw_limit)
            if not 1 <= limit <= 100:
                raise ValueError
            if "course_id" in query and query["course_id"] not in CourseId.__args__:
                raise ValueError
            if "q" in query and (
                not 1 <= len(query["q"]) <= 200 or any(ord(c) < 32 for c in query["q"])
            ):
                raise ValueError
            if "source_type" in query and query["source_type"] not in {
                "material",
                "transcript",
                "synthetic",
            }:
                raise ValueError
        except (ValueError, TypeError):
            raise ReadFault(400, "invalid_parameter") from None
        actor_fp = fingerprint(
            dict(subject=actor.subject, role=actor.role, courses=sorted(actor.courses))
        )
        request_fp = fingerprint(
            dict(
                kind=kind,
                ids=ids,
                filters={
                    k: v for k, v in query.items() if k not in {"cursor", "limit"}
                },
                limit=limit,
            )
        )
        cursor = self._decode_cursor(query["cursor"]) if "cursor" in query else None
        if cursor and (cursor.actor != actor_fp or cursor.request != request_fp):
            raise ReadFault(400, "invalid_cursor")
        if cursor and (
            len(cursor.last) != (2 if kind == "blocks" else 1)
            or type(cursor.last[-1]) is not str
            or (kind == "blocks" and type(cursor.last[0]) is not int)
        ):
            raise ReadFault(400, "invalid_cursor")
        with self.store._maintenance(), self.store._connection() as db:
            meta = db.execute(
                "SELECT publication_seq,collection_revision FROM metadata WHERE id=1"
            ).fetchone()
            if cursor and not hmac.compare_digest(
                cursor.snapshot, self._snapshot(meta)
            ):
                raise ReadFault(409, "snapshot_changed")
            source = None
            parsed = source_version = None
            if kind != "sources":
                if kind == "blocks":
                    parsed, source_version = self._parsed(db, ids[0], actor)
                    quality = self._quality(db, ids[0])
                    source = self._source(db, parsed.source_id, actor)
                else:
                    source = self._source(db, ids[0], actor)
                    if kind == "parsed_refs":
                        source_version = self._sv(db, *ids, actor)
                if cursor and cursor.acl_revision != source.acl_revision:
                    raise ReadFault(409, "snapshot_changed")
            last = cursor.last if cursor else None
            args = []
            if kind == "sources":
                courses = [c for c in actor.courses if query.get("course_id", c) == c]
                if not courses:
                    return ContentPage(items=(), next_cursor=None)
                sql = (
                    "SELECT s.id FROM sources s WHERE s.state='registered' AND s.publication_seq<=? AND s.course_id IN ("
                    + ",".join("?" for _ in courses)
                    + ") AND (s.owner=? OR EXISTS (SELECT 1 FROM source_grants g WHERE g.source_id=s.id AND g.subject=? AND g.permission='read'))"
                )
                args = [meta[0], *courses, actor.subject, actor.subject]
                if "source_type" in query:
                    sql += " AND json_extract(s.data,'$.registration.source_type')=?"
                    args.append(query["source_type"])
                if "q" in query:
                    sql += " AND instr(s.id,?)>0"
                    args.append(query["q"])
                if last:
                    sql += " AND s.id>?"
                    args.append(last[0])
                sql += " ORDER BY s.id"
            elif kind == "versions":
                sql = "SELECT v.id FROM source_versions v WHERE v.source_id=? AND v.state='verified' AND v.publication_seq<=? AND NOT EXISTS (SELECT 1 FROM source_raw_artifacts r JOIN artifacts a ON a.sha256=r.sha256 WHERE r.source_version_id=v.id AND a.state='quarantined') AND NOT EXISTS (SELECT 1 FROM artifacts a WHERE a.sha256=json_extract(v.data,'$.binding_sha256') AND a.state='quarantined')"
                args = [ids[0], meta[0]]
                if last:
                    sql += " AND v.id>?"
                    args.append(last[0])
                sql += " ORDER BY v.id"
            elif kind == "parsed_refs":
                sql = "SELECT v.id FROM parsed_versions v WHERE v.source_id=? AND v.source_version_id=? AND v.state='published' AND v.publication_seq<=? AND NOT EXISTS (SELECT 1 FROM artifact_references r JOIN artifacts a ON a.sha256=r.sha256 WHERE r.version_id=v.id AND a.state='quarantined')"
                args = [*ids, meta[0]]
                if last:
                    sql += " AND v.id>?"
                    args.append(last[0])
                sql += " ORDER BY v.id"
            else:
                sql = (
                    "SELECT block_order,id,data FROM content_blocks WHERE version_id=?"
                )
                args = [ids[0]]
                if last:
                    sql += " AND (block_order,id)>(?,?)"
                    args.extend(last)
                sql += " ORDER BY block_order,id"
            rows = db.execute(sql + " LIMIT ?", (*args, limit + 1)).fetchall()
            items = []
            size = 0
            position = None
            for row in rows[:limit]:
                if kind == "sources":
                    item = self._source_view(self._source(db, row[0], actor))
                    key = (row[0],)
                elif kind == "versions":
                    sv = self._sv(db, ids[0], row[0], actor)
                    item = SourceVersionDTO(
                        source_id=sv.source_id,
                        source_version_id=sv.source_version_id,
                        artifacts=tuple(raw_view(sv, r) for r in sv.manifest.artifacts),
                        parsed_versions_route=route(
                            "sources",
                            sv.source_id,
                            "versions",
                            sv.source_version_id,
                            "parsed",
                        ),
                    )
                    key = (row[0],)
                elif kind == "parsed_refs":
                    item = ParsedRef(
                        parsed_version_id=row[0], route=route("parsed", row[0])
                    )
                    key = (row[0],)
                else:
                    item = block_view(
                        ContentBlock.model_validate_json(row[2]),
                        parsed,
                        source_version,
                        quality,
                    )
                    key = (row[0], row[1])
                length = len(canonical(item.model_dump(mode="json")))
                if size + length > MAX_PAGE - 4096:
                    if not items:
                        raise Unavailable("Content item exceeds page limit")
                    break
                items.append(item)
                size += length
                position = key
            next_cursor = None
            if len(rows) > len(items) and position is not None:
                next_cursor = self._encode_cursor(
                    Cursor(
                        actor=actor_fp,
                        request=request_fp,
                        snapshot=self._snapshot(meta),
                        acl_revision=source.acl_revision if source else None,
                        last=position,
                    )
                )
            return ContentPage(items=tuple(items), next_cursor=next_cursor)

    def block(self, version_id, block_id, actor, query, *, structured=False):
        if set(query) - ({"start", "limit"} if not structured else set()):
            raise ReadFault(400, "invalid_parameter")
        with self.store._maintenance(), self.store._connection() as db:
            parsed, sv = self._parsed(db, version_id, actor)
            row = db.execute(
                "SELECT data FROM content_blocks WHERE version_id=? AND id=?",
                (version_id, block_id),
            ).fetchone()
            if row is None:
                raise NotFound()
            block = ContentBlock.model_validate_json(row[0])
            if structured:
                data, redacted = structure(block)
                locations = locators(block, sv)
                redacted = redacted or any(
                    public.model_dump(mode="json", exclude={"raw_reference"})
                    != original.model_dump(mode="json")
                    for public, original in zip(locations, block.locators, strict=True)
                )
                return StructureDTO(
                    parsed_version_id=version_id,
                    block_id=block_id,
                    data=data,
                    locators=locations,
                    redacted=redacted,
                    projection_sha256=structure_hash(data, locations),
                )
            try:
                if any(not re.fullmatch(r"[0-9]{1,9}", v) for v in query.values()):
                    raise ValueError
                start = int(query.get("start", 0))
                limit = int(query.get("limit", 16384))
                if start > len(block.text) or not 1 <= limit <= 16384:
                    raise ValueError
            except (ValueError, TypeError):
                raise ReadFault(400, "invalid_parameter") from None
            end = min(len(block.text), start + limit)
            return TextWindow(
                parsed_version_id=version_id,
                block_id=block_id,
                start=start,
                end=end,
                text_length=len(block.text),
                text_sha256=block.text_sha256,
                text=block.text[start:end],
            )

    def download(self, source_id, version_id, role, ordinal, actor):
        stack = ExitStack()
        try:
            stack.enter_context(self.store._maintenance())
            db = stack.enter_context(self.store._connection())
            sv = self._sv(db, source_id, version_id, actor)
            refs = [
                r
                for r in sv.manifest.artifacts
                if (r.role, r.ordinal) == (role, ordinal)
            ]
            if len(refs) != 1:
                raise NotFound()
            ref = refs[0]
            # Authorize and validate the catalog before opening this source-bound FD.
            directory = stack.enter_context(
                self.store._artifacts.directory(f"blobs/sha256/{ref.sha256[:2]}")
            )
            stream = stack.enter_context(
                os.fdopen(os.open(ref.sha256, FILE_FLAGS, dir_fd=directory), "rb")
            )
            info = _private(stream.fileno())
            # Anonymous, bounded response snapshot, never persistent content.
            snapshot = stack.enter_context(
                os.fdopen(
                    anonymous_file(),
                    "w+b",
                )
            )
            digest = hashlib.sha256()
            size = 0
            while chunk := stream.read(65536):
                size += len(chunk)
                if size > ref.size_bytes:
                    raise IntegrityError()
                digest.update(chunk)
                snapshot.write(chunk)
            if (
                info.st_size != ref.size_bytes
                or size != ref.size_bytes
                or digest.hexdigest() != ref.sha256
            ):
                raise IntegrityError()
            snapshot.flush()
            seal(snapshot.fileno())
            snapshot.seek(0)
            if hashlib.file_digest(snapshot, "sha256").hexdigest() != ref.sha256:
                raise IntegrityError()
            snapshot.seek(0)
            mime = (
                ref.mime_type
                if ref.mime_type
                in {"application/pdf", "text/plain", "application/x-subrip"}
                else "application/octet-stream"
            )
            return Download(stack, snapshot, size, mime, f"content-{ref.sha256}.bin")
        except BaseException:
            stack.close()
            raise
