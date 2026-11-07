# M1 – Validierung und Provenienz

Stand 07.11.2026. Implementierung, Architekturentscheidung, Freigabevertrag und
Bedienung: [one-source-summary-m1.md](one-source-summary-m1.md).
**TECHNICAL PASS für die synthetische M1-Integration:** 438 Tests bestanden;
Realmaterial, Liveprovider und Defaultbranch-Integration bleiben nicht freigegeben.

## Git- und Bestandsschutz (Implementierungsauftrag)

Vorhandener Worktree `Personal_Assistant-cs50-summary-mvp`, vorhandener Branch
`feat/cs50p-lecture-summary-mvp`. HEAD und `origin/master` sind lokal
`1839850249c17d855ee12bd1e0b632352ce09ffd`. Der lokale `master`-Ref ist älter
und wurde nicht verwendet oder verändert. Keine neuen Branches/Worktrees,
keine Änderungen an PR #171. Keine Commits, kein Push, PR oder Merge.
Alle Implementierungsdateien liegen uncommittiert im Zielworktree. HEAD ist die
Ausgangsrevision und wird nicht als Commit der M1-Implementierung ausgegeben.

Bestehender MVP-Operator, MVP-Tests, historische MVP-Dokumente und Implementierungen
von ContentStore, ContentReader, MaterialProcessor und Handoff bleiben bytegleich
zur Basis. Sämtliche Laufdaten stammen aus neu angelegter eigener Synthetik in
separaten `/tmp`-Roots. Testmanipulationen falscher Freigaben und Rawbytes betreffen
ausschließlich diese eigens angelegten Fixtures. Bestehende reale Roots, Approvals,
virtuelle Umgebungen, private historische Evidence und fremde Tasks bleiben erhalten.

## Exakte C27-Provenienz

Sieben Dateien selektiv aus Commit
`dc26c72ffb8f1abd4a032601c524616840154171`, keine Historienintegration.
Pfade relativ zu `src/c27_learning_summary/`:

| Datei | SHA-256 der übernommenen Datei |
| --- | --- |
| adapter.py | `74b4ef683942245cef113becb3aba95df0bece5a792675a3c2b87c4558a8ea58` |
| engine.py | `71ac1e9c01672c3f44f207189f28d38f7761086ef10841419b70b642a57cdd73` |
| models.py | `1cf4b1c4e62fd37667cd871b585b002aec0a1bb4acf797a4b8275f002cef6230` |
| export_policy.py | `93703bc6680ee4538e879a9e1f9c0623fec8775c3afd6714ecbeae623bcefb8f` |
| store.py | `7dc1e40ebe9acf9cb01fb39a5bcc51f9e896889baf74863790fc5314270b45e2` |
| export.py | `928c6d4a258a61d3c1c0e608c6105b35fc8aff68dcd766f2edf1c134eb9796da` |
| llm.py (nur Offline-Teil) | `ae7a15664678a4d231f78a605132e687c7a988424f9b1f0dd5993c557085d7e7` |

Die ersten sechs Dateien sind bytegleich zur genannten Commitfassung. `llm.py`
entspricht deren Prefix vor `class LiteLLMSummaryModel`, mit abschließendem
Zeilenumbruch nach Ruff-Formatierung. SHA-256 der vollständigen Ursprungsdatei:
`32a26c3421a5573dc4662262407ccbe6432d05bc0cd5506805d08338c7f21463`.
Die Liveklasse ist vollständig entfernt. Keine öffentlichen URL-Freigaben,
Review-Pipeline, CLI/UI, Discovery-, Acquisition- oder Batchingmodule übernommen.

Die Regressionsteilmenge stammt aus
`ca567bfac85be3626d63e73463f3c2438317bbec`,
`tests/test_c27_learning_summary.py` (Originalhash
`7ba8ee440b2aa18fb5d1c145cc095add4d48224d345302c90fee6d2aec5e1c34`).
34 Funktionen/Klassen einschließlich Fixtures/Helfern wurden ausgewählt; ihre
Bodies und Assertions bleiben inhaltlich unverändert, Imports/Fixturepfad und
Formatierung sind angepasst. 47 parametrisierte Offlinefälle werden ausgeführt.
Fünf Funktionen wurden vor dem Lauf wegen nicht übernommener Dependencies nicht
in die neue Suite aufgenommen: CLI-End-to-end, zwei Live-LLM-Abstraktionstests,
Material-Handoff-Ingestion sowie ein gemischter Limit-/Liveprovider-Test.
M1 prüft seinen vollständigen Kontext und Handoff-Bestand separat. Es werden keine
Skips/Xfails als Ersatz für fehlgeschlagene Tests eingeführt.

