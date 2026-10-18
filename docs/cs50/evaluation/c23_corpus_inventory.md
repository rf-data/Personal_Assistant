# C23-06: Tatsächlich versionierter Korpus und Datenlücken

18.10.2026, Basis Master `d654f0580f6c5d6aa5698f33dc5c93dec5ba66d5`.
[Maschinenmanifest](c23_06/corpus_manifest.v1.json),
[beobachtetes Inventar](c23_06/corpus_inventory.v1.json),
[Evaluation und Testresultate](c23_real_material_evaluation.md).

## Freigegebener Umfang

Die ausdrückliche Klarstellung des Auftraggebers erlaubt ausschließlich bereits
versionierte CS50-Fixtures und HTML-Snapshots zur **technischen Prüfung**. Keine
zusätzlichen lokalen Raw-/Receipt-/Parsed-Bundles, privaten Datenbestände oder
bestätigten unabhängigen Goldreferenzen sind freigegeben. Nach dieser Klarstellung
wurden keine zusätzlichen lokalen Originalpfade untersucht oder übernommen.
Keine Downloads, Originalkopien, Pfadkorrekturen oder produktiven Storeimporte.

Die Auswahl folgt den fünf ausdrücklich als `lecture_notes`/`assignment`
bezeichneten Seiten im vorhandenen
[CS50-Snapshotmanifest](../../course_sources/cs50/manifest.json). Index-/Week-/Linkseiten
sind Discoverybelege, keine zusätzlichen ausgewerteten Vorlesungsmaterialien.
Der vorhandene Manifestvalidator prüft seine explizite Liste und Hashes; es gibt
keine rekursive Suche nach Kursdateien in persönlichen Verzeichnissen.

## Fünf reale HTML-Rohsnapshots

| Datei unter `docs/course_sources/cs50/` | Kurs / Section | Größe, Bytes | Raw-SHA256 |
| --- | --- | ---: | --- |
| `cs50x/lecture_0.html` | `cs50x` / `0` | 669940 | `e966a32e53130acdc6c821ab77343f8a251688e52e93eb1dd12312451be2280b` |
| `cs50_python/lecture_5.html` | `cs50_python` / `5` | 89139 | `0855465b0458067ce5b6889d5e3929a49de108aa8d01d877c25e80bea0cd8367` |
| `cs50_python/practice_1.html` | `cs50_python` / nicht unabhängig gebunden | 54172 | `e01e960e04562376f0381732f8a72f3883012e945bc10d2dbb93cf791a1ef6cd` |
| `cs50_ai/lecture_1.html` | `cs50_ai` / `1` | 114568 | `27f12cea52cf1fb33444ed63dd50cdec230f1b48bd8f370f208a743db5aa4e40` |
| `cs50_ai/practice.html` | `cs50_ai` / nicht unabhängig gebunden | 69881 | `27dd092c335a06c6f52e7e22dcdb64349c6492c73d340642f83bc881357e000b` |

Gesamt **997700 Rawbytes**. Alle fünf beobachteten SHAwerte stimmen mit dem
vorhandenen Snapshotmanifest überein. Original-URLs und tatsächlich belegte
Resource-/Material-/Lecture-IDs stehen vollständig im Maschinenmanifest.
Die drei Notes-Ressourcen haben vorhandene Discovery-Identitäten; für beide
Assignments liefert der aktuelle Discoverygraph keine passende Resource-ID.
Diese IDs bleiben ausdrücklich `null`, nicht aus der URL erfunden.

Für **alle fünf** gilt:

- Originalraw vorhanden und hashgeprüft; Nutzungsumfang technische Inventur.
- Kein vollständiges freigegebenes Receipt-/Parsed-/Plan-/Revisionsbundle.
- Parser-/Schemaversion eines solchen Parsedartefakts: nicht nachgewiesen.
- SourceVersion und bestätigte Originallocator-/Blockreferenzen: nicht vorhanden.
- Source-Binding nicht vollständig verifiziert, Receipt nicht geprüft.
- Kein verifizierter aktueller Qualityreport über ein solches vollständiges Bundle.
- ContentStore-Publikation **nicht geprüft**; es wurde kein Store ausgewählt.
- Kein bestätigtes unabhängiges Gold; fünf leere Pending-Reviewaufträge.
- Klassifikation `real_incomplete_bundle`, keine fachliche Parsingbewertung.

