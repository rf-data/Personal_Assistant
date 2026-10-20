"""Source-local catalogue status, never a substitute for read-time byte verification."""

import hmac
import re
import time
from contextlib import ExitStack
from typing import Literal

from pydantic import Field

from src.content_store.errors import Forbidden
from src.content_store.models import Name, canonical, fingerprint
from src.content_store.read_models import MAX_PAGE
from src.content_store.read_views import route
from src.content_store.reader import Cursor, ReadFault
from src.job_control.models import Contract


class VersionState(Contract):
    version_id: Name
    state: Literal[
        "verified",
        "published",
        "quarantined",
        "tombstoned",
        "preparing",
        "prepared",
        "committed",
        "blocked",
        "rejected",
    ]
    read_route: str | None


class SourceStatus(Contract):
    schema_version: Literal[1] = 1
    source_id: Name
    state: Literal[
        "registered", "raw_only", "ready", "processing", "attention_required"
    ]
    raw_states: dict[str, int]
    parsed_states: dict[str, int]
    pending_runs: int | None
    kind: Literal["raw", "parsed", "runs"]
    items: tuple[VersionState, ...] = Field(max_length=50)
    next_cursor: str | None
    integrity: Literal["not_checked"] = "not_checked"
    source_route: str
    versions_route: str
    index_inputs_route: Literal["/v1/content/index/inputs"] = "/v1/content/index/inputs"


def status_reply(reader, source_id, query, actor):
    from src.content_store.search_http import SearchReply

    if set(query) - {"limit", "cursor", "kind"}:
        raise ReadFault(400, "invalid_parameter")
    raw_limit, kind = query.get("limit", "20"), query.get("kind", "parsed")
    if (
        not re.fullmatch(r"[0-9]{1,2}", raw_limit)
        or not 1 <= int(raw_limit) <= 50
        or kind not in {"raw", "parsed", "runs"}
    ):
        raise ReadFault(400, "invalid_parameter")
    limit = int(raw_limit)
    request = fingerprint(
        dict(kind="source-status-v1", source_id=source_id, view=kind, limit=limit)
    )
    actor_fp = fingerprint(
        dict(subject=actor.subject, role=actor.role, courses=sorted(actor.courses))
    )
    cursor = reader._decode_cursor(query["cursor"]) if "cursor" in query else None
    if cursor and (
        cursor.actor != actor_fp
        or cursor.request != request
        or len(cursor.last) != 1
        or type(cursor.last[0]) is not str
    ):
        raise ReadFault(400, "invalid_cursor")
    stack = ExitStack()
    try:
        stack.enter_context(reader.store._maintenance())
        db = stack.enter_context(reader.store._connection())
        source = reader._source(db, source_id, actor)
        owner = actor.role == "operator" and source.owner_subject == actor.subject
        if kind == "runs" and not owner:
            raise Forbidden()
        meta = db.execute(
            "SELECT publication_seq,collection_revision FROM metadata WHERE id=1"
        ).fetchone()
        snapshot = reader._snapshot(meta)
        if cursor and (
            not hmac.compare_digest(cursor.snapshot, snapshot)
            or cursor.acl_revision != source.acl_revision
        ):
            raise ReadFault(409, "snapshot_changed")

        def states(table):
            return dict(
                db.execute(
                    f"SELECT state,count(*) FROM {table} WHERE source_id=? GROUP BY state",
                    (source_id,),
                ).fetchall()
            )

        raw, parsed = states("source_versions"), states("parsed_versions")
        runs = states("processing_runs") if owner else {}
        pending = (
            sum(runs.get(s, 0) for s in ("preparing", "prepared", "blocked"))
            if owner
            else None
        )
        state = (
            "attention_required"
            if raw.get("quarantined")
            or parsed.get("quarantined")
            or runs.get("blocked")
            else "processing"
            if pending
            else "ready"
            if parsed.get("published")
            else "raw_only"
            if raw.get("verified")
            else "registered"
        )
        table = {
            "raw": "source_versions",
            "parsed": "parsed_versions",
            "runs": "processing_runs",
        }[kind]
        rows = db.execute(
            f"SELECT id,state FROM {table} WHERE source_id=? AND id>? ORDER BY id LIMIT ?",
            (source_id, cursor.last[0] if cursor else "", limit + 1),
        ).fetchall()
        items = tuple(
            VersionState(
                version_id=row[0],
                state=row[1],
                read_route=route("parsed", row[0])
                if kind == "parsed" and row[1] == "published"
                else route("sources", source_id, "versions")
                if kind == "raw" and row[1] == "verified"
                else None,
            )
            for row in rows[:limit]
        )
        next_cursor = (
            reader._encode_cursor(
                Cursor(
                    actor=actor_fp,
                    request=request,
                    snapshot=snapshot,
                    acl_revision=source.acl_revision,
                    last=(items[-1].version_id,),
                )
            )
            if len(rows) > limit
            else None
        )
        result = SourceStatus(
            source_id=source_id,
            state=state,
            raw_states=raw,
            parsed_states=parsed,
            pending_runs=pending,
            kind=kind,
            items=items,
            next_cursor=next_cursor,
            source_route=route("sources", source_id),
            versions_route=route("sources", source_id, "versions"),
        )
        data = canonical(result.model_dump(mode="json"))
        if len(data) > MAX_PAGE:
            raise ReadFault(503, "unavailable")
        return SearchReply(
            200, data, deadline=time.monotonic() + 2, stack=stack.pop_all()
        )
    finally:
        stack.close()


def sources_reply(reader, query, actor):
    """Keep source-list authorization through the existing HTTP delivery fence."""
    from src.content_store.search_http import SearchReply

    stack = ExitStack()
    try:
        stack.enter_context(reader.store._maintenance())
        stack.enter_context(reader.store._connection())
        result = reader.page("sources", (), query, actor)
        data = canonical(result.model_dump(mode="json"))
        if len(data) > MAX_PAGE:
            raise ReadFault(503, "unavailable")
        return SearchReply(
            200, data, deadline=time.monotonic() + 2, stack=stack.pop_all()
        )
    finally:
        stack.close()
