"""Explicit single-host recovery/integrity. No parsing, adoption or auto-release."""

import io
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager

from pydantic import TypeAdapter, ValidationError

from src.content_store.artifacts import FILE_FLAGS, _Artifacts, _private, _sync
from src.content_store.errors import (
    Busy,
    Conflict,
    ContentStoreError,
    Forbidden,
    IntegrityError,
    InvalidInput,
    Unavailable,
    UnverifiedBinding,
)
from src.content_store.limits import (
    MAX_FILES,
    MAX_METADATA_ROWS,
    MAX_STORE_BYTES,
    directory_entries,
)
from src.content_store.models import (
    ArtifactReference,
    ContentBlock,
    ParsedDocument,
    ParsedDocumentVersion,
    ParserConfiguration,
    ProcessingRun,
    Source,
    SourceVersion,
    canonical,
    checked_actor,
    fingerprint,
    sha256,
)
from src.content_store.operations_models import (
    BindingIntent,
    IntegrityFinding,
    IntegrityReport,
    Intent,
    PublicationIntent,
    RawIntent,
    RecoveryResult,
)
from src.content_store.store import ContentStore
from src.model_discovery.cs50 import deterministic_id
from src.tools_materials.quality import _json

INTENT = TypeAdapter(Intent)


@contextmanager
def exclusive(store, actor, *, writable=True):
    actor = checked_actor(actor)
    if actor.role != "operator" or (writable and store.read_only):
        raise Forbidden("writable operator maintenance required")
    try:
        with store._artifacts.lock(".content-maintenance.lock", exclusive=True):
            yield actor
    except OSError:
        raise Unavailable("content maintenance unavailable") from None


def authorize_all(store, db, actor):
    actor = checked_actor(actor)
    if actor.role != "operator":
        raise Forbidden("operator maintenance required")
    rows = db.execute("SELECT owner,course_id FROM sources")
    count = 0
    for row in rows:
        count += 1
        if count > MAX_FILES:
            raise Unavailable("source maintenance limit")
        if row[0] != actor.subject or row[1] not in actor.courses:
            raise Forbidden("complete store ownership and scope required")


def record_intent(store, run, intent, actor):
    """Internal: called ONLY after adapter verification, before prepared manifest."""
    data = canonical(intent.model_dump(mode="json"))
    ref = ArtifactReference(
        sha256=sha256(data), size_bytes=len(data), mime_type="application/json"
    )
    store._artifacts.stage(run.run_id, io.BytesIO(data), ref)
    store._artifacts.install(run.run_id, ref)
    with store._connection(write=True) as db:
        source = store._authorize(db, run.source_id, actor, write=True)
        if source.acl_revision != run.acl_revision:
            raise Forbidden("source permissions changed during preparation")
        store._record_blob(db, ref)
        store._update_run(db, run, recovery=ref)


def _run(db, run_id):
    row = db.execute(
        "SELECT data FROM processing_runs WHERE id=?", (run_id,)
    ).fetchone()
    if row is None:
        raise InvalidInput("unknown recovery run")
    return ProcessingRun.model_validate_json(row[0])


