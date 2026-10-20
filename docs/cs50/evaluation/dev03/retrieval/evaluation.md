# DEV-03C – Synthetischer Retrieval- und E2E-Nachweis

20.10.2026, bestehender Backend-master `7a4f2be`, UI-main `a7da646`.
**Technische Vorbereitung; Realstatus `blocked_pending_source_authorization`.**
Kein Originalzugriff, reales Gold, Realimport oder Realindex. DEV-02-Import #127
und UI #17 sind offen; vollständiger UI-Importpfad bleibt blockiert. Die bereits
integrierten C23-Adapter, C24-05-A/B1/B2 und FTS5-Verträge sind unabhängig nutzbar.

## Tatsächlich ausgeführter Versuch

`scripts/acceptance/dev03_retrieval.py` ist ein fest begrenztes Acceptance-Rezept
über die vorhandene C2-Testfixture `tests/test_review_fts_pilot.py`, keine neue
Pipeline/Evaluationsklasse. Es akzeptiert keine Source-/Input-/URLpfade, sondern
nur neue externe synthetische Workspace- und Ergebnisroots. Keine Abhängigkeit
von ungemergten DEV-03A/B-Dateien oder -Modellen. Ausführung:

```sh
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python \
-m scripts.acceptance.dev03_retrieval \
--workspace /tmp/dev03c-synthetic-first --output /tmp/dev03c-reports-first
```

Fünf vor Retrieval geschriebene Codezeilen mit Emoji/Combiningzeichen/CRLF, fünf
unveränderte Queries `hello`, `world`, `answer`, `print`, `missingterm`, k=4.
C23 verifiziert den vollständigen synthetischen Codebundle und publiziert exakt
gebundene Raw-/Source-/Parsed-Versionen. Ein ausdrücklich angeforderter lokaler
FTS5-Build bindet die vorhandene IndexSelection; kein Gatewayimport wird behauptet.

Das integrierte B1 erzeugt fünf Parsingreviews und 25 Queryregionsreviews sowie
fünf gesonderte Poolbestätigungen. Alle Aktionen/Reviewer sind **synthetische
Testmarker**, keine menschlichen Urteile. Die Konstanten stehen unabhängig von
Parser-/Trefferergebnissen fest. Originalpool: sämtliche fünf Zeilen pro Query.
Goldexport benutzt ausschließlich vorhandene Parsing-/Retrievalmodelle.

Alle fünf Queries laufen sowohl über den echten scoped FTS5-Adapter als auch
über `POST /v1/content/search` im tatsächlichen C16-Application-Vertrag. Vollständige
SearchResultPages, Generation, Scope, Textsubstring, Raw-/Parsed-/Locatorbindung
müssen exakt übereinstimmen. B1 persistiert den unveränderten C24-05-A-Bericht;
sein Digest entspricht der direkten bestehenden Evaluationsfunktion.

Nach Wiederöffnung von Content-/Index-/Job-/Evaluationpfaden bleiben Resultbytes,
Exports und Reports identisch. Kein versteckter Rebuild oder Reimport beim Replay.
Originalbytes und ContentStore-Inventar bleiben unverändert. Ein zusätzlicher Test
führt die bestehende Offline-CLI gegen die eingefrorenen Daten aus: Reportbytes
identisch, erneute Publikation ins vorhandene Ziel abgewiesen.

## Tatsächliche synthetische Kennzahlen

[Bestehender Report](run/evaluation/report.v1.json),
[Kurzfassung](run/evaluation/summary.md),
[Dataset/Versionen/Gold](run/data/dataset.v1.json),
[tatsächliche Resultseiten](run/data/results.v1.json),
[Dateimanifest](run/manifest.json).

| Metrik | Aggregierter Zähler | Querynenner | Ausgeschlossen | Wert |
| --- | ---: | ---: | ---: | ---: |
| Precision@4 | Summe der Querywerte 1,25 | 5 | 0 | 0,25 |
| Recall@4 | Summe 4 | 4 | 1 ohne relevantes Gold | 1 |
| MRR@4 | Summe 4 | 4 | 1 ohne relevantes Gold | 1 |
| nDCG@4 | Summe 4 | 4 | 1 mit IDCG=0 | 1 |

Macroaggregation gemäß vorhandenem A-Vertrag. Pro Query teilt Precision durch
k=4, auch wenn weniger Treffer vorhanden sind; `print` besitzt zwei relevante
Zeilen, die drei anderen positiven Queries je eine. Die No-Relevant-Query liefert
0/4 Precision, aber **keine Nullwerte** für Recall/MRR/nDCG: diese bleiben
`not_determinable` und sind aus deren Macro-Nennern ausgeschlossen.

