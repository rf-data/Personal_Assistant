"""Synthetic repositories only; runnable with the Python standard library.

Run: python3 -m unittest tests.test_worktree_manager -v
No application configuration, service, real project data or network is needed.
"""

import contextlib
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from scripts import worktree_manager as manager


def command(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_ALLOW_PROTOCOL="",
        GIT_TERMINAL_PROMPT="0",
    )
    return (
        subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "init.templateDir=",
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=synthetic@example.invalid",
                "-c",
                "commit.gpgSign=false",
                *args,
            ],
            env=env,
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )


def tree_snapshot(root):
    """Detect writes to refs, indexes, reflogs, configuration and fixture data."""
    result = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        if path.is_file() and not path.is_symlink():
            result[str(path.relative_to(root))] = (
                info.st_mtime_ns,
                info.st_mode,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
    return result


class WorktreeManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-worktrees-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "main repository"
        self.repo.mkdir()
        command(self.repo, "init", "--initial-branch=master")
        (self.repo / "README.md").write_text("Synthetic fixture\n")
        (self.repo / ".gitignore").write_text(".ignored/\n.env*\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-m", "Synthetic base")
        self.head = command(self.repo, "rev-parse", "HEAD")
        command(self.repo, "update-ref", "refs/remotes/origin/master", self.head)
        command(
            self.repo,
            "remote",
            "add",
            "origin",
            "https://github.com/example/synthetic.git",
        )
        self.hosting = dict(
            available=True,
            repository="example/synthetic",
            complete=True,
            fresh=True,
            branches={"master": self.head},
            pull_requests=[],
        )

    def add_worktree(self, name="clean", detached=False):
        path = self.base / name
        args = (
            ("--detach", str(path), self.head)
            if detached
            else ("-b", name.strip(), str(path), self.head)
        )
        command(self.repo, "worktree", "add", *args)
        return path

    def scan(self, **kwargs):
        return manager.inventory(
            self.repo,
            hosting=self.hosting,
            repository="example/synthetic",
            external_paths=(),
            **kwargs,
        )

    def record(self, path, report=None):
        return next(
            r for r in (report or self.scan())["worktrees"] if r["path"] == str(path)
        )

    def pr(self, **overrides):
        result = dict(
            number=1,
            state="closed",
            merged=True,
            draft=False,
            head_sha=self.head,
            head_ref="clean",
            head_repository="example/synthetic",
            base_ref="master",
            base_repository="example/synthetic",
        )
        result.update(overrides)
        return result

    def snapshot_file(self, **overrides):
        data = {
            k: v for k, v in self.hosting.items() if k not in {"available", "fresh"}
        }
        data.update(schema_version=1, observed_at=manager.utc_now())
        data.update(overrides)
        path = self.base / "snapshot.json"
        path.write_text(json.dumps(data))
        return path

    def test_primary_and_current_protected_candidate_never_safe(self):
        clean = self.add_worktree()
        report = self.scan()
        self.assertEqual(self.record(self.repo, report)["classification"], "ACTIVE")
        record = self.record(clean, report)
        self.assertEqual(record["classification"], "REMOVABLE_CANDIDATE")
        self.assertFalse(record["safe_to_remove"])
        self.assertEqual(record["reproducible"], "not_verified")
        self.assertEqual(len(record["pending_gates"]), len(manager.HUMAN_GATES))

    def test_both_operations_preserve_all_inputs_and_disable_fsmonitor(self):
        self.add_worktree()
        marker = self.base / "hook-was-run"
        hook = self.base / "fsmonitor.sh"
        hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
        hook.chmod(0o700)
        command(self.repo, "config", "core.fsmonitor", str(hook))
        before = tree_snapshot(self.base)
        for op, expected in (("inventory", 0), ("audit", 2)):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    manager.main([op, "--repository", str(self.repo)]), expected
                )
        self.assertEqual(before, tree_snapshot(self.base))
        self.assertFalse(marker.exists())

    def test_default_branch_checkout_is_protected_when_not_primary(self):
        command(self.repo, "checkout", "-b", "execution")
        default = self.base / "persistent-master"
        command(self.repo, "worktree", "add", str(default), "master")
        record = self.record(default)
        self.assertFalse(record["primary"])
        self.assertEqual(record["classification"], "ACTIVE")
        self.assertIn(
            "persistent_default_branch_worktree", record["classification_reasons"]
        )

    def test_status_never_executes_clean_or_process_filters(self):
        clean = self.add_worktree()
        marker = self.base / "filter-was-run"
        program = self.base / "filter.sh"
        program.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
        program.chmod(0o700)
        (clean / ".gitattributes").write_text("README.md filter=synthetic\n")
        command(self.repo, "config", "filter.synthetic.clean", str(program))
        command(self.repo, "config", "filter.synthetic.process", str(program))
        command(self.repo, "config", "filter.synthetic.required", "true")
        (clean / "README.md").write_text("Synthetic changed contents\n")
        self.record(clean)
        self.assertFalse(marker.exists())

    def test_dirty_untracked_and_ignored_are_separate(self):
        dirty = self.add_worktree("dirty")
        (dirty / "README.md").write_text("Synthetic edit\n")
        (dirty / "new file.txt").write_text("Synthetic new file")
        (dirty / ".ignored").mkdir()
        (dirty / ".ignored/data.bin").write_bytes(b"synthetic")
        record = self.record(dirty)
        self.assertEqual(record["classification"], "ACTIVE")
        self.assertEqual(record["status"]["tracked_change_count"], 1)
        self.assertEqual(record["status"]["untracked_count"], 1)
        self.assertEqual(record["status"]["ignored_indicator_count"], 1)
        self.assertFalse(record["status"]["ignored_children_enumerated"])

    def test_merged_with_ignored_data_needs_archive_review(self):
        clean = self.add_worktree()
        (clean / ".ignored").mkdir()
        (clean / ".ignored/evidence.txt").write_text("SYNTHETIC_PRIVATE_CONTENT")
        self.hosting["pull_requests"] = [self.pr()]
        record = self.record(clean)
        self.assertEqual(record["classification"], "ARCHIVE")
        self.assertNotIn("SYNTHETIC_PRIVATE_CONTENT", json.dumps(record))
        self.assertFalse(record["safe_to_remove"])

    def test_unavailable_hosting_and_missing_baseline_fail_closed(self):
        clean = self.add_worktree()
        self.hosting["available"] = False
        self.assertEqual(self.record(clean)["classification"], "REVIEW")
        command(self.repo, "update-ref", "-d", "refs/remotes/origin/master")
        record = self.record(clean)
        self.assertIn("origin_master_unavailable", record["observation_errors"])
        self.assertEqual(record["classification"], "REVIEW")

    def test_stale_incomplete_wrong_repo_and_changed_live_baseline(self):
        clean = self.add_worktree()
        for field, value in (
            ("fresh", False),
            ("complete", False),
            ("repository", "other/repo"),
            ("branches", {"master": "0" * 40}),
        ):
            with self.subTest(field=field):
                previous = self.hosting[field]
                self.hosting[field] = value
                self.assertEqual(self.record(clean)["classification"], "REVIEW")
                self.hosting[field] = previous
        command(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://github.com/other/repo.git",
        )
        self.assertEqual(self.record(clean)["classification"], "REVIEW")

    def test_draft_pr_and_branch_name_reuse_keep_active(self):
        clean = self.add_worktree()
        self.hosting["pull_requests"] = [
            self.pr(state="open", draft=True, merged=False, head_sha="0" * 40)
        ]
        record = self.record(clean)
        self.assertEqual(record["classification"], "ACTIVE")
        self.assertEqual(record["pull_requests"][0]["match"], "branch")

    def test_fork_same_name_is_not_local_branch_binding(self):
        clean = self.add_worktree()
        self.hosting["pull_requests"] = [
            self.pr(
                state="open",
                merged=False,
                head_repository="fork/synthetic",
                head_sha="0" * 40,
            )
        ]
        self.assertEqual(self.record(clean)["pull_requests"], [])

    def test_unique_commits_keep_active_even_when_pr_marked_merged(self):
        clean = self.add_worktree()
        (clean / "README.md").write_text("Synthetic unique commit\n")
        command(clean, "add", ".")
        command(clean, "commit", "-m", "Synthetic unique change")
        self.hosting["pull_requests"] = [self.pr()]
        record = self.record(clean)
        self.assertEqual(record["classification"], "ACTIVE")
        self.assertEqual(record["ancestry"]["ahead"], 1)
        self.assertFalse(record["ancestry"]["head_is_ancestor"])

    def test_detached_head_is_recorded_without_invented_branch(self):
        detached = self.add_worktree("detached", detached=True)
        record = self.record(detached)
        self.assertTrue(record["detached"])
        self.assertIsNone(record["branch"])
        self.assertEqual(record["head"], self.head)

    def test_missing_prunable_registration_is_review_not_candidate(self):
        missing = self.add_worktree("missing")
        missing.rename(self.base / "fixture-relocated")
        record = self.record(missing)
        self.assertTrue(record["prunable"])
        self.assertEqual(record["classification"], "REVIEW")
        self.assertFalse(record["status"]["available"])

    def test_locked_worktree_kept_active_without_free_text_reason(self):
        locked = self.add_worktree("locked")
        command(
            self.repo, "worktree", "lock", "--reason", "SYNTHETIC_SECRET", str(locked)
        )
        record = self.record(locked)
        self.assertEqual(record["classification"], "ACTIVE")
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(record))

    def test_wrong_repository_at_registered_path_is_not_scanned(self):
        wrong = self.add_worktree("wrong")
        wrong.rename(self.base / "saved-fixture")
        wrong.mkdir()
        command(wrong, "init", "--initial-branch=master")
        record = self.record(wrong)
        self.assertIn("worktree_identity_mismatch", record["observation_errors"])
        self.assertEqual(record["classification"], "REVIEW")

    def test_nul_parsing_handles_spaces_newlines_and_rename_sources(self):
        unusual = self.add_worktree("unusual path\n ", detached=True)
        source = unusual / "README.md"
        destination = unusual / "new\nname.txt"
        source.rename(destination)
        command(unusual, "add", "-A")
        record = self.record(unusual)
        self.assertTrue(record["status"]["available"], record["observation_errors"])
        self.assertEqual(
            record["status"]["tracked_changes"][0]["path"], "new\nname.txt"
        )
        self.assertEqual(record["status"]["tracked_changes"][0]["source"], "README.md")

    def test_private_names_and_contents_are_not_in_report(self):
        clean = self.add_worktree()
        (clean / ".env.password").write_text("SYNTHETIC_SECRET_VALUE")
        (clean / "private-customer.txt").write_text("SYNTHETIC_DOCUMENT_BODY")
        record = self.record(clean)
        raw = json.dumps(record)
        for value in (
            "SYNTHETIC_SECRET_VALUE",
            "SYNTHETIC_DOCUMENT_BODY",
            ".env.password",
            "private-customer.txt",
        ):
            self.assertNotIn(value, raw)
        self.assertEqual(record["status"]["untracked_count"], 1)
        self.assertEqual(record["status"]["ignored_indicator_count"], 1)

    def test_disk_scan_does_not_follow_symlinks_or_count_git(self):
        clean = self.add_worktree()
        outside = self.base / "external"
        outside.mkdir()
        (outside / "large").write_bytes(b"x" * 10000)
        before = manager.disk_usage(clean)
        (clean / "alias").symlink_to(outside, target_is_directory=True)
        after = manager.disk_usage(clean)
        self.assertEqual(after["apparent_bytes"], before["apparent_bytes"])
        self.assertEqual(after["symlinks"], 1)
        self.assertEqual(
            self.record(clean)["classification"], "ACTIVE"
        )  # untracked alias

    def test_budget_and_permission_errors_make_disk_estimate_partial(self):
        clean = self.add_worktree()
        record = self.record(clean, self.scan(max_entries=1))
        self.assertFalse(record["disk_usage"]["complete"])
        self.assertEqual(record["classification"], "REVIEW")
        with patch.object(manager.os, "scandir", side_effect=PermissionError):
            result = manager.disk_usage(clean)
        self.assertFalse(result["complete"])
        self.assertEqual(result["errors"], 1)

    def test_git_status_errors_are_sanitized_and_fail_closed(self):
        clean = self.add_worktree()
        original = manager.git

        def guarded(root, *args, **kwargs):
            if Path(root) == clean and args[0] == "status":
                raise manager.ObservationError("status_unavailable")
            return original(root, *args, **kwargs)

        with patch.object(manager, "git", guarded):
            record = self.record(clean)
        self.assertEqual(record["classification"], "REVIEW")
        self.assertFalse(record["status"]["available"])

    def test_timeout_and_success_with_stderr_are_incomplete(self):
        with patch.object(
            manager.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 1)
        ):
            with self.assertRaises(manager.ObservationError):
                manager.git(self.repo, "status")
        result = subprocess.CompletedProcess(
            [], 0, b"", b"PRIVATE_PATH_PERMISSION_WARNING"
        )
        with patch.object(manager.subprocess, "run", return_value=result):
            with self.assertRaises(manager.ObservationError) as raised:
                manager.git(self.repo, "status")
        self.assertNotIn("PRIVATE_PATH", str(raised.exception))

    def test_ref_changes_during_scan_revoke_candidate(self):
        clean = self.add_worktree()
        original = manager.git
        calls = 0

        def changed(root, *args, **kwargs):
            nonlocal calls
            raw = original(root, *args, **kwargs)
            if args[0] == "for-each-ref":
                calls += 1
                if calls == 2:
                    return raw + b"changed"
            return raw

        with patch.object(manager, "git", changed):
            report = self.scan()
        self.assertTrue(report["registry_or_refs_changed"])
        self.assertEqual(self.record(clean, report)["classification"], "REVIEW")

    def test_cached_and_live_remote_evidence_are_distinct(self):
        clean = self.add_worktree()
        command(self.repo, "update-ref", "refs/remotes/origin/clean", self.head)
        record = self.record(clean)
        self.assertTrue(record["local_branch_available"])
        self.assertEqual(record["cached_remote_branches"][0]["head"], self.head)
        self.assertFalse(record["live_remote_branch_available"])

    def test_hosting_schema_freshness_repository_binding_and_redaction(self):
        path = self.snapshot_file(pull_requests=[dict(self.pr(), body="PRIVATE_BODY")])
        loaded = manager.load_hosting(path, "example/synthetic")
        self.assertTrue(loaded["fresh"])
        self.assertNotIn("PRIVATE_BODY", json.dumps(loaded))
        self.assertEqual(len(loaded["sha256"]), 64)
        with self.assertRaises(ValueError):
            manager.load_hosting(path, "wrong/repo")
        old = datetime.now(UTC) - timedelta(days=2)
        path = self.snapshot_file(observed_at=old.isoformat())
        self.assertFalse(manager.load_hosting(path, "example/synthetic")["fresh"])

    def test_malformed_hosting_never_publishes_a_report(self):
        for data in (
            [],
            {"schema_version": 1},
            dict(
                schema_version=1,
                repository="example/synthetic",
                complete=True,
                observed_at=manager.utc_now(),
                branches={},
                pull_requests=[None],
            ),
        ):
            path = self.base / "malformed.json"
            path.write_text(json.dumps(data))
            with self.subTest(data=data), self.assertRaises(ValueError):
                manager.load_hosting(path, "example/synthetic")

    def test_non_utf8_filenames_remain_lossless_in_json_and_exportable_csv(self):
        clean = self.add_worktree()
        filename = os.fsencode(clean) + b"/synthetic-\xff.txt"
        fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        report = self.scan()
        self.assertEqual(
            self.record(clean, report)["status"]["untracked_files"],
            [os.fsdecode(b"synthetic-\xff.txt")],
        )
        self.assertEqual(json.loads(json.dumps(report, ensure_ascii=True)), report)
        manager.csv_text(report).encode("utf-8")

    def test_external_paths_are_stat_only(self):
        with patch.object(
            manager.os,
            "scandir",
            side_effect=AssertionError("must not list external data"),
        ):
            metadata = manager.external_metadata(self.repo)
        self.assertTrue(metadata["available"])
        self.assertFalse(metadata["contents_inspected"])
        self.assertFalse(
            manager.external_metadata(self.base / "not-present")["available"]
        )

    def test_json_and_csv_stdout_formats_preserve_all_inputs(self):
        self.add_worktree()
        before = tree_snapshot(self.base)
        for fmt in ("json", "csv"):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = manager.main(
                    ["inventory", "--repository", str(self.repo), "--format", fmt]
                )
            self.assertEqual(code, 0)
            if fmt == "json":
                self.assertEqual(
                    json.loads(output.getvalue())["summary"]["registered"], 2
                )
            else:
                import csv

                self.assertEqual(
                    len(list(csv.DictReader(io.StringIO(output.getvalue())))), 2
                )
        self.assertEqual(before, tree_snapshot(self.base))

    def test_cli_refuses_filesystem_output_options(self):
        destination = self.repo / "artifacts/forbidden"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            manager.main(["inventory", "--output-dir", str(destination)])
        self.assertFalse(destination.exists())

    def test_csv_escapes_formulas_and_roundtrips_nested_json(self):
        report = dict(
            worktrees=[dict(branch="=cmd()", status=dict(ignored=["a\nb"]), safe=False)]
        )
        text = manager.csv_text(report)
        import csv

        row = next(csv.DictReader(io.StringIO(text)))
        self.assertEqual(row["branch"], "'=cmd()")
        self.assertEqual(json.loads(row["status"]), dict(ignored=["a\nb"]))

    def test_mutating_cli_operations_are_not_supported(self):
        for op in ("remove", "prune", "archive", "create"):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                manager.main([op])


if __name__ == "__main__":
    unittest.main()
