# C11 – Offline-Validierung

Basis: aktueller `master`, `09f7384`. Die Implementierung ist unabhängig von
C10; nach dessen Integration in Master wurde die Regression einschließlich seiner
Material-Quality-Tests wiederholt. Zuvor auf `90f4ade`: 322 passed, 3 skipped
in 83,62 s.
Vollständige Verträge und Grenzen: [Architektur und CLI](README.md).

## Umgebung und Prüfungen

Vorhandene Umgebung: Python 3.12.12, Pytest 9.1.1, Ruff 0.16.3, Pydantic 2.13.4,
SymPy 1.14.0, PyMuPDF 1.28.2. Keine Installation, kein Sync, keine neuen Downloads.
Die optionalen Symboliktests verwenden ausschließlich das bereits installierte
SymPy. Ohne dieses Paket werden nur diese Tests übersprungen; der Standardpfad
und der explizite `sympy_unavailable`-Vertrag bleiben verfügbar.

```bash
CS50_TEST_PROFILE=offline python -m pytest \
  tests/test_math_formula_evaluation.py tests/test_cs50_material_*.py \
  tests/test_consolidation_math_import.py tests/test_cs50_precise_evidence.py \
  tests/test_cs50_lecture_adapter.py tests/test_knowledge_transcript_provenance.py -q
```

**423 passed, 3 skipped, 0 failed** in 109,85 s (426 gesammelte Tests).
Darin alle 123 neuen C11-Tests und 303 vorhandene angrenzende Tests,
einschließlich des inzwischen integrierten C10-Quality-Gates.

Die drei Skips betreffen die optionalen bereits vorhandenen Originalartefakte
(HTML Notes und zwei PDFs). Alle eigenen synthetischen Fixtures laufen offline.
Kein vollständiger Gesamtsuitenlauf: Der Schwerpunkt dieses Auftrags sind das
Evaluationspaket und die angrenzenden Parser-, Formel-, Lecture- und Evidence-
Verträge. Fachfremde RAG-/SDK-Profile wurden nicht durch neue Dependencies ergänzt.

```bash
ruff check src/model_evaluation/math_evaluation.py \
  src/tools_evaluation/evaluate_math.py src/tools_evaluation/math_syntax.py \
  src/tools_evaluation/math_equivalence.py src/tools_evaluation/sympy_worker.py \
  src/tools_evaluation/math_predictions.py src/tools_evaluation/math_reports.py \
  scripts/evaluate_math_formulas.py tests/test_math_formula_evaluation.py
ruff format --check <dieselben Python-Dateien>
git diff --check
```

Ruff-Lint und Formatierung erfolgreich; zusätzlich JSON-, AST-, Link-,
Zeilenende- und Dateigrößenprüfung. Commit-/Push-Hooks werden nicht zur
Umgebungsinitialisierung gestartet, damit keine Hook-Downloads erfolgen;
die entsprechenden Prüfungen laufen mit vorhandenen lokalen Werkzeugen.

## Neue Tests

123 Fälle in `tests/test_math_formula_evaluation.py` prüfen:

- Gültige/ungültige Pydantic-Daten, fehlende Quellenidentität/-referenz, Seite oder
  Abschnitt, explizite Schemaversion, Ambiguität, fehlende/zusätzliche Formeln.
- NFC, Whitespace, Unicode-Minus/Multiplikation/Indizes/Potenzen; Erhalt von
  Operatoren, Exponenten, Case und Befehls-/Zahlengrenzen.
- Brüche, Potenzen, Indizes, verschachtelte Klammern, Wurzeln, Summen, Integrale,
  Vektoren mit unterscheidbaren Skalar-/Kreuzprodukten und korrekt gepaarte `\left`/`\right`-Klammern.
- Exakte unbekannte Notation wird nicht als mathematische Erfolgsmeldung behandelt.
- Explizites Teilformelrubrik: echte Referenz-Substruktur, kein aus der Vorhersage
  abgeleiteter Teilpunkt; ungültiges Rubrik wird auch ohne Vorhersage abgewiesen.
- Rationale Polynomidentitäten und Nichtidentitäten, proportionale Gleichungen,
  konkrete Gegenbeispiele, konstante Wurzeln und unabhängige Indizes.
