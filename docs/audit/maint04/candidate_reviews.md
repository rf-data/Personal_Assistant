# MAINT-04 – Objektgebundene Reviews und getrennte Freigaben

Alle Aussagen beziehen sich auf den [geprüften Snapshot](README.md).
Empfehlung **Review**, effektiver Zustand **Keep_pending_individual_gate**.
Ein Betreiber muss jeden nachstehenden Antrag einzeln vervollständigen. Leere
Belegfelder sind fehlende Nachweise, keine stillschweigende Zustimmung.
Die [Sicherungsbedingungen](backup_restore_plan.md) gelten zusätzlich.

## BR001

Lokaler Upstreamname: `refs/remotes/origin/add_audio_transcript`.
Diese Branchkonfiguration ist zusätzliche Metadaten; ein Bundle rekonstruiert sie nicht.

Repository `rf-data/Personal_Assistant`, Typ **Branch**, Ref
`refs/heads/add_audio_transcript`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`b3b59b66942e4470475cc41657f4caf515338c67`; Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **171**.
Die vollständige erreichbare Historie umfasst **53 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: kein PR-Head oder -Base mit diesem Branchnamen. [Gemergter #4](https://github.com/rf-data/Personal_Assistant/pull/4) hatte denselben Head-SHA, aber Head `master` und Base `add_knowledge_db`; **nur Commitbezug**, keine Löschfreigabe oder aktive Kandidatenbindung.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0009 | `README.md` | Heutiger Pfad anders |
| D0049 | `docs/architecture.md` | Heutiger Pfad anders |
| D0279 | `docs/development.md` | Heutiger Pfad anders |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0401` → `monitoring/grafana/potential_metrics.md`, `D0403` → `docs/logger_notes.md`. Keine zweite Kopie erforderlich.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR001` und
`BR001.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR001: Antrag S – nur Sicherung und Restoretest

- Bindung: `Branch` `refs/heads/add_audio_transcript` bei `b3b59b66942e4470475cc41657f4caf515338c67`,
  Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR001: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR001**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR001**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.

## BR011

Lokaler Upstreamname: `refs/remotes/origin/master` (kein gleichnamiger Livebeleg).
Diese Branchkonfiguration ist zusätzliche Metadaten; ein Bundle rekonstruiert sie nicht.

Repository `rf-data/Personal_Assistant`, Typ **Branch**, Ref
`refs/heads/docs/cs50-archive`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`8ba519ed04c04c92573594ebe74b69a3c00aab1b`; Tree `02356af525ef9ff6a5dc3ebf99a1e062a363ea50`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **104**.
Die vollständige erreichbare Historie umfasst **120 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: keine namens-/Head-SHAgebundene PRzuordnung. [Gemergter #38](https://github.com/rf-data/Personal_Assistant/pull/38) benennt diesen SHA als damalige Masterbasis des CS50-Archivs. Der Kandidat endet beim Merge von #34; alte Test-/Integrationsberichte sind datierte Nachweise, keine heutige Abnahme.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0006 | `README.md` | Heutiger Pfad anders |
| D0031 | `docs/ROADMAP.md` | Heutiger Pfad anders |
| D0044 | `docs/architecture.md` | Heutiger Pfad anders |
| D0258 | `docs/cs50_knowledge_checkpoint.md` | Alter Pfad fehlt; Originalfassung nicht byteidentisch im Dokumentbestand |
| D0267 | `docs/cs50_pipeline_completion_report.md` | Alter Pfad fehlt; Originalfassung nicht byteidentisch im Dokumentbestand |
| D0281 | `docs/development.md` | Heutiger Pfad anders |
| D0288 | `docs/github_integration_status_2026-10-14.md` | Alter Pfad fehlt; Originalfassung nicht byteidentisch im Dokumentbestand |
| D0400 | `frontend/chat_app/README.md` | Heutiger Pfad anders |
| D0410 | `workers/cs50/README.md` | Heutiger Pfad anders |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0255` → `docs/cs50/operations/cs50_batch_execution.md`, `D0256` → `docs/cs50/contracts/cs50_budget_contract.md`, `D0257` → `docs/cs50/operations/cs50_course_scheduler.md`, `D0259` → `docs/cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md`, `D0260` → `docs/cs50/operations/cs50_lecture_completion.md`, `D0261` → `docs/cs50/operations/cs50_lecture_runner.md`, `D0262` → `docs/cs50/contracts/cs50_metadata_forwarding.md`, `D0268` → `docs/cs50/operations/cs50_pipeline_test_matrix.md`, `D0269` → `docs/cs50/contracts/cs50_portable_inputs.md`, `D0270` → `docs/cs50/evaluation/cs50_quality_evaluation.md`, `D0271` → `docs/cs50/operations/cs50_schedule_reporting.md`, `D0313` → `docs/logger_notes.md`, `D0401` → `monitoring/grafana/potential_metrics.md`. Keine zweite Kopie erforderlich.

Für D0258/D0267/D0288 existieren heutige Gegenstücke unter `docs/cs50/contracts/` bzw. `docs/cs50/archive/2026-10/`, aber mit anderen Bytes. Sie ersetzen nicht die exakten damaligen Fassungen. Checkpointvertrag, damaliger Pipelineabschluss und Integrations-/Teststatus verdienen einen bewussten historischen Erhaltungsentscheid.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR011` und
`BR011.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR011: Antrag S – nur Sicherung und Restoretest

- Bindung: `Branch` `refs/heads/docs/cs50-archive` bei `8ba519ed04c04c92573594ebe74b69a3c00aab1b`,
  Tree `02356af525ef9ff6a5dc3ebf99a1e062a363ea50`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR011: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR011**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR011**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.

## BR107

Repository `rf-data/Personal_Assistant`, Typ **Remote-Ref**, Ref
`refs/heads/add_audio_transcript`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`b3b59b66942e4470475cc41657f4caf515338c67`; Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **171**.
Die vollständige erreichbare Historie umfasst **53 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: kein PR-Head oder -Base mit diesem Branchnamen. [Gemergter #4](https://github.com/rf-data/Personal_Assistant/pull/4) hatte denselben Head-SHA, aber Head `master` und Base `add_knowledge_db`; **nur Commitbezug**, keine Löschfreigabe oder aktive Kandidatenbindung.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0009 | `README.md` | Heutiger Pfad anders |
| D0049 | `docs/architecture.md` | Heutiger Pfad anders |
| D0279 | `docs/development.md` | Heutiger Pfad anders |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0401` → `monitoring/grafana/potential_metrics.md`, `D0403` → `docs/logger_notes.md`. Keine zweite Kopie erforderlich.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR107` und
`BR107.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR107: Antrag S – nur Sicherung und Restoretest

- Bindung: `Remote-Ref` `refs/heads/add_audio_transcript` bei `b3b59b66942e4470475cc41657f4caf515338c67`,
  Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR107: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR107**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR107**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.

## BR109

Repository `rf-data/Personal_Assistant`, Typ **Remote-Ref**, Ref
`refs/heads/add_local_LLM`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`b3b59b66942e4470475cc41657f4caf515338c67`; Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **171**.
Die vollständige erreichbare Historie umfasst **53 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: kein PR-Head oder -Base mit diesem Branchnamen. [Gemergter #4](https://github.com/rf-data/Personal_Assistant/pull/4) hatte denselben Head-SHA, aber Head `master` und Base `add_knowledge_db`; **nur Commitbezug**, keine Löschfreigabe oder aktive Kandidatenbindung.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0009 | `README.md` | Heutiger Pfad anders |
| D0049 | `docs/architecture.md` | Heutiger Pfad anders |
| D0279 | `docs/development.md` | Heutiger Pfad anders |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0401` → `monitoring/grafana/potential_metrics.md`, `D0403` → `docs/logger_notes.md`. Keine zweite Kopie erforderlich.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR109` und
`BR109.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR109: Antrag S – nur Sicherung und Restoretest

- Bindung: `Remote-Ref` `refs/heads/add_local_LLM` bei `b3b59b66942e4470475cc41657f4caf515338c67`,
  Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR109: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR109**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR109**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.

## BR110

Repository `rf-data/Personal_Assistant`, Typ **Remote-Ref**, Ref
`refs/heads/add_organizer`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`b3b59b66942e4470475cc41657f4caf515338c67`; Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **171**.
Die vollständige erreichbare Historie umfasst **53 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: kein PR-Head oder -Base mit diesem Branchnamen. [Gemergter #4](https://github.com/rf-data/Personal_Assistant/pull/4) hatte denselben Head-SHA, aber Head `master` und Base `add_knowledge_db`; **nur Commitbezug**, keine Löschfreigabe oder aktive Kandidatenbindung.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0009 | `README.md` | Heutiger Pfad anders |
| D0049 | `docs/architecture.md` | Heutiger Pfad anders |
| D0279 | `docs/development.md` | Heutiger Pfad anders |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0401` → `monitoring/grafana/potential_metrics.md`, `D0403` → `docs/logger_notes.md`. Keine zweite Kopie erforderlich.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR110` und
`BR110.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR110: Antrag S – nur Sicherung und Restoretest

- Bindung: `Remote-Ref` `refs/heads/add_organizer` bei `b3b59b66942e4470475cc41657f4caf515338c67`,
  Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR110: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR110**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR110**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.

## BR111

Repository `rf-data/Personal_Assistant`, Typ **Remote-Ref**, Ref
`refs/heads/add_runpod`. Live/lokal vorhanden, erwarteter und beobachteter Commit
`d35c43fb698a5f015e56b067fa9f22ad8c459edf`; Tree `a26235de330eb2c07ca0b7b21fd83c98c92df235`.
Mergebase mit geprüftem master = dieser Commit; Ahead **0**, Behind **189**.
Die vollständige erreichbare Historie umfasst **35 Commits**.
Keine graph-eigenen Commits; historische Inhalte bleiben im Defaultgraphen
erreichbar. Das beweist weder gleiche heutige Dateibäume noch fachliche Obsoleszenz.
Ob die alte Commitidentität weiterhin über genau den Originalbranchnamen
adressierbar sein muss, bleibt eine offene Betreiberentscheidung.

PRbefund: keine direkte namens-/Head-SHAgebundene PRzuordnung. Der Commit ist der historische Merge von #2 (`offline_add`); dieser Herkunftsbezug macht `add_runpod` nicht zu einem aktuell benötigten oder entbehrlichen PRbranch.

Kein registrierter Worktree an diesem Ref, keine erkannte offene PRabhängigkeit. Aktive Nutzung durch Betreiber, externe Prozesse, fremde Klone oder Direktlinks **nicht bestätigt ausgeschlossen**. Originalref bis zur Entscheidung erhalten.

Historische Dokumentfassungen gegenüber dem heutigen Defaultbaum:

| MAINT-01-ID | Alter Pfad | Befund |
| --- | --- | --- |
| D0011 | `README.md` | Heutiger Pfad anders |
| D0404 | `src/core/logger_notes.md` | Alter Pfad fehlt; Originalfassung nicht byteidentisch im Dokumentbestand |

Zusätzlich byteidentisch nachgewiesene Dokumente: `D0401` → `monitoring/grafana/potential_metrics.md`. Keine zweite Kopie erforderlich.

D0011 ist ein tatsächlich leeres damaliges README. D0404 sind umfangreiche alte Logger-/Entwicklungsnotizen; heutige `docs/logger_notes.md` ist nicht byteidentisch. Keine ungeprüfte Übernahme alter Beispielinhalte.

Erhaltungsumfang: Originalcommit, Tree und gesamte erreichbare Historie unter einer
**eigenen** vorgeschlagenen Sicherungsref `refs/maint04-backup/BR111` und
`BR111.bundle`; Repository-/Scope-/Originalrefidentität im separaten Beleg.
Kein Kandidatenworktree wird gelöscht. Nichtversionierte/private Daten benötigen
bei festgestellter Betroffenheit eine getrennte ownergeführte Freigabe/Sicherung;
Bundle und sauberer Status ersetzen diese nicht.

### BR111: Antrag S – nur Sicherung und Restoretest

- Bindung: `Remote-Ref` `refs/heads/add_runpod` bei `d35c43fb698a5f015e56b067fa9f22ad8c459edf`,
  Tree `a26235de330eb2c07ca0b7b21fd83c98c92df235`. Nicht auf andere gleichzeigende Refs übertragbar.
- Betreiberentscheidung / Verantwortlicher / Zeitfenster / Beleg: **offen**.
- Explizite neue private Backup- und Recoveryroots, Zugriff, Scope und Retention:
  **nicht benannt**. Genehmigung muss Refanlage, Bundle und tatsächlichen
  Restoretest separat umfassen, niemals Remove.
- Dokumenterhalt und Daten-/Nichtnutzungsentscheidung: **offen**. SHA-/PR-/
  Worktreezustand unmittelbar vorher erneut prüfen; jede Änderung stoppt.
- Bundle-SHA256 / erfolgreicher Restorebeleg: **nicht vorhanden**; erst nach
  erlaubter tatsächlicher Ausführung ausfüllen. Antrag S ist nicht genehmigt.

### BR111: Antrag R – spätere separate Remove-Entscheidung

- Eigenständige Freigabe für exakt **BR111**, Repository/Typ/Ref/SHA wie oben;
  Betreibername, freigegebenes Fenster, verbindliche Nichtnutzung und
  Dokument-/Privatdatenentscheidung: **offen**.
- Vorher Antrag S tatsächlich ausführen und Commit/Tree/Historie, Bundle-SHA256,
  privaten Aufbewahrungsort und erfolgreichen Restore unabhängig nachweisen.
- Danach frischen vollständigen Phase-A-Abgleich und exakt erlaubten
  SHAgebundenen Einzelbefehl benennen (MAINT-02-Zeile **BR111**); keine automatische
  Übernahme aus TSV, kein Nachbarref und keine Registry-/Dateientfernung.
- Autorisierter / ausgeführter Befehl: **leer**. Ergebnis **not_executed**,
  `ready_for_removal=false`. Bis zur konkreten vollständigen Freigabe Keep.
