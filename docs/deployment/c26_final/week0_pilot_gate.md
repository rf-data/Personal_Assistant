# CS50P Week 0 Pilot Gate – 23.10.2026

Entscheidung: **blocked** für reale Ausführung. Neuer Stand auf
`c4b057a75c38655e43b8ac35a35cc82645ba2826`; Source-/Job-/Pilotoriginale unverändert.
Technische Child-Rekonstruktion ist mit dem ausdrücklich gewählten Snapshot-v2-
Vertrag offline funktionsfähig. Produktive Ausführung und fachliche Vollständigkeit
sind davon getrennt und nicht abgenommen.

Maschinenbelege: `week0_pilot_gate.v1.json`, `source_approval_matrix.v1.json` und
`validation.v1.json`. Historische Inventur aus #154 wird wiederverwendet:
[21 Ressourcen / 28 Varianten](../c26a/week0_final_plan.v1.json),
[zehn ZIPs mit vollständigen Metadaten](../c26a/manual_zip_inventory.v1.json).

## Vollständiger belegter Scope

| Materialgruppe | Vorhanden / Referenz | Aktueller Verarbeitungsstand |
| --- | --- | --- |
| Lecture Notes | Original, normalisierte 237 Blöcke, 34 Codeblöcke, Qualitäts-/Handoffexport | Rawhash und historische Modelle vorhanden; echte #149-Projektion geprüft, neuer vollständiger Produktionskettenbeleg/Grant fehlt |
| PSet-0-Übersicht | Original, 28 normalisierte Blöcke, zehn Links einschließlich aller fünf Aufgaben, Qualitäts-/Handoffexport | Wie Notes; Link-/Listen-/Parentprojektion geprüft, keine historischen Reports umgedeutet |
| Fünf Aufgaben | URLs, historische IDs, Parent und DOM-Provenienz belegt; Indoor-Voice-Discoveryfixture vorhanden | V2 rekonstruiert die fünf Bindungen in Planer, Katalogindex und Worker; vier vollständige Aufgabenoriginale fehlen, Fixture ist keine neue Produktionsfreigabe |
| Slides-PDF und Code-PDF | Zwei konkrete Referenzen | Vorhandener PDF-v2-Weg, Originalvergleich weiterhin offen |
| SRT / TXT | Zwei getrennte Source-/Lecture-Referenzen | Bestehender Transcriptimport mit Zeitstempeln; freigegebene Originalraws fehlen |
| Audio | Eine MP3-Referenz | Kein genehmigtes Raw; kein Transkriptionsauftrag |
| Lecture-Video | Acht Varianten/Player-/YouTube-/MP4-Bindungen | Keine acht abgeschlossenen Vorlesungen; Media-Plan-only |
| Shorts | Fünf Referenzen | Medienraws/Verarbeitung offen |
| Google Slides | Eine Referenz | Kein impliziter Export oder Ersatz durch ein unbekanntes PDF |
| Codeindex | Bereits gespeicherter Snapshot, 24 direkte Pythonreferenzen für Woche 0 | `manual_only`, keine Beschaffung; vorhandene IDs für mögliche Mitglieder wiederverwendet |
| ZIPs | Zehn vorhandene Rawarchive für Woche 0–9, Hashes gegen #154 unverändert | Keine Kopien/Extraktionen oder Originalimports; alle Freigaben bleiben offen |

Im normalen B5/B6-Scope 7 HTML-, 2 PDF-, 2 Transcript-, 14 Medienvarianten,
1 Präsentations- und 2 manuelle Code-/ZIP-Referenzen. Zusätzliche Wochen-ZIPs sind
separat inventarisiert und keine Week-0-Verarbeitung. Die 24 Pythonlinks werden
nur durch das bestehende Codeindex-Opt-in zum eigenen Materialscope erweitert.
`locally_present=3` meint zwei echte HTMLraws plus Indoor-Discoveryfixture;
`supported=11` ist Parser-/Adapterfähigkeit, kein Verarbeitungserfolg.

