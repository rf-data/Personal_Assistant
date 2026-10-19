# C24-05-C2: Synthetische Integration, Realpilot weiter blockiert

19.10.2026. Backendbasis `master` `df0f9a74de1d5936f20ee7f9f77cef350cde16c4`;
eigener Branch `feat/c24-05c2-real-pilot`. UI-`main`
`90816a1578bcf67739ee9acaa483c1635aa0c44b`. Auf GitHub erneut geprüft:
[A/#87](https://github.com/rf-data/Personal_Assistant/pull/87),
[B1/#90](https://github.com/rf-data/Personal_Assistant/pull/90) und
[B2/UI-#7](https://github.com/rf-data/personal-assistant-ui/pull/7) sind gemergt.
Der UI-Merge besitzt denselben Baum `e693f1d1975544319458d0772a054630406bc782`
wie der zuvor geprüfte B2-Implementierungscommit `c183329`.

**Ergebnisumfang:** Neue ausführbare synthetische Integrationstests für die
vorhandenen C23-/FTS5-/A-/B1-Verträge, keine neue Produktpipeline. Die Auftraggeber-
antwort dieses Pakets erlaubt ausdrücklich nur isolierte synthetische Stores.
Keine bestätigte reale Sourcefreigabe, privaten Pilotroots oder abgeschlossenen
menschlichen Goldreviews. Keine realen Originalzugriffe, Originalimporte oder
Indexbuilds auf Realmaterial; keine Downloads, Modellinferenz, Qdrantaufrufe oder
tatsächlichen menschlichen Bestätigungen.

## Audit der drei offenen Draft-PRs

Live-APIprüfung einschließlich Dateidiffs und vorhandener Implementierungen am
19.10.2026. Alle drei richten sich gegen Backend-`master` und bleiben unverändert
offen; keine Merge-/Close-/Deployaktion.

| PR / Branch / geprüfter Head | Tatsächlicher Inhalt | Abhängigkeiten und Grenze |
| --- | --- | --- |
| [#72](https://github.com/rf-data/Personal_Assistant/pull/72), `feat/c21q-qdrant-transcript-pilot`, `3a42b1675dffe823edc179a347fa97dd1a096fd0` | 26 geänderte Dateien: Qdrant-Compose-/Auth-/Healthguards und Runbooks, read-only `cs50_pilot.py`, CLIinventur/-alias und synthetische Sourcepfadtests. C21-Q.1 dokumentiert **keinen** Runtimepfadfix. | Keine nachgewiesene freigegebene laufende Instanz oder echte Modellinferenz. SDK, immutable Modellrevision/-gewichte, konkrete Instanz/Collection/Transport- und Betriebsfreigaben separat. Historisches SRT weiterhin D06-gesperrt. Kein erforderlicher Bestandteil des lokalen FTS5-Piloten. |
| [#88](https://github.com/rf-data/Personal_Assistant/pull/88), `feat/c24-05b-human-review-workflow`, `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` | Zwei Dokumentationsdateien: Review-ADR und Plannachtrag; **keine** Persistenz, API, UI oder ausführbaren Reviewtests. | Sein damaliges A-Mergegate ist historisch. Die technische Umsetzung ist inzwischen über B1/#90 und UI-B2/#7 integriert; ein Merge dieses Architekturentwurfs implementiert keine zusätzliche Funktion. Fachliche Realfreigaben bleiben separat. |
| [#89](https://github.com/rf-data/Personal_Assistant/pull/89), `feat/c24-05c-real-corpus-pilot`, `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d` | Zehn Metadaten-/Dokumentationsdateien: bestehender CorpusManifest/GoldDataset, Bereitschaft r1/r2, Bericht und Plan. **Keine** Review-, FTS5- oder Realpilot-Runtime. | Die frühere B-Implementierungsblockade ist aufgehoben, Source-/Roots-/Review-/D06-/D07-Gates bestehen. Elf Planungszeilen sind keine elf Dateien. C2 verwendet genau dessen dokumentierte Metadaten, ohne seinen Merge vorauszusetzen. |

Die acht bisherigen r1-/r2-JSONdateien wurden aus dem geprüften #89-Head
byteidentisch übernommen und werden über ihre ursprünglichen Dateimanifeste
validiert. Der bestehende C-Bericht erhält einen klaren aktuellen Verweis; sein
historischer Text bleibt erhalten. Kein anderer Runtimecode aus einem Draft wird
übernommen. Historische Testzahlen von #72/#88/#89 zählen nicht als neue C2-Läufe.

## Aktuelle Bereitschaft und reale Stopgrenze

[CorpusManifest r3](c24_05c/r3/corpus_manifest.v1.json),
[leerer GoldDataset r3](c24_05c/r3/gold_references.v1.json),
[Bereitschaft r3](c24_05c/r3/pilot_readiness.v1.json),
[Dateimanifest r3](c24_05c/r3/manifest.json).
Datasetversion `c24-05c2-readiness-2026-10-19-r3`, Bodydigest
`ff49500f5b7ba63c68c9919590f22bcd3bbfc5955d24286df1b953d7effb0658`,
Vorgänger `11a0dd008a5f3fb68998d57b642bd2d3f93aaa272a52b6e292aaf4f06e517040`.
Keine neue konkurrierende Korpus-/Goldmodellklasse.

Alle elf realen Inventarmetadaten mit fünf deklarierten HTMLpfaden bleiben
unverändert; null freigegebene vollständige Bundles, null bestätigte Realgold-
referenzen, null tatsächliche Pilotfragen/-reviews/-tasks. Die bekannten IDs und
Rawhashes sind **deklarierte Metadaten**, nicht erneut geprüfte Originalbytes.
Alle Realmetriken bleiben null/not_evaluable, nicht 0 Prozent. Vector/Hybrid und
reale Sicherheitsszenarien sind not_checked. SRT bleibt blocked_source_binding.
Die neue Revision entfernt ausschließlich die inzwischen überholte technische
B-Blockade und ergänzt die ausdrücklich bestätigten fehlenden Roots/Rechte.

Der geplante reale Einstieg ist **eine noch auszuwählende und freizugebende Quelle**,
fünf Parsingstellen und fünf vorab festzulegende fachliche Fragen. Es wurde keine
Quelle ausgewählt, keine reale Frage erfunden und kein echter Reviewauftrag ohne
Quellenfreigabe angelegt. Offene tatsächliche menschliche Reviewtasks: **0**.

Vor dem nächsten Realzugriff benötigt der Betreiber einen konkreten Auftrag mit:

1. Source-ID, exakten ausdrücklich erlaubten Raw-/Parsed-/Receipt-/Plan-/Bilddateien,
   Rawhash/Größe, belegter damaliger Parserrevision und Konfiguration. Keine
   Revision aus HEAD, kein Ersatzreceipt, kein impliziter Verzeichnisscan.
2. Sourcebezogener Nutzungs-/Evaluationsentscheidung mit Beleg, Entscheider/Datum,
   erlaubten Schritten, Laufzeit/Widerruf, D07 und gegebenenfalls D06. Das historische
   Python-0-SRT bleibt bis zur separaten kanonischen Bindungsentscheidung ausgeschlossen.
3. Verbindlichen privaten Content-/Index-/Evaluation-/Ergebnisroots, vorhandenen
   Source-/Course-/Principalgrants und separater Reviewer-/Approverzuweisung. B1
   verlangt zusätzliche explizite Reviewpermissions; B2-Widgets erzeugen keine Rechte.
4. Tatsächlichen menschlichen Originalreviews, bestätigten positiven/negativen
   Regionen, vollständigem Originalpool und geklärten Mehrdeutigkeiten. Fragen und
   Akzeptanzkriterien vor Suchlauf festlegen. Ein Parser oder Codex bestätigt kein
   reales Gold. Hier muss der Prozess auf echte Nutzeraktionen warten.

Danach vorhandene B-Gates, B1-API und integrierte B2-Ansicht verwenden. Größere
Originale/fehlender sicherer Renderer behalten die dokumentierten B1/B2-Grenzen;
kein direkter Dateizugriff als UIersatz. Reale Abnahme ausschließlich durch einen
tatsächlich berechtigten Approver, nie aus grünen synthetischen Tests ableiten.

## Implementierter technischer Ablauf

`tests/test_review_fts_pilot.py` benutzt vorhandene Bundle-/Reviewtesthilfen und
die tatsächlichen autorisierten APIs. Handgeschriebenes **synthetisches** Codeoriginal
mit fünf Zeilen, Emoji, Combiningzeichen und CRLF; keine CS50-Originaldatei wird
geöffnet. `material()` und `verify_material_bundle()` prüfen den vorhandenen
Parser-/Receipt-/Planvertrag; der Implementierungsbeleg ist ausdrücklich synthetisch.

1. Temporäre getrennte ContentStore-, FTS5-, EvaluationStore- und Jobroots;
   Source-/Raw-/Parsed-/Parserbindung und tatsächlicher FTS5-Rebuild.
2. Fünf statisch vorher verfasste Queries und ihre erwarteten positiven Zeilen
   vor dem ersten Suchlauf persistieren: hello, world, answer, print und missingterm.
   Handgeschriebene Konstanten, keine Treffer- oder Parserausgabe als Goldquelle.
3. Fünf Parsing-Vollblockreviews plus 25 querygebundene positive/negative
   Regionsreviews über authentifizierte B1-Application. Automatische Bestätigungen
   sind ausschließlich **synthetische Testaktionen**, keine menschlichen Urteile.
   Fünf separate Poolbestätigungen decken sämtliche fünf Originalzeilen ab.
4. B1 exportiert direkt die bestehenden A-/C23-Goldmodelle. Das vorhandene
   C23-Evaluationsgate verarbeitet den Parsingexport gegen das verifizierte
   CorpusManifest und einen expliziten read-only ContentStorehandle.
5. Tatsächliche lexikalische Suche mit unveränderter Generation, k=4, Owner-/
   Course-/Sourcescope. Alle Treffer bis k, vollständiges Seitenende, Original-
   substring, Text-/Raw-/Versionbindung und Locatoren prüfen. Backendfingerprint
   aus tatsächlichem SQLite-/Tokenizer-/Rankingvertrag. Öffentliche Suchgeneration
   ist die vorhandene HMAC-Projektion der internen Build-ID, keine neue Generation.
6. Tatsächliche SearchResultPages in bestehende A-QueryResults einbetten. B1
   persistiert den unveränderten A-Bericht; dessen Digest entspricht dem direkten
   A-Evaluator. Wiederöffnung von Index, ContentStore und Gateway erhält Ergebnis-
   bytes, Export, Report und Revisionsketten ohne Rebuild/Reparse. Identische
   Requests sind idempotent; andere Intents überschreiben keinen Report.
7. Privates temporäres `snapshots/`: Corpus, Queryplan, Gold, Ergebnisse, Parsing-
   und Retrievalreport mit exakten Dateihashes und exklusiver Ausgabe. Das ist
   ausführbare Testevidenz, kein neuer produktiver Pilotrunner oder Freigabevertrag.

Zusätzliche neue Integrationsfälle prüfen: fehlender vollständiger Goldpool bleibt
nicht evaluierbar; widersprüchliche positive/negative Anker sperren Export;
Quarantäne/Tombstone sperren Gold und liefern FTS5-stale_index; ein Contentgrant
ist kein Reviewrecht und sein Widerruf sperrt Suchtreffer; Fehler **nach** dem
Reportinsert und **vor** SQLcommit rollt Events/Heads vollständig zurück, danach
kann derselbe Request erfolgreich wiederholt werden. Ein Metadatenreadtest lässt
ausschließlich die zwölf benannten Bereitschaftsdateien zu, keine Originalreads.

Die bestehenden B1-/A-/FTS5-Suiten liefern zusätzlich ihre jeweiligen CAS-/
Parallelitäts-, Provenienz-, ACL-, Leakage- und Integritätsfälle. Ein gespeicherter
Report allein beglaubigt keine ausgeführten Sicherheitsbelege: A behält ausdrücklich
`live_authorization=not_checked` und `real_acceptance=blocked`. Kein neuer manueller
Realabnahmeentscheid und kein positiver Release durch diesen Testablauf.

## Tatsächliche Prüfung

Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, BeautifulSoup 4.11.2,
System-Pytest 7.2.1, Ruff 0.16.0; vorhandene Umgebung ohne Installation/Sync.
Pytest-7-AST-Warnungen unter Python 3.12 zählen nicht als Skips.

| Lauf | Tatsächliches Resultat | Grenze |
| --- | --- | --- |
| Neue C2-Datei, abschließender Entwicklungslauf | **8 passed / 0 failed / 0 skipped**, 54,42 s | Neue Integration und Metadaten, ausschließlich synthetisch |
| Gemeinsame C2-/B1-/A-/Projektions-/FTS5-/C23-Prüfung mit Originalzugriffs-Guard | **239 passed / 5 failed / 0 skipped / 1 deselected**, 414,53 s | Alle acht neuen und alle 45 B1-Fälle grün; fünf synthetische SRT-Fälle am zu weit gefassten Guard gesperrt, keine Produktfehler daraus ableiten |
| Gezielte Nachprüfung mit präzisiertem Guard | **9 passed / 0 failed / 0 skipped / 123 deselected**, 23,08 s | Alle fünf zuvor gesperrten Fälle plus vier überlappende Parameterfälle; nicht zum Sammellauf addieren |
| Abschließende Verschärfung des Reportabbruchtests | **1 passed / 0 failed / 0 skipped**, 20,45 s | Zusätzlich belegt: injizierter Fehler trifft den bereits eingefügten SQLhead tatsächlich; überlappt den Achter-/Sammellauf |
| Eingefrorener unabhängiger A-Replay | **identischer Report und Digest** | Nur vorhandene Snapshotbytes gelesen; kein Store/Import/Rebuild/neuer Suchlauf |
| Ruff Check / Format Check / diff check | **erfolgreich** | 18 betroffene bzw. wiederverwendete Pythondateien; keine Änderung an Runtime/Dependencies |

Kein erneuter gemeinsamer 244er-Grünlauf, keine Gesamtrepositoryabnahme und keine
neue UI-/Browser-/OIDCproviderabnahme werden behauptet. Die beiden Laufgruppen
zeigen die betroffenen Regressionen nach Korrektur des Testguards; dessen Fehler
wurden nicht als Masterfehler klassifiziert. Die Produktmodule und vorhandenen
Tests sind gegenüber der angegebenen Basis unverändert.

Tatsächliches gemeinsames Präfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python
```

Neue Fälle mit diesem Präfix:

```sh
-m pytest -q --disable-warnings -p no:cacheprovider \
  tests/test_review_fts_pilot.py --basetemp=/tmp/c2405c2-fifth
```

Der gemeinsame Lauf verwendete dieselbe Pythonumgebung über den lokalen
`/tmp/c2405c2-guarded-tests.py`-Runner und folgende `pytest.main`-Argumente:

```sh
-q --disable-warnings -p no:cacheprovider \
 tests/test_review_fts_pilot.py tests/test_evaluation_store.py \
 tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py \
 tests/test_content_index_projection.py tests/test_content_fts.py \
 tests/test_cs50_material_evaluation.py \
 -k 'not test_versioned_inventory_has_no_confirmed_real_gold' \
 --basetemp=/tmp/c2405c2-guarded-release
```

Der ausdrücklich abgewählte vorhandene Inventartest öffnet reale versionierte
HTMLrohdateien. Er wurde **nicht ausgeführt**. Ein zuvor begonnener Lauf ohne
diese Auswahl wurde noch während der B1-Datei angehalten; keine erfolgreiche
Gesamtausführung oder Realinventur wird daraus abgeleitet.

Der lokale Python-Audithook verweigert `open` für `docs/course_sources`, `data`
und `.env*` des Checkoutroots. Die SRT-Testhilfe benötigt ausschließlich den
genauen versionierten Metadatenpfad
`docs/course_sources/cs50/cs50_lecture_plan.v1.json`: dafür eine explizite Ausnahme,
keine Verzeichnisausnahme. Native `os.open(..., dir_fd=...)`-Auditereignisse enthalten
keinen Directory-FD. Der präzisierte Runner bindet solche relativen Pfade über
`/proc/self/fd/<fd>` und einen threadlokalen ContextVar an das tatsächliche private
Testverzeichnis, bevor der Hook prüft. Andernfalls erschien dessen synthetisches
`data` fälschlich als Checkout-`data`. Beide Guardfehler sperrten vor dem Lesen;
keine Originalfreigabe wurde erweitert. Die Runnerkopien und Logs bleiben privat
außerhalb des Repositories, keine neue Produkt-CLI oder Zugriffsschnittstelle.

Gezielte Nachprüfung mit demselben präzisierten Runner, denselben vier bestehenden
Dateien `test_content_retrieval_integration.py`, `test_content_index_projection.py`,
`test_content_fts.py`, `test_cs50_material_evaluation.py` und:

```sh
-q --disable-warnings -p no:cacheprovider \
-k 'test_verified_bundle_projection_fts_gold_report_reopen or test_srt_exact_cues_and_overlapping_original_times or test_actual_build_search_restart_provenance or test_repeated_build_paging_filters_and_generation_switch or test_srt_cue_text_and_known_locator' \
--basetemp=/tmp/c2405c2-scoped-plan
```

Entwicklungsläufe der neuen Datei fanden korrigierte Testannahmen: öffentliche
statt interne Indexgeneration, vorhandener Unavailable-/stale_index-Vertrag,
LocatorDTO-Anhang versus autoritativer Locator, read-only C23-Handle und
unterschiedliche Metriknenner bei ausschließlich negativem Gold. Kein Parser-/
Runtimefix und keine abgeschwächte Integritätsassertion. Ein zusätzlicher
Planmetadaten-Nachlauf war noch durch die Directory-FD-Verwechslung gesperrt
(4 passed / 5 failed); erst obiger Neuner-Lauf prüft den korrigierten Guard.
Nach der abschließenden Ergänzung der expliziten Post-Insert-Assertion wurde nur
der betroffene Node mit dem gemeinsamen Präfix erneut ausgeführt:
`-m pytest -q --disable-warnings -p no:cacheprovider
tests/test_review_fts_pilot.py::test_failed_report_commit_rolls_back_and_same_request_retries
--basetemp=/tmp/c2405c2-final-insert`.

Ruff Check und Format Check mit vorhandenem Ruff für:
`tests/test_review_fts_pilot.py`, `src/evaluation_store`,
`src/model_evaluation/{content_retrieval,material_evaluation}.py`,
`src/tools_evaluation/{evaluate_materials,evaluate_retrieval}.py`,
`src/tools_rag/{content_index,content_fts}.py`, `tests/review_support.py` und
die sechs bestehenden Testdateien des gemeinsamen Laufs; anschließend
`git diff --check`. Keine vollständige Backend-/Frontendtestsuite, nativen
PDFparser-, realen Vektor-/Hybrid-, Dienst-, Last- oder Deploymenttests.

## Eingefrorene synthetische Evidenz und Reproduktion

[Tatsächlicher A-Report](c24_05c/r3/synthetic/report.v1.json),
[Laufbindung](c24_05c/r3/synthetic/run_binding.v1.json) und
[exakte Dateihashes](c24_05c/r3/synthetic/manifest.json).
Reportdigest `9645d5946516e7b26622e713983841b9dfd125ea0b431b1b4a2ceff930deb252`.
Der Maschinenreport ist der unveränderte bestehende A-Vertrag, kein neues
Evaluationsmodell. Laufbindung enthält tatsächliche Source-/Parsed-/Parser-IDs,
Queryplan-/Reviewsnapshotbindung und exakte private Snapshotdateihashes; keine
privaten Originaltexte, Hostroots oder Tokens.

**Ausschließlich synthetische Vertragswerte, keine reale Suchqualität:** fünf
auswertbare Queries mit k=4. Precision-Makro: 1,25 / 5 = 0,25; Recall/MRR/nDCG:
je 4 / 4 = 1. Die bestätigte vollständig negative Frage ist für Precision
auswertbar; Recall/MRR bleiben bei ihr `not_determinable/no_relevant_gold`, nDCG
`not_determinable/zero_idcg`. Deshalb unterschiedliche Makronenner, kein Ersatz
fehlender Werte durch null Prozent und kein Gesamtqualitätswert.

Die privaten eingefrorenen synthetischen `gold.json`, `results.json`,
`query-plan.json`, `corpus.json`, Parsing-/Retrievalreports und ihr Dateimanifest
bleiben mit den Testlogs außerhalb Git erhalten. Reproduktion des bestehenden
A-Evaluators ohne Storezugriff oder neuen Suchlauf:

```python
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet, RetrievalResults, EvaluationConfig,
)
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval

# frozen_gold/frozen_results ausschließlich aus verifiziertem eigenen Snapshot.
dataset = ContentRetrievalEvaluationSet.model_validate(frozen_gold["retrieval"])
results = RetrievalResults.model_validate(frozen_results)
report = evaluate_retrieval(dataset, results,
    evaluation_config=EvaluationConfig(schema_version=1))
assert report.digest == expected_report_digest
```

Der ausgeführte unabhängige Replay prüfte zuerst alle Snapshotdateihashes und
dann vollständige Reportgleichheit, nicht nur die Kennzahlen. Ein neues Import-
oder Reviewereignis bindet neue Zustände; keine Behauptung gleicher Digests über
beliebige Neuimporte/Serverzeiten hinweg. Synthetische Pytestroots werden nach
Abnahme entfernt; eigener Worktree und private Belege bleiben für den offenen PR.
Andere Worktrees, Nutzerdateien, Originalbestände und virtuelle Umgebungen bleiben
unverändert. Keine automatischen Merges oder Schließungen der drei Drafts.
