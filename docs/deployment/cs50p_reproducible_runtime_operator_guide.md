# C26-CS50P-06 – Betreiberablauf

**HOLD. C26 bleibt HOLD.** Noch kein geprüftes vollständiges Releasepaket:
Wheelbeschaffung und positive Frozen-Neuinstallation sind in der Arbeitsumgebung
blockiert. Diese Anleitung bereitet spätere, ausdrücklich freigegebene Aktionen
vor; hier wurden weder Hetzner noch echte Kursdownloads oder Hostinstallation
angesprochen. [Nachweise und offene Gates](cs50p_reproducible_runtime_validation.md).
C04-Dokumente bleiben historische Übergaben; für das neue Runtimeprofil gilt dieser
Ablauf. Keine C16-Verarbeitung, kein enable/Timer und keine Coolify-/Docker-,
Firewall-, SSH- oder VPN-Konfigurationsänderungen.

## Vorbereitung am Buildrechner (CHANGE, erst nach Review)

Vorausgesetzt: Linux x86_64 mit glibc, **CPython 3.12**, venv/ensurepip/pip,
System-CA-Datei `/etc/ssl/certs/ca-certificates.crt`, vorhandenes `uv` (hier 0.9.15).
Ziel bleibt Ubuntu 24.04 x86_64, systemd >=255, cgroup v2. Andere Plattformen
werden nicht freigegeben. Das universelle uv-Lock unterstützt zusätzlich 3.13;
Buildtool und Hostreview verlangen ausdrücklich 3.12. Interpreter, OS-Pakete,
pip-Bootstrap aus ensurepip und CA-Zertifikate sind Hostvoraussetzungen, keine
online nachinstallierten Python-Dependencies. Ihre Versionen im Buildbeleg sichern.

READ-ONLY: `git status --short --branch`, `git show --stat REVIEWED_COMMIT` und
`git merge-base --is-ancestor 6351d443afe18f806d37d64010e7050b4b5fcd73 REVIEWED_COMMIT`.
Der Reviewcommit muss C06 enthalten. Keine ungeprüften Arbeitsbaumdateien verteilen.

CHANGE: In **neuen** privaten Pfaden auf dem Buildrechner ausführen. Variablen vor
Ausführung durch konkrete absolute Pfade und den Reviewcommit ersetzen. Kein
bestehendes Paket/Cache/venv als Eingabe der Wheelbeschaffung verwenden.

```sh
# CHANGE – ausschließlich neue lokale Buildpfade
umask 077
BUILD=/ABS/NEW/cs50p06-package
mkdir -m 0700 "$BUILD"
mkdir -m 0700 "$BUILD/source"
git archive --format=tar --output="$BUILD/source.tar" REVIEWED_COMMIT src scripts deployment/cs50p-download-only docs/course_sources/cs50
tar --no-same-owner --no-same-permissions -xf "$BUILD/source.tar" -C "$BUILD/source"
python3.12 -I -B "$BUILD/source/deployment/cs50p-download-only/wheelhouse.py" fetch --wheels "$BUILD/wheels" > "$BUILD/fetch.json"
```

Ab Exit !=0 **anhalten**, Teilpaket bewahren und untersuchen; kein Start/Install.
`fetch` nutzt ausschließlich PyPI über HTTPS, `--only-binary`, `--require-hashes`,
`--no-cache-dir`, keine Umgebungscredentials/-proxies und keine sdists. Alle
13 Produktionspakete sind exakt gepinnt. Kein Versions-/Hashwechsel als Workaround.

CHANGE: **neue** Venv, Installation ohne Netzwerk, danach `pip check`, echte
Import-/TLS-Initialisierung und synthetischer HTML-Download mit Wiederverwendung.
`unshare` ist ein Buildrechner-Test, keine Host-/VPN-/Firewallkonfiguration.

```sh
# CHANGE – lokale isolierte Frozen-Abnahme, keine Kursabrufe
unshare --user --map-current-user --net python3.12 -I -B "$BUILD/source/deployment/cs50p-download-only/wheelhouse.py" verify --wheels "$BUILD/wheels" --venv "$BUILD/probe-venv" --source "$BUILD/source" > "$BUILD/frozen.json"
```

