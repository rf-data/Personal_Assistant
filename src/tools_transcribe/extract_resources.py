## extract_resources.py
# import
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests


# TODO: requests.Session()

# TODO:
# seen_urls: set[str] = set()

# for material in materials:
#     if material.source_url in seen_urls:
#         continue

#     seen_urls.add(material.source_url)


def download_lecture_resource(
    url: str,
    output_dir: str | Path,
    timeout: float = 30.0,
) -> Path:

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        url,
        stream=True,
        timeout=timeout,
        allow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    response.raise_for_status()

    filename = unquote(Path(urlparse(response.url).path).name)

    if not filename:
        raise ValueError(f"Could not determine filename from URL: {url}")

    output_path = output_dir / filename

    with output_path.open("wb") as f:
        for chunk in response.iter_content(
            chunk_size=1024 * 1024,
        ):
            if chunk:
                f.write(chunk)

    return output_path


def extract_section_no(value: str) -> str | None:
    match = re.search(
        r"(?<!\d)(\d{2})",
        value,
    )

    return match.group(1) if match else None


# def extract_semester(url: str) -> str | None:
#     match = re.search(
#         r"/(\d{4}(?:ws|ss))/",
#         url,
#         flags=re.IGNORECASE,
#     )

#     return match.group(1) if match else None
