# C27 Phasen 3 und 4: Generalisierung und Kursrollout

Stand 2026-10-29. **Für spätere Ausführung vorbereitet**, soweit unten nicht
explizit als Fixture-Test markiert. Keine neuen Kursdownloads, Provideraufrufe
oder Produktionsänderungen. Kursstruktur und Kandidaten beruhen auf den bereits
vorhandenen Repo-Snapshots; kein aktueller Online-/Lizenzabgleich wurde ausgeführt.

## Phase 3: CS50P Week 1 als Generalisierungspilot

Die neue lokale Brücke wird mit synthetischen Inventaren für Week 0 **und Week 1**
geprüft: verschiedene Week-IDs und URLs, separate Lecture-/Short-Units, HTML,
TXT, ZIP, Hashbindung, Handoff, Fake-Summary, Cache und unterbrochene
Veröffentlichung. Das ist eine Generalisierungsprüfung der Verträge, keine echte
Week-1-Abnahme. Die Fixture benutzt Functions-Beispieltext; daraus wird keine
Aussage über Week-1-Lehrinhalte abgeleitet.

Für den späteren echten Pilot gilt folgende Reihenfolge:

1. Expliziten lokalen Snapshot und Quellenumfang für Week 1 auswählen. Bestehende
   Downloadwerkzeuge können nach Freigabe den Snapshot liefern. Geplante URLs
   müssen aus tatsächlichen Links stammen; kein Raten von Dateinamen.
2. Inventar nach Lecture, Short, Notes, Slides, Code, Transcript/Subtitles und
   Problem-Set aufbauen. Erwartungsledger und Elternbeziehungen reviewen. Bereits
   vorhandene Einzelaufgaben dürfen nicht durch eine Übersichtsseite als erfüllt
   gelten. Nicht unterstützte Formate explizit offen halten.
3. Download-, Lizenz- und LLM-Freigaben getrennt dokumentieren (siehe unten).
   Auswahlvorschläge bleiben pending. Keine automatische Übertragung von Week 0.
4. Zuerst eine begrenzte HTML-/TXT-Auswahl offline verarbeiten. Prüfen, dass
   Referenzen/Navigation nicht als zusätzliche Lehrinhalte erscheinen, unbekannte
   Zeiten unbekannt bleiben und Lecture/Short-Quellen getrennt bleiben.
5. Einen vollständigen Processing-Rerun und einen kontrollierten Abbruch zwischen
   Artefakt- und Quittungsveröffentlichung prüfen. Ändert sich eine Quelle oder
   Implementierung, entsteht ein neuer Schlüssel; alte Ergebnisse bleiben erhalten.
6. Fake-Summary mit expliziter, unterhalb der Bounds liegender Auswahl erzeugen.
   Alle akzeptierten Aussagen auf genaue Originalstellen prüfen; Markdown/JSON
   exportieren. Providerqualität ist damit noch nicht geprüft.
7. Erst nach separater LLM-Freigabe: begrenzter Providerpilot mit bekanntem
   Preis-/Token-/Zeitlimit. Fachreview pro Aussage und gesonderte Gesamtentscheidung.

Week-1-Abnahme erfordert: alle ausgewählten Originalhashes, korrekte Kurs-/Unit-
Bindung, bestandenes Qualitätsgate, belegte Locators, konsistente Exporte,
Idempotenz/Wiederaufnahme, keine stillen Auslassungen und dokumentierte offene
Materialtypen. Ein vollständiger Wochenabschluss erfordert zusätzlich die
Erfüllung des separat reviewten Erwartungsledgers und Fachfreigabe.

Gate B und diese Pilotvorbereitung sind unabhängig von Gate C. Ein tatsächlicher
Mehrwochenbetrieb wird erst freigegeben, wenn seine eigene Quellen-, Lizenz-,
Qualitäts- und Betriebsabnahme vorliegt.

