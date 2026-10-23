# Betreiber-Runbook: erster Bootstrap, keine aktuelle Ausführungsfreigabe

Alle Befehle hier sind **nur vorbereitet, nicht ausgeführt**. Phasen 2–10 mit
Schreibwirkung erfordern jeweils die ausdrücklich gebundene Betreiberfreigabe.
Keine Host-/Coolifyaktion durch Codex. Historische Roots werden niemals übernommen.
[Mount-/Konfigurationsvertrag](runtime_configuration.md),
[Driververtrag](driver_contract.md), [Ressourcen](resources.md).

Wichtig: Es fehlt weiterhin der reale, reviewte #148-Driver mit vollständiger
Livebeobachtung des genehmigten Ressourcenscopes. Das verhindert Phase 8 und
reguläre spätere Deploy-/Rollbackoperationen. Ein Testdriver oder gespeichertes
Inventar darf ihn nicht ersetzen. Dieses Runbook ist noch kein ausführbares
Produktionspaket ohne die ausdrücklich aufgeführten Bindungen/Freigaben.

## 1. Nur lesende Inventur und exakte Bindungen

Bestehende Coolify-Applications öffnen, nichts speichern/reloaden/deployen:
Backend Application/Dockerfile, UI Application/Docker Compose, beide Manual
only bestätigt. UUIDs, Repository/Branch/Base Directory/Dockerfile bzw. Compose
Location, Startupoverride und sämtliche zusätzlichen Trigger/Rechte erfassen.
Die Übernahme **derselben** Backend-Application auf den bestehenden Dreirollen-
Composeverbund gesondert reviewen; kein zweiter Stack, keine neue UI. Gemeldete
Composeprojekte/Labels allein beweisen diese Übernahme nicht.

Auf dem Host ausschließlich Betreiber, ohne Secret-/Env-Ausgabe:

```sh
hostname
free -m
vmstat 1 5
df -hT /srv/personal-assistant/data /srv/personal-assistant/configuration
df -i /srv/personal-assistant/data /srv/personal-assistant/configuration
findmnt -T /srv/personal-assistant/data
nproc
docker ps --format '{{.ID}} {{.Names}} {{.Image}} {{.Status}}'
docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.CPUPerc}}'
```

Alle Writer/Guardians und historische Queues zuordnen, externe Annahmen sperren
(nur nach eigener Freigabe), Idle belegen. Nicht aus Sleep auf hostweite Idle
schließen. DNS/SAN/CA, privates Netz und exklusiven Mitgliederkreis, VPN, OIDC,
UI-Launcher und negativen Zugangstest festlegen. Netzwerk `coolify` allein ist
kein privates API-Netz. Kein Hostport/öffentlicher Router für API/Gateway.

## 2. Backup und begrenzter Rückweg

Vor Veränderungen vorhandenes Backupverfahren und vollständigen Scope bestätigen:
755 MB historische Daten einschließlich CS50/Loviscach, konsistente SQLite-
Sicherungen, Konfiguration/Policies/TLS/OIDC und Image-/Coolifydefinition. Keine
Live-SQLite-Datei blind kopieren. C22-Backup deckt nur seinen Jobroot und
referenzierten Katalog ab, nicht automatisch alles. Isolierten Restore prüfen.
Bestehende historische Controller nicht für `backup` initialisieren/adoptieren.

Für den **später neu provisionierten**, nachweislich ruhenden Root ist der
bestehende Befehl (im gebundenen Runtimekontext) verwendbar:

```sh
python -m scripts.deployment backup --config "$C26_CONFIG" --output "$C26_NEW_BACKUP"
python -m scripts.deployment restore --snapshot "$C26_NEW_BACKUP" --output "$C26_NEW_RESTORE"
```

Ziele müssen neue private Pfade sein; Restore bleibt isoliert und deaktiviert.
Zuerst Erfolg/Größe des vollständigen Altbestandsbackups, Rettungszugang und
Rollback ins ruhende Sleep-System dokumentieren, sonst STOP.

## 3. Images, SHA, Ressourcen- und Composebindung

Nach Mergefreigabe Reihenfolge #156 → #149 → #148 → #157, UI #20 separat.
Keine Merges/Ready/Auto-Merge in diesem Auftrag. Kombinierte tatsächliche SHAs
prüfen; keine virtuelle GitHub-Merge-SHA oder beweglichen Branch als Ziel wählen.
Backend `deployment/Dockerfile` einschließlich #148 Gate-CLI und Preflight;
Gateway `deployment/gateway.Dockerfile`, eigene gepinnte Basisimages. UI separat
bestehende `streamlit`-Ressource. Gebundene Images bauen/prüfen nur im freigegebenen
Buildfenster ohne Jobs; Import-/Rollen-/Health-Smokes exakt mit Runtime-Lock.

