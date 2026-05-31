## apollo_extractor.py
# import
# import html
# import re
import json
# import sys
from returns.result import Result, Success, Failure
from dataclasses import dataclass   # , field
# from pathlib import Path

import requests
from bs4 import BeautifulSoup as bs
# from bs4 import NavigableString  # , Tag

from src.model_parsing.base_classes_parsing import (
    Code, 
    CodeMeta,
    Document,
    DocumentExtract,
    Element,
    ElementMeta,
    HeadingMeta,
    Image,
    ImageMeta,
    ListMeta,
    Word
    )
from src.model_parsing.classes_html_parsing import (
    BulletNode,
    CiteNode,
    CodeNode,
    Heading,
    ImageNode,
    Link, 
    LinkNode,
    BulletList,
    OtherNode,
    Paragraph,
    TextNode
)
from src.model_tools.html_extractor import HTMLCleanExtractor
# from src.utils.html_helper import normalize_url
# from src.utils.path_helper import shorten_path
# from src.utils.text_file_helper import read_html_file   # , save_text_file
# from src.utils.dict_helper import save_dict

# from src.core.memory import RunContext

@dataclass
class ApolloCleanExtractor(HTMLCleanExtractor):
    
    def extract_html(
                self, 
                f_text: str
                ) -> Result[DocumentExtract, str]:
        
        # data = self._get_apollo_data(f_text)

        apollo_extract = self._get_apollo_data(f_text)\
                            .bind(self._extract_apollo_elements)
        # (data)
        if apollo_extract is None:
            return Failure("Error while parisng")
        #########
        # TO DOs
        # - build text
        # - add_basic_metadata
        #########

        # save_folder = 
        # "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data"

        return Success(
                    DocumentExtract(
                            doc_type="html_apollo",
                            doc_name=self.doc_name,
                            text="",
                            elements=apollo_extract
                            # meta=doc_info.meta,
        ))
    

    def _get_apollo_data(
                    self, 
                    f_text: str
                    ) -> Result:

        soup = bs(f_text, self.parser)
        scripts_all = soup.find_all("script")

        apollo_text = None

        for script in scripts_all:
            text = script.text      # .string
            
            if not text:
                continue
                
            if "window.__APOLLO_STATE__" in text:
                apollo_text = str(text)
                break
        
        if not apollo_text:
            Failure("No APOLLO_STATE found")
            # raise ValueError("No APOLLO_STATE found")

        json_text = apollo_text.split(
                    "window.__APOLLO_STATE__ = ",
                    1
                    )[1]

        json_text = json_text.strip()

        if json_text.endswith(";"):
            json_text = json_text[:-1]
            
        return Success(json.loads(json_text))


    def _extract_apollo_elements(
                            self, 
                            data: dict
                            ) -> Result[list[Element], None]:

        data_root = data.get("ROOT_QUERY", {}) 

        self.logger.info("Found 'ROOT_QUERY'. Keys:\n %s",
                         data_root.keys())
        
        page_content = []      # re.match(r"", root_keys)

        for key in data.keys():
            if key.startswith("Post:"):
                # data_post.append({
                #             "key": key,
                #             "content": data[key]
                #             })
                
                info = data[key]

                if "title" in info.keys():
                    page_content.append({
                            "key": key,
                            "content": data[key]
                            })      # .split(":")[-1]

        self.logger.info("Found %s 'actual' page_content",
                        len(page_content)
                        )

        body_model = []
        for cont in page_content:
            
            p_cont = cont["content"]
            for key in p_cont.keys():
                if key.startswith("content({\"postMeteringOptions\""):
                    
                    body_model.append({
                                "key": key,
                                "content": p_cont[key].get("bodyModel")})


        self.logger.info("Found %s bodyModel(s)",
                        len(body_model)
                        )
        
        # text_full = ""
        paragraphs = body_model[0]["content"].get("paragraphs")

        current_headings = {}
        extract = []
        # medium_dict = {}
        idx = 0
        for para_ref in paragraphs:
            ref = para_ref["__ref"]

            text_type = data[ref].get("type")
            p_text = data[ref].get("text", "")
            p_markups = data[ref].get("markups", [])
            p_meta_ref = data[ref].get("metadata", 
                                       {}).get("__ref", 
                                               "")
            if text_type.startswith("H"):
                level = text_type[1]

                current_headings[level] = p_text

                for k in list(current_headings):
                    if k > level:
                        del current_headings[k]

                extract.append(
                    TextNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=current_headings[level],
                        # leaf_type="heading",
                        # inline_elements=h_elements,
                        meta=HeadingMeta(
                                        # element_id=idx, 
                                        level=level
                                        ),
                    )
                )
                idx += 1

            elif text_type == "P":  # paragraph

                extract.append(
                    TextNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=p_text,
                        # tag.decode_contents(),
                        # get_text(" ", strip=True),
                        # inline_elements=p_elements,
                        meta=ElementMeta(
                            # element_type="paragraph",
                            # element_id=idx,
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif text_type in ["ULI", "OLI"]:  # un-/ordered list
                # l_text, l_elements = self._parse_inline(tag)

                extract.append(
                    BulletNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=p_text,
                        # tag.decode_contents(),
                        # tag.get_text(" ", strip=True),
                        # inline_elements=l_elements,
                        meta=ListMeta(
                            # element_type="bullets_list",
                            # element_id=idx,
                            list_type="ordered" if text_type == "OLI" else "unordered",
                        ),
                    )
                )
                idx += 1

            elif text_type == "PRE":  # code_block
                # code = tag.get_text()

                try:
                    code = code.encode().decode("unicode_escape")
                except Exception:
                    pass

                # parts.append(f"{code}")

                # self._parse_inline(tag)
                # tag.get_text("\n", strip=False)
                # code_tag = tag.find("code")
                lang = ""

                # print(code_tag)
                # print(code_tag.attrs)
                # print(code_tag.get("class"))

                # if code_tag:
                #     classes = code_tag.get("class", [])
                #     lang = next(
                #         (
                #             c.replace("language-", "")
                #             for c in classes
                #             if c.startswith("language-")
                #         ),
                #         "",
                #     )

                extract.append(
                    CodeNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=p_text,
                        # tag.get_text(" ", strip=True),
                        meta=CodeMeta(
                            # element_type="code",
                            # element_id=idx,
                            language=lang,
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif text_type == "BQ":

                quote_text = ""
                for part in p_text.split("\n"):
                    quote_text += f"> {part}\n"

                extract.append(
                    BlockQuoteNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=quote_text,
                        # self._parse_inline(tag),
                        # ,
                        # tag.get_text(" ", strip=True),
                        meta=ElementMeta(
                            # element_type="image",
                            # element_id=idx,
                            # src=src,
                            # downloadable=success,
                            # alt=alt,
                            # style=style,
                            # text_file=str(self.save_name),
                            # folder=str(self.save_folder),
                            # image_file=src.split("/")[-1] if success else "",
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            elif text_type == "MIXTAPE_EMBED":
                extract.append(
                    LinkPreviewNode(
                        leaf_id=idx,
                        markups=p_markups,
                        text=f"[Link]({p_text})",
                        # self._parse_inline(tag),
                        # ,
                        # tag.get_text(" ", strip=True),
                        meta=ElementMeta(
                             context=dict(current_headings),
                        ),
                    )
                )
                idx += 1


            elif text_type == "IMG":  # image
                # src = tag.get("src", "")
                # alt = tag.get("alt", "")
                # style = tag.get("style", "")

                # if self.extract_config.get("scrape_images"):
                #     success = self._scrape_image(src, str(self.save_folder))
                # else:
                #     success = None

                meta_info={}
                if len(p_meta_ref) > 0:
                    meta_info = data[p_meta_ref]
                    
                extract.append(
                    ImageNode(
                        leaf_id=idx,
                        markups=p_markups,
                        meta_from_html=meta_info,
                        text=f"[image]({p_text})",
                        meta=ImageMeta(
                            context=dict(current_headings),
                        ),
                    )
                )
                idx += 1

            
            else:
                self.logger.info(
                    "Text type of element does not match with a relevant type:\t%s", 
                    text_type
                )

        self.logger.info(
            "Number of extracted elements:\t%s",
            #  Tag of element does not match with a relevant tag:\t%s",
            len(extract),
        )

        return Success(extract)

