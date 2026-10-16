"""Synthetic audit fixtures: read-only evidence, privacy, variants and exports."""

import json
import socket
import subprocess

import pytest

from scripts import repository_audit as module


def command(root, *args):
    return (
        subprocess.check_output(
            ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", *args],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Audit must not use network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    root = tmp_path / "repository"
    root.mkdir()
    command(root, "init", "--initial-branch=master")
    (root / "docs").mkdir()
    (root / "data").mkdir()
    (root / "README.md").write_text("# Example\n\n[Guide](docs/guide.md)\n")
    (root / "docs/guide.md").write_text("# Older guide\n")
    (root / "data/private.md").write_text("SYNTHETIC_PRIVATE_DATA\n")
    (root / ".env.local").write_text("SYNTHETIC_SECRET=not-a-real-key\n")
    (root / ".gitignore").write_text("local-cache/\n")
    command(root, "add", ".")
    command(
        root,
        "-c",
        "user.name=Synthetic",
        "-c",
        "user.email=synthetic@example.invalid",
        "commit",
        "-m",
        "Synthetic fixture",
    )
    return root


def test_inventory_is_deterministic_and_does_not_read_private_blobs(repo, monkeypatch):
    original = module.git
    private = {
        command(repo, "rev-parse", "HEAD:" + name)
        for name in (".env.local", "data/private.md")
    }

    def guarded(root, *args):
        assert not (args[:2] == ("cat-file", "blob") and args[2] in private)
        return original(root, *args)

    monkeypatch.setattr(module, "git", guarded)
    (repo / "local-cache").mkdir()
    (repo / "local-cache/private.json").write_text("SYNTHETIC_IGNORED_CONTENT")
    baseline = command(repo, "rev-parse", "HEAD")
    first = module.audit(repo, baseline)
    assert first == module.audit(repo, baseline)
    raw = json.dumps(first)
    assert "SYNTHETIC_SECRET" not in raw and "SYNTHETIC_PRIVATE_DATA" not in raw
    assert "SYNTHETIC_IGNORED_CONTENT" not in raw
    assert first["local_extras"]["groups"]["ignored:local-cache"]["files"] == 1
    assert all(
        not f["content_read"]
        for f in first["tracked_files"]
        if f["path"] in {".env.local", "data/private.md"}
    )
    assert command(repo, "status", "--porcelain") == ""


def test_document_variants_use_content_and_ancestry_not_just_names(repo, tmp_path):
    previous = command(repo, "rev-parse", "HEAD")
    (repo / "docs/guide.md").write_text("# Current guide\n")
    command(repo, "add", "docs/guide.md")
    command(
        repo,
        "-c",
        "user.name=Synthetic",
        "-c",
        "user.email=synthetic@example.invalid",
        "commit",
        "-m",
        "Synthetic revision",
    )
    current = command(repo, "rev-parse", "HEAD")
    older = tmp_path / "older"
    command(repo, "worktree", "add", "--detach", str(older), previous)
    (older / "docs/local.md").write_text("# Independent local note\n")
    report = module.audit(repo, current)
    guide = next(v for v in report["document_variants"] if v["path"] == "docs/guide.md")
    assert len(guide["variants"]) == 2
    assert any(
        o["relation"] == "older_committed_version" and o["worktree"] == "older"
        for o in report["observations"]
    )
    assert any(
        o["relation"] == "local_only_variant" and o["git_status"] == "untracked"
        for o in report["observations"]
    )
    assert (older / "docs/local.md").read_text() == "# Independent local note\n"


def test_symlinked_files_and_parents_are_not_read(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "reference.md").write_text("SYNTHETIC_PRIVATE")
    (repo / "alias").symlink_to(outside, target_is_directory=True)
    (repo / "docs/link.md").symlink_to(outside / "reference.md")
    assert module.read_local(repo, "alias/reference.md") is None
    assert module.read_local(repo, "docs/link.md") is None
    findings = module.links(repo, "README.md", b"[reference](alias/reference.md)")
    assert findings[0]["status"] == "symlink_not_followed"


def test_export_never_overwrites_and_invalid_ref_does_not_publish(repo, tmp_path):
    target = tmp_path / "report.json"
    args = [
        "--repository",
        str(repo),
        "--baseline",
        command(repo, "rev-parse", "HEAD"),
        "--output",
        str(target),
    ]
    module.main(args)
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        module.main(args)
    assert before == target.read_bytes()
    missing = tmp_path / "missing.json"
    with pytest.raises(ValueError):
        module.main(
            [
                "--repository",
                str(repo),
                "--baseline",
                "HEAD; unsafe",
                "--output",
                str(missing),
            ]
        )
    assert not missing.exists()


def test_inline_link_scope_separates_missing_private_and_external_targets(repo):
    findings = module.links(
        repo,
        "README.md",
        b"[ok](docs/guide.md#heading) [bad](missing.md) [web](https://example.invalid/a) [secret](.env.local)\n```\n[example](not-an-active-link.md)\n```",
    )
    assert findings == [
        dict(target="missing.md", status="missing"),
        dict(target=".env.local", status="private_target_not_inspected"),
    ]


def test_private_local_planning_reports_remain_metadata_only(repo):
    (repo / "docs/project_cleanup_execution_report.md").write_text(
        "SYNTHETIC_PRIVATE_AUDIT"
    )
    report = module.audit(repo, command(repo, "rev-parse", "HEAD"))
    assert not any(
        o["path"].endswith("project_cleanup_execution_report.md")
        for o in report["observations"]
    )
    assert "SYNTHETIC_PRIVATE_AUDIT" not in json.dumps(report)
    assert any(
        d["path"].endswith("project_cleanup_execution_report.md")
        and not d["content_read"]
        for d in report["local_extras"]["documentation"]
    )


@pytest.mark.parametrize(
    "name",
    [
        "docs/secrets.md",
        "docs/passwords.md",
        "docs/credentials.md",
        "docs/private.md",
        "configuration/api-key.yaml",
    ],
)
def test_sensitive_document_names_stay_metadata_only(repo, name):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("SYNTHETIC_PRIVATE_DOCUMENT_CANARY")
    report = module.audit(repo, command(repo, "rev-parse", "HEAD"))
    assert module.read_local(repo, name) is None
    assert not any(o["path"] == name for o in report["observations"])
    assert "SYNTHETIC_PRIVATE_DOCUMENT_CANARY" not in json.dumps(report)
