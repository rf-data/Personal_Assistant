##
# imports
# from typing import List
import gc
from datetime import datetime
from pathlib import Path
from tiktoken import encoding_for_model

from src.core.config import ChunkSettings, folder_env_vars
from src.core.logger import create_logger
from src.core.memory import ParseContext, app_session
from src.tools_rag.chunk import chunk_text
from src.tools_rag.create_embeds import embed_text, load_chunks_to_chroma
from src.utils.df_helper import save_df_to_parquet
from src.utils.path_helper import ensure_dir  # shorten_path,


def run_chunk_and_embed(
    folder_path: str,
):
    logger = app_session.logger

    files = [
        f
        for f in Path(folder_path).rglob("*_info.json")
        if f.parent.name.startswith("ready_")
    ]

    chunk_context = ParseContext(
        chunk_settings=ChunkSettings(
            container_types=[
                "heading",
                "paragraph",
                "code",
                "line_group",
                "bullet_list",
            ],
            spacy_language="de_core_news_sm",
            max_tokens=80,
            overlap_sentences=1,
            transformer_model="intfloat/multilingual-e5-base",
            # "paraphrase-multilingual-MiniLM-L12-v2",
            # "all-MiniLM-L6-v2",
            batch_size=16,  # 43
        )
    )
    chunk_context.encoder = app_session.encoder

    for idx, f_path in enumerate(files):
        chunk_context.save_name = Path(f_path).stem

        df_chunk = chunk_text(f_path=str(f_path), parse_context=chunk_context)

        chunk_context.save_name = Path(f_path).stem
        save_name = chunk_context.save_name.replace("info", "chunked")

        save_df_to_parquet(df=df_chunk, f_name=save_name, folder=Path(f_path).parent)

        logger.info("Saved chunk_df as %s", f"{save_name}")

        logger.info(
            "File #%s\n%s: \n%s chunks", idx, Path(f_path).name, {len(df_chunk)}
        )

        #
        df_embed = embed_text(df_chunk, chunk_context)

        save_name = chunk_context.save_name.replace("info", "embed")

        save_df_to_parquet(
            df=df_embed,
            f_name=save_name,
            folder=chunk_context.save_folder,
        )

        load_chunks_to_chroma(
            coll_name="QMS_apo_intfloat_multi_v1",
            data=df_embed,
            meta_data={
                "embedding_model": chunk_context.chunk_settings.transformer_model,
                "embedding_dim": len(df_embed["text_embed"].iloc[0]),
            },
            required_columns={
                "chunk_text",
                "chunk_global_id",
                "text_embed",
            },
        )

        del df_chunk
        del df_embed

        gc.collect()

    return


if __name__ == "__main__":
    log_name = "Chunk & Embed"
    name_logfile = "chunk_embed"
    today = datetime.today().strftime("%Y-%m-%d")

    logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")
    app_session.logger = logger

    encoder = encoding_for_model("gpt-4o-mini")
    app_session.encoder = encoder

    data = folder_env_vars.data_dir

    data = Path(ensure_dir(data))

    folder = "pdf"
    folder_path = f"{data}/{folder}/processed"

    run_chunk_and_embed(folder_path)
