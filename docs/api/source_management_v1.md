# DEV-02A – autorisierte Quellenverwaltung

20.10.2026. Basis Master `b2c9e3a`, DEV-01A/B und UI #16 integriert.
Die bestehende Source Registry bleibt allein maßgeblich. Keine neue Datenbank,
Queue, Importfreigabe oder API für freie Hostpfade.

## Vorhandene und ergänzte Schnittstellen

Weiterverwendet: GET `/v1/content/sources` (signierte Keysetpagination,
`course_id`, `source_type`, `limit`, `cursor`), `/sources/{id}`,
`/sources/{id}/versions`, `/sources/{id}/versions/{version}/parsed`, `/parsed/{id}`,
Rawdownload und Block-/Text-/Strukturansichten. Diese liefern SourceDTO,
SourceVersionDTO, ParsedDTO mit bestehenden Hash-/Parser-/Provenienzprojektionen.
Keine parallelen Version-/Parserobjekte und kein neuer Detailendpunkt dafür.

Die Quellenliste unterstützt zusätzlich `q`: **literale, case-sensitive Teilzeichenfolge
in der Source-ID**, 1–200 Codepoints, keine Steuerzeichen. Keine Suche in privaten
URLs, Receipts, Payloads oder Quelltexten. `%`/`_` haben keine Wildcardbedeutung.
Die vorhandenen Cursor binden auch diesen Filter. Fremde Sources/Counts bleiben
vollständig verborgen. Die Liste hält jetzt ihren Contentguard bis zur begrenzten
HTTPauslieferung, analog zur integrierten Search-API.

Neu, weil C23-04 absichtlich nur verfügbare Versionen zeigt:

`GET /v1/content/sources/{id}/status?kind=parsed&limit=20&cursor=…`

- `kind`: raw, parsed, runs; bis 50 Einträge je Seite. Signierter Cursor bindet
  Actor, Scope, Source, Ansicht, Limit, ACL- und Publikationssnapshot.
- Source-lokale Raw-/Parsed-Zustandszahlen sowie registrierte Versions-IDs und
  bestehende Read-Routen; keine globalen Totals und kein interner Run-/Receipttext.
- `runs` und `pending_runs` nur für den tatsächlichen Sourceowner mit Operatorrolle.
  Ein Source-Readgrant ist kein Zugang zu unveröffentlichten Verarbeitungsvorgängen.
- registered/raw_only/ready/processing/attention_required sind **Katalogzustände**.
  `integrity=not_checked` bedeutet ausdrücklich keine vollständige Byteprüfung aller
  Versionen. Die bestehenden Read-/Adapter-/Integritätsgates bleiben maßgeblich;
  beschädigte Bytes werden nicht durch einen Statusbericht repariert/freigegeben.
- Quarantänisierte/tombstoned Parsed-Versionen haben keinen Readlink. Ein vorhandener
  zulässiger Raw-/Parsedlink wird beim tatsächlichen Read erneut geprüft.
- Tombstoned/fremde Sources bleiben 404. Feste redigierte Fehler, keine Hostpfade.

`index_inputs_route` verweist auf die **bestehende** DEV-01B-Inputroute. Die UI
verknüpft deren autorisierte Source-/Parsed-IDs mit dem bereits implementierten
Indexstatus. Dieser Report behauptet keine ungeprüfte aktive Generation; die
vollständige Indexprüfung bleibt bei DEV-01B. Keine implizite Indizierung.

Source-/Version-/Parserdetails und Originalbytes kommen weiterhin ausschließlich
aus den vorhandenen Content-Read-Endpunkten, nicht aus der Katalogzählung.
Neue JSONstatusantwort höchstens 256 KiB, Deliverybudget 2 s; ACLguard bleibt bis
Abschluss/Abbruch gehalten. Keine Locks aus Content in C16 oder neue DDL.

## Tatsächliche Importgrenze für das nächste Paket

Vorhanden sind `MaterialBundle` für normalisierte HTML-/Code-/PDF-Materialien und
`SRTBundle`. Raw, vollständige Payload, completed Receipt, ursprünglicher Plan und
hashgebundene ImplementationEvidence sind Voraussetzungen. Der echte
`VerifiedPublicationCandidate` ist eine nicht serialisierbare Prozesscapability;
`import_verified_bundle` prüft den Adapter erneut in eigenem Storestaging.

Ein allein hochgeladenes PDF ist **kein** vollständiges B-Bundle. C18/C19 können
es kontrolliert normalisieren; der freizugebende Material-/Lecture-/Parser- und
Implementierungsbeleg bleibt notwendig. DEV-02B darf nur diesen vorhandenen
Vertrag anbinden, keine beliebigen Payloaddictionaries promoten. TXT/VTT sind
keine unterstützten ContentStore-Bundleadapter; Unknown-Time unverändert.
Historisches SRT mit falschem relativen Sourcepfad bleibt D06-blockiert.
Reale Aufnahme/D07 und produktive Roots sind in diesem Auftrag nicht freigegeben.

## Nachweise und Integrationsstatus

Geändert: `reader.py` (q), `http.py` (bestehende Liste/Statusrouting),
`source_status.py` (kleiner versionierter Transportstatus und Guard),
`tests/test_source_management.py`. Dokumentation/Schemas unter bestehendem `docs/api`.
[JSONschema](examples/source_status_v1.schema.json),
[tatsächliche synthetische Antwort](examples/source_status_v1.synthetic.json).
Testergebnisse stehen im abschließenden Prüfvermerk unten. API-PR gegen Master,
kein automatischer Merge. Ein offener PR ist keine integrierte UI-Voraussetzung;
sein eigener Branch/Worktree bleibt bis zum verifizierten Merge erhalten.

### Tatsächliche Prüfung

Python 3.12.12, Pydantic 2.13.4, SQLite 3.50.4, Pytest 9.1.1 und Ruff 0.16.0 aus
vorhandenen Umgebungen. Keine Installationen. Mit
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest`
und `-q -p no:cacheprovider tests/test_source_management.py
 tests/test_content_read_contracts.py tests/test_content_http.py
 --basetemp=/tmp/dev02a-release`: **68 passed / 0 failed / 0 skipped**, 91,84 s.
11 neue Sourcefälle, 14 DTO-/Redaktionsfälle und 43 tatsächliche lokale HTTPfälle.
Der Loopbackserver wurde ausdrücklich erlaubt; externe Dienste nicht verwendet.

Geprüft: Autorisierung/Readgrant/Entzug/fremde Source, literal q ohne private
URLsuche/Wildcards, Source-/Raw-/Parsedreferenzen, Quarantäne ohne Readlink,
Grenzen/fehlerhafte Parameter, getrennte Owner-Runs, bindende Cursor und
ACLsnapshotwechsel, gehaltener Deliveryguard. Erster Entwicklungslauf: 21 pass/
3 fail wegen falsch adressiertem Ownerattribut; korrigiert und vollständig erneut
geprüft. Keine alten Assertions oder Sicherheitslimits abgeschwächt.

Ruff Check/Format Check für vier Pythondateien sowie `git diff --check` erfolgreich.
JSONschema gegen das tatsächliche Modell, Beispiel gegen SourceStatus validiert.
Der Beispielgenerator verwendet einen separaten synthetischen temporären Store.
Logs außerhalb des Repositories; keine Realabnahme, Imports oder Produktivfreigabe.
