"""Offline notation/algebra evaluation. No predictions become independent gold."""

import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.evaluate_math_formulas import main
from src.model_evaluation.math_evaluation import (
    FormulaCase,
    FormulaDataset,
    FormulaEvaluationReport,
)
from src.tools_evaluation.evaluate_math import (
    aggregate,
    evaluate_case,
    evaluate_dataset,
    load_cases,
)
from src.tools_evaluation.math_equivalence import check_equivalence
from src.tools_evaluation.math_predictions import bind_visual_prediction
from src.tools_evaluation.math_reports import markdown_report, publish_report
from src.tools_evaluation.math_syntax import (
    FormulaSyntaxError,
    normalize_formula,
    parse_formula,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/math_evaluation/formula_cases.v1.json"
HAS_SYMPY = importlib.util.find_spec("sympy") is not None


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("No network in mathematical evaluation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def case(reference="x+1", prediction="x+1", **updates):
    data = dict(
        schema_version=1,
        case_id="own-case",
        source_document_id="synthetic:source",
        section="section-1",
        source_reference="own independent source sheet#1",
        gold_origin="synthetic",
        reference_status="confirmed",
        reference_formula=reference,
        predicted_formula=prediction,
        formula_format="latex",
    )
    data.update(updates)
    return FormulaCase.model_validate_json(json.dumps(data), strict=True)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.pop("case_id"),
        lambda d: d.pop("schema_version"),
        lambda d: d.update(schema_version=2),
        lambda d: d.update(source_reference=""),
        lambda d: d.update(source_document_id=""),
        lambda d: d.update(section=None),
        lambda d: d.update(page=True),
        lambda d: d.update(page=0),
        lambda d: d.update(reference_formula=None),
        lambda d: d.update(reference_status="absent"),
        lambda d: d.update(predicted_formula="   "),
        lambda d: d.update(prediction_sha256="0" * 64),
        lambda d: d.update(reference_parts=["x", "x"]),
        lambda d: d.update(extra_field=1),
    ],
)
def test_invalid_evaluation_data(change):
    d = case().model_dump(mode="json")
    change(d)
    with pytest.raises(ValueError):
        FormulaCase.model_validate_json(json.dumps(d), strict=True)


def test_valid_page_or_section_and_roundtrip():
    c = case(section=None, page=2)
    assert FormulaCase.model_validate_json(c.model_dump_json()) == c
    result = evaluate_case(c)
    assert result.evaluation_status == "correct"
    assert result.case.page == 2 and result.case.source_reference


@pytest.mark.parametrize(
    "a,b",
    [
        (" $ x + 1 $ ", "x+1"),
        ("x − 1", "x-1"),
        ("α + β", r"\alpha+\beta"),
        ("x²", "x^{2}"),
        ("x₁", "x_{1}"),
        (r"\( x+1 \)", "x+1"),
        ("x\t+\ny", "x+y"),
        ("x×y", r"x\times y"),
    ],
)
def test_safe_normalization(a, b):
    assert normalize_formula(a) == normalize_formula(b)


@pytest.mark.parametrize(
    "a,b",
    [
        ("x+1", "x-1"),
        ("x^2", "x^3"),
        ("x_1", "x_2"),
        ("x²", "x2"),
        ("X", "x"),
        (r"\alpha x", r"\alphax"),
        ("1 2", "12"),
        ("a/b", "ab"),
    ],
)
def test_normalization_preserves_mathematical_distinctions(a, b):
    assert normalize_formula(a) != normalize_formula(b)


@pytest.mark.parametrize(
    "a,b",
    [
        (r"\frac{x+1}{2}", "(x+1)/2"),
        ("x^{2}", "x^2"),
        ("x_{1}", "x_1"),
        (r"\left(x+1\right)", "(x+1)"),
        (r"\sqrt{x+1}", r"\sqrt{x+1}"),
        (r"\sum_{i=1}^{n}i", r"\sum_{i=1}^n i"),
        (r"\int_{0}^{1}x^2\,dx", r"\int_0^1 x^2 dx"),
        (r"\vec{a}+\vec{b}", r"\vec{a} + \vec{b}"),
    ],
)
def test_supported_structures(a, b):
    assert parse_formula(a)[1] == parse_formula(b)[1]


