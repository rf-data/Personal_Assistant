"""Isolated fake transport. No SDK, model files, endpoints or environment access."""

import json
import threading
from types import SimpleNamespace as NS

from src.content_store.errors import Busy, IntegrityError, Unavailable
from src.content_store.models import canonical
from src.tools_rag.cs50_collection import check_configuration


class FakeContentTransport:
    """Exact finite test inventory, not a Qdrant execution/quality certificate."""

    def __init__(self, *, snapshot=None):
        self.collections = (
            json.loads(json.dumps(snapshot)) if snapshot is not None else {}
        )
        self.requests = []
        self._lock = threading.Lock()
        if not isinstance(self.collections, dict) or len(self.collections) > 128:
            raise Unavailable("fake collection capacity")
        try:
            if sum(len(c["points"]) for c in self.collections.values()) > 8192:
                raise Unavailable("fake point capacity")
        except (TypeError, KeyError):
            raise IntegrityError("fake snapshot contract conflict") from None

    def snapshot(self):
        return json.loads(canonical(self.collections))

    def check(self, contract, *, allow_create=False):
        if contract.name not in self.collections:
            if not allow_create:
                raise Unavailable("vector collection unavailable")
            if len(self.collections) >= 128:
                raise Unavailable("fake collection capacity")
            self.collections[contract.name] = {
                "metadata": {
                    "content_vector_contract": contract.model_dump(mode="json")
                },
                "dimension": contract.embedding.dimension,
                "distance": "Cosine",
                "points": {},
                "indexes": list(contract.filter_indexes),
            }
        c = self.collections[contract.name]
        info = NS(
            config=NS(
                params=NS(
                    vectors=NS(size=c["dimension"], distance=NS(value=c["distance"]))
                ),
                metadata=c["metadata"],
            )
        )
        try:
            check_configuration(info, contract, metadata_key="content_vector_contract")
            if c["indexes"] != list(contract.filter_indexes):
                raise ValueError()
        except (ValueError, TypeError, KeyError, AttributeError):
            raise IntegrityError("vector collection contract conflict") from None

    def read(self, contract):
        self.check(contract)
        points = self.collections[contract.name]["points"]
        if not isinstance(points, dict) or len(points) > 4096:
            raise Unavailable("vector inventory limit")
        return json.loads(canonical(points))

    def upsert(self, contract, batch):
        self.check(contract)
        if not self._lock.acquire(blocking=False):
            raise Busy("vector transport busy")
        try:
            points = self.collections[contract.name]["points"]
            for point_id, body in batch.items():
                if (
                    point_id not in points
                    and sum(len(c["points"]) for c in self.collections.values()) >= 8192
                ):
                    raise Unavailable("fake point capacity")
                if len(points) >= 4096 and point_id not in points:
                    raise Unavailable("vector inventory limit")
                points[point_id] = json.loads(canonical(body))
        finally:
            self._lock.release()

    def query(self, contract, vector, *, scope, limit, deadline):
        """Full exact search; scope matches required keyword filter semantics."""
        import time

        self.check(contract)
        if set(scope) != set(contract.filter_indexes) or not 0 <= limit <= 4096:
            raise IntegrityError("vector query filter conflict")
        self.requests.append({"collection": contract.name, "scope": scope})
        result = []
        for point_id, point in self.read(contract).items():
            if time.monotonic() > deadline:
                raise Unavailable("vector query deadline")
            p = point["payload"]
            if all(p.get(k) in values for k, values in scope.items()):
                score = sum(a * b for a, b in zip(vector, point["vector"], strict=True))
                result.append({"id": point_id, "payload": p, "score": score})
        return sorted(result, key=lambda r: (-r["score"], r["id"]))[:limit]
