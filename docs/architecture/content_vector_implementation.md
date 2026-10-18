# C24-04-A: ContentRecord-Vektoradapter

Entwurfsentscheidung vor Implementierung, 18.10.2026. Basis Master
`30bc6d35a75456c9c71b4c3b4fe127e6b4ccedca`; #83, #84 und #85 gemergt.
Maßgeblich: [ADR](retrieval_indexing_adr.md), [Recordvertrag](index_record_contract.md),
[FTS5](content_fts_implementation.md), [Plan](../planning/c24_implementation_plan.md).

## Verbindlicher begrenzter Aufbau

- Ein C24-02-Projektor. ContentIndex erhält kleine Backendhooks für Partitiondatei,
  Backendfingerprint, Queryrepräsentation, Scores und DTOkomponente. Seine
  Generations-, Snapshot-, ACL-, Cursor- und Hydrierungslogik bleibt gemeinsam.
  Die lexikalischen Defaults und ihre Generationsidentitäten bleiben gleich.
- ContentVectorIndex verwendet diese Grenze mit eigenem versioniertem Root,
  `.vectors.json`-Partitionen, expliziter Backendmenge vector, gepinnter
  EmbeddingConfig und getrennten ContentRecord-/Collectionmodellen. Niemals
  TranscriptPayload oder Legacy-Collection als ContentRecord adoptieren.
- FakeEmbedder, offset_windows und checked_vectors werden direkt verwendet;
  VectorArtifact/validate_vectors und UploadState aus der bestehenden Ingestion
  werden für den neuen typisierten Contentplan wiederverwendet. Transcriptplan-
  revalidation und timed chunking eignen sich nicht für unbekannte Zeiten.
- Gemeinsame dimensions-/metadatengebundene Collectionprüfung aus cs50_collection;
  Contentcollections haben eigene Metadatendomain, Generation und Sourcepartition.
  Content-spezifische Upsert-/Readbackprüfung ist nötig, weil der bestehende
  Upsertvertrag ausschließlich TranscriptPayload und Original-SRTpläne akzeptiert.
- A akzeptiert ausschließlich den vorhandenen FakeEmbedder und einen isolierten
  FakeContentTransport. Keine neue reale Encodingimplementierung, kein SDKimport,
  kein Qdrantclient, kein Modellcachezugriff. Echte Transport-/LocalEmbedder-
  Ausführung und Hybridaktivierung bleiben in B gesperrt. Backendset-/RRFvertrag
  für spätere gemeinsame Generationen wird vorbereitet, nicht als aktiv ausgegeben.
- Wiederaufnahme ist ein neuer expliziter Build derselben Auswahl/Konfiguration:
  gleiche fachliche Generation und Punkt-IDs, vorhandene Punkte vollständig
  readbackprüfen, nur fehlende aufschreiben. Kein Import eines Callerplans als
  Berechtigungsbeleg und kein Aktivieren alter unvollständiger Stagingdaten.

## Bestandsprüfung und Freigabestatus

Offizielle GitHub-Issuesuche `repo:rf-data/Personal_Assistant is:issue C24` ergab
keine angelegten C24-Issues. Der vorhandene Entwurf C24-04 in planning/issues.md
bleibt maßgeblich; D01 erlaubt keine automatische Issue-/Projectverwaltung.
Der aktuelle Auftrag konkretisiert daraus A und B, keine konkurrierenden Issues.

