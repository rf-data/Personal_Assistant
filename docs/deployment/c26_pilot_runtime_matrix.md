# C26-PILOT-INTEGRATION – implementiertes Runtimeprofil

27.10.2026. **Nur Offline-Review, kein ausrollbarer Releasegrant.** Die folgende
Matrix ersetzt für den Kandidaten die darunter bewahrten früheren Sollangaben.

| Artefakt | Effektive Rolle | Nachweis / Grenze |
| --- | --- | --- |
| `deployment/c26-pilot.compose.yaml` | Bestehende Backendressource: api-gateway, api, ein capacity-worker | Dediziertes begrenztes C22-Profil; nicht mit compose.yaml, H-Staging oder Batchstack kombinieren |
| Profil `c26-pilot-control` | Nur API/Gateway | Worker bleibt bei execution false gestoppt; ohne Profil keine Dienste |
| Profil `c26-pilot-worker` | Genau ein vorhandener CapacityExecutor | Eigene spätere Aktivierung; Gate, Queue und execution müssen gültig sein |
| `deployment/c26-pilot.controller.json.example` | V2-Pflicht, execution und alle Fachopt-ins false | max_jobs/queued/parallel=1, leerer Katalog und leere Identitäten; Bootstrapvorlage, keine Runtimeauth |
| `deployment/c26-pilot.limits.json.example` | 2 GiB freie Reserve, 128 MiB Jobbaum, 1 MiB Katalogbudget, 8 MiB Reports | Der CapacityExecutor prüft jetzt auch die Summe der tatsächlich hashverifizierten Katalogbytes vor seiner Initialisierung. Capacityprüfungen sind keine Datenträgerquota. Echter 128-MiB-Quota-/Speicherabnahmebeleg bleibt Pflicht |
| `deployment/c26-pilot.ui.compose.yaml` | Vorhandene UIressource, Overlay über coolify.ui + private-https | restart no, pull never, CPU 0,50, RAM/Swap 768 MiB; separates Profil c26-pilot-ui |
| `scripts.c26_pilot_preflight` | Read-only-Prüfer des gerenderten Backendbootstrapvertrags | Keine Stores/Host-/DNS-/Secret-/Runtimeabfragen, kein Permit, begrenzter strikter JSONloader |
| G-/H-Vorlagen und Prüfer | Erhaltene zusätzliche Content-/Review-/Searchintegration | Im kleinen Erstpilot nicht auswählen; kein zweiter Stack |

## Tatsächliche Budgets und Mounts

| Rolle | CPU | RAM / RAM+Swap | PIDs | tmpfs |
| --- | --- | --- | --- | --- |
| api-gateway | 0,10 | 256 / 256 MiB | 64 | 32 MiB |
| api | 0,25 | 512 / 512 MiB | 64 | 32 MiB |
| capacity-worker | 1,00 | 1024 / 1024 MiB | 128 | 64 MiB |
| separate UI | 0,50 | 768 / 768 MiB | 128 | 64 MiB |

Alle: UID/GID10001, read-only rootfs, ALL capabilities entfernt,
no-new-privileges, keine Hostports, kein Socket/privileged/hostnetwork,
SIGTERM, Stopfrist 30s, restart no, begrenzte json-file-Logs. API nur Loopback
im Gatewaynamespace, Gateway ausschließlich genehmigtes extern bereitgestelltes
internes API-Netz, Worker `network_mode: none`. Die UI nutzt die bisherigen
Ingress-/Backendnetze; tatsächliche Egresskontrolle bleibt Betreiberpflicht.

