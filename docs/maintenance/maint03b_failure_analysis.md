# MAINT-03B – Fallanalyse und Ursachenbelege

25.10.2026. Entwicklungs-/QA-Auftrag; Produktionsstatus **HOLD**.
Basis: unveränderter MAINT-03-Commit `6b397eb4576bac93b318d0e1b8e954d16cb5e08e`.
Mastervergleich: dessen Parent `e68275205fefb7a5f6db42bc45060e505bfcefb5`,
nicht der veraltete lokale Branch `master` (`c1007ef`). Beide Quellsnapshots
enthalten ausschließlich versionierte Dateien; keine fremden Worktrees wurden
für Testläufe verwendet. Die historische [MAINT-03-Validierung](maint03_validation.md)
bleibt unverändert. Ausführung und Grenzen: [Validierung](maint03b_validation.md).

## Klassifikation

- **A:** Durch MAINT-03 kausal nachgewiesene Regression. **Kein bestätigter Fall.**
- **B:** Bereits auf der unveränderten Masterbasis vorhandener Fehler/Abbruchfall.
- **C:** Umgebung oder optionale Abhängigkeit.
- **D:** Testzustand, Isolation, Reihenfolge oder Zufallsidentität.
- **E:** Ursache noch ungeklärt. Keine der elf ursprünglichen Ursachen bleibt vollständig
  ungeklärt. Die zusätzlichen Prozessfälle N02, N03 und N04 werden weiter
  unten als E geführt. Vertrags-/Recoveryentscheidungen bleiben offen.

Mehrfachkennzeichnung trennt primäre Ursache und begünstigenden Testzustand.
Eine erfolgreiche Einzelwiederholung widerlegt keinen zustandsabhängigen Fehler;
eine Abweichung zwischen zwei Läufen ist noch kein Kausalitätsnachweis.

## Vollständige Matrix der elf ursprünglichen Fälle

`tests/` ist bei allen Test-IDs voranzustellen. „Master alt“ bezeichnet den
MAINT-03-Einzelvergleich; „Master neu“ den in MAINT-03B wiederholten Vergleich.
„M03“ bezeichnet zunächst den ursprünglichen breiten Auditlauf, zusätzlich ist
der erneute gemeinsame Lauf der elf Fälle vor Änderungen angegeben.

