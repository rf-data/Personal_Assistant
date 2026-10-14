# CS50: Integrationsplan Transcript → Knowledge

## Entscheidung und aktuelle Grenzen

Für Knowledge ist **englisches offizielles SRT die primäre Quelle**, TXT nur eine
ausdrücklich angeforderte Ergänzung. Kein Video-Download und keine Whisper-
Transkription. Die vollständige Discovery bietet pro logischer Vorlesung genau ein
englisches SRT: 12/10/7/7/9/5 Quellen für `cs50x`/Python/SQL/AI/Web/Cybersecurity.
Diese 50 Links sind anhand der HTML-Provenienz eindeutig zugeordnet; ihre Dateien
sind noch nicht abgerufen oder auf gültige Zeitstempel geprüft.

In diesem Auftrag wurde **nur die Integration analysiert**, nicht die Policy oder
der Lecture-/Knowledge-Runner umgestellt. Aktuelle `six_course_preview.md` bleibt
TXT-first. Der geplante SRT-first-Pfad muss durch eigene Offline-Vertragstests
freigegeben werden, bevor Textabrufe oder später LLM-Verarbeitung aktiviert werden.

SRT ist geeignet, weil `import_srt()` echte Cue-Zeiten und Segmentreihenfolge in
`TranscriptDocument` erhält. `build_transcript_chunks()` verlangt bekannte Start-
und Endwerte für alle Segmente. `import_txt()` setzt diese ausdrücklich auf `None`;
TXT darf deshalb weder Ersatz für fehlendes SRT sein noch in denselben zeitbasierten
Knowledge-Eingabestapel geraten. Keine künstlichen Zeiten oder automatische
Whisper-/Video-Fallbacks. Der separate zeitlose Knowledge-Pfad bleibt ein eigener
späterer Entwicklungsabschnitt.

## Selection-Vertrag

Die bestehende `_choose()`-Rangfolge ist TXT → VTT → SRT → ausdrücklich erlaubtes
Audio. `SelectionPolicy` besitzt derzeit keine Option zum Ändern dieser Text-
Priorität. `require_video=False` und `allow_transcription=False` passen bereits;
`allow_unknown_language=False` muss für den Knowledge-Pfad beibehalten werden.

Vorgeschlagene kleine Erweiterung: ein optionaler Strategie-Schalter an
`SelectionPolicy`, beispielsweise `text_strategy="transcript_first"` als unveränderter
Default und `"timed_knowledge"` als bewusste Aktivierung. Im zweiten Modus wird
nur die bevorzugte Sprache `en` mit `role=subtitles`, `format=srt` gewählt.
VTT-Fallback gehört erst nach gesonderter Zustimmung als explizite Option dazu;
TXT ist niemals ein stiller zeitbasierter Fallback. Keine Qualitäts-/Video-Auswahl
ist für diesen Modus erforderlich; vorhandene Varianten bleiben im Discovery-Graph.

Die bisherige `SelectionDecision` kann die primäre Wahl abbilden:
`purpose=text`, SRT-Kandidat, Aktionen `download, parse_subtitle`, vollständige
Alternativen und Begründung. Die veraltete Warnung „nur VTT unterstützt“ darf erst
für den tatsächlich angebundenen offiziellen SRT-Importer entfernt werden.
Ein separat aufgerufener `select_optional_txt()` kann eine weitere vorhandene
`SelectionDecision` liefern; eine Adapter-Bindung kennzeichnet sie als Supplement.
Es wird kein zweiter Knowledge-Primärinput daraus. Keine neuen Lecture-/Knowledge-
Modelle sind dafür nötig. Falls später eine gemeinsame Preview beide Auswahlen
darstellen soll, ist deren Zweck ausdrücklich zu dokumentieren; alte Defaults und
die bisherige Zwei-Entscheidungs-Struktur dürfen nicht stillschweigend wechseln.

Fehlt ein geeignetes SRT, bleibt die Entscheidung ungewählt und nennt den Grund:
fehlender Link, Sprache unbekannt/abweichend, mehrere gleichwertige Kandidaten oder
mehrere mögliche Vorlesungsbesitzer. Kein willkürliches Sortieren nach URL als
fachlicher Tie-Breaker. Ein vorhandenes TXT darf trotzdem als Supplement angeboten
werden, qualifiziert die Vorlesung aber nicht für zeitbasierte Knowledge.

