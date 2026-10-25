# MAINT-04B – Workflow-Schema und Kursgrenze

25.10.2026; Basis `1a973f40199302416c4726658eb641c40dbae724` (MAINT-04).
C26 bleibt **HOLD**. Fachliche Korrektur lokal; Integration ausstehend.

## Nachgewiesenes Ausgangsproblem

`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models`
vergleicht alle Modelle unter `workflow_http.models` beider Vertragssnapshots.
Auf dem anfänglich unveränderten Arbeitsbaum und auf einem separaten
`git archive HEAD`-Quellsnapshot schlägt er fehl. Der Quellsnapshot ist kein
zusätzlicher Gitworktree und enthält keine privaten Konfigurationen.

Der vollständige rekursive Vergleich unter Pydantic **2.13.4 und 2.14.1**
ergibt auf der Basis exakt folgende vier Differenzen, keine weiteren:

| Snapshot | Modell | JSON-Pfad |
| --- | --- | --- |
| `docs/job_control/contract.v1.json` | `WorkflowInspection` | `/$defs/Workflow/properties/course_id/enum` |
| derselbe | `WorkflowRunReport` | derselbe |
| `docs/workflows/contract.v1.json` | `WorkflowInspection` | derselbe |
| derselbe | `WorkflowRunReport` | derselbe |

Erwartet: `cs50x`, `cs50_python`, `cs50_sql`, `cs50_ai`, `cs50_web`,
`cs50_cybersecurity`, in dieser Reihenfolge. Tatsächlich zusätzlich:
`loviscach_mathe_1`. Die verkürzte Pytest-Dictdarstellung mit Artifactfeldern
beweist keine Artifactänderung. Serialisierungs-/Validierungsversion,
Pydanticversion, Zufall, Cachepurges und Testfixtures erklären die Enumdifferenz
nicht; beide frischen Prozesse liefern denselben Befund.

## Ursache und maßgeblicher Vertrag

Commit `d6f16d0547b3e2139235a8b1bbfaac17d747e353` (DEV-03E) führt
`src.model_course.ContentCourseId` ein und verbreitert den öffentlichen
`src.job_control.models.Course`-Alias für Content/ACL. Derselbe Commit bindet
unter anderem `WorkflowParams` ausdrücklich an `DiscoveryCourse`. Die bereits
existierenden `Definition` und `Workflow` in `src/workflows/models.py` importieren
aber weiter `Course` aus C16 und werden dadurch unbeabsichtigt mitverbreitert.

Die [Architekturentscheidung](../architecture/content_course_scope.md) verlangt
ausdrücklich die unveränderte Discoverykursgrenze für CS50-Workflowparameter.
Auch `workflow_type=cs50_offline_materials_v1`, die geschlossene Discovery,
Materialmodelle, beide vollständigen Workflow-Snapshots und die tatsächlich
ausführbaren `WorkflowParams` verlangen CS50. Eine Loviscach-Definition konnte
isoliert validieren, aber keinen entsprechenden gültigen Workflowjob erzeugen.
Das ist ein unvollständig isolierter Aliaswechsel, kein beabsichtigter neuer
Workflowvertrag und kein Anlass, die Snapshots zu verbreitern.

## Implementierte Korrektur

Nur `src/workflows/models.py` bezieht seinen lokalen `Course`-Alias jetzt direkt
aus `src.model_discovery.cs50.CourseId`. Die zwei Feldannotationen und alle
öffentlichen Modellnamen bleiben bestehen. Der breitere C16-/Content-/ACL-Alias
bleibt erhalten. Beide Snapshotdateien sind **bytegleich zur Basis**.
Der vollständige rekursive Vergleich liefert danach unter beiden Versionen
**null Differenzen**. Keine neue Schema-Version, Migration, neuen Tags oder Defaults.

