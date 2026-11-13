"""Synthetic-only tests and reproducible benchmarks; standard Python/Git only.

Run tests with TMPDIR inside the authorized workspace, including the existing
maintenance suites. Run benchmarks with python3 -m tests.test_worktree_fast_inventory
--benchmark. Benchmark JSON is emitted to stdout; fixture setup is not timed.
"""

import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
import unittest
from unittest.mock import patch

from scripts import worktree_fast_inventory as fast

WORKSPACE = Path(__file__).resolve().parents[1]
HEAD = b"1" * 40


def registry_row(
    path=b"/synthetic/main", branch=b"refs/heads/master", head=HEAD, extra=b""
):
    identity = b"branch " + branch if branch else b"detached"
    return (
        b"worktree "
        + path
        + b"\0HEAD "
        + head
        + b"\0"
        + identity
        + b"\0"
        + extra
        + b"\0"
    )


def refs_row(name=b"refs/heads/master", head=HEAD, target=b""):
    return name + b"\0" + head + b"\0" + target + b"\0\n"


def simulated_runner(registry=None, refs=None, root="/synthetic/main"):
    registry = registry if registry is not None else registry_row()
    refs = refs if refs is not None else refs_row()

    def run(_root, args, **kwargs):
        return {
            fast.IDENTITY: os.fsencode(root) + b"\n",
            fast.REGISTRY: registry,
            fast.REFS: refs,
        }[args]

    return run


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wt03-synthetic-", dir=WORKSPACE)
        self.base = Path(self.temp.name)
        self.repo = self.base / "main"
        self.repo.mkdir()
        self.git("init", "--initial-branch=master")
        (self.repo / "tiny.txt").write_text("synthetic\n")
        self.git("add", "tiny.txt")
        self.git("commit", "-m", "Synthetic fixture")
        self.head = self.git("rev-parse", "HEAD").strip()
        self.git("update-ref", "refs/remotes/origin/master", self.head)

    def git(self, *args):
        return subprocess.check_output(
            [
                "git",
                "-C",
                str(self.repo),
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "init.templateDir=",
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                *args,
            ],
            env=fast.git_environment(),
            stderr=subprocess.DEVNULL,
            timeout=10,
        )

    def add(self, name="linked", detached=False):
        path = self.base / name
        self.git(
            "worktree",
            "add",
            *(["--detach"] if detached else ["-b", "b" + str(len(name))]),
            str(path),
            self.head,
        )
        return path

    def snapshot(self):
        # Tests alone traverse their own fixture to detect writes by inventory.
        return {
            os.fsencode(p.relative_to(self.base)): (
                p.stat().st_mtime_ns,
                p.stat().st_mode,
                hashlib.sha256(p.read_bytes()).hexdigest(),
            )
            for p in self.base.rglob("*")
            if p.is_file() and not p.is_symlink()
        }


