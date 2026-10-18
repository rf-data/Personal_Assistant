"""Offline persistence, live ACL, real gateway and existing A evaluator acceptance."""

import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from src.content_store.errors import (
    Busy,
    Conflict,
    Forbidden,
    IntegrityError,
    Unavailable,
)
from src.content_store.models import SourceGrant
from src.evaluation_store.models import Region, ReviewGrant, ReviewSettings
from src.evaluation_store.store import EvaluationStore
from src.job_control.http import Application
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet,
    EvaluationConfig,
)
from src.model_evaluation.material_evaluation import GoldDataset
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from tests.content_retrieval_support import results_for
from tests.content_store_support import OWNER, VIEWER
from tests.review_support import (
    PERMISSIONS,
    api,
    complete_pool,
    confirm,
    draft,
    gateway,
    initialize,
    mutation,
    reviewed,
    setup_review,
    task_request,
)
from tests.test_content_fts import inventory


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def env(tmp_path):
    return setup_review(tmp_path)


def test_explicit_initialization_private_reopen_and_no_overwrite(tmp_path):
    root = tmp_path / "review"
    with pytest.raises(Unavailable):
        EvaluationStore(root)
    assert not root.exists()
    store = EvaluationStore.initialize(root)
    assert root.stat().st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in root.iterdir())
    assert EvaluationStore(root).root == store.root
    with pytest.raises(Conflict):
        EvaluationStore.initialize(root)
    with sqlite3.connect(root / "evaluation.sqlite3") as db:
        db.execute("PRAGMA user_version=2")
    with pytest.raises(IntegrityError):
        EvaluationStore(root)


def test_verified_bundle_api_restart_correction_export_evaluator(env):
    original = inventory(env.content.root)
    bundle_before = inventory(env.tmp / "bundle")
    initialize(env)
    positive = reviewed(env)
    blocks = env.content.list_content_blocks(
        env.pv.parsed_version_id, actor=OWNER
    ).items
    negative = reviewed(env, "negative", block=blocks[0], text="# Ä", start=0)
    assert negative["value"]["annotation"]["grade"] == 0
    raw = api(env, "GET", "/tasks/positive/raw")
    assert raw == '# Ä\r\nprint("hello")\n'.encode()
    env.app = gateway(env.settings, env.tmp / "jobs")
    assert api(env, "GET", "/tasks/positive")["revision"] == positive["revision"]
    revised = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(positive["revision"], "correct", correction=True, grade=2),
    )
    confirmed = confirm(env, "positive", revised, "confirm-correction")
    assert confirmed["value"]["review"]["reviewer"] == "owner"
    history = api(env, "GET", "/tasks/positive/revisions")["items"]
    assert [e["value"]["status"] for e in history] == [
        "pending",
        "in_review",
        "confirmed",
        "in_review",
        "confirmed",
    ]
    assert history[-1]["previous_revision"] == revised["revision"]
    complete_pool(env)
    api(env, "POST", "/exports/export-1", mutation())
    exported = api(env, "GET", "/exports/export-1")
    assert api(env, "GET", "/exports/export-1") == exported
    dataset = ContentRetrievalEvaluationSet.model_validate(exported["retrieval"])
    assert dataset.pools[0].pool_complete and dataset.corpus_complete
    results = results_for(dataset, page=env.page)
    external = evaluate_retrieval(
        dataset, results, evaluation_config=EvaluationConfig(schema_version=1)
    )
    assert external.report.recall_at_k.value == external.report.mrr_at_k.value == 1
    report = api(
        env,
        "POST",
        "/reports/report-1",
        mutation(export_id="export-1", results=results.model_dump(mode="json")),
    )
    assert report["value"]["report"]["digest"] == external.digest
    assert api(env, "GET", "/reports/report-1")["current"]
    api(
        env,
        "POST",
        "/acceptances/limited",
        mutation(
            report_id="report-1",
            decision="accepted_with_limitations",
            limitations=["Synthetic workflow only; real pilot remains blocked"],
        ),
    )
    acceptance = api(env, "GET", "/acceptances/limited")
    assert acceptance["value"]["approver"] == "owner"
    assert not acceptance["value"]["automatic_release"]
    assert inventory(env.content.root) == original
    assert inventory(env.tmp / "bundle") == bundle_before


