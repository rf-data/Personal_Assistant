"""Bounded, synthetic-tested, read-only observation of one exact registered root.

No removal decision. Linux openat2 is required; unsupported systems fail closed.
Working status compares raw bytes with the index without running Git filters.
trusted_local_diagnostic assumes a non-adversarial local environment; observations
are not an atomic snapshot of a concurrently changing repository. Safety stays BLOCKED.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import errno
import fnmatch
import hashlib
import json
import math
import os
import platform
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime

if __package__:
    from . import worktree_fast_inventory as fast
    from . import worktree_manager as manager
else:
    import worktree_fast_inventory as fast
    import worktree_manager as manager

HOLD = fast.HOLD
STRICT = "strict"
DIAGNOSTIC = "trusted_local_diagnostic"
MODES = (STRICT, DIAGNOSTIC)
ISOLATION_BLOCKER = "git_metadata_isolation_not_verified"
REQUIRED_OBSERVATIONS = (
    "identity",
    "integration",
    "git_status",
    "storage",
    "consistency",
)
UNVERIFIED = (
    ISOLATION_BLOCKER,
    "backup_and_independent_restore_not_verified",
    "actual_reclaimable_storage_not_verified",
    "endpoint_checks_do_not_exclude_change_and_revert_races",
    "ownership_and_nonuse_not_verified",
)
Error = fast.ObservationError
HEAD = ("rev-parse", "--verify", "HEAD")
FORMAT = ("rev-parse", "--show-object-format")
CONFIG = ("config", "--null", "--list", "--no-includes")
INDEX = ("ls-files", "--stage", "-z")
FLAGS = ("ls-files", "-v", "-z")
STAGED = ("ls-tree", "-r", "-z", "--full-tree", "HEAD")
ALLOWED = (
    fast.IDENTITY,
    fast.REGISTRY,
    fast.REFS,
    HEAD,
    FORMAT,
    CONFIG,
    INDEX,
    FLAGS,
    STAGED,
)
DEFAULTS = dict(
    subprocess_seconds=3.0,
    worker_seconds=12.0,
    deadline_seconds=15.0,
    max_git_output_bytes=1024 * 1024,
    max_total_git_bytes=4 * 1024 * 1024,
    max_report_bytes=2 * 1024 * 1024,
    max_entries=20000,
    max_read_bytes=16 * 1024 * 1024,
    max_depth=64,
)


def encoded(path):
    raw = os.fsencode(path)
    return dict(
        display=os.fsdecode(raw), bytes_base64=base64.b64encode(raw).decode("ascii")
    )


def base_report(mode=STRICT):
    return dict(
        schema_version=1,
        generated_at=datetime.now(UTC).isoformat(),
        mode=mode,
        diagnostic_status="BLOCKED",
        atomic_snapshot=False,
        environment_assumption=(
            "non_adversarial_local"
            if mode == DIAGNOSTIC
            else "strict_isolation_required"
        ),
        required_observations={key: "NOT_CHECKED" for key in REQUIRED_OBSERVATIONS},
        complete=False,
        observation_complete=False,
        safety_assurance="BLOCKED",
        safe_to_remove=False,
        lifecycle_hold=HOLD,
        removal_approval_sufficient=False,
        lifecycle_decision=HOLD,
        dimensions={
            **{
                k: "NOT_CHECKED"
                for k in (
                    "identity",
                    "git_status",
                    "integration",
                    "storage",
                    "preservation",
                )
            },
            "safety": "BLOCKED",
        },
        errors=[],
        uncertainties=list(UNVERIFIED),
        operations=[],
        snapshots={},
        git_subprocess_count=None,
        worker_subprocess_count=0,
        actual_reclaimable_storage="NOT_VERIFIED",
        preservation=dict(
            backup="NOT_VERIFIED",
            independent_restore="NOT_VERIFIED",
            evidence_references=[],
            references_verified=False,
        ),
    )


def compact_failure(mode, code):
    report = fail(base_report(mode), code)
    if mode == DIAGNOSTIC:
        report["diagnostic_status"] = "INCOMPLETE"
    return report


def fail(report, code, dimension=None):
    report["complete"] = False
    report["errors"].append(code)
    if dimension:
        report["dimensions"][dimension] = "BLOCKED"
    if code not in report["uncertainties"]:
        report["uncertainties"].append(code)
    return report


def json_bytes(report):
    return json.dumps(
        report,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def bounded_process(
    command, *, timeout, max_bytes, env=None, pass_fds=(), data=None, group=False
):
    """Bound both pipes and elapsed time; no temporary output spooling."""
    process = None
    end = time.monotonic() + timeout
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            pass_fds=pass_fds,
            start_new_session=group,
        )
        # Worker request is capped at 16 KiB; only the worker uses stdin.
        if data is not None:
            os.set_blocking(process.stdin.fileno(), False)
        output = {"out": bytearray(), "err": bytearray()}
        size, written = 0, 0
        with selectors.DefaultSelector() as selector:
            for label, pipe in (("out", process.stdout), ("err", process.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, label)
            if data is not None:
                selector.register(process.stdin, selectors.EVENT_WRITE, "in")
            while selector.get_map():
                remaining = end - time.monotonic()
                if remaining <= 0:
                    raise Error("subprocess_timeout")
                for key, _ in selector.select(remaining):
                    if key.data == "in":
                        count = os.write(key.fd, data[written:])
                        written += count
                        if written == len(data):
                            selector.unregister(key.fileobj)
                            process.stdin.close()
                        continue
                    chunk = os.read(key.fd, min(65536, max_bytes - size + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        size += len(chunk)
                        if size > max_bytes:
                            raise Error("subprocess_output_limit")
                        output[key.data].extend(chunk)
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise Error("subprocess_timeout")
        code = process.wait(timeout=remaining)
        if code:
            raise Error("subprocess_nonzero_exit")
        if output["err"]:
            raise Error("subprocess_stderr")
        return bytes(output["out"])
    except subprocess.TimeoutExpired:
        raise Error("subprocess_timeout") from None
    except OSError:
        raise Error("subprocess_os_error") from None
    finally:
        if process is not None:
            # A worker owns a session: terminate its Git children as well, even if
            # the worker already exited unexpectedly. No detached helpers allowed.
            if group:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass  # Kernel-uninterruptible I/O cannot be given a realtime bound.
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()


class OpenHow(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("mode", ctypes.c_uint64),
        ("resolve", ctypes.c_uint64),
    ]


def safe_open(parent, name, flags, *, no_xdev=True):
    """Descriptor-relative Linux openat2; reject symlinks, escapes and bind mounts."""
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "aarch64"}:
        raise Error("openat2_platform_unsupported")
    how = OpenHow(
        flags | os.O_CLOEXEC | os.O_NOFOLLOW, 0, 0x08 | 0x04 | (0x01 if no_xdev else 0)
    )  # BENEATH, NO_SYMLINKS, NO_XDEV
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(
        ctypes.c_long(437),
        ctypes.c_int(parent),
        ctypes.c_char_p(os.fsencode(name)),
        ctypes.byref(how),
        ctypes.sizeof(how),
    )
    if result < 0:
        number = ctypes.get_errno()
        if number in {errno.ENOSYS, errno.EINVAL}:
            raise Error("openat2_unavailable")
        raise OSError(number, "safe_open_failed")
    return result


def canonical(path):
    raw = os.fsencode(path)
    if (
        not raw.startswith(b"/")
        or raw == b"/"
        or b"\0" in raw
        or any(part in {b"", b".", b".."} for part in raw[1:].split(b"/"))
    ):
        raise Error("noncanonical_or_unsafe_root")
    return raw


def open_absolute(path):
    raw = canonical(path)
    root = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        # Absolute ancestors may reside on different filesystems. Never follow
        # links; NO_XDEV applies to all accesses *beneath* the selected roots.
        return safe_open(root, raw[1:], os.O_RDONLY | os.O_DIRECTORY, no_xdev=False)
    finally:
        os.close(root)


def signature(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


class Observer:
    def __init__(self, request):
        self.request = request
        self.limits = request["limits"]
        self.end = time.monotonic() + self.limits["deadline_seconds"]
        self.report = base_report(request.get("mode", STRICT))
        if self.report["mode"] == DIAGNOSTIC:
            self.report["diagnostic_status"] = "INCOMPLETE"
        self.report["git_subprocess_count"] = 0
        self.report["selected_path"] = encoded(request["worktree"])
        self.report["limits"] = self.limits
        self.report["preservation"]["evidence_references"] = request["evidence"]
        self.root = self.gitdir = self.common = None
        self.open_fds = set()
        self.read_bytes = self.entries = self.git_bytes = 0
        self.storage = dict(
            logical_regular_bytes=0,
            unique_inode_logical_bytes=0,
            entries=0,
            metadata_entries=0,
            symlinks=[],
            nested_repositories=[],
            mount_boundaries=[],
            hardlink_indicators=[],
            skipped=[],
            complete=False,
            excludes=["root .git administration"],
            actual_reclaimable_storage="NOT_VERIFIED",
        )
        self.report["storage"] = self.storage
        self.files = {}
        self.ignore_files = {}

    def check(self):
        if time.monotonic() >= self.end:
            raise Error("overall_deadline")

    def count(self, metadata=False):
        self.check()
        self.entries += 1
        self.storage["metadata_entries" if metadata else "entries"] += 1
        if self.entries > self.limits["max_entries"]:
            raise Error("filesystem_entry_limit")

    def read(self, parent, path, limit=None):
        fd = safe_open(parent, path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise Error("nonregular_metadata_or_file")
            cap = min(
                self.limits["max_read_bytes"] - self.read_bytes,
                limit if limit is not None else self.limits["max_read_bytes"],
            )
            if before.st_size > cap:
                raise Error("file_read_byte_limit")
            chunks = []
            while True:
                self.check()
                chunk = os.read(fd, min(65536, cap + 1))
                if not chunk:
                    break
                self.read_bytes += len(chunk)
                cap -= len(chunk)
                if cap < 0:
                    raise Error("file_read_byte_limit")
                chunks.append(chunk)
            if signature(before) != signature(os.fstat(fd)):
                raise Error("file_changed_during_read")
            return b"".join(chunks)
        finally:
            os.close(fd)

    def optional_read(self, parent, path):
        try:
            return self.read(parent, path)
        except FileNotFoundError:
            return b""

    def git(self, args, label):
        is_counts = (
            len(args) == 5
            and args[:3] == ("rev-list", "--left-right", "--count")
            and args[-1] == "--"
            and len(args[3].split("...")) == 2
            and all(fast.SHA.fullmatch(x.encode("ascii")) for x in args[3].split("..."))
        )
        if args not in ALLOWED and not is_counts:
            raise Error("command_not_allowed")
        self.check()
        entry = dict(operation=label)
        self.report["operations"].append(entry)
        tick = time.monotonic()
        self.report["git_subprocess_count"] += 1
        command = [
            "git",
            "--no-optional-locks",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.preloadIndex=false",
            "-c",
            "maintenance.auto=false",
            "-c",
            "gc.auto=0",
            "-c",
            "protocol.allow=never",
            "-c",
            "diff.external=",
            "--git-dir=/proc/self/fd/" + str(self.gitdir),
            "--work-tree=/proc/self/fd/" + str(self.root),
            *args,
        ]
        try:
            cap = min(
                self.limits["max_git_output_bytes"],
                self.limits["max_total_git_bytes"] - self.git_bytes,
            )
            if cap <= 0:
                raise Error("total_git_output_limit")
            result = bounded_process(
                command,
                timeout=min(
                    self.limits["subprocess_seconds"], self.end - time.monotonic()
                ),
                max_bytes=cap,
                env=fast.git_environment(),
                pass_fds=tuple({self.root, self.gitdir, self.common}),
            )
            self.git_bytes += len(result)
            entry["stdout_bytes"] = len(result)
            self.check()
            return result
        except Error as exc:
            entry["error"] = str(exc)
            raise
        finally:
            entry["seconds"] = time.monotonic() - tick

    def audit_metadata(self, fd, relative=b"", depth=0):
        """Check Git-used metadata, not other worktrees' administrative folders."""
        if depth > self.limits["max_depth"]:
            raise Error("filesystem_depth_limit")
        with os.scandir(fd) as stream:
            for item in stream:
                self.count(metadata=True)
                name = os.fsencode(item.name)
                path = relative + (b"/" if relative else b"") + name
                info = item.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise Error("symlink_in_git_metadata")
                # O_PATH validates even regular-file bind mounts without reading.
                probe = safe_open(fd, name, os.O_PATH)
                os.close(probe)
                if not relative and name in {b"worktrees", b"hooks", b"logs"}:
                    if name == b"worktrees":
                        child = safe_open(fd, name, os.O_RDONLY | os.O_DIRECTORY)
                        try:
                            self.audit_registry_metadata(child)
                        finally:
                            os.close(child)
                    continue
                if info.st_dev != os.fstat(fd).st_dev:
                    raise Error("mount_in_git_metadata")
                if stat.S_ISDIR(info.st_mode):
                    child = safe_open(fd, name, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        self.audit_metadata(child, path, depth + 1)
                    finally:
                        os.close(child)
                elif not stat.S_ISREG(info.st_mode):
                    raise Error("special_git_metadata")
                elif (
                    path
                    in {
                        b"objects/info/alternates",
                        b"objects/info/http-alternates",
                        b"info/grafts",
                        b"info/attributes",
                        b"shallow",
                    }
                    and info.st_size
                ) or path.endswith(b".promisor"):
                    raise Error("unsupported_git_object_or_attribute_layout")

    def audit_registry_metadata(self, fd):
        # These are registry administrative records, never checkout contents.
        with os.scandir(fd) as registrations:
            for row in registrations:
                self.count(metadata=True)
                child = safe_open(fd, row.name, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    with os.scandir(child) as fields:
                        for field in fields:
                            self.count(metadata=True)
                            info = field.stat(follow_symlinks=False)
                            if stat.S_ISLNK(info.st_mode):
                                raise Error("symlink_in_registry_metadata")
                            probe = safe_open(child, field.name, os.O_PATH)
                            os.close(probe)
                            # Git worktree list needs these direct regular files.
                            if field.name in {
                                "HEAD",
                                "gitdir",
                                "commondir",
                                "locked",
                            } and not stat.S_ISREG(info.st_mode):
                                raise Error("unsafe_registry_metadata")
                finally:
                    os.close(child)

    def resolve_repository(self, path):
        path = canonical(path)
        root = open_absolute(path)
        self.open_fds.add(root)
        marker = os.stat(b".git", dir_fd=root, follow_symlinks=False)
        if stat.S_ISDIR(marker.st_mode):
            gitdir_path, pointer = path + b"/.git", None
        elif stat.S_ISREG(marker.st_mode):
            pointer = self.read(root, b".git", 8192)
            if not pointer.startswith(b"gitdir: ") or not pointer.endswith(b"\n"):
                raise Error("invalid_git_pointer")
            target = pointer[8:-1]
            gitdir_path = canonical(
                target
                if target.startswith(b"/")
                else os.path.normpath(path + b"/" + target)
            )
        else:
            raise Error("unsafe_git_marker")
        gitdir = open_absolute(gitdir_path)
        self.open_fds.add(gitdir)
        common_pointer = self.optional_read(gitdir, b"commondir")
        if common_pointer and not common_pointer.endswith(b"\n"):
            raise Error("invalid_common_pointer")
        common_path = (
            os.path.normpath(gitdir_path + b"/" + common_pointer[:-1])
            if common_pointer and not common_pointer.startswith(b"/")
            else common_pointer[:-1]
            if common_pointer
            else gitdir_path
        )
        common = open_absolute(common_path)
        self.open_fds.add(common)
        if pointer is not None:
            if (
                os.path.dirname(os.path.dirname(gitdir_path)) != common_path
                or os.path.basename(os.path.dirname(gitdir_path)) != b"worktrees"
                or self.read(gitdir, b"gitdir", 8192) != path + b"/.git\n"
            ):
                raise Error("forward_reverse_identity_mismatch")
        elif common_pointer:
            raise Error("unexpected_primary_common_pointer")
        return dict(
            path=path,
            root=root,
            gitdir=gitdir,
            common=common,
            gitdir_path=gitdir_path,
            common_path=common_path,
            pointer=pointer,
            common_pointer=common_pointer,
        )

    def identity(self):
        selected = self.resolve_repository(self.request["worktree"])
        for key in (
            "root",
            "gitdir",
            "common",
            "gitdir_path",
            "common_path",
            "pointer",
            "common_pointer",
        ):
            setattr(self, key, selected[key])
        path = selected["path"]
        self.anchor = self.resolve_repository(self.request["repository"])
        common = os.fstat(self.common)
        anchor_common = os.fstat(self.anchor["common"])
        if self.common_path != self.anchor["common_path"] or (
            common.st_dev,
            common.st_ino,
        ) != (anchor_common.st_dev, anchor_common.st_ino):
            raise Error("selected_repository_identity_mismatch")
        self.audit_metadata(self.common)
        if self.common_path != self.gitdir_path:
            self.audit_metadata(self.gitdir)
        # Pin metadata bytes that affect status and configuration. NOFOLLOW reads.
        self.pinned = {}
        for label, fd, file in (
            ("config", self.common, b"config"),
            ("index", self.gitdir, b"index"),
            ("HEAD", self.gitdir, b"HEAD"),
            ("exclude", self.common, b"info/exclude"),
        ):
            self.pinned[label] = self.optional_read(fd, file)
        config = self.git(CONFIG, "configuration")
        for field in config.split(b"\0"):
            if not field:
                continue
            key, sep, value = field.partition(b"\n")
            key = key.lower()
            if not sep:
                raise Error("invalid_configuration")
            if (
                key.startswith((b"include.", b"includeif.", b"filter.", b"extensions."))
                and key
                not in {b"extensions.objectformat", b"extensions.preciousobjects"}
                or key
                in {
                    b"core.excludesfile",
                    b"core.attributesfile",
                    b"core.worktree",
                    b"core.sparsecheckout",
                    b"core.sparsecheckoutcone",
                    b"core.symlinks",
                }
                or key in {b"core.autocrlf", b"core.ignorecase"}
                and value.lower() not in {b"false", b"0"}
            ):
                raise Error("unsupported_repository_configuration")
        self.report["repository_identity"] = dict(
            selected=encoded(path),
            registry_repository=encoded(self.anchor["path"]),
            git_directory=encoded(self.gitdir_path),
            common_directory=encoded(self.common_path),
            device=os.fstat(self.root).st_dev,
            inode=os.fstat(self.root).st_ino,
            common_device=os.fstat(self.common).st_dev,
            common_inode=os.fstat(self.common).st_ino,
            origin_identity="NOT_VERIFIED",
        )
        # Git canonicalizes the pinned descriptor; require the exact registered root.
        top = self.git(fast.IDENTITY, "pinned_root")
        if top != path + b"\n":
            raise Error("repository_root_mismatch")
        return path

    def registry(self, raw, path, refs, head):
        rows = fast.parse_registry(raw, self.check)
        for row in rows:
            canonical(row["path"])
        selected = [row for row in rows if os.fsencode(row["path"]) == path]
        if len(selected) != 1:
            raise Error("selected_registration_missing_or_ambiguous")
        row = selected[0]
        if row["bare"] or row["prunable"]:
            raise Error("bare_or_prunable_registration")
        if row["head"] != head or head == "0" * len(head):
            raise Error("registered_head_mismatch")
        branch = row["branch_ref"]
        if branch and (branch not in refs or refs[branch]["head"] != head):
            raise Error("registered_branch_mismatch")
        if self.pinned["HEAD"] != (
            b"ref: " + os.fsencode(branch) + b"\n" if branch else head.encode() + b"\n"
        ):
            raise Error("registered_head_kind_mismatch")
        row["removal_approval_sufficient"] = False
        self.report["registration"] = row
        # Lexical comparisons only; never open an unrelated registration.
        self.other_paths = {os.fsencode(r["path"]) for r in rows if r is not row}
        return row

    def index(self):
        raw = self.git(INDEX, "index")
        index = {}
        if raw and not raw.endswith(b"\0"):
            raise Error("malformed_index")
        for token in raw.split(b"\0")[:-1]:
            self.check()
            header, sep, path = token.partition(b"\t")
            fields = header.split(b" ")
            if (
                not sep
                or len(fields) != 3
                or fields[0] not in {b"100644", b"100755", b"120000"}
                or not fast.SHA.fullmatch(fields[1])
                or fields[2] != b"0"
                or path in index
                or path.startswith(b"/")
                or any(p in {b"", b".", b"..", b".git"} for p in path.split(b"/"))
            ):
                raise Error("unsupported_or_malformed_index")
            index[path] = (fields[0], fields[1])
        flags = self.git(FLAGS, "index_flags")
        flagged = []
        for token in flags.split(b"\0")[:-1]:
            if len(token) < 3 or token[:2] != b"H " or token[2:] not in index:
                raise Error("masked_or_unsupported_index")
            flagged.append(token[2:])
        if len(flagged) != len(index) or len(set(flagged)) != len(index):
            raise Error("inconsistent_index_flags")
        staged_raw = self.git(STAGED, "head_tree")
        if staged_raw and not staged_raw.endswith(b"\0"):
            raise Error("malformed_head_tree")
        tree = {}
        for token in staged_raw.split(b"\0")[:-1]:
            header, sep, path = token.partition(b"\t")
            fields = header.split(b" ")
            if (
                not sep
                or len(fields) != 3
                or fields[1] != b"blob"
                or fields[0] not in {b"100644", b"100755", b"120000"}
                or not fast.SHA.fullmatch(fields[2])
                or not path
                or path in tree
                or path.startswith(b"/")
                or any(p in {b"", b".", b"..", b".git"} for p in path.split(b"/"))
            ):
                raise Error("unsupported_or_malformed_head_tree")
            tree[path] = (fields[0], fields[2])
        staged = {}
        for path in tree.keys() | index.keys():
            self.check()
            if path not in tree:
                staged[path] = b"A"
            elif path not in index:
                staged[path] = b"D"
            elif tree[path] != index[path]:
                staged[path] = (
                    b"T"
                    if (tree[path][0] == b"120000") != (index[path][0] == b"120000")
                    else b"M"
                )
        return index, staged

    def scan(self, directory, relative, index, object_format, depth=0):
        if depth > self.limits["max_depth"]:
            raise Error("filesystem_depth_limit")
        before = signature(os.fstat(directory))
        empty = True
        with os.scandir(directory) as stream:
            for entry in stream:
                self.count()
                empty = False
                name = os.fsencode(entry.name)
                path = relative + (b"/" if relative else b"") + name
                if not relative and name == b".git":
                    continue
                info = entry.stat(follow_symlinks=False)
                display = encoded(path)
                if info.st_dev != os.fstat(self.root).st_dev:
                    self.storage["mount_boundaries"].append(display)
                    self.storage["skipped"].append(display)
                    continue
                if stat.S_ISDIR(info.st_mode):
                    if (
                        os.fsencode(self.request["worktree"]) + b"/" + path
                        in self.other_paths
                    ):
                        self.storage["skipped"].append(display)
                        continue
                    try:
                        child = safe_open(directory, name, os.O_RDONLY | os.O_DIRECTORY)
                    except OSError as exc:
                        if exc.errno == errno.EXDEV:
                            self.storage["mount_boundaries"].append(display)
                            self.storage["skipped"].append(display)
                            continue
                        raise
                    try:
                        if signature(os.fstat(child)) != signature(info):
                            raise Error("directory_replaced")
                        try:
                            os.stat(b".git", dir_fd=child, follow_symlinks=False)
                        except FileNotFoundError:
                            bare = True
                            for marker in (b"HEAD", b"objects", b"refs"):
                                try:
                                    marker_info = os.stat(
                                        marker, dir_fd=child, follow_symlinks=False
                                    )
                                except FileNotFoundError:
                                    bare = False
                                    break
                            if bare:
                                self.storage["nested_repositories"].append(display)
                                self.storage["skipped"].append(display)
                            else:
                                self.scan(child, path, index, object_format, depth + 1)
                        else:
                            self.storage["nested_repositories"].append(display)
                            self.storage["skipped"].append(display)
                    finally:
                        os.close(child)
                elif stat.S_ISLNK(info.st_mode):
                    if name in {b".gitignore", b".gitattributes"}:
                        raise Error("symlinked_ignore_or_attributes")
                    target = os.readlink(name, dir_fd=directory)
                    if signature(
                        os.stat(name, dir_fd=directory, follow_symlinks=False)
                    ) != signature(info):
                        raise Error("symlink_changed")
                    self.storage["symlinks"].append(
                        dict(path=display, target=encoded(target))
                    )
                    digest = hashlib.new(
                        object_format,
                        b"blob " + str(len(target)).encode() + b"\0" + target,
                    ).hexdigest()
                    self.files[path] = (b"120000", digest.encode())
                elif stat.S_ISREG(info.st_mode):
                    try:
                        probe = safe_open(directory, name, os.O_PATH)
                    except OSError as exc:
                        if exc.errno == errno.EXDEV:
                            self.storage["mount_boundaries"].append(display)
                            self.storage["skipped"].append(display)
                            continue
                        raise
                    try:
                        if signature(os.fstat(probe)) != signature(info):
                            raise Error("file_replaced")
                    finally:
                        os.close(probe)
                    self.storage["logical_regular_bytes"] += info.st_size
                    inode = (info.st_dev, info.st_ino)
                    if inode not in self.seen_inodes:
                        self.storage["unique_inode_logical_bytes"] += info.st_size
                        self.seen_inodes.add(inode)
                    if info.st_nlink > 1:
                        self.storage["hardlink_indicators"].append(
                            dict(path=display, links=info.st_nlink)
                        )
                    digest = None
                    if path in index or name in {b".gitignore", b".gitattributes"}:
                        content = self.read(directory, name)
                        if signature(
                            os.stat(name, dir_fd=directory, follow_symlinks=False)
                        ) != signature(info):
                            raise Error("file_replaced")
                        if name == b".gitattributes" and content:
                            raise Error("attributes_require_later_review")
                        if name == b".gitignore":
                            self.ignore_files[relative] = content
                        if path in index:
                            digest = (
                                hashlib.new(
                                    object_format,
                                    b"blob "
                                    + str(len(content)).encode()
                                    + b"\0"
                                    + content,
                                )
                                .hexdigest()
                                .encode()
                            )
                    mode = b"100755" if info.st_mode & 0o111 else b"100644"
                    self.files[path] = (mode, digest)
                else:
                    self.storage["skipped"].append(display)
        if empty and relative:
            self.empty_directories.add(relative)
        if before != signature(os.fstat(directory)):
            raise Error("directory_changed_during_scan")

    @staticmethod
    def ignore_rules(raw):
        """Deliberately limited Git-ignore subset. Unsupported syntax blocks."""
        rules = []
        for line in raw.split(b"\n"):
            line = line.rstrip(b"\r").rstrip(b" ")
            if not line or line.startswith(b"#"):
                continue
            if b"//" in line or any(
                item in line for item in (b"!", b"\\", b"[", b"]", b"**")
            ):
                raise Error("unsupported_ignore_pattern")
            anchored, directory = line.startswith(b"/"), line.endswith(b"/")
            pattern = line.strip(b"/")
            if not pattern or b"//" in pattern:
                raise Error("unsupported_ignore_pattern")
            rules.append((pattern, anchored, directory))
        return rules

    def ignored(self, path, rules):
        for base, patterns in rules:
            if base and not path.startswith(base + b"/"):
                continue
            local = path[len(base) + 1 :] if base else path
            parts = local.split(b"/")
            for pattern, anchored, directory in patterns:
                if b"/" not in pattern and not anchored:
                    candidates = parts[:-1] if directory else parts
                    if any(fnmatch.fnmatchcase(p, pattern) for p in candidates):
                        return True
                else:
                    for count in range(1, len(parts) + (0 if directory else 1)):
                        candidate = parts[:count]
                        segments = pattern.split(b"/")
                        if len(candidate) == len(segments) and all(
                            fnmatch.fnmatchcase(p, pat)
                            for p, pat in zip(candidate, segments)
                        ):
                            return True
        return False

    def status(self, index, staged):
        rules = [(b"", self.ignore_rules(self.pinned["exclude"]))]
        rules.extend(
            (base, self.ignore_rules(raw)) for base, raw in self.ignore_files.items()
        )
        tokens = []
        raw_paths = []
        for path in sorted(set(index) | set(staged) | set(self.files)):
            self.check()
            mode, oid = index.get(path, (None, None))
            actual = self.files.get(path)
            x, y = staged.get(path, b" "), b" "
            if mode:
                if actual is None:
                    y = b"D"
                elif (mode == b"120000") != (actual[0] == b"120000"):
                    y = b"T"
                elif actual[1] != oid or (self.filemode and mode != actual[0]):
                    y = b"M"
            elif actual is not None:
                if path in staged:
                    y = b"?"  # Removed from index and recreated: two porcelain records.
                else:
                    x = y = b"!" if self.ignored(path, rules) else b"?"
            if x != b" " or y != b" ":
                if y == b"?" and path in staged:
                    tokens.extend((x + b"  " + path + b"\0", b"?? " + path + b"\0"))
                    raw_paths.extend([encoded(path), encoded(path)])
                else:
                    tokens.append(x + y + b" " + path + b"\0")
                    raw_paths.append(encoded(path))
        for path in sorted(self.empty_directories):
            if self.ignored(path + b"/__empty_directory_indicator__", rules):
                tokens.append(b"!! " + path + b"/\0")
                raw_paths.append(encoded(path + b"/"))
        try:
            status = manager.parse_status(b"".join(tokens))
        except (manager.ObservationError, UnicodeError):
            raise Error("invalid_constructed_status") from None
        # manager's display_path intentionally redacts names. Keep an authoritative
        # lossless path alongside every original record, including private names.
        status["raw_records"] = [
            dict(code=token[:2].decode("ascii"), path=path)
            for token, path in zip(tokens, raw_paths)
        ]
        status["staged_change_count"] = len(staged)
        status["unstaged_change_count"] = sum(
            token[1:2] not in {b" ", b"?", b"!"} for token in tokens
        )
        status["method"] = "raw_blob_index_comparison_no_filters_limited_ignore_syntax"
        status["ignored_children_enumerated"] = True
        self.report["git_status"] = status

    def recheck_identity(self):
        self.audit_metadata(self.common)
        if self.gitdir_path != self.common_path:
            self.audit_metadata(self.gitdir)
        for path, fd in (
            (self.request["worktree"], self.root),
            (self.gitdir_path, self.gitdir),
            (self.common_path, self.common),
            (self.anchor["path"], self.anchor["root"]),
            (self.anchor["gitdir_path"], self.anchor["gitdir"]),
            (self.anchor["common_path"], self.anchor["common"]),
        ):
            fresh = open_absolute(path)
            try:
                if signature(os.fstat(fresh)) != signature(os.fstat(fd)):
                    raise Error("root_identity_changed")
            finally:
                os.close(fresh)
        if (
            self.pointer is not None
            and self.read(self.root, b".git", 8192) != self.pointer
        ):
            raise Error("git_pointer_changed")
        if self.optional_read(self.gitdir, b"commondir") != self.common_pointer:
            raise Error("common_pointer_changed")
        anchor = self.anchor
        if (
            anchor["pointer"] is not None
            and self.read(anchor["root"], b".git", 8192) != anchor["pointer"]
        ):
            raise Error("registry_repository_pointer_changed")
        if (
            self.optional_read(anchor["gitdir"], b"commondir")
            != anchor["common_pointer"]
        ):
            raise Error("registry_repository_common_pointer_changed")
        if (
            anchor["pointer"] is not None
            and self.read(anchor["gitdir"], b"gitdir", 8192)
            != anchor["path"] + b"/.git\n"
        ):
            raise Error("registry_repository_reverse_pointer_changed")
        if (
            self.pointer is not None
            and self.read(self.gitdir, b"gitdir", 8192)
            != os.fsencode(self.request["worktree"]) + b"/.git\n"
        ):
            raise Error("selected_reverse_pointer_changed")
        for label, fd, path in (
            ("config", self.common, b"config"),
            ("index", self.gitdir, b"index"),
            ("HEAD", self.gitdir, b"HEAD"),
            ("exclude", self.common, b"info/exclude"),
        ):
            if self.optional_read(fd, path) != self.pinned[label]:
                raise Error("metadata_changed")

    def run(self):
        dimension = "identity"
        tick = time.monotonic()
        try:
            path = self.identity()
            registry = self.git(fast.REGISTRY, "registry_before")
            refs_raw = self.git(fast.REFS, "refs_before")
            refs = fast.parse_refs(refs_raw, self.check)
            for label, raw in (
                ("registry_before", registry),
                ("refs_before", refs_raw),
            ):
                self.report["snapshots"][label] = dict(
                    sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
                )
            head = self.git(HEAD, "head_before").rstrip(b"\n")
            if not fast.SHA.fullmatch(head):
                raise Error("invalid_head")
            head = head.decode("ascii")
            row = self.registry(registry, path, refs, head)
            self.report["dimensions"][dimension] = "WARN" if row["locked"] else "PASS"
            dimension = "integration"
            baseline = self.request["baseline"]
            if baseline not in refs:
                raise Error("baseline_ref_missing")
            base = refs[baseline]["head"]
            counts = self.git(
                ("rev-list", "--left-right", "--count", head + "..." + base, "--"),
                "ancestry",
            )
            if not re.fullmatch(rb"[0-9]+\t[0-9]+\n", counts):
                raise Error("invalid_ancestry_counts")
            ahead, behind = map(int, counts.split())
            self.report["integration"] = dict(
                local_head=head,
                baseline_ref=baseline,
                baseline_head=base,
                ahead=ahead,
                behind=behind,
                head_is_ancestor=ahead == 0,
                baseline_is_ancestor=behind == 0,
                local_refs_only=True,
                remote_freshness="NOT_VERIFIED",
                detached=row["detached"],
            )
            self.report["dimensions"][dimension] = "WARN" if ahead else "PASS"
            self.report["required_observations"]["integration"] = "COMPLETED"
            dimension = "git_status"
            object_format = self.git(FORMAT, "object_format").strip().decode("ascii")
            if object_format not in {"sha1", "sha256"}:
                raise Error("unsupported_object_format")
            index, staged = self.index()
            self.filemode = not any(
                field.lower()
                in {
                    b"core.filemode\nfalse",
                    b"core.filemode\nno",
                    b"core.filemode\noff",
                    b"core.filemode\n0",
                }
                for field in self.git(CONFIG, "status_configuration").split(b"\0")
            )
            dimension = "storage"
            self.seen_inodes = set()
            self.empty_directories = set()
            self.scan(self.root, b"", index, object_format)
            if self.storage["skipped"]:
                raise Error("filesystem_content_skipped")
            self.storage["complete"] = True
            self.report["dimensions"][dimension] = (
                "WARN"
                if (self.storage["symlinks"] or self.storage["hardlink_indicators"])
                else "PASS"
            )
            self.report["required_observations"]["storage"] = "COMPLETED"
            dimension = "git_status"
            self.status(index, staged)
            self.report["dimensions"][dimension] = (
                "WARN"
                if any(
                    self.report["git_status"][key]
                    for key in (
                        "tracked_change_count",
                        "untracked_count",
                        "ignored_indicator_count",
                    )
                )
                else "PASS"
            )
            self.report["required_observations"]["git_status"] = "COMPLETED"
            dimension = "identity"
            after_registry = self.git(fast.REGISTRY, "registry_after")
            after_refs = self.git(fast.REFS, "refs_after")
            after_head = self.git(HEAD, "head_after")
            for label, raw in (
                ("registry_after", after_registry),
                ("refs_after", after_refs),
            ):
                self.report["snapshots"][label] = dict(
                    sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
                )
            self.registry(
                after_registry,
                path,
                fast.parse_refs(after_refs, self.check),
                after_head.rstrip(b"\n").decode("ascii"),
            )
            if (
                registry != after_registry
                or refs_raw != after_refs
                or after_head != head.encode() + b"\n"
            ):
                raise Error("registry_refs_or_head_changed")
            self.recheck_identity()
            self.report["consistency"] = dict(
                registry_unchanged=True,
                refs_unchanged=True,
                head_unchanged=True,
                metadata_unchanged=True,
                atomic_snapshot=False,
            )
            self.report["registration"]["observation_complete"] = True
            self.report["required_observations"]["identity"] = "COMPLETED"
            self.report["required_observations"]["consistency"] = "COMPLETED"
            self.report["preservation"]["evidence_references"] = self.request[
                "evidence"
            ]
            self.report["dimensions"]["preservation"] = "WARN"
            self.check()
            self.report["observation_complete"] = True
            # Git's metadata opens cannot be forced through openat2 by this
            # wrapper. Strict no-follow/no-mount guarantees need OS isolation.
            # Keep the executable fail-closed even when narrow observations pass.
            fail(self.report, ISOLATION_BLOCKER, "safety")
            if self.report["mode"] == DIAGNOSTIC:
                self.report["diagnostic_status"] = "COMPLETED_WITH_LIMITATIONS"
        except Error as exc:
            fail(self.report, str(exc), dimension)
        except (OSError, ValueError, UnicodeError, OverflowError):
            fail(self.report, "filesystem_or_metadata_error", dimension)
        finally:
            for fd in self.open_fds:
                os.close(fd)
        self.report["wall_seconds"] = time.monotonic() - tick
        self.report["filesystem_read_bytes"] = self.read_bytes
        self.report["git_stdout_bytes"] = self.git_bytes
        return self.report


def load_worker_report(raw):
    """Reject ambiguous/non-JSON numbers as well as truncated worker output."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Error("invalid_worker_report")
            result[key] = value
        return result

    def constant(_value):
        raise Error("invalid_worker_report")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise Error("invalid_worker_report")
        return result

    return json.loads(
        raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=number
    )


def validate_worker_report(report, request):
    """Validate before adoption: missing evidence cannot become completion.

    This is a protocol/consistency check, not authentication of a hostile worker.
    The worker, interpreter and Git executable remain trusted local programs.
    """

    def require(condition):
        if not condition:
            raise Error("invalid_worker_report")

    template = base_report(request["mode"])
    require(isinstance(report, dict))
    compact = report.get("errors") in (
        ["report_output_limit"],
        ["worker_internal_error"],
    )
    for key, value in template.items():
        if key == "git_subprocess_count":
            require(
                (compact and report.get(key) is None)
                or (type(report.get(key)) is int and report[key] >= 0)
            )
        else:
            require(key in report and type(report[key]) is type(value))
    for key in (
        "schema_version",
        "mode",
        "complete",
        "safety_assurance",
        "safe_to_remove",
        "lifecycle_hold",
        "removal_approval_sufficient",
        "lifecycle_decision",
        "actual_reclaimable_storage",
        "atomic_snapshot",
        "environment_assumption",
    ):
        require(report[key] == template[key])
    require(report["worker_subprocess_count"] == 0)
    for key in ("errors", "uncertainties"):
        require(all(type(item) is str for item in report[key]))
    require(set(UNVERIFIED) <= set(report["uncertainties"]))
    require(
        report["preservation"]
        == {
            **template["preservation"],
            "evidence_references": [] if compact else request["evidence"],
        }
    )
    require(report["preservation"]["references_verified"] is False)
    dimensions = report["dimensions"]
    require(set(dimensions) == set(template["dimensions"]))
    require(
        all(
            type(value) is str and value in {"PASS", "WARN", "BLOCKED", "NOT_CHECKED"}
            for value in dimensions.values()
        )
    )
    require(dimensions["safety"] == "BLOCKED")
    observations = report["required_observations"]
    require(set(observations) == set(REQUIRED_OBSERVATIONS))
    require(
        all(
            type(value) is str and value in {"NOT_CHECKED", "COMPLETED"}
            for value in observations.values()
        )
    )
    observed = report["observation_complete"]
    expected = "COMPLETED_WITH_LIMITATIONS" if observed else "INCOMPLETE"
    require(
        report["diagnostic_status"]
        == (expected if request["mode"] == DIAGNOSTIC else "BLOCKED")
    )
    if compact:
        require(
            not observed and report["operations"] == [] and report["snapshots"] == {}
        )
        require(observations == template["required_observations"])
        require(dimensions == template["dimensions"])
        return
    require(report.get("selected_path") == encoded(request["worktree"]))
    require(report.get("limits") == request["limits"])
    require(
        all(
            isinstance(op, dict) and type(op.get("operation")) is str
            for op in report["operations"]
        )
    )
    require(report["git_subprocess_count"] == len(report["operations"]))
    if not observed:
        require(bool(report["errors"]))
        return
    require(all(value == "COMPLETED" for value in observations.values()))
    require(
        all(
            dimensions[key] in {"PASS", "WARN"}
            for key in REQUIRED_OBSERVATIONS
            if key != "consistency"
        )
    )
    require(dimensions["preservation"] == "WARN")
    require(report["errors"] == [ISOLATION_BLOCKER])
    require(
        report.get("consistency")
        == dict(
            registry_unchanged=True,
            refs_unchanged=True,
            head_unchanged=True,
            metadata_unchanged=True,
            atomic_snapshot=False,
        )
    )
    require(all(type(value) is bool for value in report["consistency"].values()))
    for key, fields in {
        "repository_identity": (
            "selected",
            "registry_repository",
            "git_directory",
            "common_directory",
        ),
        "registration": (
            "path",
            "head",
            "branch_ref",
            "observation_complete",
            "removal_approval_sufficient",
        ),
        "integration": (
            "local_head",
            "baseline_ref",
            "baseline_head",
            "ahead",
            "behind",
            "remote_freshness",
        ),
        "git_status": (
            "raw_records",
            "tracked_change_count",
            "untracked_count",
            "ignored_indicator_count",
            "method",
        ),
        "storage": (
            "complete",
            "logical_regular_bytes",
            "unique_inode_logical_bytes",
            "skipped",
            "actual_reclaimable_storage",
        ),
    }.items():
        require(isinstance(report.get(key), dict) and set(fields) <= set(report[key]))
    require(report["registration"]["observation_complete"] is True)
    require(report["registration"]["removal_approval_sufficient"] is False)
    require(report["registration"]["path"] == request["worktree"])
    require(report["repository_identity"]["selected"] == encoded(request["worktree"]))
    require(
        report["repository_identity"]["registry_repository"]
        == encoded(request["repository"])
    )
    require(report["integration"]["baseline_ref"] == request["baseline"])
    require(report["integration"]["remote_freshness"] == "NOT_VERIFIED")
    for key in ("local_head", "baseline_head"):
        value = report["integration"][key]
        require(type(value) is str and fast.SHA.fullmatch(value.encode("ascii")))
    require(report["registration"]["head"] == report["integration"]["local_head"])
    for section, keys in (
        ("integration", ("ahead", "behind")),
        (
            "git_status",
            ("tracked_change_count", "untracked_count", "ignored_indicator_count"),
        ),
        ("storage", ("logical_regular_bytes", "unique_inode_logical_bytes")),
    ):
        require(
            all(
                type(report[section][key]) is int and report[section][key] >= 0
                for key in keys
            )
        )
    require(type(report["git_status"]["raw_records"]) is list)
    require(
        report["git_status"]["method"]
        == "raw_blob_index_comparison_no_filters_limited_ignore_syntax"
    )
    require(
        report["storage"]["complete"] is True and report["storage"]["skipped"] == []
    )
    require(report["storage"]["actual_reclaimable_storage"] == "NOT_VERIFIED")
    for label in ("registry", "refs"):
        before, after = (
            report["snapshots"].get(label + suffix) for suffix in ("_before", "_after")
        )
        require(isinstance(before, dict) and before == after)
        require(type(before.get("bytes")) is int and before["bytes"] >= 0)
        require(
            type(before.get("sha256")) is str
            and re.fullmatch("[0-9a-f]{64}", before["sha256"])
        )
    require(
        [op["operation"] for op in report["operations"]]
        == [
            "configuration",
            "pinned_root",
            "registry_before",
            "refs_before",
            "head_before",
            "ancestry",
            "object_format",
            "index",
            "index_flags",
            "head_tree",
            "status_configuration",
            "registry_after",
            "refs_after",
            "head_after",
        ]
    )
    require(
        all(
            "error" not in op
            and type(op.get("stdout_bytes")) is int
            and op["stdout_bytes"] >= 0
            for op in report["operations"]
        )
    )


def preflight(
    worktree,
    *,
    repository=None,
    baseline="refs/heads/master",
    evidence=(),
    mode=STRICT,
    **limits,
):
    """Only the bounded child may observe source filesystem or invoke Git."""
    selected_mode = mode if mode in MODES else STRICT
    report = base_report(selected_mode)
    started = time.monotonic()
    worker_started = False
    report_cap = 4096
    try:
        if mode not in MODES:
            raise Error("invalid_mode")
        settings = dict(DEFAULTS)
        if set(limits) - set(settings):
            raise Error("unknown_limit")
        settings.update(limits)
        for key, value in settings.items():
            if key.endswith("seconds"):
                if (
                    type(value) not in {int, float}
                    or not math.isfinite(value)
                    or value <= 0
                ):
                    raise Error("invalid_limits")
            elif type(value) is not int or value <= 0:
                raise Error("invalid_limits")
        if settings["max_report_bytes"] < 4096:
            raise Error("report_limit_below_minimum")
        report_cap = settings["max_report_bytes"]
        canonical(worktree)
        if repository is None:
            raise Error("registry_repository_required")
        canonical(repository)
        if not isinstance(baseline, str) or not fast.valid_ref(os.fsencode(baseline)):
            raise Error("invalid_baseline_ref")
        if (
            not isinstance(evidence, (list, tuple))
            or len(evidence) > 32
            or any(
                not isinstance(item, str) or not item or len(item) > 1024
                for item in evidence
            )
        ):
            raise Error("invalid_evidence_references")
        request = dict(
            worktree=os.fsdecode(worktree),
            repository=os.fsdecode(repository),
            baseline=baseline,
            evidence=list(evidence),
            mode=mode,
            limits=settings,
        )
        data = json_bytes(request)
        if len(data) > 16384:
            raise Error("request_size_limit")
        report["worker_subprocess_count"] = 1
        worker_started = True
        if mode == DIAGNOSTIC:
            report["diagnostic_status"] = "INCOMPLETE"
        raw = bounded_process(
            [
                sys.executable,
                "-E",
                "-s",
                "-S",
                "-B",
                os.path.abspath(__file__),
                "--internal-worker",
            ],
            timeout=min(settings["worker_seconds"], settings["deadline_seconds"]),
            max_bytes=settings["max_report_bytes"],
            data=data,
            group=True,
            env=fast.git_environment(),
        )
        candidate = load_worker_report(raw)
        validate_worker_report(candidate, request)
        report = candidate
        report["worker_subprocess_count"] = 1
    except Error as exc:
        code = {
            "subprocess_timeout": "worker_timeout",
            "subprocess_output_limit": "worker_output_limit",
        }.get(str(exc), str(exc))
        if code == "invalid_worker_report":
            report = base_report(selected_mode)
        fail(report, code)
    except (OSError, ValueError, TypeError, RecursionError):
        report = fail(base_report(selected_mode), "invalid_request_or_worker_report")
    report.update(
        safe_to_remove=False,
        lifecycle_hold=HOLD,
        removal_approval_sufficient=False,
        lifecycle_decision=HOLD,
        actual_reclaimable_storage="NOT_VERIFIED",
        worker_subprocess_count=int(worker_started),
    )
    report["wall_seconds"] = time.monotonic() - started
    if len(json_bytes(report)) + 1 > report_cap:
        report = compact_failure(selected_mode, "report_output_limit")
        report["worker_subprocess_count"] = int(worker_started)
    return report


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Error("invalid_cli_arguments")


def main(argv=None):
    parser = Parser(
        description=__doc__,
        epilog=(
            "Exit codes: 0 only for trusted_local_diagnostic COMPLETED_WITH_LIMITATIONS; "
            "1 for diagnostic INCOMPLETE/BLOCKED and every strict result. "
            "Exit 0 confirms observation completion only: safety remains BLOCKED and lifecycle HOLD. "
            "--help exits 0 without performing observations."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default=STRICT,
        help="Default: strict. Diagnostic mode retains every limit and check; never removal approval.",
    )
    parser.add_argument("--worktree", required=True)
    parser.add_argument(
        "--repository",
        required=True,
        help="Explicit repository anchoring the registry; metadata only",
    )
    parser.add_argument("--baseline", default="refs/heads/master")
    parser.add_argument("--evidence-reference", action="append", default=[])
    for key, default in DEFAULTS.items():
        parser.add_argument(
            "--" + key.replace("_", "-"), type=type(default), default=default
        )
    try:
        args = vars(parser.parse_args(argv))
        worktree, repository, baseline, evidence = (
            args.pop("worktree"),
            args.pop("repository"),
            args.pop("baseline"),
            args.pop("evidence_reference"),
        )
        report = preflight(
            worktree,
            repository=repository,
            baseline=baseline,
            evidence=evidence,
            **args,
        )
    except Error as exc:
        report = fail(base_report(), str(exc))
    print(json_bytes(report).decode("ascii"))
    return (
        0
        if (
            report["mode"] == DIAGNOSTIC
            and report["diagnostic_status"] == "COMPLETED_WITH_LIMITATIONS"
        )
        else 1
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--internal-worker"]:
        worker_mode = STRICT
        try:
            request = json.loads(sys.stdin.buffer.read(16385))
            worker_mode = request.get("mode", STRICT)
            if worker_mode not in MODES:
                raise Error("invalid_mode")
            result = Observer(request).run()
            data = json_bytes(result)
            if len(data) + 256 > request["limits"]["max_report_bytes"]:
                result = compact_failure(worker_mode, "report_output_limit")
            sys.stdout.buffer.write(json_bytes(result))
        except Exception:
            sys.stdout.buffer.write(
                json_bytes(
                    compact_failure(
                        worker_mode if worker_mode in MODES else STRICT,
                        "worker_internal_error",
                    )
                )
            )
    else:
        sys.exit(main())
