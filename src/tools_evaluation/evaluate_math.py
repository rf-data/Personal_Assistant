"""Deterministic evaluation of independent gold/prediction pairs, no extraction."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from src.model_evaluation.math_evaluation import (
    EquivalenceResult,
    FormulaCase,
    FormulaDataset,
    FormulaEvaluationReport,
    FormulaMetrics,
    FormulaResult,
)
from src.tools_evaluation.math_equivalence import check_equivalence
from src.tools_evaluation.math_syntax import (
    FormulaSyntaxError,
    normalize_formula,
    parse_formula,
)
from src.tools_lecture.cs50_manifest import _unique_json_keys


def load_json(raw):
    def reject(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    return json.loads(raw, object_pairs_hook=_unique_json_keys, parse_constant=reject)


def read_evaluation_bytes(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Evaluation input exceeds 8 MiB")
    return raw


def load_cases(path):
    raw = read_evaluation_bytes(path)
    if Path(path).suffix.lower() == ".jsonl":
        lines = raw.decode("utf-8").splitlines()
        data = {"schema_version": 1, "cases": []}
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                data["cases"].append(load_json(line))
            except ValueError as exc:
                raise ValueError(f"JSONL line {number}: {exc}") from exc
    else:
        data = load_json(raw)
    # JSON-mode strict validation supports tuple arrays without coercing scalars.
    dataset = FormulaDataset.model_validate_json(json.dumps(data), strict=True)
    for case in dataset.cases:
        _reference_parts(case)
    return dataset, hashlib.sha256(raw).hexdigest()


def _reference_parts(case):
    """Validate the partial-credit rubric independently of every prediction."""
    if not case.reference_parts:
        return ()
    _, reference = parse_formula(case.reference_formula, case.formula_format)
    parts = []
    for text in case.reference_parts:
        _, part = parse_formula(text, case.formula_format)
        if part == reference or not any(
            part == n for child in reference.children for n in child.walk()
        ):
            raise ValueError(
                f"{case.case_id}: reference_parts must be proper reference subexpressions"
            )
        parts.append(part)
    return tuple(parts)


def _differences(reference, prediction):
    """Observable notation differences; these are not semantic diagnoses."""
    a = list(reference.walk())
    b = list(prediction.walk())
    categories = []

    def values(nodes, kind):
        return [
            n.children[1].payload()
            if kind in {"pow", "subscript"}
            else n.value
            if not n.children
            else n.payload()
            for n in nodes
            if n.kind == kind
        ]

    if values(a, "symbol") != values(b, "symbol") or values(a, "num") != values(
        b, "num"
    ):
        categories.append("symbol_error")
    if [
        n.kind
        for n in a
        if n.kind in {"add", "sub", "mul", "div", "eq", "neg", "pos", "cross", "dot"}
    ] != [
        n.kind
        for n in b
        if n.kind in {"add", "sub", "mul", "div", "eq", "neg", "pos", "cross", "dot"}
    ]:
        categories.append("operator_error")
    for kind, category in (
        ("pow", "exponent_error"),
        ("subscript", "subscript_error"),
        ("div", "fraction_error"),
    ):
        if values(a, kind) != values(b, kind):
            categories.append(category)
    if reference != prediction:
        categories.append("structure_error")
    return categories


def evaluate_case(case, *, equivalence_backend="none"):
    if equivalence_backend not in {"none", "sympy"}:
        raise ValueError("Unknown equivalence backend")
    case = FormulaCase.model_validate_json(case.model_dump_json(), strict=True)
    parts = _reference_parts(case)
    unknown = EquivalenceResult(
        status="undetermined", backend="none", reason="no_comparable_formula_pair"
    )
    common = dict(
        case=case, equivalence=unknown, evaluation_notes=case.evaluation_notes
    )
    if case.reference_status == "ambiguous" or case.prediction_ambiguous:
        return FormulaResult(
            **common,
            evaluation_status="undetermined",
            error_categories=("ambiguous_source", "not_evaluable"),
        )
    if case.reference_status == "absent":
        return FormulaResult(
            **common,
            evaluation_status="extra_formula"
            if case.predicted_formula is not None
            else "correct",
            error_categories=("extra_formula",)
            if case.predicted_formula is not None
            else (),
        )
    if case.predicted_formula is None:
        return FormulaResult(
            **common,
            evaluation_status="missing_formula",
            error_categories=("missing_formula",),
        )
    exact = case.reference_formula == case.predicted_formula
    normalized = []
    trees = []
    issues = []
    categories = []
    for label, text in (
        ("reference", case.reference_formula),
        ("prediction", case.predicted_formula),
    ):
        try:
            norm = normalize_formula(text)
        except FormulaSyntaxError as exc:
            norm = None
            issues.append(f"{label}: {exc}")
            categories.append("not_evaluable" if exc.unsupported else "format_error")
        normalized.append(norm)
        try:
            _, tree = parse_formula(text, case.formula_format)
        except FormulaSyntaxError as exc:
            tree = None
            issues.append(f"{label}: {exc}")
            categories.extend(
                ("format_error", "not_evaluable")
                if case.formula_format not in {"latex", "plain_text"}
                else ("not_evaluable",)
                if exc.unsupported
                else ("format_error", "not_evaluable")
            )
        trees.append(tree)
    common.update(
        exact_match=exact,
        normalized_reference=normalized[0],
        normalized_prediction=normalized[1],
        normalized_match=normalized[0] == normalized[1]
        if None not in normalized
        else None,
    )
    common["evaluation_notes"] = (*case.evaluation_notes, *dict.fromkeys(issues))
    if None in trees:
        return FormulaResult(
            **common,
            evaluation_status="undetermined",
            error_categories=tuple(sorted(set(categories))),
        )
    ref, pred = trees
    equivalence = check_equivalence(ref, pred, backend=equivalence_backend)
    common.update(structural_match=ref == pred, equivalence=equivalence)
    if equivalence.status == "equivalent":
        return FormulaResult(**common, evaluation_status="correct")
    categories = _differences(ref, pred)
    if pred in parts:
        status = "partially_correct"
        common["evaluation_notes"] += (
            "Exact reconstruction of an independently annotated proper source component; the full formula is incomplete.",
        )
    elif equivalence.status == "not_equivalent":
        status = "incorrect"
    else:
        status = "undetermined"
        categories.append("not_evaluable")
    return FormulaResult(
        **common,
        evaluation_status=status,
        error_categories=tuple(sorted(set(categories))),
    )


def aggregate(results):
    pairs = [r for r in results if r.exact_match is not None]

    def rate(count):
        return count / len(pairs) if pairs else None

    return FormulaMetrics(
        case_count=len(results),
        evaluable_count=sum(r.evaluation_status != "undetermined" for r in results),
        paired_count=len(pairs),
        exact_matches=sum(r.exact_match is True for r in pairs),
        exact_match_rate=rate(sum(r.exact_match is True for r in pairs)),
        normalized_matches=sum(r.normalized_match is True for r in pairs),
        normalized_match_rate=rate(sum(r.normalized_match is True for r in pairs)),
        structure_comparable_count=sum(r.structural_match is not None for r in results),
        structural_matches=sum(r.structural_match is True for r in results),
        equivalence_decided_count=sum(
            r.equivalence.status != "undetermined" for r in results
        ),
        equivalent_count=sum(r.equivalence.status == "equivalent" for r in results),
        symbolic_equivalent_count=sum(
            r.equivalence.status == "equivalent" and r.equivalence.backend == "sympy"
            for r in results
        ),
        undetermined_count=sum(r.evaluation_status == "undetermined" for r in results),
        error_frequencies=dict(
            sorted(Counter(c for r in results for c in r.error_categories).items())
        ),
    )


def evaluate_dataset(path, *, case_ids=(), equivalence_backend="none"):
    dataset, digest = load_cases(path)
    requested = set(case_ids)
    if len(requested) != len(case_ids) or requested - {
        c.case_id for c in dataset.cases
    }:
        raise ValueError("Duplicate or unknown selected case_id")
    selected = tuple(
        c for c in dataset.cases if not requested or c.case_id in requested
    )
    results = tuple(
        evaluate_case(c, equivalence_backend=equivalence_backend) for c in selected
    )
    return FormulaEvaluationReport(
        input_path=str(path),
        input_sha256=digest,
        equivalence_backend=equivalence_backend,
        metrics={
            origin: aggregate([r for r in results if r.case.gold_origin == origin])
            for origin in ("synthetic", "real")
        },
        results=results,
        failed_case_ids=tuple(
            r.case.case_id for r in results if r.evaluation_status != "correct"
        ),
    )