| Test-ID | Ursprünglicher Fehler | Unveränderter Master | MAINT-03 | Reproduzierbarkeit | Abhängigkeiten / Reihenfolge | Vermutete Ursache | Nachgewiesene Ursache / Klasse | Empfohlene Korrektur | Ergebnis MAINT-03B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `test_content_store_artifacts.py::test_private_explicit_root_and_limits` | Erwarteter `IntegrityError` fehlt | Alt und neu bestanden; unter 0077 fehlgeschlagen | Breiter Lauf fehlgeschlagen; neuer Elferlauf bestanden | Deterministisch mit umask 0077 | Vorherige globale umask-Änderung; `mkdir(mode=0755)` respektiert umask | Berechtigungsregression oder Fixture | Tatsächlicher Modus ist 0700; Store akzeptiert korrekt. **D** | Negativfixture explizit chmod 0755; Prozesszustand restaurieren | Bestanden; zusätzlich unter 0022 und 0077 bestanden; reale UID und Modus geprüft |
| `test_content_store_reimport.py::test_retry_is_recoverable_after_second_interruption[raw]` | `current.retry_of` ist `None` | Alt und neu bestanden | Breiter Lauf und neuer Elferlauf fehlgeschlagen | Zufällige Run-IDs entscheiden über Position 0 | Zwei Recoveryruns; SQL `ORDER BY id` | Fehlerhafte Retrytransaktion | Test wählt verlassenen Originalrun statt Retry. **D** | Nach `retry_of == original.run_id` auswählen; Eindeutigkeit und beide Listenrichtungen prüfen | Nachfolger `[raw-False]` bestanden; gesamte Reimportdatei inklusive beider Scopes/Richtungen bestanden |
| `test_cs50_batch_worker.py::test_managed_worker_cancel_restart_resume_and_stopped_backup[signal]` | Backup lehnt `.material-*` und Receipt mit nlink=2 ab | Alt und neu bestanden; deterministischer Crashprobe reproduziert Ablehnung auf Master | Breiter Lauf fehlgeschlagen; neuer Elferlauf bestanden | Zeitfenster beim harten Abbruch; Exit am Directorysync deterministisch | Publikationschild nach `os.link`, vor temporärem Unlink; Worker-/Cancelreihenfolge | Backupfehler oder unterbrochene Publikation | Crash hinterlässt zwei Namen desselben Inodes; Backup verweigert korrekt. **B**, zeitabhängiger Trigger **D** | Eigenen Recoveryvertrag für verifizierte Publikationsreste spezifizieren; Fail-closed bewahren | Signal-Einzelwiederholung bestanden; Abbruchfenster **nicht repariert**. Neuer deterministischer Negativtest bestätigt Ablehnung und Erhalt beider Namen |
| `test_cs50_index_end_to_end.py::test_full_offline_source_to_persisted_qdrant_and_resume[lecture-1]` | `ModuleNotFoundError: qdrant_client` | Alt und neu fehlgeschlagen | Breiter und neuer Elferlauf fehlgeschlagen | Ohne SDK deterministisch | Lokales Qdrant-SDK, synthetische Vektoren; keine Reihenfolge nötig | Fehlende optionale Installation | Top-Level-SDK fehlt. **C** | Kleines `test-qdrant`-Profil; explizite Sammlungsgrenze bei fehlendem SDK | Nicht ausgeführt: gemeinsamer Modulskip für die drei Parameter; keine behauptete Funktionsreparatur |
| `test_cs50_index_end_to_end.py::test_full_offline_source_to_persisted_qdrant_and_resume[python-10]` | `ModuleNotFoundError: qdrant_client` | Alt und neu fehlgeschlagen | Breiter und neuer Elferlauf fehlgeschlagen | Ohne SDK deterministisch | Wie oben, zehn synthetische Quellen | Fehlende optionale Installation | Top-Level-SDK fehlt. **C** | `test-qdrant`, dann expliziten lokalen External-SDK-Teilumfang ausführen | Nicht ausgeführt, derselbe Modulskip; keine neuen Qdrant-Erfolge gezählt |
| `test_cs50_index_end_to_end.py::test_full_offline_source_to_persisted_qdrant_and_resume[six-50]` | `ModuleNotFoundError: qdrant_client` | Alt und neu fehlgeschlagen | Breiter und neuer Elferlauf fehlgeschlagen | Ohne SDK deterministisch | Wie oben, 50 synthetische Quellen / sechs Kurse | Fehlende optionale Installation | Top-Level-SDK fehlt. **C** | `test-qdrant`, dann expliziten lokalen External-SDK-Teilumfang ausführen | Nicht ausgeführt, derselbe Modulskip; reale Dienste/Modelle nicht erforderlich und nicht gestartet |
| `test_cs50_llm_smoke.py::test_real_offline_worker_prepares_schema_before_initialization` | Report ohne `offline_contract_validated`; Vorbereitung bricht bei `tiktoken` ab | Alt und neu fehlgeschlagen | Breiter und neuer Elferlauf fehlgeschlagen | Ohne tiktoken deterministisch | Worker importiert globale AppSession vor reiner Vorbereitung | Fehlendes optionales SDK / unnötige Importkopplung | AppSession wird dort nur zum Setzen eines Loggers benötigt. **C/B** | AppSession erst im API-Pfad vor `configure_marvin` laden; reale Chunk-/Schemavorbereitung erhalten | Bestanden: Segment 17, Zeiten 2–12, validierter Contract, null APIrequests, danach gezielt provozierter Marvin-Initialisierungsfehler |
| `test_cs50_material_evaluation.py::test_srt_cue_text_and_known_locator` | Pydantic verwirft gleichnamiges `CS50CoursePlan` | Alt und neu einzeln bestanden | Breiter Lauf fehlgeschlagen; neuer Elferlauf bestanden | Auf Master nach Executor-Fixture deterministisch | Alter Adapter in Supportmodul, frisch importierte Builderklasse | MAINT-03-Modellregression oder Cacheidentität | Fixture entfernt nur Teile eines zusammenhängenden Modulgraphs. **D** | Vier globale Src-/Vertragspurges entfernen; Import-/Reihenfolgeprobes in frischen Prozessen | Bestanden; beide Producer-/Consumerreihenfolgen bestanden |
| `test_dev03_parsing.py::test_existing_evaluator_recipe_frozen_inputs_and_report_hashes` | Derselbe Pydantic-Klassenidentitätsfehler | Alt und neu einzeln bestanden | Breiter Lauf fehlgeschlagen; neuer Elferlauf bestanden | Derselbe Master-Reihenfolgeprobe scheitert | SRT-Support und vorheriger Fixture-Teardown | Wie voriger Fall | Dieselbe partielle Cacheentfernung. **D** | Gemeinsame Klassenidentität erhalten; keine Lockerung der Modellvalidierung | Bestanden; eingefrorene Inputs und Reporthash-Assertions erhalten |
| `test_transcript_unknown_time.py::test_unknown_locator_compatible_but_not_srt_binding` | Derselbe Pydantic-Klassenidentitätsfehler | Alt und neu einzeln bestanden | Breiter Lauf fehlgeschlagen; neuer Elferlauf bestanden | Derselbe Master-Reihenfolgeprobe scheitert | SRT-Support und vorheriger Fixture-Teardown | Wie voriger Fall | Dieselbe partielle Cacheentfernung. **D** | Cache nicht global purgen; unbekannte Zeiten weiterhin von SRT-Bindung trennen | Bestanden; beide Reihenfolgen bestanden |
| `test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models` | Versioniertes Schema ungleich aktuellem Modellschema | Alt und neu fehlgeschlagen | Breiter und neuer Elferlauf fehlgeschlagen | Auch in frischen Prozessen reproduzierbar | Gemeinsamer Kursalias, zwei Snapshotdateien; zwei Pydanticversionen geprüft | Veraltete Snapshots oder Generator-/Vertragsdrift | Vier Unterschiede: `Workflow.course_id.enum` enthält zusätzlich `loviscach_mathe_1`. **B**; gewünschte Vertragskorrektur offen | Workflowalias gegen dokumentierte CS50-Grenze entscheiden; erst danach Modell oder gezielt Snapshot ändern | Weiterhin fehlgeschlagen; keine Snapshotänderung, kein xfail/skip |

