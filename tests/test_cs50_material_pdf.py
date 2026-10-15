import subprocess
import sys
import time

import pymupdf
import pytest

from src.model_materials.materials import ParserConfig
from src.tools_materials.parse_pdf import parse_pdf, run_worker
from tests.test_cs50_material_download import binding


def pdf_bytes():
    doc = pymupdf.open()
    a = doc.new_page()
    a.insert_text((50, 50), "Own synthetic slide", fontsize=24)
    a.insert_text((50, 90), "x = y + 1")
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 2, 2))
    image.clear_with(128)
    a.insert_image(pymupdf.Rect(50, 120, 90, 160), pixmap=image)
    b = doc.new_page()
    b.insert_text((50, 50), "Second page is retained")
    raw = doc.tobytes()
    doc.close()
    return raw


def test_multipage_images_formula_and_slide_role():
    doc, blobs = parse_pdf(binding("pdf", "slides"), pdf_bytes())
    assert doc.metadata["page_count"] == 2
    assert {b.location.page for b in doc.blocks} == {1, 2}
    assert any(b.type == "math" and b.uncertainty for b in doc.blocks)
    assert doc.images and blobs
    assert doc.images[0].source_location.page == 1
    assert doc.binding.role == "slides"


@pytest.mark.parametrize("raw", [b"", b"bad", b"%PDF-corrupt"])
def test_invalid(raw):
    with pytest.raises(ValueError):
        parse_pdf(binding("pdf"), raw)


def test_page_limit():
    with pytest.raises(ValueError, match="page limit"):
        parse_pdf(binding("pdf"), pdf_bytes(), ParserConfig(name="pdf", max_pages=1))


def test_actual_subprocess_timeout():
    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        run_worker([sys.executable, "-c", "import time; time.sleep(60)"], {}, 0.2)
    assert time.monotonic() - start < 5


def test_timeout_kills_descendant(tmp_path):
    marker = tmp_path / "child.pid"
    script = (
        'import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c",'
        '"import time; time.sleep(60)"]); '
        f'open({str(marker)!r},"w").write(str(p.pid)); time.sleep(60)'
    )
    with pytest.raises(subprocess.TimeoutExpired):
        run_worker([sys.executable, "-c", script], {}, 1)
    assert marker.exists()
    pid = int(marker.read_text())
    stat = __import__("pathlib").Path(f"/proc/{pid}/stat")
    # SIGKILL delivery to descendants is asynchronous after the leader is reaped.
    deadline = time.monotonic() + 2
    while (
        stat.exists()
        and stat.read_text().split()[2] != "Z"
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert not stat.exists() or stat.read_text().split()[2] == "Z"
