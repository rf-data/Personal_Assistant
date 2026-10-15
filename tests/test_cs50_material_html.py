import base64

import pytest

from src.model_materials.materials import NormalizedDocument, ParserConfig
from src.tools_materials.parse_html import parse_html
from tests.test_cs50_material_download import binding

HTML = b"""<html><head><title>Python exercise</title><meta name="license" content="test fixture"></head>
<body><nav>Outside nav</nav><main><h1>Functions</h1><p>Use <a href="help/">help</a>.</p>
<ol><li>Read<ul><li>Then write</li></ul></li></ol><table><tr><th>Input</th><td>Output</td></tr></table>
<pre><code class="language-python">print("hello")\n</code></pre><p>Math: \\(x+y\\)</p>
<math><mi>x</mi></math><figure><img src="figure.png" alt="plot"><figcaption>Illustration</figcaption></figure>
<footer>Hidden footer</footer></main></body></html>"""


def test_structured_html_assignment_and_refs():
    d, images = parse_html(binding(role="problem_set"), HTML)
    assert d.title == "Python exercise"
    assert not images
    assert {b.type for b in d.blocks} >= {
        "heading",
        "paragraph",
        "list",
        "table",
        "code",
        "math",
        "link",
        "image_reference",
    }
    assert "Hidden footer" not in str(d.blocks)
    assert "Outside nav" not in str(d.blocks)
    assert all(b.location.dom for b in d.blocks)
    assert (
        next(b for b in d.blocks if b.type == "list").data["items"][0]["children"][0][
            "items"
        ][0]["text"]
        == "Then write"
    )
    assert (
        d.images[0].original_url == "https://cs50.harvard.edu/python/notes/0/figure.png"
    )
    assert d.images[0].caption == "Illustration"
    assert d.binding.resource.section_keys == ("0",)
    assert NormalizedDocument.model_validate_json(d.model_dump_json()) == d


def test_inline_images_deduplicate_bytes_not_locations():
    encoded = base64.b64encode(b"own synthetic image bytes").decode()
    raw = f'<main><img src="data:image/png;base64,{encoded}"><img src="data:image/png;base64,{encoded}"></main>'.encode()
    d, blobs = parse_html(binding(), raw)
    assert len(d.images) == 2 and len(blobs) == 1
    assert d.images[0].image_id != d.images[1].image_id
    assert d.images[0].sha256 == d.images[1].sha256


@pytest.mark.parametrize("raw", [b"", b"not HTML", b"<main></main>"])
def test_empty_or_invalid(raw):
    with pytest.raises(ValueError):
        parse_html(binding(), raw)


def test_limit():
    with pytest.raises(ValueError, match="limit"):
        parse_html(binding(), HTML, ParserConfig(name="html", max_blocks=1))


def test_existing_notes_assignment_snapshots_read_only():
    from pathlib import Path

    from src.model_discovery.cs50 import ResourceCandidate
    from src.model_materials.materials import MaterialResource
    from src.tools_lecture.cs50_manifest import load_fixture_manifest

    root = Path("docs/course_sources/cs50")
    manifest = load_fixture_manifest(root / "manifest.json")
    count = 0
    for course in manifest.courses:
        for page in course.pages:
            if page.role not in {"lecture_notes", "assignment"}:
                continue
            r = ResourceCandidate(
                course_id=course.course_id,
                role="notes" if page.role == "lecture_notes" else "problem_set",
                original_url=page.url,
            )
            b = MaterialResource(
                resource=r, original_url=str(page.url), role=r.role.value, format="html"
            )
            raw = (root / page.file).read_bytes()
            doc, _ = parse_html(b, raw)
            assert (
                doc.blocks
                and doc.raw_sha256 == __import__("hashlib").sha256(raw).hexdigest()
            )
            assert (root / page.file).read_bytes() == raw
            count += 1
    assert count == 5
