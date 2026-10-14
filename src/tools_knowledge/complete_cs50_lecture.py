"""Full-lecture completion requires every verified A01 chunk, never file existence."""

import hashlib
import json
from typing import Literal

from src.tools_knowledge.bind_cs50_transcript import build_cs50_knowledge_document
from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    CheckpointStore,
    Contract,
    atomic_json,
    encoded,
)
from src.tools_knowledge.cs50_quality import quality_report
from src.tools_knowledge.run_cs50_lecture import (
    checked_output,
    validate_chunk,
    verify_budget,
)
from src.tools_lecture.adapt_cs50 import Sha256
from src.tools_lecture.execute_cs50 import safe_path

FILES = {
    "extraction": "extraction.json",
    "consolidated": "consolidated.json",
    "quality": "quality.json",
    "coverage": "coverage.json",
}


class LectureCompletion(Contract):
    schema_version: Literal[1] = 1
    phase: Literal["prepared", "done"]
    job_id: Sha256
    expected_chunk_ids: tuple[str, ...]
    artifacts: dict[str, Sha256]


def complete_lecture(job, directory, budget):
    directory = checked_output(job, directory)
    with CheckpointStore(
        directory / "checkpoint", job.identity, job.chunks
    ).locked() as store:
        results = []
        audit = []
        for chunk in job.chunks:
            verify_budget(budget, store, chunk.chunk_id)
            value = store.reuse(
                chunk.chunk_id,
                lambda values, chunk=chunk: validate_chunk(job, chunk, values),
            )
            if value is None:
                raise CheckpointConflict(
                    "Lecture incomplete: every expected chunk must be done"
                )
            result, artifacts, _ = value
            verify_budget(budget, store, chunk.chunk_id, validated=True)
            results.append(result)
            audit.extend(artifacts["evidence"]["items"])
        if (
            store.state.status != "done"
            or tuple(r.analysis.chunk_id for r in results)
            != job.identity.selected_chunks
        ):
            raise CheckpointConflict("Missing/duplicate/foreign lecture result")
        document = build_cs50_knowledge_document(
            job.input,
            job.chunks,
            results,
            plan=job.plan,
            workspace=job.workspace,
            evidence_mode=job.config.evidence_mode,
        )
        consolidated = consolidate_knowledge(document)
        # Existing regular business models, not a parallel serialization contract.
        assert (
            type(document).model_validate_json(document.model_dump_json()) == document
        )
        assert (
            type(consolidated).model_validate_json(consolidated.model_dump_json())
            == consolidated
        )
        origin = "LLM" if job.config.execute_llm else "synthetic"
        coverage = {
            "schema_version": 1,
            "job_id": job.identity.job_id,
            "course_id": job.input.course_id,
            "section_key": job.input.section_key,
            "lecture_id": job.input.lecture_id,
            "resource_id": job.input.resource_id,
            "source_id": job.input.source_id,
            "expected_chunk_ids": list(job.identity.selected_chunks),
            "processed_chunk_ids": [r.analysis.chunk_id for r in results],
            "expected_chunks": len(job.chunks),
            "processed_chunks": len(results),
            "complete": True,
            "result_origin": origin,
        }
        values = {
            "extraction": document.model_dump(mode="json"),
            "consolidated": consolidated.model_dump(mode="json"),
            "quality": quality_report(
                document,
                job.chunks,
                evidence_audit=audit,
                worker_report={"validated": True, "result_origin": origin},
            ),
            "coverage": coverage,
        }
        hashes = {
            key: hashlib.sha256(encoded(value)).hexdigest()
            for key, value in values.items()
        }
        prepared = LectureCompletion(
            phase="prepared",
            job_id=job.identity.job_id,
            expected_chunk_ids=job.identity.selected_chunks,
            artifacts=hashes,
        )
        folder = safe_path(directory, directory / "completion")
        marker = safe_path(directory, directory / "completion.v1.json")
        receipt = safe_path(directory, directory / "completion.prepared.v1.json")
        existed = receipt.exists()
        if existed:
            try:
                actual = LectureCompletion.model_validate_json(receipt.read_bytes())
            except (OSError, ValueError) as error:
                raise CheckpointConflict(
                    "Corrupt lecture completion receipt"
                ) from error
            if actual != prepared:
                raise CheckpointConflict("Lecture completion identity/hash conflict")
        else:
            if folder.exists() or marker.exists():
                raise CheckpointConflict("Unreceipted lecture completion artifacts")
            atomic_json(receipt, prepared.model_dump(mode="json"))
            folder.mkdir()
        for key, filename in FILES.items():
            path = safe_path(directory, folder / filename)
            if existed:
                try:
                    raw = path.read_bytes()
                    if (
                        hashlib.sha256(raw).hexdigest() != hashes[key]
                        or json.loads(raw) != values[key]
                    ):
                        raise ValueError("integrity")
                except (OSError, ValueError) as error:
                    raise CheckpointConflict(
                        "Missing/corrupt prepared lecture artifact"
                    ) from error
            else:
                atomic_json(path, values[key])
        done = prepared.model_copy(update={"phase": "done"})
        if marker.exists():
            try:
                if LectureCompletion.model_validate_json(marker.read_bytes()) != done:
                    raise ValueError("marker")
            except (OSError, ValueError) as error:
                raise CheckpointConflict("Invalid lecture completion marker") from error
        else:
            atomic_json(marker, done.model_dump(mode="json"))
        return done, values
