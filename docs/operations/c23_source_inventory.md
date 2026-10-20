# C23-03: Reimport, Retry und explizites Quelleninventar

Bestandsaufnahme vor Implementierung, 18.10.2026. Basis: Master `5986da9`
(C23-02A/B/C, PRs #76–#78 gemergt). Maßgeblich bleiben
[ADR](../architecture/parsed_content_persistence_adr.md),
[Datenmodell](../architecture/parsed_content_data_model.md),
[Betriebsvertrag](content_store_recovery.md),
[Issue-Entwurf](../planning/issue_plan.v1.json) und
[Governance](../planning/governance.md). C23 bleibt offen.

## Anforderungs- und Gap-Matrix vor Änderung

| Anforderung | Vorhandene Implementierung | Bestehender Test | Fehlende Abnahme / Einordnung |
| --- | --- | --- | --- |
| Idempotenter Reimport | `publication.publish`, Slot/Version-ID und Requestfingerprint | A `test_t05_idempotence_keys_slots_and_changed_parser`; B `test_new_audit_receipt_does_not_rewrite_published_version` | Teilweise nachgewiesen: kombinierter B-Neustart-/Rawversionsnachweis ergänzen |
| Parser-/Source-Versionierung | Manifest/SV unabhängig von vollständigem Parserconfigfingerprint | A `test_t05_new_raw_version_preserves_the_previous_version`; B `test_changed_parser_configuration_is_separate_version`, `test_same_slot_conflict_and_new_parser_revision` | Teilweise nachgewiesen: neue Rawbytes mit tatsächlichem B-Gate ergänzen |
| Requestkey-Konflikte | Actor/Key unique, unveränderlicher Fingerprint; Slotunique | A/B Konflikttests, C `test_parallel_conflicting_request_is_not_a_new_winner` | Vollständig für Parsed nachgewiesen; Retry muss Source/Slot/Attempt zusätzlich binden |
| Mehrprozess-Reimport | Nichtblockierende Run-/DB-/Maintenancelocks, aktiver Slotunique | C `test_two_processes_same_slot_and_reader`, `test_two_processes_different_sources_can_complete` | Vollständig nachgewiesen; ausschließlich parallelen Retry ergänzen |
| Recovery nach Reject | `recover_run(action="reject")` erhält Run/Manifest/Intent; Parsed mit neuem Key möglich | C `test_crash_state_boundaries` | Raw-/Binding-Retry nicht implementiert: interne deterministische Keys bleiben terminal gebunden |
| Material-Source-Binding | Eingefrorenes Bundle, C10-Gate, vollständiger Graph, Receipt/Revision/Hashes/Locatoren | B `test_material_end_to_end_restart`, Korruptions-/Parser-/Bildfälle | Teilweise nachgewiesen: gezielte falsche Herkunft/Graph-/Revisionsfälle ergänzen |
| SRT-Source-Binding | Vollständiger Adapterplan, Executorpfade, zwei Actions, Original-Reparse | B `test_srt_end_to_end_restart`, `test_receipt_invariants`, Reparsefälle | Teilweise nachgewiesen: Section/Sourcepointer und explizite synthetische Kopie ergänzen |
| Historischer Pfadkonflikt #72 | Falsche physische Pfade werden abgewiesen; kein Fallback | B `test_historical_path_conflict_is_not_adopted`; fünf C21-Q.1-Fälle in offenem #72 | Blockiert durch externe Freigabe D06; keine realen Dateien übernehmen |
| Explizites Bestandsinventar | Bundlemodelle/Gates und autorisierte Store-Reads vorhanden | B Read-only-/ACLtests | Maschinenreport noch nicht implementiert; explizite Liste ohne Storewrites ergänzen |

Die folgenden Abschnitte dokumentieren den endgültigen Vertrag und die tatsächlich
ausgeführten Nachweise. Die Matrix beschreibt bewusst den unveränderten Ausgangsstand.

## Tatsächliche Bindungskette und Identitäten

1. `CourseDiscovery`/`ResourceCandidate` in `model_discovery.cs50` liefern den
   vollständigen Course-/Section-/Resourcegraphen. Die bestehende Resource-ID
   berücksichtigt Course, Rolle, Original-URL, Sprache und Parent; sie wird im
   ContentStore nicht neu erfunden. `select_cs50`/`adapt_cs50` beziehungsweise
   `MaterialPlan` prüfen die Lecturezuordnung gegen diesen Graphen.
2. `MaterialResource.source_id` übernimmt die Resource-ID; `material_id` bindet
   zusätzlich die konkrete Variante/URL. `lecture_ids` referenzieren Lectures,
   nicht das Material selbst. `CS50TranscriptBinding` bindet die Subtitle-Resource
   (`source_id == resource_id`) an eine **andere** Lecture-ID, Section, Sprache,
   Original-URL, Provenienz und Originalpfade. `media_id` ist keine Source-ID.
3. Material: `ArtifactReceipt` verbindet Rawhash, Parserconfig, exakten
   Normalized-Payloadhash, Bildhashes und Speicherpfade. `NormalizedDocument`
   enthält ursprüngliche Dokument-/Block-IDs und Locatorinformationen.
   SRT: `CS50Executor`/`validate_document` verbinden unveränderte Rawbytes,
   vollständige Segmentmodelle, Text, Quellenpointer und Provenienz. Das
   Executionreceipt muss exakt zwei zum geprüften Adapterplan gehörende
   done-Actions mit Raw-/Payload-/Inputhash enthalten.
4. Die B-Adapter frieren genau die expliziten Bytes ein, prüfen den vollständigen
   Graphen und Receipt und führen Materialgate/Handoff beziehungsweise
   SRT-Originalvergleich aus. `ImplementationEvidence` ist ein ausdrücklich
   bereitgestellter lokaler Revisionsbeleg, keine nachträglich aus HEAD erratene
   historische Parserrevision und keine Herausgebersignatur.
5. `SourceRegistration` erhält die Source-ID und bindet Herkunft/Original-URL.
   `SourceVersion` bindet Variante, sortiertes Rawmanifest und den unveränderten
   Binding-Snapshot. Rawreservierungen sind sourcegebunden; gleiche SHAbytes
   übertragen keine fremde Quellenberechtigung. Ein neuer Parser erzeugt keine
   neue Rawversion. Neue Rawbytes erzeugen eine neue SourceVersion.
6. `ParsedDocumentVersion` bindet SourceVersion, Stream und vollständige
   Parser-/Adapter-/Implementierungskonfiguration als Slot sowie die **exakten**
   Payload-/Projektionshashes. Referenzen archivieren Payload, Projektion,
   Binding, Receipt, Plan, Revision und Gate/Handoff. Block-/Segment-/Locator-IDs
   und Originaltexte bleiben erhalten. TOC-/Link-/Codeviews bleiben die
   vorhandenen C10-Projektionen; keine neue Aggregation oder Knowledge-Extraktion.

Die Kette ist implementiert. HTTPintegration, paginierte öffentliche Reads,
automatische Bestandsübernahme und fachliche Realmaterialabnahme sind weiterhin
Folgearbeit. Es wurden keine realen Originaldateien für C23-03 eingelesen.

## Minimaler Retry-Vertrag v1

Die nachgewiesene Lücke betrifft `store_raw_artifact` und
`register_source_version`: Ihre bisherigen Keys sind deterministisch aus dem
Raw-/Bindingslot abgeleitet. Ein bewusst verworfener Run hält seinen Key dauerhaft;
ein weiterer gewöhnlicher Aufruf bleibt `Unavailable`. Parsed-Publikation hat
bereits einen expliziten Aufruferkey und benötigt nur einen neuen Key nach Reject.

Additive optionale Keywords, bestehende Aufrufe funktionieren unverändert:

```python
from src.content_store.models import RetryAttempt
from src.content_store.adapters import import_verified_bundle, verify_material_bundle

attempt = RetryAttempt(
    schema_version=1,
    rejected_run_id="0123456789abcdef0123456789abcdef",  # tatsächlich geprüfter Run
    request_key="raw-attempt-2",                         # neuer expliziter Key
)
result = import_verified_bundle(
    store, verify_material_bundle(bundle), actor=operator,
    request_key="parsed-attempt-2", raw_retry=attempt,
)
# Für einen verworfenen Bindingrun stattdessen binding_retry=attempt.
# Low-level: store_raw_artifact(..., retry=attempt),
# register_source_version(..., binding=candidate, retry=attempt).
```

Nur `rejected` mit `error_code="operator_abandoned"` ist ein zulässiger Vorgänger.
Actor, Source, Runart, Slot und vollständiger bisheriger Requestfingerprint müssen
übereinstimmen. Ein konfliktbedingt abgelehnter Run, ein aktiver/blocked Run oder
ein anderer Scope legitimiert keinen Retry. Alter und neuer Key müssen verschieden
sein. Schlüssel bleiben global je Actor gebunden, auch zwischen Sources/Runarten.
Es gibt keine automatische Auswahl eines Vorgängers, keine Zeitfreigabe und kein
Zurücksetzen terminaler Runs.

Der neue Run besitzt eine neue UUID, aktuelle ACLrevision, eigene Stagingdateien,
eigenen Intent und optionalen JSONbezug `ProcessingRun.retry_of`. Die gleiche
SQLreservation prüft den Vorgänger und sperrt den bestehenden fachlichen Slot.
Ein vorhandenes Vorgängermanifest muss mit den neu geprüften Referenzen
übereinstimmen; ein vorhandener Recoverybeleg muss weiterhin katalogisiert,
verfügbar und hashintakt sein. Ein unvollständiger `preparing`-Vorgänger ohne
solchen Beleg autorisiert keine Wiederaufnahme seiner Bytes: der neue Attempt
beginnt vollständig neu mit erneuter Prüfung.
Recovery und Integritätsprüfung prüfen die persistierte Retryverknüpfung erneut.
Alle ursprünglichen Run-/Manifest-/Intentbytes bleiben erhalten. Ein wieder
unterbrochener Retry nutzt dieselbe C-Recovery; er wird nicht automatisch gestartet.

Der B-Import prüft das neue Bundle vollständig erneut. Die Raw-only-API prüft
weiterhin ihre deklarierte Größe/SHA, Source und Rechte; sie kann allein keine
SourceVersion oder Parsed-Version veröffentlichen. Binding/Pub verlangen unverändert
den echten B-Candidate und erneut das Gate. Quarantäne-/Tombstone-/Rechteprüfungen
werden nicht gelockert. Geänderte Payload im selben Parsed-Slot bleibt `Conflict`.

Weitere explizite Attempts desselben erlaubten Vorgängers können nach Erfolg
dieselben intakten Raw-/Source-/Parsed-Daten wiederverwenden, erzeugen aber keine
zweite Rawreservation/SourceVersion/Parsed-Version und überschreiben keine
Auditbelege. Bei derselben Parsed-Version mit anderem Requestkey werden neue
geprüfte Belege wie bisher separat archiviert. Derselbe Parsedkey mit abweichenden
Belegen bleibt ein Konflikt. Die ursprünglichen deterministischen Rawkeys werden
nach Erfolg eines Retry **nicht** still umgebogen; Folgeaufrufe geben den passenden
Retry-Attempt ausdrücklich wieder an.

Kompatibilität: kein SQLschemawechsel, keine Migration und keine Änderung der
Source-/Slot-/Versions-/Blobfingerprints. `RetryAttempt` ist ein strenger Vertrag
mit `schema_version=1`; fehlendes `retry_of` alter Run-JSONs bedeutet keinen Retry.
Gewöhnliche neue Runs behalten die bisherige serialisierte JSONform ohne dieses
Feld. Sobald Retrybelege existieren, benötigen Reader/Recovery die C23-03-Modelle;
ältere strenge Reader können dieses neue optionale JSONfeld nicht interpretieren
und müssen fail-closed bleiben. Kein unterstütztes Downgrade durch Entfernen der
Auditverknüpfung. Dieses Paket erweitert weder C16 noch C18/C20 oder C22.

## Explizites Inventar und Maschinenreport

[`inventory.py`](../../src/content_store/inventory.py) verwendet direkt die
unveränderten B-Snapshot-/Gatefunktionen. Kein zweiter Parser und kein separater
Zulassungsmechanismus. Input `InventoryRequest`, Schema 1, enthält 1–64 eindeutig
benannte `InventorySelection`-Einträge: `entry_id`, `kind` (`material`/`srt`),
erwartete `source_id`, `course_id`, ausdrücklich erwartete 40-stellige
`expected_implementation_revision` und das bestehende `MaterialBundle` oder
`SRTBundle`. Workspace absolut; alle Dateien explizit. Kein Rootscan, keine
URLauflösung und keine Suche nach ähnlichen Dateinamen.

Beispiel eines Eintrags (Pfadplatzhalter; Revision ausdrücklich bereitstellen):

```json
{
  "schema_version": 1,
  "entries": [{
    "schema_version": 1,
    "entry_id": "python-0-srt",
    "kind": "srt",
    "source_id": "resource:<bestehende-id>",
    "course_id": "cs50_python",
    "expected_implementation_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "bundle": {
      "workspace": "/private/explicit-workspace",
      "raw_path": "data/lectures/Harvard/<exakter-bindingpfad>/source.srt",
      "transcript_path": "data/lectures/Harvard/<exakter-bindingpfad>/transcript.json",
      "receipt_path": "data/lectures/Harvard/<exakter-bindingpfad>/execution.v1.json",
      "plan_path": "/private/evidence/plan.json",
      "implementation_path": "/private/evidence/implementation.json",
      "source_id": "resource:<bestehende-id>",
      "source_origin": "official"
    }
  }]
}
```

CLI nach bestehender `scripts.cs50_*`-Konvention:

```sh
python -m scripts.cs50_content_inventory \
  --selection /private/selection.json --actor owner --course cs50_python \
  --store /private/existing-content-root --output /private/new-inventory.json
```

`--store` und `--output` sind optional. Ohne Store nur Bundleprüfung; ohne Output
JSON auf stdout, kurze Zusammenfassung auf stderr. Der offline Operatorprincipal
ist expliziter Bibliotheks-/CLIinput unter der lokalen Dateisystemberechtigung,
kein neuer HTTPauthentisierungsweg. Vorhandener Store wird ausschließlich read-only
geöffnet; bestehende Source benötigt Operator/Ownership/Course für Importbereitschaft.
Keine Initialisierung, Source-/Blobregistrierung, Reservierung, Quarantäneänderung,
Recovery, Migration oder automatische Importausführung. Nur private temporäre
Gate-Snapshots außerhalb der Inputs/Store, anschließend automatisch entfernt.

Ausgabe: `InventoryReport` mit `report` und `sha256 = H(J(report))`. Body Schema 1,
kind `cs50-content-inventory-v1`, geordnete `entries`. Je Eintrag: Source/Course/Typ,
erwartete Revision, explizit gelieferte und aus dem Binding erwartete Originalpfade,
Section-/Lecture-IDs, beobachtete Raw-/Payload-/Receipt-/Plan-/Revisionshashes,
verifizierte vollständige Parserconfig, berechnete SourceVersion, gegebenenfalls
bereits publizierte Parsed-Version, `validation_status` (`verified`/`blocked`),
feste `issues`-Codes und `manual_approvals`. `null` bedeutet nicht nachgewiesen,
nicht automatisch die neueste Version. Fehlende Dateien bleiben Fehler; vorhandene
Einzelbeobachtungen eines unvollständigen Bundles sind ausdrücklich kein Gateerfolg.
Erwartete Pfade vor Gateerfolg sind deklarierte, noch nicht bestätigte Bindung.

`verified` bedeutet bestandene technische Bundleprüfung und gegebenenfalls
konsistenter gegenwärtiger Storevergleich. Es garantiert keinen späteren Commit:
ACL, Aktivruns, Quota und Zustand werden beim tatsächlichen Import neu geprüft.
Nichtsynthetische Bestände behalten D06/D07 als manuelle Freigaben; unbekannte
Herkunft wird nicht automatisch freigegeben. Keine fachliche Modellqualitätsaussage.
Reports enthalten ausdrücklich ausgewählte lokale Pfade/IDs, keine Volltexte und
keine Credentials; sie sind private Operationsbelege, keine HTTP-DTOs.

[Beispielreport](examples/c23_source_inventory.v1.json): tatsächlich mit den
synthetischen HTML-/SRT-Fixtures und dem bestehenden Gate erzeugt. Ausschließlich
die temporären Workspacepräfixe wurden durch `/example/c23-03` ersetzt und der
Bodydigest danach neu berechnet/geprüft. IDs und Originaldateihashes der
synthetischen Fixtures blieben erhalten. Das Beispiel behauptet keine existierenden
Dateien unter `/example`, keinen realen Korpus und keinen Contentimport.

Output wird ausschließlich neu publiziert. Bestehende Dateien, Symlinks sowie
Ziele innerhalb von Eingabeworkspaces/Store oder auf einzelnen Inputs/Selection
werden zurückgewiesen. Exitcodes: 0 alle technischen Gates bestanden, 1 mindestens
ein Bundle blockiert, 2 Eingabe/Store/Reportpublikation nicht ausführbar. Ein 0-Code
ersetzt keine manuelle Freigabe. Wiederholung unveränderter Inputs/Store liefert
identische Reportbytes; der Digest umfasst den Body ohne Selbsthashkreis.

## #72: historischer Konflikt und spätere Übernahme

[Draft-PR #72](https://github.com/rf-data/Personal_Assistant/pull/72) einschließlich
C21-Q.1 wurde lesend geprüft. Die Binding-/Receipt-/Dokumentpointer stimmen unter
`data/lectures/Harvard/...` überein, der damals beobachtete physische Bestand lag
unter `data/Harvard/...`. Der kanonische Root besteht seit dem ursprünglichen
Adapter. Executor und Binder verwenden Workspace plus exakten Bindingpfad,
unabhängig von `DATA_DIR`; eine neue falsche Pfadkonstruktion ist nicht belegt.
Das konkrete historische Verschiebe-/Provisionierungsereignis bleibt unbekannt.
Keine neue Untersuchung realer Dateibytes oder Behauptung erfolgter Migration.

Der unveränderte B-Adapter lehnt beide Fälle ab: fehlende kanonische Datei und
explizit als Input gelieferte bytegleiche Datei am historischen falschen Pfad.
Nur synthetische Testtripel wurden in temporären Roots ausdrücklich kopiert.
Ein manipuliertes Tripel, fehlendes Receipt oder widersprüchlicher Sourcepointer
bleibt `UnverifiedBinding`; weder Dateiname noch identischer Hash ersetzt Herkunft.

Vor einer späteren tatsächlichen Übernahme:

1. D06 ausdrücklich für konkrete Quellen, Quelldateien und **neuen** kanonischen
   Zielworkspace freigeben; berechtigten Zugriff bestätigen. D07 für Korpus,
   Reviewer, unabhängige Referenzen und fachlichen Releaseumfang klären.
2. Explizite Bundleliste mit originalem Adapterplan/Binding, Raw, Receipt,
   Payload und belegter Parserrevision erstellen. Fehlende Belege sperren;
   keine Rekonstruktion aus ähnlichen Beständen, URLs oder aktuellem HEAD.
3. Vorher-SHA/Größe und vollständige Source-/Course-/Section-/Lecture-/Resource-
   Identitäten lesend protokollieren. Inventar nennt Konflikte und bestehende
   Storeversionen, führt aber keinen Import aus.
4. Erst nach gesonderter Freigabe unveränderte Dateien exklusiv an die genau
   gebundenen Pfade im neuen Workspace kopieren. Originale/Receipts erhalten,
   keine Links oder Rewrite. Dieser Schritt ist **nicht implementiert/ausgeführt**.
5. Nachher-SHA/Größe mit Vorherbeleg vergleichen, vollständigen B-Validator und
   Inventar erneut ausführen; Kopierfehler/Bindungskonflikte blockieren.
6. Ein Operator prüft Report und Freigaben. Einen tatsächlichen Contentimport
   anschließend separat mit expliziten Keys beauftragen; Roundtrip von Raw,
   Payload, Receipt, Locator und stabilen IDs gegen Vorherbelege abnehmen.

Keine realen Daten wurden verschoben/kopiert, keine bestehenden Receipts verändert,
keine Symlinks angelegt und keine alternative Rootsuche eingeführt. D06/D07 bleiben
offen. C23-04 übernimmt spätere HTTP-/Pagination-/C16integration, C23-05 TXTzeiten,
C23-06 Realmaterialqualität und C26 Produktions-/Verbundbackupabnahme. Kein Go-live.

## Tatsächliche Offlineabnahme

Python **3.12.12**, Pydantic **2.13.5**, SQLite **3.50.4**, BeautifulSoup **4.15.0**,
System-Pytest **7.2.1**, Ruff **0.16.0**. Vorgesehene Projektvenv/Pytest 9 sowie
PyMuPDF waren nicht nutzbar; keine Installation oder Downloads. Vorhandener
Interpreter aus `ai-job-search/.venv` mit System-Pytest über `PYTHONPATH`, ohne
Plugin-Autoload. Pytest-7-AST-Warnungen unter Python 3.12 sind keine Skips.

| Lauf | Pass / Fail / Skip / Setupfehler | Nachweis |
| --- | --- | --- |
| Gemeinsame C23-03-/A-/B-/C-Suite | **222 / 0 / 0 / 0**, 487,65 s | 49 damalige neue Fälle plus sämtliche 173 A/B/C-Fälle, echte Dateien/SQLite/Prozesse |
| Inventar nach Ergänzung der tief verschachtelten Fehlerinputs | **26 / 0 / 0 / 0**, 26,26 s | Ganzes Inventarmodul, davon zwei zusätzliche Randfälle; Überschneidung, nicht addieren |
| Abschließende gesamte C23-03-Nachprüfung nach Vorgängerbelegschutz | **53 / 0 / 0 / 0**, 114,27 s | 27 Reimport-/Retryfälle und 26 Inventarfälle einschließlich aller vier nach dem gemeinsamen Lauf ergänzten Randfälle |
| Erweiterte Material-/Discovery-/Lecture-/Transcript-/Knowledge-Provenienz-/C16-Regression | **238 / 8 / 2 / 94**, 150,23 s | Acht unveränderte Baselinefehler; 94 C10-Fixturefehler wegen fehlendem PyMuPDF |
| Unveränderter Master `5986da9`: Transcript + HTMLsemantik + ein C10-Fixturefall | **48 / 8 / 1 / 1**, 18,78 s | Exakt dieselben acht fehlschlagenden Nodes und derselbe PyMuPDF-Setupfehler |
| Ruff Check / Format Check / `git diff --check` | **erfolgreich** | 29 Pythondateien; JSONschema und Beispielreportdigest ebenfalls geprüft |

Die gemeinsame Suite lief vor der letzten Vorgängermanifest-/Recoverybelegprüfung
und den zwei dazugehörigen Negativfällen. Die abschließende vollständige
Reimport-/Inventarnachprüfung ist deshalb gesondert ausgewiesen; kein angeblich
ausgeführter 226er-Gesamtlauf und keine Addition überlappender Läufe.

Die acht bestehenden Fehler sind die sechs TXT-Importnodes
`test_txt_unknown_timestamps_paragraphs_and_unicode`,
`test_explicit_encoding[cp1252]`, `test_explicit_encoding[utf-16]`,
`test_exclusive_save_and_no_overwrite`,
`test_knowledge_chunking_contract_without_llm_imports`,
`test_import_does_not_load_whisper_or_application_settings`
aus `test_official_transcript_import.py` (Nonezeiten gegenüber float) und beide
Wrapper von `test_cs50_material_html_semantics.py::test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
(`héllo` → `h√©llo`). Fehlgeschlagene Node-Listen zwischen Baseline und Branch
maschinell verglichen: identisch. Keine Änderung der TXT-/HTMLparser.

Alle **94 Setupfehler** des zusätzlich versuchten
`tests/test_cs50_material_quality.py` stammen aus derselben moduleweiten
`sources`-Fixture: sie erzeugt auch für HTMLfälle ein PDF und der vorhandene
PDFworker scheitert an `ModuleNotFoundError: No module named 'pymupdf'`.
Dieser Fehler wurde an einem unveränderten Masterfall reproduziert. Das sind
fehlende Laufzeitnachweise, keine bestandenen/skipped PDFprüfungen und keine
neu als Altfehler etikettierten Assertionfehler. Weitere PyMuPDF-Parsermodule
wurden nicht ausgeführt. Beide Regression-Skips betreffen optionale echte
HTML-/SRT-Bestände; im kleineren Baselinelauf nur der HTML-Skip. Keine vollständig
grüne Regression, keine fachliche Gold-/Modellqualität aus synthetischen Fällen.

Gemeinsames tatsächliches Präfix, jeweils Log außerhalb des Repositories:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

Gemeinsame Suite mit diesem Präfix:

```sh
-q --disable-warnings \
 tests/test_content_store_reimport.py tests/test_content_store_inventory.py \
 tests/test_content_store_recovery.py tests/test_content_store_concurrency.py \
 tests/test_content_store_integrity.py tests/test_content_store_backup.py \
 tests/test_content_store_limits.py tests/test_content_store_models.py \
 tests/test_content_store_artifacts.py tests/test_content_store_store.py \
 tests/test_content_store_adapters.py --basetemp=/tmp/c2303-acceptance
```

Inventarnachprüfung: `-q --disable-warnings tests/test_content_store_inventory.py
 --basetemp=/tmp/c2303-inventory-release`.

Abschließende gesamte C23-03-Nachprüfung mit demselben Präfix:
`-q --disable-warnings tests/test_content_store_reimport.py
 tests/test_content_store_inventory.py --basetemp=/tmp/c2303-final-targeted`.

Regression mit demselben Präfix:

```sh
-q --disable-warnings \
 tests/test_cs50_material_contracts.py tests/test_cs50_material_html.py \
 tests/test_cs50_material_html_semantics.py tests/test_cs50_material_code.py \
 tests/test_cs50_material_mapping.py tests/test_cs50_material_quality.py \
 tests/test_cs50_discovery.py tests/test_cs50_lecture_adapter.py \
 tests/test_cs50_executor.py tests/test_official_transcript_import.py \
 tests/test_knowledge_transcript_provenance.py tests/test_job_control.py \
 --basetemp=/tmp/c2303-regression
```

Baseline: lokales `git archive 5986da958d767f66e24850df25085ccbebe9ee3e src tests
 docs/course_sources scripts deployment pyproject.toml uv.lock`, ausschließlich
in `/tmp/c2303-baseline` entpackt. **Dort** dasselbe Pytestpräfix mit
`-q --disable-warnings tests/test_official_transcript_import.py
 tests/test_cs50_material_html_semantics.py
 'tests/test_cs50_material_quality.py::test_valid_v2_preserves_sources_and_is_deterministic[html]'
 --basetemp=/tmp/c2303-baseline-tests-verified`.

Ruff `check` und `format --check` jeweils für `src/content_store`,
`scripts/cs50_content_inventory.py`, `tests/content_operations_support.py`,
`tests/content_store_process.py`, `tests/test_content_store_*.py`,
`tests/content_adapter_support.py`, `tests/content_store_support.py`;
anschließend `git diff --check`. Keine vollständige Repositorytestsuite.

| Anforderung nach Änderung | Tatsächlicher Nachweis |
| --- | --- |
| R01, stabile IDs/Versionen | Neue Code-Rawbytes mit tatsächlichem B-Gate erzeugen neue SourceVersion; alte Raw-/Payload-/Receiptbytes nach Neustart identisch. Gleicher/anderer Parsedkey dedupliziert; A/B-Parserconfig-/Implementierungsrevision-/Slotkonfliktfälle wiederverwendet. |
| R02, Reject/Retry | SIGKILL bei Raw/Binding in `preparing` und `prepared`; bewusster Reject; neuer expliziter Attempt; alte Run-JSONs byteidentisch, keine neuen Datengewinner bei weiteren Attempts. Aktiver/fremder/abweichender Vorgänger blockiert; vollständiges neues Gate, Quarantäne und aktuelle Rechte bleiben wirksam. Parsed benötigt weiterhin nur neuen expliziten Key. |
| R03, Source Binding | Material-/SRT-Roundtrip aus B, falsche Herkunft trotz gleicher Bytes, Receipt-/Resource-/Lecture-/Section-/Revisionsbelege, Sourcepointer und fehlende Belege. Inventar vergleicht ausdrücklich erwartete Revision gegen tatsächlich geprüfte Revision. |
| R04, #72 | Sechs vollständig synthetische Tripelfälle: erwarteter Root, falscher Root, explizite bytegleiche Kopie in neuen Workspace, manipulierte Kopie, fehlendes Receipt und widersprüchlicher Sourcepointer. Historische synthetische Quelldateien bleiben nach Kopie unverändert; kein Fallback. |
| R05, getrennte Prozesse | Zwei neue parallele Raw-/Binding-Retryfälle: zweiter Prozess Busy/Unavailable, danach gleiche Version; zwei erneut unterbrochene Retryfälle über C-Recovery fortgesetzt. Vier bestehende C-Parallelitätsfälle (gleiche/verschiedene Quellen/Keys, aktiver Reader, widersprüchlicher Key) wiederverwendet. |
| Inventar | Schema, feste Auswahlgrenzen, HTML/PDF-v2-Vertrag/SRT, Store-/Inputbytes und Modi unverändert, Rechte/Quarantäne/Slotkonflikt, deterministischer Hash, No-Overwrite/Outputschutz, malformed/duplizierte/nonfinite/tiefe JSONinputs. PDF-Vertragsfixture behauptet keinen PDFparserlauf. |

Entwicklungsergebnisse sind getrennt: zunächst 20 pass/1 fail (falscher
Raw-Read-Testaufruf), ein Inventar-Collectionfehler (Testimport), danach
14 pass/10 fail (Testhelper verwendete die berechnete Resource-ID als JSONfeld).
Alle drei Testfehler korrigiert, gemeinsamer Zwischenlauf 45 pass. Ein initialer
Regressionsaufruf benannte ein nicht vorhandenes Testmodul (0 gesammelt), danach
der oben vollständig ausgewiesene Lauf. Ein erster Baseline-Exportversuch scheiterte
an einer System-Tarfile-API und lief anschließend versehentlich im Taskworktree;
dieser Lauf gilt **nicht** als Baseline. Erst der oben genannte unabhängig
entpackte, verifizierte Masterlauf ist der Baselinebeleg. Kein Entwicklungsfehler
wird als Altfehler oder erfolgreiche Abnahme ausgegeben.

Temporäre Fixture-/Test-/Archiv-/Cacheverzeichnisse dieses Auftrags werden nach
Abnahme entfernt; technische Logs bleiben außerhalb des Repositories. Der eigene
Featureworktree bleibt bis zum Merge des offenen PR erhalten. Andere Worktrees,
Branches, Originaldaten, Venvs und Umgebungsdateien werden nicht bereinigt.
