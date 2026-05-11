## llm_helper.py
# imports
import hashlib
import re
import os
from pathlib import Path
import json

import src.utils.path_helper as ph
from src.core.memory import session

def _make_cache_key(report_text: str, 
                   prompt: str, 
                   namespace: str) -> str:
    h = hashlib.sha256()
    h.update(prompt.encode("utf-8"))
    h.update(report_text.encode("utf-8"))
    h.update(namespace.encode("utf-8"))
    return h.hexdigest()


def _load_from_cache(key: str, cache_dir: Path=None):
    logger = session.logger

    if not cache_dir:
        folder = os.getenv("CACHE_DIR")
        cache_dir = Path(f"{folder}")
    
    fn = cache_dir / f"{key}.json"
    ph.ensure_dir(fn)
    
    if fn.exists():
        with open(fn) as f:
            logger.info("Loading cached json: %s",
                        ph.shorten_path(fn))
            return json.load(f)
        
    return None


def _save_to_cache(key: str, data: dict, cache_dir: Path=None):
    logger = session.logger

    if not cache_dir:
        cache_dir = Path(os.getenv("CACHE_DIR"))

    fn = cache_dir / f"{key}.json"
    ph.ensure_dir(fn)
    
    with open(fn, "w") as f:
        logger.info("Saving LLM response as cached json: %s",
                        ph.shorten_path(fn))
        json.dump(data, f, indent=2)


def _clean_llm_output(text: str) -> str:
    text = text.strip()

    # remove ```json ... ```
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    # if text.startswith("```"):
    #     text = text.split("```")[1]  # nimmt den mittleren Teil

    return text.strip()


def build_llm_aggregation_input(docs, agg):
    payload = []

    for i, doc in enumerate(docs, start=1):
        payload.append({
            "document_id": i,
            "title": doc.title,
            "category": doc.category,
            "summary": doc.summary,
            "key_entities": doc.key_entities,
            "key_findings": doc.key_findings,
            "methods": doc.methods,
            "main_topics": getattr(doc, "main_topics", []),
            "mechanisms": getattr(doc, "mechanisms", []),
            "outcomes": getattr(doc, "outcomes", []),
            "missing_fields": getattr(doc, "missing_fields", []),
            "review_flags": getattr(doc, "review_flags", []),
            "quality_assessment": getattr(doc, "quality_assessment", None),
            "confidence": doc.confidence
        })

    response = {
        "documents": payload,
        "pre_aggregation": agg.model_dump()
        }
    
    return json.dumps(response, indent=2, ensure_ascii=False)

# def cached_single(texts: str) -> dict:
#     key = make_cache_key(texts, 
#                         prompt, 
#                         namespace)
#     cached = load_from_cache(key)
#     if cached is not None:
#         return cached

#     result = single_escalation_by_llm(
#                                     text=texts,
#                                     prompt=prompt,
#                                     scheme=scheme,
#                                     allowed_values=allowed_values,
#                                 )
            
#     save_to_cache(key, result)
            
#     return result

#     return cached_single
    
