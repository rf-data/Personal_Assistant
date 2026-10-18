"""C23-03: missing acceptance edges of the existing A/B/C contracts."""

import json

import pytest

from src.content_store.adapters import (
    _candidate,
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import (
    Conflict,
    ContentStoreError,
    Unavailable,
    UnverifiedBinding,
)
from src.content_store.models import ProcessingRun, RetryAttempt, sha256
from src.content_store.store import ContentStore
from tests.content_adapter_support import attest, dump, material, srt
from tests.content_operations_support import child, continue_child, launch, line, stop
from tests.content_store_support import OWNER


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        raise AssertionError("C23-03 is offline")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def import_(store, bundle, key="first", **kwargs):
    verifier = (
        verify_srt_bundle
        if hasattr(bundle, "transcript_path")
        else verify_material_bundle
    )
    return import_verified_bundle(
        store, verifier(bundle), actor=OWNER, request_key=key, **kwargs
    )


def runs(store):
    with store._connection() as db:
        return tuple(
            ProcessingRun.model_validate_json(r[0])
            for r in db.execute("SELECT data FROM processing_runs ORDER BY id")
        )


def audit(store, run_id):
    with store._connection() as db:
        return db.execute(
            "SELECT data FROM processing_runs WHERE id=?", (run_id,)
        ).fetchone()[0]


def abandoned(tmp_path, phase, scope):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    process = launch(store, bundle, phase=phase, scope=scope)
    stop(process)
    run = store.inspect_recovery(actor=OWNER)[0]
    assert run.state == ("preparing" if phase == "staging" else "prepared")
    assert (
        store.recover_run(run.run_id, actor=OWNER, action="reject").outcome
        == "rejected"
    )
    return store, bundle, run, audit(store, run.run_id)


@pytest.mark.parametrize("scope", ["raw", "binding"])
@pytest.mark.parametrize("phase", ["staging", "prepared"])
def test_explicit_retry_after_reject_preserves_audit(tmp_path, scope, phase):
    store, bundle, run, old = abandoned(tmp_path, phase, scope)
    with pytest.raises(Unavailable):
        import_(store, bundle)
    retry = RetryAttempt(rejected_run_id=run.run_id, request_key="new-attempt")
    kwargs = {f"{scope}_retry": retry}
    result = import_(ContentStore(store.root, read_only=False), bundle, **kwargs)
    assert result.created
    assert audit(store, run.run_id) == old
    new = next(r for r in runs(store) if r.retry_of == run.run_id)
    assert new.run_id != run.run_id and new.state == "committed"
    assert (
        new.slot_id == run.slot_id
        and new.request_fingerprint == run.request_fingerprint
    )
    assert not import_(store, bundle, **kwargs).created
    # A second explicit attempt deduplicates even after the first succeeded.
    kwargs[f"{scope}_retry"] = RetryAttempt(
        rejected_run_id=run.run_id, request_key="another-attempt"
    )
    assert not import_(store, bundle, "second-publication", **kwargs).created
    with store._connection() as db:
        for table in ("raw_reservations", "source_versions", "parsed_versions"):
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
    assert store.verify_integrity(actor=OWNER).healthy
    assert audit(store, run.run_id) == old


@pytest.mark.parametrize("change", ["key", "source", "slot", "fingerprint", "active"])
def test_retry_cannot_rebind_abandoned_attempt(tmp_path, change):
    store, bundle, run, old = abandoned(tmp_path, "prepared", "raw")
    retry = RetryAttempt(rejected_run_id=run.run_id, request_key="new-attempt")
    verified = _candidate(verify_material_bundle(bundle))
    if change == "key":
        retry = retry.model_copy(update={"request_key": run.request_key})
    elif change == "active":
        # An unknown run cannot authorize a new attempt.
        retry = retry.model_copy(update={"rejected_run_id": "f" * 32})
    if change in {"slot", "fingerprint"}:
        from src.content_store.models import fingerprint

        with pytest.raises(Conflict):
            store._reserve(
                run.source_id,
                OWNER,
                kind="raw",
                slot_id=run.slot_id + ("x" if change == "slot" else ""),
                request_key="ignored",
                request_fingerprint=(
                    "0" * 64
                    if change == "fingerprint"
                    else fingerprint(
                        verified.manifest.artifacts[0].model_dump(
                            exclude={"role", "ordinal"}, mode="json"
                        )
                    )
                ),
                retry=retry,
            )
    elif change == "source":
        other, _ = material(tmp_path / "other", kind="code")
        with pytest.raises(Conflict):
            import_(store, other, raw_retry=retry)
    else:
        with pytest.raises(Conflict):
            import_(store, bundle, raw_retry=retry)
    assert audit(store, run.run_id) == old
    assert not store.list_source_versions(run.source_id, actor=OWNER)


def test_retry_does_not_clear_quarantine(tmp_path):
    store, bundle, run, old = abandoned(tmp_path, "prepared", "raw")
    retry = RetryAttempt(rejected_run_id=run.run_id, request_key="retry")
    first = import_(store, bundle, raw_retry=retry)
    version = store.list_source_versions(first.version.source_id, actor=OWNER)[0]
    path = store.root / version.manifest.artifacts[0].store_key
    data = path.read_bytes()
    path.write_bytes(b"damaged")
    assert store.verify_integrity(actor=OWNER).quarantined_artifacts
    path.write_bytes(data)
    with pytest.raises(ContentStoreError):
        import_(
            store,
            bundle,
            "new-publication",
            raw_retry=RetryAttempt(
                rejected_run_id=run.run_id, request_key="second-retry"
            ),
        )
    assert audit(store, run.run_id) == old
    assert not store.verify_integrity(actor=OWNER).healthy


@pytest.mark.parametrize("scope", ["raw", "binding"])
def test_retry_is_recoverable_after_second_interruption(tmp_path, scope):
    store, bundle, original, old = abandoned(tmp_path, "prepared", scope)
    retry = RetryAttempt(rejected_run_id=original.run_id, request_key="new-attempt")
    options = {f"{scope}_retry": retry.model_dump(mode="json")}
    descriptor = bundle.workspace.parent / "descriptor.json"
    process = child(
        "import",
        store.root,
        descriptor,
        "prepared",
        "first",
        scope,
        json.dumps(options),
    )
    assert line(process) == {"phase": "prepared"}
    stop(process)
    current = store.inspect_recovery(actor=OWNER)[0]
    assert current.retry_of == original.run_id
    assert store.recover_run(current.run_id, actor=OWNER).outcome == "committed"
    assert import_(store, bundle, **{f"{scope}_retry": retry}).created
    assert audit(store, original.run_id) == old
    assert store.verify_integrity(actor=OWNER).healthy


def test_retry_requires_abandonment_and_rechecks_full_gate(tmp_path):
    bundle, _ = material(tmp_path / "input")
    store = ContentStore.initialize(tmp_path / "store")
    held = launch(store, bundle, "prepared", "raw")
    try:
        current = next(
            r for r in runs(store) if r.slot_id.startswith("content_raw_slot_v1:")
        )
        retry = RetryAttempt(rejected_run_id=current.run_id, request_key="too-early")
        with pytest.raises(Conflict):
            import_(store, bundle, raw_retry=retry)
    finally:
        stop(held)
    store.recover_run(current.run_id, actor=OWNER, action="reject")
    retry = RetryAttempt(rejected_run_id=current.run_id, request_key="fresh")
    bundle.receipt_path.write_bytes(b"invalid after abandonment")
    with pytest.raises(UnverifiedBinding):
        import_(store, bundle, raw_retry=retry)
    assert not any(r.retry_of for r in runs(store))


@pytest.mark.parametrize("damage", ["manifest", "intent"])
def test_retry_rejects_damaged_predecessor_evidence(tmp_path, damage):
    store, bundle, run, old = abandoned(tmp_path, "prepared", "raw")
    retry = RetryAttempt(rejected_run_id=run.run_id, request_key="retry")
    current = next(r for r in runs(store) if r.run_id == run.run_id)
    if damage == "manifest":
        from src.content_store.models import canonical

        value = json.loads(old)
        value["manifest"][0]["sha256"] = "0" * 64
        with store._connection(write=True) as db:
            db.execute(
                "UPDATE processing_runs SET data=? WHERE id=?",
                (canonical(value).decode(), run.run_id),
            )
        expected = Conflict
    else:
        (store.root / current.recovery.store_key).write_bytes(b"damaged intent")
        expected = ContentStoreError
    before = audit(store, run.run_id)
    with pytest.raises(expected):
        import_(store, bundle, raw_retry=retry)
    assert audit(store, run.run_id) == before
    assert not any(r.retry_of for r in runs(store))


def test_parsed_reject_new_key_keeps_terminal_attempt(tmp_path):
    store, bundle, original, old = abandoned(tmp_path, "prepared", "parsed")
    with pytest.raises(Unavailable):
        import_(store, bundle, "interrupted")
    assert import_(store, bundle, "explicit-new-publication").created
    assert audit(store, original.run_id) == old
    assert store.verify_integrity(actor=OWNER).healthy


@pytest.mark.parametrize("scope", ["raw", "binding"])
def test_parallel_retry_has_one_winner(tmp_path, scope):
    store, bundle, run, old = abandoned(tmp_path, "prepared", scope)
    descriptor = bundle.workspace.parent / "descriptor.json"
    options = {
        f"{scope}_retry": RetryAttempt(
            rejected_run_id=run.run_id, request_key="retry-one"
        ).model_dump(mode="json")
    }
    held = child(
        "import", store.root, descriptor, "prepared", "held", scope, json.dumps(options)
    )
    try:
        assert line(held) == {"phase": "prepared"}
        options[f"{scope}_retry"]["request_key"] = "retry-two"
        other = child(
            "import",
            store.root,
            descriptor,
            "none",
            "other",
            scope,
            json.dumps(options),
        )
        assert line(other)["error"] in {"busy", "unavailable"}
        other.communicate(timeout=10)
        first = continue_child(held)
        assert first["created"]
        options = {k: RetryAttempt.model_validate(v) for k, v in options.items()}
        second = import_(store, bundle, "other", **options)
        assert (
            not second.created and second.version.parsed_version_id == first["version"]
        )
        assert store.verify_integrity(actor=OWNER).healthy
        assert audit(store, run.run_id) == old
    finally:
        if held.poll() is None:
            stop(held)


def test_verified_new_raw_version_and_restarts(tmp_path):
    from src.tools_materials.parse_code import parse_code

    bundle, doc = material(tmp_path / "first", kind="code")
    store = ContentStore.initialize(tmp_path / "store")
    first = import_(store, bundle)
    raw, payload, receipt = (
        getattr(bundle, p).read_bytes()
        for p in ("raw_path", "normalized_path", "receipt_path")
    )
    other, _ = material(tmp_path / "second", kind="code")
    changed = raw + b'print("second source revision")\n'
    other.raw_path.write_bytes(changed)
    new_doc, _ = parse_code(doc.binding, changed, doc.parser)
    directory = other.raw_path.parent.parent
    normalized = directory / new_doc.document_id.split(":")[1] / "normalized.v1.json"
    dump(normalized, new_doc.model_dump(mode="json"))
    other = other.model_copy(update={"normalized_path": normalized})
    r = json.loads(other.receipt_path.read_bytes())
    r.update(
        raw_sha256=sha256(changed),
        normalized_sha256=sha256(normalized.read_bytes()),
        normalized_path=normalized.relative_to(other.workspace).as_posix(),
    )
    dump(other.receipt_path, r)
    attest(other)
    second = import_(ContentStore(store.root, read_only=False), other, "new-raw")
    assert second.version.source_id == first.version.source_id
    assert second.version.source_version_id != first.version.source_version_id
    assert second.version.parsed_version_id != first.version.parsed_version_id
    reopened = ContentStore(store.root)
    assert (
        reopened.read_raw_artifact(first.version.source_id, sha256(raw), actor=OWNER)
        == raw
    )
    assert (
        reopened.read_parsed_payload(first.version.parsed_version_id, actor=OWNER)
        == payload
    )
    assert (
        reopened.read_version_artifact(
            first.version.parsed_version_id, "receipt", actor=OWNER
        )
        == receipt
    )
    assert not import_(store, bundle).created
    assert not import_(store, bundle, "other-key").created


@pytest.mark.parametrize("kind", ["material", "srt"])
def test_same_bytes_false_origin_conflicts(tmp_path, kind):
    bundle, _ = (
        material(tmp_path / "input") if kind == "material" else srt(tmp_path / "input")
    )
    store = ContentStore.initialize(tmp_path / "store")
    first = import_(store, bundle)
    if kind == "material":
        for path in (bundle.normalized_path, bundle.receipt_path):
            value = json.loads(path.read_bytes())
            value["binding"]["source_origin"] = "official"
            dump(path, value)
        value = json.loads(bundle.plan_path.read_bytes())
        value["materials"][0]["source_origin"] = "official"
        dump(bundle.plan_path, value)
        value = json.loads(bundle.receipt_path.read_bytes())
        value["normalized_sha256"] = sha256(bundle.normalized_path.read_bytes())
        dump(bundle.receipt_path, value)
        attest(bundle)
    else:
        bundle = bundle.model_copy(update={"source_origin": "official"})
    with pytest.raises(Conflict):
        import_(store, bundle, "false-origin")
    assert (
        ContentStore(store.root)
        .get_source(first.version.source_id, actor=OWNER)
        .source_origin
        == "synthetic"
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_id",
        "lecture_ids",
        "section_keys",
        "parser_version",
        "revision",
        "evidence",
    ],
)
def test_material_binding_failures(tmp_path, field):
    bundle, _ = material(tmp_path)
    if field in {"revision", "evidence"}:
        value = json.loads(bundle.implementation_path.read_bytes())
        value["implementation_revision" if field == "revision" else "source_id"] = (
            "wrong"
        )
        dump(bundle.implementation_path, value)
    elif field == "parser_version":
        value = json.loads(bundle.receipt_path.read_bytes())
        value["parser"]["version"] = "999"
        dump(bundle.receipt_path, value)
        attest(bundle)
    else:
        value = json.loads(bundle.normalized_path.read_bytes())
        if field == "source_id":
            value["binding"]["resource"]["resource_id"] = "resource:wrong"
        elif field == "lecture_ids":
            value["binding"]["lecture_ids"] = ["resource:wrong"]
        else:
            value["binding"]["resource"]["section_keys"] = ["99"]
        dump(bundle.normalized_path, value)
    with pytest.raises(UnverifiedBinding):
        verify_material_bundle(bundle)
