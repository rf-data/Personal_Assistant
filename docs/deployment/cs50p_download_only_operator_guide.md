# C26-CS50P-04: Download-only Hetzner-Pilot

**HOLD. Keine Produktionsfreigabe.** Dieses Paket ist für den manuellen Hostreview
vorbereitet. Vor einem echten Start fehlen der positive Neuinstallationsbeleg aus
dem vollständigen gepinnten Wheelhouse und der Ubuntu-24.04-/systemd-255-Hostreview.
C26 und C16 bleiben HOLD; das SQLite-Konkurrenzproblem wird hier nicht repariert.
[Validierung und Sicherung](cs50p_download_only_validation.md).

Diese Anleitung ist ausschließlich für den Download-only-Pilot maßgeblich.
Die C26-CS50P-03-/Native-Anleitungen bleiben historische Evidenz und werden **nicht**
mit diesem Ablauf kombiniert. Ein bestehender administrativer SSH-Zugang über
Tailscale genügt; keine neuen SSH-/VPN-/Firewall-/Docker-/Coolify-Einstellungen.
Alle Hostbefehle unten sind zukünftige Betreiberaktionen, hier nicht ausgeführt.
CHANGE benötigt jeweils die manuelle Freigabe des Betreibers für genau den Schritt.

## Lieferumfang und Voraussetzungen

`deployment/cs50p-download-only/` enthält `install.py`, `pilot.py`, `preflight.py`,
`cs50p-download-only.service`, Limits und verweigernde Approvalbeispiele.
Der Installer benötigt Python-Standardbibliothek und Rootrechte, die Runtime einen
separaten Systembenutzer `cs50p-download` ohne Login oder zusätzliche Gruppen.
Der bestehende Benutzer `cs50p` wird nicht übernommen.

| Pfad | Eigentum / Zweck |
| --- | --- |
| `/opt/cs50p-download-only/releases/RELEASE/app` und `venv` | root; Code lesbar, nicht durch den Dienst schreibbar |
| `/opt/cs50p-download-only/releases/RELEASE/specs` | Dienstbenutzer, 0700/0600; im Dienst schreibgeschützt |
| `/opt/cs50p-download-only/current` | root; ein atomarer Zeiger auf Code, Venv und Specs zusammen |
| `/var/lib/cs50p-download-only/archive` | Dienstbenutzer 0700; Downloads, Receipts, Versuchsnachweise |
| `/var/lib/cs50p-download-only/reports` | Dienstbenutzer 0700; permanente JSON-Reports |
| `/var/cache/cs50p-download-only` | Dienstbenutzer 0700; privates Home/Cache |
| `/opt/.cs50p-download-only-install.lock` | root, 0644; persistentes flock für Installer und laufenden Dienst |

Es werden keine Jobs-/Katalog-/SQLitepfade, Controller, Enrollment oder Grants
angelegt. Die bekannten Worker-/Native-Einstiegsskripte werden nicht mitinstalliert.
`cs50p-worker.service` und `cs50p-native@.service` erhalten `/dev/null`-Masken.
Vorhandene fremde Units, einzelne Native-Instanzen, Drop-ins, Timer,
Aktivierungslinks, Accounts oder Datenpfade blockieren die Erstinstallation.
Kein automatisches Übernehmen oder Stoppen solcher Ressourcen.
Root kann Schutzmaßnahmen bewusst verändern; das Paket schützt vor versehentlichem
Start durch den angebotenen Betriebsablauf, nicht vor einem bösartigen Administrator.

Hostvoraussetzungen: Ubuntu 24.04, Python 3.12 einschließlich `venv`/pip,
CA-Zertifikate, systemd mindestens 255 mit cgroup v2, `runuser`, `useradd`, `findmnt`,
`stat`, `systemd-analyze`, lokale ext4/xfs/btrfs-Pfade, funktionierendes flock,
fsync und Linux-renameat2. Mindestens 5 GiB freie Reserve **nach** Installation;
zusätzlich Platz für Source, Wheelhouse, neue und erhaltene Releases einplanen.
Keine NFS-/Overlay-Datenpfade für den Pilot. Die Ressourcenlimits sind keine
Diskquote und ersetzen keine Prüfung der parallel laufenden Coolify-Last.

