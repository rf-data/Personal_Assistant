"""Printable UTF-8 exports; TeX data never becomes arbitrary TeX commands."""

import html
import re
from pathlib import Path

from src.lecture_summary.models import TEMPLATE_VERSION, Formula
from src.lecture_summary.validation import safe_formula

TEMPLATE = Path(__file__).parent / "templates" / (TEMPLATE_VERSION + ".tex")


def filename(summary, extension):
    if extension not in {"md", "tex", "json"}:
        raise ValueError("Unsupported export extension")
    return f"lecture-summary-{summary.summary_id[:16]}.{extension}"


def tex_escape(text):
    escaped = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(
        escaped.get(c, c) if ord(c) >= 32 or c == "\n" else " " for c in text
    )


def md_escape(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"([\\`*_{}\[\]<>#!|$])", r"\\\1", text)
    # Each continuation stays inside its existing list item; no injected blocks.
    return text.replace("\n", " ").replace("\r", " ")


def sections(draft):
    yield "Lernziele", draft.learning_objectives
    yield "Vorkenntnisse", draft.prerequisites
    for topic in draft.topics:
        yield topic.title, topic.explanations
        yield from (
            ("Begriffe und Definitionen", topic.definitions),
            ("Formeln und Herleitungen", topic.formulas),
            ("Beispiele und Anwendungen", topic.examples),
            ("Verständnisprobleme", topic.misconceptions),
            ("Kontrollfragen", topic.questions),
        )
    yield "Wichtigste Erkenntnisse", draft.takeaways


def render(summary, *, latex=False):
    if summary.validation_status == "failed":
        raise ValueError("Failed summary cannot be exported")
    escape = tex_escape if latex else md_escape
    labels = {e.source_id: f"Q{i}" for i, e in enumerate(summary.evidence, 1)}
    title = escape(summary.content.title)
    output = [r"\section*{" + title + "}" if latex else "# " + title]
    output.append(escape("Lektionen: " + ", ".join(summary.selection.lecture_ids)))
    output.append(
        escape("Qualität: " + summary.validation_status + " · Modell: " + summary.model)
    )
    output.extend(escape(m) for m in summary.validation_messages)
    for heading, items in sections(summary.content):
        if not items:
            continue
        output.append(
            r"\subsection*{" + escape(heading) + "}"
            if latex
            else "## " + escape(heading)
        )
        for claim in items:
            refs = ", ".join(labels[s] for s in claim.source_ids)
            label = f"[{claim.kind}; {claim.quality}; {refs or 'ohne Quellenbeleg'}]"
            line = (
                escape(claim.text)
                + " "
                + (escape(label) if latex else "`" + label + "`")
            )
            output.append((r"\par " if latex else "- ") + line)
            if isinstance(claim, Formula):
                if safe_formula(claim.latex):
                    output.append(
                        (r"\[" + claim.latex + r"\]")
                        if latex
                        else "$$\n" + claim.latex + "\n$$"
                    )
                else:
                    output.append(
                        escape("Nicht sicher darstellbare Formel: " + claim.latex)
                    )
                output.append(
                    escape(
                        "Notation: "
                        + claim.notation
                        + " Voraussetzungen: "
                        + claim.assumptions
                    )
                )
    output.append(
        r"\section*{Quellenverzeichnis}" if latex else "## Quellenverzeichnis"
    )
    for evidence in summary.evidence:
        loc = evidence.locator
        position = f"{loc.origin_pointer}; Zeitstatus {loc.time_status}"
        if loc.page is not None:
            position += f"; Seite {loc.page}"
        if loc.line_start is not None:
            position += f"; Zeilen {loc.line_start}–{loc.line_end}"
        if loc.start is not None:
            position += f"; {loc.start}–{loc.end} s; Segment {loc.original_segment_id}"
        if loc.dom:
            position += "; DOM " + loc.dom
        info = (
            f"{labels[evidence.source_id]}: {evidence.title}; "
            f"{evidence.provider_id}/{evidence.course_id}/{evidence.lecture_id}; {position}; "
            f"Artefakt {evidence.artifact_id}; Version {evidence.artifact_sha256}; "
            f"Chunk {evidence.chunk_id}; Quelle {evidence.source_id}; Rolle {evidence.artifact_role}"
        )
        if evidence.source_url:
            info += "; URL " + evidence.source_url
        for label, value in (
            ("native Source-ID", evidence.native_source_id),
            ("native Dokument-ID", evidence.native_document_id),
            ("Media-ID", evidence.media_id),
            ("Original-SHA256", evidence.original_artifact_sha256),
        ):
            if value:
                info += f"; {label} {value}"
        output.append((r"\par\small " if latex else "- ") + escape(info))
    body = "\n\n".join(output) + "\n"
    result = (
        TEMPLATE.read_text(encoding="utf-8").replace("@@BODY@@", body)
        if latex
        else body
    )
    if len(result.encode("utf-8")) > 500000:
        raise ValueError("Export byte limit exceeded")
    return result