API und Worker teilen exakt denselben neuen `C26_PILOT_ROOT` nach
`/var/lib/personal-assistant/private` rw und denselben `C26_PILOT_CATALOG` nach
`/var/lib/personal-assistant/catalog` ro. `C26_PILOT_CONFIG` wird identisch nach
`/run/config/controller.json` ro gebunden. Nur Worker erhält zusätzlich
`C26_PILOT_LIMITS` nach `/run/config/limits.json` ro. Gateway: vorhandene
C26_CADDYFILE und C26_TLS_DIRECTORY ro. Alle Quellen absolut, getrennt,
vorhanden, `create_host_path=false`; keine Legacy-/Produktionsmounts adoptieren.
Root/Verzeichnisse 0700 und Config/Key/Tokenfiles 0600, jeweils UID10001.
Quotas, Kernelmountidentitäten und effektive UID werden nicht durch YAML bewiesen.

Zusätzliche Variablen: C26_RUNTIME_IMAGE/C26_GATEWAY_IMAGE als genehmigte
Registrydigests; C26_API_DNS passend zum privaten Zertifikats-SAN;
C26_PRIVATE_API_NETWORK als inventarisiertes dediziertes Netz. Die UIvariablen
bleiben vollständig in der [Sicherheitsmatrix](c26_pilot_security_acceptance.md).
Keine Werte, Pfade, Issuer oder Identitäten werden automatisch erfunden.

## Festgestellte und korrigierte Integrationsfehler

Zusätzlich zum unveränderten Job-/Artefaktmetadatenvertrag kann die vorhandene
C16-Application nun `GET /v1/jobs/{job_id}/result` für bestätigte Materialpläne
liefern. Die Route ist individuell authentifiziert, Course-begrenzt, read-only,
hash-/größengeprüft (256 KiB), ohne frei wählbare Dateipfade. Details und offene
UI-Anzeige: [APIvertrag](../job_control/api.md).

YAML-Flowlisten wie `tmpfs: [/tmp:rw,noexec,...]` wurden als mehrere Einträge
geparst. Die betroffenen C22-/Bootstrap-/UI-/Monitoring-/Pilotvorlagen verwenden
nun genau einen quotierten Mountstring. Native Composeausgabe und zusätzliche
Regression sichern die Optionen einschließlich Größenlimit. Außerdem fehlte
für das bereits im Runtime-Dockerfile kopierte `scripts/c26_runtime_preflight.py`
die Dockerignore-Ausnahme; sie ist ergänzt. Keine Images gebaut oder geladen.

APIhealth (401 für ungültige Auth) und Gatewayhealth bleiben Liveness-/Transport-
nachweise. UI `ready` prüft individuelle authentifizierte Capabilities.
Workerheartbeat beweist weder Idle noch Kindprozessfreiheit. Gate-/Scope-/
Witnessevidence ist separat erforderlich; es wurde kein /ready erfunden.

---

## Historische Runtimebewertung des Betreiberpakets 1f53289

# C26-PILOT – Runtime- und Konfigurationsmatrix

Status: **Zielkonfiguration zur Review, nicht ausrollen.** Siehe
[Lücken P01–P09](c26_pilot_gap_analysis.md) und [Betreiberschritte](c26_pilot_operator_checks.md).

## Bestehende Artefakte und vorgesehene Rollen

