# C18 – Offline-Validierung

Umgebung: Linux, Python 3.12.12, Pydantic 2.13.4, Pytest 9.1.1 und Ruff 0.16.3.
Keine neuen Abhängigkeiten. Keine LLM-/Provideraufrufe, Downloads, produktiven
Server oder produktiven Datenbanken. Die Tests verwenden kleine lokale
synthetische CS50-Fixtures und den echten C16-Executor/Guardian/Adapter.

## Prüfkommandos

Vom Repositoryroot mit der vorhandenen Entwicklungsumgebung:

```bash
python -m pytest -q \
  tests/test_cs50_workflows.py \
  tests/test_job_control.py tests/test_job_executor.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  tests/test_cs50_material_quality.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_mapping.py tests/test_cs50_material_contracts.py \
  tests/test_cs50_material_inventory.py tests/test_cs50_material_download.py \
  tests/test_cs50_material_html.py tests/test_cs50_material_html_semantics.py \
  tests/test_cs50_material_code.py \
  --basetemp=/dev/shm/c18-new-test-directory

ruff check --no-cache src/workflows src/job_control src/core/pipeline_metrics.py \
  scripts/cs50_workflow.py scripts/cs50_workflow_demo.py \
  tests/test_cs50_workflows.py tests/test_pipeline_metrics.py
ruff format --check --no-cache src/workflows src/job_control src/core/pipeline_metrics.py \
  scripts/cs50_workflow.py scripts/cs50_workflow_demo.py \
  tests/test_cs50_workflows.py tests/test_pipeline_metrics.py
```

`--basetemp` immer auf ein neues, ausschließlich für diesen Test vorgesehenes
Verzeichnis setzen. In der Arbeitsumgebung lieferte das reguläre Btrfs sporadisch
`ENOSPC` beim atomaren Ersetzen von Metadaten, auch in einem unabhängigen
Dateiumbenennungstest ohne Anwendungscode. Deshalb wurden neue temporäre
Testworkspaces auf tmpfs verwendet. Die atomare Speicherung und die Tests wurden
nicht durch einen nichtatomaren Ersatz umgangen. Die vorherigen fehlgeschlagenen
Plattenläufe werden nicht als erfolgreiche Testnachweise gezählt.

## Ergebnis am 16.10.2026

- Pytest: **286 passed, 1 skipped in 82.83 s** (287 Fälle).
- Davon alle **24 C18-Workflowtests bestanden**.
- Ruff: **All checks passed**; Formatprüfung: **23 files already formatted**.
- `git diff --check`: bestanden.

## Abdeckung

- 24 Workflowfälle: deterministischer DAG/Preview/Reporthash, Zyklen, unbekannte
  Stufen, doppelte Kanten, fehlende/ungehashte Inputs und gesperrte Prozesse.
- Echter vollständiger Zwei-Material-Lauf: Import, HTML-v2-/Code-v1-Parse, C10-Gate,
  Lecture-Handoff, vorhandene Provenienz/IDs und deduplizierte Outputreferenzen.
- Skip und explizites Resume; sechs Stalevarianten für Input, Konfiguration,
  beschädigte Ausgabe, Schema, Parser und Provenienz; abhängige Propagation,
  neue Workspaces und byteweise unveränderte alte Artefakte.
- Parallele Startversuche mit genau einem bestehenden Queuejob, fehlender Worker,
  Stop-/Weiterlaufstrategie unabhängiger Zweige und blockierte Nachfolger.
- Echter Cancel während Verarbeitung, hartes Beenden des eigenen Testworkers,
  C16-Restart-Reconciliation und Wiederaufnahme; keine fremden Prozesse angefasst.
- Startunterbrechung/Timeout ohne Workflowbeleg, sichere Fehlerprojektion,
  Eigentümer-/Course-/Quellenbindung auch im direkten C16-Adapter, Metadatenhash.
- Schreiberlaubnis nur bei expliziter Freigabe, PDF-Lebensdauersperre,
  JSON-/Markdownexport und No-Overwrite, C15-Metriken und Defaultregistry.
- Bestehende C16-Prozess-/Timeout-/Descendant-/Recoverytests sowie C15- und
  Material-/C10-Regressionen ohne Änderung der bestehenden Parser.

Der optionale HTML-Test für Originalunterlagen wird übersprungen, wenn die
lokalen Originalartefakte fehlen (`Optional original notes artifacts are not
locally provided`). Es wird dafür nichts heruntergeladen und kein synthetischer
Ersatz als Original behandelt.

## Beispiel und Grenzen

Der echte Offline-Demolauf mit zwei synthetischen Materialien schloss neun Stufen
ab; Resume verwendete dieselbe bestehende Job-ID. Der eingecheckte
[JSON-Report](example-report.v1.json) wurde zusätzlich gegen das Pydantic-Modell
und seinen kanonischen SHA-256 geprüft. [Markdown](example-report.v1.md) stammt
aus demselben Lauf. Er belegt Funktionsverkettung, keine reale Modellqualität.

PDF, LLM-/Transkriptions-/Visualjobs und C17-UI-Unterstützung sind nicht freigegeben.
Die [bekannten Grenzen und nächsten Schritte](README.md#grenzen-und-nächster-schritt)
sind Bestandteil des Übergabevertrags.
