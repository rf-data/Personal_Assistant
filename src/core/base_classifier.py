## base_classifier.py
# import
import logging
from typing import Dict
from dataclasses import dataclass, field

# from src.core.feature_enricher import FeatureEnricher



@dataclass
class BaseClassifier:
    classify_config: Dict = field(default_factory=dict)
    logger = logging.getLogger(__name__)
    bullets = {"•", "▪", "●", "‣", "◦", "–"} 

    def classify_file(self):

        return 


