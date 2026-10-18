"""Read-only corpus evaluation using existing gates; no new extraction or gold."""

import stat
import unicodedata
from collections import Counter
from pathlib import Path
from typing import get_args

from src.content_store.adapters import _capture, _json_bytes, _read, _verify_frozen
from src.content_store.errors import ContentStoreError
from src.content_store.inventory import InventoryRequest, _paths, inventory
from src.content_store.models import canonical, checked_actor, sha256, snapshot
from src.model_evaluation.material_evaluation import (
    CorpusManifest,
    Dimension,
    EvaluationReport,
    GoldDataset,
)
from src.model_evaluation.math_evaluation import FormulaCase
from src.model_materials.materials import MaterialResource
from src.tools_evaluation.evaluate_math import evaluate_case
from src.tools_lecture.execute_cs50 import safe_path
from src.tools_materials.storage import publish_bytes


def load_inputs(corpus_path, gold_path):
    return (
        CorpusManifest.model_validate_json(
            canonical(_json_bytes(_read(corpus_path))), strict=True
        ),
        GoldDataset.model_validate_json(
            canonical(_json_bytes(_read(gold_path))), strict=True
        ),
    )


def _observe(entry, roots, actor, store):
    root = Path(roots[entry.root_key])
    if not root.is_absolute():
        raise ValueError("Explicit absolute corpus roots required")
    paths = {k: safe_path(root, root / v) for k, v in entry.artifacts.items()}
    if entry.selection is not None:
        if entry.selection.bundle.workspace != root:
            raise ValueError("Bundle workspace must equal the explicitly selected root")
        paths = {
            k: safe_path(
                Path(v).parent
                if k in {"plan", "implementation", "prior_quality"}
                else root,
                Path(v),
            )
            for k, v in _paths(entry.selection).items()
        }
    aliases = {"payload": "parsed", "normalized": "parsed", "transcript": "parsed"}
    available, hashes, sizes, issues = (
        {k: None for k in ("raw", "parsed", "receipt", "quality")},
        {},
        {},
        [],
    )
    allowed = (
        entry.permission != "denied"
        and entry.origin != "unknown"
        and entry.course_id in actor.courses
    )
    for role, path in paths.items():
        role = aliases.get(role, role)
        try:
            mode = path.lstat().st_mode
            available[role] = stat.S_ISREG(mode)
            if not available[role]:
                issues.append("unsafe_artifact")
            elif allowed:
                raw = _read(path)  # Existing bounded no-symlink reader.
                hashes[role], sizes[role] = sha256(raw), len(raw)
        except FileNotFoundError:
            available[role] = False
        except (OSError, ValueError, ContentStoreError):
            available[role] = False
            issues.append("unreadable_artifact")
    if not allowed:
        issues.append("permission_or_origin_unverified")
    if not available.get("raw"):
        issues.append("missing_raw_artifact")
    if entry.raw_sha256 is not None and hashes.get("raw") not in {
        None,
        entry.raw_sha256,
    }:
        issues.append("raw_hash_conflict")
    observation = dict(
        entry_id=entry.entry_id,
        origin=entry.origin,
        format=entry.format,
        course_id=entry.course_id,
        source_id=entry.source_id,
        material_id=entry.material_id,
        section_keys=list(entry.section_keys),
        lecture_ids=list(entry.lecture_ids),
        original_url=entry.original_url,
        permission=entry.permission,
        permission_reference=entry.permission_reference,
        notes=list(entry.notes),
        available=available,
        hashes=hashes,
        sizes=sizes,
        classification="real_incomplete_bundle",
        binding_verified=False,
        receipt_verified=False,
        parser=None,
        source_version_id=None,
        content_store_publication="not_checked",
        quality=None,
        visual=None,
        issues=issues,
    )
    verified = None
    if entry.origin == "synthetic":
        observation["classification"] = "synthetic_fixture"
    elif entry.origin == "unknown":
        observation["classification"] = "unknown_origin"
    if entry.permission == "denied" or entry.course_id not in actor.courses:
        observation["classification"] = "permission_restricted"
    if entry.selection is None:
        issues.append("unverified_source_binding")
        if not available.get("receipt"):
            issues.append("missing_receipt")
        if not available.get("parsed"):
            issues.append("missing_parsed_artifact")
    elif (
        allowed
        and entry.permission == "evaluation"
        and "raw_hash_conflict" not in issues
    ):
        result = inventory(
            InventoryRequest(entries=(entry.selection,)), actor=actor, store=store
        ).report.entries[0]
        issues.extend(result.issues)
        if result.validation_status == "verified":
            try:
                frozen = _capture(entry.selection.bundle, entry.selection.kind)
                verified = _verify_frozen(frozen)
                # Reject a changed source between the two existing read-only snapshots.
                files = dict(frozen.files)
                current = {k: sha256(files[v]) for k, v in frozen.paths}
                if current != result.hashes or hashes != {
                    aliases.get(k, k): value for k, value in result.hashes.items()
                }:
                    raise ValueError("Corpus snapshot changed")
                expected_origin = (
                    "synthetic" if entry.origin == "synthetic" else "official"
                )
                if verified.registration.source_origin != expected_origin:
                    raise ValueError("Corpus origin contradicts verified binding")
                if (
                    entry.original_url is not None
                    and entry.original_url != verified.registration.original_url
                ):
                    raise ValueError("Corpus URL contradicts verified binding")
                expected_format = (
                    "srt" if verified.transcript else verified.config.parser_name
                )
                if entry.format != expected_format:
                    raise ValueError("Corpus format contradicts verified parser")
                if entry.section_keys and entry.section_keys != result.section_keys:
                    raise ValueError("Corpus section contradicts verified binding")
                if entry.lecture_ids and entry.lecture_ids != result.lecture_ids:
                    raise ValueError("Corpus lecture contradicts verified binding")
                material_id = (
                    None
                    if verified.transcript
                    else MaterialResource.model_validate_json(
                        verified.binding
                    ).material_id
                )
                if entry.material_id is not None and entry.material_id != material_id:
                    raise ValueError(
                        "Corpus material identity contradicts verified binding"
                    )
                observation.update(
                    binding_verified=True,
                    receipt_verified=True,
                    document_id=verified.original_document_id,
                    material_id=material_id,
                    original_url=verified.registration.original_url,
                    source_version_id=result.source_version_id,
                    section_keys=list(result.section_keys),
                    lecture_ids=list(result.lecture_ids),
                    parser=verified.config.model_dump(
                        mode="json", exclude={"parameters"}
                    )
                    | dict(config_id=verified.config.config_id),
                    content_store_publication=(
                        "present"
                        if result.existing_parsed_version_id
                        else "not_present"
                    )
                    if store is not None
                    else "not_checked",
                )
                if entry.origin == "real":
                    observation["classification"] = "verified_bundle"
                artifacts = {k: data for k, data, _ in verified.artifacts}
                if "quality" in artifacts:
                    report = _json_bytes(artifacts["quality"])
                    observation["quality"] = dict(
                        status=report["status"],
                        validator_version=report["validator_version"],
                        findings={}
                        if verified.transcript
                        else Counter(f["code"] for f in report["findings"]),
                    )
            except (OSError, ValueError, ContentStoreError):
                issues.append("bundle_snapshot_conflict")
                verified = None
                observation.update(
                    binding_verified=False,
                    receipt_verified=False,
                    source_version_id=None,
                    parser=None,
                    quality=None,
                )
                if entry.origin == "real":
                    observation["classification"] = "real_incomplete_bundle"
    elif entry.selection is not None:
        issues.append("evaluation_not_authorized")
    observation["issues"] = sorted(set(issues))
    return observation, verified


