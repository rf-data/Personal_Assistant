"""Explicit offline C21 acceptance profile. New private output directory only.

Run with the existing backend interpreter; supply the existing UI interpreter and
merged checkout. Loopback HTTP sockets must be permitted for the TCP scenario.
No dependency installation, productive data, downloads or automatic deployments.
"""

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_TESTS = (
    "test_workflow_http",
    "test_pdf_job_control",
    "test_pdf_workflows",
    "test_job_control",
    "test_job_executor",
    "test_cs50_workflows",
    "test_cs50_material_pdf",
    "test_cs50_material_pdf_v2",
    "test_cs50_visual_inventory",
    "test_cs50_material_quality",
    "test_cs50_material_processing",
    "test_pipeline_metrics",
    "test_monitoring_config",
    "test_math_formula_evaluation",
    "test_cs50_lecture_adapter",
    "test_cs50_material_html_semantics",
    "test_c21_acceptance",
)

SYMPY_PREFLIGHT = """import importlib.util
import json
import time
started = time.process_time()
available = importlib.util.find_spec("sympy") is not None
version = None
if available:
    import sympy
    version = sympy.__version__
print(json.dumps(dict(available=available, version=version,
                      import_cpu_seconds=round(time.process_time()-started, 3))))
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode()


def junit_records(path):
    records = []
    for node in ET.parse(path).iter("testcase"):
        status = (
            "failed"
            if node.find("failure") is not None or node.find("error") is not None
            else "skipped"
            if node.find("skipped") is not None
            else "passed"
        )
        records.append(
            dict(
                test=node.get("classname", "") + "." + node.get("name", ""),
                status=status,
            )
        )
    return records


def git_identity(path):
    values = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD", "HEAD^{tree}"], text=True
    ).splitlines()
    return dict(commit=values[0], tree=values[1])


def lifecycle_metric_check(samples):
    """Observe positive lifecycle series; never sum different test stores/runs."""
    observed = dict(
        started=0,
        running=0,
        success=0,
        failure=0,
        cancelled=0,
        timeout=0,
        duration_count=0,
    )
    valid = bool(samples) and all(s["status"] == "passed" for s in samples)
    for sample in samples:
        for line in sample.get("text", "").splitlines():
            if line.startswith("#"):
                continue
            match = re.fullmatch(r"(\w+)\{(.*)\} (\S+)", line)
            if match is None:
                valid = False
                continue
            name, labels, value = match.groups()
            labels = dict(re.findall(r'(\w+)="([^"]*)"', labels))
            if set(labels) - {"process", "worker_pool", "outcome", "le", "error_class"}:
                valid = False
            if labels.get("process") != "cs50_offline_workflow":
                continue
            key = {
                "personal_assistant_jobs_started_total": "started",
                "personal_assistant_jobs_running": "running",
                "personal_assistant_job_duration_seconds_count": "duration_count",
            }.get(name)
            if name == "personal_assistant_jobs_completed_total":
                key = labels.get("outcome")
            if (
                name == "personal_assistant_jobs_failed_total"
                and labels.get("error_class") == "timeout"
            ):
                key = "timeout"
            if key in observed:
                observed[key] = max(observed[key], float(value))
    return dict(
        requirement="c15_actual_ui_lifecycle_metrics",
        status="passed"
        if valid and all(v > 0 for v in observed.values())
        else "failed",
        observations=observed,
        aggregation="maximum observed per series across separate synthetic stores, not a cumulative total",
        identity_labels=False if valid else "invalid labels or sample",
    )


def run_step(name, command, cwd, output, env, *, timeout=900):
    started = time.monotonic()
    log = output / (name + ".log")
    with log.open("xb") as stream:
        try:
            child = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            stream.write(
                (
                    "Test process could not start: " + type(error).__name__ + "\n"
                ).encode()
            )
            code = 127
        else:
            try:
                code = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Only the new session created above, never persisted PIDs.
                for sig, wait in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
                    try:
                        os.killpg(child.pid, sig)
                    except ProcessLookupError:
                        pass
                    try:
                        child.wait(timeout=wait)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                code = 124
    return dict(
        requirement=name,
        status="passed" if code == 0 else "failed",
        exit_code=code,
        seconds=round(time.monotonic() - started, 3),
        log=log.name,
        log_sha256=sha(log.read_bytes()),
    )


def publish(output, report):
    data = json_bytes(report)
    with (output / "report.json").open("xb") as stream:
        stream.write(data)
    rows = [
        "# C21 acceptance",
        "",
        "Synthetic technical evidence; no browser or semantic quality claim.",
        "",
        "| Requirement | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    rows += [
        f"| {c['requirement']} | {c['status']} | {c.get('log', c.get('reason', 'report.json'))} |"
        for c in report["checks"]
    ]
    markdown = ("\n".join(rows) + "\n").encode()
    with (output / "summary.md").open("xb") as stream:
        stream.write(markdown)
    manifest = {
        p.name: sha(p.read_bytes())
        for p in output.iterdir()
        if p.is_file() and p.name != "manifest.json"
    }
    with (output / "manifest.json").open("xb") as stream:
        stream.write(json_bytes(dict(schema_version=1, sha256=manifest)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui-repo", required=True, type=Path)
    parser.add_argument("--ui-python", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--temp-parent",
        type=Path,
        help="Explicit writable scratch parent; e.g. preflighted tmpfs",
    )
    parser.add_argument("--profile", choices=("tcp", "full"), default="full")
    args = parser.parse_args(argv)
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        parser.error("Output already exists; no work was started")
    output = output.resolve()
    if output.is_relative_to(ROOT) or ROOT.is_relative_to(output):
        parser.error("Acceptance output must be external to the backend checkout")
    ui = args.ui_repo.resolve()
    if output.is_relative_to(ui) or ui.is_relative_to(output):
        parser.error("Acceptance output must be external to the UI checkout")
    identities = dict(backend=git_identity(ROOT), ui=git_identity(ui))
    output.mkdir(mode=0o700)
    checks = []
    report = dict(
        schema_version=1,
        profile=args.profile,
        source_origin="synthetic",
        repositories=identities,
        checks=checks,
    )
    with tempfile.TemporaryDirectory(
        prefix="c21-profile-", dir=args.temp_parent
    ) as scratch:
        env = {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": scratch,
            "C16_REPO": str(ROOT),
            "C16_PYTHON": sys.executable,
        }
        if args.profile == "full":
            # Normal import primes standard installed bytecode caches. The C11
            # worker's unchanged 2-s CPU budget includes import; a cold source
            # compilation can consume it before any formula is evaluated.
            checks.append(
                run_step(
                    "optional_sympy_import_preflight",
                    [
                        sys.executable,
                        "-I",
                        "-c",
                        SYMPY_PREFLIGHT,
                    ],
                    ROOT,
                    output,
                    env,
                    timeout=60,
                )
            )
        tcp = output / "tcp.json"
        checks.append(
            run_step(
                "streamlit_real_http_processes",
                [
                    str(args.ui_python),
                    str(ROOT / "scripts/acceptance/c21_ui_tcp.py"),
                    "--ui-repo",
                    str(ui),
                    "--backend-repo",
                    str(ROOT),
                    "--backend-python",
                    sys.executable,
                    "--output",
                    str(tcp),
                ],
                ROOT,
                output,
                env,
                timeout=240,
            )
        )
        if tcp.is_file():
            checks.extend(json.loads(tcp.read_text())["checks"])
        if args.profile == "full":
            xml = output / "backend-junit.xml"
            checks.append(
                run_step(
                    "backend_regressions",
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-q",
                        *["tests/" + n + ".py" for n in BACKEND_TESTS],
                        "--basetemp",
                        scratch + "/pytest",
                        "--junitxml",
                        str(xml),
                    ],
                    ROOT,
                    output,
                    env,
                )
            )
            if xml.is_file():
                report["backend_tests"] = junit_records(xml)
            checks.append(
                run_step(
                    "ui_regressions_apptest_router",
                    [
                        str(args.ui_python),
                        str(ROOT / "scripts/acceptance/c21_unittest.py"),
                        "--ui-repo",
                        str(ui),
                        "--output",
                        str(output / "ui-tests.json"),
                    ],
                    ui,
                    output,
                    env,
                )
            )
            if (output / "ui-tests.json").is_file():
                report["ui_tests"] = json.loads((output / "ui-tests.json").read_text())
                checks.append(
                    lifecycle_metric_check(
                        report["ui_tests"].get("lifecycle_metrics", [])
                    )
                )
            checks.append(
                run_step(
                    "ruff",
                    [
                        str(Path(sys.executable).parent / "ruff"),
                        "check",
                        "--no-cache",
                        "scripts/c21_acceptance.py",
                        "scripts/acceptance",
                        "tests/test_c21_acceptance.py",
                    ],
                    ROOT,
                    output,
                    env,
                )
            )
        else:
            checks.append(
                dict(
                    requirement="regressions",
                    status="not tested",
                    reason="TCP-only profile selected",
                )
            )
    checks.extend(
        [
            dict(
                requirement="manual_browser",
                status="not tested",
                reason="No interactive browser acceptance performed; AppTest is separate",
            ),
            dict(
                requirement="real_week0_pdf",
                status="blocked",
                reason="Original slides/source PDF absent; supply explicit local original and reviewed binding",
            ),
            dict(
                requirement="real_math_gold",
                status="blocked",
                reason="No independent real document/formula gold references supplied",
            ),
            dict(
                requirement="semantic_material_review",
                status="not tested",
                reason="Human checklist in docs/acceptance/c21_review.md; no inferred quality score",
            ),
        ]
    )
    report["technical_status"] = (
        "failed" if any(c["status"] == "failed" for c in checks) else "passed"
    )
    publish(output, report)
    print(
        json.dumps(
            dict(
                technical_status=report["technical_status"],
                report=str(output / "report.json"),
            )
        )
    )
    return 1 if report["technical_status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
