# C27-R09 – Testevidenz

Genau sechs historische Fälle neu ausgeführt: **6 bestanden, 0 fehlgeschlagen, 0 übersprungen**, Exit 0. Keine vollständige Testmatrix, Linter- oder Mypywiederholung. Alle übrigen Ergebnisse sind ausdrücklich geerbte, manifestverifizierte Evidenz.

## Identifikation und Ausführung

Auswahl ausschließlich aus den sechs Failure-Knoten von `remediation-r08.YyLgkxTm/historical-final.xml`, abgeglichen mit dessen Log und Command-JSON. Ursprünglich 117 ausgewählte Fälle: 111 bestanden, sechs kapazitätsbedingt fehlgeschlagen; zwölf Deselektionen bleiben unverändert außerhalb dieses Prüfauftrags. Die frühere breite Auswahl mit überholten Defektcharakterisierungen wird nicht reaktiviert.

| Fall | Historische pytest-Node-ID | R09 |
|---|---|---|
| H01 | `test_cli_entry_r03.py::test_actual_cli_functions_and_repeat` | PASSED |
| H02 | `test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[lecture]` | PASSED |
| H03 | `test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[short]` | PASSED |
| H04 | `test_r05_independent.py::test_unused_root_inventory_entry_preserved` | PASSED |
| H05 | `test_r05_independent.py::test_multilevel_unit_ancestry_with_direct_source` | PASSED |
| H06 | `test_real_r03.py::test_independent_real_data_acceptance` | PASSED |

Vollständige damalige absolute Selektoren, archivierte Quellpfade, ursprüngliche Fehlermeldungen, Zweck und CAP-Überschneidung stehen in `c27_r09_historical_cases.json`. Die Testquellen wurden bytegleich in `historical/` kopiert; die SHA-256-Werte wurden vor und nach Ausführung mit den versiegelten R08-Dateien verglichen. Keine Assertions geändert.

Pytest 9 schreibt für diese außerhalb des konfigurierten Root liegenden Module ein leeres `classname` im neuen JUnit. Die sechs Namen sind eindeutig. Die Zuordnung beruht auf den sechs exakten Datei::Test-Selektoren des ausgeführten Befehls, den eindeutigen Namen im unveränderten JUnit und den bytegleichen Quellen. Das XML wurde nicht nachbearbeitet. Rohbeleg: `historical.xml`, vollständiges Protokoll: `historical.txt`.

## Exakter neuer Testbefehl

```bash
cd /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/tmp/c27-review-r09.rb0c0se8:/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning TMPDIR=/tmp/c27-review-r09.rb0c0se8 XDG_CACHE_HOME=/tmp/c27-review-r09.rb0c0se8/isolated-cache GIT_OPTIONAL_LOCKS=0 R09_AUDIT_OUTPUT=/tmp/c27-review-r09.rb0c0se8/audit-output HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c26g/.venv/bin/python -m pytest -p tests.offline_guard -p tests.profile_policy -p r09_output_guard -p no:cacheprovider -c /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning/pyproject.toml /tmp/c27-review-r09.rb0c0se8/historical/test_cli_entry_r03.py::test_actual_cli_functions_and_repeat '/tmp/c27-review-r09.rb0c0se8/historical/test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[lecture]' '/tmp/c27-review-r09.rb0c0se8/historical/test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[short]' /tmp/c27-review-r09.rb0c0se8/historical/test_r05_independent.py::test_unused_root_inventory_entry_preserved /tmp/c27-review-r09.rb0c0se8/historical/test_r05_independent.py::test_multilevel_unit_ancestry_with_direct_source /tmp/c27-review-r09.rb0c0se8/historical/test_real_r03.py::test_independent_real_data_acceptance --run-external --basetemp /tmp/c27-review-r09.rb0c0se8/pytest-historical --junitxml /tmp/c27-review-r09.rb0c0se8/historical.xml -vv --tb=short -s
```

`historical-command.json` enthält argv, cwd, sämtliche hier gesetzten Umgebungswerte, Exitcode, Laufzeit und freien Speicher. Vorhandene Python-3.12.12-Umgebung nur lesend genutzt. Bytecodes und pytest-Cache deaktiviert, TMPDIR/XDG_CACHE_HOME im neuen Verzeichnis. `tests.offline_guard` verbietet Socket-/DNS-/Listenerzugriffe und Infrastrukturkommandos; der originale R03-CLI-Launcher schützt zusätzlich seine beiden Kindprozesse. `--run-external` entspricht dem historischen Profil und hebt den Offlineguard nicht auf. Keine Installation, Downloads oder echten Provideraufrufe; ausschließlich originale FakeLLM-Pfade.

