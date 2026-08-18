## filter_html_elements.py
# imports 
import re
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from typing import Literal 
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

from src.core.config import parsing_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.model_classes_parsing.base_classes_parsing import RawDocument  # DocumentExtract, 
from src.model_knowledge.data_knowledge import (
                                            LectureVideo,
                                            LectureResources,
                                            LectureScript
                                            )
from src.utils.dict_helper import load_dict, save_dict



# TODO:
# {
#   "lecture_no": "02A.4",
#   "topic": "Q"
# }

# TODO:
# def extract_material():

#   return 
####################    

def run_loviscach_url_update():
    
    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
                    name="Loviscach", 
                    file_name=f"{app_session.timestamp}_Loviscach"
                )
    # app_session.logger = create_logger()
    html_dir = parsing_env_vars.data_html
    
    for title in [
            # "JLoviscach_Mathe_2",
            # "JLoviscach_Info_1",
            # "JLoviscach_Info_2_c#",
            # "JLoviscach_Info_2_python",
            # "JLoviscach_Mensch_Maschine",
            # "JLoviscach_Mathe_2",
            "loviscach_wind_wasser",
            "loviscach_regenerativ",
            "loviscach_ing_mathe_2",
            "loviscach_ing_mathe_1",
            "loviscach_gebäudeautomation",
            "loviscach_cyber_physische_systeme",
            "lloviscach_lehre",
                    ]:
        app_session.logger.info(f"Start filtering in file '{title}'")
    
        f_path = Path(html_dir) / f"test_2026-08-16_{title}/{title}_info.json"
        elements = ["link_node", "link"]
        loviscach_url_update(f_path, elements)

    return 



LECTURE_TITLE_PATTERN = re.compile(
    r"^(?P<lecture_no>"
    r"[A-Za-z0-9._-]+)"                    # Variante A
    # r"^(?P<lecture_no>"               # Variante B (ff.)
    # r"(?:\d+(?:\.\d+)*)"
    # r"|(?:\d+[A-F]\.\d+)"
    # r"|(?:K[A-Z]?\.\d+)"
    # r")"
    r"\s+"
    r"(?P<topic>.+)$"
)


def loviscach_url_update(
                    f_path: Path, 
                    elements: list[str]
                    ):

    html_dict = load_dict(f_path, RawDocument)

    links = filter_html_elements(html_dict, elements)

    links = classify_links(
                                                        links
                                                        )

    videos = enrich_urls(links["video"])
    videos = deduplicate_videos(videos)

    scripts = extract_scripts(links["script"])
    scripts = deduplicate_scripts(scripts)

    for vid in videos:    
        # yt_id = extract_youtube_id(url.source_url)
  
        if vid.youtube_url:
            continue

            # url.youtube_url = f"https://www.youtube.com/watch?v={yt_id}"
        resolved_url = resolve_video_url(vid.source_url)

        if resolved_url:    #yt_id in seen_ids:
            vid.youtube_url = resolved_url
            vid.youtube_id = extract_youtube_id(
                resolved_url
                )

    f_name = "_".join(f_path.stem.split("_")[:-1])
    save_path = f_path.with_stem(f"{f_name}_lectures")
    save_dict(data={
                "video": [vid.model_dump(mode="json")
                               for vid in videos], 
                "script": [scr.model_dump(mode="json") for scr in scripts],
                "material": links["material"], 
                "other": links["other"]
                },     
            path=save_path)  

    # save_path = f_path.with_stem(f"{f_path.stem}_elem_filt")
    # save_dict(data=elements_filt, path=save_path)

    return LectureResources(
                    videos=videos,
                    scripts=scripts,
                    material=links["material"], 
                    other_links=links["other"]
                )


def deduplicate_scripts(
    scripts: list[LectureScript],
) -> list[LectureScript]:

    seen_urls: set[str] = set()
    unique: list[LectureScript] = []

    for script in scripts:
        if script.source_url in seen_urls:
            continue

        seen_urls.add(script.source_url)
        unique.append(script)

    return unique


def deduplicate_videos(
    videos: list[LectureVideo],
) -> list[LectureVideo]:

    seen_ids: set[str] = set()
    unique: list[LectureVideo] = []

    for video in videos:
        if video.youtube_id:
            if video.youtube_id in seen_ids:
                continue

            seen_ids.add(video.youtube_id)

        unique.append(video)

    return unique


def get_value(node, key: str, default=None):
    if isinstance(node, BaseModel):
        return getattr(node, key, default)

    if isinstance(node, dict):
        return node.get(key, default)

    return default


