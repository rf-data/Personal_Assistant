# Lesende Betreiberinventur und notwendige Coolifyeinstellungen

**Nur vom Betreiber, nicht von Codex ausgeführt.** Erst bestehende Rollen privat
zuordnen, dann exakt diese Metadaten lesen. Keine vollständigen Inspect-, Env-,
Cmd-/Args-, Compose-, Log- oder Secretdateien ausgeben. Keine unbekannte Datei
einlesen, kein Container-`exec`, APIstart, Workerstart, Probe, Restore oder Toggle
als Inventur. Die Befunde aus `operator_inventory.v1.json` bleiben erhalten.

## Ergänzung 23.10.: bestätigte Labels und offene Startursache

Backend und UI melden `coolify.type=application`, `coolify.managed=true`,
Projekt `personal-assistant`, Umgebung `production`. Die vollständigen gemeldeten
Ressourcen-/Composewerte stehen als `operator_observed` im Inventar. Backend:
`NetworkMode=coolify`, `PublishedPorts={}`, `ExposedPorts=null`, nur Sleep.
Diese Labels bestimmen weder Buildtyp noch Auto-/Preview-/Webhookstatus.
Der Wert von `com.docker.compose.project.working_dir` ist noch nicht geliefert.

Die vorhandenen Dateien haben Vorrang, siehe [Quellenbewertung](source_assessment.md).
Den tatsächlich verwendeten Buildkontext/Dockerfilepfad und die **gerenderte**
Startdefinition privat gegen diese Dateien vergleichen. Die gemeldeten
`/artifacts/…`-Pfade nicht als Repositorypfad oder Inhaltsnachweis behandeln.
Keine vollständigen Artefaktdateien oder Buildlogs teilen; nur zugeordnete Pfade,
Quellhashes, feste Startup-Klassifikation und redigierte Unterschiede berichten.

Folgende Metadaten ausschließlich auf dem Betreiberhost für die bereits
bestätigte Rolle lesen; Codex führt sie nicht aus:

```sh
: "${C26_EXISTING_CONTAINER:?Privat bestaetigte bestehende Rolle}"
docker container inspect --format \
  'type={{index .Config.Labels "coolify.type"}} managed={{index .Config.Labels "coolify.managed"}} project={{index .Config.Labels "com.docker.compose.project"}} service={{index .Config.Labels "com.docker.compose.service"}}' \
  "$C26_EXISTING_CONTAINER"
docker container inspect --format \
  'config_files={{index .Config.Labels "com.docker.compose.project.config_files"}} working_dir={{index .Config.Labels "com.docker.compose.project.working_dir"}}' \
  "$C26_EXISTING_CONTAINER"
C26_OBSERVED_IMAGE_ID=$(docker container inspect --format '{{.Image}}' "$C26_EXISTING_CONTAINER")
docker container inspect --format \
  'entrypoint_empty={{not .Config.Entrypoint}} legacy_ui_path={{eq .Path "streamlit"}} sleep_path={{eq .Path "sleep"}} sleep_arg={{eq (json .Args) "[\"infinity\"]"}} c16_entrypoint={{eq (json .Config.Entrypoint) "[\"python\",\"-m\",\"scripts.deployment\"]"}} ui_launcher={{eq (json .Config.Entrypoint) "[\"python\",\"-m\",\"admin_ui_package.container_runtime\"]"}} sleep_cmd={{eq (json .Config.Cmd) "[\"sleep\",\"infinity\"]"}} legacy_ui_cmd={{eq (json .Config.Cmd) "[\"streamlit\",\"run\",\"app_ui.py\",\"--server.address=0.0.0.0\",\"--server.port=8501\",\"--server.headless=true\"]"}}' \
  "$C26_EXISTING_CONTAINER"
docker image inspect --format \
  'id={{.Id}} entrypoint_empty={{not .Config.Entrypoint}} c16_entrypoint={{eq (json .Config.Entrypoint) "[\"python\",\"-m\",\"scripts.deployment\"]"}} ui_launcher={{eq (json .Config.Entrypoint) "[\"python\",\"-m\",\"admin_ui_package.container_runtime\"]"}} sleep_cmd={{eq (json .Config.Cmd) "[\"sleep\",\"infinity\"]"}} legacy_ui_cmd={{eq (json .Config.Cmd) "[\"streamlit\",\"run\",\"app_ui.py\",\"--server.address=0.0.0.0\",\"--server.port=8501\",\"--server.headless=true\"]"}}' \
  "$C26_OBSERVED_IMAGE_ID"
```

