# Schritt B – ausführbarer Verwaltungsplan, noch nicht freigegeben

Der Auftrag verlangt vor GitHub-Verwaltung ausdrücklich eine Planfreigabe.
**Dieser Plan wurde nicht ausgeführt.** Dokumentationsbranches/Review-PRs gehören
zu Schritt A; sie erlauben weder Issues/Projects noch produktive Ausführung.

Freigabegegenstand: die 32 Entwürfe in [issue_plan.v1.json](issue_plan.v1.json),
der [Projectvertrag](project.md), die Zuordnungen und die nachstehenden Regeln.
Keine bestehenden Issues/PRs schließen; keine Branches, Daten oder Dienste ändern.
GitHub-eigene Milestoneobjekte werden in dieser Stufe **nicht** angelegt: die zehn
Parents plus ein gemeinsames Target-milestone-Feld reichen für den Entwurf.
Eine zusätzliche Repo-Milestone-Struktur ist erst nach Bestandsprüfung zu entscheiden.

## 1. Read-only Preflight nach Freigabe

Ein vorhandenes, passend autorisiertes GitHub CLI verwenden. Es ist in der
aktuellen Umgebung nicht vorhanden; Installation oder neue Credentials sind
nicht Teil dieses Auftrags. Keine Tokens aus Projekt-Envdateien kopieren.
Beispielbefehle für die spätere passende Arbeitsumgebung:

```sh
gh auth status
gh api repos/rf-data/Personal_Assistant --jq '{default_branch,permissions}'
gh api repos/rf-data/personal-assistant-ui --jq '{default_branch,permissions}'
gh api --paginate 'repos/rf-data/Personal_Assistant/issues?state=all&per_page=100'
gh api --paginate 'repos/rf-data/personal-assistant-ui/issues?state=all&per_page=100'
gh api --paginate 'repos/rf-data/Personal_Assistant/milestones?state=all&per_page=100'
gh api --paginate 'repos/rf-data/personal-assistant-ui/milestones?state=all&per_page=100'
gh project list --owner rf-data --limit 100 --format json
gh project list --owner rf-data --closed --limit 100 --format json
```

Wenn ein Limit weitere Ergebnisse verdeckt, vollständig paginieren. Bei fehlendem
Projectzugriff stoppen und diese Teilaktion als blockiert ausweisen, nicht ein
Ersatzboard anlegen. Repo- und Projectberechtigungen getrennt prüfen; keine
automatische `gh auth refresh`-/Scopeausweitung.

Alle offenen **und geschlossenen** eigenständigen Issues abgleichen; PRs im
Issue-Endpunkt herausfiltern. Nach stabiler Plan-ID, Titel und inhaltlicher
Akzeptanz suchen. Pro Schlüssel entscheiden: wiederverwenden, genehmigt aktualisieren,
neu anlegen oder zurückstellen. Snapshot vom 17.10.2026 hatte null eigenständige
Issues, ist aber kein zukünftiger Deduplizierungsbeweis. PR #9 und #72 bleiben
verlinkte Vorgänger, keine neuen konkurrierenden Implementierungsbranches.

## 2. Freigegebene Bodies lokal vorbereiten

[issues.md](issues.md) ist die menschliche Vorschau. Die JSON-Datensätze enthalten
Repository, Typ, Priorität, Workstream, Target, Parent, Abhängigkeiten, Akzeptanz und
vorhandene Referenzen. Nach Freigabe je Plan-ID eine Markdown-Bodydatei in einem
**neuen privaten** Verzeichnis vorbereiten:

- Plan-ID, Ziel und Scope mit exakt diesem Repository.
- Parent-/Abhängigkeitsbezüge; zunächst lokale IDs, vor finaler Verknüpfung echte URLs.
- Akzeptanz aus `acceptance`, Nachweisarten, Grenzen und ausdrückliche Nichtziele.
- Bekannte Blocker, bestehende PR-Links und Hinweis „keine Produktionsfreigabe“.
- Keine Secrets, Transcripttexte oder lokalen privaten Dateipfade.

Die drei [Issue-Templates](../../.github/ISSUE_TEMPLATE/) und dieselben Templates
im UI-Repository wiederverwenden. Typen: `milestone`, `feature`, `bug`, `debt`;
für technische Schulden das Feature-Template mit entsprechendem Typ nutzen.

## 3. In kleinen überprüfbaren Batches anlegen

Zuerst die zehn Parents, anschließend Kinder in Abhängigkeitsreihenfolge; C27–C32
bekommen keine Kinder. Keine generische unkontrollierte Massenschleife. Pro Item
frische Dublettenprüfung und die genehmigte Bodydatei verwenden:

```sh
# Variablen enthalten genau einen geprüften JSON-Datensatz und dessen Bodypfad.
gh issue create --repo "$PLAN_REPOSITORY" \
  --title "$PLAN_TITLE" --body-file "$PLAN_BODY_FILE"
```

