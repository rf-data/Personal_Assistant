"""Offline regressions: every Git subprocess is fenced to disposable repositories."""

import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import worktree_archive as wa


@pytest.fixture(autouse=True)
def synthetic_git_fence(tmp_path, monkeypatch):
    run = subprocess.run

    def fenced(args, *a, **kw):
        if Path(str(args[0])).name == "git":
            assert "-C" in args, "Every test Git command needs an explicit root"
            root = Path(args[args.index("-C") + 1]).resolve()
            rehearsal = root.is_relative_to(Path("/tmp")) and any(
                part.startswith("maint05-recovery-") for part in root.parts
            )
            assert root.is_relative_to(tmp_path) or rehearsal, (
                f"Test attempted Git outside synthetic roots: {root}"
            )
            assert not any(x in args for x in ("--force", "prune", "--hard"))
        return run(args, *a, **kw)

    monkeypatch.setattr(subprocess, "run", fenced)
    # Global/system excludes, signing, templates and hooks cannot influence fixtures.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def g(root, *args):
    return wa.string(root, *args)


@pytest.fixture
def repo(tmp_path):
    base, remote, tree = (
        tmp_path / "primary",
        tmp_path / "remote.git",
        tmp_path / "tree with spaces",
    )
    base.mkdir()
    remote.mkdir()
    g(remote, "init", "--bare", "--template=")
    g(base, "init", "-b", "master", "--template=")
    g(base, "config", "commit.gpgsign", "false")
    g(base, "config", "core.excludesFile", "/dev/null")
    g(base, "config", "user.name", "Synthetic Test")
    g(base, "config", "user.email", "synthetic@example.invalid")
    (base / "tracked.txt").write_text("initial\n")
    (base / ".gitignore").write_text("important.db\nignored/\n")
    g(base, "add", ".")
    g(base, "commit", "-m", "synthetic initial")
    g(base, "remote", "add", "origin", remote)
    g(base, "worktree", "add", "-b", "archive/pilot", tree)
    g(tree, "push", "-u", "origin", "HEAD:refs/heads/archive/pilot")
    return SimpleNamespace(base=base, remote=remote, tree=tree, root=tmp_path)


def plan(r, **kw):
    return wa.plan_archive(r.base, r.tree, "origin", "archive/pilot", **kw)


def execute(r, p=None, **kw):
    p = p or plan(r)
    return wa.archive(
        r.base, p, r.root / "receipt.json", p["approval"], wa.EXCLUSIVE, **kw
    )


def advance_remote(r):
    g(r.base, "commit", "--allow-empty", "-m", "remote moved")
    g(r.base, "push", "origin", "HEAD:refs/heads/archive/pilot")


def assert_retained(r):
    assert r.tree.is_dir()
    assert any(x["worktree"] == str(r.tree) for x in wa.worktrees(r.base))


def test_clean_exact_remote_is_candidate_only_and_inventory_read_only(repo):
    index = Path(
        g(repo.tree, "rev-parse", "--path-format=absolute", "--git-path", "index")
    )
    before_index = index.read_bytes()
    refs = g(repo.base, "show-ref")
    p = plan(repo)
    assert p["status"] == "PLAN_ONLY"
    assert "CANDIDATE_FOR_ARCHIVE" in p["classifications"]
    assert "ARCHIVE_VERIFIED" not in p["classifications"]
    assert p["exact_remote_head"]
    assert p["head_reachable_via_backup_branch"] is True
    assert p["tracking_ahead_behind"] == ["0", "0"]
    assert p["recovery"] == "unverified"
    assert before_index == index.read_bytes()
    assert refs == g(repo.base, "show-ref")
    assert_retained(repo)


@pytest.mark.parametrize(
    "change,expected",
    [
        ("dirty", "DIRTY"),
        ("staged", "DIRTY"),
        ("untracked", "UNTRACKED_OR_IGNORED_RISK"),
        ("ignored", "UNTRACKED_OR_IGNORED_RISK"),
        ("ignored_dir", "UNTRACKED_OR_IGNORED_RISK"),
        ("empty_dir", "UNTRACKED_OR_IGNORED_RISK"),
    ],
)
def test_local_data_blocks(repo, change, expected):
    if change in ("dirty", "staged"):
        (repo.tree / "tracked.txt").write_text("valuable change\n")
        if change == "staged":
            g(repo.tree, "add", "tracked.txt")
    elif change == "untracked":
        (repo.tree / "valuable notes.txt").write_text("keep")
    elif change == "ignored":
        (repo.tree / "important.db").write_text("keep")
    else:
        directory = repo.tree / ("ignored" if change == "ignored_dir" else "empty")
        directory.mkdir()
        if change == "ignored_dir":
            (directory / "data").write_text("keep")
    p = plan(repo)
    assert expected in p["classifications"]
    with pytest.raises(wa.Hold, match="HOLD"):
        execute(repo, p)
    assert_retained(repo)


