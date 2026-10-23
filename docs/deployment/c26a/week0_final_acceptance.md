# CS50P Week 0 – Offline-Abnahme und Pilotbereitschaft

23.10.2026. Backend-master wurde vor Arbeitsbeginn live geprüft:
`d180a8f6e65f900a4d0d169475d78a4cb42b0d8c`. #142, #144, #150 und #152 sind
integriert; #149 bleibt Draft auf
`58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb`. Die kompatible gemeinsame Prüfung mit
#149 liegt separat im Integrationsauftrag. Dieser Branch ändert keine HTML-,
C18-, Deployment-, UI- oder Produktionskonfiguration.

**Ergebnis: kein vollständiger produktiver Week-0-Pilot und keine Serienfreigabe.**
Vorhandene Exporte und alle zehn manuellen ZIPs wurden lesend geprüft. Der echte
ZIP-Import und die C18-Aufgabenverarbeitung bleiben konkret blockiert.

## Tatsächlicher Bestand und Verarbeitbarkeit

[B5/B6-Plan und Belege](week0_final_plan.v1.json),
[ZIP-Inventur](manual_zip_inventory.v1.json),
[separater Einzelimportbericht](manual_zip_import_acceptance.md).

| Material | Nachgewiesener lokaler Stand | Technischer Weg / offener Bedarf |
| --- | --- | --- |
| Notes | Original 71718 Bytes, 237 normalisierte Blöcke, **34 Codeblöcke**, 25 Links; historischer Qualitätsbericht `passed`, 171 Handoff-v1-Units | HTML-v2 + bestehender C18-/Quality-/Handoffweg; neuer vollständiger Produktionskettenbeleg und aktuelle Grants fehlen |
| PSet-0-Übersicht | Original 15832 Bytes, 28 Blöcke, 10 Links einschließlich **aller fünf Aufgaben**; historisch `passed`, 16 Handoff-v1-Units | HTML-v2; gleiche Grenzen wie Notes, keine Inhalte aus Links ableiten |
| Fünf Aufgaben | URLs, Parent-ID, deterministische Child-IDs und DOM-Provenienz aus echtem PSet-Export belegt; eingechecktes Indoor-Voice-HTML als Discoveryfixture | Vier weitere Aufgabenoriginale fehlen; Fixture ist kein genehmigter aktueller Import. C18-Worker kann diese Child-IDs noch nicht rekonstruieren |
| Slides-PDF / Code-PDF | Zwei konkrete vorhandene Quellreferenzen; keine separat bereitgestellten Original-PDF-Artefakte in diesem Auftrag | PDF-v2 synthetisch geprüft; Originalvergleich bleibt offen |
| SRT / TXT | Zwei getrennte Quellenreferenzen, keine freigegebenen Originaldateien bereitgestellt | Bestehender Importer und Lecture-/Source-/Zeitstempelbindung synthetisch geprüft |
| Lecture-Audio | MP3-Referenz, kein genehmigtes Raw | Media-Plan-only; keine Transkription gestartet |
| Lecture-Video | Acht HTML-/Player-/MP4-/YouTube-Bindungen derselben Vorlesung, kein genehmigtes Raw | Plan-only; Auflösungen/Referenzen sind keine acht verarbeiteten Vorlesungen |
| Shorts | Fünf Referenzen, keine genehmigten Medienraws | Offen; keine Downloads oder neue Prozessoren |
| Google Slides | Eine Referenz | Referenz-only, kein impliziter Export/PDF-Ersatz |
| Codeindex | Vorhandener lokaler Snapshot mit 24 direkten Week-0-Pythonreferenzen | Reine Discovery; kein Codeindexdownload. Opt-in-Referenzprüfung bestätigt Namen/IDs für alle 24 ZIP-Mitglieder, keine Inhaltsprüfung |
| Manuelle ZIPs | **Zehn Rawarchive vorhanden und hashverifiziert**, Wochenbeschriftung 0–9 jeweils mit `srcN` konsistent | Neun Metadatenprüfungen bestanden, Woche 6 wegen GIF-Typreview gesperrt; alle Imports mangels Grants/Reserve offen |