Der historische C21-Lauf an Python Notes Week 5 bewies HTML-v2/C10/Handoff und
C13 technisch. Sein damaliger Text-/Blockbestand und sein „passed“ werden nicht
zu neuem Bundle, unabhängiger Goldreferenz oder aktuellem Persistenznachweis erklärt.

## Vier versionierte synthetische Rohfixtures

| Eintrag | Datei | Bytes | Zweck |
| --- | --- | ---: | --- |
| C10 HTML | `tests/fixtures/material_quality/notes.html` | 492 | TOC, Listen, Linkprojektion, Code, Bildreferenz |
| C10 PDF | `tests/fixtures/material_quality/source.pdf` | 1629 | Kleine synthetische PDFquelle; native Parserabnahme benötigt PyMuPDF |
| C13 HTML | `tests/fixtures/visual_inventory/source.html` | 1088 | Bildreferenzen, Inline-SVG und technische Visualinventur |
| Offizieller Import-Beispieltext | `docs/course_sources/cs50/examples/official_transcript.txt` | 110 | Ausdrücklich synthetischer zeitloser Text; keine reale TXT-Kompatibilitätsfreigabe |

Raw-SHAwerte im Inventar. Die C13-Datei `source.pdf.b64` ist zusätzlich eine
versionierte **kodierte** synthetische PDF-Fixture mit eigenem README/Generator;
ihre Base64textbytes werden nicht als Original-PDFbytes inventarisiert. Die Tests
dürfen bestehende synthetische Fixtures temporär aufbauen, aber keine privaten
Originale ersetzen. Auch die 42 C11-Formelfälle bleiben ausschließlich synthetisch.

Die vier Rohfixtures sind keine vollständigen persistierbaren Bundles. Separate
Frameworktests erzeugen ausdrücklich eigene kleine, gültige B-Testbundles und
prüfen deren technische Integrität/Publikation/Idempotenz; solche temporären
Testoutputs sind **nicht** reale Korpuseinträge oder neue unabhängige Realgoldfälle.

## Sechs bewusst offene Realmaterialgruppen

| Gruppe | Aktueller Befund / nächster erforderlicher Beleg |
| --- | --- |
| Python Week-0 Notes HTML | Original-/Receipt-/Parsedworkspace nicht freigegeben; Week-5-Datei ist kein Ersatz |
| Week-0 Lecture Slides PDF | URL/historischer Hash dokumentiert, aber kein freigegebenes vollständiges Bundle; kein Download |
| Week-0 Source-Code-PDF | Eigenes PDFformat; weder dieses Originalbundle noch ein eigenständiges reales Codeartefakt freigegeben |
| Standalone Code | Keine freigegebene Originaldatei mit Source-/Receipt-/Parservertrag |
| Python Week-0 SRT | Versionierter Adapterplan enthält Resource-/Section-/Lecturebindung. Private Dateien sind nicht freigegeben; #72/D06 bleibt blockiert. Keine alternative Rootsuche oder byteidentische Kopie als Freigabe |
| Reales TXT | Kein Originalbundle. C23-05/#81 ist inzwischen gemergt und technisch regressionsgeprüft; daraus folgt keine reale TXT-/ContentStorefreigabe |

Die Lückeneinträge haben keine ausgewählten lokalen Artefaktpfade. `available=null`
bedeutet nicht bereitgestellt, nicht „überall auf dem Host nachweislich abwesend“.
Für reale PDFs, Code, SRT, TXT, Bildbytes, Tabellen- und Formelreferenzen existiert
deshalb keine repräsentative oder fachlich bestätigte Stichprobe.

## Konsequenz für die Abnahme

**15 Einträge = 5 reale Raw-Snapshots + 4 synthetische Raw-Fixtures + 6 Datenlücken.**
Neun ausgewählte Rohdateien sind verfügbar, null vollständige Realbundles geprüft,
null reale Referenzen evaluierbar. Fünf Reviewaufträge sind `pending_review`, zehn
Einträge haben keinen Reviewauftrag; alle 15 haben kein bestätigtes Gold.
Kein HTML/PDF/Code/SRT/TXT-Format erhält hier eine fachliche Freigabe.
Der konkrete Übergabeplan steht im [Abnahmebericht](c23_real_material_evaluation.md).
