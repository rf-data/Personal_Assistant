> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-G – Betreiber-Runbook für einen späteren Hetzner/Coolify-Versuch

25.10.2026. **Produktionsstatus HOLD. Kein Schritt dieses Runbooks erteilt eine
Freigabe.** Codex hat keine Serverbefehle ausgeführt. Zunächst getrenntes,
ausdrücklich genehmigtes Staging mit synthetischen Daten; produktiver Versuch erst
nach [Gate-Matrix](c26g_readiness_matrix.md) und manuellem
[Go/No-Go](c26g_go_no_go.md). Bestehende C26-/C27-Branches/PRs bleiben unverändert.

## Befehlslegende und Ausführungsgrenze

Jeder Codeblock trägt eine Klassifizierung. Sie gilt für alle darin enthaltenen
Befehle, einschließlich Pythoncode und Variablenzuweisungen:

- **R – read-only:** liest nur. Host-/API-/IdP-/Registrykontakte trotzdem erst
  mit eigenem späteren Zugriffsmandat; in diesem Auftrag verboten.
- **L – lokal/synthetisch:** schreibt ausschließlich in neue lokale Testziele,
  exportiert Gitquellen oder verarbeitet Fakewerte. Kein Produktivmount/-secret.
- **P – produktiv zustandsändernd:** hier ausschließlich dokumentiert,
  **nicht ausgeführt**. Erfordert spätere aktions-/ressourcengenaue Freigabe und
  alle passenden Gates. Container-`exec` wird konservativ als P klassifiziert,
  auch wenn das gestartete Healthprogramm nur liest.

Die unten verwendeten privaten Env-/Configpfade sind Platzhalter für bereits
genehmigte Dateien. Keine Datei einfach `source`n, kein `set -x`, kein
`docker inspect` ohne Feldfilter, keine Ausgabe von `env`, `secrets.toml`,
Authorization, Cookies, privaten Schlüsseln oder vollständigem Compose-JSON.
Keine Datei/-DB/-Queue automatisch anlegen, wenn ein erwarteter Mount fehlt.

## 1. Mandat, Inventur und Versionen sichern

Verantwortlichen Operator, Stellvertretung, Zeitfenster, Abbruchkriterien,
Rettungszugang, betroffene Rollen und genaue Release-/Rollback-SHAs und Digests
festlegen. D09/D10/D11 sowie reale Datenrechte dokumentieren. Private Zuordnung
der Coolify-Ressourcen, Server/Environment, aktuellen Container, Netze, Queues,
Mounts, Writer und Trigger erstellen. Auto-/Preview-/Git-/Registry-/Webhook-/API-/
Schedulerpfade, Deploykonten und wartende Deployments vollständig erfassen.
„Manual only“ allein reicht nicht. Bei unbekanntem Writer/Trigger **abbrechen**.

**R – lokaler Gitvergleich; keine Netzwerkabfrage:**

```sh
git status --short --branch
git rev-parse HEAD master origin/master
git worktree list --porcelain
git for-each-ref --format='%(refname:short) %(objectname)' refs/heads refs/remotes/origin
```

Live-GitHubheads/Reviews/Checks später mit freigegebenem Readzugriff abgleichen.
Nicht aus veralteten lokalen Trackingrefs auf Integration schließen. Der spätere
Merge-/Pushtrigger muss vor jeder Repositoryintegration geklärt sein. D/E/F erben
ihre Vorgängerserien: nicht mehrfach vollständig integrieren. Diesen Auftrag
nicht zum Merge nutzen.

**R – ausschließlich später auf dem genehmigten Zielhost, pro bekannter ID:**

```sh
df -h
df -i
docker container ls --format '{{.ID}} {{.Status}}'
docker container inspect --format '{{.Id}} {{.Image}} {{.State.Running}} {{.RestartCount}}' "$C26_CONTAINER_ID"
docker container inspect --format '{{range .Mounts}}{{.Type}} {{.RW}}{{println}}{{end}}' "$C26_CONTAINER_ID"
docker container inspect --format '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}}' "$C26_CONTAINER_ID"
docker image inspect --format '{{.Id}} {{json .RepoDigests}}' "$C26_APPROVED_IMAGE"
```

