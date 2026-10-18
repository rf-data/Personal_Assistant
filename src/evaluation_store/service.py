"""Live-authorized review operations under Content -> Evaluation lock order."""

import base64
import json
from datetime import UTC, datetime

from src.content_store.errors import (
    Conflict,
    Forbidden,
    InvalidInput,
    NotFound,
    Unavailable,
)
from src.content_store.index_projection import _load, _project_locked
from src.content_store.models import ArtifactReference, canonical, fingerprint, sha256
from src.content_store.read_views import route
from src.content_store.reader import ContentReader
from src.evaluation_store.models import (
    DatasetBinding,
    EntityReply,
    Region,
    TaskSpec,
    TaskState,
)
from src.evaluation_store.store import EvaluationStore
from src.job_control.models import Principal
from src.model_evaluation.content_retrieval import (
    ContentRelevanceJudgment,
    ContentRetrievalEvaluationSet,
    EvaluationArtifact,
    EvaluationConfig,
    EvaluationScope,
    IndependentReview,
    Query,
    ReviewedBlock,
    ReviewPool,
    VersionEvidence,
    dataset_digest,
    pool_scope,
)
from src.model_evaluation.material_evaluation import GoldDataset, GoldReference
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_rag.content_index_models import VersionBinding

WRITE_PERMISSION = {
    "create": "manage",
    "task": "manage",
    "assign": "manage",
    "draft": "annotate",
    "decision": "confirm",
    "pool": "pool",
    "export": "export",
    "evaluate": "report",
    "accept": "accept",
}


def dumped(model):
    return model.model_dump(mode="json")


def version_binding(pv):
    return VersionBinding(
        source_id=pv.source_id,
        source_version_id=pv.source_version_id,
        parsed_version_id=pv.parsed_version_id,
        parser_config_id=pv.parser_config_id,
        payload_sha256=pv.payload.sha256,
        projection_sha256=pv.projection.sha256,
    )


