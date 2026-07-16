##
# imports
import os
from pathlib import Path
from datetime import datetime
from typing import List
import gc
from tiktoken import encoding_for_model

import numpy as np
import pandas as pd
import streamlit as st
# from rich.progress import Progress
# from sentence_transformers import SentenceTransformer

# import src.utils.df_helper as dfh

# import utils.ETL_preprocess_helper as eph
# from src.core.logger import create_logger
from src.core.memory import app_session, ParseContext
from src.core.config import ParseSettings
from src.core.logger import create_logger

from src.utils.general_helper import make_doc_id, load_env_vars
from src.utils.dict_helper import load_dict, get_yaml_config
from src.utils.df_helper import save_df_to_parquet
from src.utils.chroma_helper import add_chroma_data
from src.utils.path_helper import shorten_path, ensure_dir 

from src.tools_rag.chunk import (
                            document_json_to_blocks,
                            prepare_chunk_df
                            )
from src.core.config import ChunkSettings
from src.core.memory import app_session

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

def run_embedding(
            chunk_folder: str,
                  ):
    data = os.getenv("DATA_DIR")
    assert data is not None

    data = Path(ensure_dir(data))

    # chunk_folder = context.folder

    folder_path = f"{data}/{chunk_folder}/processed"
    files = [f for f in Path(folder_path).rglob("*_info.json")
             if f.parent.name.startswith("ready_")]
    
    chunk_context = ParseContext(
                    # save_name = Path(selected_file).stem,
                    # save_folder = data_embed,
                    # doc_kind=f_kind, 
                    chunk_settings = ChunkSettings(
                                    container_types = [
                                            # "body_text",
                                            "heading",
                                            "paragraph",
                                            "code",
                                            "line_group",
                                            "bullet_list",
                                            # "lvl_1_bullet",
                                            # "lvl_2_bullet"
                                            ],
                                    spacy_language = "de_core_news_sm",
                                    max_tokens = 80,
                                    overlap_sentences=1,
                                    transformer_model="intfloat/multilingual-e5-base",
                                    # "paraphrase-multilingual-MiniLM-L12-v2",
                                    # "all-MiniLM-L6-v2",
                                    batch_size=16   # 43 
                                    )
                    )
    chunk_context.encoder=app_session.encoder
    
    for idx, f_path in enumerate(files):    
        chunk_context.save_name = Path(f_path).stem

        df_chunk = chunk_text(
                            f_path=str(f_path), 
                            parse_context=chunk_context
                            )

        app_session.logger.info(
                    "File #%s\n%s: \n%s chunks",
                    idx, 
                    Path(f_path).name, 
                    {len(df_chunk)} 
                    )

        df_embed = embed_text(df_chunk, chunk_context)

        load_chunks_to_chroma(
                    coll_name="QMS_apo_intfloat_multi_v1", # : str,
                    data=df_embed, # : pd.DataFrame | str, 
                    meta_data = {
                            "embedding_model": chunk_context.chunk_settings.transformer_model,
                            "embedding_dim": len(df_embed["embed_text"].iloc[0])
                            }
                    # : dict = {}
                        )

        del df_chunk
        del df_embed
    
        gc.collect()

    return 


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

    # chunk_config = parse_context.chunk_settings
    # config.get("chunking", {})

    # embed_config = config.get("embedding", {})
    # file_folder = embed_config["file_folder"]

    # transformer_model = embed_config["transformer_model"]

    logger = app_session.logger

    parse_context.save_name = Path(f_path).stem.replace("info", "chunked")
    parse_context.save_folder = Path(f_path).parent
    # parse_context.f_name = save_name
    parse_context.doc_id = make_doc_id(f_path)

    doc_json = load_dict(f_path)
    df_blocks = document_json_to_blocks(
                                    doc_json, 
                                    parse_context
                                    )

    logger.info("Start preparing chunk_df")
    df_chunk = prepare_chunk_df(
                            df_blocks, 
                            parse_context,
                            encoder=parse_context.encoder
                            )

    # logger.info("")

    parse_context.save_name = Path(f_path).stem
    parse_context.save_folder = Path(f_path).parent
    save_name = parse_context.save_name.replace("info", "chunked")
    
    # import numpy as np

    # print(df_chunk["embed_text"].head())
    # print(df_chunk["embed_text"].map(type).value_counts())

    # for idx, value in df_chunk["embed_text"].items():
    #     if isinstance(value, np.ndarray):
    #         print("index + shape:", idx, value.shape)
    #         print()
            # print("HEAD:", value.head())
            # print()
            # print("VALUE COUNT:", value.map(type).value_counts())
            
    # print(df_chunk["embed_text"].map(type).value_counts())

    # for idx, value in df_chunk["embed_text"].items():
    #     if not isinstance(value, str):
    #         print(
    #             f"Index: {idx}",
    #             f"Typ: {type(value)}",
    #             f"Shape: {getattr(value, 'shape', None)}",
    #             f"Wert: {repr(value)[:500]}",
    #             sep="\n",
    #         )
            
    save_df_to_parquet(
                df=df_chunk, 
                f_name=save_name, # f"{}_chunked",
                folder=parse_context.save_folder
                )
    
    logger.info("Saved chunk_df as %s",
                f"{parse_context.save_name}_chunked")


    # f_name = parse_context.parse_settings.file_name
    # dst_path = f"{raw_data}/{Path(f_name).stem}.pdf"
    
    # move_file(f_name, dst_path)
    return df_chunk



