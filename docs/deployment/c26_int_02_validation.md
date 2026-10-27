# C26-INT-02 – Regression Stabilization & UI Completion

27.10.2026. **HOLD.** Kein Deployment, keine Produktionsfreigabe. C26-04 bleibt
DEFERRED. Kein Hetzner-/Coolify-/DNS-/Firewallzugriff, keine Downloads, echten Jobs,
produktiven Daten, Live-LLM-Aufrufe, echten OIDC-Secrets oder GitHubmutationen.
Vorläuferbelege werden nicht überschrieben oder als neue Erfolge gezählt.

## Ausgangsstand und Grenzen

Der vorherige Integrationsstand ist im dauerhaften Pilotworktree auf
`feat/c26-pilot-integration`, Commit `be03e83f3f09956e9b95b9652f860fa73af29c4a`,
gesichert. Zu Auftragsbeginn keine tracked Änderungen, nur das bestehende
untracked `artifacts/`. Alle 69 Dateien des früheren Quellmanifests stimmen mit
diesem Commit überein. [Vorbereitung](../../artifacts/c26_int_02/preflight.json).

Lesend über den GitHubconnector neu geprüft: Backend-master
`a8af1d9372eb435d3e1331c33b047d21120d57c2`, UI-main
`ba34e98c14e66921bf9c515c82a16201bc8baa1a`.
[Lesende Abschlussverifikation](../../artifacts/c26_int_02/final-remote-state.json)
bestätigt beide unverändert. Der lokale Branch `master`
(`c1007ef…`) und der primäre UI-main-Checkout (`b2cf9ca…`) sind veraltet und
werden nicht als aktuelle Referenz ausgegeben. UI-Patchbasis ist der vorhandene
saubere Codecommit `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`; Live-main ändert
gegenüber ihm ausschließlich `docs/c26_https.md`, +16/-0.

Das Anlegen von `fix/c26-int-02-regression-ui` wurde durch schreibgeschützte
geteilte Gitmetadaten abgewiesen. Keine Branch-/Index-/Worktreeänderung wurde
durch Umgehung erzwungen. Änderungen und vollständige Patches bleiben im
bestehenden persistenten Backendworkspace. Der tatsächliche UI-Checkout liegt
außerhalb des beschreibbaren Bereichs: **UI-Patch dort nicht angewendet und nicht
getestet.** Die ausdrücklich erlaubte Übergabe liegt separat unter
[handoff](../../artifacts/c26_int_02/handoff/). UI-Tests auf exportierten Fixtures
sind davon getrennt gekennzeichnet.

## Ursachen und Änderungen

