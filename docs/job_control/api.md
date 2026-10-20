# HTTP- und Datenvertrag v1

C20-B ergänzt den separaten, optionalen Vertrag
[`personal_assistant_workflows_v1`](../workflows/http.md). Die bisherigen
Capabilities, Prozesse, Previews, Job-, Log-, Cancel- und Artefaktantworten bleiben
unverändert. Workflow-Capabilities werden ausschließlich über die neue Route
geliefert, damit bestehende C17-/C20-DTOs mit `extra=forbid` kompatibel bleiben.

| Methode/Route | Versionierter Workflow-Vertrag |
| --- | --- |
| GET /v1/workflows/capabilities | WorkflowCapabilities, auch bei deaktivierten Workflows lesbar |
| POST /v1/workflows/inspect | WorkflowInspectRequest → WorkflowInspection; C18-Stufenpreview |
| POST /v1/workflows/execute | WorkflowExecuteRequest → WorkflowSubmission, HTTP 202 |
| POST /v1/workflows/resume | WorkflowResumeRequest → WorkflowSubmission, HTTP 202 |
| GET /v1/workflows/{workflow_id}?source_ref={ref}&offset=0&limit=10 | WorkflowInspection; Status, Stufen, aktuelle/persistierte Reports und paginierte Run-Historie |
| GET /v1/workflows/{workflow_id}/runs/{run_id}?source_ref={ref} | WorkflowRunReport; ursprünglicher Report eines konkreten Versuchs, falls vorhanden |

Jede neue Route verwendet dieselbe Bearer-Authentifizierung und unveränderte
Fehlerhülle. Die Workflow-Routen prüfen zusätzlich Eigentümerschaft für **alle**
Leser, Kursfreigaben, Katalogbindung und `workflows_enabled`. Execute/Resume
benötigen Operator, `confirmed: true`, aktuelle `preview_id`, explizite
`current_run_id` und einen Idempotency-Key. Ein frisches Execute ohne Vorlauf
sendet `current_run_id: null`; Resume benötigt eine konkrete aktuelle Job-ID.
Idempotency-Keys gelten innerhalb des Workflow-HTTP-Vertrags für
`(Subject, Key)` über Execute, Resume und alle Workflow-IDs hinweg.
Sie sind getrennt von den Keys der generischen C16-Jobroute.

Vollständige JSON-Nachrichten einschließlich aller fünf Stufen und unveränderter
Antworten stehen in [example-http.v1.json](../workflows/example-http.v1.json).
[Ablauf, Fehlercodes, Sicherheitsgrenzen und konkrete C20-UI-Übergabe](../workflows/http.md).
Die veröffentlichten Contract-Dateien enthalten die ergänzenden Pydantic-Schemas
unter `workflow_http`; ihre bisherigen `models`/Registry-Blöcke bleiben erhalten.

C19 ergänzt optional `material_parsing` (`pdf_enabled=true`, `PdfParams`,
`pdf_bundle` → `material_receipt`) auf den bestehenden Routen.
[PDF-v2-Eingabe-/Ausgabevertrag und Limits](pdf_lifecycle.md).
Die Defaultregistry bleibt bei zwei Prozessen; C18 ist separat optional.

Alle Routen unter /v1. Antwortobjekte tragen schema_version=1; Listen enthalten
versionierte Objekte. Preview-/Create-Requests haben Version 1 als Default,
Start/Cancel verwenden leere JSON-Objekte. Fehler enthalten nur
`{"schema_version":1,"error":{"code":"...","message":"..."}}`, niemals
Pydantic-Eingabewerte, Tokens, Tracebacks oder Hostpfade.

Jede Route, auch Prozesse, Logs, Artefakte und Metrics, verlangt
`Authorization: Bearer <token>`. SHA256 wird mit konfigurierten Verifiern
konstantzeitlich verglichen. Betreff, Rolle und Kursfreigaben kommen ausschließlich
aus der Serverkonfiguration. Keine Proxyheader-Rollen oder Browser-Ownerwerte.

| Methode/Route | Funktion |
| --- | --- |
| GET /v1/capabilities | Version, Registry, Backendbereitschaft und freigegebene Kurse/opaque Inputs |
| GET /v1/processes | Default- und freigegebene optionale Prozesse, Parameterschemas, Limits, Rechte und deaktivierte Einzelprozesse |
| POST /v1/previews | Parameter, Kataloghashes, Kurs-/Ressourcenbindung prüfen; kein Job |
| POST /v1/jobs | bestätigte Preview + Idempotency-Key atomar speichern und standardmäßig queued |
| POST /v1/jobs/{job_id}/start | zuvor mit start=false erstellten Job genau einmal freigeben |
| GET /v1/jobs | limit 1–100, offset 0–1000; Filter process_id/status/course_id |
| GET /v1/jobs/{job_id} | persistierter Zustand, Stage, Zeiten, Exit-Code und progress=null |
| GET /v1/jobs/{job_id}/logs | cursor/limit/query; max. 200 Ereignisse und 16.000 Bytes |
| GET /v1/jobs/{job_id}/artifacts | typisierte Referenzen, Größe/Hash/Quellbezug, keine Hostpfade/Dateiansicht |
| POST /v1/jobs/{job_id}/cancel | ausschließlich Abbruchanfrage; kein PID-/Containerparameter |
| GET /v1/metrics | authentifizierte, auf freigegebene Kurse begrenzte technische Aggregate |

