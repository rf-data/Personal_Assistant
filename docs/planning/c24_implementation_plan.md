# C24: Implementierungsplan nach dem Indexing-/Retrieval-ADR

18.10.2026 · Basis Master `95c4c40c1ab738ce1d75ac9ed554a46613419133` nach #82.
C24-01 lieferte Architekturverträge und diesen Plan. C24-02 ergänzte die
[erste Projektion ohne Backendindex](../architecture/index_projection_implementation.md),
entsprechend 02-A. Der aktuelle Benutzerauftrag **C24-03** implementiert
[Source-FTS5, Generationen und interne Suche](../architecture/content_fts_implementation.md),
entsprechend 02-B plus 03-A. HTTPsearch, Jobanbindung und UI sind weiterhin offen.
C24-04-A ergänzt jetzt den [ContentRecord-Vektoradapter samt Fake-Abnahme](../architecture/content_vector_implementation.md).
C24-04-B (reale Modell-/Qdrant-/Hybridabnahme) bleibt mangels konkreter Freigaben
blockiert; A, Draft #72 oder ein Merge erteilen diese Freigaben nicht.
C24-05-A ergänzt die [technische Retrievalevaluation und unabhängigen Goldverträge](../cs50/evaluation/content_retrieval_evaluation.md).
Die fachliche C24-05-B-Abnahme bleibt an freigegebene Realbundles, unabhängiges
Gold und einen vollständigen Reviewpool gebunden; keine D01-/D07-Freigabe.
C24-05-C hält eine [Pilotvorbereitung mit konkreten Blockaden](../cs50/evaluation/c24_real_corpus_pilot.md)
und ausschließlich bestehende Korpusmetadaten fest. A/#87 ist inzwischen integriert;
B/#88 liefert bislang nur Architektur, keinen Reviewworkflow. Reale und vollständige
synthetische Pilotabnahme bleiben bis zur tatsächlichen B-Implementierung gesperrt.
Die folgenden detaillierten Paketanforderungen bleiben Prüfplan; tatsächliche
Abnahme und Grenzen stehen im verlinkten Implementierungsbericht. [ADR](../architecture/retrieval_indexing_adr.md),
[Indexrecord-/Suchvertrag](../architecture/index_record_contract.md),
[C23-Stand](c23_implementation_plan.md), [Governance](governance.md).

## Autoritativer Plan und offizielle Nummerierung

