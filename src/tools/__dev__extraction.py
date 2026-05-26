## text_extraction.py
# import
# import re
# import gc

# from gmp_compliance.src.core.text_cleaner import TextCleaner
from src.core.memory import session

# from datetime import datetime
# from collections import defaultdict
# import os
# from pathlib import Path
# import numpy as np
# import pandas as pd
from src.utils.pdf_helper import extract_text_pymupdf

# from src.tools.cleaning import detect_repeated_lines

# import src.utils.file_helper as fh


# def _extraction_quality(text: List | str):

#     if isinstance(text, str):
#         text = [text]

#     for i, t in enumerate(text):
#         words = t.split()

#         avg_len = np.mean([len(w) for w in words])
#         long_words_10 = [w for w in words if len(w) > 10]
#         long_words_20 = [w for w in words if len(w) > 20]

#         print(f"Text # {i}")
#         print("avg_len:", avg_len)
#         print("long_words (> 10 / > 20):\n - ", long_words_10, "\n - ", long_words_20)

#     return


# ------------------
# MAIN FUNCTION
# ------------------
EXTRACT_DICT = {
    # "plumber": extract_text_plumber,
    "pymupdf": extract_text_pymupdf
}


def extract_text_per_page(
    f_path: str,
) -> list[dict]:
    config = session.model_config
    logger = session.logger
    logger.info("Preparing text for extraction.")

    extract_model = config.get("extraction", {})["extraction_model"]

    extract_fn = EXTRACT_DICT[extract_model]
    extract_results = extract_fn(f_path)

    return extract_results  # , text


# import fitz  # PyMuPDF


# repeated_lines = detect_repeated_lines(pages)
# print("[DEBUG] Repeated Lines:")
# print("count: ", len(repeated_lines))
# print("First 10 lines:")
# for line in list(repeated_lines)[:10]:
#     print(repr(line))

# new_text = {}    # defaultdict(dict)
# for word in words:
#     i = word["page"]
#     # k = word["block"]
#     block_texts = pre_processor.layout_aware_preparation(word)

#     word["text_block"] =  block_texts

#     if new_text[f"page_{i}"]:
#         new_text[f"page_{i}"].append(word)
#     else:
#         new_text[f"page_{i}"] = [word]

# page_records = []
# chunk_records = []
# for p in pages:
#     n_page = p["page"]

#     # p["text_new"] = new_text[f"page_{n_page}"]
#     text_list = new_text[f"page_{n_page}"]
#     text = [t for t in text_list["text_block"]]

# text_chunks = []
# for t in text:
#     # clean text
#     t_clean = pre_processor.clean(t, repeated_lines)
#     _extraction_quality(t_clean)

#      # semantic chunking
#     t_chunks = pre_processor.semantic_chunking(t_clean)

#     text_chunks.append(t_chunks)

# text_chunks.append(t_chunks)

# for ch in text_chunks:
#     chunk = str(ch["text_chunk"])

#     chunk_records.append({
#                 "extract_model": extract_model,
#                 "chunk_id": f"{f_name}_p{n_page}_{ch['chunk_id']}",
#                 "document_name": f_name,
#                 "page": n_page,
#                 "text_chunk": chunk,
#                 "text_chunk_lower": chunk.lower(),
#                 "n_words": len(chunk.split()),
#                 "n_tokens": ch["n_tokens"]
#                 })

# return {
#     "pages": page_records,
#     "chunks": chunk_records,
#     "words": extract_dict.get("words", [])
#     }

#####################
# page_records = []
# chunk_records = []
# for p in pages:
#     n_page = p["page"]

#     text = p["text_raw"]

#     if int(n_page) > 0:
#         print()

#     p["extract_model"] = extract_model
#     page_records.append(p)

#     now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     print(f"=== PROCESSING PAGE {n_page} ({now}) ===")

#     # clean text
#     text_clean = pre_processor.clean(text, repeated_lines)
#     _extraction_quality(text_clean)

#     # semantic chunking
#     text_chunks = pre_processor.semantic_chunking(text_clean)

#     for ch in text_chunks:
#         chunk = str(ch["text_chunk"])

