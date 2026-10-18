"""Explicit Qdrant collections; imports SDK only when actually used."""

from src.model_discovery.cs50_index import CollectionContract


def check_configuration(info, contract, *, metadata_key="cs50_contract"):
    """Shared structural gate; callers select an explicit payload metadata domain."""
    vectors = info.config.params.vectors
    if (
        isinstance(vectors, dict)
        or vectors.size != contract.embedding.dimension
        or vectors.distance.value != contract.distance
    ):
        raise ValueError("Incompatible Qdrant vector dimension or distance")
    metadata = info.config.metadata or {}
    if metadata.get(metadata_key) != contract.model_dump(mode="json"):
        raise ValueError(
            "Missing/incompatible collection model/version metadata; never adopt"
        )
    return info


def check_collection(client, contract: CollectionContract):
    info = check_configuration(client.get_collection(contract.name), contract)
    # Qdrant local mode explicitly does not build payload indexes.
    from qdrant_client.local.qdrant_local import QdrantLocal

    if not isinstance(client._client, QdrantLocal):
        for key in contract.filter_indexes:
            if (
                key not in info.payload_schema
                or info.payload_schema[key].data_type.value != "keyword"
            ):
                raise ValueError(f"Missing keyword payload index: {key}")
    return info


def ensure_collection(client, contract: CollectionContract, *, allow_create=False):
    if client.collection_exists(contract.name):
        return check_collection(client, contract)
    if not allow_create:
        raise ValueError("Collection absent; explicit creation authorization required")
    from qdrant_client import models
    from qdrant_client.local.qdrant_local import QdrantLocal

    client.create_collection(
        collection_name=contract.name,
        vectors_config=models.VectorParams(
            size=contract.embedding.dimension, distance=models.Distance.COSINE
        ),
        metadata={"cs50_contract": contract.model_dump(mode="json")},
    )
    if not isinstance(client._client, QdrantLocal):
        for key in contract.filter_indexes:
            client.create_payload_index(
                contract.name, key, models.PayloadSchemaType.KEYWORD, wait=True
            )
    return check_collection(client, contract)
