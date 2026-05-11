## text_classifier.py
# import
import re
# from collections import defaultdict
# from typing import Dict     # , List, Any
from dataclasses import dataclass       # , field
# import pprint
# import sys
# import logging

from src.core.memory import session
from src.core.data_classes import DocumentExtract
from src.core.base_classifier import BaseClassifier


@dataclass
class TXTClassifier(BaseClassifier):

    def classify_lines(self, 
                       text_extract: DocumentExtract
                       ) -> DocumentExtract: 

        self.logger = session.logger

        for block in text_extract.elements:
            for line in block.elements:

                if self._is_bullet(line):
                    line.line_type = "bullet"
                
                elif self._is_heading(line):
                    line.line_type = "heading"

                elif self._is_paragraph(line):
                    line.line_type = "text_body"

                else:
                    self.logger.info("Line does not fit any known line type: %s",
                                line)
                    line.line_type = "other"

        # line < block < 
        return  text_extract


    def _is_bullet(self, line) -> bool:

        if re.match(r"^[\*\-\•]\s*", line):
            return True
        
        if line[0] in self.bullets:
            return True
        
        return False
    

    def _is_heading(self, line) -> bool:

        # if :
        #     return True
        
        if (line.meta.n_words < 10 
            and not line.meta.ends_sentence):
            return True

        return False
    

    def _is_paragraph(self, line):

        if (line.meta.n_words >= 10 
            and (line.meta.ends_sentence
                 or re.match(r"\:$", line)
                 )
            ):
            return True
        
        return False
    
# @dataclass
# class PDFClassifier:
    
#     page_attributes: Dict[str, Any] = field(default_factory=dict)
#     classify_config: Dict = field(default_factory=dict)

#     def classify_line(self, lines, page_attributes):

#         self.page_attributes.update(page_attributes)
#         # head_foot, other = self._separate_header_footer(lines)
#         # text_rows, non_text_rows = self._filter_text(segments)
#         (text, 
#          heading, 
#          foot_note,
#          header_footer, 
#          other) = self._differentiate_text(lines)
        
#         heading = self._subdivide_heading(heading)

#         return {
#             "header_footer": header_footer, 
#             "foot_note": foot_note, 
#             "text": text, 
#             "heading": heading, 
#             "other": other
#             }

#     # def classify_paragraph(self):

#     #     return 
    
#     # def detect_table(self):

#     #     return 
    
#     def _is_header_footer(self, line):
#         up_down_edge = self.classify_config["up_down_thresh"]
        
#         # header_footer = []
#         # other = []
        
#         if (
#             line["rel_height"] < up_down_edge 
#             or line["rel_height"] > 1 - up_down_edge 
#             ) and (
#             line["n_chars"] < 100 
#             or line["n_words"] < 20
#             ):
#             return True
         
            
#             # else:
#             #     other.append(l)

#         return False # header_footer, other
    

#     def _heading_score(self, line):
#         median_size = self.page_attributes["median_size"]
        
#         heading_score = 0

#         font_sizes = line["font_size_mean"]
#         if font_sizes > median_size:        # (len(font_sizes) == 1 and 
#             heading_score += 2
#         # else: 
#         #     logger.warning("Line has more than one font size:\t", font_sizes)

#         if line["is_bold_rel"] > 0.5:
#             heading_score += 2

#         if line["n_words"] < 10:
#             heading_score += 1

#             # if line["has_numbering"]:
#             #     heading_score += 1

#             # if line["large_top_gap"]:
#             #     heading_score += 1
            
#         # line["heading_score"] = heading_score

#         return heading_score
    
#     def _subdivide_heading(self, heading):
#         logger = session.logger

#         font_span = defaultdict(list)

#         for head in heading:
#             font_size = int(head["font_size_mean"] // 1)
#             font_span[font_size].append(head)

#         span_sorted = sorted(font_span.keys(), reverse=True)