## Kontrollierte Reproduktionen

Der erneute Mastervergleich ergab **5 failed / 6 passed**, der MAINT-03-Stand
**6 failed / 5 passed**. Der zusätzliche Fehler ist die zufällige Retryauswahl,
nicht ein neuer Beweis gegen MAINT-03. Nach Korrektur: **7 passed / 1 failed /
1 Modulskip** im entsprechenden gezielten Lauf. Die drei Qdrantparameter wurden
über ihren Modulpfad ausgewählt, weil ohne SDK keine einzelnen Nodes gesammelt
werden; der Skip wird nicht als drei erfolgreiche Wiederholungen dargestellt.

Ein zweiter Masterprozess mit umask 0077 reproduzierte genau den Berechtigungsfehler.
Ein anderer Masterprozess führte zuerst
`test_cs50_executor.py::test_all_100_tasks` und dann die drei genannten
SRT-/Evaluatornodes aus: **1 passed / 3 failed**, jeweils Klassenidentität.
Die neuen Prozessprobes führen zusätzlich Adapter-, Knowledgeinput- und
Knowledgepilotfixtures vor den drei Consumern und in umgekehrter Reihenfolge aus.
Sie verändern den Modulcache des übergeordneten Testprozesses nicht.

Die private Umaskfixture registriert ihre Wiederherstellung unmittelbar nach `os.umask`.
Zusätzlich sichert eine autouse-Fixture die ursprüngliche Umask für jeden Test,
weil auch direkt aufgerufene CLI-Einstiege den Prozesszustand ändern. Das Auslesen
verwendet vorübergehend 0077, niemals die permissive Umask 0000.
Ein zusätzlicher Probe mit realem `scripts.deployment.main` und synthetisch
abgelehntem Preflight ergibt auf Master **1 passed / 1 failed** (Folgetest sieht
0077), auf MAINT-03B **2 passed**. Dabei wird kein echter Preflight ausgeführt.
Ein absichtlich bereits im Setup scheiternder abhängiger Test erzeugt im
verschachtelten Pytestlauf genau einen Setupfehler; der danach ausgeführte
Kontrolltest sieht wieder 0022. Ein zweiter Negativfall prüft denselben Restore
nach CLI-artiger Mutation und Fehler im Testkörper. Dieser absichtliche Fehler ist innerhalb eines
bestandenen Negativtests eingeschlossen, kein verschwiegenes Suiteproblem.

