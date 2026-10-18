"""Optional ContentRecord adapter on the existing lifecycle and retrieval guard.

Only fake execution is enabled in A. Real E5/Qdrant and hybrid require B review.
"""

import math
import re
import time

from pydantic import ValidationError

from src.content_store.errors import (
    Forbidden,
    IntegrityError,
    InvalidInput,
    Unavailable,
)
from src.content_store.index_models import record_set_sha256
from src.content_store.models import (
    canonical,
    checked_actor,
    fingerprint,
    sha256,
    snapshot,
)
from src.model_discovery.cs50 import deterministic_id
from src.tools_materials.quality import _json
from src.tools_rag.content_index import ContentIndex, _version_binding, _versioned
from src.tools_rag.content_index_files import initialize_root
from src.tools_rag.content_index_models import (
    BuildReceipt,
    GenerationBasis,
    VectorScoreComponent,
)
from src.tools_rag.content_vector_models import (
    ContentCollection,
    ContentVectorConfig,
    ContentVectorPayload,
    ContentVectorPlan,
    VectorPartition,
)
from src.tools_rag.content_vector_transport import FakeContentTransport
from src.tools_rag.cs50_embeddings import FakeEmbedder, checked_vectors, offset_windows
from src.tools_rag.cs50_ingestion import UploadState, VectorArtifact, validate_vectors


def collection_for(config, generation_id, source_id):
    return ContentCollection(
        **(
            config.model_dump(mode="json")
            | dict(
                name=config.name + "_" + fingerprint([generation_id, source_id])[:32],
                source_id=source_id,
                generation_id=generation_id,
                payload_schema_sha256=fingerprint(
                    ContentVectorPayload.model_json_schema()
                ),
            )
        )
    )


def map_content(records, collection, embedder):
    """Only called on authoritative C24-02 records inside the shared adapter."""
    units = []
    for record in records:
        b = record.body
        if b.source_id != collection.source_id:
            raise IntegrityError("record source conflict")
        windows = offset_windows(b.search_text, embedder)
        previous = 0
        for start, end in windows:
            if start < previous or b.search_text[previous:start].strip():
                raise IntegrityError("vector child coverage conflict")
            text = b.search_text[start:end]
            units.append(
                ContentVectorPayload(
                    schema_version=1,
                    adapter_version="content_vector_adapter_v1",
                    payload_schema="content_vector_payload_v1",
                    index_record_id=record.index_record_id,
                    source_id=b.source_id,
                    source_version_id=b.source_version_id,
                    parsed_version_id=b.parsed_version_id,
                    block_id=b.block_id,
                    record_start=b.start,
                    record_end=b.end,
                    child_start=b.start + start,
                    child_end=b.start + end,
                    offset_unit="unicode_codepoint",
                    text_sha256=b.text_sha256,
                    child_text=text,
                    child_text_sha256=sha256(text.encode()),
                    projection_fingerprint=b.projection_sha256,
                    payload_sha256=b.payload_sha256,
                    embedding_model=collection.embedding.model,
                    embedding_revision=collection.embedding.revision,
                    embedding_config_fingerprint=collection.embedding.version,
                    collection_name=collection.name,
                    collection_contract_id=collection.contract_id,
                    generation_id=collection.generation_id,
                )
            )
            previous = end
            if len(units) > 4096:
                raise Unavailable("vector child capacity")
        if b.search_text[previous:].strip():
            raise IntegrityError("vector child coverage conflict")
    return ContentVectorPlan(
        schema_version=1,
        collection=collection,
        record_set_sha256=record_set_sha256(records),
        units=tuple(units),
    )


