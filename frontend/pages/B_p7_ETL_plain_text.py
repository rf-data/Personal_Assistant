# ## B_p1_ETL_html.py
# # imports
# from pathlib import Path

# import fitz  # pymupdf

# # import shutil
# import pyinputplus as pyip
import streamlit as st

# from tiktoken import encoding_for_model

# from src.utils.path_helper import ensure_dir
# from src.core.memory import app_session
# # from src.run_text_extraction import run_text_file_extraction

# types_allowed = [".pdf", ".txt", ".md", ".json"]
# # , ".doc", ".docx", ".xls", ".xlsx"]
# # types_allowed = [".jpg", ".jpeg", ".png"]


def show():
    st.header("🏠 Startseite ")
    st.subheader("**ETL plain text files**")

    st.divider()

    st.markdown("**Under Construction**")


# def show():
#     st.header("🏠 Startseite ")
#     st.subheader("**'Prozess- und Workflowautomatisierung'**")

#     st.divider()

#     st.subheader("🖼️ Wähle eine Datenquelle")

#     action = st.menu_button(
#         "Datenquelle", options=["Ordner",
#                                 "Upload",
#                                 "URL", "Page_ID"]
#     )

#     st.divider()
#     st.subheader("🖼️ Choose a file")
#     st.write("")

#     # llm_model:
#     # name_log: extract_text
#     # name_logfile: extract_text

#     # timestamp: 2026-05-22_11-01-57

#     model_name = st.selectbox(
#         "🎯 Select a LLM model for encoding",
#         options=["gpt-4o-mini"],
#         index=None,
#         placeholder="Wähle eine Datei...",
#     )

#     if model_name:
#         encoder = encoding_for_model(model_name)
#         app_session.encoder = encoder

#     # OPTION 1 --- File browser section ---
#     if action == "Ordner":
#         # all_files zur Auswahl stellen
#         all_files = sorted(
#             [f for f in FILE_FOLDER.iterdir() if f.suffix.lower() in types_allowed]
#         )

#         st.markdown("#### 📂 Available files")

#         # TO-DO: MultiSelectionBox
#         selected_files = st.selectbox(
#             "🎯 Wähle eine Datei",
#             options=[f.name for f in all_files],
#             index=None,
#             placeholder="Wähle eine Datei...",
#         )

#         text_type = pyip.inputChoice(
#             choices=[
#                 "various",
#                 # 'url',
#                 "pdf",
#                 # 'wiki',
#                 "md",
#                 "html",
#                 "txt",
#                 "json_nb",
#             ],
#             prompt="Which kind of text: ",
#         )

#         app_session.text_type = text_type

#         # session_state.
#         run_config = {"pdf": {}, "html": {}}

#         if text_type:  # selected_file:
#             if text_type in ["html", "various"]:
#                 run_config["html"]["assemble_as_md"] = st.selectbox(
#                     "🎯 Should the extracted html-text assembled as md-file",
#                     options=[True, False],
#                     index=None,
#                     placeholder="Wähle eine Datei...",
#                 )
#                 run_config["html"]["scrape_images"] = st.selectbox(
#                     "🎯 Should the images from html text be scraped if applicable",
#                     options=[True, False],
#                     index=None,
#                     placeholder="Wähle eine Datei...",
#                 )
#                 run_config["html"]["save"] = st.selectbox(
#                     "🎯 At which stages files should be saved?",
#                     options=["info", "html", "md"],
#                     index=None,
#                     placeholder="Wähle eine Datei...",
#                 )

#             if text_type in ["pdf", "various"]:
#                 run_config["html"]["extract_source"] = st.selectbox(
#                     "🎯 Which sources should be used?",
#                     options=["raw_dict", "words"],
#                     index=None,
#                     placeholder="Wähle eine Datei...",
#                 )
#                 run_config["html"]["extraction_model"] = st.selectbox(
#                     "🎯 Which extraction function should be used?",
#                     options=["pymudpdf"],
#                     index=None,
#                     placeholder="Wähle eine Datei...",
#                 )

#             app_session.run_config = run_config
#             # src_path = FILE_FOLDER / selected_file
#             # dst_path = INPUT_FOLDER / selected_file

#             # shutil.copy(src_path, dst_path)

#             st.success(f"✅ Datei/-en gewählt: {selected_files}")

#             # st.session_state["selected_file"] = str(selected_file)

#             # hi = run_text_file_extraction(file_names=selected_files)
