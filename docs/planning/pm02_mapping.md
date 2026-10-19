# PM-02 – Soll-Ist-Zuordnung der 45 Planzeilen

19.10.2026. Führender Plan: [issue_plan.v1.json](issue_plan.v1.json), Revision
`pm01-2026-10-19`. [Maschinenlesbarer Abgleich](pm02_reconciliation.v1.json),
[manueller Ausführungsweg](pm02_project_execution.md), [Validierung](pm02_validation.md).

**Teilweise abgeschlossen / operativ blockiert.** Alle Project-Item-IDs, aktuellen
Feldwerte und Projectrechte sind `not_verified`, nicht leer oder bereits erledigt.
Die nachstehenden Ziele sind Vorschläge gegen tatsächliche PR-Belege; keine
Zuordnung zu einem beobachteten Projectitem. Keine Issue-/Projectmutation.

45 Plan-IDs → **43 eindeutige vorgeschlagene Repräsentationen**. 17 Zeilen
referenzieren 15 bestehende PRs; 27 Zeilen sind **bedingte** Issuekandidaten (davon
zehn Meilensteinparents), eine Zeile wartet auf den tatsächlichen C24-06-A-PR.
27 ist keine Anlagequote: vorhandene Issues/Draftitems/äquivalente Parentstruktur
zuerst vollständig lesen und wiederverwenden; bei Gleichwertigkeit entfällt eine
Anlage. Es werden nicht automatisch 45 Issues erzeugt.

## Vollständige Abgleichstabelle

Ein vorhandener PR ist nur die begrenzte technische oder verbleibende Gate-
Repräsentation. Bei 02/03/04 kann der technische PR deshalb vorgeschlagen Done
sein, während die ursprüngliche Planzeile Backlog bleibt. Der jeweils offene
Child-/Realabnahmeumfang bleibt ausdrücklich separat; das schließt keinen Parent.
Bestätigte bestehende Projectwerte niemals allein wegen dieser Vorschläge ersetzen.

