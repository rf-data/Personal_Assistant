#!/usr/bin/env python3
"""CHANGE: create NEW private, DENIED specs for ONE saved CS50P HTML link, offline.

No material retrieval and no source approval. The operator must review all inputs.
"""

import argparse
import json
import os
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
URL = "https://cs50.harvard.edu/python/notes/0/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(PACKAGE.parents[1]))
    import socket

    def forbidden(*_a, **_k):
        raise PermissionError("Example preparation is offline")

    socket.getaddrinfo = socket.socket.connect = forbidden
    from src.tools_materials import batch as api
    from src.tools_materials.processing import make_plan

    manifest = PACKAGE.parents[1] / "docs/course_sources/cs50/manifest.json"
    matches = [b for b in make_plan(manifest).materials if b.original_url == URL]
    if len(matches) != 1 or matches[0].format != "html":
        raise ValueError("Exactly one known saved HTML link required")
    selected = matches[0]
    # Validate original snapshot closure before writing any example output.
    original = api.plan(manifest, ["cs50_python"], [selected.material_id])
    os.umask(0o077)
    root = args.output.absolute()
    root.mkdir(mode=0o700)
    snapshots = root / "snapshots"
    snapshots.mkdir(mode=0o700)
    for name in original.files:
        destination = snapshots / name
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        destination.write_bytes(api.read_file(api.safe_path(manifest.parent, name)))
    batch = api.plan(snapshots / manifest.name, ["cs50_python"], [selected.material_id])
    (root / "batch.json").write_text(
        json.dumps(
            dict(
                batch=batch.model_dump(mode="json"),
                sha256=api.fingerprint(batch.model_dump(mode="json")),
            ),
            indent=2,
        )
        + "\n"
    )
    (root / "limits.json").write_bytes((PACKAGE / "limits.json.example").read_bytes())
    approval = json.loads((PACKAGE / "approval-entry.json.example").read_bytes())
    approval.update(
        material_id=selected.material_id, source_id=selected.source_id, original_url=URL
    )
    (root / "approvals.json").write_text(
        json.dumps(dict(schema_version=1, sources=[approval]), indent=2) + "\n"
    )
    api.load_batch(root / "batch.json")
    print(
        json.dumps(
            dict(
                status="prepared_denied",
                materials=1,
                original_url=URL,
                material_id=selected.material_id,
                source_id=selected.source_id,
                batch_sha256=api.fingerprint(batch.model_dump(mode="json")),
                download=False,
                process=False,
                expected_sha256=None,
                max_bytes=batch.max_bytes,
                processing_enabled=False,
            )
        )
    )


if __name__ == "__main__":
    main()
