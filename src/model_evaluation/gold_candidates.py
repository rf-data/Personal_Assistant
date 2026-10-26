"""Pending candidate envelopes around C23 GoldReference, never accepted gold.

Course/lecture labels here are inventory identities, not canonical ACL grants.
C23/C24 currently restrict operational CourseId to CS50; no invented Loviscach
ContentStore/Parsed binding is created by this preparation contract.
"""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.models import Name, fingerprint
from src.evaluation_store.models import QuerySpec
from src.job_control.models import Contract, Identifier, Sha
from src.model_evaluation.content_retrieval import Versioned
from src.model_evaluation.material_evaluation import GoldReference


class OriginalSource(Contract):
    entry_id: Identifier
    source_id: Name
    source_version_id: Name
    course_identity: Identifier
    lecture_identity: Identifier
    root_key: Identifier
    original_file: str = Field(min_length=1, max_length=300)
    original_sha256: Sha
    document_type: Literal["srt", "vtt", "transcript_json", "pdf", "html"]
    language: str = Field(pattern=r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})?$")
    origin: Literal["real", "synthetic"]
    permission_reference: Identifier
    parsing_status: Literal["not_checked", "available", "missing"]
    # These are descriptive labels only; never independent evidence or file reads.
    alternative_representations: tuple[Identifier, ...] = Field(
        default=(), max_length=8
    )

    @model_validator(mode="after")
    def relative_original(self):
        path = PurePosixPath(self.original_file)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in self.original_file
            or path.as_posix() != self.original_file
            or any(ord(c) < 32 for c in self.original_file)
        ):
            raise ValueError("normalized relative original file required")
        return self


class GoldCandidate(Versioned):
    query: QuerySpec
    entry_id: Identifier
    expected_answer: str | None = Field(default=None, min_length=1, max_length=2000)
    question_type: Literal[
        "fact",
        "definition",
        "relationship",
        "rule",
        "multipart",
        "contrast",
        "formula",
        "unanswerable",
    ]
    difficulty: Literal["easy", "medium", "hard"]
    generation_method: Literal["independent_source_annotation", "synthetic_reference"]
    review_status: Literal["pending_human_review"] = "pending_human_review"
    references: tuple[GoldReference, ...] = Field(min_length=1, max_length=8)
    needs_visual_context: bool = Field(strict=True)
    visual_context_complete: bool = Field(strict=True)
    ambiguity_note: str | None = Field(default=None, min_length=1, max_length=1000)
    evaluability: Literal["pending_review", "not_evaluable"]
    unanswerable_scope_note: str | None = Field(
        default=None, min_length=1, max_length=1000
    )
    # Formula predictions belong in the existing C11 pair contract after review.
    formula_original_notation: str | None = Field(
        default=None, min_length=1, max_length=1000
    )
    revision: int = Field(strict=True, ge=1)
    change_note: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def pending_independent(self):
        if (self.question_type == "unanswerable") != (self.expected_answer is None):
            raise ValueError("unanswerable questions require null expected answer")
        if (self.question_type == "unanswerable") != bool(self.unanswerable_scope_note):
            raise ValueError("explicit reviewed search scope required for unanswerable")
        if (
            self.needs_visual_context
            and not self.visual_context_complete
            or self.ambiguity_note
        ) and self.evaluability != "not_evaluable":
            raise ValueError("incomplete or ambiguous evidence is not evaluable")
        if not self.needs_visual_context and not self.visual_context_complete:
            raise ValueError("no visual requirement cannot mean missing visuals")
        if self.question_type == "formula" and self.formula_original_notation is None:
            if not self.needs_visual_context or self.evaluability != "not_evaluable":
                raise ValueError(
                    "missing formula requires visual context and exclusion"
                )
        if (
            self.question_type != "formula"
            and self.formula_original_notation is not None
        ):
            raise ValueError("formula notation applies only to formula candidates")
        for ref in self.references:
            if (
                ref.entry_id != self.entry_id
                or ref.reference_status != "pending_review"
                or ref.method != self.generation_method
                or ref.expected_locator is None
                or not ref.source_id
                or not ref.source_version_id
                or not ref.target_pointer
                or ref.expected_locator.origin_pointer != ref.target_pointer
                or ref.reviewer
                or ref.review_reference
                or ref.review_date
            ):
                raise ValueError(
                    "pending independently anchored C23 reference required"
                )
            if self.question_type == "unanswerable" and (
                ref.expected_content != "" or ref.expected_occurrences != 0
            ):
                raise ValueError(
                    "unanswerable reference must declare absent observation"
                )
        if len({r.gold_id for r in self.references}) != len(self.references):
            raise ValueError("duplicate evidence identity")
        return self


def candidate_id(entry_id, question):
    """Question identity survives answer/review revisions; wording changes make a new ID."""
    return "gc_" + fingerprint(dict(entry_id=entry_id, question=question))[:32]


class GoldCandidatePool(Versioned):
    dataset_version: Identifier
    origin: Literal["real", "synthetic"]
    sources: tuple[OriginalSource, ...] = Field(max_length=30)
    candidates: tuple[GoldCandidate, ...] = Field(max_length=30)
    real_acceptance: Literal["blocked"] = "blocked"

    @model_validator(mode="after")
    def provenance(self):
        sources = {s.entry_id: s for s in self.sources}
        if len(sources) != len(self.sources) or any(
            s.origin != self.origin for s in self.sources
        ):
            raise ValueError("duplicate source or mixed real/synthetic data")
        ids, questions, gold_ids = set(), set(), set()
        for c in self.candidates:
            sid = c.entry_id
            if sid not in sources:
                raise ValueError("evidence source missing")
            source = sources[sid]
            question = " ".join(c.query.text.casefold().split())
            if c.query.query_id != candidate_id(sid, c.query.text):
                raise ValueError("unstable candidate identity")
            if c.query.query_id in ids or question in questions:
                raise ValueError("duplicate question")
            ids.add(c.query.query_id)
            questions.add(question)
            expected_method = (
                "synthetic_reference"
                if self.origin == "synthetic"
                else "independent_source_annotation"
            )
            if c.generation_method != expected_method:
                raise ValueError("generation method contradicts origin")
            for ref in c.references:
                if (ref.source_id, ref.source_version_id, ref.original_sha256) != (
                    source.source_id,
                    source.source_version_id,
                    source.original_sha256,
                ):
                    raise ValueError("original identity/hash/version mismatch")
                if ref.gold_id in gold_ids:
                    raise ValueError("duplicate global gold identity")
                gold_ids.add(ref.gold_id)
        return self