| Problem | Root Cause | Fix | Neue Tests | Ergebnis | Restunsicherheit |
| --- | --- | --- | --- | --- | --- |
| Historische Materialplan-Quarantäne | Ursprünglich nur `OperationalError` erhalten; Statement/Code nicht rekonstruierbar. Neue Diagnose erfasst realen `SQLITE_BUSY` (5) bei `BEGIN IMMEDIATE` im Guardian eines Executor-Neustarts. | Vorhandene begrenzte Verbindungswiederöffnung bis zum noch nicht begonnenen `BEGIN` ausgedehnt; kein höherer Timeout, kein Replay von Körper/Commit. Private redigierte Fehlerbelege. | Tatsächlicher reservierter SQLitewriter nach PRAGMAsetup; roter/grüner Grenztest; dauerhafte Locks, Rollback und Commitfehler; echte Pilotpläne. | Siehe tatsächliche Läufe unten. | Der historische Fall ist nicht eindeutig mit diesem Mechanismus gleichgesetzt. |
| Worker-/Cancel-/Resume-Lock | Mehrere legitime Writer trotz eines Ausführungsworkers: API/Cancel, Heartbeat, Guardian und Adapterinitialisierung. Die bisherige BUSY-Behandlung endete vor `BEGIN`. | Nur BUSY vor erfolgreichem Transaktionsbeginn und innerhalb bestehender Setup-Deadline erneut öffnen; `in_transaction` verhindert jedes Wiederholen einer begonnenen Transaktion. | Vier unabhängige Prozesse, WAL-/Bootstrapwechsel, beide kontrollierten Commitreihenfolgen Cancel/Completion, echte Cancel-/Resumeprozesse. | Siehe Läufe und Wiederholungen. | Alte `Store.all`-Ausnahme verlor genaue Quell-/Fehlerphase; keine Behauptung, jedes denkbare Lockproblem sei behoben. |
| PDF-Workflow-/Restore Exit3 | Exit3 ist eine generische interne Adapterexception vor Restore. Derselbe Fehlercode tritt neu auch auf unverändertem Live-master bei synthetischem `material_planning` auf. Das beweist keine identische Ursache. | Adapter schreibt auch bei Storeinitialisierungsfehlern numerischen SQLitecode und sichere Kategorie; Guardian ergänzt Phase. Kein automatischer Retry oder Quarantänereset. | Isolierte PDFläufe beider Basen, gleiche unveränderte 12 Testmodule, Wiederholungen mit Reihenfolgewechsel. | Siehe Vergleich. | Ursprüngliche konkrete PDFexception bleibt mangels damaliger Diagnose unbewiesen. |
| Material-Publikation nach Cancel | `os.link(temp, target)` vor `unlink(temp)` hinterließ beim harten Abbruch zwei Namen desselben Inodes. Neuer Worker-Gruppenlauf reproduziert dies; unveränderter Vorläufer scheitert deterministisch am Syncpunkt. | Linux `renameat2(RENAME_NOREPLACE)` veröffentlicht in einer Namensraumoperation. Bestehende Dateien/Symlinks werden nicht ersetzt; kein Entfernen alter Reste. NUL-Pfade werden vor Übergabe an native C-Strings verworfen. | Harter Childexit am Directorysync, bestehende Datei/Symlink, NUL-Pfad. Historischer MAINT-Test verlangt neuen Einzel-Linkzustand und prüft anschließend weiterhin Ablehnung/Erhalt künstlicher unbekannter Hardlinks. | Roter Ursachenbeleg, grüner Gegenbeleg und Worker-/Restore-Nachlauf erhalten. | Zielkernel/-filesystem muss no-replace rename unterstützen; andernfalls fail-closed. Kein produktiver Restorebeweis; andere unveränderte Hardlink-Publikationspfade sind nicht pauschal abgedeckt. |
| Materialplan in Streamlit | Ergebnisroute vorhanden, UI zeigte nur Status und Artefaktmetadaten. Außerdem konnte ein abgeschlossener Plan trotz Workspacequarantäne gelesen werden. | Separater UI-Patch: frischer autorisierter Jobread, begrenzter Ergebnisread, Artefaktbindung und sichere JSONprojektion. Backend sperrt vor und nach Dateilesung bei Quarantäne mit 423 / `quarantined`. | 12 neue UI-Client-/AppTestmethoden, echter synthetischer IPCdurchlauf; Backendmarker während/vor Ergebnisread. | UI-Patch auf Fixture geprüft; tatsächliche UI-Anwendung ausstehend. | Keine echte OIDC-/Browser-/TLS-Abnahme; siehe UI-Vertrag. |
| Zusätzlich beobachteter Suchtest | Gesamte Pagegleichheit erwartet bytegleichen Cursor über einen Sekundenwechsel. Ein neuer Cursor bindet jedoch `expires = int(time.time()) + 300`. | Keine Änderung an C24-R oder dessen Test. Diagnostischer Testhook erzwingt auf beiden unveränderten Testdateien denselben Einsekundenwechsel. | Beidseitiger isolierter Probe: nur `next_cursor` verschieden, Treffer identisch. | Vorbestehender Testzeiteffekt belegt; rote Nachweise bleiben rot. | Separate Testvertragskorrektur außerhalb dieses Auftrags; nicht als neuer Materialplanfehler eingestuft. |

### SQLite- und Sicherheitsgrenzen

Jeder Verbindungskontext öffnet eine eigene Connection und schließt sie in
`finally`. Neue Prozesse öffnen eigene Stores; keine gemeinsame Connection wird
über Thread-/Prozessgrenzen weitergegeben. Initialisierung bleibt unter dem
bestehenden Bootstrapflock. Schema-/Identitätsprüfung kommt vor WAL-Umschaltung;
`foreign_keys=ON` und `synchronous=FULL` bleiben erhalten. Schreiboperationen
beginnen mit `BEGIN IMMEDIATE`; Job und Event werden gemeinsam committed.
Rückgabestatus und idempotente Terminalübergänge bleiben unverändert.