#         chunk_records.append({
#                 "extract_model": extract_model,
#                 "chunk_id": f"{f_name}_p{n_page}_{ch['chunk_id']}",
#                 "document_name": f_name,
#                 "page": n_page,
#                 "text_chunk": chunk,
#                 "text_chunk_lower": chunk.lower(),
#                 "n_words": len(chunk.split()),
#                 "n_tokens": ch["n_tokens"]
#                 })

# return {
#     "pages": page_records,
#     "chunks": chunk_records,
#     "words": extract_dict.get("words", [])
#     }

# if __name__ == "__main__":
#     extract_per_page()
# extract.append(page_dict)

# def layout_aware_extraction(extract_dict, pre_processor):
#     # setup logger
#     logger = session.logger
#     logger.info("Preparing text for layout_aware extraction.")

#     words = extract_dict["words"]
#     pages = extract_dict["pages"]

#     new_text = {}    # defaultdict(dict)
#     for word in words:
#         i = word["page"]
#         # k = word["block"]
#         block_texts = pre_processor.layout_aware_preparation(word)

#         word["text_block"] =  block_texts

#         if new_text[f"page_{i}"]:
#             new_text[f"page_{i}"].append(word)
#         else:
#             new_text[f"page_{i}"] = [word]

#     page_records = []
#     chunk_records = []
#     for p in pages:
#         n_page = p["page"]

#         # p["text_new"] = new_text[f"page_{n_page}"]
#         text_list = new_text[f"page_{n_page}"]
#         text = [t for t in text_list["text_block"]]

#     text_chunks = []
#     for t in text:
#         # clean text
#         t_clean = pre_processor.clean(t, repeated_lines)
#         _extraction_quality(t_clean)

#          # semantic chunking
#         t_chunks = pre_processor.semantic_chunking(t_clean)

#         text_chunks.append(t_chunks)

#     text_chunks.append(t_chunks)

#     for ch in text_chunks:
#         chunk = str(ch["text_chunk"])

#         chunk_records.append({
#                     "extract_model": extract_model,
#                     "chunk_id": f"{f_name}_p{n_page}_{ch['chunk_id']}",
#                     "document_name": f_name,
#                     "page": n_page,
#                     "text_chunk": chunk,
#                     "text_chunk_lower": chunk.lower(),
#                     "n_words": len(chunk.split()),
#                     "n_tokens": ch["n_tokens"]
#                     })

#     return {
#         "pages": page_records,
#         "chunks": chunk_records,
#         "words": extract_dict.get("words", [])
#         }

# text_rep = remove_repeated_lines(text_repaired, repeat_lines)
# text_spacy_repeat = cleaner.chunk_by_spacy(text_rep)
# print(f"{'=='*15} REMOVE REPEATED LINES {'=='*15} ")
# _extraction_quality(text_spacy_repeat["sentences"])

# text_removed = remove_noise(text_repaired)
# text_spacy_removed = cleaner.chunk_by_spacy(text_removed)
# print(f"{'=='*15} REMOVE NOISE {'=='*15} ")
# _extraction_quality(text_spacy_removed["sentences"])

# text_cutoff = header_footer_cutoff(text_repaired)
# text_spacy_cutoff = cleaner.chunk_by_spacy(text_cutoff)
# print(f"{'=='*15} HEADER / FOOTER CUT-OFF {'=='*15} ")
# _extraction_quality(text_spacy_cutoff["sentences"])

# text_dict.update({
# "no_change": text_spacy,
# "text": text_spacy_repeat["sentences"],
# "noise_removal": text_spacy_removed["sentences"],
# "cutoff": text_spacy_cutoff["sentences"]
# })
# "document_name": f_name,

# sentences =

# if len(text_blocks) > 1:
#     for k, chunk in enumerate(text_blocks):
#         text_dict["text"].append({
#                 "chunk_id": f"page_{i}_chunk_{k}",
#                 f"chunk_{k}": chunk
#                 })

# elif len(text_blocks) == 1:
#     text_dict["text"] = text_blocks

# else:
#     raise ValueError("'text_blocks' is empty.")


# info = {
#     "white_list": [],     # preprocess_config["whitelist"]
#     }
