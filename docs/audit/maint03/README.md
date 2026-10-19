# MAINT-03 – Einzelgates geprüft, null Löschungen

19.10.2026, Europe/Berlin. **Fortschrittsstand, keine ausgeführte Bereinigung.**
Der Auftrag enthält keine objektbezogenen Remove-Genehmigungen und benennt keine
autorisierten Backup-/Recoveryziele oder Sicherungs-/Restorebelege. Alle
destruktiven Einzelgates bleiben geschlossen. Kein Bestand wird allein wegen
Merge, Alter, Treegleichheit, einer TSV-Zeile oder dieses Berichts freigegeben.

- [Aktualisierte Einzelentscheidungsliste](individual_decisions.tsv)
- [Konkrete offene Betreiberentscheidungen](operator_decisions.md)
- [Unveränderte MAINT-02-Matrix](../maint02/execution_plan.tsv)
- [MAINT-02-Ausführungsplanung](../maint02/maint03_execution_plan.md)
- [Historischer Dokumenterhalt](../maint01/document_inventory.md)

## Tatsächlicher Umfang und Quellenbindung

Live Backend `master`: `3de5ae965475484070be7683cf3dda2b0c73ba1d`;
UI `main`: `af95415071e85a461579c0a1650fdd0efe6c25b9`.
GitHub-origin und Common-Gitdirs erneut verifiziert:
`rf-data/Personal_Assistant` / `$WORKSPACE/gmp_compliance/.git`,
`rf-data/personal-assistant-ui` / `$WORKSPACE/personal-assistant-ui/.git`.
`$WORKSPACE` bezeichnet `/home/robfra/0_Portfolio_Projekte`, `$TMP` ausschließlich
zuvor registrierte `/tmp`-Pfade. Primärcheckouts bleiben unverändert.

Die bestehenden MAINT-01/02-Dokumente und Tabellen sind die integrierten Fassungen:
20 Gitblobs unter `docs/audit/maint01/` und `docs/audit/maint02/` mit den lokalen
Quelldateien abgeglichen. Die vorhandenen globalen und integrierten Repository-
Agentenanweisungen gelten. Kein alter Bericht oder historische Tabelle geändert,
keine erneute Dokumentübernahme und keine neue Cleanup-Runtime.

Aktuell vor dem eigenen Remote-Branch: **115 lokale Branches**, **34 live Remote-
Branches** (32 Backend, zwei UI), **47 Trackingrefs**, **47 Registrierungen**
(37 gültig, zehn ungültig), **zwei Backend-Stashes**, keine UI-Stashes.
Das ergibt 149 Branchzeilen und 243 aktuell vorhandene typisierte Objekte, nicht
243 Löschkandidaten. Die 239 alten IDs bleiben als feste Entscheidungsmenge erhalten;
fünf hinzugekommene Objekte und ein inzwischen fehlender alter Ref erklären das Delta.

## Ergebnis der 239 Einzelprüfungen

| Nachweis | Ergebnis |
| --- | ---: |
| Identität gebunden, alter SHA unverändert | 236 |
| Live-Default-SHA weitergerückt | 2 |
| Alter Ref derzeit live nicht vorhanden | 1 |
| Alte Vorschläge Keep / Review / Archive unverändert übernommen | 103 / 103 / 33 |
| Vollständige Remove-Einzelgenehmigungen | 0 |
| Ausgeführte Löschungen / Prunes / Reparaturen / Archivierungen | 0 / 0 / 0 / 0 |
| Erstellte Backuprefs / Bundles / Restoretests | 0 / 0 / 0 |

Die beiden weitergerückten Refs sind Backend `master` und UI `main`.
Der Remote-Ref `refs/heads/docs/pm02-project-operationalization` ist bereits vor
MAINT-03 nicht mehr live vorhanden; sein Fehlen ist **keine von MAINT-03 ausgeführte
Löschung**. Die Tabelle nennt die exakten alten/neuen SHAs und ID. Diese drei
Abweichungen sperren jede Wiederverwendung alter SHA-gebundener Genehmigungen.

Die acht ursprünglichen stale-Zeilen einschließlich der sechs leichter prüfbaren
Fälle behalten ihren SHA. Alle 30 alten reinen Graphprüfkandidaten bleiben
`ahead=0`; das ist weiterhin keine operative Löschfreigabe.

## Tatsächlich ausgeführte nichtdestruktive Prüfungen

- Vollständige Live-Branch-/PRlisten: Backend 32/94, UI 2/8, jeweils `per_page=100`
  und unter einer Seite. Offene Heads und Bases zugeordnet; #72/#88/#89 bleiben
  offene Drafts. PM-01/#92, MAINT-01/#93, PM-02/#94, MAINT-02/#95 sowie die
  Agentenanweisungen #96/UI #8 sind integriert. C24-06-A bleibt geschützt.
- Lokale vollständige Branch-/Trackingrefs, Origin, Common-Gitdir, Worktree-
  Registrierungen, HEADs und Stash-IDs gelesen. Gültige Worktrees mit
  `GIT_OPTIONAL_LOCKS=0`, `gc.auto=0`, deaktivierten fsmonitor/untrackedCache und
  `status --porcelain=v1 -z --untracked-files=all` geprüft. Kein Inhaltsread der
  untracked oder ignorierten Daten; sauberer Gitstatus bestätigt deren Entbehrlichkeit nicht.
