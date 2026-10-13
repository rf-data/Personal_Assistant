# CS50 Discovery

Die Modellstufe validiert das Fixture-Manifest und definiert die Zwischenmodelle.
Die zweite Stufe extrahiert Kursindex- und Wochen-Seiten offline. Notes-,
Assignment- und CDN-Detailseiten werden nicht verarbeitet; Lecture-Planung und
Netzwerk werden nicht aufgerufen. Der Parser verwendet das bereits im
`lecture-worker`-Extra deklarierte BeautifulSoup (`bs4`) mit dem
Standardbibliothek-Backend `html.parser`; neue Dependencies sind nicht erforderlich.

## Manifest

`load_fixture_manifest(Path("docs/course_sources/cs50/manifest.json"))` aus
`src/tools_lecture/cs50_manifest.py` liefert ein `FixtureManifest`.
Dateipfade sind relativ zum Manifest, nicht zum Arbeitsverzeichnis. Alle
18 vorhandenen HTML-Fixtures bleiben unverändert. Die URLs entsprechen den
Original-URLs in ihren Browser-Speicherkommentaren; insbesondere wird die
Python-CDN-Seite ihrem tatsächlichen CDN-Pfad zugeordnet.

Das kontrollierte `role`-Vokabular beschreibt **Seitentypen**:

| Wert | Bedeutung |
| --- | --- |
| `course_index` | Kursstartseite mit Navigation |
| `week_overview` | Wochen- oder Abschnittsübersicht, auch nichtnumerische IDs |
| `lecture_notes` | HTML-Lehrtext unter `/notes/` |
| `practice_overview` | nach Wochen gegliederte Practice-Übersicht |
| `assignment` | Aufgaben-/Projekt-/Quizseite oder deren kursinterne Übersicht |
| `source_code_index` | CDN-Verzeichnis mit Lecture-Quellcode |

Der Loader prüft Pydantic-Schema, Kurs-Root, Host/HTTPS, Kurs- und Rollenpfad,
Dateizuordnung, doppelte Kurse/Dateien/URLs/JSON-Schlüssel, existierende lesbare
HTML-Dateien und Pfadauflösung innerhalb des Fixture-Verzeichnisses. Ein
vorhandener `saved from url`-Kommentar muss zur Manifest-URL passen; für künftig
rohe HTML-Dateien ist der Kommentar optional. Fehler werden als `ManifestError`
mit Manifest- bzw. Dateikontext gemeldet. Es gibt keine HTTP-Erreichbarkeitsprüfung.
Die CDN-Pfadregel entspricht den belegten Lecture-Verzeichnissen und kann später
gezielt erweitert werden. Das Modell verlangt nicht, dass jeder mögliche Kurs
oder jede Woche schon lokale Fixtures hat.

## Zwischenmodelle

Die Modelle in `src/model_discovery/cs50.py` verbieten unbekannte Felder und sind
unveränderlich; Sammlungen sind Tupel. JSON-Roundtrips erfolgen über
`model_dump_json()` / `model_validate_json()`.

| Modell | Erhaltene Informationen |
| --- | --- |
| `CourseDiscovery` | Kurs-ID, Original-URL, Titel, Provider/Plattform, Status, Abschnitte, Ressourcen, Warnungen und Provenienz |
| `SectionDiscovery` | Kurs-ID, String-Schlüssel wie `0` oder `ai`, Elternschlüssel, Reihenfolge, Titel, Original-URL, Status und Provenienz |
| `ResourceCandidate` | Kurs-ID, Rolle, Original-URL, Titel, mehrere Abschnittsschlüssel, Elternressource, Sprache/Format, Status, Varianten und Provenienz |
| `MediaVariant` | Original-Angebots-URL inklusive Query, Audio/Video, Sprache, Format, Auflösung, HDR/SDR, Medien-ID und Provenienz |
| `DiscoveryWarning` | stabiler Diagnosecode, Meldung, Kurs-/optionaler Abschnittsbezug und Provenienz |
| `Provenance` | Originalseiten-URL, optionaler Fixture-Pfad, DOM-Fundstelle und Kontextpfad |

`referenced` bedeutet bekannt/verlinkt; `parsed` bedeutet tatsächlich analysiert.
Ein geparster Kurs kann weiterhin nur referenzierte Wochen enthalten. Fehlt eine
Woche lokal, kann sie mit Status `referenced` angelegt und durch eine Warnung
beschrieben werden. Der Fixture-Loader markiert keine Discovery-Objekte als geparst.

Ressourcenrollen (`ResourceRole`) sind unabhängig von Manifest-Seitenrollen:
`lecture_video`, `audio`, `notes`, `slides`, `source_code`, `subtitles`,
`transcript`, `short`, `section`, `demo`, `problem_set`, `quiz`, `project`,
`practice`, `starter_files`, `reference`, `other`.

