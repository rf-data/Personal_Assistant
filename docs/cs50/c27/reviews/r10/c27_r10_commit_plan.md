# C27-R10 – Reproduzierbarer Commitplan (nur Vorschlag)

Keine der folgenden Arbeiten wurde ausgeführt oder ist hiermit autorisiert. **NEEDS_REVIEW**: INCLUDE ist eine Dateiauswahl für den Vorschlag, keine Gitfreigabe. REVIEW_REQUIRED blockiert die jeweilige Gruppe bis zur Entscheidung; keine implizite Teilfreigabe. Der vollständige Produktvorschlag umfasst zusammenhängend alle 32 Code-/Test-/Fixture-/Konfigurationsdateien, ergänzt um 30 historische Dokumente. Die beiden Gruppen sind gemeinsam zu reviewen; C1 hat seine Tests dabei.

Vor jeder späteren Umsetzung: Identität des Worktrees, Branch, HEAD `a8af1d9…`, leeren Index und exakte 62 Pfade/Hashes aus `c27_r10_commit_inventory.json` kontrollieren. Bei Abweichung stoppen und das Inventar gezielt aktualisieren. Zuerst I01/API-Scope, P01/Pfadpublikation, S01/Beispiele und W01/Whitespace entscheiden; danach Live-Zielbasis und Reviewvorgaben unter gesonderter Autorisierung prüfen. Keine heutige Netzfreigabe.

Die Datei `evidence/proposed-commit-groups.json` bildet dieselben Listen maschinenlesbar ab. Keine Globs, kein `git add .`, kein Verzeichnis-Staging. Ein später autorisierter Operator darf ausschließlich die freigegebenen exakten Pfade auswählen und muss die tatsächlich geplante Indexmenge vor dem Commit gegen das freigegebene Inventar vergleichen. Ein EXCLUDE oder nicht freigegebenes REVIEW_REQUIRED darf nicht hineingeraten. Werden Entscheidungen durch Inhaltsänderungen umgesetzt, sind die bisherigen Hashes nicht mehr gültig: Inventar, relevante Nachweise und Gateentscheidung gezielt aktualisieren, keine ungeprüfte Nutzung dieses Plans.

## C1-implementation-and-tests (32 Dateien)

Vorgeschlagene Nachricht: `feat(c27): add reviewed offline learning pipeline and export safeguards`.

- `.gitignore` — INCLUDE
- `frontend/pages/G_p0_lecture_summarizer.py` — INCLUDE
- `lecture_summarizer_app.py` — INCLUDE
- `scripts/c27_reviewed_week.py` — INCLUDE
- `scripts/lecture_summary_offline.py` — INCLUDE
- `src/lecture_summary/__init__.py` — REVIEW_REQUIRED
- `src/lecture_summary/adapter.py` — INCLUDE
- `src/lecture_summary/engine.py` — INCLUDE
- `src/lecture_summary/export.py` — INCLUDE
- `src/lecture_summary/export_policy.py` — INCLUDE
- `src/lecture_summary/llm.py` — INCLUDE
- `src/lecture_summary/models.py` — REVIEW_REQUIRED
- `src/lecture_summary/public_sources.v1.json` — INCLUDE
- `src/lecture_summary/reviewed_week.py` — INCLUDE
- `src/lecture_summary/store.py` — INCLUDE
- `src/llm/model_litellm.py` — INCLUDE
- `src/model_materials/acquisition.py` — INCLUDE
- `src/tools_materials/code_zip.py` — INCLUDE
- `src/tools_materials/source_acquisition.py` — INCLUDE
- `src/tools_materials/text_validation.py` — INCLUDE
- `tests/fixtures/lecture_summary/catalog.json` — INCLUDE
- `tests/fixtures/lecture_summary/r08-approved-urls.json` — INCLUDE
- `tests/fixtures/lecture_summary/sources/hello.py` — INCLUDE
- `tests/fixtures/lecture_summary/sources/notes.txt` — INCLUDE
- `tests/fixtures/lecture_summary/sources/transcript.json` — INCLUDE
- `tests/test_c27_remediation_r02.py` — INCLUDE
- `tests/test_c27_remediation_r04.py` — INCLUDE
- `tests/test_c27_remediation_r06.py` — INCLUDE
- `tests/test_c27_remediation_r08.py` — INCLUDE
- `tests/test_c27_reviewed_week.py` — INCLUDE
- `tests/test_lecture_summary.py` — REVIEW_REQUIRED
- `tests/test_lecture_summary_ui.py` — INCLUDE

