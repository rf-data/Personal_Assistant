"""Metadata inspection must not inflate entries or relax the existing importer."""

import io
import json
import socket
import stat
import struct
import subprocess
import sys
import zipfile

import pytest

from src.tools_materials import code_zip


def zipped(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return stream.getvalue()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def test_inventory_never_opens_members_and_preserves_bytes(monkeypatch):
    raw = zipped(
        [
            ("src/hello.py", b'raise RuntimeError("NEVER RUN")\n'),
            ("README.md", b"readme"),
            ("copy.md", b"readme"),
        ]
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("No member reads or extraction during inventory")

    monkeypatch.setattr(zipfile.ZipFile, "open", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extract", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", forbidden)
    report = code_zip.inventory_zip(raw)
    assert report["status"] == "metadata_checked"
    assert report["sha256"] == code_zip.sha(raw)
    assert report["entry_count"] == 3
    assert report["possible_duplicates_crc_size"] == [["README.md", "copy.md"]]
    assert not report["duplicate_contents_verified"]
    assert not report["member_contents_verified"]
    assert report["course_id"] is report["week"] is None
    assert not report["import_approved"]


@pytest.mark.parametrize("name", ["../a.py", "/a.py", "C:/a.py", "a\\b.py", "a/./b.py"])
def test_metadata_reuses_importer_path_checks(name):
    with pytest.raises(ValueError):
        code_zip.inventory_zip(zipped([(name, b"x=1")]))


@pytest.mark.parametrize(
    "name,reason", [("nested.zip", "nested_archive"), ("binary.xyz", "unknown_type")]
)
def test_unknown_and_nested_require_review(name, reason):
    report = code_zip.inventory_zip(zipped([("a.py", b"x=1"), (name, b"opaque")]))
    assert report["status"] == "blocked" and reason in report["blockers"]


def test_count_lie_rejected_before_zipinfo_allocation(monkeypatch):
    raw = bytearray(zipped([("a.py", b"x=1"), ("b.py", b"x=2")]))
    end = raw.rfind(b"PK\x05\x06")
    struct.pack_into("<2H", raw, end + 8, 1, 1)

    def forbidden(*args, **kwargs):
        raise AssertionError("Must reject count before ZipFile allocation")

    monkeypatch.setattr(zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError, match="entry count"):
        code_zip.inventory_zip(raw)


@pytest.mark.parametrize(
    "entries",
    [
        [(f"{i}.py", b"x=1") for i in range(65)],
        [("a.py", b"x" * code_zip.MIB)],
        [("A.py", b"x=1"), ("a.py", b"x=1")],
    ],
)
def test_metadata_bounds_and_collisions(entries):
    with pytest.raises(ValueError):
        code_zip.inventory_zip(zipped(entries))


@pytest.mark.parametrize("encryption_flag", [1, 0x20, 0x40])
def test_symlink_and_encryption_blocked(encryption_flag):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        item = zipfile.ZipInfo("link.py")
        item.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(item, "outside")
    with pytest.raises(ValueError):
        code_zip.inventory_zip(stream.getvalue())
    raw = bytearray(zipped([("a.py", b"x=1")]))
    central = raw.index(b"PK\x01\x02")
    struct.pack_into("<H", raw, central + 8, encryption_flag)
    with pytest.raises(ValueError):
        code_zip.inventory_zip(raw)


def test_time_limit_during_metadata_scan(monkeypatch):
    raw = zipped([("a.py", b"x=1")])
    ticks = iter([0, 0, code_zip.MAX_SECONDS + 1])
    monkeypatch.setattr(code_zip.time, "monotonic", lambda: next(ticks))
    with pytest.raises(ValueError, match="time bound"):
        code_zip.inventory_zip(raw)


def test_cli_isolated_readonly_duplicates_and_corruption(tmp_path):
    raw = zipped([("a.py", b'raise RuntimeError("NEVER RUN")\n')])
    sources = [tmp_path / name for name in ("one.zip", "copy.zip", "bad.zip")]
    for path, content in zip(sources, (raw, raw, b"broken"), strict=True):
        path.write_bytes(content)
    before = {p: p.read_bytes() for p in sources}
    done = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.cs50_zip_inventory", *map(str, sources)],
        capture_output=True,
        timeout=20,
    )
    assert done.returncode == 3, done.stderr
    report = json.loads(done.stdout)
    assert [r["status"] for r in report["archives"]] == [
        "metadata_checked",
        "metadata_checked",
        "blocked",
    ]
    assert report["archives"][1]["duplicate_archive_of"] == "one.zip"
    assert not report["import_permitted"]
    assert {p: p.read_bytes() for p in sources} == before
    assert set(tmp_path.iterdir()) == set(sources)
