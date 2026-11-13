"""Small synthetic fixtures only; every temporary write stays in WORKSPACE.

python3 -m unittest tests.test_worktree_deep_preflight -v
python3 -m tests.test_worktree_deep_preflight --benchmark
"""

import base64
import contextlib
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from scripts import worktree_deep_preflight as deep
from tests.test_worktree_fast_inventory import Fixture, WORKSPACE


def snapshot(base):
    result = {}
    for path in base.rglob("*"):
        info = path.lstat()
        if path.is_symlink():
            content = os.fsencode(os.readlink(path))
        elif path.is_file():
            content = hashlib.sha256(path.read_bytes()).digest()
        else:
            continue
        result[os.fsencode(path.relative_to(base))] = (
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            info.st_nlink,
            content,
        )
    return result


def request(path, **limits):
    return dict(
        worktree=str(path),
        repository=str(path),
        baseline="refs/heads/master",
        evidence=[],
        limits={**deep.DEFAULTS, **limits},
    )


class DeepTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.temp.cleanup)

    def hold(self, report):
        self.assertFalse(report["safe_to_remove"])
        self.assertFalse(report["removal_approval_sufficient"])
        self.assertEqual(report["lifecycle_hold"], deep.HOLD)
        self.assertEqual(report["lifecycle_decision"], deep.HOLD)
        self.assertEqual(report["actual_reclaimable_storage"], "NOT_VERIFIED")
        self.assertNotIn("REMOVABLE_CANDIDATE", json.dumps(report))
        self.assertFalse(report["complete"])
        self.assertEqual(report["safety_assurance"], "BLOCKED")
        self.assertEqual(report["dimensions"]["safety"], "BLOCKED")
        self.assertTrue(
            set(report["dimensions"].values())
            <= {"PASS", "WARN", "BLOCKED", "NOT_CHECKED"}
        )

    def observe(self, path=None, **kwargs):
        # Verify all fixture bytes, refs/index/config, modes, inode/link identities
        # and tracked-file timestamps around every public observation in this suite.
        before = snapshot(self.f.base)
        report = deep.preflight(path or self.f.repo, repository=self.f.repo, **kwargs)
        self.assertEqual(before, snapshot(self.f.base))
        self.hold(report)
        return report

    def direct_observe(self, **limits):
        before = snapshot(self.f.base)
        report = deep.Observer(request(self.f.repo, **limits)).run()
        self.assertEqual(before, snapshot(self.f.base))
        self.hold(report)
        return report

    def good(self, report):
        self.assertTrue(report["observation_complete"], report["errors"])
        self.assertEqual(report["git_subprocess_count"], 14)
        self.assertEqual(report["worker_subprocess_count"], 1)
        self.assertIn("git_metadata_isolation_not_verified", report["errors"])
        self.assertTrue(report["consistency"]["registry_unchanged"])

    def records(self, report):
        return {
            base64.b64decode(row["path"]["bytes_base64"]): row["code"]
            for row in report["git_status"]["raw_records"]
        }

    def test_clean_primary_exact_identity(self):
        report = self.observe()
        self.good(report)
        self.assertTrue(report["git_status"]["clean_tracked"])
        self.assertEqual(report["integration"]["ahead"], 0)
        self.assertEqual(
            report["storage"]["logical_regular_bytes"], len(b"synthetic\n")
        )
        self.assertEqual(
            report["repository_identity"]["inode"], self.f.repo.stat().st_ino
        )

    def test_clean_linked_worktree(self):
        path = self.f.add()
        report = self.observe(path)
        self.good(report)
        self.assertEqual(report["registration"]["path"], str(path))

    def test_dirty_unstaged(self):
        (self.f.repo / "tiny.txt").write_bytes(b"modified\n")
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"tiny.txt"], " M")
        self.assertEqual(report["git_status"]["unstaged_change_count"], 1)

    def test_staged_and_unstaged_same_path(self):
        (self.f.repo / "tiny.txt").write_bytes(b"staged\n")
        self.f.git("add", "tiny.txt")
        (self.f.repo / "tiny.txt").write_bytes(b"working\n")
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"tiny.txt"], "MM")
        self.assertEqual(report["git_status"]["staged_change_count"], 1)

    def test_staged_add_and_delete(self):
        (self.f.repo / "added").write_bytes(b"new")
        self.f.git("add", "added")
        self.f.git("rm", "tiny.txt")
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report), {b"added": "A ", b"tiny.txt": "D "})

    def test_unstaged_delete(self):
        (self.f.repo / "tiny.txt").unlink()
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"tiny.txt"], " D")

    def test_removed_and_recreated_path(self):
        self.f.git("rm", "tiny.txt")
        (self.f.repo / "tiny.txt").write_bytes(b"new untracked bytes")
        report = self.observe()
        self.good(report)
        self.assertEqual(report["git_status"]["staged_change_count"], 1)
        self.assertEqual(report["git_status"]["untracked_count"], 1)

    def test_untracked_and_ignored(self):
        (self.f.repo / ".gitignore").write_bytes(b"*.log\nignored/\n/only-root\n")
        (self.f.repo / "scratch").write_bytes(b"untracked")
        (self.f.repo / "x.log").write_bytes(b"ignored")
        (self.f.repo / "ignored").mkdir()
        (self.f.repo / "ignored/payload").write_bytes(b"ignored child")
        (self.f.repo / "only-root").write_bytes(b"ignored")
        report = self.observe()
        self.good(report)
        self.assertEqual(report["git_status"]["ignored_indicator_count"], 3)
        self.assertEqual(self.records(report)[b"scratch"], "??")
        self.assertEqual(self.records(report)[b"ignored/payload"], "!!")

    def test_nested_ignore_rules_and_info_exclude(self):
        (self.f.repo / ".git/info").mkdir(exist_ok=True)
        (self.f.repo / ".git/info/exclude").write_bytes(b"*.local\n")
        (self.f.repo / "child").mkdir()
        (self.f.repo / "child/.gitignore").write_bytes(b"/ignored\n")
        for path in ("child/ignored", "child/other.local", "outside"):
            (self.f.repo / path).write_bytes(b"synthetic")
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"child/ignored"], "!!")
        self.assertEqual(self.records(report)[b"child/other.local"], "!!")

    def test_unsupported_ignore_fails_closed(self):
        for pattern in (b"!keep\n", b"**/cache\n", b"[ab]\n", b"escaped\\ name\n"):
            (self.f.repo / ".gitignore").write_bytes(pattern)
            report = self.observe()
            self.assertFalse(report["complete"])
            self.assertIn("unsupported_ignore_pattern", report["errors"])

    def test_detached_head(self):
        report = self.observe(self.f.add(detached=True))
        self.good(report)
        self.assertTrue(report["integration"]["detached"])
        self.assertIsNone(report["registration"]["branch_ref"])

    def test_divergent_branches(self):
        path = self.f.add()
        (self.f.repo / "main-only").write_bytes(b"main")
        self.f.git("add", "main-only")
        self.f.git("commit", "-m", "Main diverges")
        subprocess.check_output(
            [
                "git",
                "-C",
                str(path),
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=/dev/null",
                "commit",
                "--allow-empty",
                "-m",
                "Branch diverges",
            ],
            env=deep.fast.git_environment(),
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        report = self.observe(path)
        self.good(report)
        self.assertEqual(
            (report["integration"]["ahead"], report["integration"]["behind"]), (1, 1)
        )
        self.assertFalse(report["integration"]["head_is_ancestor"])

    def test_missing_baseline(self):
        report = self.observe(baseline="refs/heads/absent")
        self.assertIn("baseline_ref_missing", report["errors"])
        self.assertEqual(report["dimensions"]["integration"], "BLOCKED")

    def test_baseline_must_be_full_local_ref(self):
        for baseline in ("master", "HEAD", "refs/heads/main~1", "refs/tags/v1"):
            self.assertFalse(self.observe(baseline=baseline)["complete"])

    def test_locked_is_observed_and_held(self):
        path = self.f.add()
        self.f.git("worktree", "lock", "--reason", "private reason", str(path))
        report = self.observe(path)
        self.good(report)
        self.assertTrue(report["registration"]["locked"])
        self.assertEqual(report["dimensions"]["identity"], "WARN")
        self.assertNotIn("private reason", json.dumps(report))

    def test_prunable_and_missing_root(self):
        path = self.f.add()
        path.rename(self.f.base / "moved")
        report = self.observe(path)
        self.assertFalse(report["complete"])
        self.assertEqual(report["git_subprocess_count"], 0)
        # A prunable registry row is rejected before any content traversal.
        raw = self.f.git("worktree", "list", "--porcelain", "-z")
        observer = deep.Observer(request(self.f.repo))
        with self.assertRaisesRegex(deep.Error, "bare_or_prunable_registration"):
            observer.registry(raw, os.fsencode(path), {}, self.f.head.decode())

    def test_missing_registration(self):
        observer = deep.Observer(request(self.f.repo))
        raw = self.f.git("worktree", "list", "--porcelain", "-z")
        with self.assertRaisesRegex(deep.Error, "selected_registration_missing"):
            observer.registry(
                raw, b"/synthetic/not-registered", {}, self.f.head.decode()
            )

    def test_symlink_root_and_parent_alias_rejected(self):
        alias = self.f.base / "alias"
        alias.symlink_to(self.f.repo, target_is_directory=True)
        parent = self.f.base / "parent-alias"
        parent.symlink_to(self.f.base, target_is_directory=True)
        for path in (alias, parent / "main"):
            report = self.observe(path)
            self.assertFalse(report["complete"])
            self.assertEqual(report["git_subprocess_count"], 0)

    def test_dot_dot_relative_and_slash_aliases_rejected(self):
        for path in (
            "relative",
            str(self.f.repo) + "/",
            str(self.f.repo) + "/../main",
            str(self.f.base) + "//main",
            "/",
        ):
            report = self.observe(path)
            self.assertFalse(report["complete"])
            self.assertEqual(report["worker_subprocess_count"], 0)

    def test_subdirectory_never_selects_ancestor(self):
        child = self.f.repo / "child"
        child.mkdir()
        self.assertFalse(self.observe(child)["complete"])

    def test_symlink_contents_never_followed(self):
        external = self.f.base / "outside"
        external.mkdir()
        (external / "valuable").write_bytes(b"not observed")
        (self.f.repo / "alias").symlink_to(external, target_is_directory=True)
        (self.f.repo / "broken").symlink_to("missing")
        report = self.observe()
        self.good(report)
        self.assertEqual(len(report["storage"]["symlinks"]), 2)
        self.assertEqual(
            report["storage"]["logical_regular_bytes"], len(b"synthetic\n")
        )
        self.assertNotIn("valuable", json.dumps(report))

    def test_tracked_symlink_status_and_type_change(self):
        (self.f.repo / "link").symlink_to("tiny.txt")
        self.f.git("add", "link")
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"link"], "A ")
        (self.f.repo / "link").unlink()
        (self.f.repo / "link").write_bytes(b"tiny.txt")
        self.assertEqual(self.records(self.observe())[b"link"], "AT")

    def test_nested_repository_skipped(self):
        nested = self.f.repo / "nested"
        self.f.git("init", str(nested))
        (nested / "do-not-enumerate").write_bytes(b"private")
        report = self.observe()
        self.assertIn("filesystem_content_skipped", report["errors"])
        self.assertEqual(len(report["storage"]["nested_repositories"]), 1)
        self.assertNotIn("do-not-enumerate", json.dumps(report))

    def test_nested_registered_worktree_never_traversed(self):
        path = self.f.repo / "registered-child"
        self.f.git("worktree", "add", "--detach", str(path), self.f.head)
        (path / "never-read").write_bytes(b"private")
        report = self.observe()
        self.assertFalse(report["complete"])
        self.assertNotIn("never-read", json.dumps(report))
        self.assertEqual(len(report["storage"]["skipped"]), 1)

    def test_hardlinks_logical_not_reclaimable(self):
        os.link(self.f.repo / "tiny.txt", self.f.repo / "hardlink")
        report = self.observe()
        self.good(report)
        self.assertEqual(
            report["storage"]["logical_regular_bytes"], 2 * len(b"synthetic\n")
        )
        self.assertEqual(
            report["storage"]["unique_inode_logical_bytes"], len(b"synthetic\n")
        )
        self.assertEqual(len(report["storage"]["hardlink_indicators"]), 2)

    def test_non_utf8_and_unusual_private_filenames_lossless(self):
        raw = b' secret\xff\n\t"\\ trailing '
        path = os.fsencode(self.f.repo) + b"/" + raw
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b"synthetic")
        os.close(fd)
        report = self.observe()
        self.good(report)
        self.assertIn(raw, self.records(report))
        self.assertEqual(json.loads(deep.json_bytes(report)), report)

    def test_non_utf8_registered_path(self):
        path = self.f.add(os.fsdecode(b" path\xff\n "), detached=True)
        report = self.observe(path)
        self.good(report)
        self.assertEqual(
            base64.b64decode(report["selected_path"]["bytes_base64"]), os.fsencode(path)
        )

    def test_entry_limit(self):
        report = self.observe(max_entries=1)
        self.assertIn("filesystem_entry_limit", report["errors"])
        self.assertFalse(report["storage"]["complete"])

    def test_read_byte_limit(self):
        report = self.observe(max_read_bytes=1)
        self.assertIn("file_read_byte_limit", report["errors"])

    def test_command_output_limit(self):
        report = self.observe(max_git_output_bytes=16)
        self.assertIn("subprocess_output_limit", report["errors"])

    def test_aggregate_command_output_limit(self):
        report = self.observe(max_total_git_bytes=100)
        self.assertFalse(report["complete"])

    def test_report_limit(self):
        for i in range(90):
            (self.f.repo / (str(i) + "x" * 100)).write_bytes(b"x")
        report = self.observe(max_report_bytes=4096)
        self.assertIn("report_output_limit", report["errors"])
        self.assertLess(len(deep.json_bytes(report)), 4096)

    def test_depth_limit(self):
        (self.f.repo / "a/b/c").mkdir(parents=True)
        report = self.observe(max_depth=1)
        self.assertIn("filesystem_depth_limit", report["errors"])

    def test_worker_timeout(self):
        original = subprocess.Popen
        spawned = []

        def launch(command, **kwargs):
            child = original(
                [sys.executable, "-c", "import time; time.sleep(10)"], **kwargs
            )
            spawned.append(child)
            return child

        tick = time.monotonic()
        with patch.object(deep.subprocess, "Popen", side_effect=launch):
            report = self.observe(worker_seconds=0.1)
        self.assertIn("worker_timeout", report["errors"])
        self.assertLess(time.monotonic() - tick, 2)
        self.assertIsNotNone(spawned[0].poll())

    def test_blocked_filesystem_worker_is_terminated(self):
        # A real worker starts an actual scan whose scandir is deliberately stuck.
        original = subprocess.Popen
        program = (
            "import json,sys,time; from scripts import worktree_deep_preflight as d; "
            "r=json.load(sys.stdin); d.os.scandir=lambda *a: time.sleep(30); "
            "d.Observer(r).run()"
        )

        def launch(command, **kwargs):
            return original([sys.executable, "-c", program], **kwargs)

        with patch.object(deep.subprocess, "Popen", side_effect=launch):
            report = self.observe(worker_seconds=0.3)
        self.assertIn("worker_timeout", report["errors"])

    def test_overall_deadline(self):
        report = self.observe(deadline_seconds=0.001)
        self.assertIn("worker_timeout", report["errors"])

    def injected(self, change):
        original = deep.Observer.git
        before = snapshot(self.f.base)

        def altered(observer, args, label):
            return change(observer, args, label, original(observer, args, label))

        with patch.object(deep.Observer, "git", altered):
            report = self.direct_observe()
        self.assertEqual(before, snapshot(self.f.base))
        self.hold(report)
        return report

    def test_registry_change_during_observation(self):
        report = self.injected(
            lambda o, a, label, raw: (
                raw.replace(b"\0\0", b"\0locked\0\0")
                if label == "registry_after"
                else raw
            )
        )
        self.assertIn("registry_refs_or_head_changed", report["errors"])

    def test_ref_change_during_observation(self):
        def change(o, a, label, raw):
            return (
                raw + b"refs/heads/added\0" + self.f.head + b"\0\0\n"
                if label == "refs_after"
                else raw
            )

        self.assertIn("registry_refs_or_head_changed", self.injected(change)["errors"])

    def test_mismatched_head(self):
        report = self.injected(
            lambda o, a, label, raw: (
                b"1" * 40 + b"\n" if label == "head_before" else raw
            )
        )
        self.assertIn("registered_head_mismatch", report["errors"])

    def test_mismatched_registered_branch(self):
        def change(o, a, label, raw):
            if label == "refs_before":
                return raw.replace(
                    b"refs/heads/master\0" + self.f.head,
                    b"refs/heads/master\0" + b"1" * 40,
                )
            return raw

        self.assertIn("registered_branch_mismatch", self.injected(change)["errors"])

    def test_metadata_change_during_observation(self):
        # Inject a changed recheck result without mutating the source fixture.
        original = deep.Observer.optional_read
        counts = {}

        def changed(o, fd, path):
            raw = original(o, fd, path)
            counts[path] = counts.get(path, 0) + 1
            return raw + b"changed" if path == b"index" and counts[path] == 2 else raw

        with patch.object(deep.Observer, "optional_read", changed):
            report = self.direct_observe()
        self.assertIn("metadata_changed", report["errors"])

    def test_missing_and_supplied_evidence_never_verified(self):
        for evidence in (
            (),
            ("backup-manifest.synthetic.json", "independent-restore.synthetic.json"),
        ):
            report = self.observe(evidence=evidence)
            self.good(report)
            self.assertEqual(
                report["preservation"]["evidence_references"], list(evidence)
            )
            self.assertEqual(report["preservation"]["backup"], "NOT_VERIFIED")
            self.assertEqual(
                report["preservation"]["independent_restore"], "NOT_VERIFIED"
            )
            self.assertFalse(report["preservation"]["references_verified"])

    def test_filters_fsmonitor_and_inherited_git_env_never_execute(self):
        marker = self.f.base / "executed"
        program = self.f.base / "hook.sh"
        program.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        program.chmod(0o700)
        self.f.git("config", "core.fsmonitor", str(program))
        with patch.dict(
            os.environ,
            {
                "GIT_DIR": "/not-selected",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.fsmonitor",
                "GIT_CONFIG_VALUE_0": str(program),
            },
        ):
            self.good(self.observe())
        self.f.git("config", "filter.test.process", str(program))
        self.assertIn("unsupported_repository_configuration", self.observe()["errors"])
        self.assertFalse(marker.exists())

    def test_config_includes_and_external_ignore_rejected(self):
        for key, value in (
            ("include.path", "/outside/no-read"),
            ("core.excludesFile", "/outside/no-read"),
        ):
            self.f.git("config", key, value)
            self.assertIn(
                "unsupported_repository_configuration", self.observe()["errors"]
            )
            self.f.git("config", "--unset", key)

    def test_attributes_and_masked_index_fail_closed(self):
        (self.f.repo / ".gitattributes").write_bytes(b"*.txt text\n")
        self.assertIn("attributes_require_later_review", self.observe()["errors"])
        (self.f.repo / ".gitattributes").unlink()
        self.f.git("update-index", "--assume-unchanged", "tiny.txt")
        self.assertIn("masked_or_unsupported_index", self.observe()["errors"])

    def test_git_metadata_symlink_rejected(self):
        target = self.f.base / "external-config"
        (self.f.repo / ".git/config").rename(target)
        (self.f.repo / ".git/config").symlink_to(target)
        self.assertIn("symlink_in_git_metadata", self.observe()["errors"])

    def test_reverse_pointer_mismatch(self):
        path = self.f.add()
        pointer = (path / ".git").read_text().strip()[8:]
        (Path(pointer) / "gitdir").write_bytes(b"/unintended/.git\n")
        self.assertIn("forward_reverse_identity_mismatch", self.observe(path)["errors"])

    def test_special_file_never_opened(self):
        os.mkfifo(self.f.repo / "fifo")
        report = self.observe()
        self.assertIn("filesystem_content_skipped", report["errors"])

    def test_only_selected_content_traversed(self):
        other = self.f.add()
        (other / "unrelated-do-not-open").write_bytes(b"other")
        original = deep.Observer.scan
        visited = []

        def scan(o, fd, relative, *args, **kwargs):
            visited.append(os.readlink("/proc/self/fd/" + str(fd)))
            return original(o, fd, relative, *args, **kwargs)

        with patch.object(deep.Observer, "scan", scan):
            report = self.direct_observe()
        self.good({**report, "worker_subprocess_count": 1})
        self.assertEqual(visited, [str(self.f.repo)])

    def test_no_existing_inventory_calls(self):
        with (
            patch.object(
                deep.fast, "inventory", side_effect=AssertionError("full inventory")
            ),
            patch.object(
                deep.manager, "inventory", side_effect=AssertionError("full inventory")
            ),
        ):
            report = self.direct_observe()
        self.assertTrue(report["observation_complete"], report["errors"])

    def test_mount_boundary_injected_no_traversal(self):
        (self.f.repo / "mount").mkdir()
        original = deep.safe_open

        def opened(fd, path, flags, **kwargs):
            if path == b"mount":
                raise OSError(errno.EXDEV, "synthetic bind mount")
            return original(fd, path, flags, **kwargs)

        with patch.object(deep, "safe_open", opened):
            report = self.direct_observe()
        self.assertIn("filesystem_content_skipped", report["errors"])
        self.assertEqual(len(report["storage"]["mount_boundaries"]), 1)

    def test_unsupported_kernel_fails_closed(self):
        with patch.object(deep.platform, "system", return_value="unsupported"):
            report = self.direct_observe()
        self.assertIn("openat2_platform_unsupported", report["errors"])

    def test_invalid_limits_and_evidence_keep_hold(self):
        for kwargs in (
            {"worker_seconds": 0},
            {"deadline_seconds": float("nan")},
            {"subprocess_seconds": float("inf")},
            {"max_entries": True},
            {"max_report_bytes": 1},
            {"evidence": [""]},
            {"unknown": 1},
        ):
            self.assertFalse(self.observe(**kwargs)["complete"])

    def test_cli_reports_success_and_errors_with_hold(self):
        for argv, expected in (
            (["--worktree", str(self.f.repo), "--repository", str(self.f.repo)], 1),
            ([], 1),
            (
                [
                    "--worktree",
                    str(self.f.repo),
                    "--repository",
                    str(self.f.repo),
                    "--deadline-seconds",
                    "nan",
                ],
                1,
            ),
            (
                [
                    "--worktree",
                    str(self.f.repo),
                    "--repository",
                    str(self.f.repo),
                    "--output",
                    "no-write",
                ],
                1,
            ),
        ):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = deep.main(argv)
            self.assertEqual(code, expected)
            self.hold(json.loads(output.getvalue()))

    def test_nested_bare_repository_skipped(self):
        nested = self.f.repo / "bare.git"
        self.f.git("init", "--bare", str(nested))
        report = self.observe()
        self.assertFalse(report["observation_complete"])
        self.assertEqual(len(report["storage"]["nested_repositories"]), 1)

    def test_empty_ignored_directory_indicator(self):
        (self.f.repo / ".gitignore").write_bytes(b"ignored/\n")
        (self.f.repo / "ignored").mkdir()
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"ignored/"], "!!")

    def test_symlinked_ignore_blocks_without_reading_target(self):
        target = self.f.base / "outside-ignore"
        target.write_bytes(b"*.secret\n")
        (self.f.repo / ".gitignore").symlink_to(target)
        report = self.observe()
        self.assertIn("symlinked_ignore_or_attributes", report["errors"])
        self.assertFalse(report["observation_complete"])

    def test_content_entry_limit_after_metadata(self):
        # Identity/metadata counts alone must not hide a missing content bound.
        original = deep.Observer.scan

        def scan(o, *args, **kwargs):
            o.limits["max_entries"] = o.entries + 1
            return original(o, *args, **kwargs)

        with patch.object(deep.Observer, "scan", scan):
            report = self.direct_observe()
        self.assertIn("filesystem_entry_limit", report["errors"])
        self.assertFalse(report["storage"]["complete"])

    def test_mode_change(self):
        (self.f.repo / "tiny.txt").chmod(0o755)
        report = self.observe()
        self.good(report)
        self.assertEqual(self.records(report)[b"tiny.txt"], " M")

    def test_git_timeout_is_finite(self):
        original = subprocess.Popen

        def child(command, **kwargs):
            return original(
                [sys.executable, "-c", "import time;time.sleep(10)"], **kwargs
            )

        before = snapshot(self.f.base)
        tick = time.monotonic()
        with patch.object(deep.subprocess, "Popen", side_effect=child):
            report = self.direct_observe(subprocess_seconds=0.05)
        self.assertIn("subprocess_timeout", report["errors"])
        self.assertLess(time.monotonic() - tick, 2)
        self.assertEqual(before, snapshot(self.f.base))
        self.hold(report)

    def test_registry_administrative_symlink_rejected(self):
        path = self.f.add()
        pointer = Path((path / ".git").read_text().strip()[8:])
        target = self.f.base / "outside-head"
        (pointer / "HEAD").rename(target)
        (pointer / "HEAD").symlink_to(target)
        report = self.observe()
        self.assertIn("symlink_in_registry_metadata", report["errors"])
        self.assertEqual(report["git_subprocess_count"], 0)

    def test_unsupported_object_layout(self):
        directory = self.f.repo / ".git/objects/info"
        directory.mkdir(exist_ok=True)
        (directory / "alternates").write_bytes(b"/outside/object-store\n")
        report = self.observe()
        self.assertIn("unsupported_git_object_or_attribute_layout", report["errors"])
        self.assertEqual(report["git_subprocess_count"], 0)

    def test_replacement_repository_cannot_adopt_registration(self):
        path = self.f.add()
        path.rename(self.f.base / "original-linked")
        self.f.git("init", str(path))
        report = self.observe(path)
        self.assertIn("selected_repository_identity_mismatch", report["errors"])
        self.assertEqual(report["git_subprocess_count"], 0)

    def test_explicit_registry_repository_required(self):
        report = deep.preflight(self.f.repo)
        self.hold(report)
        self.assertIn("registry_repository_required", report["errors"])
        self.assertEqual(report["worker_subprocess_count"], 0)


