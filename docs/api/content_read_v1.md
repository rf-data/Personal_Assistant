# C23-04: Authorized Content Read API v1

Stand 18.10.2026, Backendbasis `5986da9` (A/B/C, #76–#78 gemergt).
C23-03/#79 war bei Prüfung offen. Dieser PR übernimmt keine ungemergten
Retry-/Inventarfunktionen. Er liest ausschließlich bereits autoritativ gespeicherte
content-v1-Daten; historische Pfadbindung #72 bleibt D06-gesperrt. C23 bleibt offen.

Maßgeblich: [ADR](../architecture/parsed_content_persistence_adr.md),
[Datenmodell](../architecture/parsed_content_data_model.md),
[Betriebsvertrag](../operations/content_store_recovery.md),
[Plan](../planning/c23_implementation_plan.md), [Governance](../planning/governance.md).

## Aktivierung und Kompatibilität

Der bestehende C16-Server `src.job_control.http` authentifiziert zuerst über die
unveränderten Beareridentitäten/Principals. Neuer Bereich `/v1/content`, eigene
Capability `content_read_v1`, JSON-Envelopes `schema_version=1`. Kein zweiter
Server, Authmechanismus, Speicher, Import oder HTTP-Schreibauftrag.

Opt-in mit **separatem** `ContentReadSettings`-Schema 1; C16-Settings v1 und
Job-/Workflow-DTOs bleiben unverändert. Die Capability steht entsprechend der
vorhandenen Workflowkonvention an einer eigenen Route, nicht als zusätzliches
Pflichtfeld im bisherigen `/v1/capabilities`-DTO:

```json
{"schema_version":1,"root":"/private/content","cursor_key_file":"/private/secrets/content-cursor.key"}
```

Konfiguration und Schlüssel: private reguläre, einfach verlinkte Dateien,
keine Symlink-Komponenten; Config höchstens 8 KiB. Schlüssel **32–64 rohe zufällige
Bytes**, außerhalb des Content-/Jobroots, keine Bearertokens/Passwörter. Kein
Defaultkey und keine automatische Erzeugung. Contentroot absolut, außerhalb des
Repositories, bereits initialisiert und getrennt vom Jobroot. Kopieren/Öffnen
einer beliebigen SQLite-Datei legitimiert keinen Root. Nur `ContentStore(root)`
read-only, keine Initialisierung, Migration, WAL-Recovery oder Quarantäneänderung.

```sh
python -m scripts.job_control api --config /private/job-config.json \
  --content-config /private/content-read.json --port 8016
```

`--content-config` ist nur für `api` zulässig. Unkonfigurierter/unlesbarer/
gesperrter Root oder unbrauchbarer Schlüssel: Capability `enabled=false`, leere
Capabilityliste; Contentzugriffe 503. Alte APIs bleiben verfügbar. Nach Keywechsel
Server bewusst neu starten; alte Cursor scheitern an der Signatur. Kein automatischer
Keywechsel, Scheduler oder Produktivstart durch dieses Paket.

## Routen

Alle Routen benötigen gültige Authentifizierung. Objekt-IDs sind sichere ASCII-
Identitäten; Doppelpunkte können beispielsweise als `%3A` übergeben werden.
Segmente werden **genau einmal** dekodiert. Slashes/Backslashes, Prozentreste,
Doppeldecodierung, Traversal, Steuerzeichen und fehlerhaftes UTF-8 werden abgewiesen.
Keine freien Hostpfade, URLs als Downloadparameter oder Remoteproxys.

| GET-Route | Parameter / Antwort |
| --- | --- |
| `/v1/content/capabilities` | `ContentCapabilities`, keine Parameter |
| `/v1/content/sources` | `course_id`, `source_type`, `limit`, `cursor`; `ContentPage<SourceDTO>` |
| `/v1/content/sources/{source_id}` | `SourceDTO`: Course, Typ, Herkunft, sichere Original-URL, Versionsroute |
| `/v1/content/sources/{source_id}/versions` | `limit`, `cursor`; `ContentPage<SourceVersionDTO>` mit sourcegebundenen Rawreferenzen |
| `/v1/content/sources/{source_id}/versions/{source_version_id}/parsed` | `limit`, `cursor`; `ContentPage<ParsedRef>` mit konkreten Parsed-IDs/GET-Routen |
| `/v1/content/parsed/{parsed_version_id}` | `ParsedDTO`: Source-/SourceVersion-/Parser-/Schema-/Hashbezug, Quality, Warncodes, Blockanzahl |
| `/v1/content/parsed/{parsed_version_id}/blocks` | `limit`, `cursor`; `ContentPage<BlockDTO>` |
| `/v1/content/parsed/{parsed_version_id}/blocks/{block_id}/text` | `start` ab 0, `limit` 1–16384 Codepoints; `TextWindow` |
| `/v1/content/parsed/{parsed_version_id}/blocks/{block_id}/structure` | Redigiertes `StructureDTO` als JSONattachment |
| `/v1/content/sources/{source_id}/versions/{source_version_id}/raw/{role}/{ordinal}` | Exakte geprüfte Originalbytes als Attachment |

GET-Bodies werden abgewiesen; POST im Contentbereich liefert 405, `Allow: GET`.
Kein `force`, Import oder Publish. Unbekannte/duplizierte Queryparameter sind Fehler.
Die oben zusätzlich eingeführte Parsed-Referenzroute ist eine begründete
Konkretisierung des C23-01-Entwurfs: statt unbegrenzt eingebetteter Parsedhistorie
enthält die SourceVersion eine `parsed_versions_route`. Die Historie ist selbst
keysetpaginiert. Dies ist das erste implementierte HTTP-DTO v1, keine Umdeutung
eines bereits veröffentlichten DTOs. Der interne alte Store-Tupel-/BlockPagevertrag
bleibt erhalten; `ContentReader.page` ist die neue versionierte Leseprojektion auf
derselben DB und denselben Autorisierungs-/Lockprimitiven.

## Autorisierung und Zustände

Jede Objektanfrage prüft Course-Scope **und** Sourceownership oder expliziten
`SourceGrant(read)`. Viewer mit Grant darf lesen. Operator ohne Sourceberechtigung
darf es nicht; es gibt keinen globalen Administrator. Listen filtern in SQL vor
Limit/Keyset. Keine ungefilterten Gesamtzahlen. Unbekannte und fremde IDs liefern
denselben 404-Body. Gleicher Blobhash bzw. eigene Rawreservation desselben Hashes
überträgt keine Rechte an eine andere SourceVersion.

Source-Tombstone sperrt sämtliche Kindobjekte. Quarantänisierte SourceVersionen,
Parsed-Versionen und zugehörige quarantänisierte Artefakte sind nicht sichtbar.
Parsed-Tombstone sperrt diese Parsed-Version. Die separate, intakte, veröffentlichte
Raw-SourceVersion bleibt ein eigenständiger Vertrag; ein Parsed-Tombstone ersetzt
keinen Source-Tombstone. Eine registrierte Source kann weiterhin als eigene Metadaten-
hülle erscheinen, auch wenn gerade keine nutzbare Version existiert. Defekte Bytes
bei noch nicht gesetzter Quarantäne ergeben für berechtigte Leser 503; Reads
reparieren oder quarantänisieren nichts. Integritätswartung bleibt explizit.

Raw-only-Reservations sind keine Downloads. Zugänglich sind nur atomar registrierte
`verified` SourceVersionen mit Publikationssequenz und ihrem unveränderten Manifest,
unabhängig davon, ob schon eine Parsed-Version publiziert wurde. Rolle und Ordinal
werden innerhalb genau dieser SourceVersion geprüft, niemals nur über den Hash.

## Pagination und Konsistenz

`limit` 1–100, Default 50; stabile Sortierung Source-/Versions-ID, Blocks nach
`(order, block_id)`. Kein Offset. Alle Seiten in bestehender Maintenance-/DB-
Sharedlock-Transaktion; aktuelle Rechte werden bei jeder Anfrage erneut geprüft.
Antwort höchstens **256 KiB**. Falls die Bytegrenze vor dem Itemlimit erreicht
wird, enthält die Seite weniger **vollständige** Items plus gültigen Cursor zur
letzten ausgegebenen Position. Keine still gekürzten Items oder unautorisierte Counts.

Cursor v1: kanonisches JSON plus HMAC-SHA256, kanonisches Base64url ohne Padding,
höchstens 1600 Zeichen. Bindet Actor (Subject/Role/Courses, **kein Tokenhash**),
Route/Objekt-IDs, normalisierte Filter/Limit, Snapshot und letzte Position;
bei kindbezogenen Listen zusätzlich Source-ACLrevision. Cursor gewährt keine Rechte.

Gegenüber der internen Skizze aus C23-01 werden `max_publication_seq` und
`collection_revision` **nicht als ablesbare globale Zähler** in den Cursor
geschrieben. Ein separat domainmarkierter HMAC bindet beide Revisionen im Feld
`snapshot`. Bei Folgeseiten wird dieser mit den aktuellen Revisionen verglichen;
nur bei Gleichheit ist die aktuelle Publikationsobergrenze auch die ursprüngliche.
So entstehen weder ein serverseitiger Cursorspeicher noch fremde Bestandszahlen.
Kein Secret im Cursor, keine selbst entworfene Verschlüsselung.

Andere Actor-/Filterbindung, ungültige Signatur/Schema/Position: 400
`invalid_cursor`. Veränderte Collection-/Publikations-/Source-ACLrevision:
409 `snapshot_changed`, erste Seite neu laden. Ein gültiger früherer Viewer-
Cursor nach Grantentzug liefert 409 ohne Items; ein neuer Objektzugriff 404.
Konservativ invalidiert jede Collectionänderung auch Cursor auf andere Sources.
Das ist keine Aussage über Anzahl oder Inhalt solcher Änderungen.

Die vorhandenen `_sequence`, `set_source_grants` und Quarantänecommits erhöhen
Collectionrevision transaktional. Es gibt in diesem Paket keine neue Schreib-
oder Tombstone-API. Künftige Statuswriter müssen im selben Commit die Revision
erhöhen; manuelle SQLmanipulation außerhalb der Storeverträge ist kein freigegebener
Schreibweg. Normale offene Imports ändern ohne Publikation nicht den sichtbaren
Snapshot. Nichtleeres WAL/Journal/Fence sperrt wie zuvor das Read-Open.

## Texte, Locatoren und strukturierte Inhalte

`BlockDTO` enthält unveränderte stabile IDs, Reihenfolge, Typ/Originaltyp,
Aggregationrolle, Quality und relevante Warncodes. Sämtliche Locatorwerte behalten
ihre vorhandenen Einheiten: Page/DOM/Zeilen/BBox/Koordinatensystem/Chapter sowie
bekannte oder ausdrücklich unbekannte Zeitintervalle. Keine Umwandlung von `null`
in 0. Rawreferenzen bestehen aus Source-/Version-/Role-/Ordinal-/SHAbezug und
autorisierter Downloadroute. JSONpointer bleiben interne Payloadpointer, keine
Dateisystempfade. Private Pfadwerte in beschreibenden Locatorfeldern werden redigiert.

Kleine Blocktexte (bis 2048 Codepoints) stehen vollständig inline. Größere Texte:
`text=null`, vollständige Länge, exakter UTF-8-`text_sha256`, feste `text_route`.
Textfenster verwenden Python/Unicode-Codepoints, keine UTF-8-Bytes oder UTF-16-
Codeunits. `start/end` sind halb offen; `end` und `text_length` machen das Fenster
explizit. `start == text_length` liefert ein leeres Fenster. Kein Textnormalisieren.

Große Locatorlisten (mehr als 32 KiB) werden vollständig über `structure_route`
bereitgestellt: `locators=null`, `locators_in_structure=true` in der Blockview.
Kein stilles Abschneiden. Strukturattachment maximal 64 MiB; ein einzelnes nicht
darstellbares Item wird als unavailable abgewiesen. Aktuelle B-Rawmanifeste
enthalten eine primäre Rawdatei; beliebig große künftige Mehrartefaktmanifeste
benötigen gegebenenfalls einen zusätzlichen paginierten Referenzvertrag.

`StructureDTO` ist eine ausdrücklich allowlistbasierte Projektion. Unterstützt:
Tabellenzeilen/Zellen; Code-Sprache, rekonstruierten `code_view`, Zeilennummern,
Zeilengeometrie und PDF-v2-Klassifikation; vorhandenes LaTeX; stabile Bild-ID;
Heading-/Listen-/TOCmerkmale; sichere HTTP(S)-Linkziele. Freie Metadatencontainer,
lokale Bild-/Sourcepfade, Source-Markup und private Receipts werden nicht ausgegeben.
Texttragende Tabellen-/Code-/Formelwerte sind Originalinhalt, kein Metadatenkanal.
`redacted` kennzeichnet entfernte Struktur-/Locatorfelder. Nicht unterstützte
Felder bleiben unverändert in der internen Payload; kein behaupteter Informations-
verlust im Store und kein neuer Export des kompletten privaten Payloads.

`projection_sha256` im Struktur-DTO bindet kanonisches `{data,locators}` der
**redigierten** Projektion. `ParsedDTO.projection_sha256` bleibt dagegen der
ursprüngliche persistierte Projektionshash. `text_sha256` gehört zum vollständigen
Originalblock, nicht nur zum Fenster. Warnungen enthalten code/severity/category
und Vorkommenszahl, keine privaten Message-/Inputpfade. Original-URLs mit Credentials,
Query/Fragment oder ungeeignetem Schema werden `null`; nie automatisch aufrufen.

C10-Aggregationsrollen werden direkt übernommen. TOC-/Linkreferenzen und
rekonstruierte Codeansichten sind keine zusätzlichen primären Texte. Für C24/C25
primär nur freigegebene `primary`-Units aggregieren; diese API startet keinen Index
und keine Knowledge-Extraktion. JSON-/Tabellen-/Code-/Formeltexte im UI als Text
behandeln, nicht als ausführbaren Inhalt oder `innerHTML`.

## Download und Ressourcen

Source-/Course-/Grantprüfung und SourceVersion-/Manifest-/Katalogprüfung erfolgen
vor dem Öffnen des Artefakts. Bestehender FD-basierter Blobstore prüft alle Root-
Komponenten ohne Symlinks, Privateigentum, reguläre Inodes und Größe. Bounded Copy
von höchstens 64 MiB in eine **anonyme memfd-Antwortdatei**; SHA/Größe müssen exakt
dem Rawmanifest entsprechen. Danach Linuxseals gegen Schreiben, Vergrößern,
Verkleinern und Änderung der Seals. Der versiegelte Handle wird selbst nochmals
gehasht, zurückgespult und genau dieser Handle übertragen. Originalmutationen
nach der Prüfung verändern die Antwort nicht. Kein persistenter zweiter Store.

`read_files.py` verwendet Linux-UAPI und ausschließlich feste Aufrufe. Der lokale
CPythonbuild exportiert `os.memfd_create`/fcntl-Sealkonstanten nicht; wie der
bestehende C16-Guardian nutzt die kleine Kompatibilitätsbrücke `ctypes` zur bereits
geladenen libc, mit expliziter `memfd_create`-Signatur, konstantem Namen/Flags und
Fehlerprüfung. Kein Eingabeausdruck/Code, keine neue Dependency oder Installation.
Linux-ABI-Konstanten wurden gegen die lokalen UAPIheader geprüft; echte Kernel-
Seals werden in den Tests überprüft. Unsupported Linux/libc/Container-Seals führen
kontrolliert zu unavailable, nicht zu einem ungeschützten Dateifallback.

Maintenance-/DB-Sharedlocks bleiben bis zum Schließen der Antwort gehalten.
Parallele ACL-/Quarantänewriter erhalten nonblocking Busy; nach Abschluss gilt der
aktuelle Zustand für die nächste Anfrage. Chunks 64 KiB, Socketwartezeit höchstens
3 s, gesamtes Übertragungsbudget 15 s ab Headerausgabe; Abbruch schließt Handle
und Locks. Ein Abbruch nach bereits gesendeten Headern beendet die Verbindung,
er kann keinen nachträglichen JSONfehlerbody liefern. Hash-/Sealingfehler vor
Headerausgabe liefern 503. Kein HTTP-Range-/Remote-/Retrymechanismus.

Antwortheader: `Content-Disposition: attachment` mit festem hashbasiertem Namen,
`X-Content-Type-Options: nosniff`, `Cache-Control: no-store`, exakte Content-Length.
MIMEallowlist PDF, Plaintext, SRT; HTML und unbekannte Typen octet-stream.
Strukturen sind JSONattachments, niemals aktive HTMLantworten. Anonyme Antwortdatei
und alle Deskriptoren werden nach Erfolg/Abbruch geschlossen; keine Rootmigration.

## Fehler und Beispiele

Fehlerbody folgt dem bestehenden Gateway:

```json
{"schema_version":1,"error":{"code":"snapshot_changed","message":"snapshot changed"}}
```

| Status | Vertrag |
| --- | --- |
| 400 | `invalid_cursor`, `invalid_parameter`, `invalid_route` oder sonstiger ungültiger Contentparameter |
| 401 | vorhandenes `unauthenticated` |
| 404 | `not_found` für fremdes/unbekanntes/unsichtbares Objekt |
| 405 | `method_not_allowed`, `Allow: GET` |
| 409 | `snapshot_changed` |
| 422 | `invalid_request`, z. B. GET-Body; bestehende äußere Gatewaylimits behalten ihren Vertrag |
| 503 | `unavailable` bei Busy, Integrität, fehlendem Store oder fehlenden Betriebsvoraussetzungen |

Keine Hostpfade, SQLmeldungen, Stacktraces, Tokens oder Rootdetails im Fehlerbody.
Ein [synthetischer Beispielsatz](examples/content_read_v1.json) enthält tatsächlich
über das Gateway aus einem B-geprüften Material erzeugte Antworten; die IDs sind
Beispiele, keine registrierten Produktionsquellen oder aufrufbaren Zusagen.

## C16, C25 und offene Gates

Der begrenzte **C16-Publikationsadapter ist Folgearbeit**. Bestehendes
`CatalogEntry(kind="material_bundle")` erlaubt plan/raw/normalized/receipt,
aber keinen vollständigen versionierten Revisions-/Implementierungsbeleg für B.
Zusätzlich wären explizites Processregistry-/Worker-/Settings-/Resultreceipt-
Versionieren und Wiederholungsabnahme nötig. Raw-/Binding-Retry nach Reject ist
auf der aktuellen gemergten Basis weiterhin C23-03/#79. Diese Voraussetzungen
werden nicht über freie Dictionaries oder beliebige Pfade nachgebaut.

Konkretes Folgepaket: (1) genehmigten Materialkatalogvertrag mit Originalplan,
Receipt, Payload, Raw und hashgebundenem ImplementationEvidence versionieren;
(2) vorhandene C16 Owner-/Course-/Queue-/Executor-/Bestätigungskontrolle nutzen;
(3) exakt `verify_material_bundle`/`import_verified_bundle` aufrufen;
(4) `content-publication.v1.json` mit stabilen Source-/Version-/Hashrefs erzeugen;
(5) Neustart/Reject/Retry und parallele Wiederholung gegen gemergtes C23-03 abnehmen.
Kein Transcriptadapter ohne eigenen Katalogvertrag, keine C18-v1-Stageänderung.

C25 kann die zehn GET-Routen und DTOs konsumieren, Cursor ausschließlich opak
weiterreichen und 409 durch Neuabruf behandeln. Separate UI-DTO-/Client-/Browser-
abnahme, sichere Textdarstellung, Auth/TLS/Ingress und Download UX bleiben offen.
Keine Browserprüfung in diesem PR. D06/D07 und C26 Host-/Container-/Speicher-/
Key-/Verbundbackup-/Last-/Go-live-Gates bleiben offen. Keine Qdrant-/Embedding-/
FTS-/Knowledgearbeit, historische Übernahme oder produktive Datenänderung.

## Tatsächliche Offlineabnahme

Umgebung: Python **3.12.12**, Pydantic **2.13.5**, SQLite **3.50.4**,
BeautifulSoup **4.15.0**, vorhandenes System-Pytest **7.2.1**, Ruff **0.16.0**.
Projektvenv/Pytest 9 und PyMuPDF nicht nutzbar; nichts installiert/heruntergeladen.
Vorhandener Interpreter aus `ai-job-search/.venv`, System-Pytest via `PYTHONPATH`,
Plugin-Autoload deaktiviert. AST-Warnungen aus Pytest 7/Python 3.12 sind keine Skips.

| Abschließender Lauf | Pass / Fail / Skip / Collectionfehler | Aussage |
| --- | --- | --- |
| Neue HTTP-/DTO-/Cursorfälle plus C16 | **93 / 0 / 0 / 0**, 78,86 s | 43 echte Loopback-HTTPfälle, 14 DTO/Projektionsfälle, alle 36 vorhandenen C16-Fälle |
| Alle gemergten A/B/C-ContentStoretests | **173 / 0 / 0 / 0**, 303,95 s | Models/Artefakte/Store/Adapter/Recovery/Concurrency/Integrität/Backup/Limits |
| Material-/Discovery-/Lecture-/Executor-/Transcriptregression | **161 / 8 / 2 / 0**, 98,25 s | Acht unabhängig bestätigte TXT-/HTML-Altfälle, zwei optionale Originalworkspaces fehlen |
| Unveränderter Master: Transcriptimport und HTMLsemantik | **48 / 8 / 1 / 0**, 4,58 s | Exakt dieselben acht fehlgeschlagenen Nodes |
| Bestehendes C20-HTTPmodul, Sammlung versucht | **0 / 0 / 0 / 1** | `pymupdf` fehlt bereits beim Import; keine ausgeführten C20-Modulfälle behauptet |
| Unveränderter Master: C20-Sammlungsprüfung | **0 / 0 / 0 / 1**, 3,99 s | Identischer importbedingter Blocker; nicht als Skip oder bestandener Parserlauf ausgegeben |
| Ruff Check / Format Check / diff check | **erfolgreich** | Neun geänderte/neue Pythondateien; Beispiel-DTOs und lokale Dokumentationsziele geprüft |

Neuer E2E-Nachweis: echtes B-Gate → private content-v1-Publikation → neues
read-only Storehandle → tatsächlicher `HTTPServer` → authentifizierte JSON-/Text-/
Struktur-/Rawantwort. Ganze File-/Mode-/Hashinventare von Contentroot und Bundle
vor/nach Readback identisch. HTML-/PDF-v2-Vertrag/Code/SRT, C10-Rollen, Zeilen/BBox,
Nullzeiten als DTO, große Unicodecodepoints, sichere Quellenrefs und keine
Pfad-/Freimetadatenlecks geprüft. PDF-Fixture ist ein vorhandener synthetischer
Raw-/Normalisierungsvertrag; **kein neuer PDFparserlauf**.

Echte Source-/Versions-/Block-Keysetseiten mit stabiler Sortierung, veränderte
Actor-/Filter-/Sourcebestandsbindung, manipulierte Cursor, Grantentzug zwischen
Requests und keine fremden Counts. Unbekannte/fremde IDs gleicher 404-Body,
Viewergrant, Operator ohne Ownership, fehlender Course, Quarantäne/Tombstones und
tatsächlich geteilter Blob ohne Rechteübertrag. Rawmanifestrolle/-ordinal und
Cross-Sourceversionkonflikt; falsche/fehlende Bytes und Encodings; echte Kernel-
Seals mit abgewiesenem Schreibversuch und unveränderter Antwort nach nachträglicher
Blobmutation. Paralleler ACLwriter während tatsächlichem HTTPdownload Busy;
nach geschlossenem Handle funktioniert der nächste autorisierte ACLcommit.

Zusätzlich tatsächlich geprüft: bestehende **C20-HTMLinspektion über den echten
HTTPserver**, Original-`WorkflowInspection` v1 und neun Stages für die zwei
synthetischen HTML-/Code-Materialien; keine Jobs erstellt. Das ersetzt nicht die
fehlende vollständige C20-/PDF-Workerabnahme. Der vorhandene C16-MemorySocket-
Handler- und Transportsnapshottest bleibt grün; alte DTOs wurden nicht erweitert.
Keine reale Browser-, PyMuPDF-, Server-/Container- oder Produktionsprüfung behauptet.

Tatsächliches gemeinsames Pytestpräfix (pro Lauf Logumleitung nach `/tmp`):

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

HTTP/DTO/C16 mit diesem Präfix:

```sh
-q --disable-warnings tests/test_content_http.py \
 tests/test_content_read_contracts.py tests/test_job_control.py \
 --basetemp=/tmp/c2304-release
```

Die Sandbox verweigerte Socket-Erzeugung. Dieser Lauf wurde mit erweiterten
Ausführungsrechten für den echten lokalen Testserver ausgeführt. Die Testfixture
erlaubt ausschließlich ihren eigenen `127.0.0.1`-Port und sperrt externe Connects/
Namensauflösung; keine produktiven Dienste oder APIs kontaktiert.

Storetests, gleiches Präfix:

```sh
-q --disable-warnings \
 tests/test_content_store_models.py tests/test_content_store_artifacts.py \
 tests/test_content_store_store.py tests/test_content_store_adapters.py \
 tests/test_content_store_recovery.py tests/test_content_store_concurrency.py \
 tests/test_content_store_integrity.py tests/test_content_store_backup.py \
 tests/test_content_store_limits.py --basetemp=/tmp/c2304-store-acceptance
```

Materialregression, gleiches Präfix:

```sh
-q --disable-warnings \
 tests/test_cs50_material_contracts.py tests/test_cs50_material_html.py \
 tests/test_cs50_material_html_semantics.py tests/test_cs50_material_code.py \
 tests/test_cs50_material_mapping.py tests/test_cs50_discovery.py \
 tests/test_cs50_lecture_adapter.py tests/test_cs50_executor.py \
 tests/test_official_transcript_import.py --basetemp=/tmp/c2304-material-regression
```

Baseline: `git archive 5986da958d767f66e24850df25085ccbebe9ee3e src tests scripts
 docs/course_sources docs/workflows deployment pyproject.toml uv.lock` in eigenes
`/tmp/c2304-baseline` entpackt. **Dort** obiges Präfix mit
`-q --disable-warnings tests/test_official_transcript_import.py
 tests/test_cs50_material_html_semantics.py --basetemp=/tmp/c2304-baseline-tests`;
C20 dort separat `--collect-only -q --disable-warnings tests/test_workflow_http.py`.
Der erste gemeinsame HTTP/C16/C20-Aufruf sammelte wegen C20 denselben einen
Collectionfehler und führte keine Tests aus; anschließend getrennt geprüft.

Die sechs bekannten TXT-Nodes in `test_official_transcript_import.py`:
`test_txt_unknown_timestamps_paragraphs_and_unicode`, beide
`test_explicit_encoding[cp1252|utf-16]`, `test_exclusive_save_and_no_overwrite`,
`test_knowledge_chunking_contract_without_llm_imports`,
`test_import_does_not_load_whisper_or_application_settings` (None gegenüber float).
Dazu beide Wrapper von `test_cs50_material_html_semantics.py::test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
(`héllo` → `h√©llo`). Fehlgeschlagene Node-Listen zwischen Branch und Baseline
maschinell identisch verglichen. Keine dieser Implementierungen verändert.

Ruff `check` und `format --check` für `src/content_store/read_files.py`,
`read_models.py`, `read_views.py`, `reader.py`, `http.py` sowie
`src/job_control/http.py`, `scripts/job_control.py`, `tests/test_content_http.py`,
`tests/test_content_read_contracts.py`; anschließend `git diff --check`.
Keine vollständige Repositorytestsuite. Zwischenläufe (Sandbox-Socketfehler,
falsche Testannahmen zu Codeblöcken/Stageanzahl, fehlende CPython-Sealwrapper)
wurden korrigiert und nicht als Baseline oder erfolgreiche Abnahme gezählt.
Ein älterer Entwicklungsprozess wurde vor der ineffizienten Textfixtureprüfung
gezielt per SIGINT beendet; die endgültige Fixture prüft einen großen einzelnen
Unicodeblock. Der abschließende 93er-Lauf enthält alle Korrekturen.

Taskeigene temporäre Test-/Archiv-/Cacheverzeichnisse werden nach Abnahme entfernt.
Technische Logs bleiben außerhalb des Repositories; der Featureworktree bleibt
bis zum Merge des offenen PR bestehen. Primärcheckouts, andere Worktrees/Branches,
Originaldaten, Venvs und Umgebungsdateien bleiben erhalten.
