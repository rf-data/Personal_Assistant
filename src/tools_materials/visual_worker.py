"""Private, bounded source observations. No image extraction, rendering or OCR."""

import base64
import json
import math
import resource
import sys
from pathlib import Path


def html_observations(raw, limits):
    # Fixed repository path, not a path supplied in the request. Reuse DOM identity.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from bs4 import BeautifulSoup
    from bs4 import __version__ as bs4_version

    from src.tools_materials.parse_html import dom_path

    soup = BeautifulSoup(raw, "html.parser")
    observations = []
    for tag in soup.find_all(["img", "svg", "object", "embed", "source"]):
        if tag.find_parent("svg") or tag.find_parent(["template", "noscript"]):
            continue
        if tag.name in {"object", "embed"} and not (
            str(tag.get("type", "")).startswith("image/")
            or str(tag.get("data", tag.get("src", ""))).split("?")[0].endswith(".svg")
        ):
            continue
        if tag.name == "source" and not tag.find_parent("picture"):
            continue
        if len(observations) >= limits["max_assets"]:
            raise ValueError("HTML visual occurrence limit exceeded")
        figure = tag.find_parent("figure")
        caption = figure.find("figcaption") if figure else None
        references = []
        if tag.name == "svg":
            for child in tag.find_all(["image", "use", "a"]):
                ref = child.get("href", child.get("xlink:href"))
                if ref:
                    references.append(str(ref))
        observations.append(
            dict(
                token="dom:" + dom_path(tag),
                location=dict(dom=dom_path(tag)),
                tag=tag.name,
                reference=tag.get("src", tag.get("data")),
                caption=caption.get_text(" ", strip=True)[:1000]
                if caption
                else tag.get("alt"),
                context=dict(
                    alt=tag.get("alt"),
                    caption=caption.get_text(" ", strip=True)[:1000]
                    if caption
                    else None,
                    srcset=tag.get("srcset"),
                    svg_references=references,
                    active_svg=bool(tag.find(["script", "foreignObject"]))
                    if tag.name == "svg"
                    else False,
                ),
            )
        )
    return dict(
        observations=observations,
        page_count=None,
        backend=dict(name="beautifulsoup/html.parser", version=bs4_version),
    )


def rect_tuple(rect):
    values = tuple(float(v) for v in rect)
    if (
        len(values) != 4
        or not all(math.isfinite(v) for v in values)
        or values[0] > values[2]
        or values[1] > values[3]
    ):
        raise ValueError("Non-finite/reversed PDF geometry")
    return values


