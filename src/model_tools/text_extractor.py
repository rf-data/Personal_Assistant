## text_extractor.py
# import
import re
from dataclasses import dataclass

# from collections import defaultdict
# import gc
# import numpy as np
from pathlib import Path

from markdown_it import MarkdownIt

# from tiktoken import encoding_for_model
from src.model_parsing.data_classes_parsing import (
    Document,
    DocumentExtract,
    Element,
    ElementMeta,
    TextBlock,
    TextLine,
    TextWordMeta,
    Word,
)
from src.model_tools.base_extractor import BaseExtractor
from src.utils.text_file_helper import read_text_file

# @dataclass
# class CleaningStats:
#     total_words: int = 0
#     total_line: int = 0


@dataclass
class TXTCleanExtractor(BaseExtractor):
    def extract(self, f_path: str) -> DocumentExtract:
        from src.core.memory import session

        self.logger = session.logger
        self.enricher = session.enricher

        text = read_text_file(f_path)
        text_split = re.split(r"\n{2, }", text)
        self.logger.info("Text was split into %s blocks.", len(text_split))

        blocks = []
        for b_idx, block in enumerate(text_split):
            block_split = re.split(r"\n", block)
            self.logger.info(
                "Block %s was split into %s lines.\n", b_idx, len(block_split)
            )

            lines = []
            for l_idx, line in enumerate(block_split):
                words = line.split()

                if l_idx % 10 == 0:
                    self.logger.info(
                        "Starting with line %s of %s.\n", l_idx, len(block_split)
                    )

                words_clean = []
                for w_idx, word in enumerate(words):
                    words_clean.append(
                        Word(
                            text=self._clean_word_token(word),
                            meta=TextWordMeta(
                                word_no=w_idx, line_no=l_idx, block_no=b_idx
                            ),
                        )
                    )

                text_line = " ".join([w.text for w in words_clean])
                line_info = self.enricher._add_basic_metadata(
                    text_line, words_clean, TextLine()
                )
                lines.append(line_info)

            text_block = "\n".join([l.text for l in lines])
            block_info = self.enricher._add_basic_metadata(
                text_block, lines, TextBlock()
            )
            blocks.append(block_info)

        text_complete = "\n\n".join([b.text for b in blocks])
        doc_info = self.enricher._add_basic_metadata(text_complete, blocks, Document())

        return DocumentExtract(
            doc_type="txt",
            doc_name=Path(f_path).name,
            text=doc_info.text,
            elements=doc_info.elements,
            meta=doc_info.meta,
        )


@dataclass
class MDCleanExtractor(BaseExtractor):
    # TODO: LaTex / KaTex - Elemente
    # TODO: Images
    # TODO: Tabellen

    def extract(self, f_path: str) -> DocumentExtract:

        md_text = read_text_file(f_path)

        md = MarkdownIt()

        tokens = md.parse(md_text)

        elements = self._differentiate_text(tokens)

        elements_clean = []
        for element in elements:
            words_clean = []
            for word in element.text.split():
                words_clean.append(Word(text=self._clean_word_token(word)))

            txt_clean = " ".join([w.text for w in words_clean])

            element_new = self.enricher._add_basic_metadata(
                txt_clean, words_clean, Element()
            )

            element_new.meta.element_type = element.meta.element_type

            elements_clean.append(element_new)

        text_clean = "\n\n".join([ele.text for ele in elements_clean])
        doc_info = self.enricher._add_basic_metadata(
            text_clean, elements_clean, Document()
        )

        return DocumentExtract(
            doc_type="md",
            doc_name=Path(f_path).name,
            text=doc_info.text,
            elements=doc_info.elements,
            meta=doc_info.meta,
        )

    def _differentiate_text(self, tokens) -> list[Element]:

        elements = []
        for idx, t in enumerate(tokens):
            # print("type:\t", t.type)
            # print("tag:\t", t.tag)
            # print("content:\t", t.content)

            if t.content == "":
                continue

            if t.type == "heading_open":
                elements.append(
                    Element(
                        text=tokens[idx + 1].content,
                        meta=ElementMeta(
                            token_id=[idx, idx + 1, idx + 2],
                            element_type="heading",
                            level=int(t.tag[1]),
                        ),
                    )
                )

                idx += 3

            elif t.type == "paragraph_open":
                elements.append(
                    Element(
                        text=tokens[idx + 1].content,
                        meta=ElementMeta(
                            element_type="paragraph",
                            token_id=[idx, idx + 1, idx + 2],
                        ),
                    )
                )

                idx += 3

            elif t.type == "list_item_open":
                elements.append(
                    Element(
                        text=tokens[idx + 1].content,
                        meta=ElementMeta(
                            element_type="list",
                            token_id=[idx, idx + 1, idx + 2],
                        ),
                    )
                )

                idx += 3

            elif t.type == "bullet_list_open":
                elements.append(
                    Element(
                        text=tokens[idx + 1].content,
                        meta=ElementMeta(
                            element_type="bullet",
                            token_id=[idx, idx + 1, idx + 2],
                        ),
                    )
                )

                idx += 3

            elif t.type == "fence":
                elements.append(
                    Element(
                        text=tokens[idx + 1].content,
                        meta=ElementMeta(
                            element_type="code",
                            language=t.info,
                            token_id=idx,
                        ),
                    )
                )

                idx += 1

        return elements

        # heading_open
        # inline
        # paragraph_open
        # fence
        # bullet_list_open