Bewusste Akzeptanzkorrektur: Definition v1/v2, Workflowreport v1 und darin
verschachtelte State-/HTTP-Modelle lehnen den versehentlich akzeptierten
Loviscachwert nun wieder mit `literal_error` am `course_id` ab. Unbekannte Kurse
bleiben ungültig. Dies stellt den veröffentlichten Vertrag wieder her; es ist
keine Freigabe eines generischen Nicht-CS50-Workflows.

## Producer, Consumer und gespeicherte Artefakte

| Grenze | Producer / Consumer | Wirkung |
| --- | --- | --- |
| Definition v1/v2 | Freigegebene Workflow-JSONdatei im Katalog; `workflows.definition.catalog_plan`/`prepare` | Frühe CS50-Validierung, weiterhin Pfad-/Hash-/Snapshotprüfungen |
| C16-Auftrag | `workflows.service.submit`, `WorkflowParams`, Controller/Registry | Gleiche sechs Kurse wie zuvor; keine zusätzliche ausführbare Variante |
| Workflowreport v1 | `workflows.engine` erzeugt aus Definition; Service und CLI lesen/rendern | Identische CS50-Dumps, IDs, Konfigurations-/Reporthashverfahren |
| State v1 und Archiv | `workflows.state.save`/`archive`/`load` | Eingebetteter Report wird weiterhin strikt validiert; keine Dateiumschreibung |
| HTTP v1 | `workflows.http`, `http_models.WorkflowInspection`/`WorkflowRunReport` | Vollständige Schemas stimmen wieder mit beiden veröffentlichten Verträgen überein |
| ACL/Katalog/Content/Index | C16-Principal/Katalog und ContentCourseId-Consumer | Loviscach bleibt gültig; keine Rollen-/Grantänderung |
| CLI und Demo | `scripts/cs50_workflow.py`, HTTP-Demo, veröffentlichte Beispielreports | Bestehende CS50-Nachrichten und Reports weiterhin lesbar |
| Externe Clients / private Bestände | Nicht im Repository prüfbar | Kein Nachweis über externe Validatoren oder manuell erstellte Nicht-CS50-Reports |

Definition hat die bestehenden Versionen **1/2**, State/Workflow/HTTP behalten
**1**, Protokoll `personal_assistant_workflows_v1`. Definition v2 bindet weiterhin
explizite Assignment-Snapshots; deren Semantik wird nicht verändert.

Alle sechs historischen Kurswerte werden synthetisch mit Definition v1/v2,
Report, State und Jobparametern als JSON rückgelesen. Die versionierten
`example-report.v1.json` sowie Preview/Report aus `example-pdf-report.v1.json`
werden ohne Feldverlust validiert. Das prüft keine privaten Bestände und behauptet
keinen Dateibyte-Roundtrip nach beliebiger Neuformatierung. Der vorhandene
HTTP-Beispielnachrichtentest prüft zusätzlich die veröffentlichten Umschläge.

## Tests, Restrisiken und Entscheidungen

22 neue Workflow-Vertragsfälle in `tests/test_workflow_course_contract.py`;
mit den 28 RunSettings-Fällen vor Produktivänderung **5 failed / 45 passed**,
danach unter Lockversion **50 passed**. Die fünf Fehlschläge betreffen
Loviscach-Definition v1/v2, beide Schemas und den Alias-/Enumvergleich.
Ausführliche weitere Ergebnisse einschließlich roter Prozessprüfungen:
[Validierung](maint04b_validation.md).

Falls private Artefakte unter der versehentlich breiten Validierung bereits
Loviscach-Workflowreports enthalten, lehnt der korrigierte Reader sie ab. Solche
Dateien werden hier weder gesucht noch gelöscht, migriert oder neu gehasht.
Ihre spätere Übernahme benötigt eine explizite Bestands-/Versionsentscheidung.
Für reguläre CS50-Artefakte ist keine Migration erforderlich. Ein künftig
generischer Workflow benötigt einen eigenen fachlichen Vertrag mit passenden
Producern, Jobparametern und Consumerprüfung; eine Snapshotaddition allein reicht
nicht. Für die Wiederherstellung des vorhandenen CS50-Vertrags ist keine solche
Entscheidung offen.
