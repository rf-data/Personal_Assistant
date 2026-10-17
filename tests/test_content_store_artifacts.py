import io
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.content_store import ContentStore
from src.content_store.errors import IntegrityError, InvalidInput, Unavailable
from src.content_store.models import ArtifactReference, sha256


def fixture(tmp_path, data=b"original\r\n bytes\x00"):
    store = ContentStore.initialize(tmp_path / "content")
    ref = ArtifactReference(
        sha256=sha256(data), size_bytes=len(data), mime_type="application/octet-stream"
    )
    return store._artifacts, ref, data


def test_stage_install_and_deduplicate_exact_bytes(tmp_path):
    artifacts, ref, data = fixture(tmp_path)
    original = tmp_path / "original"
    original.write_bytes(data)
    for run in ("a" * 32, "b" * 32):
        with original.open("rb") as stream:
            artifacts.stage(run, stream, ref)
        artifacts.install(run, ref)
        assert artifacts.read(ref) == data
        assert not (artifacts.root / "staging" / run / ref.sha256).exists()
    assert original.read_bytes() == data
    assert original.stat().st_nlink == 1
    target = artifacts.root / ref.store_key
    assert target.stat().st_nlink == 1
    assert target.stat().st_mode & 0o777 == 0o600
    assert target.stat().st_ino != original.stat().st_ino


@pytest.mark.parametrize("data", [b"too small", b"too much data" * 20])
def test_size_mismatch_leaves_only_unpublished_staging(tmp_path, data):
    artifacts, ref, _ = fixture(tmp_path)
    with pytest.raises(IntegrityError):
        artifacts.stage("a" * 32, io.BytesIO(data), ref)
    assert not (artifacts.root / ref.store_key).exists()


def test_hash_mismatch(tmp_path):
    artifacts, ref, data = fixture(tmp_path)
    with pytest.raises(IntegrityError):
        artifacts.stage("a" * 32, io.BytesIO(b"x" * len(data)), ref)
    assert not (artifacts.root / ref.store_key).exists()


def test_existing_corruption_is_not_overwritten(tmp_path):
    artifacts, ref, data = fixture(tmp_path)
    artifacts.stage("a" * 32, io.BytesIO(data), ref)
    artifacts.install("a" * 32, ref)
    target = artifacts.root / ref.store_key
    target.write_bytes(b"x" * len(data))
    artifacts.stage("b" * 32, io.BytesIO(data), ref)
    with pytest.raises(IntegrityError):
        artifacts.install("b" * 32, ref)
    assert target.read_bytes() == b"x" * len(data)


@pytest.mark.parametrize("kind", ["symlink", "fifo", "hardlink"])
def test_nonregular_or_aliased_blob_is_rejected(tmp_path, kind):
    artifacts, ref, data = fixture(tmp_path)
    target = artifacts.root / ref.store_key
    target.parent.mkdir(mode=0o700)
    original = tmp_path / "other"
    original.write_bytes(data)
    original.chmod(0o600)
    if kind == "symlink":
        target.symlink_to(original)
    elif kind == "fifo":
        os.mkfifo(target, 0o600)
    else:
        os.link(original, target)
    with pytest.raises((OSError, IntegrityError)):
        artifacts.read(ref)
    assert original.read_bytes() == data


def test_symlinked_ancestor_and_blob_directory_are_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(Unavailable):
        ContentStore.initialize(alias / "content")
    artifacts, ref, data = fixture(tmp_path)
    (artifacts.root / "blobs/sha256" / ref.sha256[:2]).symlink_to(
        real, target_is_directory=True
    )
    artifacts.stage("a" * 32, io.BytesIO(data), ref)
    with pytest.raises(OSError):
        artifacts.install("a" * 32, ref)
    assert list(real.iterdir()) == []


def test_private_explicit_root_and_limits(tmp_path):
    with pytest.raises(InvalidInput):
        ContentStore.initialize(Path("relative"))
    root = tmp_path / "content"
    root.mkdir(mode=0o755)
    with pytest.raises(IntegrityError):
        ContentStore.initialize(root)
    with pytest.raises(ValidationError) as info:
        ArtifactReference(
            sha256="a" * 64, size_bytes=64 * 1024 * 1024 + 1, mime_type="binary"
        )
    assert "size_bytes" in str(info.value)


def test_interrupted_stream_never_installs_blob(tmp_path):
    artifacts, ref, data = fixture(tmp_path)

    class BrokenStream:
        def read(self, size):
            raise OSError("synthetic disk failure")

    with pytest.raises(OSError):
        artifacts.stage("a" * 32, BrokenStream(), ref)
    assert not (artifacts.root / ref.store_key).exists()
    assert (artifacts.root / "staging" / ("a" * 32)).is_dir()


def test_sync_failure_leaves_unpublished_evidence(tmp_path, monkeypatch):
    artifacts, ref, data = fixture(tmp_path)
    import src.content_store.artifacts as module

    original_sync = module._sync

    def fail_on_file(fd):
        import stat

        if stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError("synthetic fsync failure")
        original_sync(fd)

    monkeypatch.setattr(module, "_sync", fail_on_file)
    with pytest.raises(OSError):
        artifacts.stage("a" * 32, io.BytesIO(data), ref)
    assert not (artifacts.root / ref.store_key).exists()