#     # f_name: str = field(default_factory=str)
#     encoder: encoding_for_model
#     extract_config: Dict = field(default_factory=dict)

#     debug: bool = False
#     stats: CleaningStats = field(default_factory=CleaningStats)
#     EXTRACT_DICT = {
#         # "plumber": extract_text_plumber,
#         "pymupdf": extract_text_pymupdf
#         }
#     logger = logging.getLogger(__name__)
#     # -------------------------
#     # Public API
#     # -------------------------

#     def extract_text_per_page(
#                         self,
#                         f_path:str,
#                         ) -> List[dict]:
#         from src.core.memory import session

#         self.logger = session.logger
#         self.logger.info("Preparing text for extraction.")


#         extract_model = self.extract_config["extraction_model"]

#         extract_fn = self.EXTRACT_DICT[extract_model]
#         extract_results = extract_fn(f_path)

#         return extract_results


#     def clean_and_group_words(self, page) -> List[dict]:
#         # print("CONFIG:", self.extract_config)
#         from src.core.memory import session

#         extract_source = self.extract_config["extract_source"]

#         if "words" in extract_source:
#             words = page.get_text("words")
#             words = self._clean_words_from_words(words)
#             # lines = self._group_words_to_lines(words)

#             if "raw_dict" in extract_source:
#                 spans = self._extract_spans_from_rawdict(page)
#                 words = self._merge_sources(words, spans)

#             lines = self._group_words_to_lines(words)

#         elif "raw_dict" in extract_source:
#             lines = self._extract_spans_from_rawdict(page)

#         enricher = session.enricher

#         lines_fin = enricher.enrich_lines(lines)

#         # self._finalize_lines()

#         # # encoder = session.encoder
#         # if isinstance(lines_fin, list):
#         #     text_comb = "\n".join([l["text"] for l in lines_fin])
#         # else:
#         #     text_comb = lines_fin

#         # result = {
#         #     "n_words": len(words),
#         #     "n_tokens": len(self.encoder.encode(text_comb)),
#         #     "n_lines": len(lines_fin),
#         #     # "words": words,
#         #     "lines": lines_fin,
#         #     }

#         return lines_fin    # result, text_comb

#     # -------------------------
#     # CLEANING TEXT
#     # -------------------------
#     def _extract_spans_from_rawdict(self, page) -> List[dict]:

#         raw = page.get_text("rawdict")

#         line_info = []
#         for block in raw["blocks"]:
#             for line in block.get("lines", []):

#                 spans = line.get("spans", [])

#                 for span in spans:
#                     bbox = span["bbox"]

#                     chars = [c["c"] for c in span["chars"]]
#                     text = "".join(chars)
#                     text_clean = self._clean_word_token(text)

#                     line_info.append({
#                                 "size": span["size"],
#                                 "alpha": span["alpha"],
#                                 "flags": span["flags"],
#                                 "font": span["font"],
#                                 "color": span["color"],
#                                 "x0": bbox[0],
#                                 "y0": bbox[1],
#                                 "x1": bbox[2],
#                                 "y1": bbox[3],
#                                 # "chars": chars,
#                                 # "words": text_clean.split(" "),
#                                 "text": text_clean
#                                 })

#                 del spans
#                 # gc.collect()

#         return line_info


#     # -------------------------
#     # CLEANING TEXT
#     # -------------------------
#     # def _basic_text_cleaning(self, text: str) -> str:

#     #     text = self._clean_raw_text(text)
#     #     text = self._normalize_text(text)

#     #     return text

#     # def _clean_raw_text(self, text: str) -> str:
#     #     text = text.replace("-\n", "")   # Worttrennung fixen
#     #     text = text.replace("\n", " ")   # Zeilen verbinden

#     #     # Encoding-Artefakte entfernen
#     #     text = text.replace("￾", "")

#     #     return text


#     # # def _block_text_cleaning(self, text: str):
#     # #     text_0 = text.replace("-\n", "")
#     # #     text_1 = re.sub(r"[ \t]+", " ", text_0)
#     # #     text_2 = re.sub(r"\n{2,}", "\n", text_1)

