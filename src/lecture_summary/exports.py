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


def tex_evidence(text):
    """Break long data tokens without accepting TeX commands from the source."""
    return "".join(
        r"\allowbreak{}".join(
            tex_escape(token[i : i + 12]) for i in range(0, len(token), 12)
        )
        if len(token) >= 25 and not token.isspace()
        else tex_escape(token)
        for token in re.split(r"(\s+)", text)
    )


def cited_source_ids(summary):
    """Include every rendered claim, including retained intermediate formulas."""
    cited = {
        source_id
        for _, items in sections(summary.content)
        for c in items
        for source_id in c.source_ids
    }
    if summary.processing is not None:
        cited.update(
            source_id
            for f in summary.processing.formula_variants
            for source_id in f.source_ids
        )
    return cited


def seconds(value):
    # Display only: exact locator values and evidence identity remain untouched.
    return f"{value:.2f}".rstrip("0").rstrip(".") or "0"


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


def render(summary, *, latex=False, include_all_evidence=False):
    if summary.validation_status == "failed":
        raise ValueError("Failed summary cannot be exported")
    escape = tex_escape if latex else md_escape
    labels = {e.source_id: f"Q{i}" for i, e in enumerate(summary.evidence, 1)}
    cited = cited_source_ids(summary)
    mock = summary.model == "mock-extractive-v1"
    title = escape(summary.content.title)
    output = [r"\section*{" + title + "}" if latex else "# " + title]
    output.append(escape("Lektionen: " + ", ".join(summary.selection.lecture_ids)))
    output.append(
        escape("Qualität: " + summary.validation_status + " · Modell: " + summary.model)
    )
    output.extend(escape(m) for m in summary.validation_messages)
    if mock:
        output.append(
            escape(
                "Demonstrationsmaterial (Mock): begrenzte wörtliche, möglicherweise unvollständige "
                "Ausschnitte; keine vollständige didaktische Synthese oder fachliche Abdeckung. "
                "Im einfachen Modus höchstens zwei Ausschnitte je Lektion (Kompakt), vier "
                "(Ausführlich); hierarchisch höchstens zwei je Abschnitt."
            )
        )
    if summary.processing is not None:
        p = summary.processing
        output.append(
            escape(
                f"Hierarchischer Lauf: {p.status}; Abschnitte {len(p.completed_section_ids)}/{len(p.section_ids)}; "
                f"davon im Endergebnis zitiert {len(p.final_section_ids)}; "
                f"Originalblöcke verarbeitet {len(p.mapped_source_ids)}; Zwischenstände zitieren "
                f"{len(p.intermediate_source_ids)}; Endergebnis zitiert {len(p.final_source_ids)}; "
                f"nicht im Endergebnis zitiert {len(p.uncited_source_ids)}. "
                f"Reservierte Aufrufe {p.requests_reserved}, neu in diesem Aufruf {p.requests_this_invocation}, "
                f"Cache-Stufen {p.cached_stages}; Gesamtobergrenze {p.planned_token_upper_bound}; "
                f"Kostenobergrenze {p.cost_upper_bound_microusd} Mikro-USD (konfigurierte Annahmen)."
            )
        )
        output.extend(escape(n) for n in p.notices)
        if p.formula_variants:
            output.append(
                r"\subsection*{Formelvarianten aus Zwischenständen}"
                if latex
                else "## Formelvarianten aus Zwischenständen"
            )
            for f in p.formula_variants:
                refs = ", ".join(labels[s] for s in f.source_ids)
                output.append(
                    escape(
                        f"{f.text}; {f.quality}; {refs}; Notation: {f.notation}; Voraussetzungen: {f.assumptions}"
                    )
                )
                output.append(
                    (r"\[" + f.latex + r"\]" if latex else "$$\n" + f.latex + "\n$$")
                    if safe_formula(f.latex)
                    else escape(f.latex)
                )
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
                escape(
                    (
                        "Demonstrationsausschnitt (wörtlich, möglicherweise unvollständig): "
                        if mock
                        and claim.evidence_quote
                        and not isinstance(claim, Formula)
                        else ""
                    )
                    + claim.text
                )
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
    output.append(
        escape(
            f"Im Dokument zitierte Belegblöcke: {len(cited)} von {len(summary.evidence)} registrierten. "
            "Registriert bedeutet nicht zitiert oder fachlich abgedeckt. "
            "Die Q-Nummern bleiben stabil. Vollständige technische Evidenz einschließlich "
            "unzitierter Blöcke bleibt im Summary-JSON erhalten und ist in der Oberfläche optional einsehbar."
        )
    )
    if include_all_evidence:
        output.append(
            escape(
                "Technische Evidenz: alle registrierten Belegblöcke, auch unzitierte."
            )
        )
    for evidence in summary.evidence:
        if not include_all_evidence and evidence.source_id not in cited:
            continue
        loc = evidence.locator
        position = f"{loc.origin_pointer}; Zeitstatus {loc.time_status}"
        if loc.page is not None:
            position += f"; Seite {loc.page}"
        if loc.line_start is not None:
            position += f"; Zeilen {loc.line_start}–{loc.line_end}"
        if loc.start is not None:
            end = seconds(loc.end) if loc.end is not None else "unbekannt"
            position += (
                f"; {seconds(loc.start)}–{end} s; Segment {loc.original_segment_id}"
            )
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
            ("nativer Knowledge-Chunk", evidence.native_chunk_id),
            ("natives Knowledge-Item", evidence.native_item_id),
            ("Media-ID", evidence.media_id),
            ("Original-SHA256", evidence.original_artifact_sha256),
        ):
            if value:
                info += f"; {label} {value}"
        if evidence.parent_artifact_ids:
            info += "; Parent-Artefakte " + ", ".join(evidence.parent_artifact_ids)
        if evidence.parent_segment_ids:
            info += "; Parent-Segmente " + ", ".join(
                map(str, evidence.parent_segment_ids)
            )
        if evidence.warnings:
            info += "; Quellenhinweise " + ", ".join(evidence.warnings)
        if evidence.source_id not in cited:
            info += "; im Dokument nicht zitiert (keine vollständige fachliche Abdeckung behauptet)"
        output.append(
            (r"\par\small " if latex else "- ")
            + (tex_evidence(info) if latex else escape(info))
        )
    body = "\n\n".join(output) + "\n"
    result = (
        TEMPLATE.read_text(encoding="utf-8").replace("@@BODY@@", body)
        if latex
        else body
    )
    if len(result.encode("utf-8")) > 500000:
        raise ValueError("Export byte limit exceeded")
    return result