Zwei historische Belegschreibziele waren fest auf `/tmp/c27-remediation-r08.xqBDn5MQ/historical/{cli-entry-evidence.json,real-data-evidence.json}` gesetzt. Das offen beigefügte Plugin `r09_output_guard.py` leitet ausschließlich diese beiden `Path.write_text`-Ziele nach `audit-output/` um. Alle anderen Aufrufe werden unverändert weitergereicht. Kein Produktaufruf, keine Assertion und kein Limit wird gepatcht. Die zwei Originaldateien bzw. alten Auditverzeichnisse werden nicht beschrieben.

## Kapazität und Fehlerklassifikation

Originales Inventar: reserve_bytes=5.368.709.120 (5 GiB). Unveränderte Implementierung: `src/tools_materials/capacity.py`; keine Änderung oder Simulation des Wächters. Zusätzliche Startreserve 536.870.912 Byte, Startschwelle 5.905.580.032 Byte. Vor dem neuen Lauf: 6309310464 Byte; unmittelbar danach: 6309310464 Byte. Kein neuer Kapazitäts- oder Produktfehler.

Der ursprüngliche finale R08-Lauf hatte nur 4.838.318.080 Byte frei. Fünf Fälle zeigten direkt den Capacity-ValueError; beim CLI verdeckte CalledProcessError das Kindprozess-stderr. `historical-subprocess-capacity.json` belegt für denselben CLI-Pfad ebenfalls `ValueError: Capacity free-space reserve reached`. Es fehlten keine externen Dienste. Die erfolgreichen unveränderten Assertions nach Wiederherstellung ausreichender Kapazität schließen diese sechs historischen Umgebungsblockierungen.

## Fallzuordnung und originale Fehlertexte

### H01 – `test_cli_entry_r03.py::test_actual_cli_functions_and_repeat`

