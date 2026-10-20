# C10: Offline-Prüfbericht

Stand: 16.10.2026; Basis `90f4ade`, aktueller `master` zu Arbeitsbeginn.
Verträge, CLI, tatsächliche Pipeline und nächster Integrationsschritt stehen im
[Quality-/Handoff-Vertrag](../contracts/material_quality.md).

## Änderungen und Isolation

Additiver Validator, versionierter Report und Read-only-Lecture-Handoff. Keine
Änderung an HTML-v2, PDF-v2, Downloadlogik, produktiven Artefakten oder Knowledge-
Extraktion. Keine neue Dependency, kein Installieren/Sync, keine Downloads,
LLM-Aufrufe, Datenbank-/Serveränderungen, Migration oder automatische Ausführung.

Das vorhandene `MaterialPlan`-Modell wurde unverändert aus `processing.py` nach
`model_materials/materials.py` verschoben und am alten Importpfad explizit
reexportiert. Damit kann das Gate bestehende Planverträge wiederverwenden,
ohne beim Import Discovery-/HTML-Parser und deren optionale Dependencies zu laden.
Es gibt weiterhin genau ein Planmodell und denselben JSON-Vertrag. Ein isolierter
Test blockiert BeautifulSoup, PyMuPDF, Settings und alle LLM-/OCR-SDKs und führt
sowohl CLI-Hilfe als auch eine vollständige Prüfung erfolgreich aus.

## Fixtures und Abdeckung

`tests/fixtures/material_quality/notes.html` und `source.pdf` sind kleine eigene,
ausdrücklich synthetische Quellen. Die PDF enthält zwei Seiten und ein nummeriertes
Python-Beispiel; sie wurde einmal lokal mit PyMuPDF erzeugt und als feste Bytes
versioniert. Die Tests verarbeiten beide Dateien mit den tatsächlichen bestehenden
v2-Parsern; mutationsbasierte Fälle verändern anschließend nur Kopien im temporären
Testworkspace. Socket-Zugriffe werden in den neuen Tests blockiert.

94 neue Fälle in `tests/test_cs50_material_quality.py`:

| Bereich | Nachweis |
|---|---|
| Intakte Ein-/Ausgaben | HTML-/PDF-v2, bestehende Graphidentitäten, vollständige Provenienz, Receipt, JSON-Roundtrip |
| Fehlende Metadaten/Versionen | Optionale Titel-/Metadatenwarnungen; zwingende Versionen und Seitenanzahl; explizite Materialbindung |
| Hashes und Receipts | Intakte und falsche Raw-/Normalized-Hashes; unvollständiger Status; Parser-/Raw-Konflikte; falsche Pfade |
| Blockidentität | Doppelte IDs, wiederholte/übersprungene Ordnung, konkrete Block-/DOM-Referenz bei Modellfehlern |
| Listen/TOC/Links | Verschachtelte Listen, strukturelle Container, TOC-Marker, fehlerhafte Itemreferenzen, Inlinecode und Linkprojektionen |
| Code | Originale mit Zeilennummern, exakte reversible Zusatzansicht, falsche Präfixe/Indizes/Nummern/Strategien, Klassifikations- und Zeilengeometrie |
| Bilder | Referenzen ohne Bytes als Warnung; gültige lokale Bytes; fehlende/falsche Bytes; Manifestkonflikte; abweichende Positionen und unsichere Pfade |
| Seiten und Unsicherheiten | Unabgedeckte Seite mit konkreter Seitenreferenz, fehlende/ungültige Seiten, Geometrie, Parserwarnungen und Klassifikationsunsicherheit |
| Lecturebindung | Konflikt im Dokumentbinding und ungültige Lecture im geprüften Graphen blockieren Handoff |
| Dateifehler | Fehlende Dateien, unvollständiges JSON, Array/null, ungültige Kodierung, doppelte Schlüssel, NaN/Überlaufzahlen |
| Determinismus/Read-only | Identische Reports/Handoffs bei Wiederholung, unveränderte Eingabebytes, keine Standardausgabe-Datei |
| CLI und Consumer | JSON/stdout, Herkunft/stderr, explizite exklusive Ausgabe, Symlink-/Overwrite-Verweigerung, gültiger Mehrmaterialbatch, Duplikatabweisung |
| Aggregation | Exakte ursprüngliche Zeichenfenster; keine zusätzlichen TOC-/Link-/Codeansichtseinheiten; Manipulation von Units/Reportbindung wird abgewiesen |

