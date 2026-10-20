"""Approved catalog selection -> existing builder, always through the C16 worker."""

from contextlib import contextmanager

from src.content_store.errors import (
    ContentStoreError,
    Forbidden,
    IntegrityError,
    NotFound,
)
from src.content_store.models import canonical, sha256
from src.content_store.store import ContentStore
from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.index_models import (
    IndexInput,
    IndexJobPlan,
    IndexJobReceipt,
    IndexStatus,
)
from src.job_control.models import TERMINAL, Principal
from src.job_control.store import Conflict, Store
from src.tools_materials.quality import _json
from src.tools_rag.content_index import ContentIndex, _version_binding

PROCESS = "content_index_build"


def plan(entry, job_root):
    spec = IndexJobPlan.model_validate(
        _json(verified_files(entry)[entry.roles["index"]])
    )
    if (
        entry.kind != "index_bundle"
        or entry.course_ids != (spec.course_id,)
        or len(entry.files) != 1
    ):
        raise ValueError("index catalog scope mismatch")
    for p in (spec.content.root, spec.search.index_root, spec.content.cursor_key_file):
        if p.is_relative_to(job_root) or job_root.is_relative_to(p):
            raise ValueError("job and index/content configuration must be separate")
    return spec


def open_index(spec):
    return ContentIndex(
        ContentStore(spec.content.root),
        spec.search.index_root,
        cursor_key_file=spec.content.cursor_key_file,
    )


def authorize(spec, actor, *, owner=False):
    index = open_index(spec)
    with index.store._maintenance(), index.store._connection() as db:
        for sid in spec.source_ids:
            source = index.store._authorize(db, sid, actor, write=owner)
            if source.registration.course_id != spec.course_id:
                raise Forbidden("index course mismatch")
    return index


def verify(spec, actor, *, owner=True):
    index = authorize(spec, actor, owner=owner)
    with (
        index.files.lock(".content-index-catalog.lock"),
        index.store._maintenance(),
        index.store._connection() as db,
    ):
        projections, _, _, _ = index._export(db, spec.selection, actor, owner=owner)
        if tuple(_version_binding(p) for p in projections) != spec.versions:
            raise IntegrityError("pinned index versions changed")
        if owner:
            _, _, active = index._active()
            if active is not None:
                index._ownership(db, tuple(f.source_id for f in active.files), actor)
    return index


def prepare(entry, course, actor, job_root, resume_of=None):
    if actor.role != "operator":
        raise PermissionError("operator required for index preview")
    spec = plan(entry, job_root)
    if spec.course_id != course:
        raise PermissionError("index job course mismatch")
    if resume_of:
        store = Store(job_root)
        prior = store.get(resume_of)
        if (
            prior.process_id != PROCESS
            or prior.initiated_by != actor.subject
            or prior.status not in TERMINAL
            or prior.parameters["course_id"] != course
            or store.entry(resume_of) != entry
        ):
            raise Conflict("explicit index retry identity mismatch")
    verify(spec, actor)
    return spec


def authorize_job(store, job, actor):
    spec = plan(store.entry(job.job_id), store.root)
    authorize(spec, actor)


def input_view(ref, spec, actor):
    can_build = False
    index = authorize(spec, actor)
    if actor.role == "operator":
        try:
            with (
                index.files.lock(".content-index-catalog.lock"),
                index.store._maintenance(),
                index.store._connection() as db,
            ):
                index._ownership(db, spec.source_ids, actor)
                _, _, active = index._active()
                if active is not None:
                    index._ownership(
                        db, tuple(f.source_id for f in active.files), actor
                    )
            can_build = True
        except Forbidden:
            pass
    return IndexInput(
        input_ref=ref,
        course_id=spec.course_id,
        source_ids=spec.source_ids,
        parsed_version_ids=spec.selection.parsed_version_ids,
        selection_sha256=spec.selection_sha256,
        can_build=can_build,
    )


def _public_receipt(job, spec, index, active, manifest, outcome):
    return IndexJobReceipt(
        job_id=job.job_id,
        build_id=active.build_id,
        outcome=outcome,
        index_generation=index._hmac("index-generation-v1", active.generation_id),
        source_ids=spec.source_ids,
        parsed_version_ids=spec.selection.parsed_version_ids,
        selection_sha256=spec.selection_sha256,
        record_set_sha256=manifest.basis.record_set_sha256,
        record_count=manifest.record_count,
    )


