# C26-B5: vollständige belegte Wocheninventur und kontrollierte Verarbeitung

22.10.2026. Basis `master` / `e581e201ef6b3d6c06aca14de845e0687d213b37`.
B5 ist ein Offline-Discovery-/Planungsadapter. Er startet keine Downloads,
Parserjobs, Worker, Container, Provider oder neue Queue. Er erzeugt geprüfte
Eingaben für vorhandene Prozessoren und weist fehlende Integrationen aus.

## Git- und Kompatibilitätsstand

Vor Implementierung: Primärcheckout `gmp_compliance` sauber auf seinem vorhandenen
Branch; Live-Master `e581e20`. Die offenen Draft-PRs #148 (Worker-Deployment-Gate,
`f98eedd`) und #149 (HTML-Aggregation/Quality v2, `58aec7d`) wurden geprüft.
B5 basiert auf Master, verändert keine Datei dieser PRs und dupliziert deren
Aggregation nicht. Kompatibilität mit #149 wird in einer eigenen isolierten Kopie
getestet. Historische B5-/B6-/B7-Komponenten sind bereits integriert; dieser Auftrag
ergänzt deren Wochenplanung und ersetzt sie nicht.

## Tatsächlich belegtes Week-0-Inventar

Der Betreiber hat zusätzlich zwei **lokal erreichbare** Exportoriginale benannt.
Sie wurden ausschließlich gelesen. Ihre Hashes stimmen mit den exportierten
NormalizedDocument-Raw-Hashes überein:

| Quelle | Raw-Bytes | SHA-256 | Exportblöcke / Code |
|---|---:|---|---:|
| Notes 0 | 71.718 | `0e9af3114adec16938b89b511337f5db717ef2e14f1a606af600d6995ce09377` | 237 / 34 |
| Problem Set 0 | 15.832 | `0d06fb2afcfcc01f5e4e7abbc2a09e057e17fda8c11fa60e948f1f9836cb2372` | 28 / 0 |

Diese bestehenden Dateien wurden nicht heruntergeladen, erneut verarbeitet oder
ins Repository kopiert. Das versionierte [Inventar](week0_resources.v1.json)
enthält stattdessen URLs, Quellhashes, vorhandene Resource-/Material-IDs,
DOM-Provenienz und Bearbeitungszustände.

Mit dem vorhandenen Manifest und beiden expliziten Exporten:

| Kennzahl | Beobachtung |
|---|---:|
| Logische Resource-IDs | **21** |
| Material-/Medienvarianten | **28** |
| HTML-/PDF-/SRT-/TXT-Prozessor grundsätzlich vorhanden | **11** |
| Davon bereits an bestehenden C18-/Transcript-Graphen gebunden | **6** |
| Davon Aufgaben mit noch fehlender C18-Discoveryintegration | **5** |
| Lokale inhaltsbezogene Quellsnapshots im angegebenen Scope | **3** |
| Automatisch ausgeschlossener Codeindex / ZIP | **2** |
| Im neuen Bericht unabhängig verifizierte abgeschlossene Artefaktketten | **0** |

Die drei lokalen Quellsnapshots sind Notes 0 und Problem Set 0 aus dem Export
sowie der historische eingecheckte Indoor-Voice-Snapshot. Der lokale Week-Snapshot
belegt Medienlinks, gilt aber nicht als heruntergeladenes Video. Audio und dessen
gleichnamige MP3-Variante werden über `variant_aliases` zusammengeführt; unterschiedliche
Videoauflösungen/Varianten bleiben getrennt. Resource-IDs bestehender Ressourcen
bleiben unverändert. Aus dem reinen eingecheckten Manifest, ohne Exporte, ergeben
sich 17 logische Ressourcen und 24 Varianten; vier Aufgaben bleiben dort unbelegt.

Belegte Kategorien:

- Hauptlecture und sieben Player-/Videoangebote; Audio MP3;
- Lecture Notes, Problem-Set-Übersicht und fünf eigenständige Aufgaben;
- Lecture Slides PDF und Code-PDF als PDF, getrennt von ausführbarem Code;
- Google Slides als Referenz mit gesonderter Exportprüfung;
- englisches SRT und TXT mit bestehender Lecture-Bindung;
- fünf eigenständige Shorts: Visual Studio Code for CS50, Functions, Variables,
  Return Values und Side Effects;
- Codeindex und ZIP ausschließlich als manuell zu beschaffende Referenzen.