| Plan-ID | Repository | Vorhandener PR / vorgeschlagenes Ziel | Item-ID / Iststatus | Planstatus → Vorschlag | Aktion |
| --- | --- | --- | --- | --- | --- |
| C23 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C24 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C25 | rf-data/personal-assistant-ui | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C27 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C28 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C29 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C30 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C31 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C32 | rf-data/Personal_Assistant | milestone_parent_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C23-01 | rf-data/Personal_Assistant | [75](https://github.com/rf-data/Personal_Assistant/pull/75) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-02 | rf-data/Personal_Assistant | [76](https://github.com/rf-data/Personal_Assistant/pull/76) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-03 | rf-data/Personal_Assistant | [72](https://github.com/rf-data/Personal_Assistant/pull/72) | not_verified | Backlog → Backlog | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-04 | rf-data/Personal_Assistant | [80](https://github.com/rf-data/Personal_Assistant/pull/80) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-05 | rf-data/Personal_Assistant | [81](https://github.com/rf-data/Personal_Assistant/pull/81) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-06 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C24-01 | rf-data/Personal_Assistant | [83](https://github.com/rf-data/Personal_Assistant/pull/83) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-02 | rf-data/Personal_Assistant | [84](https://github.com/rf-data/Personal_Assistant/pull/84) | not_verified | Backlog → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-03 | rf-data/Personal_Assistant | [85](https://github.com/rf-data/Personal_Assistant/pull/85) | not_verified | Backlog → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-04 | rf-data/Personal_Assistant | [86](https://github.com/rf-data/Personal_Assistant/pull/86) | not_verified | Backlog → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-05 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C25-01 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C25-02 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C25-03 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C25-04 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-01 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-02 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-03 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-04 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-05 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-06 | rf-data/personal-assistant-ui | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C26-07 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C23-02A | rf-data/Personal_Assistant | [76](https://github.com/rf-data/Personal_Assistant/pull/76) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-02B | rf-data/Personal_Assistant | [77](https://github.com/rf-data/Personal_Assistant/pull/77) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C23-02C | rf-data/Personal_Assistant | [78](https://github.com/rf-data/Personal_Assistant/pull/78) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-05-A | rf-data/Personal_Assistant | [87](https://github.com/rf-data/Personal_Assistant/pull/87) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-05-B1 | rf-data/Personal_Assistant | [90](https://github.com/rf-data/Personal_Assistant/pull/90) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-05-B2 | rf-data/personal-assistant-ui | [7](https://github.com/rf-data/personal-assistant-ui/pull/7) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-05-C2 | rf-data/Personal_Assistant | [91](https://github.com/rf-data/Personal_Assistant/pull/91) | not_verified | Done → Done | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C24-06-A | rf-data/Personal_Assistant | active_task_pending_published_pr | not_verified | In Progress → In Progress | await_actual_task_pr_no_parallel_issue |
| C24-03-B | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C24-02-C | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| C24-04-B | rf-data/Personal_Assistant | [72](https://github.com/rf-data/Personal_Assistant/pull/72) | not_verified | Backlog → Backlog | reuse_existing_pr_item_if_present_else_add_same_pr_after_gate |
| C28-01 | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |
| PERSONAL-PYREPO | rf-data/Personal_Assistant | remaining_scope_issue | not_verified | Backlog → Backlog | reuse_matching_issue_or_project_item_else_create_scoped_issue_after_gate |

## Absichtliche Aliaszuordnungen ohne doppelte Projectitems

- C23-02 und C23-02A verwenden dasselbe technische #76-Item. #77/#78 bleiben
  eigenständige belegte Childlieferungen. Kein zweiter Implementierungsauftrag
  für den bereits integrierten Core und keine pauschale Realabnahme des Bundles.
- C23-03-Restgate und C24-04-B verwenden dasselbe bestehende #72-Pilotitem.
  #79 belegt Reimport/Inventar; der historische D06-/Instanz-/Modellentscheid
  ist dadurch nicht umgesetzt. Keine neue konkurrierende Pilotimplementierung.

## Abgrenzungen und Abhängigkeiten

C23-06/C24-05 bilden ausschließlich die verbleibende reale Abnahme ab; die
Frameworks #82/#87, B1/#90, UI-B2/#7 und C2/#91 werden nicht erneut umgesetzt.
C24-02-C sind Indexjobs, C24-03-B Search-HTTP/DTOs. C25 verwendet vorhandene
B2-Security/Client/Renderer; Review-UI ist keine fertige allgemeine Search UI.
C24-06-A bleibt laufend ohne paralleles Issue/Implementierungsauftrag.

D06 gilt für das historische SRT-Binding; D07 für tatsächliche Sourcefreigaben,
Bundles, private Roots und unabhängig bestätigtes Gold. C26 braucht eigene
Betreiber-/Host-/Betriebsentscheidungen. Keine Done-/Produktivfreigabe aus Merge.
#88 bleibt Architekturhistorie, #89-Metadaten sind in #91 erhalten. Keine Drafts
schließen/mergen oder deren bestätigte Projectwerte pauschal ändern.

PyRepo ist `human_only`, optional und ohne harte C27-Abhängigkeit. C32 enthält
Real Python und getrennte Move-/Processingzustände sowie UID-/Idempotenz-/
COPY/MOVE-/EXPUNGE-Grenzen. arXiv ergänzt denselben Discoveryvertrag mit Versionen
und Metadaten; keine Source-Promotion oder Jobaktivierung.

Die JSONdatei erhält zu jeder Plan-ID alle Originalabhängigkeiten, vorgeschlagene
Felder, verifizierte PR-SHAs/Merges, genau einen Repräsentationsschlüssel,
`performed_actions=[]` und den nicht verifizierten Itemstatus. Sie ist ein
Abgleichssnapshot, keine neue autoritative Planungsdatenbank.