Fünf evaluierbare synthetische Queries, keine realen Messwerte. Das sind
Arithmetik-/Vertragsnachweise für einen fünfzeiligen Testfall, keine Aussage zur
Qualität echter mathematischer Dokumente, zum Kurskorpus oder einer Modellleistung.
`real_acceptance=blocked`, `live_authorization=not_checked` bleibt im Offlinebericht
korrekt erhalten. Unauffällige Snapshot-/Locatorprüfungen ersetzen keine aktuelle
Liveberechtigung. Separate ACL-/Quarantänetests stehen unten, keine erfundene
Securityquote oder fachliche Freigabe aus Rankingzahlen.

## Fehlerklassifikation und konkrete Folgeschritte

| Klasse | Tatsächlicher Befund / Grenze | Folge |
| --- | --- | --- |
| Parsingverlust | Für dieses fünfzeilige Codeoriginal nicht beobachtet; alle Zeilen/Bytes geprüft | Keine Übertragung auf PDF/HTML/Formelqualität |
| Fehlende Indexaufnahme | Nicht beobachtet; vollständiger synthetischer Pool/Versionsbindungen vorhanden | Bei Realfreigabe dieselbe explizite Selection prüfen |
| Falsche Version | Nicht beobachtet; Version-/Konfigurations-/Generationsevidenz gebunden | Neue SourceVersion benötigt neue Evaluationsrevision |
| Kein relevanter Treffer | `missingterm` ist ausdrücklich ein No-Relevant-Fall, kein Rankingfehler | Goldabdeckung nicht aus Trefferliste ableiten |
| Relevanter Treffer außerhalb Top-k | In diesem kontrollierten Set nicht beobachtet | Keine reale Recallbehauptung |
| Falscher Text/Locator | Beide echten Schnittstellen exakt gegen Quellenblöcke/Locatoren geprüft | Gezielte Negativfälle im integrierten A-Testpaket |
| Berechtigung verhindert Zugriff | Widerruf/fehlende Reviewpermission/Quarantäne in C2-Verträgen getestet | Erwartete Zugriffssperre nicht als Retrievalverlust zählen |
| Technischer Fehler/Timeout | Keine Querytimeoutbehauptung aus fehlendem Realzugriff | UI-/Runtimebefunde separat dokumentieren |

P0 bleibt die konkrete Einzelgenehmigung für höchstens drei Originale und deren
Roots, Nutzungs-/Aufbewahrungs-/Weitergaberechte, D06/D07 sowie benannte echte
Reviewer/Approver und unabhängig bestätigtes Gold. P1: freigegebene Quellen am
Original auf Parsing-/Visual-/Formelstellen prüfen. Erst danach sinnvolle reale
Rankingbaseline; Parser/Chunking/Ranking währenddessen einfrieren. Kein neuer
Provider, kein neuer Evaluator und keine pauschale Planungsrunde erforderlich.

## Tests und Ausführung

