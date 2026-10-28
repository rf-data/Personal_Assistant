"""Summarize synthetic probe boundaries without interpreting SQL or user data."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(directory):
    result = json.loads((directory / "result.json").read_text())
    events = []
    for path in sorted(directory.glob("writer-*.json")):
        events.extend(json.loads(path.read_text())["events"])
    events.sort(key=lambda event: event["at_ns"])
    groups = defaultdict(list)
    for event in events:
        groups[
            (event["pid"], event["tid"], event["started_ns"], event["attempt"])
        ].append(event)
    transactions, waits, commits, closes, failures = [], [], [], [], []
    for group in groups.values():
        stages = {event["stage"]: event for event in group}
        for start, end, target in (
            ("begin_wait", "begin_ok", waits),
            ("begin_ok", "commit_ok", transactions),
            ("commit_wait", "commit_ok", commits),
            ("close_wait", "closed", closes),
        ):
            if start in stages and end in stages:
                first, last = stages[start], stages[end]
                target.append(
                    dict(
                        pid=first["pid"],
                        cycle=first["cycle"],
                        operation=first["operation"],
                        start_ns=first["at_ns"],
                        end_ns=last["at_ns"],
                        wall_ms=(last["at_ns"] - first["at_ns"]) / 1e6,
                        cpu_ms=(last["cpu_ns"] - first["cpu_ns"]) / 1e6,
                    )
                )
        if "begin_error" in stages:
            first, last = stages["begin_wait"], stages["begin_error"]
            others = [
                event
                for event in events
                if event["pid"] != first["pid"]
                and first["at_ns"] <= event["at_ns"] <= last["at_ns"]
            ]
            failures.append(
                dict(
                    pid=first["pid"],
                    cycle=first["cycle"],
                    operation=first["operation"],
                    start_ns=first["at_ns"],
                    end_ns=last["at_ns"],
                    wall_ms=(last["at_ns"] - first["at_ns"]) / 1e6,
                    cpu_ms=(last["cpu_ns"] - first["cpu_ns"]) / 1e6,
                    sqlite_code=last["sqlite_code"],
                    transaction_began=last["in_transaction"],
                    other_commits_by_pid=dict(
                        Counter(
                            event["pid"]
                            for event in others
                            if event["stage"] == "commit_ok"
                        )
                    ),
                )
            )
    for failure in failures:
        overlapping = [
            tx
            for tx in transactions
            if tx["pid"] != failure["pid"]
            and tx["start_ns"] <= failure["end_ns"]
            and tx["end_ns"] >= failure["start_ns"]
        ]
        failure["overlapping_observed_transactions"] = len(overlapping)
        failure["longest_observed_transaction_ms"] = max(
            (tx["wall_ms"] for tx in overlapping), default=None
        )

    def largest(items):
        return sorted(items, key=lambda item: item["wall_ms"], reverse=True)[:5]

    return dict(
        parameters=result["parameters"],
        passed=result["passed"],
        increments=result["increments"],
        all_writes_accounted=result["all_writes_accounted"],
        event_count=len(events),
        writes_by_operation=dict(Counter(tx["operation"] for tx in transactions)),
        failed_begins=failures,
        longest_begin_waits=largest(waits),
        longest_observed_transactions=largest(transactions),
        longest_commits=largest(commits),
        longest_closes=largest(closes),
        limitation="Boundaries bracket Python/SQLite calls, not kernel lock acquisition or fsync. CPU gaps include sleep, scheduling and I/O. Instrumentation changes timing.",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    with args.output.open("x") as stream:
        json.dump(summarize(args.directory), stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
