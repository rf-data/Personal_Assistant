"""Rebuild small explicitly synthetic fixtures; no external content or renderer."""

import base64
from pathlib import Path


def build(folder):
    import pymupdf

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 2, 2), False)
    pixmap.clear_with(128)
    png = pixmap.tobytes("png")
    encoded = base64.b64encode(png).decode()
    html = f"""<!doctype html><html><head><title>Synthetic visuals</title></head><body>
<main><h1>Synthetic visual fixture</h1>
<figure><img src="data:image/png;base64,{encoded}" alt="synthetic square"><figcaption>Synthetic gray square, no scientific meaning.</figcaption></figure>
<img src="data:image/png;base64,{encoded}" alt="same bytes, other position">
<img src="plots/local.png" alt="relative reference">
<img src="https://example.invalid/plot.svg" alt="external SVG reference">
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><path id="shape" d="M0 0 L50 40"/><use href="#shape"/></svg>
<object type="image/svg+xml" data="figures/extra.svg"></object>
<img><img src=""><img src="javascript:alert(1)"><img src="file:///never-read.png">
<picture><source srcset="small.png 1x, large.png 2x"><img srcset="fallback.png 1x"></picture>
</main></body></html>"""
    html += "\n"
    (folder / "source.html").write_text(html)
    document = pymupdf.open()
    for number in range(2):
        page = document.new_page(width=300, height=300)
        page.draw_rect(pymupdf.Rect(0, 0, 300, 300), color=None, fill=(1, 1, 1))
        page.draw_line((20, 280), (280, 280), color=(0, 0, 0))
        page.insert_text((25, 35), f"Synthetic page {number + 1}")
        if number == 0:
            page.insert_image(pymupdf.Rect(30, 50, 70, 90), stream=png)
            page.insert_image(pymupdf.Rect(90, 50, 130, 90), stream=png)
            page.draw_line((40, 180), (160, 180))
            page.draw_line((40, 110), (40, 180))
            shape = page.new_shape()
            shape.draw_polyline([(40, 180), (60, 150), (90, 170), (140, 120)])
            shape.finish(color=(0, 0, 1))
            shape.commit()
            page.draw_rect(pymupdf.Rect(210, 50, 260, 90), color=(0, 0, 0))
    pdf = document.tobytes(garbage=4, deflate=True, no_new_id=True)
    document.close()
    (folder / "source.pdf.b64").write_text(base64.b64encode(pdf).decode() + "\n")
    return html.encode(), pdf


if __name__ == "__main__":
    build(Path(__file__).parent)
