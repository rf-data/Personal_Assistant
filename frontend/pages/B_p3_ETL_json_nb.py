## B_p3_ETL_json_nb.py
# imports
import os
from pathlib import Path
from datetime import datetime
import streamlit as st

from src.core.memory import app_session, ParseContext 

from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.base_assembler import BaseAssembler
from src.model_tools_parsing.notebook_extractor import NoteBookCleanExtractor

from src.tools_parsing.extract_notebook import extract_notebook_json
from src.utils.path_helper import shorten_path  
from src.utils.dict_helper import load_dict

def show():
    # st.header("🏠 Startseite ")
    st.subheader("**JSON Notebooks**")

    parse_config = app_session.parse_settings
    st.divider()

    file_select, file_preview = st.columns(2)

    with file_select:
        st.subheader("🖼️ Select an JSON file")

        nb_data = os.getenv("DATA_JSON_NB")
        assert nb_data is not None

        input_data = f"{nb_data}/input"

        files_json = st.multiselect(
                    label="Which html file(s) should be parsed?",
                    options=list(Path(input_data).rglob("*.json")), 
                    format_func=lambda p: shorten_path(p, n=1), 
                    key="files_json"
                    )
        parse_config.file_names = st.session_state["files_json"] # html_select

        st.write(f"You selected {len(files_json)} files:")
        for idx, file in enumerate(files_json): 
            st.write(f"({idx}) ",files_json)

    with file_preview:
        st.subheader("File Preview")
        for idx, file in enumerate(files_json):
            # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
            #             unsafe_allow_html=True)
            
            nb_dict = load_dict(f"{input_data}/{file}")

            with st.expander(f"**File #{idx}: '{Path(file).stem}'**"):
                st.json(nb_dict)

            st.divider()


    st.divider()
    # st.subheader("Run Settings")

    # col1, col2 = st.columns(2)
    
    # with col1:
    st.pills(
            label="JSON_NB parser", 
            options=["html.parser", "lxml", "html5lib"], 
            selection_mode="single",
            key="parser_json"
            )
        
    if st.session_state["parser_json"] in ["lxml", "html5lib"]:
        st.error("Selected parser is most likely not yet installed.")

    parse_config.json_nb.parser = st.session_state["parser_json"]


    #     st.pills(
    #         label="Save file", 
    #         options=["info", "html", "md", "txt"], 
    #         selection_mode="multi",
    #         key="save_html"
    #         )

    #     run_config.html.save = st.session_state["save_html"]
        
    # with col2:    
    st.pills(
            label="Assemble format", 
            options=["md", "txt"], 
            default=["md", "txt"], 
            selection_mode="multi",
            key="assemble_json"
            )
        
    parse_config.json_nb.assemble = st.session_state["assemble_json"]

        # st.toggle(label="Apollo",
        #           key="apollo_html")
        # run_config.html.apollo = st.session_state["apollo_html"]

    st.toggle(label="Scrape_images",
              key="image_json")
    parse_config.json_nb.scrape_images = st.session_state["image_json"]

    if "json_parsed" not in st.session_state:
        st.session_state["json_parsed"] = "ready"

    data_processed = f"{nb_data}/processed"
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    st.divider()
    st.subheader("Start Run")

    st.markdown(f"Status 'json_parsed': {st.session_state['json_parsed']}")
    if isinstance(files_json, str):
        files_json = [files_json]

    left, right = st.columns(2)

    if (left.button("Reset", type="primary")
        and st.session_state["json_parsed"] is not None):
        st.session_state["json_parsed"] = "ready"

    if (right.button("Start run") 
        and st.session_state["json_parsed"] in ["ready", None]):
            # st.session_state["parsed"] = None
        
                # html_extract = 
        for f_path in files_json:

            f_name = Path(f_path).stem

            t_stamp = app_session.timestamp 
            save_folder = Path(f"{data_processed}/notebooks/extracted/{t_stamp}_{f_name}")        

            run_context = ParseContext(
                                parse_settings=parse_config,
                                save_folder=save_folder,
                                save_name=f"{f_name}_extracted",
                                text_type="json_nb",
                                timestamp=now
                                        )
            run_context.encoder=app_session.encoder
                

            feat_enricher = FeatureEnricher(
                                        parse_context=parse_context,
                                        # encoder=app_session.encoder
                                        )
            nb_extractor = NoteBookCleanExtractor(
                                        parse_context=parse_context,
                                        enricher=feat_enricher
                            )
                
                
            json_assembler = BaseAssembler(parse_context=parse_context)
                        
        
            extract_notebook_json(
                            extractor=nb_extractor, 
                            parse_context=parse_context,
                            f_name=f_name
                            ).bind(
                                json_assembler.render_text_file
                                )
            
        st.session_state["json_parsed"] = "done"

        # if "md" in run_config.html.assemble:
        #     assembler.render_text_file(html_extract)

        # if "txt" in run_config.html.assemble:
        #     assembler.render_plain_text(html_extract)
            
            # text = assembler.render_markdown(html_extract)
                # text = md(text)
            
            
    # run_context.run_settings = app_session.run_settings.html

   