Ein erfolgreicher `BEGIN` verlässt die Wiederöffnungsphase endgültig. Jeder
Körper-/Commitfehler führt zu Rollback und Propagation; auch LOCKED, Nicht-BUSY
und erschöpfte Setup-Deadline bleiben Fehler. Der vorhandene Connectiontimeout
von maximal zwei Sekunden wurde nicht erhöht. Die Setup-Deadline begrenzt
Wiederöffnungen, sie ist keine harte Echtzeitgarantie gegen Hostpausen.

Der Publikationsfix betrifft den konkret reproduzierten `storage.publish_bytes`-
Pfad. Andere unveränderte exklusive Hardlinkpublizierer, beispielsweise im
Rohdateiimport, werden nicht pauschal ersetzt. Eine vollständige Crashrecovery
aller Material-/Backuppfade wird damit nicht behauptet. Nicht verfügbare native
No-replace-Semantik (einschließlich nicht unterstützter Plattformen/Volumes)
führt nun in diesem Pfad ausdrücklich zum Fehler; die Pilotlaufzeit ist Linux.

`adapter-failure.v1.json` und `guardian-failure.v1.json` liegen ausschließlich im
privaten Jobverzeichnis, exklusiv mit 0600, ohne Ersetzen/Folgen von Symlinks.
Sie enthalten feste Kategorie/Komponente, numerischen SQLitecode und eine feste
Phasenmenge. Keine SQLstatements, Exceptiontexte, Quellbytes, Umgebungen, Tokens
oder Tracebacks. Ein Diagnosefehler ändert keine Ausführungsentscheidung.
Quarantänemarker und ursprüngliche quarantänisierte Jobs bleiben unangetastet.

Der neue Begin-Grenztest injiziert einen echten reservierten WALwriter **nach**
PRAGMAsetup. Ein testlokal ausgeschalteter Busyhandler macht die Ablehnung sofort
sichtbar; der Writer wird erst nach Schließen dieser abgewiesenen Connection
freigegeben. Vor dem Fix scheitert genau der Begin, danach läuft der Körper
einmal. Dies belegt die korrekt begrenzte Behandlung dieses Fehlermodus; es
rekonstruiert nicht automatisch den Busyhandlerverlauf aller alten Ausnahmen.

### PDF-/Gruppenvergleich und weitere rote Vorläufe

Unveränderter Live-master und Kandidat bestehen den isolierten PDF-/Restorefall.
Der gleiche Gruppenvergleich nutzt zwölf byteidentische Testmodule, gleiche
Pythonumgebung und denselben Offlineguard; kandidateneigene Tests werden auf
beiden Seiten gleich ausgelassen. [Basissnapshot und Testhashes](../../artifacts/c26_int_02/baseline.json).
Auf master endet ein Materialplan mit Exit3/internal; dessen ursprünglicher
Adapter speichert keinen genauen Code. [Forensik](../../artifacts/c26_int_02/master-worker-forensics.json).

Der Kandidaten-Gruppenlauf **vor** der Begin-Korrektur liefert einen neuen
Guardianfehler `sqlite_code=5`, `phase=begin`, Quarantäne und korrekt verweigerten
Executorneustart. [Unveränderter Diagnosebeleg](../../artifacts/c26_int_02/guardian-begin-busy.json).
Ein weiterer Gruppenfehler betrifft den oben kausal eingegrenzten Cursorvergleich.
Keiner dieser roten Läufe wird durch spätere Erfolge überschrieben.

Der erste UI-IPC-Lauf auf dem absichtlich geänderten Arbeitsbaum scheitert bei
Workflowfällen an `git diff --quiet HEAD`; zusätzlich scheitert ein Reviewharness
an seinem bestehenden Bereitschaftslimit. Diese Timeoutursache ist damit noch
nicht als Produktfehler oder harmloser Effekt bewiesen. Ein sauberer, aus den
exakten aktuellen Produktbytes erzeugter Testcommit wird ausschließlich als
Testfixture benutzt, ausdrücklich nicht als Liefercommit. Ein dortiger weiterer
Cancel-/Resumefehler vor dem Begin-Fix bleibt als roter Exit3-Nachweis erhalten.