@pytest.mark.parametrize("remote_state", ["missing", "mismatch", "unreachable"])
def test_remote_failures_never_verify(repo, remote_state):
    if remote_state == "missing":
        g(repo.base, "remote", "set-url", "origin", repo.root / "empty.git")
        (repo.root / "empty.git").mkdir()
        g(repo.root / "empty.git", "init", "--bare", "--template=")
    elif remote_state == "mismatch":
        advance_remote(repo)
        g(
            repo.base,
            "update-ref",
            "refs/remotes/origin/archive/pilot",
            g(repo.tree, "rev-parse", "HEAD"),
        )
    else:
        g(repo.base, "remote", "set-url", "origin", repo.root / "does not exist.git")
    p = plan(repo)
    expected = {
        "missing": "REMOTE_MISSING",
        "mismatch": "REMOTE_MISMATCH",
        "unreachable": "REMOTE_UNVERIFIED",
    }[remote_state]
    assert expected in p["classifications"]
    assert p["tracking_sha"] == p["head"]  # stale tracking is not proof
    assert not p["exact_remote_head"]
    with pytest.raises(wa.Hold):
        execute(repo, p)
    assert_retained(repo)


def test_detached_head_refused_even_when_backup_matches(repo):
    g(repo.tree, "switch", "--detach")
    assert "DETACHED_HEAD" in plan(repo)["classifications"]
    with pytest.raises(wa.Hold):
        execute(repo)


@pytest.mark.parametrize(
    "protection", ["explicit", "name", "primary", "locked", "process", "current"]
)
def test_protected_active(repo, monkeypatch, protection):
    kw = {}
    if protection == "explicit":
        kw["protect"] = [repo.tree]
    elif protection == "name":
        monkeypatch.setattr(wa, "PROTECTED_NAMES", {repo.tree.name})
    elif protection == "primary":
        repo.tree = repo.base
    elif protection == "locked":
        g(repo.base, "worktree", "lock", "--reason", "another active task", repo.tree)
    elif protection == "process":
        monkeypatch.setattr(
            wa, "activity", lambda _: {"cwd_pids": [123], "absence_proves_idle": False}
        )
    else:
        repo.base = repo.tree
    p = plan(repo, **kw)
    assert "PROTECTED_ACTIVE" in p["classifications"]
    with pytest.raises(wa.Hold):
        execute(repo, p, **kw)
    assert_retained(repo)


@pytest.mark.parametrize(
    "output", [b" M tracked.txt", b"garbage\0", b"R  new\0", b"?? \0"]
)
def test_incomplete_status_aborts(repo, monkeypatch, output):
    git = wa.git

    def broken(root, *args):
        return output if args[0] == "status" else git(root, *args)

    monkeypatch.setattr(wa, "git", broken)
    with pytest.raises(wa.Hold):
        plan(repo)
    assert_retained(repo)


def test_nul_status_handles_rename_newline_and_unicode(repo):
    g(repo.tree, "mv", "tracked.txt", "new\nname ä.txt")
    st = wa.status(repo.tree)
    rename = next(x for x in st["entries"] if x["status"].startswith("R"))
    assert rename["path"] == "new\nname ä.txt"
    assert rename["original_path"] == "tracked.txt"


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_hidden_index_flags_block(repo, flag):
    g(repo.tree, "update-index", flag, "tracked.txt")
    (repo.tree / "tracked.txt").write_text("concealed changes")
    assert plan(repo)["git_status"]["index_hazards"]
    with pytest.raises(wa.Hold):
        execute(repo)


@pytest.mark.parametrize(
    "confusion",
    ["symlink", "symlink_parent", "dotdot", "relative", "foreign", "git_symlink"],
)
def test_path_confusion_refused(repo, confusion):
    target = repo.tree
    if confusion == "symlink":
        target = repo.root / "alias"
        target.symlink_to(repo.tree, target_is_directory=True)
    elif confusion == "symlink_parent":
        alias = repo.root / "parent alias"
        alias.symlink_to(repo.root, target_is_directory=True)
        target = alias / repo.tree.name
    elif confusion == "dotdot":
        target = repo.tree / ".." / repo.tree.name
    elif confusion == "relative":
        target = Path(repo.tree.name)
    elif confusion == "foreign":
        target = repo.root / "foreign"
        target.mkdir()
        g(target, "init", "--template=")
    else:
        metadata = repo.tree / ".git"
        saved = repo.root / "original-git-file"
        metadata.rename(saved)
        metadata.symlink_to(saved)
    with pytest.raises(wa.Hold):
        wa.plan_archive(repo.base, target, "origin", "archive/pilot")
    assert repo.tree.exists()


