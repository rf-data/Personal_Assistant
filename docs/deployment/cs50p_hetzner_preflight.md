# C26-CS50P-03: privater VPN-/SSH-Preflight

**Betreiberplan, nicht ausgeführt. C26 HOLD.** Ein persönliches Tailscale-Konto
mit MFA, ein freigegebener Client, ein Server und persönliches OpenSSH-Konto
`cs50op`. Tailscale transportiert normales OpenSSH mit individuellen Schlüsseln;
Tailscale SSH bleibt aus. Keine öffentliche CS50P-UI/API und keine neuen
öffentlichen CS50P-Ports. Coolify-Netze, Container und Regeln bleiben bestehen.

Alle CHANGE-Blöcke sind spätere manuelle Schritte, keine Ausführungsfreigabe.
Variablen PUBLIC_IP, VPN_IP und CLIENT_VPN_IP durch geprüfte Werte ersetzen.
Zuerst vorhandene administrative SSH-Sitzung offen halten und Hetzner-Konsole
in einem zweiten Browserfenster auf Erreichbarkeit prüfen.

## Vorbedingungen und Rückweg

READ-ONLY, Server über bisherigen Adminzugang:

```sh
cat /etc/os-release
uname -m
id
sudo sshd -t
sudo sshd -T | rg 'pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permitrootlogin|listenaddress'
sudo ss -lntup
sudo ufw status verbose
sudo nft list ruleset
systemctl status ssh --no-pager
free -h
swapon --show
df -h /var/lib /opt
findmnt -T /var/lib
```

Erwartet: Ubuntu 24.04.5 tatsächlich bestätigen, 2 vCPU, etwa 4 GB RAM,
4 GB Swap und mindestens 5 GiB freie Reserve **nach** Runtimeinstallation.
Keine Swap-/Docker-/Coolifyänderung aus diesem Plan. Vorhandene SSH-Portnummer,
Cloud-Firewallregeln für IPv4/IPv6 und aktive Adminschlüssel privat inventarisieren.
Anpassungen an abweichende SSH-Ports benötigen einen eigenen Review.

READ-ONLY, Konsole: Hetznerprojekt/Server öffnen, Webkonsole öffnen; vorhandenen
Konsolenlogin prüfen, ohne Passwörter in Berichte zu kopieren. Rescue ist ein
separater Notfallweg mit Neustart und damit möglicher Coolify-Unterbrechung;
nur ausdrücklich im Notfall auslösen. Nicht zum VPN-Test verwenden.

## Tailscale installieren und Geräte einzeln zulassen

CHANGE, Webkonsole des eigenen Tailnets: bestehende Policy exportieren, Device
approval einschalten, nur Server und einen persönlichen Client einzeln freigeben.
Keine geteilten Logins, automatischen/preapproved Authkeys, Exit-Nodes, Subnetrouten,
Serve oder Funnel. Voraussetzung: alleiniger autorisierter Betreiber und kein
anderweitig genutztes Tailnet ohne abgestimmten Policyreview. Effekt: neue Geräte
bleiben bis Freigabe gesperrt. Rückweg: altes Policybackup wiederherstellen;
einzelne neue Geräte widerrufen. Bestehende fremde Geräte/Regeln nicht verändern.

CHANGE, Server; Voraussetzung: die folgenden neuen Paketquellenpfade existieren
noch nicht, Repositorykey und Quelle wurden anhand der offiziellen Anleitung
geprüft. Effekt: Paketquelle, Paket und tailscaled; apt kann Abhängigkeiten
installieren. Rückweg: VPN erst bei funktionierendem Adminzugang abschalten;
Paketbereinigung gesondert planen. Kein globales apt upgrade.

```sh
sudo install -d -m 0755 /usr/share/keyrings
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg -o /tmp/cs50p-tailscale-key.gpg
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list -o /tmp/cs50p-tailscale.list
sudo install -m 0644 /tmp/cs50p-tailscale-key.gpg /usr/share/keyrings/tailscale-archive-keyring.gpg
sudo install -m 0644 /tmp/cs50p-tailscale.list /etc/apt/sources.list.d/tailscale.list
sudo apt-get update
sudo apt-get install tailscale
sudo tailscale up --ssh=false --accept-routes=false --accept-dns=false
```