| Artefakt | Rolle / Einstieg | Eignung und Grenze |
| --- | --- | --- |
| `docker/DockerFile.worker` | Legacy-Coolifyworker; `CMD sleep infinity` | Bestehenden Verwaltungszustand erhalten; root, breites lecture-worker-Extra, ungepinnte Basis; kein Pilotruntimeimage |
| `deployment/Dockerfile` | Schmale C22-Runtime; `python -m scripts.deployment` | Gepinnte Basisargumente, eigener Lock, UID 10001; API/Worker per Argument; kein impliziter APIstart |
| `deployment/runtime/{pyproject.toml,uv.lock}` | Reproduzierbare schmale Laufzeitclosure | `uv sync --frozen --no-dev --no-install-project`; endgültige Basis- und Ergebnisdigests fehlen |
| `deployment/gateway.Dockerfile`, `Caddyfile` | Privates C22-TLS-Gateway auf 8443 → API 127.0.0.1:8016 | Bestehende Architektur wiederverwenden; keine neue Public-API |
| `deployment/compose.yaml`, Profil `private-production` | C22-Referenz: Gateway/API/Executor/UI | Kein fertiger Ersatz der vorhandenen zwei Ressourcen; Start würde auch UI duplizieren; nicht unverändert starten |
| `deployment/coolify.ui.compose.yaml` + `coolify.private-https.yaml` | Ersatz ausschließlich vorhandener UI-Ressource | Bestehendes dediziertes Overlay, keine Backendrollen; tatsächliche Routersuffixe/Middlewarebindung inventarisieren |
| UI `docker/DockerFile.UI` | `python -m admin_ui_package.container_runtime` → `app_admin.py` | UID 10001, festes Auth-/HTTPSstartgate, Dockerhealthcheck |
| UI `docker/docker-compose.ui.yaml` | Allgemeine UIbuildvorlage | Auth/Backend default disabled; kein abgesichertes Pilotprofil |
| `deployment/cs50-worker.compose.yaml` | `processing`/`tools`/`download`; `scripts.cs50_worker` | Separater Batch-/Materialpfad; im Erstpilot nicht aktivieren, kein zweiter Executor und kein Downloadprofil |
| `api/Dockerfile` | Legacy-APIartefakt | Kein nachgewiesener C16/C22-Ersatz; für Pilot nicht auswählen |

Buildkontext bei Backend und UI ist jeweils die Repositorywurzel. Backendbuild
verwendet `deployment/Dockerfile`, Gateway `deployment/gateway.Dockerfile`, UI
`docker/DockerFile.UI`. Schmale Dockerignore-Dateien gehören zum Review. Niemals
eine reale Secretsdatei oder die bestehende produktive Konfiguration in den
Buildkontext kopieren. Basisimageparameter `PYTHON_IMAGE`, `UV_IMAGE` und für das
Gateway `CADDY_IMAGE` müssen
freigegebene `@sha256:`-Referenzen sein. Kein `latest`, keine Runtimeinstallation.
Für jeden Ergebnisdigest unabhängiger Receipt: Repo, SHA, Lockhash,
Dockerfilehash, Basisdigests, Plattform und tatsächlich gezogener Registrydigest.

## Sollbudgets des ersten Piloten

Diese Werte sind **noch kein vorhandenes gerendertes Composeoverlay** (P04).
Keine YAML mit behaupteter Serverfreigabe erzeugt. Bestehende C22-Vorlagen sind
teilweise höher dimensioniert und haben `restart: unless-stopped`.

| Rolle | CPU | RAM / Swap gesamt | PIDs | tmpfs | Netz / Einstieg |
| --- | --- | --- | --- | --- | --- |
| Gateway | 0,10 | 256 / 256 MiB | 64 | 32 MiB | Dediziertes internal-Netz; 8443 ausschließlich intern |
| API | 0,25 | 512 / 512 MiB | 64 | 32 MiB | `network_mode: service:api-gateway`; `api --config /run/config/controller.json` |
| Executor | 1,00 | 1024 / 1024 MiB | 128 | 64 MiB | `network_mode: none`; `worker --config /run/config/controller.json` |
| UI | 0,50 | 768 / 768 MiB | 128 | 64 MiB | Dediziertes Ingress-/Backendnetz, nur expose 8501; fester UIlauncher |

Summe 1,85 CPU / 2560 MiB; die verbleibende Hostkapazität ist für Coolify,
Traefik und OS noch real zu messen. Swap ist kein zusätzliches Jobbudget.
Tmpfsverbrauch zählt zum Cgroup-RAM; Job-Adressraumlimit ist davon verschieden.
Wenn diese Budgets in Start-/Fehlertests nicht genügen, HOLD statt stiller Erhöhung.
Für alle Rollen: UID/GID `10001:10001`, read-only rootfs, `cap_drop: ALL`,
`no-new-privileges:true`, kein Dockersocket/privileged/hostnetwork,
Stopgrace 30 s, `restart: 'no'` für diesen Pilot, begrenzte json-file-Logs
10 MiB × 3. Wiederanlauf manuell nach geklärtem Zustand; Healthfehler autorisiert
keinen automatischen Containerwechsel. Separat prüfen, dass Coolify keine
zusätzliche Restart-/Health-Recoveryautomation erzwingt.

