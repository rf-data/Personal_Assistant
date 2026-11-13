"""Bounded, read-only registry/ref observations. Never removal evidence.

No worktree contents, status, disk scans, external artifacts or live remotes.
JSON goes only to stdout; all paths use lossless filesystem decoding and base64.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import selectors
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime

HOLD = "WORKTREE_LIFECYCLE_HOLD"
SHA = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
REGISTRY = ("worktree", "list", "--porcelain", "-z")
REFS = (
    "for-each-ref",
    "--sort=refname",
    "--format=%(refname)%00%(objectname)%00%(symref)%00",
    "refs/heads/",
    "refs/remotes/",
)
IDENTITY = ("rev-parse", "--show-toplevel")
ALLOWED = (IDENTITY, REGISTRY, REFS)


class ObservationError(Exception):
    """Only fixed diagnostic codes; never echo subprocess stderr or filenames."""


def git_environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_OPTIONAL_LOCKS="0",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_ALLOW_PROTOCOL="",
        LC_ALL="C",
    )
    return env


def run_git(root, args, *, timeout, max_bytes):
    """Linux pipe reader: bound combined output and wall time, no temp files.

    Git metadata commands do not launch hooks/filters/helpers. Kill/reap the
    direct child on failure, with at most 0.2 seconds for cleanup after deadline.
    """
    if args not in ALLOWED:
        raise ObservationError("command_not_allowed")
    command = [
        "git",
        "--no-optional-locks",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "maintenance.auto=false",
        "-c",
        "gc.auto=0",
        "-c",
        "protocol.allow=never",
        "-C",
        root,
        *args,
    ]
    end = time.monotonic() + timeout
    process = None
    try:
        process = subprocess.Popen(
            command,
            env=git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = {"stdout": bytearray(), "stderr": bytearray()}
        size = 0
        with selectors.DefaultSelector() as selector:
            for label, stream in (
                ("stdout", process.stdout),
                ("stderr", process.stderr),
            ):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            while selector.get_map():
                remaining = end - time.monotonic()
                if remaining <= 0:
                    raise ObservationError("subprocess_timeout")
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, min(65536, max_bytes - size + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(chunk)
                    if size > max_bytes:
                        raise ObservationError("subprocess_output_limit")
                    output[key.data].extend(chunk)
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise ObservationError("subprocess_timeout")
        code = process.wait(timeout=remaining)
        if code:
            raise ObservationError("git_nonzero_exit")
        if output["stderr"]:
            raise ObservationError("git_stderr_incomplete")
        return bytes(output["stdout"])
    except subprocess.TimeoutExpired:
        raise ObservationError("subprocess_timeout") from None
    except OSError:
        raise ObservationError("subprocess_os_error") from None
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    pass  # Bounded cleanup; no blocking final wait.
            process.stdout.close()
            process.stderr.close()


def valid_ref(name):
    """Git check-ref-format's ordinary (non-pattern) rules, on bytes."""
    return (
        name.startswith((b"refs/heads/", b"refs/remotes/"))
        and not any(c <= 32 or c == 127 or c in b"~^:?*[\\" for c in name)
        and not any(s in name for s in (b"..", b"@{", b"//"))
        and not name.endswith(b".")
        and all(
            p and not p.startswith(b".") and not p.endswith(b".lock")
            for p in name.split(b"/")
        )
    )


