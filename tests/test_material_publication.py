"""Publication interrupted at its durability boundary must retain one inode name."""

import multiprocessing
import os

import pytest

from src.tools_materials import storage


def publish_and_die(path):
    # Deterministic boundary, no timing or signals aimed at unrelated processes.
    storage.sync_directory = lambda _: os._exit(73)
    storage.publish_bytes(path, b"synthetic committed artifact")


def test_abrupt_exit_after_publication_leaves_no_second_hardlink(tmp_path):
    path = tmp_path / "receipt.json"
    child = multiprocessing.get_context("spawn").Process(
        target=publish_and_die, args=(path,)
    )
    child.start()
    child.join(timeout=10)
    try:
        assert child.exitcode == 73
        assert path.read_bytes() == b"synthetic committed artifact"
        assert path.stat().st_nlink == 1
        assert list(tmp_path.iterdir()) == [path]
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)


@pytest.mark.parametrize("existing", ["file", "symlink"])
def test_publication_never_replaces_existing_destination(tmp_path, existing):
    path = tmp_path / "receipt.json"
    target = tmp_path / "original"
    target.write_bytes(b"preserved")
    if existing == "symlink":
        path.symlink_to(target)
    else:
        path.write_bytes(b"preserved")
    with pytest.raises(FileExistsError):
        storage.publish_bytes(path, b"must not replace")
    assert path.read_bytes() == target.read_bytes() == b"preserved"
    assert not list(tmp_path.glob(".material-*"))


def test_publication_rejects_nul_instead_of_truncating_native_path(tmp_path):
    with pytest.raises(ValueError, match="publication path"):
        storage.publish_bytes(tmp_path / "prefix\0suffix", b"must not publish")
    assert list(tmp_path.iterdir()) == []
