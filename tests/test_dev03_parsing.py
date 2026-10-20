"""Actual native fixture parsing and minimal shared-image capture regression."""

import json
import socket

import pytest

from scripts.acceptance.dev03_parsing import native_pdf, run
from src.content_store.adapters import (
    _capture,
    import_verified_bundle,
    verify_material_bundle,
)
from src.content_store.errors import UnverifiedBinding
from src.content_store.models import sha256
from src.content_store.store import ContentStore
from tests.content_adapter_support import attest, dump
from tests.content_store_support import OWNER


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a, **kw):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def test_same_image_bytes_preserve_distinct_occurrences_and_hash_guards(tmp_path):
    bundle, doc = native_pdf(tmp_path / "pdf")
    assert len(doc.images) >= 2
    assert len({i.artifact_path for i in doc.images}) == 1
    assert len({i.image_id for i in doc.images}) == len(doc.images)
    assert {tuple(i.source_location.bbox) for i in doc.images} == {
        (30, 50, 70, 90),
        (90, 50, 130, 90),
    }
    candidate = verify_material_bundle(bundle)
    assert candidate is not None
    store = ContentStore.initialize(tmp_path / "content")
    published = import_verified_bundle(
        store, candidate, actor=OWNER, request_key="shared-images"
    ).version
    assert (
        store.read_parsed_payload(published.parsed_version_id, actor=OWNER)
        == bundle.normalized_path.read_bytes()
    )
    assert (
        store.read_raw_artifact(published.source_id, doc.raw_sha256, actor=OWNER)
        == bundle.raw_path.read_bytes()
    )
    # A contradictory second declaration must never be accepted as an alias.
    value = doc.model_dump(mode="json")
    value["images"][0]["sha256"] = "0" * 64
    dump(bundle.normalized_path, value)
    receipt = json.loads(bundle.receipt_path.read_bytes())
    receipt["normalized_sha256"] = sha256(bundle.normalized_path.read_bytes())
    dump(bundle.receipt_path, receipt)
    attest(bundle)
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)
    # An image path aliasing the payload is still a role collision, not an image reuse.
    value = doc.model_dump(mode="json")
    value["images"][0]["artifact_path"] = bundle.normalized_path.name
    dump(bundle.normalized_path, value)
    with pytest.raises(UnverifiedBinding, match="collision"):
        _capture(bundle, "material")


def test_existing_evaluator_recipe_frozen_inputs_and_report_hashes(tmp_path):
    output = tmp_path / "reports"
    report = run(tmp_path / "synthetic", output)
    assert len(report.report["inventory"]) == 5
    assert all(r["binding_verified"] for r in report.report["inventory"])
    assert len(report.report["results"]) == 8
    assert all(r["status"] == "passed" for r in report.report["results"])
    assert all(
        m["denominator"] == 0 and m["rate"] is None
        for g in report.report["metrics"]
        if g["origin"] == "real"
        for m in g["metrics"].values()
    )
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert all(
        sha256((output / name).read_bytes()) == digest
        for name, digest in manifest["files"].items()
    )
    assert str(tmp_path) not in (output / "pdf-native-visual.json").read_text()
    assert (
        json.loads((output / "math-sympy/report.json").read_bytes())["metrics"]["real"][
            "case_count"
        ]
        == 0
    )
    with pytest.raises(ValueError):
        run(tmp_path / "synthetic", tmp_path / "again")
    assert not (tmp_path / "again").exists()
