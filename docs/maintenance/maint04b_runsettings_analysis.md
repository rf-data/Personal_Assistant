# MAINT-04B – RunSettings und fehlender Discriminator

25.10.2026, Basis `1a973f4`. **Nachgewiesen, nicht kompatibel reparierbar ohne
Formatentscheidung.** Keine Änderung an Settingsmodellen, Alias, Defaults oder
gespeicherten Konfigurationen. C26 **HOLD**.

## Ausgangsproblem und Ursache

`src.core.config_parsing.RunSettings` ist eine mit
`Field(discriminator="meta_type")` annotierte Union aus HTML-, Notebook-, MD-,
PDF-, PlainText-, URL-, Wiki- und ChunkSettings. `src.core.config.RunSettings`
verschachtelt dieselben sieben Parsingvarianten zunächst in
`ParseSettings_all`, ebenfalls mit diesem Discriminator, und ergänzt ChunkSettings.
**DOCX und das aggregierte ParseSettings gehören keinem der Aliase an.**

Keine der acht Varianten, ihrer öffentlichen Eltern oder der privaten MAINT-04-
Feldbasen definiert `meta_type`. Es gibt keine Literalwerte, Aliaszuordnung,
Validatoren oder Defaultfactories dafür. `TypeAdapter(RunSettings)` scheitert
bereits beim Aufbau des Validators mit **PydanticUserError,
code=discriminator-no-field**, zuerst bei `ParseHTMLSettings`. Es findet noch
keine Payloadvalidierung und keine Tagentscheidung statt. Ein vom Aufrufer
übergebenes `meta_type` löst den fehlenden Modellfeldvertrag nicht.

Der Fehler bestand vor MAINT-04; dessen bestehender Negativtest wird unverändert
weiter ausgeführt. Die Konsolidierung hat kein vorheriges Tagfeld entfernt.
Beide Definitionen bleiben bytegleich zum MAINT-04-Basisstand. Die neue
Regressionscharakterisierung wurde **vor** der Workflowkorrektur ausgeführt.

## Versionen, Vererbung und Serialisierung

Getestet mit Python 3.12.12 / Pydantic **2.13.4** (Core 2.46.4) und **2.14.1**
(Core 2.50.1). Root-, beide Worker- und Runtime-Lockdateien verwenden 2.13.4;
Rootanforderung ist `pydantic>=2.13.3`. Die gesamte offene Versionsrange und
Python 3.13 wurden nicht geprüft. Beide vorhandenen Versionen zeigen denselben
Aliasfehler und dieselben gültigen Einzelmodell-Roundtrips. Keine Installation
oder Änderung von Lockdateien.

Die direkt benannten Varianten funktionieren weiter ohne Tags; alle acht leeren
Payloads validieren und ihre Dumps lassen sich mit exakt derselben Modellklasse
wieder lesen. MD, PlainText und URL validieren die Payload
`{"save":["txt"],"assemble":["md"],"scrape_images":false}` mit identischem
JSON-Dump, aber verschiedenen nominalen Typen. HTML und Notebook akzeptieren
beide ein beliebiges `parser`-Feld. Selbst ein leerer Dump verrät die Herkunft
nicht zuverlässig. Ein Wechsel zu einer ungetaggten Union würde bei solchen
Payloads anhand der Union-/Pydanticreihenfolge einen Typ auswählen.

Parsingvarianten ignorieren heute unbekannte Extras: Ein erfundenes
`meta_type` verschwindet beispielsweise im MD-Dump. ChunkSettings verbietet es
mit `extra_forbidden`. Ein gemeinsames nachträgliches Tagdefault oder geänderte
Extra-Regeln wären beobachtbare Schema-/Dump-/Validierungsänderungen. Die
nominalen Familien dürfen nicht durch geratenes Dispatching ersetzt werden.

## Aufrufer und historische Konfigurationen