Nur redigierte Aliase und Status weitergeben. Root-/Mountquellen privat exakt
zuordnen; diese verkürzten Ausgaben beweisen keine korrekte Rollenbindung.
Historische Ports 8000/6001/6002 und alle direkten UI-/APIports inklusive IPv6
gezielt prüfen; keine bestehenden Dienste ungeprüft abschalten.

## 2. Offlineprüfung und unveränderliche Buildbasis

Vorhandene dokumentierte Testumgebung verwenden; keine stillen Downloads,
Packageupdates oder automatischen Modell-/Imagepulls. Der neue Runner exportiert
die gepinnten G- und F-Quellen nach `/tmp`, wendet den kumulativen Draftdiff nur
dort an und startet Tests mit Netzwerk-/Infrastrukturguard. Er schreibt keine
Gitrefs/-indizes und kein Worktree. Ergebnisse/Datentempwurzeln bleiben erhalten.

**L – im zugewiesenen Backendworktree, nur synthetisch:**

```sh
C26G_TEST_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python
PYTHONDONTWRITEBYTECODE=1 "$C26G_TEST_PYTHON" -B scripts/c26g_offline_validation.py
```

Für einen kurzen Konfigurations-/Verbundrestorelauf denselben Runner mit
`--configuration-only` verwenden (L). Exakte Basis und Grenzen stehen in
[Validierung](c26g_integration_validation.md). Fehler oder Skips nicht als bestanden
zählen. Die historische MAINT-Prozessfehleranalyse bleibt ein eigenes Gate.

Vor späterem Build D09 genehmigen: Python-/uv-/Caddybasis mit vollständigem
RepoDigest, Plattform, Frozen-Locks, Wheelverfügbarkeit, konkreter Backend-/UI-SHA
und unabhängigem Buildreceipt. Image-ID ist kein Registry-RepoDigest. Ein
`--pull=false` verhindert nicht jeden Download fehlender Basisimages/Wheels.
Images erst in genehmigter isolierter Buildumgebung erzeugen und testen; keine
Images in diesem Auftrag gebaut. Altes FastAPI- oder `sleep infinity`-Workerimage
nicht als C16-Rollenimage behandeln.

## 3. Konfiguration vorbereiten und Verträge paaren

Nur den später regulär integrierten/geprüften Dreirollenbootstrap verwenden:
`deployment/coolify.runtime-bootstrap.compose.yaml` aus D/E/F und **separat**
UI `deployment/coolify.ui.compose.yaml` plus `coolify.private-https.yaml`.
Nicht mit C22-`compose.yaml` oder `cs50-worker.compose.yaml` kombinieren.
Keine zweite aktive Queue/Workerressource als Ausweichroute.

| Bereich | Vorzubereitende private Angaben |
| --- | --- |
| Runtime | `C26_RUNTIME_IMAGE`, `C26_GATEWAY_IMAGE`, drei Rollen, aktuelle/Target-Revisionen, Commands/Health/Limits, UUID/Server/Environment |
| Mounts | `C26_HOST_RUNTIME/DATA/CONFIGURATION/LOGS/CACHE`, `C26_CADDYFILE`, `C26_TLS_DIRECTORY`, exakt gleicher Jobroot für API/Worker, Root-/Device-/Inodepolicy |
| Netzwerk | `C26_PRIVATE_API_NETWORK` = UI `C26_BACKEND_NETWORK`; getrenntes `C26_INGRESS_NETWORK`, kein öffentlicher APIport |
| TLS/Origin | `C26_API_DNS` = Alias/SAN/API-Hostname; APIport8443, Caddy→Loopback8016; kanonischer `C26_UI_ORIGIN`, echte Proxy-CIDRs und VPN-RemoteAddr-Allowlist |
| UI/Identity | `C26_UI_IMAGE`, `ADMIN_OIDC_ISSUER`, Subjects/Sessionalter, individuelle `JOB_API_IDENTITIES`, `C26_UI_TOKENS/OIDC/API_CA`, genaue Callback-URI |
| Fachruntime | Explizite Content-/Review-/Search-/Index-/Keyroots; bislang kein verwaltetes Containerlauncherwiring, deshalb **blockiert** |
| Betrieb | Monitoring-/Alarmrouting und jeweilige eigenen Netz-/Identitäts-/Persistenzbindungen; C22-Monitoringprofil passt nicht unverändert zum C26-Netznamen |

