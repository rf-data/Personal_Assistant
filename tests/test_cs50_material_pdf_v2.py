"""Conservative PDF source classification; no execution, models or network."""

import hashlib

import pymupdf
import pytest

from src.model_materials.materials import (
    ArtifactReceipt,
    NormalizedDocument,
    ParserConfig,
)
from src.tools_lecture.execute_cs50 import ExecutionConflict, digest
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.parse_pdf import parse_pdf
from src.tools_materials.pdf_worker import classify_text
from src.tools_materials.processing import MaterialProcessor, parser_for
from tests.test_cs50_material_download import binding


def classify(text, mono=True):
    return classify_text(
        text,
        [
            dict(
                text=text,
                font="Consolas" if mono else "Helvetica",
                flags=8 if mono else 0,
                size=12,
            )
        ],
        12,
    )


@pytest.mark.parametrize(
    "text",
    [
        "print(x=1)",
        'name = input("Name: ")',
        "def hello():",
        'def hello():\n    name = input("Name: ")\n    print(name)',
        '# Comment\nname = "test"\nprint(name)',
        'print("∑x = ∫f(x)")',
    ],
)
@pytest.mark.parametrize("mono", [True, False])
def test_python_signals_are_not_overwritten_by_math(text, mono):
    kind, data, uncertainty = classify(text, mono)
    assert kind == "code" and uncertainty
    assert data["classification"]["signals"]


@pytest.mark.parametrize(
    "text",
    [
        "x² + y² = z²",
        "E = mc^2",
        "∑ x_i = n",
        "∫ f(x) dx",
        r"\frac{a}{b} = c",
        "a + b = c",
    ],
)
@pytest.mark.parametrize("mono", [True, False])
def test_real_mathematical_notation_is_not_blanket_code(text, mono):
    kind, data, uncertainty = classify(text, mono)
    assert kind == "math" and uncertainty
    assert "mathematical_notation" in data["classification"]["signals"]


@pytest.mark.parametrize("mono", [True, False])
def test_ambiguous_assignment_is_conservative(mono):
    kind, data, uncertainty = classify("x = y + 1", mono)
    assert kind == "paragraph" and any("Ambiguous" in u for u in uncertainty)
    assert "assignment" in data["classification"]["signals"]


def test_font_is_a_signal_not_proof_or_an_override():
    assert classify("hello0.py")[0] == "paragraph"
    assert classify('"just a string"')[0] == "paragraph"
    assert classify("python hello.py")[0] == "code"
    assert classify("obj.method()", mono=True)[0] == "code"
    assert classify("f(x)", mono=True)[0] == "paragraph"
    result = classify_text(
        "# comment", [dict(text="# comment", font="UnusualFont", flags=8, size=12)], 12
    )
    assert result[0] == "code" and result[1]["classification"]["monospace_ratio"] == 1


def test_line_number_view_is_separate_and_indentation_preserved():
    raw = " 8  # Comment\n 9  def hello():\n10      print('hi')\n11      return 'ok'"
    kind, data, uncertainty = classify(raw)
    assert kind == "code"
    assert [r["number"] for r in data["line_numbers"]] == [8, 9, 10, 11]
    assert (
        data["code_view"] == "# Comment\ndef hello():\n    print('hi')\n    return 'ok'"
    )
    assert (
        "\n".join(
            row["prefix"] + line
            for row, line in zip(
                data["line_numbers"], data["code_view"].split("\n"), strict=True
            )
        )
        == raw
    )
    assert any("gutter inferred" in u for u in uncertainty)


@pytest.mark.parametrize(
    "text",
    [
        "1  print('a')\n3  print('b')\n4  print('c')",
        "1 print('a')\n2 print('b')\n3 print('c')",
        "1  print('a')\n2  print('b')",
        "1  x = y + 1\n2  a = b + 1\n3  c = d + 1",
        "1  Introduction\n2  Summary\n3  Conclusion",
    ],
)
def test_uncertain_numbering_never_generates_a_code_view(text):
    _, data, _ = classify(text)
    assert "code_view" not in data and "line_numbers" not in data