Ein separater Ownershipprobe akzeptierte den realen eigenen 0700-Root und
verweigerte denselben Root bei synthetisch abweichender erwarteter UID. Kein chown,
keine fremden Dateien. Im Crashregressionstest werden echte UID, Modus 0600,
Inodegleichheit, nlink=2 und erhaltene Bytes beider Namen geprüft.

## Hardlinks: Sicherheitsentscheidung bleibt offen

Master und MAINT-03B wurden mit einem eigenen synthetischen Publikationschild am
Directorysync hart beendet (Exit 73). Beide erzeugen denselben Zustand. Der neue
Test verlangt anschließend den realen Fehler von `job_control.operations.inventory`
und überprüft, dass beide Dateien erhalten bleiben. Ein weiterer Test trennt den
normalen Python-Exceptionpfad ab: `finally` entfernt dort den temporären Alias,
das bereits publizierte Ziel bleibt unverändert, ein zweiter Publish ersetzt es
nicht. Eine Exception und ein harter Prozessabbruch sind unterschiedliche Verträge.

Der zeitabhängige Worker-/Backuptest wird nicht durch ein bedingtes „entweder
Erfolg oder Fehler ist okay“ abgeschwächt. Er kann bis zur expliziten Recoverylösung
weiterhin einen relevanten Fehlschlag liefern. Unbekannte Hardlinks dürfen weder
adoptiert noch automatisch gelöscht werden. Siehe [Restrisiken](maint03b_remaining_risks.md).

## Fachliche Einordnung der Schemaabweichung

Frische Vergleiche unter **Pydantic 2.13.4** (Repository-Lock) und **2.14.1**
(MAINT-03-Auditinterpreter) liefern identisch genau vier Abweichungen:

| Snapshot | Modell | JSON-Pfad | Unterschied |
| --- | --- | --- | --- |
| `docs/job_control/contract.v1.json` | WorkflowInspection | `/$defs/Workflow/properties/course_id/enum` | zusätzlicher Kurswert |
| `docs/job_control/contract.v1.json` | WorkflowRunReport | gleicher Pfad | zusätzlicher Kurswert |
| `docs/workflows/contract.v1.json` | WorkflowInspection | gleicher Pfad | zusätzlicher Kurswert |
| `docs/workflows/contract.v1.json` | WorkflowRunReport | gleicher Pfad | zusätzlicher Kurswert |

Die im ursprünglichen verkürzten Pytest-Dictdiff sichtbaren Artifact-/schema_version-
Ausschnitte sind **kein Beleg** für eine entsprechende Feldänderung. Der vollständige
rekursive Vergleich weist hier ausschließlich den Kursenum nach.

Commit `d6f16d0` stellt den öffentlichen C16-Alias `Course` auf `ContentCourseId`
um; `WorkflowParams` erhält ausdrücklich `DiscoveryCourse`. `workflows.models`
importiert jedoch weiterhin `Course`, wodurch auch `Definition`/`Workflow` breiter
werden. Die [damalige Architekturentscheidung](../architecture/content_course_scope.md)
sagt ausdrücklich, dass CS50-Workflowparameter beim ursprünglichen Discoverykurs
bleiben. Die verschachtelte Report-/Definitionsgrenze und der gemeinsame Alias
wurden damit nicht vollständig charakterisiert. Eine rein additive Aktualisierung
der Snapshots würde diese Mehrdeutigkeit festschreiben.