## Adapter und vorhandene Lecture-Verträge

| Discovery/Selection | Bestehender Zielvertrag | Erforderliche Abbildung |
| --- | --- | --- |
| CourseDiscovery | LectureCourse | originale course_id, Titel, provider `cs50`, source_url; lecture_blocks in Navigationsreihenfolge |
| SectionDiscovery / logische lecture_video-Ressource | lecture_no / lecture_blocks | exakt `0`, `ai`, … als Strings; nicht neu nummerieren oder aus Dateinamen ableiten |
| ausgewählte SRT-ResourceCandidate | LectureDocument | source_url=SRT-URL, file_type=`srt`, foundation, aussagekräftiger Titel, explizite lokale Artefaktpfade |
| optionales TXT | LectureDocument | file_type=`txt`, supplement, eigene Identität/Datei, kein zeitbasierter Knowledge-Task |
| echte Medienangebote | LectureMedia | media_type entsprechend Angebot, media_url tatsächliche Video-/Audio-URL; als Referenz möglich, ohne Download-/Transcribe-Task |
| SRT-SelectionDecision | ResourceTask | vorhandene Aktionen DOWNLOAD und PARSE_SUBTITLE, Inputpfad nach erfolgreichem Abruf; keine TRANSCRIBE-/Frames-Aktion |

Eine SRT-Datei ist **kein** `LectureMedia(media_type="video")`: Das wäre eine
fachlich falsche Nutzung, nur um die heutige Dispatcher-Route zu erreichen.
`LectureDocument` ist als bestehender Dateivertrag ausreichend, allerdings braucht
der CS50-Dispatcher eine eigene Untertitel-Importverzweigung statt Docling.
`LectureScript` wäre ebenso ein vorhandener Textvertrag, beseitigt diese
Dispatcherlücke aber nicht; für SRT/TXT wird konsistent LectureDocument empfohlen.

Benötigte kleine, providerbezogene Funktionen (zukünftige Namen):

1. `adapt_cs50_course(discovery)` erzeugt LectureCourse/Dateireferenzen und erhält
   den vollständigen Discovery-Graph als separate geprüfte Metadaten.
2. `bind_cs50_selection(preview, decisions)` prüft Kurs, Abschnitt, Besitzer und
   Original-URL und erzeugt eindeutige Bindungen zur logischen Vorlesung.
3. `build_cs50_transcript_tasks(bindings, artifact_state)` verwendet die expliziten
   Artefaktpfade und vorhandenen ResourceTask-Typen; kein unscharfer Dateinamenscan.
4. `acquire_cs50_text(binding)` lädt ausschließlich die ausgewählte SRT-/optional
   TXT-Datei nach bewusster Aktivierung; begrenzte Anzahl, Timeout, Größe und Retries.
5. `import_cs50_transcript(binding, raw_path)` verwendet offiziellen Importer und
   exklusives Speichern; prüft anschließend die Knowledge-Eignung.
6. `run_cs50_knowledge_input(binding, normalized_path)` übergibt ausschließlich
   geprüfte zeitbasierte Inputs und nachgewiesene Identitäten an bestehende Funktionen.

## Identität und Provenienz ohne neue Lecture-/Knowledge-Modelle

`LectureResource` hat **kein** resource_id, language oder TranscriptProvenance;
`LectureCourse` hat keine gespeicherten SectionDiscovery-Objekte, `ResourceTask`
keine task_id oder actionweise Fortschrittsfelder. Zusätzliche Constructor-Kwargs
würden keine verlässliche Speicherung solcher Informationen garantieren. Die
Discovery deshalb nicht allein in LectureCourse exportieren und anschließend verwerfen.

Empfohlen ist eine versionierte JSON-Bindung neben Course-/Task-Metadaten. Sie
enthält den unveränderten, mit vorhandenen Discovery-Modellen validierten Graphen
und explizite Zuordnungen von Auswahl, Ressourcen, Aufgaben und Artefakten. Keine
Migration der bisherigen Lecture-Daten und keine neuen Lecture-/Knowledge-Felder
sind für den ersten Adapter nötig.

