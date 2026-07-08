## config.py
# import
from pydantic import BaseModel
# from pydantic_settings import BaseSettings
# import os
from pydantic import Field, ConfigDict
from typing import List, Literal, Annotated    # Dict, 

# from src.core.memory import session_state
# from src.utils.general_helper import load_env_vars
# from src.utils.dict_helper import get_yaml_config


# ------------------------------------
# FILE_TYPE SPECIFIC PARSING SETTINGS
# ------------------------------------
class ParseFileSettings(BaseModel):
    save: List[
            Literal[
                False,
                "html",
                "info",
                "md",
                True,
                "txt" 
                ]
            ] = [False]
    assemble: List[Literal["md", "txt"]]|None = None
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
    extract_source: List[str] = Field(default_factory=list)
    extraction_model: str = ""
    extract_text_info: bool = False
    extract_graphics: bool = False 
    percentiles: List[float] = Field(default_factory=list)


class ParsePlainTextSettings(ParseFileSettings):
    pass


class ParseURLSettings(ParseFileSettings):
    pass


class ParseWikiSettings(ParseFileSettings):
    query: str|None = None
    query_time: str|None = None
    query_param: Literal["page_title", "page_id"] = Field(default="page_id")
    
    page_id: List[int] = Field(default_factory=list)
    page_title: List[str] = Field(default_factory=list)
    # article_to_parse: List[int] = Field(default_factory=list)
    language: Literal["en", "de"] = Field(default="en")        # Literal["en", "de"]
    max_retries: int = Field(default=3)


# ------------------------------------
# FILE_TYPE SPECIFIC GENERAL SETTINGS
# ------------------------------------
class GeneralFileSettings(BaseModel):
    # parser: str = ""
    extraction_tags: List[str] = Field(default_factory=list)
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
    container_types: List = Field(default_factory=list) 
    # [
    #                         "heading",
    #                         "paragraph",
    #                         "code",
    #                         "bullet_list"
    #                         ]
    spacy_language: Literal[
                        "de_core_news_sm", 
                        None
                        ] = Field(default=None)
    # "",
    max_tokens: int = Field(default_factory=int)
    overlap_sentences: int = Field(default_factory=int)
    batch_size: int = Field(default_factory=int)
    transformer_model: Literal[
                        "all-MiniLM-L6-v2", 
                        None
                        ] = Field(default=None)

    model_config = ConfigDict(
        extra="forbid"
    )


class GeneralSettings(BaseModel):
    txt_elements: List[str] = Field(default_factory=list)
    md_elements: List[str] = Field(default_factory=list)

    docx: GenDOCXSettings = Field(default_factory=GenDOCXSettings)    
    html: GenHTMLSettings = Field(default_factory=GenHTMLSettings)
    json_nb: GenNotebookSettings = Field(default_factory=GenNotebookSettings)
    md: GenMDSettings = Field(default_factory=GenMDSettings)
    pdf: GenPDFSettings = Field(default_factory=GenPDFSettings)
    plain_text: GenPlainTextSettings = Field(default_factory=GenPlainTextSettings)
    url: GenURLSettings = Field(default_factory=GenURLSettings)
    wiki: GenWikiSettings = Field(default_factory=GenWikiSettings)

    model_config = ConfigDict(
        extra="forbid"
    )
    
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
    url_path: List[str] | None = Field(default=None)
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

    model_config = ConfigDict(
        extra="forbid"
    )



ParseSettings_all = Annotated[
            ParseHTMLSettings | ParseNotebookSettings | \
            ParseMDSettings | ParsePDFSettings | \
            ParsePlainTextSettings | ParseURLSettings | \
            ParseWikiSettings,
            Field(discriminator="meta_type")
            ]

RunSettings = Annotated[ParseSettings_all | ChunkSettings,
                        Field(discriminator="meta_type")]
    # def __post_init__(self):

    #     load_env_vars(name=self.env_name)
    #     raw_config = get_yaml_config(self.config_name)

    #     self.general_config = raw_config.get("general_args", {})
    #     self.extract_config = raw_config.get("extraction", {})
    #     # self.config_name 
    #     # c_path = os.getenv("CONFIG_PATH")

    #     return 
    

    # def load_from_yaml(self):
        
    #     self._create_general_config()
        

    #     return 


    # def _create_general_config(self):
        
    #     self.name_log = self.general_config.get("name_log")
    #     self.name_logfile = self.general_config.get("name_logfile")
    #     # self.

    #     return 
    

    # def _create_extraction_config(self):


    #     return 