Der vorhandene Codeindex-Snapshot wird nicht nach weiteren Python-Dateien durchsucht.
Nicht beobachtete Python-Dateien erhalten keine erfundenen Ressourcen-IDs.

## Fünf Aufgaben und Provenienz

Alle fünf Links stammen aus dem echten Problem-Set-0-Export; ihre Resource-IDs
werden mit `ResourceCandidate.resource_id` deterministisch aus Kurs, Rolle, URL,
Sprache und Parent-ID berechnet. Der Parent ist die vorhandene Problem-Set-ID
`resource:1200b44f5efad4c2796fe526c66701859159dc235f6c7d947edf25a9935bdf05`.

| Aufgabe | Belegte URL | Resource-ID |
|---|---|---|
| Indoor Voice | `https://cs50.harvard.edu/python/psets/0/indoor/` | `resource:4ee69e33f96d9fc48e28dabd6c4a5e85498b500d3ac6234004cc004dda63f5e6` |
| Playback Speed | `https://cs50.harvard.edu/python/psets/0/playback/` | `resource:250a4c6a09635fec5bc78ba47fc4b532e6c83bf814ff61ab63a9da9ea39e4dfb` |
| Making Faces | `https://cs50.harvard.edu/python/psets/0/faces/` | `resource:31f50347c0e791010e7aceea629e268a9a14d0e584989ba7a2ba89bda5cc5f12` |
| Einstein | `https://cs50.harvard.edu/python/psets/0/einstein/` | `resource:a72ee41697270bf06d0503f78b0c6e6b6b675c4c8bc7a3fa33967e4ae9332869` |
| Tip Calculator | `https://cs50.harvard.edu/python/psets/0/tip/` | `resource:1000d0fb21f0b535d7e876d723bf1763d03e41ddddf9a391ee77320907899069` |

Die drei zusätzlichen Belegarten werden auseinandergehalten: Link im Week-Snapshot,
Link in einem ausdrücklich gelieferten Export, vorhandener eigener Inhalts-Snapshot.
Wiederholte Links/Fragmente werden nur innerhalb derselben bestehenden Identität
zusammengeführt; Provenienz bleibt erhalten. Unterschiedliche Rollen, Sprachen,
Parents oder Medienvarianten werden nicht nach Textgleichheit verschmolzen.
Die vollständigen Inhalte der vier zusätzlichen Aufgaben liegen nicht vor.
Auch der historische Indoor-Snapshot ist kein neuer Produktionsdownload.

## API und Betriebsmodi

Neue additive Module:

- `src/model_materials/week.py`: `WeekRequest`, `DiscoverySnapshot`, `LocalSource`,
  `WorkflowReference`, `WeekLimits`, `WeekResource`, `WeekReport`;
- `src/tools_materials/week.py`: `plan_week`, `prepare_material_batches`,
  `prepare_transcript_batches`, `resolve_workflow_reference`;
- `scripts/cs50_week.py`: lesende JSON-CLI;
- `tests/test_cs50_week_materials.py`: Offline- und Adaptertests.

Alle neuen persistierbaren Wochenverträge beginnen bei Schema 1. Bestehende
Discovery-, Material-, Receipt-, Transcript-, C16-/C18- und Aggregationsverträge
werden nicht verändert. Es gibt keine neuen Dependencies oder Jobdatenbanken.

```python
request = WeekRequest(
    manifest=Path('/explicit/snapshots/manifest.json'),
    course_id='cs50_python', week='0', mode='plan',
    material_types=('html', 'pdf', 'transcript'),
    material_ids=(explicit_material_id,),
)
report = plan_week(request, existing_source_approvals)
```

`discovery_only` liest nur die validierten Index-/Week-Snapshots, bereits deklarierte
Assignment-Snapshots und explizite hashgebundene Discovery-Exporte. Es liest keine
Materialarchive und führt keinen Parserjob aus. Zusätzliche Links werden nicht geöffnet.

`plan` zeigt Auswahl, Prozessor, Parserkonfiguration, `planned_steps`, Freigaben,
Kapazitätsbedarf und Blocker. Ohne explizite IDs gilt die ausdrücklich angegebene
Typauswahl als Scope; eine zu große Auswahl wird blockiert, nicht still gekürzt.

