> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-G – Integrationsvalidierung und Übergabe

25.10.2026. **Offline geprüft, Produktion HOLD; Defaultintegration pending.**
Keine produktiven Dienste/DBs/Queues, SSH, Coolify, DNS, Firewall, TLS, IdP,
echten Zugangsdaten, Kursdownloads, Images/Modelle oder externen Produktiv-APIs
verwendet. GitHub-Leseversuche lieferten keinen aktuellen Livezustand.

## Änderungen und bewusste Grenzen

- `scripts/c26g_preflight.py`: lesender begrenzter Prüfer für normalisiertes
  Backend-/UI-Compose-JSON und **deaktivierte** Settings. Verwendet das echte
  Settingsmodell und den bestehenden HTTPS-Preflight, prüft obligatorisches v2,
  drei Rollen, API-/Worker-Mount-/Netz-/Commandbindung, feste Profile, Images,
  Hardening und privaten UI-Vertrag. Begrenztes JSON mit Duplicate-Key-/NaN-/
  Größenprüfung; Fehlerausgaben enthalten nur feste Statuswerte.
- `deployment/c26g.staging.controller.json.example`: v2 ausdrücklich, alle
  Ausführungsflags false, keine Identitäten/Kataloge, Limits1. Auf der G-Basis
  ohne D korrekt inkompatibel; ausschließlich im temporären Verbund positiv
  geprüft. Kein automatisches Konfigurationsupgrade oder Store-/Journalbootstrap.
- `scripts/c26g_offline_validation.py`: gepinnter Gitarchivexport und kumulativer
  Draftdiff nur in neuer `/tmp`-Quellkopie; keine Index-/Ref-/Worktreeänderung.
  Unterdrückt Pluginautoload und nutzt den bestehenden Offlineguard. Testdaten
  liegen außerhalb des Quellroots, um die bestehende Persistent-Root-Policy zu
  erhalten. Kein Securitycheck wurde für die Tests abgeschaltet.
- `tests/test_c26g_readiness.py`:28 Fälle zu fehlenden Variablen, ungültigem
  Gate/Protokoll/Identity/Root/TLS/Issuer/Proxy/Netz/Ports/Worker/Mount/Image/
  Restart/Command/Profil, striktem JSON und geheimnisfreien CLIfehlern. Auf der
  Basis fehlt v2; dort ist die erwartete Ablehnung **kein** isolierter positiver
  Nachweis aller späteren Detailchecks. In der Verbundkopie werden deren
  Positivbasis und mutierte Einzelbedingungen tatsächlich geprüft.
- `tests/test_c26g_restore.py`: gemeinsamer gestoppter synthetischer Content-/
  Review-/Jobrestore, neue Roots, Rawbytes/Reviewrevisionen, Registration-/
  Jobidempotenz und interrupted-Zustand; Ledgermanipulation abgewiesen,
  ursprüngliche Daten weiterhin lesbar. Evaluationbackup nur als Testtechnik
  unter dem vorhandenen Reviewlock, kein neues Produktionstool.

Keine bestehenden Gate-, Auth-, TLS-, Executor-, Backup-, Retry-, Quarantäne-,
Hardlink- oder Produktivtemplatekontrollen geändert. Kein zweiter Controller,
keine neue Queue, DBmigration oder Runtimeabhängigkeit. Die fünf angeforderten
Dokumente enthalten aktuelle Quellgrenzen, vollständige Gate-/Entscheidungsmatrizen,
klassifizierte spätere Befehle und manuelles HOLD.

## Quellintegration ohne Änderung der Draftbranches

Basis exakt `778367396cd52526eca59edd41c2367f5e43b897`.
Kumulativer Gitdiff `e68275205fefb7a5f6db42bc45060e505bfcefb5` →
`7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` enthält #148/#157/D/E/F bereits.
D `8b0ba2d`, E `28e9a60`, F `7ffb4ed` bilden die erwartete Folge.
`git apply --check` und Anwendung auf der Archivkopie: konfliktfrei.
MAINT-03/03B/04/04B bleiben dabei Bestandteil der G-Basis; kein Whole-File-Ersatz
aus F über die späteren MAINT-Änderungen. Der Runner kopiert nur die vier neuen
G-Prüf-/Fixturedateien in die temporäre Kopie. Dokumente werden nicht zum Test
in andere Worktrees geschrieben.

