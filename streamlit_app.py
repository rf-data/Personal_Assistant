## streamlit_app.py
# imports
# import os
from datetime import datetime

import streamlit as st
from tiktoken import encoding_for_model


from src.utils.dict_helper import get_yaml_config
from frontend.pages import (
                        A_p0_cockpit, 
                        A_p1_simple_LLM_actions, 
                        A_p2_file_system,
                        A_p3_transcribe,
                        A_p4_emails, 
                        A_p5_monitoring, 
                        B_p0_ETL_html,
                        B_p1_ETL_pdf,
                        B_p2_ETL_wiki_page,
                        B_p3_ETL_json_nb,
                        B_p4_ETL_docx,
                        B_p5_ETL_md,
                        B_p6_ETL_OCR_text,
                        B_p7_ETL_plain_text,
                        C_p0_ETL_excel,
                        C_p1_ETL_csv_parquet,
                        C_p2_ETL_matlab,
                        D_p0_EDA_dash,
                        D_p1_pca, 
                        D_p2_eval_dash,
                        E_p0_rag_status,
                        E_p1_chunk_embed,
                        E_p2_sop_generation,
                        F_p0_development
                        )

from src.core.logger import create_logger

# import sys
# from pathlib import Path
from src.core.memory import app_session
from src.core.config import GeneralSettings, ParseSettings
from src.utils.general_helper import load_env_vars


load_env_vars() # (name=".env.frontend")


general_config = get_yaml_config("streamlit_general", 
                                 model=GeneralSettings)

parse_config = get_yaml_config("streamlit_run", 
                                 model=ParseSettings)

# general_config = config.get("general_args", {})
log_name = parse_config.name_log
name_logfile = parse_config.name_logfile

model_name = parse_config.llm_model
encoder = encoding_for_model(model_name)
app_session.encoder = encoder

app_session.general_settings = general_config  # str(selected_file)
app_session.parse_settings = parse_config

# setup logger
# now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# app_session.timestamp = now

today = datetime.today().strftime("%Y-%m-%d")
app_session.timestamp = today

logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")
app_session.logger = logger


# === STATE INIT ===
if "page" not in st.session_state:
    st.session_state.page = "General Features"

if "subpage" not in st.session_state:
    st.session_state.subpage = "RAG System"

if "navigate_to" not in st.session_state:
    st.session_state.navigate_to = None


# # === SIDEBAR LOGIC ===
# # Session-State
# if "page" not in st.session_state:
#     st.session_state.page = "General Tools"
    # hide_sidebar()   


# ------ SIDEBAR: GLOBAL NAVIGATION ------
st.sidebar.markdown("#### 🎥 Personal assistent")

with st.sidebar:        # Page Switching
    st.header("📁 Division")
    if st.session_state.navigate_to is not None:
        st.session_state.tool = st.session_state.navigate_to
        st.session_state.navigate_to = None

    st.radio(
            "Division",
            options=[
                "General Features",
                "Extract Text",
                "Extract Data",
                "DataViz & Dashboards",
                "RAG System",
                "Development",
                ],
            key="page",
            label_visibility="collapsed"
            )

    st.markdown("---")

PROJECT_MAP = {
    "General Features": ("General Features", "Cockpit"),
    "Extract Text": ("Extract Text", "ETL HTML"),
    "Extract Data": ("Extract Data", "ETL Excel"),
    "DataViz & Dashboards": ("DataViz & Dashboards", "EDA_dash"),
    "RAG System": ("RAG System", "RAG_Status"),
    "Development": ("Development", "Development_Area")
    }

page, default_sub = PROJECT_MAP[st.session_state.page]
if st.session_state.page != page:
    st.session_state.page = page
    st.session_state.subpage = default_sub


