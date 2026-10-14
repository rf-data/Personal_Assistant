# Abschluss der CS50-Quellenintegration: sechs Kurse

Historischer Abschlussstand mit 21/50 geparsten Wochen. Die nachfolgende Erweiterung
auf **50/50** steht in [full_coverage_report.md](full_coverage_report.md);
die generierten Übersicht-/Preview-Dateien bilden inzwischen diesen vollständigen Stand ab.

## Umfang und Ergebnis

Alle sechs Kurse verwenden denselben Offline-Pfad:
`load_fixture_manifest → parse_course_index/parse_week_page → combine_course_pages → preview_course`.
Die vorhandene interne ID **`cs50x`** bleibt erhalten (nicht `cs50_x`). Die weiteren
IDs sind `cs50_python`, `cs50_sql`, `cs50_ai`, `cs50_web` und `cs50_cybersecurity`.
Keine Lecture-/Knowledge-Modelle, Runner, Marvin-/SQLite-Konfiguration oder
Selection-Regeln wurden geändert. `CourseId` erlaubt lediglich die zwei neuen IDs;
die bestehende Discovery-Modellstruktur bleibt identisch.

34 lokale HTML-Fixtures: unverändert 18 der bisherigen vier Kurse plus 16 neue
Originalseiten (zwei Indizes, neun Web-Wochen, fünf Cybersecurity-Wochen), abgerufen
am 13.10.2026. Es wurden ausschließlich diese HTML-Seiten heruntergeladen, keine
Assets, Detailseiten, Untertitel-, TXT-, Audio- oder Videodateien.

| Kurs | Abschnitte | Geparst / logische Vorlesungen | TXT | SRT | VTT | Standard-Downloads | Optionale zusätzliche MP4-Downloads |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| cs50x | 12 | 2 | 6 | 6 | 0 | 2 TXT | 2 |
| cs50_python | 10 | 2 | 2 | 2 | 0 | 2 TXT | 2 |
| cs50_sql | 7 | 2 | 2 | 2 | 0 | 2 TXT | 2 |
| cs50_ai | 7 | 1 | 1 | 1 | 0 | 1 TXT | 1 |
| cs50_web | 9 | 9 | 9 | 9 | 0 | 9 TXT | 9 |
| cs50_cybersecurity | 5 | 5 | 5 | 5 | 0 | 5 TXT | 5 |
| Gesamt | 50 | 21 | 25 | 25 | 0 | 21 TXT | 21 |

TXT/SRT zählen die in den geparsten Seiten angebotenen Links; CS50x enthält drei
Sprachfassungen pro Vorlesung. Die tatsächliche Erreichbarkeit und Dateiinhalte
wurden nicht geprüft. In den analysierten Seiten gibt es keine VTT-Angebote;
das ist keine Aussage über sämtliche externen CDN-Dateien.

29 Abschnitte der bisherigen vier Kurse bleiben mangels lokaler Wochen-Fixtures
`referenced`. Sie erhalten weder erfundene Vorlesungen noch Download-Vorschläge.
Die neuen Kurse sind vollständig geparst. Insgesamt gibt es 220 ResourceCandidates
und 227 Medienvarianten einschließlich Audio, Player- und YouTube-Alternativen.

| Ressourcenrolle | Angebote |
| --- | ---: |
| lecture_video (logische Hauptvorlesung) | 21 |
| audio | 21 |
| notes | 21 |
| slides | 42 |
| source_code | 31 |
| subtitles | 25 |
| transcript | 25 |
| short | 12 |
| problem_set (einschließlich Cybersecurity-Assignments) | 11 |
| project | 8 |
| demo | 1 |
| section | 1 |
| quiz | 1 |

Die vollständigen Abschnitte, Ressourcen-IDs, Original-URLs, Variantenverteilungen
und Warnungen stehen in [six_course_overview.md](../../operations/six_course_overview.md).
Alle Fixture-URLs und SHA256-Werte stehen in
[six_course_fixture_provenance.md](../../operations/six_course_fixture_provenance.md).

## Nachgewiesene HTML-Abweichungen und kleine Parserergänzungen

