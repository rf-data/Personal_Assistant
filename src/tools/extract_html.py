## extract_html.py
# import
# import os
# import sys
from pathlib import Path
from typing import Literal

# from src.core.feature_enricher import FeatureEnricher
from src.model_parsing.data_classes_parsing import DocumentExtract
from src.model_tools.base_assembler import BaseAssembler

# from datetime import datetime
# import pprint
# from tiktoken import encoding_for_model
# from src.core.logger import create_logger
from src.model_tools.html_extractor import HTMLCleanExtractor

# import src.utils.general_helper as gh
# import src.utils.dict_helper as dh
from src.utils.dict_helper import save_dict
from src.utils.text_file_helper import save_text_file  # , create_md_from_extract

# import src.utils.path_helper as ph
# from markdownify import markdownify as md


# def extract_md_file():
#     from src.core.memory import session

#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_extract_text_file(config) #


def extract_html_file(
    extractor: HTMLCleanExtractor,
    f_path: str = None,  # file_path: str,
    url: str = None,
    f_text: str = None,
    save: Literal["html", "md"] | list | None = None,
) -> DocumentExtract:
    from src.core.memory import session_state

    logger = session_state.logger
    logger.info("Starting extracting HTML-FILE.")

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

    if f_path is not None:
        html_extract = extractor.extract(f_path=f_path)

    elif url is not None:
        html_extract = extractor.extract(url=url)

    elif f_text is not None:
        html_extract = extractor.extract(f_text=f_text)

    else:
        logger.error("Neither 'file_path' nor 'url' nor 'f_text' were provided.")
        # sys.exit()
        return

    if save is not None:
        save_folder = session_state.save_folder
        save_name = session_state.save_name

        if "html" in save:
            extract_dict = html_extract.model_dump()
            save_html = Path(f"{save_folder}/{save_name}")
            save_dict(extract_dict, save_html)

        if "md" in save:
            text = extract_dict["text"]
            assembler = BaseAssembler()
            text = assembler.create_md_from_extract(extract_dict)
            # text = md(text)
            save_text_file(text, save_name, save_folder)

    # pprint.pprint(text_extract)
    # return text_extract

    return html_extract


# if __name__ == "__main__":
#     extract_html_file()