@pytest.mark.parametrize(
    "a,b",
    [
        ("a+b", "a-b"),
        ("x^2", "x^3"),
        ("x_1", "x_2"),
        (r"\frac{x}{y}", r"\frac{y}{x}"),
        ("(a+b)c", "a+bc"),
        (r"\sum_{i=1}^{n}i", r"\sum_{i=2}^{n}i"),
        (r"\int_0^1 x dx", r"\int_0^2 x dx"),
        (r"\sqrt{x+1}", r"\sqrt{x-1}"),
    ],
)
def test_structural_differences(a, b):
    assert parse_formula(a)[1] != parse_formula(b)[1]


@pytest.mark.parametrize(
    "text",
    [
        r"\sin{x}",
        r"\begin{matrix}1&0\end{matrix}",
        r"\unknown{x}",
        "f(x)",
        "sin(x)",
        "x^123",
        "x^^2",
        r"\frac{x}{",
        "a=b=c",
        "x+",
        "x\x08+1",
        "x\u200b+1",
        "1.5+x",
        "(" * 30 + "x" + ")" * 30,
        "+".join(["x"] * 300),
    ],
)
def test_unsupported_or_malformed_is_explicit(text):
    with pytest.raises(FormulaSyntaxError):
        parse_formula(text)
    result = evaluate_case(case(text, text))
    assert result.evaluation_status == "undetermined"
    assert (
        "not_evaluable" in result.error_categories
        or "format_error" in result.error_categories
    )


def test_unsupported_exact_match_is_not_math_success():
    r = evaluate_case(case(r"\sin{x}", r"\sin{x}"))
    assert r.exact_match and r.normalized_match and r.structural_match is None
    assert r.equivalence.status == "undetermined"


@pytest.mark.parametrize(
    "reference,prediction,status,category",
    [
        ("x", None, "missing_formula", "missing_formula"),
        (None, "x", "extra_formula", "extra_formula"),
        (None, None, "correct", None),
    ],
)
def test_absence_is_not_an_empty_exact_match(reference, prediction, status, category):
    r = evaluate_case(
        case(
            reference,
            prediction,
            reference_status="absent" if reference is None else "confirmed",
        )
    )
    assert r.evaluation_status == status and r.exact_match is None
    if category:
        assert category in r.error_categories


def test_ambiguous_gold_and_ambiguous_prediction_abstain():
    for updates in ({"reference_status": "ambiguous"}, {"prediction_ambiguous": True}):
        r = evaluate_case(case(**updates))
        assert r.evaluation_status == "undetermined"
        assert r.error_categories == ("ambiguous_source", "not_evaluable")


def test_partial_requires_an_independent_proper_gold_component():
    c = case(r"\frac{x+1}{2}", "x+1", reference_parts=["x+1"])
    r = evaluate_case(c)
    assert r.evaluation_status == "partially_correct"
    assert "fraction_error" in r.error_categories
    with pytest.raises(ValueError, match="proper reference"):
        evaluate_case(case("x+1", "x", reference_parts=["y"]))
    assert evaluate_case(case("x+1", "x")).evaluation_status == "undetermined"


@pytest.mark.parametrize(
    "reference,prediction,category",
    [
        ("x+1", "y+1", "symbol_error"),
        ("x+1", "x-1", "operator_error"),
        ("x^2", "x^3", "exponent_error"),
        ("x_1", "x_2", "subscript_error"),
        (r"\frac{x+1}{2}", r"\frac{x-1}{2}", "fraction_error"),
    ],
)
def test_notation_error_categories_do_not_imply_math_false(
    reference, prediction, category
):
    r = evaluate_case(case(reference, prediction))
    assert category in r.error_categories and r.evaluation_status == "undetermined"


