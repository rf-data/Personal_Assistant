# C26-PILOT-INTEGRATION – aktuelle lokale Reviewchecks

27.10.2026. **Keine hier dokumentierte Liveaktion ist ausgeführt.** R/C/L aus
dem nachfolgenden ursprünglichen Paket bleiben maßgeblich. Neue lokale Befehle
sind ausschließlich auf einer Reviewmaschine mit synthetischen Inputs erlaubt.
Der neue Pilot-Composevertrag ersetzt den früher fehlenden kleinen Rollensatz,
nicht die produktive Gate-/Witness-/Driverfreigabe. Coolify4.5.0/Compose5.6.0
müssen gegen die gerenderte tatsächliche Ressourcenfassung geprüft werden;
lokale Compose5.0.2-Evidence beweist deren konkrete Kompatibilität nicht.

## N01 – Quell- und Patchidentität, nur lesen

**Zweck:** Vollständige Lieferung vor Review/Commit verifizieren.
**Voraussetzung:** Angegebener persistenter Pilot-Workspace, gesichertes Handoff;
kein Livehost. **Befehl:**

```sh
sha256sum -c artifacts/c26_pilot_integration/handoff/checksums.sha256
```

**Erwartung:** Alle gesicherten Quelldateien, Belege und Patches OK.
**HOLD:** Fehlende Datei oder abweichender Hash; nicht anhand Branchname fortsetzen.
**Seiteneffekte:** Nur lokales Lesen. **Rückweg:** Keiner; abweichende Daten erhalten.

## N02 – Compose rendern, ausschließlich lokales config

**Zweck:** Effektive Backendkonfiguration aller expliziten Profile prüfen.
**Voraussetzung:** Bereits vorhandene Compose-CLI; neue private Ergebnisdatei;
alle C26-Pilot-Pfad-/DNS-/Netz-/Digestvariablen anhand Runtime-Matrix ausschließlich
auf synthetische lokale Werte gesetzt. Kein envfile mit echten Secrets.
`PILOT_RENDERED` muss eine neue absolute Reviewdatei außerhalb des Checkouts sein.
**Befehl:**

```sh
: "${PILOT_RENDERED:?Neue lokale synthetische Ergebnisdatei erforderlich}"
(umask 077; set -C; DOCKER_HOST=unix:///tmp/c26-pilot-review-no-daemon.sock COMPOSE_DISABLE_ENV_FILE=1 docker compose --env-file /dev/null -f deployment/c26-pilot.compose.yaml --profile '*' config --format json > "$PILOT_RENDERED")
```

**Erwartung:** Exit0; drei deklarierte Rollen, keine ports, feste Digests,
identische API-/Workerqueue und Config, ein quotierter tmpfs-Mount je Rolle.
Das Manifest enthält deklarierte Rollen, keinen gestarteten Worker.
**HOLD:** Fehlende Variable, extra Dienst/Mount/Port, Tag, Profile-/Limitabweichung.
**Seiteneffekte:** Neue private Datei, kein Daemonzugriff, kein Containerstart.
**Rückweg:** Datei als Reviewevidence behalten; niemals daraus ein up/build/pull ableiten.

## N03 – Deaktiviertes Pilotmanifest prüfen

**Zweck:** V2-Pflicht, geschlossene Flags, Einjobgrenze und wirksame Composefelder prüfen.
**Voraussetzung:** N02, vorhandener Python3.12-Testinterpreter unter
`PILOT_BACKEND_PYTHON`, synthetische unveränderte Vorlagen. **Befehl:**

```sh
: "${PILOT_BACKEND_PYTHON:?Vorhandener gepruefter Python3.12-Interpreter erforderlich}"
"$PILOT_BACKEND_PYTHON" -B -m scripts.c26_pilot_preflight --compose "$PILOT_RENDERED" --controller deployment/c26-pilot.controller.json.example --limits deployment/c26-pilot.limits.json.example
```

**Erwartung:** offline_configuration_valid, execution_enabled=false,
deployment_permitted=false, production_release=HOLD; Exit0.
**HOLD:** Refusal/Exit2, unbekannte Felder oder jeder Versuch, true/Testauthority
als Bootstrap einzusetzen. **Seiteneffekte:** Nur Dateilesen; keine Stores,
Hostpfade, DNS oder Credentials öffnen. **Rückweg:** Keine Änderung; Inputs korrigieren
und neu reviewen, nie eine Prüfung mit künstlichem Genehmigungsfeld umgehen.

## N04 – Neue Ergebnis-/Gateverträge offline prüfen

