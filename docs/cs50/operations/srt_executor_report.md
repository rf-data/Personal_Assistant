# PR 4: Kontrollierter CS50-SRT-Executor

## Umfang und Verträge

`src/tools_lecture/execute_cs50.py` implementiert `CS50Executor` und den ausführbaren
Moduleinstieg. Er lädt und revalidiert den vollständigen Version-1-Adapterplan mit
seinen bestehenden Pydantic-Verträgen. Die 50 Bindungen und 100 Tasks behalten ihre
IDs, externe Abhängigkeiten und expliziten Zielpfade. Der allgemeine Lecture-Runner,
Loviscach, Discovery, Selection und Chunking bleiben unverändert.

Der historische Plan bleibt unverändert: `planned_only=true` und
`execution_supported=false` beschreiben seinen Erstellungszustand. Die neue CLI
meldet nach implementiertem und offline geprüftem Ausführungspfad
`execution_supported=true`. Dieses Fähigkeitsmerkmal ist keine Ausführungsfreigabe:
nur `--execute` aktiviert Netzwerk und Schreiben. Standard ist Dry-Run, maximal eine
Vorlesung. Ausführung benötigt zusätzlich einen expliziten Kursfilter. Abschnitt
`0` und nichtnumerische Schlüssel wie `ai` bleiben Strings.

### Kleine nachgewiesene Modellkorrektur

Der vorhandene offizielle Importer referenziert `TranscriptSource.OFFICIAL_SUBTITLE`
und `OFFICIAL_TRANSCRIPT`, die im tatsächlichen Arbeitsbaum und in PR 3 fehlen.
Nur diese beiden Enum-Werte wurden ergänzt. Alte Enum-Werte und JSON-Verträge
bleiben erhalten; Segment-, Lecture- und Knowledge-Modelle wurden nicht umgebaut.

## Download und Import

* Nur die geprüfte ausgewählte HTTPS-URL auf `cdn.cs50.net`, ohne Redirects,
  Proxy-Umgebungsvariablen, YouTube oder yt-dlp.
* HTTPX-Streaming mit 64-KiB-Blöcken, 15 Sekunden Request-/I/O-Timeout,
  8 MiB Gesamtgrößenlimit und 60 Sekunden Downloadbudget. Das Budget wird zwischen
  Requests und empfangenen Blöcken geprüft; ein bereits laufendes I/O kann bis
  zum eingestellten I/O-Timeout weiterlaufen.
* Höchstens zwei zusätzliche Versuche bei Transportfehlern, Timeout, HTTP 429
  und 5xx; Backoff 1/2 Sekunden, begrenzt durch das verbleibende Budget.
  404, Redirects und Größenfehler werden nicht wiederholt. Importfehler werden
  nicht automatisch wiederholt.
* Temporäre Datei im Zielverzeichnis, SHA-256, `fsync`, atomare exklusive
  Veröffentlichung mittels `os.link`. Vorhandene Zieldateien werden nie ersetzt.
* DOWNLOAD bestätigt den Transport und Hash; PARSE_SUBTITLE validiert danach
  separat die tatsächliche SRT. Ein syntaktisch ungültiger Download bleibt als
  überprüfbarer Rohinput erhalten, der Import wird als fehlgeschlagen dokumentiert.
* Der echte `import_srt(..., preserve_empty_cues=True)` prüft UTF-8/BOM,
  Cue-Syntax und Zeitangaben. Zusätzlich prüft der Executor nicht abnehmende
  Startzeiten und mindestens einen nicht leeren Cue. Überlappende Cues bleiben
  zulässig, Wiederholungen und Mehrzeilentext unverändert. Es entstehen keine
  künstlichen Zeitstempel.
* Das normalisierte `TranscriptDocument` enthält Sprache, Original-URL,
  `official_subtitle`, expliziten Quellpfad, Format, tatsächlichen Importzeitpunkt
  und ausschließlich die bereits geprüfte `media_id` (sonst `None`). JSON wird
  temporär serialisiert und exklusiv veröffentlicht.

