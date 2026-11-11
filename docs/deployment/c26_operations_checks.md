# C26 – Lesende Prüfkommandos für die spätere Betreiberabnahme

24.10.2026. Ergänzung zum [konsolidierten Bericht](c26_operations_acceptance.md).
**Keines dieser Netz-/Hostkommandos wurde von Codex am Ziel ausgeführt.**
Ausgaben sind neue Betreiberbelege, keine hier erteilte Betriebsfreigabe.
Die Bashblöcke wurden nur mit `bash -n` geprüft. Bestehende Werkzeuge benutzen;
fehlende Programme als ungeprüft melden, nichts installieren.

Nur bestätigte eigene Ziele verwenden. Private IPs, Mountpfade, Mitgliedschaft
und Fehlermeldungen lokal aufbewahren; zum Review nur redigierte Befunde mit
Zeit, Quellnetz, Ziel, IP-Familie und Exitstatus teilen. Keine `.env`, Secrets,
vollständigen Inspect-/Log-/Prozessargument-/SSH-Konfigurationsdumps senden.
Kein `set -x`. Keine SSH-Verbindung durch Codex und keine Cloud-/Coolify-API.
Die Hostblöcke führt der Betreiber ausschließlich in seiner bereits autorisierten
Hostkonsole aus; sie enthalten keinen Verbindungsaufbau dorthin.

## 1. DNS aus dem Betreibernetz und einem zweiten externen Netz

**Zweites Netz erforderlich:** zusätzlich z.B. ein unabhängiger Mobilfunkzugang,
außerhalb erlaubter Admin-CIDRs und ohne VPN/HTTP-Proxy. Quelle/Route privat notieren.
Gleiche Befehle von beiden Netzen aus; nicht auf dem Server als Ersatz ausführen.

```bash
date -u +%FT%TZ
for c26_host in demo.franke-data.dev admin.franke-data.dev coolify.franke-data.dev; do
  printf '\nDNS %s\n' "$c26_host"
  dig +noall +answer "$c26_host" A
  dig +noall +answer "$c26_host" AAAA
  dig +noall +answer "$c26_host" CNAME
done
```

Mit den in der Hetzner-Konsole **gelesenen** öffentlichen Adressen vergleichen.
CDN-/Proxyantwort, private Adresse und tatsächliche Origin-IP auseinanderhalten.
Kein AAAA ist ein DNSbefund; ein vorhandenes öffentliches IPv6 darf nicht wegen
fehlender Testkonnektivität als abgesichert gelten. Keine DNSänderung ausführen.

## 2. Neue TCP-Verbindungen zur bestätigten Origin-IP

Die Variablen selbst im Terminal auf die bestätigten Werte setzen. Kein altes
Skriptziel oder vermeintlich aktueller DNSwert wird automatisch übernommen.
`C26_SSH_PORT` ist der bestehende bestätigte Port, nicht zwingend 22.

```bash
set -u
: "${C26_SERVER_IPV4:?Bestaetigte oeffentliche Origin-IPv4 setzen}"
: "${C26_SSH_PORT:?Bestehenden SSH-Port aus eigener Konfiguration bestaetigen}"
date -u +%FT%TZ
for c26_port in 80 443 "$C26_SSH_PORT" 8000 6001 6002 8501 8443 8016; do
  if nc -4 -zv -w 3 "$C26_SERVER_IPV4" "$c26_port"; then
    printf 'IPv4 TCP %s: ERREICHBAR\n' "$c26_port"
  else
    c26_status=$?
    printf 'IPv4 TCP %s: nicht verbunden, exit=%s\n' "$c26_port" "$c26_status"
  fi
done
if test -n "${C26_SERVER_IPV6:-}"; then
  for c26_port in 80 443 "$C26_SSH_PORT" 8000 6001 6002 8501 8443 8016; do
    if nc -6 -zv -w 3 "$C26_SERVER_IPV6" "$c26_port"; then
      printf 'IPv6 TCP %s: ERREICHBAR\n' "$c26_port"
    else
      c26_status=$?
      printf 'IPv6 TCP %s: nicht verbunden, exit=%s\n' "$c26_port" "$c26_status"
    fi
  done
else
  printf 'IPv6: nicht gemessen; Adressbestand und Routing separat bestaetigen.\n'
fi
```