Die synthetische Katalogfixture ist bytegleich zu
`tests/fixtures/lecture_summary/catalog.json` aus demselben Commit; neuer Pfad
`tests/fixtures/cs50_summary_m1/c27-catalog.fixture`, SHA-256
`43f28d94713e8f4c04c0b58f5e22436babe4ee61765d29cc4a9e7e2d708b6f12`.
Die abweichende Dateiendung vermeidet die allgemeine Ignore-Regel für neue JSONdateien.

## Ausführungsumgebung und Entwicklungsnachweise

Neue isolierte Umgebung `/tmp/cs50-summary-m1-env`, Python 3.12.12.
Keine Installation mit Netz, keine Updates bestehender Umgebungen. Eine `.pth`
verweist nur auf vorhandene gecachte Drittbibliotheken; BeautifulSoup, soupsieve
und PyMuPDF samt Metadaten wurden aus einer bestehenden Umgebung in die neue
Testumgebung kopiert. Kein fremder Projektcode wurde als Testimport verwendet.
Dies ist keine erneut ausgeführte frische Wheelhouse-Installation; die bestehende
F2-Abnahme wird weder verändert noch als neuer M1-Nachweis ausgegeben.

| Komponente | Version |
| --- | --- |
| Python / SQLite | 3.12.12 / 3.50.4 |
| Pydantic / pytest | 2.13.4 / 9.1.1 |
| httpx | 0.28.1 |
| BeautifulSoup / soupsieve | 4.15.0 / 3.0.4 |
| charset-normalizer / PyMuPDF | 3.5.1 / 1.28.2 |
| Ruff | 0.16.3 |

`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
`-p no:cacheprovider` und neue isolierte `--basetemp`-Verzeichnisse gelten für
alle Testläufe. Socket-Verbindungen und DNS werden in M1-Tests abgewiesen.

Erster Entwicklungsversuch: Collectionfehler durch `strict=True` auf einem
Pydantic-Literal; null Tests ausgeführt. Korrigiert durch expliziten Vorabvalidator
analog zum bestehenden MVP. Keine Abnahme dieses Fehlversuchs.
Danach **35 M1-Tests bestanden in 134,09 s**
(`/tmp/cs50-summary-m1-dev-02.xml`) und separat **47 C27-Regressionen in 16,68 s**
(`/tmp/cs50-summary-m1-c27-01.xml`). Nach zusätzlicher unabhängiger Sliceprüfung
bestanden vier gezielte Fälle in 14,05 s (`/tmp/cs50-summary-m1-probe-03.xml`).
Diese Zwischenläufe ersetzen nicht den gemeinsamen Schlusslauf der finalen Fassung.
Ein Aufruf von `python -m ruff` konnte den nur gecachten Binarypfad nicht finden;
die tatsächlichen Ruff-Prüfungen verwenden deshalb direkt dessen bestehendes Binary.

## Finale Implementierungsbytes und gemeinsamer Lauf

| Gegenstand | SHA-256 |
| --- | --- |
| src/cs50_summary_mvp.py | `676836aacdc7bd13b634110cff5467704d0cf951557d3bf6df7e53ae62ff25e4` |
| aktueller pfadgebundener MVP-/M1-Codefingerprint | `ae0a79ebfce7610aee7e0b3b0a6177c274d21d5751b9ae118100532ad711419e` |
| tests/test_cs50_summary_mvp.py | `78bf950f54e6b58efc7d79182db26affd9dbeb044b8a15631988cf0988250778` |
| tests/test_cs50_summary_c27_regression.py | `e48b93378ba815d84f48ed9c32059666d62eae209d8facd44c897d4b9493e371` |

Zusammen mit dem echten HEAD wird dieser Fingerprint in jeder neu erstellten
synthetischen Import- und Summaryfreigabe gebunden. Der historische-Code-Test
erstellt bewusst eine eigene synthetische Importfixture unter einer simulierten
früheren Identität. Anschließend muss die unveränderte MVP-Suche HOLD liefern,
während ausschließlich die separat neu freigegebene M1-Verarbeitung zulässig ist.
Er verändert keine tatsächliche historische Freigabe.

Nach der letzten Implementierungsänderung gestarteter Schlusslauf:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /tmp/cs50-summary-m1-env/bin/python -m pytest \
  tests/test_cs50_summary_mvp.py tests/test_cs50_summary_c27_regression.py \
  tests/test_cs50_learning_mvp.py tests/test_content_store_adapters.py \
  tests/test_content_store_integrity.py tests/test_content_read_contracts.py \
  tests/test_content_fts.py tests/test_content_retrieval_integration.py \
  tests/test_content_index_projection.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_html.py tests/test_cs50_material_html_semantics.py \
  tests/test_cs50_material_quality.py \
  -m 'not external_integration' -q -p no:cacheprovider \
  --basetemp=/tmp/cs50-summary-m1-final-01 \
  --junitxml=/tmp/cs50-summary-m1-final-01.xml \
  > /tmp/cs50-summary-m1-final-01.log 2>&1
```

