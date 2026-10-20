# Vollständige CS50-Fixture-Coverage

## Ergebnis

Alle **50 von 50 Navigationsabschnitten** der sechs vorhandenen Kursindizes sind
jetzt lokal geparst. Der unveränderte CS50-Parser erkennt **50 logische
Hauptvorlesungen**, jeweils genau eine pro Abschnitt. Keine neue HTML-Parserfunktion
war erforderlich. Die internen IDs bleiben `cs50x`, `cs50_python`, `cs50_sql`,
`cs50_ai`, `cs50_web`, `cs50_cybersecurity`; insbesondere bleiben Woche `0` und
der nichtnumerische CS50x-Schlüssel `ai` unverändert erhalten.

Die 29 fehlenden offiziellen Wochen-URLs wurden aus der bestehenden Discovery
übernommen und in geprüften Gruppen von höchstens drei gleichzeitigen Abrufen
gespeichert: Timeout 25 Sekunden, keine automatischen Retries, keine rekursive
Linkverfolgung. Alle 29 Antworten: HTTP 200, effektive URL identisch zur entdeckten
URL. Keine nicht erreichbare Wochen-Seite. Einzelabrufe stehen in
[week_fixture_fetch_report.md](week_fixture_fetch_report.md).
Audio, Video, TXT, SRT, Notes-, Assignment- und CDN-Detailseiten wurden nicht abgerufen.

## Manifest und unveränderte Daten

63 HTML-Fixtures = 6 Indizes + 50 Wochen + 7 bereits vorhandene Detail-Fixtures.
`docs/course_sources/cs50/manifest.json` enthält für jeden Eintrag Original-URL, lokale Datei, Rolle und
SHA-256 der tatsächlichen Dateibytes. Der Loader prüft den Hash und meldet bei
Abweichung Dateipfad und `SHA-256 mismatch`. Das optionale `FixturePage.sha256`
ist die einzige notwendige Modellergänzung; alte Manifest-Dateien ohne Hash bleiben
lesbar. Lecture-/Knowledge-/Discovery-Ergebnismodelle wurden nicht geändert.
Hashes im aktuellen Manifest sind vollständig, nicht optional ausgelassen.

Die ursprünglichen 34 HTML-Dateien wurden nicht geändert. Das zusätzliche
`docs/course_sources/cs50/regression_manifest.json` hält die bisherige Teilabdeckung (21 Wochen) fest,
verweist auf dieselben unveränderten Dateien und dient ausschließlich Regressionstests.
Produktive Discovery und die generierten Berichte verwenden `docs/course_sources/cs50/manifest.json` mit
vollständiger Coverage. So bleiben Tests für `referenced`, fehlende Fixtures und
die vor Erweiterung gesicherten Discovery-/Preview-Verträge erhalten.

## Kurse, Hauptvorlesungen und Textquellen

| Kurs-ID | Abschnitte / Vorlesungen | Neue Wochen | SRT-Angebote | TXT-Angebote | Englisches SRT je Vorlesung | Standard-TXT-Downloads |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cs50x | 12 / 12 | 10 | 36 | 36 | 12 | 12 |
| cs50_python | 10 / 10 | 8 | 10 | 10 | 10 | 10 |
| cs50_sql | 7 / 7 | 5 | 7 | 7 | 7 | 7 |
| cs50_ai | 7 / 7 | 6 | 7 | 7 | 7 | 7 |
| cs50_web | 9 / 9 | 0 | 9 | 9 | 9 | 9 |
| cs50_cybersecurity | 5 / 5 | 0 | 5 | 5 | 5 | 5 |
| Gesamt | 50 / 50 | 29 | 74 | 74 | 50 | 50 |

CS50x bietet Englisch, Portugiesisch und Spanisch. Die anderen fünf Kurse verlinken
englisches SRT/TXT. Es gibt für jede Hauptvorlesung **genau einen** englischen
SRT- und TXT-Kandidaten; keine unbekannte Sprache bei diesen englischen Textangeboten.
Keine VTT-Links in den analysierten Wochen. Das bedeutet nicht, dass unverlinkte
VTT-Dateien außerhalb der Fixtures ausgeschlossen wären.

Die bestehende Selection bleibt unverändert TXT-first: 50 vorgeschlagene
TXT-Downloads, keine Video-/Audio-Downloads und keine Transkription. Eine separate
optionale Video-Preview schlägt zusätzlich 50 MP4-Dateien vor (720p, SDR bevorzugt,
unbekannte Video-Sprache ausdrücklich erlaubt). Sie wurde nur erzeugt, nicht
ausgeführt. Für die geplante SRT-first-Policy würden die geprüften Angebote 50
englische SRT-Quellen ermöglichen, optional ergänzt um 50 englische TXT-Dateien.
Das ist eine Coverage-Aussage, kein bereits implementierter Knowledge-Plan.

Die Dateien sind **angeboten**, nicht heruntergeladen oder inhaltlich validiert.
HTTP-Erreichbarkeit, SRT-Syntax, tatsächliche Sprache und Zeitqualität müssen erst
beim später explizit aktivierten Textabruf geprüft werden. Der vorhandene einzelne
Python-Woche-0-Pilot ersetzt diese Prüfung für die übrigen Quellen nicht.