Neue Testentwicklungsfehler bleiben ebenfalls dokumentiert: drei UI-AppTests
lasen nach nur einem Rerun einen erwartungsgemäß noch zwischengespeicherten
Jobstatus; der Test wartet nun die vorhandenen Pollintervalle wie die bisherigen
Tests ab. Ein Completion-Konkurrenztest hatte noch keine erfolgreiche
Artefaktreferenz konstruiert; diese gültige Testvorbedingung wurde ergänzt. Der
erste 300-Zyklen-Stress überschritt unter parallelen Suites sein neu erfundenes
30-Sekunden-Testlimit, ohne erhaltenen SQLitefehler; der reguläre Regressionstest
nutzt 64 Zyklen, der längere Messlauf wird getrennt ausgewiesen. Keine produktiven
Timeouts, Sicherheitsassertionen oder Quarantänen wurden dafür gelockert.

## Tatsächlich ausgeführte Tests

| Lauf | Passed | Failed | Errors | Skipped | Deselected |
| --- | ---: | ---: | ---: | ---: | ---: |
| [broad-final](../../artifacts/c26_int_02/broad-final.log) | 3138 | 1 | 0 | 25 | 180 |
| [fixes-final](../../artifacts/c26_int_02/fixes-final.log) | 24 | 0 | 0 | 0 | 0 |
| [repeat-1](../../artifacts/c26_int_02/repeat-1.log) | 7 | 0 | 0 | 0 | 0 |
| [repeat-2](../../artifacts/c26_int_02/repeat-2.log) | 7 | 0 | 0 | 0 | 0 |
| [repeat-3](../../artifacts/c26_int_02/repeat-3.log) | 7 | 0 | 0 | 0 | 0 |
| [repeat-4](../../artifacts/c26_int_02/repeat-4.log) | 7 | 0 | 0 | 0 | 0 |
| [repeat-5](../../artifacts/c26_int_02/repeat-5.log) | 7 | 0 | 0 | 0 | 0 |
| [compose](../../artifacts/c26_int_02/compose.log) | 92 | 0 | 0 | 0 | 0 |
| [ui-gated-contract](../../artifacts/c26_int_02/ui-gated-contract.log) | 1 | 0 | 0 | 0 | 0 |
| [master-pdf-isolated](../../artifacts/c26_int_02/master-pdf-isolated.log) | 1 | 0 | 0 | 0 | 0 |
| [candidate-pdf-isolated](../../artifacts/c26_int_02/candidate-pdf-isolated.log) | 1 | 0 | 0 | 0 | 0 |
| [master-runtime-group](../../artifacts/c26_int_02/master-runtime-group.log) | 263 | 1 | 0 | 0 | 2 |
| [candidate-runtime-group (vor Begin-Fix)](../../artifacts/c26_int_02/candidate-runtime-group.log) | 262 | 2 | 0 | 0 | 2 |
| [pre](../../artifacts/c26_int_02/pre.log) | 33 | 1 | 0 | 0 | 0 |
| [publication-red](../../artifacts/c26_int_02/publication-red.log) | 2 | 1 | 0 | 0 | 0 |
| [publication-green](../../artifacts/c26_int_02/publication-green.log) | 27 | 0 | 0 | 0 | 0 |
| [begin-red](../../artifacts/c26_int_02/begin-red.log) | 0 | 1 | 0 | 0 | 0 |
| [begin-green](../../artifacts/c26_int_02/begin-green.log) | 15 | 0 | 0 | 0 | 0 |
| [transitions-red](../../artifacts/c26_int_02/transitions-red.log) | 2 | 2 | 0 | 0 | 0 |
| [transitions](../../artifacts/c26_int_02/transitions.log) | 4 | 0 | 0 | 0 | 0 |
| [diagnostics](../../artifacts/c26_int_02/diagnostics.log) | 12 | 0 | 0 | 0 | 0 |
| [churn](../../artifacts/c26_int_02/churn.log) | 1 | 0 | 0 | 0 | 0 |
| [master-cursor-probe (absichtlich roter Diagnoseprobe)](../../artifacts/c26_int_02/master-cursor-probe.log) | 0 | 1 | 0 | 0 | 0 |
| [candidate-cursor-probe (absichtlich roter Diagnoseprobe)](../../artifacts/c26_int_02/candidate-cursor-probe.log) | 0 | 1 | 0 | 0 | 0 |
| [UI final, vollständige Standardsuite + alle IPCopt-ins](../../artifacts/c26_int_02/ui-final.log) | 189 | 0 | 0 | 0 | 0 |
| [UI früherer Defaultlauf](../../artifacts/c26_int_02/ui-full.log) | 164 | 0 | 0 | 25 | 0 |
| [UI-IPC nach Begin-Fix](../../artifacts/c26_int_02/ui-ipc-fixture.log) | 25 | 0 | 0 | 0 | 0 |