Vom Betreiber freizugebende Werte, **ohne Default-Raten**:

```sh
: "${C26_RENDERED_COMPOSE:?Reviewtes tatsächliches Coolify-Rendering}"
: "${C26_ENV_FILE:?Private Datei mit genehmigten Mounts/DNS/Netz/Images}"
: "${C26_PROJECT:?Tatsächlich adoptierter Backendprojektname}"
: "${C26_RUNTIME_IMAGE:?Registryname@sha256 mit Buildbeleg}"
: "${C26_GATEWAY_IMAGE:?Gatewayname@sha256 mit Buildbeleg}"
: "${C26_RUNTIME_SHA:?Tatsächlicher kombinierter Backendcommit}"
docker image inspect "$C26_RUNTIME_IMAGE" --format '{{.Id}} {{json .RepoDigests}} {{json .Config.Entrypoint}} {{json .Config.Cmd}}'
docker image inspect "$C26_GATEWAY_IMAGE" --format '{{.Id}} {{json .RepoDigests}}'
```

Tag, OCI-Label oder SOURCE_COMMIT-Env allein ist kein SHA-Provenienzbeleg.
Exaktes Rendering muss Loopback-Namespace, UID/Mounts/RO-Rechte/Healthchecks,
fehlende öffentlichen Ports/Router und Limits bestätigen. Coolify Raw-Deploy
kann auch bei inaktivem Profil pullen/stoppen/Netze ändern. Erst nach bestätigter
Adoption und separat genehmigtem Bootstrap darf der folgende direkte Compose-
Betrieb im **gleichen kontrollierten** Projekt stattfinden; ist er für die
reale Coolify-Ressource nicht genehmigt, STOP, keine Ersatzressource anlegen.

```sh
dc() { docker compose --env-file "$C26_ENV_FILE" -p "$C26_PROJECT" -f "$C26_RENDERED_COMPOSE" --profile c26-runtime-approved "$@"; }
dw() { docker compose --env-file "$C26_ENV_FILE" -p "$C26_PROJECT" -f "$C26_RENDERED_COMPOSE" --profile c26-runtime-approved --profile c26-worker-approved "$@"; }
```

Nie ungezieltes `up`, `down`, `--remove-orphans`, Pull/Build oder Coolify-Deploy
als Ersatz verwenden. UI und fremde Container bleiben außerhalb des Scopes.

## 4. Neuen Runtime-Root ausdrücklich provisionieren

**Schreibend, nur Betreiber nach Freigabe der exakten Hostpfade/UIDs und Mounts.**
Vorschlag Host `/srv/personal-assistant/runtime/c26-v1` → `/app/runtime-state`;
Root `c16`, neue Konfigurationsdateien unter bestehendem configuration-Mount.
Existiert der Zielroot schon, STOP und untersuchen; nicht leeren oder übernehmen.
Elternpfade auf Symlinks/fremde Mounts prüfen und Mountpolicy bestätigen.

```sh
namei -l /srv/personal-assistant/runtime/c26-v1
namei -l /srv/personal-assistant/configuration/c26-runtime
sudo install -d -m 0755 -o root -g root /srv/personal-assistant/runtime
sudo mkdir /srv/personal-assistant/runtime/c26-v1
sudo chown 10001:10001 /srv/personal-assistant/runtime/c26-v1
sudo chmod 0700 /srv/personal-assistant/runtime/c26-v1
sudo mkdir /srv/personal-assistant/runtime/c26-v1/c16
sudo chown 10001:10001 /srv/personal-assistant/runtime/c26-v1/c16
sudo chmod 0700 /srv/personal-assistant/runtime/c26-v1/c16
```

Nur neue, vorher nicht vorhandene Konfigurationsziele verwenden. Die zwei
versionierten `.example`-Dateien nach Prüfsumme als `controller.json` und
`limits.json` ablegen (UID10001/0600); privates Konfigurationsverzeichnis im
bestehenden configuration-Bind 0700/UID10001. Nicht über existierende Dateien
kopieren. Kein historisches SQLite/Katalogmaterial in den neuen Root kopieren.

Zunächst Mountidentität in einem ausdrücklich genehmigten kurzlebigen **Prüf-
container** erheben. Das ist kein API-/Workerstart, aber bereits eine gesondert
freizugebende Containeraktion. Keine Dockerrechte in Runtimecontainer mounten:

```sh
dc run --rm --no-deps --entrypoint python api -c 'import json; from pathlib import Path; from src.runtime_paths import mounts; print(json.dumps(mounts()[Path("/app/runtime-state")]))'
```

