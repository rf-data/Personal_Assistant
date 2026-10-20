# C24 Indexrecord- und Retrievalvertrag v1

18.10.2026 · Normative Spezifikation. **C24-02 implementiert Modelle und
lesende Projektion**; C24-03 ergänzt Build/Rebuild, Source-FTS5 und interne Suche.
[Projektionsabnahme](index_projection_implementation.md),
[FTS5-Implementierung und Grenzen](content_fts_implementation.md).
[ADR](retrieval_indexing_adr.md) und [Implementierungsplan](../planning/c24_implementation_plan.md)
gehören dazu. Im Folgenden „muss“ bezeichnet die verbindlichen Abnahmekriterien;
HTTP und reale Vektor-/Hybridaktivierung bleiben geplante Folgearbeit.
[C24-04-A](content_vector_implementation.md) implementiert die optionale
ContentRecord-Vektorvariante ausschließlich mit Fake-Encoding/-Transport.
Bestehende [Contentmodelle](../../src/content_store/models.py), `Contract`, `Name`,
`Sha`, `Principal` und `ContentLocator` wiederverwenden. Neue Modelle in
`src/content_store/index_models.py`, ein gemeinsamer Projektor in
`src/content_store/index_projection.py`; Backendadapter unter `src/tools_rag/`.
Keine neue Source-/Evidence-/Locatorhierarchie.

## IndexRecord und Identitätsdomänen

Alle neuen Verträge: explizites `schema_version=1`, strenge Typen, extra forbid,
frozen und validierte Kopien verschachtelter Werte, keine implizite Schemaadoption.
`J` ist bestehendes `content_store.models.canonical` (sortierte Schlüssel, kompaktes
UTF-8, kein LF/NaN/Unicode-Normalisieren), `H` SHA256, `D` bestehendes
`model_discovery.cs50.deterministic_id`. Hashwerte sind 64 lowercase Hexzeichen.

`IndexRecord` besteht aus `body: IndexRecordBody`, `index_record_id`,
`generation_id`, `build_id`, `schema_version=1`. Bei reiner C24-02-Projektion sind
beide Kontextfelder ausdrücklich **null**; weder Build noch aktive Generation
werden erfunden. Ein späterer Builder muss beide gemeinsam binden. Bodyfelder sind **alle** Pflicht;
nullable ist nur ausdrücklich unten so markiert:

| Feld | Typ / Invariante |
| --- | --- |
| `schema_version`, `index_schema` | Literal 1, Literal `content_index_record_v1` |
| `source_id`, `source_version_id`, `parsed_version_id` | Bestehende identische ContentStore-IDs, keine Rekonstruktion aus Dateinamen |
| `course_id` | CourseId der Source, kein ACLnachweis |
| `block_id`, `block_order` | ContentBlock-ID und nichtnegative Originalreihenfolge |
| `content_type`, `original_type` | Vorhandener Blocktyp bzw. unveränderte Typbezeichnung |
| `aggregation_role` | Literal `primary`; Referenzblöcke erzeugen keine Records |
| `origin_pointer` | Exakter `ContentBlock.payload_pointer`, JSON Pointer, kein Hostpfad |
| `text_sha256`, `text_length` | SHA über **gesamten** Originalblock UTF-8; Länge in Codepoints |
| `start`, `end`, `offset_unit` | Strict int, `0 <= start < end <= text_length`, Literal `unicode_codepoint` |
| `search_text`, `search_text_sha256` | `block.text[start:end]` und SHA seiner UTF-8-Bytes; in v1 **keine** Textableitung/Normierung |
| `locators` | Vollständige unveränderte tuple[ContentLocator, ...]; Raw-SHAs gehören zum SourceVersionmanifest |
| `parser_config_id`, `parser_fingerprint` | Bestehende Config-ID und `H(J(ParserConfiguration.model_dump(mode="json")))` |
| `payload_sha256`, `projection_sha256` | Bestehende Parsed-Artefakthashes, keine Hashes redigierter HTTPprojektionen |
| `projection_policy_id` | `D("content_index_policy_v1", H(J(policy)))` für vollständig fixierte Projektions-/Fensterregeln |

