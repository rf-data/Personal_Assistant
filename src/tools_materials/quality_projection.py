"""Technical integrity checks for v2 HTML handoff metadata, without raw reparsing."""

from collections import Counter, defaultdict

from src.tools_materials.html_projection import (
    dom_ancestors,
    link_owners,
    list_contexts,
    reference_kind,
)
from src.tools_materials.mapping import aggregation_exclusions, map_material


def audit_html_projection(audit, document, units=None, unresolved=None):
    if document.parser.name != "html" or document.parser.version != "2":
        return
    if any(f.severity == "error" for f in audit.findings):
        return
    blocks = {b.block_id: b for b in document.blocks}
    lists = [b for b in document.blocks if b.type == "list"]
    excluded = aggregation_exclusions(document)
    eligible = [b for b in document.blocks if b.block_id not in excluded and b.text]
    last_items, values = {}, {}
    item_sources = {}
    for parent in lists:
        for index, dom in enumerate(parent.data.get("item_doms", [])):
            if dom in item_sources:
                audit.add(
                    "list_hierarchy_inconsistent",
                    "Duplicate structural list/item DOM",
                    block=parent,
                )
            item_sources[dom] = (parent, index, dom)
    for block in document.blocks:
        contexts = block.data.get("list_context", [])
        expected = [
            item_sources[dom]
            for dom in reversed(tuple(dom_ancestors(block.location.dom)))
            if dom in item_sources
        ]
        if any(parent.order >= block.order for parent, _, _ in expected):
            audit.add(
                "list_hierarchy_inconsistent",
                "List content precedes its structural parent",
                block=block,
            )
        if not isinstance(contexts, list) or len(contexts) != len(expected):
            audit.add(
                "list_hierarchy_inconsistent",
                "List ancestry is incomplete or has an inconsistent depth",
                block=block,
            )
            continue
        for context, (parent, index, dom) in zip(contexts, expected, strict=True):
            if not isinstance(context, dict) or (
                context.get("list_dom"),
                context.get("item_dom"),
                context.get("item_index"),
                context.get("ordered"),
            ) != (parent.location.dom, dom, index, parent.data.get("ordered")):
                audit.add(
                    "list_parent_missing",
                    "Context does not identify the enclosing source list/item",
                    block=block,
                )
                continue
            value = context.get("value")
            if dom in values and values[dom] != value:
                audit.add(
                    "list_hierarchy_inconsistent",
                    "Blocks in one item disagree about its explicit HTML value",
                    block=block,
                )
            values[dom] = value
            previous = last_items.get(parent.block_id, -1)
            if index < previous:
                audit.add(
                    "list_hierarchy_inconsistent",
                    "List item order moves backwards",
                    block=block,
                )
            last_items[parent.block_id] = index
    for parent in lists:
        doms = parent.data.get("item_doms", [])
        if not isinstance(doms, list) or doms != [
            f"{parent.location.dom}/li[{i + 1}]" for i in range(len(doms))
        ]:
            audit.add(
                "list_hierarchy_inconsistent",
                "Source item DOMs are not in direct sibling order",
                block=parent,
            )
    if any(f.severity == "error" for f in audit.findings):
        return  # Source integrity must hold before constructing typed projections.
    try:
        assigned, expected_unresolved = link_owners(document, eligible)
        expected_contexts = list_contexts(document)
        if units is None:
            units = map_material(document, projection_version=2)
        if unresolved is None:
            unresolved = expected_unresolved
    except (ValueError, KeyError, TypeError) as exc:
        audit.add(
            "projection_invalid", f"Cannot construct typed HTML projection: {exc}"
        )
        return
    seen = Counter()
    windows_by_block = defaultdict(list)
    for unit in units:
        block = blocks.get(unit.block.block_id)
        if block is None:
            audit.add(
                "projection_invalid",
                "Unit refers to an absent source block",
                block=unit.block,
            )
            continue
        windows_by_block[block.block_id].append(unit)
        if block.block_id in excluded:
            audit.add(
                "projection_invalid",
                "Structural/reference content became an extra text unit",
                block=block,
            )
        if unit.list_context != expected_contexts.get(block.block_id, ()):
            audit.add(
                "list_hierarchy_inconsistent",
                "Projected ancestry differs from original source contexts",
                block=block,
            )
        for ref in unit.references:
            seen[ref.source_block_id] += 1
            source = blocks.get(ref.source_block_id)
            if source is None or source.type != "link":
                audit.add(
                    "reference_source_missing",
                    "Projected link source does not exist",
                    block=block,
                )
                continue
            if (
                ref.original_url != source.data.get("original_url")
                or ref.source_dom != source.location.dom
                or ref.text != source.text
                or ref.kind != reference_kind(document, source.data["original_url"])
            ):
                audit.add(
                    "reference_projection_invalid",
                    "URL, DOM, text or link classification differs from source",
                    block=source,
                )
            if ref not in assigned.get(block.block_id, []) or unit.char_start != 0:
                audit.add(
                    "reference_projection_invalid",
                    "Link is not attached once to its uniquely resolved source block's first window",
                    block=source,
                )
    if tuple(unresolved) != expected_unresolved:
        audit.add(
            "reference_projection_invalid",
            "Unresolved reference inventory differs from source ownership",
        )
    for entry in unresolved:
        ref = entry.reference
        seen[ref.source_block_id] += 1
        source = blocks.get(ref.source_block_id)
        audit.add(
            "reference_unresolved",
            f"Reference retained without text ownership: {entry.reason}",
            severity="info" if entry.reason == "excluded_content" else "warning",
            block=source,
        )
    for block in document.blocks:
        if block.type == "link":
            count = seen[block.block_id]
            if count != 1:
                audit.add(
                    "reference_duplicate"
                    if count > 1
                    else "reference_projection_missing",
                    f"Expected one link projection or unresolved record; found {count}",
                    block=block,
                )
    # Exact windows must cover each original text block once, including every code character.
    for block in eligible:
        windows = windows_by_block[block.block_id]
        cursor = 0
        for unit in windows:
            if (
                unit.block != block
                or unit.char_start != cursor
                or unit.text != block.text[unit.char_start : unit.char_end]
            ):
                audit.add(
                    "aggregation_content_mismatch",
                    "Projection changed source block, character content or window order",
                    block=block,
                )
            cursor = unit.char_end
        if cursor != len(block.text):
            audit.add(
                "aggregation_content_mismatch",
                "Projection does not cover the complete source text/code",
                block=block,
            )
    for block in eligible:
        if any(
            c.ordered and c.ordinal is None
            for c in expected_contexts.get(block.block_id, ())
        ):
            audit.add(
                "list_numbering_unresolved",
                "Available source metadata does not determine the displayed list number",
                severity="warning",
                block=block,
            )
