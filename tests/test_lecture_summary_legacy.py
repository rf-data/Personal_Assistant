"""Focused legacy/security tests: synthetic files, no network or services."""

import json
import socket

import pytest

from src.content_store.models import sha256
from src.lecture_summary.exports import render
from src.lecture_summary.legacy import LegacyEntry, LegacyManifest, candidate, recognize, relative_locator
from src.lecture_summary.legacy_inventory import scan
from src.lecture_summary.models import Selection
from src.lecture_summary.providers import MockProvider
from src.lecture_summary.service import SummaryService
from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import MaterialResource
from src.tools_materials.parse_html import parse_html
from src.tools_materials.storage import RegisteredStorage


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: pytest.fail("Network forbidden"))


@pytest.fixture
def sources(tmp_path):
    transcript = dict(source="/historical/unregistered/audio.m4a", text="Synthetische Vektoren.",
        segments=[dict(seg_id=7, start=1, end=2, text="Synthetische Vektoren.")])
    knowledge = dict(source_id="synthetic-source", chunks=[dict(
        analysis=dict(chunk_id="c1", relevant=True, domains=["mathematics"]),
        extraction=dict(chunk_id="c1", statements=[dict(statement_id="s1",
            text="Synthetische Vektoren.", semantic_type="statement", segment_ids=[7], start=1, end=2)],
            formulas=[dict(expression_id="f1", plain_text="Synthetisch: x=1", latex="x=1",
                expression_type="formula", segment_ids=[7], start=1, end=2)]))], visual_candidates=[])
    for name, obj in (("t.json", transcript), ("k.json", knowledge)):
        (tmp_path / name).write_text(json.dumps(obj))
    storage = RegisteredStorage({"legacy": {"path": str(tmp_path), "readonly": True}})

    def entry(name="t.json", key="t", **changes):
        values = dict(key=key, storage_id="legacy", locator=name,
            expected_sha256=sha256((tmp_path / name).read_bytes()),
            provider_id="synthetic", course_id="mathe", lecture_ids=("l1",),
            title="Synthetische Lektion", identity_evidence="explicit_registration")
        values.update(changes)
        return LegacyEntry(**values)
    return tmp_path, storage, entry


def build(storage, *entries):
    return candidate(storage, LegacyManifest(entries=entries))


def test_transcript_knowledge_e2e_preserves_originals_and_parent_provenance(sources):
    root, storage, entry = sources
    before = {p: p.read_bytes() for p in root.iterdir()}
    catalog, report = build(storage, entry(), entry("k.json", "k", parent_keys=("t",)))
    assert not report["review"] and report["registered"] is False
    artifacts = catalog.lectures[0].sources
    assert artifacts[1].parent_artifact_ids == (artifacts[0].artifact_id,)
    assert all(a.role == "derived" for a in artifacts)
    result = SummaryService(catalog, storage, MockProvider()).generate(
        Selection(provider_id="synthetic", course_id="mathe", lecture_ids=("l1",)))
    derived = [e for e in result.evidence if e.native_source_id == "synthetic-source"]
    assert {e.native_item_id for e in derived} == {"s1", "f1"}
    assert all(e.parent_segment_ids == (7,) and e.native_chunk_id == "c1" for e in derived)
    assert all("derived_knowledge_not_independent_evidence" in e.warnings for e in derived)
    assert result.validation_status == "needs_review"
    assert "Quellenverzeichnis" in render(result) and r"\end{document}" in render(result, latex=True)
    assert "Parent-Artefakte" in render(result) and "Parent-Segmente 7" in render(result, latex=True)
    assert before == {p: p.read_bytes() for p in root.iterdir()}