Die Vergleiche prüfen ausschließlich bekannte feste Vektoren; ein `false`
bezeichnet keine bestimmte andere Startdefinition. Unterschiedliche Pythonpfade,
Wrapper oder unbekannte Args privat einordnen, nicht dumpen oder ausprobieren.
Diese vorgeschlagenen Docker-Templates wurden hier nicht gegen Docker ausgeführt.

| Lesender Befund | Zulässiger Schluss / weiterer Beleg |
| --- | --- |
| Tatsächliches Image hat Deployment-Entrypoint; Container hat anderen Entrypoint und Sleep als effektiven Prozess | Überschreibung gegenüber dem Image liegt vor; in gerenderter Compose und Coolify-Startfeldern lokalisieren, bewusste Absicht separat bestätigen |
| Tatsächliches Image ohne Entrypoint mit Sleep-CMD; Container unverändert ebenso | Sleep ist bereits Image-Default; vorhandene `docker/DockerFile.worker` ist ein Kandidat, tatsächlichen Buildpfad anhand Buildbeleg bestätigen |
| UI-Image hat Legacy-Streamlit-CMD und Container unverändert denselben Start | Mit historischem UI-Build vereinbar; unveränderliche Build-/Quellbindung statt allein Tag belegen |
| Aktuelles Launcherimage, aber direkte Streamlit-Laufzeit | Container-/Compose-/Coolify-Override prüfen; geschützten Launcher nicht durch direktes Streamlit ersetzen |
| Gemischte/fehlende/unbekannte Metadaten oder kein Buildbeleg | Ursache bleibt `unverified`; keine Build-/Startänderung oder neue Runtimeinstanz zur Diagnose |

## Drei nächste Betreiberaktionen

### 1. Ressourcen, Trigger und sämtliche Writer lesen

In Coolify 4.4.7 die bestehende Backend- und UI-Ressource öffnen, **ohne Speichern**:
Application-Label mit maßgeblicher Ressourcen-ID abgleichen; Buildstrategie (Dockerfile/Compose/Registry),
UUID, Repository/Branch, Base Directory, Compose Location, Raw-/Normalmodus,
Start-Overrides, Replikate, laufende/wartende Deployments lesen. Auto Deploy,
Preview Deployments, Git-/manuelle Webhooks, Registry-/API-/Schedulertrigger und
Deployberechtigungen separat dokumentieren. Keine Tokens oder Webhook-URLs teilen.
GitHub-Webhooks/Actions/Deploykeys nur in bestehenden read-only Anzeigen zuordnen.
Eine Docker-Containerbenennung beweist keinen dieser Werte.

```sh
docker container ls --format '{{.ID}}\t{{.Status}}\t{{.Image}}'
: "${C26_EXISTING_CONTAINER:?Privat bestaetigte bestehende Rolle}"
docker container inspect --format \
  '{{.Image}} running={{.State.Running}} restart={{.HostConfig.RestartPolicy.Name}} network={{.HostConfig.NetworkMode}}' \
  "$C26_EXISTING_CONTAINER"
docker container inspect --format '{{json .HostConfig.PortBindings}}' "$C26_EXISTING_CONTAINER"
docker container inspect --format '{{json .Config.ExposedPorts}}' "$C26_EXISTING_CONTAINER"
docker container inspect --format \
  'memory={{.HostConfig.Memory}} cpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}' \
  "$C26_EXISTING_CONTAINER"
```

Alle weiteren Container/Hostrunner privat auf C16-, C26-, CS50- und Loviscach-
Writer prüfen, nur Rollenaliase/Rootzuordnung berichten. Keine Prozessargumente
oder Umgebungen dumpen. Sleep im gemeldeten Container beweist nicht, dass auf dem
gesamten Host kein zweiter Executor arbeitet. Kein neuer Dienst, bevor alle Writer
einem Root und Verantwortlichen zugeordnet sind.

### 2. Runtime, Persistenz, Kapazität und Backups zuordnen

```sh
df -hT /srv/personal-assistant/data
df -i /srv/personal-assistant/data
du -sh /srv/personal-assistant/data
free -h
docker container inspect --format \
  '{{range .Mounts}}{{println .Source "->" .Destination "rw=" .RW}}{{end}}' \
  "$C26_EXISTING_CONTAINER"
```

