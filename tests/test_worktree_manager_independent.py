"""Independent, dependency-free safety checks using exclusively synthetic Git data."""

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import worktree_manager as manager


class WorktreeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wt01a-independent-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repository"
        self.root.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_AUTHOR_NAME="Synthetic",
            GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Synthetic",
            GIT_COMMITTER_EMAIL="test@example.invalid",
        )
        self.git("init", "--initial-branch=master")
        self.git("config", "commit.gpgsign", "false")
        (self.root / "README.md").write_text("Synthetic fixture\n")
        (self.root / ".gitignore").write_text("cache/\n.env*\n")
        self.git("add", ".")
        self.git("commit", "-m", "Synthetic fixture")
        self.head = self.git("rev-parse", "HEAD").strip()
        self.git("update-ref", "refs/remotes/origin/master", self.head)

    def git(self, *args, root=None):
        return subprocess.check_output(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-C",
                str(root or self.root),
                *args,
            ],
            env=self.env,
            stderr=subprocess.DEVNULL,
        ).decode()

    def worktree(self, name="feature", *, detached=False):
        path = self.base / name
        self.git(
            "worktree",
            "add",
            *(["--detach"] if detached else ["-b", "synthetic-feature"]),
            str(path),
            self.head,
        )
        return path

    def report(self):
        return manager.inventory(self.root, external_paths=(), disk_seconds=5)

    def row(self, report, path):
        return next(r for r in report["worktrees"] if r["path"] == str(path))

    def test_git_metadata_and_all_fixture_bytes_are_preserved(self):
        path = self.worktree()
        (path / "valuable-untracked.md").write_text("Synthetic valuable work\n")

        def fingerprint():
            return {
                str(p.relative_to(self.base)): hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
                for p in self.base.rglob("*")
                if p.is_file() and not p.is_symlink()
            }

        before = fingerprint()
        self.report()
        self.report()
        self.assertEqual(before, fingerprint())

    def test_missing_registered_path_remains_registered_and_requires_review(self):
        path = self.worktree()
        path.rename(self.base / "synthetic-relocated")
        before = self.git("worktree", "list", "--porcelain", "-z")
        row = self.row(self.report(), path)
        self.assertTrue(row["prunable"])
        self.assertEqual(row["classification"], "REVIEW")
        self.assertFalse(row["safe_to_remove"])
        self.assertEqual(before, self.git("worktree", "list", "--porcelain", "-z"))

    def test_dirty_untracked_and_ignored_metadata_never_exposes_contents(self):
        path = self.worktree()
        (path / "README.md").write_text("SYNTHETIC_PRIVATE_CONTENT")
        (path / "notes.md").write_text("SYNTHETIC_UNTRACKED_CONTENT")
        (path / "cache").mkdir()
        (path / "cache/data.bin").write_bytes(b"SYNTHETIC_IGNORED_CONTENT")
        (path / ".env.credentials").write_text("SYNTHETIC_SECRET_CONTENT")
        row = self.row(self.report(), path)
        self.assertEqual(row["classification"], "ACTIVE")
        self.assertEqual(row["status"]["untracked_files"], ["notes.md"])
        self.assertEqual(row["status"]["tracked_change_count"], 1)
        self.assertEqual(row["status"]["ignored_indicator_count"], 2)
        raw = json.dumps(row)
        for value in (
            "SYNTHETIC_PRIVATE_CONTENT",
            "SYNTHETIC_UNTRACKED_CONTENT",
            "SYNTHETIC_IGNORED_CONTENT",
            "SYNTHETIC_SECRET_CONTENT",
            ".env.credentials",
        ):
            self.assertNotIn(value, raw)

    def test_existing_path_with_missing_git_marker_does_not_fall_back(self):
        path = self.worktree()
        (path / ".git").rename(path / "synthetic-disabled-marker")
        row = self.row(self.report(), path)
        self.assertFalse(row["status"]["available"])
        self.assertEqual(row["classification"], "REVIEW")

    def test_missing_baseline_never_proves_integration(self):
        path = self.worktree()
        self.git("update-ref", "-d", "refs/remotes/origin/master")
        row = self.row(self.report(), path)
        self.assertFalse(row["ancestry"].get("head_is_ancestor", False))
        self.assertEqual(row["classification"], "REVIEW")

    def test_bounded_disk_scan_does_not_follow_static_symlink_targets(self):
        path = self.worktree()
        outside = self.base / "external"
        outside.mkdir()
        (outside / "data.bin").write_bytes(b"x" * 100000)
        (path / "external-link").symlink_to(outside, target_is_directory=True)
        result = manager.disk_usage(path, max_entries=1000, seconds=5)
        self.assertEqual(result["symlinks"], 1)
        self.assertLess(result["apparent_bytes"], 100000)
        self.assertFalse(manager.disk_usage(path, max_entries=1, seconds=5)["complete"])

    def test_external_availability_never_lists_or_reads_artifact_children(self):
        outside = self.base / "external"
        outside.mkdir()
        with patch.object(
            os, "scandir", side_effect=AssertionError("No external listing")
        ):
            result = manager.external_metadata(outside)
        self.assertTrue(result["available"])
        self.assertFalse(result["contents_inspected"])

    def test_odd_worktree_paths_survive_registry_and_csv(self):
        path = self.worktree("feature with\nnewline")
        report = self.report()
        self.assertEqual(self.row(report, path)["path"], str(path))
        rows = list(csv.DictReader(io.StringIO(manager.csv_text(report))))
        self.assertIn(str(path), [row["path"] for row in rows])

    def test_rename_parser_preserves_record_boundaries(self):
        result = manager.parse_status(b"R  new\nname.md\0old\tname.md\0?? next.md\0")
        self.assertEqual(result["tracked_changes"][0]["source"], "old\tname.md")
        self.assertEqual(result["untracked_files"], ["next.md"])

    def test_git_errors_are_sanitized(self):
        error = subprocess.CompletedProcess([], 128, b"", b"SYNTHETIC_SECRET_TOKEN")
        with patch.object(subprocess, "run", return_value=error):
            with self.assertRaises(manager.ObservationError) as exc:
                manager.git(self.root, "status")
        self.assertNotIn("SYNTHETIC_SECRET_TOKEN", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
