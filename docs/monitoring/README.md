# C15 – Monitoring Stack Hardening & Pipeline Observability

Stand: 16.10.2026. Analyse-Ausgangsstand `09f7384`; abschließend auf den aktuellen
`master` bei `1a02efc` mit C11–C13 aktualisiert. Ausschließlich dieses Repository.
Kein Deployment, kein Image-Pull, keine Änderung laufender Container, produktiver
Daten oder Volumes.

- [Ist-Analyse und Sicherheitsgrenzen](audit.md)
- [Betrieb, Profile, Persistenz und Migration](operations.md)
- [Metrics v1 und Job-Control-Integration](pipeline-metrics.md)
- [Validierung und Grenzen](validation.md)

Der Kernstack enthält Prometheus, Alertmanager und Grafana. Host-, Container-
und Administrationszugriff werden über Profile aktiviert. Systemmetriken
benötigen den jeweiligen Exporter **und** explizite Target-Discovery.
Die Pipeline-Ansicht liefert ohne echten Exporter keine Messwerte.

```bash
python -m scripts.validate_monitoring --native --output /tmp/neuer-monitoring-report.json
python -m pytest -q tests/test_monitoring_config.py tests/test_pipeline_metrics.py
```

Vorhandene Reports werden nicht überschrieben. Fehlende native Werkzeuge
erscheinen als `not_run`; strukturelle Gültigkeit bestätigt weder PromQL
noch Image-Kompatibilität oder Laufzeitverhalten.

## Integrationsstand nach C16/C18

C15/PR 65, C16/PR 66 und C18/PR 67 sind inzwischen gemergt. Der
[authentifizierte C16-Jobexporter](../job_control/integration.md) liefert reale
Queue-/Job-/Heartbeatbeobachtungen. Ein Scrape ist ausdrücklich zu konfigurieren;
vorhandene Dashboards belegen kein laufendes Target. C18 ergänzt genau einen
festen Prozess-/Stage-Labelwert. Die früheren Paket-Testzahlen bleiben historische
Nachweise; aktuelle Auditprüfungen stehen in [audit/validation.md](../audit/validation.md).