def filter_html_elements(
                    html_doc: RawDocument, 
                    elements: list[str] | None = None
                    ):

    if not elements:
        raise ValueError(f"No elements provided")
    
    elements_filt: dict[str, dict] = {}
    match_idx = 0

    def walk(node) -> None:
        nonlocal match_idx

        node_type = (
            get_value(node, "container_type")
            or get_value(node, "leaf_type")
            )

        if node_type in elements:
            if isinstance(node, BaseModel):
                elements_filt[f"element_{match_idx}"] = (
                    node.model_dump(mode="python")
                )
            else:
                elements_filt[f"element_{match_idx}"] = node

            match_idx += 1

        for child_key in ("elements", "inline_elements"):
            children = get_value(node, child_key, [])
            if not children:
                    continue

            for child in children:
                if isinstance(child, (BaseModel, dict)):
                    walk(child)

    walk(html_doc)

    # for c_idx, element in enumerate(html_dict.get("elements", [])):
    #     # print("Filter")

    #     c_type = element.get("container_type")
    #     if c_type and c_type in elements:

    #         print(f"Found one demanded html element ('{elements}') in container #{c_idx}")
    #         elements_filt[f"url_c{c_idx}"] = element
    #         continue

    #     sub_elements = element.get("elements")
    #     if sub_elements:
    #         for l_idx, sub_element in enumerate(sub_elements): 

    #             l_type = sub_element.get("leaf_type")
    #             if l_type and l_type in elements:
    #                 print(f"Found one demanded html element ('{elements}') in leaf #{l_idx} of container #{c_idx}")
    #                 elements_filt[f"url_c{c_idx}_l{l_idx}"] = sub_element
    #                 continue

    # save_path = f_path.with_stem(f"{f_path.stem}_elem_filt")
    # save_dict(data=elements_filt, path=save_path)

    return elements_filt


def classify_links(
            links: dict[str, dict]
            ) -> dict[str, dict]: 
    # tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:

    video_links = {}
    script_links = {}
    material_links = {}
    other_links = {}

    for key, link in links.items():
        href = link.get("href", "")
        title = extract_link_title(link).strip()
        safe_title = "_".join(title.split())

        if "/videos/v.php" in href:
            video_links[key] = link

        elif "skript" in safe_title.lower():       #  == 
            # or "/Skript/" in href
            # and href.lower().endswith(".pdf")
            # ):
            script_links[key] = link

        elif (
            "material" in safe_title.lower()
            or href.lower().endswith(".zip")
            ):
            material_links[key] = link

        else:
            other_links[key] = link

    return {
        "video": video_links, 
        "script": script_links, 
        "material": material_links, 
        "other": other_links
        }


def extract_scripts(
        links: dict[str, dict],
    ) -> list[LectureScript]:

    scripts = []

    for link in links.values():
        href = link.get("href")

        if not href:
            continue

        scripts.append(
            LectureScript(
                source_url=href,
            )
        )

    return scripts


# def is_script_link(link: dict) -> bool:
#     return (
#         link.get("leaf_type") == "link_node"
#         and extract_link_title(link).strip().lower() == "skript"
#         and link.get("href", "").lower().endswith(".pdf")
#     )


def parse_lecture_title(
    title: str,
) -> tuple[str | None, str]:

    match = LECTURE_TITLE_PATTERN.match(title)

    if not match:
        return None, title

    return (
        match.group("lecture_no"),
        match.group("topic").strip(),
    )


def infer_video_kind(
    lecture_no: str | None,
) -> Literal["foundation", "supplement"]:

    if not lecture_no:
        return "foundation"

    if re.search(r"\d[A-F]\.", lecture_no):
        return "supplement"

    if lecture_no.startswith("K"):
        return "supplement"

    return "foundation"


def extract_link_title(link_node: dict) -> str:
    texts: list[str] = []

    for element in link_node.get("inline_elements", []):
        text = element.get("text")

        if text:
            texts.append(text.strip())

    if texts:
        return " ".join(texts).strip()

    # Fallback
    return link_node.get("text", "").strip()


def enrich_urls(urls: dict[str, dict]) -> list[LectureVideo]:

    videos: list[LectureVideo] = []
    for url_info in urls.values():
        href = url_info.get("href")

        if not href:
            continue

        # Nur Video-Links verarbeiten
        if "/videos/v.php" not in href:
            continue

        title = extract_link_title(url_info)
        safe_title = "_".join(title.replace(",", " ").split())

        lecture_no, topic = parse_lecture_title(safe_title)
        youtube_id = extract_youtube_id(href)

        youtube_url = (
            f"https://www.youtube.com/watch?v={youtube_id}"
            if youtube_id
            else None
            )

        videos.append(
                    LectureVideo(
                        title=safe_title,
                        lecture_no=lecture_no,
                        topic=topic,
                        section=None,
                        kind=infer_video_kind(lecture_no),
                        source_url=href,
                        youtube_url=youtube_url,
                        youtube_id=youtube_id,
                        duration=None,
                        # source_url="", 
                        # youtube_url="", 
                        # youtube_id="",      # : str | None = None
                        # duration="",        # : str | None = None
                        # section="",         # : str | None = None
                        # kind: str = "foundation"
                            )
                    )

    return videos

# title: str
#     kind: Literal["foundation", "supplement"]   #  = "foundation"
#     lecture_no: str | None = None
#     topic: str | None = None
#     section: str | None = None
#     source_url: str
#     youtube_url: str | None #  = None
#     youtube_id: str | None  #  = None
#     # duration: str | None = None
#     duration: int | None = None

def extract_youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    return query.get("v", [None])[0]


def resolve_video_url(url: str) -> str | None:
    response = requests.get(
        url,
        timeout=10,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "youtube.com/watch" in href or "youtu.be/" in href:
            return href

    return None


if __name__ == "__main__":
    run_loviscach_url_update()