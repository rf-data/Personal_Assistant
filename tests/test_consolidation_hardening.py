"""Exercise real consolidation/runner boundaries, synthetic data, no SDK/network."""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from src.model_knowledge.data_knowledge import (
    ConsolidatedKnowledgeDocument,
    TranscriptKnowledgeDocument,
)
from src.run_knowledge_consolidation import (
    main,
    process_course_knowledge,
    process_knowledge_file,
)
from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
from src.tools_knowledge.consolidation_run import RunReport, hash_bytes, read_json
from src.tools_knowledge.consolidation_validation import validate_output
from src.tools_knowledge.cs50_checkpoint import encoded, fingerprint

FIXTURES = Path(__file__).parent / "fixtures/consolidation/synthetic_course"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def course(tmp_path):
    root = tmp_path / "inputs"
    root.mkdir()
    for path in FIXTURES.glob("*.json"):
        (root / path.name).write_bytes(path.read_bytes())
    return root, sorted(root.glob("*.json")), tmp_path / "outputs"


def run(course, **kwargs):
    root, paths, output = course
    return process_course_knowledge(paths, output, "offline", input_root=root, **kwargs)


def mutate(path, callback):
    value = json.loads(path.read_bytes())
    callback(value)
    path.write_bytes(encoded(value))


def test_course_read_only_and_deterministic(course):
    root, paths, output = course
    before = {p.name: p.read_bytes() for p in paths}
    a = run(course)
    b = run((root, list(reversed(paths)) + paths, output))
    assert a == b
    assert not output.exists()
    assert before == {p.name: p.read_bytes() for p in paths}
    assert a.counts["lectures_examined"] == 2
    assert a.counts["inputs_selected"] == 4
    assert a.counts["objects_processed"] == 32
    assert a.counts["objects_remaining"] == 24
    assert a.counts["objects_merged"] == a.counts["duplicates"] == 8
    assert a.counts["pending"] == 4
    assert a.counts["conflicts"] >= 8
    assert RunReport.model_validate_json(a.model_dump_json()) == a
    payload = a.model_dump(mode="json", exclude={"report_sha256"})
    assert a.report_sha256 == fingerprint(payload)


def test_evidence_provenance_and_ids(course):
    document = TranscriptKnowledgeDocument.model_validate_json(
        course[1][0].read_bytes()
    )
    original = document.model_dump_json()
    result = consolidate_knowledge(document)
    assert result == consolidate_knowledge(document)
    assert document.model_dump_json() == original
    assert [i.statement_id for i in result.statements] == [
        "KS0001",
        "KS0002",
        "KS0003",
        "KS0004",
    ]
    assert [i.expression_id for i in result.formulas] == ["KF0001", "KF0002"]
    assert len(result.statements[0].evidence) == len(result.formulas[0].evidence) == 2
    assert result.statements[0].evidence[1].segment_ids == [1]
    assert result.formulas[0].verification_status == "pending"
    assert result.transcript_provenance == document.transcript_provenance
    validate_output(document, result)


@pytest.mark.parametrize(
    "left,right",
    [
        ("x = a + b", "x = a - b"),
        ("A maps to B.", "a maps to b."),
        ("x²", "x2"),
        ("x^2", "x^3"),
        ("x_i", "x_j"),
        (r"\frac{a}{b}", r"\frac{b}{a}"),
        ("x y", "xy"),
        ("The result is positive.", "The result is not positive."),
    ],
)
def test_distinct_facts_are_not_merged(course, left, right):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    chunk = doc.chunks[0]
    chunk.extraction.statements = [
        chunk.extraction.statements[0].model_copy(
            update={"text": left, "statement_id": "S1"}
        ),
        chunk.extraction.statements[1].model_copy(
            update={"text": right, "statement_id": "S2"}
        ),
    ]
    chunk.extraction.formulas = [
        chunk.extraction.formulas[0].model_copy(
            update={"latex": left, "plain_text": left, "expression_id": "F1"}
        ),
        chunk.extraction.formulas[1].model_copy(
            update={"latex": right, "plain_text": right, "expression_id": "F2"}
        ),
    ]
    doc.chunks = [chunk]
    result = consolidate_knowledge(doc, statement_similarity=0, expression_similarity=0)
    assert len(result.statements) == len(result.formulas) == 2


