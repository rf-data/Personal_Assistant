# C. MAINT-01 – Cleanup Proposal

19.10.2026. **Vorschlag, keine Lösch-/Close-/Mergefreigabe.**
[Branchinventar](branch_inventory.md), [Dokumenteninventar](document_inventory.md).
MAINT-01 hat keine bestehende Datei, keinen Branch/Worktree/PR entfernt, geschlossen,
resettet, geprunt oder inhaltlich überschrieben. Quellindizes/Arbeitsstände bleiben
unverändert; die einzige Dokumentübernahme liegt im separaten Konsolidierungs-PR.

## Behalten und getrennte Entscheidungen

| Aktion | Konkreter Bestand | Grund / benötigter Nachweis |
| --- | --- | --- |
| behalten | gmp_compliance und personal-assistant-ui | Bestätigte Primärcheckouts; niemals durch Worktrees ersetzen oder entfernen |
| behalten | C24-06-A Backend und detached UIworktree | Laufender Auftrag; fünf untracked Implementierungs-/Test-/Dokumentdateien; Demoabhängigkeit |
| behalten | PM-01 / #92 | Separater offener Planungs-PR; weder Änderungen noch dessen Texte in MAINT integrieren |
| behalten | #72 Qdrant-/C21-Q-Pilot | Eigener ungeprüfter Draftscope, Instanz-/Modell-/Sourcebinding-Gates offen |
| integrieren, nur reviewen | Historischer #88-Review-ADR | Ein unverändertes fehlendes Architekturdokument, Provenienzmanifest; kein API-/Runtime-/Statuswechsel |
| später prüfen | #88 und #89 | B1/B2/C2 überholen frühere Implementierungsblockaden; #89-Metadaten bereits in #91. Owner entscheidet über Draftabschluss; keine Close-Aktion |
| behalten | Zwei Backend-Stashes, untracked nutrition/Completion-Audit, .gitignore-Änderung | Nicht inventarisierte Inhalte bzw. Nutzerdelta; sichern/zuordnen, keine Anwendung oder automatische Kopie |
| später prüfen | 41 graph-eigene Heads mit gemergtem PR, davon 33 treegleich | Commit-/Patch-/Treeidentität getrennt prüfen; acht verbleibende sind nicht treegleich. Kein blanket-delete |
| später prüfen | 24 unmerged_unique_work-Zeilen | Echte nicht im Defaultgraph enthaltene Commit-IDs, teils Archiv-/Legacy-/Codereferenzen; Scope und Sicherung klären |
| blockiert | Env-Dateien/ungeklärte Docversionen | Privacy-/Rechte-/Versionsprüfung; keine Inhalte oder Hashes für Env/untracked dokumentiert |
| möglicherweise später bereinigen | Zehn ungültige Worktreeeinträge / zwölf nicht mehr live vorhandene Trackingrefs | Nur Verwaltungsreste als Kandidaten; Restverzeichnisse, fremde Nutzung, ungeprüfte ignorierte Daten und eigene separate Freigabe zuerst klären |


## Konkrete graph-integrierte Kandidaten – noch nicht löschen

Die folgende Tabelle beschränkt sich auf `stale_candidate`-Zeilen. Weitere
`merged_clean`-Branches sind technisch integriert, benötigen aber dieselbe
individuelle Nutzungs-/Sicherungsprüfung. Die [vollständige Tabelle](branches.tsv)
enthält für **jeden** Branch lokale/live SHA, PR-/Mergebeleg, unique_commits,
branch_changes_since_merge_base, fehlende Pfade, Worktreezustand und Risiko.

