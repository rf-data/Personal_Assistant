## B_p0_ETL_html.py
# imports
import os
from pathlib import Path
from datetime import datetime
import streamlit as st

from src.core.memory import app_session, ParseContext 

from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.html_extractor import HTMLCleanExtractor
from src.model_tools_parsing.apollo_extractor import ApolloCleanExtractor
from src.model_tools_parsing.base_assembler import BaseAssembler

from src.tools_parsing.extract_html import extract_html_file

from src.utils.path_helper import shorten_path  
# from src.utils.text_file_helper import save_text_file
from src.utils.html_helper import read_html_file


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

        input_data = os.getenv("DATA_INPUT")
        assert input_data is not None

        files_html = st.selectbox(       # multiselect(
                    label="Which html file(s) should be parsed?",
                    options=list(Path(input_data).rglob("*.html")), 
                    format_func=lambda p: shorten_path(p, n=1), 
                    # for f in Path(input_data).iterdir()
                    #         if f.suffix == ".html"],
                    key="files_html"
                    )
        parse_config.file_names = st.session_state["files_html"] # html_select

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

        parse_config.html.parser = st.session_state["parser_html"]


        st.pills(
            label="Save file", 
            options=["info", "html", "md", "txt"], 
            selection_mode="multi",
            key="save_html"
            )

        parse_config.html.save = st.session_state["save_html"]
        
    with col2:    
        st.pills(
            label="Assemble format", 
            options=["md", "txt"], 
            default=["md", "txt"], 
            selection_mode="multi",
            key="assemble_html"
            )
        
        parse_config.html.assemble = st.session_state["assemble_html"]

        st.toggle(label="Apollo",
                  key="apollo_html")
        parse_config.html.apollo = st.session_state["apollo_html"]

        st.toggle(label="Scrape_images",
              key="image_html")
        parse_config.html.scrape_images = st.session_state["image_html"]

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

            t_stamp = app_session.timestamp 
            save_folder = Path(f"{data_processed}/html_files/extracted/{t_stamp}_{f_name}")        

            parse_context = ParseContext(
                                    parse_settings=parse_config,
                                    save_folder=save_folder,
                                    save_name=f"{f_name}_extracted",
                                    text_type="html",
                                    timestamp=now
                                    )
            parse_context.encoder=app_session.encoder
            

            feat_enricher = FeatureEnricher(
                                    parse_context=parse_context,
                                    # encoder=app_session.encoder
                                    )
            if st.session_state["apollo_html"]:
                # st.write("Under Construction ")
                html_extractor = ApolloCleanExtractor(
                                                parse_context=parse_context,
                                                enricher=feat_enricher
                        )
                    # html_assembler=ApolloCleanExtractor(
                    #                         run_context=run_context
                    #                             )
            else:
                html_extractor = HTMLCleanExtractor(
                                                parse_context=parse_context,
                                                enricher=feat_enricher
                        )

              
            html_assembler = BaseAssembler(parse_context=parse_context)
                    
                # html_extract = 
            extract_html_file(
                        extractor=html_extractor, 
                        parse_context=parse_context
                        ).bind(html_assembler.render_text_file)
            
        st.session_state["html_parsed"] = "done"

        # if "md" in run_config.html.assemble:
        #     assembler.render_text_file(html_extract)

        # if "txt" in run_config.html.assemble:
        #     assembler.render_plain_text(html_extract)
            
            # text = assembler.render_markdown(html_extract)
                # text = md(text)
            
            
    # run_context.run_settings = app_session.run_settings.html

   