Abschnittseltern und Ressourceneltern bilden Hierarchien innerhalb eines Kurses;
Kurszuordnung, doppelte Identitäten, unbekannte Eltern/Abschnitte und Zyklen werden
bei der Kursvalidierung geprüft. Einzelobjekte dürfen zunächst separat aufgebaut
werden, der zusammengesetzte Kurs verlangt geschlossene Referenzen.

IDs sind berechnete Eigenschaften: SHA-256 über ein eindeutig JSON-kodiertes
Identitätstupel, keine Zufallswerte und kein prozessabhängiges `hash()`.
Kurs: Kurs-ID; Abschnitt: Kurs-ID + Schlüssel; Ressource: Kurs-ID + Rolle +
Original-URL + Sprache + Eltern-ID; Variante: Medientyp + Angebots-URL.
Titel, Reihenfolge, Status, Provenienz und die Variantenliste ändern die
Ressourcenidentität nicht. Derselbe Link in mehreren Wochen wird durch mehrere
`section_keys` abgebildet. Ressourceneltern müssen deshalb zuerst gebaut werden.
Eine fachlich andere Rolle, Sprache, Elternzuordnung oder URL erzeugt eine andere
Identität. Diese erste Stufe normalisiert keine semantisch äquivalenten URLs.
Die IDs sind nicht als Eingabefelder gespeichert; nach JSON-Roundtrip werden sie
identisch neu berechnet. `model_copy(update=...)` umgeht wie bei Pydantic üblich
Validierung; für validierte Änderungen neu mit `model_validate` konstruieren.

## Späterer Export nach LectureCourse

Kurs-ID, Titel, Provider, Original-URL und Abschnittsschlüssel lassen sich auf
`LectureCourse` abbilden. Ressourcen können Titel, `source_url`, `lecture_blocks`,
Sprache-unabhängiges Dateiformat und explizit ermittelte Lecture-Nummer/Thema
liefern. Medien bieten URL/ID und Audio-/Videotyp für `LectureMedia`; Notes und
Transkripte passen zu `LectureScript`, Slides zu `LectureDocument`, Code und
Aufgaben zu `LectureMaterial`. Die Wahl von `resource_kind` ist eine spätere
explizite Mappingentscheidung.

Zusätzlich erhalten bleiben müssen Abschnittstitel/-reihenfolge/-hierarchie,
semantische Rollen, Aufgabenbeziehungen, Sprache, alle Angebotsvarianten und deren
Qualitäts-/Playerinformationen, Discovery-Status, Warnungen und Provenienz.
Die heutigen Lecture-Modelle bilden das nicht verlustfrei ab. Diese Stufe ändert
sie nicht und implementiert noch keinen Export.

## Validierung

`python -m pytest tests/test_cs50_discovery.py` prüft alle Fixtures, negative
Manifestfälle, Hierarchie, nichtnumerische Abschnittsschlüssel, deterministische
IDs und JSON-Roundtrips mit mehreren Varianten. Ein automatisch aktiver
Netzwerkwächter blockiert Sockets und DNS während der Tests.

Ausgeführt für den ersten Modell-PR: **25 Tests bestanden** mit Python 3.12.12,
Pydantic 2.14.1 und pytest 9.1.1; Ruff-Lint und Formatprüfung erfolgreich.
Die unveränderten HTML-Fixtures wurden byteweise mit dem ursprünglichen
Arbeitsbaum verglichen. Es wurden keine Projektabhängigkeiten geändert.

Die Repository-Hooks `trailing-whitespace` und `end-of-file-fixer` werden auf
Code, Manifest und Markdown geprüft. Beim Commit der unveränderten
Browser-HTML-Snapshots werden diese beiden verändernden Hooks übersprungen,
um die geforderte Byteidentität der Fixtures zu bewahren; die übrigen
konfigurierten Commit-Checks laufen auch für die Fixtures.


## Offline-Extraktion von Index und Wochen

`src/tools_lecture/prepare_cs50.py` bietet:

```python
from pathlib import Path
from src.tools_lecture.prepare_cs50 import (
    parse_course_index, parse_week_page, combine_course_pages,
    discover_fixture_courses,
)

courses = discover_fixture_courses(
    Path("docs/course_sources/cs50/manifest.json")
)

# Parser sind reine Funktionen; HTML und Originalseiten-URL explizit übergeben.
index = parse_course_index(
    index_html, "https://cs50.harvard.edu/python/",
    course_id="cs50_python", fixture_file="cs50_python/index.html",
)
week = parse_week_page(
    week_html, "https://cs50.harvard.edu/python/weeks/0/",
    course_id="cs50_python", fixture_file="cs50_python/week_0.html",
)
course = combine_course_pages(index, [week])
```