- Abstain bei Definitionsbereichsproblemen, variablen Nennern, nicht unterstützten
  Exponenten/Operatoren, unbekannten Gleichungslösungsmengen und der Konstanten `\pi`.
- SymPy optional: kein impliziter Backendaufruf, explizit fehlendes Paket, isolierte
  Ausführung, CPU-/Adressraum-/Dateilimits vor symbolischer Arbeit und Timeout mit
  Beendigung/Reaping der Prozessgruppe; auch ein realer kurzer Walltimeout.
- Problematische Python-/Shell-/LaTeX-Inputs werden nicht ausgeführt. Isolierter
  CLI-Import und Standardauswertung blockieren Settings, Visual-/LLM-SDKs und
  SymPy vollständig. Tests brauchen keine API-Schlüssel oder produktiven Daten.
- Nenner, Nullraten, getrennte `synthetic`-/`real`-Aggregationen, die 42 unabhängig
  festgelegten erwarteten Statuswerte und die vollständige Kategorienabdeckung.
- JSON/JSONL, Fallauswahl, Duplikate, beschädigte Dateien, ungültige Kodierung,
  doppelte Schlüssel, begrenztes Lesen vor dem Parsen großer Dateien sowie
  deterministische Report-/Markdown-Wiederholung.
- Exakte Output-Hashes, JSON-Roundtrip, exklusive Publikation, Verweigerung
  bestehender/leerer Verzeichnisse und Symlinks sowie Manifest als Abschlussmarker
  bei unterbrochenem Schreiben.
- Read-only-Anbindung vorhandener `VisualAnalysisDocument`-Vorhersagen an
  unabhängiges Gold: Quellen-/Abschnitts-/Batch-/Expression-Prüfung, Hashbindung,
  keine Änderung an Gold, Originaldatei oder Knowledge und explizite Abweisung
  alter `results`-Wurzeln.

## Beispielauswertung

Tatsächlich ausgeführter Aufruf:

```bash
python -m scripts.evaluate_math_formulas \
  --cases docs/math_evaluation/formula_cases.v1.json \
  --equivalence sympy --output docs/math_evaluation/example
```

Die [JSON-Ausgabe](example/report.json), [Markdown-Zusammenfassung](example/summary.md)
und das [Hashmanifest](example/manifest.json) sind vollständig versioniert.

42 synthetische Fälle, 31 entschiedene Rekonstruktionsfälle, 37 vergleichbare
nicht ambige Formelpaare; 10 exakte und 12 normalisierte Matches, 12
Strukturmatches bei 33 strukturell vergleichbaren Paaren. 16 bestätigte
Äquivalenzen einschließlich identischer unterstützter Notation, davon vier
zusätzliche Nachweise im SymPy-Worker; 11 nicht entscheidbare Fälle.

Die Rekonstruktionsstatus sind 17 `correct`, zehn `incorrect`, zwei
`partially_correct`, je ein `missing_formula`/`extra_formula` und elf
`undetermined`. Die absichtlich falschen Vorhersagen dienen als Gegenbeispiele und
sind **keine gemessenen Fehler eines Extraktionsmodells**. Reale Goldreferenzen:
0; reale Raten: `null` / `n/a`.

## Grenzen und nächste Integration

Die unveränderten Produktionspfade sind weiterhin die vorhandenen PDF-/Visual-/
Knowledge-Komponenten; dieses Paket startet sie nicht. Ihr gesamter produktiver
Runner ist durch diese Tests nicht als betriebsbereit zertifiziert. Insbesondere
werden die dokumentierte alte Visual-Dateiform und die Runner-Importabweichung
nicht automatisch repariert.

Für die nächste reale Evaluation zunächst 10–20 unabhängig annotierte Formeln aus
bereits vorhandenen lokalen Seiten/Frames mit Quellen-ID und Fundstelle auswählen.
Anschließend vorhandene Originalvorhersagen über den Read-only-Adapter binden,
reale Goldgruppe separat auswerten und nicht entscheidbare Definitionsbereiche
manuell prüfen. Keine automatische Übernahme von `correct` oder Modell-Confidence
in bestehende Knowledge-Verifikationsflags.