Im dokumentierten B5/B6-Week-0-Scope weiterhin **21 logische Ressourcen / 28
Varianten**, davon 7 HTML, 2 PDF, 2 Transcript, 14 Medien, 1 Präsentationsreferenz,
2 manuelle Code-/ZIP-Referenzen. Die zusätzlichen neun ZIPs anderer Wochen sind
in der getrennten Archivliste, nicht als Week-0-Verarbeitung gezählt. Die 24
Pythonreferenzen werden nur im ausdrücklich gewählten Codeindex-Opt-in geprüft;
sie erhöhen den normalen B5/B6-Scope nicht stillschweigend.

Der B6-Plan meldet 3 lokal belegte Einträge: zwei echte Exportoriginale plus die
versionierte Indoor-Discoveryfixture. Das sind **keine drei neuen Importerfolge**.
Elf Bindungen haben prinzipiell einen Dokument-/Transcriptadapter; darunter sind
auch die fünf aktuell workerblockierten Aufgaben. `supported` bedeutet daher
keinen erfolgreichen oder genehmigten Verarbeitungspfad für den gesamten Scope.

Alle sechs Exportdateien wurden hashverifiziert, die historischen Qualitäts- und
Handoffmodelle gelesen. Die sechs Hashes stehen im Plan. Zwei historische
Qualitätsberichte `passed` sind vorhanden; **0 neue vollständige reale
Produktionsartefaktketten** wurden verifiziert: ursprünglicher Plan,
Downloadreceipts, Job-/Stagejournale und heutige SourceApprovals fehlen. Das
widerspricht nicht den historisch berichteten Pilotverarbeitungen. Keine dieser
Dateien und keine alten Pilotdaten wurden verändert.

## Präziser C18-Blocker

`WeekRequest.discovery_exports` trägt den hashgebundenen PSet-Snapshot zum
B5/B6-Planer; `week._inventory` leitet daraus bereits die fünf stabilen IDs ab.
Der bestehende C18-Einstieg `workflows.definition.prepare` und die
C16-Katalogindexierung rekonstruieren dagegen `processing.make_plan` über
`discover_fixture_courses`, das nur Index- und Wochenübersichten in den
Discoverygraphen aufnimmt. Eine `assignment`-Datei im bestehenden Manifest allein
ändert diesen Graphen nicht.

Der neue Test `test_real_children_rejected_even_with_hash_bound_overview_in_bundle`
übernimmt die tatsächliche PSet-Originaldatei samt Hash in ein isoliertes Bundle,
verifiziert Parent und fünf historische Child-IDs und ruft für jedes Child die
bestehende C18-Vorbereitung auf. Alle fünf enden mit
`No resources match explicit scope`, bevor Import oder Parsing stattfinden.
Leere ausdrücklich nicht verfügbare Platzhalter dienen nur dem negativen
Auswahltest; es werden keine Aufgabeninhalte erfunden oder Jobs gestartet.

**C18-Aufgabenbindung funktioniert damit noch nicht.** Kein ungültiges Bundle
wurde als einsatzbereit ausgegeben. Benötigt wird ein gemeinsam reviewtes,
explizit versioniertes Snapshot-/Adapter-Opt-in für Katalogindexierung,
Batch-Revalidierung/Sealing und Workerrekonstruktion. Dabei müssen exakt derselbe
hashgebundene Übersichtssnapshot, Parent/Child-Identitäten, Original-URLs und
DOM-Provenienz verwendet werden; bisherige Bundles und alte Pilotartefakte bleiben
unverändert. Ein bloßes Durchreichen eines extern vorberechneten Plans würde die
bestehende Worker-Revalidierung umgehen und wurde nicht eingebaut.

## Technischer Batchplan und Kapazität

`week0_final_plan.v1.json` enthält den tatsächlichen B6-CourseRequest, den
B6-CourseReport und die vollständigen B5-Ressourcen mit URLs, IDs, Parsern,
Schritten, Hashes, lokalen Alias-Pfaden, fehlenden Grants und Blockern.
Pfadaliase `${REPO}` und `${QUALITY_EXPORT}` schützen lokale Pfade; der Datensatz
ist ein Abnahmebericht, kein unverändert ausführbares DTO. Die darin enthaltene
`course_request` wird nach expliziter Ersetzung dieser beiden Aliase zum vorhandenen
CLI-Input. Keine SourceApprovals erzeugt, keine Freigabeflags gesetzt.