#         idx = 1
#         for size in span_sorted:
#             heads = font_span[size]

#             logger.info("HEADING: size=%s  |  count=%s", 
#                         size, 
#                         len(heads))
            
#             for h in heads:
#                 h["line_type"] += f"_lvl_{idx}"

#                 logger.info("line_type = %s\n'%s'",
#                             h["line_type"],
#                             h["text"])
            
#             idx += 1
            

#         return font_span
    

#     def _is_foot_note(self, line, prev_type):
#         logger = session.logger 

#         foot_note_thresh = self.classify_config["foot_note_thresh"]

#         median_size = self.page_attributes["median_size"]
#         page_height = self.page_attributes["height"]

#         logger.info("Median font size = %s  | page:height = %s",
#                     round(median_size, 2), 
#                     page_height)
#         font_size = line.get("font_size_mean", None)
#         text = line.get("text", "").strip()

#         if font_size is None:
#             return False 
        
#         score = 0

#         if line["y0_min"] > 0.8 * page_height:
#             score += 1

#         if font_size < 0.8 * median_size:
#             score += 1

#         if re.match(r"^\s*(\d+|\*|†)", text):
#             score += 2    
        
#         if prev_type == "foot_note":
#             score += 2 

#         # if line["n_words"] < 15:
#         #     score += 1
             
#         # if len(line["font_sizes"]) != 1:
#         #     logger = session.logger
#         #     logger.info("Line has more than one or no font_size.\n%s",
#         #                 line)

#         return score >= foot_note_thresh


#     def _is_column(self, lines):

#         inter_word_gap = ""

#         return 

#     def _is_table(self, lines):


#         return 

#     def _differentiate_text(self, lines):
#         # setup logger
#         logger = session.logger

#         left_indent = self.page_attributes["left_indent"]

#         start_tol = self.classify_config["start_tol"]
#         y_tol = self.classify_config["y_gap_line"]
#         head_thresh = self.classify_config["heading_threshold"]
        
#         bullet_start_x = 0
#         bullet_start_y = 0
#         # bullet_lines = []
#         # body_text_lines = []
#         text_lines = []
#         heading = []
#         header_footer = []
#         foot_notes = []
#         no_text = []

#         lines_sorted = sorted(
#                             lines,
#                             key=lambda l: l["y0_mean"]
#                             )
                            
#         for i, line in enumerate(lines_sorted):
#             line["line_type"] = "tba"
#             text = line["text"]

#             prev_type = lines_sorted[i-1]["line_type"] if i > 0 else "tba"
#             # if (i >0 
#             #     and 
#             #     segments[i-1]["line_type"] not in [
#             #                                 "lvl_1_bullet",
#             #                                 "lvl_2_bullet"
#             #                                 ]):
#             #     text_lines.append(bullet_lines)
#             #     bullet_lines = []                
            
#             if (re.match(r"^(\d+\.\d+)", text)
#                 or re.match(r"^(\•\d+)", text)
#                 or re.match(r"^(\([ivx]+\))", text)):
#                 # or ):
#                 if (bullet_start_x == 0 
#                     or line["x0_min"] < bullet_start_x):
#                     line["line_type"] = "lvl_1_bullet"

#                 else: 
#                     line["line_type"] = "lvl_2_bullet"

#                 text_lines.append(line)

#                 bullet_start_x = line["x0_min"]
#                 bullet_start_y = line["y0_mean"]

#             elif (
#                 i > 0
#                 and prev_type in [
#                                 "lvl_1_bullet",
#                                 "lvl_2_bullet"
#                                 ]
#                 and line["x0_min"] > bullet_start_x
#                 and abs(line["y0_mean"] - bullet_start_y) < y_tol
#             ):
            
#                 if (re.match(r"^(\d+\.\d+)", text)
#                     or re.match(r"^(\•\d+)", text)
#                     or re.match(r"^(\([ivx]+\))", text)):
#                     # new_text = " ".join([b["text"] for b in bullet_lines])
#                     # for line in bullet
#                     # new_lines

