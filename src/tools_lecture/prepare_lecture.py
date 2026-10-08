## prepare_lecture.py
# import
import re
from pprint import pformat
from pathlib import Path
from urllib.parse import urlparse, unquote
from pydantic import BaseModel  # , Field

from src.core.memory import app_session

from src.model_parsing.base_classes_parsing import RawDocument
from src.model_lecture.data_resources import (
    LectureResource,
    LectureScript,
    LectureMedia,
)

from src.utils.general_helper import get_value


LECTURE_TITLE_PATTERN = re.compile(
    r"^(?P<lecture_no>"
    r"[A-Za-z0-9._-]+)"  # Variante A
    # r"^(?P<lecture_no>"               # Variante B (ff.)
    # r"(?:\d+(?:\.\d+)*)"
    # r"|(?:\d+[A-F]\.\d+)"
    # r"|(?:K[A-Z]?\.\d+)"
    # r")"
    r"\s+"
    r"(?P<topic>.+)$"
)


def get_resource_metadata_from_url(
    source_url: str,
) -> dict:

    url_path = unquote(urlparse(source_url).path)

    file_name = Path(url_path).name

    if not file_name:
        return {}

    path = Path(file_name)

    file_type = path.suffix.removeprefix(".").lower() or None

    title = path.stem or None

    return {
        "title": title,
        "file_type": file_type,
    }


def enrich_resource_metadata(
    resource: LectureResource,
) -> LectureResource:

    metadata = get_resource_metadata_from_url(resource.source_url)

    title = None
    title_meta = metadata.get("title")

    if resource.title:
        title = normalize_resource_title(resource.title)

    elif title_meta:
        title = normalize_resource_title(title_meta)

    # if title:
    #     title = normalize_resource_title(title)

    lecture_no = resource.lecture_no
    topic = resource.topic

    if title and (lecture_no is None or topic is None):
        parsed_no, parsed_topic = parse_resource_title(title)

        lecture_no = lecture_no or parsed_no

        topic = topic or parsed_topic

    updates = {
        "title": title,
        "file_type": (resource.file_type or metadata.get("file_type")),
        "lecture_no": lecture_no,
        "topic": topic,
    }

    if not resource.title:
        updates["title"] = metadata.get("title")

    if not resource.file_type:
        updates["file_type"] = metadata.get("file_type")

    if resource.local_path is not None and resource.local_path.is_file():
        updates["downloaded"] = True

    return resource.model_copy(update=updates)


def normalize_resource_title(
    title: str,
) -> str:

    while "__" in title:
        title = title.replace("__", "_")

    return title.strip("_")


def parse_resource_title(
    title: str,
) -> tuple[str | None, str | None]:

    if "_" not in title:
        return None, title.replace("_", " ")

    resource_no, topic = title.split(
        "_",
        maxsplit=1,
    )

    topic = topic.replace("_", " ").replace(",", "").strip()

    return resource_no, topic


def validate_lecture_resources(
    resource_data: dict,
) -> dict:

    videos = resource_data.get(
        "videos",
        [],
    )

    scripts = resource_data.get(
        "scripts",
        [],
    )

    report = {
        "n_videos": len(videos),
        "n_scripts": len(scripts),
        "n_material": len(
            resource_data.get(
                "material",
                [],
            )
        ),
        "n_other": len(
            resource_data.get(
                "other_links",
                [],
            )
        ),
        "videos_without_block": [
            video.get("lecture_no")
            for video in videos
            if not video.get("lecture_blocks")
        ],
        "videos_without_media_id": [
            video.get("title") for video in videos if not video.get("media_id")
        ],
        "scripts_without_block": [
            script.get("source_url")
            for script in scripts
            if not script.get("lecture_blocks")
        ],
    }

    if app_session.logger is not None:
        app_session.logger.info(
            "Overview report:\n%s", format_validation_report(report)
        )

    return report


def format_validation_report(
    report: dict,
) -> str:

    lines = []

    for key, value in report.items():
        formatted = pformat(value, width=80, compact=True)

        lines.append(f"  {key}:\t{formatted}")

    return "\n".join(lines)


def deduplicate_scripts(
    scripts: list[LectureScript],
) -> list[LectureScript]:

    by_url: dict[str, LectureScript] = {}

    for script in scripts:
        existing = by_url.get(script.source_url)

        if existing is None:
            by_url[script.source_url] = script
            continue

        for block_id in script.lecture_blocks:
            if block_id not in existing.lecture_blocks:
                existing.lecture_blocks.append(block_id)

    return list(by_url.values())


def deduplicate_videos(
    videos: list[LectureMedia],
) -> list[LectureMedia]:

    by_id: dict[str, LectureMedia] = {}
    without_id: list[LectureMedia] = []

    for video in videos:
        if not video.media_id:
            without_id.append(video)
            continue

        existing = by_id.get(video.media_id)

        if existing is None:
            by_id[video.media_id] = video
            continue

        for block_id in video.lecture_blocks:
            if block_id not in existing.lecture_blocks:
                existing.lecture_blocks.append(block_id)

    return [
        *by_id.values(),
        *without_id,
    ]


def filter_html_elements(html_doc: RawDocument, elements: list[str] | None = None):

    if not elements:
        raise ValueError(f"No elements provided")

    elements_filt: dict[str, dict] = {}
    match_idx = 0

    seen_links: set[str] = set()

    def walk(node) -> None:
        nonlocal match_idx

        node_type = get_value(node, "container_type") or get_value(node, "leaf_type")

        if node_type in elements:
            if isinstance(node, BaseModel):
                node_dict = node.model_dump(mode="python")
            else:
                node_dict = node

            # Links anhand href deduplizieren
            if node_type in {
                "link_node",
                "link",
            }:
                href = node_dict.get("href")

                if href:
                    if href in seen_links:
                        return

                    seen_links.add(href)

            elements_filt[f"element_{match_idx}"] = node_dict

            match_idx += 1

        for child_key in (
            "elements",
            "inline_elements",
        ):
            children = get_value(
                node,
                child_key,
                [],
            )

            if not children:
                continue

            for child in children:
                if isinstance(
                    child,
                    (BaseModel, dict),
                ):
                    walk(child)

        # if node_type in elements:
        #     if isinstance(node, BaseModel):
        #         node_dict = node.model_dump(
        #             mode="python"
        #         )
        #     else:
        #         node_dict = node

        #     if isinstance(node, BaseModel):
        #         elements_filt[f"element_{match_idx}"] = node.model_dump(mode="python")
        #     else:
        #         elements_filt[f"element_{match_idx}"] = node

        #     match_idx += 1

        # for child_key in ("elements", "inline_elements"):
        #     children = get_value(node, child_key, [])
        #     if not children:
        #         continue

        #     for child in children:
        #         if isinstance(child, (BaseModel, dict)):
        #             walk(child)

    walk(html_doc)

    return elements_filt


def classify_links(links: dict[str, dict]) -> dict[str, dict]:

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

        elif "skript" in safe_title.lower():  #  ==
            script_links[key] = link

        elif (
            "/material/" in href.lower()
            or "/praktikum/" in href.lower()
            or href.lower().endswith(".zip")
        ):
            material_links[key] = link

        elif "github.com/" in href.lower():
            material_links[key] = link

        else:
            other_links[key] = link

    return {
        "video": video_links,
        "script": script_links,
        "material": material_links,
        "other": other_links,
    }


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
