# CS50 Resource Selection und Processing Preview

## Bestandsaufnahme

`src/model_lecture/data_resources.py` definiert ResourceAction (`download`,
`parse_subtitle`, `transcribe`, `parse_document`, `chunk`, `extract_frames`,
`extract_knowledge`, `extract_metadata`) und ResourceTask mit Ressource,
Input-Pfaden, Aktionen und Status. LectureMedia kann Audio/Video, URL und Media-ID
abbilden, aber keine Sprach-, Qualitäts- oder HDR/SDR-Alternativen. Dokumentmodelle
bilden Skripte und Material ab; die Discovery-Rollen und Provenienz sind umfangreicher.
Diese bestehenden Modelle bleiben unverändert.

`plan_lecture.py` arbeitet mit lokalen Dateien: vorhandene Transcript-JSONs benötigen
keine Aktion, VTT führt zu `parse_subtitle`, lokales Audio zu `transcribe`, ansonsten
zu `download`. Dokumente führen abhängig vom Dateibestand zu Download oder Parsing.
Dabei verändert der Planner Ressourcentitel und lokale Pfade. Der Runner enthält
numerische Loviscach-Abschnitte; Woche `0` und `ai` brauchen einen eigenen Exportweg.

`process_lecture.py` und `process_url.py` führen reale Aktionen aus, initialisieren
Transkriptionskonfiguration und suchen über yt-dlp Untertitel bzw. Audio. Der Download
ist deshalb kein verlässlicher Auftrag für die in dieser Preview gewählte direkte
720p-URL. `download_document` lädt Dateien über urllib herunter. Der Untertitelparser
verarbeitet ausschließlich VTT und verwendet standardmäßig Deutsch; die CS50-Fixtures
enthalten SRT. TXT-Transkripte sind noch nicht als TranscriptDocument normalisiert.
Der DIY-Dokumentparser unterstützt PDF; andere Dokumentformate hängen vom Backend ab.
ZIP-Quellcode ist kein unterstützter Parsing-Auftrag.

Vor produktiver Integration sind direkte CS50-URLs, explizite Sprache, SRT/TXT-
Normalisierung, lokale Zustandsprüfung und die Übergabe des Download-Ergebnisses an
Folgeschritte erforderlich. Slides, Notes und Source Code bleiben vollständig im
Discovery-Graph, erhalten in dieser auf Vorlesungstext und Video begrenzten Policy
aber keine Aufgaben. Player-/YouTube-URLs bleiben Alternativen; ihre konkrete
Qualität wird offline nicht behauptet.

## Verträge und Auswahl

`SelectionPolicy`, `SelectionOption`, `SelectionDecision`, `LecturePreview` und
`CoursePreview` liegen in `src/model_discovery/cs50_selection.py`. Alle sind immutable
Pydantic-Modelle. CoursePreview erhält den vollständigen CourseDiscovery unverändert,
inklusive Hierarchie, Status, Medienvarianten und Provenienz. Options referenzieren
Resource-ID und gegebenenfalls Variant-ID. Aktionen sind typisierte Namen des
bestehenden ResourceAction-Vokabulars: dessen direkter Import würde bereits
Environment-Konfiguration initialisieren. Ein AST-Test prüft die Namen ohne Import.
Es werden keine ResourceTasks erzeugt.

`preview_course(course, policy)` ist eine reine Funktion ohne Dateizugriffe oder
Netzwerk. `render_preview(previews)` gibt ausschließlich Markdown zurück. Ein
Aufrufer kann diesen Text ausdrücklich speichern; die Preview selbst schreibt nichts.

Defaults: Englisch (`en`), exakt `720p`, SDR vor HDR, Video nicht erforderlich,
unbekannte Sprache nicht erlaubt, Transkription nicht erlaubt. Konfigurierbar sind
Sprache, Auflösung (`360p`, `720p`, `1080p`, `4k`), Dynamikumfangpräferenz und die drei
Freigaben. Es gibt keinen stillen Sprach- oder Auflösungsfallback. Fehlende
HDR/SDR-Metadaten sind nach bekannten Angeboten nachrangig und erzeugen eine Warnung.
Unbekannte Sprache ist nur durch `allow_unknown_language=True` auswählbar, immer
nachrangig zur bekannten bevorzugten Sprache.

Textpriorität: TXT-Transkript, VTT, SRT, ausdrücklich erlaubte direkte Audioquelle.
Ohne passende Text-/Audioquelle darf bei erlaubter Transkription genau die gewählte
Videoqualität verwendet werden. Bei gleichzeitig angefordertem Video wird nur dessen
Download vorgeschlagen; der Textschritt verwendet dieselbe Quelle für `transcribe`.
SRT und TXT erhalten Integrationswarnungen und sind keine ausführbaren Taskketten.
Ohne passende Quelle enthält die Entscheidung einen Grund und keine Aktionen.
Mehrere gleichwertige verschiedene URLs werden als mehrdeutig abgelehnt, nicht
lexikografisch willkürlich ausgewählt. Alternativen sind deterministisch sortiert.

Eine Hauptvorlesungs-Resource ist eine logische Vorlesung, unabhängig von der Anzahl
ihrer Sprach-/Medienvarianten und Wochenzuordnungen. Die Zuordnung von Begleitmaterial
erfolgt über explizite Eltern oder eindeutig gemeinsame Abschnitte. Mehrdeutige
Zuordnungen werden ausgeschlossen und gemeldet. Referenzierte Wochen ohne extrahierte
Vorlesung bleiben im Graph; sie erzeugen keine Preview-Vorlesung.

## Offline-Ergebnis

Die sieben lokal geparsten Vorlesungen haben je ein englisches TXT-Transkript. Die
Default-Preview schlägt deshalb sieben TXT-Downloads und keine Videodownloads vor.
Bei `require_video=True` sind die beiden CS50x-Vorlesungen mit englischem 720p SDR
wählbar. Die übrigen fünf Videos fehlen unter strenger Policy wegen unbekannter
Sprache; mit expliziter Freigabe sind sieben 720p-Angebote wählbar. CS50 AI hat dabei
zusätzlich unbekannten Dynamikumfang. Sämtliche Player-, Sprach- und Qualitätsangebote
bleiben erhalten. Der vollständige Beispielreport steht in `selection_preview.md`.

Validierung: 24 neue Offline-Testfälle plus 69 bestehende CS50-Tests, insgesamt
93 Tests. Sie prüfen alle drei CS50x-Sprachen und vier Auflösungen, HDR/SDR, fehlende
Transkripte und Metadaten, Mehrdeutigkeit, fehlende Zielqualität, stabile Reihenfolge,
Unveränderlichkeit und genau einen Videodownload bei gemeinsamer Nutzung. Socket und
DNS sind während der Tests gesperrt. Ruff und Repository-Commit-Hooks werden ebenfalls
geprüft. Es gibt keine Änderungen an Lecture-Modellen, Loviscach oder Taskplanung.