## Mounts und Rechte

| Rolle | Ziel | Mode / Zweck |
| --- | --- | --- |
| API + Executor | `/var/lib/personal-assistant/private` | Identischer neuer lokaler Pilotroot, rw; 0700, UID 10001; gleiche SQLite/WAL/flock-Sicht |
| API + Executor | `/var/lib/personal-assistant/catalog` | Neuer synthetischer Katalog ro; 0700-Verzeichnisse, 0600-Dateien, UID 10001, Hashliste |
| API + Executor | `/run/config/controller.json` | ro, 0600 UID 10001; individuelles Token nur als Hash im Backend |
| Gateway | `/run/tls` und `/etc/caddy/Caddyfile` | ro; privater Key 0600 UID 10001; SAN zur bestätigten privaten API-DNSidentität |
| UI | `/run/secrets/c16` | ro, individuelle Tokendatei 0600 UID 10001; keine gemeinsame Administratorkennung |
| UI | `/home/adminui/.streamlit/secrets.toml` | ro, 0600 UID 10001, OIDC-/Cookieschlüssel; nie in Git/Build/Logs |
| UI | `/run/ca/ca.crt` | ro, bestätigtes CA-Bundle für private API **und** erforderliche öffentliche IdP-CAketten |

Alle Hostquellen müssen bereits existieren; `bind.create_host_path: false`.
Kein rekursives `chown`/`chmod` des Altbestands. Die bestehenden Workerziele
`/app/.cache` oder `/app/cache`, `/app/configuration`, `/app/data`, `/app/logs`
und UI `/data`, `/logs` werden nur inventarisiert, nicht als Pilotroot adoptiert.
Ausgaben unter `/app` benötigen zusätzlich die vorhandene explizite
`PA_PERSISTENT_ROOTS_FILE`-Mountpolicy; der neue externe C22-Root vermeidet eine
implizite Ausnahme, verlangt trotzdem Ownership-/Volumeabnahme.

Eine Container-mem_limit begrenzt **keinen persistenten Datenträger**.
128-MiB-Pilotquota sowie mindestens 2 GiB freie Rootreserve vor Start und
unabhängige Diskbeobachtung sind zusätzliche Freigabebedingungen. Quota ohne
geprüftes Rückverfahren nicht am bestehenden Storage aktivieren. Quota und
fsync/WAL/flock werden zunächst nur auf neuem synthetischem Ziel geprüft.

## Controllerzustand

Vorbereitung: `execution_enabled=false`, `workflows_enabled=false`,
`pdf_enabled=false`, `index_jobs_enabled=false`, `import_jobs_enabled=false`,
`max_parallel=1`, `max_queued=1`, `max_jobs=1`, `worker_ttl=10`.
**Startvertragsgrenze:** `Executor.__init__` verweigert einen Start bei
`execution_enabled=false`. Deshalb in C05 zunächst nur API/Gateway starten,
den Executor lediglich konfigurieren und ausdrücklich gestoppt halten. Kein
Workerhealth-PASS in dieser Stufe erwarten. Das noch fehlende Coolifyoverlay
muss diese gestufte Aktivierung ausdrücklich unterstützen; unverändertes
C22-Gesamtcompose würde den deaktivierten Executor erfolglos starten.
Erst C08 setzt execution true und startet genau einen Executor unter weiterhin
geschlossenem integriertem Admissiongate. Workerhealth/Idle, alle Rollen und
authentifizierte UIreadiness **vor** dem separaten Resumegrant prüfen. Ein
verschiedenes API-/Worker-Settingsfile als improvisierten Ersatz nicht verwenden.
Ein genehmigter Operator, nur `cs50_python`; ein `manifest`-Eintrag, siehe Scope.
Keine unvorhandenen Gateflags in master einschreiben: `extra=forbid` lehnt sie ab.
Nach technischer Gateintegration muss **jeder** API-/Worker-/CLIwriter dieselbe
verpflichtende Policy, denselben Root und denselben vollständigen Scope verwenden.
Keine Downgrade-/v1-Fallbackroute; Testkoordinatorflags sind keine Livefreigabe.

