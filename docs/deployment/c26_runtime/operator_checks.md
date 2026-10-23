# Verbleibende Betreiberprüfungen — drei lesende Pakete

Nur vom Betreiber ausführen. Codex greift nicht auf Hetzner, Coolify oder private
Runtime-/TLS-/OIDC-Dateien zu. Keine Save-, Reload-, Load-Compose-, Build-,
Deploy-, Probe-, Backup-/Restore- oder Startaktion als Inventur verwenden.
Auch Compose-Reload kann serverseitig arbeiten. Nur vorhandene Anzeigen lesen;
Secrets, Tokens, Webhook-URLs, Umgebungsdumps und komplette Logs nicht teilen.

## Bereits bestätigt — nicht erneut als unbekannt behandeln

| Wert | Backend | UI |
| --- | --- | --- |
| Ressourcentyp / Buildstrategie | Application / Dockerfile | Application / Docker Compose |
| Auto Deploy | Manual deployments only | Manual deployments only |
| Build cache / Build-ARG-Injektion | aktiviert / aktiviert | aktiviert / aktiviert |
| Source commit availability | Runtime only (preserves cache) | Runtime only (preserves cache) |
| Builder | Deployment server | nicht geliefert |
| Aktueller Start / Inhalt | bewusster Sleep-Platzhalter | gezeigter Composeinhalt entspricht `docker/docker-compose.ui.yaml`; Backend und Auth deaktiviert |

Die Erwartung bei normalem Git-Push/Merge ist damit **kein Autodeploy**. Separate
Preview-/Webhook-/API-/Registry-/Scheduler-/manuelle Trigger und Rechte bleiben
zu prüfen. Bestätigte Inhalte sind keine belegten Pfadfelder oder Imagedigests.

## 1. Buildpfade, Ressourcenbindung und zusätzliche Trigger

In den bestehenden beiden Applications ausschließlich die derzeitigen Felder und
vorhandenen Deploymentdetails lesen, ohne Speichern oder erneutes Laden:

| Noch fehlend | Konkreter lesender Schritt / redigierter Rückbeleg |
| --- | --- |
| Backend-Dockerfile und Base Directory | In General/Build die tatsächlich gespeicherten Felder und eventuelle Startüberschreibungen lesen; konkreten Pfad oder ausdrücklich leer melden. Nicht `docker/DockerFile.worker` aus dem Sleep-CMD ableiten |
| UI-Composepfad und Base Directory | Tatsächliche Compose Location lesen; Inhalt ist bereits bestätigt. `/artifacts/…`-Label nicht als Pfadfeld einsetzen |
| Repository/Branch, UUID und aktueller Build | Vorhandene Source-/Application-/Deploymentdetails zuordnen; SHA, Zeit, Image-ID/RepoDigest und Ressourcenalias privat verbinden. Runtime-only SOURCE_COMMIT ist kein unveränderliches Buildlabel |
| Zusätzliche Trigger | Preview-Einstellung, vorhandene Git-Webhooks, API-/Registry-/Schedulerwege, Deployrechte und wartende Deployments in bestehenden Anzeigen lesen; Status/Anzahl ohne URLs/Tokens liefern |
| Sichere spätere Backendadoption | Nur vorhandene Buildstrategie-/Raw-/Custom-Command-Felder ansehen; ob dieselbe Application eine Composeumstellung unterstützt und wie Rollen ersetzt werden, bleibt vor der Migration gesondert zu prüfen. Jetzt nicht umschalten |

Für die beiden bereits zugeordneten Container optional gefilterte Metadaten lesen:

```sh
: "${C26_EXISTING_CONTAINER:?Bereits bestaetigte bestehende Rolle}"
docker container inspect --format \
  'image_id={{.Image}} network={{.HostConfig.NetworkMode}} ports={{json .HostConfig.PortBindings}}' \
  "$C26_EXISTING_CONTAINER"
docker container inspect --format \
  'project={{index .Config.Labels "com.docker.compose.project"}} service={{index .Config.Labels "com.docker.compose.service"}} config_files={{index .Config.Labels "com.docker.compose.project.config_files"}} working_dir={{index .Config.Labels "com.docker.compose.project.working_dir"}}' \
  "$C26_EXISTING_CONTAINER"
C26_OBSERVED_IMAGE_ID=$(docker container inspect --format '{{.Image}}' "$C26_EXISTING_CONTAINER")
docker image inspect --format \
  '{{.Id}} {{json .RepoDigests}} {{index .Config.Labels "org.opencontainers.image.revision"}}' \
  "$C26_OBSERVED_IMAGE_ID"
```

Image-Entrypoint/CMD privat mit Container-Entrypoint/CMD und Buildrecord vergleichen;
nur Klassifikation melden: unveränderter Sleep-Default, Überschreibung gegenüber
dem Image, historischer UI-Start oder unbekannt. Keine vollständigen Cmd/Args
teilen. `docker/DockerFile.worker` passt zum bestätigten bewussten Platzhalter;
die tatsächliche Buildauswahl und das konkrete Overrideverfahren fehlen noch.
Ein Image-ID-Digest ist kein Registry-Manifestdigest. Fehlende RepoDigests nicht
aus Tags oder SOURCE_COMMIT erfinden.

## 2. Eine Queue, echte Runtimepfade, Budget und Rückweg