Tailscale kann eigene Netfilterregeln anlegen. Vorherigen/nachherigen nft-/UFW-
Zustand und bestehende Coolify-Erreichbarkeit lesend vergleichen; bei Abweichung
anhalten und den VPN-Rückweg über die alte Adminsitzung nutzen. Keine Docker-
Chains verändern. Keine neue öffentliche Firewallfreigabe für CS50P oder VPN
ableiten; die tatsächlich erlaubte ausgehende Relayverbindung muss funktionieren.

Authentifizierungslink privat im persönlichen Konto öffnen. CHANGE: genau dieses
Servergerät nach Namen/Adresse in der Geräteverwaltung freigeben. Client: offizielle
Tailscale-App installieren, mit demselben persönlichen Konto anmelden, einzeln
freigeben und VPN verbinden (CHANGE; Effekt: Client-VPN; Rückweg: trennen/widerrufen).
Auf Linux gilt dort ebenfalls `sudo tailscale up --ssh=false --accept-routes=false
--accept-dns=false` (CHANGE mit denselben Voraussetzungen). Keine Authlinks speichern.

READ-ONLY, jeweils Server und Client:

```sh
tailscale status
tailscale ip -4
tailscale ip -6
```

CHANGE, Tailnetpolicy: nur nach Export/Review, folgende **Beispielwerte ersetzen**.
Im dedizierten Tailnet vollständige erlaubende Altregeln entfernen, insbesondere
`*`-zu-`*`; Regeln sind additiv. In einem geteilten Tailnet erst separaten Review
abschließen. Effekt: nur ausdrücklich benannter Client erreicht SSH am Server;
Rückweg: gespeicherte Policy über Browser zurücksetzen. Geräteinhaber separat
prüfen; die IP-Bindung identifiziert ein Gerät, nicht dessen menschlichen Benutzer.

```json
{
  "hosts": {
    "cs50p-client": "100.100.10.1",
    "cs50p-server": "100.100.10.2"
  },
  "grants": [
    {"src": ["cs50p-client"], "dst": ["cs50p-server"], "ip": ["tcp:22"]}
  ],
  "tests": [
    {"src": "100.100.10.1", "accept": ["cs50p-server:22"], "deny": ["cs50p-server:8501", "cs50p-server:8000"]},
    {"src": "100.100.10.3", "deny": ["cs50p-server:22"]}
  ]
}
```

Policytests müssen im Tailneteditor bestehen. Explizite IPv6-Zugriffe ebenfalls
negativ prüfen; keine pauschalen IPv6-Freigaben ergänzen. Die fremde Test-IP wird
nicht als weiteres autorisiertes Gerät eingerichtet.

## Persönliches SSH-Konto

CHANGE, Client: neuer Schlüssel mit Passphrase, falls noch keiner vorhanden.
Voraussetzung: Zielname neu. Effekt: lokaler privater Schlüssel; Rückweg: public
Key am Server widerrufen, privaten Schlüssel privat erhalten.

```sh
ssh-keygen -t ed25519 -a 64 -f ~/.ssh/cs50p_operator
```

CHANGE, bestehende Adminsitzung: Konto neu anlegen und ausschließlich den geprüften
öffentlichen Schlüssel installieren. Voraussetzung: `cs50op` ist noch nicht belegt,
`/tmp/cs50p_operator.pub` enthält den separat übertragenen **öffentlichen** Schlüssel.
Effekt: persönlicher Login ohne Passwort; Rückweg: nach Rückkehr zum alten Admin
Konto sperren/Key widerrufen, Home erhalten. Kein Mitglied der docker-Gruppe.

```sh
sudo adduser --disabled-password --gecos '' cs50op
sudo install -d -m 0700 -o cs50op -g cs50op /home/cs50op/.ssh
sudo install -m 0600 -o cs50op -g cs50op /tmp/cs50p_operator.pub /home/cs50op/.ssh/authorized_keys
```

READ-ONLY: Serverhostkey über alte Sitzung/Konsole ermitteln und mit neuem Login
vergleichen, nicht ungeprüft aus ssh-keyscan vertrauen:

```sh
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

READ-ONLY, Client (SSH kann lokale known_hosts-Metadaten anlegen; Fingerprint prüfen):

```sh
ssh -i ~/.ssh/cs50p_operator -o IdentitiesOnly=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no cs50op@VPN_IP 'id; hostname'
```

CHANGE: erst nach erfolgreichem Schlüsseltest eine neue dedizierte sshd-Dropindatei
per `sudoedit /etc/ssh/sshd_config.d/00-cs50p-keys.conf` anlegen. Voraussetzung:
Include-Reihenfolge und bestehende Match-Regeln sind geprüft. Inhalt für das
persönliche Konto: `Match User cs50op`, eingerückt `PasswordAuthentication no`,
`KbdInteractiveAuthentication no`, `PubkeyAuthentication yes`, danach `Match all`.
Effekt: Schlüsselpflicht für cs50op; Rückweg: nur diese neue Datei über alte
Adminsitzung zurücknehmen und erneut validieren/reloaden. Bestehende administrative
Authentifizierung nicht umstellen. Kein SSH-Passwortzugang für den CS50P-Betreiber.

READ-ONLY: effektive Regeln **für diese Verbindung** prüfen:

```sh
sudo sshd -t
sudo sshd -T -C user=cs50op,addr=CLIENT_VPN_IP,host=cs50p-client | rg 'passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication'
```

CHANGE: `sudo systemctl reload ssh`. Voraussetzung: beide Prüfungen erfolgreich,
alte Sitzung bleibt offen. Effekt: neue Logins nutzen die Regeln; Rückweg: eigene
Dropindatei zurücknehmen und nach Syntaxprüfung reloaden.

READ-ONLY/Negativtests vom Client:

```sh
ssh -i ~/.ssh/cs50p_operator -o IdentitiesOnly=yes cs50op@VPN_IP 'id'
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password,keyboard-interactive -o BatchMode=yes cs50op@VPN_IP true
ssh -i ~/.ssh/UNAUTHORIZED_KEY -o IdentitiesOnly=yes -o BatchMode=yes cs50op@VPN_IP true
```

Erwartet: nur erster Login erfolgreich; unbekannter Schlüssel und Passwortversuch
werden abgewiesen. UNAUTHORIZED_KEY ist ein existierender, nicht zugelassener
Testschlüssel. Unfreigegebenes Gerät, anderes Konto und gesperrte Ports müssen
scheitern. VPN aus/an und erneuten Schlüssellogin prüfen, alte Adminsitzung behalten.

**Keine öffentliche SSH-Regel in diesem Auftrag ändern.** Erst nach allen positiven
und negativen VPN-Tests, Konsolenprüfung und separater Betreiberentscheidung
darf genau die bestehende öffentliche SSH-Regel eingeschränkt werden. Vorher
Regel-ID und IPv4/IPv6-Zustand exportieren; Rückweg über Hetzner-Webkonsole:
exakt alte Cloudregel wiederherstellen, eigenes Dropin zurücknehmen, `sshd -t`
(READ-ONLY), `systemctl reload ssh` (CHANGE). Keine UFW-/nft-Flushes oder Dockerregeln.

CHANGE, optionaler VPN-Rückweg über den **alten** Adminzugang:
`sudo tailscale down`. Effekt: VPN fällt weg; Voraussetzung: alternativer Zugang
funktioniert. Rückweg: obigen `tailscale up`-Befehl wieder ausführen. Kein Reboot.

Offizielle, am 27.10.2026 gelesene Quellen:
[Ubuntu-Pakete](https://pkgs.tailscale.com/stable/#ubuntu),
[Gerätefreigabe](https://tailscale.com/kb/1099/device-approval),
[Grants](https://tailscale.com/kb/1324/grants),
[Policy-Syntax](https://tailscale.com/kb/1337/policy-syntax),
[Tailscale SSH und Portübernahme](https://tailscale.com/kb/1193/tailscale-ssh),
[Hetzner-Rescue](https://docs.hetzner.com/cloud/servers/getting-started/rescue-system/).
Bei Installation erneut prüfen; keine Livevalidierung behauptet.
