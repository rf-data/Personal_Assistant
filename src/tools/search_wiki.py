## wiki_search.py
# import
# import requests
# import sys
# # import json
# import os
# from pathlib import Path
# from datetime import datetime
# from typing import Literal
# from pyinputplus import inputYesNo


# import browser_cookie3
# from playwright.sync_api import sync_playwright

from src.core.logger import create_logger
from src.model_tools.wiki_client import WikipediaClient
from src.utils.dict_helper import get_yaml_config
from src.utils.general_helper import load_env_vars


def wiki_article_search(query, general_config: dict, save: bool = False):

    header = {
        "User-Agent": general_config["header_agent"],
        "Referer": general_config["header_referer"],
        "Accept": general_config["header_accept"],
    }

    wiki = WikipediaClient(wiki_config=general_config, header=header)

    results = wiki.search_article(query, save=save)

    return results


if __name__ == "__main__":
    load_env_vars()

    from src.core.memory import session_state

    query = input("Please enter wikipedia_search_query:")
    # n_results=5
    config = get_yaml_config("wiki_requests")

    general_config = config.get("general_args")
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]

    # setup logger
    logger = create_logger(name=log_name, file_name=name_logfile)
    session_state.logger = logger

    wiki_article_search(query, general_config, save=True)
