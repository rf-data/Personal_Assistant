import pytest

from src.tools_materials.parse_code import parse_code
from tests.test_cs50_material_download import binding


@pytest.mark.parametrize(
    "fmt,body,language",
    [
        ("py", b'\xef\xbb\xbf# own fixture\nprint("hello")\n', "python"),
        ("sql", b"-- own fixture\nSELECT 1;\n", "sql"),
        ("html", b"<p>literal source, not rendered</p>", "html"),
        ("md", "Unicode: café\n".encode(), "markdown"),
    ],
)
def test_exact_lines_and_encoding(fmt, body, language):
    d, images = parse_code(binding(fmt, "source_code"), body)
    assert "".join(b.text for b in d.blocks) == body.decode("utf-8-sig")
    assert all(b.data["language"] == language for b in d.blocks)
    assert d.blocks[-1].location.line_end == len(d.blocks)
    assert not images


@pytest.mark.parametrize("body", [b"", b"\xff", b"\x00code"])
def test_invalid_code(body):
    with pytest.raises((ValueError, UnicodeError)):
        parse_code(binding("py", "source_code"), body)


def test_zip_explicitly_unsupported():
    with pytest.raises(ValueError, match="archives"):
        parse_code(binding("zip", "source_code"), b"PK arbitrary")


def test_encoded_path_traversal_never_imported_as_source(tmp_path):
    from src.model_discovery.cs50 import ResourceCandidate
    from src.model_materials.materials import MaterialResource
    from src.tools_materials.parse_code import parse_code

    r = ResourceCandidate(
        course_id="cs50_python",
        role="source_code",
        original_url="https://cdn.cs50.net/python/%2e%2e%2fevil.py",
    )
    b = MaterialResource(
        resource=r, original_url=str(r.original_url), format="py", role="source_code"
    )
    with pytest.raises(ValueError, match="path"):
        parse_code(b, b"print(1)")
