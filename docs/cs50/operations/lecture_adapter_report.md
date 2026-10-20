# PR 3: Deterministischer Selection→Lecture-Adapter

## Ergebnis und Plan

Der Adapter verwendet den expliziten `timed_knowledge`-Modus aus PR 2 / #14.
Er erzeugt Referenzen und Metadaten, führt aber keine ResourceTasks aus. Die
versionierte Datei [cs50_lecture_plan.v1.json](../../course_sources/cs50/cs50_lecture_plan.v1.json) enthält
für alle sechs Kurse den vollständigen Discovery-Graphen einschließlich Varianten,
Sprachen, Hierarchie und HTML-Provenienz, die geprüfte Preview, echte LectureCourse-
Objekte und alle Ressourcen-/Quellen-/Task-/Artefaktbindungen.

| Kurs-ID | Abschnitte / Hauptvorlesungen / SRT-Bindungen | Exportierte Ressourcen | DOWNLOAD | PARSE_SUBTITLE |
| --- | ---: | ---: | ---: | ---: |
| cs50x | 12 | 233 | 12 | 12 |
| cs50_python | 10 | 145 | 10 | 10 |
| cs50_sql | 7 | 77 | 7 | 7 |
| cs50_ai | 7 | 77 | 7 | 7 |
| cs50_web | 9 | 77 | 9 | 9 |
| cs50_cybersecurity | 5 | 44 | 5 | 5 |
| Gesamt | 50 | 653 | 50 | 50 |

Alle 100 Tasks sind zunächst PENDING. Ihre Task-IDs und 100 Ausgabepfade sind
eindeutig. `artifact_state` ist leer: Es wird weder ein Download noch ein Import
oder ein vorhandenes Artefakt behauptet. Der Plan hat `schema_version=1`,
`adapter_version="cs50_selection_lecture_v1"`, `planned_only=true` und
`execution_supported=false`. Bestehende Modelle, Selection-Defaults und Runner
bleiben unverändert. Der PR baut auf der Branch aus #14 auf, ohne sie zu mergen.

## Funktionen und Modellkompatibilität

`src/tools_lecture/adapt_cs50.py` stellt bereit:

- `adapt_cs50_course(discovery)` erstellt ein echtes `LectureCourse` mit einer
  Referenz pro ResourceCandidate. Navigationsreihenfolge und Blockschlüssel bleiben
  erhalten. Ressourcen werden deterministisch nach Abschnitt, Rolle und ID sortiert.
- `bind_cs50_selection(preview, decisions, artifact_root=...)` erwartet eine Map
  **logische lecture_id → SelectionDecision** für genau die Vorlesungen der Preview.
  Die Policy muss `timed_knowledge` sein; Preview und Entscheidungen werden gegen
  die bestehende reine Selection erneut geprüft. Fehlende, ungewählte oder
  widersprüchliche Quellen führen zu einem verständlichen Fehler.
- `build_cs50_transcript_tasks(bindings, artifact_state)` erstellt pro Quelle zwei
  getrennte bestehende `ResourceTask`-Objekte in externen Task-Bindungen. Die
  Funktion liest keine Dateien, sucht keine Dateinamen und führt keine Aktionen aus.
- `build_cs50_course_plan(preview, ...)` kombiniert die überprüften Verträge.
  `CS50AdapterPlan.model_validate_json(...)` validiert beim Laden auch die
  Konsistenz von Export, Auswahl, Provenienz, Ressourcenindex, Tasks und Pfaden.

SRT, TXT, Notes und Slides werden als `LectureDocument` exportiert. Source Code,
Assignments, Projekte und Referenz-/Startermaterial werden als `LectureMaterial`
abgebildet; sonstige Rollen bleiben `LectureOther`. Ihre feinere fachliche Rolle
steht weiterhin im Discovery-Graphen. Die Hauptvorlesung und Audioangebote werden
als `LectureMedia`-Referenzen exportiert. `media_url=None` bedeutet, dass keine
Qualität oder Player-Alternative für einen Download ausgewählt wurde.

LectureResource besitzt keine Resource-ID, Sprache oder Provenienz. Daher ordnet
`lecture_resource_ids[i]` die unveränderte Discovery-ID ausdrücklich dem Eintrag
`lecture_course.resources[i]` zu. Die SRT-Bindung und ihre Tasks verwenden echte
LectureDocument-Instanzen; SRT wird niemals als Videomedium behandelt. Exportierte
Course-Ressourcen bleiben `downloaded=false` und haben noch keinen lokalen Bestand.
Die separate ausgewählte Document-Referenz enthält den geplanten Roh-SRT-Zielpfad.