#     # #     return text_2


#     # def _normalize_text(self, text: str) -> str:
#     #     # Mehrere Spaces reduzieren
#     #     text_0 = re.sub(r"\s+", " ", text)

#     #     # Absatzstruktur wieder herstellen
#     #     text_1 = re.sub(r"(?<=[.!?])\s+", "\n", text_0)

#     #     return text_1.strip()

#     # -------------------------
#     # CLEANING WORDS
#     # -------------------------
#     def _clean_word_token(self, word: str) -> str:
#         word = unicodedata.normalize("NFKC", word)
#         word = word.replace("￾", "")
#         # word = re.sub(r"\s+", " ", word)

#         # Optional: weitere Artefakte
#         word = word.strip()

#         return word


#     def _normalize_token(self, t: str) -> str:
#         t = t.lower()
#         t = re.sub(r"\d+$", "", t)          # entfernt Footnote-Zahlen
#         t = re.sub(r"[^\wäöüß]", "", t)    # entfernt Sonderzeichen

#         return t


#     def _clean_words_from_words(self,
#                      words: List[tuple]) -> List[dict]:
#         cleaned = []

#         for w in words:
#             (
#             x0, y0, x1, y1,        # position
#             text,                  # text
#             *layout     # block_no, line_no, word_no    #
#             ) = w

#             text_clean = self._clean_word_token(text)

#             # Skip leere Tokens
#             if text_clean:
#                 cleaned.append({
#                             "x0": x0,
#                             "y0": y0,
#                             "x1": x1,
#                             "y1": y1,
#                             "text": text_clean,
#                             # "block_no": block_no,
#                             # "line_no": line_no,
#                             # "word_no": word_no
#                             })

#         return cleaned


#     # -------------------------
#     # CLUSTERING / GROUPING
#     # -------------------------

#     def _merge_sources(self, words, spans):

#         # print(f"Length of 'words' | 'spans':\t{len(words)} | {len(spans)} ")

#         from src.core.memory import session

#         logger = session.logger

#         logger.info("Start merging information from both sources")
#         merged = []

#         for word in words:
#             best_span = None
#             best_overlap = 0

#             span_map = defaultdict(list)

#             for span in spans:  # spans_sorted:
#             # for word in words_sorted:
#                 # word_clean = self._normalize_token(word["text"])
#                 # span_words_clean = [self._normalize_token(w) for w in span["text"].split(" ")]

#                 y_bin_span = int(span["y0"] // 5)
#                 span_map[y_bin_span].append(span)

#                 y_bin_word = int(word["y0"] // 5)

#                 candidate_spans = (
#                                 span_map[y_bin_word - 1]
#                                 + span_map[y_bin_word]
#                                 + span_map[y_bin_word + 1]
#                                 )

#                 for span in candidate_spans:
#                     # if word_clean not in span_words_clean:
#                     #     continue

#                     overlap = self._bbox_overlap(word, span)

#                     if overlap > best_overlap:
#                         best_overlap = overlap
#                         best_span = span

#                     del overlap

#             if best_span:
#                 word.update({
#                         "font": best_span["font"],
#                         "size": best_span["size"],
#                         "flags": best_span["flags"],
#                         "color": best_span["color"],
#                         "alpha": best_span["alpha"]
#                         })
#                 # y_match = abs(float(y_span) - word["y0"]) < y_tol
#                 # bbox_match =


#                 # if bbox_match and text_match:
#                 #     y_groups[y_span].append(word)
#                 merged.append(word)

#         del spans
#         # gc.collect()

#         del words
#         # gc.collect()

#         return merged


#     def _bbox_overlap(self, a, b):

#         x_overlap = max(0,
#                         min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
#                     )
#         y_overlap = max(0,
#                         min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
#                     )

#         return x_overlap * y_overlap    #  > 0

#                     # words.update({
#                     #         "size": raw["size"],
#                     #         "alpha": raw["alpha"],
#                     #         "flags": raw["flags"],
#                     #         "font": raw["font"].lower(),
#                     #         "color": raw["color"],
#                     #         })

#         #         else:

#         #             mismatch.append({
#         #                 "raw": raw,
#         #                 "words": words
#         #                 })

#         # if mismatch:
#         #     for i, mis in mismatch:
#         #         pprint.pprint(f"mismatch line # {i}:\n", mis)


#     def _group_words_to_lines(
#                             self,
#                             words: List[dict]
#                             ) -> List[List[dict]]:
#         y_tol = self.extract_config["y_gap_words"]    # 3
#         # x_tol = self.extract_config["x_gap_words"]

#         words_sorted = sorted(
#                         words,
#                         key=lambda w: (w["y0"], w["x0"])
#                         )