Die aktive Importsuche findet als konkreten Aliasaufrufer nur
`src/tools_parsing/extract_medium.py` (Legacy-`__main__`):
`get_yaml_config("run_args", model=RunSettings)`. Dieser Pfad benötigt außerdem
das fehlende `RunContext`, das nur auskommentierte `get_yaml_config` und das
fehlende `read_html_file`. Ein funktionierender importierter Alias würde diese
weiteren Produktfehler nicht lösen. Darüber hinaus behandelt der Runner
`run_config` wie eine aggregierte Konfiguration (`name_log`, `name_logfile`),
obwohl diese Felder in den Aliasvarianten fehlen. Es gibt keine versionierte
`run_args.yaml` im vorhandenen Konfigurationsbestand.

Der heutige YAML-Loader `utils.dict_helper.load_yaml_config` ruft
`cls.model_validate` auf; ein `Annotated`-Unionalias hat diese BaseModel-Methode
nicht. Auch dafür darf kein stiller Loaderumbau erfolgen. Der konkrete Alias-
Aufrufer verwendet gerade den nicht mehr implementierten alten Loader.
Die realen Lecture-Kontextbuilder lesen dagegen ausdrücklich `ParseSettings`
und `GeneralSettings`, nicht `RunSettings`.

`configuration/cfg_parsing.yaml` und `streamlit_run.yaml` verwenden verschachtelte
Aggregatfelder ohne `meta_type`. Beide funktionieren mit Legacy-ParseSettings;
streamlit_run bleibt wegen seiner Loggingfelder mit Parsing-ParseSettings
ungültig. Die bisherigen Logging-/PDFflagunterschiede zwischen den beiden
Familien bleiben erhalten. Alle MAINT-04-Goldens werden weiter geprüft. Über
private alte Alias-Payloads/Pickles ist keine Aussage möglich.

## Entscheidungsvorlage statt stillschweigender Migration

| Option | Vertrag und Konsequenz | Bewertung |
| --- | --- | --- |
| Bestehenden Alias durch Standardtags reparieren | Acht bisher nicht dokumentierte Literalwerte und neue Feld-/Dumpdefaults festlegen; DOCX-Mitgliedschaft und Aggregate separat entscheiden; Herkunft alter mehrdeutiger Payloads bleibt unbekannt | Ohne fachliche Formatfreigabe nicht kompatibel |
| Discriminator entfernen / Typ aus Feldern raten | Mehrdeutige MD/PlainText/URL- und HTML/Notebookpayloads erhalten scheinbar gültige, möglicherweise falsche Klassen | Nicht implementieren |
| Neuen versionierten Envelope mit expliziter Herkunft und Variante einführen | Tags, zulässige Varianten und versionierten Loader neu definieren; bisherige explizite Einzel-/Aggregatmodelle weiter lesen; unversionierte Payload nur mit vom Aufrufer bekannter Herkunft | Empfohlener Folgeauftrag, hier nicht implementiert |

Vor Umsetzung entscheiden: Tagvokabular; Formatversion; beide Modellfamilien;
DOCX und Aggregate; fehlende/unbekannte Tags; Default-/Dumpregeln; heutige
Legacy-Aufrufer ersetzen oder erhalten. Dann mit Originalkopien und explizitem
Reader alte gültige Payloads prüfen. Unbekannte Herkunft darf keine automatische
Migration auslösen. Die Aliasfunktion bleibt bis dahin nachweislich defekt;
dieser Bericht behauptet keine Reparatur oder Freigabe.

## Tests und Restrisiken

`tests/test_runsettings_contract.py` ergänzt **28 Fälle**: Fehlercode beim
Adapteraufbau, acht Variantendefaults pro Familie, nominale Mehrdeutigkeit,
Tagverlust/Extraablehnung, ungültige Literals und zwei historische YAMLs.
Legacydeklarationen werden mit dem vorhandenen MAINT-04-AST-Harness geladen;
das ersetzt keinen echten `core.config`-SDK-/Envimport. Bestehende
`test_broken_discriminated_alias_stays_visible` und alle MAINT-04-
Charakterisierungen bleiben unverändert. Ergebnisse und Grenzen stehen in
[Validierung](maint04b_validation.md), SDKbefunde in
[Legacyintegration](maint04b_legacy_integration.md).