Neue URL und numerische Issue-ID sofort in einer privaten Zuordnung
`Plan-ID -> Repository, Nummer, URL, Database-ID` erfassen. Vor erneutem Versuch
nach Timeout erst suchen, ob die Anlage bereits gelang. Keine automatische
Wiederholung, die Dubletten erzeugt. Nach jedem Batch Bestand und Bodies lesen.
Erst die resultierenden **realen URLs** in die Roadmap/Eltern-/Abhängigkeitslinks
übernehmen; keine vorweggenommenen GitHub-Issuenummern in Git committen.

Labels vor Verwendung inventarisieren und nur fehlende genehmigte Typ-Labels
`type:milestone`, `type:feature`, `type:bug`, `type:debt` sowie `blocked` anlegen.
Bestehende Labels nicht umbenennen/überschreiben. Die neuen Templates setzen
absichtlich keine noch nicht vorhandenen Labels automatisch.

Native Sub-Issues nach Bestands-/Rechteprüfung verknüpfen. Die Database-ID des
Kindes ist **nicht** seine repositorylokale Issuenummer:

```sh
# Beispielparameter werden aus der geprüften Zuordnung übernommen, nicht erfunden.
gh api -X POST "repos/$PARENT_REPOSITORY/issues/$PARENT_NUMBER/sub_issues" \
  -F sub_issue_id="$CHILD_DATABASE_ID"
```

Cross-Repository-Kinder referenzieren ihr tatsächliches UI- oder Backendrepository.
Keine vorhandenen Parentbeziehungen ersetzen. Bei nicht verfügbarem Native-Link
zunächst eindeutige bidirektionale URL-Checklisten verwenden und die API-Grenze
protokollieren, statt einen zweiten Parent oder doppelte Issues anzulegen.
[GitHub REST Sub-Issues](https://docs.github.com/en/rest/issues/sub-issues).

## 4. Genau ein gemeinsames Project konfigurieren

Vorhandenes passendes Project wiederverwenden. Nur falls nach vollständigem
Inventar keines besteht und Neuanlage freigegeben ist:

```sh
gh project create --owner rf-data --title 'Personal Assistant – Development' \
  --format json
# PROJECT_NUMBER aus der tatsächlichen Antwort, kein Platzhalterboard:
gh project field-list "$PROJECT_NUMBER" --owner rf-data --format json
gh project field-create "$PROJECT_NUMBER" --owner rf-data --name Priority \
  --data-type SINGLE_SELECT --single-select-options 'P0,P1,P2,P3'
gh project field-create "$PROJECT_NUMBER" --owner rf-data --name Workstream \
  --data-type SINGLE_SELECT \
  --single-select-options 'Persistence,Retrieval,UI,Operations,Sources,Evaluation,Legacy,Entities'
gh project field-create "$PROJECT_NUMBER" --owner rf-data --name 'Target milestone' \
  --data-type SINGLE_SELECT --single-select-options 'C23,C24,C25,C26,C27,C28,C29,C30,C31,C32'
```

Feldanlage nur für tatsächlich fehlende Felder; Optionen vorher vergleichen.
Vorhandenes Statusfeld in der Weboberfläche kontrolliert auf die fünf vereinbarten
Optionen abgleichen. Automatische Done-/Issue-Close-/Archive-Regeln vorher prüfen
und für diese Planung deaktivieren; keine fremden Projectitems umklassifizieren.
Ansichten gemäß [project.md](project.md) manuell speichern. CLI-Feldbefehle allein
beweisen keine fertigen Ansichten oder geänderten Workflowregeln.

```sh
gh project item-add "$PROJECT_NUMBER" --owner rf-data --url "$ISSUE_URL" \
  --format json
# IDs aus field-list und item-add; Optionen nicht anhand erfundener IDs setzen:
gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" \
  --field-id "$FIELD_ID" --single-select-option-id "$OPTION_ID"
```

Status initial Backlog, Priority/Workstream/Target aus dem genehmigten Plan.
Blockierte Aufgaben zusätzlich entsprechend kennzeichnen. Parent C26 wird erst
nach tatsächlicher Operator-Go-live-Entscheidung Done, nicht nach PR-Merge.
[CLI-Referenz](https://cli.github.com/manual/gh_project),
[Felder](https://cli.github.com/manual/gh_project_field-create),
[Items](https://cli.github.com/manual/gh_project_item-edit).

## 5. Ergebnis und Wiederaufnahme

Nach jedem Batch lesen: eindeutiger Parent pro Meilenstein, 22 Kinder ausschließlich
C23–C26, richtiges Repository, native/ersatzweise URL-Beziehungen, keine doppelten
Entwürfe, eine gemeinsame Project-ID und korrekte Felder/Ansichten. Neue IDs/URLs
und ausgelassene/wegen Rechten blockierte Aktionen protokollieren. Bei Teilfehler
kein destruktives Rollback/Löschen: anhand der Zuordnung wiederaufnehmen.

Keine alten Issues/PRs schließen, keine Deployments, Downloads oder Datenmigrationen.
Erst nach separater Schritt-B-Freigabe des konkret reviewten Planstands handeln.