## Phase 4: CS50P Weeks 2–9

| Welle | Vorbereitung | Freigabe zur Ausführung |
|---|---|---|
| Week 2 | identische Verträge an einem weiteren Inventar bestätigen; Abweichungen zu Week 1 erfassen | Week-1-Technikpilot und separate Week-2-Grants |
| Weeks 3–4 | je Woche eigenes Inventar, Teilpläne, Test- und Budgetbericht | vorherige Welle ohne ungeklärte Quellen-/Resume-Konflikte |
| Weeks 5–6 | parser- und materialtypspezifische Lücken prüfen; Code/Archive getrennt zuordnen | explizite Material- und Memberfreigaben; keine Sammelannahme |
| Weeks 7–9 | dieselben Verträge; größere Medien-/Projektdateien gesondert bewerten | Review je Woche, ausreichende Kapazität, eigene Freigaben |

Dies sind sequentielle Planungswellen, keine behaupteten Laufzeiten oder
vollständigen Materiallisten. Maximal eine Woche und ein Materialprozess
zeitgleich. Nach jedem Batch Status, Ausgaben, Fehler, verbleibende Budgets und
nächste Handlung festhalten. Keine globale Wiederholung erfolgreicher Downloads.
Ein Fehler einer Unit hält ihre Abnahme offen; unabhängige Units dürfen unter
ihren eigenen Grants fortgesetzt werden. Eine fehlende Pflichtquelle verhindert
den Wochenabschluss, nicht die Dokumentation bereits bestandener Teile.

## Kursadapter und CS50 AI

Ein künftiger Kursadapter liefert eine unveränderte Schnittstelle:

- Course-/Section-/Unit-Identitäten, explizite Materiallinks und Elternbeziehungen;
- versioniertes Inventar plus Pflicht-/Optional-/Alternativledger;
- ResourceCandidate/MaterialResource mit Original-URL und Provenienz;
- unterstützte Parserroute und deren Grenzen, kein stiller Fallback auf LLM;
- ContentBlock/ContentLocator oder TranscriptDocument plus Qualitätsnachweise;
- Summary-Katalog und getrennte Auswahl-, Review- und Freigabeinformationen.

Kursabhängig bleiben Linkdiscovery, Erwartungen, Titel und Formatangebote.
Parser-, Quellen-, Cache- und Reviewlogik bleiben gemeinsam. Nicht temporale
Materialien erhalten keine erfundenen Transcript-Zeitstempel. Neue Formate brauchen
einen eigenen getesteten Adapter, ehe sie als abgeschlossen gelten.

**CS50 AI ist der nächste Kurskandidat**, wie beauftragt. Vorhandene CS50-AI-
Repo-Snapshots und Discoveryverträge dienen später zur Planung. Als erster Pilot
ist eine explizit abgegrenzte Lecture mit Textmaterial vorgesehen; genaue Einheit,
Links und Umfang werden vor Download anhand des dann freigegebenen Inventars
bestimmt. Notebook-/Projekt-/Daten-/Archivdateien bleiben getrennt zu prüfen;
Code wird statisch verarbeitet, nicht ausgeführt. Keine automatische Übernahme
von CS50P-Lizenzen oder CS50P-Budgets. Der Kursadapter ist hier spezifiziert,
aber noch nicht als neuer Adapter implementiert oder mit echten AI-Daten getestet.

## Getrennte Freigaben