class ReviewService:
    def __init__(self, settings):
        self.settings = settings
        self.ledger = EvaluationStore(settings.root)
        self.reader = ContentReader(settings.content)
        self.content = self.reader.store

    def _grant(self, actor, dataset_id, permission):
        grant = next(
            (
                g
                for g in self.settings.grants
                if (g.subject, g.dataset_id) == (actor.subject, dataset_id)
            ),
            None,
        )
        if grant is None or "read" not in grant.permissions:
            raise NotFound("review unavailable")
        if permission not in grant.permissions:
            raise Forbidden("review permission required")
        return grant

    @staticmethod
    def _tasks(db, dataset_id):
        prefix = f"{dataset_id}/task/"
        rows = db.execute(
            "SELECT entity FROM heads WHERE substr(entity,1,?)=? ORDER BY entity",
            (len(prefix), prefix),
        ).fetchall()
        return {r[0][len(prefix) :]: EvaluationStore.get(db, r[0]) for r in rows}

    def _visible(self, actor, grant, task):
        if (
            task["value"]["task"]["assignee"] != actor.subject
            and "manage" not in grant.permissions
        ):
            raise NotFound("review unavailable")

    @staticmethod
    def _region(region, loaded):
        if region.parsed_version_id not in loaded:
            raise Conflict("region outside dataset")
        source, sv, pv, parser, blocks, _, _ = loaded[region.parsed_version_id]
        block = next((b for b in blocks if b.block_id == region.block_id), None)
        if (
            block is None
            or region.end > len(block.text)
            or block.text[region.start : region.end] != region.original_region
            or region.text_sha256 != block.text_sha256
            or region.locator not in block.locators
            or region.raw_sha256 not in {r.sha256 for r in sv.manifest.artifacts}
            or (
                region.source_id,
                region.source_version_id,
                region.parser_config_id,
                region.payload_sha256,
                region.projection_sha256,
            )
            != (
                source.source_id,
                sv.source_version_id,
                parser.config_id,
                pv.payload.sha256,
                pv.projection.sha256,
            )
        ):
            raise Conflict("original region binding changed")
        return block

    def call(self, dataset_id, action, actor, request=None, *, item=None, offset=0):
        if not isinstance(actor, Principal):
            raise Forbidden("authenticated principal required")
        # Gateway Identity is a Principal subclass containing a token digest.
        # Never persist/serialize that subclass or compare it to a plain Principal.
        actor = Principal(subject=actor.subject, role=actor.role, courses=actor.courses)
        permission = (
            "export"
            if action == "export_read"
            else WRITE_PERMISSION.get(action, "read")
        )
        grant = self._grant(actor, dataset_id, permission)
        write = action in WRITE_PERMISSION
        if write and not self.settings.writes_enabled:
            raise Forbidden("review writes disabled")
        entity = f"{dataset_id}/dataset"
        # No Content callback while holding a review lock. Recheck this immutable
        # binding under the final transaction, after obtaining Content guards.
        with self.ledger.connection() as db:
            before = self.ledger.get(db, entity)
        if action == "create":
            spec = request.dataset
            if spec.dataset_id != dataset_id:
                raise InvalidInput("dataset identity mismatch")
        elif before:
            spec = DatasetBinding.model_validate(before["value"]).spec
        else:
            raise NotFound("review unavailable")
        with self.content._maintenance(), self.content._connection() as cdb:
            budget = [0]
            loaded = {
                pid: _load(self.content, cdb, pid, actor, False, budget=budget)
                for pid in spec.selection.parsed_version_ids
            }
            sources = {v[0].source_id for v in loaded.values()}
            if not sources.issubset(grant.source_ids):
                raise Forbidden("dataset source scope required")
            origins = {v[0].registration.source_origin for v in loaded.values()}
            if len(origins) != 1:
                raise InvalidInput("mixed corpus origins unsupported")
            origin = "synthetic" if origins == {"synthetic"} else "real"
            if write and origin == "real" and not self.settings.real_reviews_enabled:
                raise Forbidden("real review authorization required")
            with self.ledger.connection(write=write) as db:
                current = self.ledger.get(db, entity)
                if current != before:
                    raise Conflict("dataset changed")
                if current:
                    binding = DatasetBinding.model_validate(current["value"])
                    if (
                        binding.versions
                        != tuple(version_binding(v[2]) for v in loaded.values())
                        or binding.origin != origin
                    ):
                        raise Conflict("dataset version changed")
                else:
                    binding = DatasetBinding(
                        schema_version=1,
                        spec=spec,
                        actor=actor,
                        versions=tuple(version_binding(v[2]) for v in loaded.values()),
                        origin=origin,
                    )
                tasks = self._tasks(db, dataset_id)
                for task in tasks.values():
                    TaskState.model_validate(task["value"])
                    self._region(
                        Region.model_validate(task["value"]["task"]["region"]), loaded
                    )
                result, mime = self._execute(
                    db,
                    cdb,
                    binding,
                    loaded,
                    tasks,
                    grant,
                    action,
                    actor,
                    request,
                    item,
                    offset,
                )
                # Serialize before either guard is released, including mutations.
                if isinstance(result, dict) and "revision" in result:
                    EntityReply.model_validate(result)
                data = result if isinstance(result, bytes) else canonical(result)
                if len(data) > 2 * 1024**2:
                    raise Unavailable("review response limit")
                return data, mime

    def _execute(
        self, db, cdb, binding, loaded, tasks, grant, action, actor, req, item, offset
    ):
        did = binding.spec.dataset_id
        prefix = f"{did}/"
        key = prefix + (
            "dataset"
            if action == "create"
            else "task/" + (req.task.task_id if action == "task" else item)
            if action in {"task", "assign", "draft", "decision"}
            else "pool/" + req.query_id
            if action == "pool"
            else action + "/" + item
            if action in {"export", "evaluate", "accept"}
            else "dataset"
        )
        task = tasks.get(item)
        if action in {
            "get",
            "region",
            "raw",
            "revisions",
            "assign",
            "draft",
            "decision",
        }:
            if task is None:
                raise NotFound("review unavailable")
            self._visible(actor, grant, task)
        if (
            action in {"draft", "decision"}
            and task["value"]["task"]["assignee"] != actor.subject
        ):
            raise Forbidden("assigned reviewer required")
        if action in WRITE_PERMISSION:
            replay = self.ledger.replay(db, key, actor, req)
            if replay:
                return dict(schema_version=1, **replay), "application/json"
        state = self._state(db, did, tasks, loaded)
        if action == "create":
            if self.ledger.get(db, key):
                raise Conflict("dataset already exists")
            value = dumped(binding)
        elif action == "task":
            if len(tasks) >= 64:
                raise Unavailable("task limit")
            if req.task.task_id in tasks:
                raise Conflict("task already exists")
            self._region(req.task.region, loaded)
            if req.task.query_id and req.task.query_id not in {
                q.query_id for q in binding.spec.queries
            }:
                raise InvalidInput("unknown query")
            value = dict(
                schema_version=1,
                task=dumped(req.task),
                status="pending",
                annotation=None,
                review=None,
                assisted=False,
            )
        elif action == "assign":
            if task["value"]["status"] not in {"pending", "needs_clarification"}:
                raise Conflict("assignment requires pending or clarification")
            value = {
                **task["value"],
                "task": {**task["value"]["task"], "assignee": req.assignee},
            }
        elif action == "draft":
            old = task["value"]
            if (old["status"] in {"confirmed", "rejected"}) != req.correction:
                raise Conflict("explicit correction required for terminal review")
            annotation = req.annotation
            if (
                old["task"]["kind"] == "retrieval"
                and (annotation.grade is None or annotation.quality is not None)
            ) or (
                old["task"]["kind"] == "parsing"
                and (annotation.quality is None or annotation.grade is not None)
            ):
                raise InvalidInput("annotation kind mismatch")
            value = {
                **old,
                "status": "in_review",
                "annotation": dumped(annotation),
                "review": None,
                "assisted": old["assisted"] or annotation.mode == "assisted",
            }
        elif action == "decision":
            old = task["value"]
            if old["status"] != "in_review":
                raise Conflict("review must be in progress")
            if req.decision == "confirmed" and (
                old["assisted"] or old["annotation"]["mode"] != "independent_original"
            ):
                raise Forbidden("independent original annotation required")
            review = IndependentReview(
                status="confirmed" if req.decision == "confirmed" else "rejected",
                method="synthetic_reference"
                if binding.origin == "synthetic"
                else "independent_source_annotation",
                reviewer=actor.subject,
                evidence_reference=req.evidence_reference,
                review_date=datetime.now(UTC).date(),
            )
            value = {**old, "status": req.decision, "review": dumped(review)}
            if req.decision == "confirmed":
                self._gold(
                    value, loaded
                )  # Validate existing gold contract before commit.
        elif action == "pool":
            if req.query_id not in {q.query_id for q in binding.spec.queries}:
                raise InvalidInput("unknown query")
            selected = {
                k: t
                for k, t in tasks.items()
                if t["value"]["task"]["query_id"] == req.query_id
            }
            if (
                set(req.reviewed_task_ids) != set(selected)
                or len(req.reviewed_task_ids) != len(set(req.reviewed_task_ids))
                or any(t["value"]["status"] != "confirmed" for t in selected.values())
            ):
                raise Conflict("pool needs all query tasks confirmed")
            projections = self._projections(cdb, binding, actor)
            required = {
                (p.body.parsed_version_id, r.body.block_id)
                for p in projections.values()
                for r in p.body.records
            }
            covered = {
                (
                    t["value"]["task"]["region"]["parsed_version_id"],
                    t["value"]["task"]["region"]["block_id"],
                )
                for t in selected.values()
            }
            if not required.issubset(covered):
                raise Conflict("pool original block coverage incomplete")
            value = dict(
                query_id=req.query_id,
                tasks={k: t["revision"] for k, t in selected.items()},
                coverage_note=req.coverage_note,
                review=dumped(
                    IndependentReview(
                        status="confirmed",
                        method="synthetic_reference"
                        if binding.origin == "synthetic"
                        else "independent_source_annotation",
                        reviewer=actor.subject,
                        evidence_reference=req.evidence_reference,
                        review_date=datetime.now(UTC).date(),
                    )
                ),
            )
        elif action == "export":
            dataset, parsing = self._export(db, cdb, binding, loaded, tasks, actor)
            value = dict(
                state=state,
                dataset_sha256=dataset_digest(dataset),
                parsing_sha256=fingerprint(dumped(parsing)),
                scope_actor=dumped(actor),
            )
        elif action == "evaluate":
            exported = self.ledger.get(db, prefix + "export/" + req.export_id)
            dataset, _ = self._export(db, cdb, binding, loaded, tasks, actor)
            if (
                exported is None
                or exported["value"]["state"] != state
                or exported["value"]["dataset_sha256"] != dataset_digest(dataset)
            ):
                raise Conflict("current export required")
            report = evaluate_retrieval(
                dataset,
                req.results,
                evaluation_config=EvaluationConfig(schema_version=1),
            )
            value = dict(
                state=state,
                export_id=req.export_id,
                export_revision=exported["revision"],
                report=dumped(report),
            )
        elif action == "accept":
            reported = self.ledger.get(db, prefix + "evaluate/" + req.report_id)
            if reported is None or reported["value"]["state"] != state:
                raise Conflict("current evaluation report required")
            report = reported["value"]["report"]["report"]
            if req.decision.startswith("accepted") and (
                report["release_blocker"]
                or report["evaluable_queries"] == 0
                or self._security_blocked(db, did)
            ):
                raise Forbidden("evaluation blocks acceptance")
            if req.decision == "accepted" and any(
                s["status"] != "passed" for s in report["security"]
            ):
                raise Forbidden("security evidence incomplete")
            if req.decision == "accepted_with_limitations" and not req.limitations:
                raise InvalidInput("limitations required")
            value = dict(
                state=state,
                report_id=req.report_id,
                report_revision=reported["revision"],
                report_digest=reported["value"]["report"]["digest"],
                decision=req.decision,
                limitations=list(req.limitations),
                approver=actor.subject,
                time=datetime.now(UTC).isoformat(),
                origin=binding.origin,
                scope_sha256=fingerprint(dumped(binding)),
                automatic_release=False,
            )
        elif action == "list":
            visible = [
                (k, t)
                for k, t in tasks.items()
                if t["value"]["task"]["assignee"] == actor.subject
                or "manage" in grant.permissions
            ]
            return dict(
                schema_version=1,
                items=[dict(task_id=k, **t) for k, t in visible[offset : offset + 10]],
                next_offset=offset + 10 if len(visible) > offset + 10 else None,
            ), "application/json"
        elif action == "get":
            return dict(schema_version=1, **task), "application/json"
        elif action == "revisions":
            events = self.ledger.history(db, prefix + "task/" + item)
            return dict(
                schema_version=1,
                items=events[offset : offset + 10],
                next_offset=offset + 10 if len(events) > offset + 10 else None,
            ), "application/json"
        elif action == "region":
            region = Region.model_validate(task["value"]["task"]["region"])
            sv = loaded[region.parsed_version_id][1]
            ref = next(
                r for r in sv.manifest.artifacts if r.sha256 == region.raw_sha256
            )
            return dict(
                schema_version=1,
                region=dumped(region),
                view="parsed_context_only"
                if task["value"]["task"]["unanchored_finding"]
                else "parsed_codepoint_selection",
                unanchored_finding=task["value"]["task"]["unanchored_finding"],
                original_attachment=route(
                    "sources",
                    region.source_id,
                    "versions",
                    region.source_version_id,
                    "raw",
                    ref.role,
                    str(ref.ordinal),
                ),
            ), "application/json"
        elif action == "raw":
            region = Region.model_validate(task["value"]["task"]["region"])
            ref = next(
                r
                for r in loaded[region.parsed_version_id][1].manifest.artifacts
                if r.sha256 == region.raw_sha256
            )
            if ref.size_bytes > 2 * 1024**2:
                raise Unavailable("use existing bounded Content attachment")
            return self.content._read_blob(ref, cdb), "application/octet-stream"
        elif action == "export_read":
            stored = self.ledger.get(db, prefix + "export/" + item)
            if stored is None or stored["value"]["state"] != state:
                raise Conflict("export stale or unavailable")
            dataset, parsing = self._export(db, cdb, binding, loaded, tasks, actor)
            if stored["value"]["dataset_sha256"] != dataset_digest(dataset):
                raise Conflict("export scope changed")
            return dict(
                schema_version=1,
                snapshot=stored,
                retrieval=dumped(dataset),
                parsing=dumped(parsing),
            ), "application/json"
        elif action in {"report_read", "accept_read"}:
            stored = self.ledger.get(
                db,
                prefix + ("evaluate/" if action == "report_read" else "accept/") + item,
            )
            if stored is None:
                raise NotFound("review unavailable")
            blocked = action == "accept_read" and self._security_blocked(db, did)
            return dict(
                schema_version=1,
                current=stored["value"]["state"] == state
                and not (
                    blocked
                    and stored["value"].get("decision", "").startswith("accepted")
                ),
                blocked_by_security=blocked,
                **stored,
            ), "application/json"
        else:
            raise NotFound("review unavailable")
        if action in {"export", "evaluate", "accept"} and self.ledger.get(db, key):
            raise Conflict("immutable snapshot identity already used")
        result = self.ledger.append(db, key, actor, req, value, dumped(binding))
        return dict(schema_version=1, **result), "application/json"

    @staticmethod
    def _security_blocked(db, did):
        prefix = did + "/evaluate/"
        rows = db.execute(
            "SELECT value FROM heads WHERE substr(entity,1,?)=?", (len(prefix), prefix)
        )
        return any(
            any(
                s["status"] == "failed"
                for s in json.loads(row[0])["report"]["report"]["security"]
            )
            for row in rows
        )

    @staticmethod
    def _state(db, did, tasks, loaded):
        prefix = did + "/pool/"
        pools = {
            r[0]: EvaluationStore.get(db, r[0])["revision"]
            for r in db.execute(
                "SELECT entity FROM heads WHERE substr(entity,1,?)=? ORDER BY entity",
                (len(prefix), prefix),
            )
        }
        return dict(
            tasks={k: t["revision"] for k, t in tasks.items()},
            pools=pools,
            content=fingerprint(
                [
                    dict(source=dumped(v[0]), version=dumped(v[1]), parsed=dumped(v[2]))
                    for v in loaded.values()
                ]
            ),
        )

    @staticmethod
    def _gold(value, loaded):
        spec = TaskSpec.model_validate(value["task"])
        r, a = spec.region, value["annotation"]
        review = IndependentReview.model_validate(value["review"])
        if spec.kind == "retrieval":
            return ContentRelevanceJudgment(
                schema_version=1,
                query_id=spec.query_id,
                gold_target_id=spec.task_id,
                source_id=r.source_id,
                source_version_id=r.source_version_id,
                parsed_version_id=r.parsed_version_id,
                block_id=r.block_id,
                start=r.start,
                end=r.end,
                original_region=r.original_region,
                text_sha256=r.text_sha256,
                region_sha256=sha256(r.original_region.encode()),
                raw_sha256=r.raw_sha256,
                locator=r.locator,
                grade=a["grade"],
                review=review,
            )
        block = next(
            b for b in loaded[r.parsed_version_id][4] if b.block_id == r.block_id
        )
        if spec.unanchored_finding or a["quality"] == "undetermined":
            return None
        if r.start != 0 or r.end != len(block.text):
            raise InvalidInput("C23 parsing gold requires a complete block observation")
        if a["quality"] != "undetermined" and a["expected_content"] is None:
            raise InvalidInput("independent parsing observation required")
        # Undetermined is a confirmed finding, not an evaluable expected text.
        return GoldReference(
            gold_id=spec.task_id,
            entry_id=spec.corpus_entry_id,
            source_id=r.source_id,
            source_version_id=r.source_version_id,
            original_sha256=r.raw_sha256,
            dimension=spec.dimension,
            source_reference="review-task:" + spec.task_id,
            created_date=review.review_date,
            target_pointer=block.payload_pointer,
            expected_content=a["expected_content"],
            expected_locator=r.locator,
            reference_status="confirmed",
            method=review.method,
            reviewer=review.reviewer,
            review_reference=review.evidence_reference,
            review_date=review.review_date,
            notes=(a["quality"], a["comment"], *a["error_categories"]),
        )

    def _projections(self, cdb, binding, actor):
        budget = [0]
        return {
            pid: _project_locked(
                self.content,
                cdb,
                pid,
                actor,
                binding.spec.selection.config,
                budget=budget,
            )
            for pid in binding.spec.selection.parsed_version_ids
        }

    def _export(self, db, cdb, binding, loaded, tasks, actor):
        if actor != binding.actor:
            raise Forbidden("export requires original dataset actor and scope")
        projections = self._projections(cdb, binding, actor)
        versions = []
        evidence_bytes = 0
        for pid, (source, sv, pv, parser, blocks, _, _) in loaded.items():
            refs = {
                r.sha256: ArtifactReference(
                    **r.model_dump(include={"sha256", "size_bytes", "mime_type"})
                )
                for r in (*sv.manifest.artifacts, pv.payload, pv.projection)
            }
            evidence_bytes += sum(r.size_bytes for r in refs.values())
            if (
                evidence_bytes > 1024**2
                or sum(len(v[4]) for v in loaded.values()) > 2000
            ):
                raise Unavailable("bounded export evidence limit")
            versions.append(
                VersionEvidence(
                    source=source,
                    source_version=sv,
                    parsed_version=pv,
                    parser=parser,
                    blocks=blocks,
                    projection=projections[pid],
                    artifacts=tuple(
                        EvaluationArtifact(
                            reference=r,
                            base64_bytes=base64.b64encode(
                                self.content._read_blob(r, cdb)
                            ).decode(),
                        )
                        for r in refs.values()
                    ),
                )
            )
        scope = EvaluationScope(
            actor=actor,
            courses=tuple(sorted({v.source.registration.course_id for v in versions})),
            source_ids=tuple(sorted({v.source.source_id for v in versions})),
            parsed_version_ids=binding.spec.selection.parsed_version_ids,
        )
        gold = [
            self._gold(t["value"], loaded)
            for t in tasks.values()
            if t["value"]["status"] == "confirmed"
        ]
        dataset = ContentRetrievalEvaluationSet(
            schema_version=1,
            dataset_version=binding.spec.dataset_version,
            origin=binding.origin,
            review_status="confirmed"
            if all(t["value"]["status"] == "confirmed" for t in tasks.values())
            and tasks
            else "pending_review",
            corpus_complete=False,
            corpus_reference=binding.spec.corpus_reference,
            projection_config=binding.spec.selection.config,
            retrieval=binding.spec.retrieval,
            queries=tuple(
                Query(query_id=q.query_id, text=q.text, scope=scope)
                for q in binding.spec.queries
            ),
            versions=tuple(versions),
            judgments=tuple(g for g in gold if isinstance(g, ContentRelevanceJudgment)),
            pools=(),
        )
        pools = []
        for q in dataset.queries:
            pool = self.ledger.get(db, f"{binding.spec.dataset_id}/pool/{q.query_id}")
            current = {
                k: t["revision"]
                for k, t in tasks.items()
                if t["value"]["task"]["query_id"] == q.query_id
            }
            if pool and pool["value"]["tasks"] == current:
                p = pool["value"]
                blocks = tuple(
                    ReviewedBlock(
                        parsed_version_id=v.parsed_version.parsed_version_id,
                        block_id=b.block_id,
                        text_sha256=b.text_sha256,
                    )
                    for v in versions
                    for b in v.blocks
                    if any(
                        r.body.block_id == b.block_id for r in v.projection.body.records
                    )
                )
                pools.append(
                    ReviewPool(
                        query_id=q.query_id,
                        pool_complete=True,
                        scope_sha256=pool_scope(dataset, q),
                        reviewed_blocks=blocks,
                        coverage_note=p["coverage_note"],
                        review=IndependentReview.model_validate(p["review"]),
                    )
                )
        dataset = ContentRetrievalEvaluationSet.model_validate(
            {
                **dumped(dataset),
                "pools": [dumped(p) for p in pools],
                "corpus_complete": len(pools) == len(dataset.queries),
            }
        )
        parsing = GoldDataset(
            schema_version=1,
            dataset_version=binding.spec.dataset_version,
            references=tuple(g for g in gold if isinstance(g, GoldReference)),
        )
        return dataset, parsing
