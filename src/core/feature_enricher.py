## feature_enricher.py
# import
# # import unicodedata
import re
import sys
import numpy as np
# # import pandas as pd
# # from sklearn.cluster import KMeans
# # from sklearn.metrics import silhouette_score
# # import subprocess
# # import gc
from typing import List, Dict, Callable, Optional # , , Any
from dataclasses import dataclass, field
# from tiktoken import encoding_for_model

from src.core.data_classes import (Word, Line, Document,
                                   Element) # BaseContainer

@dataclass
class FeatureEnricher:

    encoder: Callable = field(default=Callable) #  encoding_for_model
    page_height: int = field(default_factory=int)
    page_width: int = field(default_factory=int)
    text_prep_config: Dict = field(default_factory=dict)


    def enrich_pages(self, pages):
        from src.core.memory import session

        logger = session.logger
        logger.info("Start enriching pages")
        
        # if 
        for page_info in pages: 
            page_lines = page_info.get("lines") or page_info.get("segments")

            sizes = []
            fonts = []
            is_bold = []
            left_indent = []
            right_indent = []
            for p in page_lines:
                # print(f"type and length of 'p':\t{type(p)} | {len(p)}")
                if isinstance(p, dict):
                    sizes.extend(p["font_sizes"]) 
                    fonts.extend(p["fonts"])
                    is_bold.append(p["is_bold_rel"])
                
                    left_indent.append(p["x0_min"])
                    right_indent.append(p["x1_max"])

                elif isinstance(p, list):   
                    
                    for sub_page in p:
                        sizes.extend(sub_page["font_sizes"]) 
                        fonts.extend(sub_page["fonts"])
                        is_bold.append(sub_page["is_bold_rel"])
                       
                        left_indent.append(sub_page["x0_min"])
                        right_indent.append(sub_page["x1_max"])
                              
            page_info["median_font_size"] = np.median(sizes)
            page_info["font_size_max"] = max(sizes)
            page_info["fonts"] = list(set(fonts))
            page_info["is_bold_rel"] = sum(is_bold) / len(is_bold)
            # page_info["alpha_mean"] = np.mean([p["alpha_mean"] for p in page_lines])
            page_info["left_indent"] = min(left_indent)
            page_info["right_indent"] = max(right_indent)
    
        # font_flags
        
        # line_spacing_before
        # line_spacing_after
        # bullet_level

        return pages
    

    def enrich_blocks(self, blocks: List[dict]) -> List[dict]:
        from src.core.memory import session

        logger = session.logger

        for i, block in enumerate(blocks):
            text = block["text"]
            lines = block["lines"]  # , None) # or block.get("segments", None)

            if len(lines) == 0:
                logger.error("No 'lines' in lines.\nBLOCK:\n%s",
                             block["text"])
                #  Keys in 'block':\n%s",
                #              block.keys()
                # sys.exit()
                continue

            words = []      # seg["words"]
            for line in lines:
                word_info = line["words"]
                words.extend(word_info)

            blocks[i] = self._add_metadata(text, words, block)

        return blocks
    

    def enrich_lines(self, 
                     lines: List[Word], 
                     text=None) -> List[Line]:

        from src.core.memory import session

        logger = session.logger
        logger.info("Start enriching lines")

        # seg_final = []
        for i, words in enumerate(lines):
            if not words:
                continue
            
            if isinstance(words, list):
                text = " ".join([w.text for w in words])

                for w in words:
                    if "bold" in w.meta.font.lower():
                        w.meta.is_bold = True
                    else:
                        w.meta.is_bold = False
            
            elif isinstance(words, dict):
                text = words.get("text", None)
                words = words["words"]

            lines[i] = self._add_metadata(text, words, Line())

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
    

    def _add_basic_metadata(self, 
                            text: str,
                            word_info: List[Word],
                            info_obj: Optional[Document | Line | Element]):
        
        info_obj.elements = word_info
        info_obj.text = text

        info_obj.meta.n_words = len(text.split())
        info_obj.meta.n_chars = len(text)
        info_obj.meta.n_tokens = len(self.encoder.encode(text))
            
        info_obj.meta.has_hyphen = sum([bool(re.match(r".+[a-zäöüß]-\s+", w.text.lower())) 
                                 for w in word_info]) > 0
        info_obj.meta.end_hyphen = bool(re.match(r".+[a-zäöüß]-$", text.lower()))
        info_obj.meta.ends_sentence = bool(re.search(r"(?<!\b[A-Z0-9])[.!?](?:[\"')\]]+)?\s*$", text.strip()))
        info_obj.meta.has_punct = bool(re.search(r"(?<!\b[A-Z])[.!?:;](?:[\"')\]]+)?\s*", text.strip()))

        return info_obj
    

    def _add_metadata(self, 
                      text: str, 
                      word_info: List[Word], 
                      info_obj: Line):

        width_thresh = self.text_prep_config["width_thresh_rel"]
        # left_thresh = self.text_prep_config["left_right_thresh"]
        
        info_obj = self._add_basic_metadata(text, word_info, info_obj())
        
        info_obj.meta.x_start_min = min(w.meta.x_start for w in word_info)
        info_obj.meta.x_end_max = max(w.meta.x_end for w in word_info)

        info_obj.meta.y_start_min = min(w.meta.y_start for w in word_info)
        info_obj.meta.y_start_mean = np.mean([w.meta.y_start for w in word_info])
        info_obj.meta.y_end_max = max(w.meta.y_end for w in word_info)
            
        height = np.median([w.meta.y_end - w.meta.y_start for w in word_info])
        info_obj.meta.height = height
        info_obj.meta.rel_height = (info_obj.meta.y_start_min / self.page_height)
        info_obj.meta.width = info_obj.meta.x_end_max - info_obj.meta.x_start_min
        info_obj.meta.rel_width = (info_obj.meta.width / self.page_width)
        info_obj.meta.rel_start = info_obj.meta.x_start_min / self.page_width

        info_obj.meta.is_wide = info_obj.meta.width > (width_thresh * self.page_width)
        
        # typography 
        info_obj.meta.fonts = list(set(
                                w.meta.font for w in word_info
                                ))
        
        sizes = list(set([w.meta.size for w in word_info]))
        info_obj.meta.font_sizes = sizes
        info_obj.meta.font_size_mean = sum(sizes) / len(sizes)
        info_obj.meta.font_size_max = max(sizes)
        info_obj.meta.is_bold_rel = np.mean([w.meta.is_bold for w in word_info])
        info_obj.meta.alpha_mean = np.mean([w.meta.alpha for w in word_info])

        # info_obj["inter_word_gap"] = self._get_inter_word_gaps(word_info)

        return info_obj



    def _get_inter_word_gaps(self, word_info: List[Word]):

        i = 0

        word_gaps = []
        while i < len(word_info) - 1:

            curr_word = word_info[i]
            next_word = word_info[i+1]

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