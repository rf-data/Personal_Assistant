## document_assembler.py
# imports
import re
from dataclasses import dataclass, field

#
from pathlib import Path

import pandas as pd

# import src.utils.general_helper as gh


@dataclass
class DocumentAssembler:
    # gh.load_env_vars()
    # data_processed = parsing_env_vars("DATA")
    infos: list = field(default_factory=list)
    doc_name: str = field(default_factory=str)

    last_heading: list = field(default_factory=list)

    def __init__(self, run_context):
        self.logger = run_context.logger

        self.save_folder = run_context.save_folder
        self.assemble_config = run_context.run_settings

        return

    def collect(self, page_info, f_name):
        (timestamp, _, _, gmp_part, chapter, _, page, _) = f_name.split("_")

        headings = page_info["headings"]
        block_texts = page_info["text_bodies"]

        # head_infos = list()

        heads = []
        for head_info in headings.values():
            for h_info in head_info:
                heads.append(
                    {
                        "x0_min": h_info["x0_min"],
                        "y0_min": h_info["y0_min"],
                        "line_type": h_info["line_type"],
                        "text": h_info["text"],
                    }
                )

        blocks = []
        for block in block_texts:
            # head_info = list(head.values())

            # for h_info in head_info:
            blocks.append(
                {
                    "x0_min": block["x0_min"],
                    "y0_min": block["y0_min"],
                    "text": block["text"],
                }
            )

        # block_texts = page_info["text_bodies"]

        # head_foot = page_info["header_footer"]
        # foot_notes = page_info["text_bodies"]

        rebuild = self._rebuild_text(blocks, heads)

        self.infos.append(
            {
                "file_name": f_name,
                "timestamp": timestamp,
                "gmp_part": gmp_part,
                "chapter": chapter,
                "page": page,
                "text_bodies": rebuild["blocks"],
                "headings": heads,
                "text": rebuild["text"],
            }
        )

        return

    def assemble_document(self, save_file: bool = False) -> dict:
        # percents = self.assemble_config["percentiles"]

        f_infos = self.infos
        f_info_sorted = sorted(f_infos, key=lambda info: info["page"])
        final = []
        pending = ""
        for idx, curr_info in enumerate(f_info_sorted):
            curr_text = curr_info["text"]
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

                f_info_sorted[idx - 1]["text_merged"] = prev_text

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
            f_info_sorted[-1]["text_merged"] = "\n\n".join(final)

        self.infos = f_info_sorted

        info_red = []
        page_info = {}
        for info in f_info_sorted:
            page = info["page"]
            page_info.setdefault(page, []).append(info)

            info_red.append(
                {
                    k: v
                    for k, v in info.items()
                    if k
                    in [
                        "gmp_part",
                        "chapter",
                        "page",
                        "text",
                        "text_merged",
                        "timestamp",
                    ]
                }
            )

        block_red = []
        for _, info_list in page_info.items():
            for info in info_list:
                text_bodies = sorted(info["text_bodies"], key=lambda t: t["y0_min"])
                idx = 0
                for idx, t_body in enumerate(text_bodies):
                    # t_body["text_id"] = idx
                    block_dict = {
                        k: v
                        for k, v in info.items()
                        if k in ["gmp_part", "chapter", "page", "timestamp"]
                    }

                    block_dict.update(
                        {
                            "block_id": idx,
                            "text": t_body["text"],
                            "context_heading": t_body["context_heading"],
                        }
                    )

                    block_red.append(block_dict)

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

        if save_file:
            import src.utils.dict_helper as dh

            save_path = f"{self.save_folder}/{self.doc_name}"
            dh.save_dict(f_info_sorted, Path(save_path))

        return {"info_dict": f_info_sorted, "info_df": df_info, "block_df": df_block}
        #

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
                heading_lvl = headings_sorted[idx]["line_type"]
                if not head_lvl or heading_lvl.split("_")[-1] <= head_lvl:
                    relevant_heads = []

                head_text = headings_sorted[idx]["text"]
                text.append(head_text)
                relevant_heads.append(head_text)

                idx += 1

                # if idx > len(headings_sorted) - 1:
                #     break

            text.append(curr_block["text"])
            curr_block["context_heading"] = relevant_heads.copy()

            # self.logger.info("Keys of 'curr_block':\n%s",
            #                  curr_block.keys())

            # sys.exit()
            # idx = 0

        # optional: remaining headings
        while idx < len(headings_sorted):
            head_text = headings_sorted[idx]["text"]

            text.append(head_text)
            self.last_heading.append(head_text)

            idx += 1

        return {"text": "\n\n".join(text), "blocks": text_blocks_sorted}

        # prüfen ob unvollständig
        # prev_text = pending[0].strip()[:-1]

        #     else:
        #         prev_text = pending[0].strip() + " "

        #     prev_text = (prev_text
        #                 + text_splits[0].strip()
        #                 + ".")
        #     # f_info_sorted[idx-1]["text_merged"] = prev_text
        #     f_info_sorted[idx-1]["text_merged"] = prev_text

        #     curr_text = ".".join(text_splits)
        #     pending = []

        # end_hyphen = re.match(
        #                     r".+[a-zäöüß]-$",
        #                     curr_text.lower()
        #                     )

        # elif is_last:
        #     # if pending:
        #     pending.append(curr_text)
        #     final.append(pending)
        #     pending = []

        # else:
        #     final.append(curr_text)
        #     # pending = []
        # final
        #

        # if incomplete:
        #     # curr = ""
        #     prev_info = f_info_sorted[idx-1]

        # return

    """
    {
    "doc_id": "...",
    "blocks": [
        {
        "block_id": 1,
        "text": "...",
        "type": "paragraph",
        "table_id": null,
        "page": 1,
        "bbox": {...},
        "metadata": {
            "is_heading": false,
            "section": "Einführung"
        }
        }
    ]
    }
    """

    #         y_head = head["y0_min"]
    #         head_text = head["text"]

    #         if y_head < y_curr:
    #             pending.append(head_text)
    #             # continue

    #         else:
    #             #  y_curr < y_head
    #             #     and y_head < y_next):
    #             #     pending.append(text_curr)
    #             pending.append(text_curr)
    #             break

    #         # y_head = head["y0_min"]

    # return


#         all_text = f"""
# {"=" * 25}
# PAGE '{no_page}'
# {"=" * 25}

# {full_text}
# """


# page_info["text_bodies"] = b_text
#     page_info["header_footer"] = class_dict["header_footer"]
#     page_info["headings"] = class_dict["heading"]
#     page_info["foot_notes"] = class_dict["foot_notes"]
#     page_info["non_text_segments"] = class_dict["other"]

# self.text_bodies.append(all_text)
# # ext_complete.append(all_text)

# return


# def build(self, blocks):

#     results = []

#     for i, b in enumerate(blocks):
#         results.append({
#             "block_id": i,
#             "text": b["text"],
#             "type": b.get("type", "text"),
#             "table_id": b.get("table_id"),
#             "y": b.get("y0_mean"),
#             "x": b.get("x0_min"),
#         })

#     return results
