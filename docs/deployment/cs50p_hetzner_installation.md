# C26-CS50P-03: minimale Erstinstallation

**HOLD, ausschließlich späterer Betreiberplan.** Zuerst
[VPN-/SSH-Preflight](cs50p_hetzner_preflight.md), danach dieses Dokument und
[Erstlauf](cs50p_first_run.md). SQLitebefund und fehlender positiver
Runtime-Neuinstallationstest bleiben Sperrgründe. Kein automatisches Deployment.
Ubuntuversion/Architektur müssen am echten Host bestätigt werden.

## Paketvorbereitung

Basis ist `2f2b410f41cd4db4e26075b891a03c6cb1ff0cd6` plus separat geprüfter
C26-CS50P-03-Patch. Erst regulär committen/pushen/reviewen; kein Merge auf master
durch diesen Auftrag. Keine ungeprüften Arbeitsbaumdateien verteilen.
Der Reviewcommit heißt im Folgenden REVIEWED_COMMIT, die neue Releasekennung RELEASE.

READ-ONLY, vertrauenswürdiger Buildrechner, im Repository:

```sh
git status --short --branch
git show --stat REVIEWED_COMMIT
git diff --check REVIEWED_COMMIT
uname -m
uv --version
```

CHANGE, neue Paketpfade auf einem Linux-Buildrechner mit passender Hostarchitektur
und CPython 3.12. Voraussetzung: exakter Reviewcommit, freigegebener Paketindex,
neue leere Zielpfade. Effekt: Sourcearchiv, neue Buildvenv und heruntergeladene
Runtimewheels, **keine Kursdownloads**; Rückweg: Dateien privat erhalten, nicht
installieren. Fehlende gepinnte Wheels blockieren, keine Versionen ersetzen.

```sh
mkdir -m 0700 cs50p-package
git archive --format=tar --output=cs50p-package/source.tar REVIEWED_COMMIT
python3.12 -m venv cs50p-package/build-venv
cs50p-package/build-venv/bin/python -m pip download --only-binary=:all: --require-hashes -r deployment/cs50p-mvp/requirements.txt -d cs50p-package/wheels
sha256sum cs50p-package/source.tar > cs50p-package/source.sha256
```

Der Requirements-Export stammt aus `deployment/runtime/uv.lock`; Hostbetrieb
benötigt kein uv und keine zweite Queue-/Containerarchitektur. Der Sourcecommit
muss die unveränderten Requirements enthalten. Buildumgebung, Wheeldateien,
Hashes und Lizenzen zusätzlich im privaten Paketmanifest erfassen. Vor Transfer
eine **neue** CPython-3.12-Testvenv mit demselben Offline-Pipinstall wie unten
erstellen, `pip check` und CLIimports prüfen. Dieser positive Closurebeleg fehlt
hier. Kein Erfolg allein aus vorhandenen Testpaketen ableiten.

CHANGE, Client: geprüftes Paket über bestehenden administrativen VPN-/SSH-Zugang
in neuen privaten Stagingpfad übertragen, z.B. `scp -r cs50p-package ADMIN@VPN_IP:cs50p-package-RELEASE`.
Voraussetzung: geprüfter Hostkey und genug Platz; Effekt: Stagingdateien im
Adminhome; Rückweg: nicht installieren, Paket erhalten. ADMIN ist das bestehende
persönliche Administratorkonto desselben Betreibers. Keine Secrets im Paket.

## Accounts, Code und persistente Daten

READ-ONLY, Server als bestehender Administrator:

```sh
id cs50p
id cs50op
ls -ld /opt/cs50p /var/lib/cs50p-mvp /var/cache/cs50p-mvp
df -h /opt /var/lib /var/cache
stat -fc %T /sys/fs/cgroup
tar -tf cs50p-package-RELEASE/source.tar
```

