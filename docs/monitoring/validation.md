# Offline-Validierung

Befehle aus dem Repository mit vorhandener Python-3.12-Umgebung:

```bash
python -m scripts.validate_monitoring --native --output /tmp/neuer-monitoring-report.json
python -m pytest -q tests/test_monitoring_config.py tests/test_pipeline_metrics.py
ruff check src/core/pipeline_metrics.py src/core/monitoring_validation.py \
  scripts/validate_monitoring.py tests/test_pipeline_metrics.py tests/test_monitoring_config.py
ruff format --check src/core/pipeline_metrics.py src/core/monitoring_validation.py \
  scripts/validate_monitoring.py tests/test_pipeline_metrics.py tests/test_monitoring_config.py
git diff --check
```

`--root` erlaubt einen expliziten Konfigurationscheckout. `--output` schreibt
ausschließlich eine neue Datei (auch Symlinks werden nicht überschrieben).
Ohne Output geht JSON nach stdout, Kurzstatus nach stderr.
Exit 0: strukturelle Prüfungen und alle tatsächlich ausgeführten nativen Checks
erfolgreich; Exit 1: Befunde/native Fehler; Exit 2: ungültige Eingabe oder I/O.
Fehlende native Tools sind transparent not_run und machen Exit 0 nicht zu
einem Nachweis dieser Prüfungen. Ohne --native werden keine Programme gestartet.

Strukturelle Prüfungen: YAML ohne doppelte Keys, Compose-Sicherheitsinvarianten,
Profile, Pins, Loopback, Mounts/Datenpfade, Configrechte, Ressourcen-/Healthcheck-
Settings, DNS/Rulepfade, Alertnamen, lokaler Receiver, Datasource-/Dashboard-
Referenzen, No-data-Verhalten und generierter Metrics-Snapshot.
Dies ersetzt keine vollständige Compose-/PromQL-/Grafana-Schemaprüfung.

Die native Option benutzt feste Konfigurationsprüfkommandos mit 30-s-Limit:
Docker Compose config (alle Profile, keine Daemonverbindung), promtool check config,
promtool test rules und amtool check-config. Prometheus-Pfade werden nur in einer
privaten temporären Konfigurationskopie auf den Checkout abgebildet.
Compose erhält ein isoliertes Environment einschließlich privatem DOCKER_CONFIG,
keine allgemeine .env und ausschließlich
**synthetische Null-Digests** für die Syntaxprüfung. Keine Images werden damit
ausgeführt oder gezogen. Der produktive Overrides-Check weist diese Platzhalter ab.
Keine Secretdatei wird gelesen und kein nativer Output mit möglichen Geheimnissen
in Reports aufgenommen.

Die synthetischen Promtool-Regelfälle in tests/fixtures/monitoring decken Down/
Healthy/fehlenden Exporter, echte Null-Verfügbarkeit, fehlende Metrics,
lange laufende/beendete Jobs und hohe Fehlerrate ab.
Diese Datei ist kein produktives Scrape- oder Rule-Input und wird nicht gemountet.
[Offizielles Rule-Testformat](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/).

## Tatsächlich ausgeführt

Python 3.12.12, Pytest 9.1.1, Ruff 0.16.3, Docker Compose 5.0.2.
Keine Dependencyinstallation und keine Änderung von pyproject/Lockfile.

- **50 C15-Tests bestanden**, darunter echte daemonlose Compose-config-Prüfungen
  für Default-/alle Profile und Port-Overrides, Sicherheitsmutationen, YAML,
  Discovery, Secretreferenzen, unveränderte Datenpfade, Ignore-Regeln,
  Histogramme/Kardinalität, deterministische Reports und No-Overwrite.
- **127 Tests auf aktuellem master `1a02efc` bestanden**: dieselben 50 C15-Tests
  plus 77 Konsolidierungsregressionen nach dem Rebase auf C11–C13.
- **46 Lecture-/Checkpoint-Tests auf `1a02efc` erneut bestanden** (148,50 s),
  weil C12 die bestehende Konsolidierung verändert hat. Auch der abschließende
  separate C15-Lauf besteht mit 50 Tests nach Erhalt beider Rule-Dateiendungen.
- **155 bestehende Pipeline-Regressionen auf Ausgangsstand `09f7384` bestanden**
  (614,72 s): Materialqualität/-verarbeitung, Checkpoints, Scheduler/-Reports und
  Lecture-Runner. Der separat diagnostizierte Schedulerlauf bestand mit 5 Tests;
  sein 30-s-Faulthandler-Stack zeigte laufende lokale Modellvalidierung, keinen
  abgebrochenen Test. Doppelt ausgeführte Tests werden nicht als zusätzliche
  Testabdeckung gezählt.
- Ruff-Check und Formatprüfung aller fünf neuen Python-Dateien erfolgreich.
- Python-AST, JSON/YAML, Dokumentlinks, finale Newlines, Dateigrößen und
  git diff --check erfolgreich.
- Docker Compose config erfolgreich, ohne Daemon/Containerstart.
- **promtool und amtool fehlen**: Prometheus-Konfiguration, PromQL und die acht
  nativen Rule-Tests sowie Alertmanager-Produktschema wurden hier nicht nativ
  geprüft. Die entsprechenden Checks sind im Report ausdrücklich not_run.

[Maschinenlesbares Beispiel](validation.example.json) protokolliert insbesondere
fehlende native Werkzeuge, statt sie als erfolgreich darzustellen.

Nicht ausgeführt: Docker up/run/build/pull, Daemonzugriff, tatsächliche HTTP-
Healthchecks, Grafana-Laufzeit/Import, Benachrichtigungsversand, Live-Pipeline,
Secret-/Datenprüfung, Migration oder Deployment.
Diese Prüfungen bleiben vor einer späteren Betreiberfreigabe erforderlich.
