# CS50 Discovery: erste Stufe

Diese Stufe validiert das Fixture-Manifest und definiert die Zwischenmodelle.
Sie extrahiert noch keine HTML-Ressourcen und ruft weder Netzwerk noch
Lecture-Planung auf. Pydantic und Standardbibliothek reichen für den Laufzeitcode.

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

Ausgeführt für diesen PR: **25 Tests bestanden** mit Python 3.12.12,
Pydantic 2.14.1 und pytest 9.1.1; Ruff-Lint und Formatprüfung erfolgreich.
Die unveränderten HTML-Fixtures wurden byteweise mit dem ursprünglichen
Arbeitsbaum verglichen. Es wurden keine Projektabhängigkeiten geändert.

Die Repository-Hooks `trailing-whitespace` und `end-of-file-fixer` werden auf
Code, Manifest und Markdown geprüft. Beim Commit der unveränderten
Browser-HTML-Snapshots werden diese beiden verändernden Hooks übersprungen,
um die geforderte Byteidentität der Fixtures zu bewahren; die übrigen
konfigurierten Commit-Checks laufen auch für die Fixtures.