Beide Parser liefern `CourseDiscovery`. Der Wochenparser liefert einen Fragmentkurs
mit genau einem `parsed`-Abschnitt. Die Zusammenführung hält Original-URL, Titel
und Reihenfolge aus der Navigation fest; der Wochen-`h1` bleibt zusätzlich in
Provenienz und Vorlesungstitel erhalten. Nur erfolgreich geparste Wochen werden
promoviert. Nicht vorhandene Wochen bleiben `referenced` mit
`missing_week_fixture`; bei nachträglichem Ergänzen wird diese Warnung neu berechnet.

Die Hauptvorlesung ist ein `ResourceCandidate(role="lecture_video")` mit der
Wochen-URL als stabiler Original-URL und sämtlichen Videoangeboten als Varianten.
Dadurch hängt ihre ID nicht davon ab, welcher Player oder welche Qualität zuerst
angeboten wird. Sie erhält Status `parsed`, weil ihre Angebotsstruktur extrahiert
wurde. Notes, Slides, Code, Audio, Untertitel, Transkripte, Shorts, Section, Demo,
Quiz, Project und Problem Set behalten ihre verlinkte Original-URL und den Status
`referenced`: deren Inhalte wurden nicht verarbeitet. Audio-/Demo-Medienangebote
haben zusätzlich `MediaVariant`-Einträge und gehören nicht zur Video-Hauptgruppe.

Listen werden rekursiv über `ul` und `ol` traversiert. Der vollständige Kontextpfad
steht an jeder Fundstelle in `Provenance.context_path`; z. B. unterscheiden sich
`Lecture > Slides > PDF` und `Lecture > Source Code > PDF`. Pro Fundstelle bleibt
ein DOM-Pfad mit `nth-of-type` erhalten. Nicht alle Listengruppen sind eigene
Ressourcen: diese Listenhierarchie bleibt in Provenienz erhalten. Gemeinsame
Ressourcen können mehreren Wochen angehören, ohne eine einzelne Elternvorlesung
als künstlichen Besitzer festzulegen (`parent_resource_id` bleibt hier leer).

`merge_resource_candidates()` vereinigt identische Modell-IDs mit allen
Abschnittsschlüsseln, Varianten und Provenienzen. Varianten mit derselben
URL/Medientyp werden nur einmal aufgeführt; Player und YouTube bleiben verschiedene
Angebote, auch bei gleicher Medien-ID. Widersprüchliche Metadaten derselben Variante
lösen `CS50ParseError` aus, statt eine Sprach-/Qualitätsangabe still zu verwerfen.
Die Zusammenführung verarbeitet Wochen in Navigationsreihenfolge und ist bei
wiederholtem Parsing deterministisch. Der Kursstatus `parsed` bedeutet weiterhin
nicht, dass alle Abschnitte lokal vorhanden sind.

Sprachen kommen aus Sprachlabels bzw. URL-Segmenten wie `/lang/en/` oder `/pt/`;
Qualität und HDR/SDR aus Listenpfad und gegebenenfalls Dateinamen. Ohne explizite
Sprach-/Dynamikangabe bleibt das Feld `None`; es gibt keinen pauschalen
Englisch-/SDR-Default. `.mp4.download` wird als Format `mp4` erkannt, die URL bleibt
unverändert. CS50-Player-`screen`-Parameter und direkte YouTube-/Embed-URLs bleiben
erhalten. Browserlokale iframe-Dateinamen werden nicht als Medien-IDs interpretiert;
`data-src` hat Vorrang, falls dort eine echte Medienadresse erhalten geblieben ist.

Die Extraktion ist auf Navigation und Ressourcenlisten im `main` begrenzt;
`details`-Anleitungen und ihre Code-/Downloadbefehle werden nicht ausgewertet.
Einführungsvideos im Kursindex gehören nicht zur Wochenextraktion. Fehlende
Navigation/`main`/Wochenüberschrift, widersprüchliche Kurs-/Wochenzuordnung und
mehrere gleichrangige Lecture-Zweige führen zu verständlichen `CS50ParseError`-
Fehlern. Unbekannte Ressourcenrollen, ungültige Links und nicht auflösbare Embeds
werden als `DiscoveryWarning` dokumentiert. Eine strukturell lesbare Woche ohne
Vorlesung bleibt als geparster Abschnitt sichtbar, meldet aber `missing_lecture`
und erhält keine erfundene Vorlesungsressource.

Fixtures, Modelle und bisherige Lecture-/Loviscach-Pipeline bleiben unverändert.
Ein Export nach `LectureCourse` ist weiterhin nicht implementiert. Der aktuelle
[Extraktionsreport](extraction_report.md) enthält die Ergebnisse pro Kurs.