## 1. Geprüftes Paket bauen (Buildrechner)

READ-ONLY: sauberen Reviewcommit ermitteln. C26-CS50P-03 muss enthalten sein:
`81db9ed3f5fc7e0c3d6952b438f015ae6521af3c`. Diese Lieferung ist wegen
Git-Schreibschutz zunächst ein Patch; zuerst in einer beschreibbaren Umgebung
anwenden, reviewen und committen. `REVIEWED_COMMIT` muss danach auch C26-CS50P-04
enthalten. Keine ungeprüften Arbeitsbaumdateien verteilen.

```sh
git status --short --branch
git show --stat REVIEWED_COMMIT
git merge-base --is-ancestor 81db9ed3f5fc7e0c3d6952b438f015ae6521af3c REVIEWED_COMMIT
```

CHANGE, Linux-Buildrechner mit passender Hostarchitektur/CPython 3.12: neue private
Paketpfade und Venv anlegen. Die pip-download-Zeile benötigt den separat freigegebenen
Paketindex und lädt ausschließlich Runtimewheels. Keine Kursmaterialabrufe.
Die Pfadvariablen bezeichnen ausschließlich neu angelegte Taskpfade.

```sh
umask 077
mkdir cs50p04-package
mkdir cs50p04-package/source
mkdir cs50p04-package/wheels
git archive --format=tar --output=cs50p04-package/source.tar REVIEWED_COMMIT
tar --no-same-owner --no-same-permissions -xf cs50p04-package/source.tar -C cs50p04-package/source
python3.12 -m venv cs50p04-package/check-venv
cs50p04-package/check-venv/bin/python -m pip download --only-binary=:all: --require-hashes -r cs50p04-package/source/deployment/cs50p-mvp/requirements.txt -d cs50p04-package/wheels
cs50p04-package/check-venv/bin/python -m pip install --no-index --only-binary=:all: --find-links=cs50p04-package/wheels --require-hashes -r cs50p04-package/source/deployment/cs50p-mvp/requirements.txt
cs50p04-package/check-venv/bin/python -m pip check
```

Abbruch bei fehlenden Wheels/Versionen/Hashes. Keine Versionsänderung, kein
system-site-packages und kein Rückgriff auf die bestehende Testvenv. Positiven
Buildbeleg, Python-/Architekturversion und Wheelhashes für den Review sichern.
Zusätzlich aus `source` mit `PYTHONDONTWRITEBYTECODE=1 ../check-venv/bin/python
-c 'import ssl,sqlite3,httpx,bs4,pymupdf,pydantic,pydantic_settings,returns; import scripts.cs50p_mvp'`
die echten Runtimeimporte prüfen.
Die Buildvenv nicht auf den Host kopieren. Rückweg: Paket privat behalten,
Hostinstallation auslassen; keine vorhandenen Umgebungen löschen.

## 2. Specs vorbereiten (offline, Buildrechner)

CHANGE: `cs50p04-package/specs` neu anlegen; darunter `snapshots/` mit dem bereits
geprüften Discoverymanifest `manifest.json` und allen darin referenzierten Dateien
in ihrer relativen Struktur. Keine neuen Discovery-/Kursdownloads in diesem Schritt.
Die folgenden Befehle setzen ein vollständiges, zuvor geprüftes Snapshotpaket voraus.
Absolute Manifestpfade im Quellbatch sind Buildpfade; der Installer bindet sie an
seinen konkreten Releasepfad um und berechnet den Batchhash neu. Identitäten,
URLs und Snapshotbytes/-hashes bleiben erhalten; die reguläre `load_batch`-
Neuplanung validiert das umgebundene Paket vor dem Releasewechsel erneut.
Nur Batch-v1, ein bis drei HTML-/PDF-Materialien aus `cs50_python`; kein
Assignment-/Code-/Media-Batch. `--resource` für höchstens drei explizite IDs wiederholen.