Collection: 439 Fälle, 438 ausgewählt. Ausdrücklich abgewählt ist ausschließlich
der bestehende `test_optional_original_python_notes_read_only`, da Realmaterial
ohne neue Freigabe nicht zulässig ist. Er zählt nicht als bestanden oder als Skip.
Die Testsuite prüft echten Import, HTML-v2-Parsing, Quality/Handoff, Publication,
FTS sowie M1 anschließend mit gesperrten Parsing-/Download-/Index-/Publication-
Einstiegspunkten. Jeder akzeptierte Claim wird über Ref, Block-ID, vollständigen
Textbereich, ParsedVersion, Rawhash und originale Locators nachgewiesen.
Weitere M1-Fälle prüfen falsche und doppelte Approvalfelder, Ablauf, Codeidentität,
Versions-/Rawkonflikte, fehlende Slices, sämtliche Reader-Seiten bei mehr als
100 Blöcken, lange TextWindow-Folgen, Whitespace-Lücken, Outputbestandsschutz,
veränderte Quellen während Erzeugung und fehlende automatische Wiederholung
unbelegter Teilruns. Der Restart erfolgt in einem separaten Pythonprozess;
identische Wiederholung und Restart erhalten Quell- und Zielinventare bytegleich.

Ergebnis des einmaligen gemeinsamen Schlusslaufs: **438 passed, 1 deselected
in 483,16 s**, Exitcode **0**. JUnit: 438 Fälle, Laufzeit 483,117 s,
**0 Failures, 0 Errors, 0 Skips**, keine Xfails/Xpasses. Nach der letzten
Implementierungsänderung war kein Korrektur- oder Wiederholungslauf nötig.

| Datei | Bestandene Fälle |
| --- | ---: |
| test_cs50_summary_mvp.py | 42 |
| test_cs50_summary_c27_regression.py | 47 |
| test_cs50_learning_mvp.py | 50 |
| test_content_store_adapters.py | 49 |
| test_content_store_integrity.py | 16 |
| test_content_read_contracts.py | 14 |
| test_content_fts.py | 47 |
| test_content_retrieval_integration.py | 6 |
| test_content_index_projection.py | 41 |
| test_cs50_material_processing.py | 8 |
| test_cs50_material_html.py | 7 |
| test_cs50_material_html_semantics.py | 17 |
| test_cs50_material_quality.py | 94 |

| Nachweis | SHA-256 |
| --- | --- |
| /tmp/cs50-summary-m1-final-01.xml | `211848b4d0c2c0075d814eb2d57ca39983739f640a83ef268ede13670c9a89fa` |
| /tmp/cs50-summary-m1-final-01.log | `df7478d349b238f1d3141a66df314e4a19561269e057c0612a17750619b51904` |

Ruff 0.16.3 `check --no-cache` und `format --check --no-cache` bestanden auf
allen zehn neuen Pythondateien: sieben C27-Module, M1-Operator und zwei Testsuites.
Die Prüfung bestehender Git-Diffs und einzeln sämtlicher 13 neuer Dateien mittels
`git diff --no-index --check /dev/null <datei>` ergab keinen Whitespace-Befund.
Die Markdown-Links wurden gegen die tatsächlichen lokalen Dateien geprüft.
Nach dem Testlauf blieb der tatsächliche Implementierungsfingerprint identisch
zum hier dokumentierten und in den synthetischen Freigaben gespeicherten Wert.
Danach wurden ausschließlich diese neuen Dokumente um Nachweise ergänzt.