Bestehendes Python 3.12.12, Pydantic 2.13.4, SQLite 3.50.4, Pytest 9.1.1.
Keine Installation oder externen Dienste. Tatsächlicher Befehl:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
-q -p no:cacheprovider tests/test_dev03_retrieval.py tests/test_review_fts_pilot.py \
tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py \
--basetemp=/tmp/dev03c-contracts
```

**75 passed / 0 failed / 0 skipped**, 183,78 s. Ein neues Acceptance-Rezept-/CLI-
Replay/Hash-/No-Overwrite-Szenario plus acht bestehende C2-Fälle und 66 bestehende
A-Fälle. Tatsächliche C23-/B1-/FTS5-Nutzung, unvollständiger Pool, widersprüchliches
Gold, ACL/Quarantäne/Tombstone und Reporttransaktionsrollback; keine statischen
Erfolgsmocks. Netzwerkzugriff in den Tests verboten. Neue CLI separat erfolgreich
mit fünf synthetischen Queries ausgeführt. Report-/Dateihashes geprüft; keine
privaten Hostroots in versionierten JSONdateien. UI-Nachweis folgt separat.

## Tatsächliche UI-Vertragsprüfung

Eigener unveränderter, detached Checkout von UI-main `a7da646` unter
`/tmp/dev03-ui-reference`; keine Nutzung der ungemergten DEV-02-UI. Bestehende
Review-/Such-AppTests gegen den tatsächlichen integrierten Backendstand dieses
C-Worktrees (`7a4f2be`, neue Acceptance-Dateien werden vom Backend nicht importiert):

```sh
REVIEW_BACKEND_REPO=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03c \
REVIEW_BACKEND_PYTHON=/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/personal-assistant-ui/.venv/bin/python -c \
'import sys; sys.path.append("/usr/lib/python3/dist-packages"); import pytest; raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","tests/test_review_ui.py","tests/test_search_ui.py"]))'
```

**20 passed / 1 failed / 0 skipped**, 297,31 s. Der erste Reviewtest hatte einen
AppTest-Scriptstarttimeout nach unveränderten 25 s, noch vor Tasköffnung/Annotation.
Keine Fehlklassifikation als Gold-/Parsing-/Rankingfehler und keine Parser-/
Produktkorrektur dafür. Der exakt gleiche Node
`tests/test_review_ui.py::ReviewUITests::test_actual_app_review_confirm_restart_history_gold`
bestand anschließend isoliert mit demselben Präfix und unveränderten Limits:
**1 passed / 0 failed / 0 skipped**, 10,81 s. Kein grüner kompletter 21er-Wiederlauf
behauptet und keine Erhöhung der Timeouts. Bei Wiederholung kalten UI-Start gezielt
profilieren; aus diesem einmaligen Timingbefund wird kein bestätigter Runtime-
Datenfehler abgeleitet. Bestehendes C25-Browserabnahmeissue bleibt offen.

Diese Tests verwenden tatsächliche Streamlit-App/Backends/Gates/FTS5 mit eigenen
synthetischen Szenarien; sie sind **kein** menschlicher Review des obigen Experiments
und keine Browser-/Realabnahme. UI Python 3.12.12, Streamlit 1.65.0, Pydantic 2.14.0,
vorhandenes System-Pytest 7.2.1 hinten an sys.path; kein Dependencydownload. AST-/
unittestwarnungen sind keine Skips. Netzwerkrequests werden zum tatsächlichen
isolierten HTTPHandler transportiert, keine statischen Erfolgsmocks.

Ruff Check/Format Check für beide neuen Pythondateien und diff check erfolgreich.
75er-Backendlauf, 21er-UIlauf und isolierter Recheck bleiben getrennte, teilweise
überlappende Nachweise. Ausgeführter technischer Vorbereitungsumfang:
`technical_preparation_complete – real_acceptance_blocked`.
Dauerhafte Berichte liegen im PR; master-Integration ist bis zum regulären Merge
noch offen. Eigener Branch/Worktree bleibt deshalb bestehen. MAINT und alle
anderen historischen/aktiven Arbeiten bleiben unberührt, keine Auto-Merges.

Aktualisierte Integrationsbeobachtung während des Auftrags: Backend-Import #127
ist inzwischen extern auf master `61ad351` gemergt. UI #17 bleibt offen. Die hier
protokollierte synthetische Baseline verwendet unverändert den zu Beginn integrierten
`7a4f2be`-Stand und keine ungemergten Source-Import- oder DEV-03-Folgepakete.
Realverarbeitung bleibt unabhängig davon durch die Betreiberentscheidung gesperrt.

Vor Veröffentlichung wurde master `2c51da6` lokal integriert: enthält inzwischen
DEV-02B #127 und DEV-03A #128, beide extern gemergt. Das neue C-Replayszenario
wurde danach erneut unverändert ausgeführt:
`tests/test_dev03_retrieval.py --basetemp=/tmp/dev03c-current-replay` mit obigem
Backendpräfix, **1 passed / 0 failed / 0 skipped**, 47,45 s. Kein Import aus dem
noch ungemergten DEV-03B, keine neue Corpus-/Gold-/Reportmodellklasse. Frühere
75er-/UIläufe behalten ihren expliziten historischen Basisbezug, nicht addieren.

## Abschließender Status

Die vorhandene Fixture-Implementationsrevision `"a" * 40`, Reviewer und
Reviewdatum sind deklarierte synthetische Testmarker, keine reale historische
Parserrevision oder menschliche Originalbestätigung. Code-/Backendversionen und
Ausführungen bleiben explizit wie oben protokolliert.

A [#128](https://github.com/rf-data/Personal_Assistant/pull/128) ist integriert;
alle acht Dateien exakt auf master geprüft. Sein ausschließlich taskeigener
Worktree/Branch/Trackingref und der unveränderte eigene UI-Testcheckout wurden
nach sauberem Status und vollständiger Nichtnutzungsprüfung normal entfernt.
Keine fremden/MAINT-/DEV-02-Worktrees oder primären Checkouts geändert.
B [#130](https://github.com/rf-data/Personal_Assistant/pull/130) und dieser C-PR
[#129](https://github.com/rf-data/Personal_Assistant/pull/129) sind offen;
Branches/Worktrees bleiben deshalb erhalten. Project #1 enthält A/B/C jeweils
exakt einmal. Keine Issueanlage/-schließung, keine Status-/Workflowmutation.
Reale Korpus-/Retrievalabnahme #107/#108 bleibt offen.

Für Realverarbeitung fehlen weiterhin ausschließlich die konkret ausgefüllten
Einzelfreigaben/Roots/Nutzungs-/Aufbewahrungsrechte, D06/D07 und tatsächlich
benannte berechtigte Reviewer/Approver mit unabhängig bestätigtem Originalgold.
Keine zusätzliche allgemeine Architektur-/Planungsrunde erforderlich.
