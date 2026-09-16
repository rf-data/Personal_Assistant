## B_p0_ETL_html.py
# imports
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.core.config import folder_env_vars
from src.core.memory import ParseContext, app_session
from src.model_parsing.apollo_extractor import ApolloCleanExtractor
from src.model_parsing.base_assembler import BaseAssembler
from src.model_parsing.feature_enricher import FeatureEnricher
from src.model_parsing.html_extractor import HTMLCleanExtractor
from src.tools_parsing.extract_html import extract_html_file
from src.utils.path_helper import move_file, shorten_path

# from src.utils.text_file_helper import save_text_file
from src.utils.streamlit_helper import st_file_preview

"""
TO-DOs:
- move file after processing
- allow preview on processed file(s)

"""


def show():
    st.header("**ETL HTML text**")

    parse_config = app_session.parse_settings
    st.divider()

    file_select, file_preview = st.columns(2)

    with file_select:
        st.subheader("🖼️ Select an html file")

        html_data = folder_env_vars.data_html
        data_dir = folder_env_vars.data_dir

        input_data = f"{data_dir}/input"

        files_html = st.multiselect(  # multiselect(
            label="Which html file(s) should be parsed?",
            options=list(Path(input_data).rglob("*.html")),
            format_func=lambda p: shorten_path(p, n=1),
            # for f in Path(input_data).iterdir()
            #         if f.suffix == ".html"],
            key="files_html",
        )
        # st.session_state["files_html"] # html_select

    with file_preview:
        st.subheader("File Preview")
        st.write(
            f"You selected {len(files_html) if len(files_html) > 0 else '0'} files:"
        )

        for idx, file in enumerate(files_html, start=1):
            st.write(f"({idx}) {shorten_path(file, 1)}")

    for idx, file in enumerate(files_html):
        # with st.expander(f"({idx}) {shorten_path(file, 1)}"):
        st_file_preview(file)
        # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
        #             unsafe_allow_html=True)

        # st.divider()

    st.divider()
    st.subheader("Run Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.pills(
            label="HTML parser",
            options=["html.parser", "lxml", "html5lib"],
            selection_mode="single",
            key="parser_html",
        )

        if st.session_state["parser_html"] in ["lxml", "html5lib"]:
            st.error("Selected parser is most likely not yet installed.")

        parse_config.html.parser = st.session_state["parser_html"]

        st.pills(
            label="Save file",
            options=["info", "html", "md", "txt"],
            selection_mode="multi",
            key="save_html",
        )

        parse_config.html.save = st.session_state["save_html"]

    with col2:
        st.pills(
            label="Assemble format",
            options=["md", "txt"],
            default=["md", "txt"],
            selection_mode="multi",
            key="assemble_html",
        )

        parse_config.html.assemble = st.session_state["assemble_html"]

        st.toggle(label="Apollo", key="apollo_html")
        parse_config.html.apollo = st.session_state["apollo_html"]

        st.toggle(label="Scrape_images", key="image_html")
        parse_config.html.scrape_images = st.session_state["image_html"]

    rag_ready = st.toggle(
        label="Perform RAG-ready extraction",
        # key="pdf_image"
    )

    if "html_parsed" not in st.session_state:
        st.session_state["html_parsed"] = "ready"

    # data_processed = f"{html_data}/processed"
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'html_parsed': {st.session_state['html_parsed']}")
    if isinstance(files_html, str):
        files_html = [files_html]

    left, right = st.columns(2)

    if (
        left.button("Reset", type="primary")
        and st.session_state["html_parsed"] is not None
    ):
        st.session_state["html_parsed"] = "ready"

    if right.button("Start run") and st.session_state["html_parsed"] in ["ready", None]:
        # st.session_state["parsed"] = None
        for f_path in files_html:
            f_name = Path(f_path).stem
            parse_config.file_name = f_name

            t_stamp = app_session.timestamp
            save_folder = Path(
                f"{html_data}/{'ready' if rag_ready else 'test'}_{t_stamp}_{f_name}"
            )

            parse_context = ParseContext(
                parse_settings=parse_config,
                save_folder=save_folder,
                save_name=f_name,
                text_type="html",
                timestamp=now,
            )
            parse_context.encoder = app_session.encoder

            feat_enricher = FeatureEnricher(
                parse_context=parse_context,
                # encoder=app_session.encoder
            )
            if st.session_state["apollo_html"]:
                # st.write("Under Construction ")
                html_extractor = ApolloCleanExtractor(
                    parse_context=parse_context, enricher=feat_enricher
                )
            # html_assembler=ApolloCleanExtractor(
            #                         run_context=run_context
            #                             )
            else:
                html_extractor = HTMLCleanExtractor(
                    parse_context=parse_context, enricher=feat_enricher
                )

            html_assembler = BaseAssembler(parse_context=parse_context)

            # html_extract =
            extract_html_file(
                extractor=html_extractor, parse_context=parse_context
            ).bind(html_assembler.render_text_file)

            # f_name = parse_context.parse_settings.file_name
            dst_path = f"{data_dir}/raw/{f_name}.html"

            move_file(f_path, dst_path)

        st.session_state["html_parsed"] = "done"

        # if "md" in run_config.html.assemble:
        #     assembler.render_text_file(html_extract)

        # if "txt" in run_config.html.assemble:
        #     assembler.render_plain_text(html_extract)

        # text = assembler.render_markdown(html_extract)
        # text = md(text)

    # run_context.run_settings = app_session.run_settings.html
