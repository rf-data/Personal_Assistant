## base_extractor.py
# import
import logging
from dataclasses import dataclass, field

from src.model_tools.feature_enricher import FeatureEnricher


@dataclass
class BaseCleaner:
    enricher: FeatureEnricher = field(default_factory=FeatureEnricher())
    extract_config: dict = field(default_factory=dict)
    logger = logging.getLogger(__name__)
    doc_name: str = field(default_factory=str)

    def extract(self):

        return