Die neue `c26g.staging.controller.json.example` ist eine deaktivierte v2-Vorlage:
Root `/app/runtime-state/c16`, alle Ausführungsflags false, leere Identitäten und
Kataloge, Limits1. Keine echte UI-Nutzung damit behaupten: vorhandene OIDC-Subjects
ohne freigegebene Backendidentitäten müssen scheitern. Die alte Draftcontrollervorlage
wählt noch v1. Nicht das F-Testprofil als produktiven Ersatz aktivieren.

Nach Vorliegen vollständiger **gerenderter**, privat gespeicherter Compose-JSONs
prüfen. Coolify-generierte Router-/Middlewarelabels müssen enthalten sein;
fehlende Labels nicht mit erfundenen Werten auffüllen.

**R – lokale/private Offlineprüfung, keine Verbindung/Queueöffnung:**

```sh
python -B -m scripts.c26g_preflight \
  --backend-compose-json /private/c26/backend-rendered.json \
  --ui-compose-json /private/c26/ui-rendered.json \
  --controller /private/c26/controller.json \
  --origin "$C26_UI_ORIGIN" --tls-router "$C26_TLS_ROUTER" \
  --http-router "$C26_HTTP_ROUTER" --middleware "$C26_PRIVATE_MIDDLEWARE"
```

Exit0 bedeutet nur `offline_configuration_valid`, weiterhin HOLD und
`deployment_permitted=false`. Die G-Basis ohne D verweigert die v2-Konfiguration
korrekt. Dies prüft deklarierte Teilverträge, keine Zertifikatdatei, echte
Dateirechte, vollständige Compose-Semantik, laufenden Dienste oder Trustwahrheit.
Die Fachaktivierung passt absichtlich nicht in diesen deaktivierten Stagingcheck.

## 4. Secrets und Mounts bereitstellen

**P – ausschließlich nach eigener D10-Freigabe, hier nicht ausgeführt:**
Der Betreiber stellt individuelle Tokenfiles, OIDC-Client-/Cookie-Secret,
TLS-Schlüssel und Monitoringcredentials über seinen geprüften Secretkanal bereit.
Keine Klartexte in Shellargumenten/Env/Reports/Images/Git. Backend nur Tokenhashes;
UI liest pro individueller Rollenbindung aus 0600-Dateien. Eigentümer muss der
Dienst-UID10001 entsprechen; Verzeichnisse0700. CA-Bundle enthält öffentliche
Vertrauensanker für API **und** benötigte IdP-Zertifikate; privater Schlüssel nur
im Gateway. Keine pauschalen chmod/chown auf vorhandenen Daten.

Vorbereitete Binds müssen existieren (`create_host_path:false`). Mountpolicy aus
dem **Zielcontainernamespace** erheben, nicht vom Host raten. Runtime-Lockpfad
`/app/runtime` nicht übermounten. Lokales Linuxdateisystem, kein NFS/SMB/repliziertes
Volume. Secretbackup separat verschlüsseln und Recoveryzugang benennen.

**R – später im genehmigten Runtime-UID-/Mountkontext, kein Store/Gatebootstrap:**

```sh
python -B -m scripts.c26_runtime_preflight \
  --config /app/configuration/c26-runtime/controller.json \
  --limits /app/configuration/c26-runtime/limits.json \
  --runtime-mount /app/runtime-state \
  --runtime-image "$C26_RUNTIME_IMAGE" --gateway-image "$C26_GATEWAY_IMAGE"
python -B -m scripts.deployment check --config /app/configuration/c26-runtime/controller.json
```

Die erste Prüfung meldet vorhandene Queue nur `present_unverified`, nie gesund.
Reserve plus volle Bootstrapbudgets: 6.123.683.840 Bytes, zusätzlich Images,
Backup-/Restorebedarf und sonstige Daten einplanen. Genug Disk ist keine Quota.

**P – schreibt eine temporäre Probe im genehmigten Zielvolume, hier nicht ausgeführt:**

```sh
python -B -m scripts.deployment probe --config /app/configuration/c26-runtime/controller.json
```

Probe prüft rename/fsync/flock/WAL und entfernt nur ihren eigenen Probeunterordner.
Ein echter Mount-/Crash-/Stromausfallnachweis ist zusätzlich erforderlich.

## 5. Vor jeder Änderung sichern

