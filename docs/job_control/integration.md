# C14/C15 und späteres Deployment

C14-/C17-API-Mapping: [HTTP-Vertrag](api.md). Der reale UI-Client ist inzwischen
im separaten UI-Repository durch [PR #2](https://github.com/rf-data/personal-assistant-ui/pull/2)
gemergt. Er steuert die zwei C16-Defaultprozesse; der zusätzliche C18-Workflow
ist noch nicht im UI-Vertrag freigegeben. [Aktuelle Integration](https://github.com/rf-data/personal-assistant-ui/blob/main/docs/c17_integration.md). Serverseitige Beareridentität darf niemals durch
ein aus dem Browser übermitteltes actor/role-Feld ersetzt werden. Keine Tokens
oder internen Speicherorte im Streamlit-Session-State. Lokales CLI und
identitätsgeschützter HTTP-Transport existieren in C16, kein Live-Deployment.

## Metriken

C15/PR 65 war beim Start dieses Pakets noch offen. Sein veröffentlichter
Metrics-v1-Vertrag bei e74d3405 ist Referenz, keine vorausgesetzte Master-Pipeline.
Ist src.core.pipeline_metrics später vorhanden, validiert/rendert genau dieser
C15-Code die gemeinsamen Samples. Andernfalls verwendet der C16-Adapter einen
kleinen festen Textencoder mit denselben Namen und Labels; keine C15-
Implementierung wird kopiert oder stillschweigend als gemergt behandelt.

Abschlussstand: PR 65 ist inzwischen in `master` bei `b58f63c` integriert.
C16 wurde darauf aktualisiert. Die Integrationssuite verwendet den tatsächlichen
C15-Validator, einschließlich der Tests seiner Monitoring-Konfiguration.

GET /v1/metrics ist authentifiziert und auf die Kursfreigaben des Clients
beschränkt. Für Prometheus genau eine stabile separate Scrapeidentität mit den
vorgesehenen Kursfreigaben konfigurieren; keine einzelnen Nutzer als Targets,
keine mehrfachen überlappenden Controller-Snapshots summieren.

Beispiel für eine spätere, ausdrücklich separat zu aktivierende Scrape-Konfiguration:

```yaml
scrape_configs:
  - job_name: personal_assistant_job_control
    metrics_path: /v1/metrics
    authorization:
      type: Bearer
      credentials_file: /run/secrets/job_control_scrape_token
    static_configs:
      - targets: ["127.0.0.1:8016"]
```

Der Targetname gilt nur bei gemeinsamem Netzwerk-Namespace. In getrennten
Containern sind ein geprüfter privater HTTP-Adapter/Proxy und passende Adressierung
nötig. Der C15-Standardpfad `/metrics` muss für dieses Target explizit ersetzt
werden. Diese Dokumentation ändert keine laufende Scrape-Konfiguration und
enthält keinen produktiven Token.

Quelle ist ausschließlich die private SQLite-Jobhistorie und der echte
Executorheartbeat. Counter zählen tatsächliche gestartete Versuche.
Queued-Abbrüche ohne Dispatch zählen nicht als gestartete/terminal ausgeführte
Versuche. Interrupted wird nicht als bestätigter Erfolg/Fehler umgedeutet.
Dauern stammen aus der Guardian-Uhr und bestätigtem Ende. Fehlende Stage-
Instrumentierung wird ausgelassen, kein erfundener Stage-Prozentwert.

Gemeinsame Familien: workers_available, jobs_started_total, jobs_completed_total,
jobs_failed_total, jobs_running, job_duration_seconds sowie älteste laufende
Startzeit (alle mit personal_assistant_-Präfix). Kein Heartbeatdatensatz bedeutet
unbekannte Workerzahl/ausgelassene Availability; abgelaufener Heartbeat bedeutet
echte Null-Verfügbarkeit. Feste Labels nur process/worker_pool/outcome/error_class
und Histogramm-le; keine Job-/Nutzer-/Course-/Lecture-IDs oder URLs.

Neu in C16: personal_assistant_queue_jobs{process,worker_pool}, echte persistente
queued-Einträge. Das ist eine ausdrücklich dokumentierte C15-Erweiterung; der
C15-Validator bekommt sie nicht als bereits bekannte Familie untergeschoben.
Keine Stage-Histogramme ohne tatsächlich vorhandene Messungen.

C19: Der optionale PDF-Einzeladapter verwendet den bereits vorhandenen endlichen
Prozesswert `material_parsing`. `jobs_started_total`, bestätigte Outcomes und
Laufzeiten werden wie bei den bisherigen Adaptern erfasst. Sowohl PDF-Worker-
als auch Job-Walltimeout zählen unter `jobs_failed_total{error_class="timeout"}`.
PDF-Stufen in C18 gehören weiter zum einen `cs50_offline_workflow`-Job; sie werden
nicht als zusätzliche Einzeljobs gezählt. Kein neuer Labelwert und keine IDs/Pfade.

Pull-only: keine Netzwerkverbindung zu Prometheus/Grafana, kein Monitoring-SDK im
Dispatchpfad. Ein Metrics-Request-/Monitoring-Ausfall kann Jobs nicht stoppen.
Auth/privates Netzwerk, TLS/Proxy, Scrape-Discovery und Erweiterung des C15-
Schemas sind spätere Betreiber-/Integrationsschritte, keine automatischen Änderungen.

## Docker-/Workerprüfung

Bestehender api/Dockerfile: Python 3.11, fehlende api/requirements.txt und
fastapi_main; kein verwendbarer Controllerstart.
docker/DockerFile.worker nutzt Python 3.12 und umfangreiche lecture-worker-
Dependencies mit Tools für andere Pipelinearten. Keines dieser Images wurde
gebaut, gezogen oder gestartet und keine Livekonfiguration geändert.

Später: dedizierte Nicht-root-API-/Executor-Services auf demselben privaten
lokalen Dateisystem für SQLite/flock, Read-only Repository und freigegebene Inputs,
nur explizites Jobworkspace schreibbar, kein Docker-Socket. Eigener TLS-/Ingress-
Prozess, begrenzte Verbindungen, Request-/Rate-Limits, Secretdateien und
cgroup-Grenzen. Kein NFS-/Mehrhost-/mehrere-Worker-Modell mit dieser SQLite-Lösung.
Mehrere API-Prozesse benötigen einen geprüften Produktions-HTTP-Adapter; die
entkoppelte Controllerklasse erlaubt das ohne Workerrefactoring.

Der eingebaute HTTPServer bindet ausschließlich an Loopback und ist ein lokaler
Startweg, keine Produktionsfreigabe.
[Python weist auf diese Grenze hin](https://docs.python.org/3.12/library/http.server.html).
Die Root-/Socket-/Host-Mounts des Monitoring-Stacks gehören keinesfalls in den
Controller. Keine Änderungen an Coolify oder Hetzner und keine Deployments.
