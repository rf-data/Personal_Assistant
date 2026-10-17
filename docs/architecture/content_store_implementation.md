# C23-02A/B: ContentStore und geprüfte CS50-Adapter

Stand **17.10.2026**. C23-02B ergänzt den gemergten A-Kern auf Master
`6ef394a2f7a4debccce75f7b5e1ef3449f9457aa` (PR #76). Der folgende
[B-Abschnitt](#c23-02b-geprüfte-bundleadapter) beschreibt den aktuellen
Bibliotheksvertrag. Die A-Abschnitte/Testläufe darunter dokumentieren den
vorherigen Stand; ihre damalige Publikationssperre wird ausschließlich für
geprüfte B-Kandidaten aufgehoben. **Keine produktive Contentpipeline**. D04 wurde im C23-02A-Auftrag ausdrücklich für
SQLite plus unveränderliche Dateien und Offlineprüfungen freigegeben. C23 bleibt
insgesamt offen; Daten-/Migrations-/Deploymentfreigaben entstehen dadurch nicht.

Branchbasis ist `master` `a2dc080ac5896c9c8032f42bf51ecb5fdb9a71c6`, der
während des Auftrags das C23-01-ADR aus PR #75 aufgenommen hat. Vor Veröffentlichung
wurde der isolierte Branch auf diese Basis aktualisiert. Die ausgeführten Tests
beziehen sich auf die vorherige Laufzeitbasis `053209ad89fac828c7f47677056c44a624ac1af7`;
zwischen beiden Bases unterscheiden sich ausschließlich Dokumentationsdateien.
[ADR](parsed_content_persistence_adr.md),
[Datenmodell](parsed_content_data_model.md) und
[Umsetzungsplan](../planning/c23_implementation_plan.md) sind damit direkt im
Master vorhanden. Maßgeblich bleiben ihre Hashdomänen/IDs; folgende Einschränkungen
konkretisieren die ausdrücklich beauftragte Aufteilung A/B/C.

## Paket und tatsächliche Verantwortlichkeiten

| Datei | Implementierter Umfang |
| --- | --- |
| [`__init__.py`](../../src/content_store/__init__.py) | Exportiert ausschließlich `ContentStore`; kein globaler Store, keine Settingsinitialisierung |
| [`models.py`](../../src/content_store/models.py) | Source, SourceVersion, RawArtifact/Manifest, ParsedDocument/-Version, ContentBlock/-Locator, ParserConfiguration, ProcessingRun, ArtifactReference, SourceGrant; separate SourceView/ParsedDocumentView; canonical JSON und deterministische Hashes |
| [`errors.py`](../../src/content_store/errors.py) | Acht vereinbarte Fehlerklassen mit festen Codes und redigierten Operationstexten; kein Weiterreichen roher SQLite-/OSmeldungen |
| [`artifacts.py`](../../src/content_store/artifacts.py) | Interner privater FD-basierter Blob-/Stagingstore, Root-/Inode-/Dateitypprüfungen, Größen-/SHA-Prüfung, Sperren und exklusive Publikation |
| [`schema.py`](../../src/content_store/schema.py) | Exakte content-v1-DDL, Schema-ID/Application-ID, Constraints und Unveränderlichkeitstrigger; kein C16-Schema |
| [`store.py`](../../src/content_store/store.py) | Explizite Initialisierung/Wiederöffnung, SQLtransaktionen, Source-/Grant-/Rawoperationen, Run-/Manifestbausteine und autorisierte Reads; B-Publikation ausschließlich nach Adaptergate |
| [`adapters.py`](../../src/content_store/adapters.py) | Explizite Material-/SRT-Bundles, unveränderlicher Snapshot, Gate/Reparse, Prozess-lokaler Candidate |
| [`publication.py`](../../src/content_store/publication.py) | Kleine Integration in vorhandene Run-/Staging-/SQL-Primitiven; Quellenbindung und atomare Parsed-Publikation |
| [`_testing.py`](../../src/content_store/_testing.py) | Nicht exportierter synthetischer Testvertrag; konkrete fünfstufige Publication in dauerhaft als Test markierter Datenbank, keine Produktionspromotion |

Vorhandene `Principal`-/`Contract`-Formen und
`model_discovery.cs50.deterministic_id` werden direkt wiederverwendet. Das Paket
importiert weder Knowledge-/Entity-/LLM-/Embeddingmodelle noch Parser-/Settings-
oder Queueinitialisierung. C16s `Store` wird nicht aufgerufen. Bestehende
`safe_path`-Hilfen prüfen überwiegend Pfadnamen vor dem Öffnen; für den neuen
Blobstore wird stattdessen jeder Verzeichnisbestandteil über `openat` mit
`O_DIRECTORY|O_NOFOLLOW` geöffnet. Auch die exklusive Linkpublikation und fsync
folgen den bestehenden POSIX-Invarianten, ohne Originaldateien zu hardlinken oder
die Hilfen pauschal umzubauen. Dies erfordert keine zusätzliche Dependency.

## Initialisierung und Schema

`ContentStore.initialize(explicit_absolute_root)` ist die einzige öffentliche
Initialisierung. Sie akzeptiert nur einen neuen oder bereits leeren privaten
Root außerhalb des Repositories; dessen Parent muss existieren. Nichtleere Roots,
auch mit fremdem `jobs.sqlite3`, werden nicht übernommen. `ContentStore(root)`
öffnet ausschließlich bereits initialisierte Bestände und ist standardmäßig
read-only. Schreiben nach Neustart verlangt `ContentStore(root, read_only=False)`.
Initialisierungsfehler können einen unvollständigen Root hinterlassen: keine
automatische Löschung, Adoption oder Reparatur beim nächsten Aufruf.

SQLite hat `application_id=0x43323343`, `user_version=1` und
`metadata.identity='content-v1'`. Zusätzlich werden die vollständigen SQLdefinitionen
aller Tabellen, Indizes und Trigger geprüft, `quick_check` und FKprüfung ausgeführt.
Unbekannte, neue, fehlende oder beschädigte Schemas scheitern kontrolliert.
Schema-/Storeidentität kann nicht durch ein normales SQLupdate geändert werden.

Tatsächliche **14 Tabellen**, **ein partieller Unique-Index**, **21 Trigger**:

| Tabellen | Zweck / zentrale Constraints |
| --- | --- |
| `metadata` | Zweck `content` oder `synthetic_test`, monotone Publikationssequenz und Collectionrevision |
| `sources`, `source_grants` | Eindeutige Namespace-/externe Sourceidentität; Owner/Kurs und Grant-PK; Sourceidentität unveränderlich, ACLrevision separat |
| `artifacts`, `raw_reservations` | SHA-PK, Hex-/Größencheck; Source-/SHA-Reservierung mit committed Rawrun und FK; Blobhash allein ist kein Recht |
| `source_versions`, `source_raw_artifacts` | Source-/Manifest-/Variantunique, role/ordinal-PK; zusammengesetzte FKs auf Sourceversion und zugehörige Source-Rawreservierung |
| `parser_configs`, `parsed_documents`, `parsed_versions` | Vollständige Config, logischer Stream, eindeutiger Slot; zusammengesetzte Source-FKs, Payload-/Projektions-FKs, Publikationssequenz |
| `processing_runs` | Unique Actor/Requestkey, Inputfingerprint, ACLrevision, Zustände/Manifest/Fehlercode; partieller Slotunique für unvollständige Runs |
| `content_blocks`, `content_locators` | Versions-/Block-PK, eindeutige Reihenfolge, Texthash, FK auf Ursprung und Block; Known-/Unknown-Zeitchecks |
| `artifact_references` | Run-/Rollen-/Ordinal-PK, Blob-/Versions-FKs, unveränderliche referenzierte Publicationbelege |

Vollständige DDL steht in `schema.py`, ohne zweite Schemaquelle in diesem
Dokument. `foreign_keys=ON`, WAL und `synchronous=FULL`; Schreibtransaktionen
verwenden `BEGIN IMMEDIATE`. SQLite wartet maximal zwei Sekunden; es gibt keine
automatischen Wiederholungen. Lokale Lockkonflikte liefern sofort `Busy`.

### Rein lesendes Öffnen und WAL-Grenze

SQLite `mode=ro` allein kann WAL-/SHM-Dateien erzeugen. Deshalb serialisiert ein
zusätzlicher `.content-db.lock` kurze SQLoperationen: Writer exklusiv, Reader
shared. Writer checkpointen nach Commit/Rollback mit `wal_checkpoint(TRUNCATE)`.
Reader öffnen `mode=ro&immutable=1` erst unter diesem Lock und nur ohne nichtleeres
WAL/Journal. Ein nichtleeres WAL nach Prozessabbruch führt zu `Unavailable`;
es wird niemals ignoriert oder durch ein schreibendes Öffnen heimlich adoptiert.
Es werden weder DB, Verzeichnisse noch Lock-/Journaldateien durch Reads erzeugt.
Tests vergleichen dafür Dateibestand, Modi und sämtliche Bytes vor/nach Reads.

Dies ist eine bewusste konservative A-Einschränkung gegenüber parallelen WAL-
Lesern: kein NFS/Mehrhostbetrieb, kein fremder Schreiber neben dem Store und
kein automatisches Crash-Recovery. C23-02C muss diese Grenze unter echten
Mehrprozess-/Crashbedingungen abnehmen, bevor sie gelockert werden darf.

## Dateien, Integrität und Zustände

```text
<content_root>/content.sqlite3
<content_root>/blobs/sha256/<erste-zwei-Hexzeichen>/<sha256>
<content_root>/staging/<run_id>/<sha256>
<content_root>/locks/<run_id>.lock
<content_root>/.content-maintenance.lock
<content_root>/.content-db.lock
```

Root/Verzeichnisse 0700, Dateien 0600 und eigener UID; Symlinks, Spezialdateien,
fremde Eigentümer, Gruppen-/Weltzugriff und vorhandene Hardlink-Aliasse werden
abgewiesen. Staging/Blobverzeichnisse müssen auf demselben Dateisystem liegen.
Ein Stream wird mit erwarteter Größe + 1 begrenzt, SHA bytegenau geprüft,
Stagingdatei synchronisiert und exklusiv intern verlinkt. Danach wird ausschließlich
der eigene Staginglink entfernt. Originaldateien werden weder geändert noch
verlinkt. Existierende Blobs werden vollständig geprüft, niemals ersetzt.
Root- und Komponentenprüfungen erfolgen über sichere Deskriptoren; administrativer
Zugriff mit derselben UID/Volumehoheit ist keine isolierte Sicherheitsgrenze.

Rawartefakte und jedes JSONartefakt: höchstens 64 MiB; JSONtiefe höchstens 64,
50.000 Blöcke, 500 Bildverweise. Originalpayload wird als Bytes gespeichert,
**nicht** neu serialisiert. Nur eigene Metadaten/Projektionen benutzen C23s J(v)
(sortierte kompakte UTF-8-Keys, keine LF/NaN/Normalisierung). Die unveränderte
Manifestliste mit `role, ordinal, sha256, size_bytes, mime_type` bleibt ihre eigene
Hashdomäne. Originalpfade/Receipts werden erst durch B separat als überprüfte
Bindings/Provenienz ergänzt, nicht still in diese Manifestdomäne aufgenommen.

Publicationbausteine reservieren erst einen Run, stagen Bytes, committen das
geprüfte Manifest als `prepared`, installieren Blobs und veröffentlichen die
gesamten Parsed-/Block-/Locator-/Artefaktmetadaten mit Runabschluss in **einem**
letzten SQLcommit. Datei und SQL sind keine gemeinsame Transaktion. Kein
Jobresultat ist Veröffentlichungsautorität.

| Zustand | Verhalten in A |
| --- | --- |
| `preparing` | Slot/Run persistent, keine veröffentlichte Parsed-Version |
| `prepared` | Manifest persistent, Blobs teilweise/ganz vorhanden; weiter unsichtbar |
| `committed` | Vollständig veröffentlichte Version/Rawreservierung; gleicher Request liefert gleichen Inhalt nach erneuter Hashprüfung |
| `blocked` | Fehler/Abbruch, Staging-/Manifestbelege erhalten; gleicher Request gesperrt, anderer Request desselben Slots `Busy`; kein Resume |
| `rejected` | Nachweisbarer Widerspruch gegen bereits veröffentlichten Slot, `Conflict`; gespeicherter Fehler, kein blockierender Importslot und keine neue Version |

Es gibt keine selbsttätige Recovery, GC oder Retention. Ein echter abrupt
beendeter Prozess kann `prepared` oder einen nichtleeren WAL hinterlassen; dann
bleibt Publication gesperrt. Korruptions-/Quarantäneflags blockieren Reads;
fehlende/kaputte Bytes werden bei jedem Zugriff erkannt, ohne Reparse/Overwrite
oder automatisches Quarantäneupdate aus einem read-only-Handle. Persistierte
Incident-/Quarantänesteuerung und Byte-Restore folgen in C23-02C.

## Vorhandene APIs und Sicherheitsgrenze

Öffentlich verfügbar: `initialize`, wieder öffnen, `register_source`,
`store_raw_artifact`, `get_source`, `set_source_grants`, `list_sources`,
`list_source_versions`, `get_parsed_document`, `read_raw_artifact`,
`read_parsed_payload`, `list_content_blocks`. Raw bleibt ohne Parsing speicherbar
und über eine Sourceautorisation bytegenau lesbar. Source-Registrierung ist
Metadatenregistrierung, **keine Bestätigung einer offiziellen Sourcebindung**.

Im A-Stand waren `register_source_version` und `publish_parsed_document`
gesperrt. In B bleibt die Freigabe auf ausgestellte, erneut geprüfte Kandidaten
beschränkt; normale Dictionaries bleiben abgewiesen. Ein synthetischer Teststore
kann den B-Einstieg nicht verwenden.
Ein Dictionary mit `verified=true` oder synthetischem Herkunftsfeld schaltet
keinen öffentlichen Import frei. So kann A insbesondere #72 nicht umgehen.

Interner `_testing`-Vertrag für Tests: dauerhaft `purpose=synthetic_test` beim
Initialisieren, Namespace `synthetic:...`, Sourceorigin/-typ synthetisch,
Parsername und Adapter fest synthetisch, explizit markierte `SyntheticPayload:1`,
validierte Block-/Locator-/Rawrefs. Doppelte JSONkeys, falsche Pointer, nicht
endliche Zahlen oder ungeprüfte Origins scheitern. Ein normaler `content`-Store
kann durch dieses API weder umgeschaltet noch mit synthetischen Parsed-Inhalten
befüllt werden. Testversionen tragen stets `quality_status=synthetic_test_only`.
Dieser Helper ist keine fachliche Parser-/CS50-Abnahme.

Reads verlangen Course-Scope **und** Owner oder Sourcegrant; Operator allein
genügt nicht. Writes verlangen Operator und Ownership. ACLänderungen nutzen
Compare-and-Swap und Collectionrevision. Vor Manifest- und finalem Commit werden
Rechte/ACLrevision nochmals geprüft. Identische Blobs in verschiedenen Sources
teilen keine Rechte. Source-/Parsed-Metadatenviews enthalten keine Root-/Receipt-
pfade; vollständige Blöcke und Byteexports sind interne vertrauenswürdige
Leseverträge und brauchen vor HTTP eine eigene redigierte Projektion.

Pagination ist noch nicht freigegeben: `cursor!=None` und eine nicht vollständig
in `limit` (1–100) passende Ergebnismenge liefern `Unavailable`, niemals eine
scheinbar vollständige abgeschnittene Seite oder unautorisierte Counts.
Signierte Cursor, Antwortgrößen-/Textfenster-/Metadataredaktion und Tombstoning
folgen mit eigenem Lesevertrag; in A existieren keine HTTP-/UI-/C16adapter.

## Kleines ausdrücklich synthetisches Beispiel

Nur in einem **neuen privaten temporären Testroot** ausführen. Es zeigt den
internen Testvertrag, keinen freigegebenen Kursimport:

```python
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from src.content_store._testing import (
    SyntheticPayload, initialize_synthetic_store,
    publish_synthetic, register_synthetic_version,
)
from src.content_store.models import (
    ContentBlock, ContentLocator, ParserConfiguration, RawArtifact,
    RawManifest, SourceRegistration, sha256,
)
from src.job_control.models import Principal

with TemporaryDirectory(prefix="c23-02a-example-") as temporary:
    store = initialize_synthetic_store(Path(temporary) / "content")
    actor = Principal(subject="test-owner", role="operator", courses=("cs50_python",))
    source = store.register_source(SourceRegistration(
        identity_namespace="synthetic:example", external_identity="one",
        course_id="cs50_python", source_type="synthetic", source_origin="synthetic",
    ), actor=actor)
    raw = b"Original\r\n"
    ref = store.store_raw_artifact(source.source_id, io.BytesIO(raw),
        expected_sha256=sha256(raw), expected_size=len(raw), mime_type="text/plain", actor=actor)
    version = register_synthetic_version(store, source.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)), actor=actor)
    block = ContentBlock(block_id="example-block", order=0, type="paragraph",
        original_type="paragraph", payload_pointer="/blocks/0", text="Original\r\n",
        locators=(ContentLocator(raw_artifact_sha256=ref.sha256,
            origin_pointer="/blocks/0", time_status="unknown"),))
    body = (SyntheticPayload(blocks=(block,)).model_dump_json(indent=2) + "\n").encode()
    parser = ParserConfiguration(parser_name="synthetic", parser_version="1",
        parameters={"encoding": "utf-8"}, implementation_revision="example-1",
        payload_schema="SyntheticPayload:1", adapter_version="synthetic_fixture_v1")
    result = publish_synthetic(store, version.source_version_id, body, parser,
        actor=actor, request_key="example-1")
    assert store.read_parsed_payload(result.version.parsed_version_id, actor=actor) == body
    assert store.list_content_blocks(result.version.parsed_version_id, actor=actor).items[0].text == "Original\r\n"
```

## C23-02B: geprüfte Bundleadapter

Die vollständige Bestandszuordnung wurde vor der Implementierung im
[Adaptervertrag](content_adapter_contract.md) festgehalten. Wiederverwendet
werden `MaterialPlan`/`NormalizedDocument`/`ArtifactReceipt`,
`prepare_material_handoff()` einschließlich C10, `CS50AdapterPlan`, die
**reine Konstruktor-/Pfadprüfung** von `CS50Executor` und `validate_document()`
mit tatsächlichem SRT-Reparse. Die kleinen Executionreceipt-Invarianten aus dem
Knowledgebinder sind ohne dessen Knowledgeimporte umgesetzt; einen bestehenden
Pydantic-Typ `ExecutionReceipt` gibt es nicht. Kein Executor-Run oder Download.

### Tatsächliche Bibliothekssignaturen

```python
from src.content_store.adapters import (
    MaterialBundle, SRTBundle, ImplementationEvidence,
    verify_material_bundle, verify_srt_bundle, import_verified_bundle,
)

# Dateien ausdrücklich auswählen; Pfade innerhalb workspace können relativ sein.
material = MaterialBundle(
    workspace=workspace, raw_path=raw, normalized_path=normalized,
    receipt_path=receipt, plan_path=plan, implementation_path=implementation,
    prior_quality_path=None,  # optionaler alter Report, niemals Freigabe
)
candidate = verify_material_bundle(material)
# Für SRT stattdessen:
# SRTBundle(workspace=..., raw_path=..., transcript_path=..., receipt_path=...,
#           plan_path=..., implementation_path=..., source_id=..., source_origin="synthetic")
# candidate = verify_srt_bundle(bundle)
result = import_verified_bundle(store, candidate, actor=principal, request_key="import-1")
version_id = result.version.parsed_version_id
assert store.read_parsed_payload(version_id, actor=principal) == normalized.read_bytes()
receipt_bytes = store.read_version_artifact(version_id, "receipt", actor=principal)
```

Die bestehenden Core-Signaturen bleiben erhalten:
`register_source_version(source_id, manifest, *, variant_key, binding, actor)`
verlangt den ausgestellten Candidate als `binding`; vorher müssen Source und
Source-gebundene Rawreservierung existieren. `publish_parsed_document(
source_version_id, candidate, *, actor, request_key, job_ref=None)` prüft denselben
Kandidaten erneut; `job_ref!=None` bleibt gesperrt. Der Convenienceimport führt
alle Schritte aus. Keine implizite Storeinitialisierung, kein CLI-/HTTP-Publish.

`read_version_artifact(version_id, role, *, actor, request_key=None)` liest
hashgeprüfte, intern vertrauenswürdige Originalbytes/Belege. Ohne Requestkey wird
der erste publizierte Beleg geliefert; mit Key der Beleg dieses abgeschlossenen
Imports. Das ist kein externes DTO. Vorhandene Source-/Block-/Locator-Reads gelten
weiter; für B prüfen Parsed-Reads zusätzlich Rawmanifest und Bindingblob.

### Revisionsbeleg und Prüfgrenzen

Die vorhandenen Receipts enthalten **keine Implementierungsrevision**. Deshalb
ist eine zusätzliche explizite `ImplementationEvidence`-JSONdatei erforderlich:
`schema_version=1`, `implementation_revision` (40 Hexzeichen), `parser_name`,
`parser_version`, vollständige `parameters`, `source_id`, `binding_id`,
`raw_sha256`, `payload_sha256`, `receipt_sha256`, `evidence_reference`.
Materialparameter entsprechen exakt `ParserConfig.model_dump(mode="json")`,
Binding-ID der Material-ID. Für SRT: Parser `srt` Version `1`, Binding-ID=Source-ID,
Parameter `encoding=utf-8-sig`, `media_format=srt`, Sprache aus Binding,
`preserve_empty_cues=true`. Adapterversion ist `cs50_srt_content_v1`, Payloadschema
explizit `TranscriptDocument:legacy-unversioned`.

Dieser Beleg ist eine **lokale Attestierung**, keine Signatur oder nachträglicher
Nachweis des historischen Parsercodes. Kein automatisches Auffüllen mit HEAD.
Fehlender/widersprüchlicher Beleg sperrt. Ein Beispiel wird im synthetischen
Fixturehelper `tests/content_adapter_support.py::attest` erstellt; seine Revision
`aaaa...` ist ausdrücklich synthetisch. Reale Attestierungen erfordern später
geprüfte Herkunft, D06/D07 und einen eigenen Importauftrag.

### Snapshot, Trust Boundary und Commit

Explizite typed Bundles erlauben keinen Directoryscan. Dateien werden begrenzt
über FD-Komponenten mit `O_NOFOLLOW` als reguläre Inodes gelesen; Symlinks/FIFO,
Traversal, kollidierende Pfade und wechselnde Dateistatistik sperren. Maximal
64 MiB je Datei, 506 Dateien und 256 MiB originale Snapshotbytes. Tiefe/finite
JSONwerte und doppelte Keys werden geprüft. Keine neuen Dependencies.

Zuerst werden unveränderliche Bytes in einen privaten Snapshot kopiert und das
bestehende Gate ausgeführt. Ein Candidate ist eine **prozesslokale opaque
Capability** ohne Datenfelder/`verified`-Flag. Die Registry hält nur unveränderliche
Byte-Tupel. Dictionaries, nachgebaute Instanzen und beliebige Pfade autorisieren
keine Core-Publikation. Vor SourceVersion und Parsed-Publikation wird derselbe
Snapshot in eigenem Store-Staging aufgebaut und erneut geprüft. Erst danach
stagen die vorhandenen Blobprimitiven genau diese Bytes mit Größe/SHA und fsync.
Administrativer Python-/Dateisystemzugriff derselben UID ist keine Sandboxgrenze.

Owner/Operator/Course werden bei Reservierung und ACLrevision bei Prepared-/finalem
Commit geprüft. Read-only Handles stagen nicht. Der letzte SQLcommit veröffentlicht
Parsed-Version, alle Blöcke/Locatoren, Auditrefs und Runabschluss gemeinsam.
Rawreservierung und vollständig geprüfte SourceVersion bleiben unabhängig und
können nach späterem Parsed-Fehler erhalten bleiben. Unterbrochene Runs bleiben
wie in A blockiert; keine automatische Recovery. content-v1-DDL, `jobs.sqlite3`,
C16/C18/C20 und `_testing.py` unverändert. Runart `raw` bezeichnet byteerhaltende
Übernahme, `parsed_version_id` kennzeichnet Parsed-Publikation.

### Projektionen, Archivrollen und Idempotenz

Materiale: HTML-v2, PDF-v2 und vorhandener Code-v1-Vertrag. Alle Originalblöcke
bleiben mit identischer Block-ID, Text, Daten und vorhandener Location lesbar;
`math` wird als `formula` mit `original_type=math` projiziert. Koordinatensystem
bleibt `unknown`, da Location kein solches Feld liefert. Titel/Unsicherheit/
Metadaten bleiben im byteidentischen Payload/Handoff. Bilder ohne lokale Bytes
bleiben technische Referenzen mit C10-Warnung; deklarierte Bytes müssen existieren
und zu Receipt-/Imagehash passen.

Die Projektion enthält **exakt** C10-`aggregation_units`, `excluded_blocks` und
`alternative_views`; nur die Units sind später primärer Aggregationseingang.
Blocktext und `code_view` sind zusätzliche lesbare Sichten, keine weiteren
Indexeinträge. SourceVersion enthält nur primäre Rawdatei, keine Parserbilder.

SRT: vollständiger Plan/Graph und genau zwei passende done-Taskrecords mit
Download-/Parse-/Inputhash, Sprache, Source/Resource/Section/Lecture und
Originalpfad werden geprüft. `validate_document` vergleicht vollständige
Segmentmodelle und Text mit dem Raw-SRT. Reihenfolge, IDs, Multiline/Unicode und
Überlappungen bleiben erhalten. Projection referenziert Originalseg_id/Pointer;
die persistierte Block-ID entsteht anschließend aus Parsed-Version und seg_id.
Projektionen referenzieren den Slot, niemals zirkulär ihre eigene Versions-ID.

Archivrollen: `payload`, `projection`, `binding`, `receipt`, `plan`,
`implementation`, `quality`; bei Material zusätzlich `handoff`, optional
`prior_quality`, lokale Bilder `image:<original_image_id>`. Ein Sourcebindingblob
wird bereits mit der SourceVersion separat archiviert. Nur neu erzeugte
Quality-`inputs` verwenden logische Snapshotpfade; Originaldateien unverändert.

Gleiche Payload/Projektion im gleichen Slot: gleiche Version und `created=False`.
Ein neuer Request archiviert seine erneut geprüften Belege im neuen Run, ohne
bestehende Version/Belege umzuschreiben. Gleicher Request mit anderen Belegen
liefert `Conflict`; gleicher Slot mit anderem Payload/Projektion ebenfalls.
Neuer vollständiger Parserconfig-/Implementierungsstand erzeugt einen neuen Slot
bei gleicher Rawversion. Reale #72-Pfade bleiben `UnverifiedBinding`: keine Suche
unter `data/Harvard`, kein Link/Rewrite und keine Bestandsadoption. Portable relative
SRTbindings werden unterstützt; absolute historische Bindings bleiben blockiert.

### B-Abnahme und verbleibende Grenzen

Verfügbare Umgebung erneut geprüft: Python **3.12.12**, Pydantic **2.13.5**,
System-Pytest **7.2.1**, Ruff **0.16.0**. Keine lokal nutzbare Pytest-9- oder
PyMuPDF-Installation gefunden, keine Installation/Downloads vorgenommen. Die
verfügbare Projekt-Pythonumgebung plus System-Pytest wurde wie unten benutzt.
Warnungen überwiegend Pytest-7-AST-Rewriting unter Python 3.12.

| B-Lauf | Pass / Fail / Skip | Aussage |
| --- | --- | --- |
| Neue Adaptertests + alle drei A-ContentStoremodule | **120 / 0 / 0**, 45,25 s | 49 Adapterfälle + 71 A-Fälle, tatsächliche Dateien und SQLite; Wiederöffnung, Unverändertheit, C10/Reparse, Konflikte, ACL/Abbruch, Auditbelege, defekter Rawbezug |
| Material-/Discovery-/Lecture-/Executor-/Transcript-/C16-Regression | **197 / 8 / 2**, 81,96 s | Acht Fehler unten; zwei optionale echte HTML-/SRT-Bestände nicht vorhanden |
| Unverändertes Masterarchiv: gesamtes `test_official_transcript_import.py` | **33 / 6 / 0**, 1,03 s | Exakt die sechs bekannten TXT-Fälle aus A, gleiche None/float-Ursache |
| Unverändertes Masterarchiv: zwei HTML-Unicode-Nodes | **0 / 2 / 0**, 16 deselected, 2,25 s | Exakt dieselbe Abweichung `héllo` → `h√©llo` wie im Branch; HTMLparser unverändert |
| Nach finaler C10-Inputkey-Präzisierung: fünf betroffene Material-/Auditfälle | **5 / 0 / 0**, 44 deselected, 9,57 s | Originale C10-Inputkeys bleiben erhalten; nur Pfadwerte logisch |
| Ruff Check / Format Check / diff check | **erfolgreich** | 15 Pythondateien formatiert, 18 lokale Dokumentationsziele geprüft |

Die zusätzliche HTMLabweichung tritt in
`test_cs50_material_html_semantics.py::test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
bei beiden Wrapperparametern auf; sie ist auf der unveränderten Basis in dieser
lokalen Parserumgebung reproduziert. Die sechs TXT-Nodes sind im historischen
A-Abschnitt vollständig aufgeführt. Keine vollständig grüne bestehende Regression
behauptet und keine fachfremden TXT-/HTMLparseränderungen vorgenommen. Die
PyMuPDF-abhängigen PDFparsermodule wurden **nicht ausgeführt**; das sind keine
zusätzlichen Pytest-Skips. Pytest 9 und PDFparserregression bleiben für eine bereits
vollständig eingerichtete CI-/Projektumgebung offen.

Tatsächliche Abnahmekommandos (Präfix für alle Pytest-Läufe):

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
  -q --disable-warnings \
  tests/test_content_store_adapters.py tests/test_content_store_models.py \
  tests/test_content_store_artifacts.py tests/test_content_store_store.py \
  --basetemp=/tmp/c2302b-acceptance
```

Regression mit demselben Präfix und `--basetemp=/tmp/c2302b-regression`:
`tests/test_cs50_material_contracts.py tests/test_cs50_material_html.py
 tests/test_cs50_material_html_semantics.py tests/test_cs50_material_code.py
 tests/test_cs50_material_mapping.py tests/test_cs50_discovery.py
 tests/test_cs50_lecture_adapter.py tests/test_cs50_executor.py
 tests/test_official_transcript_import.py tests/test_job_control.py`.

Baseline: `git archive 6ef394a2f7a4debccce75f7b5e1ef3449f9457aa` der benötigten
`src`, Testdateien, `tests/conftest.py` und `pyproject.toml` in eigenen
`/tmp/c2302b-baseline`-Snapshot. Dort derselbe Pytest-Aufruf für
`tests/test_official_transcript_import.py`, anschließend
`tests/test_cs50_material_html_semantics.py -k code_preserves_exact_whitespace`.
Separate Basetemps `/tmp/c2302b-baseline-tests` und
`/tmp/c2302b-html-baseline-tests`. Keine Nutzerdateien oder Originaltranskripte.

Ruff `check` und `format --check` jeweils für `src/content_store`,
`src/model_lecture/data_resources.py`, `tests/content_adapter_support.py`,
`tests/test_content_store_adapters.py`, `tests/content_store_support.py` und die
drei A-ContentStoretestmodule; anschließend `git diff --check`.
Entwicklungsläufe: zunächst 42 Adapterfälle grün, dann 118 und 119 ContentStorefälle
grün; nach zusätzlichen Audit-/Rawkorruptionstests und finaler Integration **120**.
Diese Wiederholungen werden nicht addiert. Die neue Adapterdatei wurde außerdem
in frischem Prozess mit gesperrten Settings-/Knowledge-/LLM-/PDF-/HTMLparserimports
auf tatsächliche HTML- und SRT-Bundles geprüft.

Taskeigene Snapshot-/Test-/Cacheverzeichnisse werden nach Abnahme entfernt;
Logdateien bleiben als lokale technische Nachweise außerhalb des Repositories.
Der Worktree bleibt bis zum Merge des offenen B-PRs erhalten.

C23-02C übernimmt Recovery, konkurrierende Prozesse/Last und Backup/Restore.
TXT/VTT, HTTP, C16-Importadapter und vollständige Pagination bleiben ausstehend.
C23 bleibt offen; alle B-Testbytes sind synthetisch. Der PDF-Test prüft einen
selbst zusammengestellten PDF-v2-Normalisierungsvertrag gegen die kleine
vorhandene synthetische PDFdatei; er behauptet keinen neuen PDF-Parserlauf oder
inhaltliche Richtigkeit der Extraktion. Materialgate beurteilt technische
Konsistenz und markiert semantische Warnungen; keine Modellqualitätskennzahl.

## Historische A-Tests und tatsächlich ausgeführte Kommandos

Umgebung: Python **3.12.12**, Pydantic **2.13.5**, SQLite **3.50.4**, Ruff
**0.16.0**. Backendvenv/uvcache waren nicht verfügbar. Ausschließlich vorhandene
lokale Pakete wurden benutzt: Python aus der bestehenden `ai-job-search/.venv`,
System-Pytest **7.2.1** über `PYTHONPATH` und Ruff aus dem Pre-commit-Cache.
Kein Paket installiert und kein Cache/Lockfile verändert. Pytest 7 liegt unter
der Devgruppenanforderung `>=9.0.3`; ein Lauf mit dem vorgesehenen Pytest 9 bleibt
für CI/Umgebung mit diesem bereits verfügbaren Paket ausstehend. Die Warnungen
stammen überwiegend aus Pytest-7-AST-Rewriting unter Python 3.12.

Gemeinsames tatsächlich verwendetes Präfix für die folgenden pytest-Kommandos:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

| Lauf / Argumente hinter diesem Präfix | Ergebnis |
| --- | --- |
| `-q --disable-warnings tests/test_content_store_models.py tests/test_content_store_artifacts.py tests/test_content_store_store.py --basetemp=/tmp/c2302a-tests-20261017/core` | **71 passed**, 0 failed, 0 skipped, 29,46 s |
| `-q --disable-warnings tests/test_cs50_material_contracts.py tests/test_cs50_discovery.py tests/test_official_transcript_import.py tests/test_job_control.py --basetemp=/tmp/c2302a-tests-20261017/regression` | **103 passed, 6 failed**, 0 skipped, 18,97 s |
| Die sechs unten genannten Nodes gegen unveränderten Gitarchiv-Snapshot `053209ad` unter `/tmp/c2302a-baseline-20261017`, `-q --disable-warnings -c /tmp/c2302a-baseline-20261017/pyproject.toml ... --basetemp=/tmp/c2302a-tests-20261017/baseline` | **6 failed**, gleiche Ursachen, 0 passed/skipped, 0,73 s |

Die ersten Entwicklungsprüfungen ergaben 58 passed/2 failed (fehlender Import,
anschließend korrigiert), danach 70 passed; die abschließende Suite enthält die
zusätzliche Prüfung gegen Teststore-Promotion. Diese Läufe werden nicht addiert.
Dabei wurden dieselben drei neuen Testmodule einmal mit `-q` und einmal mit
`-q --disable-warnings`, noch ohne explizites `--basetemp`, ausgeführt.

| Akzeptanz | Tatsächlicher Nachweis in den drei neuen Testmodulen |
| --- | --- |
| T01 | Initialisierung/FKs/WAL/FULL, kein schreibendes Read-Open, fremde/neue/kaputte Schemas abgewiesen |
| T02 | Rawbyte-/Hashroundtrip nach neuem Prozess, Dedup, falsche Hashes/Größen, kaputte Blobs, Symlinks/FIFO/Hardlinks, Stream-/fsync-Fehler |
| T03 | Stabile Source-/CS50-IDs, Konflikte, synthetischer SourceVersion-/Manifestbezug und Source-bound Rawrefs |
| T04 | Fünf Blockarten, vollständige Reihenfolge/Locator, Unicode/CRLF/Whitespace unverändert, bekannte/null-Zeiten, unveränderter Payloadhash nach Wiederöffnung |
| T05 | Gleicher/neuer Requestkey, kein zweiter Slotgewinner, andere Bytes → Conflict, neuer Parser/Rawversion getrennt, alte Inhalte erhalten |
| T06 | Owner/Course/Grant, fremder Operator ohne Rechte, identische Bytes ohne Rechteübertrag, ACLänderung vor Commit |
| T07 | Echter Prozessabbruch vor Commit, injizierter SQLite-/Diskfehler, Rollback/FKs, Run-/Manifestbelege, keine unvollständigen Reads oder automatische Adoption, Quarantänestatus |

Die sechs bestehenden Fehler sind exakt
`tests/test_official_transcript_import.py::test_txt_unknown_timestamps_paragraphs_and_unicode`,
`::test_explicit_encoding[cp1252]`, `::test_explicit_encoding[utf-16]`,
`::test_exclusive_save_and_no_overwrite`,
`::test_knowledge_chunking_contract_without_llm_imports`,
`::test_import_does_not_load_whisper_or_application_settings`.
Der TXTimport erzeugt `start/end=None`, das unveränderte Transcriptmodell
verlangt float. Der Basissnapshot reproduziert dieselben sechs Fehler ohne
ContentStorecode. **Keine vollständig grüne bestehende Regression behauptet**;
TXT bleibt C23-05, nicht Bestandteil dieses Fixes. Materialmodelle: 4 passed,
Discovery: 30 passed, C16: 36 passed, übriger Transcriptimport: 33 passed.

Der Baselinevergleich verwendete eine reine Kopie der versionierten Dateien,
keinen weiteren Worktree und keine lokalen Originaldaten:

```sh
git archive 053209ad89fac828c7f47677056c44a624ac1af7 \
  src tests/test_official_transcript_import.py tests/conftest.py pyproject.toml \
  | tar -x -C /tmp/c2302a-baseline-20261017
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
  -q --disable-warnings -c /tmp/c2302a-baseline-20261017/pyproject.toml \
  /tmp/c2302a-baseline-20261017/tests/test_official_transcript_import.py::test_txt_unknown_timestamps_paragraphs_and_unicode \
  /tmp/c2302a-baseline-20261017/tests/test_official_transcript_import.py::test_explicit_encoding \
  /tmp/c2302a-baseline-20261017/tests/test_official_transcript_import.py::test_exclusive_save_and_no_overwrite \
  /tmp/c2302a-baseline-20261017/tests/test_official_transcript_import.py::test_knowledge_chunking_contract_without_llm_imports \
  /tmp/c2302a-baseline-20261017/tests/test_official_transcript_import.py::test_import_does_not_load_whisper_or_application_settings \
  --basetemp=/tmp/c2302a-tests-20261017/baseline
```

Zusätzlich tatsächlich ausgeführt:

```sh
/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff check \
  src/content_store tests/content_store_support.py tests/test_content_store_models.py \
  tests/test_content_store_artifacts.py tests/test_content_store_store.py
/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff format --check \
  src/content_store tests/content_store_support.py tests/test_content_store_models.py \
  tests/test_content_store_artifacts.py tests/test_content_store_store.py
git diff --check
```

Abschlussstatus: **alle drei Checks erfolgreich**, zehn Pythondateien formatiert;
das obige Beispiel wurde unverändert erfolgreich ausgeführt. **31 lokale
Dokumentationsverweise** und Python-Syntax geprüft. Vollständige lokale Logs werden als Arbeitsnachweis
außerhalb des Repositories aufbewahrt; keine produktiven Quelldateien/Secrets
wurden für Tests eingelesen. Keine Gesamtsuite und keine Live-API-/Qdranttests.

## Konkrete Übergabe und verbleibende Grenzen

**C23-02B (in diesem PR implementiert):** Material-/SRT-Bundleadapter mit
vollständiger Discovery-/Receipt-/Originalpfad-/Hash-/Parserrevisionsbindung und
erneutem Quality Gate über eingefrorenem Staging. Bestehende Payloads/IDs unverändert erhalten, C10-Units/
Exclusions/Codeviews genau einmal übernehmen. Die SourceVersion-/Publish-Einstiege akzeptieren nur B-Kandidaten;
der synthetische Vertrag bleibt unverändert isoliert.
#72 bleibt bis separater geprüfter Bestandsfreigabe blockiert.

**C23-02C:** vollständige Run-/WAL-Recovery, konkurrierende Prozesse und
Abbruchzeitpunkte unter Last, Manifest-/DB-/Blob-Reconciliation, persistierte
Quarantäne-/Retentions-/Löschsteuerung, Backup/Restore und Integrationsabnahme.
Livebackup, automatische WAL-Reparatur, Slotübernahme nach Zeitablauf und
unbelegte Datei-Adoption sind derzeit gesperrt. C16/C18/C20 werden nicht erweitert;
Jobresultate sind keine Contentautorität. Der neue Contentroot wird noch nicht
vom C22-Verbundbackup erfasst. Kein produktiver Go-live durch diesen PR.
