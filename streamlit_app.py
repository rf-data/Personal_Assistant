## streamlit_app.py
# imports
import streamlit as st
import os
from datetime import datetime
# import sys
# from pathlib import Path

from src.core.memory import session
from src.core.logger import create_logger
from frontend.pages import p0_start, p1_extract
import src.utils.general_helper as gh
import src.utils.dict_helper as dh

gh.load_env_vars(name=".env.frontend")
config_name = os.getenv("CONFIG_NAME")
config = dh.get_yaml_config(config_name)

general_config = config.get("general_args", {})
log_name = general_config["name_log"]
name_logfile = general_config["name_logfile"]

session.model_config = config      # str(selected_file)

# setup logger
today = datetime.now().strftime("%Y-%m-%d")
logger = create_logger(name=log_name, 
                        file_name=f"{today}_{name_logfile}")
session.logger = logger

# === Section 1: Project Presentation ===
st.sidebar.markdown("#### 🎥 Text-Extraktion")      
presentation = st.sidebar.radio(
    "Chapter:",
    options=[
        "🏠 Start",
        "🔍 Extraktion / Parsing"
        # "🧭 Introduction",
        # "🛠️ Pipeline & Airflow",
        # "🔌 APIs",
        # "🧪 MLflow",
        # "📦 Docker",
        # "📡 Monitoring",
        # "🏁 Conclusion",
            ],
    key="presentation",         
    index=0,
    args=("presentation",)
    )


PAGES_PRESENTATION = {
    "🏠 Home": p0_start.show,
    "🔍 Extraktion / Parsing": p1_extract.show


    # "🧭 Introduction": pres_1_intro.show,
    # "🛠️ Pipeline & Airflow": pres_2_pipelines.show,
    # "🔌 APIs": pres_3_apis.show,
    # "🧪 MLflow": pres_4_mlflow.show,
    # "📦 Docker": pres_5_docker.show,
    # "📡 Monitoring": pres_6_monitoring.show,
    # "🏁 Conclusion": pres_7_conclusion.show
            }

PAGES_PRESENTATION[presentation]()