@pytest.mark.parametrize("phase", ["before_execute", "during_rehearsal"])
def test_remote_branch_race_retains_tree(repo, monkeypatch, phase):
    p = plan(repo)
    if phase == "before_execute":
        advance_remote(repo)
    else:
        rehearsal = wa.rehearsal

        def moved(*args):
            proof = rehearsal(*args)
            advance_remote(repo)
            return proof

        monkeypatch.setattr(wa, "rehearsal", moved)
    with pytest.raises(wa.Hold):
        execute(repo, p)
    assert_retained(repo)


@pytest.mark.parametrize(
    "phase", ["before_execute", "during_rehearsal", "after_unlock"]
)
@pytest.mark.parametrize("kind", ["tracked", "untracked", "ignored"])
def test_local_race_retains_tree(repo, monkeypatch, phase, kind):
    p = plan(repo)

    def change():
        name = {
            "tracked": "tracked.txt",
            "untracked": "new.txt",
            "ignored": "important.db",
        }[kind]
        (repo.tree / name).write_text("new valuable state")

    if phase == "before_execute":
        change()
    elif phase == "during_rehearsal":
        rehearsal = wa.rehearsal

        def changed(*args):
            result = rehearsal(*args)
            change()
            return result

        monkeypatch.setattr(wa, "rehearsal", changed)
    else:
        git = wa.git

        def changed(root, *args):
            result = git(root, *args)
            if args[:2] == ("worktree", "unlock"):
                change()
            return result

        monkeypatch.setattr(wa, "git", changed)
    with pytest.raises(wa.Hold):
        execute(repo, p)
    assert_retained(repo)


@pytest.mark.parametrize(
    "approval,ack",
    [(None, None), ("yes", wa.EXCLUSIVE), (None, wa.EXCLUSIVE), ("correct", None)],
)
def test_missing_operator_authorization(repo, approval, ack):
    p = plan(repo)
    if approval == "correct":
        approval = p["approval"]
    with pytest.raises(wa.Hold, match="approval"):
        wa.archive(repo.base, p, repo.root / "receipt.json", approval, ack)
    assert not (repo.base / ".git" / "maint05-archive.lock").exists()
    assert_retained(repo)


def test_archive_restore_roundtrip_spaces_and_replay(repo):
    refs = g(repo.base, "show-ref")
    record = execute(repo)
    assert record["state"] == "ARCHIVED"
    assert record["status"] == "ARCHIVED"
    assert record["classifications"] == ["ARCHIVE_VERIFIED"]
    assert not repo.tree.exists()
    assert refs == g(repo.base, "show-ref")  # no branch deletion/rewriting
    assert json.loads((repo.root / "receipt.json").read_text())["state"] == "PREPARED"
    complete = json.loads((repo.root / "receipt.json.completed.json").read_text())
    assert complete == record
    with pytest.raises(wa.Hold):
        wa.plan_archive(repo.base, repo.tree, "origin", "archive/pilot")
    rp = wa.restore_plan(repo.base, record, repo.tree)
    assert not repo.tree.exists()  # default remains a plan
    result = wa.restore(repo.base, record, repo.tree, rp["approval"], wa.EXCLUSIVE)
    assert result["status"] == "RESTORED"
    assert g(repo.tree, "rev-parse", "HEAD") == record["head"]
    assert (repo.tree / "tracked.txt").read_text() == "initial\n"
    assert refs == g(repo.base, "show-ref")
    with pytest.raises(wa.Hold):
        wa.restore_plan(repo.base, record, repo.tree)


