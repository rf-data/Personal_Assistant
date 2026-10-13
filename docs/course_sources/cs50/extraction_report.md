# CS50: Offline-Extraktionsreport

Grundlage: die vier Kursindex- und sieben Wochen-Fixtures aus dem validierten
`manifest.json`. Die übrigen sieben Detail-Fixtures werden nicht extrahiert.
Erzeugt mit `discover_fixture_courses()`; keine HTTP-Anfragen, Downloads,
Transkriptionen oder LLM-Aufrufe. Der PR baut auf dem Modell-PR #6 auf.

## Übersicht

| Kurs | Abschnitte | parsed / referenced | Hauptvorlesungen | Ressourcen | Video-Hauptangebote | Alle Medienvarianten |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| cs50x | 12 | 2 / 10 | 2 | 38 | 60 | 63 |
| cs50_python | 10 | 2 / 8 | 2 | 28 | 14 | 16 |
| cs50_sql | 7 | 2 / 5 | 2 | 22 | 20 | 22 |
| cs50_ai | 7 | 1 / 6 | 1 | 11 | 6 | 7 |

„Alle Medienvarianten“ enthält zusätzlich sieben Audioangebote und eine Demo.
Player und YouTube zählen als separate Angebote; Auflösung, HDR/SDR und
Sprachfassung werden nicht zu neuen Vorlesungen. Insgesamt: **7 Hauptvorlesungen,
100 Video-Hauptangebote, 108 Medienvarianten und 99 Ressourcenkandidaten**.

## Ressourcentypen

| Rolle | CS50x | Python | SQL | AI |
| --- | ---: | ---: | ---: | ---: |
| lecture_video | 2 | 2 | 2 | 1 |
| audio | 2 | 2 | 2 | 1 |
| notes | 2 | 2 | 2 | 1 |
| slides | 4 | 4 | 4 | 2 |
| source_code | 6 | 6 | 6 | 2 |
| subtitles | 6 | 2 | 2 | 1 |
| transcript | 6 | 2 | 2 | 1 |
| short | 6 | 6 | 0 | 0 |
| section | 1 | 0 | 0 | 0 |
| demo | 1 | 0 | 0 | 0 |
| problem_set | 2 | 2 | 2 | 0 |
| quiz | 0 | 0 | 0 | 1 |
| project | 0 | 0 | 0 | 1 |

Slides-PDFs und Source-Code-PDFs sind getrennte Rollen; die Quellenpfade stehen
an jeder Ressource in der Provenienz. Notes, Aufgaben, Shorts und CDN-Indizes
sind ausschließlich verlinkte Referenzen. Keine ihrer Inhalte wurde importiert.

## Kursdetails

### cs50x

**Navigationsreihenfolge:** 0, 1, 2, 3, 4, 5, 6, 7, ai, 8, 9, 10.

**Abschnittstitel in derselben Reihenfolge:** Week 0 Scratch; Week 1 C; Week 2 Arrays; Week 3 Algorithms; Week 4 Memory; Week 5 Data Structures; Week 6 Python; Week 7 SQL; Artificial Intelligence; Week 8 HTML, CSS, JavaScript; Week 9 Flask; Week 10 The End.

**Geparste Hauptvorlesungen:**

- Week 0 Scratch: 30 Angebote (3 CS50-Player, 3 YouTube, 24 MP4).
- Week 1 C: 30 Angebote (3 CS50-Player, 3 YouTube, 24 MP4).

**Varianten:** je Woche 10 Angebote für `en`, `pt`, `es`; je Sprache
acht MP4-Angebote aus HDR/SDR × 360p/720p/1080p/4K. Untertitel und
Transkripte haben ebenfalls alle drei Sprachfassungen. „This is CS50“ ist eine
separate Demo in Woche 0 und wird nicht in die Hauptvorlesung aufgenommen.

**Discovery-Warnungen:**

- `missing_week_fixture`: 10 (Abschnitte 2, 3, 4, 5, 6, 7, ai, 8, 9, 10); sie bleiben `referenced`.
- `local_embed_ignored`: 2 (Wochen 0, 1); lokale Browser-iframe-Adressen werden zugunsten der expliziten Medienangebote ignoriert.
- Keine unbekannten Ressourcenrollen, ungültigen Links oder fehlenden Hauptvorlesungen in den geparsten Fixtures.

### cs50_python

**Navigationsreihenfolge:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9.

**Abschnittstitel in derselben Reihenfolge:** Functions, Variables; Conditionals; Loops; Exceptions; Libraries; Unit Tests; File I/O; Regular Expressions; Object-Oriented Programming; Et Cetera.

**Geparste Hauptvorlesungen:**

