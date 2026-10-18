# C24-02: Deterministische ContentStore-Indexprojektion

18.10.2026 · Basis `master` `2d7a813ed8c668b3d73dd62119d3ca24330d76cb`
nach Merge von [C24-01/#83](https://github.com/rf-data/Personal_Assistant/pull/83).
Die frühere [77-Fälle-Vorprüfung](../planning/c24_02_preflight.md) bleibt historisch.
Maßgeblich: [ADR](retrieval_indexing_adr.md), [Recordvertrag](index_record_contract.md),
[Umsetzungsplan](../planning/c24_implementation_plan.md),
[ContentStore](content_store_implementation.md), [C23-06](../cs50/evaluation/c23_real_material_evaluation.md).

## Implementiert und ausdrücklich nicht implementiert

Implementiert sind `index_models.py` (strenge versionierte Modelle, Fingerprints,
Recordset-/Resultdigests) und `index_projection.py` (ein vollständiger scoped
Snapshot und deterministische Auswahl/Fenster). `ContentStore` erhält genau eine
kleine delegierende Lesemethode. Keine DDLänderung oder Migration.

Bewusst außerhalb dieses PR: FTS5, Qdrant, Embeddings, Ranking, Indexfiles oder
aktive Generationen, HTTPsearch, UI, Jobs/Scheduler, Downloads und Reparse. Diese
Stufe entspricht C24-02-A des offiziellen Plans; die spätere Backend-/Rebuild-
und Retrievalintegration benötigt eigene PRs. Keine fachliche Realmaterialabnahme.

## Aufruf und Ein-/Ausgabe

```python
from src.content_store.store import ContentStore
from src.content_store.index_models import IndexProjectionConfig

store = ContentStore(explicit_existing_private_root)  # read-only
result = store.project_content_for_index(
    existing_parsed_version_id,
    actor=authenticated_principal,
    config=IndexProjectionConfig(schema_version=1, max_codepoints=2000,
                                 overlap_codepoints=0),
)
# Identische Funktion auch direkt in src.content_store.index_projection:
# project_content_for_index(store, parsed_version_id, *, actor, config=None)
```

Actor ist ein vorhandener `Principal`, kein Subjectstring oder selbstdeklariertes
`verified`-Dictionary. Ausschließlich ein bereits initialisierter ContentStore und
eine konkrete publizierte ParsedVersion. Keine Suche nach Dateien, keine freien
Payload-/Receiptpfade. Die Funktion schreibt weder Store noch Outputdateien.
Ein neues CLI-/No-Overwrite-Dateiformat wird deshalb nicht eingeführt; Aufrufer
können das validierte Ergebnis ausdrücklich in eigenem Testcode serialisieren.

`IndexProjectionResult(schema_version=1, body, digest)` bindet den kanonischen Body.
Body enthält projection_version, status=projected, usage, source_origin,
Source-/SourceVersion-/Parsed-/Parseridentität, Originalpayload-/Projektionshash,
Konfiguration/-fingerprint, Record-/Ausschlusszahlen, error_count=0,
record_set_sha256, vollständige Records und maschinenlesbare Exclusions.
`usage=verified_content` bedeutet technisch geprüfte Storepublikation und keine
fachliche Bestätigung; synthetische B-Bundles behalten source_origin=synthetic.
Es gibt keinen erfolgreichen Teilreport mit Fehlern. Fehler liefern bestehende
redigierte Storeexceptions oder `IndexProjectionError.reason`, keine Teilausgabe.

IndexRecord folgt dem C24-01-Bodyvertrag. Nur der spätere Buildkontext ist in
Projektionsausgaben `generation_id=null,build_id=null`. Beide werden von einem
zukünftigen Builder gemeinsam gesetzt; fachliche Record-ID und Recordsethash
bleiben davon unabhängig. Vorhandene IndexRecord-Dictionaries sind keine Capability
zum Import oder zur späteren Rechteumgehung.

## Datenfluss, Integrität und Autorisierung

1. Config/Actor validiert kopieren, Storepurpose prüfen. Normale API akzeptiert
   ausschließlich content-Purpose; synthetic_test bleibt gesperrt.
2. Unter bestehendem Maintenance-Sharedlock und **einer** DB-Sharedlock-Transaktion
   Course plus Owner/read-Grant autorisieren. Source-/SourceVersion-/Parsed-/Parser-
   und Dokumentidentität samt SQL-/Modellbezug vergleichen, Status prüfen.
3. Sourcegebundene Rawreservations-/Manifestrefs, Payload, Projektion, Binding und
   sämtliche versiongebundenen archivierten Artefakte auf Katalogstatus, Größe,
   private reguläre Inodes und SHA prüfen. Cache nur innerhalb dieses Aufrufs;
   unterschiedliche SHAbytes werden nicht als gleich akzeptiert. Kein neuer
   ungeprüfter Langzeitcache. Aktuelle Quarantäne/Tombstones sperren die Ausgabe.
4. Alle Blöcke, nicht nur 100, lesen. Ihre ID/Reihenfolge/Texthashes und vollständige
   SQLlocatoren gegen unveränderliche Projektion prüfen. SRT-Cue-IDfinalisierung
   entspricht exakt bestehendem `content_cue_v1` in C23-Publikation/Integrität.
5. Bereits gespeicherte Handoff-/Normalized-Modelle validieren, C10-Auswahldaten
   vergleichen. Das reine Handoffmodell prüft vorhandene MaterialUnits mit den
   bestehenden Mappingregeln; **kein** prepare_material_handoff-/Rawparseraufruf.
   SRT liest vorhandene Transcriptmodelle/Cuepointer und bestehendes Binding;
   Raw-SRT wird gehasht, nicht erneut geparst.
6. Originalfenster projizieren, Typed Record-/Resultmanifest validieren, dann Locks
   lösen. Der Snapshot ist eine technische Beobachtung zum Aufrufzeitpunkt.
   Grantänderungen während der Projektion erhalten Busy. Spätere Builds/Suchen
   müssen Source-/Course-/Grant-/Status-/Hashregeln **erneut** live prüfen.

Die ursprüngliche Arbeitsbundlewurzel wird nach Storepublikation nicht benötigt;
keine historischen Pfade werden korrigiert. DB-/Payload-/Receipt-/Rawbytes bleiben
unverändert. Neue Scoped-Exportprüfung ergänzt die nicht vollständig paginierte
interne Blockliste; öffentliche redigierte HTTPpages werden nicht zu einem
vermeintlich atomaren privaten Snapshot zusammengesetzt.

## Aggregation, Fenster und Provenienz

Ein Projektor für alle späteren Backends, keine Chroma-/Transcript-Doppelpipeline.
Materialaggregation übernimmt exakt gespeicherte aggregation_units,
excluded_blocks und alternative_views; widersprüchliche Rollen/Units sperren die
Projektion. Originaltext bleibt kanonisch: kein strip, NFC, Headingpräfix,
Tabellenzellenserializer oder code_view-Ersatz. `.strip()` wird ausschließlich zur
Klassifikation rein leerer Suchfenster genutzt, niemals auf ausgegebenem Text.

Primäre HTMLtabellen höchstens einmal; PDFtabellen, TOC, Linkprojektionen, leere
Listencontainer und reference-only Formeln/Bilder nicht neu promoten. Alternative
Codeansichten liefern einen Ausschlussbeleg und keinen zweiten Textrecord.
SRT-Cues behalten Originalseg_id und überlappende bekannte Zeiten. Keine Zeit- oder
Geometrieinterpolation. Block-/Kapitelgrenzen bleiben hart. Alle ursprünglichen
Locatorwerte werden unverändert übernommen, sofern sichere Metadaten darstellbar
sind: DOM nur in der vorhandenen strukturierten HTMLpfadform; Hostpfade/unklare
beschreibende Locatorwerte werden ausdrücklich abgewiesen statt umgeschrieben.
Freies Block.data, Receipts, URLs, Parserparameter und private Pfade werden nicht
kopiert; Originaltext kann natürlich pfadähnlichen Code enthalten.

Konfiguration: max_codepoints strict 1–2000 (Default 2000), overlap 0 oder 128,
kleiner als max_codepoints; alle übrigen Policywerte fix. Dies konkretisiert die
im Auftrag verlangte konfigurierbare maximale Größe, kein neuer Chunkalgorithmus.
Benachbarte gespeicherte Units je Block werden auf korrekte Deckung geprüft und
zu zusammenhängenden Bereichen vereinigt. Überschneidungen/Duplikate sind Fehler;
Lücken werden nicht überbrückt. Fenster end=min(start+max, stop), bei weiterem
Fenster start=end-overlap. Halb offene Python-/Unicode-Codepointanker, niemals
UTF-16-, Byte- oder Tokenoffsets. Whitespacefenster bleiben explizit ausgeschlossen.

Exclusions nennen block_id/block_order und reason, gegebenenfalls start/end:
C10-Gründe table_of_contents/reference_projection/geometric_table_projection/
list_structure/non_text_reference sowie alternative_view, empty_text und
whitespace_window. Gezählt werden Ausschlussereignisse: ein Codeblock kann einen
primären Record **und** einen alternative_view-Beleg besitzen. Keine erfundene
Zahl vermeintlicher Tabellenzellen oder nicht vorhandener Formeln.

## Identitäten, Manifest und Fehlergrenzen

Bestehende canonical/fingerprint/deterministic_id direkt wiederverwendet.
IndexRecord-ID bindet `content_index_record_v1` und SHA des vollständigen Body;
Body bindet Source-/Parsed-/Blockidentität, ganzen Blockhash, Originalslice/-hash,
Offsets, Locatoren, Parserconfig/-fingerprint, Originalpayload-/Projektionshash
und vollständige Projektionspolicy. Kein Actor, Rootpfad, Zeitstempel, BuildUUID
oder Prozesszustand beeinflusst fachliche IDs. Andere SourceVersion oder Policy
liefert neue IDs, auch bei gleichem Text. Reihenfolge block_order/start/Record-ID.

Recordsethash: nach Record-ID sortiertes length-framed canonical JSON von
{index_record_id,body}, exakt wie im ADR. Resultdigest: SHA kanonischer Body,
kein Selbsthash. Bei gleichem Storezustand und gleicher Config sind komplette
Projektionsausgaben reproduzierbar. HMAC/Signatur/Authentizität gegen denselben
UID-Angreifer wird damit nicht behauptet.

Feste Grenzen: vorhandene 64-MiB-Artefakt-/JSON-/50.000-Block-Verträge; 128 MiB
aufruflokales Blob-/Runbelegbudget; maximal 20.000 gebundene Artefaktreferenzen;
200.000 Records, konservativ 32 MiB summiertes Record-JSON und abschließend
höchstens 64 MiB kanonisches Gesamtergebnis. Vor weiterem Record wird abgebrochen,
keine abschneidende „erfolgreiche“ Ausgabe. Keine Produktionslastfreigabe.

| Fehler | Verhalten |
| --- | --- |
| Forbidden / NotFound | Fehlender Actor/Course/Grant, falscher Storepurpose oder unsichtbarer Status; keine Daten als Fallback |
| IntegrityError / Unavailable / Busy | Vorhandene Blob-/DB-/WAL-/Fenceregeln; keine Reparatur, Retryschleife oder Quarantäneänderung |
| InvalidInput | Nicht typisierte/ungültige Config, ungültige Parameter; keine freien Dictionaryadapter |
| IndexProjectionError(snapshot_binding) | Source-/Version-/Parser-/Payload-/Belegkonflikt oder nicht validierbare gespeicherte Struktur |
| IndexProjectionError(block_binding) | SQLblock-/Texthash-/Locator-/Projektionswiderspruch |
| IndexProjectionError(aggregation_binding) | Ungültige/abweichende Units, Rollen, Ausschlüsse oder Ansichten |
| IndexProjectionError(unsupported_adapter) | Nicht unterstützter persistierter Adapter; keine heuristische Auswahl |
| IndexProjectionError(unsafe_metadata) | Nicht sicher repräsentierbare Metadaten; keine stillen Pfadänderungen |
| IndexProjectionError(projection_limit) | Explizites Ressourcenbudget überschritten; kein Teilresultat |

## Synthetische Tests und verbleibende Grenzen

`_testing.project_synthetic_for_index` ist ein ausdrücklich separater privater
Testadapter auf dauerhaft synthetic_test markierten Roots/Source-Namespace und
SyntheticPayload; keine normale API kann solche Daten promoten. Damit werden
Nullzeiten/TXTartige Texte und primäre Formeltypen ohne erfundenen produktiven
TXTadapter geprüft. Der aktuelle B-Store unterstützt weiterhin nur überprüfte
Material-/SRT-Bundles. Echte TXT-Contentpublikation bleibt Folgearbeit.

Das PDF-v2-Beispiel nutzt vorhandene synthetische Normalized-Verträge, keinen
nativen PDFparser. Reale CS50-SRTdateien wurden nicht gelesen/kopiert/migriert.
D06/D07, unabhängige Goldreferenzen, fachliche Parsing-/Retrievalqualität und
Produktionsfähigkeit bleiben offen. Zukünftige Suchausgaben benötigen zusätzlich
den redigierten C23-DTOvertrag und eine neue Liveprüfung, nicht dieses private
Projektionsmanifest als öffentlichen Download.

## Tatsächlich ausgeführte Prüfungen

Gemeinsames tatsächliches Präfix (Python 3.12.12, Pydantic 2.13.5,
System-Pytest 7.2.1, SQLite 3.50.4; keine Installation oder Synchronisierung):

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

Gemeinsame Abnahme mit diesem Präfix:

```sh
-q --disable-warnings -p no:cacheprovider \
 tests/test_content_index_projection.py tests/test_content_store_models.py \
 tests/test_content_store_adapters.py tests/test_content_store_store.py \
 tests/test_content_read_contracts.py tests/test_cs50_material_evaluation.py \
 --basetemp=/tmp/c2402-release
```

**200 passed / 0 failed / 0 skipped / 0 setup errors**, 152,30 s:
40 neue Projektionsfälle und 160 bestehende Fälle (25 Models, 49 Adapter,
34 Store, 14 Read, 38 C23-06). Danach wurde ausschließlich die explizite Auflösung
von Materialpointern nach Blockorder gehärtet und ein zusätzlicher Negativfall
aufgenommen. Der **gesamte** betroffene Projektorbereich erneut geprüft:

```sh
-q --disable-warnings -p no:cacheprovider tests/test_content_index_projection.py \
 --basetemp=/tmp/c2402-final-projector
```

**41 passed / 0 failed / 0 skipped / 0 setup errors**, 71,28 s.
Diese Läufe überlappen; kein ausgeführter 201er-Gesamtlauf wird behauptet.
Die abschließende 41er-Suite enthält alle Projektoränderungen. Store-/Testadapter-
Delegation und bestehende übrige Runtime wurden danach nicht verändert.

Nachgewiesen: B-geprüfte HTML/Code/PDF-v2-Bundles, Quelle/Version/Artefakte,
Codeeinrückung und CRLF, keine code_view-/PDFtable-/Formeldubletten, genaue
Unicode-/Combining-/Emojianker, konfigurierter Overlap und Wiederherstellung,
synthetische Nullzeiten, echte gespeicherte SRT-Cuezeiten und Überlappungen,
125 vollständige Blöcke, Wiederöffnung, Prozessneustart und identische Resultate
mit einer tatsächlichen separaten Kopie des Repositorycodes. Keine privaten
Materialien werden dabei kopiert. IDs/Hashes/manifeste, neue SourceVersion/Text,
Schema-/Configmanipulation, Rolle/Grant/Course und Widerruf, echte Locks mit Busy
für parallelen ACLwriter, Source-/Parsed-Tombstone und Quarantäne, beschädigte
Payload-/Projektions-/Handoff-/Binding-/Receiptbytes, SQLblock-/Texthash-/Locator-
und Pointerkonflikte, falsche/duplizierte Units, unzulässige Metadaten und Budget.
Dateiinventare von Originalbundle und Store vor/nach Projektion unverändert.

Entwicklungsläufe desselben Testmoduls mit obigem Präfix und je eigenem Basetemp:

| Basetemp | Pass / Fail / Skip / Setup | Dauer |
| --- | --- | --- |
| `/tmp/c2402-index-dev1` | 14 / 16 / 0 / 0 | 45,17 s |
| `/tmp/c2402-index-dev2` | 30 / 0 / 0 / 0 | 60,48 s |
| `/tmp/c2402-index-dev3` | 37 / 2 / 0 / 0 | 71,63 s |

Korrigierte neue Entwicklungsdefekte: ein nicht vorhandenes SQLfeld
processing_runs.parsed_version_id statt des bestehenden Run-JSONmodells sowie
zwei bei Testerweiterung fehlende Imports. Das sind keine Baselinefehler;
sie sind in den abschließenden grünen Läufen geprüft. Frühere Ruffbefunde zu
Imports/Formatierung ebenfalls korrigiert. Keine alten HTML-/Recoveryfehler
umklassifiziert: deren vollständige Module wurden hier nicht ausgeführt.

Ruff 0.16.0 `check` und `format --check` erfolgreich für genau fünf Pythondateien:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check src/content_store/index_models.py \
 src/content_store/index_projection.py src/content_store/store.py \
 src/content_store/_testing.py tests/test_content_index_projection.py
# Derselbe Dateiumfang mit format --check.
git diff --check
```

[Beispielmanifest](examples/index-projection.v1.json) stammt aus einer tatsächlichen
B-geprüften synthetischen Codepublikation, zwei Records, keine Ausschlüsse.
Digest `0dab31ec36850261139b2f9a4099e289e5bae0190401f23bdb9b27cca8ba7fe8`.
Keine aktive Generation und keine Hostroots im Ergebnis. Das
[Schema](examples/index-projection.schema.v1.json) entspricht exakt
IndexProjectionResult.model_json_schema(); der Ergebnisdigest wird vom Modell
bei Wiederöffnung validiert. Dokumentationsverweise, Schema und Beispiel erneut
geprüft. Keine erfundenen Realmaterial- oder Retrievalqualitätszahlen.

Eigene synthetische Testroots/Codekopien/Caches und temporärer Beispielstore werden
nach Abnahme entfernt; Laufprotokolle bleiben außerhalb des Repositories. Worktree
und Branch bleiben für den offenen C24-02-PR erhalten. Keine Bereinigung fremder
Worktrees, Originale, Umgebungsdateien, produktiver Datenbanken oder Venvs.
