# MAINT-04B – Legacy-Einstiegspunkte und Abhängigkeiten

25.10.2026, Basis `1a973f4`; C26 **HOLD**. Keine optionalen Pakete installiert,
keine Originalmaterialien, Downloads, Modelle, APIs oder LLMs verwendet.
**Importinventar und begrenzte synthetische Prüfung**, keine vollständige
Legacy-DOCX-/DIY-/Doclingabnahme. Produktive Parser unverändert.

## Methode und vorhandene Umgebungen

Alle acht angeforderten Eingangsdateien einschließlich AGENTS.md waren vorhanden
und wurden gelesen. Maßgeblich sind außerdem MAINT-03s R05/R06/R07/R15,
MAINT-03Bs Profil-/Isolationsgrenzen und die MAINT-04-Kompatibilitätsmatrix.

Zwei vorhandene Python-3.12.12-Interpreter wurden ausschließlich lesend verwendet:

- **K**: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python`,
  Pydantic 2.13.4, pytest 9.1.1; keine PDF-/HTML-SDKs.
- **E**: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`,
  Pydantic 2.14.1, pytest 9.1.1, BeautifulSoup 4.15.0, PyMuPDF 1.27.2.2,
  markdown-it-py 4.2.0. Keine DOCX-/OCR-/Tokenizer-/Session-SDKs.

Weitere vorhandene Projektinterpreter wurden nur auf Distributionsmetadaten
geprüft, nicht für Änderungen oder Tests fremder Projekte verwendet. Keiner
enthielt python-docx, returns, tiktoken oder Docling. In separaten vorhandenen
UI-/Jobsucheumgebungen sind pandas/NumPy/pydantic-settings verfügbar; diese
Pakete wurden nicht zwischen Umgebungen vermischt. Kein reproduzierter Neubau
des Root-/Worker-/Runtimeprofils wird behauptet.

`scripts/maint04b_legacy_probe.py` führt **22 frische Importe pro Interpreter**
aus: je ein `python -I -B`-Kindprozess, leeres temporäres CWD, freigegebene
synthetische Envwerte statt geerbter Credentials. Auditgrenze verbietet
Dotenv-Lesen, Dateischreiben, Verbindungs-/Listener-/DNSaufrufe und externe
Prozesse. Keine SDKs oder Zielmodule werden substituiert. Es werden nur Module
importiert, keine Runnerfunktionen gestartet. Fehlertyp, erstes fehlendes Modul
und Projektstackpositionen werden protokolliert, keine privaten Envwerte.
Die Auditgrenze ist kein Betriebssystem-Sandboxersatz.

## Abhängigkeitsmatrix

`M:` bedeutet tatsächlichen `ModuleNotFoundError` beim ersten Importhindernis,
nicht den Nachweis, dass der übrige Importgraph funktioniert. „Optional“ bezieht
sich auf die schlanke Rootanwendung; für den gewählten Legacy-Pfad sind diese
Pakete tatsächlich erforderlich. „AST“ bezeichnet ausgeschnittenen Originalcode
mit kontrollierten Laufzeitgrenzen, keinen Vollimport.

