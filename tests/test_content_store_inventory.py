"""Synthetic inventory, path binding, and strict no-write acceptance."""

import json
import shutil

import pytest
from pydantic import ValidationError

from scripts.cs50_content_inventory import main
from src.content_store.adapters import verify_srt_bundle
from src.content_store.errors import InvalidInput, UnverifiedBinding
from src.content_store.inventory import (
    InventoryReport,
    InventoryRequest,
    InventorySelection,
    inventory,
    report_bytes,
)
from src.content_store.models import sha256
from src.content_store.store import ContentStore
from src.model_materials.materials import NormalizedDocument
from tests.content_adapter_support import REVISION, attest, dump, material, srt
from tests.content_store_support import OTHER, OWNER
from tests.test_content_store_reimport import import_, offline  # noqa: F401


def selection(bundle, *, entry_id="chosen", source_id=None):
    if hasattr(bundle, "transcript_path"):
        kind, source = "srt", bundle.source_id
    else:
        kind = "material"
        source = NormalizedDocument.model_validate_json(
            bundle.normalized_path.read_bytes()
        ).binding.source_id
    return InventorySelection(
        entry_id=entry_id,
        kind=kind,
        source_id=source_id or source,
        course_id="cs50_python",
        expected_implementation_revision=REVISION,
        bundle=bundle,
    )


def bytes_tree(root):
    return {
        str(p.relative_to(root)): (sha256(p.read_bytes()), p.stat().st_mode)
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("kind", ["html", "pdf", "srt"])
def test_inventory_read_only_hashes_and_existing_version(tmp_path, kind, monkeypatch):
    bundle, _ = (
        srt(tmp_path / "input")
        if kind == "srt"
        else material(tmp_path / "input", kind=kind)
    )
    store = ContentStore.initialize(tmp_path / "store")
    first = import_(store, bundle)
    before = bytes_tree(tmp_path)
    request = InventoryRequest(entries=(selection(bundle),))
    reader = ContentStore(store.root)

    def forbidden(*args, **kwargs):
        raise AssertionError("Inventory must not stage or register")

    monkeypatch.setattr(reader, "register_source", forbidden)
    monkeypatch.setattr(reader, "_reserve", forbidden)
    monkeypatch.setattr(reader._artifacts, "stage", forbidden)
    report = inventory(request, actor=OWNER, store=reader)
    result = report.report.entries[0]
    assert result.validation_status == "verified" and not result.issues
    assert result.existing_parsed_version_id == first.version.parsed_version_id
    assert result.source_version_id == first.version.source_version_id
    assert result.hashes["raw"] == sha256(bundle.raw_path.read_bytes())
    assert result.hashes["receipt"] == sha256(bundle.receipt_path.read_bytes())
    assert result.parser.implementation_revision == REVISION
    assert result.section_keys == ("0",) and result.lecture_ids
    assert not result.manual_approvals
    assert report_bytes(report) == report_bytes(
        inventory(request, actor=OWNER, store=reader)
    )
    assert bytes_tree(tmp_path) == before
    assert InventoryReport.model_validate_json(report_bytes(report)) == report


@pytest.mark.parametrize(
    "change",
    [
        "source",
        "course",
        "revision",
        "receipt",
        "missing_evidence",
        "section",
        "pointer",
    ],
)
def test_inventory_binding_failures_are_not_imports(tmp_path, change):
    bundle, _ = srt(tmp_path / "input")
    item = selection(bundle)
    if change == "source":
        item = item.model_copy(update={"source_id": "resource:wrong"})
    elif change == "course":
        item = item.model_copy(update={"course_id": "cs50_sql"})
    elif change == "revision":
        item = item.model_copy(update={"expected_implementation_revision": "b" * 40})
    elif change in {"receipt", "section"}:
        value = json.loads(bundle.receipt_path.read_bytes())
        value["binding"]["section_key" if change == "section" else "resource_id"] = (
            "wrong"
        )
        dump(bundle.receipt_path, value)
        attest(bundle)
    elif change == "pointer":
        value = json.loads(bundle.transcript_path.read_bytes())
        value["source"] = "data/Harvard/wrong/source.srt"
        dump(bundle.transcript_path, value)
        value = json.loads(bundle.receipt_path.read_bytes())
        for record in value["actions"].values():
            if record["action"] == "parse_subtitle":
                record["sha256"] = sha256(bundle.transcript_path.read_bytes())
        dump(bundle.receipt_path, value)
        attest(bundle)
    else:
        bundle.implementation_path.unlink()
    before = bytes_tree(tmp_path)
    report = inventory(InventoryRequest(entries=(item,)), actor=OWNER)
    assert report.report.entries[0].validation_status == "blocked"
    assert report.report.entries[0].issues
    assert bytes_tree(tmp_path) == before
    assert not (tmp_path / "store").exists()


def test_inventory_conflict_acl_and_quarantine(tmp_path):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    first = import_(store, bundle)
    request = InventoryRequest(entries=(selection(bundle),))
    result = inventory(
        request, actor=OTHER, store=ContentStore(store.root)
    ).report.entries[0]
    assert result.issues == ("forbidden",)
    assert result.existing_parsed_version_id is None
    # Same slot with independently reattested different output must conflict.
    value = json.loads(bundle.normalized_path.read_bytes())
    value["title"] = "Changed output"
    dump(bundle.normalized_path, value)
    receipt = json.loads(bundle.receipt_path.read_bytes())
    receipt["normalized_sha256"] = sha256(bundle.normalized_path.read_bytes())
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    assert inventory(
        request, actor=OWNER, store=ContentStore(store.root)
    ).report.entries[0].issues == ("conflict",)
    blob = store.root / first.version.payload.store_key
    blob.write_bytes(b"damaged")
    store.verify_integrity(actor=OWNER)
    assert (
        inventory(request, actor=OWNER, store=ContentStore(store.root))
        .report.entries[0]
        .validation_status
        == "blocked"
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "expected",
        "relocated",
        "explicit_copy",
        "corrupt_copy",
        "missing_receipt",
        "source_pointer",
    ],
)
def test_synthetic_historical_triplets(tmp_path, scenario):
    bundle, _ = srt(tmp_path / "input")
    original = {
        field: getattr(bundle, field).read_bytes()
        for field in ("raw_path", "transcript_path", "receipt_path")
    }
    if scenario != "expected":
        relocated = {}
        for field in original:
            path = getattr(bundle, field)
            historical = bundle.workspace / path.relative_to(
                bundle.workspace
            ).as_posix().replace("data/lectures/", "data/", 1)
            historical.parent.mkdir(parents=True, exist_ok=True)
            path.rename(historical)
            relocated[field] = historical
        wrong = bundle.model_copy(update=relocated)
        with pytest.raises(UnverifiedBinding):
            verify_srt_bundle(wrong)
        if scenario == "relocated":
            bundle = wrong
        else:
            root = tmp_path / "explicit-new-synthetic-workspace"
            copied = {}
            for field, source in relocated.items():
                target = root / getattr(bundle, field).relative_to(bundle.workspace)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                assert target.read_bytes() == original[field]
                copied[field] = target
            bundle = bundle.model_copy(update={"workspace": root, **copied})
            if scenario == "corrupt_copy":
                bundle.raw_path.write_bytes(b"changed")
            elif scenario == "missing_receipt":
                bundle.receipt_path.unlink()
            elif scenario == "source_pointer":
                value = json.loads(bundle.transcript_path.read_bytes())
                value["provenance"]["source_file"] = "data/Harvard/elsewhere/source.srt"
                dump(bundle.transcript_path, value)
            for field, path in relocated.items():
                assert path.read_bytes() == original[field]
    report = inventory(InventoryRequest(entries=(selection(bundle),)), actor=OWNER)
    result = report.report.entries[0]
    assert (result.validation_status == "verified") == (
        scenario in {"expected", "explicit_copy"}
    )
    if scenario == "explicit_copy":
        assert result.hashes["raw"] == sha256(original["raw_path"])
        assert result.hashes["receipt"] == sha256(original["receipt_path"])
        assert result.hashes["payload"] == sha256(original["transcript_path"])


