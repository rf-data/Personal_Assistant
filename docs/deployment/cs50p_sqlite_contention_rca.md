# C26-CS50P-05 – SQLite-Contention: Ursachenanalyse

28.10.2026. **HOLD. Kein Produktivfix und keine Betriebsfreigabe.**
Basis `81db9ed3f5fc7e0c3d6952b438f015ae6521af3c`, separater, bereits
bereitgestellter Detached-Checkout `Personal_Assistant-cs50p-05`.
Nur neue synthetische Datenbanken; keine bestehenden Job-/Quarantänedaten benutzt.

## Ergebnis und Beweisgrenze

Die neue Timeline belegt verweigerte Writeraufnahme trotz fortschreitender anderer
Writer: Ein `BEGIN IMMEDIATE` scheitert nach **2.004,241 ms**, während zwei andere
Prozesse **208 Commits** abschließen. Der betroffene Thread verbraucht in diesem
Intervall **2,046 ms CPUzeit**. Es gibt keinen erfolgreich begonnenen Körper und
keinen Replay. Die längste beobachtete überlappende Transaktion umfasst **90,394 ms**
zwischen erfolgreicher Begin-Rückkehr und Commit-Rückkehr.

Dieser Fall benötigt **keine wiederholte Storeinitialisierung**, keinen Controller,
Guardian oder Executor: drei unabhängige Stores, 300 atomare Inkremente je Prozess,
keine Pausen, ein gepinnter WAL-Leser genügen. Die Ursache dieses neuen Fehlers ist
damit Konkurrenz um die SQLite-Einzelwriteraufnahme innerhalb des bestehenden
Budgets mit ausbleibendem Fortschritt eines Contenders (Writerstarvation).
Ein einzelner Lockhalter über das gesamte Fehlerintervall erklärt die 208 anderen
Commits nicht. Die Verteilung von Busyhandler-Schlafzeiten, Schedulerpausen und
Storage-Latenz ist mit Python-Aufrufgrenzen allein jedoch **nicht** bewiesen.
Ebenso wenig identifizieren diese Daten den Lockhalter des alten Native-Setupfehlers.

Der Kontrolllauf **ohne gepinnten Leser und ohne Reinitialisierung** scheitert
ebenfalls: zwei Beginfehler nach 2.048,102 beziehungsweise 2.013,109 ms;
währenddessen 207 beziehungsweise 216 andere Commits. Der künstliche lange
Lesesnapshot ist also ebenfalls keine notwendige Bedingung dieses Fehlermodus.
Ein einzelner Writer bestätigt dagegen 300/300 Inkremente. Ein einmaliger
Wiederholungspass mit drei Writern hebt die roten Fälle nicht auf.

737 bestätigte Inkremente (300/137/300), persistierter Wert 737, WAL,
`integrity_check=ok`, leeres `foreign_key_check`: Der rote Lauf zeigt fehlenden
Fortschritt, keine verlorenen oder doppelten bestätigten Writes. Das ist kein grüner
Stresstest. Rohereignisse und berechnete Zusammenfassung:
`artifacts/c26_cs50p_05/trace-no-reinit/` und `trace-no-reinit-summary.json`.

**Kleinster nächster Untersuchungsschritt:** den vorhandenen 3×300-Probe ohne
Reinitialisierung einmal auf einem isolierten lokalen Linux-/WAL-Testvolume mit
gleichzeitigen, PID-/Monotonic-korrelierten `fcntl`-, `fdatasync`-/`fsync`- und
Schedulerbelegen ausführen. Nur neue synthetische DBs. Damit zunächst Busyhandler-
Aufnahmelücken von Storage-/Schedulerpausen trennen; anschließend eine begrenzte,
geordnete Writeraufnahme als isolierten Kandidaten gegen denselben roten Probe
und die Sicherheitsregression prüfen. Kein Lock-/Timeoutumbau auf bloßen Verdacht.
`strace`/`perf` sind hier nicht verfügbar; CPU-Affinität allein isoliert keine I/O.

## Alte rote Belege verifiziert

Alle **61** Mitglieder von
`artifacts/c26_cs50p_03/raw-evidence.tar.gz` wurden gegen Länge und SHA-256 des
ursprünglichen `raw-evidence-manifest.json` geprüft. Archiv-SHA-256:
`a5f7c2ac729ae862daf68220689a02333e7e938b107359029cc743262383fb91`.
Prüfergebnis: `artifacts/c26_cs50p_05/historical-verification.json`.
Originaldateien und C26-CS50P-03-Berichte bleiben unverändert.

