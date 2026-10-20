# CS50-Offline-Workflows (C18, Vertrag v1)

C20-B stellt die vorhandenen Services jetzt zusätzlich über den
[versionierten HTTP-Vertrag](http.md) bereit: schreibfreie Stufenprüfung,
bestätigtes Execute/Resume, Status, Run-Historie und ursprüngliche Run-Reports.
[Vollständige synthetische HTTP-Beispiele](example-http.v1.json),
[Offline-Validierung und Grenzen](http_validation.md).
Die Engine, Queue, PDF-Parser und Stageverträge bleiben bestehen; Workflows sind
weiterhin standardmäßig deaktiviert. Es gibt keine UI-Änderungen in diesem Paket.

Die [Architekturentscheidung](architecture.md) beschreibt den untersuchten Bestand
und die Integration in C16. Dieses Paket orchestriert vorhandene Runner für
maximal drei ausdrücklich ausgewählte lokale Materialien. Es ruft keine Provider
auf und verändert keine bestehenden Kurs-, Lecture- oder Knowledge-Objekte.

## Ablauf und Verträge

```mermaid
flowchart LR
  P[Bestehender Materialplan] --> I[Lokaler Import pro Material]
  I --> N[HTML-v2, Code-v1 oder PDF-v2 Normalisierung]
  N --> Q[C10 Quality Gate]
  Q --> H[Referenzierbarer Lecture-Material-Handoff]
```

Die Importzweige verschiedener Materialien sind unabhängig. Ein C16-Job führt
die deterministisch topologisch sortierten Stufen sequenziell aus. Unbekannte
Abhängigkeiten, doppelte IDs/Kanten und Zyklen sind Fehler. Die ausführbare
Allowlist enthält ausschließlich die fünf Verträge in `definition.ACTIVE`:

| Process-ID | Vorhandener Runner | Eingabe → Ausgabe |
| --- | --- | --- |
| `material_planning` | `processing.make_plan` | freigegebener Discovery-Manifest/Snapshots → ausgewählter `MaterialPlan` |
| `local_material_import` | `MaterialDownloader.obtain(local_file=…)` | Binding + lokale Bytes → Raw + `ArtifactReceipt` |
| `material_parsing` | `MaterialProcessor.parse` | kopierter Import/Receipt + ParserConfig → `NormalizedDocument`, Receipt, Raw, ggf. Bilder |
| `quality_evaluation` | `prepare_material_handoff` | bestehender Plan/Normalized/Receipt/Raw → `MaterialReview` |
| `lecture_material_handoff` | `prepare_material_handoff` | bestandenes Gate + dieselben Quellen → `LectureMaterialHandoff` |

Import/Handoff bleiben interne Stufen. C19 ergänzt einen separat freizugebenden
C16-PDF-v2-Einzeladapter; [Vertrag und Prozesskontrolle](../job_control/pdf_lifecycle.md).
Der zusätzliche Registry-Prozess heißt `cs50_offline_workflow`. Der vorhandene
C10-Handoff erhält die originale Provenienz und dessen Aggregationsvertrag:
TOC-, Link- und abgeleitete Codeprojektionen werden nicht erneut als kanonischer
Materialtext aggregiert. Ein Handoff startet keine Knowledge-Extraktion.

[contract.v1.json](contract.v1.json) enthält die Pydantic-JSON-Schemas für
Definition, Stage, Workflow und State, die C16-Workflowparameter, Registry und
fünf **deaktivierte** Folgeverträge: Transkription, Visual Enrichment, Knowledge
Extraction, Konsolidierung und Formula Evaluation. Diese Verträge deklarieren
Inputs/Outputs und bestehende Runner; sie schalten keine Ausführung frei.

## Eingaben und Identitäten

Ein freigegebener C16-Katalogeintrag `kind=workflow_bundle` enthält `root`, die
SHA-256-Hashes **aller** lokalen Dateien, `course_ids` sowie die Rollen
`manifest` (bestehender CS50-Manifest) und `workflow` (Definition v1). Definition:

