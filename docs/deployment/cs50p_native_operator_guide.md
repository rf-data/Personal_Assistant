# CS50P: minimaler nativer Hetzner-Betriebsplan

## C26-CS50P-03: Betreiberpaket

Zusammenhängender [Erstlauf](cs50p_first_run.md),
[VPN-/SSH-Preflight](cs50p_hetzner_preflight.md),
[versionierte Installation/Rückfall](cs50p_hetzner_installation.md) und
[aktueller SQLite-/Releasebefund](cs50p_mvp_release_readiness.md).
Die folgenden nativen Quellen-/Katalogbefehle bleiben die Detailreferenz.
Kein Hostbetrieb freigegeben; frühere Testerfolge sind kein SQLite-Stabilitätsbeweis.

**HOLD für Hostbetrieb.** Diese Befehle sind ein späterer Betreiberplan. In diesem
Auftrag wurden kein Server, VPN, SSH, systemd-Dienst oder Produktionsjob geändert.
Die bisherige MVP-Anleitung bleibt historische Evidenz; ihre v2-/Token-
Verarbeitungsbefehle gelten nicht für den neuen nativen Scope.

## Voraussetzungen und Installation

READ-ONLY, über bestehenden autorisierten VPN-/SSH-Zugang:

```sh
id
id cs50p
sudo sshd -t
sudo sshd -T | rg 'pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permitrootlogin'
sudo ss -lntup
systemctl status ssh tailscaled --no-pager
findmnt -T /var/lib
findmnt -T /var/cache
df -h /var/lib /var/cache
```

Betreiber prüft VPN-Geräte-/ACL-Freigabe, Schlüssel/Hostkey, einen einzigen
zugelassenen Betreiber, geschlossenen öffentlichen APIzugang und separaten
Rettungszugang in der Hetznerkonsole. Keine SSH-/Firewalländerung dieses Pakets.
Dedizierter Dienstaccount cs50p ohne Login und ohne weitere Benutzerprozesse;
SSH-Betreiber darf gezielt sudo -u cs50p und die genannten Dienstaktionen ausführen.
Wenn Account/Verzeichnisse bestehen: erst Eigentum/Inhalt prüfen, nicht übernehmen.

CHANGE, erst nach Account-/Pfadreview, ausschließlich neue dedizierte Pfade:

```sh
sudo useradd --system --user-group --home-dir /var/cache/cs50p-mvp --shell /usr/sbin/nologin cs50p
sudo install -d -m 0755 /opt/cs50p/app
sudo install -d -o cs50p -g cs50p -m 0700 /var/lib/cs50p-mvp /var/cache/cs50p-mvp
sudo install -d -o cs50p -g cs50p -m 0700 /var/lib/cs50p-mvp/specs /var/lib/cs50p-mvp/archive /var/lib/cs50p-mvp/reports /var/lib/cs50p-mvp/catalog /var/lib/cs50p-mvp/jobs
sudo tar -xf /srv/reviewed-cs50p/source.tar -C /opt/cs50p/app
sudo python3.12 -m venv /opt/cs50p/venv
sudo /opt/cs50p/venv/bin/python -m pip install --no-index --find-links=/srv/reviewed-cs50p/wheels --require-hashes -r /opt/cs50p/app/deployment/cs50p-mvp/requirements.txt
sudo install -m 0644 /opt/cs50p/app/deployment/cs50p-mvp/cs50p-download.service /etc/systemd/system/cs50p-download.service
sudo install -m 0644 /opt/cs50p/app/deployment/cs50p-mvp/cs50p-native@.service /etc/systemd/system/cs50p-native@.service
sudo systemctl daemon-reload
```

Weder enable noch Timer installieren. Code/venv sind root-eigen und für cs50p
lesbar, nicht schreibbar. Wheels und source.tar kommen ausschließlich aus dem
geprüften Kandidaten-/Runtimepaket. Ein positives `--require-hashes`-Wheelclosure-
Installationsergebnis auf dem Ziel fehlt noch: nicht durch ungepinnte Pakete ersetzen.
Die Testvenv dieses Auftrags ist ausdrücklich kein deploybares Runtimepaket.
Installation scheitert bei fehlenden Wheels geschlossen.