def _intent(store, run, db=None):
    if run.retry_of is not None:
        from src.content_store.store import _retry_parent

        if db is not None:
            _retry_parent(db, run)
        else:
            with store._connection() as connection:
                _retry_parent(connection, run)
    if run.recovery is None:
        raise UnverifiedBinding("legacy run has no verified recovery intention")
    # Explicit integrity inspection may examine quarantined bytes; it never clears
    # the flags. Recovery itself still requires an available catalog reference.
    data = (
        store._artifacts.read(run.recovery)
        if db is not None
        else store._read_blob(run.recovery)
    )
    value = _json(data)
    canonical(value)
    intent = INTENT.validate_python(value)
    if intent.run_id != run.run_id or run.kind != "raw":
        raise UnverifiedBinding("recovery intention belongs to another run")
    if isinstance(intent, RawIntent):
        expected_slot = deterministic_id(
            "content_raw_slot_v1", run.source_id, intent.reference.sha256
        )
        expected_fingerprint = fingerprint(intent.reference.model_dump(mode="json"))
        refs = (intent.reference,)
    elif isinstance(intent, BindingIntent):
        v = intent.version
        if (
            v.source_id != run.source_id
            or intent.registration.resolved_id != run.source_id
            or v.binding_sha256 != intent.reference.sha256
        ):
            raise UnverifiedBinding("prepared source binding mismatch")
        expected_slot = deterministic_id("content_binding_slot_v1", v.source_version_id)
        expected_fingerprint = fingerprint(
            dict(version=v.source_version_id, binding=intent.reference.sha256)
        )
        refs = (intent.reference,)
    else:
        if intent.version.source_id != run.source_id:
            raise UnverifiedBinding("prepared publication source mismatch")
        expected_slot = intent.version.slot_id
        expected_fingerprint = fingerprint(
            dict(
                slot_id=expected_slot,
                payload_sha256=intent.version.payload.sha256,
                projection_sha256=intent.version.projection.sha256,
                artifacts=[
                    dict(role=a.role, **a.reference.model_dump(mode="json"))
                    for a in intent.artifacts
                ],
            )
        )
        refs = tuple(
            {a.reference.sha256: a.reference for a in intent.artifacts}.values()
        )
    if (
        run.slot_id != expected_slot
        or run.request_fingerprint != expected_fingerprint
        or run.manifest != refs
    ):
        raise UnverifiedBinding("prepared manifest or request fingerprint mismatch")
    if isinstance(intent, PublicationIntent):
        _publication_proof(store, run, intent)
    return intent


