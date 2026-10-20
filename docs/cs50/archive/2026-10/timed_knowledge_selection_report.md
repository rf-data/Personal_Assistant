# PR 2: Explizite SRT-first-Auswahl für Knowledge

## Ergebnis

`SelectionPolicy(text_strategy="timed_knowledge")` plant für alle 50 geparsten
Hauptvorlesungen genau eine englische offizielle SRT-Quelle. Der unveränderte
Default heißt `transcript_first`: TXT → VTT → SRT → ausdrücklich erlaubte
Transkription. Die vier historischen Discovery-/Preview-SHA256-Snapshots bestehen
unverändert. Lecture-/Knowledge-Modelle und Runner wurden nicht geändert.

| Kurs-ID | Vorlesungen | Englische SRT-Auswahlen | Geplante Downloads | Geplante Subtitle-Imports |
| --- | ---: | ---: | ---: | ---: |
| cs50x | 12 | 12 | 12 | 12 |
| cs50_python | 10 | 10 | 10 | 10 |
| cs50_sql | 7 | 7 | 7 | 7 |
| cs50_ai | 7 | 7 | 7 | 7 |
| cs50_web | 9 | 9 | 9 | 9 |
| cs50_cybersecurity | 5 | 5 | 5 | 5 |
| Gesamt | 50 | 50 | 50 | 50 |

Dies sind ausschließlich Vorschläge, keine ausgeführten Downloads oder Imports.
Video-/Audio-/Whisper-Auswahlen: **0**. Die vollständigen Original-URLs,
Resource-IDs, Zuordnungen, Alternativen und Warnungen stehen separat in
[knowledge_selection_preview.md](../../operations/knowledge_selection_preview.md).

## Auswahlvertrag

Die neue Strategie nutzt weiterhin `SelectionOption`, `SelectionDecision`,
`LecturePreview` und `CoursePreview`. Der vollständige immutable Discovery-Graph
bleibt erhalten. Die logische Vorlesung steht in `LecturePreview.resource_id`,
ihre Abschnitte in `section_keys`, der Kurs in `preview.discovery.course_id`.
`selected.resource_id` identifiziert dagegen die konkrete SRT-Ressource. Ihre
Original-URL, Sprache, Rolle `subtitles` und Format `srt` werden unverändert
übernommen. Die Auswahl erfindet keine zusätzliche Lecture-ID.

Akzeptiert wird genau ein Kandidat mit exakt bevorzugter Sprache (Default `en`),
ohne Medienvarianten, mit offizieller HTTPS-CDN-URL und Provenienz auf der
zugehörigen offiziellen Wochen-Seite. Die CDN-Struktur muss zum bestehenden
Kurs-Prefix passen; Abschnitt und `lang`-Teil müssen den Metadaten entsprechen.
Diese Prüfungen sind bewusst konservativ und vollständig offline. Abweichende
zukünftige CDN-/Provenienz-Strukturen benötigen eine nachgewiesene Erweiterung.
Sie beweisen die Herkunft des Links, nicht die Erreichbarkeit oder den Inhalt
der noch nicht abgerufenen SRT-Datei.

Die Zuordnung verwendet explizite Eltern oder einen eindeutig gemeinsamen
Abschnitt. Mehrere passende SRT-Kandidaten beziehungsweise mehrdeutige
Vorlesungszuordnungen ergeben keine Auswahl und keine Aktionen. Fehlende,
anderssprachige, unbekanntsprachige oder unbelegte Kandidaten werden mit einem
verständlichen Grund abgelehnt. `allow_unknown_language=True` erlaubt in diesem
Modus keine unbekannte Sprache. `require_video` und `allow_transcription` werden
für die Auswahl ignoriert: auch bei fehlendem SRT gibt es keinen Fallback.

Eine erfolgreiche Entscheidung hat `purpose="text"` und
`actions=("download", "parse_subtitle")`. `integration_pending` weist darauf hin,
dass der offizielle Importer bereits existiert, seine Lecture-Runner-Anbindung
aber eine separate Aufgabe bleibt. Es werden keine `ResourceTask`-Objekte erzeugt.

