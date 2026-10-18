"""One scoped read-only ContentStore projection. No parser, backend or file output."""

import re

from pydantic import ValidationError

from src.content_store.errors import Forbidden, IntegrityError, InvalidInput, NotFound
from src.content_store.index_models import (
    MAX_RECORDS,
    MAX_RESULT_BYTES,
    IndexProjectionBody,
    IndexProjectionConfig,
    IndexProjectionResult,
    IndexRecord,
    IndexRecordBody,
    ProjectionExclusion,
    record_set_sha256,
)
from src.content_store.models import (
    MAX_BLOCKS,
    ArtifactReference,
    ContentBlock,
    ContentLocator,
    ParsedDocument,
    ParsedDocumentVersion,
    ParserConfiguration,
    ProcessingRun,
    RawArtifact,
    SourceVersion,
    canonical,
    checked_actor,
    fingerprint,
    sha256,
    snapshot,
)
from src.model_discovery.cs50 import deterministic_id
from src.tools_materials.quality import _json

MAX_SNAPSHOT_BYTES = 128 * 1024**2
MAX_REFERENCES = 20_000


class IndexProjectionError(IntegrityError):
    """Fixed diagnostics only; no partial result, SQL, paths or extracted content."""

    def __init__(self, reason):
        if reason not in {
            "snapshot_binding",
            "block_binding",
            "aggregation_binding",
            "unsupported_adapter",
            "unsafe_metadata",
            "projection_limit",
        }:
            raise ValueError("unknown projection error")
        self.reason = reason
        super().__init__(reason)


def _require(condition, reason="snapshot_binding"):
    if not condition:
        raise IndexProjectionError(reason)


def project_content_for_index(store, parsed_version_id, *, actor, config=None):
    """Project a verified publication under one existing maintenance/DB snapshot.

    Reader grants authorize this read only. They never authorize a future build
    or retrieval; those operations must recheck current rights independently.
    """
    return _project(
        store, parsed_version_id, actor=actor, config=config, synthetic=False
    )


def _project(store, version_id, *, actor, config, synthetic):
    from src.content_store.store import ContentStore

    actor = checked_actor(actor)
    if not isinstance(store, ContentStore) or not isinstance(version_id, str):
        raise InvalidInput("typed store and version identity required")
    if not version_id or len(version_id) > 200:
        raise InvalidInput("bounded version identity required")
    if config is None:
        config = IndexProjectionConfig(schema_version=1)
    if not isinstance(config, IndexProjectionConfig):
        raise InvalidInput("typed index projection configuration required")
    try:
        config = snapshot(config)
    except ValidationError:
        raise InvalidInput("invalid index projection configuration") from None
    expected_purpose = "synthetic_test" if synthetic else "content"
    if store._purpose != expected_purpose:
        raise Forbidden("projection store purpose denied")
    try:
        with store._maintenance(), store._connection() as db:
            _require(
                db.execute("SELECT purpose FROM metadata WHERE id=1").fetchone()[0]
                == expected_purpose
            )
            source, sv, version, parser, blocks, projection, artifacts = _load(
                store, db, version_id, actor, synthetic
            )
            intervals, excluded, alternatives = _selection(
                source, sv, version, parser, blocks, projection, artifacts, synthetic
            )
            return _records(
                source,
                sv,
                version,
                parser,
                blocks,
                intervals,
                excluded,
                alternatives,
                config,
                synthetic,
            )
    except IndexProjectionError:
        raise
    except (
        ValidationError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        UnicodeError,
        RecursionError,
    ):
        raise IndexProjectionError("snapshot_binding") from None