def _publication_proof(store, run, intent):
    """Recheck persisted receipt/graph/projection evidence without invoking parsers."""
    from src.content_store.adapters import ImplementationEvidence

    named = {a.role: a.reference for a in intent.artifacts}
    data = {
        role: _available(store, run.run_id, named[role])
        for role in (
            "payload",
            "projection",
            "binding",
            "receipt",
            "plan",
            "implementation",
            "quality",
        )
    }
    evidence = ImplementationEvidence.model_validate(_json(data["implementation"]))
    config = intent.config
    raw = intent.source_version.manifest.artifacts[0]
    if (
        evidence.parser_name != config.parser_name
        or evidence.parser_version != config.parser_version
        or evidence.parameters != config.parameters
        or evidence.implementation_revision != config.implementation_revision
        or evidence.source_id != run.source_id
        or evidence.raw_sha256 != raw.sha256
        or evidence.payload_sha256 != intent.version.payload.sha256
        or evidence.receipt_sha256 != named["receipt"].sha256
    ):
        raise UnverifiedBinding("prepared implementation evidence mismatch")
    projection = _json(data["projection"])
    canonical(projection)
    if (
        projection.get("slot_id") != run.slot_id
        or projection.get("binding_sha256") != intent.source_version.binding_sha256
    ):
        raise UnverifiedBinding("prepared projection binding mismatch")
    expected = [b.model_dump(mode="json") for b in intent.blocks]
    actual = projection.get("blocks", [])
    if config.adapter_version == "cs50_srt_content_v1":
        from src.model_transcribe.data_transcribe import TranscriptDocument
        from src.tools_lecture.adapt_cs50 import CS50AdapterPlan, CS50TranscriptBinding

        binding = CS50TranscriptBinding.model_validate(_json(data["binding"]))
        plan = CS50AdapterPlan.model_validate(_json(data["plan"]))
        if (
            not any(binding in course.bindings for course in plan.courses)
            or evidence.binding_id != binding.source_id
        ):
            raise UnverifiedBinding("prepared SRT plan binding mismatch")
        document = TranscriptDocument.model_validate(_json(data["payload"]))
        receipt = _json(data["receipt"])
        tasks = [
            t
            for c in plan.courses
            for t in c.tasks
            if t.resource_id == binding.resource_id
        ]
        records = {}
        for task in tasks:
            action = task.task.actions[0].value
            record = dict(
                status="done",
                action=action,
                sha256=raw.sha256
                if action == "download"
                else intent.version.payload.sha256,
            )
            if action == "parse_subtitle":
                record["input_sha256"] = raw.sha256
            records[task.task_id] = record
        if len(records) != 2 or receipt != dict(
            schema_version=1, binding=binding.model_dump(mode="json"), actions=records
        ):
            raise UnverifiedBinding("prepared SRT receipt mismatch")
        if (
            document.source != str(binding.raw_srt_path)
            or document.language != binding.language
            or document.provenance is None
            or document.provenance.source_url != binding.transcript_url
            or document.provenance.source_file != str(binding.raw_srt_path)
            or document.provenance.language != binding.language
            or document.provenance.media_id != binding.media_id
            or document.provenance.media_format != "srt"
            or document.provenance.transcript_source.value != "official_subtitle"
        ):
            raise UnverifiedBinding("prepared SRT provenance mismatch")
        if len(document.segments) != len(expected):
            raise UnverifiedBinding("prepared segment count mismatch")
        for segment, block in zip(document.segments, intent.blocks, strict=True):
            loc = block.locators[0]
            if (segment.seg_id, segment.text, segment.start, segment.end) != (
                loc.original_segment_id,
                block.text,
                loc.start,
                loc.end,
            ):
                raise UnverifiedBinding("prepared segment projection mismatch")
        for block in actual:
            block["block_id"] = deterministic_id(
                "content_cue_v1",
                intent.version.parsed_version_id,
                str(block["locators"][0]["original_segment_id"]),
            )
    elif config.adapter_version == "cs50_material_content_v1":
        from src.model_materials.materials import (
            ArtifactReceipt,
            MaterialPlan,
            NormalizedDocument,
        )
        from src.model_materials.quality import MaterialQualityReport
        from src.tools_lecture.material_handoff import (
            LectureMaterialHandoff,
            MaterialReview,
        )

        document = NormalizedDocument.model_validate(_json(data["payload"]))
        receipt = ArtifactReceipt.model_validate(_json(data["receipt"]))
        plan = MaterialPlan.model_validate(_json(data["plan"]))
        quality = MaterialQualityReport.model_validate(_json(data["quality"]))
        handoff = LectureMaterialHandoff.model_validate(
            _json(_available(store, run.run_id, named["handoff"]))
        )
        MaterialReview(report=quality, handoff=handoff)
        if (
            document.binding not in plan.materials
            or receipt.binding != document.binding
            or _json(data["binding"]) != document.binding.model_dump(mode="json")
            or receipt.status != "completed"
            or receipt.error
            or receipt.parser != document.parser
            or receipt.raw_sha256 != raw.sha256
            or document.raw_sha256 != raw.sha256
            or receipt.normalized_sha256 != intent.version.payload.sha256
            or evidence.binding_id != document.binding.material_id
            or intent.version.original_document_id != document.document_id
            or document.parser.model_dump(mode="json") != config.parameters
            or handoff.document != document
            or handoff.receipt != receipt
            or handoff.normalized_sha256 != intent.version.payload.sha256
            or handoff.plan_sha256 != named["plan"].sha256
            or not quality.passed
        ):
            raise UnverifiedBinding("prepared material receipt or gate mismatch")
        for key in ("aggregation_units", "excluded_blocks", "alternative_views"):
            if projection.get(key) != handoff.model_dump(mode="json")[key]:
                raise UnverifiedBinding("prepared material aggregation mismatch")
    else:
        raise UnverifiedBinding("unsupported prepared adapter")
    if actual != expected:
        raise UnverifiedBinding("prepared block projection mismatch")


def _staged(store, run_id, ref):
    with store._artifacts.directory(f"staging/{run_id}") as fd:
        return store._artifacts._read_at(fd, ref)


def _available(store, run_id, ref):
    try:
        return store._artifacts.read(ref)
    except FileNotFoundError:
        return _staged(store, run_id, ref)


def _install(store, run_id, ref):
    try:
        store._artifacts.read(ref)
        return
    except FileNotFoundError:
        pass
    # A corrupt installed file NEVER falls back to a staged replacement.
    _staged(store, run_id, ref)
    store._artifacts.install(run_id, ref)


