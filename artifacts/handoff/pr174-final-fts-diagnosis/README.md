# PR #174 – dauerhafte Diagnose-Nachweise

Entscheidung und alle 19 Suchläufe: [kompakter Bericht](../../../docs/cs50/pr174-fts-final-reliability-diagnosis.md).
[Methodik und Harness-Abweichungen](method-notes.md) erläutern die Grenzen.

- `evidence/historical/`: unveränderte Archivkopie des **historischen isolierten** Berichts; keine neuen Messungen.
- `evidence/target-case-*`: der **neue Zielworktree-Test** und seine fünf Suchen, Originalkommando, Exit, pytest-Phasen und sichere Logs.
- `evidence/{normal,single,contention,recovery}-searches.json`: vollständige neue Phasen-/Budget-/Nativfehlermessungen.
- `evidence/*-run.json`: feste Samplezahlen, Affinität, Konkurrenten-Lebenszyklus und Bytevergleich des frischen synthetischen Roots.
- `evidence/search-summary.{json,csv}`: alle 19 Läufe, einschließlich Fehlerzeitpunkt/Restbudget.
- `evidence/environment.json`, `session.json`, `verification.json`: Interpreter/Zielstand, Hashmanifest und unveränderte Zielquellen.
- `evidence/guard-check.log`: erlaubte `/tmp`-dir_fd-Zugriffe, vor dem Syscall abgewiesene Zielschreibzugriffe und Netzwerksperre.
- `evidence/contract-review.json`: gesonderte Korrektur des diagnostischen Stringvergleichs; Originalhandler-AST und Originalfehlerkonstruktor.
- `evidence/fts-probe-measured-version.py`: tatsächlich gemessene Instrumentierung mit dem fehlerhaften diagnostischen Stringvergleich. Die korrigierte Version liegt in `harness/fts_probe.py`; Timingcode identisch.
- `evidence/initial-harness-*`, `harness-diagnostic-*`, `initial-replay-harness-*`: erhaltene Harness-Startfehler vor jeder Suche; keine FTS-Fehlversuche/Erfolgsnachweise.
- `harness/`: überprüfbare testinterne Instrumentierung und feste Messrunner. Keine Paketinstallation, kein Download.
- `handoff.patch`: vollständiger neuer Bericht, Methodik, Harness und Nachweise; keine bestehenden/unabhängigen Dateien.
- `SHA256SUMS`: Integrität der Übergabedateien einschließlich Patch.

Die maschinenlesbaren Kommandos enthalten ihre tatsächlichen Ziel-/Ausgabepfade.
Für eine neue Ausführung müssen **frische** `/tmp`- und Evidenzpfade verwendet werden;
bestehende Root-/Evidenzpfade dürfen nicht überschrieben werden. Der Originaltest
bleibt direkt im angegebenen Zielworktree. Seine Messumgebung verwendet:

```text
PYTHONDONTWRITEBYTECODE=1
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
GIT_OPTIONAL_LOCKS=0
PYTHONPATH=<dieses Handoff>/harness:<Zielworktree>
FTS_DIAG_TARGET=<Zielworktree>
FTS_PROBE_OUTPUT=<frische Messdatei>
FTS_DIAG_TEST_REPORT=<frische pytest-Phasendatei>
FTS_DIAG_ENV_OUTPUT=<frische Umgebungsdatei>
```

`run_target_case.py` installiert die Instrumentierung und startet pytest mit den
Argumenten aus `target-case-command.json`. `sitecustomize.py` installiert vorher
die Netz-/Schreibsperren auch in Python-Kindprozessen. Für eine neue Messsession
benötigen die Replayrunner ein dazu passendes neues `session.json`; bestehende
Nachweise und Testroots sind keine Quelle für einen neuen frischen Originaltest.
Die festen Replays sind unabhängige Diagnoseaufrufe, keine automatische
Wiederholung/Fortsetzung fehlgeschlagener Arbeit.

Quelldiagnose: `8190fcc805f4b361f1b91b23805e8941691deab2`. Kein neuer Commit.
Bericht und Handoff sind uncommittet im bereitgestellten Workspace gesichert.
Commit/Push/PR-Update/Merge sind verboten; Defaultbranch-Integration steht aus.
Kein neuer Git-Branch/Worktree wurde erstellt oder entfernt. Temporäre Testdaten
bleiben zur Nachprüfung unter dem in `session.json` dokumentierten `/tmp`-Root.