Erforderlich: Exit 0, `positive_frozen_install=true`, 13 Wheelhashes,
`pip_check` ohne Befund, exakte installierte Distributionen plus dokumentierter
Bootstrap-pip und `smoke.synthetic=true`. Ohne erlaubte Netzwerk-Namespace oder
positive Ausgabe bleibt dieser Beleg offen; keinen Erfolg behaupten. Probevenv
nicht auf Hetzner übertragen. Das Tool verweigert vorhandene Venvpfade. SHA-256
bindet die freigegebenen Artefakte; ein Hashmanifest allein erteilt keine Freigabe.
READ-ONLY zur Kontrolle des Exports (lokales stdout mit `runtime/requirements.txt`
vergleichen; keine neue Auflösung/Indexkontakte):

```sh
# READ-ONLY – uv 0.9.15, aus dem geprüften source
uv export --project "$BUILD/source/deployment/cs50p-download-only/runtime" --locked --offline --no-cache --no-dev --no-emit-project --no-header --format requirements.txt
```

CHANGE: Offline ein verweigerndes Beispiel vorbereiten. Das Skript kopiert nur die
bereits versionierten Discovery-Snapshots, validiert ihre Closure und plant genau
eine HTML-Datei. Es lädt keine URL. Die **gesamte** referenzierte Snapshotclosure
bleibt erhalten, auch wenn sie Metadaten anderer Kursseiten enthält.

```sh
# CHANGE – neue lokale Specs, keinerlei Quellenfreigabe
"$BUILD/probe-venv/bin/python" -I -B "$BUILD/source/deployment/cs50p-download-only/prepare_example.py" --output "$BUILD/specs"
```

READ-ONLY: `batch.json`, `limits.json`, `approvals.json` und Snapshothashes reviewen.
Zum Quellenreview Schritt 5 ausführen und **vor** Installation freigegebene Specs
neu versiegeln. Der Installer benötigt diese Quellenfreigaben schon für seinen
Offlinepreflight; ein `prepared_denied`-Beispiel ist absichtlich nicht installierbar.

CHANGE: Nach positivem Frozen-Test und Quellenreview Paket manifestieren. Source,
Wheels, Specs und Buildbelege zusammen prüfen. Der Manifesthash muss separat über
den Reviewkanal bekannt sein; das Manifest ist keine Signatur. Das Paket darf nur
die genannten geprüften Dateien enthalten, keine privaten Umgebungen/Secrets.

```sh
# CHANGE – Releasepaket auf dem Buildrechner; probe-venv bleibt lokal
cd "$BUILD"
find source wheels specs -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
sha256sum fetch.json frozen.json >> SHA256SUMS
sha256sum SHA256SUMS
mkdir -m 0700 transfer
# CHANGE – geprüfte Eingaben, keine Venv kopieren
cp -a source wheels specs fetch.json frozen.json SHA256SUMS transfer/
tar -cf release.tar -C transfer .
sha256sum release.tar
```

## 1. READ-ONLY – ein Host-Preflight-Befehl

Nur die separat gehashte/reviewte `host_preflight.py` muss vorab über den bestehenden
Betreiberweg in einem privaten Stagingpfad vorliegen. Kein ungeprüftes Remote-
Skript an Root pipen. Auf Hetzner als bestehender Administrator **genau einen**
Befehl ausführen; Pfad ersetzen. Keine Umleitung auf eine Hostdatei erforderlich:

```sh
# READ-ONLY – ausschließlich Bestandsaufnahme, auch ohne installierte Runtime
sudo python3 -I -B /ABS/STAGING/host_preflight.py
```

