# C26-CS50P-03: erster privater Durchlauf

**Noch nicht freigegeben: HOLD.** Nur nach SQLiteentscheidung, Paketreview,
positivem Neuinstallationstest und Hostpreflight ausführen. Keine echten
Kursdownloads/Jobs in diesem Codexauftrag. Ein Betreiber, ein Downloaddienst,
anschließend genau eine ausdrücklich genehmigte native C16-Instanz.
Der [Installationsplan](cs50p_hetzner_installation.md) regelt Konten/Rechte;
die [native Anleitung](cs50p_native_operator_guide.md) enthält Details der
Quellen-/Katalogerstellung. Alte v2-/Tokenbefehle des MVP sind kein nativer Startweg.

## Verbindung und Installation prüfen

CHANGE, Client: Tailscale-App verbinden (Linux siehe
[Preflight](cs50p_hetzner_preflight.md)). Voraussetzung: Konto/Gerät ausdrücklich
freigegeben; Effekt: private VPN-Verbindung; Rückweg: trennen, alten Adminzugang
behalten. READ-ONLY:

```sh
tailscale status
tailscale ip -4
ssh -i ~/.ssh/cs50p_operator -o IdentitiesOnly=yes -o PasswordAuthentication=no cs50op@VPN_IP
```

READ-ONLY, Server:

```sh
cd /opt/cs50p/app
id
id cs50p
df -h /var/lib/cs50p-mvp
systemctl cat cs50p-download.service cs50p-native@job_review.service
/opt/cs50p/venv/bin/python -m pip check
/opt/cs50p/venv/bin/python -m scripts.cs50p_native --help
```

Nachfolgende Plan-/Seal-/Init-/Recover-/Dateilesebefehle führt das persönliche
**Administratorkonto** des Betreibers aus; cs50op erhält nur die begrenzten
Regeln des Installationsplans. Für die konkrete Job-ID trägt der Admin einmalig
die Dienstfreigabe ein. Keine sudo-Shell als cs50p benutzen.

## Materialien vorbereiten und herunterladen

READ-ONLY, Admin: freigegebenes Discoverymanifest/Snapshots, konkrete Source-ID,
Lizenz-/robots-/Nutzungs-/Aufbewahrungs-/Widerrufsreferenzen prüfen. In
`approvals.json` download **und** process müssen ausdrücklich freigegeben sein.
Keine synthetischen Angaben als Quellenfreigabe verwenden.

```sh
sudo -u cs50p cat /var/lib/cs50p-mvp/specs/discovery/manifest.json
sudo -u cs50p cat /var/lib/cs50p-mvp/specs/approvals.json
sudo -u cs50p cat /var/lib/cs50p-mvp/specs/limits.json
```

CHANGE, Admin: Batch für genau die geprüfte SOURCE_ID erstellen. Voraussetzung:
geprüfte Dateien installiert, output neu, maximal drei erlaubte HTML/PDF-Materialien.
Effekt: Batchdatei; Rückweg: noch keinen Download starten, Datei erhalten.

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch plan --manifest /var/lib/cs50p-mvp/specs/discovery/manifest.json --course cs50_python --resource SOURCE_ID --output /var/lib/cs50p-mvp/specs/batch.json --limits /var/lib/cs50p-mvp/specs/limits.json
```

READ-ONLY, Admin: Offlinepreview ohne `--confirm`, keine Netzübertragung:

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_mvp download --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --reports /var/lib/cs50p-mvp/reports
```

CHANGE, cs50op: `sudo systemctl start --no-block cs50p-download.service`.
Voraussetzung: Preview geprüft, ausreichende Reserve, keine Workerinstanz aktiv.
Effekt: echte begrenzte HTTPS-Downloads, private Rohdateien, Hashreceipts und
Reports; Rückweg: `sudo systemctl stop cs50p-download.service` (CHANGE; laufende
Übertragung endet, Teil-/Fehlerdaten erhalten). Kein automatischer Retry.

READ-ONLY, nach Start und auch nach erneutem SSH-Login (Journal als Admin):

```sh
systemctl status cs50p-download.service --no-pager
sudo journalctl -u cs50p-download.service -n 100 --no-pager
sudo -u cs50p ls -l /var/lib/cs50p-mvp/reports
sudo -u cs50p cat /var/lib/cs50p-mvp/reports/DOWNLOAD_REPORT.json
```