Alle sechs Exportdateien erneut ausschließlich gelesen und hashverglichen;
alle zehn ZIPs nur begrenzt zum Rawhashvergleich gelesen. Zwei historische
Qualitätsberichte `passed` bleiben historische Belege. **0 neu vollständig
verifizierte reale Produktionsartefaktketten**, 0 neue echte Imports, 0 produktive
Jobs. Ursprüngliche Pläne, Download-/Importreceipts und Job-/Stagejournale sowie
heutige Grants liegen dafür nicht vollständig vor. Keine neuen Erfolge aus
Ressourcenlinks, Originaldateien oder bloßer Modelllesbarkeit abgeleitet.

## Reparierte C18-Aufgabenbindung

Der bisherige Negativtest aus #154 bleibt gültig für den Legacydefault. Der neue
explizite `assignment_discovery: true`-Pfad bindet dieselbe PSet-Übersicht über
Rawhash, URL und stabilen Provenienzlabel in Batch-/Definition-v2. Details und
Operatorrezept: [assignment_snapshots.md](assignment_snapshots.md).

Die echte Exportprüfung vergleicht alle fünf historischen IDs und die vollständige
bisherige Provenienz einschließlich deren Reihenfolge. Frische Workervorbereitung
und C16-Katalogindexierung rekonstruieren identische Bindungen. Ein synthetischer
Test versiegelt fünf getrennte Ein-Quellen-Bundles und führt einen Fall über den
vorhandenen lokalen C16/C18-Worker vollständig aus. Keine erfundenen echten
Aufgabeninhalte und keine Downloads. Fehlende Grants, geänderte Snapshots,
Kataloglücken, unpassende Cachepläne und als Aufgaben getarnte Code-URLs sperren.

Alte Bundles/Bytes/IDs bleiben erhalten. Producer und Worker müssen den neuen
Opt-in gemeinsam unterstützen; deshalb ist das vor regulärer Codeintegration
keine Aussage über den laufenden Hetzner-Worker. Eine B5-Discoveryliste allein
wird weiterhin nicht zu einem genehmigten Workflow.

## ZIP-Format- und Freigabematrix

Alle zehn Zuordnungen besitzen jetzt **bereits vorhandene Quellreferenzen** mit
Resource-/Material-IDs und DOM-Belegen aus den lokalen Kurssnapshots. Die URLs
wurden nicht aus Dateinamen erfunden. Die lokale Wochenbeschriftung `week_N_src`
und Archivwurzel `srcN` sind konsistent. Die Rawbytes↔Quell-URL-/Jahresbindung der
manuellen Beschaffung bleibt vom Betreiber zu bestätigen. Ein Snapshotlink ist
kein HTTP-Beschaffungsreceipt und keine SourceApproval.

| Archiv | Metadaten aus #154 | Bestehender Importerscope | Noch erforderliche Freigabe |
| --- | --- | --- | --- |
| week_0_src.zip | 24 Pythondateien, unauffällig | Unterstützt, höchstens sieben explizit gewählte Pythonmitglieder je Import | Archiv + jedes gewählte Mitglied: konkrete Grants/Hashes/Provenienz; Speicher |
| week_1_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben plus separat reviewte Scopeerweiterung |
| week_2_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben plus Scopeerweiterung |
| week_3_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben; kleineres Archiv ersetzt keine Week-0-Zuordnung |
| week_4_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben plus Scopeerweiterung |
| week_5_src.zip | Python, fünf CRC-/Größenduplikatkandidaten | Noch nicht unterstützt | Zusätzlich Inhaltsduplikate prüfen, IDs/Pfade getrennt halten |
| week_6_src.zip | 21 Python, 1 TXT, 3 CSV, **2 GIF** | Noch nicht unterstützt; Inventur verlangt Typreview | Zusätzlich explizites GIF-/Nicht-Code-Review, keine Bildpipeline |
| week_7_src.zip | Python, unauffällig | Noch nicht unterstützt | Grants/Hashes/Speicher/Scopeerweiterung |
| week_8_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben |
| week_9_src.zip | Python, unauffällig | Noch nicht unterstützt | Wie oben |