Viewer lesen und prüfen Previews innerhalb ihrer Kursfreigaben.
Operatoren dürfen Jobs erstellen; Start/Abbruch benötigt zusätzlich Eigentümerschaft.
Auch ein Operator kann fremde Jobs nicht abbrechen.
Ein Viewer außerhalb des Kurses erhält keinen Zugriff auf dessen Jobs/Logs/Artefakte.

## Parameter und Bestätigung

Materialplanung:

```json
{"process_id":"material_planning","parameters":{
  "source_ref":"approved_snapshots","course_id":"cs50_python",
  "section":"0","resource_id":null,"output_name":"material-plan"
}}
```

source_ref ist eine Serverkatalog-ID, kein Dateipfad. Section/Resource filtern den
bestehenden MaterialPlan.select-Vertrag; mindestens der konkrete Kurs ist nötig.
Maximal 100 ausgewählte Materialien. output_name ist ein reiner Identifier,
der ausschließlich jobintern als results/<name>.json aufgelöst wird.

Qualitätsprüfung:

```json
{"process_id":"quality_evaluation","parameters":{
  "material_ref":"approved_material","course_id":"cs50_python",
  "output_name":"quality-report"
}}
```

Der serverseitige Bundle-Katalog bindet Plan, Normalized, Raw und Receipt sowie
alle benötigten lokalen Bildbytes. C10 prüft deren technische Konsistenz.
Ein technischer Gate-Fehler liefert einen fehlgeschlagenen Job mit Exit 1 und
trotzdem eine referenzierte strukturierte Quality-Reportdatei.

Create-Body: vollständige Preview aus dem vorherigen Response,
`confirmed: true`, optional `start: false`.
Header Idempotency-Key: 16–64 alphanumerische Zeichen/_/-.
Unbekannte Prozess-IDs oder Parameter, Pfade, Shell-/Python-Kommandos und
ersetzte Previewdaten werden abgewiesen. Globale/LLM-/Downloadausführung ist nicht angeboten.

## Persistenz und Status

Job enthält job_id, process_id, status, created_at/started_at/finished_at,
parameters, progress, phase, exit_code, error/error_class, artifact_refs,
initiated_by, input_refs/output_refs, cancellable und echte monotone Ausführungsdauer.
Keine künstlichen Prozentwerte, auch bei completed bleibt progress=null.

created → queued → running → completed | failed | interrupted.
queued/running → cancel_requested → cancelled, erst nach Executorbestätigung.
Interruption ist keine bestätigte erfolgreiche Ausführung. created wird nicht
automatisch freigegeben. Bereits terminale Jobs werden niemals erneut ausgeführt.

Idempotency bindet (authentifizierter Subject, Key) an dieselbe bestätigte
Preview/start-Absicht. Wiederholung liefert denselben Job, auch nach Neustart,
abgeschlossenem Job oder zeitweilig unerreichbarem Worker. Abweichender Body
unter demselben Key: 409. Ein neuer bewusster Auftrag braucht einen neuen Key.
Es gibt keine automatische Retrystrategie für fehlgeschlagene/interrupted Jobs.

Artefakthashes beschreiben die zum Veröffentlichungszeitpunkt vorhandenen Bytes.
Input- und Output-Dateien werden exklusiv neu angelegt. Kein beliebiger
Download-Endpunkt und keine statische Dateifreigabe sind implementiert.

HTTP: 200 Lesen/Preview, 202 akzeptierte Job-/Start-/Cancel-Anfrage.
Fehler: 401 unauthenticated, 403 forbidden, 404 not_found,
409 conflict, 422 invalid_request, 503 unavailable, 500 internal_error.
Transportfehler liefern http_rejected. Payload 32 KiB, Socketzeitlimit 3 s,
kein Chunked-Encoding/mehrdeutige Content-Length, eine Anfrage pro Verbindung.

## Historischer C14-Vertrag und aktueller C17-Client

Referenz: UI-PR 1 bei b003a870, inzwischen gemergt. /v1/capabilities,
previews, jobs, start/cancel, Logs und Artefaktoperationen folgen dessen Entwurf.
Der ursprüngliche C14-Stand besaß nur den Fakeadapter. C17/
[UI-PR #2](https://github.com/rf-data/personal-assistant-ui/pull/2) ist inzwischen
gemergt und implementiert den echten C16-HTTP-Client mit eigenen Wire-DTOs und
getrennter Fake-Demo. Die folgenden Unterschiede erklären das historische Mapping.

Notwendiges Mapping: job_id ↔ run_id, initiated_by ↔ owner,
finished_at ↔ ended_at, completed ↔ succeeded. C17 bildet `interrupted`
ausdrücklich ab und deutet es nicht als Erfolg um. Logs sind strukturierte
Cursorereignisse statt einer reinen Zeilenliste. Artifact-DTOs ergänzen Größe/Hash;
private Speicherorte bleiben auf dem Server. C16 nutzt echte freigegebene
Manifest-/Materialbundles, keine Fake-discovery_ref/normalized_ref.

Für C14-create/start-Trennung start=false senden und danach /start aufrufen.
C16s Standard ist ein atomar angenommener queued-Auftrag mit bestätigter Preview.
Der C17-Client prüft Registry/Schemas und bietet diese beiden Defaultadapter an.
Der optionale C18-Prozess `cs50_offline_workflow` benötigt eine gesonderte
UI-Vertragserweiterung; [Backend-Workflowvertrag](../workflows/README.md).
Dieses Dokumentationsaudit ändert keinen UI-Code.