Bereitstellen: **vollständiges JSON von stdout**, Exitstatus und etwaiges stderr,
verwendeter Skripthash sowie Datum/Zeit der Ausführung. Insbesondere `os`, `systemd`,
`memory`, `swap`, `load`, `paths` mit `disk`/`mount`, `users`, `prerequisites`,
alle `commands` samt Exitcodes und `unit_paths` erhalten. Im privaten Review teilen;
IP-Adressen, Tailscale-Gerätenamen und Benutzernamen dürfen konsistent redigiert
werden, Statuswerte/Pfade/Kapazitäten/Ports/Fehler nicht entfernen. Keine Secrets
oder Inhalte privater Konfigurationen beifügen.

Die Ausgabe bleibt `HOLD/host_review_required=true`; sie ist keine automatische
Admission. Fehlende CS50P-Identität/Pfade/Units sind vor Erstinstallation erwartet.
Bestehende fremde Ressourcen blockieren Adoption. Keine Portbindung wird benötigt;
Listenerinventar dient dem Koexistenzreview. `ss`, systemd und Tailscale werden nur
abgefragt; kein Dockeraufruf, keine neue SSH-Verbindung oder Quellen-DNS-Prüfung.
Metadatenprüfung ersetzt keine echten flock/fsync/renameat2-/cgroup-Tests.

## 2. CHANGE – geprüftes Releasepaket übertragen

Erst nach Paket-/Hostreview; Betreiber nutzt seinen bereits funktionierenden
Tailscale-/SSH-Zugang. Die folgenden Befehle wurden hier **nicht ausgeführt**.
`operator@EXISTING_TAILSCALE_HOST` und den neuen privaten Stagingpfad ersetzen.

```sh
# CHANGE – nur Übertragung über den bestehenden Betreiberzugang
scp release.tar operator@EXISTING_TAILSCALE_HOST:/ABS/PRIVATE/STAGING/release.tar
```

```sh
# READ-ONLY – auf dem Host mit separat freigegebenem TAR-SHA vergleichen
sha256sum /ABS/PRIVATE/STAGING/release.tar
tar -tf /ABS/PRIVATE/STAGING/release.tar
```

CHANGE: Nach Vergleich in ein **neues**, betreibereigenes 0700-Verzeichnis entpacken
(`tar --no-same-owner --no-same-permissions -xf ... -C ...`). READ-ONLY: im entpackten
Paket `sha256sum SHA256SUMS` mit separatem Reviewhash vergleichen, dann
`sha256sum -c SHA256SUMS`. Unbekannte Zusatzdateien ausschließen. Während Root-
Installation Eingaben unverändert unter Kontrolle des Administrators halten.

## 3. CHANGE – Installation nach expliziter Betreiberfreigabe

Voraussetzung: positiver Frozenbeleg, Host-/Quellenreview, ausreichende Kapazität und
explizite Freigabe genau dieser Installation. Kein automatischer Durchlauf aller
Anleitungsschritte. Fehlende Hostpakete separat reviewen; dieses Paket installiert
kein apt-Paket. `SOURCE`, `WHEELS`, `SPECS` durch absolute geprüfte Pfade ersetzen:

```sh
# CHANGE – installiert und bleibt gestoppt
sudo python3.12 /ABS/PACKAGE/source/deployment/cs50p-download-only/install.py install --source /ABS/PACKAGE/source --wheelhouse /ABS/PACKAGE/wheels --specs /ABS/PACKAGE/specs --release cs50p06-review1
```

Erwartet `installed_stopped`, `processing_enabled=false`. Identische Wiederholung
ist erlaubt; Upgrade nur mit neuer Kennung und gestopptem Dienst. Fehler: Teilrelease
bewahren, tatsächlichen Zeiger prüfen, nicht starten; gleiche fehlerhafte Kennung
nicht wiederverwenden. Root-Code/Venv, privater Account ohne Login/Zusatzgruppen,
0700-Datenpfade/0600-Specs, atomarer Releasezeiger und persistente Worker-Masken.
Keine Datenadoption, keine Aktivierung und kein automatischer Dienststart.

## 4. READ-ONLY – installierte Unit und Runtime prüfen