`index_record_id = D("content_index_record_v1", H(J(body)))`.
Der Body enthält keine Buildzeit, Actor-/ACLrevision, Dateipfade, Zufallswerte oder
Backend-/Generationdaten. Gleiches unverändertes Original plus gleicher Policy
liefert dieselben fachlichen Records, auch nach Rebuild. Parser-/Projektion-/
Policyänderungen erzeugen neue IDs; globale Deduplikation nach Textsha ist verboten.
Derselbe Text in zwei Sources überträgt weder Identität noch Rechte.

`build_id` ist ein neuer UUID4-Hexstring pro explizitem Versuch (kein Fachdatenkey).
`generation_id = D("content_index_generation_v1", H(J(generation_basis)))`.
Basis: schema_version=1, policy_id, **sortierte** selection mit Source-/SourceVersion-/
Parsed-IDs, Payload-/Projektions-/Parserfingerprints, record_set_sha256 und
sortierte Backendkonfigurationen einschließlich SQLite-/Tokenizer-/Scoreversion
bzw. Embedding-/Collectionvertrag. Build-ID und Revisionen sind ausgeschlossen.
Kein Selbsthashkreis: record_set_sha256 bezieht sich ausschließlich auf Bodies
und deren Record-IDs, niemals auf generation_id/build_id des Envelopes.

`record_set_sha256`: Records nach `index_record_id` sortieren; für jeden Record
UTF-8 von `J({index_record_id, body})` als `decimal_byte_length + b":" + bytes`
in einen SHA256-Stream schreiben. Keine sortierabhängigen Dictreprs oder
plattformabhängigen Zeilenenden. Duplikate sind Fehler, kein stilles DISTINCT.

### Exaktes Ankerbeispiel

Synthetisch, keine Kursquelle oder Goldreferenz: Blocktext `A😀é\n` besteht aus
fünf Unicode-Codepoints (das letzte sichtbare Zeichen vor LF ist e plus Combining
Acute). `start=1,end=4` ergibt `😀é`, UTF-16-Indizes wären andere Werte.
Der Blockhash bindet den ganzen Text; Suchtexthash nur das Fenster. Eine NFC-
Umwandlung zu `é` verändert Hash und Offsets und ist deshalb ausgeschlossen.

<!-- c24-anchor:start -->
```json
{
  "origin": "synthetic_documentation_only",
  "block_text": "A😀é\n",
  "text_sha256": "d1f47a1411a08ac3d7580161ea02159fbda06c7a49b96b36b6b387bc47dd4bb1",
  "text_length": 5,
  "start": 1,
  "end": 4,
  "offset_unit": "unicode_codepoint",
  "search_text": "😀é",
  "search_text_sha256": "865ca477c528c065fc12374110af1e6381070fa2fc10782205b8fac3a2fb9351"
}
```
<!-- c24-anchor:end -->

Öffentlicher Textanker ist immer
`(parsed_version_id, block_id, text_sha256, start, end)` plus offset_unit.
`origin_pointer` referenziert die Payload; Raw-/Seiten-/DOM-/Zeilen-/Zeitbezüge
kommen aus **demselben** Locator. Kein geratenes Mapping von Tokenpositionen,
UTF-8-Bytes, Graphemen oder UTF-16 auf diese Anker.

## Aggregation und Chunking

Policy v1: `selection=content_primary_v1`, `max_codepoints=2000` (Default, explizit 1–2000 konfigurierbar),
`overlap_codepoints=0`, `boundary=block`, `normalization=none`,
`chapter_context=metadata_only`, `empty_text=reference_only`.
Alternative konfigurierte Policy v1 darf ausschließlich overlap=128 verwenden;
die Fenstergröße muss größer als der Overlap sein; sämtliche Policyparameter sind identitätsrelevant. Keine satz-/tokenabhängige
Segmentierung im lexikalischen Projektor und keine künstlichen Headings im Text.

1. Parsed-Payload/Projektion und alle gebundenen Bytes gemäß Store prüfen;
   `ContentBlock` und gespeicherte `aggregation_units` lesen. Materialunits gegen
   Block-ID/Originalfenster/Hash und vorhandene exclusions/alternative_views prüfen.
   SRTunits über ihren eindeutigen payload_pointer einem gespeicherten Cueblock
   zuordnen; keine MaterialUnit-ID für SRT erfinden. Beim SRT-Abgleich dieselbe
   vorhandene C23-Finalisierung berücksichtigen: projiziertes `cue:{seg_id}` wird
   zu `D("content_cue_v1", parsed_version_id, str(original_segment_id))`, wie in
   `publication.py` und der Integritätsprüfung in `operations.py`. Danach müssen
   Blocks/SQLprojektion mit der unveränderlichen Projektion übereinstimmen; kein
   neues IDschema und keine Mutation der gespeicherten Projektionsbytes.
