"""Explicit snapshot plan and hash-bound material parser/resume orchestration."""

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import model_validator

from src.model_discovery.cs50 import CourseDiscovery, DiscoveryModel, deterministic_id
from src.model_materials.materials import (
    ArtifactReceipt,
    ImageArtifact,
    Location,
    MaterialResource,
    NormalizedDocument,
    ParserConfig,
)
from src.tools_lecture.execute_cs50 import ExecutionConflict, digest, write_state
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.inventory import CODE, capability, format_of
from src.tools_materials.storage import locate, locked, publish_bytes


class MaterialPlan(DiscoveryModel):
    schema_version: Literal[1] = 1
    snapshot_coverage: Literal["local_snapshot_only"] = "local_snapshot_only"
    courses: tuple[CourseDiscovery, ...]
    materials: tuple[MaterialResource, ...]

    @model_validator(mode="after")
    def validate_bindings(self):
        courses = {c.course_id: c for c in self.courses}
        if len(courses) != len(self.courses) or len(
            {b.material_id for b in self.materials}
        ) != len(self.materials):
            raise ValueError("Duplicate course/material identity")
        for b in self.materials:
            course = courses.get(b.resource.course_id)
            if course is None or b.resource not in course.resources:
                raise ValueError(
                    "Material resource contradicts complete discovery graph"
                )
            # Main logical lecture IDs already exist in the graph; never infer from filename.
            expected = sorted(
                {
                    r.resource_id
                    for r in course.resources
                    if r.role == "lecture_video"
                    and set(r.section_keys) & set(b.resource.section_keys)
                }
            )
            if sorted(b.lecture_ids) != expected:
                raise ValueError(
                    "Logical lecture assignment contradicts discovery graph"
                )
        return self

    def select(self, *, course=None, section=None, lecture=None, resource=None):
        rows = tuple(
            b
            for b in self.materials
            if (course is None or b.resource.course_id == course)
            and (section is None or section in b.resource.section_keys)
            and (lecture is None or lecture in b.lecture_ids)
            and (resource is None or resource in {b.source_id, b.material_id})
        )
        if not rows:
            raise ValueError("No resources match explicit scope")
        return rows


def make_plan(manifest):
    courses = discover_fixture_courses(manifest)
    materials = []
    for c in courses:
        for r in c.resources:
            lectures = tuple(
                sorted(
                    {
                        lecture.resource_id
                        for lecture in c.resources
                        if lecture.role == "lecture_video"
                        and set(lecture.section_keys) & set(r.section_keys)
                    }
                )
            )
            materials.append(
                MaterialResource(
                    resource=r,
                    original_url=str(r.original_url),
                    lecture_ids=lectures,
                    format=format_of(str(r.original_url), r.format),
                    role=r.role.value,
                    language=r.language,
                )
            )
    return MaterialPlan(courses=courses, materials=tuple(materials))


def parser_for(binding):
    support, reason = capability(binding.original_url, binding.format)
    if support != "supported":
        return None, support, reason
    if binding.role in {
        "lecture_video",
        "audio",
        "short",
        "section",
        "demo",
        "transcript",
        "subtitles",
    }:
        return (
            None,
            "unsupported",
            "Media/transcripts retain their separate reviewed pipeline",
        )
    if binding.format == "html":
        name = (
            "code"
            if binding.role == "source_code" and not binding.original_url.endswith("/")
            else "html"
        )
    elif binding.format == "pdf":
        name = "pdf"
    elif binding.format in CODE:
        name = "code"
    elif binding.format in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
        name = "image"
    else:
        return None, "unsupported", "No reviewed parser"
    return (
        ParserConfig(name=name, version="2" if name in {"html", "pdf"} else "1"),
        "selected",
        "Supported local parser; remote content not checked",
    )


def plan_steps(binding):
    parser, status, reason = parser_for(binding)
    download = deterministic_id("material_task", binding.material_id, "download")
    parse = deterministic_id(
        "material_task",
        binding.material_id,
        "parse_document",
        parser.config_id if parser else "",
    )
    return dict(
        material_id=binding.material_id,
        source_id=binding.source_id,
        course_id=binding.resource.course_id,
        section_keys=binding.resource.section_keys,
        lecture_ids=binding.lecture_ids,
        status=status,
        reason=reason,
        parser=parser.model_dump() if parser else None,
        tasks=[
            dict(task_id=download, action="download", depends_on=[]),
            dict(task_id=parse, action="parse_document", depends_on=[download]),
        ]
        if parser
        else [],
    )