def test_normalized_document_native_binding_and_original_identity(sources):
    root, storage, entry = sources
    resource = ResourceCandidate(course_id="cs50x", role="notes", original_url="https://example.org/notes")
    binding = MaterialResource(resource=resource, lecture_ids=("week0",),
        original_url="https://example.org/notes", role="notes", format="html")
    doc, _ = parse_html(binding, b"<main><p>Synthetic source only.</p></main>")
    (root / "d.json").write_text(doc.model_dump_json())
    catalog, report = build(storage, entry("d.json", "d", course_id="cs50x", lecture_ids=("week0",)))
    assert report["accepted"][0]["native_document_id"] == doc.document_id
    result = SummaryService(catalog, storage, MockProvider()).generate(
        Selection(provider_id="synthetic", course_id="cs50x", lecture_ids=("week0",)))
    assert result.evidence[0].original_artifact_sha256 == doc.raw_sha256
    assert result.evidence[0].native_source_id == binding.source_id
    assert result.evidence[0].locator.dom


@pytest.mark.parametrize("payload", [[], {}, {"schema_name": "DoclingDocument"},
    {"container_type": "document", "elements": []}, {"source": "x", "segments": [], "text": "",
        "chunks": [], "visual_candidates": []}, {"source": "x", "segments": "invalid", "text": ""}])
def test_unsupported_ambiguous_or_invalid_schema(payload):
    with pytest.raises(ValueError):
        recognize(json.dumps(payload).encode())


@pytest.mark.parametrize("change", [dict(lecture_ids=()), dict(lecture_ids=("l1", "l1")),
    dict(identity_evidence="native_metadata")])
def test_missing_or_ambiguous_ids_go_to_review(sources, change):
    _, storage, entry = sources
    catalog, report = build(storage, entry(**change))
    assert catalog is None and report["review"]


def test_native_ids_and_contradictory_explicit_metadata(sources):
    root, storage, entry = sources
    path = root / "t.json"
    obj = json.loads(path.read_bytes())
    obj.update(provider_id="synthetic", course_id="mathe", lecture_id="l1")
    path.write_text(json.dumps(obj))
    assert build(storage, entry(identity_evidence="native_metadata"))[0]
    catalog, report = build(storage, entry(lecture_ids=("wrong",)))
    assert catalog is None and "Contradictory" in report["review"][0]["detail"]


def test_copies_deduplicated_and_ids_independent_of_root(sources):
    root, storage, entry = sources
    (root / "copy.json").write_bytes((root / "t.json").read_bytes())
    catalog, report = build(storage, entry(), entry("copy.json", "copy"))
    assert len(catalog.lectures[0].sources) == 1
    assert report["review"][0]["reason"] == "duplicate_content"
    mirror = root / "mirror"
    mirror.mkdir()
    (mirror / "t.json").write_bytes((root / "t.json").read_bytes())
    other = RegisteredStorage({"legacy": {"path": str(mirror), "readonly": True}})
    mirrored, _ = build(other, entry())
    assert catalog.lectures[0].sources[0].artifact_id == mirrored.lectures[0].sources[0].artifact_id


def test_conflicting_native_versions_both_rejected(sources):
    root, storage, entry = sources
    obj = json.loads((root / "t.json").read_bytes())
    obj["source_id"] = "same-native-source"
    (root / "t.json").write_text(json.dumps(obj))
    obj["segments"][0]["text"] = "Changed synthetic version."
    (root / "copy.json").write_text(json.dumps(obj))
    catalog, report = build(storage, entry(), entry("copy.json", "copy"))
    assert catalog is None and len(report["review"]) == 2
    assert all(r["reason"] == "conflicting_native_versions" for r in report["review"])


def test_parent_provenance_conflict_is_not_silently_accepted(sources):
    root, storage, entry = sources
    for filename, field, media in (("t.json", "provenance", "one"),
                                   ("k.json", "transcript_provenance", "other")):
        obj = json.loads((root / filename).read_bytes())
        obj[field] = dict(transcript_source="manual_subtitle", media_id=media)
        (root / filename).write_text(json.dumps(obj))
    catalog, report = build(storage, entry(), entry("k.json", "k", parent_keys=("t",)))
    assert len(catalog.lectures[0].sources) == 1
    assert "provenance mismatch" in report["review"][0]["detail"]


@pytest.mark.parametrize("parent", [(), ("unknown",)])
def test_missing_parent_not_guessed_from_filename(sources, parent):
    _, storage, entry = sources
    catalog, report = build(storage, entry("k.json", "k", parent_keys=parent))
    assert catalog is None and report["review"][0]["reason"] == "invalid_parent"


