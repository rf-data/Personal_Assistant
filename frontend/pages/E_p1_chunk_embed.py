## E_p1_chunk_embed.py
# imports

from pathlib import Path

import pandas as pd
import streamlit as st

from src.core.config import env_variables

# from src.utils.st_eda_helper import st_df_profile
from src.tools_rag.create_embeds import load_chunks_to_chroma  # chunk_text, embed_text,
from src.utils.chroma_helper import get_chroma_client, list_files_in_coll
from src.utils.path_helper import ensure_dir, shorten_path


def show():
    st.header("🏠 Startseite ")
    st.subheader("**Chunk & Embed**")

    data = env_variables.data_dir

    data = Path(ensure_dir(data))

    # st.warning("ADAPT TO NEW FILE SYSTEM")

    # st.divider()

    # # parse_settings = {
    # #     "c_types_to_filter": [
    # #                         "heading",
    # #                         "paragraph",
    # #                         "code",
    # #                         "bullet_list"
    # #                         ],
    # #     "spacy_language": "",
    # #     "max_tokens": ""
    # # }

    chunk_folder = st.pills(
        label="Select folder (processed files)",
        options=["txt_md", "docx", "html", "pdf", "json"],
        selection_mode="single",
        # key="chunk_folder"
    )

    folder_path = f"{data}/{chunk_folder}/processed"
    # # files = [f for f in Path(folder_path).rglob("*_info.json")
    # #          if f.parent.name.startswith("ready_")]

    # files_to_chunk = st.multiselect(
    #     label="Which json file should be chunked?",
    #     options=files,
    #     # key="chunk_files",
    #     format_func=lambda p: shorten_path(p, n=1)
    # )

    # f_kind = st.selectbox(
    #                 label="Kind of document",
    #                 options=["regulatory", "comment", "SOP"],
    #                 # index="regulatory",
    #                 accept_new_options=True
    #                 )
    # # f_path = str(selected_file)

    # # st.selectbox(       # multiselect(
    # #         label="Which json file should be chunked?",
    # #         options=[shorten_path(f, n=1) for f in Path(folder_path).rglob("*.json")],
    # #         key="chunk_files"
    # #         )
    # if files_to_chunk is not None:
    #     chunk_context = ParseContext(
    #                 # save_name = Path(selected_file).stem,
    #                 # save_folder = data_embed,
    #                 doc_kind=f_kind,
    #                 chunk_settings = ChunkSettings(
    #                                 container_types = [
    #                                         # "body_text",
    #                                         "heading",
    #                                         "paragraph",
    #                                         "code",
    #                                         "line_group",
    #                                         "bullet_list",
    #                                         # "lvl_1_bullet",
    #                                         # "lvl_2_bullet"
    #                                         ],
    #                                 spacy_language = "de_core_news_sm",
    #                                 max_tokens = 80,
    #                                 overlap_sentences=1,
    #                                 transformer_model="intfloat/multilingual-e5-base",
    #                                 # "paraphrase-multilingual-MiniLM-L12-v2",
    #                                 # "all-MiniLM-L6-v2",
    #                                 batch_size=43
    #                                 )
    #                 )
    #     chunk_context.encoder=app_session.encoder

    # # f_path = f"{folder_path}/{str(selected_file)}"
    # if "chunk_status" not in st.session_state:
    #     st.session_state["chunk_status"] = "ready"

    # st.markdown(f"Status 'chunk_status': {st.session_state['chunk_status']}")

    # left, right = st.columns(2)

    # if (left.button("Reset", type="primary")
    #     and st.session_state["chunk_status"] is not None):
    #     st.session_state["chunk_status"] = "ready"

    # if (right.button("Start run")
    #     and st.session_state["chunk_status"] in ["ready", None]):

    #     for idx, f_path in enumerate(files_to_chunk):

    #         chunk_context.save_name = Path(f_path).stem

    #         df_chunk = chunk_text(
    #                         f_path=str(f_path),
    #                         parse_context=chunk_context
    #                         )

    #         st.write(f"""
    #             File #{idx}
    #             {Path(f_path).name}:
    #             {len(df_chunk)} chunks
    #             """)
    #         # st.info(f"Chunking file #{idx}")

    #         """
    #         import streamlit as st
    #         import time

    #         progress_text = "Chunking files... Please wait."
    #         my_bar = st.progress(0, text=progress_text)

    #         for i in range(0, len(files_to_chunk)):
    #             time.sleep(0.01)
    #             my_bar.progress(percent_complete + 1, text=progress_text)
    #         time.sleep(1)
    #         my_bar.empty()

    #         st.button("Rerun")
    #         """
    #         # with st.expander(f"Preview df '{Path(f_path).stem}'"):
    #         #     st_df_profile(df_chunk)

    #         df_embed = embed_text(df_chunk, chunk_context)

    #         load_chunks_to_chroma(
    #                 coll_name="QMS_apo", # : str,
    #                 data=df_embed, # : pd.DataFrame | str,
    #                 # meta_data: dict = {}
    #                     )

    #         del df_chunk
    #         del df_embed
    #         # del embeddings

    #         gc.collect()

    #     st.session_state["chunk_status"] = "done"

    st.divider()
    st.error(
        "\n**TEXT EMBEDDINGS MUST BE CREATED IN CODESPACE (w/o UI) OR GOOGLE COLAB**",
        icon="🚨",
    )
    # st.markdown("")
    st.divider()

    st.subheader("Upload Data to ChromaDB")

    dfs_embed = [
        f
        for f in Path(folder_path).rglob("*_embed.parquet")
        if f.parent.name.startswith("ready_")
    ]

    chroma_client = get_chroma_client()
    chroma_colls = chroma_client.list_collections()
    coll_name = st.selectbox(
        label="Selct a database", options=[coll.name for coll in chroma_colls]
    )
    # "QMS_apo"
    coll = [c for c in chroma_colls if c.name in coll_name]
    f_names, _, _ = list_files_in_coll(coll[0])

    dfs_filtered = [df_path for df_path in dfs_embed if df_path.stem not in f_names]

    files_to_load = st.multiselect(
        label="Which files should be uploaded?",
        options=dfs_filtered,  # set(dfs_embed) - set(f_names),
        format_func=lambda p: shorten_path(p, n=1),
    )

    st.info(f"You selcted {len(files_to_load)} files.")
    start_upload = st.toggle("Start Upload")

    if start_upload:
        for f_path in files_to_load:
            # df_path = f" /{f_path}.parquet"
            df_upload = pd.read_parquet(f_path)

            load_chunks_to_chroma(
                coll_name=coll_name,  # : str,
                data=df_upload,  # : pd.DataFrame | str,
                required_columns={
                    "chunk_text",
                    "chunk_global_id",
                    # "f_name",
                    "text_embed",
                },
                # meta_data: dict = {}
            )
        start_upload = False

    # st.markdown("**Under Construction**")


