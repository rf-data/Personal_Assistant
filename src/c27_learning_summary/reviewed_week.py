"""Explicit local review batches → existing parsers/handoff → summary catalog.

This adapter has no transport or provider. Input directories are read only.
Acquisition plans remain unapproved; processing results do not grant publication.
ZIPs are inspected in memory; member source identities require a later mapping.
"""

import hashlib
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from src.c27_learning_summary.adapter import (
    artifact,
    material_handoff_blocks,
    transcript_blocks,
)
from src.c27_learning_summary.models import Catalog, Course, Material, Unit, Week
from src.content_store.models import canonical, fingerprint
from src.job_control.catalog import read_file, safe_path
from src.job_control.operations import private
from src.model_discovery.cs50 import (
    CourseDiscovery,
    Provenance,
    ResourceCandidate,
    SectionDiscovery,
)
from src.model_lecture.data_resources import LectureDocument
from src.model_materials.acquisition import WeekInventory, WeekMaterial
from src.model_materials.materials import (
    ArtifactReceipt,
    MaterialPlan,
    MaterialResource,
    ParserConfig,
)
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials import (
    code_zip,
    parse_code,
    parse_html,
    quality,
    source_acquisition,
    text_validation,
)
from src.tools_materials.capacity import check_capacity
from src.tools_materials.storage import artifact_root, locked, publish_bytes
from src.tools_transcribe import import_transcript as transcript_import

VERSION = "c27-local-review-v1"
MAX_REPORT = 16 * 1024**2


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(root, relative, limit=8 * 1024**2):
    return read_file(safe_path(root, relative), limit)


def _source_owner(row: WeekMaterial, by_id: Mapping[str, WeekMaterial]) -> WeekMaterial:
    """Inventory roots are valid; downloaded summary sources need a direct unit."""
    if row.parent_material_id is None:
        raise ValueError(
            "Summary source is a root entry; lecture/short parent required"
        )
    owner = by_id.get(row.parent_material_id)
    if owner is None:
        raise ValueError("Summary source references an unknown parent")
    if owner.material_type not in {"lecture", "short"}:
        raise ValueError("Summary source requires a direct lecture/short parent")
    return owner


def verify_review(root):
    """Recheck paired plans, snapshot ledger and exact report bytes on every run."""
    root = safe_path(Path(root).absolute())
    evidence = {}

    def checked(name, limit=8 * 1024**2):
        raw = read(root, name, limit)
        evidence[name] = sha(raw)
        return raw

    inv1, inv2 = (checked(f"inventory-0{i}.json") for i in (1, 2))
    plan1, plan2 = (checked(f"plan-0{i}.json") for i in (1, 2))
    if inv1 != inv2 or plan1 != plan2:
        raise ValueError("Review inventory/plan versions differ; reconcile explicitly")
    inventory = WeekInventory.model_validate(quality._json(inv2))
    proposal = quality._json(plan2)
    if proposal["inventory_sha256"] != fingerprint(inventory.model_dump(mode="json")):
        raise ValueError("Plan canonical inventory hash mismatch")
    snapshots = quality._json(checked("snapshots.json"))
    if (snapshots["course_id"], snapshots["week_id"], snapshots["source_origin"]) != (
        inventory.course_id,
        inventory.week_id,
        inventory.source_origin,
    ):
        raise ValueError("Snapshot scope mismatch")
    if not 1 <= len(snapshots["pages"]) <= 32:
        raise ValueError("Snapshot count limit")
    inventory_snapshots = {(s["url"], s["sha256"]) for s in inventory.snapshots}
    for page in snapshots["pages"]:
        if not source_acquisition.official(page["url"]):
            raise ValueError("Nonofficial snapshot")
        if sha(checked(page["path"], inventory.limits.html_bytes)) != page["sha256"]:
            raise ValueError("Snapshot hash mismatch")
        if (page["url"], page["sha256"]) not in inventory_snapshots:
            raise ValueError("Snapshot absent from inventory ledger")
    if inventory_snapshots != {(s["url"], s["sha256"]) for s in snapshots["pages"]}:
        raise ValueError("Inventory snapshot ledger is not fully covered")
    report = quality._json(checked("download-batch-01/download-report.json", 65536))
    if report["status"] != "COMPLETE" or not 1 <= len(report["files"]) <= 32:
        raise ValueError("Incomplete or oversized download report")
    rows, seen_names, seen_urls, total = [], set(), set(), 0
    by_id = {r.material_id: r for r in inventory.materials}
    for entry in report["files"]:
        name, url = entry["filename"], entry["source_url"]
        if Path(name).name != name or name in seen_names or url in seen_urls:
            raise ValueError("Duplicate or nonflat report filename/URL")
        seen_names.add(name)
        seen_urls.add(url)
        if not source_acquisition.official(url):
            raise ValueError("Nonofficial report source")
        matches = [
            r
            for r in inventory.materials
            if r.source_url == url
            and r.material_type in {"page", "transcript", "subtitles", "source_code"}
        ]
        candidates = []
        for match in matches:
            parent = (
                by_id.get(match.parent_material_id)
                if match.parent_material_id is not None
                else None
            )
            if (
                match.material_type == "page"
                and parent is not None
                and parent.material_type in {"course", "week", "shorts"}
            ):
                # Scope pages stay in the inventory. The same URL may also be
                # explicitly bound to a lecture/short page (real CS50P Week 0).
                continue
            _source_owner(match, by_id)
            candidates.append(match)
        if len(candidates) != 1:
            raise ValueError("Ambiguous/absent lecture or short source binding")
        row = candidates[0]
        raw = checked("download-batch-01/" + name, inventory.limits.ceiling(row))
        if (
            entry["status"] != "DOWNLOADED"
            or type(entry["bytes"]) is not int
            or len(raw) != entry["bytes"]
            or sha(raw) != entry["sha256"]
        ):
            raise ValueError("Download size/hash/status mismatch")
        total += len(raw)
        if total > inventory.limits.transfer_bytes:
            raise ValueError("Batch byte limit")
        rows.append((row, entry, raw))
    if type(report["total_bytes"]) is not int or total != report["total_bytes"]:
        raise ValueError("Download report total mismatch")
    return root, inventory, rows, evidence


