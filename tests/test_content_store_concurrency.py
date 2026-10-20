import pytest

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.backup import backup
from src.content_store.errors import Busy
from src.content_store.models import sha256
from src.content_store.store import ContentStore
from tests.content_adapter_support import attest, dump, material
from tests.content_operations_support import (
    child,
    continue_child,
    launch,
    line,
    seeded,
    stop,
)
from tests.content_store_support import OWNER


@pytest.mark.parametrize("same_key", [True, False])
def test_two_processes_same_slot_and_reader(tmp_path, same_key):
    store, original, doc, result = seeded(tmp_path)
    bundle, _ = material(tmp_path / "second", kind="code")
    process = launch(store, bundle, request="held")
    try:
        reader = child("read", store.root, result.version.parsed_version_id)
        assert line(reader)["sha256"] == sha256(original.normalized_path.read_bytes())
        reader.communicate(timeout=5)
        other = child(
            "import",
            store.root,
            bundle.workspace.parent / "descriptor.json",
            "none",
            "held" if same_key else "other",
            "parsed",
        )
        assert line(other)["error"] in {"busy", "unavailable"}
        other.communicate(timeout=10)
        with pytest.raises(Busy):
            backup(store, tmp_path / "backup", actor=OWNER)
        finished = continue_child(process)
        assert finished["created"]
        again = import_verified_bundle(
            store, verify_material_bundle(bundle), actor=OWNER, request_key="held"
        )
        assert not again.created
        with store._connection() as db:
            assert db.execute("SELECT count(*) FROM parsed_versions").fetchone()[0] == 2
    finally:
        if process.poll() is None:
            stop(process)


def test_two_processes_different_sources_can_complete(tmp_path):
    bundle, _ = material(tmp_path / "first")
    other, _ = material(tmp_path / "second", kind="code")
    store = ContentStore.initialize(tmp_path / "store")
    held = launch(store, bundle)
    try:
        dump(other.workspace.parent / "descriptor.json", other.model_dump(mode="json"))
        second = child(
            "import",
            store.root,
            other.workspace.parent / "descriptor.json",
            "none",
            "other",
            "parsed",
        )
        assert line(second)["created"]
        second.communicate(timeout=10)
        assert continue_child(held)["created"]
        assert store.verify_integrity(actor=OWNER).healthy
    finally:
        if held.poll() is None:
            stop(held)


def test_parallel_conflicting_request_is_not_a_new_winner(tmp_path):
    import json

    bundle, _ = material(tmp_path / "first")
    other, _ = material(tmp_path / "second")
    value = json.loads(other.normalized_path.read_bytes())
    value["title"] = "contradiction"
    dump(other.normalized_path, value)
    receipt = json.loads(other.receipt_path.read_bytes())
    receipt["normalized_sha256"] = sha256(other.normalized_path.read_bytes())
    dump(other.receipt_path, receipt)
    attest(other)
    store = ContentStore.initialize(tmp_path / "store")
    held = launch(store, bundle, request="same")
    try:
        dump(other.workspace.parent / "descriptor.json", other.model_dump(mode="json"))
        second = child(
            "import",
            store.root,
            other.workspace.parent / "descriptor.json",
            "none",
            "same",
            "parsed",
        )
        assert line(second)["error"] == "conflict"
        second.communicate(timeout=10)
        assert continue_child(held)["created"]
    finally:
        if held.poll() is None:
            stop(held)
