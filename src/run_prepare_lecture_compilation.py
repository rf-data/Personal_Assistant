## run_prepare_lecture_compilation.py
# imports
import re
from pydantic import BaseModel  # , Field
from pathlib import Path
from pprint import pformat
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.memory_knowledge import KnowledgeContext
from src.core.logger import create_logger
from src.model_classes_parsing.base_classes_parsing import (
    RawDocument,
)  # DocumentExtract,
from src.model_knowledge.data_resources import (
    LectureResource,
    LectureScript,
    LectureVideo,
    # RawLectureBlock
)
from src.utils.dict_helper import load_dict, save_dict


# ! TODO:
# Info_2_python lieferte dagegen:
#
# n_videos: 0
# n_scripts: 0
# n_material: 0
# n_other: 0
#
# obwohl der HTML-Parser Content gefunden hatte.
#
################################################
#
# ? NEXT_COURSES
# (1) Harvard CS50x
# --> "https://cs50.harvard.edu/x/"
#
# (2) Harvard CS50 Python
# --> "https://cs50.harvard.edu/python/"
#
# (3) Harvard CS50 SQL
# --> "https://cs50.harvard.edu/sql/"
#
# (4) Harvard CS50 AI + Harvard CS50 Professional Certificate AI
# --> "https://cs50.harvard.edu/ai/"

# ! TODO: DataModel MIT_Course
# (1): 6.1200J Mathematics for Computer Science (Spring 2024)
# -> url="https://ocw.mit.edu/courses/6-1200j-mathematics-for-computer-science-spring-2024"
#
# (2): 18.01SC Single Variable Calculus | Fall 2010
# -> "https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/"
#
# (3): [01/26/2027 -> 05/16/2027] Machine Learning with Python: from Linear Models to Deep Learning- 6.86x
# --> https://learn.mit.edu/courses/course-v1:MITxT+6.86x
#
# (4): [09/01/2026 -> 12/24/2026] Probability - The Science of Uncertainty and Data - 6.431x
# --> "https://learn.mit.edu/courses/course-v1:MITxT+6.431x"
#
# (5): [09/01/2026 -> 12/22/2026] Fundamentals of Statistics - 18.6501x
# --> "https://learn.mit.edu/courses/course-v1:MITxT+18.6501x"
#
# (6): [01/19/027 -> 05/17/2027] Data Analysis: Statistical Modeling and Computation in Applications
# --> "https://learn.mit.edu/courses/course-v1:MITxT+6.419x"
#
# (7): Capstone Exam in Statistics and Data Science - DS-CFx
# -> https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/

# Course
# ├── metadata
# │   ├── institution
# │   ├── course_number
# │   ├── title
# │   ├── semester
# │   ├── instructors
# │   ├── department
# │   ├── level
# │   └── prerequisites
# │
# ├── syllabus
# ├── calendar
# │
# ├── lectures[]
# │   ├── lecture_no
# │   ├── title
# │   ├── topics
# │   ├── video
# │   ├── notes
# │   └── readings
# │
# ├── assignments[]
# ├── exams[]
# └── other_resources[]
#
# 18.01SC Single Variable Calculus
# │
# ├── 1. Differentiation
# │   ├── Part A
# │   ├── Part B
# │   └── Exam 1
# │
# ├── 2. Applications of Differentiation
# ├── 3. Definite Integral and Applications
# ├── 4. Techniques of Integration
# └── 5. Exploring the Infinite
#     │
#     └── Sessions
#          ├── Lecture Video
#          ├── Course Notes
#          ├── Worked Examples
#          └── Problems


def run_prepare_lecture_compilation() -> None:

    dict_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(context_path, KnowledgeContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,
        # , "RF_LOG"),
        file_name=context.logger_f_name,
        # ", "rf_log")
    )

    info_paths = context.info_paths
    elements = context.extract_elements

    app_session.logger.info(
        """
Preparing lecture compilation for %s course(s)
Filtering %s elements: %s
""",
        len(info_paths),
        len(elements),
        elements,
    )

    for i_path in info_paths:
        prepare_lecture_compilation(Path(i_path), elements)

    return None


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

    title = title.replace(",", "")

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


def find_lecture_table(
    html_doc: RawDocument,
):
    for element in html_doc.elements:
        if get_value(element, "container_type") == "table":
            return element

    return None


def contains_lecture_resources(
    node,
) -> bool:

    found = False

    def walk(current) -> None:
        nonlocal found

        if found:
            return

        href = get_value(current, "href", "")

        if href:
            if (
                "/videos/v.php" in href
                or "/Skript/" in href
                or href.lower().endswith(".pdf")
            ):
                found = True
                return

        for child_key in ("elements", "inline_elements"):
            children = get_value(
                current,
                child_key,
                [],
            )

            if not children:
                continue

            for child in children:
                if isinstance(child, (BaseModel, dict)):
                    walk(child)

    walk(node)

    return found


