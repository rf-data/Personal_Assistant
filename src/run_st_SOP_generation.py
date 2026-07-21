## run_SOP_generation.py
# imports
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.core.memory import SOPGenContext, app_session

# from src.tools_rag.retrieve import normalise_chroma_results
# from src.tools_rag.generate import summarize_chunks
from src.utils.dict_helper import save_dict

#                                 build_context,
#                                 build_sop_prompt,
#                                 generate_sop
#                                 )


"""
# Pipeline Architektur
1. User Request
   Thema, Dokumenttyp, Modus: neu / überarbeiten

2. Template Loading
   passende Vorlage laden: SOP, AA, VA, Prüfprotokoll usw.

3. Retrieval Plan
   aus Thema + Vorlage gezielte Suchfragen ableiten

4. Retrieval
   Chroma/FAISS → relevante Chunks

5. Post-Retrieval Extraction
   Chunks → strukturierte Fakten/Stichpunkte mit Quellen

6. Merge / Deduplication
   Fakten zusammenführen, Dopplungen entfernen, Widersprüche markieren

7. Template Mapping
   Fakten den Vorlage-Kapiteln zuordnen

8. Chapter Generation
   kapitelweise SOP schreiben

9. QA Pass
   Vollständigkeit, fehlende Pflichtkapitel, Quellenabdeckung, Halluzinationscheck

10. Export
   Markdown / DOCX / ODT
"""


from src.tools_rag.retrieve import (
    flatten_retrieval_results,
    get_templates,
    retrieve_for_sop,
)


# streamlit run streamlit_app.py
def run_st_sop_generation(
    # user_request: UserRequest,
    sop_context: SOPGenContext,
):
    # esults: dict,

    # results =user_request.results
    # q_f_type = sop_context.q_file_type
    # chapters = sop_context.chapters
    # query = user_request.query
    # client = sop_context.client

    chapter_templates = get_templates(sop_context)
    # q_f_type, chapters)

    chapter_results = retrieve_for_sop(
        sop_context=sop_context,  # .collection,
        # topic=sop_context.query,
        template_chapters=chapter_templates,
        # n_results_per_query=sop_context.n_results,
    )

    chunks = flatten_retrieval_results(chapter_results)

    today = app_session.timestamp or datetime.today().strftime("%Y-%m-%d")

    save_folder = (
        sop_context.save_folder or "/workspaces/gmp_compliance/data/rag_queries"
    )
    save_name = sop_context.save_name or f"{today}_SOP_{sop_context.title}"

    chunks_serialized = [asdict(chunk) for chunk in chunks]

    save_dict(data=chunks_serialized, path=Path(save_folder) / save_name)

    # for chunk in chunks:
    chunks_sum = summarize_chunks(chunks)

    # template = load_sop_template(q_f_type)
    # retrieve_plan = create_retrieval_plan()

    # for chapter_idx, sub_plan in enumerate(retrieve_plan, start=1):
    #     results = retrieve_chapter_chunks(sub_plan)
    #     chunks = normalise_chroma_results(results)

    #     chunks_ing = ingest_chunks(chunks)
    #     chunk_sum = summarize_chunks(chunks_ing)

    #     # context = build_context(chunk_sum)
    #     add_chapter_text(template,
    #                      chunk_sum,
    #                      chapter_idx)


if __name__ == "__main__":
    n_results = 10
    rag_colls = ["QMS_apo_intfloat_multi_v1"]  # rag_colls,
    sop_title = "Hygienmonitoring"  # sop_title,
    sop_topics = """
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

    sop_context = SOPGenContext(
        # query=rag_query,
        work_mode="create",
        n_results=n_results,
        collection=rag_colls,
        title=sop_title,
        topics=topic_list,
        transformer_model="intfloat/multilingual-e5-base",
        q_doc_type="SOP",
    )

    run_st_sop_generation(sop_context)

    # with st.expander("Preview 'retrieved chunks'"):
    #     st.json(chunks)


#     prompt = build_sop_prompt(rag_query, context)

#     sop_md = generate_sop(prompt, client)

#     with st.expander("Prompt & SOP"):
#         st.markdown("**Prompt**")
#         st.text(prompt)
#         st.divider()

#         st.markdown(f"""
# **SOP**

# {sop_md}
# """)

#     save_path = Path(rag_context.save_folder) / f"{rag_context.save_name}_sop.md"
#     save_path.write_text(sop_md, encoding="utf-8")