def inspect_recovery(store, *, actor):
    actor = checked_actor(actor)
    with store._maintenance(), store._connection() as db:
        result = []
        for row in db.execute(
            "SELECT data FROM processing_runs WHERE state!='committed' ORDER BY id"
        ):
            run = ProcessingRun.model_validate_json(row[0])
            try:
                store._authorize(db, run.source_id, actor, write=True)
            except Forbidden:
                continue
            if len(result) >= MAX_FILES:
                raise Unavailable("recovery inspection limit")
            result.append(run)
        return tuple(result)


def recover_run(store, run_id, *, actor, action="resume"):
    store._artifacts._run_id(run_id)
    if action not in {"resume", "reject"}:
        raise InvalidInput("explicit recovery action required")
    with (
        exclusive(store, actor) as actor,
        store._artifacts.lock(f"locks/{run_id}.lock", exclusive=True),
    ):
        with store._connection() as db:
            run = _run(db, run_id)
            store._authorize(db, run.source_id, actor, write=True)
            if run.actor != actor.subject:
                raise Forbidden("run ownership required")
        if run.state == "committed":
            with store._connection() as db:
                if run.parsed_version_id:
                    store._parsed(db, run.parsed_version_id, actor)
                for ref in run.manifest:
                    store._read_blob(ref, db)
            return RecoveryResult(
                run_id=run_id,
                outcome="already_committed",
                parsed_version_id=run.parsed_version_id,
            )
        if run.state == "rejected":
            return RecoveryResult(
                run_id=run_id, outcome="rejected", reason=run.error_code
            )
        if action == "reject":
            with store._connection(write=True) as db:
                store._update_run(
                    db, run, state="rejected", error_code="operator_abandoned"
                )
            return RecoveryResult(
                run_id=run_id, outcome="rejected", reason="operator_abandoned"
            )
        try:
            if run.state not in {"prepared", "blocked"} or not run.manifest:
                raise UnverifiedBinding("incomplete preparation remains blocked")
            intent = _intent(store, run)
            for ref in run.manifest:
                _available(store, run_id, ref)
            for ref in run.manifest:
                _install(store, run_id, ref)
            with store._connection(write=True) as db:
                source = store._authorize(db, run.source_id, actor, write=True)
                if source.acl_revision != run.acl_revision:
                    raise Forbidden("source permissions changed during import")
                if isinstance(intent, RawIntent):
                    store._commit_raw(db, run, intent.reference, actor)
                elif isinstance(intent, BindingIntent):
                    from src.content_store.publication import finish_binding

                    finish_binding(store, db, run, intent, actor)
                else:
                    from src.content_store.publication import finish_publication

                    finish_publication(store, db, run, intent, actor)
            return RecoveryResult(
                run_id=run_id,
                outcome="committed",
                parsed_version_id=intent.version.parsed_version_id
                if isinstance(intent, PublicationIntent)
                else None,
            )
        except Conflict:
            with store._connection(write=True) as db:
                store._update_run(db, run, state="rejected", error_code="conflict")
            raise
        except (OSError, ValidationError, ValueError, ContentStoreError) as error:
            with store._connection(write=True) as db:
                store._update_run(
                    db, run, state="blocked", error_code="recovery_incomplete"
                )
            if isinstance(error, Forbidden):
                raise
            return RecoveryResult(
                run_id=run_id, outcome="blocked", reason="recovery_incomplete"
            )


def _incident(store, value):
    incident_id = uuid.uuid4().hex
    data = canonical(dict(schema_version=1, incident_id=incident_id, **value))
    with store._artifacts.directory("incidents", create=True) as fd:
        from src.content_store.limits import capacity

        if len(tuple(directory_entries(fd))) >= MAX_FILES:
            raise Unavailable("incident retention capacity exceeded")
        capacity(fd, len(data))
        out = os.open(
            incident_id + ".json",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=fd,
        )
        try:
            with os.fdopen(out, "wb", closefd=False) as stream:
                stream.write(data)
                stream.flush()
                _sync(out)
        finally:
            os.close(out)
        _sync(fd)
    return incident_id


