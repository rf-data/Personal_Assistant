"""Read-only bridge from immutable B6 imports to B7; no reparse or staging."""

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.job_control.operations import private
from src.model_materials.materials import ArtifactReceipt, MaterialResource
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials import batch as api
from src.tools_materials import code_import
from src.tools_materials.capacity import MIB, CapacityLimits
from src.tools_materials.quality import _json
from src.tools_materials.storage import locate


def verify_code(binding, ref, approvals):
    try:
        return _verify_code(binding, ref, approvals)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed pinned B6 evidence") from error


def _verify_code(binding, ref, approvals):
    if ref.batch is None or ref.receipt_sha256 is None or approvals is None:
        raise ValueError("Pinned B6 import/batch and current source grants required")
    batch = api.load_batch(safe_path(ref.batch))
    code_import.checked(
        batch,
        CapacityLimits(
            reserve_bytes=5 * 1024**3, archive_bytes=64 * MIB, max_materials=8
        ),
    )
    by_mid = {b.material_id: b for b in batch.materials}
    by_source = {b.source_id: b for b in batch.materials}
    if by_mid.get(binding.material_id) != binding:
        raise ValueError("B6 batch/source binding changed")
    parent = by_mid.get(ref.container_material_id or binding.material_id)
    if parent is None or (parent != binding and parent.format != "zip"):
        raise ValueError("Explicit selected ZIP container required")
    root = private(safe_path(ref.workspace), directory=True)
    folder = private(locate(root, parent.material_id.split(":")[-1]), directory=True)
    receipt_bytes = read_file(private(locate(folder, "import.v1.json")), MIB)
    envelope = _json(receipt_bytes)
    if set(envelope) != {"receipt", "sha256"}:
        raise ValueError("Unknown B6 receipt envelope")
    body = envelope["receipt"]
    if (
        api.sha(receipt_bytes) != ref.receipt_sha256
        or envelope["sha256"] != fingerprint(body)
        or body["schema_version"] != 1
        or body["kind"] != "c26-offline-code"
        or MaterialResource.model_validate(body["binding"]) != parent
        or body["batch_sha256"] != fingerprint(batch.model_dump(mode="json"))
        or body["importer_sha256"] != code_import.revision()
        or body["execution_supported"] is not False
        or body["knowledge_fact_verified"] is not False
    ):
        raise ValueError("Pinned B6 receipt identity/revision changed")
    members = body["members"]
    if not isinstance(members, list) or len(members) > 64:
        raise ValueError("B6 member bound")
    selected = {m["name"]: m["source_id"] for m in members if m["status"] == "selected"}
    if len(selected) != sum(m["status"] == "selected" for m in members):
        raise ValueError("Duplicate B6 selected member")
    if parent.format == "zip":
        if not 1 <= len(selected) <= 7 or len(set(selected.values())) != len(selected):
            raise ValueError("B6 member selection conflict")
    elif members:
        raise ValueError("Standalone Python cannot have archive members")
    source_ids = {parent.source_id, *selected.values()}
    if not source_ids <= by_source.keys():
        raise ValueError("Unknown B6 member/source")
    expected_approvals = {}
    for source in source_ids:
        grant = api.approval(by_source[source], approvals, "process")
        if grant.expected_sha256 is None:
            raise PermissionError("Pinned B6 parent/member hashes required")
        expected_approvals[source] = fingerprint(grant.model_dump(mode="json"))
        if source == parent.source_id and grant.expected_sha256 != body["raw_sha256"]:
            raise ValueError("B6 container hash changed")
        for member in members:
            if member.get("source_id") == source and (
                member["sha256"] != grant.expected_sha256
                or member["material_id"] != by_source[source].material_id
                or member["archive_source_id"] != parent.source_id
                or member["archive_sha256"] != body["raw_sha256"]
            ):
                raise ValueError("B6 member/archive relationship changed")
    if expected_approvals != body["approvals"]:
        raise ValueError("Current B6 import-group grants changed")
    marker = _json(read_file(private(locate(root, "selection.v1.json")), 16384))
    if (
        marker["batch_sha256"] != body["batch_sha256"]
        or marker["members"].get(parent.source_id) != selected
    ):
        raise ValueError("B6 root selection changed")
    hashes = body["files"]
    if not isinstance(hashes, dict) or not 1 <= len(hashes) <= 128:
        raise ValueError("B6 output manifest bound")
    expected = {}
    total = len(receipt_bytes)
    for name, digest in hashes.items():
        if name == "import.v1.json":
            raise ValueError("Self-referential B6 manifest")
        content = read_file(private(locate(folder, name)), 16 * MIB)
        total += len(content)
        if total > 16 * MIB or api.sha(content) != digest:
            raise ValueError("B6 output hash/budget changed")
        expected[name] = content
    expected["import.v1.json"] = receipt_bytes
    code_import.verify(folder, expected)  # Existing exact inventory/permission check.
    raw = read_file(private(locate(folder, "raw/source")), MIB)
    if len(raw) != body["raw_bytes"] or api.sha(raw) != body["raw_sha256"]:
        raise ValueError("B6 immutable input changed")
    if binding.format == "zip":
        return dict(
            adapter="b6_code_archive",
            processed=False,
            provenance="pinned_b6_import_group",
            code_members=list(selected.values()),
        )
    if binding.source_id not in source_ids:
        raise ValueError("Python is not a selected member of this import")
    workspace = locate(folder, "materials")
    key = binding.material_id.split(":")[-1]
    path = private(locate(workspace, f"{key}/receipt.v1.json"))
    receipt = ArtifactReceipt.model_validate(_json(read_file(path, MIB)))
    grant = api.approval(binding, approvals, "process")
    if (
        receipt.binding != binding
        or receipt.raw_sha256 != grant.expected_sha256
        or not receipt.normalized_path
    ):
        raise ValueError("B6 Python receipt changed")
    review = prepare_material_handoff(
        workspace=workspace,
        receipt_path=path,
        raw_path=locate(workspace, f"{key}/raw/source"),
        normalized_path=locate(workspace, receipt.normalized_path),
        plan_path=locate(folder, "plan.v1.json"),
    )
    if review.handoff is None:
        raise ValueError("B6 Python quality/handoff failed")
    return dict(
        adapter="b6_code_handoff",
        processed=True,
        provenance="pinned_b6_import_group",
        technical_quality=review.report.status,
        parser_revision=receipt.parser.config_id,
        container_material_id=parent.material_id,
        container_sha256=body["raw_sha256"],
    )
