# CS50P-MVP: Manueller Deploymentplan

**HOLD. Kein Deployment/Go-live durch Codex. Bestehender Coolifyworker bleibt unverändert.**
Exakte Quellbasis INT-02 `6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d` plus vollständiger
MVP-Patch und `candidate-files.sha256` in der Übergabe. SHA-256 bindet die tatsächlichen
Kandidatendateien; ein nachträglicher Commit muss zusätzlich festgehalten werden.
Kein Merge auf master, kein automatischer Push, keine Gitbereinigung.

## Übergabe in den vorbereiteten Featureworktree

Der vorbereitete Worktree `Personal_Assistant-cs50p-mvp` / `feat/c26-cs50p-mvp`
war sauber und auf der INT-02-Basis, liegt jedoch außerhalb der Schreibfreigabe
für diese Sitzung. Auch gemeinsame Gitmetadaten sind read-only. Deshalb wurden
Implementierung und Tests auf einer **vollständigen Exportkopie** dieser Basis
unter `artifacts/cs50p_mvp/source` ausgeführt; keine fremden Worktrees geändert.
Die folgenden Befehle gehören in den vorbereiteten Featureworktree.

READ-ONLY:
```sh
git status --short
git branch --show-current
git rev-parse HEAD
git apply --check ../Personal_Assistant-c26-pilot/artifacts/cs50p_mvp/cs50p-mvp.patch
```
READ-ONLY, Prüfsummen aus dem Übergabeverzeichnis (relative Manifestpfade):
```sh
(cd ../Personal_Assistant-c26-pilot/artifacts/cs50p_mvp && sha256sum -c checksums.sha256)
```
 Nur sauberer erwarteter Branch und identische
Basis sind zulässig. CHANGE (lokale Featuredateien/Commit, kein Servereffekt):
```sh
git apply ../Personal_Assistant-c26-pilot/artifacts/cs50p_mvp/cs50p-mvp.patch
git add README.md scripts/cs50p_mvp.py src/tools_materials/https_transport.py src/tools_materials/download.py src/tools_materials/storage.py src/tools_materials/batch.py tests/test_cs50p_mvp.py tests/test_cs50_material_download.py deployment/cs50p-mvp docs/deployment/cs50p_mvp_*.md
git diff --cached --check
git commit -m 'feat(cs50p): prepare bounded private server worker MVP'
```
Rückweg vor Commit: reverse-apply nur den eigenen Patch, wenn dessen Dateien seitdem
unverändert sind; sonst Daten sichern und einzeln prüfen. Nach Commit reguläres Revert.
READ-ONLY danach `git rev-parse HEAD` und `git show --stat --oneline HEAD` dokumentieren.
Push ausschließlich auf erneut ausdrücklich freigegebenen Featurebranch; kein Push
in diesem Paket durchgeführt. PR/Review ausstehend, kein automatischer Merge.

## Hostinventur und neue isolierte Laufzeit

READ-ONLY, Betreiber auf Hetzner:
```sh
uname -m
python3.12 --version
systemd --version
findmnt -T /var/lib
stat -fc %T /sys/fs/cgroup
df -h /var/lib
free -m
systemctl list-timers --all
```
Vorhandene Coolify/Dockerressourcen zusätzlich lesend inventarisieren; nichts stoppen.
Mindestens 5 GiB freie Reserve plus geschätzte Inkremente erforderlich. Den eigenen
Datenbereich auf ein begrenztes, persistentes Dateisystem/Quota legen: vorgeschlagen
2 GiB exklusives MVP-Datenvolume, Cache 128 MiB, private tmpfs (Download 32 MiB / Worker 128 MiB) und begrenzte
Journalaufbewahrung. Diese OSgrenzen müssen manuell geprüft/konfiguriert werden;
Pythonbaumlimits sind **keine Diskquota**. Die Units setzen eigene begrenzte /tmp-
tmpfs; persistenter Cache und Datenvolume benötigen weiterhin Hostquotas.
Keine bestehende Datenpartition umformatieren, keine pauschale Journalkonfiguration ändern.

CHANGE, nur nach separater Betreiberfreigabe (neuer Account/Verzeichnisse):
```sh
sudo useradd --system --no-create-home --home-dir /var/cache/cs50p-mvp --shell /usr/sbin/nologin cs50p
sudo install -d -o root -g root -m 0755 /opt/cs50p /opt/cs50p/app
sudo install -d -o cs50p -g cs50p -m 0700 /var/lib/cs50p-mvp /var/lib/cs50p-mvp/specs /var/lib/cs50p-mvp/archive /var/lib/cs50p-mvp/catalog /var/lib/cs50p-mvp/jobs /var/lib/cs50p-mvp/reports /var/cache/cs50p-mvp
```
Nur ausführen, wenn Account/Pfade nicht schon fremd verwendet werden. Seiteneffekt
neue isolierte Ressourcen; Rückweg Dienste stoppen und Account inaktiv lassen,
Verzeichnisse/Cache/venv nicht automatisch entfernen. Kein Benutzer in docker/sudo.
Geprüften Quellstand inklusive Commit-/Dateimanifest als root-owned Code nach
`/opt/cs50p/app` übertragen; alle Verzeichnisse lesbar/ausführbar für cs50p, Code für
cs50p nicht schreibbar. Venvinstallation siehe [Abhängigkeiten](cs50p_mvp_dependencies.md).
Kein Appmount in bestehendem Coolify, kein Dockersocket.