`process_existing` **plant** nur die Verarbeitung ausdrücklich benannter und
hashverifizierter lokaler Dateien. `prepare_material_batches` liefert dafür
bestehende einquellige `Batch`-Objekte, `prepare_transcript_batches` die bestehenden
SRT-/TXT-Batches. Beide rufen den Controller und die Prozessoren nicht selbst auf.
Zum bestehenden Materialablauf gehören nach separater Ausführungsfreigabe der
lokale Import über `MaterialDownloader.obtain(local_file=...)` mit hashgebundenem
Receipt, `batch.seal` und Controller-Preview/Submission. Der Quellpfad bleibt über
`WeekRequest.local_sources` eindeutig an die Material-ID gebunden; der Transcript-
Adapter verwendet seine vorhandene Source-ID-zu-Datei-Zuordnung. B5 führt diese
Schritte nicht aus. Die eigentliche Ausführung bleibt beim vorhandenen freigegebenen Adapter und
seiner erneuten Preflight-/Freigabeprüfung. Ein `ready_*` ist keine Ausführungsfreigabe.

`approved_acquisition` zeigt die zusätzlich erforderliche Downloadfreigabe und
die bestehende serielle Beschaffung als geplanten Schritt. Die automatische
Produktivimplementierung dieses Modus bleibt ausdrücklich gesperrt. Keine
implizite Beschaffung nach erfolgreich verarbeitetem anderem Material.

Die vorhandene `SourceApproval` bindet Resource-, Material-, Kurs- und URL-Identität
sowie Verarbeitung/Download und Operatorbelege. Ein vorhandener Dateipfad reicht
nicht: `LocalSource.expected_sha256` und Freigabehash müssen beide zu den gelesenen
Bytes passen. Discovery-Exportfreigabe ist keine Processing-/Downloadfreigabe.

## Routing und vorhandene Komponenten

| Typ | Vorhandene Komponente | B5-Behandlung |
|---|---|---|
| HTML/PDF im bisherigen Graphen | `MaterialProcessor`, `src.workflows.definition`, `src.workflows.service`, C16-Registry/Guardian | Geprüfte Eingaben für denselben einquelligen C18-Pfad |
| SRT/TXT | `src.tools_materials.transcripts.run`, `src.tools_transcribe.import_transcript` | Bestehende Offline-Adapter; kein neuer Transcript-Parser |
| Bereits abgeschlossene Ergebnisse | `media_evidence.verify`, `prepare_material_handoff`, bestehende Receipt-/Hash-/Config-Prüfungen | Nur explizit benannte Belege prüfen und unverändert wiederverwenden |
| Audio/Video/Shorts | `src.tools_materials.media_plan.plan`, bestehende Transcript-/Medienevidence | Separater Zweck-/Evidence-/Kapazitätsplan nötig; kein Fallback oder Massenlauf |
| Google Slides | bestehender Media-Plan-Exportblocker | Exportmöglichkeit und Berechtigung separat prüfen |
| Codeindex/PY/ZIP und andere Code-/Archivformate | vorhandene B6-Komponenten nur als spätere manuelle Option | Im B5-Plan stets `manual_only`; keine automatische Batch-/Jobübergabe |
| Unbekannt/extern unfreigegeben | Review | Kein HTML- oder Codeparser-Fallback |

Die Code-/Archivprüfung steht vor der Parserauswahl und prüft auch tatsächliche
URL-Suffixe und Codeindexpfade. Eine irreführende Rolle `notes`, ein HTML-Formathint
oder vorhandene Grants erlauben weder `.py`/`.zip` noch einen Codeindex im Batch.
Ein Code-PDF bleibt ein PDF. B5 aktiviert keinen vollständigen Codeimporter;
B6 kann später nach eigenständiger Betreiberfreigabe Hash/Herkunft/Import prüfen.

### Expliziter Architekturblocker: neue Aufgaben im C18-Graphen

`discover_fixture_courses` und damit `make_plan` rekonstruieren C18-Resource-IDs
bisher nur aus Course-Index und Week-Overview. Ein Aufgabenlink im separaten
Problem-Set-Export gehört noch nicht zu diesem unveränderten Graphen.
B5 erfasst ihn mit Parent und Provenienz, blockiert aber `assignment_child_c18_adapter_not_integrated`
auch bei vorhandener lokaler Datei und vollständigen Grants. Es werden keine
fremden IDs als bestehende C18-Eingaben eingeschleust.

