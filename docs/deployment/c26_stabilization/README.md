# C26 Stabilization & Release Unblocking — 23.10.2026

**GO: Code- und Dokumentationsreview sowie lesende Betreiberinventur.
NO-GO: Merge, Deployment und produktiver Week-0-Batch.** Coolifys tatsächliche
Triggerwirkung ist weiterhin unbekannt. Auch dieser Korrektur-PR benötigt vor
einem Merge einen belegten, kontrollierten Deploymentpfad. Kein Auto-Merge.

## Geprüfte Basis und Änderungen

Backend-Master: `e502aa915ad0e928dbe7e92eacd44fff0152912b` mit integriertem #155.
UI-Main: `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`.
Die Primärcheckouts wurden nicht umgeschaltet. Die lokale Worktreeinventur,
GitHub-Abfrage, Testläufe und Quellhashes sind in `validation.v1.json` zusammengefasst.
Historische Berichte unter `../c26_final/` bleiben unverändert erhalten.

### A: Drei optionale Tokenizerimporte

Die drei Setupfehler betreffen `tests/test_cs50_batch.py`: sechs Kurse mit
Fake-HTTP, explizite Kurs-/CLI-Sperre und isoliertes synthetisches CLI-Resume.
`tiktoken>=0.12.0` ist in `pyproject.toml` ausschließlich im Extra
`lecture-worker` deklariert und im Lockfile enthalten. Die vorhandene kleine
Python-3.12.12-Testumgebung enthält dieses Extra nicht; das ist für diese
Offlinefälle angemessen. Die Tests benötigen weder Tokenisierung noch Marvin.

Ursache: `bind_cs50_transcript → find_knowledge → memory → tiktoken` sowie
gleichartige indirekte Imports über Retry-, Pfad- und allgemeine Helfer. Nach
Entfernung dieser Kante wurde ein zweiter zu früher optionaler Import sichtbar:
`general_helper → config → pydantic_settings`.

Sitzungs- und Konfigurationsimporte erfolgen jetzt erst in den Funktionen, die
sie nutzen. Reine Chunk-/Provenienz-/Hashfunktionen bleiben ohne diese Extras
importierbar. Keine Dependency-, Lockfile-, Runtimeprofil- oder Umgebungsänderung.
Der bestehende frische `python -I`-Importtest verbietet zusätzlich jeden Import
von `tiktoken` und `pydantic_settings` und prüft, dass die globale Sitzung und
globale Ordnerkonfiguration nicht geladen wurden. Echte LLM-/Parserfunktionen
benötigen weiterhin ihre vorhandenen optionalen Profile.

### B: SQLite und Quarantäne

Die alte Config-Resume-Datenbank wurde ausschließlich mit `mode=ro` gelesen:
WAL-Modus, `quick_check=ok`, erster Job abgeschlossen, Folgejob unterbrochen mit
`OperationalError`. Dieser historische Datensatz enthält keinen SQLitecode.

Auf dem neuen Master trat derselbe Fehlerpfad erneut auf, diesmal bei
`test_partial_failure_and_independent_branch_strategy[False]`:
**SQLITE_BUSY (5) an `Store.connection`, `PRAGMA synchronous=FULL`**, aus
`guardian.should_stop → Store.get`. Vollständiger Vorlauf: 23 bestanden,
1 Quarantänefehler. Die temporäre Diagnose erfasste Fehlercode und Stackframes;
sie änderte weder SQLiteparameter noch die Quarantäneregeln.

Ein neuer deterministischer Test hält eine echte exklusive SQLiteverbindung,
beobachtet den Fehler genau an diesem PRAGMA und gibt den Lock erst beim
Schließen der fehlgeschlagenen Verbindung frei. Beide Varianten (Leser/Writer)
schlagen vor der Korrektur fehl. Danach wird nur das Verbindungssetup vor jeder
Transaktion mit einer frischen Verbindung innerhalb des bisherigen Zwei-Sekunden-
Budgets wiederholt. `synchronous=FULL`, Foreign Keys, Transaktionsgrenzen und
Quarantäne bleiben erhalten. Kein Wiederholen von Transaktion, Commit oder Job.
Tests decken außerdem dauerhaften Lock, anderen Setupfehler und Body-Rollback ab.