**Zweck:** Kleinsten synthetischen C16/Gate/Worker/Ergebnisvertrag reproduzieren.
**Voraussetzung:** N01, vorhandene Testvenv, neuer externer Root in PILOT_TEST_ROOT;
kein echter Queue-/Katalogpfad. **Befehl:**

```sh
: "${PILOT_TEST_ROOT:?Neuer isolierter synthetischer Testroot erforderlich}"
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 "$PILOT_BACKEND_PYTHON" -m pytest -q -o addopts= -p no:cacheprovider -p tests.offline_guard tests/test_c26_pilot_workflow.py tests/test_c26_pilot_results.py tests/test_c26_pilot_mounts.py --basetemp="$PILOT_TEST_ROOT"
```

**Erwartung:** Tatsächliche Einzelresultate, keine nicht ausgeführten Tests als PASS.
**HOLD:** Jeder Fehler/Quarantäne-/Cleanupbefund; kein wiederholtes Starten auf
demselben Root. **Seiteneffekte:** Ausschließlich neue synthetische lokale
Testdateien und begrenzte Childprozesse. **Rückweg:** Belege und Quarantäne behalten,
keine Marker/DB löschen und keine Zeit-/Sicherheitsassertion lockern.

## N05 – Ergebnis-UI vorbereiten: BLOCKED

**Zweck:** Vollständigen Plan statt nur Artefaktmetadaten anzeigen.
**Voraussetzung:** Separater persistenter beschreibbarer UI-Checkout und eigener
Featurebranch, verifizierter UI-main, unabhängige UI-Tests.
**Aktion:** Noch kein ausführbarer Commitbefehl hier: die Sandbox erlaubt außerhalb
des Backend-Pilot-Workspaces nur /tmp und schützt die vorhandenen UI-Worktrees.
Der neue Backendvertrag steht in docs/job_control/api.md; UI soll ihn typisiert,
begrenzt und ohne unsafe HTML darstellen, bei Client-/Sessionwechsel neu authentifizieren.
**Erwartung:** Spätere Streamlit-Plananzeige plus APIfehler-/Rollen-/Expiry-/
Widerrufstests. **HOLD:** Nur Metadaten sichtbar oder UIänderungen im Backendrepo.
**Seiteneffekte:** Jetzt keine. **Rückweg:** Vorhandene UI bleibt unverändert.

Für Cold Bootstrap, Deploy, execution true oder Resume existiert hier **kein**
zulässiger Livebefehl. Die produktive Trust-/Driverkette fehlt. C05/C06/C08
bleiben BLOCKED; neue Templates ersetzen kein autorisiertes Operationspermit.
Die N-Befehle sind Konfigurations-/Testchecks, keine Genehmigung zu Serveraktionen.

---

## Ursprüngliche Read-only-/Change-/Live-Acceptance-Schritte

# C26-PILOT – Einzeln ausführbare Betreiberchecks

**Diese Anleitung ist kein Ausführungsauftrag.** Codex hat keine Verbindung zu
Hetzner, SSH, Cloudfirewall oder Coolify hergestellt. R-Schritte kann der Betreiber
jetzt lesend durchführen. C- und L-Schritte brauchen eine **eigene ausdrückliche
Freigabe** und ihre jeweils genannten Voraussetzungen. Ein HOLD stoppt abhängige
Schritte; keine Fehler mit `|| true` übergehen. Kein echter Job im aktuellen Auftrag.

## Arbeitsweise und Klassen

- **READ-ONLY CHECK:** Keine Dienst-/Daten-/Konfigurationsänderung, kein Job und
  kein Prüfrequest an die Anwendung. Hostbefehle ausschließlich in einer vom
  Betreiber bereits genehmigten Hostkonsole, keine hier neu einzurichtende SSHverbindung.
- **CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED:** Persistente Änderung,
  einschließlich Sicherung, neuem synthetischem Storage, Identitäten und Rollback.
- **LIVE ACCEPTANCE – SEPARATE APPROVAL REQUIRED:** Aktiver Netzwerk-/Browser-/
  Healthverkehr oder synthetischer Testjob auf dem freigegebenen Ziel.

Private Ergebnisse beim Betreiber halten. Nur redigierte Bool-/Status-/Hashbefunde
teilen; keine Env-, Vollinspect-, Secret-, Cookie-, OAuthcode-, Log- oder HARdumps.
Die nachstehenden Container-IDs sind **jeweils** aus R02 zu übernehmen; ein Name
ist keine beweiskräftige Rollenidentität. Variablen müssen im jeweiligen Schritt
lokal explizit gesetzt sein. Fehlender Wert ist ein beabsichtigter Abbruch.

## R01 – Ressourcen eindeutig zuordnen — READ-ONLY CHECK

