"""Lossless body/code traversal and explicit v2 normalization, fully offline."""

import hashlib

import pytest
from bs4 import BeautifulSoup

from src.model_materials.materials import (
    ArtifactReceipt,
    NormalizedDocument,
    ParserConfig,
)
from src.tools_lecture.execute_cs50 import ExecutionConflict, digest
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.parse_html import parse_html
from src.tools_materials.processing import MaterialProcessor, parser_for
from tests.test_cs50_material_download import binding


def parse(markup, **limits):
    return parse_html(
        binding(), markup.encode(), ParserConfig(name="html", version="2", **limits)
    )[0]


def body(doc):
    return [
        b
        for b in doc.blocks
        if b.type not in {"list", "link", "math", "image_reference"}
    ]


def resolve(soup, path):
    for component in path.strip("/").split("/"):
        name, ordinal = component.rstrip("]").split("[")
        soup = soup.find_all(name, recursive=False)[int(ordinal) - 1]
    return soup


def test_list_paragraphs_multipart_and_hierarchy_in_source_order():
    markup = '<main><ol start="3"><li value="8">Lead<p>Paragraph <code>f(x)</code>.</p><ul><li>Nested</li></ul>Tail<pre><code>if True:\n    print("yes")\n</code></pre><p>Last</p></li><li></li></ol></main>'
    d = parse(markup)
    assert [b.text for b in body(d)] == [
        "Lead",
        "Paragraph f(x).",
        "Nested",
        "Tail",
        'if True:\n    print("yes")\n',
        "Last",
    ]
    outer, inner = [b for b in d.blocks if b.type == "list"]
    assert outer.text == inner.text == ""
    assert outer.data["start"] == "3" and len(outer.data["item_doms"]) == 2
    nested = next(b for b in d.blocks if b.text == "Nested")
    assert [c["item_index"] for c in nested.data["list_context"]] == [0, 0]
    assert nested.data["list_context"][0]["value"] == "8"
    assert nested.data["list_context"][-1]["list_dom"] == inner.location.dom
    assert d.blocks.index(inner) < d.blocks.index(nested)
    assert [b.order for b in d.blocks] == list(range(len(d.blocks)))
    assert len(set(b.block_id for b in d.blocks)) == len(d.blocks)


@pytest.mark.parametrize("container", ["p", "li", "div", "blockquote"])
def test_inline_code_and_code_in_links(container):
    d = parse(
        f'<main><{container}>Use <code>print("hi")</code>, then <a href="/help"><code>len(x)</code></a>.</{container}></main>'
    )
    p = body(d)[0]
    assert p.text == 'Use print("hi"), then len(x).'
    assert [s["text"] for s in p.data["inline_code"]] == ['print("hi")', "len(x)"]
    for s in p.data["inline_code"]:
        assert p.text[s["start"] : s["end"]] == s["text"]
    link = next(b for b in d.blocks if b.type == "link")
    assert link.text == "len(x)" and link.data["reference_only"]
    assert link.data["inline_code"][0]["dom"].endswith("/a[1]/code[1]")
    assert not any(b.type in {"unknown_block", "code"} for b in d.blocks)


@pytest.mark.parametrize(
    "wrapper",
    ["<pre>{}</pre>", '<div class="language-python"><pre><code>{}</code></pre></div>'],
)
def test_code_preserves_exact_whitespace_quotes_entities_and_unicode(wrapper):
    source = "\n  def hello(name):\n\tprint(&quot;héllo&quot;, name, &quot;&lt;&amp;&gt;&quot;)\n    return &apos;ok&apos;\n\n"
    d = parse(
        "<main><ul><li><p>Before</p>"
        + wrapper.format(source)
        + "<p>After</p></li></ul></main>"
    )
    code = next(b for b in d.blocks if b.type == "code")
    assert (
        code.text
        == '\n  def hello(name):\n\tprint("héllo", name, "<&>")\n    return \'ok\'\n\n'
    )
    assert [b.type for b in body(d)] == ["paragraph", "code", "paragraph"]
    assert code.data["list_context"][0]["item_index"] == 0
    if "language-python" in wrapper:
        assert code.data["language"] == "python"


