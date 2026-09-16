## base_extractor.py
# import
# import logging
import logging
import re
import unicodedata
from dataclasses import dataclass, field

from src.core.memory import ParseContext

# from typing import Any
from src.model_parsing.feature_enricher import FeatureEnricher
from src.utils.general_helper import get_file_config


@dataclass
class BaseExtractor:
    # enricher: FeatureEnricher = field(default_factory=FeatureEnricher())
    # extract_config: dict = field(default_factory=dict)
    # logger = logging.getLogger(__name__)
    # doc_name: str = field(default_factory=str)
    parse_context: ParseContext  #  = field(init=False)
    text_type: str = field(init=False)

    enricher: FeatureEnricher  #  = field(init=False)
    # extract_config:  = parse_context.parse_settings
    logger: logging.Logger = field(init=False)

    #  enricher: FeatureEnricher,
    #  parse_context: ParseContext

    def __post_init__(self):
        self.logger = self.parse_context.logger
        self.text_type = self.parse_context.text_type
        # self.enricher = enricher

        self.save_folder = self.parse_context.save_folder
        self.save_name = self.parse_context.save_name
        self.doc_name = self.parse_context.run_id

        self.extract_config = get_file_config(
            self.parse_context.parse_settings, self.text_type
        )
        self.general_config = get_file_config(
            self.parse_context.general_settings, self.text_type
        )
        self.setup()

        return

    def setup(self):
        """Hook für Subklassen."""
        pass

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
