# MAINT-04 – Inventar der Parsing-Konfiguration

Stand: 25.10.2026. Basis `aafba19d549316300a79da37f0ab5f9224d82d37`
(MAINT-03B), davor `6b397eb` (MAINT-03), davor `e682752` (damaliger
`origin/master`). Arbeitsbranch `refactor/maint04-parsing-config` im zugewiesenen
Worktree `Personal_Assistant-maint04`. C26 bleibt **HOLD**.

Gelesen: [AGENTS.md](../../AGENTS.md), [Architektur](../architecture.md),
[Workflowarchitektur](../workflows/architecture.md), alle fünf
[MAINT-03-Berichte](maint03_legacy_inventory.md) einschließlich Architekturreview,
Risikomatrix, Modernisierungsplan und Validierung sowie alle vier
[MAINT-03B-Berichte](maint03b_validation.md) einschließlich Profile, Fehleranalyse
und Restrisiken. Historische Cleanupakten unter `docs/audit/maint04` bleiben
unverändert. Dies ist der Parsing-Codeauftrag.

## Methode und Belege

Versionierte Python-/YAML-Dateien wurden mit `rg`, AST und tatsächlichen
Aufrufstellen untersucht. Laufzeitvergleich unter Pydantic **2.13.4** (Rootlock)
und **2.14.1** (MAINT-03B-Offlineumgebung), jeweils Python 3.12.12.
Keine Aussage über sämtliche zukünftigen Versionen aus `pydantic>=2.13.3`.

Die vor dem Produktivrefactoring erzeugte, danach unveränderte
[Baseline](../../tests/fixtures/parsing_config/maint03b_contracts.json) enthält
für **beide Familien × 21 Klassen** sämtliche geerbten Feldnamen/Annotationen,
Requiredstatus, Default bzw. Factory, Aliases, Modellkonfiguration, vollständige
Defaultpayloads und SHA-256 der Validierungs- und Serialisierungsschemas.
Die Hashes verwenden `json.dumps(schema, sort_keys=True)` mit Standardseparatoren.
Die Datei wurde gegen die expliziten Feld-/Defaultunterschiede geprüft; bestehende
Workflow-Snapshots wurden weder neu erzeugt noch verändert.

`config_parsing` wird wirklich importiert. `config` wird für die Modellprüfung aus
seinen **echten unveränderten Klassendeklarationen** inklusive Typaliasen und dem
neuen gemeinsamen Import kompiliert; Envklassen/-instanzen werden ausgelassen.
Das ist keine Simulation von Pydantic, aber auch kein vollständiger Import der
Legacyanwendung. `pydantic_settings`, `tiktoken`, `returns`, NumPy, Pandas,
python-docx und Docling fehlen in den verwendeten schlanken Umgebungen.
Private `.env`-/Benutzerkonfigurationen und gespeicherte Produktivdaten wurden
nicht gelesen. Externe dynamische Plugins sind nicht abschließend inventarisierbar.

## Matrix der 21 Namen

L = `src.core.config`, P = `src.core.config_parsing`.
Kategorien: **1** gleiche Klasse samt Semantik; **2** gleiche Struktur, andere
nominale Identität; **3** Default-/Factoryabweichung; **4** Feld-/Typabweichung;
**5** Validierungs-/Serialisierungsabweichung; **6** dynamische Nutzung ungeklärt.
Keine Klasse erfüllt familienübergreifend Kategorie 1. Kategorie 6 bleibt als
allgemeine externe Nutzungsgrenze bestehen, nicht als belegter Aufrufer.