**P – organisatorisch und technisch zustandsändernd, erst später freigeben:**
Ingressannahmen/Trigger schließen; UI und Annahmepfade sperren, Gatehold setzen,
bekannte Arbeit kontrolliert drainen. Alle Writer einschließlich Legacy-/Pilot-/
Importprozessen müssen beendet sein. Created/queued Jobs bewusst abwickeln oder
mit individueller bestätigter APIaktion abbrechen. Kein blindes Statusupdate in SQL.
API/Worker geordnet stoppen; Workerheartbeat0 und terminale Jobs bestätigen.
Fehlender Heartbeat allein ist kein Beweis, dass alle Prozesse beendet sind.

**P – C22-Jobbackup in neuen privaten Zielpfad, hier nicht ausgeführt:**

```sh
python -B -m scripts.deployment backup \
  --config /private/c26/controller.json --output /private/backups/NEW-job-snapshot
```

Der C22-Shared-/Exclusive-Wartungslock schützt nur kooperierende Launcher. Keine
lebende SQLite-Datei per rsync/cp sichern, `backup_hetzner.sh` nicht verwenden.
C22-Grenzen20.000Dateien/2GiB/Baum und8MiB-Manifest prüfen. Hardlinks/Symlinks/
Spezialdateien oder Quarantäneprobleme nicht umgehen. Unvollständiger Snapshot
ohne letztes Manifest ist kein Backup.

ContentStore separat mit bestehender `src.content_store.backup.backup` sichern:
SQLite-Backup-API plus Raw-/Parsed-/Receiptblobs, ACL/Publikationsstand und
Incident-/Stagingzustände. EvaluationStore ist **nicht automatisch Teil** davon
oder des C22-Bundles. Für ihn fehlt ein produktiver Verbundadapter. Der neue Test
demonstriert SQLitebackup unter dem bestehenden Reviewlock und vollständige
Schema-/Ledger-/Headprüfung; daraus entsteht kein freigegebenes Produktionstool.

**Sperrpunkt G18:** Vor produktivem Wechsel einen reviewten Adapter für den
gesamten gestoppten Verbund bereitstellen und auf Staging abnehmen. Gemeinsamer
Checkpoint muss Job-/Workflowreferenzen, Contentversionen/ACLs und Review-/Gold-/
Reportreferenzen sowie Konfiguration/Indexgeneration erfassen. Index ist
rekonstruierbar, Content/Reviews/Jobs sind es nicht. Verschlüsselte Offsitekopie,
Hashmanifest und Wiederherstellungszeit prüfen. Keine automatische Retentionlöschung.

## 6. Isolierte Wiederherstellung vor dem Start testen

**L – ausführbare lokale Probe ohne echte Daten oder Credentials:**

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$C26G_TEST_PYTHON" -B -m pytest -q -o addopts= -p no:cacheprovider \
  -p tests.offline_guard tests/test_c26g_restore.py \
  tests/test_content_store_backup.py tests/test_deployment_operations.py \
  -m 'not external_integration' --basetemp=/tmp/NEW-c26g-restore-probe
```

**P – spätere echte Jobwiederherstellung, schreibt ausschließlich in neuen,
genehmigten isolierten Root; hier nicht ausgeführt:**

```sh
python -B -m scripts.deployment restore \
  --snapshot /private/backups/APPROVED-job-snapshot \
  --output /private/restore/NEW-jobroot