@pytest.mark.skipif(
    not HAS_SYMPY, reason="Optional installed SymPy backend unavailable"
)
@pytest.mark.parametrize(
    "reference,prediction,status",
    [
        ("(a+b)^2", "a^2+2ab+b^2", "equivalent"),
        ("2x+4=0", "x=-2", "equivalent"),
        ("x^2-5x+6=0", "(x-2)(x-3)=0", "equivalent"),
        (r"\frac{x+x}{2}", "x", "equivalent"),
        (r"\sqrt{16}", "4", "equivalent"),
        ("x^2", "x^3", "not_equivalent"),
        ("x+1", "x-1", "not_equivalent"),
        ("x+1=2", "x-1=2", "not_equivalent"),
        ("x_1", "x_2", "not_equivalent"),
        (r"\sqrt{x^2}", "x", "undetermined"),
        ("x/x", "1", "undetermined"),
        ("1/(x-x+1)", "1", "undetermined"),
        ("x^2=0", "x=0", "undetermined"),
        (r"\sum_{i=1}^n i", "n", "undetermined"),
        ("x^9", "x*x", "undetermined"),
    ],
)
def test_isolated_symbolic_decisions(reference, prediction, status):
    a, b = parse_formula(reference)[1], parse_formula(prediction)[1]
    r = check_equivalence(a, b, backend="sympy", timeout=10)
    assert r.status == status, r
    assert r.backend == "sympy"


def test_symbolic_backend_is_optional_and_explicit():
    a, b = parse_formula("x+x")[1], parse_formula("2x")[1]
    assert check_equivalence(a, b).reason == "symbolic_check_not_requested"
    with pytest.raises(ValueError):
        check_equivalence(a, b, backend="unsafe")


def test_sympy_absence_has_no_fallback_parser(monkeypatch):
    import builtins

    from src.tools_evaluation.sympy_worker import compare_trees

    original = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name == "sympy":
            raise ImportError("deliberately unavailable")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(ImportError):
        compare_trees(
            parse_formula("x+x")[1].payload(), parse_formula("2x")[1].payload()
        )


def test_timeout_kills_and_reaps_worker(monkeypatch):
    from src.tools_evaluation import math_equivalence as module

    events = []

    class Fake:
        pid = 123

        def communicate(self, *a, **kw):
            raise subprocess.TimeoutExpired("bounded-worker", kw["timeout"])

        def wait(self):
            events.append("reaped")

    monkeypatch.setattr(module.subprocess, "Popen", lambda *a, **kw: Fake())
    monkeypatch.setattr(
        module.os, "killpg", lambda pid, signal: events.append(("killed", pid))
    )
    r = check_equivalence(parse_formula("x")[1], parse_formula("y")[1], backend="sympy")
    assert r.reason == "worker_timeout" and events == [("killed", 123), "reaped"]


def test_real_wall_timeout():
    r = check_equivalence(
        parse_formula("x")[1], parse_formula("y")[1], backend="sympy", timeout=0.001
    )
    assert r.status == "undetermined" and r.reason == "worker_timeout"


def test_problematic_inputs_cannot_execute(tmp_path):
    sentinel = tmp_path / "executed"
    for text in (
        f"__import__('pathlib').Path('{sentinel}').touch()",
        'open("/tmp/forbidden","w")',
        r"\input{/etc/passwd}",
        r"\write18{touch owned}",
        "x.__class__",
        "lambda:x",
    ):
        assert (
            evaluate_case(
                case("x", text), equivalence_backend="sympy"
            ).evaluation_status
            == "undetermined"
        )
    assert not sentinel.exists()


def test_metrics_denominators_and_separate_origins():
    rows = [
        evaluate_case(case()),
        evaluate_case(case("x", None)),
        evaluate_case(case(r"\unknown{x}", r"\unknown{x}")),
    ]
    m = aggregate(rows)
    assert m.case_count == 3 and m.evaluable_count == 2 and m.paired_count == 2
    assert (
        m.exact_match_rate == 1
        and m.structural_matches == 1
        and m.undetermined_count == 1
    )
    assert aggregate([]).exact_match_rate is None
    report = evaluate_dataset(DATA)
    assert (
        report.metrics["real"].case_count == 0
        and report.metrics["real"].normalized_match_rate is None
    )


