## wiki_client.py
# import
import logging
import os
import random
import sys

# from pyinputplus import inputYesNo
import time

# Any, List, , Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

import requests

from src.model_parsing.data_classes_wiki import (
    ResultItem,
    SearchResult,
    WikiPage,
    WikiPageMeta,
)

# load_env_vars
from src.utils.dict_helper import save_dict  # , get_yaml_config
from src.utils.general_helper import load_from_cache, make_cache_key, save_to_cache
from src.utils.text_file_helper import save_text_file


@dataclass
class WikipediaClient:
    header: dict = field(default_factory=dict)
    logger = logging.getLogger(__name__)
    now: str | None = field(init=False)
    query: str | None = field(default=None)
    save_folder: Path | None = field(init=False)
    url: str | None = field(default=None)
    wiki_config: dict = field(default_factory=dict)
    req_session: requests.Session | None = field(default=None)

    # from requests.adapters import HTTPAdapter
    # from urllib3.util.retry import Retry

    def __post_init__(self):
        from src.core.memory import session_state

        self.now = self.wiki_config.get(
            "query_time", datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        )

        self.save_folder = Path(os.getenv("DATA_WIKI"))

        self.logger = session_state.logger

        return

    def search_article(
        self,
        query,
        # parse: bool=False,
        save: bool = False,
    ):

        # self.query = query

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
        }

        data = self._get_wiki_response(params)

        results = data.get("query", {}).get("search", [])

        q_results = []
        for idx, hit in enumerate(results):
            q_results.append(
                ResultItem(
                    title=hit.get("title"),
                    page_id=hit.get("pageid"),
                    snippet=hit.get("snippet"),
                    word_count=hit.get("wordcount"),
                    timestamp=hit.get("timestamp"),
                )
            )

            self.logger.info(
                "[Result #%s] Title:\t%s (pageid=%s)", idx, hit["title"], hit["pageid"]
            )
            self.logger.info("snippet:\n%s\n\n", hit["snippet"])

        s_info = data.get("query", {}).get("searchinfo", {})
        s_results = SearchResult(
            query=query,
            params=params,
            results=q_results,
            suggestion=s_info.get("suggestion"),
            suggestion_hits=s_info.get("totalhits"),
        )

        if save:
            raw_path = Path(f"{self.save_folder}/query/{self.now}_{query}_raw")
            norm_path = Path(f"{self.save_folder}/query/{self.now}_{query}_norm")

            save_dict(data, raw_path)
            save_dict(s_results.model_dump(), norm_path)

        return s_results

    # parse = inputYesNo("Start parsing all search hits? Enter 'yes' or 'no'.")

    #         if parse == "yes":

    #             # id_list = inputStr()
    #             # self._parse_max_retry()
    #             self.query = query

    #             all_extract = []
    #             for hit in results:
    #                 # all_extract.append(

    #                 #                 )
    #                 resp = self.parse_article(page_id=hit["pageid"],
    #                                           save=True)
    #                 # if resp.status_code == 429:
    #                 #     self._random_sleep()

    #             return all_extract

    #         else:

    def parse_article(
        self,
        page_info: dict,
        query_param: Literal["page_title", "page_id"] = "page_id",
        save: Literal["info"] | list | None = None,
    ) -> WikiPage | None:
        from src.core.memory import session_state

        self.logger.info(
            "Start parsing page (title=%s | id=%s)",
            page_info.get("title"),
            page_info.get("page_id"),
        )
        params = {
            # "action": "query",
            "action": "parse",
            "format": "json",
            # "section": int,
            # # section         Only parse the content of the section with this identifier.
            "prop": "text",
            # # text            Gives the parsed text of the wikitext.
            # # langlinks       Gives the language links in the parsed wikitext.
            # # categories      Gives the categories in the parsed wikitext.
            # # categorieshtml  Gives the HTML version of the categories.
            # # links           Gives the internal links in the parsed wikitext.
            # # templates       Gives the templates in the parsed wikitext.
            # # images          Gives the images in the parsed wikitext.
            # # externallinks   Gives the external links in the parsed wikitext.
            # # tocdata         Gives the table of contents information in the parsed wikitext.
            # # 'wikitext' --> text
        }

        if query_param == "page_title":
            params["page"] = page_info.get("title")

        elif query_param == "page_id":
            params["pageid"] = page_info.get("page_id")

        else:
            self.logger.error("No 'page_title' and 'page_id' have been provided")
        # req_session = requests.Session()
        # response = req_session.get(url,
        #                            params=params)

        data = self._parse_max_retry(params)
        if data is None:
            self.logger.error("Exceeded max_retries; Could not get page text")
            return

        # print("\nDATA_keys:\n", data.keys())
        # print("2nd lvl keys (after 'parse'):\n", data["parse"].keys())
        # print("3rd lvl keys (after 'parse' / 'text'):\n", data["parse"]["text"].keys())

        art_text = data.get("parse", {}).get("text", "").get("*", "")

        session_state.page_id = page_info.get("page_id")

        article = WikiPage(
            text=art_text,
            title=page_info.get("title", ""),
            meta=WikiPageMeta(
                page_id=session_state.page_id,
                wordcount=page_info.get("word_count"),
                timestamp=page_info.get("timestamp", ""),
            ),
        )
        if save and "info" in save:
            f_name = f"{self.now}_{article.title}_info"
            folder = f"{self.save_folder} / {article.title}_{article.meta.page_id}"

            save_dict(article.model_dump(), Path(f"{f_name}/{folder}"))

            # html_text =

            save_text_file(
                data=art_text, file_name=f_name, folder=folder, suffix="html"
            )

        # save_path = Path(f"/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/wiki_info/{topic}")
        # save_dict(data, save_path)

        # pages = data["query"]["pages"]
        # sections = data["parse"]["sections"]
        # page = next(iter(pages.values()))

        # text = data["parse"]["text"]["*"]

        # print(text[:2000])

        return article

    # def normalize_response(
    #                     self,
    #                     page_info: WikiPage
    #                     ) -> W:

    #     return

    def _parse_max_retry(self, params):

        MAX_RETRIES = self.wiki_config.get("max_retries", 3)

        self.logger.info(
            "Start requesting wiki-API.\nMax_retries: %s\nParameter:\t%s",
            MAX_RETRIES,
            params,
        )
        for att in range(MAX_RETRIES):
            self.logger.info("Starting attempt #%s", att)

            try:
                resp = self._get_wiki_response(params)
                return resp

            except Exception as e:
                self.logger.exception("Failed request attempt #%s:\n%s", att, e)

                self._random_sleep()
                continue

        return

    def _get_wiki_url(self) -> str:
        language = self.wiki_config["language"]

        if language == "en":
            base_url = os.getenv("WIKI_EN_API")
        elif language == "de":
            base_url = os.getenv("WIKI_DE_API")
        else:
            self.logger.error("Invalid language:\t%s", language)
            sys.exit()

        if base_url is None:
            self.logger.error("No API_URL provided in '.env'.")
            sys.exit()

        return base_url

    def _get_wiki_response(self, params: dict) -> dict:

        if self.url is None:
            self.url = self._get_wiki_url()

        # if mode == "search":
        #     endpoint = self.wiki_config["search_API"]
        #     url = url + endpoint

        # req_session = requests.Session()

        key = make_cache_key(self.url, sorted(params.items()))
        cached = load_from_cache(key, folder="wiki/raw")

        if cached is not None:
            return cached

            # load_from_cache(key)

        # sha256(url + sorted(params))

        if self.req_session is None:
            self.req_session = requests.Session()

        response = self.req_session.get(
            self.url, headers=self.header, timeout=10, params=params
        )
        try:
            response.raise_for_status()

            data = response.json()
            save_to_cache(key, data=data, folder="wiki/raw")

            return data

        except requests.exceptions.HTTPError as e:
            self.logger.error("HTTP ERROR:\t%s\n", e, response.text[:1000])

            raise

        except requests.exceptions.JSONDecodeError as e:
            self.logger.error("JSON ERROR:\t%s\n", e, response.text[:1000])

            raise
        # print(response.status_code)
        # print(response.text[:500])

    def _random_sleep(self):

        sleep_time = random.uniform(1.0, 2.5)
        self.logger.info("Rate limited. Waiting %s", round(sleep_time, 2))

        time.sleep(sleep_time)
        # print()
        return