```sh
# READ-ONLY
sudo python3.12 /ABS/PACKAGE/source/deployment/cs50p-download-only/preflight.py
sudo systemd-analyze verify /etc/systemd/system/cs50p-download-only.service
sudo systemd-analyze security --offline=yes /etc/systemd/system/cs50p-download-only.service
systemctl cat cs50p-download-only.service
systemctl show cs50p-download-only.service -p ActiveState -p UnitFileState -p MemoryMax -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec -p TimeoutStartUSec -p TimeoutStopUSec
systemctl show cs50p-worker.service cs50p-native@review-blocked.service -p LoadState -p ActiveState
readlink /opt/cs50p-download-only/current
```

Erwartet: Preflight `checked`; Download inaktiv/static, Worker masked/inaktiv,
50 % eines Kerns, 256 MiB RAM/0 Swap, 32 Tasks, 600 s Start-/30 s Stopgrenze.
Zusätzliche Units/Instanzen/Drop-ins und reale Speicherlast prüfen. Ubuntu-/systemd-
Abnahme ist hier noch offen; Ergebnisse dokumentieren. Nicht probeweise C16 starten.

## 5. READ-ONLY/CHANGE – genau eine Quelle freigeben

Kandidat **`https://cs50.harvard.edu/python/notes/0/`**, Format HTML,
Host `cs50.harvard.edu`, HTTPS Port 443, kein Query/Fragment/Redirect. Die URL ist
in der vorhandenen Week-0-Snapshotseite verlinkt; keine aktuelle Materialdatei wurde
abgerufen. Aktuelle Größe und Herausgeber-SHA sind **unbekannt**. Maximal 1 MiB,
6 MiB akzeptierte Response-Payload über alle Versuche, höchstens ein Retry; kein
rekursives Nachladen. Dateityp/Länge/Größe werden erst beim freigegebenen Transfer
verbindlich validiert. Transportoverhead zählt nicht zur Payloadgrenze.