def code_pdf():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        " 1  # Example\n 2  def hello():\n 3      print(x=1)",
        fontname="cour",
        fontsize=12,
    )
    raw = doc.tobytes()
    doc.close()
    return raw


def test_real_worker_keeps_every_extracted_character_and_bbox():
    raw = code_pdf()
    with pymupdf.open(stream=raw, filetype="pdf") as original:
        source = original[0].get_text("dict")["blocks"][0]
    text = "\n".join(
        "".join(s["text"] for s in line["spans"]) for line in source["lines"]
    )
    doc, _ = parse_pdf(binding("pdf"), raw)
    block = doc.blocks[0]
    assert block.type == "code" and block.text == text and block.text.startswith(" 1")
    assert block.location.page == 1 and block.location.bbox == tuple(source["bbox"])
    assert block.data["line_bboxes"] == [list(line["bbox"]) for line in source["lines"]]
    assert block.data["code_view"] == "# Example\ndef hello():\n    print(x=1)"
    assert NormalizedDocument.model_validate_json(doc.model_dump_json()) == doc


@pytest.mark.parametrize(
    "limits,message",
    [
        ({"max_blocks": 1}, "block limit"),
        ({"max_images": 0}, "image"),
        ({"max_bytes": 5}, "byte limit"),
    ],
)
def test_pdf_limits_preserved(limits, message):
    from tests.test_cs50_material_pdf import pdf_bytes

    with pytest.raises(ValueError, match=message):
        parse_pdf(
            binding("pdf"), pdf_bytes(), ParserConfig(name="pdf", version="2", **limits)
        )


def test_old_pdf_receipt_readable_not_reinterpreted_or_overwritten(tmp_path):
    from src.tools_materials.parse_html import build_document

    b = binding("pdf")
    raw = code_pdf()
    old_config = ParserConfig(name="pdf")
    assert old_config.version == "1"
    old = build_document(
        b,
        raw,
        old_config,
        [dict(type="math", text="legacy", location=dict(page=1, bbox=(0, 0, 10, 10)))],
    )
    assert NormalizedDocument.model_validate_json(old.model_dump_json()) == old
    with pytest.raises(ValueError, match="v1 is read-only"):
        parse_pdf(b, raw, old_config)
    source = tmp_path / "original.pdf"
    source.write_bytes(raw)
    w = tmp_path / "old-workspace"
    downloader = MaterialDownloader(w)
    receipt = downloader.obtain(b, execute=True, local_file=source)
    rawpath, rp = downloader.paths(b)
    normalized = w / "legacy/normalized.v1.json"
    normalized.parent.mkdir()
    normalized.write_text(old.model_dump_json())
    receipt = receipt.model_copy(
        update=dict(
            status="completed",
            parser=old_config,
            normalized_path="legacy/normalized.v1.json",
            normalized_sha256=digest(normalized),
        )
    )
    rp.write_text(receipt.model_dump_json())
    before = [digest(p) for p in (rawpath, normalized, rp)]
    assert ArtifactReceipt.model_validate_json(rp.read_bytes()) == receipt
    assert MaterialProcessor(w).inspect(b, old_config) == receipt
    with pytest.raises(ExecutionConflict, match="configuration"):
        MaterialProcessor(w).parse(b, execute=True)
    new_w = tmp_path / "new-workspace"
    MaterialDownloader(new_w).obtain(b, execute=True, local_file=source)
    result = MaterialProcessor(new_w).parse(b, execute=True)
    new = NormalizedDocument.model_validate_json(
        (new_w / result.normalized_path).read_bytes()
    )
    assert new.parser.version == parser_for(b)[0].version == "2"
    assert (
        new.binding == old.binding and new.raw_sha256 == hashlib.sha256(raw).hexdigest()
    )
    assert (
        new.document_id != old.document_id
        and new.blocks[0].block_id != old.blocks[0].block_id
    )
    assert before == [digest(p) for p in (rawpath, normalized, rp)]