Aus exakt diesem Ergebnis die private Policy mit schema_version1, repository
`/app`, roots genau einem Grant `{path: /app/runtime-state/c16, mount_point:
/app/runtime-state, mount_identity: <obiges Ergebnis>, purposes:
[job_workspace], owner_uid: 10001}` erstellen. Nicht device/source/root schätzen.
Datei `persistent-roots.json` außerhalb des Jobroots, 0600/UID10001. Nach jeder
Mount-/Dockeränderung erneut überprüfen; keine alten Policies blind übernehmen.

Offline-Konfiguration prüfen, **keine Queueöffnung**:

```sh
dc run --rm --no-deps --entrypoint python api -m scripts.c26_runtime_preflight \
  --config /app/configuration/c26-runtime/controller.json \
  --limits /app/configuration/c26-runtime/limits.json \
  --runtime-mount /app/runtime-state \
  --runtime-image "$C26_RUNTIME_IMAGE" --gateway-image "$C26_GATEWAY_IMAGE"
```

Erwartet validierte deaktivierte Config und `queue_status=uninitialized`,
`queue_healthy=false`, keine Deploymentfreigabe. Danach **eigene** Freigabe
für DB-/Gateprovisionierung; nur im leeren neuen Root, als Runtime-UID:

```sh
dc run --rm -T --no-deps --entrypoint python api - <<'PY'
import os
from pathlib import Path
from src.job_control.models import load_settings
from src.job_control.operations import private
from src.job_control.store import Store
from src.job_control.deployment_gate import Gate
os.umask(0o077)
s = load_settings(private(Path('/app/configuration/c26-runtime/controller.json')))
assert str(s.root) == '/app/runtime-state/c16'
assert s.deployment_gate_required and not s.execution_enabled
assert not (s.identities or s.catalog or s.workflows_enabled or s.pdf_enabled or s.index_jobs_enabled or s.import_jobs_enabled)
assert (s.max_parallel, s.max_queued, s.max_jobs) == (1, 1, 1)
assert list(private(s.root, directory=True).iterdir()) == []
Store(s.root, deployment_gate_required=True)  # ausdrücklich schreibend
Gate(s).initialize()                         # initial held, niemals open
assert Gate(s).status()['phase'] == 'held'
PY
```

Dies verwendet ausschließlich bestehenden Store/Gate-Kern. Kein Schema/Queue-
Neuentwurf, kein temporäres Abschalten von `deployment_gate_required`.
Teilfehler: Root/Journals erhalten, STOP, nicht blind wiederholen oder Locks löschen.
Ein späterer API-/Workerstart erzeugt bei fehlender Queue weiterhin keinen Ersatz.

## 5. Gateway/API ohne Worker starten

Alte Sleepinstanz und alle anderen Writer vorher konkret zuordnen/idle belegen;
nur die genehmigte alte Backendinstanz kontrolliert stoppen, keine globalen
Stop-/Down-/Pruneaktionen. Private Netz-/TLS-/Caddyfilebindung muss bereits
abgenommen sein, sonst STOP. Workerprofil noch nicht aktivieren:

```sh
dc up -d --no-deps api-gateway
dc up -d --no-deps api
```

API bleibt execution=false, ohne Identitäten/Katalog, Gate held. Das Gateway
kann erst mit der API gesund werden; API `depends_on` ist deshalb service_started,
kein zyklischer Health-Start. API teilt real den Gateway-Netznamespace.

## 6. Health und Recoverygrenzen prüfen

```sh
dc exec -T api python -m scripts.deployment health --role api --config /app/configuration/c26-runtime/controller.json
dc exec -T api python -m scripts.deployment_gate status --config /app/configuration/c26-runtime/controller.json
dc exec -T api-gateway python /opt/gateway_health.py
dc ps
```

API/Gateway-Health beweist 401 für ungültigen Bearer plus TLS/DBintegrität,
keine Endnutzerberechtigung oder Pilotfreigabe. Gate muss held bleiben.
Fehler/Quarantäne/falscher Mount: geschlossen stoppen/untersuchen, keine Recovery
als Automatismus. Erst jetzt gesonderte Worker-Healthstartfreigabe.

## 7. Genau einen Worker starten, Annahme weiter geschlossen

Der vorhandene Executor verweigert execution=false. Deshalb nach eigener
Freigabe eine **separate** `worker-held.json` aus dem deaktivierten Controller
neu erstellen, ausschließlich execution=true; Identitäten/Katalog/Workflows
weiter leer/false. Gleicher Root/Limits, Gate held. In genehmigter privater
Compose-Env `C26_WORKER_CONFIG=/app/configuration/c26-runtime/worker-held.json`
binden und Rendering erneut prüfen. Das ist eine bewusst vorübergehende
ungleiche API-/Workerconfig und **keine finale Gate-Readiness**.

