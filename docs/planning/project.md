# Ein gemeinsames GitHub Project – PM-01

19.10.2026. Ausschließlich das vom Projektinhaber benannte
[**User-Project #1**](https://github.com/users/rf-data/projects/1) weiterverwenden.
Kein weiteres Project, kein Ersatzplanungsdienst. Vorgesehener Name bleibt
„Personal Assistant – Development“; **der tatsächliche Titel ist nicht auslesbar**.
Eine Namensabweichung ist deshalb weder bestätigt noch ausgeschlossen.

## Tatsächliches Inventar und Zugriffslücke

| Merkmal | Nachgewiesener Stand | Nächster Prüfschritt |
| --- | --- | --- |
| Owner / Nummer / URL | URL des Eigentümers: `rf-data`, User-Project `1`, obiger Link | Über autorisierte Projectansicht/API öffnen |
| Globale Project-Node-ID | unbekannt, Nummer 1 ist keine GraphQL-ID | `ProjectV2.id` lesen |
| Titel / Beschreibung | unbekannt; geplanter Titel siehe oben | Tatsächlichen Titel übernehmen, keine Umbenennung erzwingen |
| Verknüpfte Repositories | unbekannt; geplant Backend + UI | Beide Repos/bestehende Verknüpfungen prüfen |
| Views / Layouts / Filter | unbekannt | Bestehende Ansichten inventarisieren, sinnvoll weiterverwenden |
| Felder / IDs / Typen / Optionen | unbekannt | Status, Priority, Workstream, Milestone samt existierenden Werten lesen |
| Items / Draftitems / Issue-/PR-Links | unbekannt | Vollständig paginieren, auch Drafttitel/IDs deduplizieren |
| Automatisierungen | unbekannt | Auto-Done/Close/Add/Archive vor Itemänderungen prüfen; unverändert lassen bis gezielter Entscheid |
| Zugriffsrollen / Schreibrechte | unbekannt | Owner-/Projectrolle und Token/App-Berechtigungen separat nachweisen |

Repo-Adminrechte beider Repositories sind beobachtet. Sie reichen als
Projectberechtigungsnachweis nicht aus. Der Connector bietet keine Projecttools
und lehnt Owner-/Repo-Projects und GraphQL ab; `gh` ist nicht vorhanden. Der
öffentliche Webabruf liefert keinen Projectinhalt. Keine Credentials aus lokalen
Dateien lesen, keine automatische Installation oder Scopeausweitung.

**Keine bestehenden Views/Felder/Items oder Regeln wurden geändert.** Folgendes
ist eine kontrollierte Sollzuordnung, keine behauptete Istkonfiguration.

## Felder nach Bestandsprüfung zuordnen

| Gewünschtes Feld | Bedeutung / vorgeschlagene Werte |
| --- | --- |
| Status | Bestehende Werte bevorzugen; Soll Backlog, Ready, In Progress, In Review, Done. Keine vorhandenen Optionen löschen/ersetzen, um diese fünf zu erzwingen |
| Priority | Bestehende Skala mappen; P0 Release-Gate, P1 Kernpfad, P2 optional/später, P3 Idee |
| Workstream | Persistence, Retrieval, UI, Operations, Sources, Evaluation, Legacy, Entities; vorhandene passende Werte wiederverwenden |
| Target milestone | C23–C32, bei eigenständigem PyRepo-Projekt leer; vorhandenes Milestonefeld statt Duplikat nutzen |
| Repository / Assignees / Labels | Eingebaute Felder nutzen; unbestätigte Assignees leer lassen |

Lieferzustand/Realabnahme bleibt im Issuebody nachvollziehbar und ist kein neuer
automatischer Done-Workflow. `blocked` und konkreter Entscheid im Issue; bei schon
begonnener Arbeit tatsächlichen Arbeitsstatus erhalten. Optionale Semantik bleibt
außerhalb des lexikalischen kritischen Pfads.

## Gewünschte Ansichten, erst nach Inventar speichern

| Ansicht | Vorschlag |
| --- | --- |
| Active Work | Bestehendes Board nach Status; Backlog/Done ausblenden; Priority, Workstream, Target und Repository anzeigen |
| Roadmap by Milestone | Tabelle nach vorhandenem Target-milestone-Feld gruppieren; keine erfundenen Termine/Timeline |
| Blocked Issues | Tabelle nach `blocked`-Label, abgeschlossene Items ausblenden; konkrete Blockade im Issuebody |
| My Projects / Personally Owned Work | Persönliches Vorhaben über `owner:human`/`personal-project`-Labels sichtbar machen; Account/Assignee nur nach Bestätigung. Kein C27-Abhängigkeitspfeil |

Konkrete Filter an tatsächliche Feld-/Optionsnamen anpassen und in der UI prüfen;
keine ungetesteten Filter als gespeichert ausgeben. Labelkonventionen zuerst lesen;
für PyRepo gegebenenfalls `owner:human`, `cs50p`, `personal-project`, `optional`
kontrolliert ergänzen. Account `rf-data` ist verifiziert, eine Zuweisung wurde nicht
vorgenommen. Keine Codex-Automation an das persönliche Vorhaben hängen.

## Workflows, Rechte und nächste Schritte

Kein Auto-Close/-Archive/-Add aktivieren und keine vorhandenen Workflows blind
deaktivieren. Existierende PR-Merge-zu-Done-Regeln dürfen Meilenstein-Parents oder
Realabnahme nicht automatisch abschließen; konkrete Regel/Itemwirkung zuerst
lesen, dann gezielt entscheiden. Keine fremden Items umklassifizieren.

Mit geeignetem bereits autorisiertem GitHub-Web-/APIzugriff bestehende Struktur
und Projectrechte belegen, den [Ausführungsablauf](github_execution.md) anwenden
und reale IDs/Optionen/Itemlinks erfassen. Erst dann die genehmigten verbleibenden
Issues und Updates ausführen. Kein weiteres Board erstellen, auch bei fehlendem
Zugriff. [Tatsächliche Aktionen und Grenzen](pm01_validation.md).