| Name | Vorher | Laufzeitbefund | Umsetzung |
| --- | --- | --- | --- |
| ParseFileSettings | 2 | gleiche Defaults/Schema, gegenseitige Instanzablehnung | gemeinsame FileFields, zwei öffentliche Klassen |
| ParseDOCXSettings | 2 | eigener Name, familienintern ParseFileSettings | gemeinsame DOCXFields plus lokale Basisklasse |
| ParseHTMLSettings | 2 | bool-/str-Factories | gemeinsame HTMLFields plus lokale Basisklasse |
| ParseMDSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; erbt gemeinsame Dateifelder |
| ParseNotebookSettings | 2 | str-Factory | gemeinsame NotebookFields plus lokale Basisklasse |
| ParsePDFSettings | 3, 4, 5 | drei Flags nur P; extraction_model Default/Factory und Schema unterscheiden sich | eigene Felddefinitionen beider Varianten erhalten |
| ParsePlainTextSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame Dateifelder |
| ParseURLSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame Dateifelder |
| ParseWikiSettings | 2 | Literals, Listen, nullable Queries | gemeinsame WikiFields plus lokale Basisklasse |
| GeneralFileSettings | 2 | extraction_tags-Listenfactory | gemeinsame GeneralFileFields |
| GenDOCXSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenHTMLSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenMDSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenNotebookSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenPDFSettings | 2 | int-/float-Factories, keine Bereichsvalidatoren | gemeinsame PDFGeneralFields plus lokale Basisklasse |
| GenPlainTextSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenURLSettings | 2 | keine eigenen Felder | nominale lokale Unterklasse; gemeinsame GeneralFileFields |
| GenWikiSettings | 2 | zwei leere Headerstrings | gemeinsame WikiGeneralFields plus lokale Basisklasse |
| ChunkSettings | 2 | extra=forbid, nullable Modellliterale | gemeinsame ChunkFields, getrennte öffentliche Identitäten |
| GeneralSettings | 2 | gleiches JSON/Schema, **verschiedene verschachtelte Klassen/Factories** | gemeinsame GeneralFields; lokale acht Modellbindungen erhalten |
| ParseSettings | 4, 5 | nur L: name_log/name_logfile; PDFs verhalten sich verschieden | beide vollständigen Verträge und lokale Factories erhalten |

Damit sind die Feldquellen der **19 strukturell gleichen Klassen** konsolidiert,
nicht deren öffentliche Pythonidentitäten. Zehn schlichte private Pydantic-
Feldbasen ersetzen doppelte nichtleere Deklarationen. Die neun leeren nominalen
Unterklassen pro Familie bleiben zur Typkompatibilität bestehen. GeneralSettings
behält seine acht lokalen Typ-/Factorybindungen. Keine dynamische Klassenfactory.

## Felder, Defaults, Validierung

Alle Felder aller 21 Klassen sind **nicht required**. Auslassen konstruiert den
Default; explizites `null` ist nur bei nullable Annotationen zulässig. Keine
Dataclass und kein Enum in diesen beiden 21er-Familien. Keine eigenen Field-/
Modelvalidatoren, Serializer, Aliasgeneratoren oder Feldaliases. Es gelten
Pydantics normale nichtstrikte Typkonvertierungen; etwa numerische Strings zu
int/float und `"false"` zu bool. Ungültige Literals werden abgelehnt. Negative
Retry-/Tokenwerte sind bislang nicht begrenzt und werden hier nicht normalisiert.

| Deklaration | Eigene Felder und Defaults (geerbte Felder kommen hinzu) |
| --- | --- |
| ParseFileSettings | save: Liste aus False/html/info/md/True/txt = [False]; assemble: Liste md/txt oder None = None; scrape_images: bool=False |
| ParseDOCXSettings | tbl_text_mode: long/brief = brief |
| ParseHTMLSettings | apollo: bool factory bool→False; parser: str factory str→leer |
| ParseNotebookSettings | parser: str factory str→leer |
| ParsePDFSettings, beide | extract_source: list[str] factory list; extraction_model: str, L Default leer/P factory str; extract_text_info=False; extract_graphics=False; percentiles: list[float] factory list |
| ParsePDFSettings, nur P | classify_header_footer=True; classify_foot_notes=True; classify_headings=True |
| ParseWikiSettings | query/query_time: str oder None=None; query_param: page_title/page_id=page_id; page_id: list[int] factory list; page_title: list[str] factory list; language: en/de=en; max_retries: int=3 |
| GeneralFileSettings | extraction_tags: list[str] factory list |
| GenPDFSettings | y_gap_words, x_gap_words, y_gap_line, heading_threshold, foot_note_thresh, start_tol: int factory int→0; width_thresh, up_down_thresh, left_right_thresh: float factory float→0.0 |
| GenWikiSettings | header_referer/header_accept: str=leer |
| ChunkSettings | container_types: untypisierte list factory list; spacy_language: de_core_news_sm/None=None; max_tokens, overlap_sentences, batch_size: int factory int; transformer_model: all-MiniLM-L6-v2/paraphrase-multilingual-MiniLM-L12-v2/intfloat/multilingual-e5-base/None=None |
| GeneralSettings | txt_elements/md_elements: list[str] factory list; docx/html/json_nb/md/pdf/plain_text/url/wiki: jeweilige lokale Gen*-Modellfactory |
| ParseSettings, beide | llm_model: str factory str; url_path: list[str] oder None=None; file_name: str oder None=None; file_id: int factory int; page_range: list[int] oder all=all; acht lokale Parse*-Modellfactories |
| ParseSettings, nur L | name_log/name_logfile: str factory str→leer |