## Identität, Provenienz und Zielpfade

| Information | Speicherung / Bedeutung |
| --- | --- |
| course_id | ursprüngliche geprüfte Discovery-Kurs-ID, unverändert |
| section_key | Originalschlüssel, insbesondere `0` und `ai`; keine Integer-Konvertierung |
| lecture_id | Resource-ID der logischen Hauptvorlesung |
| resource_id | davon verschiedene Resource-ID des ausgewählten englischen SRT |
| source_id | expliziter Alias dieser SRT-Resource-ID; keine Ableitung aus Dateinamen oder YouTube-ID |
| transcript_url, language, role | Original-SRT-URL, `en`, `subtitles`; Auswahl muss zur Preview passen |
| provenance | ursprüngliche HTML-Provenienz einschließlich Fixture, Locator und Kontextpfad |
| transcript_source | geplante Importstrategie `official_subtitle`, keine KnowledgeEvidence-Modalität |
| media_id | nur eindeutige vorhandene Varianten-ID im passenden Sprachkontext; sonst None |

Cybersecurity Woche 0 behält beide bekannten IDs `kUovJpWqEMk` und `fJYdAN4Vh5c`
sowie die Discovery-Warnung. Sowohl die LectureMedia-Referenz als auch die
SRT-Bindung haben hier `media_id=None`. Es wird kein Konflikt durch willkürliche
Auswahl aufgelöst. Medienzuordnung beweist noch keine zeitliche Synchronität.

Mit dem expliziten Default `artifact_root=data/lectures` lauten die Zielpfade:

```text
data/lectures/Harvard/<course_id>/cs50-v1/<section_key>/<lecture-id-hash>/<srt-resource-id-hash>/source.srt
data/lectures/Harvard/<course_id>/cs50-v1/<section_key>/<lecture-id-hash>/<srt-resource-id-hash>/transcript.json
```

IDs bestimmen diese Pfade, niemals umgekehrt. Identitätsbindungen enthalten die
vollständigen IDs einschließlich `resource:`-Prefix. Traversal im Artifact-Root
und unsichere Abschnittskomponenten werden abgelehnt; Pfadkollisionen werden
innerhalb und zwischen Kursen geprüft. Der Root ist explizit und wird nicht aus
Dateibestand oder `LectureCourse.root` ermittelt. Für spätere Runner muss derselbe
Root ausdrücklich übergeben werden. Ein SRT mit mehreren Abschnittszuordnungen
bedarf einer gesonderten eindeutigen Bindung und wird hier konservativ abgelehnt.

## Externe Abhängigkeiten und Artefaktzustand

`ResourceTask` kann weder Task-ID noch Output-Pfad oder Abhängigkeiten speichern.
`CS50TaskBinding` hält deshalb `task_id`, `depends_on`, `output_path` und Identität
außerhalb dieses bestehenden Vertrags. Die PARSE_SUBTITLE-Task verweist auf die
DOWNLOAD-Task derselben Quelle und erhält deren Roh-SRT-Pfad als `input_paths`.
Das normalisierte Transcript-JSON ist ihr expliziter externer Output-Pfad.

**Diese Tasks dürfen noch nicht als nackte ResourceTasks an den alten Runner
übergeben werden.** Dessen Dokument-Dispatch kennt den offiziellen SRT-Importer
nicht und wertet die externe Abhängigkeit nicht aus. PR 4 benötigt den separaten
CS50-Handler mit Dependency-Prüfung vor Download/Import und vor Provider-Erstellung.

Optional kann ein zukünftiger Aufrufer geprüfte `CS50ArtifactState`-Beobachtungen
nach Resource-ID übergeben. Identität, URL, Sprache, Version und beide Pfade müssen
exakt passen. Ein bestätigter Roh-Hash plant DOWNLOAD als SKIPPED. Ein bestätigtes
validiertes Transcript mit Output-Hash und passendem SRT-Input-Hash plant auch
PARSE_SUBTITLE als SKIPPED. Es wird niemals DONE erfunden. Unvalidiertes bestehendes
Transcript, fehlende Hashbelege, fremde State-Einträge oder Widersprüche stoppen
die Planung. Der Adapter prüft **nicht** die Dateien oder berechnet ihre Hashes;
PR 4 muss diese Außenbeobachtungen tatsächlich überprüfen. Retry-, Locking-,
Crash-/Resume- und atomare Schreibausführung sind hier noch nicht implementiert.