def test_inventory_cli_no_overwrite_and_input_protection(tmp_path, capsys):
    bundle, _ = material(tmp_path / "input")
    request = InventoryRequest(entries=(selection(bundle),))
    path = tmp_path / "selection.json"
    dump(path, request.model_dump(mode="json"))
    target = tmp_path / "report.json"
    args = [
        "--selection",
        str(path),
        "--actor",
        "owner",
        "--course",
        "cs50_python",
        "--output",
        str(target),
    ]
    assert main(args) == 0
    original = target.read_bytes()
    report = InventoryReport.model_validate_json(original)
    assert report.report.entries[0].validation_status == "verified"
    assert main(args) == 2 and target.read_bytes() == original
    for forbidden in (
        path,
        bundle.raw_path,
        bundle.workspace / "new.json",
        bundle.implementation_path,
    ):
        assert main([*args[:-1], str(forbidden)]) == 2
    for malformed in (
        b"{broken",
        b'[{"x":NaN}]',
        b'{"entries":[],"entries":[]}',
        b"[" * 2000 + b"0" + b"]" * 2000,
    ):
        path.write_bytes(malformed)
        assert main(args) == 2
    assert "Inventory input" in capsys.readouterr().err


@pytest.mark.parametrize(
    "mutation", ["duplicate", "kind", "schema", "revision", "digest"]
)
def test_inventory_strict_schema(tmp_path, mutation):
    bundle, _ = material(tmp_path / "input")
    request = InventoryRequest(entries=(selection(bundle),))
    value = request.model_dump(mode="json")
    if mutation == "duplicate":
        value["entries"] *= 2
    elif mutation == "kind":
        value["entries"][0]["kind"] = "srt"
    elif mutation == "schema":
        value["schema_version"] = 2
    elif mutation == "revision":
        value["entries"][0]["expected_implementation_revision"] = "unknown"
    else:
        report = inventory(request, actor=OWNER).model_dump(mode="json")
        report["sha256"] = "0" * 64
        with pytest.raises(ValidationError):
            InventoryReport.model_validate(report)
        return
    with pytest.raises(ValidationError):
        InventoryRequest.model_validate(value)


def test_inventory_rejects_write_handle_and_untyped_request(tmp_path):
    bundle, _ = material(tmp_path / "input")
    request = InventoryRequest(entries=(selection(bundle),))
    store = ContentStore.initialize(tmp_path / "store")
    with pytest.raises(InvalidInput):
        inventory(request, actor=OWNER, store=store)
    with pytest.raises(InvalidInput):
        inventory(request.model_dump(), actor=OWNER)


@pytest.mark.parametrize("field", ["receipt_path", "plan_path"])
def test_incomplete_inventory_with_deep_untrusted_metadata(tmp_path, field):
    bundle, _ = srt(tmp_path / "input")
    request = InventoryRequest(entries=(selection(bundle),))
    bundle.raw_path.unlink()
    getattr(bundle, field).write_bytes(b"[" * 2000 + b"0" + b"]" * 2000)
    result = inventory(request, actor=OWNER).report.entries[0]
    assert result.validation_status == "blocked" and result.issues == (
        "unverified_binding",
    )
