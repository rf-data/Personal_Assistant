##
# imports 
import streamlit as st
from pathlib import Path
import os
import shutil

import fitz # pymupdf

import src.utils.general_helper as gh
import src.utils.path_helper as ph

gh.load_dotenv(".env.streamlit")

FILE_FOLDER = Path(os.getenv("FOLDER_FILES"))   
INPUT_FOLDER = Path(os.getenv("FOLDER_INPUT"))

ph.ensure_dir(Path(FILE_FOLDER))
ph.ensure_dir(Path(INPUT_FOLDER))

types_allowed = [".pdf", ".txt", ".md"]
                # , ".doc", ".docx", ".xls", ".xlsx"]
    # types_allowed = [".jpg", ".jpeg", ".png"]


def show():
    st.header("🏠 Startseite ")
    st.subheader("**'Prozess- und Workflowautomatisierung'**")

    st.divider()


    st.subheader("🖼️ Wähle eine Datenquelle")
      
    action = st.menu_button("Datenquelle", 
                            options=["Ordner", "Upload", "Web_Scraping"])
    
    st.divider()
    st.subheader("🖼️ Wähle eine Datei")
    st.write("")

    # OPTION 1 --- File browser section ---
    if action == "Ordner":
            
        all_files = sorted([f for f 
                            in FILE_FOLDER.iterdir() 
                            if f.suffix.lower() in types_allowed])

        st.markdown("#### 📂 Vorhandene Dateien")

        selected_file = st.selectbox(
                "🎯 Wähle eine Datei",
                options=[f.name for f in all_files],
                index=None,
                placeholder="Wähle eine Datei..."
            )

        if selected_file:
            src_path = FILE_FOLDER / selected_file
            dst_path = INPUT_FOLDER / selected_file

            shutil.copy(src_path, dst_path)

            st.success(f"✅ Datei gewählt: {selected_file}")
            
            st.session_state["selected_file"] = str(selected_file)


    # OPTION 2 --- Upload section ---
    elif action == "Upload":
        uploaded_file = st.file_uploader("📤 Lade eine Datei hoch",
                                         accept_multiple_files=False,
                                         max_upload_size=10,
                                        type=types_allowed)

        if uploaded_file is not None:

            st.markdown("**Datei prüfen**")

            st.write("Dateiname:", uploaded_file.name)
            st.write("Dateityp:", uploaded_file.type)
            st.write("Dateigröße:", uploaded_file.size, "Bytes")

            # Vorschau für Textdateien
            if uploaded_file.type == "text/plain":

                content = uploaded_file.getvalue().decode("utf-8")

                st.text_area(
                    "Text-Vorschau",
                    content[:3000],
                    height=300
                )

            # Vorschau pdf-Dateien
            if uploaded_file.type == "pdf":
                pdf_bytes = uploaded_file.read()

                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                first_page = doc[0]
                text = first_page.get_text()

                st.text_area("PDF-Vorschau", text[:3000], height=300)


            confirm = st.checkbox("Datei ist korrekt")

            if confirm:

                save_path = INPUT_FOLDER / uploaded_file.name
                suffix = Path(uploaded_file.name).suffix

                if suffix == ".pdf":
                    uploaded_file.seek(0)

                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success(f"✅ Datei '{uploaded_file.name}' erfolgreich gespeichert!")

                st.session_state["selected_file"] = str(uploaded_file)

    # OPTION 3 --- web scraping ---
    elif action == "Web_Scraping":
        st.write("Folgt demnächst")
    
    st.divider()