def test_formula_representations_must_both_agree(course):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    chunk = doc.chunks[0]
    first, second = chunk.extraction.formulas
    second.plain_text = first.plain_text  # contradictory LaTeX still differs
    doc.chunks = [chunk]
    assert len(consolidate_knowledge(doc).formulas) == 2


def test_different_statement_metadata_stays_separate(course):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    doc.chunks[1].extraction.statements[0].topic = "Other topic"
    assert len(consolidate_knowledge(doc).statements) == 5


def test_first_write_and_verified_skip(course):
    first = run(course, write=True)
    assert first.counts["completed"] == 4
    files = {
        p: (p.read_bytes(), p.stat().st_mtime_ns) for p in course[2].glob("*.json")
    }
    assert len(files) == 12
    second = run(course, write=True)
    third = run(course)
    assert second.counts["skipped"] == third.counts["skipped"] == 4
    assert files == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
    for item in second.inputs:
        assert item.output_sha256 == hash_bytes(Path(item.output_path).read_bytes())


@pytest.mark.parametrize(
    "kind,status",
    [
        ("input_changed", "stale"),
        ("config_changed", "stale"),
        ("output_missing", "invalid"),
        ("output_json", "invalid"),
        ("output_schema", "invalid"),
        ("output_hash", "invalid"),
        ("cache_corrupt", "invalid"),
        ("cache_schema", "invalid"),
        ("marker_corrupt", "invalid"),
        ("marker_conflict", "invalid"),
        ("no_receipt", "invalid"),
    ],
)
def test_resume_rejects_unverified_artifacts(course, kind, status):
    report = run(course, write=True)
    target = Path(report.inputs[0].output_path)
    prepared = target.with_name(target.name + ".prepared.v1.json")
    marker = target.with_name(target.name + ".completed.v1.json")
    if kind == "input_changed":
        mutate(
            course[1][0], lambda v: v.update(language="de", transcript_provenance=None)
        )
    elif kind == "config_changed":
        result = process_course_knowledge(
            course[1], course[2], "changed-contract", input_root=course[0], write=True
        )
        assert result.counts["stale"] == 4
        return
    elif kind == "output_missing":
        target.rename(target.with_suffix(".saved"))
    elif kind in ("output_json", "cache_corrupt", "marker_corrupt"):
        {"output_json": target, "cache_corrupt": prepared, "marker_corrupt": marker}[
            kind
        ].write_text("{")
    elif kind in ("output_schema", "cache_schema"):
        (target if kind == "output_schema" else prepared).write_text("{}")
    elif kind == "output_hash":
        mutate(target, lambda v: v["statements"][0].update(text="Changed statement"))
    elif kind == "marker_conflict":
        mutate(marker, lambda v: v.update(output_sha256="0" * 64))
    else:
        prepared.rename(prepared.with_suffix(".saved"))
        marker.rename(marker.with_suffix(".saved"))
    before = {p: p.read_bytes() for p in course[2].iterdir()}
    result = run(course, write=True)
    assert result.inputs[0].status == status
    assert result.counts["skipped"] == 3
    assert before == {p: p.read_bytes() for p in course[2].iterdir()}


@pytest.mark.parametrize("where", ["before_output", "after_output"])
def test_interrupted_publication_recovery(course, monkeypatch, where):
    import src.tools_knowledge.consolidation_run as module

    real = module.atomic_json

    def interrupt(path, value, **kwargs):
        if (where == "before_output" and path.name.endswith("_deterministic.json")) or (
            where == "after_output" and path.name.endswith(".completed.v1.json")
        ):
            raise KeyboardInterrupt
        return real(path, value, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module, "atomic_json", interrupt)
        with pytest.raises(KeyboardInterrupt):
            run(course, write=True)
    pending = run(course)
    assert pending.inputs[0].status == "pending"
    assert pending.inputs[0].decision == "resume_prepared"
    assert run(course, write=True).counts["completed"] == 4
    assert run(course).counts["skipped"] == 4