Private absolute Pfade einer **echten C16-Settingsdatei**, separater Limitsdatei
und Mountpolicy feststellen. Vorhandene `*.paths.json` nicht als Settings laden.
Nur Metadaten teilen; Configinhalt privat mit dem vorhandenen Settingsmodell
abgleichen: absoluter `root`, Katalogclosure, individuelle Identitäten,
`execution_enabled`, `workflows_enabled`, Featureflags, `max_parallel=1`,
`max_queued=1` für den vorgeschlagenen begrenzten Bootstrap, Gatepflicht.
Das sind Zielanforderungen, keine behaupteten aktuellen Werte.

```sh
: "${C26_VERIFIED_CONFIG_FILE:?Bestaetigte bestehende Datei; kein geratenes Muster}"
: "${C26_VERIFIED_LIMITS_FILE:?Bestaetigte bestehende Datei}"
: "${C26_VERIFIED_POLICY_FILE:?Bestaetigte bestehende Datei}"
stat -c '%a %u:%g %s %n' \
  "$C26_VERIFIED_CONFIG_FILE" "$C26_VERIFIED_LIMITS_FILE" "$C26_VERIFIED_POLICY_FILE"
```

UID-/Root-/Mountpolicy muss im vorgesehenen Container ebenfalls passen. Keine
rekursiven `chown`/`chmod`, keine Migration oder Kopie der 755 MB. Den Jobroot
nicht aus dem Namen eines Pilotordners oder dem Vorhandensein einer DB erraten.
Annahme-/Dispatchpfade, vorhandene Queue-/Jobzustände, Heartbeat, Quarantäne und
Lockzuordnung über bereits vorhandene genehmigte Nur-Lese-Statusanzeigen belegen.
Fehlt eine solche Anzeige und ist der Root nicht bestätigt, bleibt Live-Idle
**unverified**; keinen Controller/Store oder Probejob zur Inventur initialisieren.
Eine Backupkopie beweist nicht den gegenwärtigen Live-Idle-Zustand.

Vorhandene Backupkataloge/Manifeste, Zeitpunkte und isolierte Restorebelege privat
zuordnen, ohne einen Backup-/Restorelauf zu starten. C22-Backup erfasst Jobroot und
referenzierte Kataloge; weitere CS50-/Loviscach-Verzeichnisse, TLS/OIDC und
Konfigurationen außerhalb dieses Scopes benötigen eigenen bestätigten Schutz.
Keine laufende SQLite mit `cp` sichern oder WAL/SHM separieren.

### 3. Private Transportkette und unveränderliche Versionen belegen

Für API, Worker, UI und Gateway nach deren tatsächlicher Zuordnung:

```sh
C26_OBSERVED_IMAGE_ID=$(docker container inspect --format '{{.Image}}' "$C26_EXISTING_CONTAINER")
docker image inspect --format \
  '{{.Id}} {{json .RepoDigests}} {{index .Config.Labels "org.opencontainers.image.revision"}}' \
  "$C26_OBSERVED_IMAGE_ID"
: "${C26_EXISTING_PRIVATE_NETWORK:?Bestaetigtes vorhandenes Netz}"
docker network inspect --format \
  '{{.Name}} internal={{.Internal}} members={{len .Containers}}' \
  "$C26_EXISTING_PRIVATE_NETWORK"
docker network inspect --format '{{range .Containers}}{{println .Name}}{{end}}' \
  "$C26_EXISTING_PRIVATE_NETWORK"
```

Build-/Deploybeleg mit tatsächlicher SHA und laufendem RepoDigest verbinden.
Fehlende Labels/RepoDigests bleiben **unverified**. Ein Image-ID-Digest ist kein
Registry-Manifestdigest; keine Gate-Imagereferenz daraus erfinden. Für den
gemeldeten alten lokalen Tag separat einen verlässlichen ruhenden Rückweg sichern.

DNS/SAN/CA, Zertifikatsablauf/Renewal, VPN-Technik/Routen, genehmigte/entzogene
Geräte und die am Traefik sichtbare RemoteAddr privat prüfen. Alle UI-Router,
Redirects, Middleware-Anhängung, Origin/WebSocketpeers, privaten API-Netzmitglieder
und direkten Portbindungen zuordnen. OIDC-Issuer/Callback/Subjects/Rollen/Kurse
privat abgleichen, niemals Keys, Cookies oder Bearer ausgeben. Bestehenden IdP,
Traefik und Rettungszugang unverändert lassen.

