"""Structured HTML/assignment import. No fetches, rendered JS or inference."""

import base64
import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

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
    config = config or ParserConfig(name="html", version="2")
    check_input(raw, config, "html")
    if config.version != "2":
        raise ValueError("HTML parser v1 is read-only; use v2 in a new workspace")
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
                data={**context(tag), **(data or {})},
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

    def toc(tag):
        # Explicit publisher markup, never a guess from a list of anchor links.
        return (
            tag.get("id") in {"markdown-toc", "toc", "table-of-contents"}
            or bool(set(tag.get("class", ())) & {"toc", "table-of-contents"})
            or tag.get("role") == "doc-toc"
            or str(tag.get("aria-label", "")).casefold()
            in {"table of contents", "inhaltsverzeichnis"}
        )

    def context(tag):
        ancestors = list(reversed([tag, *tag.parents]))
        data = {}
        if any(toc(a) for a in ancestors if isinstance(a, Tag)):
            data["content_role"] = "table_of_contents"
        items = []
        for li in ancestors:
            if not isinstance(li, Tag) or li.name != "li":
                continue
            parent = li.parent
            if not isinstance(parent, Tag) or parent.name not in {"ul", "ol"}:
                continue
            items.append(
                dict(
                    list_dom=dom_path(parent),
                    item_dom=dom_path(li),
                    item_index=sum(
                        isinstance(s, Tag) and s.name == "li"
                        for s in li.previous_siblings
                    ),
                    ordered=parent.name == "ol",
                    value=li.get("value"),
                )
            )
        if items:
            data["list_context"] = items
        return data

    def language(tag):
        for ancestor in [tag, *tag.parents]:
            if not isinstance(ancestor, Tag):
                continue
            if ancestor.name in {"main", "body", "html"}:
                break
            for attr in ("data-language", "lang"):
                if ancestor.get(attr):
                    return ancestor[attr]
            for cls in ancestor.get("class", ()):
                if cls.startswith(("language-", "lang-")):
                    return cls.split("-", 1)[1]
        return None

    ignored = {"footer", "aside", "style", "noscript", "title", "meta"}
    inline_tags = {
        "a",
        "abbr",
        "b",
        "bdi",
        "bdo",
        "br",
        "cite",
        "code",
        "del",
        "em",
        "i",
        "img",
        "ins",
        "kbd",
        "mark",
        "math",
        "q",
        "s",
        "samp",
        "small",
        "span",
        "strong",
        "sub",
        "sup",
        "time",
        "u",
        "var",
        "wbr",
        "script",
    }

    def hidden(tag):
        return (
            tag.name in ignored
            or (tag.name == "nav" and not toc(tag))
            or (
                tag.name == "script"
                and not str(tag.get("type", "")).startswith("math/")
            )
        )

    def inline(nodes):
        chunks = []

        def visit(node):
            if isinstance(node, Comment):
                return
            if isinstance(node, NavigableString):
                chunks.append([re.sub(r"\s+", " ", str(node)), None])
            elif isinstance(node, Tag) and not hidden(node):
                if node.name == "code":
                    chunks.append([node.get_text("", strip=False), node])
                elif node.name == "br":
                    chunks.append(["\n", None])
                elif node.name != "img":
                    for child in node.children:
                        visit(child)

        for node in nodes:
            visit(node)
        # Trim only ordinary HTML whitespace, never code's own whitespace.
        while chunks and chunks[0][1] is None and not chunks[0][0].strip():
            chunks.pop(0)
        while chunks and chunks[-1][1] is None and not chunks[-1][0].strip():
            chunks.pop()
        if chunks and chunks[0][1] is None:
            chunks[0][0] = chunks[0][0].lstrip()
        if chunks and chunks[-1][1] is None:
            chunks[-1][0] = chunks[-1][0].rstrip()
        text = ""
        spans = []
        for value, code in chunks:
            if code is not None:
                spans.append(
                    dict(
                        start=len(text),
                        end=len(text) + len(value),
                        text=value,
                        dom=dom_path(code),
                        language=language(code),
                    )
                )
            text += value
        return text, spans

    def references(node):
        if not isinstance(node, Tag) or hidden(node):
            return
        if node.name == "img":
            image(node)
            return
        if node.name == "a" and node.get("href"):
            text, spans = inline(node.children)
            emit(
                node,
                "link",
                text,
                dict(
                    original_url=urljoin(binding.original_url, node["href"]),
                    reference_only=True,
                    inline_code=spans,
                ),
            )
        elif node.name in {"math", "script"}:
            emit(
                node,
                "math",
                node.get_text(),
                dict(source_markup=str(node), reference_only=True),
                ("source notation; not semantically verified",),
            )
            return
        for child in node.children:
            references(child)

    def flow(tag, kind="paragraph", data=None):
        run = []
        fragment = 0

        def flush():
            nonlocal fragment
            if not run:
                return
            text, spans = inline(run)
            if text:
                emit(
                    tag,
                    kind,
                    text,
                    dict(
                        **(data or {}),
                        fragment_index=fragment,
                        inline_code=spans,
                    ),
                )
                fragment += 1
                for expression in re.findall(r"\\\(.+?\\\)|\$\$.+?\$\$", text):
                    emit(
                        tag,
                        "math",
                        expression,
                        dict(reference_only=True),
                        ("literal notation candidate; not verified",),
                    )
            for child in run:
                references(child)
            run.clear()

        for child in tag.children:
            if isinstance(child, Tag) and (
                child.name not in inline_tags
                or child.name == "img"
                or child.find(["pre", "ul", "ol", "p", "div", "figure", "img", "table"])
                is not None
            ):
                flush()
                walk(child)
            else:
                run.append(child)
        flush()

    def walk(tag):
        if not isinstance(tag, Tag) or hidden(tag):
            return
        name = tag.name
        if name == "img":
            image(tag)
        elif name == "a" and tag.get("href"):
            text, spans = inline(tag.children)
            emit(
                tag,
                "link",
                text,
                dict(
                    original_url=urljoin(binding.original_url, tag["href"]),
                    reference_only=True,
                    inline_code=spans,
                ),
            )
            flow(tag)
        elif name == "pre":
            code = tag.find("code")
            emit(
                tag,
                "code",
                tag.get_text("", strip=False),
                dict(
                    language=language(code or tag),
                    language_classes=(code or tag).get("class", []),
                ),
            )
        elif name in {"ul", "ol"}:
            emit(
                tag,
                "list",
                data=dict(
                    ordered=name == "ol",
                    start=tag.get("start"),
                    reversed=tag.has_attr("reversed"),
                    item_doms=[
                        dom_path(li) for li in tag.find_all("li", recursive=False)
                    ],
                ),
            )
            for child in tag.children:
                if isinstance(child, Tag):
                    walk(child)
        elif name == "table":
            rows = [
                [
                    c.get_text(" ", strip=True)
                    for c in tr.find_all(["td", "th"], recursive=False)
                ]
                for tr in tag.find_all("tr")
            ]
            emit(
                tag, "table", "\n".join("\t".join(row) for row in rows), dict(rows=rows)
            )
            references(tag)
        elif re.fullmatch(r"h[1-6]", name or ""):
            flow(tag, "heading", dict(level=int(name[1])))
        elif name in inline_tags:
            flow(tag)
        elif (
            not tag.find(True, recursive=False)
            and tag.get_text(strip=True)
            and name
            not in {
                "main",
                "article",
                "body",
                "div",
                "section",
                "li",
                "p",
                "figcaption",
                "blockquote",
                "dt",
                "dd",
                "header",
                "hr",
            }
        ):
            emit(
                tag,
                "unknown_block",
                tag.get_text(" ", strip=True),
                dict(tag=name),
                ("unclassified HTML element",),
            )
        else:
            flow(tag)

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
