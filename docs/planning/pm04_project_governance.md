# PM-04 – Project-Governance und abschließende Konsistenzprüfung

19.10.2026, Europe/Berlin. [Project #1](https://github.com/users/rf-data/projects/1),
privat, Owner rf-data, ID `PVT_kwHOC92AuM4BneNA`. **Alle sicher lösbaren
Governancepunkte geprüft; Statusfeld bereinigt.** Reale Abnahmen und laufende
Entwicklung bleiben außerhalb dieses organisatorischen Abschlusses.
Die aktuelle Dokumentintegration wartet auf regulären Review/Merge.

Maßgeblich bleiben [der 45er-Plan](issue_plan.v1.json),
[PM-03-Ausführungsnachweis](pm03_project_execution.md) und
[Reconciliation mit dem neuen Abschnitt `pm04_governance`](pm03_reconciliation.v1.json).
Keine neue Roadmap oder parallele Planungsdatenbank. PM-01 #92, PM-02 #94 und
PM-03 #118/#120 sind nach live gelesenem PRzustand gemergt; die bestehenden
Planungsdokumente wurden aus dem tatsächlichen master gelesen.

## Ausgangsinventur vor Statusbereinigung

| Prüfung | Tatsächlich verifiziert |
| --- | --- |
| Project-Items | **60**: 33 PRs, 27 Issues; keine Drafts/Archive |
| Statuswerte | 34 Backlog / 26 Done; alle 27 Issues offen |
| Plan-IDs | **44/45** auf 42 kanonische Items; Aliaspaare korrekt |
| Parent / Blocked-by | **14 / 35**, unverändert |
| Felder / Views | **20 / 8**, keine Neuanlage |
| Milestones | 12, 42 Zuordnungen; keine Due-Dates |
| Datums-/Iterationseinträge | **0**; keine Terminwerte ergänzt |
| UI-Aufnahme | Sieben offene Issues jeweils einmal vorhanden; null offene PRs |
| Priority | P0/P1/P2 separat; 6 P0 / 29 P1 / 9 P2 / 16 unbelegt |

Der PM-03-Kernstand 56 wurde nicht wiederhergestellt: die vier späteren
Dokumentations-PRs #118–#121 erklären 60. Eigene spätere Dokumentationsaufnahme
wird nach Veröffentlichung separat gelesen; sie ersetzt keine Planrepräsentation.
Keine doppelten Items, Issueziele oder Aliasrepräsentationen.

## C24-06-A bleibt pending_real_target

Vollständige offene/geschlossene Issue- und PRlisten **beider** Repositories
enthalten weiterhin kein tatsächlich veröffentlichtes Scopeziel für C24-06-A.
Kein Parallelissue und kein Draft-Item erzeugt. Parent ist C24
([Backend #99](https://github.com/rf-data/Personal_Assistant/issues/99)); belegte
Abhängigkeiten sind C24-05-B2
([UI #7](https://github.com/rf-data/personal-assistant-ui/pull/7)) und C24-05-C2
([Backend #91](https://github.com/rf-data/Personal_Assistant/pull/91)). Deren
technischer Merge ersetzt keine lokale Browser-/Humanabnahme dieses Auftrags.

Erst nach Veröffentlichung des tatsächlichen PRs/geeigneten Issues dessen Scope
prüfen und genau dieses Ziel idempotent verknüpfen. Bis dahin 44/45 ausdrücklich
beibehalten; kein künstlicher 45/45-Abschluss und kein Eingriff in aktive Arbeit.

## Statusfeld: eine verifizierte Konfigurationsänderung

Vorher waren Priority, Workstream und Target milestone zusätzliche Statusoptionen.
Kein Item nutzte sie, kein gespeicherter Viewfilter referenzierte sie ausdrücklich.
Die Boards #1/#2 verwenden das Statusfeld als Spaltenfeld; leere Statusspalten
sind nicht mit einer eigenen Priority-/Workstreameigenschaft zu verwechseln.

Die öffentliche API zeigt Workflowtrigger/-ziele nicht vollständig. Der Betreiber
bestätigte nach expliziter Prüfung in der Oberfläche: **„Nach UI-Prüfung: keine
Verwendung“** dieser drei Optionen in irgendeinem der sieben Workflows.
Erst danach wurden genau diese drei Optionen entfernt. Die restlichen Optionen
blieben mit ihren bisherigen IDs, Namen, Farben, Beschreibungen und ihrer
Reihenfolge erhalten: **Backlog, In progress, Ready, In review, Done**.
Keine kosmetische Neuordnung bereits verwendeter Werte.

Ein unterstützter `updateProjectV2Field`-Aufruf mit expliziten vorhandenen
Options-IDs. Unmittelbarer Readback bestätigt sämtliche fünf Optionstupel exakt.
Die vollständigen Identitäten/Feldwerte/Zustände aller 60 Items, alle anderen
Felder, sämtliche Views und Workflow-Metadaten sind vor/nach der Mutation gleich.
**Null Itemstatusmutationen, null Issueclosures, null Workflowänderungen.**
Priority P0/P1/P2 und Workstream bleiben ihre bereits vorhandenen eigenen Felder.
Keine Datenmigration und kein zusätzliches Target-Milestonefeld.

## Views und Roadmap: frühere Spaltenempfehlung korrigiert

Alle acht Views wurden wiederverwendet. Die tatsächlichen `items(query:...)`-
Mengen stimmen jeweils mit unabhängiger Auswertung sämtlicher Feldwerte überein:

| Zielansicht | Vorhandene View | Treffer vor Dokumentations-PR |
| --- | --- | ---: |
| Roadmap / Milestones | #4 Roadmap | bestehende Timeline, keine Datumseinträge |
| Active Work | #6 | 0 |
| Prioritized Backlog | #2, Gruppierung Priority / Spalten Status | 34 |
| Blocked / Requires Decision | #7 | 17 |
| Technical Delivery / Real Acceptance Pending | #8 | 23 |

Roadmap #4 meldet Title/Assignees/Status und keine Gruppierung. GitHub dokumentiert
`visible_fields` ausdrücklich als für Roadmaps nicht anwendbar. Der frühere
PM-03-Spaltenvorschlag ist damit korrigiert; der fehlgeschlagene Aufruf wurde nicht
wiederholt. [Öffentlicher Views-Vertrag](https://docs.github.com/en/rest/projects/views).

Konkreter optionaler Betreiberschritt: View #4 → **View → Group by → Milestone**
oder Workstream. Date fields/Markers erst auf tatsächlich beschlossene Daten
beziehen; derzeit existieren keine Datumswerte oder Milestone-Due-Dates.
[Roadmap-Konfiguration](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout).
Der verfügbare GraphQL-Updatevertrag bietet dafür keine Gruppierungs-/Sortierfelder.
Die vorhandenen Tabellen #6–#8 zeigen Milestone/Workstream/Acceptance bereits.
Keine neue View als kosmetischer Ersatz und keine erfundenen Zeitbalken.

## Verbindliche Pflege- und Sicherheitsregeln

- Item added → Backlog, Auto-close-Auslöser → Done; Auto-addfilter
  `is:issue,pr is:open`, native Auswahl nur Backend. Diese Einstellungen sind
  Betreiberangaben; verfügbare API-Metadaten werden davon getrennt dokumentiert.
- Auto-close liefert weiterhin `enabled=false`, ist aber ohne ausdrückliche
  Deaktivierungsbestätigung **vorsorglich als aktiv** zu behandeln. Keine
  potenziell Issue-schließenden Statusaktionen und kein Umschalten der Automatisierung.
- Das bestätigte Tariflimit verhindert eine zweite native Auto-add-Regel.
  UI-Aufnahme bleibt manuell mit `gh project item-add`, nur nach vollständiger
  URL-/Node-ID-Prüfung und mit anschließendem Readback; vorhandene Einträge wiederverwenden.
  Kein Polling, Scheduler, Actionsworkflow oder neues Secret.
- Done beschreibt ausschließlich den belegten Scope des jeweiligen Items.
  Technische PR-Merges dürfen offene Parent-/Real-/Produktionsabnahmen nicht schließen.
  C23-06 ([#107](https://github.com/rf-data/Personal_Assistant/issues/107)), C24-05
  ([#108](https://github.com/rf-data/Personal_Assistant/issues/108)), C26
  ([#100](https://github.com/rf-data/Personal_Assistant/issues/100)) und die
  C26-06/-07-Abnahmen bleiben offen/Backlog mit gesondertem Acceptancefeld.
- D06/D07 bleiben sourcebezogene Entscheidungen. Keine Realmaterial-/Migration-/
  Produktions-/Deploymentfreigabe. PRs #72/#88/#89 nicht geändert oder geschlossen.

## Nachweise, Grenzen und Integration

CLI authentifiziert als rf-data mit vorhandenen Scopes, keine Credentialdatei
geöffnet. Vollständige Pagination der Projectitems einschließlich Archivzustand,
Feldwerte, Felder/Optionen, Views/Gruppierungen, Workflows, Repository-Issues/-PRs
und Milestones geprüft. Bestehende Parent-/Blockingkanten explizit erneut gelesen;
keine Änderung der 14/35 Kanten. 45 IDs, 42 kanonische Ziele, Aliaspaare,
eindeutige Issues, tatsächliche Filtermengen, Quellplan-SHA und geschützte
Abnahmezustände validiert. Kein Real- oder MAINT-Inventarlauf.

Dauerhafte Änderungen: zwei vorhandene PM-03-Dokumente aktualisiert und dieser
kleine neue Governancebericht. `issue_plan.v1.json` und alte MAINT-Unterlagen
unverändert. Quellplan-SHA256 weiterhin
`629b1c3471bc8654908bb99fbe5e1bc277edfb28272e1801bc8a8f065831580d`.
JSON-/ID-/Link-/Whitespaceprüfung; keine Runtimeänderung und keine Anwendungs-/
Ruff-/Pytestabnahme. Normaler eigener Dokumentations-PR; keine automatische
Zusammenführung. Der offene auftragseigene Branch bleibt bis verifiziertem Merge
erhalten. Kein neuer lokaler Arbeitsbranch/Worktree und keine Bestandsbereinigung.

Verbleibende Betreiberaktionen: optionale Roadmapgruppierung und echte Terminplanung,
spätere Veröffentlichung/Bindung von C24-06-A sowie normale Dokumentreview/-integration.
Fachliche Realabnahmen sind **keine PM-04-Abschlussvoraussetzung**. Sie werden durch
diese Governanceprüfung weder bestätigt noch als erledigt ausgegeben.

Publikationsbasis vor PRanlage: `e478520d259ad1342f5641828586c4cd2876114f`.
AGENTS, Quellplan und beide fortgeschriebenen PM-03-Dateien sind gegenüber der
Inventurbasis `d5f622be5b5435b20099823be5c4c300cfcaad50` byteidentisch.
Zwischenzeitliche fremde Integrationen werden durch diesen Dokumentations-PR
weder überschrieben noch als eigene Änderungen ausgegeben.

Letzter Readback vor PRanlage: weiterhin **60 Items**, nun **33 Backlog /
27 Done**. Ausschließlich #121 wechselte durch einen zwischenzeitlichen fremden
Merge von OPEN/Backlog zu MERGED/Done. Das ist keine PM-04-Statusmutation.
Alle 27 Issues bleiben OPEN; geschützte Drafts #72/#88/#89, alle 14/35 Beziehungen,
Views und Workflow-Metadaten unverändert. Ausgangs- und spätere Zählwerte werden
nicht als gleichzeitige Snapshots ausgegeben.

## Nach Veröffentlichung: 61 Items, Dokumentintegration offen

[Eigener PR #122](https://github.com/rf-data/Personal_Assistant/pull/122), Branch
`docs/pm04-project-governance`, offen gegen master. Die vorhandene Backendregel
fügte ausschließlich diesen neuen Dokumentations-PR einmalig mit Backlog hinzu;
kein manueller `item-add` und keine doppelte Aufnahme. Livebestand nun **61 Items
= 34 PRs + 27 Issues, 34 Backlog / 27 Done**. Die 44/45 Plan-IDs bleiben unverändert.

Alle bisherigen Items erneut abgeglichen: ausschließlich der zuvor dokumentierte
fremde Merge #121 verändert seinen Stand. Alle 27 Issues weiterhin offen, 14/35
Beziehungen, acht Views, Workflow-Metadaten und geschützte Drafts #72/#88/#89
unverändert. Die exakt drei PRdateien wurden aus dem veröffentlichten Commit
byteidentisch zurückgelesen; JSON-/ID-/Hash-/Link- und Whitespaceprüfung erfolgreich.
Anwendungstests/Ruff nicht ausgeführt, da ausschließlich Markdown/JSON geändert.

Beide primären lokalen Checkouts unverändert und ohne tracked/untracked
Statusänderungen. Kein lokaler Arbeitsbranch/Worktree angelegt. Der eigene
Remote-Arbeitsbranch bleibt wegen des offenen PRs erhalten; keine Bestandsobjekte
oder privaten Daten bereinigt. **Die dauerhafte Integration dieser Aktualisierung
in master ist noch nicht erfolgt und bleibt bis Review/Merge offen.**