[HTML-Report](../examples/material-quality-html.v1.json) und
[PDF-Report](../examples/material-quality-pdf.v1.json) wurden mit `validate_material`
aus diesen Fixtures erzeugt. Die dortigen `/tmp/c10-quality-examples`-Pfade sind
explizite Beispielpfade des Generierungslaufs. Beide Reports sind
`passed_with_warnings`; der HTML-Report weist auf fehlende lokale Bildbytes hin,
der PDF-Report auf die bereits gespeicherten heuristischen Unsicherheiten.
Dies sind keine neu behaupteten Ergebnisse für die realen CS50-Originaldateien.
Die zuvor getesteten Originalworkspaces standen in dieser Sitzung nicht bereit;
es wurde kein Ersatzdownload vorgenommen.

## Ausgeführte Prüfungen

Vorhandene Umgebung: Python 3.12.12, Pytest 9.1.1, Ruff 0.16.3,
Pydantic 2.13.4, PyMuPDF 1.28.2. Ausführung mit dem vorhandenen Interpreter,
ohne `uv sync` oder Dependencyinstallation.

```bash
CS50_TEST_PROFILE=offline python -m pytest \
  tests/test_cs50_material_*.py \
  tests/test_cs50_executor.py::test_fresh_sync_import \
  tests/test_cs50_executor.py::test_success_and_verified_resume \
  tests/test_cs50_lecture_adapter.py tests/test_cs50_precise_evidence.py -q
```

**261 passed, 3 skipped, 0 failed** in 112,25 s (264 gesammelte Tests).

Die drei übersprungenen Tests benötigen optionale lokale Originalartefakte:
ein HTML- und zwei PDF-Originaltests. Alle deterministischen Fixtures laufen
vollständig offline. Der neue C10-Testblock allein: **94 passed**.

```bash
ruff check src/model_materials/materials.py src/model_materials/quality.py \
  src/tools_materials/processing.py src/tools_materials/quality.py \
  src/tools_lecture/material_handoff.py scripts/cs50_material_quality.py \
  tests/test_cs50_material_quality.py
ruff format --check <dieselben Python-Dateien>
git diff --check
```

Ruff-Lint, Ruff-Format und Whitespaceprüfung: erfolgreich. JSON-, AST-,
Zeilenende-, Debugger- und Dateigrößenprüfungen wurden ebenfalls lokal
ausgeführt. Die Git-Hooks wurden für den Commit/Push deaktiviert, damit deren
Pre-commit-Umgebungsinitialisierung keine Downloads oder Cacheinstallation auslöst;
die entsprechenden Prüfungen erfolgten mit den vorhandenen lokalen Werkzeugen.

Der Gesamtsuitenversuch scheiterte bereits bei der Sammlung an sieben bestehenden
Testmodulen wegen des nicht installierten `qdrant_client`. Ein separater sauberer
Checkout von `90f4ade` reproduzierte exakt dieselben sieben Sammlungsfehler:
`test_cs50_index_cli`, `test_cs50_index_contract`, `test_cs50_ingestion`,
`test_cs50_knowledge_index_checkpoint`, `test_cs50_knowledge_index_mapping`,
`test_cs50_retrieval`, `test_cs50_retrieval_evaluation`.
Ein Versuch mit `--continue-on-collection-errors` wurde während des umfassenden
Six-Course-Batchtests abgebrochen; daraus wird kein Gesamtsuitenerfolg abgeleitet.
Es wurden keine optionalen Pakete nachinstalliert und keine fachfremden Fehler
geändert. Die bestandene Regression umfasst den gesamten vorhandenen Materialblock
sowie die unmittelbar angrenzenden Executor-, Lecture- und Evidence-Verträge.

## Bekannte Grenzen / Empfehlung

Technische Konsistenz ist keine semantische Inhaltsfreigabe. Seitenlücken,
Parserheuristiken und fehlende Bildbytes bleiben reviewpflichtig. Der Handoff ist
ein referenzierbarer Snapshot und verlangt erneute Prüfung vor späterer Nutzung;
er ist noch kein Legacy-Lecture-Runner- oder Knowledge-Evidence-Input.

Als nächsten Schritt einen Read-only-Lecture-Consumer für diese logischen IDs und
`aggregation_units` implementieren und einen nicht zeitbasierten Material-Evidence-
Vertrag evaluieren. Erst nach Quellenzitat-/Dedup-Regressionsnachweis eine separat
freigegebene Extraktion anschließen. Details und Eingabeverträge:
[Material Quality Gate](../contracts/material_quality.md).
