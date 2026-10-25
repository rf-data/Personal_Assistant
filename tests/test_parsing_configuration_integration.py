"""Isolated legacy boundaries; SDK functions are injected, not executed.

Real function/class AST is used where module imports require unavailable legacy
SDKs. Modern synthetic PDF/HTML/material tests provide the separate parser gate.
"""

import ast
import logging
from dataclasses import is_dataclass
from enum import StrEnum
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

import pytest
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.core.config_parsing import ChunkSettings, GeneralSettings, ParseSettings
from src.utils.general_helper import get_file_config
from src.utils.path_helper import ensure_dir
from tests.parsing_config_support import ROOT


def declarations(path, names, **namespace):
    tree = ast.parse((ROOT / path).read_text())
    nodes = [
        n
        for n in tree.body
        if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names
    ]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


@pytest.fixture
def context_models():
    return declarations(
        "src/core/memory_parsing.py",
        ["PARSER_BACKEND", "ParseContext"],
        BaseModel=BaseModel,
        ConfigDict=ConfigDict,
        Field=Field,
        Path=Path,
        Literal=Literal,
        StrEnum=StrEnum,
        Encoding=type("UnusedEncoding", (), {}),
        ChunkSettings=ChunkSettings,
        GeneralSettings=GeneralSettings,
        ParseSettings=ParseSettings,
    )


def test_context_family_assignment_and_json(context_models):
    context = context_models.ParseContext(
        parser_backend="diy", save_folder="unchanged", save_name="source"
    )
    assert type(context.parse_settings) is ParseSettings
    assert type(context.general_settings) is GeneralSettings
    assert context.parser_backend is context_models.PARSER_BACKEND.DIY
    assert (
        context_models.ParseContext.model_validate_json(
            context.model_dump_json()
        ).save_name
        == "source"
    )
    with pytest.raises(ValidationError):
        context.parser_backend = "unknown"
    with pytest.raises(ValidationError):
        context.parse_settings = None
    for suffix in ("pdf", "docx", "md", "html", "json_nb", "plain_text", "url", "wiki"):
        assert get_file_config(context.parse_settings, suffix) is getattr(
            context.parse_settings, suffix
        )
    # Existing naming mismatch; do not introduce a txt/plain_text alias.
    with pytest.raises(ValueError, match="txt"):
        get_file_config(context.parse_settings, "txt")


@pytest.mark.parametrize("suffix", ["pdf", "docx", "md"])
def test_lecture_context_preserves_paths_and_yaml(tmp_path, context_models, suffix):
    source = tmp_path / "original" / f"notes.{suffix}"
    source.parent.mkdir()
    source.write_bytes(b"synthetic source; context construction only")
    session = SimpleNamespace()
    loader = declarations(
        "src/utils/dict_helper.py",
        ["load_yaml_config"],
        Path=Path,
        GeneralSettings=GeneralSettings,
        ParseSettings=ParseSettings,
        yaml=yaml,
        app_session=SimpleNamespace(logger=logging.getLogger(__name__)),
        shorten_path=str,
    )
    calls = []

    def unused_encoder(model):
        calls.append(model)
        return None

    builder = declarations(
        "src/tools_lecture/process_lecture.py",
        ["build_document_parse_context"],
        Path=Path,
        ParseContext=context_models.ParseContext,
        GeneralSettings=GeneralSettings,
        ParseSettings=ParseSettings,
        folder_env_vars=SimpleNamespace(config_dir=ROOT / "configuration"),
        load_yaml_config=loader.load_yaml_config,
        ALLOWED_TEXT_TYPES={"pdf", "docx", "md"},
        ensure_dir=ensure_dir,
        make_doc_id_by_content=lambda p: Path(p).read_bytes().hex(),
        encoding_for_model=unused_encoder,
        app_session=session,
    )
    result = builder.build_document_parse_context(
        SimpleNamespace(local_path=source), tmp_path
    )
    assert result.local_path == source
    assert result.save_folder == tmp_path / "parsed"
    assert result.save_name == result.run_id == "notes"
    assert result.text_type == suffix
    assert result.doc_kind == "lecture"
    assert result.parser_backend is None  # Builder never selected a backend.
    assert result.parse_settings.pdf.classify_header_footer is False
    assert result.general_settings.pdf.x_gap_words == 35
    assert calls == ["gpt-4o-mini"]
    assert session.parse_context is result
    assert source.read_bytes().startswith(b"synthetic")


