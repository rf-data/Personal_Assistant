"""Strict local text/source import. No evaluation, execution or archive extraction."""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from src.model_materials.materials import Location, ParserConfig
from src.tools_materials.parse_html import build_document, check_input

LANGUAGES = {
    "py": "python",
    "sql": "sql",
    "js": "javascript",
    "html": "html",
    "css": "css",
    "c": "c",
    "h": "c",
    "txt": "text",
    "md": "markdown",
}


def parse_code(binding, raw, config=None):
    config = config or ParserConfig(name="code")
    check_input(raw, config, "code")
    if binding.format not in LANGUAGES:
        raise ValueError("Unsupported source format; archives are never extracted")
    text = raw.decode("utf-8-sig", errors="strict")
    if not text.strip() or "\x00" in text:
        raise ValueError("Empty or binary source file")
    source_path = unquote(urlsplit(binding.original_url).path).lstrip("/")
    p = PurePosixPath(source_path)
    if not source_path or ".." in p.parts or "\\" in source_path:
        raise ValueError("Unsafe explicit source path")
    lines = text.splitlines(keepends=True)
    # One line per block gives exact, lossless references without guessed syntax boundaries.
    parts = [
        dict(
            type="code",
            text=line,
            data=dict(language=LANGUAGES[binding.format], source_path=source_path),
            location=Location(line_start=i, line_end=i),
        )
        for i, line in enumerate(lines, start=1)
    ]
    return build_document(
        binding,
        raw,
        config,
        parts,
        metadata=dict(
            source_path=source_path,
            programming_language=LANGUAGES[binding.format],
            encoding="utf-8-sig",
        ),
    ), {}
