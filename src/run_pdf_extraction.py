## run_text_extraction.py
# import
# import click
import os
from pathlib import Path
from datetime import datetime
from tiktoken import encoding_for_model
from typing import List

from src.core.memory import session
from src.core.logger import create_logger
# from gmp_compliance.src.tools.__dev__extraction import extract_text_per_page
# from src.core.pdf_clean_extractor import PDFCleanExtractor
# from src.core.feature_enricher import FeatureEnricher

import src.utils.general_helper as gh
import src.utils.dict_helper as dh
import src.utils.path_helper as ph


# ------------------
# MAIN FUNCTION
# ------------------
def text_extraction():  
    # load env variables and config
    gh.load_env_vars()

    config_name = input("Enter 'config_file' name (no suffix): ")
    config = dh.get_yaml_config(config_name)
    session.model_config = config

    return run_text_extraction(config)


def run_text_extraction(config: dict, 
                        file_name: str | List=None,
                        folder: str=None) -> Path:
    # load env variables and config
    gh.load_env_vars()
    data_processed = os.getenv("DATA_PROCESSED")
    
    general_config = config.get("general_args", {})
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]
    model_name = general_config["llm_model"]
    enc = encoding_for_model(model_name)

    extract_config = config["extraction"]

    if file_name is None:
        file_name = extract_config["file_name"]

    if folder is None:
        folder = os.getenv("DATA_RAW")   

    if isinstance(file_name, str):
        file_name = [file_name]

    f_path = []
    for file in file_name:
        f_path.append(f"{folder}/{file}")

    session.model_config = config
    
    extractor = TextCleanExtractor(enc, extract_config)
    
    # setup logger
    logger = create_logger(name=log_name, 
                           file_name=name_logfile)
    session.logger = logger

    # extract text from pdf + cleaning
    # now = "2026-04-10_11-59-06" 
    now = general_config.get(
                        "timestamp", 
                        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        )
    session.state.timestamp = now

    if isinstance(file_name, str):
        file_name = [file_name]

    for path in f_path:
        logger.info("Start layout_aware extraction from file:\t%s",
                    ph.shorten_path(path))
        
        name_short = Path(path).name.split(".")[0]
        
        extract_results = extractor.extract_text_per_page(f_path)
        
        feat_enricher = session.enricher
        results_enriched = feat_enricher.enrich_pages(extract_results)

        save_path = Path(f"{data_processed}/extract_from_text/{now}_{name_short}_extract.json")
        dh.save_dict(results_enriched, save_path)

        # text_comb = "\n\n".join(text)
        # dh.save_md_file(text_comb, f"{now}_{name_short}_text", f"{data_processed}/extract_from_words")

    return save_path


if __name__ == "__main__":
    text_extraction()
 