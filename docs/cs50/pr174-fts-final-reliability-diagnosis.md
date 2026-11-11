# PR #174 – Final FTS Reliability Diagnosis

Datum: 2026-11-08. Ziel: `Personal_Assistant-cs50-m2a`, HEAD
`8190fcc805f4b361f1b91b23805e8941691deab2`. Nur synthetische Offline-Diagnose.

| Ergebnis | Bewertung |
| --- | --- |
| Reproduziert im Zielworktree | **JA unter kontrollierter CPU-Konkurrenz**; ohne Zusatzlast **NEIN**. Originaler `lecture_171`-Test: **1 passed in 74,52 s**. |
| Nativfehler | **Bestätigt für die sechs neuen Lastsuchen:** `sqlite3.OperationalError`, **9 / SQLITE_INTERRUPT**, `interrupted`. Historischer Nativfehler: **unbekannt**. |
| Performance-Bottleneck | Live-Projektion/Recordaufbau vor SQLite. Normal: Median **474,706 ms** für `_export`, **39,413 ms** für den gesamten FTS-Adapter; vollständige SQLite-Prüfungen samt MATCH **38,448 ms**. |
| Vertragsverletzung | **NEIN beobachtet.** Fristüberschreitung wird als `Unavailable` abgewiesen; kein verspäteter Sucherfolg, keine Teilergebnisse. Der bestehende Vertrag ist kooperativ, kein harter 2-s-Prozessabbruch. |
| Zuverlässigkeitsrisiko | **CPU-abhängige Nichtverfügbarkeit bestätigt:** 6/6 Ausfälle auf einem Kern mit drei Konkurrenten. Das Budget ist jedes Mal schon vor SQLite verbraucht. Keine bestätigte Datenkorruption. |
| Minimal sinnvolle Maßnahme | Zugesichertes Ressourcen-/Lastprofil für Offline-M2.1 festlegen und dort diesen Fall prüfen. Falls diese Konkurrenzlast unterstützt werden soll: gemessene Live-Projektion gezielt optimieren, insbesondere `_records` und `_selection`, unter Erhalt sämtlicher Bindungs-, ACL- und Integritätsprüfungen. Kein spekulativer SQLite-Fix. |
| Release-Empfehlung Offline-M2.1 | **HOLD für eine pauschale Freigabe.** Freigabe erst mit belegtem Ressourcen-/Lastprofil und belastbarem Budgetabstand. Die FTS-Diagnose bestätigt keinen Fehler im M2.1-Summarycode und ersetzt keine Abnahme weiterer Releasekriterien. |

## Historische Nachweise

Der [isolierte Vorgängerbericht](../../artifacts/handoff/pr174-final-fts-diagnosis/evidence/historical/pr174-fts-root-cause-analysis.md)
berichtet SQLITE_INTERRUPT unter CPU-Konkurrenz, etwa 513 ms vor dem Backend
(einschließlich Live-Projektion), etwa 38 ms für SQLite-Prüfungen/MATCH und keine
bestätigte Korruption. Seine Messungen/Regressionen werden hier nicht als neue
Nachweise gezählt. Archivkopie und Original sind hashgleich. Der native Code
des ursprünglichen historischen Fehlers bleibt **unbekannt**.

## Neue Messungen im tatsächlichen PR-Worktree

Originaltest: `tests/test_cs50_summary_batch_stress.py::test_long_source_run_cache_and_guarded_process_restart[lecture_171]`.
**1 passed in 74,52 s**, einschließlich Coverage, Cache und bewachtem Prozessneustart;
171 Blöcke, 226 Slices/Indexrecords, 1.724.416 SQLite-Bytes. Seine fünf FTS-Suchen
liegen im MVP-Aufbau; der folgende Summary-/Cache-/Restartpfad verbietet Suche.
Produktmodule, Test und bestehender Interpreter wurden direkt aus dem Zielworktree geladen.
Python 3.12.12 / SQLite 3.50.4 / pytest 9.1.1 / Pydantic 2.13.4, vier verfügbare CPUs.

Vorab begrenzter Plan: **T** fünf Originaltest-Suchen; **N** drei normale neue Suchen;
**S** drei Kontrollsuchen auf CPU 0; **C** sechs unabhängige Suchen auf CPU 0 mit
drei zusätzlichen CPU-Prozessen auf demselben Kern; **R** zwei vorab geplante
Kontrollsuchen nach Lastende mit ursprünglicher Affinität. Kein Retry/Resume eines
fehlgeschlagenen Requests. Lastmessung insgesamt 15,636 s; Konkurrenten maximal
45 s, während aller Messungen aktiv, danach beendet/eingesammelt; Affinität wiederhergestellt.

Zeiten in **ms**: Gesamt = öffentlicher Such-Contextmanager inklusive Validierung,
Sperrerwerb, Ergebnisverwendung und Abschluss; Live = `_export` einschließlich
Live-Projektion/Recordexport; FTS = gesamter `search_database`-Aufruf; Rest = gemeinsame
2-s-Deadline unmittelbar vor SQLite-Verbindungsaufbau. Manifest-/Recordsetbeweis
außerhalb von `_export` ist in Live nicht enthalten. Die Deadline beginnt nach den
anfänglichen Sperren; Gesamtzeit entspricht daher nicht exakt ihrem Geltungsbereich.