def _normalized(text):
    # Only a separate text metric; code/formulas never use whitespace folding.
    return " ".join(unicodedata.normalize("NFC", text).split())


def _category(code):
    if code in {
        "missing_text",
        "duplicated_text",
        "content_mismatch",
        "code_corruption",
        "table_structure_loss",
        "structure_mismatch",
    }:
        return "parsing_candidate"
    if (
        code == "wrong_locator"
        or "binding" in code
        or code == "source_version_conflict"
    ):
        return "source_binding_provenance"
    if (
        "integrity" in code
        or "projection" in code
        or code == "bundle_snapshot_conflict"
    ):
        return "persistence_projection"
    if (
        "artifact" in code
        or "permission" in code
        or code in {"raw_hash_conflict", "missing_receipt", "evaluation_not_authorized"}
    ):
        return "data_permission"
    return "evaluation_gap"


def _compare(reference, entry, observation, verified):
    result = dict(
        gold_id=reference.gold_id,
        entry_id=entry.entry_id,
        origin=entry.origin,
        format=entry.format,
        dimension=reference.dimension,
        status="not_evaluable",
        scores={},
        issues=[],
    )
    if reference.reference_status != "confirmed":
        result["issues"] = ["gold_" + reference.reference_status]
        return result
    if entry.origin == "real" and reference.method != "independent_source_annotation":
        result["issues"] = ["missing_independent_gold"]
        return result
    if verified is None or not observation["binding_verified"]:
        result["issues"] = ["unverified_source_binding"]
        return result
    if (
        reference.source_id,
        reference.source_version_id,
        reference.original_sha256,
    ) != (
        entry.source_id,
        observation["source_version_id"],
        observation["hashes"].get("raw"),
    ):
        result["issues"] = ["source_version_conflict"]
        return result
    blocks = {b.payload_pointer: b for b in verified.blocks}
    block = blocks.get(reference.target_pointer)
    scores = result["scores"]
    if reference.expected_content is not None:
        actual = block.text if block is not None else None
        scores["exact_content"] = actual == reference.expected_content
        if reference.dimension == "text":
            scores["normalized_text"] = actual is not None and _normalized(
                actual
            ) == _normalized(reference.expected_content)
        if reference.dimension == "formula":
            formula = evaluate_case(
                FormulaCase(
                    schema_version=1,
                    case_id=reference.gold_id,
                    source_document_id=reference.source_id,
                    section=reference.source_reference,
                    source_reference=reference.review_reference,
                    gold_origin=entry.origin,
                    reference_status="confirmed",
                    reference_formula=reference.expected_content,
                    predicted_formula=actual,
                    formula_format="latex",
                )
            )
            result["formula_status"] = formula.evaluation_status
            result["issues"].extend(formula.error_categories)
            scores["formula_correct"] = (
                None
                if formula.evaluation_status == "undetermined"
                else formula.evaluation_status == "correct"
            )
    if reference.expected_structure is not None:
        actual = block.model_dump(mode="json") if block is not None else {}
        actual["type"] = block.original_type if block is not None else None
        scores["structure"] = all(
            actual.get(key) == value
            for key, value in reference.expected_structure.items()
        )
    if reference.expected_locator is not None:
        scores["locator"] = (
            block is not None and reference.expected_locator in block.locators
        )
    if reference.expected_occurrences is not None:
        if reference.expected_content is None:
            result["issues"].append("occurrence_reference_missing_content")
        else:
            count = sum(
                b.text == reference.expected_content and b.aggregation_role == "primary"
                for b in verified.blocks
            )
            scores["occurrences"] = count == reference.expected_occurrences
            if count > reference.expected_occurrences:
                result["issues"].append("duplicated_text")
    if block is None:
        result["issues"].append("missing_text")
    if scores.get("exact_content") is False and block is not None:
        result["issues"].append(
            "code_corruption" if reference.dimension == "code" else "content_mismatch"
        )
    if scores.get("locator") is False:
        result["issues"].append("wrong_locator")
    if scores.get("structure") is False:
        result["issues"].append(
            "table_structure_loss"
            if reference.dimension == "table"
            else "structure_mismatch"
        )
    result["status"] = (
        "failed"
        if False in scores.values()
        else "undetermined"
        if None in scores.values() or not scores
        else "passed"
    )
    result["issues"] = sorted(set(result["issues"]))
    return result


