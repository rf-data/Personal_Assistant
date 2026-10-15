"""Synthetic materials over real six-course/lecture identities. Never real HTTP."""

import json

import httpx

from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import MaterialResource
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.mapping import map_material
from src.tools_materials.processing import MaterialPlan, MaterialProcessor, make_plan
from src.tools_materials.storage import artifact_root, save_model

HTML = b'<html><head><title>Own synthetic note</title></head><body><main><h1>Function</h1><p>A function accepts an argument.</p><pre><code>print("own fixture")</code></pre><img src="figure.png" alt="Unfetched image"></main></body></html>'


def pdf():
    import pymupdf

    doc = pymupdf.open()
    a = doc.new_page()
    a.insert_text((30, 40), "Own fixture: x = y + 1")
    b = doc.new_page()
    b.insert_text((30, 40), "Second slide")
    raw = doc.tobytes()
    doc.close()
    return raw


def demo(manifest, output, *, course=None, all_courses=False):
    if all_courses and course:
        raise ValueError("Choose course or all_courses")
    root = artifact_root(output)
    root.mkdir(parents=True, exist_ok=False)
    base = make_plan(manifest)
    selected = [
        b
        for b in base.materials
        if b.role == "notes" and (not course or b.resource.course_id == course)
    ]
    if not course and not all_courses:
        selected = selected[:1]
    if not selected:
        raise ValueError("No matching demo course")
    rows = [
        b.model_copy(
            update={"source_origin": "synthetic", "license_status": "reviewed"}
        )
        for b in selected
    ]
    # Additional own synthetic resources are explicitly added to a separate demo graph,
    # not claimed as discovered remote offers. Only the first lecture is mixed-material.
    first = rows[0]
    synthetic = []
    for suffix, role, fmt in [
        ("slides.pdf", "slides", "pdf"),
        ("example.py", "source_code", "py"),
        ("assignment.html", "problem_set", "html"),
    ]:
        url = (
            str(first.resource.original_url).rstrip("/")
            + "/synthetic-fixture/"
            + suffix
        )
        r = ResourceCandidate(
            course_id=first.resource.course_id,
            role=role,
            original_url=url,
            section_keys=first.resource.section_keys,
            parent_resource_id=first.lecture_ids[0],
        )
        synthetic.append(r)
        rows.append(
            MaterialResource(
                resource=r,
                original_url=url,
                role=role,
                format=fmt,
                lecture_ids=first.lecture_ids,
                source_origin="synthetic",
                license_status="reviewed",
            )
        )
    graphs = tuple(
        c.model_copy(update={"resources": c.resources + tuple(synthetic)})
        if c.course_id == first.resource.course_id
        else c
        for c in base.courses
    )
    plan = MaterialPlan(courses=graphs, materials=tuple(rows))
    save_model(root / "demo-plan.v1.json", plan)
    bodies = {
        b.original_url: (
            pdf()
            if b.format == "pdf"
            else b'# Own fixture\nprint("hello")\n'
            if b.format == "py"
            else HTML
        )
        for b in rows
    }

    def fake(req):
        if str(req.url) not in bodies:
            raise AssertionError("Undeclared demo URL")
        b = next(b for b in rows if b.original_url == str(req.url))
        mime = (
            "application/pdf"
            if b.format == "pdf"
            else "text/plain"
            if b.format == "py"
            else "text/html"
        )
        return httpx.Response(
            200, content=bodies[str(req.url)], headers={"content-type": mime}
        )

    downloader = MaterialDownloader(root, transport=httpx.MockTransport(fake))
    processor = MaterialProcessor(root)
    receipts = []
    units = 0
    from src.model_materials.materials import NormalizedDocument

    for b in rows:
        downloader.obtain(b, execute=True, license_reviewed=True)
        receipt = processor.parse(b, execute=True)
        assert processor.parse(b, execute=True) == receipt
        doc = NormalizedDocument.model_validate_json(
            (root / receipt.normalized_path).read_bytes()
        )
        units += len(map_material(doc))
        receipts.append(receipt)
    result = dict(
        schema_version=1,
        source_origin="synthetic",
        courses=len({b.resource.course_id for b in rows}),
        main_lectures=len(selected),
        materials_completed=len(receipts),
        extra_own_fixture_materials=3,
        mapped_units=units,
        real_downloads=0,
        unfetched_images=len(selected) + 1,
        known_snapshot_candidates=len(base.materials),
        coverage="selected synthetic subset; not live reachability",
    )
    from src.tools_materials.storage import publish_bytes

    publish_bytes(
        root / "demo-result.v1.json", (json.dumps(result, indent=2) + "\n").encode()
    )
    return result