| Historischer Lauf | Roter Beleg | Was er nicht enthält |
| --- | --- | --- |
| baseline | 81/82 bestanden; Guardian `sqlite_code=5`, `phase=setup`, Quarantäne | Kein Beginfehler, keine Lockhalter-Timeline |
| sqlite-process | 64 und 300 Zyklen: Code 5, begin | Keine Haltezeiten/Operationsindizes |
| sqlite-diagnostic | 300: increment 12, 2,070246 s, Code 5, begin | Kein Nachweis eines einzelnen langen Writers |
| sqlite-final | ohne Pause 300: increment 184, 2,093511 s, Code 5, begin | Pausenpässe beweisen keine Ursachenbehebung |
| Resume / Native CLI | 10/10 beziehungsweise 5/5 bestanden | Kein Gegenbeweis zum roten Stressfall; überlappende Läufe nicht addieren |

Neuer **unveränderter Basislauf vor Instrumentierung**: 5 passed / 1 failed,
32,55 s. Diesmal scheitert **300 mit 10-ms-Pause**, increment 197,
2,024335 s, Code 5, begin. Die angeblich entscheidende Pausenvariable ist damit
keine zuverlässige Produktkorrektur. Log/JUnit: `baseline.log` / `baseline.xml`.

## Verbindungs- und Prozesstimeline

| Komponente | Verbindungen und Writeraufnahme | Kritischer Abschnitt |
| --- | --- | --- |
| Controller | Eigener Store; create/start/cancel schreiben; Status-/Resultleser separat | Jobvalidierung, Kapazitätsprüfung und Job+Eventupdate atomar; create liest die begrenzte Jobhistorie innerhalb des Writers |
| Executor | Eigener Store; Singletonflock schützt Executoranzahl, nicht SQLitewriter | Startup-/Stepheartbeat; Claim, Reconcile und Quarantäneübergänge. `serve` pausiert 100 ms; Native-Runloop 50 ms |
| Guardian | Neuer Prozess und Store je Job, eigener Lifecycleflock | Running-/Terminalupdate; Stop-/Cancelerkennung sind Reads. Payload/Cleanup/Artefaktdateilesen liegen außerhalb der Writertransaktion |
| Adapter | Weiterer Prozess mit eigenem Store beim Start | Initialisierung; Workflow-/Materialarbeit benutzt eigene Zustände und keine dauerhaft gehaltene Job-DB-Connection |
| Storeinitialisierung | Bootstrapflock serialisiert nur Initialisierungen | Immer `BEGIN IMMEDIATE`, auch bei unverändertem v1-Schema; danach separate Verbindung für WAL-PRAGMA |
| Native Status/Result | `mode=ro`, ohne Storeinitialisierung | Kein SQLwriter; WAL-/SHM-Metadaten können dennoch nötig sein |

Jeder Storekontext öffnet eine eigene Connection. Reihenfolge:
Connect → `foreign_keys=ON` → `synchronous=FULL` → bei Write `BEGIN IMMEDIATE`
→ Körper → Commit oder Rollback → Close. Kein geteilter Connectionpool und keine
Connectionweitergabe zwischen Prozessen. Keine nachgewiesene Connectionleckage.
Die ursprünglichen v1-Identitäts-/Schemaprüfungen bleiben vor der WAL-Umschaltung.

