# CS50P-MVP: Privater Betreiberablauf

## C26-CS50P-03: aktueller Einstieg

Für den nativen Einzelbetreiberbetrieb gilt jetzt der zusammenhängende
[Erstlauf](cs50p_first_run.md) mit [VPN-Preflight](cs50p_hetzner_preflight.md)
und [Installation](cs50p_hetzner_installation.md). Der nachfolgende frühere
MVP-/v2-Ablauf bleibt historische Evidenz; keine Token-/Testkoordinatorbefehle
als native Freigabe verwenden. Gesamtstatus weiterhin HOLD, siehe
[aktuellen Befund](cs50p_mvp_release_readiness.md).

**HOLD. Alle CHANGE-Beispiele sind spätere manuelle Betreiberaktionen nach Review
und gesonderter Freigabe. Codex hat keinen Hostzugriff durchgeführt.**
Voraussetzungen und Installation: [Deploymentplan](cs50p_mvp_deployment_plan.md).
Befehle im Repositoryroot `/opt/cs50p/app`; Datenpfade sind neu und MVP-exklusiv.
`<SOURCE_REF>`, `<WORKFLOW_ID>`, `<REPORT>`, `<RESULT>` sind explizit zu ersetzende
Platzhalter; keine Copy/Paste-Freigabe für unbekannte Quellen.

## VPN / SSH zuerst lesend prüfen

