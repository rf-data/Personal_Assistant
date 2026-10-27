"""Real SQLite setup contention, transaction boundaries and durable quarantine."""

import sqlite3

import pytest

from src.job_control.store import Store


@pytest.mark.parametrize("write", [False, True])
def test_transient_setup_busy_reopens_before_entering_transaction(
    tmp_path, monkeypatch, write
):
    store = Store(tmp_path / "private")
    connect = sqlite3.connect
    holder = connect(store.path)
    holder.execute("PRAGMA locking_mode=EXCLUSIVE")
    holder.execute("BEGIN EXCLUSIVE")
    holder.execute("SELECT * FROM worker").fetchall()
    busy = []
    connections = []

    class ObservedConnection(sqlite3.Connection):
        failed_setup = False

        def execute(self, sql, *args):
            try:
                return super().execute(sql, *args)
            except sqlite3.OperationalError as error:
                assert sql == "PRAGMA synchronous=FULL"
                assert error.sqlite_errorcode == sqlite3.SQLITE_BUSY
                self.failed_setup = True
                busy.append(error.sqlite_errorcode)
                raise

        def close(self):
            super().close()
            if self.failed_setup:
                # Event boundary: release only after the real setup failure and
                # closure of its connection. No timing-dependent sleeps/threads.
                holder.rollback()
                holder.close()

    def observed(*args, **kwargs):
        kwargs.update(timeout=0, factory=ObservedConnection)
        db = connect(*args, **kwargs)
        connections.append(db)
        return db

    monkeypatch.setattr(sqlite3, "connect", observed)
    entered = 0
    try:
        with store.connection(write=write) as db:
            entered += 1
            assert db.execute("PRAGMA synchronous").fetchone() == (2,)
            assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
            db.execute("INSERT INTO worker VALUES(1,42)")
    finally:
        holder.close()
    assert busy == [sqlite3.SQLITE_BUSY]
    assert len(connections) == 2 and entered == 1
    with connect(store.path) as db:
        assert db.execute("SELECT heartbeat FROM worker").fetchall() == [(42,)]


def test_transaction_body_is_never_replayed(tmp_path):
    store = Store(tmp_path / "private")
    entered = 0
    with pytest.raises(sqlite3.OperationalError, match="body failure"):
        with store.connection(write=True) as db:
            entered += 1
            db.execute("INSERT INTO worker VALUES(1,42)")
            raise sqlite3.OperationalError("body failure")
    assert entered == 1
    with store.connection() as db:
        assert db.execute("SELECT * FROM worker").fetchall() == []


def test_persistent_exclusive_lock_still_fails_closed(tmp_path):
    store = Store(tmp_path / "private")
    with sqlite3.connect(store.path) as holder:
        holder.execute("PRAGMA locking_mode=EXCLUSIVE")
        holder.execute("BEGIN EXCLUSIVE")
        holder.execute("SELECT * FROM worker").fetchall()
        with pytest.raises(sqlite3.OperationalError) as raised:
            with store.connection():
                pytest.fail("A persistently locked database was admitted")
        assert raised.value.sqlite_errorcode == sqlite3.SQLITE_BUSY
    holder.close()


def test_non_busy_setup_error_is_not_retried(tmp_path, monkeypatch):
    store = Store(tmp_path / "private")
    connect = sqlite3.connect
    closed = []
    opened = []

    class BrokenConnection(sqlite3.Connection):
        def execute(self, sql, *args):
            if sql == "PRAGMA synchronous=FULL":
                return super().execute("SELECT FROM invalid syntax")
            return super().execute(sql, *args)

        def close(self):
            closed.append(self)
            super().close()

    def broken(*args, **kwargs):
        db = connect(*args, **kwargs, factory=BrokenConnection)
        opened.append(db)
        return db

    monkeypatch.setattr(sqlite3, "connect", broken)
    with pytest.raises(sqlite3.OperationalError) as raised:
        with store.connection():
            pytest.fail("Invalid connection was admitted")
    assert raised.value.sqlite_errorcode == sqlite3.SQLITE_ERROR
    assert opened == closed and len(opened) == 1


def test_transient_begin_busy_reopens_only_before_any_transaction_body(
    tmp_path, monkeypatch
):
    store = Store(tmp_path / "private")
    connect = sqlite3.connect
    holder = connect(store.path)
    opened, busy, closed = [], [], []

    class ObservedConnection(sqlite3.Connection):
        failed_begin = False

        def execute(self, sql, *args):
            if sql == "BEGIN IMMEDIATE" and not busy:
                # Acquire the real WAL writer only after this connection's
                # PRAGMA setup. The injected zero busy-handler wait exposes
                # SQLITE_BUSY immediately, as WAL recovery may do in practice.
                holder.execute("BEGIN IMMEDIATE")
            try:
                return super().execute(sql, *args)
            except sqlite3.OperationalError as error:
                assert sql == "BEGIN IMMEDIATE"
                assert error.sqlite_errorcode == sqlite3.SQLITE_BUSY
                assert not self.in_transaction
                self.failed_begin = True
                busy.append(error.sqlite_errorcode)
                raise

        def close(self):
            super().close()
            closed.append(self)
            if self.failed_begin:
                holder.rollback()

    def observed(*args, **kwargs):
        kwargs.update(timeout=0, factory=ObservedConnection)
        db = connect(*args, **kwargs)
        opened.append(db)
        return db

    monkeypatch.setattr(sqlite3, "connect", observed)
    entered = 0
    try:
        with store.connection(write=True) as db:
            entered += 1
            db.execute("INSERT INTO worker VALUES(1,42)")
    finally:
        holder.close()
    assert entered == 1 and busy == [sqlite3.SQLITE_BUSY]
    assert len(opened) == 2 and opened == closed
    with connect(store.path) as db:
        assert db.execute("SELECT heartbeat FROM worker").fetchone() == (42,)


def test_persistent_reserved_writer_is_not_retried_after_setup_budget(tmp_path):
    store = Store(tmp_path / "private")
    holder = sqlite3.connect(store.path)
    try:
        holder.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.OperationalError) as raised:
            with store.connection(write=True):
                pytest.fail("Persistently busy writer entered a transaction body")
        assert raised.value.sqlite_errorcode == sqlite3.SQLITE_BUSY
        assert raised.value.job_db_phase == "begin"
        assert holder.in_transaction
    finally:
        holder.rollback()
        holder.close()


def test_commit_failure_rolls_back_without_replaying_body_or_commit(
    tmp_path, monkeypatch
):
    store = Store(tmp_path / "private")
    connect = sqlite3.connect
    opened = []

    def observed(*args, **kwargs):
        db = connect(*args, **kwargs)
        opened.append(db)
        return db

    monkeypatch.setattr(sqlite3, "connect", observed)
    entered = 0
    with pytest.raises(sqlite3.IntegrityError) as raised:
        with store.connection(write=True) as db:
            entered += 1
            db.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
            db.execute(
                "CREATE TABLE child(parent_id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED)"
            )
            db.execute("INSERT INTO child VALUES(42)")
    assert raised.value.job_db_phase == "commit"
    assert entered == 1 and len(opened) == 1
    with store.connection() as db:
        assert (
            db.execute(
                "SELECT name FROM sqlite_master WHERE name IN ('parent','child')"
            ).fetchall()
            == []
        )
