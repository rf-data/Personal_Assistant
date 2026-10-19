# PM-01 – autorisierte Ausführung und konkrete Zugriffsgrenze

19.10.2026. PM-01 autorisiert die beschriebenen **nichtdestruktiven Planungsänderungen**.
Eine erneute allgemeine Planfreigabe ist nicht nötig. Der Auftrag verlangt vor
Issue-/Projectmutationen aber die tatsächliche Prüfung des bestehenden Projects
und seiner Berechtigungen. Diese Prüfung ist mit den verfügbaren Werkzeugen
nicht möglich; deshalb bisher keine solche Mutation. Repositorydokumentation
wird unabhängig davon im separaten Planungs-PR konsolidiert.

## 1. Bekannter Bestand, keine erneute pauschale Freigabe

- Einziges Ziel: [Project #1](https://github.com/users/rf-data/projects/1), vom
  Eigentümer benannt; keine Projectneuanlage.
- Repo-Account `rf-data` und Repo-Schreibrechte bestätigt; Projectrechte unbekannt.
- 0 eigenständige Issues in vollständigen Backend-/UI-RESTantworten; 89/7 PRs.
- [45 Planzeilen](issues.md), darunter alle 32 ursprünglichen IDs. Technisch
  gelieferte Scopes referenzieren bestehende PRs, keine neuen offenen Doppelaufträge.
- #72/#88/#89 und alte offene PRs bleiben unverändert. C24-06-A ist unabhängig.

Project-Views/Felder/Items/Automatisierungen und Milestone-/Labelbestände sind
**unbekannt**, nicht leer. Auch unbekannte bestehende Draftitems berücksichtigen.
Ohne diese Prüfung keine blind angelegten Issues/Labels/Items und keine erfundenen
IDs/Optionswerte. Der [Inventarstatus](project.md) nennt jede Lücke.

## 2. Benötigter Zugriff, keine neue Software voraussetzen

Entweder vorhandene autorisierte GitHub-Weboberfläche verwenden oder in einer
bereits freigegebenen Umgebung ein verfügbares `gh` mit Projects-v2-Zugriff.
Hier fehlt `gh`; der Connector lehnt die nötigen Endpunkte ab. Keine Installation,
kein Lesen von `.env`-/Tokenfiles und keine automatische Berechtigungsausweitung.
Keine Tokens im Chat anfordern. Ein passender App-/Tokenzugriff muss Owner und
konkretes Project lesen bzw. für Änderungen schreiben dürfen.

Folgende **nicht ausgeführten** Beispiele dienen einer solchen Arbeitsumgebung:

```sh
gh auth status
gh project view 1 --owner rf-data --format json
gh project field-list 1 --owner rf-data --format json
gh project item-list 1 --owner rf-data --limit 100 --format json
gh api --paginate 'repos/rf-data/Personal_Assistant/issues?state=all&per_page=100'
gh api --paginate 'repos/rf-data/personal-assistant-ui/issues?state=all&per_page=100'
gh api --paginate 'repos/rf-data/Personal_Assistant/labels?per_page=100'
gh api --paginate 'repos/rf-data/personal-assistant-ui/labels?per_page=100'
gh api --paginate 'repos/rf-data/Personal_Assistant/milestones?state=all&per_page=100'
gh api --paginate 'repos/rf-data/personal-assistant-ui/milestones?state=all&per_page=100'
```

Bei mehr als 100 Projectitems tatsächlich vollständig über die API paginieren;
`--limit 100` allein beweist keine Vollständigkeit. Views, Workflows und Rollen
zusätzlich in Settings prüfen, wenn der genutzte CLI/APIweg sie nicht liefert.
Die Projectnummer 1 nicht als globale Node-ID verwenden. Native Repo-Milestones
nur nach Bestand/Bedarf setzen; vorhandenes gemeinsames Targetfeld bevorzugen.
Keine parallelen Milestones zur bloßen Verdopplung der zehn Parents anlegen.

## 3. Deduplizierung vor jeder Mutation

1. Frische offene/geschlossene Issue- und Projectitemliste inklusive Drafts lesen.
   Nach stabiler Plan-ID, Titel **und tatsächlichem Scope** abgleichen. 19.10.-Snapshot
   ist kein zukünftiger Dublettenbeweis.
2. Technisch implementierte Zeilen als vorhandene PR-/Meilensteinevidenz führen;
   keine offenen Reimplementierungsissues anlegen. Teilintegrierte Aufgaben nur
   mit ihrem Restumfang anlegen/aktualisieren. 02-C/03-B referenzieren #85.
3. Parents C23/C24 und C24-05 nicht Done setzen: D06/D07/Realabnahme fehlen.
   C26 niemals allein aufgrund von Merge/CI oder synthetischer Abnahme abschließen.
4. Bestehende unbekannte Projectitems zuerst zuordnen. Wenn eine Zeile bereits
   durch vorhandenes Issue/PR/Draftitem abgedeckt ist, dieses verwenden.
5. Original-ID, echte Issue-/PR-URL und Item-ID sofort erfassen. Nach Timeout vor
   Wiederholung erneut suchen; keine Doppelerstellung durch automatischen Retry.

## 4. Kleine kontrollierte Änderungen nach Zugriffsnachweis

Bodies aus [JSON](issue_plan.v1.json)/[Vorschau](issues.md) konkret vorbereiten:
Scope, aktuelle Grenzen, Priorität, Abhängigkeiten, Ownerfrage, Akzeptanz und reale
PR-Links. Keine Secrets/Originaltexte/private Pfade. Bestehende Templates nutzen.
Keine `Closes`-Referenz auf Realabnahme-/Meilenstein-Parents im Implementierungs-PR.

Nur verbleibende genehmigte Aufgaben anlegen oder bestehende aktualisieren;
Parents/Abhängigkeiten als tatsächliche URLs verlinken, native Sub-Issues nur bei
nachgewiesenem APIzugriff. Kein vorhandenes Parent ersetzen. Ohne native Funktion
bidirektionale URL-Checklisten verwenden, keine zweite Hierarchie erfinden.

PyRepo Inspector: einzig persönlich durch den Projektinhaber, keine Codex-Aufträge.
Account vor Assignment erneut prüfen; Labels an inventarisierte Konventionen
anpassen. Kein Programmcode/Repository. C27 bleibt unabhängig und hat keine
Hard-Abhängigkeit zum persönlichen Projekt. C32 enthält Real Python und kontrollierte
Moves; arXiv ist ein gemeinsamer Discovery-Provider, kein separater Scheduler.

Danach Project #1 wiederverwenden: existierende Felder/Statusoptionen mappen,
fehlende Felder gezielt ergänzen, ein Item je tatsächlichem Scope verknüpfen,
Prioritäten/Targets setzen und die vier gewünschten Views kontrolliert speichern.
Vor Statusänderungen automatische Done-/Close-/Archive-/Add-Regeln prüfen; keine
ungeprüften Auto-Regeln aktivieren oder bestehende Regeln pauschal abschalten.

## 5. Ergebnisprotokoll und Grenzen

Nach jedem Batch: vollständige Zuordnung Plan-ID → Issue/PR → Projectitem,
Abhängigkeiten, Priority/Target, fehlende Owner und gespeicherte Views erneut
lesen. Nur tatsächlich bestätigte Felder/IDs als Iststand dokumentieren. Bei
Teilfehler kein Löschen/Rollback bestehender Issues, sondern anhand der Zuordnung
fortsetzen. PM-01 hat bisher ausschließlich Dokumentation und den eigenen PR
geändert; **keine** Issues/Labels/Milestones/Projectdaten.

[PM-01-Prüfprotokoll](pm01_validation.md). Keine PRs mergen/schließen, keine fremden
Branches verändern, keine Produktions-/Mail-/Scheduleraktion. Die operative
Projectkonsolidierung bleibt bis zur benannten Zugriffsmöglichkeit offen.
