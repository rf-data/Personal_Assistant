

import numpy as np 
from dataclasses import dataclass, field
from typing import List
import logging

from src.core.memory import session


@dataclass
class TextMerger:

    text_prep_config: dict = field(default_factory=dict)
    logger = logging.getLogger(__name__)

    # def merge_table_columns(self, table_groups: List[dict]):

    #     blocks = []
    #     current = None
    #     block_id = 0

    #     for group in table_groups:

    #         for segment in group:

    #             if current is None:
    #                 current = self._init_col_block(segment)
    #                 continue

    #             if self._should_group_cols(current, segment):
    #                 current = self._group_cols(current, segment)

    #             else:
    #                 current["col_block_id"] = block_id
    #                 blocks.append(current)
    #                 block_id += 1

    #                 current = self._init_col_block(segment)

    #         if current:
    #             current["col_block_id"] = block_id
    #             blocks.append(current)

    #             block_id += 1
    #             current = None

    #     return blocks


    def merge_text_lines(
                        self, 
                        lines: List[dict]
                        ) -> List[dict]:
        # setup logger
        self.logger = session.logger

        lines_sorted = sorted(
                            lines,
                            key=lambda l: l["y0_mean"]
                            )
        blocks = []
        bullets = []
        text_bodies = []
        # headings = []
        for line in lines_sorted:
            line["text_body_id"] = "n.a"
            line["bullet_id"] = "n.a"
            # line

            # if isinstance(line, list) and line:
            if line["line_type"] == "body_text":
                text_bodies.append(line)
                
            elif line["line_type"] in [
                                    "lvl_1_bullet",
                                    "lvl_2_bullet"
                                    ]:
                bullets.append(line)

            elif line["line_type"] == "heading":
                blocks.append(line)

            else:
                self.logger.warning("Unknown 'line_type':\t%s\ntext:\t%s",
                               line["line_type"],
                               line["text"])

        self.logger.info("len_bullets = %s | len_text_bodies = %s \t[merge_text_lines()]",
                    len(bullets),
                    len(text_bodies)
                    )
        
        if text_bodies:
            blocks.extend(self._merge_text_bodies(text_bodies))

        if bullets:
            blocks.extend(self._merge_bullets(bullets))

        return blocks
    

    def _merge_text_bodies(self, text_bodies):
        
        self.logger.info("Start merging text bodies")

        text_bodies = self._merge_text_groups(text_bodies)

        text_bodies = self._finalize_body_text(text_bodies)

        text_body_id = 1
        for t_body in text_bodies:
            t_body["text_body_id"] = text_body_id 

        return text_bodies
    

    def _merge_bullets(self, bullets):

        bullets = self._merge_text_groups(bullets)

        bullets = self._finalize_body_text(bullets)

        if isinstance(bullets, dict):
            bullets = [bullets]

        bullet_id = 1
        for bul in bullets:
            bul["bullet_id"] = bullet_id

        return bullets

        # bullet_id = 1

        #         block = self._merge_text_groups(line) 
        #         for b in block:
        #                 # print("[DEBUG] dtype b in block:\t", type(b))
                        
        #                 b["bullet_id"] = "n.a"
        #                                     # block
        #             text_body_id += 1

        #             block = self._finalize_body_text(block)
        #             blocks.append(block)
                
        #         elif line[0]["line_type"] in [
        #                                     "lvl_1_bullet",
        #                                     "lvl_2_bullet"
        #                                     ]:
        #             bullet = self._merge_text_groups(line) 
        #             for b in bullet:
        #                 # print("[DEBUG] dtype b in bullet:\t", type(b))
        #                 b["bullet_id"] = bullet_id 
        #                 b["text_body_id"] = "n.a"

        #             bullet_id += 1
                    
        #             bullet = self._finalize_body_text(bullet)
        #             blocks.append(bullet)
        
            
            
            # else:

                # logger.warning("Line is empty (len=%s) or unexpected dtype (%s) [merge_text_lines()]",
                #             len(line),
                #             type(line))

        # current: 
        # for text in text_bodies:
            
        # return blocks
    
    
    def _merge_text_groups(self, lines: List[dict]) -> List[dict]:

        # y_tol = self.text_prep_config["y_gap_line"]

        lines_sorted = sorted(lines, 
                            key=lambda l: (l["y0_min"]))
                                # , l["x0_min"]))
        
        current = []
        final = []
        for i, curr_line in enumerate(lines_sorted):
            words = curr_line["words"] # [w["text"] for w in seg["words"]]
            words_sort = sorted(words, key=lambda w: w["x0"])

            text = " ".join([w["text"].strip() for w in words_sort])
            curr_line["text"] = text
            
            # if len(current) == 0:
            # current.append(curr_line)
                # continue

            # is_last = i == len(lines_sorted) - 1
            prev_line = None if i == 0 else lines_sorted[i-1]

            if not prev_line: 
                current.append(curr_line)

            elif self._should_merge(prev_line, curr_line):
                current.append(curr_line)

            else:
                final.append({
                        "text": self._merge_text(current),
                        # " ".join([line["text"] for line in current]),
                        "lines": current
                        })
                    
                    # current)

                current = [curr_line]

        if current:
            final.append({
                    "text": self._merge_text(current),
                    "lines": current
                    })

        # blocks = self._merge_text
        #    
        #    seg["text"] = text
        # final = self._merge_text_body(final)

        return final
    

    def _merge_text(self, lines):
                        
        text = ""

        for i, line in enumerate(lines):
            if i == 0:
                text += line["text"]
                continue

            prev = lines[i-1] if i > 0 else ""

            if prev and prev["end_hyphen"]:
                text = text.rstrip("-") + line["text"].lstrip()
            else:
                text += " " + line["text"]

        # print("Merged text to:\n", text)
        return text
    
            # end_condition = (
            #             line["ends_sentence"]
            #             or is_last
            #             or (
            #                 next_seg
            #                 and abs(next_seg["y0_mean"] - line["y0_mean"]) > y_tol
            #                 )
                        # or (
                        #     next_seg
                        #     and not next_seg["starts_low"]
                        #     and not seg["ends_sentence"]
                        #     )
                        # )

            # if end_condition:
            #     final.append({
            #             "text": " ".join([line["text"] for line in current]),
            #             "lines": current.copy()
            #             })

            #     current = []

            # else:
            #     current.append(seg)
       
    

    # def _end_condition(self, segment):

    #     return (
    #         segment["ends_sentence"]
    #         or (
    #             next
    #         )
    #     )
    

    def _finalize_body_text(self, blocks: List[dict]):

        enricher = session.enricher
        # text_bodies = enricher.enrich(text_bodies)

        return enricher.enrich_blocks(blocks)
    

    def merge_segments_to_blocks(
                            self, 
                            segments: List[dict]
                            ) -> List[dict]:

        blocks = []
        current = None
        block_id = 0

        for seg in segments:

            if current is None:
                current = self._init_block(seg)
                continue

            if self._should_merge(current, seg):
                current = self._merge_into_block(current, seg)

            else:
                current["block_id"] = block_id
                blocks.append(current)
                block_id += 1

                current = self._init_block(seg)

        if current:
            current["block_id"] = block_id
            blocks.append(current)

        return blocks


    def _should_merge(self, prev, curr):
        y_tol = self.text_prep_config["y_gap_line"]

        if prev["end_hyphen"]:
            return True
            
        if not prev["ends_sentence"][0]:
            return True
        
        y_gap = abs(prev["y1_max"] - curr["y0_min"])
        if y_gap < min(1.5 * prev["height"], y_tol):  # später dynamisch machen
            return True
            
            # return True

        # vertikaler Abstand
       
        
        # Satzende
        # not ["ends_sentence"]

        return False
    
    # (same_column 
    #             and small_gap 
    #             and not seg["ends_sentence"])


    def _should_group_cols(self, block, seg):
        y_tol = self.text_prep_config["y_tol_line"]

        # gleiche Spalte
        same_column = block.get("column") == seg.get("column")

        # vertikaler Abstand
        y_gap = abs(seg["segments"]["y0_min"] - block["y1_max"])
        small_gap = y_gap < y_tol   # später dynamisch machen

        # Satzende
        # not ["ends_sentence"]

        return (same_column 
                and small_gap)


    def _init_block(self, seg):

        return {
            "text": seg["text"],
            "column": seg.get("column"),
            "y0_min": seg["y0_min"],
            "y0_mean": seg["y0_mean"],
            "y1_max": seg["y1_max"],
            "segments": [seg],
        }


    def _init_col_block(self, seg):
        text = seg["text"]
        seg_info = seg["segments"]
        # print("tbl_segment keys:\n", seg["segments"].keys())

        return {
            "text": text,
            "column": seg_info["column"],   # seg.get("column"),
            "y0_min": seg_info["y0_min"],    #  for s in seg["segments"]],
            "y0_mean": seg_info["y0_mean"],    # for s in seg["segments"]], # seg[""],
            "y1_max": seg_info["y1_max"],    # for s in seg["segments"]],   # seg[""],
            "segments": [seg_info],
        }
    

    def _merge_into_block(self, block, seg):

        block["text"] += " " + seg["text"]
        block["y1_max"] = max(block["y1_max"], seg["y1_max"])
        block["y0_min"] = min(block["y0_min"], seg["y0_min"])
        block["y0_mean"] = np.mean(block["y0_all"] + seg["y0_all"])
        block["segments"].append(seg)

        return block
    

    def _group_cols(self, block, seg):
        text = seg["text"]
        seg_info = seg["segments"]

        block["text"] += " " + text
        block["y1_max"] = max(block["y1_max"], seg_info["y1_max"])
        block["y0_min"] = min(block["y0_min"], seg_info["y0_min"])
        block["y0_mean"] = np.mean(block["y0_all"] + seg_info["y0_all"])
        block["segments"].append(seg)

        return block