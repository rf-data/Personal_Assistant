"""No remote/Drive reads: synthetic manifests for the proposed two-hop copy."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.c26_copy_inventory import inventory, main


def test_manifests_compare_full_tree_unicode_empty_dirs_and_duplicates(tmp_path):
    source, stage, target = (tmp_path / n for n in ("source", "stage", "target"))
    for root in (source, stage, target):
        root.mkdir()
        (root / "empty").mkdir()
        (root / "code é 😀\n.txt").write_bytes(b"\tprint('synthetic')\r\n")
        (root / "same-bytes").write_bytes(b"\tprint('synthetic')\r\n")
    first = inventory(source)
    assert first == inventory(stage) == inventory(target) == inventory(source)
    assert first["directories"] == ["empty"] and len(first["files"]) == 2
    assert (
        first["files"][0]["sha256"]
        == hashlib.sha256(b"\tprint('synthetic')\r\n").hexdigest()
    )
    assert len({f["sha256"] for f in first["files"]}) == 1
    assert str(tmp_path) not in json.dumps(first)
    (stage / "extra").write_bytes(b"unexpected")
    assert inventory(stage) != first  # Extras cannot pass an inventory comparison.
    (target / "same-bytes").write_bytes(b"changed")
    assert inventory(target) != first


def test_unsafe_entries_and_limits(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(b"123456")
    with pytest.raises(ValueError, match="Byte"):
        inventory(root, max_bytes=5)
    with pytest.raises(ValueError, match="Entry"):
        inventory(root, max_entries=0)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError):
        inventory(link)
    (root / "symlink").symlink_to(root / "file")
    with pytest.raises(ValueError):
        inventory(root)
    (root / "symlink").unlink()
    os.mkfifo(root / "fifo")
    with pytest.raises(ValueError):
        inventory(root)


def test_mutation_during_read_is_not_a_successful_manifest(tmp_path, monkeypatch):
    path = tmp_path / "source"
    path.mkdir()
    file = path / "file"
    file.write_bytes(b"synthetic")
    original = os.open

    def changed(name, flags):
        file.write_bytes(b"changed-size")
        return original(name, flags)

    monkeypatch.setattr(os, "open", changed)
    with pytest.raises(ValueError, match="changed"):
        inventory(path)


def test_cli_safe_error_and_no_source_writes(tmp_path, capsys):
    root = tmp_path / "source"
    root.mkdir()
    file = root / "file"
    file.write_bytes(b"synthetic")
    assert main([str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "c26-copy-inventory"
    assert list(root.iterdir()) == [file] and file.read_bytes() == b"synthetic"
    assert main([str(tmp_path / "private-missing-name")]) == 2
    output = capsys.readouterr().out
    assert (
        "private-missing-name" not in output
        and json.loads(output)["status"] == "blocked"
    )
    with pytest.raises(ValueError):
        inventory(Path("relative"))


def test_standalone_stdin_invocation_requires_no_repository_import(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "file").write_bytes(b"synthetic")
    script = Path(__file__).resolve().parents[1] / "scripts/c26_copy_inventory.py"
    result = subprocess.run(
        [sys.executable, "-B", "-", str(root)],
        input=script.read_bytes(),
        capture_output=True,
        cwd=tmp_path,
        check=True,
    )
    assert json.loads(result.stdout) == inventory(root)
    assert not result.stderr and list(tmp_path.iterdir()) == [root]
