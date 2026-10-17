"""Owned synthetic processed bundles; no course originals or external services."""

import json
from pathlib import Path

from src.content_store.adapters import ImplementationEvidence, MaterialBundle, SRTBundle
from src.content_store.models import sha256
from src.model_discovery.cs50 import (
    CourseDiscovery,
    Provenance,
    ResourceCandidate,
    SectionDiscovery,
)
from src.model_materials.materials import (
    ArtifactReceipt,
    MaterialPlan,
    MaterialResource,
    ParserConfig,
)
from src.tools_lecture.adapt_cs50 import CS50AdapterPlan
from src.tools_lecture.execute_cs50 import validate_document
from src.tools_materials.parse_code import parse_code
from src.tools_materials.parse_html import build_document, parse_html
from src.tools_transcribe.import_transcript import import_srt

ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40  # Explicit synthetic implementation attestation, not inferred HEAD.


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def attest(bundle, *, revision=REVISION):
    payload = getattr(bundle, "normalized_path", None) or bundle.transcript_path
    if isinstance(bundle, MaterialBundle):
        value = json.loads(payload.read_bytes())
        from src.model_materials.materials import NormalizedDocument

        doc = NormalizedDocument.model_validate(value)
        source, identity = doc.binding.source_id, doc.binding.material_id
        name, version, params = (
            doc.parser.name,
            doc.parser.version,
            doc.parser.model_dump(mode="json"),
        )
    else:
        source = identity = bundle.source_id
        plan = CS50AdapterPlan.model_validate_json(bundle.plan_path.read_bytes())
        binding = next(
            b for c in plan.courses for b in c.bindings if b.source_id == source
        )
        name, version = "srt", "1"
        params = dict(
            encoding="utf-8-sig",
            media_format="srt",
            language=binding.language,
            preserve_empty_cues=True,
        )
    evidence = ImplementationEvidence(
        implementation_revision=revision,
        parser_name=name,
        parser_version=version,
        parameters=params,
        source_id=source,
        binding_id=identity,
        raw_sha256=sha256(bundle.raw_path.read_bytes()),
        payload_sha256=sha256(payload.read_bytes()),
        receipt_sha256=sha256(bundle.receipt_path.read_bytes()),
        evidence_reference="Synthetic fixture authored independently for C23-02B tests",
    )
    dump(bundle.implementation_path, evidence.model_dump(mode="json"))


def material(tmp_path, kind="html", *, local_image=False, max_blocks=20000):
    lecture = ResourceCandidate(
        course_id="cs50_python",
        role="lecture_video",
        original_url="https://cs50.harvard.edu/python/lectures/0/",
        section_keys=("0",),
    )
    format_ = "py" if kind == "code" else kind
    resource = ResourceCandidate(
        course_id="cs50_python",
        role="source_code" if kind != "html" else "notes",
        original_url=f"https://cs50.harvard.edu/python/notes/0/test.{format_}",
        section_keys=("0",),
        provenance=(
            Provenance(
                original_url="https://cs50.harvard.edu/python/weeks/0/",
                fixture_file=f"synthetic.{format_}",
                locator="authored synthetic fixture",
            ),
        ),
    )
    binding = MaterialResource(
        resource=resource,
        lecture_ids=(lecture.resource_id,),
        original_url=str(resource.original_url),
        format=format_,
        role=resource.role.value,
        source_origin="synthetic",
    )
    course = CourseDiscovery(
        course_id="cs50_python",
        original_url="https://cs50.harvard.edu/python/",
        sections=(
            SectionDiscovery(
                course_id="cs50_python",
                key="0",
                original_url="https://cs50.harvard.edu/python/weeks/0/",
            ),
        ),
        resources=(lecture, resource),
    )
    plan = MaterialPlan(courses=(course,), materials=(binding,))
    config = ParserConfig(
        name=kind, version="1" if kind == "code" else "2", max_blocks=max_blocks
    )
    if kind == "html":
        raw = (ROOT / "tests/fixtures/material_quality/notes.html").read_bytes()
        doc, blobs = parse_html(binding, raw, config)
    elif kind == "code":
        raw = '# Ä\r\nprint("hello")\n'.encode()
        doc, blobs = parse_code(binding, raw, config)
    else:
        # Synthetic normalized PDF-v2 contract fixture. Verification never parses PDF.
        raw = (ROOT / "tests/fixtures/material_quality/source.pdf").read_bytes()
        texts = [
            ("code", "1  x = 1\n2  print(x)\n3  # Ä"),
            ("table", "A B"),
            ("math", "x² + y² = z²"),
        ]
        parts = []
        for kind_, text in texts:
            data = {}
            if kind_ != "table":
                data = dict(
                    classification=dict(
                        strategy="python_math_v2",
                        signals=["synthetic"],
                        monospace_ratio=1.0,
                        python_syntax_valid=False,
                    ),
                    line_bboxes=[[0, 0, 30, 10] for _ in text.split("\n")],
                )
            if kind_ == "code":
                data.update(
                    code_view="x = 1\nprint(x)\n# Ä",
                    line_number_strategy="sequential_aligned_two_space_gutter_v1",
                    line_numbers=[
                        dict(line_index=i, number=i + 1, prefix=f"{i + 1}  ")
                        for i in range(3)
                    ],
                )
            parts.append(
                dict(
                    type=kind_,
                    text=text,
                    data=data,
                    location=dict(page=1, bbox=[0, 0, 100, 100]),
                )
            )
        doc, blobs = (
            build_document(
                binding,
                raw,
                config,
                parts,
                metadata=dict(page_count=2),
                title="Synthetic PDF",
            ),
            {},
        )
    root = tmp_path / "bundle"
    directory = root / binding.material_id.split(":")[1]
    normalized = directory / doc.document_id.split(":")[1] / "normalized.v1.json"
    if local_image:
        from src.model_materials.materials import NormalizedDocument

        value = doc.model_dump(mode="json")
        value["images"][0].update(
            artifact_path="images/local.bin", sha256=sha256(b"synthetic image")
        )
        doc = NormalizedDocument.model_validate(value)
        blobs = {"images/local.bin": b"synthetic image"}
    dump(normalized, doc.model_dump(mode="json"))
    raw_path = directory / "raw/source"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(raw)
    for relative, data in blobs.items():
        target = normalized.parent / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    receipt = ArtifactReceipt(
        binding=binding,
        status="completed",
        raw_sha256=sha256(raw),
        origin="local_import",
        parser=doc.parser,
        normalized_path=normalized.relative_to(root).as_posix(),
        normalized_sha256=sha256(normalized.read_bytes()),
        image_hashes={p: sha256(b) for p, b in blobs.items()},
        history=("completed",),
    )
    receipt_path = directory / "receipt.v1.json"
    dump(receipt_path, receipt.model_dump(mode="json"))
    plan_path = tmp_path / "plan.json"
    dump(plan_path, plan.model_dump(mode="json"))
    bundle = MaterialBundle(
        workspace=root,
        raw_path=raw_path,
        normalized_path=normalized,
        receipt_path=receipt_path,
        plan_path=plan_path,
        implementation_path=tmp_path / "implementation.json",
    )
    attest(bundle)
    return bundle, doc


