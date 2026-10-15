"""Structured HTML/assignment import. No fetches, rendered JS or inference."""

import base64
import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import (
    Block,
    ImageArtifact,
    Location,
    NormalizedDocument,
    ParserConfig,
)


def build_document(
    binding, raw, config, parts, *, title=None, images=(), metadata=None, warnings=()
):
    raw_hash = hashlib.sha256(raw).hexdigest()
    doc_id = deterministic_id(
        "material_doc", binding.material_id, raw_hash, config.config_id
    )
    blocks = tuple(
        Block(block_id=deterministic_id("material_block", doc_id, str(i)), order=i, **p)
        for i, p in enumerate(parts)
    )
    if not blocks:
        raise ValueError("No supported content blocks extracted")
    return NormalizedDocument(
        binding=binding,
        raw_sha256=raw_hash,
        parser=config,
        title=title,
        blocks=blocks,
        images=tuple(images),
        metadata=metadata or {},
        warnings=tuple(warnings),
    )


def check_input(raw, config, name):
    if config.name != name or not raw or len(raw) > config.max_bytes:
        raise ValueError(
            "Parser/input mismatch, empty input or configured byte limit exceeded"
        )


def dom_path(tag):
    parts = []
    while isinstance(tag, Tag) and tag.name != "[document]":
        same = [
            s
            for s in tag.previous_siblings
            if isinstance(s, Tag) and s.name == tag.name
        ]
        parts.append(f"{tag.name}[{len(same) + 1}]")
        tag = tag.parent
    return "/" + "/".join(reversed(parts))


