## chunk.py
# import
# import re
from collections.abc import Callable

import pandas as pd

from src.core.memory import session

# from collections import Counter
from src.utils.spacy_helper import load_spacy_model


def prepare_chunk_df(df):
    logger = session.logger
    config = session.model_config
    chunk_config = config.get("chunking", {})
    spacy_lang = chunk_config["spacy_language"]

    nlp = load_spacy_model(spacy_lang)

    df_dict = df.to_dict(orient="index")  # .copy()

    df_dict_new = []
    for idx, row in df_dict.items():
        chunks = _chunk_by_sentences(row["text"], chunk_config, nlp)

        for chunk in chunks:
            # text = ""
            #
            # for head in row["context_heading"]:
            # text = text + head + "\n"
            # chunk += chunk["text"]
            # chunk["text_aug"] = chunk_text        # f"{heading}\n{chunk["text"]}"
            row_new = row.copy()
            row_new.update(chunk)

            df_dict_new.append(row_new)

        if idx % 10 == 0:
            logger.info("Finished %s of %s df_rows:", idx, len(df_dict))

    df_chunk = pd.DataFrame(df_dict_new)

    # columns:
    # timestamp, gmp_part,
    # chapter, page, block_id,
    # text, context_heading

    # # chunk_id,
    # chunk_text,
    # chunk_len,
    # block_type,
    # section,
    # chunk_rank, # prev_chunk_id / next_chunk_id,
    # chunk_text, chunk_len,

    # OPTIONAL
    # chunk_start / chunk_end,
    # section / heading_context, has_numbers,
    # is_definition_like?,
    # semantic_density [len(unique_words) / total_words]

    return df_chunk


# def _chunk_text(text, chunk_size=300, overlap=50):
#     words = text.split()
#     chunks = []

#     for i in range(0, len(words), chunk_size - overlap):
#         chunk = words[i:i+chunk_size]

#         text = " ".join(chunk)

#         chunks.append({
#             "chunk_id": i,
#             "text_chunk": text,
#             "n_tokens": len(text)
#             })

#     return chunks


def _chunk_by_sentences(
    block_text: str, chunk_config: dict, nlp: Callable
) -> list[dict]:
    max_tokens = chunk_config["max_tokens"]

    encoder = session.encoder

    chunks = []
    current = []
    current_len = 0
    chunk_id = 1
    cursor = 0

    doc = nlp(block_text)
    for sent in doc.sents:
        tokens = len(encoder.encode(sent.text))

        if current_len + tokens > max_tokens:
            text = " ".join(current)
            n_words = len(text.split(" "))

            chunk_start = block_text.find(text, cursor)
            chunk_end = chunk_start + len(text)
            cursor = chunk_end

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_start": chunk_start,
                    "chunk_end": chunk_end,
                    "text": text,
                    # "n_chars": len(text),
                    "n_words": n_words,
                    "n_tokens": len(encoder.encode(text)),
                }
            )

            overlap_sentences = current[-2:]
            current = overlap_sentences.copy()  # []
            current_len = sum(len(encoder.encode(s)) for s in current)  #  0

            chunk_id += 1

        current.append(sent.text)
        current_len += tokens

    if current:
        text = " ".join(current)

        chunk_start = block_text.find(text, cursor)
        chunk_end = chunk_start + len(text)
        cursor = chunk_end

        chunks.append(
            {
                "chunk_id": chunk_id,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end,
                "text": text,
                "n_chars": len(text),
                "n_words": len(text.split(" ")),
                "n_tokens": len(encoder.encode(text)),
            }
        )

    return chunks