## Zielkonfiguration in Coolify — jetzt nur prüfen, nicht umstellen

| Feld / Bereich | Voraussetzung bzw. genehmigter Zielwert |
| --- | --- |
| Backendressource | Bestehende Ressource nachgewiesen übernehmen; Typ-/UUIDänderung ist ein eigener Migrationsentscheid, kein beiläufiges Anlegen einer zweiten App |
| Build/Compose | Compose-Unterstützung für `network_mode: service:api-gateway`; Raw/as-is-Kandidat mit exakt geprüftem finalen Rendering unter 4.4.7 |
| Base Directory / Compose Location | Repositoryroot und `deployment/coolify.runtime-bootstrap.compose.yaml`, nur nach genehmigter Adoption |
| Images | Geprüfte Registryreferenzen `@sha256:…`; API/Worker identisch, Gateway separat fixiert; kein Pull/Build/Tagwechsel durch diese Inventur |
| Profile / Restart | `c26-runtime-approved` erst nach Freigabe, zunächst `restart: no`; Wirkung im tatsächlichen Coolifyrenderer bestätigen |
| Backend Domains / Proxy | Für alle drei Backendrollen keine Domain und keine Traefikroute; `traefik.enable=false`; keine Hostports |
| Netzwerke | API nur Namespacekopplung; Gateway nur bestätigtes dediziertes internes API-Netz; Worker `none`; kein automatisch injiziertes zusätzliches `coolify`-Netz |
| Mounts / UID | Genau die bestätigten vier Quellen/Ziele, Config read-only; keine automatisch angelegten Hostpfade; UID 10001 nur bei nachgewiesener bestehender Berechtigung |
| Start / Health | Exakte EntryPoints/Kommandos und Compose-Healthchecks der Vorlage; keine globalen Start-/Healthoverrides |
| UI | Bestehende UI ersetzen, gepinntes #19/#20-Image, geschützter `container_runtime`-Launcher; vorhandenes UI-/Ingressnetz plus bestätigtes privates API-Netz |
| UI HTTPS | Bestehende UI-Ressource und bestätigten Servicekey erhalten; vorhandene C22-/C26-HTTPS-Einstellungen mit exakter Origin, privater API-URL, individuellen Bindungen, OIDC/CA und RemoteAddr-Allowlist übernehmen; `ui`-Overlay nicht blind mit `streamlit` zusammenführen |
| Trigger | Exklusiver genehmigter Driverpfad; alle alternativen automatischen und manuellen Wege nachweislich kontrolliert; kein Merge solange unbekannt |

Die aktuelle [Coolify-Dokumentation](https://coolify.io/docs/applications/builds/docker-compose)
unterscheidet Application/Service und beschreibt Rawmodus/Compose-Healthchecks.
Die konkrete 4.4.7-Oberfläche und ihre Auswirkungen sind noch nicht verifiziert.
Normalmodus darf die Namespace-/Netz-/Proxyverträge nicht heimlich erweitern.
Falls Raw-/Profilsupport oder sichere Ressourcenadoption nicht belegbar sind,
**NO-GO**, kein alternativer spontaner Containerstart.

Für jeden offenen Wert gilt: Befund mit Datum, Ressourcenalias und Prüfschritt
privat festhalten; nur redigierte Status-/Hashbelege weitergeben. Es wird keine
SourceApproval, Deployfreigabe oder Ready-Transition aus dieser Inventur erzeugt.

Die beispielhaften Pythonkommandos verlangen das tatsächlich geprüfte Runtimeimage
mit passender venv/PATH. Vorhandene Moduldateien im alten Sleep-Image beweisen
weder importierbare Abhängigkeiten noch einen geeigneten Interpreter. Kein
nachträgliches `uv sync`, Paketinstallieren oder Startversuch im Bestandscontainer.
Die Vorlage referenziert bewusst das bestehende schlanke C22-Runtime-Buildrezept
`deployment/Dockerfile`; dessen exaktes gebautes Manifest und der kombinierte
Deploymentcommit nach den noch offenen Reviews stehen noch nicht fest.
