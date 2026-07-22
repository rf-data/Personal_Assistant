## chroma_helper.py
# import
# import subprocess
from datetime import datetime

import chromadb

# import numpy as np
import pandas as pd
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

# import streamlit as st
# from src.utils.general_helper import load_env_vars
from src.core.config import env_variables
from src.core.memory import SOPGenContext, app_session

# from fastapi import Depends

# load_dotenv()

# _client: ClientAPI | None = None
# _collection: Collection | None = None

# def get_chroma_client() -> ClientAPI:
# 	global _client
# 	if _client is None:
# 		_client = chromadb.PersistentClient(
#           # chromadb.CloudClient(
#             api_key=env_variables("CHROMA_API_KEY"),
#             tenant=env_variables("CHROMA_TENANT"),
#             database=env_variables("CHROMA_DATABASE")
#         )
# 	return _client
# VARIANTE A (LOKAL)

"""
collection.modify(
    name = "new_name",
    metadata="{}
    )

client.delete_collection(name="")

collection.count() --> returns number of records
collection.peek() --> returns first 10 records
"""


def get_chroma_client() -> ClientAPI:
    # global _client

    # if _client is None:
    # load_env_vars()

    # if db_path is None:
    db_path = env_variables.chroma_dir

    client = chromadb.PersistentClient(path=db_path)

    return client


def get_chroma_collection(
    coll_name: str,
    # client: ClientAPI = Depends(get_chroma_client)
) -> Collection:
    client = get_chroma_client()

    chroma_coll = client.get_or_create_collection(
        name=coll_name,
        embedding_function=None,
        metadata={
            "description": "",
            "created": str(datetime.now()),
            "hnsw:space": "cosine",
            # "embedding_model": "",
            # "embedding_dim"
        },
    )

    return chroma_coll


# def get_chroma_collection(client: ClientAPI = Depends(get_chroma_client)) -> Collection:
# 	global _collection
# 	if _collection is None:
# 		_collection = client.get_or_create_collection(
# 		    name="my_collection",
# 		)
# 	return _collection


# def _create_metadata(data):

#     heading_context = data["heading_context"].tolist()

#     metadata = {
#             "doc_id": data["doc_id"],
#             "container_id": data["container_id"],
#             "chunk_id": data["chunk_id"],
#             "doc_name": data["f_name"],
#             # "page": 1,
#             "chapter": heading_context[0],
#             "section": heading_context[-1],
#             # "document_group": "guideline",
#         }

#     return metadata

# for col in data.columns:


#
# return


def list_files_in_coll(coll: Collection) -> tuple[set, int, set]:
    meta = coll.get(include=["metadatas"]).get("metadatas")

    seen_before = set()
    null_name = set()
    null_id = 0

    for f_meta in meta:
        f_name = f_meta.get("doc_name", None) or f_meta.get("f_name", None) or "null"

        if f_name == "null":
            null_name.add(f"id {null_id}: {f_meta}")
            # .get('doc_id',                                           'null')}")
            null_id += 1

        seen_before.add(f_name)

    return seen_before, null_id, null_name


def add_chroma_data(
    chroma_coll: Collection,
    data: pd.DataFrame,
    doc_column: str,  # "chunk_text"
    id_column: str,  # "chunk_global_id"
    metadatas: dict | None = None,
) -> None:
    logger = app_session.logger

    documents = data[doc_column].fillna("").astype(str).tolist()
    ids = data[id_column].astype(str).tolist()
    embeddings = [
        emb.tolist() if hasattr(emb, "tolist") else emb for emb in data["text_embed"]
    ]

    if not all(doc.strip() for doc in documents):
        raise ValueError("At least one chunk has empty text.")

    if len(set(ids)) != len(ids):
        duplicate_ids = (
            pd.Series(ids).loc[lambda s: s.duplicated(keep=False)].unique().tolist()
        )
        raise ValueError(f"Duplicate chunk IDs found: {duplicate_ids[:10]}")

    embedding_dimensions = {len(embedding) for embedding in embeddings}

    if len(embedding_dimensions) != 1:
        raise ValueError(f"Inconsistent embedding dimensions: {embedding_dimensions}")

    n_records = len(documents)

    if not (len(ids) == len(embeddings) == len(metadatas) == n_records):
        raise ValueError("Lengths of documents, ids, embeddings and metadatas differ.")

    chroma_coll.add(
        ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
    )

    # logger.info("Added new data to ChromaDB collection '%s'",
    #             coll_name)
    logger.info(
        "Added %s chunks to ChromaDB collection '%s' with embedding dimension %s",
        n_records,
        chroma_coll.name,
        next(iter(embedding_dimensions)),
    )

    return