```sh
mkdir -m 0700 cs50p04-package/specs
cp cs50p04-package/source/deployment/cs50p-download-only/limits.json.example cs50p04-package/specs/limits.json
cp cs50p04-package/source/deployment/cs50p-download-only/approvals.json.example cs50p04-package/specs/approvals.json
```

Snapshots jetzt aus dem freigegebenen privaten Reviewpaket nach `specs/snapshots/`
übernehmen. Danach, vom Repositoryroot des exportierten `source` aus (Paketpfade
im folgenden Beispiel relativ zu `source`):

```sh
PYTHONDONTWRITEBYTECODE=1 ../check-venv/bin/python -m scripts.cs50_batch plan --manifest "$(realpath ../specs/snapshots/manifest.json)" --course cs50_python --resource REVIEWED_SOURCE_ID --output "$(realpath ../specs)/batch.json" --limits ../specs/limits.json
```

READ-ONLY: Batch, Snapshotclosure, URLs und maximal drei IDs prüfen. CHANGE:
`approvals.json` mit konkreten geprüften `SourceApproval`-Einträgen ergänzen;
`approval-entry.json.example` zeigt das Schema, erteilt aber keine Freigabe.
Zweck, Lizenz/Attribution, robots, Aufbewahrung, Widerruf und Reviewreferenz
materialbezogen ausfüllen. Keine Platzhalter/Synthetic-Referenzen übernehmen.
`expected_sha256` nur bei unabhängig bekanntem Hash setzen; andernfalls bindet
SHA-256 lokale Integrität, ohne unabhängigen Herkunftsbeweis.

Die bestehende Admission verlangt unverändert **download=true und process=true**.
`process=true` ist hier nur eine vorhandene Quellenzulässigkeitsprüfung und startet
keine Verarbeitung. Der neue Einstiegspunkt bietet kein Process-/Workerkommando.
Wer diese Erklärung nicht abgeben kann, lässt beide false; der Pilot bleibt gesperrt.
Kein Weglassen dieser Prüfung zur Erreichung eines Downloadstarts.

CHANGE: das geprüfte Sourcearchiv, Installerdateien, Wheels und Specs mit einem
SHA-256-Dateimanifest binden, dessen Hash separat im Review sichern. Erst danach
über den vorhandenen VPN-/SSH-Zugang in einen neuen privaten Stagingpfad übertragen.
Kein Projekt-.env, Secret, Testtoken oder Controller im Paket. READ-ONLY auf dem
Host: Paketmanifest und separat freigegebenen Hash vergleichen, Archivliste prüfen.
Die Installerinputs sind vertrauenswürdige, während der Installation unveränderte
Rootinputs; Hashes ersetzen keinen unabhängigen Review des Pakets.

## 3. READ-ONLY: Host prüfen, noch nichts installieren/starten

Als bestehender Administrator, ohne Änderungen an gemeinsamer Infrastruktur:

```sh
cat /etc/os-release
python3.12 --version
systemctl --version
stat -fc %T /sys/fs/cgroup
command -v useradd runuser findmnt systemd-analyze
getent passwd cs50p-download
systemctl list-units --all 'cs50p-*'
systemctl list-unit-files 'cs50p-*'
ls -ld /opt/cs50p-download-only /var/lib/cs50p-download-only /var/cache/cs50p-download-only
df -h /opt /var/lib /var/cache
findmnt -T /var/lib
```

Neue Identität/Pfade sollten fehlen. Vorhandene unbekannte Ressourcen zuerst
separat untersuchen, nicht entfernen/adoptieren. Hostlast und freien Speicher
prüfen. Fehlendes `venv`/CA/Hostpaket erfordert einen separaten geprüften
Paketinstallationsschritt; der Pilot führt kein apt/Hostupgrade durch.

## 4. CHANGE: Installieren, gestoppt lassen

Voraussetzungen: positiver Buildbeleg, Paket-/Hostreview und manuelle Freigabe.
`SOURCE`, `WHEELS`, `SPECS` als absolute überprüfte Stagingpfade setzen;
`RELEASE` als neue eindeutige Kennung, z.B. `cs50p04-review1`.
Den Installer aus genau derselben geprüften Sourceversion aufrufen:

```sh
sudo python3 "$SOURCE/deployment/cs50p-download-only/install.py" install --source "$SOURCE" --wheelhouse "$WHEELS" --specs "$SPECS" --release "$RELEASE"
```

Effekt: Account, private Daten, neuer Rootcode/Venv, versiegelte Specs, Masken,
Downloadunit, ein Releasezeiger und `daemon-reload`. Kein Download, Start, enable,
Timer, C16 oder Admission-Enrollment. Erwartete Ausgabe `installed_stopped`.
Exakt gleiches Paket/Release ist wiederholbar. Gleiche Kennung mit anderen Bytes
oder ein unvollständiger Release wird abgewiesen. Eine fehlgeschlagene Vorbereitung
bleibt erhalten, bisheriger `current` unverändert; nach Untersuchung neue Kennung
verwenden. Ein Fehler nach Zeigerwechsel/daemon-reload ist kein erfolgreicher
Abschluss: tatsächlichen Zeiger und Unit prüfen; Dienste bleiben ungestartet.
Rückweg: gestoppt lassen, ggf. unten aufgezeichneten alten Release auswählen.

READ-ONLY nach Installation:

```sh
sudo python3 "$SOURCE/deployment/cs50p-download-only/preflight.py"
sudo systemd-analyze verify /etc/systemd/system/cs50p-download-only.service
sudo systemd-analyze security --offline=yes /etc/systemd/system/cs50p-download-only.service
systemctl cat cs50p-download-only.service
systemctl show cs50p-worker.service cs50p-native@review-blocked.service -p LoadState
systemctl show cs50p-download-only.service -p ActiveState -p UnitFileState -p MemoryMax -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec -p TimeoutStartUSec
readlink /opt/cs50p-download-only/current
```

Erwartet: Preflight checked, Worker masked, Download inaktiv/static, 50 % eines
Kerns, 256 MiB RAM/kein Swap, 32 Tasks, 600 s Gesamttimeout, Stop 30 s.
Preflight bleibt offline und schreibt keine Anwendungsdaten. Der echte Hostreview
muss zusätzliche/instanzspezifische Units und geerbte systemd-Drop-ins ausschließen.
Erst bei dokumentiertem positivem Review darf ein Betreiber den Status für diesen
Download-only-Umfang auf READY FOR HOST REVIEW bzw. seine konkrete Startfreigabe setzen.

## 5. CHANGE: Ein manuell freigegebener Downloadlauf

Voraussetzung: alle bisherigen Gates erfüllt, genaue URLs/Approvals/Limits geprüft,
keine parallele alte Downloadunit, Hostressourcen verfügbar. Kein allgemeines C26-Go.

```sh
sudo systemctl start --no-block cs50p-download-only.service
```

Der Systemmanager hält den Dienst unabhängig vom SSH-Terminal. Jetzt darf die
SSH-Sitzung beendet und später neu verbunden werden; systemd setzt den Lauf fort.
READ-ONLY nach Neuverbindung:

```sh
systemctl status cs50p-download-only.service --no-pager
systemctl show cs50p-download-only.service -p ActiveState -p Result -p ExecMainStatus -p MainPID
sudo journalctl -u cs50p-download-only.service -n 100 --no-pager
sudo find /var/lib/cs50p-download-only/reports -maxdepth 1 -type f -name 'download-*.json' -ls
```

Nach erfolgreichem oneshot ist **inactive** normal; `Result=success`,
`ExecMainStatus=0` und der neue JSON-Report `status=completed` müssen zusammenpassen.
READ-ONLY: genaue neue Reportdatei mit `sudo cat /EXACT/REPORT` prüfen, referenzierte
Raw-/Receipthashes kontrollieren. Downloads und Reports liegen auf persistenten
Hostpfaden und bleiben nach SSH-Ende/Reboot/Uninstall erhalten. Journalretention
hängt von vorhandener Hostkonfiguration ab; keine globale journald-Änderung.
Dateireports ersetzen deshalb kein dauerhaftes Journalarchiv aller Preflightfehler.