def _metadata(store, db):
    """Validate serialized contracts AND their SQL projections; never repair them."""
    from src.content_store import schema

    count = sum(
        db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
        for name in schema.TABLES
    )
    if count > MAX_METADATA_ROWS:
        raise Unavailable("metadata verification limit")
    sources = {}
    for row in db.execute("SELECT * FROM sources"):
        item = Source.model_validate_json(row["data"])
        if (
            item.source_id,
            item.owner_subject,
            item.registration.course_id,
            item.registration.identity_namespace,
            item.registration.external_identity,
            item.publication_seq,
        ) != (
            row["id"],
            row["owner"],
            row["course_id"],
            row["namespace"],
            row["external_id"],
            row["publication_seq"],
        ):
            raise IntegrityError("source metadata mismatch")
        sources[item.source_id] = item
    configs = {}
    for row in db.execute("SELECT * FROM parser_configs"):
        item = ParserConfiguration.model_validate_json(row["data"])
        if item.config_id != row["id"]:
            raise IntegrityError("parser identity mismatch")
        configs[item.config_id] = item
    for row in db.execute("SELECT * FROM parsed_documents"):
        if (
            ParsedDocument(
                source_id=row["source_id"], representation_key=row["representation_key"]
            ).parsed_document_id
            != row["id"]
        ):
            raise IntegrityError("document identity mismatch")
    versions = {}
    for row in db.execute("SELECT * FROM source_versions"):
        item = SourceVersion.model_validate_json(row["data"])
        if (
            item.source_version_id,
            item.source_id,
            item.variant_key,
            item.manifest.digest,
            item.publication_seq,
        ) != (
            row["id"],
            row["source_id"],
            row["variant_key"],
            row["manifest_sha256"],
            row["publication_seq"],
        ):
            raise IntegrityError("source version metadata mismatch")
        raw = db.execute(
            "SELECT data FROM source_raw_artifacts WHERE source_version_id=? ORDER BY role,ordinal",
            (item.source_version_id,),
        ).fetchall()
        if [json.loads(r[0]) for r in raw] != [
            a.model_dump(mode="json") for a in item.manifest.artifacts
        ]:
            raise IntegrityError("raw manifest references mismatch")
        versions[item.source_version_id] = item
    for row in db.execute("SELECT * FROM parsed_versions"):
        v = ParsedDocumentVersion.model_validate_json(row["data"])
        if (
            v.parsed_version_id,
            v.source_id,
            v.parsed_document_id,
            v.source_version_id,
            v.slot_id,
            v.parser_config_id,
            v.payload.sha256,
            v.projection.sha256,
            v.publication_seq,
        ) != tuple(
            row[k]
            for k in (
                "id",
                "source_id",
                "document_id",
                "source_version_id",
                "slot_id",
                "parser_config_id",
                "payload_sha256",
                "projection_sha256",
                "publication_seq",
            )
        ):
            raise IntegrityError("parsed metadata mismatch")
        if (
            v.payload_schema != configs[v.parser_config_id].payload_schema
            or versions[v.source_version_id].source_id != v.source_id
        ):
            raise IntegrityError("parsed lineage mismatch")
        blocks = []
        for b in db.execute(
            "SELECT * FROM content_blocks WHERE version_id=? ORDER BY block_order",
            (v.parsed_version_id,),
        ):
            block = ContentBlock.model_validate_json(b["data"])
            if (block.block_id, block.order, block.text_sha256) != (
                b["id"],
                b["block_order"],
                b["text_sha256"],
            ):
                raise IntegrityError("block projection mismatch")
            locations = db.execute(
                "SELECT * FROM content_locators WHERE version_id=? AND block_id=? ORDER BY ordinal",
                (v.parsed_version_id, block.block_id),
            ).fetchall()
            if len(locations) != len(block.locators):
                raise IntegrityError("locator count mismatch")
            for i, (loc, stored) in enumerate(
                zip(block.locators, locations, strict=True)
            ):
                if loc.model_dump(mode="json") != json.loads(stored["data"]) or (
                    i,
                    loc.raw_artifact_sha256,
                    loc.time_status,
                    loc.start,
                    loc.end,
                ) != (
                    stored["ordinal"],
                    stored["raw_sha256"],
                    stored["time_status"],
                    stored["start"],
                    stored["end"],
                ):
                    raise IntegrityError("locator projection mismatch")
                if loc.raw_artifact_sha256 not in {
                    a.sha256 for a in versions[v.source_version_id].manifest.artifacts
                }:
                    raise IntegrityError("locator raw binding mismatch")
            blocks.append(block)
        if [b.order for b in blocks] != list(range(len(blocks))):
            raise IntegrityError("block order mismatch")
        try:
            projection = _json(store._artifacts.read(v.projection))
        except (OSError, ContentStoreError):
            continue  # Physical corruption is attributed/quarantined by scan.
        canonical(projection)
        expected = [b.model_dump(mode="json") for b in blocks]
        actual = projection.get("blocks", [])
        if configs[v.parser_config_id].adapter_version == "cs50_srt_content_v1":
            for block in actual:
                block["block_id"] = deterministic_id(
                    "content_cue_v1",
                    v.parsed_version_id,
                    str(block["locators"][0]["original_segment_id"]),
                )
        if projection.get("slot_id") != v.slot_id or actual != expected:
            raise IntegrityError("stored projection disagrees with SQL blocks")
    runs = []
    for row in db.execute("SELECT * FROM processing_runs"):
        r = ProcessingRun.model_validate_json(row["data"])
        if r.retry_of is not None:
            from src.content_store.store import _retry_parent

            try:
                _retry_parent(db, r)
            except Conflict:
                raise IntegrityError("stored retry lineage conflict") from None
        if (
            r.run_id,
            r.source_id,
            r.actor,
            r.request_key,
            r.request_fingerprint,
            r.slot_id,
            r.kind,
            r.state,
        ) != tuple(
            row[k]
            for k in (
                "id",
                "source_id",
                "actor",
                "request_key",
                "fingerprint",
                "slot_id",
                "kind",
                "state",
            )
        ) or sources[r.source_id].owner_subject != r.actor:
            raise IntegrityError("run/source ownership mismatch")
        runs.append(r)
    return versions, runs


