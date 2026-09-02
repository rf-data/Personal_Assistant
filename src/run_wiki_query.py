## run_wiki_query.py
# import
from __future__ import annotations
from datetime import datetime

from src.core.logger import create_logger
from src.core.memory import app_session, WikiContext
from src.core.config import parsing_env_vars

from src.tools_parsing.search_wiki import wiki_article_search

from src.utils.dict_helper import load_dict, save_dict


# ------------------
# MAIN FUNCTION
# ------------------
def run_wiki_query():

    context_name = input("Enter name of context file (no suffix): ")
    dict_path = parsing_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(path=dict_path)

    return wiki_query(WikiContext.model_validate(context))


def wiki_query(context: WikiContext):
    cfg_general = context.general_settings
    cfg_parse = context.parse_settings
    cfg_wiki = cfg_parse.wiki

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # app_session.timestamp = now
    
    # setup logger
    log_name = cfg_parse.name_log
    name_logfile = cfg_parse.name_logfile
    app_session.logger = create_logger(name=log_name, file_name=name_logfile)

    query = cfg_wiki.query
    if not query: 
        # len(context.parse_settings.wiki.query) == 0: 
        # parse_config.wiki.query = query
        query = input("Enter the query: ")
        cfg_wiki.query = query

    result = wiki_article_search(parse_context=context)

    print("Result:\n", result)

    save_path = parsing_env_vars.data_wiki / f"{query}_{now}.json"
    save_dict(
        data=result.model_dump(mode="json"),
        path=save_path
        )

if __name__ == "__main__":
    run_wiki_query()


