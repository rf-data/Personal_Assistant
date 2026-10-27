> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Verbleibende Gates und Betreiberentscheidungen

25.10.2026. **Produktion HOLD. Git-/Defaultbranchintegration ausstehend.**
Nachweise und genaue Fehler: [Validierung](c26h_validation.md).
Der [Stagingablauf](c26h_staging_runbook.md) ist Vorbereitung für einen späteren
separat genehmigten Versuch, keine hier erteilte Infrastrukturfreigabe.

## Technischer Abnahmestand

| Gegenstand | Stand | Noch erforderlich |
| --- | --- | --- |
| D/E/F-Quellen und zehn G-Dateien | Im H-Arbeitsbaum vorhanden, Hashprovenienz geprüft | Regulärer Review-/Commit-/PR-Weg; keine vorhandene H-Integrationscommitkette |
| Launcher-Content/Review/Search | Lokal implementiert und synthetisch geprüft | Exakte Runtimeimages/Lockinstallation, reale Dateirechte, Mounts und API-/Worker-/UI-Abnahme |
| Deaktivierte Stagingmodelle | Unitchecks und echte lokale Compose-config-Prüfung | Echte Coolifyprojektion/Netze/Roots/Ingress ohne fremde Writer oder Trigger |
| Collector/Coordinator/Gate | Gemeinsamer Offlinevertrag hält Livegrenze geschlossen | Produktiver Producer-/Build-/Operatortrust, externer CAS/Fencing-Witness und separat reviewter Livevertrag/Driver |
| Backup/Restore/Rollback | Synthetische Verbund-/Tamper-/Idempotenz- und inerte Rollbackproben | Produktiver Review-/Verbundadapter, Verschlüsselung/Offsite, Keyrecovery, RPO/RTO und alter Rückwärtsscope |
| C16-P1 | Bestehende Fixture-Race deterministisch bewiesen und korrigiert | Reale Container-/cgroup-/OOM-/Host-Cancellation separat abnehmen |
| C16-P2 | Isoliert auf Basis/H und in H-Gruppe bestanden; Ursache des historischen Fristüberschreiters offen | Phasenmessung mit erhaltenen Worker-/Guardian-/SQLiteereignissen, ohne Timeout- oder Quarantänelockerung |
| Monitoring | Statische/Git-bezogene Prüfung; Archiveffekt geklärt | Echter Alarmweg, Empfang, Bestätigung, Auflösung und Ausfallüberwachung |

## P1 – Behandelte Testursache, Sicherheitsvertrag unverändert

Exakte ID:
`tests/test_job_executor.py::test_real_nonzero_timeout_cancel_and_descendant_groups[cancel-cancelled]`.
Der historische Root-Exit -15 statt -9 allein beweist keine ausgebliebene
SIGKILL-Eskalation. Die deterministische Vorherprobe auf unveränderter Basis und
H zeigt TERM→KILL an dieselbe Gruppe, aber TERM vor Installation des Ignorehandlers.
Die interne Testprobe synchronisiert jetzt auf beide bereiten Prozesse und
publiziert die PIDliste vollständig. Der Guardian, seine Graceperiod von 0,4 s,
Gruppen-/Subreaper-/Parentdeathlogik, Cleanupbestätigung und strenge -9-Assertion
bleiben unverändert. Zwei neue Slow-start-Regressionen sichern Cancel und Timeout.
Das ist keine Abschwächung der produktiven Cancellationgarantie.

## P2 – Offene Verzögerungsursache

Exakte ID:
`tests/test_job_executor.py::test_real_background_worker_cli_and_api_lifecycle`.
Der historische Test erreichte nach Annahme keinen terminalen Zustand innerhalb
seiner unveränderten Achtsekundenfrist. Die gesicherte Datenbank enthält queued,
dispatching und offline_adapter; erst die Testbereinigung beendet den Supervisor
und persistiert interrupted. Sie enthält keinen nachgewiesenen SQLITE_BUSY-,
Deadlock- oder Quarantänefehler. Solche Ursachen sind damit weder bewiesen noch
vollständig ausgeschlossen. Auch natürliches späteres Completed ist unbekannt,
weil die Bereinigung den Worker beendet hat.