Die vorhandenen Entwürfe in [issue_plan.v1.json](issue_plan.v1.json) und
[issues.md](issues.md#c24-01) bleiben unverändert. Insbesondere:
C24-02 umfasst **Volltextindex/Reindexierung**, C24-03 **Such-API/Trefferbelege**.
Die im Auftrag vorgeschlagenen Projektions-/FTS-Unterpakete werden darunter
geordnet, nicht als neue konkurrierende Issues nummeriert. Keine Issue-/Project-
Erstellung und kein automatischer Statuswechsel (D01 bleibt separat).

| Offizieller Entwurf | Kleine sequenzielle Implementierungs-PRs / Abnahme |
| --- | --- |
| C24-01 Strategie | Dieser ADR, Normativvertrag, sichere Snapshotgrenze und präziser Plan; noch keine Runtime |
| C24-02 Volltext/Reindexierung | **02-A** Indexmodelle + ein deterministischer Projektor + bounded autorisierter Export; **02-B** Generations-/Rebuildstore und FTS5-Sourceadapter samt interner Suche; **02-C** explizite C16-Anbindung/Statusvertrag nach freigegebenem Katalog-/Jobvertrag |
| C24-03 Such-API | **03-A** Retrievalfassade, Livehydrierung, Cursor und Redigierung; **03-B** opt-in Capability/Routes am bestehenden Gateway, begrenzte Antworten und Cross-Repo-DTOvertrag; kein zweiter Server |
| C24-04 optionaler Pilot | Vorhandenen Draft #72 zuerst reviewen; **04-A** ContentRecord-Ankeradapter unter vorhandenen Vektor-/Embeddinggates; **04-B** explizit freigegebene lokale Instanz-/Encoding-/Retrieval-/Recoveryabnahme, dann optional Hybrid |
| C24-05 Evaluation | Review-/Querydatensatz und Metriken, technische Fixtureabnahme; danach separat freigegebene reale Relevanzurteile, Limits und manuelle Format-/Releaseentscheidung |

C24-02-A beginnt auf gemergtem C23 und diesem ADR. 02-B benötigt 02-A, 03-A
benötigt 02-B und C23-04; 03-B benötigt 03-A. 02-C benötigt zusätzlich den expliziten
Job-/Katalogvertrag; es blockiert die unabhängige lokale Bibliotheksabnahme nicht.
04 benötigt die neue Ankerprojektion und den sicheren Queryvertrag, aber bleibt
optional. 05 kann technische Metriken parallel entwickeln, reale Abnahme benötigt
D07 und C23-06-Realbelege. Keine feste Termin-/Personal-/Kapazitätszusage.

## C24-02-A: deterministische Projektion und Storegrenze

- Implementiere ausschließlich `index_models.py`/`index_projection.py` unter
  `src/content_store/` plus fokussierte Tests; bestehende Typen/Hashhelfer importieren.
- Eine gemeinsame autorisierte Export-/Hydrierungsfunktion an den vorhandenen
  Maintenance-/DBlockprimitiven ergänzen. Alle selektierten Versions-/Blob-/Block-
  und Locatorbezüge im selben Snapshot prüfen; private bounded Snapshotdateien
  statt viele unverbundene paginierte Getter. Keine Defaultpfade und keine DB-DDL-
  Migration. Read-only-Verhalten und vollständige Byteinventare vor/nach beweisen.
- Exakte gespeicherte Aggregationsauswahl nutzen, einschließlich SRTpointermapping.
  Validierte Unitdeckung und Referenzcounts; keine Promotion von Formeln/Bildern/
  PDFtables/code_view. Keine neue HTML-/PDF-/SRT-Extraktion und kein Gate-Reparse.
- Deterministische body-/Record-/Policy-/Generationshashes mit kleinen synthetischen
  ASCII-/Unicode-/Combining-/Emoji-/CRLFfällen. Wiederholung und Änderung einzelner
  Identitätsparameter beweisen. Pro Source-/Parserwechsel keine IDkollision.
- Harte Block-/Chaptergrenzen, deckungsgleiche nichtüberlappende Units, Overlap128,
  exakte Originalrekonstruktion, Tabellenzellen-/Ansichtduplikation und unbekannte
  Medienzeiten prüfen. C23-05 ist kein TXT-Bundleadapter; fehlende Publikation bleibt
  unsupported/unverified, kein synthetischer Ersatz als Original.

Fertig wenn derselbe Snapshot dieselben Records liefert und fehlende/unerlaubte/
quarantänisierte/inkonsistente Inputs fail closed bleiben; weder Teststoredaten
noch freie Caller-Dicts können einen produktiven Indexsnapshot legitimieren.

## C24-02-B/C: FTS5, Generationen, Rebuild und Jobs

Neue kleine Backendmodule unter `src/tools_rag/content_fts.py` und
`src/tools_rag/content_index.py`; beide konsumieren nur den **einen** Projektor.
Separater privater abgeleiteter Root; kein globaler Chroma-/Qdranthelperimport.

02-B muss tatsächliche SQLite-/FTS5-Integration im expliziten Testroot beweisen:
Sourcepartitionen, Quotes/Operatoren, stabile Einfügeordnung/Scores, RRF-Ties,
vollständige begrenzte Listen, Pfad-/SQL-/Querylimits, Signatur-/Schemagates und
Hash-/Vollständigkeitsprüfung vor Manifest/Activewechsel. FTS5-Verfügbarkeit beim
Start testen; fehlendes Modul bedeutet unavailable, kein Download/Extensionload.
SQLite-BM25 ist lexical, kein Recall-/Semantiknachweis für Code oder Formeln.

Echte Prozessabbrüche vor/nach Manifest, vor/nach Active-Replace und vor Response;
keine Teilergebnisse, konsistentes Wiederöffnen, CAS-Konflikt zweier Builder,
ACLentzug während Build, kaputte/fehlende Files, Budget/ENOSPC und unbekanntes
Schema prüfen. Rebuild darf ohne ursprünglichen Arbeitsworkspace, Reparse oder
Knowledge funktionieren. Quarantäne/Tombstone in einer indexierten Version sperrt
Sourcepartition inklusive alter Statistiken, andere erlaubte Sources bleiben in
separaten Requests nutzbar. Alte Generation nicht als Suchfallback anbieten.

02-C versioniert erst den ausdrücklichen Indexrequest-/Catalog-/Processregistry-/
Settings-/Outputvertrag für bestehende C16-Owner-/Course-/Bestätigungs-/Executor-
Kontrolle. Input: konkrete Store-IDs/Selection/Policy; Output: redigierter
`index-build.v1.json` (IDs, Status, Counts ausschließlich im eigenen Scope, feste
Fehlercodes). Idempotenz, restart/cancel/deadline und parallele Wiederholung prüfen.
C18-v1 endet weiterhin am Materialhandoff; eine Indexstage braucht separat neue
Stage-/Output-/Capabilityverträge mit UIabnahme. Kein watcher/cron/zweite Queue,
keine automatische Indexierung nach Import und kein Jobzugriff unter Contentlocks.

## C24-03: interner Suchvertrag und spätere API

Implementiere Fassade über Adapter, nicht zweite Ranking-/Indexprojektion.
Die atomare Livehydrierung aus 02-A erhält eine querygebundene Guard-Lebensdauer.
Tests: Viewer mit Grant; Owner ohne Course; Operator ohne Ownership; gleichhashige
fremde Sources; Grantentzug zwischen Seiten; Writer Busy während Guard; aktuelle
Tombstones/Quarantäne; manipulierte Bodies/Anker; fehlende Bytes; unbekannt/fremd
ununterscheidbar; verborgene Inhalte verändern keine erlaubten Scores/Antworten.
Keine globalen BM25-/Indexcounts, kein Backendpayload als alleiniger Berechtigungsbeleg.

C24-03-B ergänzt erst nach diesen Tests am C16-Gateway eine separate opt-in
Searchcapability und den JSON-/Fehler-/Cursorvertrag. Bestehende Job-, Workflow-
und Content-DTOs bleiben kompatibel. Keine C24-01-Route ist heute aufrufbar.
APIbeispiele aus tatsächlicher synthetischer Gatewayausführung erzeugen;
Keine manuellen Fantasieantworten als Laufzeitevidenz. Query/Cursor/Response-
Limits, auth/no-store, fehlende Capability, Socketabbruch und maximale Guarddauer
mit wirklichem Loopbackserver testen. Keine externen APIziele.

## C24-04: vorhandene Semantik gezielt adaptieren

Draft #72 bleibt vorhandener Pilot, kein paralleler Download-/Ingestionpfad.
Zuerst Iststand/Phase-A-/Phase-B-Belege und D06 prüfen. SDK/isolierte Instanz,
immutable lokale E5-Revision, Modellrechte/Cache und jede Remoteübertragung müssen
ausdrücklich bereitgestellt/freigegeben werden. Keine automatische Installation,
Collectionanlage oder Embeddingkosten durch FTS5-Arbeit.

Wiederverwenden: EmbeddingConfig, LocalEmbedder/checked_vectors, konfigurations-
gebundene Collection-/Readback-/Resume-/Transportgates. TranscriptPayload bleibt
zeitgebunden und unverändert; ContentRecord benötigt einen expliziten neuen
Payloadschema-/Collectionvertrag innerhalb derselben bestehenden Pipeline.
Alte Punkt-IDs niemals als ParsedVersion-/Block-IDs ausgeben. Das ist eine
gezielte Erweiterung, keine zweite konkurrierende CS50-Ingestionimplementierung.

Alle Backends verwenden dieselben Indexrecord-IDs. Falls das bestehende
`offset_windows` einen Record weiter unterteilen muss: Kindfensteranker
`block_start=record.start+window.start`, entsprechend end; jeder Vektor verweist
auf die ursprüngliche Record-ID und exakte Originalsubstringhashes. Rückabbildung
mehrerer Kindpunkte zu einem Record: höchster Cosinescore, Tie über Kinderanker;
dann deterministischer Recordrang vor Hybrid-RRF. Keine Transcripttimestamps
interpolieren und TXT nicht in TimedPayload zwingen. Getrennte Generationen bei
verschiedener Backendmenge; keine still teilweise verfügbare Hybridantwort.

## Evaluationsvertrag für C24-05

Vorhanden: `cs50_retrieval_evaluation.ranking_metrics` berechnet Recall/MRR für
vollständige nichtleere Mengen; `reviewed_metrics` prüft reale zeitgebundene
Transcriptbelege. Es ist **kein** universeller Content-/Precision-/nDCGvertrag.
`tools_evaluation/retrieval_metrics.py` sind Stümpfe. Reine Rankingarithmetik
wiederverwenden/zentral ergänzen statt parallele Formeln pro Adapter; spezifische
Pilotreviewgates unverändert erhalten. C23-06-Modelle für Review-/Herkunftsregeln
referenzieren; Retrievalrelevanz benötigt einen eigenen kleinen versionierten
Urteilsvertrag statt Zweckentfremdung von Parsing-Expectedtexten.

`ContentRetrievalEvaluationSet` v1 soll dataset_version, origin (synthetic/real/unknown),
Query-ID/-Text, erlaubten Actor-/Course-/Source-Scope als nichtgeheime Testidentität,
exakte Source-/Parsed-Versionen/Rawhashes, generation/config fingerprints und k
binden. `ContentRelevanceJudgment` v1 bindet Query-ID, stabile gold_target_id, vollständigen
Blockanker und geprüften Locator, grade (0–3), Annotationmethode, Reviewer,
Reviewbeleg/-datum, pending_review/confirmed/rejected und Mehrdeutigkeitsnotiz.
`pool_complete` mit begrenztem geprüftem Korpusumfang ist explizit zu bestätigen.
Keine Goldableitung aus Suchresultaten und keine erfundenen Reviewer. Unbestätigte,
ambige oder unbekannte Urteile nicht in evaluierbare Nenner aufnehmen.

Goldziel ist eine unabhängig annotierte Originalregion, **kein bestimmtes
Chunkingfenster**. Treffer kreditieren ein Ziel nur bei gleichem Parsed-/Block-Hash
und vollständiger Überdeckung der annotierten [start,end)-Region; überlange Ziele
über 2.000 Codepoints vor Review explizit in kleinere Zielregionen zerlegen.
Mehrere überlappende Chunks desselben Ziels liefern nur beim ersten Auftreten
Relevanzkredit; ihre weiteren Rangpositionen bleiben bestehen (Gain 0), kein
nachträgliches Vorrücken. Ziele im Gold pro Query disjunkt annotieren oder als
bewusstes gemeinsames Ziel gruppieren, damit kein Treffer Mehrfachkredit erzeugt.
Precision und nDCG benutzen dieselbe eindeutige Zielkreditierung. C24-05 muss diese
Zuordnung samt Grenzen unabhängig reviewen; kein Jaccard-/Textähnlichkeitsersatz.

| Metrik | Zähler / Nenner / nicht bestimmbar |
| --- | --- |
| Precision@k je Query | Neu kreditierte relevante Ziele in ersten k Rängen / **k**, auch wenn weniger Treffer; nur bestätigter vollständiger Reviewpool und bewertbare Top-k erlauben Interpretation |
| Recall@k je Query | Verschiedene relevante getroffene Ziele / alle relevanten bestätigten Ziele des exakt autorisierten, abgeschlossenen Pools; kein relevantes Ziel → null |
| RR@k / MRR@k | 1/erstem relevanten Rang innerhalb k, bei keinem Treffer 0; Summe RR / Zahl evaluierbarer Queries mit mindestens einem relevanten Ziel |
| nDCG@k | DCG=sum((2^grade−1)/log2(rank+1)); / IDCG desselben vollständigen abgestuften Zielpools, Top-k ideale Reihenfolge; IDCG=0 → null |
| Locator-Korrektheit | Unabhängig bestätigte korrekte Locatorzuordnungen / alle retournierten und unabhängig geprüften Locatorzuordnungen; known/unknown separat und keine erwartete Geometrie erfinden |
| Provenienz-Korrektheit | Korrekte Source-/Version-/Block-/Text-/Raw-/Parserankerkette / tatsächlich geprüfte retournierten Trefferketten; technische Hashprüfung und unabhängiges Originalreview separat |
| ACL-/Leakagefehler | Verbotene ausgegebene IDs/Texte/Locatoren/Scores bzw. fremdbeeinflusste Antworten, sowie Zahl tatsächlich ausgeführter Angriffsszenarien; **jeder** bestätigte Fehler sperrt Release |

Jeder Report enthält rohe Zähler/Nenner, Nullgründe, dataset_version, Methode,
Format und Ursprung sowie evaluierbare/nicht evaluierbare Queryzahlen.
Precision/Recall/MRR/nDCG macro: Summe definierter Querywerte / Anzahl dieser Queries;
zusätzlich Einzelqueryzähler/-nenner, keine stillen Nullwerte für fehlende Reviews.
Null Nenner ist null/not_determinable, keine Nullprozentqualität. Unvollständige
Pools oder unbewertete Top-k bleiben not_evaluable. Relevanzgrad 0 ist ein geprüftes
negatives Urteil, kein Default für ungeprüfte Treffer.

Drei strikt getrennte Gruppen: synthetische technische Fälle, reale berechtigte
Quellen ohne bestätigte Urteile (nur Technik), reale unabhängig bestätigte Gold-
Urteile (begrenzt fachlich evaluierbar). Unknown-Origin keine Realbewertung.
FTS/vector/hybrid, k und sämtliche Konfigurationen separat berichten. Aktuell keine
realen Retrievalqualitätszahlen: C23-06 hat null vollständige freigegebene Realbundles
und null bestätigtes Gold. Die zehn historischen Pilotfragen sind keine Freigabe.

## C25/C26-Übergabe und verbleibende Risiken

- C25-01 konsumiert erst die tatsächliche versionierte C24-03-Capability; C23-04
  ermöglicht heute nur Contentreads. Filter/Paging bleiben serverautoritativ.
- C25-02 verknüpft Suchanker über vorhandene Text-/Struktur-/Rawrouten, rendert
  Unicodecodepoints korrekt trotz JavaScript-UTF-16 und zeigt unknown statt 0.
  Kein Filesystemzugriff, ungeschütztes HTML oder automatischer Originalfetch.
- C25-03 zeigt scoped Indexstatus, keine fremden Counts; Refresh ist keine
  Schreibaktion. C25-04 braucht echte Browser-/Rollen-/Filter-/Deep-Linkabnahme.
- C26 prüft Mount/atomic replace/fsync/flock, Ressourcen/Timeout/Last, Host-/UID-
  Isolation, TLS/Auth, private Keyrotation, Retention und Verbundrestore. Index ist
  rebuildbar, aber alte Textkopien bleiben schutzbedürftig. Keine automatische GC.
- Ein Build verlangt Ownership aller ausgewählten Sources. Gemischte Ownership
  erteilt keinem Operator zusätzliche Rechte; ein späterer delegierter Builddienst
  bräuchte einen eigenen ausdrücklich freigegebenen Vertrag.
- Sourcepartitionen erhöhen Dateianzahl/Fan-out und erzeugen bewusst andere Ränge
  als globales BM25. Die konservativen 32-Source-/1.000-Match-/Byte-/Zeitgrenzen
  können Suchanfragen sperren. Keine Skalierungs-/Relevanzfreigabe vor Messung.
- Referenz-only Formeln/PDFtables/Bilder sind heute nicht im Textindex. Unicode61
  bewahrt nicht jede Code-/Operatorunterscheidung im Matching. Spätere strukturierte
  Suchprojektionen erfordern Policyversion und eigene Abnahme.
- Full-closure-Livehashprüfung kostet I/O; kein ungeprüfter Cache eingeführt.
  Bestehende Storelimits oder WAL-/Journal-/Recoveryfences bleiben vorrangig.
- D06/D07 und fachliche C23-/C24-Abnahme bleiben offen; FTSentscheidung und Merge
  genehmigen weder historische Übernahme noch Produktivbetrieb oder echte Embeddings.

## Tatsächlich ausgeführte Prüfungen C24-01

Geprüft auf obiger Masterbasis, Python **3.12.12**, vorhandenes System-Pytest
**7.2.1**, Pydantic **2.13.5**, SQLite **3.50.4**. Keine Installation/Sync,
kein Indexservice und keine Suche über Originalmaterial. Runtime, Tests,
Dependencies, Issuepläne und sämtliche Originalbytes bleiben unverändert.

Tatsächlicher begrenzter bestehender Vertragslauf:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
 -q --disable-warnings -p no:cacheprovider \
 tests/test_content_read_contracts.py tests/test_cs50_embeddings.py \
 --basetemp=/tmp/c2401-contract-tests
```

**18 passed / 0 failed / 0 skipped / 4 setup errors**, 22 gesammelte Fälle,
1,42 s. Alle 14 vorhandenen DTO-/Redigierungs-/Locatorfälle sowie vier reine
Embedding-/Vektor-/Offsetfälle bestanden. Vier timed-Transcript-Mappingfälle
konnten wegen fehlendem **tiktoken** nicht eingerichtet werden:
`test_real_import_chunk_mapping_and_empty_cues[cs50_python|cs50_cybersecurity]`,
`test_unrelated_private_configuration_not_exported`,
`test_partial_cue_keeps_real_cue_times`. Importkette:
`bind_cs50_transcript → find_knowledge → core.memory → tiktoken`.
Dies sind nicht ausgeführte Setupfälle, keine bestandenen Mappingtests. Keine
Dependency nachinstalliert, kein umfangreicher Regressionstest und keine C24-
Runtimeabnahme behauptet. Pytest-7-Warnungen sind keine Skips.

Zusätzlich eine direkte Offline-Pythonprüfung mit demselben Interpreter,
PYTHONPATH und PYTHONDONTWRITEBYTECODE, ohne Pytest/SDK/Modell:

- Fünf geänderte/neue Markdowndateien: **121 lokale Linkvorkommen einschließlich
  Zielanker** geprüft; alle vorhanden. Je Dokument eine Hauptüberschrift,
  geschlossene Codefences; keine absoluten privaten Hostpfade als Linkziele.
- JSON im `c24-anchor`-Marker eingelesen; Originalslice, Textlänge, beide UTF-8-
  SHA256-Werte sowie Unterschiede zu NFC und UTF-16 überprüft.
- Bestehende `canonical/fingerprint/deterministic_id` auf identischen JSON-
  Roundtrip und verändertes Ankerfeld geprüft. Dies ist keine Prüfung einer
  bereits implementierten IndexRecord-Klasse.
- Bestehenden ContentLocator mit unknown/not_applicable geprüft, keine Nullzeit
  in 0 gewandelt. `ranking_metrics([{1,2},{3}], [[2,4],[0,3]], k=2)` ergibt
  Recall/MRR je 0,75: ausdrücklich synthetischer Arithmetikcheck, keine Modellwerte.
- FTS5-Featureprobe ausschließlich `sqlite3.connect(":memory:")` und
  `CREATE VIRTUAL TABLE capability_probe USING fts5(text)`: verfügbar.
  Keine Textinserts, persistenten Indexdateien oder produktive Datenbanken.
- `git diff --check` erfolgreich; abschließender Diff ausschließlich fünf
  Dokumentationsdateien. Ruff entfällt, weil keine Pythondatei geändert wurde.

Die Prüfungen sind technische Dokument-/bestehende Primitiveprüfungen.
Deterministischer neuer Projektor, FTSranking, Generationwechsel, Live-ACL-Suche,
HTTPsearch, Performance, Browser und reale Retrievalqualität sind hier **nicht
implementiert oder getestet**; dafür gilt die obige Folge-PR-Matrix.

Eigener temporärer Pytestroot wird nach Abschluss entfernt. Der C24-Worktree
bleibt bis zum Merge seines offenen PR bestehen; Primärcheckouts, andere
Worktrees/Branches, private Bestände und virtuelle Umgebungen bleiben erhalten.