def test_idempotency_cas_and_state_machine(env):
    initialize(env)
    request = task_request(env)
    head = api(env, "POST", "/tasks", request)
    assert api(env, "POST", "/tasks", request) == head
    api(env, "POST", "/tasks", {**request, "reason": "changed"}, status=409)
    api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(
            head["revision"],
            "assisted-confirm",
            decision="confirmed",
            evidence_reference="test",
        ),
        status=409,
    )
    req = draft(head["revision"])
    first = api(env, "POST", "/tasks/positive/draft", req)
    assert api(env, "POST", "/tasks/positive/draft", req) == first
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(head["revision"], "stale"),
        status=409,
    )
    last = confirm(env, "positive", first)
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(last["revision"], "silent-correction"),
        status=409,
    )
    corrected = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(last["revision"], "correction", correction=True),
    )
    clarification = api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(
            corrected["revision"],
            "clarify",
            decision="needs_clarification",
            evidence_reference="uncertain-original",
        ),
    )
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(clarification["revision"], "new-annotation"),
    )


def test_pool_is_separate_and_stales_after_correction(env):
    initialize(env)
    head = reviewed(env)
    api(
        env,
        "POST",
        "/pool",
        mutation(
            query_id="query-1",
            reviewed_task_ids=["positive"],
            coverage_note="Missing original line",
            evidence_reference="test",
        ),
        status=409,
    )
    api(env, "POST", "/exports/pending", mutation())
    exported = api(env, "GET", "/exports/pending")
    assert not exported["retrieval"]["corpus_complete"]
    assert not exported["retrieval"]["pools"]
    b = env.content.list_content_blocks(env.pv.parsed_version_id, actor=OWNER).items[0]
    reviewed(env, "negative", block=b, text="# Ä", start=0)
    complete_pool(env)
    api(env, "POST", "/exports/complete", mutation())
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(head["revision"], "correction", correction=True),
    )
    api(env, "GET", "/exports/complete", status=409)
    api(env, "POST", "/exports/after", mutation())
    assert not api(env, "GET", "/exports/after")["retrieval"]["pools"]


@pytest.mark.parametrize(
    "field",
    [
        "source_id",
        "source_version_id",
        "parsed_version_id",
        "block_id",
        "parser_config_id",
        "text_sha256",
        "raw_sha256",
        "payload_sha256",
        "projection_sha256",
        "locator",
        "start",
    ],
)
def test_bad_binding_fails_before_publication(env, field):
    initialize(env)
    req = task_request(env)
    r = req["task"]["region"]
    if field.endswith("sha256"):
        r[field] = "f" * 64
        if field == "raw_sha256":
            r["locator"]["raw_artifact_sha256"] = "f" * 64
    elif field == "locator":
        r[field]["origin_pointer"] = "/wrong"
    elif field == "start":
        r["start"] += 1
        r["end"] += 1
    else:
        r[field] = "missing"
    api(env, "POST", "/tasks", req, status=409)
    assert not api(env, "GET", "/tasks")["items"]


def grant_viewer(env, permissions=("read",)):
    env.content.set_source_grants(
        env.pv.source_id,
        (SourceGrant(subject="viewer"),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    grant = ReviewGrant(
        schema_version=1,
        subject="viewer",
        dataset_id="synthetic-review",
        source_ids=(env.pv.source_id,),
        permissions=permissions,
    )
    env.settings = env.settings.model_copy(
        update={"grants": (*env.settings.grants, grant)}
    )
    env.app = gateway(env.settings, env.tmp / "jobs")


def test_readgrant_is_not_review_permission_and_foreign_tasks_redacted(env):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    grant_viewer(env)
    assert api(env, "GET", "/tasks", actor=VIEWER)["items"] == []
    known = api(env, "GET", "/tasks/positive", actor=VIEWER, status=404)
    assert api(env, "GET", "/tasks/unknown", actor=VIEWER, status=404) == known
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(head["revision"]),
        actor=VIEWER,
        status=404,
    )
    env.app = gateway(
        env.settings.model_copy(update={"grants": env.settings.grants[:1]}),
        env.tmp / "jobs",
    )
    api(env, "GET", "/tasks", actor=VIEWER, status=404)


def test_explicit_assignment_and_separate_confirmation_permission(env):
    initialize(env)
    grant_viewer(env, ("read", "annotate"))
    head = api(env, "POST", "/tasks", task_request(env, assignee="viewer"))
    first = api(
        env, "POST", "/tasks/positive/draft", draft(head["revision"]), actor=VIEWER
    )
    api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(first["revision"], decision="confirmed", evidence_reference="test"),
        actor=VIEWER,
        status=404,
    )
    api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(first["revision"], "manager-attempt"),
        status=404,
    )


