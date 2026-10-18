"""Real ContentStore/adapter gates, synthetic bytes only. No runtime services."""

import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.content_store._testing import project_synthetic_for_index, publish_synthetic
from src.content_store.adapters import (
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import (
    Busy,
    Forbidden,
    IntegrityError,
    InvalidInput,
    NotFound,
)
from src.content_store.index_models import (
    IndexProjectionConfig,
    IndexProjectionResult,
    IndexRecord,
    record_set_sha256,
)
from src.content_store.index_projection import (
    IndexProjectionError,
    project_content_for_index,
)
from src.content_store.models import (
    ContentBlock,
    SourceGrant,
    canonical,
    sha256,
)
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from tests.content_adapter_support import material, srt
from tests.content_store_support import OTHER, OWNER, VIEWER, config, payload, seeded


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def no_network(*a, **kw):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)


def published(tmp_path, kind="html"):
    bundle, doc = material(tmp_path, kind)
    store = ContentStore.initialize(tmp_path / "store")
    version = import_verified_bundle(
        store,
        verify_material_bundle(bundle),
        actor=OWNER,
        request_key="projection-test",
    ).version
    return store, version, bundle, doc


def inventory(root):
    return {
        str(p.relative_to(root)): (p.stat().st_mode, sha256(p.read_bytes()))
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("kind", ["html", "code", "pdf"])
def test_verified_materials_repeat_exact_bytes_and_exclusions(
    tmp_path, kind, monkeypatch
):
    store, version, bundle, doc = published(tmp_path, kind)
    before = inventory(tmp_path)
    # Existing payload has already passed the adapter: projection must not reparse.
    from src.tools_lecture import material_handoff
    from src.tools_materials import parse_html

    monkeypatch.setattr(
        material_handoff,
        "prepare_material_handoff",
        lambda **kw: pytest.fail("no gate reparse"),
    )
    monkeypatch.setattr(
        parse_html, "parse_html", lambda *a, **kw: pytest.fail("no raw parse")
    )
    first = store.project_content_for_index(version.parsed_version_id, actor=OWNER)
    again = project_content_for_index(
        ContentStore(store.root), version.parsed_version_id, actor=OWNER
    )
    assert first == again
    assert IndexProjectionResult.model_validate_json(first.model_dump_json()) == first
    assert (
        first.body.usage == "verified_content"
        and first.body.source_origin == "synthetic"
    )
    assert first.body.error_count == 0 and first.body.record_count == len(
        first.body.records
    )
    originals = {b.block_id: b for b in doc.blocks}
    for record in first.body.records:
        b, body = originals[record.body.block_id], record.body
        assert body.search_text == b.text[body.start : body.end]
        assert body.text_sha256 == sha256(b.text.encode())
        assert body.search_text_sha256 == sha256(body.search_text.encode())
        assert record.build_id is record.generation_id is None
        assert str(tmp_path) not in record.model_dump_json()
    if kind == "pdf":
        assert [r.body.content_type for r in first.body.records] == ["code"]
        assert first.body.records[0].body.search_text == doc.blocks[0].text
        assert first.body.records[0].body.search_text != doc.blocks[0].data["code_view"]
        assert {x.reason for x in first.body.exclusions} == {
            "alternative_view",
            "geometric_table_projection",
            "non_text_reference",
        }
    assert inventory(tmp_path) == before
    # The original workspace is not needed once the store publication is verified.
    monkeypatch.setattr(
        Path, "read_bytes", lambda *a: pytest.fail("must use scoped store descriptors")
    )
    assert (
        project_content_for_index(
            ContentStore(store.root), version.parsed_version_id, actor=OWNER
        )
        == first
    )


def test_srt_exact_cues_and_overlapping_original_times(tmp_path):
    bundle, doc = srt(tmp_path)
    store = ContentStore.initialize(tmp_path / "store")
    version = import_verified_bundle(
        store, verify_srt_bundle(bundle), actor=OWNER, request_key="srt"
    ).version
    result = project_content_for_index(
        store,
        version.parsed_version_id,
        actor=OWNER,
        config=IndexProjectionConfig(schema_version=1, max_codepoints=5),
    )
    assert len(result.body.records) > 2
    for record in result.body.records:
        b = record.body
        loc = b.locators[0]
        cue = next(s for s in doc.segments if s.seg_id == loc.original_segment_id)
        assert b.search_text == cue.text[b.start : b.end]
        assert (loc.start, loc.end, loc.time_status) == (cue.start, cue.end, "known")
        assert b.block_id.startswith("content_cue_v1:")
    assert doc.segments[0].end > doc.segments[1].start


def synthetic(tmp_path, *, text="A😀é\r\n\t  x + − y²  "):
    store, source, ref, sv = seeded(tmp_path)
    data = payload(ref.sha256, text=text)
    version = publish_synthetic(
        store, sv.source_version_id, data, config(), actor=OWNER
    ).version
    return store, version, json.loads(data)


def test_synthetic_isolated_unknown_time_formula_unicode_and_code(tmp_path):
    store, version, original = synthetic(tmp_path)
    with pytest.raises(Forbidden):
        project_content_for_index(store, version.parsed_version_id, actor=OWNER)
    cfg = IndexProjectionConfig(schema_version=1, max_codepoints=3)
    result = project_synthetic_for_index(
        store, version.parsed_version_id, actor=OWNER, config=cfg
    )
    assert result.body.usage == "synthetic_test_only"
    for block in original["blocks"]:
        values = [
            r.body for r in result.body.records if r.body.block_id == block["block_id"]
        ]
        if block["aggregation_role"] == "primary":
            # Reconstruct from anchors, including intentionally excluded pure whitespace.
            rebuilt = [None] * len(block["text"])
            for b in values:
                rebuilt[b.start : b.end] = b.search_text
            for exclusion in result.body.exclusions:
                if (
                    exclusion.block_id == block["block_id"]
                    and exclusion.start is not None
                ):
                    rebuilt[exclusion.start : exclusion.end] = block["text"][
                        exclusion.start : exclusion.end
                    ]
            assert "".join(rebuilt) == block["text"]
        if block["type"] in {"code", "formula"}:
            assert all(
                loc.time_status == "unknown" and loc.start is loc.end is None
                for b in values
                for loc in b.locators
            )
    assert result.body.records[0].body.offset_unit == "unicode_codepoint"
    # Synthetic null times are infrastructure only; no TXT publication adapter.
    assert all(
        r.body.locators[0].start is None
        for r in result.body.records
        if r.body.content_type == "formula"
    )


def test_max_windows_overlap_and_configuration_identity(tmp_path):
    store, version, original = synthetic(tmp_path, text="word 😀 + x\n" * 450)
    cfg = IndexProjectionConfig(
        schema_version=1, max_codepoints=200, overlap_codepoints=128
    )
    result = project_synthetic_for_index(
        store, version.parsed_version_id, actor=OWNER, config=cfg
    )
    values = [r.body for r in result.body.records if r.body.block_order == 1]
    assert len(values) > 2 and values[1].start == 72
    assert all(b.end - b.start <= 200 for b in values)
    text = original["blocks"][1]["text"]
    rebuilt = values[0].search_text
    for left, right in zip(values, values[1:], strict=False):
        assert left.search_text[-128:] == right.search_text[:128]
        rebuilt += right.search_text[128:]
    assert rebuilt == text
    changed = project_synthetic_for_index(
        store,
        version.parsed_version_id,
        actor=OWNER,
        config=IndexProjectionConfig(
            schema_version=1, max_codepoints=201, overlap_codepoints=128
        ),
    )
    assert result.digest != changed.digest
    assert {r.index_record_id for r in result.body.records}.isdisjoint(
        r.index_record_id for r in changed.body.records
    )


@pytest.mark.parametrize(
    "value",
    [
        {"schema_version": 2},
        {"schema_version": 1, "max_codepoints": True},
        {"schema_version": 1, "max_codepoints": 2001},
        {"schema_version": 1, "overlap_codepoints": 1},
        {"schema_version": 1, "max_codepoints": 128, "overlap_codepoints": 128},
        {"schema_version": 1, "extra": True},
    ],
)
def test_invalid_configuration(value):
    with pytest.raises(ValidationError):
        IndexProjectionConfig.model_validate(value)


def test_acl_live_grants_roles_course_and_revocation(tmp_path):
    store, version, _, _ = published(tmp_path)
    vid = version.parsed_version_id
    for actor in [
        OTHER,
        VIEWER,
        Principal(subject=OWNER.subject, role="operator", courses=()),
    ]:
        with pytest.raises(Forbidden):
            project_content_for_index(store, vid, actor=actor)
    with pytest.raises(Forbidden):
        project_content_for_index(store, vid, actor="owner")
    store.set_source_grants(
        version.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert project_content_for_index(
        store, vid, actor=VIEWER
    ) == project_content_for_index(store, vid, actor=OWNER)
    store.set_source_grants(version.source_id, (), expected_acl_revision=1, actor=OWNER)
    with pytest.raises(Forbidden):
        project_content_for_index(store, vid, actor=VIEWER)


def corrupt_db(store, sql, args=()):
    with sqlite3.connect(store.root / "content.sqlite3") as db:
        triggers = list(
            db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        )
        for (name,) in triggers:
            db.execute('DROP TRIGGER "' + name + '"')
        db.execute(sql, args)
    # Return exact schema so tests exercise scoped content verification, not DDL checks.
    from src.content_store.schema import TRIGGERS

    with sqlite3.connect(store.root / "content.sqlite3") as db:
        for text in TRIGGERS.values():
            db.execute(text)
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")


@pytest.mark.parametrize(
    "target",
    ["source", "source_version", "parsed_quarantine", "parsed_tombstone", "artifact"],
)
def test_status_excludes_content(tmp_path, target):
    store, v, _, _ = published(tmp_path)
    operations = {
        "source": ("UPDATE sources SET state='tombstoned' WHERE id=?", v.source_id),
        "source_version": (
            "UPDATE source_versions SET state='quarantined' WHERE id=?",
            v.source_version_id,
        ),
        "parsed_quarantine": (
            "UPDATE parsed_versions SET state='quarantined' WHERE id=?",
            v.parsed_version_id,
        ),
        "parsed_tombstone": (
            "UPDATE parsed_versions SET state='tombstoned' WHERE id=?",
            v.parsed_version_id,
        ),
        "artifact": (
            "UPDATE artifacts SET state='quarantined' WHERE sha256=?",
            v.projection.sha256,
        ),
    }
    sql, arg = operations[target]
    with store._maintenance(), store._connection(write=True) as db:
        db.execute(sql, (arg,))
    with pytest.raises((Forbidden, NotFound)):
        project_content_for_index(store, v.parsed_version_id, actor=OWNER)


@pytest.mark.parametrize(
    "role", ["payload", "projection", "handoff", "binding", "receipt"]
)
def test_missing_or_wrong_bytes_rejected(tmp_path, role):
    store, v, _, _ = published(tmp_path)
    with store._maintenance(), store._connection() as db:
        digest = db.execute(
            "SELECT sha256 FROM artifact_references WHERE version_id=? AND role=?",
            (v.parsed_version_id, role),
        ).fetchone()[0]
    path = store.root / f"blobs/sha256/{digest[:2]}/{digest}"
    path.write_bytes(b"corrupted")
    with pytest.raises(IntegrityError):
        project_content_for_index(
            ContentStore(store.root), v.parsed_version_id, actor=OWNER
        )


@pytest.mark.parametrize("field", ["text", "order", "locator", "text_hash"])
def test_sql_projection_and_locator_binding_rejected(tmp_path, field):
    store, v, _, _ = published(tmp_path)
    if field == "locator":
        corrupt_db(
            store,
            "UPDATE content_locators SET raw_sha256=? WHERE version_id=?",
            (v.payload.sha256, v.parsed_version_id),
        )
    elif field == "text_hash":
        corrupt_db(
            store,
            "UPDATE content_blocks SET text_sha256=? WHERE version_id=?",
            ("0" * 64, v.parsed_version_id),
        )
    else:
        with store._maintenance(), store._connection() as db:
            row = db.execute(
                "SELECT id,data FROM content_blocks WHERE version_id=? ORDER BY block_order LIMIT 1",
                (v.parsed_version_id,),
            ).fetchone()
        b = json.loads(row[1])
        b["text" if field == "text" else "order"] = "changed" if field == "text" else 99
        corrupt_db(
            store,
            "UPDATE content_blocks SET data=? WHERE version_id=? AND id=?",
            (json.dumps(b), v.parsed_version_id, row[0]),
        )
    with pytest.raises(IntegrityError):
        project_content_for_index(store, v.parsed_version_id, actor=OWNER)


def test_budget_and_no_partial_result(tmp_path, monkeypatch):
    store, v, _, _ = published(tmp_path)
    from src.content_store import index_projection as module

    monkeypatch.setattr(module, "MAX_SNAPSHOT_BYTES", 1)
    with pytest.raises(IndexProjectionError, match="projection_limit"):
        project_content_for_index(store, v.parsed_version_id, actor=OWNER)


def test_result_and_record_tampering_rejected(tmp_path):
    store, v, _, _ = published(tmp_path)
    result = project_content_for_index(store, v.parsed_version_id, actor=OWNER)
    value = result.model_dump(mode="json")
    value["body"]["record_count"] += 1
    with pytest.raises(ValidationError):
        IndexProjectionResult.model_validate(value)
    value = result.body.records[0].model_dump(mode="json")
    value["body"]["start"] += 1
    with pytest.raises(ValidationError):
        IndexRecord.model_validate(value)
    with pytest.raises(ValueError):
        record_set_sha256([result.body.records[0]] * 2)
    record = result.body.records[0]
    data = canonical(
        dict(
            index_record_id=record.index_record_id,
            body=record.body.model_dump(mode="json"),
        )
    )
    assert (
        record_set_sha256([record])
        == hashlib.sha256(str(len(data)).encode() + b":" + data).hexdigest()
    )


def test_process_restart_and_other_working_directory(tmp_path):
    store, v, original = synthetic(tmp_path)
    # Process restart reads an existing store; cannot initialize/promote a test store.
    script = "from src.content_store._testing import project_synthetic_for_index;from src.content_store.store import ContentStore;from tests.content_store_support import OWNER;import sys;print(project_synthetic_for_index(ContentStore(sys.argv[1]),sys.argv[2],actor=OWNER).digest)"
    expected = project_synthetic_for_index(
        store, v.parsed_version_id, actor=OWNER
    ).digest
    env = {
        k: val
        for k, val in os.environ.items()
        if k not in {"OPENAI_API_KEY", "QDRANT_API_KEY"}
    }
    for cwd in [Path.cwd(), tmp_path]:
        env["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parents[1]), "/usr/lib/python3/dist-packages"]
        )
        completed = subprocess.run(
            [sys.executable, "-c", script, str(store.root), v.parsed_version_id],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        assert completed.stdout.strip() == expected


def test_more_than_100_blocks_are_complete(tmp_path):
    from src.content_store._testing import SyntheticPayload

    store, _, ref, sv = seeded(tmp_path)
    base = json.loads(payload(ref.sha256))["blocks"][0]
    blocks = []
    for i in range(125):
        value = json.loads(json.dumps(base))
        value.update(
            block_id=f"synthetic-block:{i}",
            order=i,
            payload_pointer=f"/blocks/{i}",
            text=f"Text {i}",
        )
        value["locators"][0]["origin_pointer"] = f"/blocks/{i}"
        blocks.append(ContentBlock.model_validate(value))
    data = SyntheticPayload(blocks=tuple(blocks)).model_dump_json().encode()
    v = publish_synthetic(
        store, sv.source_version_id, data, config(), actor=OWNER
    ).version
    result = project_synthetic_for_index(store, v.parsed_version_id, actor=OWNER)
    assert result.body.record_count == 125
    assert [r.body.block_order for r in result.body.records] == list(range(125))


def test_new_raw_sourceversion_and_text_are_distinct(tmp_path):
    from src.content_store._testing import register_synthetic_version
    from src.content_store.models import RawArtifact, RawManifest
    from tests.content_store_support import raw

    store, v, _ = synthetic(tmp_path, text="original")
    first = project_synthetic_for_index(store, v.parsed_version_id, actor=OWNER)
    ref = raw(store, v.source_id, data=b"new synthetic original")
    sv = register_synthetic_version(
        store,
        v.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=OWNER,
    )
    second_v = publish_synthetic(
        store,
        sv.source_version_id,
        payload(ref.sha256, text="changed"),
        config(),
        actor=OWNER,
        request_key="next",
    ).version
    second = project_synthetic_for_index(store, second_v.parsed_version_id, actor=OWNER)
    assert first.body.source_id == second.body.source_id
    assert first.body.source_version_id != second.body.source_version_id
    assert {r.index_record_id for r in first.body.records}.isdisjoint(
        r.index_record_id for r in second.body.records
    )
    assert (
        first.body.records[1].body.text_sha256
        != second.body.records[1].body.text_sha256
    )


@pytest.mark.parametrize("change", ["duplicate", "missing", "excluded", "view"])
def test_aggregation_references_must_equal_persisted_handoff(tmp_path, change):
    from src.content_store.index_projection import _load, _selection

    store, v, _, _ = published(tmp_path)
    with store._maintenance(), store._connection() as db:
        source, sv, version, parser, blocks, projection, artifacts = _load(
            store, db, v.parsed_version_id, OWNER, False
        )
        if change == "duplicate":
            projection["aggregation_units"].append(projection["aggregation_units"][0])
        if change == "missing":
            projection["aggregation_units"].pop()
        if change == "excluded":
            projection["excluded_blocks"] = {}
        if change == "view":
            projection["alternative_views"].append("blocks.0.data.code_view")
        with pytest.raises(IndexProjectionError, match="aggregation_binding"):
            _selection(
                source, sv, version, parser, blocks, projection, artifacts, False
            )


def test_unsafe_metadata_rejected_and_unrelated_data_not_exported(tmp_path):
    from src.content_store._testing import SyntheticPayload

    store, _, ref, sv = seeded(tmp_path)
    value = json.loads(payload(ref.sha256))
    value["blocks"][0]["data"] = {
        "secret": "not-exported",
        "host": "/home/private/input",
    }
    data = SyntheticPayload.model_validate(value).model_dump_json().encode()
    v = publish_synthetic(
        store, sv.source_version_id, data, config(), actor=OWNER
    ).version
    result = project_synthetic_for_index(store, v.parsed_version_id, actor=OWNER)
    assert (
        "not-exported" not in result.model_dump_json()
        and "/home/private" not in result.model_dump_json()
    )
    value["blocks"][0]["locators"][0]["dom"] = "/home/private/input"
    v2 = publish_synthetic(
        store,
        sv.source_version_id,
        SyntheticPayload.model_validate(value).model_dump_json().encode(),
        config(implementation_revision="synthetic-revision-2"),
        actor=OWNER,
        request_key="unsafe",
    ).version
    with pytest.raises(IndexProjectionError, match="unsafe_metadata"):
        project_synthetic_for_index(store, v2.parsed_version_id, actor=OWNER)


def test_projection_holds_acl_writer_lock(tmp_path, monkeypatch):
    store, v, _, _ = published(tmp_path)
    from src.content_store import index_projection as module

    original = module._records

    def during(*args, **kwargs):
        with pytest.raises(Busy):
            store.set_source_grants(
                v.source_id,
                (SourceGrant(subject=VIEWER.subject),),
                expected_acl_revision=0,
                actor=OWNER,
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "_records", during)
    assert project_content_for_index(
        store, v.parsed_version_id, actor=OWNER
    ).body.record_count
    store.set_source_grants(
        v.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )


def test_invalid_schema_types_and_mutated_configuration(tmp_path):
    for value in [{"schema_version": True}, {"schema_version": 1.0}, {}]:
        with pytest.raises(ValidationError):
            IndexProjectionConfig.model_validate(value)
    store, v, _, _ = published(tmp_path)
    broken = IndexProjectionConfig(schema_version=1).model_copy(
        update={"max_codepoints": 0}
    )
    with pytest.raises(InvalidInput):
        project_content_for_index(
            store, v.parsed_version_id, actor=OWNER, config=broken
        )
    with pytest.raises(InvalidInput):
        project_content_for_index(store, v.parsed_version_id, actor=OWNER, config={})
    with pytest.raises(Forbidden):
        project_synthetic_for_index(store, v.parsed_version_id, actor=OWNER)


def test_fachliche_records_in_another_checkout(tmp_path):
    store, v, _ = synthetic(tmp_path)
    expected = project_synthetic_for_index(
        store, v.parsed_version_id, actor=OWNER
    ).digest
    checkout = tmp_path / "other-checkout"
    # Copy repository code only, never source bundles, env files or original materials.
    shutil.copytree(
        Path(__file__).resolve().parents[1] / "src",
        checkout / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    script = (
        "from src.content_store._testing import project_synthetic_for_index;"
        "from src.content_store.store import ContentStore;from src.job_control.models import Principal;"
        "import sys;actor=Principal(subject='owner',role='operator',courses=('cs50_python',));"
        "print(project_synthetic_for_index(ContentStore(sys.argv[1]),sys.argv[2],actor=actor).digest)"
    )
    env = dict(
        os.environ,
        PYTHONPATH="/usr/lib/python3/dist-packages",
        PYTHONDONTWRITEBYTECODE="1",
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(store.root), v.parsed_version_id],
        cwd=checkout,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert result.stdout.strip() == expected


def test_non_resolving_material_pointer_rejected(tmp_path):
    from src.content_store.index_projection import _load, _selection

    store, v, _, _ = published(tmp_path)
    with store._maintenance(), store._connection() as db:
        source, sv, version, parser, blocks, projection, artifacts = _load(
            store, db, v.parsed_version_id, OWNER, False
        )
        b = blocks[0]
        blocks[0] = b.model_copy(
            update={
                "payload_pointer": "/blocks/999",
                "locators": tuple(
                    loc.model_copy(update={"origin_pointer": "/blocks/999"})
                    for loc in b.locators
                ),
            }
        )
        with pytest.raises(IndexProjectionError, match="block_binding"):
            _selection(
                source, sv, version, parser, blocks, projection, artifacts, False
            )