Realen CLI zweimal offline mit TXT-Materialauswahl ausführen: 18 Sections/Claims, zuerst 18 Fakecalls, danach 0; gleiche Run-ID und verifizierter Cache.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; CLI verbarg stderr in CalledProcessError; zusätzlicher identischer Subprozessbeleg weist Capacity free-space reserve reached nach.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_cli_entry_r03.py:22: in test_actual_cli_functions_and_repeat
    reply=subprocess.run(argv,env=env,capture_output=True,text=True,check=True)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/subprocess.py:571: in run
    raise CalledProcessError(retcode, process.args,
E   subprocess.CalledProcessError: Command '['/tmp/c27-test-env/bin/python', '-c', 'import socket,runpy\ndef forbidden(*a,**kw):raise AssertionError("R03 offline CLI")\nfor name in ("connect","connect_ex","bind","listen"):setattr(socket.socket,name,forbidden)\nfor name in ("create_connection","getaddrinfo"):setattr(socket,name,forbidden)\nrunpy.run_module("scripts.c27_reviewed_week",run_name="__main__")\n', '--review-root', '/home/OPERATOR/cs50p-week0-review-RbZ8OQqe', '--output', '/tmp/c27-remediation-r08.xqBDn5MQ/pytest-historical-final/test_actual_cli_functions_and_0/output', '--fake-summary', '--material-id', 'week_material:191f887faf9bf853e27e6e3bbdeedf2744f0629150c757b7f617589ed82ee0ab']' returned non-zero exit status 1.
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: CLI-Erzeugung und Wiederholung in verwandten Fällen; CAP-Einzelaufruf ohne die vollständigen historischen Wiederholungsassertions. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_cli_entry_r03.py`; SHA-256 `d070c280b4026a45c2e123fbeea5e01f108699042316338ca349638a8304f45e`.

### H02 – `test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[lecture]`

Lecture als gültigen Inventarwurzelknoten ohne Parent erhalten; unverändertes Inventar und direkte Quellen nach process_review im Katalog.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; ValueError: Capacity free-space reserve reached vor den nachgelagerten Assertions.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_r05_independent.py:97: in test_valid_unit_roots_keep_direct_sources
    cat,_,_=api.process_review(root,tmp_path/'output')
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/lecture_summary/reviewed_week.py:394: in process_review
    check_capacity(
src/tools_materials/capacity.py:71: in check_capacity
    free_space(root, reserve, additional)
src/tools_materials/capacity.py:67: in free_space
    raise ValueError("Capacity free-space reserve reached")
E   ValueError: Capacity free-space reserve reached
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: Gültige Roots und Graphidentität; unterschiedliche historische Parametrisierung und Testidentität. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_r05_independent.py`; SHA-256 `059bcd04fad9cf52559f928d6a73d5472832b32073f9295b0dafb7135dd4a3c7`.

### H03 – `test_r05_independent.py::test_valid_unit_roots_keep_direct_sources[short]`

Short als gültigen Inventarwurzelknoten ohne Parent erhalten; unverändertes Inventar und direkte Quellen nach process_review im Katalog.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; ValueError: Capacity free-space reserve reached vor den nachgelagerten Assertions.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_r05_independent.py:97: in test_valid_unit_roots_keep_direct_sources
    cat,_,_=api.process_review(root,tmp_path/'output')
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/lecture_summary/reviewed_week.py:394: in process_review
    check_capacity(
src/tools_materials/capacity.py:71: in check_capacity
    free_space(root, reserve, additional)
src/tools_materials/capacity.py:67: in free_space
    raise ValueError("Capacity free-space reserve reached")
E   ValueError: Capacity free-space reserve reached
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: Gültige Roots und Graphidentität; unterschiedliche historische Parametrisierung und Testidentität. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_r05_independent.py`; SHA-256 `059bcd04fad9cf52559f928d6a73d5472832b32073f9295b0dafb7135dd4a3c7`.

### H04 – `test_r05_independent.py::test_unused_root_inventory_entry_preserved`

Zusätzlichen nicht heruntergeladenen Wurzel-Inventareintrag erhalten; verify_review verändert das Inventar nicht und process_review gelingt.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; ValueError: Capacity free-space reserve reached vor den nachgelagerten Assertions.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_r05_independent.py:113: in test_unused_root_inventory_entry_preserved
    api.process_review(root,tmp_path/'output')
src/lecture_summary/reviewed_week.py:394: in process_review
    check_capacity(
src/tools_materials/capacity.py:71: in check_capacity
    free_space(root, reserve, additional)
src/tools_materials/capacity.py:67: in free_space
    raise ValueError("Capacity free-space reserve reached")
E   ValueError: Capacity free-space reserve reached
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: Inventarerhalt in verwandter Root-/Graphprobe; kein identischer Test. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_r05_independent.py`; SHA-256 `059bcd04fad9cf52559f928d6a73d5472832b32073f9295b0dafb7135dd4a3c7`.

### H05 – `test_r05_independent.py::test_multilevel_unit_ancestry_with_direct_source`

Mehrstufige Unit-Abstammung über einen shorts-Container mit direkter Downloadquelle akzeptieren; Verifikation und Processing gelingen.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; ValueError: Capacity free-space reserve reached vor den nachgelagerten Assertions.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_r05_independent.py:118: in test_multilevel_unit_ancestry_with_direct_source
    rewrite(root,mutate);api.verify_review(root);api.process_review(root,tmp_path/'output')
                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/lecture_summary/reviewed_week.py:394: in process_review
    check_capacity(
src/tools_materials/capacity.py:71: in check_capacity
    free_space(root, reserve, additional)
src/tools_materials/capacity.py:67: in free_space
    raise ValueError("Capacity free-space reserve reached")
E   ValueError: Capacity free-space reserve reached
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: Mehrstufige Abstammung und direkte Quellen in verwandten Graphproben; kein identischer Test. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_r05_independent.py`; SHA-256 `059bcd04fad9cf52559f928d6a73d5472832b32073f9295b0dafb7135dd4a3c7`.

### H06 – `test_real_r03.py::test_independent_real_data_acceptance`

Echte lokale Eingaben gegen historische Hashes prüfen; 106 Inventarzeilen/24 erwartete IDs, TXT 18/18, Cachewiederholung und kontrolliertes Chunklimit beider vollständiger HTML-Selektionen.

Ursprüngliche Blockierung: CAPACITY_BLOCKED: damaliger freier Speicher 4.838.318.080 Byte < unveränderte 5.368.709.120 Byte Reserve; ValueError: Capacity free-space reserve reached vor den nachgelagerten Assertions.

Originaler Fehlertext (unverändert aus R08-JUnit):

```text
/tmp/c27-remediation-r08.xqBDn5MQ/historical/test_real_r03.py:15: in test_independent_real_data_acceptance
    single=run(root,processing,fake_summary=True,material_ids=selected)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
scripts/c27_reviewed_week.py:17: in run
    catalog, report, reused = process_review(review_root, output / "processing")
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/lecture_summary/reviewed_week.py:394: in process_review
    check_capacity(
src/tools_materials/capacity.py:71: in check_capacity
    free_space(root, reserve, additional)
src/tools_materials/capacity.py:67: in free_space
    raise ValueError("Capacity free-space reserve reached")
E   ValueError: Capacity free-space reserve reached
```

R08-CAP: keine identische Testidentität. Inhaltliche Überschneidung: Echte lokale Daten und TXT-Verarbeitung; historische Vollauswahl-/Inventarassertions damit nicht identisch belegt. Sie wurde nicht als Erfolg dieses Falles gezählt. R09: **PASSED**, Fall geschlossen. Bytegleiche Testquelle: `historical/test_real_r03.py`; SHA-256 `a3d8bceb6bef893e980233429d720a08cb755520d156367005dfaba4dfa33edd`.

## Geerbte Regressionen und CLI-Nachweise

R08-CAP wurde anhand seines tatsächlichen Testberichts, Command-JSONs und JUnit ausgewertet. Die 23 dortigen Node-IDs entsprechen mengenidentisch den 23 Failure-Identitäten aus R08 `regression-completion.xml`; alle 23 CAP-Ergebnisse sind PASSED. Keine der sechs historischen Node-IDs ist darunter. Der separate frische Canary-Fall ist ebenfalls PASSED. Die vollständigen übernommenen Rohbelege und exakten Befehle stehen in `inherited-evidence/`; Quell-/Kopierhashes in `evidence-provenance.json`.

Der geerbte reale CLI-Aufruf hat Exit 0, processing_reused=false, 18 Fakecalls/18 Claims, zwei neue Exportdateien, downloads=0 und externe llm_calls=0. Er ist kein zusätzlicher pytest-Fall. Der geerbte Canary belegt vier frische öffentliche Dateien, Canary in beiden privaten Inputs und null Leaks. Die sechs Exportdateihashes wurden gegen die tatsächlich archivierten CAP-Dateien nachgerechnet. Es gab keinen Anlass, diese bestandenen Prüfungen erneut auszuführen.

Quelle: `/home/OPERATOR/codex-logs/c27rollout/handoff/remediation-r08.YyLgkxTm/historical-final-command.json`

```bash
/tmp/c27-test-env/bin/python -m pytest -p tests.offline_guard -p tests.profile_policy -p no:cacheprovider -c /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning/pyproject.toml /tmp/c27-remediation-r08.xqBDn5MQ/historical -k 'not characterize_residual and not public_url_original_bytes' --run-external --basetemp /tmp/c27-remediation-r08.xqBDn5MQ/pytest-historical-final --junitxml /tmp/c27-remediation-r08.xqBDn5MQ/historical-final.xml -q
```

Quelle: `/home/OPERATOR/codex-logs/c27rollout/handoff/r08-capacity-completion/regressions-command.json`

```bash
/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c26g/.venv/bin/python -m pytest -p tests.offline_guard -p tests.profile_policy -p no:cacheprovider -c /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning/pyproject.toml 'tests/test_c27_remediation_r04.py::test_valid_inventory_roots_and_multilevel_graph_keep_identity[False]' 'tests/test_c27_remediation_r04.py::test_valid_inventory_roots_and_multilevel_graph_keep_identity[True]' tests/test_c27_remediation_r04.py::test_scope_page_and_lecture_page_may_share_url_without_losing_inventory 'tests/test_c27_reviewed_week.py::test_acquisition_parser_quality_summary_and_cache[0]' 'tests/test_c27_reviewed_week.py::test_acquisition_parser_quality_summary_and_cache[1]' 'tests/test_c27_reviewed_week.py::test_reuse_rejects_tampered_output[0]' 'tests/test_c27_reviewed_week.py::test_reuse_rejects_tampered_output[1]' 'tests/test_c27_reviewed_week.py::test_resume_after_interrupted_publication[0]' 'tests/test_c27_reviewed_week.py::test_resume_after_interrupted_publication[1]' 'tests/test_c27_reviewed_week.py::test_revision_invalidates_processing[0]' 'tests/test_c27_reviewed_week.py::test_revision_invalidates_processing[1]' tests/test_c27_reviewed_week.py::test_real_penguin_week0_read_only 'tests/test_c27_reviewed_week.py::test_explicit_summary_selection[0]' 'tests/test_c27_reviewed_week.py::test_explicit_summary_selection[1]' 'tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[success]' 'tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[needs_attention]' 'tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[rejected]' 'tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[uncertainty]' tests/test_c27_remediation_r02.py::test_cli_invalid_input_is_explicit tests/test_c27_remediation_r02.py::test_cli_cache_miss_does_not_generate_again tests/test_c27_remediation_r02.py::test_reviewed_material_attribution_reaches_export tests/test_c27_remediation_r02.py::test_cli_repeat_exports_current_review_without_overwriting_earlier_export tests/test_c27_remediation_r06.py::test_regular_cli_public_files_and_repeat_are_canary_free --run-external --basetemp /tmp/c27-r08-capacity-completion.tkn3mta2/pytest-regressions --junitxml /tmp/c27-r08-capacity-completion.tkn3mta2/regressions.xml -q
```

Quelle: `/home/OPERATOR/codex-logs/c27rollout/handoff/r08-capacity-completion/fresh-cli-canary-command.json`

```bash
/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c26g/.venv/bin/python -m pytest -p tests.offline_guard -p tests.profile_policy -p no:cacheprovider -c /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning/pyproject.toml tests/test_c27_remediation_r08.py::test_r07_actual_cli_exports --run-external --basetemp /tmp/c27-r08-capacity-completion.tkn3mta2/pytest-fresh-cli-canary --junitxml /tmp/c27-r08-capacity-completion.tkn3mta2/fresh-cli-canary.xml -q
```

Quelle: `/home/OPERATOR/codex-logs/c27rollout/handoff/r08-capacity-completion/real-cli-command.json`

```bash
/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c26g/.venv/bin/python -c 'import socket,runpy
def forbidden(*a,**kw): raise AssertionError("Offline CLI capacity probe")
for name in ("connect","connect_ex","bind","listen"):setattr(socket.socket,name,forbidden)
for name in ("create_connection","getaddrinfo"):setattr(socket,name,forbidden)
runpy.run_module("scripts.c27_reviewed_week",run_name="__main__")
' --review-root /home/OPERATOR/cs50p-week0-review-RbZ8OQqe --output /tmp/c27-r08-capacity-completion.tkn3mta2/real-cli-output --fake-summary --material-id week_material:191f887faf9bf853e27e6e3bbdeedf2744f0629150c757b7f617589ed82ee0ab
```

## F04 und weitere Regressionseinordnung

F04: zwölf R07-Schutzverletzungen im definierten öffentlichen Exportvertrag geschlossen. Elf R08-JUnit-Erfolge umfassen acht mailto/tel-Aliaskombinationen, historische v1/v2-Ergebnisse inklusive Cache/Review/Report sowie echte UI-Downloadpayloads. Die zugehörigen gespeicherten öffentlichen Payloads sind Canary-frei; private Bytes und historische Cachebindungen bleiben laut Belegen erhalten. Den zwölften Vertrag schließt der frische CAP-CLI-Canary; der ältere verifizierte Processingcache-Lauf bleibt gesonderte Evidenz. Kein zweimaliges Zählen der zwölf Szenarien.

Alle 75 freigegebenen URLwerte der unveränderten R08-Fixture stimmen mit den unabhängigen R07/R05-Kompatibilitätsdatensätzen überein. `tests/test_c27_remediation_r08.py::test_approved_urls_and_legitimate_metadata_identity` ist im versiegelten R08-JUnit bestanden; seine unveränderten Assertions prüfen URLbytes, komplette Refmetadaten, JSON/Markdown, Identitäten, Hashes, Locators und private Resultbytes. Kein neuer Lauf wegen bestehender vollständiger Evidenz.

F01/F02/F03/F05 und Parent-Fix: keine nachgewiesene Regression im überprüften Umfang. Konkrete bereits bestandene Identitäten (vollständige maschinenlesbare Zuordnung in `evidence-assessment.json`):

- **F01**: `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[root]`, `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[runs]`, `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[run]`, `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[lock]`, `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[state]`, `test_independent_r03.py::test_unsafe_entries_do_not_change_external_sentinel[raw]`, `test_independent_r03.py::test_descriptor_swap_at_write_or_read[recovery]`, `test_independent_r03.py::test_descriptor_swap_at_write_or_read[cache]`, `test_independent_r03.py::test_descriptor_swap_at_write_or_read[publish]`
- **F02**: `test_independent_r03.py::test_full_generation_boundary_and_duplicates[1]`, `test_independent_r03.py::test_full_generation_boundary_and_duplicates[16]`, `test_independent_r03.py::test_full_generation_boundary_and_duplicates[17]`, `test_independent_r03.py::test_full_generation_boundary_and_duplicates[24]`, `test_independent_r03.py::test_full_generation_boundary_and_duplicates[32]`
- **F03**: `tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[success]`, `tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[needs_attention]`, `tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[rejected]`, `tests/test_c27_remediation_r02.py::test_cli_regular_states_export_and_repeat[uncertainty]`, `tests/test_c27_remediation_r02.py::test_cli_invalid_input_is_explicit`, `tests/test_c27_remediation_r02.py::test_cli_cache_miss_does_not_generate_again`, `tests/test_c27_remediation_r02.py::test_cli_repeat_exports_current_review_without_overwriting_earlier_export`
- **F05**: `test_independent_r03.py::test_usage_aggregate_independent[sequence0]`, `test_independent_r03.py::test_usage_aggregate_independent[sequence1]`, `test_independent_r03.py::test_usage_aggregate_independent[sequence2]`, `test_independent_r03.py::test_usage_aggregate_independent[sequence3]`, `test_independent_r03.py::test_usage_aggregate_independent[sequence4]`
- **Parent**: `test_r05_independent.py::test_download_source_invalid_parent_controlled_at_both_entrypoints[root_source]`, `test_r05_independent.py::test_download_source_invalid_parent_controlled_at_both_entrypoints[unknown]`, `test_r05_independent.py::test_download_source_invalid_parent_controlled_at_both_entrypoints[week]`, `test_r05_independent.py::test_download_source_invalid_parent_controlled_at_both_entrypoints[transcript]`, `tests/test_c27_remediation_r04.py::test_valid_inventory_roots_and_multilevel_graph_keep_identity[False]`, `tests/test_c27_remediation_r04.py::test_valid_inventory_roots_and_multilevel_graph_keep_identity[True]`

Die neuen H02–H05 ergänzen den Parent-Positivnachweis; H01 bestätigt den tatsächlichen CLI-Wiederholungsweg. Die Test-/Produktdateien stimmen mit R08 bzw. der kompletten CAP-Worktreesicherung überein. Globale Mypy-Schuld bleibt 6.104 → 6.104, null neue/entfernte Diagnosen laut versiegeltem Vergleich. **Mypy ist nicht global grün.** Keine neue globale Typprüfung ausgeführt.

## Zählregeln und reale Week-0-Grenze

Nur sechs neue pytest-Erfolge. Der historische finale Prüfbestand wird fallweise von 111 bestanden + sechs blockiert auf 117 bestanden fortgeschrieben. Die alte Regression bleibt durch Ersetzung der 23 Outcomes bei 813 bestanden/2 Skip aus 815 Fällen; die R08-Auswahl umfasst nach CAP 98 eindeutige Erfolge. Diese Bestände werden wegen Überschneidungen nicht zu einer globalen Summe addiert. Die R07-Szenarien und CLI-Subprozesse werden nicht zusätzlich als Tests aufaddiert. Die zwei alten Skips werden nicht als PASSED ausgegeben.

H06 bestätigt erneut 16 historische Eingabehashes, 106 Inventareinträge, 24 erwartete IDs und vier bereits vorhandene Downloads mit 39.845 Bytes. TXT: 18 Sections/Claims und Cachewiederverwendung. Beide vollständigen HTML-Unitselektionen bleiben mit `Chunk limit exceeded; narrow source selection or increase chunk size` blockiert. H06 ist PASSED, weil dies seine ursprüngliche erwartete Assertion ist; damit ist keine Vollwochenverarbeitung bestanden. `full_week_acceptance=false` bleibt ausdrücklich sichtbar.
