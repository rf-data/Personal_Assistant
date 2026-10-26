"""Isolated verified code bundle and operator-approved index catalog, no real data."""

import json
import time
from types import SimpleNamespace

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.index_projection import project_content_for_index
from src.content_store.models import canonical, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.search_models import SearchSettings
from src.content_store.store import ContentStore
from src.job_control.controller import Controller
from src.job_control.http import Application
from src.job_control.index_models import IndexJobPlan
from src.job_control.models import TERMINAL, CatalogEntry, Identity, Settings
from src.tools_rag.content_index import ContentIndex, _version_binding
from src.tools_rag.content_index_models import IndexSelection
from tests.content_adapter_support import material
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.test_content_fts import keyfile

TEXT = '# 😀 e\u0301 hello\r\n\tprint("hello")\r\nanswer = "hello"\n'
PROCESS = "content_index_build"
INDEX = "/v1/content/index/"


def token(actor):
    return "synthetic_index_token_" + actor.subject + "_000000000000"


def setup(tmp_path):
    bundle, doc = material(tmp_path, "code", code_raw=TEXT.encode())
    content = ContentStore.initialize(tmp_path / "content")
    pv = import_verified_bundle(
        content, verify_material_bundle(bundle), actor=OWNER, request_key="index-jobs"
    ).version
    key = keyfile(tmp_path)
    index = ContentIndex.initialize(content, tmp_path / "index", cursor_key_file=key)
    selection = IndexSelection(parsed_version_ids=(pv.parsed_version_id,))
    content_settings = ContentReadSettings(root=content.root, cursor_key_file=key)
    search_settings = SearchSettings(schema_version=1, index_root=index.root)
    projection = project_content_for_index(content, pv.parsed_version_id, actor=OWNER)
    spec = IndexJobPlan(
        schema_version=1,
        course_id="cs50_python",
        content=content_settings,
        search=search_settings,
        selection=selection,
        versions=(_version_binding(projection),),
    )
    approved = tmp_path / "approved"
    approved.mkdir(mode=0o700)
    (approved / "index.v1.json").write_bytes(canonical(spec.model_dump(mode="json")))
    (approved / "index.v1.json").chmod(0o600)
    entry = CatalogEntry(
        kind="index_bundle",
        root=approved,
        files={"index.v1.json": sha256((approved / "index.v1.json").read_bytes())},
        roles={"index": "index.v1.json"},
        course_ids=("cs50_python",),
    )
    settings = Settings(
        root=tmp_path / "jobs",
        catalog={"synthetic-index": entry},
        identities=tuple(
            Identity(**a.model_dump(), token_sha256=sha256(token(a).encode()))
            for a in [OWNER, VIEWER, OTHER]
        ),
        execution_enabled=True,
        index_jobs_enabled=True,
    )
    controller = Controller(settings)
    app = Application(
        controller, content_settings=content_settings, search_settings=search_settings
    )
    return SimpleNamespace(
        tmp=tmp_path,
        bundle=bundle,
        content=content,
        pv=pv,
        index=index,
        spec=spec,
        settings=settings,
        controller=controller,
        app=app,
        entry=entry,
        trace=[],
    )


def api(env, method, path, value=None, *, actor=OWNER, key=None, expected=200):
    headers = {"Authorization": "Bearer " + token(actor)}
    if key is not None:
        headers["Idempotency-Key"] = key
    response = env.app.request(
        method, path, headers, canonical(value) if value is not None else b""
    )
    try:
        status, raw, mime = response
        data = json.loads(raw)
        assert status == expected, (method, path, status, data)
        env.trace.append(dict(method=method, path=path, status=status, response=data))
        return data
    finally:
        if hasattr(response, "close"):
            response.close()


def preview(env, *, actor=OWNER, resume_of=None, expected=200):
    return api(
        env,
        "POST",
        "/v1/previews",
        dict(
            schema_version=1,
            process_id=PROCESS,
            parameters=dict(
                schema_version=1,
                source_ref="synthetic-index",
                course_id="cs50_python",
                resume_of=resume_of,
            ),
        ),
        actor=actor,
        expected=expected,
    )


def create(env, key="synthetic_index_request_0001", *, resume_of=None, start=True):
    p = preview(env, resume_of=resume_of)
    return api(
        env,
        "POST",
        "/v1/jobs",
        dict(schema_version=1, preview=p, confirmed=True, start=start),
        key=key,
        expected=202,
    )


def finish(env, executor, job, timeout=15):
    until = time.monotonic() + timeout
    while True:
        executor.step()
        current = env.controller.store.get(job["job_id"])
        if current.status in TERMINAL:
            return current
        assert time.monotonic() < until, current
        time.sleep(0.04)


def status(env, *, actor=OWNER, expected=200):
    return api(
        env,
        "GET",
        INDEX + "status?input_ref=synthetic-index",
        actor=actor,
        expected=expected,
    )