def run(store, job, entry, output):
    actor = Principal(
        subject=job.initiated_by,
        role="operator",
        courses=(job.parameters["course_id"],),
    )
    spec = plan(entry, store.root)
    index = verify(spec, actor)
    prior_id = job.parameters["resume_of"]
    if prior_id:
        # Verify terminal owner/request binding against original approved catalog;
        # snapshot paths differ, the byte/hash intent must not.
        original = store.entry(job.job_id)
        prepare(original, spec.course_id, actor, store.root, prior_id)
        with (
            index.files.lock(".content-index-catalog.lock"),
            index.store._maintenance(),
            index.store._connection() as db,
        ):
            _, active, manifest = index._active()
            if active is not None and active.build_id == prior_id.removeprefix("job_"):
                if (
                    manifest.basis.selection != spec.selection
                    or manifest.basis.versions != spec.versions
                ):
                    raise IntegrityError("retry activation binding mismatch")
                # Recheck every partition before acknowledging response loss.
                projections, records, _, _ = index._export(
                    db, spec.selection, actor, owner=True
                )
                import time

                from src.content_store.index_models import record_set_sha256

                if record_set_sha256(records) != manifest.basis.record_set_sha256:
                    raise IntegrityError("retry record set mismatch")
                for proof in manifest.files:
                    from src.tools_rag.content_index import _gen_path

                    data = index.files.read(_gen_path(active) + "/" + proof.name)
                    if len(data) != proof.size_bytes or sha256(data) != proof.sha256:
                        raise IntegrityError("retry partition mismatch")
                    index._verify_partition(
                        data,
                        [r for r in records if r.body.source_id == proof.source_id],
                        time.monotonic() + 2,
                        source_id=proof.source_id,
                        generation_id=active.generation_id,
                    )
                receipt = _public_receipt(
                    job, spec, index, active, manifest, "already_active"
                )
                _save(output, receipt)
                return
    # No adoption/resume of partial staging. New explicit C16 request => new build ID.
    index.build(spec.selection, actor=actor, build_id=job.job_id.removeprefix("job_"))
    with index.files.lock(".content-index-catalog.lock"):
        _, active, manifest = index._active()
        if active is None or active.build_id != job.job_id.removeprefix("job_"):
            raise IntegrityError("job activation no longer current")
        receipt = _public_receipt(job, spec, index, active, manifest, "activated")
        _save(output, receipt)


def _save(output, receipt):
    import os

    with output.open("xb") as stream:
        stream.write(canonical(receipt.model_dump(mode="json")))
        stream.flush()
        os.fsync(stream.fileno())
    output.chmod(0o600)