## Health, Readiness und Beendigung

| Prüfung | Exakter vorhandener Einstieg | Aussage / Grenze |
| --- | --- | --- |
| APIhealth | `python -m scripts.deployment health --role api --config /run/config/controller.json` | DBprüfung + 401 auf ungültigen Bearer an `/v1/processes`; **keine** authentifizierte Readiness |
| Workerhealth | `python -m scripts.deployment health --role worker --config /run/config/controller.json` | Frischer DBheartbeat; kein Beweis für Idle/Drain/Kindprozessende |
| Gatewayhealth | `python /opt/gateway_health.py` | CA/SAN-validiertes TLS, erwartete 401; keine erfolgreiche Operatorauth |
| UIhealth | `python -m admin_ui_package.container_runtime health` | Loopback-Streamlit-Liveness, keine Backendfreigabe |
| UIreadiness | `python -m admin_ui_package.container_runtime ready` | Liveness + individuelle C16-capabilities über verifiziertes HTTPS |
| Deploymentreadiness | Aktuell kein produktiver Einstieg vorhanden | Benötigt zusätzlich Version/Instanz/Scope, alle Rollen, Queue/Guardian, Trigger und freigegebene Images |

Vorlagenhealthchecks: 15-s-Intervall, 5-s-Timeout, 3 Versuche, 30-s-Startfrist.
Startup mit fehlendem Configroot/CA/Token/IdP verweigern; fehlender Pflichtinput
ist HOLD. Kein erfundener `/ready`-Endpunkt. Health darf weder Queue initialisieren
noch Heartbeats schreiben. UI-Backendfehler dürfen keine Restartschleife erzeugen.

Cancel über bestehende Jobaktion; Ownerbindung serverseitig, wiederholter Cancel
idempotent. Erst bestätigtes Guardian-/Prozessende erlaubt den terminalen Status.
SIGTERM schließt den managed Executor; nach hartem Verlust gelten Interrupted/
Quarantäne und explizite Untersuchung. Kein SQLite-/Journal-/Locklöschen,
automatischer Retry oder automatischer Resume. `sleep infinity` bleibt auf Hetzner
bis einer später ausdrücklich genehmigten, rückwegfähigen Umstellung unverändert.

## C26-INT-02-Nachtrag

Der Planlesevertrag liefert bei vorhandener oder während der Lesung entstehender
Workspacequarantäne 423 / `quarantined`, nach Auth-/Courseprüfung. Neue private
Jobdiagnosen heißen `adapter-failure.v1.json` und `guardian-failure.v1.json`;
sie enthalten feste Kategorien, numerischen SQLitecode und Transaktionsphase.
Sie sind kein Erfolgs-/Cleanupbeweis und berechtigen zu keinem Retry/Resume.
Originalmarker und alte Publikationsreste werden niemals automatisch entfernt.

Die von `storage.publish_bytes` gespeicherten Plan-/Receipt-/JSON-Dateien werden
auf Linux mit atomarem No-replace-Rename veröffentlicht.
Der Zielkernel und das tatsächliche Volume müssen diese Operation unterstützen;
fehlende Unterstützung bleibt ein Fehler. Der neue Quellenfix macht keine
historischen nlink=2-Dateien zu vertrauenswürdigen Einzeldateien. Sicherheits-
prüfungen und Backup-/Restoregrenzen bleiben bestehen; C26-04 bleibt DEFERRED.

Die UI-Anzeige liegt als separat anwendbarer Patch vor. Sie wurde nur auf einer
Testfixture geprüft, nicht im tatsächlichen UI-Repository angewendet oder getestet.
[Alle neuen Nachweise und offenen Punkte](c26_int_02_validation.md).
