from src.model_materials.materials import NormalizedDocument
from src.tools_materials.mapping import MaterialCollection, MaterialUnit, map_material
from src.tools_materials.parse_html import parse_html
from tests.test_cs50_material_download import binding
from tests.test_cs50_material_html import HTML


def test_exact_mapping_no_invented_evidence_or_facts():
    doc, _ = parse_html(binding(), HTML)
    units = map_material(doc, max_chars=5)
    assert len({u.unit_id for u in units}) == len(units)
    assert units
    assert all(not u.knowledge_fact_verified for u in units)
    assert all(
        u.block.type not in {"math", "image_reference", "unknown_block"} for u in units
    )
    assert all(u.text == u.block.text[u.char_start : u.char_end] for u in units)
    assert all(u.binding.source_id == doc.binding.source_id for u in units)
    for u in units:
        assert MaterialUnit.model_validate_json(u.model_dump_json()) == u
    assert (
        map_material(
            NormalizedDocument.model_validate_json(doc.model_dump_json()), max_chars=5
        )
        == units
    )
    assert MaterialCollection().name != "cs50_transcript_chunks_v1"
    assert not MaterialCollection().execution_supported
