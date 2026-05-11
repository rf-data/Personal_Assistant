## run_text_preparation.py
# import
# import click
import os
from pathlib import Path
from datetime import datetime
from tiktoken import encoding_for_model

from src.core.memory import session
from src.core.logger import create_logger
from src.tools.build_structure import build_structure_from_lines
# from src.tools.extraction import  extraction_per_page
from src.core.feature_enricher import FeatureEnricher
# from gmp_compliance.src.core._dev_block_classifier import BlockClassifier
from src.core.pdf_cleaner import TextCleaner
# from src.core.tbl_col_detector import TableColumnDetector
from src.core.text_classifier import DocumentClassifier
from src.core.text_merger import TextMerger
# text_clean_extractor import TextCleanExtractor

import src.utils.general_helper as gh
import src.utils.dict_helper as dh
# from src.utils.extract_pdf_helper import extract_info_and_grafics


def _flatten_segments(seg_records):
    flat = []
    for page_info in seg_records:
        lines = []
        # for line in seg_info.keys():
        segments = page_info["segments"]
        # print("[DEBUG] len segments:\t", len(segments))

        for seg in segments:
            # print("len seg:\t", len(seg))

            for line in seg:
                if isinstance(line, list) and len(line) == 1:
                    line = line[0]
                    lines.append(line)
                else:
                    print(f"line: len={len(line)} | type ={type(line)}")
                    for l in line:
                        lines.append(l)

        page_info["segments"] = lines
        flat.append(page_info)

    feat_enricher = session.enricher
    flat = feat_enricher.enrich_pages(flat)
             
    return flat

# ------------------
# MAIN FUNCTION
# ------------------

def text_preparation():  
    # load env variables and config
    gh.load_env_vars()

    config_name = input("Enter 'config_file' name (no suffix): ")
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    return run_text_preparation(config)