def get_lecture_block_nodes(
    table,
) -> list:

    blocks = []

    for element in get_value(table, "inline_elements", []):
        if get_value(element, "leaf_type") != "other_node":
            continue

        if contains_lecture_resources(element):
            blocks.append(element)

    return blocks


def lecture_block_extraction(
    html_doc: RawDocument,
) -> list[dict]:  # [RawLectureBlock]:

    table = find_lecture_table(html_doc)

    if table is None:
        raise ValueError("No lecture table found.")

    print("\nidx | leaf_type | text[:100] | n_elements:")
    for idx, element in enumerate(get_value(table, "inline_elements", [])):
        print(
            idx,
            get_value(element, "leaf_type"),
            get_value(element, "text", "")[:100],
            len(get_value(element, "inline_elements", [])),
        )

    row_nodes = get_lecture_block_nodes(table)

    blocks = []

    for idx, block_node in enumerate(row_nodes, start=1):
        # block_id = f"{block_idx:02d}"
        block_id = infer_block_id(block_node, fallback_idx=idx)

        blocks.append(
            {
                "block_id": block_id,
                "node": block_node,
            }
        )

    return blocks


def prepare_lecture_compilation(f_path: Path, elements: list[str]) -> dict[str, list]:
    info_dict = load_dict(
        f_path,
        RawDocument,
    )
    lecture_blocks = lecture_block_extraction(info_dict)

    all_videos: list[LectureVideo] = []
    all_scripts: list[LectureScript] = []

    all_materials = []
    all_other = []

    for block in lecture_blocks:
        # block_id = block["block_id"]
        block_node = block["node"]

        links = filter_html_elements(
            block_node,
            elements,
        )

        links = classify_links(links)

        videos = enrich_urls(links["video"])

        scripts = extract_scripts(links["script"])

        scripts = deduplicate_scripts(scripts)

        for video in videos:
            # video.lecture_blocks = [block_id]

            if video.youtube_url:
                continue

            resolved_url = resolve_video_url(video.source_url)

            if resolved_url:
                video.youtube_url = resolved_url
                video.youtube_id = extract_youtube_id(resolved_url)

        all_videos.extend(videos)
        all_scripts.extend(scripts)

        all_materials.extend(links["material"].values())

        all_other.extend(links["other"].values())

    all_videos = assign_video_blocks_by_order(all_videos)

    all_videos = deduplicate_videos(all_videos)

    all_videos = [enrich_resource_metadata(video) for video in videos]

    all_scripts = deduplicate_scripts(all_scripts)

    all_scripts = [enrich_resource_metadata(script) for script in all_scripts]

    all_materials = [enrich_resource_metadata(material) for material in all_materials]

    # exams = [
    #     enrich_resource_metadata(exam)
    #     for exam in exams
    #     ]

    f_name = "_".join(f_path.stem.split("_")[:-1])

    save_path = f_path.with_stem(f"{f_name}_lectures_new")

    resource_data = {
        "videos": [vid.model_dump(mode="json") for vid in all_videos],
        "scripts": [script.model_dump(mode="json") for script in all_scripts],
        "material": all_materials,
        # [mat.model_dump(mode="json") for mat in all_material],
        "other_links": all_other,
        # [other.model_dump(mode="json") for other in all_other],
    }

    resource_data.update({"report": validate_lecture_resources(resource_data)})

    save_dict(data=resource_data, path=save_path)

    return resource_data


