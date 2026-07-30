## E_p0_rag_system.py
# imports
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.core.config import parsing_env_vars
from src.tools_rag.create_embeds import load_chunks_to_chroma
from src.utils.chroma_helper import get_chroma_client, list_files_in_coll
from src.utils.path_helper import shorten_path


def show():
    # st.subheader("🏠 Startseite ")

    st.subheader("Status Vector & Graph DBs")

    chroma_client = get_chroma_client()
    chroma_colls = chroma_client.list_collections()

    with st.expander("**Overview 'ChromaDB collections'**"):
        st.markdown(f"""
    **Chroma DB**\n
    n_collections = {len(chroma_colls)}      \n

    """)
        if len(chroma_colls) > 0:
            for idx, coll in enumerate(chroma_colls):
                # files = coll.get("")

                with st.expander(f"Collection #{idx}: **{coll.name}**"):
                    st.markdown(f"""
    n_records: {coll.count()}

    first 10 records:
    """)
                    #
                    # {st.json(coll.peek())}

                    try:
                        data = coll.get(limit=10, include=["documents", "metadatas"])
                        st.json(data)

                        st.divider()

                        st.markdown("Files included:")
                        """
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

                            if f_name not in seen_before:
                                st.markdown(f"- {f_name}")

                            seen_before.add(f_name)
                        """
                        f_names, n_nameless, set_nameless = list_files_in_coll(coll)

                        for file in sorted(f_names):
                            st.markdown(f"- {file}")

                        with st.expander(f"Count 'row w/o file names': {n_nameless}"):
                            st.markdown("Rows w/o file names")
                            st.json(set_nameless)

                    except Exception as e:
                        st.error(f"Could not preview collection: {e}")

    # st.divider()
    with st.expander("**Create a ChromaDB collection**"):
        coll_new = st.text_input(label="Enter name of new collection")

        start_create = st.button(label="Start creating collection")

        if start_create:
            chroma_client.create_collection(name=coll_new)
            start_create = False

    # st.divider()
    with st.expander("**Add data to ChromaDB collection**"):
        #    st.subheader("Upload Data to ChromaDB")
        root = parsing_env_vars.data_dir
        data_folder = st.pills(
            label="Select folder (processed files)",
            options=["txt_md", "docx", "html", "pdf", "json"],
            selection_mode="single",
            # key="chunk_folder"
        )

        folder_path = f"{root}/{data_folder}/processed"

        dfs_embed = [
            f
            for f in Path(folder_path).rglob("*_embed.parquet")
            if f.parent.name.startswith("ready_")
        ]
        st.info(f"Found {len(dfs_embed)} files")
        chroma_client = get_chroma_client()
        chroma_colls = chroma_client.list_collections()
        coll_name = st.selectbox(
            label="Select a database", options=[coll.name for coll in chroma_colls]
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

        n_files = len(files_to_load)
        st.info(f"You selcted {n_files} files.")
        start_upload = st.button("Start Upload")
        st.write(f"Status 'Upload': {start_upload}")

        if start_upload:
            progress_text = "Uploading in progress. Please wait."
            my_bar = st.progress(0, text=progress_text)

            for idx, f_path in enumerate(files_to_load):
                # df_path = f" /{f_path}.parquet"

                time.sleep(0.01)
                my_bar.progress((idx + 1) / n_files, text=progress_text)

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

    # st.divider()
    with st.expander("**Delete data from ChromaDB collection**"):
        del_coll_name = st.selectbox(
            label="Data from which collection should be deleted?",
            options=[c.name for c in chroma_colls],
        )

        del_complete = st.toggle("Delete entire collection?")
        ent_deletion = st.button("Start deletion")
        st.write(f"Status 'Deletion (entire)': {ent_deletion}")

        # coll_to_delete = [c for c in chroma_colls if c.name in del_coll_name]

        if chroma_colls and del_complete and ent_deletion:
            chroma_client.delete_collection(name=del_coll_name)

            del_complete = False
            ent_deletion = False
            # coll_to_delete[0].delete()

            #

            # if ent_deletion:
            #     for coll in chroma_colls:
            #         if coll.name ==
            #         delete_coll = chromadel_coll_name
            #     delete_coll

        else:
            st.write("Under Construction")

    #     del_coll_name.delete(
    #         ids=["id1", "id2", "id3",...],
    #     )

    #     del_coll_name.delete(
    #     where={"doc_id": doc_id}
    # )

    #     # st.session_state["query_started"] = "done"


"""
Chunks
↓
Normalisierung
(
retrieved_chunks = [
    {
        "text": "...",
        "source": "...",
        "metadata": {...},
        "distance": 0.23,
    }
]
)
↓
Kontext bauen
↓
SOP-Template wählen
↓
LLM Prompt bauen
↓
SOP generieren
↓
SOP speichern / anzeigen
↓
Review-Feedback sammeln
"""