def _load(store, db, version_id, actor, synthetic):
    row = db.execute(
        "SELECT * FROM parsed_versions WHERE id=? AND state='published'", (version_id,)
    ).fetchone()
    if row is None:
        raise NotFound("parsed version unavailable")
    source = store._authorize(db, row["source_id"], actor)
    src = db.execute("SELECT * FROM sources WHERE id=?", (source.source_id,)).fetchone()
    _require(
        src is not None
        and (
            src["id"],
            src["course_id"],
            src["owner"],
            src["namespace"],
            src["external_id"],
        )
        == (
            source.source_id,
            source.registration.course_id,
            source.owner_subject,
            source.registration.identity_namespace,
            source.registration.external_identity,
        )
    )
    version = ParsedDocumentVersion.model_validate_json(row["data"])
    expected = (
        version.parsed_version_id,
        version.source_id,
        version.source_version_id,
        version.parsed_document_id,
        version.slot_id,
        version.parser_config_id,
        version.payload.sha256,
        version.projection.sha256,
        version.publication_seq,
    )
    _require(
        tuple(
            row[k]
            for k in (
                "id",
                "source_id",
                "source_version_id",
                "document_id",
                "slot_id",
                "parser_config_id",
                "payload_sha256",
                "projection_sha256",
                "publication_seq",
            )
        )
        == expected
    )
    _require(
        version.source_id == source.source_id
        and (version.quality_status == "synthetic_test_only") == synthetic
    )
    if synthetic:
        _require(
            source.registration.source_origin == "synthetic"
            and source.registration.source_type == "synthetic"
            and source.registration.identity_namespace.startswith("synthetic:")
        )
    svrow = db.execute(
        "SELECT * FROM source_versions WHERE id=? AND source_id=? AND state='verified'",
        (version.source_version_id, source.source_id),
    ).fetchone()
    if svrow is None:
        raise NotFound("source version unavailable")
    sv = SourceVersion.model_validate_json(svrow["data"])
    _require(
        (
            sv.source_version_id,
            sv.source_id,
            sv.variant_key,
            sv.manifest.digest,
            sv.publication_seq,
        )
        == tuple(
            svrow[k]
            for k in (
                "id",
                "source_id",
                "variant_key",
                "manifest_sha256",
                "publication_seq",
            )
        )
    )
    parserrow = db.execute(
        "SELECT data FROM parser_configs WHERE id=?", (version.parser_config_id,)
    ).fetchone()
    streamrow = db.execute(
        "SELECT * FROM parsed_documents WHERE id=?", (version.parsed_document_id,)
    ).fetchone()
    _require(parserrow is not None and streamrow is not None)
    parser = ParserConfiguration.model_validate_json(parserrow[0])
    stream = ParsedDocument(
        source_id=streamrow["source_id"],
        representation_key=streamrow["representation_key"],
    )
    _require(
        parser.config_id == version.parser_config_id
        and parser.payload_schema == version.payload_schema
        and stream.parsed_document_id == version.parsed_document_id
        and stream.source_id == source.source_id
    )

    # Every referenced artifact is state/size/SHA checked once, under the same locks.
    cache, consumed = {}, 0

    def read(ref):
        nonlocal consumed
        known = db.execute(
            "SELECT size_bytes,state FROM artifacts WHERE sha256=?", (ref.sha256,)
        ).fetchone()
        _require(known is not None and known[0] == ref.size_bytes)
        if known[1] != "available":
            raise NotFound("version artifact unavailable")
        if ref.sha256 not in cache:
            consumed += ref.size_bytes
            _require(consumed <= MAX_SNAPSHOT_BYTES, "projection_limit")
            cache[ref.sha256] = store._read_blob(ref, db)
        return cache[ref.sha256]

    rawrows = db.execute(
        "SELECT * FROM source_raw_artifacts WHERE source_version_id=? ORDER BY role,ordinal",
        (sv.source_version_id,),
    ).fetchall()
    _require(len(rawrows) == len(sv.manifest.artifacts))
    for rawrow, ref in zip(rawrows, sv.manifest.artifacts, strict=True):
        _require(
            rawrow["source_id"] == source.source_id
            and (rawrow["role"], rawrow["ordinal"], rawrow["sha256"])
            == (ref.role, ref.ordinal, ref.sha256)
            and RawArtifact.model_validate_json(rawrow["data"]) == ref
        )
        reservation = db.execute(
            "SELECT data FROM raw_reservations WHERE source_id=? AND sha256=?",
            (source.source_id, ref.sha256),
        ).fetchone()
        _require(
            reservation is not None
            and ArtifactReference.model_validate_json(reservation[0])
            == ArtifactReference(**ref.model_dump(exclude={"role", "ordinal"}))
        )
        read(ref)
    payload = read(version.payload)
    projection = _json(read(version.projection))
    canonical(projection)
    _require(
        projection.get("schema_version") == 1
        and projection.get("slot_id") == version.slot_id
    )
    references = db.execute(
        "SELECT a.*,r.state AS run_state,r.source_id AS run_source "
        "FROM artifact_references a JOIN processing_runs r ON r.id=a.run_id "
        "WHERE a.version_id=? ORDER BY a.rowid LIMIT ?",
        (version_id, MAX_REFERENCES + 1),
    ).fetchall()
    _require(0 < len(references) <= MAX_REFERENCES, "projection_limit")
    first_run, artifacts, runs = references[0]["run_id"], {}, {}
    for item in references:
        if item["run_id"] not in runs:
            run_data = db.execute(
                "SELECT data FROM processing_runs WHERE id=?", (item["run_id"],)
            ).fetchone()[0]
            consumed += len(run_data.encode("utf-8"))
            _require(consumed <= MAX_SNAPSHOT_BYTES, "projection_limit")
            runs[item["run_id"]] = ProcessingRun.model_validate_json(run_data)
        _require(
            item["run_state"] == "committed"
            and item["run_source"] == source.source_id
            and runs[item["run_id"]].parsed_version_id == version_id
            and item["ordinal"] == 0
        )
        ref = ArtifactReference.model_validate_json(item["data"])
        _require(item["sha256"] == ref.sha256)
        data = read(ref)
        if item["run_id"] == first_run:
            _require(item["role"] not in artifacts)
            artifacts[item["role"]] = data
    _require(
        artifacts.get("payload") == payload
        and artifacts.get("projection") == read(version.projection)
    )
    if not synthetic:
        bindingrow = db.execute(
            "SELECT size_bytes FROM artifacts WHERE sha256=?", (sv.binding_sha256,)
        ).fetchone()
        _require(bindingrow is not None)
        binding = read(
            ArtifactReference(
                sha256=sv.binding_sha256,
                size_bytes=bindingrow[0],
                mime_type="application/json",
            )
        )
        _require(
            artifacts.get("binding") == binding
            and {"receipt", "plan", "implementation", "quality"} <= artifacts.keys()
        )
    artifacts["payload"] = payload
    blocks = _blocks(db, version, sv, parser, projection)
    return source, sv, version, parser, blocks, projection, artifacts


