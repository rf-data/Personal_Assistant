#!/usr/bin/env python3
"""Synthetic HTML transfer/reuse using real download imports; no source network IO."""

import argparse
import hashlib
import importlib.abc
import json
import os
import socket
import sys
import tempfile
from pathlib import Path


class RuntimeOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {
            "pymupdf",
            "fitz",
            "pydantic_settings",
            "returns",
            "typer",
            "yaml",
            "pytest",
            "tenacity",
            "dotenv",
        }:
            raise AssertionError("Non-runtime import: " + fullname)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source))
    sys.meta_path.insert(0, RuntimeOnly())

    def forbidden(*_a, **_k):
        raise AssertionError("Network access in synthetic smoke")

    socket.getaddrinfo = socket.socket.connect = forbidden
    import httpx

    from scripts.cs50p_mvp import admit, download
    from src.tools_materials import batch as api
    from src.tools_materials.capacity import CapacityLimits
    from src.tools_materials.https_transport import PublicHTTPSTransport
    from src.tools_materials.processing import make_plan

    # Initialize the actual HTTPX/TLS dependency path without opening a connection.
    transport = PublicHTTPSTransport()
    transport.close()
    manifest = args.source / "docs/course_sources/cs50/manifest.json"
    selected = next(
        b
        for b in make_plan(manifest).materials
        if b.original_url == "https://cs50.harvard.edu/python/notes/0/"
    )
    batch = api.plan(manifest, ["cs50_python"], [selected.material_id])
    assert len(batch.materials) == 1
    body = b"<!doctype html><html><body>Synthetic runtime test only</body></html>"
    approval = api.SourceApproval(
        material_id=selected.material_id,
        source_id=selected.source_id,
        course_id="cs50_python",
        original_url=selected.original_url,
        **{
            key: "SYNTHETIC OFFLINE TEST ONLY"
            for key in (
                "approval_reference",
                "usage_reference",
                "license_review_reference",
                "robots_review_reference",
                "retention_reference",
                "revocation_reference",
            )
        },
        download=True,
        process=True,
        expected_sha256=hashlib.sha256(body).hexdigest(),
    )
    limits = CapacityLimits.model_validate_json(
        (Path(__file__).parent / "limits.json.example").read_bytes()
    )
    approvals = api.Approvals(sources=(approval,))
    admit(batch, limits, approvals)
    requests = []

    def serve(request):
        requests.append(str(request.url))
        return httpx.Response(200, headers={"content-type": "text/html"}, content=body)

    previous = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory(prefix="cs50p06-smoke-") as name:
            root = Path(name)
            for folder in ("archive", "reports"):
                (root / folder).mkdir(mode=0o700)
            for filename, value in (
                (
                    "batch.json",
                    dict(
                        batch=batch.model_dump(mode="json"),
                        sha256=api.fingerprint(batch.model_dump(mode="json")),
                    ),
                ),
                ("limits.json", limits.model_dump(mode="json")),
                ("approvals.json", approvals.model_dump(mode="json")),
            ):
                (root / filename).write_text(json.dumps(value))
            from types import SimpleNamespace

            options = SimpleNamespace(
                batch=root / "batch.json",
                limits=root / "limits.json",
                approvals=root / "approvals.json",
                archive=root / "archive",
                reports=root / "reports",
                confirm=True,
                retry_failed=False,
            )
            first, code = download(options, transport=httpx.MockTransport(serve))
            assert code == 0 and first["status"] == "completed", first
            second, code = download(options, transport=httpx.MockTransport(serve))
            assert code == 0 and second["materials"][0]["reused"], second
            assert len(requests) == 1
            receipt = list((root / "archive").rglob("receipt.v1.json"))
            assert len(receipt) == 1
            assert (
                json.loads(receipt[0].read_bytes())["raw_sha256"]
                == hashlib.sha256(body).hexdigest()
            )
            assert len(list((root / "reports").glob("download-*.json"))) == 2
    finally:
        os.umask(previous)
    print(
        json.dumps(
            dict(
                status="checked",
                synthetic=True,
                transfers=1,
                reused=True,
                processing_enabled=False,
            )
        )
    )


if __name__ == "__main__":
    main()