@pytest.mark.parametrize(
    "defect",
    [
        "source",
        "course",
        "lecture",
        "segment",
        "chunk",
        "item",
        "interval",
        "confidence",
        "empty",
        "partial",
        "visual",
        "json",
        "missing",
        "duplicate_json",
    ],
)
def test_bad_input_does_not_stop_other_lectures(course, defect):
    path = course[1][0]

    def change(v):
        extraction = v["chunks"][0]["extraction"]
        item = extraction["statements"][0]
        if defect in ("source", "course", "lecture"):
            v[defect + "_id"] = None
        elif defect == "segment":
            item["segment_ids"] = []
        elif defect == "chunk":
            extraction["chunk_id"] = "foreign"
        elif defect == "item":
            extraction["statements"].append({**item, "text": "Conflicting same ID"})
        elif defect == "interval":
            item["end"] = -1
        elif defect == "confidence":
            item["llm_confidence"] = 2
        elif defect == "empty":
            item["text"] = " "
        elif defect == "partial":
            v["chunks"][0]["extraction"] = None
        elif defect == "visual":
            v["visual_candidates"] = [
                dict(
                    chunk_id="foreign",
                    segment_ids=[1],
                    start=1,
                    end=2,
                    reason="synthetic",
                )
            ]

    if defect == "missing":
        path.rename(path.with_suffix(".saved"))
    elif defect == "json":
        path.write_text("{")
    elif defect == "duplicate_json":
        path.write_text('{"source_id":"one","source_id":"two"}')
    else:
        mutate(path, change)
    report = run(course, write=True)
    assert report.inputs[0].status == "invalid"
    assert report.counts["completed"] == 3
    assert report.counts["errors"] >= 1
    if defect in ("segment", "chunk", "visual"):
        assert report.counts["missing_evidence_references"] >= 1


def test_missing_provenance_is_reported_without_inference(course):
    mutate(course[1][0], lambda v: v.update(transcript_provenance=None))
    result = run(course)
    assert result.inputs[0].status == "pending"
    assert "missing_provenance" in [f.code for f in result.inputs[0].findings]
    assert not course[2].exists()


def test_duplicate_chunk_and_item_id_conflicts_fail_core(course):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    doc.chunks[1].analysis.chunk_id = doc.chunks[0].analysis.chunk_id
    with pytest.raises(ValueError, match="identity_conflict"):
        consolidate_knowledge(doc)
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    item = doc.chunks[0].extraction.statements[0]
    doc.chunks[0].extraction.statements.append(
        item.model_copy(update={"segment_ids": [99]})
    )
    with pytest.raises(ValueError, match="identity_conflict"):
        consolidate_knowledge(doc)


def test_identical_repeated_chunk_deduplicates_evidence(course):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    doc.chunks.append(doc.chunks[0].model_copy(deep=True))
    result = consolidate_knowledge(doc)
    assert len(result.statements) == 4
    assert len(result.statements[0].evidence) == 2
    validate_output(doc, result)


def test_selection_is_by_declared_identity(course):
    report = run(
        course, lecture_ids=("lecture1",), course_id="synthetic-calculus", write=True
    )
    assert report.counts["inputs_selected"] == 2
    assert report.counts["completed"] == report.counts["skipped"] == 2
    assert all(i.decision == "not_selected" for i in report.inputs[:2])
    assert not list(course[2].glob("lecture0*.json"))


@pytest.mark.parametrize("collision", ["filename", "source"])
def test_identity_or_filename_collisions_do_not_overwrite(course, collision):
    root, paths, output = course
    if collision == "filename":
        directory = root / "other"
        directory.mkdir()
        path = directory / paths[0].name
        path.write_bytes(paths[1].read_bytes())
        paths.append(path)
    else:
        first = json.loads(paths[0].read_bytes())
        mutate(paths[1], lambda v: v.update(source_id=first["source_id"]))
    report = run(course, write=True)
    assert report.counts["invalid"] >= 2
    assert report.counts["conflicts"] >= 2


@pytest.mark.parametrize(
    "kind",
    [
        "outside",
        "input_symlink",
        "output_symlink",
        "ancestor_symlink",
        "output_artifact_symlink",
        "traversal",
    ],
)
def test_unsafe_paths(course, tmp_path, kind):
    root, paths, output = course
    if kind == "outside":
        root = tmp_path / "other-root"
    elif kind == "input_symlink":
        alias = root / "alias_know_extract.json"
        alias.symlink_to(paths[0])
        paths = [alias]
    elif kind == "output_symlink":
        real = tmp_path / "real"
        real.mkdir()
        output.symlink_to(real, target_is_directory=True)
    elif kind == "ancestor_symlink":
        real = tmp_path / "real"
        real.mkdir()
        alias = tmp_path / "alias"
        alias.symlink_to(real, target_is_directory=True)
        output = alias / "new"
    elif kind == "output_artifact_symlink":
        output.mkdir()
        filename = paths[0].name.replace("_know_extract", "_know_deterministic")
        (output / filename).symlink_to(paths[0])
    elif kind == "traversal":
        paths = [root / ".." / "inputs" / paths[0].name]
    if kind in ("output_symlink", "ancestor_symlink"):
        with pytest.raises(ValueError, match="Symlink"):
            process_course_knowledge(
                paths, output, "offline", input_root=root, write=True
            )
    else:
        result = process_course_knowledge(
            paths, output, "offline", input_root=root, write=True
        )
        assert result.counts["invalid"] >= 1


