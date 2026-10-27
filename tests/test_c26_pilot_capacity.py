"""The pilot input budget is enforced before worker initialization/dispatch."""

import hashlib

import pytest
from test_job_control import offline as offline
from test_job_control import setup as setup

from scripts.cs50_worker import CapacityExecutor
from src.tools_materials.capacity import MIB, CapacityLimits


def test_worker_accepts_small_synthetic_catalog_under_explicit_limit(setup):
    worker = CapacityExecutor(setup.settings, CapacityLimits(catalog_bytes=MIB))
    try:
        assert not worker.children
        assert not setup.controller.store.all()
    finally:
        worker.close()


def test_worker_refuses_hash_valid_oversized_catalog_before_initialization(setup):
    entry = setup.settings.catalog["demo_snapshots"]
    padding = b"x" * MIB
    (entry.root / "padding.bin").write_bytes(padding)
    changed = entry.model_copy(
        update={
            "files": entry.files | {"padding.bin": hashlib.sha256(padding).hexdigest()}
        }
    )
    settings = setup.settings.model_copy(
        update={"catalog": {"demo_snapshots": changed}}
    )
    before = {str(p): p.read_bytes() for p in settings.root.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="catalog byte budget"):
        CapacityExecutor(settings, CapacityLimits(catalog_bytes=MIB))
    assert before == {
        str(p): p.read_bytes() for p in settings.root.rglob("*") if p.is_file()
    }
