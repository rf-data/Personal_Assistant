## run_wiki_extraction.py
# import
#
# import sys
# from typing import List
# from pathlib import Path
from datetime import datetime

# from src.core.text_extractor import TXTCleanExtractor, MDCleanExtractor
# from src.core.pdf_extractor import PDFCleanExtractor
# from src.core.html_extractor import HTMLCleanExtractor
# from src.core.notebook_extractor import NoteBookCleanExtractor
# from src.core.text_classifier import TXTClassifier
# from src.core.feature_enricher import FeatureEnricher
# from src.core.base_assembler import BaseAssembler
# from src.tools.build_structure import build_structure_from_lines
# # from src.tools.extraction import  extraction_per_page
from src.model_tools.feature_enricher import FeatureEnricher

# from tiktoken import encoding_for_model
# from src.core.memory import session_state
from src.core.logger import create_logger

# # from gmp_compliance.src.core._dev_block_classifier import BlockClassifier
# from src.core.text_cleaner import TextCleaner
# # from src.core.tbl_col_detector import TableColumnDetector
# from src.core.document_classifier import DocumentClassifier
# from src.core.text_merger import TextMerger
# # text_clean_extractor import TextCleanExtractor
from src.tools_parsing.extract_wiki import extract_wiki_article
from src.tools_parsing.post_extract_processing_wiki import process_wiki

# from src.tools.extract_html import extract_html_file
# from src.tools.extract_pdf import extract_pdf_file
# from src.tools.post_extract_processing_pdf import process_pdf
# from src.tools.assemble_pdf import assemble_single_pdf
# from src.tools.extract_notebook import extract_notebook_json
# from src.tools.classify_txt import classify_txt_file
# from src.utils.general_helper import load_env_vars
# from src.utils.path_helper import shorten_path
from src.utils.dict_helper import get_yaml_config

# from src.utils.text_file_helper import save_text_file
# from src.utils.html_helper import scrape_source_code
# # from src.utils.extract_pdf_helper import extract_info_and_grafics

# ------------------
# MAIN FUNCTION
# ------------------


# def wiki_extraction():


#     return run_wiki_extraction(
#                             query,
#                             query_time,
#                             config,
#                             save=True
#                             )


def run_wiki_extraction(query, query_time, config, save=False):
    # load env variables and config
    # load_env_vars()

    # config_name = input("Enter 'config_file' name (no suffix): ")
    config = get_yaml_config("wiki_requests")
    session.model_config = config

    general_config = config.get("general_args", {})
    # page_ids = general_config.get("file_name", {})
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]

    parse_config = config.get("article_parsing", {})
    query = parse_config["query"]
    query_time = parse_config["query_time"]

    now = general_config.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    session.state.timestamp = now

    # setup logger
    logger = create_logger(name=log_name, file_name=name_logfile)
    session.logger = logger

    extract = extract_wiki_article(
        query, query_time, config.get("extraction", {}), save=True
    )

    hi = process_wiki(
        extract,
        prepare_config=config.get("text_preparation", {}),
        enricher=FeatureEnricher(),
    )


###############

# session.model_config = config

# data_raw = env_variables("DATA_RAW")
# #
# data_processed = env_variables("DATA_PROCESSED")

# general_config = config.get("general_args", {})
# url = general_config.get("url", {})
# log_name = general_config["name_log"]
# name_logfile = general_config["name_logfile"]
# model_name = general_config["llm_model"]
# encoder = encoding_for_model(model_name)
# session.encoder = encoder

# now = general_config.get(
#                     "timestamp",
#                     datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                     )
# session.state.timestamp = now

# # save_folder = !

# classify_config = config.get("classification", {})

# # setup logger
# logger = create_logger(name=log_name,
#                        file_name=name_logfile)
# session.logger = logger


# if len(file_names) > 0:
#     if isinstance(file_names, (str, Path)):
#         file_names = [file_names]

# elif len(url) > 0:
#     if isinstance(url, str):
#         url = [url]

# elif (len(file_names) == 0
#       and len(url) == 0):
#     logger.error("Neither file names nor url were provided.")    #  OR scraping url's source code was not successful.")
#     sys.exit()

# else:
#     logger.error("No file names provided. Proceeding with scraped 'soup'.")


