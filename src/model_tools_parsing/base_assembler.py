## base_doc_assembler.py
# imports
import logging
import re
from dataclasses import dataclass, field
from typing import Literal, List, Any, Dict
from returns.result import Success, Result

from src.core.memory import ParseContext
from src.model_classes_parsing.base_classes_parsing import DocumentExtract
from src.utils.text_file_helper import save_text_file
# import src.utils.general_helper as gh
from src.utils.general_helper import get_file_config


@dataclass
class BaseAssembler:
    parse_context: Any 
    text_type: str = field(init=False)

    logger: logging.Logger = field(init=False)
    infos: list = field(default_factory=list)
    
    assemble_elements: Dict = field(default_factory=dict)
    last_heading: list = field(default_factory=list)
    


    def __post_init__(self):        # , parse_context: ParseContext
        # from src.core.memory import session

        self.logger = self.parse_context.logger
        self.text_type = self.parse_context.text_type

        self.save_folder = self.parse_context.save_folder
        self.save_name = self.parse_context.save_name
        
        self.general_config = get_file_config(
                                    self.parse_context.general_settings,
                                    self.text_type
                                    )

        self.assemble_config = get_file_config(
                                    self.parse_context.parse_settings,
                                    self.text_type
                                    )
        
        self.assemble_elements = {
                "txt": get_file_config(
                                self.parse_context.general_settings,
                                "txt_elements"
                                ),
                # self.parse_context.general_settings.txt_elements,
                "md": get_file_config(
                                self.parse_context.general_settings,
                                "md_elements"
                                )
                # self.parse_context.general_settings.md_elements
                }
        
        self.save = self.assemble_config.save

        self.setup()

        return 


    def setup(self):
        """Hook für Subklassen."""
        pass

        
        # print("'self.save':", self.save)
        
        # return


    def collect(self):

        return


    def render_text_file(
                    self, 
                    extract: DocumentExtract
                    ) -> Result[str, None]:
        """
        für:
        LLM
        Zusammenfassungen
        Export
        """
        # HEAD_DICT = {
        #     "1": "# "
        # }
        if isinstance(extract, Result):
            extract = extract.unwrap()

        # if extract.doc_type == "nb_json":
        #     # elements_sorted = _flat_sort_nb_elements(extract)
        #     # elements = extract.get("elements", {})
        #     elements_sorted = sorted(
        #         elements, key=lambda e: e.container_id
        #     )

        # else:
        #     elements_sorted = sorted(
        #         elements, key=lambda e: e.container_id
        #     )

        # assert self.assemble_config.save is not None

        if self.save and "md" in self.save:

            elements_sorted = self._filter_sort_elements(
                elements=extract.elements,
                text_type="md"
                )

            # print("[DEBUG 'MD'] elements_sorted (dtype | len_elements | text):\n%s (all) %s ([0]) | %s | %s",
            #       type(elements_sorted),
            #       type(elements_sorted[0]),
            #       len(elements_sorted[0].elements),
            #       elements_sorted[0].text)
            
            text_md = self._assemble_md_text(elements_sorted)
            
            # if "md" in self.assemble_config.save:
            save_text_file(
                        text_md, 
                        self.save_name, 
                        self.save_folder
                        )
                
        if self.save and "txt" in self.save:
            elements_sorted = self._filter_sort_elements(
                elements=extract.elements,
                text_type="txt"
                )

            # print("[DEBUG 'TXT'] elements_sorted (dtype | len_elements | text):\n%s (all) %s ([0]) | %s | %s",
            #       type(elements_sorted),
            #       type(elements_sorted[0]),
            #       len(elements_sorted[0].elements),
            #       elements_sorted[0].text)
            
            text_txt = self._assemble_plain_text(elements_sorted)

            save_text_file(
                        text_txt, 
                        self.save_name, 
                        self.save_folder,
                        suffix="txt"
                        )

        
        return Success("Text rendering successful.")


    def _filter_sort_elements(
                        self, 
                        elements: List,
                        text_type: Literal["txt", "md"]
                        ) -> List: 
        # ="md"
        filter_elements = self.assemble_elements[text_type]
        # assert filter_elements is not None
        # print("[DEBUG 'filter_sort()'] length 'elements': %s",
        #       len(elements))
        
        # print("[DEBUG 'filter_sort()'] 'filzter_elements': %s",
        #       filter_elements)
        # elements_filt = []                 
        # for ele in elements:
            # if (hasattr(ele, "container_type") 
            #     and ele.container_type in filter_elements:
                # elements_filt.append(ele)
            
            # elif (hasattr(ele, "leaf_type") 
            #     and ele.leaf_type in filter_elements):
            #     elements_filt.append(ele)
        
        if (filter_elements is not None 
            and len(filter_elements) > 0): 
            elements_filt = [ele for ele in elements
                            if ele.container_type in filter_elements]
        
        else:
            elements_filt = elements
        # elements_sorted = 

        # print("[DEBUG 'filter_sort()'] length 'elements_filt': %s",
        #       len(elements_filt))
        return sorted(
                elements_filt, 
                key=lambda e: e.container_id 
                if e.container_id is not None else 10**12
                )


    def _assemble_md_text(
                        self, 
                        elements
                        ) -> str: #, None]:

        text_final = []
        for element in elements:
            # if element["text"] in ["", "\n \n"]:
            #     continue

            # logger.info("DataType 'element' | 'keys' in 'meta':\t%s | %s",
            #             type(element),
            #             element.get("meta").keys())

            text = element.text
            
            if not text:
                continue

            meta = element.meta
            assert meta is not None

            e_type = (
                    getattr(element, "container_type", None) 
                    or getattr(element, "element_type", None) 
                    or getattr(element, "leaf_type", None)
                    or "")
            assert e_type is not None
            
            c_type = getattr(element, "cell_type", None) or ""
            assert c_type is not None

            if e_type == "heading":
                level = meta.level or 1
                text_final.append(f"{'#' * level} {text}\n")

            elif e_type == "paragraph":
                if text.endswith(":"):
                    text_final.append(text)

                elif ":" in text:
                    text = re.sub(
                        r"(?<!\n)\s+(-\s)",
                        #  [a-zA-Z0-9\)])[:|\n]\s+(-\s)",
                        r"\n\1",
                        text,
                    )
                    text_final.append(f"{text}\n")

                else:
                    text_final.append(f"{text}\n")

            elif e_type == "bullets_list":
                lines = text.split("\n")

                # for text in text_splits:
                #     text = "- " + text + "\n"

                bullet_text = "\n".join(
                    [line.strip() for line in lines 
                     if line.strip()]
                )
                # " ".join(text_splits)

                text_final.append(f"{bullet_text}\n")

            elif e_type == "code" or c_type == "code_block":
                # text_splits = element["text"].split("\n")

                # for text in text_splits:
                #     text = "- " + text + "\n"

                # text_fixed = "".join(text_splits)

                # text_splits = text.split(":\n")
                # text = ":\n\t".join(text_splits)

                lang = meta.language or "python"

                text_final.append(f"```{lang}\n{text}\n```\n")

            elif e_type is None and c_type is not None:
                sub_elements = element.elements # {}
                sub_elements_sorted = sorted(
                    sub_elements, key=lambda e: e.meta.element_id or 0
                )

                sub_e_text = self._assemble_md_text(sub_elements_sorted)
                text_final.append(sub_e_text)

            else:
                text_final.append(f"{text}\n")

        return "\n".join(text_final)        # Success()


    def _assemble_plain_text(
                        self, 
                        elements
                        ) -> str: # Result[, None]:

        text_final = ""
        for element in elements:

            text = element.text
            
            if not text:
                continue

            meta = element.meta
            assert meta is not None

            e_type = (
                    getattr(element, "container_type", None) 
                    or getattr(element, "element_type", None) 
                    or getattr(element, "leaf_type", None)
                    or "")
            assert e_type is not None
            
            c_type = getattr(element, "cell_type", None) or ""
            assert c_type is not None

            if e_type == "paragraph":
                if text.endswith(":"):
                    text_final += f"{text}\n\n"

                elif ":" in text:
                    text = re.sub(
                        r"(?<!\n)\s+(-\s)",
                        #  [a-zA-Z0-9\)])[:|\n]\s+(-\s)",
                        r"\n\1",
                        text,
                    )
                    text_final += f"{text}\n"

                else:
                    text_final += f"{text}\n"

            elif e_type == "bullets_list":
                lines = text.split("\n")

                # for text in text_splits:
                #     text = "- " + text + "\n"

                bullet_text = "\n".join(
                    [line.strip() for line in lines 
                     if line.strip()]
                )
                # " ".join(text_splits)

                text_final += f"{bullet_text}\n"


            elif e_type == "code" or c_type == "code_block":

                lang = meta.language or "tba"

                text_final += f"```{lang}\n{text}\n```\n"


            elif e_type is None and c_type is not None:
                sub_elements = element.elements # {}
                sub_elements_sorted = sorted(
                    sub_elements, key=lambda e: e.meta.element_id or 0
                )

                sub_e_text = self._assemble_plain_text(sub_elements_sorted)
                
                assert sub_e_text is not None
                text_final += sub_e_text

            else:
                text_final += f"{text}\n"


        return text_final       # Success()
