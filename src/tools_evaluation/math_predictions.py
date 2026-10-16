"""Bind an existing visual prediction to independently supplied gold, read-only."""

import hashlib
import json

from src.model_evaluation.math_evaluation import FormulaCase
from src.model_knowledge.data_knowledge import VisualAnalysisDocument
from src.tools_evaluation.evaluate_math import load_json, read_evaluation_bytes


def bind_visual_prediction(case, path, *, batch_id, expression_id):
    case = FormulaCase.model_validate_json(case.model_dump_json(), strict=True)
    raw = read_evaluation_bytes(path)
    data = load_json(raw)
    # Existing legacy models ignore extras. Never silently accept the old
    # {"results": ...} shape as an empty current VisualAnalysisDocument.
    if (
        not isinstance(data, dict)
        or set(data) - set(VisualAnalysisDocument.model_fields)
        or "api_results" not in data
    ):
        raise ValueError(
            "Expected explicit current VisualAnalysisDocument.api_results; legacy shapes require reviewed conversion"
        )
    document = VisualAnalysisDocument.model_validate_json(raw, strict=True)
    if (
        document.source_id != case.source_document_id
        or not case.section
        or case.page is not None
    ):
        raise ValueError(
            "Visual source_id/section cannot be inferred from a PDF page or different document"
        )
    batches = [r for r in document.api_results if r.batch_id == batch_id]
    if len(batches) != 1 or batches[0].section_id != case.section:
        raise ValueError("Missing, duplicate or foreign-section visual batch")
    expressions = [
        e for e in batches[0].expressions if e.expression_id == expression_id
    ]
    if len(expressions) != 1:
        raise ValueError("Missing or duplicate visual expression_id")
    expression = expressions[0]
    if expression.section_id != case.section or expression.batch_id != batch_id:
        raise ValueError("Expression contradicts selected batch/section")
    if case.formula_format not in {"latex", "plain_text"}:
        raise ValueError("Unsupported prediction format")
    value = (
        expression.visual_latex
        if case.formula_format == "latex"
        else expression.visual_plain_text
    )
    # No fallback between formats, no gold inference, repair or Knowledge writes.
    payload = case.model_dump(mode="json")
    payload.update(
        predicted_formula=value if value and value.strip() else None,
        prediction_ambiguous=expression.ambiguous,
        prediction_reference=f"{path}#api_results/{batch_id}/expressions/{expression_id}",
        prediction_sha256=hashlib.sha256(raw).hexdigest(),
    )
    return FormulaCase.model_validate_json(json.dumps(payload), strict=True)
