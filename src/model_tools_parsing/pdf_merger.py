## pdf_merger
# import
import re
# import logging
from dataclasses import dataclass, field

from src.core.memory import app_session, ParseContext 
from src.model_classes_parsing.base_classes_parsing import (
                                                    LineGroup, 
                                                    BulletList,
                                                    TextBlock
                                                    )
from src.model_tools_parsing.feature_enricher import FeatureEnricher


@dataclass
class PDFMerger:
    # headings: list = field(init=False)

    def __init__(self, 
                 parse_context:ParseContext, 
                 enricher):
        
        self.merge_config = parse_context.parse_settings.pdf
        self.general_config = parse_context.general_settings.pdf
        self.enricher = enricher
        # FeatureEnricher = field(default_factory=FeatureEnricher())
        self.logger = parse_context.logger

        self.page_heigth: float = field(default_factory = float)
        self.page_width: float = field(default_factory = float)        
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

    def _starts_new_bullet(self, line: LineGroup) -> bool:
        text = line.text.strip()
        return bool(re.match(
            r"^(?:[-–•▪●]|[a-z]\)|\([ivxlcdm]+\)|[ivxlcdm]+)\s+",
            text,
            re.I,
        ))


    def merge_text_lines(
                    self, 
                    lines: list[LineGroup],
                    headings: list[LineGroup],
                    page_attributes: dict
                    ) -> dict:
        # setup logger
        # self.logger = session_state.logger

        # self.headings = headings
        self.page_attributes = page_attributes
        # .get("height")
        # self.page_width = page_attributes.get("width")

        lines_sorted = sorted(lines, 
                              key=lambda l: 
                              l.meta.y_start_mean)
        # blocks = []
        # bullets = []
        bullet_items = []
        text_bodies = []
        # headings = []
        for line in lines_sorted:
            if line.line_type in ["body_text", "tba"]:
                text_bodies.append(line)
        
            elif line.line_type in ["lvl_1_bullet", 
                                    "lvl_2_bullet"]:
                bullet_items.append(line)

            elif line.line_type == "heading":
                self.logger.error("Found 'heading' in merge_text_lines()")
                headings.append(line)

            else:
                self.logger.warning(
                    "Unknown 'line_type':\t%s\ntext:\t%s",
                    line.line_type,
                    line.text,
                )

        self.logger.info(
            "len_bullet_items = %s | len_text_bodies = %s \t\t in merge_text_lines()",
            len(bullet_items),
            len(text_bodies),
        )

        return {
            # "blocks": 
            "bullets": self._merge_bullets(bullet_items),
            "text_bodies": self._merge_text_bodies(text_bodies), 
            "headings": headings
            }


    def _merge_text_bodies(
                    self, 
                    text_bodies: list[LineGroup],
                    headings: list[LineGroup] | None = None,
                    ) -> list[TextBlock]:

        self.logger.info("Start merging text bodies")

        text_bodies = self._merge_text_groups(
                        lines = text_bodies,
                        headings = headings
                        )

        text_bodies = self._finalize_body_text(text_bodies)

        for text_body_id, t_body in enumerate(text_bodies, start=1):
            t_body.text_body_id = text_body_id

        return text_bodies
    

    def _merge_bullets(
                    self, 
                    bullets: list[LineGroup]
                    ) -> list[TextBlock]:

        bullets = self._merge_text_groups(bullets)

        bullets = self._finalize_body_text(bullets)

        # if isinstance(bullets, dict):
        #     bullets = [bullets]

        bullets_new = []
        bullet_id = 1
        for bul in bullets:
            
            bullets_new.append(
                    BulletList(
                        bullet_id = bullet_id,
                        text= bul.text,
                        meta = bul.meta,
                        # : ElementMeta | None = Field(default_factory=ElementMeta)
                        elements = bul.elements
                        # : list[Word] = Field(default_factory=list)
                    )
            )

            bullet_id += 1

        return bullets_new

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


    def _has_heading_between(
                        self,
                        prev: LineGroup,
                        curr: LineGroup,
                        headings: list[LineGroup],
                    ) -> bool:
        y_prev = prev.meta.y_start_min
        y_curr = curr.meta.y_start_min

        if y_prev > y_curr:
            y_prev, y_curr = y_curr, y_prev

        return any(
            y_prev < h.meta.y_start_min < y_curr
            for h in headings
        )


    def _merge_text_groups(
                        self, 
                        lines: list[LineGroup],
                        headings: list[LineGroup] | None = None
                        ) -> list[TextBlock]:

        # y_tol = self.text_prep_config["y_gap_line"]

        headings = headings or []
        headings_sorted = sorted(
                    headings,
                    key=lambda h: h.meta.y_start_min,
                )

        lines_sorted = sorted(
            lines, key=lambda l: (
                            l.meta.y_start_min, 
                            l.meta.x_start_min
                            )
                            )
        # , l["x0_min"]))
        is_bullet_mode = any(
                    l.line_type in ["lvl_1_bullet", 
                                    "lvl_2_bullet"]
                    for l in lines_sorted
                )
        current = []
        final = []
        for curr_line in lines_sorted:
            
            words_sort = self._word_reading_order(curr_line.elements)
            curr_line.text = " ".join(w.text.strip() for w in words_sort)

            if (
                current 
                and is_bullet_mode 
                and self._starts_new_bullet(curr_line)
                ):
            # print("curr_type:\t", type(current[0]))

                final.append(
                    TextBlock(
                        text=self._merge_text(current), 
                        elements=current)
                        )
                
                current = [curr_line]
                continue
            # text = " ".join([w.text.strip() for w in words_sort])
            # curr_line.text = text

            # if len(current) == 0:
            # current.append(curr_line)
            # continue

            # is_last = i == len(lines_sorted) - 1
            prev_line = current[-1] if current else None
            # None if i == 0 else lines_sorted[i - 1]
            
            if prev_line is None:
                current = [curr_line]
            
            elif self._has_heading_between(prev_line, 
                                           curr_line, 
                                           headings_sorted):
                final.append(
                    TextBlock(
                        text=self._merge_text(current),
                        elements=current,
                    )
                )
                current = [curr_line]

            elif self._should_merge(prev_line, curr_line):
                current.append(curr_line)

            else:
                final.append(
                    TextBlock(
                        text=self._merge_text(current), 
                        elements=current
                        )
                )

                current = [curr_line]

        if current:
            final.append(
                TextBlock(
                    text=self._merge_text(current),
                    elements=current,
                )
            )


        return final


    def _merge_text(self, lines: list[LineGroup]) -> str:

        text = ""

        for i, line in enumerate(lines):
            if i == 0:
                text += line.text
                continue

            prev = lines[i - 1] if i > 0 else ""

            if prev and prev.meta.end_hyphen:
                text = text.rstrip("-") + line.text.lstrip()
            else:
                text += " " + line.text

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


    def _word_reading_order(self, words):
        return sorted(
            words,
            key=lambda w: (
                round(w.meta.y_start / 2) * 2,  # kleine y-Abweichungen gruppieren
                w.meta.x_start
            )
        )


    def _finalize_body_text(
                        self, 
                        blocks: list[TextBlock]
                        ) -> list[TextBlock]:

        # enricher = session.enricher
        # text_bodies = enricher.enrich(text_bodies)

        return self.enricher.enrich_blocks(blocks, 
                                           self.page_attributes)

    # def merge_segments_to_blocks(
    #                         self,
    #                         segments: List[dict]
    #                         ) -> List[dict]:

    #     blocks = []
    #     current = None
    #     block_id = 0

    #     for seg in segments:

    #         if current is None:
    #             current = self._init_block(seg)
    #             continue

    #         if self._should_merge(current, seg):
    #             current = self._merge_into_block(current, seg)

    #         else:
    #             current.meta.block_id = block_id
    #             blocks.append(current)
    #             block_id += 1

    #             current = self._init_block(seg)

    #     if current:
    #         current["block_id"] = block_id
    #         blocks.append(current)

    #     return blocks

    def _should_merge(self, prev: LineGroup, curr: LineGroup) -> bool:
        y_tol = self.general_config.y_gap_line

        if prev.meta.end_hyphen:
            return True

        if not prev.meta.ends_sentence:
            return True

        y_gap = abs(prev.meta.y_end_max - curr.meta.y_start_min)
        if y_gap < min(1.5 * prev.meta.height, y_tol):  # später dynamisch machen
            return True

            # return True

        # vertikaler Abstand

        # Satzende
        # not ["ends_sentence"]

        return False

    # (same_column
    #             and small_gap
    #             and not seg["ends_sentence"])

    # def _should_group_cols(self, block, seg):
    #     y_tol = self.merge_config["y_tol_line"]

    #     # gleiche Spalte
    #     same_column = block.get("column") == seg.get("column")

    #     # vertikaler Abstand
    #     y_gap = abs(seg["segments"]["y0_min"] - block["y1_max"])
    #     small_gap = y_gap < y_tol   # später dynamisch machen

    #     # Satzende
    #     # not ["ends_sentence"]

    #     return (same_column
    #             and small_gap)

    # def _init_block(self, seg):

    #     return {
    #         "text": seg["text"],
    #         "column": seg.get("column"),
    #         "y0_min": seg["y0_min"],
    #         "y0_mean": seg["y0_mean"],
    #         "y1_max": seg["y1_max"],
    #         "segments": [seg],
    #     }

    # def _init_col_block(self, seg):
    #     text = seg["text"]
    #     seg_info = seg["segments"]
    #     # print("tbl_segment keys:\n", seg["segments"].keys())

    #     return {
    #         "text": text,
    #         "column": seg_info["column"],   # seg.get("column"),
    #         "y0_min": seg_info["y0_min"],    #  for s in seg["segments"]],
    #         "y0_mean": seg_info["y0_mean"],    # for s in seg["segments"]], # seg[""],
    #         "y1_max": seg_info["y1_max"],    # for s in seg["segments"]],   # seg[""],
    #         "segments": [seg_info],
    #     }

    # def _merge_into_block(self, block, seg):

    #     block["text"] += " " + seg["text"]
    #     block["y1_max"] = max(block["y1_max"], seg["y1_max"])
    #     block["y0_min"] = min(block["y0_min"], seg["y0_min"])
    #     block["y0_mean"] = np.mean(block["y0_all"] + seg["y0_all"])
    #     block["segments"].append(seg)

    #     return block

    # def _group_cols(self, block, seg):
    #     text = seg["text"]
    #     seg_info = seg["segments"]

    #     block["text"] += " " + text
    #     block["y1_max"] = max(block["y1_max"], seg_info["y1_max"])
    #     block["y0_min"] = min(block["y0_min"], seg_info["y0_min"])
    #     block["y0_mean"] = np.mean(block["y0_all"] + seg_info["y0_all"])
    #     block["segments"].append(seg)

    #     return block
