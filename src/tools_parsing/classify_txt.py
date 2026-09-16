## classify_txt.py
# import
#
# from datetime import datetime
# import pprint
# from tiktoken import encoding_for_model

# from src.core.logger import create_logger
# from src.core.feature_enricher import FeatureEnricher
# import src.utils.general_helper as gh
# from gmp_compliance.src.model_parsing.classes_html_parsing import DocumentExtract
from src.model_parsing.text_classifier import TXTClassifier

# import src.utils.dict_helper as dh
from src.utils.dict_helper import save_dict
from src.utils.text_file_helper import save_text_file

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
def classify_txt_file(
    file: DocumentExtract,  # file_path: str,
    classifier: TXTClassifier,
    save: bool = False,
) -> DocumentExtract:
    from src.core.memory import session_state

    # load env variables and config
    #  gh.load_env_vars()

    logger = session_state.logger

    txt_classified = classifier.classify_lines(file)

    if save:
        logger.info("Start saving '%s' as json and md_file.")

        save_folder = session_state.save_folder
        save_name = session_state.save_name

        path_json = save_folder / f"{save_name}.json"

        # text = txt_classified.text
        save_dict(txt_classified.model_dump(), path_json)
        save_text_file(txt_classified.text, save_name, save_folder)

    return txt_classified
