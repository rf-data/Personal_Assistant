"""Offline projection integrity, legacy snapshots and declared pilot export checks."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.model_materials.materials import ArtifactReceipt, NormalizedDocument
from src.tools_lecture.material_handoff import (
    LectureMaterialHandoff,
    _units,
    aggregation_exclusions,
    prepare_material_handoff,
)
from src.tools_materials.html_projection import link_owners
from src.tools_materials.mapping import MaterialUnit, map_material
from src.tools_materials.quality import _Audit
from src.tools_materials.quality_projection import audit_html_projection
from tests.test_cs50_material_html_semantics import parse
from tests.test_cs50_material_quality import case as case
from tests.test_cs50_material_quality import sources as sources


def project(doc, max_chars=2000):
    units = map_material(doc, projection_version=2, max_chars=max_chars)
    excluded = aggregation_exclusions(doc)
    unresolved = link_owners(
        doc, [b for b in doc.blocks if b.block_id not in excluded and b.text]
    )[1]
    return units, unresolved


def audit(doc, units=None, unresolved=None):
    result = _Audit()
    audit_html_projection(result, doc, units, unresolved)
    return result.findings


def errors(findings):
    return {f.code for f in findings if f.severity == "error"}


@pytest.mark.parametrize("max_chars", [5, 2000])
def test_multiple_links_are_metadata_once_even_across_windows(max_chars):
    d = parse(
        '<main><p>See <a href="#one">One</a>, <a href="https://example.org/x?q=1#f">Two</a>, <a href="next/">Three</a>.</p></main>'
    )
    units, unresolved = project(d, max_chars)
    assert not unresolved
    assert "".join(u.text for u in units) == "See One, Two, Three."
    refs = [r for u in units for r in u.references]
    assert [r.text for r in refs] == ["One", "Two", "Three"]
    assert [r.kind for r in refs] == [
        "internal_anchor",
        "external_reference",
        "document_reference",
    ]
    assert len(units[0].references) == 3
    assert all(not u.references for u in units[1:])
    assert [r.original_url for r in refs] == [
        b.data["original_url"] for b in d.blocks if b.type == "link"
    ]
    assert not errors(audit(d, units, unresolved))
    for u in units:
        assert MaterialUnit.model_validate_json(u.model_dump_json()) == u


def test_problem_set_seven_steps_and_five_tasks_are_reconstructible():
    from src.tools_materials.parse_html import parse_html
    from tests.test_cs50_material_download import binding

    markup = (
        "<html><title>Fixture</title><main><ol>"
        + "".join(f"<li>Step {i}</li>" for i in range(1, 7))
        + "<li><p>Submit</p><ul>"
        + "".join(
            f'<li><a href="{name}/">{name}</a></li>'
            for name in ("indoor", "playback", "faces", "einstein", "tip")
        )
        + "</ul></li></ol></main></html>"
    )
    b = binding(role="problem_set").model_dump(mode="json")
    # This is a synthetic seven-step fixture, not a replacement for the remote pilot.
    b["original_url"] = b["resource"]["original_url"] = (
        "https://cs50.harvard.edu/python/psets/0/"
    )
    from src.model_materials.materials import MaterialResource

    d = parse_html(MaterialResource.model_validate(b), markup.encode())[0]
    units, unresolved = project(d)
    assert len(units) == 12 and not unresolved
    assert [u.list_context[0].ordinal for u in units[:7]] == list(range(1, 8))
    tasks = [u for u in units if u.references]
    assert len(tasks) == 5
    assert [u.list_context[-1].item_index for u in tasks] == list(range(5))
    assert all(
        u.list_context[-1].parent_item_dom == units[6].list_context[0].item_dom
        for u in tasks
    )
    assert all(u.references[0].kind == "task_material" for u in tasks)
    assert not errors(audit(d, units, unresolved))


def test_three_levels_numbering_multipart_code_and_reversed():
    d = parse(
        '<main><ol start="3"><li value="8"><p>A</p><p>B</p><pre>\tprint(&quot;x&quot;)\n\n</pre><ul><li>Nested<ol reversed start="5"><li>Deep</li><li value="2">Last</li></ol></li></ul></li><li>Next</li></ol></main>'
    )
    units, unresolved = project(d, 7)
    outer = [u for u in units if len(u.list_context) == 1]
    assert all(u.list_context[0].ordinal == 8 for u in outer[:-1])
    assert outer[-1].list_context[0].ordinal == 9
    first_item = units[0].list_context[0]
    assert all(u.list_context[0] == first_item for u in outer[:-1])
    deep = [u for u in units if len(u.list_context) == 3]
    assert [u.list_context[-1].ordinal for u in deep] == [5, 2]
    assert all(
        u.list_context[-1].depth == 3 and u.list_context[-1].reversed for u in deep
    )
    assert (
        "".join(u.text for u in units if u.block.type == "code") == '\tprint("x")\n\n'
    )
    assert not errors(audit(d, units, unresolved))


@pytest.mark.parametrize(
    "markup,reason",
    [
        (
            '<main><ul id="toc"><li><a href="#x">X</a></li></ul></main>',
            "excluded_content",
        ),
        (
            '<main><p>Lead<a href="/x">X</a><img src="x">Tail</p></main>',
            "no_unique_owner",
        ),
        (
            '<main><p>Lead<a href="/x"><img src="x"></a>Tail</p></main>',
            "no_unique_owner",
        ),
    ],
)
def test_ambiguous_and_excluded_references_are_explicit(markup, reason):
    d = parse(markup)
    units, unresolved = project(d)
    assert len(unresolved) == 1 and unresolved[0].reason == reason
    assert not any(u.references for u in units)
    findings = audit(d, units, unresolved)
    f = next(f for f in findings if f.code == "reference_unresolved")
    assert f.severity == ("info" if reason == "excluded_content" else "warning")
    assert f.block_id == unresolved[0].reference.source_block_id
    assert not errors(findings)


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "reference_projection_missing"),
        ("duplicate", "reference_duplicate"),
        ("url", "reference_projection_invalid"),
        ("kind", "reference_projection_invalid"),
        ("dom", "reference_projection_invalid"),
        ("absent_source", "reference_source_missing"),
        ("wrong_owner", "reference_projection_invalid"),
    ],
)
def test_reference_projection_corruption(change, code):
    d = parse('<main><p><a href="#x">X</a></p><p>Other</p></main>')
    units, unresolved = project(d)
    first, other = units
    ref = first.references[0]
    if change == "missing":
        first = first.model_copy(update={"references": ()})
    elif change == "duplicate":
        first = first.model_copy(update={"references": (ref, ref)})
    elif change == "wrong_owner":
        first = first.model_copy(update={"references": ()})
        other = other.model_copy(update={"references": (ref,)})
    else:
        field, value = {
            "url": ("original_url", "https://changed.test/"),
            "kind": ("kind", "external_reference"),
            "dom": ("source_dom", "/wrong[1]"),
            "absent_source": ("source_block_id", "missing"),
        }[change]
        first = first.model_copy(
            update={"references": (ref.model_copy(update={field: value}),)}
        )
    findings = audit(d, (first, other), unresolved)
    assert code in errors(findings)
    assert any(f.block_id for f in findings if f.code == code)


@pytest.mark.parametrize(
    "change", ["missing", "reverse", "parent", "depth", "item_order", "value_conflict"]
)
def test_broken_list_hierarchies_fail(change):
    d = parse(
        "<main><ol><li><p>A</p><p>B</p><ul><li>Nested</li></ul></li><li>Last</li></ol></main>"
    )
    if change in {"parent", "depth"}:
        units, unresolved = project(d)
        u = next(u for u in units if u.text == "Nested")
        c = u.list_context[-1].model_copy(
            update={"parent_item_dom": "/wrong[1]"}
            if change == "parent"
            else {"depth": 9}
        )
        units = tuple(
            x.model_copy(update={"list_context": (*x.list_context[:-1], c)})
            if x == u
            else x
            for x in units
        )
        assert "list_hierarchy_inconsistent" in errors(audit(d, units, unresolved))
        return
    payload = json.loads(d.model_dump_json())
    nested = next(b for b in payload["blocks"] if b["text"] == "Nested")
    if change == "missing":
        nested["data"]["list_context"].pop(0)
    elif change == "reverse":
        nested["data"]["list_context"].reverse()
    elif change == "item_order":
        next(b for b in payload["blocks"] if b["type"] == "list")["data"][
            "item_doms"
        ].reverse()
    else:
        next(b for b in payload["blocks"] if b["text"] == "B")["data"]["list_context"][
            0
        ]["value"] = "9"
    assert errors(
        audit(NormalizedDocument.model_validate_json(json.dumps(payload)))
    ) & {"list_parent_missing", "list_hierarchy_inconsistent"}


@pytest.mark.parametrize(
    "mutation", ["omit_code", "duplicate_code", "alter_code", "structural_unit"]
)
def test_code_coverage_and_structural_duplicates_fail(mutation):
    d = parse('<main><p>A<a href="/x">X</a></p><pre>print("hi")\n</pre></main>')
    units, unresolved = project(d)
    code = units[-1]
    if mutation == "omit_code":
        units = units[:-1]
    elif mutation == "duplicate_code":
        units = (*units, code)
    elif mutation == "alter_code":
        units = (*units[:-1], code.model_copy(update={"text": "changed"}))
    else:
        link_unit = next(u for u in map_material(d) if u.block.type == "link")
        units = (*units, link_unit)
    assert errors(audit(d, units, unresolved)) & {
        "aggregation_content_mismatch",
        "projection_invalid",
    }


def test_unknown_numbering_and_empty_item_are_reported_without_guess():
    d = parse(
        '<main><ol start="bad"><li>A</li></ol><ol><li></li><li>B</li><li value="9">C</li></ol></main>'
    )
    units, unresolved = project(d)
    assert [u.list_context[0].ordinal for u in units] == [None, None, 9]
    assert (
        sum(f.code == "list_numbering_unresolved" for f in audit(d, units, unresolved))
        == 2
    )


def test_new_handoff_and_legacy_snapshot_compatibility(case):
    paths = case()
    review = prepare_material_handoff(**paths)
    h = review.handoff
    assert review.report.schema_version == h.schema_version == 2
    assert h.adapter_version == "cs50_lecture_material_v2"
    assert LectureMaterialHandoff.model_validate_json(h.model_dump_json()) == h
    payload = json.loads(h.model_dump_json())
    payload.update(
        schema_version=1,
        adapter_version="cs50_lecture_material_v1",
        aggregation_units=[
            json.loads(u.model_dump_json()) for u in _units(h.document, 1)
        ],
    )
    payload.pop("unresolved_references")
    for u in payload["aggregation_units"]:
        u.pop("references", None)
        u.pop("list_context", None)
    legacy = LectureMaterialHandoff.model_validate_json(json.dumps(payload))
    assert legacy.schema_version == 1
    assert "unresolved_references" not in json.loads(legacy.model_dump_json())
    assert all(
        "references" not in json.loads(u.model_dump_json())
        for u in legacy.aggregation_units
    )
    assert [(u.unit_id, u.text) for u in legacy.aggregation_units] == [
        (u.unit_id, u.text) for u in h.aggregation_units
    ]
    broken = json.loads(h.model_dump_json())
    next(u for u in broken["aggregation_units"] if u["references"])["references"][0][
        "original_url"
    ] = "https://wrong.test/"
    with pytest.raises(ValidationError):
        LectureMaterialHandoff.model_validate_json(json.dumps(broken))


@pytest.mark.parametrize(
    "material,blocks,codes,units_count,links",
    [
        ("material_01", 237, 34, 171, None),
        ("material_02", 28, 0, 16, 10),
    ],
)
def test_optional_exact_week0_export(material, blocks, codes, units_count, links):
    root = os.environ.get("CS50_WEEK0_QUALITY_EXPORT")
    if not root:
        pytest.skip(
            "Real pilot exports are remote; user prohibits SSH/downloads. Await local copies."
        )
    folder = Path(root) / material
    before = {
        p: p.read_bytes()
        for p in (
            folder / "original.html",
            folder / "normalized.v1.json",
            folder / "quality.v1.json",
        )
    }
    doc = NormalizedDocument.model_validate_json(before[folder / "normalized.v1.json"])
    assert (
        doc.raw_sha256 == hashlib.sha256(before[folder / "original.html"]).hexdigest()
    )
    assert len(doc.blocks) == blocks
    assert sum(b.type == "code" for b in doc.blocks) == codes
    if links is not None:
        assert sum(b.type == "link" for b in doc.blocks) == links
    old, new = _units(doc, 1), _units(doc, 2)
    assert len(old) == len(new) == units_count
    assert [(u.unit_id, u.block, u.text, u.char_start, u.char_end) for u in old] == [
        (u.unit_id, u.block, u.text, u.char_start, u.char_end) for u in new
    ]
    assert not errors(audit(doc))
    from bs4 import BeautifulSoup

    from src.tools_materials.parse_html import dom_path

    main = BeautifulSoup(before[folder / "original.html"], "html.parser").find("main")
    assert main is not None
    raw_codes = {
        dom_path(tag): tag.get_text("", strip=False)
        for tag in main.find_all("pre")
        if not any(
            parent.name in {"nav", "footer", "aside", "style", "noscript"}
            for parent in tag.parents
        )
    }
    assert raw_codes == {b.location.dom: b.text for b in doc.blocks if b.type == "code"}
    if material == "material_02":
        assert sum(r.kind == "task_material" for u in new for r in u.references) == 5
        tasks = [u for u in new if any(r.kind == "task_material" for r in u.references)]
        assert len(tasks) == 5
        assert all(
            len(u.list_context) == 2
            and u.list_context[0].ordered
            and u.list_context[0].item_index == 6
            and u.list_context[0].ordinal == 7
            for u in tasks
        )
        assert len({u.list_context[-1].parent_item_dom for u in tasks}) == 1
        outer = next(
            b
            for b in doc.blocks
            if b.block_id == tasks[0].list_context[0].source_block_id
        )
        assert len(outer.data["item_doms"]) == 7

    assert {p: p.read_bytes() for p in before} == before


def test_all_existing_notes_assignment_fixtures_keep_exact_windows():
    from src.model_discovery.cs50 import ResourceCandidate
    from src.model_materials.materials import MaterialResource
    from src.tools_lecture.cs50_manifest import load_fixture_manifest
    from src.tools_materials.parse_html import parse_html

    root = Path("docs/course_sources/cs50")
    manifest = load_fixture_manifest(root / "manifest.json")
    baselines = {
        row["file"]: row
        for row in json.loads(
            Path(
                "tests/fixtures/material_quality/html_projection_baseline.v1.json"
            ).read_text()
        )["fixtures"]
    }
    count = 0
    for course in manifest.courses:
        for page in course.pages:
            if page.role not in {"lecture_notes", "assignment"}:
                continue
            raw = (root / page.file).read_bytes()
            role = "notes" if page.role == "lecture_notes" else "problem_set"
            r = ResourceCandidate(
                course_id=course.course_id, role=role, original_url=page.url
            )
            d = parse_html(
                MaterialResource(
                    resource=r, original_url=str(page.url), role=role, format="html"
                ),
                raw,
            )[0]
            before, after = _units(d, 1), _units(d, 2)
            assert [
                (u.unit_id, u.block, u.char_start, u.char_end, u.text) for u in before
            ] == [(u.unit_id, u.block, u.char_start, u.char_end, u.text) for u in after]
            row = baselines[page.file]
            windows = [
                (u.unit_id, u.block.block_id, u.char_start, u.char_end, u.text)
                for u in after
            ]
            assert (
                hashlib.sha256(
                    json.dumps(
                        windows, ensure_ascii=False, separators=(",", ":")
                    ).encode()
                ).hexdigest()
                == row["windows_sha256"]
            )
            assert hashlib.sha256(raw).hexdigest() == row["raw_sha256"]
            assert (
                len(before) == len(after) == row["units_before"] == row["units_after"]
            )
            assert not errors(audit(d))
            assert (root / page.file).read_bytes() == raw
            count += 1
    assert count == 5


@pytest.mark.parametrize("broken", [False, True])
def test_end_to_end_gate_list_reference_projection(case, broken):
    from src.tools_materials.parse_html import parse_html
    from src.tools_materials.quality import validate_material

    paths = case()
    receipt = ArtifactReceipt.model_validate_json(paths["receipt_path"].read_bytes())
    raw = b'<html><title>Offline fixture</title><main><ol start="4"><li><p>See <a href="#x">X</a> and <a href="help/">Help</a>.</p><pre>print("hi")\n</pre></li></ol></main></html>'
    doc = parse_html(receipt.binding, raw)[0]
    if broken:
        data = json.loads(doc.model_dump_json())
        next(b for b in data["blocks"] if b["type"] == "code")["data"][
            "list_context"
        ] = []
        doc = NormalizedDocument.model_validate_json(json.dumps(data))
    normalized = doc.model_dump_json().encode()
    paths["raw_path"].write_bytes(raw)
    paths["normalized_path"].write_bytes(normalized)
    receipt = receipt.model_copy(
        update={
            "raw_sha256": doc.raw_sha256,
            "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
        }
    )
    paths["receipt_path"].write_text(receipt.model_dump_json())
    before = {p: p.read_bytes() for p in paths["workspace"].rglob("*") if p.is_file()}
    review = prepare_material_handoff(**paths)
    assert review.report == validate_material(**paths)
    if broken:
        assert review.report.status == "failed" and review.handoff is None
        assert "list_hierarchy_inconsistent" in errors(review.report.findings)
        assert any(
            f.block_id
            for f in review.report.findings
            if f.code == "list_hierarchy_inconsistent"
        )
    else:
        assert review.report.passed
        assert [
            r.text for u in review.handoff.aggregation_units for r in u.references
        ] == ["X", "Help"]
        assert (
            "".join(
                u.text
                for u in review.handoff.aggregation_units
                if u.block.type == "code"
            )
            == 'print("hi")\n'
        )
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize(
    "filename", ["material-quality-html.v1.json", "material-quality-pdf.v1.json"]
)
def test_existing_v1_quality_reports_stay_readable(filename):
    from src.model_materials.quality import MaterialQualityReport

    report = MaterialQualityReport.model_validate_json(
        (Path("docs/cs50/examples") / filename).read_bytes()
    )
    assert report.schema_version == 1
    assert report.validator_version == "cs50_material_quality_v1"
    assert MaterialQualityReport.model_validate_json(report.model_dump_json()) == report


def test_equal_link_text_uses_dom_and_other_document_anchor_stays_document_reference():
    d = parse(
        '<main><p><a href="https://cs50.harvard.edu/python/notes/1/#x">Same</a></p><p><a href="mailto:a@example.org">Same</a></p></main>'
    )
    units, unresolved = project(d)
    assert not unresolved
    assert [u.references[0].kind for u in units] == [
        "document_reference",
        "other_scheme",
    ]
    assert len({u.references[0].source_block_id for u in units}) == 2
    assert not errors(audit(d, units, unresolved))