def group_paths(paths, gap):
    """Connected components by rectangle proximity; retain every original path.

    Page backgrounds remain separate observations so an enclosing full-page
    rectangle does not connect every unrelated drawing into one candidate.
    """
    parent = list(range(len(paths)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, left in enumerate(paths):
        if left["background"]:
            continue
        a = left["bbox"]
        for j in range(i + 1, len(paths)):
            right = paths[j]
            if right["background"]:
                continue
            b = right["bbox"]
            if (
                a[0] <= b[2] + gap
                and b[0] <= a[2] + gap
                and a[1] <= b[3] + gap
                and b[1] <= a[3] + gap
            ):
                parent[root(j)] = root(i)
    groups = {}
    for i, path in enumerate(paths):
        groups.setdefault(root(i), []).append(path)
    return list(groups.values())


def pdf_observations(raw, limits):
    import pymupdf

    observations, signatures = [], {}
    path_count = operation_count = 0
    with pymupdf.open(stream=raw, filetype="pdf") as document:
        if document.needs_pass or len(document) > limits["max_pages"]:
            raise ValueError("Encrypted PDF or page limit exceeded")
        for page_number, page in enumerate(document, start=1):
            bounds = rect_tuple(page.rect * page.derotation_matrix)
            width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
            # Metadata only: do not create Pixmaps, decode or extract image bytes.
            for index, info in enumerate(
                page.get_image_info(hashes=False, xrefs=False)
            ):
                observations.append(
                    dict(
                        token=f"pdf-image:{page_number}:{index}",
                        location=dict(page=page_number, bbox=rect_tuple(info["bbox"])),
                        tag="pdf_image",
                        reference=None,
                        context=dict(
                            width=info["width"],
                            height=info["height"],
                            page_bounds=bounds,
                            rotation=page.rotation,
                        ),
                    )
                )
                if len(observations) > limits["max_assets"]:
                    raise ValueError("PDF visual occurrence limit exceeded")
            paths = []
            for index, drawing in enumerate(page.get_drawings()):
                bbox = rect_tuple(drawing["rect"])
                path_count += 1
                operations = len(drawing["items"])
                operation_count += operations
                if (
                    path_count > limits["max_paths"]
                    or operation_count > limits["max_operations"]
                ):
                    raise ValueError("PDF vector path/operation limit exceeded")
                area = max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])
                background = bool(width * height and area >= width * height * 0.8)
                signature = (
                    tuple(round(v, 3) for v in bbox),
                    drawing["type"],
                    operations,
                    tuple(drawing.get("fill") or ()),
                    tuple(drawing.get("color") or ()),
                )
                signatures.setdefault(signature, set()).add(page_number)
                paths.append(
                    dict(
                        index=index,
                        bbox=bbox,
                        operations=operations,
                        background=background,
                        signature=signature,
                        rectangle=any(item[0] == "re" for item in drawing["items"]),
                    )
                )
            for group in group_paths(paths, limits["grouping_gap"]):
                bbox = (
                    min(p["bbox"][0] for p in group),
                    min(p["bbox"][1] for p in group),
                    max(p["bbox"][2] for p in group),
                    max(p["bbox"][3] for p in group),
                )
                observations.append(
                    dict(
                        token=f"pdf-paths:{page_number}:"
                        + ",".join(str(p["index"]) for p in group),
                        location=dict(page=page_number, bbox=bbox),
                        tag="pdf_vectors",
                        reference=None,
                        context=dict(
                            path_indices=[p["index"] for p in group],
                            path_count=len(group),
                            operation_count=sum(p["operations"] for p in group),
                            page_background_candidate=any(
                                p["background"] for p in group
                            ),
                            rectangle_present=any(p["rectangle"] for p in group),
                            single_path=len(group) == 1,
                            page_bounds=bounds,
                            rotation=page.rotation,
                        ),
                        _signatures=[p["signature"] for p in group],
                    )
                )
                if len(observations) > limits["max_assets"]:
                    raise ValueError("PDF visual occurrence limit exceeded")
        pages = len(document)
    for observation in observations:
        if observation["tag"] == "pdf_vectors":
            observation["context"]["repeated_layout_candidate"] = any(
                len(signatures[s]) > 1 for s in observation.pop("_signatures")
            )
    return dict(
        observations=observations,
        page_count=pages,
        backend=dict(name="pymupdf", version=pymupdf.VersionBind),
    )


def main():
    destination = sys.stdout
    sys.stdout = sys.stderr
    request = json.loads(sys.stdin.read())
    limits = request["limits"]
    memory = limits["memory_mb"] * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (max(1, int(limits["timeout"])), max(2, int(limits["timeout"]) + 1)),
    )
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
    raw = base64.b64decode(request["raw"], validate=True)
    if len(raw) > limits["max_bytes"]:
        raise ValueError("Raw visual input byte limit exceeded")
    if request["kind"] == "html":
        result = html_observations(raw, limits)
    elif request["kind"] == "pdf":
        if not raw.startswith(b"%PDF-"):
            raise ValueError("Expected PDF magic")
        result = pdf_observations(raw, limits)
    else:
        raise ValueError("Only HTML/PDF visual observations supported")
    json.dump(result, destination, allow_nan=False)


if __name__ == "__main__":
    main()
