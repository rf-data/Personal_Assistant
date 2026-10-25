"""Fresh-process probes preserve parent identities, umask and test state."""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.job_control.operations import inventory

ROOT = Path(__file__).resolve().parents[1]


def test_pdf_pid_marker_is_invisible_until_json_is_complete(tmp_path):
    result = child(
        """
import json, os, runpy, sys, time
from pathlib import Path
probe = Path(sys.argv[1]) / 'tests/helpers/pdf_lifecycle_probe.py'
directory = Path(sys.argv[2])
marker = directory / 'pdf-pid.json'
namespace = runpy.run_path(str(probe))
original = Path.open
observed = []
def observe_open(path, *args, **kwargs):
    stream = original(path, *args, **kwargs)
    mode = args[0] if args else kwargs.get('mode', 'r')
    if 'w' in mode and path.parent == directory:
        observed.append(path)
        if marker.exists():
            stream.close()
            raise AssertionError('PID marker visible before JSON is complete')
    return stream
class Finished(Exception):
    pass
def stop_before_native_parser(seconds):
    raise Finished
Path.open = observe_open
time.sleep = stop_before_native_parser
sys.argv = [str(probe), 'pdf', str(directory), 'unused-native-parser']
try:
    namespace['main']()
except Finished:
    pass
assert len(observed) == 1
assert json.loads(marker.read_text()) == dict(
    pid=os.getpid(), group=os.getpgrp(), parent=os.getppid())
assert list(directory.iterdir()) == [marker]
""",
        tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def child(code, *args):
    return subprocess.run(
        [sys.executable, "-I", "-c", code, str(ROOT), *map(str, args)],
        cwd=ROOT,
        env={
            "PATH": os.defpath,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        capture_output=True,
        text=True,
        timeout=90,
    )


@pytest.mark.parametrize("mask", [0o022, 0o077])
def test_public_root_rejected_under_either_umask(mask):
    result = child(
        """
import os, sys, pytest
sys.path.insert(0, sys.argv[1])
os.umask(int(sys.argv[2]))
raise SystemExit(pytest.main(['-q', '-o', 'addopts=', '-p', 'no:cacheprovider',
 'tests/test_content_store_artifacts.py::test_private_explicit_root_and_limits']))
""",
        mask,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("stage", ["setup", "body"])
def test_umask_restored_after_dependent_fixture_setup_error(tmp_path, stage):
    sample = tmp_path / "test_fixture_failure.py"
    failure = (
        """
import os, pytest
@pytest.fixture
def broken(private_umask):
    assert os.umask(0o077) == 0o077
    raise RuntimeError('deliberate dependent setup failure')
def test_setup_failure(broken):
    pass
"""
        if stage == "setup"
        else """
import os
def test_cli_style_mutation():
    os.umask(0o077)
    raise RuntimeError('deliberate CLI-style failure')
"""
    )
    sample.write_text(
        failure
        + """
def test_next_test_sees_original_mask():
    previous = os.umask(0o022)
    os.umask(previous)
    assert previous == 0o022
"""
    )
    report = tmp_path / "result.xml"
    result = child(
        """
import os, sys, pytest
sys.path.insert(0, sys.argv[1]); os.umask(0o022)
raise SystemExit(pytest.main(['-q', '-o', 'addopts=', '-p', 'no:cacheprovider',
 '-p', 'tests.conftest', sys.argv[2], '--junitxml=' + sys.argv[3]]))
""",
        sample,
        report,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    suite = ET.parse(report).getroot().find("testsuite")
    assert suite.attrib["errors"] == ("1" if stage == "setup" else "0")
    assert suite.attrib["failures"] == ("0" if stage == "setup" else "1")
    assert suite.attrib["tests"] == "2"
    assert "deliberate" in result.stdout


@pytest.mark.parametrize("reverse", [False, True])
def test_model_identity_survives_fixture_teardown(reverse):
    producers = [
        "tests/test_cs50_executor.py::test_all_100_tasks",
        "tests/test_cs50_lecture_adapter.py::test_real_courses_bindings_and_resource_index[0-12]",
        "tests/test_cs50_knowledge_input.py::test_all_50_contracts_without_processing",
        "tests/test_cs50_knowledge_pilot.py::test_fake_llm_response_and_request_contract",
    ]
    consumers = [
        "tests/test_cs50_material_evaluation.py::test_srt_cue_text_and_known_locator",
        "tests/test_dev03_parsing.py::test_existing_evaluator_recipe_frozen_inputs_and_report_hashes",
        "tests/test_transcript_unknown_time.py::test_unknown_locator_compatible_but_not_srt_binding",
    ]
    nodes = list(reversed(consumers + producers)) if reverse else producers + consumers
    result = child(
        """
import sys, pytest
sys.path.insert(0, sys.argv[1])
raise SystemExit(pytest.main(['-q', '-o', 'addopts=', '-p', 'no:cacheprovider',
 '-p', 'tests.offline_guard', *sys.argv[2:]]))
""",
        *nodes,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_hard_kill_during_publication_keeps_backup_fail_closed(tmp_path):
    target = tmp_path / "receipt.v1.json"
    result = child(
        """
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1]); os.umask(0o077)
from src.tools_materials import storage
storage.sync_directory = lambda path: os._exit(73)
storage.publish_bytes(Path(sys.argv[2]), b'synthetic receipt')
""",
        target,
    )
    assert result.returncode == 73, result.stderr
    (alias,) = tmp_path.glob(".material-*")
    for path in (alias, target):
        meta = path.stat()
        assert meta.st_uid == os.getuid() and meta.st_mode & 0o777 == 0o600
        assert meta.st_nlink == 2 and meta.st_ino == target.stat().st_ino
        assert path.read_bytes() == b"synthetic receipt"
    with pytest.raises(ValueError, match="Only unlinked regular files"):
        inventory(tmp_path)
    assert alias.exists() and target.exists()  # No implicit recovery or deletion.


def test_sync_exception_cleans_temporary_alias_without_replacing(tmp_path, monkeypatch):
    from src.tools_materials import storage

    def fail(path):
        raise OSError("synthetic directory sync failure")

    target = tmp_path / "receipt.v1.json"
    monkeypatch.setattr(storage, "sync_directory", fail)
    with pytest.raises(OSError, match="directory sync"):
        storage.publish_bytes(target, b"original")
    assert target.read_bytes() == b"original" and target.stat().st_nlink == 1
    assert not list(tmp_path.glob(".material-*"))
    with pytest.raises(FileExistsError):
        storage.publish_bytes(target, b"replacement")
    assert target.read_bytes() == b"original"
