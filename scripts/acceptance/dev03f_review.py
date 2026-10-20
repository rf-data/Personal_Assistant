"""Private DEV-03F offline review exports over sealed DEV-03E observations.

No parser, server, database, import, index or substitute for B1 authorization.
Human attestations remain separate from provenance-ready C23 gold.
"""

import argparse
import html
import json
import os
import pwd
import re
import resource
import shutil
import sys
import uuid
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath

from src.content_store.artifacts import _open_directory, _private, explicit_root
from src.content_store.models import ContentLocator, canonical, fingerprint, sha256
from src.content_store.reader import private_bytes
from src.evaluation_store.models import Annotation
from src.model_evaluation.content_retrieval import IndependentReview
from src.model_evaluation.material_evaluation import GoldDataset, GoldReference
from src.model_materials.materials import ParserConfig
from src.tools_materials.quality import _json

REPO = Path(__file__).resolve().parents[2]
DIGEST = "a37319b9b0d18fb246f6071638a35ae30b39f39f01187a3579cf5a501862500e"
RUN_DIGEST = "6551d52db9e7cb416d91ca807adea06d30bec9589417850f8f6e5ca3726b458b"
DAY = date(2026, 10, 20)
VERSION = "dev03f-loviscach-review-2026-10-20-r1"
FORMULA_DECISIONS = {
    "exact_match",
    "mathematically_equivalent",
    "incorrect",
    "incomplete",
    "not_evaluable",
}


def private_dir(path):
    path = explicit_root(path)
    fd = _open_directory(path)
    try:
        _private(fd, directory=True)
    finally:
        os.close(fd)
    return path


def read(path):
    return _json(private_bytes(path, 64 * 1024**2))


def write(folder, name, data):
    if PurePosixPath(name).name != name or name in {"", ".", ".."}:
        raise ValueError("Explicit leaf name required")
    if len(data) + sum(
        p.stat().st_size for p in folder.iterdir() if p.is_file()
    ) > 64 * 1024**2 or shutil.disk_usage(folder).free < 256 * 1024**2 + len(data):
        raise OSError("Private export capacity limit")
    fd = _open_directory(private_dir(folder))
    try:
        out = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
        )
        with os.fdopen(out, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(fd)
    finally:
        os.close(fd)


def dump(folder, name, value):
    write(folder, name, canonical(value) + b"\n")


def checked_relative(root, name):
    relative = PurePosixPath(name)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in name
        or relative.as_posix() != name
    ):
        raise ValueError("Relative artifact path required")
    return root / name


def verify_manifest(root):
    private_dir(root)
    manifest = read(root / "manifest.json")
    if manifest["inventory_digest"] != DIGEST:
        raise ValueError("Inventory binding mismatch")
    for name, digest in manifest["files"].items():
        if sha256(private_bytes(checked_relative(root, name), 64 * 1024**2)) != digest:
            raise ValueError("Private artifact integrity mismatch")
    return manifest


def source_inventory():
    data = _json(
        (
            REPO / "docs/cs50/evaluation/dev03/loviscach/corpus_inventory.v1.json"
        ).read_bytes()
    )
    if fingerprint(data["inventory"]) != DIGEST or data["sha256"] != DIGEST:
        raise ValueError("Authorized inventory mismatch")
    return data["inventory"]["entries"]


def original(root, entry):
    # Original permissions are preserved. Only the exact hash-bound regular file
    # is read, via a no-follow descriptor; private output checks are separate.
    parent = _open_directory(root)
    try:
        fd = os.open(
            entry["file_name"],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent,
        )
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            import stat

            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_size != entry["raw_artifact"]["size_bytes"]
            ):
                raise ValueError("Original regular-file/size mismatch")
            data = stream.read(16 * 1024**2 + 1)
        if sha256(data) != entry["raw_artifact"]["sha256"]:
            raise ValueError("Original hash mismatch")
        return data
    finally:
        os.close(parent)


