# Nachgewiesener Ist-Stand

Geprüft wurden alle versionierten Compose-Dateien:
`docker/docker-compose.monitoring.yaml` und `docker/docker-compose.ml.yaml`.
Lokale Environment-/Secretdateien, Datenablagen und Docker-Daemon wurden nicht
untersucht. Aussagen betreffen Konfiguration, keine tatsächlich laufenden Dienste.

| Befund bei `09f7384` | Auswirkung | C15 |
| --- | --- | --- |
| Alertmanager/node-exporter `latest`, Portainer `lts` | nicht reproduzierbare Erstellung | Digest der bereits freigegebenen Installation erforderlich; keine automatische Versionswahl |
| Prometheus `v3.5.0`, Grafana `12.1.0`, cAdvisor SHA256 | bestehende Pins; keine Aussage zur CVE-Freiheit | unverändert |
| Ports 9090/9093/3000/8080/9100/9443 ohne Hostadresse | auf allen Interfaces veröffentlicht | feste Loopback-Bindings, nur Portnummer konfigurierbar |
| Portainer standardmäßig mit Docker-Socket | vollständige Hostadministration | Profil `admin`; bleibt mächtige Administrationsschnittstelle |
| cAdvisor mit Host-Root, /var/run, Docker-Metadaten, /dev/kmsg | sensible Hostinformationen; Socket-Mount ist keine API-Autorisierung | Profil `containers`, bestehende Binds nachvollziehbar, /dev/kmsg entfällt |
| node-exporter mit /proc, /sys und Host-Root | sensible Hostmetadaten | Profil `host`, Binds read-only |
| keine Limits/Healthchecks, mehrfach restart always | Ressourcenverbrauch und Bereitschaft unkontrolliert | CPU-/RAM-/PID-/Loglimits, unless-stopped, fünf HTTP-Probes; Portainer-Ausnahme |
| Konfigurationen schreibbar | Änderung im Container möglich | read-only Configs/Root-Dateisystem, cap_drop, no-new-privileges |
| Target `alertmanager: 9093` | ungültiger Endpunkt durch Leerzeichen | Compose-DNS `alert_manager:9093` |
| relative Rule-Globs | Basispfadabhängigkeit | explizit /etc/prometheus/rules/*.yaml |
| kein Grafana-Provisioning | manuelle Einrichtung | feste Datasource- und Dashboard-UIDs |
| kein explizites Grafana-Bootstrap-Secret | Standardzugang bei neuer Datenbank möglich | externe Secretdatei erforderlich; bestehende Konten unverändert |
| Default-Bridge und alle Targets aktiv | keine Trennung optionaler Fähigkeiten | internes Netz, optionale Targets über File-SD |

Alertmanager besaß einen leeren lokalen Receiver. Der neue Name `local-only`
macht dieselbe Senke ausdrücklich sichtbar; es wird nichts versendet.

Die separate ML-Compose-Datei verwendet Postgres `13` (beweglicher Major-Tag),
Hostports 5433/5000, lokale MLflow-Build-/Artefaktpfade und Environment-Referenzen
für Datenbankzugänge. Sie wird vom Monitoring nicht geladen und bleibt unverändert.
Diese Pin-/Port-/Buildpfadrisiken sind ein eigener Folgeauftrag. Ihre YAML-Syntax
wurde geprüft; keine Datenbank, MLflow oder Container wurden gestartet.

## Implementiert und noch nicht verfügbar

`src/core/logger.py` erstellt Rich-/rotierende Dateihandler.
`src/core/observability.py` konfiguriert LiteLLM-/Langfuse-Callbacks und
`Agent.instrument_all()`: LLM-Tracing, kein Prometheus-Exporter.
Diese Module bleiben unverändert und werden von C15 nicht importiert.

`src/tools_knowledge/cs50_checkpoint.py` persistiert Job-/Chunkzustände und
Dispatchreservierungen. `schedule_cs50.py` verarbeitet ausgewählte Lectures
sequenziell und schreibt `schedule.status.v1.json`. Material-Runner besitzen
ArtifactReceipts mit completed/Fehlerzuständen. Diese Verträge liefern keine
globalen Counter, Worker-Heartbeats oder vollständigen Laufzeithistogramme.
Ein Scheduler-Pendingzustand ist keine persistente Queue.

Im geprüften Python-Code wurde weder ein prometheus_client-Exporter noch ein
start_http_server-Metrics-Endpunkt gefunden. `frontend/pages/A_p5_monitoring.py`
ist eine Platzhalterseite; `monitoring/grafana/potential_metrics.md` eine Ideenliste.
Ein allgemeiner authentifizierter Job-Control-Service ist nicht implementiert.
Produktive Reports/Logs wurden nicht ausgewertet oder in Messwerte umgedeutet.

Nach Zusammenführung von C11–C13 wurde die Analyse gegen `1a02efc` bestätigt.
Insbesondere C12 ergänzt versionierte Konsolidierungs-Audits und überprüfte
Receipts/Resume in `consolidation_run.py`. Auch diese neuen Ausgaben sind keine
Worker-Heartbeats, globalen Counter oder Prometheus-Endpunkte. Die Monitoring-
Dateien selbst wurden durch diese zwischenzeitlichen Merges nicht geändert.

## Verbleibende Grenzen

Loopback ist keine Authentifizierung. Produktion benötigt TLS, Identität,
Autorisierung, Netzfreigaben, Backups und einen geprüften Patchprozess.
Docker-Administratoren umgehen interne Netzgrenzen.
Die Profile host/containers/admin behalten bewusst sensible Sicht bzw. Rechte.
Root bei Portainer/cAdvisor ist ausdrücklich angegeben; Kernservices und
node-exporter verwenden die vorgesehenen Image-UIDs.
Insbesondere cAdvisor als UID 0 kann über den Host-Root-Bind auch Dateiinhalte
lesen; read-only bedeutet keinen Schutz vertraulicher Hostdateien. /var/run kann
zudem den Docker-Socket enthalten, dessen API durch einen read-only Bind nicht
auf Leseoperationen beschränkt wird. Dieses Profil ist daher nur für bewusst
freigegebene lokale Hosts vorgesehen, keine Grenze für nicht vertrauenswürdigen Code.

Portainer besitzt im nicht festgelegten Betreiber-Image keinen verifizierten
HTTP-Probe-Client. Sein Healthcheck ist ausdrücklich deaktiviert; keine
Versionsprüfung wird als Bereitschaft ausgegeben. Vor Verwendung HTTPS
`/api/system/status` extern prüfen. Alle konkreten Image-Probes sind noch in
Staging zu testen. Read-only/cap-drop kann auf manchen Kernel-/cgroup-Systemen
Exporter-Sicht einschränken; keine automatische Rechteausweitung.