**Voraussetzung:** Bereits autorisierter Zugang zur bestehenden Coolifyverwaltung.
**UI-Aktion:** Projekt öffnen → Ressource `personal_assistant:Worker_1` und die
vorhandene UIressource jeweils öffnen; Ressourcen-UUID, Environment/Serverzuordnung,
Repository, Branch, Buildtyp und zuletzt tatsächlich deployten Commit privat notieren.
Keine Edit-/Save-/Redeploy-/Restarttaste betätigen.
**Erwartung:** Zwei eindeutige bestehende Ressourcen; Backend-/UI-Repos wie im Auftrag.
**HOLD:** UUID/Zuordnung unbekannt, mehrere Kandidaten oder abweichender Server.
**Seiteneffekt:** Nur lesender Verwaltungszugriff/Auditprotokoll.
**Rückweg:** Ansicht schließen; keine Wiederherstellung nötig.

## R02 – Hostbudget und Containerliste — READ-ONLY CHECK

**Voraussetzung:** Betreiberkonsole am bestätigten Zielhost, keine neue SSHfreigabe.
**Befehle, einzeln:**

```sh
date -u
docker version --format '{{.Server.Version}}'
docker compose version
df -h /
free -m
docker ps --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Ports}}'
```

**Erwartung:** Gemeldeter Host; 2 vCPU/4 GB RAM/4 GB Swap separat mit Hostinventar
abgleichen; ausreichend Reserve, kein unerwarteter API-/UIhostport.
**HOLD:** Keine eindeutige Ressourcenzuordnung, niedrige Reserve oder unbekannte
Worker; die gemeldeten ca. 21 GB frei sind keine aktuelle Messung.
**Seiteneffekt:** Nur Kernel-/Docker-/Dateisystemabfragen.
**Rückweg:** Keine Änderung. Nichts löschen, um vermeintlich Platz freizumachen.

## R03 – Image, User, Restart und Healthstatus — READ-ONLY CHECK

**Voraussetzung:** `PILOT_CONTAINER_ID` explizit auf genau eine R02-ID setzen;
für jede zugeordnete Rolle getrennt wiederholen.

```sh
: "${PILOT_CONTAINER_ID:?Container-ID aus R02 erforderlich}"
docker inspect --format 'id={{.Id}} image={{.Image}} user={{.Config.User}} restart={{.HostConfig.RestartPolicy.Name}} status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}absent{{end}} readonly={{.HostConfig.ReadonlyRootfs}}' "$PILOT_CONTAINER_ID"
```

**Erwartung:** Istzustand passt zum Auftrag (zunächst ggf root/Health absent);
reale Image-ID wird gesichert. **Noch kein** Pilotpass.
**HOLD:** Identität ungeklärt oder unbekannte aktive Runtime.
**Seiteneffekt:** Lesend; keine Healthlog-/Envwerte ausgegeben.
**Rückweg:** Keine Änderung.

## R04 – Tatsächliche Mountziele — READ-ONLY CHECK

**Voraussetzung:** Genau eine bestätigte `PILOT_CONTAINER_ID`; Mountpfade bleiben privat.

```sh
: "${PILOT_CONTAINER_ID:?Container-ID aus R02 erforderlich}"
docker inspect --format '{{range .Mounts}}{{printf "%s -> %s type=%s rw=%t\n" .Source .Destination .Type .RW}}{{end}}' "$PILOT_CONTAINER_ID"
```

**Erwartung:** Backendziele `/app/.cache` **oder** `/app/cache` anhand Istzustand
aufklären; configuration/data/logs sowie UI /data und /logs exakt erfassen.
**HOLD:** Unbekannter/fehlender Zielpfad, überlappende Datenspeicher oder impliziter
Dockerpfad. Keine pauschale Übernahme in den Pilot.
**Seiteneffekt:** Mountmetadaten sichtbar, keine Dateiinhalte.
**Rückweg:** Keine Änderung; niemals Quelle umbenennen oder chmod/chown ausführen.

## R05 – Rechte und Filesystem der bestätigten Quelle — READ-ONLY CHECK

**Voraussetzung:** `PILOT_MOUNT_SOURCE` ist ein einzelner vorhandener Pfad aus R04;
kein rekursiver Scan, keine Geheimnisdatei öffnen.

```sh
: "${PILOT_MOUNT_SOURCE:?Vorhandener Mountpfad aus R04 erforderlich}"
stat --format='uid=%u gid=%g mode=%a type=%F' -- "$PILOT_MOUNT_SOURCE"
findmnt --target "$PILOT_MOUNT_SOURCE" --output TARGET,FSTYPE,OPTIONS
```