| Modul / Einstieg | Erwartete Funktion | Import K / E | Benötigte Dependency / Pflicht im Pfad | Optional im Projekt | Offline-Testbarkeit | Vorhandene / neue Abdeckung | Prüfergebnis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `core.config_parsing` | Reine Parsingmodelle | OK / OK | Pydantic, Rootpflicht | Nein | Ja | MAINT-04, RunSettings neu | Echte Importe SDK-frei; Alias selbst defekt |
| `core.config` | Legacy-Settings und Env | M:pydantic_settings / gleich | pydantic-settings; synthetische Pflicht-Envwerte | lecture-worker | Ja mit passenden Paketen | MAINT-04 AST | Kein echter Vollimport; Envinitialisierung bleibt eager |
| `core.memory_parsing` | ParseContext/Backend/Encoder | M:tiktoken / gleich | tiktoken | lecture-worker | Teilweise | MAINT-04 Kontext-/Assignment-AST | Reales Modul blockiert; reiner Kontext separat charakterisiert |
| `core.memory` | Globale AppSession | M:tiktoken / gleich | tiktoken, config/Settings | lecture-worker | Mit SDKs und synthetischer Env | Isolierte IO-/Parsergrenzen | Kein globaler Sessionvollimport behauptet |
| `model_parsing.base_classes_parsing` | Legacy-Records | OK / OK | Pydantic, Rootpflicht | Nein | Ja | Neue PDF-Word-JSONgrenze | Echte Word-/WordMeta-Modelle; Aliase mit meta_type separat problematisch |
| `model_parsing.pdf_extractor` | DIY-PDF | M:fitz / M:returns | PyMuPDF, returns, Session, NumPy/Enricher | lecture-worker / transitive SDKs | Teilweise | MAINT-04 Dispatch; 3 neue reale PDF-Wortgrenzen | Vollimport fehlt; echter SDK-Text und Originalnormalisierung separat geprüft |
| `model_parsing.docx_extractor` | Strukturierter DOCX-Parser | M:returns / gleich | returns, python-docx, Session/Enricher | lecture-worker | Erst nach Import-/SDKreparatur | Statischer Befund, Annotationprobe | Zusätzlich ungebundene Document/Paragraph/Table/CT_P/CT_Tbl |
| `model_parsing.text_extractor` | MD-/TXT-Parser | M:tiktoken / gleich | markdown-it-py, Session und Helfer | unclear / lecture-worker | Erst nach Vertrag-/Importklärung | MAINT-04 Grenztests | TXT importiert nicht vorhandenes memory.session; weitere ungebundene Recordnamen |
| `model_parsing.url_extractor` | Legacy-URL-Extraktion | M:bs4 / M:requests | bs4, requests; interne fehlende Module | Optional/transitiv | Nur synthetisches HTML, kein Fetch | R06 statisch | Zusätzlich fehlen src.model_tools und read_html_file |
| `tools_parsing.extract_pdf` | PDF-Extract-/Restructure-Schritt | M:returns / gleich | returns, PDFCleanExtractor, Session | lecture-worker | Mit SDKprofil | MAINT-04 Dispatch | Echter Vollpfad blockiert |
| `tools_parsing.parse_document` | Backendrouter | M:tiktoken / gleich | Context, DIY und eager Doclinghelper | lecture-worker | Teilweise | MAINT-04 Dispatch/Outputnamen | Docling wird sogar für DIY importseitig benötigt; DOCX-Dispatch auskommentiert |
| `tools_parsing.extract_medium` | Legacy-Mediumrunner | M:pydantic_settings / gleich | Settings, Session, bs4 und Helfer | Optional | Erst nach Vertragsklärung | R06, Aliasanalyse | Zusätzlich RunContext/get_yaml_config/read_html_file nicht vorhanden |
| `utils.text_file_helper` | DOCX-Text/Tabellen und Textdateien | M:pandas / gleich | pandas; python-docx für DOCX | frontend / lecture-worker | Mit kleinen SDKs | R07, isolierte NameError-Probes | Document-Import auskommentiert; keine scheinbare Reparatur mit Fake-Document |
| `utils.pdf_helper` | Zählen/Splitten | M:pypdf / gleich | pypdf, Session | lecture-worker | Mit SDKs | Statische Prüfung | Kein Splitlauf; keine LibreOffice- oder Originaldatenverwendung |
| `utils.docling_helper` | Converter/OCRoptionen | M:PIL / gleich | Pillow, Docling/Core/RapidOCR | lecture-worker transitiv | Konfiguration ja; Konvertierung ggf. Modellcache | MAINT-04 injizierte Outputgrenze | Keine echte OCR-/Formelerkennung oder Modelle |
| `tools_lecture.process_lecture` | Dokument-/Medienaktionen | M:tiktoken / gleich | tiktoken, Settings, Parser, Transcribeprovider | lecture-worker | Kontextgrenze ja, Gesamtpfad nein | MAINT-04 YAML-/Kontextbuilder | Kein echtes Media-/LLM-Processing |
| `run_lecture_processing` | Interaktiver Legacyrunner | M:tiktoken / gleich | LectureContext, process_lecture | lecture-worker | Nur explizite synthetische Konfiguration | Statisch, keine main-Ausführung | Nicht ausführbar in den vorhandenen schlanken Umgebungen |
| `tools_materials.processing` | Moderne Materialpipeline | M:bs4 / OK | bs4; PDF-SDK erst im PDFzweig | test-offline | Ja | Materialcontract/PDF/HTML/Code/Processing/E2E | Echte synthetische Tests; keine Legacyvollintegration daraus ableiten |
| `tools_lecture.adapt_cs50` | Transcript-/Lectureadapter | OK / OK | reine Verträge; kein Legacy-SDK zum Import | Rootpflicht | Ja | Lectureadapter/DEV03/MAINT-03B-Isolation | Frischer Import bestanden |
| `scripts.cs50_materials` | Material-CLI | M:bs4 / OK | Materialpipeline; PyMuPDF im PDFzweig | test-offline | Ja | Bestehende Material-E2E-/CLIfälle | Import E bestanden; synthetische CLIprüfungen separat |
| `scripts.cs50_lecture` | Lecture-CLI/Supervisor | OK / OK | Reine CLI; Provider/LLM erst bei Ausführung | Root / optionale Provider | Ja im Offlineprofil | Lecture-Runner und LLM-Smoke | Import bestanden; kein echter APIaufruf |
| `scripts.cs50_worker` | Kontrollierter Jobrunner | OK / OK | C16/Capacity; konkrete Adapter erst später | Root / jeweilige Adapter | Ja synthetisch | Workflow-/Workerprüfungen | Import bestanden; kein Server gestartet |