Die neun leeren Unterklassen haben keine zusätzlichen Felder. Extra-Fields werden
bei ParseSettings, GeneralSettings und ChunkSettings **verboten**, bei den
Datei-/Generaldateimodellen standardmäßig **ignoriert**. Deshalb verwirft L die
classify-Flags und beide Varianten ignorieren historische Wiki-Felder `parser`
und `article_to_parse`. Das ist erhaltenes Verhalten, keine neue Migrationsregel.
Settings sind veränderlich und validieren Zuweisungen nicht. Instanzdefaults
einschließlich Listen und verschachtelten Modellen bleiben voneinander getrennt.
Manipulation von gemeinsam geerbten Klassenfeld-Metadaten ist kein freigegebener
Erweiterungspunkt; siehe [Kompatibilitätsgrenzen](maint04_compatibility_matrix.md).

`model_validate`, `model_dump`, `model_validate_json`, `model_dump_json` und beide
`model_json_schema`-Modi bilden die relevanten öffentlichen Pydantic-v2-APIs.
Factorydefaults fehlen teils im Schema, obwohl dieselben Werte serialisiert
werden: Ls `extraction_model` besitzt ein Schema-Default `""`, Ps Factory nicht.

## Typalias-, Kontext- und Modellgrenzen

| Definition | Befund / Abgrenzung |
| --- | --- |
| L.ParseSettings_all | Annotated-Union von HTML/Notebook/MD/PDF/PlainText/URL/Wiki, discriminator meta_type |
| L.RunSettings | ParseSettings_all oder ChunkSettings, discriminator meta_type |
| P.RunSettings | direkte Union der sieben Dateimodelle plus ChunkSettings mit demselben Discriminator |
| beide RunSettings | TypeAdapter scheitert bereits auf Basis mit PydanticUserError: Varianten haben kein meta_type; kein nachgewiesener echter TypeAdapter-Aufrufer; keine Änderung am gespeicherten Format zur Reparatur |
| memory_parsing.PARSER_BACKEND | StrEnum DIY=diy, DOCLING=docling; kein Enumfeld in den 21 Settingsklassen |
| memory_parsing.ParseContext | BaseModel, arbitrary_types_allowed und validate_assignment=True; ignoriert Extras; acht Dateitypen plus None, doc_kind regulatory/commentSOP/lecture; local_path Path factory Path; save_folder/save_name str oder Path factory str; IDs str-Factories, header dict-Factory, Backend/Encoding nullable; drei P-Settingsfactories |
| core.memory.AppSession | Laufzeit/Logger/Encoding/Envstatus, L-Settings und separater P-ParseContext; keine Zusammenlegung |
| core.memory_sop | L-Settingsimporte im SOP-Laufzeitkontext; keine Modellmigration |
| core.memory_lecture.LectureContext | Laufzeit für Lecture-/Transcript-/Knowledge-Orchestrierung, kein dritter gleichnamiger Parsingvertrag |
| model_materials.materials.ParserConfig | unabhängiger eingefrorener DiscoveryModel-Vertrag, extra=forbid; name html/pdf/code/image, version 1/2; max_bytes=16 MiB (1 Byte..64 MiB), max_pages=100 (1..500), max_blocks=20000 (1..50000), max_images=100 (0..500), timeout=20 (0..120, exklusiv 0, endlich), memory_mb=1024 (256..4096); after-Validator erlaubt v2 nur HTML/PDF; config_id aus model_dump_json gehasht |
| weitere Materialmodelle | MaterialPlan/NormalizedDocument/ArtifactReceipt binden ParserConfig; Location/Block/ImageArtifact sind Outputs/Locatoren, keine Settingsduplikate |
| utils.docling_helper | lokale PdfPipelineOptions/RapidOcrOptions und gecachte Converter; OCR aus im Dokumentpfad, enrichment explizites bool; Bildpfad separat OCR an, 90s Timeout; SDK-eigene Modelle, keine zweite Repository-Konfigfamilie |
| core.config übrige Klassen | FolderEnvVars/AgenticEnvVars mit globaler Initialisierung; MLOpsEnvVars/OrganizerEnvVars Loader; NIRSettigs und weitere Domainmodelle außerhalb Parsing; unverändert |
| core.config_transcribe/config_knowledge | TranscribeSettings, DownloadSettings, RecordingSettings, ScreenshotSettings, TranscriptionBackend und KnowledgeSettings gehören zu Nachbarstufen; keine Parsingduplikate |
| model_parsing/base_classes_parsing | 51 Element-/Meta-/Outputmodelle, line_types/container_types/doc_container diskriminierte Outputaliase; nicht Settings |
| model_parsing/classes_html_parsing, data_classes_wiki | HTML-Knoten und Wiki-Response-/Metamodelle; keine Parsingkonfigurationen |
| model_parsing/__classes_pdf_parsing | historischer auskommentierter Entwurf, keine aktiven Klassendeklarationen |

