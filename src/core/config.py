## config.py
# import
from typing import Annotated, Literal  # Dict,
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# from src.core.memory import session_state
# from src.utils.general_helper import load_env_vars
# from src.utils.dict_helper import get_yaml_config


# ------------------------------------
# GENERAL SETTINGS (from .env files)
# ------------------------------------
class ParseEnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.parse",
        env_file_encoding="utf-8",
        # env_ignore_case=False
        # env_nested_delimiter="__"
    )
    app_name: str = "personal_assistant"

    # raw data
    data_dir: str
    data_audio: str
    data_docx: str
    data_html: str
    data_image: str
    data_json_nb: str
    data_pdf: str
    data_txt_md: str
    data_wiki: str
    data_qms: str

    # other folder_paths
    log_dir: str
    report_dir: str
    config_dir: str
    cache_dir: str
    chroma_dir: str

    # wikipedia relevance
    wiki_en_api: str
    header_agent: str


parsing_env_vars = ParseEnvVars()


class AIAgenticEnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.agentic",
        env_file_encoding="utf-8",
        # env_ignore_case=False
        # env_nested_delimiter="__"
    )
    app_name: str = "personal_assistant"
    
    # llm token
    hf_api_key: str
    openai_api_key: str
    # claude_token: str
    # gemini_token: str
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str
    langfuse_base_url: str


agentic_env_vars = AIAgenticEnvVars()


class MLOpsEnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.mlops",
        env_file_encoding="utf-8",
        # env_ignore_case=False
        # env_nested_delimiter="__"
    )
    app_name: str = "personal_assistant"
    # MLflow relevance
    mlflow_artifacts: str
    mlflow_db: str
    mlflow_tracking_uri: str
    mlflow_backup: str
    fingerprint_exp: str
    fingerprint_run: str

mlops_env_vars = MLOpsEnvVariables()


"""
from pydantic import BaseModel, model_validator, field_validator, Field
from typing import Optional
from datetime import date

mlops_env_vars = MLOpsEnvVars()


class OrganizerEnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.organizer",
        env_file_encoding="utf-8",
        # env_ignore_case=False
        # env_nested_delimiter="__"
    )
    app_name: str = "personal_assistant"

    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    email_rf_address: str
    email_rf_pw: str
    email_llf_address: str
    email_llf_pw: str


organizer_env_vars = OrganizerEnvVars()
# class EnvVariables(BaseSettings):
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         # env_ignore_case=False
#         # env_nested_delimiter="__"
#     )
#     app_name: str = "gmp_compliance"

#     # raw data
#     data_dir: str
#     data_audio: str
#     data_docx: str
#     data_html: str
#     data_image: str
#     data_json_nb: str
#     data_pdf: str
#     data_txt_md: str
#     data_wiki: str
#     data_qms: str

#     # other folder_paths
#     log_dir: str
#     report_dir: str
#     config_dir: str
#     cache_dir: str
#     chroma_dir: str

#     # wikipedia relevance
#     wiki_en_api: str
#     header_agent: str

#     # llm token
#     hf_api_key: str
#     openai_api_key: str
#     # claude_token: str
#     # gemini_token: str
#     langfuse_public_key: str
#     langfuse_secret_key: str
#     langfuse_host: str
#     langfuse_base_url: str

#     # MLflow relevance
#     mlflow_artifacts: str
#     mlflow_db: str
#     mlflow_tracking_uri: str
#     mlflow_backup: str
#     fingerprint_exp: str
#     fingerprint_run: str


# parsing_env_vars = EnvVariables()


"""
from pydantic import BaseModel, model_validator, field_validator, Field
from typing import Optional
from datetime import date

class DateRange(BaseModel):
    start_date: date
    end_date: date
    max_days: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        delta = (self.end_date - self.start_date).days
        if self.max_days and delta > self.max_days:
            raise ValueError(f"Range exceeds maximum of {self.max_days} days")
        return self

    @field_validator("start_date")
    @classmethod
    def start_date_not_in_past(cls, v):
        if v < date.today():
            raise ValueError("start_date cannot be in the past")
        return v

# Clean, structured validation error - not a Python exception buried in a
# traceback
range_query = DateRange(start_date=date(2025, 1, 10),
end_date=date(2025, 1, 5))
# ValidationError: end_date must be after start_date