- Beide Live-Defaults erweitern die jeweilige MAINT-02-Basis nachweislich:
  Backend sechs neue Commits, `behind_by=0`, Mergebase
  `ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0`; UI zwei neue Commits, `behind_by=0`,
  Mergebase `90816a1578bcf67739ee9acaa483c1635aa0c44b`.
  Nachweis über den authentifizierten GitHub-Commitvergleich, nicht über alte
  `origin/*`-Cachewerte. Bei 64 unveränderten, bereits auf MAINT-02 vollständig
  enthaltenen Branchheads folgt daraus weiterhin `ahead=0`, gleiche Mergebase
  und alter Behindwert plus sechs/zwei. Dieser **abgeleitete** Nachweis ist im
  TSV ausdrücklich von einer neu lokal ausgeführten Graphberechnung getrennt.
- 95 Branchzeilen erneut gegen ihre tatsächlichen gemergten PR-Heads auf
  Commit-/Treeidentität geprüft; alle 33 Archive-Vorschläge weiterhin treegleich.
  Kein semantischer Obsoleszenznachweis und keine ausgeführte Archivierung.
- Bei zehn ungültigen Registrierungen: Pfad-/Gitzuordnung, vorhandener Index
  gegen aufgezeichneten HEAD und ausschließlich unmittelbare Restverzeichnis-
  metadaten geprüft. Zehn Indexprüfungen ohne gestagte Änderungen; acht Pfade
  fehlen, zwei Restwurzeln bestehen. Private/ignorierte/untracked Restdaten und
  Betreiber-/Prozessnutzung bleiben `not_verified`; kein Prune, Repair oder Checkout.
- Alle 239 IDs, Repository/Typ/Identität, SHAs und Tabellenverknüpfungen geprüft.
  Jede Cleanupaktion explizit `not_executed`, keine Backup-/Restorebelege erfunden.
  Historische MAINT-01/02-Graph-, Patch- und Dokumentbelege bleiben am Originalort.

**Nicht erneut ausgeführt:** aktuelle Patchäquivalenz gegen die neuen Defaults,
vollständige neue Graph-/Unique-Commit-Berechnung für nicht integrierte Branchheads,
semantischer Dokumentreview, private Datensicherung, Nichtnutzungsbestätigung oder
Restoretest. Diese Werte sind im TSV unbekannt bzw. klar historisch, nicht als
frische erfolgreiche Einzelgateprüfung dargestellt. Ein späterer Remove-Auftrag
muss die vollständige Phase A unmittelbar vorher erneut bestehen. Keine Fetches,
Ref-/Trackingupdates, Downloads privater Bestände, Env-/Credentialreads oder Services.

## Entscheidungsliste und Datenvertrag

`individual_decisions.tsv`: UTF-8/LF mit Header und JSONzellen. Eine Zeile pro
unveränderter MAINT-02-ID; kein Shellrunner. `baseline_proposed_action` bleibt
Keep/Review/Archive. `effective_disposition` heißt Keep bzw. Keep bis zum vollständigen
Einzelgate, **keine** Betreiberbestätigung oder Promotion zu Remove.
`authorization_evidence`, `backup_evidence`, `restore_evidence`,
`authorized_cleanup_command` und `executed_cleanup_command` bleiben leer,
`cleanup_result=not_executed`. Leerer Nachweis heißt fehlend, nicht erfolgreich.
`observation` unterscheidet gleicher SHA, weitergerückter SHA und live fehlender Ref.
Die Herkunft jeder Metadatenprüfung und deren Grenzen stehen in `inspection_evidence`
und `checks`; alle nicht bestätigten Rechte-/Daten-/Nutzungsfragen in den Blockern.

Nichtversionierte Inhalte, Envfamilien, historische private Gitobjekte und
vollständige Host-/Prozessdaten werden nicht veröffentlicht. Bestehende Backup- und
Recoverydaten nicht geöffnet oder verändert. Ein unveränderter Commit ist kein Backup.

## Integration, Validierung und eigener Lifecycle

Ausschließlich drei neue Dokumentationsdateien unter `docs/audit/maint03/`, eigener
Remote-Branch `docs/maint03-controlled-cleanup`; kein neuer lokaler Branch oder
Worktree erforderlich. Dauerhafte Übernahme ausschließlich über normalen PR-/
Reviewprozess in Backend `master`; kein UI-Dokument verändert. Default-Tree nach
Merge gegen den geprüften PR-Tree und die drei Gitblobs verifizieren.

Struktur-, SHA-/ID-, JSONzellen-, Link- und Whitespaceprüfung erfolgreich.
Quellrefs, alle 47 Registrierungen, 37 gültige Worktree-HEADs/-Statusausgaben und
beide Stashes erneut mit dem Eingangssnapshot verglichen: unverändert.
Keine Anwendungs-,
Ruff-, Pytest- oder destruktiven Tests behauptet: ausschließlich Dokumentation.
Private stdlib-Helfer und Metadaten sind Einmalprüfmittel, keine Produktivänderung,
keine Backups und keine neue Planungsdatenbank.

Für die spätere Entfernung ausschließlich des neu für MAINT-03 angelegten Remote-
Branches erst Merge und exakten Head erneut prüfen. Der vorhandene Connector
bietet keine Branchlöschung; die zuvor bestätigte fehlende Git-Schreibauthentifizierung
ist kein Grund, Tokens/Envdateien zu lesen oder Gitkonfiguration zu ändern.
Ist die Entfernung weiterhin nicht möglich, Branch erhalten und den konkreten
Aufbewahrungsgrund im zugehörigen PR und Abschluss dokumentieren. Kein früherer
MAINT-/PM-/Agentenbranch und kein alter Worktree gehört zu diesem eigenen Lifecycle.

Die Bestandsbereinigung bleibt **ausstehend wegen fehlender Einzelentscheidungen**;
dieser Fortschrittsbericht behauptet ausschließlich tatsächlich geprüfte Metadaten
und null Cleanupaktionen. Keine automatische Freigabe durch Integration des Berichts.