ParseContext hat standardmäßig doc_kind=regulatory und keinen gewählten Backend.
Sein arbitrary Encoding ist ein Laufzeitobjekt, kein JSON-Schema-Vertrag. Mit
einem injizierten beliebigen Encodingtyp wirft die echte Klassendeklaration bei
model_json_schema PydanticInvalidForJsonSchema (IsInstanceSchema); die 42
Settingsschemas sind davon unabhängig. Kein behauptetes vollständiges Context-
Schema mit dem hier nicht installierten Tokenizer.

## Verwendung und Persistenz

| Pfad | Tatsächliche Konfigurationsverwendung / Grenze |
| --- | --- |
| core/memory.py, memory_sop.py; frontend/pages/D_p1_pca.py | L-Imports; globale Session bzw. Streamlit-Legacyeinstieg |
| core/memory_parsing.py | P-Imports, P-Factories und strikte Instanzannahme im Kontext |
| tools_lecture/process_lecture.py | P ParseSettings/GeneralSettings, load_yaml_config cfg_parsing/cfg_general; build_document_parse_context; anschließende Backendwahl bleibt separat |
| utils/dict_helper.py | L-Imports für Annotationen; load_yaml_config nutzt tatsächlich übergebenes cls.model_validate; load_dict nutzt BaseModel-Prüfung plus model_validate für Dict/Liste, ansonsten Dataclasses; save_dict schreibt JSON über make_json_safe |
| model_parsing/base_extractor, base_classifier, base_assembler | Dataclasses lesen dateispezifische Teilmodelle über get_file_config/getattr; speichern Kontextpfade und -namen; keine persistenten Settingsklassen |
| model_parsing/pdf_extractor, pdf_merger, pdf_cleaner, pdf_classifier | Kontextsettings, PDF-Extraktions-/Layoutfelder und classify-Flags; page_range bleibt unverändert einschließlich Reihenfolge/Indexsemantik |
| model_parsing/docx_extractor | Dataclass, tbl_text_mode steuert brief/long; echte Extraktion benötigt weiterhin fehlende Document-/Paragraph-/Table-Bindungen und optionale Pakete |
| model_parsing/html_extractor, url_extractor, notebook_extractor, text_extractor | Dataclasses binden HTML-/Notebook-/Textsettings über Basis oder eigene Initialisierung; externe URL-/Bildpfade bleiben ungetestet |
| model_parsing/apollo_extractor.ApolloCleanExtractor, notebook_extractor.NoteBookCleanExtractor | Unterklassen von HTMLCleanExtractor ohne erneuten Dataclass-Dekorator; Apollo übernimmt dessen Settingsbindung, Notebook bindet json_nb und general_settings.json_nb.extraction_tags selbst; nb_language=field(default_factory=str) ist keine neu verarbeitete Dataclass-Felddefinition |
| model_parsing/feature_enricher | Dataclass mit ParseContext/Encoding; Laufzeit-Anreicherung, kein neuer persistierter Vertrag |
| model_parsing/wiki_client, wiki_classifier, wiki_assembler | Query-/Header-/Klassifikations-/Renderkonfiguration, teils vorhandene Legacyprobleme |
| model_parsing/document_assembler, base_cleaner, text_classifier, pdf_assembler | zusätzliche Laufzeitdataclasses/Renderer; kein dritter Settingsvertrag |
| tools_parsing/parse_document.py | DIY nur PDF, DOCLING eigener Converterpfad; Doclingziel source.parent.parent/parsed, Name stem_docling.json und stem_docling.md |
| src/run_st_pdf_extract.py; tools_parsing/extract_*.py | Legacy-/CLI-/UIpfade über Context/AppSession; fehlende session_state-/Importhelfer bleiben offen, kein behaupteter E2E-Smoke |
| tools_knowledge/find_knowledge, rebuild_knowledge, postprocess_visual; tools_rag/chunk | benachbarte Knowledge-/Visual-/Chunk-Laufzeiten und globale Session; keine direkten neuen Configimporte; große SDKketten nicht ausgeführt |
| tools_materials/processing, parse_html, parse_pdf, parse_code, code_import, week | unabhängiger ParserConfig-Vertrag, Hash-/Receipt-/Version-/Ressourcenregeln; keine direkte Abhängigkeit von den 21 Klassen |
| scripts/cs50_materials.py, cs50_lecture.py und Job-/Workflowrunner | moderne explizite Material-/Lectureverträge; synthetische vorhandene CLItests prüfen diese separate Grenze |