# feat_enricher = FeatureEnricher()
# # session.enricher = feat_enricher

# if len(url) > 0:
#     for u in url:
#         session.state.save_folder = Path(f"{data_processed}/html_files/extracted")
#         session.state.save_name = f"{now}_{u}_extracted"

#         extractor = HTMLCleanExtractor(
#                                 extract_config = config.get("html_extraction", {}),
#                                 enricher=feat_enricher
#                                 )

#         html_extract = extract_html_file(
#                                     extractor,
#                                     u,
#                                     save=True
#                                     )

#         assemble_config = config.get("assemble_html", {})

#         if assemble_config.get("assemble_as_md", None):
#             # text = html_extract.text

#                 save_name = ""
#                 assembler = BaseAssembler()
#                 text = assembler.create_md_from_extract(html_extract.model_dump())
#                 # text = md(text)
#                 save_text_file(text,
#                             save_name,
#                             session.state.save_folder)

#     for file in file_names:

#         suffix = Path(file).suffix[1:]
#         session.state.suffix = suffix

#         f_path = f"{data_raw}/{file}"
#         f_name = Path(f_path).stem

#         logger.info("Start extraction from file:\t%s",
#                     shorten_path(f_path))

#         if suffix == "txt":
#             # EXTRACTION
#             session.state.save_folder = Path(f"{data_processed}/txt_files/extracted")
#             session.state.save_name = f"{now}_{f_name}_extracted"

#             txt_extractor = TXTCleanExtractor(
#                                     extract_config = config.get("txt_extraction", {}),
#                                     enricher=feat_enricher
#                                     )

#             txt_extract = extract_txt_file(
#                                         f_path,
#                                         txt_extractor,
#                                         save=True
#                                         )

#             txt_classifier = TXTClassifier(
#                                     classify_config=classify_config
#                                     )

#             # CLASSIFICATION
#             session.state.save_folder = Path(f"{data_processed}/txt_files/classified")
#             session.state.save_name = f"{now}_{f_name}_classified"

#             text_class = classify_txt_file(
#                                 txt_extract,
#                                 txt_classifier,
#                                 save=True
#                                 )


#         elif suffix == "md":
#             session.state.save_folder = Path(f"{data_processed}/md_files/extracted")
#             session.state.save_name = f"{now}_{f_name}_extracted"

#             md_extractor = MDCleanExtractor(
#                                     extract_config = config.get("md_extraction", {}),
#                                     enricher=feat_enricher
#                                     )

#             md_extract_ = extract_md_file(
#                             f_path,
#                             md_extractor,
#                             save=True
#                             )


#         elif suffix == "pdf":
#             session.state.save_folder = Path(f"{data_processed}/pdf_files/extract_from_text")
#             session.state.save_name = f"{now}_{f_name}"

#             # TODO: include table/column_detection
#             # TODO: improve header_footer detection

#             pdf_extractor = PDFCleanExtractor(
#                                     extract_config = config.get("pdf_extraction", {}),
#                                     enricher=feat_enricher
#                                     )

#             pdf_extract_raw = extract_pdf_file(
#                                         f_path,
#                                         pdf_extractor,
#                                         save=True
#                                         )

#             session.state.save_folder = Path(f"{data_processed}/pdf_files/processed")
#             # session.state.save_name = f"{now}_{f_name}"
#             pdf_extract_fin = process_pdf(pdf_extract_raw,
#                                         config.get("pdf_text_preparation", {}),
#                                         enricher=feat_enricher)

#             # session.state.save_name = f"{now}_{f_name}_assembled"

#             assemble_pdf_config = config.get("pdf_assembly", {})

#             if assemble_pdf_config.get("assemble_as_md") is True:

#                 session.state.save_name = f"{now}_{f_name}"
#                 session.state.save_folder = f"{data_processed}/pdf_files/assembled"

#                 # assembler = PDFPageAssembler()

#                 logger.info("Start assembling pdf_file '%s'",
#                             f_name)

#                 text = assemble_single_pdf(pdf_extract_fin,
#                                            assemble_pdf_config,
#                                            save=True)
#                 # text = md(text)
#                 # save_text_file(text,
#                 #             save_name,
#                 #             )
#             # pdf_assembled = assemble_single_pdf(extracts_processed,
#             #                                     assemble_pdf_config)