def scan(store, db):
    """Under exclusive maintenance. Bounded complete reference walk."""
    if [r[0] for r in db.execute("PRAGMA integrity_check")] != ["ok"] or db.execute(
        "PRAGMA foreign_key_check"
    ).fetchone():
        raise IntegrityError("content database integrity failed")
    try:
        versions, runs = _metadata(store, db)
    except (ValidationError, ValueError, KeyError, TypeError, AttributeError):
        raise IntegrityError("stored content contract invalid") from None
    findings, bad, count, total = [], set(), 0, 0
    for row in db.execute("SELECT * FROM artifacts ORDER BY sha256"):
        count += 1
        total += row["size_bytes"]
        if count > MAX_FILES or total > MAX_STORE_BYTES:
            raise Unavailable("content verification size limit")
        ref = ArtifactReference(
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
            mime_type="application/octet-stream",
        )
        try:
            store._artifacts.read(
                ref
            )  # Quarantine flags are checked separately, never cleared.
        except (OSError, ContentStoreError):
            bad.add(ref.sha256)
    if db.execute("SELECT purpose FROM metadata WHERE id=1").fetchone()[0] == "content":
        for version in versions.values():
            if (
                db.execute(
                    "SELECT 1 FROM artifacts WHERE sha256=?", (version.binding_sha256,)
                ).fetchone()
                is None
            ):
                raise IntegrityError("verified source binding catalog missing")
    for digest in sorted(bad):
        sv = {
            v.source_version_id
            for v in versions.values()
            if v.binding_sha256 == digest
            or any(a.sha256 == digest for a in v.manifest.artifacts)
        }
        pv = {
            r[0]
            for r in db.execute(
                "SELECT DISTINCT version_id FROM artifact_references WHERE sha256=? AND version_id IS NOT NULL",
                (digest,),
            )
        }
        pv.update(
            r[0]
            for r in db.execute(
                "SELECT id FROM parsed_versions WHERE payload_sha256=? OR projection_sha256=?",
                (digest, digest),
            )
        )
        affected_runs = set()
        for run in runs:
            if run.recovery is not None and run.recovery.sha256 == digest:
                affected_runs.add(run.run_id)
                if run.parsed_version_id:
                    pv.add(run.parsed_version_id)
                else:
                    hashes = {a.sha256 for a in run.manifest}
                    sv.update(
                        v.source_version_id
                        for v in versions.values()
                        if v.source_id == run.source_id
                        and (
                            v.binding_sha256 in hashes
                            or any(a.sha256 in hashes for a in v.manifest.artifacts)
                        )
                    )
        if sv:
            pv.update(
                r[0]
                for r in db.execute("SELECT id,source_version_id FROM parsed_versions")
                if r[1] in sv
            )
        findings.append(
            IntegrityFinding(
                code="artifact_unavailable",
                artifact_sha256=digest,
                source_version_ids=tuple(sorted(sv)),
                parsed_version_ids=tuple(sorted(pv)),
                run_ids=tuple(sorted(affected_runs)),
            )
        )
    with store._artifacts.directory("staging") as staged:
        entries = tuple(directory_entries(staged))
        if len(entries) > MAX_FILES:
            raise Unavailable("staging inspection limit")
        known = {r.run_id for r in runs}
        for name in entries:
            if name not in known:
                findings.append(IntegrityFinding(code="unowned_staging"))
            try:
                with store._artifacts.directory("staging/" + name):
                    pass
            except (OSError, ContentStoreError):
                findings.append(IntegrityFinding(code="unsafe_staging"))
    for run in runs:
        if run.state in {"prepared", "blocked"}:
            try:
                for ref in run.manifest:
                    _available(store, run.run_id, ref)
                if run.recovery:
                    _intent(store, run, db)
            except (OSError, ValueError, ContentStoreError):
                findings.append(
                    IntegrityFinding(
                        code="run_evidence_unavailable", run_ids=(run.run_id,)
                    )
                )
        if run.state == "committed":
            if run.recovery and not any(
                ref.sha256 in bad for ref in run.manifest + (run.recovery,)
            ):
                try:
                    _intent(store, run, db)
                except (ValueError, ContentStoreError, KeyError):
                    raise IntegrityError(
                        "committed verification intention mismatch"
                    ) from None
            for ref in run.manifest + ((run.recovery,) if run.recovery else ()):
                row = db.execute(
                    "SELECT size_bytes FROM artifacts WHERE sha256=?", (ref.sha256,)
                ).fetchone()
                if row is None or row[0] != ref.size_bytes:
                    raise IntegrityError("committed run artifact catalog mismatch")
    return findings, count