Synthetischer End-to-End-Root aus genau diesem Schlusslauf:
`/tmp/cs50-summary-m1-final-01/test_import_summary_every_clai0/`.
Die eigenen HTMLbytes sind 380 Bytes lang; die gespeicherte Summary enthält
fünf Claims aus allen fünf geeigneten Blöcken, fünf verarbeitete/zitierte Refs,
null unzitierte Refs und `review_status=unreviewed`. Der Test verbietet nach dem
Import weitere Parser-, Download-, Index- und Publication-Aufrufe; beim Cache-
Wiederabruf ist zusätzlich FakeLLM gesperrt. Ein separater CLI-Prozess liefert
denselben vollständigen Bericht bei unveränderten Dateiinventaren.

| Identität dieses synthetischen Falls | Wert |
| --- | --- |
| Source-ID | `resource:fd35721e7e07c012647b4a4bbd790e76c2980a071444f2eb1fa76d8289aa48cd` |
| Raw-SHA-256 | `ddfe8f2912719302b753cf194bc073d781bc78be553c0cf503aef4f2c9e646d7` |
| ParsedVersion | `content_version_v1:f07b304136d0b17c4ed7977367df524784af1698811274483568974cf979ea16` |
| M1-Cacheidentität | `77011bade63ff1bcf6b22bb7932fcbbcae1e7ddd89349fcedabc9ec15a2fde83` |

Die Raw-/Sourceidentität entspricht absichtlich der wiederverwendeten eigenen
synthetischen MVP-Fixture. Es ist ein neu erzeugter Root mit neuer Freigabe und
neuer ParsedVersion unter aktuellem Code, kein Wiederabruf historischer Runtime.

## Grenzen und empfohlene Folgeaufträge

FakeLLM liefert mechanische wörtliche Auszüge. Technische Belegung beweist weder
fachliche Korrektheit noch eine didaktische Synthese. Jede Summary bleibt
`unreviewed`; das C27-Label `ready_for_review` ist keine Freigabe. Coverage bedeutet
vollständige geeignete Eingabe, nicht Vollständigkeit einer realen Vorlesung.
Nur das ausgewählte HTMLmaterial wird erfasst; bei mehreren Lecturebindungen
verwendet der interne Einquellenkatalog die erste vorhandene Bindung und erweitert
die Quellenauswahl nicht. Bilder, rein strukturelle Blöcke und alternative
Projektionen werden mit Gründen inventarisiert. Bildinhalte werden nicht interpretiert.

32 Slices sind eine harte Obergrenze des gewählten Kerns. Lange Quellen können
deshalb HOLD ergeben. Code-/Formelslices können bei ungünstigen Schnittgrenzen
die Syntaxprüfung nicht bestehen; keine stillen Ersatzclaims. Widersprüche,
abgewiesene Claims, unbekannte Quellzustände und beschädigte Caches erfordern
Operatorprüfung; Teilruns bleiben erhalten. Beide Roots sind private lokale
Dateisystemartefakte für denselben vertrauenswürdigen User, kein neues
Authentifizierungs- oder Signatursystem. Kooperierende Prozesse müssen die Locks
respektieren. Fehler-/HOLD-Fälle ändern keinen bestehenden Root zur Reparatur.
Der bekannte SQLite-B1 aus PR #171 wird durch lokale Tests weder geschlossen noch
als reproduziert behauptet. Keine Produktions-, Last- oder Deploymentabnahme.

Für eine echte HTMLquelle: separater Auftrag mit konkret geprüfter Herkunft,
Nutzungsfreigabe, exakten Rawbytes und neuem Importroot plus aktueller
ProcessingApproval. Danach neue SummaryApproval für genau diese veröffentlichte
Version und aktuellen Code, eigener Summaryroot und fachlicher Claim-/Coverage-
Review. Keine Aktualisierung historischer Freigaben; für nicht mehr gültige
historische Importfreigaben HOLD und gesonderte Operatorentscheidung.

