## config.py
# import
from typing import Annotated, Literal  # Dict,

from pydantic import BaseModel, ConfigDict, Field

from src.core import _parsing_settings

# from pydantic_settings import BaseSettings, SettingsConfigDict


# ------------------------------------
# FILE_TYPE SPECIFIC PARSING SETTINGS
# ------------------------------------
class ParseFileSettings(_parsing_settings.FileFields):
    pass


class ParseDOCXSettings(_parsing_settings.DOCXFields, ParseFileSettings):
    pass


class ParseHTMLSettings(_parsing_settings.HTMLFields, ParseFileSettings):
    pass


class ParseMDSettings(ParseFileSettings):
    pass


class ParseNotebookSettings(_parsing_settings.NotebookFields, ParseFileSettings):
    pass


class ParsePDFSettings(ParseFileSettings):
    extract_source: list[str] = Field(default_factory=list)
    extraction_model: str = Field(default_factory=str)
    extract_text_info: bool = False
    extract_graphics: bool = False
    percentiles: list[float] = Field(default_factory=list)

    classify_header_footer: bool = True
    classify_foot_notes: bool = True
    classify_headings: bool = True


class ParsePlainTextSettings(ParseFileSettings):
    pass


class ParseURLSettings(ParseFileSettings):
    pass


class ParseWikiSettings(_parsing_settings.WikiFields, ParseFileSettings):
    pass


# ------------------------------------
# FILE_TYPE SPECIFIC GENERAL SETTINGS
# ------------------------------------
class GeneralFileSettings(_parsing_settings.GeneralFileFields):
    pass
    # assemble_as_md: bool = Field(default_factory=bool)
    # scrape_images: bool = Field(default_factory=bool)


class GenDOCXSettings(GeneralFileSettings):
    pass


class GenHTMLSettings(GeneralFileSettings):
    pass


class GenMDSettings(GeneralFileSettings):
    pass


class GenNotebookSettings(GeneralFileSettings):
    pass


class GenPDFSettings(_parsing_settings.PDFGeneralFields, GeneralFileSettings):
    pass


class GenPlainTextSettings(GeneralFileSettings):
    pass


class GenURLSettings(GeneralFileSettings):
    pass


class GenWikiSettings(_parsing_settings.WikiGeneralFields, GeneralFileSettings):
    pass


#     query: str = Field(default_factory=str)
#     query_time: str = Field(default_factory=str)
#     article_to_parse: List[int] = Field(default_factory=list)
#     language: Literal["en", "de"] = Field(default="en")        # Literal["en", "de"]
#     max_retries: int = Field(default=3)

# ------------------------------------
# TOP_LEVEL SETTINGS
# ------------------------------------


class ChunkSettings(_parsing_settings.ChunkFields):
    pass


class GeneralSettings(_parsing_settings.GeneralFields):
    docx: GenDOCXSettings = Field(default_factory=GenDOCXSettings)
    html: GenHTMLSettings = Field(default_factory=GenHTMLSettings)
    json_nb: GenNotebookSettings = Field(default_factory=GenNotebookSettings)
    md: GenMDSettings = Field(default_factory=GenMDSettings)
    pdf: GenPDFSettings = Field(default_factory=GenPDFSettings)
    plain_text: GenPlainTextSettings = Field(default_factory=GenPlainTextSettings)
    url: GenURLSettings = Field(default_factory=GenURLSettings)
    wiki: GenWikiSettings = Field(default_factory=GenWikiSettings)

    # env_name: str = Field(default_factory=str)
    # config_name: str = Field(default_factory=str)
    # general_config: Dict = Field(default_factory=dict)
    # extract_config: Dict = Field(default_factory=dict)


class ParseSettings(BaseModel):
    # name_log: str = Field(default_factory=str)
    # name_logfile: str = Field(default_factory=str)
    llm_model: str = Field(default_factory=str)
    url_path: list[str] | None = Field(default=None)
    file_name: str | None = Field(default=None)
    file_id: int = Field(default_factory=int)
    page_range: list[int] | Literal["all"] = Field(default="all")

    docx: ParseDOCXSettings = Field(default_factory=ParseDOCXSettings)
    html: ParseHTMLSettings = Field(default_factory=ParseHTMLSettings)
    json_nb: ParseNotebookSettings = Field(default_factory=ParseNotebookSettings)
    md: ParseMDSettings = Field(default_factory=ParseMDSettings)
    pdf: ParsePDFSettings = Field(default_factory=ParsePDFSettings)
    plain_text: ParsePlainTextSettings = Field(default_factory=ParsePlainTextSettings)
    url: ParseURLSettings = Field(default_factory=ParseURLSettings)
    wiki: ParseWikiSettings = Field(default_factory=ParseWikiSettings)

    model_config = ConfigDict(extra="forbid")


# ParseSettings_all = Annotated[
#     ParseHTMLSettings
#     | ParseNotebookSettings
#     | ParseMDSettings
#     | ParsePDFSettings
#     | ParsePlainTextSettings
#     | ParseURLSettings
#     | ParseWikiSettings,
#     Field(discriminator="meta_type"),
# ]

RunSettings = Annotated[
    ParseHTMLSettings
    | ParseNotebookSettings
    | ParseMDSettings
    | ParsePDFSettings
    | ParsePlainTextSettings
    | ParseURLSettings
    | ParseWikiSettings
    | ChunkSettings,
    Field(discriminator="meta_type"),
]