def _blocks(db, version, sv, parser, projection):
    rows = db.execute(
        "SELECT * FROM content_blocks WHERE version_id=? ORDER BY block_order LIMIT ?",
        (version.parsed_version_id, MAX_BLOCKS + 1),
    ).fetchall()
    _require(len(rows) <= MAX_BLOCKS, "projection_limit")
    blocks = [ContentBlock.model_validate_json(r["data"]) for r in rows]
    _require(
        [b.order for b in blocks] == list(range(len(blocks)))
        and len({b.block_id for b in blocks}) == len(blocks),
        "block_binding",
    )
    actual = projection.get("blocks")
    _require(isinstance(actual, list) and len(actual) == len(blocks), "block_binding")
    if parser.adapter_version == "cs50_srt_content_v1":
        actual = [
            dict(
                b,
                block_id=deterministic_id(
                    "content_cue_v1",
                    version.parsed_version_id,
                    str(b["locators"][0]["original_segment_id"]),
                ),
            )
            for b in actual
        ]
    _require(actual == [b.model_dump(mode="json") for b in blocks], "block_binding")
    raw_hashes = {r.sha256 for r in sv.manifest.artifacts}
    for row, b in zip(rows, blocks, strict=True):
        _require(
            (row["id"], row["block_order"], row["text_sha256"])
            == (b.block_id, b.order, b.text_sha256),
            "block_binding",
        )
        locrows = db.execute(
            "SELECT * FROM content_locators WHERE version_id=? AND block_id=? ORDER BY ordinal",
            (version.parsed_version_id, b.block_id),
        ).fetchall()
        _require(len(locrows) == len(b.locators), "block_binding")
        for i, (locrow, loc) in enumerate(zip(locrows, b.locators, strict=True)):
            _require(
                (
                    locrow["ordinal"],
                    locrow["raw_sha256"],
                    locrow["time_status"],
                    locrow["start"],
                    locrow["end"],
                )
                == (i, loc.raw_artifact_sha256, loc.time_status, loc.start, loc.end)
                and ContentLocator.model_validate_json(locrow["data"]) == loc
                and loc.raw_artifact_sha256 in raw_hashes
                and loc.origin_pointer == b.payload_pointer,
                "block_binding",
            )
    return blocks


