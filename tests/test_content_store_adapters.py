"""Real file + SQLite adapter verification, synthetic bundles only, no network."""

import json
import socket

import pytest

from src.content_store.adapters import (
    VerifiedPublicationCandidate,
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import Conflict, Forbidden, Unavailable, UnverifiedBinding
from src.content_store.models import SourceGrant, sha256
from src.content_store.store import ContentStore
from src.model_discovery.cs50 import deterministic_id
from tests.content_adapter_support import attest, dump, material, srt
from tests.content_store_support import OTHER, OWNER, VIEWER


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.mark.parametrize("kind", ["html", "pdf", "code"])
def test_material_end_to_end_restart(tmp_path, kind):
    bundle, doc = material(tmp_path, kind, local_image=kind == "html")
    originals = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    candidate = verify_material_bundle(bundle)
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(store, candidate, actor=OWNER, request_key="first")
    assert result.created
    vid = result.version.parsed_version_id
    reopened = ContentStore(store.root)
    assert (
        reopened.read_parsed_payload(vid, actor=OWNER)
        == bundle.normalized_path.read_bytes()
    )
    assert (
        reopened.read_raw_artifact(doc.binding.source_id, doc.raw_sha256, actor=OWNER)
        == bundle.raw_path.read_bytes()
    )
    assert reopened.get_parsed_document(vid, actor=OWNER).payload_sha256 == sha256(
        bundle.normalized_path.read_bytes()
    )
    blocks = reopened.list_content_blocks(vid, actor=OWNER, limit=100).items
    assert [b.block_id for b in blocks] == [b.block_id for b in doc.blocks]
    assert [b.text for b in blocks] == [b.text for b in doc.blocks]
    for b, original in zip(blocks, doc.blocks, strict=True):
        assert b.data == original.data
        for field in ("page", "dom", "bbox", "line_start", "line_end"):
            assert getattr(b.locators[0], field) == getattr(original.location, field)
        assert b.locators[0].coordinate_system == "unknown"
        assert b.locators[0].raw_artifact_sha256 == doc.raw_sha256
    for role, path in (
        ("receipt", bundle.receipt_path),
        ("plan", bundle.plan_path),
        ("implementation", bundle.implementation_path),
    ):
        assert (
            reopened.read_version_artifact(vid, role, actor=OWNER) == path.read_bytes()
        )
    projection = json.loads(
        reopened.read_version_artifact(vid, "projection", actor=OWNER)
    )
    handoff = json.loads(reopened.read_version_artifact(vid, "handoff", actor=OWNER))
    for key in ("aggregation_units", "excluded_blocks", "alternative_views"):
        assert projection[key] == handoff[key]
    assert {u["block"]["block_id"] for u in projection["aggregation_units"]}.isdisjoint(
        projection["excluded_blocks"]
    )
    if kind == "html":
        image = doc.images[0]
        assert (
            reopened.read_version_artifact(vid, f"image:{image.image_id}", actor=OWNER)
            == b"synthetic image"
        )
    if kind == "pdf":
        assert any(b.type == "formula" for b in blocks)
        assert (
            next(b for b in blocks if b.type == "table").aggregation_role
            == "reference_projection"
        )
        code = next(b for b in blocks if b.type == "code")
        assert code.data["code_view"] != code.text
        assert [
            u["text"]
            for u in projection["aggregation_units"]
            if u["block"]["type"] == "code"
        ] == [code.text]
    assert all(p.read_bytes() == data for p, data in originals.items())
    assert not import_verified_bundle(
        store, candidate, actor=OWNER, request_key="first"
    ).created
    assert not import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="again"
    ).created
    assert len(reopened.list_source_versions(doc.binding.source_id, actor=OWNER)) == 1


def test_srt_end_to_end_restart(tmp_path):
    bundle, doc = srt(tmp_path)
    store = ContentStore.initialize(tmp_path / "store")
    candidate = verify_srt_bundle(bundle)
    result = import_verified_bundle(store, candidate, actor=OWNER, request_key="srt")
    vid = result.version.parsed_version_id
    reopened = ContentStore(store.root)
    assert (
        reopened.read_parsed_payload(vid, actor=OWNER)
        == bundle.transcript_path.read_bytes()
    )
    blocks = reopened.list_content_blocks(vid, actor=OWNER).items
    assert len(blocks) == len(doc.segments) == 2
    assert "\n" in blocks[0].text and "Ä" in blocks[0].text
    assert blocks[1].locators[0].start < blocks[0].locators[0].end
    for b, seg in zip(blocks, doc.segments, strict=True):
        assert b.text == seg.text
        assert (
            b.locators[0].original_segment_id,
            b.locators[0].start,
            b.locators[0].end,
        ) == (seg.seg_id, seg.start, seg.end)
        assert b.block_id == deterministic_id("content_cue_v1", vid, str(seg.seg_id))
    assert (
        reopened.read_version_artifact(vid, "receipt", actor=OWNER)
        == bundle.receipt_path.read_bytes()
    )
    assert not import_verified_bundle(
        store, verify_srt_bundle(bundle), actor=OWNER, request_key="srt2"
    ).created


