## chunk.py
# import
# import re
import streamlit as st
from collections.abc import Callable
from typing import List
import pandas as pd

from src.core.memory import ParseContext

# from collections import Counter
from src.utils.spacy_helper import load_spacy_model


# df_blocks = document_json_to_blocks(json_path)
# df_chunks = prepare_chunk_df(df_blocks)
# df_chunks.to_parquet("chunks.parquet")

"""
CHUNK TECHNIQUES
(1) Fixed / Sliding Window ~
(2) Semantic ~
(3) Hierarchical ~
(4) LLM based ~
(5) Agentic ~
"""

def document_json_to_blocks(
                    doc_elements: List,
                    parse_context: ParseContext
                    ):

    blocks = []
    # → filter: paragraph, heading, code, bullets_list
    # → one row per bloc
    chunk_config = parse_context.chunk_settings
    c_types_to_filter = chunk_config.container_types
    # ["heading",
    #                             "paragraph",
    #                             "code",
    #                             "bullet_list"
    #                             ]

    for element in doc_elements:
        c_type = element.get("container_type")

        if c_type not in c_types_to_filter:
            parse_context.logger.info("[C_TYPE_MISMATCH]: %s", c_type)
            continue

        text = element.get("text", "").strip()
        if not text:
            continue
        # if element["container_type"] in c_types_to_filter:
        blocks.append({
                    "doc_id": 0,
                    "container_id": element["container_id"],
                    "container_type": element["container_type"],
                    "heading_context": element.get("meta", 
                                                   {}).get("context"),
                    "text": element["text"],
                    # "n_tokens": element.meta.n_tokens
                })

    parse_context.logger.info("Length 'blocks': %s", 
                              len(blocks))
    
    try: 
        st.write("Length 'blocks': %s", 
                              len(blocks))
    except ImportError:
        pass

    return blocks   # pd.DataFrame()

"""
doc_id
block_id / container_id
chunk_id
chunk_global_id
container_type
heading_context
chunk_text
n_tokens
chunk_start
chunk_end
"""

def prepare_chunk_df(
                blocks: List[dict], 
                parse_context: ParseContext,
                encoder
                ):

    logger = parse_context.logger

    chunk_config = parse_context.chunk_settings
    spacy_lang = chunk_config.spacy_language

    nlp = load_spacy_model(spacy_lang)

    # df_dict = df.to_dict(orient="index")  # .copy()

    chunks_all = []
    for idx, row in enumerate(blocks):

        # "doc_id": 0,
        # "block_id / container_id": element.container_id,
        #             "container_type": element.container_type,
        #             "heading_context": element.meta.context,
        #             "text": element.text,
        
        chunks = _chunk_by_sentences(
                                block_text=row["text"], 
                                chunk_config=chunk_config, 
                                encoder=encoder, 
                                nlp=nlp
                                )
        try: 
            st.write("Length 'chunks': %s", 
                    len(chunks))
        except ImportError:
            pass

        for chunk in chunks:
            # text = ""
            #
            # for head in row["context_heading"]:
            # text = text + head + "\n"
            # chunk += chunk["text"]
            # chunk["text_aug"] = chunk_text        # f"{heading}\n{chunk["text"]}"
            # row_new = row.copy()
            # row_new.update(chunk)
            # chunk["chunk_text"] = text

            chunk.update({
                    "doc_id": 0,
                    "container_id": row["container_id"],
                    "container_type": row["container_type"],
                    "heading_context": row["heading_context"],
            })

            chunks_all.append(chunk)

        if idx % 10 == 0:
            logger.info("Finished %s of %s 'blocks':", 
                        idx, 
                        len(blocks))

    df_chunk = pd.DataFrame(chunks_all)
    df_chunk["chunk_global_id"] = (
                        df_chunk["doc_id"].astype(str)
                        + "::"
                        + df_chunk["container_id"].astype(str)
                        + "::"
                        + df_chunk["chunk_id"].astype(str)
                        )
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


def _chunk_by_sentences(
    block_text: str, 
    chunk_config: dict, 
    encoder, 
    nlp: Callable
    ) -> list[dict]:
    max_tokens = chunk_config.max_tokens
    overlap_sentences = chunk_config.overlap_sentences

    # encoder = session.encoder

    chunks = []
    current = []
    current_len = 0
    chunk_id = 0
    # cursor = 0

    doc = nlp(block_text)
    for sent in doc.sents:

        sent_text = sent.text.strip()
        if not sent_text:
            continue

        sent_tokens = len(encoder.encode(sent_text))
        sent_start = sent.start_char
        sent_end = sent.end_char

        if current and current_len + sent_tokens > max_tokens:
            chunk_text = " ".join(x["text"] for x in current)
            # n_words = len(text.split(" "))

            # chunk_start = block_text.find(text, cursor)
            # chunk_end = chunk_start + len(text)
            # cursor = chunk_end

            chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_start": current[0]["start"], # chunk_start,
                    "chunk_end": current[-1]["end"], # chunk_end,
                    "chunk_text": chunk_text,
                    "n_chars": len(chunk_text),
                    "n_words": len(chunk_text.split()),
                    "n_tokens": len(encoder.encode(chunk_text)),
                })

            # overlap_sentences = current[-2:]
            # current = overlap_sentences.copy()  # []
            # current_len = sum(len(encoder.encode(s)) for s in current)  #  0
            
            current = current[-overlap_sentences:] if overlap_sentences > 0 else []
            current_len = sum(x["tokens"] for x in current)
            chunk_id += 1

        current.append({
                "text": sent_text,
                "start": sent_start,
                "end": sent_end,
                "tokens": sent_tokens,
                })
        
        current_len += sent_tokens

    if current:
        chunk_text = " ".join(x["text"] for x in current)

        # chunk_start = block_text.find(text, cursor)
        # chunk_end = chunk_start + len(text)
        # cursor = chunk_end

        chunks.append({
                "chunk_id": chunk_id,
                "chunk_start": current[0]["start"],
                "chunk_end": current[-1]["end"],
                "chunk_text": chunk_text,
                "n_chars": len(chunk_text),
                "n_words": len(chunk_text.split()),
                "n_tokens": len(encoder.encode(chunk_text)),
            })

    return chunks



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
