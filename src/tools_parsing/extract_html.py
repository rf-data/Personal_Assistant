## extract_html.py
# import
# from pathlib import Path

# from typing import Literal
from returns.result import Failure, Result, Success

from src.core.config import folder_env_vars
from src.core.memory import ParseContext
from src.model_parsing.base_classes_parsing import DocumentExtract

# from src.model_tools.base_assembler import BaseAssembler
from src.model_parsing.html_extractor import HTMLCleanExtractor

# from src.utils.dict_helper import save_dict
from src.utils.path_helper import shorten_path

# from src.utils.text_file_helper import save_text_file  # , create_md_from_extract


# def extract_md_file():

#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_extract_text_file(config) #


def extract_html_file(
    extractor: HTMLCleanExtractor,
    parse_context: ParseContext,
    f_text: str | None = None,
) -> Result[DocumentExtract, str]:
    logger = app_session.logger

    data_dir = folder_env_vars.data_dir
    # html_data = folder_env_vars.data_html

    if parse_context.parse_settings.file_name is not None:
        f_name = parse_context.parse_settings.file_name
        f_path = f"{data_dir}/input/{f_name}.html"

        logger.info("Starting extracting HTML-FILE: %s", shorten_path(f_path))

        html_extract = extractor.extract(f_path=f_path)

    # elif parse_context.parse_settings.url_path is not None:
    #     html_extract = extractor.extract(url=parse_context.parse_settings.url_path)

    elif f_text is not None:
        html_extract = extractor.extract(f_text=f_text)

    else:
        logger.error("Neither 'file_path' nor 'url' nor 'f_text' were provided.")
        # sys.exit()
        return Failure("Neither 'file_path' nor 'url' nor 'f_text' were provided.")

    # if "html" in run_context.run_settings.html.save:
    #     save_folder = run_context.save_folder
    #     save_name = run_context.save_name

    #     # if "html" in run_context.save:
    #     extract_dict = html_extract.model_dump()
    #     save_html = Path(f"{save_folder}/{save_name}")
    #     save_dict(extract_dict, save_html)

    # if "md" in run_context.save:
    #     text = extract_dict["text"]
    #     assembler = BaseAssembler()
    #     text = assembler.create_md_from_extract(extract_dict)
    #     # text = md(text)
    #     save_text_file(text, save_name, save_folder)

    # pprint.pprint(text_extract)
    # return text_extract

    return Success(html_extract)


# if __name__ == "__main__":
#     extract_html_file()
