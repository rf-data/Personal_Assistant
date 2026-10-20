"""Authorized local orchestration of the integrated PDF-v2/C13 workers.

No MaterialResource is fabricated: these are isolated worker observations, not
C23 publications or C10 quality receipts. All content and diagnostics stay private.
"""

import argparse
import base64
import html
import json
import math
import os
import pwd
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path

from src.content_store.models import ContentLocator, canonical, fingerprint, sha256
from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import ParserConfig
from src.model_materials.visual_inventory import InventoryLimits
from src.tools_evaluation.math_syntax import FormulaSyntaxError, parse_formula

REPO = Path(__file__).resolve().parents[2]
INVENTORY = REPO / "docs/cs50/evaluation/dev03/loviscach/corpus_inventory.v1.json"
AUTHORIZED = "a37319b9b0d18fb246f6071638a35ae30b39f39f01187a3579cf5a501862500e"
MAX_OUTPUT = 128 * 1024**2
RESERVE = 256 * 1024**2
BOOTSTRAP = """import runpy,sys
def audit(event,args):
    if event.startswith(('socket.','urllib.','http.client.')):
        raise PermissionError('Network disabled for local evaluation')
sys.addaudithook(audit)
runpy.run_path(sys.argv[1],run_name='__main__')
"""


def checked_path(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Explicit absolute path required")
    for parent in (*reversed(path.parents), path):
        if parent.is_symlink():
            raise ValueError("Symlink path forbidden")
    return path


def private_directory(path):
    path = checked_path(path)
    if not path.exists():
        parent = path.parent
        if not parent.exists():
            private_directory(parent)
        info = parent.stat()
        if info.st_mode & 0o022:
            raise PermissionError("Writable parent forbidden")
        path.mkdir(mode=0o700)
    info = path.stat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise PermissionError("Private owned directory required")
    return path


def budget(root, additional=0):
    total = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    if (
        total + additional > MAX_OUTPUT
        or shutil.disk_usage(root).free < RESERVE + additional
    ):
        raise OSError("Private output capacity limit")


def write(root, path, data):
    path = checked_path(path)
    if not path.is_relative_to(root):
        raise ValueError("Output outside run")
    private_directory(path.parent)
    budget(root, len(data))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def dump(root, path, value):
    write(root, path, canonical(value) + b"\n")


def inventory():
    value = json.loads(INVENTORY.read_bytes())
    if (
        fingerprint(value["inventory"]) != value["sha256"]
        or value["sha256"] != AUTHORIZED
    ):
        raise ValueError("Authorization inventory mismatch")
    entries = value["inventory"]["entries"]
    if len(entries) != 4 or entries[0]["file_name"] != "Mathe_1_2020-01-31.pdf":
        raise ValueError("Exact four authorized inputs required")
    return entries


def read_original(input_root, entry):
    path = checked_path(input_root / entry["file_name"])
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 16 * 1024**2:
            raise ValueError("Bounded regular original required")
        data = stream.read(16 * 1024**2 + 1)
        after = os.fstat(stream.fileno())
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or len(data) != entry["raw_artifact"]["size_bytes"]
        or sha256(data) != entry["raw_artifact"]["sha256"]
    ):
        raise ValueError("Original identity changed")
    return data


def worker(root, folder, name, request, timeout):
    """Invoke the unchanged integrated worker; keep stdin/stdout/stderr private.

    wait4 measures this particular child's peak RSS, not a cumulative parent peak.
    No extracted expression becomes a command or Python program.
    """
    private_directory(folder)
    request_path = folder / "request.json"
    dump(root, request_path, request)
    output = folder / "response.json"
    error = folder / "diagnostics.txt"
    started = time.monotonic()
    out_fd = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    err_fd = os.open(error, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with (
        request_path.open("rb") as stdin,
        os.fdopen(out_fd, "wb") as stdout,
        os.fdopen(err_fd, "wb") as stderr,
    ):
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-c",
                BOOTSTRAP,
                str(REPO / "src/tools_materials" / name),
            ],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    break
                if time.monotonic() - started > timeout:
                    raise TimeoutError("Bounded worker deadline")
                time.sleep(0.01)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            raise
    metrics = dict(
        elapsed_seconds=time.monotonic() - started,
        max_rss_kib=usage.ru_maxrss,
        user_seconds=usage.ru_utime,
        system_seconds=usage.ru_stime,
        returncode=process.returncode,
    )
    dump(root, folder / "resources.json", metrics)
    if process.returncode or output.stat().st_size > 64 * 1024**2:
        raise ValueError("Worker failed; diagnostics retained privately")
    budget(root)
    return json.loads(output.read_bytes())


