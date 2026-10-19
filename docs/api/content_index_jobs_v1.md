# DEV-01B / C24-02-C – kontrollierte Indexjobs

Basis: Backend `79d800caf3270de07296b49dc4585c1e01ceb085`, DEV-01A/#124 integriert.
[Search-API](content_search_v1.md), [FTS5-Lebenszyklus](../architecture/content_fts_implementation.md),
[Implementierungsplan](../planning/c24_implementation_plan.md),
[bestehendes Issue #115](https://github.com/rf-data/Personal_Assistant/issues/115).
Keine zweite Queue, Datenbank, Suchengine oder automatische Indizierung.
[Tatsächliche Tests und Grenzen](content_index_jobs_validation.md).

## Konfiguration und Anfragevertrag

`Settings.index_jobs_enabled` ist standardmäßig false. Zusätzlich ist die bisherige
`execution_enabled`-Freigabe erforderlich. Ein ausdrücklich angelegter privater,
vorhandener ContentStore und leerer/bestehender FTS5-Root bleiben Voraussetzungen;
HTTP liest/provisioniert weder automatisch Stores noch Quellen.

Der zusätzliche C16-Prozess heißt `content_index_build`. Er verwendet die
vorhandenen Routen `/v1/previews`, `/v1/jobs`, `/v1/jobs/{id}`, `/start`, `/cancel`,
`/artifacts` und `/logs`. Actor/Role/Courses kommen ausschließlich aus C16.

```json
{"schema_version":1,"process_id":"content_index_build","parameters":{"schema_version":1,"source_ref":"approved-index-v1","course_id":"cs50_python","resume_of":null,"output_name":"index-build"}}
```

Der Client bestätigt die tatsächliche serverseitige Vorschau und sendet sie im
bestehenden StartRequest mit `confirmed=true` und `Idempotency-Key` (16–64 ASCII-
Identifierzeichen). Gleicher Actor/Key/Intent liefert denselben persistierten Job,
auch nach Neustart oder Fehler. Anderer Intent unter gleichem Key bleibt Conflict.
Kein zweiter Job wird heimlich erstellt. Unterschiedliche Keys sind ausdrücklich
unterschiedliche Vorgänge; C16 serialisiert denselben Prozess, der vorhandene
Indexbuildlock schützt zusätzlich gegen konkurrierende Bibliotheks-/CLI-Builder.

`source_ref` bezeichnet ausschließlich einen serverseitig freigegebenen
`CatalogEntry(kind="index_bundle")`. Genau eine hashgebundene JSONdatei,
`roles={"index":"index.v1.json"}`, und genau ein Course. Keine HTTP-Hostpfade,
Kommandos, SQLstrings, freie Selectoren oder neuen Candidate-Dictionaries.
`IndexParams`/`IndexJobPlan`/`IndexJobReceipt`/`IndexStatus` sind in
[index_models.py](../../src/job_control/index_models.py) bzw. den bestehenden
[C16-Modellen](../../src/job_control/models.py) dokumentiert und versioniert.

Die private `IndexJobPlan`-Datei enthält:

- Ganzzahlige `schema_version=1`, Course-ID.
- Die bereits integrierten `ContentReadSettings` und `SearchSettings` aus A.
- Bestehende `IndexSelection` inklusive unveränderter Projektionspolicy.
- 1–32 vollständige, sortierte `VersionBinding`-Belege: Source-/SourceVersion-/
  ParsedVersion-/ParserConfig-ID, Payload- und Projektionshash. Die IDs entsprechen
  exakt der Selektion. Keine heuristische Auswahl der „neuesten“ Version.

Die Belege werden aus dem tatsächlich verifizierten bestehenden Projektionsvertrag
gewonnen und vom Operator freigegeben. Vor Annahme und im Worker werden sie erneut
mit der tatsächlichen Projektion verglichen. Ein JSONfeld ist kein Ersatz für die
ContentStore-/B-Gates. Raw-/Payload-/Locatorbytes werden weder repariert noch neu
geparst. Der Cursor-Key wird nur über seinen privaten vorhandenen Dateipfad
referenziert; seine Bytes werden nicht in den Job kopiert oder ausgegeben.
Content, Index, Key und Jobroot müssen getrennt sein; keine Symlinkadoption.

Beispiel eines Katalogeintrags (alle Werte ausdrücklich private Platzhalter):

```json
{"kind":"index_bundle","root":"/absolute/private/approved","files":{"index.v1.json":"<exakter SHA256>"},"roles":{"index":"index.v1.json"},"course_ids":["cs50_python"]}
```

APIstart weiterhin mit `--content-config` und `--search-config`, Worker weiterhin
mit **derselben** privaten C16-Konfiguration. Die neuen Indexstatusrouten zeigen
nur Katalogeinträge, deren Content-/Searchsettings exakt dem bedienten A-Vertrag
entsprechen. Indizierung erfolgt ausschließlich nach bewusster Bestätigung und
C16-Freigabe, niemals beim Öffnen einer Seite/Capability/Statusansicht.

## Autorisierung und Aktivierung

Preview/Create/Start prüfen aktuellen Course plus Operatorrolle und vollständige
Ownership aller ausgewählten Sources. Read-Grants verleihen kein Buildrecht.
Vor Dispatch prüft C16 die aktuellen Identitäten, Flagfreigabe und den unveränderten
Katalog. Der feste Offlineadapter liest ausschließlich die hashgebundene Selektion.
Die bestehenden FTS5-Checks prüfen die vollständige Projektion erneut, private
Stagingbytes, SHA/Größe, SQLite-/FTS-Closure, Content-/ACLsnapshot und Policy vor
dem atomaren Activewechsel. Keine reduzierte Integrität zur Beschleunigung.

Eine zusätzlich nachgewiesene Lücke der Bibliotheksgrenze ist geschlossen:
Ersetzen einer aktiven Generation verlangt nun ebenfalls Ownership und Course
für **alle bereits aktiven Sources**. Sonst könnte ein Operator mit eigener
Teilselektion einen fremden Indexbestand verdrängen. Beide Prüfungen liegen unter
dem vorhandenen Catalog-/Contentguard vor Aufbau und unmittelbar vor Aktivierung.
Gemischte Ownership braucht getrennte ausdrücklich provisionierte Indexroots;
es gibt keine erfundene globale Administratorrolle.

C16 gibt Jobdaten nicht allein wegen desselben Courses frei: Indexjobdetails,
History, Logs, Artifactreferenzen und Indexstatus benötigen aktuelle Rechte auf
sämtliche gebundenen Sources. Widerruf entzieht diese Ansichten; APIantworten halten
den Contentguard auch durch Encoding/Delivery. Indexkataloglabels stehen ausschließlich
in der eigenen autorisierten Inputroute, nicht in der courseweiten C16-Inputliste.
Die vorhandenen C15-/C16-Metrikfamilien zählen diesen neuen Prozess nicht und
führen keine sourceübergreifenden Indexjobcounts ein.

## Receipts, Abbruch und Wiederanlauf

Die bestehenden privaten `BuildReceipt`-, Manifest- und Activeformate bleiben
unverändert. `ContentIndex.build(..., build_id=...)` erlaubt zusätzlich die an den
C16-Job gebundene 32stellige Hex-ID; wiederverwendete/ungültige IDs werden abgewiesen,
keine vorhandenen Versuche überschrieben. Zufällige IDs bleiben der Bibliotheksdefault.

Der neue kleine C16-Ergebnisbeleg `IndexJobReceipt` bindet Job-/Build-ID, Outcome
`activated`/`already_active`, opaque Generation-HMAC, explizite Source-/Parsed-IDs,
Selektions-/Recordsethash und scoped Recordcount. Keine Pfade, Keybytes oder globalen
Contentrevisionen. C16 veröffentlicht seine gewöhnliche hashgebundene
`Artifact(kind="index_build")`-Referenz erst nach bestätigtem Prozessende.

| Zustand | Kontrollierte Behandlung |
| --- | --- |
| Abbruch vor Activewechsel, Teilstaging/Ready | Kein Teilindex aktiv; C16 interrupted/failed, unvollständige Bytes bleiben private Belege |
| Abbruch nach atomarem Activewechsel / Responseverlust | Aktive vollständige Generation kann bereits sichtbar sein, auch wenn Job interrupted/cancelled ist |
| Wiederholung desselben Keys | Derselbe terminale Job, kein automatischer Wiederstart |
| Bewusster neuer Auftrag mit `resume_of=<terminaler eigener Job>` | Gleichen Course/Katalog/Ownership und vollständige Versionbelege neu prüfen |
| Vorgänger ist noch exakt aktive Generation | Alle Bytes/FTS erneut verifizieren und `already_active` bestätigen, ohne Active neu zu schreiben |
| Keine entsprechende aktive Vorgängergeneration | Neuer Build mit neuer Job-/Build-ID aus unverändert geprüftem ContentStore; **keine** Übernahme alten Stagings |
| Geänderte Rechte/Hashes/Selektion, unbestätigtes Prozessende | Fail closed; keine automatische Übernahme oder Sperraufhebung |

C16-Jobstatus und tatsächlicher Aktivierungseffekt sind getrennt. Cancel/Timeout
sind kein Rücknahmeversprechen für einen schon atomar aktivierten Index. Alte
Generationen und Staging werden nicht durch diesen Auftrag gelöscht. Ein verlorener
Guardian kann die bestehende C16-Quarantäne auslösen; sie wird niemals automatisch
zurückgesetzt oder als Wiederanlaufrecht behandelt.

## Autorisierte Statusrouten

Alle Routen im bestehenden Gateway, authentifiziert, GET-only, keine Bodies:

| Route | Antwort |
| --- | --- |
| `/v1/content/index/capabilities` | Version, enabled, Prozess-ID, Limits und explizite Retrypolicy |
| `/v1/content/index/inputs?offset=0&limit=10` | Nur aktuell lesbare freigegebene Selektionen; Source-/Parsed-IDs, Selektionshash, `can_build` |
| `/v1/content/index/status?input_ref=approved-index-v1&offset=0&limit=10` | `IndexStatus`, bis 20 autorisierte Jobs/Seite, vorhandener geprüfter Ergebnisbeleg |

Keine globalen Totals. `next_offset` bezieht sich ausschließlich auf erlaubte
Einträge. Inputseiten höchstens zehn Einträge, Jobseiten höchstens zwanzig, Offset
0–1000, Antwort höchstens 256 KiB. Doppelte/unbekannte Parameter abgewiesen.
`can_build` bezeichnet Sourceownership/Role; Ausführungsflag, Workerzustand und
bestätigte neue Vorschau bleiben zusätzliche Voraussetzungen.

Status unterscheidet `not_indexed`, `active`, `stale`, `blocked`, `failed`,
`building`, soweit nachweisbar. `active` wird durch denselben sourcebegrenzten
FTS5-/Liveverifikationspfad wie Search überprüft, nicht aus einem alten Cache
abgeleitet. Quarantäne, fehlende oder unprüfbare Versionen/Partitionen bleiben
blocked/unavailable. Eine andere aktive Versionsauswahl ist stale; alte explizite
Versionen werden nicht automatisch auf aktuelle Versionen umgeschrieben.
`latest_activation` ist separat committed/not_committed/undetermined. Ein historischer
Receipt oder Jobabschluss ist keine aktuelle Capability und kein Ersatz für den
live bestätigten Status. Eine nicht beweisbare Aussage bleibt undetermined.

Feste redigierte Fehler aus C16/A: 401 unauthenticated, 403/404 für verweigerte
Operationen/Ansichten, 409 Konflikt, 422 Parameter/Schemaverstoß, 503 unavailable.
Unbekannte/fremde Inputs werden nicht als Sourceinventar ausgegeben. Keine
Fehlermeldung enthält Sourcebytes, Credentials, SQL oder Hostpfade.

## Grenzen und UI-Übergabe

Worker: 180 s Wallclock, 120 s CPU, 768 MiB Adressraum, 64 MiB Dateigröße,
bestehende C16-Prozess-/FDlimits. Die strengeren bisherigen C24-Limits gelten
zusätzlich: maximal 32 Sources bei Abfragen, 1.000 Matches, 128 MiB Query-I/O,
volle Projektion-/Hash-/FTS-Prüfung und Queryfristen. Keine Skalierungsfreigabe;
Livevollverifikation kann bei größeren Beständen weiterhin unavailable liefern.

C25 nutzt die gemergte A-Suche und diese Routen nur nach tatsächlicher
Capabilityantwort. Auf A-only Backends bleibt Indexjobbedienung deaktiviert;
fehlende Routen werden nicht als lokale Speicher-/Indexierschnittstelle ersetzt.
UI-PR und gemeinsamer synthetischer Client-/AppTestnachweis werden getrennt
versioniert. Kein produktiver Betrieb, reale Sourcefreigabe oder menschliches
Gold durch erfolgreiche synthetische Jobs.