Die Wiederholungen sind je sieben tatsächliche Fälle, keine 35 neuen unterschiedlichen Tests. Der
300-Zyklen-Messlauf mit vier unabhängigen Prozessen endet mit vier Exitcodes 0,
SQLiteintegrität `ok` und dem erwarteten finalen Heartbeat;
[Messwerte](../../artifacts/c26_int_02/extended_churn.json). Kein produktiver Timeout geändert.

Weitere rote UI-Vorläufe: 12 Methoden mit 3 AppTestfehlern; 25 IPCmethoden mit
6 Errors (einschließlich mehrerer Subtests); sauberer Vor-Begin-Fix-Snapshot mit
25 Methoden und einem fehlgeschlagenen Cancel-/Resume-Subtest. Diese Ergebnisse
werden nicht durch Subtraktion als zusätzliche Passed-Methoden ausgegeben;
Rohlogs und Summary bleiben erhalten. Zwei früh abgebrochene breite Versuche
haben keine vollständige Endbilanz. Einer enthält ein nicht abschließend
zugeordnetes Setup-`E`; dessen fehlender Traceback wird nicht durch einen
behaupteten Ursachenbeleg ersetzt. Sie sind weder erfolgreich noch
als vollständig ausgeführte Suite gezählt.

**Nicht ausgeführt:** tatsächliche UI-Repository-Anwendung/-Tests, reale OIDC-/TLS-/VPN-/
WSS-/Browser-/Hostabnahme, Imagepull/-build/-start, positive gefrorene Runtimeinstallation,
produktiver Backup/Restore, produktive LLMrequests, Downloads und Jobs.


Vollständige getrennte Bilanz: [summary.json](../../artifacts/c26_int_02/summary.json).
Alle neuen Logs/XML bleiben unter `artifacts/c26_int_02/`; die früheren
`artifacts/c26_pilot_integration/`-Nachweise bleiben unverändert erhalten.
Relevante Originalfehlerbelege sind zusätzlich bytegleich und ausdrücklich
historisch markiert [gesichert](../../artifacts/c26_int_02/historical/ORIGIN.json);
sie werden nicht als neue Tests gezählt.
Wiederholungen und Basissuiten werden nicht zu einer Zahl unterschiedlicher
bestandener Tests addiert. Skips, Deselections und nicht ausgeführte Bereiche
zählen nicht als passed.

## Antworten auf die Abschlussfragen