```json
{
  "schema_version": 1,
  "workflow_type": "cs50_offline_materials_v1",
  "course_id": "cs50_python",
  "section": "0",
  "lecture_ids": [],
  "sources": {"resource:<existing-id>": "local/notes.html"},
  "source_origin": "official",
  "max_bytes": 524288,
  "max_blocks": 1000,
  "continue_independent": true
}
```

`resource:<existing-id>` ist durch eine echte vorhandene Resource-/Material-ID
aus dem bestehenden Plan zu ersetzen. Jede Auswahl muss genau ein Binding
auflösen. Es gibt keine freie URL-/Shell-/Provider-Eingabe. Relative Pfade müssen
portabel, symlinkfrei und im freigegebenen Katalog enthalten sein. Für erzeugte
synthetische Fixtures ist `source_origin=synthetic` ausdrücklich gesetzt.

`workflow_id` bleibt über Versuche stabil und ist an Eigentümer, Course und
Source-Ref gebunden. `run_id` ist die echte C16-Job-ID des aktuellen Versuchs.
`stage_id` nutzt vorhandene `material_task`-IDs einschließlich des bestehenden
Parse-Tasks; `stage.job_id` bezeichnet den tatsächlichen produzierenden Job.
Wiederverwendete Stufen behalten ihre ursprüngliche Job-ID und Outputpfade.

## Preview, Skip, Stale und Resume

`plan`/`preview` berechnen dieselbe schreibfreie Vorschau: Reihenfolge, erwartete
Inputs/Outputs, vorhandene Inputhashes, fehlende Inputs, blockierte/ausführbare
Stufen, verifizierte Wiederverwendung und erwartete neue Workspaces. Ohne
vorhandene Ausführung bleiben Zeitstempel und Run-ID leer. Gleiche Inputs und
gleicher persistenter Zustand liefern denselben Preview-Hash. Ein fehlerhafter
Manifest/Definitionsvertrag liefert einen CLI-Fehler statt eines erfundenen Plans.

Skip erfolgt nur nach erneuter Prüfung von Input-/Abhängigkeitshashes,
stufenrelevanter Konfiguration, Outputbytes/-hashes, vorhandenen Modellversionen,
Parser-/Receipt-Konsistenz und Quellenprovenienz. Parseprüfung verwendet auch
`MaterialProcessor.inspect`; Quality/Handoff werden gegen den bestehenden
Offline-Vertrag geprüft. Fehlende oder widersprüchliche Belege verhindern Skip.

Geänderte Inputs/Konfiguration, beschädigte Ausgaben oder inkompatible
Parser-/Schema-/Provenienzbelege markieren erfolgreiche Stufen als `stale` und
propagieren diese Entscheidung auf abhängige Stufen. Unabhängige gültige Zweige
bleiben wiederverwendbar. `execute` liefert bei vorhandener Ausführung deren Job
zurück; nur **explizites `resume`** startet nach einem terminalen Versuch neue
Arbeit. Sind alle Ergebnisse gültig, liefert Resume dieselbe bestehende Job-ID.
Gleichzeitige identische Starts verwenden die bestehende C16-Idempotenz/Queue.

Neue/ungültige Stufen laufen in einem neuen Job-/Stageverzeichnis. Gültige alte
Artefakte werden weder überschrieben noch gelöscht. Parsing erhält eine neue
Kopie des Imports und aktualisiert dessen ursprünglichen Receipt nicht.
Unvollständige, nicht bestätigte Outputs nach Abbruch werden nicht übernommen.

| Zustand | Bedeutung / nächster Schritt |
| --- | --- |
| `pending` | C16-Job wartet in dessen Queue |
| `ready` | Inputs und Abhängigkeiten erlauben Ausführung |
| `blocked` | fehlender Input, ungültiger Vorgänger oder Stopstrategie |
| `stale` | frühere erfolgreiche Ausgabe erfüllt den aktuellen Vertrag nicht |
| `running` | bestehender C16-Job führt eine Stufe aus |
| `completed` | neue Ausgabe erfolgreich geprüft |
| `skipped` | frühere Ausgabe erneut vollständig verifiziert |
| `failed` | Stufenfehler oder fehlgeschlagener C16-Job |
| `cancelled` / `interrupted` | C16 hat Abbruch/Workerverlust bestätigt; explizites Resume möglich |