def test_publication_lock_conflict_is_explicit(course):
    from src.tools_knowledge.consolidation_run import publication_lock

    with publication_lock(course[2]):
        with pytest.raises(BlockingIOError):
            run(course, write=True)
    assert not list(course[2].glob("*.json"))


def test_legacy_output_readable_but_not_adopted(course):
    result = run(course)
    item = result.inputs[0]
    doc = TranscriptKnowledgeDocument.model_validate_json(
        Path(item.input_path).read_bytes()
    )
    output = Path(item.output_path)
    output.parent.mkdir()
    output.write_text(consolidate_knowledge(doc).model_dump_json())
    original = output.read_bytes()
    assert (
        ConsolidatedKnowledgeDocument.model_validate_json(original).source_id
        == doc.source_id
    )
    assert run(course, write=True).inputs[0].status == "invalid"
    assert output.read_bytes() == original


@pytest.mark.parametrize(
    "damage", ["metadata", "missing", "invented", "duplicate_ids", "changed"]
)
def test_output_validation(course, damage):
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    result = consolidate_knowledge(doc)
    if damage == "metadata":
        result.lecture_id = "other"
    elif damage == "missing":
        result.statements[0].evidence.clear()
    elif damage == "invented":
        result.formulas[0].evidence[0].chunk_id = "foreign"
    elif damage == "duplicate_ids":
        result.statements[1].statement_id = result.statements[0].statement_id
    else:
        result.statements[0].evidence[0].end += 1
    with pytest.raises(ValueError):
        validate_output(doc, result)


def test_cli_report_no_overwrite_and_exit_status(course, tmp_path, capsys):
    root, paths, output = course
    target = tmp_path / "report.json"
    args = [
        "--input-root",
        str(root),
        "--output-root",
        str(output),
        "--report",
        str(target),
    ]
    for path in paths:
        args += ["--input", str(path)]
    assert main(args) == 0
    report = RunReport.model_validate_json(target.read_bytes())
    assert report.counts["pending"] == 4
    assert "synthetic-calculus/lecture0" in capsys.readouterr().out
    original = target.read_bytes()
    with pytest.raises(SystemExit) as exc:
        main(args + ["--write"])
    assert exc.value.code == 2 and target.read_bytes() == original
    assert not output.exists()
    paths[0].write_text("{")
    args = args[: args.index("--report")] + sum(
        (["--input", str(p)] for p in paths), []
    )
    assert main(args) == 1


def test_empty_selection_is_explicit(course):
    report = run(course, lecture_ids=("absent",))
    assert report.counts["inputs_selected"] == 0
    assert report.counts["skipped"] == 4


def test_single_file_helper_is_read_only_and_exclusive(course, tmp_path):
    target = tmp_path / "single.json"
    result = process_knowledge_file(course[1][0], target, "offline")
    assert isinstance(result, ConsolidatedKnowledgeDocument) and not target.exists()
    assert process_knowledge_file(course[1][0], target, "offline", write=True) == result
    with pytest.raises(FileExistsError):
        process_knowledge_file(course[1][0], target, "offline", write=True)


