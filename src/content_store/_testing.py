"""Internal synthetic fixture contract, NEVER a verified CS50/publication adapter.

Only a permanently synthetic_test database and synthetic namespace can use this.
It is not exported, registered with a runner, selected by payload metadata, or
reachable through ContentStore.publish_parsed_document(). No production promotion.
"""

import io
import json

from pydantic import Field, ValidationError, model_validator

from src.content_store.errors import Conflict, Forbidden, IntegrityError, InvalidInput
from src.content_store.models import (
    MAX_BLOCKS,
    MAX_BYTES,
    ArtifactReference,
    ContentBlock,
    ParsedDocument,
    ParsedDocumentVersion,
    ParserConfiguration,
    PublishedVersion,
    RawManifest,
    SourceVersion,
    canonical,
    fingerprint,
    sha256,
    snapshot,
)
from src.content_store.store import ContentStore, _encoded
from src.job_control.models import Contract
from src.model_discovery.cs50 import deterministic_id


class SyntheticPayload(Contract):
    schema_version: int = Field(default=1, ge=1, le=1)
    source_origin: str = Field(default="synthetic", pattern=r"^synthetic$")
    blocks: tuple[ContentBlock, ...] = Field(min_length=1, max_length=MAX_BLOCKS)

    @model_validator(mode="after")
    def ordered(self):
        if [b.order for b in self.blocks] != list(range(len(self.blocks))) or len(
            {b.block_id for b in self.blocks}
        ) != len(self.blocks):
            raise ValueError("Synthetic block identity/order conflict")
        if sum(b.type == "image_reference" for b in self.blocks) > 500:
            raise ValueError("Image count limit")
        for index, block in enumerate(self.blocks):
            if block.payload_pointer != f"/blocks/{index}":
                raise ValueError("Synthetic block pointer mismatch")
            if any(
                loc.origin_pointer != block.payload_pointer for loc in block.locators
            ):
                raise ValueError("Synthetic origin pointer mismatch")
        return self


def initialize_synthetic_store(root):
    return ContentStore._initialize(root, purpose="synthetic_test")


def _scope(store, db, source_id, actor):
    if (
        store._purpose != "synthetic_test"
        or db.execute("SELECT purpose FROM metadata WHERE id=1").fetchone()[0]
        != "synthetic_test"
    ):
        raise Forbidden(
            "synthetic contract requires a permanently synthetic test store"
        )
    source = store._authorize(db, source_id, actor, write=True)
    reg = source.registration
    if (
        not reg.identity_namespace.startswith("synthetic:")
        or reg.source_origin != "synthetic"
        or reg.source_type != "synthetic"
    ):
        raise Forbidden("synthetic contract requires a synthetic source")
    return source


def register_synthetic_version(
    store, source_id, manifest: RawManifest, *, actor, variant_key="default"
):
    if not isinstance(manifest, RawManifest):
        raise InvalidInput("typed synthetic manifest required")
    manifest = snapshot(manifest)
    binding_sha = fingerprint(
        {
            "contract": "synthetic_fixture_v1",
            "source_id": source_id,
            "manifest": manifest.digest,
        }
    )
    version_id = deterministic_id(
        "content_source_version_v1", source_id, variant_key, manifest.digest
    )
    with store._maintenance():
        with store._connection() as db:
            _scope(store, db, source_id, actor)
            for ref in manifest.artifacts:
                row = db.execute(
                    "SELECT data FROM raw_reservations WHERE source_id=? AND sha256=?",
                    (source_id, ref.sha256),
                ).fetchone()
                if row is None or ArtifactReference.model_validate_json(
                    row[0]
                ) != ArtifactReference(**ref.model_dump(exclude={"role", "ordinal"})):
                    raise IntegrityError("raw manifest lacks source-bound reservation")
                store._read_blob(ref)
        with store._connection(write=True) as db:
            _scope(store, db, source_id, actor)
            existing = db.execute(
                "SELECT data FROM source_versions WHERE id=?", (version_id,)
            ).fetchone()
            if existing:
                return SourceVersion.model_validate_json(existing[0])
            version = SourceVersion(
                source_version_id=version_id,
                source_id=source_id,
                variant_key=variant_key,
                manifest=manifest,
                binding_sha256=binding_sha,
                publication_seq=store._sequence(db),
            )
            db.execute(
                "INSERT INTO source_versions VALUES (?,?,?,?,'verified',?,?)",
                (
                    version_id,
                    source_id,
                    variant_key,
                    manifest.digest,
                    version.publication_seq,
                    _encoded(version),
                ),
            )
            for ref in manifest.artifacts:
                db.execute(
                    "INSERT INTO source_raw_artifacts VALUES (?,?,?,?,?,?)",
                    (
                        version_id,
                        source_id,
                        ref.role,
                        ref.ordinal,
                        ref.sha256,
                        _encoded(ref),
                    ),
                )
            return version