Bei bestehenden cs50p-Pfaden oder UID: anhalten und Eigentum/Inhalte prüfen;
keine fremden Accounts/Pfade übernehmen. Archiv vor Rootextraktion auf absolute
Pfade, `..`, Links und unerwartete Dateien prüfen; Quelle ist ausschließlich das
reviewte `git archive`. Keine komplette Projekt-.env oder Produktionsdaten kopieren.
Architektur muss zum Wheelhouse passen; lokales Dateisystem mit WAL/flock/fsync/
renameat2 erforderlich, kein NFS. Cgroup-v2-Ausgabe erwartet `cgroup2fs`.

CHANGE, Admin; Voraussetzung: alle folgenden Zielpfade neu. Effekt: gesonderter
unprivilegierter Account ohne Login, root-eigener Code/venv, private persistente
Daten. Rückweg: nur eigene Dienste stoppen und neue Installation unbenutzt lassen;
Accounts, Inputs, DB und Ergebnisse erhalten. Kein userdel/rm/clean.

```sh
sudo useradd --system --user-group --home-dir /var/cache/cs50p-mvp --shell /usr/sbin/nologin cs50p
sudo install -d -m 0755 /opt/cs50p /opt/cs50p/releases /opt/cs50p/releases/RELEASE /opt/cs50p/releases/RELEASE/app
sudo install -d -o cs50p -g cs50p -m 0700 /var/lib/cs50p-mvp /var/cache/cs50p-mvp
sudo install -d -o cs50p -g cs50p -m 0700 /var/lib/cs50p-mvp/specs /var/lib/cs50p-mvp/archive /var/lib/cs50p-mvp/catalog /var/lib/cs50p-mvp/reports /var/lib/cs50p-mvp/jobs
sudo tar --no-same-owner --no-same-permissions -xf cs50p-package-RELEASE/source.tar -C /opt/cs50p/releases/RELEASE/app
sudo python3.12 -m venv /opt/cs50p/releases/RELEASE/venv
sudo /opt/cs50p/releases/RELEASE/venv/bin/python -m pip install --no-index --only-binary=:all: --find-links=cs50p-package-RELEASE/wheels --require-hashes -r /opt/cs50p/releases/RELEASE/app/deployment/cs50p-mvp/requirements.txt
sudo ln -s /opt/cs50p/releases/RELEASE/app /opt/cs50p/app
sudo ln -s /opt/cs50p/releases/RELEASE/venv /opt/cs50p/venv
```

Falls Python 3.12/venv/CA-Zertifikate fehlen: vorab separater Paketreview,
CHANGE `sudo apt-get install python3.12-venv ca-certificates`; Voraussetzung:
Pakettransaktionsvorschau geprüft. Effekt: Hostpakete; Rückweg: keine pauschale
Deinstallation gemeinsam genutzter Pakete. Kein globales Upgrade/Reboot.