def revision():
    """Resume keys bind implementation and installed parser dependencies."""
    from importlib.metadata import version

    from src.c27_learning_summary import adapter, models
    from src.model_materials import materials
    from src.tools_lecture import material_handoff
    from src.tools_materials import html_projection, mapping, quality_projection

    modules = [
        sys.modules[__name__],
        adapter,
        models,
        materials,
        material_handoff,
        parse_html,
        parse_code,
        code_zip,
        source_acquisition,
        text_validation,
        quality,
        html_projection,
        mapping,
        quality_projection,
        transcript_import,
    ]
    return fingerprint(
        {
            "python": sys.version,
            "modules": {m.__name__: sha(read_file(Path(m.__file__))) for m in modules},
            "packages": {n: version(n) for n in ("pydantic", "beautifulsoup4")},
        }
    )


def binding_for(row, inventory, videos):
    role = {"page": "reference"}.get(row.material_type, row.material_type)
    resource = ResourceCandidate(
        course_id=row.course_id,
        role=role,
        original_url=row.source_url,
        title=row.title,
        provenance=(
            Provenance(
                original_url=row.source_url,
                fixture_file="inventory-02.json",
                locator=row.material_id,
                context_path=row.discovered_from,
            ),
        ),
        section_keys=(row.week_id,),
        language="en" if row.material_type in {"transcript", "subtitles"} else None,
    )
    return MaterialResource(
        resource=resource,
        original_url=row.source_url,
        role=role,
        format=row.source_format,
        language=resource.language,
        lecture_ids=tuple(v.resource_id for v in videos),
        source_origin=inventory.source_origin,
    )


def publish_same(root, name, data):
    """Resume interrupted publication; conflicts never overwrite previous bytes."""
    path = safe_path(root, name)
    if path.exists():
        if read_file(path, MAX_REPORT) != data:
            raise ValueError("Existing processing output conflicts")
    else:
        check_capacity(root.parent, MAX_REPORT, 5 * 1024**3, len(data))
        publish_bytes(path, data)


