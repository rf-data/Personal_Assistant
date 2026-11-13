"""B2 contract tests. All repository access is to self-created tiny fixtures."""

import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from scripts import worktree_deep_preflight as deep
from tests import test_worktree_deep_preflight as b1


class DiagnosticTests(unittest.TestCase):
    hold = b1.DeepTests.hold

    def setUp(self):
        self.f = b1.Fixture()
        self.addCleanup(self.f.temp.cleanup)

    def observe(self, path=None, **kwargs):
        before = b1.snapshot(self.f.base)
        report = deep.preflight(
            path or self.f.repo, repository=self.f.repo, mode=deep.DIAGNOSTIC, **kwargs
        )
        self.assertEqual(before, b1.snapshot(self.f.base))
        self.hold(report)
        self.assertEqual(report["mode"], deep.DIAGNOSTIC)
        self.assertTrue(set(deep.UNVERIFIED) <= set(report["uncertainties"]))
        return report

    def direct(self, change=None, **limits):
        request = {**b1.request(self.f.repo, **limits), "mode": deep.DIAGNOSTIC}
        original = deep.Observer.git
        before = b1.snapshot(self.f.base)

        def altered(observer, args, label):
            raw = original(observer, args, label)
            return change(observer, args, label, raw) if change else raw

        with patch.object(deep.Observer, "git", altered):
            report = deep.Observer(request).run()
        self.assertEqual(before, b1.snapshot(self.f.base))
        self.hold(report)
        return report

    def completed(self, report):
        self.assertEqual(
            report["diagnostic_status"], "COMPLETED_WITH_LIMITATIONS", report["errors"]
        )
        self.assertTrue(report["observation_complete"])
        self.assertEqual(set(report["required_observations"].values()), {"COMPLETED"})
        self.assertEqual(report["errors"], [deep.ISOLATION_BLOCKER])
        self.assertEqual(report["git_subprocess_count"], 14)
        self.assertFalse(report["atomic_snapshot"])
        self.assertFalse(report["consistency"]["atomic_snapshot"])
        self.assertEqual(report["environment_assumption"], "non_adversarial_local")

    def incomplete(self, report, error):
        self.assertEqual(report["diagnostic_status"], "INCOMPLETE")
        self.assertFalse(report["observation_complete"])
        self.assertIn(error, report["errors"])

    def test_default_and_explicit_strict_retain_blocker(self):
        before = b1.snapshot(self.f.base)
        reports = [
            deep.preflight(self.f.repo, repository=self.f.repo, **kwargs)
            for kwargs in ({}, {"mode": deep.STRICT})
        ]
        for report in reports:
            self.hold(report)
            self.assertEqual(report["diagnostic_status"], "BLOCKED")
            self.assertEqual(report["mode"], deep.STRICT)
            self.assertTrue(report["observation_complete"])
            self.assertIn(deep.ISOLATION_BLOCKER, report["errors"])
            self.assertEqual(report["git_subprocess_count"], 14)
        self.assertEqual(before, b1.snapshot(self.f.base))

    def test_complete_primary_and_linked_diagnostics(self):
        linked = self.f.add()
        for path in (self.f.repo, linked):
            self.completed(self.observe(path))

    def test_warnings_are_completed_observations_without_authorization(self):
        linked = self.f.add()
        self.f.git("worktree", "lock", str(linked))
        (linked / "tiny.txt").write_bytes(b"dirty synthetic bytes")
        report = self.observe(
            linked, evidence=["synthetic-backup", "synthetic-restore"]
        )
        self.completed(report)
        self.assertEqual(report["dimensions"]["identity"], "WARN")
        self.assertEqual(report["dimensions"]["git_status"], "WARN")
        self.assertEqual(report["preservation"]["backup"], "NOT_VERIFIED")
        self.assertEqual(report["preservation"]["independent_restore"], "NOT_VERIFIED")
        self.assertIs(report["preservation"]["references_verified"], False)

    def test_requires_explicit_canonical_paths_and_valid_mode(self):
        for path, kwargs, error in (
            (self.f.repo, {}, "registry_repository_required"),
            (None, {"repository": self.f.repo}, "invalid_request_or_worker_report"),
            ("relative", {"repository": self.f.repo}, "noncanonical_or_unsafe_root"),
            (self.f.repo, {"repository": "relative"}, "noncanonical_or_unsafe_root"),
        ):
            with self.subTest(error=error):
                report = deep.preflight(path, mode=deep.DIAGNOSTIC, **kwargs)
                self.hold(report)
                self.assertEqual(report["diagnostic_status"], "BLOCKED")
                self.assertEqual(report["worker_subprocess_count"], 0)
                self.assertIn(error, report["errors"])
        report = deep.preflight(
            self.f.repo, repository=self.f.repo, mode="waive_safety"
        )
        self.hold(report)
        self.assertIn("invalid_mode", report["errors"])

    def test_missing_baseline_is_incomplete(self):
        report = self.observe(baseline="refs/heads/missing")
        self.incomplete(report, "baseline_ref_missing")
        self.assertEqual(report["required_observations"]["integration"], "NOT_CHECKED")

    def test_skipped_nested_repository_is_incomplete(self):
        self.f.git("init", str(self.f.repo / "nested"))
        report = self.observe()
        self.incomplete(report, "filesystem_content_skipped")
        self.assertFalse(report["storage"]["complete"])

    def test_worker_timeout_kills_actual_child(self):
        original = subprocess.Popen
        spawned = []

        def launch(command, **kwargs):
            process = original(
                [sys.executable, "-c", "import time;time.sleep(10)"], **kwargs
            )
            spawned.append(process)
            return process

        tick = time.monotonic()
        with patch.object(deep.subprocess, "Popen", side_effect=launch):
            report = self.observe(worker_seconds=0.05)
        self.incomplete(report, "worker_timeout")
        self.assertIsNone(report["git_subprocess_count"])
        self.assertIsNotNone(spawned[0].poll())
        self.assertLess(time.monotonic() - tick, 2)

    def test_git_timeout_is_incomplete(self):
        original = subprocess.Popen

        def launch(command, **kwargs):
            return original(
                [sys.executable, "-c", "import time;time.sleep(10)"], **kwargs
            )

        with patch.object(deep.subprocess, "Popen", side_effect=launch):
            report = self.direct(subprocess_seconds=0.05)
        self.incomplete(report, "subprocess_timeout")
        self.assertEqual(report["operations"][0]["error"], "subprocess_timeout")

    def test_deadline_is_incomplete(self):
        self.incomplete(self.observe(deadline_seconds=0.001), "worker_timeout")

    def test_registry_changes_are_incomplete(self):
        report = self.direct(
            lambda o, a, label, raw: (
                raw.replace(b"\0\0", b"\0locked\0\0")
                if label == "registry_after"
                else raw
            )
        )
        self.incomplete(report, "registry_refs_or_head_changed")
        self.assertNotIn("consistency", report)

    def test_head_changes_are_incomplete(self):
        report = self.direct(
            lambda o, a, label, raw: b"1" * 40 + b"\n" if label == "head_after" else raw
        )
        self.incomplete(report, "registered_head_mismatch")
        self.assertEqual(report["required_observations"]["consistency"], "NOT_CHECKED")

    def test_ref_changes_are_incomplete(self):
        report = self.direct(
            lambda o, a, label, raw: (
                raw + b"refs/heads/added\0" + self.f.head + b"\0\0\n"
                if label == "refs_after"
                else raw
            )
        )
        self.incomplete(report, "registry_refs_or_head_changed")

    def test_metadata_change_is_incomplete(self):
        with patch.object(
            deep.Observer,
            "recheck_identity",
            side_effect=deep.Error("metadata_changed"),
        ):
            self.incomplete(self.direct(), "metadata_changed")

    def test_unsupported_ignore_is_incomplete(self):
        for pattern in (b"!keep\n", b"**/cache\n", b"[ab]\n", b"escape\\ space\n"):
            (self.f.repo / ".gitignore").write_bytes(pattern)
            self.incomplete(self.observe(), "unsupported_ignore_pattern")

    def test_unsupported_config_and_filter_never_execute(self):
        marker = self.f.base / "must-not-exist"
        program = self.f.base / "filter.sh"
        program.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        program.chmod(0o700)
        for key, value in (
            ("include.path", "/outside/no-read"),
            ("core.excludesFile", "/outside/no-read"),
            ("filter.synthetic.process", str(program)),
            ("core.autocrlf", "true"),
        ):
            self.f.git("config", key, value)
            self.incomplete(self.observe(), "unsupported_repository_configuration")
            self.f.git("config", "--unset", key)
        self.assertFalse(marker.exists())

    def test_attributes_remain_unsupported(self):
        (self.f.repo / ".gitattributes").write_bytes(b"*.txt filter=synthetic\n")
        self.incomplete(self.observe(), "attributes_require_later_review")

    def test_filesystem_and_git_limits_are_retained(self):
        for limits, error in (
            ({"max_entries": 1}, "filesystem_entry_limit"),
            ({"max_read_bytes": 1}, "file_read_byte_limit"),
            ({"max_git_output_bytes": 16}, "subprocess_output_limit"),
            ({"max_total_git_bytes": 100}, "subprocess_output_limit"),
        ):
            with self.subTest(limits=limits):
                self.incomplete(self.observe(**limits), error)
        (self.f.repo / "a/b/c").mkdir(parents=True)
        self.incomplete(self.observe(max_depth=1), "filesystem_depth_limit")

    def test_report_limit_is_incomplete_and_bounded(self):
        for i in range(40):
            (self.f.repo / (str(i) + "x" * 100)).write_bytes(b"x")
        report = self.observe(max_report_bytes=4096)
        self.incomplete(report, "report_output_limit")
        self.assertLessEqual(len(deep.json_bytes(report)) + 1, 4096)
        self.assertIsNone(report["git_subprocess_count"])

    def test_worker_pipe_limit_is_incomplete(self):
        with patch.object(
            deep, "bounded_process", side_effect=deep.Error("subprocess_output_limit")
        ):
            self.incomplete(self.observe(), "worker_output_limit")

    def test_symlink_and_repository_identity_checks_remain(self):
        linked = self.f.add()
        alias = self.f.base / "alias"
        alias.symlink_to(linked, target_is_directory=True)
        self.incomplete(self.observe(alias), "filesystem_or_metadata_error")
        linked.rename(self.f.base / "original-linked")
        self.f.git("init", str(linked))
        report = self.observe(linked)
        self.incomplete(report, "selected_repository_identity_mismatch")
        self.assertEqual(report["git_subprocess_count"], 0)

    def test_allowlist_has_no_diagnostic_exception(self):
        observer = deep.Observer({**b1.request(self.f.repo), "mode": deep.DIAGNOSTIC})
        for args in (
            ("status",),
            ("worktree", "remove", "any"),
            ("gc",),
            ("clean", "-fd"),
            ("checkout", "master"),
            ("rev-list", "--left-right", "--count", "HEAD...master", "--"),
        ):
            with self.assertRaisesRegex(deep.Error, "command_not_allowed"):
                observer.git(args, "disallowed")
        self.completed(self.observe())

    def test_worker_validation_rejects_missing_observations(self):
        valid = self.direct()
        mutations = [
            lambda r, key=key: r.pop(key)
            for key in (
                "observation_complete",
                "required_observations",
                "git_status",
                "integration",
                "storage",
                "consistency",
                "repository_identity",
                "registration",
                "snapshots",
                "operations",
                "preservation",
            )
        ]
        mutations += [
            lambda r, key=key: r["required_observations"].pop(key)
            for key in deep.REQUIRED_OBSERVATIONS
        ]
        mutations += [
            lambda r: r["required_observations"].update(storage="NOT_CHECKED"),
            lambda r: r["snapshots"].pop("registry_after"),
            lambda r: r["operations"].pop(),
            lambda r: r["storage"].update(complete=False),
            lambda r: r["storage"].update(skipped=["unobserved"]),
            lambda r: r["consistency"].update(head_unchanged=False),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                report = copy.deepcopy(valid)
                mutate(report)
                with patch.object(
                    deep, "bounded_process", return_value=deep.json_bytes(report)
                ):
                    result = self.observe()
                self.assertEqual(result["diagnostic_status"], "BLOCKED")
                self.assertIn("invalid_worker_report", result["errors"])
                self.assertFalse(result["observation_complete"])

    def test_worker_validation_rejects_safety_or_identity_lies(self):
        valid = self.direct()
        mutations = [
            lambda r, key=key, value=value: r.update({key: value})
            for key, value in (
                ("complete", True),
                ("safe_to_remove", True),
                ("removal_approval_sufficient", True),
                ("lifecycle_hold", "RELEASED"),
                ("lifecycle_decision", "APPROVED"),
                ("actual_reclaimable_storage", 10),
                ("safety_assurance", "PASS"),
                ("mode", deep.STRICT),
                ("observation_complete", "true"),
                ("observation_complete", False),
                ("errors", []),
                ("uncertainties", []),
                ("diagnostic_status", "INCOMPLETE"),
                ("dimensions", []),
                ("selected_path", deep.encoded("/wrong")),
                ("atomic_snapshot", True),
            )
        ]
        mutations += [
            lambda r: r["preservation"].update(backup="VERIFIED"),
            lambda r: r["preservation"].update(independent_restore="VERIFIED"),
            lambda r: r["registration"].update(removal_approval_sufficient=True),
            lambda r: r["integration"].update(baseline_ref="refs/heads/wrong"),
            lambda r: r["storage"].update(actual_reclaimable_storage="VERIFIED"),
            lambda r: r["integration"].update(ahead=None),
            lambda r: r["git_status"].update(raw_records=None),
            lambda r: r["git_status"].update(tracked_change_count=None),
            lambda r: r["consistency"].update(head_unchanged=1),
            lambda r: r["preservation"].update(references_verified=0),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                report = copy.deepcopy(valid)
                mutate(report)
                with patch.object(
                    deep, "bounded_process", return_value=deep.json_bytes(report)
                ):
                    result = self.observe()
                self.assertEqual(result["diagnostic_status"], "BLOCKED")
                self.assertFalse(result["observation_complete"])

    def test_malformed_worker_reports_never_crash_or_succeed(self):
        for raw in (
            b"null",
            b"[]",
            b"false",
            b"42",
            b"{}",
            b'{"lifecycle_hold":',
            b'{"a":1,"a":2}',
            b'{"a":NaN}',
            b'{"a":1e999}',
            b"[" * 2000 + b"]" * 2000,
        ):
            with self.subTest(raw=raw[:40]):
                with patch.object(deep, "bounded_process", return_value=raw):
                    report = self.observe()
                self.assertEqual(report["diagnostic_status"], "BLOCKED")
                self.assertFalse(report["observation_complete"])

    def test_incomplete_worker_cannot_claim_completed_status(self):
        report = self.direct()
        report["observation_complete"] = False
        report["errors"].append("baseline_ref_missing")
        with patch.object(
            deep, "bounded_process", return_value=deep.json_bytes(report)
        ):
            result = self.observe()
        self.assertEqual(result["diagnostic_status"], "BLOCKED")
        self.assertIn("invalid_worker_report", result["errors"])

    def test_parent_final_report_size_limit(self):
        valid = self.direct()
        valid["wall_seconds"] = 0
        cap = len(deep.json_bytes(valid)) + 128
        valid["limits"]["max_report_bytes"] = cap
        # Fill the bounded worker payload so the parent's count/time additions overflow.
        valid["padding"] = ""
        valid["padding"] = "x" * (cap - len(deep.json_bytes(valid)) - 1)
        raw = deep.json_bytes(valid)
        self.assertLessEqual(len(raw), cap)
        with patch.object(deep, "bounded_process", return_value=raw):
            report = self.observe(max_report_bytes=cap)
        self.incomplete(report, "report_output_limit")
        self.assertLessEqual(len(deep.json_bytes(report)) + 1, cap)

    def test_cli_exit_codes_and_no_mutation(self):
        before = b1.snapshot(self.f.base)
        base = ["--repository", str(self.f.repo), "--worktree", str(self.f.repo)]
        for extra, expected_code, status in (
            ([], 1, "BLOCKED"),
            (["--mode", "strict"], 1, "BLOCKED"),
            (["--mode", deep.DIAGNOSTIC], 0, "COMPLETED_WITH_LIMITATIONS"),
            (
                ["--mode", deep.DIAGNOSTIC, "--baseline", "refs/heads/absent"],
                1,
                "INCOMPLETE",
            ),
            (["--mode", "unknown"], 1, "BLOCKED"),
            (["--mode", deep.DIAGNOSTIC, "--remove"], 1, "BLOCKED"),
        ):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = deep.main(base + extra)
            self.assertEqual(code, expected_code)
            report = json.loads(output.getvalue())
            self.hold(report)
            self.assertEqual(report["diagnostic_status"], status)
        self.assertEqual(before, b1.snapshot(self.f.base))

    def test_help_documents_exit_codes_and_assumptions(self):
        with (
            contextlib.redirect_stdout(io.StringIO()) as output,
            self.assertRaises(SystemExit) as caught,
        ):
            deep.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        help_text = output.getvalue()
        for text in (
            deep.DIAGNOSTIC,
            "non-adversarial",
            "atomic snapshot",
            "Exit codes:",
            "COMPLETED_WITH_LIMITATIONS",
            "INCOMPLETE/BLOCKED",
            "lifecycle HOLD",
        ):
            self.assertIn(text, help_text)


if __name__ == "__main__":
    unittest.main()
