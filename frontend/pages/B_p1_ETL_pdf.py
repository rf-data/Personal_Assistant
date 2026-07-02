## B_p1_ETL_pdf.py
# imports
import os
from pathlib import Path
from datetime import datetime
import streamlit as st

from src.utils.streamlit_helper import st_file_preview
from src.core.memory import app_session, ParseContext 
# from src.model_tools.base_assembler import BaseAssembler

from src.utils.path_helper import shorten_path  
from src.utils.pdf_helper import pdf_page_count
# from src.utils.html_helper import read_html_file
from src.run_st_pdf_extract import run_pdf_extraction

def show():
    # st.header("🏠 Startseite ")
    st.subheader("**ETL pdf_files**")

    parse_config = app_session.parse_settings
    general_settings = app_session.general_settings
    st.divider()

    # file_select, file_preview 
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🖼️ Select an pdf file")

        pdf_data = os.getenv("DATA_PDF")
        assert pdf_data is not None

        input_data = f"{pdf_data}/input"
                
        pdf_files = st.multiselect(       # selectbox, multiselect(
                    label="Which pdf file(s) should be parsed?",
                    options=list(Path(input_data).rglob("*.pdf")), 
                    format_func=lambda p: shorten_path(p, n=1), 
                    key="pdf_files"
                    )
        
        # parse_config.file_id = int(st.number_input("File number"))
        #  = st.session_state["pdf_file"] # html_select

        # st.write(f"You selected {len(files_pdf)} files:")
        # for idx, file in enumerate(files_pdf): 
    with col2:
        st.write(f"Selected:")
        for idx, file in enumerate(pdf_files):
            st.write(f"#{idx}\t", shorten_path(file, 1))

    st.divider()

    # with file_preview:
    st.subheader("File Preview")
    for idx, file in enumerate(pdf_files):
        # for idx, file in enumerate(files_pdf):
            # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
            #             unsafe_allow_html=True)
            
            # html_str = read_html_file(f"{input_data}/{file}")
            # , *, height=500, key=None)

        with st.expander(f"**File # {idx}' {Path(file).stem}'**"):
                    # st.html(html_str[:500])
                # st.pdf(pdf_file)
            st_file_preview(file)
            

        st.divider()
        
    # st.divider()
    st.subheader("Run Settings")

    # col1, col2 = st.columns(2)

    # with col1:
        # st.pills(
        #     label="HTML parser", 
        #     options=["html.parser", "lxml", "html5lib"], 
        #     selection_mode="single",
        #     key="parser_html"
        #     )
        
        # if st.session_state["parser_html"] in ["lxml", "html5lib"]:
        #     st.error("Selected parser is most likely not yet installed.")

        # parse_config.pdf.parser = st.session_state["parser_html"]

    if isinstance(pdf_files, list) and len(pdf_files) == 1:
        st.toggle(
                label="Parse all pages?",
                key="parse_pdf_all"
                )

        n_pages = pdf_page_count(pdf_files[0])

        if st.session_state["parse_pdf_all"] is False and n_pages > 1:

            value_range = st.slider(
                            "Page range",
                            min_value=0,
                            max_value=n_pages,
                            value=(0, int(n_pages/2))
                                )

            min_val, max_val = value_range

            col1, col2 = st.columns(2)

            with col1:
                min_val = st.number_input(
                        "Min",
                        value=min_val,
                        key="min_number"
                    )

            with col2:
                max_val = st.number_input(
                        "Max",
                        value=max_val,
                        key="max_number"
                    )

            parse_config.page_range = [p for p in range(
                                                    min_val,
                                                    max_val + 1
                                                    )]
            # st.session_state["parse_pdf_all"] is False
            
    else:
        parse_config.page_range = "all"

    st.pills(
            label="Save file", 
            options=[
                "assembled",
                "class",
                "info",  
                "md", 
                "merge",
                "txt"
                ], 
            selection_mode="multi",
            key="pdf_save"
            )

    parse_config.pdf.save = st.session_state["pdf_save"]
        
    # with col2:    
    st.pills(
            label="Assemble format", 
            options=["md", "txt"], 
            default=["md", "txt"], 
            selection_mode="multi",
            key="pdf_assemble"
            )
        
    parse_config.pdf.assemble = st.session_state["pdf_assemble"]

        # st.toggle(label="Apollo",
        #           key="apollo_html")
        # parse_config.html.apollo = st.session_state["apollo_html"]

    st.toggle(label="Scrape_images",
              key="pdf_image")
    parse_config.pdf.scrape_images = st.session_state["pdf_image"]

    rag_ready = st.toggle(
                    label="Perform RAG-ready extraction",
                    # key="pdf_image"
                )
    
    if "pdf_parsed" not in st.session_state:
        st.session_state["pdf_parsed"] = "ready"

    data_processed = f"{pdf_data}/processed"
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'pdf_parsed': {st.session_state['pdf_parsed']}")
    # if isinstance(files_pdf, str):
    #     files_pdf = [files_pdf]

    left, right = st.columns(2)

    if (left.button("Reset", type="primary")
        and st.session_state["pdf_parsed"] is not None):
        st.session_state["pdf_parsed"] = "ready"

    if (right.button("Start run") 
        and st.session_state["pdf_parsed"] in ["ready", None]):
            # st.session_state["parsed"] = None
        for file in pdf_files:
            f_name = Path(file).stem

            t_stamp = app_session.timestamp 
            save_folder = Path(f"{data_processed}/{'ready' if rag_ready else 'test'}_{t_stamp}_{f_name}")        

            parse_config.file_name = str(file)

            parse_context = ParseContext(
                                parse_settings=parse_config,
                                general_settings=general_settings,
                                save_folder=save_folder,
                                save_name=f_name,
                                text_type="pdf",
                                timestamp=now
                                )
            parse_context.encoder=app_session.encoder
            parse_context.logger=app_session.logger
                
            app_session.run_context = parse_context

            run_pdf_extraction(parse_context)

            st.success(f"Parsing finished\t '{f_name}'")
        ##################

        st.session_state["pdf_parsed"] = "done"

    # st.markdown("**Under Construction**")


