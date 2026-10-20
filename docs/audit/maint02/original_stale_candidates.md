# Die acht ursprünglichen stale_candidate-Zeilen

Alle acht konkreten SHAs sind gegenüber MAINT-01 unverändert; alle acht
`ahead=0`, Mergebase gleich Branch-HEAD. Damit ist ihre committed Historie im
aktuellen Backenddefault erhalten. Dokumentvarianten können gegenüber dessen
heutigem Tree dennoch abweichen; historisch erhalten bedeutet nicht semantisch
obsolet. Eigene lokale Änderungen, Betreiberbedarf und Nutzerverweise sind
separat zu beurteilen.

| MAINT-02 / MAINT-01 | Scope und Branch | Unveränderter HEAD | Aktuelle Klasse | Sperre |
| --- | --- | --- | --- | --- |
| BR001 / B0001 | local `add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |
| BR011 / B0011 | local `docs/cs50-archive` | `8ba519ed04c04c92573594ebe74b69a3c00aab1b` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |
| BR012 / B0012 | local `docs/cs50-completion-audit` | `571874524b8b976b68f78668a4274896629229ec` | protected_active | Worktree zusätzlich gesperrt: $WORKSPACE/Personal_Assistant-completion-audit |
| BR101 / B0099 | local `review/cs50-complete` | `a6b49d9eed1d6a56c1f9bc81cafb7953ccfafa42` | stale_candidate | Worktree zusätzlich gesperrt: $WORKSPACE/Personal_Assistant-completion |
| BR107 / B0105 | remote `add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |
| BR109 / B0107 | remote `add_local_LLM` | `b3b59b66942e4470475cc41657f4caf515338c67` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |
| BR110 / B0108 | remote `add_organizer` | `b3b59b66942e4470475cc41657f4caf515338c67` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |
| BR111 / B0109 | remote `add_runpod` | `d35c43fb698a5f015e56b067fa9f22ad8c459edf` | stale_candidate | nur Graphgrundbedingungen; Nutzung/Backup/Freigabe offen |

Die ersten beiden lokalen Branches und vier Remote-Branches ohne Worktree bilden
sechs technische Prüfkandidaten. **0/8 sind abschließend entfernbar bestätigt.**
Die vorgeschlagenen sechs SHA-gebundenen Refbefehle in
[execution_plan.tsv](execution_plan.tsv) gelten ausschließlich nach allen dort
benannten Voraussetzungen und ausdrücklicher MAINT-03-Einzelfreigabe.

`docs/cs50-completion-audit` besitzt zwei untracked Dokumente; deren Inhalte wurden
nicht geöffnet. Der ungültige `review/cs50-complete`-Worktree hat ein erhaltenes
`workers`-Verzeichnis; dessen Inhalte wurden nicht untersucht. Weder ein sauberer
Registrierungsindex noch `ahead=0` erlaubt den Verlust dieser Dateien. Keine
Registrybereinigung oder Verzeichnislöschung vorgeschlagen.

Vor Entscheidung pro BR-ID: frischer SHA/Live-Default, vollständige Graphprüfung,
aktuelle offene PR-Heads und -Bases, Worktreebindung, private Datensicherung,
Dokumenterhalt, Betreiber-/Prozess-/Linkprüfung, getesteter Restoreweg und explizite
Freigabe. Die sechste/siebte Bedingung kann nicht aus `git cherry` abgeleitet werden.
