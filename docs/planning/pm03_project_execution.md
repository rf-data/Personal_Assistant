# PM-03 – GitHub Project #1 operativ konsolidiert

19.10.2026, Europe/Berlin. [Bestehendes privates Project](https://github.com/users/rf-data/projects/1),
`PVT_kwHOC92AuM4BneNA`, Owner `rf-data`, Updateberechtigung live bestätigt.
Backendbasis `b6fc464ef5217e3c1641e504d9f9c37989e0c4b1`, UI
`af95415071e85a461579c0a1650fdd0efe6c25b9`.
**Project-Konsolidierung ausgeführt und zurückgelesen; offene fachliche Abnahmen
bleiben offen. Dokumentintegration wartet auf regulären PRreview.**

Führende [45er-Planung](issue_plan.v1.json), [PM-02-Mapping](pm02_mapping.md) und
[PM-02-Reconciliation](pm02_reconciliation.v1.json) bleiben unverändert.
[Maschinenlesbarer Liveabgleich](pm03_reconciliation.v1.json) enthält alle 45 IDs,
Ziel-/Item-IDs, echte Feldwerte, Parent-/Abhängigkeitsmodi und konkrete Blocker.
Die frühere fehlende CLI-/Projectberechtigung wurde durch die ausdrücklich
freigegebene, vorhandene CLI behoben; dies ersetzt keine Realfreigabe.

Aktueller Fortsetzungsstand: PR #118 ist inzwischen gemergt. Das bestätigte
Tariflimit verhindert eine zweite native Auto-add-Regel; die UI wird nach
Betreiberentscheidung manuell und idempotent über `gh project item-add` gepflegt.
Der aktuelle Nachweis und die verbleibenden menschlichen Gates stehen im letzten
Abschnitt. Frühere Aufnahmestände und Konfigurationsvorschläge bleiben datiert.

## Tatsächliches Delta vor Veröffentlichung dieses Dokumentations-PRs

| Objekt | Vorher | Nachher / Änderung |
| --- | ---: | --- |
| Project-Items | 28 | **56**: 29 PRs, 27 Issues, keine Draft-Items/Archive |
| Bestehende Items erhalten | 28 | 28, Statuswerte unverändert |
| Neue eigenständige Issues | 0 | **27**: 20 Backend, sieben UI |
| Neuer PR-Eintrag | 0 | UI [#7](https://github.com/rf-data/personal-assistant-ui/pull/7), technisch gemergt |
| Status | 22 Done / 6 Backlog | **23 Done / 33 Backlog** |
| Felder | 18 | **20**, Workstream und Acceptance ergänzt |
| Views | 5 | **8**, drei neu und eine vorhandene angepasst |
| Native Repository-Milestones | 0 | **12**, alle offen, ohne erfundene Termine |
| Native Milestonezuordnungen | 0 | **42**: 26 neue Issues, 16 gemergte technische PRs |
| Native Sub-Issue-/Blocked-by-Kanten | 0 | **14 / 35** |
| Repräsentierte Plan-IDs | nicht Project-verifiziert | **44 / 45**, ein expliziter Blocker |

14 vorhandene kanonische PR-Items und zwei unterstützende PR-Items (#79/#82)
erhielten Metadaten; UI #7 kam einmal hinzu. 44 Items tragen jeweils Priority,
Workstream und Acceptance. Priority nutzt das vorhandene Feld: **6 P0 / 29 P1 /
9 P2 / 12 unbelegte**; keine zweite Priority und kein unnötiges P3.
Keine assignees oder menschlichen Freigaben erfunden.

Zehn Parent-Issues gruppieren weiterhin offene fachliche Umfänge. Native
Milestones sind Repositorygruppierung für die Roadmap, keine zweite
kanonische Aufgabe oder Abnahme. Backend: C23/C24/C26–C32; UI: C24/C25/C26.
PERSONAL-PYREPO hat keinen Milestone und trägt `human_only` und `optional`.
C27 besitzt keine harte Abhängigkeit von diesem persönlichen Vorhaben.

## Kanonische Ziele und Abhängigkeiten

`C23-02`/`C23-02A` teilen Backend #76, `C23-03`/`C24-04-B` Backend #72.
Damit 44 IDs auf 42 echte Project-Ziele, plus ein unveröffentlichtes aktives Ziel
= 43 geplante kanonische Repräsentationen. Kein Alias erzeugt ein Parallelissue.
Bei #72 gilt die höhere Priorität P1 und Workstream `Persistence / Retrieval`;
wegen unterschiedlicher C23-/C24-Ziele kein willkürlicher nativer Milestone.
Der Draft selbst, seine Texte/Heads/Bases und sein Project-Status bleiben unverändert.

C24-06-A: vollständige aktuelle PRliste enthält weiterhin keinen veröffentlichten
Backend-PR des geschützten Auftrags. Kein paralleles Issue oder Draft-Item erzeugt,
keine Donebehauptung. Zuordnung nach späterer tatsächlicher PRveröffentlichung
nachholen; aktive Backend-/UIworktrees unverändert erhalten.

Bei Issuezielen wurden mögliche Parent-/Abhängigkeitskanten nativ hergestellt und
zurückgelesen. PRziele werden nicht in Issues umgebaut: ihre Abhängigkeiten und
Parentbezüge bleiben explizite Plan-/URLbindungen. Neue Issuekörper enthalten
alle tatsächlichen Parent-/Dependencylinks; zwei PRparents können nur so
repräsentiert werden. Ein Alias erhält keine native Selbstabhängigkeit.
Keine `Closes`-Anweisungen, Issueclosures oder PRmerges.

Neue Issues, jeweils genau einmal im Project:

| Plan-ID | Repository-Issue |
| --- | --- |
| C23-06 | [rf-data/Personal_Assistant#107](https://github.com/rf-data/Personal_Assistant/issues/107) |
| C23 | [rf-data/Personal_Assistant#98](https://github.com/rf-data/Personal_Assistant/issues/98) |
| C24-02-C | [rf-data/Personal_Assistant#115](https://github.com/rf-data/Personal_Assistant/issues/115) |
| C24-03-B | [rf-data/Personal_Assistant#114](https://github.com/rf-data/Personal_Assistant/issues/114) |
| C24-05 | [rf-data/Personal_Assistant#108](https://github.com/rf-data/Personal_Assistant/issues/108) |
| C24 | [rf-data/Personal_Assistant#99](https://github.com/rf-data/Personal_Assistant/issues/99) |
| C25-01 | [rf-data/personal-assistant-ui#10](https://github.com/rf-data/personal-assistant-ui/issues/10) |
| C25-02 | [rf-data/personal-assistant-ui#11](https://github.com/rf-data/personal-assistant-ui/issues/11) |
| C25-03 | [rf-data/personal-assistant-ui#12](https://github.com/rf-data/personal-assistant-ui/issues/12) |
| C25-04 | [rf-data/personal-assistant-ui#13](https://github.com/rf-data/personal-assistant-ui/issues/13) |
| C25 | [rf-data/personal-assistant-ui#9](https://github.com/rf-data/personal-assistant-ui/issues/9) |
| C26-01 | [rf-data/personal-assistant-ui#14](https://github.com/rf-data/personal-assistant-ui/issues/14) |
| C26-02 | [rf-data/Personal_Assistant#109](https://github.com/rf-data/Personal_Assistant/issues/109) |
| C26-03 | [rf-data/Personal_Assistant#110](https://github.com/rf-data/Personal_Assistant/issues/110) |
| C26-04 | [rf-data/Personal_Assistant#111](https://github.com/rf-data/Personal_Assistant/issues/111) |
| C26-05 | [rf-data/Personal_Assistant#112](https://github.com/rf-data/Personal_Assistant/issues/112) |
| C26-06 | [rf-data/personal-assistant-ui#15](https://github.com/rf-data/personal-assistant-ui/issues/15) |
| C26-07 | [rf-data/Personal_Assistant#113](https://github.com/rf-data/Personal_Assistant/issues/113) |
| C26 | [rf-data/Personal_Assistant#100](https://github.com/rf-data/Personal_Assistant/issues/100) |
| C27 | [rf-data/Personal_Assistant#101](https://github.com/rf-data/Personal_Assistant/issues/101) |
| C28-01 | [rf-data/Personal_Assistant#116](https://github.com/rf-data/Personal_Assistant/issues/116) |
| C28 | [rf-data/Personal_Assistant#102](https://github.com/rf-data/Personal_Assistant/issues/102) |
| C29 | [rf-data/Personal_Assistant#103](https://github.com/rf-data/Personal_Assistant/issues/103) |
| C30 | [rf-data/Personal_Assistant#104](https://github.com/rf-data/Personal_Assistant/issues/104) |
| C31 | [rf-data/Personal_Assistant#105](https://github.com/rf-data/Personal_Assistant/issues/105) |
| C32 | [rf-data/Personal_Assistant#106](https://github.com/rf-data/Personal_Assistant/issues/106) |
| PERSONAL-PYREPO | [rf-data/Personal_Assistant#117](https://github.com/rf-data/Personal_Assistant/issues/117) |

## Ansichten und tatsächliche Filterprüfung

- [Roadmap #4](https://github.com/users/rf-data/projects/1/views/4): vorhandene
  Roadmap erhalten; native Milestones existieren. Erweiterung sichtbarer Spalten
  endete mit API-Exit 1; erneuter Read beweist unveränderte Ansicht. Keine
  erfolgreiche Änderung oder konkrete serverseitige Fehlerursache behauptet.
- [Priority board #2](https://github.com/users/rf-data/projects/1/views/2): bestehende
  Prioritygruppierung und Statusspalten erhalten, Filter `status:Backlog,Ready`,
  **33 Items** tatsächlich über die API gefunden.
- [Active Work #6](https://github.com/users/rf-data/projects/1/views/6): In progress /
  In review, **0 Items**. Das ist der tatsächliche Projectbestand; C24-06-A wird
  nicht ersatzweise eingetragen oder verborgen als abgeschlossen ausgegeben.
- [Blocked / Requires Decision #7](https://github.com/users/rf-data/projects/1/views/7):
  Requires decision / Real acceptance pending / Production acceptance pending,
  **17 Items**.
- [Technical Delivery / Real Acceptance Pending #8](https://github.com/users/rf-data/projects/1/views/8):
  Technical delivery only / Real acceptance pending / Production acceptance pending,
  **23 Items**; Status und Acceptance sind nebeneinander sichtbar.

Die vier Filter wurden nicht nur gespeichert: tatsächliche `items(query:...)`-
Ergebnisse stimmen jeweils exakt mit unabhängig aus allen Feldwerten bestimmten
Itemmengen überein. Neue Tabellen zeigen Title, Repository, Status, Priority,
Workstream, Acceptance, Milestone, Parent issue und Assignees. Serverreihenfolge
der Spalten wurde als Menge geprüft. Bestehende Views #1/#3/#4/#5 unverändert;
kein Browser-/Darstellungsreview behauptet.

Offener UI-Schritt für Roadmap #4: als berechtigter Betreiber Viewkonfiguration
öffnen; soweit das Layout unterstützt Milestone, Priority, Workstream und
Acceptance als sichtbare Felder hinzufügen, vorhandenes Layout/Filter erhalten,
speichern und gegen die echten Milestonegruppen prüfen. Keine Start-/Zieltermine
erfinden. Für Prioritäts-/Abnahmedetails stehen die drei getesteten Tabellen bereit.

## Automatisierungen und Sicherheit

Vor erster Anlage hat der Betreiber die bislang nicht auslesbaren Einstellungen
bestätigt: Item added → Backlog, Auto-close issue bei Done, Auto-addfilter
`is:issue,pr is:open`. `enabled=false` wurde vor jeder damaligen Issueanlage und
im Endzustand live gelesen. Die frühere Zuschreibung einer Deaktivierung an den
Betreiber ist **nicht bestätigt** und wird mit der neuesten Betreiberangabe
korrigiert. Der Agent hat keine Workflowkonfiguration verändert oder reaktiviert.
Die damals offene Repositoryauswahl ist inzwischen ausdrücklich bestätigt:
Backend ausgewählt, UI nicht ausgewählt. Eine UI-Erweiterung ist noch nicht
ausgeführt; der untenstehende Fortsetzungsvermerk trennt Bestätigung und Änderung.

Vor jedem Create alle passenden Repository-Issues/PRs und Project-Items erneut
abgeglichen; nach Anlage Project erneut gelesen. Sechs automatisch aufgenommene
Issue-Items wiederverwendet, 21 nach verifiziertem Fehlen manuell aufgenommen.
APIverzögerungen und einzelne fehlgeschlagene Writes führten zu begrenzten
Readbacks und Wiederaufnahme anhand vorhandener Identitäten, nicht zu blinden
Createwiederholungen. Endbestand beweist: 27 eindeutige neue Issues, ein Item
je kanonischem Ziel, keine Duplikate.

Die zusätzlichen Statusoptionen Priority/Workstream/Target milestone werden von
keinem Item verwendet, aber weiterhin erhalten: andere Workflowzielkonfigurationen
sind über den verfügbaren Vertrag nicht vollständig lesbar. Konkreter Betreiber-
Schritt: alle Workflowtrigger/-ziele und gespeicherten Viewfilter in der Oberfläche
prüfen, dann erst die drei Optionen einzeln zur Entfernung freigeben. Keine
Optionen aufgrund ihrer Namen automatisch löschen. Auto-close wird bis zur ausdrücklichen Betreiberbestätigung vorsorglich als
aktiv behandelt; keine schließungsgefährlichen Statusaktionen. Der API-Befund
`enabled=false` ist eine Beobachtung, keine bestätigte Betreiberaktion.
Done ist keine Realabnahme.

Acceptance-Endbestand: **16 Technical delivery only, vier Real acceptance pending,
drei Production acceptance pending, zehn Requires decision, elf Planned,
zwölf unbelegt**. Alle 27 neuen Issues bleiben offen/Backlog. D06/D07/C23-06/
C24-05/C26 sind nicht durch technische PRabschlüsse freigegeben. Keine Realmaterial-,
Produktiv-, Datenbank-, Mail-, Embedding- oder Qdrantaktion durchgeführt.

## Tatsächliche Validierung und offener Lifecycle

Vollständige paginierte Issue-/PR-/Milestonelisten beider Repositories sowie
Project-Items einschließlich archivierter Zustände, Feldwerte, Optionen, Views
und Workflows gelesen. Alle letzten Verbindungen ohne weitere Seite; Item-/
Feld-/Relationgrenzen geprüft. 45 IDs, Aliaspaare, 27 Original-Issueidentitäten,
14 Parent- und 35 Blocked-by-Kanten, 42 Milestonezuordnungen, offene Zustände,
private Projectidentität und Scope-/Abnahmetrennung geprüft. Keine neue Laufzeit,
keine Anwendungs-/Ruff-/Pytestabnahme erforderlich oder behauptet.

[Sourceplan](issue_plan.v1.json) SHA256
`629b1c3471bc8654908bb99fbe5e1bc277edfb28272e1801bc8a8f065831580d` unverändert.
JSONinvarianten, lokale Markdownziele, UTF-8/LF und Whitespace geprüft.
PRs #72/#88/#89: Titel, Körper, Zustand, Draftflag, Head-/Base-SHAs und nativer
Milestone unverändert; lediglich die ausdrücklich vorgesehenen Projectmetadaten
für #72 ergänzt. Übrige Altitems und ihre Statuswerte unverändert erhalten.
16 bereits gemergte technische PRs erhielten bewusst ausschließlich einen
nativen Milestone. Keine alten PRs gemergt/geschlossen oder Commits umgeschrieben.

Nur zwei neue Dokumente unter `docs/planning/`, eigener Remote-Dokumentationsbranch
`docs/pm03-project-operationalization`, kein neuer lokaler Branch/Worktree.
Der nachfolgende MAINT-04-Auftrag verlangt, keine PRs zu mergen: Dokumente daher
über regulären PR vorlegen; Integration in master und abschließender eigener
Branchabbau bleiben bis Review/Merge offen. Nie einen offenen PR als integrierte
Dokumentation ausgeben. Alle alten PM-/MAINT-/Agentenbranches, Registrierungen,
Primärcheckouts, Stashes und private Inhalte bleiben erhalten.

Der Zählstand 56 gilt unmittelbar vor Anlage eigener Dokumentations-PRs. Deren
mögliche automatische Projectaufnahme ist keine neue Planrepräsentation; nach
Veröffentlichung separat lesen und im PR/Abschluss ausweisen. Private Ablauf-
belege bleiben außerhalb des Repositories; keine Credentials, Volltexte oder
privaten Hostroots im Maschinenreport.

## Rücklesen nach Veröffentlichung der Dokumentations-PRs

[PM-03 #118](https://github.com/rf-data/Personal_Assistant/pull/118) und
[MAINT-04 #119](https://github.com/rf-data/Personal_Assistant/pull/119) wurden vom
bestehenden Workflow automatisch aufgenommen: aktueller Bestand **58 Items**,
31 PRs / 27 Issues, **23 Done / 35 Backlog**. Beide neuen Dokumentationsitems sind
Backlog/offene PRs; sie ersetzen keine Plan-ID und sind keine Duplikate der
kanonischen Aufgaben. Die 56 zuvor geprüften Items und ihre Feldwerte sind
unverändert. Alle 27 neuen Issues bleiben offen; Auto-close weiterhin `false`.

Beide PRs sind ungemergt. Dokumente sind damit reviewbar, aber noch nicht in
master integriert. Beide ausschließlich auftragseigenen Remotebranches bleiben
aus genau diesem Grund erhalten. Kein lokaler Arbeitsbranch/Worktree wurde erzeugt
oder entfernt. Frühere Bestandsrefs werden davon nicht berührt.

## Fortsetzung nach abschließender Betreiberangabe

Die aktuelle Betreiberbestätigung schließt die Konfigurationslücke: Backend
`rf-data/Personal_Assistant` ist bei Auto-add ausgewählt, UI
`rf-data/personal-assistant-ui` nicht; Filter `is:issue,pr is:open`, Item added
→ Backlog und Auto-close bei Done. **Eine Deaktivierung von Auto-close wurde
nicht ausdrücklich bestätigt.** Die API liefert erneut `enabled=false`; diese
Beobachtung bleibt von der menschlichen Bestätigung getrennt. Bis zu deren
Vorliegen gelten potenziell Issue-schließende Statusaktionen als gesperrt.
Keine Auto-close-Änderung, keine neue Statusmutation und kein Issueabschluss.

Neuer vollständiger Liveabgleich: **58 Items**, davon **50 Backend / acht UI**,
31 PRs / 27 Issues, weiterhin 23 Done / 35 Backlog. Beide Repositories sind
bereits nativ mit dem Project verknüpft. Alle ursprünglichen 28 Items behalten
Identität/Status; auch die Feldzuordnungen aller späteren 58 Items sind identisch.
44 der 45 Plan-IDs bleiben an ihre verifizierten Ziele gebunden. C24-06-A besitzt
weiterhin keinen veröffentlichten Backend-PR; kein Ersatzissue erzeugt.
Die vollständigen paginierten Issue-/PRlisten beider Repositories enthalten alle
27 vorgesehenen offenen Issues jeweils genau einmal. **Null fehlende Issues,
null neue Issues oder Items, keine erneute Abarbeitung alter Create-Skripte.**

### UI-Auto-add: konkrete noch auszuführende Konfiguration

**Historischer Vorschlag, inzwischen durch bestätigtes Tariflimit und den unten
dokumentierten manuellen Betreibervertrag ersetzt. Keine zweite Regel voraussetzen.**

Der aktuelle öffentliche GraphQL-Vertrag stellt für Projectworkflows nur die
Mutation `deleteProjectV2Workflow` bereit, keine Create-/Update-Mutation.
`ProjectV2Workflow` bietet lediglich Metadaten einschließlich `enabled`, keine
Repository-/Filterkonfiguration. Es wurde keine Löschmutation oder inoffizielle
Session-/Webroute verwendet. Repositoryverknüpfung allein aktiviert kein Auto-add.

GitHub dokumentiert eine separate Auto-add-Regel pro zusätzlichem Repository;
Duplikate sind tarifabhängig begrenzt. Aktivierung übernimmt bestehende passende
Items nicht rückwirkend. [GitHub: Auto-add konfigurieren und duplizieren](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically).
Der Kontoplan ist über die verfügbare APIantwort nicht bestätigt (`plan_name=null`);
eine freie zweite Regel wird daher nicht behauptet.

Verbleibender Betreiberablauf in Project #1 → Workflows:

1. Die bestehende Backend-Auto-add-Regel erhalten. Bei verfügbarem Tarifkontingent
   über deren Menü **Duplicate workflow** eine UI-Regel anlegen.
2. Für die Kopie ausschließlich `rf-data/personal-assistant-ui` und
   `is:issue,pr is:open` wählen, **Save and turn on workflow** ausführen.
   Item added → Backlog und Auto-close unverändert lassen.
3. Gespeicherten Regelname und Repository-/Filterbindung bestätigen; falls GitHub
   das Duplikat wegen des Tariflimits ablehnt, genau diese Blockade dokumentieren.
   Kein Tarifwechsel, keine Backend-Ersetzung und kein Testissue automatisch anlegen.
4. Danach Workflows und Project erneut vollständig lesen, neue Auto-add-Einträge
   gegen vorhandene URLs/Node-IDs prüfen. Bestehende acht UI-Items bleiben erhalten;
   keine Doppelanlage. Für jeden später tatsächlich fehlenden Auftrag bleibt die
   Prüfung vor Create und der anschließende Liveabgleich verpflichtend.

Der notwendige Oberflächenschritt ist angefragt, **nicht ausgeführt oder bestätigt**.
Es entstand keine Ersatzautomatisierung, kein Actionsworkflow und kein neues Secret.
Ein vollständiger Auto-add-Erfolg für beide Repositories wird nicht behauptet.
[Öffentlicher Projects-Vertrag](https://docs.github.com/en/graphql/reference/projects)
und die live geprüfte Schemastruktur begrenzen die verfügbaren APIaktionen.

### Prüfung dieses Fortsetzungsumfangs

Project-/Item-/Feld-/Workflow-Pagination und vollständige Repository-Issue-/PRlisten
geprüft; keine offene Seite. Alle Quell-IDs, Aliasbindungen, Itemidentitäten,
Status-/Metadatenwerte und eindeutigen Issueziele validiert. JSONstruktur,
UTF-8/LF, lokale Verweise und Whitespace geprüft. Keine Runtimeänderung oder
Anwendungs-/Ruff-/Pytestabnahme. Nur die beiden vorhandenen Dokumente in
[PR #118](https://github.com/rf-data/Personal_Assistant/pull/118) werden aktualisiert;
keine neue PR-/Branch-/Worktreeanlage. Masterintegration wartet weiterhin auf
regulären Review/Merge, der eigene offene Branch bleibt erhalten.

## Manuelle UI-Aufnahme nach bestätigtem Tariflimit

19.10.2026. Der Betreiber bestätigt, dass GitHub eine zweite Auto-add-Regel wegen
des Tariflimits verhindert. Die bestehende Backend-Regel und Auto-close bleiben
unverändert. Damit ist die frühere offene Tarifentscheidung geklärt; es wird
**keine zweite Automatisierung** vorausgesetzt oder aufgebaut.

Project #1 dient weiterhin beiden Repositories. Der bestätigte offene Filter
`is:issue,pr is:open` gilt als Auswahl für den manuellen UI-Abgleich. Sämtliche
UI-Issues und -PRs wurden einschließlich geschlossener Einträge paginiert gelesen:
**sieben offene Issues, null offene PRs**, acht historische PRs im Inventar.
Alle sieben offenen Issues (#9–#15) sind bereits **jeweils genau einmal** im
Project enthalten. Der vorhandene gemergte UI-PR #7 bleibt erhalten. Eine pauschale
Nachaufnahme historischer geschlossener PRs gehört nicht zum offenen Filter.

Ausgeführter Abgleich: vor jeder möglichen Anlage vollständigen Projectbestand
mit den exakten UI-URLs/Node-IDs vergleichen; vorhandene Einträge wiederverwenden.
Ergebnis **sieben wiederverwendet, null `item-add`-Aufrufe, null Neuanlagen**.
Es war kein Schreibaufruf erforderlich. Ein zweiter vollständiger Project- und
UI-Read bestätigt erneut jedes offene Ziel genau einmal und unveränderte
Quellzustände/-texte. Die Felder sämtlicher vorher vorhandenen 58 Items sind
identisch. Keine Statusmutation, kein Issueabschluss und keine Workflowänderung.

### Verbindlicher manueller Ablauf für spätere fehlende UI-Ziele

1. Vollständige offene UI-Issue-/PRliste und Project-Itemliste lesen; Pagination
   einschließlich archivierter Items vollständig prüfen. Bestehende kanonische
   URL/Node-ID bedeutet Wiederverwendung. Duplikate oder unklarer Zustand stoppen.
2. Nur bei tatsächlich fehlendem offenem Ziel dessen Zustand und Identität sowie
   den Projectbestand unmittelbar vorher erneut lesen. `PM03_UI_URL` bezeichnet
   ausschließlich die dabei verifizierte exakte URL, keine Scanwurzel oder Liste.
3. Genau einen manuellen Aufruf ausführen:

   ```sh
   gh project item-add 1 --owner rf-data --url "$PM03_UI_URL" --format json
   ```

4. Project danach vollständig erneut lesen: exakte Zielidentität genau einmal,
   serverseitige Item-ID und Backlog aus Item added prüfen; keine Statusänderung
   als Ersatz durchführen. Bei Timeout/Fehler zuerst lesen, nie blind erneut anlegen.
5. Bei Wiederholung dieselben vorhandenen Einträge wiederverwenden. Neue Issues
   oder PRs werden durch dieses Verfahren nicht erzeugt. Keine Hintergrundaufgabe,
   kein Zeitplan, keine GitHub-Actions-Datei und kein neues Secret anlegen.

Auto-close wird vorsorglich als aktiv behandelt, solange seine Deaktivierung
nicht ausdrücklich bestätigt ist. Der APIbefund bleibt getrennt davon
`enabled=false`; der Agent ändert ihn nicht. D06/D07/C23-06/C24-05/C26 bleiben
offen, keine Realabnahme wird durch eine technische Lieferung ersetzt.

### Dokumentintegration und tatsächliche Prüfung

PR #118 ist nach live gelesenem Zustand gemergt; die beiden maßgeblichen Berichte
wurden aus dem tatsächlichen aktuellen master gelesen. Der manuelle Nachtrag
ändert ausschließlich diese bestehenden Dateien. Kein neuer Modell-/Reporttyp,
keine Runtime-/Konfigurationsänderung und kein zusätzlicher lokaler Worktree.
Der eigene kleine Folge-PR bleibt bis zum regulären Review/Merge offen; sein
Branch wird vorher nicht entfernt. Andere Branches/Worktrees/PRs bleiben geschützt.

Geprüft: vollständige Repository-/Projectpagination, sieben eindeutige offene
UI-Ziele, Wiederholungsabgleich, unveränderte Item-/Sourcefelder und Workflows,
JSONinvarianten, UTF-8/LF, lokale Links und Whitespace. Keine Anwendungs-, Ruff-,
Pytest- oder Automatisierungsabnahme behauptet; ausschließlich bestehende
Planungsdokumentation und ein einmaliger kontrollierter CLI-Abgleich.

Nach Veröffentlichung von [Folge-PR #120](https://github.com/rf-data/Personal_Assistant/pull/120):
**59 Project-Items**. Die bestehende Backend-Auto-add-Regel nahm
den Dokumentations-PR einmal als Backlog auf. Diese automatische Aufnahme ist
kein manueller UI-Zugang.
Alle vorherigen 58 Itemfelder, alle 27 offenen Issuezustände und sämtliche
Workflow-Metadaten sind unverändert. Kein Merge oder Branchabbau ausgeführt;
der offene Folge-PR hält seinen eigenen Branch bis zur verifizierten Integration.