@pytest.mark.parametrize("change", ["segment", "time", "identity"])
def test_invalid_parent_evidence_rejected(sources, change):
    root, storage, entry = sources
    obj = json.loads((root / "k.json").read_bytes())
    if change == "segment":
        obj["chunks"][0]["extraction"]["statements"][0]["segment_ids"] = [999]
    elif change == "time":
        obj["chunks"][0]["extraction"]["statements"][0]["end"] = 100
    (root / "k.json").write_text(json.dumps(obj))
    kwargs = dict(lecture_ids=("other",)) if change == "identity" else {}
    catalog, report = build(storage, entry(), entry("k.json", "k", parent_keys=("t",), **kwargs))
    assert len(catalog.lectures[0].sources) == 1 and report["review"][0]["reason"] == "invalid_parent"


@pytest.mark.parametrize("locator", ["../t.json", "sub/../t.json", "/etc/passwd", "a\\b", "./t.json"])
def test_unsafe_path_translation(sources, locator):
    _, storage, _ = sources
    with pytest.raises(ValueError):
        relative_locator(storage, "legacy", locator)


def test_absolute_path_only_translated_inside_named_root(sources):
    root, storage, _ = sources
    assert relative_locator(storage, "legacy", str(root / "t.json")) == "t.json"
    with pytest.raises(PermissionError):
        storage.create("legacy", "new.json", b"no")


def test_links_and_nested_mounts_rejected(sources, monkeypatch):
    root, storage, _ = sources
    (root / "link.json").symlink_to(root / "t.json")
    with pytest.raises((ValueError, OSError)):
        relative_locator(storage, "legacy", "link.json")
    import src.runtime_paths
    monkeypatch.setattr(src.runtime_paths, "mounts", lambda **kw: {root, root / "t.json"})
    with pytest.raises(ValueError, match="mount"):
        relative_locator(storage, "legacy", "t.json")


def test_missing_mount_corrupt_json_and_changed_hash(sources):
    root, storage, entry = sources
    expected = entry()
    (root / "t.json").write_bytes(b"{")
    assert build(storage, entry())[0] is None
    assert "fingerprint changed" in build(storage, expected)[1]["review"][0]["detail"]
    missing = RegisteredStorage({"legacy": {"path": str(root / "unmounted"), "readonly": True}})
    assert build(missing, expected)[0] is None


def test_inventory_exceeds_old_limit_and_streams_metadata(tmp_path):
    folder = tmp_path / "provider/course/transcripts"
    folder.mkdir(parents=True)
    for i in range(4050):
        (folder / f"{i}.json").touch()
    meta = folder.parent / "metadata"
    meta.mkdir()
    (meta / "course.json").write_text(json.dumps(dict(provider="provider", course_id="course",
        resources=[dict(lecture_no="l1", local_path=str(folder / "0.json")),
                   dict(local_path="/outside/untrusted.json") ])))
    storage = RegisteredStorage({"legacy": {"path": str(tmp_path), "readonly": True}})
    counts, references, progress = {}, [], []
    def emit(event):
        counts[event["event"]] = counts.get(event["event"], 0) + 1
        if event["event"] == "resource_reference":
            references.append(event)
    report = scan(storage, "legacy", emit, progress=progress.append)
    assert report["complete"] and report["files"] == 4051
    assert counts["file"] == 4051 and len(progress) >= 8
    assert report["courses"][0]["identity_status"] == "course_metadata_matches_directory"
    assert report["courses"][0]["declared_lecture_ids"] == ["l1"]
    assert references[0]["file_status"] == "present_regular_file"
    assert references[1]["file_status"] == "unregistered_or_unsafe_reference"


def test_inventory_missing_root_and_links_report_incomplete(sources):
    root, storage, _ = sources
    (root / "loop").symlink_to(root)
    events = []
    report = scan(storage, "legacy", events.append)
    assert not report["complete"] and any(e.get("reason") == "symlink" for e in events)
    missing = RegisteredStorage({"legacy": {"path": str(root / "missing"), "readonly": True}})
    assert not scan(missing, "legacy", events.append)["root_available"]