def parse_html(binding, raw, config=None):
    config = config or ParserConfig(name="html")
    check_input(raw, config, "html")
    soup = BeautifulSoup(raw, "html.parser")
    if not soup.find():
        raise ValueError("Expected HTML markup")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    metadata = {
        m.get("name", m.get("property")): m.get("content")
        for m in soup.select("meta[content]")
        if m.get("name", m.get("property"))
    }
    main = soup.find("main") or soup.find("article") or soup.body or soup
    warnings = (
        []
        if main.name in {"main", "article"}
        else ["No explicit main/article landmark; boilerplate filtering is partial"]
    )
    for tag in list(main.select("nav, footer, aside, style, noscript, script")):
        if not (tag.name == "script" and str(tag.get("type", "")).startswith("math/")):
            tag.decompose()
    parts = []
    images = []
    blobs = {}

    def emit(tag, kind, text="", data=None, uncertainty=()):
        if len(parts) >= config.max_blocks:
            raise ValueError("HTML block limit exceeded")
        parts.append(
            dict(
                type=kind,
                text=text,
                data=data or {},
                location=Location(dom=dom_path(tag)),
                uncertainty=uncertainty,
            )
        )

    def image(tag):
        if len(images) >= config.max_images:
            raise ValueError("HTML image limit exceeded")
        src = tag.get("src", "")
        if not src:
            return
        url = urljoin(binding.original_url, src)
        if "_files/" in src or src.startswith(("file:", "blob:")):
            url = None
            warnings.append(
                "Browser-local image reference; original remote URL unknown"
            )
        location = Location(dom=dom_path(tag))
        image_id = deterministic_id(
            "image_ref",
            binding.material_id,
            hashlib.sha256(raw).hexdigest(),
            location.dom,
        )
        kwargs = {}
        if src.startswith("data:"):
            match = re.fullmatch(
                r"data:(image/(?:png|jpeg|gif|webp));base64,([A-Za-z0-9+/=\s]+)", src
            )
            if not match:
                warnings.append("Unsupported inline image encoding; reference only")
            else:
                content = base64.b64decode(match[2], validate=True)
                if not content or len(content) > config.max_bytes:
                    raise ValueError("Invalid/oversized inline image")
                sha = hashlib.sha256(content).hexdigest()
                path = f"images/{sha}.bin"
                blobs[path] = content
                kwargs = dict(artifact_path=path, sha256=sha, mime_type=match[1])
                url = None
        figure = tag.find_parent("figure")
        caption = figure.find("figcaption") if figure else None
        images.append(
            ImageArtifact(
                image_id=image_id,
                source_location=location,
                original_url=url,
                caption=caption.get_text(" ", strip=True)
                if caption
                else tag.get("alt"),
                context=tag.parent.get_text(" ", strip=True)[:1000],
                **kwargs,
            )
        )
        emit(
            tag,
            "image_reference",
            tag.get("alt", ""),
            dict(
                image_id=image_id,
                source_reference="inline:raster" if src.startswith("data:") else src,
            ),
        )

    def walk(tag):
        if not isinstance(tag, Tag):
            return
        name = tag.name
        if name == "img":
            image(tag)
            return
        if name == "a" and tag.get("href"):
            emit(
                tag,
                "link",
                tag.get_text(" ", strip=True),
                dict(original_url=urljoin(binding.original_url, tag["href"])),
            )
        elif name in {"math", "script"}:
            emit(
                tag,
                "math",
                tag.get_text(),
                dict(source_markup=str(tag)),
                ("source notation; not semantically verified",),
            )
            return
        elif name in {"pre"}:
            code = tag.find("code")
            emit(
                tag,
                "code",
                tag.get_text(),
                dict(language=(code or tag).get("class", [])),
            )
            return
        elif name in {"ul", "ol"}:

            def items(node):
                return [
                    dict(
                        text=" ".join(
                            str(c)
                            if not isinstance(c, Tag)
                            else c.get_text(" ", strip=True)
                            for c in li.contents
                            if not isinstance(c, Tag) or c.name not in {"ul", "ol"}
                        ).strip(),
                        children=[
                            dict(ordered=sub.name == "ol", items=items(sub))
                            for sub in li.find_all(["ul", "ol"], recursive=False)
                        ],
                    )
                    for li in node.find_all("li", recursive=False)
                ]

            emit(
                tag,
                "list",
                tag.get_text(" ", strip=True),
                dict(ordered=name == "ol", items=items(tag)),
            )
            for child in tag.find_all(["a", "img", "math", "pre"]):
                walk(child)
            return
        elif name == "table":
            rows = [
                [
                    c.get_text(" ", strip=True)
                    for c in tr.find_all(["td", "th"], recursive=False)
                ]
                for tr in tag.find_all("tr")
            ]
            emit(
                tag,
                "table",
                "\n".join("\t".join(row) for row in rows),
                data=dict(rows=rows),
            )
            for child in tag.find_all(["a", "img", "math"]):
                walk(child)
            return
        elif re.fullmatch(r"h[1-6]", name or ""):
            emit(
                tag, "heading", tag.get_text(" ", strip=True), dict(level=int(name[1]))
            )
        elif name in {"p", "figcaption", "blockquote", "dt", "dd"}:
            text = tag.get_text(" ", strip=True)
            if text:
                emit(tag, "paragraph", text)
                for expression in re.findall(r"\\\(.+?\\\)|\$\$.+?\$\$", text):
                    emit(
                        tag,
                        "math",
                        expression,
                        uncertainty=("literal notation candidate; not verified",),
                    )
        elif (
            not tag.find(True, recursive=False)
            and tag.get_text(strip=True)
            and name not in {"title", "meta", "br", "hr"}
        ):
            emit(
                tag,
                "unknown_block",
                tag.get_text(" ", strip=True),
                dict(tag=name),
                ("unclassified HTML element",),
            )
            return
        for child in tag.children:
            if isinstance(child, Tag) and not (name == "pre" and child.name == "code"):
                # inline text already belongs to its containing semantic block
                if name in {
                    "p",
                    "figcaption",
                    "blockquote",
                    "dt",
                    "dd",
                } and child.name not in {"a", "img", "math", "script"}:
                    for nested in child.find_all(["a", "img", "math", "script"]):
                        walk(nested)
                else:
                    walk(child)

    walk(main)
    return build_document(
        binding,
        raw,
        config,
        parts,
        title=title,
        images=images,
        metadata=metadata,
        warnings=warnings,
    ), blobs
