## A_p2_emails.py
# imports
import streamlit as st
from docx import Document
from datetime import datetime

import os
from pathlib import Path

from src.utils.path_helper import shorten_path  
from src.utils.streamlit_helper import st_file_preview

from src.core.memory import app_session, ParseContext 

from src.tools_parsing.extract_word import extract_word

# input_data = os.getenv("DATA_INPUT")
# assert input_data is not None

data = os.getenv("DATA_DIR")
assert data is not None

docx_data= os.getenv("DATA_DOCX")
assert docx_data is not None

# data_processed = os.getenv("DATA_PROCESSED")
# assert data_processed is not None

folder_options = [
        f"{docx_data}/input",
        f"{docx_data}/raw",
        f"{data}/_QMS_apo",
        f"{docx_data}/processed",
        ]

def show():
    st.header("🏠 Startseite ")
    st.subheader("**ETL Word files**")


    parse_config = app_session.parse_settings
    general_settings = app_session.general_settings

    st.divider()

    
    # with col1:

    # input_data = f"{docx_data}/input"
    data_processed = f"{docx_data}/processed"
    
    docx_folder= st.pills(
            "**Select data folder**", 
            options=folder_options, 
            selection_mode="single", 
            format_func=lambda p: shorten_path(p, n=1),
            # key="docx_folder"
            )
    
    if docx_folder:
        docx_file = st.selectbox(
                    label="File", 
                    options=list(Path(docx_folder).rglob("*.docx")), 
                    format_func=lambda p: shorten_path(p, n=1)
                    # selection_mode="single"
                    )
       
        # st.markdown(f"Your selected files of type '{preview_suffix}' in folder '{preview_folder}'.")
        st.divider()

    if docx_folder and docx_file:
        with st.expander(f"File Preview: '{Path(docx_file).stem}'"):
            st.markdown("### File Preview")
            st_file_preview(docx_file)

            st.divider()

            st.markdown("### File Structure")
            # with st.expander("File Structure"):
            doc = Document(docx_file)

            for i, p in enumerate(doc.paragraphs):
                st.write(
                    f"{i:03d} | {p.style.name:20} | {repr(p.text)}"
                )

    st.divider()
    st.subheader("Run Settings")

    if "docx_parsed" not in st.session_state:
        st.session_state["docx_parsed"] = "ready"

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'docx_parsed': {st.session_state['docx_parsed']}")
    # if isinstance(files_pdf, str):
    #     files_pdf = [files_pdf]

    left, right = st.columns(2)

    if (left.button("Reset", type="primary")
        and st.session_state["docx_parsed"] is not None):
        st.session_state["docx_parsed"] = "ready"

    if (right.button("Start run") 
        and st.session_state["docx_parsed"] in ["ready", None]):
            # st.session_state["parsed"] = None
        # for file in pdf_files:
        f_name = Path(docx_file).stem

        t_stamp = app_session.timestamp 
        save_folder = Path(f"{data_processed}/extracted/{t_stamp}_{f_name}")        

        parse_config.file_name = str(docx_file)

        parse_context = ParseContext(
                                parse_settings=parse_config,
                                general_settings=general_settings,
                                save_folder=save_folder,
                                save_name=f"{f_name}_extracted",
                                text_type="docx",
                                timestamp=now
                                )
        parse_context.encoder=app_session.encoder
        parse_context.logger=app_session.logger
                
        app_session.run_context = parse_context

        file_dict = extract_word(docx_file)
        
        st.json(file_dict)
        # run_word_extraction(parse_context)

        st.session_state["docx_parsed"] = "done"
    # with col2:
    #     st.write(f"Selected:")
    #     for idx, file in enumerate(pdf_files):
    #         st.write(f"#{idx}\t", shorten_path(file, 1))
    #     preview_file = st.selectbox(       # selectbox, multiselect(
    #                 label="Which file should be rendered?",
    #                 options=[f for f in Path(preview_folder).iterdir()
    #                          if f.suffix in preview_suffix], 
    #                 format_func=lambda p: shorten_path(p, n=1), 
    #                 # key="pdf_files"
    #                 )
        
    

    # st.markdown("**Under Construction**")
