# C27-R11 – Commit-/PR-Vorschlag

**Nur Plan.** Kein Staging/Commit/Push/Checkout/Fetch/Merge/Rebase/Reset/PR in R11. 62 R10-Kandidaten bleiben als Inhalt vorgesehen: 11 werden an andere Zielpfade umgebunden (zehn Paketdateien und eine Testsuite), 51 bleiben am selben Zielpfad. Zusätzlich exakt 21 geplante Dateien: 16 Archivberichte, drei aktuelle Dokument-/Manifestdateien, eine Koexistenzsuite und die begrenzte bestehende Hookkonfiguration. **83 eindeutige Zielpfade** auf der unveränderten lokal bekannten Basis. Bei neuer Live-Basis ist dies eine explizit neu abzugleichende Soll-Liste, keine Erlaubnis, vorhandenen Zielinhalt zu überschreiben.

## C1 – Learning-Implementierung und zugehörige Tests, 34 Dateien

Empfohlener Commit: `feat(c27): isolate reviewed learning pipeline and retain export safeguards`.
32 bisherige Code-/Test-/Fixture-/Konfigurationskandidaten nach untenstehender Zuordnung plus **tests/test_c27_summary_coexistence.py** und die unten präzisierte **.pre-commit-config.yaml**-Anpassung. Alle aktiven Namespace-/Monkeypatch-/Dateipfadänderungen und exakten Ignoreausnahmen gehören hierher. Ein vorheriger Commit nur mit Modellen oder nur mit Namespaceumzug wäre nicht eigenständig prüfbar. Bestehende vier CS50P-Dateien als selektive Herkunft dokumentieren; keine zusätzlichen fremden Branchcommits einschließen.

