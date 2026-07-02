## A_p0_wiki_search.py
# imports
import streamlit as st

from src.utils.chroma_helper import get_chroma_client, run_chroma_query

def show():
    # st.subheader("🏠 Startseite ")

    st.subheader("Status Vector & Graph DBs")

    chroma_client = get_chroma_client()
    chroma_colls = chroma_client.list_collections()
    st.markdown(f"""
**Chroma DB**\n
n_collections = {len(chroma_colls)}                
""")
    if len(chroma_colls) > 0:
        for idx, coll in enumerate(chroma_colls):
            st.markdown(f"""
Collection #{idx}: {coll}
n_records: {coll.count()}

first 10 records:
{coll.peek()}

""")
            

    st.divider()
    st.subheader("RAG Query")
    
    rag_colls = st.multiselect(       # selectbox, multiselect(
                    label="Which chroma DB collection should be used?",
                    options=chroma_colls
                    # format_func=lambda p: shorten_path(p, n=1), 
                    # key="pdf_files"
                    )

    rag_query = st.text_input(
                        label = "Enter your query", 
                        # max_chars = 100
                        )
    st.write(f"The current query is:\n{rag_query}")

    n_results = st.slider(
                        "n_results",
                        min_value = 1,
                        max_value = 20,
                        value = 10
                        # value=min_val,
                        # key="min_number"
                    )

    left, right = st.columns(2)
    if "query_started" not in st.session_state:
        st.session_state["query_started"] = "ready"
    st.markdown(f"Status 'query_started': {st.session_state['query_started']}")
    
    if (left.button("Reset", type="primary")
        and st.session_state["query_started"] is not None):
        st.session_state["query_started"] = "ready"

    if (right.button("Start run") 
        and st.session_state["query_started"] in ["ready", None]):
        
        results = run_chroma_query(
                        chroma_coll=rag_colls[0],
                        query=rag_query,
                        n_results=n_results
                            )
        

        st.json(results)

        # run_st_SOP_generation()
        
        # st.session_state["query_started"] = "done"


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