@pytest.mark.parametrize("extra", ["reviewer", "actor", "role", "approver"])
def test_request_cannot_supply_identity(env, extra):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    req = draft(head["revision"])
    req[extra] = "forged"
    api(env, "POST", "/tasks/positive/draft", req, status=422)


def test_assisted_preannotation_cannot_confirm_itself(env):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    head = api(
        env, "POST", "/tasks/positive/draft", draft(head["revision"], mode="assisted")
    )
    api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(
            head["revision"],
            "assisted-confirm",
            decision="confirmed",
            evidence_reference="test",
        ),
        status=404,
    )
    head = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(head["revision"], "rename-as-independent"),
    )
    api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(
            head["revision"],
            "assisted-confirm",
            decision="confirmed",
            evidence_reference="test",
        ),
        status=404,
    )


def test_missing_evidence_and_unknown_schema_rejected(env):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    head = api(env, "POST", "/tasks/positive/draft", draft(head["revision"]))
    req = mutation(head["revision"], decision="confirmed")
    api(env, "POST", "/tasks/positive/decision", req, status=422)
    req = draft(head["revision"])
    req["schema_version"] = True
    api(env, "POST", "/tasks/positive/draft", req, status=422)


def test_disabled_writes_and_gateway_capability(env):
    disabled = Application(env.app.controller)
    env.app = disabled
    assert not api(env, "GET", "/v1/evaluation/capabilities")["enabled"]
    api(env, "GET", "/tasks", status=503)
    env.app = gateway(
        env.settings.model_copy(update={"writes_enabled": False}), env.tmp / "jobs"
    )
    api(env, "POST", value=mutation(dataset=env.spec), status=404)


def test_revoked_grant_and_missing_course_block_every_action(env):
    initialize(env)
    grant_viewer(env, PERMISSIONS)
    head = api(env, "POST", "/tasks", task_request(env, assignee="viewer"))
    head = api(
        env, "POST", "/tasks/positive/draft", draft(head["revision"]), actor=VIEWER
    )
    env.content.set_source_grants(
        env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
    )
    api(env, "GET", "/tasks/positive", actor=VIEWER, status=404)
    api(
        env,
        "POST",
        "/tasks/positive/decision",
        mutation(head["revision"], decision="confirmed", evidence_reference="test"),
        actor=VIEWER,
        status=404,
    )
    actor = OWNER.model_copy(update={"courses": ("cs50x",)})
    with pytest.raises(Forbidden):
        env.app.review.service.call("synthetic-review", "get", actor, item="positive")


@pytest.mark.parametrize("kind", ["quarantine", "tombstone"])
def test_content_status_blocks_existing_export(env, kind):
    initialize(env)
    reviewed(env)
    api(env, "POST", "/exports/current", mutation())
    with env.content._maintenance(), env.content._connection(write=True) as db:
        db.execute(
            "UPDATE parsed_versions SET state=? WHERE id=?",
            (
                "quarantined" if kind == "quarantine" else "tombstoned",
                env.pv.parsed_version_id,
            ),
        )
    api(env, "GET", "/exports/current", status=404)
    api(env, "POST", "/exports/after", mutation(), status=404)


def test_parsing_gold_is_separate_and_original_unchanged(env):
    before = inventory(env.content.root)
    initialize(env)
    head = api(
        env,
        "POST",
        "/tasks",
        task_request(env, kind="parsing", text='print("hello")\n', start=0),
    )
    head = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(
            head["revision"],
            grade=None,
            quality="incorrect",
            expected_content="independently corrected text",
            error_categories=["symbol_error"],
        ),
    )
    confirm(env, "positive", head)
    api(env, "POST", "/exports/parsing", mutation())
    exported = api(env, "GET", "/exports/parsing")
    parsing = GoldDataset.model_validate(exported["parsing"])
    assert parsing.references[0].expected_content == "independently corrected text"
    assert parsing.references[0].notes[0] == "incorrect"
    assert parsing.references[0].entry_id == "synthetic-code-entry"
    assert not exported["retrieval"]["judgments"]
    assert inventory(env.content.root) == before


