## chroma_helper.py
# import
# import subprocess
from typing import Any
from datetime import datetime
import os
import numpy as np
import pandas as pd

from src.utils.general_helper import load_env_vars
from src.core.memory import app_session, SOPGenContext

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
# from fastapi import Depends

# load_dotenv()

# _client: ClientAPI | None = None
# _collection: Collection | None = None

# def get_chroma_client() -> ClientAPI:
# 	global _client
# 	if _client is None:
# 		_client = chromadb.PersistentClient(
#           # chromadb.CloudClient(
#             api_key=os.getenv("CHROMA_API_KEY"),
#             tenant=os.getenv("CHROMA_TENANT"),
#             database=os.getenv("CHROMA_DATABASE")
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
    load_env_vars()

    # if db_path is None:
    db_path = os.getenv("CHROMA_PATH")
    assert db_path is not None

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
                                            "created": str(datetime.now())
                                        }
                                        )

    return chroma_coll

# def get_chroma_collection(client: ClientAPI = Depends(get_chroma_client)) -> Collection:
# 	global _collection
# 	if _collection is None:
# 		_collection = client.get_or_create_collection(
# 		    name="my_collection",
# 		)
# 	return _collection


def _to_chroma_scalar(
                value: Any
                ) -> str | int | float | bool | None:
    """Konvertiert Werte in Chroma-kompatible Metadata-Typen."""

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, pd.Series):
        raise TypeError(
            "Chroma metadata received a pandas Series. "
            f"Series name: {value.name!r}. "
            "Use the value from the current row instead."
        )

    if isinstance(value, (list, tuple, set, dict, np.ndarray)):
        return str(value)

    try: 
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return str(value)


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

    
def _create_or_update_metadata(
                    data: pd.DataFrame, 
                    excluded_columns: set[str], 
                    meta_data: dict | None = None
                    ):
    
    meta_data = meta_data or {}

    # if len(meta_data) == 0:
    #     meta_data = _create_metadata(data)
        
    metadata_columns = [
        column
        for column in data.columns
        if column not in excluded_columns
        ]

    metadatas = []
    for _, row in data.iterrows():
        chunk_metadata = {}
        
        for key, value in meta_data.items():
            if key == "meta": 
                continue
           
            if isinstance(value, pd.Series):
                raise TypeError(
                    f"meta_data[{key!r}] is a pandas Series. "
                    "Pass a global scalar or read the value from row[key]."
                )

            converted = _to_chroma_scalar(value)

            if converted is not None:
                chunk_metadata[key] = converted

        shared_meta = meta_data.get("meta", {})
        
        if shared_meta:
            if not isinstance(shared_meta, dict):
                raise TypeError(
                    "meta_data['meta'] must be a dictionary."
                )

            for key, value in shared_meta.items():
                converted = _to_chroma_scalar(value)

                if converted is not None:
                    chunk_metadata[key] = converted  
    
        for column in metadata_columns:
            converted = _to_chroma_scalar(row[column])

            if converted is not None:
                chunk_metadata[column] = converted  
        
        # Praktisch für Filter und Debugging
        chunk_metadata["chunk_global_id"] = str(
                row["chunk_global_id"]
            )

        # None-Werte entfernen, da Chroma je nach Version
        # damit Probleme machen kann.
        chunk_metadata = {
                key: value
                for key, value in chunk_metadata.items()
                if value is not None
            }

        metadatas.append(chunk_metadata)

    return metadatas


def add_chroma_data(
                coll_name: str, 
                data: pd.DataFrame,
                meta_data: dict | None = None
                ) -> None:

    logger = app_session.logger
    meta_data = meta_data or {}

    required_columns = {
        "chunk_text",
        "chunk_global_id",
        # "f_name", 
        "text_embed",
    }

    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )
    
    if data.empty:
        raise ValueError("No chunk data supplied.")
    
    documents = data["chunk_text"].fillna("").astype(str).tolist()
    ids = data["chunk_global_id"].astype(str).tolist()
    embeddings = [
            emb.tolist() if hasattr(emb, "tolist") else emb
            for emb in data["text_embed"]
            ]
    
    if not all(doc.strip() for doc in documents):
        raise ValueError("At least one chunk has empty text.")

    if len(set(ids)) != len(ids):
        duplicate_ids = (
            pd.Series(ids)
            .loc[lambda s: s.duplicated(keep=False)]
            .unique()
            .tolist()
        )
        raise ValueError(
            f"Duplicate chunk IDs found: {duplicate_ids[:10]}"
        )

    embedding_dimensions = {
        len(embedding)
        for embedding in embeddings
    }

    if len(embedding_dimensions) != 1:
        raise ValueError(
            f"Inconsistent embedding dimensions: {embedding_dimensions}"
        )

    metadatas = _create_or_update_metadata(data, required_columns, meta_data)

    n_records = len(documents)

    if not (
        len(ids)
        == len(embeddings)
        == len(metadatas)
        == n_records
    ):
        raise ValueError(
            "Lengths of documents, ids, embeddings and metadatas differ."
        )
    
    chroma_coll = get_chroma_collection(coll_name=coll_name)
    
    chroma_coll.add(
        ids=ids, 
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
        )

    # logger.info("Added new data to ChromaDB collection '%s'",
    #             coll_name)
    logger.info(
        "Added %s chunks to ChromaDB collection '%s' "
        "with embedding dimension %s",
        n_records,
        coll_name,
        next(iter(embedding_dimensions)),
        )

    return 

# collection.upsert()       -> update + insert data


def run_chroma_query(
        context: SOPGenContext
        # chroma_coll: Collection, 
        #                   query: str, 
        #                   n_results: int=1
                          ):

    results = []
    
    for chrom_coll in context.collection:
        coll = get_chroma_collection(chrom_coll)
        query = context.query

        q_results = coll.query(
                    query_texts=query, #["Was ist Chroma?"],
                    n_results=context.n_results
                )
    
#     collection.query(
#     query_embeddings=[[11.1, 12.1, 13.1], [1.1, 2.3, 3.2]],
#     n_results=100,
#     where={"page": 10}, # query records with metadata field 'page' equal to 10
#     where_document={"$contains": "search string"} # query records with the search string in the records' document
# )
        results.append(q_results)
        app_session.logger.info("Result from query '%s':\n%s",
                                query,
                                results)
    
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

#     API_KEY = os.getenv("CHROMA_API_KEY")
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