Bewertung: **reproduzierbarer unzureichend behandelter SQLite-Setup-Lockkonflikt**,
keine nachgewiesene Datenkorruption oder Löschung durch Fixtures. WAL-Abschluss-
und Recovery-Locks sind eine plausible Erklärung, ausdrücklich keine bewiesene
Identität des ursprünglichen Lockhalters. SQLite dokumentiert kurze exklusive
Locks auch bei WAL-Lesern und dass der Busy-Handler nicht immer aufgerufen wird.
Siehe [WAL, Abschnitt 9](https://www.sqlite.org/wal.html#sometimes_queries_return_sqlite_busy_in_wal_mode)
und [Busy-Handler](https://www.sqlite.org/c3ref/busy_handler.html).

Die Korrektur behandelt den belegten Setupfehler; sie ist keine pauschale
Entwarnung für alle historischen Guardianverluste. Anhaltendes Locking,
I/O-/Kapazitätsfehler oder unbestätigtes Cleanup bleiben blockierend. Der konkrete
ursprüngliche Config-Resume-Auslöser und die Eigenschaften des Produktionsmounts
sind weiterhin nicht vollständig erklärt. Produktionsfreigabe verlangt einen
separat genehmigten begrenzten Lauf auf dem belegten lokalen Linux-/WAL-Mount,
saubere Journale und Prüfung sämtlicher Unterbrechungen. Bestehende Quarantäne
nicht löschen oder automatisch zurücksetzen.

Der erneute Fehler hat Code 5, nicht `SQLITE_FULL` oder `SQLITE_IOERR`; der
betroffene neue Testroot war exklusiv und synthetisch. Das spricht für einen
Lockkonflikt zwischen den legitimen Verbindungen desselben Jobs, nicht für
Root-Wiederverwendung oder ein fremdes Fixture-Cleanup. Es beweist die konkrete
Entstehung des früheren Config-Resume-Fehlers nicht. Testlauf: SQLite 3.50.4;
historische Nur-Lese-Inspektion: System-SQLite 3.40.1. Redigierter Fehlerbeleg:
`sqlite_observation.v1.json`.

## D: Drafts und Integrationsreihenfolge

| PR | Geprüfter Head | Git/Review/Produktion |
| --- | --- | --- |
| [Backend #149](https://github.com/rf-data/Personal_Assistant/pull/149) | `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb` | Diff auf #155 anwendbar; HTML-Aggregation fachlich reviewfähig; Handoff-v2-Verbraucher und tatsächlicher Rollout separat abnehmen |
| [Backend #148](https://github.com/rf-data/Personal_Assistant/pull/148) | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Diff auf #155 und nach #149/Korrektur anwendbar; Gate-Kern reviewfähig, betrieblich unvollständig: konkreter Driver, Triggerinventur, Erstbootstrap und Hostbelege fehlen |
| [UI #20](https://github.com/rf-data/personal-assistant-ui/pull/20) | `6b84e3c09f877309a3fd1c6f9cbcf61bb9f46788` | Dokumentationsdiff auf Main anwendbar; fachlich reviewfähig, Live-HTTPS-/OIDC-/VPN-Abnahme fehlt |

Alle drei: OPEN/Draft, GitHub `mergeable=true/clean`, keine Reviews,
Inline-Reviewkommentare oder Check-Runs. Commitstatus `pending` mit null Kontexten
ist kein grüner oder laufender CI-Beleg. Auch die tatsächlichen Backend-/UI-
Default-SHAs besitzen keine Check-Runs oder GitHub-Actions-Läufe.
Lokale Regression ersetzt kein Review.
Kein PR wurde geändert, gemergt oder automatisch auf Ready gesetzt.

1. **Jetzt GO:** fachliches Review dieses Korrektur-PRs, von #149, des Gate-Kerns
   in #148 und von UI #20; parallel die [lesende Inventur](https_vpn_operator.md).
2. **Vor jedem Merge NO-GO bis belegt:** Coolify-Ressourcen/Branch/Trigger,
   wartende Deployments, exakte Worker-/Queue-/Mountzuordnung, Backup/Rollback
   und Verantwortlicher für einen kontrollierten Deploymentpfad. Push-/Preview-
   Trigger gehören ebenfalls zum Bestand. Eine etwaige Triggeränderung braucht
   eigene Freigabe. Unbekannte Werte verhindern einen Merge auch bei Docs.
   Solange der Gate-Erstbootstrap fehlt, muss ein freigegebener vorhandener
   Wartungs-/Annahmestopp mit Drain und belegtem Idle jeden möglichen
   Containerwechsel absichern; ein noch nicht integriertes Gate gilt nicht als
   Schutz der vorangehenden Stabilisierung oder von #149.
3. Danach separat genehmigt: **Stabilisierung → #149 → #148 → UI #20**.
   Vor jedem Schritt aktuellen Master/Main, exakten Head, Reviews und Regression
   erneut prüfen. Für #149 insbesondere echte HTML-Projektion und v1/v2-Handoff;
   für #148 zusätzlich C16/C18, Gate/Drain/Recovery und Rolloutvertrag. UI #20
   darf fachlich parallel gelesen werden; sein Betriebsdokument soll den
   tatsächlich genehmigten Backendpfad beschreiben.
4. Vor #148-Produktionswirkung müssen konkreter Driver und exklusiver Triggerpfad
   reviewt und der Erstbootstrap separat genehmigt sein. Gate-Default ist opt-in;
   ein Merge schützt bestehende Writer nicht automatisch. Keine überlappenden
   alten/neuen Worker und keine Umgehung durch unabhängige Import-/Pilotprozesse.
5. Deployment, HTTPS/VPN-Negativabnahme, Rollback und Resume benötigen eigene
   Betreiberfreigaben für exakte SHA/Image-Digest-Paare. Danach erst über einen
   [einzelnen Week-0-Piloten](week0_operator.md) entscheiden. Kein Auto-Merge.

## C: Kapazität und Betreiberaktionen

Die Messung, das unveränderte Batchbudget und der konkrete Bereinigungsplan stehen
in [capacity.md](capacity.md). **Lokaler Pilot: NO-GO**, solange erforderlicher
freier Platz, Inodes/Mount, Grants und Rohdaten nicht belegt sind. Ein kleineres
Archiv rechtfertigt kein Unterschreiten der bestehenden Mindestreserve.

Die beiden ausführbaren Checklisten sind [HTTPS/VPN](https_vpn_operator.md) und
[CS50P Week 0](week0_operator.md). Ihre Befehle sind Betreiberrezepte, keine in
diesem Auftrag ausgeführten Hostaktionen. Es wurden keine produktiven Writer,
echten Kursdownloads oder Imports der vorhandenen ZIP-Archive gestartet.

## Aktuelle Validierung

| Lauf | Ergebnis |
| --- | --- |
| Drei zuvor blockierte Knowledge-Batchfälle, echte Offlinefunktionen/Fake-HTTP/Resume | **3 bestanden** |
| Relevante gemeinsame Regression: #155 + Korrektur + unveränderte #149/#148 | **493 bestanden**, 2 erwartete Testdatenwarnungen |
| Knowledge-Runner, Scheduler/Resume, Reports, Budget und Checkpoints | **65 bestanden** |
| Knowledge-Input und erste vier SQLitefälle | **31 bestanden, 1 übersprungen**: ursprünglicher SRT-Pilot nicht bereitgestellt |
| C18 vor SQLitekorrektur, mit Diagnose | **23 bestanden, 1 Quarantänefehler** mit belegtem SQLITE_BUSY |
| Deterministischer SQLitetest vor Korrektur | **2 fehlgeschlagen, 2 bestanden**; erwarteter Negativbeleg |
| C18 nach Korrektur und erste vier SQLitefälle | **28 bestanden** |
| UI-Main + unveränderter #20-Diff | **24 bestanden, 9 Subtests bestanden** |

Die 493 Fälle enthalten nochmals alle 24 C18-, 66 Gate-, 34 HTML-, 15
Assignment-, 23 Materialbatch-Worker- und fünf endgültigen SQLitefälle sowie
C16/B5/B6/ZIP/Multiformat/HTTPS-/Runtimepfade. Läufe überlappen und werden nicht
addiert. Die echten HTML-Exporte wurden lesend geprüft; das ist kein neuer
Produktionsjob. Keine vollständige Suite aller optionalen Repositoryprofile
oder produktive Image-/Host-/Browserabnahme behauptet.

Ruff-Formatprüfung aller sieben geänderten Pythondateien und neue Tests/SQLite-
Datei: bestanden. Vollständiger Ruff-Lint der berührten Altdateien meldet dieselben
drei bereits auf Master vorhandenen F821-Befunde (`_get_extract_knowledge`,
`classify_resource_file`, `run_name`), keine neuen. Diese Legacyfunktionen
sind nicht Teil des getesteten Offlinepfads und bleiben außerhalb dieses Fixes.
JUnit-/Loghashes, Fehlversuche und Quellen stehen in `validation.v1.json`.

## Aufbewahrung und Abschlussgrenze

Eigene Artefakte dieses Auftrags: Branch `fix/c26-stabilization`, Worktrees
`Personal_Assistant-c26-stabilization`, `Personal_Assistant-c26-stabilization-compat`
und `personal-assistant-ui-c26-stabilization-check`, Ergebnisse unter
`Personal_Assistant-c26-stabilization-results`. Kompatibilitätsworktrees enthalten
absichtlich die unveränderten Draft-Diffs und die Korrektur. Vorbestehende
Worktrees, Pythonumgebungen, Bundles, Git-Objekte, Pilotdaten und Konfigurationen
bleiben erhalten. Keine Bereinigung oder Speicherlimitänderung durchgeführt.

Die Dokumente werden mit dem Review-PR bereitgestellt. Ohne genehmigten Merge
sind sie noch nicht im Defaultbranch integriert; diese Integration bleibt wegen
der ausdrücklich ungeklärten Produktionswirkung ausstehend. Branch und Worktrees
bleiben dafür erhalten, auch bei einer externen Statusänderung ohne Löschfreigabe.