Unverändert: max. drei Materialien, 1 MiB pro Material, 6 MiB akzeptierte Payload
über Versuche, ein begrenzter Retry, DNS nur öffentliche IPs, numerisch gepinnter
Connect mit Original-TLS/SNI, TLSprüfung, URL-Allowlist, keine Redirects/Proxies,
Content-/SHA-Prüfung, atomare Veröffentlichung ohne Überschreiben. Details:
[Downloadpolicy](cs50p_mvp_download_policy.md). Es wird keine C16-Verarbeitung
oder semantische Parser-/C10-Abnahme der heruntergeladenen Dokumente behauptet.

## 6. Stop, Wiederholung, Upgrade und Rollback

CHANGE: `sudo systemctl stop cs50p-download-only.service`. Effekt: SIGTERM für
Dienst-cgroup, nach 30 s ggf. SIGKILL; persistente Daten bleiben. READ-ONLY:
`systemctl show cs50p-download-only.service -p ActiveState -p MainPID -p Result`
und Report/Journal prüfen. Erst nach belegtem Prozessende weiterarbeiten.

Ein normaler neuer Start prüft vorhandene Artefakthashes und kann vollständige,
identische Downloads wiederverwenden. Unterbrochene/fehlgeschlagene Receipts oder
`.download-*`-Reste werden nicht automatisch gelöscht/freigegeben. Bei Stop/Crash
zuerst Belege untersuchen; dieses Erstpilotpaket bietet bewusst keinen operativen
Retry-Override in der Unit. Eine spätere Retryfreigabe braucht einen separaten
konkreten Review mit unveränderten Schutzlimits; keine Ad-hoc-Direktdownloads
außerhalb der Unit und kein automatisches Recover/Entfernen von Beweisen.

READ-ONLY vor Upgrade: aktuellen `readlink`, Releasehashes und Reports sichern.
CHANGE: eigene Unit stoppen, anschließend neue geprüfte Source/Wheels/Specs mit
**neuer** Releasekennung über denselben Installbefehl installieren. Alte Releases
und Daten bleiben. Kein Start während des Wechsels; flock sperrt den Wechsel gegen
einen laufenden angebotenen Download. Preflight/Unitreview erneut ausführen.
Unveränderte Unit ist Voraussetzung; Unitänderungen benötigen einen separaten
Migrationsreview und werden nicht still ersetzt.

CHANGE für Rollback, nur bei gestopptem Dienst und bekanntem vollständigem Altrelease:

```sh
sudo python3 "$SOURCE/deployment/cs50p-download-only/install.py" rollback --release OLD_RELEASE
```

Effekt: Integritäts-/Offlinepreflight, dann atomarer Zeiger auf alten Code/Venv/Specs;
kein Start, keine Datenrücksetzung. Alte Approvalreferenzen müssen weiterhin gültig
sein; technische Hashgültigkeit ersetzt keinen erneuten Quellenreview. Kein
Schema-/SQLite-Rollback beteiligt. Fehlende/veränderte Altreleases bleiben gesperrt.

## 7. CHANGE: Uninstall ohne Datenlöschung

Nach Stop und belegtem Prozessende:

```sh
sudo python3 "$SOURCE/deployment/cs50p-download-only/install.py" uninstall
```

Entfernt ausschließlich die bytegleich eigene Downloadunit und lädt systemd neu.
Idempotent. Benutzer, Gruppen, Releases, Zeiger, Specs, Daten, Cache, Reports,
Lifecyclelock und die Worker-/Native-Masken bleiben ausdrücklich erhalten.
Keine `userdel`, `rm -rf`, Unmask-, apt-, Docker- oder Infrastrukturaktion.
Das ist der sichere Rückbau dieses Download-only-Pilots, keine Datenvernichtung.
Wiederherstellung: geprüftes ursprüngliches Paket mit ursprünglicher Releasekennung
nochmals installieren; erhaltene identische Releases werden wiederverwendet.
Eine vollständige Löschung oder spätere Workeraktivierung benötigt einen eigenen
Auftrag. READ-ONLY danach: Unit nicht mehr vorhanden, Worker weiterhin masked,
Report-/Archiveigentum und Hashes unverändert, Coolify/Docker unverändert.
