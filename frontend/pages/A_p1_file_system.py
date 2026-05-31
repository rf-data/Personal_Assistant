##
# imports
import os
from pathlib import Path

import fitz  # pymupdf
import streamlit as st

from src.utils.streamlit_helper import show_tree
from src.utils.path_helper import ensure_dir
from src.utils.general_helper import load_env_vars

load_env_vars()

data = os.getenv("DATA_DIR")
assert data is not None

data = Path(ensure_dir(data))

FOLDER_DICT = {
            "Input Folder": data / "input",
            "Raw Data": data / "raw", 
            "Processed Data": data / "processed/pdf_files", 
            # "HTML_processed": data / "processed/html_files",
            # "Notebooks_processed": data / "processed/notebooks"
            }

types_allowed = [".pdf", ".txt", ".md", ".json", ".html"]


def show():

    st.header("**Browse 'DATA' Folder' and 'File Upload'**")

    # st.divider()

    (browse, 
     upload,
     unzip_files,
    list_files
     ) = st.tabs(["Browse 'DATA' folder",
                    "Upload new data",
                    "Unzip files",
                    "List Files"]) # , border=True)

    with browse:
        st.subheader("**Browse DATA Folder**")
        options = [
                "Input Folder", 
                "Raw Data", 
                "Processed Data", 
                # "HTML_processed",
                # "Notebooks_processed"
                ]
        
        folder = st.pills("Folder", 
                        options, 
                        selection_mode="single")
        st.markdown(f"Your selected options: {folder}.")

        # root = Path("data")
        if folder is None:
            folder_path = data

        else:    
            folder_path = FOLDER_DICT.get(folder, "")
        
        assert folder_path is not None
        show_tree(folder_path)

    # st.divider()

    with upload:
        st.subheader("**Upload new data files**")
        uploaded_file = st.file_uploader(
            "📤 Upload a file",
            accept_multiple_files=False,
            max_upload_size=10,
            type=types_allowed,
        )

        if uploaded_file is not None:
            if not isinstance(uploaded_file, list):
                uploaded_file = [uploaded_file]

            st.write("You selected '%s' files.", 
                     len(uploaded_file))

            for file in uploaded_file:
                st.markdown("**File check**")

                st.write("File name:", file.name)
                st.write("File type:", file.type)
                st.write("File size:", file.size, "bytes")

                # Vorschau für Textdateien
                if file.type == "text/plain":
                    content = file.getvalue().decode("utf-8")

                    st.text_area("text file preview", content[:3000], height=300)

                    # Vorschau pdf-Dateien
                if file.type == "pdf":
                    pdf_bytes = file.read()

                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                    first_page = doc[0]
                    text = first_page.get_text()

                    st.text_area("pdf file preview", text[:3000], height=300)

                confirm = st.checkbox("Upload file")

                if confirm:
                    save_path = FOLDER_DICT["Raw Data"] / file.name
                    suffix = Path(file.name).suffix

                    if suffix == ".pdf":
                        uploaded_file.seek(0)

                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    st.success(f"✅ File '{file.name}' successfully saved.")

                    # st.session_state["selected_file"] = str(uploaded_file)

    with  unzip_files:
        st.subheader("**Unzip files**")

        st.divider()
        st.markdown("**Under Construction**")
        
    with list_files:
        st.subheader("**List Folder Files**")

        st.divider()
        st.markdown("**Under Construction**")