# ------ SIDEBAR: PROJECT-SPECIFIC ELEMENTS ------
with st.sidebar:
    if st.session_state.page == "General Features":
        st.subheader("General Features")

        st.radio(
                "Choose a tool",
                options=[
                    "Cockpit",
                    "simple LLM actions",
                    "File System",
                    "Transcription",
                    "E-Mail & Calender",
                    "Monitoring"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )

    elif st.session_state.page == "Extract Text":
        st.subheader("Extract Text")

        st.radio(
                "Abschnitt",
                options=[
                    "ETL html_file",
                    "ETL pdf_file",
                    "ETL wiki_page",
                    "ETL json_notebook",
                    "ETL word",
                    "ETL md_file",
                    "ETL OCR text",
                    "ETL plain_text",
                    # "ETL URL",
                    ],
                key="subpage",
                label_visibility="collapsed"
            )
 
    elif st.session_state.page == "Extract Data":
        st.subheader("Extract Data")

        st.radio(
                "Abschnitt",
                options=[
                    "ETL Excel",
                    "ETL CSV & Parquet",
                    "ETL MatLab"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )

    elif st.session_state.page == "DataViz & Dashboards":
        st.subheader("DataViz & Dashboards")

        st.radio(
                "Abschnitt",
                options=[
                    "EDA Dashboard",
                    "PCA",
                    # "Evaluation Dashboard",
                    ],
                key="subpage",
                label_visibility="collapsed"
            )
     # "Development": ("Development_Area", None)

    elif st.session_state.page == "RAG System":
        st.subheader("RAG System")

        st.radio(
                "Abschnitt",
                options=[
                    "RAG_Status",
                    "Chunk & Embed",
                    "SOP_Generation"
                    # "Evaluation Dashboard",
                    ],
                key="subpage",
                label_visibility="collapsed"
            )
        
    elif st.session_state.page == "Development":
        st.subheader("Development")

        st.radio(
                "Abschnitt",
                options=[
                    "Development_Area",
                    # "Markowitz",
                    # "Recommendation"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )
        
# === ROUTING ===

page = st.session_state.page
sub = st.session_state.subpage

if page == "General Features":
    if sub == "Cockpit": A_p0_cockpit.show()
    elif sub == "simple LLM actions": A_p1_simple_LLM_actions.show()
    elif sub == "File System": A_p2_file_system.show()
    elif sub == "Transcription": A_p3_transcribe.show()
    elif sub == "E-Mails & Calender": A_p4_emails.show()
    elif sub == "Monitoring": A_p5_monitoring.show()

elif page == "Extract Text":
    if sub == "ETL html_file": B_p0_ETL_html.show()
    elif sub == "ETL pdf_file": B_p1_ETL_pdf.show()
    elif sub == "ETL wiki_page": B_p2_ETL_wiki_page.show()
    elif sub == "ETL json_notebook": B_p3_ETL_json_nb.show()
    elif sub == "ETL word": B_p4_ETL_docx.show()
    elif sub== "ETL md_file": B_p5_ETL_md.show()
    elif sub== "ETL OCR text": B_p6_ETL_OCR_text.show()
    elif sub == "ETL plain_text": B_p7_ETL_plain_text.show()
  
    # elif sub == "ETL URL": A_p1_file_upload.show()

elif page == "Extract Data":
    if sub == "ETL Excel": C_p0_ETL_excel.show()
    elif sub == "ETL CSV & Parquet": C_p1_ETL_csv_parquet.show()
    elif sub == "ETL MatLab": C_p2_ETL_matlab.show()

elif page == "DataViz & Dashboards":
    if sub == "EDA Dashboard": D_p0_EDA_dash.show()
    elif sub == "PCA": D_p1_pca.show()
    elif sub == "Evaluation Dashboard": D_p2_eval_dash.show()

elif page == "RAG System":
    if sub == "RAG_Status": E_p0_rag_status.show()
    elif sub == "Chunk & Embed": E_p1_chunk_embed.show()
    elif sub == "SOP_Generation": E_p2_sop_generation.show()

elif page == "Development":
    if sub == "Development_Area": E_p1_chunk_embed.show()


# PAGES_PRESENTATION[presentation]()
