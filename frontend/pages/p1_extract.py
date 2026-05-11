##
# imports
import streamlit as st
import requests
from pathlib import Path

from src.core.memory import session
from frontend.pages.p0_start import INPUT_FOLDER, FILE_FOLDER
from src.utils.dict_helper import load_dict

config = session.model_config
extract_dict = config.get("extraction", {})
request_dict = extract_dict["request_api"]
# {
#         ".pdf": "http://localhost:5678/webhook-test/extract_pdf",
#         ".txt": "",
#         ".md": "",
#         ".xls": "",
#         ".doc": ""
#         }

def show():
    st.header("🔍 Extraktion / Parsing")

    st.divider()
    
    file_name = st.session_state["selected_file"]
     #  = str(dst_path)
    
    suffix = file_name.suffix()

    st.markdown(f"Extraktion der Datei {file_name}")
    
    if st.button("Extraktion starten", 
              type="primary"):

        requests.post(
                    REQUEST_DICT[suffix],
                    json={
                        "file_name": str(file_name),
                        "folder": str(INPUT_FOLDER),
                        "config": config
                        },
                    timeout=30
                    )
        # text = extract_pdf(file_name=file_name,
        #                    folder=INPUT_FOLDER,
        #                    config=config)   # " --> SEND API-REQUEST"

    result_path = Path(f"{FILE_FOLDER}/{file_name}")    
    
    if result_path.exists:
        text = load_dict(result_path)

        st.write(text)

    else:
        st.write("Warte auf Abschluss Extraktion...")

    answer = " --> GET API-ANSWER"
    if answer:
        "show text zur überprüfung VOR nächsten Schritt"



