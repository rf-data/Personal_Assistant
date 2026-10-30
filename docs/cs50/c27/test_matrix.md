# C27 Testmatrix und Akzeptanzkriterien

Stand 2026-10-29. Ergebnisse und genaue Befehle: [Validierung](validation.md).

| Gate / Gegenstand | Geprüfter Nachweis | Akzeptanz / Grenze |
|---|---|---|
| A: Content-/Materialverträge | vorhandene Content-Adapter-, Materialcontract-, Quality-, Transcript- und Week-Tests | Keine Änderungen der zentralen DTOs, IDs, Locator-/Zeitschemata; keine Gleichsetzung zeitloser Quellen mit Zeitmarken |
| B: Patch | SHA, isolierte Anwendung, Manifestvergleich, additive Ignore-Lösung, Fake-Smoke | Nur dokumentierte Ignore-Kontextabweichung; nachfolgender Fake-Label-Fix separat nachgewiesen |
| B: Engine | Scope, fehlende Quellen, Hashfehler, Originalbelege, Cacheinvalidierung, Deduplizierung, unbelegte Aussagen, Widersprüche, Syntax, Budget/Retry/Abbruch | Akzeptierte Texte stammen exakt aus referenzierten Slices; Fehler/Teilresultate bleiben sichtbar |
| B: UI | vollständige Streamlit-AppTests: Navigation, Status, Generate, Review, Cache, Exporte | Kein impliziter Provideraufruf beim Laden; Browser-/HTTP-Smoke bleibt ungeprüft |
| B: lokaler Kataloganschluss | generierte Week-0-/Week-1-Fixtures: HTML-v2 → Qualitätsgate; TXT → unbekannte Zeiten; ZIP → nur Inspektion | Beide Week-IDs korrekt, separate Lecture-/Short-Quellen; Fixture nicht als Real Data markieren |
| B: Eingabeintegrität | abweichende Inventare/Pläne, kanonischer Hash, Rohdaten/Snapshots, Summen, Duplikate, Traversal, Symlink, falscher Scope | Verarbeitung vor Ausgabestart ablehnen |
| B: Wiederaufnahme | Abbruch vor Katalogveröffentlichung, danach gleiche bestehende Bytes; manipulierte Ausgabe; geänderte Implementierung | Kein Überschreiben; vollständige Eingabe-/Ausgabeprüfung vor Cachehit; neuer Schlüssel bei Revision |
| B: Fake-Label-Regression | lange Definition mit >200 Zeichen vor „is“ | Nur Thema begrenzen; voller Originaltext und Referenz bleiben erhalten |
| C: reale lokale Dateiintegrität | zwei Inventare und zwei Pläne bytegleich; sechs Snapshotseiten; vier Downloadfiles, SHA und Bytezahlen | Alle gelieferten Dateien konsistent; keine Aussage über fehlende restliche Wochenmaterialien |
| C: reales HTML | zwei vorhandene HTML-Dateien: 65 bzw. 34 Blöcke, unverändertes Qualitätsgate und Handoff bestanden | Technischer Parsing-/Quellennachweis; vollständige gemeinsame Summaryauswahl überschreitet Chunk-Limit |
| C: reales TXT | Functions-TXT, 18 Segmente/Slices → Fake → 18 belegte Claims → zweiter Lauf aus Cache; JSON/Markdown | Originalhash/URL/Unit stimmen; Zeit/Dauer unbekannt; Ergebnis `ready_for_review`, kein fachliches Approval |
| C: reales ZIP | 777 Bytes, Verzeichnis plus drei Pythonmitglieder, CRC/Bounds/Hashes | Kein Entpacken oder Ausführen; Quellenmapping und Code-Summary noch blockiert |
| C: Ursprungsbestand | alle Dateihashes vor/nach dem externen Opt-in-Test gleich | Reviewquelle ausschließlich lesend |
| Rollout | Week-1-Generalisation nur mit Fixtures; Weeks 2–9/Kursadapter/CS50 AI spezifiziert | Für spätere Ausführung vorbereitet; keine realen Akquisitions-/Provider-/Betriebsnachweise |

Für eine **volle echte Week-0-Abnahme** fehlen: ein überprüfter vollständiger
Pflichtmaterialbestand, Code-Memberzuordnung, Review der HTML-Aggregationsgrenzen
und vollständiger Inhaltsabdeckung, Fachreview sowie getrennte notwendige
Freigaben. Der Status lautet ausdrücklich nicht „Woche abgeschlossen“.

Für einen **Providerrollout** fehlen zusätzlich reale SDK-/Providerprüfung,
explizite Daten-/Modell-/Budgetfreigabe, harter kumulativer Budgetstopp und eine
bewusste Regel für kostenpflichtige Wiederholung abgebrochener Abschnitte.
Lokale Fake- und SDK-Doppeltests decken diese Punkte nicht ab.
