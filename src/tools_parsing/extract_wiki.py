## wiki_extraction.py
# import
# import requests
# import sys
# # import json


# from pathlib import Path
# from tiktoken import encoding_for_model
# from datetime import datetime
from typing import Literal

# from pyinputplus import inputYesNo
# import browser_cookie3
# from playwright.sync_api import sync_playwright
from src.model_tools_parsing.html_extractor import HTMLCleanExtractor

# from src.core.feature_enricher import FeatureEnricher
from src.model_tools_parsing.wiki_client import WikipediaClient

# from src.core.logger import create_logger
# from src.core.wiki_assembler import WikiPageAssembler
from src.tools_parsing.extract_html import extract_html_file

# from src.utils.general_helper import load_env_vars
from src.utils.dict_helper import load_dict  # , get_yaml_config

# from src.utils.text_file_helper import save_text_file


def extract_wiki_article(
    feat_enricher,
    extract_config: dict,
    save: Literal["html", "info", "md"] | list | None = None,
):
    from src.core.memory import session_state

    logger = session_state.logger
    now = session_state.timestamp

    header = {
        "User-Agent": folder_env_vars.header_agent,
        "Referer": folder_env_vars.header_referer,
        "Accept": folder_env_vars.header_accept,
    }

    wiki = WikipediaClient(wiki_config=extract_config, header=header)

    query_time = extract_config["query_time"]
    query = extract_config["query"]

    data_wiki = folder_env_vars.data_wiki
    result_path = f"{data_wiki}/query/{query_time}_{query}_norm.json"

    result = load_dict(result_path)

    # session_state.save_folder = folder_env_vars("DATA_WIKI") # / "extract_raw"

    to_parse = extract_config.get("article_to_parse", [])

    # info_extract = []
    # text_extract = []
    for item in result.get("results", []):
        if to_parse and item["page_id"] not in to_parse:
            logger.info("Skipping item '%s' (id=%s).", item["title"], item["page_id"])
            continue

        # extract WikiPage_info by API-request
        page_extract = wiki.parse_article(item, save=save)

        # -->  run_context.page_id = page_id

        page_text = page_extract.text

        # info_extract.append(page_extract)

        # extract 'text' from WikiPage_info
        extractor = HTMLCleanExtractor(
            extract_config=extract_config,
            enricher=feat_enricher,
            doc_name=page_extract.title,
            header=header,
        )

        # session.state.save_name = f""
        session_state.save_folder = (
            f"{data_wiki}/{page_extract.title}_{session_state.page_id}"
        )
        session_state.save_name = f"{now}_{page_extract.title}_text"

        html_extract = extract_html_file(
            extractor=extractor, f_text=page_text, save=save
        )

        # if wiki_config.get("assemble_as_md", None):
        #     # text = html_extract.text

        #     save_name = ""
        #     assembler = WikiPageAssembler()
        #     text = assembler.create_md_from_extract(html_extract.model_dump())
        #     # text = md(text)
        #     save_text_file(text,
        #                    save_name,
        #                    session.state.save_folder)

    return html_extract

    # for page in results.results:

    # headers = {}
    # 'User-Agent': 'MediaWiki REST API docs examples/0.1 (https://meta.wikimedia.org/wiki/User:APaskulin_(WMF))'

    # if parse:
    #     for hit in results:
    #         wiki.parse_article(page_id=hit["pageid"])


# if __name__ == "__main__":
#     load_env_vars()

#     from src.core.memory import session

#     wiki_config = get_yaml_config("wiki_requests")

#     general_config = wiki_config.get("general_args", {})
#     log_name = general_config["name_log"]
#     name_logfile = general_config["name_logfile"]

#     now = general_config.get(
#                         "timestamp",
#                         datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                         )
#     session.state.timestamp = now

#     parse_config = wiki_config.get("article_parsing", {})
#     query = parse_config["query"]

#     query_time = parse_config["query_time"]

#     # setup logger
#     logger = create_logger(name=log_name,
#                            file_name=name_logfile)
#     session.logger = logger

#     extract_wiki_article(
#                     query,
#                     query_time,
#                     parse_config,
#                     save=True
#                     )
