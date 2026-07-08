## apollo_extractor.py
# import
# import html
import re
import json
from pathlib import Path
# import sys
from returns.result import Result, Success, Failure
from dataclasses import dataclass   # , field
# from pathlib import Path

# import requests
from bs4 import BeautifulSoup as bs
# from bs4 import NavigableString  # , Tag

from src.model_classes_parsing.base_classes_parsing import (
    BulletList,
    Code, 
    CodeMeta,
    RawDocument,
    DocumentExtract,
    Element,
    ElementMeta,
    Heading,
    HeadingMeta,
    Image,
    ImageMeta,
    LinkPreview,
    ListMeta,
    # Quote, 
    Word
    )

from src.model_tools_parsing.html_extractor import HTMLCleanExtractor
# from src.utils.html_helper import normalize_url
# from src.utils.path_helper import shorten_path
from src.utils.html_helper import read_html_file   # , save_text_file
from src.utils.dict_helper import save_dict

# from src.core.memory import RunContext

# @dataclass
class ApolloCleanExtractor(HTMLCleanExtractor):
    
    def extract(
            self, 
            f_path: str
            ) -> Result[DocumentExtract, str]:
        
        # data = self._get_apollo_data(f_text)
        f_text = read_html_file(f_path) 
        apollo_extract = self._get_apollo_data(f_text)\
                            .bind(self._extract_apollo_elements)
        # (data)
        if apollo_extract is None:
            return Failure("Error while parsing")

        if isinstance(apollo_extract, Result):
            apollo_extract = apollo_extract.unwrap()

        #########
        # TO DOs
        # - build text
        # - add_basic_metadata
        #########
        elements_clean = []
        for element in apollo_extract:
            # text_clean = self._clean_text(element.text)
            words_clean = []
            for word in re.findall(r"\S+|\n", 
                                   element.text):
                # element.text.split():   # text_clean.split():

                words_clean.append(
                                Word(
                                    text=self._clean_word_token(word),
                                    leaf_id=None
                                    )
                                )

            if (hasattr(element, "container_type") 
                and element.container_type != "code"):
                txt_clean = self._clean_text(element.text)
            
            elif (hasattr(element, "leaf_type") 
                and element.leaf_type != "code"):
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
            text_clean, elements_clean, RawDocument()
        )
        
        f_path = Path(f"{self.save_folder}/{self.save_name}")
        save_dict(data=doc_info.model_dump(
                            mode="json",
                            serialize_as_any=True,
                            ), 
                path=f_path)

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
        # self.logger.info("Created soup from '%s'", shorten_path(f_path))

        apollo_text = None

        for script in scripts_all:
            text = script.text      # .string
            
            if not text:
                continue
                
            if "window.__APOLLO_STATE__" in text:
                apollo_text = str(text)
                break
        
        if not apollo_text:
            return Failure("No APOLLO_STATE found")
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

            # print("[DEBUG] 'data[key]' keys:",
            #       data[ref].keys())
            para = data.get(ref)
            if not para:
                self.logger.warning("Missing paragraph ref: %s", ref)
                continue

            metadata = data[ref].get("metadata") or {}
            p_meta_ref  = metadata.get("__ref", "")

            text_type = para.get("type")
            p_text = para.get("text", "")
            p_markups = para.get("markups", [])
            
            if not text_type:
                self.logger.warning("Paragraph without type: %s", ref)
                continue

            if text_type.startswith("H"):
                level = text_type[1]

                current_headings[level] = p_text

                for k in list(current_headings):
                    if k > level:
                        del current_headings[k]

                extract.append(
                    Heading(
                        container_id=idx,
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
                    Paragraph(
                        container_id=idx,
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
                    BulletList(
                        container_id=idx,
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
                    Code(
                        container_id=idx,
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
                    BlockQuote(
                        container_id=idx,
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
                    LinkPreview(
                        container_id=idx,
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
                    Image(
                        container_id=idx,
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