Isolierte und gruppierte Erfolge sind kein Ursachenfix. Kein Timeout wurde
erhöht, keine Assertion auf beliebige Terminalzustände gelockert und kein
SQL-Replay eingeführt. Weiteres Vorgehen: Originalfrist als Messgrenze erhalten,
Readiness/Queue/Claim/Adapter/Ergebniscommit getrennt zeitlich erfassen, zulässige
SQLitefehlercodes datensparsam sichern, einen möglichen verspäteten natürlichen
Abschluss nur in einer ausdrücklich getrennten Diagnose beobachten. Vorherige
Tests/Last/Plattformzustand sind Hypothesen; gemeinsame Testroots oder ein fremder
Writer sind nicht nachgewiesen. Bis dahin **nicht reproduzierbarer Prozessbefund
mit offener Ursache**, keine bestätigte H-Regression und keine Sicherheitsfreigabe.

## Weitere Bestandsrisiken

MAINT-03B/04B-Quarantäne-, SQLite-/Exit-3- und Hardlink-Crashbefunde bleiben erhalten.
Ein harter Publishabbruch kann zwei Links desselben Inodes hinterlassen; korrekte
Backupablehnung darf nicht als Fehler wegkonfiguriert werden. Keine Marker/Locks/
Links löschen oder adoptieren, keine automatischen Wiederholungen unbestätigter
Ausgänge. Die zusätzliche alte G-Exitcodeabweichung bei Quality Evaluation ist in
der Validierung getrennt von P1/P2 erfasst. Ein grüner begrenzter Lauf beseitigt
keinen dieser historischen roten Befunde.

## Vor einem isolierten Hetzner-Staging zu entscheiden

1. Benannter Betreiber, gesondertes Stagingmandat, Host/Architektur/Region/Budget,
   Rettungszugang, Rückweg und klare Trennung von Produktionsressourcen.
2. Exakte Backend-/Gateway-/UI-/Basisdigests, geprüfte Build-/Registrybelege,
   Lockinstallation und kompatible UI-Revision; hier kein Image gebaut oder geladen.
3. Neue eindeutig getrennte Runtime-/Content-/Review-/Index-/Log-/Cacheroots,
   bestätigte UID/GID, privater Konfigurations-/Cursor-Keybereich, Datenträgerbudget,
   Writer-/Triggerinventur und genau ein Executor. Keine Produktivbestände kopieren.
4. Domain/VPN/IPv4/IPv6/Private-API-TLS, exakte SAN-/CA-/Proxy-/Originbindung,
   OIDCissuer/Callback/Rollen/Scopes sowie externe Secret-/Tokenrotation und Widerruf.
5. Fachumfang zunächst ausschließlich synthetisch. Reale Kursdaten und Reviews
   benötigen eigene D06/D07-Rechte, Owner, Reviewer und Akzeptanzkriterien.
6. Konsistenter verschlüsselter Verbundbackup-/Restorevertrag einschließlich
   EvaluationStore, Keyrecovery, Retention/RPO/RTO und unabhängiger Kopie.
7. Alarmempfänger/Incident-/Rollbackowner, Zustelltest, aktueller freigegebener
   Rückwärtsscope; keine automatische Recovery nach Unknown-/Quarantänezustand.
8. Für jede spätere echte Mutation eigener geprüfter Livevertrag/Driver und
   produktive Trustkette. Synthetischer Witness, Collector-Capture, Healthstatus
   oder diese Dokumente können diese Betreiberentscheidung nicht ersetzen.

Kein Merge, Deployment, Serverzugriff oder Löschen ist Teil dieses Abschlusses.
Der aktuelle Branch/Worktree und alle fremden Artefakte bleiben erhalten. Wegen
schreibgeschützter Gitmetadaten und Mergeverbot fehlen Commit/PR und dauerhafte
Integration dieser Berichte in `master`. Der AGENTS.md-Lifecycle bleibt pending.
