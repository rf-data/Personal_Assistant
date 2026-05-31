## extract_text.py
# import
# import os
from pathlib import Path

# from gmp_compliance.src.model_parsing.classes_html_parsing import DocumentExtract

# from datetime import datetime
# import pprint
# from tiktoken import encoding_for_model
# from src.core.logger import create_logger
from src.model_tools.text_extractor import TXTCleanExtractor  # , MDCleanExtractor

# from src.core.feature_enricher import FeatureEnricher
# import src.utils.general_helper as gh
# import src.utils.dict_helper as dh
from src.utils.dict_helper import save_dict

# import src.utils.path_helper as ph


# def extract_text_file():
#     from src.core.memory import session

#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_extract_txt_file(config) #


# ------------------
# MAIN FUNCTION
# ------------------
def extract_txt_file(
    file_path: str,  # file_path: str,
    extractor: TXTCleanExtractor,
    save: bool = False,
) -> DocumentExtract:
    from src.core.memory import session_state

    logger = session_state.logger

    # file_path = Path(extract_config["file_path"])
    # suffix = file_path.suffix

    ##################
    # CASE 1
    ##################
    # if suffix == ".txt":
    logger.info("Starting extracting a TXT-FILE")

    txt_extract = extractor.extract(file_path)

    if save:
        save_folder = session_state.save_folder
        save_name = session_state.save_name

        save_txt = Path(f"{save_folder}/{save_name}.json")
        save_dict(txt_extract.model_dump(), save_txt)

    return txt_extract


# if __name__ == "__main__":
#     extract_txt_file()
