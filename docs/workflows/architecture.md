# C18 – Architekturentscheidung

Bestandsaufnahme vor Implementierung: Backend-`master` bei `303f0a6`, C16/PR 66
gemergt. Es existiert eine private SQLite-Jobhistorie mit eigener begrenzter
Queue, Linux-Guardian, Restart-Reconciliation und zwei freigegebenen Adaptern.
Eine zweite Jobqueue oder neue Datenbank ist nicht erforderlich.

| Vorhanden | Befund / Wiederverwendung |
| --- | --- |
| `tools_lecture/plan_lecture.py`, `model_lecture/data_resources.py` | Lecture-/ResourceTasks mit Medien-/Zeitbezug und globaler Settingskopplung; keine Material-Workflow-Recovery |
| `tools_lecture/adapt_cs50.py`, `execute_cs50.py` | explizite CS50-Pläne, SRT-Receipts, Pfad-/Hash-/atomare Metadatenfunktionen |
| `tools_materials/processing.py` | `make_plan`, `MaterialPlan.select`, `plan_steps`, `MaterialProcessor.parse/inspect` |
| `tools_materials/download.py` | vorhandener `obtain(local_file=…)`-Import und Raw-Receiptprüfung; kein HTTP-Pfad im Workflow |
| `model_materials/materials.py` | bestehende Course-/Resource-/Material-/Parser-/Dokument-/Block-IDs und ArtifactReceipt |
| `tools_materials/storage.py` | exklusive Veröffentlichung statt Überschreiben gültiger Artefakte |
| `tools_lecture/material_handoff.py` | C10-Quality-Gate und vorhandener referenzierbarer Handoff ohne Knowledge-Extraktion |
| `tools_knowledge/cs50_checkpoint.py` | Knowledge-spezifische Chunk-/Provider-Receipts; nicht als allgemeine Workflow-IDs umdeuten |
| `tools_knowledge/consolidation_run.py` | konservative Offline-Konsolidierung und Stale-Regeln; kein automatisch freigegebener Workflowrunner |
| `tools_evaluation/`, `tools_materials/visual_inventory.py` | separate begrenzte Evaluation/Visualinventur, zunächst nur Stage-Verträge |

Entscheidung: Ein ausdrücklich zusätzlich freigeschalteter C16-Prozess
`cs50_offline_workflow` führt einen kleinen Graphen **sequenziell innerhalb
eines bestehenden C16-Jobs** aus. Stage-Prozessverträge referenzieren die oben
vorhandenen Funktionen. Import/Parse/Handoff sind nur innerhalb dieses geprüften
Workflows freigegeben, keine freien neuen Einzeljob-Einstiegspunkte.
Workflow-ID ist stabil; `run_id` ist die C16-Job-ID der aktuellen Ausführung.
Stages verweisen auf diesen kontrollierenden Job, nicht auf erfundene Einzeljobs.

Versionierte atomare Workflow-Metadaten liegen im bereits privaten C16-Workspace;
die Jobqueue und Jobstatus bleiben ausschließlich in dessen unveränderter
SQLite-v1-Datenbank. Keine neue Datenbank, Schema-Adoption oder Migration.
Vollständige alte Stagebelege/Artefakte bleiben bei Resume in ihren ursprünglichen
Jobverzeichnissen. Neue Arbeit erhält neue Stageverzeichnisse; Parsing arbeitet
auf einer neuen Kopie des Imports, damit dessen gültiger Receipt unverändert bleibt.

Erster Umfang: höchstens drei explizite lokale HTML-v2-/Code-v1-Materialien.
PDF ist bewusst gesperrt: `parse_pdf.run_worker` setzt `start_new_session=True`.
Dessen Prozessgruppe liegt außerhalb der C16-Payloadgruppe; ein Workflow-Cancel
kann dafür derzeit keine vollständig bestätigte Beendigung garantieren.
Kein Parser wird geändert und diese Lücke wird nicht durch andere Killlogik verdeckt.

Die Erweiterung bleibt im C16-Default deaktiviert. Für Workflowtests/-betrieb
eine eigene explizit freigegebene C16-Konfiguration verwenden. C17s derzeitige
Job-DTOs kennen nur die zwei Einzelprozesse; deren Erweiterung ist ein separater
UI-Vertragsschritt. In C18 gibt es keine Streamlitänderung.

Stage-/Workflow-/State-Schemas ergänzen ausschließlich Ausführungsmetadaten;
fachliche Material-, Receipt-, Quality-, Handoff- und Knowledge-Modelle bleiben
bestehen. Der Workflow-Prozessvertrag wird bei Preview, Dispatch und im festen
Adapter geprüft. Netzwerkzugriffe sind im Adapter zusätzlich technisch gesperrt.

C15s endliches Labelvokabular erhält genau den statischen Prozess-/Stagewert
`cs50_offline_workflow` (jetzt jeweils elf Werte). Es werden keine fachlichen IDs
als neue Metriklabels eingeführt. Das bestehende C16-Metrikformat im deaktivierten
Default bleibt unverändert; der neue Prozess wird nur bei vorhandenen Jobs
emittiert.