| Exakte R10-Quelle | Exakter Zielpfad | Empfehlung |
|---|---|---|
| `.gitignore` | `.gitignore` | INCLUDE_AFTER_CHANGE |
| `frontend/pages/G_p0_lecture_summarizer.py` | `frontend/pages/G_p0_lecture_summarizer.py` | INCLUDE_AFTER_CHANGE |
| `lecture_summarizer_app.py` | `lecture_summarizer_app.py` | INCLUDE_AS_IS |
| `scripts/c27_reviewed_week.py` | `scripts/c27_reviewed_week.py` | INCLUDE_AFTER_CHANGE |
| `scripts/lecture_summary_offline.py` | `scripts/lecture_summary_offline.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/__init__.py` | `src/c27_learning_summary/__init__.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/adapter.py` | `src/c27_learning_summary/adapter.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/engine.py` | `src/c27_learning_summary/engine.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/export.py` | `src/c27_learning_summary/export.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/export_policy.py` | `src/c27_learning_summary/export_policy.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/llm.py` | `src/c27_learning_summary/llm.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/models.py` | `src/c27_learning_summary/models.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/public_sources.v1.json` | `src/c27_learning_summary/public_sources.v1.json` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/reviewed_week.py` | `src/c27_learning_summary/reviewed_week.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/store.py` | `src/c27_learning_summary/store.py` | INCLUDE_AFTER_CHANGE |
| `src/llm/model_litellm.py` | `src/llm/model_litellm.py` | INCLUDE_AS_IS |
| `src/model_materials/acquisition.py` | `src/model_materials/acquisition.py` | INCLUDE_AS_IS |
| `src/tools_materials/code_zip.py` | `src/tools_materials/code_zip.py` | INCLUDE_AS_IS |
| `src/tools_materials/source_acquisition.py` | `src/tools_materials/source_acquisition.py` | INCLUDE_AS_IS |
| `src/tools_materials/text_validation.py` | `src/tools_materials/text_validation.py` | INCLUDE_AS_IS |
| `tests/fixtures/lecture_summary/catalog.json` | `tests/fixtures/lecture_summary/catalog.json` | INCLUDE_AS_IS |
| `tests/fixtures/lecture_summary/r08-approved-urls.json` | `tests/fixtures/lecture_summary/r08-approved-urls.json` | INCLUDE_AS_IS |
| `tests/fixtures/lecture_summary/sources/hello.py` | `tests/fixtures/lecture_summary/sources/hello.py` | INCLUDE_AS_IS |
| `tests/fixtures/lecture_summary/sources/notes.txt` | `tests/fixtures/lecture_summary/sources/notes.txt` | INCLUDE_AS_IS |
| `tests/fixtures/lecture_summary/sources/transcript.json` | `tests/fixtures/lecture_summary/sources/transcript.json` | INCLUDE_AS_IS |
| `tests/test_c27_remediation_r02.py` | `tests/test_c27_remediation_r02.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_c27_remediation_r04.py` | `tests/test_c27_remediation_r04.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_c27_remediation_r06.py` | `tests/test_c27_remediation_r06.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_c27_remediation_r08.py` | `tests/test_c27_remediation_r08.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_c27_reviewed_week.py` | `tests/test_c27_reviewed_week.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_lecture_summary.py` | `tests/test_c27_learning_summary.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_lecture_summary_ui.py` | `tests/test_lecture_summary_ui.py` | INCLUDE_AFTER_CHANGE |

Zusätzliche C1-Pfade: `tests/test_c27_summary_coexistence.py` und `.pre-commit-config.yaml`.

## C2 – Historische Projektbelege, 30 Dateien

Empfohlener Commit: `docs(c27): preserve historical validation with declared example normalization`.
29 Dateien bytegleich; einzig example-summary.md nach der beschriebenen Sechs-Leerzeichen-Normalisierung. **Keine erneuerten Testerfolgszahlen in historischen Berichten.** Die beiden historischen Manifeste bleiben bytegleich und gelten ausschließlich für ihre früheren Dateibytes. C2 zusammen mit C3 reviewen, damit die historische Einordnung unmittelbar sichtbar ist.

| Exakte R10-Quelle | Exakter Zielpfad | Empfehlung |
|---|---|---|
| `docs/cs50/c27/README.md` | `docs/cs50/c27/README.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/architecture_and_components.md` | `docs/cs50/c27/architecture_and_components.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/cs50p_component_provenance.v1.json` | `docs/cs50/c27/cs50p_component_provenance.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/handoff-files.v1.json` | `docs/cs50/c27/handoff-files.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/handoff.md` | `docs/cs50/c27/handoff.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/integration_plan.md` | `docs/cs50/c27/integration_plan.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/real_data_acceptance.v1.json` | `docs/cs50/c27/real_data_acceptance.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r02.md` | `docs/cs50/c27/remediation_r02.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r04.md` | `docs/cs50/c27/remediation_r04.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r06.md` | `docs/cs50/c27/remediation_r06.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r08.md` | `docs/cs50/c27/remediation_r08.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/rollout_plan.md` | `docs/cs50/c27/rollout_plan.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/summarizer_integration.v1.json` | `docs/cs50/c27/summarizer_integration.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/initial-integration.txt` | `docs/cs50/c27/test-results/initial-integration.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/pipeline-regression.txt` | `docs/cs50/c27/test-results/pipeline-regression.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/review-final.txt` | `docs/cs50/c27/test-results/review-final.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/summarizer-final.txt` | `docs/cs50/c27/test-results/summarizer-final.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test_matrix.md` | `docs/cs50/c27/test_matrix.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/validation.md` | `docs/cs50/c27/validation.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/validation.v1.json` | `docs/cs50/c27/validation.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/README.md` | `docs/lecture_summary/README.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/architecture.md` | `docs/lecture_summary/architecture.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/example-summary.json` | `docs/lecture_summary/example-summary.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/example-summary.md` | `docs/lecture_summary/example-summary.md` | INCLUDE_AFTER_CHANGE |
| `docs/lecture_summary/handoff-files.json` | `docs/lecture_summary/handoff-files.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/offline-report.json` | `docs/lecture_summary/offline-report.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/operations.md` | `docs/lecture_summary/operations.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/test-results.txt` | `docs/lecture_summary/test-results.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/validation.json` | `docs/lecture_summary/validation.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/validation.md` | `docs/lecture_summary/validation.md` | KEEP_AS_HISTORICAL_EVIDENCE |

## C3 – Aktueller Status, Reviews und Abschlussdokumentation, 19 Dateien

Empfohlener Commit: `docs(c27): record scope resolution and implementation approval gates`.
Die folgende Tabelle enthält alle 21 Zusätze insgesamt; **Koexistenztest und .pre-commit-config.yaml gehören C1**, alle übrigen 19 gehören C3. Quellen unter /tmp sind erst nach SHA256SUMS-Verifikation aus dem vollständigen R11-Paket zu kopieren. Das private Paketmanifest darf nicht als Manifest einer selektiven Repositorykopie ausgegeben werden.

| Quelle | Exakter Repositoryzielpfad | Behandlung |
|---|---|---|
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r09/c27_r09_summary.md` | `docs/cs50/c27/reviews/r09/c27_r09_summary.md` | copy immutable historical report; explain external references in reviews/README.md |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r09/c27_r09_historical_cases.json` | `docs/cs50/c27/reviews/r09/c27_r09_historical_cases.json` | copy immutable historical report; explain external references in reviews/README.md |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r09/c27_r09_test_evidence.md` | `docs/cs50/c27/reviews/r09/c27_r09_test_evidence.md` | copy immutable historical report; explain external references in reviews/README.md |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r09/c27_r09_gate_decisions.md` | `docs/cs50/c27/reviews/r09/c27_r09_gate_decisions.md` | copy immutable historical report; explain external references in reviews/README.md |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_summary.md` | `docs/cs50/c27/reviews/r10/c27_r10_summary.md` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_commit_inventory.json` | `docs/cs50/c27/reviews/r10/c27_r10_commit_inventory.json` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_integration_assessment.md` | `docs/cs50/c27/reviews/r10/c27_r10_integration_assessment.md` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_commit_plan.md` | `docs/cs50/c27/reviews/r10/c27_r10_commit_plan.md` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_pr_draft.md` | `docs/cs50/c27/reviews/r10/c27_r10_pr_draft.md` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r10/c27_r10_gate_decisions.md` | `docs/cs50/c27/reviews/r10/c27_r10_gate_decisions.md` | copy immutable R10 record; R11 plan supersedes execution proposal |
| `/tmp/c27-r11-cjxf689_/c27_r11_summary.md` | `docs/cs50/c27/reviews/r11/c27_r11_summary.md` | copy this design record after its final checksum validation; archive, not live status |
| `/tmp/c27-r11-cjxf689_/c27_r11_file_decisions.json` | `docs/cs50/c27/reviews/r11/c27_r11_file_decisions.json` | copy this design record after its final checksum validation; archive, not live status |
| `/tmp/c27-r11-cjxf689_/c27_r11_conflict_analysis.md` | `docs/cs50/c27/reviews/r11/c27_r11_conflict_analysis.md` | copy this design record after its final checksum validation; archive, not live status |
| `/tmp/c27-r11-cjxf689_/c27_r11_integration_design.md` | `docs/cs50/c27/reviews/r11/c27_r11_integration_design.md` | copy this design record after its final checksum validation; archive, not live status |
| `/tmp/c27-r11-cjxf689_/c27_r11_commit_plan.md` | `docs/cs50/c27/reviews/r11/c27_r11_commit_plan.md` | copy this design record after its final checksum validation; archive, not live status |
| `/tmp/c27-r11-cjxf689_/c27_r11_gate_decisions.md` | `docs/cs50/c27/reviews/r11/c27_r11_gate_decisions.md` | copy this design record after its final checksum validation; archive, not live status |
| neu anzufertigen | `docs/cs50/c27/reviews/README.md` | create current status, historical index, publication decisions, path mapping and normalization provenance |
| neu anzufertigen | `docs/cs50/c27/operations_current.md` | create current offline operating instructions for isolated namespace |
| neu anzufertigen | `docs/cs50/c27/integration_manifest.v2.json` | generate exact final 82 other planned paths with hashes/sizes/actions; omit self, bind externally |
| neu anzufertigen | `tests/test_c27_summary_coexistence.py` | add only meaningful namespace/schema-family isolation and cold-import regressions |
| bestehende `.pre-commit-config.yaml` | `.pre-commit-config.yaml` | end-of-file-fixer: drei exakte Byteerhaltungs-Ausnahmen, alle anderen Hooks unverändert |

Die sechs R11-Berichte sind der Stand dieses Designs. Spätere Implementierungsergebnisse gehören in reviews/README.md und eine ausdrücklich aktualisierte Integrationsmanifestfassung, nicht als nachträglich behauptete Testausführung in diese archivierten Berichte. Die tatsächliche Abschlussdokumentation muss erfolgte Änderungen, neue zielbezogene Tests, Ziel-/Commit-/PR-Identitäten und verbleibende Gates nennen. PR-/Merge-Link und verifizierter Defaultbranchinhalt dürfen erst nach tatsächlicher Verifikation eingetragen werden. Wenn dies einen weiteren Dokumentcommit/PR erfordert, als eigene abschließende Phase offenhalten; keinen vollständigen Projektabschluss vorweg behaupten.

## Exakte Ausschlüsse im bekannten Scope

Keine der 62 Inhaltsquellen wird vollständig verworfen. Folgende **21 Pfade dürfen vom Learning-Vorschlag nicht gestaged/veröffentlicht werden**: elf ursprüngliche Pfade mit anderweitig aufgenommenem Inhalt und zehn unveränderte Cachedateien. Wenn die alte Acceptance-Datei auf der späteren Basis bereits tracked ist, heißt Ausschluss ausdrücklich **keine Änderung/keine Löschung** dieses vorhandenen Inhalts.

- `.ruff_cache/.gitignore`
- `.ruff_cache/0.16.3/14392489710586582593`
- `.ruff_cache/0.16.3/17688539607854952212`
- `.ruff_cache/0.16.3/238446461390248762`
- `.ruff_cache/0.16.3/2582520910028759232`
- `.ruff_cache/0.16.3/2615147935293565000`
- `.ruff_cache/0.16.3/3306832361351920961`
- `.ruff_cache/0.16.3/5456288279222267804`
- `.ruff_cache/0.16.3/6921677250368324301`
- `.ruff_cache/CACHEDIR.TAG`
- `src/lecture_summary/__init__.py`
- `src/lecture_summary/adapter.py`
- `src/lecture_summary/engine.py`
- `src/lecture_summary/export.py`
- `src/lecture_summary/export_policy.py`
- `src/lecture_summary/llm.py`
- `src/lecture_summary/models.py`
- `src/lecture_summary/public_sources.v1.json`
- `src/lecture_summary/reviewed_week.py`
- `src/lecture_summary/store.py`
- `tests/test_lecture_summary.py`

Zusätzlich ist die unnormalisierte R10-Byteversion von docs/lecture_summary/example-summary.md ausgeschlossen; derselbe Zielpfad erhält nur die deklarierte Ableitung. Das Original bleibt in den bestehenden externen Handoffs/Patches, SHA steht im JSONinventar und neuen Historienindex. Kein Löschauftrag.

Private Originalrohmaterialien, private Summary-/Processingstores, .env/Credentials, Umgebungen, ganze Handoffpakete, Audit-/Rekonstruktionshelfer und evidence/-Snapshots sind weiterhin außerhalb der Veröffentlichung. Dies ist eine Ausschlusspolitik für Inhalte außerhalb der 62, keine Behauptung, alle unbekannten privaten Dateien inventarisiert zu haben. Die neue evidence/-Ablage dieses Pakets wird ebenfalls nicht nach Git kopiert. Es gibt keine Verzeichnisfreigabe, keine Globs zum Staging und kein `git add -A`, `git add .` oder `git add -f`.

## Notwendige Vorcommit-Anpassungen

- Vollständiger Namespace-/Testpfadumzug und exakte Import-/Monkeypatchliste aus dem Integrationsdesign; echter JSONdateipfad in R06-Test Zeile 288 mit umstellen.
- .gitignore auf neuer Basis additiv zusammenführen: `!src/c27_learning_summary/__init__.py` und `!src/c27_learning_summary/public_sources.v1.json`; bisherige Fixture-/historische JSONausnahmen aus R10 erhalten. Bereits existierende Acceptance-Ausnahmen niemals entfernen.
- Zusätzliche exakte JSONausnahmen (keine breite reviews- oder docs-Freigabe):
  - `!/docs/cs50/c27/integration_manifest.v2.json`
  - `!/docs/cs50/c27/reviews/r09/c27_r09_historical_cases.json`
  - `!/docs/cs50/c27/reviews/r10/c27_r10_commit_inventory.json`
  - `!/docs/cs50/c27/reviews/r11/c27_r11_file_decisions.json`
- Historische Publikationswahl P01/S01 im aktuellen Index erklären; nur sechs Schlussleerzeichen in example-summary.md entfernen und nachweisen. Source-, Ref-, Run- oder Reviewidentitäten nicht „bereinigen“.
- Aktuelle Bedienung erklärt Namespace, getrennte Speicher, Offlineprofile, Quellkonfiguration, neue Processingrevision und gültige CLI-/UI-Einstiege; keine alten tmp-Umgebungen voraussetzen. Historische C26-/C27-Laufbefehle sind keine heutigen Autorisierungen.
- Finale 83 Pfade gegen genehmigte Liste vergleichen, Hashes/Modi aktualisieren, eigenes integration_manifest.v2.json erzeugen. Alle neuen Bytes müssen reviewt werden; R10-Hashes binden nur die Ausgangsquellen.

## Ausführungsreihenfolge nach gesonderter Freigabe

1. Konkrete Implementierungsfreigabe dieses Plans einholen. Live-Abgleich/Netz-/Git-/PR-Aktionen separat nur im dann autorisierten Umfang. Aktuelle GitHub-Zielbasis, Reviews/Checks und geschützte/draft Tasks prüfen. Nicht vom 173 Commits alten lokalen master starten.
2. Erhaltenen Quellworktree und Handoffs sichern/identifizieren; neuen eigenen Arbeitsbranch/-worktree von bestätigter Zielbasis verwenden. Das ist späteres Integrationsarbeiten auf Taskbranch, noch kein Merge in master. Abweichungen zum Plan gezielt auflösen, Dateiliste neu binden.
3. C1/C2/C3-Inhalte vollständig vorbereiten; keine Commits in dieser R11. Implementierung lokal prüfen, MD-Normalisierung auf sechs bekannte Stellen begrenzen; aktuelle Dokumentation und finale Pfadhashes erstellen. Keine Rohdaten mitkopieren.
4. Die unten begründeten fokussierten Offlineprüfungen auf dem finalen Inhalt durchführen. Resultate pro Basis/Scope dokumentieren; bei Änderungen nur betroffene Prüfungen erneut ausführen. Kein grünes Gesamtprojekt erfinden.
5. Ausschließlich freigegebene exakte Pfade über eine **explizite Datei-Allowlist** stagen; geplanter Operator kann die maschinenlesbare `exact_planned_target_paths`-Liste nach Review in einzelne Pfadargumente oder NUL-Pfadliste umsetzen. Vorher Status/Index kontrollieren; nachher `git diff --cached --name-status` und Inhalte gegen finale Allowlist/Hashes prüfen. Fremde Staginginhalte blockieren den Commit. `git diff --cached --check` muss ohne neue Whitespaceprobleme bestehen, Hooks nicht umgehen. Erst danach die drei zusammenhängenden Commits erstellen und Commitbäume/Änderungsumfang prüfen.
6. Regulärer PR nach master, die drei Commits zusammen reviewen. Titelvorschlag: „C27: isolate reviewed learning pipeline and preserve validation history“. Beschreibung beginnt mit Trigger/API-Kollision, neuer Namespace, unverändert getrennte Acceptance-APIs, tatsächliche Tests und offenen Produktgates. Auf die gespeicherte fix-Linie als parallelen Vertrag verweisen; keine unbestätigten PRnummern/Live-Checks angeben. PR-Erstellung/Push erfordern später passende Autorisierung.
7. Nach erforderlichen Reviews und Checks gemäß Schutzregeln integrieren, sofern gesondert erlaubt. Kein Umgehen von Reviews und kein Zwang zur Integration des fix-Branches. Nach tatsächlichem Merge Commit-/Tree-/Dokumentinhalte auf lokalem **und live** master verifizieren; bei Squash genaue Inhalte statt bloßer Commit-ID-/Patchähnlichkeit prüfen.
8. Abschlussdokumentation mit tatsächlicher Integration abgleichen und regulär in master sichern. Nur neu für diesen Folgeauftrag erzeugte Git-Artefakte nach sauberem Daten-/Nutzungs-/Ownershipcheck ordentlich entfernen. Dieser vorbestehende Learning-Worktree und Branch, MAINT-Artefakte, Acceptance-Branches und andere Handoffs sind keine Cleanupkandidaten dieses Plans. Bei ungemergtem PR oder Unsicherheit alles erhalten und Pending dokumentieren.

## Fokussierte Regressionen – später, nicht in R11

Keine vollständige Repositoryregression: geändert werden Namespace, Tests, drei bestehende Basisdateien sowie Dokumentation. Für genau diese Änderungen ist die folgende Auswahl begründet. Gegen die endgültige Zielbasis neu ausführen; historische R09-Erfolge beziehen sich auf unveränderte alte Bytes.

Gemeinsame spätere Optionen: bereits vorhandener geprüfter Python-3.12-Interpreter mit Offlineprofil und Streamlit; `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-p tests.offline_guard -p no:cacheprovider`, frische eigene basetemp-Pfade außerhalb des Repos. Keine Installation, Provider oder Downloads impliziert; bestehender 5-GiB-Wächter plus dokumentierte Arbeitsreserve unverändert. Ausführung heute: **keine**.

| Auswahl | Begründung und Erfolgserwartung |
|---|---|
| tests/test_c27_learning_summary.py, tests/test_lecture_summary_ui.py | Alle umgestellten Imports/Monkeypatches, Store/Review, Claimsyntax, SDK-Stubs, UIstart/-downloads; keine ausgefallenen alten Node-IDs nach Umbenennungsabbildung |
| tests/test_c27_reviewed_week.py | revision(), neue Processingkeys, Parent-/Quellenverträge und CLI; externer Fall ohne erneute Rohdatenautorisierung als nicht ausgeführt ausweisen |
| tests/test_c27_remediation_r02.py, tests/test_c27_remediation_r04.py | Storeisolation, 16/17/24/32-Grenzen, Usage/needs_attention, v1/v2/Reviewhash, Parent-/URLregression |
| tests/test_c27_remediation_r06.py, tests/test_c27_remediation_r08.py | Quellenfreigaben, historische 75 URLwerte, URI-/Alias-/Cache-/Revocation-/Canarygrenzen, UI-/CLIexporter; R06-Konfigpfad muss wirklich neue JSONdatei lesen |
| tests/test_c27_summary_coexistence.py | Cold-Import, Schemafamilien, beide Importreihenfolgen, getrennte Storeidentitäten; bei fehlender Acceptance den externen Overlaynachweis gesondert durchführen |
| tests/test_cs50_code_zip.py, tests/test_cs50_zip_inventory.py, tests/test_cs50_material_contracts.py, tests/test_cs50_material_processing.py | code_zip.sha-Entkopplung und vier selektierte CS50P-Verträge; Bytes, Limits und Parser-/ZIPverhalten erhalten |
| tests/test_lecture_summary.py, tests/test_lecture_summary_acceptance.py, tests/test_lecture_summary_contract.py, tests/test_lecture_summary_hierarchy.py, tests/test_lecture_summary_legacy.py, tests/test_lecture_summary_presentation.py | Nur wenn Acceptance auf Zielbasis/gesondertem Dateioverlay vorhanden ist: erhaltene Gegenlinienverträge inkl. RegisteredStorage/Export/Hierarchy, keine Kopie in Learning-PR |

Zusätzliche konkrete Shared-LLM-Prüfung im umgezogenen Backendtest: bounded bleibt ohne Legacysettings, kontrollierter Stub für alten __init__-/Callback-/Cachepfad und unveränderte completion-Signatur. Nur dieser bekannte gemeinsame Produktionsdelta rechtfertigt ergänzte Assertions; keine bloße Spiegelung der Importersetzung.

CLI: einmal synthetischer Offline-E2E mit neuem eigenen Output, Fake→Review→Cache→JSON/Markdown, keine externe Rohdatenauswahl; im Test bereits über run() abgedeckt. Ein CLI-Subprozess-Canary mit unabhängigem Socketguard ist wegen umgestellter Importpfade und vier Ausgabedateien zusätzlich begründet, nicht eine volle neue Realdatenabnahme. Exakte historische sechs R09-Fälle bleiben Referenz; erneute Ausführung mit realen Rohbytes nur nach eigener entsprechender Autorisierung und bei betroffener Basis/Processingänderung. Fake/Fixtures reichen nicht als Ersatz für deren ursprüngliche Echtdatenidentitäten.

Ruff check/format ohne Cache auf geänderten aktiven Pythondateien. Fokussierter Mypy-Diagnosevergleich mit derselben Konfiguration, dokumentierter alter/neuer Namespaceabbildung, ohne Cache im Repository. Kein globaler Mypylauf ohne neuen sachlichen Anlass; 6.104 bleibt historische Schuld, keine heutige Zählung. Dokument-/Manifestprüfungen: JSONsyntax, exakte 83 Pfade, Quellen-/Zielmapping, relativer Quellenbezug, historische Manifestrollen, declared MD-Transformation, keine aktuellen Erfolgsaussagen aus alten Logs.

## Review- und Rollbackstrategie

Architekturreview bestätigt Namespace/Modellgrenzen und bewussten doppelten Funktionsumfang. Securityreview fokussiert F01-Storeketten und R08-Projektionen/Allowlist, getrennt von der unbewerteten Acceptance-Publikationspolicy. Dokumentreview bestätigt Herkunft, historische Statusangaben, lokale Pfade und MD-Ableitung. Kein automatisches approved/passed-Gate zwischen den Modellfamilien.

Vor Commit: Fehler in Taskworktree korrigieren, neu hashbinden und gezielt validieren; keine Nutzerdateien oder fremden Staginginhalte verwerfen. Nach Veröffentlichung/Integration: regulärer **Revert-PR** der zusammengehörenden Produkt-/aktuellen Dokumentänderungen, erforderliche Reviews beachten; kein Reset/Forcepush. Historische Evidenz weiter erhalten und Rollback im Statusindex erklären. Shared-LLM-/code_zip-Rücknahme gegen zwischenzeitliche Änderungen reviewen, keine fremden Fixes zurückdrehen. Stores, Rohresultate, Reviewevents und alte Exporte niemals löschen oder auf alte Bytes umschreiben. Neue Namespace-/Processingrevision benötigt keine destruktive Datenmigration. Bereits erfolgte Netz-/Provideraufrufe wären nicht rückgängig zu machen, sind hier weder geplant noch erlaubt.

## Präzisierung des Hookvertrags: drei historische Dateien ohne finales LF

Die tatsächlich vorhandene .pre-commit-config.yaml aktiviert trailing-whitespace **und** end-of-file-fixer. Eine rein lesende Byteprüfung der 62 Kandidaten findet exakt drei Dateien ohne finales LF: docs/lecture_summary/example-summary.json, docs/lecture_summary/example-summary.md und tests/fixtures/lecture_summary/sources/transcript.json. Eine automatische LF-Ergänzung würde die Zusage bytegleicher historischer JSONevidenz bzw. die hashgebundene synthetische Quelle verändern. Der MD-Entwurf entfernt die sechs Schlussleerzeichen und erhält bewusst seine übrigen Bytes einschließlich fehlendem LF.

Deshalb als ausdrücklich reviewte Konfigurationsänderung **nur am Eintrag end-of-file-fixer** folgende verankerte Ausnahme ergänzen:
```yaml
      - id: end-of-file-fixer
        exclude: '^(docs/lecture_summary/example-summary\.json|docs/lecture_summary/example-summary\.md|tests/fixtures/lecture_summary/sources/transcript\.json)$'
        stages: [pre-commit]
```
Die Regex bezeichnet exakt die drei ausgeschriebenen Pfade, keine Verzeichnisse oder weiteren JSONdateien. Falls auf der späteren Zielbasis bereits eine Hookausnahme existiert, deren semantischen Inhalt erhalten und die drei Pfade explizit ergänzen. Kein SKIP, kein --no-verify, keine globale Hookdeaktivierung. Insbesondere bleiben JSONsyntaxprüfung und trailing-whitespace für diese Dateien aktiv; die sechs MD-Leerzeichen müssen verschwinden. Alle anderen Hookeinträge und deren Versionen bleiben unverändert. Die neue Auswahl beträgt dadurch **83 Zielpfade**, davon C1 34, C2 30, C3 19. Gegen die freigegebenen Bytehashes prüfen, dass Hooks keine historischen Originale/Fixturequellen umgeschrieben haben. Nur lokal bereits vorhandene Hookumgebungen verwenden, keine Downloads aus dem aktuellen Auftrag ableiten. Ist die erforderliche Hookumgebung später nicht vorhanden, als konkrete Validierungsvoraussetzung dokumentieren, nicht umgehen.