@pytest.mark.parametrize(
    "target",
    ["raw_path", "normalized_path", "receipt_path", "plan_path", "implementation_path"],
)
def test_material_corrupt_bytes(tmp_path, target):
    bundle, _ = material(tmp_path)
    getattr(bundle, target).write_bytes(b"corrupt")
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)


@pytest.mark.parametrize(
    "target",
    ["raw_path", "transcript_path", "receipt_path", "plan_path", "implementation_path"],
)
def test_srt_corrupt_bytes(tmp_path, target):
    bundle, _ = srt(tmp_path)
    getattr(bundle, target).write_bytes(b"corrupt")
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle)


@pytest.mark.parametrize(
    "change", ["segment", "time", "text", "source", "language", "provenance"]
)
def test_rehashed_transcript_still_reparsed(tmp_path, change):
    bundle, _ = srt(tmp_path)
    value = json.loads(bundle.transcript_path.read_bytes())
    if change == "segment":
        value["segments"][0]["text"] = "forged"
    elif change == "time":
        value["segments"][0]["start"] = 0.5
    elif change == "text":
        value["text"] = "forged"
    elif change == "source":
        value["source"] = "data/Harvard/forged.srt"
    elif change == "language":
        value["language"] = "de"
    else:
        value["provenance"]["source_url"] = "https://example.invalid"
    dump(bundle.transcript_path, value)
    receipt = json.loads(bundle.receipt_path.read_bytes())
    for record in receipt["actions"].values():
        if record["action"] == "parse_subtitle":
            record["sha256"] = sha256(bundle.transcript_path.read_bytes())
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle)


@pytest.mark.parametrize(
    "change", ["input", "task", "action", "source", "lecture", "extra", "state"]
)
def test_receipt_invariants(tmp_path, change):
    bundle, _ = srt(tmp_path)
    value = json.loads(bundle.receipt_path.read_bytes())
    parse = next(
        v for v in value["actions"].values() if v["action"] == "parse_subtitle"
    )
    if change == "input":
        parse["input_sha256"] = "0" * 64
    elif change == "task":
        value["actions"]["forged"] = value["actions"].pop(next(iter(value["actions"])))
    elif change == "action":
        parse["action"] = "download"
    elif change in {"source", "lecture"}:
        value["binding"][f"{change}_id"] = "resource:forged"
    elif change == "extra":
        value["actions"]["extra"] = parse.copy()
    else:
        parse["status"] = "prepared"
    dump(bundle.receipt_path, value)
    attest(bundle)
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle)


@pytest.mark.parametrize("missing", [True, False])
def test_implementation_required(tmp_path, missing):
    bundle, _ = srt(tmp_path)
    if missing:
        bundle.implementation_path.unlink()
    else:
        value = json.loads(bundle.implementation_path.read_bytes())
        value["parameters"]["preserve_empty_cues"] = False
        dump(bundle.implementation_path, value)
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle)


def test_historical_path_conflict_is_not_adopted(tmp_path):
    bundle, _ = srt(tmp_path)
    historical = bundle.workspace / bundle.raw_path.relative_to(
        bundle.workspace
    ).as_posix().replace("data/lectures/", "data/", 1)
    historical.parent.mkdir(parents=True)
    bundle.raw_path.rename(historical)
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle)
    with pytest.raises(UnverifiedBinding):
        verify_srt_bundle(bundle.model_copy(update={"raw_path": historical}))


@pytest.mark.parametrize("missing", [True, False])
def test_declared_image_required(tmp_path, missing):
    bundle, _ = material(tmp_path, local_image=True)
    image = bundle.normalized_path.parent / "images/local.bin"
    if missing:
        image.unlink()
    else:
        image.write_bytes(b"changed")
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)


