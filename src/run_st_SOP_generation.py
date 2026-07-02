## run_SOP_generation.py
# imports
from pathlib import Path
import streamlit as st

from src.core.memory import RAGContext
from src.tools_rag.retrieve import normalise_chroma_results
from src.tools_rag.generate import (
                                build_context, 
                                build_sop_prompt,
                                generate_sop
                                )

# streamlit run streamlit_app.py
def run_st_sop_generation(rag_context: RAGContext): 
    # esults: dict, 
    results = rag_context.results
    rag_query = rag_context.query
    client = rag_context.client

    chunks = normalise_chroma_results(results)
    context = build_context(chunks)
    prompt = build_sop_prompt(rag_query, context)

    sop_md = generate_sop(prompt, client)

    with st.expander("Prompt & SOP"):
        st.markdown("**Prompt**")
        st.text(prompt)
        st.divider()

        st.markdown(f"""
**SOP**

{sop_md}
""")

    save_path = Path(rag_context.save_folder) / f"{rag_context.save_name}_sop.md"
    save_path.write_text(sop_md, encoding="utf-8")


