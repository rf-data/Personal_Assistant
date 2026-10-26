"""Explicit local provenance checks and human review export; no gold promotion."""

import csv
import io
import os
import stat
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.models import sha256, snapshot
from src.job_control.catalog import read_file, safe_path
from src.job_control.models import Contract, Identifier
from src.model_evaluation.gold_candidates import GoldCandidatePool
from src.tools_materials.quality import _json


class OriginalGrant(Contract):
    root: Path
    permission_reference: Identifier
    origin: Literal["real", "synthetic"]
    permission: Literal["evaluation"]
    entry_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def explicit_root(self):
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("explicit absolute original root required")
        if len(set(self.entry_ids)) != len(self.entry_ids):
            raise ValueError("unique authorized entries required")
        return self


def _original_bytes(root, relative):
    """Open every component relative to held fds; reject symlink races/FIFOs."""
    path = safe_path(root, relative)
    root = safe_path(root)
    if not root.is_absolute():
        raise ValueError("explicit absolute original root required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:-1]:
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = child
        file_fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
        )
        try:
            if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                raise ValueError("regular original required")
            with os.fdopen(file_fd, "rb", closefd=False) as stream:
                raw = stream.read(16 * 1024**2 + 1)
            if len(raw) > 16 * 1024**2:
                raise ValueError("original exceeds preparation limit")
            return raw
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def validate_originals(pool, grants):
    """Hashes prove byte identity, not semantic correctness or operator permission."""
    pool = snapshot(pool)
    grants = {key: snapshot(grant) for key, grant in grants.items()}
    # Check every grant before any source read. Strings alone cannot confer rights:
    # the operator must supply a previously authorized private grant configuration.
    for source in pool.sources:
        grant = grants.get(source.root_key)
        if (
            grant is None
            or grant.permission != "evaluation"
            or source.entry_id not in grant.entry_ids
            or grant.origin != source.origin
            or grant.permission_reference != source.permission_reference
        ):
            raise ValueError("explicit original authorization missing")
        if not grant.root.is_absolute() or ".." in grant.root.parts:
            raise ValueError("explicit absolute original root required")
    for source in pool.sources:
        raw = _original_bytes(grants[source.root_key].root, source.original_file)
        if sha256(raw) != source.original_sha256:
            raise ValueError("original hash mismatch")
        if source.document_type != "pdf":
            lines = raw.decode("utf-8-sig").splitlines()
            for candidate in pool.candidates:
                if candidate.entry_id != source.entry_id:
                    continue
                for ref in candidate.references:
                    locator = ref.expected_locator
                    if locator.line_start is not None and max(
                        locator.line_start, locator.line_end or locator.line_start
                    ) > len(lines):
                        raise ValueError("original line reference does not exist")
    return pool


def review_csv(pool):
    pool = snapshot(pool)
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "question_id",
            "question",
            "expected_answer",
            "source_id",
            "source_version_id",
            "course_identity",
            "lecture_identity",
            "original_file",
            "sha256",
            "locators_json",
            "review_status",
            "evaluability",
            "needs_visual_context",
            "question_type",
            "difficulty",
            "generation_method",
            "ambiguity_note",
            "formula_original_notation",
            "revision",
            "change_note",
            "decision",
            "reason",
            "reviewer",
            "review_date",
            "review_reference",
        ]
    )
    sources = {s.entry_id: s for s in pool.sources}

    def cell(value):
        # Prevent spreadsheet formula execution in free-text/source fields.
        text = str(value)
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text

    for c in pool.candidates:
        source = sources[c.entry_id]
        from src.content_store.models import canonical

        locators = canonical(
            [r.expected_locator.model_dump(mode="json") for r in c.references]
        ).decode()
        writer.writerow(
            [
                cell(v)
                for v in [
                    c.query.query_id,
                    c.query.text,
                    c.expected_answer or "",
                    source.source_id,
                    source.source_version_id,
                    source.course_identity,
                    source.lecture_identity,
                    source.original_file,
                    source.original_sha256,
                    locators,
                    c.review_status,
                    c.evaluability,
                    c.needs_visual_context,
                    c.question_type,
                    c.difficulty,
                    c.generation_method,
                    c.ambiguity_note or "",
                    c.formula_original_notation or "",
                    c.revision,
                    c.change_note,
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            ]
        )
    return output.getvalue()


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--grants", type=Path, help="Explicit private authorized grants JSON"
    )
    parser.add_argument("--review-csv", type=Path)
    args = parser.parse_args(argv)
    try:
        pool = GoldCandidatePool.model_validate(
            _json(read_file(safe_path(args.dataset)))
        )
        grant_values = (
            {} if args.grants is None else _json(read_file(safe_path(args.grants)))
        )
        if not isinstance(grant_values, dict):
            raise ValueError("grant mapping required")
        grants = {
            key: OriginalGrant.model_validate(value)
            for key, value in grant_values.items()
        }
        pool = validate_originals(pool, grants)
        if args.review_csv:
            # New exclusive output only, and never inside any material root.
            output = safe_path(args.review_csv)
            if any(
                output.is_relative_to(g.root) or g.root.is_relative_to(output)
                for g in grants.values()
            ):
                raise ValueError("review output must be outside original roots")
            with output.open("x", encoding="utf-8", newline="") as stream:
                stream.write(review_csv(pool))
    except (ValueError, OSError, TypeError, RecursionError):
        parser.exit(2, "candidate validation failed; no original details disclosed\n")
    print(
        f"Validated pending candidates: {len(pool.candidates)}; real acceptance blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
