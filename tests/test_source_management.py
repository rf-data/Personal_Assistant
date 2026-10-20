"""Source status through the actual authenticated gateway, synthetic stores only."""

import json
from urllib.parse import urlencode

import pytest

from src.content_store.errors import Busy
from src.content_store.models import SourceGrant
from src.content_store.source_status import SourceStatus
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.index_job_support import setup, token


@pytest.fixture
def env(tmp_path):
    return setup(tmp_path)


def get(env, path, actor=OWNER, expected=200):
    reply = env.app.request("GET", path, {"Authorization": "Bearer " + token(actor)})
    try:
        code, raw, _ = reply
        assert code == expected, (code, raw)
        return json.loads(raw)
    finally:
        if hasattr(reply, "close"):
            reply.close()


def route(env, **kw):
    result = "/v1/content/sources/" + env.pv.source_id + "/status"
    return result + ("?" + urlencode(kw) if kw else "")


def test_registered_versions_and_redacted_status(env):
    result = SourceStatus.model_validate(get(env, route(env)))
    assert result.state == "ready" and result.integrity == "not_checked"
    assert result.raw_states == {"verified": 1} and result.parsed_states == {
        "published": 1
    }
    assert result.items[0].version_id == env.pv.parsed_version_id
    assert (
        str(env.tmp) not in result.model_dump_json()
        and "request_key" not in result.model_dump_json()
    )
    raw = get(env, route(env, kind="raw"))
    assert raw["items"][0]["version_id"] == env.pv.source_version_id
    assert (
        get(env, result.items[0].read_route)["parsed_version_id"]
        == env.pv.parsed_version_id
    )


def test_source_acl_course_and_revocation(env):
    get(env, route(env), OTHER, 404)
    get(env, route(env), VIEWER, 404)
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    result = get(env, route(env), VIEWER)
    assert result["pending_runs"] is None
    get(env, route(env, kind="runs"), VIEWER, 404)
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
    )
    get(env, route(env), VIEWER, 404)


def test_literal_id_search_not_hidden_metadata(env):
    source = env.pv.source_id
    assert (
        len(get(env, "/v1/content/sources?" + urlencode({"q": source}))["items"]) == 1
    )
    assert not get(env, "/v1/content/sources?q=%25")["items"]
    assert not get(env, "/v1/content/sources?q=cs50.harvard.edu")["items"]
    assert not get(env, "/v1/content/sources?q=resource", OTHER)["items"]


@pytest.mark.parametrize(
    "query",
    [
        {"kind": "unknown"},
        {"limit": "51"},
        {"limit": "0"},
        {"q": "private"},
        {"cursor": "forged"},
    ],
)
def test_bad_status_inputs(env, query):
    get(env, route(env, **query), expected=400)


def test_quarantine_tombstone_are_metadata_only(env):
    with env.content._connection(write=True) as db:
        db.execute("UPDATE parsed_versions SET state='quarantined'")
    value = get(env, route(env))
    assert value["state"] == "attention_required"
    assert (
        value["items"][0]["state"] == "quarantined"
        and value["items"][0]["read_route"] is None
    )
    get(env, "/v1/content/parsed/" + env.pv.parsed_version_id, expected=404)


def test_status_holds_authorization_until_reply_close(env):
    reply = env.app.request(
        "GET", route(env), {"Authorization": "Bearer " + token(OWNER)}
    )
    try:
        assert reply.status == 200
        with pytest.raises(Busy):
            env.content.set_source_grants(
                env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
            )
    finally:
        reply.close()
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
    )


def test_status_pagination_and_cursor_binding(env):
    from src.content_store.adapters import (
        import_verified_bundle,
        verify_material_bundle,
    )
    from tests.content_adapter_support import attest

    attest(env.bundle, revision="b" * 40)
    import_verified_bundle(
        env.content,
        verify_material_bundle(env.bundle),
        actor=OWNER,
        request_key="second-config",
    )
    first = get(env, route(env, limit=1))
    assert len(first["items"]) == 1 and first["next_cursor"]
    second = get(env, route(env, limit=1, cursor=first["next_cursor"]))
    assert second["items"][0]["version_id"] != first["items"][0]["version_id"]
    assert second["next_cursor"] is None
    get(env, route(env, kind="raw", limit=1, cursor=first["next_cursor"]), expected=400)
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
    )
    get(env, route(env, limit=1, cursor=first["next_cursor"]), expected=409)