def srt(tmp_path):
    plan_path = tmp_path / "plan.json"
    from src.model_discovery.cs50_selection import SelectionPolicy
    from src.tools_lecture.adapt_cs50 import build_cs50_course_plan
    from src.tools_lecture.select_cs50 import preview_course

    # Complete small discovery graph: one logical lecture, one official SRT
    # reference, synthetic bytes below. No artificial slicing of planned tasks.
    saved = json.loads(
        (ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json").read_bytes()
    )
    graph = next(
        c["preview"]["discovery"]
        for c in saved["courses"]
        if c["lecture_course"]["course_id"] == "cs50_python"
    )
    graph["sections"] = [v for v in graph["sections"] if v["key"] == "0"]
    graph["resources"] = [
        v
        for v in graph["resources"]
        if v["section_keys"] == ["0"]
        and (
            v["role"] == "lecture_video"
            or (
                v["role"] == "subtitles"
                and v["format"] == "srt"
                and v["language"] == "en"
            )
        )
    ]
    graph["warnings"] = []
    discovery = CourseDiscovery.model_validate(graph)
    preview = preview_course(
        discovery, SelectionPolicy(text_strategy="timed_knowledge")
    )
    plan = CS50AdapterPlan(courses=(build_cs50_course_plan(preview),))
    dump(plan_path, plan.model_dump(mode="json"))
    course = next(
        c for c in plan.courses if c.lecture_course.course_id == "cs50_python"
    )
    binding = next(b for b in course.bindings if b.section_key == "0")
    root = tmp_path / "bundle"
    raw = root / binding.raw_srt_path
    raw.parent.mkdir(parents=True)
    raw.write_bytes(
        "1\n00:00:00,100 --> 00:00:03,000\nHallo Ä\nMehrzeilig\n\n2\n00:00:02,000 --> 00:00:04,000\n∑ x²\n".encode()
    )
    doc = import_srt(
        raw,
        language=binding.language,
        original_url=binding.transcript_url,
        preserve_empty_cues=True,
    )
    doc.source = str(binding.raw_srt_path)
    doc.provenance.source_file = str(binding.raw_srt_path)
    doc.provenance.media_id = binding.media_id
    payload = root / binding.transcript_json_path
    dump(payload, doc.model_dump(mode="json"))
    validate_document(payload, binding, raw)
    actions = {}
    for task in course.tasks:
        if task.resource_id == binding.resource_id:
            action = task.task.actions[0].value
            actions[task.task_id] = dict(
                status="done",
                action=action,
                sha256=sha256((raw if action == "download" else payload).read_bytes()),
            )
            if action == "parse_subtitle":
                actions[task.task_id]["input_sha256"] = sha256(raw.read_bytes())
    receipt = raw.parent / "execution.v1.json"
    dump(
        receipt,
        dict(
            schema_version=1, binding=binding.model_dump(mode="json"), actions=actions
        ),
    )
    bundle = SRTBundle(
        workspace=root,
        raw_path=raw,
        transcript_path=payload,
        receipt_path=receipt,
        plan_path=plan_path,
        implementation_path=tmp_path / "implementation.json",
        source_id=binding.source_id,
        source_origin="synthetic",
    )
    attest(bundle)
    return bundle, doc