2. Nur `aggregation_role=primary` mit ausdrücklich gespeicherter Unitdeckung
   aufnehmen. Unstimmige Rolle/Auswahl sperrt die **ganze** betroffene Projektion.
   Nicht erneut `prepare_material_handoff`/Rawparser starten. Für synthetische
   Teststoreprojektionen ohne B-Auswahldaten nur einen ausdrücklich markierten
   separaten Testadapter verwenden; niemals in content-Purpose promoten.
3. Unitintervalle je Block sortieren; Überlappung/Duplikat ist Fehler. Benachbarte
   Intervalle werden zur Deckungsprüfung vereinigt; echte Lücken nie überbrücken.
   Innerhalb jedes gedeckten Bereichs [a,b): Fensterstart a; end=min(start+max_codepoints,b),
   nächster start=end-overlap, **nur wenn end<b**. Kein Nullfenster und keine
   Schleife hinter dem letzten Fenster. Unveränderte SRT-Cuegrenzen/Blockgrenzen
   bleiben hart; keine Vermischung zweier Kapitel, Seitenblöcke oder Cues.
4. Sortierung bleibt `(parsed_version_id, block_order, start, index_record_id)`;
   chapter_path und alle Ursprungslocatoren bleiben erhalten. Nur leere oder rein
   whitespacehaltige Fenster sind nicht textindexierbar und werden separat gezählt.
   Sie bleiben in den Originalblöcken; Coveragereport weist diese Intervalle aus.

| Inhalt auf aktuellem B/C10-Stand | Verbindliche Auswahl |
| --- | --- |
| Heading/Absatz/nichtleere Liste/Code | Originaltext einmal, vorgegebene Auswahl; Einrückung, Zeilennummern, CR/LF und Unicode bleiben |
| HTMLtable mit Text | Tableblock einmal; `data.rows`/Zellen nicht zusätzlich serialisieren. Leere Texttabelle bleibt Referenz |
| PDFtable | `geometric_table_projection`, nicht primär. Keine nachträgliche Zell-/Textpromotion |
| TOC/Links/leere Listencontainer | reference_projection/structure, keine zusätzlichen Textrecords |
| `code_view`, alternative_views | Nur Referenzen auf vorhandene Struktur; Originalcode mit Nummern bleibt Suchtext. Kein zweiter Record aus der Ansicht |
| Formel/math, Bild, unknown_block | Auf dieser Basis non_text_reference; kein Formel-/OCR-/Captiontext automatisch erzeugen |
| SRT | Je gespeicherten Cue primäre Texte und echte Cuezeiten; Originalseg_id erhalten |
| TXT/andere Unknown-Time-Daten | Nur wenn tatsächlich geprüfte Storepublikation existiert. C23-05 repariert lokale TXTimporte, liefert heute **keinen** allgemeinen TXT-Storeadapter |

Formeln/Tabellen/Bilder bleiben über ihre ContentBlock-/Locator-/Strukturrouten
referenzierbar. Ihre fehlende Textindexierbarkeit wird pro Grund/Typ im privaten
Buildreport gezählt. Eine spätere zusätzliche strukturierte Suchprojektion braucht
eigene Policyversion, geprüfte Textabbildung und Evaluation; keine stille Erweiterung
von primary. Ein zukünftiger primary-Formelblock würde seinen expliziten Typ und
seinen Originaltext behalten, nicht als mathematisch verifiziert gelten.

Bei Overlap bleibt jedes Fenster ein Originalslice. Wiederherstellung je Block:
nach start sortieren, überlappende Codepoints auf Gleichheit prüfen und nur noch
nicht gedeckte Endteile anfügen. Lücken/fehlende Whitespacefenster explizit aus dem
autoritativen Original ergänzen; Suchtreffer sind kein vollständiges Archiv.
Keine Textnormalisierung und kein nachträgliches Dedup über verschiedene Sources.

