# PM-02 – teilweise abgeschlossen / operativ blockiert

19.10.2026, Europe/Berlin. Eigener Branch
`docs/pm02-project-operationalization`, eigener PM-02-Worktree. Keine Runtime-,
Browser-, Realmaterial-, Mailbox- oder Produktionsabnahme.

## Basis und tatsächliche Liveprüfung

Backend `master` `ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0`, Tree
`ae70d919950dcc4159b0378dcebf0cda8b137cfa`; UI `main`
`90816a1578bcf67739ee9acaa483c1635aa0c44b`. PM-01/#92 ist am 19.10.2026
unter `69e14590fb2d5967d276ea73029f6433a83d9b39`, MAINT-01/#93 unter
`ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0` gemergt. Live-PRdaten bestätigen
A/#87, B1/#90, UI-B2/#7 und C2/#91; #72/#88/#89 weiter offene Drafts.

Existenz der tatsächlichen Dateien geprüft: [führender JSONplan](issue_plan.v1.json),
[Vorschau](issues.md), [PM-01-Prüfung](pm01_validation.md),
[Projectvertrag](project.md), [Ausführungsplan](github_execution.md),
[MAINT-Importmanifest](../audit/maint01/import_manifest.md). Keine Ersatzdatei
für einen nicht gefundenen Pfad erfunden. Source-Planrevision
`pm01-2026-10-19`, 45 Zeilen, zehn Meilensteinparents, ursprüngliche 32 IDs erhalten.

GitHub-Connector: vollständige `issues?state=all&per_page=100`- und
`pulls?state=all&per_page=100`-Antworten je Repository gelesen, Backend **91**, UI
**7** Einträge pro Liste, jeweils weniger als 100. Sämtliche Issue-Endpunkt-
Einträge sind PRs; **0 eigenständige Issues** offen/geschlossen. Labels in diesen
PRs sind kein vollständiges Repository-Labelinventar. Sieben offene Backend-PRs,
keine offenen UI-PRs vor Erstellung des eigenen PM-02-PR. Der Account `rf-data`
ist per Profil erneut verifiziert, beide Repos melden admin/maintain/push/triage/pull.

## Phase A: Projectinventar nicht verifiziert

| Merkmal | Beobachteter Nachweis | Status |
| --- | --- | --- |
| Project-URL / erwarteter Owner / Nummer | Auftrag nennt https://github.com/users/rf-data/projects/1, rf-data, 1 | nutzerbenannt; Live-Identität `not_verified` |
| Globale Node-ID / tatsächlicher Titel | Keine lesbare Projectantwort | `not_verified`, null |
| Bestehende Items / Itemanzahl / verlinkte Drafts/Issues/PRs | Keine lesbare paginierte Itemliste | `not_verified`, null, **nicht 0** |
| Felder / Optionen / Views | Keine lesbaren Projectendpunkte | `not_verified` |
| Workflows / Automatisierungen | Keine entsprechende Lesecapability | `not_verified` |
| Projectlese-/Schreibrechte | Repositoryrechte beweisen keine Projectrechte | `not_verified` |
| Repository-Issues / Repo-Rechte | Vollständige lesbare RESTantworten | verifiziert, 0 eigenständige Issues |
| Repository-Labels / Milestones | Endpunkte vom Connector abgewiesen | `not_verified`, null |

Tatsächliche Zugriffsversuche: Project-Web-URL, Owner-Projects, GraphQL,
`users/rf-data/projectsV2/1` und Label-/Milestone-Endpunkte beider Repositories.
Der Connector weist diese als nicht unterstützte URLfamilien mit
`INVALID_ARGUMENT` zurück. Das ist eine **Werkzeuggrenze vor Projectprüfung**,
kein Nachweis eines fehlenden Projects oder verweigerter Nutzerrechte. Eine
Token-/Scopeausweitung wird daraus nicht abgeleitet und nicht versucht.

Unterstützte Alternativen geprüft: `gh` nicht verfügbar, nicht installiert.
Pluginverwaltung nach „GitHub Projects“ durchsucht: GitHub bereits installiert,
keine exponierte Projectcapability; andere vorgeschlagene Trackingdienste sind
kein erlaubter Ersatz und wurden nicht installiert/verbunden. Öffentlicher
Webabruf von Project sowie Label-/Milestone-Seiten liefert Cache miss ohne Inhalt.
Keine Credentials/Envdateien gelesen, Tokens angefordert oder Scopes erweitert.

**Harte Startbedingung nicht erfüllt.** Keine Issue-/Project-/Feld-/View-/
Workflowmutation; der beauftragte [manuelle GitHub-UI-Ausführungsweg](pm02_project_execution.md)
ist konkret dokumentiert. Kein neues Project und keine Ersatzdatenbank.