Von **zweitem nicht erlaubtem Netz** S-Ziel: 80/443 für bestehende öffentliche
Domains erreichbar; SSH nur gemäß genehmigter Quellregel, 8000/6001/6002 und alle
internen Appports nicht öffentlich erreichbar. Im erlaubten Adminnetz kann SSH
absichtlich erreichbar sein. Unassigned Admin-Domain ist kein Grund, deren
8501-Port zu öffnen. Jeder `nc`-Aufruf baut eine neue Verbindung auf, keine
Wiederverwendung einer Sitzung vor Aktivierung der Cloud-Firewall.

„Nicht verbunden“ unterscheidet nicht automatisch Firewall-Drop, Reject, keinen
Listener oder fehlende IPv6-Konnektivität. Mit positivem 443-Referenztest auf
derselben Adresse, Docker-PortBindings und Cloudkonsole zusammen bewerten.
Kein breiter Scan, keine HTTP-/Loginversuche auf den direkten Coolifyports nötig.

## 3. TLS: korrigierte OpenSSL-Syntax und echte Verifikationsfehler

`-connect` erwartet **Host:Port**, `-servername` einen **DNSnamen**; beide ohne
`https://`. Das im IDE markierte Beispiel mit URLschema ist daher fehlerhaft.
Nicht `2>/dev/null` verwenden: Ketten-/Hostnamenfehler müssen sichtbar bleiben.
Der reine `x509 -dates`-Ausdruck beweist selbst keine erfolgreiche TLSprüfung.

```bash
set -o pipefail
date -u +%FT%TZ
for c26_host in demo.franke-data.dev admin.franke-data.dev coolify.franke-data.dev; do
  printf '\nTLS %s\n' "$c26_host"
  if timeout 12s openssl s_client \
      -connect "$c26_host:443" \
      -servername "$c26_host" \
      -verify_hostname "$c26_host" \
      -verify_return_error </dev/null \
      | openssl x509 -noout -dates -issuer -subject -ext subjectAltName; then
    printf 'Kette/Hostname und Zertifikatsausgabe: Pipeline erfolgreich.\n'
  else
    c26_status=$?
    printf 'TLS/Timeout/Parser fehlgeschlagen: exit=%s; kein bestandener TLS-Nachweis.\n' "$c26_status"
  fi
done
```

Das prüft die vom jeweiligen Resolver gewählte Adresse. Bei mehreren A/AAAA
Adressen zusätzlich jede bestätigte Origin-Adresse mit Host/SNI prüfen. Für IPv6
in `-connect` die Adresse einklammern (`[Adresse]:443`), weiterhin DNS als SNI
und `-verify_hostname`. Ein Defaultzertifikat für die noch nicht zugewiesene
Admin-Domain kann fehlschlagen; das wird protokolliert und nicht durch `-k`,
Trust-Ausnahmen oder Domainänderung „repariert“.

Öffentliche HTTP-/HTTPS-Erreichbarkeit ohne Body-/Header-/Cookieausgabe:

```bash
for c26_host in demo.franke-data.dev admin.franke-data.dev coolify.franke-data.dev; do
  for c26_scheme in http https; do
    printf '\n%s://%s\n' "$c26_scheme" "$c26_host"
    curl --noproxy '*' --connect-timeout 4 --max-time 10 \
      --silent --show-error --output /dev/null \
      --write-out 'status=%{http_code} remote=%{remote_ip} tls_verify=%{ssl_verify_result}\n' \
      "$c26_scheme://$c26_host/"
  done
done
```

Kein `--location`: unbekannten Redirectzielen nicht folgen. Ohne `--fail` wird
ein 4xx als messbarer HTTPbefund ausgegeben; HTTP 200 ist kein Auth-/WSS-/C16-
Nachweis. Aktuell für unzugeordnetes Admin kein bestimmter Status vorausgesetzt.

## 4. Nur in der bestehenden Hostkonsole: OS, Kapazität, Hotplugbefund

```bash
date -u +%FT%TZ
cat /etc/os-release
uname -sr
getconf _NPROCESSORS_ONLN
df -hT /
df -i /
free -h
swapon --show --bytes
uptime
ip -br address
ip route show
ip -6 route show
ss -lnt
ss -lnu
systemctl show docker cloud-init-hotplugd.service \
  --property=LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,ActiveEnterTimestamp,InactiveEnterTimestamp
```

Kein `restart`, `reset-failed`, `cloud-init clean`, Paketupdate oder Reboot.
Anhand Zeitpunkt und heutiger Interfaces/Routen feststellen, ob I1 aktuell
relevant ist. Logs nur bei weiterem Bedarf privat gezielt lesen, nicht pauschal
in Chat/PR übernehmen. Die obigen Zahlen sind erst nach Durchführung neue O-Belege.

## 5. Hostkonsole: Firewallleseprüfung, keine Regeln ändern