def _selection(source, sv, version, parser, blocks, projection, artifacts, synthetic):
    intervals, excluded, alternatives = {}, {}, set()
    if synthetic:
        from src.content_store._testing import SyntheticPayload

        _require(
            parser.adapter_version == "synthetic_fixture_v1"
            and parser.parser_name == "synthetic",
            "unsupported_adapter",
        )
        payload = SyntheticPayload.model_validate(_json(artifacts["payload"]))
        _require(payload.blocks == tuple(blocks), "block_binding")
        for b in blocks:
            if b.aggregation_role == "primary":
                _require(
                    b.type
                    in {"heading", "paragraph", "code", "table", "formula", "list"},
                    "aggregation_binding",
                )
                intervals[b.block_id] = [(0, len(b.text))] if b.text else []
            else:
                excluded[b.block_id] = "non_text_reference"
        return intervals, excluded, alternatives
    _require(projection.get("adapter_version") == parser.adapter_version)
    if parser.adapter_version == "cs50_material_content_v1":
        from src.model_materials.materials import NormalizedDocument
        from src.tools_lecture.material_handoff import LectureMaterialHandoff

        doc = NormalizedDocument.model_validate(_json(artifacts["payload"]))
        handoff = LectureMaterialHandoff.model_validate(_json(artifacts["handoff"]))
        _require(
            handoff.document == doc
            and doc.binding.source_id == source.source_id
            and doc.binding.source_origin == source.registration.source_origin
            and doc.binding.resource.course_id == source.registration.course_id
            and doc.raw_sha256 == sv.manifest.artifacts[0].sha256
            and version.original_document_id == doc.document_id
            and parser.parser_name == doc.parser.name
            and parser.parser_version == doc.parser.version
            and parser.parameters == doc.parser.model_dump(mode="json")
        )
        _require(
            _json(artifacts["binding"]) == doc.binding.model_dump(mode="json")
            and sv.variant_key == (doc.binding.variant_id or "default")
        )
        for key in ("aggregation_units", "excluded_blocks", "alternative_views"):
            _require(
                projection.get(key) == handoff.model_dump(mode="json")[key],
                "aggregation_binding",
            )
        excluded = dict(handoff.excluded_blocks)
        alternatives = {b.block_id for b in doc.blocks if "code_view" in b.data}
        for unit in handoff.aggregation_units:
            intervals.setdefault(unit.block.block_id, []).append(
                (unit.char_start, unit.char_end)
            )
        _require(len(doc.blocks) == len(blocks), "block_binding")
        for original, b in zip(doc.blocks, blocks, strict=True):
            _require(b.payload_pointer == f"/blocks/{b.order}", "block_binding")
            _require(
                (b.block_id, b.order, b.text, b.data, b.original_type, b.type)
                == (
                    original.block_id,
                    original.order,
                    original.text,
                    original.data,
                    original.type,
                    "formula" if original.type == "math" else original.type,
                ),
                "block_binding",
            )
            _require(
                b.locators
                == (
                    ContentLocator(
                        raw_artifact_sha256=doc.raw_sha256,
                        origin_pointer=b.payload_pointer,
                        **original.location.model_dump(),
                        time_status="not_applicable",
                    ),
                ),
                "block_binding",
            )
    elif parser.adapter_version == "cs50_srt_content_v1":
        from src.model_transcribe.data_transcribe import TranscriptDocument
        from src.tools_lecture.adapt_cs50 import CS50TranscriptBinding

        binding = CS50TranscriptBinding.model_validate(_json(artifacts["binding"]))
        doc = TranscriptDocument.model_validate(_json(artifacts["payload"]))
        _require(
            binding.source_id == source.source_id
            and binding.course_id == source.registration.course_id
            and binding.language == sv.variant_key == doc.language
            and doc.source == str(binding.raw_srt_path)
            and doc.provenance is not None
            and doc.provenance.source_file == str(binding.raw_srt_path)
        )
        _require(len(doc.segments) == len(blocks) and parser.parser_name == "srt")
        units = []
        for i, (segment, b) in enumerate(zip(doc.segments, blocks, strict=True)):
            _require(
                (b.text, b.payload_pointer, b.original_type, b.type)
                == (segment.text, f"/segments/{i}", "srt_cue", "paragraph"),
                "block_binding",
            )
            _require(
                len(b.locators) == 1
                and (
                    b.locators[0].original_segment_id,
                    b.locators[0].start,
                    b.locators[0].end,
                    b.locators[0].time_status,
                )
                == (segment.seg_id, segment.start, segment.end, "known"),
                "block_binding",
            )
            units.append(
                dict(order=b.order, payload_pointer=b.payload_pointer, text=b.text)
            )
            intervals[b.block_id] = [(0, len(b.text))] if b.text else []
        _require(projection.get("aggregation_units") == units, "aggregation_binding")
    else:
        raise IndexProjectionError("unsupported_adapter")
    for b in blocks:
        reason = excluded.get(b.block_id)
        role = (
            "primary"
            if intervals.get(b.block_id)
            else "reference_projection"
            if reason
            in {
                "table_of_contents",
                "reference_projection",
                "geometric_table_projection",
            }
            else "structure"
            if reason == "list_structure"
            else "non_text_reference"
        )
        # Empty SRT cues are still primary, but produce an explicit empty exclusion.
        if parser.adapter_version == "cs50_srt_content_v1":
            role = "primary"
        _require(b.aggregation_role == role, "aggregation_binding")
    return intervals, excluded, alternatives


