# PM-02 – konkreter manueller Weg in GitHub Project #1

19.10.2026. **Nicht ausgeführt.** [Abgleich](pm02_mapping.md),
[JSON mit tatsächlichen Aktionen](pm02_reconciliation.v1.json),
[Validierungsbericht](pm02_validation.md).

Diese Anleitung nutzt ausschließlich das bestehende
[User-Project #1](https://github.com/users/rf-data/projects/1). Sie ist der explizit
beauftragte Fortsetzungsweg bei fehlender Connectorfähigkeit, kein zweites Board,
keine Planungsdatenbank und kein automatischer Mutationsrunner. Eine erneute
allgemeine PM-01-/PM-02-Planfreigabe ist nicht nötig; vor Änderungen bleiben
Identität, vollständiger Bestand und erforderliche Rechte nachzuweisen.

## 1. Bestehendes Project und Grenzen der Sichtbarkeit prüfen

1. Mit dem bereits berechtigten GitHub-Account Project #1 öffnen. Owner `rf-data`,
   Nummer 1, tatsächlichen Titel und URL lesen. Keine Neuanlage oder Umbenennung,
   nur weil der Titel vom Soll „Personal Assistant – Development“ abweicht.
2. In den Projecteinstellungen vorhandene Zugriffsrollen und die eigene effektive
   Schreibberechtigung prüfen. Repositoryrechte separat kontrollieren. Repo-Admin
   ist kein Nachweis für Projectzugriff. Keine neuen Tokens oder Scopeausweitung.
3. Bestehende Views/Filter und deren Feldspalten erfassen. Eine ungefilterte
   Ansicht verwenden, offene/geschlossene und archivierte Items sowie Draftitems
   kontrollieren. Alle Seiten bzw. nachgeladenen Items lesen; sichtbare erste
   Bildschirmzeilen sind kein vollständiges Inventar. Unzugängliche/redigierte
   Items und Zählgrenzen dokumentieren. Bei unklarer Sichtbarkeit weiter stoppen.
4. Felder und tatsächliche Optionen erfassen: Status, Priority, Workstream,
   Target/Milestone, Repository/Assignee/Labels sowie fachliche Zusatzfelder.
   Bestehende fachlich bestätigte Werte erhalten. IDs nicht aus Anzeigenamen ableiten.
5. Vor Itemaufnahme vorhandene Workflows lesen, insbesondere Item-added,
   PR-merged/Issue-closed→Done, Status→Issue-close sowie Auto-Add/Auto-Archive.
   Keinen Workflow blind aktivieren oder deaktivieren. Bei einer Regel, die den
   geplanten manuellen Parent-/Realabnahmestatus überschreiben würde, zunächst
   deren konkrete Wirkung mit dem zuständigen Owner klären.

GitHub beschreibt die möglichen Status-/Close-Automatisierungen und deren
Project-Menü unter [Workflows](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations).
Dies beschreibt Produktmöglichkeiten, **keinen beobachteten Workflow von Project #1**.

Node-ID für einen späteren APIweg über einen **bereits autorisierten vorhandenen**
Project-APIzugang lesen, niemals die Zahl 1 als Node-ID einsetzen. Der vorliegende
Connector blockiert sowohl GraphQL als auch den REST-ProjectsV2-Leseweg. Ein
UI-Nachweis von Owner/Nummer/URL/Titel/Rechten ist als solcher zu dokumentieren;
eine dort nicht sichtbare globale Node-ID bleibt `not_verified`. Keine Node-ID
erraten, keinen APIerfolg behaupten. Für manuelle Aktionen muss die Identität
in der UI tatsächlich belegt sein; unbekannte Items/Rechte sperren weiterhin.
[Offizieller API-/Sichtbarkeitsvertrag](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects).

## 2. Vollständigen Bestand mit den 45 Plan-IDs abgleichen

Vor jeder Anlage beide Repository-Issuelisten einschließlich geschlossener Issues,
Labels und Milestones neu lesen. Die PM-02-Aufnahme enthält null eigenständige
Issues, ist aber keine zukünftige Garantie. Project-Draftitems existieren eventuell
bereits, obwohl keine Repo-Issues existieren. Keine neuen Issues allein aus dem
REST-Zählwert erzeugen.

Pro Plan-ID die [Abgleichstabelle](pm02_mapping.md) verwenden:

- Nach Plan-ID, Repository, tatsächlichem Scope und vorhandener Issue-/PR-URL suchen.
  Ein ähnlicher Titel reicht weder für Gleichsetzung noch für eine neue Dublette.
- Tatsächliche Issue-/PR-URL, Projectitem-Link/ID, Iststatus und bestätigte Werte
  erfassen. Erst nach Prüfung den `not_verified`-Platzhalter bewusst ersetzen.
- Äquivalente Parent-Issues, Drafts oder bereits sinnvolle Meilensteinstruktur
  wiederverwenden. Fehlt wirklich eine Repräsentation, den passenden verbleibenden
  Scope wählen. Zehn Parentkandidaten sind keine Verpflichtung, zehn vorhandene
  gleichwertige Gruppen nochmals als Issues anzulegen.
- Die zwei bewussten Aliaspaare nur einmal aufnehmen: C23-02/C23-02A → #76 und
  C23-03-Restgate/C24-04-B → #72. Beide Plan-IDs am selben überprüften Item vermerken.
  Alle unterstützenden PRs aus dem JSON bleiben Evidence, keine zusätzlichen
  gleichwertigen Aufgaben.

Es gibt 43 vorgeschlagene Zielrepräsentationen für 45 Plan-IDs: 15 vorhandene
PR-Ziele, 27 **bedingte** Issuekandidaten und einen wartenden aktiven Auftrag.
Jeder Kandidat kann durch einen vorhandenen exakten Treffer entfallen. Die Zahlen
sind eine Prüfliste, keine Anlageschleife und kein Erfolgsnachweis.

## 3. Vorhandene PRs wiederverwenden, technische Grenzen erhalten

Die Tabelle referenziert vorhandene PRs für bereits gelieferte Teilumfänge. #87,
#90, UI #7 und #91 sind integriert. Deren technische Items dürfen nur in diesem
begrenzten Scope Done sein. Ein Parent/Realrelease wird dadurch nicht freigegeben.

Für C24-02/03/04 gelten besondere Grenzen: #84 belegt Projektion, #85 FTS5/interne
Suche, #86 einen gated Vektoradapter mit Fake-Nachweis. Der jeweilige technische
PR-Vorschlag Done unterscheidet sich deshalb vom Source-Planstatus Backlog.
Indexjobs bleiben C24-02-C, HTTPsearch C24-03-B, echter optionaler Pilot C24-04-B.
Diese offenen Anteile nicht auf dem technischen PR verstecken oder als erledigt
hochziehen. Einen bereits bestätigten fremden Projectstatus nicht pauschal ändern.

Einen fehlenden PR-Eintrag nach vollständiger Dublettenprüfung über dessen echte
URL in die unterste „Add item“-Zeile aufnehmen; alternativ über die Projectauswahl
in der PR-Seitenleiste. Nach Hinzufügen den Eintrag neu öffnen und URL, Repository
und Head/Merge prüfen. GitHub dokumentiert diese Wege unter
[Items hinzufügen](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project).
Nach Timeout zuerst erneut nach derselben URL suchen, nicht blind wiederholen.

#72/#88/#89 bleiben offen und ungemergt. Bei #88/#89 gibt es keinen erneuten
Implementierungsauftrag: Architekturhistorie bzw. in #91 bereits erhaltene
Metadaten, reale Source-/Goldgates separat. #72 ist bestehender optionaler Pilot
mit D06-/Instanz-/Modell-/Transportgrenzen. Keine Branch-/PRstatusänderung.
C24-06-A bleibt ein aktiver separater Auftrag: erst den tatsächlich veröffentlichten
PR zuordnen, kein paralleles Issue oder neue Implementierung erzeugen und keine
Worktrees/Artefakte/Tests verändern.

## 4. Tatsächlich fehlende Issues kontrolliert anlegen

Nur nach erfolgreicher Phase A und erneuter Einzelfallsuche:

1. Wirklich fehlende Parentrepräsentationen zuerst festlegen; sinnvolle bestehende
   Projectgruppen oder Parent-Issues erhalten. Das Zielrepository steht pro Zeile
   im führenden Plan, insbesondere UI-C25 und UI-C26-Kinder nicht ins Backend kopieren.
2. In der betreffenden Repository-Issueansicht das vorhandene passende Template
   verwenden. Titel mit stabiler `[Plan-ID]`, Body mit exakt verbleibendem Scope,
   Akzeptanz, Abhängigkeiten, Priority/Target, Ownerfrage und echten PR-Belegen.
   Keine privaten Originaltexte, Hostpfade oder Tokens. Keine automatischen
   `Closes`-Referenzen auf Realabnahme-/Meilensteinparents in Implementierungs-PRs.
3. `C23-06` bzw. `C24-05` nur als offene reale Abnahme führen: D07, vollständige
   berechtigte Bundles, exakte Roots, menschliches Gold/Pool und Approver fehlen.
   D06 betrifft das historische SRT-Binding. Keine synthetische Metrik als Realwert.
4. Neue URL sofort im Abgleich erfassen, dann genau dieses Issue einmal in
   Project #1 aufnehmen. Bei Savefehler/Timeout erst nach Plan-ID/URL suchen.
5. Native Unteraufgaben nur mit passenden vorhandenen Rechten und ohne Ersetzen
   bestehender Beziehungen zuordnen. Sonst eindeutige bidirektionale URLbezüge
   zwischen Parent und Kind verwenden. Abhängigkeiten aus `depends_on` übernehmen;
   ein Meilensteinlabel allein stellt keine Abhängigkeit her.

PyRepo Inspector ist ein **persönliches optionales CS50P-Projekt**: Body mit
`human_only`, keine Codex-Implementierung oder automatischen Codex-Aufträge.
Account vor Assignment prüfen; vorhandene Labelkonventionen nutzen, eventuell
`owner:human`, `cs50p`, `personal-project`, `optional` gezielt ergänzen. Keine
Hard-Abhängigkeit von C27 und kein neues Repository/Programmcode.

C32 muss Real Python, Medium und autorisierte Newsletter samt eigenem explizit
konfiguriertem Zielordner, getrenntem Processing-/Movestatus, UID/Idempotenz und
Provider-COPY/MOVE-/EXPUNGE-Grenzen enthalten. Keine Mailaktion hier. arXiv ist
zusätzlicher Provider des gemeinsamen C28/C31-Discoveryvertrags mit IDs/Versionen
und Metadatenbindung; keine automatische Source-Promotion, PDFs oder Jobaktivierung.

## 5. Felder und vorgeschlagene Views

Bestehende äquivalente Felder/Optionen verwenden. Nur tatsächlich Fehlendes ergänzen:
Priority P0–P3, Workstream und C23–C32-Target sind Sollwerte, keine gelesenen Optionen.
Ein vorhandenes natives Milestonefeld nicht durch einen gleichwertigen Custom-Clone
verdoppeln. Unbekannte oder fachlich bestätigte Istwerte nicht aus einer Tabelle
überschreiben. Blocker/Abnahmestatus zunächst im Issuebody und vorhandenen passenden
Labels ausdrücken; kein zusätzliches Feld ohne Bedarf erfinden.

| Gewünschte Ansicht | Kontrollierte Einrichtung nach Inventar |
| --- | --- |
| Roadmap / Milestones | Bestehende passende Ansicht verwenden; nach tatsächlichem Target-/Milestonefeld gruppieren, keine erfundenen Termine |
| Aktive Arbeit | Tatsächliche aktive/In-Review-Werte filtern; C24-06-A aktiv, nicht Done |
| Backlog nach Priorität | Unbegonnene Aufgaben nach vorhandener Priority-Skala sortieren; Freigaben/Owner vor Ready klären |
| Blockierte Aufgaben | Bestehendes Blockerfeld/Label verwenden; D06/D07/C26-Entscheid und nächsten Schritt im Issuebody erhalten |
| Technisch geliefert / Realabnahme offen | Gelieferte technische Evidenz und offene Abnahme getrennt filtern; keine neue Gesamtnote oder automatische Releasefreigabe |

Vorhandene persönlich verantwortete Ansicht aus PM-01 erhalten, falls vorhanden;
PyRepo nach geeigneten persönlichen Labels sichtbar machen. Keine Views löschen.
Neue/geänderte Ansichten ausdrücklich speichern und erneut öffnen. Konkrete
Filter an die tatsächlichen Feld-/Optionsnamen anpassen; die obigen Namen sind
Vorschläge, keine ausgeführten Viewänderungen. GitHub beschreibt diese
[Projektansichten und Felder](https://docs.github.com/en/issues/planning-and-tracking-with-projects).

## 6. Abschlusskontrolle und idempotente Wiederaufnahme

Nach jedem kleinen Batch neu lesen und anhand des kanonischen Zielschlüssels
abgleichen, nicht anhand der Reihenfolge im Browser. Eine Plan-ID besitzt genau
eine dokumentierte Zielrepräsentation; mehrere Alias-IDs erzeugen kein zweites Item.
Bei jedem Folgelauf zuerst echte URL/Item-ID suchen. Bereits erfolgreiche Anlagen
wiederverwenden; kein destruktiver Rollback und keine Löschung zur Dublettenbereinigung.

Prüfen: vorhandene bestätigte Werte erhalten, alle vorgesehenen Repositories und
Abhängigkeiten korrekt, kein Parent fälschlich Done, keine echte Abnahme aus
synthetischen Belegen, keine unbeabsichtigte Workflowwirkung. Verborgene/unlesbare
Items und unvollständige Pagination bleiben `not_verified`; keine Nullzählung.

Nur nach tatsächlicher Durchführung Issue-/Item-/Feld-/View-IDs und Aktionszahlen
im Maschinenabgleich aktualisieren. Davor `performed_actions=[]`, Mutationen 0,
Bestandszahlen null und Verifikation `not_verified` erhalten. Der eigene spätere
Dokumentations-PR ist keine Issue-/Projectmutation und kein operativer Erfolg.