```

Danach zwingend:

1. Manifestbestand, Hashes, Datenbankversion/quick_check und alle Job-/Workflow-/
   Receiptreferenzen prüfen. `activated:false` verlangen; kein Prozessstart.
2. Content-Snapshot mittels bestehender `src.content_store.backup.restore`
   unter **geprüfter berechtigter Betreiberidentität** in einen anderen neuen
   Root restaurieren. Diese API validiert Manifest, DB und unveränderliche Blobs;
   es existiert kein allgemeiner `scripts.content_store`-CLIbefehl. Vor produktiver
   Verwendung muss der in Schritt5 geforderte Adapter diesen Aufruf kapseln.
3. Evaluation-DB über den abgenommenen Adapter in neuen privaten Reviewroot
   restaurieren. Snapshotdigest vor Kopie, vollständige `EvaluationStore`-
   Schema-/Events-/Headprüfung nach Kopie. Bestehenden Root nicht initialisieren
   oder überschreiben. Gleichnamige fremde DB und unvollständige Ledger ablehnen.
4. Raw-/Parsedversionen, ACLrevisionen, Reviewzustände/Gold/Reports, Idempotenz
   und Job-/Workflowartefakte gemeinsam prüfen; falsche/replayed Receipts und
   manipulierte Blobs müssen vor Aktivierung scheitern.
5. FTS5 bei Bedarf aus unverändertem Content neu bauen, neue Generation und
   Cursor-Key-/Invalidierungspolicy prüfen. Secrets getrennt wiederbereitstellen;
   private Konfiguration explizit auf Restore-Mounts binden. Keine automatische
   Pfadumschreibung historischer Katalog-/Originalreferenzen.
6. Quarantäne/interrupted/Journale erhalten. Gate nach Restore geschlossen.
   F-Enrollment bindet Device/Inode; Kopie darf alten Witness nicht wiederverwenden.
   Unabhängigen Witness nicht zusammen mit der Jobqueue zurückrollen. Neue
   Einschreibung/Recovery ist eigene Betreiber-/Trustentscheidung.
7. Original- und Restorewriter niemals gleichzeitig starten. RTO messen,
   Originaldaten unverändert lassen, Ergebnis redigiert festhalten.

## 7. Startfolge und Readiness

**Sperrpunkt G10–G15:** Derzeit gibt es keinen abgenommenen Livekoordinator/
Driver. Authentifizierte E-Captures sind keine D-Permits; F ist ausschließlich
Fixturecode. Kein Diagnose-/Preflight-/Healthbefehl kann diesen Sperrpunkt öffnen.
Kein erfundener `live`-Flag, kein direkter Coolify-APIcall als Ersatz.

Nach späterer Freigabe des exakten Livevertrags: alle Trigger geschlossen,
alte Rollen ohne Überlappung stoppen, genehmigten v2-Root geschlossen initialisieren,
Koordinator/Witness/Produzenten außerhalb des ersetzten Verbunds verfügbar halten.
Jede Mutation benötigt aktuellen Scope, separate Betreiberautorisierung und
einmaliges Claim. Folgende Kommandos beschreiben nur die begrenzten unterliegenden
Containeraktionen eines später abgenommenen Drivers, **keine heutigen Startbefehle**.

**P – gesperrte spätere Driveraktionen, hier nicht ausgeführt:**

```sh
docker compose --env-file /private/c26/runtime.env \
  -f deployment/coolify.runtime-bootstrap.compose.yaml --profile c26-runtime-approved \
  up -d --no-build --pull never api-gateway api
docker compose --env-file /private/c26/runtime.env \
  -f deployment/coolify.runtime-bootstrap.compose.yaml --profile c26-worker-approved \
  up -d --no-build --pull never capacity-worker
```

Gateway darf vor API kurz unhealthy sein; API hängt an `service_started`, nicht
Gatewayhealth. Bei Gatewayneuerstellung auch API neu erstellen, weil sie dessen
Netznamespace teilt. API-/Worker-PID-Namespaces bleiben getrennt. Kein weiterer
Executor. Zunächst nur freigegebenes deaktiviertes Healthprofil; der alte
Controller kann einen Workerstart absichtlich verweigern. Keine automatische
Initialisierung/Flagsänderung zur Behebung.

**P – späterer Containerexec für Health, hier nicht ausgeführt:**

```sh
docker exec "$C26_API_CONTAINER" python -B -m scripts.deployment health --role api --config /app/configuration/c26-runtime/controller.json
docker exec "$C26_WORKER_CONTAINER" python -B -m scripts.deployment health --role worker --config /app/configuration/c26-runtime/controller.json
docker exec "$C26_GATEWAY_CONTAINER" python /opt/gateway_health.py
```

API-/Gatewayhealth erwarten401 mit absichtlich ungültigem Bearer: Authgrenze/
Liveness, **keine** vollständige fachliche Readiness. Zusätzlich echte Queue,
Workerleases/Heartbeat, Root-/Scope-/Image-/Instanz-/Deploymentbindung und
Quarantänefreiheit prüfen. UI erst nach API-/Workerreadiness an die geprüften
Netze/Secrets koppeln; Ingress weiter privat und während Abnahme beschränkt.

**P – spätere UI-Driveraktion, hier nicht ausgeführt:**

```sh
docker compose --env-file /private/c26/ui.env \
  -f deployment/coolify.ui.compose.yaml -f deployment/coolify.private-https.yaml \
  up -d --no-build --pull never ui
