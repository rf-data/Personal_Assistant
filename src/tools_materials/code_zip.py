"""Bounded ZIP inspection in memory. Never extract member paths to disk."""

import hashlib
import io
import stat
import struct
import time
import unicodedata
import zipfile
import zlib
from pathlib import PurePosixPath

from src.tools_materials.capacity import MIB


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


MAX_MEMBERS = 64
MAX_TOTAL = 8 * MIB
MAX_RATIO = 100
MAX_SECONDS = 5


def _within(deadline):
    if time.monotonic() >= deadline:
        raise ValueError("ZIP inspection time bound")


def _open_checked(raw, deadline):
    """Shared central-directory checks, before any member decompression."""
    _within(deadline)
    if not 1 <= len(raw) <= MIB:
        raise ValueError("ZIP raw size bound")
    # Bound allocation of ZipInfo objects before opening the central directory.
    end = raw.rfind(b"PK\x05\x06", max(0, len(raw) - 65557))
    if end < 0 or len(raw) < end + 22:
        raise ValueError("Missing ZIP end record")
    disk, start_disk, count, total, size, offset, comment = struct.unpack_from(
        "<4H2LH", raw, end + 4
    )
    if (
        disk
        or start_disk
        or count != total
        or not 1 <= total <= MAX_MEMBERS
        or offset + size != end
        or end + 22 + comment != len(raw)
        or b"PK\x06\x06" in raw[max(0, end - 76) : end]
    ):
        raise ValueError("Unsupported ZIP layout/count/ZIP64")
    # Do not trust the EOCD count before ZipFile allocates its ZipInfo objects.
    cursor, actual = offset, 0
    while cursor < end:
        _within(deadline)
        if cursor + 46 > end or raw[cursor : cursor + 4] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP central directory")
        actual += 1
        if actual > total:
            raise ValueError("ZIP entry count mismatch")
        lengths = struct.unpack_from("<3H", raw, cursor + 28)
        cursor += 46 + sum(lengths)
    if cursor != end or actual != total:
        raise ValueError("ZIP entry count mismatch")
    seen, paths, unpacked = set(), {}, 0
    archive = zipfile.ZipFile(io.BytesIO(raw))
    try:
        infos = archive.infolist()
        if len(infos) != total:
            raise ValueError("ZIP entry count mismatch")
        for item in infos:
            _within(deadline)
            name = item.orig_filename
            stripped = name[:-1] if item.is_dir() else name
            parts = stripped.split("/")
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if (
                not stripped
                or len(name) > 512
                or "\\" in name
                or ":" in name
                or any(ord(c) < 32 or ord(c) == 127 for c in name)
                or PurePosixPath(name).is_absolute()
                or any(p in {"", ".", ".."} for p in parts)
                or kind not in {0, stat.S_IFREG, stat.S_IFDIR}
                or (kind == stat.S_IFDIR) != item.is_dir()
                and kind != 0
                or item.flag_bits & (1 | 0x20 | 0x40)
                or item.extract_version >= 45
                or item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                or item.file_size > MIB
                or item.file_size > MAX_RATIO * max(1, item.compress_size)
                or item.is_dir()
                and item.file_size
            ):
                raise ValueError("Unsafe ZIP member or resource limit")
            key = unicodedata.normalize("NFC", stripped).casefold()
            if key in seen:
                raise ValueError("Colliding ZIP paths")
            seen.add(key)
            paths[key] = item.is_dir()
            unpacked += item.file_size
            if unpacked > MAX_TOTAL:
                raise ValueError("ZIP total size bound")
        for path in paths:
            _within(deadline)
            if any(
                parent in paths and not paths[parent]
                for parent in (
                    str(p) for p in PurePosixPath(path).parents if str(p) != "."
                )
            ):
                raise ValueError("ZIP file/directory collision")
        _within(deadline)
        return archive, infos
    except BaseException:
        archive.close()
        raise


def inventory_zip(raw):
    """Metadata only: no member reads, extraction, CRC/content verification.

    Reuses the importer's bounds and path checks. Unknown types, executables and
    nested archives require review. Course/week and approval are never inferred.
    """
    deadline = time.monotonic() + MAX_SECONDS
    archive, infos = _open_checked(raw, deadline)
    members, seen, possible_duplicates, blocked = [], {}, [], set()
    known = {".py", ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml"}
    nested = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".whl"}
    with archive:
        for item in infos:
            _within(deadline)
            extension = PurePosixPath(item.filename).suffix.casefold()
            kind = "directory" if item.is_dir() else "file"
            if not item.is_dir():
                if extension in nested:
                    blocked.add("nested_archive")
                elif extension not in known:
                    blocked.add("unknown_type")
                if (item.external_attr >> 16) & 0o111:
                    blocked.add("executable_mode")
                key = (item.CRC, item.file_size)
                if key in seen:
                    possible_duplicates.append([seen[key], item.filename])
                seen[key] = item.filename
            members.append(
                dict(
                    name=item.filename,
                    kind=kind,
                    extension=extension,
                    declared_bytes=item.file_size,
                    compressed_bytes=item.compress_size,
                    crc32=f"{item.CRC:08x}",
                )
            )
    if not any(m["name"].endswith(".py") and m["kind"] == "file" for m in members):
        blocked.add("no_python_member")
    _within(deadline)
    unpacked = sum(m["declared_bytes"] for m in members)
    compressed = sum(m["compressed_bytes"] for m in members)
    return dict(
        schema_version=1,
        archive_bytes=len(raw),
        sha256=sha(raw),
        entry_count=len(members),
        declared_uncompressed_bytes=unpacked,
        compression_ratio=unpacked / max(1, compressed),
        members=members,
        possible_duplicates_crc_size=possible_duplicates,
        duplicate_contents_verified=False,
        member_contents_verified=False,
        course_id=None,
        week=None,
        binding_status="operator_evidence_required",
        status="blocked" if blocked else "metadata_checked",
        blockers=sorted(blocked),
        import_approved=False,
        limits=dict(
            raw_bytes=MIB,
            members=MAX_MEMBERS,
            member_bytes=MIB,
            total_bytes=MAX_TOTAL,
            ratio=MAX_RATIO,
            seconds=MAX_SECONDS,
        ),
    )


def inspect_zip(raw):
    deadline = time.monotonic() + MAX_SECONDS
    archive, infos = _open_checked(raw, deadline)
    result = []
    with archive:
        for item in infos:
            _within(deadline)
            if item.is_dir():
                result.append(
                    (dict(name=item.filename, status="excluded_directory"), None)
                )
                continue
            try:
                with archive.open(item) as stream:
                    content = stream.read(MIB + 1)
                    if len(content) != item.file_size or stream.read(1):
                        raise ValueError("ZIP actual member size mismatch")
            except zlib.error as error:
                raise ValueError("Invalid compressed ZIP member") from error
            status = (
                "candidate_python" if item.filename.endswith(".py") else "excluded_type"
            )
            if mode := item.external_attr >> 16:
                if mode & 0o111:
                    status = "excluded_executable_mode"
            if status == "candidate_python":
                try:
                    text = content.decode("utf-8-sig", errors="strict")
                    if not text.strip() or "\x00" in text:
                        status = "excluded_binary_or_empty"
                except UnicodeError:
                    status = "excluded_encoding"
            result.append(
                (
                    dict(
                        name=item.filename,
                        sha256=sha(content),
                        bytes=len(content),
                        status=status,
                    ),
                    content,
                )
            )
    _within(deadline)
    return result