```bash
if command -v ufw >/dev/null 2>&1; then
  sudo -n ufw status verbose
fi
if command -v nft >/dev/null 2>&1; then
  sudo -n nft list ruleset
fi
if command -v iptables >/dev/null 2>&1; then
  sudo -n iptables -S
  sudo -n iptables -t nat -S
fi
if command -v ip6tables >/dev/null 2>&1; then
  sudo -n ip6tables -S
  sudo -n ip6tables -t nat -S
fi
```

Nur bereits autorisierte Leserechte; `sudo -n` soll keine Passworteingabe oder
Eskalationskonfiguration auslösen. Fehlende Rechte/Tools als U markieren, nichts
installieren. Regel-/Adressausgaben privat prüfen. UFW `active` beweist nicht,
dass Docker-Published-Ports gefiltert sind; NAT/FORWARD und ggf. Dockerketten
beachten. Cloud-Firewallregeln erscheinen hier nicht.

**Zusätzlich manuell in Hetzner, nur ansehen:** exakte Server-/Firewallzuordnung
(auch Labelselector und mehrere Firewalls), öffentliche IPv4/IPv6, jede kombinierte
Allowregel einschließlich Quellnetzen/Portbereichen. Kein `hcloud`-/Cloud-API-Aufruf,
kein Save/Apply/Attach. Neue Origin-Verbindungen aus Abschnitt 2 mit diesem
Regelbild vergleichen. Bei VPN/privatem Cloudweg ist die öffentliche Cloudkante
kein ausreichender Schluss auf die innere Route.

## 6. Hostkonsole: gefilterte Docker-Metadaten

```bash
docker version --format '{{.Server.Version}}'
docker compose version
docker ps -a --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Jetzt UI, bestehenden Backendcontainer und bestehenden Proxy **bewusst** anhand
des Inventars zuordnen; keine neuen Rollen oder Container voraussetzen. Werte
für die folgenden drei Variablen selbst setzen. Container-ID möglichst vollständig.

```bash
set -u
: "${C26_UI_CONTAINER:?Tatsaechlichen bestehenden UI-Container bestaetigen}"
: "${C26_BACKEND_CONTAINER:?Tatsaechlichen bestehenden Backendcontainer bestaetigen}"
: "${C26_PROXY_CONTAINER:?Tatsaechlichen bestehenden Proxycontainer bestaetigen}"
for c26_container in "$C26_UI_CONTAINER" "$C26_BACKEND_CONTAINER" "$C26_PROXY_CONTAINER"; do
  docker inspect --format \
    '{{.Name}} image_id={{.Image}} user={{.Config.User}} network_mode={{.HostConfig.NetworkMode}} status={{.State.Status}} restarts={{.RestartCount}}' \
    "$c26_container"
  docker inspect --format \
    '{{if .State.Health}}health={{.State.Health.Status}}{{else}}health=not-configured{{end}}' \
    "$c26_container"
  docker inspect --format '{{json .HostConfig.PortBindings}}' "$c26_container"
  docker inspect --format \
    '{{range $name,$network := .NetworkSettings.Networks}}{{$name}} {{$network.NetworkID}} {{$network.IPAddress}} {{$network.GlobalIPv6Address}};{{end}}' \
    "$c26_container"
  docker inspect --format \
    '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}} rw={{.RW}};{{end}}' \
    "$c26_container"
  docker top "$c26_container" -eo pid,ppid,user,comm
done
```

Keine `.Config.Env`, Health-Logausgaben, freien Labels oder Prozessargumente
ausgeben. `comm=python` beweist noch nicht `app_admin.py`; Launcher/Buildpfad
später in der Ressourcenansicht und gegen den genehmigten Imagevertrag prüfen.
Kein `docker exec`/`run`, keine Pulls/Builds/Restart/Stop/Prune/Volumebefehle.
`ss` allein kann Docker-NAT nicht ausschließen; PortBindings zusätzlich nötig.

Die bereits lokal vorhandene Image-ID und die bestätigten Netznamen selbst aus
obigem Inventar übernehmen. Image-Inspect lädt kein fehlendes Image nach:

```bash
: "${C26_IMAGE_ID:?Eine bestaetigte lokal vorhandene Image-ID setzen}"
docker image inspect --format \
  'id={{.Id}} repo_digests={{json .RepoDigests}} oci_revision={{index .Config.Labels "org.opencontainers.image.revision"}}' \
  "$C26_IMAGE_ID"
