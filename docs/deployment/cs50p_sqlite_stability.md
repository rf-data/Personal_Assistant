# C26-CS50P-03: SQLite-Stabilitätsbefund

27.10.2026. **HOLD; Fehlermodus reproduziert, Restursache nicht abschließend
geklärt, kein Produktivfix behauptet.** Keine bestehenden Datenbanken benutzt.
Nur neue synthetische pytest-Wurzeln unter /tmp, gesicherte Logs/JUnitdateien
unter `artifacts/c26_cs50p_03/`. Produktdateien in src/ und scripts/ unverändert.

## Ausgangsstand und Zusammenhang mit C26-INT-02

HEAD und live Featurebranch: `2f2b410f41cd4db4e26075b891a03c6cb1ff0cd6`.
Native Admission ist committed und auf GitHub gesichert; der frühere Hinweis
auf einen ausschließlich uncommitteten Nativepatch ist historisch. Lokale
README-Erweiterung bestand vorher und wurde weder verändert noch in Taskpatches
aufgenommen. Sie wird separat als Beleg erhalten. Gitindex liegt außerhalb der
beschreibbaren Wurzeln: keine Commit-/Branch-/Worktreemutation.

[C26-INT-02](c26_int_02_validation.md) erweiterte das Wiederöffnen bis vor
erfolgreiches `BEGIN IMMEDIATE`. Diese Behandlung ist bereits im geprüften HEAD.
Sie deckt vorübergehendes BUSY während Setup/Begin ab, garantiert jedoch keine
Writerfairness oder erfolgreiche Aufnahme innerhalb des vorhandenen 2-s-Budgets.
Der neue Befund darf nicht als Fehlen des alten Begin-Fixes beschrieben werden.

## Connection- und Transaktionsaudit

| Aspekt | Tatsächlicher Vertrag / verbleibende Grenze |
| --- | --- |
| Lifecycle | Jeder Storekontext öffnet eigene Connection, schließt in finally; keine geteilte Connection zwischen Prozessen. Bootstrapflock serialisiert Storeinitialisierungen, nicht alle Transaktionen. |
| Writer | BEGIN IMMEDIATE vor Körper; Executorheartbeat, Guardianstatus, Cancel und Storeinitialisierung können trotz max_parallel=1 konkurrieren. Initialisierung nimmt auch bei bestehendem Schema eine Schreibtransaktion. |
| WAL | Nach Identitäts-/Schemaprüfung aktiviert; Leser können alten Snapshot behalten, während Writer committen. WAL entfernt nicht die Einzelwritergrenze. |
| Busy | connect timeout aus verbleibendem 2-s-Setupbudget; erneutes Öffnen nur BUSY vor Beginn und ohne in_transaction. Kein pauschaler Timeoutanstieg, keine neuen Retries. |
| Körper/Commit | Kein Replay, Rollback und Propagation. Unklarer Commit wird nicht erneut ausgeführt. Bestehende Regression prüft deferred-FK-Commitfehler. |
| Cancel/Resume | Zustandsprüfung und Eventupdate innerhalb derselben Writertransaktion; deterministische Cancel/Completion-Reihenfolgen getestet. Resume benötigt neue Identität/Freigabe; kein automatischer Jobneustart. |
| Crash | Eigener Prozess wird mit offener synthetischer Transaktion getötet; ungecommittete Änderung muss beim Wiederöffnen fehlen. Kein produktiver Crash/Restoretest. |
| Quarantäne | Guardian-/Cleanupunsicherheit blockiert weitere Ausführung und Resultatabruf. Kein Entfernen oder automatisches Recover von Quarantäne. |

Native Status/Result verwenden SQL mode=ro ohne Storeinitialisierung. Das beseitigt
nicht die Writerkonkurrenz innerhalb des Workers. SQLite kann bei Lesern WAL/SHM-
Metadaten anlegen. Keine SQL-, Rohdaten- oder Secretinhalte in Fehlerbelegen.

## Reproduktionsbedingungen und erhaltene rote Belege

Python 3.12.12, SQLite 3.50.4, Linux auf lokalem /dev/vdc; vorhandene Testvenv
nur lesend verwendet. Keine Paketinstallation. Ziel-Ubuntu/SQLite ist damit
nicht nachgewiesen. Host-/cgroupweite Fremdlast und Schedulerpausen sind nicht
vollständig beobachtbar; die erste neue Stresssuite überlappte mit dem Baseline-
Gruppenlauf, der zweite Diagnoselauf wurde anschließend einzeln ausgeführt.