K: **5 importiert, 17 am ersten Dependencyhindernis abgebrochen**.
E: **7 importiert, 15 am ersten Dependencyhindernis abgebrochen**.
Diese 44 Importprobes sind keine 44 bestandenen Pytestfälle. Keine Skips oder
Importfehler werden in erfolgreiche Parserläufe umgerechnet.

## Bestätigte Produktfehler versus optionale Pakete

Die fehlenden Drittanbieterpakete sind Umgebungsgrenzen. Davon unabhängig sind
die projektextern nicht lösbaren Bindungen statisch nachvollziehbar: kein
versioniertes `src/model_tools.py`, keine aktive Definition von `read_html_file`,
`get_yaml_config`, `memory.RunContext` oder `memory.session`. Keine geratenen
Reexports, Ersatzsessions oder neuen Loader hinzugefügt.

Für R07 wurden `read_docx_text` und `extract_docx` als unveränderte Original-
Funktionskörper ausgeführt: beide liefern **NameError: Document**, vor jedem
Dateizugriff. Die Originaldeklaration von `DOCXCleanExtractor._iter_block_items`
liefert denselben Fehler bereits bei Auswertung der Annotation. Das sind
isolierte Bindungsnachweise; noch kein vollständiger DOCX-Modulimport und keine
Parsingprüfung mit installiertem python-docx. Deshalb bleibt die Reparatur offen.

`parse_document` importiert DIY, Klassifizierer/Assembler und Doclinghelper auf
Modulebene. Dessen `__main__` wählt ausdrücklich Docling; der Lecture-Kontextbuilder
wählt bisher keinen Backenddefault. Die zulässigen Lecture-Suffixe enthalten DOCX,
während der tatsächliche Router nur DIY-PDF oder Docling dispatcht. Diese Lücke
darf nicht durch eine automatische Backendwahl oder neue Defaults verdeckt werden.
DIY nutzt im Extraktionsschritt `ParseContext.local_path`; ein abweichendes
`file_path` ist deshalb gesondert zu prüfen, kein hier bestätigter Fix.

Dynamische Grenzen: MaterialProcessor importiert HTML/PDF/Codeparser erst im
jeweiligen Verarbeitungszweig; deren Importstatus ist nicht durch den Import des
Processors allein bewiesen. TXT importiert `memory.session` innerhalb von extract.
Im untersuchten Legacyrouter wurde kein aktiver `importlib.import_module`-
Pluginmechanismus gefunden. Externe Namespace-Erweiterungen bleiben unbekannt.

## Synthetische Pfade und Reproduktion

Die neue `tests/test_legacy_pdf_boundary.py` erzeugt drei kleine zweitseitige PDFs
mit **echtem PyMuPDF**, liest echte Wort-/Boundingboxdaten, führt die unveränderten
Originalmethoden `_clean_word_token` und `_clean_words_from_words` aus und liest
die echten `Word`-Modelle aus JSON zurück. Textreihenfolge, alle vier Koordinaten,
Quellhash und fehlende Nebenausgaben werden geprüft. Nur die beiden Methoden
werden per AST geladen; vollständiger Extractor, Enricher, returns und Session
sind nicht emuliert. Es ist ein repräsentativer **Teilpfad**. Ein vollständiger
Legacy-PDF- oder DOCXpfad ist mit den vorhandenen Abhängigkeiten nicht ausführbar.
Die moderne Material-PDFpipeline wird davon getrennt real synthetisch geprüft.

```bash
# Bestehenden passenden Interpreter verwenden, nichts installieren:
PYTHONDONTWRITEBYTECODE=1 "$MAINT_PYTHON" scripts/maint04b_legacy_probe.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$OFFLINE_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard tests/test_legacy_pdf_boundary.py \
  tests/test_parsing_configuration_integration.py
```

`MAINT_PYTHON` ist K oder E, `OFFLINE_PYTHON` ist E. Ergebnisse aller tatsächlich
ausgeführten Suites stehen in [Validierung](maint04b_validation.md).

