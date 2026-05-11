# ## extract_helper.py
# # import
# from pathlib import Path
# import re
# from typing import List, Tuple
# from tiktoken import encoding_for_model
# # import pdfplumber
# import fitz  # PyMuPDF

# from src.core.feature_enricher import FeatureEnricher
# from src.core.base_data import PageExtract
# # from src.utils.file_helper import make_json_safe


# BULLETS = {"•", "▪", "●", "‣", "◦", "–"}    # , "-"

# # def extract_blocks(page, f_name, page_num):  
# #     preprocessor = session.preprocessor

# #     height = page.rect.height
# #     blocks = page.get_text("blocks")

# #     block_info = []
# #     for k, b in enumerate(blocks):
# #         block_info = preprocessor.classify_block(b, height)

# #         block_info.update({
# #                 "file_name": f_name,
# #                 "page": page_num,
# #                 "block": k
# #                 })
                
# #     return block_info


# def extract_text_pymupdf(path):
#     from src.core.memory import session 
    
#     # get Text_preprocessor
#     extractor = session.extractor
#     # extract_config = session.model_config

#     # session.encoder = enc

#     # f_name = Path(path).stem
#     doc = fitz.open(path)

#     records = []
#     # texts = []
#     # text_records = []
#     for i, page in enumerate(doc):
#         # etxract text
#         # text_raw = page.get_text("text")  
        
#         # text_clean = " ".join([w[4] for w in text_raw.split()])

#         # # count tokens in text_clean
#         # n_tokens = len(enc.encode(text_clean))
#         # text_processed = {
#                     # "page": i,
#                     # "height_page": page.rect.height,
#                     # "width_page": page.rect.width,
#                     # "text_clean": text_clean,
#                     # "n_tokens": n_tokens
#                     # }

#         config = session.model_config
#         general_config = config.get("general_args", {})
#         model_name = general_config["llm_model"]
#         encoder = encoding_for_model(model_name)

#         page_height = page.rect.height 
#         page_width = page.rect.width 
#         text_prep_config = config.get("text_preparation", {})

#         feat_enricher = FeatureEnricher(
#                             encoder=encoder,
#                             page_height=page_height,
#                             page_width=page_width,
#                             text_prep_config=text_prep_config
#                             )
#         session.enricher = feat_enricher

#         lines = extractor.clean_and_group_words(page)

#         words_processed = PageExtract(
#                         doc_type = "pdf",
#                         text = " ".join([l.text for l in lines]),
#                         page_no = i,
#                         metadata = {
#                                 "height_page": page.rect.height,
#                                 "width_page": page.rect.width,
#                                 },
#                         elements = lines
#                             )

#         records.append(words_processed)
#         # texts.append(text)

#     return records    # , texts



# def extract_grafics(path: str | Path) -> dict:
    
#     # from src.core.memory import session 

#     doc = fitz.open(path)

#     non_text = {
#         "doc_path": str(path),
#         "graphs": []
#         }
#     for i, page in enumerate(doc):

#         non_text["graphs"].append({
#                                 "type": "pdf",
#                                 "page": i, 
#                                 "drawings": _extract_drawings(page),
#                                 "bullets": _extract_bullet_chars(page)
#                                 })
                   
#     return non_text



# def _extract_drawings(page):
#     drawings = page.get_drawings()

#     reduced = []
#     for d in drawings:

#         reduced.append({
#             "bbox": d.get("rect"),
#             "fill": d.get("fill"),
#             "color": d.get("color"),
#             "width": d.get("width"),
#             "type": d.get("type"),
#             "n_items": len(d.get("items", []))
#         })

#     return reduced  # make_json_safe(drawings)


# def _extract_bullet_chars(page):
    
#     raw = page.get_text("rawdict")
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

#     # for bul in bullets:
#     #     bul["is_bullet"] = _is_bullet_char(bul)

#     return bullets


# def _is_bullet_drawing(d: dict) -> bool:
#     x0, y0, x1, y1 = d["bbox"]
    
#     width = x1 - x0
#     height = y1 - y0
    
#     return (
#         width < 10 and
#         height < 10 and
#         abs(width - height) < 2   # ~kreisförmig
#     )

# # {
# #         # "pages": pages_records, 
# #         "words": ,
# #         # "text": text_records
# #         }


# # def extract_text_plumber(file_path: str, preprocess_config: dict) -> dict:
# #     model_name = preprocess_config["model_name"]
    
# #     pages = []
# #     with pdfplumber.open(file_path) as pdf:
# #         for i, page in enumerate(pdf.pages):
# #             text = page.extract_text(x_tolerance=2, y_tolerance=2)  # layout=True) 
            
# #             enc = encoding_for_model(model_name)
# #             n_tokens = len(enc.encode(text))
# #             pages.append({
# #                     "page": i,
# #                     "text_raw": text if text else []
# #                     })