`select_optional_txt()` ist nur auf ausdrücklichen separaten Aufruf verfügbar.
Der Aufrufer muss die Kandidaten zuvor eindeutig auf eine Vorlesung begrenzen.
Das Ergebnis bezeichnet TXT ausdrücklich als Ergänzung. `preview_course()`
fügt diese Entscheidung niemals automatisch hinzu; TXT wird nicht zum
zeitbasierten Knowledge-Primärinput.

## JSON-Kompatibilität

Alte Policy-JSONs ohne `text_strategy` werden mit dem bisherigen Default geladen.
Der Serializer lässt das Feld beim Default weg, auch in verschachtelten Previews.
Damit bleiben bestehende JSON-Darstellung und SHA256-Snapshots unverändert.
Bei `timed_knowledge` wird die Strategie gespeichert und beim Roundtrip erhalten.
Die vorhandenen Decision-/Option-Verträge wurden nicht erweitert. Die vollständige
Discovery-Provenienz bleibt im eingebetteten Graph statt in erfundenen Option-Feldern.

## Reproduktion und Tests

In der tatsächlich installierten lokalen uv-Umgebung, Python 3.12.12, ausgeführt:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_discovery.py tests/test_cs50_extraction.py \
  tests/test_cs50_selection.py tests/test_cs50_six_courses.py \
  tests/test_cs50_full_coverage.py tests/test_cs50_timed_selection.py -q
# 136 passed

UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_srt_knowledge_integration.py \
  tests/test_cs50_uv_installed_integration.py tests/test_cs50_llm_smoke.py -q
# 15 passed; nur vorhandene Offline-Tests, kein API-Smoke-Test aktiviert

UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python \
  scripts/report_cs50_sources.py --knowledge-preview
```

Die letzte Anweisung schreibt ausschließlich die Knowledge-Preview, keine
produktiven Daten. `--output /tmp/cs50-preview` ermöglicht einen getrennten
Ausgabeordner. Ohne den neuen Parameter bleibt die bisherige Report-Erzeugung
unverändert.

19 neue Testfälle prüfen alle sechs Kurse mit 50 Vorlesungen, erhaltene IDs/URLs,
JSON-Roundtrips und Legacy-JSON, Reihenfolgeunabhängigkeit von Ressourcen und
Medienvarianten, fehlendes SRT, Mehrdeutigkeit, fehlende Sprache/Provenienz,
kursfremde CDN-Pfade, fehlende Abschnitte, getrenntes optionales TXT und die
reproduzierbare CLI-Ausgabe ausschließlich in eine separate Preview-Datei. Socket-,
DNS- und Connection-Aufrufe sind in den neuen Tests gesperrt. Bestehende Tests
decken weiterhin TXT-first, Sprach-/HDR-/Auflösungsvarianten und Default-Fallbacks
ab. Ruff-Format und Ruff-Check für die geänderten Python-Dateien bestehen.

## PR-Basis und verbleibende Arbeit

Die vollständige Sechs-Kurse-/50-Wochen-Basis war lokal vorhanden, aber noch nicht
auf GitHub veröffentlicht. Sie wird auf `feat/cs50-full-coverage` separat von der
neuen Strategie bereitgestellt; der kleine PR zielt auf diese Basisbranch und
enthält nur Auswahlmodus, Preview-CLI, neue Tests und diesen Bericht samt Preview.
Die Basis wiederum baut auf `feat/cs50-selection-preview` auf. Kein Merge wird
ausgeführt. Die Originalbytes und SHA256-Werte der HTML-Fixtures bleiben erhalten.

Für spätere Verarbeitung fehlen weiterhin der explizite Selection→Lecture-Adapter,
kontrollierter SRT-Download, Import/Validierung des tatsächlichen Inhalts und die
Runner-Anbindung mit Status-/Resume-Vertrag. Diese Änderungen gehören in spätere
kleine PRs; keine davon wird durch diese Policy automatisch aktiviert.