#         elif suffix == "html":
#             session.state.save_folder = Path(f"{data_processed}/html_files/extracted")
#             session.state.save_name = f"{now}_{f_name}_extracted"

#             html_extractor = HTMLCleanExtractor(
#                                     extract_config = config.get("html_extraction", {}),
#                                     enricher=feat_enricher
#                                     )

#             html_extract = extract_html_file(
#                                 extractor=html_extractor,
#                                 f_path=f_path,
#                                 save=True
#                                 )

#             assemble_config = config.get("assemble_html", {})

#             if assemble_config.get("assemble_as_md", None):
#                 # text = html_extract.text

#                 save_name = ""
#                 assembler = BaseAssembler()
#                 text = assembler.create_md_from_extract(html_extract.model_dump())
#                 # text = md(text)
#                 save_text_file(text,
#                             save_name,
#                             session.state.save_folder)

#         elif suffix == "json":

#             session.state.save_folder = Path(f"{data_processed}/notebooks/extracted")
#             session.state.save_name = f"{now}_{f_name}_extracted"

#             nb_extractor = NoteBookCleanExtractor(
#                                     extract_config = config.get("nb_extraction", {}),
#                                     enricher=feat_enricher
#                                     )

#             nb_extract = extract_notebook_json(
#                                 extractor=nb_extractor,
#                                 f_path=f_path,
#                                 save=True
#                                 )


#             assemble_config = config.get("assemble_nb", {})

#             if assemble_config.get("assemble_as_md", None):
#                 # text = html_extract.text

#                 save_name = ""
#                 assembler = BaseAssembler()
#                 text = assembler.create_md_from_extract(nb_extract.model_dump())
#                 # text = md(text)
#                 save_text_file(text,
#                             save_name,
#                             session.state.save_folder)

#         else:
#             logger.error("File has an unknown suffix ('%s'). Extraction cannnot be performed and will be skipped.",
#                           suffix)

#     return


# if __name__ == "__main__":
#     text_file_extraction()

#     # struct_config = config.get("build_structure", {})
#     file_folder = struct_config["file_folder"]
#     data_folder = f"{data_processed}/{file_folder}"
#     file_t_stamp = struct_config["file_timestamp"]

#     text_prep_config = config.get("text_preparation", {})
#     # extract_info = text_prep_config.get("extract_text_info", False)
#     # extract_grafs = text_prep_config.get("extract_grafics", False)
#     # feat_config = config.get("features", {})


#     path_txt = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/ApoGesetze.txt"
#     extractor = TXTCleanExtractor(
#                                 encoder = enc,
#                                 enricher= enricher
#     )

#     from src.core.memory import session
#     # load env variables and config
#     gh.load_env_vars()
#     data_processed = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/processed"
#     # env_variables("DATA_PROCESSED")

#     general_config = config.get("general_args", {})
#     log_name = general_config["name_log"]
#     name_logfile = general_config["name_logfile"]
#     model_name = general_config["llm_model"]
#     now = general_config.get(
#                         "timestamp",
#                         datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                         )
#     session.state.timestamp = now

#     # setup logger
#     logger = create_logger(name=log_name,
#                            file_name=name_logfile)
#     session.logger = logger

#     enc = encoding_for_model(model_name)

#     enricher = FeatureEnricher(
#                             encoder = enc,
#                             )


# ##########################

#     # extract non_text_elements from pdfs
#     for file in raw_files:
#         # non_text = {}
#         # text_info = {}
#         name_short = file.split(".")[0]

#         # path = Path(f"{data_raw}/{file}")
#         # non_text, text_info = extract_info_and_grafics(
#         #                                 path,
#         #                                 get_info=extract_info,
#         #                                 get_grafics=extract_grafs
#         #                                 )
#         # save_folder = f"{data_processed}/extract_from_text"
#         # non_text_path = Path(f"{save_folder}/{now}_{name_short}_text_info.json")
#         # info_path = Path(f"{save_folder}/{now}_{name_short}_text_info.json")

#         # dh.save_dict(non_text, non_text_path)
#         # dh.save_dict(text_info, info_path)

#     # extract text from pdfs
#     if isinstance(file_name, str):
#         file_name = [file_name]