@contextmanager
def status(controller, ref, actor, *, offset=0, limit=10):
    """Keep the same content guard through a redacted status response."""
    entry = controller.settings.catalog.get(ref)
    if entry is None or entry.kind != "index_bundle":
        raise NotFound()
    spec = plan(entry, controller.settings.root)
    index = authorize(spec, actor)
    view = input_view(ref, spec, actor)
    # Read job DB before any index/content locks. Never nest C16 DB inside Content.
    all_jobs = []
    for job in controller.store.all():
        if job.process_id != PROCESS or job.input_refs != (ref,):
            continue
        try:
            controller.allowed(actor, job)
        except (PermissionError, KeyError):
            continue
        all_jobs.append(job)
    latest = all_jobs[0] if all_jobs else None
    jobs = tuple(all_jobs[offset : offset + limit + 1])
    receipt = None
    for job in jobs[:limit]:
        if job.artifact_refs:
            artifact = job.artifact_refs[0]
            data = read_file(
                safe_path(
                    controller.store.directory(job.job_id),
                    "results/" + job.parameters["output_name"] + ".json",
                )
            )
            if sha256(data) != artifact.sha256 or len(data) != artifact.size_bytes:
                raise IntegrityError("job receipt bytes mismatch")
            receipt = IndexJobReceipt.model_validate(_json(data))
            if receipt.job_id != job.job_id:
                raise IntegrityError("job receipt identity mismatch")
            if receipt.selection_sha256 == spec.selection_sha256:
                break
            receipt = None
    # Retain source authorization while encoding/sending status, including errors.
    with (
        index.files.lock(".content-index-catalog.lock"),
        index.store._maintenance(),
        index.store._connection() as db,
    ):
        for sid in spec.source_ids:
            index.store._authorize(db, sid, actor)
        _, active, manifest = index._active()
        state = "not_indexed" if active is None else "stale"
        generation = None
        activation = "undetermined"
        if latest:
            activation = (
                "committed"
                if active
                and (
                    active.build_id == latest.job_id.removeprefix("job_")
                    or receipt
                    and receipt.job_id == latest.job_id
                    and receipt.build_id == active.build_id
                )
                else "not_committed"
                if active is None
                else "undetermined"
            )
        if (
            manifest is not None
            and manifest.basis.selection.config == spec.selection.config
            and all(v in manifest.basis.versions for v in spec.versions)
        ):
            try:
                import time

                from src.tools_rag.content_index import QUERY_SECONDS, SLOTS

                if not SLOTS.acquire(blocking=False):
                    raise IntegrityError("status query capacity")
                try:
                    # Reuse the actual source-local retrieval verifier, not a
                    # weaker metadata-only assertion that an index is active.
                    page = index._search(
                        db,
                        "__index_status_probe__",
                        '"__index_status_probe__"',
                        actor,
                        spec.course_id,
                        spec.source_ids,
                        None,
                        1,
                        None,
                        "0" * 64,
                        "0" * 64,
                        time.monotonic() + QUERY_SECONDS,
                    )
                    generation = index._hmac(
                        "index-generation-v1", active.generation_id
                    )
                    if page.index_generation != generation:
                        raise IntegrityError("status generation changed")
                    state = "active"
                finally:
                    SLOTS.release()
            except ContentStoreError:
                state, generation = "blocked", None
        if state == "not_indexed" and latest:
            if latest.status in {"queued", "running", "cancel_requested"}:
                state = "building"
            elif latest.status in {"failed", "interrupted", "cancelled"}:
                state = "failed"
        if any(
            not db.execute(
                "SELECT 1 FROM parsed_versions WHERE id=? AND source_id=? AND source_version_id=? AND state='published'",
                (v.parsed_version_id, v.source_id, v.source_version_id),
            ).fetchone()
            for v in spec.versions
        ):
            state, generation = "blocked", None
        answer = IndexStatus(
            input=view,
            state=state,
            index_generation=generation,
            jobs=jobs[:limit],
            next_offset=offset + limit if len(jobs) > limit else None,
            receipt=receipt,
            latest_activation=activation,
        )
        yield answer


def guarded_reply(controller, actor, result, status_code, *, scoped_job=None):
    """Protect index-job metadata on the existing generic C16 routes as well."""
    import time
    from contextlib import ExitStack

    from src.content_store.search_http import SearchReply
    from src.job_control.http import encode
    from src.job_control.models import Job

    candidates = (
        [result]
        if isinstance(result, Job)
        else list(result)
        if isinstance(result, (tuple, list))
        else []
    )
    if scoped_job is not None:
        candidates.append(scoped_job)
    jobs = {
        j.job_id: j
        for j in candidates
        if isinstance(j, Job) and j.process_id in {PROCESS, "content_import"}
    }
    if not jobs:
        return None
    # All C16 reads happen before acquiring Content locks.
    from src.job_control import import_jobs

    specs = []
    for jid, job in jobs.items():
        if job.process_id == "content_import":
            spec = import_jobs.plan(
                controller.store.entry(jid), controller.settings.root
            )
        else:
            spec = plan(controller.store.entry(jid), controller.settings.root)
        specs.append((spec, job))
    stack = ExitStack()
    try:
        groups = {}
        import_specs = []
        for spec, job in specs:
            sources = groups.setdefault(spec.content.root, set())
            if job.process_id == "content_import":
                import_specs.append((spec, job))
            else:
                sources.update(spec.source_ids)
        for root, sources in sorted(groups.items()):
            content = ContentStore(root)
            stack.enter_context(content._maintenance())
            db = stack.enter_context(content._connection())
            for spec, job in import_specs:
                if spec.content.root == root:
                    import_jobs.authorize(spec, actor, db, job_owner=job.initiated_by)
            for sid in sorted(sources):
                content._authorize(db, sid, actor)
        deadline = time.monotonic() + 2
        return SearchReply(
            status_code, encode(result), deadline=deadline, stack=stack.pop_all()
        )
    finally:
        stack.close()
