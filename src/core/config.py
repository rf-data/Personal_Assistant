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
# FILE_TYPE SPECIFIC RUN SETTINGS
# ------------------------------------
class RunFileSettings(BaseModel):
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


class RunHTMLSettings(RunFileSettings):
    apollo: bool = Field(default_factory=bool)
    parser: str = Field(default_factory=str)


class RunMDSettings(RunFileSettings):
    pass


class RunNotebookSettings(RunFileSettings):
    pass


class RunPDFSettings(RunFileSettings):
    extract_source: List[str] = Field(default_factory=list)
    extraction_model: str = ""
    extract_text_info: bool = False
    extract_grafics: bool = False 
    percentiles: List[float] = Field(default_factory=list)


class RunPlainTextSettings(RunFileSettings):
    pass


class RunURLSettings(RunFileSettings):
    pass


class RunWikiSettings(RunFileSettings):
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
    parser: str = ""
    extraction_tags: List[str] = Field(default_factory=list)
    # assemble_as_md: bool = Field(default_factory=bool)
    # scrape_images: bool = Field(default_factory=bool)


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
class GeneralSettings(BaseModel):
    txt_elements: List[str] = Field(default_factory=list)
    md_elements: List[str] = Field(default_factory=list)
    
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

    

class RunSettings(BaseModel):
    name_log: str = Field(default_factory=str)
    name_logfile: str = Field(default_factory=str)
    llm_model: str = Field(default_factory=str)
    url_path: List[str] | None = Field(default=None)
    file_names: List[str] | None = Field(default=None)

    html: RunHTMLSettings = Field(default_factory=RunHTMLSettings)
    json_nb: RunNotebookSettings = Field(default_factory=RunNotebookSettings)
    md: RunMDSettings = Field(default_factory=RunMDSettings)
    pdf: RunPDFSettings = Field(default_factory=RunPDFSettings)
    plain_text: RunPlainTextSettings = Field(default_factory=RunPlainTextSettings)
    url: RunURLSettings = Field(default_factory=RunURLSettings)
    wiki: RunWikiSettings = Field(default_factory=RunWikiSettings)

    model_config = ConfigDict(
        extra="forbid"
    )



RunSettings_all = Annotated[
            RunHTMLSettings | RunNotebookSettings | \
            RunMDSettings | RunPDFSettings | \
            RunPlainTextSettings | RunURLSettings | \
            RunWikiSettings,
            Field(discriminator="meta_type"),
            ]
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