#     cleaner = TextCleaner(
#                     text_prep_config=text_prep_config
#                     )
#     merger = TextMerger(
#                     text_prep_config=text_prep_config
#                     )

#     # classifier = BlockClassifier()

#     # text_complete = []
#     for name in file_name:
#         logger.info("Start extracting text from file:\t%s",
#                     name)

#         name_short =Path(name).stem
#         f_path = f"{data_folder}/{file_t_stamp}_{name}.json"
#         results = dh.load_dict(f_path)
#         page_height = results[0]["height_page"]
#         page_width = results[0]["width_page"]

#         # TableColumnDetector
#         doc_class = DocumentClassifier(
#                                     page_attributes={
#                                                 "height": page_height,
#                                                 "width": page_width
#                                                 },
#                                     text_prep_config=text_prep_config
#                                     )
#         feat_enricher = FeatureEnricher(
#                             encoder=encoder,
#                             page_height=page_height,
#                             page_width=page_width,
#                             text_prep_config=text_prep_config
#                             )
#         session.enricher = feat_enricher

#         segment_records = build_structure_from_lines(results, name_short)

#         flat_records = _flatten_segments(segment_records)

#         text_complete = []
#         for page_info in flat_records:
#             page = page_info["page"]
#             segments = page_info["segments"]

#             logger.info("\nStart preparating text from page %s",
#                         page)


#             page_attributes = {
#                         "median_size": page_info["median_font_size"],
#                         "left_indent": page_info["left_indent"]
#                         }

#             segments = sorted(
#                         segments,
#                         key=lambda s: (
#                             s["y0_min"],
#                             s["x0_min"]
#                             )
#                         )

#             class_dict = doc_class.classify_line(segments, page_attributes)
#             # logger.info("Length 'text_segments' (after detect):\t%s", len(text_segments))

#             blocks_text = merger.merge_text_lines(class_dict["text"])

#             blocks_text = cleaner.handle_body_text_hyphens(blocks_text)


#     #         logger.info("Length 'text_segments' (after hyphen):\t%s", len(text_segments))

#     #         blocks = merger.merge_segments_to_blocks(text_segments)
#     #         logger.info("Length 'blocks'(after merge):\t%s", len(blocks))

#     #         blocks = classifier.classify_simple(blocks)
#     #         logger.info("Length 'blocks' (after classify):\t%s", len(blocks))

#     #         if len(tbl_col_segments) > 0:
#     #             left_segs, right_segs = cleaner.handle_column_hyphens(tbl_col_segments)
#     #             left_blocks = merger.merge_table_columns(left_segs)
#     #             right_blocks = merger.merge_table_columns(right_segs)
#     #         else:
#     #             left_blocks = []
#     #             right_blocks = []

#             # final_blocks = blocks + left_blocks + right_blocks
#             # final_blocks = sorted(
#             #     final_blocks,
#             #     key=lambda b: (
#             #         b.get("column", 0),
#             #         b["y0_min"]
#             #     )
#             # )

#     #         logger.info("n_segments (text): %d", len(text_segments))
#     #         logger.info("n_segments (table / column): %d", len(tbl_col_segments))

#     #         page_info["blocks"] = final_blocks


#     #         # blocks = classifier.classify_simple(blocks)

#     #         # page_info["blocks"] = tab_detect.detect(blocks)

#         # block_records = {
#         #             "blocks": records_class
#         #             }
# return {
# "header_footer": head_foot,
# "text": text,
# "heading": heading,
# "other": other
#             # }
#             page_info["text_bodies"] = blocks_text
#             page_info["header_footer"] = class_dict["header_footer"]
#             page_info["headings"] = class_dict["heading"]
#             page_info["foot_notes"] = class_dict["foot_note"]
#             page_info["non_text_segments"] = class_dict["other"]

#             save_path = Path(
#                         f"{data_processed}/classified/"
#                         f"{now}_{name_short}_p{page}_class.json"
#                         )
#             dh.save_dict(page_info, save_path)

#             full_text = [block["text"] for block in blocks_text]
#             full_text = "\n\n".join(full_text)

#             # assembler.collect(full_text, page_info, page)

#             all_text = f"""
# {"=" * 25}
# PAGE '{page}'
# {"=" * 25}

