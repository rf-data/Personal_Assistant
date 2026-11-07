# One-Source Retrieval – Validierungsnachweise

Aktueller Stand: Prompt 25, 06.11.2026. **F2 geschlossen, TECHNICAL PASS**
für die frische scoped Python-3.12.12-Umgebung und den Offline-Schlusslauf.
Der Abschnitt „Prompt 25“ dokumentiert AC1–AC14 und Integrationsgrenzen;
Prompt-20/24-Zahlen und damalige HOLD-Entscheidungen bleiben historische Ergebnisse. Redaktion ersetzt persönliche Pfade durch
Platzhalter; die separat gesicherten Originalberichte bleiben unverändert.

## Historischer Prompt-20-Nachweis

Stand: 2026-11-06. Architektur, Verträge, CLI-Beispiele und der vor Implementierung
festgelegte Testplan stehen in [one-source-retrieval-mvp.md](one-source-retrieval-mvp.md).

## Git-Ausgangslage, Umfang und Integrationsstatus

Worktree: `<repository>`.
Branch: `feat/cs50p-one-source-retrieval-mvp`.
HEAD, Merge-Base und vorhandenes `origin/master`:
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Ausgangsstatus sauber.
PR #171 war bei der lesenden GitHub-Prüfung offen, Draft und nicht integriert;
seine master-Base entsprach diesem Commit. Keine seiner Änderungen übernommen.

Vier neue Dateien, keine Änderung vorhandener Implementierungen oder Manifeste:

- `scripts/cs50_learning_mvp.py`: expliziter serieller Offline-Operator.
- `tests/test_cs50_learning_mvp.py`: eigene Synthetik und reale lokale APIs.
- `docs/cs50/one-source-retrieval-mvp.md`: Analyse, Testplan, Verträge, Grenzen.
- `docs/cs50/one-source-retrieval-validation.md`: dieser Nachweis.

Wiederverwendet: MaterialDownloader, MaterialProcessor, ParserConfig,
MaterialPlan/MaterialResource, NormalizedDocument/ArtifactReceipt,
prepare_material_handoff, MaterialBundle/ImplementationEvidence,
verify_material_bundle/import_verified_bundle, ContentStore,
project_content_for_index über ContentIndex.build, IndexSelection,
search_lexical und ContentReader. Keine neue Datenbanktechnologie, kein Worker,
keine Extraction, LLM, Embeddings, Knowledge-Pipeline, UI oder CI-Änderung.

Commit/Push/PR-Aktionen/Merge sind auftragsgemäß unterblieben. Die Dateien sind
uncommittiert; HEAD wird nicht als Implementierungscommit ausgegeben. Der allgemeine
AGENTS.md-Lifecycle bleibt wegen der ausdrücklich untersagten Integration nach
master **pending**. Der bereits existierende Branch und Worktree bleiben erhalten.
Keine Git-Artefakte dieses Auftrags wurden erstellt oder gelöscht; keine fremden
Worktrees, Datenbanken, historischen Daten, Downloads oder Approval-Manifeste
verändert. Neue Runtime-/Testdaten ausschließlich in neuen `/tmp`-Verzeichnissen.

## Geprüfte finale Pythonbytes

Die letzte Codefassung vor dem gemeinsamen Schlusslauf hat folgende SHA-256:

| Gegenstand | SHA-256 |
| --- | --- |
| scripts/cs50_learning_mvp.py | `f7911f775a417f29b0055c4237b9ca472fe25e42734c1abe4babbf07c69c440b` |
| tests/test_cs50_learning_mvp.py | `45ad7ed286b351483836aa22c9102033151cbaceedbca854b1ea598c394eea40` |
| tatsächliche src/-Pythonbytes plus Operator, pfadgebundener Fingerprint | `548ff425c202e1bd6c78e7e3df76c8a3fdefe723bf929ba71cea5db70f5d25cd` |

Der Codefingerprint wird bereits in der synthetischen Operatorfreigabe gebunden
und im Implementierungsnachweis zusammen mit dem Freigabehash referenziert.

## Testumgebung und transparent erhaltene Fehlversuche

Der Systeminterpreter Python 3.11 hatte kein Pydantic. Ein erster uv-Offlinestart
scheiterte am schreibgeschützten bestehenden uv-Cache. Es wurde nichts installiert
oder heruntergeladen. Anschließend wurde ein neuer Python-3.12-venv unter `/tmp`
erstellt und auf bereits gecachte Pakete verwiesen. Keine bestehende venv geändert.

Der erste Operator-Entwicklungslauf (`/tmp/cs50-mvp-tests-01`) wurde nach zwei
Fehleranzeigen abgebrochen: Ein erwarteter DOM-Pfad war im öffentlichen Reader
redigiert. Die vorhandene Reader-Implementierung blieb unverändert. Der Operator
prüft nun den öffentlichen Originalpointer und weist den DOM aus dem gespeicherten
Payload separat aus. Dieser abgebrochene Lauf hat keinen vollständigen JUnit-
Abschlussbericht und wird nicht als bestanden gezählt.

Danach bestand die korrigierte Zwischenfassung 26 Tests in 47,99 s
(`/tmp/cs50-mvp-tests-02.xml`). Nach weiteren Freigabe-/Bestandsschutztests bestand
eine Zwischenfassung 58 Tests in 109,82 s (`/tmp/cs50-mvp-final-01.xml`). Nach
strikter Schema-/Nichtleer-/Distinct-Query-Prüfung bestanden 62 Tests in 61,55 s
(`/tmp/cs50-mvp-final-02.xml`). Diese enthalten 36 neue Operatorfälle und 26
vorhandene MaterialProcessor-/Downloadfälle; MockTransport führt keine echten
Downloads durch. Es wurden keine Skips/Xfails in Tests eingeführt.

Der erste breitere Lauf (`/tmp/cs50-mvp-regression-01.xml`, zugehörige `.log`)
erfasste 284 Tests: **187 passed, 2 failed, 94 errors, 1 skipped** in 321,43 s.
Die fünf ausdrücklich geforderten Dateien bestanden darin bereits vollständig:
49 Adapter-, 47 FTS-, 6 Retrievalintegration-, 18 Importjob- und 41 Projectionfälle.
94 Fehler entstanden im gemeinsamen Fixture der MaterialQuality-Tests durch
fehlendes `pymupdf`; zwei Unicodefälle scheiterten an Encoding-Erkennung.
Der bestehende optionale Originalmaterialtest wurde durch die vorhandene Policy
übersprungen; dies ist kein Realnachweis.

Ein zweiter neuer venv `/tmp/cs50-mvp-validated-env` erhielt ausschließlich Kopien
bereits vorhandener **Drittbibliotheken** aus
`<historischer-fremd-venv>/lib/python3.12/site-packages`: BeautifulSoup,
soupsieve und PyMuPDF samt Paketmetadaten. Keine Projektdatei oder Änderung aus
diesem Worktree übernommen, kein Worktree gewechselt und dort nichts geschrieben.
Weitere Pakete stammen aus dem vorhandenen uv-Cache. `PYTHONDONTWRITEBYTECODE=1`
und `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` gelten für die Testläufe.

Die erste gezielte Umgebungsprobe ergab 2 passed/2 failed
(`/tmp/cs50-mvp-environment-probe-01.xml`): PyMuPDF war nun verfügbar, aber der
zusätzlich eingebundene Debian-Paketpfad lieferte weiterhin `chardet`, das die
kurze UTF-8-Fixture als andere Kodierung deutete. Nach Entfernen **dieses
zusätzlichen Systempaketpfades im neuen Test-venv** benutzt BeautifulSoup das
bereits gecachte charset-normalizer. Alle vier gezielten Fälle bestanden in
1,52 s (`/tmp/cs50-mvp-environment-probe-02.xml`). Kein Parser, Test oder
Encodingdetektor wurde gemockt, gepatcht oder funktional geändert.

Finales Offline-Profil:

| Komponente | Version |
| --- | --- |
| Python | 3.12.12 |
| SQLite (FTS5 vorhanden) | 3.50.4 |
| Pydantic / pytest | 2.13.4 / 9.1.1 |
| BeautifulSoup / soupsieve | 4.15.0 / 3.0.4 |
| charset-normalizer / httpx | 3.5.1 / 0.28.1 |
| PyMuPDF (nur bestehende Quality-Regression) | 1.28.2 |

## Gemeinsamer Schlusslauf nach letzter Codeänderung

Die vor der Implementierung verifizierten vorhandenen Testfunktionen sind Teil
dieses Laufs, einschließlich ihrer bestehenden Parametrisierungen:

| Datei | Testfunktion |
| --- | --- |
| test_content_store_adapters.py | test_material_end_to_end_restart |
| test_content_retrieval_integration.py | test_verified_bundle_projection_fts_gold_report_reopen |
| test_content_fts.py | test_actual_build_search_restart_provenance |
| test_content_import_jobs.py | test_import_explicit_index_search_restart_and_acl |

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /tmp/cs50-mvp-validated-env/bin/python -m pytest \
  tests/test_cs50_learning_mvp.py \
  tests/test_content_store_adapters.py tests/test_content_fts.py \
  tests/test_content_retrieval_integration.py tests/test_content_import_jobs.py \
  tests/test_content_index_projection.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_download.py tests/test_cs50_material_html.py \
  tests/test_cs50_material_html_semantics.py tests/test_cs50_material_quality.py \
  tests/test_cs50_material_contracts.py \
  -m 'not external_integration' \
  --basetemp=/tmp/cs50-mvp-final-all-01 -p no:cacheprovider \
  --junitxml=/tmp/cs50-mvp-final-all-01.xml
```

Log: `/tmp/cs50-mvp-final-all-01.log`. Collection: 346 Fälle, davon 345 ausgewählt.
Genau ein bestehender Test ist ausdrücklich abgewählt:
`test_optional_original_python_notes_read_only` aus
`test_cs50_material_html_semantics.py`. Er benötigt reale Originalartefakte;
eine Ausführung ist in diesem Auftrag nicht freigegeben. Dies wird weder als
bestandener Test noch als reale Abnahme gewertet. Endergebnis:
**345 passed, 1 deselected in 343,33 s (5:43), Exitcode 0**.
JUnit enthält null Failures, null Errors und null Skips; keine Xfails.

| Datei | bestandene Fälle |
| --- | ---: |
| test_cs50_learning_mvp.py | 36 |
| test_content_store_adapters.py | 49 |
| test_content_fts.py | 47 |
| test_content_retrieval_integration.py | 6 |
| test_content_import_jobs.py | 18 |
| test_content_index_projection.py | 41 |
| test_cs50_material_processing.py | 8 |
| test_cs50_material_download.py | 18 |
| test_cs50_material_html.py | 7 |
| test_cs50_material_html_semantics.py | 17 |
| test_cs50_material_quality.py | 94 |
| test_cs50_material_contracts.py | 4 |

SHA-256 des finalen JUnit:
`576207e82b95d47abe974a264440333fda2eeaa1afef7ef864a57a29aaddd5af`.
SHA-256 des finalen Logs:
`6aa8deeff87d3c7da86eaeada4ce05f021f194be31f824329e4f3db9a1e8c165`.

Ruff 0.16.3 `check --no-cache` und `format --check --no-cache` für beide neuen
Pythondateien wurden ausgeführt; Ergebnis grün. Alle Tests verwenden isolierte
neue Datenroots. Frühere Fehlerartefakte bleiben erhalten; es gab kein
Retry-until-green und keine Änderungen an Bestandstests, um Fehler zu verdecken.
Ein zusätzliches `git diff --no-index --check /dev/null <neue-datei>` prüfte alle
vier neuen Dateien ohne Whitespace-Befund (Exitcode 1 wegen neuer Dateidifferenz,
keine Fehlerausgabe). `git diff --check` für den vorhandenen Bestand war ebenfalls
ohne Befund. Nach dem Schlusslauf wurden nur Dokumentationsergebnisse ergänzt;
die beiden Pythonhashes und der Implementierungsfingerprint wurden erneut geprüft
und stimmen mit der getesteten Fassung und dem separaten CLI-Nachweis überein.

## Separater finaler synthetischer CLI-Nachweis

Neue Laufumgebung:
`/tmp/cs50p-prompt20-final-evidence-uxscbbab`.
MVP-Root darunter: `new-private-mvp`.
Vier eigenständige CLI-Prozesse: `run`, identischer `run`, `search`, `status`.
Vollständige JSON-Berichte liegen als `run.json`, `repeat.json`,
`restart-search.json`, `status.json` und `summary.json` daneben. Die vier
zugehörigen stderr-Dateien sind leer; Exitcodes alle 0.

Der frühere Zwischenstand-Nachweis unter
`/tmp/cs50p-prompt20-evidence-8d0rhuk2` bleibt ebenfalls erhalten und wird nicht
mit dem finalen Codefingerprint verwechselt.

| Nachweis | Tatsächlicher Wert |
| --- | --- |
| eigene Rawbytes | 380 Bytes, selbst verfasstes HTML mit Überschrift, drei Absätzen, Codeblock |
| Raw-SHA-256 vor/nach Lauf und im Store | `ddfe8f2912719302b753cf194bc073d781bc78be553c0cf503aef4f2c9e646d7` |
| Source-ID | `resource:fd35721e7e07c012647b4a4bbd790e76c2980a071444f2eb1fa76d8289aa48cd` |
| SourceVersion | `content_source_version_v1:06f096fe0eb843ce119274e05591277e528d1f84e2f7ae6300c7bf6b4a7171d2` |
| ParsedVersion | `content_version_v1:3a6a78abb172f9b1e01c13f52083206e31696b8fc921dc29f14e5473a4a4e2d6` |
| ParserConfig-ID | `content_parser_v1:3610617e6d79985ea3ec8ee842c480841710e4970f70be4add88d640ccedf6a8` |
| Build-ID | `ad51925130494b53a05bd105956a2ad6` |
| interne Generation | `content_index_generation_v1:eaf146576166faa9fb78b11f99a9a9a82863df27324ef2e71fdcc3db16554a9e` |
| öffentlicher Generationstoken | `23d504f713cdf3534bd48c95879079d072941a78e0e6d6d65d73555c3cc5e249` |
| tatsächlich indexierte Records | 5 |
| Publikationen nach Wiederholung/Neustart | eine SourceVersion mit genau einer ParsedVersion |

Die vorab definierten Abnahmeaufgaben und exakten erwarteten Originalpassagen:

| Query | Erwartete Passage | tatsächlich beobachteter Rang |
| --- | --- | --- |
| variable | A variable stores a value under a chosen name. | 1 |
| input | The input function returns text entered by the learner. | 2 |
| loop | A loop repeats instructions while its condition remains true. | 1 |

Jeder gezählte Treffer stammt aus SQLite FTS5 und wird über ContentReader
aufgelöst: richtige Source-/ParsedVersion, Rawhash, `/blocks/n`-Pointer,
bytegenauer Originaltext und im gespeicherten Payload vorhandener DOM-Bezug.
Der `input`-Codeblock kann vor dem erwarteten Absatz stehen; der echte Rang 2
wird beibehalten. Kein künstliches Ranking und keine Ersatzpassagen.
ParsedVersion, Build-ID und beide Generationen bleiben beim Wiederholen und
beim separaten Suchprozess gleich. Die ursprünglich ausgewählten Input- und
Plandateien werden beim Wiederabruf nicht benötigt; Closure und Rawbytes liegen
im eigenen MVP-Root beziehungsweise ContentStore.

## AC1–AC12 und offene Abnahme

| Kriterium | Befund |
| --- | --- |
| AC1 | Synthetischer vollständiger CLI-Durchlauf erfolgreich. |
| AC2 | Persistente ParsedVersion und Originalrawbytes aus neu geöffnetem Store nachgewiesen. |
| AC3 | Expliziter ContentIndex.build, echte FTS5-Datei und aktive Generation. |
| AC4 | Echte Treffer mit Originaltext, Source-ID, ParsedVersion, Raw-/Blockreferenzen. |
| AC5 | Separater Prozess findet dieselben Inhalte und dieselbe Indexgeneration. |
| AC6 | Wiederholung publiziert und indexiert nicht erneut; Inventar unverändert. |
| AC7 | Hash-, Binding-, Freigabe-, Ablauf-, Schema- und Parserfehler abgewiesen. |
| AC8 | preparing/publication_pending/index_pending ergeben HOLD; Status ist Beobachtung. Verlorene Publikationsantwort führt zu keinem automatischen Retry. |
| AC9 | Fremde Stores/Roots werden abgelehnt; Input-/Manifestbytes bleiben erhalten. Bestehende Implementierungen sind unverändert. |
| AC10 | Reale Abnahme BLOCKED: keine konkrete Originalmaterialfreigabe. Die Verarbeitungsgrenze wurde eingehalten. |
| AC11 | BLOCKED: keine drei freigegebenen Originalmaterialaufgaben ausgeführt. Synthetische Ränge ersetzen diese nicht. |
| AC12 | PASS für alle 345 ausgewählten neuen/relevanten bestehenden Fälle auf finaler Codefassung; ein unfreigegebener Originalmaterialtest ausdrücklich abgewählt. Frühere Fehlschläge sind oben erhalten. |

**TECHNICAL PASS** für den synthetischen One-Source-MVP und das geprüfte Profil.
**REAL-SOURCE ACCEPTED und MVP ACCEPTED sind nicht erreicht.**

## Restrisiken, Erhaltung und nächster Schritt

Der Operator bleibt ein lokaler serieller Ablauf mit vertrauenswürdiger
Operatoridentität und privatem Freigabe-Attest, kein neues Authentifizierungssystem.
Kodierungserkennung hängt vom installierten Parserprofil und von deklarierten
HTML-Charsets ab; das geprüfte Profil ist oben konkret festgehalten. Bei späterer
Abnahme müssen insbesondere Originalcode, Umlaute, Sonderzeichen und Quellen-
Zuordnung am freigegebenen Material fachlich geprüft werden. Ein Quellen-URL-
Label oder ein bestandener Strukturcheck beweist keine semantische Korrektheit.

Nach unvollständigen Operationen ist eine gesonderte Operatoruntersuchung nötig;
es erfolgt keine automatische Recovery, Quarantäneaufhebung oder Doppelpublikation.
Die C16-HTTP-Schranke bleibt unverändert. `TECHNICAL PASS` eines CLI-Laufs allein
ist kein globales Acceptance-Urteil und ersetzt weder die Testsuite noch Realabnahme.

Die neuen Testumgebungen, Zwischenstands-/Fehlernachweise und finalen Runtime-
Artefakte bleiben unter ihren eindeutigen `/tmp`-Pfaden erhalten. Es wurde nichts
bereinigt; `/tmp` ist kein dauerhaftes Archiv. Alle relevanten Ergebnisse,
Entscheidungen, Hashes und Grenzen sind deshalb hier im Repository dokumentiert.
Der nächste fachliche Schritt ist eine separat belegte Originalmaterialfreigabe
mit Material-/Resource-ID, URL/Herkunft, exaktem Rawhash, vollständigem Plan,
Parser-/Implementierungsbindung und drei vorab festgelegten Passagen. Erst dann
ist ein eigener neuer privater Realabnahmeroot vorgesehen. Integration und
Bereinigung bleiben unter dem aktuellen Verbot ausgesetzt.

## Git-Endstatus

Nach Codeprüfung und Schlusslauf unverändert derselbe Worktree, Branch und HEAD;
Merge-Base und `origin/master` weiterhin
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Keine getrackte Datei verändert,
keine Stagingänderung. Tatsächlicher `git status --porcelain=v1`:

```text
?? docs/cs50/one-source-retrieval-mvp.md
?? docs/cs50/one-source-retrieval-validation.md
?? scripts/cs50_learning_mvp.py
?? tests/test_cs50_learning_mvp.py
```

Es gab keinen Commit, Push, Merge, PR-Eingriff oder Git-Cleanup. Der Branch und
Worktree bleiben mitsamt uncommittierter Arbeit erhalten; die Dokumente sind noch
nicht in master integriert. Der technische Implementierungs-/Testauftrag ist
nachgewiesen, die reale Abnahme und der allgemeine Integrations-Lifecycle bleiben
aus den beschriebenen konkreten Gründen offen.

## Prompt 24: vor Änderungen festgelegte Prüfstrategie (2026-11-06)

Git-Identität und exakt vier bekannte ungetrackte Dateien wurden bestätigt.
Alle vier Ausgangsdateien wurden separat kopiert und bytegenau geprüft; die
ursprünglichen Hashes bleiben im historischen Prompt-20-Abschnitt erhalten.
Backup und technische Logs sind private temporäre Operatorartefakte.
Vor Änderungen: Prompt-20-Bericht, Prompt-22-Abschlussnachweis und vollständiges
Prompt-23-Review gelesen; 72/72 Manifestdateien geprüft, zusätzlich gesamter
Prompt-22-Dateibestand und Original separat gehasht (74 geschützte Dateien).

Feste Reihenfolge und begrenzte Laufanzahl:

1. Offline-Installation in neuen isolierten Python-3.12.12-venv aus vorhandenen
   uv-Lockverträgen und verifizierbaren lokalen Caches prüfen (120 s je Versuch,
   höchstens zwei begründete Vertragsvarianten, kein Netz und kein Pythondownload).
   Charset-normalizer ausdrücklich wählen, chardet ausschließen; FTS5 aktiv prüfen.
   Fehlende Wheels bedeuten HOLD für AC6. Eine bestehende persönliche Umgebung
   darf dann nur ergänzende technische Regression liefern, keinen AC6-Nachweis.
2. Neue F1-Fälle einmal gezielt (180 s): gültige Suche, Revision-/Hashwechsel,
   fehlende Bindung, ungültige Approval, unveränderte Root-/Storebytes,
   forensischer Status. Mismatches nur mit synthetischen Fixtures/Injection.
3. Vollständige MVP-Datei einmal (240 s), einschließlich echtem Prozessrestart
   und gültiger Idempotenz.
4. Gemeinsamer Schlusslauf einmal nach letzter Codeänderung (900 s), exakt die
   zwölf unten stehenden Dateien in dieser Reihenfolge, eigene neue temporäre
   Testroots, JUnit und Exitcode. Bei konkreter nötiger Codekorrektur höchstens
   ein neuer gezielter Lauf und ein weiterer vollständiger Schlusslauf; jeden
   Fehlversuch dokumentieren. Kein Retry-until-green.
5. Ruff check und format --check beider Pythondateien (je 60 s), Diff-/Privacy-
   Kontrolle, erneuter Original-/Evidence-Hashvergleich und Git-Endzustand.

```text
tests/test_cs50_learning_mvp.py
tests/test_content_store_adapters.py
tests/test_content_fts.py
tests/test_content_retrieval_integration.py
tests/test_content_import_jobs.py
tests/test_content_index_projection.py
tests/test_cs50_material_processing.py
tests/test_cs50_material_download.py
tests/test_cs50_material_html.py
tests/test_cs50_material_html_semantics.py
tests/test_cs50_material_quality.py
tests/test_cs50_material_contracts.py
```

Alle Pfade existieren. Erfolg: alle ausgewählten Fälle bestanden, null Fehler,
Skips oder Xfails. Der vorhandene externe Originalmaterialtest wird sichtbar mit
`-m 'not external_integration'` abgewählt; keine neue Skip-/Xfail-Ausnahme.
`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
`-p no:cacheprovider`; synthetische Daten, kein Realmateriallauf.
Ein installierter, tatsächlich geprüfter frischer venv ist zusätzlich zwingend
für Integrationsfreigabe. Historische Resultate werden nicht neu zugeschrieben.