def run_text_preparation(config: dict):
    # load env variables and config
    gh.load_env_vars()
    
    # data_raw = os.getenv("DATA_RAW")
    data_processed = os.getenv("DATA_PROCESSED")
    
    general_config = config.get("general_args", {})
    raw_files = general_config["file_name"]
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]
    model_name = general_config["llm_model"]
    now = general_config.get(
                        "timestamp", 
                        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        )
    session.state.timestamp = now

    encoder = encoding_for_model(model_name)

    struct_config = config.get("build_structure", {})
    file_folder = struct_config["file_folder"]
    data_folder = f"{data_processed}/{file_folder}"
    file_t_stamp = struct_config["file_timestamp"]
    file_name = struct_config["file_name"]

    text_prep_config = config.get("text_preparation", {})
    # extract_info = text_prep_config.get("extract_text_info", False)
    # extract_grafs = text_prep_config.get("extract_grafics", False)
    # feat_config = config.get("features", {})
    
    # setup logger
    logger = create_logger(name=log_name, file_name=name_logfile)
    session.logger = logger

    
    # extract non_text_elements from pdfs
    for file in raw_files:
        # non_text = {}
        # text_info = {}
        name_short = file.split(".")[0]

        # path = Path(f"{data_raw}/{file}")
        # non_text, text_info = extract_info_and_grafics(
        #                                 path, 
        #                                 get_info=extract_info,
        #                                 get_grafics=extract_grafs
        #                                 )
        # save_folder = f"{data_processed}/extract_from_text"
        # non_text_path = Path(f"{save_folder}/{now}_{name_short}_text_info.json")
        # info_path = Path(f"{save_folder}/{now}_{name_short}_text_info.json")

        # dh.save_dict(non_text, non_text_path)
        # dh.save_dict(text_info, info_path)

    # extract text from pdfs
    if isinstance(file_name, str):
        file_name = [file_name]
    
    cleaner = TextCleaner(
                    text_prep_config=text_prep_config
                    )
    merger = TextMerger(
                    text_prep_config=text_prep_config
                    )
    
    # classifier = BlockClassifier()

    # text_complete = []
    for name in file_name:
        logger.info("Start extracting text from file:\t%s",
                    name)
        
        name_short =Path(name).stem 
        f_path = f"{data_folder}/{file_t_stamp}_{name}.json"
        results = dh.load_dict(f_path)
        page_height = results[0]["height_page"]
        page_width = results[0]["width_page"] 

        # TableColumnDetector
        doc_class = DocumentClassifier(
                                    page_attributes={
                                                "height": page_height,
                                                "width": page_width
                                                },
                                    text_prep_config=text_prep_config
                                    )
        feat_enricher = FeatureEnricher(
                            encoder=encoder,
                            page_height=page_height,
                            page_width=page_width,
                            text_prep_config=text_prep_config
                            )
        session.enricher = feat_enricher
        
        segment_records = build_structure_from_lines(results, name_short)
        
        flat_records = _flatten_segments(segment_records)

        text_complete = []
        for page_info in flat_records:
            page = page_info["page"]
            segments = page_info["segments"]

            logger.info("\nStart preparating text from page %s", 
                        page)
            

            page_attributes = {
                        "median_size": page_info["median_font_size"],
                        "left_indent": page_info["left_indent"]
                        }

            segments = sorted(
                        segments,
                        key=lambda s: (
                            s["y0_min"],
                            s["x0_min"]
                            )
                        )

            class_dict = doc_class.classify_line(segments, page_attributes)
            # logger.info("Length 'text_segments' (after detect):\t%s", len(text_segments))
            
            blocks_text = merger.merge_text_lines(class_dict["text"])

            blocks_text = cleaner.handle_body_text_hyphens(blocks_text)

            
    #         logger.info("Length 'text_segments' (after hyphen):\t%s", len(text_segments))

    #         blocks = merger.merge_segments_to_blocks(text_segments)
    #         logger.info("Length 'blocks'(after merge):\t%s", len(blocks))

    #         blocks = classifier.classify_simple(blocks)
    #         logger.info("Length 'blocks' (after classify):\t%s", len(blocks))
            
    #         if len(tbl_col_segments) > 0:
    #             left_segs, right_segs = cleaner.handle_column_hyphens(tbl_col_segments)
    #             left_blocks = merger.merge_table_columns(left_segs)
    #             right_blocks = merger.merge_table_columns(right_segs)
    #         else:
    #             left_blocks = []
    #             right_blocks = []

            # final_blocks = blocks + left_blocks + right_blocks
            # final_blocks = sorted(
            #     final_blocks,
            #     key=lambda b: (
            #         b.get("column", 0),
            #         b["y0_min"]
            #     )
            # )

    #         logger.info("n_segments (text): %d", len(text_segments))
    #         logger.info("n_segments (table / column): %d", len(tbl_col_segments))
            
    #         page_info["blocks"] = final_blocks
            
            
    #         # blocks = classifier.classify_simple(blocks)

    #         # page_info["blocks"] = tab_detect.detect(blocks)

    #         # block_records = {
    #         #             "blocks": records_class
    #         #             }
    # return {
            # "header_footer": head_foot, 
            # "text": text, 
            # "heading": heading, 
            # "other": other
            # }
            page_info["text_bodies"] = blocks_text
            page_info["header_footer"] = class_dict["header_footer"]
            page_info["headings"] = class_dict["heading"]
            page_info["foot_notes"] = class_dict["foot_note"]
            page_info["non_text_segments"] = class_dict["other"]

            save_path = Path(
                        f"{data_processed}/classified/"
                        f"{now}_{name_short}_p{page}_class.json"
                        )
            dh.save_dict(page_info, save_path)

            full_text = [block["text"] for block in blocks_text]
            full_text = "\n\n".join(full_text)
            
            # assembler.collect(full_text, page_info, page)

            all_text = f"""
{"=" * 25}
PAGE '{page}'
{"=" * 25}

{full_text}

"""
            text_complete.append(all_text)

        text_final = "\n".join(text_complete)
        dh.save_md_file(text_final, f"{now}_{name_short}_text", 
                        f"{data_processed}/classified")

    return 