## Phase B: 45er-Mapping und Grenzen

[Menschenlesbarer Abgleich](pm02_mapping.md),
[maschinenlesbarer Abgleich](pm02_reconciliation.v1.json), Schema 1.
Der Plan bleibt führend und unverändert; dieser Abgleich ist ein datierter Snapshot.

- Alle 45 Plan-IDs erhalten genau einen vorgeschlagenen Repräsentationsschlüssel.
- 43 eindeutige vorgeschlagene Ziele: 15 bestehende PR-Ziele (17 Planzeilen),
  27 bedingte Issuekandidaten einschließlich zehn Parents, ein wartender aktiver Auftrag.
- Zwei Aliaspaare vermeiden doppelte Items: C23-02/C23-02A → #76;
  C23-03-Restgate/C24-04-B → #72. Vor jeder Aufnahme echte Itemsuche erforderlich.
- C24-02/03/04-PR-Items gelten nur für integrierte technische Teilumfänge;
  offene Child-/Realabnahmeanteile bleiben separat, kein pauschales Parent-Done.
- C24-06-A bleibt laufend; D06/D07 und C26 eigenständige Entscheidungen.
  PyRepo bleibt human_only/optional ohne C27-Hard-Abhängigkeit. C32/arXiv-Verträge
  sind aus dem Sourceplan vollständig erhalten.
- Alle Projectitem-IDs und Iststatuswerte bleiben `not_verified`. Auch vorhandene
  Projectdubletten, Statuskonsistenz und fachlich bestätigte Werte sind **nicht**
  als geprüft ausgegeben. 45 Projectbindungen bleiben blockiert.

## Tatsächliche Aktionszahlen

| Aktion / Bestand | Tatsächlicher Wert |
| --- | --- |
| Bestehende Projectitems | unbekannt (`null`, `not_verified`) |
| Wiederverwendete Issues | 0 Aktionen |
| Neu angelegte / aktualisierte Issues | 0 / 0 |
| Hinzugefügte / geänderte Projectitems | 0 / 0 |
| Erstellte/geänderte Felder / Views | 0 / 0 |
| Geänderte Automatisierungen / Labels / Milestones | 0 / 0 / 0 |
| Blockierte Projectzuordnungen | 45 Planzeilen |
| Eigener Dokumentations-PR | einziger neuer Repositoryvorgang, keine operative Projectkonsolidierung |

Es wird kein PR gemergt oder geschlossen und kein fremder Branch verändert.
C24-06-A, seine Worktrees/Artefakte/Prüfungen und die drei Drafts bleiben unangetastet.
Bestehende Projectwerte wurden durch diesen Task nicht geschrieben; ihre aktuelle
Unverändertheit gegenüber fremden Aktivitäten kann ohne Leserecht nicht geprüft
werden und bleibt im JSON ausdrücklich `not_verified`.

## Ausgeführte Dokumentationsprüfung

JSON parsebar; Eingangs-SHA256 an exakte Sourceplanbytes gebunden, ursprüngliche
45 IDs und alle Abhängigkeiten/Targets/Owner-/Optionalfelder mit Source abgeglichen.
Pro ID genau ein Ziel, Aliasabdeckung vollständig, 43 kanonische Ziele konsistent,
alle referenzierten PR-/Merge-SHAs gegen den gelesenen Livebestand geprüft.
Abhängigkeitsgraph azyklisch. Alle operativen Mutationszahlen 0 und alle unbekannten
Project-/Labels-/Milestonebestände null/not_verified; keine falschen Erfolgswerte.
30 lokale Markdownziele/Anker, UTF-8/LF und `git diff --check` erfolgreich geprüft.
Sieben geänderte/neue Dokumentations-/Metadatendateien einschließlich der einen
Ignoreausnahme, 43 eindeutige Zielschlüssel, sechs geschützte Worktreezustände. Führender Plan,
PM-01-/MAINT-Nachweise und geschützte Worktree-HEADs/Statusmetadaten unverändert.

Keine Ruff-/Pytest-/Browsererfolge behauptet: nur Dokumentation und eine gezielte
Ignoreausnahme für den öffentlichen JSON-Abgleich geändert. Keine neue Runtime,
Testsuite, Dependency, Datenbank oder automatisierte Projectverwaltung eingeführt.

Nach Veröffentlichung eigenen sauberen Worktree für den offenen PR behalten.
Nur eigene temporäre PM-02-Hilfsdateien werden nach Prüfung entfernt; andere
Worktrees/Branches/Tempdaten und persistente Bestände werden nicht bereinigt.
