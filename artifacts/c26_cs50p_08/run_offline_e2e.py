"""Synthetic end-to-end evidence generator; uses only reviewed test fixtures."""

import argparse
import json
import shutil
import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.tools_materials import week_acquisition as api
from src.tools_materials import week_processing as processing
from tests.test_cs50p_week_completion import acquire, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("New evidence output required")

    def forbidden(*args, **kwargs):
        raise AssertionError("Real network forbidden in synthetic E2E")

    with (
        tempfile.TemporaryDirectory(prefix="cs50p08-e2e-") as temporary,
        patch.object(socket, "getaddrinfo", forbidden),
        patch.object(socket.socket, "connect", forbidden),
        patch.object(
            shutil, "disk_usage", lambda _: SimpleNamespace(free=20 * 1024**3)
        ),
    ):
        root = Path(temporary)
        raw, output, calls = root / "raw", root / "processed", []
        acquired = acquire(inventory(), raw, calls)
        receipts = {
            str(p.relative_to(raw)): p.read_bytes()
            for p in raw.rglob("receipt.v1.json")
        }
        before = api.completeness(acquired, raw)
        processed = processing.process(acquired, raw, output, offline_test=True)
        report = api.completeness(acquired, raw, output)
        first_transfers = len(calls)
        repeated = acquire(acquired, raw, calls)
        resumed = processing.process(repeated, raw, output, offline_test=True)
        assert before["status"] == "HOLD" and before["overall"]["acquisition_complete"]
        assert report["status"] == "FULLY_COMPLETE" and report["c26_status"] == "HOLD"
        assert len(calls) == first_transfers
        assert all(r["reused"] for r in resumed["materials"])
        assert receipts == {
            str(p.relative_to(raw)): p.read_bytes()
            for p in raw.rglob("receipt.v1.json")
        }
        evidence = dict(
            kind="synthetic-offline-e2e",
            production_evidence=False,
            positive_frozen_install=False,
            real_hetzner_acceptance=False,
            first_transfers=first_transfers,
            second_transfers=0,
            processing=processed,
            processing_reused=True,
            downloadreceipts_unchanged=True,
            report=report,
        )
        args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        json.dumps(
            dict(status="PASS", source_origin="synthetic", output=str(args.output))
        )
    )


if __name__ == "__main__":
    main()