def parse_registry(raw, check=lambda: None):
    if not raw or not raw.endswith(b"\0\0"):
        raise ObservationError("malformed_registry")
    rows, paths = [], set()
    for block in raw[:-2].split(b"\0\0"):
        check()
        fields = {}
        for item in block.split(b"\0"):
            key, sep, value = item.partition(b" ")
            if key in fields or key not in {
                b"worktree",
                b"HEAD",
                b"branch",
                b"detached",
                b"bare",
                b"locked",
                b"prunable",
            }:
                raise ObservationError("malformed_registry_field")
            if key in {b"worktree", b"HEAD", b"branch"} and (not sep or not value):
                raise ObservationError("malformed_registry_field")
            if key in {b"detached", b"bare"} and sep:
                raise ObservationError("malformed_registry_field")
            fields[key] = value
        path = fields.get(b"worktree", b"")
        if not path.startswith(b"/") or path in paths:
            raise ObservationError("invalid_or_duplicate_registry_path")
        paths.add(path)
        bare = b"bare" in fields
        if bare:
            if any(k in fields for k in (b"HEAD", b"branch", b"detached")):
                raise ObservationError("malformed_bare_registration")
        elif (
            not SHA.fullmatch(fields.get(b"HEAD", b""))
            or (b"branch" in fields) == (b"detached" in fields)
            or b"branch" in fields
            and (
                not valid_ref(fields[b"branch"])
                or not fields[b"branch"].startswith(b"refs/heads/")
            )
        ):
            raise ObservationError("malformed_registry_head_or_branch")
        rows.append(
            dict(
                path=os.fsdecode(path),
                path_bytes_base64=base64.b64encode(path).decode("ascii"),
                branch_ref=os.fsdecode(fields[b"branch"])
                if b"branch" in fields
                else None,
                head=fields[b"HEAD"].decode("ascii") if b"HEAD" in fields else None,
                detached=b"detached" in fields,
                bare=bare,
                locked=b"locked" in fields,
                prunable=b"prunable" in fields,
                # Reasons are arbitrary free text; presence is enough for this tier.
                safe_to_remove=False,
                lifecycle_hold=HOLD,
                observation_errors=[],
                observation_complete=False,
                contents_verified=False,
                reproducible="not_verified",
            )
        )
    return rows


def parse_refs(raw, check=lambda: None):
    refs = {}
    if raw and not raw.endswith(b"\0\n"):
        raise ObservationError("malformed_refs")
    for line in raw.split(b"\n")[:-1]:
        check()
        parts = line.split(b"\0")
        if len(parts) != 4 or parts[-1] != b"":
            raise ObservationError("malformed_refs")
        name, head, target, _ = parts
        if (
            not valid_ref(name)
            or not SHA.fullmatch(head)
            or head == b"0" * len(head)
            or target
            and not valid_ref(target)
        ):
            raise ObservationError("malformed_ref_name_or_head")
        name = os.fsdecode(name)
        if name in refs:
            raise ObservationError("duplicate_ref")
        refs[name] = dict(head=head.decode("ascii"), symref=os.fsdecode(target) or None)
    for value in refs.values():
        check()
        target = value["symref"]
        if target and (target not in refs or refs[target]["head"] != value["head"]):
            raise ObservationError("missing_or_inconsistent_symbolic_ref")
    return refs