# resources


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
        "videos_without_youtube_id": [
            video.get("title") for video in videos if not video.get("youtube_id")
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


def infer_block_id(
    block_node,
    fallback_idx: int,
) -> str:

    links = filter_html_elements(
        block_node,
        elements=["link_node", "link"],
    )

    # (1.)
    for link in links.values():
        href = link.get("href", "")

        match = re.search(
            r"/Skript/(\d{2})_",
            href,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    # (2.)
    for link in links.values():
        href = link.get("href", "")

        if "/videos/v.php" not in href:
            continue

        title = extract_link_title(link)

        lecture_no, _ = parse_lecture_title(title)

        if not lecture_no:
            continue

        match = re.match(r"(\d{2})", lecture_no)

        if match:
            return match.group(1)

    # (3.) Fallback
    return f"{fallback_idx:02d}"


def infer_video_block(
    lecture_no: str | None,
) -> str | None:

    if not lecture_no:
        return None

    match = re.match(r"^(\d{2})", lecture_no)

    if match:
        return match.group(1)

    return None


def is_letter_prefixed_video(
    lecture_no: str | None,
) -> bool:

    if not lecture_no:
        return False

    return bool(re.match(r"^[A-Za-z]", lecture_no))


def infer_script_block(
    source_url: str,
) -> str | None:

    match = re.search(
        r"/(\d{2})_[^/]+\.pdf$",
        source_url,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


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


def assign_video_blocks_by_order(
    videos: list[LectureVideo],
) -> list[LectureVideo]:
    """
    Ergänzt lecture_blocks für Videos, deren lecture_no mit
    einem Buchstaben beginnt.

    Strategie:
    1. Numerisch beginnende lecture_no bestimmen ihren Block direkt.
    2. Buchstaben-Videos erben den zuletzt bekannten nummerierten Block.
    3. Gibt es noch keinen vorherigen Block, wird der nächste
       nummerierte Block verwendet.

    Die Reihenfolge von `videos` muss der Reihenfolge der Links
    im ursprünglichen Dokument entsprechen.
    """

    if not videos:
        return videos

    # Für jede Position merken, welcher nummerierte Block
    # als nächstes folgt.
    next_blocks: list[str | None] = [None] * len(videos)

    next_block: str | None = None

    for idx in range(len(videos) - 1, -1, -1):
        direct_block = infer_video_block(videos[idx].lecture_no)

        if direct_block:
            next_block = direct_block

        next_blocks[idx] = next_block

    # Vorwärtslauf:
    # normale Videos aktualisieren current_block,
    # Buchstaben-Videos erben ihn.
    current_block: str | None = None

    for idx, video in enumerate(videos):
        direct_block = infer_video_block(video.lecture_no)

        if direct_block:
            current_block = direct_block

            if direct_block not in video.lecture_blocks:
                video.lecture_blocks.append(direct_block)

            continue

        # Nur explizit buchstabenbasierte alte Erklärvideos
        # automatisch über die Position zuordnen.
        if not is_letter_prefixed_video(video.lecture_no):
            continue

        block_id = current_block or next_blocks[idx]

        if block_id and block_id not in video.lecture_blocks:
            video.lecture_blocks.append(block_id)

    return videos


def deduplicate_videos(
    videos: list[LectureVideo],
) -> list[LectureVideo]:

    by_id: dict[str, LectureVideo] = {}
    without_id: list[LectureVideo] = []

    for video in videos:
        if not video.youtube_id:
            without_id.append(video)
            continue

        existing = by_id.get(video.youtube_id)

        if existing is None:
            by_id[video.youtube_id] = video
            continue

        for block_id in video.lecture_blocks:
            if block_id not in existing.lecture_blocks:
                existing.lecture_blocks.append(block_id)

    return [
        *by_id.values(),
        *without_id,
    ]


def get_value(node, key: str, default=None):
    if isinstance(node, BaseModel):
        return getattr(node, key, default)

    if isinstance(node, dict):
        return node.get(key, default)

    return default


def filter_html_elements(html_doc: RawDocument, elements: list[str] | None = None):

    if not elements:
        raise ValueError(f"No elements provided")

    elements_filt: dict[str, dict] = {}
    match_idx = 0

    def walk(node) -> None:
        nonlocal match_idx

        node_type = get_value(node, "container_type") or get_value(node, "leaf_type")

        if node_type in elements:
            if isinstance(node, BaseModel):
                elements_filt[f"element_{match_idx}"] = node.model_dump(mode="python")
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

        elif "material" in safe_title.lower() or href.lower().endswith(".zip"):
            material_links[key] = link

        else:
            other_links[key] = link

    return {
        "video": video_links,
        "script": script_links,
        "material": material_links,
        "other": other_links,
    }


def extract_scripts(
    links: dict[str, dict],
) -> list[LectureScript]:

    scripts = []

    for link in links.values():
        href = link.get("href")

        if not href:
            continue

        block_id = infer_script_block(href)

        scripts.append(
            LectureScript(
                source_url=href,
                lecture_blocks=([block_id] if block_id else []),
            )
        )

    return scripts


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

    # Alte Erklär-/Aufgabenvideos mit Buchstabenpräfix:
    # K01, KB.27, P3, S01, ...
    if re.match(r"^[A-Za-z]", lecture_no):
        return "supplement"

    # Nummerierter Block + Buchstaben-Suffix:
    # 01A.1, 03C.2, ...
    if re.search(r"\d[A-F]\.", lecture_no):
        return "supplement"

    # if lecture_no.startswith("K"):
    #     return "supplement"

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

        lecture_no, topic = parse_lecture_title(title)

        topic = normalize_whitespace(topic)

        safe_title = "_".join(title.replace(",", " ").split())

        block_id = infer_video_block(lecture_no)

        youtube_id = extract_youtube_id(href)

        youtube_url = (
            f"https://www.youtube.com/watch?v={youtube_id}" if youtube_id else None
        )

        videos.append(
            LectureVideo(
                title=safe_title,
                lecture_no=lecture_no,
                topic=topic,
                # section=None,
                resource_kind=infer_video_kind(lecture_no),
                lecture_blocks=([block_id] if block_id else []),
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


def normalize_whitespace(
    text: str,
) -> str:

    return " ".join(text.split())


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
    run_prepare_lecture_compilation()