| Lauf | Ergebnis | Beobachtung |
| --- | --- | --- |
| baseline | 81 passed, 1 failed / 82; 86,49 s | Native CLI-Worker wird durch Quarantäne blockiert. Gesicherter Guardianbeleg: SQLitecode 5, Phase setup. Nicht als begin ausgeben. |
| sqlite-process | 2 passed, 2 failed / 4; 27,91 s | Beide Stressfälle (64/300 Zyklen) liefern BUSY 5 bei begin. Crashrollback und dauerhafter Writer-Fail-closed bestehen. |
| sqlite-diagnostic | 3 passed, 1 failed / 4; 18,74 s | 64-Zyklenfall besteht; 300-Zyklenfall: increment, Index 12, 2,070246 s, BUSY 5, begin. |
| sqlite-final | 5 passed, 1 failed / 6; 39,72 s | Ohne Pause: 300 Zyklen scheitern bei increment 184 nach 2,093511 s / BUSY 5 / begin; 64 Zyklen bestehen. Beide Fälle mit 10-ms-Testpause, Crashrollback und Dauerlockablehnung bestehen. |

Logs und XML haben jeweils denselben Dateistamm. Der erste Stressquellstand
liegt separat in sqlite-red-source.py. Die finale Testfassung ergänzt
Operationsindex/-dauer und kontrollierte 10-ms-Writerpausen als **Testvariable**;
dies ist keine produktive Heartbeat-/Timeoutänderung. Finale Läufe und
Wiederholungsraten stehen in [Release Readiness](cs50p_mvp_release_readiness.md).
Überlappende Läufe nicht addieren.

Stressaufbau: drei unabhängige spawn-Prozesse, jeweils eigener Store, synchroner
Start; jeder führt 64 bzw. 300 atomare Inkremente aus und initialisiert alle
16 Zyklen neu. Ein weiterer Connectionkontext hält bewusst einen WAL-Lesesnapshot.
Assertions verlangen alle Inkremente genau einmal, Snapshotstabilität, WAL,
integrity_check=ok und keine Quarantäne. Keine verlorenen Writes werden toleriert.

Das belegt reale Konkurrenz mit erschöpftem Begin-Budget. Es unterscheidet noch
nicht eindeutig lang gehaltene Writertransaktionen, Scheduler-/I/O-Pausen und
Writerstarvation. Der historische Nativebericht nannte begin; der neue Native-
Fehler nennt setup. Gleicher SQLitecode allein beweist keine gemeinsame Ursache.
Eine willkürliche zusätzliche Mutex-/Backoff-/Timeoutschicht wäre daher derzeit
kein nachgewiesener minimaler Ursachenfix. Die roten Stresstests bleiben sichtbar.

## Weitere Eingrenzung vor Hostfreigabe

Erforderlich ist ein kontrollierter Nachlauf mit transaktionsgenauen Haltezeiten
und Prozess-/Scheduler-/fsync-Korrelation auf isolierter CPU/I/O, getrennt nach
Heartbeat, Bootstrap und Guardian. Diagnose nur mit festen Phasen und Zeitwerten,
keine SQL-/Eingabebytes. Danach erst entscheiden, ob vermeidbare Writeraufnahme
oder Scheduling behandelt werden muss. Einen länger als das bestehende Budget
gehaltenen Writer weiterhin fail-closed ablehnen; Körper/Commit nie wiederholen.
Keine früheren Quarantänen als Testdaten übernehmen oder „reparieren“.

READ-ONLY, Produktquellen prüfen:

```sh
git show 2f2b410:src/job_control/store.py
git diff -- src/job_control scripts
```

CHANGE, ausschließlich lokale synthetische Testdaten/Reports; Voraussetzung:
passende Testumgebung und neue Testwurzeln, keine Produktionspfade. Effekt:
Testprozesse, neue temporäre DBs und JUnitdatei; Rückweg: Prozesse beendet lassen,
Belege bis Review erhalten. PYTHON durch eigenen passenden Interpreter ersetzen:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHON -m pytest -q -o addopts= -p no:cacheprovider -p tests.offline_guard tests/test_cs50p_sqlite_stability.py tests/test_job_store_contention.py tests/test_c26_int_02_sqlite.py --junitxml=NEW_SQLITE_RESULT.xml
```

Das Auftreten erwarteter Lockablehnung im expliziten Dauerlocktest ist ein
erfolgreicher Sicherheitsnachweis. BUSY im Test, der vollständige Fortschritte
konkurrierender Writer verlangt, bleibt ein **fehlgeschlagener** Stresstest;
keine Umdeklaration oder Aufweichung der Assertion.
