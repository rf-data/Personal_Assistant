## D_p1_pca.py
# imports
import os
from pathlib import Path
import streamlit as st
import pandas as pd

from src.core.memory import app_session     # , ParseContext 
from src.core.config import ParseSettings

from src.run_PCA import explained_variance_by_pca
from src.utils.path_helper import shorten_path  
# from src.utils.dict_helper import load_dict


def show():
    st.header("🏠 Startseite ")
    st.subheader("**Principal Component Analysis**")

    run_config = ParseSettings()    # app_session.parse_settings
    st.divider()

    file_select, file_preview = st.columns(2)

    with file_select:
        st.subheader("🖼️ Select a data file")

        input_data = os.getenv("DATA_INPUT")
        assert input_data is not None

        st.warning("ADAPT TO NEW FILE SYSTEM")

        pca_file = st.selectbox(
                    label="Which data file(s) should be used?",
                    options=list(Path(input_data).rglob("*.csv")), 
                    format_func=lambda p: shorten_path(p, n=1), 
                    # options=[shorten_path(f, n=1) for f in Path(input_data).iterdir()
                    #         if f.suffix == ".csv"],
                    key="files_pca"
                    )
        
         
        if isinstance(pca_file, str):
            run_config.file_names = [pca_file]
            # else pca_file
        
        # st.session_state["pca_file"] # html_select

        # st.write(f"You selected {len(pca_file)} files:")
        # for idx, file in enumerate(pca_file): 
        #     st.write(f"({idx}) ", pca_file)

    with file_preview:
        st.subheader("File Preview")
        # for idx, file in enumerate(pca_file):
            # st.markdown(f"**File #{idx}: '{Path(file).stem}'**\n",
            #             unsafe_allow_html=True)
            
        data = pd.read_csv(f"{input_data}/{pca_file}")

        with st.expander(f"**File '{Path(pca_file).stem}'**"):
            st.dataframe(data)

        st.divider()

    # st.divider()
    st.subheader("Start Run")

    if "run_pca" not in st.session_state:
        st.session_state["run_pca"] = "ready"

    st.markdown(f"Status 'run_pca': {st.session_state['run_pca']}")
    # if isinstance(pca_file, str):
    #     file_pca = [file_pca]

    left, right = st.columns(2)

    if (left.button("Reset", type="primary")
        and st.session_state["run_pca"] is not None):
        st.session_state["run_pca"] = "ready"

    pca_config = {
            "sg_window_len": 25,
            "sg_poly": 5,
            "sg_deriv": 1,
            "n_pca": 10,
            "st_viz": True
        }

    if (right.button("Start run") 
        and st.session_state["run_pca"] in ["ready", None]):
            # st.session_state["parsed"] = None
        
                # html_extract = 
        # for f_path in files_pca:

            # f_name = Path(f_path).stem

            # t_stamp = app_session.timestamp 
            # save_folder = Path(f"{data_processed}/notebooks/extracted/{t_stamp}_{f_name}")        

        explained_variance_by_pca(
                f_path=f"{input_data}/{pca_file}",
                config=pca_config
            )
    
    # st.markdown("**Under Construction**")
