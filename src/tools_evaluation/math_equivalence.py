"""Optional, isolated and bounded equivalence checking of parsed syntax trees."""

import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from src.model_evaluation.math_evaluation import EquivalenceResult


def check_equivalence(left, right, *, backend="none", timeout=5.0):
    if backend not in {"none", "sympy"}:
        raise ValueError("Unknown equivalence backend")
    if not 0 < timeout <= 10:
        raise ValueError("Timeout must be within (0, 10] seconds")
    if left == right:
        return EquivalenceResult(
            status="equivalent",
            backend="structural_identity",
            reason="identical_supported_notation",
        )
    if backend == "none":
        return EquivalenceResult(
            status="undetermined", backend="none", reason="symbolic_check_not_requested"
        )
    request = json.dumps(dict(left=left.payload(), right=right.payload())).encode()
    if len(request) > 65536 or os.name != "posix":
        return EquivalenceResult(
            status="undetermined",
            backend="sympy",
            reason="isolation_or_request_limit_unavailable",
        )
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).with_name("sympy_worker.py")),
                ],
                stdin=subprocess.PIPE,
                stdout=output,
                stderr=errors,
                start_new_session=True,
                env={"LANG": "C.UTF-8"},
            )
            try:
                process.communicate(request, timeout=timeout)
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
            if process.returncode or output.tell() > 32768:
                return EquivalenceResult(
                    status="undetermined",
                    backend="sympy",
                    reason="worker_resource_limit_or_failure",
                )
            output.seek(0)
            value = json.loads(output.read())
            return EquivalenceResult(backend="sympy", **value)
        except subprocess.TimeoutExpired:
            return EquivalenceResult(
                status="undetermined", backend="sympy", reason="worker_timeout"
            )
        except (OSError, ValueError, TypeError):
            return EquivalenceResult(
                status="undetermined",
                backend="sympy",
                reason="worker_unavailable_or_invalid_output",
            )
