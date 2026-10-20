# Repositoryinventar und Vollständigkeitsabgleich (C17.0)

Stand: 16.10.2026. Primär `gmp_compliance` / `rf-data/Personal_Assistant`.
[Maschineninventar](audit/repository_inventory.v1.json),
[UI-Inventar](audit/ui_inventory.v1.json),
[Remote-/PR-Snapshot](audit/remote_snapshot.v1.json).
Die veröffentlichte JSON-Fassung enthält ausschließlich Pfade/Blob-IDs der
verifizierten bereits veröffentlichten Git-Trees und aktuelle Dokumentations-
und Testbelege. Vollständige lokale Worktree-/Pfad-/Hash-/Import-/Statusdetails
liegen ausschließlich in der ignorierten privaten Ablage `docs/_local_audit_c170/`
und werden nicht mit dem PR übertragen. Die Daten dokumentieren konkrete Snapshots; sie sind kein laufender Server- oder
Datensatzscanner. [Dokumentenaudit](documentation_audit.md) und
[Freigabeliste](cleanup_plan.md) enthalten die fachlichen Bewertungen.

## Ausgangszustand und ausgeführter Abgleich

| Bereich | Vorher lokal | Verifizierte Referenz / Ergebnis |
| --- | --- | --- |
| Backend-Hauptarbeitskopie | Branch `master`, `b58f63c` (C15) | neuer Audit-Branch `docs/c170-repository-consolidation-public` ab Remote-`master` `78b35a5` |
| Backend-Remote | `78b35a53b7fc7148a1cbaeb93c4152d35a0725f1` | Tree `d67a1115855ac0a78b555a6a6067aa8788a7e321`, lokal exakt geprüft |
| Verifizierter C18-Inhalt | `d2c07f9` | derselbe vollständige Tree wie Remote-`master`; PR #67 inzwischen gemergt |
| UI-Hauptarbeitskopie | `main`, `b2cf9ca` | älter; im Audit unverändert, keine UI-Datei geschrieben |
| UI-Remote / geprüfter C17-Inhalt | Remote `137651e`, lokal `9d9ed61` | beide Tree `495ab64ab6f860840afc7a2c104816f5ef5e5255`; UI-Prüfung gegen diesen aktuellen Inhalt |

Die GitHub-Mergeobjekte wurden anhand ihres kanonischen signierten Inhalts und
Commit-/Treehashes verifiziert. Der Wechsel im Hauptverzeichnis erfolgte ohne
Reset, Force, Cherry-Pick alter Codekopien oder History-Rewrite. Der alte lokale
`master`-Ref bleibt erhalten; die Arbeitsdateien liegen jetzt auf dem neuen
Audit-Branch mit vollständigem aktuellem Masterinhalt und den Auditänderungen.

Vor dem Wechsel gab es im Hauptverzeichnis **keine versionierte lokale Änderung**,
aber eine zusätzliche Benutzer-Roadmap. Sie blieb unversioniert und bytegleich;
Dateiname und Vergleichshash verbleiben ausschließlich im privaten lokalen Bericht.
Private lokale Konsolidierungsberichte und ignorierte Planungsdateien wurden
nur als Metadaten erfasst, nicht inhaltlich gelesen oder veröffentlicht.

## Versionierte Ausgangsbasis

627 Dateien, darunter 353 Pythondateien. Die Kategorien sind disjunkt nach
Scannerpriorität; beispielsweise zählen drei Fixture-READMEs unter Fixtures,
insgesamt existieren deshalb 130 Markdown-/RST-Dokumente bei 127 Einträgen in
der Kategorie Dokumentation. Diese Zahlen beziehen sich auf den Master-Tree vor
den neu erzeugten Auditdateien, nicht auf eine selbstreferenzielle Endzählung.

| Kategorie | Dateien |
| --- | ---: |
| Pythonmodule außerhalb spezieller Kategorien | 185 |
| Runner / Shell-/CLI-Einstiege | 46 |
| Tests außerhalb der Fixtures | 64 |
| Modellpfade | 40 |
| Prototypen | 24 |
| Dokumentation | 127 |
| Fixtures | 15 |
| Konfiguration | 14 |
| Docker-/Deploymentdateien | 4 |
| Weitere Dateien / Locks / Quellsnapshots | 108 |

Der öffentliche JSON-Bericht enthält relative Pfade, Git-Blob-IDs und Kategorien
aus der unabhängig verifizierten veröffentlichten Basis. Vollständige Bytegrößen,
statische Pythonimports und Main-Guard-Indikatoren bleiben im privaten lokalen
Detailbericht. Alle
353 versionierten Pythondateien waren syntaktisch per AST lesbar; das führt
keinen Modulcode aus und bestätigt weder Importierbarkeit noch Funktionsfähigkeit.
Dateien mit sensitiven Namen, private Runtime-/Datenpfade und Symlinks werden
nicht für Inhalts-/Hashprüfungen geöffnet.

## Lokale Struktur und Zuständigkeit