def candidate(entry, kind, pointer, location, text, hypothesis, syntax=None):
    locator = ContentLocator(
        raw_artifact_sha256=entry["raw_artifact"]["sha256"],
        origin_pointer=pointer,
        page=location.get("page"),
        bbox=location.get("bbox"),
        coordinate_system="pdf_points_top_left_unrotated",
        time_status="not_applicable",
    )
    return dict(
        candidate_id=deterministic_id(
            "dev03e_review_v1",
            entry["source_id"],
            locator.raw_artifact_sha256,
            kind,
            pointer,
        ),
        source_id=entry["source_id"],
        file_name=entry["file_name"],
        original_sha256=locator.raw_artifact_sha256,
        source_version_id=None,
        parsed_version_id=None,
        locator=locator.model_dump(mode="json"),
        kind=kind,
        extracted_result=text[:2000] if text else None,
        excerpt_truncated=bool(text and len(text) > 2000),
        hypothesis=hypothesis,
        technical_status="possible_error",
        syntax_status=syntax,
        independent_reference=None,
        review_decision=None,
        reviewed_by=None,
        reviewed_at=None,
        assigned_reviewer="robfra",
        reviewer_status="pending_review",
        procedure="integrated PDF-v2/C13 observations; C11 bounded notation grammar",
    )


def analyze(entry, data, visual):
    candidates = []
    syntax = Counter()
    types = Counter(p["type"] for p in data["parts"])
    page_counts = Counter(p["location"].get("page") for p in data["parts"])
    technical = Counter()
    seen = Counter(
        sha256(p.get("text", "").encode()) for p in data["parts"] if p.get("text")
    )
    for i, part in enumerate(data["parts"]):
        loc, text = part["location"], part.get("text", "")
        bbox = loc.get("bbox")
        if not loc.get("page") or not 1 <= loc["page"] <= entry["page_count"]:
            technical["invalid_page"] += 1
        if bbox is None or len(bbox) != 4 or not all(math.isfinite(x) for x in bbox):
            technical["missing_or_invalid_bbox"] += 1
        if text and (
            part["type"] == "math"
            or re.search(r"[=√∫∑∂²³]|\\(?:frac|sqrt|sum|int)\b", text)
        ):
            try:
                parse_formula(text, "plain_text")
                status = "syntax_valid"
            except FormulaSyntaxError as error:
                status = "not_evaluable" if error.unsupported else "syntax_invalid"
            syntax[status] += 1
            candidates.append(
                candidate(
                    entry,
                    "formula",
                    f"/parts/{i}",
                    loc,
                    text,
                    "literal_math_candidate_requires_original_review",
                    status,
                )
            )
        reason = (
            "repeated_text_may_be_header_or_footer"
            if text and seen[sha256(text.encode())] > 1
            else "replacement_character_observed_source_loss_unconfirmed"
            if "\ufffd" in text
            else "task_label_boundary_requires_review"
            if re.search(r"(?m)^\s*(?:Aufgabe\s+)?\d{1,2}[.)]\s", text)
            else "font_heading_heuristic_requires_review"
            if part["type"] == "heading"
            else None
        )
        if reason:
            candidates.append(
                candidate(entry, "structure", f"/parts/{i}", loc, text, reason)
            )
        if part["type"] == "table":
            candidates.append(
                candidate(
                    entry,
                    "visual",
                    f"/parts/{i}",
                    loc,
                    text,
                    "geometric_table_may_overlap_text_requires_review",
                )
            )
    for i, observation in enumerate(visual["observations"]):
        candidates.append(
            candidate(
                entry,
                "visual",
                f"/observations/{i}",
                observation["location"],
                None,
                "needs_visual_review_" + observation["tag"],
            )
        )
    if (
        data["page_count"] != entry["page_count"]
        or visual["page_count"] != entry["page_count"]
    ):
        technical["page_count_conflict"] += 1
    return dict(
        file_name=entry["file_name"],
        source_id=entry["source_id"],
        original_sha256=entry["raw_artifact"]["sha256"],
        page_count=data["page_count"],
        part_types=dict(types),
        total_parts=len(data["parts"]),
        text_blocks=sum(bool(p.get("text")) for p in data["parts"]),
        page_coverage={
            str(p): page_counts[p] for p in range(1, entry["page_count"] + 1)
        },
        formula_candidates=sum(c["kind"] == "formula" for c in candidates),
        syntax=dict(syntax),
        structure_candidates=sum(c["kind"] == "structure" for c in candidates),
        visual_observations=len(visual["observations"]),
        visual_tags=dict(Counter(o["tag"] for o in visual["observations"])),
        image_references=len(data["images"]),
        table_candidates=types["table"],
        parser_warning_count=len(data["warnings"]),
        uncertain_parts=sum(bool(p.get("uncertainty")) for p in data["parts"]),
        technical_findings=dict(technical),
        candidates=candidates,
        quality_denominator=0,
        quality_rate=None,
        gold_status="pending_review",
    )


