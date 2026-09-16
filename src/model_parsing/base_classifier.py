## base_classifier.py
# import
import logging
from dataclasses import dataclass, field

from src.core.config import GeneralSettings

# from src.core.feature_enricher import FeatureEnricher
from src.core.memory import ParseContext
from src.utils.general_helper import get_file_config


@dataclass
class BaseClassifier:
    parse_context: ParseContext
    text_type: str = field(init=False)

    general_config: GeneralSettings = field(default_factory=GeneralSettings, init=False)
    classify_config: GeneralSettings = field(
        default_factory=GeneralSettings, init=False
    )
    logger: logging.Logger = field(init=False)
    bullets: set[str] = field(default_factory=lambda: {"•", "▪", "●", "‣", "◦", "–"})

    def __post_init__(self):
        # self.logger = getattr(
        #     self.parse_context,
        #     "logger",
        #     logging.getLogger(self.__class__.__name__)
        # )

        self.logger = self.parse_context.logger
        self.text_type = self.parse_context.text_type

        self.general_config = get_file_config(
            self.parse_context.general_settings, self.text_type
        )

        self.classify_config = get_file_config(
            self.parse_context.parse_settings, self.text_type
        )
        # {
        #     **self.default_config(),
        #     **getattr(self.parse_context, "classify_config", {}),
        #     **self.classify_config,
        # }

        self.setup()

    # def default_config(self) -> dict:
    #     return {}

    def setup(self):
        """Hook für Subklassen."""
        pass

    def classify_file(self):
        return