Empfehlung für einen separaten Vertragsreview: zuerst festlegen, ob nur ACL/Katalog
oder auch gespeicherte Workflowreports den zusätzlichen Kurs führen sollen. Dann
alte CS50-JSONroundtrips, neue/unbekannte Kurse, Definition, Jobparameter, Reports
und beide versionierten Schemas gemeinsam prüfen. Bis dahin bleiben der konkrete
Fehler und alle Assertions sichtbar; öffentliche Akzeptanzbereiche werden hier
nicht stillschweigend geändert.


## Zusätzliche Befunde des vollständigen MAINT-03B-Laufs

Der erste vollständige Lauf nach Umaskrestauration ergab **2.373 passed /
47 failed / 25 skipped / 87 deselected**, 2 Warnungen, 2.560,59 s. Dies ist
ein tatsächlicher roter Lauf und wird nicht nachträglich als Erfolg umgedeutet.
Die anfänglichen Fortschrittsmeldungen hatten nur den letzten Logblock betrachtet
und dadurch ältere Fehlerzeichen übersehen; die abschließende Bewertung verwendet
den vollständigen JUnitreport, beziehungsweise bei unterbrochenen Läufen
die vollständig gesicherten Fortschrittszeichen mit abgeglichener Nodeliste.

### N01 – Native HTTPS-Preflighttests falsch dem Offlineprofil zugeordnet

45 Fehler stammen aus `tests/test_https_preflight.py`. Dessen `render` ruft
tatsächlich `docker compose ... config --format json` auf; auch die mutierten
Negativfälle erzeugen zuerst diese echte native Ausgabe. Der neue Offlineguard
wirft **vor Popen-Ausführung** `Offline profile forbids infrastructure commands`.
Keine Dockeraktion wurde dafür ausgeführt. Die ursprüngliche MAINT-03-Suite hatte
solche nativen CLIprüfungen noch zugelassen; dieser Auftrag verbietet sie.

Die fehlerhafte Zuordnung in MAINT-03B ist korrigiert: die vollständige Datei
gehört zu External Integration. Ihre Assertions bleiben unverändert; keine
Simulation von Composeausgaben und kein bedingter Erfolg. Diese 45 Guardfehler
sind keine nachgewiesenen Routing-/Produktfehler und keine MAINT-03-Regression.
Sie bleiben als historisches Resultat erhalten. Die Korrektur wird durch einen
fortgesetzte Ausführung aller ausgewählten Fälle des richtig abgegrenzten
Profils validiert; Prozessunterbrechungen sind in der Validierung offengelegt.

Zusätzlich sind alle acht SDKgebundenen Qdrantdateien ausdrücklich External: auch
ein zufällig bereits installiertes SDK aktiviert sie nicht ohne `--run-external`.
Ein Negativtest stellt einen SDK-Dateinamen mit einer verbotenen Setupfixture
bereit und prüft, dass diese ohne Opt-in nicht läuft. Der bestehende Negativtest
für ein kaputtes installiertes SDK bleibt erhalten.

### N02 – Workflow-Resume trifft Sicherheitsquarantäne (E)

Node: `tests/test_workflow_http.py::test_stale_resume_runs_only_required_stages_and_preserves_old_bytes[normalized]`.
Im vollständigen Lauf wirft `Executor.step` **Unavailable: Unconfirmed cleanup;
dispatch quarantined**, statt dass der erwartete synthetische Resume abschließt.
Der tatsächliche Quarantänemarker ist im Fehlerpfad nachgewiesen. Die tieferliegende
Guardian-Ausnahme beziehungsweise ein etwaiger Verlust der Prozessendbestätigung
ist durch den JUnitstack allein nicht erklärt. Die temporäre ursprüngliche
Testwurzel stand bei der anschließenden Detaildiagnose nicht mehr zur Verfügung;
die Standard-Pytest-Tempretention ist deshalb keine geeignete Forensiksicherung.

