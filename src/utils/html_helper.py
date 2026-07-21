## html_helper.py
# import

# import urllib.request as u_req       # pathlib,os,uuid
import html
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs

from src.core.memory import app_session
from src.utils.text_file_helper import read_text_file

# def read_html_file(f_path):

#     soup =
#     return soup


def read_html_file(f_path: str, unescaped: bool = False):
    file = read_text_file(f_path)

    # unicode escapes decoden
    # try:
    #     file = codecs.decode(file, "unicode_escape")
    # except Exception:
    #     pass

    # file = file.replace('\\n', '\n')
    # file = re.sub(r'\\(?!n|t|"|u)', '', file)

    # HTML entities decoden (&amp; etc.)
    if unescaped:
        file = file.replace('\\"', '"')
        file = html.unescape(file)

    # print(repr(file[:5000]))
    # sys.exit()

    return file


def scrape_source_code(url):
    page = requests.get(url)

    soup = bs(page.content, "html.parser")
    return soup


# urls = []
#     if f_path is not None:
#         if isinstance(f_path, (str, Path)):
#             f_path = [f_path]

#         for file in f_path:
#             files.append(file)

#     if folder is not None:
#         if isinstance(f_path, (str, Path)):
#             folder = [folder]


def show_element_attributes(soup, element_tag: str):
    logger = app_session.logger
    all_elements = soup.findall(element_tag)

    for idx, element in enumerate(all_elements):
        logger.info("[Element # %s] Attributes:\n%s", idx, element.attrs)

    return None


def normalize_url(url: str, base_url: str = "https:"):
    if url.startswith("//"):
        return urljoin(
            base_url,  # "https://en.wikipedia.org",
            url,
        )

    return url


def check_and_get_elements(soup, elements: str | list[str]) -> list:
    logger = app_session.logger

    if isinstance(elements, str):
        elements = [elements]

    extract = []
    for el in elements:
        if getattr(soup, el, None):
            logger.info("Element(s) of type '%s' found:\n", el)
            el_list = soup.findall(el)

            all_ele = []
            for idx, e in enumerate(el_list):
                all_ele.append(e)
                logger.info("#%s:\t%s", idx, e.text)

            extract.append({"element_type": el, "elements": all_ele})
        else:
            logger.info("No Element(s) of type '%s' found.", el)

    return extract