class ParserTests(unittest.TestCase):
    def test_normal_registry_and_refs(self):
        self.assertEqual(fast.parse_registry(registry_row())[0]["head"], HEAD.decode())
        self.assertEqual(
            fast.parse_refs(refs_row())["refs/heads/master"]["head"], HEAD.decode()
        )

    def test_unusual_and_non_utf8_path_bytes(self):
        path = b'/synthetic/ space\tline\nquote"slash\\-\xff '
        row = fast.parse_registry(registry_row(path))[0]
        self.assertEqual(os.fsencode(row["path"]), path)
        self.assertEqual(base64.b64decode(row["path_bytes_base64"]), path)
        self.assertEqual(json.loads(json.dumps(row, ensure_ascii=True)), row)

    def test_detached_locked_prunable(self):
        row = fast.parse_registry(
            registry_row(
                branch=None, extra=b"locked private\nreason\0prunable private\0"
            )
        )[0]
        self.assertTrue(row["locked"] and row["prunable"] and row["detached"])
        self.assertIsNone(row["branch_ref"])
        self.assertNotIn("private", json.dumps(row))

    def test_bare_registration(self):
        self.assertTrue(
            fast.parse_registry(b"worktree /synthetic/bare\0bare\0\0")[0]["bare"]
        )

    def test_malformed_registry_fails_closed(self):
        for raw in (
            b"",
            registry_row()[:-1],
            registry_row() + b"x",
            registry_row(extra=b"unexpected x\0"),
            registry_row(extra=b"HEAD " + HEAD + b"\0"),
            registry_row(head=b"bad"),
            registry_row(branch=b"refs/heads/bad..ref"),
            registry_row(extra=b"detached\0"),
            registry_row(path=b"relative"),
            registry_row() * 2,
            b"worktree /x\0HEAD " + HEAD + b"\0\0",
        ):
            with self.subTest(raw=raw), self.assertRaises(fast.ObservationError):
                fast.parse_registry(raw)

    def test_malformed_refs_fail_closed(self):
        for raw in (
            b"malformed",
            refs_row()[:-1],
            refs_row(head=b"bad"),
            refs_row(head=b"0" * 40),
            refs_row(name=b"refs/heads/a\nb"),
            refs_row(name=b"refs/heads/.hidden"),
            refs_row(name=b"refs/heads/a.lock"),
            refs_row(name=b"refs/heads/a@{b"),
            refs_row() * 2,
            refs_row(target=b"refs/heads/missing"),
        ):
            with self.subTest(raw=raw), self.assertRaises(fast.ObservationError):
                fast.parse_refs(raw)

    def test_cached_symbolic_ref_and_non_utf8_ref(self):
        raw = (
            refs_row(b"refs/remotes/origin/master")
            + refs_row(
                b"refs/remotes/origin/HEAD", target=b"refs/remotes/origin/master"
            )
            + refs_row(b"refs/heads/\xff")
        )
        refs = fast.parse_refs(raw)
        self.assertEqual(
            refs["refs/remotes/origin/HEAD"]["symref"], "refs/remotes/origin/master"
        )
        self.assertIn(os.fsdecode(b"refs/heads/\xff"), refs)

    def test_sha256_object_ids(self):
        self.assertEqual(
            fast.parse_registry(registry_row(head=b"a" * 64))[0]["head"], "a" * 64
        )
        self.assertEqual(
            fast.parse_refs(refs_row(head=b"a" * 64))["refs/heads/master"]["head"],
            "a" * 64,
        )