Specs nicht aus Tests kopieren. Prüfen und mit 0600 an cs50p übergeben:
limits.json aus `deployment/cs50p-mvp/limits.json.example`, Discoverymanifest und
hashgebundene Snapshots sowie echte Quellenfreigaben. Die konkrete Erzeugung von
Batch, Katalog und Controller steht im [nativen Quellenablauf](cs50p_native_operator_guide.md#quellen-download-und-materialreview).
`native_uid` muss `id -u cs50p` entsprechen, Modus `ssh-runtime`, identities leer.
Keine Testtoken, synthetischen Manifeste oder offline-test-Grants auf den Host.
CHANGE `sudo install -o cs50p -g cs50p -m 0600 REVIEWED_LIMITS /var/lib/cs50p-mvp/specs/limits.json`;
Voraussetzung: Zieldatei neu, Inhalt geprüft. Effekt: neue Specs; Rückweg: nicht
enrollen/starten; nach Enrollment niemals in-place verändern.

READ-ONLY, Integrität/Rechte und Neuinstallation:

```sh
readlink /opt/cs50p/app
readlink /opt/cs50p/venv
sudo -u cs50p test ! -w /opt/cs50p/app/scripts/cs50p_native.py
sudo -u cs50p test ! -w /opt/cs50p/venv/bin/python
/opt/cs50p/venv/bin/python -m pip check
cd /opt/cs50p/app
sudo -u cs50p /opt/cs50p/venv/bin/python -c 'import ssl,sqlite3,httpx,bs4,pymupdf,pydantic,pydantic_settings,returns; print(sqlite3.sqlite_version,ssl.OPENSSL_VERSION)'
sudo -u cs50p /opt/cs50p/venv/bin/python -m scripts.cs50p_native --help
```

Test-/Importbefehle mit `PYTHONDONTWRITEBYTECODE=1` ausführen, wenn Rootpakete keine
Bytecodecaches erhalten sollen. Keiner dieser Tests ersetzt Ressourcenabnahme.

## systemd und Zugriff

CHANGE, Admin: nur die beiden nativen Profile installieren. Voraussetzung: neue
Unitnamen, Code-/Spec-/Pfadreview und positiver Runtimecheck. Effekt: manuell
startbare Services; Rückweg: stoppen, eigene Units nach Review zurücknehmen und
daemon-reload; Daten erhalten. Kein enable, Timer oder Legacyworker parallel.

```sh
sudo install -m 0644 deployment/cs50p-mvp/cs50p-download.service /etc/systemd/system/cs50p-download.service
sudo install -m 0644 deployment/cs50p-mvp/cs50p-native@.service /etc/systemd/system/cs50p-native@.service
sudo systemctl daemon-reload
```

READ-ONLY:

```sh
sudo systemd-analyze verify /etc/systemd/system/cs50p-download.service /etc/systemd/system/cs50p-native@job_review.service
sudo systemd-analyze security --offline=yes /etc/systemd/system/cs50p-download.service /etc/systemd/system/cs50p-native@.service
systemctl cat cs50p-download.service cs50p-native@job_review.service
systemctl show cs50p-native@job_review.service -p MemoryMax -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec -p RuntimeMaxUSec -p KillMode -p Restart
```

| Profil | CPU | RAM / Swap | Tasks | Zeit | Netzwerk / Schreibpfade |
| --- | --- | --- | --- | --- | --- |
| Download | 50 % eines Kerns | 256 MiB / 0 | 32 | Starttimeout 600 s | HTTPS/DNS; archive, reports, cache |
| Native Instanz | 100 % eines Kerns | 1 GiB / 0 | 128 | 120 s, Stop 30 s | PrivateNetwork, AF_UNIX; jobs, cache |

90-s-C16-Adapterlimit und eigene RLIMITs gelten zusätzlich. Downloadpolicy begrenzt
Materialanzahl/Bytes/Transfer; Werte im reviewed batch/report kontrollieren.
Konkret: höchstens drei Materialien à 1 MiB, 6 MiB akzeptierte Payload über alle
Versuche, ein begrenzter Downloadretry, 10 s I/O und 45 s Downloaddeadline;
Details und Resolvergrenze in der [Downloadpolicy](cs50p_mvp_download_policy.md).
5-GiB-Reserve und Bytebudgets sind **keine Diskquote**. Keine Gesamtslice für
mehrere Download-/Jobdienste vorhanden: ersten Download und Worker nacheinander
ausführen, Coolify-Auslastung dabei überwachen. Persistent: archive, catalog, jobs
(DB/WAL/SHM, Grants, Events, Workflowergebnisse), reports. Journalpersistenz auf
dem Host prüfen; bestehende globale journald-Konfiguration hier nicht verändern.
Jobstatus/Events bleiben unabhängig davon in SQLite, Reports/Resultate als Dateien.

CHANGE, Admin: gezielte sudo-Regeln per `sudo visudo -f /etc/sudoers.d/cs50p-operator`
vorbereiten. Voraussetzung: cs50op ist alleiniger Betreiber; Pfad vorher neu und
Regeln unabhängig geprüft. Nur feste root-eigene CLI-Module mit einzelnen
Subkommandos als cs50p erlauben; kein `sudo python`, `sudo -u cs50p sh`, keine
Schreibrechte an Code/venv, keine docker-/systemd-journal-Gruppe. Für den ersten
Job exakt dessen systemctl-Instanz und die Downloadunit zulassen. Beispiel
**nach** Ersetzen von JOB_ID (keine wildcard-Unitfreigabe):

```sudoers
cs50op ALL=(cs50p) /opt/cs50p/venv/bin/python -m scripts.cs50p_native preflight *, /opt/cs50p/venv/bin/python -m scripts.cs50p_native review *, /opt/cs50p/venv/bin/python -m scripts.cs50p_native approve *, /opt/cs50p/venv/bin/python -m scripts.cs50p_native status *, /opt/cs50p/venv/bin/python -m scripts.cs50p_native result *, /opt/cs50p/venv/bin/python -m scripts.cs50p_native cancel *
cs50op ALL=(root) /usr/bin/systemctl start --no-block cs50p-download.service, /usr/bin/systemctl stop cs50p-download.service, /usr/bin/systemctl start --no-block cs50p-native@JOB_ID.service, /usr/bin/systemctl stop cs50p-native@JOB_ID.service
```

Effekt: cs50op kann nur diese Werkzeuge/Dienste als Dienstbenutzer/root aufrufen.
CLI-Argumentwildcards sind Teil der vertrauenswürdigen Einzelbetreibergrenze und
gewähren Zugriff auf alle für cs50p zugänglichen Specs, keine Mehrmandantenisolation.
Init/Plan/Seal/Recover und private Logabfrage zunächst durch das bestehende
Administratorkonto ausführen; keine allgemeine sudo-Erweiterung nötig. Nach
Approval trägt der Admin die konkrete Job-ID ein. READ-ONLY `sudo visudo -cf
/etc/sudoers.d/cs50p-operator` und `sudo -l -U cs50op`; bei Fehlern nicht fortfahren.
Rückweg: ausschließlich diese neue Sudoersdatei durch Admin zurücknehmen, validieren.
Hostprüfung dieses Templates steht aus; Distributionpfade vorher kontrollieren.

## Manuelles Update und Rückfall

READ-ONLY: aktuelle Symlinkziele, Dateihashes, Config-/Limitsbytes und letzte Jobs
privat erfassen. CHANGE: benannte Jobinstanz und Downloadunit stoppen (Erstlauf),
danach keine aktive cgroup/Worker mehr; kein automatischer Wiederanlauf.
Neue Release-/Venvpfade wie oben anlegen und prüfen. Grant wird durch geänderten
Code ungültig; keine Freigabe über ein Update hinweg verwenden.

CHANGE, Admin, nur nach beendetem Job und Review der Alt-/Neuziele; Effekt:
atomarer Wechsel je Symlink, nicht über beide gleichzeitig. Kein Dienststart
dazwischen. Rückweg: dieselben Befehle mit den aufgezeichneten **alten** Zielen.

```sh
sudo ln -s /opt/cs50p/releases/NEW_RELEASE/app /opt/cs50p/app.next
sudo ln -s /opt/cs50p/releases/NEW_RELEASE/venv /opt/cs50p/venv.next
sudo mv -T /opt/cs50p/app.next /opt/cs50p/app
sudo mv -T /opt/cs50p/venv.next /opt/cs50p/venv
```

Voraussetzung: `.next` existiert nicht, aktuelle Ziele unmittelbar zuvor geprüft.
Nach Wechsel Imports/Preflight wiederholen. Enrollment/Configbindung verhindert
stille Spezifikationswechsel. Bei geändertem Scope neuer leerer Workspace nach
Review; vorhandene Jobs/Grants nicht umschreiben. Kein Datenbankdowngrade,
Quarantänereset, Replay oder automatisches Löschen alter Releases. Bei unklarem
Datenzustand stoppen und untersuchen. C26-04 Backup/Restore bleibt DEFERRED;
diese Rückkehr zum Code ist kein nachgewiesenes Datenrestore.