Standardmäßig laufen unabhängige Zweige nach einem Stufenfehler weiter;
`continue_independent=false` blockiert alle noch offenen Stufen. Abhängige Stufen
bleiben stets blockiert. Ein Fehler erzeugt keinen künstlichen Output. Ein
fehlgeschlagenes Quality Gate behält seinen echten Fehlerreport als Stufenbeleg.
Bei einem Abbruch zwischen Stufen wird keine fiktive unterbrochene Stufe erzeugt.
C16-Timeouts/Startfehler ohne Workflowbeleg bleiben im Workflowreport als
Jobfehler sichtbar. C16 übernimmt Prozessgruppen, Limits, Cancel und Recovery.

## Persistenz und Reports

Die unveränderte C16-SQLite-v1-Datenbank enthält weiterhin allein Queue und
Jobhistorie. Private, atomare Workflow-Metadaten liegen daneben unter
`workflows/<workflow_id>/state.v1.json`; alte bestätigte Versuche werden exklusiv
unter `history/<run_id>.json` archiviert. Ein OS-Lock verhindert konkurrierende
Workflow-Schreiber. Metadaten werden auf Graph, Eigentümer, Versuchslinie und
Reporthash geprüft. Höchstens zehn bestätigte Workflowversuche sind erlaubt.

Unveränderliche Stageausgaben liegen unter
`jobs/<job_id>/results/stages/<stage_id_hash>/`. Der C16-Workflowreport ist ein
bestehender C16-Artifact vom Typ `workflow_report`. Jeder Output nennt Typ,
vorhandene fachliche Identität, relativen Pfad, SHA-256 und Bytegröße. Die
Gesamtprojektion dedupliziert `(kind, identity, sha256)`; identische Rawbytes in
Import und Parse werden nicht doppelt gezählt. Der Report ist keine neue
Knowledge-Aggregation.

Reports enthalten Stage-/Jobzuordnung, Inputhashes, Outputs, Entscheidungen,
Fehler, Stalegründe, Start/Ende und Laufzeit. `report_sha256` ist der SHA-256 der
kanonischen JSON-Darstellung ohne dieses Feld (bestehender C16-`fingerprint`).
Laufzeiten/Job-IDs echter Ausführungen variieren; deterministisch ist die
Entscheidung bei identischem Zustand, nicht eine erfundene konstante Laufzeit.
JSON-/Markdownexport ist ausschließlich auf neue Pfade außerhalb der Katalog-
und privaten Jobworkspaces erlaubt; bestehende Exporte werden abgelehnt.

## Lokale CLI

Wie bei C16 erfolgt der Einstieg als Python-Modul vom Repositoryroot. Eine eigene
explizite Offline-Konfiguration verwendet `execution_enabled=true`,
`workflows_enabled=true`, Operatoridentität, Coursegrant und den beschriebenen
Hashkatalog. Im Default bleibt die Erweiterung deaktiviert. Keine produktiven
Workspaces oder Token für den Test verwenden.

```bash
python -m scripts.cs50_workflow_demo --output /tmp/c18-example-new
# Das Demo erzeugt zwei synthetische lokale Materialien und einen echten C16-Lauf.

python -m scripts.cs50_workflow preview --config /tmp/c18-example-new/config.json --token-file /tmp/c18-example-new/token --source-ref synthetic_workflow --workflow-id synthetic_workflow
python -m scripts.job_control worker --config /tmp/c18-example-new/config.json
# Worker in einem separaten Terminal; kein zweiter Executor im CLI.
python -m scripts.cs50_workflow execute --confirm --wait --config /tmp/c18-example-new/config.json --token-file /tmp/c18-example-new/token --source-ref synthetic_workflow --workflow-id synthetic_workflow
python -m scripts.cs50_workflow resume --confirm --wait --config /tmp/c18-example-new/config.json --token-file /tmp/c18-example-new/token --source-ref synthetic_workflow --workflow-id synthetic_workflow
python -m scripts.cs50_workflow report --config /tmp/c18-example-new/config.json --token-file /tmp/c18-example-new/token --source-ref synthetic_workflow --workflow-id synthetic_workflow --json-output /tmp/c18-export-new.json --markdown-output /tmp/c18-export-new.md
```