Für einen begrenzten LiteLLM-Smoke: eigener Folgeauftrag zur Providerintegration,
ausdrückliche Upload-/Providerfreigabe für konkrete Slices und aktuellen Code,
genaues Modell und Endpunkt, höchstens ein Aufruf ohne Retry, harte Input-/Output-,
Zeit- und Kostenlimits. Rawantwort, Usage, Finish-Reason, Claim-Belege und
Coverage prüfen; bei Truncation oder unbelegten Claims HOLD. Dieser Stand hat
absichtlich keine Liveproviderklasse und führt einen solchen Smoke nicht aus.

## Lifecycle nach Implementierung (historischer Stand)

Implementierung und Nachweise bleiben zur Review im vorgegebenen Worktree.
Defaultbranch-Integration blieb **pending**, weil Commit/Push/PR/Merge im damaligen
Implementierungsauftrag ausdrücklich verboten waren. Daher kein vollständiger Lifecycle-Abschluss
nach AGENTS.md und keine Branch-/Worktree-Löschung. Keine Git-Artefakte angelegt
oder entfernt. Neue Testumgebung, Logs und synthetische Roots unter `/tmp` bleiben
als Entwicklungsnachweise erhalten; keine bestehenden Daten gelöscht.

Abschließende lokale Prüfung nach Implementierung: derselbe Branch/HEAD, `origin/master` unverändert
auf der vorgegebenen Basis, lokales `master` unverändert auf `c1007efdbac3c1544020f328a3a1347e481797ba`.
Getrackter und gestagter Diff sind leer. Genau 13 neue Lieferdateien:
zwei M1-Dokumente, sieben C27-Module, M1-Operator, zwei Testsuites und eine
synthetische Katalogfixture. Keine Runtime-, Approval- oder Originalmaterialdatei
liegt unter diesen neuen Git-Lieferdateien. PR #171 wurde zum Schluss erneut
lesend geprüft: weiterhin offen, Draft und nicht gemergt, derselbe Head
`929fb1e1aa821e779b7d7ad327cf5a323666bd31`. Keine PR-Mutation ausgeführt.


## Release-Vorbereitung: CI-Konflikt mit PR #171

