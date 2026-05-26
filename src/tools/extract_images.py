## extract_images.py
# import
import re
from pathlib import Path

from src.core.logger import create_logger
from src.core.memory import session_state
from src.utils.dict_helper import (
    get_yaml_config,
    load_dict,  # , shorten_path
    save_dict,
)

# from src.model_parsing.data_classes_parsing import Element
from src.utils.general_helper import load_env_vars
from src.utils.path_helper import list_files

# ------------------
# MAIN FUNCTION
# ------------------


def scrape_images_from_url():
    # load env variables and config
    load_env_vars()

    config_name = input("Enter 'config_file' name (no suffix): ")
    config = get_yaml_config(config_name)
    session_state.model_config = config

    return run_scrape_images_from_url(config)


def run_scrape_images_from_url(config):
    # url: Optional[str | List],
    # f_path: Optional[str | Path | List],
    # folder: Optional[str | Path | List]

    # from src.core.memory import session
    # logger = session.logger

    data_processed = Path(
        "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/processed"
    )
    general_config = config.get("general_args", {})
    url = general_config.get("url", None)
    f_path = general_config.get("file_name", None)
    folder = general_config.get("folder_name", None)
    log_name = general_config["name_log"]
    name_logfile = general_config["name_logfile"]

    # setup logger
    logger = create_logger(name=log_name, file_name=name_logfile)
    session.logger = logger

    urls = []
    if url is not None:
        if isinstance(url, str):
            urls.append(url)

        elif isinstance(url, list):
            urls.extend(url)
        # urls.extend(url)
        logger.info("Extracted %s urls from config", len(url))

    folder_list = []
    if f_path is not None:
        folder_list.extend(f_path)
        logger.info(
            "Extracted %s f_path (type=%s) from config", type(f_path), len(f_path)
        )

    if folder is not None:
        if isinstance(folder, list):
            for fold in folder:
                folder_list.append(data_processed / fold)
        elif isinstance(folder, (str, Path)):
            folder_list.append(data_processed / folder)

        logger.info(
            "Extracted %s folder (type=%s) from config", len(folder), type(folder)
        )

    logger.info("'folder_list' contains %s paths", len(folder_list))

    if len(folder_list) > 0:
        files = list_files(folder=folder_list, suffix="json")

        if isinstance(files, (str, Path)):
            files = [files]

        img_urls = []
        for file in files:
            extract_dict = load_dict(file)

            elements = extract_dict.get("elements", [])
            img_urls.extend(_extract_image_urls(elements))

        logger.info("Found %s image_urls in provided files and folder", len(img_urls))
        # urls.extend(_extract_image_urls(files))
        save_path = Path(f"{data_processed}/url_dict.json")
        save_dict(img_urls, save_path)

    return


# class Element(BaseContainer):
#     text: str = Field(default_factory=str)
#     structure_level: str = "element"
#     meta: Optional[ElementMeta | ImageMeta | CodeMeta]  = Field(default_factory=ElementMeta)
#     elements: List[Word]  = Field(default_factory=list)

# class ImageMeta(ElementMeta):
#     element_type: str = "image"
#     src: str = Field(default_factory=str)
#     text_file: str = Field(default_factory=str)
#     folder: str = Field(default_factory=str)
#     image_file: str = Field(default_factory=str)


def _extract_image_urls(elements: list[dict]):

    img_urls = []

    for element in elements:
        text = element.get("text", "")
        e_type = element.get("meta", {}).get("element_type")
        c_type = element.get("meta", {}).get("cell_type")

        if e_type == "image":
            img_urls.append(text)

        elif e_type is None and c_type in ["code_block", "md_block"]:
            sub_elements = element.get("elements", [])

            if len(sub_elements) > 0:
                sub_matches = _extract_image_urls(sub_elements)

                if len(sub_matches) == 1:
                    img_urls.append(sub_matches)

                elif len(sub_matches) > 1:
                    img_urls.extend(sub_matches)

        elif isinstance(text, str):
            matches = re.findall(r"(https?://[^)\s]+\.(?:png|jpg|jpeg|webp|gif))", text)

            # matches = re.findall(
            #                 r"\[image\]\((https?://[^)]+\.(?:png|jpg|jpeg|webp|gif))\)",
            #                 text
            #                 )
            # element.update({"matches": matches})

            if len(matches) == 1:
                img_urls.append(matches)

            elif len(matches) > 1:
                img_urls.extend(matches)

            # urls.extend(matches)

    return img_urls


# def _extract_image_urls(elements: dict | List[dict]):
#     # from src.core.memory import session
#     logger = session.logger

#     e_urls = []
#     for element in elements:
#         meta = element.get("meta", {})
#         e_type = meta.get("element_type")
#         c_type = meta.get("cell_type")

#         if e_type == "image":
#             text = element.get("text", "")
#             matches = re.findall(
#                             r"\[image\]\((https?://[^)]+)\)",
#                             text
#                             )
#             e_urls.append(matches)

#         elif e_type is None and c_type is not None:
#             sub_elements = element.get("elements", [])

#             e_urls.extend(_extract_image_urls(sub_elements))

#         else:
#             logger.info(
#                     "Element does not have image_urls:\t%s",
#                     element.get("text"))

#     return e_urls


if __name__ == "__main__":
    scrape_images_from_url()