**Aktuell keines der zehn Archive zum Import freigegeben.** Der bestehende #144-
Importer übernimmt ausschließlich explizit ausgewählte `.py`-Mitglieder mit
passender Identität/Hash und Grant. Andere Typen werden im bestehenden Receipt
`excluded_type`, niemals automatisch als importierte Dateien behandelt.
Die reine Inventur kennt `.py/.txt/.md/.csv/.json/.yaml/.yml/.toml`; GIF bleibt
außerhalb ihrer Allowlist. Die Woche-6-Dateinamen stehen im Matrix-JSON; ihr
GIF-Inhalt wurde nicht dekomprimiert oder als Bild verifiziert. Keine notwendige
Änderung für den begrenzten Week-0-Piloten; deshalb keine Typ-/Scopeerweiterung.

Unveränderte ZIP-Grenzen: 1 MiB Raw, 64 Einträge, 1 MiB je Mitglied, 8 MiB
Gesamtexpansion, Ratio 100, keine ZIP64-/Traversal-/Symlink-/Kollisions-/
Verschlüsselungs-/Nested-Archive-Freigabe. Keine enthaltene Datei ausgeführt,
keine Grenzerhöhung, kein zusätzlicher Download.

## Vollständige Liste erforderlicher Betreiberfreigaben

1. Je tatsächlich ausgewähltem Material exakte Source-/Material-ID, Kurswoche,
   ursprüngliche URL, Rawhash, Prozessschritt und konkrete Belege für Nutzung,
   Lizenzprüfung, Robotsprüfung, Aufbewahrung und Widerruf bestätigen. Keine
   pauschale Freigabe aus dem Auftrag ableiten. Downloadrechte nur bei künftig
   separat genehmigter Beschaffung; der aktuelle Auftrag beschafft nichts.
2. Für ZIP: Archivgrant **und** separater Grant pro ausgewählter Pythondatei,
   explizite Mitgliedszuordnung zu bestehenden Codeindex-IDs sowie tatsächlicher
   Mitgliedshash. Höchstens sieben Mitglieder / acht Materialien inklusive ZIP.
   `source_approval_matrix.v1.json` enthält Anforderungen, keine aktivierten Grants.
3. Manuelle Beschaffung mit passender URL/Jahres-/Rawhashbindung bestätigen.
   Gleiche Namen und CRC-/Größenpaare sind kein Inhalts-/Rechtebeweis. Eine
   begrenzte Inhalts-/Mitgliedshashprüfung muss der Betreiber ermöglichen, bevor
   ein tatsächlicher Import mit vollständigen Grants beginnen darf.
4. Die eingecheckte Grant-Beispieldatei hat `sources: []`; bestätigte aktuelle
   Runtimegrants wurden nicht bereitgestellt. SourceApproval-v1 bindet die
   einzelnen Quellen/Schritte und Belegreferenzen. Die B6-Planung verlangt darüber
   hinaus aktuelle Gültigkeits-/Widerrufs-/Scope-/Conditions-Policies. Kein
   eigenmächtiges `process=true`, `download=true` oder erfundene Reviewreferenzen.
5. Hostroot/Queue/Worker, Kapazität, gegebenenfalls neue unveränderliche Katalog-
   und Ergebnisziele und ein enges Pilotfenster separat genehmigen. Bestehende
   Pilotroots/Artefakte dürfen nicht umgehängt, ergänzt oder überschrieben werden.
