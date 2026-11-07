"""Explicit one-source offline HTML retrieval; no downloads or automatic recovery."""

import argparse
import fcntl
import json
import os
import stat
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from src.content_store.adapters import (
    ImplementationEvidence,
    MaterialBundle,
    _read,
    import_verified_bundle,
    verify_material_bundle,
)
from src.content_store.artifacts import explicit_root
from src.content_store.errors import ContentStoreError
from src.content_store.models import canonical, fingerprint, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.reader import ContentReader, ReadFault, private_bytes
from src.content_store.store import ContentStore
from src.job_control.models import Contract, Identifier, Principal, Sha
from src.model_materials.materials import (
    MaterialPlan,
    NormalizedDocument,
    ParserConfig,
)
from src.runtime_paths import checked_path
from src.tools_lecture.execute_cs50 import write_state
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials.processing import MaterialProcessor, parser_for
from src.tools_materials.quality import _json
from src.tools_materials.storage import publish_bytes
from src.tools_rag.content_index import ContentIndex, RetrievalFault
from src.tools_rag.content_index_models import IndexSelection

REPO = Path(__file__).resolve().parents[1]
ACTIONS = ("local_import", "parse", "publish", "index", "retrieve")
OWNED = {
    ".mvp.lock",
    "intent.json",
    "state.json",
    "input.html",
    "plan.json",
    "approval.json",
    "material",
    "implementation.json",
    "store",
    "index",
    "cursor.key",
}


class Hold(ValueError):
    """The isolated root must be retained for explicit operator inspection."""


def checked_query(value):
    terms = value.split()
    if (
        not terms
        or len(value) > 512
        or len(value.encode("utf-8")) > 2048
        or len(terms) > 8
        or any(len(t) > 64 for t in terms)
    ):
        raise Hold("query exceeds the existing lexical search contract")
    return value


class RetrievalTask(Contract):
    query: str = Field(min_length=1, max_length=256)
    expected_passage: str = Field(min_length=1, max_length=2000, pattern=r"\S")

    @field_validator("query")
    @classmethod
    def bounded_query(cls, value):
        return checked_query(value)


class ProcessingApproval(Contract):
    """Private operator attestation, not a license inferred from a URL/domain."""

    schema_version: Literal[1]
    status: Literal["approved"]
    approved_by: Identifier
    evidence_reference: str = Field(min_length=1, max_length=2000, pattern=r"\S")
    valid_until: AwareDatetime
    resource_id: str
    material_id: str
    original_url: str
    source_origin: Literal["synthetic", "official"]
    raw_sha256: Sha
    plan_sha256: Sha
    parser: ParserConfig
    implementation_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    implementation_sha256: Sha
    actions: tuple[str, ...]
    retrieval_tasks: tuple[RetrievalTask, ...] = Field(min_length=3, max_length=3)

    @field_validator("schema_version", mode="before")
    @classmethod
    def explicit_schema(cls, value):
        if type(value) is not int:
            raise ValueError("explicit integer schema_version required")
        return value

    @model_validator(mode="after")
    def distinct_tasks(self):
        if (
            len({" ".join(t.query.split()).casefold() for t in self.retrieval_tasks})
            != 3
        ):
            raise ValueError("three distinct retrieval queries required")
        return self


def implementation_identity():
    """Record a real HEAD and actual Python bytes, including an uncommitted operator."""
    revision = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--verify", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    files = sorted((REPO / "src").rglob("*.py")) + [Path(__file__).resolve()]
    return revision, fingerprint(
        {p.relative_to(REPO).as_posix(): sha256(_read(p)) for p in files}
    )


def approved_implementation(approval):
    """Use the same revision/byte contract before execution and retrieval."""
    revision, code_hash = implementation_identity()
    if (
        approval.implementation_revision != revision
        or approval.implementation_sha256 != code_hash
    ):
        raise Hold(
            "current implementation does not match processing/retrieval approval"
        )
    return revision, code_hash


def inventory(root):
    """Observe existing data without adopting, deleting or changing any file."""
    result = {}
    for p in sorted(root.rglob("*")):
        info = p.lstat()
        if stat.S_ISLNK(info.st_mode) or not (
            stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
        ):
            raise Hold("unsafe output entry")
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise Hold("nonprivate output entry")
        result[p.relative_to(root).as_posix()] = {
            "mode": stat.S_IMODE(info.st_mode),
            "sha256": sha256(_read(p)) if p.is_file() else None,
        }
    return result


