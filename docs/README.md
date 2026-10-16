# Dokumentation — Einstieg und Gültigkeit

Stand: 16.10.2026. Die [Architektur](architecture.md) und [Roadmap](ROADMAP.md)
führen den tatsächlich gemergten Entwicklungsstand. Fachliche Verträge und
Paketnachweise bleiben in ihren bestehenden sinnvollen Unterordnern; es gibt
keine umfangreiche Verschiebung in eine neue Ordnerhierarchie.

| Bereich | Aktueller Einstieg | Art der Aussage |
| --- | --- | --- |
| Entwicklung | [Umgebung, CLI und Offlineprüfungen](development.md) | reproduzierbare lokale Arbeitsweise; keine automatische Installation |
| CS50 / Materialien / Lectures | [CS50-Index](cs50/README.md) | fachliche Verträge, getrennte Evaluation und Betrieb |
| Qualität | [C10](cs50/contracts/material_quality.md), [Prüfbericht](cs50/evaluation/material_quality.md) | technische Materialqualität / read-only Handoff |
| Mathematik | [C11](math_evaluation/README.md), [Nachweis](math_evaluation/validation.md) | unterstützte Syntax und unabhängige synthetische Kontrollen |
| Konsolidierung | [C12](knowledge_consolidation_hardening.md), [Nachweis](knowledge_consolidation_test_results.md) | konservativer Offlinevertrag / Evidence und Resume |
| Visual Assets | [C13](visual_inventory.md), [Nachweis](visual_inventory_test_results.md) | technische Referenz-/Geometrieinventur, kein neues Enrichment |
| Job-Control | [C16](job_control/README.md), [Integration](job_control/integration.md) | API, Queue, begrenzter Executor und Betriebsgrenzen |
| Orchestrierung | [C18](workflows/README.md), [Nachweis](workflows/validation.md) | optionaler lokaler Materialworkflow; weitere Stufen deaktiviert |
| Monitoring | [C15](monitoring/README.md), [Metrikvertrag](monitoring/pipeline-metrics.md) | Konfiguration/Schema und explizite C16-Integration |
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

„Gemergt“ wird durch den [Remote-Snapshot](audit/remote_snapshot.v1.json) belegt.
„Offline getestet“ ist stets auf die aufgeführte Suite und Umgebung begrenzt.
„Historisch“ bedeutet bewahrter früherer Stand, nicht fehlgeschlagen oder nutzlos.
Verträge, Beispiele, Tests und echte Produktionsartefakte werden getrennt
betrachtet. Bei widersprüchlichen alten Aussagen gelten aktuelle
Implementierung/Verträge und die expliziten Grenzen der Paketdokumentation.