def material_blocks(row, entry, raw, inventory, root, output):
    original = safe_path(root, "download-batch-01/" + entry["filename"])
    if row.material_type in {"transcript", "subtitles"}:
        binding = binding_for(row, inventory, ())
        text_validation.validate_text_source(original, binding)
        document = transcript_import.import_transcript(
            original,
            language="en",
            original_url=row.source_url,
            format=row.source_format,
        )
        transcript_path = safe_path(output, row.material_id + ".transcript.json")
        if transcript_path.exists():
            previous = TranscriptDocument.model_validate_json(
                read_file(transcript_path)
            )
            # The importer records its local import time. Keep the first observation
            # when recovering publication, while comparing every content field below.
            if previous.provenance is None:
                raise ValueError("Existing transcript provenance missing")
            document.provenance.acquired_at = previous.provenance.acquired_at
        publish_same(
            output,
            row.material_id + ".transcript.json",
            canonical(document.model_dump(mode="json")),
        )
        return binding, transcript_blocks(document, raw_sha256=entry["sha256"])
    if row.source_format != "html":
        raise ValueError("Local review route requires HTML or transcript")
    text_validation.validate_html_page(original)
    # The existing MaterialPlan requires all explicit logical lecture video IDs.
    # Select the inventory's player reference within this exact unit, no URL guesses.
    candidates = [
        r
        for r in inventory.materials
        if r.parent_material_id == row.parent_material_id
        and r.material_type == "video"
        and r.source_url
    ]
    if not candidates:
        raise ValueError(
            "Material quality handoff needs an explicit unit video reference"
        )
    player = next(
        (r for r in candidates if r.source_url.startswith("https://video.cs50.io/")),
        candidates[0],
    )
    video = ResourceCandidate(
        course_id=row.course_id,
        role="lecture_video",
        original_url=player.source_url,
        section_keys=(row.week_id,),
        title=player.title,
    )
    binding = binding_for(row, inventory, (video,))
    course = CourseDiscovery(
        course_id=row.course_id,
        original_url=row.source_url,
        sections=(
            SectionDiscovery(
                course_id=row.course_id, key=row.week_id, original_url=row.source_url
            ),
        ),
        resources=(video, binding.resource),
    )
    plan = MaterialPlan(courses=(course,), materials=(binding,))
    cfg = ParserConfig(
        name="html",
        version="2",
        max_bytes=inventory.limits.html_bytes,
        max_blocks=1000,
        max_images=100,
        memory_mb=512,
    )
    document, blobs = parse_html.parse_html(binding, raw, cfg)
    key = binding.material_id.split(":")[1]
    normalized = key + "/" + document.document_id.split(":")[1] + "/normalized.v1.json"
    payload = (document.model_dump_json(indent=2) + "\n").encode()
    receipt = ArtifactReceipt(
        binding=binding,
        status="completed",
        origin="local_import",
        raw_sha256=entry["sha256"],
        parser=cfg,
        normalized_path=normalized,
        normalized_sha256=sha(payload),
        image_hashes={p: sha(b) for p, b in blobs.items()},
        history=("selected", "verified", "parsed", "normalized", "completed"),
    )
    for name, data in {
        key + "/raw/source": raw,
        normalized: payload,
        key + "/receipt.v1.json": (receipt.model_dump_json(indent=2) + "\n").encode(),
        key + "/plan.v1.json": (plan.model_dump_json(indent=2) + "\n").encode(),
        **{str(Path(normalized).parent / n): b for n, b in blobs.items()},
    }.items():
        publish_same(output, name, data)
    review = prepare_material_handoff(
        workspace=output,
        normalized_path=output / normalized,
        receipt_path=output / key / "receipt.v1.json",
        raw_path=output / key / "raw/source",
        plan_path=output / key / "plan.v1.json",
    )
    publish_same(
        output, key + "/quality.json", canonical(review.report.model_dump(mode="json"))
    )
    if review.handoff is None:
        errors = [f.code for f in review.report.findings if f.severity == "error"]
        raise ValueError("Existing material quality gate failed: " + ",".join(errors))
    publish_same(
        output, key + "/handoff.json", canonical(review.handoff.model_dump(mode="json"))
    )
    return binding, material_handoff_blocks(review)


