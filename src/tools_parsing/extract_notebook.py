## extract_notebook.py
# import
import os
# import sys
from pathlib import Path
from returns.result import Result, Success, Failure

from src.core.memory import ParseContext
# # from src.core.feature_enricher import FeatureEnricher
# from gmp_compliance.src.model_parsing.classes_html_parsing import DocumentExtract

# # from datetime import datetime
# # import pprint
# # from tiktoken import encoding_for_model
# # from src.core.logger import create_logger
from src.model_tools_parsing.notebook_extractor import NoteBookCleanExtractor
from src.model_classes_parsing.base_classes_parsing import DocumentExtract
# # import src.utils.general_helper as gh
# # import src.utils.dict_helper as dh
from src.utils.dict_helper import save_dict
from src.utils.path_helper import shorten_path
from src.utils.text_file_helper import save_text_file  # , create_md_from_extract

# from markdownify import markdownify as md


# def extract_md_file():
#     from src.core.memory import session

#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_extract_text_file(config) #


def extract_notebook_json(
    extractor: NoteBookCleanExtractor,
    parse_context: ParseContext,
    f_name: str,  # file_path: str,
    # save: bool = False,
) -> Result[DocumentExtract, str]:
    # from src.core.memory import app_session

    logger = parse_context.logger
    logger.info("Starting extracting notebook from json-file")

    input_data = os.getenv("DATA_INPUT")
    if input_data is None:
        logger.error("Folder 'input_data' is 'None'.")
        # sys.exit()
        return Failure("Folder 'input_data' is 'None'.")
    

    # file_names = run_context.run_settings.file_names
    # if isinstance(file_names, list) and len(file_names) > 0:
    #     for idx, f_name in enumerate(file_names):
            
    f_path = f"{input_data}/{f_name}.json"
                
            # if f_name: 
            #     # ) != 0:
            #     f_path = 
    logger.info("Starting extracting JSON-Notebook (%s)",
                                    shorten_path(f_path))

    nb_extract = extractor.extract(
                            f_path=f_path
                            )
    # else:
        
    return Success(nb_extract)

    # logger.info("Try getting source code from %s",
    #             url)

    # path_md = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/ApoGesetze.md"
    # md_extractor = MDCleanExtractor(
    #                             encoder = enc,
    #                             enricher = enricher
    #                             )

    # logger.info("[DEBUG] fn_arguments:\nfile_path = %s | url = %s | save = %s",
    #             f_path,
    #             url,
    #             save)

    # if f_path is not None:
    #     extract = extractor.extract(f_path=f_path)

    # # elif url is not None:
    # #     html_extract = extractor.extract(url)

    # else:
    #     logger.error("Neither 'file_path' nor 'url' were provided.")
    #     # sys.exit()
    #     return

    # if save and extract is not None:
    #     logger.info("Saving dict and text (as md) of '%s'", shorten_path(f_path))
    #     save_folder = app_session.save_folder
    #     save_name = app_session.save_name

    #     extract_dict = extract.model_dump()
    #     save_nb = Path(f"{save_folder}/{save_name}.json")
    #     save_dict(extract_dict, save_nb)

    #     # text = extract_dict["text"]
    #     text = create_md_from_extract(extract_dict)
    #     # text = md(text)
    #     save_text_file(text, save_name, save_folder)

    # # # pprint.pprint(text_extract)
    # # # return text_extract

    # return extract


# if __name__ == "__main__":
#     extract_notebook_json()