def _quarantine(store, db, findings, count):
    incident = None
    if findings:
        incident = _incident(
            store,
            dict(
                kind="integrity", findings=[f.model_dump(mode="json") for f in findings]
            ),
        )
        for f in findings:
            if f.artifact_sha256:
                db.execute(
                    "UPDATE artifacts SET state='quarantined' WHERE sha256=?",
                    (f.artifact_sha256,),
                )
            for sid in f.source_version_ids:
                db.execute(
                    "UPDATE source_versions SET state='quarantined' WHERE id=?", (sid,)
                )
            for pid in f.parsed_version_ids:
                db.execute(
                    "UPDATE parsed_versions SET state='quarantined' WHERE id=? AND state!='tombstoned'",
                    (pid,),
                )
        db.execute(
            "UPDATE metadata SET collection_revision=collection_revision+1 WHERE id=1"
        )
    return IntegrityReport(
        findings=tuple(findings),
        checked_artifacts=count,
        incident_id=incident,
        quarantined_artifacts=db.execute(
            "SELECT count(*) FROM artifacts WHERE state='quarantined'"
        ).fetchone()[0],
        quarantined_source_versions=db.execute(
            "SELECT count(*) FROM source_versions WHERE state='quarantined'"
        ).fetchone()[0],
        quarantined_parsed_versions=db.execute(
            "SELECT count(*) FROM parsed_versions WHERE state='quarantined'"
        ).fetchone()[0],
    )


def verify_integrity(store, *, actor):
    with exclusive(store, actor) as actor, store._connection(write=True) as db:
        authorize_all(store, db, actor)
        try:
            findings, count = scan(store, db)
        except IntegrityError:
            _incident(store, dict(kind="metadata_integrity", code="integrity_error"))
            with store._artifacts.directory() as fd:
                marker = os.open(
                    ".content-recovery-required",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=fd,
                )
                os.close(marker)
                _sync(fd)
            raise
        return _quarantine(store, db, findings, count)


