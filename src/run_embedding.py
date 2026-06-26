##
# imports
import os
from datetime import datetime
from typing import List
import numpy as np
import pandas as pd
from rich.progress import Progress
# from sentence_transformers import SentenceTransformer

# import src.utils.df_helper as dfh

# import utils.ETL_preprocess_helper as eph
# from src.core.logger import create_logger
from src.core.memory import app_session, ParseContext

# from src.utils.general_helper import load_env_vars
from src.utils.dict_helper import load_dict     # , get_yaml_config
from src.utils.df_helper import save_df_to_parquet
from src.utils.chroma_helper import add_chroma_data

from src.tools_rag.chunk import (
                            document_json_to_blocks,
                            prepare_chunk_df
                            )

# importlib.reload(sh)
# importlib.reload(dbh)


# def text_embedding():
#     load_env_vars()
#     config_name = input("Enter 'config_file' name (no suffix): ")

#     config = get_yaml_config(config_name)
#     # app_session.model_config = config

#     general_config = config.get("general_args", {})
#     log_name = general_config["name_log"]
#     name_logfile = general_config["name_logfile"]

#     # setup logger
#     logger = create_logger(name=log_name, file_name=name_logfile)
#     app_session.logger = logger

#     run_context = RunContext(
#         logger=logger, 

#     )

#     return run_text_embedding(run_context)


def chunk_text(
            f_path: str, 
            parse_context: ParseContext
            ):
    # Load environment variables & paths
    # gh.load_env_vars()
    # data_processed = os.getenv("DATA_PROCESSED")

    # config = app_session.model_config
    # general_config = parse_context.general_settings   # get("general_args", {})

    # file_name = general_config["file_name"]
    # f_path = f"{data_processed}/{data_processed}/{f_name}"

    # now = (parse_context.timestamp or 
    #        datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    # app_session.timestamp = now

    chunk_config = parse_context.chunk_settings
    # config.get("chunking", {})

    # embed_config = config.get("embedding", {})
    # file_folder = embed_config["file_folder"]

    # transformer_model = embed_config["transformer_model"]

    logger = app_session.logger

    doc_json = load_dict(f_path)
    df_blocks = document_json_to_blocks(
                                    doc_json["elements"], 
                                    chunk_config
                                    )

    logger.info("Start preparing chunk_df")
    df_chunk = prepare_chunk_df(
                            df_blocks, 
                            chunk_config,
                            encoder=parse_context.encoder
                            )

    # logger.info("")
    
    save_df_to_parquet(
                df=df_chunk, 
                f_name=f"{parse_context.save_name}_chunked",
                folder=parse_context.save_folder
                )
    
    logger.info("Saved chunk_df as %s",
                f"{parse_context.save_name}_chunked")

    return df_chunk



####################################################
### FUNCTION IN COLAB

# def embed_text(df, chunk_settings):
#     from  import SentenceTransformer
#     logger = app_session.logger

#     logger.info("Start creating embeddings from 'text' chunks")
    
#     ## using SBERT for text embeddings
#     transformer_model = chunk_settings.transformer_model

#     model = SentenceTransformer(transformer_model)
#     texts = df["chunk_text"].tolist()

#     embeddings = []
#     batch_size = chunk_settings.batch_size  # 256

#     with Progress() as progress:
#         task = progress.add_task(
#             f"Start embedding with {len(texts)} texts...", total=len(texts)
#         )
#         for i in range(0, len(texts), batch_size):
#             batch = texts[i : i + batch_size]
#             emb = model.encode(
#                             batch, 
#                             convert_to_numpy=True, 
#                             normalize_embeddings=True
#                             )
#             embeddings.append(emb)
#             progress.update(task, advance=len(batch))

#     embeddings = np.vstack(embeddings)

#     logger.info("Finished creating embeddings\n--> embeddings shape:\t", embeddings.shape)

#     df["text_embed"] = list(embeddings)

#     # load_chunks_to_chroma(df, coll_name="apo_qms")

#     return df


def load_chunks_to_chroma(coll_name: str,
                          data: pd.DataFrame | str, 
                          meta_data: dict = {}
                        ):

    if isinstance(data, str):

        folder = os.getenv("DATA_EMBED")
        # f_name = data
        data = pd.read_parquet(f"{folder}/{data}.parquet")

    add_chroma_data(coll_name=coll_name,
                    data=data,
                    meta_data=meta_data)

    return 


####################################################



    # # load df
    # df = pd.read_parquet(file_path)

    # logger.info("\n%s DF %s\n", "=" * 15, "=" * 15)
    # logger.info("shape = %s", df.shape)
    # logger.info("columns:\n%s", df.columns)
    # logger.info("head:\n%s", df.head(5).T)

    # # Prepare text for embedding
    # # df_prep = prepare_embed(df)

    # # Generate embeddings
    # df_emb = embed_text(df, transformer_model)
    # logger.info("\n%s DF_EMBED %s\n", "=" * 15, "=" * 15)
    # logger.info("shape = %s", df_emb.shape)
    # logger.info("columns:\n%s", df_emb.columns)
    # logger.info("head:\n%s", df_emb.head(5))

    # # # Upload embeddings to MongoDB
    # # dbh.upload_embeds(df_emb, coll_name)
    # dfh.save_df_to_parquet(
    #     df=df_emb,
    #     f_name=f"{now}_df_embed_all",
    #     folder=f"{data_processed}/embedded",
    #     chunked=True,
    # )



"""
    ETL pipeline for text embeddings of product data.

    Steps:
    1. Load environment variables and paths.
    2. Load product data from MongoDB.
    3. Prepare text for embedding (cleaning, combining columns, etc.).
    4. Generate embeddings.
    5. Upload embeddings back to MongoDB.
"""

# def prepare_embed(df_in):
#     logger = session.logger

#     logger.info("Start preparing df for embedding")
#     df = df_in.copy()

#     # prepare df for embedding
#     df["text"] = (
#         df["clean_designation"].fillna("").astype(str).str.strip()
#         + " "
#         + df["clean_description"].fillna("").astype(str).str.strip()
#     ).str.strip()

#     print("created column 'text' from 'clean_designation' and 'clean_description'.")
#     return df




# if __name__ == "__main__":
    
#     # chunk_text()

#     load_chunks_to_chroma(coll_name="qms_apo",
#                           data: pd.DataFrame | str = "", 
#                           meta_data: dict = {}
#                         ):