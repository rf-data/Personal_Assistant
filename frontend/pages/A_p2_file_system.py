##
# imports
import os
from pathlib import Path

import fitz  # pymupdf
import streamlit as st

from src.tools_parsing.extract_word import extract_word 
from src.utils.streamlit_helper import show_tree, st_file_preview
from src.utils.path_helper import ensure_dir, shorten_path  
from src.utils.general_helper import load_env_vars
from src.utils.zipfile_helper import unpack_entire_zipfolder

load_env_vars()

data = os.getenv("DATA_DIR")
assert data is not None

data = Path(ensure_dir(data))

# FOLDER_DICT = {
#             "Input Folder": data / "input",
#             "Raw Data": data / "raw", 
#             "Processed Data": data / "processed/pdf_files", 
#             # "HTML_processed": data / "processed/html_files",
#             # "Notebooks_processed": data / "processed/notebooks"
#             }

# types_allowed = [".pdf", ".txt", ".md", ".json", ".html"]


def show():

    st.header("**Browse 'DATA' Folder' and 'File Upload'**")

    # st.divider()

    (
        preview,
        browse, 
        upload,
        unzip_files,
        list_files
     ) = st.tabs([
            "File Preview", 
            "Browse 'DATA' folder",
            "Upload new data",
            "Unzip files",
            "List Files"]) # , border=True)

    with preview:

        left, right = st.columns(2)

        preview_suffix = left.pills(
            label="Select file type(s)", 
            options=["txt_md", "txt", "html", "pdf", "json"], 
            default=["txt_md"], 
            selection_mode="single",
            # key="file_preview"
            )
        
        rag_ready = right.toggle(
                    label="Filter out RAG-ready extracts",
                    # key="pdf_image"
                )
        folder_options = [
            f"{data}/{preview_suffix}/input",
            f"{data}/{preview_suffix}/raw",
            f"{data}/_QMS_apo",
            f"{data}/{preview_suffix}/processed",
            f"{data}/{preview_suffix}/embedded"
            ]


        preview_folder = st.selectbox(
                                label="Folder", 
                                options=folder_options, 
                                format_func=lambda p: shorten_path(p, n=2)
                                # selection_mode="single"
                                )
        st.markdown(f"Your selected files of type '{preview_suffix}' in folder '{shorten_path(preview_folder, 1)}'.")
        st.divider()

        file_options = [f for f in Path(preview_folder).rglob("*")
                        if f.is_file() and Path(f).stem.startswith(f"{'ready_' if rag_ready else 'test_'}")]
        # [f for f in Path(preview_folder[0]).rglob(preview_suffix)]
                            #  if f.suffix in preview_suffix]
        
        preview_file = st.selectbox(       # selectbox, multiselect(
                    label="Which file should be rendered?",
                    options=file_options, 
                    format_func=lambda p: shorten_path(p, n=2) 
                    # key="pdf_files"
                    )
        
        if preview_file and preview_folder:
            with st.expander(f"Preview on '{Path(preview_file).stem}'"):
                st_file_preview(preview_file)

        else:
            st.warning("No 'preview_folder' and 'preview_file' selected or no file available")

    with browse:
        st.subheader("**Browse DATA Folder**")
        st.divider()
        st.markdown("**Under Construction**")
        # options = [
        #         "Input Folder", 
        #         "Raw Data", 
        #         "Processed Data", 
        #         # "HTML_processed",
        #         # "Notebooks_processed"
        #         ]
        
        # folder = st.pills("Folder", 
        #                 options, 
        #                 selection_mode="single")
        # st.markdown(f"Your selected options: {folder}.")

        # # root = Path("data")
        # if folder is None:
        #     folder_path = data

        # else:    
        #     folder_path = FOLDER_DICT.get(folder, "")
        
        # assert folder_path is not None
        # show_tree(folder_path)

    # st.divider()

    with upload:
        st.subheader("**Upload new data files**")

        st.divider()
        st.markdown("**Under Construction**")

        # uploaded_file = st.file_uploader(
        #     "📤 Upload a file",
        #     accept_multiple_files=False,
        #     max_upload_size=10,
        #     type=types_allowed,
        # )

        # if uploaded_file is not None:
        #     if not isinstance(uploaded_file, list):
        #         uploaded_file = [uploaded_file]

        #     st.write("You selected '%s' files.", 
        #              len(uploaded_file))

        #     for file in uploaded_file:
        #         st.markdown("**File check**")

        #         st.write("File name:", file.name)
        #         st.write("File type:", file.type)
        #         st.write("File size:", file.size, "bytes")

        #         # Vorschau für Textdateien
        #         if file.type == "text/plain":
        #             content = file.getvalue().decode("utf-8")

        #             st.text_area("text file preview", content[:3000], height=300)

        #             # Vorschau pdf-Dateien
        #         if file.type == "pdf":
        #             pdf_bytes = file.read()

        #             doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        #             first_page = doc[0]
        #             text = first_page.get_text()

        #             st.text_area("pdf file preview", text[:3000], height=300)

        #         confirm = st.checkbox("Upload file")

        #         if confirm:
        #             save_path = FOLDER_DICT["Raw Data"] / file.name
        #             suffix = Path(file.name).suffix

        #             if suffix == ".pdf":
        #                 uploaded_file.seek(0)

        #             with open(save_path, "wb") as f:
        #                 f.write(file.getbuffer())

        #             st.success(f"✅ File '{file.name}' successfully saved.")

        #             # st.session_state["selected_file"] = str(uploaded_file)

    with  unzip_files:
        st.subheader("**Unzip files**")

        st.divider()
        # st.divider()
        st.markdown("**Under Construction**")

        # input_data = FOLDER_DICT["Input Folder"]
        # zip_files = st.multiselect(
        #         label="Which zip file(s) should be unpacked?",
        #         options=[shorten_path(f, n=1) for f in Path(input_data).iterdir()
        #                 if f.suffix == ".zip"],
        #         key="files_zip"
        #             )
        
        # assert zip_files is not None

        # if "unzip_files" not in st.session_state:
        #     st.session_state["unzip_files"] = "ready"
    
        # st.markdown(f"Status 'unzip_files': {st.session_state['unzip_files']}")

        # left, right = st.columns(2)
        # if (left.button("Reset", type="primary")
        #     and st.session_state["unzip_files"] is not None):
        #     st.session_state["unzip_files"] = "ready"

        # if (right.button("Start unzipping") 
        #     and st.session_state["unzip_files"] in ["ready", None]):
        #         # st.session_state["parsed"] = None
        #     for f_path in zip_files:
                
        #         unpack_entire_zipfolder(
        #                     src_path=f"{input_data}/{f_path}",
        #                     dst_folder=str(input_data)
        #         )

        
    with list_files:
        st.subheader("**List Folder Files**")

        st.divider()
        st.markdown("**Under Construction**")