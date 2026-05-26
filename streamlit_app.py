## streamlit_app.py
# imports
import os
from datetime import datetime

import streamlit as st

import src.utils.dict_helper as dh
from gmp_compliance.frontend.pages import (
                                        A_p0_wiki_search, A_p1_file_upload,
                                        B_p0_ETL_plain_text
                                        )
from src.core.logger import create_logger

# import sys
# from pathlib import Path
from src.core.memory import session_state
from src.core.config import Settings
from src.utils.general_helper import load_env_vars


# st_settings = Settings(
#             env_name=".env.frontend",
#             config_name="streamlit_app"
# )

load_env_vars(name=".env.frontend")
config_name = os.getenv("CONFIG_NAME")
config = dh.get_yaml_config(config_name)

general_config = config.get("general_args", {})
log_name = general_config["name_log"]
name_logfile = general_config["name_logfile"]

session_state.general_config = config  # str(selected_file)

# setup logger
today = datetime.now().strftime("%Y-%m-%d")
logger = create_logger(name=log_name, file_name=f"{today}_{name_logfile}")
session_state.logger = logger



# === STATE INIT ===
if "page" not in st.session_state:
    st.session_state.page = "general_tools"

if "subpage" not in st.session_state:
    st.session_state.subpage = None

if "navigate_to" not in st.session_state:
    st.session_state.navigate_to = None


# === SIDEBAR LOGIC ===
# Session-State
if "page" not in st.session_state:
    st.session_state.page = "general_tools"
    # hide_sidebar()   


# ------ SIDEBAR: GLOBAL NAVIGATION ------
st.sidebar.markdown("#### 🎥 Personal assistent")

with st.sidebar:        # Page Switching
    st.header("📁 Tools")
    if st.session_state.navigate_to is not None:
        st.session_state.tool = st.session_state.navigate_to
        st.session_state.navigate_to = None

    tools = st.radio(
                "Tools",
                options=[
                    "general_tools",
                    "Extract text",
                    "Extract data"
                    ],
                key="tool",
                label_visibility="collapsed"
            )

    st.markdown("---")

PROJECT_MAP = {
    "General Tools": ("general_tools", "query"),
    "Extract text": ("extract_text", None),
    "Extract data": ("extract_data", None)
}
page, default_sub = PROJECT_MAP[st.session_state.project]
if st.session_state.page != page:
    st.session_state.page = page
    st.session_state.subpage = default_sub


# ------ SIDEBAR: PROJECT-SPECIFIC ELEMENTS ------
with st.sidebar:
    if st.session_state.page == "general_tools":
        st.subheader("General Tools")

        st.radio(
                "Choose a tool",
                options=[
                    "WikiQuery",
                    "File Upload",
                    # "Chat with files"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )
    
    elif st.session_state.page == "extract_text":
        st.subheader("Extract text")

        st.radio(
                "Abschnitt",
                options=[
                    "ETL plain_text",
                    "ETL HTML",
                    "ETL JSON_notebook",
                    "ETL pdf_file",
                    "ETL URL",
                    "ETL MS Word"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )

    elif st.session_state.page == "extract_data":
        st.subheader("Extract data")

        st.radio(
                "Abschnitt",
                options=[
                    "ETL csv parquet",
                    "ETL excel"
                    ],
                key="subpage",
                label_visibility="collapsed"
            )



# === ROUTING ===

page = st.session_state.page
sub = st.session_state.subpage

if page == "general_tools":
    if sub == "WikiQuery": A_p0_wiki_search.show()
    elif sub == "File Upload": A_p1_file_upload.show()
    # elif sub == "File Chat": A_p2_file_chat.show()
    

elif page == "extract text":
    if sub == "ETL plain_text": B_p0_ETL_plain_text.show()
    # elif sub == "ETL HTML": A_p1_file_upload.show()
    # elif sub == "ETL JSON_notebook": A_p1_file_upload.show()
    # elif sub == "ETL pdf_file": A_p1_file_upload.show()
    # elif sub == "ETL URL": A_p1_file_upload.show()
    # elif sub == "ETL MS Word": A_p1_file_upload.show()



# PAGES_PRESENTATION[presentation]()
