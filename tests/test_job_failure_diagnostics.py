"""Safe evidence captures failure codes, never error text, SQL or source paths."""

import json
import sqlite3

import pytest

from src.job_control import adapter_worker
from src.job_control.diagnostics import record_failure
from src.job_control.store import Store


def test_failed_transaction_records_phase_code_and_rolls_back(tmp_path):
    store = Store(tmp_path / "private")
    directory = store.directory("synthetic_job")
    directory.mkdir()
    with pytest.raises(sqlite3.OperationalError) as raised:
        with store.connection(write=True) as db:
            db.execute("INSERT INTO worker VALUES(1,42)")
            db.execute("SELECT PRIVATE_MARKER FROM absent_table")
    record_failure(store.root, "synthetic_job", "guardian", raised.value)
    path = directory / "guardian-failure.v1.json"
    value = json.loads(path.read_bytes())
    assert value == dict(
        schema_version=1,
        component="guardian",
        category="Error",
        sqlite_code=sqlite3.SQLITE_ERROR,
        phase="body",
    )
    assert "PRIVATE_MARKER" not in path.read_text()
    assert path.stat().st_mode & 0o777 == 0o600
    with store.connection() as db:
        assert db.execute("SELECT * FROM worker").fetchall() == []
    record_failure(store.root, "synthetic_job", "guardian", RuntimeError("new failure"))
    assert json.loads(path.read_bytes()) == value


def test_adapter_exit_three_retains_safe_diagnostic_even_if_store_initialization_fails(
    tmp_path, monkeypatch
):
    store = Store(tmp_path / "private")
    directory = store.directory("synthetic_job")
    directory.mkdir()
    monkeypatch.setattr("src.job_control.guardian.arm_parent_death", lambda *_: None)
    with sqlite3.connect(":memory:") as db:
        try:
            db.execute("SELECT PRIVATE_MARKER FROM absent_table")
        except sqlite3.Error as error:
            failure = error

    def broken(*_):
        raise failure

    monkeypatch.setattr(adapter_worker, "Store", broken)
    assert (
        adapter_worker.main(
            ["--root", str(store.root), "--job-id", "synthetic_job", "--parent", "1"]
        )
        == 3
    )
    value = json.loads((directory / "adapter-failure.v1.json").read_bytes())
    assert value["sqlite_code"] == sqlite3.SQLITE_ERROR
    assert "PRIVATE_MARKER" not in json.dumps(value)


def test_diagnostic_failure_never_replaces_file_or_changes_decision(tmp_path):
    store = Store(tmp_path / "private")
    directory = store.directory("synthetic_job")
    directory.mkdir()
    target = tmp_path / "preserved"
    target.write_text("preserved")
    (directory / "adapter-failure.v1.json").symlink_to(target)
    record_failure(
        store.root, "synthetic_job", "adapter", RuntimeError("PRIVATE_MARKER")
    )
    record_failure(store.root, "../escape", "adapter", RuntimeError("PRIVATE_MARKER"))
    record_failure(
        store.root, "synthetic_job", "../escape", RuntimeError("PRIVATE_MARKER")
    )
    assert target.read_text() == "preserved"
