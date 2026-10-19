# MAINT-02 – Tatsächliche Validierung und Grenzen

19.10.2026. Git 2.39.5, vorhandenes Python 3 für stdlib-/Git-Metadatenprüfungen;
keine Installation. Dokumentationsänderung ausschließlich unter diesem neuen
Auditverzeichnis. Kein Anwendungs-, Ruff-, Pytest- oder Browserlauf: kein Python-
oder Produktivcode geändert. Destruktive Befehle wurden weder an Originalen noch
an temporären Testobjekten ausgeführt.

## Git- und Liveprüfungen

GitHub-Repositories, Defaultbranches, vollständige Branchlisten und PRlisten
(`state=all&per_page=100`) über authentifizierten Connector read-only gelesen.
32 Backend-/ein UI-Branch, 92 Backend-/sieben UI-PRs; jede Liste kleiner als die
Seitengröße. Offene und gemergte PRs mit Head/Base/SHA/Draft und Mergezeitpunkt
verknüpft. Branch- und PRlisten unmittelbar vor Veröffentlichung erneut gelesen:
identischer Quellbestand, einschließlich #94 und #72/#88/#89. Eigener neuer PR
und eigener Remote-Branch sind zusätzliche, im Quellsnapshot ausgeschlossene Zugänge.

Für jede Branchzeile lokal vorhandenen Commit, Mergebase und vollständigen
Defaultbereich, Ahead/Behind, graph-eigene Commit-IDs/Datums-/Betreffmetadaten,
`git cherry` und Git-Tree gegen tatsächlichen gemergten PR-Head geprüft. Scope ist
Repository plus local/remote plus exakter Name; keine Vermischung mit Cache-Refs.

Beispiel wiederholbarer **read-only** Graphaufrufe für den unveränderten BR001-HEAD:

```sh
GIT_OPTIONAL_LOCKS=0 git -c gc.auto=0 -C "$MAINT_BACKEND_REPO" merge-base ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0 b3b59b66942e4470475cc41657f4caf515338c67
GIT_OPTIONAL_LOCKS=0 git -c gc.auto=0 -C "$MAINT_BACKEND_REPO" rev-list --left-right --count ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0...b3b59b66942e4470475cc41657f4caf515338c67
GIT_OPTIONAL_LOCKS=0 git -c gc.auto=0 -C "$MAINT_BACKEND_REPO" cherry ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0 b3b59b66942e4470475cc41657f4caf515338c67
GIT_OPTIONAL_LOCKS=0 git -c gc.auto=0 -C "$MAINT_BACKEND_REPO" rev-parse b3b59b66942e4470475cc41657f4caf515338c67^{tree}
```

Weitere exakte IDs/Heads/PRheads und Ergebnisse stehen im Branch-TSV; pro Objekt
steht ein direkt ausführbarer read-only Basisprüfaufruf in der Ausführungstabelle.
Er ersetzt nicht die zusätzlichen Vorbedingungen. Treegleichheit, Patchäquivalenz,
heutiger Dateiunterschied und historische fachliche Relevanz werden getrennt
geführt. Relevanz und Betreiber-/externe Prozessverwendung bleiben ungeprüft.

## Tabellen- und Erhaltungsprüfungen

- 147 Branch-, 46 Worktree-, 46 Cache- und 239 Ausführungszeilen: eindeutige IDs,
  konsistente Repository/Scope/Name/Pfadidentität und volle SHAs geprüft.
- Alle BR↔WT-, TR→Upstream-, MAINT-01- und historischen Dokumentbezüge konsistent;
  JSONzellen parsebar. Alle acht alten Kandidaten mit unverändertem SHA/ahead=0,
  alle zehn alten ungültigen Registrierungen erneut identifiziert.
- Alle 239 Autorisierungsflags wahr, keine Remove-Aktion, kein freigegebener
  Löschkandidat. Bedingte lokale Löschvorschläge tragen erwarteten Alt-SHA,
  Remotevorschläge genaues SHA-Lease und Ref; Rückweg jeweils angegeben.
  Kein Worktree-/Registry-Löschbefehl, keine Globs oder globales Prune.
- 160 vorhandene lokale Branch-/Cache-Refs, alle 46 Quellregistrierungen und beide
  Stash-SHAs unverändert. Alle 36 gültigen Quellworktrees haben identische HEADs
  und byteidentische `status --porcelain=v1 -z --untracked-files=all`-Ausgabe.
  Statusmetadaten sind **kein Inhaltsbackup** und erfassen nicht alle ignorierten
  Daten. Keine Aussage über vollständigen Dateisystemgleichstand.
- MAINT-01-Dateien, alte Importe und C24-06-A unverändert. Historischer ADR und
  acht #89-JSON-Gitblobs gleich zum integrierten Stand; kein erneuter Import.
- UTF-8/LF und 19 lokale Markdownziele erfolgreich geprüft. Staging und
  `git diff --cached --check` auf ausschließlich neue Auditdokumentation prüfen;
  Veröffentlichung erst bei gleichem lokalem und remote Git-Tree. Keine
  Runtime-/Deployment-/Datenbankänderung.

Private stdlib-Helfer und ursprüngliche API-/Git-Metadatenprotokolle verbleiben
außerhalb des Repositories im eigens angelegten privaten Auditroot. Keine Inhalte
von Env-, Credential- oder privaten Daten protokolliert. Die Helfer sind ein
Einmalaudit, keine neue Anwendungs-/Cleanup-Automatik.

## Offene Grenzen und Abschluss der eigenen Umgebung

Keine Betreiberbestätigung zur tatsächlichen Nichtnutzung, kein privates Backup,
kein Restoreversuch, keine semantische Bewertung historischer Fassungen und kein
inhaltsbezogener Nachweis über ignorierte/private/untracked Dateien. Kein echter
Cleanup und keine MAINT-03-Freigabe. Null beobachtete CWD-Treffer beweisen keine
Nichtnutzung. Mit veränderten Heads/PRs ist die Entscheidung neu zu prüfen.

Eigene neue Umgebung: `$WORKSPACE/Personal_Assistant-maint02`, Branch
`docs/maint02-cleanup-verification`, privater Auditroot `/tmp/maint02-qflp6kgw`.
Alle bleiben erhalten: Worktree wegen offenem PR; Auditroot einschließlich Helfern
und Metadaten wegen des ausdrücklichen Löschverbots dieses Auftrags. Die allgemeine
Cleanupregel wird dadurch für diesen Auftrag übersteuert. Kein anderer Worktree,
Branch, Cache, temporärer Quellpfad oder virtuelle Umgebung bereinigt.