| Freigabe | Erforderlicher Reviewinhalt | Kein impliziter Folgeauftrag |
|---|---|---|
| Download | Inventarhash, einzelne Material-IDs/URLs/Formate, Byteobergrenzen, Reviewer und Referenz | keine Verarbeitung, kein LLM, keine Folge-Downloads |
| Lizenz/Nutzung | Quelle, Lizenzstand, erlaubter Zweck, Attribution und Umgang mit abgeleiteten Ausgaben | Downloadbericht-Lizenzstring allein genügt nicht; keine rechtliche Prüfung in C27 |
| Lokale Verarbeitung | vorhandene Rohdaten, Hashes, Parser, getrennte Ausgabe, Bounds und Quellenmapping | keine Produktion oder Codeausführung |
| LLM | konkreter Provider/Modell, Materialauswahl, Preisstand, Datenübertragung, Token-/Geldlimit, Timeout/Retry | keine Veröffentlichung oder Gesamtfreigabe |
| Fachreview/Veröffentlichung | einzelne Behauptungen, Belegstellen, Widersprüche und Gesamtentscheidung | technische Gate-Erfolge sind keine Fachfreigabe |

Diese Tabellen bereiten spätere Entscheidungen vor. Für den aktuellen Auftrag
sind nur lokale Datei- und Offline-/Fake-Prüfungen autorisiert.

## Budget- und Wiederaufnahmeregeln

Akquisitionsvertrag aus 07/08: ein Prozess, maximal 32 MiB Transfer/Batch,
64 MiB Archiv, 16 MiB Berichte, 5 GiB freie Reserve, 540 s Wall-Time. HTML/TXT
je höchstens 1 MiB, Untertitel 2 MiB, PDF 8 MiB, Code/ZIP je 1 MiB; ZIP maximal
64 Mitglieder, 8 MiB entpackte Größe im Speicher, Ratio 100 und 5 s Inspektion.
Die neue lokale Brücke übernimmt keine Downloads und beschränkt ihren Reviewbatch
zusätzlich auf 32 Dateien/Snapshots und 16 MiB Ausgaben. Die Gesamtzeit- und
Prozessisolierung des 08-Produktionsworkers wird dadurch nicht ersetzt; für die
Reviewbrücke wird kein harter OS-Zeit-/RAM-Sandboxnachweis behauptet.

Summary-Grenzen bleiben: standardmäßig 24 Chunks à 2.000 Zeichen, maximal
32 Chunks, 24.000 Request-Bytes, 1.500 Outputtokens/Request, 20 s Timeout,
120 s pro Lauf und null Retries (vertragliche Obergrenzen siehe SummaryConfig).
Grenzüberschreitungen führen zu offenem Status; Auswahl gezielt verkleinern.
Keine verdeckte Inhaltskürzung. Eine vollständige Zusammenführung großer HTML-
Units benötigt später eine gesondert geprüfte hierarchische Lösung; fremde
C27c-Branches werden dafür nicht übernommen.

Aktuelles externes LLM-Budget: **0 Aufrufe / 0 Kosten autorisiert**. Für spätere
Providerläufe vorab harte Gesamtschranken festlegen: maximale Requests,
Input-/Outputtokens und Geldbetrag; Worst Case aus Requestzahl, Kontext-/Output-
Bounds und zum Freigabezeitpunkt geprüften Preisen berechnen. Unbekannte Usage
als unbekannt ausweisen, nicht als kostenlos. Die bestehende Engine zählt Usage
und berechnet Kosten bei konfigurierten Preisen; ein harter kumulativer Geldstopp
ist hier noch nicht implementiert und ist vor Mehrwochen-Providerbetrieb nötig.

Processing-Resume prüft Rohdaten/Report/Implementierung und sämtliche quittierten
Ausgaben. Gleiche Bytes werden wiederverwendet; veränderte Quellen/Parser erhalten
neue Schlüssel. Widersprüche erfordern Prüfung, niemals Überschreiben/Force.
Der Summarizer cached abgeschlossene Läufe. Fehlgeschlagene/abgebrochene Läufe
bewahren Rohantworten und Abschnitte, starten beim nächsten Versuch aber neu;
ein Abschnitts-Resume mit Fortsetzung bezahlter Calls ist noch nicht implementiert.
Dafür muss vor Providerrollout eine gesonderte Abrechnung-/Resume-Regel entstehen.