```

## 8. HTTPS-, Auth- und fachliche Smokes

**R – spätere genehmigte Erreichbarkeitsproben, hier nicht ausgeführt:**

```sh
curl --silent --show-error --max-time 5 --cacert "$C26_PUBLIC_CA" \
  --output /dev/null --write-out '%{http_code}\n' "$C26_UI_ORIGIN/_stcore/health"
curl --silent --show-error --max-time 5 --cacert "$C26_API_CA" \
  --header 'Authorization: Bearer health-probe-invalid' \
  --output /dev/null --write-out '%{http_code}\n' "$C26_API_ORIGIN/v1/processes"
curl --silent --show-error --max-time 5 --config /private/c26/viewer-curl.conf \
  --output /dev/null --write-out '%{http_code}\n' "$C26_API_ORIGIN/v1/processes"
curl --silent --show-error --max-time 5 --config /private/c26/metrics-curl.conf \
  --output /dev/null --write-out '%{http_code}\n' "$C26_API_ORIGIN/v1/metrics"
```

Erwartung UI200 im zulässigen Netz, API ungültiger Bearer401, eigener gültiger
Viewer200, Metrics eigener scopespezifischer Viewer200. Curl-Konfigdateien sind
private0600-Dateien mit eigener CA/Auth; ihr Inhalt bleibt verborgen. Kein `-k`,
`--verbose` oder Headerdump. Health ohne IdP-Login beweist keine OIDCfunktion.

Im echten Browser zusätzlich Login/Logout/Callback/abgelaufene Session und
rollen-/quellenfremde Identität testen. Cookies Secure/HttpOnly/SameSite,
WebSocket mit exaktem Origin, fehlender/fremder/doppelter Origin und manipulierten
Forwarded-Headern prüfen. Außerhalb VPN UI/API/WSS/direct ports über IPv4/IPv6
müssen verweigern. Rotierte/widerrufene Identität muss tatsächlich unwirksam sein.

**P – fachliche Schreibsmokes, nur später auf ausdrücklich genehmigter
synthetischer Stagingqueue:** genau ein Preview→bestätigter Job→Ergebnis;
Viewerwrite verweigern; Cancel/Resume mit frischen Bestätigungen, identischen
Idempotenzschlüsseln und neuer Ausgabeversion prüfen. Keine echten Kursdownloads,
LLMs oder Originaldaten. Allgemeine Content-/Review-/Search-UI erst nach G15/G25
testen; gegen den heutigen verwalteten Launcher bleibt dieser Schritt blockiert.

## 9. Monitoring und Alarmzustellung

C15-Regeln/Dashboards wiederverwenden. Eigener Metrics-Viewer, richtige Kurse,
API-TLSprüfung, private Netze, begrenzte Logs und TSDBretention. Keine Subjects,
Job-IDs, PIDs, URLs oder Inhalte als Labels. Metriken/Logdateien ohne Secrets
prüfen; Loglevel nicht zur Diagnose auf unredigierte Requestdumps erhöhen.
Disk/Inodes, Backupalter/-fehler, Queue/Heartbeat/Quarantäne/Gatehold,
Zertifikatablauf sowie Ausfall der Überwachung selbst abdecken.

**L – nur falls geprüftes promtool lokal vorhanden, keine Zustellbehauptung:**

```sh
promtool test rules tests/fixtures/monitoring/rules.test.yaml
```

Das vorhandene Monitoringtemplate enthält **keinen** Alertmanager/Receiver.
Erst G21/D11-B umsetzen und Route/Empfänger privat bestätigen. Wenn die spätere
Entscheidung tatsächlich Alertmanager umfasst, ist folgendes ein möglicher
separat freizugebender Test; URL darf keine Credentials enthalten:

**P – sendet später einen echten Testalarm, hier nicht ausgeführt:**

```sh
amtool --alertmanager.url="$C26_PRIVATE_ALERTMANAGER" alert add \
  alertname=C26ReadinessProbe severity=warning c26_probe_id="$C26_ALARM_PROBE_ID"
