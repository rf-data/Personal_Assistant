## feature_enricher.py
# import
# # import unicodedata
import logging
import re
import sys
from collections.abc import Callable  # , , Any
from dataclasses import dataclass, field

# # import pandas as pd
# # from sklearn.cluster import KMeans
# # from sklearn.metrics import silhouette_score
# # import subprocess
# # import gc
import numpy as np

# from tiktoken import encoding_for_model
from src.model_classes_parsing.base_classes_parsing import (
    Line,
    LineGroup,
    LineSplit,
    PageExtract,
    PDFPageExtract,
    TextBlock,  # TextBlockMeta,
    Word,
    container_types,
    document_leafs,
    line_types,
)


@dataclass
class FeatureEnricher:
    
    # structure_dict = {
    #             "line" : Line,
    #              "line_group": LineGroup,
    #               "line_split": LineSplit if line.structure_object == "line" else LineSplit}

    structure_dict = {"line": Line, 
                      "line_group": LineGroup, 
                      "line_split": LineSplit}

    def __init__(self, 
                 parse_context,
                 page_height: float=0.0, 
                 page_width: float=0.0):
        self.page_height = page_height
        self.page_width = page_width
        
        self.logger = parse_context.logger

        self.encoder = parse_context.encoder

        self.text_prep_config = parse_context.parse_settings

        return
    

    def enrich_pages(
        self, 
        pages: list[PageExtract | PDFPageExtract]
    ) -> list[PageExtract | PDFPageExtract]:

        self.logger.info("Start enriching pages")

        # if
        for page_info in pages:
            page_lines = page_info.elements
            # get("lines") or page_info.get("segments")

            sizes = []
            fonts = []
            is_bold = []
            left_indent = []
            right_indent = []
            for line in page_lines:
                # print(f"type and length of 'p':\t{type(p)} | {len(p)}")
                # if isinstance(line, dict):
                sizes.extend(w.meta.size for w in line.elements)
                fonts.extend(w.meta.font for w in line.elements)
                is_bold.extend(w.meta.is_bold for w in line.elements)

                left_indent.append(line.meta.x_start_min)
                right_indent.append(line.meta.x_end_max)

                # elif isinstance(line, list):

                #     for sub_page in line:
                #         sizes.extend(sub_page["font_sizes"])
                #         fonts.extend(sub_page["fonts"])
                #         is_bold.append(sub_page["is_bold_rel"])

                #         left_indent.append(sub_page["x0_min"])
                #         right_indent.append(sub_page["x1_max"])

            page_info.meta.median_font_size = np.median(sizes)
            page_info.meta.max_font_size = max(sizes)
            page_info.meta.fonts = list(set(fonts))
            page_info.meta.is_bold_rel = sum(is_bold) / len(is_bold)
            # page_info["alpha_mean"] = np.mean([p["alpha_mean"] for p in page_lines])
            page_info.meta.left_indent = min(left_indent)
            page_info.meta.right_indent = max(right_indent)

        # font_flags

        # line_spacing_before
        # line_spacing_after
        # bullet_level

        return pages

    def enrich_blocks(self, 
                      blocks: list[TextBlock],
                      page_attributes: dict) -> list[TextBlock]:

        self.page_height = page_attributes.get("height")
        self.page_width = page_attributes.get("width")

        for idx, block in enumerate(blocks):
            text = block.text
            lines = block.elements  # , None) # or block.get("segments", None)

            if len(lines) == 0:
                self.logger.error("No 'lines' in lines.\nBLOCK:\n%s", text)
                #  Keys in 'block':\n%s",
                #              block.keys()
                # sys.exit()
                continue

            words = []  # seg["words"]
            for line in lines:
                words_info = line.elements
                words.extend(words_info)

            blocks[idx] = self._add_metadata(text, words, block)

        return blocks

    # def enrich_words(self,
    #                  words: List[Word],
    #                  ):
    #     for w in words:
    #         text = " ".join([word.text for word in line])

    #             for word in line:
    #                 if "bold" in word.meta.font.lower():
    #                     word.meta.is_bold = True
    #                 else:
    #                     word.meta.is_bold = False

    #     return

    def enrich_lines(
                self, 
                lines: list[line_types], 
                text=None
                ) -> list[LineSplit]:

        for idx, line in enumerate(lines):
            if not line:
                continue

            # if isinstance(line, list):
            #     words= line
            # else:
            words = line.elements

            # if isinstance(line, list):
            text = " ".join([w.text for w in words])

            for w in words:
                if "bold" in w.meta.font.lower():
                    w.meta.is_bold = True
                else:
                    w.meta.is_bold = False

            # elif isinstance(line, dict):
            #     text = words.get("text", None)
            #     words = words["words"]

            s_obj = self.structure_dict.get(line.container_type)

            if s_obj is None:
                self.logger.error(
                    "Meta_data cannnot be added to '%s' since its container_type '%s'",
                    "is unknown or cannot be transformed.",
                    line.text,
                    line.container_type,
                )
                continue

            lines[idx] = self._add_metadata(text, words, s_obj())

            # print(f"lin (len={len(words)}):\n", words)
            # if lin[0].get("words", None):
            #     lin_sorted = sorted(lin,
            #                         key=lambda w: w["x0"])
            #     text = " ".join([w["text"] for w in lin_sorted])

            # else:
            #     text= lin["text"]

            # print("[DEBUG] 'text' in enrich_lines():\t", text)
            # words = lin["words"]
            # lin_sort = sorted(seg["words"], key=lambda w: w["x0"])

            # text = " ".join(w["text"] for w in seg_sort)
            # text = lin["text"]

        return lines

    # Document|Line|LineSplit|Element
    def _add_basic_metadata(
        self, 
        text: str, 
        leaf_info: list[document_leafs], 
        info_obj: container_types | None
    ):



        if info_obj is None:
            self.logger.info(
                "No info_obj provided or provided info_obj is of type 'None'."
            )

            # return None
            sys.exit()

        if not hasattr(info_obj, "elements"):
            self.logger.info(
                "Provided info_obj of type '%s' has no attribute 'elements'. --> SKIP",
                type(info_obj),
            )
            # .container_type or info_obj.leaf_type

            return info_obj

        # self.logger.info("Starting adding 'basic_metadata' on text (len=%s)," \
        #                  "list of subunit_infos (len=%s) and " \
        #                  "unit_info (type=%s)",
        #                  len(text),
        #                  len(word_info),
        #                  type(info_obj))

        info_obj.elements = leaf_info
        info_obj.text = text

        info_obj.meta.n_words = len(text.split())
        info_obj.meta.n_chars = len(text)
        info_obj.meta.n_tokens = len(self.encoder.encode(text))

        info_obj.meta.has_hyphen = (
            sum([bool(re.match(r".+[a-zäöüß]-\s+", l.text.lower())) for l in leaf_info])
            > 0
        )
        info_obj.meta.end_hyphen = bool(re.match(r".+[a-zäöüß]-$", text.lower()))
        info_obj.meta.ends_sentence = bool(
            re.search(r"(?<!\b[A-Z0-9])[.!?](?:[\"')\]]+)?\s*$", text.strip())
        )
        info_obj.meta.has_punct = bool(
            re.search(r"(?<!\b[A-Z])[.!?:;](?:[\"')\]]+)?\s*", text.strip())
        )

        return info_obj

    def _add_metadata(
        self, 
        text: str, 
        leaf_info: list[document_leafs], 
        info_obj: Line | LineSplit | TextBlock
    ):

        # width_thresh = self.text_prep_config["width_thresh_rel"]
        # left_indent =
        # left_thresh = self.text_prep_config["left_right_thresh"]

        assert float(self.page_height) is not 0.0
        assert float(self.page_width) is not 0.0

        info_obj = self._add_basic_metadata(text, 
                                            leaf_info, 
                                            info_obj)

        info_obj.meta.x_start_min = min(l.meta.x_start for l in leaf_info)
        info_obj.meta.x_end_max = max(l.meta.x_end for l in leaf_info)

        info_obj.meta.y_start_min = min(l.meta.y_start for l in leaf_info)
        info_obj.meta.y_start_mean = np.mean([l.meta.y_start for l in leaf_info])
        info_obj.meta.y_end_max = max(l.meta.y_end for l in leaf_info)

        height = np.median([l.meta.y_end - l.meta.y_start for l in leaf_info])
        info_obj.meta.height = height
        info_obj.meta.rel_height = info_obj.meta.y_start_min / self.page_height
        info_obj.meta.width = info_obj.meta.x_end_max - info_obj.meta.x_start_min
        info_obj.meta.rel_width = info_obj.meta.width / self.page_width
        info_obj.meta.rel_start = info_obj.meta.x_start_min / self.page_width

        # info_obj.meta.is_wide = info_obj.meta.width > (width_thresh * self.page_width)

        # typography
        info_obj.meta.fonts = list(set(w.meta.font for w in leaf_info))

        sizes = list(set([w.meta.size for w in leaf_info]))
        info_obj.meta.font_sizes = sizes
        info_obj.meta.font_size_mean = sum(sizes) / len(sizes)
        info_obj.meta.font_size_max = max(sizes)
        info_obj.meta.is_bold_rel = np.mean([w.meta.is_bold for w in leaf_info])
        info_obj.meta.alpha_mean = np.mean([w.meta.alpha for w in leaf_info])

        # info_obj["inter_word_gap"] = self._get_inter_word_gaps(leaf_info)

        return info_obj

    def _get_inter_word_gaps(self, leaf_info: list[Word]):

        i = 0

        word_gaps = []
        while i < len(word_info) - 1:
            curr_word = word_info[i]
            next_word = word_info[i + 1]

            word_gaps.append(abs(curr_word.meta.x_end - next_word.meta.x_start))

            # for i, word in enumerate(word_info):

        return word_gaps

    # def enrich_raw_lines(
    #                     self,
    #                     lines: List[dict]
    #                     ):

    #     # lines_new = []

    #     for i, lin in enumerate(lines):
    #         if not lin:
    #             continue

    #         text= lin["text"]
    #         words = text.split(" ")

    #         lines[i].update({
    #                     "words": words,
    #                     "n_words": len(words),
    #                     "n_chars": len(text),
    #                     "n_tokens": len(self.encoder.encode(text)),
    #                     "line_height": abs(lin["y0"] - lin["y1"]),
    #                     "x0_min": lin["x0"],
    #                     "y0_min": lin["y0"],
    #                     "y0_mean": lin["y0"],
    #                     "x1_max": lin["x1"],
    #                     "y1_max": lin["y1"],
    #                     "has_hyphen": sum([bool(re.match(r".+[a-zäöüß]-\s+", w["text"].lower()))
    #                              for w in words]) > 0,
    #                     "rel_start": lin["x0"] / self.page_width,

    #         })

    #     info_dict["line_height"] = block_height
    #     info_dict["rel_height"] = (info_dict["y0_min"] / self.page_height)
    #     info_dict["line_width"] = info_dict["x1_max"] - info_dict["x0_min"]
    #     info_dict["rel_width"] = (info_dict["line_width"] / self.page_width)

    #     info_dict["starts_low"] = text[0].islower()
    #     info_dict["starts_digit"] = text[0].isdigit()
    #     info_dict["is_upper"] = text.isupper()
    #     info_dict["is_short"] = info_dict["n_words"] < 10
    #     info_dict["is_wide"] = info_dict["line_width"] > (width_thresh * self.page_width)
    #     info_dict["left_aligned"] = info_dict["x0_min"] < (left_thresh * self.page_width)
    #     info_dict["is_long"] = info_dict["n_words"] > 20

    #     info_dict["end_hyphen"] = bool(re.match(r".+[a-zäöüß]-$", text.lower()))
    #     info_dict["ends_sentence"] = bool(re.search(r"(?<!\b[A-Z])[.!?;](?:[\"')\]]+)?\s*$", text.strip())),
    #     info_dict["has_punct"] = bool(re.search(r"(?<!\b[A-Z])[.!?;](?:[\"')\]]+)?\s*", text.strip()))

    # return lines

    # lin["n_words"] = len(text.split())
    # lin["n_chars"] = len(text)
    # lin["n_tokens"] = len(self.encoder.encode(text)),

    # print("[DEBUG] words:\n", words)

    # if len(words) == 1:
    #     # words = words[0]
    #     print("[DEBUG] words:\n", words)
    # # else:
    # #     print("[DEBUG] words (len > 1):\n", words)

    # line_height = np.median([w["y1"] - w["y0"] for w in words])
    # lin["x0_min"] = min(w["x0"] for w in words)
    # lin["y0_min"] = min(w["y0"] for w in words)
    # lin["y0_all"] = [w["y0"] for w in words]
    # lin["y0_mean"] = np.mean(lin["y0_all"])
    # lin["x1_max"] = max(w["x1"] for w in words)
    # lin["y1_max"] = max(w["y1"] for w in words)
    # lin["has_hyphen"] = sum([bool(re.match(r".+[a-zäöüß]-\s+", w["text"].lower()))
    #                      for w in words]) > 0

    # lin["rel_start"] = lin["x0_min"] / self.page_width
    # lin["line_height"] = line_height
    # lin["rel_height"] = (lin["y0_min"] / self.page_height)
    # lin["line_width"] = lin["x1_max"] - lin["x0_min"]
    # lin["rel_width"] = (lin["line_width"] / self.page_width)

    # lin["starts_low"] = text[0].islower()
    # lin["starts_digit"] = text[0].isdigit()
    # lin["is_upper"] = text.isupper()
    # lin["is_short"] = lin["n_words"] < 10
    # lin["is_wide"] = lin["line_width"] > (width_tol * self.page_width)
    # lin["left_aligned"] = lin["x0_min"] < min(start_tol,
    #                                           start_tol_rel * self.page_width)
    # lin["is_long"] = lin["n_words"] > 20

    # lin["end_hyphen"] = bool(re.match(r".+[a-zäöüß]-$", text.lower()))
    # lin["ends_sentence"] = bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*$", text.strip()))
    # lin["has_punct"] = bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*", text.strip()))

    # return lines
