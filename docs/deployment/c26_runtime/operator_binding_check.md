# Fünf lesende Betreiberpakete für die Ressourcenbindung

Bitte nur die folgenden fünf Pakete aus den **bestehenden** Applications liefern.
Projekt `personal-assistant`, Environment `production`: Backend
`personal-assistantworker-1`, UI
`personal-assistant-uimain-a8xzljz4fq52vt1yt43nheg5`. Buildtypen und Manual deployments
only, Previewanzeige None und vorhandene APIeinstiege sind bereits bestätigt.
Die Application-UUIDs wurden ausdrücklich benannt: Backend syboxap8mpf8lgjzpjdsqm0z,
UI a8xzljz4fq52vt1yt43nheg5. Diese Werte nicht nochmals als unbekannt abfragen.

Keine Eingabe ändern, Checkbox umschalten oder Save/Deploy/Restart/Load Compose/
Reload betätigen. Einige Felder speichern sofort. Nur sichtbare Werte ablesen.
Keine Secrets, Envwerte, API-Tokens, Webhookgeheimnisse/-URLs, Cookies,
privaten Schlüssel oder vollständigen Logs/Inspectausgaben teilen. Befehle nur
redigiert, ohne Secretargumente; sonst lediglich „Override vorhanden“ melden.

## 1. Sourcebindung und ergänzende Scope-UUIDs

In den bestehenden, bereits durch ihre UUID benannten Applications unter
**Source/Git** tatsächlich gewähltes Repository und Branch ablesen; zusätzlich
Projekt/Environment/Server-UUID, soweit angezeigt. Nur IDs/Repositorynamen teilen,
keine URL mit Token/Query. Bereits bestätigte Application-UUIDs bleiben
operator_observed; Repository-/Branch-/Scopezuordnung ist damit nicht bewiesen.

Zuordnung: JSONmatrix `repository`, `branch`; ergänzende Scope-UUIDs an denselben
Applicationdatensatz. Ein Repositoryname im Auftrag bezeichnet das Zielrepository,
nicht die bestätigte Coolifyauswahl.

## 2. Buildpfade und Overrides einschließlich Leerzuständen

Je Application **Configuration → General/Build** (Bezeichnungen können leicht
abweichen) lesen: **Base directory**, Backend **Dockerfile location**, UI
**Docker compose location**, **Custom build command**, **Custom start command**.
Beim Backend zusätzlich vorhandene Compose-Location nur melden, wenn tatsächlich
angezeigt. Vorhandene **Final build/start command (preview)** nur ablesen.
`docker/DockerFile.worker` nicht selbst auswählen. Für jeden angezeigten Wert
Input und wirksamen Wert getrennt erfassen:

| Zustand | Zu meldender Befund | Bedeutung im Inventar |
| --- | --- | --- |
| `value` | Sichtbarer echter Feldwert, ggf. redigiert | `operator_observed`, effektiver Wert nur soweit belegt |
| `explicit_empty` | Feld tatsächlich leer, `displayed_value=""` | Eingabe leer; effektiver Default zunächst `unverified` |
| `coolify_default` | Wirksamer Standard samt UI-/Versionsbeleg | Default nur mit Beleg, nicht aus Placeholdertext ableiten |
| `not_displayed` | Bereich geprüft, Feld nicht angezeigt | Kein Rückschluss auf leer/deaktiviert |
| `not_checked` | Noch nicht geprüft oder nicht zugänglich | Bleibt offen |

Beispiel: `{input_state: explicit_empty, displayed_value: "", effective_value:
null, effective_status: unverified}`. Ein graues `/docker-compose.yaml`-Placeholder
ist kein eingegebener oder bereits bewiesener wirksamer Pfad. Werte in
`base_directory`, `dockerfile_location|compose_location`, `custom_build_command`,
`custom_start_command` der jeweiligen Application eintragen. Eine generierte
`/artifacts/…/docker-compose.yaml` ist kein Repository-Pfadfeld.

## 3. Zusätzliche Deploytrigger und Rechte

Je Application **Advanced/Preview deployments/Webhooks** sowie zugehörige
GitHub-App-/Repository-Webhooks und vorhandene **Keys & Tokens/API-Rechte** nur
ansehen. Bereits belegt ist Previewanzeige None; offen bleibt das explizite
Featureflag. Melden: separate Git-/Webhook-/API-/Registry-/
Schedulerauslöser; berechtigte Deployakteure/Scopes; ausstehende Deployments und
aktive Previews. Keine URLs, geheimen Werte oder Tokens liefern/neu erzeugen.
Nicht sichtbare oder nicht geprüfte Trigger ausdrücklich offen lassen.