# {full_text}

# """
#             text_complete.append(all_text)

#         text_final = "\n".join(text_complete)
#         dh.save_md_file(text_final, f"{now}_{name_short}_text",
#                         f"{data_processed}/classified")

#     return


# # segment_info = {
# #                 "page": n_page,
# #                 "height_page": page_info["height_page"],
# #                 "width_page": page_info["width_page"],
# #                 "segments": segments,
# #                 "segment_text": segment_text
# #                 }

#     # def _merge_hyphenated_words(self, words: List[tuple]) -> List[tuple]:
#     #     merged = []
#     #     skip_next = False

#     #     for i in range(len(words)):
#     #         if skip_next:
#     #             skip_next = False
#     #             continue

#     #         x0, y0, x1, y1, text, *rest = words[i]

#     #         if text.endswith("-") and i + 1 < len(words):
#     #             next_word = words[i + 1][4]

#     #             if next_word in self.stop_words:
#     #                 merged_text = text + " " + next_word.lstrip()
#     #             else:
#     #                 merged_text = text[:-1] + next_word

#     #             merged.append((x0, y0, x1, y1, merged_text, *rest))
#     #             skip_next = True
#     #         else:
#     #             merged.append(words[i])

#     #     return merged


# #         # text_spacy =

# #         # settings.update(info)
# #         # result = {
# #         #     "document_name": name_short,
# #         #     "pages": extract_result
# #         #     }

# #         # page_docs.append(extract_result["pages"])         # = List[dict]
# #         # chunk_docs.append(extract_result["chunks"])
# #         # # text[name_short] = str(cleaned_text)

# #         # df_

# #         # df_pages = pd.DataFrame(extract_result["pages"])
# #         # df_chunks = pd.DataFrame(extract_result["chunks"])

# #         # logger.info("Head 'pages_df':\n%s", df_pages.head())
# #         # logger.info("Head 'chunks_df':\n%s", df_chunks.head())

# #         # logger.info("dtypes in 'pages_df'")
# #         # for col in df_pages.columns:
# #         #     logger.info("Col '%s':\t%s",
# #         #                 col,
# #         #                 df_pages[col].map(type).unique())

# #         # logger.info("dtypes in 'df_chunks'")
# #         # for col in df_chunks.columns:
# #         #     logger.info("Col '%s':\t%s",
# #         #                 col,
# #         #                 df_chunks[col].map(type).unique())

# #         # timestamp = session.state.now
# #         # f_name = Path(f_path).stem   # name.split(".")[0]
# #         # data_processed = env_variables("DATA_PROCESSED")

# #         # chunk_folder = f"{data_processed}/chunk_df"
# #         # chunk_file = f"{timestamp}_{f_name}_chunk_df"
# #         # dfh.save_df_to_parquet(
# #         #                     df=df_chunks,
# #         #                     f_name=chunk_file,
# #         #                     folder=chunk_folder,
# #         #                     # chunked=True
# #         #                     )

# #         # page_folder = f"{data_processed}/page_df"
# #         # page_file = f"{timestamp}_{f_name}_page_df"
# #         # dfh.save_df_to_parquet(
# #         #                     df=df_pages,
# #         #                     f_name=page_file,
# #         #                     folder=page_folder,
# #         #                     # chunked=True
# #         #                     )

# #         # words = extract_result.get("words", {})
# #         # if len(words) > 0:
# #         #     df_words = pd.DataFrame(words)
# #         #     logger.info("Head 'df_words':\n%s", df_words.head())
# #         #     logger.info("dtypes in 'df_words'")

# #         #     for col in df_words.columns:
# #         #         logger.info("Col '%s':\t%s",
# #         #                     col,
# #         #                     df_words[col].map(type).unique())

# #         #     word_folder = f"{data_processed}/word_df"
# #         #     word_file = f"{timestamp}_{f_name}_word_df"
# #         #     dfh.save_df_to_parquet(
# #         #                         df=df_words,
# #         #                         f_name=word_file,
# #         #                         folder=word_folder,
# #         #                         # chunked=True
# #         #                         )


#     # result_path = f"{data_processed}/{now}_texts_raw.json"
#     # dh.save_dict(docs, result_path)