## Prompt 24: Git-Ausgang, Sicherung und aktueller Änderungsumfang

Auftrag: eigenständigen MVP-PR vorbereiten, ausdrücklich ohne Commit, Push,
PR-Aktion, Merge oder Cleanup. Der task-spezifische Integrationsstopp hat Vorrang
vor dem allgemeinen AGENTS.md-Lifecycle. Die Dokumente sind noch nicht in
`master`; Integration und Lifecycle-Abschluss bleiben **pending**.

Worktree öffentlich redigiert: `<repository>` (vorgegebener MVP-Worktree).
Branch `feat/cs50p-one-source-retrieval-mvp`; HEAD, Merge-Base und lokales
`origin/master` jeweils `a8af1d9372eb435d3e1331c33b047d21120d57c2`.
Lokales `master`: `c1007efdbac3c1544020f328a3a1347e481797ba`, kein Beleg
für den Live-Defaultstand. Kein Fetch und keine Live-/Reviewregelprüfung.
Ausgang: genau vier bekannte ungetrackte Dateien, getrackter und gestagter Diff
leer, keine unbekannten zusätzlichen Änderungen.

Vor Änderungen separat gesichert und bytegenau verifiziert:
`/tmp/cs50-p24-hardening-tyrrtdlp/baseline/` mit denselben vier relativen Pfaden,
zusätzlich `baseline.json` mit Branch/HEAD/Status/Hashes. Das ist ein temporärer
lokaler Backup, kein neues Git-Artefakt und kein dauerhaftes Archiv.

| Ausgangsdatei | SHA-256 vor Prompt 24 |
| --- | --- |
| scripts/cs50_learning_mvp.py | `f7911f775a417f29b0055c4237b9ca472fe25e42734c1abe4babbf07c69c440b` |
| tests/test_cs50_learning_mvp.py | `45ad7ed286b351483836aa22c9102033151cbaceedbca854b1ea598c394eea40` |
| docs/cs50/one-source-retrieval-mvp.md | `4ebf3a11f8c212cbda6b233325c48111c92e23e682cfbffe5e516fcfe056823c` |
| docs/cs50/one-source-retrieval-validation.md | `3ee0d81a2e0a7bc5ea911345c3fbe9703f43d6afaf6c1df4f226d4b125085005` |

Geändert gegenüber diesem gesicherten Stand:

- Operator: gemeinsame Implementierungsprüfung vor `run`/`search`, lesender
  Status mit separat ausgewiesener Retrievalautorisierung.