## Persistenz, Abhängigkeiten und Resume

Neben den beiden expliziten Artefakten liegt pro Bindung `execution.v1.json`.
Der versionierte Beleg enthält die komplette `CS50TranscriptBinding`, einschließlich
Kurs, Abschnitt, lecture/resource/source IDs, URL, Sprache, HTML-Provenienz und
Zielpfaden. Jeder Task erhält separat `running`, `prepared`, `done` oder `failed`,
Ausgangshash, ggf. SRT-Eingangshash und eine Fehlermeldung. Dies ist der externe
Ausführungsstatus; die ursprünglichen `ResourceTask`-Objekte im Plan bleiben erhalten.

Ein `prepared`-Hash wird vor der Veröffentlichung persistiert. Nach einem Abbruch
zwischen Veröffentlichung und Abschluss kann eine identische Datei deshalb belegt
übernommen werden. Eine Datei ohne solchen Beleg wird abgewiesen. `done` erfordert
weiterhin eine existierende Datei mit identischem Hash. Normalisiertes JSON wird
zusätzlich erneut modellvalidiert, gegen Original-SRT-Segmente/Text geprüft und auf
Provenienzkonflikte untersucht. Der Import benötigt den abgeschlossenen Download-
Task und seinen geprüften Rohinhalt. Identitäts-, Hash- oder Provenienzkonflikte
führen zu einem Fehler, nicht zu Überschreiben oder automatischem Reparieren.

POSIX `flock` verhindert gleichzeitige Ausführungen derselben Bindung und wird
bei Prozessende freigegeben. Pfade müssen innerhalb der expliziten Artefaktwurzel
und des gewählten Workspace liegen; `..` und Symlinks werden abgewiesen. Linux/
POSIX-Dateisystem mit Hardlinks und Directory-fsync ist vorausgesetzt. Kooperativer
lokaler Betrieb ist vorgesehen, kein Schutz gegen einen gleichzeitig böswillig
manipulierten Dateisystembaum. Nach hartem Prozessabbruch können temporäre Dateien
zurückbleiben; sie werden weder gesucht noch als fertige Artefakte übernommen.

Die bestehende Datei `docs/course_sources/cs50/cs50_lecture_plan.v1.json` bleibt die vollständige Discovery-
und Identitätsreferenz. Kurs-/Lecture-/Resource-/Source-IDs passen nicht vollständig
in `TranscriptDocument`; sie bleiben deshalb im separaten Beleg und im Plan erhalten.
Kein Knowledge-Aufruf findet statt.

## Offline-Tests und uv-Umgebung

Die reguläre lokale `.venv` verwendet Python 3.12.12 und pytest 9.1.1.
`UV_CACHE_DIR=/tmp/cs50-uv-cache uv sync --offline --frozen --extra lecture-worker`
war erfolgreich: 139 Pakete geprüft, keine Installation oder Änderung erforderlich.
Keine zusätzliche Dependency, kein Lockfile-Umbau und keine Downloads waren nötig.
HTTPX ist Basisabhängigkeit; Settings und BeautifulSoup sind bereits im deklarierten
`lecture-worker` enthalten. Bestehende Lecture-Settings bleiben Importvoraussetzung;
Tests setzen harmlose Werte und verwenden keine produktiven Schlüssel.

Der neue Testsatz prüft: alle 100 tatsächlichen Fake-HTTP-Task-Ausführungen,
Download/Import/JSON, doppelte Ausführung ohne erneuten HTTP-Aufruf, UTF-8/BOM,
leere/fehlerhafte SRT, falsche Zeitfolge, leere Cues, 404/429/5xx, Redirects,
Timeout, partiell empfangene Daten, Größenlimit, Aufräumen bei Ausnahmen,
Resume nach Fehler/Veröffentlichungsabbruch, fehlende fertige Artefakte,
Hash-/Identitäts-/Provenienzkonflikte, Abhängigkeiten, Symlinks, Pfade,
Prozesslock, Dry-Run ohne Schreiben und synchronen Modulimport im frischen
Subprozess mit 20-Sekunden-Limit und gesperrtem Netzwerk.