Das ist eine Integrationssimulation, **kein** Merge/Commit/PR und kein Nachweis
der Integration in `master`. Gepinnte Quellobjekte müssen lokal verfügbar sein;
der Runner lädt fehlende Objekte nicht nach. Nach späterer tatsächlicher
Integration mit anderer Basis ist ein erneuter aktueller Testauftrag erforderlich.

## Umgebung

Vorhandener Interpreter ausschließlich lesend genutzt:
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`.
Python3.12.12, pytest9.1.1, Pydantic2.14.1, HTTPX0.28.1, PyYAML6.0.3,
PyMuPDF1.27.2.2; SQLiteversion im bestehenden Profil3.50.4.
Runtime-Lock sieht unter anderem Pydantic2.13.4 und PyMuPDF1.28.2 vor: **kein
exakter Runtimeimage-/Lockinstallationsbeleg**. uv wurde weder synchronisiert
noch aktualisiert; keine Pakete installiert. System-`python` fehlt, deshalb
expliziter vorhandener Interpreter. Ruff0.16.0 aus vorhandenem Pre-commit-Cache.

UI: Archivkopie des lokal vorhandenen Gitobjekts
`e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`, vorhandener Interpreter
`/home/robfra/0_Portfolio_Projekte/personal-assistant-ui-c26b/.venv/bin/python`.
Weder UI-Arbeitsbaum noch UIbranches/Venv geändert.

## Ausgeführte Läufe

| Lauf | Ergebnis | Beleg / Grenze |
| --- | --- | --- |
| Erste neue G-Basisfälle | **29 passed**, 9,30s | `/tmp/c26g-base-tests.xml`; ohne D positive Modellablehnung, erster Verbundrestore |
| Früher Konfigurationslauf auf Verbundkopie | **11 passed,17 errors** | `/tmp/c26g-composite-config.xml`; neuer Testhelfer interpolierte fälschlich `${VAR}` in einem YAMLkommentar |
| Früher breiter Verbundlauf | **577 passed,1 skipped,17 errors**,166,31s | `/tmp/c26g-composite-suite.xml`; dieselben17 Fixturefehler, bestehende D/E/F-/C16-/C22-Fälle grün; Skip betrifft externen echten Compose-CLItest |
| Erster neuer Kurzrunner | **28 passed,1 failed**,3,07s | `/tmp/c26g-offline-pzuxf5ch/result.xml`; Testdaten versehentlich im Quellroot, ContentStore verweigerte korrekt die Initialisierung |
| Korrigierter vollständiger Runner | **594 passed,1 deselected**,142,48s | `/tmp/c26g-offline-qyei33ap/result.xml`; keine Skips/Fehler, externer Composefall explizit abgewählt |
| UI HTTPS-/Container-Startschutz | **20 passed**,4,487s | unittest in `/tmp/c26g-ui-hg161gua`; keine zusätzliche Subtestzahl behauptet; Netzwerk explizit gesperrt, nur eigene Fake-OIDC-/Tokenfiles |
| G-Basis: Contentbackup/-Recovery, EvaluationStore, PDFrestore, Monitoring und Workflow-Snapshot plus neue Fälle | **127 passed,1 deselected**,159,49s | `/tmp/c26g-base-regression-final.xml`; externer echter Listenerfall abgewählt; vor Verstärkung des neuen Jobrestorefalls |
| Verstärkter Job-/Verbundrestore und Konfigurationsfälle auf Verbundkopie | **29 passed**,6,30s | `/tmp/c26g-offline-8o2uno8j/result.xml`; finaler Code, einschließlich persistiertem interrupted-Job und Idempotenzreplay |
| Dieselben finalen neuen Fälle auf G-Basis | **29 passed**,7,60s | `/tmp/c26g-base-new-final.xml`; korrekte v2-Ablehnung auf dieser Basis und vollständiger gemeinsamer Restore |
| Echte lokale Compose-CLIauswertung und HTTPS-Konfigurationsnegative | **46 passed**,12,03s | `/tmp/c26g-compose-render.xml`; nur Docker Compose5.0.2 `config`, kein Dockerdaemon/Containerkontakt, keine Downloads |
| Zusätzlich echter C26-Renderer, vier Profilkombinationen und gepaarter G-Prüfer | **4 Profilprüfungen +1 Paarprüfung bestanden** | Ohne Profil0 Rollen, Runtimeprofil2, Workerprofil1, beide3; echte normalisierte Backend-/UI-Konfiguration mit synthetischen Werten und simulierten Coolifylabels. Keine zusätzlichen Pytestfälle daraus zählen |

Die beiden eigenen Testhelferfehler sind behoben: YAMLkommentarzeilen werden vor
der nur testspezifischen Interpolation ausgelassen; der Runner legt Testdaten
in einem eigenen benachbarten `/tmp`-Root ab. Kein Produktivcheck gelockert.
Ein initialer Archivexport mit dem älteren System-Python scheiterte am fehlenden
`tarfile.extractall(filter=...)`; mit dem dokumentierten Python3.12 durchgeführt.
Keine dieser Vorbereitungsfehler ist ein Produktivbefund.

Die Restoreneuprüfung wurde anschließend um einen tatsächlich persistierten
interrupted-Job mit eigenem Idempotenzschlüssel verstärkt; der endgültige
Nachlauf ist in der Tabelle ausdrücklich getrennt. Der breite594er-Lauf wurde
vor dieser zusätzlichen Testassertion und der Ergänzung des festen G15-
Blockertexts ausgeführt; die betroffenen29 Fälle danach erneut auf beiden
Quellständen. Bestehender Anwendungscode und Gatekontrollen blieben identisch.

Testzahlen überlappen und werden nicht zu einer fiktiven Gesamtsuite addiert.
Keine Behauptung vollständiger Repository-, UI-, SDK-, Container-, Browser-
oder Hosted-CI-Abdeckung. Die bekannten roten MAINT-Prozessläufe bleiben als
historische, kausal offene Befunde erhalten; dieser Auftrag verändert ihre
Statistik oder Sicherheitsgrenzen nicht.

## Was die geprüften Verträge belegen

| Bereich | Automatisch geprüfter Umfang | Offen |
| --- | --- | --- |
| Konfiguration | Deaktivierte v2-Positivbasis und mutierte negative Gate-/Netz-/Mount-/Image-/TLS-/Proxy-/Issuerbedingungen; zusätzlich echte lokale Compose5.0.2-Auswertung | Echter Coolifyrenderer, Laufzeitdateien, Paket-/Zertifikatsinhalt, vollständige Laufzeitsemantik |
| C26-D | Admission/Dispatch/Drain, vollständiger Operationscope, Einmalpermit, Versions-/Journal-/Approval-/Recovery-/Rollback-/Resumeprüfungen | Verbindliche produktive Root-/Writerpolicy und echte Freigabe |
| C26-E | MockTransport, Nonces/Replays, TLS-Pin-Kontext ohne Netzwerk, Credentials/Freshness/Budgets, feste Geheimnisfehler und Capturetrennung | Echter Handshake/Producer/Readrechte/Registryverifier; serverseitige Coolifyfrische |
| C26-F | Fixtureissuer, lokaler Testwitness, CAS/Grantverbrauch/Fencing, Crash-/Lock-/Claim-/Rollback-/Resume und inerter Driver | Produktiver Operatorverifier, unabhängiger externer Witness, Koordinatorbetrieb, Livevertrag und echter Driver |
| Persistenz | Temporäre SQLite/WAL/flock, Content-/Blob-/Review-/Jobrestore, Hash-/Schema-/Ledger-/ACL-/Idempotenz, keine Aktivierung | Reales Zielvolume, konsistenter produktiver Verbundadapter, Offsite/Encryption/RPO/RTO |
| UI | ASGI-Header-/Origin-/Proxy-/Session-/Rollen-/Startschutz, synthetische Secretfiles | Echtes OIDC/Browser/TLS/VPN/WebSockets/Rotation/Widerruf |

D/E/F sind kompatibel **als Offlineverträge**. Die Livegrenze ist absichtlich
geschlossen: E `Capture.gate_fixture()` verwirft authenticated Captures, D bleibt
synthetisch, F verlangt `offline_fixture`, Fixtureverifier, `local_test_only` und
inerten Driver. Ein positiver Lauf erzeugt weder einen Livegrant noch ein Permit
für produktive Containeränderungen. G-Vorlage und bestehende Legacy-v1-Vorlage
sind nicht austauschbar. Fachsettings fehlen zusätzlich im verwalteten
Containerlauncher; Details G15 der Readiness-Matrix.

## Reproduktion

**L – nur neue synthetische Quell-/Datenkopien, keine Produktion:**

```sh
C26G_TEST_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python
PYTHONDONTWRITEBYTECODE=1 "$C26G_TEST_PYTHON" -B scripts/c26g_offline_validation.py
PYTHONDONTWRITEBYTECODE=1 "$C26G_TEST_PYTHON" -B scripts/c26g_offline_validation.py --configuration-only
```

`--configuration-only` selektiert die28 Konfigurationsfälle und den einen
Verbundrestorefall. Der vollständige Runner verwendet16 Dateien, die oben
genannten Quellobjekte und den bestehenden `tests.offline_guard`.
Der Guard sperrt Netzwerk/Listener und direkte Docker-/SSH-/Cloudbefehle im
Pytestprozess, ist aber **keine transitive Betriebssystemsandbox**. Bestehende
Childprobes nutzen nur synthetische lokale Roots/Adapter; keine Serverkomponenten.

Der getrennte Compose-Lauf verwendet die exakt geprüften Tests, nur lokale
Konfigurationsauswertung. Dafür ist Docker Compose CLI, aber kein laufender
Daemon erforderlich. Keine pauschale External-Suite ausführen.

**L – auf der vom Runner ausgegebenen Verbundkopie, nur Compose-Rendering:**

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$C26G_TEST_PYTHON" -B -m pytest -q -o addopts= -p no:cacheprovider \
  --run-external tests/test_https_preflight.py \
  tests/test_deployment_operations.py::test_compose_cli_resolves_only_explicit_profiles \
  --basetemp=/tmp/NEW-c26g-compose-render
```