def case(
    entry,
    kind,
    pointer,
    location,
    prediction,
    worker_digest,
    criterion,
    hypothesis,
    syntax=None,
    candidate_id=None,
    observation=None,
):
    locator = ContentLocator(
        raw_artifact_sha256=entry["raw_artifact"]["sha256"],
        origin_pointer=pointer,
        page=location["page"],
        bbox=location["bbox"],
        coordinate_system="pdf_points_top_left_unrotated",
        time_status="not_applicable",
    )
    return dict(
        review_id="lov_"
        + fingerprint([entry["source_id"], locator.raw_artifact_sha256, kind, pointer])[
            :48
        ],
        source_id=entry["source_id"],
        file_name=entry["file_name"],
        original_sha256=locator.raw_artifact_sha256,
        source_version_id=None,
        parsed_version_id=None,
        kind=kind,
        locator=locator.model_dump(mode="json"),
        worker_response_sha256=worker_digest,
        prediction=prediction[:2000] if prediction else None,
        excerpt_truncated=bool(prediction and len(prediction) > 2000),
        selection_criterion=criterion,
        hypothesis=hypothesis,
        syntax_status=syntax,
        source_candidate_id=candidate_id,
        visual_observation=observation,
        reference_status="pending_review",
        assigned_reviewer="robfra",
    )