class ObservationTests(unittest.TestCase):
    def scan(self, registry=None, refs=None, **kwargs):
        with patch.object(
            fast, "run_git", side_effect=simulated_runner(registry, refs)
        ):
            return fast.inventory("/synthetic/main", **kwargs)

    def assert_hold(self, report):
        self.assertFalse(report["safe_to_remove"])
        self.assertFalse(report["removal_approval_sufficient"])
        for row in report["worktrees"]:
            self.assertFalse(row["safe_to_remove"])
            self.assertEqual(row["lifecycle_hold"], fast.HOLD)

    def test_normal_observation_timing_and_constant_command_count(self):
        report = self.scan()
        self.assertTrue(report["complete"])
        self.assertEqual(report["subprocess_count"], 5)
        self.assertTrue(
            all(v["seconds"] >= 0 and v["error"] is None for v in report["operations"])
        )
        self.assertEqual(
            report["snapshots"]["registry_before"],
            report["snapshots"]["registry_after"],
        )
        self.assert_hold(report)

    def test_duplicate_heads_are_not_deduplicated_worktrees(self):
        report = self.scan(
            registry_row() + registry_row(b"/synthetic/other", branch=None)
        )
        self.assertEqual(report["summary"]["registered"], 2)
        self.assertEqual(report["duplicate_heads"], {HEAD.decode(): 2})
        self.assert_hold(report)

    def test_missing_or_mismatched_registered_branch(self):
        for refs in (b"", refs_row(head=b"2" * 40)):
            with self.subTest(refs=refs):
                report = self.scan(refs=refs)
                self.assertFalse(report["complete"])
                self.assertTrue(report["worktrees"][0]["observation_errors"])
                self.assertFalse(report["worktrees"][0]["observation_complete"])
                self.assertEqual(report["subprocess_count"], 5)
                self.assert_hold(report)

    def test_no_remote_refs_is_valid_and_detached_needs_no_branch(self):
        report = self.scan(registry_row(branch=None), b"")
        self.assertTrue(report["complete"])
        self.assertEqual(report["refs"], {})

    def test_unborn_head_is_incomplete(self):
        report = self.scan(registry_row(head=b"0" * 40), b"")
        self.assertFalse(report["complete"])
        self.assertIn(
            "unborn_or_missing_head", report["worktrees"][0]["observation_errors"]
        )

    def test_changed_registry_or_refs(self):
        for command in (fast.REGISTRY, fast.REFS):
            original = simulated_runner()
            calls = 0

            def changing(root, args, **kwargs):
                nonlocal calls
                raw = original(root, args, **kwargs)
                if args == command:
                    calls += 1
                    if calls == 2:
                        return (
                            registry_row(extra=b"locked\0")
                            if command == fast.REGISTRY
                            else refs_row() + refs_row(b"refs/remotes/origin/new")
                        )
                return raw

            with (
                self.subTest(command=command),
                patch.object(fast, "run_git", side_effect=changing),
            ):
                report = fast.inventory("/synthetic/main")
                self.assertFalse(report["complete"])
                self.assertIn(
                    "registry_or_refs_changed", [e["code"] for e in report["errors"]]
                )
                self.assert_hold(report)

    def test_malformed_final_refs_revoke_all_rows(self):
        original = simulated_runner()
        count = 0

        def corrupt(root, args, **kwargs):
            nonlocal count
            count += 1
            return b"bad" if count == 5 else original(root, args, **kwargs)

        with patch.object(fast, "run_git", side_effect=corrupt):
            report = fast.inventory("/synthetic/main")
        self.assertFalse(report["complete"])
        self.assertEqual(len(report["worktrees"]), 1)
        self.assert_hold(report)

    def test_timeout_is_reported_and_stops_subprocesses(self):
        with patch.object(
            fast, "run_git", side_effect=fast.ObservationError("subprocess_timeout")
        ) as run:
            report = fast.inventory("/synthetic/main")
        self.assertEqual(run.call_count, 1)
        self.assertFalse(report["complete"])
        self.assertEqual(report["operations"][0]["error"], "subprocess_timeout")
        self.assert_hold(report)

    def test_overall_deadline_and_no_later_commands(self):
        clock = [0.0]
        original = simulated_runner()

        def delayed(root, args, **kwargs):
            self.assertLessEqual(kwargs["timeout"], 0.5)
            clock[0] += 0.6
            return original(root, args, **kwargs)

        with (
            patch.object(fast.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(fast, "run_git", side_effect=delayed) as run,
        ):
            report = fast.inventory("/synthetic/main", deadline_seconds=0.5)
        self.assertEqual(run.call_count, 1)
        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["code"], "overall_deadline")

    def test_deadline_checked_during_parsing(self):
        def exhausted():
            raise fast.ObservationError("overall_deadline")

        for parser, raw in (
            (fast.parse_registry, registry_row()),
            (fast.parse_refs, refs_row()),
        ):
            with self.assertRaisesRegex(fast.ObservationError, "overall_deadline"):
                parser(raw, exhausted)

    def test_invalid_limits_rejected(self):
        for kwargs in (
            {"deadline_seconds": 0},
            {"subprocess_seconds": float("inf")},
            {"deadline_seconds": float("nan")},
            {"max_output_bytes": -1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                fast.inventory("/synthetic/main", **kwargs)

    def test_no_filesystem_traversal_or_registration_visits(self):
        with (
            patch.object(os, "scandir", side_effect=AssertionError("no scandir")),
            patch.object(os, "walk", side_effect=AssertionError("no walk")),
            patch.object(Path, "rglob", side_effect=AssertionError("no rglob")),
            patch.object(Path, "stat", side_effect=AssertionError("no path stat")),
            patch.object(Path, "open", side_effect=AssertionError("no file reads")),
        ):
            report = self.scan(registry_row(b"/nonexistent/path"))
        self.assertTrue(report["complete"])
        self.assertFalse(report["worktrees"][0]["contents_verified"])

    def test_cli_success_failure_and_no_removal_authorization(self):
        for refs, expected in ((refs_row(), 0), (b"", 1)):
            with (
                patch.object(fast, "run_git", side_effect=simulated_runner(refs=refs)),
                contextlib.redirect_stdout(io.StringIO()) as out,
            ):
                code = fast.main(["--repository", "/synthetic/main"])
            self.assertEqual(code, expected)
            self.assert_hold(json.loads(out.getvalue()))
        for args in (
            [],
            ["remove"],
            ["--repository", "/synthetic/main", "--output", "x"],
            ["--repository", "/synthetic/main", "--deadline-seconds", "nan"],
        ):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                fast.main(args)


class SyntheticGitTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.temp.cleanup)

    def test_actual_local_cached_refs_and_symbolic_remote(self):
        self.f.git(
            "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"
        )
        report = fast.inventory(self.f.repo)
        self.assertTrue(report["complete"], report["errors"])
        self.assertEqual(report["subprocess_count"], 5)
        self.assertIn("refs/remotes/origin/master", report["refs"])
        self.assertEqual(report["worktrees"][0]["head"], self.f.head.decode())

    def test_actual_detached_locked_prunable_and_duplicate_heads(self):
        locked = self.f.add("locked", detached=True)
        missing = self.f.add("missing", detached=True)
        self.f.git("worktree", "lock", "--reason", "private reason", str(locked))
        missing.rename(self.f.base / "relocated-fixture")
        report = fast.inventory(self.f.repo)
        self.assertTrue(report["complete"], report["errors"])
        rows = {r["path"]: r for r in report["worktrees"]}
        self.assertTrue(rows[str(locked)]["locked"])
        self.assertTrue(rows[str(missing)]["prunable"])
        self.assertEqual(report["duplicate_heads"], {self.f.head.decode(): 3})
        self.assertNotIn("private reason", json.dumps(report))

    def test_actual_unusual_non_utf8_worktree_path(self):
        path = self.f.add(os.fsdecode(b' space\n\tquote"slash\\-\xff '), detached=True)
        report = fast.inventory(self.f.repo)
        self.assertTrue(report["complete"], report["errors"])
        row = next(r for r in report["worktrees"] if r["detached"])
        self.assertEqual(base64.b64decode(row["path_bytes_base64"]), os.fsencode(path))
        self.assertTrue(fast.inventory(path)["complete"])

    def test_actual_registry_and_ref_changes_during_execution(self):
        for kind in ("registry", "refs"):
            original = fast.run_git
            calls = 0

            def changed(root, args, **kwargs):
                nonlocal calls
                raw = original(root, args, **kwargs)
                if args == fast.REFS:
                    calls += 1
                    if calls == 1:
                        if kind == "registry":
                            self.f.add("added-during-observation", detached=True)
                        else:
                            self.f.git(
                                "update-ref", "refs/remotes/origin/new", self.f.head
                            )
                return raw

            with (
                self.subTest(kind=kind),
                patch.object(fast, "run_git", side_effect=changed),
            ):
                report = fast.inventory(self.f.repo)
            self.assertFalse(report["complete"])
            self.assertIn(
                "registry_or_refs_changed", [e["code"] for e in report["errors"]]
            )
            self.assertTrue(
                all(not r["observation_complete"] for r in report["worktrees"])
            )

    def test_all_fixture_bytes_and_metadata_preserved(self):
        path = self.f.add()
        (path / "untracked").write_bytes(b"synthetic valuable bytes")
        before = self.f.snapshot()
        self.assertTrue(fast.inventory(self.f.repo)["complete"])
        self.assertEqual(before, self.f.snapshot())

    def test_actual_malformed_and_missing_ref(self):
        (self.f.repo / ".git/refs/heads/broken").write_bytes(b"not an object id\n")
        report = fast.inventory(self.f.repo)
        self.assertFalse(report["complete"])
        self.assertIn("git_stderr_incomplete", [e["code"] for e in report["errors"]])
        (
            self.f.repo / ".git/refs/heads/broken"
        ).unlink()  # Own fabricated corrupt fixture.
        (self.f.repo / ".git/refs/heads/master").unlink()
        self.assertFalse(fast.inventory(self.f.repo)["complete"])

    def test_subdirectory_cannot_silently_select_ancestor_repository(self):
        subdir = self.f.repo / "child"
        subdir.mkdir()
        report = fast.inventory(subdir)
        self.assertFalse(report["complete"])
        self.assertEqual(report["subprocess_count"], 1)

    def test_only_allowlisted_commands_no_status_or_mutation(self):
        original = fast.subprocess.Popen
        commands = []

        def record(command, **kwargs):
            commands.append(command)
            self.assertEqual(command[command.index("-C") + 1], str(self.f.repo))
            self.assertIn(tuple(command[command.index("-C") + 2 :]), fast.ALLOWED)
            return original(command, **kwargs)

        with (
            patch.object(fast.subprocess, "Popen", side_effect=record),
            patch.object(os, "scandir", side_effect=AssertionError("no traversal")),
        ):
            self.assertTrue(fast.inventory(self.f.repo)["complete"])
        self.assertEqual(len(commands), 5)
        with self.assertRaises(fast.ObservationError):
            fast.run_git(str(self.f.repo), ("status",), timeout=1, max_bytes=100)

    def test_inherited_git_environment_and_hooks_are_disabled(self):
        marker = self.f.base / "hook-executed"
        hook = self.f.base / "hook.sh"
        hook.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        hook.chmod(0o700)
        self.f.git("config", "core.fsmonitor", str(hook))
        self.f.git("config", "filter.test.process", str(hook))
        with patch.dict(
            os.environ,
            {
                "GIT_DIR": "/nonexistent",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.fsmonitor",
                "GIT_CONFIG_VALUE_0": str(hook),
            },
        ):
            self.assertTrue(fast.inventory(self.f.repo)["complete"])
        self.assertFalse(marker.exists())


class SubprocessTests(unittest.TestCase):
    def python_child(self, program):
        original = subprocess.Popen

        def launch(command, **kwargs):
            return original([sys.executable, "-c", program], **kwargs)

        return patch.object(fast.subprocess, "Popen", side_effect=launch)

    def test_real_timeout_kills_and_reaps_child(self):
        tick = time.monotonic()
        with (
            self.python_child("import time; time.sleep(10)"),
            self.assertRaisesRegex(fast.ObservationError, "subprocess_timeout"),
        ):
            fast.run_git("/synthetic", fast.REGISTRY, timeout=0.05, max_bytes=1024)
        self.assertLess(time.monotonic() - tick, 1.0)

    def test_real_overall_deadline_limits_child_timeout(self):
        tick = time.monotonic()
        with self.python_child("import time; time.sleep(10)"):
            report = fast.inventory(
                "/synthetic", subprocess_seconds=5, deadline_seconds=0.05
            )
        self.assertLess(time.monotonic() - tick, 1.0)
        self.assertFalse(report["complete"])
        self.assertEqual(report["subprocess_count"], 1)

    def test_output_limit_retains_fail_closed_report(self):
        with self.python_child("import os; os.write(1, b'x' * 10000)"):
            report = fast.inventory("/synthetic", max_output_bytes=32)
        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["code"], "subprocess_output_limit")

    def test_output_limit_applies_to_stdout_and_stderr(self):
        for fd in (1, 2):
            with (
                self.subTest(fd=fd),
                self.python_child(f"import os; os.write({fd}, b'x' * 10000)"),
                self.assertRaisesRegex(
                    fast.ObservationError, "subprocess_output_limit"
                ),
            ):
                fast.run_git("/synthetic", fast.REFS, timeout=2, max_bytes=32)

    def test_stderr_and_nonzero_are_sanitized(self):
        for program, code in (
            ("import sys; sys.stderr.write('SECRET')", "git_stderr_incomplete"),
            ("import sys; sys.exit(2)", "git_nonzero_exit"),
        ):
            with (
                self.python_child(program),
                self.assertRaisesRegex(fast.ObservationError, code) as raised,
            ):
                fast.run_git("/synthetic", fast.REFS, timeout=2, max_bytes=1024)
            self.assertNotIn("SECRET", str(raised.exception))

    def test_launch_os_error_is_fail_closed(self):
        with patch.object(fast.subprocess, "Popen", side_effect=OSError("SECRET")):
            report = fast.inventory("/synthetic")
        self.assertFalse(report["complete"])
        self.assertEqual(report["errors"][0]["code"], "subprocess_os_error")