**Erwartung:** Tatsächliche UID/GID/Modi/Storage bekannt; für neue Pilotsources später
UID 10001, Root 0700 und Config 0600 erforderlich.
**HOLD:** Symlink, fremder/unklarer Owner, schreibbarer öffentlicher Pfad oder
unklare WAL-/flocksemantik. `stat` beweist weder effektiven Schreibzugriff noch fsync/WAL.
**Seiteneffekt:** Metadatenabfrage.
**Rückweg:** Keine Änderung; keine Rechtekorrektur im Bestand.

## R06 – Netze, Namespaces und Limits — READ-ONLY CHECK

**Voraussetzung:** Je bestätigte Container-ID aus R02 einzeln ausführen.

```sh
: "${PILOT_CONTAINER_ID:?Container-ID aus R02 erforderlich}"
docker inspect --format 'netmode={{.HostConfig.NetworkMode}} cpus_nano={{.HostConfig.NanoCpus}} memory={{.HostConfig.Memory}} memoryswap={{.HostConfig.MemorySwap}} pids={{.HostConfig.PidsLimit}} privileged={{.HostConfig.Privileged}} ports={{json .NetworkSettings.Ports}}' "$PILOT_CONTAINER_ID"
docker inspect --format '{{range $name,$net := .NetworkSettings.Networks}}{{printf "%s ipv4=%s ipv6=%s\n" $name $net.IPAddress $net.GlobalIPv6Address}}{{end}}' "$PILOT_CONTAINER_ID"
```

**Erwartung:** UI-/Worker-/Traefiknetzzuordnung nachvollziehbar; fehlende Istlimits
werden als Lücke erfasst. Später: API im Gatewaynamespace, Executor ohne Netz.
**HOLD:** Fremde Netzmitglieder/Hostports, privileged, unbekannter Namespace.
**Seiteneffekt:** Ausschließlich Metadatenabfrage.
**Rückweg:** Keine Änderung. Netze nicht vorsorglich trennen.

## R07 – Build-/Branch-/SHAbindung — READ-ONLY CHECK

**Voraussetzung:** R01 bestätigt.
**UI-Aktion:** Je Ressource → Source/Build-Konfiguration lesen; Repository-/Branch-
bindung, Buildkontext, Dockerfile-/Composepfad, ausgewählten Commit und aktuelle
Deploymentdetails privat erfassen. Backend master und UI main bestätigen;
konkrete Serverrevisionen gegen Auftrags-Iststand abgleichen. Image-/Registryansicht
auf tatsächlichen Digest und vorhandene Provenienz prüfen; keine Zugangsdaten öffnen.
**Erwartung:** Alte Identität nachvollziehbar, noch keine Zielsha freigegeben.
**HOLD:** Nur Branch/Tag bekannt, Buildprovenienz/alter Digest fehlt oder Zielsha driftet.
**Seiteneffekt:** Lesender Verwaltungszugriff.
**Rückweg:** Keine Änderung; ein rebuild ist kein Check.

## R08 – Alle Trigger und offene Deployments — READ-ONLY CHECK

**Voraussetzung:** Rechte zum Lesen beider Coolifyressourcen sowie zuständiger
Repository-/CIeinstellungen, ohne Tokens/Webhooksecrets anzuzeigen.
**UI-Aktion:** Pro Ressource Auto-Deploy, PR-/Previewdeployments, Webhookzuordnung,
Deploy-APIberechtigungen, Registryupdates, Schedules/Retryregeln und
Deploymentliste (running/queued/pending) ansehen; GitHub-App-/Webhook-/Actions-
Triggerpfade zu genau diesen Ressourcen bestätigen. Verwaltungsrollen und direkte
Deploy-/Restartpfade inventarisieren. Nur Status/Referenzen, keine URLs mit Tokens.
**Erwartung:** Auto-Deploy aus, keine offenen Deployments; vollständige Triggerliste.
**HOLD:** Jeder unbekannte/parallel nutzbare Mutationspfad oder offener Deploymentjob.
**Seiteneffekt:** Nur lesen.
**Rückweg:** Keine Änderung, keinen Webhook „testen“ und keine Queue abbrechen.

## R09 – Routenzustand erhalten — READ-ONLY CHECK

**Voraussetzung:** R01, lesbare Domain-/Netz-/Custom-Labelansicht.
**UI-Aktion:** UI hat keine Admin-Domain und keinen Hostport 8501; Zuordnung von
`demo.franke-data.dev` und `coolify.franke-data.dev`, Middlewarelisten und
Zertifikatsreferenzen privat notieren. Noch keine Domain hinzufügen und kein ACMEtest.
**Erwartung:** Bestehender Verwaltungszugang bleibt unverändert nachvollziehbar.
**HOLD:** Adminroute bereits vorhanden, unbekannte Routeraliases oder globale
Änderung zur Pilotaktivierung erforderlich.
**Seiteneffekt:** Lesender Zugriff; keine DNS-/TLSrequests durch diesen Check.
**Rückweg:** Keine Änderung.

