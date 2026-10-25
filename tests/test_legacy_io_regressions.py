"""Legacy IO contracts, using real files and an isolated session logger."""

import importlib
import logging
import sys
import zipfile
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def legacy_io(monkeypatch):
    # Do not load credentials, dotenv files or optional SDKs through AppSession.
    memory = ModuleType("src.core.memory")
    memory.app_session = SimpleNamespace(logger=logging.getLogger(__name__))
    monkeypatch.setitem(sys.modules, "src.core.memory", memory)
    paths = importlib.import_module("src.utils.path_helper")
    # This module binds app_session at import time. Restore the module cache too.
    name = "src.utils.zipfile_helper"
    package = importlib.import_module("src.utils")
    missing = object()
    previous_attribute = getattr(package, "zipfile_helper", missing)
    previous = sys.modules.pop(name, None)
    archives = importlib.import_module(name)
    try:
        yield paths, archives
    finally:
        sys.modules.pop(name, None)
        if previous is not None:
            sys.modules[name] = previous
        if previous_attribute is missing:
            delattr(package, "zipfile_helper")
        else:
            package.zipfile_helper = previous_attribute


def test_move_preserves_existing_destination(legacy_io, tmp_path):
    paths, _ = legacy_io
    source, target = tmp_path / "source.txt", tmp_path / "target.txt"
    source.write_bytes(b"new")
    target.write_bytes(b"valuable old data")
    assert paths.move_file(source, target) is None
    assert source.read_bytes() == b"new"
    assert target.read_bytes() == b"valuable old data"


@pytest.mark.parametrize("target_name", ["target.txt", "extensionless"])
def test_move_creates_only_target_parent(legacy_io, tmp_path, target_name):
    paths, _ = legacy_io
    source, target = tmp_path / "source.txt", tmp_path / "nested" / target_name
    source.write_bytes(b"payload")
    assert paths.move_file(source, target) is None
    assert not source.exists()
    assert target.is_file()
    assert target.read_bytes() == b"payload"


def test_missing_move_source_is_not_created(legacy_io, tmp_path):
    paths, _ = legacy_io
    source = tmp_path / "missing" / "extensionless"
    with pytest.raises(FileNotFoundError):
        paths.move_file(source, tmp_path / "target.txt")
    assert not source.parent.exists()


@pytest.mark.parametrize("suffix", ["json", ".json"])
def test_list_accepts_single_file(legacy_io, tmp_path, suffix):
    paths, _ = legacy_io
    source = tmp_path / "document.json"
    source.write_text("{}", encoding="utf-8")
    assert paths.list_files(str(source), suffix) == [source]


def test_list_combines_files_and_directories_without_suffix_directories(
    legacy_io, tmp_path
):
    paths, _ = legacy_io
    folder = tmp_path / "folder"
    folder.mkdir()
    child = folder / "document.json"
    child.write_text("{}", encoding="utf-8")
    (folder / "directory.json").mkdir()
    (folder / "other.txt").touch()
    explicit = tmp_path / "explicit.json"
    explicit.touch()
    assert paths.list_files([explicit, folder], "json") == [explicit, child]


@pytest.mark.parametrize("name", ["missing", "missing.json"])
def test_list_missing_input_has_no_write_side_effect(legacy_io, tmp_path, name):
    paths, _ = legacy_io
    source = tmp_path / "absent-parent" / name
    with pytest.raises(ValueError):
        paths.list_files(source, "json")
    assert not source.parent.exists()


def test_list_rejects_wrong_file_suffix(legacy_io, tmp_path):
    paths, _ = legacy_io
    source = tmp_path / "document.txt"
    source.touch()
    with pytest.raises(ValueError):
        paths.list_files(source, "json")


def test_single_zip_extract_honors_destination(legacy_io, tmp_path, monkeypatch):
    _, archives = legacy_io
    source = tmp_path / "archive.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("nested/document.txt", "payload")
        archive.writestr("other.txt", "untouched")
    cwd, target = tmp_path / "cwd", tmp_path / "destination"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    assert (
        archives.unpack_single_zipfile(str(source), "nested/document.txt", str(target))
        is None
    )
    assert (target / "nested/document.txt").read_text() == "payload"
    assert not (target / "other.txt").exists()
    assert list(cwd.iterdir()) == []


def test_zip_missing_member_does_not_write(legacy_io, tmp_path):
    _, archives = legacy_io
    source, target = tmp_path / "archive.zip", tmp_path / "destination"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("document.txt", "payload")
    with pytest.raises(KeyError):
        archives.unpack_single_zipfile(str(source), "missing.txt", str(target))
    assert not target.exists()


def test_entire_zip_destination_remains_compatible(legacy_io, tmp_path):
    _, archives = legacy_io
    source, target = tmp_path / "archive.zip", tmp_path / "destination"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("nested/document.txt", "payload")
    assert archives.unpack_entire_zipfolder(str(source), str(target)) is None
    assert (target / "nested/document.txt").read_text() == "payload"
