"""Read-only worktree inventory. No creation, archive, removal or ref mutations.

Python standard library only. Reports are emitted exclusively to stdout.
See docs/maintenance/worktree_lifecycle.md for evidence and privacy boundaries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

VERSION = 1
CLASSIFICATIONS = ("ACTIVE", "ARCHIVE", "REMOVABLE_CANDIDATE", "REVIEW")
EXTERNAL_PATHS = (
    "/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance",
    "/mnt/data",
)
HUMAN_GATES = (
    "exact_path_operator_approval",
    "ownership_and_process_use",
    "document_integration_and_historical_evidence",
    "artifact_backup_and_independent_restore",
    "dependencies_and_environment",
    "external_artifact_mapping",
)
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


class ObservationError(Exception):
    """A deliberately content-free diagnostic; never include Git stderr."""


def utc_now():
    return datetime.now(UTC).isoformat()


def git_path(raw):
    # Git appends one newline; path whitespace itself must survive unchanged.
    return Path(os.fsdecode(raw[:-1] if raw.endswith(b"\n") else raw))


def origin_repository(root):
    raw = git(root, "config", "--get", "remote.origin.url", allowed=(0, 1))
    url = os.fsdecode(raw).rstrip("\n")
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?",
        url,
    )
    return match[1] if match else None


def git(root, *args, timeout=30, allowed=(0,)):
    # Do not inherit a caller's alternate index, worktree, namespace or Git config.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_OPTIONAL_LOCKS="0",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_ALLOW_PROTOCOL="",  # Also denies lazy fetch on older Git versions.
        LC_ALL="C",
    )
    overrides = []
    if args[0] == "status":
        # Index refresh may otherwise run arbitrary clean/process filter programs.
        configured = git(
            root,
            "config",
            "--name-only",
            "--get-regexp",
            r"^filter\..*\.(clean|process|required)$",
            allowed=(0, 1),
        )
        for raw in configured.splitlines():
            key = os.fsdecode(raw)
            if not re.fullmatch(r"filter\..+\.(clean|process|required)", key):
                raise ObservationError("unsupported_filter_configuration")
            overrides.extend(
                ["-c", key + ("=false" if key.endswith(".required") else "=")]
            )
    try:
        result = subprocess.run(
            [
                "git",
                "--no-optional-locks",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-c",
                "core.preloadIndex=false",
                "-c",
                "core.hooksPath=/dev/null",
                *overrides,
                "-C",
                str(root),
                *args,
            ],
            env=env,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObservationError(f"git_{args[0]}_{type(exc).__name__}") from None
    if result.returncode not in allowed or result.stderr:
        raise ObservationError(f"git_{args[0]}_incomplete_exit_{result.returncode}")
    return result.stdout


def parse_worktrees(raw):
    """Porcelain -z preserves whitespace, newlines and non-UTF8 path bytes."""
    records = []
    for block in raw.split(b"\0\0"):
        if not block:
            continue
        record = {}
        for line in block.split(b"\0"):
            if not line:
                continue
            key, _, value = line.partition(b" ")
            record[os.fsdecode(key)] = os.fsdecode(value)
        if "worktree" not in record:
            raise ObservationError("invalid_worktree_porcelain")
        records.append(record)
    if not records:
        raise ObservationError("empty_worktree_registry")
    return records


def private_path(name):
    """Keep aggregate counts but redact sensitive filenames in local reports too."""
    return any(
        part in {"data", "documents", "__orga", "orga", "mongo_db", "models"}
        or part.startswith(".env")
        or re.search(r"secret|credential|password|token|private|api.?key", part, re.I)
        or Path(part).suffix.lower() in {".pem", ".key", ".db", ".sqlite", ".sqlite3"}
        for part in Path(name).parts
    )


def display_path(name):
    return "[private path omitted]" if private_path(name) else name


def parse_status(raw):
    changes, untracked, ignored = [], [], []
    tokens = iter(raw.split(b"\0"))
    for token in tokens:
        if not token:
            continue
        if len(token) < 4 or token[2:3] != b" ":
            raise ObservationError("invalid_status_porcelain")
        code = token[:2].decode("ascii")
        path = display_path(os.fsdecode(token[3:]))
        if code == "??":
            untracked.append(path)
        elif code == "!!":
            ignored.append(path)
        else:
            change = dict(status=code, path=path)
            if "R" in code or "C" in code:
                source = next(tokens, None)
                if source is None or not source:
                    raise ObservationError("invalid_status_rename")
                change["source"] = display_path(os.fsdecode(source))
            changes.append(change)
    return dict(
        available=True,
        tracked_changes=changes,
        tracked_change_count=len(changes),
        untracked_files=untracked,
        untracked_count=len(untracked),
        ignored_indicators=ignored,
        ignored_indicator_count=len(ignored),
        clean_tracked=not changes,
        ignored_children_enumerated=False,
    )


def has_symlink_component(path):
    return any(p.is_symlink() for p in (path, *path.parents))


def disk_usage(root, *, max_entries=200000, seconds=15):
    """lstat only, never follow symlinks or cross devices; count each inode once.

    Apparent sizes, not allocation or reclaimable disk space. .git is excluded.
    Any skipped content makes the estimate partial and blocks candidacy.
    """
    result = dict(
        apparent_bytes=0,
        entries=0,
        symlinks=0,
        complete=True,
        errors=0,
        skipped_mounts=0,
        nested_git_markers=0,
        method="lstat_unique_inodes_no_symlinks_no_mounts_excludes_dotgit",
    )
    started = time.monotonic()
    seen = set()
    try:
        device = root.lstat().st_dev
        stack = [root]
        while stack:
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if entry.name == ".git":
                            if directory != root:
                                result["nested_git_markers"] += 1
                            continue
                        if (
                            result["entries"] >= max_entries
                            or time.monotonic() - started > seconds
                        ):
                            result["complete"] = False
                            result["limit_reached"] = True
                            return result
                        result["entries"] += 1
                        try:
                            info = entry.stat(follow_symlinks=False)
                            inode = (info.st_dev, info.st_ino)
                            if inode in seen:
                                continue
                            seen.add(inode)
                            if info.st_dev != device:
                                result["skipped_mounts"] += 1
                                result["complete"] = False
                                continue
                            if stat.S_ISLNK(info.st_mode):
                                result["symlinks"] += 1
                            elif stat.S_ISDIR(info.st_mode):
                                stack.append(Path(entry.path))
                            elif stat.S_ISREG(info.st_mode):
                                result["apparent_bytes"] += info.st_size
                            else:
                                result["complete"] = False
                                result["special_files"] = (
                                    result.get("special_files", 0) + 1
                                )
                        except OSError:
                            result["errors"] += 1
                            result["complete"] = False
            except OSError:
                result["errors"] += 1
                result["complete"] = False
    except OSError:
        result["errors"] += 1
        result["complete"] = False
    return result


def external_metadata(path):
    record = dict(path=str(path), contents_inspected=False, mapping="not_verified")
    try:
        info = path.lstat()
        record.update(
            available=True,
            is_directory=stat.S_ISDIR(info.st_mode),
            is_symlink=stat.S_ISLNK(info.st_mode),
            symlink_component=has_symlink_component(path),
            mode=oct(stat.S_IMODE(info.st_mode)),
            mtime_ns=info.st_mtime_ns,
            device=info.st_dev,
        )
    except FileNotFoundError:
        record.update(available=False, reason="not_present")
    except OSError as exc:
        record.update(available=None, reason=type(exc).__name__)
    return record


def load_hosting(path, repository, *, max_age_hours=24):
    """Only consume an explicit, sanitized, schema-validated metadata snapshot."""
    if path is None:
        return dict(
            available=False, reason="not_supplied", branches={}, pull_requests=[]
        )
    raw = path.read_bytes()
    data = json.loads(raw)
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != VERSION
        or data.get("repository") != repository
        or not isinstance(data.get("branches"), dict)
        or not isinstance(data.get("pull_requests"), list)
        or type(data.get("complete")) is not bool
    ):
        raise ValueError("invalid hosting snapshot schema or repository")
    observed = datetime.fromisoformat(data["observed_at"])
    if observed.tzinfo is None:
        raise ValueError("hosting timestamp must include timezone")
    age = (datetime.now(UTC) - observed).total_seconds()
    for name, sha in data["branches"].items():
        if (
            not isinstance(name, str)
            or not isinstance(sha, str)
            or not SHA.fullmatch(sha)
        ):
            raise ValueError("invalid hosting branch")
    for pr in data["pull_requests"]:
        if (
            not isinstance(pr, dict)
            or not isinstance(pr.get("number"), int)
            or pr.get("state") not in {"open", "closed"}
            or type(pr.get("merged")) is not bool
            or type(pr.get("draft")) is not bool
            or not isinstance(pr.get("head_sha"), str)
            or not SHA.fullmatch(pr["head_sha"])
            or not all(
                isinstance(pr.get(k), str)
                for k in ("head_ref", "head_repository", "base_ref", "base_repository")
            )
        ):
            raise ValueError("invalid hosting PR")
    # Never propagate extra fields (e.g. bodies, users or credential-bearing URLs).
    fields = (
        "number",
        "state",
        "merged",
        "draft",
        "head_sha",
        "head_ref",
        "head_repository",
        "base_ref",
        "base_repository",
    )
    return dict(
        available=True,
        repository=repository,
        observed_at=data["observed_at"],
        complete=data["complete"],
        fresh=0 <= age <= max_age_hours * 3600,
        sha256=hashlib.sha256(raw).hexdigest(),
        branches=data["branches"],
        pull_requests=[{k: p[k] for k in fields} for p in data["pull_requests"]],
    )


def classify(record):
    """Recommendations, never a removal decision. Known activity takes priority."""
    status = record.get("status", {})
    active = []
    if record["primary"]:
        active.append("primary_checkout")
    if record["current"]:
        active.append("inventory_execution_worktree")
    if record["branch"] == "master":
        active.append("persistent_default_branch_worktree")
    if record["locked"]:
        active.append("worktree_locked")
    if status.get("tracked_change_count", 0) or status.get("untracked_count", 0):
        active.append("uncommitted_or_untracked_work")
    if any(p["state"] == "open" for p in record["pull_requests"]):
        active.append("open_pr_including_drafts")
    if record.get("ancestry", {}).get("ahead", 0):
        active.append("commits_outside_baseline")
    if active:
        return "ACTIVE", active
    risks = list(record["observation_errors"])
    if record["prunable"]:
        risks.append("prunable_registration_requires_recovery_review")
    if not record.get("hosting_verified"):
        risks.append("hosting_or_live_baseline_not_verified")
    if not record.get("ancestry", {}).get("head_is_ancestor"):
        risks.append("head_not_proven_retained_in_baseline")
    disk = record.get("disk_usage", {})
    if not disk.get("complete"):
        risks.append("disk_metadata_incomplete")
    if disk.get("symlinks") or disk.get("nested_git_markers"):
        risks.append("symlink_or_nested_repository_requires_review")
    if record.get("submodule_count"):
        risks.append("submodules_not_audited")
    if risks:
        return "REVIEW", sorted(set(risks))
    if status.get("ignored_indicator_count"):
        return "ARCHIVE", ["ignored_data_needs_preservation_review"]
    return "REMOVABLE_CANDIDATE", ["automatic_observations_pass_human_gates_pending"]


def inventory(
    root,
    *,
    hosting=None,
    repository=None,
    external_paths=EXTERNAL_PATHS,
    max_entries=200000,
    disk_seconds=15,
):
    root = root.resolve()
    common = git_path(git(root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    common = common.resolve()
    registry = git(root, "worktree", "list", "--porcelain", "-z")
    registrations = parse_worktrees(registry)
    # No arbitrary ref input: the agreed comparison is specifically origin/master.
    refs_raw = git(
        root,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)",
        "refs/heads/",
        "refs/remotes/",
    )
    refs = {}
    for line in refs_raw.splitlines():
        name, sha = line.split(b"\0")
        refs[os.fsdecode(name)] = sha.decode("ascii")
    baseline = refs.get("refs/remotes/origin/master")
    shallow = git(root, "rev-parse", "--is-shallow-repository").strip() != b"false"
    partial = bool(
        git(root, "config", "--get", "extensions.partialClone", allowed=(0, 1))
    )
    hosting = hosting or dict(
        available=False, reason="not_supplied", branches={}, pull_requests=[]
    )
    origin = origin_repository(root)
    hosting_verified = bool(
        repository
        and hosting.get("available")
        and hosting.get("repository") == repository
        and repository == origin
        and hosting.get("complete")
        and hosting.get("fresh")
        and baseline
        and hosting["branches"].get("master") == baseline
    )
    records = []
    ancestry_cache = {}
    for index, reg in enumerate(registrations):
        path = Path(reg["worktree"])
        branch = reg.get("branch")
        short_branch = branch.removeprefix("refs/heads/") if branch else None
        head = reg.get("HEAD")
        matches = []
        for pr in hosting["pull_requests"]:
            same_branch = bool(
                short_branch
                and pr["head_repository"] == repository
                and pr["head_ref"] == short_branch
            )
            same_sha = pr["head_sha"] == head
            if same_branch or same_sha:
                matches.append(
                    dict(
                        **pr,
                        match="branch_and_sha"
                        if same_branch and same_sha
                        else "branch"
                        if same_branch
                        else "sha_only",
                    )
                )
        record = dict(
            path=str(path),
            branch=short_branch,
            branch_ref=branch,
            detached="detached" in reg,
            head=head,
            primary=index == 0,
            current=path == root,
            prunable="prunable" in reg,
            prunable_reason=reg.get("prunable"),
            locked="locked" in reg,
            # Lock reasons can contain free text; presence alone is sufficient.
            observation_errors=[],
            status=dict(available=False),
            ancestry={},
            local_branch_available=bool(branch and branch in refs),
            local_branch_head=refs.get(branch),
            cached_remote_branches=[
                dict(ref=k, head=v)
                for k, v in refs.items()
                if k.startswith("refs/remotes/")
                and short_branch
                and k.split("/", 3)[-1] == short_branch
            ],
            remote_availability_source="explicit_hosting_snapshot"
            if hosting.get("available")
            else "cached_refs_only_live_unknown",
            live_remote_branch_available=(short_branch in hosting["branches"])
            if short_branch and hosting.get("available") and hosting.get("complete")
            else None,
            live_remote_branch_head=hosting["branches"].get(short_branch),
            hosting_verified=hosting_verified,
            pull_requests=matches,
            reproducible="not_verified",
            safe_to_remove=False,
            lifecycle_hold="WORKTREE_LIFECYCLE_HOLD",
            pending_gates=list(HUMAN_GATES),
        )
        errors = record["observation_errors"]
        if not baseline:
            errors.append("origin_master_unavailable")
        if shallow or partial:
            errors.append("shallow_or_partial_history")
        if branch and refs.get(branch) != head:
            errors.append("registered_branch_head_mismatch")
        if head not in ancestry_cache:
            ancestry = {}
            if baseline and head and SHA.fullmatch(head):
                try:
                    ahead, behind = git(
                        root,
                        "rev-list",
                        "--left-right",
                        "--count",
                        f"{head}...{baseline}",
                    ).split()
                    ancestry = dict(
                        baseline_ref="origin/master",
                        baseline_head=baseline,
                        ahead=int(ahead),
                        behind=int(behind),
                        head_is_ancestor=int(ahead) == 0,
                    )
                except ObservationError:
                    pass
            ancestry_cache[head] = ancestry
        record["ancestry"] = ancestry_cache[head]
        if not record["ancestry"]:
            errors.append("ancestry_unavailable")
        try:
            if has_symlink_component(path):
                raise ObservationError("worktree_symlink_component")
            if not path.is_dir():
                raise ObservationError("worktree_missing_or_inaccessible")
            # A missing .git must not make Git walk up into an unrelated repository.
            top = git_path(git(path, "rev-parse", "--show-toplevel"))
            actual_common = git_path(git(path, "rev-parse", "--git-common-dir"))
            if not actual_common.is_absolute():
                actual_common = path / actual_common
            if top != path or actual_common.resolve() != common:
                raise ObservationError("worktree_identity_mismatch")
            if git(path, "rev-parse", "HEAD").strip().decode("ascii") != head:
                raise ObservationError("worktree_head_changed")
            record["status"] = parse_status(
                git(
                    path,
                    "status",
                    "--porcelain=v1",
                    "-z",
                    "--untracked-files=all",
                    "--ignored=matching",
                    "--ignore-submodules=all",
                )
            )
            stages = git(path, "ls-files", "--stage", "-z")
            record["submodule_count"] = sum(
                t.startswith(b"160000 ") for t in stages.split(b"\0")
            )
            record["disk_usage"] = disk_usage(
                path, max_entries=max_entries, seconds=disk_seconds
            )
            if git(path, "rev-parse", "HEAD").strip().decode("ascii") != head:
                errors.append("worktree_head_changed_during_scan")
        except ObservationError as exc:
            errors.append(str(exc))
        record["classification"], record["classification_reasons"] = classify(record)
        records.append(record)
    changed = registry != git(
        root, "worktree", "list", "--porcelain", "-z"
    ) or refs_raw != git(
        root,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)",
        "refs/heads/",
        "refs/remotes/",
    )
    if changed:
        for record in records:
            record["observation_errors"].append("registry_or_refs_changed_during_scan")
            if record["classification"] != "ACTIVE":
                record["classification"] = "REVIEW"
            record["classification_reasons"].append(
                "registry_or_refs_changed_during_scan"
            )
    counts = Counter(r["classification"] for r in records)
    return dict(
        schema_version=VERSION,
        generated_at=utc_now(),
        repository_path=str(root),
        repository=origin,
        git_common_dir=str(common),
        baseline_head=baseline,
        git_version=git(root, "--version").decode().strip(),
        registry_sha256=hashlib.sha256(registry).hexdigest(),
        refs_sha256=hashlib.sha256(refs_raw).hexdigest(),
        registry_or_refs_changed=changed,
        policy="observations_only_no_removal_authorization",
        hosting={
            k: v for k, v in hosting.items() if k not in {"branches", "pull_requests"}
        },
        external_artifacts=[external_metadata(Path(p)) for p in external_paths],
        summary=dict(
            registered=len(records),
            classifications={k: counts[k] for k in CLASSIFICATIONS},
            prunable=sum(r["prunable"] for r in records),
            status_unavailable=sum(not r["status"]["available"] for r in records),
            with_tracked_changes=sum(
                bool(r["status"].get("tracked_change_count")) for r in records
            ),
            with_untracked=sum(
                bool(r["status"].get("untracked_count")) for r in records
            ),
            with_ignored=sum(
                bool(r["status"].get("ignored_indicator_count")) for r in records
            ),
            apparent_bytes_lower_bound=sum(
                r.get("disk_usage", {}).get("apparent_bytes", 0) for r in records
            ),
            disk_incomplete=sum(
                not r.get("disk_usage", {}).get("complete") for r in records
            ),
            lifecycle_holds=len(records),
            safe_to_remove=0,
        ),
        worktrees=records,
        limitations=[
            "Point-in-time observations, not an atomic filesystem snapshot or process-use audit.",
            "Ignored entries are indicators, not exhaustive child-file counts.",
            "Disk size excludes .git and does not estimate reclaimable space.",
            "No content backups, restore tests or document retention reviews performed.",
            "Cached remote refs are not proof of live availability; hosting snapshot has its own timestamp.",
        ],
    )


def csv_text(report):
    # Nested cells are JSON; scalar strings are spreadsheet-formula escaped.
    fields = list(dict.fromkeys(k for row in report["worktrees"] for k in row))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in report["worktrees"]:
        values = {}
        for key in fields:
            value = row.get(key)
            if isinstance(value, (dict, list, bool)) or value is None:
                value = json.dumps(value, ensure_ascii=True, sort_keys=True)
            elif isinstance(value, str) and value.startswith(
                ("=", "+", "-", "@", "\t", "\r", "\n")
            ):
                value = "'" + value
            if isinstance(value, str):
                value = value.encode("utf-8", "backslashreplace").decode("utf-8")
            values[key] = value
        writer.writerow(values)
    return stream.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inventory", "audit"))
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--hosting-repository", help="Snapshot binding, e.g. rf-data/Personal_Assistant"
    )
    parser.add_argument("--hosting-snapshot", type=Path)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--max-disk-entries", type=int, default=200000)
    parser.add_argument("--disk-seconds", type=float, default=15)
    args = parser.parse_args(argv)
    if args.max_disk_entries <= 0 or args.disk_seconds <= 0:
        parser.error("disk limits must be positive")
    if args.hosting_snapshot and not args.hosting_repository:
        parser.error("--hosting-snapshot requires --hosting-repository")
    try:
        root = args.repository.resolve()
        top = git_path(git(root, "rev-parse", "--show-toplevel"))
        if root != top:
            raise ValueError("--repository must name the worktree root")
        hosting = load_hosting(args.hosting_snapshot, args.hosting_repository)
        report = inventory(
            root,
            hosting=hosting,
            repository=args.hosting_repository,
            max_entries=args.max_disk_entries,
            disk_seconds=args.disk_seconds,
        )
        report["operation"] = args.operation
        if args.format == "csv":
            print(csv_text(report), end="")
        else:
            print(json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True))
        return (
            2
            if args.operation == "audit" and report["summary"]["lifecycle_holds"]
            else 0
        )
    except (ObservationError, OSError, ValueError, KeyError, TypeError) as exc:
        # No raw exception messages: filenames and third-party errors may be private.
        print(
            f"WORKTREE_LIFECYCLE_HOLD: inventory failed ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
