## base_extractor.py
# import
# import logging
import re
import unicodedata
from dataclasses import dataclass   # , field

from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.core.memory import ParseContext


@dataclass
class BaseExtractor:
    # enricher: FeatureEnricher = field(default_factory=FeatureEnricher())
    # extract_config: dict = field(default_factory=dict)
    # logger = logging.getLogger(__name__)
    # doc_name: str = field(default_factory=str)

    def __init__(self, 
                 enricher: FeatureEnricher, 
                 parse_context: ParseContext):
        self.enricher = enricher

        self.extract_config = parse_context.parse_settings
        self.logger = parse_context.logger
        

        return 


    def extract(self):

        return

    # -------------------------
    # CLEANING WORDS
    # -------------------------
    def _clean_word_token(self, word: str) -> str:
        word = unicodedata.normalize("NFKC", word)
        word = re.sub(r"[\￾\﻿]", "", word)

        # word = re.sub(r"\s+", " ", word)

        # Optional: weitere Artefakte
        word = word.strip()

        return word

    def _normalize_token(self, t: str) -> str:
        t = t.lower()
        t = re.sub(r"\d+$", "", t)  # entfernt Footnote-Zahlen
        t = re.sub(r"[^\wäöüß]", "", t)  # entfernt Sonderzeichen

        return t