## Ressourcen und Varianten

Insgesamt 653 eindeutige ResourceCandidates, 700 Medienvarianten einschließlich
Player/YouTube/Audio. Die vollständige Verteilung pro Kurs, Titel, Reihenfolge,
IDs und Original-URLs stehen in [six_course_overview.md](../../operations/six_course_overview.md).

| Rolle | Angebote |
| --- | ---: |
| lecture_video | 50 |
| audio | 50 |
| notes | 50 |
| slides | 100 |
| source_code | 109 |
| subtitles | 74 |
| transcript | 74 |
| short | 79 |
| section | 9 |
| demo | 3 |
| problem_set | 31 |
| project | 16 |
| quiz | 7 |
| other | 1 |

Videos, Notes und Slides werden in jeder Woche angeboten. Source Code wird
tatsächlich **nicht verlinkt** in CS50x Woche 10, Web Woche 1 sowie Cybersecurity
Wochen 1–4. Keine Platzhalter und keine konstruierten CDN-URLs. HDR/SDR und
360p/720p/1080p/4K bleiben erhalten; fehlender Dynamikumfang wird nicht als SDR
ausgegeben. Mehrere Sprachfassungen bleiben Varianten einer logischen Vorlesung.

CS50x Woche 10 enthält den zusätzlichen Kontext `Seminars`: Ein verlinktes
Begleitangebot bleibt `other` mit `unknown_resource_role`. Seine Inhalte werden
nicht erschlossen. Dafür wird kein neuer Ressourcentyp oder Parser erfunden.
Cybersecurity Woche 0 behält den bekannten Widerspruch zwischen Player-/Embed-IDs
mit `multiple_lecture_media_ids`; er betrifft keine SRT-Auswahl und wird nicht
durch ein erfundenes `media_id` aufgelöst.

CS50x Woche 10 verlinkt außerdem eine Slides-PDF unter `/2024/`, während die
Vorlesungsmedien unter `/2025/` liegen. Diese nachweisbare Jahresabweichung in der
Originalseite wird unverändert bewahrt, nicht automatisch auf 2025 umgeschrieben.
Die Snapshot-Zeitpunkte der ursprünglichen und ergänzten Seiten sind verschieden.

Discovery-Warnungen: sieben `local_embed_ignored` aus alten Browser-Fixtures,
ein `unknown_resource_role` und ein `multiple_lecture_media_ids`.
Keine `missing_week_fixture`, `missing_lecture` oder `missing_lecture_media`.

## Identität, Wiederholung und Testabdeckung

Die bestehenden Resource-/Variant-IDs bleiben erhalten. Tests prüfen alle zuvor
entdeckten Ressourcen gegen die vollständigen Kurse: URLs, Rollen, alte
Wochenzuordnungen, Provenienz und Varianten gehen nicht verloren. Neu hinzukommende
Wochenreferenzen dürfen vorhandene Ressourcen ergänzen. Wiederholtes Kombinieren
derselben geparsten `ai`-Seite verändert den Graphen nicht und erzeugt keine Dopplung.
Die bereits gesicherten vollständigen Teilgraph-/Standard-Preview-Hashes der vier
ursprünglichen Kurse bleiben über das Regression-Manifest gültig.

**117 Offline-Tests bestanden** im installierten uv-Interpreter (Python 3.12.12):
Manifest, vier ursprüngliche Kurse, Selection, sechs Kurse und vollständige Coverage.
Der separate abschließende Lauf für Coverage sowie die bestehenden
SRT-/uv-Integrations- und Offline-Smoke-Regressionen bestand mit **25 Tests**.
Zehn Coverage-Tests sind in beiden Läufen enthalten; zusammen wurden alle
**132 unterschiedlichen CS50-Testfälle** ausgeführt, vollständig ohne API-Aufruf.
Die Coverage-Tests sperren Socket/DNS bereits vor ihrer Kurs-Discovery.

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_discovery.py tests/test_cs50_extraction.py \
  tests/test_cs50_selection.py tests/test_cs50_six_courses.py \
  tests/test_cs50_full_coverage.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_full_coverage.py tests/test_cs50_srt_knowledge_integration.py \
  tests/test_cs50_uv_installed_integration.py tests/test_cs50_llm_smoke.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python scripts/report_cs50_sources.py
```

Die Übersicht, beiden bisherigen Selection-Previews und
[six_course_fixture_provenance.md](../../operations/six_course_fixture_provenance.md) wurden aus
dem vollständigen Manifest neu generiert. Der bisherige
`six_course_completion_report.md` beschreibt weiterhin den historischen Stand
21/50; dieser Coverage-Bericht ist der aktuelle Stand.

Keine produktiven Runner, Downloader oder Importer wurden ausgeführt oder geändert;
keine Marvin-/SQLite-Änderungen, LLM-Aufrufe, neue Dependencies oder automatische Merges.
Die konkrete Fortsetzung steht in [transcript_knowledge_integration_plan.md](transcript_knowledge_integration_plan.md).