# collection.upsert()       -> update + insert data


def run_chroma_query(
    context: SOPGenContext,
    # chroma_coll: Collection,
    #                   query: str,
    #                   n_results: int=1
):
    results = []

    for chrom_coll in context.collection:
        coll = get_chroma_collection(chrom_coll)
        query = context.query

        q_results = coll.query(
            query_texts=query,  # ["Was ist Chroma?"],
            n_results=context.n_results,
        )

        #     collection.query(
        #     query_embeddings=[[11.1, 12.1, 13.1], [1.1, 2.3, 3.2]],
        #     n_results=100,
        #     where={"page": 10}, # query records with metadata field 'page' equal to 10
        #     where_document={"$contains": "search string"} # query records with the search string in the records' document
        # )
        results.append(q_results)
        app_session.logger.info("Result from query '%s':\n%s", query, results)

    return results


"""
# Initialisiert Chroma und speichert Daten im Ordner
# ./meine_vektoren
client = chromadb.PersistentClient(path="./meine_vektoren")

# Collection erstellen oder abrufen
collection = client.create_collection(name="meine_dokumente")

# Daten in die Collection einbetten
collection.add(
    documents=["Das ist ein lokales Dokument.", "Chroma ist eine Vektordatenbank."],
    metadatas=[{"source": "notiz"}, {"source": "wiki"}],
    ids=["doc1", "doc2"]
)

# Ähnlichkeitssuche durchführen
results = collection.query(
    query_texts=["Was ist Chroma?"],
    n_results=1
)

print(results)
"""

# VARIANTE B (Docker)
"""
docker run -d -p 8000:8000 -v \
	/lokaler/pfad/zu/daten:/chroma/chroma chromadb/chroma


"""

# VARIANTE C (Cloud)
# def start_chroma_cloud(config):

#     API_KEY = env_variables("CHROMA_API_KEY")
#     # subprocess.run(["chroma", "login", "--api-key", f"{API_KEY}"])

#     client = chromadb.CloudClient(
#                     cloud_port=config.get("cloud_port"),
#                     cloud_host=config.get("cloud_host"),
#                     api_key=API_KEY,
#                     tenant=config.get("tenant"),
#                     database=config.get("database")
#                     )

#     return client


# def get_chroma_collection(client: ClientAPI = Depends(get_chroma_client)) -> Collection:
# 	global _collection
# 	if _collection is None:
# 		_collection = client.get_or_create_collection(
# 		    name="my_collection",
# 		)
# 	return _collection

"""
...
from fastapi import Depends
from chroma_connection import get_chroma_collection
...
@app.post("/api_route/")
async def use_chroma(collection=Depends(get_chroma_collection)):
...

from fastapi import FastAPI, HTTPException, Depends
from chroma_connection import get_chroma_collection
from pydantic import BaseModel
from typing import Optional

class RequestBody(BaseModel):
    ids: list[str]
    documents: list[str]
    metadatas: list[dict]

app = FastAPI(title="ChromaDB FastAPI Integration")

@app.post("/api/documents/")
async def add_documents(request: RequestBody, col=Depends(get_chroma_collection)):
    try:
        col.add(
            ids=request.ids,
            documents=request.documents,
            metadatas=request.metadatas
        )
        return {"message": "Documents added successfully", "ids": request.ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


Test your API
Run your app.

npm
pnpm
yarn
bun
bun run dev
If you run your app, you can now add documents to your Chroma collection using your new endpoint! You may need to modify this command if your app is running on a different port.

curl -X POST "http://localhost:8000/api/documents/" \
     -H "Content-Type: application/json" \
     -d '{
       "ids": ["1", "2"],
       "documents": ["Hello Chroma from FastAPI!", "Second doc with different metadata"],
       "metadatas": [{ "category": "technology" }, { "category": "example" }]
     }'
"""

# if __name__ == "__main__":

#     load_env_vars()

#     config = {
#             "database": 'knowledge_DB',
#             "cloud_port": int(443),
#             "cloud_host": 'europe-west1.gcp.trychroma.com',
#             "tenant": '8dcf52e0-1b13-40c2-9179-0401ebf1e94f'
#         }

#     start_chroma_client(config)
