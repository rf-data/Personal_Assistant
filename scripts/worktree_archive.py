"""Conservative worktree audit and explicitly approved archival. Default: read only.

Run with ``uv run python -m scripts.worktree_archive --help``. No push, branch
removal, force, prune, stash, reset or clean operation is implemented.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

SCHEMA = 1
PROTECTED_NAMES = frozenset(
    {
        "Personal_Assistant",
        "Personal_Assistant-c26h",
        "Personal_Assistant-c24r",
        "Personal_Assistant-c26g",
        "Personal_Assistant-cs50-real01",
        "Personal_Assistant-maint05",
    }
)
PROTECTED_BRANCHES = frozenset({"master", "main"})
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
EXCLUSIVE = "ALL_WRITERS_STOPPED"


class Hold(RuntimeError):
    """Evidence is insufficient; no destructive fallback is permitted."""


def now():
    return dt.datetime.now(dt.UTC).isoformat()


def git(root, *args):
    # Inherited Git selectors could silently redirect an audit to another repo.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
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
                "core.hooksPath=/dev/null",
                "-C",
                str(root),
                *map(str, args),
            ],
            env=env,
            capture_output=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Hold(f"Git unavailable/timeout: {args[0]}") from exc
    if result.returncode:
        # Do not echo URLs/credentials or private filenames from stderr.
        raise Hold(f"Git failed: {args[0]} (exit {result.returncode})")
    return result.stdout


def string(root, *args):
    return os.fsdecode(git(root, *args)).strip()


def canonical(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise Hold("Explicit absolute path without '..' required")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise Hold("Symlink path/ancestor refused")
    if path != path.resolve():
        raise Hold("Noncanonical path refused")
    return path


def identity(path):
    s = path.stat()
    return [s.st_dev, s.st_ino]


def nul(data):
    if data and not data.endswith(b"\0"):
        raise Hold("Incomplete NUL-delimited Git output")
    return [os.fsdecode(x) for x in data.split(b"\0")[:-1]]


def worktrees(repo):
    rows, row = [], {}
    for line in nul(git(repo, "worktree", "list", "--porcelain", "-z")):
        if not line:
            if row:
                rows.append(row)
                row = {}
            continue
        key, _, value = line.partition(" ")
        row[key] = value
    if row:
        rows.append(row)
    if not rows or any("worktree" not in x or "HEAD" not in x for x in rows):
        raise Hold("Incomplete worktree registration")
    return rows


def status(repo):
    data = git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
        "--ignore-submodules=none",
    )
    parts = nul(data)
    entries, i = [], 0
    allowed = set(" MADRCUT?!")
    while i < len(parts):
        item = parts[i]
        if len(item) < 4 or item[2] != " " or not set(item[:2]) <= allowed:
            raise Hold("Malformed/incomplete Git status")
        code, name = item[:2], item[3:]
        entry = {"status": code, "path": name}
        if "R" in code or "C" in code:
            i += 1
            if i >= len(parts) or not parts[i]:
                raise Hold("Incomplete rename/copy status")
            entry["original_path"] = parts[i]
        entries.append(entry)
        i += 1
    # Git can intentionally conceal changes via index flags; refuse these and
    # submodules rather than relying on a superficially clean status.
    flags = nul(git(repo, "ls-files", "-v", "-z"))
    hazards = [s[2:] for s in flags if s[:1] != "H"]
    stages = nul(git(repo, "ls-files", "--stage", "-z"))
    hazards.extend(s.partition("\t")[2] for s in stages if s.startswith("160000 "))
    # Include empty untracked directories, which status itself can omit. Do not
    # descend into ignored stores, venvs or private data, or read file contents.
    extras = sorted(
        set(
            nul(
                git(
                    repo,
                    "ls-files",
                    "--others",
                    "--directory",
                    "-z",
                    "--exclude-standard",
                )
            )
        )
    )
    ignored = sorted(
        set(
            nul(
                git(
                    repo,
                    "ls-files",
                    "--others",
                    "--directory",
                    "--ignored",
                    "-z",
                    "--exclude-standard",
                )
            )
        )
    )
    return {
        "entries": entries,
        "extra_paths": extras,
        "ignored_paths": ignored,
        "index_hazards": sorted(set(hazards)),
        "complete": True,
    }


def branch_ref(repo, name, protected_branches=()):
    if (
        not name
        or name.startswith("-")
        or name in PROTECTED_BRANCHES | set(protected_branches)
    ):
        raise Hold("Explicit nonprotected backup branch required")
    git(repo, "check-ref-format", "refs/heads/" + name)
    return "refs/heads/" + name


def remote_url(repo, remote):
    if not remote or remote.startswith("-"):
        raise Hold("Explicit named remote required")
    urls = string(repo, "remote", "get-url", "--all", remote).splitlines()
    if len(urls) != 1 or not urls[0] or urls[0].startswith("-"):
        raise Hold("Ambiguous remote URL")
    return urls[0]


def remote_head(repo, url, ref):
    try:
        lines = string(repo, "ls-remote", "--refs", "--", url, ref).splitlines()
    except Hold as exc:
        return {"state": "unverified", "sha": None, "error": str(exc), "at": now()}
    if not lines:
        return {"state": "missing", "sha": None, "at": now()}
    fields = [line.split("\t") for line in lines]
    if (
        len(fields) != 1
        or len(fields[0]) != 2
        or fields[0][1] != ref
        or not SHA.fullmatch(fields[0][0])
    ):
        return {
            "state": "unverified",
            "sha": None,
            "error": "Ambiguous ls-remote output",
            "at": now(),
        }
    return {"state": "verified", "sha": fields[0][0], "at": now()}


def remote_catalog(repo, url):
    """One authoritative inventory-only snapshot; never used for execution."""
    try:
        lines = string(repo, "ls-remote", "--refs", "--heads", "--", url).splitlines()
        refs = {}
        for line in lines:
            sha, ref = line.split("\t")
            if (
                not SHA.fullmatch(sha)
                or not ref.startswith("refs/heads/")
                or ref in refs
            ):
                raise ValueError("Invalid remote snapshot")
            refs[ref] = sha
        return {"state": "verified", "refs": refs, "at": now()}
    except (Hold, ValueError) as exc:
        return {"state": "unverified", "sha": None, "error": str(exc), "at": now()}


def common_dir(repo):
    return canonical(
        string(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )


def activity(path):
    """Positive Linux cwd evidence only. Absence never proves inactivity."""
    pids = []
    try:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                cwd = (entry / "cwd").resolve(strict=True)
                if cwd == path or path in cwd.parents:
                    pids.append(int(entry.name))
            except (OSError, RuntimeError):
                pass
    except OSError:
        pass
    return {"cwd_pids": sorted(pids), "absence_proves_idle": False}


def optional_ref(repo, ref):
    try:
        value = string(repo, "rev-parse", "--verify", ref)
        return value if SHA.fullmatch(value) else None
    except Hold:
        return None


def check(
    repo,
    path,
    remote=None,
    backup_branch=None,
    protect=(),
    remote_cache=None,
    protected_branches=(),
):
    repo, path = canonical(repo), canonical(path)
    rows = worktrees(repo)
    row = next((r for r in rows if r["worktree"] == str(path)), None)
    if row is None:
        raise Hold("Exact worktree not registered (already archived or wrong path)")
    if common_dir(path) != common_dir(repo):
        raise Hold("Worktree belongs to another common Git directory")
    canonical(path / ".git")
    head = string(path, "rev-parse", "--verify", "HEAD")
    if not SHA.fullmatch(head) or head != row["HEAD"]:
        raise Hold("HEAD changed during registration scan")
    branch = row.get("branch")
    actual = string(path, "symbolic-ref", "-q", "HEAD") if branch else None
    if branch != actual:
        raise Hold("Branch changed during scan")
    local_sha = optional_ref(repo, branch) if branch else None
    if branch and local_sha != head:
        raise Hold("Branch HEAD mismatch")
    st = status(path)
    active = activity(path)
    classes, blockers = [], []
    reasons = []
    if path == Path(rows[0]["worktree"]):
        reasons.append("primary checkout")
    if (
        path == repo
        or path.name in PROTECTED_NAMES
        or str(path) in {str(canonical(p)) for p in protect}
    ):
        reasons.append("explicit/current-task protection")
    if "locked" in row or "prunable" in row:
        reasons.append("locked/prunable registration requires investigation")
    if active["cwd_pids"]:
        reasons.append("process cwd in worktree")
    if reasons:
        classes.append("PROTECTED_ACTIVE")
        blockers.extend(reasons)
    if any(x["status"] not in ("??", "!!") for x in st["entries"]):
        classes.append("DIRTY")
        blockers.append("tracked changes")
    if (
        st["extra_paths"]
        or st["ignored_paths"]
        or any(x["status"] in ("??", "!!") for x in st["entries"])
    ):
        classes.append("UNTRACKED_OR_IGNORED_RISK")
        blockers.append(
            "unsecured untracked/ignored paths (including empty directories)"
        )
    if st["index_hazards"]:
        blockers.append("index flags/submodules require separate evidence")
    if not branch:
        classes.append("DETACHED_HEAD")
        blockers.append("detached HEAD unsupported for removal")
    upstream = (
        string(path, "for-each-ref", "--format=%(upstream)", branch) if branch else ""
    )
    tracking_sha = optional_ref(path, upstream) if upstream else None
    configured_remote = (
        string(path, "for-each-ref", "--format=%(upstream:remotename)", branch)
        if branch
        else None
    )
    configured_merge = (
        string(path, "for-each-ref", "--format=%(upstream:remoteref)", branch)
        if branch
        else None
    )
    tracking_counts = None
    if tracking_sha:
        tracking_counts = string(
            path, "rev-list", "--left-right", "--count", f"HEAD...{upstream}"
        ).split()
    chosen = backup_branch or (branch.removeprefix("refs/heads/") if branch else None)
    evidence = {
        "state": "unverified",
        "sha": None,
        "error": "No explicit remote/branch",
    }
    url = None
    ref = "refs/heads/" + chosen if chosen else None
    if remote and chosen:
        try:
            branch_ref(repo, chosen, protected_branches)
            url = remote_url(path, remote)
            key = (url, ref)
            if remote_cache is not None:
                if (url, "*") not in remote_cache:
                    remote_cache[(url, "*")] = remote_catalog(path, url)
                catalog = remote_cache[(url, "*")]
                if catalog["state"] == "unverified":
                    evidence = catalog
                else:
                    evidence = {
                        "state": "verified" if ref in catalog["refs"] else "missing",
                        "sha": catalog["refs"].get(ref),
                        "at": catalog["at"],
                    }
                remote_cache[key] = evidence
            else:
                evidence = remote_head(path, url, ref)
        except Hold as exc:
            evidence = {"state": "unverified", "sha": None, "error": str(exc)}
    if evidence["state"] == "unverified":
        classes.append("REMOTE_UNVERIFIED")
        blockers.append("authoritative remote SHA unverified")
    elif evidence["state"] == "missing":
        classes.append("REMOTE_MISSING")
        blockers.append("backup branch absent on authoritative remote")
    elif evidence["sha"] != head:
        classes.append("REMOTE_MISMATCH")
        blockers.append("backup branch HEAD differs")
    exact = evidence["state"] == "verified" and evidence["sha"] == head
    reachable = True if exact else None
    remote_counts = None
    if evidence["state"] == "verified" and optional_ref(path, evidence["sha"]):
        remote_counts = string(
            path, "rev-list", "--left-right", "--count", f"HEAD...{evidence['sha']}"
        ).split()
        if not exact:
            # rev-list counts: all local-only commits absent means ancestor.
            reachable = remote_counts[0] == "0"
    if not blockers:
        classes.append("CANDIDATE_FOR_ARCHIVE")
    classes.append("PR_OR_MERGE_UNVERIFIED")
    return {
        "schema_version": SCHEMA,
        "observed_at": now(),
        "status": "HOLD" if blockers else "PLAN_ONLY",
        "path": str(path),
        "path_identity": identity(path),
        "common_dir": str(common_dir(repo)),
        "head": head,
        "subject": string(path, "log", "-1", "--format=%s"),
        "branch": branch,
        "local_branch_sha": local_sha,
        "registration": row,
        "git_status": st,
        "upstream": upstream or None,
        "configured_remote": configured_remote or None,
        "configured_merge_ref": configured_merge or None,
        "tracking_sha": tracking_sha,
        "tracking_ahead_behind": tracking_counts,
        "remote_ahead_behind": remote_counts,
        "remote": remote,
        "remote_url": url,
        "backup_ref": ref,
        "remote_evidence": evidence,
        "remote_branch_sha": evidence["sha"],
        "remote_branch_presence": "present"
        if evidence["state"] == "verified"
        else "absent"
        if evidence["state"] == "missing"
        else "unknown",
        "named_tracking_ref": f"refs/remotes/{remote}/{chosen}"
        if remote and chosen
        else None,
        "named_tracking_sha": optional_ref(path, f"refs/remotes/{remote}/{chosen}")
        if remote and chosen
        else None,
        "head_present_on_remote": True if reachable else "unknown",
        "head_reachable_via_backup_branch": reachable
        if reachable is not None
        else "unknown",
        "exact_remote_head": exact,
        "recovery": "unverified",
        "activity": active,
        "pr_merge": "unverified; review open PRs and task ownership separately",
        "classifications": classes,
        "blockers": blockers,
        "operator_requirements": [
            "review task/PR ownership",
            "stop ALL writers",
            "explicit approval",
            "fresh recovery rehearsal",
        ],
    }


def fingerprint(plan):
    keys = (
        "path",
        "path_identity",
        "common_dir",
        "head",
        "branch",
        "local_branch_sha",
        "remote",
        "remote_url",
        "backup_ref",
        "git_status",
    )
    values = {key: plan[key] for key in keys}
    values["remote_sha"] = plan["remote_evidence"]["sha"]
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def plan_archive(repo, path, remote, backup_branch, protect=(), protected_branches=()):
    result = check(
        repo,
        path,
        remote,
        backup_branch,
        protect,
        protected_branches=protected_branches,
    )
    result.update(kind="worktree-archive-plan", fingerprint=fingerprint(result))
    result["approval"] = f"ARCHIVE {result['fingerprint']}"
    result["restore_instruction"] = (
        "Use restore --record <receipt.json> --target <free-absolute-path>; inspect plan before --execute"
    )
    return result


def save_new(path, data):
    path = canonical(path)
    # Exclusive creation; never overwrite an old approval, receipt or user data.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextlib.contextmanager
def exclusive(repo):
    # Cooperative Linux flock in the shared Git directory, not an unlinkable
    # temporary lock. All operators of this CLI share the same lock inode.
    path = common_dir(repo) / "maint05-archive.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Hold("Another archival/restore operation holds the lock") from exc
        if identity(path) != [os.fstat(fd).st_dev, os.fstat(fd).st_ino]:
            raise Hold("Exclusive lock identity changed")
        yield
    finally:
        os.close(fd)


def rehearsal(repo, url, ref, sha):
    # All writes here are to a new synthetic recovery repo, never the audited repo.
    with tempfile.TemporaryDirectory(prefix="maint05-recovery-") as scratch:
        root = Path(scratch)
        recovered = root / "checkout"
        bare = root / "recovery.git"
        bare.mkdir()
        git(bare, "init", "--bare", "--template=")
        git(bare, "fetch", "--no-tags", "--", url, ref)
        if string(bare, "rev-parse", "FETCH_HEAD") != sha:
            raise Hold("Remote changed during recovery rehearsal")
        git(bare, "fsck", "--full", "--no-reflogs", sha)
        git(bare, "worktree", "add", "--detach", recovered, sha)
        if (
            string(recovered, "rev-parse", "HEAD") != sha
            or status(recovered)["entries"]
        ):
            raise Hold("Recovery checkout did not reproduce a clean expected HEAD")
    return {
        "verified_at": now(),
        "sha": sha,
        "method": "isolated fetch/fsck/full checkout",
        "verified": True,
    }


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise Hold("Archive plan must be a JSON object")
    if (
        plan.get("schema_version") != SCHEMA
        or plan.get("kind") != "worktree-archive-plan"
    ):
        raise Hold("Unsupported archive plan")
    if (
        plan.get("fingerprint") != fingerprint(plan)
        or plan.get("approval") != "ARCHIVE " + plan["fingerprint"]
    ):
        raise Hold("Plan fingerprint/approval mismatch")
    if plan.get("blockers") or "CANDIDATE_FOR_ARCHIVE" not in plan.get(
        "classifications", []
    ):
        raise Hold("Archive plan is on HOLD")


def archive(
    repo,
    plan,
    receipt,
    approval=None,
    exclusive_writers=None,
    protect=(),
    protected_branches=(),
):
    validate_plan(plan)
    if approval != plan["approval"] or exclusive_writers != EXCLUSIVE:
        raise Hold(
            "Exact plan approval AND ALL_WRITERS_STOPPED acknowledgement required"
        )
    repo, path, receipt = canonical(repo), canonical(plan["path"]), canonical(receipt)
    if (
        receipt == path
        or path in receipt.parents
        or common_dir(repo) == receipt
        or common_dir(repo) in receipt.parents
    ):
        raise Hold("Receipt must survive worktree removal and be outside Git metadata")
    if receipt.exists() or Path(str(receipt) + ".completed.json").exists():
        raise Hold("Receipt already exists; never replay or overwrite")
    with exclusive(repo):
        current = plan_archive(
            repo,
            path,
            plan["remote"],
            plan["backup_ref"].removeprefix("refs/heads/"),
            protect,
            protected_branches,
        )
        validate_plan(current)
        if current["fingerprint"] != plan["fingerprint"]:
            raise Hold("Plan is stale; local/remote/path identity changed")
        # Git worktree lock prevents ordinary administrative move/remove by other
        # operators during rehearsal. It does NOT stop editors or filesystem writes.
        reason = "MAINT05 " + plan["fingerprint"]
        git(repo, "worktree", "lock", "--reason", reason, path)
        try:
            proof = rehearsal(
                repo, plan["remote_url"], plan["backup_ref"], plan["head"]
            )
            pending = dict(
                plan,
                kind="worktree-archive-record",
                state="PREPARED",
                status="PREPARED",
                recovery=proof,
                exclusive_writers_ack=EXCLUSIVE,
                prepared_at=now(),
            )
            # Durable recovery data exists BEFORE removal, including on a crash.
            save_new(receipt, pending)
        finally:
            rows = worktrees(repo)
            row = next((r for r in rows if r["worktree"] == str(path)), None)
            if row is None or row.get("locked") != reason:
                raise Hold("Worktree lock ownership lost; investigate, do not remove")
            git(repo, "worktree", "unlock", path)
        # Immediately repeat all local identity/status and authoritative remote
        # checks AFTER unlock. Git refuses dirty/untracked removal without force;
        # ignored-file races still require the operator's exclusive writer contract.
        final = plan_archive(
            repo,
            path,
            plan["remote"],
            plan["backup_ref"].removeprefix("refs/heads/"),
            protect,
            protected_branches,
        )
        validate_plan(final)
        if final["fingerprint"] != plan["fingerprint"]:
            raise Hold("State changed before removal; PREPARED receipt retained")
        git(repo, "worktree", "remove", path)
        if path.exists() or any(r["worktree"] == str(path) for r in worktrees(repo)):
            raise Hold("Removal outcome unverified; PREPARED receipt retained")
        complete = dict(
            pending,
            state="ARCHIVED",
            status="ARCHIVED",
            archived_at=now(),
            classifications=["ARCHIVE_VERIFIED"],
        )
        # Separate exclusive completion receipt: the PREPARED record is immutable.
        save_new(Path(str(receipt) + ".completed.json"), complete)
        return complete


def restore_plan(repo, record, target):
    repo, target = canonical(repo), canonical(target)
    if not isinstance(record, dict):
        raise Hold("Archive record must be a JSON object")
    if (
        record.get("kind") != "worktree-archive-record"
        or record.get("schema_version") != SCHEMA
    ):
        raise Hold("Verified archive record required")
    if record.get("state") != "ARCHIVED" or not record.get("recovery", {}).get(
        "verified"
    ):
        raise Hold(
            "Archive completion/recovery not verified; reconcile PREPARED manually"
        )
    if (
        not SHA.fullmatch(record.get("head", ""))
        or record["recovery"].get("sha") != record["head"]
    ):
        raise Hold("Invalid recovery SHA")
    original = record.get("branch", "")
    if not original.startswith("refs/heads/"):
        raise Hold("Explicit original branch required")
    branch_ref(repo, original.removeprefix("refs/heads/"))
    backup = record.get("backup_ref", "")
    if not backup.startswith("refs/heads/"):
        raise Hold("Explicit backup ref required")
    branch_ref(repo, backup.removeprefix("refs/heads/"))
    if str(common_dir(repo)) != record.get("common_dir"):
        raise Hold("Restore must use the recorded repository")
    if target.exists() or target.is_symlink():
        raise Hold("Restore target already exists")
    if not target.parent.is_dir():
        raise Hold("Restore parent must exist")
    rows = worktrees(repo)
    if any(r["worktree"] == str(target) or r.get("branch") == original for r in rows):
        raise Hold("Target/branch already registered in a worktree")
    local = optional_ref(repo, original)
    if local is not None and local != record["head"]:
        raise Hold("Existing local branch differs; never reset it")
    if remote_url(repo, record["remote"]) != record["remote_url"]:
        raise Hold("Remote URL changed")
    evidence = remote_head(repo, record["remote_url"], backup)
    if evidence["state"] != "verified" or evidence["sha"] != record["head"]:
        raise Hold("Restore remote SHA unavailable or changed")
    result = {
        "kind": "worktree-restore-plan",
        "status": "PLAN_ONLY",
        "target": str(target),
        "original_path": record["path"],
        "branch": original,
        "head": record["head"],
        "create_branch": local is None,
        "remote_evidence": evidence,
    }
    # Approval must remain stable across fresh timestamped remote checks.
    result["approval"] = (
        "RESTORE "
        + hashlib.sha256(
            json.dumps(
                {k: result[k] for k in ("target", "branch", "head", "create_branch")},
                sort_keys=True,
            ).encode()
        ).hexdigest()
    )
    return result


def restore(repo, record, target, approval=None, exclusive_writers=None):
    if exclusive_writers != EXCLUSIVE:
        raise Hold("ALL_WRITERS_STOPPED acknowledgement required")
    with exclusive(repo):
        plan = restore_plan(repo, record, target)
        if approval != plan["approval"]:
            raise Hold("Exact restore plan approval required")
        git(
            repo, "fetch", "--no-tags", "--", record["remote_url"], record["backup_ref"]
        )
        if string(repo, "rev-parse", "FETCH_HEAD") != record["head"]:
            raise Hold("Fetched restore SHA changed")
        final = restore_plan(repo, record, target)
        if final["approval"] != plan["approval"]:
            raise Hold("Restore identity changed")
        branch = plan["branch"].removeprefix("refs/heads/")
        if plan["create_branch"]:
            git(repo, "worktree", "add", "-b", branch, target, record["head"])
        else:
            git(repo, "worktree", "add", target, branch)
        if (
            string(target, "rev-parse", "HEAD") != record["head"]
            or status(target)["entries"]
        ):
            raise Hold("Restore postcondition failed; retained for investigation")
        return dict(final, status="RESTORED")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protect", type=Path, action="append", default=[])
    parser.add_argument("--protected-backup-branch", action="append", default=[])
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--remote", default="origin")
    for name in ("check", "archive"):
        p = sub.add_parser(name)
        p.add_argument("--worktree", type=Path, required=True)
        p.add_argument("--remote", required=True)
        p.add_argument("--backup-branch", required=True)
        if name == "archive":
            p.add_argument("--plan", type=Path)
            p.add_argument("--save-plan", type=Path)
            p.add_argument("--receipt", type=Path)
            p.add_argument("--execute", action="store_true")
            p.add_argument("--approve")
            p.add_argument("--exclusive-writers")
    rest = sub.add_parser("restore")
    rest.add_argument("--record", type=Path, required=True)
    rest.add_argument("--target", type=Path, required=True)
    rest.add_argument("--execute", action="store_true")
    rest.add_argument("--approve")
    rest.add_argument("--exclusive-writers")
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            cache, records = {}, []
            for row in worktrees(canonical(args.repo)):
                try:
                    records.append(
                        check(
                            args.repo,
                            Path(row["worktree"]),
                            args.remote,
                            protect=args.protect,
                            remote_cache=cache,
                            protected_branches=args.protected_backup_branch,
                        )
                    )
                except (Hold, OSError) as exc:
                    records.append(
                        {
                            "path": row["worktree"],
                            "registration": row,
                            "status": "HOLD",
                            "classifications": [
                                "REMOTE_UNVERIFIED",
                                "PR_OR_MERGE_UNVERIFIED",
                            ],
                            "blockers": [str(exc)],
                            "git_status": {"complete": False},
                        }
                    )
            result = {
                "schema_version": SCHEMA,
                "at": now(),
                "status": "HOLD"
                if any(r["status"] == "HOLD" for r in records)
                else "PLAN_ONLY",
                "worktrees": records,
            }
        elif args.command in ("check", "archive"):
            result = plan_archive(
                args.repo,
                args.worktree,
                args.remote,
                args.backup_branch,
                args.protect,
                args.protected_backup_branch,
            )
            if args.command == "archive" and args.execute:
                if not args.plan or not args.receipt or args.save_plan:
                    raise Hold(
                        "Execution requires existing --plan, new --receipt; no --save-plan"
                    )
                saved = json.loads(args.plan.read_text())
                if any(saved[k] != result[k] for k in ("path", "remote", "backup_ref")):
                    raise Hold("CLI selection differs from saved plan")
                result = archive(
                    args.repo,
                    saved,
                    args.receipt,
                    args.approve,
                    args.exclusive_writers,
                    args.protect,
                    args.protected_backup_branch,
                )
            elif args.command == "archive" and args.save_plan:
                save_new(args.save_plan, result)
        else:
            record = json.loads(args.record.read_text())
            result = (
                restore(
                    args.repo, record, args.target, args.approve, args.exclusive_writers
                )
                if args.execute
                else restore_plan(args.repo, record, args.target)
            )
    except (Hold, OSError, ValueError, KeyError, TypeError) as exc:
        result = {"schema_version": SCHEMA, "status": "HOLD", "error": str(exc)}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 3 if result.get("status") == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())
