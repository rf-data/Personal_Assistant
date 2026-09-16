## doc_classifier.py
# import
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

# from gmp_compliance.src.model_parsing.classes_html_parsing import DocumentExtract, LineGroup
# import pprint
# import sys
from src.model_parsing.text_classifier import BaseClassifier


@dataclass
class WikiClassifier(BaseClassifier):
    page_attributes: dict[str, Any] = field(default_factory=dict)

    def classify_links(self, extract_elements: list[dict]) -> DocumentExtract:
        paragraphs = []
        for element in extract_elements:
            e_type = element.get("meta", {}).get("element_type")

            if e_type == "paragraph":
                paragraphs.append(element)

        return elements_raw

    def classify_line(self, lines: list[LineGroup], page_attributes: dict):
        from src.core.memory import session

        self.logger = session.logger

        self.page_attributes.update(page_attributes)
        # head_foot, other = self._separate_header_footer(lines)
        # text_rows, non_text_rows = self._filter_text(segments)
        class_dict = self._differentiate_text(lines)
        # {"text": text_lines,
        #         "heading": heading,
        #         "foot_notes": foot_notes,
        #         "header_footer": header_footer,
        #         "other": no_text}

        heading = self._subdivide_heading(class_dict["heading"])
        class_dict["heading"] = heading

        return class_dict

    # def classify_paragraph(self):

    #     return

    # def detect_table(self):

    #     return

    def _is_header_footer(self, line):
        up_down_edge = self.classify_config["up_down_thresh"]

        # header_footer = []
        # other = []

        if (
            line.meta.rel_height < up_down_edge
            or line.meta.rel_height > 1 - up_down_edge
        ) and (line.meta.n_chars < 100 or line.meta.n_words < 20):
            return True

            # else:
            #     other.append(l)

        return False  # header_footer, other

    def _heading_score(self, line):
        median_size = self.page_attributes["median_size"]

        heading_score = 0

        font_sizes = line.meta.font_size_mean
        if font_sizes > median_size:  # (len(font_sizes) == 1 and
            heading_score += 2
        # else:
        #     logger.warning("Line has more than one font size:\t", font_sizes)

        if line.meta.is_bold_rel > 0.5:
            heading_score += 2

        if line.meta.n_words < 10:
            heading_score += 1

            # if line["has_numbering"]:
            #     heading_score += 1

            # if line["large_top_gap"]:
            #     heading_score += 1

        # line["heading_score"] = heading_score

        return heading_score

    def _subdivide_heading(self, heading):
        font_span = defaultdict(list)

        for head in heading:
            font_size = int(head.meta.font_size_mean // 1)
            font_span[font_size].append(head)

        span_sorted = sorted(font_span.keys(), reverse=True)

        head_fin = []
        idx = 1
        for size in span_sorted:
            heads = font_span[size]

            self.logger.info("HEADING: size=%s  |  count=%s", size, len(heads))

            for h in heads:
                h.meta.line_type += f"_lvl_{idx}"

                head_fin.append(h)

                self.logger.info("line_type = %s\n'%s'", h.meta.line_type, h.text)

            idx += 1

        return head_fin

    def _is_foot_note(self, line, prev_type):
        foot_note_thresh = self.classify_config["foot_note_thresh"]

        median_size = self.page_attributes["median_size"]
        page_height = self.page_attributes["height"]

        self.logger.info(
            "Median font size = %s  | page:height = %s",
            round(median_size, 2),
            page_height,
        )
        font_size = line.meta.font_size_mean
        text = line.text.strip()

        if font_size is None:
            return False

        score = 0

        if line.meta.y_start_min > 0.8 * page_height:
            score += 1

        if font_size < 0.8 * median_size:
            score += 1

        if re.match(r"^\s*(\d+|\*|†)", text):
            score += 2

        if prev_type == "foot_note":
            score += 2

        # if line["n_words"] < 15:
        #     score += 1

        # if len(line["font_sizes"]) != 1:
        #     logger = session.logger
        #     logger.info("Line has more than one or no font_size.\n%s",
        #                 line)

        return score >= foot_note_thresh

    def _is_column(self, lines):
        inter_word_gap = ""

        return

    def _is_table(self, lines):
        return

    def _differentiate_text(self, lines: list[LineGroup]):
        left_indent = self.page_attributes["left_indent"]

        start_tol = self.classify_config["start_tol"]
        y_tol = self.classify_config["y_gap_line"]
        head_thresh = self.classify_config["heading_threshold"]
        width_thresh = self.classify_config["width_thresh"]

        bullet_start_x = 0
        bullet_start_y = 0
        # bullet_lines = []
        # body_text_lines = []
        text_lines = []
        heading = []
        header_footer = []
        foot_notes = []
        no_text = []

        lines_sorted = sorted(lines, key=lambda l: l.meta.y_start_mean)

        for idx, line in enumerate(lines_sorted):
            line.meta.line_type = "tba"
            text = line.text

            # curr_type = type(line)
            # if "LineGroup" not in str(curr_type):
            #     print(f"curr_type (idx={idx}):\t", curr_type)

            prev_type = lines_sorted[idx - 1].meta.line_type if idx > 0 else "tba"
            # if (i >0
            #     and
            #     segments[i-1]["line_type"] not in [
            #                                 "lvl_1_bullet",
            #                                 "lvl_2_bullet"
            #                                 ]):
            #     text_lines.append(bullet_lines)
            #     bullet_lines = []

            if (
                re.match(r"^(\d+\.\d+)", text)
                or re.match(r"^(\•\d+)", text)
                or re.match(r"^(\([ivx]+\))", text)
            ):
                # or ):
                if bullet_start_x == 0 or line.meta.x_start_min < bullet_start_x:
                    line.meta.line_type = "lvl_1_bullet"

                else:
                    line.meta.line_type = "lvl_2_bullet"

                text_lines.append(line)

                bullet_start_x = line.meta.x_start_min
                bullet_start_y = line.meta.y_start_mean

            elif (
                idx > 0
                and prev_type in ["lvl_1_bullet", "lvl_2_bullet"]
                and line.meta.x_start_min > bullet_start_x
                and abs(line.meta.y_start_mean - bullet_start_y) < y_tol
            ):
                if (
                    re.match(r"^(\d+\.\d+)", text)
                    or re.match(r"^(\•\d+)", text)
                    or re.match(r"^(\([ivx]+\))", text)
                ):
                    # new_text = " ".join([b["text"] for b in bullet_lines])
                    # for line in bullet
                    # new_lines

                    # bullet_lines = [line]
                    line.meta.line_type = "lvl_2_bullet"
                    (bullet_start_x, bullet_start_y) = (
                        line.meta.x_start_min,
                        line.meta.y_start_mean,
                    )

                else:
                    line.meta.line_type = "lvl_1_bullet"
                    bullet_start_y = line.meta.y_start_mean

                text_lines.append(line)

            elif self._is_foot_note(line, prev_type):
                line.meta.line_type = "foot_note"
                foot_notes.append(line)
                self.logger.info("FOOT_NOTE:\t%s", line.text)

            elif self._heading_score(line) >= head_thresh:
                # ((line["n_words"] < 6
                #         or line["n_chars"] < 60)
                #         and line["line_width"]):

                line.meta.line_type = "heading"
                self.logger.info("HEADING:\t%s", line.text)
                heading.append(line)

            elif line.meta.ends_sentence:
                line.meta.line_type = "body_text"
                text_lines.append(line)

            elif self._is_header_footer(line):
                line.meta.line_type = "header_footer"
                header_footer.append(line)

            elif abs(line.meta.x_start_min - left_indent) < start_tol:  # "left_aligned"
                # info_obj.meta.width
                if line.meta.rel_width > width_thresh:
                    line.meta.line_type = "body_text"
                    text_lines.append(line)

                elif (
                    idx > 0
                    and prev_type == "body_text"
                    and (
                        line.text[0].islower()
                        or line.text[0].isdigit()
                        or line.meta.ends_sentence
                    )
                ):
                    gap = abs(
                        line.meta.y_start_min - lines_sorted[idx - 1].meta.y_start_min
                    )

                    if line.meta.ends_sentence:
                        line.meta.line_type = "body_text"
                        # body_text_lines.append(line)
                        text_lines.append(line)

                    elif gap < y_tol:
                        line.meta.line_type = "body_text"
                        text_lines.append(line)

                elif self._heading_score(line) >= head_thresh:
                    # ((line["n_words"] < 6
                    #     or line["n_chars"] < 60)
                    #     and line["line_width"]):
                    line.meta.line_type = "heading"
                    heading.append(line)
                    self.logger.info("HEADING:\t%s", line.text)

                else:
                    no_text.append(line)

            else:
                no_text.append(line)

        # if bullet_lines:
        #     text_lines.append(bullet_lines)

        # if body_text_lines:
        #     text_lines.append(body_text_lines)

        self.logger.info(
            "Splitting lines (n=%s) into text (n=%s), header_footer (n=%s), heading (n=%s), foot_notes (n=%s) and non_text lines (n=%s)",
            len(lines),
            len(text_lines),
            len(header_footer),
            len(heading),
            len(foot_notes),
            len(no_text),
        )

        if len(no_text) > 0:
            for i, t in enumerate(no_text):
                self.logger.info("'No_text' line # %s:\n%s", i, t.text)
                # [f"{t}\n" for t in ])

        return {
            "text": text_lines,
            "heading": heading,
            "foot_notes": foot_notes,
            "header_footer": header_footer,
            "other": no_text,
        }


# raw = page.get_text("rawdict")
#     bullets = []

#     for block in raw["blocks"]:
#         for line in block.get("lines", []):
#             for span in line.get("spans", []):
#                 for char in span.get("chars", []):
#                     if char["c"] in BULLETS:

#                 # text = span["text"]

#                 # for i, char in enumerate(text):
#                 #     if char in BULLETS:
#                         bullets.append({
#                             "char": char,
#                             # "bbox": span["bbox"],   # grob
#                             # "line": line["bbox"],   # besser für Matching
#                             # "span_text": text,
#                             "bbox": char["bbox"],
#                             "origin": char["origin"]
#                         })
