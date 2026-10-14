# CS50-Archivierung und lokale Bereinigung

Geprüfter master: `8ba519ed04c04c92573594ebe74b69a3c00aab1b`.
PR #34 gemergt; #27–#37 per GitHub-Metadaten und Git-Ancestry enthalten.
Master-Baum `02356af525ef9ff6a5dc3ebf99a1e062a363ea50` entspricht exakt dem
dokumentierten vollständigen Abschlussbaum. Keine fehlenden Änderungen gegenüber
dem Abschlussstand; abweichende lokale Original-Commit-IDs bleiben gesichert.

Die vollständige Offline-Suite lief auf einem frischen, unveränderten
origin/master-Worktree in der vorhandenen regulären uv-Umgebung: **461 passed,
6 bekannte TXT failed, 5 skipped, 0 errors** in **1682,30 s (28:02)**. Alle 472
Test-IDs und Ergebnisstatus entsprechen exakt der Abschlussbaseline. Keine
zusätzliche Regression oder Setupfehler. Keine SDK-Installation oder Upgrades.
Rohbelege: /tmp/cs50-archive-master.xml und /tmp/cs50-archive-master.log;
Baselinevergleich: /tmp/cs50-completion-final.xml. Exitcode 1 wegen bekannter TXT-Fehler.
Der gezielte Dokumentations-/Preview-Pfadtest bestand: 19 passed in 18,89 s.

49 Git-Verschiebungen plus vier zusätzlich erhaltene Abschluss-/Auditberichte;
[vollständige Pfadliste](archive_manifest.md). Neue Einstiege:
[README](../README.md), contracts/, operations/, evaluation/, archive/2026-10/.
HTML-Fixtures, Manifest und Kurs-/Task-JSONs unverändert. Originale unversionierter
Berichte und src/prio_list.md bleiben erhalten. Kein produktiver Datenimport.

Lokaler master ist ebenfalls auf 8ba519e. Vor dem Fast-Forward-Prüfaufruf:
keine versionierten Änderungen, keine Kollision neuer versionierter Pfade mit
lokalen Dateien. `git merge --ff-only origin/master` meldete „Already up to date“;
kein Reset/erzwungener Checkout. SHA-256-Vergleich bestätigt unveränderte drei
geschützte Dateien vor/nach dem Aufruf.

Dokumentations-PR: wird nach abgeschlossenen Prüfungen erstellt, kein Merge.
Bereinigung nach verifiziert identischem Baselinestatus und erneuter Einzelprüfung:
**ein physischer Worktree** (Personal_Assistant-pilot-tests) entfernt und dessen
integrierter Branch test/portable-cs50-pilot mit git branch -d gelöscht.
**14 bereits nicht mehr vorhandene /tmp-Worktrees** ausschließlich aus der
Git-Registrierung entfernt. Alle git worktree remove-Aufrufe ohne --force; jede
Entfernung anschließend per Dateisystem/Git-Liste verifiziert. Keine Daten dieser
14 Pfade gelöscht, da sie bereits fehlten. Vier detached Commits vorher durch
archive/cs50-2026-10/-Branches gesichert und geprüft; übrige nicht integrierte
Commits bleiben über bestehende lokale Branches erreichbar. Die
[aktualisierte Worktree-Tabelle](local_cleanup_inventory.md) dokumentiert Zustand,
Commit-Ancestry, untracked/ignored Dateien und Dry-Run-Empfehlungen vor Entfernung.

Historische offene PRs: [Einzelbewertung](historical_pr_review.md).
#6/#10/#11 funktional ersetzt; #9 teilweise integriert, TXT-Rest bleibt relevant.
Keine automatischen Schließungen oder Merges.

Verbleibend: sechs TXT-Vertragsfehler; fachlich manuell freizugebender realer
segment_v1-Test und Gold-Set/didaktische Qualität; optionales SDK-Profil;
allgemeiner Legacy-Consolidation-Resume-Vertrag. Keine Produktionsalgorithmen,
Modelle, Prompts oder Testassertions in diesem Auftrag geändert. Einzige
Python-Anpassungen: Markdown-Standardausgabepfad und entsprechender Snapshotpfad.

## Bekannte TXT-Fehler, separat

- `tests.test_official_transcript_import::test_txt_unknown_timestamps_paragraphs_and_unicode`
- `tests.test_official_transcript_import::test_explicit_encoding[cp1252]`
- `tests.test_official_transcript_import::test_explicit_encoding[utf-16]`
- `tests.test_official_transcript_import::test_exclusive_save_and_no_overwrite`
- `tests.test_official_transcript_import::test_knowledge_chunking_contract_without_llm_imports`
- `tests.test_official_transcript_import::test_import_does_not_load_whisper_or_application_settings`

Ursache: import_txt erzeugt None-Zeitangaben, TranscriptSegment verlangt float.
Keine künstlichen Zeitstempel oder abgeschwächten Assertions. Optionales SDK-Profil
und drei Originalpilot-/eine Workerintegration sind die fünf erklärten Skips.