def test_frozen_bytes_not_live_paths(tmp_path):
    bundle, _ = material(tmp_path)
    original = bundle.normalized_path.read_bytes()
    candidate = verify_material_bundle(bundle)
    bundle.normalized_path.write_bytes(b"forged after validation")
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(store, candidate, actor=OWNER, request_key="frozen")
    assert (
        store.read_parsed_payload(result.version.parsed_version_id, actor=OWNER)
        == original
    )


def test_same_slot_conflict_and_new_parser_revision(tmp_path):
    bundle, _ = material(tmp_path)
    store = ContentStore.initialize(tmp_path / "store")
    first = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    value = json.loads(bundle.normalized_path.read_bytes())
    value["title"] = "Another title"
    dump(bundle.normalized_path, value)
    receipt = json.loads(bundle.receipt_path.read_bytes())
    receipt["normalized_sha256"] = sha256(bundle.normalized_path.read_bytes())
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    with pytest.raises(Conflict):
        import_verified_bundle(
            store, verify_material_bundle(bundle), actor=OWNER, request_key="conflict"
        )
    attest(bundle, revision="b" * 40)
    second = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="newparser"
    )
    assert (
        second.created
        and second.version.source_version_id == first.version.source_version_id
    )
    assert second.version.parser_config_id != first.version.parser_config_id


def test_permissions_on_every_read_and_write(tmp_path):
    bundle, doc = material(tmp_path)
    candidate = verify_material_bundle(bundle)
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(store, candidate, actor=OWNER, request_key="first")
    vid = result.version.parsed_version_id
    for actor in (OTHER, VIEWER):
        with pytest.raises(Forbidden):
            import_verified_bundle(store, candidate, actor=actor, request_key="bad")
        with pytest.raises(Forbidden):
            store.read_version_artifact(vid, "receipt", actor=actor)
    store.set_source_grants(
        doc.binding.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert (
        store.read_version_artifact(vid, "receipt", actor=VIEWER)
        == bundle.receipt_path.read_bytes()
    )
    with pytest.raises(Forbidden):
        import_verified_bundle(store, candidate, actor=VIEWER, request_key="viewer")


@pytest.mark.parametrize("failure", ["acl", "abort"])
def test_before_commit_no_partial_publication(tmp_path, monkeypatch, failure):
    bundle, doc = material(tmp_path)
    candidate = verify_material_bundle(bundle)
    store = ContentStore.initialize(tmp_path / "store")
    original = store._prepared

    def hook(run, refs, actor):
        original(run, refs, actor)
        if run.slot_id.startswith("content_slot_v1:"):
            if failure == "abort":
                raise OSError("controlled interruption")
            store.set_source_grants(
                doc.binding.source_id, (), expected_acl_revision=0, actor=OWNER
            )

    monkeypatch.setattr(store, "_prepared", hook)
    with pytest.raises((Forbidden, Unavailable)):
        import_verified_bundle(store, candidate, actor=OWNER, request_key="interrupted")
    with store._connection() as db:
        assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM content_blocks").fetchone()[0] == 0


def test_no_caller_approval_flags(tmp_path):
    with pytest.raises(UnverifiedBinding):
        VerifiedPublicationCandidate()
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle({"verified": True})
    store = ContentStore.initialize(tmp_path / "store")
    with pytest.raises(Unavailable):
        store.publish_parsed_document(
            "anything", {"verified": True}, actor=OWNER, request_key="bad"
        )
    forged = object.__new__(VerifiedPublicationCandidate)
    with pytest.raises(UnverifiedBinding):
        import_verified_bundle(store, forged, actor=OWNER, request_key="bad")


@pytest.mark.parametrize(
    "target", ["raw_path", "normalized_path", "plan_path", "implementation_path"]
)
def test_symlinks_rejected(tmp_path, target):
    bundle, _ = material(tmp_path)
    path = getattr(bundle, target)
    other = path.with_name(path.name + ".real")
    path.rename(other)
    path.symlink_to(other)
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)


def test_material_parameter_mismatch_and_limit(tmp_path):
    bundle, _ = material(tmp_path)
    value = json.loads(bundle.receipt_path.read_bytes())
    value["parser"]["max_blocks"] = 100
    dump(bundle.receipt_path, value)
    attest(bundle)
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)