## C2-historical-documents (30 Dateien)

Vorgeschlagene Nachricht: `docs(c27): preserve historical implementation and remediation evidence`.

- `docs/cs50/c27/README.md` — INCLUDE
- `docs/cs50/c27/architecture_and_components.md` — INCLUDE
- `docs/cs50/c27/cs50p_component_provenance.v1.json` — INCLUDE
- `docs/cs50/c27/handoff-files.v1.json` — INCLUDE
- `docs/cs50/c27/handoff.md` — REVIEW_REQUIRED
- `docs/cs50/c27/integration_plan.md` — INCLUDE
- `docs/cs50/c27/real_data_acceptance.v1.json` — REVIEW_REQUIRED
- `docs/cs50/c27/remediation_r02.md` — REVIEW_REQUIRED
- `docs/cs50/c27/remediation_r04.md` — REVIEW_REQUIRED
- `docs/cs50/c27/remediation_r06.md` — REVIEW_REQUIRED
- `docs/cs50/c27/remediation_r08.md` — REVIEW_REQUIRED
- `docs/cs50/c27/rollout_plan.md` — INCLUDE
- `docs/cs50/c27/summarizer_integration.v1.json` — INCLUDE
- `docs/cs50/c27/test-results/initial-integration.txt` — REVIEW_REQUIRED
- `docs/cs50/c27/test-results/pipeline-regression.txt` — REVIEW_REQUIRED
- `docs/cs50/c27/test-results/review-final.txt` — REVIEW_REQUIRED
- `docs/cs50/c27/test-results/summarizer-final.txt` — REVIEW_REQUIRED
- `docs/cs50/c27/test_matrix.md` — INCLUDE
- `docs/cs50/c27/validation.md` — REVIEW_REQUIRED
- `docs/cs50/c27/validation.v1.json` — INCLUDE
- `docs/lecture_summary/README.md` — INCLUDE
- `docs/lecture_summary/architecture.md` — INCLUDE
- `docs/lecture_summary/example-summary.json` — REVIEW_REQUIRED
- `docs/lecture_summary/example-summary.md` — REVIEW_REQUIRED
- `docs/lecture_summary/handoff-files.json` — INCLUDE
- `docs/lecture_summary/offline-report.json` — INCLUDE
- `docs/lecture_summary/operations.md` — REVIEW_REQUIRED
- `docs/lecture_summary/test-results.txt` — REVIEW_REQUIRED
- `docs/lecture_summary/validation.json` — INCLUDE
- `docs/lecture_summary/validation.md` — REVIEW_REQUIRED

## C3 – Aktuelle R09-/R10-Dokumentation, getrennt von den 62

Vorgeschlagene Nachricht: `docs(c27): record R09 validation closure and R10 preflight decisions`.
Quelle jeweils relativ zu dieser Übergabe; Zielpfade ausdrücklich nur geplant, nicht angelegt:

| Übergabequelle | Vorgeschlagener Repositorypfad |
|---|---|
| `r09-current/c27_r09_summary.md` | `docs/cs50/c27/reviews/r09/c27_r09_summary.md` |
| `r09-current/c27_r09_historical_cases.json` | `docs/cs50/c27/reviews/r09/c27_r09_historical_cases.json` |
| `r09-current/c27_r09_test_evidence.md` | `docs/cs50/c27/reviews/r09/c27_r09_test_evidence.md` |
| `r09-current/c27_r09_gate_decisions.md` | `docs/cs50/c27/reviews/r09/c27_r09_gate_decisions.md` |
| `c27_r10_summary.md` | `docs/cs50/c27/reviews/r10/c27_r10_summary.md` |
| `c27_r10_commit_inventory.json` | `docs/cs50/c27/reviews/r10/c27_r10_commit_inventory.json` |
| `c27_r10_integration_assessment.md` | `docs/cs50/c27/reviews/r10/c27_r10_integration_assessment.md` |
| `c27_r10_commit_plan.md` | `docs/cs50/c27/reviews/r10/c27_r10_commit_plan.md` |
| `c27_r10_pr_draft.md` | `docs/cs50/c27/reviews/r10/c27_r10_pr_draft.md` |
| `c27_r10_gate_decisions.md` | `docs/cs50/c27/reviews/r10/c27_r10_gate_decisions.md` |