Medienzeiten: known behält unverändert start/end des berührten Cues, auch für
Teilslices; keine lineare Interpolation. unknown/not_applicable bleibt null/null.
Überlappende Originalcues bleiben überlappend. Line-/BBox-/DOMlocatoren eines
Blocks sind konservative Ursprungsbelege, keine behauptete Geometrie einzelner
Suchzeichen. Nicht belegte Seiten-/Zeilen-/Chapterwerte bleiben unbekannt.

## Generation und Rebuild

`IndexSelection` ist ein expliziter versionierter Operatorauftrag: konkrete
sortierte Source-/SourceVersion-/Parsed-IDs und erlaubte Backends, kein freier
Hostpfad, kein `latest` per Namensheuristik. Es gibt im ContentStore keinen
allgemeinen Latest-Pointer. Alte veröffentlichte Versionen sind nur dann gültig,
wenn bewusst selektiert; eine neue Publikation ersetzt die Auswahl nicht heimlich.
Eine Suche verwendet ausschließlich die aktuelle aktivierte Auswahl und niemals
eine frühere Generation. Fehlende/abweichende selektierte IDs sperren Aktivierung.

`BuildReceipt` v1 (privat) bindet build_id, generation_id, selection/policyhash,
Actor.subject, geprüfte Source-ACLrevisionen, Contentpublication-/Collectionrevision,
Implementierungsrevision, UTC-Beginn/Ende, Backendfingerprints, Recordanzahl/-sethash,
Referenz-/Exklusionszahlen, Dateien mit SHA/Größe und Prüf-/Fehlercodes. Keine
Tokens/Originalvolltexte/private Receipts im Jobresult. Immutable Dateien liegen unter `generations/<generation_id>/<build_id>/`;
`active.json` enthält intern schema_version=1, generation_id, build_id und
manifest_sha256. Ein gleiches fachliches Generationsresultat kann physisch andere
SQLitebytes haben; jeder konkrete Build hat daher eigene unveränderliche Datei-/
Manifesthashes. No-op-Versuche referenzieren den zuvor aktivierten Build und
archivieren nur ihren neuen Attemptbeleg. Manifest wird zuletzt
exklusiv veröffentlicht; Hash belegt Integrität, keine Signatur gegen gleiche UID.

| Zustand | Zulässige Aktion / sichtbare Generation |
| --- | --- |
| preparing | Neuer eigener privater Stagingroot außerhalb Repo/Content-/Jobroot, bisherige aktive Generation bleibt |
| building | Ein Projektor erzeugt Bodies, Backends konsumieren dieselben Records; keine sichtbaren Teilergebnisse |
| verified | Vollständige Selection/Deckung, Record-IDs/Hashes, Referenzcounts, FKs/SQLite-/FTS-integrity-check, Backendreadback und Manifest erneut prüfen |
| active | Erst nach erneuter Sourceownership/Course-/ACL-/Status-/Hashprüfung alle Dateien fsync, Directory fsync, active.json per same-filesystem atomic replace unter Catalog-Exklusivlock; parent fsync |
| failed/interrupted/cancelled | Nur fester Fehlercode, keine Aktivierung; explizit neuer Versuch, keine Adoption unvollständiger fremder Stagingdaten |
| retired | Nur private frühere Generation, keine Query/Fallback/Cursorfortsetzung; Entfernen ausschließlich separater expliziter Retentionauftrag |

Aktivierung verwendet CAS auf den vollständigen vorherigen Activepointerhash und auf den exakt
geprüften Contentrevisionstoken. Gleiches Generationsergebnis darf als no-op mit
neuem Buildbeleg enden; kein Überschreiben bestehender immutable Generationsfiles.
Bei Crash nach atomic replace und vor Response liest der Wiederholer active.json,
validiert Manifest/Hashes und liefert already_active. Unklares Activefile, kaputte
Generation oder unbekannte Schemas: Unavailable, kein „besteht irgendwie“-Fallback.
Ein Engine-/Tokenizerwechsel erzwingt neue Backendkonfiguration und Generation.
Rebuild benötigt nur verifizierte gespeicherte Daten, niemals Reparse/Extraktion.

