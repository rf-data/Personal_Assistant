# Konfiguration und Profile

Alle Befehle sind manuell aus dem Backend-Repository auszuführen. Beispiele
bezeichnen Platzhalter, keine vorhandenen Serverpfade. Secrets bleiben außerhalb
von Git und Buildkontext. [Sicherheitsvertrag](security.md),
[Abnahmebedingungen](c22_validation.md).

**Local Development:** bestehender `scripts.job_control check --config` und
UI `streamlit run app_admin.py`; keine produktiven Dienste. UI-Backend und Auth
bleiben standardmäßig `disabled`. Demo nur mit `APP_ENV=local` explizit wählen.
`deployment/profiles.toml` dokumentiert die drei Profile ohne Auto-Start.

**Local Integration:** vorhandenen C21-TCP-Driver mit vorhandenen Umgebungen und
expliziten Pfaden starten. Er erzeugt neue synthetische Daten, begrenzt Verbindungen
auf seinen eigenen Loopback-Endpunkt und überschreibt keine Reports:

```sh
UI_PYTHON -B scripts/acceptance/c21_ui_tcp.py \
  --ui-repo /absolute/path/to/personal-assistant-ui \
  --backend-repo /absolute/path/to/Personal_Assistant \
  --backend-python /absolute/path/to/backend/.venv/bin/python \
  --output /new/external/c22-tcp-report.json
```

Ergänzend `pytest tests/test_deployment_operations.py
tests/test_deployment_transport.py` für verwaltete Rollen, Neustarts und Restore.
Keine produktiven Configs oder Inputs an diese Tests übergeben.