Die vier R09-Berichte sind bytegleiche Archivkopien mit lokalen Pfadangaben und externen Evidenzreferenzen. Publikationsreview ist erforderlich; das heutige technische Ergebnis wird bereits in R10 zusammengefasst. Fehlende extern referenzierte Rohbelege dürfen nicht als im Repository enthalten behauptet werden. Alle neun kopierten R09-Berichts-/Begleitdateien verbleiben in dieser privaten Übergabe; nur die vier oben genannten Berichte sind Kandidaten für C3. Keine Tests-/Raw-Ausgabe aus `pytest-historical/` in Git übernehmen.

Die geplanten JSON-Zielpfade sind bisher nicht durch die exakten .gitignore-Ausnahmen freigegeben. Vor C3 muss ein späterer autorisierter Dokumentationsschritt eng begrenzte Ausnahmen für `docs/cs50/c27/reviews/r09/c27_r09_historical_cases.json` und `docs/cs50/c27/reviews/r10/c27_r10_commit_inventory.json` vorschlagen/reviewen. Die Änderung an `.gitignore` ist dann gegenüber dem heutigen C1-Hash erneut zu inventarisieren. Kein erzwungenes Staging und keine breite JSON-Ausnahme. C3 ist dadurch konkret vorbereitet, aber noch nicht unmittelbar ausführbar.

`SHA256SUMS` gilt für das **gesamte private Recoverypaket**, nicht für eine selektive Repositorykopie. Es bleibt zusammen mit dem vollständigen Paket außerhalb von Git dauerhaft zu sichern. Eine spätere selektive Veröffentlichung benötigt ein eigenes Manifest ihres exakten freigegebenen Inhalts; das Recoverymanifest darf dafür nicht unverändert benutzt werden. Audithelfer, Gitkonfigurations-/Metadatensnapshots und alle `evidence/`-Inhalte sind nicht Teil des Produktcommits.

## Historische Belege und heutige Freigabe

Die 30 ursprünglichen Dokumente einschließlich Testlogs sind historische dauerhafte Nachweise, keine jetzt erzeugten Wegwerf-Testausgaben. `docs/lecture_summary/handoff-files.json` bindet 27 frühere Dateien, davon acht heute abweichend; `docs/cs50/c27/handoff-files.v1.json` bindet 50 frühere Dateien, davon zehn heute abweichend. Diese Manifeste nicht als aktuelles Manifest benutzen oder still überschreiben. R10-Inventar und kopierte R09-Berichte erklären ihre zeitliche Rolle. Historische C26-280-Erfolge, initiale C27-Gruppen und R02–R08-Berichte sind keine neue R10-Testmatrix. Aktuelle R09-6/6-, CAP-23/23-/Canary-Nachweise getrennt darstellen; keine Addition überlappender Gruppen.

## Ausschlüsse und spätere Prüfung

Von den 62 ist kein Pfad als EXCLUDE identifiziert; offene Dateien bleiben REVIEW_REQUIRED. Außerhalb der 62 sind die zehn vorhandenen Ruff-Cachedateien in der JSON-Inventarliste explizit EXCLUDE. Originalrohmaterial `/home/OPERATOR/cs50p-week0-review-RbZ8OQqe`, private Summary-Stores, .env-/Credentialdateien, Umgebungen, temporäre Rekonstruktionen und andere Handoffs bleiben außerhalb des Commits. Keine Löschung. `.gitignore` ist kein umfassender Rohdatenschutz: TXT/HTML/ZIP unter docs können unignoriert sein, daher ausschließlich diese Pfadlisten verwenden.

Die Recovery hat `git diff --check` für den bestehenden tracked Diff erfolgreich wiederholt, weil unveränderte Ausgangslage vor Berichterstellung bestätigt werden musste. Das deckt die unversionierten Dateien nicht ab. Ein ergänzender rein lesender Textcheck bestätigt sechs nachgestellte Leerzeichen im historischen example-summary.md (159–164). Diese wurden weder geändert noch verborgen. Ein späterer vollständiger Index-Diff muss sie offen behandeln; keine Umgehung von Hooks oder Reviewvorgaben.

Nach späterer genehmigter Auswahl: Indexpfade und Inhalt kontrollieren, relevante Prüfungen nur bei neuen Inhalten/Basisänderung, reguläres PR-/Reviewverfahren mit tatsächlichem Defaultbranch. Kein Commit, PR, Merge oder Push im Recoveryauftrag. Dokumente erst nach überprüfter tatsächlicher Integration als auf master vorhanden melden. Keine Cleanup-Autorisierung aus diesem Plan ableiten; alle vorbestehenden Artefakte bleiben erhalten.