def inventory(
    root,
    *,
    subprocess_seconds=5.0,
    deadline_seconds=20.0,
    max_output_bytes=8 * 1024 * 1024,
):
    """Five sequential Git reads, independent of registered worktree count.

    complete means only the explicitly limited registry/ref observation succeeded.
    Partial rows are retained with holds; no success exit on uncertainty.
    """
    if (
        not all(
            math.isfinite(v) and v > 0 for v in (subprocess_seconds, deadline_seconds)
        )
        or type(max_output_bytes) is not int
        or max_output_bytes <= 0
    ):
        raise ValueError("limits must be finite and positive")
    root = os.path.abspath(
        os.fsdecode(root)
    )  # Lexical only; never visit registrations.
    started = time.monotonic()
    end = started + deadline_seconds
    report = dict(
        schema_version=1,
        generated_at=datetime.now(UTC).isoformat(),
        repository_path=root,
        scope="registry_and_cached_refs_only",
        complete=False,
        safe_to_remove=False,
        lifecycle_hold=HOLD,
        removal_approval_sufficient=False,
        consistency=dict(registry_unchanged=None, refs_unchanged=None),
        errors=[],
        operations=[],
        subprocess_count=0,
        worktrees=[],
        refs={},
        snapshots={},
        limits=dict(
            subprocess_seconds=subprocess_seconds,
            deadline_seconds=deadline_seconds,
            max_output_bytes=max_output_bytes,
        ),
        limitations=[
            "Endpoint comparison is not atomic and cannot detect change-and-revert races.",
            "Registered paths, contents, status, identity and process use are not verified.",
            "Cached remote refs do not establish live remote availability or integration.",
            "No backup, archive, restoration, disk size or removal assessment is performed.",
            "Git metadata reads are trusted to describe its registry and visible ref namespace.",
        ],
    )

    def check():
        if time.monotonic() >= end:
            raise ObservationError("overall_deadline")

    def observe(label, action, command=False):
        tick = time.monotonic()
        entry = dict(operation=label, seconds=0.0, error=None)
        report["operations"].append(entry)
        try:
            check()
            if command:
                report["subprocess_count"] += 1
                raw = run_git(
                    root,
                    action,
                    timeout=min(subprocess_seconds, end - time.monotonic()),
                    max_bytes=max_output_bytes,
                )
                entry["stdout_bytes"] = len(raw)
                result = raw
            else:
                result = action()
            check()
            return result
        except ObservationError as exc:
            entry["error"] = str(exc)
            raise
        finally:
            entry["seconds"] = time.monotonic() - tick

    def snapshot(label, command, parser):
        raw = observe(label, command, True)
        report["snapshots"][label] = dict(
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
        )
        return raw, observe(label + "_parse", lambda: parser(raw, check))

    def consistency(rows, refs, label):
        for row in rows:
            check()
            branch, head = row["branch_ref"], row["head"]
            errors = []
            if head and head == "0" * len(head):
                errors.append("unborn_or_missing_head")
            if branch and branch not in refs:
                errors.append("registered_branch_missing")
            elif branch and refs[branch]["head"] != head:
                errors.append("registered_branch_head_mismatch")
            if errors:
                row["observation_errors"].extend(errors)
                report["errors"].append(
                    dict(operation=label, code="registry_ref_inconsistent")
                )

    try:
        top = observe("repository_identity", IDENTITY, True)
        if top != os.fsencode(root) + b"\n":
            raise ObservationError("repository_root_mismatch")
        before_registry, rows = snapshot("registry_before", REGISTRY, parse_registry)
        report["worktrees"] = rows
        before_refs, refs = snapshot("refs_before", REFS, parse_refs)
        report["refs"] = refs
        observe(
            "consistency_before", lambda: consistency(rows, refs, "consistency_before")
        )
        after_registry, after_rows = snapshot(
            "registry_after", REGISTRY, parse_registry
        )
        after_refs, after_ref_values = snapshot("refs_after", REFS, parse_refs)
        observe(
            "consistency_after",
            lambda: consistency(after_rows, after_ref_values, "consistency_after"),
        )
        report["consistency"] = dict(
            registry_unchanged=before_registry == after_registry,
            refs_unchanged=before_refs == after_refs,
        )
        if before_registry != after_registry or before_refs != after_refs:
            raise ObservationError("registry_or_refs_changed")
        check()
    except ObservationError as exc:
        report["errors"].append(
            dict(operation=report["operations"][-1]["operation"], code=str(exc))
        )
    report["complete"] = not report["errors"]
    for row in report["worktrees"]:
        row["observation_complete"] = (
            report["complete"] and not row["observation_errors"]
        )
    counts = Counter(r["head"] for r in report["worktrees"] if r["head"])
    report["duplicate_heads"] = {h: n for h, n in counts.items() if n > 1}
    report["summary"] = dict(
        registered=len(report["worktrees"]),
        lifecycle_holds=len(report["worktrees"]),
        safe_to_remove=0,
    )
    report["wall_seconds"] = time.monotonic() - started
    if report["wall_seconds"] >= deadline_seconds and report["complete"]:
        report["complete"] = False
        report["errors"].append(dict(operation="finalize", code="overall_deadline"))
        for row in report["worktrees"]:
            row["observation_complete"] = False
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        required=True,
        help="Explicit worktree root authorized for metadata observation",
    )
    parser.add_argument("--subprocess-seconds", type=float, default=5.0)
    parser.add_argument("--deadline-seconds", type=float, default=20.0)
    parser.add_argument("--max-output-bytes", type=int, default=8 * 1024 * 1024)
    args = parser.parse_args(argv)
    try:
        report = inventory(
            args.repository,
            subprocess_seconds=args.subprocess_seconds,
            deadline_seconds=args.deadline_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    except (ValueError, OSError):
        parser.error("invalid repository argument or limits")
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
