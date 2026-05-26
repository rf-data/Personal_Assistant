## config.py
# import
from pydantic_settings import BaseSettings
import os

from src.core.memory import session_state
from src.utils.general_helper import load_env_vars
from src.utils.dict_helper import get_yaml_config




class Settings(BaseSettings):
    env_name: str = Field(default_factory=str)
    config_name: str = Field(default_factory=str)
    general_config: Dict = Field(default_factory=dict)
    extract_config: Dict = Field(default_factory=dict)

    name_log: str = Field(default_factory=str)
    name_logfile: str = Field(default_factory=str)



    def __post_init__(self):

        load_env_vars(name=self.env_name)
        raw_config = get_yaml_config(self.config_name)

        self.general_config = raw_config.get("general_args", {})
        self.extract_config = raw_config.get("extraction", {})
        # self.config_name 
        # c_path = os.getenv("CONFIG_PATH")

        return 
    

    def load_from_yaml(self):
        
        self._create_general_config()
        

        return 


    def _create_general_config(self):
        
        self.name_log = self.general_config.get("name_log")
        self.name_logfile = self.general_config.get("name_logfile")
        # self.

        return 
    

    def _create_extraction_config(self):


        return 