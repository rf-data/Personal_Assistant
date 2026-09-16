## base_doc_assembler.py
# imports
import re
from dataclasses import dataclass

#
# import src.utils.general_helper as gh
from src.model_parsing.base_assembler import BaseAssembler


@dataclass
class WikiPageAssembler(BaseAssembler):
    # assemble_config: Dict = field(default_factory=dict)
    # infos: List = field(default_factory=list)
    # doc_name: str = field(default_factory=str)
    # save_folder: str = field(default_factory=str)
    # logger = logging.getLogger(__name__)

    # last_heading: List = field(default_factory=list)

    # def collect(self):

    #     return

    def create_md_from_extract(self, extract: dict):
        # HEAD_DICT = {
        #     "1": "# "
        # }
        elements = extract.get("elements", {})

        if extract.get("doc_type") == "nb_json":
            # elements_sorted = _flat_sort_nb_elements(extract)
            # elements = extract.get("elements", {})
            elements_sorted = sorted(
                elements, key=lambda e: e.get("meta").get("cell_id", 0)
            )

        else:
            elements_sorted = sorted(
                elements, key=lambda e: e.get("meta").get("element_id", 0)
            )

        text_final = self._state_text_type(elements_sorted)

        return text_final

    def _render_markdown(self, node):
        if isinstance(node, TextNode):
            return node.text

        elif isinstance(node, LinkNode):
            return f"[{node.text}]({node.href})"

    def _state_text_type(self, elements):
        text_final = []
        for element in elements:
            # if element["text"] in ["", "\n \n"]:
            #     continue

            # logger.info("DataType 'element' | 'keys' in 'meta':\t%s | %s",
            #             type(element),
            #             element.get("meta").keys())

            text = element.get("text", "")  # .strip()

            if not text:
                continue

            meta = element.get("meta", {})
            e_type = meta.get("element_type", None)
            c_type = meta.get("cell_type", None)

            if e_type == "heading":
                level = int(meta.get("level", 1))
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
                    [line.strip() for line in lines if line.strip()]
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

                lang = meta.get("language", "tba")

                text_final.append(f"```{lang}\n{text}\n```\n")

            elif e_type is None and c_type is not None:
                sub_elements = element.get("elements", {})
                sub_elements_sorted = sorted(
                    sub_elements, key=lambda e: e.get("meta").get("element_id", 0)
                )

                sub_e_text = self._state_text_type(sub_elements_sorted)
                text_final.append(sub_e_text)

            else:
                text_final.append(f"{text}\n")

        return "\n".join(text_final)
