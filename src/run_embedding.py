## 
# imports 
import os
import pandas as pd
import numpy as np
from datetime import datetime
from rich.progress import Progress
from sentence_transformers import SentenceTransformer

# import utils.ETL_preprocess_helper as eph 
import src.utils.general_helper as gh 
import utils.dict_helper as dh
import src.utils.df_helper as dfh 

from src.core.memory import session
from src.core.logger import create_logger

# importlib.reload(sh)
# importlib.reload(dbh)

def text_embedding():
    gh.load_env_vars()
    config_name = input("Enter 'config_file' name (no suffix): ")
    
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    return run_text_embedding()

def run_text_embedding():
    """
    ETL pipeline for text embeddings of product data.

    Steps:
    1. Load environment variables and paths.
    2. Load product data from MongoDB.
    3. Prepare text for embedding (cleaning, combining columns, etc.).
    4. Generate embeddings.
    5. Upload embeddings back to MongoDB.
    """
    #Load environment variables & paths
    # gh.load_env_vars()
    data_processed = os.getenv("DATA_PROCESSED")

    config = session.model_config
    general_config = config.get("general_args", {})
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]
    now = general_config.get(
                        "timestamp", 
                        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        )
    session.state.timestamp = now

    embed_config = config.get("embedding", {})
    file_folder = embed_config["file_folder"]
    file_name = embed_config["file_name"]
    file_path = f"{data_processed}/{file_folder}/{file_name}"

    transformer_model = embed_config["transformer_model"]

    # setup logger
    logger = create_logger(name=log_name, 
                           file_name=name_logfile)
    session.logger = logger

    # load df
    df = pd.read_parquet(file_path)
    
    logger.info("\n%s DF %s\n",
                        "=" * 15,
                        "=" * 15)
    logger.info("shape = %s",
                df.shape)
    logger.info("columns:\n%s", 
                df.columns)
    logger.info("head:\n%s",
                    df.head(5).T)
    
    # Prepare text for embedding
    # df_prep = prepare_embed(df)

    # Generate embeddings
    df_emb = embed_text(df, transformer_model)
    logger.info("\n%s DF_EMBED %s\n",
                        "=" * 15,
                        "=" * 15)
    logger.info("shape = %s",
                df_emb.shape)
    logger.info("columns:\n%s", df_emb.columns)
    logger.info("head:\n%s", df_emb.head(5))

    # # Upload embeddings to MongoDB
    # dbh.upload_embeds(df_emb, coll_name)
    dfh.save_df_to_parquet(df=df_emb, 
                           f_name=f"{now}_df_embed_all", 
                           folder=f"{data_processed}/embedded",
                           chunked=True)
    return 



def prepare_embed(df_in):
    logger = session.logger
    
    logger.info("Start preparing df for embedding")
    df = df_in.copy()

    # prepare df for embedding
    df["text"] = (
        df["clean_designation"].fillna("").astype(str).str.strip()
        + " "
        + df["clean_description"].fillna("").astype(str).str.strip()
                ).str.strip()
            
    print("created column 'text' from 'clean_designation' and 'clean_description'.")
    return df



def embed_text(df, transformer_model):
    logger = session.logger

    logger.info("Start creating embeddings from 'text' chunks")
    # lazy imports
    # try:
    #     from sentence_transformers import SentenceTransformer
    # except ImportError:
    #     raise ImportError("sentence_transformers is not installed.")
    
    # path = os.path.join(df_in, "df_test_embedded.csv")
    # df_pre = pd.read_csv(path)
    # df = df_pre.head(10).copy()
    # df = df_in.copy()
    
    ## using SBERT for text embeddings
    model = SentenceTransformer(transformer_model)
    texts = df["text"].tolist()

    embeddings = []
    batch_size = 256

    with Progress() as progress:
        task = progress.add_task(f"Start embedding with {len(texts)} texts...", total=len(texts))
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            emb = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
            embeddings.append(emb)
            progress.update(task, advance=len(batch))

    embeddings = np.vstack(embeddings)

    print(f"Finished creating embeddings\n--> embeddings shape:\t", embeddings.shape)

    df["text_embed"] = list(embeddings)

    return df


if __name__ == "__main__":
    text_embedding()
