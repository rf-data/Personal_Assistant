## B_p1_ETL_pdf.py
# imports
import os
from pathlib import Path
from datetime import datetime
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from src.core.memory import app_session, ParseContext 

from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.pdf_extractor import PDFCleanExtractor
# from src.model_tools.base_assembler import BaseAssembler

from src.tools_parsing.assemble_pdf import assemble_single_pdf
from src.tools_parsing.extract_pdf import extract_pdf_file
from src.tools_parsing.post_extract_processing_pdf import post_process_pdf

from src.utils.path_helper import shorten_path  
from src.utils.pdf_helper import pdf_page_count
# from src.utils.html_helper import read_html_file


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

        input_data = os.getenv("DATA_INPUT")
        assert input_data is not None
        
        pdf_file = st.selectbox(       # multiselect(
                    label="Which pdf file(s) should be parsed?",
                    options=list(Path(input_data).rglob("*.pdf")), 
                    format_func=lambda p: shorten_path(p, n=1), 
                    key="pdf_file"
                    )
        parse_config.file_names = st.session_state["pdf_file"] # html_select

        # st.write(f"You selected {len(files_pdf)} files:")
        # for idx, file in enumerate(files_pdf): 
    with col2:
        st.write(f"\n\nSelected:\t", shorten_path(pdf_file, 1))

    st.divider()

    # with file_preview:
    st.subheader("File Preview")
        # for idx, file in enumerate(files_pdf):
            # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
            #             unsafe_allow_html=True)
            
            # html_str = read_html_file(f"{input_data}/{file}")
            # , *, height=500, key=None)

    with st.expander(f"**File '{Path(pdf_file).stem}'**"):
                # st.html(html_str[:500])
            # st.pdf(pdf_file)

        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()

        pdf_viewer(input=pdf_bytes, width=300)

    st.divider()


    st.divider()
    st.subheader("Run Settings")

    col1, col2 = st.columns(2)

    with col1:
        # st.pills(
        #     label="HTML parser", 
        #     options=["html.parser", "lxml", "html5lib"], 
        #     selection_mode="single",
        #     key="parser_html"
        #     )
        
        # if st.session_state["parser_html"] in ["lxml", "html5lib"]:
        #     st.error("Selected parser is most likely not yet installed.")

        # parse_config.pdf.parser = st.session_state["parser_html"]

        st.toggle(
            label="Parse all pages?",
            key="parse_pdf_all"
            )

        n_pages = pdf_page_count(pdf_file)

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

        st.pills(
            label="Save file", 
            options=["info", "html", "md", "txt", "extract"], 
            selection_mode="multi",
            key="pdf_save"
            )

        parse_config.pdf.save = st.session_state["pdf_save"]
        
    with col2:    
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

    if "pdf_parsed" not in st.session_state:
        st.session_state["pdf_parsed"] = "ready"


    data_processed = os.getenv("DATA_PROCESSED")
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
        # for f_path in files_pdf:

        f_name = Path(pdf_file).stem

        t_stamp = app_session.timestamp 
        save_folder = Path(f"{data_processed}/pdf_files/extracted/{t_stamp}_{f_name}")        

        parse_context = ParseContext(
                            parse_settings=parse_config,
                            general_settings=general_settings,
                            save_folder=save_folder,
                            save_name=f"{f_name}_extracted",
                            text_type="pdf",
                            timestamp=now
                            )
        parse_context.encoder=app_session.encoder
        parse_context.logger=app_session.logger
            
        app_session.run_context = parse_context
        
        feat_enricher = FeatureEnricher(
                                    parse_context=parse_context,
                                    # encoder=app_session.encoder
                                    )
            
        pdf_extractor = PDFCleanExtractor(
                                        parse_context=parse_context,
                                        enricher=feat_enricher
                                        )

              
        # pdf_assembler = BaseAssembler(run_context=run_context)
                    
            # html_extract = 
        extract_pdf_file(
                    extractor=pdf_extractor, 
                    parse_context=parse_context
                    ).bind(
                        post_process_pdf
                        ).bind(
                            assemble_single_pdf
                            )
        # html_assembler.render_text_file)
            
        st.session_state["pdf_parsed"] = "done"

    # st.markdown("**Under Construction**")
