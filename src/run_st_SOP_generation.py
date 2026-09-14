## run_SOP_generation.py
# imports
# from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from src.core.config import folder_env_vars, agentic_env_vars
from src.core.logger import create_logger
from src.core.memory import LLMContext, SOPGenContext, app_session
from src.core.observability import configure_llm_observability
from src.core.retry import my_before_sleep

# from src.tools_rag.retrieve import normalise_chroma_results
from src.tools_rag.generate_chunks_facts import (
    build_chunk_fact_pool,
    build_knowledge_pool,
    configure_marvin,
    consolidate_facts,
    #                             group_filtered_facts
)
from src.tools_rag.generate_sop import generate_chapter_plan  # generate_chapter_text,
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
 ↓
RetrievedChunk

5. Ingestion + Fact Extraction
   ↓
IngestedChunk
IngestedFact
   │
   └── chunk_id

6. Fact Consolidation
   ↓
ConsolidatedFact
   │
   └── SourceReference(chunk_id)

6b. Knowledge Pool
   ↓
KnowledgePool
├── chunks
└── consolidated_facts

7. Template Mapping

###########


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
@retry(
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_not_exception_type((TypeError, ValueError, AttributeError)),
    before_sleep=my_before_sleep,
    stop=stop_after_attempt(3),
)
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
        f"{folder_env_vars.data_dir}/sop_{sop_context.title}"
        # workspaces/gmp_compliance/data/rag_queries"
    )

    chunks_serialized = [chunk.model_dump() for chunk in chunks]
    save_dict(
        data=chunks_serialized,
        path=Path(save_folder) / f"{today}_{sop_context.title}_chunk_retr",
    )

    # for chunk in chunks:
    # configure_langfuse(folder_env_vars)
    configure_llm_observability(agentic_env_vars)
    configure_marvin(sop_context)

    chunks_facts = build_chunk_fact_pool(chunks, sop_context)
    # facts_group = group_filtered_facts(chunks_facts.get("facts", []))
    facts_con = consolidate_facts(
        chunks_facts["facts"],  # , []),  # acts_group: list[IngestedFact],
        sop_context,
        # similarity_threshold: float = 0.90,
    )

    facts_con_serialized = {
        topic: [fact.model_dump() for fact in facts]
        for topic, facts in facts_con.items()
    }

    # print("type 'facts_con':\t", type(facts_con))
    # print("type 'facts_con' values:\t'", type(next(iter(facts_con.values()))))

    save_dict(
        data=facts_con_serialized,
        path=Path(save_folder) / f"{today}_{sop_context.title}_fact_con",
        # f"{save_name}_facts_consol"
    )

    know_pool = build_knowledge_pool(chunks=chunks_facts["chunks"], facts=facts_con)

    save_dict(
        data=know_pool.model_dump(),
        path=Path(save_folder) / f"{today}_{sop_context.title}_knowledge",
    )

    chapter_plans, plan_evals = generate_chapter_plan(
        know_pool,
        # sop_context,
        chapter_templates,
    )

    save_dict(
        data={c_name: subs.model_dump() for c_name, subs in chapter_plans.items()},
        path=Path(save_folder) / f"{today}_{sop_context.title}_chapter_plans",
    )

    save_dict(
        data={c_name: evals.model_dump() for c_name, evals in plan_evals.items()},
        path=Path(save_folder) / f"{today}_{sop_context.title}_plan_evals",
    )
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
    sop_title = "Hygienemonitoring"  # sop_title,
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
        # save_folder="/workspaces/gmp_compliance/data/rag_queries",
        llm_context=LLMContext(
            name_logger="",
            name_logfile="",
            path_tracker_file="",
            # generation_model: str = "openai/gpt-5-mini"   # LiteLLM
            # extraction_model: str = "openai:gpt-4o",
            # model="gpt-4o",
            temperature=1.0,
            callbacks=[""],
        ),
        work_mode="create",
        n_results=n_results,
        collection=rag_colls,
        title=sop_title,
        topics=topic_list,
        transformer_model="intfloat/multilingual-e5-base",
        q_doc_type="SOP",
        similarity_threshold=0.7,
    )

    # logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name="SOP_Gen", file_name=f"{app_session.timestamp}_sop_gen"
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
