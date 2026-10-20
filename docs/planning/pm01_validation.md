# PM-01 – Planungsprüfung und tatsächliche Aktionen

19.10.2026, Europe/Berlin. **Nur Planung/Metadatenprüfung**, keine Runtime-,
Browser-, Realmaterial-, Mailbox- oder Produktionsabnahme. Eigener Branch
`docs/pm01-project-consolidation`; eigener PM-Worktree. C24-06-A bleibt unverändert.

## Tatsächliche Bestandsprüfung

Backend `master` `4c057ae33d41ba98e227879cc8a51283338e4a0b`, UI `main`
`90816a1578bcf67739ee9acaa483c1635aa0c44b`. Default-Heads, beide vollständigen
Issue-/PR-Listen, Profil und Repo-Rechte über GitHub-Connector gelesen. Vor Erstellung des eigenen PM-01-PR: Backend
89, UI sieben Einträge pro Liste, jeweils unter 100; Issue-Einträge sämtlich PRs,
**null eigenständige Issues**. Die PR-Liste bestätigt #87/#90/#91 und UI #7 als
merged; #72/#88/#89 bleiben offene Drafts. [Status/Umfang](status.md).

Geprüft wurden Default-Dateien/Verträge, erste Merge-Parents, die Dateilisten der
drei Draft-Heads und die in #91 erhaltenen Pilotmetadaten. #88 hat zwei Dokumente,
#89 zehn Metadaten-/Dokumentationsdateien und keine Runtime, #72 26 Dateien mit
Piloten-/Deploymentvorbereitung. Die acht JSONdateien aus #89 stimmen byteidentisch
mit dem integrierten Bestand überein; keine neuen realen Quellen-/Hashprüfungen.

Der Nutzer nennt [Project #1](https://github.com/users/rf-data/projects/1).
**Nicht prüfbar:** tatsächlicher Titel/Node-ID, Repositorylinks, Views, Felder und
Optionen, Items, Automatisierungen und Berechtigungen. Connector: keine Projecttools;
Owner-/Repo-Projects, GraphQL sowie Milestone-/Label-Inventar liefern
`INVALID_ARGUMENT` („not an allowed ... endpoint“). `gh` nicht installiert;
öffentlicher Webabruf liefert keinen Projectinhalt (Cache miss). Repo-Adminrechte
beweisen keine Projectrechte. Keine Credentials/Envdateien gelesen und keine
Installation oder Scopeausweitung vorgenommen.

## Dokumentations- und Konsistenzprüfung

Der vorhandene JSONplan wird weiterhin als Planungsdatei verwendet, keine neue
Runtime/DB/Planungsdienst eingeführt. Alle **32 ursprünglichen Schlüssel** sind
beibehalten; **13 präzise ergänzte Zeilen** ergeben **45 Planzeilen**, davon zehn
Meilensteinparents. Das sind keine 45 neu anzulegenden offenen Implementierungen.
Die Vorschau wird aus demselben JSONstand erstellt.

Ergebnis der abschließenden Strukturprüfung: 45 eindeutige Einträge, zehn
Meilensteinparents, azyklischer Abhängigkeitsgraph, 32 Backlog-/12 technische
Done-/ein In-Progress-Vorschlag; 156 lokale Markdownziele/Anker über elf
geänderte/neue Dokumentationsdateien geprüft, acht #89-JSONdateien byteidentisch.

Tatsächliche Prüfungen mit vorhandener Python-Standardbibliothek:

- JSON parsebar, eindeutige IDs, ursprüngliche 32 IDs vollständig erhalten;
  Titel/Akzeptanz und Abhängigkeiten mit der Markdown-Vorschau abgeglichen.
- Referenzen gültig, Abhängigkeitsgraph azyklisch, Parent-/Repository-/Target-
  Zuordnung geprüft; Projectstatus/Prioritäten als Vorschläge gekennzeichnet.
- Done ausschließlich für belegten technischen Scope, nie für C23/C24/C26-
  Parents oder reale C23-06/C24-05-Abnahme. C24-06-A bleibt In Progress.
- Keine C27- oder sonstige Hard-Abhängigkeit zum persönlichen PyRepo-Projekt;
  Owner human_only, optional, keine Codex-Automation/Implementierung.
- C32 enthält Real Python, eigenen konfigurierten Zielordner, getrennten Move-
  und Verarbeitungsstatus, Idempotenz/UID/COPY/MOVE und EXPUNGE-Grenze.
- arXiv als zusätzlicher gemeinsamer Discovery-Provider mit Metadaten-/Identifier-/
  Versionsbindung, Humanreview, Rate Limits und ohne PDFdownload/Source-Promotion.
- Alle relativen Markdownziele/Anker der geänderten Dateien, geschlossene
  Codefences, UTF-8/LF/Abschlussnewline und `git diff --check` geprüft.
- Die Aufnahme vom 17.10.2026 liegt byteidentisch unter
  [status_c230_2026-10-17.md](status_c230_2026-10-17.md). Historische Validierungs-
  und Korpusberichte sowie C24-06-A-Dateien wurden nicht geändert.

Reproduzierbare Basisprüfung im eigenen Planungscheckout:

```sh
python3 -m json.tool docs/planning/issue_plan.v1.json > /dev/null
git diff --check
```

Die zusätzlichen obigen Graph-/Vorschau-/Grenz-/Link-/Byteprüfungen wurden separat
mit einem temporären stdlib-Prüfskript ausgeführt; JSON-Parsing allein beweist sie
nicht. Keine Anwendungstests/Ruff/Pytest als ausgeführt behauptet: ausschließlich
Dokumente und die bestehende Planungs-JSONdatei geändert. Keine Runtime angepasst,
keine Dienste gestartet/gestoppt und keine laufenden C24-06-A-Prüfungen übernommen.

## GitHub-Aktionen und noch offene Arbeit

Tatsächlich: eigener Planungsbranch und zugehöriger Review-PR im Backendrepository.
Keine UI-Dateiänderung, daher kein zweiter UI-PR. Keine Issues angelegt/geändert,
keine Labels/Assignees/Milestones gesetzt und keine Projectitems/Views/Felder/
Automatisierungen verändert. Keine PRs gemergt/geschlossen oder fremden Branches
verändert. Kein neues Project/Repository, kein PyRepo-Programmcode, keine Mails
oder Scheduled Jobs.

Der Auftrag **autorisiert** nichtdestruktive Planung; eine neue allgemeine
Planfreigabe fehlt nicht. Es fehlt der technisch mögliche Nachweis von Inventar
und Rechten am bestehenden Project vor den ausdrücklich bedingten operativen
Änderungen. [Konkreter Zugriffs-/UIablauf](github_execution.md),
[Inventartabelle](project.md). Die operative Erfolgsvoraussetzung „Project bietet
die konsolidierte Übersicht“ ist deshalb noch offen; keine vollständige operative
Konsolidierung behauptet. D06/D07, Realreviews und C26-Betreiberentscheidungen
bleiben eigenständig.

Nur eigene temporäre Generator-/Prüfdateien werden nach Abschluss entfernt.
Der eigene Worktree bleibt für den offenen PR erhalten; C24-06-A, Hauptcheckouts,
andere Worktrees/Branches, virtuelle Umgebungen und persistente Daten bleiben
unverändert. Kein Löschen von Branches oder fremden Artefakten.