`plan`, `preview`, `status` und `report` starten keine Verarbeitung und benötigen
keinen Worker. `execute`, `resume` und `cancel` erfordern `--confirm`; `--wait`
wartet begrenzt auf den vorhandenen C16-Worker. Ohne Wait wird das Jobobjekt
zurückgegeben. Reportexitcode: 0 für erfolgreich/planbar, 1 für fehlgeschlagen,
blockiert, unterbrochen oder abgebrochen; ungültige CLI-Anfragen: 2 mit sicherem
Fehlercode. Kurs-/Ownerrechte werden auch beim schreibfreien Zugriff geprüft.

Der zusätzliche Prozess ist bei freigeschalteter Konfiguration auch über die
bestehenden C16-Preview/Create/Start/Cancel-Endpunkte verfügbar. Es gibt keinen
neuen Workflow-Server. C15 verwendet den expliziten zusätzlichen endlichen
Process-/Stage-Labelwert `cs50_offline_workflow`; Workflow-/Job-/Material-IDs
werden weiterhin niemals Metriklabels.

## Grenzen und nächster Schritt

- HTML-v2, Code-v1 und PDF-v2, maximal drei Materialien, 1 MiB pro Quelle, 2.000 Blöcke;
  maximal 13 Stufen. Der C16-Workflowjob ist auf 90 s Wandzeit, 60 s CPU,
  768 MiB Adressraum und 8 MiB pro Ausgabedatei begrenzt.
- PDF-v2 ist nach C19-Lebenszyklustests freigegeben: innerhalb C16 erbt sein
  Worker die kontrollierte Adaptergruppe. Höchstens 20 Seiten/20 Bilder,
  10 s Worker-Wallzeit und 512 MiB Workeradressraum; engere Byte-/Blocklimits
  der Definition gelten weiterhin. Andere PDF-Versionen bleiben gesperrt.
- Keine Transkription, visuellen Providerjobs, Knowledge-Extraktion oder
  automatische Konsolidierung/Formelevaluation. Deren Verträge sind Vorbereitung.
- Keine allgemeine DAG-Plattform, Parallelworker oder automatische Wiederholung.
- C17s UI-DTOs kennen bisher nur die zwei ursprünglichen Prozesse. Workflowbetrieb
  benötigt ein separates C16-Profil/Workspace; die UI wird in diesem PR nicht
  erweitert. Nächster UI-Schritt ist ein versionierter Preview-/Status-/Report-
  Vertrag mit getesteter Cancel-/Resume-Darstellung.
- Der Beispielreport ist ein echter synthetischer Offline-Lauf und belegt
  Runnerverkettung und Provenienz, keine Qualitätsaussage zu realen Kursunterlagen.

Beispiele: [JSON](example-report.v1.json), [Markdown](example-report.v1.md).
PDF-Demo: `python -m scripts.cs50_workflow_demo --pdf --output /tmp/c19-new-pdf-demo`.
PDF-Beleg: [JSON](example-pdf-report.v1.json), [Markdown](example-pdf-report.v1.md),
[C19-Testbericht](../job_control/pdf_validation.md).
Testnachweis und reproduzierbare Prüfkommandos: [validation.md](validation.md).

Der HTML-/Code-Beispielreport zeigt den Statusabruf nach Abschluss: Die neun
Stufen sind bereits erneut verifiziert und deshalb `skipped`; ihre Job-ID,
Laufzeiten und ursprünglichen Outputpfade bleiben erhalten.
