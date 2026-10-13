"""Run the complete offline path with installed dependencies and real module imports."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("marvin") is None,
    reason="Requires the installed lecture-worker uv environment",
)
def test_real_installed_srt_pipeline(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "TMPDIR", "LD_LIBRARY_PATH")
        if key in os.environ
    }
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(root / "tests/helpers/cs50_uv_integration_probe.py"),
            str(root),
            str(tmp_path),
        ],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "result.json").read_text())
    assert all(status == "passed" for status in report["steps"].values())
    assert report["network_attempts"] == 0
    assert report["course_id"] == "cs50_python"
    assert report["language"] == "en"
    assert report["provenance"]["transcript_source"] == "official_subtitle"