1. **Sind die drei ursprünglichen Fehler behoben?** Nicht für alle historisch kausal bewiesen. Der neu präzise erfasste SQLite-Begin-Fehlermodus und der konkrete Hardlink-Abbruchdefekt sind reproduziert und korrigiert. Die ursprünglichen OperationalError-/PDF-Exit3-Daten enthalten keine hinreichende Fehlerphase; diese Lücke wird ausdrücklich beibehalten. Die betroffenen aktuellen synthetischen Fälle bestehen in den neuen Wiederholungen und im finalen Quellstand.
2. **Neue Regressionen?** Kein weiterer bestätigter Produktdefekt im final geprüften Materialplan-Pilotpfad. Zusätzliche rote Vorläufe sind vollständig ausgewiesen. Der finale Such-Cursor-Testfehler ist auf beiden Basen deterministisch als Testzeiteffekt belegt; C24-R bleibt unverändert.
3. **Materialplanung offline zuverlässig?** Der synthetische, gated Einjobpfad und die authentifizierten Ergebnisreads sind wiederholt bestanden. Dies ist ein begrenzter Offline-Nachweis, keine Aussage über echte Materialien, Downloads, LLMs, Hostpausen oder ungeprüfte Images.
4. **Vollständiger authentifizierter UI-Abruf?** Auf der separat exportierten Testfixture mit echten synthetischen Workerprozessen, individuellen C16-Testtokens, APIbytes und kanonischer Streamlit-App nachgewiesen. Im tatsächlichen UI-Repository noch nicht angewendet/getestet; keine echte IdP-/Browseranmeldung.
5. **Commits/Patches?** Ausgangscommit `be03e83f3f09956e9b95b9652f860fa73af29c4a`; kein neuer Backend- oder UI-Liefercommit wegen der dokumentierten Schreibgrenzen. Vollständiger Backendpatch und separater UI-Patch einschließlich Tests, SHA-256-Dateien und Anwendungsprüfung in der persistenten Übergabe. Testfixturecommits sind keine Liefercommits.
6. **Tatsächliche Tests?** Die obige Tabelle, Rohlogs, JUnitdaten, Quellmanifeste und Befehlsaufzeichnungen bilden ausschließlich tatsächlich ausgeführte Läufe ab. Passed/Failed/Errors/Skipped/Deselected und nicht ausgeführte Bereiche bleiben getrennt; keine Addition überlappender Suiten.
7. **Blocker für eingeschränkten Hetznerpilot?** Historische Kausalitätslücke, tatsächliche UI-Anwendung, reguläres Review/Integration sowie produktive Trust-/Build-/Driverkette, Installations-/Imageclosure, Ressourcen-/Triggerinventar, sicherer Rückweg und tatsächliche Host-/Auth-/Netzabnahme. Kein Offlinepass hebt diese Blocker auf. C26-04 bleibt DEFERRED.
8. **Nächste technische Aufgabe?** Den vollständigen UI-Patch in einem eigenen beschreibbaren UI-Featureworktree auf der bestätigten main-Basis anwenden und mit dem exakt gesicherten Backendkandidaten validieren/reviewen. Verbleibende SQLite-/Exit3-Ausnahmen ausschließlich mit der neuen Phasendiagnose gezielt klassifizieren; Cursor-Testvertrag als separate C24-R-Aufgabe behandeln. Keine Deploymentfreigabe.


## Reproduktion

Vorhandener Backendinterpreter:
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.venv/bin/python`.
Keine Pakete installiert oder aktualisiert. Backend Python 3.12.12 / SQLite 3.50.4;
[Backendumgebung](../../artifacts/c26_int_02/backend-environment.json),
[UIumgebung](../../artifacts/c26_int_02/ui-environment.json).
Die anfängliche Ressourceninventur lief mit System-Python und dessen SQLite
3.40.1; diese Versionszahl ist ausdrücklich nicht die Testvenvversion.
[Startressourcen](../../artifacts/c26_int_02/resources-start.json).
Cgroup-/UID-weite Fremdlast ist in dieser Sandbox nicht vollständig beobachtbar;
frühe Gruppenläufe überlappten mit getrennten synthetischen Testwurzeln.

Reproduktion nur mit **neuen**, externen synthetischen Testwurzeln, niemals mit
vorhandenen Quarantäneroots. Grundprofil:

```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.venv/bin/python \
  -m pytest -v --tb=short -o addopts= -p no:cacheprovider \
  -p tests.offline_guard -m 'not external_integration' \
  tests/test_job_store_contention.py tests/test_c26_int_02_sqlite.py \
  tests/test_job_failure_diagnostics.py tests/test_material_publication.py \
  tests/test_c26_pilot_workflow.py tests/test_c26_pilot_results.py \
  tests/test_cs50_batch_worker.py tests/test_deployment_pdf_restore.py \
  --basetemp=/tmp/c26-int-02-operator-NEW