def evaluate(corpus, gold, *, roots, actor, store=None):
    if type(corpus) is not CorpusManifest or type(gold) is not GoldDataset:
        raise ValueError("Typed versioned corpus and gold datasets required")
    actor = checked_actor(actor)
    corpus, gold = snapshot(corpus), snapshot(gold)
    if gold.dataset_version != corpus.dataset_version:
        raise ValueError("Corpus/gold dataset version mismatch")
    if actor.role != "operator" or (store is not None and not store.read_only):
        raise ValueError("Explicit operator and read-only store required")
    entries = {e.entry_id: e for e in corpus.entries}
    if any(r.entry_id not in entries for r in gold.references):
        raise ValueError("Gold references unknown corpus entry")
    if any(
        entries[r.entry_id].origin == "real"
        and r.reference_status == "confirmed"
        and r.method != "independent_source_annotation"
        for r in gold.references
    ):
        raise ValueError("Real gold requires independent source annotation")
    observations, views = {}, {}
    for entry in corpus.entries:
        observations[entry.entry_id], views[entry.entry_id] = _observe(
            entry, roots, actor, store
        )
        if (
            sum(sum(row["sizes"].values()) for row in observations.values())
            > 128 * 1024 * 1024
        ):
            raise ValueError("Corpus observation budget exceeds 128 MiB")
    results = [
        _compare(r, entries[r.entry_id], observations[r.entry_id], views[r.entry_id])
        for r in gold.references
    ]
    groups = []
    for origin in ("synthetic", "real"):
        for format_ in ("html", "pdf", "code", "srt", "txt"):
            for dimension in get_args(Dimension):
                selected = [
                    r
                    for r in results
                    if (r["origin"], r["format"], r["dimension"])
                    == (origin, format_, dimension)
                ]
                metrics = {}
                for metric in (
                    "exact_content",
                    "normalized_text",
                    "structure",
                    "locator",
                    "occurrences",
                    "formula_correct",
                ):
                    values = [
                        r["scores"][metric]
                        for r in selected
                        if r["scores"].get(metric) is not None
                    ]
                    numerator, denominator = sum(values), len(values)
                    metrics[metric] = dict(
                        numerator=numerator,
                        denominator=denominator,
                        rate=numerator / denominator if denominator else None,
                    )
                groups.append(
                    dict(
                        origin=origin,
                        format=format_,
                        dimension=dimension,
                        reference_count=len(selected),
                        not_evaluable=sum(
                            r["status"] == "not_evaluable" for r in selected
                        ),
                        undetermined=sum(
                            r["status"] == "undetermined" for r in selected
                        ),
                        metrics=metrics,
                    )
                )
    counts = Counter(r.reference_status for r in gold.references)
    for entry in corpus.entries:
        refs = [r for r in gold.references if r.entry_id == entry.entry_id]
        observations[entry.entry_id]["gold_review"] = dict(
            confirmed=sum(r.reference_status == "confirmed" for r in refs),
            pending=sum(r.reference_status == "pending_review" for r in refs),
        )
        if not any(r.reference_status == "confirmed" for r in refs):
            observations[entry.entry_id]["issues"].append("missing_gold_reference")
        row = observations[entry.entry_id]
        row["findings"] = [
            dict(code=code, category=_category(code)) for code in row["issues"]
        ]
    for result in results:
        result["findings"] = [
            dict(code=code, category=_category(code)) for code in result["issues"]
        ]
    by_origin = {
        origin: {
            status: sum(
                r.reference_status == status and entries[r.entry_id].origin == origin
                for r in gold.references
            )
            for status in ("confirmed", "pending_review", "rejected")
        }
        for origin in ("real", "synthetic", "unknown")
    }
    body = dict(
        schema_version=1,
        evaluator_version="cs50_corpus_evaluation_v1",
        dataset_version=corpus.dataset_version,
        corpus_sha256=sha256(canonical(corpus.model_dump(mode="json"))),
        gold_sha256=sha256(canonical(gold.model_dump(mode="json"))),
        release_status="requires_manual_real_acceptance",
        gold_counts=dict(
            confirmed=counts["confirmed"],
            pending_review=counts["pending_review"],
            rejected=counts["rejected"],
            missing_entries=sum(
                not any(r.entry_id == e.entry_id for r in gold.references)
                for e in corpus.entries
            ),
            by_origin=by_origin,
            entries_without_confirmed=sum(
                not any(
                    r.entry_id == e.entry_id and r.reference_status == "confirmed"
                    for r in gold.references
                )
                for e in corpus.entries
            ),
        ),
        inventory=list(observations.values()),
        results=results,
        metrics=groups,
        metric_method="explicit reviewed reference windows; no corpus-wide precision/recall claim",
        format_readiness={
            fmt: dict(
                real_entries=sum(
                    e.origin == "real" and e.format == fmt for e in corpus.entries
                ),
                available_real_raw=sum(
                    row["origin"] == "real"
                    and row["format"] == fmt
                    and row["available"].get("raw") is True
                    for row in observations.values()
                ),
                verified_real_bundles=sum(
                    row["origin"] == "real"
                    and row["format"] == fmt
                    and row["binding_verified"]
                    for row in observations.values()
                ),
                evaluable_real_references=sum(
                    r["origin"] == "real"
                    and r["format"] == fmt
                    and r["status"] != "not_evaluable"
                    for r in results
                ),
                manual_acceptance="not_granted_by_framework",
            )
            for fmt in ("html", "pdf", "code", "srt", "txt")
        },
    )
    return EvaluationReport(report=body, sha256=sha256(canonical(body)))