def process_one(root, input_root, entry):
    folder = private_directory(root / entry["file_name"].removesuffix(".pdf"))
    raw = read_original(input_root, entry)
    config = ParserConfig(name="pdf", version="2")
    request = dict(raw=base64.b64encode(raw).decode(), config=config.model_dump())
    data = worker(root, folder / "pdf", "pdf_worker.py", request, config.timeout)
    again = worker(
        root, folder / "pdf-repeat", "pdf_worker.py", request, config.timeout
    )
    if data != again:
        raise ValueError("PDF observation repeat differs")
    limits = InventoryLimits()
    request = dict(
        raw=base64.b64encode(raw).decode(), kind="pdf", limits=limits.model_dump()
    )
    visual = worker(
        root, folder / "visual", "visual_worker.py", request, limits.timeout
    )
    visual_again = worker(
        root, folder / "visual-repeat", "visual_worker.py", request, limits.timeout
    )
    if visual != visual_again:
        raise ValueError("Visual observation repeat differs")
    # Validate original image artifacts without changing the authoritative response.
    for image in data["images"]:
        blob = base64.b64decode(data["blobs"][image["artifact_path"]], validate=True)
        if sha256(blob) != image["sha256"]:
            raise ValueError("Image artifact hash conflict")
    summary = analyze(entry, data, visual)
    summary.update(
        pdf_observations_sha256=fingerprint(data),
        visual_observations_sha256=fingerprint(visual),
        repeat_identical=True,
        config=config.model_dump(mode="json"),
        visual_limits=limits.model_dump(mode="json"),
    )
    if read_original(input_root, entry) != raw:
        raise ValueError("Original bytes changed")
    dump(root, folder / "analysis.json", summary)
    return summary


def select_candidates(summaries):
    selected = []
    for kind, maximum in (("formula", 20), ("structure", 10), ("visual", 10)):
        pools = [[c for c in s["candidates"] if c["kind"] == kind] for s in summaries]
        # Round-robin across documents; prefer distinct page/hypothesis pairs.
        pools = [
            sorted(
                pool,
                key=lambda c: (
                    c["locator"]["page"],
                    c["hypothesis"],
                    c["candidate_id"],
                ),
            )
            for pool in pools
        ]
        chosen = []
        seen = set()
        for diverse in (True, False):
            while len(chosen) < maximum:
                progress = False
                for pool in pools:
                    match = next(
                        (
                            c
                            for c in pool
                            if not diverse
                            or (c["file_name"], c["locator"]["page"], c["hypothesis"])
                            not in seen
                        ),
                        None,
                    )
                    if match is None:
                        continue
                    pool.remove(match)
                    chosen.append(match)
                    seen.add(
                        (
                            match["file_name"],
                            match["locator"]["page"],
                            match["hypothesis"],
                        )
                    )
                    progress = True
                    if len(chosen) == maximum:
                        break
                if not progress:
                    break
        selected.extend(chosen)
    return selected