Einzelwiederholung auf MAINT-03B: **1 passed**, 14,57 s. Die unveränderte
Masterwiederholung bestand ebenfalls: **1 passed**, 12,48 s. Die fortgesetzte breite
Ausführung wird in der Validierung separat ausgewiesen. Ein Einzelpass widerlegt den breiten Fehlschlag nicht.
Guardian-/Executorcode blieb unverändert. Kein Nachweis einer kausalen Regression
durch MAINT-03 oder einer reparierten Cleanupursache. **Klassifikation E**, mögliche
Prozess-/Timing-/Isolationsabhängigkeit noch offen.

Die Sicherheitsquarantäne wird nicht gelöscht oder ignoriert; kein Retry,
Timeoutbudget oder Cleanupbestätigungsgate wird gelockert. Die abschließenden Ausführungssegmente
verwenden jeweils eine eigens angelegte, explizite `--basetemp`-Wurzel, damit
Marker, Events und Jobdaten nach dem Lauf lesbar bleiben. Eine dauerhafte Änderung
am Guardian benötigt zuerst eine phasenbezogene synthetische Reproduktion.


### N03 – Cancel-/Resume-Job mit OperationalError unterbrochen (E)

Node: `tests/test_cs50_workflows.py::test_cancel_during_real_execution_and_resume`.
Der korrigiert abgegrenzte Extended-Lauf enthält für diesen Node ein `F`.
Wegen der späteren Laufunterbrechung liegt aus diesem Segment kein abschließender
Pytest-Traceback/JUnitreport vor. Die Fehlerzuordnung ist aus der unveränderten
sequentiellen Sammlung und den vollständigen Fortschrittszeichen rekonstruierbar.

Die erhaltene synthetische Testwurzel
`/tmp/maint03b-final-profile-data-0xn86wha/test_cancel_during_real_execut0/private`
erlaubt zusätzliche Belege. Eine Kopie von SQLite-, WAL-/SHM-Dateien und Marker
unter `/tmp/maint03b-cancel-forensics-zmt7_14s` wurde ausschließlich lesend
abgefragt; der Originalzustand blieb erhalten. Der erste Job endet bestätigt mit
`cancelled`, Exit -15 und 1,315 s Laufzeit. Der anschließende Resumejob
`job_167e219bf1634ebfa6911a0002281535` endet dagegen am 25.10.2026 um
14:06:42,609 UTC mit `interrupted` und
`Execution interrupted (OperationalError); no automatic retry`.
Exitcode und Laufzeit fehlen; der Quarantänemarker verweist genau auf diesen Job.

Nachgewiesen ist damit eine im Guardian registrierte OperationalError-Ausnahme
und die anschließende fail-closed Quarantäne. Der konkrete SQLitefehlercode,
Ausnahmetext und die auslösende Operation wurden dort nicht persistiert.
Lock-/Busy-Konkurrenz ist eine Hypothese, kein Ursachenbeweis. Insbesondere
rechtfertigt sie weder Transaktionsreplays noch größere Timeouts oder gelöschte
Quarantäne. `Store.connection` besitzt bereits eine begrenzte Wiederholung vor
Transaktionsbeginn für bestimmte SQLITE_BUSY-Fälle; das erklärt diesen Vorfall
nicht abschließend. Guardian, Executor und Store bleiben unverändert. Die frischen Einzelgegenproben
bestehen auf MAINT-03B (7,99 s) und Master (8,79 s); keine Ursachenreparatur.

**Klassifikation E**; keine bestätigte MAINT-03-Regression. N02 und N03 werden
nicht ohne Nachweis zu derselben Ursache zusammengefasst. Ein Folgeschritt muss
zuerst Phasen und SQLitefehler synthetisch reproduzieren und sichere,
datensparsame Diagnostik reviewen. Die vorhandenen Sicherheitsgates bleiben
verbindlich. Einzelgegenproben und das unverrechnete breite Fehlerresultat sind
in der Validierung getrennt ausgewiesen.