```

Exakte tatsächlich benutzte Gruppen, Reihenfolgen, Roots und Umgebungen stehen
in den gesicherten Laufskripten und
[followup-commands.json](../../artifacts/c26_int_02/followup-commands.json).
Der Cursorprobe ist ein diagnostischer, absichtlich roter Vergleich; keine
Produkt-/C24-R-Datei wurde dafür verändert. Native Composeprüfungen verwenden
nur `docker compose config`, explizite synthetische Inputs und einen nicht
existierenden Daemonsocket; kein Pull/Build/Containerstart.

## UI-Vertrag und Sicherung

[Separater UI-Vertrag](../../artifacts/c26_int_02/handoff/ui-files/docs/c26_material_plan.md).
Der Backendhash bindet die ursprünglichen Datei-Bytes. Die normalisierte
JSONantwort kann diesen Hash nicht lokal erneut ergeben. Die UI prüft deshalb
die vollständige zurückgegebene Artefaktreferenz gegen den frisch autorisierten
Job und respektiert die serverseitige Hash-/Größenprüfung. Unvollständige Jobs
lösen keinen Ergebnisread aus. Die Projektion bewahrt numerische Abschnittsreferenzen und opaque Lecture-IDs,
zusätzlich zu Kurs, Materialnummer, Rolle, Format und Herkunftstyp.
Höchstens 256 KiB Datei, 260 KiB Antwort,
100 Materialien und 6 Kurse; keine ungefilterten Freitexte/URLs/Pfade/Secrets.

Die vollständige Lieferung liegt in [HANDOFF.md](../../artifacts/c26_int_02/handoff/HANDOFF.md):
[Backendpatch](../../artifacts/c26_int_02/handoff/backend.patch),
[UI-Patch](../../artifacts/c26_int_02/handoff/ui.patch),
[SHA-256](../../artifacts/c26_int_02/handoff/checksums.sha256),
[Dateiprüfsummen](../../artifacts/c26_int_02/handoff/source-checksums.sha256) und
[Anwendungs-/Bytevergleich](../../artifacts/c26_int_02/handoff/package-manifest.json).
Diese Lieferhüllen sind von ihrem eigenen Patch ausgenommen, damit keine
selbstrückbezüglichen Hashes entstehen. Alle beabsichtigten Quellen, Tests,
Dokumente und neuen synthetischen Belege sind durch die kuratierte Dateiliste
abgedeckt. `git diff --check`, tatsächlicher Forward-Apply gegen `be03e83`,
Reverse-Check und Bytevergleich aller beabsichtigten Dateien sind vor Abschluss
verlangt; die maschinenlesbare Bestätigung wird erst durch den ausgeführten
Packager erzeugt.

Kein Pushziel wurde ausdrücklich freigegeben, kein Push/PR/Merge ausgeführt.
Defaultbranchintegration und tatsächliche UI-Anwendung bleiben pending;
das ausdrückliche Mergeverbot geht der allgemeinen Lifecycle-Regel vor.
Nichts entfernt: vorhandene/geteilte Branches, Worktrees, Stashes, Venvs,
Daten und historische Quarantänen bleiben erhalten. Eigene Testfixtures und
synthetische Forensikroots bleiben bis Review/erlaubter Integration als
Reproduktionsbeleg erhalten. [Git-Artefaktinventar](../../artifacts/c26_int_02/git-artifacts.json).
Es existiert kein alleiniger Lieferstand unter `/tmp` und kein behaupteter
Defaultbranch-/Lifecycleabschluss.


## Restgrenzen und konkrete nächste Arbeit

C26 bleibt HOLD, C26-04 DEFERRED. Unbewiesene historische Exceptionursachen,
fehlende Anwendung/Tests im tatsächlichen UI-Repository sowie ausstehendes
reguläres Review/Integration sind transparent offen. Die produktive
Gate-Trustkette, unabhängige Producer-/Buildreceipts, Betreiberverifikation,
monotoner externer Witness und exklusiver Driver bleiben ungeklärt. Ebenso
frozen Runtimeinstallation/Imageclosure, tatsächliche UID-/Mount-/Cgroup-/
NPROC-/PID1-/Cancel-/Quotenabnahme, Ressourcen-/Triggerinventar und sicherer
Legacyrückweg. Echte VPN-/IPv4-/IPv6-/TLS-/OIDC-/WSS-/Browsernachweise fehlen.
Dieser Auftrag darf diese Livepunkte weder ausführen noch durch Fixtures ersetzen.

Nächster technischer Schritt: die separat gelieferte UI-Änderung auf einem
beschreibbaren UI-Feature-Worktree anwenden, gegen genau den hier geprüften
Backendkandidaten inklusive Gate-/Quarantänevertrag ausführen und beide Pakete
reviewen. Parallel bleibt ein gezielter SQLite-/Exit3-Ursachennachweis erforderlich,
falls die neuen redigierten Diagnosen noch unbehandelte Phasen zeigen. Eine
separate C24-R-Testvertragsaufgabe sollte Cursorinhalte und Cursorvalidierung
prüfen, ohne bytegleiche neue Ablaufzeit-Tokens über Sekundenwechsel zu fordern.
Keine Go-live-Freigabe und kein Merge durch diesen Auftrag.