| Metadatum | Nachweisbare Quelle / Übergabe |
| --- | --- |
| course_id | geprüftes CourseDiscovery.course_id, unverändert bis Knowledge-Dokument |
| Abschnitt / lecture_blocks | SectionDiscovery.key, inklusive `0`/`ai`; Reihenfolge separat erhalten |
| lecture_id | resource_id der logischen Hauptvorlesung, nicht SRT-Dateiname oder YouTube-ID |
| resource_id | resource_id des ausgewählten SRT-/TXT-Kandidaten; vollständige Auswahl-Bindung erhalten |
| source_id | ausdrücklich übergebene ID des SRT-Kandidaten als Quellenidentität; alias zur geprüften resource_id, nicht erfundener Filename |
| transcript_url | exakte ausgewählte SRT-Original-URL |
| language | ausgewählter Kandidat `en`; bei Provenienz-Widerspruch Import/Export abbrechen |
| TranscriptProvenance | official_subtitle, Original-URL, lokale Quelldatei, language, format=srt, tatsächlicher Importzeitpunkt |
| HTML-Provenienz / Qualität / Alternativen | Discovery-Graph und Bindung; TranscriptProvenance bildet Fixture/DOM/context_path nicht vollständig ab |
| raw-/normalized-Hash, Adapterversion | Artefakt-Bindung; Quellen-ID identifiziert den Link, Hash identifiziert dessen konkrete Inhaltsversion |
| Chunk-/Segment-IDs und Start/End | bestehender Importer, Chunker und attach_chunk_provenance, keine Neubildung durch Adapter |

Der offizielle Importer setzt aktuell media_id nicht. Ein späterer Adapter darf
dieses Feld nur aus einer eindeutig geprüften Medienzuordnung ergänzen; keine
Ableitung aus CDN-SRT-URL oder Dateiname. Bei Cybersecurity Woche 0 bleiben mehrere
IDs unaufgelöst; media_id bleibt `None`, Alternativen/Warnung bleiben erhalten.
Auch bei sonst eindeutiger ID ist die Zuordnung zu prüfen, nicht die Bild-/Ton-
Synchronität als bewiesen zu behaupten. `KnowledgeEvidence.source="transcript"`
bezeichnet die Modalität; `TranscriptProvenance.transcript_source="official_subtitle"`
bezeichnet die Herkunft. Beide dürfen nicht ineinander umbenannt werden.

## Wiederverwendbare Funktionen und nachgewiesene Lücken

**Importer:** `import_srt/import_txt/import_vtt` sind lokal, explizit für Sprache und
Original-URL, UTF-8/BOM-fähig und bewahren Cue-Zeiten. `save_imported_transcript()`
schreibt exklusiv mit `x`. Der vorhandene Python-0-Pilot benötigt
`preserve_empty_cues=True`; diese bewusste Option bewahrt gültige stille Cues und
ihre Segmentpositionen, ohne beschädigte Zeitangaben zu akzeptieren.
Das ist kein unkontrolliertes Zusammenführen wiederholter Untertiteltexte.

**Direkter Textdownload:** `download_lecture_resource()` in extract_resources
verwendet Requests, Streaming, Timeout und HTTP-Statusprüfung. Wiederverwendbar ist
dieser Transportansatz, **nicht unverändert die Speicherlogik**: Sie nimmt den
Server-Dateinamen und öffnet mit `wb`, kann damit überschreiben/kollidieren, hat
keine Gesamtgrößengrenze oder atomare Fertigstellung und aktualisiert keine Task-
Provenienz. Ein schmaler sicherer Wrapper sollte einen festgelegten Zielpfad unter
course_root, exklusive/temporäre Datei, Hash und Erfolgspersistenz übernehmen.
Keine Videoplayer-Auflösung nötig; keine yt-dlp-Inspection.

`download_document()` prüft zwar bestehende local_path, benutzt sonst Titel/
lecture_no als Dateiname und `urlretrieve` ohne explizites Timeout; heruntergeladene
Pfade/Status werden nicht zuverlässig in die Ressourcen zurückgeschrieben.
Für CS50-SRT ist das kein fertiger sicherer Downloader. Beide Funktionen wurden
hier nur gelesen, nicht aufgerufen.

**Nicht verwenden:** `acquire_transcript_source()` leitet jede URL zu
`process_youtube_video()` weiter; dieser Weg bevorzugt Deutsch/Englisch, kann
Audio-Fallbacks und Whisper auslösen. `download_subtitles()` fordert VTT an und
liest `requested_subtitles['de']` selbst bei anders übergebenem language. Die
yt-dlp-DownloadSettings haben standardmäßig 20 Retries. Das ist keine passende
Route für einen bereits ausgewählten offiziellen englischen SRT-Link.