[CS50 Web](https://cs50.harvard.edu/web/) verwendet in allen neun Wochen
`Watch lecture.` als Wurzel der verschachtelten Ressourcenliste. Bisher erkannte
der Parser nur `Lecture`; dadurch würden direkte MP4-Angebote nicht zur logischen
Hauptvorlesung gehören. Beide exakt nachgewiesenen Wurzeltexte werden nun akzeptiert.
`Start <a>Project 0</a>.` und `Finish <a>Final Project</a>.` erfordern die zusätzliche
Berücksichtigung des Linklabels bei der Rollenbestimmung. `Final Project` wird als
`project` erkannt. Context-Pfade und Original-URLs werden unverändert erhalten.

[CS50 Cybersecurity](https://cs50.harvard.edu/cybersecurity/) verwendet die bekannte
`Lecture`-Wurzel und `MP4 → HDR/SDR → Auflösung`. `Assignment N` wird im vorhandenen
Vokabular der Aufgabenfamilie `problem_set` zugeordnet; `Final Project` bleibt
`project`. Diese Zuordnung bedeutet keine Verarbeitung der Aufgabeninhalte.

Für verschachtelte Listen, Audio, Notes, Slides, Source Code, Subtitles, Transcript,
YouTube und CS50-Player waren keine neuen Parser nötig. `.mp4.download` bleibt als
Original-URL erhalten und wird durch den bestehenden Formatparser als MP4 erkannt.
Source-Code-PDFs bleiben gegenüber Slides-PDFs über ihren Kontext getrennt.
Die Projekt- und Assignment-Ergänzungen ändern keine gespeicherte Hierarchie.

Web bietet pro Woche 360p/720p/1080p/4K, YouTube und CS50-Player. HDR/SDR ist dort
nicht angegeben und bleibt unbekannt. Cybersecurity bietet alle vier Auflösungen
jeweils in HDR und SDR. Web verlinkt Keynote/PDF-Folien, ZIP-Source-Code in acht
Wochen und sechs Projekte. Cybersecurity verlinkt Google Slides/PDF-Folien,
Source-Code-Index/PDF/ZIP nur in Woche 0, fünf Assignments und ein Abschlussprojekt.
Ein fehlender Code-Link in anderen Wochen wird nicht ergänzt.

Cybersecurity Woche 0 enthält im Embed `kUovJpWqEMk`, in der Video-Liste dagegen
`fJYdAN4Vh5c`. Beide IDs/URLs bleiben Varianten **einer** durch Kurs und Wochen-URL
identifizierten logischen Vorlesung. Eine neue Warnung
`multiple_lecture_media_ids` meldet mehrere Player-IDs innerhalb derselben
Sprachgruppe. Ob die Player unterschiedliche Aufnahmen enthalten, wurde nicht
geprüft; sie werden weder überschrieben noch als identischer Inhalt behauptet.
Die eindeutig bezeichneten direkten CDN-Qualitätsangebote bleiben auswählbar.

## Selection und spätere Lecture-Verarbeitung

[six_course_preview.md](../../operations/six_course_preview.md) nutzt unverändert die Standard-Policy:
Englisch, TXT vor Untertiteln, Video nicht angefordert, Transkription nicht erlaubt.
Ergebnis: 21 vorgeschlagene TXT-Downloads; **keine** Audio-/Video-/SRT-Downloads.
Die vollständigen Alternativen bleiben erhalten.

[six_course_video_preview.md](../../operations/six_course_video_preview.md) ist eine separate,
ausdrücklich konfigurierte Preview mit `require_video=True` und
`allow_unknown_language=True`. Sie schlägt zusätzlich genau ein 720p-MP4 pro
logischer Vorlesung vor. Cybersecurity wählt SDR; Web und AI behalten unbekannten
Dynamikumfang samt Warnung. Nicht als Englisch ausgewiesene Video-Angebote werden
nur aufgrund dieser ausdrücklich erlaubten unbekannten Sprache gewählt, nicht
durch Ableitung aus dem Kursnamen oder dem englischen TXT-Link.
Mit strenger Sprachpolicy bleiben solche Videos bewusst ungewählt.

Es entstehen keine ResourceTasks. Die 21 bzw. optional 42 Download-Vorschläge sind
keine ausgeführten Downloads. Kein Export nach LectureCourse, keine Transkription
und keine Knowledge Extraction. Für eine spätere Lecture-Integration sind Kurs,
Abschnitt, Vorlesungs-ID, Ressourcenrolle, URL und ausgewählte Qualität verfügbar;
Alternativen, Fixture-Provenienz, Sprachunsicherheit und Warnungen müssen separat
erhalten bleiben. TXT muss weiterhin über den offiziellen Import normalisiert
werden; der zeitlose Knowledge-Pfad ist hier nicht implementiert.

## Einschränkungen und nicht ausführbare Ressourcen

Alle verlinkten Ressourcen der neuen Wochen erhalten eine bekannte Rolle; es gibt
keine `other`-/`unknown_resource_role`-Fälle. Erkennen eines Angebots bedeutet jedoch
keine ausführbare Lecture-Verarbeitung: Notes-Inhalte, Google Slides, Keynote,
Source-Code-Archive/-Indizes/-PDFs, Projekte, Assignments, Quiz, Shorts, Demos und
Sections erhalten in diesem Selection-Pfad keine eigenen Processing-Tasks.
Welcome-Videos und allgemeine Navigation werden nicht als Vorlesungen behandelt.

Der Parser untersucht keine Detailseiten, CDN-Verzeichnisse, JavaScript-generierten
Listen oder nicht verlinkten Formate. Die HTML-Fixtures sind zeitlich verschiedene
Snapshots; die alten vier werden nicht durch aktuellere Kursseiten ersetzt.
Video-Language und teilweise HDR/SDR fehlen in den Originalen. Die bestehende
Selection-Warnung zum fehlenden SRT-Parser bezieht sich noch auf die damalige
Lecture-Anbindung, obwohl inzwischen ein separater offizieller SRT-Importer
existiert. Diese Selection-Logik wurde in diesem Abschnitt nicht umgestellt.

Discovery meldet 29 `missing_week_fixture`, sieben `local_embed_ignored` aus alten
Browser-Fixtures und eine `multiple_lecture_media_ids` in Cybersecurity Woche 0.
Web hat keine Discovery-Warnungen. Lokale Browser-Embed-Dateien werden weiterhin
ignoriert, während ihre expliziten Medienlinks erhalten bleiben.

## Tests und reproduzierbare Berichterstellung

In der tatsächlich installierten uv-Umgebung (Python 3.12.12) bestanden
**102 Offline-Tests** für Manifest, bisherige vier Kurse, Selection und die beiden
neuen Kurse. Nach Ergänzung expliziter Titelprüfungen bestanden die neun neuen
Regressionstests erneut. Socket/DNS sind in den Tests gesperrt.

Abgedeckt: alle 34 Fixture-Dateien, unveränderte bisherige 18 Einträge, sechs IDs,
Navigationsreihenfolge und Titel, Woche 0, `parsed`/`referenced`, eindeutige logische
Vorlesungen und Resource-IDs, Medien-Provenienz, TXT/SRT-Angebote, Slides/Source-PDF,
Webs imperative Liste und Satzlinks, HDR/SDR/360p–4K, unbekannte Sprache, strenge
Ablehnung ungeeigneter Videos, SDR-Auswahl, stabile Auswahl bei umgekehrter
Variantenreihenfolge und keine doppelten Video-Downloads. Vier vor der Änderung
gesicherte SHA256-Verträge prüfen die vollständigen ursprünglichen Discovery- und
Standard-Preview-Daten einschließlich IDs und Provenienz auf unveränderte Ergebnisse.

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_discovery.py tests/test_cs50_extraction.py \
  tests/test_cs50_selection.py tests/test_cs50_six_courses.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python scripts/report_cs50_sources.py
```

Der zweite Befehl erzeugt die vier genannten Markdown-Artefakte ausschließlich aus
lokalen Fixtures. Manifest-/Parser-/Selection-Läufe benötigen keine API-Keys,
Marvin, Netzwerk oder App-Runner. Ruff und `git diff --check` prüfen die Änderungen.
Keine neue Dependency, keine Migration und kein automatisches Mergen.

Der Entwicklungsabschnitt **Quellen-Discovery und Resource-Selection für sechs
CS50-Kurse** ist damit abgeschlossen. Produktive Ausführung, vollständiges Abrufen
der übrigen 29 Wochen und Lecture-/Knowledge-Export bleiben ausdrücklich spätere
Aufgaben; sie werden durch diesen Bericht nicht als abgeschlossen ausgewiesen.