def select_cases(entries, documents):
    chosen = []
    for entry, doc in zip(entries, documents, strict=True):
        analysis, pdf, visual = doc
        formulas = [c for c in analysis["candidates"] if c["kind"] == "formula"]
        if not formulas:
            raise ValueError("Document lacks the expected actual formula observations")
        control = next(
            (c for c in formulas if c["syntax_status"] == "syntax_valid"),
            formulas[len(formulas) // 2],
        )
        selected = [(control, "systematic_control")]
        selected += [
            (c, "candidate")
            for c in formulas
            if c["candidate_id"] != control["candidate_id"]
        ][:4]
        for c, criterion in selected:
            chosen.append(
                case(
                    entry,
                    "formula",
                    c["locator"]["origin_pointer"],
                    c["locator"],
                    c["extracted_result"],
                    analysis["pdf_observations_sha256"],
                    criterion,
                    c["hypothesis"],
                    c["syntax_status"],
                    c["candidate_id"],
                )
            )
        # A control is not asserted correct. Pick a middle ordinary paragraph
        # without a source-backed math classification, task label or repetition.
        counts = Counter(p.get("text", "") for p in pdf["parts"])
        ordinary = [
            (i, p)
            for i, p in enumerate(pdf["parts"])
            if p["type"] == "paragraph"
            and p.get("text")
            and len(p["text"]) <= 2000
            and counts[p["text"]] == 1
            and not re.search(
                r"(?m)^\s*(?:Aufgabe\s+)?\d{1,2}[.)]\s|[=√∫∑²³]", p["text"]
            )
        ]
        if not ordinary:
            raise ValueError("No unflagged systematic text control available")
        i, p = ordinary[len(ordinary) // 2]
        chosen.append(
            case(
                entry,
                "structure",
                f"/parts/{i}",
                p["location"],
                p["text"],
                analysis["pdf_observations_sha256"],
                "systematic_control",
                None,
            )
        )
    # Fill remaining structure/visual quotas round-robin across sources.
    for kind, maximum in (("structure", 10), ("visual", 10)):
        pools = []
        for entry, (analysis, _pdf, visual) in zip(entries, documents, strict=True):
            rows = []
            if kind == "structure":
                for c in analysis["candidates"]:
                    if c["kind"] == kind:
                        rows.append(
                            case(
                                entry,
                                kind,
                                c["locator"]["origin_pointer"],
                                c["locator"],
                                c["extracted_result"],
                                analysis["pdf_observations_sha256"],
                                "candidate",
                                c["hypothesis"],
                                candidate_id=c["candidate_id"],
                            )
                        )
            else:
                observations = visual["observations"]
                order = list(range(len(observations)))
                if order:
                    middle = order.pop(len(order) // 2)
                    order.insert(0, middle)
                for n, i in enumerate(order):
                    o = observations[i]
                    rows.append(
                        case(
                            entry,
                            kind,
                            f"/observations/{i}",
                            o["location"],
                            None,
                            analysis["visual_observations_sha256"],
                            "systematic_control" if n == 0 else "candidate",
                            None if n == 0 else "needs_visual_review_" + o["tag"],
                            observation=o,
                        )
                    )
            pools.append(rows)
        while sum(c["kind"] == kind for c in chosen) < maximum:
            progress = False
            for pool in pools:
                while pool and any(
                    c["review_id"] == pool[0]["review_id"] for c in chosen
                ):
                    pool.pop(0)
                if pool:
                    chosen.append(pool.pop(0))
                    progress = True
                if sum(c["kind"] == kind for c in chosen) == maximum:
                    break
            if not progress:
                break
    return chosen


def gold_template(cases):
    return GoldDataset(
        schema_version=1,
        dataset_version=VERSION,
        references=tuple(
            GoldReference(
                gold_id=c["review_id"],
                entry_id=c["file_name"].removesuffix(".pdf").replace(".", "_"),
                source_id=c["source_id"],
                original_sha256=c["original_sha256"],
                dimension="image"
                if c["kind"] == "visual"
                else c["kind"]
                if c["kind"] == "formula"
                else "structure",
                source_reference="DEV-03F original-only region " + c["review_id"],
                created_date=DAY,
                reference_status="pending_review",
                method="parser_preannotation",
                notes=(
                    "Unpublished worker observations; no SourceVersion/ParsedVersion and no independent gold yet.",
                ),
            )
            for c in cases
        ),
    )


def render(folder, input_root, entries, cases):
    import pymupdf

    entry_map = {e["file_name"]: e for e in entries}
    originals = []
    comparisons = []
    for n, c in enumerate(cases):
        raw = original(input_root, entry_map[c["file_name"]])
        with pymupdf.open(stream=raw, filetype="pdf") as doc:
            page = doc[c["locator"]["page"] - 1]
            if page.rotation:
                raise ValueError(
                    "Rotated review crop needs an explicit supported renderer"
                )
            r = pymupdf.Rect(c["locator"]["bbox"])
            r = pymupdf.Rect(r.x0 - 4, r.y0 - 4, r.x1 + 4, r.y1 + 4) & page.rect
            if r.is_empty or r.width * r.height > 2_000_000:
                raise ValueError("Review crop limit")
            png = page.get_pixmap(
                matrix=pymupdf.Matrix(1.25, 1.25), clip=r, alpha=False
            ).tobytes("png")
        image = f"original-{n:02d}.png"
        write(folder, image, png)
        c["original_region_image"] = image
        heading = (
            "<h2>"
            + html.escape(c["review_id"])
            + "</h2><p>"
            + html.escape(c["file_name"])
            + " / Seite "
            + str(c["locator"]["page"])
            + "</p>"
        )
        picture = '<img src="' + image + '" alt="Originalregion">'
        originals.append(
            "<section>"
            + heading
            + picture
            + "<p>Referenz selbst am Original bestimmen; Antwortvorlage im Editor ausfüllen.</p></section>"
        )
        comparisons.append(
            "<section>"
            + heading
            + '<div class="pair">'
            + picture
            + "<pre>"
            + html.escape(
                c["prediction"]
                if c["prediction"] is not None
                else json.dumps(c["visual_observation"], ensure_ascii=False, indent=2)
            )
            + "</pre></div></section>"
        )
    header = "<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'\"><style>img{max-width:95%}.pair{display:flex;gap:1rem}.pair>*{max-width:48%}pre{white-space:pre-wrap}section{border-bottom:1px solid #888}</style>"
    write(
        folder,
        "originals.html",
        (
            header
            + "<h1>1. Unabhängige Originalannotation – robfra</h1>"
            + "".join(originals)
        ).encode(),
    )
    write(
        folder,
        "comparison.html",
        (
            header
            + "<h1>2. Vergleich nach eigener Originalannotation</h1>"
            + "".join(comparisons)
        ).encode(),
    )


def prepare(run_root, input_root, output_root):
    private_dir(run_root)
    private_dir(output_root)
    if output_root == run_root or output_root.is_relative_to(run_root):
        raise ValueError("New sibling output required")
    if shutil.disk_usage(output_root).free < 320 * 1024**2:
        raise OSError("Private capacity reserve")
    verify_manifest(run_root)
    report = read(run_root / "report.json")
    if (
        fingerprint(report["report"]) != report["sha256"]
        or report["sha256"] != RUN_DIGEST
    ):
        raise ValueError("Report digest mismatch")
    entries = source_inventory()
    report_documents = {d["source_id"]: d for d in report["report"]["documents"]}
    documents = []
    for e in entries:
        original(input_root, e)
        folder = run_root / e["file_name"].removesuffix(".pdf")
        analysis = read(folder / "analysis.json")
        pdf = read(folder / "pdf/response.json")
        visual = read(folder / "visual/response.json")
        if (
            fingerprint(pdf) != analysis["pdf_observations_sha256"]
            or fingerprint(visual) != analysis["visual_observations_sha256"]
            or analysis["original_sha256"] != e["raw_artifact"]["sha256"]
        ):
            raise ValueError("Actual worker binding mismatch")
        if {
            k: v for k, v in analysis.items() if k != "candidates"
        } != report_documents.get(e["source_id"]):
            raise ValueError("Analysis differs from the bound DEV-03E report")
        for c in analysis["candidates"]:
            match = re.fullmatch(r"/parts/([0-9]+)", c["locator"]["origin_pointer"])
            if match:
                part = pdf["parts"][int(match[1])]
                if (
                    c["extracted_result"] != (part.get("text", "")[:2000] or None)
                    or c["locator"]["page"] != part["location"]["page"]
                    or c["locator"]["bbox"] != part["location"]["bbox"]
                ):
                    raise ValueError("Candidate differs from actual worker output")
        documents.append((analysis, pdf, visual))
    cases = select_cases(entries, documents)
    if Counter(c["kind"] for c in cases) != dict(formula=20, structure=10, visual=10):
        raise ValueError("Bounded review selection incomplete")
    path = output_root / ("review-f-" + uuid.uuid4().hex)
    path.mkdir(mode=0o700)
    render(path, input_root, entries, cases)
    execution = read(run_root / "execution.json")
    body = dict(
        schema_version=1,
        dataset_version=VERSION,
        inventory_digest=DIGEST,
        source_run_report_sha256=report["sha256"],
        exporter_sha256=sha256(Path(__file__).read_bytes()),
        parser_execution=execution["implementation_revision"],
        pdf_worker_sha256=execution["pdf_worker_sha256"],
        visual_worker_sha256=execution["visual_worker_sha256"],
        parser_config=ParserConfig(name="pdf", version="2").model_dump(mode="json"),
        model_revision=None,
        cases=cases,
        source_versions_bound=False,
        status="gold_review_prepared",
    )
    package = dict(package=body, sha256=fingerprint(body))
    dump(path, "package.json", package)
    dump(path, "pending_gold.v1.json", gold_template(cases).model_dump(mode="json"))
    dump(
        path,
        "responses.blank.json",
        dict(
            schema_version=1,
            package_sha256=package["sha256"],
            previous_sha256=None,
            responses=[
                dict(
                    review_id=c["review_id"],
                    confirm=False,
                    original_reviewed_independently=False,
                    annotation=None,
                    formula_decision=None,
                    latex_reference=None,
                    equivalence_reason=None,
                    evidence_reference=None,
                    reviewed_at=None,
                )
                for c in cases
            ],
        ),
    )
    pending = IndependentReview(
        status="pending_review", method="independent_source_annotation"
    ).model_dump(mode="json")
    dump(
        path,
        "query_worksheet.json",
        dict(
            schema_version=1,
            package_sha256=package["sha256"],
            status="pending_review",
            queries=[
                dict(
                    query_id=f"q-{n}-{intent}",
                    source_id=e["source_id"],
                    source_version_id=None,
                    parsed_version_id=None,
                    intent=intent,
                    text=None,
                    relevance_judgments=[],
                    pool_complete=False,
                    review=pending,
                )
                for n, e in enumerate(entries)
                for intent in ("term", "task", "symbol", "concept", "equation")
            ],
        ),
    )
    write(
        path,
        "README.md",
        (
            """# Privater DEV-03F-Reviewexport
1. originals.html öffnen. Original selbst beurteilen, Referenz nicht vom Parser kopieren.
2. Antworten als neue private Datei anhand responses.blank.json im Editor anlegen.
   annotation verwendet B1 Annotation: schema_version=1, mode=independent_original,
   quality=correct/partial/incorrect/undetermined, expected_content=selbst geprüfte
   Referenz oder null, error_categories=[], comment=Begründung. Keine Vorbelegung.
3. Erst danach comparison.html konsultieren und explizit urteilen.
   Formelentscheid: exact_match/mathematically_equivalent/incorrect/incomplete/not_evaluable.
   Bei Äquivalenz Begründung; reviewed_at als tatsächlicher ISO-Zeitpunkt mit Zeitzone.
4. confirm und original_reviewed_independently nur selbst auf true setzen. Beleg angeben.
   Kein automatischer Goldentscheid. capture verlangt ausdrückliche lokale Attestation.
5. Versiegelte Dateien nicht bearbeiten. Jede Erfassung erzeugt eine neue Datei,
   Vorrevision ausdrücklich per previous_sha256 und --previous binden. Konfliktzweige
   bleiben getrennte Offlinebelege, keine automatische Auflösung oder B1-Headbehauptung.
6. SourceVersion/ParsedVersion fehlen: auch erfasste menschliche Belege bleiben für
   C23-Gold/Qualitätsmetriken gesperrt. Kein B1-Task, kein APIrechteersatz.
7. query_worksheet.json enthält 20 leere Arbeitsaufträge, keine Evaluationsqueries.
   Fragen/Relevanzen vor Retrieval am Original bestimmen. Kein Index oder Retrieval
   ohne zusätzliche isolierte Roots, technische Bindungen und ausdrückliche Freigabe.
Alle Exporte privat 0700/0600, keine Cloud, keine automatische Löschung.
"""
        ).encode(),
    )
    files = {
        p.name: sha256(private_bytes(p, 64 * 1024**2))
        for p in path.iterdir()
        if p.is_file()
    }
    dump(
        path,
        "manifest.json",
        dict(schema_version=1, inventory_digest=DIGEST, files=files),
    )
    for e in entries:
        original(input_root, e)
    return path, package


def capture(
    package_root, responses_path, output_path, previous_path=None, *, attest=False
):
    if not attest or pwd.getpwuid(os.getuid()).pw_name != "robfra":
        raise PermissionError("Explicit local reviewer attestation required")
    verify_manifest(package_root)
    if responses_path.parent != package_root.parent or (
        previous_path and previous_path.parent != package_root.parent
    ):
        raise ValueError("Explicit private sibling input required")
    package = read(package_root / "package.json")
    if fingerprint(package["package"]) != package["sha256"]:
        raise ValueError("Package digest mismatch")
    response_bytes = private_bytes(responses_path, 1024**2)
    data = _json(response_bytes)
    if (
        set(data)
        != {"schema_version", "package_sha256", "previous_sha256", "responses"}
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or data["package_sha256"] != package["sha256"]
    ):
        raise ValueError("Response binding/schema mismatch")
    parent = None
    reviews = {}
    if previous_path:
        previous = read(previous_path)
        parent = previous["sha256"]
        if (
            fingerprint(previous["snapshot"]) != parent
            or previous["snapshot"]["package_sha256"] != package["sha256"]
        ):
            raise ValueError("Previous revision mismatch")
        reviews = {r["review_id"]: r for r in previous["snapshot"]["reviews"]}
        if len(reviews) != len(previous["snapshot"]["reviews"]):
            raise ValueError("Duplicate previous reviews")
    if data["previous_sha256"] != parent:
        raise ValueError("Explicit previous revision required")
    cases = {c["review_id"]: c for c in package["package"]["cases"]}
    seen = set()
    changed = 0
    if not isinstance(data["responses"], list) or not 1 <= len(data["responses"]) <= 40:
        raise ValueError("Bounded response list required")
    for rid, row in reviews.items():
        if rid not in cases or row["binding"] != cases[rid]:
            raise ValueError("Previous review binding mismatch")
        old_annotation = Annotation.model_validate(row["annotation"])
        review = IndependentReview.model_validate(row["review"])
        if (
            review.status != "confirmed"
            or review.reviewer != "robfra"
            or review.method != "independent_source_annotation"
            or old_annotation.mode != "independent_original"
        ):
            raise ValueError("Previous reviewer mismatch")
    for row in data["responses"]:
        if set(row) != {
            "review_id",
            "confirm",
            "original_reviewed_independently",
            "annotation",
            "formula_decision",
            "latex_reference",
            "equivalence_reason",
            "evidence_reference",
            "reviewed_at",
        }:
            raise ValueError("Unknown response fields")
        rid = row["review_id"]
        if rid not in cases or rid in seen:
            raise ValueError("Unknown/duplicate case")
        seen.add(rid)
        if row["confirm"] is False:
            continue
        if (
            row["confirm"] is not True
            or row["original_reviewed_independently"] is not True
        ):
            raise ValueError("Explicit independent decision required")
        annotation = Annotation.model_validate(row["annotation"])
        c = cases[rid]
        if annotation.mode != "independent_original" or annotation.quality is None:
            raise ValueError("Independent explicit quality required")
        if annotation.quality != "undetermined" and not annotation.expected_content:
            raise ValueError("Independent reference required")
        for name in ("latex_reference", "equivalence_reason"):
            if row[name] is not None and (
                not isinstance(row[name], str)
                or not row[name].strip()
                or len(row[name]) > 2048
            ):
                raise ValueError("Bounded human reference fields required")
        if c["kind"] == "formula":
            mapping = {
                "exact_match": "correct",
                "mathematically_equivalent": "correct",
                "incorrect": "incorrect",
                "incomplete": "partial",
                "not_evaluable": "undetermined",
            }
            if (
                row["formula_decision"] not in FORMULA_DECISIONS
                or annotation.quality != mapping[row["formula_decision"]]
            ):
                raise ValueError("Formula decision/quality conflict")
            if (
                row["formula_decision"] == "mathematically_equivalent"
                and not row["equivalence_reason"]
            ):
                raise ValueError("Human equivalence justification required")
        elif row["formula_decision"] is not None:
            raise ValueError("Formula decision on nonformula")
        moment = datetime.fromisoformat(row["reviewed_at"])
        if moment.utcoffset() is None:
            raise ValueError("Actual timezone-aware review time required")
        review = IndependentReview(
            status="confirmed",
            method="independent_source_annotation",
            reviewer="robfra",
            evidence_reference=row["evidence_reference"],
            review_date=moment.date(),
        )
        reviews[rid] = dict(
            review_id=rid,
            annotation=annotation.model_dump(mode="json"),
            review=review.model_dump(mode="json"),
            reviewed_at=moment.astimezone(UTC).isoformat(),
            formula_decision=row["formula_decision"],
            latex_reference=row["latex_reference"],
            equivalence_reason=row["equivalence_reason"],
            binding=c,
        )
        changed += 1
    if not changed:
        raise ValueError("No explicit new human decision")
    gold = gold_template(package["package"]["cases"])
    refs = []
    for ref in gold.references:
        if ref.gold_id in reviews:
            r = reviews[ref.gold_id]
            ref = ref.model_copy(
                update=dict(
                    expected_content=r["annotation"]["expected_content"],
                    method="independent_source_annotation",
                    reviewer=r["review"]["reviewer"],
                    review_reference=r["review"]["evidence_reference"],
                    review_date=date.fromisoformat(r["review"]["review_date"]),
                    notes=(
                        "Human offline attestation recorded; provenance binding still pending. Not confirmed C23 gold.",
                    ),
                )
            )
        refs.append(ref)
    gold = GoldDataset.model_validate(
        dict(schema_version=1, dataset_version=VERSION, references=refs)
    )
    snapshot = dict(
        schema_version=1,
        package_sha256=package["sha256"],
        previous_sha256=parent,
        responses_sha256=sha256(response_bytes),
        captured_by="robfra",
        captured_at=datetime.now(UTC).isoformat(),
        reviews=sorted(reviews.values(), key=lambda r: r["review_id"]),
        gold=gold.model_dump(mode="json"),
        confirmed_c23_gold=0,
        provenance_status="pending_versions",
        quality_rate=None,
    )
    output_path = Path(output_path)
    if output_path.parent != package_root.parent:
        raise ValueError("New private sibling revision required")
    private_dir(output_path.parent)
    dump(
        output_path.parent,
        output_path.name,
        dict(snapshot=snapshot, sha256=fingerprint(snapshot)),
    )
    return snapshot


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("prepare")
    for name in ("run-root", "input-root", "output-root"):
        a.add_argument("--" + name, type=Path, required=True)
    a = sub.add_parser("capture")
    for name in ("package-root", "responses", "output"):
        a.add_argument("--" + name, type=Path, required=True)
    a.add_argument("--previous", type=Path)
    a.add_argument("--attest-independent-human-review", action="store_true")
    args = p.parse_args(argv)

    def audit(event, arguments):
        if event.startswith(("socket.", "urllib.", "http.client.")):
            raise PermissionError("Network forbidden")

    sys.addaudithook(audit)
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024**2, 1024 * 1024**2))
    try:
        if args.command == "prepare":
            path, package = prepare(args.run_root, args.input_root, args.output_root)
            print(
                json.dumps(
                    dict(
                        status="gold_review_prepared",
                        package_name=path.name,
                        cases=len(package["package"]["cases"]),
                        confirmed_gold=0,
                    )
                )
            )
        else:
            result = capture(
                args.package_root,
                args.responses,
                args.output,
                args.previous,
                attest=args.attest_independent_human_review,
            )
            print(
                json.dumps(
                    dict(
                        offline_human_reviews=len(result["reviews"]),
                        confirmed_c23_gold=0,
                    )
                )
            )
    except Exception as error:
        print(
            "Offline export stopped; no contents emitted. Error class: "
            + type(error).__name__
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