def review_package(root, input_root, entries, summaries):
    import pymupdf

    folder = private_directory(root / "review")
    selected = select_candidates(summaries)
    entry_map = {e["file_name"]: e for e in entries}
    cards = []
    for n, item in enumerate(selected):
        entry = entry_map[item["file_name"]]
        raw = read_original(input_root, entry)
        loc = item["locator"]
        with pymupdf.open(stream=raw, filetype="pdf") as pdf:
            page = pdf[loc["page"] - 1]
            rect = pymupdf.Rect(loc["bbox"] or page.rect)
            # A horizontal/vertical vector can have zero-area geometry. Preserve
            # its locator and include a small explicit context margin for viewing.
            rect = (
                pymupdf.Rect(rect.x0 - 4, rect.y0 - 4, rect.x1 + 4, rect.y1 + 4)
                & page.rect
            )
            if rect.is_empty or rect.is_infinite:
                raise ValueError("Invalid original-region crop")
            # Fixed low-resolution, bounded local comparison, never OCR.
            if rect.width * rect.height > 2_000_000:
                raise ValueError("Review crop pixel budget")
            png = page.get_pixmap(
                matrix=pymupdf.Matrix(1.25, 1.25), clip=rect, alpha=False
            ).tobytes("png")
        image_name = f"region-{n:02d}.png"
        write(root, folder / image_name, png)
        item["original_region_image"] = image_name
        cards.append(
            "<section><h2>"
            + html.escape(item["file_name"])
            + " / page "
            + str(loc["page"])
            + "</h2><p>"
            + html.escape(item["hypothesis"])
            + '</p><div class="pair"><img src="'
            + image_name
            + '" alt="Original region"><pre>'
            + html.escape(item["extracted_result"] or "No text: visual candidate")
            + "</pre></div><p>Independent reference and review decision: pending</p></section>"
        )
    page = (
        "<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'\"><title>Private original review</title><style>.pair{display:flex;gap:1rem}.pair>*{max-width:48%}pre{white-space:pre-wrap}section{border-bottom:1px solid #888}</style><h1>Private review — robfra — no confirmed gold</h1>"
        + "\n".join(cards)
    )
    write(root, folder / "index.html", page.encode())
    dump(
        root,
        folder / "candidates.json",
        dict(schema_version=1, inventory_digest=AUTHORIZED, candidates=selected),
    )
    return dict(Counter(c["kind"] for c in selected))