**Planner:** SUPPORTED_TRANSCRIPT_SUFFIXES enthält nur `vtt`; SRT wird nicht als
Untertitel erkannt. `get_required_actions()` routet Dokumente zum Document-Parser,
also nicht zum SRT-Importer. `build_resource_tasks()` macht fehlende Pfade zu `[]`,
während `get_transcript_actions()` zunächst auf `None` prüft. JSON wird weitgehend
über Namensheuristiken als Transcript klassifiziert. `get_resource_path()` mutiert
Titel und sucht unscharf nach Namen/lecture_no. Diese Pfade nicht für geprüfte
CS50-Artefaktzuordnung verwenden; ein expliziter CS50-Planner ist kleiner und sicherer
als eine breite Änderung der Loviscach-Heuristiken.

**Processing:** `execute_task()` lädt Transkriptionskonfiguration und konstruiert
einen Provider vor jedem Aktionsdispatch. Der Dokumentpfad kennt DOWNLOAD/
PARSE_DOCUMENT, der Medienpfad PARSE_SUBTITLE mit dem alten VTT-Parser. Dieser
Parser akzeptiert nur VTT, defaultet auf Deutsch und entfernt Textüberlappungen.
Die offizielle SRT-Route muss davor abgegrenzt werden und darf keinen Whisper-
Provider erzeugen. Es reicht ein CS50-Zweig plus Import-/Download-Handler; bisherige
Loviscach-Verarbeitung bleibt unverändert.

**Runner:** `run_lecture_processing()` übergibt aktuell course_root an
`lecture_processing()` und weiter an `execute_task()`, obwohl dieses einen
LectureContext mit lecture_root erwartet. `run_lecture_planning()` hat außerdem
einen Einstieg mit festen Blöcken 1–28 und einem nicht definierten lecture_info.
Der neue CS50-Einstieg muss echte Course-/Context-/Bindings-Daten übergeben und
darf nicht diese Platzhalter übernehmen. Kein numerischer range über Kurswochen.

**Knowledge:** Der aktuelle Runner scannt alle Transcript-JSONs rekursiv und
überspringt anhand des Ergebnisdateinamens. Er konfiguriert Marvin vor dem Laden,
bildet source_id aus dem Dateinamen, setzt lecture_id nicht und leitet media_id nur
aus transcript_url ab (CDN-SRT liefert dabei None). Sprach- und TranscriptProvenance-
Weitergabe sowie deterministische/semantische Ergebnis-Metadaten sind schon vorhanden.
Minimal erforderlich sind optionale, explizite geprüfte Identitätsargumente und
ein Eingabemanifest für CS50, ohne Legacy-Aufrufer zu ändern. Keine Erfindung von
IDs und kein TXT im zeitbasierten Scan. Der bekannte synchrone Marvin-Hänger bleibt
ein separater Blocker für echte LLM-Ausführung, keine Aufgabe dieses Plans.

## Status, Retry und Resume

ResourceCandidate.status `parsed/referenced` beschreibt **HTML-Discovery**, nicht
Download, Import oder Knowledge-Fertigstellung. Die Task-Zustände PENDING/RUNNING/
DONE/FAILED/SKIPPED sind vorhanden, werden im bisherigen Processing nicht als
verlässlicher persistierter, aktionsweiser Resume-Vertrag benutzt.

Für CS50 zunächst eine Aktion pro ResourceTask mit einer externen eindeutigen
Bindungs-ID aus Resource-ID, Aktion, Artefaktversion und Adapterversion. DOWNLOAD
und Import sind getrennte abhängige Schritte. PENDING → RUNNING → DONE erst nach
Dateifertigstellung, Hashprüfung und (bei Import) TranscriptDocument-Validierung.
Bei Fehler FAILED mit verständlichem Grund. Nach Crash ist RUNNING kein Erfolg;
temporäre Datei nicht als Download wiederverwenden. Ohne passende Quelle entsteht
ein diagnostischer ungewählter Selection-Eintrag, keine erfundene ResourceTask.

Resume nur, wenn source_id/resource_id, URL, Sprache, Inhalts-Hash, Version und
Artefaktvalidierung zur gespeicherten Bindung passen. Existenz einer Datei allein
reicht nicht. Bestehendes normiertes JSON nicht überschreiben; widersprüchliche
Versionen separat ablegen oder als Konflikt stoppen. Kein SRT/TXT/Mediendatei-
Fallback nach korruptem SRT ohne ausdrückliche Strategieentscheidung.

