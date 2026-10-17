"""Verified adapters use the existing content-v1 transaction/artifact primitives.

No DDL migration, queue, public synthetic promotion, or automatic recovery.
"""

import io

from src.content_store.adapters import _candidate
from src.content_store.errors import (
    Conflict,
    Forbidden,
    IntegrityError,
    UnverifiedBinding,
)
from src.content_store.models import (
    ArtifactReference,
    ContentBlock,
    ParsedDocument,
    ParsedDocumentVersion,
    PublishedVersion,
    SourceVersion,
    fingerprint,
    sha256,
    snapshot,
)
from src.content_store.store import _encoded
from src.model_discovery.cs50 import deterministic_id


def _ref(data, mime="application/json"):
    return ArtifactReference(sha256=sha256(data), size_bytes=len(data), mime_type=mime)


def _scope(store, db, verified, actor, revision=None):
    source = store._authorize(db, verified.registration.resolved_id, actor, write=True)
    if source.registration != verified.registration:
        raise Conflict("verified source differs from registered identity")
    if revision is not None and source.acl_revision != revision:
        raise Forbidden("source permissions changed during import")
    if (
        store._purpose != "content"
        or db.execute("SELECT purpose FROM metadata WHERE id=1").fetchone()[0]
        != "content"
    ):
        raise Forbidden("verified adapters require a normal content store")
    return source


def _source_version(verified, sequence=1):
    source_id = verified.registration.resolved_id
    return SourceVersion(
        source_version_id=deterministic_id(
            "content_source_version_v1",
            source_id,
            verified.variant_key,
            verified.manifest.digest,
        ),
        source_id=source_id,
        variant_key=verified.variant_key,
        manifest=verified.manifest,
        binding_sha256=sha256(verified.binding),
        publication_seq=sequence,
    )


def _bound_raw(store, db, verified):
    for ref in verified.manifest.artifacts:
        row = db.execute(
            "SELECT data FROM raw_reservations WHERE source_id=? AND sha256=?",
            (verified.registration.resolved_id, ref.sha256),
        ).fetchone()
        if row is None or ArtifactReference.model_validate_json(
            row[0]
        ) != ArtifactReference(**ref.model_dump(exclude={"role", "ordinal"})):
            raise UnverifiedBinding("raw manifest lacks source-bound reservation")
        store._read_blob(ref, db)


def _known_source_version(store, db, verified):
    expected = _source_version(verified)
    row = db.execute(
        "SELECT data,state FROM source_versions WHERE id=?",
        (expected.source_version_id,),
    ).fetchone()
    if row is None:
        raise UnverifiedBinding("verified source version required")
    old = SourceVersion.model_validate_json(row[0])
    if (
        row[1] != "verified"
        or old.model_copy(update={"publication_seq": 1}) != expected
    ):
        raise Conflict("source version binding conflict")
    _bound_raw(store, db, verified)
    return old