def test_unknown_time_and_codepoint_contract(env):
    initialize(env)
    req = task_request(env)
    r = req["task"]["region"]
    for text in ("😀 e\u0301\r\n", "a−b", "x²"):
        typed = Region.model_validate(
            {
                **r,
                "start": 0,
                "end": len(text),
                "original_region": text,
                "locator": {
                    **r["locator"],
                    "time_status": "unknown",
                    "start": None,
                    "end": None,
                },
            }
        )
        assert Region.model_validate_json(typed.model_dump_json()) == typed
        assert typed.locator.start is None
        # Valid shape cannot invent a region absent from the authoritative block.
        altered = {
            **req,
            "task": {**req["task"], "region": typed.model_dump(mode="json")},
        }
        api(env, "POST", "/tasks", altered, status=409)
    with pytest.raises(ValidationError):
        Region.model_validate({**r, "end": r["end"] + 1})


def test_tamper_revisions_and_heads_fail_closed(env):
    initialize(env)
    reviewed(env)
    with sqlite3.connect(env.settings.root / "evaluation.sqlite3") as db:
        db.execute(
            "UPDATE events SET body=replace(body,'Explicit synthetic','Changed synthetic') WHERE seq=1"
        )
    env.app = gateway(env.settings, env.tmp / "jobs")
    api(env, "GET", "/tasks", status=503)


def test_transaction_rollback_and_concurrent_cas(env, monkeypatch):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    store = EvaluationStore(env.settings.root)
    with pytest.raises(RuntimeError):
        with store.connection(write=True) as db:
            db.execute("DELETE FROM events")
            raise RuntimeError("synthetic interrupted transaction")
    assert api(env, "GET", "/tasks/positive")["revision"] == head["revision"]
    service = env.app.review.service
    from src.evaluation_store.models import Draft

    requests = [
        Draft.model_validate(draft(head["revision"], "racer-" + str(i)))
        for i in range(2)
    ]

    def run(req):
        try:
            service.call("synthetic-review", "draft", OWNER, req, item="positive")
            return "committed"
        except (Busy, Conflict):
            return "blocked"

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, requests)) == ["blocked", "committed"]


