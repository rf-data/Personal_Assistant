"""Explicit offline FTS build/search over an existing authorized ContentStore."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from src.content_store.errors import ContentStoreError
from src.content_store.index_models import IndexProjectionConfig
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.tools_rag.content_index import ContentIndex
from src.tools_rag.content_index_models import IndexSelection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["build", "search", "status", "discard"])
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--cursor-key", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--role", choices=["viewer", "operator"], required=True)
    parser.add_argument("--course", action="append", required=True)
    parser.add_argument("--version", action="append", default=[])
    parser.add_argument("--max-codepoints", type=int, default=2000)
    parser.add_argument("--overlap", type=int, default=0)
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--query")
    parser.add_argument("--source", action="append")
    parser.add_argument("--content-type", action="append")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--cursor")
    parser.add_argument("--build-id")
    args = parser.parse_args(argv)
    try:
        actor = Principal(
            subject=args.actor, role=args.role, courses=tuple(args.course)
        )
        store = ContentStore(args.store)
        if args.initialize and (args.operation != "build" or not args.execute):
            raise ValueError()
        if args.operation in {"build", "discard"} and not args.execute:
            print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "dry_run",
                        "operation": args.operation,
                    }
                )
            )
            return 0
        index = (
            ContentIndex.initialize(store, args.index, cursor_key_file=args.cursor_key)
            if args.initialize
            else ContentIndex(store, args.index, cursor_key_file=args.cursor_key)
        )
        if args.operation == "build":
            if not args.version:
                raise ValueError()  # Empty selection is available only in the typed API.
            result = index.build(
                IndexSelection(
                    parsed_version_ids=tuple(sorted(args.version)),
                    config=IndexProjectionConfig(
                        schema_version=1,
                        max_codepoints=args.max_codepoints,
                        overlap_codepoints=args.overlap,
                    ),
                ),
                actor=actor,
            )
            print(
                json.dumps(
                    dict(
                        schema_version=1,
                        state=result.state,
                        build_id=result.build_id,
                        generation_id=result.generation_id,
                        record_count=result.record_count,
                    )
                )
            )
        elif args.operation == "search":
            with index.search_lexical(
                args.query,
                actor=actor,
                course_id=args.course[0] if len(args.course) == 1 else None,
                source_ids=tuple(args.source) if args.source else None,
                content_types=tuple(args.content_type) if args.content_type else None,
                limit=args.limit,
                cursor=args.cursor,
            ) as page:
                print(page.model_dump_json())
        elif args.operation == "status":
            print(
                json.dumps(
                    [
                        dict(
                            build_id=r.build_id,
                            state=r.state,
                            generation_id=r.generation_id,
                        )
                        for r in index.inspect_builds(actor=actor)
                    ]
                )
            )
        else:
            if not args.build_id:
                raise ValueError()
            index.discard_build(args.build_id, actor=actor)
            print(json.dumps({"schema_version": 1, "status": "discarded"}))
        return 0
    except ContentStoreError as error:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "error": {
                        "code": error.code,
                        "message": "index operation rejected",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, TypeError, ValidationError):
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "error": {
                        "code": "invalid_request",
                        "message": "index operation rejected",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