## R10 – Cloudfirewall und IPv6zuordnung — READ-ONLY CHECK

**Voraussetzung:** Bereits genehmigter Betreiber-Lesezugang zur Cloudkonsole.
**UI-Aktion:** Für exakt den bestätigten Server Firewallzuordnungen sowie IPv4-/
IPv6regeln ansehen. SSHquellbeschränkung und Portregeln 80/443/8000/6001/6002
privat erfassen; Regelzuordnung ausdrücklich mit Serveridentität verbinden.
**Erwartung:** Bekannter IPv4befund eingeordnet; IPv6/unabhängige Negativprobe
bleiben bis L02 offen. Keine Netzsperre allein aus einer Regelansicht behaupten.
**HOLD:** Unklare Zuordnung oder ungeschützter Admin-/APIpfad.
**Seiteneffekt:** Nur Verwaltungslesen.
**Rückweg:** Keine Änderung, keine Firewalltaste betätigen.

## R11 – Rückweg verfügbar? — READ-ONLY CHECK

**Voraussetzung:** Betreiber kennt vorhandene Sicherungsreferenzen.
**UI-Aktion:** Nur Vorhandensein/Alter/Abdeckung von Ressourcenexport,
Konfigurationskopie, sicher verfügbaren Secretquellen und alten Imagedigests
mit [Rollbackanforderungen](c26_pilot_rollback.md) vergleichen; keine Secretinhalte
öffnen/ausgeben und keine Restoreprobe auf diesem Host.
**Erwartung:** Expliziter Befund je Konfiguration: recoverable / unknown / absent.
**HOLD:** Maskierte Screenshots als einzige Quelle, fehlendes altes Image oder
fehlende unabhängige Secret-/Configwiederherstellung. Dann C03–C08 blockiert.
**Seiteneffekt:** Nur Existenz-/Abdeckungsprüfung.
**Rückweg:** Keine Änderung; fehlende Sicherung über C01 separat behandeln.

## R12 – Gateintegration auf freigegebenem Quellcheckout — READ-ONLY CHECK

**Voraussetzung:** Reiner Quellcheckout auf einer lokalen Reviewmaschine; nicht
im Server-/Runtimeverzeichnis. Repositorypfad mit `cd` ausdrücklich auswählen.

```sh
git rev-parse HEAD
git ls-tree -r --name-only HEAD -- src/job_control/deployment_gate.py src/job_control/runtime_collector.py src/job_control/deployment_coordinator.py src/job_control/coolify_readiness.py scripts/deployment_gate.py tests/test_deployment_gate.py tests/test_deployment_gate_v2.py tests/test_runtime_collector.py tests/test_deployment_coordinator.py
```

**Erwartung heute:** SHA `a8af1d9…`, **keine** dieser Dateien. Dies bestätigt die
Integrationslücke; es ist ausdrücklich kein bestandener Deploymentcheck.
**HOLD:** Gatekette fehlt oder nur PRtitel/alte Testerfolge als Nachweis verfügbar.
**Seiteneffekt:** Nur Lesen lokaler Gitobjekte.
**Rückweg:** Keine Änderung; reguläre technische Integration separat reviewen.

## C01–C08 — CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED

Jeder Tabellenpunkt ist eine **einzelne** freizugebende Aktion. Keine dieser
Aktionen ist hier ausgeführt. „BLOCKED“ bedeutet, dass der vorhandene
Produktionsbefehl noch fehlt; es wird kein fiktiver CLI/Driver empfohlen.