: "${C26_INGRESS_NETWORK:?Bestaetigtes bestehendes Proxy-Netz setzen}"
: "${C26_BACKEND_NETWORK:?Bestaetigtes bestehendes internes API-Netz setzen}"
for c26_network in "$C26_INGRESS_NETWORK" "$C26_BACKEND_NETWORK"; do
  docker network inspect --format \
    '{{.Name}} id={{.Id}} internal={{.Internal}} {{range .Containers}}{{.Name}} {{.IPv4Address}} {{.IPv6Address}};{{end}}' \
    "$c26_network"
done
```

Fehlendes Backendnetz/RepoDigest/Health bleibt U, kein automatisches Erzeugen.
OCI-Revision ist eine Behauptung des Images, keine unabhängige Buildreceipt.
Keine neue API-/Gateway-/Workerrolle starten, um diese Felder zu befüllen.

Mountmetadaten für genau einen bereits bestätigten bestehenden Pfad, keine
Dateiinhalte/DBs/Volumekopien und keine rekursive Dateninventur:

```bash
: "${C26_KNOWN_PATH:?Bestaetigten vorhandenen Mountpfad aus obigem Inventar setzen}"
findmnt -T "$C26_KNOWN_PATH" -o TARGET,SOURCE,FSTYPE,OPTIONS
df -hT "$C26_KNOWN_PATH"
df -i "$C26_KNOWN_PATH"
stat -c 'device=%d inode=%i uid=%u gid=%g mode=%a type=%F' -- "$C26_KNOWN_PATH"
```

Hostmetadaten beweisen nicht die Mountidentität im späteren Container-Namespace.
Keine `scripts.deployment probe/backup/restore`, `Gate.initialize`, Worker-CLI,
SQL-/SQLite- oder `rsync`-Aufrufe in dieser Phase. Auch das Legacybackup `--dry`
ist kein offline lesender Check. Der bereits vorhandene queuefreie #157-Preflight
ist erst nach gesondert freigegebenem Zielmount/Policy sinnvoll; kein Docker-Exec
als spontane Ersatzprüfung.

## 7. Coolify, Trigger, Backup und spätere Funktionsabnahme – nur ansehen

In bestehender authentifizierter Oberfläche pro Backend/UI/Pilot und weiteren
geschützten Ressourcen aufschreiben, ohne Aktionen auszulösen:

- bestätigte Application-/Environment-/Serverzuordnung, installierte Version,
  Repository/Branch, Base Directory und exakten Dockerfile-/Composepfad;
- tatsächliche Revision, lokale Image-ID und Registrydigest/Buildreceipt;
- vorhandene Domains, Zielservice/-port, Ingress-/Backendnetze, UI-Middlewares
  und deren Zuordnung zu allen Routern, vertraute Proxyquellen;
- Manual-/Auto-Deploy, Preview-Feature **und** vorhandene Previews, externe
  Webhooks/APIberechtigte/Registry-/Schedulertrigger, aktive/wartende Deployments;
- bereits vorhandene Backupausführungen mit Zeit/Status/Größe/Scope/externer
  Verfügbarkeit und Secret-/APP_KEY-Aufbewahrung **ohne Werte**;
- vorhandene Alarmziele und letzter bekannter Beleg; kein Testalarm jetzt.

**Nicht klicken:** Deploy/Redeploy/Restart, Save, Validate connection, Generate,
Configure backup, Back up now, Download, Restore, Cleanup oder Delete. Kein
Testaufruf der angezeigten Deploy-URL und keine neue Token-/API-Anmeldung.

**Spätere separate Abnahme** nach freigegebener HTTPS-Anbindung: echter Browser-
Login/Logout/Ablauf, unbekannter Subject und Viewer-Negativfälle, WSS-Reconnect,
sichere Cookies, Origin-/Forwarded-Headerabwehr, individuelle C16-Capabilities,
privates Profil aus zweitem Netz mit korrektem SNI und gefälschtem X-Forwarded-For
ablehnen. Hier keine Tokens/Cookies in Curlargumenten und kein Jobstart als Probe.

## Protokollvorlage

| Zeit UTC | Prüf-ID / Befehlsabschnitt | Messort/Quellnetz | Ziel / Familie | Exit/Status | Erwartung erfüllt? | Redigierter Beleg / offene Frage |
|---|---|---|---|---|---|---|
| auszufüllen | z.B. N1 / Abschnitt 2 | zweites externes Netz, ohne VPN | bestätigte Origin-IP / IPv4 | auszufüllen | offen | keine Credentials/privaten Rohdumps |

Bis neue Belege vorliegen gelten die getrennten HOLDs des Hauptberichts.