class ContentVectorIndex(ContentIndex):
    IDENTITY = "content-vectors-fake-v1"
    METHOD = "vector"
    RANKING = "cosine_l2_v1"
    CURSOR_DOMAIN = b"content-vector-cursor-v1\0"

    def __init__(
        self,
        store,
        index_root,
        *,
        cursor_key_file,
        config,
        embedder,
        transport,
        _synthetic=False,
    ):
        if not isinstance(config, ContentVectorConfig):
            raise InvalidInput("typed ContentRecord vector configuration required")
        self.config = snapshot(config)
        if (
            type(embedder) is not FakeEmbedder
            or type(transport) is not FakeContentTransport
            or self.config.embedding.provider != "fake"
        ):
            raise Forbidden("real vector pilot blocked pending explicit B approval")
        if (
            embedder.config != self.config.embedding
            or self.config.embedding.dimension > 128
        ):
            raise InvalidInput("vector model/dimension conflict")
        self.embedder, self.transport = embedder, transport
        self.last_upload = None
        super().__init__(
            store, index_root, cursor_key_file=cursor_key_file, _synthetic=_synthetic
        )

    @classmethod
    def initialize(
        cls,
        store,
        index_root,
        *,
        cursor_key_file,
        config,
        embedder,
        transport,
        _synthetic=False,
    ):
        # Validate all configuration/key/purpose gates using an existing empty FTS root
        # is deliberately avoided: no temporary root adoption or implicit model load.
        from pathlib import Path

        from src.content_store.artifacts import explicit_root
        from src.content_store.reader import private_bytes
        from src.content_store.store import ContentStore

        if not isinstance(store, ContentStore):
            raise InvalidInput("typed ContentStore required")

        if (
            not isinstance(config, ContentVectorConfig)
            or config.embedding.provider != "fake"
            or type(embedder) is not FakeEmbedder
            or type(transport) is not FakeContentTransport
        ):
            raise Forbidden("real vector pilot blocked pending explicit B approval")
        config = snapshot(config)
        if config.embedding != embedder.config or config.embedding.dimension > 128:
            raise InvalidInput("vector configuration conflict")
        if store._purpose != ("synthetic_test" if _synthetic else "content"):
            raise Forbidden("index store purpose denied")
        root = explicit_root(index_root)
        key = Path(cursor_key_file)
        if (
            not key.is_absolute()
            or ".." in key.parts
            or any(
                key.is_relative_to(p)
                for p in (root, store.root, Path(__file__).resolve().parents[2])
            )
            or not 32 <= len(private_bytes(key, 64)) <= 64
        ):
            raise InvalidInput("explicit separate private cursor key required")
        initialize_root(root, store.root, store._purpose, identity=cls.IDENTITY)
        return cls(
            store,
            root,
            cursor_key_file=key,
            config=config,
            embedder=embedder,
            transport=transport,
            _synthetic=_synthetic,
        )

    def _backend_spec(self):
        if (
            type(self.embedder) is not FakeEmbedder
            or type(self.transport) is not FakeContentTransport
        ):
            raise Forbidden("real vector pilot blocked pending explicit B approval")
        if self.embedder.config != self.config.embedding:
            raise Unavailable("vector embedding configuration changed")
        return dict(
            name="content_vector_fake_v1",
            backend_set="vector",
            collection_config=self.config.contract_id,
            model=self.config.embedding.model,
            revision=self.config.embedding.revision,
            embedding=self.config.embedding.version,
            score="cosine_l2_v1",
            ranking=self.RANKING,
        )

    def resume(self, build_id, *, actor):
        """New verified attempt, bound to one prior incomplete build's intent."""
        actor = checked_actor(actor)
        if not isinstance(build_id, str) or not re.fullmatch("[0-9a-f]{32}", build_id):
            raise InvalidInput("explicit vector build identity required")
        with (
            self.files.lock(".content-index-build.lock", exclusive=True),
            self.files.lock(".content-index-catalog.lock"),
        ):
            prior = BuildReceipt.model_validate(
                _versioned(self.files.read("attempts/" + build_id + "/status.json"))
            )
            if actor.subject != prior.actor:
                raise Forbidden("vector resume ownership denied")
            if not prior.generation_id or prior.state not in {
                "building",
                "verifying",
                "ready",
                "failed",
            }:
                raise InvalidInput("vector resume intent unavailable")
            with self.store._maintenance(), self.store._connection() as db:
                self._ownership(db, prior.source_ids, actor)
                projections, records, _, _ = self._export(
                    db, prior.selection, actor, owner=True
                )
                basis = GenerationBasis(
                    selection=prior.selection,
                    versions=tuple(_version_binding(p) for p in projections),
                    record_set_sha256=record_set_sha256(records),
                    policy_id=prior.selection.config.policy_id,
                    backend=self._backend_spec(),
                )
                expected = deterministic_id(
                    "content_index_generation_v1",
                    fingerprint(basis.model_dump(mode="json")),
                )
                if expected != prior.generation_id:
                    raise IntegrityError("vector resume configuration conflict")
        # build rechecks all rights and bytes; persisted staging is never adopted.
        return self.build(prior.selection, actor=actor)

    def _partition_name(self, source_id):
        return "source-" + fingerprint(source_id) + ".vectors.json"

    def _readback(self, plan, artifact, *, complete):
        validate_vectors(artifact, plan)
        expected = {
            p.point_id: dict(payload=p.model_dump(mode="json"), vector=list(v))
            for p, v in zip(plan.units, artifact.vectors, strict=True)
        }
        actual = self.transport.read(plan.collection)
        if not set(actual) <= set(expected) or any(
            actual[k] != expected[k] for k in actual
        ):
            raise IntegrityError("vector readback payload/vector conflict")
        if complete and set(actual) != set(expected):
            raise Unavailable("vector readback incomplete")
        return expected, set(actual)

    def _build_partition(self, records, *, source_id, generation_id, deadline):
        collection = collection_for(self.config, generation_id, source_id)
        plan = map_content(records, collection, self.embedder)
        vectors = []
        batch = self.config.embedding.batch_size
        for i in range(0, len(plan.units), batch):
            if time.monotonic() > deadline:
                raise Unavailable("vector build deadline")
            vectors.extend(
                checked_vectors(
                    self.embedder.encode(
                        [p.child_text for p in plan.units[i : i + batch]]
                    ),
                    self.config.embedding,
                    len(plan.units[i : i + batch]),
                )
            )
        artifact = validate_vectors(
            VectorArtifact(
                plan_id=plan.plan_id,
                embedding_version=self.config.embedding.version,
                vectors=tuple(tuple(v) for v in vectors),
            ),
            plan,
        )
        self.transport.check(collection, allow_create=True)
        expected, matched = self._readback(plan, artifact, complete=False)
        if plan.units:
            self.last_upload = UploadState(
                plan_id=plan.plan_id,
                artifact_id=artifact.artifact_id,
                status="uploading",
                expected_points=len(plan.units),
                verified_points=len(matched),
            )
        try:
            pending = [k for k in expected if k not in matched]
            for i in range(0, len(pending), batch):
                if time.monotonic() > deadline:
                    raise Unavailable("vector upload deadline")
                self.transport.upsert(
                    collection, {k: expected[k] for k in pending[i : i + batch]}
                )
                _, matched = self._readback(plan, artifact, complete=False)
            self._readback(plan, artifact, complete=True)
        except Exception:
            if plan.units:
                self.last_upload = UploadState(
                    plan_id=plan.plan_id,
                    artifact_id=artifact.artifact_id,
                    status="failed",
                    expected_points=len(plan.units),
                    verified_points=len(matched),
                    error_class="content_vector_failed",
                )
            raise
        if plan.units:
            self.last_upload = UploadState(
                plan_id=plan.plan_id,
                artifact_id=artifact.artifact_id,
                status="done",
                expected_points=len(plan.units),
                verified_points=len(plan.units),
            )
        return canonical(
            VectorPartition(
                schema_version=1,
                plan=plan,
                artifact=artifact,
                artifact_id=artifact.artifact_id,
            ).model_dump(mode="json")
        )

    def _decode(self, data, records, source_id, generation_id):
        try:
            part = VectorPartition.model_validate(_json(data))
            expected = map_content(
                records,
                collection_for(self.config, generation_id, source_id),
                self.embedder,
            )
            if expected != part.plan:
                raise ValueError()
            self._readback(part.plan, part.artifact, complete=True)
            return part
        except (ValueError, TypeError, KeyError, ValidationError, IndexError):
            raise IntegrityError("vector partition binding conflict") from None

    def _verify_partition(self, data, records, deadline, *, source_id, generation_id):
        self._decode(data, records, source_id, generation_id)
        if time.monotonic() > deadline:
            raise Unavailable("vector verification deadline")

    def _query_value(self, query, match):
        if (
            self.embedder.config != self.config.embedding
            or self.embedder.count(self.config.embedding.query_prefix + query)
            > self.config.embedding.max_tokens
        ):
            raise InvalidInput("vector query model/token conflict")
        try:
            return checked_vectors(
                self.embedder.encode([query], query=True), self.config.embedding, 1
            )[0]
        except (ValueError, TypeError):
            raise Unavailable("vector query encoding unavailable") from None

    def _search_partition(
        self, data, records, query, content_types, deadline, *, source_id, generation_id
    ):
        try:
            return self._search_checked(
                data,
                records,
                query,
                content_types,
                deadline,
                source_id=source_id,
                generation_id=generation_id,
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            IndexError,
            AttributeError,
            OverflowError,
        ):
            raise IntegrityError("vector response contract conflict") from None

    def _search_checked(
        self, data, records, query, content_types, deadline, *, source_id, generation_id
    ):
        part = self._decode(data, records, source_id, generation_id)
        plan = part.plan
        chosen = {
            r.index_record_id
            for r in records
            if not content_types or r.body.content_type in content_types
        }
        expected = {p.point_id: p for p in plan.units if p.index_record_id in chosen}
        c = plan.collection
        scope = dict(
            source_id=(c.source_id,),
            generation_id=(c.generation_id,),
            collection_contract_id=(c.contract_id,),
            parsed_version_id=tuple(
                sorted({p.parsed_version_id for p in expected.values()})
            ),
            source_version_id=tuple(
                sorted({p.source_version_id for p in expected.values()})
            ),
            index_record_id=tuple(sorted(chosen)),
        )
        response = self.transport.query(
            c, query, scope=scope, limit=len(expected), deadline=deadline
        )
        if len(response) != len(expected) or {r["id"] for r in response} != set(
            expected
        ):
            raise IntegrityError("vector candidates incomplete/foreign")
        winners = {}
        vectors = {
            p.point_id: v
            for p, v in zip(plan.units, part.artifact.vectors, strict=True)
        }
        for row in response:
            p = expected[row["id"]]
            score = row["score"]
            if (
                type(score) not in (float, int)
                or not math.isfinite(score)
                or not -1.00001 <= score <= 1.00001
                or row["payload"] != p.model_dump(mode="json")
                or not math.isclose(
                    float(score),
                    sum(a * b for a, b in zip(query, vectors[p.point_id], strict=True)),
                    abs_tol=1e-6,
                    rel_tol=1e-5,
                )
            ):
                raise IntegrityError("vector candidate score/provenance conflict")
            candidate = (-float(score), p.child_start, p.child_end, p.point_id)
            if (
                p.index_record_id not in winners
                or candidate < winners[p.index_record_id]
            ):
                winners[p.index_record_id] = candidate
        return sorted(
            [(rid, -v[0]) for rid, v in winners.items()], key=lambda x: (-x[1], x[0])
        )

    def _rank_scores(self, hits):
        return [(score, rid, score) for rid, score in hits]

    def _score_component(self, source_id, score):
        return VectorScoreComponent(source_id=source_id, raw_score=score)

    def search_vector(self, *args, **kwargs):
        return super().search_lexical(*args, **kwargs)

    def search_lexical(self, *args, **kwargs):
        raise InvalidInput("use independent lexical index")


class ContentRetrieval:
    """Thin facade over the same lifecycle/guard, no second ranking pipeline."""

    def __init__(self, *, lexical, vector=None):
        if (
            type(lexical) is not ContentIndex
            or vector is not None
            and type(vector) is not ContentVectorIndex
        ):
            raise InvalidInput("typed ContentStore adapters required")
        self.lexical, self.vector = lexical, vector
        if vector is not None and lexical.store.root != vector.store.root:
            raise InvalidInput("shared authoritative ContentStore required")

    def search(self, query, *, method="lexical", **kwargs):
        if method == "lexical":
            return self.lexical.search_lexical(query, **kwargs)
        if method == "vector" and self.vector is not None:
            return self.vector.search_vector(query, **kwargs)
        raise Unavailable("requested backend unavailable; hybrid pilot blocked")