def recover_database(root, *, actor):
    """Explicit WAL recovery before normal opening. Ambiguity leaves a durable fence."""
    actor = checked_actor(actor)
    if actor.role != "operator":
        raise Forbidden("operator database recovery required")
    store = object.__new__(ContentStore)
    store._artifacts = _Artifacts(root)
    store.root, store.read_only = store._artifacts.root, False
    db = None
    try:
        with (
            exclusive(store, actor),
            store._artifacts.lock(".content-db.lock", exclusive=True),
        ):
            with store._artifacts.directory() as fd:
                if ".content-recovery-required" in directory_entries(fd):
                    raise Unavailable(
                        "previous ambiguous recovery requires isolated restore"
                    )
                files = {}
                for suffix in ("", "-wal", "-shm", "-journal"):
                    try:
                        file = os.open(
                            "content.sqlite3" + suffix, FILE_FLAGS, dir_fd=fd
                        )
                    except FileNotFoundError:
                        continue
                    try:
                        info = _private(file)
                        if info.st_size > MAX_STORE_BYTES:
                            raise Unavailable("database recovery size limit")
                        files[suffix] = info.st_size
                    finally:
                        os.close(file)
                if files.get("-journal", 0):
                    raise Unavailable("hot rollback journal recovery is not supported")
                wal_size = files.get("-wal", 0)
                physical_frames = 0
                if wal_size:
                    with (store.root / "content.sqlite3-wal").open("rb") as wal:
                        header = wal.read(32)
                    if len(header) != 32 or int.from_bytes(header[:4], "big") not in (
                        0x377F0682,
                        0x377F0683,
                    ):
                        raise Unavailable(
                            "invalid WAL header; isolated restore required"
                        )
                    page = int.from_bytes(header[8:12], "big")
                    if (
                        page < 512
                        or page > 65536
                        or page & (page - 1)
                        or (wal_size - 32) % (page + 24)
                    ):
                        raise Unavailable("ambiguous WAL frame layout")
                    physical_frames = (wal_size - 32) // (page + 24)
            # SQLite's read-only WAL view is used to authorize the recovered source set.
            db = sqlite3.connect(
                (store.root / "content.sqlite3").as_uri() + "?mode=ro",
                uri=True,
                timeout=2,
            )
            db.row_factory = sqlite3.Row
            ContentStore._validate(db)
            authorize_all(store, db, actor)
            store._purpose = db.execute(
                "SELECT purpose FROM metadata WHERE id=1"
            ).fetchone()[0]
            with store._artifacts.directory() as fd:
                marker = os.open(
                    ".content-recovery-required",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=fd,
                )
                os.write(
                    marker,
                    b"Explicit SQLite recovery in progress; do not remove manually.\n",
                )
                _sync(marker)
                os.close(marker)
                _sync(fd)
            # Preserve engine input for diagnosis before SQLite can checkpoint/close it.
            _incident(store, dict(kind="wal_recovery", files=files))
            writer = sqlite3.connect(
                (store.root / "content.sqlite3").as_uri() + "?mode=rw",
                uri=True,
                timeout=2,
            )
            try:
                writer.row_factory = sqlite3.Row
                writer.execute("PRAGMA foreign_keys=ON")
                writer.execute("PRAGMA synchronous=FULL")
                writer.execute("PRAGMA busy_timeout=2000")
                result = writer.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
                # Reject ignored/truncated/corrupt or uncommitted tails instead of guessing.
                if wal_size and (
                    result[0] or result[1] != physical_frames or result[2] != result[1]
                ):
                    raise Unavailable("SQLite could not account for every WAL frame")
                ContentStore._validate(writer)
                findings, count = scan(store, writer)
                report = _quarantine(store, writer, findings, count)
                writer.commit()
                db.close()
                db = None
                if writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
                    raise Busy("SQLite WAL checkpoint busy")
            finally:
                writer.close()
            with store._artifacts.directory() as fd:
                os.unlink(".content-recovery-required", dir_fd=fd)
                _sync(fd)
            return report
    except (OSError, sqlite3.Error, ValueError):
        raise Unavailable("database recovery could not establish consistency") from None
    finally:
        if db is not None:
            db.close()
