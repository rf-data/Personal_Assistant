## E_p0_rag_system.py
# imports
import streamlit as st

from src.utils.chroma_helper import get_chroma_client, list_files_in_coll


def show():
    # st.subheader("🏠 Startseite ")

    st.subheader("Status Vector & Graph DBs")

    chroma_client = get_chroma_client()
    chroma_colls = chroma_client.list_collections()
    st.markdown(f"""
**Chroma DB**\n
n_collections = {len(chroma_colls)}      \n

""")
    if len(chroma_colls) > 0:
        for idx, coll in enumerate(chroma_colls):
            files = coll.get("")

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

                    for file in f_names:
                        st.markdown(f"- {file}")

                    with st.expander(f"Count 'row w/o file names': {n_nameless}"):
                        st.markdown("Rows w/o file names")
                        st.json(set_nameless)

                except Exception as e:
                    st.error(f"Could not preview collection: {e}")

    st.subheader("Delete data from ChromaDB collection")

    del_coll_name = st.selectbox(
        label="Data from which collection should be deleted?",
        options=[c.name for c in chroma_colls],
    )

    del_complete = st.toggle("Delete entire collection?")
    ent_deletion = st.toggle("Start deletion?")

    coll_to_delete = [c for c in chroma_colls if c.name in del_coll_name]

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