Initial keine automatische Resume-Engine für teilweise gebaute Indexfiles:
abgebrochener Versuch bleibt belegt, neuer expliziter Attempt baut neu. C16-/C18-
Jobreceipt bleibt Attemptnachweis. Eine später beschlossene Resumeoptimierung muss
dieselben Hash-/Closuregates erfüllen, ohne Content-Recovery als Indexqueue zu nutzen.

Lockordnung bei Query/Aktivierung: **Indexcatalog → Contentmaintenance → Content-DB
→ Sourceindexhandle**, alle nonblocking, innerhalb der vorhandenen Storegrenzen.
Catalog shared pinnt aktive Generation und hält Retention fern; Content shared
verhindert Rechte-/Statusänderung bis zur Antwort. Builder hält beim langen
Staging/FTSaufbau keine Content-/Cataloglocks. Export unter Contentsharedlocks in
bounded privaten Snapshot; danach Inputsnapshot und Liveversion erneut prüfen.
Zur Aktivierung Locks in obiger Reihenfolge neu nehmen; kein Upgrade von shared
auf exclusive. Kein Code unter Contentlock ruft Catalog-/Joblocks auf. Bestehende
C22-Fence liegt bei späterem Verbund immer außen. Keine umgekehrte Verschachtelung.

Buildberechtigung: Operator plus **Ownership und Course-Scope jeder selektierten
Source**, wie bestehende Writes; niemals globaler Administrator oder Readerexport
als Publishrecht. Entzogene Berechtigung beim finalen Check sperrt Aktivierung.
Neu grantberechtigte Leser können danach dieselbe aktive Sourcepartition benutzen;
ACLrevision in Receipt ist historischer Prüfbeleg und kein künftiges Readrecht.

## Retrieval und Autorisierung

Interne Fassade `ContentRetrieval` aus `src.tools_rag.content_vectors`:
lexical standardmäßig, vector optional als ausdrücklich synthetische A-Ausführung;
hybrid bleibt gesperrt. Ohne Vektoradapter funktioniert lexical unabhängig.

```python
with retrieval.search(
    query, actor=principal, course_id=None, source_ids=None,
    content_types=None, method="lexical", limit=20, cursor=None,
) as page:
    bounded_serialize(page)  # geprüfte DTOs; Locks bis Abschluss/Abbruch
```

Contextmanager pinnt Generation und autorisierten Snapshot bis zur Serialisierung.
C24-03 muss für HTTP die Guard-Lebensdauer bis zum Ende der begrenzten Übertragung
verlängern wie C23-04; kein ungeschütztes Lösen vor Headerausgabe. Keine Netzwerk-
oder Benutzercallbacks während Index-/Contentwrites, keine Hintergrundsuche.

Query v1: nichtleerer String, höchstens 512 Codepoints/2 KiB UTF-8; Split an
Unicodewhitespace, höchstens acht Suchterme, je höchstens 64 Codepoints.
Jeder Term wird als **literale FTSphrase** mit verdoppelten Quotes codiert;
Verknüpfung ausschließlich AND. Keine freien MATCH-Ausdrücke, Wildcards, NEAR,
Spalten-/SQLsyntax oder Queryexpansion. Parametergebundene SQLwerte. Satzzeichen
werden nicht eigenmächtig entfernt; keine Tokens nach FTSanalyse bedeutet leeres
Ergebnis. Tokens/Tokenpositionen ändern nie die Originalanker. Eine Query kann
wegen FTS-Tokenisierung `x+y` und `x-y` nicht semantisch unterscheiden.

`source_ids`: null oder 1–32 unique IDs, `content_types`: null oder eindeutige
vorhandene Typen; limit strict int 1–100. Filter werden vor Suche mit live Source-
Ownership/Grants und Course-Scope geschnitten. Fremde/unbekannte IDs werden gleich
behandelt und erscheinen weder in Fehlern noch Zählern. Nullfilter kann höchstens
32 **erlaubte** aktive Sources durchsuchen; darüber `scope_required` ohne Count,
Aufrufer soll einen engeren Course-/Sourcefilter wählen. Kein stiller Top-32-Cut.
Nicht erlaubte Sources zählen nicht gegen dieses Limit und werden nicht geöffnet.

Innerhalb Snapshot:

1. Actor über `checked_actor` validieren; Store root, aktive Generation und Cursor
   prüfen. Erlaubte Sources aus aktuellen Storetabellen ableiten, vor Candidate-
   Limits/Ranking. Indexseitige ACL-/Ownerfelder sind ausdrücklich unzulässig.