Für eine spätere eigene SDKumgebung zuerst die vorhandene kleine Gruppe
`test-offline` verwenden; keine pauschale Installation von lecture-worker,
frontend, NLP oder RAG. Die folgenden Paketversionen stammen aus dem bestehenden
Rootlock, sind **nicht installiert worden**:

| Paket / Version | Zweck einer gezielten Folgeprüfung | Risiken / weitere Voraussetzungen |
| --- | --- | --- |
| python-docx 1.2.0, lxml 6.1.1 | Synthetisches DOCX erzeugen/lesen, Paragraphen/Tabelle/Headings | Native XMLabhängigkeit; fehlende lokale Document-/CT_*-Imports bleiben Produktfehler |
| pandas 3.0.5, NumPy 2.5.2 | Eager Texthelperimport / Tabellen bzw. Enricher | Native Wheels, vergrößerte Importoberfläche; pandas ist nicht Teil test-offline |
| returns 0.29.0 | Echte Result-/Success-Kette | Kein Fake-Result als Integrationsnachweis |
| pydantic-settings 2.15.0 | Reales config-Modul | Nur leeres CWD und synthetische Envwerte, keine privaten .env-Dateien |
| tiktoken 0.14.0 | Echter ParseContext-Typ / Lecturebuilder | Keinen Encoder/Modellcache nachladen; für PDF ohne Tokenizer zunächst encoder=None |
| PyMuPDF 1.27.2.2, pypdf 6.16.1 | DIY bzw. Splithelper | PyMuPDF in E vorhanden; pypdf fehlt; nur kleine synthetische Dateien |
| Docling 2.129.0, Core 2.97.2, RapidOCR 3.9.2, Pillow 12.3.0 | Converter-/OCRkonfiguration | Großer transitiver Modell-/Torchgraph und mögliche Downloads; kein Installationsvorschlag für diesen Auftrag |

Reproduzierbare Folgeprüfungen nach gezielter Bereitstellung gecachter Wheels:

1. In eigener Umgebung und leerem CWD den vorhandenen Probe erneut ausführen.
   Es genügt nicht, nur das erste fehlende Paket zu installieren und den Rest des
   Graphen als funktionsfähig zu melden. Keine echten Credentials bereitstellen.
2. Mit python-docx ein DOCX mit Überschrift, zwei Absätzen und 2x2-Tabelle unter
   eigener Tempwurzel speichern. `read_docx_text`, `extract_docx` und
   `list(read_docx_tables(...))` **ohne injiziertes Document** aufrufen; aktuell
   ist der NameError reproduzierbar. Danach lokale Importreparatur separat mit
   exakten Text-/Tabellenassertions gegen dasselbe synthetische Dokument prüfen.
3. Strukturierter DOCX-Parser: zuerst echter Vollimport (aktuell weitere
   Annotation-/Recordprobleme), dann ParseContext(text_type="docx", encoder=None),
   echte GeneralSettings/ParseSettings und synthetischen Logger verwenden.
   Parser und Enricher dürfen nicht durch Fakes ersetzt werden; fehlende Bindungen
   sind Fehler, keine Skips.
4. DIY-PDF: vorhandene synthetische PDFfixture wiederverwenden; local_path und
   file_path ausdrücklich gleich setzen, parser_backend="diy" und benötigte PDF-
   Klassifikationskonfiguration explizit wählen. Vollimport, Extract, Postprocess
   und Assemble getrennt prüfen. Der eager Doclingimport ist vorher als eigene
   Dependencyentscheidung zu lösen, keine großen Modelle dafür herunterladen.
5. Docling/OCR erst mit ausdrücklich vorbereitetem lokalem SDK-/Modellcache und
   gesperrtem Netz testen; die normale Converterkonfiguration deaktiviert OCR,
   die Bildkonfiguration aktiviert RapidOCR. Keine automatische Formel-/OCR-
   oder Backendfreigabe aus den injizierten MAINT-04-Tests ableiten.

## Restrisiken und offene Entscheidungen

Kein neuer Legacy-Produktcodefix: Ohne echte passende SDKfixture wäre die kleine
DOCX-Importänderung unvollständig validiert. Vollständiger DOCX-, DIY-, Docling-,
OCR-, TXT-, URL-/Medium-, interaktiver Legacy- und Media-/LLMpfad bleiben offen.
Die fehlenden Symbole brauchen jeweils einen geklärten Aufrufervertrag; insbesondere
keine neue `RunSettings`-Semantik als Nebenreparatur. Isolation/Guardian/SQLite/
Hardlinkpolicy aus MAINT-03B bleiben unverändert und separat zu bewerten.
