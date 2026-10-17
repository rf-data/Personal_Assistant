import ast
import json
from pathlib import Path

import pytest
from content_store_support import config, payload, registration
from pydantic import ValidationError

from src.content_store._testing import SyntheticPayload
from src.content_store.errors import InvalidInput
from src.content_store.models import (
    ContentLocator,
    RawArtifact,
    RawManifest,
    SourceRegistration,
    canonical,
    sha256,
)
from src.model_discovery.cs50 import ResourceCandidate, deterministic_id


def test_golden_hash_domains_match_adr():
    # Independently specified C23-01 example, no newline/Unicode normalization.
    reg = SourceRegistration(
        identity_namespace="synthetic:c23-01",
        external_identity="hello-html",
        course_id="cs50_python",
        source_type="synthetic",
        source_origin="synthetic",
    )
    assert (
        reg.resolved_id
        == "content_source_v1:a70e83a6e45fb92e94cd9427eebf5bcce62bf879e579e7e4c99e8ecd2d22fe38"
    )
    raw = b"<p>Hallo.</p>\n"
    assert (
        sha256(raw)
        == "6bbbfa1c14ef11d6d8b93f091501ded1ea414d28094c9aba4758229fb03c40e8"
    )
    manifest = RawManifest(
        artifacts=(
            RawArtifact(sha256=sha256(raw), size_bytes=14, mime_type="text/html"),
        )
    )
    assert (
        deterministic_id(
            "content_source_version_v1", reg.resolved_id, "default", manifest.digest
        )
        == "content_source_version_v1:248082cd4cb185e10f1d4581595450baa8e0b48154fe0d49920581044dddc1aa"
    )
    assert canonical({"z": "Ä", "a": 1}) == '{"a":1,"z":"Ä"}'.encode()


def test_parser_configuration_is_complete_and_key_order_independent():
    first = config(parameters={"encoding": "utf-8", "settings": {"b": 2, "a": 1}})
    second = config(parameters={"settings": {"a": 1, "b": 2}, "encoding": "utf-8"})
    assert first.config_id == second.config_id
    assert first.config_id != config(parser_version="2").config_id
    assert (
        first.config_id
        != config(implementation_revision="new-implementation").config_id
    )
    assert json.loads(first.model_dump_json()) == first.model_dump(mode="json")
    assert registration().resolved_id == registration().resolved_id


def test_cs50_id_is_not_recomputed():
    resource = ResourceCandidate(
        course_id="cs50_python",
        role="notes",
        original_url="https://cs50.harvard.edu/python/notes/0/",
    )
    reg = SourceRegistration(
        identity_namespace="cs50",
        external_identity=resource.resource_id,
        source_id=resource.resource_id,
        course_id=resource.course_id,
        source_type="material",
        source_origin="official",
    )
    assert reg.resolved_id == resource.resource_id
    with pytest.raises(ValidationError):
        SourceRegistration.model_validate(reg.model_dump() | {"source_id": "different"})


@pytest.mark.parametrize(
    "change",
    [
        {"time_status": "known"},
        {"time_status": "unknown", "start": 0, "end": 0},
        {"time_status": "not_applicable", "end": 1},
        {"time_status": "known", "start": 2, "end": 1},
        {"time_status": "known", "start": float("nan"), "end": 2},
        {"page": 0},
        {"bbox": [3, 0, 1, 2]},
        {"bbox": [0, 0, float("inf"), 1]},
        {"line_end": 2},
        {"origin_pointer": "../escape"},
    ],
)
def test_invalid_locators_are_rejected(change):
    values = {
        "raw_artifact_sha256": "a" * 64,
        "origin_pointer": "/blocks/0",
        "time_status": "unknown",
    }
    with pytest.raises(ValidationError):
        ContentLocator(**(values | change))


@pytest.mark.parametrize("status", ["unknown", "not_applicable"])
def test_unknown_times_roundtrip_as_null(status):
    loc = ContentLocator(
        raw_artifact_sha256="a" * 64, origin_pointer="/blocks/0", time_status=status
    )
    assert json.loads(loc.model_dump_json())["start"] is None
    assert ContentLocator.model_validate_json(loc.model_dump_json()) == loc


@pytest.mark.parametrize(
    "mutate",
    [
        lambda x: x[1].update(block_id=x[0]["block_id"]),
        lambda x: x[1].update(order=4),
        lambda x: x[1].update(payload_pointer="/not-the-block"),
    ],
)
def test_synthetic_blocks_validate_identity_order_and_pointer(mutate):
    obj = json.loads(payload("a" * 64))
    mutate(obj["blocks"])
    with pytest.raises(ValidationError):
        SyntheticPayload.model_validate(obj)


def test_raw_manifest_requires_unique_sorted_primary():
    a = RawArtifact(sha256="a" * 64, size_bytes=1, mime_type="text/plain")
    with pytest.raises(ValidationError):
        RawManifest(artifacts=(a, a))
    with pytest.raises(ValidationError):
        RawManifest(artifacts=(a.model_copy(update={"role": "attachment"}),))
    with pytest.raises(ValidationError):
        RawManifest(artifacts=(a, a.model_copy(update={"role": "attachment"})))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1: "key"}, b"binary"])
def test_unsafe_canonical_values_fail(value):
    with pytest.raises(InvalidInput):
        canonical(value)


def test_json_depth_and_executable_text():
    value = "leaf"
    for _ in range(65):
        value = {"nested": value}
    with pytest.raises(InvalidInput):
        canonical(value)
    text = "__import__('os').system('MUST_NOT_RUN')"
    assert json.loads(canonical({"text": text}))["text"] == text


def test_package_has_no_knowledge_or_runtime_imports():
    root = Path(__file__).resolve().parents[1] / "src/content_store"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    word in (node.module or "").lower()
                    for word in (
                        "knowledge",
                        "embedding",
                        "marvin",
                        "settings",
                        "chromadb",
                        "qdrant",
                    )
                )