2. Jede erlaubte selektierte Sourcepartition vollständig gegen aktuelle Source-/
   SourceVersion-/Parsed-/Artefaktzustände und gebundene Fingerprints prüfen.
   Alle selektierten Versionen müssen sichtbar und vollständig hashgeprüft sein.
   Statusentzug macht die Partition stale; keine Scores aus ihrem früheren Inhalt.
   Unterschiedliche globale Contentrevision allein sperrt eine neue erste Seite
   nicht, wenn die angefragte Auswahl vollständig unverändert gültig bleibt.
3. Suche nur in diesen Sourcepartitionen; Score/Rang nur aus erlaubten Partitionen.
   Contenttypfilter vor Ranking. Kandidaten anhand exakter IDs/Anker/Blockhashes
   aus demselben Content-Snapshot hydrieren, nie Indexsnippet blind ausgeben.
4. Gleichheit der indexierten Slices/Locatoren/Fingerprints erneut prüfen, öffentlich
   über vorhandene `read_views.locators/route/public_url` redigieren. Body-/Raw-
   Provenienz bleibt intern; `original_source_checked` eines Pilottreffers genügt
   nicht als Content-ACL. Bytefehler ohne gesetzte Quarantäne: Unavailable, keine
   Reparatur oder heuristische Teilfreigabe.

Erlaubte Source mit ungültiger Partition ergibt `stale_index` ohne Source-/
Versionsdetails, **keine erfolgreiche Teilseite**. Nicht berechtigte stale Sources
beeinflussen Antwort nicht. Nicht selektierte erlaubte Sources sind „nicht in der
Suchauswahl“, nicht „beweisbar leer“. Authentifizierter Status auf den erlaubten
Scope begrenzen; keine globalen Generationcounts oder fremden Bestandszahlen.

### SearchHit und SearchPage

`SearchHit` v1: schema_version=1; index_record_id; source_id/source_version_id/parsed_version_id;
block_id/content_type; `anchor` wie oben; `locators` als vorhandene redigierte
LocatorDTOs; `excerpt: TextWindow`; method (`lexical`, `vector`, `hybrid`);
`components` mit backend/sourcepartition, raw_score, score_schema und direction;
ranking_score/ranking_schema; opake index_generation; Content-Text-/Strukturrouten.
Kein Owner-/Grant-/Autorisierungsstatus, privater Receipt-/Hostpfad, freies metadata
oder Vollpayload. Ein Source-lokaler Rohscore muss seinen Partitionbezug behalten.

Excerpt ist der erste Bereich `[record.start, min(record.end, record.start+512))`
aus dem aktuellen Originalblock, höchstens 512 Codepoints; kann den Queryterm bei
langen Records nicht zeigen. Es ist keine behauptete genaue Matchgeometrie.
`TextWindow.text_sha256` bleibt der vollständige Blockhash, nicht Excerpthash.
Große Locatorlisten analog C23: null + locators_in_structure + feste structure_route,
kein Abschneiden. Texte enthalten keine HTMLhighlight-Tags und sind in C25 als
Text zu rendern. Pfadähnliche Strings **im Originalcode/Text** bleiben Originalinhalt;
Metadatenredigierung ist kein beliebiges Entfernen fachlicher Textzeichen.

