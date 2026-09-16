## run_text_extraction.py
# import
# import click


# from pathlib import Path
# from datetime import datetime
# from tiktoken import encoding_for_model
from returns.result import Result, Success

from src.core.memory import ParseContext, app_session
from src.model_parsing.base_classes_parsing import PDFPageExtract

# from src.core.logger import create_logger
# from gmp_compliance.src.model_parsing.classes_html_parsing import PDFPageExtract
# from gmp_compliance.src.tools.__dev__extraction import extract_text_per_page
from src.model_parsing.pdf_extractor import PDFCleanExtractor

# from src.core.feature_enricher import FeatureEnricher

# import src.utils.general_helper as gh
# import src.utils.dict_helper as dh
# import src.utils.path_helper as ph


# ------------------
# MAIN FUNCTION
# ------------------
# def pdf_extraction():
#     # load env variables and config
#     gh.load_env_vars()

#     config_name = input("Enter 'config_file' name (no suffix): ")
#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_pdf_extraction(config)


def extract_pdf_file(
    # f_path: str,  #  | List=None,
    extractor: PDFCleanExtractor,
    parse_context: ParseContext,
) -> Result[list[PDFPageExtract], str]:
    logger = app_session.logger
    logger.info("Starting extracting PDF-FILE.")

    # input_data = folder_env_vars("DATA_INPUT")
    # assert input_data is not None

    # name_short = Path(f_path).name.split(".")[0]

    # extract content from file
    f_name = parse_context.parse_settings.file_name
    # f_path = f"{input_data}/{f_name}"
    extract_results = extractor.extract_text_per_page(f_name)

    # feat_enricher = session.enricher
    # results_enriched = feat_enricher.enrich_pages(extract_results)

    extract_grouped = []
    for page_extract in extract_results.unwrap():
        extract_grouped.append(
            extractor.restructure_lines(
                page_extract,
                # save=run_context.parse_settings.pdf.save
            )
        )

    app_session.logger.info("Finished 'extract_pdf.py'")

    return Success(extract_grouped)  # extract_grouped


# if __name__ == "__main__":
#     extract_pdf_file()


# data_processed = folder_env_vars("DATA_PROCESSED")

# general_config = config.get("general_args", {})
# log_name = general_config["name_log"]
# name_logfile = general_config["name_logfile"]
# model_name = general_config["llm_model"]
# enc = encoding_for_model(model_name)

# extract_config = config["extraction"]

# if file_name is None:
#     file_name = extract_config["file_name"]

# if folder is None:
#     folder = folder_env_vars("DATA_RAW")

# if isinstance(file_name, str):
#     file_name = [file_name]

# f_path = []
# for file in file_name:
#     f_path.append(f"{folder}/{file}")

# session.model_config = config

# extractor = TextCleanExtractor(enc, extract_config)

# # setup logger
# logger = create_logger(name=log_name,
#                        file_name=name_logfile)

# extract text from pdf + cleaning
# now = "2026-04-10_11-59-06"
# now = general_config.get(
#                     "timestamp",
#                     datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                     )
# session.state.timestamp = now

# if isinstance(file_name, str):
#     file_name = [file_name]

# for path in f_path:
#     logger.info("Start layout_aware extraction from file:\t%s",
#                 ph.shorten_path(path))
