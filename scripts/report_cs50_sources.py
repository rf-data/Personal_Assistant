"""Rebuild six-course documentation from local HTML only; no ResourceTasks."""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model_discovery.cs50_selection import SelectionPolicy  # noqa: E402
from src.tools_lecture.cs50_manifest import load_fixture_manifest  # noqa: E402
from src.tools_lecture.prepare_cs50 import discover_fixture_courses  # noqa: E402
from src.tools_lecture.select_cs50 import preview_course, render_preview  # noqa: E402


def overview(courses):
    lines = [
        "# Kombinierte CS50-Kurs- und Ressourcenübersicht",
        "",
        "Aus lokalen Fixtures generiert; Angebote und Downloads sind ausschließlich Dry-Run-Vorschläge.",
        "",
        f"{len(courses)} Kurse, {sum(len(c.sections) for c in courses)} Navigationsabschnitte, "
        f"{sum(s.status == 'parsed' for c in courses for s in c.sections)} geparste Abschnitte.",
        "",
        "Standard: Englisch, TXT vor Untertiteln, kein Video, keine Transkription. "
        "Optionale Video-Preview: 720p, SDR bevorzugt, unbekannte Sprache ausdrücklich zugelassen. "
        "Unbekannte Sprache oder HDR/SDR werden nicht ergänzt.",
        "",
        "| Kurs-ID | Abschnitte | Logische Vorlesungen | TXT-/SRT-/VTT-Angebote | Standard-Downloads | Optional TXT + MP4 |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for course in courses:
        default = preview_course(course)
        videos = preview_course(
            course, SelectionPolicy(require_video=True, allow_unknown_language=True)
        )
        formats = Counter(
            r.format
            for r in course.resources
            if r.role.value in {"transcript", "subtitles"}
        )

        def downloads(preview):
            counts = Counter(
                d.selected.format
                for lecture in preview.lectures
                for d in lecture.decisions
                if d.selected and "download" in d.actions
            )
            return (
                ", ".join(f"{n} {kind}" for kind, n in sorted(counts.items()))
                or "keine"
            )

        lines.append(
            f"| {course.course_id} | {len(course.sections)} | {len(default.lectures)} | "
            f"{formats['txt']}/{formats['srt']}/{formats['vtt']} | {downloads(default)} | {downloads(videos)} |"
        )
    lines += [
        "",
        "Angebote zählen ResourceCandidates (einschließlich Sprachfassungen), nicht ausgeführte Downloads. "
        "Logische Vorlesungen zählen nur tatsächlich geparste Wochen; verlinkte Wochen werden nicht hochgerechnet.",
        "",
    ]
    for course in courses:
        lines += [
            f"## {course.course_id}",
            "",
            f"Original-Kurs: {course.original_url}",
            "",
            "### Abschnitte in Navigationsreihenfolge",
            "",
            "| Reihenfolge | Schlüssel | Titel | Status |",
            "| ---: | --- | --- | --- |",
        ]
        lines.extend(
            f"| {s.order} | {s.key} | {s.title} | {s.status.value} |"
            for s in course.sections
        )
        lines += [
            "",
            "### Ressourcenangebote nach Typ",
            "",
            "| Rolle | Anzahl |",
            "| --- | ---: |",
        ]
        counts = Counter(r.role.value for r in course.resources)
        lines.extend(f"| {role} | {n} |" for role, n in sorted(counts.items()))
        lines += [
            "",
            "### Medienvarianten (einschließlich Player/YouTube/Audio)",
            "",
            "| Format | Auflösung | HDR/SDR | Anzahl |",
            "| --- | --- | --- | ---: |",
        ]
        variants = Counter(
            (
                v.format or "unbekannt",
                v.resolution or "unbekannt",
                v.dynamic_range or "unbekannt",
            )
            for r in course.resources
            for v in r.variants
        )
        lines.extend(
            f"| {kind} | {quality} | {dr} | {n} |"
            for (kind, quality, dr), n in sorted(variants.items())
        )
        lines += ["", "### Ressourcen mit Kurs-/Abschnittszuordnung", ""]
        lines.extend(
            f"- Abschnitt {', '.join(r.section_keys)}; `{r.role.value}`; `{r.resource_id}`: {r.original_url}"
            for r in course.resources
        )
        lines += ["", "### Discovery-Warnungen", ""]
        lines.extend(
            f"- Abschnitt {w.section_key}: `{w.code}` — {w.message}"
            for w in course.warnings
        )
        if not course.warnings:
            lines.append("Keine.")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "docs/course_sources/cs50/manifest.json"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/course_sources/cs50"
    )
    args = parser.parse_args()
    courses = discover_fixture_courses(args.manifest)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "six_course_overview.md").write_text(
        overview(courses), encoding="utf-8"
    )
    for name, policy in [
        ("six_course_preview.md", SelectionPolicy()),
        (
            "six_course_video_preview.md",
            SelectionPolicy(require_video=True, allow_unknown_language=True),
        ),
    ]:
        (args.output / name).write_text(
            render_preview(tuple(preview_course(c, policy) for c in courses)),
            encoding="utf-8",
        )
    manifest = load_fixture_manifest(args.manifest)
    checksums = [
        "# HTML-Fixture-Provenienz",
        "",
        "Ursprüngliche 34 HTML-Fixtures unverändert; 29 fehlende Wochen am 13.10.2026 ergänzt. "
        "Alle SHA256-Werte sind im aktuellen Manifest hinterlegt und beim Laden geprüft.",
        "",
        "| Fixture | Original-URL | SHA256 |",
        "| --- | --- | --- |",
    ]
    checksums.extend(
        f"| {p.file} | {p.url} | `{hashlib.sha256((args.manifest.parent / p.file).read_bytes()).hexdigest()}` |"
        for c in manifest.courses
        for p in c.pages
    )
    (args.output / "six_course_fixture_provenance.md").write_text(
        "\n".join(checksums) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
