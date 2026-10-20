# C26-A – Tatsächliche Readiness- und Testnachweise

20.10.2026 · Status **`deployment_prepared`**.
Die [Bereitstellung und Betreiberfreigaben](worker.md) sind vorbereitet.
Die inzwischen gemeldeten Hostdaten werden im [kleinen Pilotplan](hetzner_small_pilot.md)
berücksichtigt; sie wurden nicht durch eigene SSH-/Hostprüfungen bestätigt.
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

Eigener Branch `feat/c26a-cs50-worker`, eigener Worktree; primäre Checkouts und
andere offene Aufträge bleiben unberührt. Code, Konfiguration und diese dauerhaften
Nachweise liegen in [PR #135](https://github.com/rf-data/Personal_Assistant/pull/135)
gegen master. Der PR ist offen, die Dateien enthalten ausschließlich Code,
Deploymentvorlagen, Dokumentation, synthetische Tests und den geprüften Beleg.
Commit-Hooks inklusive JSONprüfung erfolgreich. Getrackter Gitstatus sauber;
der bekannte eigene Ruffcache bleibt ignoriert. Beide primären Checkouts sauber.
Kein automatischer Merge/Close,
keine Done-Einstufung offener C26-Abnahmen und keine MAINT-Bereinigung.
Bis zur bestätigten Integration müssen Branch/Worktree erhalten bleiben;
`deployment_prepared` ersetzt weder den Git-Integrationsabschluss noch Staging-
oder Produktionsfreigabe.