def publish(report, output, *, input_roots, input_files=()):
    output = Path(output).absolute()
    safe_path(output.parent, output)
    for root in input_roots:
        root = Path(root).absolute()
        if output == root or output.is_relative_to(root) or root.is_relative_to(output):
            raise ValueError("Report output overlaps input root")
    if any(
        output == Path(path).absolute() or Path(path).absolute().is_relative_to(output)
        for path in input_files
    ):
        raise ValueError("Report output overlaps input file")
    output.mkdir(parents=True, exist_ok=False)
    data = canonical(report.model_dump(mode="json")) + b"\n"
    body = report.report
    markdown = (
        "# CS50 corpus evaluation\n\nTechnical preparation; real acceptance requires manual review.\n\n"
        f"Dataset: {body['dataset_version']}\n\nGold: {body['gold_counts']}\n\n"
        + "\n".join(
            f"- {row['entry_id']}: {row['classification']}; {', '.join(row['issues'])}"
            for row in body["inventory"]
        )
        + "\n"
    ).encode()
    files = {
        "evaluation_report.v1.json": data,
        "summary.md": markdown,
        "corpus_inventory.v1.json": canonical(
            dict(
                schema_version=1,
                dataset_version=body["dataset_version"],
                entries=body["inventory"],
            )
        )
        + b"\n",
    }
    for name, raw in files.items():
        publish_bytes(output / name, raw)
    publish_bytes(
        output / "manifest.json",
        canonical(
            dict(
                schema_version=1,
                files={name: sha256(raw) for name, raw in files.items()},
            )
        )
        + b"\n",
    )
