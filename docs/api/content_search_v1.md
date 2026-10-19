# DEV-01 A / C24-03-B: autorisierte lexikalische Search-HTTP-API

19.10.2026. Implementierung auf Backend-master `e478520d259ad1342f5641828586c4cd2876114f`.
[Bestehendes Issue #114](https://github.com/rf-data/Personal_Assistant/issues/114),
[FTS5-Implementierung](../architecture/content_fts_implementation.md),
[Retrievalvertrag](../architecture/index_record_contract.md),
[Content-Lesevertrag](content_read_v1.md). Kein zweites Retrievalsystem.
Historische Integrationsvoraussetzung: Der A-Implementierungs-PR muss vor darauf
aufbauender UI-Integration gemergt werden. #124 ist inzwischen in Master
`79d800c` integriert. Kontrollierte Indexjobs bleiben ein eigenes
[DEV-01B-Paket](content_index_jobs_v1.md).

## Opt-in und tatsächliche Routen

C16 authentifiziert **vor** Routing und Konfigurationszugriff mit den vorhandenen
Identitäten. Eine Session erhält keine Rechte aus Requestfeldern/Proxy-Rollen.
Die vorhandenen Viewer-/Operatorrollen und aktuellen Course-/Owner-/Source-Grants
des ContentStores bleiben maßgeblich. Die Suche erlaubt keine Schreiboperation.

| Route | Methode | Ergebnis |
| --- | --- | --- |
| `/v1/content/search/capabilities` | GET | `SearchCapabilities`, auch bei deaktivierter Suche autorisiert lesbar |
| `/v1/content/search` | POST JSON | Unveränderte `SearchResultPage` aus C24-03 |

POST hält Querytexte aus URLs heraus. Weder Body noch Route werden geloggt.
Keine Queryparameter/Fragmente, freien Pfade, SQLstrings als Steuerfelder,
Methodenwahl oder Backendauswahl. Suchwörter werden vom bestehenden FTS5-Adapter
als begrenzte **literale** AND-Terme behandelt; keine freie MATCH-Syntax.
Ein deaktiviertes/fehlendes Capability liefert `enabled=false`; Suchaufrufe 503.
Ein fehlendes aktives Indexmanifest bei gültigem Root liefert dagegen 200,
`items=[]`, `index_generation=null`. Kein impliziter Rebuild oder Scan.

## Request und kompatible Response

```json
{"schema_version":1,"query":"hello","course_id":"cs50_python","source_ids":null,"content_types":["code"],"limit":20,"cursor":null}
```

`SearchRequest` verlangt explizit die ganzzahlige Version 1. Extra-Felder,
doppelte JSONkeys, nichtendliche Zahlen und fehlerhaftes UTF-8 werden abgewiesen.
Query bleibt exakt erhalten, ohne NFC-/Whitespace-/Codeänderung. Grenzen:
512 Codepoints / 2.048 UTF-8-Bytes, 1–8 whitespacegetrennte Terme à höchstens
64 Codepoints, 1–100 Treffer je Seite (Default 20). Optional: bestehende Course-ID,
1–32 eindeutige Source-IDs, 1–9 eindeutige Contenttypen des internen Vertrags.
Cursor höchstens 1.600 URLsafe-Zeichen. Body höchstens 32.768 Bytes, Antwort
höchstens 262.144 Bytes. Die strengeren internen Ressourcenlimits bleiben erhalten.

Responses verwenden direkt die vorhandenen
[`SearchResultPage`/`SearchHit`](../../src/tools_rag/content_index_models.py),
keine parallelen Treffer- oder Locatorobjekte. Jeder Treffer enthält Source-,
SourceVersion-, ParsedVersion-, Block- und IndexRecord-ID, Text-SHA, Unicode-
Codepointanker und exakten Originalausschnitt. Kein generierter Ersatztext.
Redigierte Locatoren verweisen auf sourcegebundene Rawhashes und bestehende
Contentrouten. Seiten/Abschnitte/Cuezeiten werden nur aus vorhandenen Locatoren
übernommen; unbekannte Zeiten bleiben null/unknown. Große Locatorlisten bleiben
über `structure_route` referenziert. Keine private Payload-/Receipt-/Hostdatei-URL.

Ranking bleibt `source_rrf_v1` mit sourceinternem BM25; Rohscores verschiedener
Sources werden nicht addiert. Der opaque `index_generation`-HMAC ist keine
Trefferzahl, Sourceinventur oder Berechtigung. Es gibt keine globalen Counts.

[Schema-Snapshot](examples/content_search_v1.schema.json) enthält Request,
Capabilities und **dieselbe** bestehende Pageklasse. Das
[synthetische Beispiel](examples/content_search_v1.synthetic.json) stammt aus
einem tatsächlichen Gateway-Aufruf mit verifiziertem B-Bundle und FTS5-Build;
es behauptet keine reale Suchqualität.

## Rechte, Cursor und Auslieferungsgrenze

Jede Suche öffnet nur den explizit vorhandenen Index. Der private C23-04-Key wird
neu geladen; keine gecachten Treffer, Generations-/ACLentscheidungen oder alten
Capabilities autorisieren einen Request. Der ContentStore prüft seine aktuelle
Datenbank-/WAL-/Fencegrenze bei jedem Zugriff. Fremde/unbekannte Sourcefilter
liefern dieselbe leere Auswahl; weder Treffer noch Scores oder Counts fremder
Sources werden ausgegeben. Ohne irgendeinen Course-Scope antwortet die API 403
`search_scope_denied`: Das betrifft ausschließlich die eigene Identität.
Eine gültige Identität ohne passende Source-Grants erhält keine verborgenen
Existenzhinweise und kann deshalb denselben leeren Trefferdatensatz erhalten.
Die UI darf daraus keinen Nachweis einer existierenden fremden Quelle ableiten.

Vor jeder Sourcepartition erfolgt die vorhandene Live-ACL-/Status-/Hash- und
vollständige Projektionsprüfung. Fremde Partitionen werden nicht geöffnet oder
gerankt. Quarantäne/Tombstone einer indexierten Version sperrt ihre gesamte
Sourcepartition als `stale_index`; kein alter Statistik-/Textfallback. Selektierte
Versionen sind ausdrücklich generationgebunden; eine neu publizierte Version
wird ohne bewussten Rebuild nicht automatisch mitindiziert.

Cursor bleiben die vorhandenen HMACsignierten C24-Cursor: Actor einschließlich
Role/Course, exakte Query/Filter/Limit/Methode, Generation, Contentrevision und
Ergebnismenge gebunden. TTL 300 Sekunden; Keyrotation, Manipulation, fremde
Identität oder Parameteränderung legitimieren keine Fortsetzung. Kein Offsetcursor
und keine Ausweitung des Scopes durch einen vorher gültigen Cursor.

`SearchHTTP` serialisiert unter dem vorhandenen `search_lexical`-Guard. Ein
`SearchReply` besitzt die noch offenen Locks bis zur vollständigen HTTP-Auslieferung
bzw. Fehlerbehandlung. Der C16-Handler schließt sie in `finally`, auch bei
Verbindungsabbruch. Zusätzliche Frist zwei Sekunden ab fertig hydrierter Seite einschließlich
JSONserialisierung und Auslieferung, innerhalb der bestehenden Retrieval-Guardfrist. Ein vor Sendebeginn
abgelaufener Reply wird geschlossen, ohne Trefferbytes zu senden. Ein Widerruf
nach bereits begonnenem autorisiertem Request kann erst nach dessen Guardcommit
erfolgen; bis dahin erhält ein Writer Busy. Bereits ausgelieferte Bytes lassen
sich nicht rückwirkend zurückrufen. Direktnutzer von `Application.request` müssen
`SearchReply.close()` in `finally` aufrufen; das ist dieselbe explizite
Responselebensdauergrenze wie bei vorhandenen Downloadantworten.

HTTP setzt `Cache-Control: no-store` und `X-Content-Type-Options: nosniff`.
Antworten werden weder im Gateway noch in einer neuen Persistenz gespeichert.
Der vorhandene lokale HTTPServer bindet ausschließlich `127.0.0.1`; TLS/Proxy/
Mehrmandantenisolation und Produktivbetrieb sind keine Abnahme dieses Pakets.

## Fehlervertrag

| Status | Feste Codes / Bedeutung |
| --- | --- |
| 401 | `unauthenticated`, bestehende C16-Authentifizierung |
| 403 | `search_scope_denied`, eigene Identität ohne Courses |
| 404 | `not_found`, unbekannte Route/geschützte nicht verfügbare Ressource |
| 405 | `method_not_allowed`, mit Allow GET bzw. POST |
| 409 | `snapshot_changed`, `stale_index`: neu laden bzw. expliziten Rebuild prüfen |
| 422 | `invalid_request`, `invalid_parameter`, `invalid_cursor`, `scope_required`, `query_too_broad` |
| 503 | `unavailable`, `busy`: deaktiviert, beschädigt, inkompatibel oder Kapazität belegt |

JSONform: `{"schema_version":1,"error":{"code":"unavailable","message":"unavailable"}}`.
Keine Python-, SQL-, Pfad-, Query-, Token- oder Sourceinhalte in Fehlerdiagnosen.
Frühe C16-/Transportablehnungen behalten ihren bestehenden redigierten Vertrag.
Partiell abgebrochene Netzwerkantworten sind vom Client als Fehler zu verwerfen.

## Private Konfiguration und lokaler Start

Bestehende private C16- und ContentReadSettings-Dateien ausdrücklich bereitstellen.
Neue private SearchSettings-Datei (kein Credentialinhalt):

```json
{"schema_version":1,"index_root":"/absolute/private/existing-index"}
```

Der Index muss zuvor durch die vorhandene explizite Bibliothek/CLI gebaut sein.
Kein Initialisieren, Import, Indexieren oder Recovery beim HTTP-Start/Lesen.
Content, Index, Jobs und optionaler Reviewstore müssen getrennte private Roots
sein; der bestehende Cursor-Key muss außerhalb von Content, Index und Jobroot
liegen. Keine neuen Defaultpfade, Datenbankmigrationen oder Dependencies.

```sh
python -m scripts.job_control api --config "$JOB_CONFIG" \
  --content-config "$CONTENT_CONFIG" --search-config "$SEARCH_CONFIG" --port 8016
```

`--search-config` ist ausschließlich im API-Modus und zusammen mit
`--content-config` zulässig. Bestehende Job-/Workflow-/Review-/Contentrouten und
Settings behalten ihre bisherigen Defaultwerte und getrennten Capabilities.

## Übergabe an DEV-01 B und C

A liefert den führenden Suchvertrag. Paket B muss den vorhandenen C16-Executor
mit explizit freigegebenen Indexselektionen, sicherem Commit-/Idempotenz-/
Wiederanlaufbeleg und scoped Status ergänzen. Die aktuellen Catalog-/Worker-
Prozesse kennen nur Material/Quality/PDF/Workflow; keine freie Indexrootübergabe
an HTTP, kein Hintergrundbuild dieses Pakets.

Paket C muss den **gemergten** Vertrag in den bestehenden authentifizierten
Streamlitclient übernehmen, ohne lokale Trefferpersistenz, frei wählbare Rollen
oder Filesystemreads. `next_cursor=null`, leere Treffer und
`index_generation=null` getrennt anzeigen; nach Session-/Rechtewechsel geschützte
Ansichten verwerfen. Detailnavigation nutzt die enthaltenen Text-/Strukturrouten.
Echte UI-/Browserintegration, Indexjobs und gemeinsamer MVP-End-to-End-Lauf sind
nicht durch die Paket-A-Tests nachgewiesen. Reale Quellen, D06/D07, fachliche
Retrievalqualität und Produktionsfreigabe bleiben gesondert offen.
