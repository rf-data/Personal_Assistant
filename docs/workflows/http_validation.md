# C20-B – Offline-Validierung

17.10.2026 (Europe/Berlin). Basis: aktueller Backend-Master `5f3aa3c`, Tree
`82d0331`, nach C19/PR 69. Keine produktiven Daten, Netzwerk-/LLM-Aufrufe,
Downloads, neuen Dependencies, Migrationen, Parseränderungen oder UI-Edits.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Breite C16/C18/C19-/Material-/Quality-/Monitoring-Regression einschließlich zunächst 30 HTTP-Fällen | **401 passed, 2 skipped, 279.95 s** |
| Abschließende vollständige HTTP-Suite nach Ergänzungen und Annahme-Race-Absicherung | **37 passed, 79.60 s** |
| Zusätzlich abschließende Route-/Read-only-Prüfung einschließlich Workflow-ID `capabilities` | **2 passed, 4.38 s** |
| Unveränderte C20-UI-Suite gegen diesen Backendcheckout, einschließlich beider tatsächlicher Backendintegrationen | **90 tests, OK, 45.246 s** |
| Ruff check | **All checks passed** |
| Ruff format --check | **12 files already formatted** |
| git diff --check | **erfolgreich** |
| Vergleich bisheriger JSON-Vertragsblöcke mit Master | **unverändert**, Ergänzung nur unter `workflow_http` |
| Separater tatsächlicher HTTP-Demolauf mit PDF-v2 | **completed, 5 stages, 1 job**, Resume mit identischer Job-ID |

Die Läufe überlappen; ihre Fallzahlen werden nicht zu einer vermeintlichen
einzigen Testsuite addiert. Die zwei Skips sind bestehende optionale Prüfungen
mit nicht bereitgestellten realen PDF-Artefakten. Es wurden keine Dateien nachgeladen.
Die letzten HTTP-Ergänzungen wurden im abschließenden 37-Fälle-Lauf geprüft;
der zuletzt ergänzte Routingfall zusätzlich gezielt. Alle Produktionslimits
blieben unverändert. Python 3.12.12, Pydantic 2.13.4, PyMuPDF 1.28.2,
Pytest 9.1.1, Ruff 0.16.3 aus den vorhandenen Umgebungen.

Ein erster Lauf auf dem regulären temporären Dateisystem zeigte die lokal bereits
bekannten PDF-Timeouts/Supervisor-I/O-Probleme. Die vollständigen Prozessprüfungen
liefen anschließend in einem frischen tmpfs-Testbereich. Zwei neue Testfehler
(Annahme einer `.pdf`-Dateiendung und doppeltes Executor-Schließen) wurden
korrigiert. Die zusätzliche Race-Prüfung stellt sicher, dass eine reservierte,
von C18 abgewiesene Wiederverwendung beim Replay weiterhin neu validiert wird.
Weder Parser, Guardian noch Timeouts wurden für erfolgreiche Tests abgeschwächt.

## Abgedeckte Fälle

- Vollständige deterministische Stagepreview durch den echten C16-Application-
  Router; vor/nach Inspect unveränderte Inputs, SQLite-Jobdaten, Workflowmetadaten
  und Artefakte. Mutations-/Executionhelfer werden während der Leseprüfung gesperrt.
  SQLite-interne WAL/SHM-Verwaltung ist ausdrücklich ausgenommen und im Vertrag erklärt.
- Bestehende synthetische C19-PDF-Fixture mit mehreren Seiten und Bildbytes;
  echter Import, PDF-v2-Parsing, Quality und Handoff im bestehenden C16-Job.
- Fünf `skipped / verified_reuse`, ursprünglicher `completed`-Report, kanonischer
  Reporthash und separater Dateihash; identische Job-ID ohne neuen Versuch.
- Zwei gleichzeitige identische Starts, doppelte Requests, Browser-Refresh,
  verlorene Antwort nach dauerhafter C16-Annahme, Wiederholung nach Workerende,
  gleicher Key bei geändertem Body/Workflow/Aktion und reservierter Intent bei
  vorübergehend fehlendem Worker.
- Veraltete Preview, geänderte Inputbytes, genehmigte Konfigurationsänderung,
  Ausführungspolicy und Parent; falsche Hashes, fehlende Definition, ungültiges JSON
  und ungültiges Manifest. Kein neuer Job bei abgewiesenen Eingaben.
- Teil-Resume nach beschädigtem Normalized oder geänderter Parserkonfiguration:
  Planung/Import bleiben beim alten Job, die letzten drei Stufen erzeugen neue
  Outputs. Alte Bytes bleiben unverändert, auch bereits beschädigte Belege werden
  nicht überschrieben. Frühere angenommene Reuse-Keys bleiben an den alten Job gebunden.