[Draft #72](https://github.com/rf-data/Personal_Assistant/pull/72), Head
`3a42b1675dffe823edc179a347fa97dd1a096fd0`, bleibt offen/draft.
Sein Bericht nennt Phase A teilweise blockiert und Phase B blockiert. Die dort
berichteten 84 passed / 2 skipped sind Source-/Executor-/Pilotvertragsprüfungen,
keine reale Modell-/Qdrantabnahme. Historisches Binding data/Harvard versus
data/lectures/Harvard bleibt D06; keine Kopie/Migration/Symlinks hier.
LocalEmbedder besitzt bereits local_files_only, immutable Revision, E5präfixe und
Dimensions-/Tokenprüfung. Qdranthelper unter utils bindet Appsettings/Cloud-Inferenz
und wird nicht importiert. Bestehende CS50-CLI kann explizite Clients erzeugen,
ihre Freigaben sind kein ContentRecord-/C24-04-B-Permit.
Der [direkt gelesene Validierungsbericht dieses Heads](https://github.com/rf-data/Personal_Assistant/blob/3a42b1675dffe823edc179a347fa97dd1a096fd0/docs/qdrant/c21q_validation.md)
weist 0 hochgeladene/verifizierte Punkte, retrieval executed=false und fehlende
Modell-/Instanzfreigaben aus. Seine 157 timed Chunks sind keine E5-Vektorzahl;
die zehn Fragen sind eine Reviewvorlage ohne unabhängige Goldurteile.

C24-04-B: **blocked**. Nicht bereitgestellt sind freigegebene isolierte Instanz,
Namespace, SDK-/Serverversion, konkrete lokal verfügbare immutable Modellrevision,
Cache-/Downloadfreigabe, explizite SourceVersions mit Materialrechten, Transportziel,
Lauf-/Speicherlimits und Recovery-/Bereinigungsabnahme. Kein reales Pilotieren.
C23-06-Realgold und damit fachliche Retrievalqualität bleiben ebenfalls blockiert.

## Implementierte Verträge und Aufruf

```python
from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_rag.cs50_embeddings import FakeEmbedder
from src.tools_rag.content_vector_models import ContentVectorConfig
from src.tools_rag.content_vector_transport import FakeContentTransport
from src.tools_rag.content_vectors import ContentVectorIndex, ContentRetrieval

config = ContentVectorConfig(schema_version=1, name="content_authorized_test",
                             embedding=EmbeddingConfig.fake(max_tokens=32))
engine = FakeEmbedder(config.embedding)
transport = FakeContentTransport()  # ausdrücklich isolierter Testbestand
index = ContentVectorIndex.initialize(
    existing_store, new_explicit_vector_root, cursor_key_file=explicit_private_key,
    config=config, embedder=engine, transport=transport,
)
receipt = index.build(existing_selection, actor=authenticated_owner_operator)
with ContentRetrieval(lexical=existing_fts_index, vector=index).search(
    "Python", method="vector", actor=authenticated_reader, limit=20,
) as page:
    serialized = page.model_dump_json()  # innerhalb der Snapshotguard
# Wiederöffnung: ContentVectorIndex(... dieselbe Config/Engine/Transport ...)
# Expliziter Retry einer unvollständigen Absicht, mit neuer Build-UUID:
receipt = index.resume(existing_failed_build_id, actor=authenticated_owner_operator)
```

Kein neuer CLI-/HTTP-/Jobzugang. Die bestehende FTS-CLI bleibt lexikalisch und
verweigert den inkompatiblen Vektorroot. Actor ist Principal, kein Subjectstring.
Normale content- und dauerhaft synthetische Testroots bleiben getrennt; private
Testadapter dürfen einen synthetic_test-Root nicht als content öffnen/promoten.

Die ursprünglichen IndexRecords/IDs werden unverändert projiziert. Payloadschema
`content_vector_payload_v1`, Adapter `content_vector_adapter_v1`, Schema integer 1,
extra forbid und frozen. Eigenständiger UUID5-Namespace gegenüber Transcriptpunkten.
Payload enthält Record-/Source-/SourceVersion-/Parsed-/Block-ID, Recordstart/-ende,
Kindstart/-ende in Originalcodepoints, ganzen Blocktexthash, exakten Kindtext/-hash,
Originalpayload-/Projektionshash, Modellname/-revision und kompletten
EmbeddingConfigfingerprint sowie Collectionname/-vertrag und Generation.
Keine erfundene Lecture-ID, keine Medienzeiten aus Textoffsets. Bekannte/unknown
Locatoren kommen erst aus der gemeinsamen autoritativen Hydrierung.

`child_start = record.start + window.start`, entsprechend end. Vorhandenes
offset_windows zählt mit Passageprefix und tatsächlichem Tokenlimit; Query wird
mit Queryprefix geprüft/encodiert. Keine eigene Tokenisierung, Normalisierung,
Codeeinrückungskorrektur oder neue Recordgrenze. Leer-/Whitespacefenster werden
nach bestehendem Vertrag ausgelassen; andere Deckungslücken oder Überlappungen
sind Fehler. Indexrecord und Kindpunkt sind getrennte Identitäten. Punkt-ID bindet
den vollständigen Payload, einschließlich Config/Collection/Generation/Kindtext.

EmbeddingConfig bindet alle Parameter, Prefixe, Dimension, L2, Batchgröße und
Revision. Fake muss cs50-test-hash/fake-v1 ausweisen. E5 verlangt im bestehenden
Vertrag 768 Dimensionen, 512 Tokens, query:/passage: und eine immutable 40-Hex-
Revision; LocalEmbedder lädt local_files_only/CPU/trust_remote_code=False. Diese
reale Ausführung wird in A ausdrücklich verweigert, auch bei vorhandenen Paketen.
Weder latest noch Fakevektoren unter echtem Modellnamen werden adoptiert.

## Collection-, Build- und Resumevertrag

ContentVectorConfig legt logischen Namen, Embedding, distance Cosine, Backendmenge
vector, Payload-/Adapterversion und sechs Filterindexes fest: source_id,
source_version_id, parsed_version_id, generation_id, index_record_id,
collection_contract_id. Je Source und Generation entsteht ein deterministischer
physischer Collectionname unter diesem expliziten Namespace. ContentCollection
bindet außerdem den exakten Payload-JSONschemahash, Source und Generation.
Metadatendomain `content_vector_contract` ist mit `cs50_contract` inkompatibel.
Name allein, passende Dimension allein oder alte Transcriptpunkte reichen nie.

FakeContentTransport bildet nur diese logischen Collection-/Filter-/Upsert-
Eigenschaften ab. Die geteilte check_configuration prüft Dimension, Cosinedistance
und komplette versionierte Metadaten; die vorhandene echte Transcriptprüfung nutzt
denselben Kern und unverändert ihre SDK-/Keywordindexgates. Fakeprüfung verlangt
die sechs deklarierten Filterfelder. Das beweist keine real angelegten Qdrantindexes.

Jede Sourcepartition speichert einen strengen ContentVectorPlan plus wieder-
verwendeten VectorArtifact und dessen Hash, privat als `.vectors.json`. Plan bindet
Recordset, Kindpayloads und Collection; validate_vectors prüft Plan-/Modellhash,
Anzahl, Dimension, endliche normierte Nichtnullvektoren. Readback vergleicht alle
erwarteten IDs, vollständigen Payloads und Vektoren; unerwartete/fehlende/defekte
Punkte bleiben Fehler. Keine automatische Korrektur bestehender falscher Punkte.
UploadState wird als interner Prüfnachweis wiederverwendet (`last_upload`); dieser
ist flüchtig. Dauerhafte Absicht/Fehler stehen im bestehenden privaten BuildReceipt,
vollständiger Readbackbeleg im gehashten Partitionsartefakt. Null Kindpunkte benötigen
keinen erfundenen UploadState mit positiver Sollzahl.

Die C24-03-Staging-/Manifest-/Catalog-/Active-Publikation wird direkt geerbt:
PREPARING → BUILDING → VERIFYING → READY → ACTIVE. Kein Teil-Upsert aktiviert
eine Generation. Finaler Rechte-/Snapshot-/Hashcheck ist identisch zu FTS5.
Grantänderungen während Embedding/Upsert sind möglich, verhindern dann aber die
abschließende Aktivierung. Früherer gültiger Active bleibt erhalten. Rootidentity,
Partitionssuffix, Backendfingerprint und Modellconfig unterscheiden die Backend-
Generation vom lexikalischen Bestand. Ein Name/Pointer kann kein Hybrid vortäuschen.

`resume(build_id, actor=...)` liest ausschließlich eine gespeicherte eigene
unvollständige Absicht. Unter Build-/Catalog-/Contentlocks werden Ownership,
Sourceauswahl und der aus aktueller Config plus unveränderten Records erneut
berechnete Generationfingerprint geprüft. Abweichende Config/Modell/Sourceversion
wird abgewiesen. Danach startet der gemeinsame Builder einen neuen Versuch und
prüft nochmals Rechte/Bytes. Er nutzt keine ungeprüften alten Stagingdateien.
Gleiche Fakevektoren und IDs werden kontrolliert reproduziert; bereits vorhandene
identische Punkte werden nur gelesen, fehlende nachgeschrieben und abschließend
vollständig readbackgeprüft. Vorbereitung ohne vollständige Generationabsicht,
discarded und bereits aktive Versuche werden nicht als Resume adoptiert.

Modell-/Collectionwechsel brauchen einen neuen expliziten Indexroot und eine neue
Generation; alte konfigurierte Roots bleiben für ihre frühere Config unverändert.
Rebuild mit neuer gepinnter Parsed-/SourceVersion im selben Modell erzeugt neue
Generations-/Kindpunkt-IDs. Kein automatisches latest, Reparieren oder Collection-GC.
`discard_build` entfernt wie bisher nur eigene inaktive lokale Derivate. Fake-
Collections bleiben im isolierten Transport; reale Retention/Namespacebereinigung
muss B ausdrücklich regeln. Kein heimliches Löschen fremder oder alter Collections.

## Sichere Suche und Scorevertrag

ContentRetrieval ist eine dünne method-Auswahl auf denselben ContentIndex-Guard.
Lexical bleibt der Default, optional vector, unbekannt/fehlend/hybrid liefert
Unavailable. Beide Adapter müssen denselben autoritativen ContentStore verwenden.
Kein stiller Fallback oder zweiter Hydrierungs-/Cursorweg.

Vor Queryencoding oder Transportzugriff wird der angefragte Scope mit live
Owner/Readgrant und Course geschnitten. Fremde/unbekannte Sources bleiben gleich
unsichtbar, ohne Backendrequests oder Counts. Danach gelten dieselben vollständigen
C24-02-Closure-/Status-/Sourcepartitionchecks wie bei FTS5. Ein quarantänisierter
gepinnt selektierter Bestand sperrt die ganze Sourcepartition; kein alter Fallback.
Archivierter Vektorplan wird erneut aus diesen aktuellen Originalrecords abgeleitet
und mit gespeicherten Payloads/Config/Generation verglichen. Kompletter aktueller
Transportreadback muss passen, bevor Kandidaten als vollständig gelten.

Exact-Queryfilter bindet alle sechs Felder, nach Contenttyp erlaubte Record-IDs
und Source-/ParsedVersionmengen. Alle passenden Kindpunkte werden begrenzt gelesen;
keine ANN-/Top-k-Abkürzung. IDs, Payloads, Vollständigkeit und endliche Scores werden
geprüft, der Cosinewert zusätzlich gegen die geprüften Archivvektoren nachgerechnet
(Floattoleranz abs 1e-6 / rel 1e-5, normbedingter Randtoleranzbereich 1e-5).
Pro Record gewinnt höchster Kind-Cosinescore, Tie über Start/Ende/Punkt-ID;
danach Recordsortierung Score DESC / Record-ID ASC. Mehrere Kinder erzeugen keine
doppelten Records und keine erfundenen Text-/Zeitanker.

Public SearchHit/SearchResultPage sind additive Varianten des bestehenden DTOs:
method vector, Komponente backend content_vectors_fake, cosine_l2_v1,
higher_is_better; keine Wahrscheinlichkeitsnormalisierung. Excerpt und Locatoren
kommen aus demselben live geprüften Originalblock wie bei lexical. Kein Payload,
Collection-/Cachepfad, Rawreceipt oder globaler Indexcount in der Antwort.

Die Cursorlogik und HMACbindung an Actor/Role/Courses, Query/Filter/Limit/Method,
Generation, opaken Content-Snapshot und vollständigen Resultset bleiben gemeinsam.
Vector hat eine eigene HMACdomain; ein Lexicalcursor ist ungültig. TTL fünf Minuten,
keine ungeschützte Offsetpagination. Bei Rechte-/Snapshot-/Generationswechsel
keine Items, sondern kontrollierter Neustart. Locks bleiben bis zur Verwendung
innerhalb des Contextmanagers gehalten; Sourcewriter/Aktivierung erhalten Busy.

## Grenzen, Hybrid und B-Übergabe

A zusätzlich: maximal 128 Fake-Dimensionen, 4.096 Kinder pro Sourcepartition,
128 Fakecollections und 8.192 gespeicherte Punkte pro isoliertem Fake-Transport.
Bestehende Dateigrenze 64 MiB je Partition, 128 MiB kumulative Querybytes,
64 MiB Recordbudget, 1.000 Resultrecords, 32 erlaubte Sources, 100 Hits/256 KiB,
zwei Queryslots, 2-s-Query-/5-s-Guard und 15-min-Build bleiben bestehen.
Vollständige Reprojektion, Fake-Tokenfenster und Readback kosten CPU/RAM. Keine
reale Last-/RSSfreigabe; die dokumentierte C24-03-Skalierungsgrenze bleibt offen.
Bounded Python-/Hashschritte sind keine hart präemptive Isolation.

HybridContract bereitet ausschließlich Backendmenge lexical+vector, backend_rrf_v1,
Konstante 60 und Zustand blocked_pending_pilot vor. B muss eine vollständige
gemeinsame Selection-/Backendgeneration aktivieren, Kindpunkte zuerst zu Records
reduzieren und dann je Backendrang `1/(60+rank)` fusionieren. Keine Addition von
Cosine/BM25 und kein Hybridlabel bei fehlendem Backend. A aktiviert keine Fusion.

B benötigt zusätzlich zur obigen Freigabeliste: konkreten Qdranttransport mit
SDK-/Server-/Metadaten-/Keywordfilterprüfung, begrenztes exaktes gefiltertes Query,
Timeout/Isolation, echte Persistenz-/Readback-/Crash-/Resume-/Konkurrenzabnahme,
Modellpräfix-/Fasttokenizer-/Unicodeprüfung mit lokalem E5 und explizite
Snapshot-/Recovery-/Namespace-/Cleanupverantwortung. Die FakeSnapshot-Methode
simuliert Neustart ausschließlich im Test; sie ist kein Qdrantbackup und keine
Freigabe, Materialtexte in beliebige Dateien oder an Remoteziele zu exportieren.
Vor echtem Remote-Upsert muss B die aktuelle Owner-/Course-/Statusfreigabe je
Übertragung neu prüfen; A überträgt ausschließlich in isolierten Prozessspeicher.
Lange reale Modell-/SDKoperationen benötigen eine gesondert geprüfte abbruchfähige
Worker-/Transportgrenze. A ist dafür kein Laufzeitnachweis.

Es gibt keine reale Collection-/SDK-/Modellausführung, keinen CLI-/HTTP-/UI-/Job-
oder Produktionsbetrieb, kein Hybridbenchmark und keine Retrievalgold-Metriken.
Das optionale Paket schließt weder D06/D07 noch C23/C24/C26 fachlich automatisch.

## Tatsächliche Nachweise

Synthetische Laufzeitausgaben: [Kindpayload](examples/content-vector-payload.synthetic.v1.json)
und [Suchseite](examples/content-vector-search.synthetic.v1.json). Beide stammen
aus echten lokalen B-Adapter-/ContentStore-/Fakeadapterläufen, keine manuell
erfundenen Treffer. Fake-Scores belegen nur Vertrag und deterministische Zuordnung.

Umgebung: Python 3.12.12, SQLite 3.50.4, Pydantic 2.13.5, System-Pytest 7.2.1,
Ruff 0.16.0. Vorhandener Interpreter ai-job-search/.venv; System-Pytest über
PYTHONPATH, keine Installation/Sync. Sowohl dort als auch im explizit geprüften
Projektinterpreter fehlen qdrant_client, sentence_transformers und tiktoken.
Private Modellcaches oder Realmaterialpfade wurden nicht durchsucht.

Tatsächliches gemeinsames Pytestpräfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
 -q --disable-warnings -p no:cacheprovider
```

| Lauf mit diesem Präfix | Ergebnis | Konkreter Bezug |
| --- | --- | --- |
| tests/test_content_vectors.py --basetemp=/tmp/c2404-final33 | **33 passed / 0 failed / 0 skipped**, 165,25 s | abschließender ganzer Lauf einschließlich Typ- und zusätzlichem Snapshot-Kapazitätsgate |
| tests/test_content_vectors.py --basetemp=/tmp/c2404-final | **32 passed / 0 failed / 0 skipped**, 79,61 s | vollständige neue Suite, echte private Store-/Indexdateien; Fake-Encoding und Fake-Transport |
| dieselbe Datei -k embedding_errors --basetemp=/tmp/c2404-gate | **1 passed / 31 deselected**, 4,82 s | nach ergänzter Typprüfung auch nach Konstruktion: Austausch gegen realen/unklaren Transport verweigert; Überschneidung, nicht addieren |
| tests/test_content_vectors.py tests/test_content_fts.py tests/test_content_index_projection.py --basetemp=/tmp/c2404-first | **114 passed / 1 failed / 0 skipped**, 324,82 s | 47 FTS- und 41 Projektionsfälle sämtlich grün; damalige 27 Vektorfälle mit einer später korrigierten Testannahme |
| tests/test_cs50_embeddings.py tests/test_content_store_models.py tests/test_content_store_adapters.py tests/test_content_store_store.py tests/test_content_read_contracts.py --basetemp=/tmp/c2404-store | **126 passed / 0 failed / 0 skipped / 4 setup errors**, 129,34 s | 122 bestehende Store-/Adapter-/Readfälle und vier reine Offset-/Vektorprüfungen grün; vier timed-Chunk-Mappings wegen tiktoken nicht eingerichtet |
| tests/test_cs50_embeddings.py tests/test_cs50_ingestion.py tests/test_cs50_index_contract.py tests/test_cs50_retrieval.py tests/test_cs50_index_cli.py tests/test_cs50_index_end_to_end.py --basetemp=/tmp/c2404-legacy | **4 collection errors**, 1,16 s; 11 sonst sammelbare Fälle nicht ausgeführt | fehlendes qdrant_client verhindert SDK-Module und davon abhängige CLI-Fixtures; gesamter Lauf bricht vor Ausführung ab |

Die vier Setupfälle sind `test_real_import_chunk_mapping_and_empty_cues` für
cs50_python/cs50_cybersecurity, `test_unrelated_private_configuration_not_exported`
und `test_partial_cue_keeps_real_cue_times`. Importkette bind_cs50_transcript →
find_knowledge → core.memory → tiktoken. Kein Fehler wurde durch ein Fake-Modul
oder Skip verdeckt. Die bestehende echte SDK-Collectionprüfung ist **not_checked**;
der gemeinsame metadaten-/dimensionsgebundene Kern wird zusätzlich im neuen
Legacy-Gatetest ohne SDK tatsächlich geprüft. Das ersetzt keine SDKintegration.

Abgedeckt: Payload-/Punktidentität und Legacyabgrenzung; Unicode/Emoji/Combining,
Codewhitespace, Kind- und von null verschiedene Recordoffsets; bekannte SRT- und
synthetische Unknown-Time-Locatoren; neue Raw-/ParsedVersion und geänderte
Modellkonfiguration; korrekte höchste Kind-Cosinewerte, deduplizierte vollständige
Cursorseiten und Tie-Break; ungültige Scores/Hashes/Collectionmetadaten; keine
fremden Collections/Requests/Counts; Livegrants, Quarantäne und Tombstones;
fehlende Dateien/Collection ohne Fallback; Abbruch vor Embedding/bei Teil-Upsert,
unvollständiger Readback, explizites Resume mit gleichem Fingerprint und Ablehnung
falscher Config/Actor; identischer Retry ohne weitere Upserts; Guard-Busy und
ACLänderung während Build; separater Prozess aus explizitem FakeSnapshot;
unveränderte autoritative Contentbytes. Prozess-/Catalog-Parallelität und SIGKILL-
Aktivierungsgrenzen des gemeinsamen Builders werden zusätzlich durch die 47
unveränderten FTS-Fälle geprüft, nicht als reale Qdrantprozesse ausgegeben.

Entwicklungsläufe derselben Vektordatei: 31 passed / 1 failed in 137,44 s bzw.
97,15 s. Der Unicode-Test verwendete zuerst einen nicht vorhandenen Getter,
dann irrtümlich .items statt des vorhandenen SourceVersion-Tupels. Korrigiert
wurde der Testaufruf, keine Store-API. Im gemeinsamen ersten Lauf nahm ein
Pagingtest identische Fake-Cosinescores an; tatsächliche Hashfeatures unterscheiden
sich je Text. Er prüft nun den wirklichen Score und stabilen IDtie sowie den
höchsten Kindscore. Anschließend zwei gezielte Unicode-/Resumefälle bestanden
(10,83 s), danach die obige vollständige 32er-Suite. Keine Entwicklungsläufe
oder überlappenden Nachprüfungen werden zu einer erfundenen Gesamtsuite addiert.
Bei der Ergänzung des Snapshot-Kapazitätsfalls blieb zunächst ein Rest des
vorherigen Testfunktionskörpers im neuen Test stehen (32 passed / 1 failed,
132,71 s). Die Testgrenze wurde korrigiert; die abschließende 33er-Suite prüft
beide Fälle erfolgreich. Der zusätzliche Code begrenzt auch eingelesene Fake-
Snapshots auf 128 Collections und 8.192 Punkte, bevor Resume möglich ist.

Ruff Check / Format Check erfolgreich für acht geänderte/neue Pythondateien plus
unverändertes content_fts.py; git diff --check erfolgreich. Beide Laufzeitbeispiele
gegen die tatsächlichen Modelle validiert, 62 lokale Linkvorkommen in fünf
Dokumenten geprüft. Keine vollständige
Repositorysuite oder reale Parsing-/Relevanz-/HTTP-/UI-/Qdrant-/E5abnahme.
PDFfälle verwenden vorhandene normalisierte Modelle, keinen nativen PDFparser.
Eigene temporäre synthetische Testroots/Caches werden nach Prüfung entfernt;
Logs bleiben außerhalb des Repositories. Der offene PR-Worktree bleibt erhalten,
andere Worktrees, Entwicklungsumgebungen und Primärcheckouts unverändert.
