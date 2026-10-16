"""Independent formula evaluation contracts; never Knowledge verification flags."""

from typing import Annotated, Literal

from pydantic import Field, StrictInt, field_validator, model_validator

from src.model_discovery.cs50 import DiscoveryModel, NonEmpty

Formula = Annotated[str, Field(min_length=1, max_length=2048)]
Category = Literal[
    "missing_formula",
    "extra_formula",
    "symbol_error",
    "operator_error",
    "exponent_error",
    "subscript_error",
    "fraction_error",
    "structure_error",
    "format_error",
    "ambiguous_source",
    "not_evaluable",
]
Status = Literal[
    "correct",
    "partially_correct",
    "incorrect",
    "missing_formula",
    "extra_formula",
    "undetermined",
]


class FormulaCase(DiscoveryModel):
    schema_version: Literal[1]  # Explicit: no implicit legacy version.
    case_id: NonEmpty
    source_document_id: NonEmpty
    page: StrictInt | None = Field(default=None, ge=1)
    section: NonEmpty | None = None
    source_reference: (
        NonEmpty  # Independent reference sheet / manually reviewed source.
    )
    gold_origin: Literal["synthetic", "real"]
    reference_status: Literal["confirmed", "absent", "ambiguous"]
    reference_formula: Formula | None
    predicted_formula: Formula | None
    formula_format: NonEmpty
    # Independently annotated proper source components; never inferred from prediction.
    reference_parts: tuple[Formula, ...] = ()
    evaluation_notes: tuple[NonEmpty, ...] = ()
    prediction_ambiguous: bool = False
    prediction_reference: str | None = None
    prediction_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("reference_formula", "predicted_formula")
    @classmethod
    def nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Use null for an absent formula, not whitespace")
        return value

    @model_validator(mode="after")
    def checked_gold(self):
        if self.page is None and self.section is None:
            raise ValueError("Source page or section is required")
        if self.reference_status == "confirmed" and self.reference_formula is None:
            raise ValueError("Confirmed gold needs an independent reference formula")
        if self.reference_status == "absent" and self.reference_formula is not None:
            raise ValueError("Absent gold cannot contain a reference formula")
        if self.reference_parts and self.reference_status != "confirmed":
            raise ValueError("Partial-credit references require confirmed gold")
        if len(set(self.reference_parts)) != len(self.reference_parts):
            raise ValueError("Duplicate reference parts")
        if self.prediction_sha256 is not None and not self.prediction_reference:
            raise ValueError("Prediction artifact hash needs its explicit reference")
        return self


class FormulaDataset(DiscoveryModel):
    schema_version: Literal[1]
    cases: tuple[FormulaCase, ...] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_cases(self):
        if len({c.case_id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate case_id")
        return self


class EquivalenceResult(DiscoveryModel):
    status: Literal["equivalent", "not_equivalent", "undetermined"]
    backend: Literal["structural_identity", "none", "sympy"]
    reason: str
    backend_version: str | None = None


class FormulaResult(DiscoveryModel):
    schema_version: Literal[1] = 1
    case: FormulaCase
    evaluation_status: Status
    exact_match: bool | None = None
    normalized_match: bool | None = None
    structural_match: bool | None = None
    normalized_reference: str | None = None
    normalized_prediction: str | None = None
    equivalence: EquivalenceResult
    error_categories: tuple[Category, ...] = ()
    evaluation_notes: tuple[str, ...] = ()


class FormulaMetrics(DiscoveryModel):
    case_count: int
    evaluable_count: int
    paired_count: int
    exact_matches: int
    exact_match_rate: float | None
    normalized_matches: int
    normalized_match_rate: float | None
    structure_comparable_count: int
    structural_matches: int
    equivalence_decided_count: int
    equivalent_count: int
    symbolic_equivalent_count: int
    undetermined_count: int
    error_frequencies: dict[str, int]


class FormulaEvaluationReport(DiscoveryModel):
    schema_version: Literal[1] = 1
    evaluator_version: Literal["formula_evaluation_v1"] = "formula_evaluation_v1"
    purpose: Literal["offline_evaluation_harness_not_model_quality"] = (
        "offline_evaluation_harness_not_model_quality"
    )
    input_path: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    equivalence_backend: Literal["none", "sympy"]
    metrics: dict[Literal["synthetic", "real"], FormulaMetrics]
    results: tuple[FormulaResult, ...]
    failed_case_ids: tuple[str, ...]