Serielle Dokument-/Transcriptgruppen mit jeweils höchstens acht Materialien:

1. Notes + PSet-Übersicht (2): Raw-/Grantprüfung → bestehender lokaler Import →
   HTML-v2 → Quality Gate → Lecture-Handoff, gegebenenfalls bestätigte Artefakte
   wiederverwenden. Kein neuer Verarbeitungsauftrag wurde hier ausgelöst.
2. Fünf Child-Aufgaben (5): erst C18-Adaptervertrag und freigegebene Originale;
   Parent-/Snapshotbindung vor Import und Qualität prüfen.
3. Slides + Code-PDF (2): getrennte Material- und Lecture-IDs → vorhandener
   PDF-v2-Adapter → Seiten-/Code-/Provenienzqualität → Handoff.
4. SRT + TXT (2): getrennte Source-/Rohhash-/Lecturebindungen → bestehender
   Transcriptimport → Zeitstempel-/Texterhalt und Importreceipt; keine Whisper-
   oder LLM-Aktivierung.
5. Woche-0-ZIP: separater manueller Importweg, nach eigenen Grants/Hashbindung
   genau ein Archiv und höchstens sieben ausgewählte Pythonmitglieder. Andere
   neun Archive bleiben Inventur-only. Medien/Google Slides separat offen.

Der vollständige 28-Varianten-Scope ist eine Inventur, kein zulässiger einzelner
8er-Ausführungsbatch; entsprechende globale Kapazitätsblocker werden nicht
verschwiegen. Der Plan enthält die vier kleineren Gruppen mit ihren tatsächlichen
B5-Blockern. Aktuell **0 freigegebene Submissions, 0 verarbeitete/reused Ergebnisse**.

Unveränderte Grenzen: 1 MiB Raw je Material, 8 MiB je B5-Gruppe, mindestens 5 GiB
Reserve, 768 MiB Jobbudget, 512 MiB Parser, ein paralleler/ein wartender Job,
60 CPU-/90 Wallsekunden, PDF höchstens 20 Seiten. C16-PDFparser weiterhin
1 MiB / 20 Seiten / 10 Sekunden. Keine Grenzen erhöht. Transcript-Raw höchstens
1 MiB, expliziter kleiner Scope. Tatsächliche Hostmemory und Queue-/Workerzustände
sind unbekannt; lokale freie Bytes sind eine Planbeobachtung, keine Hostzusage.
Lokal zu Beginn 4,0 GB, nach Prüfungen rund 3,9 GB frei; Inodeanzeige liefert
0/0/0 und ist nicht auswertbar. Keine Caches/Venvs/Daten bereinigt.

Reproduktion ausschließlich mit dem vorhandenen Plan-CLI, eigenem Ziel und
explizit aufgelösten lokalen Alias-Pfaden:

```sh
PYTHONDONTWRITEBYTECODE=1 "$TEST_PYTHON" -B -m scripts.cs50_course plan \
  --request "$OWN_RESOLVED_REQUEST" > "$OWN_PLAN_REPORT"
PYTHONDONTWRITEBYTECODE=1 "$TEST_PYTHON" -B -m scripts.cs50_course preflight \
  --request "$OWN_RESOLVED_REQUEST" > "$OWN_PREFLIGHT_REPORT"
```

Preflight bleibt aktuell `blocked`; `plan`-Exit 0 bedeutet nur erfolgreiche
Planerzeugung. Discovery-, technische und fachliche Completion sind jeweils false.
Neue Quelle/Approval/Parser-/Handoffversion verlangt neue Prüfung; keine pauschale
Serienfreigabe. Bereits gültige aktuelle Artefakte nur über den bestehenden
hash-/grant-/revisionsgebundenen Evidence-Verifier wiederverwenden.

## Aktuelle Tests und Grenzen

| Lauf | Tatsächliches Ergebnis |
| --- | --- |
| Material-/ZIP-/B5-/B6-/Transcript-/PDF-v2-Regressionen | **242 bestanden, 2 übersprungen**, 261,84 s |
| Finaler Sicherheitsstand: neue Inventur + bestehender ZIP-Importer + echter C18-Negativfall | **72 bestanden, 0 übersprungen**, 71,80 s |
| Separate gemeinsame Prüfung Master + unveränderte #148/#149-Diffs | 304 bestanden, 2 fehlgeschlagen; Einzelwiederholungen bestanden, siehe getrennten Integrationsbericht |

