# C21 – Manuelle Browser- und Materialprüfung

Diese Vorlage ist eine offene Reviewstruktur, kein ausgefülltes menschliches
Abnahmeprotokoll. `not tested` bleibt bestehen, bis eine Person den Originalbezug
und das beobachtete Ergebnis dokumentiert. Ein technisches `passed` ist keine
Bestätigung fachlicher Richtigkeit oder Vollständigkeit.

## Protokollkopf

- Reviewer, Datum/Zeitzone, geprüfte Versionen, Browser und Auflösung:
- Dokument-ID, Source-/Resource-/Material-ID, Quell-URL und Raw-SHA-256:
- Course, Section, Lecture-ID, Normalized-SHA-256 und Parserkonfiguration:
- Block-IDs / DOM-Pfade beziehungsweise Seiten/BBoxes der Stichproben:
- Unabhängige Referenz und deren Herkunft (nicht aus der Vorhersage erzeugt):
- Ergebnis: `passed`, `failed`, `skipped`, `blocked` oder `not tested`:

## Browserabnahme

| Prüfung | Erwartung | Ergebnis / Beobachtung |
| --- | --- | --- |
| Login und Rollenwechsel | nur freigegebene Identität/Courses, keine Daten des vorherigen Owners | not tested |
| Preview / Graph | alle fünf Stufen, tatsächliche Entscheidungen und Referenzen lesbar | not tested |
| Execute / Resume | jeweils bewusste Checkbox, genau eine Mutation | not tested |
| Polling, Seitenwechsel, Refresh | keine automatische zusätzliche Ausführung, Pending-Intent bleibt nachvollziehbar | not tested |
| Antwortverlust / Backendausfall | sicherer Fehler, gleicher Retry-Body/Key, kein erfundener Erfolg | not tested |
| Cancel / Timeout / Restart | echte Zwischen- und Endzustände, explizites Resume möglich | not tested |
| Historie / Artefakte / Logs | ursprünglicher Run statt heutiger Skip-Projektion, richtige Hashart und Produzenten | not tested |
| TLS / OIDC / Produktionskonfiguration | separate freigegebene Umgebung nötig, hier keine Aktivierung | not tested |

## Fachliche Materialprüfung

| Bereich | Nachvollziehbare Stichprobe | Ergebnis |
| --- | --- | --- |
| Textvollständigkeit | erster/letzter Inhaltsabschnitt und mindestens ein mittlerer Absatz gegen Original; konkrete Auslassungen nennen | not tested |
| Struktur | Überschriftenebenen, Listen und Reihenfolge; TOC-/Linkprojektionen nicht doppelt aggregiert | not tested |
| Tabellen | Zeilen-/Spaltenbezug gegen Original; geometrische Projektionen und Unsicherheit getrennt | not tested |
| Code | Originalzeichen, Einrückungen/Zeilennummern; `code_view` als abgeleitete Sicht und nicht als zweite Quelle | not tested |
| Formeln | Operatoren, Exponenten, Indizes, Brüche und Gültigkeitsbereich; unabhängige Goldpaare im C11-Vertrag | blocked ohne reale Goldannotation |
| Bilder | C13-Asset-ID, DOM/Seite/BBox, lokaler Byte-/Hashstatus, Caption und fehlende Vektoren; ohne Bytes kein inhaltliches Urteil | not tested |
| Provenienz | Original-SHA, Binding, Block-ID und Fundstelle durch alle Artefakte verfolgen | not tested |
| Fehlende Inhalte | konkrete Originalfundstelle, erwarteter Inhalt, vorhandene Extraktion und Schweregrad | not tested |
| Knowledge-Nutzbarkeit | konkrete referenzierbare Aggregationseinheiten; keine erfundenen Transcript-Zeitintervalle | not tested |

C10 unterscheidet technische Befunde und `semantic_review`. C11 erlaubt
`undetermined` und meldet unbekannte Syntax ausdrücklich. C13 unterscheidet
Referenz, verfügbare Bytes, Unsicherheit und Reviewbedarf. Diese Grenzen bei jeder
Beobachtung erhalten; keine synthetische Erfolgsquote als reale Modellqualität.

Für Week-0-PDFs benötigt: lokal bereitgestellte Original-Slides und Source-Code-PDF,
zugehörige Original-URLs, überprüfte Course-/Section-/Lecture-/Resource-Bindung und
Quell-SHAs. Für mathematische Qualität zusätzlich unabhängig annotierte Original-
und Referenzformeln mit Seiten-/Blockbezug sowie getrennte Predictions. Kein Download.