| ID | Ausgangsvoraussetzungen | Exakter Befehl oder UI-Aktion | Erwartetes Ergebnis | Fehler-/HOLD-Kriterium | Potenzielle Seiteneffekte | Rückweg |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | R01–R11, eigenes privates Sicherungsziel, Genehmigung | In bestehender Coolifyverwaltung die beiden Ressourcen-/Compose-/Routingkonfigurationen in genehmigten privaten Sicherungsspeicher exportieren bzw. exakt kopieren; getrennte Secretquellen durch Betreiber sichern; Rekonstruktion nur am isolierten Konfigurationstestziel prüfen | Abdeckung und Restorefähigkeit der relevanten Config, alte abrufbare Images belegt | Export enthält nur Maskierungen/fehlt; kein isoliertes Testziel; unbekannte Secrets → Änderung blockiert | Private Sicherungskopie entsteht, keine Livekonfigänderung | Kopie geschützt aufbewahren; keine produktive Restoreaktion |
| C02 | R08 vollständig, C01, eigener exklusiver Gate-/Driverpfad technisch vorhanden | In beiden Ressourcen Auto-Deploy/Preview und alle inventarisierten alternativen Trigger deaktiviert bestätigen; weitere genehmigte Trigger ausschließlich über inventarisierte Schalter sperren; offene Deployments nur mit eigener Abbruchfreigabe beenden | Kein alternativer Mutationspfad, keine pending Deployments | Unbekannter Trigger oder direkte parallele Mutation möglich | Geplante Automation angehalten | Vorwerte gesichert; Wiederöffnung benötigt eigene Freigabe und darf Gate nicht umgehen |
| C03 | C01/C02, geprüfte neue Pfade und Quotaentscheidung, keine Altpfade | Nur auf neuem isoliertem Teststorage: `python -m scripts.deployment probe --config "$PILOT_NEW_CONFIG"` nach ausdrücklich genehmigtem Anlegen des neuen Roots/Katalogs/Config mit UID 10001 und Modi 0700/0600; Pfad und Config zuvor prüfen | rename/fsync/flock/SQLite-WAL am neuen Ziel wahr; Quota separat abgenommen | Pfad existiert als Altbestand, unerwartete Dateien/UID, Probe/Quota fehlt | Synthetische temporäre Probedateien/DB; neuer Pilotstorage, keine Altbestandsrechte ändern | Neuen Root getrennt behalten; keine Löschung/Adoption/Restore |
| C04 | C01–C03, bestätigter IdP/CA/VPN-/Netz-/Egressvertrag | IdP: eigene App mit Callback `https://admin.franke-data.dev/oauth2callback`; genau einen bestätigten Subject freigeben; individuelle Backend-/Tokenbindung und ro-Secrets gemäß Sicherheitsmatrix außerhalb Git bereitstellen; noch keine Adminroute | Vollständige private Identity-/Trustkonfiguration, keine Sharedtokens | Offene Issuer-/Subject-/CA-/Proxyfelder oder weiter Benutzerzugriff | IdPapp/Secretdaten und private Netzkonfiguration entstehen | Vorherige Config bleibt gesichert; neue Identität entziehen, Altzugänge erhalten |
| C05 | P01–P08 abgeschlossen, frischer leerer Pilotroot, C01–C04, spezifischer Backend-SHA-/Digest-/Scopegrant | **BLOCKED:** Kein produktiver permitpflichtiger Wechselbefehl vorhanden. Nach Integration ausschließlich reviewten Driver auf vorhandene Backend-UUID mit schmalem Rollenset anwenden: zunächst API/Gateway starten, konfigurierten Executor gestoppt halten; kein direkter Coolify-Deployklick | Annahme geschlossen, execution false, private API, kein gestarteter Executor | Fehlender Stufenstart-/Driver-/Bootstrap-/Rückwegnachweis; unbekannte Instanz/Queue | Bestehender `sleep infinity`-Container wird erst dann ersetzt | B01–B05, separat genehmigt; ohne Wiederherstellung keine Umstellung |
| C06 | C05 nachgewiesen, spezifischer UIgrant, read-only Inputs, private Readiness | **BLOCKED bis C05/Driver erfüllt:** vorhandene UI-UUID über gleichen exklusiven Gatepfad mit `coolify.ui.compose.yaml` + `coolify.private-https.yaml` auf genehmigten Digest wechseln; keine neue Ressource erzeugen | Fester Launcher, oidc/http/production, keine Adminroute/Hostports, execution false | Startguard/CA/Readiness schlägt fehl; Altcommand oder Auth disabled | UIunterbrechung | Gesicherte UIconfig/Image via genehmigtem Rollback, Adminroute geschlossen |
| C07 | C05/C06 gesund und authentifiziert ready, C01, privates Profil bestätigt | Coolify: nur inventarisierter UIservice → Domain `https://admin.franke-data.dev`; jede generierte Admin-HTTPSrouter-Middlewareliste um `${C26_ROUTE_ID}-private@docker` ergänzen und tatsächliche Bindung prüfen; genehmigte private DNS-/TLS-/IdPkonfiguration anwenden | Nur genehmigte Quellen gelangen zur OIDC-UI; Demo/Coolify unverändert | Globaler Routereingriff, falsche Quelle, fehlende Middleware/AAAA-/CAprüfung | Neue ausschließlich private Adminroute, DNS/TLSrequests | Nur neue Adminroute/Labels/DNS nach B03 zurücknehmen; keine Auth-disabled-Route |
| C08 | C01–C07 und L01–L04 bestanden, eigener einmaliger Job-/Resumegrant | **BLOCKED bis produktiver Koordinator vorhanden:** bei geschlossenem Gate Configwechsel auf `execution_enabled=true`, andere Opt-ins false und max_jobs/max_queued/max_parallel=1; genau einen Executor starten; `docker exec "$PILOT_WORKER_ID" python -m scripts.deployment health --role worker --config /run/config/controller.json` und UIreadiness aus L01 ausführen; echter Idle-/Scope-/Instanznachweis vor frischem Resumegrant | Worker läuft gesund/idle unter geschlossenem Gate; erst Resume macht einen Auftrag annehmbar | Gate fehlt, Worker startet bei false, Jobslot nicht frisch, Health-/Idle-/Scopelücke | Workerstart und Configwechsel; Annahme erst nach getrennter Resumeentscheidung | Annahme gegatet schließen, ggf Ownercancel nach L05; nie DB/Marker zurücksetzen |