```

Zeitpunkt/Probe-ID, Routingentscheidung, Empfängereingang, menschliche Bestätigung,
Zustelllatenz und anschließende Auflösung dokumentieren. Bei anderem Dienst
dessen genehmigtes Testverfahren verwenden, keinen fiktiven Endpoint erfinden.
Fehlende/verspätete Zustellung oder nicht erreichbarer Vertreter bedeutet NO-GO.

## 10. Stop, Restart, Fehler und Rollback

**P – erst später: Ingress/Trigger/Admission schließen, bekannte Arbeit drainen,
UI stoppen, API stoppen, Executor mit SIGTERM stoppen und Cleanup abwarten,
Gateway zuletzt. Hier nicht ausgeführt:**

```sh
docker compose --env-file /private/c26/ui.env -f deployment/coolify.ui.compose.yaml \
  -f deployment/coolify.private-https.yaml stop --timeout 30 ui
docker compose --env-file /private/c26/runtime.env -f deployment/coolify.runtime-bootstrap.compose.yaml stop --timeout 30 api
docker compose --env-file /private/c26/runtime.env -f deployment/coolify.runtime-bootstrap.compose.yaml stop --timeout 30 capacity-worker
docker compose --env-file /private/c26/runtime.env -f deployment/coolify.runtime-bootstrap.compose.yaml stop --timeout 30 api-gateway
```

Nicht `down -v`, `clean`, `prune`, DBreset, gespeicherte PIDs signalisieren oder
Quarantäne/Locks entfernen. Bei ungeklärtem Cleanup keinen zweiten Worker starten.
Draft `restart:no` startet nicht automatisch; C22 `unless-stopped` kann Prozesse
neu starten, **keine** automatische fachliche Wiederholung. Queued Jobs können
später normal dispatchen; interrupted Jobs verlangen neue bestätigte Aktion.

Rollbackreihenfolge:

1. **P, separat freizugeben:** Gate/Witness geschlossen halten, aktuelle Fehler-
   und Datenlage sichern, Scope/Claim/Receipt prüfen. Unklarer Seiteneffekt:
   kein Retry, kein automatischer Rollback/Resume, manueller Recoveryhold.
2. **R:** altes genehmigtes Image/Config/Schema gegen heutigen Datenstand und
   gesicherten Buildtyp prüfen. Kein alter Code auf unbekannt geändertem Schema.
3. **P, separat freizugeben:** bei Dateninkompatibilität erst Schritt6 in neue
   Roots durchführen; Originale erhalten. Bei kompatibler Datenlage nur geprüfte
   Image-/Configrückkehr. Keine pauschale Datenrücksetzung mit Verlust neuer Jobs.
4. **P, nur späterer Livekoordinator:** vollständige umgekehrte Operation mit
   frischem Rollbackgrant, einmaligem Permit und neuen Containerbelegen ausführen.
   Die unterliegenden Startaktionen stehen in Schritt7; ein operativer
   Live-Rollback-CLI existiert derzeit nicht. Daher bleibt dieser Pfad gesperrt.
5. **R/P entsprechend Schritt7–9:** Health, Instanz/Scope, Daten-/Idempotenz-/
   Alarmbelege wiederholen. Geprüfte Rückkehr bleibt held.
6. **P, getrennte neue Freigabe:** Resume erst nach neuer Session/Challenge/
   Betreibergrant und vollständigem Current=Target-Nachweis. Recovery oder
   gesunder Healthcheck erteilt niemals automatisch Resume.

Bei Zertifikats-/Tokenrotation die echte Inodebindung von Dateimounts beachten:
atomarer Hostdateiaustausch kann alten Containerinhalt belassen. Neue Bindung/
Instanz kontrolliert herstellen, Sessions/Widerruf erneut prüfen. Keine parallele
unbelegte Weitergeltung alter und neuer Identitäten.

## 11. Abschluss des späteren Versuchs

Für jedes Pflichtgate Zeitpunkt/Prüfer, genaue Version/Scope und redigierte
Evidenz sichern. Manuelle Entscheidung in `c26g_go_no_go.md` festhalten;
unbekannte Werte und rote Sicherheits-/Restore-/Alarmgates sperren. Go-live ist
ein eigener späterer Operatorakt, keine Nebenwirkung dieses Runbooks.

Dokumente später über regulären Review in den tatsächlichen Defaultbranch
integrieren. Jetzt kein Merge und kein Worktree-/Branchcleanup. Bei ungemergten
Änderungen oder ungeklärter Ownership alles erhalten und Abschluss als pending
melden. Keine bestehenden MAINT-/C26-/C27-Artefakte bereinigen.
