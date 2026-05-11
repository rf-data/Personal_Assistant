## text_structure_builder.py
# import
# import unicodedata
import re
import numpy as np
# import pandas as pd
# from sklearn.cluster import KMeans
# from sklearn.metrics import silhouette_score
# import subprocess
# import gc
from typing import List, Dict   # , Optional, Any
from dataclasses import dataclass, field
from tiktoken import encoding_for_model

# from src.core.logging import create_logger
# from src.utils.spacy_helper import load_spacy_model



@dataclass
class TextStructureBuilder:
    
    # def __init__(self, f_name, preprocess_config, ):
    struct_config: Dict = field(default_factory=dict)
    # debug: bool = False
    # stats: CleaningStats = field(default_factory=CleaningStats)

        
    # -------------------------
    # Public API
    # -------------------------
    def build_structure(self, 
                        all_lines: List[dict]) -> tuple[List[Dict], List[str]]:
       
        # as lazy import to avoid circular importing
        from src.core.memory import session
        
        enricher = session.enricher

        # process flow
        segments_all = []
        for line in all_lines:
            seg = self._split_lines_into_segments(line["words"])            
            segments_all.append(enricher.enrich_lines(seg))

        segments = self._assign_columns(segments_all)
        # _geometric_col_assignment(segments_all)    # ments_all)

        segments_sort = self._sort_reading_order(segments)
        results = self._group_segments(segments_sort)
        
        texts = []
        info = []
        for res in results:
            texts.append(res["text_merge"])
            info.append(res["segments"])

        return info, texts   # , text
  

    # -------------------------
    # RESTRUCTURING  
    # -------------------------
    def _split_lines_into_segments(self, 
                                   words: List[dict]) -> List[List[dict]]:
        x_tol = self.struct_config["x_tol_line"] # , 35)

        segments = []
        current = [words[0]]

        for i in range(1, len(words)):
            prev = words[i-1]
            curr = words[i]

            gap = curr["x0"] - prev["x1"]

            if (gap > x_tol):
                # or (gap > small_tol and token_type_change):
                segments.append({
                            "words": current,
                            "text": " ".join(c["text"] for c in current)
                            })
                
                current = [curr]
            else:
                current.append(curr)
        
        if current:
            segments.append({
                        "words": current,
                        "text": " ".join(c["text"] for c in current)
                        })

        return segments
    
    
    def _group_segments(
                    self, 
                    segments_sorted: List[List[dict]]
                    ) -> List[dict]:
        
        y_tol = self.struct_config["y_tol_line"]
        
        # line_dict = {
        seg_grouped = []
        current = []

        prev_bottom = None
        # pending = segments[0]
        
        for seg in segments_sorted:
            # seg = s["segment"]

            top = min(w["y0_min"] for w in seg)
            bottom = max(w["y1_max"] for w in seg)

            if prev_bottom is None:
                current.append(seg)
            else:
                gap = top - prev_bottom

                if gap < y_tol:
                    current.append(seg)
                else:
                    seg_grouped.append(self._finalize_segments(current))
                    current = [seg]

            prev_bottom = bottom


        if current:
            seg_grouped.append(self._finalize_segments(current))

        return seg_grouped
    

    def _sort_reading_order(self, 
                            segments: List[List[dict]]):

        if not segments:
           return segments
    
        # if all(l["column"] is None for l in lines):
        #     return sorted(segments, key=lambda l: l["y0_mean"])

        # seg_sorted = 

        def segment_key(seg: List[dict]):
            return (
                # min(w["column"] for w in seg),
                min(w["y0_min"] for w in seg),
                min(w["x0_min"] for w in seg),
            )
        
        # seg_sorted = 
        
        return sorted(segments, key=segment_key)
    

    # def _group_lines_into_segments(self, 
    #                               lines: List[dict]) -> List[dict]:
        

    #     # print("[DEBUG - group_lines_into_segments]")
    #     # print(type(line))
    #     # print(line[:3] if isinstance(line, list) else line)
        
    #     if not lines:
    #         return []
        
    #     segments = []
    #     current = [lines[0]]

    #     for i in range(1, len(lines)):
    #         prev = lines[i - 1]
    #         curr = lines[i]

    #         prev_x1 = prev["x1_max"]
    #         curr_x0 = curr["x0_min"]
    #         gap = curr_x0 - prev_x1

    #         if gap > x_tol:
    #             segments.append(current)
    #             current = [curr]
    #         else:
    #             current.append(curr)

    #     if current:
    #         segments.append(current)

    #     return segments


    # def _split_lines_by_large_x_gaps(self, 
    #                                  lines: List[dict]
    #                                  ) -> List[List[dict]]:
    #     x_tol = self.struct_config["x_tol_line"] # , 35)

    #     segments = []
    #     current_segment = []

    #     lines_sorted = sorted(lines, key=lambda l: (l["y0_min"], l["x0_min"]))

    #     prev_x1 = None

    #     for line in lines_sorted:
    #         if prev_x1 is None:
    #             current_segment.append(line)
    #         else:
    #             gap = line["x0_min"] - prev_x1

    #             if gap > x_tol:
    #                 segments.append(current_segment)
    #                 current_segment = [line]
    #             else:
    #                 current_segment.append(line)

    #         prev_x1 = line["x1_max"]


    #     # lines_sort = sorted(lines, key=lambda w: (w["y0_min"], w["x0_min"]))
    #     # # for line in lines_sort:
    #     # segments = self._group_lines_into_segments(lines_sort)
        
    #     if current_segment:
    #         segments.append(current_segment)

    #     return segments
        
    # -------------------------
    # FEATURE ENRICHMENT 
    # -------------------------
    # def _finalize_segments(
    #                 self, 
    #                 segments: List[dict]
    #                 ) -> List[dict]:

    #     # line_sort = sorted(line, key=lambda w: w["y0_min"])

    #     results = []
    #     for seg in segments:
    #         # words = [w for w in lines]
    #         # if not line:
    #         #     continue

    #         text = " ".join(w["text"] for w in seg) # line_sort)

    #         x0_min = min(w["x0"] for w in seg)  # line_sort)
    #         y0_min = min(w["y0"] for w in seg)  # line_sort)
    #         x1_max = max(w["x1"] for w in seg)  # line_sort)
    #         y1_max = max(w["y1"] for w in seg)  # line_sort)

    #         segment_height = y1_max - y0_min
    #         segment_width = x1_max - x0_min
        
    #         line_info = {
    #             "text_segment": text,
    #             "words": seg, 
    #             "n_chars": len(text),
    #             "n_words": len(text.split()),
    #             "n_tokens": len(self.encoder.encode(text)),

    #             "segment_height": segment_height,
    #             "rel_height": (y0_min / self.page_height), 
    #             "segment_width": segment_width,
    #             "rel_width": (segment_width / self.page_width),
    #             "x0_min": x0_min,
    #             "y0_min": y0_min,
    #             "y0_mean": np.mean([w["y0"] for w in seg]),
    #             "x1_max": x1_max,
    #             "y1_max": y1_max,

    #             # "is_upper": text.isupper(),
    #             "ends_sentence": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*$", text.strip())),
    #             "has_punct": bool(re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*", text.strip()))
    #             }

    #         # line_info = self._detect_table_blocks(line_info, 
    #         #                                       max_width)
    #         results.append(line_info)

    #     # w_groups_final = self._classify_w_group(groups_info)

    #     return results


    def _finalize_segments(self, 
                            segments: List[List[dict]]):

        # print("[DEBUG] _finalize_paragraph:\n", paragraphs[0][0])
        text = "\n\n".join(s["text"] for seg in segments for s in seg)

        # n_table_lines = sum(l.get("is_table_line", False) for l in lines)

        segments_info = {
            "text_merge": text,
            "segments": segments
        #     "n_cols": max([l["column"] for l in lines]),
        #     "is_table": n_table_lines / max(len(lines), 1) > 0.5
            }
        
        return segments_info 
    

    # -------------------------
    # LABELLING 
    # -------------------------
    def _assign_columns(
                    self, 
                    segments_all: List[List[dict]]
                    ) -> List[List[dict]]:
        
        flat_segments = [s for line in segments_all 
                         for s in line]

        x_positions = sorted(set(round(s["x0_min"], 1) 
                                 for s in flat_segments))
        # cluster x0_min → columns


        if len(x_positions) < 2:
            for line in segments_all:
                for seg in line:
                    seg["column"] = 0
            return segments_all
        
        gaps = [
            (x_positions[i + 1] - x_positions[i], x_positions[i], x_positions[i + 1])
            for i in range(len(x_positions) - 1)
            ]

        largest_gap, left_x, right_x = max(gaps, 
                                           key=lambda x: x[0])
        threshold = (left_x + right_x) / 2

        for seg in segments_all:
            for words in seg:
                words["column"] = (
                            0 if words["x0_min"] < threshold 
                            else 1
                            )

        return segments_all     # list of segments (dict)
    
    
    
                    # [seg for seg in segments], 
                    # key=lambda s: (
                    #     s["column"],
                    #     s["y0_min"],  #  for w in seg),
                    #     s["x0_min"]   # for w in seg)
                    #     )
                    # )
    # sorted(
    #                 segments, 
    #                 key=lambda seg: (
    #                     seg["column"],
    #                     seg["y0_min"],  #  for w in seg),
    #                     seg["x0_min"]   # for w in seg)
    #                     )
    #                 )
    

        # col_groups = {}

        # for line in segments:
        #     col = line["column"]
        #     col_groups.setdefault(col, []).append(line)

        # sorted_cols = sorted(
        #                 col_groups.keys(),
        #                 key=lambda c: np.mean(
        #                                 [l["x0_min"] for l in col_groups[c]]
        #                                 )
        #                     )

        # ordered_lines = []

        # for col in sorted_cols:
        #     col_lines = sorted(col_groups[col], key=lambda l: l["y0_mean"])
        #     ordered_lines.extend(col_lines)

        # return ordered_lines
       
        # sorted(
        #         lines,
        #         key=lambda l: (l["column"] if l["column"] is not None else 0, 
        #                        l["y0_mean"])
        #     )
    
        # # verschiedene Cluster-Zahlen testen
        # best_k = 1
        # best_score = -np.inf

        # for k in range(2, max_cols + 1):
        #     kmeans = KMeans(n_clusters=k, n_init=n_init)
        #     labels = kmeans.fit_predict(x_starts)

        #     score = silhouette_score(x_starts, labels)  
        #     # kmeans.inertia_             # je kleiner desto besser

        #     if k == 1 or score < best_score:
        #         best_k = k
        #         best_score = score
        #         best_labels = labels

        # return best_k, best_labels


    # def _assign_columns(self, lines: List) -> List:

    #     # k, labels = self._detect_columns(words_clean)
    #     k, labels = self._detect_columns_from_lines(lines)
        
    #     lines_enriched = []
    #     for line, col in zip(lines, labels):

    #         text = "".join([w[4] for w in line])
    #         x0 = min(w[0] for w in line)
    #         y0 = min(w[1] for w in line)
    #         x1 = max(w[2] for w in line)
    #         y1 = max(w[3] for w in line)

    #         lines_enriched.append({
    #             "text": text,
    #             "x0": x0,
    #             "y0": y0,
    #             "x1": x1,
    #             "y1": y1,
    #             "column": col,
    #             "n_cols": k
    #         })

    #     return lines_enriched
    



        #     curr_line = segments[i]

        #     if pending["text"].endswith("-"):
        #         merged_text = self._handle_hyphen_in_line(pending["text"], 
        #                                                   curr_line["text"])  # _handle
                
        #         pending["text"] = merged_text
        #         pending["ends_sentence"] = bool(
        #                                 re.search(r"(?<!\b[A-Z])[.!?](?:[\"')\]]+)?\s*$", 
        #                                           merged_text.strip())
        #                                 )
                
        #         continue 

        #     if not current:
        #         current.append(pending)
        #     else:
        #         prev_line = current[-1]

        #         gap = pending["y0_mean"] - prev_line["y0_mean"]
        #         same_col = pending["column"] == prev_line["column"]

        #         if gap < y_tol and same_col and not prev_line["ends_sentence"]:
        #             current.append(pending)
        #         else:
        #             paragraphs.append(self._finalize_paragraph(current))
        #             current = [pending]

        #     pending = curr_line

        # if pending:
        #     if current:
        #         prev_line = current[-1]

        #         gap = pending["y0_mean"] - prev_line["y0_mean"]
        #         same_col = pending["column"] == prev_line["column"]

        #         if gap < y_tol and same_col and not prev_line["ends_sentence"]:
        #             current.append(pending)
        #         else:
        #             paragraphs.append(self._finalize_paragraph(current))
        #             current = [pending]
            
        #     else:    
        #         current = [pending]

        # if current:
        #     paragraphs.append(self._finalize_paragraph(current))

        # return paragraphs


    
    


