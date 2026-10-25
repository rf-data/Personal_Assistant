"""Explicit collection boundary for local Qdrant integration tests."""

from tests.optional_dependencies import require_qdrant

qdrant_client = require_qdrant()
QdrantClient = qdrant_client.QdrantClient
models = qdrant_client.models
