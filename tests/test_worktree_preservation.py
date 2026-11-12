"""Executable preservation protocol experiment, restricted to self-created fixtures.

No production archive/restore API or CLI. The fixture owns all input/output roots
under its TemporaryDirectory; no caller-supplied repository is accepted.
"""

import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import patch


class Hold(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_ALLOW_PROTOCOL="file",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_NO_LAZY_FETCH="1",
        GIT_OPTIONAL_LOCKS="0",
        LC_ALL="C",
    )
    result = subprocess.run(
        [
            "git",
            "--no-optional-locks",
            "-C",
            str(root),
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "init.templateDir=",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=synthetic@example.invalid",
            "-c",
            "commit.gpgSign=false",
            *args,
        ],
        env=env,
        capture_output=True,
        timeout=15,
    )
    if result.returncode:
        raise Hold("git operation failed")
    return result.stdout.strip()


def relative_name(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise Hold("invalid relative name")
    parts = name.split("/")
    if PurePosixPath(name).is_absolute() or any(
        p in {"", ".", "..", ".git"} for p in parts
    ):
        raise Hold("unsafe relative name")
    return name


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Hold("duplicate JSON key")
        result[key] = value
    return result


def independent_verify(archive, trusted_manifest_sha256):
    """Reader written separately from fixture capture. Exact names, types, hashes."""
    if archive.is_symlink() or any(p.is_symlink() for p in archive.parents):
        raise Hold("archive path symlink")
    manifest_path = archive / "manifest.json"
    if (
        not stat.S_ISREG(manifest_path.lstat().st_mode)
        or manifest_path.stat().st_nlink != 1
    ):
        raise Hold("manifest inode")
    raw = manifest_path.read_bytes()
    if len(raw) > 65536 or digest(raw) != trusted_manifest_sha256:
        raise Hold("untrusted or oversized manifest")
    manifest = json.loads(raw, object_pairs_hook=unique_keys)
    if manifest.get("version") != 1 or manifest.get("complete") is not True:
        raise Hold("incomplete manifest")
    if manifest.get("scope") != "synthetic-regular-files-only":
        raise Hold("unsupported scope")
    if manifest.get("repository") != "example/synthetic":
        raise Hold("repository mismatch")
    head = manifest.get("head", "")
    if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
        raise Hold("invalid head")
    # Check all metadata before reading payloads, so a symlinked parent cannot
    # redirect even an otherwise valid-looking file entry to external bytes.
    actual = {"manifest.json"}
    device = archive.stat().st_dev
    for directory, dirs, files in os.walk(archive, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            info = path.lstat()
            if info.st_dev != device or not (
                stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)
            ):
                raise Hold("unsupported payload inode or device")
            if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                raise Hold("payload hardlink")
            actual.add(path.relative_to(archive).as_posix())
            if len(actual) > 101:
                raise Hold("payload enumeration budget")
    expected = {"manifest.json"}
    records = manifest["entries"]
    if len(records) > 100:
        raise Hold("entry budget")
    total = 0
    for item in records:
        name = relative_name(item["path"])
        if (
            name in expected
            or name not in {"history.bundle", "files"}
            and not name.startswith("files/")
        ):
            raise Hold("duplicate or unknown payload namespace")
        expected.add(name)
        path = archive / name
        info = path.lstat()
        if item["type"] == "directory":
            if not stat.S_ISDIR(info.st_mode):
                raise Hold("directory type mismatch")
        elif item["type"] == "file":
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise Hold("regular unlinked payload required")
            total += info.st_size
            if total > 1024 * 1024 or info.st_size != item["size"]:
                raise Hold("size budget or mismatch")
            if digest(path.read_bytes()) != item["sha256"]:
                raise Hold("payload digest mismatch")
        else:
            raise Hold("unsupported inode type")
        if stat.S_IMODE(info.st_mode) != item["mode"]:
            raise Hold("mode mismatch")
    if "history.bundle" not in expected or "files" not in expected:
        raise Hold("missing required payload")
    if actual != expected:
        raise Hold("unexpected or missing payload")
    return manifest


class SyntheticProtocol:
    """Only create this from unittest; all repositories and data are fabricated."""

    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-preservation-")
        self.base = Path(self.temp.name)
        self.repo = self.base / "source"
        self.repo.mkdir(mode=0o700)
        git(self.repo, "init", "--initial-branch=master")
        (self.repo / ".gitignore").write_text("ignored/\n")
        (self.repo / "tracked.txt").write_text("synthetic committed bytes\n")
        (self.repo / "run.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.repo / "run.sh").chmod(0o700)
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "Synthetic fixture")
        self.head = git(self.repo, "rev-parse", "HEAD").decode()
        (self.repo / "ignored").mkdir(mode=0o700)
        (self.repo / "ignored" / "local.bin").write_bytes(b"synthetic ignored bytes")
        (self.repo / "untracked\nname").write_bytes(b"synthetic untracked bytes")
        (self.repo / "empty").mkdir(mode=0o700)
        self.archive = self.base / "archive"

    def scan(self, max_entries=100, max_bytes=1024 * 1024):
        rows = []
        size = 0
        for directory, dirs, files in os.walk(self.repo, followlinks=False):
            if Path(directory) == self.repo:
                dirs.remove(".git")
            for name in sorted(dirs + files):
                p = Path(directory) / name
                info = p.lstat()
                rel = p.relative_to(self.repo).as_posix()
                relative_name(rel)
                if info.st_dev != self.repo.stat().st_dev:
                    raise Hold("mount boundary")
                row = {"path": "files/" + rel, "mode": stat.S_IMODE(info.st_mode)}
                if stat.S_ISDIR(info.st_mode):
                    row["type"] = "directory"
                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                    fd = os.open(p, flags)
                    with os.fdopen(fd, "rb") as stream:
                        opened = os.fstat(stream.fileno())
                        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                            raise Hold("source changed")
                        data = stream.read(max_bytes + 1)
                    size += len(data)
                    if size > max_bytes:
                        raise Hold("byte budget")
                    row.update(type="file", size=len(data), sha256=digest(data))
                else:
                    raise Hold("unsupported inode or hardlink")
                rows.append(row)
                if len(rows) > max_entries:
                    raise Hold("entry budget")
        return sorted(rows, key=lambda x: x["path"])

    def capture(self, *, max_entries=100, max_bytes=1024 * 1024, after_copy=None):
        # Dirty tracked/index state is intentionally unsupported by this experiment.
        if git(self.repo, "status", "--porcelain", "--untracked-files=no"):
            raise Hold("dirty tracked or index state requires expanded protocol")
        if git(self.repo, "ls-files", "-v").splitlines() != [
            b"H .gitignore",
            b"H run.sh",
            b"H tracked.txt",
        ]:
            raise Hold("unexpected or masked index")
        before = self.scan(max_entries, max_bytes)
        self.archive.mkdir(mode=0o700)  # exclusive; no overwrite/adopt
        git(
            self.repo,
            "bundle",
            "create",
            str(self.archive / "history.bundle"),
            "refs/heads/master",
        )
        (self.archive / "history.bundle").chmod(0o600)
        (self.archive / "files").mkdir(mode=0o700)
        for row in before:
            target = self.archive / row["path"]
            source = self.repo / row["path"].removeprefix("files/")
            if row["type"] == "directory":
                target.mkdir(mode=row["mode"])
            else:
                with target.open("xb") as out:
                    out.write(source.read_bytes())
                target.chmod(row["mode"])
        if after_copy:
            after_copy()
        if (
            self.scan(max_entries, max_bytes) != before
            or git(self.repo, "rev-parse", "HEAD").decode() != self.head
        ):
            raise Hold("source changed during capture")
        bundle = self.archive / "history.bundle"
        rows = [
            {"path": "files", "type": "directory", "mode": 0o700},
            {
                "path": "history.bundle",
                "type": "file",
                "mode": 0o600,
                "size": bundle.stat().st_size,
                "sha256": digest(bundle.read_bytes()),
            },
            *before,
        ]
        manifest = {
            "version": 1,
            "repository": "example/synthetic",
            "scope": "synthetic-regular-files-only",
            "head": self.head,
            "complete": True,
            "entries": rows,
        }
        raw = json.dumps(manifest, sort_keys=True).encode()
        with (self.archive / "manifest.json").open("xb") as out:
            out.write(raw)  # completion marker written last
        return digest(raw)

    def alter_manifest(self, change):
        path = self.archive / "manifest.json"
        manifest = json.loads(path.read_bytes())
        change(manifest)
        path.write_text(json.dumps(manifest, sort_keys=True))
        return digest(path.read_bytes())

    def restore(self, anchor, name="restore"):
        # Target is an unambiguous fixture child; operator paths cannot be supplied.
        if name not in {"restore", "restore-second"}:
            raise Hold("invalid synthetic target")
        manifest = independent_verify(self.archive, anchor)
        target = self.base / name
        target.mkdir(mode=0o700)
        git(target, "init", "--initial-branch=restore")
        git(target, "bundle", "verify", str(self.archive / "history.bundle"))
        git(target, "fetch", str(self.archive / "history.bundle"), "refs/heads/master")
        git(target, "cat-file", "-e", manifest["head"] + "^{commit}")
        git(target, "checkout", "--detach", manifest["head"])
        # Exact snapshot overlay; fixture only, no existing operator files.
        for row in manifest["entries"]:
            if not row["path"].startswith("files/"):
                continue
            output = target / row["path"].removeprefix("files/")
            if row["type"] == "directory":
                output.mkdir(exist_ok=True)
            else:
                output.write_bytes((self.archive / row["path"]).read_bytes())
            output.chmod(row["mode"])
        # Independently recompute restored payload bytes and mode; verify Git closure.
        for row in manifest["entries"]:
            if row["path"].startswith("files/"):
                output = target / row["path"].removeprefix("files/")
                if stat.S_IMODE(output.stat().st_mode) != row["mode"]:
                    raise Hold("restored mode mismatch")
                if (
                    row["type"] == "file"
                    and digest(output.read_bytes()) != row["sha256"]
                ):
                    raise Hold("restored hash mismatch")
        actual = set()
        for directory, dirs, files in os.walk(target, followlinks=False):
            if Path(directory) == target:
                dirs.remove(".git")
            for name in dirs + files:
                path = Path(directory) / name
                if path.is_symlink():
                    raise Hold("restored symlink")
                actual.add(path.relative_to(target).as_posix())
        expected = {
            r["path"].removeprefix("files/")
            for r in manifest["entries"]
            if r["path"].startswith("files/")
        }
        if actual != expected:
            raise Hold("restored inventory mismatch")
        if git(target, "rev-parse", "HEAD").decode() != manifest["head"]:
            raise Hold("restored head mismatch")
        git(target, "fsck", "--full", "--no-reflogs")
        if (target / ".git/objects/info/alternates").exists():
            raise Hold("shared object dependency")
        return target


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.f = SyntheticProtocol()
        self.addCleanup(self.f.temp.cleanup)

    def test_independent_restore_without_source_or_remote(self):
        anchor = self.f.capture()
        self.f.repo.rename(self.f.base / "source-unavailable")
        target = self.f.restore(anchor)
        self.assertEqual(
            (target / "ignored/local.bin").read_bytes(), b"synthetic ignored bytes"
        )
        self.assertTrue((target / "empty").is_dir())
        self.assertEqual(
            (target / "untracked\nname").read_bytes(), b"synthetic untracked bytes"
        )
        self.assertEqual(stat.S_IMODE((target / "run.sh").stat().st_mode), 0o700)

    def test_payload_corruption_and_missing_payload(self):
        anchor = self.f.capture()
        p = self.f.archive / "files/ignored/local.bin"
        p.write_bytes(b"corrupt")
        with self.assertRaises(Hold):
            self.f.restore(anchor)
        p.unlink()  # synthetic fixture only
        with self.assertRaises((Hold, OSError)):
            self.f.restore(anchor)

    def test_manifest_requires_independent_trusted_digest(self):
        anchor = self.f.capture()
        self.f.alter_manifest(lambda m: m.update(head="0" * 40))
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_incomplete_manifest(self):
        self.f.capture()
        anchor = self.f.alter_manifest(lambda m: m.update(complete=False))
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_traversal_absolute_git_and_duplicate_names(self):
        self.f.capture()
        original = (self.f.archive / "manifest.json").read_bytes()
        for name in [
            "../escape",
            "/tmp/escape",
            "files/../escape",
            "files/.git/config",
            "files//x",
            "files/./x",
            "files\\x",
            "history.bundle",
        ]:
            with self.subTest(name=name):
                (self.f.archive / "manifest.json").write_bytes(original)
                anchor = self.f.alter_manifest(
                    lambda m, name=name: m["entries"].append(
                        {
                            "path": name,
                            "type": "file",
                            "mode": 0o600,
                            "size": 0,
                            "sha256": digest(b""),
                        }
                    )
                )
                with self.assertRaises((Hold, OSError)):
                    self.f.restore(anchor)

    def test_source_symlink_nested_repository_hardlink_fifo(self):
        for kind in ["symlink", "nested", "hardlink", "fifo"]:
            with self.subTest(kind=kind):
                p = self.f.repo / "unsafe"
                if kind == "symlink":
                    p.symlink_to("/nonexistent/external")
                elif kind == "nested":
                    p.mkdir()
                    (p / ".git").write_text("synthetic nested marker")
                elif kind == "hardlink":
                    os.link(self.f.repo / "tracked.txt", p)
                else:
                    os.mkfifo(p)
                with self.assertRaises(Hold):
                    self.f.capture()
                if kind == "nested":
                    (p / ".git").unlink()
                    p.rmdir()
                else:
                    p.unlink()

    def test_dirty_tracked_and_staged_state_require_expanded_protocol(self):
        (self.f.repo / "tracked.txt").write_text("synthetic changed")
        with self.assertRaises(Hold):
            self.f.capture()
        git(self.f.repo, "add", "tracked.txt")
        with self.assertRaises(Hold):
            self.f.capture()

    def test_masked_index_rejected(self):
        git(self.f.repo, "update-index", "--assume-unchanged", "tracked.txt")
        with self.assertRaises(Hold):
            self.f.capture()

    def test_entry_and_byte_budget(self):
        with self.assertRaises(Hold):
            self.f.capture(max_entries=1)
        with self.assertRaises(Hold):
            self.f.capture(max_bytes=1)

    def test_source_mutation_leaves_no_complete_manifest(self):
        with self.assertRaises(Hold):
            self.f.capture(
                after_copy=lambda: (self.f.repo / "untracked\nname").write_bytes(
                    b"changed"
                )
            )
        self.assertFalse((self.f.archive / "manifest.json").exists())

    def test_existing_archive_and_restore_destinations_rejected(self):
        anchor = self.f.capture()
        with self.assertRaises(FileExistsError):
            self.f.capture()
        self.f.restore(anchor)
        with self.assertRaises(FileExistsError):
            self.f.restore(anchor)

    def test_extra_payload_symlink_and_mode_change_rejected(self):
        anchor = self.f.capture()
        p = self.f.archive / "extra"
        p.write_bytes(b"unexpected")
        with self.assertRaises(Hold):
            self.f.restore(anchor)
        p.unlink()
        p.symlink_to("/nonexistent")
        with self.assertRaises(Hold):
            self.f.restore(anchor)
        p.unlink()
        (self.f.archive / "files/run.sh").chmod(0o600)
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_repository_mismatch_and_unavailable_commit(self):
        self.f.capture()
        anchor = self.f.alter_manifest(
            lambda m: m.update(repository="other/repository")
        )
        with self.assertRaises(Hold):
            self.f.restore(anchor)
        anchor = self.f.alter_manifest(
            lambda m: m.update(repository="example/synthetic", head="0" * 40)
        )
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_incremental_bundle_fails_without_original_prerequisites(self):
        self.f.capture()
        (self.f.repo / "tracked.txt").write_text("synthetic second commit")
        git(self.f.repo, "add", "tracked.txt")
        git(self.f.repo, "commit", "-m", "Synthetic second")
        self.f.head = git(self.f.repo, "rev-parse", "HEAD").decode()
        incremental = self.f.base / "incremental.bundle"
        git(
            self.f.repo,
            "bundle",
            "create",
            str(incremental),
            "refs/heads/master",
            "^HEAD~1",
        )
        p = self.f.archive / "history.bundle"
        p.write_bytes(incremental.read_bytes())

        def update(m):
            m["head"] = self.f.head
            row = next(x for x in m["entries"] if x["path"] == "history.bundle")
            row.update(size=p.stat().st_size, sha256=digest(p.read_bytes()))

        anchor = self.f.alter_manifest(update)
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_interrupted_capture_without_manifest_is_not_backup(self):
        self.f.archive.mkdir()
        (self.f.archive / "partial").write_bytes(b"synthetic partial")
        with self.assertRaises((Hold, OSError)):
            self.f.restore("0" * 64)

    def test_permission_and_capacity_failures_leave_no_complete_manifest(self):
        # Inject failures; permission bits alone are ineffective under privileged CI.
        with patch("os.open", side_effect=PermissionError("synthetic denied read")):
            with self.assertRaises(PermissionError):
                self.f.scan()

        def capacity_failure():
            raise OSError(28, "synthetic full disk")

        with self.assertRaises(OSError):
            self.f.capture(after_copy=capacity_failure)
        self.assertFalse((self.f.archive / "manifest.json").exists())

    def test_git_timeout_is_not_success(self):
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("synthetic git", 15)
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.f.capture()
        self.assertFalse(self.f.archive.exists())

    def test_archive_ancestor_symlink_rejected(self):
        anchor = self.f.capture()
        alias = self.f.base / "alias"
        alias.symlink_to(self.f.archive, target_is_directory=True)
        with self.assertRaises(Hold):
            independent_verify(alias, anchor)

    def test_omitted_committed_file_fails_exact_restore_inventory(self):
        self.f.capture()
        anchor = self.f.alter_manifest(
            lambda m: m.update(
                entries=[
                    row for row in m["entries"] if row["path"] != "files/tracked.txt"
                ]
            )
        )
        (self.f.archive / "files/tracked.txt").unlink()
        with self.assertRaises(Hold):
            self.f.restore(anchor)

    def test_duplicate_json_keys_rejected_even_with_matching_digest(self):
        self.f.capture()
        p = self.f.archive / "manifest.json"
        raw = p.read_bytes().replace(b'"version": 1', b'"version": 0, "version": 1')
        p.write_bytes(raw)
        with self.assertRaises(Hold):
            self.f.restore(digest(raw))


if __name__ == "__main__":
    unittest.main()