#                     # bullet_lines = [line]
#                     line["line_type"] = "lvl_2_bullet"
#                     bullet_start_x, bullet_start_y = line["x0_min"], line["y0_mean"]

#                 else:
#                     line["line_type"] = "lvl_1_bullet"
#                     bullet_start_y = line["y0_mean"]

#                 text_lines.append(line)

#             elif self._is_foot_note(line, prev_type):
#                 line["line_type"] = "foot_note"
#                 foot_notes.append(line)
#                 logger.info("FOOT_NOTE:\t%s", line["text"])

#             elif self._heading_score(line) >= head_thresh:
#                 # ((line["n_words"] < 6 
#                 #         or line["n_chars"] < 60)
#                 #         and line["line_width"]):
                
#                 line["line_type"] = "heading"
#                 logger.info("HEADING:\t%s", line["text"])
#                 heading.append(line)
            
#             elif line["ends_sentence"]:
#                 line["line_type"] = "body_text"
#                 text_lines.append(line)

#             elif self._is_header_footer(line):
#                 line["line_type"] = "header_footer"
#                 header_footer.append(line)

#             elif abs(line["x0_min"] - left_indent) < start_tol:      # "left_aligned"
                
#                 if line["is_wide"]:
#                     line["line_type"] = "body_text"
#                     text_lines.append(line)
            
#                 elif (
#                     i > 0
#                     and prev_type == "body_text"
#                     and (line["text"][0].islower()
#                         or line["text"][0].isdigit()
#                         or line["ends_sentence"])  
#                     ):
#                     gap = abs(line["y0_min"] - lines_sorted[i-1]["y0_min"])

#                     if line["ends_sentence"]:
#                         line["line_type"] = "body_text"
#                         # body_text_lines.append(line)
#                         text_lines.append(line)

#                     elif gap < y_tol:
#                         line["line_type"] = "body_text"
#                         text_lines.append(line)

#                 elif self._heading_score(line) >= head_thresh:
#                     # ((line["n_words"] < 6 
#                     #     or line["n_chars"] < 60)
#                     #     and line["line_width"]):
#                     line["line_type"] = "heading"
#                     heading.append(line)
#                     logger.info("HEADING:\t%s", line["text"])
                 
#                 else:
#                     no_text.append(line)

#             else:
#                 no_text.append(line)

#         # if bullet_lines:
#         #     text_lines.append(bullet_lines)
        
#         # if body_text_lines:
#         #     text_lines.append(body_text_lines)

#         logger.info("Splitting lines (n=%s) into text (n=%s), header_footer (n=%s), heading (n=%s), foot_notes (n=%s) and non_text lines (n=%s)",
#                     len(lines),
#                     len(text_lines),
#                     len(header_footer),
#                     len(heading),
#                     len(foot_notes),
#                     len(no_text))

#         if len(no_text) > 0:
#             for i, t in enumerate(no_text):
#                 logger.info("'No_text' line # %s:\n%s",
#                             i,
#                             t["text"])
#                         # [f"{t}\n" for t in ])
            
#         return (text_lines, heading, 
#                 foot_notes, 
#                 header_footer, no_text)
    


# # raw = page.get_text("rawdict")
# #     bullets = []

# #     for block in raw["blocks"]:
# #         for line in block.get("lines", []):
# #             for span in line.get("spans", []):
# #                 for char in span.get("chars", []):
# #                     if char["c"] in BULLETS:

# #                 # text = span["text"]
                
# #                 # for i, char in enumerate(text):
# #                 #     if char in BULLETS:
# #                         bullets.append({
# #                             "char": char,
# #                             # "bbox": span["bbox"],   # grob
# #                             # "line": line["bbox"],   # besser für Matching
# #                             # "span_text": text,
# #                             "bbox": char["bbox"],
# #                             "origin": char["origin"]
# #                         })