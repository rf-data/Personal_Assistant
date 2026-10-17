"""Offline report, evidence classification and no-overwrite acceptance checks."""

import hashlib
import json

import pytest

from scripts.c21_acceptance import (
    json_bytes,
    junit_records,
    lifecycle_metric_check,
    main,
    publish,
    run_step,
)


def test_no_overwrite_before_spawning_or_git_reads(tmp_path, monkeypatch):
    output = tmp_path / "retained"
    output.mkdir()
    sentinel = output / "important.txt"
    sentinel.write_text("preserve")

    def forbidden(*args, **kwargs):
        raise AssertionError("No process before output validation")

    monkeypatch.setattr("subprocess.Popen", forbidden)
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--ui-repo",
                str(tmp_path),
                "--ui-python",
                "/missing",
                "--output",
                str(output),
            ]
        )
    assert error.value.code == 2
    assert sentinel.read_text() == "preserve"


def test_output_symlink_is_rejected(tmp_path):
    link = tmp_path / "report"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(SystemExit):
        main(
            [
                "--ui-repo",
                str(tmp_path),
                "--ui-python",
                "/missing",
                "--output",
                str(link),
            ]
        )
    assert link.is_symlink()


def test_junit_preserves_failed_skipped_and_passed(tmp_path):
    xml = tmp_path / "junit.xml"
    xml.write_text(
        '<testsuites><testsuite><testcase classname="a" name="pass"/><testcase classname="a" name="fail"><failure/></testcase><testcase classname="a" name="error"><error/></testcase><testcase classname="a" name="skip"><skipped/></testcase></testsuite></testsuites>'
    )
    assert [r["status"] for r in junit_records(xml)] == [
        "passed",
        "failed",
        "failed",
        "skipped",
    ]


def test_deterministic_reports_hashes_and_explicit_unperformed_checks(tmp_path):
    report = dict(
        schema_version=1,
        checks=[
            dict(
                requirement="browser",
                status="not tested",
                reason="AppTest is not a browser",
            ),
            dict(
                requirement="pdf_original", status="blocked", reason="Original missing"
            ),
        ],
    )
    for name in ("first", "second"):
        target = tmp_path / name
        target.mkdir()
        publish(target, report)
        manifest = json.loads((target / "manifest.json").read_text())
        for file, expected in manifest["sha256"].items():
            assert hashlib.sha256((target / file).read_bytes()).hexdigest() == expected
        assert json.loads((target / "report.json").read_text()) == report
        assert "not tested" in (target / "summary.md").read_text()
    assert (tmp_path / "first/manifest.json").read_bytes() == (
        tmp_path / "second/manifest.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        publish(tmp_path / "first", report)


def test_nonfinite_json_rejected_and_key_order_stable():
    assert json_bytes(dict(b=2, a="Ä")) == json_bytes(dict(a="Ä", b=2))
    with pytest.raises(ValueError):
        json_bytes(dict(rate=float("nan")))


def test_missing_executable_is_reported_without_exposing_arguments(tmp_path):
    result = run_step(
        "spawn_error", ["/missing/c21-tool", "private-argument"], tmp_path, tmp_path, {}
    )
    assert result["status"] == "failed" and result["exit_code"] == 127
    log = (tmp_path / result["log"]).read_bytes()
    assert b"FileNotFoundError" in log and b"private-argument" not in log
    assert result["log_sha256"] == hashlib.sha256(log).hexdigest()


def test_metrics_require_actual_positive_outcomes_and_reject_identity_labels():
    def sample(name, **labels):
        labels = dict(process="cs50_offline_workflow", worker_pool="default", **labels)
        return (
            "personal_assistant_"
            + name
            + "{"
            + ",".join(f'{k}="{v}"' for k, v in labels.items())
            + "} 1"
        )

    rows = [
        sample("jobs_started_total"),
        sample("jobs_running"),
        sample("job_duration_seconds_count", outcome="success"),
        sample("jobs_failed_total", error_class="timeout"),
        *[
            sample("jobs_completed_total", outcome=o)
            for o in ("success", "failure", "cancelled")
        ],
    ]
    assert (
        lifecycle_metric_check([dict(status="passed", text="\n".join(rows))])["status"]
        == "passed"
    )
    assert lifecycle_metric_check([])["status"] == "failed"
    assert (
        lifecycle_metric_check([dict(status="passed", text="\n".join(rows[:-1]))])[
            "status"
        ]
        == "failed"
    )
    assert (
        lifecycle_metric_check(
            [
                dict(
                    status="passed",
                    text="\n".join(rows + [sample("jobs_running", job_id="secret")]),
                )
            ]
        )["status"]
        == "failed"
    )