def test_dataset_gold_catalog_and_repeatability():
    dataset, _ = load_cases(DATA)
    assert len(dataset.cases) == 42
    catalog = json.loads((DATA.parent / "gold_references.v1.json").read_bytes())
    for c in dataset.cases:
        gold = catalog["references"][c.section]
        assert c.reference_formula == gold["reference_formula"]
        assert c.reference_status == gold["reference_status"]
        assert (
            c.source_reference.endswith("/" + c.section)
            and c.gold_origin == "synthetic"
        )
    a = evaluate_dataset(DATA)
    assert a.model_dump_json() == evaluate_dataset(DATA).model_dump_json()
    assert FormulaEvaluationReport.model_validate_json(a.model_dump_json()) == a
    assert markdown_report(a) == markdown_report(evaluate_dataset(DATA))


def test_jsonl_selection_and_invalid_input(tmp_path):
    p = tmp_path / "cases.jsonl"
    first = case()
    second = case(case_id="second", gold_origin="real")
    p.write_text(first.model_dump_json() + "\n" + second.model_dump_json() + "\n")
    report = evaluate_dataset(p, case_ids=["second"])
    assert len(report.results) == 1 and report.metrics["real"].case_count == 1
    assert report.metrics["synthetic"].case_count == 0
    for selected in (["missing"], ["second", "second"]):
        with pytest.raises(ValueError):
            evaluate_dataset(p, case_ids=selected)
    p.write_text('{"schema_version":1,"schema_version":1}\n')
    with pytest.raises(ValueError, match="line 1"):
        load_cases(p)
    with pytest.raises(ValueError):
        FormulaDataset(schema_version=1, cases=(first, first))


@pytest.mark.parametrize(
    "bad",
    [
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b'{"schema_version":NaN}',
        b'{"schema_version":1,"schema_version":1}',
    ],
)
def test_invalid_files_are_cli_errors(tmp_path, bad, capsys):
    p = tmp_path / "bad.json"
    p.write_bytes(bad)
    assert main(["--cases", str(p)]) == 2
    assert "Evaluation failed" in capsys.readouterr().err


