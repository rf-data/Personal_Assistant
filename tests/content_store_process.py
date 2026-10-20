"""Separate-process crash/concurrency harness, owned synthetic roots only."""

import json
import os
import socket
import sqlite3
import sys
from pathlib import Path


def forbidden(*a, **kw):
    raise AssertionError("process harness is offline")


socket.socket.connect = forbidden
socket.getaddrinfo = forbidden


def emit(value):
    print(json.dumps(value), flush=True)


def pause(phase):
    emit(dict(phase=phase))
    if sys.stdin.readline().strip() != "continue":
        os._exit(71)


def main():
    from src.content_store.adapters import (
        MaterialBundle,
        SRTBundle,
        import_verified_bundle,
        verify_material_bundle,
        verify_srt_bundle,
    )
    from src.content_store.errors import ContentStoreError
    from src.content_store.store import ContentStore
    from tests.content_store_support import OWNER

    command, root = sys.argv[1:3]
    if command == "wal":
        # Actual SQLite WAL from a killed process, not a fabricated sidecar.
        db = sqlite3.connect(Path(root) / "content.sqlite3")
        db.execute("PRAGMA wal_autocheckpoint=0")
        db.execute(
            "UPDATE metadata SET collection_revision=collection_revision+1 WHERE id=1"
        )
        db.commit()
        pause("wal")
        return
    if command == "read":
        store = ContentStore(root)
        data = store.read_parsed_payload(sys.argv[3], actor=OWNER)
        from src.content_store.models import sha256

        emit(dict(sha256=sha256(data)))
        return
    if command == "restore":
        from src.content_store.backup import restore

        result = restore(Path(sys.argv[3]), Path(root), actor=OWNER)
        emit(dict(snapshot_id=result.snapshot.snapshot_id))
        return
    store = ContentStore(root, read_only=False)
    descriptor, phase, request, scope = sys.argv[3:7]
    value = json.loads(Path(descriptor).read_bytes())
    srt = "transcript_path" in value
    candidate = (
        verify_srt_bundle(SRTBundle.model_validate(value))
        if srt
        else verify_material_bundle(MaterialBundle.model_validate(value))
    )

    def selected(run):
        prefix = {
            "raw": "content_raw_slot_v1:",
            "binding": "content_binding_slot_v1:",
            "parsed": "content_slot_v1:",
        }[scope]
        return run.slot_id.startswith(prefix)

    prepared = store._prepared

    def on_prepared(run, refs, actor):
        prepared(run, refs, actor)
        if phase == "prepared" and selected(run):
            pause(phase)

    store._prepared = on_prepared
    install = store._artifacts.install

    def on_install(run_id, ref):
        install(run_id, ref)
        with store._connection() as db:
            from src.content_store.operations import _run

            run = _run(db, run_id)
        if phase == "installed" and selected(run) and run.state == "prepared":
            pause(phase)

    store._artifacts.install = on_install
    stage = store._artifacts.stage

    def on_stage(run_id, stream, ref):
        if phase == "staging":
            with store._connection() as db:
                from src.content_store.operations import _run

                run = _run(db, run_id)
            if selected(run):
                original_stream = stream

                class Interrupted:
                    def __init__(self):
                        self.first = True

                    def read(self, n):
                        if self.first:
                            self.first = False
                            return original_stream.read(min(n, 8))
                        pause(phase)
                        return original_stream.read(n)

                stream = Interrupted()
        return stage(run_id, stream, ref)

    store._artifacts.stage = on_stage
    if phase == "before_commit":
        import src.content_store.publication as publication

        finish = publication.finish_publication

        def on_finish(*args, **kwargs):
            pause(phase)
            return finish(*args, **kwargs)

        publication.finish_publication = on_finish
    update_run = store._update_run

    def on_update(db, run, **updates):
        result = update_run(db, run, **updates)
        if (
            phase == "before_sql_commit"
            and selected(run)
            and updates.get("state") == "committed"
        ):
            pause(phase)
        return result

    store._update_run = on_update
    publish = store.publish_parsed_document

    def on_publish(*args, **kwargs):
        result = publish(*args, **kwargs)
        if phase == "after_commit":
            pause(phase)
        return result

    store.publish_parsed_document = on_publish
    try:
        retries = {}
        if len(sys.argv) > 7:
            from src.content_store.models import RetryAttempt

            retries = {
                key: RetryAttempt.model_validate(value)
                for key, value in json.loads(sys.argv[7]).items()
            }
        result = import_verified_bundle(
            store, candidate, actor=OWNER, request_key=request, **retries
        )
        emit(dict(created=result.created, version=result.version.parsed_version_id))
    except ContentStoreError as error:
        emit(dict(error=error.code))


if __name__ == "__main__":
    main()