- MVP-Tests: 14 neue synthetische Fälle, insgesamt 50; Bestandstests unverändert.
- Architektur-/CLI-Dokument: neuer Vertrag, begründetes Testprofil, aktive
  Encoding-/FTS5-Probe, Installations- und Testkommandos, Scope/Restrisiken.
- Validierungsdokument: historische Resultate erhalten, persönlicher Worktreepfad
  redigiert, neue Prompt-24-Strategie und Ergebnisse separat ergänzt.
- Zusätzlich `tests/profiles/cs50-mvp-requirements.txt`: 22 exakte Pins mit
  Wheel-Hashes aus Root-uv.lock, begründete begrenzte Profilprojektion.

Keine vorhandene getrackte Datei verändert. Insbesondere Root-pyproject/uv.lock,
Guardian, Executor, Job-Control, C16-Schranken, B1, Stage-0-Validator und
GitHub Actions bleiben unverändert. Keine Arbeitskopien oder Branches erzeugt
oder gelöscht. Der bestehende MVP-Branch und Worktree werden mit uncommittierter
Arbeit wegen des ausdrücklich untersagten Integrationsschritts erhalten.

## Prompt 24: F1-Ursache, Korrektur und F2-Befund

F1: `run` band aktuelle Revision/Pythonbytes in `preflight()`, während `search`
über `observe()` direkt `report()` erreichte. Dort wurden nur der gespeicherte
Approvalhash, Schema, Ablauf und Akteur geprüft. Eine frühere Freigabe konnte so
mit verändertem aktuellem Code erfolgreich zur Suche verwendet werden.

Korrektur: `approved_implementation()` verwendet unverändert
`implementation_identity()` und die vorhandenen `sha256`/`fingerprint`/`canonical`
Funktionen. Beide Operationspfade erzwingen denselben Vertrag. Zusätzlich prüft
`retrieval_approval()` gespeicherten Approvalhash, Schema, Ablauf, Akteur und
Aktionen sowie aktuelle Revision/Fingerprint gegen Approval **und** Intent.
Bei Abweichung Exitcode 2, JSON HOLD, kein Aufruf von `retrieve()`. Keine alte
Freigabe oder Runtime wird aktualisiert; keine Migration oder Wiederverarbeitung.

Status ist forensisch erforderlich. `observed` mit Exitcode 0 bestätigt nur das
Lesen; `technical_status=NOT_ASSESSED` und `retrieval_authorization=HOLD` machen
Mismatch/ungültige Freigabe sichtbar. Alte Identität und Publikationsdaten bleiben
lesbar. Passende Autorisierung wird als `current`, niemals als aktuelles Test-PASS
bezeichnet. Fehlende Bootstrapdateien und beschädigte Stores bleiben bekannte
Beobachtungsgrenzen. Der Operator ist kein neues Authentifizierungssystem.

F2: Das historische Erfolgsprofil verwendete manuell kopierte Drittbibliotheken
und eine `.pth` mit absoluten Cachepfaden. Es ist kein portabler Herstellungsbeleg.
Die tatsächlichen relevanten Imports sind Pydantic für Verträge, httpx für
bestehende Downloader-/MockTransport-Tests, BeautifulSoup für HTML/Discovery,
PyMuPDF für bestehende PDF-/Quality-Fixtures und pytest. Ruff ist das Prüfwerkzeug;
charset-normalizer ist eine ausdrückliche Encodingvorgabe. Transitive Pins und
Wheel-Hashes sind im zusätzlichen Profil vollständig festgelegt. Der vorhandene
Rootvertrag wird nicht global reorganisiert.