def test_document_backend_and_output_names(tmp_path, context_models):
    calls = []
    source = tmp_path / "course" / "original" / "Notes.PDF"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic; converter is injected")
    context = context_models.ParseContext(
        parser_backend="diy", save_folder="configured", save_name="configured-name"
    )
    routing = declarations(
        "src/tools_parsing/parse_document.py",
        ["parse_document"],
        Path=Path,
        ParseContext=context_models.ParseContext,
        PARSER_BACKEND=context_models.PARSER_BACKEND,
        FeatureEnricher=lambda **kw: "enricher",
        parse_pdf_diy=lambda **kw: calls.append(kw),
        parse_document_docling=lambda *args, **kw: calls.append((args, kw)),
    )
    routing.parse_document(source, context)
    assert calls.pop() == {
        "file_path": source,
        "parse_context": context,
        "enricher": "enricher",
    }
    context.parser_backend = "docling"
    routing.parse_document(source, context)
    assert calls.pop() == ((source,), {"save_folder": source.parent.parent / "parsed"})
    assert (
        context.save_folder == "configured" and context.save_name == "configured-name"
    )
    context.parser_backend = None
    with pytest.raises(ValueError, match="Unknown parser backend"):
        routing.parse_document(source, context)


def test_persisted_dictionary_adapter(tmp_path):
    import json

    loader = declarations(
        "src/utils/dict_helper.py",
        ["load_dict", "ensure_json_suffix"],
        Path=Path,
        BaseModel=BaseModel,
        is_dataclass=is_dataclass,
        json=json,
        ensure_dir=ensure_dir,
        shorten_path=lambda *args: str(args[0]),
        app_session=SimpleNamespace(logger=logging.getLogger(__name__)),
    )
    path = tmp_path / "stored.json"
    payload = ParseSettings(file_name="notes.pdf", pdf={"classify_headings": False})
    path.write_text(payload.model_dump_json())
    assert loader.load_dict(path.with_suffix(""), cls=ParseSettings) == payload
    path.write_text(json.dumps([payload.model_dump()]))
    assert loader.load_dict(path, cls=ParseSettings) == [payload]


def test_docling_boundary_keeps_json_markdown_names(tmp_path):
    import json

    session = SimpleNamespace(logger=logging.getLogger(__name__))
    writer = declarations(
        "src/utils/text_file_helper.py",
        ["save_text_file"],
        Path=Path,
        app_session=session,
        ensure_dir=ensure_dir,
        shorten_path=str,
    )
    document = SimpleNamespace(
        export_to_dict=lambda: {"texts": [{"text": "synthetic"}]},
        export_to_markdown=lambda: "# Synthetic\n",
    )
    options = []

    def converter(enrich):
        options.append(enrich)
        return SimpleNamespace(convert=lambda path: SimpleNamespace(document=document))

    boundary = declarations(
        "src/tools_parsing/parse_document.py",
        ["parse_document_docling"],
        Path=Path,
        get_docling_converter=converter,
        ensure_dir=ensure_dir,
        json=json,
        save_text_file=writer.save_text_file,
    )
    output = tmp_path / "parsed"
    assert boundary.parse_document_docling(Path("Notes.docx"), output) is document
    assert options == [False]
    assert sorted(p.name for p in output.iterdir()) == [
        "Notes_docling.json",
        "Notes_docling.md",
    ]
    assert (
        json.loads((output / "Notes_docling.json").read_text())
        == document.export_to_dict()
    )
    assert (output / "Notes_docling.md").read_text() == "# Synthetic\n"