```sh
dw up -d --no-deps capacity-worker
dw exec -T capacity-worker python -m scripts.deployment health --role worker --config /app/configuration/c26-runtime/worker-held.json
dc exec -T api python -m scripts.deployment_gate status --config /app/configuration/c26-runtime/controller.json
```

Frischer Heartbeat, genau eine Executor-/Gatelease, leere neue Queue, Gate held;
kein zweiter Worker, kein angenommener/dispatchter Job. UID/Mount/Digest und RAM/
Swap nachmessen. Workerstart allein erteilt weder Workflow- noch Pilotfreigabe.

## 8. Neue ausdrückliche Aktivierungsfreigabe

Erst alle Betreiberbelege und der reale #148-Driver: eine finale gemeinsame
Settingsdatei mit individuell genehmigten Identitäten, konkret gehashtem Katalog,
execution=true und nur benötigten ausdrücklich erlaubten Workflows erstellen.
PDF/Import/Index bleiben false; keine Tokens im Repository. SourceApproval nicht
aus Operatorinventur erzeugen. max_jobs/queued/parallel und Limits bleiben 1.
Die genaue Aktivierung samt Neustarts braucht eigene Freigabe.

Worker/API kontrolliert stoppen (keine Überlappung), gemeinsame finale Settings
privat veröffentlichen, C26_WORKER_CONFIG auf dieselbe controller.json binden,
Rendering prüfen, API und genau einen Worker gezielt neu starten. Gate bleibt
held. Alle Rollen-/Mount-/Version-/individuellen UI-/VPN-/TLS-/OIDC-Positiv- und
Negativchecks erneut; unbekannte Inputs oder Quarantäne blockieren.

Der externe genehmigte Koordinator muss `Gate(final_settings).release(plan,
resume_approval, real_driver)` aufrufen. **Kein vorhandener CLI-Befehl führt dies
aus**; `check-plan` validiert nur. Beim initial held-Bootstrap gilt Current=Target
für SHA und Image, auf die nun laufende Runtime gebunden, nicht Sleep→Runtime
als angeblich schon gegateter Wechsel. Settings-, Persistenz-, geschützte
Ressourcen- und Gatewaybindung sowie Live-Readiness müssen stimmen. Freigabe
aktuell ≤1h und vom Betreiber, keine erfundene Observation/Testdriver.
Ohne reviewten echten Driver/Koordinator bleibt hier NO-GO; weitere technische
Arbeit nach Lieferung des echten Ressourcen-/Triggerscopes erforderlich.

## 9. Ein Material, ein explizit genehmigter Batch

Separates GO für konkret gebundene vorhandene Raw-Datei + SourceApproval,
C18-/B6-/Kapazitätsprüfung, Batchmanifest und Hashes; keine neuen Kursdownloads
oder ZIPimporte. Ein Material, ein Job, kein paralleles LLM/Parsing/Download.
Vor Start Genehmigung und Idempotenzbindung über bestehende C16-Preview/Confirm-
API prüfen; keine pauschale Create-Anfrage ohne belegten Katalog. Resultat,
Quality/Handoff/Child-IDs und Journal prüfen. `max_jobs=1` verhindert einen
zweiten gespeicherten Job. Nach Abschluss Intake wieder über den genehmigten
Wartungs-/Gatepfad schließen, nicht durch Journaledit. Keine automatischen Retries.

## 10. Rollback oder gesperrter Rückweg

Fehler: externe Annahme sperren, Gate-/Quarantänezustand erhalten. Wenn Rollen
anlaufen, aber nichts angenommen wurde, nach eigener Freigabe gezielt Worker
und API stoppen, dann Gateway; nicht auf Sleep als gesunde Runtime umschalten:

```sh
dw stop capacity-worker
dc stop api
dc stop api-gateway
```

Früheren Sleepzustand nur mit geprüftem altem Image-/Konfigurationsbeleg und eigener
Rollbackfreigabe herstellen, Root/Journals behalten, keine Queue aktivieren.
Späterer regulärer Rollback nur `Gate.run` mit realem Driver, frischem gebundenem
Rollbackplan und kompatiblen Images; Recovery bleibt zunächst verified/geschlossen,
Resume separat. Kein altes Image auf Definition-v2-Jobs loslassen, keine Daten-
oder Journalüberschreibung. Restore nur in neuen getrennten Root. Unbekanntes
Guardian-/SQLite-/Cleanupverhalten bleibt NO-GO und wird untersucht.