def register(store, source_id, manifest, *, variant_key, binding, actor):
    verified = _candidate(binding, staging_parent=store.root / "staging")
    if (
        source_id != verified.registration.resolved_id
        or variant_key != verified.variant_key
        or type(manifest) is not type(verified.manifest)
        or snapshot(manifest) != verified.manifest
    ):
        raise UnverifiedBinding("source manifest contradicts verified bundle")
    expected = _source_version(verified)
    ref = _ref(verified.binding)
    with store._maintenance():
        with store._connection() as db:
            _scope(store, db, verified, actor)
            _bound_raw(store, db, verified)
            old = db.execute(
                "SELECT id FROM source_versions WHERE id=?",
                (expected.source_version_id,),
            ).fetchone()
            if old:
                return _known_source_version(store, db, verified)
        slot = deterministic_id("content_binding_slot_v1", expected.source_version_id)
        run = store._reserve(
            source_id,
            actor,
            kind="raw",
            slot_id=slot,
            request_key=slot,
            request_fingerprint=fingerprint(
                dict(version=expected.source_version_id, binding=ref.sha256)
            ),
        )
        with store._running(run):
            store._artifacts.stage(run.run_id, io.BytesIO(verified.binding), ref)
            store._prepared(run, (ref,), actor)
            store._artifacts.install(run.run_id, ref)
            with store._connection(write=True) as db:
                _scope(store, db, verified, actor, run.acl_revision)
                _bound_raw(store, db, verified)
                store._record_blob(db, ref)
                version = _source_version(verified, store._sequence(db))
                db.execute(
                    "INSERT INTO source_versions VALUES (?,?,?,?,'verified',?,?)",
                    (
                        version.source_version_id,
                        source_id,
                        variant_key,
                        manifest.digest,
                        version.publication_seq,
                        _encoded(version),
                    ),
                )
                for raw in manifest.artifacts:
                    db.execute(
                        "INSERT INTO source_raw_artifacts VALUES (?,?,?,?,?,?)",
                        (
                            version.source_version_id,
                            source_id,
                            raw.role,
                            raw.ordinal,
                            raw.sha256,
                            _encoded(raw),
                        ),
                    )
                db.execute(
                    "INSERT INTO artifact_references VALUES (?,?,0,?,NULL,?)",
                    (run.run_id, "source_binding", ref.sha256, _encoded(ref)),
                )
                store._update_run(db, run, state="committed", manifest=(ref,))
                return version