def test_inventory_permission_error_and_nested_mount(sources, monkeypatch):
    root, storage, _ = sources
    (root / "blocked").mkdir()
    import src.lecture_summary.legacy_inventory as module
    original = module.os.open
    def denied(name, *args, **kwargs):
        if name == "blocked":
            raise PermissionError("synthetic permission error")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(module.os, "open", denied)
    monkeypatch.setattr(module, "mounts", lambda **kw: {root, root / "t.json"})
    events = []
    report = scan(storage, "legacy", events.append)
    assert not report["complete"]
    assert {"PermissionError", "nested_mount_or_device_boundary"} <= {e.get("reason") for e in events}


def test_inventory_does_not_open_or_hash_media(sources, monkeypatch):
    root, storage, _ = sources
    (root / "movie.mp4").write_bytes(b"synthetic media")
    monkeypatch.setattr(storage, "read", lambda *a, **kw: pytest.fail("No content reads outside metadata"))
    report = scan(storage, "legacy", lambda e: None)
    assert report["complete"] and report["files"] == 3


def test_duplicate_json_keys_are_not_silently_overridden():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        recognize(b'{"source":"one","source":"two","text":"","segments":[]}')


@pytest.mark.parametrize("change", ["duplicate_chunk", "mismatched_chunk", "duplicate_item"])
def test_ambiguous_native_knowledge_ids_rejected(sources, change):
    root, storage, entry = sources
    obj = json.loads((root / "k.json").read_bytes())
    if change == "duplicate_chunk":
        obj["chunks"].append(obj["chunks"][0])
    elif change == "mismatched_chunk":
        obj["chunks"][0]["extraction"]["chunk_id"] = "other"
    else:
        obj["chunks"][0]["extraction"]["statements"] *= 2
    (root / "k.json").write_text(json.dumps(obj))
    catalog, report = build(storage, entry(), entry("k.json", "k", parent_keys=("t",)))
    assert len(catalog.lectures[0].sources) == 1 and report["review"]


def test_inventory_output_enospc_is_not_swallowed_or_retried(sources):
    _, storage, _ = sources
    calls = []
    def failed(event):
        calls.append(event)
        raise OSError(28, "synthetic ENOSPC")
    with pytest.raises(OSError, match="ENOSPC"):
        scan(storage, "legacy", failed)
    assert len(calls) == 1


def test_cli_explicit_manifest_candidate_roundtrip_and_no_overwrite(sources, monkeypatch):
    import sys
    from scripts.lecture_summary import register
    from scripts.lecture_summary_legacy import main
    from src.lecture_summary.local import load_service

    root, _, _ = sources
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    config = register(root / "base", root, "t.json", "synthetic", "mathe", "l1", "Synthetic", "transcript_json")
    bindings, output = root / "bindings", root / "candidate"
    monkeypatch.setattr(sys, "argv", ["legacy", "manifest", "--config", str(config),
        "--output", str(bindings), "--knowledge-for", "l1", "--knowledge", "k.json"])
    assert main() == 0
    monkeypatch.setattr(sys, "argv", ["legacy", "catalog", "--manifest", str(bindings / "manifest.json"),
        "--roots", str(bindings / "roots.json"), "--output", str(output)])
    assert main() == 0
    service = load_service(output / "summary.json", offline_only=True)
    assert len(service.catalog.lectures[0].sources) == 2
    assert service.provider.model == "mock-extractive-v1"
    assert before == {name: (root / name).read_bytes() for name in before}
    assert (output / "catalog_review.json").stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        main()
    rebound = root / "rebound"
    monkeypatch.setattr(sys, "argv", ["legacy", "manifest", "--config", str(output / "summary.json"),
        "--output", str(rebound)])
    assert main() == 0
    manifest = LegacyManifest.model_validate_json((rebound / "manifest.json").read_bytes())
    assert manifest.entries[1].parent_keys == (manifest.entries[0].key,)
