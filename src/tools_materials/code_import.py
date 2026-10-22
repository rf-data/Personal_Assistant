"""Thin offline Python/ZIP adapter over code-v1, material quality and handoff.

No HTTP, code execution, queue, ContentStore or Knowledge publication. An archive
member becomes a known Python source only through an explicit mapping AND its
own current approval/hash, never through a guessed filename identity.
"""

import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import Contract, fingerprint
from src.job_control.operations import private
from src.model_materials.materials import ArtifactReceipt, ParserConfig
from src.tools_lecture.execute_cs50 import sync_directory
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials import batch as api
from src.tools_materials import code_structure, code_zip, parse_code
from src.tools_materials.capacity import MIB, check_capacity
from src.tools_materials.inventory import official
from src.tools_materials.processing import make_plan
from src.tools_materials.quality import _json
from src.tools_materials.storage import artifact_root, locked, publish_bytes


class LocalSource(Contract):
    path: Path
    members: dict[str, str] = Field(default_factory=dict, max_length=7)


def load_inputs(path):
    data = _json(read_file(private(safe_path(Path(path))), 16384))
    if not isinstance(data, dict) or not 1 <= len(data) <= 8:
        raise ValueError("Explicit bounded source mapping required")
    return {key: LocalSource.model_validate(value) for key, value in data.items()}


def supported(binding):
    return (
        binding.resource.course_id == "cs50_python"
        and binding.resource.section_keys == ("0",)
        and binding.role == "source_code"
        and binding.format in {"py", "zip"}
        and official(binding.original_url)
        and not urlsplit(binding.original_url).fragment
        and len(binding.lecture_ids) == 1
        and binding.source_id != binding.lecture_ids[0]
    )


def checked(batch, limits):
    limits.batch_size(batch)
    if not 1 <= len(batch.materials) <= 8 or not all(map(supported, batch.materials)):
        raise ValueError("Select at most eight bound Week-0 Python/ZIP materials")
    if limits.reserve_bytes < 5 * 1024**3 or limits.archive_bytes > 64 * MIB:
        raise ValueError("C26 reserve/budget must remain 5 GiB / at most 64 MiB")
    current = api.plan(
        batch.manifest,
        ["cs50_python"],
        [b.material_id for b in batch.materials],
        synthetic=batch.source_origin == "synthetic",
        include_code_indexes=True,
    )
    if current.model_copy(update={"max_bytes": batch.max_bytes}) != batch:
        raise ValueError("Code discovery selection changed")
    plan = make_plan(batch.manifest, include_code_indexes=True)
    return plan.model_copy(
        update={
            "materials": tuple(
                b.model_copy(update={"source_origin": batch.source_origin})
                for b in plan.materials
            )
        }
    )


def revision():
    from src.model_materials import materials
    from src.tools_lecture import material_handoff
    from src.tools_materials import code_discovery, mapping, parse_html, quality

    return fingerprint(
        dict(
            python=sys.version,
            modules={
                module.__name__: api.sha(read_file(Path(module.__file__)))
                for module in (
                    sys.modules[__name__],
                    code_zip,
                    code_structure,
                    parse_code,
                    parse_html,
                    materials,
                    material_handoff,
                    code_discovery,
                    mapping,
                    quality,
                )
            },
        )
    )


def encoded(model):
    return (model.model_dump_json(indent=2) + "\n").encode()


def json_bytes(value):
    from src.content_store.models import canonical

    return canonical(value) + b"\n"


def layout(batch, inputs, root):
    by_id = {b.source_id: b for b in batch.materials}
    children = set()
    for source, item in inputs.items():
        if source not in by_id or not item.path.is_absolute():
            raise ValueError("Unknown source or nonabsolute input")
        if safe_path(item.path).is_relative_to(root):
            raise ValueError("Original must be outside output root")
        parent = by_id[source]
        if parent.format == "py" and item.members:
            raise ValueError("Python source cannot contain members")
        if parent.format == "zip" and not item.members:
            raise ValueError("ZIP needs explicit selected Python members")
        for name, child_id in item.members.items():
            if not name or child_id in children or child_id in inputs:
                raise ValueError("Duplicate/ambiguous member binding")
            child = by_id.get(child_id)
            if (
                child is None
                or child.format != "py"
                or child.lecture_ids != parent.lecture_ids
                or child.resource.section_keys != parent.resource.section_keys
            ):
                raise ValueError("Missing/cross-lecture member binding")
            children.add(child_id)
    if set(inputs) | children != set(by_id):
        raise ValueError("Input selection must exactly match batch")
    return by_id