@pytest.mark.parametrize(
    "conflict",
    [
        "directory",
        "file",
        "symlink",
        "branch_checked_out",
        "branch_changed",
        "remote_changed",
        "remote_unavailable",
        "prepared",
        "sha",
        "remote_url",
    ],
)
def test_restore_conflicts_preserve_data(repo, conflict):
    record = execute(repo)
    if conflict == "directory":
        repo.tree.mkdir()
        (repo.tree / "valuable").write_text("keep")
    elif conflict == "file":
        repo.tree.write_text("keep")
    elif conflict == "symlink":
        repo.tree.symlink_to(repo.root / "missing")
    elif conflict == "branch_checked_out":
        g(repo.base, "worktree", "add", repo.root / "other", "archive/pilot")
    elif conflict == "branch_changed":
        g(repo.base, "commit", "--allow-empty", "-m", "new")
        g(
            repo.base,
            "update-ref",
            "refs/heads/archive/pilot",
            g(repo.base, "rev-parse", "HEAD"),
        )
    elif conflict == "remote_changed":
        advance_remote(repo)
    elif conflict in ("remote_unavailable", "remote_url"):
        if conflict == "remote_unavailable":
            repo.remote.rename(repo.root / "remote-offline.git")
        else:
            g(repo.base, "remote", "set-url", "origin", repo.root / "wrong.git")
    elif conflict == "prepared":
        record["state"] = "PREPARED"
    else:
        record["recovery"]["sha"] = "0" * 40
    with pytest.raises(wa.Hold):
        wa.restore_plan(repo.base, record, repo.tree)
    if conflict == "directory":
        assert (repo.tree / "valuable").read_text() == "keep"
    if conflict == "file":
        assert repo.tree.read_text() == "keep"


@pytest.mark.parametrize(
    "operation", ["fetch", "fsck", "remove", "unlock", "completion"]
)
def test_git_failure_keeps_recovery_evidence(repo, monkeypatch, operation):
    git = wa.git
    save = wa.save_new

    def failed(root, *args):
        if args[0] == operation or args[:2] == ("worktree", operation):
            raise wa.Hold("Synthetic Git failure")
        return git(root, *args)

    def failed_completion(path, data):
        if str(path).endswith(".completed.json"):
            raise OSError("synthetic completion write failure")
        return save(path, data)

    monkeypatch.setattr(wa, "git", failed)
    if operation == "completion":
        monkeypatch.setattr(wa, "save_new", failed_completion)
    with pytest.raises((wa.Hold, OSError)):
        execute(repo)
    if operation == "completion":
        assert not repo.tree.exists()
        assert (
            json.loads((repo.root / "receipt.json").read_text())["state"] == "PREPARED"
        )
    else:
        assert_retained(repo)


def test_cooperative_exclusion(repo):
    with wa.exclusive(repo.base):
        with pytest.raises(wa.Hold, match="Another"):
            execute(repo)
    assert_retained(repo)


@pytest.mark.parametrize(
    "branch", ["master", "main", "-option", "bad..name", "refs/heads/master"]
)
def test_invalid_or_protected_backup(repo, branch):
    if branch == "refs/heads/master":
        # A literal branch with this name is valid Git; protect it explicitly.
        p = wa.plan_archive(
            repo.base, repo.tree, "origin", branch, protected_branches=[branch]
        )
    else:
        p = wa.plan_archive(repo.base, repo.tree, "origin", branch)
    assert p["status"] == "HOLD"


def test_additional_protected_branch_cannot_be_bypassed_by_old_plan(repo):
    p = plan(repo)
    with pytest.raises(wa.Hold):
        execute(repo, p, protected_branches=["archive/pilot"])
    assert_retained(repo)


def test_plan_tampering_and_receipt_paths(repo):
    p = plan(repo)
    tampered = copy.deepcopy(p)
    tampered["head"] = "0" * 40
    with pytest.raises(wa.Hold, match="fingerprint"):
        execute(repo, tampered)
    for receipt in (repo.tree / "receipt.json", repo.base / ".git" / "receipt.json"):
        with pytest.raises(wa.Hold, match="Receipt"):
            wa.archive(repo.base, p, receipt, p["approval"], wa.EXCLUSIVE)
    receipt = repo.root / "receipt.json"
    receipt.write_text("valuable old receipt")
    with pytest.raises(wa.Hold):
        execute(repo, p)
    assert receipt.read_text() == "valuable old receipt"
    assert_retained(repo)


def test_cli_default_and_hold_exit_codes(repo, capsys):
    args = [
        "--repo",
        str(repo.base),
        "archive",
        "--worktree",
        str(repo.tree),
        "--remote",
        "origin",
        "--backup-branch",
        "archive/pilot",
    ]
    assert wa.main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PLAN_ONLY"
    assert_retained(repo)
    assert wa.main([*args, "--execute"]) == 3
    assert json.loads(capsys.readouterr().out)["status"] == "HOLD"
    assert_retained(repo)