class ProcessTests(unittest.TestCase):
    def test_both_pipes_output_bounded(self):
        for fd in (1, 2):
            with self.assertRaisesRegex(deep.Error, "subprocess_output_limit"):
                deep.bounded_process(
                    [sys.executable, "-c", f"import os; os.write({fd},b'x'*10000)"],
                    timeout=2,
                    max_bytes=32,
                    group=True,
                )

    def test_errors_sanitized(self):
        for code in ("import sys;sys.stderr.write('SECRET')", "raise SystemExit(2)"):
            with self.assertRaises(deep.Error) as caught:
                deep.bounded_process(
                    [sys.executable, "-c", code], timeout=2, max_bytes=1024
                )
            self.assertNotIn("SECRET", str(caught.exception))

    def test_command_allowlist(self):
        observer = deep.Observer(request("/synthetic/no-read"))
        for args in (
            ("status",),
            ("checkout", "master"),
            ("rev-list", "--left-right", "--count", "HEAD...master", "--"),
        ):
            with self.assertRaisesRegex(deep.Error, "command_not_allowed"):
                observer.git(args, "disallowed")


def benchmark():
    rows = []
    for count, others in ((1, 0), (25, 0), (100, 4)):
        f = Fixture()
        try:
            for i in range(count - 1):
                (f.repo / f"untracked-{i}").write_bytes(b"tiny synthetic bytes\n")
            for i in range(others):
                f.add(f"other-{i}", detached=True)
            before = snapshot(f.base)
            samples = []
            for _ in range(3):
                report = deep.preflight(f.repo, repository=f.repo)
                if not report["observation_complete"]:
                    raise RuntimeError(report["errors"])
                samples.append(
                    dict(
                        observation_complete=report["observation_complete"],
                        safety_assurance=report["safety_assurance"],
                        wall_seconds=report["wall_seconds"],
                        git_subprocess_count=report["git_subprocess_count"],
                        worker_subprocess_count=report["worker_subprocess_count"],
                        total_subprocess_count=report["git_subprocess_count"] + 1,
                        git_seconds=sum(op["seconds"] for op in report["operations"]),
                        git_stdout_bytes=report["git_stdout_bytes"],
                        report_bytes=len(deep.json_bytes(report)),
                        filesystem_entries=report["storage"]["entries"],
                        metadata_entries=report["storage"]["metadata_entries"],
                        logical_regular_bytes=report["storage"][
                            "logical_regular_bytes"
                        ],
                    )
                )
            if before != snapshot(f.base):
                raise RuntimeError("source mutation")
            rows.append(
                dict(
                    kind="actual_small_synthetic_git",
                    files=count,
                    unrelated_registered_worktrees=others,
                    samples=samples,
                    median_wall_seconds=statistics.median(
                        s["wall_seconds"] for s in samples
                    ),
                )
            )
        finally:
            f.temp.cleanup()
    return dict(
        schema_version=1,
        generated_at=deep.datetime.now(deep.UTC).isoformat(),
        python=sys.version,
        git_version=subprocess.check_output(["git", "--version"], timeout=5)
        .decode()
        .strip(),
        limits=deep.DEFAULTS,
        measurements=rows,
        methodology="Three serial samples; setup and cleanup excluded; full parent/worker observation and report transfer timed. No real repositories inspected.",
        limitations=[
            "No total RSS or physical/reclaimable storage measurement.",
            "Synthetic fixtures and warm caches do not predict production runtime.",
            "Mount rejection is fault-injected in tests; no privileged mount fixture.",
        ],
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--benchmark"]:
        print(json.dumps(benchmark(), indent=2, sort_keys=True))
    else:
        unittest.main()