READ-ONLY: Betreiber prüft konkrete Nutzung, aktuelle robots-Regeln und Material-
rechte. Die [offizielle Lizenzseite](https://cs50.harvard.edu/python/license/) nennt
CC BY-NC-SA 4.0; Zweck, Namensnennung, nichtkommerzielle Nutzung, Aufbewahrung,
Widerruf und Drittinhalte bleiben materialbezogen zu klären. Der hiesige Abruf von
`https://cs50.harvard.edu/robots.txt` scheiterte; **keine** positive robots-Abnahme.
Ein robots-Review ist keine Lizenzfreigabe. Keine Schutz-/Zugriffssperren umgehen.

CHANGE am Buildrechner: Nach ausdrücklicher URL-Freigabe reale Reviewreferenzen
statt `REPLACE_...` in **genau einem** Approval hinterlegen. `material_id` und
`source_id` aus dem erzeugten Batch unverändert verwenden. Bestehende Admission
verlangt **download=true und process=true**. Letzteres erklärt Quellenzulässigkeit,
startet aber keinen Worker; wer diese Erklärung nicht abgeben kann, bleibt gesperrt.
Kein Abschwächen dieses Gates. Bei unabhängig bekanntem SHA `expected_sha256`
eintragen, andernfalls explizite Betreiberentscheidung zur erstmaligen lokalen
Hashbindung dokumentieren. SHA ohne bekannten Vergleichswert beweist keine
unabhängige Herausgeberschaft. Anschließend Paket gemäß Vorbereitung neu hashen.
Nach Installation keine Specs editieren: geänderte Freigaben brauchen ein neues
geprüftes Release. Vor dem Start Freigabegültigkeit erneut kontrollieren.

## 6. CHANGE – erster Downloadstart (gesonderte Freigabe)

```sh
# CHANGE – erst nach allen obigen Gates und ausdrücklicher Startfreigabe
sudo systemctl start --no-block cs50p-download-only.service
```

Systemd hält den Lauf unabhängig vom SSH-Terminal. Kein `enable`, kein C16-Start,
keine parallelen Direktaufrufe. flock sperrt parallele Downloads und Releasewechsel.

## 7. READ-ONLY – Status und Logs, auch nach Neuverbindung

```sh
# READ-ONLY
systemctl status cs50p-download-only.service --no-pager
systemctl show cs50p-download-only.service -p ActiveState -p Result -p ExecMainStatus -p MainPID
sudo journalctl -u cs50p-download-only.service -n 100 --no-pager
sudo find /var/lib/cs50p-download-only/reports -maxdepth 1 -type f -name 'download-*.json' -ls
```

Nach oneshot ist `inactive` normal: `Result=success`, `ExecMainStatus=0` und der
**neue** Report `status=completed` müssen zusammenpassen. Journalretention richtet
sich nach vorhandener Hostkonfiguration; Dateireports liegen persistent/private.

## 8. READ-ONLY – Ergebnis und Wiederverwendung prüfen

```sh
# READ-ONLY – konkrete Pfade aus dem neuen Report/Materialverzeichnis einsetzen
sudo cat /var/lib/cs50p-download-only/reports/EXACT_REPORT.json
sudo cat /var/lib/cs50p-download-only/archive/EXACT_MATERIAL/receipt.v1.json
sudo sha256sum /var/lib/cs50p-download-only/archive/EXACT_MATERIAL/raw/source
sudo stat -c '%U %G %a %s %n' /var/lib/cs50p-download-only/archive/EXACT_MATERIAL/raw/source
```

Exakt eine passende URL/Identität, `verified`, Größe <=1048576 und Raw-/Receipt-SHA
prüfen; Report enthält außerdem Receipthash. Veröffentlichung erfolgt validiert,
atomar und ohne Überschreiben unbekannter Bytes. Keine `.download-*`-/Incomingreste
ignorieren/löschen. Eine **erneut freigegebene CHANGE**-Wiederholung von Schritt 6
muss im neuen Report `reused=true`, dieselben Rawbytes und keine weitere Übertragung
ergeben. Das ist lokal synthetisch getestet; am Host noch offen. Kein Verarbeitungstest.

## 9. CHANGE – Stop und kontrollierter Rückbau

```sh
# CHANGE – nur eigene Downloadunit stoppen
sudo systemctl stop cs50p-download-only.service
```

```sh
# READ-ONLY – erst bei MainPID=0 und inaktiv weiterarbeiten
systemctl show cs50p-download-only.service -p ActiveState -p MainPID -p Result
```

SIGTERM schreibt nach Möglichkeit einen interrupted-Report; nach 30 s kann systemd
SIGKILL senden. Teilreste bewahren/untersuchen; kein automatischer Retry oder Clean.
CHANGE optional, erst nach belegtem Prozessende:

```sh
# CHANGE – entfernt ausschließlich die unveränderte eigene Downloadunit
sudo python3.12 /ABS/PACKAGE/source/deployment/cs50p-download-only/install.py uninstall
```

Benutzer, Releases, Specs, Archive, Receipts, Reports, Cache, Lifecyclelock und
Worker-Masken bleiben erhalten. READ-ONLY: Unit fehlt, Daten/Rechte unverändert,
Worker weiter maskiert prüfen. Keine Benutzer-/Datenlöschung oder Unmask-Aktion.

## 10. CHANGE – Rollback

READ-ONLY vor Releasewechsel: `readlink /opt/cs50p-download-only/current` und
alte Kennung/Hashbelege notieren. Nach Stop aus Schritt 9 und erneuter Prüfung der
Gültigkeit alter Quellenfreigaben:

```sh
# CHANGE – OLD_RELEASE durch vorhandene vollständige geprüfte Kennung ersetzen
sudo python3.12 /ABS/PACKAGE/source/deployment/cs50p-download-only/install.py rollback --release OLD_RELEASE
```

Kein Start, keine Datenrücksetzung: alter gemeinsamer Code-/Venv-/Specs-Zeiger.
READ-ONLY: Schritt 4 und Zeigerprüfung wiederholen. Beim ersten Release ohne
Altrelease ist Rollback nicht verfügbar; gestoppt lassen bzw. datenbewahrend
uninstallieren. Änderungen der Unit benötigen separaten Migrationsreview.
