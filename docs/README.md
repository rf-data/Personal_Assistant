# Dokumentation — Einstieg und Gültigkeit

Planungsabgleich 17.10.2026: Backend `476f0a0d`, UI `14ccfc20`. Die
[Architektur](architecture.md) und [Roadmap](ROADMAP.md) unterscheiden den
gemergten Entwicklungsstand von künftigen Meilensteinen. Fachliche Verträge und
Paketnachweise bleiben in ihren bestehenden sinnvollen Unterordnern; es gibt
keine umfangreiche Verschiebung in eine neue Ordnerhierarchie.

| Bereich | Aktueller Einstieg | Art der Aussage |
| --- | --- | --- |
| Planung / Pflege | [Roadmap](ROADMAP.md), [Status](planning/status.md), [Issue-Entwurf](planning/issues.md), [Project](planning/project.md), [Freigabeplan](planning/github_execution.md), [Pflege](planning/governance.md), [Planprüfung](planning/validation.md) | C23–C32 geplant; keine Issue-/Project-Erstellung ohne gesonderte Freigabe |
| Entwicklung | [Umgebung, CLI und Offlineprüfungen](development.md) | reproduzierbare lokale Arbeitsweise; keine automatische Installation |
| CS50 / Materialien / Lectures | [CS50-Index](cs50/README.md) | fachliche Verträge, getrennte Evaluation und Betrieb |
| Qualität | [C10](cs50/contracts/material_quality.md), [Prüfbericht](cs50/evaluation/material_quality.md) | technische Materialqualität / read-only Handoff |
| Mathematik | [C11](math_evaluation/README.md), [Nachweis](math_evaluation/validation.md) | unterstützte Syntax und unabhängige synthetische Kontrollen |
| Konsolidierung | [C12](knowledge_consolidation_hardening.md), [Nachweis](knowledge_consolidation_test_results.md) | konservativer Offlinevertrag / Evidence und Resume |
| Visual Assets | [C13](visual_inventory.md), [Nachweis](visual_inventory_test_results.md) | technische Referenz-/Geometrieinventur, kein neues Enrichment |
| Job-Control | [C16](job_control/README.md), [Integration](job_control/integration.md), [C19 PDF](job_control/pdf_lifecycle.md) | API, Queue, begrenzter Executor, optionales PDF-v2 und Betriebsgrenzen |
| Orchestrierung | [C18](workflows/README.md), [Nachweis](workflows/validation.md) | optionaler lokaler Materialworkflow; weitere Stufen deaktiviert |
| Monitoring | [C15](monitoring/README.md), [Metrikvertrag](monitoring/pipeline-metrics.md) | Konfiguration/Schema und explizite C16-Integration |
| Systemabnahme | [C21-Plan](acceptance/c21_test_plan.md), [Ergebnisse](acceptance/c21_results.md), [Review](acceptance/c21_review.md) | tatsächliche HTTP-/Prozess-/AppTest-Nachweise und offene fachliche/Browsertests |
| Deployment | [C22-Architektur](deployment/architecture.md), [Abnahme](deployment/c22_validation.md), [Betrieb](deployment/operations.md) | gemergte Templates/Recoverytests; reale Runtime-/Produktionsfreigabe offen |
| Admin-/Chat-UI | [separates UI-Repository](https://github.com/rf-data/personal-assistant-ui/blob/main/README.md), [C17](https://github.com/rf-data/personal-assistant-ui/blob/main/docs/c17_integration.md) | kanonischer UI-Einstieg, Clientvertrag und UI-Deployment |
| Workerprofile | [CS50](../workers/cs50/README.md), [Index](../workers/cs50_index/README.md) | deklarierte Profile, Cache-/SDKgrenzen und frühere Installationsnachweise |
| Repositoryaudit | [Inventar](repository_inventory.md), [Dokumentenaudit](documentation_audit.md), [Cleanupplan](cleanup_plan.md), [Validierung](audit/validation.md) | Ist-Abgleich und konkrete sichere/offene Maßnahmen |

## Beibehaltene Struktur

`cs50/contracts/`, `cs50/operations/`, `cs50/evaluation/`, `job_control/`,
`monitoring/`, `math_evaluation/`, `workflows/` und `examples/` bleiben bestehen.
Neue Auditbelege liegen in `audit/`. Eine spätere gemeinsame `pipelines/`- oder
`contracts/`-Migration würde derzeit Referenzen ändern, ohne einen belegten
fachlichen Vorteil; sie ist nicht Teil dieser Bereinigung.

Historische Berichte behalten ihre damaligen Commit-/Testergebnisse:
[CS50-Archiv](cs50/archive/2026-10/README.md),
[frühere Übersichtsdokumente](archive/2026-10/repository-overview/README.md),
[frühere Konsolidierung](project_consolidation_report.md).
Die Archivseiten und lokalen Planungsnotizen sind keine aktuellen Betriebsaufträge.
`logger_notes.md`, `src/prio_list.md` und alte Experiment-READMEs bleiben als
unklare/historische Kandidaten sichtbar, bis ihre Verwendung separat geklärt ist.

## Nachweistiefe

„Gemergt“ wird im [aktuellen Default-Branch-Abgleich](planning/status.md) mit PRs
und Commits belegt. Der [C17.0-Snapshot](audit/remote_snapshot.v1.json) bleibt ein
historischer Nachweis seines damaligen Stands.
„Offline getestet“ ist stets auf die aufgeführte Suite und Umgebung begrenzt.
„Historisch“ bedeutet bewahrter früherer Stand, nicht fehlgeschlagen oder nutzlos.
Verträge, Beispiele, Tests und echte Produktionsartefakte werden getrennt
betrachtet. Bei widersprüchlichen alten Aussagen gelten aktuelle
Implementierung/Verträge und die expliziten Grenzen der Paketdokumentation.

Raw Sources und Parsed Content haben Vorrang. Vorhandene Knowledge-Verträge
bleiben erhalten; weitere Extraktion wird erst nach materialbezogener fachlicher
Evaluation priorisiert. [Verbindlicher Pflegeprozess](planning/governance.md).