def _safe_metadata(block, source, sv, version, parser):
    identifiers = (
        block.block_id,
        source.source_id,
        sv.source_version_id,
        version.parsed_version_id,
        parser.config_id,
    )
    _require(
        all(re.fullmatch(r"[A-Za-z0-9_:.-]+", x) for x in identifiers),
        "unsafe_metadata",
    )
    _require(
        re.fullmatch(r"[a-z][a-z0-9_]{0,63}", block.original_type) is not None,
        "unsafe_metadata",
    )
    for loc in block.locators:
        if loc.dom is not None:
            _require(
                re.fullmatch(
                    r"/(?:[A-Za-z][A-Za-z0-9:_-]*\[[1-9][0-9]*\])(?:/[A-Za-z][A-Za-z0-9:_-]*\[[1-9][0-9]*\])*",
                    loc.dom,
                )
                is not None,
                "unsafe_metadata",
            )
        from src.content_store.read_views import label

        _require(
            label(loc.coordinate_system) is not None
            and all(label(x) is not None for x in loc.chapter_path),
            "unsafe_metadata",
        )


def _records(
    source,
    sv,
    version,
    parser,
    blocks,
    intervals,
    excluded,
    alternatives,
    config,
    synthetic,
):
    records, omissions, size = [], [], 0
    for block in blocks:
        _safe_metadata(block, source, sv, version, parser)
        ranges = intervals.get(block.block_id, [])
        if not ranges:
            omissions.append(
                ProjectionExclusion(
                    block_id=block.block_id,
                    block_order=block.order,
                    reason=excluded.get(block.block_id, "empty_text"),
                )
            )
        if block.block_id in alternatives:
            omissions.append(
                ProjectionExclusion(
                    block_id=block.block_id,
                    block_order=block.order,
                    reason="alternative_view",
                )
            )
        end_seen = -1
        merged = []
        for a, b in sorted(ranges):
            _require(
                type(a) is int
                and type(b) is int
                and 0 <= a < b <= len(block.text)
                and a >= end_seen,
                "aggregation_binding",
            )
            if merged and a == end_seen:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
            end_seen = b
        for start, stop in merged:
            while start < stop:
                end = min(start + config.max_codepoints, stop)
                text = block.text[start:end]
                if not text.strip():
                    omissions.append(
                        ProjectionExclusion(
                            block_id=block.block_id,
                            block_order=block.order,
                            reason="whitespace_window",
                            start=start,
                            end=end,
                        )
                    )
                else:
                    body = IndexRecordBody(
                        schema_version=1,
                        index_schema="content_index_record_v1",
                        source_id=source.source_id,
                        source_version_id=sv.source_version_id,
                        parsed_version_id=version.parsed_version_id,
                        course_id=source.registration.course_id,
                        block_id=block.block_id,
                        block_order=block.order,
                        content_type=block.type,
                        original_type=block.original_type,
                        aggregation_role="primary",
                        origin_pointer=block.payload_pointer,
                        text_sha256=block.text_sha256,
                        text_length=len(block.text),
                        start=start,
                        end=end,
                        offset_unit="unicode_codepoint",
                        search_text=text,
                        search_text_sha256=sha256(text.encode("utf-8")),
                        locators=block.locators,
                        parser_config_id=parser.config_id,
                        parser_fingerprint=fingerprint(parser.model_dump(mode="json")),
                        payload_sha256=version.payload.sha256,
                        projection_sha256=version.projection.sha256,
                        projection_policy_id=config.policy_id,
                    )
                    record = IndexRecord(
                        schema_version=1, body=body, index_record_id=body.record_id
                    )
                    size += len(canonical(record.model_dump(mode="json")))
                    _require(
                        len(records) < MAX_RECORDS and size <= MAX_RESULT_BYTES // 2,
                        "projection_limit",
                    )
                    records.append(record)
                if end == stop:
                    break
                start = end - config.overlap_codepoints
    body = IndexProjectionBody(
        schema_version=1,
        projection_version="content_index_projection_v1",
        status="projected",
        usage="synthetic_test_only" if synthetic else "verified_content",
        source_origin=source.registration.source_origin,
        source_id=source.source_id,
        source_version_id=sv.source_version_id,
        parsed_version_id=version.parsed_version_id,
        parser_config_id=parser.config_id,
        payload_sha256=version.payload.sha256,
        projection_sha256=version.projection.sha256,
        config=config,
        config_fingerprint=fingerprint(config.model_dump(mode="json")),
        record_count=len(records),
        exclusion_count=len(omissions),
        error_count=0,
        record_set_sha256=record_set_sha256(records),
        records=tuple(records),
        exclusions=tuple(omissions),
    )
    return IndexProjectionResult(
        schema_version=1, body=body, digest=fingerprint(body.model_dump(mode="json"))
    )