## Quellen und Policy vorbereiten

Die mitgelieferten Discovery-Snapshots dienen als vorhandener Metadatenstand, nicht als
aktuell vollständig geprüfter Livekurs. Betreiber muss konkrete Ressourcen und Provenienz
prüfen; Snapshotpfade im Batch bleiben absolute Serverpfade und werden nicht vom Laptop
übernommen. READ-ONLY Inventar ohne Materialdownload:
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch inventory --manifest /opt/cs50p/app/docs/course_sources/cs50/manifest.json
```
CHANGE (neuer hashgebundener Batch; keine Netzwerkabrufe), unter cs50p:
```sh
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50_batch plan --manifest /opt/cs50p/app/docs/course_sources/cs50/manifest.json --course cs50_python --resource resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a --output /var/lib/cs50p-mvp/specs/batch.json --limits /var/lib/cs50p-mvp/specs/limits.json
```
Vorher CHANGE: limits.json.example privat als 0600 cs50p-eigene limits.json kopieren;
SourceApproval nach vorhandener `deployment/cs50-source-approvals.json.example` ausfüllen,
exakt gegen erzeugtes Binding prüfen und eigene Token/Identität anlegen. Keine Beispiel-
freigabe übernehmen. Katalog/Controller initial gesperrt aus controller.json.example.
Rückweg neue Spezifikationen ungenutzt erhalten; Dateien werden nicht überschrieben.

DNS zum genehmigten Resolver und HTTPSegress zu den konkreten öffentlichen Kurszielen
notwendig. Anwendung erzwingt Allowlist/IPpinning; keine ungeprüfte egress-Netzwerkfreigabe
als bereits wirksam ausgeben. Worker hat PrivateNetwork, nur Unixsockets; Downloader
braucht Netzwerk. Keine neuen öffentlichen Ports; VPN/SSH siehe Betreiberleitfaden.

## Units prüfen/installieren/starten

READ-ONLY, nach vorhandener Venv auf dem Zielhost:
```sh
systemd-analyze verify /opt/cs50p/app/deployment/cs50p-mvp/cs50p-download.service /opt/cs50p/app/deployment/cs50p-mvp/cs50p-worker.service
```
CHANGE (zwei neue manuelle Units, kein Start):
```sh
sudo install -o root -g root -m 0644 /opt/cs50p/app/deployment/cs50p-mvp/cs50p-download.service /etc/systemd/system/cs50p-download.service
sudo install -o root -g root -m 0644 /opt/cs50p/app/deployment/cs50p-mvp/cs50p-worker.service /etc/systemd/system/cs50p-worker.service
sudo systemctl daemon-reload
```
Seiteneffekt Unitdefinitionen geladen, keine Enable-/Timer-/Restartautomatik.
Rückweg Units gestoppt und ungenutzt lassen; nur eigene Dateien nach Identitätsprüfung
zurücknehmen, daemon-reload. Startbefehle/Abbruch/Ergebnisabruf stehen im
[Betreiberleitfaden](cs50p_mvp_operator_guide.md).

Ausführung erst nach Gate-/Quellen-/Quota-/Build-/VPNabnahme. Das Paket erzeugt kein
Admissionpermit. Insbesondere ist die vorhandene C26-Gate-/Image-/Driverkette für das
native Profil noch nicht positiv belegt. Weder gate_required=false noch ein Dummypermit
oder ein direkter ungeprüfter Executorstart sind zulässige Abkürzungen.

## Update und Rückfall

Manuelles Update: Worker/Download kontrolliert stoppen (CHANGE); Status, eigene Daten
und aktuelle Code-/Venvrevision lesend prüfen. Neue freigegebene Revision in einen
separaten root-owned Releasepfad exportieren, private Spec-/Kataloghashes und Gates neu
prüfen. Keine automatische Queue-/DBmigration, kein In-place-Datenumbau. Erst danach
Unit-Arbeitspfad/Interpreter geprüft umstellen (CHANGE; Unitbackup davor).
Rückweg Stop, alte Unit/Code-/Venvrevision wiederherstellen, daemon-reload; persistente
Daten erhalten und Kompatibilität vor Neustart prüfen. Der bisherige Coolifyzustand
wurde nie verändert und bleibt der unveränderte Rückfallstand. Backup/Restore und
vollständiges Produktionsmonitoring sind weiterhin zurückgestellt.

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
