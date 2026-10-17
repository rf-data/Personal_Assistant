# Ein gemeinsames GitHub Project – Entwurf

**Nicht angelegt oder geändert.** Vorgesehener Owner `rf-data`, Name
**Personal Assistant – Development**, für beide Repositories. Eine vorhandene
passende Project-ID zuerst suchen und wiederverwenden. Bestand/Zugriff sind
wegen der [Connectorgrenzen](status.md) unbekannt; keine Project-URL erfinden
und keine parallelen Boards pro Repository erzeugen.

## Felder und Bedeutungen

| Feld | Typ / Werte | Regel |
| --- | --- | --- |
| Status | bestehendes Single Select: Backlog, Ready, In Progress, In Review, Done | exakt diese fünf Arbeitszustände; kein sechster Blocked-Status |
| Priority | Single Select: P0, P1, P2, P3 | P0 = Release-Gate, P1 = Kernpfad, P2 = später/optional, P3 = unverbindliche Idee |
| Workstream | Single Select: Persistence, Retrieval, UI, Operations, Sources, Evaluation, Legacy, Entities | primäre Zuständigkeit, kein neuer fachlicher Status |
| Target milestone | Single Select: C23, C24, C25, C26, C27, C28, C29, C30, C31, C32 | gemeinsames strategisches Ziel; keine doppelten Repo-Milestones nötig |

Die eingebauten Felder Repository, Assignees und Labels wiederverwenden. Kein
Owner oder Lieferdatum wird erfunden. Fehlende Zuweisung ist sichtbar und vor
Ready zu klären. Parent und Kinder erhalten denselben Target-milestone-Wert,
auch wenn ein UI-Kind zu einem Backend-Parent gehört.

Blockierung: Label `blocked`, konkreter Grund/Abhängigkeit, nächste Entscheidung
und zuständige Person im Issue. Vor Start verbleibt das Issue Backlog; eine
begonnene blockierte Arbeit bleibt mit Label im tatsächlichen Arbeitsstatus.
Die Projektsicht ersetzt weder native Parent-/Sub-Issue-Beziehungen noch URLs.
[Offizielle Filterdokumentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/filtering-projects).

## Ansichten

| Name | Layout / Filter / Gruppierung |
| --- | --- |
| Active Work | Board nach Status; Filter `-status:Backlog -status:Done`; Priority/Workstream/Target milestone und Repository anzeigen |
| Roadmap by Milestone | Tabelle mit allen geplanten Paketen, nach Target milestone gruppiert; Parents und Cross-Repository-Kinder sichtbar; keine unbelegten Zeitachsen |
| Blocked Issues | Tabelle, Filter `label:blocked -status:Done`; Blockiergrund im Issue, gruppiert nach Target milestone |

Optionen/gespeicherte Ansichten im UI prüfen und explizit speichern. Die Tabelle
„Roadmap“ ist ohne Terminentscheid keine Timeline. Bei einem vorhandenen Board
seine Felder und Items erst inventarisieren; abweichende Statusoptionen nicht
ungefragt löschen, ersetzen oder alle vorhandenen Items umklassifizieren.

## Automatisierung und Rechte

GitHub kann standardmäßig geschlossene Issues beziehungsweise gemergte PRs auf
Done setzen. Für diese Planung solche Workflows vor dem Einfügen prüfen und die
automatische Abschluss-/Schließlogik deaktivieren; der Parentabschluss bleibt
manuell. Auch Auto-Archive/Auto-Add werden zunächst nicht aktiviert.
Ein PR-Merge belegt keine fachliche Evaluation oder Produktionsfreigabe.
[Offizielle Workflowdokumentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations).

Der Connector zeigt Repo-Schreibrechte, stellt aber keine Projects-v2-Werkzeuge
bereit und lehnt GraphQL/Owner-Projects ab. `gh` fehlt lokal; es wurde nicht
installiert und kein Token aus Dateien verwendet. Projects benötigen einen
passenden Ownerzugriff und passende API-Berechtigungen; Repo-admin allein genügt
als Nachweis nicht. GitHub dokumentiert `read:project` für lesende und `project`
für schreibende Classic-Token-Zugriffe; feinere Token-/Apprechte nach gewähltem
Verfahren prüfen. [API und Authentifizierung](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).

Nach ausdrücklicher Freigabe kann ein bereits verfügbares autorisiertes `gh`
oder die GitHub-Weboberfläche diese Konfiguration anwenden. Keine neue
Appinstallation oder Credentialausweitung wird aus der Planfreigabe abgeleitet.
[Konkreter Ablauf](github_execution.md), [Feldbefehle](https://cli.github.com/manual/gh_project_field-create).
