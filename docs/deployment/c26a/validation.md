# C26-A – Tatsächliche Readiness- und Testnachweise

Der [C26-B1-Nachtrag](#c26-b1--worker-image-integration) vom 21.10.2026
ergänzt den folgenden historischen C26-A-Stand um die Skriptintegration des
bestehenden Worker-Dockerfiles. Keine nachträgliche Umdeutung älterer Testläufe.
Die [C26-B2-Pilotvorbereitung](#c26-b2--html-pilotvorbereitung) ergänzt den
quellengenauen Ablauf, Betriebsdateien und die separat genehmigte Mountkorrektur.

20.10.2026 · Status **`deployment_prepared`**.
Die [Bereitstellung und Betreiberfreigaben](worker.md) sind vorbereitet.
Die inzwischen gemeldeten Hostdaten werden im [kleinen Pilotplan](hetzner_small_pilot.md)
berücksichtigt; sie wurden nicht durch eigene SSH-/Hostprüfungen bestätigt.
Aktuelle Betreiberwahl ist der [vorhandene Backendcontainer und zweistufige
Bestandskopie über penguin](existing_backend_and_drive.md). Das separate
Composeprofil ist nur noch eine vorbereitete Alternative, keine zweite Instanz
als Standard. Es wird kein zusätzliches Image gebaut oder installiert.
Kein `staging_tested` oder `production_approved`, kein Hetznerzugriff, keine echten
CS50-Downloads, keine Images gebaut/gepullt, keine bestehenden Stores verändert.

## Laufumgebung

Vorhandene Backendumgebung: Python **3.12.12**, Pydantic **2.13.4**, SQLite
**3.50.4**, PyMuPDF **1.28.2**, BeautifulSoup **4.15.0**, Pytest **9.1.1**,
Ruff **0.16.0**, lokale Docker-Compose-CLI **5.0.2**. Keine Installation oder
Neuauflösung. Das unveränderte minimale C22-Laufzeitprofil bindet Abhängigkeiten:

| Datei | Tatsächlicher SHA256 |
| --- | --- |
| `deployment/runtime/pyproject.toml` | `7b5a938b4dae4544fd3ca14bbf4cc8c7fadd04ece094e56013816924b97e30e9` |
| `deployment/runtime/uv.lock` | `fedbe3619188ce39fffbc0d727752b1389eb4e4b1c9552641437859db424ca3f` |

Die tatsächlich verwendete vorhandene Projektvenv stellt diese Parser-/Modell-
abhängigkeiten bereit. Eine frische Installation ausschließlich aus dem C22-
Imagekontext wurde nicht ausgeführt und ist kein behaupteter Nachweis.

Der lokale Workspace hatte weniger als 512 MiB frei. Die bestehende C22-Schwelle
wurde **nicht** abgesenkt. Die folgenden synthetischen Tests liefen deshalb unter
neuen isolierten `/dev/shm/c26a-*`-Roots (lokales tmpfs, etwa 3,3 GiB verfügbar).
Der Prozessneustart-/SQLite-/Restoretest ist kein Hostreboot-/Datenträgercrashtest
und kein Beleg für Persistenz dieses tmpfs über einen Rechnerneustart.
Auf Hetzner muss ein ausdrücklich freigegebenes dauerhaftes lokales Volume geprüft
werden. Die Testroots enthalten ausschließlich eigene synthetische Daten.

## Tatsächliche Pytest-Läufe

Gemeinsamer Präfix, mit `C26_PYTHON` als vorhandener Backend-Pythonumgebung:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$C26_PYTHON" -m pytest -q -p no:cacheprovider
```

Gemeinsamer relevanter Regressionslauf:

```sh
tests/test_cs50_batch_worker.py tests/test_cs50_material_download.py \
tests/test_cs50_workflows.py tests/test_pdf_workflows.py \
tests/test_deployment_operations.py tests/test_deployment_pdf_restore.py \
--basetemp=/dev/shm/c26a-release
```

**96 passed / 0 failed / 0 skipped, 158,89 s**: damals 18 neue C26-Fälle und
78 bestehende Download-/C18-/C19-/C22-Fälle. Echte Native-PDF- und Guardianprozesse,
keine alleinigen Mock-Screenshots. Die HTTP-Quelle ist ausdrücklich ein
`httpx.MockTransport` mit synthetischen Bytes, kein externer Download.

Danach wurden ausschließlich die Zurückhaltung fremder Kursmetadaten im neuen
Controlreport, nichtleere Freigabebelege und der neue CLI-Fehler-/Vorschaupfad
gezielt ergänzt. Keine Änderungen an den bestehenden Download-/Parser-/Queue-
oder C22-Operationsmodulen. Abschließende neue C26-Suite:

```sh
tests/test_cs50_batch_worker.py --basetemp=/dev/shm/c26a-final-acceptance
```

**22 passed / 0 failed / 0 skipped, 16,11 s** auf dem endgültigen Code.
Dieser Lauf überlappt die 18 neuen Fälle des 96er-Laufs. Kein nicht ausgeführter
gemeinsamer 100er-Lauf wird behauptet; die Zahlen werden nicht addiert.

| Prüfung | Tatsächlicher Umfang |
| --- | --- |
| Auswahl | Explizite Kurse/Ressourcen, Snapshot-/Batchhashes, keine stillen Downloads bei Preview |
| Autorisierung | Exakte Material-/Source-/Course-/URLbindung, Schrittflags, fehlende/falsche Belege, Viewer-/Course-/Katalog-/Maintenance-Ablehnung |
| Download | Vorhandener echter Streaming-/Receiptpfad mit Testtransport, Header/MIME-/Größenprüfung, SHA, serielles Intervall, kein HTTP bei Wiederholung |
| Fehler | 429 ohne automatischen Retry, persistierte Fehlversuche, expliziter Retry, erwarteter SHA falsch, manipuliertes Raw, Symlinks und No-Overwrite |
| Nicht unterstützte Formate | Medienrolle bleibt unsupported ohne Transportaufruf |
| Übergabe | Neue C18-Katalogpakete, unveränderter originaler HTTP-Receipt, vorhandene `prepare`-/Kataloghashprüfung |
| Managed E2E | Separater echter C22-Worker, drei C16-Workflows für HTML/Code/PDF, tatsächlicher Cancel und SIGTERM, zweiter Workerprozess, explizites Resume |
| Wiederverwendung | Bestehende bereits committete Stufenausgaben unverändert; weiterer Resume erzeugt keinen zusätzlichen Job; alle wiederverwendeten Stufen skipped |
| Speicherung | C16-SQLite und C18-Status-/Stageartefakte über Prozessneustart, sämtliche Outputgrößen/-hashes und NormalizedDocument-Provenienz geprüft |
| Sicherung | Gestoppter tatsächlicher C22-Backup-/Restore, neuer Root, sämtliche referenzierten Workflow-Outputhashes nach Restore gleich, kein Aktivieren |
| CLI | Tatsächlicher Moduleinstieg: Plan, schreibfreie Downloadvorschau, fehlendes Confirm, kaputte JSONeingabe ohne Inhaltsausgabe |
| Veröffentlichung | Beispielreport gegen bestehende Workflowmodelle und Reporthashes validiert; keine privaten Host-/Testrootpfade enthalten |

Entwicklungsläufe bleiben getrennt: zunächst **10 passed / 1 failed**, 2,78 s
(falscher Testmethodenname `available` statt `worker_available`), danach
**10 passed / 1 failed**, 4,50 s (Test wartete nach Restart nicht auf den neuen
Heartbeat). Nach Korrektur **11 passed**, 13,51 s. Die späteren gezielten Läufe
umfassen **21 passed**, 15,75 s und den neuen CLI-Fall **1 passed**, 1,07 s.
Diese Fälle überlappen mit der abschließenden Suite und werden nicht addiert.
Die beiden früheren Fehler waren korrigierte neue Testannahmen, keine als Baseline
deklarierten Produktivfehler. Keine Gesamtrepository- oder UI-Suite behauptet.

## Versionsgebundener synthetischer E2E-Beleg

[synthetic_worker.v1.json](synthetic_worker.v1.json) sind die unveränderten
Ausgabebytes des erfolgreichen E2E-Falls aus dem obigen 96er-Lauf. Die enthaltenen
Workflowberichte verwenden unverändert C18-`Workflow`, Stages/Outputs und dessen
`report_sha256`, die Jobs C16. Der kleine äußere Testbeleg hat keinen neuen
fachlichen Evaluator oder neue Queue-/Goldmodelle.

- Drei synthetische Transfers, drei abgeschlossene Materialworkflows.
- Unterbrochener PDFversuch tatsächlich `cancelled`, weiterer Versuch abgeschlossen.
- Drei bereits committete Outputhashes nach Wiederaufnahme identisch erhalten.
- Separater Workerneustart, Hash-/Größenprüfung, idempotenter weiterer Resume und
  gestoppter Backup-/Restore tatsächlich ausgeführt.
- **0 echte Downloads**, keine Qualitätswerte, keine Server-/Containerbehauptung.
- Bodydigest `8b8119ff507988771511a610037fb49a2c88fe2d5d2745f9693b8f96ccf185a7`.
- Exakte Dateibytes, 46698 Bytes, SHA256
  `8933c811164ac03c5c23c47bd2c2959c26e4f2e1550fd5af8b1b61929bc00934`.

Laufzeiten, Job-IDs und PDFbytes echter Ausführungen können variieren. Reproduziert
werden dieselben überprüften Zustands-/Hash-/Wiederverwendungsbedingungen, keine
erfundene konstante Job-ID oder Benchmark. Die Originale dieser Tests sind
synthetische Fixtures, kein fachlich bewerteter CS50-Korpus.

## Compose, Images und verbleibende Grenzen

Die tatsächliche CLI-Auswertung `docker compose … config --format json` verwendet
ausschließlich deklarierte Dummywerte für Digest, Mountpfade und Egress-Netz;
keine dieser Pfadangaben wurde provisioniert. Ohne Daemonkontakt erfolgreich:

| Gewähltes Profil | Tatsächliche Dienste | Veröffentlichte Ports |
| --- | --- | ---: |
| keines | keine | 0 |
| processing | executor | 0 |
| tools | offline-cli | 0 |
| download | downloader | 0 |

Zusätzlich automatisierte YAML-/Dockerfileprüfungen für UID, read-only,
Capabilities, fehlende Hostports/Docker-Sockets, explizite Profile und
`create_host_path=false`; Downloader hat nur Spezifikations-, Archiv- und den
zusätzlichen read-only Kapazitätsdateimount, keine Jobdatenbank oder Secrets.
Die neue CLI wird tatsächlich in den bestehenden Buildkontext aufgenommen;
Lockdateien bleiben unverändert. Ruff Check und Format Check erfolgreich für
die drei neuen Pythondateien; lokale Dokumentationsverweise, JSON-/Belegmodelle
und `git diff --check` werden vor Veröffentlichung geprüft.

Der erste Docker-Image-Leseversuch war im Sandboxkontext nicht erlaubt; mit dem
zulässigen read-only Zugriff wurde anschließend der **leere lokale Imagebestand**
bestätigt. Es gibt keinen Imagebuild-, Container-, cgroup-, OOM-, read-only-FS-,
Container-PID-/Egress-/Coolify- oder echten Healthcheck-Nachweis im Zielcontainer.
Nichts gepullt/installiert und kein Serverzustand verändert. Diese Abnahmen,
Image-/Quellenfreigaben, Hostverifikation und konsistenter Verbundrestore bleiben offen.

## Nachtrag: operatorgemeldeter 2-vCPU-/4-GiB-Host

Das vorhandene Composepaket ist parametrisiert, keine neue Anwendung. Die kleine
Envvorlage rendert den Worker mit **1 CPU / 1024 MiB / 128 PIDs**, tmpfs 128 MiB,
`restart: no` und Swaplimit gleich RAMlimit; CLI und Downloader jeweils 256 MiB.
Alle Limits werden nur als Konfiguration nachgewiesen, nicht als auf dem Host
gemessene Durchsetzung. Deployaccount, SSHalias/Hostkeyvertrauensbeleg, Image-
und Rootfreigaben bleiben offen. Bestehende Coolifydienste unverändert.

Die explizite private Limitsdatei ist in allen drei Rollen RO gemountet.
Kleines Profil: **5 GiB Freiraumreserve, drei Materialien, Archiv 64 MiB,
Katalog 128 MiB, Jobroot 512 MiB und Exporte 16 MiB**. Die C26-Kontrollen prüfen
vor Schreiben/Einreichung, im HTTPstream sowie regelmäßig im bestehenden Executor.
Es handelt sich um Stoppschwellen, keine atomare Reservation oder Filesystemquota.
Keine Änderung an C22s bestehender 512-MiB-Untergrenze, C16-Queue oder C19-Limits.
Der kleine Hostplan benennt Ausgabenwachstum, Backup-/Imagezuschläge, unbekannte
Gesamtkursgrößen und die konkrete noch auszufüllende Installationsfreigabe.

Tatsächlicher gemeinsamer Lauf mit obigem Python-/Pytestpräfix:

```sh
tests/test_cs50_capacity.py tests/test_cs50_batch_worker.py \
tests/test_cs50_material_download.py tests/test_deployment_operations.py \
--basetemp=/dev/shm/c26a-small-release
```

**78 passed / 0 failed / 0 skipped, 44,38 s**: 13 Kapazitätsfälle, 23 C26-Fälle
einschließlich zweier tatsächlicher Workerprozessabläufe und 42 bestehende
Download-/C22-Fälle. Kein externer HTTP-/Host-/Containerzugriff. Der reale Workerprozess
führt synthetische HTML-/Code-/PDFbytes aus; die Quelle bleibt MockTransport.

Neu nachgewiesen: striktes Policy-/Privatrechteformat, fehlende konfigurierte
Limitsdatei sperrt statt Defaultfallback, kleine Materialanzahl und wiederholbarer
Kapazitätsplan, 5-GiB-Grenzfälle mit simuliertem freien Speicher, Ablehnung vor
neuen Writes, Streamabbruch ohne Rawpublikation, symlinkfreie Größenprüfung,
Reportbudget sowie Einzelworkerpflicht. Compose wird tatsächlich ohne Daemon
gerendert und auf die kleinen Ressourcen-/Swap-/Neustart-/Mountwerte geprüft.
Die volle 5-GiB-Policy kann im nur 3,3-GiB-Testtmpfs nicht laufen; die Prozessfälle
verwenden ausdrücklich die generische 512-MiB-Reserve, keine abgeschwächte
Hostvorlage und keine behauptete Hostkapazitätsabnahme.

Der zweite echte E2E-Fall erzeugt ausschließlich eine eigene sparse Testdatei
mit deklarierter Größe über dem Jobbudget. Sie belegt keine zwei GiB physisch.
Der C26-Worker stoppt während einer laufenden PDFstufe mit Exit 2 über vorhandenes
Childcleanup; danach expliziter Neustart/Resume, unveränderte committete Outputs,
Idempotenz und gestoppter C22-Backup/Restore erfolgreich. Das ist ein tatsächlicher
Budgetabbruch, **kein injizierter Kernel-ENOSPC-, Container-OOM- oder Hostcrashtest**.

Ein vorheriger Entwicklungslauf hatte **35 passed / 1 failed**, 44,61 s:
Compose gibt in dieser CLIversion Bytewerte als JSONstrings zurück. Die Prüfung
wurde auf numerische Werte konvertiert; keine Ressourcenwerte geändert. Ruff
meldete zuvor eine Testfixture-Importkollision, die vor der Abnahme korrigiert ist.
Diese Läufe werden nicht addiert. Der ältere versionierte E2E-Beleg bleibt bytegleich
und behauptet keinen neuen Container- oder Hosttest.

Nach der abschließenden Zuordnung von Downloadberichten zum Archivbudget (statt
zum separaten Exportbudget) und dem ausdrücklichen Diagnosefall bei hoher Reserve:

```sh
tests/test_cs50_capacity.py tests/test_cs50_batch_worker.py \
--basetemp=/dev/shm/c26a-small-final
```

**37 passed / 0 failed / 0 skipped, 52,17 s** auf dem endgültigen Pythoncode:
14 Kapazitätsfälle und 23 C26-Fälle. Bestehende Originalbytes oberhalb des
Exportbudgets verhindern keinen schreibfreien Downloadpreviewbericht im Archiv.
Ein Report bleibt bei unterschrittener C26-Reserve lesbar, während eine neue
Einreichung abgewiesen wird; C22s Mindestreserve wird dabei weiterhin geprüft.
Dieser Lauf überlappt mit dem 78er-Lauf und wird nicht addiert.
Ruff Check und Format Check erfolgreich für alle **sechs** betroffenen Pythondateien;
beide Kapazitätsvorlagen gegen ihr tatsächliches Modell validiert, ursprünglicher
versionierter E2E-Beleg byteidentisch. Kein gesamter Repositorytestlauf.

## Integration und Lifecycle

### Aktualisierung auf Master und lokale Bestandsvorbereitung

Während der Veröffentlichung wurden #132–#134 gemergt. Master
`7ed22f3d40fa5a1ea388152b81bf883865e2f4f1` wurde regulär in den eigenen Branch
übernommen; fremde Worktrees wurden nicht verändert. Danach mit demselben
Python-/Pytestpräfix:

```sh
tests/test_cs50_capacity.py tests/test_cs50_batch_worker.py \
tests/test_cs50_material_download.py tests/test_deployment_operations.py \
--basetemp=/dev/shm/c26a-integrated-release
```

**79 passed / 0 failed / 0 skipped, 41,81 s**: 37 C26- und 42 vorhandene
Download-/C22-Fälle auf dem integrierten Stand. Dieser Lauf ersetzt nicht die
historischen Laufzahlen und wird mit ihnen nicht addiert.

Die anschließende Betreiberentscheidung präzisiert `coolify` als lokalen SSHalias
und Google Drive als **lokalen** ChromeOS-/9p-Pfad auf `penguin`. Dessen explizite
Metadatenprüfung: Verzeichnis vorhanden, kein eigener Symlink, les-/durchsuchbar,
Mount `/mnt/chromeos`, Typ `9p`; Schreibbarkeit im Agentkontext nicht gegeben,
ohne Schreibprobe. Gemeldete virtuelle Kapazität ist keine Cloudquota.
Keine Hetznerverbindung, Quellinventur, Kopie, Cloudverifikation oder Löschung.

Neu: `scripts/c26_copy_inventory.py`, stdlib-only, ohne SSH-/Kopier-/Cloudaktionen.
Es liefert ein begrenztes kanonisches relatives Dateiinventar mit SHA256 und
Verzeichnisliste. Einzeln geprüfte synthetische Fälle: Unicode/CRLF und Leerordner,
Byte-Duplikate, zusätzliche/veränderte Zieldateien, Symlinks/FIFO, Ressourcenlimits,
beobachtete Änderung beim Lesen, fehlende Roots, pfadfreie Fehlantwort und keine
Quelldateischreibvorgänge. Separater Prozess über stdin funktioniert ohne
Repositoryimports; das ist **kein ausgeführter SSHtest**.

```sh
tests/test_c26_copy_inventory.py --basetemp=/tmp/c26a-copy-final-tests
```

**5 passed / 0 failed / 0 skipped, 0,20 s** auf dem endgültigen Inventarskript.
Vor dem zusätzlichen stdin-Fall: vier erfolgreiche Fälle, 0,13 s, überlappend.
Keine neuen Abhängigkeiten, keine Server-/Datenmigration. Befehlsvorlagen werden
nur mit `bash -n` und Python-AST geprüft, nicht zur Ausführung gebracht.

**Abgebrochener lokaler Ausführungsfehler:** Beim ersten Schreiben der neuen
Befehlsdokumentation kollidierte ein Heredoc-Begrenzer mit eingebettetem Beispielcode.
Dadurch lief unbeabsichtigt ein lokaler rsync-**Dry-Run** mit falschem Rootbereich
an. Er wurde per Interrupt beendet (Exit 130), ohne Kopie, Upload oder SSHzugriff.
Ein fehlgeschlagener `mkdir`-Aufruf hatte ein leeres Ziel und legte nichts an.
Es erfolgte eine unerwünschte lokale Metadatendurchsicht; sie ist kein Inventar-
oder Abnahmenachweis und wurde nicht weiterverwendet. Anschließend keine laufenden
rsync-Prozesse festgestellt; Gitstatus enthielt nur die drei erwarteten neuen
Auftragsdateien. Dokumentation danach ausschließlich direkt gepatcht; die endgültigen
Shellbeispiele werden zur Syntaxprüfung nur als Daten an `bash -n` übergeben.

Empfehlung: bestehendes Backend für genau einen bestätigten HTML-Notes-Pilot
verwenden, sofern Skriptstand, tatsächliche Mounts/Identität/Limits und Sourcefreigabe
belegt sind. `sleep infinity` und zwei importierbare SRTmodule sind dafür kein
vollständiger Funktionsnachweis. SRT-/Material-/Audio-/Videowege und persistierte
Downloadactions gegenüber C16-Processingjobs werden im aktuellen Runbook getrennt.
Ein `docker exec`-Worker startet nach Containerrestart nicht automatisch neu;
echter Containerrestart und Ressourcendurchsetzung bleiben ungeprüft.

Während dieses Nachtrags wurde [PR #135](https://github.com/rf-data/Personal_Assistant/pull/135)
extern gemergt. Neuer Basisstand `5064904259ce8a02b0600a5e646f9e06563a0cac`
besitzt exakt denselben Git-Tree `97041e968a2accc8e058c24391b335401af72c15`
wie der oben tatsächlich geprüfte integrierte C26-Stand `d95d110`. Keine erneute
identische 79er-Suite als zusätzlicher Erfolg ausgegeben.

Der verbliebene Nachtrag verwendet den neuen eigenen Branch
`feat/c26a-existing-backend-copy-handoff` ab diesem Master und den vorhandenen
auftragseigenen C26-Worktree. Ursprüngliche Branchrefs, primäre Checkouts und
andere Aufträge wurden nicht bereinigt. Die Übernahme erfolgt als separater
[Folge-PR #136](https://github.com/rf-data/Personal_Assistant/pull/136);
der bereits gemergte PR wird nicht umgeschrieben.

Ruff Check und Format Check für alle acht betroffenen Pythondateien erfolgreich.
22 Shellblöcke nur mit `bash -n`, eingebetteten Pythoncode nur mit AST geprüft;
28 lokale Markdownlinks gültig, ursprünglicher versionierter E2E-Beleg bytegleich,
`git diff --check` erfolgreich. Keine Dependencies installiert. Der bekannte eigene
Ruffcache bleibt ignoriert. Beide primären Checkouts werden ausschließlich lesend
auf Gitstatus geprüft. Kein automatischer Merge/Close, keine Done-Einstufung offener
C26-Abnahmen, keine MAINT-Bereinigung. Der Folgebranch/Worktree bleibt bis zu dessen
bestätigter Integration erhalten. `deployment_prepared` ersetzt weder Gitintegration
noch Staging-, Cloudkopier- oder Produktionsfreigabe.

## C26-B1 – Worker-Image-Integration

21.10.2026, Basis `origin/master`
`a328a764d8a2bb8167ea1f44e4e1509faaaf506c`, integrierte C26-A-PRs #135/#136.
Der Betreiber hat Dockerfile `docker/DockerFile.worker` und Repositorywurzel
als tatsächliche Coolify-Build-Einstellungen bestätigt. Diese Einstellungen
wurden nicht über SSH oder eine Coolify-API abgerufen.

**Implementiert:** gezielte Kopie von sechs bestehenden Laufzeitskripten und
einem stdlib-only Smokeprüfer, obligatorischer netzwerkfreier `--help`-Check der
vier angeforderten Module während des Builds, Dockerfile-spezifische
Kontext-Allowlist und automatisierte Tests. Keine Änderung an Abhängigkeiten,
Lockfile, C22-Alternativimage, Bind-Mounts, Standardstart oder Restart-Policy.
Die bestehende [Anleitung](existing_backend_and_drive.md#c26-b1--skripte-im-vorhandenen-worker-image)
enthält die späteren manuellen Redeploy-/Containerprüfbefehle.

### Dependency- und Kontextnachweis

Vorhandene Projektvenv: Python 3.12.12, Pytest 9.1.1, Pydantic 2.13.4,
PyMuPDF 1.28.2, Ruff 0.16.0. Keine Installation oder Lockneuauflösung.
Der offline ausgeführte Lockexport verwendet exakt das bisherige Workerprofil:

```sh
UV_CACHE_DIR=/tmp/c26b1-uv-cache uv export --offline --frozen \
  --no-default-groups --extra lecture-worker --no-emit-project \
  --format requirements-txt --no-hashes
```

**125 selektierte gelockte Distributionen**, einschließlich httpx, Pydantic,
BeautifulSoup, PyMuPDF, PyYAML, pydantic-settings und python-dotenv. Marvin,
OpenAI und LiteLLM sind nicht ausgewählt. Zusätzliche lokale Importinspektion:
Alle vier tatsächlichen CLI-Hilfeaufrufe erfolgreich; die 16 dabei geladenen
Distributionen sind sämtlich im selektierten Profil enthalten. Netzwerkzugriff
wurde dabei per Python-Audithook abgewiesen. Das ersetzt keine frische Installation
dieser 125 Distributionen und keinen vollständigen Imagetest.

Die Laufzeittests kopieren Pythoncode, die vier bisherigen YAMLdateien und genau
die sieben Image-Skripte in einen isolierten Root, ohne `docs`, Testdaten, `.env`,
Originale oder Host-Pythonpfade. Die CLI-Prozesse erzeugen dort keine neuen Dateien.
Negativfälle prüfen fehlende transitive Skripte, Symlinks, Import-/CLIfehler,
Timeouts sowie die Zurückhaltung von Fehlerausgaben und privaten Umgebungsvariablen.

Eine zusätzliche **tatsächlich ausgeführte lokale Docker-BuildKit-Kontextprüfung**
verwendet ausschließlich synthetische Testdateien, dieselbe spezifische
Ausschlussdatei und `FROM scratch; COPY . /context/`. Export nur in einen neuen
lokalen Testroot; kein Baseimage, Paketdownload, Image-Tag, laufender Container
oder Hostmount. Dockers eigener Matcher bestätigt die enthaltenen Laufzeitdateien
und ausgeschlossenen Secret-/Daten-/Hilfsskript-Canaries. Das ist ausdrücklich
**kein Build des Worker-Dockerfiles**.

Der erste Kontexttest schlug fehl (14 passed / 1 failed / 1 skipped, 37,29 s):
Verzeichnis-Ausnahmen schlossen unbeabsichtigt weitere Kinddateien ein. Diese
Ausnahmen wurden entfernt. Die korrigierte native Prüfung bestand separat
(1 passed, 4,78 s) und im abschließenden gemeinsamen Lauf unten. Keine echte
Credential- oder Originaldatei war Teil dieser synthetischen Kontexte.

### Tatsächliche Tests

Gemeinsames Präfix mit der vorhandenen Backendvenv als `C26_PYTHON`:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$C26_PYTHON" -m pytest -q -p no:cacheprovider
```

Neue abschließende Suite, zusätzlich `C26_WORKER_CONTEXT_AUDIT=1`:

```sh
tests/test_worker_image_content.py --basetemp=/tmp/c26b1-worker-release
```

**15 passed / 0 failed / 1 skipped, 25,61 s.** Der Skip ist ausschließlich
`test_built_worker_image`: kein gebautes Worker-Image zur Verfügung. Die native
Docker-Kontextprüfung wurde ausgeführt, nicht übersprungen. Der vorherige gemeinsame
Lauf (15 passed / 1 skipped, 70,42 s) und der reine Laufzeitlauf (14 passed /
1 skipped, 18,46 s) überlappen; nicht addieren.

Zwischen dem vorherigen Gesamtlauf und dem abschließenden Release-Lauf wurden
versteckte Unterverzeichnisse unter `src` zusätzlich abgesichert:
Die erste erweiterte Prüfung deckte zwei noch eingeschlossene synthetische
Python-Canaries auf (1 failed, 5,56 s). Explizite Unterbaum-Ausschlüsse schließen
sie aus; derselbe native Kontexttest besteht danach (1 passed, 2,58 s).
Nur die Ignore-Regeln und deren Testcanaries wurden dabei ergänzt, keine
Änderung am Smokeprüfer oder an den vier geprüften CLI-Modulen.

Bestehende relevante Regression, gleiches Präfix:

```sh
tests/test_cs50_batch_worker.py tests/test_cs50_capacity.py \
tests/test_cs50_material_download.py tests/test_deployment_operations.py \
--basetemp=/tmp/c26b1-regression-final
```

**77 passed / 2 failed / 0 skipped, 223,04 s.** Die zwei Varianten von
`test_managed_worker_cancel_restart_resume_and_stopped_backup` schlugen fehl:
`signal` wartete zu lange auf den Abschluss der Folgejobs; `capacity` wurde
beim anschließenden Report durch den vorhandenen Quarantänefence gesperrt.
Keine neue Timeout-/Quarantäneumgehung oder Runtimeänderung. Der frühere gleiche
Lauf wurde vor Abschluss unterbrochen und besitzt kein Abnahmeergebnis.

Die beiden betroffenen Prozessfälle anschließend mit demselben unveränderten
Test-/Runtimecode in neuen isolierten tmpfs-Roots außerhalb der eingeschränkten
Sandbox nachgeprüft:

```sh
tests/test_cs50_batch_worker.py::test_managed_worker_cancel_restart_resume_and_stopped_backup \
--basetemp=/dev/shm/c26b1-process-final
```

**2 passed / 0 failed / 0 skipped, 91,18 s.** Tatsächliche separate Worker-
und PDFprozesse, kontrollierter Abbruch, Wiederanlauf, Resume und gestoppter
Backup-/Restoreroundtrip. Die Schutzgrenzen blieben aktiv. Es wurde weder ein
unveränderter Master-Baselinelauf noch eine neue gemeinsame grüne 79er-Suite
ausgeführt; der erste Fehlerlauf bleibt sichtbar. tmpfs ist kein Nachweis eines
persistenten Hostvolumes. Keine vollständige Repositorytestsuite.

Ruff Check und Format Check für beide neuen Pythondateien erfolgreich.
25 Shellblöcke der beiden betroffenen Runbooks nur mit `bash -n` geprüft,
acht lokale Markdownverweise gültig; `git diff --check` erfolgreich.
`src`, bestehende Skripte, `configuration`, `deployment`, `pyproject.toml` und
`uv.lock` sind gegenüber der genannten Basis unverändert. Testlogs und eigene
synthetische Testdaten liegen außerhalb des Repositories; kein Original gelesen.

### Vollbuild, Hostfreigabe und Lifecycle

**Vollständigen Worker-Dockerbuild und Smokeprüfung in dessen Image nicht
ausgeführt.** Der geprüfte Dockerendpunkt ist ein lokaler Unixsocket, kein Hetzner-
oder SSHkontext. Auf seinem Dateisystem waren vor den Tests nur rund **2,82 GB**
frei; weder Python-3.12-slim-Basis noch Workerimage waren lokal vorhanden. Das
bestehende breite Workerimage wurde vom Betreiber bereits mit rund **3,49 GB**
virtueller Größe gemeldet. Diese Werte sind keine genaue Buildplatzprognose,
reichen aber nicht für einen verantwortbaren Vollbuild einschließlich Paket-/
Buildcache und Reserve. Deshalb kein Pull oder Vollbuildversuch, keine
Image-/Cachelöschung und kein schlankeres Ersatzimage als vermeintlicher Nachweis.

Die eingebauten Buildprüfungen und der optionale Test mit
`C26_WORKER_TEST_IMAGE=<lokaler-image-tag>` müssen auf einem ausreichend großen,
freigegebenen Buildhost nachgeholt werden. Defaultstart `sleep infinity` bleibt;
ein neuer C16-Worker wird dadurch nicht automatisch gestartet oder neu gestartet.
Kein SSHzugriff, Coolify-Redeploy, echter Download, Driveupload, produktiver
Storeeingriff oder Eingriff in bestehende Container/Volumes/Images.

Eigener Branch `feat/c26b1-worker-image-entrypoints` und Worktree bleiben für den
regulären offenen PR erhalten. Kein automatischer Merge, keine Bereinigung
historischer oder fremder Branches/Worktrees. Gitintegration, tatsächlicher
Imagebuild und Hetzner-/Pilotabnahme sind getrennte verbleibende Schritte.

## C26-B2 – HTML-Pilotvorbereitung

21.10.2026, Basis `7420df62765aab127f5abeb3e39d355678844148`, B1/#138 gemergt.
Die erfolgreiche Aktualisierung und vier CLI-Smokes des laufenden Workers sowie
die vier Bind-Mounts und zuletzt 14 GiB freien Speicher hat der Betreiber
gemeldet. Keine eigene Hetznerdiagnose. Der konkrete
[HTML-Pilotablauf](html_pilot.md) verwendet ausschließlich vorhandene C26/C16/C18-
Modelle, genau eine bestehende offizielle Notes-Resource und fünf aktive Stufen.

### Gefundene Ursache und eng begrenzte Korrektur

`Settings.private_paths` und `storage.artifact_root` lehnten sämtliche Ziele
lexikalisch unter ihrem Codecheckout ab. Im Worker ist dieser `/app`, weshalb
auch `/app/data/<Pilot>` scheiterte. Der Betreiber hat die gezielte Korrektur
ausdrücklich genehmigt, einschließlich Mountidentität, Zweckbindung, privater
Roots und Workerrechte; keine Freigabe für Servereingriffe.

`src.runtime_paths.output_path` ergänzt nun beide bestehenden Prüfstellen.
Externe Workspaces behalten ihren Vertrag. Interne Datenroots benötigen die
explizite, private, UID-gebundene Policy über `PA_PERSISTENT_ROOTS_FILE`.
Repository, genauer Unterbaum, Zweck und Mountidentität müssen übereinstimmen.
Kein Default aufgrund des Namens `data`; Codebereiche bleiben gesperrt.
Die Policy wird nicht gecacht. Kernelmountdaten, Symlinkfreiheit, unveränderte
Auflösung, private Ownership und tatsächliche Schreibrechte werden erneut geprüft.
Verschachtelte/gestapelte Mounts, unbekannte oder nicht persistente Dateisysteme,
unlesbare Daten und fremd schreibbare Mounteltern bleiben gesperrt.

Geprüfte Aufrufstellen: Materialdownload/-publikation und C26-Output verwenden
weiter `artifact_root`; C16-Konfiguration verwendet weiter `Settings`.
Guardian/Executor reichen ausschließlich den expliziten Policypfad zusätzlich
in ihrer bereinigten Umgebung weiter. Kindprozesse validieren selbst erneut;
keine übrigen Secrets oder Hostumgebung übernommen. Keine Änderung an Queue,
SQLite-/Workflow-/Materialschemas, Source-IDs, Receiptbytes oder Parsern.
C23-Store- und sonstige Repositorygrenzen bleiben unverändert.

### Generator, Source und Readiness

`scripts.cs50_pilot` exportiert genau die zwei bereits versionierten
CS50-Python-Discovery-Snapshots, prüft deren feste SHAwerte und die vorhandene
Notes-0-Identität. Ein lokaler tatsächlicher Export bestand; keine aktuelle
Notes-Seite gelesen oder heruntergeladen. Manifest/Binding sind die vorhandenen
Modelle, ohne private absolute Pfade im exportierten Source-Binding.
Der Export kopiert ausschließlich schon versionierte Discoverybytes, keine
Originalbestände, Credentials, Tokens oder produktiven Konfigurationen.

Der Helfer erstellt nur nach ausdrücklichem Setupconfirm einen neuen privaten
Bereich, Pfadpolicy, tatsächliche Identity/Tokenbindung, bestehende Limits und
ein absichtlich **unbestätigtes** SourceApproval-Formular. Katalog und Controller
entstehen erst nach gültigem vorhandenem Receipt/Bundle; niemals bestehende Roots
oder Jobdatenbanken übernehmen. Der authentifizierte Principal wird vom Betreiber
benannt, kein Beispielnutzer als real ausgegeben. Neue CLI im bisherigen
Worker-Dockerfile gezielt ergänzt; kein zweiter Dienst oder neue Dependency.

Preflight ist phasengebunden (plan/download/process), Exit 2 bei Blockern.
Es erzeugt weder Dateien, SQLiteinitialisierung, Lockdateien noch HTTPverkehr.
Nur vorhandene Locks nonblocking prüfen; bei DBbestand fehlende Lockbelege,
nichtleeres WAL/Journal, unbekannte Schemas, laufende oder fremde Jobs sperren.
Der spätere Writer bleibt für Autorisierung/Hashprüfung und Reservierung maßgeblich.
Kontrollierter Workerrestart ist über bestehende C16-/C18-Mechanismen dokumentiert;
kein Neustart des Containers und kein automatischer Resume durch den Helfer.

### Tatsächliche lokale Prüfung

Vorhandene Pythonumgebung unverändert: Python 3.12.12, Pytest 9.1.1,
Pydantic 2.13.4, PyMuPDF 1.28.2, Ruff 0.16.0. Keine Paketinstallation,
keine Lockänderung. Gemeinsames Pytestpräfix:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$C26_PYTHON" -m pytest -q -p no:cacheprovider
```

Abschließender Lauf auf dem endgültigen Pythoncode:

```sh
tests/test_runtime_paths.py tests/test_cs50_pilot.py tests/test_job_control.py \
--basetemp=/dev/shm/c26b2-final
```

**91 passed / 0 failed / 0 skipped, 19,41 s**: 34 neue Pfad-/Mountfälle,
21 neue Generator-/Preflight-/Pilotfälle und 36 bestehende C16-Fälle.
Neue Fälle prüfen reale private Dateien/Policies und synthetische Kernelrecords:
gleichnamige ungemountete Verzeichnisse, Zweck-/Subtree-/UIDgrenzen, Codepfade,
Traversal/Symlinks, Nested/Stacked/Changed-Mounts, fehlende Mountdaten, private
Policylage/-rechte, Revocation, Escaping und tatsächliche Zugriffsablehnung.

Der vollständige neue synthetische Ablauf nutzt echten MockTransport-Receipt,
Katalogversiegelung, konfigurierte C16-Authentifizierung, tatsächlichen Executor
mit Guardian-/HTML-Workerprozessen und fünf C18-Stufen. Ein Job, completed,
sämtliche Outputgrößen/-hashes korrekt; Resume legt keinen zweiten Job an.
Keine bloß vorgefertigten APIantworten. Der HTTPtransport, die Kernelmountrecords
und der verfügbare Speicher sind ausdrücklich synthetisch modelliert: lokal sind
keine 5 GiB frei, die produktive Reserve wurde nicht abgesenkt. Die realen
Kindprozesse arbeiten in temporären externen Testroots. Das ist kein realer
Container-Bind-Mount-, Hostvolume-, Containerrestart- oder Hetznernachweis.

Breitere relevante Regression vor den abschließenden Ergänzungen an Parentrechten
und den Preflightchecks:

```sh
tests/test_job_control.py tests/test_deployment_operations.py \
tests/test_cs50_material_download.py tests/test_cs50_batch_worker.py \
tests/test_cs50_capacity.py tests/test_cs50_workflows.py \
tests/test_worker_image_content.py --basetemp=/dev/shm/c26b2-regression
```

**154 passed / 0 failed / 2 skipped, 209,57 s.** Skips sind native optionale
Docker-Kontextprüfung und vollständiger Worker-Imagetest. Die native Kontextprüfung
wurde separat mit `C26_WORKER_CONTEXT_AUDIT=1` ausgeführt:
`tests/test_worker_image_content.py::test_native_docker_context_excludes_private_files
 --basetemp=/tmp/c26b2-native-context`: **1 passed, 2,44 s**. Scratch-Export nur
synthetischer Dateien, kein Workerbuild, kein bestehender Container verändert.
Der vollständige Imagetest bleibt nicht ausgeführt; kein gebautes B2-Workerimage
vorhanden, kein Vollbuild/Host-Redeploy Bestandteil der Freigabe.

Die 36 C16-Fälle überschneiden sich mit dem finalen 91er-Lauf; nicht addieren.
Nach dem breiteren Lauf wurden Mounteltern zusätzlich gegen fremde Schreibrechte
geschützt und die neuen Preflight-/HTTP-/DBprüfungen vervollständigt. Der endgültige
91er-Lauf enthält die betroffenen neuen Fälle plus C16; keine neue gemeinsame
grüne 156er-Suite oder vollständige Repositorytestsuite behauptet.

Entwicklungsläufe getrennt: Pfade **31 passed, 1,00 s**; erste Pilotsuite
**15 passed / 2 failed, 8,47 s** (Vergleich des unveränderten Discoverybindings
mit dem separat als lizenzgeprüft markierten Receiptbinding). Korrigiert wurde
der Vergleich, keine Hash-/Rechteprüfung entfernt. Danach **48 passed, 15,19 s**,
**49 passed, 10,75 s**, **54 passed, 11,30 s**; diese überlappen die finale Suite.

Ruff Check und Format Check für alle acht geänderten Pythondateien erfolgreich.
42 Shellblöcke in den vier betroffenen Dokumenten ausschließlich mit `bash -n`,
drei eingebettete Pythonbeispiele ausschließlich mit AST geprüft; 29 lokale
Markdownverweise gültig, `git diff --check` erfolgreich. Die vorbereiteten
Host-/Containerbefehle wurden dabei als Daten geprüft, nicht ausgeführt.

### Offene Betreiberentscheidungen und Lifecycle

Noch erforderlich: PRreview/Merge, freigegebener Codeupdate des bestehenden Workers,
erneuter Smoke, echte Mount-/Benutzer-/Ressourcenprüfung, exakte neue private
Pilot-/Policy-/Token-/Bundlepfade, tatsächlicher Principal sowie sourcebezogene
Nutzungs-/Lizenz-/Robots-/Retentions-/Widerrufbelege und Download-/Processingfreigabe.
Realer Download, aktuelle Notesbytes/-größe/-HTTPstatus, tatsächliche Hostreserve,
Mountpersistenz und Restart auf Hetzner bleiben `not_checked`.
Reale Ausführung bleibt bis zu diesen Entscheidungen **blocked**.

Keine SSHverbindung, kein Build/Redeploy auf Hetzner, keine realen CS50-Downloads,
LLM-, Embedding-, Cloud- oder Qdrantaufrufe und keine Loviscach-/Storeänderung.
Der eigene Branch `feat/c26b2-single-html-pilot` und Worktree bleiben für den
offenen regulären PR erhalten. Keine Bereinigung anderer oder historischer
Git-Artefakte, kein automatischer Merge. Ein technischer PR erteilt keine
Quellenfreigabe oder fachliche Realabnahme.