Es gibt noch kein tatsächliches `TranscriptProvenance` mit Importzeitpunkt und
keine Segment-/Chunk-IDs oder Zeitstempel. Diese entstehen erst beim realen
offiziellen Import. Keine künstlichen Importzeiten, Zeiten oder Wissensergebnisse.

## Offline-Tests und Umgebung

**Ergebnis: 166 bestanden**, sowohl im aktuellen Arbeitsbaum als auch in einer
isolierten Arbeitskopie mit dem identischen Git-Tree von PR #14 als Basis und
ausschließlich den fünf neuen PR-Dateien. Ruff-Check, Ruff-Format, Python-/JSON-
Syntax, EOF- und Git-Whitespace-Prüfungen bestehen ebenfalls.

30 neue Adapter-Testfälle plus 136 bestehende Discovery-/Selection-Testfälle
prüfen alle sechs Kurse, 50 Bindungen, 100 Tasks, vollständige JSON-Roundtrips,
stabile Reihenfolge, unveränderte Eingaben, Provenienzkonflikte, kollidierende Pfade,
fehlende Entscheidungen, expliziten Artefaktzustand und exklusive Report-Ausgabe.
Netzwerkverbindungen sind gesperrt. Ein frischer synchroner Subprozess importiert
den echten Adapter mit 20 Sekunden Timeout; Marvin, Whisper, yt-dlp und der
Processing-Runner werden nicht importiert. Die reinen Funktionen werden zusätzlich
mit gesperrtem `open`/`Path.open` getestet.

Die bestehenden Lecture-Verträge importieren `src.core.config`, das Folder- und
Agentic-Settings lädt. Diese bestehende Kopplung bleibt unverändert. Die Tests
verwenden echte Modelle mit vollständigen harmlosen Settings in einem Verzeichnis
ohne `.env`-Dateien; es werden weder reale API-Schlüssel benötigt noch Modelle
oder Konfiguration durch Attrappen ersetzt.

Die aktuelle uv-Basisumgebung hat Pydantic 2.13.4 / pytest 9.1.1, aber nicht die
deklarierten optionalen Worker-Pakete `pydantic-settings` und BeautifulSoup.
Offline-`uv --with` konnte deren Transitivabhängigkeiten nicht vollständig aus dem
Cache auflösen. Daher nutzt `/tmp/cs50-adapter-test-env` denselben Python 3.12.12
und die bereits installierten Basispakete sowie vorhandene echte Cache-Paketdateien
für pydantic-settings 2.15.0, BeautifulSoup 4.15.0 und SoupSieve über eine lokale
Test-`.pth`-Datei. Keine Downloads, keine Änderungen an Projekt-venv, pyproject
oder Lockfile. Die Library selbst enthält keinerlei Cache-/Test-Bootstrap.

Testbefehl für diese kontrollierte Offline-Umgebung:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache UV_PROJECT_ENVIRONMENT=/tmp/cs50-adapter-test-env \
  uv run --offline --no-sync python -m pytest \
  tests/test_cs50_lecture_adapter.py tests/test_cs50_discovery.py \
  tests/test_cs50_extraction.py tests/test_cs50_selection.py \
  tests/test_cs50_six_courses.py tests/test_cs50_full_coverage.py \
  tests/test_cs50_timed_selection.py -q
```

Zum Erzeugen einer **neuen separaten** Plan-Datei in einer Umgebung mit den
bestehenden Worker-/Settings-Abhängigkeiten:

```bash
uv run --offline --no-sync python scripts/report_cs50_lecture_plan.py \
  --output /tmp/cs50_lecture_plan.v1.json --artifact-root data/lectures
```

Die CLI validiert den vollständigen Roundtrip vor dem Schreiben, öffnet den
Report mit `x` und verweigert bestehende Dateien sowie Report-Ausgabe unter dem
Transcript-Artifact-Root. Sie erstellt keine Transcript-Artefaktverzeichnisse.
Für vollständig isolierte Verwendung sind die bestehenden Settings explizit
mit unbenutzten Offline-Werten zu setzen. Ruff und Python-Syntax der neuen
Python-Dateien werden zusätzlich geprüft. Keine Änderungen an Loviscach,
Knowledge-Runnern, Chunking, Marvin oder SQLite.
