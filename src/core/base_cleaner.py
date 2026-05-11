## base_extractor.py
# import
import logging
from typing import Dict
from dataclasses import dataclass, field

from src.core.feature_enricher import FeatureEnricher


@dataclass
class BaseCleaner:

    enricher: FeatureEnricher = field(default_factory=FeatureEnricher())
    extract_config: Dict = field(default_factory=dict)
    logger = logging.getLogger(__name__)
    doc_name: str = field(default_factory=str)
    

    def extract(self):

        return 
    
