## A_p2_emails.py
# imports
from datetime import datetime
from pathlib import Path

import streamlit as st
from docx import Document

from src.core.config import parsing_env_vars
from src.core.memory import ParseContext, app_session
from src.model_tools_parsing.base_assembler import BaseAssembler
from src.model_tools_parsing.docx_extractor import DOCXCleanExtractor
from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.utils.path_helper import shorten_path
from src.utils.streamlit_helper import st_file_preview

# from src.tools_parsing.extract_docx import extract_docx

data = parsing_env_vars.data_dir
docx_data = parsing_env_vars.data_docx

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

    docx_folder = st.pills(
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
            format_func=lambda p: shorten_path(p, n=1),
            # selection_mode="single"
        )

        parse_config.file_name = docx_file
        # parse_config.run_id = Path(docx_file).stem
        # st.markdown(f"Your selected files of type '{preview_suffix}' in folder '{preview_folder}'.")
        st.divider()

    if docx_folder and docx_file:
        with st.expander(f"**File Preview:** '{Path(docx_file).stem}'"):
            st.markdown("### File Preview")
            st_file_preview(docx_file)

            # st.divider()

        with st.expander(f"**File Structure** '{Path(docx_file).stem}'"):
            st.markdown("### File Structure")
            # with st.expander("File Structure"):
            doc = Document(docx_file)

            for i, p in enumerate(doc.paragraphs):
                st.write(f"{i:03d} | {p.style.name:20} | {repr(p.text)}")

            st.divider()

        with st.expander(f"**Tables'** {Path(docx_file).stem}'"):
            st.markdown("### Tables")
            st_file_preview(docx_file, table=True)

    st.divider()
    st.subheader("Run Settings")
    col1, col2 = st.columns(2)

    # with col1:
    rag_ready = col1.toggle(
        label="Perform RAG-ready extraction",
        # key="pdf_image"
    )

    col1.toggle(label="Scrape_images", key="image_docx")
    parse_config.docx.scrape_images = st.session_state["image_docx"]

    col1.selectbox(
        label="Parsing mode 'table data'",
        options=["long", "brief"],
        key="tbl_text_mode",
    )
    parse_config.docx.tbl_text_mode = st.session_state["tbl_text_mode"]

    col2.pills(
        label="Save file",
        options=[
            "info",
            # "html",
            "md",
            "txt",
        ],
        selection_mode="multi",
        key="save_docx",
    )

    parse_config.docx.save = st.session_state["save_docx"]

    col2.pills(
        label="Assemble format",
        options=["md", "txt"],
        default=["md", "txt"],
        selection_mode="multi",
        key="assemble_docx",
    )

    parse_config.docx.assemble = st.session_state["assemble_docx"]

    if "docx_parsed" not in st.session_state:
        st.session_state["docx_parsed"] = "ready"

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'docx_parsed': {st.session_state['docx_parsed']}")
    # if isinstance(files_pdf, str):
    #     files_pdf = [files_pdf]

    left, right = st.columns(2)

    if (
        left.button("Reset", type="primary")
        and st.session_state["docx_parsed"] is not None
    ):
        st.session_state["docx_parsed"] = "ready"

    if right.button("Start run") and st.session_state["docx_parsed"] in ["ready", None]:
        # st.session_state["parsed"] = None
        # for file in pdf_files:
        f_name = Path(docx_file).stem

        t_stamp = app_session.timestamp
        save_folder = Path(
            f"{data_processed}/{'ready' if rag_ready else 'test'}_{t_stamp}_{f_name}"
        )
        # {t_stamp}_{f_name}/
        # Path(f"{data_processed}/{t_stamp}_{f_name}")

        parse_config.file_name = str(docx_file)

        parse_context = ParseContext(
            parse_settings=parse_config,
            general_settings=general_settings,
            save_folder=save_folder,
            save_name=f"{f_name}",
            text_type="docx",
            timestamp=now,
        )
        parse_context.encoder = app_session.encoder
        parse_context.logger = app_session.logger

        app_session.run_context = parse_context

        feat_enricher = FeatureEnricher(
            parse_context=parse_context,
            # encoder=app_session.encoder
        )

        docx_extractor = DOCXCleanExtractor(
            parse_context=parse_context, enricher=feat_enricher
        )

        docx_assembler = BaseAssembler(parse_context=parse_context)

        # file_dict =
        docx_extractor.extract(docx_file).bind(docx_assembler.render_text_file)

        # extract_docx(docx_file)

        # st.json(file_dict.unwrap().model_dump())
        # run_word_extraction(parse_context)

        # st.session_state["docx_parsed"] = "done"
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