Konkreter Folgeschritt: eine versionierte, opt-in Erweiterung der bestehenden
Discovery-/C18-Bundlebindung, die den genehmigten Problem-Set-Snapshot mit Hash
ins unveränderliche Bundle übernimmt und dessen Child-IDs innerhalb des Workers
identisch rekonstruiert. Alte Default-Graphen/IDs und v1-Bundles bleiben erhalten.
Das erfordert ein eigenes Review des bestehenden C18-Vertrags; B5 baut dafür keine
zweite Pipeline und keinen alternativen Worker. Der Standalone-HTMLparser kann
solche Texte bereits verarbeiten; blockiert ist die verifizierbare Orchestrierungsbindung.

## Status, Wiederverwendung und Vollständigkeit

Discovery, Acquisition und Processing bleiben getrennt. Referenz-only-Code ist
`manual_required`/`not_requested`, kein fehlgeschlagener Workflow. Ein lokaler,
nicht gepinnter Inhalt ist `local_present`; erst der erwartete Hash macht ihn
`verified`. Ohne Source-Grant/Hash/Adapter/Kapazität entsteht kein fertiger Batch.

Abgeschlossene Materialevidence wird über den bestehenden Quality-Handoff geprüft,
Transcripte über vorhandene Transcript-/Importer-Receipts. Geänderte Rohbytes,
Receipts, Parserkonfigurationen, Importerrevisionen oder Qualität blockieren Reuse.
Es gibt keine Überschreibung, automatische Reparatur oder Wiederholung.
Ein einzelner defekter Beleg lässt andere verifizierte Ergebnisse bestehen.
SRT übernimmt Quellzeiten und leere Cues; TXT behält unbekannte Zeiten als `null`.
TXT wird nicht still in eine zeitbasierte KnowledgeEvidence umgewandelt.

Der Bericht enthält Resource-/Material-ID, Bindung, Titel, Kurs/Woche/Lecture,
Originalquelle, Parents, Status, Prozessor, Parser, geplante Schritte, explizite
Workflowreferenzen, Qualität, Freigabelücken, Einschränkungen und Zähler.
Counts, Auswahl, Parents und Completion-Flags werden bei Modellvalidierung geprüft.

`scope_processing_complete` wird nur für einen nichtleeren ausdrücklich definierten
Scope mit tatsächlich verifizierten abgeschlossenen Ergebnissen true.
`technical_workflow_complete` bezeichnet dieselbe technische Scope-Abdeckung,
nicht den Abschluss aller denkbaren Kursmaterialien. `subject_matter_verified`
und `full_week_discovery_verified` bleiben false. Snapshotvollständigkeit ist keine
Live-Web-/Lehrinhaltsvollständigkeit.

Die zwei erfolgreichen alten Pilotjobs sind Betreiber-/Exportreferenz. B5 behauptet
keine neue Prüfung ihrer kompletten Receipt-/Plan-/Controllerkette und setzt keine
Produktionszustände zurück. Deshalb zählt das reine Discovery-Inventar null neu
verifizierte Prozessketten; das bedeutet nicht, dass diese alten Jobs fehlgeschlagen sind.

## Root- und Ressourcenvertrag

`WorkflowReference.relative_path` ist relativ zum expliziten `controller_root`.
Ein Root namens `.../jobs` kann regulär `jobs/job_<id>/results/...` enthalten:
`.../jobs/jobs/job_<id>/...`. Der Resolver fügt keinen weiteren Präfix hinzu,
prüft Jobbindung, portable Pfade, Symlinkfreiheit und Hash. Bestehende Roots,
Job-IDs und Artefaktreferenzen werden nicht verändert. Für einen künftig separat
freigegebenen neuen Root wäre der Name `.../controller` eindeutiger; das ist keine
Migrationsempfehlung für den bestehenden Pilotroot.

| Grenze | B5-Plan / unveränderter bestehender Vertrag |
|---|---|
| Ausgewählte Materialien | höchstens 8; kein stilles Weglassen |
| Raw-Bytes | höchstens 1 MiB je Datei; insgesamt höchstens 8 MiB |
| Freie Reserve | mindestens 5 GiB plus Allowances |
| Planungsallowance | Reserve + 4 × Gesamtrawbudget + 512 MiB Jobs + 16 MiB Reports |
| Worker/Queue | ein bestehender Worker; `max_parallel=1`, `max_queued=1` |
| Guardian | vorhandene 90 s Wandzeit, 60 s CPU, 768 MiB Envelope |
| Parser | vorhandene 512 MiB, 10 s; 1.000 Blöcke; PDF höchstens 20 Seiten |
| PDF-Bilder | vorhandene 20-Bilder-Grenze, vorhandener bounded PDF-v2-Prozess |
| Neue Discovery-Exporte | höchstens 8, jeweils höchstens 1 MiB |