def test_list_links_images_and_original_dom_are_not_lost_or_shifted():
    markup = '<html><body><main><nav><p>Exclude</p></nav><p>First</p><ul><li><p>Read <a href="next"><code>x</code></a>.</p><img src="plot.png" alt="plot"><pre>code\n</pre><p>End</p></li></ul></main></body></html>'
    soup = BeautifulSoup(markup, "html.parser")
    d = parse(markup)
    assert "Exclude" not in str(d.blocks)
    assert [b.text for b in body(d)] == ["First", "Read x.", "code\n", "End"]
    assert [b.type for b in d.blocks] == [
        "paragraph",
        "list",
        "paragraph",
        "link",
        "image_reference",
        "code",
        "paragraph",
    ]
    assert len(d.images) == 1 and d.images[0].original_url.endswith("/plot.png")
    assert d.blocks[0].location.dom.endswith("/main[1]/p[1]")
    for b in d.blocks:
        assert resolve(soup, b.location.dom) is not None
        for span in b.data.get("inline_code", []):
            assert resolve(soup, span["dom"]).get_text() == span["text"]
    assert NormalizedDocument.model_validate_json(d.model_dump_json()) == d
    assert parse(markup) == d


@pytest.mark.parametrize(
    "wrapper",
    [
        '<ul id="markdown-toc">{}</ul>',
        '<nav aria-label="Table of contents"><ul>{}</ul></nav>',
        '<div role="doc-toc"><ul>{}</ul></div>',
    ],
)
def test_toc_requires_explicit_structure_and_is_preserved(wrapper):
    d = parse(
        "<main>"
        + wrapper.format('<li><a href="#one">One</a></li>')
        + '<ul><li><a href="#two">Ordinary anchor list</a></li></ul></main>'
    )
    one = next(b for b in d.blocks if b.type == "paragraph" and b.text == "One")
    two = next(
        b
        for b in d.blocks
        if b.type == "paragraph" and b.text == "Ordinary anchor list"
    )
    assert one.data["content_role"] == "table_of_contents"
    assert "content_role" not in two.data
    assert len([b for b in d.blocks if b.type == "link"]) == 2


def test_limits_apply_to_each_emitted_child_and_nested_image():
    with pytest.raises(ValueError, match="block limit"):
        parse("<main><ul><li><p>A</p><p>B</p></li></ul></main>", max_blocks=2)
    with pytest.raises(ValueError, match="image limit"):
        parse('<main><ul><li><img src="x"></li></ul></main>', max_images=0)
    with pytest.raises(ValueError, match="byte limit"):
        parse("<main><p>abc</p></main>", max_bytes=5)


def test_version_one_remains_readable_and_cannot_be_silently_reparsed(tmp_path):
    b = binding()
    source = tmp_path / "original.html"
    source.write_text("<main><p>Official <code>print</code>.</p></main>")
    old_config = ParserConfig(name="html")
    assert (
        old_config.version == "1"
    )  # Existing defaults/omitted legacy fields stay stable.
    from src.tools_materials.parse_html import build_document

    old = build_document(
        b,
        source.read_bytes(),
        old_config,
        [dict(type="paragraph", text="legacy", location={"dom": "/main[1]/p[1]"})],
    )
    assert NormalizedDocument.model_validate_json(old.model_dump_json()) == old
    with pytest.raises(ValueError, match="v1 is read-only"):
        parse_html(b, source.read_bytes(), old_config)
    w = tmp_path / "old-workspace"
    worker = MaterialDownloader(w)
    receipt = worker.obtain(b, execute=True, local_file=source)
    raw, receipt_path = worker.paths(b)
    target = w / "old-output/normalized.v1.json"
    target.parent.mkdir()
    target.write_text(old.model_dump_json())
    receipt = receipt.model_copy(
        update=dict(
            status="completed",
            parser=old_config,
            normalized_path="old-output/normalized.v1.json",
            normalized_sha256=digest(target),
        )
    )
    receipt_path.write_text(receipt.model_dump_json())
    raw_hash, old_hash, receipt_hash = digest(raw), digest(target), digest(receipt_path)
    assert ArtifactReceipt.model_validate_json(receipt_path.read_bytes()) == receipt
    assert MaterialProcessor(w).inspect(b, old_config) == receipt
    with pytest.raises(ExecutionConflict, match="configuration"):
        MaterialProcessor(w).parse(b, execute=True)
    assert (digest(raw), digest(target), digest(receipt_path)) == (
        raw_hash,
        old_hash,
        receipt_hash,
    )
    new_worker = MaterialDownloader(tmp_path / "new-workspace")
    new_worker.obtain(b, execute=True, local_file=source)
    result = MaterialProcessor(tmp_path / "new-workspace").parse(b, execute=True)
    new = NormalizedDocument.model_validate_json(
        (tmp_path / "new-workspace" / result.normalized_path).read_bytes()
    )
    assert new.parser.version == parser_for(b)[0].version == "2"
    assert (
        new.binding == old.binding
        and new.raw_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    )
    assert (
        new.document_id != old.document_id
        and new.blocks[0].block_id != old.blocks[0].block_id
    )
    assert digest(target) == old_hash and digest(receipt_path) == receipt_hash


