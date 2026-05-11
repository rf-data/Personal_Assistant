## build_structure.py
# import
import os
from pathlib import Path
from datetime import datetime
from tiktoken import encoding_for_model

from src.core.memory import session
from src.core.text_structure_builder import TextStructureBuilder
import src.utils.general_helper as gh
import src.utils.dict_helper as dh



def build_structure_from_lines(results: dict, f_name: str):

    data_processed = os.getenv("DATA_PROCESSED")

    config = session.model_config
    # general_config = config.get("general_args", {})
    # files_name = general_config["result_name"]
    # model_name = general_config["llm_model"]

    struct_config = config.get("build_structure", {})

    # word_records = results["words"]    
    # page_height = results[0]["height_page"]
    # page_width = results[0]["width_page"]
    
    # enc = encoding_for_model(model_name)
    struct_build = TextStructureBuilder(
                                struct_config=struct_config
                                )

    segment_records = []
    # segment_text = []
    for page_info in results: 
        # height, lines, n_lines, n_tokens, n_words, page, width
        n_page = page_info["page"]
        segments, texts = struct_build.build_structure(page_info["lines"])

        segment_text = "\n\n".join(texts)
        segment_info = {
                "page": n_page,
                "height_page": page_info["height_page"],
                "width_page": page_info["width_page"],
                "segments": segments,
                "segment_text": segment_text 
                }
        
        # page_height = results[0]["height_page"]
        # page_width = results[0]["width_page"]
        segment_records.append(segment_info)
        # para_text.append(texts)

        # now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if not session.state.timestamp:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            session.state.timestamp = now
        else: 
            now = session.state.timestamp
        # now = "2026-04-27_20-06-10"
        
        # dict_path = f"{data_processed}/build_structure/{now}_{f_name}_p{n_page}.json"
        # fh.save_dict(segment_info, Path(dict_path))

        # # print(f"[DEBUG] list in build_structure (l. 56; len={len(para_text)}):\n", para_text[0])
        
        # fh.save_md_file(segment_text, f"{now}_{f_name}_p{n_page}", 
        #                 f"{data_processed}/build_structure")

   
    return segment_records  # , para_text


if __name__ == "__main__":
    # load env variables and config
    gh.load_env_vars()
    data_processed = os.getenv("DATA_PROCESSED")
    
    config_name = input("Enter 'config_file' name (no suffix): ")
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    struct_config = config.get("build_structure", {})
    file_folder = struct_config["file_folder"]
    data_folder = f"{data_processed}/{file_folder}"
    timestamp = struct_config["file_timestamp"]
    files_name = struct_config["file_name"]

    for f_name in files_name:
        result_path = Path(f"{data_folder}/{timestamp}_{f_name}.json")
        results = dh.load_dict(result_path)
        build_structure_from_lines(results, f_name)