def test_worker_keeps_real_math_alongside_assignment_code():
    original = pymupdf.open()
    p = original.new_page()
    p.insert_text((50, 50), "print(x=1)", fontname="cour", fontsize=12)
    p.insert_text((50, 100), "x^2 + y^2 = z^2", fontname="cour", fontsize=12)
    raw = original.tobytes()
    original.close()
    result, _ = parse_pdf(binding("pdf"), raw)
    assert [(b.type, b.text) for b in result.blocks] == [
        ("code", "print(x=1)"),
        ("math", "x^2 + y^2 = z^2"),
    ]
    assert all(b.uncertainty for b in result.blocks)


@pytest.mark.parametrize(
    "key,pages", [("CS50_LECTURE_PDF_ARTIFACTS", 32), ("CS50_SOURCE_PDF_ARTIFACTS", 24)]
)
def test_optional_original_pdf_preserves_text_and_all_misclassifications(key, pages):
    import os
    from pathlib import Path

    root_value = os.environ.get(key)
    if not root_value:
        pytest.skip(f"Optional local original not supplied via {key}")
    root = Path(root_value)
    matches = list(root.glob("*/receipt.v1.json"))
    assert len(matches) == 1
    rp = matches[0]
    receipt = ArtifactReceipt.model_validate_json(rp.read_bytes())
    rawpath = rp.parent / "raw/source"
    np = root / receipt.normalized_path
    before = [digest(p) for p in [rp, rawpath, np]]
    old = NormalizedDocument.model_validate_json(np.read_bytes())
    assert old.parser.version == "1" and digest(rawpath) == receipt.raw_sha256
    new, _ = parse_pdf(receipt.binding, rawpath.read_bytes())
    expected = []
    with pymupdf.open(rawpath) as pdf:
        assert len(pdf) == pages == new.metadata["page_count"]
        for number, page in enumerate(pdf, 1):
            for block in page.get_text(
                "dict", flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
            )["blocks"]:
                if block["type"] != 0:
                    continue
                text = "\n".join(
                    "".join(s["text"] for s in line["spans"]) for line in block["lines"]
                )
                if text.strip():
                    expected.append((number, tuple(block["bbox"]), text))
    assert [
        (b.location.page, b.location.bbox, b.text)
        for b in new.blocks
        if b.type not in {"table", "image_reference"}
    ] == expected
    pairs = list(zip(old.blocks, new.blocks, strict=True))
    for a, b in pairs:
        assert a.location == b.location and a.text == b.text.strip()
    if pages == 24:
        repaired = [(a, b) for a, b in pairs if a.type == "math"]
        assert len(repaired) == 23
        assert all(
            b.type == "code" and b.data["classification"]["python_syntax_valid"]
            for _, b in repaired
        )
        codes = [b for b in new.blocks if b.type == "code"]
        assert len(codes) == 24 and len(new.blocks) == 48
        assert all(b.data["line_number_strategy"] for b in codes)
        for b in codes:
            assert (
                "\n".join(
                    r["prefix"] + s
                    for r, s in zip(
                        b.data["line_numbers"],
                        b.data["code_view"].split("\n"),
                        strict=True,
                    )
                )
                == b.text
            )
        assert all(b.type == "paragraph" for b in new.blocks if "\n" not in b.text)
    else:
        repaired = [(a, b) for a, b in pairs if a.type == "math"]
        assert len(repaired) == 1 and repaired[0][1].type == "code"
        assert repaired[0][1].text.startswith("print(")
    assert NormalizedDocument.model_validate_json(new.model_dump_json()) == new
    assert before == [digest(p) for p in [rp, rawpath, np]]
