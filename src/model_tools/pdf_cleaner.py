## pdf_cleaner.py
# imports
import re
from dataclasses import dataclass, field

# from gmp_compliance.src.model_parsing.classes_html_parsing import TextBlock


@dataclass
class PDFCleaner:
    clean_config: dict = field(default_factory=dict)
    stop_words = ["und", "oder", "bzw.", "sowie", "als"]

    def handle_column_hyphens(self, tbl_col_groups: list[dict]) -> tuple[list, list]:

        left_cleaned = []
        right_cleaned = []

        for group in tbl_col_groups:
            # print("[DEBUG] rows:\n", rows)

            # for left, right in group.items():
            left = [
                {"idx": i, "text": l["text"], "segments": l}
                for i, l in enumerate(group[0]["left"])
            ]
            right = [
                {"idx": i, "text": r["text"], "segments": r}
                for i, r in enumerate(group[0]["right"])
            ]

            print(
                "[DEBUG] handle_col_hyphens:\n"
                f"n_left = {len(left)}\tn_right = {len(right)}"
            )

            left_segs = []
            right_segs = []
            left_segs.append(self._fix_column_hyphens(left))
            right_segs.append(self._fix_column_hyphens(right))

            left_cleaned.extend(left_segs)
            right_cleaned.extend(right_segs)
            # cleaned.append({
            #             "left": left_segs,
            #             "right": right_segs
            #             })
        print(
            "[DEBUG] handle_col_hyphens (END):\n"
            f"n_left = {len(left_cleaned)}\tn_right = {len(right_cleaned)}"
        )

        return left_cleaned, right_cleaned

        # left_segs = [seg["left"] for seg in tbl_col_segments]
        # right_segs = [seg["right"] for seg in tbl_col_segments]

    def _fix_column_hyphens(self, text_list: list[dict]):

        cleaned = []
        for i, curr_seg in enumerate(text_list):
            curr_text = curr_seg["text"]
            curr_info = curr_seg["segments"]

            print("[DEBUG] seg keys:\n", curr_seg.keys())

            if i < len(text_list) - 1:
                next_seg = text_list[i + 1]

                if curr_info["end_hyphen"] and next_seg["segments"]["starts_low"]:
                    print(f"Fixing end_hyphen in segment '{i}")
                    curr_text, text_list[i + 1]["text"] = self._fix_end_hyphen(
                        curr_seg, next_seg
                    )

            if curr_info["has_hyphen"]:
                print(f"Fixing inline_hyphen in segment '{i}'")
                curr_text = self._fix_inline_hyphen(curr_text)

            curr_seg["text"] = curr_text
            cleaned.append(curr_seg)

        return cleaned

    # def handle_body_text_hyphens(self, blocks: List[dict]):

    #     # print("[DEBUG] 'blocks' in handle_body_text_hyphens():"
    #     #       f"\ntype={type(blocks)} | len={len(blocks)}"
    #     #     #   "first element:\n", blocks[0]

    #             #   b_info[0]
    #             #   )

    #     for block in blocks:
    #         for b_info in block:

    #             # print("[DEBUG] 'b_info' in handle_body_text_hyphens():",
    #             #     f"\ntype={type(blocks)} | len={len(blocks)}"
    #             #     )
    #             text = b_info["text"]

    #             if text.strip().endswith("-"):
    #                 text = self._fix_inline_hyphen(text)

    #             if "-" in text.strip():
    #                 text = self._fix_inline_hyphen(text)

    #             b_info["text"] = text
    #     return blocks

    def handle_body_text_hyphens(self, blocks: list[TextBlock]) -> list[TextBlock]:

        # blocks_sorted = sorted(
        #                     blocks,
        #                     key=lambda l: (l["y0_min"],
        #                                     l["x0_min"]))

        # for line in lines_sorted:
        #     words = line["words"] # [w["text"] for w in line["words"]]
        #     words_sort = sorted(words, key=lambda w: w["x0"])
        #     line["text"] = " ".join([w["text"] for w in words_sort])

        cleaned = []

        for i, block in enumerate(blocks):
            # print("length of 'block':\t", len(block))
            # for i, b in enumerate(block):
            # print(f"block # {i} keys:\t", block.keys())
            # sys.exit()

            text = block.text

            # letzter Segment?
            # if i < len(lines_sorted) - 1:
            #     next_line = lines_sorted[i+1]
            #     next_text = next_line["text"]

            #     # hyphen am Ende
            #     # if text.endswith("-") and next_text[0].islower():
            #     #     line["text"], next_line["text"] = self._fix_end_hyphen(line, next_line)

            if "-" in text:
                block.text = self._fix_inline_hyphen(text)

            cleaned.append(block)

        return cleaned

    def _fix_inline_hyphen(self, text: str) -> str:

        from src.core.memory import session

        # setup logger
        logger = session.logger

        text_splits = text.split("-")
        # re.findall(r"(\w+)-\s+", text) #
        print("len text_splits:\t", len(text_splits))

        # skip = False

        text_new = []
        i = 0

        while i < len(text_splits):
            # for i, text in enumerate(text_splits):

            left = text_splits[i].strip()

            if i < len(text_splits) - 1:
                right = text_splits[i + 1].strip()
                if right == "":
                    if i < len(text_splits) - 2:
                        right = text_splits[i + 2].strip()
                    else:
                        right = "-"

                first_word = right.split(" ")[0]

                if first_word in self.stop_words or first_word == ",":
                    merged = left + "- " + right
                    i += 2

                elif first_word and first_word[0].isupper():
                    merged = left + "-" + right
                    i += 2

                else:
                    merged = left + right
                    i += 1

                logger.info(
                    "Fix split between '%s' \nand \n'%s'. \n-> '%s'",
                    left[-20:],
                    right[:20],
                    merged,
                )

                text_new.append(merged)
                # text_splits[i+1] = text_splits[i+1][len(right):].lstrip()

            else:
                text_new.append(left)
                i += 1

        return " ".join(text_new)

    def _fix_end_hyphen(self, curr_line, next_line):
        """
        Fix hyphenation across line boundaries.
        Does NOT merge segments structurally.
        """

        from src.core.memory import session

        logger = session.logger

        y_tol = self.text_prep_config["y_gap_line"]

        curr_text = curr_line["text"]
        next_text = next_line["text"]

        curr_info = curr_line.get("lines", None)
        if curr_info is None:
            curr_y0_mean = curr_line["y0_mean"]
            next_y0_mean = next_line["y0_mean"]
        else:
            curr_y0_mean = curr_info["y0_mean"]
            next_y0_mean = curr_info["y0_mean"]

        y_gap = abs(curr_y0_mean - next_y0_mean)
        left = re.findall(r"(\w+)-$", curr_text)
        right = re.findall(r"^(\w+)", next_text)

        if left and right and y_gap < y_tol:
            # left_word = left[0]
            right_word = right[0]

            if (right_word in self.stop_words) or "," in right_word:
                curr_line["text"] = curr_text + " " + next_text.lstrip()
                logger.info(
                    "Fix end_hyphen after stop_word (/ ',') between '%s' and '%s'.",
                    curr_text[-20:],
                    right_word,
                )

            else:
                curr_line["text"] = curr_text[:-1] + right_word
                logger.info(
                    "Fix end_hyphen between '%s' and '%s'.", curr_text[-20:], right_word
                )

            # entferne Wort aus next_line
            next_line["text"] = next_text[len(right_word) :].lstrip()

            if next_line["text"].startswith("-"):
                curr_line["text"] = curr_text + right_word[0]
                next_line["text"] = next_text[1:].lstrip()

        return curr_line["text"], next_line["text"]

    def merge_hyphenated_words(self, segments):
        merged = []
        prev = None
        block_id = 0

        for seg in segments:
            # print("[DEBUG] block:\n", block)

            if prev is None:
                prev = seg
                continue
                # print("[DEBUG] prev:\n", prev)

            # prev_text = prev["text"]     #, "")
            curr_text = seg["text"]

            # extract left + right word
            left_word = re.findall(r"(\w+)-$", prev["text"])
            right_start = re.findall(r"^(\w+)", curr_text)

            if left_word and right_start:
                left_word = left_word[0]
                right_start = right_start[0]

                if right_start in self.stop_words or right_start.startswith(","):
                    prev["text"] = prev["text"] + " " + curr_text.lstrip()

                else:
                    prev["text"] = prev["text"][:-1] + "" + curr_text.lstrip()

                # prev["text"] = prev["text"] + " " + curr_text.lstrip()

                # if prev and prev["text"].endswith("-"):
                #     curr_block = block["text"]
                #     # [i + 1][4]
                #     if curr_block[0] in self.stop_words:

                #     # prev["text"] = self._merge(prev["text"], block["text"])
                # elif "-" prev["text"].str()
            else:
                # if prev:
                prev["block_id"] = block_id
                merged.append(prev)

                block_id += 1

                prev = seg

        if prev:
            prev["block_id"] = block_id
            merged.append(prev)

        return merged

    # def _handle_hyphen_in_line(self, prev_text, curr_text):

    #     return