Die Profilprojektion wurde gegen das vorhandene uv.lock geprüft: 22/22 Versionen
und vollständige Wheel-Hashmengen stimmen; alle transitiven Dependency-Namen sind
enthalten. Das ist eine statische Vertragsprüfung, **keine installierte Umgebung**.
Die entscheidende Abweichung zum verwendeten historischen Profil ist soupsieve
2.9.2 im Root-Lock gegenüber 3.0.4 im historischen Erfolgsprofil. Sie bleibt offen.
Installations- und Testanleitung ohne persönliche Cache-/Worktreepfade stehen im
[Architekturdokument](one-source-retrieval-mvp.md#prompt-24-portabler-dependencyvertrag-und-ausführungsgrenze).

## Prompt 24: tatsächlich ausgeführte Umgebungsversuche und Fehler

Alle neuen Helpers, Cachekopie und Testroots liegen unter dem eigenen temporären
Nachweisroot `/tmp/cs50-p24-hardening-tyrrtdlp/`. Der vorhandene uv-Cache wurde
mit intakter Paketmanagerstruktur in diesen beschreibbaren Root kopiert; keine
Drittbibliothek wurde manuell aus einem venv übernommen oder neu verpackt.
Keine neuen `.pth`-Verweise, kein Netz, kein Python-/Paketdownload.

| Versuch | Ergebnis / Exitcode | Nachweisdatei im temporären Nachweisroot |
| --- | --- | --- |
| Frischer Python-3.12.12-venv mit Root-`uv sync --locked --offline --no-default-groups --group test-offline --no-install-project` | 1: PyMuPDF 1.28.2 Wheel nicht im Cache | install-root.log |
| Root-Testgruppenentwurf ausschließlich in Scratchkopie; `uv lock --offline` | 1: globale optionale OCR-Auflösung benötigt nicht gecachte Torch-Metadaten | profile-lock.log |
| `uv pip sync --offline --require-hashes --only-binary :all:` mit scoped Profil im neuen venv | 1: annotated-types 0.8.0 nicht für diese Auflösung im Cache verfügbar | install-scoped.log |
| Erste Ruff-Aufrufe über `python -m ruff` im historischen venv | 1 / 1: Ruff-Pythonmodul fand sein Binary nicht | Toolausgabe; kein Testergebnis |
| Ruff über bereits vorhandenes Paket-Binary 0.16.3 | check erfolgreich, beide Pythondateien vor Testbeginn formatiert | Toolausgabe |
| Erster Dokumentations-Schreibhelper | Shellfehler 126 wegen kollidierendem Heredoc; kein Text geschrieben, fehlgestartete Beispielkommandos führten keine Tests aus | Toolausgabe; anschließend durch Patch ersetzt |

Keiner dieser Fehlversuche wird als erfolgreicher Build gezählt. In den lokalen
uv-/pip-Caches wurden keine installierbaren BeautifulSoup-/soupsieve-/PyMuPDF-
Wheels gefunden. Der unvollständige frische venv enthält nur den uv-Bootstrap.
**AC6 bleibt HOLD**, F2 ist nicht geschlossen. Keine unbegrenzten Wiederholungen.

Die ergänzende Regression verwendet ausdrücklich den **bestehenden historischen**
venv aus Prompt 20, dessen persönliche `.pth` bereits vorhanden war. Er wurde
weder neu hergestellt noch verändert. Dieser Testlauf belegt Codeverhalten in
jenem Profil und ersetzt AC6 nicht. Gemessen: Python 3.12.12, SQLite 3.50.4,
Pydantic 2.13.4, pytest 9.1.1, BeautifulSoup 4.15.0, soupsieve 3.0.4,
charset-normalizer 3.5.1, httpx 0.28.1, PyMuPDF 1.28.2. BeautifulSoup meldet
`charset_normalizer` als aktiven Detektor; kein Debian-Paketpfad ergänzt.

## Prompt 24: neue technische Validierung

Nach letzter Pythonänderung/formatierten Bytes:

| Gegenstand | SHA-256 |
| --- | --- |
| scripts/cs50_learning_mvp.py | `dc6343d066aa59f0ce1e72921312e2c5ec427793939173c6630981afc0529ea2` |
| tests/test_cs50_learning_mvp.py | `bb151f28f5e0241a0b3226dcb6862359c0e2680a2dc4c592f3015ca16bdac0e4` |
| src/-Pythonbytes plus Operator, bestehender Fingerprintvertrag | `363e5dc5f16f9169f76e06238070dfc1f1df29d09c77e1c380f341443cec5145` |
| tests/profiles/cs50-mvp-requirements.txt | `6d26f94c499ecf530394156bf57b9e4d579a61603ea04d733af67b6957dc46c1` |

Alle drei pytest-Läufe sind **ergänzende Tests im historischen Profil**.
`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-B`,
`-p no:cacheprovider`, jeweils eigener neuer `--basetemp` und JUnit.

| Lauf | Ergebnis | Timeout | Artefakte im Nachweisroot |
| --- | --- | --- | --- |
| Neue F1-Fälle (`-k 'search_current_implementation or search_changed_implementation or search_invalid_saved_binding'`) | 14 passed, 36 deselected, 42,92 s, Exit 0 | 180 s | f1.log / f1.xml / f1-command.json |
| Vollständige MVP-Datei | 50 passed, 99,38 s, Exit 0 | 240 s | mvp.log / mvp.xml / mvp-command.json |
| Gemeinsamer Schlusslauf aller zwölf festgelegten Dateien | 359 passed, 1 deselected, 351,08 s, Exit 0 | 900 s | final.log / final.xml / final-command.json |

Die vollständige MVP-Datei enthält gültige Suche und Idempotenz, Restart in echten
separaten Pythonprozessen, alte Approval-/Hash-/Closuretests und alle neuen Fälle.
Keine Repositorydatei wurde zur Mismatchsimulation verändert. Negative Aufrufe
prüfen das gesamte private Testrootinventar, einschließlich sämtlicher SQLite-,
Store-, Index-, Approval- und Intentdateien: Bytes und Modi bleiben unverändert.
Es gibt keine neuen Skips/Xfails. Der externe Originalmaterialfall wird beim
Schlusslauf ausdrücklich abgewählt; er ist weder Synthetik-PASS noch Realnachweis.

Finales JUnit: **359 Testcases**, null Failures, Errors oder Skips; keine
Xfails. 360 Fälle gesammelt, genau der vorhandene
`test_optional_original_python_notes_read_only` sichtbar abgewählt. Neue und
relevante Tests nach letzter Pythonänderung ausgeführt; keine fehlgeschlagenen
pytest-Läufe und kein zusätzlicher Korrektur-/Wiederholungszyklus in Prompt 24.
Die oben dokumentierten Installations-/Werkzeugfehler bleiben erhalten.

| Datei im gemeinsamen Schlusslauf | Bestanden |
| --- | ---: |
| test_cs50_learning_mvp.py | 50 |
| test_content_store_adapters.py | 49 |
| test_content_fts.py | 47 |
| test_content_retrieval_integration.py | 6 |
| test_content_import_jobs.py | 18 |
| test_content_index_projection.py | 41 |
| test_cs50_material_processing.py | 8 |
| test_cs50_material_download.py | 18 |
| test_cs50_material_html.py | 7 |
| test_cs50_material_html_semantics.py | 17 |
| test_cs50_material_quality.py | 94 |
| test_cs50_material_contracts.py | 4 |

SHA-256 finales JUnit:
`4db62089db75bdfe3b0503182e9a83bb6b388b6aadb808f4815a6c3dfef379ec`.
SHA-256 finales Testlog:
`61503ca2c5f766bfa5b34ea250ec2e1e3d1373a30c6cd8fe36a1a4e80a11672d`.
Ruff 0.16.3 `check --no-cache` und `format --check --no-cache` beider
Pythondateien erfolgreich. `git diff --check` und zusätzliche
`git diff --no-index --check /dev/null <Lieferdatei>` für alle fünf ungetrackten
Dateien ohne Whitespacebefund. Pfad-/Privacyprüfung ohne persönliche absolute
Worktreepfade; lokale Dokumentationslinks aufgelöst. Root-pyproject/uv.lock
bytegenau gegen HEAD bestätigt. Kein Runtime-/Materialdump Bestandteil des Diffs.
Die aktive ergänzende Umgebungsprobe bestätigte FTS5 mit eigener Unicodezeile,
`charset_normalizer`, fehlendes `chardet` und deaktivierte User-Site-Packages.
Sie beschreibt ausschließlich das historische Profil, nicht die frische Umgebung.

## Prompt 24: historische Realabnahme und Evidenzerhaltung

Gelesene private Nachweise: Prompt-20-Ergebnis und finale Repositorydokumente;
Prompt-22-final-acceptance mit CLI-, Handoff-, Retrieval- und Integritätsnachweisen;
vollständiges unabhängiges Prompt-23-Review. Ihre privaten Inhalte werden nicht
in diese öffentliche Dokumentation kopiert.

Prompt 22: 71.718 Originalbytes, Raw-SHA-256
`0e9af3114adec16938b89b511337f5db717ef2e14f1a606af600d6995ce09377`,
237 normalisierte Blöcke, 171 Indexrecords, genau eine ParsedVersion und drei
vorab festgelegte geeignete Goldpassagen jeweils Rang 1; Restart und Idempotenz.
Prompt 23: 72/72 Manifestdateien bestätigt, Original/Rawkopien bytegleich,
Implementierungsfingerprint konsistent und beide SQLite-Integritätschecks ok;
keine CRITICAL-/HIGH-Findings, F1/F2 als Integrationsblocker.

Diese Ausführungsergebnisse gelten für die konkreten historischen Pythonbytes
mit Fingerprint `548ff425c202e1bd6c78e7e3df76c8a3fdefe723bf929ba71cea5db70f5d25cd`.
Sie sind kein neuer Testnachweis für die geänderte Fassung. Prompt 24 führt keine
Realmaterialverarbeitung, Suche im Realroot, neue Goldauswertung oder
SQLite-Schreiböffnung aus. Originale und Evidence werden ausschließlich gehasht.

Die damalige Offline-Anweisung wurde durch den zusätzlichen öffentlichen Abruf
der Notes-Seite verletzt. Diese historische Tatsache und die damaligen
HOLD-Entscheidungen bleiben bestehen. Der Betreiber hat am **06.11.2026** für
den einmaligen dokumentierten Abruf eine Ausnahme akzeptiert, sofern die lokalen
Dateien unverändert geblieben sind. Damit darf der überprüfte lokale Lauf als
fachlicher und technischer Nachweis für genau den geprüften Stand verwendet
werden. Die Akzeptanz macht den Vorgang **nicht rückwirkend regelkonform**. Sie
betrifft die dokumentierten, nachgeprüften lokalen Bestände und erlaubt weder
eine pauschale Aussage über sämtliche Dateien noch über den gesamten
Netzwerkverkehr. Historische Nachweise, Approval und MaterialPlan werden nicht
rückwirkend geändert. Kein automatischer Realmaterial-Re-Run.

Vor Prompt-24-Änderungen direkt geprüft: 72/72 Manifestdateien mit Hash, Größe
und Modus; zusätzlich kompletter vorhandener Prompt-22-Dateibestand samt Manifest
und Original erfasst, insgesamt 74 geschützte Dateien. Abschließender Vergleich: **74/74 Dateihashes unverändert**, identischer
Dateibestand; **72/72 Manifestdateien** auch größen- und moduskonsistent. Original,
input-Rawkopie, Material-Rawkopie und gespeicherter Rawblob sind erneut bytegleich.
Die SQLite-Dateien wurden nicht geöffnet, sondern ausschließlich gehasht. Die vier MVP-Dateien ändern sich jetzt absichtlich; ihr alter Stand
ist separat gesichert und darf nicht mehr als aktueller Code ausgegeben werden.

## Prompt 24: FMEA, Reviewempfehlung und offene Freigaben

| Befund | Fehlerfolge | Kontrolle / Neubewertung | Restrisiko und Freigabe |
| --- | --- | --- | --- |
| F1, Integritäts-/Freigabebindung, zuvor MEDIUM | Aktueller Suchcode verwendet historische Approval ohne neue Identitätsprüfung | Gemeinsames Gate; neue Negativfälle; keine Mutation | Im vertrauenswürdigen lokalen seriellen Modell reduziert; gemeinsame User-/Dateisystemmanipulation und Codewechsel nach Prüfmoment werden nicht isoliert. Kein aktueller Integrationsblocker aus F1. |
| F2, Reproduzierbarkeit, MEDIUM | Fachlicher/technischer Erfolg lässt sich auf frischem Checkout nicht herstellen | Pins/Hashes und Anleitung ergänzt, zwei Installationsversuche gescheitert | Weiterhin Integrationsblocker; AC6 HOLD; soupsieve-Differenz ungeprüft. |

Weitere Grenzen aus Prompt 23 bleiben sichtbar: Bootstrapstatus benötigt Intent
und State (F3); Python-Socketsperren erben nicht in frische Unterprozesse (F4);
HTML läuft synchron ohne harte Worker-Timeout-/Speicherisolation (F5).
Operatoridentität ist ein vertrauenswürdiges lokales Attest, keine digitale
Signatur. Unklare Publikationszustände benötigen gesonderte manuelle Untersuchung;
keine automatische Quarantäneaufhebung, Recovery, Migration oder Job-Control.
Kein Produktions-, Skalierungs- oder unbeaufsichtigter Betrieb freigegeben.

Empfehlung: später eigenständiger MVP-PR mit genau den fünf genannten Dateien.
Vorgeschlagener Titel: `Add controlled CS50P one-source retrieval MVP with implementation-bound search`.
Funktionale Module sind bereits im Basiscommit vorhanden; keine harte Abhängigkeit
von PR #171. Der lokale Stage-0-Branch steht unverändert auf
`929fb1e1aa821e779b7d7ad327cf5a323666bd31`; seine geänderten Dateipfade
überschneiden sich nicht mit dem MVP-Lieferumfang. Gemeinsame Bibliothek:
Stage 0 ändert unter anderem `src/tools_materials/storage.py`. Wird das zuerst
integriert, sind neuer Fingerprint, explizite neue Freigaben für spätere Läufe und
Regression auf dem tatsächlichen Gesamtstand erforderlich. Stage 0 gilt nicht als
abgeschlossen; PR #171 bleibt unabhängig und unverändert. Keine B1-Experimente
oder historischen Diagnoseberichte übernehmen.

Vor PR-Freigabe: vollständigen genehmigten Offlinecache/Wheelhouse bereitstellen,
frischen Python-3.12.12-venv anhand des Vertrags erfolgreich installieren,
Encoding-/FTS5-Probe und exakt die zwölf Dateien plus Ruff ausführen. Die
soupsieve-Differenz dabei tatsächlich prüfen; bei erforderlicher Versionsänderung
gezielt Vertrag/Hashprovenienz reviewen. Kein Onlinepaketabruf ohne separaten Auftrag.

Vor Merge zusätzlich: tatsächliche Live-master-Basis bestätigen, aktuellen
PR-171-Status nur bei Bedarf lesend prüfen, unabhängiges Code-/Freigabereview,
Dependency-/Encodingreview, Dokumentations-/Privacyreview und geltende Required
Reviews/Branchregeln/CI erfüllen. Im vorliegenden Basisstand existiert kein
`.github/workflows`-Testworkflow; eine lokale grüne Suite ist kein Hosted-CI-Beleg.
Eine geeignete spätere CI-Ausführung braucht Linux, den festgelegten Interpreter,
vollständige Dependencybereitstellung, FTS5/Encodingprobe und die dokumentierte
synthetische Suite. GitHub Actions bleiben in diesem Auftrag unverändert.

Kein Bedarf für automatische Realmaterialwiederholung aus den vorliegenden
Befunden. Scope bleibt eine reale HTML-Quelle, privater lokaler nichtkommerzieller
Betrieb, lexikalische Suche und kontrollierte Operatorausführung; keine Knowledge
Extraction, LLMs oder unbeaufsichtigte Job-Control-Nutzung.

## Prompt 24: AC1–AC12 und Freigabestufen

Diese Matrix gehört ausschließlich zu Prompt 24; die oben erhaltene Prompt-20-
Matrix hat andere Kriterien und wird nicht rückwirkend umgedeutet.

| Kriterium | Status | Nachweis / Grenze |
| --- | --- | --- |
| AC1 – aktuelle Implementierungsbindung bei Search | PASS | Gemeinsame Funktion vor `retrieve()`, positiver Fall und negative aktuelle Identität geprüft. |
| AC2 – abweichender Fingerprint verhindert Erfolg | PASS | Injizierter Fingerprint-/Revisionswechsel und fehlende Identität: Exit 2, HOLD, kein Retrieval. |
| AC3 – Daten bei Ablehnung unverändert | PASS | Gesamte synthetische Rootinventare einschließlich ContentStore/SQLite vor/nach Ablehnung identisch. |
| AC4 – ehrlicher forensischer Status | PASS | Alte Identität lesbar; `NOT_ASSESSED` und Autorisierung HOLD, kein aktuelles Test-PASS. |
| AC5 – Umgebung ohne persönliche Pfade beschreibbar | PASS | Scoped Lockprojektion, exakter Interpreter, Anleitung und aktive Probe; statischer Vertrag, keine erfolgreiche Installation behauptet. |
| AC6 – frische isolierte Testumgebung hergestellt/geprüft | HOLD | Zwei Offlineinstallationen gescheitert; fehlende Wheel-/Cachegrundlage; soupsieve-Differenz ungeprüft. |
| AC7 – relevante Regression auf finalem Code | PASS | 359/359 ausgewählte Fälle im historischen Profil; null Failures/Errors/Skips, ein externer Originalmaterialfall ausdrücklich abgewählt. Kein AC6-Nachweis. |
| AC8 – Original-/Prompt-22-Evidence bytegleich | PASS | Abschließend 72/72 Manifestdateien und 74/74 geschützte Dateien unverändert; Original und sämtliche Rawkopien bytegleich. |
| AC9 – keine privaten Laufzeitdaten öffentlich | PASS | Redaktion persönlicher Pfade; fünf Lieferdateien, keine privaten Inputs/Outputs, Pläne, Approvals, SQLite-Dateien oder Ergebnisdumps. |
| AC10 – B1-/Stage-0-/C16-Schranken unverändert | PASS | Kein getrackter Diff; Produktmodule, historische Nachweise und fremde Worktrees nicht beschrieben. |
| AC11 – keine automatische Materialverarbeitung | PASS | Nur explizite bestehende Operatoraufrufe mit Synthetik; keine Recovery/Migration/Quarantäneaufhebung oder neue Job-Control. |
| AC12 – Git-Ausgang und Endzustand dokumentiert | PASS | Branch/HEAD unverändert; initial vier, final fünf ungetrackte Lieferdateien; getrackter und gestagter Diff leer. |

| Stufe | Entscheidung und Geltungsbereich |
| --- | --- |
| TECHNICAL PASS | Bestätigt für die finalen Pythonbytes: 14 neue F1-Fälle, 50 MVP-Fälle und abschließend 359 ausgewählte Fälle im ergänzenden historischen Profil. Keine portable Neuinstallation behauptet. |
| MVP ACCEPTED | Historischer lokaler Einzelquellennachweis aus Prompt 22 unter der expliziten Betreiber-Ausnahme akzeptiert; keine neue Realabnahme der Prompt-24-Bytes. |
| INTEGRATION READY | HOLD wegen F2/AC6. Eigenständiger PR inhaltlich vorbereitet, aktuell keine Integrationsfreigabe. |
| MERGE READY | HOLD: AC6, tatsächliche Livebasis, Pflichtreviews und CI fehlen. |
| DEPLOYMENT READY | HOLD / außerhalb dieses lokalen, kontrollierten MVP-Auftrags; keine Produktionsfreigabe. |

## Prompt 24: Git-Endstatus und Erhaltung

Endaufnahme bestätigt denselben Branch, HEAD und Basisstand. Getrackter und
gestagter Diff sind leer. Tatsächlicher `git status --porcelain=v1 --untracked-files=all`:

```text
?? docs/cs50/one-source-retrieval-mvp.md
?? docs/cs50/one-source-retrieval-validation.md
?? scripts/cs50_learning_mvp.py
?? tests/profiles/cs50-mvp-requirements.txt
?? tests/test_cs50_learning_mvp.py
```

Es gibt ausdrücklich keinen Commit, Push, Merge,
PR-Eingriff, Branchwechsel oder Cleanup. Die fünf vorgesehenen Dateien bleiben
uncommittiert im bestehenden Worktree. Der PR ist nicht erstellt; die Dokumente
sind noch nicht in master integriert. Dieser Integrations-/Lifecycle-Schritt
bleibt auftragsgemäß pending. Keine eigenen temporären Git-Artefakte entstanden;
der vorbestehende Branch und Worktree sowie alle temporären Nachweise werden
erhalten. Kein fremdes Artefakt darf daraus als bereinigbar abgeleitet werden.

## Prompt 25: frische Umgebung und Offline-VERIFY (06.11.2026)

**F2 geschlossen; TECHNICAL PASS für das neue scoped Linux-Profil.** Dieser
Abschnitt ergänzt die historischen Prompt-20/22/23/24-Ergebnisse. Die früheren
HOLD-Entscheidungen beschreiben ihren damaligen Stand. INSTALL und VERIFY liefen
in getrennten Sitzungen. VERIFY hat keine Pakete installiert, keine Downloads,
Remote-Git-/Web-/Connectorzugriffe oder Realmaterialverarbeitung ausgeführt.

### Ausgangszustand, Installationsbindung und Profil

AGENTS.md, Root-pyproject/uv.lock, scoped Requirements und der vorhandene
zwölfteilige Plan wurden vor dem Lauf gelesen. Branch
`feat/cs50p-one-source-retrieval-mvp`, HEAD
`a8af1d9372eb435d3e1331c33b047d21120d57c2`; getrackter und gestagter Diff leer.
Genau die fünf unten aufgeführten Lieferdateien waren bereits ungetrackt.
Die VERIFY-Ausgangsaufnahme stimmt mit INSTALL für alle **1137 erfassten
Repositorydateien** und **74 geschützten Dateien** überein. Unbekannte
Änderungen wurden nicht festgestellt.

Der maschinenlesbare `install-evidence/install-report.json` meldet **PASS**.
Alle 23 Dateien seines Evidence-Hashmanifests wurden erneut geprüft.
INSTALL belegte eine vorher nicht existente venv und einen leeren privaten Cache;
keine historische venv wird als neue Installation ausgegeben. Die tatsächlichen
erfolgreichen uv-0.9.15-Befehle stehen mit portablen Platzhaltern im
[MVP-Vertrag](one-source-retrieval-mvp.md#prompt-25-reproduzierbare-installation-und-f2-abschluss).
INSTALL verwendete ausschließlich PyPI und files.pythonhosted.org, nur Wheels,
`--require-hashes`, `--link-mode copy`, keine Pythoninstallation oder Source-Builds.
Der erste Sync wurde wegen unvereinbarer Flags vor Download abgewiesen;
der korrigierte Aufruf ließ das redundante `--no-build` weg und behielt
`--only-binary :all:`. Beide Versuche bleiben im Installationsnachweis erhalten.

| Bindung | Verifizierter Wert |
| --- | --- |
| Interpreter | `<env-root>/venv/bin/python`, CPython 3.12.12, Linux x86_64 |
| Requirements SHA-256 | `6d26f94c499ecf530394156bf57b9e4d579a61603ea04d733af67b6957dc46c1` |
| Root-uv.lock SHA-256 | `63e72cbcf0df19c6f06e8088f1406e7404c2e0fe4b094a9f91f7fce5276cc19c` |
| Umgebungsfingerprint SHA-256 | `ba93899321f718c31c83327376e727b362615dbd4e6756797cb76e9bc7373d95` |
| SQLite / FTS5 | 3.50.4 / aktiv, Unicode-Abfrage bestanden |
| Encodingdetektor | charset-normalizer 3.5.1, Modul `charset_normalizer`, kein `chardet` |
| Isolation | keine System-/User-Site-Packages, keine persönlichen Cachepfad-.pth-Verweise |
| Dependencyprüfung | `uv --no-config --offline --cache-dir <env-root>/uv-cache --no-python-downloads pip check --python <env-root>/venv/bin/python`: Exit 0 |

Alle 22 Pins und vollständigen Wheel-Hashmengen stimmen erneut mit `uv.lock`
überein; die transitive Closure aus sieben Seeds ist vollständig. Unter Linux
werden 21 Pakete installiert; colorama 0.4.6 ist nur für Windows markiert und
wurde hier nicht installiert. Pythonanforderungen, Plattform-Wheeltags,
Metadatenabhängigkeiten und **1005 RECORD-Dateihashes** wurden aktiv erneut geprüft.
Der einzige `.pth`-Inhalt ist `import _virtualenv`; kein Paket wird über einen
persönlichen Cache eingebunden. Root-pyproject, Root-lock, Requirements und beide
Python-Lieferdateien bleiben bytegleich. Der HOLD-Kommentar im unveränderten
Requirements-Header stammt aus Prompt 24; die aktuelle Bewertung steht hier.

| Installiertes Paket | Version |
| --- | --- |
| annotated-types | 0.8.0 |
| anyio | 4.14.2 |
| beautifulsoup4 | 4.15.0 |
| certifi | 2026.7.22 |
| charset-normalizer | 3.5.1 |
| h11 | 0.16.0 |
| httpcore | 1.0.9 |
| httpx | 0.28.1 |
| idna | 3.19 |
| iniconfig | 2.3.0 |
| packaging | 26.3 |
| pluggy | 1.6.0 |
| pydantic | 2.13.4 |
| pydantic-core | 2.46.4 |
| pygments | 2.21.0 |
| pymupdf | 1.28.2 |
| pytest | 9.1.1 |
| ruff | 0.16.3 |
| soupsieve | 2.9.2 |
| typing-extensions | 4.16.0 |
| typing-inspection | 0.4.4 |

**Eigenständiges neues Profil:** soupsieve **2.9.2** kommt aus dem Lockfile,
während das historische Erfolgsprofil **3.0.4** verwendete. Der neue Lauf besteht
mit 2.9.2; historische Resultate werden weder umetikettiert noch als identisches
Profil ausgegeben. Validiert ist Linux x86_64 mit Python 3.12.12; andere
Plattformen/Interpreter sind nicht automatisch abgedeckt.

### Fester Schlusslauf und deaktiviertes Netzwerk

Vor Testbeginn wurde `test-evidence/verify-plan.json` festgelegt: genau ein
gemeinsamer Lauf über die zwölf vorhandenen Testdateien, Timeout 900 s,
keine separaten wiederholten F1-/MVP-Läufe, keine Retries. F1- und MVP-Teilmengen
werden aus demselben JUnit ausgewertet. Es gab keine Python-/Dependencyänderung
und keinen Korrektur-/Wiederholungslauf; danach wurden nur diese beiden
Markdown-Dokumente ergänzt.

Zusätzlich zur deaktivierten Netzfreigabe installiert der private
`offline_exec.py` vor Prozessstart einen Linux-x86_64-seccomp-Filter mit
`NoNewPrivs=1`: `socket`/`socketpair` sind nur für AF_UNIX zulässig;
andere Familien ergeben EPERM. Der Filter wird durch fork/exec in
Test-Unterprozesse vererbt. Der Start verwendet `close_fds=True` und
Datei-/Pipe-Standarddeskriptoren. IPv4-/IPv6-Socketproben vor und nach exec
ergaben EPERM, AF_UNIX-Socketpair blieb möglich; `/proc/self/status` bestätigte
`Seccomp=2`, drei Filter und NoNewPrivs. Dafür wurden keine externen Ziele
kontaktiert. Probe und Testlog dokumentieren die Sperre. Das ist ein privater
Testlauncher, keine neue produktive Guardian-/Executor- oder Worker-Schranke.

Tatsächlicher Testaufruf, nur persönliche Rootpräfixe durch Variablen ersetzt
(`repo-root` ist das Arbeitsverzeichnis; `venv=<env-root>/venv`,
`evidence=<env-root>/test-evidence`):

```bash
env -i HOME="$evidence" PATH="$venv/bin:/usr/bin:/bin" LANG=C.UTF-8 \
  TMPDIR="$evidence" PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_PYTHON_DOWNLOADS=never UV_OFFLINE=1 \
  "$venv/bin/python" -I -B "$evidence/offline_exec.py" /usr/bin/timeout 900 \
  "$venv/bin/python" -B -m pytest \
  tests/test_cs50_learning_mvp.py \
  tests/test_content_store_adapters.py tests/test_content_fts.py \
  tests/test_content_retrieval_integration.py tests/test_content_import_jobs.py \
  tests/test_content_index_projection.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_download.py tests/test_cs50_material_html.py \
  tests/test_cs50_material_html_semantics.py tests/test_cs50_material_quality.py \
  tests/test_cs50_material_contracts.py -m 'not external_integration' \
  --deselect=tests/test_cs50_material_html_semantics.py::test_optional_original_python_notes_read_only \
  -p no:cacheprovider --basetemp="$evidence/synthetic-tests" \
  --junitxml="$evidence/final.xml"
```

Ergebnis: **360 gesammelt, 359 passed, genau 1 explizit deselected**, Exit **0**.
**0 Failures, 0 Errors, 0 Skips, 0 Xfails, 0 Xpasses.** JUnit-Laufzeit
**524.433 s**, gemessene Befehlslaufzeit einschließlich Launcher
**526.53 s**. Alle **50 MVP-Fälle**, darunter die **14 F1-Fälle**
(`search_current_implementation`, `search_changed_implementation`,
`search_invalid_saved_binding`), sind Teil dieses einen Schlusslaufs.
Restart und Idempotenz laufen mit realen separaten Pythonprozessen bzw.
persistierter eigener Synthetik. Downloadtests verwenden synthetische Responses.
Der Originalmaterialtest wurde vor Fixtureausführung abgewählt; er ist kein
Skip und kein neuer Realmaterialnachweis.

| Datei | Bestanden |
| --- | ---: |
| test_content_fts.py | 47 |
| test_content_import_jobs.py | 18 |
| test_content_index_projection.py | 41 |
| test_content_retrieval_integration.py | 6 |
| test_content_store_adapters.py | 49 |
| test_cs50_learning_mvp.py | 50 |
| test_cs50_material_contracts.py | 4 |
| test_cs50_material_download.py | 18 |
| test_cs50_material_html.py | 7 |
| test_cs50_material_html_semantics.py | 17 |
| test_cs50_material_processing.py | 8 |
| test_cs50_material_quality.py | 94 |

Ruff **0.16.3 aus derselben frischen venv**, unter derselben Netzsperre:
`python -B -m ruff check --no-cache` sowie
`python -B -m ruff format --check --no-cache`, jeweils auf
`scripts/cs50_learning_mvp.py` und `tests/test_cs50_learning_mvp.py`,
jeweils **Exit 0**. uv ist das separat vorhandene Installationswerkzeug 0.9.15
und wird nicht als venv-Paket ausgewiesen.

Private Nachweise unter `<env-root>/test-evidence/`: `verify-plan.json`,
`environment.json`, `network-probe.log`, `dependency-check.log`,
`final-command.json`, `final.log`, `final.xml`, `test-results.json`,
`ruff-command.json`/`ruff.log`, `format-command.json`/`format.log`,
`local-integration-check.json`, Git-/Integritätsaufnahmen und
`verify-report.json`; `evidence-sha256.json` bindet die finalen Nachweisdateien.
Die exakten privaten Interpreter-/Logpfade stehen in den Maschinenberichten.

| Finaler Nachweis | SHA-256 |
| --- | --- |
| JUnit `final.xml` | `c582d5a3ccac04a25645de843f892b527c1cb440997b497e37ca0f1e93178e5b` |
| Testlog `final.log` | `312d3c398b968e29c4499dfca310c6caaf5a9651d41215d7f18b5217ad7e3d21` |

### Prompt-25-Abnahme AC1–AC14

Diese Kriterien gehören zu Prompt 25; die historischen AC-Matrizen bleiben erhalten.

| Kriterium | Status | Nachweis |
| --- | --- | --- |
| AC1 – Frische Python-3.12.12-venv | PASS | INSTALL-Protokoll bestätigt vorher fehlende venv und leeren privaten Cache; VERIFY prüft exakt diese venv. |
| AC2 – Scoped Installation | PASS | INSTALL PASS; 22 Lockpins, davon 21 unter Linux, vollständige transitive Closure; keine Neuauflösung. |
| AC3 – Paket-/Wheel-Hashes | PASS | uv --require-hashes, 21 ausgewählte Wheels gegen Lockdaten; 1005 installierte RECORD-Dateihashes in VERIFY erneut geprüft. |
| AC4 – Keine Cachepfad-.pth-Abhängigkeit | PASS | Keine System-/User-Site-Packages, keine externen Paket-Symlinks; einzig _virtualenv.pth mit import _virtualenv. |
| AC5 – Dependencyprüfung | PASS | uv pip check erneut offline: 21 kompatible Pakete, Exit 0; aktive Metadaten-Dependencies ebenfalls geprüft. |
| AC6 – Encoding und soupsieve | PASS | charset-normalizer 3.5.1 aktiv, kein chardet; soupsieve 2.9.2 explizit als neues Profil getestet. |
| AC7 – SQLite-FTS5 | PASS | SQLite 3.50.4; virtuelle FTS5-Tabelle mit eigener Unicodezeile erfolgreich abgefragt; bestehende Datenbanken nicht geöffnet. |
| AC8 – Frische Offline-Regression | PASS | 359 passed im einmaligen zwölfteiligen Schlusslauf; vererbter seccomp-Filter, keine Fehler/Skips/Xfails; ein Realmaterialfall abgewählt. |
| AC9 – F1 weiterhin bestanden | PASS | Alle 14 F1-Fälle aus demselben Schlusslauf bestanden; insgesamt 50 MVP-Fälle einschließlich Prozessrestart und Idempotenz. |
| AC10 – Ruff und Format | PASS | Ruff 0.16.3 aus der frischen venv: check und format --check auf beiden Pythondateien, jeweils Exit 0. |
| AC11 – Historische/private Integrität | PASS | 72/72 historische Manifestdateien und 74/74 geschützte Dateien einschließlich Original/Rawkopien vor/nach Lauf unverändert; Bestand identisch. |
| AC12 – Keine neuen privaten Git-Inhalte | PASS | Nur zwei bestehende Markdown-Lieferdateien ergänzt; persönliche Pfade redigiert; Evidence und Synthetik bleiben außerhalb des Repositorys. |
| AC13 – B1/Stage 0/C16 unverändert | PASS | Sämtliche getrackten Repositorydateien gegen Ausgangsaufnahme identisch; keine Job-Control-/Guardian-/Executor- oder Freigabeänderung. |
| AC14 – Git dokumentiert | PASS | Branch/HEAD unverändert, dieselben fünf ungetrackten Lieferdateien, kein getrackter/gestagter Diff; keine Git-Artefakte angelegt/entfernt. |

### Integrität, Freigabestufen und nächster Schritt

Der private Prompt-22-Bestand einschließlich vorhandener SQLite-Dateien wurde
ausschließlich als Bytes gehasht. **72/72 Manifestdateien** stimmen in Hash,
Größe und Modus; **74/74 geschützte Dateien** und ihr Dateibestand bleiben
vor/nach Tests und Dokumentation identisch. Original und historische Rawkopien
bleiben unverändert. INSTALL-Evidence bleibt ebenfalls vollständig unverändert.
Keine Originaltexte, Approval-/MaterialPlan-Dateien, Datenbanken, Rawkopien oder
privaten Suchausgaben werden in Git übernommen.

| Stufe | Entscheidung |
| --- | --- |
| TECHNICAL PASS | PASS für die aktuellen Pythonbytes und den frischen scoped Vertrag; F1 bestätigt, F2 geschlossen. |
| MVP ACCEPTED | Bestehende fachliche Akzeptanz des historischen Prompt-22-Einzelquellennachweises unter dokumentierter Betreiber-Ausnahme bleibt bestehen; keine neue Realabnahme. |
| INTEGRATION READY | Technisch und inhaltlich für einen eigenständigen PR über genau fünf Lieferdateien vorbereitet; F2 ist kein Blocker mehr. Tatsächliche Integration bleibt pending. |
| MERGE READY | HOLD: Livebasis, Konflikte am dann aktuellen Zielstand, Pflichtreviews und Hosted-CI sind offline nicht verifiziert; Merge ist hier verboten. |
| DEPLOYMENT READY | HOLD / nicht Gegenstand dieses kontrollierten lokalen MVP-Auftrags. |

Nur lokale Git-Daten geprüft: gespeichertes `origin/master` entspricht HEAD
`a8af1d9…`; der lokale `master` bei `c1007efd…` ist ein Vorfahr und liegt
**173 Commits zurück**. Keine der fünf Lieferdateien existiert in diesen beiden
Refs oder im lokalen Stage-0-Reviewref `929fb1e1…`.
Damit ist kein gleichnamiger Add/Add-Konflikt in diesen gespeicherten Bäumen
sichtbar; eine aktuelle Mergekonfliktfreiheit wird daraus nicht abgeleitet.
Der Stage-0-Reviewref liegt zwei Commits vor der Basis und ändert unter anderem
`src/tools_materials/storage.py`, acquisition und text_validation. Gemeinsame
Integration kann daher Implementierungsfingerprint und Verhalten ändern und
braucht dann neue Regression. Fremde Worktreeinhalte wurden nicht übernommen;
Live-GitHub und der aktuelle PR-#171-Status wurden nicht geprüft. Keine
Remote-Git-/PR-Aktion und keine Freigabe von PR #171.

Die MVP-Grenzen gelten weiter: einzelne lokale HTML-Quelle, lexikalisches
Retrieval, serieller expliziter Operator; keine neue Job-Control-, LLM-,
Embedding-, Knowledge-, Worker- oder Produktionsfreigabe. F3 (Bootstrapstatus
benötigt Intent/State) und F5 (synchrone HTML-Verarbeitung ohne harte
Prozesszeit-/Speicherisolation) bleiben bestehen. F4 ist für diesen Testlauf
zusätzlich durch die vererbte OS-Socketsperre abgedeckt; die produktive
Implementierung erhält dadurch keine eigene Netzisolation. Prompt 22 bleibt
historischer Nachweis für seinen damaligen Fingerprint. Die einmalige
Onlineabweichung bleibt dokumentiert und akzeptiert; keine neuen Abrufe.

Git-Endzustand wie zu Beginn:

```text
?? docs/cs50/one-source-retrieval-mvp.md
?? docs/cs50/one-source-retrieval-validation.md
?? scripts/cs50_learning_mvp.py
?? tests/profiles/cs50-mvp-requirements.txt
?? tests/test_cs50_learning_mvp.py
```

Nur die beiden Markdowndateien haben gegenüber dem VERIFY-Ausgang neue Bytes;
Operator, Tests, Requirements und alle getrackten Dateien bleiben unverändert.
`git diff --check` und Whitespace-/Pfad-/Linkprüfung der Lieferdateien sind
bestanden. Keine Commits, Pushes, PR-Erstellung, Merges oder neuen Git-Artefakte.
Der vorhandene Branch/Worktree und die private venv samt Nachweisen bleiben
erhalten. Die dauerhafte Integration der Dokumente in den tatsächlichen
Defaultbranch `master` bleibt gemäß AGENTS.md **pending**, weil dieser Auftrag
Integration ausdrücklich verbietet; kein allgemeiner Lifecycle-Abschluss und
keine Bereinigung werden behauptet. Nächster Schritt ist separat autorisierter
PR-/Reviewprozess über genau die fünf Lieferdateien mit aktueller Zielbasis.
