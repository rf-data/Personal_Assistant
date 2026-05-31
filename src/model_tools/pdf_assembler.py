## pdf_assembler.py
# imports
import re
from dataclasses import dataclass

# import os
from pathlib import Path

import pandas as pd

# from gmp_compliance.src.model_parsing.classes_html_parsing import CollectionItem, PDFPageExtract
from src.model_tools.base_assembler import BaseAssembler
from src.utils.dict_helper import save_dict
from src.utils.text_file_helper import save_text_file

# from src.utils.df_helper import save_df_to_parquet
# import src.utils.general_helper as gh


@dataclass
class PDFAssembler(BaseAssembler):


    def collect(self, page_info: PDFPageExtract) -> None:

        headings = page_info.headings
        block_texts = page_info.text_bodies

        # head_infos = list()

        self.logger.info(
            "Collecting from page %s (file=%s)", page_info.page_no, page_info.doc_name
        )
        heads_all = []
        for head_info in headings:
            meta = head_info.meta

            heads_all.append(
                {
                    "x0_min": meta.x_start_min,
                    "y0_min": meta.y_start_min,
                    "page": page_info.page_no,
                    "text_type": meta.line_type,
                    "text": head_info.text,
                }
            )

        blocks_all = []
        for block in block_texts:
            # head_info = list(head.values())

            # for h_info in head_info:
            meta = block.meta
            blocks_all.append(
                {
                    "x0_min": meta.x_start_min,
                    "y0_min": meta.y_start_min,
                    "page": page_info.page_no,
                    "text_type": "block",
                    "ends_sentence": meta.ends_sentence,
                    "text": block.text,
                }
            )

        # block_texts = page_info["text_bodies"]

        # head_foot = page_info["header_footer"]
        # foot_notes = page_info["text_bodies"]

        text_reb = self._rebuild_text(blocks_all, heads_all)

        self.infos.append(
            CollectionItem(
                doc_name=page_info.doc_name,
                # "timestamp": timestamp,
                # "gmp_part": gmp_part,
                # "chapter": chapter,
                page=page_info.page_no,
                text_bodies=blocks_all,
                headings=heads_all,
                text=text_reb["text"],
            )
        )

        return

    # def collect(self,
    #                 page_info: PDFPageExtract):

    #         (timestamp, _,
    #          _, gmp_part,
    #          chapter, _,
    #          page, _) = f_name.split("_")

    #         headings = page_info["headings"]
    #         block_texts = page_info["text_bodies"]

    #         # head_infos = list()

    #         heads = []
    #         for head_info in headings.values():
    #             for h_info in head_info:
    #                 heads.append({
    #                         "x0_min": h_info["x0_min"],
    #                         "y0_min": h_info["y0_min"],
    #                         "line_type": h_info["line_type"],
    #                         "text": h_info["text"]
    #                         })

    #         blocks = []
    #         for block in block_texts:
    #             # head_info = list(head.values())

    #             # for h_info in head_info:
    #             blocks.append({
    #                         "x0_min": block["x0_min"],
    #                         "y0_min": block["y0_min"],
    #                         "text": block["text"]
    #                         })

    #         # block_texts = page_info["text_bodies"]

    #         # head_foot = page_info["header_footer"]
    #         # foot_notes = page_info["text_bodies"]

    #         rebuild = self._rebuild_text(blocks, heads)

    #         self.infos.append({
    #                 "file_name": f_name,
    #                 "timestamp": timestamp,
    #                 "gmp_part": gmp_part,
    #                 "chapter": chapter,
    #                 "page": page,
    #                 "text_bodies": rebuild["blocks"],
    #                 "headings": heads,
    #                 "text": rebuild["text"]
    #                 })

    #         return

    def assemble_document(self) -> dict:
        # percents = self.assemble_config["percentiles"]

        f_infos = self.infos
        f_info_sorted = sorted(f_infos, key=lambda info: info.page)
        final = []
        pending = ""
        for idx, curr_info in enumerate(f_info_sorted):
            curr_text = curr_info.text
            # incomplete = False

            is_last = idx == len(f_info_sorted) - 1

            if pending:
                text_splits = re.split(
                    r"(?<!\b[A-Z0-9])[.!?](?:[\"')\]]+)?\s*", curr_text, maxsplit=1
                )

                if len(text_splits) < 2:
                    self.logger.warning(
                        "Current text was splitted into less than 2 parts:\tn=%s",
                        len(text_splits),
                    )

                if pending.endswith("-"):
                    prev_text = pending[:-1] + text_splits[0].lstrip() + "."

                else:
                    prev_text = (
                        pending.rstrip(".") + " " + text_splits[0].lstrip() + "."
                    )

                f_info_sorted[idx - 1].text_merged = prev_text

                curr_text = ".".join(text_splits[1:])
                pending = ""

            ends_sentence = re.search(
                r"(?<!\b[A-Z0-9])[.!?](?:[\"')\]]+)?\s*$", curr_text.strip()
            )

            if not ends_sentence and not is_last:
                # incomplete = True

                pending = curr_text

            final.append(curr_text)

        if pending:
            self.logger.info("Added info to 'final':\nTEXT:\t'%s'", pending)
            final.append(pending)

        if final:
            f_info_sorted[-1].text_merged = "\n\n".join(final)

        self.infos = f_info_sorted

        info_red = []
        page_info = {}
        for info in f_info_sorted:
            page = info.page
            page_info.setdefault(page, []).append(info)

            info_red.append(
                {
                    "page": page,
                    "text": info.text,
                    "text_merged": info.text_merged,
                    # k:v for k, v in info.items()
                    # if k in ["gmp_part", "chapter",
                    #          "page", "text",
                    #          "text_merged", "timestamp"]
                }
            )

        block_red = []
        for page_no, info_list in page_info.items():
            ends_sentence = True

            for info in info_list:
                # if str(ends_sentence) in ["True", "true"]:
                #     curr_text = t_body["text"]

                #     p_no = str(page_no - 1)
                #     prev_text = list(page_info[p_no].values())[-1].get("text")

                text_bodies = sorted(info.text_bodies, key=lambda t: t["y0_min"])

                idx = 0

                for idx, t_body in enumerate(text_bodies):
                    # t_body["text_id"] = idx
                    # block_dict =

                    # block_dict.update(
                    #         {"ends_sentence": })

                    block_red.append(
                        {
                            "page": page_no,
                            "block_id": idx,
                            "ends_sentence": t_body["ends_sentence"],
                            "text": t_body["text"],
                            "context_headings": t_body["context_heading"],
                        }
                    )

                    idx += 1

        df_info = pd.DataFrame(info_red)
        df_block = pd.DataFrame(block_red)

        self.logger.info("DF_INFO SHAPE = %s", df_info.shape)
        # self.logger.info("DF DESCRIPTION:\n%s",
        #             df_info.describe(
        #                         percentiles=percents
        #                         ))
        self.logger.info("DF_INFO HEAD:\n%s", df_info.head(5))

        self.logger.info("DF_BLOCK SHAPE = %s", df_block.shape)
        # self.logger.info("DF DESCRIPTION:\n%s",
        #             df_info.describe(
        #                         percentiles=percents
        #                         ))
        self.logger.info("DF_BLOCK HEAD:\n%s", df_block.head(5))

        if self.save and "info" in str(self.save):
            dict_path = f"{self.save_folder}/{self.save_name}_info"

            save_dict(page_info, Path(dict_path))

            # for name, df in [("df_info", df_info),
            #                 ("df_block", df_block)]:
            #     save_df_to_parquet(df=df,
            #                        f_name=f"{self.save_name}_{name}",
            #                        folder=self.save_folder)

        return {"info_dict": page_info, "info_df": df_info, "block_df": df_block}

    #             #

    def create_md_from_extract(self, extract: dict):

        # HEAD_DICT = {
        #     "1": "# "
        # }
        self.logger.info("Start md_file creation")

        text_bodies = []
        headings = []
        for _, info_all in extract.items():
            for info in info_all:
                heads = info.headings

                if isinstance(heads, list):
                    headings.extend(heads)

                else:
                    # if len(heads) >= 2:
                    # headings.extend(heads)
                    self.logger.info(
                        "'heading' in 'info' is not a 'list':\t", type(heads)
                    )

                t_bodies = info.text_bodies
                if isinstance(t_bodies, list):
                    headings.extend(t_bodies)

                else:
                    # if len(heads) >= 2:
                    # headings.extend(heads)
                    self.logger.info(
                        "'t_bodies' in 'info' is not a 'list':\t", type(t_bodies)
                    )
                # if len(t_bodies) == 1:
                #     text_bodies.append(t_bodies)

                # elif len(t_bodies) >= 2:
                #     text_bodies.extend(t_bodies)

        # text_bodies = self._check_multi_page_text(text_bodies)

        elements = text_bodies + headings

        text = ""
        for ele in sorted(
            elements, key=lambda e: (e.get("page"), e.get("y_start_min"))
        ):
            if ele.get("text_type") == "block":
                text += "\n"

            text += f"{ele.get('text')}\n"

        save_text_file(text, f"{self.save_name}", self.save_folder)

        return

        # if extract.get("doc_type") == "nb_json":
        #     # elements_sorted = _flat_sort_nb_elements(extract)
        #     # elements = extract.get("elements", {})
        #     elements_sorted = sorted(elements,
        #                             key=lambda e: e.get("meta").get("cell_id", 0))

        # else:
        #     elements_sorted = sorted(elements,
        #                             key=lambda e: e.get("meta").get("element_id", 0))

        # text_final = self._state_text_type(elements_sorted)

        # return text_final

    # def _check_multi_page_text(self, text_bodies):

    #     return

    def _rebuild_text(self, text_blocks: list[dict], headings: list[dict]) -> dict:

        # self.logger.info("Length of text_blocks | text_blocks[0]:\t%s  | %s",
        #                  len(text_blocks),
        #                  len(text_blocks[0])
        #                  )
        # self.logger("Keys of text_block[0][0]:\t%s",
        #             text_blocks[0][0].keys())

        text_blocks_sorted = sorted(text_blocks, key=lambda b: b["y0_min"])
        headings_sorted = sorted(headings, key=lambda h: h["y0_min"])
        # block["x0_min"],
        #                 block["y0_min"],
        #                 block["text"]
        text = []
        idx = 0
        relevant_heads = []
        head_lvl = None
        # for i in range(len(headings_sorted)):
        for curr_block in text_blocks_sorted:
            if (
                not headings_sorted
                or headings_sorted[0]["y0_min"] > curr_block["y0_min"]
            ):
                relevant_heads = self.last_heading

            # collect all headings before this block
            while (
                idx < len(headings_sorted)
                and headings_sorted[idx]["y0_min"] < curr_block["y0_min"]
            ):
                # y_curr:
                self.last_heading = []
                heading_lvl = headings_sorted[idx]["text_type"]
                if not head_lvl or heading_lvl.split("_")[-1] <= head_lvl:
                    relevant_heads = []

                head_text = headings_sorted[idx]["text"]
                text.append(head_text)
                relevant_heads.append(head_text)

                idx += 1

            text.append(curr_block["text"])
            curr_block["context_heading"] = relevant_heads.copy()

        # optional: remaining headings
        while idx < len(headings_sorted):
            head_text = headings_sorted[idx]["text"]

            text.append(head_text)
            self.last_heading.append(head_text)

            idx += 1

        return {"text": "\n\n".join(text), "blocks": text_blocks_sorted}
