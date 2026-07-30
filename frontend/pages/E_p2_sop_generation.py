## E_p2_sop_generation.py
# imports
#
from pathlib import Path

import streamlit as st

# from src.core.memory import SOPGenContext
# from src.run_st_SOP_generation import run_st_sop_generation
# from src.core.memory import app_session, ParseContext
from src.core.config import parsing_env_vars

# from src.core.config import ChunkSettings
# from src.utils.path_helper import shorten_path, ensure_dir
# from src.utils.st_eda_helper import st_df_profile
from src.utils.chroma_helper import get_chroma_client  # , run_chroma_query

# from src.run_embedding import chunk_text, embed_text, load_chunks_to_chroma


def show():
    st.header("🏠 Startseite ")
    st.subheader("**SOP Generation**")

    # st.subheader("RAG Query")

    chroma_client = get_chroma_client()
    chroma_colls = chroma_client.list_collections()

    rag_colls = st.multiselect(  # selectbox, multiselect(
        label="Which chroma DB collection should be used?",
        options=[c.name for c in chroma_colls],  # chroma_colls
        # format_func=lambda p: shorten_path(p, n=1),
        # key="pdf_files"
    )

    sop_title = st.text_input(
        label="Enter name of SOP to be written",
        value="Hygienemonitoring",
        # max_chars = 100
    )

    st.write(f"Title of SOP to be written:\t **{sop_title}**")
    # st.divider()
    sop_topics = st.text_area(
        label="which topics to be covered (Provide bullets of enumerated key words and / or short phrases)",
        value="""
- Hygienemonitoring in der aseptischen Herstellung
- mikrobiologische Überwachung von Luft, Personal und Oberflächen
- Probenahme, Häufigkeit, Warn- und Aktionsgrenzen
- Dokumentation, Trendanalyse und Maßnahmen bei Abweichung
""",
        height="content",
    )

    """
    - Hygienemonitoring in der aseptischen Herstellung
- mikrobiologische Überwachung von Luft, Personal und Oberflächen
- Probenahme, Häufigkeit, Warn- und Aktionsgrenzen
- Dokumentation, Trendanalyse und Maßnahmen bei Abweichung
    """
    topic_list = [
        line.removeprefix("-").strip()
        for line in sop_topics.splitlines()
        if line.removeprefix("-").strip()
    ]

    st.info(
        f"You provided a list with **{len(topic_list)}** topics (**{len(sop_topics)}** characters)"
    )

    #    st.write(f"You wrote  in 'SOP topics'.")
    st.divider()

    n_results = st.slider(
        "n_results",
        min_value=1,
        max_value=20,
        value=10,
        # value=min_val,
        # key="min_number"
    )

    st.warning(
        "Due to RAM issues, 'SOP_Generation' script needs to be run locally or in RunPod"
    )
    #    ADAPT TO NEW FILE SYSTEM''")

    data = parsing_env_vars.data_dir
    folder_path = f"{data}/{sop_title}"
    dates = [f.stem.split("_")[0] for f in Path(folder_path).rglob("*.json")]

    run_date = st.pills(
        label="Select a run date",
        options=[set(dates)],
        selection_mode="single",
        # key="chunk_folder"
    )

    files = [
        f for f in Path(folder_path).rglob("*.json") if f.name.startswith(run_date)
    ]

    with st.expander("**Preview 'Retrieved Chunks'**"):
        st.json()

    with st.expander("**Preview 'Consilidated Facts'**"):
        st.json()

    with st.expander("**Preview 'Knowledge Pool'**"):
        st.json()

    with st.expander("**Preview 'Retrieved Chunks'**"):
        st.json()
    # left, right = st.columns(2)
    # if "query_started" not in st.session_state:
    #     st.session_state["query_started"] = "ready"
    # st.markdown(f"Status 'query_started': {st.session_state['query_started']}")

    # if (
    #     left.button("Reset", type="primary")
    #     and st.session_state["query_started"] is not None
    # ):
    #     st.session_state["query_started"] = "ready"

    # if right.button("Start run") and st.session_state["query_started"] in [
    #     "ready",
    #     None,
    # ]:
    #     sop_context = SOPGenContext(
    #         # query=rag_query,
    #         work_mode="create",
    #         n_results=n_results,
    #         collection=rag_colls,
    #         title=sop_title,
    #         topics=topic_list,
    #         transformer_model="intfloat/multilingual-e5-base",
    #         q_doc_type="SOP",
    #     )

    #     # results = run_chroma_query(
    #     #                 context=sop_context
    #     #                 # chroma_coll=rag_colls[0],
    #     #                 # query=,
    #     #                 # n_results=n_results
    #     #                     )

    #     # st.json(results)

    #     run_st_sop_generation(sop_context)

    # data = Path(ensure_dir(data))

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

    # chunk_folder = st.pills(
    #         label="Select folder (processed files)",
    #         options=["txt_md",
    #                  "docx",
    #                  "html",
    #                  "pdf",
    #                  "json"],
    #         selection_mode="single",
    #         # key="chunk_folder"
    #         )

    # folder_path = f"{data}/{chunk_folder}/processed"
    # files = [f for f in Path(folder_path).rglob("*_info.json")
    #          if f.parent.name.startswith("ready_")]

    # selected_file = st.multiselect(
    #     label="Which json file should be chunked?",
    #     options=files,
    #     key="chunk_files",
    #     format_func=lambda p: shorten_path(p, n=1)
    # )

    # # f_path = str(selected_file)

    # # st.selectbox(       # multiselect(
    # #         label="Which json file should be chunked?",
    # #         options=[shorten_path(f, n=1) for f in Path(folder_path).rglob("*.json")],
    # #         key="chunk_files"
    # #         )
    # if selected_file is not None:
    #     chunk_context = ParseContext(
    #                 # save_name = Path(selected_file).stem,
    #                 # save_folder = data_embed,
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
    #                                 transformer_model = "all-MiniLM-L6-v2",
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

    #     for file in selected_file:

    #         chunk_context.save_name = Path(file).stem

    #         df_chunk = chunk_text(
    #                         f_path=str(file),
    #                         parse_context=chunk_context
    #                         )

    #         with st.expander(f"Preview df '{Path(file).stem}'"):
    #             st_df_profile(df_chunk)

    #         df_embed = embed_text(df_chunk, chunk_context)

    #         load_chunks_to_chroma(
    #                 coll_name="QMS_apo", # : str,
    #                 data=df_embed, # : pd.DataFrame | str,
    #                 # meta_data: dict = {}
    #                     )

    #     st.session_state["chunk_status"] = "done"

    # st.divider()
    # st.error('\n**TEXT EMBEDDINGS MUST BE CREATED IN CODESPACE OR GOOGLE COLAB**',
    #          icon="🚨")
    # # st.markdown("")
    # st.divider()

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
