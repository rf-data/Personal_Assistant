## B_p1_ETL_html.py
# imports
import os
from pathlib import Path
from datetime import datetime
import streamlit as st

from src.core.memory import app_session, RunContext 

from src.model_tools.feature_enricher import FeatureEnricher
from src.model_tools.html_extractor import HTMLCleanExtractor
from src.model_tools.apollo_extractor import ApolloCleanExtractor
from src.model_tools.base_assembler import BaseAssembler

from src.tools.extract_html import extract_html_file

from src.utils.path_helper import shorten_path  
# from src.utils.text_file_helper import save_text_file
from src.utils.html_helper import read_html_file


def show():
    st.header("ETL HTML text")
    
    run_config = app_session.run_settings
    st.divider()

    file_select, file_preview = st.columns(2)

    with file_select:
        st.subheader("🖼️ Select an html file")

        input_data = os.getenv("DATA_INPUT")
        assert input_data is not None

        files_html = st.multiselect(
                    label="Which html file(s) should be parsed?",
                    options=[shorten_path(f, n=1) for f in Path(input_data).iterdir()
                            if f.suffix == ".html"],
                    key="files_html"
                    )
        run_config.file_names = st.session_state["files_html"] # html_select

        st.write(f"You selected {len(files_html)} files:")
        for idx, file in enumerate(files_html): 
            st.write(f"({idx}) ",files_html)

    with file_preview:
        st.subheader("File Preview")
        for idx, file in enumerate(files_html):
            # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
            #             unsafe_allow_html=True)
            
            html_str = read_html_file(f"{input_data}/{file}")

            with st.expander(f"**File #{idx}: '{Path(file).stem}'**"):
                st.html(html_str[:500])

            st.divider()


    st.divider()
    st.subheader("Run Settings")

    col1, col2 = st.columns(2)
    
    with col1:
        st.pills(
            label="HTML parser", 
            options=["html.parser", "lxml", "html5lib"], 
            selection_mode="single",
            key="parser_html"
            )
        
        if st.session_state["parser_html"] in ["lxml", "html5lib"]:
            st.error("Selected parser is most likely not yet installed.")

        run_config.html.parser = st.session_state["parser_html"]


        st.pills(
            label="Save file", 
            options=["info", "html", "md", "txt"], 
            selection_mode="multi",
            key="save_html"
            )

        run_config.html.save = st.session_state["save_html"]
        
    with col2:    
        # st.pills(
        #     label="Assemble format", 
        #     options=["md", "txt"], 
        #     selection_mode="multi",
        #     key="assemble_html"
        #     )
        
        # run_config.html.assemble = st.session_state["assemble_html"]

        st.toggle(label="Apollo",
                  key="apollo_html")
        run_config.html.apollo = st.session_state["apollo_html"]

        st.toggle(label="Scrape_images",
              key="image_html")
        run_config.html.scrape_images = st.session_state["image_html"]

    if "html_parsed" not in st.session_state:
        st.session_state["html_parsed"] = "ready"


    data_processed = os.getenv("DATA_PROCESSED")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'html_parsed': {st.session_state['html_parsed']}")
    if isinstance(files_html, str):
        files_html = [files_html]

    left, right = st.columns(2)

    if (left.button("Reset", type="primary")
        and st.session_state["html_parsed"] is not None):
        st.session_state["html_parsed"] = "ready"

    if (right.button("Start run") 
        and st.session_state["html_parsed"] in ["ready", None]):
            # st.session_state["parsed"] = None
        for f_path in files_html:

            f_name = Path(f_path).stem

            run_context = RunContext(
                                    run_settings=run_config,
                                    save_folder=Path(f"{data_processed}/html_files/extracted/{now}_{f_name}"),
                                    save_name=f"{f_name}_extracted",
                                    text_type="html",
                                    timestamp=now
                                    )
            run_context.encoder=app_session.encoder
                # if st.session_state["apollo_html"]:
                #     st.write("Under Construction ")
                #     # html_extractor = ApolloCleanExtractor(
                #     #                             run_context=run_context
                #     #     )
                #     # html_assembler=ApolloCleanExtractor(
                #     #                         run_context=run_context
                #     #                             )

            feat_enricher = FeatureEnricher(
                                    run_context=run_context,
                                    # encoder=app_session.encoder
                                    )
                # else:
            html_extractor = HTMLCleanExtractor(
                                                run_context=run_context,
                                                enricher=feat_enricher
                        )
            html_assembler = BaseAssembler(run_context=run_context)
                    
                # html_extract = 
            extract_html_file(
                        extractor=html_extractor, 
                        run_context=run_context
                        ).bind(html_assembler.render_text_file)
            
        st.session_state["html_parsed"] = "done"

        # if "md" in run_config.html.assemble:
        #     assembler.render_text_file(html_extract)

        # if "txt" in run_config.html.assemble:
        #     assembler.render_plain_text(html_extract)
            
            # text = assembler.render_markdown(html_extract)
                # text = md(text)
            
            
    # run_context.run_settings = app_session.run_settings.html

   