- Week 0 Functions: 7 Angebote (1 CS50-Player, 1 YouTube, 5 MP4).
- Week 5 Unit Tests: 7 Angebote (1 CS50-Player, 1 YouTube, 5 MP4).

**Varianten:** je Vorlesung HDR in 4K sowie SDR in 360p/720p/1080p/4K;
Untertitel/Transkripte mit explizitem `en`. Die Videolinks tragen kein
explizites Sprachlabel, daher Sprache `None`. Der Navigationstitel
„Functions, Variables“ bleibt erhalten; der Wochen-Titel „Week 0 Functions“
steht zusätzlich in Provenienz und Hauptvorlesung.

**Discovery-Warnungen:**

- `missing_week_fixture`: 8 (Abschnitte 1, 2, 3, 4, 6, 7, 8, 9); sie bleiben `referenced`.
- `local_embed_ignored`: 2 (Wochen 0, 5); lokale Browser-iframe-Adressen werden zugunsten der expliziten Medienangebote ignoriert.
- Keine unbekannten Ressourcenrollen, ungültigen Links oder fehlenden Hauptvorlesungen in den geparsten Fixtures.

### cs50_sql

**Navigationsreihenfolge:** 0, 1, 2, 3, 4, 5, 6.

**Abschnittstitel in derselben Reihenfolge:** Querying; Relating; Designing; Writing; Viewing; Optimizing; Scaling.

**Geparste Hauptvorlesungen:**

- Week 0 Querying: 10 Angebote (1 CS50-Player, 1 YouTube, 8 MP4).
- Week 6 Scaling: 10 Angebote (1 CS50-Player, 1 YouTube, 8 MP4).

**Varianten:** je Vorlesung HDR/SDR × 360p/720p/1080p/4K; `screen`-Parameter
der CS50-Player bleiben unverändert. Untertitel/Transkripte mit `en`,
Videosprachen ohne explizite Angabe bleiben `None`.

**Discovery-Warnungen:**

- `missing_week_fixture`: 5 (Abschnitte 1, 2, 3, 4, 5); sie bleiben `referenced`.
- `local_embed_ignored`: 2 (Wochen 0, 6); lokale Browser-iframe-Adressen werden zugunsten der expliziten Medienangebote ignoriert.
- Keine unbekannten Ressourcenrollen, ungültigen Links oder fehlenden Hauptvorlesungen in den geparsten Fixtures.

### cs50_ai

**Navigationsreihenfolge:** 0, 1, 2, 3, 4, 5, 6.

**Abschnittstitel in derselben Reihenfolge:** Search; Knowledge; Uncertainty; Optimization; Learning; Neural Networks; Language.

**Geparste Hauptvorlesungen:**

- Week 1 Knowledge: 6 Angebote (1 CS50-Player, 1 YouTube, 4 MP4).

**Varianten:** vier MP4-Angebote 360p/720p/1080p/4K mit unveränderter
`.mp4.download`-URL; CS50-Player mit `screen`; englische Untertitel/Transkripte.
Video-Sprachlabel und HDR/SDR sind nicht angegeben und bleiben `None`.
Quiz 1 und Project 1 sind Referenzen; die vorhandene Shopping-Detailseite
(Project 4) wird in dieser Stufe nicht verarbeitet.

**Discovery-Warnungen:**

- `missing_week_fixture`: 6 (Abschnitte 0, 2, 3, 4, 5, 6); sie bleiben `referenced`.
- `local_embed_ignored`: 1 (Wochen 1); lokale Browser-iframe-Adressen werden zugunsten der expliziten Medienangebote ignoriert.
- Keine unbekannten Ressourcenrollen, ungültigen Links oder fehlenden Hauptvorlesungen in den geparsten Fixtures.

## Tests

`python -m pytest tests/test_cs50_extraction.py tests/test_cs50_discovery.py`
prüft Navigation, Woche 0, Rollen anhand vollständiger Listenpfade, Sprach- und
Qualitätsvarianten, Playerparameter, lokale/live Embeds, Demo-Abgrenzung,
Mehrfachzuordnung, Deduplizierung, deterministische Ergebnisse, inkrementelle
Zusammenführung und strukturelle Fehler. Alle Tests blockieren Netzwerkzugriffe.

**69 Tests bestanden** (44 Extraktions- und 25 bestehende Manifest-/Modelltests)
mit Python 3.12.12, Pydantic 2.14.1, BeautifulSoup 4.15.0 und pytest 9.1.1.
Ruff-Lint/Formatprüfung und die konfigurierten Commit-Checks sind erfolgreich.
Keine Projektabhängigkeiten wurden geändert.