Die Datei-/Gen*-Blattmodelle werden im Src-Bestand überwiegend über die acht
Defaultfactories/Typannotationen der jeweiligen Wurzelklasse erreicht; es wurde
kein allgemeiner direkter Blattmodell-Importaustausch vorgenommen. Zusätzliche
Legacy-UI-Aufrufer sind `frontend/pages/B_p0_ETL_html.py` (Apollo-Option und
ApolloCleanExtractor), `B_p1_ETL_pdf.py` und `B_p3_ETL_json_nb.py` (Notebook).
`_prototypes/run_text_extraction.py` besitzt ebenfalls einen Notebookeinstieg;
historische Prototypen sind kein Nachweis einer heute freigegebenen Pipeline.

Vier versionierte Konfigurationsdateien: `configuration/cfg_parsing.yaml`,
`cfg_general.yaml`, `streamlit_run.yaml`, `streamlit_general.yaml`. cfg_parsing
setzt classify_header_footer=False; L ignoriert das, P behält es. streamlit_run
enthält Loggingfelder und wird von P abgelehnt. Generaldateien unterscheiden sich
unter anderem bei PDF-Abständen; keine automatische Vereinheitlichung.
Zusätzliche [synthetische gespeicherte JSON-Payloads](../../tests/fixtures/parsing_config/legacy_payloads.json)
repräsentieren historische Formen, sind ausdrücklich **kein Produktionskorpus**.
Die tatsächliche externe Nutzung, private Payloads und dynamische Klassenfeld-
Mutationen bleiben ungeklärt. Sie rechtfertigen keine automatische Migration.

## Dataclass-Inventar der Legacy-Parser

Statische eigene Annotationen und direkte Kontextbindungen; geerbte Felder gelten
zusätzlich. `field(init=False)` ist Laufzeitzustand, kein persistierter Konfigdefault.
Diese Klassen wurden nicht zu Pydantic-Settings umgebaut.

Die Tabelle ist ein statisches Inventar, keine erfolgreiche Initialisierung
aller Dataclasses: etwa BaseCleaners `FeatureEnricher()`-Ausdruck und die
WikipediaClient-Zugriffe auf alte Kontextattribute bleiben gesondert zu prüfen.
Sie werden nicht durch neue Defaultwerte oder erfundene Kontextaliases kaschiert.

