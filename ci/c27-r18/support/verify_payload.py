"""Independent stdlib verifier. No application imports or extraction; read only."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import PurePosixPath


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def components(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Invalid path")
    parts = value.split("/")
    if PurePosixPath(value).is_absolute() or any(p in ("", ".", "..") for p in parts):
        raise ValueError("Unsafe relative path")
    return parts


def directory(parent_fd, name):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)


def absolute_root(value):
    if not value.startswith("/"):
        raise ValueError("Root must be absolute")
    current = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in components(value[1:]):
            child = directory(current, part)
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def verify_file(root_fd, entry):
    parts = components(entry["path"])
    parent = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = directory(parent, part)
            os.close(parent)
            parent = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("Nonregular file or hardlink: " + entry["path"])
            digest = hashlib.sha256()
            total = 0
            while chunk := os.read(fd, 1024 * 1024):
                total += len(chunk)
                if total > entry["bytes"]:
                    raise ValueError("Size exceeded: " + entry["path"])
                digest.update(chunk)
            after = os.fstat(fd)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise ValueError("Concurrent mutation: " + entry["path"])
            if total != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                raise ValueError("Hash/size mismatch: " + entry["path"])
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def inventory(fd, prefix="", seen=None):
    if seen is None:
        seen = set()
    for name in os.listdir(fd):
        path = prefix + name
        components(path)
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = directory(fd, name)
            try:
                inventory(child, path + "/", seen)
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            seen.add(path)
        else:
            raise ValueError("Unexpected link/special file: " + path)
    return seen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--scope", choices=("input", "overlay", "acceptance"), required=True)
    parser.add_argument("--allow-source-extras", action="store_true",
                        help="Sender only; NEVER use on a received payload")
    args = parser.parse_args()
    with open(args.manifest, "rb") as handle:
        raw = handle.read()
    if hashlib.sha256(raw).hexdigest() != args.expected_manifest_sha256:
        raise ValueError("Manifest pin mismatch")
    manifest = json.loads(raw, object_pairs_hook=unique_object)
    if args.scope == "acceptance":
        combined = {entry["path"]: entry for entry in manifest["input_files"]}
        if len(combined) != len(manifest["input_files"]):
            raise ValueError("Duplicate input path")
        overlay_paths = [entry["path"] for entry in manifest["overlay_files"]]
        if len(overlay_paths) != len(set(overlay_paths)):
            raise ValueError("Duplicate overlay path")
        for entry in manifest["overlay_files"]:
            prior = entry.get("prior_sha256")
            if prior and (entry["path"] not in combined or combined[entry["path"]]["sha256"] != prior):
                raise ValueError("Overlay prior hash differs from input manifest")
            if entry["path"] in combined and not prior:
                raise ValueError("Undeclared overlay replacement")
            combined[entry["path"]] = entry
        entries = list(combined.values())
    else:
        entries = manifest[args.scope + "_files"]
    paths = [entry["path"] for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate file path")
    fd = absolute_root(args.root)
    try:
        if not args.allow_source_extras and inventory(fd) != set(paths):
            raise ValueError("Receiver file set differs from allowlist")
        for entry in entries:
            verify_file(fd, entry)
        if not args.allow_source_extras and inventory(fd) != set(paths):
            raise ValueError("Receiver file set changed during verification")
    finally:
        os.close(fd)
    print(json.dumps({"status": "VERIFIED", "scope": args.scope,
                      "files": len(entries), "bytes": sum(e["bytes"] for e in entries),
                      "exact_receiver_set": not args.allow_source_extras,
                      "manifest_sha256": args.expected_manifest_sha256}))


if __name__ == "__main__":
    main()
