"""Real synthetic PDF -> legacy word cleanup -> real typed JSON boundary.

Only the two real method bodies are loaded via AST. Missing returns, AppSession,
NumPy and tokenizer dependencies prevent a full Legacy extractor import here.
No substitute PDF SDK, tokenizer, enricher or Result implementation is supplied.
This is explicitly a partial parsing path, not DIY/lecture end-to-end coverage.
"""

import ast
import hashlib
import re
import unicodedata
from types import SimpleNamespace

import pytest
from pydantic import TypeAdapter

from src.model_parsing.base_classes_parsing import Word, WordMeta
from tests.parsing_config_support import ROOT

pymupdf = pytest.importorskip(
    "pymupdf", reason="Synthetic legacy PDF boundary needs test-offline / PyMuPDF"
)


def methods(path, cls, names, **namespace):
    tree = ast.parse((ROOT / path).read_text())
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    nodes = [
        n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name in names
    ]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


@pytest.mark.parametrize(
    "text", ["Synthetic legacy PDF", "Second page tokens", "123 numeric words"]
)
def test_synthetic_pdf_legacy_words_preserve_text_geometry_and_source(tmp_path, text):
    path = tmp_path / "synthetic.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), text)
        pdf.new_page().insert_text((72, 72), "Unselected page")
        pdf.save(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    cleanup = methods(
        "src/model_parsing/base_extractor.py",
        "BaseExtractor",
        ["_clean_word_token"],
        re=re,
        unicodedata=unicodedata,
    )
    boundary = methods(
        "src/model_parsing/pdf_extractor.py",
        "PDFCleanExtractor",
        ["_clean_words_from_words"],
        Word=Word,
        WordMeta=WordMeta,
    )
    context = SimpleNamespace(
        _clean_word_token=lambda value: cleanup._clean_word_token(None, value)
    )
    with pymupdf.open(path) as pdf:
        original = pdf[0].get_text("words")
        words = boundary._clean_words_from_words(context, original)
    assert [w.text for w in words] == text.split()
    assert [
        (w.meta.x_start, w.meta.y_start, w.meta.x_end, w.meta.y_end) for w in words
    ] == [w[:4] for w in original]
    adapter = TypeAdapter(list[Word])
    assert adapter.validate_json(adapter.dump_json(words)) == words
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert {p.name for p in tmp_path.iterdir()} == {"synthetic.pdf"}