| Dataclass | Eigene Annotationen / Defaultausdrücke | Kontextbindungen |
| --- | --- | --- |
| base_assembler.BaseAssembler | `parse_context: Any`; `text_type: str = field(init=False)`; `logger: logging.Logger = field(init=False)`; `infos: list = field(default_factory=list)`; `assemble_elements: dict = field(default_factory=dict)`; `last_heading: list = field(default_factory=list)` | `self.text_type = self.parse_context.text_type`; `self.save_folder = self.parse_context.save_folder`; `self.save_name = self.parse_context.save_name`; `self.general_config = get_file_config(self.parse_context.general_settings, self.text_type)`; `self.assemble_config = get_file_config(self.parse_context.parse_settings, self.text_type)`; `self.assemble_elements = {'txt': get_file_config(self.parse_context.general_settings, 'txt_elements'), 'md': get_file_config(self.parse_context.general_settings, 'md_elements')}` |
| base_classifier.BaseClassifier | `parse_context: ParseContext`; `text_type: str = field(init=False)`; `general_config: GeneralSettings = field(default_factory=GeneralSettings, init=False)`; `classify_config: GeneralSettings = field(default_factory=GeneralSettings, init=False)`; `logger: logging.Logger = field(init=False)`; `bullets: set[str] = field(default_factory=lambda: {'•', '▪', '●', '‣', '◦', '–'})` | `self.text_type = self.parse_context.text_type`; `self.general_config = get_file_config(self.parse_context.general_settings, self.text_type)`; `self.classify_config = get_file_config(self.parse_context.parse_settings, self.text_type)` |
| base_cleaner.BaseCleaner | `enricher: FeatureEnricher = field(default_factory=FeatureEnricher())`; `extract_config: dict = field(default_factory=dict)`; `doc_name: str = field(default_factory=str)` | geerbter/imperativer Laufzeitzustand |
| base_extractor.BaseExtractor | `parse_context: ParseContext`; `text_type: str = field(init=False)`; `enricher: FeatureEnricher`; `logger: logging.Logger = field(init=False)` | `self.text_type = self.parse_context.text_type`; `self.save_folder = self.parse_context.save_folder`; `self.save_name = self.parse_context.save_name`; `self.doc_name = self.parse_context.run_id`; `self.extract_config = get_file_config(self.parse_context.parse_settings, self.text_type)`; `self.general_config = get_file_config(self.parse_context.general_settings, self.text_type)` |
| document_assembler.DocumentAssembler | `infos: list = field(default_factory=list)`; `doc_name: str = field(default_factory=str)`; `last_heading: list = field(default_factory=list)` | `self.logger = run_context.logger`; `self.save_folder = run_context.save_folder`; `self.assemble_config = run_context.run_settings` |
| docx_extractor.DOCXCleanExtractor | `mode: Literal['brief', 'long'] = 'brief'`; `bullets: list = field(default_factory=list, init=False)` | geerbter/imperativer Laufzeitzustand |
| feature_enricher.FeatureEnricher | keine eigenen Klassenfelder | `self.encoder = parse_context.encoder`; `self.text_prep_config = parse_context.parse_settings` |
| html_extractor.HTMLCleanExtractor | `req_session: requests.Session \| None = field(default=None)` | `self.header = self.parse_context.header` |
| pdf_assembler.PDFAssembler | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| pdf_classifier.PDFClassifier | `page_attributes: dict[str, Any] = field(default_factory=dict)` | geerbter/imperativer Laufzeitzustand |
| pdf_cleaner.PDFCleaner | keine eigenen Klassenfelder | `self.clean_config = parse_context.parse_settings` |
| pdf_extractor.PDFCleanExtractor | keine eigenen Klassenfelder | `self.doc_name = parse_context.run_id`; `self.extract_config = parse_context.parse_settings.pdf`; `self.page_range = parse_context.parse_settings.page_range`; `self.general_config = parse_context.general_settings.pdf`; `self.save_folder = parse_context.save_folder`; `self.save_name = parse_context.save_name`; `self.text_type = parse_context.text_type` |
| pdf_merger.PDFMerger | keine eigenen Klassenfelder | `self.merge_config = parse_context.parse_settings.pdf`; `self.general_config = parse_context.general_settings.pdf` |
| text_classifier.TXTClassifier | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| text_extractor.TXTCleanExtractor | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| text_extractor.MDCleanExtractor | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| url_extractor.URLCleanExtractor | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| wiki_assembler.WikiPageAssembler | keine eigenen Klassenfelder | geerbter/imperativer Laufzeitzustand |
| wiki_classifier.WikiClassifier | `page_attributes: dict[str, Any] = field(default_factory=dict)` | geerbter/imperativer Laufzeitzustand |
| wiki_client.WikipediaClient | `url: str \| None = field(default=None)`; `req_session: requests.Session \| None = field(default=None)` | `self.now = parse_context.parse_settings.wiki.query_time or parse_context.timestamp or datetime.now().strftime('%Y-%m-%d_%H-%M-%S')`; `self.wiki_config = parse_context.parse_settings.wiki`; `self.query_param = parse_context.query_param`; `self.header = parse_context.header`; `self.save = parse_context.save` |