Die vorhandene Zwei-Sekunden-Setupdeadline begrenzt das Wiederöffnen ausschließlich
vor erfolgreichem Begin. Der SQLite-Busyhandler kann das Restbudget in einem
einzigen Begin verbrauchen. Danach sind weitere Wiederöffnungen korrekt verboten.
Die Deadline ist keine harte Echtzeitgarantie gegen Hostpausen. SQLite erlaubt
auch im WAL nur einen Writer; Busytimeout garantiert keine Aufnahme-Reihenfolge.
Siehe [Transaktionen](https://www.sqlite.org/lang_transaction.html),
[WAL-Konkurrenz](https://www.sqlite.org/wal.html#concurrency),
[Busytimeout](https://www.sqlite.org/c3ref/busy_timeout.html) und
[Busyhandler](https://www.sqlite.org/c3ref/busy_handler.html).

### Konkrete neue Fehlertimeline

Zeiten sind gemeinsame monotone Nanosekunden desselben isolierten Probelaufs;
PIDwerte gelten nur in dessen Namespace. Maschinell berechnete Werte stehen in
`trace-no-reinit-summary.json`, alle Ereignisse im Roharchiv.

1. Parent erzeugt neuen privaten Root, Schema und Heartbeat 0; hält WAL-Snapshot 0.
2. Drei spawn-Prozesse initialisieren je einmal und starten an einer Barrier.
3. Jeder öffnet pro Inkrement eine neue Connection und versucht Begin/Update/Commit.
4. PID 6 hat 137 Inkremente bestätigt und versucht Zyklus 137. Setup gelingt;
   Begin bleibt ohne erfolgreiche Aufnahme. PID 5 und 7 committen weiter.
5. Begin liefert nach 2.004,241 ms BUSY 5, `in_transaction=False`. Connection
   schließt; kein Körper, kein Commit, kein Jobneustart.
6. Andere Prozesse beenden je 300 Inkremente. Parent liest im alten Snapshot
   weiter 0, nach dessen Ende 737; Integrität und Foreign Keys bestehen.

## Instrumentierung und Reproduktion

Einzige Produktquelländerung: optionale DEBUG-Ereignisse des Loggers
`job_control.sqlite` in `Store.connection`. Die Standardkonfiguration aktiviert
DEBUG nicht. Erfasst werden PID/TID, monotone Start-/Ereigniszeit, Thread-CPUzeit,
Versuchsnummer, Writeflag, feste Stage, Transaktionsflag und numerischer Fehlercode.
Keine Pfade, Jobidentitäten, SQL, Parameter, Exceptiontexte, Tracebacks oder Secrets.
Loggerfehler ersetzen keine Ausführungsentscheidung; deaktivierte und fehlschlagende
Beobachtung sind getestet. Kein eigener Dateilogger, kein Flush/fsync im Produktpfad.

`scripts.sqlite_contention_probe` legt ausschließlich einen **neuen** Outputordner
und einen neuen privaten `/tmp/sqlite-probe-*`-Root an. Es nimmt keinen bestehenden
Datenbankpfad entgegen. Tracehandler puffern nur im Speicher; Ausgabe folgt nach
Ende der Transaktionen. Die Beobachtung verändert Timing; ein grüner Tracepass
widerlegt daher keinen roten Lauf. Operations-/Zykluslabels liefert nur der
synthetische Harness. Python-Grenzen sind keine Kernel-Lock-/fsync-Messungen.

READ-ONLY: Archivmitglieder, Hashmanifest, Zusammenfassungen und Logs ansehen.
CHANGE: folgende Befehle erzeugen ausschließlich neue synthetische DBs/Belege und
begrenzte Kindprozesse. Voraussetzung: vorhandener passender Pythoninterpreter,
neue Outputpfade, keine parallele Testsuite für die Messung. Hier verwendet:
Python 3.12.12, SQLite 3.50.4, vorhandene c24r-Testvenv; keine Installation.

```sh
PYTHONDONTWRITEBYTECODE=1 /PATH/TO/python -m scripts.sqlite_contention_probe \
  --output NEW_TRACE_DIRECTORY --cycles 300 --writers 3 --reinitialize-every 0
PYTHONDONTWRITEBYTECODE=1 /PATH/TO/python -m scripts.sqlite_contention_report \
  NEW_TRACE_DIRECTORY --output NEW_SUMMARY.json
```

Das Lastprofil ist festgelegt; Prozessscheduling und Auftreten des kurzen
Starvationfehlers bleiben zeitabhängig. Der neue ereignisgesteuerte Mehrprozesstest
hält dagegen einen realen reservierten Writer bis nach der Ablehnung des Contenders:
Heartbeat und selbst unveränderte Schemawiederöffnung scheitern deterministisch
an Begin, ohne Transaktionskörper. WAL-Read sieht unveränderte Daten; harter
Writerabbruch und Wiederöffnung beweisen Rollback. Dies reproduziert exakt die
Begin-/Fail-closed-Grenze, **nicht** automatisch die Ursache jedes Stressfehlers.

## Vermiedene Writes und geprüfte Korrekturkandidaten

| Kandidat | Befund | Entscheidung |
| --- | --- | --- |
| v1-Initialisierung nur lesend | Nachweislich unnötige Writeraufnahme für Schemakontrolle; Dauerlocktest zeigt Ablehnung auch ohne geplantes SQLupdate | Separater Optimierungskandidat. Schema-/Journalwechsel und Bootstrapvertrag müssen atomar geprüft bleiben. Kein Fix des roten reinit-freien Incrementfalls |
| Heartbeats seltener / Testpause übernehmen | Verändert Last, nicht Fairness; sogar 10-ms-Pausenlauf neu rot | Keine Produktänderung und keine Aufweichung des Livenessvertrags |
| Terminal-/No-op-Transition vor Writer zurückgeben | Könnte Writes sparen, muss aber Cancel/Completion und aktuelle Autorisierung atomar wahren | Kein ungeprüfter Fastpath; vorhandene atomare Rereads bleiben |
| Writerkörper verkürzen | Status-/Heartbeatwrites kurz, externe Payload-/Artefaktarbeit bereits außerhalb; alte Logs enthalten keine Haltezeiten | Kein belegter einzelner langer Anwendungskörper als Ursache dieses neuen Fehlers |
| Länger warten / weitere Retries / Replay | Verdeckt Budgeterschöpfung oder riskiert doppelte Wirkung | Verboten; unverändert |
| Zusätzlicher Mutex/Writerbroker | Geordnete Aufnahme könnte Starvation adressieren; bloßes nichtblockierendes flock-Polling garantiert selbst keine Fairness | Keine spekulative neue Lockhierarchie. Erst Kernel-/Schedulingbelege und begrenzten Kandidaten mit Crash-/Cancelregression prüfen |

## Cancel, Resume, Recovery, Quarantäne und Ein-Job-Grenze

Job+Eventupdate, Cancel/Completion-Reread, Admission-Gates, Grantverbrauch,
Quarantäne, Recovery und Retrybudget bleiben unverändert. Dauerhafte
Lockkonflikte müssen weiterhin fehlschlagen; unbekannt abgeschlossene Transaktionen
werden nie erneut ausgeführt. Ein Storefehler allein erzeugt keinen erfundenen
Quarantänemarker; die bestehenden Guardian-/Executorfehlerpfade entscheiden wie
bisher bei unbestätigtem Cleanup. Bestehende Marker werden weder gelöscht noch adoptiert.

Der neue gesonderte Ein-Job-Test benutzt die echte Native-Freigabe und C16-
Prozesskette bei `max_parallel=max_queued=1`, einem synthetischen gebundenen
Materialworkflow, dem unveränderten 50-ms-Runloop und einem unabhängigen
reconnectenden Read-only-Statusclient bei 10 Hz. Ergebnis-/Hashprüfung, exakt ein
Job, Integrität und verweigerter zweiter Start sind gefordert. **Bestanden.**
Dies ist eine lokale realistisch begrenzte Konkurrenzprüfung, keine Hetzner-
Hardware-, Cgroup-, Powerloss-, Produktionsdaten- oder vollständige Kursabnahme.

Die Integritätsaussage gilt ausschließlich für die tatsächlich geprüften
synthetischen Zustände. Zusätzlich nennt die aktuelle
[SQLite-WAL-Dokumentation, Abschnitt 11](https://www.sqlite.org/wal.html)
einen seltenen WAL-Reset-Datenfehler bei konkurrierendem Write/Checkpoint und
Fixversionen 3.51.3 beziehungsweise Backport 3.50.7. Die Testlaufzeit meldet
3.50.4; ein entsprechender Backport ist hier nicht nachgewiesen. Das ist eine
separate offene Runtime-/Integritätsgrenze, **kein** belegter Auslöser des BUSY.
Keine Runtimeinstallation oder Abhängigkeitsänderung in diesem Auftrag; ein
grünes `integrity_check` ersetzt weder diesen Versionsnachweis noch Powerlosstests.

## Tatsächliche Validierung und offene Integration

Neue gezielte Tests: **5 passed / 12,91 s** (`targeted-final.log/.xml`): zwei echte
Dauerlock-/Crashvarianten, sichere Diagnosefelder, deaktivierte/defekte Diagnose
und unabhängiger Ein-Job-Statusclient.

| Neuer Lauf | Ergebnis / Sekunden | Bewertung |
| --- | --- | --- |
| Unveränderte Stresssuite, Diagnose standardmäßig aus | 4 passed / 2 failed; 36,59 s | 300 ohne Pause: Beginfehler Zyklus 169 nach 2,008836 s; 300 mit 10 ms: Zyklus 249 nach 2,009242 s |
| Trace, 3×300, Reinit alle 16, Leser gepinnt | 900/900; 10,060 s | Ein Pass; längste erfolgreiche Beginwartezeit 1.981,708 ms |
| Trace, 3×300, kein Reinit, Leser gepinnt | 737/900; 8,124 s | Rot, obige 208-Commit-Timeline |
| Einmalige geplante Wiederholung desselben Profils | 900/900; 9,291 s | Zeitabhängigkeit erhalten; keine behauptete Stabilisierung |
| Trace, 3×300, kein Reinit, kein gepinnter Leser | 661/900; 7,519 s | Zwei Beginfehler; Leserpinning nicht erforderlich |
| Trace, 1×300, kein Reinit, Leser gepinnt | 300/300; 2,737 s | Gesonderter Einzelwriterkontrolllauf; erfolgreiche Beginwartezeit maximal 0,896 ms |
| Trace, 3×300, kein Reinit, 10-ms-Pause | 900/900; 12,923 s | Pass; getrennt von rotem 10-ms-Stresstest ausweisen |
| Trace, 3×300, kein Reinit, 100-ms-Pause | 900/900; 39,866 s | Begrenzter Lastkontrolllauf; kein Produktparameter geändert |

Alle sieben Traceläufe prüfen bestätigte Writeanzahl gegen persistierten Zähler,
WAL, `integrity_check`, `foreign_key_check` und Quarantänemarker auch dann, wenn
ein Writer scheitert. Alle bestätigten Writes sind exakt bilanziert, alle sieben
Integritätsprüfungen bestehen. Die geforderte vollständige Writezahl wird in den
beiden roten Läufen weiterhin als Fehler gewertet. Volle Logs/JUnit/Timelines:
`artifacts/c26_cs50p_05/raw-evidence.tar.gz`; Mitglieder und SHA-256 in
`raw-evidence-manifest.json`; Laufzusammenfassung in `results.json` und
`trace-*-summary.json`. Messungen und Regression liefen nacheinander;
Host-/VM-weite Fremdlast ist nicht ausgeschlossen.

Breite Regression über C18-/Native-/MVP-/C16-/Operations-/Admission-Gatepfade:
**359 passed / 1 failed / 1 deselected**, 355,17 s; eine bestehende Fork-/Thread-
DeprecationWarning. Roter Node:
`test_cs50_workflows.py::test_stale_propagates_and_resume_preserves_existing_outputs[parser]`.
Gesicherte Guardianmeldung: Code 5, **setup**, Quarantäne aktiv. Nur lesend
geprüfte neue synthetische Fehler-DB: WAL, `integrity_check=ok`, leeres
`foreign_key_check`. Log/JUnit `regression-final.*`, sichere Forensik
`regression-forensics.json`. Das Ergebnis beweist keine vollständig grüne
Regression; die alte Setup-/Quarantäneklasse ist weiterhin offen.

Zwei erste Testentwicklungsversuche wurden abgebrochen: Der neue Test versuchte
nach SIGKILL eines auf einem multiprocessing.Event wartenden eigenen Kindes
dieses Event zu setzen. Faulthandler belegt einen Testharnessdeadlock in
`Event.set/notify_all`. Dieser unnötige Teardown wurde entfernt; keine Änderung
an Produktcleanup/-timeouts. Ein erster breiter Testaufruf benannte eine nicht
existierende Datei und sammelte null Tests; auch dieser Log bleibt erhalten.

Live-default lesend geprüft: **master**, SHA
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Der lokale master
`c1007efdbac3c1544020f328a3a1347e481797ba` ist veraltet. Die Änderungen dieses
Auftrags sind dort nicht integriert; kein PR ist für diesen Auftrag erstellt oder
gemergt. Die geteilten Gitmetadaten liegen außerhalb der beschreibbaren Wurzeln
und sind ausdrücklich read-only. Keine Umgehung, kein Commit/Branch-/Indexwrite.
Review-/Defaultbranchintegration bleibt **pending**, damit auch der vollständige
Lifecycleabschluss gemäß AGENTS.md. Die vorhandenen historischen C26-Dokumente
halten außerdem externe Deploymenttrigger für ungeklärt; keine Liveänderung wird
aus diesem Untersuchungsauftrag abgeleitet.

Der bereitgestellte Checkout ist vorbestehend und wird nicht entfernt. Es wurden
keine eigenen Gitbranches/-worktrees oder Remotebranches angelegt; entsprechend
keine solchen Artefakte entfernt. Quellen, Dokumentation, Rohbelege und prüfbare
Übergabe bleiben im Repositoryworkspace erhalten. Synthetische `/tmp`-Roots,
Testlogs und bestehende Venv bleiben bis Review erhalten. Keine Bereinigung
fremder/MAINT-inventarisierter Artefakte, Primärcheckouts, Stashes oder Daten.