# from sentence_transformers import SentenceTransformer

# model_name = "sentence-transformers/all-MiniLM-L6-v2"

# model = SentenceTransformer(model_name)

# embeddings = model.encode(
#     df_chunks["chunk_text"].tolist(),
#     batch_size=32,
#     show_progress_bar=True,
#     normalize_embeddings=True,
# )
# def _chunk_by_sentences(block_text: str,
#                         chunk_config: dict,
#                         nlp) -> list[dict]:
#     max_tokens = chunk_config["max_tokens"]
#     overlap_sentences = chunk_config.get("overlap_sentences", 1)

#     encoder = session.encoder
#     doc = nlp(block_text)

#     chunks = []
#     current = []
#     current_len = 0
#     chunk_id = 0

#     for sent in doc.sents:
#         sent_text = sent.text.strip()
#         if not sent_text:
#             continue

#         sent_tokens = len(encoder.encode(sent_text))
#         sent_start = sent.start_char
#         sent_end = sent.end_char

#         if current and current_len + sent_tokens > max_tokens:
#             chunk_text = " ".join(x["text"] for x in current)

#             chunks.append({
#                 "chunk_id": chunk_id,
#                 "chunk_start": current[0]["start"],
#                 "chunk_end": current[-1]["end"],
#                 "chunk_text": chunk_text,
#                 "n_chars": len(chunk_text),
#                 "n_words": len(chunk_text.split()),
#                 "n_tokens": len(encoder.encode(chunk_text)),
#             })

#             current = current[-overlap_sentences:] if overlap_sentences > 0 else []
#             current_len = sum(x["tokens"] for x in current)
#             chunk_id += 1

#         current.append({
#             "text": sent_text,
#             "start": sent_start,
#             "end": sent_end,
#             "tokens": sent_tokens,
#         })
#         current_len += sent_tokens

#     if current:
#         chunk_text = " ".join(x["text"] for x in current)

#         chunks.append({
#             "chunk_id": chunk_id,
#             "chunk_start": current[0]["start"],
#             "chunk_end": current[-1]["end"],
#             "chunk_text": chunk_text,
#             "n_chars": len(chunk_text),
#             "n_words": len(chunk_text.split()),
#             "n_tokens": len(encoder.encode(chunk_text)),
#         })

#     return chunks