class MaterialProcessor:
    def __init__(self, workspace):
        self.downloader = MaterialDownloader(workspace)
        self.workspace = self.downloader.workspace

    def inspect(self, binding, config=None):
        binding = MaterialResource.model_validate_json(binding.model_dump_json())
        raw, path = self.downloader.paths(binding)
        if path.exists():
            pending = ArtifactReceipt.model_validate_json(path.read_bytes())
            if pending.binding != binding:
                raise ExecutionConflict("Material receipt binding conflict")
            if (
                pending.status == "failed"
                and "verified" not in pending.history
                and not raw.exists()
            ):
                # Read-only failure observation is not permission to parse/resume an unverified source.
                return pending
        receipt = self.downloader.validate(binding)
        if receipt.status != "completed":
            return receipt
        parser = config or parser_for(binding)[0]
        if receipt.parser != parser or receipt.normalized_path is None:
            raise ExecutionConflict("Parser configuration/output binding conflict")
        target = locate(self.workspace, receipt.normalized_path)
        if not target.is_file() or digest(target) != receipt.normalized_sha256:
            raise ExecutionConflict("Normalized document hash conflict")
        document = NormalizedDocument.model_validate_json(target.read_bytes())
        if (
            document.binding != binding
            or document.parser != parser
            or document.raw_sha256 != receipt.raw_sha256
        ):
            raise ExecutionConflict("Normalized document provenance conflict")
        expected = {
            i.artifact_path: i.sha256 for i in document.images if i.artifact_path
        }
        if expected != receipt.image_hashes:
            raise ExecutionConflict("Image manifest conflict")
        for path, sha in expected.items():
            file = locate(self.workspace, Path(receipt.normalized_path).parent / path)
            if not file.is_file() or digest(file) != sha:
                raise ExecutionConflict("Image artifact hash conflict")
        return receipt

    def parse(self, binding, *, execute=False, config=None):
        selected, status, reason = parser_for(binding)
        if selected is None:
            return {
                "status": status,
                "reason": reason,
                "material_id": binding.material_id,
            }
        config = config or selected
        if config.name != selected.name:
            raise ExecutionConflict("Parser kind contradicts resource binding")
        if not execute:
            return plan_steps(binding)
        with locked(self.workspace):
            receipt = self.downloader.validate(binding)
            if receipt.status == "completed":
                return self.inspect(binding, config)
            if receipt.parser is not None and receipt.parser != config:
                raise ExecutionConflict(
                    "Existing parser receipt configuration conflict; use a new workspace"
                )
            raw, receipt_path = self.downloader.paths(binding)
            content = raw.read_bytes()
            if len(content) > config.max_bytes:
                raise ValueError("Raw source exceeds parser byte limit")
            try:
                if config.name == "html":
                    from src.tools_materials.parse_html import parse_html

                    doc, blobs = parse_html(binding, content, config)
                elif config.name == "pdf":
                    from src.tools_materials.parse_pdf import parse_pdf

                    doc, blobs = parse_pdf(binding, content, config)
                elif config.name == "code":
                    from src.tools_materials.parse_code import parse_code

                    doc, blobs = parse_code(binding, content, config)
                else:
                    from src.tools_materials.parse_html import build_document

                    sha = hashlib.sha256(content).hexdigest()
                    path = f"images/{sha}.bin"
                    image_id = deterministic_id("image_ref", binding.material_id, sha)
                    image = ImageArtifact(
                        image_id=image_id,
                        source_location=Location(),
                        artifact_path=path,
                        sha256=sha,
                        mime_type=receipt.mime_type,
                        original_url=binding.original_url,
                    )
                    doc = build_document(
                        binding,
                        content,
                        config,
                        [
                            dict(
                                type="image_reference",
                                location=Location(),
                                data=dict(image_id=image_id),
                            )
                        ],
                        images=[image],
                        warnings=[
                            "Image bytes archived; no rendering or semantic validation"
                        ],
                    )
                    blobs = {path: content}
                directory = (
                    Path(binding.material_id.split(":")[1])
                    / doc.document_id.split(":")[1]
                )
                relative = str(directory / "normalized.v1.json")
                data = (doc.model_dump_json(indent=2) + "\n").encode()
                hashes = {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()}
                prepared = receipt.model_copy(
                    update=dict(
                        status="parsed",
                        parser=config,
                        normalized_path=relative,
                        normalized_sha256=hashlib.sha256(data).hexdigest(),
                        image_hashes=hashes,
                        error=None,
                        history=receipt.history + ("parsed",),
                    )
                )
                if receipt.normalized_sha256 is not None and (
                    receipt.normalized_sha256 != prepared.normalized_sha256
                    or receipt.image_hashes != hashes
                ):
                    raise ExecutionConflict("Prepared parser output changed")
                write_state(receipt_path, prepared.model_dump(mode="json"))
                for path, bytes_ in {**blobs, "normalized.v1.json": data}.items():
                    output = locate(self.workspace, directory / path)
                    if output.exists():
                        if digest(output) != hashlib.sha256(bytes_).hexdigest():
                            raise ExecutionConflict(
                                "Existing parser artifact hash conflict"
                            )
                    else:
                        publish_bytes(output, bytes_)
                completed = prepared.model_copy(
                    update=dict(
                        status="completed",
                        history=prepared.history + ("normalized", "completed"),
                    )
                )
                write_state(receipt_path, completed.model_dump(mode="json"))
                return self.inspect(binding, config)
            except Exception as exc:
                # Keep write-ahead hashes after a post-publication interruption.
                current = ArtifactReceipt.model_validate_json(receipt_path.read_bytes())
                failed = current.model_copy(
                    update=dict(
                        status="conflict"
                        if isinstance(exc, ExecutionConflict)
                        else "failed",
                        parser=config,
                        error=f"{type(exc).__name__}: {exc}",
                        history=current.history
                        + (
                            "conflict"
                            if isinstance(exc, ExecutionConflict)
                            else "failed",
                        ),
                    )
                )
                write_state(receipt_path, failed.model_dump(mode="json"))
                raise
