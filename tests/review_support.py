"""Actual gateway and verified synthetic B bundles; never real reviewer identities."""

import json
from types import SimpleNamespace

from src.content_store.models import fingerprint, sha256
from src.content_store.read_models import ContentReadSettings
from src.evaluation_store.models import ReviewGrant, ReviewSettings
from src.evaluation_store.store import EvaluationStore
from src.job_control.controller import Controller
from src.job_control.http import Application
from src.job_control.models import Identity, Settings
from tests.content_store_support import OWNER, VIEWER
from tests.test_content_fts import hits, make_index

BASE = "/v1/evaluation/datasets/synthetic-review"
PERMISSIONS = (
    "read",
    "manage",
    "annotate",
    "confirm",
    "pool",
    "export",
    "report",
    "accept",
)


def token(subject):
    return "synthetic_review_session_token_" + subject + "_000000000"


def gateway(settings, jobs_root):
    identities = tuple(
        Identity(**p.model_dump(), token_sha256=sha256(token(p.subject).encode()))
        for p in (OWNER, VIEWER)
    )
    controller = Controller(Settings(root=jobs_root, identities=identities))
    return Application(
        controller, content_settings=settings.content, review_settings=settings
    )


def setup_review(tmp_path, kind="code", *, code_raw=None):
    if code_raw is None:
        index, content, pv, doc, selection, receipt, key = make_index(tmp_path, kind)
    else:
        from src.content_store.adapters import (
            import_verified_bundle,
            verify_material_bundle,
        )
        from src.content_store.store import ContentStore
        from src.tools_rag.content_index import ContentIndex
        from src.tools_rag.content_index_models import IndexSelection
        from tests.content_adapter_support import material
        from tests.test_content_fts import keyfile

        bundle, doc = material(tmp_path, "code", code_raw=code_raw)
        content = ContentStore.initialize(tmp_path / "content")
        pv = import_verified_bundle(
            content, verify_material_bundle(bundle), actor=OWNER, request_key="first"
        ).version
        key = keyfile(tmp_path)
        index = ContentIndex.initialize(
            content, tmp_path / "index", cursor_key_file=key
        )
        selection = IndexSelection(parsed_version_ids=(pv.parsed_version_id,))
        index.build(selection, actor=OWNER)
    EvaluationStore.initialize(tmp_path / "reviews")
    settings = ReviewSettings(
        schema_version=1,
        root=tmp_path / "reviews",
        content=ContentReadSettings(root=content.root, cursor_key_file=key),
        writes_enabled=True,
        grants=(
            ReviewGrant(
                schema_version=1,
                subject=OWNER.subject,
                dataset_id="synthetic-review",
                source_ids=(pv.source_id,),
                permissions=PERMISSIONS,
            ),
        ),
    )
    page = hits(index)
    config = dict(
        method="lexical",
        ranking_schema="source_rrf_v1",
        backend_fingerprint="b" * 64,
        index_generation=page.index_generation,
        k=4,
        adapter="c24_search_result_page_v1",
    )
    config["configuration_fingerprint"] = fingerprint(config)
    spec = dict(
        schema_version=1,
        dataset_id="synthetic-review",
        dataset_version="synthetic-review-v1",
        selection=selection.model_dump(mode="json"),
        retrieval=config,
        queries=[dict(schema_version=1, query_id="query-1", text="hello")],
        corpus_reference="Independent synthetic constants; not human real review",
    )
    return SimpleNamespace(
        app=gateway(settings, tmp_path / "jobs"),
        settings=settings,
        content=content,
        pv=pv,
        doc=doc,
        index=index,
        page=page,
        spec=spec,
        tmp=tmp_path,
        trace=[],
    )


def api(env, method, path="", value=None, *, actor=OWNER, status=200):
    target = path if path.startswith("/v1/") else BASE + path
    body = json.dumps(value, ensure_ascii=False).encode() if value is not None else b""
    response = env.app.request(
        method, target, {"Authorization": "Bearer " + token(actor.subject)}, body
    )
    code, raw, mime = response
    parsed = json.loads(raw) if mime == "application/json" else raw
    assert code == status, (target, code, parsed)
    if mime == "application/json":
        env.trace.append(
            dict(
                method=method, route=target, request=value, status=code, response=parsed
            )
        )
    return parsed


def mutation(revision=None, key="first", **fields):
    return dict(
        schema_version=1,
        expected_revision=revision,
        idempotency_key=key,
        reason="Explicit synthetic test action",
        **fields,
    )


def initialize(env):
    return api(env, "POST", value=mutation(dataset=env.spec))


def region(env, block, text, start):
    pv = env.pv
    return dict(
        schema_version=1,
        source_id=pv.source_id,
        source_version_id=pv.source_version_id,
        parsed_version_id=pv.parsed_version_id,
        block_id=block.block_id,
        text_sha256=block.text_sha256,
        raw_sha256=block.locators[0].raw_artifact_sha256,
        parser_config_id=pv.parser_config_id,
        payload_sha256=pv.payload.sha256,
        projection_sha256=pv.projection.sha256,
        locator=block.locators[0].model_dump(mode="json"),
        start=start,
        end=start + len(text),
        original_region=text,
    )


def task_request(
    env,
    task_id="positive",
    block=None,
    text="hello",
    start=7,
    kind="retrieval",
    assignee="owner",
):
    block = (
        block
        or env.content.list_content_blocks(env.pv.parsed_version_id, actor=OWNER).items[
            1
        ]
    )
    return mutation(
        task=dict(
            schema_version=1,
            task_id=task_id,
            kind=kind,
            assignee=assignee,
            region=region(env, block, text, start),
            query_id="query-1" if kind == "retrieval" else None,
            corpus_entry_id="synthetic-code-entry" if kind == "parsing" else None,
        )
    )


def draft(
    revision,
    key="draft",
    *,
    grade=3,
    correction=False,
    mode="independent_original",
    **fields,
):
    return mutation(
        revision,
        key,
        annotation=dict(
            schema_version=1,
            mode=mode,
            grade=grade,
            comment="Handwritten synthetic original observation",
            **fields,
        ),
        correction=correction,
    )


def confirm(env, task_id, head, key="confirm", actor=OWNER):
    return api(
        env,
        "POST",
        f"/tasks/{task_id}/decision",
        mutation(
            head["revision"],
            key,
            decision="confirmed",
            evidence_reference="synthetic-independent-original-test-evidence",
        ),
        actor=actor,
    )


def reviewed(env, task_id="positive", **kw):
    head = api(env, "POST", "/tasks", task_request(env, task_id, **kw))
    head = api(
        env,
        "POST",
        f"/tasks/{task_id}/draft",
        draft(head["revision"], grade=0 if task_id == "negative" else 3),
    )
    return confirm(env, task_id, head)


def complete_pool(env):
    return api(
        env,
        "POST",
        "/pool",
        mutation(
            query_id="query-1",
            reviewed_task_ids=["positive", "negative"],
            coverage_note="All original synthetic code lines examined independently",
            evidence_reference="synthetic-pool-coverage-test-record",
        ),
    )