Folgeauftrag vom 07.11.2026. [PR #171](https://github.com/rf-data/Personal_Assistant/pull/171)
wurde erneut ausschließlich lesend geprüft: offen, Draft, nicht gemergt,
Head weiterhin `929fb1e1aa821e779b7d7ad327cf5a323666bd31`, Base-SHA weiterhin
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Der tatsächliche Live-Defaultbranch
`master` steht dagegen inzwischen auf `1839850249c17d855ee12bd1e0b632352ce09ffd`,
identisch zu M1-HEAD und lokalem `origin/master`. Keine Ref-Aktualisierung ausgeführt.

Der konkrete Konflikt liegt in `ci/c27-stage0/validate.py` aus PR #171:
`verify_candidate(root, data)` ruft `verify_prerequisites(root, data)` auf. Dieses
verlangt neben den 40 Prerequisite-Hashes und zwei zurückgestellten Profilpfaden
die Abwesenheit aller 55 Pfade aus `data["stage1"]["allowlist"]` auch im aktuellen
Checkout. Sieben M1-Lieferdateien überschneiden sich damit:

```text
src/c27_learning_summary/adapter.py
src/c27_learning_summary/engine.py
src/c27_learning_summary/export.py
src/c27_learning_summary/export_policy.py
src/c27_learning_summary/llm.py
src/c27_learning_summary/models.py
src/c27_learning_summary/store.py
```

In einer eigenen Kopie der unveränderten sechs Stage-0-Produkte, 40 Prerequisites
und des vollständigen Reviewpakets besteht der Originalvalidator zunächst.
Nach Overlay der 13 M1-Dateien scheitert dieselbe Prüfung reproduzierbar mit:
`Stage-1 path exists: src/c27_learning_summary/adapter.py`.
Es gibt keinen Dateischnitt zwischen den 13 M1-Dateien und den sechs
Stage-0-Produkten, aber eine unvereinbare globale CI-Abwesenheitsregel.
Das ist ein lokal reproduzierter Vertragskonflikt, kein behaupteter fehlgeschlagener
GitHub-Actions-Lauf: M1s Ausgangsbasis enthält diesen Validator noch gar nicht.
Der Workflow aus #171 prüft außerdem explizit den jeweiligen PR-Head, nicht einen
zukünftigen kombinierten Merge-Stand. Ein grüner Einzel-Head schließt dieses Gate
deshalb nicht.

Der [minimale Vorschlag und kombinierte Testplan](one-source-summary-m1.md)
begrenzen die Stage-1-Abwesenheit auf den festen historischen BASE-Snapshot, vor
und nach Anwendung des exakten Stage-0-Patches. Aktuelle Produkt-/Prerequisite-
Hashes und sämtliche historischen Pins bleiben wirksam. Der Vorschlag steht nur
im M1-Dokument; kein Schreiben nach PR #171, kein produktiver Validatorpatch und
keine Veränderung historischer Manifeste, Reviewtests oder Evidence.

### Neue begrenzte Vorschlagsprüfung

Eigene Hilfsdateien und Kopien ausschließlich unter
`/tmp/cs50-m1-release-prep-8zhipA/`. Ausführung mit dem vorhandenen Python 3.12.12,
`-I -S -B`, ohne Bibliotheksinstallation oder Netz. Die Probe prüft Funktionen
des Validators; sie ist kein vollständiger Workflow-/Merge- oder M1-Produktlauf.

| Neue Prüfung | Ergebnis |
| --- | --- |
| Originalkandidat ohne M1-Overlay | PASS |
| Originalkandidat mit 13 M1-Dateien | Erwartete Ablehnung am Stage-1-Pfad |
| Vorschlag mit unverändertem Stage-0-Paket plus M1 | PASS: `verify_review` und `verify_candidate` |
| Historischer BASE-Export, BASE-Produkt-Hashes, exakter Patch und Kandidatenprüfung | PASS; Stage-1-Abwesenheit vor/nach Patch |
| Eigene historische Stage-1-Negativoverlays | Alle 55 Pfade einzeln abgewiesen |
| Produktions-AST-Smoke für historischen Snapshot und aktuellen Overlay | Beide PASS, einschließlich tatsächlichem Linux-`renameat2` |
| Aktuelle Validator-Vertragstests als angepasste temporäre Kopie | 13 Tests, 0 Fehler, 0 Failures, 0 Skips |

Bei den 13 Vertragstests prüft der frühere globale Stage-1-Ablehnungstest nun
positiv `verify_candidate` und negativ `verify_stage0_isolation`. Der falsche
Head wird am echten M1-Checkout geprüft, da die temporären Dateikopien kein
Git-Repository sind. Alle anderen Testkörper bleiben unverändert. Die Tests
ändern nur eigene Kopien; die sechs Produkt- und 40 Prerequisite-Manipulationen,
Reviewpaket-/Rebinding-, Pfad-, Symlink-, Modus- und Profilablehnungen bestehen.
Die zusätzlichen 55 Prüfungen zählen nicht als 55 separate unittest-Testmethoden.
Die vollständige CLI mit richtigem kombiniertem HEAD und die gezielten Tests
beider neuen historischen Aufrufstellen stehen im gemeinsamen Release-Gate aus.

| Temporärer Nachweis (relativ zur obigen Wurzel) | SHA-256 |
| --- | --- |
| stage0-coexistence-proposal.patch | `4934c1f539840c1d7fc90c57ccd1577f4402420ab540f31fc02c11f2b56018a6` |
| probe-result.json | `286dec775d70a66bdd6a477310a3f2587e2bc7db237b8beaf7779dc524095b9c` |
| contract-tests.log | `9569b50dbb0ab49d26f9b450434e706615a3c21ed12d62b7555fd645a56221e0` |
| probe.py | `d6d5e5eef8a993d4678b156844190818a24fe2e3d41703eba5f8d649afe1008c` |

Die elf nicht dokumentarischen M1-Dateien sind bytegleich zum geprüften Stand;
aktueller pfadgebundener Implementierungsfingerprint weiterhin
`ae0a79ebfce7610aee7e0b3b0a6177c274d21d5751b9ae118100532ad711419e`.
Original-Log und JUnit des 438-Tests-Laufs wurden erneut gegen ihre dokumentierten
Hashes geprüft; JUnit bestätigt 438 Fälle, null Fehler/Failures/Skips. Dieser
Lauf wird nicht als neu ausgeführt oder als kombinierte Stage-0-/M1-Abnahme
umdeklariert. Nach ausschließlich dokumentarischen Änderungen kein erneuter
vollständiger Produktlauf; die neue Validatorprobe ist separat ausgewiesen.

### Konkretes Commit-/Draft-PR-Paket und Bestandsschutz

Die [exakte 13-Dateien-Allowlist samt Commit-/Draft-PR-Text](one-source-summary-m1.md)
ist verbindlich. Nur diese zwei bereits vorgesehenen M1-Dokumente werden im
Folgeauftrag erweitert. Keine zusätzliche Repositorydatei, keine Runtime- oder
Freigabedatei, keine CI-Datei und keine bestehende getrackte Datei kommt hinzu.

Das Vorbereitungspaket liegt unter `/tmp/cs50-m1-release-prep-8zhipA/`:
separater `m1.index`, eigene `objects/`, `m1-13-files.patch`,
`m1-staging-summary.json`, `m1-files.sha256`, `git-add-m1.sh` sowie
`draft-pr-body.md`. Der separate Index wird von HEAD aufgebaut und ausschließlich
mit den 13 expliziten Pfaden befüllt; `git diff --cached --name-status` muss dort
exakt 13 Additionen liefern. Whitespace, Datei-/Blobhashes und unveränderter echter
Index werden geprüft. Die Zusammenfassung enthält den vorbereiteten Tree und
Patchhash. Diese temporäre Vorschau ist kein Commit und ersetzt kein tatsächliches
Staging im gemeinsamen Index, der außerhalb der beschreibbaren Workspace-Grenze liegt.

Der echte Index bleibt leer, die 13 Lieferdateien bleiben dort untracked. Keine
Commits, kein Push und keine Draft-PR-Eröffnung ausgeführt; Commit und Draft-PR
sind konkret vorbereitet. PR #171 und master bleiben unverändert. Vorhandene
Branches und Worktrees sind keine Artefakte dieses Folgeauftrags; es wurden keine
neuen angelegt oder entfernt. Sämtliche Vorschlagskopien/Logs verbleiben unter
`/tmp`, damit die Vorbereitung nachprüfbar bleibt.

### Verbleibende Release-Gates und Lifecycle

| Gate | Status und notwendiger Nachweis |
| --- | --- |
| M1-Scope/Review | 13-Dateien-Paket vorbereitet; tatsächlicher Commit, Push, Draft-PR und reguläre Review stehen aus. Vor Veröffentlichung finale Allowlist und echte Revisionsbindung erneut prüfen. |
| CI-Koexistenz | HOLD bis separate, geprüfte Umsetzung des dokumentierten Validator-/Vertragstestvorschlags; historische Pins und Stage-0-Produktbytes dürfen dabei nicht geändert werden. Keine Änderung an #171 in diesem Auftrag. |
| Gemeinsame technische Regression | HOLD bis vollständiger Lauf auf echtem kombiniertem Git-Stand gemäß Testplan, einschließlich echter Publication, ContentStore, Reader, Freigaben und zusätzlicher Fehlerfälle. Einzelprüfungen ersetzen ihn nicht. |
| SQLite-B1 | Weiterhin offen wie in #171 dokumentiert. Kein neuer Nachweis seiner Behebung; bei Auftreten Fehler/Evidence erhalten und separat entscheiden. |
| Realmaterial/fachliche Abnahme | HOLD bis konkrete Herkunfts-/Verarbeitungsfreigabe, exakte Rawbytes, neue codegebundene Approvals und fachlicher Claim-/Coverage-Review vorliegen. Synthetik ist keine Realfreigabe. |
| Liveprovider/Deployment | Separater Auftrag mit konkreten Provider-/Upload-/Budgetgrenzen beziehungsweise Betriebsabnahme erforderlich; der M1-Kern bleibt FakeLLM-only. |
| Defaultbranch-Integration/Cleanup | Pending: reguläre PR-Integration der Änderungen und Dokumente noch ausstehend; task-spezifisch kein Merge und keine Änderung an master. Bestehenden Branch/Worktree erhalten. |

Die Vorbereitung ist geliefert; Release und allgemeiner Lifecycle-Abschluss nach
AGENTS.md bleiben pending. Dokumente liegen ausschließlich im vorgesehenen
M1-Paket und müssen später mit ihm regulär nach master integriert werden.
Keine automatische Merge-Aktion und keine Branch-/Worktree-Bereinigung.