#         lines = []
#         current_line = []
#         for i, w in enumerate(words_sorted):
#             if not current_line:
#                 current_line.append(w)
#                 continue

#             prev_line = current_line[-1]
#             # prev_w = words_sorted[i-1]

#             if (
#                 abs(w["y0"] - prev_line["y0"]) < y_tol
#                 # and abs(w["x0"] - prev_w["x1"]) < x_tol
#                 # and w["line_no"] == prev_w["line_no"]
#                 # and w["block_no"] == prev_w["block_no"]
#                 ):
#                 current_line.append(w)
#             # elif abs(w["x0"] - prev_w["x1"]) < x_tol:

#             else:
#                 lin_sort = sorted(current_line,
#                                 key=lambda w: w["x0"])
#                 # print("lin_sort:\t", lin_sort)

#                 lines.append(lin_sort)

#                 current_line = [w]

#         if current_line:
#             lin_sort = sorted(current_line,
#                                 key=lambda w: w["x0"])
#             # print(f"lin_sort (len={len(lin_sort)}):\t", lin_sort)

#             lines.append(lin_sort)
#             # lines.append(
#             #     sorted(current_line,
#             #     key=lambda w: w["x0"])
#             #     )

#         # print("length of lines [_group_words_to_lines()]:\t", len(lines))

#         return lines

#     # def _group_words_by_pdf_line(self,
#     #                              words: List[tuple],
#     #                              page_height) -> List[List[tuple]]:
#     #     groups = {}

#     #     for w in words:
#     #         key = (w[5], w[6])
#     #         groups.setdefault(key, []).append(w)

#     #     lines = [sorted(g, key=lambda x: x[0]) for g in groups.values()]
#     #     lines = sorted(lines, key=lambda line: (min(w[1] for w in line),
#     #                                             min(w[0] for w in line)))

#     #     final_lines = self._finalize_line(lines,
#     #                                       page_height)

#     #     return final_lines


#     # def _finalize_lines(
#     #                 self,
#     #                 lines: List[List[dict]],
#     #                 page_height: int,
#     #                 page_width: int
#     #                 ) -> List[dict]:

#     #     lines_final = []
#     #     for words in lines:
#     #         # words = [w for w in lines]
#     #         if not words:
#     #             continue

#     #         # words_sort = sorted(words, key=lambda w: w["x0"])

#     #         # text = " ".join(w["text"] for w in words_sort)

#     #         # x0_min = min(w["x0"] for w in words_sort)
#     #         # y0_min = min(w["y0"] for w in words_sort)
#     #         # x1_max = max(w["x1"] for w in words_sort)
#     #         # y1_max = max(w["y1"] for w in words_sort)

#     #         line_height = y1_max - y0_min
#     #         line_width = x1_max - x0_min

#     #         line_info = {
#     #             # "words": words_sort,
#     #             # "text": text,
#     #             # "n_chars": len(text),
#     #             # "n_words": len(words_sort),
#     #             # "n_tokens": len(self.encoder.encode(text)),

#     #             # "line_height": line_height,
#     #             # "rel_height": (y0_min / page_height),
#     #             # "line_width": line_width,
#     #             # "rel_width": (line_width / page_width),
#     #             # "x0_min": x0_min,
#     #             # "y0_min": y0_min,
#     #             # "y0_mean": np.mean([w["y0"] for w in words]),
#     #             # "x1_max": x1_max,
#     #             # "y1_max": y1_max,

#     #             "is_upper": text.isupper(),
#     #             "ends_sentence": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*$", text.strip())),
#     #             "has_punct": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*", text.strip()))
#     #             }

#     #         lines_final.append(line_info)

#     #     # w_groups_final = self._classify_w_group(groups_info)

#     #     return lines_final


#  # def build_text_from_words(self, words: List[tuple]) -> str:

#     #     words_clean = self.basic_words_cleaning(words)
#     #     # words_sorted = sorted(words_clean,
#     #     #                     key=lambda w: (round(w[1], 1),
#     #     #                                     w[0]))

#     #     lines = self._group_words_to_lines(words_clean)
#     #     k, label = self._detect_columns_from_lines(lines)

#     #     if k > 1:
#     #         lines_enriched = self._assign_columns(lines)
#     #         columns = self._group_lines_by_columns(lines_enriched)
#     #         paragraphs = self._merge_columns_to_paragraphs(columns)
#     #     else:
#     #         paragraphs = self._merge_lines_to_paragraphs(lines)

#     #     text_words = "\n\n".join([
#     #                     " ".join([
#     #                         "".join([w[4] for w in line])
#     #                         for line in para
#     #                     ])
#     #                     for para in paragraphs
#     #                 ])

#     #     return text_words
