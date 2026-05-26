##
# imports
import os
from pathlib import Path

import fitz  # pymupdf

# import shutil
import streamlit as st

import src.utils.path_helper as ph
from src.utils.general_helper import load_env_vars

load_env_vars(".env.frontend")

FILE_FOLDER = Path(os.getenv("FOLDER_FILES"))
# INPUT_FOLDER = Path(os.getenv("FOLDER_INPUT"))

ph.ensure_dir(Path(FILE_FOLDER))
# ph.ensure_dir(Path(INPUT_FOLDER))

types_allowed = [".pdf", ".txt", ".md", ".json"]
# , ".doc", ".docx", ".xls", ".xlsx"]
# types_allowed = [".jpg", ".jpeg", ".png"]


def show():
    # st.header("🏠 Startseite ")
    st.subheader("**'File Upload'**")

    st.divider()

    uploaded_file = st.file_uploader(
        "📤 Lade eine Datei hoch",
        accept_multiple_files=False,
        max_upload_size=10,
        type=types_allowed,
    )

    if uploaded_file is not None:
        if not isinstance(uploaded_file, list):
            uploaded_file = [uploaded_file]

        st.write("You selected '%s' files.", len(uploaded_file))

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
                save_path = FILE_FOLDER / file.name
                suffix = Path(file.name).suffix

                if suffix == ".pdf":
                    uploaded_file.seek(0)

                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())

                st.success(f"✅ File '{file.name}' successfully saved.")

                # st.session_state["selected_file"] = str(uploaded_file)