Kein Paketparameter `PILOT_NEW_CONFIG` wird automatisch gesetzt. Ohne exakten
genehmigten neuen Pfad/Config ist C03 nicht auszuführen. C04 ist keine Freigabe
beliebiger Firewall-/VPNänderungen; notwendige Eingriffe benötigen einen eigenen
konkreten Plan. Für noch fehlende Driverbefehle muss die technische Folgearbeit
die genauen Kommandos liefern und erneut prüfen. Vorher kein „nur deployen“.

## L01–L05 — LIVE ACCEPTANCE – SEPARATE APPROVAL REQUIRED

| ID | Ausgangsvoraussetzungen | Exakter Befehl oder UI-Aktion | Erwartetes Ergebnis | Fehler-/HOLD-Kriterium | Potenzielle Seiteneffekte | Rückweg |
| --- | --- | --- | --- | --- | --- | --- |
| L01 | C05/C06, geschlossenes Admissiongate, execution false, `PILOT_*_ID` aus neuer Inventur | API: `docker exec "$PILOT_API_ID" python -m scripts.deployment health --role api --config /run/config/controller.json`; Gateway: `docker exec "$PILOT_GATEWAY_ID" python /opt/gateway_health.py`; UI: `docker exec "$PILOT_UI_ID" python -m admin_ui_package.container_runtime ready`; Executor hier noch gestoppt lassen | Diese drei Checks Exit 0, genehmigte Images/Versionen; Workerzahl jetzt 0, Workerprüfung erst C08 | 401health allein als Readiness ausgegeben; ungewollter Workerstart; Identity-/Image-/Instanz-/Scope fehlt | Interner Health-/TLS-/authentifizierter Prüfverkehr, keine Jobs | Annahme geschlossen, kein Auto-Restart; B01 zur Diagnose |
| L02 | C07, eigene unabhängige Quelle ohne VPN, tatsächliche IPv4/IPv6 und freigegebene Geräte-IP bekannt | Jeden unten stehenden curl-Befehl einzeln von zweiter Quelle ausführen; im Browser WSSupgrade von nicht erlaubter Quelle zusätzlich prüfen | Ablehnung vor UI, kein UIinhalt/IdPredirect; korrekte TLSprüfung; gleiche Prüfung für entzogene Geräte | TLSfehler als Netzpass, 200/302 zur App, Header-Spoofing öffnet Zugriff, IPv6 ungetestet | Ausschließlich Testrequests/Sicherheitslogs | Kein Job; Route schließen nach B03 wenn separat genehmigt |
| L03 | C07/L02, erlaubtes Gerät, eigene individuelle Testidentitäten und Widerrufsfreigabe | Browser auf `https://admin.franke-data.dev/`: Login/Refresh/Expiry/Logout; unbekannten Benutzer ablehnen; Viewer/Create und fremden Course/Owner ablehnen; Cookieflags und WSSorigin/Header gemäß Sicherheitsmatrix prüfen; keine HAR/Tokenwerte speichern | Nur genehmigter Operator, keine implizite Rolle, Grenzen auf API und UI wirksam | Geteilte Token, veraltete Session nutzbar, unerwartete Rechte | OIDC-Sessions/Prüfverkehr; Widerruf betrifft nur genehmigte Testidentität | Abmelden, individuelle Testbindung sperren, Gate geschlossen |
| L04 | Reviewimages, isoliertes synthetisches Containerziel **ohne Altvolumes**, execution am Livepilot weiter false | #109-Abnahme im isolierten Ziel nach vorhandenen Container-/Acceptanceharnesses: Limits/OOM/SIGTERM/KILL/Parent-Death/Cancel und missing-input-Startguards prüfen; Deploy mit aktivem/unklarem Job und verlorenen Locks muss Gate ablehnen | Cgroup/PID1/Storage/Health plus Drain-/Idleraces bestanden, Livezustand unberührt | Kein isoliertes Ziel, fehlende Gateharnesses oder unbestätigtes Kindprozessende | Eigene synthetische Testcontainer/Prozesse, bewusst injizierte Fehler | Nur eigene Testressourcen stoppen; Belege erhalten; keine Live-Restarts |
| L05 | L01–L04 und C08, eigener Freigabesatz für **einen** Job, reproduzierbarer Katalog | UI Jobs: `material_planning`, genehmigten `source_ref`, `cs50_python`, Section `0`, Output `pilot-material-plan` wählen; Preview prüfen und genau einmal bestätigen/starten. Erstclient schließen; von zweitem freigegebenen Gerät dieselbe Job-ID beobachten. Falls separat genehmigt und noch running: Owner-Cancel auslösen, bis bestätigtem terminalen Status beobachten | Ein Job, keine Downloads/LLM, verifizierter JSONplan oder bestätigter Cancel; zweiter Job verweigert; keine lokale Laufzeitabhängigkeit | Unbekanntes Ergebnis, zweiter Job möglich, nicht genehmigter Egress, Quarantäne, keine bestätigte Beendigung | Ein synthetischer Job, SQLite-/Log-/Artefaktschreibzugriffe | Annahme geschlossen lassen; kein Retry/Resume. Quarantäne/Belege erhalten, B01–B05 nur separat freigegeben |