def build_code(workspace, binding, raw, plan_path, root, limits):
    config = ParserConfig(name="code", max_bytes=MIB)
    document, _ = parse_code.parse_code(binding, raw, config)
    key = binding.material_id.split(":")[-1]
    normalized = f"{key}/{document.document_id.split(':')[-1]}/normalized.v1.json"
    payload = encoded(document)
    receipt = ArtifactReceipt(
        binding=binding,
        status="completed",
        origin="local_import",
        raw_sha256=api.sha(raw),
        parser=config,
        normalized_path=normalized,
        normalized_sha256=api.sha(payload),
        history=("selected", "verified", "parsed", "normalized", "completed"),
    )
    files = {
        f"{key}/raw/source": raw,
        f"{key}/receipt.v1.json": encoded(receipt),
        normalized: payload,
        f"{key}/structure.v1.json": json_bytes(code_structure.inspect_structure(raw)),
    }
    if sum(map(len, files.values())) > 8 * MIB:
        raise ValueError("Code projection size bound")
    check_capacity(
        root, limits.archive_bytes, limits.reserve_bytes, sum(map(len, files.values()))
    )
    for name, content in files.items():
        publish_bytes(workspace / name, content)
    review = prepare_material_handoff(
        workspace=workspace,
        normalized_path=workspace / normalized,
        raw_path=workspace / key / "raw/source",
        receipt_path=workspace / key / "receipt.v1.json",
        plan_path=plan_path,
    )
    if review.handoff is None:
        raise ValueError("Existing material quality gate rejected source")
    # Existing quality DTO, archive-relative path aliases; never private hostpaths.
    quality = review.report.model_dump(mode="json")
    quality["inputs"] = dict(
        workspace="materials",
        plan="plan.v1.json",
        normalized=normalized,
        raw=f"{key}/raw/source",
        receipt=f"{key}/receipt.v1.json",
    )
    files[f"{key}/quality.v1.json"] = json_bytes(quality)
    files[f"{key}/handoff.v1.json"] = encoded(review.handoff)
    summary = dict(
        source_id=binding.source_id,
        material_id=binding.material_id,
        document_id=document.document_id,
        raw_sha256=api.sha(raw),
        code_blocks=len(document.blocks),
        aggregation_units=len(review.handoff.aggregation_units),
        excluded_blocks=review.handoff.excluded_blocks,
        quality=review.report.status,
    )
    if len(review.handoff.aggregation_units) != len(document.blocks):
        raise ValueError("Code blocks lost at handoff")
    return files, summary


def prepare_unit(
    root, raw, parent, item, by_id, grants, plan, batch_digest, implementation, limits
):
    files = {"raw/source": raw, "plan.v1.json": encoded(plan)}
    summaries, members = [], []
    if parent.format == "zip":
        inspected = code_zip.inspect_zip(raw)  # Validate the WHOLE archive first.
        available = {meta["name"]: (meta, data) for meta, data in inspected}
        if set(item.members) - available.keys():
            raise ValueError("Selected member absent")
        payloads = []
        for name, child_id in item.members.items():
            meta, data = available[name]
            if (
                meta["status"] != "candidate_python"
                or api.sha(data) != grants[child_id].expected_sha256
            ):
                raise ValueError("Member type/hash not approved")
            payloads.append((by_id[child_id], data))
        for meta, _data in inspected:
            meta = dict(meta)
            if meta["name"] in item.members:
                child = by_id[item.members[meta["name"]]]
                meta.update(
                    status="selected",
                    source_id=child.source_id,
                    material_id=child.material_id,
                    archive_source_id=parent.source_id,
                    archive_sha256=api.sha(raw),
                )
            elif meta["status"] == "candidate_python":
                meta["status"] = "excluded_not_selected"
            members.append(meta)
    else:
        payloads = [(parent, raw)]
    with tempfile.TemporaryDirectory(prefix=".code-check-", dir=root) as directory:
        staging = Path(directory)
        publish_bytes(staging / "plan.v1.json", files["plan.v1.json"])
        for binding, content in payloads:
            code_files, summary = build_code(
                staging / "materials",
                binding,
                content,
                staging / "plan.v1.json",
                root,
                limits,
            )
            files.update(
                {"materials/" + name: data for name, data in code_files.items()}
            )
            summaries.append(summary)
    body = dict(
        schema_version=1,
        kind="c26-offline-code",
        binding=parent.model_dump(mode="json"),
        batch_sha256=batch_digest,
        importer_sha256=implementation,
        approvals={
            key: fingerprint(grant.model_dump(mode="json"))
            for key, grant in sorted(grants.items())
        },
        raw_sha256=api.sha(raw),
        raw_bytes=len(raw),
        members=members,
        code=summaries,
        files={name: api.sha(data) for name, data in sorted(files.items())},
        execution_supported=False,
        knowledge_fact_verified=False,
    )
    files["import.v1.json"] = json_bytes(dict(receipt=body, sha256=fingerprint(body)))
    if sum(map(len, files.values())) > 16 * MIB:
        raise ValueError("Code unit output bound")
    return files, body