- Fehlgeschlagener vorheriger Job: Execute wiederholt ihn nicht automatisch;
  ausdrückliches Resume erhält neuen Parentbezug und führt erforderliche Arbeit aus.
- Tatsächliches PDF-Cancel, Worker-Timeout und Executor-Kill/-Neustart über den
  vorhandenen C19-Testprobeaufbau; HTTP zeigt laufende Stufe, terminalen Job,
  Fehlerklasse und nach explizitem Resume erfolgreiche Wiederaufnahme. Die
  Testprobe ist ausschließlich vertrauenswürdiger Testcode, kein API-Parameter.
- Viewer-/Operatorrechte, eigener Viewer-Subject, fremder Owner im gleichen Kurs,
  Kursentzug, Source-Alias vor erster Stage, deaktivierte Workflows, nicht
  freigegebene Quellen, fehlende Authentifizierung und unerlaubte Pfade/Extrafelder.
- Manipulierte Reportbytes, Statehash und neu gehashte fremde Stage-/Outputrefs;
  Ablehnung vor dem Öffnen dieser Stagepfade. Aktuelle und historische Run-Reports
  erhalten die ursprünglichen Entscheidungen und Produzenten-IDs.
- Schema-/Versionsprüfung, strikte boolesche Bestätigung, fehlender Key/Parent,
  Queryduplikate/-grenzen, unveränderte bestehende C16-Schemas, vollständige
  veröffentlichte JSON-Nachrichten und No-Overwrite des Demoreports.

## Reproduktion

Aus dem Backendcheckout, vorhandene Dependencies, keine Installation:

```bash
C20B_TEST_ROOT=$(mktemp -d /dev/shm/c20b-tests-XXXXXX)
uv run --offline --no-sync python -m pytest -q \
  tests/test_workflow_http.py \
  tests/test_pdf_job_control.py tests/test_pdf_workflows.py \
  tests/test_job_control.py tests/test_job_executor.py tests/test_cs50_workflows.py \
  tests/test_cs50_material_pdf.py tests/test_cs50_material_pdf_v2.py \
  tests/test_cs50_visual_inventory.py tests/test_cs50_material_quality.py \
  tests/test_cs50_material_processing.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  --basetemp="$C20B_TEST_ROOT"

uv run --offline --no-sync ruff check --no-cache \
  src/job_control/http.py src/workflows scripts/cs50_workflow_http_demo.py \
  tests/test_workflow_http.py
uv run --offline --no-sync ruff format --check --no-cache \
  src/job_control/http.py src/workflows scripts/cs50_workflow_http_demo.py \
  tests/test_workflow_http.py
git diff --check
```

Für `--basetemp` immer einen neuen leeren Testpfad verwenden. Auf Systemen ohne
tmpfs einen neuen regulären temporären Testpfad wählen. Der Beispielreport wird
mit dem in [http.md](http.md) dokumentierten Demoaufruf exklusiv neu geschrieben.

Der zusätzliche UI-Kompatibilitätslauf erfolgte **ohne UI-Änderungen** im vorhandenen
C20-Checkout (Head `29ae186`):

```bash
C16_REPO=/pfad/zum/backendcheckout \
C16_PYTHON=/pfad/zur/bestehenden/backend-venv/bin/python \
  /pfad/zur/bestehenden/ui-venv/bin/python -m unittest discover -s tests -v
```

Diese UI-Suite belegt bestehende DTO-/Job-/PDF-Kompatibilität. Sie aktiviert die
neuen Workflow-HTTP-Routen **noch nicht im UI**; dessen bestehende Sperren bleiben
bis zum separat beschriebenen Folgepatch erhalten. Streamlit meldet im Bare-
Testmodus erwartete `missing ScriptRunContext`-Hinweise; die Tests bestehen.

## Abnahmegrenze und Folgeschritt

[example-http.v1.json](example-http.v1.json) enthält sieben vollständige Nachrichten
aus dem tatsächlichen synthetischen Application-/Queue-/PDF-Lauf ohne Socketserver.
Es ist kein Browser- oder produktiver Servernachweis und keine Bewertung realer
Kursmaterialien. Keine beliebigen Artefaktbytes werden über HTTP ausgeliefert.

Die vollständige Backendfunktion ist verfügbar. Als nächster Schritt kann der
C20-UI-Folgepatch die in [http.md](http.md#konkreter-übergabevertrag-für-den-c20-ui-folgepatch)
festgelegten DTOs/Routen und den bestätigten Intentablauf anbinden. Danach sind
Live-Stufenanzeige und UI-Resume einschließlich unverändertem Job gezielt über
diese HTTP-Schnittstelle abzunehmen. Kein Merge oder Deployment erfolgt automatisch.