DOWNLOAD_REPORT durch tatsächlichen Dateinamen ersetzen. Erfolgreicher oneshot
kann bereits inactive sein; Exitstatus und Report zusammen prüfen. Nicht allein
vom Dienstzustand auf Erfolg schließen. Erst bei verifizierten Materialien weiter.

CHANGE, Admin: Integrität erneut prüfen und neuen Katalog versiegeln.
Voraussetzung: Download beendet, alle gewünschten Materialien verified, Ziel neu.
Effekt: gebundene Katalog-/Workflowdateien; Rückweg: nicht enrollen, Dateien erhalten.

```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch seal --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --output /var/lib/cs50p-mvp/catalog/batch-001 --confirm
```

READ-ONLY: `sudo -u cs50p cat /var/lib/cs50p-mvp/catalog/batch-001/catalog.json`.
Alle Materialien müssen sealed sein. SOURCE_REF aus dem tatsächlichen Katalog
übernehmen. Controllerdatei mit tatsächlicher Dienst-UID und diesem Katalog
**exklusiv neu** erstellen: vollständiger Pythonbefehl in
[Quellen-/Katalogreview](cs50p_native_operator_guide.md#quellen-download-und-materialreview).
Dieser CHANGE erzeugt nur controller.json; Voraussetzung: neuer leerer nativer
Scope, echte Freigaben, ssh-runtime. Rückweg: nicht enrollen; niemals Enrollment
oder bestehende Specs umschreiben. Die Beispiel-UID 1000 ist kein Identitätsbeleg.

## Enrollment, genau eine Freigabe, Start

Für die Lesbarkeit folgende Shellfunktion als **CHANGE nur der aktuellen Sitzung**
definieren; Voraussetzung: root-eigene CLI und geprüfte fixe Specs. Effekt:
Abkürzung; Rückweg: neue Shell oder `unset -f n` (CHANGE, nur Sitzung).

```sh
n() { sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native "$1" --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json "${@:2}"; }
```

READ-ONLY: `n preflight`. Vor Enrollment erwartet not_enrolled, danach checked.
CHANGE, Admin: `n init --confirm`. Voraussetzung: Preflight geprüft, leerer privater
jobs-Pfad. Effekt: native Bindung und SQLitequeue, **keine Jobfreigabe**; Rückweg:
keinen Job freigeben, DB/Enrollment erhalten. Bei Fremddaten/Quarantäne anhalten.

READ-ONLY, cs50op: `n review --source-ref SOURCE_REF --workflow-id cs50p_first`.
Hashes, Stufen, Grenzen und review_id privat prüfen.
CHANGE: `n approve --source-ref SOURCE_REF --workflow-id cs50p_first --review-id REVIEW_SHA --ttl 300 --confirm`.
Voraussetzung: genau dieser unveränderte Review, keine aktive Freigabe.
Effekt: ein created-Job mit einmaligem Grant, maximal 300 s gültig; JOB_ID aus
Ausgabe übernehmen. Rückweg: `n cancel --job-id JOB_ID` (CHANGE; Abbruchstatus,
Grant/Events bleiben erhalten). Jede Spec-/Code-/Inputänderung macht ihn ungültig.

CHANGE, cs50op, nach exakter Instanzfreigabe durch Admin:

```sh
sudo systemctl start --no-block cs50p-native@JOB_ID.service
```

Voraussetzung: TTL gültig, keine parallele Instanz, kein Downloaddienst aktiv.
Effekt: Verbrauchsbeleg vor C16-Start; höchstens dieser eine Job, ohne Netzwerk.
Rückweg: kontrolliertes Cancel, erforderlichenfalls Dienststop unten. Kein direkter
foreground-`run` im SSH-Terminal: Verbindungsabbruch ist dort kein Persistenzbeleg.
`Restart=no`, kein enable/Timer: Reboot/Fehler startet keinen Job automatisch neu.

READ-ONLY: `n status --job-id JOB_ID` und
`systemctl status cs50p-native@JOB_ID.service --no-pager`.
Jetzt SSH mit `exit` beenden (CHANGE nur Sitzung), VPN trennen/verbinden (CHANGE
nur Verbindung) und neu anmelden. Der Hosttest muss belegen, dass systemd weiterläuft;
in der Offlineumgebung wurde kein echter SSH-Verbindungsabbruch getestet.

READ-ONLY nach Neuverbindung, Funktion n erneut setzen; Journal als Admin:

```sh
n status --job-id JOB_ID
sudo journalctl -u cs50p-native@JOB_ID.service -n 100 --no-pager
n result --job-id JOB_ID
```

Erwartet: completed, Exit 0, geprüfte Artefakthashes und Referenzen. Ergebnis
frühestens bei completed abrufen; fehlende/korrupt referenzierte Bytes oder
Quarantäne blockieren. Dauerhafte Eingaben/Ergebnisse bleiben unter /var/lib.
CHANGE, optional Clientexport in **neue** private Datei; Voraussetzung: completed,
geprüfter Hostkey, konkrete Job-ID, genehmigtes result-Sudo. Effekt: lokale Kopie;
Rückweg: privat erhalten, keine Veröffentlichung.

```sh
(umask 077; set -o noclobber; ssh -i ~/.ssh/cs50p_operator cs50op@VPN_IP 'cd /opt/cs50p/app && sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native result --config /var/lib/cs50p-mvp/specs/controller.json --limits /var/lib/cs50p-mvp/specs/limits.json --job-id JOB_ID' > cs50p-JOB_ID-result.json)
```

READ-ONLY, Client: `sha256sum cs50p-JOB_ID-result.json`. Die Exportdatei ist ein
JSONreport; gewünschte Ergebnisdateien erst anhand seiner geprüften Pfade/Hashes
separat privat abrufen, keine öffentliche Downloadroute einrichten.

## Cancel, Stop, Crash und Resume

CHANGE: `n cancel --job-id JOB_ID`. Voraussetzung: konkrete eigene Job-ID.
Effekt: cancel_requested/cancelled; Rückweg: kein Undo/Replay, ggf. frischer Resume.
READ-ONLY: `n status --job-id JOB_ID` bis terminal. cancel_requested beweist
noch keinen beendeten Prozess. CHANGE bei notwendigem harten Dienststop:

```sh
sudo systemctl stop cs50p-native@JOB_ID.service
sudo systemctl stop cs50p-download.service
```

Voraussetzung: bekannte eigene Units; Effekt: vollständige Dienst-cgroup endet,
Download-/Jobdaten bleiben; Rückweg: erst Status/Logs untersuchen und **neu**
reviewen, kein Restart mit verbrauchtem Grant. READ-ONLY:

```sh
systemctl show cs50p-native@JOB_ID.service -p ActiveState -p SubState -p MainPID -p Result -p ControlGroup
n status --job-id JOB_ID
```

CHANGE, Admin, nur bei bestätigtem Dienstende und nichtterminalem Crashjob:
`n recover --job-id JOB_ID --confirm`. Effekt: Reconciliation unter Worker- und
Guardianlock; Rückweg: keine Zustandsrücknahme, ggf. neuer Review. Quarantäne oder
unbekannte Lifecycledateien bleiben blockiert; keine gespeicherten PIDs signalisieren.

READ-ONLY: `n review --source-ref SOURCE_REF --workflow-id cs50p_first --resume`.
CHANGE: `n approve --source-ref SOURCE_REF --workflow-id cs50p_first --resume --review-id NEW_REVIEW_SHA --ttl 300 --confirm`.
Voraussetzung: zulässiger terminaler Vorgänger, neue Prüfung; Effekt: neue Job-ID
mit previous_run_id; Rückweg: neuen Job canceln. Neuen Instanznamen vom Admin
freigeben lassen und oben starten. completed wird nicht erneut freigegeben.
Replay, paralleler Start, unbekannter/abgelaufener Grant und offline-test im
ssh-runtime müssen abgewiesen werden; keine Quarantäne löschen.

Änderungen zurücknehmen: eigene Units stoppen, Logs/Status sichern, dann nur den
aufgezeichneten alten Codestand gemäß [Update/Rückfall](cs50p_hetzner_installation.md#manuelles-update-und-rückfall)
wieder auswählen. Daten/Specs/Grants erhalten. VPN-/SSH-Rückweg steht im Preflight;
keine Coolifyänderung, kein produktives Restoreversprechen.
