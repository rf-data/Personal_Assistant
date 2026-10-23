"""Read-only inventory of explicit local ZIPs; never an import or downloader."""

import argparse
import json
import multiprocessing
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.tools_materials.code_zip import MAX_SECONDS, MIB, inventory_zip


def _inspect(path, connection):
    try:
        result = inventory_zip(read_file(safe_path(path), MIB))
    except (OSError, ValueError, RuntimeError) as error:
        # No exception text, archive comments or contents in reports.
        result = dict(status="blocked", error_class=type(error).__name__)
    try:
        connection.send_bytes(json.dumps(result).encode())
    finally:
        connection.close()


def inspect_path(path):
    """An owned spawned process enforces a wall-clock limit including file I/O."""
    context = multiprocessing.get_context("spawn")
    reader, writer = context.Pipe(duplex=False)
    process = context.Process(target=_inspect, args=(path, writer))
    process.start()
    writer.close()
    try:
        if not reader.poll(MAX_SECONDS):
            return dict(status="blocked", error_class="InventoryTimeout")
        try:
            return json.loads(reader.recv_bytes(128 * 1024))
        except (EOFError, OSError, ValueError):
            return dict(status="blocked", error_class="InventoryWorkerFailure")
    finally:
        reader.close()
        if process.is_alive():
            process.terminate()
        process.join(1)
        if process.is_alive():
            process.kill()
            process.join()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= len(args.archives) <= 10 or len(set(args.archives)) != len(
        args.archives
    ):
        parser.error("Provide one to ten distinct explicitly authorized local paths")
    rows, seen = [], {}
    for path in args.archives:
        if not path.is_absolute():
            parser.error("Explicit absolute input paths required")
        result = inspect_path(path)
        if digest := result.get("sha256"):
            result["duplicate_archive_of"] = seen.get(digest)
            seen.setdefault(digest, path.name)
        rows.append(dict(archive_name=path.name, **result))
    print(
        json.dumps(
            dict(schema_version=1, archives=rows, import_permitted=False), indent=2
        )
    )
    return 0 if all(r["status"] == "metadata_checked" for r in rows) else 3


if __name__ == "__main__":
    raise SystemExit(main())