Der bestehende `retry_download`-Decorator begrenzt auf drei Versuche; seine
Fehlerklassifikation berücksichtigt Builtin-Timeout/ConnectionError bzw.
exc.status_code. Requests-Ausnahmen/HTTPError.response brauchen einen kleinen
expliziten Übersetzer, damit die beabsichtigten Retries tatsächlich greifen.
Nur transiente Timeout/429/5xx wiederholen, Gesamtdeadline und Versuche begrenzen;
404, ungültiges SRT, Provenienzkonflikte und Hashkonflikte nicht automatisch
wiederholen. Kein Rückgriff auf die 20 yt-dlp-Retries.

Knowledge hat bereits einen Prompt-/Input-/Modell-/Schema-basierten Chunk-Cache und
`retry_llm_call` mit maximal vier Versuchen. Das ist weder Download-Resume noch
ein Kostenlimit für vollständige Kurse. Für CS50 später explizit begrenzte Quellen,
Chunks, Aufrufe und Retry-Budgets sowie Quellen-/Artefaktvalidierung bei Resume.
Diese kostenpflichtige Ausführung bleibt standardmäßig deaktiviert.

## Kleine PRs mit klaren Abnahmekriterien

| PR | Umfang | Abnahme / Offline-Tests |
| --- | --- | --- |
| 1 — vollständige Fixture-Coverage (in diesem Auftrag umgesetzt) | 29 Wochen, 63 SHA-256-Einträge, Loaderprüfung, aktuelle Berichte, historische Regression | 50/50 geparst, keine erfundenen Quellen, alte IDs/Dateien erhalten, Hash-Manipulation erkannt |
| 2 — reine Knowledge-Selection | optionaler timed_knowledge-Modus, SRT-first, separater optionaler TXT-Supplement-Plan; unveränderte Defaults | 50 englische SRT-Angebote, null Video/Whisper, fehlende Sprache/SRT/Mehrdeutigkeit klar, Reihenfolge stabil |
| 3 — reiner Lecture-Adapter | LectureCourse/Document/Media-Referenzen und versionierte Auswahl-/Provenienz-Bindung, Task-Plan ohne Ausführung | `0`/`ai`, SRT-Resource-ID vs lecture_id, keine Metadatenverluste, JSON-Roundtrip, doppelte URLs/Wochen/Varianten |
| 4 — kontrollierter Textabruf und offizieller Import | direkter SRT/TXT-Transport, exklusive Artefakte, begrenzte Retries/Status/Resume, CS50-Processing-Dispatch vor Provider-Erstellung | fake HTTP, 404/429/Timeout, Teil-Datei/Crash, Hash-Konflikt, korruptes SRT, UTF-8/BOM/stille Cues, null yt-dlp/Whisper/LLM |
| 5 — explizite Knowledge-Eingabebindung | kleine optionale Identitätsübergabe und CS50-Eingabemanifest im vorhandenen Runner; Legacy-Verhalten unverändert | importiertes SRT → echter Chunker → synthetische Aussagen/Formeln → JSON → echte deterministische Consolidation; source_id/lecture_id/Sprache/Provenienz/Segmentzeiten vollständig |
| 6 — separat autorisierte produktive Probe | erst nach erfolgreicher isolierter Marvin-Initialisierung, begrenzter einzelner CS50-Pilot mit explizitem API-Opt-in | Default offline, Deadline/Prozessgruppe, Aufruf-/Retrybudget, Tokenprotokoll; keine komplette Kursausführung und kein automatischer Merge |

PR 4 kann zunächst vollständig mit lokalen/synthetischen Dateien und Fake-HTTP
geprüft werden. Ein echter Textabruf benötigt eine spätere ausdrückliche
Aktivierung; er ist in diesem Auftrag nicht freigegeben. PR 5 benötigt keine echten
LLM-Aufrufe für seinen Datenvertrag. Die vorhandenen source_id-/Provenienz-Modelle
und Consolidation-Funktionen werden wiederverwendet, nicht erneut umgestellt.

Bis PR 5 ist die **Quellenvorbereitung vollständig**, die automatisierte
Transcript→Knowledge-Ausführung aber noch nicht produktionsreif. Die Roadmap
unterscheidet diese beiden Zustände ausdrücklich.
