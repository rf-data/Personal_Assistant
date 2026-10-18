"""Source-local FTS5 backend. No ContentStore writes, embeddings or SDKs."""

import sqlite3
import time
from functools import lru_cache

from src.content_store.errors import IntegrityError, Unavailable
from src.content_store.models import canonical

APP_ID = 0x43323446
VERSION = 1
DDL = (
    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE records (rowid INTEGER PRIMARY KEY, record_id TEXT NOT NULL UNIQUE, parsed_version_id TEXT NOT NULL, content_type TEXT NOT NULL, body TEXT NOT NULL, text TEXT NOT NULL)",
    "CREATE VIRTUAL TABLE fts USING fts5(text, tokenize='unicode61 remove_diacritics 0')",
)


@lru_cache(maxsize=1)
def expected_schema():
    try:
        with sqlite3.connect(":memory:") as db:
            for ddl in DDL:
                db.execute(ddl)
            if not hasattr(db, "serialize") or not hasattr(db, "deserialize"):
                raise Unavailable("SQLite snapshot API required")
            return dict(
                db.execute(
                    "SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"
                )
            )
    except sqlite3.Error:
        raise Unavailable("SQLite FTS5 unavailable") from None


def backend_spec():
    expected_schema()
    return dict(
        name="sqlite_fts5_v1",
        sqlite_version=sqlite3.sqlite_version,
        tokenizer="unicode61 remove_diacritics 0",
        score="sqlite_fts5_bm25_v1",
        ranking="source_rrf_v1",
    )


def _check(db, records):
    if (
        db.execute("PRAGMA application_id").fetchone()[0] != APP_ID
        or db.execute("PRAGMA user_version").fetchone()[0] != VERSION
        or dict(
            db.execute(
                "SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"
            )
        )
        != expected_schema()
        or db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
    ):
        raise IntegrityError("index database schema/integrity")
    if dict(db.execute("SELECT key,value FROM metadata")) != backend_spec():
        raise IntegrityError("index backend configuration")
    ordered = sorted(
        records,
        key=lambda r: (
            r.body.parsed_version_id,
            r.body.block_order,
            r.body.start,
            r.index_record_id,
        ),
    )
    if db.execute("SELECT count(*) FROM records").fetchone()[0] != len(ordered):
        raise IntegrityError("index completeness")
    for row, record in zip(
        db.execute(
            "SELECT rowid,record_id,parsed_version_id,content_type,body,text FROM records ORDER BY rowid"
        ),
        ordered,
        strict=True,
    ):
        b = record.body
        if row != (
            row[0],
            record.index_record_id,
            b.parsed_version_id,
            b.content_type,
            canonical(b.model_dump(mode="json")).decode(),
            b.search_text,
        ):
            raise IntegrityError("index record/projection mismatch")
    if (
        db.execute("SELECT rowid,text FROM fts ORDER BY rowid").fetchall()
        != db.execute("SELECT rowid,text FROM records ORDER BY rowid").fetchall()
    ):
        raise IntegrityError("FTS and records disagree")
    db.execute("INSERT INTO fts(fts,rank) VALUES('integrity-check',1)")


def build_database(records, *, deadline=None):
    expected_schema()
    deadline = time.monotonic() + 900 if deadline is None else deadline
    try:
        with sqlite3.connect(":memory:") as db:
            db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            db.execute(f"PRAGMA application_id={APP_ID}")
            db.execute(f"PRAGMA user_version={VERSION}")
            for ddl in DDL:
                db.execute(ddl)
            db.executemany(
                "INSERT INTO metadata VALUES (?,?)", sorted(backend_spec().items())
            )
            ordered = sorted(
                records,
                key=lambda r: (
                    r.body.parsed_version_id,
                    r.body.block_order,
                    r.body.start,
                    r.index_record_id,
                ),
            )
            for i, r in enumerate(ordered, 1):
                if time.monotonic() > deadline:
                    raise Unavailable("index build deadline")
                b = r.body
                db.execute(
                    "INSERT INTO records VALUES (?,?,?,?,?,?)",
                    (
                        i,
                        r.index_record_id,
                        b.parsed_version_id,
                        b.content_type,
                        canonical(b.model_dump(mode="json")).decode(),
                        b.search_text,
                    ),
                )
                db.execute(
                    "INSERT INTO fts(rowid,text) VALUES (?,?)", (i, b.search_text)
                )
            _check(db, ordered)
            db.commit()
            data = db.serialize()
            if len(data) > 64 * 1024**2:
                raise Unavailable("source index byte limit")
            return data
    except sqlite3.Error:
        raise Unavailable("FTS build unavailable") from None


def search_database(data, records, match, content_types, deadline):
    expected_schema()
    if len(data) > 64 * 1024**2:
        raise Unavailable("source index byte limit")
    db = sqlite3.connect(":memory:")
    try:
        db.deserialize(data)
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        _check(db, records)
        db.execute("PRAGMA query_only=ON")
        sql = "SELECT records.record_id,bm25(fts,1.0) FROM fts JOIN records ON records.rowid=fts.rowid WHERE fts MATCH ?"
        params = [match]
        if content_types:
            sql += (
                " AND records.content_type IN ("
                + ",".join("?" for _ in content_types)
                + ")"
            )
            params += list(content_types)
        sql += " ORDER BY bm25(fts,1.0),records.record_id LIMIT 1001"
        return db.execute(sql, params).fetchall()
    except sqlite3.Error:
        raise Unavailable("FTS query/database unavailable") from None
    finally:
        db.close()