@pytest.mark.parametrize(
    "raw",
    [b"garbage", b"0\trefs/heads/archive/pilot\n", b"a" * 40 + b"\trefs/heads/other\n"],
)
def test_malformed_remote_output_unverified(repo, monkeypatch, raw):
    git = wa.git
    monkeypatch.setattr(
        wa,
        "git",
        lambda root, *args: raw if args[0] == "ls-remote" else git(root, *args),
    )
    assert plan(repo)["remote_evidence"]["state"] == "unverified"


def test_failed_inventory_catalog_never_means_missing(repo, monkeypatch, capsys):
    git = wa.git
    calls = []

    def offline(root, *args):
        if args[0] == "ls-remote":
            calls.append(args)
            raise wa.Hold("offline")
        return git(root, *args)

    monkeypatch.setattr(wa, "git", offline)
    assert wa.main(["--repo", str(repo.base), "inventory"]) == 3
    result = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert len(result["worktrees"]) == 2
    assert all(
        "REMOTE_MISSING" not in r["classifications"] for r in result["worktrees"]
    )
    assert_retained(repo)


def test_git_subprocess_fence_rejects_real_repository():
    with pytest.raises(AssertionError, match="outside synthetic"):
        wa.git(Path(__file__).resolve().parents[1], "status", "--short")


def test_git_environment_cannot_redirect_repository(repo, monkeypatch):
    monkeypatch.setenv("GIT_DIR", "/definitely/not/a/repository")
    monkeypatch.setenv("GIT_WORK_TREE", "/")
    assert plan(repo)["head"] == g(repo.tree, "rev-parse", "HEAD")


def test_status_command_failure_is_hold(repo, monkeypatch, capsys):
    git = wa.git

    def fail(root, *args):
        if args[0] == "status":
            raise wa.Hold("Synthetic status failure")
        return git(root, *args)

    monkeypatch.setattr(wa, "git", fail)
    assert wa.main(["--repo", str(repo.base), "inventory"]) == 3
    result = json.loads(capsys.readouterr().out)
    assert all(not r["git_status"]["complete"] for r in result["worktrees"])
    assert_retained(repo)


@pytest.mark.parametrize("drift", ["url", "branch", "head", "path"])
def test_identity_drift_invalidates_plan(repo, drift):
    p = plan(repo)
    if drift == "url":
        g(repo.base, "remote", "set-url", "origin", repo.root / "changed.git")
    elif drift == "branch":
        g(repo.tree, "switch", "-c", "other-identity")
    elif drift == "head":
        g(repo.tree, "commit", "--allow-empty", "-m", "local new commit")
    else:
        g(repo.base, "worktree", "move", repo.tree, repo.root / "relocated")
    with pytest.raises(wa.Hold):
        execute(repo, p)
    assert (repo.root / "relocated").exists() if drift == "path" else repo.tree.exists()


def test_replay_archive_with_saved_plan_does_not_repeat(repo):
    p = plan(repo)
    execute(repo, p)
    with pytest.raises(wa.Hold):
        wa.archive(
            repo.base, p, repo.root / "second-receipt.json", p["approval"], wa.EXCLUSIVE
        )
    assert not repo.tree.exists()
    assert not (repo.root / "second-receipt.json").exists()


def test_restore_approval_is_required(repo):
    record = execute(repo)
    with pytest.raises(wa.Hold, match="approval"):
        wa.restore(repo.base, record, repo.tree, None, wa.EXCLUSIVE)
    assert not repo.tree.exists()


def test_restore_fetch_race_fails_before_checkout(repo, monkeypatch):
    record = execute(repo)
    rp = wa.restore_plan(repo.base, record, repo.tree)
    git = wa.git

    def change(root, *args):
        if root == repo.base and args[0] == "fetch":
            advance_remote(repo)
        return git(root, *args)

    monkeypatch.setattr(wa, "git", change)
    with pytest.raises(wa.Hold, match="SHA"):
        wa.restore(repo.base, record, repo.tree, rp["approval"], wa.EXCLUSIVE)
    assert not repo.tree.exists()


def test_inventory_successful_catalog_verifies_exact_not_protected_primary(
    repo, capsys
):
    assert wa.main(["--repo", str(repo.base), "inventory"]) == 3
    result = json.loads(capsys.readouterr().out)
    child = next(r for r in result["worktrees"] if r["path"] == str(repo.tree))
    assert child["exact_remote_head"]
    assert "CANDIDATE_FOR_ARCHIVE" in child["classifications"]


def test_completion_receipt_collision_aborts_before_removal(repo):
    collision = repo.root / "receipt.json.completed.json"
    collision.write_text("retain")
    with pytest.raises(wa.Hold):
        execute(repo)
    assert collision.read_text() == "retain"
    assert_retained(repo)
