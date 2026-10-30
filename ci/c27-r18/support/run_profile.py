"""R17 CI runner; product tests and assertions remain unchanged."""
import argparse
import collections
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("PDF_PROFILE", "UI_PROFILE", "NAMESPACE_BASE", "NAMESPACE_OVERLAY"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    raw = Path(args.manifest).read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.expected_manifest_sha256:
        raise ValueError("Manifest pin mismatch")
    manifest = json.loads(raw)
    expected = manifest["profiles"][args.profile]["nodeids"]
    if len(expected) != len(set(expected)):
        raise ValueError("Duplicate selection")
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Python 3.12 required")
    cgroup = Path('/sys/fs/cgroup')
    limits = {name: (cgroup / name).read_text().strip()
              for name in ('memory.max', 'memory.swap.max', 'cpu.max', 'pids.max')}
    if (limits['memory.max'] == 'max' or int(limits['memory.max']) > 4*1024**3
            or limits['memory.swap.max'] != '0' or limits['pids.max'] == 'max'
            or int(limits['pids.max']) > 256):
        raise ValueError('Required cgroup v2 memory/swap/PID limits not enforced')
    quota, period = limits['cpu.max'].split()
    if quota == 'max' or int(quota) > 2*int(period):
        raise ValueError('Required CPU quota not enforced')
    versions = {name: importlib.metadata.version(name) for name in ("pymupdf", "pytest")}
    if versions != {"pymupdf": "1.28.2", "pytest": "9.1.1"}:
        raise ValueError("Locked runtime versions differ")
    if args.profile == "UI_PROFILE":
        versions["streamlit"] = importlib.metadata.version("streamlit")
        if versions["streamlit"] != "1.61.1":
            raise ValueError("Locked Streamlit version differs")
    results, work = Path(args.results), Path(args.work)
    results.mkdir(mode=0o755, parents=False, exist_ok=False)
    results.chmod(0o755)  # Host watchdog can inspect only this dedicated nonsecret evidence tree.
    work.mkdir(mode=0o700, parents=False, exist_ok=False)
    allowed_environment = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
    os.environ.clear()
    os.environ.update(allowed_environment)
    os.environ.update(HOME="/work/home", TMPDIR="/work/tmp", PYTHONPATH=str(Path.cwd()),
                      OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                      NUMEXPR_NUM_THREADS="1", STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
                      STREAMLIT_SERVER_HEADLESS="true", STREAMLIT_SERVER_FILE_WATCHER_TYPE="none")
    Path("/work/home").mkdir(exist_ok=True)
    Path("/work/tmp").mkdir(exist_ok=True)
    if args.profile != "UI_PROFILE":
        try:
            importlib.metadata.version("streamlit")
        except importlib.metadata.PackageNotFoundError:
            pass
        else:
            raise ValueError("Streamlit is prohibited outside UI_PROFILE")
    import pymupdf
    if args.profile == "UI_PROFILE":
        from streamlit.testing.v1 import AppTest
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path.cwd()))
    import pytest

    class Evidence:
        def __init__(self):
            self.collected = []
            self.reports = []

        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            self.collected = [item.nodeid for item in items]
            (results / "collected.json").write_text(json.dumps(self.collected, indent=2) + "\n")
            if collections.Counter(self.collected) != collections.Counter(expected):
                raise pytest.UsageError("Exact profile collection mismatch; execution blocked")

        def pytest_runtest_logreport(self, report):
            self.reports.append({"nodeid": report.nodeid, "phase": report.when,
                                 "outcome": report.outcome,
                                 "wasxfail": hasattr(report, "wasxfail")})

    plugin = Evidence()
    argv = ["-c", "pyproject.toml", "-p", "tests.offline_guard", "-p", "no:cacheprovider",
            "--basetemp", str(work / "pytest"), "--junitxml", str(results / "junit.xml"),
            "-o", "junit_family=xunit2", "--strict-markers", "--tb=short", *expected]
    if args.collect_only:
        argv.append("--collect-only")
    (results / "command.json").write_text(json.dumps({
        "runner_argv": sys.argv, "pytest_main_args": argv,
        "invocation_kind": "pytest.main with exact-selection/evidence plugin",
        "cwd": str(Path.cwd()),
        "python": platform.python_version(), "versions": versions, "cgroup_limits": limits,
        "profile": args.profile, "manifest_sha256": args.expected_manifest_sha256,
        "collect_only": args.collect_only}, indent=2) + "\n")
    started = time.monotonic()
    rc = int(pytest.main(argv, plugins=[plugin]))
    elapsed = time.monotonic() - started
    expected_counts = collections.Counter((node, phase) for node in expected
                                          for phase in ("setup", "call", "teardown"))
    actual_counts = collections.Counter((r["nodeid"], r["phase"]) for r in plugin.reports)
    junit_exists = (results / "junit.xml").is_file()
    junit_cases = []
    if junit_exists:
        junit_cases = list(ET.parse(results / "junit.xml").getroot().iter("testcase"))
    junit_ok = (junit_exists and len(junit_cases) == len(expected)
                and not any(list(case) for case in junit_cases))
    passed = (not args.collect_only and rc == 0 and junit_ok and expected_counts == actual_counts
              and all(r["outcome"] == "passed" and not r["wasxfail"] for r in plugin.reports))
    collection_ok = collections.Counter(plugin.collected) == collections.Counter(expected)
    state = ("COLLECTION_VERIFIED" if args.collect_only and collection_ok and rc == 0
             else "PASSED" if passed else "FAILED_OR_INCOMPLETE")
    (results / "outcomes.json").write_text(json.dumps({"status": state, "pytest_exit_code": rc,
        "expected": len(expected), "collected": len(plugin.collected),
        "actual_call_count": sum(r["phase"] == "call" for r in plugin.reports),
        "passed_call_count": sum(r["phase"] == "call" and r["outcome"] == "passed" and not r["wasxfail"] for r in plugin.reports),
        "junit_case_count": len(junit_cases), "junit_verified": junit_ok,
        "elapsed_seconds": elapsed,
        "cgroup": {name: (Path("/sys/fs/cgroup") / name).read_text()
                   for name in ("memory.peak", "memory.events", "cpu.stat", "pids.peak")
                   if (Path("/sys/fs/cgroup") / name).is_file()},
        "reports": plugin.reports}, indent=2) + "\n")
    (results / "report.md").write_text(
        f"# {args.profile}\n\nStatus: {state}\n\nExpected: {len(expected)}; "
        f"collected: {len(plugin.collected)}; actual call reports: {sum(r['phase'] == 'call' for r in plugin.reports)}; pytest exit: {rc}; elapsed: {elapsed:.3f}s.\n\n"
        "See junit.xml, the externally captured sibling .log, command.json and outcomes.json.\n")
    return 0 if passed or (args.collect_only and collection_ok and rc == 0) else (rc or 1)


if __name__ == "__main__":
    sys.exit(main())