def test_changed_parser_configuration_is_separate_version(tmp_path):
    bundle, first_doc = material(tmp_path / "first")
    other, second_doc = material(tmp_path / "second", max_blocks=19000)
    store = ContentStore.initialize(tmp_path / "store")
    first = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    second = import_verified_bundle(
        store, verify_material_bundle(other), actor=OWNER, request_key="second"
    )
    assert first.version.source_version_id == second.version.source_version_id
    assert first.version.parsed_document_id == second.version.parsed_document_id
    assert first.version.parser_config_id != second.version.parser_config_id
    assert first_doc.document_id != second_doc.document_id
    assert first.version.original_document_id == first_doc.document_id
    assert second.version.original_document_id == second_doc.document_id


def test_reference_only_image_and_recomputed_gate(tmp_path):
    bundle, _ = material(tmp_path)
    prior = tmp_path / "prior.json"
    prior.write_bytes(b'{"status":"passed","verified":true}')
    bundle = bundle.model_copy(update={"prior_quality_path": prior})
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    vid = result.version.parsed_version_id
    report = json.loads(store.read_version_artifact(vid, "quality", actor=OWNER))
    assert any(f["code"] == "image_reference_only" for f in report["findings"])
    assert report["inputs"]["workspace"] == "."
    assert set(report["inputs"]) == {
        "workspace",
        "normalized",
        "receipt",
        "raw",
        "plan",
    }
    assert (
        store.read_version_artifact(vid, "prior_quality", actor=OWNER)
        == prior.read_bytes()
    )
    bundle.raw_path.write_bytes(b"changed")
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)


def test_import_without_settings_inference_or_knowledge(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = """import importlib.abc, sys, socket
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, name, *args):
  if name.startswith(('src.tools_knowledge', 'src.model_knowledge', 'src.core.config')) or name.split('.')[0] in {'pydantic_settings','openai','torch','pymupdf','fitz','bs4'}: raise AssertionError(name)
def forbidden(*a, **k): raise AssertionError('network')
socket.socket.connect = forbidden
socket.getaddrinfo = forbidden
sys.meta_path.insert(0, Guard())
from src.content_store.adapters import verify_srt_bundle, SRTBundle, verify_material_bundle, MaterialBundle
verify_srt_bundle(SRTBundle.model_validate_json(sys.argv[1]))
verify_material_bundle(MaterialBundle.model_validate_json(sys.argv[2]))
"""
    sbundle, _ = srt(tmp_path / "srt-input")
    mbundle, _ = material(tmp_path / "html-input")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            sbundle.model_dump_json(),
            mbundle.model_dump_json(),
        ],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_read_only_publication_does_not_stage(tmp_path, monkeypatch):
    bundle, _ = material(tmp_path)
    candidate = verify_material_bundle(bundle)
    store = ContentStore.initialize(tmp_path / "store")
    readonly = ContentStore(store.root)

    def forbidden(*a, **kw):
        raise AssertionError("read-only publication must not stage")

    monkeypatch.setattr("src.content_store.adapters._verify_frozen", forbidden)
    with pytest.raises(Forbidden):
        import_verified_bundle(readonly, candidate, actor=OWNER, request_key="bad")
    with pytest.raises(Forbidden):
        readonly.publish_parsed_document(
            "anything", candidate, actor=OWNER, request_key="bad"
        )


def test_new_audit_receipt_does_not_rewrite_published_version(tmp_path):
    bundle, _ = material(tmp_path)
    store = ContentStore.initialize(tmp_path / "store")
    original_receipt = bundle.receipt_path.read_bytes()
    first = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    bundle.receipt_path.write_bytes(original_receipt + b"\n")
    attest(bundle)
    candidate = verify_material_bundle(bundle)
    with pytest.raises(Conflict):
        import_verified_bundle(store, candidate, actor=OWNER, request_key="first")
    second = import_verified_bundle(store, candidate, actor=OWNER, request_key="second")
    assert not second.created and second.version == first.version
    vid = first.version.parsed_version_id
    assert store.read_version_artifact(vid, "receipt", actor=OWNER) == original_receipt
    assert (
        store.read_version_artifact(vid, "receipt", actor=OWNER, request_key="second")
        == original_receipt + b"\n"
    )


def test_missing_bound_raw_blocks_parsed_reads_after_restart(tmp_path):
    from src.content_store.errors import IntegrityError

    bundle, _ = material(tmp_path)
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    raw = result.version.source_version_id
    version = store.list_source_versions(result.version.source_id, actor=OWNER)[0]
    assert version.source_version_id == raw
    (store.root / version.manifest.artifacts[0].store_key).unlink()
    with pytest.raises(IntegrityError):
        ContentStore(store.root).read_parsed_payload(
            result.version.parsed_version_id, actor=OWNER
        )