Zuordnung `additional_triggers`: pro Mechanismus Zustand, Quelle/Datum und wer
ihn kontrolliert. Die Repositoryprüfung steht im [Triggernachtrag](deployment_trigger_audit.md).
Ein angezeigter APIeinstieg beweist weder berechtigte Akteure noch Aufrufe.
Für späteren Driver braucht es einen exklusiven, genehmigten
Wechselpfad samt gebundenem Triggerkontrollbeleg. Manual only allein reicht nicht.

## 4. Image-/Buildprovenienz beider laufender Container

**Deployments → tatsächlich zugehöriger Build**: Deployment-ID, volle Commit-SHA,
gewählte Dockerfile-/Compose-Datei, Buildbeleg und Bezug zum Container ablesen.
Nur die relevanten redigierten Metadaten teilen, keine vollständigen Logs.
Falls UI die Imagewerte nicht zeigt, die untenstehenden Filter verwenden.

Getrennt melden: Container-ID; gemeldete Image-Referenz/Tag; lokale Image-ID;
Registry-RepoDigests; belegte Build-SHA und zugehörige Deployment-ID. Fehlende
RepoDigests als leere Liste melden, keine Image-ID einsetzen. SHA-artiger Tag,
OCI-Label oder SOURCE_COMMIT Runtime only allein beweist keine Buildherkunft.
Zuordnung `image_id`, `repo_digests`, `build_sha` und Buildbeleg derselben Application.

## 5. Geschlossener Dreirollen-Scope und spätere Adoption

Im Bestand bestätigen: Welche **eine** Backend-Application darf später Gateway,
API und Worker verwalten, welcher tatsächliche Composeprojektname soll gelten,
und bleiben UI/andere Apps/Mounts außerhalb ihres Wechsels? Kein Save/Umstellen.
Aktuelle Container-/Service-/Netz-/Mountzuordnung, alle unabhängigen Writer und
Queues sowie Backup-/Restore-/Sleep-Rückweg belegen. Für den neuen Root nur
Pfad-/Mountfreigabevorschlag, nichts erstellen. Private API-Netz-ID/Mitglieder,
TLS-SAN/CA-Fingerprint/DNS, VPN/OIDC-Bindung und aktuelle RAM-/Swapreserve nur
soweit bereits lesend belegbar. Keine Key-/Tokeninhalte oder produktiven DBzugriffe.

Zuordnung: Application-Scopebeleg mit ausgeschlossener bestehender UI; offene
Live-/Mount-/Healthprüfungen bleiben `unverified`. Der heutige Sleepbestand ist
keine bereits gesunde API-/Worker-Runtime und kein fertiger Driver-Nachweis.

## Wenige Hostfilter, nur falls die Oberfläche nicht genügt

Ausschließlich Betreiber, nach Bestätigung der aktuellen Containeridentitäten.
Die Namen unten sind gemeldeter Altbestand und können inzwischen veraltet sein.
Keine SSH-Verbindung/Hostabfrage durch Codex. Die Filter zeigen keine Envwerte,
Befehlsargumente, vollständigen Labels oder Prozessargumente:

```sh
for C26_INSPECT_CONTAINER in \
  syboxap8mpf8lgjzpjdsqm0z-20261022T151524 \
  streamlit-a8xzljz4fq52vt1yt43nheg5-20261014T055035
do
  docker inspect --format 'container={{.Id}} image_id={{.Image}} image_ref={{.Config.Image}} project={{index .Config.Labels "com.docker.compose.project"}} service={{index .Config.Labels "com.docker.compose.service"}} network_mode={{.HostConfig.NetworkMode}} ports={{json .NetworkSettings.Ports}}' "$C26_INSPECT_CONTAINER"
  docker top "$C26_INSPECT_CONTAINER" -eo pid,comm
done
```

```sh
docker image inspect --format 'id={{.Id}} repo_digests={{json .RepoDigests}}' \
  syboxap8mpf8lgjzpjdsqm0z:3b91d39195e0d13fe0442d4594b28e431b0f4236 \
  a8xzljz4fq52vt1yt43nheg5_streamlit:b2cf9ca9ba44ee770dab4d834a6ae8285f34776b
```

Referenzdrift möglich: `.Image` des Containers muss mit inspiziertem Image `.Id`
übereinstimmen. Bei abweichendem Tag dessen Wert nicht als laufendes Image ausgeben.

```sh
docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} rw={{.RW}}{{println}}{{end}}{{range $name, $network := .NetworkSettings.Networks}}network={{$name}} id={{$network.NetworkID}}{{println}}{{end}}' \
  syboxap8mpf8lgjzpjdsqm0z-20261022T151524
```

Keine pauschale `docker inspect`-/`.Config.Env`-/`docker logs`-Ausgabe, keine
API-/Webhook-Testaufrufe, keine Tokens für diese Bestandsfrage erzeugen. Alle
Kommandos sind nur vorbereitet und syntaxgeprüft, nicht auf Hetzner ausgeführt.
