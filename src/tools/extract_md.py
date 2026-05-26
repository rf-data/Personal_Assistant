## extract_text.py
# import
# import os
from pathlib import Path

# from src.core.feature_enricher import FeatureEnricher
from src.model_parsing.data_classes_parsing import DocumentExtract

# from datetime import datetime
# import pprint
# from tiktoken import encoding_for_model
# from src.core.logger import create_logger
from src.model_tools.text_extractor import MDCleanExtractor

# import src.utils.general_helper as gh
# import src.utils.dict_helper as dh
from src.utils.dict_helper import save_dict

# import src.utils.path_helper as ph


# def extract_md_file():
#     from src.core.memory import session

#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_extract_text_file(config) #


def extract_md_file(
    file_path: str,  # file_path: str,
    extractor: MDCleanExtractor,
    save: bool = False,
) -> DocumentExtract:
    from src.core.memory import session_state

    logger = session_state.logger

    # file_path = Path(extract_config["file_path"])
    # suffix = file_path.suffix

    ##################
    # CASE 2
    ##################
    # elif suffix == ".md":
    logger.info("Starting extracting a MD-FILE")
    # path_md = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/ApoGesetze.md"
    # md_extractor = MDCleanExtractor(
    #                             encoder = enc,
    #                             enricher = enricher
    #                             )
    md_extract = extractor.extract(file_path)

    if save:
        save_folder = session_state.save_folder
        save_name = session_state.save_name

        save_md = Path(f"{save_folder}/{save_name}.json")
        save_dict(md_extract.model_dump(), save_md)

    # pprint.pprint(text_extract)
    # return text_extract

    return md_extract


# if __name__ == "__main__":
#     extract_md_file()
