# C19 – Offline-Abnahme

16.10.2026; Linux, Python 3.12.12, Pydantic 2.13.4, Pytest 9.1.1,
Ruff 0.16.3, PyMuPDF 1.28.2 aus der bestehenden Entwicklungsumgebung.
Keine Installation, neuen Dependencies, Downloads, LLMs, API-Schlüssel oder
produktiven Dienste/Daten. Native Worker werden wirklich als Prozesse gestartet.

## Ergebnisse

| Lauf | Ergebnis |
| --- | --- |
| Breite relevante Regression, 372 Fälle | **370 passed, 2 skipped in 199.52 s** |
| Abschließende C19-Abnahme nach zusätzlicher sofortiger Restart-Reconciliation und Beispielprüfung | **25 passed in 95.50 s** |
| Ruff check | **All checks passed** |
| Ruff format --check | **26 files already formatted** |
| git diff --check | bestanden |
| Echter synthetischer C16/C18-PDF-Demolauf | completed, fünf Stufen, Exit 0, Resume verwendet denselben Job |

Die beiden Pytestläufe überlappen: 24 der C19-Fälle sind bereits im breiten Lauf
enthalten. Die abschließende Suite ergänzt die Reportprüfung und prüft den
unmittelbaren Executor-Neustart erneut; keine Addition zu einer erfundenen Zahl
unabhängiger Fälle. Die zwei übersprungenen PDF-v2-Tests benötigen optionale reale
lokale Artefakte. Es wurde dafür nichts heruntergeladen.

## Reproduktion

Vom Repositoryroot mit der bestehenden Entwicklungsumgebung; `python` und `ruff`
bezeichnen deren Programme. Temporäre Pfade müssen jeweils neu sein.

```bash
python -m pytest -q \
  tests/test_pdf_job_control.py tests/test_pdf_workflows.py \
  tests/test_job_control.py tests/test_job_executor.py tests/test_cs50_workflows.py \
  tests/test_cs50_material_pdf.py tests/test_cs50_material_pdf_v2.py \
  tests/test_cs50_visual_inventory.py tests/test_cs50_material_quality.py \
  tests/test_cs50_material_processing.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  --basetemp=/dev/shm/c19-new-regression-directory

python -m pytest -q tests/test_pdf_job_control.py tests/test_pdf_workflows.py \
  --basetemp=/dev/shm/c19-new-acceptance-directory

ruff check --no-cache src/job_control src/workflows \
  src/tools_materials/parse_pdf.py src/tools_materials/pdf_worker.py \
  scripts/cs50_workflow_demo.py tests/test_cs50_workflows.py \
  tests/test_pdf_job_control.py tests/test_pdf_workflows.py \
  tests/helpers/pdf_lifecycle_probe.py
ruff format --check --no-cache src/job_control src/workflows \
  src/tools_materials/parse_pdf.py src/tools_materials/pdf_worker.py \
  scripts/cs50_workflow_demo.py tests/test_cs50_workflows.py \
  tests/test_pdf_job_control.py tests/test_pdf_workflows.py \
  tests/helpers/pdf_lifecycle_probe.py
git diff --check

python -m scripts.cs50_workflow_demo --pdf --output /tmp/c19-new-pdf-example
```

Der breite Befehl enthält mit dem abschließend ergänzten Reporttest nun einen
Fall mehr als der oben dokumentierte 372-Fälle-Lauf. Der zusätzliche Fall wurde
in der abschließenden Abnahme erfolgreich ausgeführt.

Wie bei C18 wurden neue tmpfs-Testverzeichnisse verwendet: Das lokale Btrfs hatte
bereits unabhängig nachgewiesene sporadische ENOSPC-Probleme bei atomarem Ersetzen.
Ein erster Plattenlauf und ein früher tmpfs-Lauf waren nicht vollständig grün.
Der tmpfs-Lauf zeigte konkret Fork-Fehler durch das UID-weite NPROC-Limit 32;
diese führten zur dokumentierten festen PDF-/Workflowgrenze 512. Ein Zugriff auf
eine nicht serialisierte Dokument-ID im neuen Test wurde auf das vorhandene
Pydantic-Modell korrigiert. Fehlgeschlagene Vorläufe zählen nicht als Abnahme;
Atomare Speicherung und Provenienzprüfungen bleiben erhalten; die Ressourcen
bleiben auf feste, dokumentierte Werte begrenzt.

## Konkrete Abdeckung

- Erfolgreiches PDF-v2 über den echten C16-Executor/Guardian: Mehrseiten-PDF,
  Bildbytes, Raw-/Normalized-SHA, Course-/Lecture-/Resource-/Materialbindung,
  Parserconfig, Jobzeiten, Exit und gehashter Receipt.