**Production Template:** `deployment/compose.yaml`, ausschließlich explizites
Profil `private-production`; ohne Profil null Dienste. Benötigte Variablen müssen
auch für die reine Compose-Auswertung belegt sein. Fehlende Werte führen zum
Abbruch. `pull_policy: never`, keine Ports, keine Watcher/Auto-Deploy-Hooks.
Die UI-Änderung aus dem separaten [UI-PR #5](https://github.com/rf-data/personal-assistant-ui/pull/5) ist Voraussetzung.

| Variable | Vertrag |
| --- | --- |
| `BACKEND_DIGEST`, `UI_DIGEST`, `GATEWAY_DIGEST` | geprüfte lokal vorhandene Release-Images, vollständige 64-stellige SHA256-Digests |
| `PYTHON_IMAGE`, `UV_IMAGE`, `CADDY_IMAGE` | nur beim manuellen Build: explizite Version **und** `@sha256:<64 hex>`; keine Tags ohne Digest |
| `C22_PRIVATE` | bestehender lokaler Workspace, UID/GID 10001, 0700; nicht automatisch angelegt |
| `C22_CATALOG` | separater freigegebener Katalog; readonly im API-/Executor-Container |
| `C22_CONFIG` | bestehende 0600-Controllerdatei, Eigentümer 10001; Startvorlage `deployment/controller.json.example` |
| `C22_API_DNS` | kontrollierter DNS-Name, identisch mit Zertifikat-SAN und privatem Docker-Alias |
| `C22_TLS` | private 0700-Gateway-Daten: `api.crt`, `api.key` 0600, `ca.crt`; Eigentümer 10001 |
| `C22_CA` | öffentliches ausstellendes CA-Zertifikat als Datei für UI/Prometheus; niemals privater Schlüssel |
| `C22_UI_ENV` | private UI-Envdatei mit OIDC-Issuer, Subject-Allowlisten und individuellen Dateibindings |
| `C22_UI_SECRETS` | privates Verzeichnis mit individuellen Bearerdateien; 0600, UID 10001 |
| `C22_OIDC` | private Streamlit-`secrets.toml`, 0600 UID 10001; kein Secret im Image |
| `C22_INGRESS_NETWORK` | bereits vorhandenes Reverse-Proxy-Netz; keine automatische Netzerzeugung für öffentlichen Ingress |

Controller-JSON nutzt unverändertes `Settings`-Schema v1. Die Vorlage enthält
keine Identitäten, keinen Katalog und deaktiviert Ausführung, Workflows und PDF.
Für Freigaben muss der Operator echte Kurs-Scopes, SHA256 der individuellen Tokens
und erlaubte Katalogdateien hinterlegen. Katalogwurzeln im JSON verwenden
`/var/lib/personal-assistant/catalog/<ref>`; identische absolute Pfade in beiden
Containern. Runtime-Config und Workspace bleiben getrennt. `max_parallel=1` für
die angegebene Ressourcendimensionierung; eine Erhöhung verlangt neue Abnahme.

Private UI-Envdatei: `ADMIN_OIDC_ISSUER`, `ADMIN_OPERATOR_SUBJECTS` und
`ADMIN_VIEWER_SUBJECTS` als JSON-Listen, `JOB_API_IDENTITIES` als JSON-Liste der
bestehenden `{ui_subject, backend_subject, role, token_file}`-Bindings.
Tokenpfade liegen unter `/run/secrets/c16/`. Compose fixiert server/http/production/
oidc und HTTPS-Origin. Keine Bearerwerte in Umgebungsvariablen.
OIDC-`[auth]` enthält `client_id`, `client_secret`, mindestens 32 Zeichen
`cookie_secret`, HTTPS-`redirect_uri` mit `/oauth2callback` und HTTPS-Metadata-URL.
Es wird der bestehende einzelne Standardprovider verwendet.

**Offene Dependency:** Das UI-Lockfile und die lokale UI-Umgebung enthalten kein
Authlib. Der Produktionslauncher verweigert dann den Start. Vor Go-live muss ein
geprüftes Authlib mit transitiven Dependencies im UI-Lockfile aufgenommen und
offline/mit ausdrücklicher Downloadfreigabe bereitgestellt werden. C22 installiert
oder kopiert keine ungeprüften Auth-Pakete aus anderen Umgebungen.

Manuelle Builds erst nach Freigabe der erforderlichen Images/Wheels und Digests;
hier wurden sie wegen fehlender Images nicht gestartet:

```sh
docker build --pull=false -f deployment/Dockerfile \
  --build-arg PYTHON_IMAGE="$PYTHON_IMAGE" --build-arg UV_IMAGE="$UV_IMAGE" .
docker build --pull=false -f deployment/gateway.Dockerfile \
  --build-arg PYTHON_IMAGE="$PYTHON_IMAGE" --build-arg CADDY_IMAGE="$CADDY_IMAGE" .
# Im UI-Repository: docker build -f docker/DockerFile.UI mit PYTHON_IMAGE/UV_IMAGE.
```

`--pull=false` allein verhindert fehlende Basisimage-Downloads nicht. Deshalb
vorher lokale Verfügbarkeit und Freigabe prüfen. Frozen Locks verhindern
Neuauflösung, nicht den erstmaligen Wheelbezug. Dateispezifische Dockerignore-
Allowlists begrenzen den Buildkontext. Keine gesamten Daten-/Configverzeichnisse
in Images aufnehmen. Release-Image-Digests danach erfassen; ein lokaler Image-ID-
Hash ist kein Registry-RepoDigest. Veröffentlichung wäre ein eigener Auftrag.

Monitoring ergänzt `-f deployment/monitoring.compose.yaml --profile
private-monitoring`: zusätzlich `PROMETHEUS_DIGEST`, `GRAFANA_DIGEST`,
`C22_PROMETHEUS_CONFIG`, `C22_METRICS_TOKEN`, `C22_PROMETHEUS_DATA`,
`C22_GRAFANA_PASSWORD`, `C22_GRAFANA_DATA`. Alle Bindquellen bestehen vorher.
Die kopierte `deployment/prometheus.yaml` muss an beiden markierten Stellen den
echten API-DNS-Namen enthalten. Dashboard-/Rule-Mounts referenzieren die bestehenden
C15-Dateien. Es gibt keinen Alertmanager oder Host-Exporter in diesem Profil;
Alarmrouting und Datenträgerbeobachtung müssen separat abgenommen werden.

## C26-B – bestehende Coolify-UI

Der [HTTPS-Nachtrag](https.md) führt die neuen parametrisierbaren UI-/OIDC-/Proxy-
Verträge und den UI-only-Rollout aus. Dafür nicht das vollständige C22-Profil
aktivieren; bestehendes Backend und Executor bleiben unverändert.
