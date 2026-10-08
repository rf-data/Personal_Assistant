## qdrant_helper.py
# import
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document


from src.core.config import agentic_env_vars


def get_qdrant_client():
    # connect to Qdrant Cloud
    client = QdrantClient(
        url=agentic_env_vars.qdrant_cloud_endpoint,
        # "https://xyz-example.eu-central.aws.cloud.qdrant.io",
        api_key=agentic_env_vars.qdrant_cloud_api_key,
        cloud_inference=True,
    )

    return client


def ensure_collection(collection_name: str, vector_size: int, client):

    # create collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    return


def upload_records(collection_name, records, client):
    # points generator
    points = []
    for i, menu_item in enumerate(records):
        point = PointStruct(
            id=i,
            vector=Document(
                text=f"{menu_item[0]} {menu_item[1]}",
                model="sentence-transformers/all-MiniLM-L6-v2",
            ),
            payload={
                "item_name": menu_item[0],
                "description": menu_item[1],
                "price": menu_item[2],
                "category": menu_item[3],
            },
        )
        points.append(point)

    # upsert points to collection
    client.upsert(
        collection_name=collection_name,
        points=points,
    )

    return None


"""




"""
