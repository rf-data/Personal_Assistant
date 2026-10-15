"""Private bounded subprocess entrypoint. Stdout is a capped result file."""

import base64
import hashlib
import json
import resource
import sys


def main():
    destination = sys.stdout
    sys.stdout = (
        sys.stderr
    )  # Native-library diagnostics must never corrupt the JSON channel.
    request = json.loads(sys.stdin.read())
    config = request["config"]
    memory = config["memory_mb"] * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (max(1, int(config["timeout"])), max(2, int(config["timeout"]) + 1)),
    )
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
    import pymupdf

    raw = base64.b64decode(request["raw"], validate=True)
    parts = []
    images = []
    blobs = {}
    warnings = []
    total_images = 0

    def emit(kind, text="", data=None, location=None, uncertainty=()):
        if len(parts) >= config["max_blocks"]:
            raise ValueError("PDF block limit exceeded")
        parts.append(
            dict(
                type=kind,
                text=text,
                data=data or {},
                location=location,
                uncertainty=uncertainty,
            )
        )

    with pymupdf.open(stream=raw, filetype="pdf") as doc:
        if doc.needs_pass or len(doc) > config["max_pages"]:
            raise ValueError("Encrypted PDF or page limit exceeded")
        metadata = doc.metadata
        for number, page in enumerate(doc, start=1):
            blocks = page.get_text(
                "dict", flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
            )["blocks"]
            spans = [
                s
                for b in blocks
                if b["type"] == 0
                for line in b["lines"]
                for s in line["spans"]
            ]
            sizes = sorted(s["size"] for s in spans)
            typical = sizes[len(sizes) // 2] if sizes else 12
            for b in blocks:
                if b["type"] != 0:
                    continue
                text = "\n".join(
                    "".join(s["text"] for s in line["spans"]) for line in b["lines"]
                ).strip()
                if not text:
                    continue
                ss = [s for line in b["lines"] for s in line["spans"]]
                kind = (
                    "code"
                    if ss
                    and all(
                        "mono" in s["font"].lower() or "courier" in s["font"].lower()
                        for s in ss
                    )
                    else "paragraph"
                )
                uncertain = ()
                if any(c in text for c in "=∑√∫"):
                    kind = "math"
                    uncertain = (
                        "PDF literal formula candidate; not verified or reconstructed",
                    )
                elif ss and min(s["size"] for s in ss) > typical * 1.2:
                    kind = "heading"
                    uncertain = ("font-size heading heuristic",)
                emit(
                    kind,
                    text,
                    location=dict(page=number, bbox=b["bbox"]),
                    uncertainty=uncertain,
                )
            for table in page.find_tables().tables:
                emit(
                    "table",
                    text="\n".join(
                        "\t".join(cell or "" for cell in row) for row in table.extract()
                    ),
                    data=dict(rows=table.extract()),
                    location=dict(page=number, bbox=table.bbox),
                    uncertainty=("geometric table candidate; may overlap text blocks",),
                )
            for image in page.get_images(full=True):
                item = doc.extract_image(image[0])
                content = item["image"]
                total_images += len(content)
                if (
                    len(images) >= config["max_images"]
                    or total_images > config["max_bytes"]
                ):
                    raise ValueError("PDF image count/byte limit exceeded")
                sha = hashlib.sha256(content).hexdigest()
                path = f"images/{sha}.bin"
                blobs[path] = base64.b64encode(content).decode()
                positions = page.get_image_rects(image[0])
                for rect in positions or [None]:
                    if len(images) >= config["max_images"]:
                        raise ValueError("PDF image reference limit exceeded")
                    location = dict(
                        page=number, bbox=list(rect) if rect is not None else None
                    )
                    token = f"image-{number}-{len(images)}"
                    images.append(
                        dict(
                            image_id=token,
                            source_location=location,
                            artifact_path=path,
                            sha256=sha,
                            mime_type="image/" + item["ext"],
                            context=page.get_text()[:1000],
                        )
                    )
                    emit(
                        "image_reference", data=dict(image_id=token), location=location
                    )
            if not spans:
                warnings.append(
                    f"Page {number}: no extractable text; OCR/visual interpretation unavailable"
                )
        json.dump(
            dict(
                parts=parts,
                images=images,
                blobs=blobs,
                metadata=metadata,
                warnings=warnings,
                page_count=len(doc),
            ),
            destination,
        )


if __name__ == "__main__":
    main()