### N04 – PDF-Probe erreicht den geplanten Fehlerpunkt nicht (E)

Node: `tests/test_pdf_job_control.py::test_real_pdf_worker_cancel_timeouts_parent_death_and_restart[adapter-exit]`.
Die letzte Fortsetzung scheitert bei `wait_for(marker.exists)` nach den bestehenden
12 Sekunden: `Bounded PDF lifecycle condition not reached`. Der Adapter-SIGKILL
wurde also noch nicht ausgelöst; kein Beweis eines fehlerhaften Cleanupresultats.

Die synthetische Testwurzel unter
`/tmp/maint03b-final-rest-yfd0crl4/test_real_pdf_worker_cancel_ti4` enthält keinen
PDFmarker, jedoch einen Guardianmarker. Eine nur lesend untersuchte SQLitekopie
unter `/tmp/maint03b-pdf-adapter-forensics-53vqofoc` zeigt bereits nach 2,689 s
einen fehlgeschlagenen Job, Exit 3, `error_class=internal`,
`Offline adapter returned non-zero or missing output`. Ein Quarantänemarker fehlt.
Der konkrete Adapterfehler wurde nicht behalten; weder Timeoutverlängerung noch
N03s OperationalError sind dadurch gerechtfertigt. Eigene Einzelprozesse bestehen
auf beiden Ständen; **Klassifikation E**, keine bestätigte MAINT-03-Regression.
Einzeln: MAINT-03B 1 passed in 3,10 s, Master 1 passed in 4,98 s. Auch die
abschließende betroffene Testdatei besteht; die tiefere Fehlerursache ist dadurch
nicht behoben. Die bestehende 12-Sekunden-Grenze und alle Prozess-/Bytesprüfungen
bleiben erhalten.

### N05 – Nicht atomare PID-Markerfixture (B/D, korrigiert)

Node: `tests/test_pdf_workflows.py::test_pdf_workflow_interrupted_stage_is_not_skipped_and_explicit_resume_succeeds[cancel]`.
`wait_for(marker.exists)` kehrt zurück, aber direkt danach liefert
`json.loads(marker.read_text())` einen JSONDecodeError auf dem **leeren** String.
Der vorhandene Testprobe verwendet `Path.write_text`: Öffnen mit `w` erzeugt den
sichtbaren finalen Pfad vor dem eigentlichen JSONwrite. Ein erfolgreicher späterer
Lesezugriff oder Einzelpass schließt diese Lücke nicht.

Die neue isolierte Negativprobe hält die echte Dateioperation genau nach dem
Öffnen zum Schreiben an und verlangt, dass der finale PIDmarker noch unsichtbar
ist. Diese Assertion scheitert identisch auf dem unveränderten Master und dem
unveränderten MAINT-03B-Testhelper. Damit ist eine bereits bestehende
Fixture-Publikationsrace **B/D** nachgewiesen, keine MAINT-03-Regression.

`tests/helpers/pdf_lifecycle_probe.py` schreibt jetzt zuerst eine temporäre Datei
im selben synthetischen Verzeichnis und veröffentlicht sie nach Schließen per
Rename. Dies gilt für PDF- und Guardianmarker. Der neue Negativtest prüft das
unsichtbare Zwischenstadium, vollständiges JSON, richtige PID-/Gruppenwerte und
den fehlenden temporären Rest nach Erfolg. Kein Produktwriter, Parservertrag,
Timeout, Signaltest oder Cleanupgate wurde geändert. Die Auswirkungen der letzten
Fixtureänderung sind durch die gezielte abschließende Prüfung in der Validierung
ausgewiesen; historische Fehlschläge bleiben unverrechnet erhalten.


Abschließender Nachlauf nach der Markerfixturekorrektur: neue Markerregression
und sämtliche Fälle aus den drei betroffenen PDF-/Workflowdateien ergeben
**62 passed / 1 failed**, keine Skips oder Sammlungsausfälle. Nur der alte
Schemasnapshot scheitert. Das grenzt N05s Testkorrektur ab und ersetzt weder den
breiten roten Befund noch die offene N03-/N04-Diagnose.
