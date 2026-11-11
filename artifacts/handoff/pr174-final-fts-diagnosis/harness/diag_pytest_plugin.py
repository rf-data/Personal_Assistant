"""Only fixed test identity, outcome and duration; never failure/source payloads."""
import json
import os
from pathlib import Path
import pytest

REPORTS = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    if call.excinfo is not None:
        # File/function/line only. No locals, source lines or arbitrary messages.
        report.diag_error = dict(
            exception_class=call.excinfo.type.__name__,
            frames=[dict(file=str(entry.path), line=entry.lineno + 1, function=entry.name)
                    for entry in call.excinfo.traceback],
            known_guard_message=str(call.excinfo.value) if str(call.excinfo.value) in {
                'Synthetic diagnosis forbids network',
                'Diagnostic attempted a forbidden PR-worktree write',
            } else None,
        )


def pytest_runtest_logreport(report):
    REPORTS.append(dict(stage=report.when, outcome=report.outcome, seconds=report.duration,
                        error=getattr(report, 'diag_error', None)))
    Path(os.environ['FTS_DIAG_TEST_REPORT']).write_text(json.dumps(REPORTS, indent=2) + '\n')