Die beiden Skips verlangen explizite Original-PDF-Artefakte für Slides und
Code-PDF; diese wurden nicht bereitgestellt. Kein Original-PDF-Erfolg behauptet.
Die absichtlich doppelte synthetische ZIP-Datei erzeugt eine erwartete
`zipfile`-Warnung, keinen fehlerhaften Test. Die Läufe überlappen; Zahlen nicht
zu einer vermeintlich unabhängigen Gesamtsuite addieren. Im finalen 72er-Lauf sind
17 neue Inventurfälle, 54 vorhandene ZIP-Fälle und ein neuer echter
C18-Blockernachweis enthalten. Neue Tests benötigen kein Netzwerk.

| Angeforderter Nachweis | Prüfweg |
| --- | --- |
| Fünf Links / stabile Child-IDs / C18-Rekonstruktion | Vorhandene echte B5/B6-Exportfälle + neuer echter C18-Negativfall; Rekonstruktion ausdrücklich blockiert |
| HTML-Code unverändert | Beide echten #149-Exportfälle im getrennten Integrationslauf, 34 Notes-Codeblöcke und fünf PSet-Links erhalten |
| B5/B6, fehlende Medien, Hash-/Grantblocker | Bestehende Week-/Course-Suiten, keine Erwerbs-/Jobaufrufe |
| ZIP ohne Codeausführung / Provenienz / Idempotenz | Vorhandene tatsächliche `code_import`-Roundtrips mit synthetischen Quellen |
| Traversal / Bomben / Duplikate / korrupte Archive | Vorhandene ZIP-Suite plus neue Metadatenfälle, manipulierte Zähler vor Objektanlage abgewiesen |
| PDF / Transcript / Lecturebindung | PDF-v2- und Multiformat-/Week-/Course-Fälle; nur synthetische Rawdaten |
| Historische Pilotdaten unverändert | Hash-/Bytevergleich aller sechs explizit gelieferten Originale vor/nach Prüfung; keine Schreibpfade in alte Daten |

Quell-/JUnit-/Ergebnishashes: `week0_final_validation.v1.json`. Nicht ausgeführte
Originalimports oder produktive Ketten bleiben ausstehend. Ein anfänglicher
unbegrenzter Auswahlversuch `batch.plan` über sämtliche CS50P-Ressourcen wurde von
der vorhandenen 32er-Batchgrenze zurückgewiesen; die Abnahme verwendet danach den
expliziten Week-0-Scope und unveränderte Grenzen. Die erste Ausführung des lokalen
Reporthelpers benötigte einen expliziten Repo-Importpfad; der korrigierte Lauf
hat den Plan ohne Downloads/Worker erzeugt.

## Nächste Betreiberentscheidungen und Review

Vor einem kontrollierten produktiven Week-0-Lauf fehlen aktuelle Einzelgrants und
Quellbelege, C18-Child-Integration, vier Aufgabenoriginale, freigegebene PDF-/
Transcript-/Medienraws oder bewusst genehmigte Teilscopes, ausreichende Kapazität,
aktueller Worker-/Queue-/Mountnachweis und unabhängige Quality-/fachliche Abnahme.
Die ZIPs benötigen zusätzlich die im separaten Importbericht genannten Grants,
Mitgliedshashes und Reserve. Kein vollständiger Pilot allein durch den vorhandenen
Plan oder bestandene synthetische Tests.

Eigener Branch `feat/c26-week0-acceptance`, Worktree
`Personal_Assistant-c26-week0-acceptance`, separate Ergebnisse in
`Personal_Assistant-c26-week0-results`. Keine Änderungen an fremden Worktrees,
Produktivcontainern oder Volumes; keine Archive/Extrakte in Git. Der eigene
Review-PR wird ohne Auto-Merge erstellt. Wegen des nicht autorisierten Merges
bleiben Branch, Worktree und Belege erhalten. Dokumente sind bis zum regulären
Review/Merge noch nicht im Default-Branch integriert. Auch ein späterer Merge
benötigt zuvor die im parallelen Integrationsaudit offene Auto-Deploy-Prüfung.
