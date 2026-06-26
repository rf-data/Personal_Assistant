## chroma_helper.py
# import
# import subprocess
from datetime import datetime
import os
import pandas as pd

from src.utils.general_helper import load_env_vars
from src.core.memory import app_session

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
                                            "creatred": str(datetime.now())
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

def add_chroma_data(coll_name: str, 
                    data: pd.DataFrame,
                    meta_data: dict):

    logger = app_session.logger

    f_text = list(data[["text"]])
    assert len(f_text) > 0

    f_meta = meta_data.get("meta", {})
    f_id = meta_data.get("id", "")
    f_embeds = list(data[["text_embed"]])

    chroma_coll = get_chroma_collection(coll_name=coll_name)
    chroma_coll.add(
        documents=f_text,
        # ["Das ist ein lokales Dokument.", "Chroma ist eine Vektordatenbank."],
        embeddings=f_embeds,
        metadatas=f_meta,
        # [{
        # "source": "notiz",
        # "chapter": "",
        # "scores": int,...}, {"source": "wiki", ....}],
        ids=f_id
        # ["doc1", "doc2"]
    )

    logger.info("Added new data to ChromaDB collection '%s'",
                coll_name)
    return 

# collection.upsert()       -> update + insert data

def run_chroma_similarity(chroma_coll: Collection, 
                          query: str, 
                          n_results: int=1):

    results = chroma_coll.query(
                    query_texts=["Was ist Chroma?"],
                    n_results=n_results
                )
    
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
def start_chroma_cloud(config):

    API_KEY = os.getenv("CHROMA_API_KEY")
    # subprocess.run(["chroma", "login", "--api-key", f"{API_KEY}"])
    
    client = chromadb.CloudClient(
                    cloud_port=config.get("cloud_port"),
                    cloud_host=config.get("cloud_host"),
                    api_key=API_KEY,
                    tenant=config.get("tenant"),
                    database=config.get("database")
                    )
                        
    return client


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