def seal(root, name):
    files = {
        p.relative_to(root).as_posix(): sha256(p.read_bytes())
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
    for path in root.rglob("*"):
        info = path.lstat()
        expected = 0o700 if path.is_dir() else 0o600
        if (
            path.is_symlink()
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != expected
        ):
            raise PermissionError("Unsafe private artifact")
    dump(
        root,
        root / name,
        dict(schema_version=1, inventory_digest=AUTHORIZED, files=files),
    )


def run(input_root, output_root, complete=None):
    os.umask(0o077)
    if pwd.getpwuid(os.getuid()).pw_name != "robfra":
        raise PermissionError("Authorized local operator required")
    input_root, output_root = checked_path(input_root), checked_path(output_root)
    if (
        input_root == output_root
        or input_root.is_relative_to(output_root)
        or output_root.is_relative_to(input_root)
        or output_root.is_relative_to(REPO)
        or REPO.is_relative_to(output_root)
    ):
        raise ValueError("Separate external private root required")
    entries = inventory()
    for entry in entries:
        read_original(input_root, entry)
    private_directory(output_root)
    budget(output_root)
    if complete is None:
        root = output_root / ("run-" + uuid.uuid4().hex)
        root.mkdir(mode=0o700)
        revision = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip()
        dump(
            root,
            root / "execution.json",
            dict(
                schema_version=1,
                inventory_digest=AUTHORIZED,
                operator="robfra",
                reviewer="robfra",
                authorization_reference="DEV-03E operator authorization 2026-10-20",
                input_root=str(input_root),
                implementation_revision=revision,
                pdf_worker_sha256=sha256(
                    (REPO / "src/tools_materials/pdf_worker.py").read_bytes()
                ),
                visual_worker_sha256=sha256(
                    (REPO / "src/tools_materials/visual_worker.py").read_bytes()
                ),
                runner_sha256=sha256(Path(__file__).read_bytes()),
                python_version=sys.version,
                course_id="loviscach_mathe_1",
                binding="isolated_worker_no_C23_publication",
            ),
        )
        summary = process_one(root, input_root, entries[0])
        dump(
            root,
            root / "first-complete.json",
            dict(
                summary_sha256=fingerprint(summary),
                safe_to_continue=not bool(summary["technical_findings"]),
            ),
        )
        seal(root, "first-manifest.json")
        return root, [summary]
    if not re.fullmatch(r"run-[a-f0-9]{32}", complete):
        raise ValueError("Explicit run identity required")
    if not (output_root / complete).is_dir():
        raise ValueError("Existing first-stage run required")
    root = private_directory(output_root / complete)
    execution = json.loads((root / "execution.json").read_bytes())
    if execution["inventory_digest"] != AUTHORIZED or execution["input_root"] != str(
        input_root
    ):
        raise ValueError("Run binding mismatch")
    if execution["runner_sha256"] != sha256(Path(__file__).read_bytes()):
        raise ValueError("Runner changed between explicit stages")
    for name in ("pdf", "visual"):
        if execution[name + "_worker_sha256"] != sha256(
            (REPO / f"src/tools_materials/{name}_worker.py").read_bytes()
        ):
            raise ValueError("Integrated worker changed")
    first_manifest = json.loads((root / "first-manifest.json").read_bytes())
    for name, digest in first_manifest["files"].items():
        path = checked_path(root / name)
        if not path.is_relative_to(root) or sha256(path.read_bytes()) != digest:
            raise ValueError("First-run artifact mismatch")
    if not json.loads((root / "first-complete.json").read_bytes())["safe_to_continue"]:
        raise ValueError("First run requires technical investigation")
    write(
        root,
        root / "completion.lock",
        b"Exclusive explicit completion; retained, never auto-reused\n",
    )
    summaries = [
        json.loads(
            (
                root / entries[0]["file_name"].removesuffix(".pdf") / "analysis.json"
            ).read_bytes()
        )
    ]
    summaries += [process_one(root, input_root, entry) for entry in entries[1:]]
    review = review_package(root, input_root, entries, summaries)
    for entry in entries:
        read_original(input_root, entry)
    public = [
        {k: v for k, v in s.items() if k not in {"candidates"}} for s in summaries
    ]
    report = dict(
        schema_version=1,
        inventory_digest=AUTHORIZED,
        implementation_revision=execution["implementation_revision"],
        documents=public,
        review_candidates=review,
        independent_gold_references=0,
        quality_denominator=0,
        quality_rate=None,
        status="real_parsing_evaluation_completed_gold_pending",
        C10="not_run_no_material_binding",
        C23="not_imported",
        retrieval="not_run",
    )
    dump(root, root / "report.json", dict(report=report, sha256=fingerprint(report)))
    seal(root, "manifest.json")
    return root, summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--complete", help="Exact first-stage run directory name")
    args = parser.parse_args(argv)

    def deny_network(event, arguments):
        if event.startswith(("socket.", "urllib.", "http.client.")):
            raise PermissionError("Network disabled for local evaluation")

    sys.addaudithook(deny_network)
    # Bound local review rendering too; the integrated workers keep their own limits.
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024**2, 1024 * 1024**2))
    try:
        root, summaries = run(args.input_root, args.output_root, args.complete)
    except Exception as error:
        print(
            "Local evaluation stopped; private evidence retained. Error class: "
            + type(error).__name__
        )
        return 2
    print(
        json.dumps(
            dict(
                run_name=root.name,
                processed_documents=len(summaries),
                summaries=[
                    {
                        k: s[k]
                        for k in (
                            "file_name",
                            "page_count",
                            "total_parts",
                            "text_blocks",
                            "formula_candidates",
                            "structure_candidates",
                            "visual_observations",
                            "image_references",
                            "table_candidates",
                            "parser_warning_count",
                            "technical_findings",
                        )
                    }
                    for s in summaries
                ],
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
