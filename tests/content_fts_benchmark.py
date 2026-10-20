"""Explicit synthetic technical measurement; no relevance labels or real corpus."""

import argparse
import json
import platform
import socket
import sqlite3
import time
from pathlib import Path

import pydantic

from src.content_store._testing import synthetic_content_index
from src.content_store.artifacts import explicit_root
from src.content_store.errors import ContentStoreError
from tests.content_store_support import OWNER
from tests.test_content_fts import hits, inventory, synthetic_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--records", type=int, default=125)
    args = parser.parse_args()
    root = explicit_root(args.work_root)
    if not 1 <= args.records <= 1001:
        raise ValueError("records limit")
    if args.output.exists():
        raise ValueError("output exists")
    root.mkdir(mode=0o700)

    def forbidden(*a, **kw):
        raise AssertionError("network forbidden")

    socket.socket.connect = forbidden
    socket.getaddrinfo = forbidden
    _, store, _, selection, key = synthetic_index(root, count=args.records)
    index = synthetic_content_index(
        store, root / "measured-index", cursor_key_file=key, initialize=True
    )
    original = inventory(store.root)
    start = time.perf_counter()
    first = index.build(selection, actor=OWNER)
    build_seconds = time.perf_counter() - start
    _, active, manifest = index._active()
    source_bytes = sum(f.size_bytes for f in manifest.files)
    queries = []
    for query in [
        str(args.records - 1),
        "Python " + str(args.records - 1),
        "café " + str(args.records - 1),
        "unfindable",
        "function",
    ]:
        samples = []
        for _ in range(3):
            start = time.perf_counter()
            try:
                page = hits(index, query, limit=100)
                outcome = dict(
                    status="ok",
                    returned=len(page.items),
                    next_cursor=bool(page.next_cursor),
                )
            except ContentStoreError as error:
                outcome = dict(status=error.code, returned=None, next_cursor=False)
            samples.append(time.perf_counter() - start)
        queries.append(dict(query=query, elapsed_seconds=samples, **outcome))
    start = time.perf_counter()
    repeated = index.build(selection, actor=OWNER)
    rebuild_seconds = time.perf_counter() - start
    assert repeated.generation_id == first.generation_id
    assert inventory(store.root) == original
    report = dict(
        schema_version=1,
        data_kind="synthetic_technical_fixture",
        relevance_quality_evaluated=False,
        environment=dict(
            python=platform.python_version(),
            sqlite=sqlite3.sqlite_version,
            pydantic=pydantic.__version__,
        ),
        sources=1,
        records=first.record_count,
        source_sqlite_bytes=source_bytes,
        active_generation_bytes=sum(
            p.stat().st_size
            for p in (
                index.root
                / "generations"
                / active.generation_id.split(":")[1]
                / active.build_id
            ).iterdir()
        ),
        total_index_bytes_after_rebuild=sum(
            p.stat().st_size for p in index.root.rglob("*") if p.is_file()
        ),
        build_seconds=build_seconds,
        rebuild_seconds=rebuild_seconds,
        queries=queries,
        unchanged_content_bytes=True,
        notes=[
            "Three warm-process sequential measurements per query; verification and hydration included.",
            "A deadline can reject a request before match counting; errors are reported, never treated as empty successful results.",
            "No relevance judgments, precision, recall or MRR.",
            "No throughput/RSS/load approval; one Source on a local test filesystem.",
        ],
    )
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)
        output.write("\n")
    print(
        json.dumps(
            dict(
                records=first.record_count,
                build_seconds=build_seconds,
                rebuild_seconds=rebuild_seconds,
            )
        )
    )


if __name__ == "__main__":
    main()
