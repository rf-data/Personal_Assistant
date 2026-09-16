## wiki_search.py
# import
# import requests
# import sys
# # import json

# from pathlib import Path
# from datetime import datetime
# from typing import Literal
# from pyinputplus import inputYesNo


# import browser_cookie3
# from playwright.sync_api import sync_playwright
# from src.core.config import GenWikiSettings
# from src.core.logger import create_logger
from src.core.config import folder_env_vars

# from src.utils.dict_helper import get_yaml_config
# from src.utils.general_helper import load_env_vars
from src.core.memory import ParseContext
from src.model_parsing.wiki_client import WikipediaClient


def wiki_article_search(parse_context: ParseContext):
    general_config = parse_context.general_settings.wiki
    parse_config = parse_context.parse_settings.wiki

    parse_context.header = {
        "User-Agent": folder_env_vars.header_agent,
        "Referer": general_config.header_referer,
        "Accept": general_config.header_accept,
    }

    wiki = WikipediaClient(parse_context)

    # wiki_config=run_config,
    #                        header=header)

    results = wiki.search_article(query=parse_config.query)

    return results


if __name__ == "__main__":
    # # load_env_vars()

    # from src.core.memory import session_state

    # run_config = session_state.run_settings.wiki

    # query = run_config.query
    # query = input("Please enter wikipedia_search_query:")
    # # n_results=5
    # config = get_yaml_config("wiki_requests")

    # general_config = config.get("general_args")
    # log_name = general_config["name_log"]
    # name_logfile = general_config["name_logfile"]

    # # setup logger
    # logger = create_logger(name=log_name, file_name=name_logfile)
    # session_state.logger = logger

    wiki_article_search(RunContext())