6. Fachliche Abnahmekriterien und bewusst ausgeschlossene Medienvarianten oder
   einen ausdrücklich begrenzten Teilscope entscheiden. Ein Teilpilot wird nicht
   als vollständiger Week-0-Abschluss bezeichnet.

## Rein lesender Speicher-Preflight

Der neue CLI verwendet die bestehenden CapacityLimits, `free_space` und bei
Workflowplanung den bestehenden `estimate`-Vertrag. Er scannt keine fremden
Bäume, legt keine Verzeichnisse an und verändert keinen Datenbestand.

```sh
"$TEST_PYTHON" -B -m scripts.c26_storage_preflight \
  --target-parent "$CONFIRMED_EXISTING_TARGET_PARENT" --purpose zip-import
"$TEST_PYTHON" -B -m scripts.c26_storage_preflight \
  --target-parent "$CONFIRMED_EXISTING_TARGET_PARENT" --purpose week-pilot \
  --batch "$EXPLICIT_HASH_VERIFIED_BATCH_REPORT"
```

Exit 3: blockiert. Exit 4: weitere Betreiberprüfung erforderlich, **kein Permit**.
Der Pfad muss bereits existieren und zum tatsächlichen Zielfilesystem gehören.
Inodeanzeige 0/0/0 bleibt unknown. Ein alter Freispeicherwert ersetzt keine frische
Prüfung vor jedem späteren Schreibschritt und keine bestätigte Mountzuordnung.

Gemessen weniger als vier Milliarden freie Bytes. ZIPplanung benötigt unverändert
5368709120 Bytes Reserve plus 83886080 Bytes konservatives Ausgabebudget,
zusammen **5452595200 Bytes**. Das Beispiel eines einzelnen C18-Child-Batches
benötigt nach bestehendem Estimate **7539766700 Bytes**, einschließlich des
vorhandenen 2-GiB-Jobbudgets. Beide blockiert. Das ist keine neue Dateigrenze;
aktuelle Werte und Budgets stehen im JSON. Keine automatische Bereinigung.

Weitere bestehende Grenzen: B5 höchstens acht Materialien / 8 MiB Raw pro Gruppe,
1 MiB je Material, ein paralleler und ein wartender Job, 768 MiB Jobmemory,
60 CPU-/90 Wallsekunden; PDF-v2 maximal 20 Seiten, 1 MiB und 10 Sekunden im
C16-Adapter, 512 MiB Parsermemory. Kein Anheben zur Behebung fehlender Rawdaten.

## Konkrete geplante Ausführung und Wiederverwendung

Noch **keinen** dieser Schritte produktiv ausgeführt. Geplante Gruppen:

1. Zwei HTMLquellen einzeln: frische Grants/Rawhash prüfen → neuen C18-Input
   versiegeln → vorhandener HTML-v2-Parser → #149-Quality-/Handoff-v2. Alte
   normalisierte Daten nur nach kompletter Receipt-/Plan-/Grant-/Versionsprüfung
   wiederverwenden; vorhandene Exportdateien bleiben unangetastet.
2. Fünf Aufgaben jeweils als Ein-Quellen-v2-Bundle: erst fehlende Originale und
   Grants, dann dieselbe gebundene Übersicht in Planung und Worker. Parent-/
   URL-/DOM-/Hashgleichheit vor jeder Submission, Kapazitäts-/Queuecheck davor.
3. Zwei PDFs getrennt: tatsächliche Größen und Seiten prüfen, vorhandener PDF-v2-
   Weg, Code-/Seitenerhalt und technische Qualität. Keine behaupteten Original-
   PDF-Erfolge aus synthetischen Tests; vorhandene Originaltests bleiben offen.
4. SRT und TXT im bestehenden kleinen Transcriptimport: Source-/Lecture-/Sprach-/
   Zeitstempelbindung, Importreceipt und Qualität prüfen. Keine automatische
   Transkription, Whisper-, LLM-, Embedding- oder Wissensextraktionsaktivierung.