def benchmark():
    """Serial, tiny fixtures; simulated rows never construct checkout trees."""
    results = []
    for count, simulated in (
        (1, False),
        (10, False),
        (30, False),
        (100, True),
        (200, True),
    ):
        f = None
        try:
            if simulated:
                root = "/synthetic/main"
                raw = b"".join(
                    registry_row(f"/synthetic/w{i}".encode(), branch=None)
                    for i in range(count)
                )
                context = lambda: patch.object(
                    fast, "run_git", side_effect=simulated_runner(raw, b"", root)
                )
            else:
                f = Fixture()
                for i in range(count - 1):
                    f.add(f"w{i}", detached=True)
                root = f.repo
                context = contextlib.nullcontext
            samples = []
            for _ in range(3):
                with (
                    context(),
                    patch.object(
                        fast.subprocess, "Popen", wraps=subprocess.Popen
                    ) as spawned,
                ):
                    tracemalloc.start()
                    tick = time.perf_counter()
                    report = fast.inventory(root)
                    wall = time.perf_counter() - tick
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                if not report["complete"] or report["summary"]["registered"] != count:
                    raise RuntimeError("benchmark observation incomplete")
                samples.append(
                    dict(
                        wall_seconds=wall,
                        subprocess_count=spawned.call_count,
                        command_attempts=report["subprocess_count"],
                        python_tracemalloc_peak_bytes=peak,
                    )
                )
            results.append(
                dict(
                    kind="simulated_registry" if simulated else "actual_synthetic_git",
                    worktrees=count,
                    samples=samples,
                    median_wall_seconds=statistics.median(
                        s["wall_seconds"] for s in samples
                    ),
                )
            )
        finally:
            if f:
                f.temp.cleanup()
    return dict(
        schema_version=1,
        generated_at=fast.datetime.now(fast.UTC).isoformat(),
        python=sys.version,
        git_version=subprocess.check_output(["git", "--version"], timeout=5)
        .decode()
        .strip(),
        measurements=results,
        methodology="Three serial samples per size. Setup/cleanup excluded. tracemalloc enabled during timed inventory.",
        resource_limitations=[
            "Python allocation peaks exclude Git child memory and kernel buffers; they are not total RSS.",
            "Simulated rows measure parsing/consistency/serialization preparation with no Git child processes or checkouts.",
            "Final JSON serialization and stdout capture are excluded; machine/filesystem/cache affect wall times.",
            "No production worktrees inspected; these measurements do not predict 110-worktree runtime precisely.",
        ],
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--benchmark"]:
        print(json.dumps(benchmark(), indent=2, sort_keys=True))
    else:
        unittest.main()
