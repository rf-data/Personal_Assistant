"""Private bounded subprocess entrypoint. Stdout is a capped result file."""

import ast
import base64
import hashlib
import json
import re
import resource
import sys


def numbered_lines(text):
    """Candidate only: consecutive numbers and a constant two-space gutter.

    Leading alignment spaces belong to the gutter; indentation after its two
    separator spaces belongs to code. No stripping/dedenting of the payload.
    """
    lines = text.split("\n")
    rows = []
    payload = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"( *)([0-9]{1,5})(  )(.*)", line)
        if not match:
            return None
        prefix = match[1] + match[2] + match[3]
        rows.append(dict(line_index=index, number=int(match[2]), prefix=prefix))
        payload.append(match[4])
    if len(rows) < 3 or len({len(r["prefix"]) for r in rows}) != 1:
        return None
    numbers = [r["number"] for r in rows]
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        return None
    return rows, "\n".join(payload)


def classify_text(text, spans, typical):
    """Source-backed heuristics only; ast.parse never compiles or runs code."""
    fonts = ("mono", "courier", "consolas", "menlo", "monaco", "typewriter", "cmtt")
    total = sum(len(s["text"]) for s in spans)
    mono = sum(
        len(s["text"])
        for s in spans
        if s.get("flags", 0) & 8 or any(f in s.get("font", "").lower() for f in fonts)
    )
    ratio = mono / total if total else 0
    monospaced = ratio >= 0.6
    numbered = numbered_lines(text)
    candidate = numbered[1] if numbered and monospaced else text
    signals = set()
    if monospaced:
        signals.add("monospace")
    if "\n" in candidate:
        signals.add("multiline")
    if re.search(r"(?m)^\s*#", candidate):
        signals.add("python_comment")
    if re.search(
        r"(?m)^[ \t]*(?:async[ \t]+)?(?:def[ \t]+\w+[ \t]*\([^\n]*\)|class[ \t]+\w+(?:\([^\n]*\))?)[ \t]*(?:->[^\n:]+)?[ \t]*:",
        candidate,
    ):
        signals.add("python_definition")
    if re.search(
        r"(?m)^[ \t]*(?:from[ \t]+\w+[ \t]+import[ \t]+|import[ \t]+\w+|(?:if|elif|for|while|with|try|except)[ \t:].*:[ \t]*$)",
        candidate,
    ):
        signals.add("python_statement")
    # Documentation signatures can be incomplete Python but still have a
    # distinctive builtin call form. Generic f(x) is deliberately insufficient.
    builtin = r"(?:print|input|len|str|int|float|range|enumerate|isinstance|open)"
    if re.search(
        r"(?m)^[ \t]*(?:\w+[ \t]*=[ \t]*)?" + builtin + r"[ \t]*\(", candidate
    ):
        signals.add("python_builtin_call")
    tree = None
    try:
        tree = ast.parse(candidate)
    except (SyntaxError, ValueError, RecursionError):
        pass
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                signals.add("assignment")
                if isinstance(node.value, (ast.JoinedStr, ast.Constant)) and isinstance(
                    getattr(node.value, "value", ""), str
                ):
                    signals.add("python_string_assignment")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                signals.add("python_method_call")
            if isinstance(
                node, (ast.Return, ast.Raise, ast.Pass, ast.Break, ast.Continue)
            ):
                signals.add("python_control")
    if re.search(r"(?m)^[ \t]*python(?:3)?[ \t]+[\w./-]+\.py(?:[ \t]|$)", candidate):
        signals.add("python_cli")
    decisive = signals & {
        "python_definition",
        "python_builtin_call",
        "python_string_assignment",
    }
    supported = monospaced and signals & {
        "python_statement",
        "python_method_call",
        "python_control",
        "python_cli",
    }
    comment_fragment = monospaced and "python_comment" in signals and tree is not None
    uncertainty = ()
    if decisive or supported or comment_fragment:
        kind = "code"
        uncertainty = (
            "Python-shaped source; heuristic classification, not execution or semantic verification",
        )
        if tree is None:
            uncertainty += (
                "Incomplete/non-parseable Python fragment or documentation signature",
            )
    elif re.search(
        r"[∑Σ∫√∂∞∈≠≤≥²³]|\\(?:sum|int|frac|sqrt)\b|\^\s*(?:\w|\{)", candidate
    ) or (
        "=" in candidate
        and "assignment" not in signals
        and re.search(r"[+*/()]", candidate)
    ):
        kind = "math"
        signals.add("mathematical_notation")
        uncertainty = (
            "Literal mathematical notation candidate; not semantically verified or reconstructed",
        )
    elif "assignment" in signals or "=" in candidate:
        kind = "paragraph"
        uncertainty = (
            "Ambiguous assignment/equation; insufficient Python or mathematical evidence",
        )
    elif monospaced:
        kind = "paragraph"
        uncertainty = ("Monospace font alone is insufficient to identify code",)
    elif spans and min(s["size"] for s in spans) > typical * 1.2:
        kind = "heading"
        uncertainty = ("font-size heading heuristic",)
    else:
        kind = "paragraph"
    data = dict(
        classification=dict(
            strategy="python_math_v2",
            signals=sorted(signals),
            monospace_ratio=ratio,
            python_syntax_valid=tree is not None,
        )
    )
    if numbered and monospaced and kind == "code":
        data.update(
            line_numbers=numbered[0],
            code_view=numbered[1],
            line_number_strategy="sequential_aligned_two_space_gutter_v1",
        )
        uncertainty += (
            "Line-number gutter inferred from consecutive aligned numbers; original text retained",
        )
    return kind, data, uncertainty


def bounded_limit(kind, soft, hard):
    """Worker limits may tighten, never raise an inherited job hard limit."""
    _, inherited = resource.getrlimit(kind)
    if inherited != resource.RLIM_INFINITY:
        hard = min(hard, inherited)
    resource.setrlimit(kind, (min(soft, hard), hard))


def main():
    destination = sys.stdout
    sys.stdout = (
        sys.stderr
    )  # Native-library diagnostics must never corrupt the JSON channel.
    request = json.loads(sys.stdin.read())
    config = request["config"]
    if config["name"] != "pdf" or config["version"] != "2":
        raise ValueError("Only PDF-v2 normalization is supported by this worker")
    memory = config["memory_mb"] * 1024 * 1024
    bounded_limit(resource.RLIMIT_AS, memory, memory)
    bounded_limit(
        resource.RLIMIT_CPU,
        max(1, int(config["timeout"])),
        max(2, int(config["timeout"]) + 1),
    )
    bounded_limit(resource.RLIMIT_FSIZE, 64 * 1024 * 1024, 64 * 1024 * 1024)
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
                )
                if not text.strip():
                    continue
                ss = [s for line in b["lines"] for s in line["spans"]]
                kind, data, uncertain = classify_text(text, ss, typical)
                data["line_bboxes"] = [line["bbox"] for line in b["lines"]]
                emit(
                    kind,
                    text,
                    data=data,
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
