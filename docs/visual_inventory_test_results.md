# C13 – Offline-Testresultate

Basis: `master` (`09f7384`). Vorhandene Umgebung: Python 3.12.12,
Pydantic 2.13.4, Pytest 9.1.1, Ruff 0.16.3, PyMuPDF 1.28.2,
BeautifulSoup 4.15.0. Keine Installationen, Downloads, API-Schlüssel oder
Live-LLM-Aufrufe. Keine produktiven Datensätze oder Server verwendet.

## Neue Inventur und bestehende Materialpipeline

```bash
python -m pytest -q tests/test_cs50_visual_inventory.py tests/test_cs50_material_*.py
```

Ergebnis: **279 passed, 3 skipped** (282 Fälle, davon 69 neue C13-Tests).
Alle zwölf bestehenden Material-Testmodule sind enthalten. Skips betreffen
optionale reale Originalnotizen und zwei nicht lokal bereitgestellte Original-PDFs;
es wurden keine Ersatzdownloads versucht.

Die neuen Tests prüfen insbesondere:

- Echte HTML-v2-/PDF-v2-Ausgaben auf ausschließlich synthetischen Quellen.
- Rasterbilder, externe/relative/Inline-/SVG-Referenzen, Figure-Captions,
  fehlendes `src`, Responsive-Referenzen und aktive/unsichere SVG-Inhalte.
- Einzelpfade, Rechtecke, Seitenhintergründe, wiederkehrende Layoutsignaturen,
  mehrpfadige geometrische Gruppen und Text/Grafik auf derselben Seite.
- Tatsächlich gleiche Bildbytes an unterschiedlichen Positionen sowie echte
  überlappende Bildvorkommen mit gleicher BBox; keine inhaltsbasierte Deduplikation.
- Nachgewiesene mehrfache XRef-Referenzen im bestehenden PDF-v2-Parser:
  physische Positionen nicht doppelt zählen, alle ursprünglichen Bild-/Block-IDs
  als bestätigte Aliase erhalten; keine kanonische Parseränderung.
- Stabile Asset-IDs, explizite Dokument-/Material-/Kurs-/Lecture-Referenzen,
  DOM-Positionen, BBoxes, rotierte PDF-Seiten und Original-Hashes.
- Fehlende/unpassende Artefaktbytes, unsichere Pfade/Symlinks/Traversal,
  falsche Raw-Hashes, ungültiges JSON/Schema und optionaler Receipt-/Planvergleich.
- Byte-/Seiten-/Asset-/Pfad-/Operationslimits, Pixel-Metadatenwarnung und
  sichtbare Worker-Timeouts. Keine Inventur-Bilddecodierung oder -extraktion.
- Unveränderte Quellbytes und mtimes bei wiederholter Inventur, JSON-/Markdown-
  Publikation, Exitcodes, No-Overwrite und deterministische Reporthashes.
- Reproduzierbare eingecheckte Beispielberichte. Ein sauberer isolierter Prozess
  sperrt optionale SDKs, Settings, Memory, BeautifulSoup/PyMuPDF sowie C10-Module
  und prüft den Normalized-only-Pfad ohne diese Laufzeitabhängigkeiten.

Socketverbindungen und DNS sind in den neuen Parent-Tests gesperrt. Der feste
Raw-Worker importiert ausschließlich die lokalen Beobachtungsfunktionen und
bestehende Parser-/DOM-Helfer; er enthält keine Netzwerk-/SDK-Aufrufe.

## Knowledge-/Provenienz-/Import-Regression

```bash
python -m pytest -q \
  tests/test_knowledge_source_id.py \
  tests/test_knowledge_transcript_provenance.py \
  tests/test_consolidation_math_import.py \
  tests/test_lazy_marvin_import.py
```

Ergebnis: **57 passed**. Zusammen **336 passed, 3 skipped**.
Bestehende Knowledge-/Materialmodelle und Parser wurden nicht verändert.

## Statische und Artefaktprüfungen

```bash
ruff check src/model_materials/visual_inventory.py \
  src/tools_materials/visual_inventory.py \
  src/tools_materials/visual_worker.py \
  scripts/cs50_visual_inventory.py tests/test_cs50_visual_inventory.py \
  tests/fixtures/visual_inventory/build_fixture.py
ruff format --check src/model_materials/visual_inventory.py \
  src/tools_materials/visual_inventory.py \
  src/tools_materials/visual_worker.py \
  scripts/cs50_visual_inventory.py tests/test_cs50_visual_inventory.py \
  tests/fixtures/visual_inventory/build_fixture.py
git diff --check
python -m scripts.cs50_visual_inventory --help
```

Ergebnis: Ruff **All checks passed**, sechs Dateien korrekt formatiert,
keine Whitespace-Fehler. AST, JSON, Newlines, Dateigrößen, lokale Dokumentlinks,
Base64-PDF-Magic und Beispielreporthashes wurden zusätzlich lokal geprüft.
Netzwerkabhängige Pre-Commit-Umgebungen wurden nicht initialisiert; zutreffende
Prüfungen wurden mit den bereits installierten Tools ausgeführt.

## Beispielbeobachtungen

| Quelle | Assets | Verfügbare Bildpositionen | Eindeutige Artefaktpfade | Vektorkandidaten | Bestätigte Aliase | Fehler |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Synthetisches HTML | 12 | 2 | 1 | 0 | 0 | 0 |
| Synthetisches PDF, zwei Seiten | 8 | 2 | 1 | 6 | 2 | 0 |

Die Werte stammen aus ausgeführten Inventuren, nicht aus einer semantischen
Goldbewertung. JSON-/Markdown-Beispiele und Grenzen sind in
[Visual Inventory](visual_inventory.md) verlinkt. Es wird weder ein produktiver
Visual-Enrichment-Lauf noch ein vollständiger Repository-Gesamttest behauptet.