| Scope / Branch | Lokale SHA | Live-Remote-SHA | Technischer Beleg | Konkretes Risiko / erforderliche Sicherung |
| --- | --- | --- | --- | --- |
| local / add_audio_transcript | b3b59b66942e4470475cc41657f4caf515338c67 | b3b59b66942e4470475cc41657f4caf515338c67 | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |
| local / docs/cs50-archive | 8ba519ed04c04c92573594ebe74b69a3c00aab1b | – | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |
| local / docs/cs50-completion-audit | 571874524b8b976b68f78668a4274896629229ec | – | merge-base = Head; ahead=0; kein passender PR | Untracked Auditdokumente zuerst separat prüfen/sichern; keine Freigabe |
| local / review/cs50-complete | a6b49d9eed1d6a56c1f9bc81cafb7953ccfafa42 | – | merge-base = Head; ahead=0; kein passender PR | Ungültiger Worktree mit Restverzeichnis; Bestand/Nutzung zuerst bestätigen |
| remote / add_audio_transcript | b3b59b66942e4470475cc41657f4caf515338c67 | b3b59b66942e4470475cc41657f4caf515338c67 | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |
| remote / add_local_LLM | – | b3b59b66942e4470475cc41657f4caf515338c67 | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |
| remote / add_organizer | – | b3b59b66942e4470475cc41657f4caf515338c67 | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |
| remote / add_runpod | – | d35c43fb698a5f015e56b067fa9f22ad8c459edf | merge-base = Head; ahead=0; kein passender PR | Bekannte Nutzung/ignorierte Daten prüfen; exakten SHA/Ref sichern, separate Löschfreigabe |


## Besondere graph-eigene Gegenbeispiele

| Lokaler Branch | Eigene Commits / PR | Nachweis / Empfehlung |
| --- | --- | --- |
| docs/c170-repository-consolidation-public | 1 / #68 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-course-reporting | 8 / #34 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-lecture-completion | 6 / #32 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-offline-extraction | 2 / #7 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-portable-inputs | 2 / #28 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-quality-evaluation-contract | 10 / #36 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| feat/cs50-timed-knowledge | 4 / #14 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |
| test/cs50-worker-profiles | 4 / #30 | Tree unterscheidet sich vom gemergten PR-Head. Exakte Commit-/Dateiliste aus branches.tsv separat reviewen; keine Löschannahme |


`add_knowledge_db`, `improve_wiki_extract`, der Codespacebranch und
`feat/cs50-full-coverage` haben live graph-eigene Arbeit. Legacydateien oder
historische Sourceartefaktpfade sind keine Übernahmefreigabe. Keine Zusammenführung
abweichender fachlicher/alter Pipelinestände erzwingen. `fix/cs50-html-semantics`
besitzt zusätzlich eine uncommittete `.gitignore`-Änderung; sein Worktree bleibt.

## Erforderliche Freigabe vor späterer Löschung

Je konkretem lokalem/Remote-Ref nochmals Live-SHA, Default und offene/merged PRs
prüfen. Alle seit dem Merge entstandenen Commit-IDs, Patch-/Treestatus und exklusiven
Dateien abgleichen. Dirty/untracked **und ignorierte** Dateien separat durch deren
Owner zuordnen und sichern; Stashes sind repoübergreifend zur Worktreefrage zu prüfen.
Bekannte Prozesse/Editoren/Tasks beenden oder ihre Nichtnutzung bestätigen. Quelle
und Hash/Commitbeleg für jede zu erhaltende Version nachvollziehbar sichern.
Erst dann benennt der Eigentümer einzeln die freigegebenen Branches/Worktrees/Refs.

Keine vorbereiteten destruktiven Sammelbefehle. Prunable bedeutet Git-Metadaten-
Befund, nicht Erlaubnis, verbliebene Verzeichnisse oder aktive Worktrees zu löschen.
Ältere Branchdaten allein sind kein Kriterium. Clean bedeutet keine Entbehrlichkeit.

## Eigene MAINT-Artefakte und laufende Arbeit

Der eigene Konsolidierungsbranch/Worktree bleibt für den offenen PR bestehen.
Private Hilfsskripte und reine Inventurmetadaten bleiben im eigens angelegten
MAINT-Auditroot außerhalb des Repositories erhalten: Der aktuelle Auftrag verbietet
auch Dateilöschungen ausdrücklich. Keine Bereinigung fremder/alter Tempverzeichnisse,
Venvs, Caches oder persistenter Daten. Eine spätere Entfernung der eigenen privaten
Hilfsdateien kann zusammen mit einer ausdrücklichen Cleanupfreigabe erfolgen.

[Validierung und Gültigkeitsgrenzen](README.md). Keine tatsächliche Real-/Produktions-/
Browser-/Qdrant-/Mail-/Scheduleraktion, keine Änderung an C24-06-A oder PM-01.