def test_import_in_clean_subprocess_without_sdk_or_settings(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = r"""
import importlib, socket, sys
sys.path.insert(0, sys.argv[1])
class Block:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'marvin','openai','pydantic_ai','numpy'} or fullname in {'src.core.config','src.core.memory'}:
            raise AssertionError('Forbidden import: '+fullname)
sys.meta_path.insert(0, Block())
def forbidden(*a, **kw): raise AssertionError('Network forbidden')
socket.create_connection=forbidden; socket.getaddrinfo=forbidden
socket.socket.connect=forbidden; socket.socket.connect_ex=forbidden
runner=importlib.import_module('src.run_knowledge_consolidation')
from pathlib import Path
report=runner.process_course_knowledge(list(Path(sys.argv[2]).glob('*.json')),Path(sys.argv[3]),'offline',input_root=Path(sys.argv[2]))
assert report.counts['pending']==4
print('offline passed')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(root),
            str(FIXTURES.absolute()),
            str(tmp_path / "out"),
        ],
        cwd=tmp_path,
        env={},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "offline passed" in result.stdout
    assert not list(tmp_path.iterdir())


@pytest.fixture
def semantic_functions():
    # Same isolation convention as test_knowledge_transcript_provenance: compile
    # real functions and replace only SDK/cache boundaries, never their logic.
    import __future__

    import ast
    from types import SimpleNamespace

    from src.model_knowledge import data_knowledge as models

    path = (
        Path(__file__).resolve().parents[1]
        / "src/tools_knowledge/semantic_knowledge.py"
    )
    functions = [
        node
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.FunctionDef)
    ]
    namespace = {
        **vars(models),
        "json": json,
        "app_session": SimpleNamespace(logger=None),
        "marvin": SimpleNamespace(Agent=lambda **kw: SimpleNamespace()),
        "SEMANTIC_CONSOLIDATION_PROMPT": "synthetic-test-only",
        "ENTITY_EXTRACTION_PROMPT": "synthetic-test-only",
    }
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            str(path),
            "exec",
            flags=__future__.annotations.compiler_flag,
        ),
        namespace,
    )
    return namespace


def fake_semantic(namespace):
    from src.model_knowledge.data_knowledge import SemanticBatchLLMResult

    namespace["consolidate_semantic_batch"] = lambda **kwargs: SemanticBatchLLMResult()
    namespace["extract_entity_batch"] = lambda **kwargs: object()
    namespace["merge_lecture_entities"] = lambda results: []
    return namespace["consolidate_semantic_knowledge"]


def test_semantic_boundary_is_explicit_and_resume_does_not_call_stage(
    course, semantic_functions
):
    stage = fake_semantic(semantic_functions)
    calls = []

    def provider(**kwargs):
        calls.append(kwargs["document"].source_id)
        return stage(**kwargs)

    result = run(
        course, semantic_stage=provider, semantic_contract="synthetic-fallback-v1"
    )
    assert result.counts["pending"] == 4 and calls == []  # dry run never invokes it
    result = run(
        course,
        write=True,
        semantic_stage=provider,
        semantic_contract="synthetic-fallback-v1",
    )
    assert result.counts["completed"] == 4 and len(calls) == 4
    assert all(i.output_path.endswith("_know_consol.json") for i in result.inputs)
    result = run(
        course,
        write=True,
        semantic_stage=provider,
        semantic_contract="synthetic-fallback-v1",
    )
    assert result.counts["skipped"] == 4 and len(calls) == 4
    result = run(
        course,
        write=True,
        semantic_stage=provider,
        semantic_contract="synthetic-fallback-v2",
    )
    assert result.counts["stale"] == 4 and len(calls) == 4
    with pytest.raises(ValueError, match="explicit callable"):
        run(course, semantic_stage=provider)


def test_one_stage_failure_continues_course(course, semantic_functions):
    stage = fake_semantic(semantic_functions)

    def provider(**kwargs):
        if kwargs["document"].source_id == "synthetic-0-captions":
            raise RuntimeError("Synthetic stage failure")
        return stage(**kwargs)

    result = run(
        course, write=True, semantic_stage=provider, semantic_contract="test-v1"
    )
    assert result.counts["failed"] == 1 and result.counts["completed"] == 3
    assert result.inputs[0].decision == "stage_failed"


@pytest.mark.parametrize(
    "damage", ["source_ids", "evidence_mapping", "formulas", "duplicate_evidence"]
)
def test_semantic_stage_cannot_invent_or_double_count_references(
    course, semantic_functions, damage
):
    stage = fake_semantic(semantic_functions)

    def provider(**kwargs):
        result = stage(**kwargs)
        if damage == "source_ids":
            result.statements[0].source_statement_ids = ["foreign"]
        elif damage == "evidence_mapping":
            left, right = result.statements[:2]
            left.source_statement_ids, right.source_statement_ids = (
                right.source_statement_ids,
                left.source_statement_ids,
            )
        elif damage == "formulas":
            result.formulas[0].plain_text = "invented"
        else:
            result.statements[1].evidence.append(
                result.statements[0].evidence[0].model_copy()
            )
        return result

    result = run(
        course, write=True, semantic_stage=provider, semantic_contract="test-v1"
    )
    assert result.counts["invalid"] == 4
    assert not list(course[2].glob("*.json"))


def test_semantic_exact_merges_keep_operators_and_review_metadata(
    course, semantic_functions
):
    stage = fake_semantic(semantic_functions)
    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    deterministic = consolidate_knowledge(doc)
    result = stage(deterministic, model_name="offline")
    assert len(result.statements) == 4  # old punctuation-stripping merged +/-
    first = result.statements[0]
    duplicate = first.model_copy(deep=True)
    duplicate.needs_review = True
    duplicate.review_reason = "Synthetic review flag"
    merged = semantic_functions["merge_exact_canonical_statements"]([first, duplicate])
    assert len(merged) == 2
    duplicate = first.model_copy(deep=True)
    duplicate.evidence[0].segment_ids = [999]
    merged = semantic_functions["merge_statement_evidence_from_canonical"](
        [first, duplicate]
    )
    assert any(e.segment_ids == [999] for e in merged)
    assert any(e.segment_ids == [0] for e in merged)


@pytest.mark.parametrize("cached", [False, True])
def test_semantic_validator_rejects_reused_and_invented_ids(
    course, semantic_functions, cached
):
    from types import SimpleNamespace

    doc = TranscriptKnowledgeDocument.model_validate_json(course[1][0].read_bytes())
    statements = consolidate_knowledge(doc).statements
    invalid = SimpleNamespace(
        canonical_statements=[
            SimpleNamespace(source_statement_ids=["KS0001", "KS0001"])
        ],
        discarded_statements=[],
    )
    if cached:
        semantic_functions.update(
            hash_text=lambda value: fingerprint(value),
            make_cache_key=lambda **kwargs: "synthetic",
            load_from_cache=lambda **kwargs: invalid,
        )
        with pytest.raises(ValueError, match="more than once"):
            semantic_functions["consolidate_semantic_batch"](
                statements, batch_id="test", model_name="offline", agent=object()
            )
    else:
        validate = semantic_functions["validate_semantic_batch_result"]
        with pytest.raises(ValueError, match="more than once"):
            validate(statements, invalid)
        invalid.canonical_statements[0].source_statement_ids = ["foreign"]
        with pytest.raises(ValueError, match="invented"):
            validate(statements, invalid)


def test_changed_input_during_stage_is_not_published(course, semantic_functions):
    stage = fake_semantic(semantic_functions)

    def provider(**kwargs):
        mutate(
            course[1][0],
            lambda value: value.update(language="de", transcript_provenance=None),
        )
        return stage(**kwargs)

    result = run(
        course, write=True, semantic_stage=provider, semantic_contract="test-v1"
    )
    assert result.inputs[0].status == "invalid"
    assert "changed during" in result.inputs[0].findings[-1].message
    assert not list(course[2].glob("lecture0_captions*.json"))


def test_implicit_provenance_timestamp_cannot_make_replay_nondeterministic(course):
    mutate(course[1][0], lambda v: v["transcript_provenance"].pop("acquired_at"))
    result = run(course)
    assert result.inputs[0].status == "invalid"
    assert "acquired_at" in result.inputs[0].findings[-1].message


def test_receipt_duplicate_keys_and_nan_are_invalid(tmp_path):
    path = tmp_path / "bad.json"
    for value in ('{"phase":"prepared","phase":"completed"}', '{"value":NaN}'):
        path.write_text(value)
        with pytest.raises(ValueError):
            read_json(path)


def test_checked_in_report_matches_executed_synthetic_fixture(course):
    from src.tools_knowledge.consolidation_run import report_for

    report = run(course)
    entries = [
        i.model_copy(
            update=dict(
                input_path="tests/fixtures/consolidation/synthetic_course/"
                + Path(i.input_path).name,
                output_path="example-output/" + Path(i.output_path).name,
            )
        )
        for i in report.inputs
    ]
    portable = report_for(entries, report.config, False)
    path = (
        Path(__file__).resolve().parents[1] / "docs/examples/consolidation-run.v1.json"
    )
    assert path.read_bytes() == encoded(portable.model_dump(mode="json"))


def test_wrong_input_name_does_not_publish(course):
    root, paths, output = course
    invalid = root / "wrong-name.json"
    invalid.write_bytes(paths[0].read_bytes())
    result = run((root, [invalid], output), write=True)
    assert result.inputs[0].status == "invalid"
    assert not list(output.glob("*.json"))