READ-ONLY, aus /opt/cs50p/app:

```sh
cd /opt/cs50p/app
/opt/cs50p/venv/bin/python -m pip check
sudo systemd-analyze verify cs50p-download.service cs50p-native@job_review.service
systemctl cat cs50p-download.service cs50p-native@job_review.service
systemctl show cs50p-native@job_review.service -p MemoryMax -p TasksMax -p CPUQuotaPerSecUSec -p RuntimeMaxUSec -p PrivateNetwork
/opt/cs50p/venv/bin/python -m scripts.cs50p_native --help
```

## Quellen, Download und Materialreview

Manifest/Snapshots, konkreten CS50P-HTML/PDF-Source-ID-Auszug und approvals.json
manuell auf Herkunft, Nutzung, Lizenz, robots, Aufbewahrung und Widerruf prüfen.
Keine Beispiele/Synthetic-Referenzen als reale Erklärung übernehmen. Specs/Dateien
mit Eigentümer cs50p und Modus 0600, Eltern 0700 installieren. limits.json aus dem
MVP-Profil verwenden. Jeder Download benötigt download **und** process Freigabe.

CHANGE – Batchdatei erstellen (SOURCE_ID vorher konkret aus Discoveryreview ersetzen):

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch plan --manifest /var/lib/cs50p-mvp/specs/discovery/manifest.json --course cs50_python --resource SOURCE_ID --output /var/lib/cs50p-mvp/specs/batch.json --limits /var/lib/cs50p-mvp/specs/limits.json
```

READ-ONLY – erster verwendbarer Download-CLI-Aufruf als Offlinepreview:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_mvp download --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --reports /var/lib/cs50p-mvp/reports
```

CHANGE – erster wirklicher Download unter allen systemd-Limits:

```sh
sudo systemctl start --no-block cs50p-download.service
```

Direkte CLI-Syntax desselben Downloads ist der Previewbefehl plus `--confirm`;
für Dauerbetrieb das Dienstprofil verwenden. Abrufe und Reports werden geschrieben.
Rückweg: `sudo systemctl stop cs50p-download.service`; Daten erhalten. Fehler/
Teilreste zuerst untersuchen, Retry nur ausdrücklich nach MVP-Anleitung.

READ-ONLY:

```sh
systemctl status cs50p-download.service --no-pager
sudo journalctl -u cs50p-download.service -n 100 --no-pager
sudo -u cs50p ls -l /var/lib/cs50p-mvp/reports
sudo -u cs50p cat /var/lib/cs50p-mvp/reports/DOWNLOAD_REPORT.json
```

CHANGE – Integritätsprüfung und Versiegelung, Ziel muss neu sein:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch seal --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --output /var/lib/cs50p-mvp/catalog/batch-001 --confirm
```

READ-ONLY: `sudo -u cs50p cat /var/lib/cs50p-mvp/catalog/batch-001/catalog.json`.
Nur wenn **alle** materials den Status sealed haben, Katalog in den Controller
übernehmen. Einzelne Rohdaten/Receipt-/Workflowdateien privat prüfen.

CHANGE – exakte Konfigurationsanlage, cs50p-UID automatisch aus realem OS-Account;
keine Tokens. Das Beispiel enthält bewusst einen leeren, nicht startfähigen Katalog:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python - <<'PY'
import json, os
from pathlib import Path
example=Path('/opt/cs50p/app/deployment/cs50p-mvp/native-controller.json.example')
sealed=json.loads(Path('/var/lib/cs50p-mvp/catalog/batch-001/catalog.json').read_text())
assert sealed['materials'] and all(r['status']=='sealed' for r in sealed['materials'])
value=json.loads(example.read_text())
value['native_uid']=os.getuid()
value['catalog']=sealed['catalog']
path=Path('/var/lib/cs50p-mvp/specs/controller.json')
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'w') as f:
    json.dump(value,f,sort_keys=True,indent=2)
    f.write('\n')
PY
```

Bei existierendem controller.json anhalten und bewusst neuen Scope/Pfad planen;
nicht überschreiben. Diese Specs und Limits bleiben für diesen Scope bytegenau.

## Native Admission und Verarbeitung