def test_optional_original_python_notes_read_only():
    """An absent original is a skip, never a download or synthetic replacement."""
    import collections
    import json
    import os
    import re
    from pathlib import Path

    from bs4 import Comment, NavigableString

    root = Path(os.environ.get("CS50_NOTES_ARTIFACTS", "/tmp/python0-notes-artifacts"))
    receipts = sorted(root.glob("*/receipt.v1.json"))
    if not receipts:
        pytest.skip("Optional original notes artifacts are not locally provided")
    matches = [
        (p, ArtifactReceipt.model_validate_json(p.read_bytes())) for p in receipts
    ]
    matches = [
        (p, r)
        for p, r in matches
        if r.binding.original_url == "https://cs50.harvard.edu/python/notes/0/"
    ]
    assert len(matches) == 1
    path, receipt = matches[0]
    raw_path = path.parent / "raw/source"
    normalized = root / receipt.normalized_path
    before = {p: digest(p) for p in [path, raw_path, normalized]}
    raw = raw_path.read_bytes()
    assert digest(raw_path) == receipt.raw_sha256
    old = NormalizedDocument.model_validate_json(normalized.read_bytes())
    new, blobs = parse_html(receipt.binding, raw)
    assert old.parser.version == "1" and new.parser.version == "2" and not blobs
    main = BeautifulSoup(raw, "html.parser").find("main")
    source_text = "".join(
        str(n)
        for n in main.descendants
        if isinstance(n, NavigableString)
        and not isinstance(n, Comment)
        and not any(
            t.name in {"nav", "footer", "aside", "script", "style", "noscript"}
            for t in n.parents
        )
    )
    primary_text = "\n".join(
        b.text for b in new.blocks if b.type not in {"link", "math", "image_reference"}
    )

    def tokenize(text):
        return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

    assert tokenize(source_text) == tokenize(
        primary_text
    )  # Includes order, not just a bag of tokens.
    from src.tools_materials.parse_html import dom_path

    source_codes = {
        dom_path(t): t.get_text("", strip=False) for t in main.find_all("pre")
    }
    assert {
        b.location.dom: b.text for b in new.blocks if b.type == "code"
    } == source_codes
    source_inline = {
        dom_path(t): t.get_text("", strip=False)
        for t in main.find_all("code")
        if not t.find_parent("pre")
    }
    actual_inline = [
        s for b in new.blocks if b.type != "link" for s in b.data.get("inline_code", [])
    ]
    assert collections.Counter(s["dom"] for s in actual_inline) == collections.Counter(
        source_inline.keys()
    )
    assert {s["dom"]: s["text"] for s in actual_inline} == source_inline
    assert len(main.select("a[href]")) == len(
        [b for b in new.blocks if b.type == "link"]
    )
    assert len(main.find_all("img")) == len(new.images)
    assert not any(b.type == "unknown_block" for b in new.blocks)
    assert NormalizedDocument.model_validate_json(new.model_dump_json()) == new
    assert json.loads(path.read_bytes())["parser"]["version"] == "1"
    assert {p: digest(p) for p in before} == before


@pytest.mark.parametrize(
    "image",
    [
        '<img src="x" alt="plot">',
        '<a href="image"><span><img src="x" alt="plot"></span></a>',
    ],
)
def test_image_splits_surrounding_list_prose_in_document_order(image):
    d = parse("<main><ul><li>Before" + image + "After</li></ul></main>")
    assert [(b.type, b.text) for b in d.blocks if b.type not in {"list", "link"}] == [
        ("paragraph", "Before"),
        ("image_reference", "plot"),
        ("paragraph", "After"),
    ]
    assert len(d.images) == 1


def test_non_html_versions_and_missing_legacy_version_stay_unchanged():
    assert ParserConfig.model_validate({"name": "html"}).version == "1"
    assert ParserConfig(name="pdf").version == ParserConfig(name="code").version == "1"
    with pytest.raises(ValueError, match="only implemented for HTML"):
        ParserConfig(name="code", version="2")


def test_equal_list_entries_keep_distinct_source_positions():
    d = parse("<main><ul><li>Same</li><li>Same</li></ul></main>")
    entries = body(d)
    assert [b.text for b in entries] == ["Same", "Same"]
    assert [b.data["list_context"][0]["item_index"] for b in entries] == [0, 1]
    assert entries[0].location.dom != entries[1].location.dom
