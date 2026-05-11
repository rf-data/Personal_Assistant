## text_cleaner.py
# import
from collections import defaultdict
from pathlib import Path
# import gc
# import logging
import fitz  # PyMuPDF
# import numpy as np
from typing import List # , Dict, Optional # Any
from dataclasses import dataclass       # , field
# from tiktoken import encoding_for_model

from src.core.feature_enricher import FeatureEnricher
from src.core.base_extractor import BaseExtractor
# from src.utils.pdf_helper import extract_text_pymupdf
from src.core.data_classes import (Span, SpanMeta,
                                   Word, WordMeta,
                                   Line, # LineMeta,
                                   PageExtract, PageMeta,
                                   DrawMeta, GraphMeta, BulletMeta)

# @dataclass
# class CleaningStats:
#     total_words: int = 0
#     total_line: int = 0


@dataclass
class PDFCleanExtractor(BaseExtractor):
    
    bullets = {"•", "▪", "●", "‣", "◦", "–"} 

    def extract_text_per_page(
                        self,
                        f_path:str, 
                        ) -> List[Line]:
        
        self.logger.info("Preparing text for extraction.")       
        

        extract_model = self.extract_config["extraction_model"]

        extract_fn = self.extract_config[extract_model]
        # extract_results = extract_fn(f_path)  
        doc = fitz.open(f_path)

        self.doc_name = Path(f_path).name
        self.extract_config["pymupdf"] = self.extract_text_pymupdf

        records = []
        for idx, page in enumerate(doc):
            
            self.enricher = FeatureEnricher(
                                encoder=session.encoder,
                                page_height=page.rect.height ,
                                page_width=page.rect.width,
                                text_prep_config=self.extract_config
                                )
            # session.enricher = feat_enricher

            extract = extract_fn(page)
            extract.page = idx

            records.append(extract)

        return records 
    

    def extract_text_pymupdf(self, page) -> PageExtract:

        lines = self._extract_and_group_words(page)
        # enricher = session.enricher
        
        lines = self.enricher.enrich_lines(lines)
        extract = PageExtract(
                            doc_type = "pdf",
                            doc_name = self.doc_name,
                            text = " ".join([l.text for l in lines]),
                            # page_no = i,
                            meta = PageMeta(
                                height = page.rect.height,
                                width = page.rect.width,
                                    ),
                            elements = lines
                                )

            # records.append(words_processed)
            # texts.append(text)

        return extract    # , texts


    def extract_grafics(self, path: str | Path) -> dict:
        
        # from src.core.memory import session 

        doc = fitz.open(path)

        graphs = []
        for i, page in enumerate(doc):

            graphs.append(
                        GraphMeta(
                            graph_type = "pdf",
                            page_no = i+1, 
                            drawings = self._extract_drawings(page),
                            bullets = self._extract_bullet_chars(page)
                            ))
                    
        return {
            "doc_name": Path(path).name,
            "meta": graphs
            }

    # -----------------------------
    # CLEANING TEXT
    # -----------------------------

    def _clean_words_from_words(self, 
                     words: List[tuple]) -> List[Word]:
        cleaned = []
        
        for w in words:
            (
            x0, y0, x1, y1,        # position
            text,                  # text
            *layout     # block_no, line_no, word_no    # 
            ) = w
            
            text_clean = self._clean_word_token(text)
            
            # Skip leere Tokens
            if text_clean:
                cleaned.append(Word(
                            meta = WordMeta(
                                x_start = x0, 
                                y_start = y0, 
                                x_end = x1, 
                                y_end = y1, 
                                text = text_clean
                                ) 
                        ))
                
        return cleaned
    
    # -----------------------------
    # EXTRACTING TEXT + NON_TEXT
    # -----------------------------
    def _extract_and_group_words(self, page) -> List[Word] | List[Span]:
        
        extract_source = self.extract_config["extract_source"]

        if "words" in extract_source:
            words = page.get_text("words") 
            words = self._clean_words_from_words(words)
            # lines = self._group_words_to_lines(words)

            if "raw_dict" in extract_source:
                spans = self._extract_spans_from_rawdict(page)
                words = self._merge_sources(words, spans)
            
            lines = self._group_words_to_lines(words)

        elif "raw_dict" in extract_source:
            lines = self._extract_spans_from_rawdict(page)
       
        else:
            raise ValueError()
            # sys.exit()
            # return None
        # self._finalize_lines()

        # # encoder = session.encoder
        # if isinstance(lines_fin, list):
        #     text_comb = "\n".join([l["text"] for l in lines_fin])
        # else: 
        #     text_comb = lines_fin

        # result = {
        #     "n_words": len(words),
        #     "n_tokens": len(self.encoder.encode(text_comb)),
        #     "n_lines": len(lines_fin), 
        #     # "words": words,
        #     "lines": lines_fin,
        #     }
        
        return lines    # result, text_comb 


    def _extract_drawings(self, page):
        drawings = page.get_drawings()

        reduced = []
        for idx, d in enumerate(drawings):

            reduced.append(
                    DrawMeta(
                        drawing_id = idx,
                        bbox = d.get("rect"),
                        fill = d.get("fill"),
                        color = d.get("color"),
                        width = d.get("width"),
                        draw_type = d.get("type"),
                        n_items = len(d.get("items", []))
                        ))

        return reduced  # make_json_safe(drawings)


    def _extract_bullet_chars(self, page):
        
        raw = page.get_text("rawdict")
        bullets = []

        for block in raw["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for idx, char in enumerate(span.get("chars", [])):
                        if char["c"] in self.bullets:

                            bullets.append(
                                        BulletMeta(
                                            bullet_id = idx,
                                            char = char,
                                            bbox = char["bbox"],
                                            origin = char["origin"]
                                        ))

        return bullets


    def _is_bullet_drawing(self, d: dict) -> bool:
        x0, y0, x1, y1 = d["bbox"]
        
        width = x1 - x0
        height = y1 - y0
        
        return (
            width < 10 and
            height < 10 and
            abs(width - height) < 2   # ~kreisförmig
        )


    def _extract_spans_from_rawdict(self, page) -> List[Span]:

        raw = page.get_text("rawdict")

        line_info = []
        for block in raw["blocks"]:
            for line in block.get("lines", []):
                
                spans = line.get("spans", [])
                    
                for span in spans:
                    bbox = span["bbox"]

                    chars = [c["c"] for c in span["chars"]]
                    text = "".join(chars)
                    text_clean = self._clean_word_token(text)
                    
                    line_info.append(Span(
                                meta = SpanMeta(
                                    size = span["size"], 
                                    alpha = span["alpha"],
                                    flags = span["flags"],
                                    font = span["font"],
                                    color = span["color"],
                                    x_start = bbox[0],
                                    y_start = bbox[1],
                                    x_end = bbox[2],
                                    y_end = bbox[3]
                                    ),
                                text = text_clean
                            ))

                del spans
                # gc.collect()
        
        return line_info

    # -------------------------
    # CLUSTERING / GROUPING 
    # -------------------------
   
    def _merge_sources(self, 
                       words: List[Word], 
                       spans: List[Span]
                       ) -> List[Word]:
            
        # print(f"Length of 'words' | 'spans':\t{len(words)} | {len(spans)} ")
        
        self.logger.info("Start merging information from both sources")
        merged = []

        for word in words:
            best_span = None
            best_overlap = 0

            span_map = defaultdict(list)

            for span in spans:  # spans_sorted:
            # for word in words_sorted:
                # word_clean = self._normalize_token(word["text"])
                # span_words_clean = [self._normalize_token(w) for w in span["text"].split(" ")]

                y_bin_span = int(span.meta.y_start // 5)
                span_map[y_bin_span].append(span)

                y_bin_word = int(word.meta.y_start // 5)

                candidate_spans = (
                                span_map[y_bin_word - 1]
                                + span_map[y_bin_word]
                                + span_map[y_bin_word + 1]
                                )

                for span in candidate_spans:
                    # if word_clean not in span_words_clean:
                    #     continue

                    overlap = self._bbox_overlap(word, span)

                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_span = span

                    del overlap

            if best_span:
                word.meta.font = best_span["font"]
                word.meta.size = best_span["size"]
                word.meta.flags = best_span["flags"]
                word.meta.color = best_span["color"]
                word.meta.alpha = best_span["alpha"]
                
                merged.append(word)

        del spans
        # gc.collect()
            
        del words
        # gc.collect()

        return merged



    def _group_words_to_lines(
                            self, 
                            words: List[Word]
                            ) -> List[Word]:
        y_tol = self.extract_config["y_gap_words"]    # 3
        # x_tol = self.extract_config["x_gap_words"]

        words_sorted = sorted(
                        words, 
                        key=lambda w: (w.meta.y_start, w.meta.x_start)
                        )     
        
        lines = []
        current_line = []
        for i, w in enumerate(words_sorted):
            if not current_line:
                current_line.append(w)
                continue
            
            prev_line = current_line[-1]
            # prev_w = words_sorted[i-1]

            if (
                abs(w.meta.y_start - prev_line.meta.y_start) < y_tol
                # and abs(w["x0"] - prev_w["x1"]) < x_tol
                # and w["line_no"] == prev_w["line_no"]
                # and w["block_no"] == prev_w["block_no"]
                ):
                current_line.append(w)
            # elif abs(w["x0"] - prev_w["x1"]) < x_tol:

            else:
                lin_sort = sorted(current_line,
                                key=lambda w: w.meta.x_start) 
                # print("lin_sort:\t", lin_sort)

                lines.append(lin_sort)

                current_line = [w]

        if current_line:
            lin_sort = sorted(current_line,
                                key=lambda w: w.meta.x_start) 
            # print(f"lin_sort (len={len(lin_sort)}):\t", lin_sort)
                
            lines.append(lin_sort)
            # lines.append(
            #     sorted(current_line,
            #     key=lambda w: w["x0"])    
            #     )
        
        # print("length of lines [_group_words_to_lines()]:\t", len(lines))
        
        return lines

    # -------------------------
    # HELPER FUNCTIONS
    # -------------------------
    def _bbox_overlap(self, a: Word, b: Word) -> float:

        x_overlap = max(0, 
                        min(a.meta.x_end, 
                            b.meta.x_end) - max(a.meta.x_start, 
                                                b.meta.x_start)
                    )
        y_overlap = max(0,
                        min(a.meta.y_end, 
                            b.meta.y_end) - max(a.meta.y_start, 
                                                b.meta.y_start)
                    )

        return x_overlap * y_overlap    #  > 0

                    # words.update({
                    #         "size": raw["size"],
                    #         "alpha": raw["alpha"],
                    #         "flags": raw["flags"],
                    #         "font": raw["font"].lower(),
                    #         "color": raw["color"],
                    #         })
                    
        #         else:

        #             mismatch.append({
        #                 "raw": raw,
        #                 "words": words
        #                 })
                    
        # if mismatch:     
        #     for i, mis in mismatch:                    
        #         pprint.pprint(f"mismatch line # {i}:\n", mis)

        
    

    # def _group_words_by_pdf_line(self, 
    #                              words: List[tuple],
    #                              page_height) -> List[List[tuple]]:
    #     groups = {}

    #     for w in words:
    #         key = (w[5], w[6]) 
    #         groups.setdefault(key, []).append(w)

    #     lines = [sorted(g, key=lambda x: x[0]) for g in groups.values()]
    #     lines = sorted(lines, key=lambda line: (min(w[1] for w in line), 
    #                                             min(w[0] for w in line)))

    #     final_lines = self._finalize_line(lines, 
    #                                       page_height)

    #     return final_lines
     

    # def _finalize_lines(
    #                 self, 
    #                 lines: List[List[dict]],
    #                 page_height: int,
    #                 page_width: int
    #                 ) -> List[dict]:

    #     lines_final = []
    #     for words in lines:
    #         # words = [w for w in lines]
    #         if not words:
    #             continue

    #         # words_sort = sorted(words, key=lambda w: w["x0"])

    #         # text = " ".join(w["text"] for w in words_sort)

    #         # x0_min = min(w["x0"] for w in words_sort)
    #         # y0_min = min(w["y0"] for w in words_sort)
    #         # x1_max = max(w["x1"] for w in words_sort)
    #         # y1_max = max(w["y1"] for w in words_sort)

    #         line_height = y1_max - y0_min
    #         line_width = x1_max - x0_min
        
    #         line_info = {
    #             # "words": words_sort,
    #             # "text": text,
    #             # "n_chars": len(text),
    #             # "n_words": len(words_sort),
    #             # "n_tokens": len(self.encoder.encode(text)),

    #             # "line_height": line_height,
    #             # "rel_height": (y0_min / page_height), 
    #             # "line_width": line_width,
    #             # "rel_width": (line_width / page_width),
    #             # "x0_min": x0_min,
    #             # "y0_min": y0_min,
    #             # "y0_mean": np.mean([w["y0"] for w in words]),
    #             # "x1_max": x1_max,
    #             # "y1_max": y1_max,

    #             "is_upper": text.isupper(),
    #             "ends_sentence": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*$", text.strip())),
    #             "has_punct": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*", text.strip()))
    #             }
        
    #         lines_final.append(line_info)

    #     # w_groups_final = self._classify_w_group(groups_info)

    #     return lines_final


 # def build_text_from_words(self, words: List[tuple]) -> str:

    #     words_clean = self.basic_words_cleaning(words)
    #     # words_sorted = sorted(words_clean, 
    #     #                     key=lambda w: (round(w[1], 1), 
    #     #                                     w[0]))

    #     lines = self._group_words_to_lines(words_clean)
    #     k, label = self._detect_columns_from_lines(lines)

    #     if k > 1:
    #         lines_enriched = self._assign_columns(lines)
    #         columns = self._group_lines_by_columns(lines_enriched)
    #         paragraphs = self._merge_columns_to_paragraphs(columns)
    #     else:
    #         paragraphs = self._merge_lines_to_paragraphs(lines)

    #     text_words = "\n\n".join([
    #                     " ".join([
    #                         "".join([w[4] for w in line])
    #                         for line in para
    #                     ])
    #                     for para in paragraphs
    #                 ])

    #     return text_words