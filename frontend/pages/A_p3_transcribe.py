## A_p3_trasncribe.py
# imports
from pathlib import Path
import streamlit as st

from src.core.config import parsing_env_vars
from src.utils.path_helper import shorten_path  #, ensure_dir
from src.utils.dict_helper import load_dict


def show():
    st.header("🏠 Startseite ")
    st.subheader("**Transcription**")

    st.divider()

    with st.expander("Create transcript files"):
        st.markdown("**Under Construction**")

    with st.expander("View transcript files"):
        st.markdown("**Under Construction**")

        folder = Path(parsing_env_vars.data_transcripts) / "Vorkurs_Mathe_JLoviscach"
        files = [f for f in folder.iterdir()
                 if f.suffix == ".json"]

        st.write(f"Found {len(files)} files.")

        st.divider()

        transcripts = st.multiselect(
                        label="Select files to be shown (max: 5)",
                        options=files,
                        format_func=lambda p: shorten_path(p, n=1),
                        max_selections=5
                        )

        for trans in transcripts:
            st.write(f"File name: '{trans.name}'")

            trans_file = load_dict(trans)
            st.json(trans_file)
            st.divider()
            
        # list(folder.iterdir())