- Ungültige, fehlende oder nach Preview geänderte PDFs; widersprüchliche
  Receipt-/Kataloghashes; vollständige gültige und beschädigte vorhandene
  Normalizedausgaben. Originalbytes bleiben bytegleich. Ein vorhandenes
  Jobverzeichnis wird nicht überschrieben; kein freier Pfad/Command/Parserparameter.
- Wirklicher Cancel bei laufendem Worker, wiederholter Cancel während Anfrage,
  Cancel nach Abschluss (bestehender Konflikt), Worker-Walltimeout und Job-Walltimeout.
- SIGKILL des eigenen Executors, sofortige Reconciliation über den vorhandenen
  Lifecycle-Lock, zusätzlich erneuter Neustart ohne Dispatch; SIGKILL des
  Adapter-Parents mit lebendem PDF-Kind. Nach bestätigtem Ende sind die zugehörigen
  `/proc`-Einträge entfernt; ein separat gestarteter fremder Prozess bleibt lebend.
- Fault Injection ersetzt nur im vertrauenswürdigen Testhelper den Workeraufruf
  durch einen blockierten Prozess vor dem vorhandenen PDF-Entrypoint. Sie nutzt
  den tatsächlichen `run_worker`, Adapter, Guardian, Queue und Restartcode.
  Kein Fehlerflag, Delay, Shellkommando oder Testhelper ist per API registriert.
- PDF in C18: dieselben fünf vorhandenen Stufen, echte C10-Prüfung und Handoff;
  Source-/Dokumentprovenienz, Bilder und identische Wiederholungen.
- Stale bei beschädigtem Raw, Normalized, Receipt oder Bild sowie geänderter
  Konfiguration; abhängiger Handoff wird stale. Explizites Resume nutzt neue
  Ausgabeorte und erhält alte, auch beschädigte Belege zur Nachvollziehbarkeit.
- Resume nach Cancel, Worker-/Jobtimeout und Executorverlust verwirft keine
  abgeschlossenen Plan-/Importbelege und übernimmt keine unbestätigte Parseausgabe.
- C15-Metriken bleiben endlich und ohne IDs/Pfade. Timeoutklassifikation wird
  sowohl bei Einzeljobs als auch beim Workflow aus dem tatsächlichen Fehler abgeleitet.
- Bestehende PDF-v2-/C13-/C10-, C16-, HTML-/Code-Workflow-, DAG-/Resume- und
  Monitoringtests bleiben grün. Die alten generischen C16-Tests decken zusätzlich
  TERM-ignorierende Nachfahren, Orphan-Exit, Gruppenkill und Quarantäne ab.

## Beispiel und Grenzen

[JSON](../workflows/example-pdf-report.v1.json) und
[Markdown](../workflows/example-pdf-report.v1.md) stammen aus demselben echten
synthetischen Lauf. Das JSON enthält den C16-Job, Preview, Report und vorhandenen
PDF-Receipt einschließlich ursprünglicher Bindung, Parserpolicy und Quellhashes.
Der Report ist erneut validiert und kanonisch gehasht; fünf Stufen erscheinen beim
anschließenden Statusabruf als `skipped`, ihre echten Zeiten/Jobrefs bleiben erhalten.
Demo-Input enthält keine echten Kursunterlagen; sein Erfolg ist keine Aussage
über reale CS50-Qualität oder mathematische Rekonstruktion.

Freigegeben sind ausschließlich die in [pdf_lifecycle.md](pdf_lifecycle.md)
benannten lokalen C16-/C18-Pfade. Linux, dedizierte private Arbeitsverzeichnisse
und vorhandenes PyMuPDF sind erforderlich. Unbestätigte Bereinigung bleibt
quarantänepflichtig. Kein allgemeiner Schutz vor beliebigen feindlichen Programmen,
keine automatische UID-/cgroup-Konfiguration und keine Produktionsfreigabe.
Der UID-weite Grenzwert ist ausdrücklich kein per-Job-Prozesszähler.

Die vollständige Repositorytestsuite mit optionalen SDK-/Serviceprofilen wurde
nicht ausgeführt; dieser Nachweis betrifft die oben genannten Offline-Regressionen.
Andere bekannte Altbefunde, insbesondere TXT-Transkripte ohne numerische Zeitwerte,
bleiben außerhalb C19. C17-UI-Integration, reale Dokumentevaluation und spätere
Visual-/Knowledgefolgestufen benötigen eigene geprüfte Schritte.
