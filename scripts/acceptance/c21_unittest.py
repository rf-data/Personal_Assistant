"""Run the unchanged UI suite and retain actual test and subtest outcomes."""

import argparse
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    sys.path.insert(0, str(args.ui_repo))
    records = []
    metrics = []
    from scripts.demo_job_backend import Harness

    original_close = Harness.close
    original_call = Harness.call
    backend_python = os.environ["C16_PYTHON"]
    backend_repository = os.environ["C16_REPO"]

    def observe_metrics(harness, phase):
        try:
            # Existing synthetic test workspace, before its worker is stopped.
            text = subprocess.check_output(
                [
                    backend_python,
                    "-m",
                    "scripts.acceptance.c21_server",
                    "--config",
                    str(Path(harness.ready["token_file"]).parent / "config.json"),
                    "--metrics",
                ],
                cwd=backend_repository,
                text=True,
                timeout=15,
            )
            metrics.append(dict(status="passed", phase=phase, text=text))
        except (OSError, subprocess.SubprocessError) as error:
            metrics.append(dict(status="failed", error=type(error).__name__))

    def observe_close(harness):
        try:
            observe_metrics(harness, "before_close")
        finally:
            original_close(harness)

    def observe_call(harness, value):
        response = original_call(harness, value)
        if (
            value.get("action") == "fault_status"
            and response.get("pdf_started")
            and not getattr(harness, "_c21_metrics_observed", False)
        ):
            harness._c21_metrics_observed = True
            observe_metrics(harness, "native_pdf_probe")
        return response

    class Result(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            records.append(dict(test=test.id(), status="passed"))

        def addFailure(self, test, err):
            super().addFailure(test, err)
            records.append(dict(test=test.id(), status="failed"))

        def addError(self, test, err):
            super().addError(test, err)
            records.append(dict(test=test.id(), status="failed"))

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            records.append(dict(test=test.id(), status="skipped", reason=reason))

        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            records.append(
                dict(
                    test=subtest.id(),
                    status="passed" if err is None else "failed",
                    subtest=True,
                )
            )

    suite = unittest.defaultTestLoader.discover(str(args.ui_repo / "tests"))
    with (
        patch.object(Harness, "close", observe_close),
        patch.object(Harness, "call", observe_call),
    ):
        result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(
            dict(
                schema_version=1,
                tests_run=result.testsRun,
                successful=result.wasSuccessful(),
                records=records,
                lifecycle_metrics=metrics,
            ),
            stream,
            indent=2,
        )
        stream.write("\n")
    return (
        0
        if result.wasSuccessful() and all(m["status"] == "passed" for m in metrics)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
