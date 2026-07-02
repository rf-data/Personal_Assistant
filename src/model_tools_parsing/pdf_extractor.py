## text_cleaner.py
# import
import re
from collections import defaultdict
from dataclasses import dataclass  # , field
from pathlib import Path
from typing import Literal
from returns.result import Result, Success, Failure

# import numpy as np
# import gc
# import logging
import fitz  # PyMuPDF

# from src.utils.pdf_helper import extract_text_pymupdf

from src.model_classes_parsing.base_classes_parsing import (
                                            Bullet,
                                            BulletMeta,
                                            Drawing,
                                            DrawingMeta,
                                            Graphics,
                                            Image,
                                            ImageMeta,
                                            Line,
                                            LineGroup,
                                            LineSplit,
                                            PageMeta,
                                            PDFPageExtract,
                                            Span,
                                            SpanMeta,
                                            Word,
                                            WordMeta
                                                )


# from tiktoken import encoding_for_model
from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.base_extractor import BaseExtractor
from src.utils.dict_helper import save_base_model_as_dict

from src.core.memory import ParseContext

# @dataclass
# class CleaningStats:
#     total_words: int = 0
#     total_line: int = 0


@dataclass
class PDFCleanExtractor(BaseExtractor):
    bullets = {"•", "▪", "●", "‣", "◦", "–"}
    heading_prefix = (
                r"^("
                r"(?:[IVXLCDM]+)"
                r"|(?:[A-Z](?:\.\d+)*)"
                r"|(?:\d+(?:\.\d+)*)"
                r")(?:\.|\)|\])?\s+"
                )
    
    def __init__(self, 
                 enricher: FeatureEnricher, 
                 parse_context: ParseContext):
        
        self.doc_name = parse_context.run_id
        self.enricher = enricher
        self.extract_config = parse_context.parse_settings.pdf
        self.page_range = parse_context.parse_settings.page_range
        self.general_config = parse_context.general_settings.pdf
        # self.extraction_tags = run_context.general_settings.html.extraction_tags
        # self.header = run_context.header

        self.logger = parse_context.logger
        # self.parser = self.extract_config.parser
        self.save_folder = parse_context.save_folder
        self.save_name = parse_context.save_name
        self.text_type = parse_context.text_type

        return 
    

    def extract_text_per_page(
        self,
        f_path: str,
    ) -> Result[list[PDFPageExtract], str]:

        self.logger.info("Preparing text for extraction.")

        self.doc_name = Path(f_path).name
        # self.extract_config["pymupdf"] = 
        extract_fn = self._extract_text_pymupdf

        extract_graphics = self.extract_config.extract_graphics
        # ", False)
        extract_images = self.extract_config.scrape_images # ", False)
        # extract_model = self.extract_config.extraction_model   #"]

        # extract_fn = self.extract_config[extract_model]
        # extract_results = extract_fn(f_path)
        doc = fitz.open(f_path)


        pages = [(idx, page) for idx, page in enumerate(doc)
                if (self.page_range == "all" 
                    or idx in self.page_range)]
        # if self.page_range == "all":
        #     pages = [(idx, page) in range(len(doc))]

        # else:
        #     for idx, page in enumerate(doc):
        #         if idx in self.page_range:
        #             # page = doc[page_num]
        #             pages.append((idx, page))


        records = []
        # graphs = []
        # images = []
        for (idx, page) in pages:     # enumerate(doc):
            if idx % 5 == 0:
                self.logger.info("Start extracting page #%s", idx)

            self.enricher.page_height = page.rect.height
            self.enricher.page_width = page.rect.width

            extract = extract_fn(page)
            extract.page_no = idx

            if extract_graphics:
                self.logger.info(
                    "Start extracting graphics from %s (page: %s)", self.doc_name, idx
                )

                graphics = self._extract_grafics(page)
                extract.graphics = graphics
                # graphics.page_no = idx

                # graphs.append(graphics)

            if extract_images:
                self.logger.info(
                    "Start extracting images from %s (page: %s)", 
                    self.doc_name, 
                    idx
                )

                images = self._extract_images(page, idx)
                extract.images = images

            records.append(extract)

        # records_enriched = self.enricher.enrich_pages(records)
        records_enriched = self.enricher.enrich_pages(records)

        return Success(records_enriched)


    def restructure_lines(
                    self, 
                    extract: PDFPageExtract, 
                    # save: bool = False
                    ) -> Result[PDFPageExtract, str]:

        # process flow
        line_splits_all = []
        for line in extract.elements:

            # print("line (pdf_extractor l.140):", type(line), 
            #       "\n", line)
            l_splits = self._split_lines(line.elements)
            line_splits_all.append(self.enricher.enrich_lines(l_splits))

        line_splits = self._assign_columns(line_splits_all)
        # _geometric_col_assignment(segments_all)    # ments_all)

        line_splits_sort = self._sort_reading_order(line_splits)
        line_groups = self._group_splitted_lines(line_splits_sort)

        # l_group_enr = self.enricher.enrich_lines(line_groups)

        extract.elements = self.enricher.enrich_lines(line_groups)

        # texts = []
        # info = []
        # for res in results:
        #     texts.append(res["text_merge"])
        #     info.append(res["segments"])

        if "extract" in self.extract_config.save:   # save:
            # save_folder = session.state.save_folder
            # save_name = session.state.save_name
            # now = session.state.timestamp
            page_no = extract.page_no

            save_path = Path(f"{self.save_folder}/{self.save_name}_p{page_no}_extracted")

            save_base_model_as_dict(extract, 
                                    save_path)

            # text_comb = "\n\n".join(text)
            # dh.save_md_file(text_comb, f"{now}_{name_short}_text", f"{data_processed}/extract_from_words")

        return Success(extract) # , text

        #     def extract_grafics(self, page) -> GraphMeta:

        # # from src.core.memory import session

        # # doc = fitz.open(path)

        # # graphs = []
        # # for i, page in enumerate(doc):

        #     # graphs.append(
        # return GraphMeta(
        #             # graph_type = "pdf",
        #             # page_no = i+1,
        #             drawings = self._extract_drawings(page),
        #             bullets = self._extract_bullet_chars(page)
        #             )

        # return {
        #     "doc_name": Path(path).name,
        #     "meta": graphs
        #     }

    def _extract_text_pymupdf(self, page) -> PDFPageExtract:

        lines = self._extract_and_group_words(page)

        lines = self.enricher.enrich_lines(lines)
        extract = PDFPageExtract(
            doc_type="pdf",
            doc_name=self.doc_name,
            text=" ".join([l.text for l in lines]),
            # page_no = i,
            meta=PageMeta(
                height=page.rect.height,
                width=page.rect.width,
            ),
            elements=lines,
        )

        # records.append(words_processed)
        # texts.append(text)

        return extract  # , texts


    def _extract_grafics(self, page) -> Graphics:

        # from src.core.memory import session

        # doc = fitz.open(path)

        # graphs = []
        # for i, page in enumerate(doc):

        # graphs.append(
        return Graphics(
            # graph_type = "pdf",
            # page_no = i+1,
            drawings=self._extract_drawings(page),
            bullets=self._extract_bullet_chars(page),
        )

        # return {
        #     "doc_name": Path(path).name,
        #     "meta": graphs
        #     }

    # -----------------------------
    # CLEANING TEXT
    # -----------------------------

    def _clean_words_from_words(self, 
                                words: list[tuple]) -> list[Word]:
        cleaned = []

        for w in words:
            (
                x0,
                y0,
                x1,
                y1,  # position
                text,  # text
                *layout,  # block_no, line_no, word_no    #
            ) = w

            text_clean = self._clean_word_token(text)

            # Skip leere Tokens
            if text_clean:
                cleaned.append(
                    Word(
                        meta=WordMeta(x_start=x0, y_start=y0, x_end=x1, y_end=y1),
                        text=text_clean,
                    )
                )

        return cleaned

    # -----------------------------
    # EXTRACTING TEXT + NON_TEXT
    # -----------------------------
    def _extract_and_group_words(self, page) -> list[Word | Span]:

        extract_source = self.extract_config.extract_source

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

        return lines  # result, text_comb


    def _extract_images(self, page, page_no: int):
        # from src.core.memory import session

        image_list = page.get_images()

        save_folder = self.save_folder
        save_name = f"{self.save_name}_p{page_no}_extracted"

        # print the number of images found on the page
        if image_list:
            self.logger.info("Found %s images on page %s.", 
                             len(image_list), 
                             {page_no})
        else:
            self.logger.info("No images found on page %s", 
                             page_no)
            return []

        img_all = []
        for img_idx, img in enumerate(image_list, start=1):  # enumerate the image list
            xref = img[0]  # get the XREF of the image
            pix = fitz.Pixmap(page, xref)  # create a Pixmap

            if pix.n - pix.alpha > 3:  # CMYK: convert to RGB first
                pix = fitz.Pixmap(fitz.csRGB, pix)

            pix.save(
                f"{save_folder}/{save_name}_img{img_idx}.png"
            )  # save the image as png

            img_all.append(
                Image(
                    meta=ImageMeta(
                        folder=save_folder,
                        image_file=f"{save_name}_img{img_idx}",
                        text_file=save_name,
                    )
                )
            )
            pix = None

        return img_all

    #     save_folder = session.state.save_folder
    #             save_name = session.state.save_name
    #             # now = session.state.timestamp
    #             page_no = extract.page_no

    #             save_path = Path(f"{save_folder}/{save_name}_p{page_no}.json")

    #             save_base_model_as_dict(extract, save_path)

    # class Image(BaseLeaf):
    #     text: str = Field(default_factory=str)
    #     meta: Optional[ImageMeta] = Field(default_factory=ImageMeta)

    # class ImageMeta(ElementMeta):
    #     element_type: str = "image"
    #     src: str = Field(default_factory=str)
    #     downloadable: bool = Field(default_factory=bool)
    #     alt: str = Field(default_factory=str)
    #     style: str = Field(default_factory=str)
    #     text_file: str = Field(default_factory=str)
    #     folder: str = Field(default_factory=str)
    #     image_file: str = Field(default_factory=str)

    def _extract_drawings(self, page):

        self.logger.info("Start extracting drawings / vector graphics.")

        drawings = page.get_drawings()

        reduced = []
        for idx, d in enumerate(drawings):
            reduced.append(
                Drawing(
                    meta=DrawingMeta(
                        drawing_id=idx,
                        bbox=d.get("rect"),
                        fill=d.get("fill"),
                        color=d.get("color"),
                        width=d.get("width"),
                        draw_type=d.get("type"),
                        n_items=len(d.get("items", [])),
                    )
                )
            )

        return reduced  # make_json_safe(drawings)


    def _extract_bullet_chars(self, page):
        self.logger.info("Start extracting bullet chars.")

        raw = page.get_text("rawdict")
        bullets = []

        for block in raw["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for idx, char in enumerate(span.get("chars", [])):
                        if char["c"] in self.bullets:
                            bullets.append(
                                Bullet(
                                    text=char,
                                    meta=BulletMeta(
                                        bullet_id=idx,
                                        char=char,
                                        bbox=char["bbox"],
                                        origin=char["origin"],
                                    ),
                                )
                            )

        return bullets


    def _is_bullet_drawing(self, d: dict) -> bool:
        x0, y0, x1, y1 = d["bbox"]

        width = x1 - x0
        height = y1 - y0

        return (
            width < 10 and height < 10 and abs(width - height) < 2  # ~kreisförmig
        )


    def _extract_spans_from_rawdict(self, page) -> list[Span]:

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

                    line_info.append(
                        Span(
                            meta=SpanMeta(
                                size=span["size"],
                                alpha=span["alpha"],
                                flags=span["flags"],
                                font=span["font"],
                                color=span["color"],
                                x_start=bbox[0],
                                y_start=bbox[1],
                                x_end=bbox[2],
                                y_end=bbox[3],
                            ),
                            text=text_clean,
                        )
                    )

                del spans
                # gc.collect()

        return line_info

    # -------------------------
    # CLUSTERING / GROUPING
    # -------------------------

    def _merge_sources(self, words: list[Word], spans: list[Span]) -> list[Word]:

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
                word.meta.font = best_span.meta.font
                word.meta.size = best_span.meta.size
                word.meta.flags = best_span.meta.flags
                word.meta.color = best_span.meta.color
                word.meta.alpha = best_span.meta.alpha

                merged.append(word)

        del spans
        # gc.collect()

        del words
        # gc.collect()

        return merged


    def _group_words_to_lines(self, words: list[Word]) -> list[Line]:
        y_tol = self.general_config.y_gap_words  # 3
        # x_tol = self.extract_config["x_gap_words"]

        words_sorted = sorted(words, key=lambda w: (w.meta.y_start, w.meta.x_start))

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

                lines.append(Line(elements=lin_sort))

                current_line = [w]

        if current_line:
            lin_sort = sorted(current_line, key=lambda w: w.meta.x_start)
            # print(f"lin_sort (len={len(lin_sort)}):\t", lin_sort)

            lines.append(Line(elements=lin_sort))
            # lines.append(
            #     sorted(current_line,
            #     key=lambda w: w["x0"])
            #     )

        # print("length of lines [_group_words_to_lines()]:\t", len(lines))

        return lines

    # -------------------------
    # RESTRUCTURING
    # -------------------------
    def _split_lines(self, line_words: list[Word]) -> list[LineSplit]:
        x_tol = self.general_config.x_gap_words  # , 35)

        line_splits = []
        current = [line_words[0]]

        for i in range(1, len(line_words)):
            prev = line_words[i - 1]
            curr = line_words[i]

            gap = curr.meta.x_start - prev.meta.x_end

            if gap > x_tol:
                # or (gap > small_tol and token_type_change):
                line_splits.append(
                    LineSplit(elements=current, text=" ".join(c.text for c in current))
                )

                current = [curr]
            else:
                current.append(curr)

        if current:
            line_splits.append(
                LineSplit(elements=current, text=" ".join(c.text for c in current))
            )

        return line_splits



    def is_numbered_heading(self, text: str) -> bool:
        
        return bool(
                re.match(
                    self.heading_prefix, 
                    text.strip()
                    )
                    )
        #     r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\s+\S+",
        # ))


    def _group_splitted_lines(
        self, splitted_lines_sorted: list[list[LineSplit]]
    ) -> list[LineGroup]:

        paragraph_y_gap = self.general_config.y_gap_words

        # line_dict = {
        line_group = []
        current = []

        prev_top = None
        # pending = segments[0]

        for line in splitted_lines_sorted:
            # seg = s["segment"]
            # for line in line_split:
            top = min(l.meta.y_start_min for l in line)
            # bottom = max(l.meta.y_end_max for l in line)



            if prev_top is None:
                current.append(line)
            
            elif current and self.is_numbered_heading(
                                " ".join(l.text for l in current[-1])
                                ):
                line_group.append(self._finalize_splitted_lines(current))
                current = [line]
                prev_top = top
                continue

            else:
                y_delta = top - prev_top
                
                if y_delta < paragraph_y_gap:
                    current.append(line)

                else:
                    line_group.append(
                            self._finalize_splitted_lines(
                                current
                                )
                                )
                    current = [line]

            prev_top = top

        if current:
            line_group.append(self._finalize_splitted_lines(current))

        return line_group


    def _sort_reading_order(
        self, splitted_lines: list[list[LineSplit]]
    ) -> list[list[LineSplit]]:

        if not splitted_lines:
            return splitted_lines

        # if all(l["column"] is None for l in lines):
        #     return sorted(segments, key=lambda l: l["y0_mean"])

        # seg_sorted =

        def line_key(line: list[LineSplit]):
            return (
                # min(w["column"] for w in seg),
                min(l.meta.y_start_min for l in line),
                min(l.meta.x_start_min for l in line),
            )

        # seg_sorted =

        lin_sorted = sorted(splitted_lines, key=lambda line: line_key(line))
        #   : (line.meta.y_start_min,
        #                     line.meta.x_start_min)

        return lin_sorted

    # -------------------------
    # HELPER FUNCTIONS
    # -------------------------
    def _bbox_overlap(self, a: Word, b: Word) -> float:

        x_overlap = max(
            0, min(a.meta.x_end, b.meta.x_end) - max(a.meta.x_start, b.meta.x_start)
        )
        y_overlap = max(
            0, min(a.meta.y_end, b.meta.y_end) - max(a.meta.y_start, b.meta.y_start)
        )

        return x_overlap * y_overlap  #  > 0

    def _finalize_splitted_lines(
        self, splitted_lines: list[list[LineSplit]]
    ) -> LineGroup:

        text_all = []
        words_all = []
        for split_line in splitted_lines:
            # print("[DEBUG] _finalize_paragraph:\n", paragraphs[0][0])
            text = " ".join(l.text for l in split_line)
            text_all.append(text)

            for l in split_line:
                words_all.extend(l.elements)
        # for l in line)

        # n_table_lines = sum(l.get("is_table_line", False) for l in lines)

        # split_info = {

        # #     "n_cols": max([l["column"] for l in lines]),
        # #     "is_table": n_table_lines / max(len(lines), 1) > 0.5
        #     }
        # l_group =

        return LineGroup(text="\n\n".join(text_all), elements=words_all)

    # -------------------------
    # LABELLING
    # -------------------------
    def _assign_columns(
        self, splitted_lines: list[list[LineSplit]]
    ) -> list[list[LineSplit]]:

        flat_lines = []  # l.elements
        for line in splitted_lines:
            # if len(line.elements) == 1:
            # for line in line_group:

            if isinstance(line, list):
                flat_lines.extend(line)

            else:
                flat_lines.append(line)
                #  for l in line]

        x_positions = sorted(set(round(l.meta.x_start_min, 1) for l in flat_lines))
        # cluster x0_min → columns

        if len(x_positions) < 2:
            for line_group in splitted_lines:
                for line in line_group:
                    # words = line.elements
                    line.meta.column = None

            return splitted_lines

        gaps = [
            (x_positions[i + 1] - x_positions[i], x_positions[i], x_positions[i + 1])
            for i in range(len(x_positions) - 1)
        ]

        largest_gap, left_x, right_x = max(gaps, key=lambda x: x[0])
        threshold = (left_x + right_x) / 2

        for line_group in splitted_lines:
            for line in line_group:
                # words = line.elements
                line.meta.column = 0 if line.meta.x_start_min < threshold else 1
        # for line in flat_lines:
        #     for l in line.elements:
        #         l.meta.column

        return splitted_lines  # list of segments (dict)

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
