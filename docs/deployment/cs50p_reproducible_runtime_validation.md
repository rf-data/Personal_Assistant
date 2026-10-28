# C26-CS50P-06 – Validierung und Übergabe

28.10.2026. **HOLD**, auch für die isolierte Installation; **C26 gesamt HOLD**.
Ein reproduzierbarer Installationsweg und eine lesende Hostinventur liegen vor.
Ein positives Frozen-Wheelhouse oder eine Ubuntu-/systemd-255-Abnahme werden nicht
behauptet. [Ausführbarer Betreiberleitfaden](cs50p_reproducible_runtime_operator_guide.md).

## Git-Basis und Eigentum

Basisbranch `feat/c26-cs50p-04-download-only`, exakter HEAD
`6351d443afe18f806d37d64010e7050b4b5fcd73` (Elterncommit
`81db9ed3f5fc7e0c3d6952b438f015ae6521af3c`). Lokaler HEAD, Trackingref und live
über den GitHub-Connector gelesener Branch stimmen überein:
[gesicherte Basis](https://github.com/rf-data/Personal_Assistant/commit/6351d443afe18f806d37d64010e7050b4b5fcd73).
Shell-`git ls-remote` scheiterte an DNS; diese Abfrage wurde durch den **lesenden**
GitHub-Connector ersetzt. Keine Remoteänderung und kein Push/Merge/PR-Schreibzugriff.

Der bereitgestellte C04-Arbeitsbaum hatte keine getrackten Änderungen, aber vier
vorhandene ungetrackte Dateien: `artifacts/c26_cs50p_04/handoff/c26-cs50p-04.patch`,
`checksums.sha256`, `source-checksums.sha256` sowie
`artifacts/c26_cs50p_04/install-tests.xml`. Sie wurden nicht übernommen/verändert.
C04-Validierung, Betreiberhandbuch, historische C03-/C04-Belege und Schutzgrenzen
wurden gelesen und nicht überschrieben. C05 und andere Aufgaben bleiben unberührt.

Die gemeinsame `.git`-Verwaltung ist schreibgeschützt. Innerhalb des erlaubten
Projektpfads wurde daher ausschließlich aus dem gesicherten Gitcommit eine
**separate lokale Bare-Kopie ohne Hardlinks** erstellt und ihr eigener persistenter
Feature-Worktree angelegt. Das ist keine Umgehung für Schreibzugriffe auf das
ursprüngliche Repository. Taskeigene Git-Artefakte unter dem gelieferten C04-Pfad:

- `.c26-cs50p-06/repository.git`: eigene Objektkopie/Refs, Ursprung auf GitHub gesetzt.
- `.c26-cs50p-06/worktree`: eigene Änderungen und dauerhafte Dokumente.
- Branch `feat/c26-cs50p-06-reproducible-runtime` nur in dieser separaten Gitkopie.
- Die lokale Basiskopie `feat/c26-cs50p-04-download-only` dient als Referenz.

Kein fremder Checkout/Branch/Worktree, keine Daten, Venv oder Stash entfernt.
Die Dokumente sind **noch nicht in `master` integriert**. Das explizite Push-/Merge-
Verbot verhindert hier den Abschluss des Repository-Lifecycles. Eigene Gitkopie,
Branch und Worktree bleiben deshalb persistent erhalten; Integration/Review und
spätere exakt begrenzte Bereinigung bleiben pending. Nicht aus dem ursprünglichen
Repository auf den gleichnamigen Branch schließen: die neue Ref liegt separat.

## Tatsächliche Runtime-Closure

Produktionsprofil `deployment/cs50p-download-only/runtime/`, mit vorhandenem
`uv 0.9.15`; Ursprung der Pins/Artefakthashes ist `deployment/runtime/uv.lock`.
Die bestehende allgemeine Runtime und `deployment/cs50p-mvp/requirements.txt`
bleiben unverändert. Keine neue Paketverwaltung oder Versions-/Hashlockerung.
Der separate Lock wurde offline aus der vorhandenen Closure abgeleitet, um die
neue Projektmetadatenwurzel ergänzt und auf Produktions-/Devgraph reduziert;
`uv export --locked --offline --no-cache --no-dev --no-emit-project --no-header`
prüft den Projekt-/Lockzustand. Der Export enthält **13** Produktionspakete.

| Direkte Dependency | Downloadpfad / Begründung |
| --- | --- |
| `httpx==0.28.1` | `scripts.cs50p_mvp`, MaterialDownloader, Budgettransport und tatsächlicher HTTPS-/TLS-Transport |
| `pydantic==2.13.4` | Batch, Approval, Snapshot-, Material- und Receiptverträge; SHA-/Identitätsbindung |
| `beautifulsoup4==4.15.0` | Gespeicherte Discoveryseiten neu planen/validieren, auch vor einem reinen PDF-Download |

Transitiv exakt: `annotated-types==0.8.0`, `anyio==4.14.2`,
`certifi==2026.7.22`, `h11==0.16.0`, `httpcore==1.0.9`, `idna==3.19`,
`pydantic-core==2.46.4`, `soupsieve==2.9.2`, `typing-extensions==4.16.0`,
`typing-inspection==0.4.4`.

PDF-Parser `pymupdf`, Settings/returns/typer/yaml/tenacity/dotenv gehören nicht zur
Downloadruntime. Vorhandene Importketten enthalten zwar wiederverwendete C16-/C18-
Module, instanziieren/starten aber keine Worker. Parserimporte erfolgen erst bei
Verarbeitung. Ein neuer Smokeprozess sperrt diese Zusatzimporte sowie pytest
explizit, initialisiert den echten HTTPX-/TLS-Transport ohne Netz, lädt/prüft den
vorhandenen Snapshotplan und führt nur synthetische Mocktransfers aus. PDFbytes
werden heruntergeladen/validiert, niemals geparst. Keine `src/`-Änderungen nötig.
Devpakete pytest/ruff stehen nur in der Devgruppe. Bestehende Tests benötigen darüber
hinaus ihre bisherigen synthetischen PDF-/YAML-Fixtureabhängigkeiten; diese wurden
nicht zu Produktionsabhängigkeiten erklärt oder auf dem Host installiert.

## Frozen-Wheelhouse: belastbare Aussagegrenze

`wheelhouse.py fetch` benötigt einen **neuen**, leeren Zielpfad und lädt nur gepinnte
hashgebundene Wheels vom expliziten HTTPS-Index. `check` prüft lesend die vollständige
Closure, Versionen und Hashes, lehnt fehlende/zusätzliche/doppelte Artefakte, andere
Dateitypen und Symlinks ab. `verify` erzeugt eine neue CPython-3.12-Venv, installiert
mit `--isolated --no-cache-dir --no-index --only-binary=:all: --require-hashes`,
prüft `pip check`, echte Imports/TLS, synthetischen Transfer/Reuse und die exakten
installierten Distributionen. Kein system-site-packages, lokaler Paketcache oder
Online-Fallback. Prüfung im separaten Netzwerk-Namespace ist dokumentiert.
Installer nutzt dieselbe Produktionsliste und Artefaktprüfung **vor** User-/Release-
Mutation. `pip` bleibt Bestandteil des bereits vorhandenen Installationswegs.

**Tatsächlicher positiver Frozen-Test: nicht möglich.** Der reale Fetchversuch
brach Exit 1 im pip-Unterprozess ab: `No matching distribution found for
annotated-types==0.8.0`; das Tool meldet Exit 2 und `positive_frozen_install=false`.
Separate Resolverproben für `pypi.org`, `files.pythonhosted.org`, `github.com` ergeben
jeweils `gaierror`, errno -3, `Temporary failure in name resolution`. Kein Wheel
wurde beschafft. Die vollständige Verify-Routine sperrt danach korrekt vor
Installation: alle 13 Wheels fehlen. Ihre positiven Install-/Distributionsprüfungen
bleiben bis zu einer zugänglichen Buildumgebung unbestätigt. Kein Cacheersatz,
kein TLS-Bypass, kein Connector-Binärtransfer als Ersatzbeleg.

Der lokal vorhandene CPython 3.12.12 hat keine funktionierende Standard-CA-Suche.
Der Fetchpreflight verwendet deshalb explizit das vorhandene Ubuntu-/Debian-
Systembundle `/etc/ssl/certs/ca-certificates.crt`; dessen Laden gelang. Die
HTTPS-Runtime bezieht ihr Bundle aus dem gepinnten certifi-Paket. Ein CA-Fehler
wird weiterhin gesperrt. Das ist kein Nachweis eines erfolgreichen HTTPS-Abrufs.

**Echte negative Fresh-Venv-Prüfung:** Venv tatsächlich mit ensurepip erstellt,
danach im Netzwerk-Namespace echte pip-Installation erst gegen leeres Wheelhouse
und die vollständige Produktionsliste: Exit 1, fehlende Dependency. Anschließend
ein ausschließlich synthetisches beschädigtes Wheel gegen seinen ursprünglichen
Hash: Exit 1, Hashfehler. Der Negativbeleg ist kein installierbares Produktionswheel.

Belege in `artifacts/c26_cs50p_06/`: `wheelhouse-fetch.json`,
`wheelhouse-verify.json`, `network-blocker.json`, `negative-fresh-venv.json`.

## Validierung und Hostgrenze

Lokale Umgebung: Debian 12, systemd 252, Linux x86_64, CPython 3.12.12 aus der
bereits vorhandenen isolierten Testvenv. Sie wurde nicht verändert oder als
Frozen-Runtime ausgegeben. Tests mit separatem User-/Netzwerk-Namespace und
`tests.offline_guard`; keine Quellen-/Hostverbindung.

| Anforderung | Tatsächlich geprüft / Grenze |
| --- | --- |
| Erstinstallation und Wiederholung | Reale Dateibytes/Rechte/Symlinks im neuen temporären Dateibaum; Systemkonto, systemctl und positiver Runtimeinstall über aufgezeichneten Adapter. Kein Root-/Ubuntuinstallationsbeleg |
| Releasewechsel und Rollback | Gemeinsamer atomarer Code-/Venv-/Specs-Zeiger, unveränderliche Releasekennung, defekte Releases gesperrt; bisheriger Zeiger bleibt bei fehlenden/beschädigten Artefakten erhalten |
| Fehlende Dependency / beschädigtes Wheel | Echte Offline-pip-Abbrüche in neuer Venv; zusätzlich realer Artefaktchecker im Installeradapter vor Releaseanlage |
| Konfiguration und Rechte | 0700-/0600-Pfade/Specseal, root-eigener Code/Venv lesbar für Account, Symlinks/fremde Ressourcen abgewiesen; echte systemd-UID-/cgroup-Wirkung offen |
| Downloadpersistenz / Wiederverwendung | Synthetische Raw-/Receipt-/Reportbytes bleiben bei Wechsel/Rollback/Rückbau; zweiter Mockaufruf ohne zweiten Transfer |
| Parallele Läufe | Reales flock im Test; bestehende Downloadlock-/Installerlock-/aktive-Unit-Sperren erhalten |
| Stop und Rückbau | SIGTERM-/Interrupted-Reportverhalten offline getestet; Adapteruninstall entfernt nur eigene unveränderte Unit und bewahrt Daten/User/Masken. Echter systemd-Stop/SIGKILL auf Zielhost offen |
| systemd statisch | verify/security auf lokaler **252**-Syntaxfixture erfolgreich; lediglich beide Exec-Zeilen auf `/usr/bin/true` umgeschrieben, nichts installiert/gestartet |
| C16 und Koexistenz | Unit unverändert, Worker-/Native-Einstiegsskripte weiter ausgeschlossen, Masken erhalten, keine start-/enable-/Docker-/SSH-/apt-/userdel-Operationen im Installeradapter; keine Coolify-/Firewall-/VPN-Änderung |
| Hostpreflight | Neuen Vorinstallationspreflight lokal ausgeführt, JSON erzeugt; reine Inventur, keine Probeänderungen und kein Hetznerbeleg. Private lokale Hostausgabe nur unter `/tmp` bewahrt |

Finale Regression: **114 passed, 1 skipped**, keine Fehler; XML enthält genaue
Laufzeit. Der Skip ist die bisherige ausdrücklich nicht freigegebene externe
Composeintegration. Neue Tests prüfen Wheelclosure/Manipulation, reale pip-
Negativfälle, Installerzeiger und lesende Preflightbefehle. Testzahlen beziehen
sich auf einen finalen Lauf, Zwischenläufe werden nicht addiert.

CHANGE ausschließlich neue lokale Testartefakte (bereits ausgeführt):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 unshare --user --map-current-user --net /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.venv/bin/python -m pytest -q -o addopts= -p no:cacheprovider -p tests.offline_guard tests/test_cs50p_frozen_runtime.py tests/test_cs50p_download_only_install.py tests/test_cs50p_mvp.py tests/test_cs50_material_download.py tests/test_cs50_capacity.py --junitxml=artifacts/c26_cs50p_06/offline-tests.xml
```

Die Testvenv ist nur ein vorbestehendes lokales Testwerkzeug; Betreiber nutzen den
neuen Frozenweg statt dieses absoluten Pfads. Lint/Format, AST, JSON, uv-Export und
Patchanwendung sind gesondert im Validierungs-/Handoffbeleg festgehalten.
Die vorherigen C04-102 Tests bleiben enthalten. Das ältere SQLite-/C26-Gate wird
hier weder repariert, umgedeutet noch umgangen.

## Ein-Datei-Beispiel und Quellenreview

`prepare_example.py` wurde offline im Netzwerk-Namespace ausgeführt. Genau ein
HTML-Kandidat `https://cs50.harvard.edu/python/notes/0/` aus dem gespeicherten Week-0-
Link. IDs im Beleg `denied-example.json`; 67 private Dateien einschließlich aller
referenzierten Discovery-Snapshots unter neuem `/tmp/cs50p06-denied-example`.
Dateien 0600, Verzeichnisse 0700, Batch erneut validiert, Approvals **false/false**.
Kein reales Approvalpaket ausgeliefert; die lokalen Specs sind bewusst gesperrt.

Aktuelle Materialgröße und Herausgeber-SHA unbekannt, keine HEAD-/GET-Abfrage dieser
Materialdatei. Die vorhandenen Grenzen bleiben 1 MiB/Datei und 6 MiB akzeptierte
Payload pro Aufruf über Versuche, maximal ein Retry. HTTPS/Hosts/DNS-Pinning/
TLS/Redirect-/Content-/Längen-/Hashschutz, Receipts und atomare Publikation sowie
Wiederverwendung sind offline regressionsgeprüft. Ohne unabhängigen erwarteten
Hash wird ausschließlich lokale Integrität gebunden, keine Herausgeberschaft.

Nur die öffentliche [offizielle Lizenzinformation](https://cs50.harvard.edu/python/license/)
wurde neu gelesen: CC BY-NC-SA 4.0; materialbezogene Nutzungs-/Drittrechteprüfung
bleibt beim Betreiber. `https://cs50.harvard.edu/robots.txt` war über das Webwerkzeug
nicht abrufbar; robots-Gate bleibt offen. Keine Kursdatei geladen. Die bestehende
doppelte Quellenzulässigkeit download/process bleibt erhalten; process=true
aktiviert im angebotenen Downloadablauf keinen C16-Worker.

## Offene Freigaben und Abschluss

1. Vollständige unveränderte Wheels auf zugänglichem geprüften Buildrechner neu
   beschaffen; positiven Frozen-Neuinstallationsbeleg inklusive aller 13 Hashes,
   exakter Distributionen und Smoke erzeugen. Vorher kein freigegebenes Release-TAR.
2. Betreiber liefert die vollständige lesende Hetzner-Preflightausgabe; Kapazität
   neben Coolify, bestehende Ressourcen, Plattform und Voraussetzungen reviewen.
3. Genau eine Material-URL und reale Referenzen für Nutzung, Lizenz/Attribution,
   robots, Aufbewahrung/Widerruf sowie Hashstrategie genehmigen. Default deny bleibt.
4. Installation separat ausdrücklich freigeben; echte Ubuntu-24.04-/systemd-255-
   Abnahme inklusive UID, Rechte, cgroup, Masken und Lifecycle durchführen.
5. Erst danach erster kleiner Download und spätere Reuse-Wiederholung jeweils
   freigeben; SSH-Unabhängigkeit, Logs/Report/Receipt/Hash/Größe real prüfen.
6. Regulärer Review und Integration von Code **und Dokumenten** nach `master`
   durch Berechtigte; kein automatischer Push/Merge. Taskartefakte bis dahin halten.

Die Lieferung ist für Review vorbereitet; **HOLD**, kein READY FOR HOST REVIEW mit
behauptetem Installationsnachweis, kein Produktions-Go. Auch eine spätere positive
isolierte Downloadinstallation ändert den **C26-Gesamtstatus HOLD** nicht.
