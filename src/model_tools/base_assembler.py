## base_doc_assembler.py
# imports
# import logging
import re
from dataclasses import dataclass, field
from typing import Literal, List
from returns.result import Success, Result

from src.core.memory import RunContext
from src.model_parsing.base_classes_parsing import DocumentExtract
from src.utils.text_file_helper import save_text_file
# import src.utils.general_helper as gh


@dataclass
class BaseAssembler:
    # assemble_config: dict = field(default_factory=dict)
    infos: list = field(default_factory=list)
    # save_folder: str = field(default_factory=str)
    # save_name: str = field(default_factory=str)
    # logger = logging.getLogger(__name__)

    last_heading: list = field(default_factory=list)

    def __init__(self, run_context: RunContext):
        # from src.core.memory import session

        self.logger = run_context.logger

        self.save_folder = run_context.save_folder
        self.save_name = run_context.save_name

        self.assemble_config = run_context.run_settings.html

        self.assemble_elements = {
                "txt": run_context.general_settings.txt_elements,
                "md": run_context.general_settings.md_elements
                }
        self.save = self.assemble_config.save

        return


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

        assert self.assemble_config.assemble is not None

        if "md" in self.assemble_config.assemble:

            elements_sorted = self._filter_sort_elements(
                elements=extract.elements,
                text_type="md"
                )

            text_md = self._assemble_md_text(elements_sorted)
            
            # if "md" in self.assemble_config.save:
            save_text_file(
                        text_md, 
                        self.save_name, 
                        self.save_folder
                        )
                
        if "txt" in self.assemble_config.assemble:
            elements_sorted = self._filter_sort_elements(
                elements=extract.elements,
                text_type="txt"
                )
        
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

        # elements_filt = []                 
        # for ele in elements:
            # if (hasattr(ele, "container_type") 
            #     and ele.container_type in filter_elements:
                # elements_filt.append(ele)
            
            # elif (hasattr(ele, "leaf_type") 
            #     and ele.leaf_type in filter_elements):
            #     elements_filt.append(ele)

        elements_filt = [ele for ele in elements
                         if ele.container_type in filter_elements]
        # elements_sorted = 

        return sorted(
                elements_filt, 
                key=lambda e: e.container_id
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

            e_type = element.element_type or ""
            # assert e_type is not None
            
            c_type = element.cell_type or ""
            # assert c_type is not None

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

                lang = meta.language or "tba"

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

            e_type = element.element_type or ""
            # assert e_type is not None
            
            c_type = element.cell_type or ""
            # assert c_type is not None

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