Der Originalpilot `data/lectures/cs50_python/lecture0.srt.txt` wurde als Fake-HTTP-
Response durch den vollständigen Executor verarbeitet, ohne die Quelle zu ändern:
189973 Bytes, SHA-256
`719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c`,
2228 Cues, darunter zwei leere Cues. Ergebnisartefakte lagen ausschließlich in
pytest-Temporärverzeichnissen.

Ausgeführte Befehle (abschließende Ergebnisse siehe unten):

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_executor.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_discovery.py tests/test_cs50_extraction.py tests/test_cs50_selection.py tests/test_cs50_six_courses.py tests/test_cs50_full_coverage.py tests/test_cs50_timed_selection.py tests/test_cs50_lecture_adapter.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_official_transcript_import.py -q
```

Die vorhandenen offiziellen Importtests ergeben **33 bestanden, 6 fehlgeschlagen**.
Alle sechs Fehler stammen vom vorhandenen TXT-Pfad: `start=None/end=None` wird vom
aktuellen `TranscriptSegment(start: float, end: float)` abgewiesen. Diese bekannte,
separate Vertragslücke wird hier nicht durch einen Zeitmodellumbau verdeckt. SRT-
und VTT-Importfälle bestehen nach Ergänzung der fehlenden Herkunfts-Enum-Werte.

## Manuell freizugebender einzelner echter Download

Im Repository-Verzeichnis zuerst ohne Netzwerk und ohne Artefaktänderungen prüfen:

```bash
uv run --offline --no-sync python -m src.tools_lecture.execute_cs50 \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --course cs50_python --section 0 --max-lectures 1 --dry-run
```

Erst nach eigener Prüfung bewusst ausführen:

```bash
uv run --offline --no-sync python -m src.tools_lecture.execute_cs50 \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --course cs50_python --section 0 --max-lectures 1 --execute
```

`uv --offline` verhindert Paketdownloads; der ausdrücklich aktivierte Executor
verwendet dann HTTP für genau diese ausgewählte offizielle SRT-Quelle. Derselbe
Befehl dient der überprüften Wiederaufnahme. Zielpfade entsprechen exakt dem Plan
unter `data/lectures/Harvard/cs50_python/cs50-v1/0/…`; vorbestehende unbestätigte
Artefakte werden abgewiesen. Codex hat diesen Execute-Befehl nicht mit echtem HTTP
aufgerufen. Keine Audio-/Video-, LLM-, Whisper-, Knowledge- oder API-Verarbeitung.

## Abschließende Ergebnisse

| Prüfung | Ergebnis |
| --- | --- |
| Neue Executor-Regressionen in regulärer uv-Umgebung | 33 bestanden, 50,42 s |
| Bestehende CS50-/Lecture-Adapter-Regressionen in regulärer uv-Umgebung | 166 bestanden, 157,80 s |
| Dieselben 166 Regressionen in isolierter vorheriger uv-Testumgebung | 166 bestanden, 177,64 s |
| Vorhandene offizielle Importtests | 33 bestanden, 6 bekannte TXT-Vertragsfehler |
| Ruff Check und Format, Diff-Whitespace | bestanden |
| Echter Netzwerkdownload während Implementierung | keiner |

Die reguläre und isolierte Umgebung verwenden echte Modelle und Pakete, keine
Modell-Stubs. Der Python-0-Pilot wurde ausdrücklich mit originalen lokalen Bytes
getestet; die weiteren 49 Quellen wurden im Executor mit synthetischen HTTP-
Response-Inhalten geprüft. Damit sind Task-Zuordnung und Ausführung offline belegt,
nicht die heutige Erreichbarkeit sämtlicher Original-URLs.