5. Genau **ein** Week-0-ZIP, sobald alle obigen Bedingungen erfüllt sind, mit
   expliziter kleiner Mitgliederwahl im vorhandenen `code import` in einem neuen
   privaten temporären Ziel. Original unverändert, nur Python übernehmen, Raw-/
   Outputhashes und Provenienz, danach identischer Repeat/Receiptvergleich.
   Übrige neun Archive ausschließlich Inventur. Kein bestandener Preview zählt
   als Importtest. Medien/Shorts/Slidesreferenzen bleiben separat offen.

0 neue verifizierte reale Ergebnisreuses. Ein vollständiger Plan ist keine
vollständige Discovery des gesamten Kurses, keine erfolgreiche technische
Verarbeitung und kein fachlicher Abschluss. Aktuell alle drei Completionachsen
false; B6-preflight blocked, keine neuen Submissions.

## Gesamtfolge und Abschlussprüfung

1. **Codeintegration:** C18-v2 und #149 fachlich reviewen; #148/UI #20 samt offenen
   Laufzeit-/Betriebsbelegen bewerten. Vor jedem Merge Auto-Deploy separat klären.
2. **Betriebsprüfung:** read-only Hostinventur und Betreiberfreigaben nach dem
   separaten [HTTPS-/VPN-Gate](https_vpn_release_gate.md), keine Hostannahmen.
3. **HTTPS/VPN:** separat genehmigter Rollout mit realen Negativtests, Health,
   exakter Version, Rollback und anschließend eigener Resume-Freigabe.
4. **Week 0:** erst nach Quell-/Speicher-/Workerfreigabe die obigen kleinen Gruppen
   ausführen lassen. Bei unbekannten Jobs, Hash-, Qualitäts- oder Budgetfehlern
   geschlossen bleiben; keinen Teilerfolg stillschweigend als Abschluss zählen.
5. **Abschluss:** vollständige Raw→Receipt→Plan→Worker→Normalized→Quality→Handoff-
   Ketten sowie alle Source-/Material-/Parent-IDs und Logs prüfen, fachliche
   Vollständigkeit separat abnehmen und fehlende/exkludierte Quellen berichten.

Rollout-/Rollbackbedingungen stehen im Release-Gate. Für Materialfehler zuerst
keine neuen Annahmen, Originale und unabhängige Pilotdaten erhalten. Kein
ungeprüftes Replay oder Adopting von Ausgaben; nur im vorhandenen geprüften
Resume-/Receiptvertrag nach separater Entscheidung fortsetzen. Ergebnisroots
und historische Artefakte nicht löschen oder überschreiben.

## Aktuelle Validierung und Integrationsgrenze

Final jeweils **20 bestanden** auf eigenem Stand und zusammen mit #148/#149:
15 Assignmentfälle einschließlich aller echten Childbindungen, synthetischem
Sealing/Worker, Legacyserialisierung, Hash-/Katalog-/Cache-/Manualpolicyfehlern,
Quellroot-Schutz und fünf rein lesenden Speicherfällen. Der breitere gemeinsame
Lauf hat **433 Erfolge und drei `tiktoken`-Importfehler** in älteren Knowledge-
Batchtests. Kein historischer Erfolg ersetzt diese offene Testumgebungslücke.
Die Läufe überlappen; genaue JUnit-/Patch-/Quellhashes in `validation.v1.json`.

Die bekannte Quarantänediagnose und die verbleibenden HTTPS-/Hostfreigaben stehen
im separaten Release-Gate. Für Original-PDF-/Transcript-/Medienabnahme bleiben die
fehlenden Rawdaten offen; hier keine produktiven Erfolge daraus abgeleitet.
Eigener Reviewbranch und Worktrees bleiben wegen des ausstehenden regulären
Reviews erhalten. Keine automatische Integration, kein Auto-Merge oder Rollout.