| Lauf | Gesamt | Live | FTS | Rest vor SQLite | Ergebnis / nativer Code | Abbruchphase |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| T1 | 624.187 | 539.039 | 54.211 | +1436.897 | OK | — |
| T2 | 497.037 | 427.878 | 39.497 | +1548.027 | OK | — |
| T3 | 914.776 | 840.515 | 40.652 | +1131.921 | OK | — |
| T4 | 547.652 | 479.948 | 38.518 | +1496.542 | OK | — |
| T5 | 510.798 | 439.740 | 39.330 | +1534.860 | OK | — |
| N1 | 703.294 | 604.322 | 52.266 | +1354.817 | OK | — |
| N2 | 521.073 | 452.987 | 37.706 | +1522.000 | OK | — |
| N3 | 537.773 | 469.464 | 39.268 | +1507.027 | OK | — |
| S1 | 601.693 | 529.168 | 40.780 | +1445.338 | OK | — |
| S2 | 509.406 | 441.325 | 38.092 | +1533.928 | OK | — |
| S3 | 531.488 | 463.344 | 38.328 | +1512.696 | OK | — |
| C1 | 2206.207 | 2052.218 | 1.674 | -166.963 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| C2 | 2075.468 | 1932.935 | 10.997 | -51.737 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| C3 | 2765.687 | 2608.834 | 11.177 | -732.029 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| C4 | 2587.951 | 2419.500 | 11.132 | -562.858 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| C5 | 3050.917 | 2785.503 | 11.171 | -1025.884 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| C6 | 2907.499 | 2700.231 | 11.143 | -843.210 | Unavailable; 9 / SQLITE_INTERRUPT | Schema/Integrität: execute PRAGMA integrity_check |
| R1 | 746.047 | 619.440 | 78.104 | +1338.911 | OK | — |
| R2 | 701.172 | 609.492 | 51.613 | +1356.719 | OK | — |

T+N: **8/8 erfolgreich**, Median Gesamt **542,713 ms**, Live **474,706 ms**,
FTS **39,413 ms**, vollständige SQLite-Prüfungen/MATCH **38,448 ms**, MATCH allein
**0,359 ms**. Verschachtelte Projektionsmediane `_load` / `_selection` / `_records`:
84,647 / 150,118 / 227,348 ms. S: 3/3, R: 2/2 erfolgreich. Insgesamt **13 Erfolge / 6 Abweisungen**.

C: **6/6 SQLITE_INTERRUPT (9)** bei `execute(PRAGMA integrity_check)` vor MATCH.
Vor SQLite fehlen bereits **51,737–1.025,884 ms** Budget; Live allein dauert
**1.932,935–2.785,503 ms**. Der Progresshandler erkennt hier die verstrichene
Deadline. Die kurze FTS-Zeit enthält abgebrochene Prüfungen und ist kein
vollständiger Backendbenchmark. Dieselben unveränderten synthetischen Snapshotbytes
bestehen vor/nach Lastende alle Prüfungen. Kein Nachweis von Datenkorruption;
keine rückwirkende Identifikation des historischen Fehlers oder seiner damaligen CPU-Last.

## Vertrag, Grenzen und Ergebnissicherung

Die 2,075–3,051 s bis zum Lastfehler verletzen den dokumentierten
[kooperativen Zeitvertrag](../architecture/content_fts_implementation.md#limits-und-betriebsgrenzen)
nicht: Python-/I/O-Schritte sind nicht hart präemptiv. Keine erfolgreiche Suche
überschritt ihre interne Deadline. Unveränderter Fehlervertrag: `Unavailable`,
Code `unavailable`, `unavailable: FTS query/database unavailable`, `raise ... from None`.

Nur Wrapper und AST-geprüfte zusätzliche Zeitmarken im Arbeitsspeicher;
keine Produkt-/Testdateiänderung, künstliche Uhr, Timeout-Erhöhung, Retry oder
entfernte Prüfung. Netzwerk und Zielworktree-Schreibzugriffe wurden in Python
bewacht; Bytecode/pytest-Cache deaktiviert. Ausschließlich frische synthetische
Testroots unter `/tmp/pr174-final-fts-8zl1moi6`; dortige Fixture-Schreibzugriffe sind
für den unveränderten Originaltest nötig. Zusätzliche Suchen sind lesend; ihre
Rootbytes bleiben vor/nach jeder Reihe identisch. Diagnoseoutput enthält keine
Quelltexte, SQL-Bindwerte, Approvalinhalte oder Secrets. Keine 515-Test-Regression.

[Methodik und dokumentierte Harness-Korrekturen](../../artifacts/handoff/pr174-final-fts-diagnosis/method-notes.md):
zwei frühe Guardabbrüche und ein Replay-Rootselektor-Abbruch jeweils vor jeder Suche;
ein rein diagnostischer Fehlertextvergleich übersah das vorhandene `unavailable: `-Präfix.
Dessen gespeichertes `false` ist kein Produktbefund. Der Originalhandler wurde per AST
geprüft, der Checker korrigiert und die Rohmessung unverändert bewahrt; keine Suchwiederholung dafür.

Abschluss: Ziel-HEAD unverändert, Ziel-`git status` leer, **1.155 getrackte Dateien
bytegleich**, `git diff --check` Exit 0. Keine Git-Artefakte angelegt/entfernt,
keine Remote-/PR-Aktion. Andere Aufgaben und Worktrees bleiben unangetastet.

Bericht und [Messnachweise/Handoff](../../artifacts/handoff/pr174-final-fts-diagnosis/README.md)
sind dauerhaft im bereitgestellten Projekt-Workspace **uncommittet** gesichert;
vollständiger Patch: `artifacts/handoff/pr174-final-fts-diagnosis/handoff.patch`.
Kein Commit/Push/PR-Update/Merge gemäß Auftrag; Integration in `master` bleibt
**ausstehend**. Temporäre synthetische Testroots bleiben zur Nachprüfung erhalten.
Keine task-eigenen Git-Branches/Worktrees zur Bereinigung.