Alle Befehle aus /opt/cs50p/app. SOURCE_REF aus catalog.json, WORKFLOW_ID z.B.
cs50p_batch001, REVIEW_SHA und JOB_ID aus den jeweils vorherigen geprüften Reports
konkret einsetzen. Keine spitzen Klammern als Shellumleitung verwenden.

READ-ONLY – vor init meldet der Preflight `not_enrolled`, danach `checked`:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native preflight --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json
```

CHANGE – einmalig neue leere Queue/Enrollment anlegen, keine Jobfreigabe:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native init --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --confirm
```

READ-ONLY – kanonischen Review mit Hashes und geplantem Workflow ansehen:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native review --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --source-ref SOURCE_REF --workflow-id WORKFLOW_ID
```

CHANGE – genau einen Job freigeben, zeitlich begrenzt (Standard 300, maximal 600 s):

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native approve --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --source-ref SOURCE_REF --workflow-id WORKFLOW_ID --review-id REVIEW_SHA --ttl 300 --confirm
```

CHANGE – erster tatsächlich verwendbarer CLI-Verarbeitungsbefehl; konsumiert den
Grant und nutzt C16. Für SSH-unabhängigen Betrieb den darunterstehenden Dienststart
verwenden; **genau eine** der beiden Startvarianten:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native run --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID
```

```sh
sudo systemctl start --no-block cs50p-native@JOB_ID.service
```

Der zweite Befehl startet genau dieselbe CLI mit Hostlimits und privatem Netzwerk.
Der Job kann jetzt ohne offene SSH-Sitzung enden. Kein Neustart mit demselben Grant.

READ-ONLY – Status/Logs/Ergebnis (SQL-Lesen kann flüchtige WAL/SHM-Metadaten anlegen):

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native status --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID
systemctl status cs50p-native@JOB_ID.service --no-pager
sudo journalctl -u cs50p-native@JOB_ID.service -n 100 --no-pager
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native result --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID
```

`result` liefert den hashgeprüften Workflowreport einschließlich aller relativen
Ergebnispfade/Hashes und prüft die referenzierten Dateien. Abruf über SSH/stdout ist
serverseitig lesend; Umleitung in eine neue lokale Datei ist lokal CHANGE. Einzelne
Ergebnisse nur nach Pfad-/Hashreview aus dem privaten Workspace kopieren; keine
öffentliche Downloadroute öffnen.

CHANGE – kontrollierter Jobabbruch:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native cancel --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID
```

`cancel_requested` ist noch kein Prozessende. Status bis cancelled/interrupted
prüfen. Dienst-Rückweg, auch bei defekten Specs:

```sh
sudo systemctl stop cs50p-native@JOB_ID.service
```

systemd beendet die gesamte Dienst-cgroup; C16 signalisiert nur eigene, noch nicht
reapte Kinder. Nie einen gespeicherten PID aus Dateien mit kill übernehmen.

CHANGE – nur nach beendetem Dienst, bei nichtterminalem Job nach Crash:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native recover --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID --confirm
```

Fehlender Lifecyclebeleg/Quarantäne blockiert; dann Daten sichern und separat
untersuchen. Für erlaubtes Resume `review` und `approve` jeweils zusätzlich mit
`--resume` ausführen, den **neuen** review_id und die **neue** Job-ID verwenden.
Ein completed-Job wird nicht wiederholt. Kein Scheduler/automatischer Retry.

## Sicherer Rückweg

CHANGE: ausschließlich die benannte native Instanz und ggf. Downloaddienst stoppen.
READ-ONLY: in systemctl/Queue Terminalstatus und freien Speicher prüfen, Logs sichern.
Specs, Grants, Verbrauchsbelege, SQLite, Inputs und Ergebnisse privat erhalten.
Keine automatische Bereinigung, kein Reset/Prune und keine Quarantäneaufhebung.
Geänderte Config/Limits nicht in-place „reparieren“; exakten freigegebenen Stand
wiederherstellen oder neuen leeren Scope nach Review aufbauen. Rückkehr zum alten
Code erst bei vollständig gestopptem nativen Dienst; der alte v2-Pfad erhält dadurch
keine native Freigabe. Keine Abschaltung seiner Gates, keine öffentliche API öffnen.
