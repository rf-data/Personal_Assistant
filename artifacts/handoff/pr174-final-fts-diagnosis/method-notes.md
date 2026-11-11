# Methodik, Harness-Korrekturen und Sicherung

Der [bestehende Vertrag](../../../docs/architecture/content_fts_implementation.md#limits-und-betriebsgrenzen)
nennt ausdrücklich kooperative Python-/I/O-Schritte mit späterer Fristprüfung.
Die 2,075–3,051 s bis zum Lastfehler sind daher keine nachgewiesene
Vertragsverletzung. Der Adapter behält `Unavailable`, Code `unavailable`,
`unavailable: FTS query/database unavailable` und `raise ... from None`.
Der native Code 9 bleibt nur im testintern untersuchten Exceptionkontext erhalten.
Keine Fehlervertrags-, Deadline-, Retry- oder Produktcodeänderung;
alle Integritätsprüfungen bleiben bestehen.

Die temporäre Instrumentierung setzt ausschließlich Wrapper und Zeitmarken
in einer In-Memory-Kopie von `_check` ein. Nach Entfernen dieser Marken muss
deren AST exakt dem Original entsprechen. Keine künstliche Uhr, Sleeps oder
Profiler in den Zeitmessungen; die Werte enthalten Schedulerzeit und geringen
Messoverhead. Netzwerk ist in Python-Eltern-/Kindprozessen blockiert.
Ein separat geprüfter Schreibschutz blockiert Zielworktree-Schreibzugriffe;
Bytecode und pytest-Cache sind deaktiviert. Output enthält feste Phasen,
Zahlen, Fehlerklassen/-codes und erlaubte Fehlermeldungen, keine Quellen,
Query-/SQL-Bindwerte, Approvalinhalte, Secrets oder Providerantworten.

Harness-Abweichungen sind getrennt aufbewahrt: Zwei erste Testanläufe endeten
vor jeder Suche, weil der Schreibschutz relative `os.open(..., dir_fd=...)`
falsch auflöste. Nach Korrektur bestand die separate Guardprüfung und der
Originaltest. Ein erster Replaystart erkannte zusätzlich pytest's `current`-Symlink
als zweiten Root und stoppte ebenfalls vor jeder Suche. Der Rootselektor wurde
korrigiert. Außerdem erwartete ein rein diagnostischer Vertragsvergleich den
Fehlertext ohne `unavailable: `-Präfix: Sein gespeichertes `false` ist **kein**
Produktbefund. [Vertragsreview](evidence/contract-review.json)
prüft den unveränderten Originalhandler per AST und den Originalfehlerkonstruktor;
der Checker ist korrigiert, Rohmessungen bleiben unverändert. Dafür wurden
keine Suchrequests erneut ausgeführt. Die tatsächlich gemessene Harnessversion
ist zusätzlich archiviert. Keine vollständige 515-Test-Regression.

Abschlussprüfung: Ziel-HEAD unverändert; Ziel-`git status` leer;
**1.155 getrackte Dateien bytegleich**, `git diff --check` Exit 0.
Keine Git-Artefakte angelegt/entfernt, keine Remote-/PR-Aktionen.
Andere Worktrees, Branches und vorhandene Dokumente wurden nicht verändert.

Dauerhafte neue Nachweise und Harness:
[artifacts/handoff/pr174-final-fts-diagnosis](README.md).
Dort liegen Einzelmessungen als JSON/CSV, exakte Aufrufe, Prozess-/Guard-
und Dateiverifikation sowie der vollständige Übergabepatch `handoff.patch`.
Der Bericht und diese Dateien sind im bereitgestellten Projekt-Workspace
**uncommittet** gesichert. Commit/Push/PR-Update/Merge sind auftragsgemäß
ausgeblieben; Integration in `master` ist damit ausdrücklich **ausstehend**.
Die temporären synthetischen Testroots bleiben für Nachprüfung erhalten.
Es gibt keine task-eigenen Git-Branches oder Worktrees zur Bereinigung.
