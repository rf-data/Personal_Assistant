"""Bounded synthetic SQLite probe. Never accepts an existing database/root.

Run as ``python -m scripts.sqlite_contention_probe --output NEW_DIRECTORY``.
Boundary records accumulate in memory; JSON is written after transactions close.
This is an investigation tool, not a worker or production admission path.
"""

import argparse
import json
import logging
import multiprocessing
import os
import platform
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from src.job_control.store import SQLITE_DIAGNOSTICS, Store


class Boundaries(logging.Handler):
    def __init__(self):
        super().__init__()
        self.events = []
        self.operation = "initialize"
        self.cycle = -1

    def emit(self, record):
        self.events.append(
            dict(record.sqlite_boundary, operation=self.operation, cycle=self.cycle)
        )


def writer(root, barrier, output, cycles, pause, reinitialize_every):
    trace = Boundaries()
    SQLITE_DIAGNOSTICS.addHandler(trace)
    SQLITE_DIAGNOSTICS.setLevel(logging.DEBUG)
    SQLITE_DIAGNOSTICS.propagate = False
    completed, failure = 0, None
    try:
        store = Store(root)
        barrier.wait(timeout=15)
        for cycle in range(cycles):
            trace.operation, trace.cycle = "increment", cycle
            with store.connection(write=True) as db:
                db.execute("UPDATE worker SET heartbeat=heartbeat+1 WHERE id=1")
            completed += 1
            if reinitialize_every and cycle % reinitialize_every == 0:
                trace.operation = "reinitialize"
                store = Store(root)
            if pause:
                time.sleep(pause)
    except Exception as error:
        failure = dict(
            operation=trace.operation,
            cycle=trace.cycle,
            category=type(error).__name__,
            sqlite_code=getattr(error, "sqlite_errorcode", None),
            phase=getattr(error, "job_db_phase", None),
        )
    finally:
        SQLITE_DIAGNOSTICS.removeHandler(trace)
        with (output / f"writer-{os.getpid()}.json").open("x") as stream:
            json.dump(
                dict(completed=completed, failure=failure, events=trace.events), stream
            )


def run(
    output, *, cycles=300, writers=3, pause=0, reinitialize_every=16, pin_reader=True
):
    output.mkdir(mode=0o700)  # Exclusive; never overwrite an earlier investigation.
    root = Path(tempfile.mkdtemp(prefix="sqlite-probe-")) / "private"
    store = Store(root)
    store.heartbeat(0)
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(writers)
    children = [
        context.Process(
            target=writer,
            args=(root, barrier, output, cycles, pause, reinitialize_every),
        )
        for _ in range(writers)
    ]
    started = time.monotonic()
    try:
        with store.connection() as reader:
            if pin_reader:
                reader.execute("BEGIN")
                assert reader.execute("SELECT heartbeat FROM worker").fetchone() == (0,)
            for child in children:
                child.start()
            until = time.monotonic() + 120
            for child in children:
                child.join(timeout=max(0, until - time.monotonic()))
            if any(child.exitcode != 0 for child in children):
                raise RuntimeError("Probe child failed or exceeded its bound")
            snapshot = reader.execute("SELECT heartbeat FROM worker").fetchone()[0]
            assert not pin_reader or snapshot == 0
        reports = [
            json.loads(path.read_text())
            for path in sorted(output.glob("writer-*.json"))
        ]
        with store.connection() as db:
            value = db.execute("SELECT heartbeat FROM worker").fetchone()[0]
            integrity = db.execute("PRAGMA integrity_check").fetchall()
            foreign_keys = db.execute("PRAGMA foreign_key_check").fetchall()
            journal = db.execute("PRAGMA journal_mode").fetchone()[0]
        result = dict(
            python=sys.version,
            sqlite=sqlite3.sqlite_version,
            platform=platform.platform(),
            affinity=sorted(os.sched_getaffinity(0)),
            root=str(root),
            parameters=dict(
                cycles=cycles,
                writers=writers,
                pause=pause,
                reinitialize_every=reinitialize_every,
                pin_reader=pin_reader,
            ),
            seconds=time.monotonic() - started,
            increments=value,
            completed=[report["completed"] for report in reports],
            failures=[report["failure"] for report in reports],
            integrity=integrity,
            foreign_key_check=foreign_keys,
            journal=journal,
            quarantine=(root / "quarantine").exists(),
        )
        result["all_writes_accounted"] = value == sum(result["completed"])
        result["passed"] = (
            len(reports) == writers
            and result["failures"] == [None] * writers
            and value == cycles * writers
            and integrity == [("ok",)]
            and foreign_keys == []
            and journal == "wal"
            and not result["quarantine"]
        )
        with (output / "result.json").open("x") as stream:
            json.dump(result, stream, indent=2)
        return result
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
            if child.pid is not None:
                child.join(timeout=5)
        # Synthetic roots and evidence retained for review; never auto-cleaned.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycles", type=int, choices=(64, 300), default=300)
    parser.add_argument("--writers", type=int, choices=(1, 3), default=3)
    parser.add_argument("--pause", type=float, choices=(0, 0.01, 0.1), default=0)
    parser.add_argument("--reinitialize-every", type=int, choices=(0, 16), default=16)
    parser.add_argument("--no-pinned-reader", action="store_true")
    args = parser.parse_args(argv)
    result = run(
        args.output,
        cycles=args.cycles,
        writers=args.writers,
        pause=args.pause,
        reinitialize_every=args.reinitialize_every,
        pin_reader=not args.no_pinned_reader,
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("passed", "increments", "failures", "seconds")
            }
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