Unbekannte/zu kleine Speicher- oder RAMkapazität blockiert den Plan. Die deklarierten
Kapazitäts-/Single-Worker-Angaben sind Planungsbeobachtungen; sie ersetzen nicht die
aktuellen Kapazitäts-, Queue-, Guardian- und Source-Prüfungen beim späteren Start.
Es wird keine Kapazität am Produktionshost gemessen oder vorausgesetzt.

Die echten PDF-Dateigrößen/Seitenzahlen wurden ohne Download nicht ermittelt.
Eine Erhöhung auf größere PDFs ist nicht aktiviert. Falls eine freigegebene Datei
1 MiB/20 Seiten überschreitet, zuerst tatsächliche Byte-/Seiten-/Bildanforderung,
Parserausdehnung, freie Reserve, Scratch-/Artefaktbudget und Laufzeit messen und
separat begründen. Kein automatischer großer Download, OCR, Whisper, GPU oder Cloud.
PDF-v2 erhält Raw-Hash, Seiten-/BBox-Provenienz und verfügbare Bildreferenzen;
Layout- und Codeklassifikation bleiben heuristisch und keine fachliche Garantie.

## CLI und Reproduktion

Nur eingecheckte Snapshots, keine Artefaktsuche:

```sh
python -B -m scripts.cs50_week --manifest /explicit/repo/docs/course_sources/cs50/manifest.json
```

Für das vollständige belegte Inventar eine private Request-JSON erstellen und
Pfade auf die vorhandenen lokalen Exporte setzen. Keine Raw-Exporte ins Repo kopieren:

```json
{
  "manifest": "/explicit/repo/docs/course_sources/cs50/manifest.json",
  "mode": "discovery_only",
  "discovery_exports": [
    {
      "label": "operator_export/notes0.html", "role": "lecture_notes",
      "path": "/explicit/local/cs50_quality_review/material_01/original.html",
      "original_url": "https://cs50.harvard.edu/python/notes/0/",
      "sha256": "0e9af3114adec16938b89b511337f5db717ef2e14f1a606af600d6995ce09377"
    },
    {
      "label": "operator_export/pset0.html", "role": "assignment",
      "path": "/explicit/local/cs50_quality_review/material_02/original.html",
      "original_url": "https://cs50.harvard.edu/python/psets/0/",
      "sha256": "0d06fb2afcfcc01f5e4e7abbc2a09e057e17fda8c11fa60e948f1f9836cb2372"
    }
  ]
}
```

```sh
python -B -m scripts.cs50_week --request "$WEEK_REQUEST_JSON"
```

Die CLI schreibt JSON nur auf stdout. Der Report bleibt ein Plan; keinen Report als
Execution-Token verwenden. Reproduktion bindet IDs/Zähler/Quellhashes; der Request-
Fingerprint enthält auch explizite lokale Pfade und ändert sich bei deren Verlagerung.

## Nächste Betreiberentscheidung und offene Lücken

1. Zuerst B5 und die separate Aggregationsarbeit reviewen; kein automatischer Merge.
2. Einen kleinen expliziten Materialscope bestimmen: vorhandene Notes/PSet-/PDF-/
   Transcriptbindungen; bestehende Ergebnisse mit ihren Original-Receipts/Plänen
   zur Reuse-Prüfung benennen. Keine Job-Replays zum bloßen Reporting.
3. Für die fünf Aufgaben die oben beschriebene C18-Discoverybindung gesondert
   freigeben; ihre aktuellen Inhaltsdateien bleiben bis expliziter Quellenfreigabe
   unbeschafft. Vier Aufgaben haben weiterhin keinen lokalen Inhalts-Snapshot.
4. Pro zusätzlicher Quelle Nutzung, Lizenz, Zugriff, Aufbewahrung, Widerruf und
   Download/Processing ausdrücklich entscheiden. PDFs bei Überschreitung separat
   budgetieren. Medien/Shorts nur mit Zweck-/Evidence-Plan; keine Massenverarbeitung.
5. Für einen späteren Lauf tatsächliche Revision, persistente Roots, bestehende
   einzelne Worker-/Queueinstanz und Kapazität vor Ort prüfen. Deployment und
   Änderungen am laufenden Pilot sind durch diesen Auftrag nicht freigegeben.

Tests, geprüfte Originalhashes, Fehlversuche und Aufbewahrung:
[Validierungsbericht](complete_week_validation.md).
