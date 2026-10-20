"""Owned complete synthetic bundles and real C16 import execution helpers."""

from types import SimpleNamespace

from src.content_store.inventory import InventorySelection
from src.content_store.models import canonical, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.store import ContentStore
from src.job_control.controller import Controller
from src.job_control.http import Application
from src.job_control.import_models import ContentImportPlan
from src.job_control.models import CatalogEntry, Identity, Settings
from tests.content_adapter_support import REVISION, material, srt
from tests.content_store_support import OTHER, OWNER, VIEWER
from tests.index_job_support import api, token
from tests.index_job_support import finish as finish
from tests.test_content_fts import keyfile

IMPORT = "/v1/content/import/"
KEY = "synthetic_import_request_0001"


def setup(tmp_path, kind="code"):
    approved = tmp_path / "approved"
    approved.mkdir(mode=0o700)
    bundle, doc = (srt if kind == "srt" else material)(
        approved / "input", **({} if kind == "srt" else {"kind": kind})
    )
    source_id = bundle.source_id if kind == "srt" else doc.binding.source_id
    content = ContentStore.initialize(tmp_path / "content")
    key = keyfile(tmp_path)
    read = ContentReadSettings(root=content.root, cursor_key_file=key)
    spec = ContentImportPlan(
        schema_version=1,
        content=read,
        allowed_subjects=(OWNER.subject,),
        selection=InventorySelection(
            entry_id="synthetic-import",
            kind="srt" if kind == "srt" else "material",
            source_id=source_id,
            course_id="cs50_python",
            expected_implementation_revision=REVISION,
            bundle=bundle,
        ),
    )
    (approved / "import.v1.json").write_bytes(canonical(spec.model_dump(mode="json")))
    files = {
        p.relative_to(approved).as_posix(): sha256(p.read_bytes())
        for p in approved.rglob("*")
        if p.is_file()
    }
    for p in approved.rglob("*"):
        p.chmod(0o700 if p.is_dir() else 0o600)
    entry = CatalogEntry(
        kind="content_import_bundle",
        root=approved,
        files=files,
        roles={"import": "import.v1.json"},
        course_ids=("cs50_python",),
    )
    settings = Settings(
        root=tmp_path / "jobs",
        catalog={"synthetic-import": entry},
        identities=tuple(
            Identity(**a.model_dump(), token_sha256=sha256(token(a).encode()))
            for a in (OWNER, VIEWER, OTHER)
        ),
        execution_enabled=True,
        import_jobs_enabled=True,
    )
    controller = Controller(settings)
    app = Application(controller, content_settings=read)
    return SimpleNamespace(
        tmp=tmp_path,
        bundle=bundle,
        doc=doc,
        content=content,
        read=read,
        spec=spec,
        entry=entry,
        settings=settings,
        controller=controller,
        app=app,
        trace=[],
    )


def preview(env, key=KEY, *, actor=OWNER, expected=200):
    return api(
        env,
        "POST",
        IMPORT + "preview",
        {"schema_version": 1, "input_ref": "synthetic-import", "request_key": key},
        actor=actor,
        expected=expected,
    )


def create(env, key=KEY, *, p=None, expected=202, start=True):
    p = preview(env, key) if p is None else p
    return api(
        env,
        "POST",
        "/v1/jobs",
        dict(schema_version=1, preview=p["preview"], confirmed=True, start=start),
        key=key,
        expected=expected,
    )


def add_index(env):
    """Preapprove the deterministic selection before import; never auto-build it."""
    from src.content_store.search_models import SearchSettings
    from src.job_control.import_jobs import inspect, verified
    from src.job_control.index_models import IndexJobPlan
    from src.tools_rag.content_index import ContentIndex
    from src.tools_rag.content_index_models import IndexSelection, VersionBinding

    info = inspect(env.entry, env.spec, OWNER, "synthetic-import")
    with verified(env.entry, env.spec) as (_, detail):
        binding = VersionBinding(
            source_id=info.source_id,
            source_version_id=info.source_version_id,
            parsed_version_id=info.parsed_version_id,
            parser_config_id=info.parser_config_id,
            payload_sha256=info.payload_sha256,
            projection_sha256=sha256(detail.projection),
        )
    index = ContentIndex.initialize(
        env.content, env.tmp / "index", cursor_key_file=env.read.cursor_key_file
    )
    search = SearchSettings(schema_version=1, index_root=index.root)
    spec = IndexJobPlan(
        schema_version=1,
        course_id="cs50_python",
        content=env.read,
        search=search,
        selection=IndexSelection(parsed_version_ids=(info.parsed_version_id,)),
        versions=(binding,),
    )
    root = env.tmp / "approved-index"
    root.mkdir(mode=0o700)
    data = canonical(spec.model_dump(mode="json"))
    (root / "index.v1.json").write_bytes(data)
    (root / "index.v1.json").chmod(0o600)
    entry = CatalogEntry(
        kind="index_bundle",
        root=root,
        files={"index.v1.json": sha256(data)},
        roles={"index": "index.v1.json"},
        course_ids=("cs50_python",),
    )
    env.settings = env.settings.model_copy(
        update=dict(
            index_jobs_enabled=True,
            catalog={**env.settings.catalog, "synthetic-index": entry},
        )
    )
    env.controller = Controller(env.settings)
    env.search = search
    env.index = index
    env.index_spec = spec
    env.app = Application(
        env.controller, content_settings=env.read, search_settings=search
    )
    return env