@contextmanager
def output_root(path, *, create=False):
    root = checked_path(explicit_root(path))
    if create:
        # Never initialize or adopt an existing directory, even an empty one.
        root.mkdir(mode=0o700)
        publish_bytes(root / ".mvp.lock", b"")
    info = root.stat()
    if not root.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Hold("private owned output root required")
    if set(p.name for p in root.iterdir()) - OWNED:
        raise Hold("unknown output contents; root retained")
    fd = os.open(root / ".mvp.lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = inventory(root)
        yield root, before


def load(root, name):
    return _json(_read(root / name))


def actor_for(intent, subject):
    if subject != intent["actor"]:
        raise Hold("operator identity conflict")
    return Principal(subject=subject, role="operator", courses=("cs50_python",))


def bundle_at(root):
    intent = load(root, "intent.json")
    processor = MaterialProcessor(root / "material")
    plan = MaterialPlan.model_validate(load(root, "plan.json"))
    (binding,) = plan.select(resource=intent["material_id"])
    receipt = processor.inspect(binding, ParserConfig.model_validate(intent["parser"]))
    raw, receipt_path = processor.downloader.paths(binding)
    return MaterialBundle(
        workspace=root / "material",
        raw_path=raw,
        normalized_path=root / "material" / receipt.normalized_path,
        receipt_path=receipt_path,
        plan_path=root / "plan.json",
        implementation_path=root / "implementation.json",
    )


def preflight(args):
    if not all((args.input, args.plan, args.material, args.approval)):
        raise Hold("run requires input, plan, material and approval")
    for p in (args.input, args.plan, args.approval):
        checked_path(p)
        if p.is_relative_to(args.output_root):
            raise Hold("inputs must be outside output root")
    raw, plan_bytes = _read(args.input), _read(args.plan)
    approval_bytes = private_bytes(args.approval, 65536)
    approval = ProcessingApproval.model_validate(_json(approval_bytes))
    plan = MaterialPlan.model_validate(_json(plan_bytes))
    (binding,) = plan.select(resource=args.material)
    parser = approval.parser
    revision, code_hash = approved_implementation(approval)
    if (
        approval.valid_until <= datetime.now(UTC)
        or approval.approved_by != args.actor
        or approval.actions != ACTIONS
        or approval.resource_id != binding.source_id
        or approval.material_id != binding.material_id
        or approval.original_url != binding.original_url
        or approval.source_origin != binding.source_origin
        or approval.raw_sha256 != sha256(raw)
        or approval.plan_sha256 != sha256(plan_bytes)
        or binding.resource.course_id != "cs50_python"
        or binding.format != "html"
        or parser.name != "html"
        or parser.version != "2"
        or parser_for(binding)[0] is None
        or parser_for(binding)[0].name != "html"
        or not raw
        or len(raw) > parser.max_bytes
        or (
            binding.source_origin == "official" and binding.license_status != "reviewed"
        )
    ):
        raise Hold("approval, raw hash, plan or implementation binding rejected")
    intent = {
        "schema_version": 1,
        "actor": args.actor,
        "source_id": binding.source_id,
        "material_id": binding.material_id,
        "original_url": binding.original_url,
        "source_origin": binding.source_origin,
        "raw_sha256": sha256(raw),
        "plan_sha256": sha256(plan_bytes),
        "approval_sha256": sha256(approval_bytes),
        "implementation_revision": revision,
        "implementation_sha256": code_hash,
        "parser": parser.model_dump(mode="json"),
    }
    intent["request_key"] = "cs50-mvp-" + fingerprint(intent)
    return raw, plan_bytes, approval_bytes, approval, binding, intent


def verify_persisted(root, intent, state, actor):
    store = ContentStore(root / "store")
    vid = state["parsed_version_id"]
    view = store.get_parsed_document(vid, actor=actor)
    if (
        view.source_id != intent["source_id"]
        or view.source_version_id != state["source_version_id"]
        or view.parser_config_id != state["parser_config_id"]
        or store.read_raw_artifact(view.source_id, intent["raw_sha256"], actor=actor)
        != _read(root / "input.html")
        or sha256(_read(root / "input.html")) != intent["raw_sha256"]
    ):
        raise Hold("stored raw/source binding conflict")
    payload = store.read_parsed_payload(vid, actor=actor)
    doc = NormalizedDocument.model_validate_json(payload)
    bundle = bundle_at(root)
    if (
        sha256(payload) != view.payload_sha256
        or doc.binding.material_id != intent["material_id"]
        or doc.raw_sha256 != intent["raw_sha256"]
        or doc.binding.source_origin != intent["source_origin"]
        or doc.parser.model_dump(mode="json") != intent["parser"]
        or payload != _read(bundle.normalized_path)
        or sha256(_read(root / "plan.json")) != intent["plan_sha256"]
    ):
        raise Hold("persisted normalized document conflict")
    for role, path in (
        ("receipt", bundle.receipt_path),
        ("plan", bundle.plan_path),
        ("implementation", bundle.implementation_path),
    ):
        if store.read_version_artifact(vid, role, actor=actor) != _read(path):
            raise Hold("persisted bundle evidence conflict")
    return store, doc


def retrieve(root, intent, state, actor, queries):
    store, doc = verify_persisted(root, intent, state, actor)
    index = ContentIndex(store, root / "index", cursor_key_file=root / "cursor.key")
    reader = ContentReader(
        ContentReadSettings(
            root=root / "store",
            cursor_key_file=root / "cursor.key",
        )
    )
    results = []
    originals = {b.block_id: b for b in doc.blocks}
    for query in queries:
        with index.search_lexical(
            query,
            actor=actor,
            source_ids=(intent["source_id"],),
            limit=5,
        ) as page:
            pass  # Release the search snapshot before independently resolving sources.
        if page.index_generation != state["index_generation"]:
            raise Hold("persistent index generation conflict")
        resolved = []
        for hit in page.items:
            original = originals.get(hit.block_id)
            text = reader.block(
                hit.parsed_version_id,
                hit.block_id,
                actor,
                {
                    "start": str(hit.excerpt.start),
                    "limit": str(hit.excerpt.end - hit.excerpt.start),
                },
            )
            structure = reader.block(
                hit.parsed_version_id,
                hit.block_id,
                actor,
                {},
                structured=True,
            )
            if (
                hit.source_id != intent["source_id"]
                or hit.parsed_version_id != state["parsed_version_id"]
                or original is None
                or text.text != hit.excerpt.text
                or text.text_sha256 != sha256(original.text.encode())
                or text.text != original.text[text.start : text.end]
                or not structure.locators
                or any(
                    loc.raw_artifact_sha256 != intent["raw_sha256"]
                    or loc.raw_reference.source_id != intent["source_id"]
                    or loc.raw_reference.source_version_id != hit.source_version_id
                    or loc.origin_pointer != f"/blocks/{original.order}"
                    for loc in structure.locators
                )
            ):
                raise Hold("retrieval provenance conflict")
            resolved.append(
                {
                    "hit": hit.model_dump(mode="json"),
                    "source_block": text.model_dump(mode="json"),
                    "source_structure": structure.model_dump(mode="json"),
                    "original_location": original.location.model_dump(mode="json"),
                }
            )
        results.append(
            {
                "query": query,
                "index_generation": page.index_generation,
                "results": resolved,
            }
        )
    return results


def retrieval_approval(root, intent, actor):
    """Validate the saved attestation without rewriting any historical evidence."""
    approval_bytes = _read(root / "approval.json")
    if sha256(approval_bytes) != intent["approval_sha256"]:
        raise Hold("saved approval conflict")
    approval = ProcessingApproval.model_validate(_json(approval_bytes))
    if (
        approval.valid_until <= datetime.now(UTC)
        or approval.approved_by != actor.subject
        or approval.actions != ACTIONS
    ):
        raise Hold("saved processing/retrieval approval no longer valid")
    revision, code_hash = approved_implementation(approval)
    if (
        intent.get("implementation_revision") != revision
        or intent.get("implementation_sha256") != code_hash
    ):
        raise Hold("saved intent implementation binding rejected")
    return approval


def report(root, intent, state, actor, queries):
    approval = retrieval_approval(root, intent, actor)
    tasks = approval.retrieval_tasks
    results = retrieve(root, intent, state, actor, [t.query for t in tasks] + queries)
    acceptance = []
    for task, result in zip(tasks, results[:3], strict=True):
        rank = next(
            (
                i
                for i, r in enumerate(result["results"], 1)
                if task.expected_passage in r["source_block"]["text"]
            ),
            None,
        )
        acceptance.append(
            {"query": task.query, "rank": rank, "passed": rank is not None}
        )
    passed = all(t["passed"] for t in acceptance)
    return {
        "schema_version": 1,
        "status": "completed" if passed else "retrieval_failed",
        "technical_status": "TECHNICAL PASS" if passed else "FAIL",
        "real_source_status": (
            "REAL-SOURCE ACCEPTED"
            if passed and intent["source_origin"] == "official"
            else "BLOCKED"
        ),
        "mvp_status": "PENDING",
        "intent": intent,
        "publication": state,
        "retrieval_acceptance": acceptance,
        "searches": results,
        "raw_bytes_verified": True,
    }


def run(args):
    raw, plan, approval_bytes, approval, binding, intent = preflight(args)
    actor = actor_for(intent, args.actor)
    exists = args.output_root.exists()
    with output_root(args.output_root, create=not exists) as (root, before):
        if exists:
            if load(root, "intent.json") != intent:
                raise Hold(
                    "existing input/approval intent conflict; use a new isolated root"
                )
            state = load(root, "state.json")
            if state["phase"] != "ready":
                raise Hold("incomplete operation; inspect status, no automatic retry")
            verify_material_bundle(bundle_at(root))
        else:
            for name, data in (
                ("intent.json", canonical(intent)),
                ("input.html", raw),
                ("plan.json", plan),
                ("approval.json", approval_bytes),
            ):
                publish_bytes(root / name, data)
            state = {"schema_version": 1, "phase": "preparing"}
            write_state(root / "state.json", state)
            processor = MaterialProcessor(root / "material")
            processor.downloader.obtain(
                binding, execute=True, local_file=root / "input.html"
            )
            receipt = processor.parse(binding, execute=True, config=approval.parser)
            raw_path, receipt_path = processor.downloader.paths(binding)
            normalized = root / "material" / receipt.normalized_path
            review = prepare_material_handoff(
                workspace=root / "material",
                raw_path=raw_path,
                normalized_path=normalized,
                receipt_path=receipt_path,
                plan_path=root / "plan.json",
            )
            if not review.report.passed or review.handoff is None:
                raise Hold("quality/handoff gate rejected material")
            evidence = ImplementationEvidence(
                implementation_revision=intent["implementation_revision"],
                parser_name=receipt.parser.name,
                parser_version=receipt.parser.version,
                parameters=receipt.parser.model_dump(mode="json"),
                source_id=binding.source_id,
                binding_id=binding.material_id,
                raw_sha256=sha256(raw),
                payload_sha256=sha256(_read(normalized)),
                receipt_sha256=sha256(_read(receipt_path)),
                evidence_reference=(
                    f"operator approval sha256:{intent['approval_sha256']}; "
                    f"actual Python bytes sha256:{intent['implementation_sha256']}"
                ),
            )
            publish_bytes(
                root / "implementation.json",
                canonical(evidence.model_dump(mode="json")),
            )
            candidate = verify_material_bundle(bundle_at(root))
            if _read(args.input) != raw or _read(raw_path) != raw:
                raise Hold("input changed before publication")
            store = ContentStore.initialize(root / "store")
            publish_bytes(root / "cursor.key", os.urandom(32))
            state["phase"] = "publication_pending"
            write_state(root / "state.json", state)
            publication = import_verified_bundle(
                store,
                candidate,
                actor=actor,
                request_key=intent["request_key"],
            )
            state.update(
                phase="published",
                parsed_version_id=publication.version.parsed_version_id,
                source_version_id=publication.version.source_version_id,
                parser_config_id=publication.version.parser_config_id,
            )
            write_state(root / "state.json", state)
            verify_persisted(root, intent, state, actor)
            index = ContentIndex.initialize(
                store, root / "index", cursor_key_file=root / "cursor.key"
            )
            state["phase"] = "index_pending"
            write_state(root / "state.json", state)
            built = index.build(
                IndexSelection(parsed_version_ids=(state["parsed_version_id"],)),
                actor=actor,
            )
            if built.state != "active" or built.generation_id is None:
                raise Hold("index activation not confirmed")
            with index.search_lexical(
                approval.retrieval_tasks[0].query, actor=actor, limit=5
            ) as page:
                index_generation = page.index_generation
            state.update(
                phase="ready",
                build_id=built.build_id,
                generation_id=built.generation_id,
                index_generation=index_generation,
                record_count=built.record_count,
            )
            write_state(root / "state.json", state)
        if _read(args.input) != raw:
            raise Hold("input changed after processing")
        result = report(root, intent, state, actor, args.query or [])
        result["inventory_before"] = before
        result["inventory_after_sha256"] = fingerprint(inventory(root))
        result["reused_publication"] = exists
        return result


def observe(args):
    with output_root(args.output_root) as (root, _before):
        intent, state = load(root, "intent.json"), load(root, "state.json")
        actor = actor_for(intent, args.actor)
        if args.operation == "search":
            if state["phase"] != "ready":
                raise Hold("incomplete operation; search not accepted")
            if not args.query:
                raise Hold("search requires at least one query")
            return report(root, intent, state, actor, args.query)
        observed = {
            "schema_version": 1,
            "status": "observed",
            "intent": intent,
            "publication": state,
            "technical_status": "NOT_ASSESSED",
        }
        # Forensic observation stays available after code changes or expiry.
        # A current approval binding alone is not a new retrieval acceptance.
        try:
            retrieval_approval(root, intent, actor)
            observed["retrieval_authorization"] = {"status": "current"}
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            observed["retrieval_authorization"] = {
                "status": "HOLD",
                "reason": str(error)
                if isinstance(error, Hold)
                else type(error).__name__,
            }
        if (root / "store").exists():
            store = ContentStore(root / "store")
            sources = store.list_sources(actor=actor)
            observed["sources"] = [s.model_dump(mode="json") for s in sources]
            observed["recovery"] = [
                r.model_dump(mode="json") for r in store.inspect_recovery(actor=actor)
            ]
            if (root / "index").exists():
                index = ContentIndex(
                    store, root / "index", cursor_key_file=root / "cursor.key"
                )
                observed["builds"] = [
                    b.model_dump(mode="json") for b in index.inspect_builds(actor=actor)
                ]
            reader = (
                ContentReader(
                    ContentReadSettings(
                        root=store.root, cursor_key_file=root / "cursor.key"
                    )
                )
                if (root / "cursor.key").exists()
                else None
            )
            observed["versions"] = []
            for source in sources:
                for version in store.list_source_versions(
                    source.source_id, actor=actor
                ):
                    row = version.model_dump(mode="json")
                    if reader:
                        row["parsed"] = reader.page(
                            "parsed_refs",
                            (source.source_id, version.source_version_id),
                            {},
                            actor,
                        ).model_dump(mode="json")
                    observed["versions"].append(row)
        return observed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run", "search", "status"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--material")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--query", action="append")
    args = parser.parse_args(argv)
    previous_umask = os.umask(0o077)
    try:
        checked_path(explicit_root(args.output_root))
        Principal(subject=args.actor, role="operator", courses=("cs50_python",))
        for query in args.query or []:
            checked_query(query)
        if args.operation == "status" and args.query:
            raise Hold("status does not accept queries")
        if args.operation != "run" and any(
            (args.input, args.plan, args.material, args.approval)
        ):
            raise Hold("input arguments are only valid for run")
        result = run(args) if args.operation == "run" else observe(args)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in {"completed", "observed"} else 2
    except (
        ContentStoreError,
        ReadFault,
        RetrievalFault,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "HOLD",
                    "success": False,
                    "code": getattr(error, "code", "operation_incomplete_or_rejected"),
                    "reason": str(error)
                    if isinstance(error, Hold)
                    else type(error).__name__,
                    "recovery": "retain root; inspect status; no automatic retry or quarantine release",
                }
            ),
            file=sys.stderr,
        )
        return 2
    finally:
        os.umask(previous_umask)


if __name__ == "__main__":
    raise SystemExit(main())