Bevorzugt **normales OpenSSH mit Schlüsseln über Tailscale als Netzschicht**.
Keine automatische Aktivierung von Tailscale SSH, kein Austausch der SSHauthentifizierung.
[Tailscale beschreibt beide Betriebsweisen](https://tailscale.com/kb/1193/tailscale-ssh).
Ein Betreiber, explizit zugelassenes authentifiziertes Gerät, enge Tailnetregel nur
zum Workerhost:22. MFA und Gerätefreigabe in der bestehenden Tailnetverwaltung prüfen.
Keine Default-allow-all-Regel als Sicherheitsnachweis verwenden.

READ-ONLY, Betreiber prüft lokal/via bestehendem autorisiertem Zugang (keine Secrets ausgeben):
```sh
tailscale version
tailscale status
tailscale ip -4
sudo sshd -T | rg 'passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitrootlogin'
sudo ss -lntup
sudo ufw status verbose
systemctl is-active tailscaled ssh
```
Cloudfirewall zusätzlich lesend in Hetznerkonsole prüfen; Coolifyports/Routen unverändert.
Falls VPN fehlt: Betreiber installiert den signaturgeprüften offiziellen Client manuell
und autorisiert genau Server und Chromebook im eigenen Tailnet. Kein Shell-Pipe-
Installationsbefehl, kein Authkey in Logs; diese Anleitung erteilt keine Setupfreigabe.

READ-ONLY bezüglich Serverkonfiguration (SSH kann lokale known_hosts/Auditlogs schreiben):
```sh
ssh -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o IdentitiesOnly=yes -i ~/.ssh/hetzner_cs50p operator@<TAILSCALE_IP>
```
Hostkey zuerst über bekannten Kanal vergleichen. Zwei unabhängige neue VPN-/SSH-
Sitzungen testen, einschließlich Neuverbindung vom Chromebook. Bestehende Sitzung und
öffentlicher, bisher erlaubter Rettungszugang bleiben bis dahin offen. Hetznerkonsole/
Rescuezugang vorab auf Erreichbarkeit prüfen, keine Zugangsdaten dokumentieren.

Erst nach eigener Freigabe: Schlüssel hinterlegen (authorized_keys restriktiv),
`PubkeyAuthentication yes`, `PasswordAuthentication no`,
`KbdInteractiveAuthentication no`, Rootlogin deaktiviert; bestehende sshd-Konfiguration
mit Metadaten sichern, separate Drop-in-Datei verwenden. **Keine automatische Firewall-
oder SSHänderung durch dieses Paket.** Vor Reload READ-ONLY Syntaxprüfung:
```sh
sudo sshd -t
```
CHANGE, nur nach bestandenen VPN-/Schlüsseltests: `sudo systemctl reload ssh`.
Seiteneffekt neue Logins nach neuer Policy; Rückweg über offene Rettungssitzung/Konsole
Drop-in zurücknehmen, gesicherte Konfiguration wiederherstellen, erneut Syntax prüfen
und reload. Öffentlichen SSHzugang erst anschließend in Host-/Cloudfirewall gezielt
begrenzen; keine pauschale UFW-Neuladung, kein Defaultpolicywechsel, kein Schließen
von Coolifyports. Firewallrückweg vorher in Konsole festlegen. Bei VPNausfall Konsole/
bestehenden eingeschränkten Rettungsweg nutzen, keine öffentliche CS50P-API öffnen.

## Download starten, abmelden, später lesen

READ-ONLY Preview (keine Netzwerkverbindung):
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_mvp download --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --reports /var/lib/cs50p-mvp/reports
```
CHANGE – erster serverseitiger Downloadstart, erst nach Quellen-/Hostfreigabe:
```sh
sudo systemctl start --no-block cs50p-download.service
```
Seiteneffekt ausgehende HTTPSabrufe und Raw/Receipts/Reports; Rückweg Dienst stoppen,
Dateien privat erhalten. Danach SSH schließen und Chromebook ausschalten möglich.
Dienst gehört systemd, nicht der SSHsitzung. Kein automatischer Rebootneustart.

READ-ONLY nach erneuter SSHverbindung:
```sh
systemctl status cs50p-download.service --no-pager
systemctl show cs50p-download.service -p Result -p ExecMainStatus -p CPUUsageNSec -p MemoryPeak
sudo journalctl -u cs50p-download.service -n 100 --no-pager
sudo -u cs50p ls -l /var/lib/cs50p-mvp/reports
sudo -u cs50p cat /var/lib/cs50p-mvp/reports/<REPORT>
```
CHANGE – Download abbrechen: `sudo systemctl stop cs50p-download.service`.
Seiteneffekt SIGTERM, max. 30 s später SIGKILL; Rückweg nur expliziter neuer Versuch
nach Untersuchung. Für genehmigten Retry zuerst Teilreste/Receipts untersuchen; keine unbekannten Dateien
löschen. Danach CHANGE, unter Beibehaltung aller Dienstlimits, ein temporäres Drop-in
`/etc/systemd/system/cs50p-download.service.d/retry.conf` erstellen:
```ini
[Service]
ExecStart=
ExecStart=/opt/cs50p/venv/bin/python -m scripts.cs50p_mvp download --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --reports /var/lib/cs50p-mvp/reports --confirm --retry-failed
```
READ-ONLY, Syntax prüfen: `systemd-analyze verify cs50p-download.service`.
CHANGE: `sudo systemctl daemon-reload`, danach
`sudo systemctl start --no-block cs50p-download.service`. Seiteneffekt expliziter Retry
unter denselben Limits; Rückweg stoppen und ausschließlich dieses eigene Drop-in
nach Prüfung seiner Identität wieder entfernen, daemon-reload. Keine anderen Drop-ins
ändern. Kein foreground-SSHlauf als dauerhafter Betrieb. Nie Limits entfernen.

## Geprüfte Dateien an vorhandene Verarbeitung übergeben

CHANGE, unter cs50p, Katalogziel muss neu sein:
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch seal --batch /var/lib/cs50p-mvp/specs/batch.json --archive /var/lib/cs50p-mvp/archive --approvals /var/lib/cs50p-mvp/specs/approvals.json --limits /var/lib/cs50p-mvp/specs/limits.json --output /var/lib/cs50p-mvp/catalog/batch-001 --confirm
```
Seiteneffekt unveränderliche geprüfte Bundles/catalog.json; Rückweg nicht aktivieren,
Daten erhalten. Bei Teilfehlern nicht denselben Zielordner wiederverwenden.
Betreiber bindet den erzeugten Katalog exakt in controller.json, individuelle
C16-Identität mit coursegrant `cs50_python`, Tokenhash und private Tokendatei.
Controllerreview und gültige vorhandene C26-v2-Admission separat erforderlich;
execution/workflows bleiben bis dahin false. `deployment_gate_required` bleibt true.
Die bestehende [Gate-Dokumentation](c26d_gate_v2.md) gilt weiter. Wenn sie für native
systemd-Ausführung keine gültige Admission liefern kann, bleibt Verarbeitung HOLD;
kein Ersatzpermit und kein Wechsel auf einen ungeprüften Dockerstart.

CHANGE, nur mit freigegebenem Controller und erfüllter Admission:
```sh
sudo systemctl start cs50p-worker.service
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_workflow execute --config /var/lib/cs50p-mvp/specs/controller.json --token-file /var/lib/cs50p-mvp/specs/operator.token --source-ref <SOURCE_REF> --workflow-id <WORKFLOW_ID> --confirm
```
Seiteneffekt ein bestehender C16-Job; Rückweg kontrolliert cancel. Keine LLMs oder
Knowledge-Extraktion. SSH kann jetzt geschlossen werden. Job-ID/Workflow-ID aufbewahren.
READ-ONLY Status und vorhandene Reports/Artefakte:
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_workflow status --config /var/lib/cs50p-mvp/specs/controller.json --token-file /var/lib/cs50p-mvp/specs/operator.token --source-ref <SOURCE_REF> --workflow-id <WORKFLOW_ID>
sudo journalctl -u cs50p-worker.service -n 100 --no-pager
sudo -u cs50p cat /var/lib/cs50p-mvp/jobs/jobs/<JOB_ID>/results/<RESULT>
```
Tatsächliche relative Ergebnisnamen/Hashes stehen im Workflowreport; keine geratenen
Artefakte öffnen. Ergebnisse bleiben serverseitig. Optionaler Export in neues privates
Ziel ist CHANGE (neue Datei), Abruf per SSH/stdout ist READ-ONLY gegenüber Serverdaten.

CHANGE – einzelner Job kontrolliert abbrechen:
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_workflow cancel --config /var/lib/cs50p-mvp/specs/controller.json --token-file /var/lib/cs50p-mvp/specs/operator.token --source-ref <SOURCE_REF> --workflow-id <WORKFLOW_ID> --confirm
```
Seiteneffekt persistente Cancelanforderung und Guardiancleanup. Status bis terminal
prüfen; bei Quarantäne stoppen und untersuchen. Rückweg ausschließlich bestehendes
`resume --confirm` nach Freigabe, niemals Marker löschen oder DB/PIDs manipulieren.
CHANGE – gesamten Worker stoppen: `sudo systemctl stop cs50p-worker.service`.
Seiteneffekt Prozessgruppenstop; Ergebnisse bleiben. Rückweg erneuter manueller
Start nach Status-/Admissionprüfung; kein automatisches Wiederholen aktiver Jobs.

## Konkreter Admissionblocker

Die Bestandsprüfung von `deployment_gate.py` / `deployment_scope.py` und
`c26d_gate_v2.md` zeigt: v2 bindet derzeit einen vollständigen UI/API/Worker-
Operationscope, Image-/Containerbelege und einen ausdrücklich synthetischen
Offlinejournalmodus. Für einen einzelnen nativen systemd-Worker gibt es in
diesem Bestand keinen nachgewiesenen produktiven Admissionpfad. Eine leere neue
Queue ohne gültiges Journal wird ebenfalls abgewiesen. Daher reicht das bloße
Setzen von execution_enabled/workflows_enabled nicht zum Start.

Eine separate, überprüfte Anpassung des bestehenden Admissionvertrags an die
vereinfachte native Runtime ist vor einem echten Verarbeitungsjob nötig. Dieses
Paket hat keine solche Freigabe oder produktive Gateerweiterung implementiert.
Es erzeugt keinen synthetischen Ersatzbeleg und entfernt keine Sperre.