| Noch fehlend | Konkreter lesender Schritt / Rückbeleg |
| --- | --- |
| Aktiver C16-Root und alle Writer | Besitzer der bestehenden Roots/Rollen befragen und vorhandene read-only Statusanzeigen zuordnen: Queue-/Jobzustände, Heartbeat, Quarantäne und Locks. Kein Store/Controller zur Inventur initialisieren. Fehlt ein bestätigter Root/Status, bleibt Idle unverified |
| Controllerconfig, Mountpolicy und Limits | Tatsächliche vorhandene Dateien privat gegen Settings/CapacityLimits/Mountvertrag prüfen; nur Pfad/Modus/UID/Hash und freigegebene nicht geheime Felder berichten. `*.paths.json` mit nur repository/roots/schema_version ist keine C16-Settingsdatei |
| Wirksame Mounts | Vorhandenen Container-Mounttabellen die vier bestätigten Ziele und wirklichen Root/UID/Zweck zuordnen; keine rekursiven Berechtigungsänderungen oder Pilotmigration |
| RAM/CPU/Workerbudget | Vorhandene Server-/Containermetriken und wirksame Limits für Coolify/Systemdienste/Traefik/UI/weitere Container lesen; CPUzahl und Peakreserve einschließlich späterem Buildfenster liefern. [Budget](resources.md) verwendet keine behauptete Livebelegung |
| Backup und Rollback | Bereits vorhandene Manifest-/Zeit-/Hash-/Scope-/Restorebelege und frühere verfügbare Images zuordnen. C22-Jobrootbackup allein schützt nicht automatisch alle 755 MB, Konfigurationen und TLS/OIDC. Keinen neuen Sicherungs-/Restorelauf starten |

Optional auf dem bestätigten Host nur lesen:

```sh
df -hT /srv/personal-assistant/data
df -i /srv/personal-assistant/data
free -m
nproc
docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.MemPerc}} {{.CPUPerc}}'
docker container inspect --format \
  '{{range .Mounts}}{{println .Source "->" .Destination "rw=" .RW}}{{end}}' \
  "$C26_EXISTING_CONTAINER"
: "${C26_VERIFIED_CONFIG_FILE:?Vorhandene bestaetigte Datei}"
: "${C26_VERIFIED_LIMITS_FILE:?Vorhandene bestaetigte Datei}"
: "${C26_VERIFIED_POLICY_FILE:?Vorhandene bestaetigte Datei}"
stat -c '%a %u:%g %s %n' \
  "$C26_VERIFIED_CONFIG_FILE" "$C26_VERIFIED_LIMITS_FILE" "$C26_VERIFIED_POLICY_FILE"
```

Ein einzelner Stats-Snapshot belegt keine Peakreserve. Keine Live-SQLite mit `cp`
sichern, WAL/SHM nicht trennen, Quarantäne/Locks nicht entfernen. Kein Resume als
Diagnose. Es wird keine neue Queue oder SourceApproval aus diesen Daten erzeugt.

## 3. Privater Zugang und späterer begrenzter Pilot

| Noch fehlend | Konkreter lesender Schritt / Rückbeleg |
| --- | --- |
| Privates API-Netz | Bestehende Netzwerk-Metadaten lesen: internal-Flag, erlaubte Mitglieder, DNSname/Alias; gemeinsame Traefik-Netze sind noch kein privater APIpfad |
| DNS/TLS/VPN/OIDC | Vorhandene Domain-/Router-/Middleware-/VPN-/IdP-Anzeigen privat auf exakten SAN/CA/Ablauf, RemoteAddr-Allowlist an allen UI-Routern, zugelassene/entzogene Geräte, Issuer/Callback und individuelle Rollen/Kurse prüfen. Keine Schlüssel/Cookies/Bearer teilen |
| Quellen und erster Batch | Bereits gespeicherte SourceApproval-Referenzen, Kurs-/Ressourcen-/Hashbindung und vorhandene Aufgaben-/PDF-/Transcript-Rohartefakte inventarisieren. Fehlendes bleibt operator_action_required; keine neuen Freigaben oder Downloads erzeugen |

```sh
: "${C26_EXISTING_PRIVATE_NETWORK:?Bestaetigtes vorhandenes Netz}"
docker network inspect --format \
  '{{.Name}} internal={{.Internal}} members={{len .Containers}}' \
  "$C26_EXISTING_PRIVATE_NETWORK"
```

Der spätere Pilot benötigt nach eigener Freigabe frisches C18-/B6-Preflight,
genehmigte Limits auf dem tatsächlichen Worker-Mount und genau einen begrenzten
Materialjob. Die Abnahme von TLS/VPN/OIDC und Negativzugriffen erfolgt erst nach
gesondert genehmigtem Bootstrap. Kein Login-/Jobstart als heutige Inventur.

## Vorgeschlagenes Ziel — kein aktueller Coolify-Istwert

Bestehende Backend-Application nach separat geprüfter Adoption: Raw-Compose-
Kandidat der vorhandenen Vorlage, keine Backenddomains/Hostports, API im Gateway-
Namespace, Worker ohne Netz, gleiche digestgebundene Backendversion, vier
bestehende Mounts, Config read-only und vorhandene Health-/Ressourcenlimits.
Pflichtwerte und Profil erst im genehmigten Ablauf binden. [4.4.7-Grenzen](coolify_compatibility.md)
beachten: Ein inaktives Profil macht einen Coolify-Deployaufruf nicht folgenlos.

Bestehende UI-Application/Service `streamlit` erhalten, geschützten Launcher und
individuelle C16-/OIDC-/Origin-/CA-Bindungen übernehmen. `ui`-Overlays nicht blind
hinzufügen. Aktuelle UI-Grundwerte disabled bleiben bis zur separaten Freigabe
unverändert. Alle anderen Bestandsressourcen und Daten bleiben bestehen.