# #     return {
# #         "pages": pages,
# #         "n_tokens": n_tokens
# #         }



# """
# Gut, dass du das hinterfragst – genau hier entscheidet sich, ob du Daten sinnvoll nutzt oder nur mitschleppst.

# Kurz gesagt:
# 👉 In der aktuellen Form bringt dir words fast nichts
# 👉 Aber: Daraus lassen sich sehr wertvolle strukturierte Features bauen

# 🧠 Was steckt wirklich in words?

# Nicht „nur Wörter“, sondern:

# (x0, y0, x1, y1, text, ...)

# 👉 Das ist Layout + Text

# Und das ist der Unterschied zwischen:

# ❌ normalem NLP
# ✅ dokumentenbasiertem Verständnis (PDF, Papers, Reports)
# 🔥 Realistisch betrachtet

# Wenn du NICHT vorhast:

# Layout-Analyse
# Tabellen-/Header-Erkennung
# wissenschaftliche Dokumente strukturieren

# 👉 dann: weg damit

# 🟢 Aber wenn du es nutzen willst…

# Dann bitte NICHT als Liste speichern, sondern als Features extrahieren

# 🧩 Sinnvolle Features aus words

# Ich gebe dir bewusst nur Dinge, die wirklich Mehrwert bringen.

# 1️⃣ Text-basierte Features (low effort, high value)
# 🔹 Durchschnittliche Wortlänge
# avg_word_len = np.mean([len(w[4]) for w in words])

# 👉 Indikator für:

# wissenschaftlicher Text vs. einfacher Text
# 🔹 Großbuchstaben-Anteil
# upper_ratio = sum(w[4].isupper() for w in words) / len(words)

# 👉 erkennt:

# Überschriften
# Akronyme
# 🔹 Zahlenanteil
# digit_ratio = sum(any(c.isdigit() for c in w[4]) for w in words) / len(words)

# 👉 erkennt:

# Tabellen
# Messwerte
# Referenzen
# 2️⃣ Layout-Features (das eigentliche Gold)
# 🔹 Textdichte (sehr stark!)
# page_area = height * width
# text_area = sum((w[2]-w[0]) * (w[3]-w[1]) for w in words)

# density = text_area / page_area

# 👉 erkennt:

# Textseite vs. Abbildung vs. Tabelle
# 🔹 Y-Position → Struktur erkennen
# y_positions = [w[1] for w in words]

# Features:

# min / max / mean
# std

# 👉 erkennt:

# Header (oben)
# Footer (unten)
# 🔹 Zeilenstruktur (wichtig!)

# Cluster nach y:

# 👉 daraus kannst du:

# Anzahl Zeilen
# Zeilenlänge
# Paragraph-Struktur

# ableiten

# 3️⃣ Semantische Layout-Features (sehr stark für dein Projekt)
# 🔹 Header Detection (extrem nützlich!)

# Heuristik:

# if word[1] < threshold and word[4].isupper():

# 👉 typische Paper-Titel:

# groß
# oben
# wenige Wörter
# 🔹 Section Detection

# Erkennen von:

# "INTRODUCTION"
# "METHODS"
# "RESULTS"

# 👉 oft:

# eigene Zeile
# Großbuchstaben
# mittige Position
# 4️⃣ Chunk-Verbesserung (das unterschätzt du gerade)

# Dein Chunking ist aktuell:

# 👉 rein textbasiert

# Mit words kannst du:

# 🔹 Layout-aware Chunking
# keine Chunk-Grenze mitten im Absatz
# keine Trennung von Überschrift + Text

# 👉 das ist MASSIV besser für LLMs

# ⚠️ Was du NICHT tun solltest
# df["words"] = words

# → das ist:

# ❌ Speicher-Müll
# ❌ nicht nutzbar
# ❌ verursacht genau deine Arrow-Probleme

# 🧭 Klare Empfehlung (ehrlich)

# Für dein aktuelles Projekt:

# 👉 Phase 1:

# DROP words

# 👉 Phase 2 (optional, wenn du weitergehst):

# Extrahiere nur:

# {
#     "text_density": ...,
#     "avg_word_len": ...,
#     "upper_ratio": ...,
#     "digit_ratio": ...,
#     "n_lines": ...,
# }

# → das reicht völlig

# 🔥 Real Talk

# Du bist gerade an einem typischen Punkt:

# „Ich habe viele Daten → also sind sie wertvoll“

# Nein.

# 👉 80% davon sind Ballast
# 👉 20% sind Features

# Deine Aufgabe ist:

# 👉 die 20% zu isolieren

# 🚀 Wenn du willst

# Ich kann dir im nächsten Schritt:

# 👉 eine Funktion bauen:

# extract_layout_features(words, page_height, page_width)
# """