def test_reports_hashes_no_overwrite_and_cli(tmp_path, capsys):
    output = tmp_path / "new-report"
    report = evaluate_dataset(DATA, case_ids=["M01", "M33"])
    manifest = publish_report(report, output)
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    before = {p: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        publish_report(report, output)
    assert before == {p: p.read_bytes() for p in output.iterdir()}
    empty = tmp_path / "existing-empty"
    empty.mkdir()
    with pytest.raises(FileExistsError):
        publish_report(report, empty)
    assert main(["--cases", str(DATA), "--case-id", "M01"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["results"][0]["case"]["case_id"] == "M01"
    assert "Cases requiring review" in captured.err
    assert main(["--cases", str(DATA), "--case-id", "M33", "--fail-on-failures"]) == 1
    assert main(["--cases", str(DATA), "--output", str(output)]) == 2


def test_output_symlinks_are_refused(tmp_path):
    directory = tmp_path / "existing"
    directory.mkdir()
    link = tmp_path / "link"
    link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        publish_report(evaluate_dataset(DATA, case_ids=["M01"]), link / "report")
    assert not list(directory.iterdir())


def visual_file(path):
    from src.model_knowledge.data_knowledge import (
        VisualAnalysisDocument,
        VisualExpression,
        VisualKnowledgeResult,
    )

    expr = VisualExpression(
        expression_id="e1",
        visual_labels=None,
        visual_plain_text="x+1",
        visual_latex="x+1",
        section_id="section-1",
        batch_id="b1",
        start=1,
        end=2,
    )
    document = VisualAnalysisDocument(
        source_id="synthetic:source",
        api_results=[
            VisualKnowledgeResult(
                batch_id="b1",
                section_id="section-1",
                start=1,
                end=2,
                expressions=[expr],
            )
        ],
    )
    path.write_text(document.model_dump_json())
    return document


def test_visual_prediction_binding_preserves_independent_gold(tmp_path):
    path = tmp_path / "visual.json"
    document = visual_file(path)
    gold = case("x-1", None)
    before = path.read_bytes()
    bound = bind_visual_prediction(gold, path, batch_id="b1", expression_id="e1")
    assert bound.reference_formula == "x-1" and bound.predicted_formula == "x+1"
    assert (
        bound.source_reference == gold.source_reference
        and bound.prediction_sha256 == hashlib.sha256(before).hexdigest()
    )
    assert (
        path.read_bytes() == before
        and document.api_results[0].expressions[0].visual_latex == "x+1"
    )
    with pytest.raises(ValueError):
        bind_visual_prediction(
            case(source_document_id="foreign"), path, batch_id="b1", expression_id="e1"
        )
    with pytest.raises(ValueError):
        bind_visual_prediction(
            case(section=None, page=1), path, batch_id="b1", expression_id="e1"
        )
    with pytest.raises(ValueError):
        bind_visual_prediction(gold, path, batch_id="b1", expression_id="missing")
    path.write_text(json.dumps({"results": []}))
    with pytest.raises(ValueError, match="legacy"):
        bind_visual_prediction(gold, path, batch_id="b1", expression_id="e1")


def test_cli_import_has_no_sdks_settings_or_sympy(tmp_path):
    code = """import importlib.abc,sys,runpy,socket
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0] in {'sympy','openai','marvin','pydantic_ai','docling','torch','pymupdf','bs4','pydantic_settings'}: raise AssertionError(name)
def forbidden(*a,**kw): raise AssertionError('network forbidden')
socket.socket.connect=forbidden
socket.getaddrinfo=forbidden
sys.meta_path.insert(0,Guard())
sys.argv=['evaluate_math_formulas','--cases',sys.argv[1],'--case-id','M01']
runpy.run_module('scripts.evaluate_math_formulas',run_name='__main__')
"""
    import os

    result = subprocess.run(
        [sys.executable, "-c", code, str(DATA)],
        cwd=ROOT,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(
    not HAS_SYMPY, reason="Optional installed SymPy backend unavailable"
)
def test_full_gold_set_has_independently_expected_outcomes():
    expected = [
        "correct",
        "correct",
        "correct",
        "incorrect",
        "correct",
        "incorrect",
        "correct",
        "correct",
        "incorrect",
        "correct",
        "incorrect",
        "correct",
        "incorrect",
        "correct",
        "undetermined",
        "incorrect",
        "incorrect",
        "correct",
        "undetermined",
        "correct",
        "undetermined",
        "correct",
        "undetermined",
        "correct",
        "undetermined",
        "correct",
        "incorrect",
        "correct",
        "incorrect",
        "correct",
        "correct",
        "extra_formula",
        "missing_formula",
        "undetermined",
        "undetermined",
        "undetermined",
        "undetermined",
        "partially_correct",
        "partially_correct",
        "incorrect",
        "undetermined",
        "undetermined",
    ]
    report = evaluate_dataset(DATA, equivalence_backend="sympy")
    assert [r.evaluation_status for r in report.results] == expected
    assert report.metrics["synthetic"].case_count == 42
    assert report.metrics["synthetic"].evaluable_count == 31
    assert report.metrics["synthetic"].symbolic_equivalent_count == 4
    assert report.metrics["real"].case_count == 0
    assert set(report.metrics["synthetic"].error_frequencies) == {
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
    }


@pytest.mark.skipif(
    not HAS_SYMPY, reason="Optional installed SymPy backend unavailable"
)
def test_known_constants_do_not_become_arbitrary_equation_variables():
    r = check_equivalence(
        parse_formula(r"\pi=0")[1], parse_formula("1=0")[1], backend="sympy", timeout=10
    )
    assert r.status == "undetermined"
    assert r.reason == "named_constant_outside_rational_polynomial_subset"


def test_unavailable_symbolic_worker_is_an_explicit_unknown(monkeypatch):
    from src.tools_evaluation import math_equivalence as module

    class Fake:
        returncode = 0

        def __init__(self, stdout):
            self.stdout = stdout

        def communicate(self, *args, **kwargs):
            self.stdout.write(
                b'{"status":"undetermined","reason":"sympy_unavailable","backend_version":null}'
            )

    monkeypatch.setattr(
        module.subprocess, "Popen", lambda *args, **kwargs: Fake(kwargs["stdout"])
    )
    r = check_equivalence(
        parse_formula("x+x")[1], parse_formula("2x")[1], backend="sympy"
    )
    assert r.status == "undetermined" and r.reason == "sympy_unavailable"


def test_worker_sets_limits_before_symbolic_work(monkeypatch, capsys):
    import io
    import resource
    from types import SimpleNamespace

    from src.tools_evaluation import sympy_worker as module

    calls = []
    monkeypatch.setattr(
        resource, "setrlimit", lambda kind, limits: calls.append((kind, limits))
    )
    monkeypatch.setattr(
        module.sys,
        "stdin",
        SimpleNamespace(buffer=io.BytesIO(b'{"left":[],"right":[]}')),
    )

    def comparison(*args):
        assert len(calls) == 3
        return "undetermined", "test_limits", None

    monkeypatch.setattr(module, "compare_trees", comparison)
    module.main()
    assert json.loads(capsys.readouterr().out)["reason"] == "test_limits"
    assert calls == [
        (resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024)),
        (resource.RLIMIT_CPU, (2, 3)),
        (resource.RLIMIT_FSIZE, (32768, 32768)),
    ]


def test_invalid_partial_rubric_is_rejected_even_without_prediction(tmp_path):
    invalid = case("x+1", None, reference_parts=["y"])
    with pytest.raises(ValueError, match="proper reference"):
        evaluate_case(invalid)
    p = tmp_path / "bad-gold.json"
    p.write_text(
        json.dumps({"schema_version": 1, "cases": [invalid.model_dump(mode="json")]})
    )
    with pytest.raises(ValueError, match="proper reference"):
        load_cases(p)


def test_report_manifest_is_completion_marker(tmp_path, monkeypatch):
    from src.tools_evaluation import math_reports as module

    output = tmp_path / "interrupted"
    original = module.publish_bytes

    def fail_summary(path, contents):
        if path.name == "summary.md":
            raise OSError("simulated publication interruption")
        original(path, contents)

    monkeypatch.setattr(module, "publish_bytes", fail_summary)
    with pytest.raises(OSError, match="interruption"):
        publish_report(evaluate_dataset(DATA, case_ids=["M01"]), output)
    assert (output / "report.json").exists() and not (output / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        publish_report(evaluate_dataset(DATA, case_ids=["M01"]), output)


@pytest.mark.parametrize(
    "formula",
    [r"\left(x+1)", r"(x+1\right)", r"\left[x+1\right)", r"\frac{x\right}{2}"],
)
def test_invalid_sized_delimiters_are_not_normalized_into_valid_math(formula):
    result = evaluate_case(case(formula, formula))
    assert result.evaluation_status == "undetermined"
    assert "format_error" in result.error_categories


@pytest.mark.parametrize("reader", ["dataset", "visual"])
def test_input_byte_limit_precedes_parsing(tmp_path, reader):
    path = tmp_path / "oversized.json"
    with path.open("wb") as stream:
        stream.seek(8 * 1024 * 1024)
        stream.write(b"x")
    with pytest.raises(ValueError, match="exceeds 8 MiB"):
        if reader == "dataset":
            load_cases(path)
        else:
            bind_visual_prediction(case(), path, batch_id="b1", expression_id="e1")


@pytest.mark.parametrize(
    "formula", [r"\sum_{i=1}^n i=a=b", r"\sum_{i=1}^n i+(a=b)", r"\frac{x=1}{2}"]
)
def test_bound_annotations_do_not_license_nested_or_chained_equalities(formula):
    result = evaluate_case(case(formula, formula))
    assert result.evaluation_status == "undetermined"
    assert "not_evaluable" in result.error_categories


@pytest.mark.parametrize("backend", ["none", "sympy"])
def test_explicit_vector_cross_and_dot_products_are_never_scalar_aliases(backend):
    result = evaluate_case(
        case(r"\vec{a}\times\vec{b}", r"\vec{a}\cdot\vec{b}"),
        equivalence_backend=backend,
    )
    assert result.structural_match is False
    assert result.equivalence.status == "undetermined"
    assert result.evaluation_status == "undetermined"
    assert "operator_error" in result.error_categories