| Pfadgruppe | Befund / zuständiger Einstieg |
| --- | --- |
| `src/model_*`, `src/tools_*` | Discovery-, Material-, Transcript-, Lecture-, Knowledge- und Evaluationsverträge/-funktionen |
| `src/job_control/`, `src/workflows/` | gemergte C16-/C18-Steuerung; private Jobqueue und begrenzte Offlineausführung |
| `scripts/`, `src/run_*.py` | moderne explizite CLIs neben teilweise global konfigurierten Legacyrunnern |
| `tests/`, `tests/fixtures/` | deterministische Offlinefälle, synthetische Fixtures und optionale Originalprüfungen |
| `configuration/`, `docker/`, `workers/`, `monitoring/` | versionierte Konfiguration/Profile neben ignorierten lokalen Betreiberdateien und Runtimevolumes |
| `frontend/`, `streamlit_app.py`, `st_admin_app.py`, `st_chat_app.py` | erhaltene frühere Streamlit-/Chat-/Adminpfade; kein Ersatz für die separate C17-App |
| `_prototypes/` | Experimente; teilweise weiter referenziert, kein pauschales Löschziel |
| `data`, `logs`, `mongo_db`, DVC, `.venv`, Caches und private Orga-/Konfiguration | nur aggregierte Metadaten, keine Inhaltsprüfung, Migration oder Löschung |

## Andere Worktrees und lokale Abweichungen

16 Backend-Worktrees und drei UI-Worktrees wurden anhand Git-HEAD, Status,
Dokumentpfad und SHA-256 erfasst. Kein Worktree/Branch wurde entfernt.
In **keinem** der untersuchten Backend-HEADs existiert eine Pythondatei, deren
relativer Pfad im aktuellen Master fehlt. Ältere Implementierungen an denselben
Pfaden unterscheiden sich teilweise: Das beweist keine ungeprüfte fachliche
Gleichwertigkeit. Sie wurden nicht zurückkopiert oder als neue Masterfunktion
übernommen. Der geprüfte C18-Inhalt ist sogar vollständig treegleich zur Basis.

Noch lokal vorhandene Änderungen außerhalb des Primärverzeichnisses:

- Älterer Abschlussaudit-Snapshot: zwei unversionierte Abschlussdokumente;
  ihre Inhalte sind bereits im vorhandenen CS50-Archiv nachweisbar erhalten.
- Älterer HTML-Parser-Snapshot: lokale Änderung an `.gitignore`; nicht übernommen.
- `gmp_compliance`: die oben genannte unversionierte Roadmap-Ergänzung;
  keine Veröffentlichung ihres Inhalts.

Alle übrigen untersuchten Backend-Worktrees waren vor dem Audit versioniert
unverändert. Ihre unterschiedlichen lokalen Commit-HEADs sind nur im privaten Detailbericht dokumentiert;
Ancestry, identische Bäume und inhaltliche Varianten werden getrennt ausgewiesen.
Der vorherige [Konsolidierungsbericht](project_consolidation_report.md) bleibt ein
historischer Nachweis und wird nicht als aktueller Gesamttest umgedeutet.

## Ignorierte/unversionierte Dateien und Schutzgrenzen

Die Inventur zählt rund 55.000 von Git sichtbare ignorierte Dateien nach
Pfadgruppe, Bytegröße, Symlink- und Statfehlerzahl. Die exakten lokalen Snapshotzahlen
stehen im privaten Detailbericht. Darunter sind Umgebungen/Caches, lokale Daten und Logs,
Konfigurationen und Monitoringpersistenz. Es werden keine privaten Dateiinhalt-
oder Rohdatenlisten veröffentlicht.

Git meldete nicht lesbare lokale Monitoringunterverzeichnisse. Ihre Kinder sind
nicht vollständig inventarisiert; die Aggregatzahlen sind Untergrenzen, keine
Behauptung vollständiger produktiver Datenerfassung. Der Auditor verfolgt keine
Symlinks. Die separate Testvalidierung dokumentiert außerdem den gefundenen
Fehler der früheren Monitoring-Fixture und deren anschließende Begrenzung auf
versionierte Konfigurationen; [Nachweis](audit/validation.md).

## Offene PRs und vollständiger Dokumentationsstand

C10–C13/C15/C16/C18 im Backend sowie C14/C17 im UI sind gemergt. Weiterhin offen
sind Backend-PRs #6, #9, #10 und #11. [Einzelprüfung](cs50/operations/historical_pr_review.md):
#9 enthält den noch relevanten TXT-Unknown-Time-Rest; die übrigen Funktionen
wurden später fachlich integriert/ersetzt. Kein alter PR wird hier geschlossen,
gemergt oder ungeprüft übernommen.

Vor der Aktualisierung fehlten lokal elf Markdown-/RST-Dokumente aus C16/C18
und dessen Fixturebeschreibung, außerdem deren JSON-Vertrags-/Reportartefakte.
Nach dem Wechsel ist jedes versionierte Dokument des aktuellen Master vorhanden.
49 weitere alte Dokumentpfade sind durch das bereits bestehende Archivierungs-
manifest auf heutige Verträge/Betriebs-/Archivpfade abgebildet; sie sind nicht
allein wegen anderer Namen als verloren oder identisch bewertet worden.
[Pro-Datei-Abgleich](documentation_audit.md).
