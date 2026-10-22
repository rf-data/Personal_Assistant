"""DOM-bound metadata for the existing material windows; never rewrite source text."""

from typing import Literal
from urllib.parse import urldefrag, urlsplit

from pydantic import Field

from src.model_discovery.cs50 import DiscoveryModel


class MaterialReference(DiscoveryModel):
    source_block_id: str
    source_dom: str
    text: str
    original_url: str
    relation: Literal["linked_block"] = "linked_block"
    kind: Literal[
        "internal_anchor",
        "task_material",
        "document_reference",
        "external_reference",
        "other_scheme",
    ]


class UnresolvedReference(DiscoveryModel):
    reference: MaterialReference
    reason: Literal["excluded_content", "no_unique_owner"]


class MaterialListContext(DiscoveryModel):
    source_block_id: str  # Structural list block, retained in the document.
    list_dom: str
    item_dom: str
    depth: int = Field(ge=1)
    item_index: int = Field(ge=0)
    parent_item_dom: str | None
    ordered: bool
    start: str | None
    value: str | None
    reversed: bool
    ordinal: int | None  # None when source data cannot determine numbering safely.


def dom_ancestors(dom):
    """Nearest element first; slash boundaries keep sibling ordinals distinct."""
    while dom:
        yield dom
        dom = dom.rsplit("/", 1)[0]


def reference_kind(document, url):
    source, _ = urldefrag(document.binding.original_url)
    target, fragment = urldefrag(url)
    if fragment and target == source:
        return "internal_anchor"
    parsed, base = urlsplit(url), urlsplit(source)
    if parsed.scheme not in {"http", "https"}:
        return "other_scheme"
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        return "external_reference"
    # Only a problem-set descendant is known to be an assignment/material link.
    if (
        document.binding.role == "problem_set"
        and parsed.path.startswith(base.path.rstrip("/") + "/")
        and parsed.path != base.path
    ):
        return "task_material"
    return "document_reference"


def link_owners(document, content_blocks):
    """Use source DOM containment only; text equality is never ownership evidence."""
    assigned, unresolved = {}, []
    by_dom = {}
    for block in content_blocks:
        by_dom.setdefault(block.location.dom, []).append(block)
    for link in document.blocks:
        if link.type != "link":
            continue
        ref = MaterialReference(
            source_block_id=link.block_id,
            source_dom=link.location.dom,
            text=link.text,
            original_url=link.data["original_url"],
            kind=reference_kind(document, link.data["original_url"]),
        )
        if link.data.get("content_role") == "table_of_contents":
            unresolved.append(
                UnresolvedReference(reference=ref, reason="excluded_content")
            )
            continue
        candidates = next(
            (by_dom[dom] for dom in dom_ancestors(link.location.dom) if dom in by_dom),
            [],
        )
        if len(candidates) != 1:
            unresolved.append(
                UnresolvedReference(reference=ref, reason="no_unique_owner")
            )
        else:
            assigned.setdefault(candidates[0].block_id, []).append(ref)
    return assigned, tuple(unresolved)


def list_contexts(document):
    """Retain the complete outer-to-inner ancestry and source numbering tokens."""
    lists = {b.location.dom: b for b in document.blocks if b.type == "list"}
    values = {}
    for b in document.blocks:
        for c in b.data.get("list_context", []):
            values[c["item_dom"]] = c.get("value")
    ordinals = {}
    for parent in lists.values():
        if not parent.data["ordered"]:
            continue
        reverse = parent.data.get("reversed", False)
        step = -1 if reverse else 1
        start = parent.data.get("start")
        try:
            ordinal = (
                int(start)
                if start is not None
                else (len(parent.data["item_doms"]) if reverse else 1)
            )
        except (ValueError, TypeError):
            ordinal = None
        for dom in parent.data["item_doms"]:
            if dom not in values:
                ordinal = None
            elif values[dom] is not None:
                try:
                    ordinal = int(values[dom])
                except (ValueError, TypeError):
                    ordinal = None
            ordinals[dom] = ordinal
            if ordinal is not None:
                ordinal += step
    result = {}
    for b in document.blocks:
        chain = []
        for depth, c in enumerate(b.data.get("list_context", []), 1):
            parent = lists[c["list_dom"]]
            ordered = c["ordered"]
            reverse = parent.data.get("reversed", False)
            ordinal = ordinals.get(c["item_dom"])
            chain.append(
                MaterialListContext(
                    source_block_id=parent.block_id,
                    list_dom=c["list_dom"],
                    item_dom=c["item_dom"],
                    depth=depth,
                    item_index=c["item_index"],
                    parent_item_dom=chain[-1].item_dom if chain else None,
                    ordered=ordered,
                    start=parent.data.get("start"),
                    value=c.get("value"),
                    reversed=reverse,
                    ordinal=ordinal,
                )
            )
        result[b.block_id] = tuple(chain)
    return result