####################################################
### FUNCTION IN COLAB
import streamlit as st
from sentence_transformers import SentenceTransformer


@st.cache_resource
def load_embedding_model(model_name: str):
    return SentenceTransformer(model_name)

def embed_text(
            df_embed: pd.DataFrame, 
            parse_context: ParseContext
            ):
    logger = app_session.logger

    # from sentence_transformers import SentenceTransformer

    logger.info("Start creating embeddings from 'text' chunks")
    
    ## using SBERT for text embeddings

    chunk_settings = parse_context.chunk_settings
    transformer_model = chunk_settings.transformer_model

    model = load_embedding_model(transformer_model)
    texts = df_embed["embed_text"].tolist()

    embeddings = []
    batch_size = 16     # chunk_settings.batch_size  # 256

    # progress_bar = st.progress(0)

    # with Progress() as progress:
    # task = progress.add_task(
    print(
        f"Start embedding with {len(texts)} texts..."
        )

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        emb = model.encode(
                    batch, 
                    # batch_size=chunk_settings.batch_size,
                    convert_to_numpy=True, 
                    normalize_embeddings=True
                    # show_progress_bar=True
                            )
        embeddings.append(emb)
            # progress.update(task, advance=len(batch))
            
        # progress = min((i + len(batch)) / len(texts), 1.0)
        # progress_bar.progress(progress)

    # progress_bar.empty()

    embeddings = np.vstack(embeddings)
    
    
    logger.info("Finished creating embeddings\n--> embeddings shape:\t%s", 
                embeddings.shape)

    # df_embed["embed_text"] = list(embeddings)

    
    embeddings = np.asarray(embeddings)

    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected a 2D embedding matrix, got shape {embeddings.shape}"
        )
    

    if len(embeddings) != len(df_embed):
        raise ValueError(
            f"Embedding count ({len(embeddings)}) does not match "
            f"DataFrame rows ({len(df_embed)})"
        )

    df_embed["embed_text"] = [
        row.astype(float).tolist()
        for row in embeddings
    ]

    del embeddings
    
    # load_chunks_to_chroma(df, coll_name="apo_qms")
    save_name = parse_context.save_name.replace("info", "embed")
    
    save_df_to_parquet(
                df=df_embed, 
                f_name=save_name, # f"{}_chunked",
                folder=parse_context.save_folder
                )

    # save_path = f"{f_directory}/{f_stem.replace("chunked", "embed")}{f_suffix}"

    # df_embed.to_parquet(save_path, index=False)

    return df_embed


def load_chunks_to_chroma(
                    coll_name: str,
                    data: pd.DataFrame, #  | str, 
                    meta_data: dict = {}
                        ):

    # if isinstance(data, str):

    #     folder = os.getenv("DATA_EMBED")
    #     # f_name = data
    #     data = pd.read_parquet(f"{folder}/{data}.parquet")
    # for key, value in meta_data.items():
    #     print(
    #         key,
    #         type(value),
    #         getattr(value, "shape", None),
    #     )

    add_chroma_data(
                coll_name=coll_name,
                data=data,
                meta_data=meta_data
                )

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




if __name__ == "__main__":
    load_env_vars()
    # general_config = get_yaml_config("streamlit_general", 
    #                              model=GeneralSettings)

    parse_config = get_yaml_config("streamlit_run", 
                                    model=ParseSettings)

    # general_config = config.get("general_args", {})
    log_name = parse_config.name_log
    name_logfile = parse_config.name_logfile

    model_name = parse_config.llm_model
    encoder = encoding_for_model(model_name)
    app_session.encoder = encoder

    today = datetime.today().strftime("%Y-%m-%d")
    logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")
    app_session.logger = logger

    folder = "pdf"
    
    run_embedding(folder)

#     # chunk_text()

#     load_chunks_to_chroma(coll_name="qms_apo",
#                           data: pd.DataFrame | str = "", 
#                           meta_data: dict = {}
#                         ):