Die G-Fixtureinterpolation ist bewusst **kein** Ersatz für Compose. Im separaten
CLI-Paarcheck wurden dieselben deaktivierten Settings mit dem tatsächlich
gerenderten Dreirollenbootstrap und der tatsächlich gerenderten UI geprüft.
Coolify-Routerlabels bleiben dabei synthetisch; keine echte Ingressabnahme.

## Gitübergabe und notwendiger Erhalt

`git add --dry-run` scheiterte mit `index.lock: Read-only file system` im
gemeinsamen Gitverzeichnis. Keine Umgehung über separaten Index, Ref-/Gitconfig-
Änderung oder Remote-Schreibweg. Kein Commit/Push/PR/Merge. Der vorbestehende
Branch und Worktree bleiben erhalten; keine neuen Gitbranches/-worktrees
erzeugt und keine vorhandenen entfernt. Taskartefakte sind ausschließlich neue
G-Dateien im zugewiesenen Arbeitsbaum und eigene `/tmp/c26g-*`-Quell-/Test-/
Patchartefakte. Die anfangs erfolglos angelegte leere Tempwurzel bleibt ebenfalls
erhalten; keine pauschale Tempbereinigung.

Vollständiges Übergabepaket: `/tmp/c26g-delivery/c26g-readiness.patch`;
Manifest mit exakter Basis/Dateihashes/Patchhash und Anwendungsprüfung:
`/tmp/c26g-delivery/manifest.json`. Abschließende Prüfergebnisse unten.
Die fünf dauerhaften Berichte liegen im Arbeitsbaum, sind aber wegen explizitem
Mergeverbot und fehlenden Git-Schreibrechten **noch nicht in master integriert**.
Der AGENTS.md-Lifecycleabschluss bleibt ausdrücklich pending; keine erfolgreiche
Integration oder Bereinigung behauptet. Nach späterer Integration auf den dann
aktuellen Default-Tree Inhalte vollständig erneut verifizieren.

## Abschließende Qualitäts- und Patchprüfung

Ruffcheck und Formatcheck der vier neuen Pythondateien bestanden; keine
Suppressions. Python-AST und JSONvorlage geparst, alle13 relativen Dokumentlinks
aufgelöst, Whitespaceprüfung bestanden. Geprüfte D/E/F-/C27-/G-/Defaultheads
nach der Arbeit unverändert. Keine Produktions- oder Defaultbranchdatei geändert.

Das Übergabepaket enthält ausschließlich die zehn neuen G-Dateien: fünf
Dokumente, zwei Skripte, zwei Tests und eine deaktivierte Controllervorlage.
Prüfverfahren: rückwärts `git apply --check` gegen den Arbeitsbaum, vorwärts
Check und tatsächliche Anwendung in frischem `git archive` der exakten G-Basis,
anschließend byteweiser/SHA-256-Abgleich aller zehn Dateien. Alle bisherigen
Archivdateien bleiben dabei unverändert. Das Manifest sichert die exakte
Dateiliste, Hashes und Prüfergebnisse. Kein Gitindex und keine Ref wird dabei
geschrieben; Patchprüfung ist keine Integration.