The mode="after" argument on model_validator is the critical detail —
it means the validator runs after all individual fields are validated
and coerced to their types, so self.start_date and self.end_date are
actual date objects by the time you compare them, not raw strings.
Using mode="before" runs against raw input instead. This distinction is
the kind of thing that only surfaces when you've tried to write a
cross-field validator and gotten confusing type errors at runtime.
"""


# ------------------------------------
# FILE_TYPE SPECIFIC PARSING SETTINGS
# ------------------------------------
class ParseFileSettings(BaseModel):
    save: list[Literal[False, "html", "info", "md", True, "txt"]] = [False]
    assemble: list[Literal["md", "txt"]] | None = None
    scrape_images: bool = False


class ParseDOCXSettings(ParseFileSettings):
    tbl_text_mode: Literal["long", "brief"] = "brief"


class ParseHTMLSettings(ParseFileSettings):
    apollo: bool = Field(default_factory=bool)
    parser: str = Field(default_factory=str)


class ParseMDSettings(ParseFileSettings):
    pass


class ParseNotebookSettings(ParseFileSettings):
    parser: str = Field(default_factory=str)


class ParsePDFSettings(ParseFileSettings):
    extract_source: list[str] = Field(default_factory=list)
    extraction_model: str = ""
    extract_text_info: bool = False
    extract_graphics: bool = False
    percentiles: list[float] = Field(default_factory=list)


class ParsePlainTextSettings(ParseFileSettings):
    pass


class ParseURLSettings(ParseFileSettings):
    pass


class ParseWikiSettings(ParseFileSettings):
    query: str | None = None
    query_time: str | None = None
    query_param: Literal["page_title", "page_id"] = Field(default="page_id")

    page_id: list[int] = Field(default_factory=list)
    page_title: list[str] = Field(default_factory=list)
    # article_to_parse: List[int] = Field(default_factory=list)
    language: Literal["en", "de"] = Field(default="en")  # Literal["en", "de"]
    max_retries: int = Field(default=3)


# ------------------------------------
# FILE_TYPE SPECIFIC GENERAL SETTINGS
# ------------------------------------
class GeneralFileSettings(BaseModel):
    # parser: str = ""
    extraction_tags: list[str] = Field(default_factory=list)
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


class GenPDFSettings(GeneralFileSettings):
    y_gap_words: int = Field(default_factory=int)
    x_gap_words: int = Field(default_factory=int)

    width_thresh: float = Field(default_factory=float)
    y_gap_line: int = Field(default_factory=int)
    up_down_thresh: float = Field(default_factory=float)
    left_right_thresh: float = Field(default_factory=float)
    heading_threshold: int = Field(default_factory=int)
    foot_note_thresh: int = Field(default_factory=int)
    start_tol: int = Field(default_factory=int)


class GenPlainTextSettings(GeneralFileSettings):
    pass


class GenURLSettings(GeneralFileSettings):
    pass


class GenWikiSettings(GeneralFileSettings):
    # header_agent
    header_referer: str = ""
    header_accept: str = ""


#     query: str = Field(default_factory=str)
#     query_time: str = Field(default_factory=str)
#     article_to_parse: List[int] = Field(default_factory=list)
#     language: Literal["en", "de"] = Field(default="en")        # Literal["en", "de"]
#     max_retries: int = Field(default=3)

# ------------------------------------
# TOP_LEVEL SETTINGS
# ------------------------------------


class ChunkSettings(BaseModel):
    container_types: list = Field(default_factory=list)
    # [
    #                         "heading",
    #                         "paragraph",
    #                         "code",
    #                         "bullet_list"
    #                         ]
    spacy_language: Literal["de_core_news_sm", None] = Field(default=None)
    # "",
    max_tokens: int = Field(default_factory=int)
    overlap_sentences: int = Field(default_factory=int)
    batch_size: int = Field(default_factory=int)
    transformer_model: Literal[
        "all-MiniLM-L6-v2",
        "paraphrase-multilingual-MiniLM-L12-v2",
        "intfloat/multilingual-e5-base",
        None,
    ] = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class GeneralSettings(BaseModel):
    txt_elements: list[str] = Field(default_factory=list)
    md_elements: list[str] = Field(default_factory=list)

    docx: GenDOCXSettings = Field(default_factory=GenDOCXSettings)
    html: GenHTMLSettings = Field(default_factory=GenHTMLSettings)
    json_nb: GenNotebookSettings = Field(default_factory=GenNotebookSettings)
    md: GenMDSettings = Field(default_factory=GenMDSettings)
    pdf: GenPDFSettings = Field(default_factory=GenPDFSettings)
    plain_text: GenPlainTextSettings = Field(default_factory=GenPlainTextSettings)
    url: GenURLSettings = Field(default_factory=GenURLSettings)
    wiki: GenWikiSettings = Field(default_factory=GenWikiSettings)

    model_config = ConfigDict(extra="forbid")

    # env_name: str = Field(default_factory=str)
    # config_name: str = Field(default_factory=str)
    # general_config: Dict = Field(default_factory=dict)
    # extract_config: Dict = Field(default_factory=dict)


class NIRSettigs(BaseModel):
    n_pca_comps: int = Field(default_factory=int)
    q_quantile: float = Field(default_factory=float)
    t2_quantile: float = Field(default_factory=float)

    sg_deriv: int = Field(default_factory=int)
    sg_poly: int = Field(default_factory=int)
    sg_window_len: int = Field(default_factory=int)


class ParseSettings(BaseModel):
    name_log: str = Field(default_factory=str)
    name_logfile: str = Field(default_factory=str)
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


ParseSettings_all = Annotated[
    ParseHTMLSettings
    | ParseNotebookSettings
    | ParseMDSettings
    | ParsePDFSettings
    | ParsePlainTextSettings
    | ParseURLSettings
    | ParseWikiSettings,
    Field(discriminator="meta_type"),
]

RunSettings = Annotated[
    ParseSettings_all | ChunkSettings, Field(discriminator="meta_type")
]