def publish(store, source_version_id, candidate, *, actor, request_key):
    verified = _candidate(candidate, staging_parent=store.root / "staging")
    stream = ParsedDocument(
        source_id=verified.registration.resolved_id,
        representation_key=verified.representation,
    )
    config = verified.config
    slot = deterministic_id(
        "content_slot_v1",
        source_version_id,
        stream.parsed_document_id,
        config.config_id,
    )
    entries = (
        ("payload", verified.payload, "application/json"),
        ("projection", verified.projection, "application/json"),
        ("binding", verified.binding, "application/json"),
    ) + verified.artifacts
    named = tuple((role, _ref(data, mime), data) for role, data, mime in entries)
    payload_ref, projection_ref = named[0][1], named[1][1]
    version_id = deterministic_id(
        "content_version_v1", slot, payload_ref.sha256, projection_ref.sha256
    )
    blocks = verified.blocks
    if verified.transcript:
        blocks = tuple(
            ContentBlock.model_validate(
                b.model_dump()
                | dict(
                    block_id=deterministic_id(
                        "content_cue_v1",
                        version_id,
                        str(b.locators[0].original_segment_id),
                    )
                )
            )
            for b in blocks
        )
    intent = fingerprint(
        dict(
            slot_id=slot,
            payload_sha256=payload_ref.sha256,
            projection_sha256=projection_ref.sha256,
            artifacts=[
                dict(role=role, **ref.model_dump(mode="json")) for role, ref, _ in named
            ],
        )
    )
    with store._maintenance():
        with store._connection() as db:
            _scope(store, db, verified, actor)
            source_version = _known_source_version(store, db, verified)
            if source_version.source_version_id != source_version_id:
                raise UnverifiedBinding("candidate belongs to another source version")
        run = store._reserve(
            stream.source_id,
            actor,
            kind="raw",
            slot_id=slot,
            request_key=request_key,
            request_fingerprint=intent,
        )
        if run.state == "committed":
            with store._connection() as db:
                return PublishedVersion(
                    version=store._parsed(db, run.parsed_version_id, actor),
                    created=False,
                )
        with store._running(run):
            with store._connection() as db:
                old = db.execute(
                    "SELECT data FROM parsed_versions WHERE slot_id=?", (slot,)
                ).fetchone()
                if old:
                    old_version = ParsedDocumentVersion.model_validate_json(old[0])
                    if old_version.parsed_version_id != version_id:
                        raise Conflict(
                            "same slot has different payload or projection bytes"
                        )
                    store._parsed(db, version_id, actor)
            # Equal hashes may occur in different roles. Install each blob only once.
            unique = {ref.sha256: (ref, data) for _, ref, data in named}
            refs = tuple(ref for ref, _ in unique.values())
            for ref, data in unique.values():
                store._artifacts.stage(run.run_id, io.BytesIO(data), ref)
            store._prepared(run, refs, actor)
            for ref in refs:
                store._artifacts.install(run.run_id, ref)
            with store._connection(write=True) as db:
                _scope(store, db, verified, actor, run.acl_revision)
                _known_source_version(store, db, verified)
                for ref in refs:
                    store._record_blob(db, ref)
                if old:
                    version = old_version
                else:
                    known_config = db.execute(
                        "SELECT data FROM parser_configs WHERE id=?",
                        (config.config_id,),
                    ).fetchone()
                    if known_config and known_config[0] != _encoded(config):
                        raise Conflict("parser configuration identity collision")
                    db.execute(
                        "INSERT OR IGNORE INTO parser_configs VALUES (?,?)",
                        (config.config_id, _encoded(config)),
                    )
                    db.execute(
                        "INSERT OR IGNORE INTO parsed_documents VALUES (?,?,?)",
                        (
                            stream.parsed_document_id,
                            stream.source_id,
                            stream.representation_key,
                        ),
                    )
                    version = ParsedDocumentVersion(
                        parsed_version_id=version_id,
                        parsed_document_id=stream.parsed_document_id,
                        source_version_id=source_version_id,
                        source_id=stream.source_id,
                        slot_id=slot,
                        parser_config_id=config.config_id,
                        payload=payload_ref,
                        projection=projection_ref,
                        payload_schema=config.payload_schema,
                        original_document_id=verified.original_document_id,
                        quality_status=verified.quality_status,
                        publication_seq=store._sequence(db),
                    )
                    db.execute(
                        "INSERT INTO parsed_versions VALUES (?,?,?,?,?,?,?,?,'published',?,?)",
                        (
                            version_id,
                            stream.source_id,
                            stream.parsed_document_id,
                            source_version_id,
                            slot,
                            config.config_id,
                            payload_ref.sha256,
                            projection_ref.sha256,
                            version.publication_seq,
                            _encoded(version),
                        ),
                    )
                    for block in blocks:
                        db.execute(
                            "INSERT INTO content_blocks VALUES (?,?,?,?,?)",
                            (
                                version_id,
                                block.block_id,
                                block.order,
                                block.text_sha256,
                                _encoded(block),
                            ),
                        )
                        for ordinal, loc in enumerate(block.locators):
                            db.execute(
                                "INSERT INTO content_locators VALUES (?,?,?,?,?,?,?,?)",
                                (
                                    version_id,
                                    block.block_id,
                                    ordinal,
                                    loc.raw_artifact_sha256,
                                    loc.time_status,
                                    loc.start,
                                    loc.end,
                                    _encoded(loc),
                                ),
                            )
                for role, ref, _ in named:
                    db.execute(
                        "INSERT INTO artifact_references VALUES (?,?,0,?,?,?)",
                        (run.run_id, role, ref.sha256, version_id, _encoded(ref)),
                    )
                store._update_run(
                    db,
                    run,
                    state="committed",
                    manifest=refs,
                    parsed_version_id=version_id,
                )
            return PublishedVersion(version=version, created=not bool(old))


def read_artifact(store, version_id, role, *, actor, request_key=None):
    """Internal trusted API, not an HTTP DTO. No caller-controlled filesystem paths."""
    with store._maintenance(), store._connection() as db:
        store._parsed(db, version_id, actor)
        row = db.execute(
            "SELECT a.data FROM artifact_references a JOIN processing_runs r ON r.id=a.run_id "
            "WHERE a.version_id=? AND a.role=? AND a.ordinal=0 AND r.state='committed' "
            "AND (? IS NULL OR r.request_key=?) ORDER BY a.rowid LIMIT 1",
            (version_id, role, request_key, request_key),
        ).fetchone()
        if row is None:
            raise IntegrityError("version artifact unavailable")
        return store._read_blob(ArtifactReference.model_validate_json(row[0]), db)