def verify(folder, expected):
    """Exact immutable bytes and inventory; incomplete/foreign files block reuse."""
    actual = set()
    for path in folder.rglob("*"):
        safe_path(path)
        if path.is_dir():
            private(path, directory=True)
            if not any(
                path.relative_to(folder) in Path(name).parents for name in expected
            ):
                raise ValueError("Unexpected code archive directory")
            continue
        private(path)
        name = path.relative_to(folder).as_posix()
        if name not in expected or read_file(path, 16 * MIB) != expected[name]:
            raise ValueError("Code archive changed")
        actual.add(name)
    if actual != set(expected):
        raise ValueError("Incomplete code archive; no adoption or repair")


def run(batch, root, approvals, inputs, *, action, limits):
    if action not in {"preview", "import", "report"}:
        raise ValueError("Unknown code import action")
    plan = checked(batch, limits)
    root = artifact_root(Path(root))
    private(root.parent, directory=True)
    by_id = layout(batch, inputs, root)
    batch_digest = fingerprint(batch.model_dump(mode="json"))
    selection = dict(
        batch_sha256=batch_digest,
        members={key: value.members for key, value in sorted(inputs.items())},
    )
    marker = json_bytes(selection)
    implementation, rows = revision(), []

    def process():
        for source, item in inputs.items():
            parent = by_id[source]
            selected = [source, *item.members.values()]
            row = dict(
                source_id=source,
                material_id=parent.material_id,
                format=parent.format,
                lecture_ids=list(parent.lecture_ids),
                source_origin=batch.source_origin,
                selected_sources=selected,
                status="blocked",
            )
            stage = "approval"
            try:
                grants = {
                    key: api.approval(by_id[key], approvals, "process")
                    for key in selected
                }
                if any(g.expected_sha256 is None for g in grants.values()):
                    raise PermissionError("Each source needs its expected hash")
                row["download_approved"] = {
                    key: g.download for key, g in grants.items()
                }
                if action == "preview":
                    row["status"] = "selected" if item.path.is_file() else "missing"
                else:
                    stage = "capacity"
                    check_capacity(
                        root, limits.archive_bytes, limits.reserve_bytes, 16 * MIB
                    )
                    folder = root / parent.material_id.split(":")[-1]
                    stage = (
                        "original_input"
                        if action == "import"
                        else "archive_verification"
                    )
                    path = (
                        item.path
                        if action == "import"
                        else private(safe_path(folder / "raw/source"))
                    )
                    raw = read_file(safe_path(path), batch.max_bytes)
                    if api.sha(raw) != grants[source].expected_sha256:
                        raise ValueError("Original hash changed")
                    stage = "parse_and_gate"
                    expected, receipt = prepare_unit(
                        root,
                        raw,
                        parent,
                        item,
                        by_id,
                        grants,
                        plan,
                        batch_digest,
                        implementation,
                        limits,
                    )
                    reused = folder.exists()
                    if action == "import" and not reused:
                        stage = "publication"
                        check_capacity(
                            root,
                            limits.archive_bytes,
                            limits.reserve_bytes,
                            sum(map(len, expected.values())),
                        )
                        folder.mkdir(mode=0o700)
                        sync_directory(root)
                        for name, content in expected.items():
                            publish_bytes(folder / name, content)
                    stage = "archive_verification"
                    private(folder, directory=True)
                    verify(folder, expected)
                    row.update(
                        status="processed",
                        reused=reused,
                        raw_sha256=receipt["raw_sha256"],
                        members=receipt["members"],
                        code=receipt["code"],
                    )
            except (
                ValueError,
                OSError,
                RuntimeError,
                zipfile.BadZipFile,
                NotImplementedError,
            ) as error:
                row.update(error_class=type(error).__name__, error_stage=stage)
                if isinstance(error, FileNotFoundError):
                    row["status"] = "missing"
            rows.append(row)

    if action == "preview":
        process()
    else:
        new = action == "import" and not root.exists()
        if new:
            root.mkdir(mode=0o700)
        private(root, directory=True)
        with locked(root):
            path = root / "selection.v1.json"
            if new:
                publish_bytes(path, marker)
            if read_file(private(path), 16384) != marker:
                raise ValueError("Different code selection in existing root")
            process()
    return dict(
        schema_version=1,
        action=action,
        batch_sha256=batch_digest,
        importer_sha256=implementation,
        materials=rows,
        status_counts=dict(sorted(Counter(r["status"] for r in rows).items())),
        selected_materials=len(batch.materials),
        processed_materials=sum(
            len(r["selected_sources"]) for r in rows if r["status"] == "processed"
        ),
        full_week_coverage=False,
        network_requests=0,
        c18_publication=False,
        execution_supported=False,
        knowledge_fact_verified=False,
        human_quality="not_evaluated",
    )