def process_review(root, output):
    """Explicit offline processing only; return a bounded, provenance-bound catalog.

    The receipt is written last. Reuse rechecks every input and output hash;
    interrupted runs can publish identical missing files, never replace conflicts.
    """
    root, inventory, rows, evidence = verify_review(root)
    output = artifact_root(output)
    if output == root or output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("Input and output directories must be disjoint")
    implementation = revision()
    key = fingerprint(dict(version=VERSION, inputs=evidence, revision=implementation))
    target = output / key
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    private(output, directory=True)
    with locked(output):
        receipt_path = target / "receipt.json"
        if receipt_path.exists():
            receipt = quality._json(read_file(receipt_path, 65536))
            if receipt["key"] != key or receipt["inputs"] != evidence:
                raise ValueError("Processing receipt binding mismatch")
            for name, digest in receipt["outputs"].items():
                if sha(read(target, name, MAX_REPORT)) != digest:
                    raise ValueError("Processing output hash mismatch")
            if (
                "catalog.json" not in receipt["outputs"]
                or "report.json" not in receipt["outputs"]
            ):
                raise ValueError("Processing receipt output ledger incomplete")
            catalog = Catalog.model_validate_json(
                read(target, "catalog.json", MAX_REPORT)
            )
            return catalog, quality._json(read(target, "report.json", MAX_REPORT)), True
        check_capacity(
            output, inventory.limits.report_bytes, inventory.limits.reserve_bytes
        )
        target.mkdir(mode=0o700, parents=True, exist_ok=True)
        units, records = {}, []
        by_id = {r.material_id: r for r in inventory.materials}
        for row, entry, raw in rows:
            owner = _source_owner(row, by_id)
            unit = units.setdefault(
                owner.material_id,
                Unit(
                    section_id=owner.material_id,
                    title=owner.title,
                    kind=cast(Literal["lecture", "short"], owner.material_type),
                    materials=(),
                ),
            )
            record = dict(
                filename=entry["filename"],
                material_id=row.material_id,
                unit_id=owner.material_id,
                source_url=row.source_url,
                raw_sha256=entry["sha256"],
            )
            if row.source_format == "zip":
                members = source_acquisition.validate_source(raw, "zip")
                record.update(
                    status="verified_archive_only",
                    members=[m for m, _ in members],
                    summary_status="BLOCKED: explicit member-to-source mapping required",
                )
                publish_same(
                    target, row.material_id + ".archive-members.json", canonical(record)
                )
            else:
                binding, blocks = material_blocks(
                    row, entry, raw, inventory, root, target
                )
                summary_material = Material(
                    material_id=row.material_id,
                    source_id=binding.source_id,
                    source_path="download-batch-01/" + entry["filename"],
                    attribution=entry.get("attribution"),
                    resource=LectureDocument(
                        title=row.title,
                        source_url=row.source_url,
                        content_hash=entry["sha256"],
                        file_type=row.source_format,
                        downloaded=True,
                        license=entry.get("license"),
                    ),
                    available=True,
                    verification="operator_verified"
                    if inventory.source_origin == "official"
                    else "synthetic_test_only",
                    processing_status="completed",
                    blocks=blocks,
                    artifact=artifact(
                        blocks,
                        artifact_id=key + ":" + entry["filename"],
                        parser_version=VERSION + ":" + implementation[:12],
                        last_run=key,
                    ),
                )
                unit.materials += (summary_material,)
                record.update(status="handoff_ready", blocks=len(blocks))
            records.append(record)
        catalog = Catalog(
            origin="operator_reviewed_local"
            if inventory.source_origin == "official"
            else "synthetic",
            courses=(
                Course(
                    course_id=inventory.course_id,
                    course_title=inventory.course_id,
                    provider="Harvard",
                    source_url=None,
                    weeks=(
                        Week(
                            section_id=inventory.week_id,
                            title="Week " + inventory.week_id,
                            units=tuple(units.values()),
                        ),
                    ),
                ),
            ),
        )
        report = dict(
            version=VERSION,
            course_id=inventory.course_id,
            week_id=inventory.week_id,
            evidence_kind="real_local_raw"
            if inventory.source_origin == "official"
            else "fixture",
            inputs=evidence,
            materials=records,
            full_week_acceptance=False,
            license_approval="not_granted_by_this_adapter",
            llm_calls=0,
            downloads=0,
        )
        publish_same(target, "catalog.json", canonical(catalog.model_dump(mode="json")))
        publish_same(target, "report.json", canonical(report))
        # Fail if processing raced a change in the read-only source directory.
        if verify_review(root)[3] != evidence:
            raise ValueError("Review inputs changed during processing")
        outputs = {
            p.relative_to(target).as_posix(): sha(read_file(p, MAX_REPORT))
            for p in target.rglob("*")
            if p.is_file()
        }
        if sum(p.stat().st_size for p in target.rglob("*") if p.is_file()) > MAX_REPORT:
            raise ValueError("Processing output budget exceeded")
        publish_same(
            target,
            "receipt.json",
            canonical(dict(key=key, inputs=evidence, outputs=outputs)),
        )
        return catalog, report, False