def publish_synthetic(
    store,
    source_version_id,
    payload: bytes,
    config: ParserConfiguration,
    *,
    actor,
    request_key="synthetic-request",
):
    """Exercise the real reserve/stage/prepare/install/commit path with tiny gold fixtures."""
    if (
        not isinstance(payload, bytes)
        or len(payload) > MAX_BYTES
        or not isinstance(config, ParserConfiguration)
    ):
        raise InvalidInput("bounded synthetic payload and typed parser required")
    config = snapshot(config)
    if (
        config.parser_name != "synthetic"
        or config.adapter_version != "synthetic_fixture_v1"
        or config.payload_schema != "SyntheticPayload:1"
    ):
        raise InvalidInput("synthetic parser contract required")
    try:

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result

        parsed = json.loads(payload, object_pairs_hook=unique_object)
        if (
            not isinstance(parsed, dict)
            or parsed.get("source_origin") != "synthetic"
            or parsed.get("schema_version") != 1
        ):
            raise ValueError("explicit synthetic payload marker required")
        canonical(
            parsed
        )  # JSON depth and finite-value bound; never replaces original bytes.
        document = SyntheticPayload.model_validate(parsed)
    except (ValidationError, ValueError, UnicodeError, RecursionError):
        raise InvalidInput("invalid synthetic payload") from None
    with store._maintenance():
        with store._connection() as db:
            row = db.execute(
                "SELECT data FROM source_versions WHERE id=? AND state='verified'",
                (source_version_id,),
            ).fetchone()
            if row is None:
                raise InvalidInput("synthetic source version required")
            source_version = SourceVersion.model_validate_json(row[0])
            _scope(store, db, source_version.source_id, actor)
            raw_hashes = {a.sha256 for a in source_version.manifest.artifacts}
            for block in document.blocks:
                if any(
                    loc.raw_artifact_sha256 not in raw_hashes for loc in block.locators
                ):
                    raise IntegrityError("block origin outside source version")
        stream = ParsedDocument(
            source_id=source_version.source_id, representation_key="synthetic:fixture"
        )
        slot = deterministic_id(
            "content_slot_v1",
            source_version_id,
            stream.parsed_document_id,
            config.config_id,
        )
        projection = canonical(
            {
                "schema_version": 1,
                "slot_id": slot,
                "blocks": [b.model_dump(mode="json") for b in document.blocks],
            }
        )
        payload_ref = ArtifactReference(
            sha256=sha256(payload),
            size_bytes=len(payload),
            mime_type="application/json",
        )
        projection_ref = ArtifactReference(
            sha256=sha256(projection),
            size_bytes=len(projection),
            mime_type="application/json",
        )
        version_id = deterministic_id(
            "content_version_v1", slot, payload_ref.sha256, projection_ref.sha256
        )
        intent = fingerprint(
            {
                "slot_id": slot,
                "payload_sha256": payload_ref.sha256,
                "projection_sha256": projection_ref.sha256,
            }
        )
        run = store._reserve(
            source_version.source_id,
            actor,
            kind="synthetic",
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
                    store._parsed(db, old_version.parsed_version_id, actor)
            if old:
                with store._connection(write=True) as db:
                    source = _scope(store, db, source_version.source_id, actor)
                    if source.acl_revision != run.acl_revision:
                        raise Forbidden("source permissions changed during import")
                    store._update_run(
                        db, run, state="committed", parsed_version_id=version_id
                    )
                return PublishedVersion(version=old_version, created=False)
            refs = (payload_ref, projection_ref)
            for ref, data in zip(refs, (payload, projection), strict=True):
                store._artifacts.stage(run.run_id, io.BytesIO(data), ref)
            store._prepared(run, refs, actor)
            for ref in refs:
                store._artifacts.install(run.run_id, ref)
            with store._connection(write=True) as db:
                source = _scope(store, db, source_version.source_id, actor)
                if source.acl_revision != run.acl_revision:
                    raise Forbidden("source permissions changed during import")
                for ref in refs:
                    store._record_blob(db, ref)
                encoded_config = _encoded(config)
                known_config = db.execute(
                    "SELECT data FROM parser_configs WHERE id=?", (config.config_id,)
                ).fetchone()
                if known_config and known_config[0] != encoded_config:
                    raise Conflict("parser configuration identity collision")
                db.execute(
                    "INSERT OR IGNORE INTO parser_configs VALUES (?,?)",
                    (config.config_id, encoded_config),
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
                    quality_status="synthetic_test_only",
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
                for block in document.blocks:
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
                for role, ref in zip(("payload", "projection"), refs, strict=True):
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
            return PublishedVersion(version=version, created=True)


def project_synthetic_for_index(store, parsed_version_id, *, actor, config=None):
    """Explicit permanently synthetic projection; never accepted on content roots."""
    from src.content_store.index_projection import _project

    return _project(
        store, parsed_version_id, actor=actor, config=config, synthetic=True
    )


def synthetic_content_index(store, index_root, *, cursor_key_file, initialize=False):
    """Explicit test-only FTS adapter; cannot open/promote normal content stores."""
    from src.tools_rag.content_index import ContentIndex

    if store._purpose != "synthetic_test":
        raise Forbidden("permanently synthetic test store required")
    factory = ContentIndex.initialize if initialize else ContentIndex
    return factory(store, index_root, cursor_key_file=cursor_key_file, _synthetic=True)