# segment_info = {
#                 "page": n_page,
#                 "height_page": page_info["height_page"],
#                 "width_page": page_info["width_page"],
#                 "segments": segments,
#                 "segment_text": segment_text 
#                 }

    # def _merge_hyphenated_words(self, words: List[tuple]) -> List[tuple]:
    #     merged = []
    #     skip_next = False
        
    #     for i in range(len(words)):
    #         if skip_next:
    #             skip_next = False
    #             continue
            
    #         x0, y0, x1, y1, text, *rest = words[i]
            
    #         if text.endswith("-") and i + 1 < len(words):
    #             next_word = words[i + 1][4]
                
    #             if next_word in self.stop_words:
    #                 merged_text = text + " " + next_word.lstrip()
    #             else:
    #                 merged_text = text[:-1] + next_word
                
    #             merged.append((x0, y0, x1, y1, merged_text, *rest))
    #             skip_next = True
    #         else:
    #             merged.append(words[i])
        
    #     return merged


if __name__ == "__main__":
    text_preparation()
    
#         # text_spacy = 

#         # settings.update(info)
#         # result = {
#         #     "document_name": name_short,    
#         #     "pages": extract_result    
#         #     }

#         # page_docs.append(extract_result["pages"])         # = List[dict]
#         # chunk_docs.append(extract_result["chunks"])
#         # # text[name_short] = str(cleaned_text)

#         # df_

#         # df_pages = pd.DataFrame(extract_result["pages"])
#         # df_chunks = pd.DataFrame(extract_result["chunks"])

#         # logger.info("Head 'pages_df':\n%s", df_pages.head())
#         # logger.info("Head 'chunks_df':\n%s", df_chunks.head())

#         # logger.info("dtypes in 'pages_df'")
#         # for col in df_pages.columns:
#         #     logger.info("Col '%s':\t%s",
#         #                 col, 
#         #                 df_pages[col].map(type).unique())

#         # logger.info("dtypes in 'df_chunks'")
#         # for col in df_chunks.columns:
#         #     logger.info("Col '%s':\t%s",
#         #                 col, 
#         #                 df_chunks[col].map(type).unique())
            
#         # timestamp = session.state.now
#         # f_name = Path(f_path).stem   # name.split(".")[0]
#         # data_processed = os.getenv("DATA_PROCESSED")
        
#         # chunk_folder = f"{data_processed}/chunk_df"
#         # chunk_file = f"{timestamp}_{f_name}_chunk_df"
#         # dfh.save_df_to_parquet(
#         #                     df=df_chunks, 
#         #                     f_name=chunk_file,
#         #                     folder=chunk_folder, 
#         #                     # chunked=True
#         #                     )

#         # page_folder = f"{data_processed}/page_df"
#         # page_file = f"{timestamp}_{f_name}_page_df"
#         # dfh.save_df_to_parquet(
#         #                     df=df_pages, 
#         #                     f_name=page_file,
#         #                     folder=page_folder, 
#         #                     # chunked=True
#         #                     )
        
#         # words = extract_result.get("words", {})
#         # if len(words) > 0:
#         #     df_words = pd.DataFrame(words)
#         #     logger.info("Head 'df_words':\n%s", df_words.head())
#         #     logger.info("dtypes in 'df_words'")
        
#         #     for col in df_words.columns:
#         #         logger.info("Col '%s':\t%s",
#         #                     col, 
#         #                     df_words[col].map(type).unique())
                
#         #     word_folder = f"{data_processed}/word_df"
#         #     word_file = f"{timestamp}_{f_name}_word_df"
#         #     dfh.save_df_to_parquet(
#         #                         df=df_words, 
#         #                         f_name=word_file,
#         #                         folder=word_folder, 
#         #                         # chunked=True
#         #                         )




#     # result_path = f"{data_processed}/{now}_texts_raw.json"
#     # dh.save_dict(docs, result_path)
        