Cancel nie durch einen zweiten Job „nachtesten“: schnelle Planung kann bereits
abgeschlossen sein. Der konkrete Cancelnachweis stammt dann aus L04, nicht aus
einem erfundenen L05-Erfolg. Kein Schlaf-/Shelljob als Ersatzrunner einführen.

### L02 – unabhängige negative Requests, einzeln

Nur nach eigener Livefreigabe. `PILOT_PUBLIC_IPV4`, `PILOT_PUBLIC_IPV6` und
`PILOT_ALLOWED_DEVICE_IP` müssen echte zuvor bestätigte Adressen sein. Kein `-k`,
keine Cookies/Authheader/Secrets. TLSfehler und Transportfehler getrennt bewerten.

```sh
: "${PILOT_PUBLIC_IPV4:?Bestaetigte oeffentliche IPv4 erforderlich}"
: "${PILOT_ALLOWED_DEVICE_IP:?Genehmigte Geraete-IP fuer Spoofingprobe erforderlich}"
curl --noproxy '*' --connect-timeout 5 --max-time 10 --resolve "admin.franke-data.dev:443:$PILOT_PUBLIC_IPV4" -H "X-Forwarded-For: $PILOT_ALLOWED_DEVICE_IP" -sS -o /dev/null -w '%{http_code}\n' https://admin.franke-data.dev/
curl --noproxy '*' --connect-timeout 5 --max-time 10 --resolve "admin.franke-data.dev:443:$PILOT_PUBLIC_IPV4" -sS -o /dev/null -w '%{http_code}\n' https://admin.franke-data.dev/oauth2callback
: "${PILOT_PUBLIC_IPV6:?Bestaetigte oeffentliche IPv6 erforderlich}"
curl --noproxy '*' --connect-timeout 5 --max-time 10 --resolve "admin.franke-data.dev:443:[$PILOT_PUBLIC_IPV6]" -H "X-Forwarded-For: $PILOT_ALLOWED_DEVICE_IP" -sS -o /dev/null -w '%{http_code}\n' https://admin.franke-data.dev/
```

Zusätzlich alle vorhandenen Adminrouteraliases und bestätigten öffentlichen
Backendports separat prüfen; die historischen Ports 8000/6001/6002 ersetzen
keine Inventur von 8016/8443/8501 und der tatsächlichen IPv6bindung. Dafür vor
Ausführung konkrete Zieladressen/Ports und Prüfquelle im Freigabemanifest
eintragen. Ein API-401 beweist Auth, aber keine private Netzisolation.

## Protokoll je einzelnem Schritt

Betreiber hält ID, Zeitpunkt/Quelle, bestätigte Ressourcen-/Image-/Konfigidentität,
eigene Freigabereferenz (nur C/L), redigiertes Soll-/Ist-Ergebnis, HOLDursache,
beobachtete Seiteneffekte und tatsächlich ausgeführten Rückweg privat fest.
Nicht ausgeführte Punkte heißen **NOT TESTED**, niemals PASS. Nach erfolgreichem
Pilotjob bleibt C26 HOLD und #111 DEFERRED.
