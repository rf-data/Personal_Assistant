"""Bounded ZIP inspection in memory. Never extract member paths to disk."""

import io
import stat
import struct
import unicodedata
import zipfile
import zlib
from pathlib import PurePosixPath

from src.tools_materials.batch import sha
from src.tools_materials.capacity import MIB

MAX_MEMBERS = 64
MAX_TOTAL = 8 * MIB
MAX_RATIO = 100


def inspect_zip(raw):
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
    result, seen, paths, unpacked = [], set(), {}, 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) != total:
            raise ValueError("ZIP entry count mismatch")
        for item in infos:
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
                or item.flag_bits & 1
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
            if any(
                parent in paths and not paths[parent]
                for parent in (
                    str(p) for p in PurePosixPath(path).parents if str(p) != "."
                )
            ):
                raise ValueError("ZIP file/directory collision")
        for item in infos:
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
    return result