Rawscore lexical: endliches `sqlite_fts5_bm25_v1`, lower_is_better, eine Textspalte,
Gewicht 1.0, Sourcepartition. Vector: endlicher `cosine_l2_v1`, higher_is_better,
fixierte Modellkonfiguration, keine Wahrscheinlichkeit. Finale Sortierung nach
ranking_score DESC, index_record_id ASC. RRF-Konstanten und Scope siehe
[ADR](retrieval_indexing_adr.md#lexikalischer-adapter-und-scores).
Überlappende Fenster bleiben eigenständige Anker/Records; keine nachträgliche
Merge-/Dedupverschiebung über Seiten. Evaluation fasst sie separat zu Goldzielen
zusammen. UI darf gleiche Blöcke gruppieren, darf dabei Ranking/Anker nicht erfinden.

`SearchPage` v1: schema_version=1; items (vollständige SearchHits), next_cursor nullable,
index_generation (domainmarkierter HMAC der internen ID), ranking_schema,
`selection_scope="explicit_active_selection"`. Keine total_count, Existenceflags,
rohen globalen Revisionen oder fremden Treffer-/Indexzahlen. Generationreferenz
ist opak und kein Downloadpfad; Source-/Backendkomponenten enthalten nur erlaubte IDs.

### Paging, Fehler und Ressourcen

Cursor nutzt C23s HMAC-Prinzip mit **eigener Domain und eigenem Schema**, keinen
wiederverwendbaren Content-Cursor. Bindet Actor.subject/role/sorted courses,
kanonischen Query-/Filter-/Limit-/Methodfingerprint, opake Generation, Snapshot-
HMAC (publication_seq/collection_revision), Ergebnissatzdigest, letzte Position
und Ablaufzeit. Keine Querytexte oder ablesbaren globalen Zähler im Cursor.
Maximal 1.600 Zeichen, HMAC-SHA256, kanonisches Base64url, TTL 5 Minuten.
Vor jeder Folgeseite aktuelle Berechtigungen erneut prüfen. Jegliche Revision- oder
Generationänderung: snapshot_changed ohne Items, Neustart erste Seite. Ungültige
Signatur/Actor-/Querybindung: invalid_cursor. Cursor gewährt niemals Rechte.

V1 berechnet deterministisch den **vollständigen begrenzten** Ergebnissatz erneut;
kein ungesicherter Scoreoffset oder zweite Resultqueue. Für jeden erlaubten
Sourceshard höchstens 1.000 passende Records und insgesamt höchstens 1.000;
`LIMIT 1001` erkennt Überschreitung, dann `query_too_broad` ohne Count/Teilergebnisse.
RRF arbeitet erst auf vollständigen erlaubten Listen; keine versteckte Top-k-
Approximation. Matchreihenfolge pro Source ist vollständig fixiert. Keine Requests
an Qdrant über diesen Rahmen hinaus; dort konfigurierten Timeout zusätzlich binden.

| Grenze | Festes v1-Verhalten |
| --- | --- |
| Query / Filter / Seite | Obige 512 CP/2 KiB/8 Terme, 32 Sources, 100 Hits; 256 KiB komplette JSONantwort, kleinere vollständige Seite plus Cursor wenn nötig |
| Liveprüfung | Max. 128 MiB gelesene/verifizierte Bytes je Request; keine ungeprüfte Cacheabkürzung, Überschreitung unavailable |
| Indexgeneration | Max. 128 Sources, 200.000 Records, 256 MiB Suchtext, 1 GiB Indexfiles; neues Stagingbudget zusätzlich einplanen |
| Build | Höchstens 2 GiB Staging/aktive+neue Dateienbudget, 15 Minuten explizite Jobdeadline; Abbruch ohne Aktivierung |
| SQLite / Handles | Progresshandler + monotone Gesamtabfragefrist 2 s ab Querybeginn, kurze nichtblockierende Locks; keine Extension-/ATTACH-/Client-SQLrechte |
| Antwort / Parallelität | Gesamtresponsefrist 5 s, max. zwei aktive Suchen pro Prozess, danach Busy; Socketlimits aus C23 zusätzlich |
| Ressourcenfehler | Festes unavailable/Busy, keine unbegrenzten Retries; reale Durchsatz-/Lastabnahme C26 |

Diese konservativen Grenzen können gültige große Korpora abweisen. Sie sind ein
expliziter Anfangsvertrag, keine behauptete Skalierungsfreigabe. Nachweislich
nicht fristgerecht abbruchfähige Backendoperationen müssen isoliert/abgewiesen
werden; ein Timeout darf keinen weiterlaufenden Hintergrundworker hinterlassen.

Interne feste Fehlercodes: unauthenticated; invalid_parameter/invalid_cursor;
snapshot_changed; scope_required/query_too_broad; stale_index; unavailable/Busy.
Die spätere C24-03-HTTPabbildung folgt C23 (401/400/409/503), scoped Query-/Scope-
Limits 400; keine neue Route in C24-01. Explizite einzelne fremde/fehlende
Contentobjekte behalten 404-Gleichbehandlung; Search mit leerem erlaubtem Scope
liefert leere items, keine Information über die abgefragten fremden IDs.
Keine Score-/Snippet-/Candidatecaches zwischen Actors; keine globalen Querycounts.
