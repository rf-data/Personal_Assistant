## html_extractor.py
# import
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup as bs
from bs4 import NavigableString  # , Tag

# from gmp_compliance.src.model_parsing.classes_html_parsing import (
#     BulletNode,
#     CiteNode,
#     CodeMeta,
#     CodeNode,
#     Document,
#     DocumentExtract,
#     Element,
#     ElementMeta,
#     HeadingMeta,
#     Image,
#     ImageMeta,
#     ImageNode,
#     LinkNode,
#     ListMeta,
#     OtherNode,
#     TextNode,
#     Word,
# )
from src.model_tools import HTMLCleanExtractor

from src.utils.html_helper import normalize_url
from src.utils.path_helper import shorten_path
from src.utils.text_file_helper import read_html_file


@dataclass
class URLCleanExtractor(HTMLCleanExtractor):
    def extract(self, f_path=None, url=None, f_text=None):
        # parser = extract_config["html_parser"]
        parser = "html.parser"  # "lxml"
        if f_path is not None:
            # data_src == "file":
            file = read_html_file(f_path)

            soup = bs(file, parser)

            self.logger.info("Created soup from '%s'", shorten_path(f_path))

        elif url is not None:
            # data_src == "file":
            page = requests.get(url, timeout=10)

            soup = bs(page.content, parser)

            self.logger.info("Created soup from '%s'", url)

        elif f_text is not None:
            soup = bs(f_text, parser)

            self.logger.info("Created soup from '%s'", f_text[:100])

        else:
            self.logger.error("Neither 'f_path' nor 'url' nor 'f_text' were provided.")
            sys.exit()

        # extract_approach = extract_config["extract_approach"]
        # self.relevant_tags = self.extract_config["extraction_tags"]

        root = soup.find("div", class_="container") or soup.body or soup

        elements_all = self._extract_elements(root)

        elements_clean = []
        for element in elements_all:
            # text_clean = self._clean_text(element.text)
            words_clean = []
            for word in re.findall(r"\S+|\n", element.text):
                # element.text.split():   # text_clean.split():

                words_clean.append(Word(text=self._clean_word_token(word)))

            if element.meta.element_type != "code":
                txt_clean = self._clean_text(element.text)
            else:
                txt_clean = element.text

            # " ".join([w.text for w in words_clean])

            # if element.meta.element_type == "bullets_line":
            #     txt_splits = txt_clean.split("-")
            #     txt_clean = "\n-".join(txt_splits)

            element_new = self.enricher._add_basic_metadata(
                txt_clean, words_clean, element
            )

            # element_new.meta.element_type = element.meta.element_type

            elements_clean.append(element_new)

        text_clean = "\n\n".join([ele.text for ele in elements_clean])
        doc_info = self.enricher._add_basic_metadata(
            text_clean, elements_clean, Document()
        )

        return DocumentExtract(
            doc_type="md",
            doc_name=self.doc_name,
            text=doc_info.text,
            elements=doc_info.elements,
            meta=doc_info.meta,
        )

    def _clean_text(self, text: str) -> str:
        text = html.unescape(text)

        # Mehrfache Leerzeichen
        text = re.sub(r"[ \t]+", " ", text)

        # Mehrfache Leerzeilen
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Spaces vor newline
        text = re.sub(r" +\n", "\n", text)

        text = text.replace('\\"', '"')
        text = text.replace("\\n", "\n")
        text = re.sub(r'\\(?!n|t|"|u)', "", text)

        # text = re.sub(r"(\\\\n)", "\n", text)
        # text = re.sub(r'(\\\")', '"', text)
        # text = text.replace('\\"', '"')
        # text = text.replace('\\n', '\n')

        return text

    def _is_inside_relevant_parent(self, tag):
        return tag.find_parent(["p", "ul", "ol", "pre", "table"]) is not None

    def _extract_elements(self, root) -> list[Element]:
        self.logger.info(
            "Relevant tags (in _extract_elements()):\n%s", self.RELEVANT_TAGS
        )

        extract = []
        current_headings = {}
        idx = 0
        for tag in root.find_all(self.RELEVANT_TAGS, recursive=True):
            # protection against duplicates
            if tag.name in ["code", "li"] and self._is_inside_relevant_parent(tag):
                continue

            if tag.name.startswith("h"):
                # in ["h1", "h2", "h3",
                #   "h4", "h5", "h6"]:      # heading

                level = int(tag.name[1])

                h_text, h_elements = self._parse_inline(tag)
                current_headings[level] = h_text
                # tag.get_text(" ",
                #                                        strip=True)

                # tiefere Headings löschen
                for k in list(current_headings):
                    if k > level:
                        del current_headings[k]

                extract.append(
                    Element(
                        text=current_headings[level],
                        leaf_type="heading",
                        inline_elements=h_elements,
                        meta=HeadingMeta(element_id=idx, level=level),
                    )
                )
                idx += 1

            elif tag.name == "p":  # paragraph
                p_text, p_elements = self._parse_inline(tag)

                extract.append(
                    Element(
                        text=p_text,
                        # tag.decode_contents(),
                        # get_text(" ", strip=True),
                        inline_elements=p_elements,
                        meta=ElementMeta(
                            element_type="paragraph",
                            element_id=idx,
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif tag.name in ["ul", "ol"]:  # un-/ordered list
                l_text, l_elements = self._parse_inline(tag)

                extract.append(
                    Element(
                        text=l_text,
                        # tag.decode_contents(),
                        # tag.get_text(" ", strip=True),
                        inline_elements=l_elements,
                        meta=ListMeta(
                            element_type="bullets_list",
                            element_id=idx,
                            list_type="ordered" if tag.name == "ol" else "unordered",
                        ),
                    )
                )
                idx += 1

            elif tag.name == "pre":  # code_block
                code = tag.get_text()

                try:
                    code = code.encode().decode("unicode_escape")
                except Exception:
                    pass

                # parts.append(f"{code}")

                # self._parse_inline(tag)
                # tag.get_text("\n", strip=False)
                code_tag = tag.find("code")
                lang = ""

                # print(code_tag)
                # print(code_tag.attrs)
                # print(code_tag.get("class"))

                if code_tag:
                    classes = code_tag.get("class", [])
                    lang = next(
                        (
                            c.replace("language-", "")
                            for c in classes
                            if c.startswith("language-")
                        ),
                        "",
                    )

                extract.append(
                    Element(
                        text=code,
                        # tag.get_text(" ", strip=True),
                        meta=CodeMeta(
                            element_type="code",
                            element_id=idx,
                            language=lang,
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif tag.name == "table":
                tab_text, tab_elements = self._parse_inline(tag)

                extract.append(
                    Element(
                        text=tab_text,
                        # tag.get_text(" ", strip=True),
                        inline_elements=tab_elements,
                        meta=ElementMeta(element_type="table", element_id=idx),
                    )
                )
                idx += 1

            elif tag.name == "sup":
                cit_text, cit_elements = self._parse_inline(tag)

                extract.append(
                    Element(
                        text=cit_text,
                        # tag.get_text(" ", strip=True),
                        inline_elements=cit_elements,
                        meta=ElementMeta(element_type="ext_reference", element_id=idx),
                    )
                )
                idx += 1

            elif tag.name == "img":  # image
                src = tag.get("src", "")
                alt = tag.get("alt", "")
                style = tag.get("style", "")

                if self.extract_config.get("scrape_images"):
                    success = self._scrape_image(src, str(self.save_folder))
                else:
                    success = None

                extract.append(
                    Image(
                        text=f"[image]({alt or src})",
                        # self._parse_inline(tag),
                        # ,
                        # tag.get_text(" ", strip=True),
                        meta=ImageMeta(
                            element_type="image",
                            element_id=idx,
                            src=src,
                            downloadable=success,
                            alt=alt,
                            style=style,
                            text_file=str(self.save_name),
                            folder=str(self.save_folder),
                            image_file=src.split("/")[-1] if success else "",
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif tag.name == "a":  # external link
                ref_text, ref_elements = self._parse_inline(tag)

                extract.append(
                    Element(
                        text=ref_text,
                        # tag.get_text(" ", strip=True),
                        inline_elements=ref_elements,
                        meta=ElementMeta(element_type="link_reference", element_id=idx),
                    )
                )
                idx += 1

            else:
                self.logger.info(
                    "Tag of element does not match with a relevant tag:\t%s", tag.name
                )

        self.logger.info(
            "Number of extracted elements:\t%s",
            #  Tag of element does not match with a relevant tag:\t%s",
            len(extract),
        )

        return extract

    def _parse_inline(self, tag) -> tuple[str, list]:
        parts = []
        text_full = []

        for child in tag.children:
            # normaler Text
            if isinstance(child, NavigableString):
                text = str(child)

                if child.name not in ["code", "p"]:
                    text = text.replace("\n", " ")

                parts.append(TextNode(text=text))
                text_full.append(text)

            # inline code
            elif child.name == "code":
                code = child.get_text()

                try:
                    code = bytes(code, "utf-8").decode("unicode_escape")
                except Exception:
                    pass

                # parts.append()       # strip=True
                parts.append(CodeNode(text=code))
                text_full.append(f"{code}")

            # links
            elif child.name == "a":
                a_text, a_elements = self._parse_inline(child)
                # text =
                href = child.get("href", "")

                parts.append(
                    LinkNode(text=a_text, href=href, inline_elements=a_elements)
                )
                text_full.append(a_text)

            elif child.name == "img":
                img_text, img_elements = self._parse_inline(child)
                src = child.get("src", "")
                alt = child.get("alt", "")

                parts.append(
                    ImageNode(
                        src=src, alt=alt, text=img_text, inline_elements=img_elements
                    )
                )
                text_full.append(alt or src)

            elif child.name == "sup":
                sup_text, sup_elements = self._parse_inline(child)
                # text =
                href = child.get("href", "")

                parts.append(
                    CiteNode(text=sup_text, href=href, inline_elements=sup_elements)
                )
                text_full.append(sup_text)

            # bold
            elif child.name in ["strong", "b"]:
                bold_text, bold_elements = self._parse_inline(child)

                text = f"**{bold_text}**"

                parts.append(TextNode(text=text, inline_elements=bold_elements))
                text_full.append(text)

            # italic
            elif child.name in ["em", "i"]:
                ital_text, ital_elements = self._parse_inline(child)

                text = f"*{ital_text}*"

                parts.append(TextNode(text=text, inline_elements=ital_elements))
                text_full.append(text)

            elif child.name == "li":
                li_text, li_elements = self._parse_inline(child)

                text = f"\n- {li_text}\n"

                parts.append(BulletNode(text=text, inline_elements=li_elements))
                text_full.append(text)

            elif child.name == "br":
                text = "\n"

                parts.append(TextNode(text=text))
                text_full.append(text)

            else:
                other_text, other_elements = self._parse_inline(child)

                text = f"{other_text}"

                parts.append(OtherNode(text=text, inline_elements=other_elements))
                text_full.append(text)

        return "".join(text_full), parts

    def _scrape_image(self, img_url: str, save_folder: str) -> bool:
        # logger = session.logger

        img_name = img_url.split("/")[-1].split("?")[0]

        if self._is_blacklisted(img_url):
            return False

        img_url_norm = normalize_url(img_url)

        # if not Path(img_url_norm).suffix():
        #     img_url_norm += ".png"
        try:
            if self.req_session is None:
                self.req_session = requests.Session()

            r = self.req_session.get(
                img_url_norm, timeout=15, headers=self.header, stream=True
            )

            r.raise_for_status()

            content_type = r.headers.get("content-type", "")

            if not content_type.startswith("image/"):
                self.logger.warning(
                    "URL is not an image: %s (%s)", img_url, content_type
                )

                return False

            suffix_final = self._ensure_suffix(img_url_norm, content_type)

            # suffix = self.MIME_MAP.get(content_type.split(";")[0])
            save_path = Path(f"{save_folder}/{img_name}{suffix_final}")

            with open(save_path, "wb") as f:
                self.logger.info("Scraping image '%s'", f"{img_url_norm}{suffix_final}")

                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return True

        except Exception:
            self.logger.exception("Failed downloading image '%s'", img_url)

        return False

    def _ensure_suffix(self, url: str, content_type: str) -> str:
        url_suffix = Path(url).suffix
        cont_suffix = self.MIME_MAP.get(content_type.split(";")[0])

        return url_suffix or cont_suffix or "bin"

    def _is_blacklisted(self, img_url):
        if re.search(r"/\d{1,2}px-", img_url):
            self.logger.info(
                "Image '%s' appears to be small (<= 60px) and will not be scraped.",
                img_url,
            )
            #  word)
            return True

        for word in self.BLACKLIST_ICON:
            if word.lower() in img_url.lower():
                self.logger.info(
                    "Image '%s' is blacklisted (keyword='%s') and will not be scraped.",
                    img_url,
                    word,
                )
                return True

        return False

    # def _extract_elements_from_soup(self, soup):
    #     extract_elements = self.extract_config["extract_elements"]

    #     extract = {}
    #     if "paragraph" in extract_elements:
    #         extract["para"] = self._extract_paragraphs(soup)

    #     if "image" in extract_elements:
    #         extract["img"] = self._extract_images(soup)

    #     if "table" in extract_elements:
    #         extract["table"] = self._extract_tables(soup)

    #     if "list" in extract_elements:
    #         extract["list"] = self._extract_lists(soup)
    #         # CAVE: ORDERED vs. UNORDERED

    #     if "link" in extract_elements:
    #         extract["link"] = self._extract_links(soup)

    #     return extract

    # element_by_id = soup.find('div', id= 'main-content')
    # element_by_class = soup.find('div', class_= 'content')
    # element_by_attrs = soup.find('div', attrs={'class': 'content', 'data-lang': 'en'})

    # print("element_by_id : ",element_by_id.text)
    # print("element_by_class : ",element_by_class.text)
    # print("element_by_attrs : ",element_by_attrs.text)


# url = 'https://en.wikipedia.org/wiki/Alan_Turing'
# page = requests.get(url)
# soup = bs(page.content, "lxml")
# print(soup)

# code_source = '''
# <html>
#   <body>
#     <h1 id="first"> Title 1 </h1>
#     <div id="main-content"> Unique main content </div>
#     <div class="content"> Initial content </div>
#     <div class="content" data-lang="en"> A second English content </div>
#     <h1 id="second"> Title 2 </h1>
#     <ul id="lists">
#         <li class="chip"> Element 1 </li>
#         <li class="chip"> Element 2 </li>
#         <li class="chip"> Element 3 </li>
#     </ul>
#     <div>
#         <p class="paragraph"> A new paragraph </p>
#     </div>
#   </body>
# </html>
# '''

# soup = bs(code_source, 'html.parser')
# element_by_id = soup.find('div', id= 'main-content')
# element_by_class = soup.find('div', class_= 'content')
# element_by_attrs = soup.find('div', attrs={'class': 'content', 'data-lang': 'en'})

# print("element_by_id : ",element_by_id.text)
# print("element_by_class : ",element_by_class.text)
# print("element_by_attrs : ",element_by_attrs.text)
