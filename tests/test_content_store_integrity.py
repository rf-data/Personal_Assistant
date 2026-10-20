import pytest

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.errors import ContentStoreError, Forbidden
from src.content_store.store import ContentStore
from tests.content_adapter_support import material
from tests.content_operations_support import seeded
from tests.content_store_support import OTHER, OWNER, VIEWER


@pytest.mark.parametrize(
    "role", ["raw", "payload", "projection", "receipt", "image", "recovery_intent"]
)
@pytest.mark.parametrize("damage", ["missing", "bytes"])
def test_persistent_quarantine_and_unaffected_source(tmp_path, role, damage):
    bundle, doc = material(tmp_path / "input", local_image=True)
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="first"
    )
    other, _ = material(tmp_path / "other", kind="code")
    intact = import_verified_bundle(
        store, verify_material_bundle(other), actor=OWNER, request_key="other"
    )
    if role == "raw":
        digest = doc.raw_sha256
    elif role == "recovery_intent":
        from src.content_store.models import ProcessingRun

        with store._connection() as db:
            run = ProcessingRun.model_validate_json(
                db.execute(
                    "SELECT data FROM processing_runs WHERE request_key='first'"
                ).fetchone()[0]
            )
        digest = run.recovery.sha256
    else:
        name = f"image:{doc.images[0].image_id}" if role == "image" else role
        from src.content_store.models import sha256

        digest = sha256(
            store.read_version_artifact(
                result.version.parsed_version_id, name, actor=OWNER
            )
        )
    path = store.root / "blobs/sha256" / digest[:2] / digest
    original = path.read_bytes()
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"damaged")
    report = store.verify_integrity(actor=OWNER)
    assert not report.healthy and report.incident_id
    assert report.quarantined_parsed_versions == 1
    assert bool(report.quarantined_source_versions) == (role == "raw")
    reopened = ContentStore(store.root, read_only=False)
    with pytest.raises(ContentStoreError):
        reopened.read_parsed_payload(result.version.parsed_version_id, actor=OWNER)
    assert (
        reopened.read_parsed_payload(intact.version.parsed_version_id, actor=OWNER)
        == other.normalized_path.read_bytes()
    )
    path.write_bytes(original)
    path.chmod(0o600)
    # Correct bytes alone cannot clear a persisted incident/quarantine.
    assert not reopened.verify_integrity(actor=OWNER).healthy
    with pytest.raises(ContentStoreError):
        reopened.read_parsed_payload(result.version.parsed_version_id, actor=OWNER)
    assert (store.root / "incidents" / (report.incident_id + ".json")).exists()


def test_shared_raw_quarantines_all_parser_versions(tmp_path):
    store, bundle, doc, first = seeded(tmp_path)
    other, _ = material(tmp_path / "second", max_blocks=19000)
    second = import_verified_bundle(
        store, verify_material_bundle(other), actor=OWNER, request_key="second"
    )
    assert first.version.source_version_id == second.version.source_version_id
    (store.root / "blobs/sha256" / doc.raw_sha256[:2] / doc.raw_sha256).unlink()
    report = store.verify_integrity(actor=OWNER)
    assert (
        report.quarantined_parsed_versions == 2
        and report.quarantined_source_versions == 1
    )


def test_complete_store_scope_and_readonly_maintenance(tmp_path):
    store, _, _, _ = seeded(tmp_path)
    for actor in (VIEWER, OTHER):
        with pytest.raises(Forbidden):
            store.verify_integrity(actor=actor)
    with pytest.raises(Forbidden):
        ContentStore(store.root).verify_integrity(actor=OWNER)


def test_metadata_contradiction_is_fenced_without_repair(tmp_path):
    store, _, _, _ = seeded(tmp_path)
    import json

    from src.content_store import schema

    with store._connection(write=True) as db:
        row = db.execute(
            "SELECT version_id,id,data FROM content_blocks LIMIT 1"
        ).fetchone()
        damaged = json.loads(row["data"])
        damaged["text"] = "Jello"
        # Fault injection only: restore the exact trigger before integrity verification.
        db.execute("DROP TRIGGER immutable_content_blocks_update")
        db.execute(
            "UPDATE content_blocks SET data=? WHERE version_id=? AND id=?",
            (json.dumps(damaged), row["version_id"], row["id"]),
        )
        db.execute(schema.TRIGGERS["immutable_content_blocks_update"])
    from src.content_store.errors import IntegrityError, Unavailable

    with pytest.raises(IntegrityError):
        store.verify_integrity(actor=OWNER)
    assert (store.root / ".content-recovery-required").exists()
    with pytest.raises(Unavailable):
        ContentStore(store.root)


def test_unowned_staging_is_reported_without_adoption(tmp_path):
    store, bundle, _, result = seeded(tmp_path)
    orphan = store.root / "staging" / ("f" * 32)
    orphan.mkdir(mode=0o700)
    report = store.verify_integrity(actor=OWNER)
    assert "unowned_staging" in {f.code for f in report.findings}
    assert orphan.exists()
    assert (
        store.read_parsed_payload(result.version.parsed_version_id, actor=OWNER)
        == bundle.normalized_path.read_bytes()
    )