def test_sigkill_uncommitted_review_transaction_reopens(env):
    initialize(env)
    before = api(env, "GET", "/tasks")
    code = """
import sys,time
from src.evaluation_store.store import EvaluationStore
s=EvaluationStore(sys.argv[1])
from src.evaluation_store.models import Mutation
from src.job_control.models import Principal
with s.connection(write=True) as db:
 old=s.get(db,"synthetic-review/dataset")
 req=Mutation(schema_version=1,expected_revision=old["revision"],idempotency_key="killed-append",reason="Synthetic uncommitted audit append")
 actor=Principal(subject="owner",role="operator",courses=("cs50_python",))
 s.append(db,"synthetic-review/dataset",actor,req,old["value"],old["value"])
 print("uncommitted",flush=True)
 time.sleep(30)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(env.settings.root)],
        stdout=subprocess.PIPE,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
    )
    try:
        import select

        assert select.select([process.stdout], [], [], 5)[0]
        assert process.stdout.readline().strip() == "uncommitted"
        process.send_signal(signal.SIGKILL)
        assert process.wait(timeout=5) == -signal.SIGKILL
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
    env.app = gateway(env.settings, env.tmp / "jobs")
    assert api(env, "GET", "/tasks") == before


def test_live_content_locks_prevent_revocation_between_check_and_commit(
    env, monkeypatch
):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    append = EvaluationStore.append.__func__
    attempted = []

    def guarded(cls, db, *args):
        with pytest.raises(Busy):
            env.content.set_source_grants(
                env.pv.source_id, (), expected_acl_revision=0, actor=OWNER
            )
        attempted.append(True)
        return append(cls, db, *args)

    monkeypatch.setattr(EvaluationStore, "append", classmethod(guarded))
    api(env, "POST", "/tasks/positive/draft", draft(head["revision"]))
    assert attempted == [True]


def test_review_settings_default_deny_real_authorization(env):
    value = env.settings.model_dump(mode="json")
    value.pop("writes_enabled")
    assert not ReviewSettings.model_validate(value).writes_enabled
    with pytest.raises(ValidationError):
        ReviewSettings.model_validate({**value, "real_reviews_enabled": True})
    with pytest.raises(ValidationError):
        ReviewSettings.model_validate(
            {**value, "root": str(env.content.root / "review")}
        )


def test_independent_viewer_requires_explicit_permission_and_assignment(env):
    initialize(env)
    grant_viewer(env, ("read", "annotate", "confirm"))
    head = api(env, "POST", "/tasks", task_request(env, assignee="viewer"))
    head = api(
        env, "POST", "/tasks/positive/draft", draft(head["revision"]), actor=VIEWER
    )
    head = confirm(env, "positive", head, actor=VIEWER)
    assert head["value"]["review"]["reviewer"] == "viewer"
    api(env, "POST", "/exports/independent", mutation())
    exported = api(env, "GET", "/exports/independent")
    assert exported["retrieval"]["judgments"][0]["review"]["reviewer"] == "viewer"
    assert "token_sha256" not in json.dumps(env.trace)
    assert str(env.tmp) not in json.dumps(env.trace)
    api(
        env,
        "POST",
        "/acceptances/unauthorized",
        mutation(report_id="none", decision="accepted", limitations=[]),
        actor=VIEWER,
        status=404,
    )


def test_export_actor_revoked_and_change_before_guard(env, monkeypatch):
    from contextlib import contextmanager

    grant_viewer(env, PERMISSIONS)
    api(env, "POST", value=mutation(dataset=env.spec), actor=VIEWER)
    head = api(
        env, "POST", "/tasks", task_request(env, assignee="viewer"), actor=VIEWER
    )
    head = api(
        env, "POST", "/tasks/positive/draft", draft(head["revision"]), actor=VIEWER
    )
    confirm(env, "positive", head, actor=VIEWER)
    api(env, "POST", "/exports/viewer", mutation(), actor=VIEWER)
    original = EvaluationStore.connection
    calls = []

    @contextmanager
    def revoke_after_loading(self, **kwargs):
        with original(self, **kwargs) as db:
            yield db
        if not calls:
            calls.append(True)
            env.content.set_source_grants(
                env.pv.source_id, (), expected_acl_revision=1, actor=OWNER
            )

    monkeypatch.setattr(EvaluationStore, "connection", revoke_after_loading)
    api(env, "GET", "/exports/viewer", actor=VIEWER, status=404)
    api(env, "POST", "/exports/revoked", mutation(), actor=VIEWER, status=404)


def test_actual_unicode_combining_emoji_crlf_verified_bundle(tmp_path):
    raw = '# 😀 e\u0301\r\nprint("hello")\r\n'.encode()
    env = setup_review(tmp_path, code_raw=raw)
    before = inventory(env.content.root)
    initialize(env)
    block = env.content.list_content_blocks(
        env.pv.parsed_version_id, actor=OWNER
    ).items[0]
    head = api(
        env,
        "POST",
        "/tasks",
        task_request(env, block=block, text="😀 e\u0301", start=2),
    )
    head = api(env, "POST", "/tasks/positive/draft", draft(head["revision"], grade=0))
    confirm(env, "positive", head)
    assert api(env, "GET", "/tasks/positive/raw") == raw
    api(env, "POST", "/exports/unicode", mutation())
    gold = api(env, "GET", "/exports/unicode")["retrieval"]["judgments"][0]
    assert gold["original_region"] == "😀 e\u0301" and gold["end"] - gold["start"] == 4
    assert inventory(env.content.root) == before


def test_unanchored_and_undetermined_parsing_findings_never_become_gold(env):
    initialize(env)
    req = task_request(env, kind="parsing")
    req["task"]["unanchored_finding"] = True
    head = api(env, "POST", "/tasks", req)
    head = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(
            head["revision"],
            grade=None,
            quality="incorrect",
            expected_content="Original text missing from every parsed block",
        ),
    )
    head = confirm(env, "positive", head)
    assert head["value"]["status"] == "confirmed"
    assert api(env, "GET", "/tasks/positive/region")["view"] == "parsed_context_only"
    api(env, "POST", "/exports/findings", mutation())
    exported = api(env, "GET", "/exports/findings")
    assert (
        not exported["retrieval"]["judgments"] and not exported["parsing"]["references"]
    )
    corrected = api(
        env,
        "POST",
        "/tasks/positive/draft",
        draft(
            head["revision"],
            "uncertain",
            correction=True,
            grade=None,
            quality="undetermined",
            expected_content=None,
        ),
    )
    confirm(env, "positive", corrected, "confirm-uncertainty")
    api(env, "POST", "/exports/undetermined", mutation())
    assert not api(env, "GET", "/exports/undetermined")["parsing"]["references"]


def test_security_failure_blocks_manual_acceptance(env):
    initialize(env)
    reviewed(env)
    block = env.content.list_content_blocks(
        env.pv.parsed_version_id, actor=OWNER
    ).items[0]
    reviewed(env, "negative", block=block, text="# Ä", start=0)
    complete_pool(env)
    api(env, "POST", "/exports/security", mutation())
    dataset = ContentRetrievalEvaluationSet.model_validate(
        api(env, "GET", "/exports/security")["retrieval"]
    )
    from src.model_evaluation.content_retrieval import SecurityEvidence

    results = results_for(
        dataset,
        page=env.page,
        security=(
            SecurityEvidence(
                scenario="text_leak",
                status="failed",
                reason="Synthetic injected leakage evidence",
                evidence_sha256="a" * 64,
                confirmed_leak=True,
            ),
        ),
    )
    report = api(
        env,
        "POST",
        "/reports/leak",
        mutation(export_id="security", results=results.model_dump(mode="json")),
    )
    assert report["value"]["report"]["report"]["release_blocker"]
    # A later report cannot erase already recorded security evidence.
    clean = results_for(dataset, page=env.page)
    api(
        env,
        "POST",
        "/reports/clean",
        mutation(export_id="security", results=clean.model_dump(mode="json")),
    )
    api(
        env,
        "POST",
        "/acceptances/laundered",
        mutation(
            report_id="clean",
            decision="accepted_with_limitations",
            limitations=["Later report omitted previous security failure"],
        ),
        status=404,
    )
    for decision in ("accepted", "accepted_with_limitations"):
        api(
            env,
            "POST",
            "/acceptances/leak",
            mutation(
                report_id="leak",
                decision=decision,
                limitations=["Cannot waive confirmed leak"],
            ),
            status=404,
        )
    api(
        env,
        "POST",
        "/acceptances/rejected",
        mutation(
            report_id="leak",
            decision="rejected",
            limitations=["Confirmed leak blocks release"],
        ),
    )
    rejected = api(env, "GET", "/acceptances/rejected")
    assert rejected["current"] and rejected["blocked_by_security"]


def test_assignment_changes_revision_and_disallows_rebinding(env):
    initialize(env)
    head = api(env, "POST", "/tasks", task_request(env))
    assigned = api(
        env,
        "POST",
        "/tasks/positive/assign",
        mutation(head["revision"], "assignment", assignee="viewer"),
    )
    assert assigned["revision"] != head["revision"]
    api(env, "POST", "/tasks/positive/draft", draft(assigned["revision"]), status=404)
    req = mutation(
        assigned["revision"],
        "rebind",
        assignee="viewer",
        region=task_request(env)["task"]["region"],
    )
    api(env, "POST", "/tasks/positive/assign", req, status=422)


@pytest.mark.parametrize(
    "suffix", ["?offset=-1", "?offset=0&offset=1", "?all=true", "#fragment"]
)
def test_bounded_routes(env, suffix):
    initialize(env)
    api(env, "GET", "/tasks" + suffix, status=422)


def test_existing_wire_handler_authentication_no_store_and_attachment(env):
    from types import SimpleNamespace

    from src.job_control.http import handler_for
    from tests.review_support import BASE, token
    from tests.test_job_control import MemorySocket

    initialize(env)
    reviewed(env)
    for path in ("/tasks/positive", "/tasks/positive/raw"):
        request = MemorySocket(
            (
                "GET "
                + BASE
                + path
                + " HTTP/1.0\r\nAuthorization: Bearer "
                + token("owner")
                + "\r\n\r\n"
            ).encode()
        )
        handler_for(env.app)(request, ("127.0.0.1", 1), SimpleNamespace())
        output = bytes(request.output)
        assert b"200 OK" in output and b"Cache-Control: no-store" in output
        assert b"X-Content-Type-Options: nosniff" in output
        assert b"token_sha256" not in output and str(env.tmp).encode() not in output
        if path.endswith("raw"):
            assert b"Content-Disposition: attachment" in output
            assert output.endswith('# Ä\r\nprint("hello")\n'.encode())
    code, _, _ = env.app.request("GET", BASE + "/tasks", {})
    assert code == 401
