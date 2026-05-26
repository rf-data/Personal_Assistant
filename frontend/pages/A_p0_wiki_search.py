##
# imports
import os
from pathlib import Path

import fitz  # pymupdf

# import shutil
import pyinputplus as pyip
import streamlit as st
from tiktoken import encoding_for_model

import src.utils.path_helper as ph
from src.core.memory import session_state
from src.run_text_extraction import run_text_file_extraction
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
    st.header("🏠 Startseite ")
    st.subheader("**'Prozess- und Workflowautomatisierung'**")

    st.divider()

    st.subheader("🖼️ Wähle eine Datenquelle")

    action = st.menu_button(
        "Datenquelle", options=["Ordner", "Upload", "URL", "Page_ID"]
    )

    st.divider()
    st.subheader("🖼️ Choose a file")
    st.write("")

    # llm_model:
    # name_log: extract_text
    # name_logfile: extract_text

    # timestamp: 2026-05-22_11-01-57

    model_name = st.selectbox(
        "🎯 Select a LLM model for encoding",
        options=["gpt-4o-mini"],
        index=None,
        placeholder="Wähle eine Datei...",
    )

    if model_name:
        encoder = encoding_for_model(model_name)
        session_state.encoder = encoder

    # OPTION 1 --- File browser section ---
    if action == "Ordner":
        # all_files zur Auswahl stellen
        all_files = sorted(
            [f for f in FILE_FOLDER.iterdir() if f.suffix.lower() in types_allowed]
        )

        st.markdown("#### 📂 Available files")

        # TO-DO: MultiSelectionBox
        selected_files = st.selectbox(
            "🎯 Wähle eine Datei",
            options=[f.name for f in all_files],
            index=None,
            placeholder="Wähle eine Datei...",
        )

        text_type = pyip.inputChoice(
            choices=[
                "various",
                # 'url',
                "pdf",
                # 'wiki',
                "md",
                "html",
                "txt",
                "json_nb",
            ],
            prompt="Which kind of text: ",
        )

        session_state.text_type = text_type

        # session_state.
        run_config = {"pdf": {}, "html": {}}

        if text_type:  # selected_file:
            if text_type in ["html", "various"]:
                run_config["html"]["assemble_as_md"] = st.selectbox(
                    "🎯 Should the extracted html-text assembled as md-file",
                    options=[True, False],
                    index=None,
                    placeholder="Wähle eine Datei...",
                )
                run_config["html"]["scrape_images"] = st.selectbox(
                    "🎯 Should the images from html text be scraped if applicable",
                    options=[True, False],
                    index=None,
                    placeholder="Wähle eine Datei...",
                )
                run_config["html"]["save"] = st.selectbox(
                    "🎯 At which stages files should be saved?",
                    options=["info", "html", "md"],
                    index=None,
                    placeholder="Wähle eine Datei...",
                )

            if text_type in ["pdf", "various"]:
                run_config["html"]["extract_source"] = st.selectbox(
                    "🎯 Which sources should be used?",
                    options=["raw_dict", "words"],
                    index=None,
                    placeholder="Wähle eine Datei...",
                )
                run_config["html"]["extraction_model"] = st.selectbox(
                    "🎯 Which extraction function should be used?",
                    options=["pymudpdf"],
                    index=None,
                    placeholder="Wähle eine Datei...",
                )

            session_state.run_config = run_config
            # src_path = FILE_FOLDER / selected_file
            # dst_path = INPUT_FOLDER / selected_file

            # shutil.copy(src_path, dst_path)

            st.success(f"✅ Datei/-en gewählt: {selected_files}")

            # st.session_state["selected_file"] = str(selected_file)

            hi = run_text_file_extraction(file_names=selected_files)

    # OPTION 2 --- Upload section ---
    elif action == "Upload":
        uploaded_file = st.file_uploader(
            "📤 Lade eine Datei hoch",
            accept_multiple_files=False,
            max_upload_size=10,
            type=types_allowed,
        )

        if uploaded_file is not None:
            st.markdown("**Datei prüfen**")

            st.write("Dateiname:", uploaded_file.name)
            st.write("Dateityp:", uploaded_file.type)
            st.write("Dateigröße:", uploaded_file.size, "Bytes")

            # Vorschau für Textdateien
            if uploaded_file.type == "text/plain":
                content = uploaded_file.getvalue().decode("utf-8")

                st.text_area("Text-Vorschau", content[:3000], height=300)

            # Vorschau pdf-Dateien
            if uploaded_file.type == "pdf":
                pdf_bytes = uploaded_file.read()

                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                first_page = doc[0]
                text = first_page.get_text()

                st.text_area("PDF-Vorschau", text[:3000], height=300)

            confirm = st.checkbox("Datei ist korrekt")

            if confirm:
                save_path = FILE_FOLDER / uploaded_file.name
                suffix = Path(uploaded_file.name).suffix

                if suffix == ".pdf":
                    uploaded_file.seek(0)

                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success(f"✅ Datei '{uploaded_file.name}' erfolgreich gespeichert!")

                st.session_state["selected_file"] = str(uploaded_file)

    # OPTION 3 --- web scraping ---
    elif action == "URL":
        url = input("Enter the url to scrape...")

        session_state.text_type = "url"

        hi = run_text_file_extraction(url=url)
        # pyip.inputChoice(choices=[
        #                                 'various',
        #                                 # ,
        #                                 'pdf',
        #                                 # 'wiki',
        #                                 'md',
        #                                 'txt',
        #                                 'json_nb'
        #                                 ],
        #                         prompt='Which kind of text: ')

        # st.write("Folgt demnächst")

        st.divider()

    # wiki:
    #     query: Partial_least # turing
    #     query_time: 2026-05-18_13-08-12
    #     article_to_parse:
    #         - 314204
    #     language: en        # Literal["en", "de"]
    #     max_retries: 3
    #     assemble_as_md: True
    #     # scrape_images: True
    #     save:
    #         - info
    #         - html
    #         - md

    # OPTION 4 --- parse WikiPage ---
    elif action == "Page_ID":
        # run_config["html"]["extract_source"]
        wiki_config = {}

        wiki_config["article_to_parse"] = st.selectbox(
            "🎯 Which pages should be scraped?",
            options=["raw_dict", "words"],
            index=None,
            placeholder="Wähle eine Datei...",
        )
        wiki_config["language"] = st.selectbox(
            "🎯 Which extraction function should be used?",
            options=["pymudpdf"],
            index=None,
            placeholder="Wähle eine Datei...",
        )
        wiki_config["assemble_as_md"] = st.selectbox(
            "🎯 Should the extracted html-text assembled as md-file",
            options=[True, False],
            index=None,
            # placeholder="Wähle eine Datei..."
        )
        wiki_config["scrape_images"] = st.selectbox(
            "🎯 Should the images from html text be scraped if applicable",
            options=[True, False],
            index=None,
            placeholder="Wähle eine Datei...",
        )
        wiki_config["save"] = st.selectbox(
            "🎯 At which stages files should be saved?",
            options=["info", "html", "md"],
            index=None,
            placeholder="Wähle eine Datei...",
        )

        st.write("Folgt demnächst")
