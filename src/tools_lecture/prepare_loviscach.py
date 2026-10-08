## prepare_loviscach.py
# import
from typing import Literal
from pydantic import BaseModel  # , Field
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from src.model_parsing.base_classes_parsing import RawDocument

from src.utils.general_helper import get_value, normalize_whitespace
from src.tools_lecture.prepare_lecture import extract_link_title, filter_html_elements
from src.model_lecture.data_resources import LectureScript, LectureMedia


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
        # text = get_value(current, "text", "")

        if href:
            href_lower = href.lower()
            title = extract_link_title(current).lower()

            if (
                "/videos/v.php" in href_lower
                or "/skript/" in href_lower
                # or "/material/" in href_lower
                or href_lower.endswith(".pdf")
                or "skript" in title
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

    def walk(node) -> None:

        children = get_value(
            node,
            "inline_elements",
            [],
        )

        if not children:
            return

        child_resource_nodes = [
            child
            for child in children
            if (
                isinstance(child, (BaseModel, dict))
                and get_value(child, "leaf_type") == "other_node"
                and contains_lecture_resources(child)
            )
        ]

        if (
            get_value(node, "leaf_type") == "other_node"
            and contains_lecture_resources(node)
            and not child_resource_nodes
        ):
            blocks.append(node)
            return

        for child in children:
            if isinstance(child, (BaseModel, dict)):
                walk(child)

    walk(table)

    # return blocks
    # for element in get_value(table, "inline_elements", []):
    #     if get_value(element, "leaf_type") != "other_node":
    #         continue

    #     if contains_lecture_resources(element):
    #         blocks.append(element)

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
    print(f"Detected lecture rows: {len(row_nodes)}")

    blocks = []

    for idx, block_node in enumerate(row_nodes, start=1):
        # block_id = f"{block_idx:02d}"
        block_id = infer_block_id(block_node, fallback_idx=idx)

        print(
            f"Row {idx:02d} -> "
            f"block_id={block_id} | "
            f"{get_value(block_node, 'text', '')[:100]}"
        )

        blocks.append(
            {
                "block_id": block_id,
                "node": block_node,
            }
        )

    return blocks


def infer_block_id(
    block_node,
    fallback_idx: int,
) -> str:

    block_text = get_value(
        block_node,
        "text",
        "",
    ).lower()

    # Klausur-/Prüfungsblock
    if "klausurvorbereitung" in block_text or "prüfungsvorbereitung" in block_text:
        return "exam"

    links = filter_html_elements(
        block_node,
        elements=["link_node", "link"],
    )

    # (1.) scripts files
    for link in links.values():
        href = link.get("href", "")

        match = re.search(
            r"/(?:Skript|Skripte)/(\d{2})_",
            href,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    # (2.) media files
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


def assign_video_blocks_by_order(
    videos: list[LectureMedia],
) -> list[LectureMedia]:
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

            if not video.lecture_blocks:
                video.lecture_blocks.append(direct_block)

            continue

        if video.lecture_blocks:
            continue

        # Nur explizit buchstabenbasierte alte Erklärvideos
        # automatisch über die Position zuordnen.
        if not is_letter_prefixed_video(video.lecture_no):
            continue

        block_id = current_block or next_blocks[idx]

        if block_id:
            # and block_id not in video.lecture_blocks:
            video.lecture_blocks.append(block_id)

    return videos


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


def enrich_urls(urls: dict[str, dict]) -> list[LectureMedia]:

    videos: list[LectureMedia] = []

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

        media_id = extract_media_id(href)

        youtube_url = (
            f"https://www.youtube.com/watch?v={media_id}" if media_id else None
        )

        videos.append(
            LectureMedia(
                title=safe_title,
                lecture_no=lecture_no,
                topic=topic,
                # section=None,
                resource_kind=infer_video_kind(lecture_no),
                lecture_blocks=([block_id] if block_id else []),
                source_url=href,
                youtube_url=youtube_url,
                media_id=media_id,
                media_type="video",
                duration=None,
                # source_url="",
                # youtube_url="",
                # media_id="",      # : str | None = None
                # duration="",        # : str | None = None
                # section="",         # : str | None = None
                # kind: str = "foundation"
            )
        )

    return videos


def extract_media_id(
    url: str | None,
) -> str | None:

    if not url:
        return None

    youtube_id = extract_youtube_id(url)

    if youtube_id:
        return youtube_id

    return None


def extract_youtube_id(url: str) -> str | None:

    parsed = urlparse(url)

    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    # youtube.com/watch?v=...
    if host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }:
        if path == "watch":
            query = parse_qs(parsed.query)

            return query.get(
                "v",
                [None],
            )[0]

        # /shorts/<id>
        # /embed/<id>
        # /live/<id>
        parts = path.split("/")

        if len(parts) >= 2 and parts[0] in {
            "shorts",
            "embed",
            "live",
        }:
            return parts[1]

    # youtu.be/<id>
    if host in {
        "youtu.be",
        "www.youtu.be",
    }:
        return path.split("/")[0] if path else None

    return None


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
