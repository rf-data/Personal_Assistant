# CS50-Pipeline: Abschlussaudit

Stand: 14. Oktober 2026. Geprüfter `origin/master` nach Fetch:
`571874524b8b976b68f78668a4274896629229ec`. Analyse im isolierten
Worktree auf `docs/cs50-completion-audit`. Änderungen ausschließlich an diesem
Bericht und [dem Abschlussplan](cs50_pipeline_completion_plan.md).

## Ergebnis und Beweisgrenzen

Die sechs Kurse sind vollständig **entdeckt und geplant**, nicht vollständig
mit echten Quellen und echten Knowledge-Ergebnissen verarbeitet. Der kontrollierte
SRT-Pfad einschließlich verifizierter Wiederaufnahme ist implementiert und offline
für alle 50 Quellen/100 Aktionen getestet. Der Knowledge-Pfad ist dagegen ein
bewusst begrenzter Python-Woche-0-Pilot: ein Input, höchstens zwei Chunks.

Eine vollständige Vorlesung, ein kompletter Kurs und ein sechs-Kurse-Knowledge-
Batch sind über den CS50-Einstieg derzeit **nicht ausführbar**. Ein Shell-Loop
über Pilot-Aufrufe würde fehlende globale Budgets, Resume und Gesamtvollständigkeit
nicht ersetzen und wird hier nicht als produktiver Lösungsweg empfohlen.

Die vollständige Suite auf diesem Stand: **374 bestanden, 9 fehlgeschlagen,
0 Setupfehler, 4 Skips**, 387 Fälle, 299,04 s. Alle Discovery-, Selection-,
Adapter-, Fake-Executor-, CS50-Binding-, Legacy-/segment_v1- und Lazy-Import-
Regressionen bestehen. Kein echter Download oder LLM-Aufruf wurde gestartet.

Nachweisstufen im Folgenden:

- **O**: aktuell durch Offline-Tests mit echten Kernfunktionen nachgewiesen.
- **H**: historischer echter Pilot laut vorhandenen Berichten; kein erneuter
  Zugriff auf maschinenlokale produktive Ergebnisse in diesem Audit.
- **T**: implementierte technische Fähigkeit, deren vollständiger realer
  Betriebsumfang hier nicht nachgewiesen wurde.
- **F**: fehlend oder für den gewünschten Betriebsumfang unvollständig.

## Git-/GitHub-Stand

GitHub meldet #24 und #25 als geschlossen und in master gemergt. Damit sind
SDK-freie deterministische Importe und der gemeinsame Transcript-Metadatenvertrag
integriert. Für #26 antwortet die Repository-PR-API mit 404; ein abrufbarer PR
oder dessen Integration ist aktuell nicht belegt. Die zwei betreffenden
Weitergabetests scheitern weiterhin. #26 ist hier eine Folgeaufgabe, kein als
offen vorausgesetzter GitHub-Status.

Ältere Aussagen aus `post_merge_audit.md` über fehlende versionierte HTMLs,
acht maschinenabhängige Pilotfehler, vier Lazy-Import-Fehler und neun fehlende
Konfliktprüfungen sind durch #21–#25 überholt. Die verbleibenden Probleme werden
unten getrennt aufgeführt. Es wurde kein PR gemergt, geschlossen oder rebased.

## Quellen- und Planinventar

Quelle: `docs/course_sources/cs50/manifest.json`, 63 hashgebundene lokale HTMLs:
sechs Indizes, 50 Wochenseiten, sieben zusätzliche historische Detail-Fixtures.
`regression_manifest.json` hält den früheren 34-Seiten-Stand. Kein Live-Crawl;
heutige HTTP-Erreichbarkeit aller URLs ist deshalb nicht bestätigt.

| Interne ID | Abschnitte / Hauptvorlesungen | Englische SRT-Bindungen | Tasks |
|---|---:|---:|---:|
| cs50x | 12 | 12 | 24 |
| cs50_python | 10 | 10 | 20 |
| cs50_sql | 7 | 7 | 14 |
| cs50_ai | 7 | 7 | 14 |
| cs50_web | 9 | 9 | 18 |
| cs50_cybersecurity | 5 | 5 | 10 |
| Gesamt | 50 | 50 | 100 |

Die tatsächliche erste ID ist **cs50x**, nicht cs50_x. Woche `0` und Schlüssel
`ai` bleiben Strings. Die Snapshots bieten 74 SRT- und 74 TXT-Kandidaten,
davon jeweils 50 englische; zusätzliche Sprachfassungen liegen bei CS50x.
VTT ist im Snapshot-Angebot nicht vorhanden. Ressourcentypen umfassen Video,
Audio, Notes, Slides, Source Code und Aufgaben-/Begleitverweise; sie werden im
SRT-first-Pfad nicht automatisch heruntergeladen oder verarbeitet.

`cs50_lecture_plan.v1.json` ist portable und besitzt 50 getrennte Lecture-/SRT-
Bindungen sowie 100 eindeutige Tasks. Original-Discovery und Medienvarianten
sind darin enthalten. Cybersecurity Woche 0 bleibt bei nicht eindeutigen Video-
IDs `media_id=None`; das verhindert keine SRT-Verarbeitung.

## Vollständiger Datenweg und produktive Einstiegspunkte

```mermaid
flowchart LR
  A[63 lokale HTMLs + Manifest] --> B[Discovery]
  B --> C[timed_knowledge Selection]
  C --> D[Adapterplan / 50 Bindungen]
  D --> E[CS50Executor: DOWNLOAD]
  E --> F[PARSE_SUBTITLE / TranscriptDocument]
  F --> G[geprüftes Knowledge-Inputmanifest]
  G --> H[echter zeitbasierter Chunker]
  H --> I[isolierter Pilot: 1–2 Chunks, Python 0]
  I --> J[Evidence: chunk oder segment_v1]
  J --> K[deterministische Consolidation]
  K --> L[JSON-Artefakte + Quality-Report]
```

| Stufe | Einstieg, Kernfunktionen und Modelle | Ein-/Ausgabe und Identität | Nachweis / aktuelle Grenze |
|---|---|---|---|
| Discovery | `src/tools_lecture/cs50_manifest.py`: load_fixture_manifest; `prepare_cs50.py`: parse_course_index, parse_week_page, combine_course_pages, discover_fixture_courses. `src/model_discovery/cs50.py`: CourseDiscovery, SectionDiscovery, ResourceCandidate, MediaVariant, Provenance, DiscoveryWarning. | Manifest/HTML → immutable Discovery-Graph; SHA-256, offizielle URL, DOM-/Kontextpfad, course_id, Section-Key, Parent-/Resource-/Variant-ID. | O: 6/50; Navigationsreihenfolge, verschachtelte Rollen, HDR/SDR/Sprachen, Deduplizierung. Keine Live-Verifikation oder Notes-/Assignment-/CDN-Inhaltsextraktion. |
| Selection | `select_cs50.py`: preview_course, _choose_timed, select_optional_txt. SelectionPolicy, SelectionOption, SelectionDecision, LecturePreview, CoursePreview. | Discovery + Policy → Dry-Run-Entscheidungen mit URL/Rolle/Sprache/Alternativen. | O: 50 eindeutige en-SRTs. Default bleibt TXT-first; timed_knowledge ohne TXT/VTT/Video/Whisper-Fallback. Unbekannte Sprache/Mehrdeutigkeit führt zu keiner Auswahl. |
| Lecture-Adapter | `adapt_cs50.py`: adapt_cs50_course, bind_cs50_selection, build_cs50_transcript_tasks, build_cs50_course_plan. CS50AdapterPlan/CoursePlan, TranscriptBinding, TaskBinding, ArtifactState plus bestehende LectureCourse/Document/Media und ResourceTask. | Preview → versionierter Plan; SRT als LectureDocument, getrennte lecture_id/resource_id; source_id aliasiert SRT-resource_id. | O: 50/100, Roundtrip, Pfad-/Identitätskollisionen. ResourceTask besitzt keine eigenen Abhängigkeits-/Ausgabefelder: CS50TaskBinding muss mitgeführt werden. Kein Dispatch nackter Tasks an Legacy-Runner. |
| SRT-Download | `execute_cs50.py`: CS50Executor.select/run/download, safe_path, digest, write_state. CLI im selben Modul. | Geprüfter Plan + Auswahl → source.srt und execution.v1.json pro Quelle. | O/T: Stream, Größenlimit, begrenzte Retries, HTTPS-CDN, keine Redirects/yt-dlp. 50 Downloads nur mit Fake-HTTP nachgewiesen; heutiger Serverbestand ungeprüft. |
| Offizieller Import | Executor-PARSE_SUBTITLE → `tools_transcribe/import_transcript.py`: import_srt; validate_order/validate_document. TranscriptDocument, TranscriptSegment, TranscriptProvenance. | Roh-SRT → transcript.json; Original-URL/Sprache/Quelle/relative geplante Source-Pfade, media_id falls eindeutig. | O/H: Syntax/UTF-8-BOM, Zeiten, Reihenfolge, Text gegen Roh-SRT. preserve_empty_cues=True; leere Cues bleiben vorhanden, kein Inhaltsbeleg. TXT ist getrennt fehlerhaft. |
| Knowledge-Input | `tools_knowledge/bind_cs50_transcript.py`: bind_cs50_knowledge_input, load_knowledge_transcript, save_knowledge_manifest. CS50KnowledgeInput/Manifest. | Plan + done-Receipts + beide Dateien → explizites Inputmanifest mit Identitäten, Hashes, Transcript-/Discovery-Provenienz. | O: erneut überprüfte Dateien/Versionen, kein Filename-Scan. CLI erstellt genau einen Input; gespeicherte Artefaktpfade werden absolut und sind nicht automatisch relocatable. |
| Chunking | build_cs50_knowledge_chunks → `find_knowledge.py`: build_transcript_chunks. KnowledgeSettings, TranscriptChunk. | Verifiziertes Transcript → IDs/Segmente/Originalzeiten/Text. Leere Cues werden ohne Renummerierung ausgeschlossen. | O: 45-s-Ziel, zwei Cue-Overlap. max_duration ist im Chunker nicht aktiv; Cue-Anzahl ist kein Zeit-Overlap. Pilot verwirft Chunks >6000 Zeichen statt sie aufzuteilen. CS50-Wrapper ruft enrich_chunks nicht auf; Nachbarkontext bleibt daher dort normalerweise None. |
| LLM-Extraktion | `scripts/cs50_knowledge_pilot.py`: main/worker; `cs50_extraction_provider.py`: OpenAIHTTPProvider, RequestBudget, messages_for, validate_response; Prompt in `agent/prompts/prompt_know_extract.py`. ChunkKnowledgeResult/Analysis/Extract, KnowledgeStatement, MathExpression. | Genau ein Python-0-Input + Fenster → ein/zwei Modellantworten, Prompt-Hash, Usage/Status/Runtime. | O/H/F: echter historischer HTTP-Pilot; Fake-HTTP-Verträge heute grün. Kein vollständiger Lecture-/Kursrunner. Default Marvin, HTTP explizit; kein SDK für HTTP erforderlich. |
| Evidence | build_cs50_knowledge_document; `cs50_precise_evidence.py`: precise_input, bind_precise_candidates; Legacy attach_chunk_provenance. KnowledgeEvidence, ConsolidatedEvidence. | Ergebnis + geprüfte Originalsegmente → Quellenmodalität transcript, Cue-IDs/Zeiten; Identität aus Input, nicht LLM. | O: Legacy Voll-Chunk; segment_v1 originale Teilmengen, keine leeren/fremden/duplizierten IDs, Modellzeiten ersetzt. Keine semantische Entailment-Prüfung; realer präziser Qualitätstest fehlt. |
| Consolidation | `consolidate_knowledge.py`: consolidate_knowledge. TranscriptKnowledgeDocument → ConsolidatedKnowledgeDocument. | Deterministisches Statement-/Formel-Merging mit Evidence; Sprache, Kurs/Lecture, media_id und Transcript-Provenienz erhalten. | O: echter Import, Math-Helper, source_id-Regeln, separate Belegstellen. Keine semantische/visuelle LLM-Stufe erforderlich. section_key/resource_id/Discovery-Provenienz bleiben zusätzlich in externen Bindungen. |
| Quality/Persistenz | `cs50_quality.py`: quality_report; Pilot-save; `scripts/report_cs50_quality.py`. JSON-Dict cs50_quality_v2, vorhandene Dokumentmodelle. | Pro Run extraction.json, consolidated.json, chunks.json, Sidecars, evidence_bindings.v1.json, input_manifest.json, worker_result/supervision/configuration. | O/F: Kennzahlen und Roundtrips; keine kursweite Aggregation, kein Durable-Knowledge-Resume, keine vollständige Job-Coverageprüfung. JSON-Ausgaben exklusiv, aber nicht atomar publiziert. |

### CLI-Inventar und Freigaben

| Einstieg | Parameter / Verhalten |
|---|---|
| `python -m scripts.report_cs50_sources` | --manifest, --output, --knowledge-preview. Letzteres verwendet timed_knowledge; normale Übersicht TXT-first. Rein offline; Markdown-Ausgaben per write_text können bestehende Reportdateien ersetzen. |
| `python -m scripts.report_cs50_lecture_plan` | --manifest, --artifact-root (Default data/lectures), --output. Vollständiger JSON-Roundtrip; exklusive Neuanlage, keine Task-Ausführung. |
| `python -m src.tools_lecture.execute_cs50` | --plan, --course, --section, --max-lectures (Default 1), --dry-run oder --execute. Ohne execute bleibt Dry-Run. execute verlangt course; sequenzieller Kurs-Prefix bis max-lectures, Abbruch bei erstem Fehler. |
| `python -m scripts.report_cs50_knowledge_input` | --plan, --course, --section, --output. Exakt eine Bindung; revalidiert vorhandene Artefakte, schreibt neues Manifest außerhalb der Source-Roots. |
| `python -m scripts.cs50_knowledge_pilot` | --plan, --manifest, --output, --provider {marvin,openai_http}, --model; --max-chunks {1,2}, --chunk-index; --timeout, --token-budget, --input-limit, --output-limit; --evidence-mode {chunk,segment_v1}; --execute-llm, --probe-marvin. Offline Default, neuer Outputordner; Parent-/Worker-Freigabe. Python 0 hart begrenzt; segment_v1 real nur mit openai_http. |
| `python -m scripts.report_cs50_quality` | --extraction, --chunks, --worker-report optional, --evidence-bindings optional, --output. Exklusive Ausgabe, Modell-/Audit-Identitätsprüfung, kein LLM. |
| `python -m scripts.cs50_llm_smoke` | älterer separater Smoke-Helfer mit --transcript, --output, --model, --max-chunks, --timeout, --enable-api; seine supervise-Funktion wird vom aktuellen Pilot wiederverwendet. Kein Lecture-Batch und keine Alternative zur geprüften CS50-Inputbindung. |

### Ausführungs-/Resume-Verträge

SRT: pro Quelle POSIX flock, Receipt-Version und vollständige Binding-Gleichheit.
DOWNLOAD/PARSE_SUBTITLE sind getrennte Schritte. running/failed/prepared/done sind
persistiert. Temporäre Datei, fsync, vorbereiteter Hash, exklusive Hardlink-
Publikation und atomarer Receipt-Wechsel verhindern Übernahme beliebiger Dateien.
Ein prepared-Hash kann einen Abbruch nach Publikation auflösen. Wiederverwendung
fordert Hash und bei normalisiertem Transcript erneuten Vergleich mit Roh-Cues.
Eine bloß vorhandene Datei oder eine geänderte Provenienz führt zum Konflikt.

Die initialen Adapter-Flags bleiben Literal planned_only=True und
execution_supported=False, während der heutige Executor einen Ausführungspfad
hat und dessen Dry-Run execution_supported=True ausgibt. Das ist eine veraltete
Planbeschreibung, kein Beleg eines fehlenden Executors. Auch Selection-Warnung
integration_pending und Task-Grund future handler sind inzwischen veraltet.
Der Executor vertraut seinen eigenen Receipts, nicht einem allein behaupteten
SKIPPED-Status aus dem Adapter.

Knowledge: Pilot-Verzeichnis und Dateien müssen neu sein. Es gibt weder
Chunk-Ledger noch Resume in dieses Verzeichnis. Ein Abbruch kann gültige einzelne
Chunkdateien und unvollständige JSONs hinterlassen; ein neuer Aufruf startet
wieder einen neuen Run. Einzeldateien sind kein geprüfter Wiederverwendungsbeleg.
save() und save_knowledge_manifest() verwenden open('x'), aber keine atomare
Temp-Datei-/fsync-/Publish-Sequenz. Hash-/Schema-/Jobversionen für Knowledge-
Checkpoint-Adoption fehlen. build_cs50_knowledge_document erlaubt absichtlich
Teilresultate und prüft nicht, dass alle Chunks einer ganzen Vorlesung vorliegen.

Der allgemeine `run_knowledge_consolidation.py` wird im Pilot nicht verwendet.
Sein existenzbasierter Skip ist **keine sichere CS50-Resume-Lösung**. Er wurde
für diesen Audit ohne SDK-Import aus der echten AST-Funktionsdefinition
process_course_knowledge isoliert geprüft, nur in TemporaryDirectory: leere
Datei, '{broken' und '{}' führten jeweils zu null Processing-Aufrufen. Dieser
befundene Fehler rechtfertigt kein Einschleusen des Legacy-Runners in CS50.

## End-to-End-Fragen

| Frage | Befund |
|---|---|
| Alle SRTs eines Kurses? | T/O: mit course und explizitem max-lectures bis Kursgröße möglich; Fake-HTTP test_execute_all_100_with_fake_http verarbeitet 50 Sources/100 Aktionen. Live-Erreichbarkeit aller SRTs fehlt. Standard 1 wählt immer den ersten passenden Eintrag, nicht automatisch die nächste offene Lecture. |
| Erfolgreiche Imports wiederverwenden? | O: Executor und Knowledge-Inputbinder revalidieren Identitäten, Hashes, Provenienz und Roh-/normalisierten Inhalt. |
| Ganze Vorlesung / mehr als zwei Chunks? | F: CLI und RequestBudget erlauben nur 1/2, Worker autorisiert nur Python Woche 0. Ein vollständiges Inputtranskript wird gechunked, aber nur das ausgewählte Fenster verarbeitet. |
| Mehrere Vorlesungen/Kurse? | Download: begrenzter sequenzieller Kursloop. Knowledge: kein Batch-Runner, kein Kursmanifest-Dispatch, kein globaler Status. |
| Abbruch/Resume? | SRT O; Knowledge F. Unknown/outstanding API-Anfragen nach Kill haben keinen dauerhaften Versuchseintrag. |
| Limits? | Pilot: Requestzahl 1/2, keine API-Retries, HTTP 20 s, Prozess 0–120 s (Default 45), Inputreserve via UTF-8-Bytes +2048, Tokenreserve ≤64000, Output ≤2000. Kein monetärer Preis-/Modell-Allowlist-Vertrag, kein Kurs-/Batchbudget oder persistentes Reservierungsjournal. |
| Provenienz komplett? | CS50-Direktpfad O für source_id/URL/Sprache/Kurs/Lecture/media/Transcript-Provenienz und Evidence. Section/Resource/Discovery-/Hashes zusätzlich im Input-/Evidence-Manifest; bestehende fachliche Knowledge-Modelle tragen nicht alle externen Bindungen. |
| Beschädigte Teiloutputs? | SRT O; Knowledge nur beim expliziten Laden/Validieren erkennbar. Kein Resume-Adopter, kein done-Marker für Vollständigkeit, kein atomarer Mehrartefakt-Commit. |
| Kursweite Quality-Aggregation? | F: pro Source/Run verfügbar; kein gewichteter Kursreport, kein Coverage-/Budget-Dashboard. |
| Maschinenunabhängige Ausführung? | Discovery/Plan/Tests O. Produktive Inputmanifestpfade werden absolut und checked != input vergleicht sie. CLI bindet Workspace an cwd; Verschieben vorhandener Manifeste ist nicht gelöst. Worker-Abhängigkeiten/Settings bleiben notwendig. |

Downloadgrenzen: pro Quelle 8 MiB, HTTP-Timeout 15 s, Gesamt-Deadline 60 s,
zwei Retries (maximal drei Versuche; konfigurierbar bis drei Retries), Backoff.
404/andere Status/Redirects scheitern; 429/5xx/Transport-/Timeoutfehler begrenzt
wiederholbar. Gesamt-Deadline und Transporttimeout sind kein kursweiter SLA oder
hart isolierter Gesamtprozess-Timeout. Sie dürfen nicht als Batchbudget gelten.

## Identität, Speicherformate und Architekturgrenzen

1. Bestehende Discovery-/Lecture-/Transcript-/Knowledge-Modelle reichen für einen
   ersten vollständigen SRT-Knowledge-Pfad. Neue fachliche Ergebnisarchitektur ist
   nicht nötig. Es fehlt eine versionierte **Ausführungsbindung** für Job, Chunk-
   Fingerprint, Artefakthash, Budget und Completion; source_id bleibt unverändert.
2. Chunk-IDs wie chunk_0020 sind innerhalb einer Source/Chunkkonfiguration lokal.
   Source + Transcript-SHA + vollständige Chunking-Konfiguration/Chunkplan +
   Prompt-/Evidence-Version + Provider/Modell müssen Wiederverwendung qualifizieren.
   Gleich benannte Dateien oder Chunknummern aus einer anderen Konfiguration
   dürfen keinen Resume-Hit ergeben.
3. Provider-Rohfelder bleiben bei segment_v1 vor Bindung als geparstes JSON erhalten.
   Legacy-Sidecars sind Pydantic-Felder vor Postprocessing, keine vollständigen
   HTTP-Rohantworten. Unlesbare/abgeschnittene/refused Antworten haben nicht
   notwendigerweise ein vollständiges Sidecar. Fehlerberichte liefern teils nur
   Exception-Klassennamen; für Batchbetrieb fehlen sichere strukturierte Gründe.
4. segment_v1 bindet einmal am Provider und erneut am geprüften Input. Der
   erneute Quellencheck ist sinnvoll; die genaue Kostenstelle wiederholter
   SRT-Reimports pro Chunk sollte vor Vollkursbetrieb offline profiliert werden.
   Eine Optimierung darf Rohhash-/Mutationsprüfungen nicht abschaffen.
5. Kein SDK-Import beim deterministischen CS50-Pfad; allgemeine Lecture-Modelle
   importieren weiterhin Settings aus core/config.py. root/chroma/data/API-
   Konfigurationsfelder sind auch ohne echten API-Call erforderlich; Tests setzen
   isolierte Platzhalter. Kein Secrets-Dump. Ohne definierte Worker-Umgebung ist
   der Pfad nicht lediglich mit Pydantic ausführbar.
6. Die ältere smoke RequestBudget-Klasse und der heutige Provider-Budgetvertrag
   überlappen, haben aber unterschiedliche Aufgaben. Keine pauschale Zusammenführung:
   für Batch den heutigen Budgetvertrag erweitern und Pilotlimits erhalten.
7. Import-SRT und Executor-Prüfung sollten wiederverwendet werden, nicht die
   allgemeinen Video-/Whisper-/Visual-Processing-Runner. Unvollständige Formeln
   und VisualCandidates dürfen zunächst als offen erhalten bleiben; kein
   automatischer Video-/Visual-LLM-Fallback für einen SRT-Knowledge-Kurslauf.

## Fachliche Qualität und notwendige Evaluation

Historischer Nachweis aus `docs/course_sources/cs50/first_llm_quality_report.md`:
ein gpt-4o-mini-Aufruf, 3316 Input-/491 Output-Tokens, sechs Statements, keine
Formeln, sechs konsolidierte Statements. Vier Topics fehlen; Intro-/Moderations-
aussagen besitzen wenig Konzept-Lernwert. Diese Zahlen wurden aus dem bestehenden
Bericht übernommen, nicht erneut aus produktiven Dateien rekonstruiert.

Die damaligen ursprünglichen LLM-Belege sind nicht rekonstruierbar: Der Legacy-
Helper ersetzt IDs/Zeiten durch den ganzen Chunk. segment_v1 korrigiert die
technische Zuordnung: explizite Original-Cues, gültige nicht leere ID-Teilmengen,
Zeitunion aus Originalsegmenten, kein freier Quell-/Zeitwert vom LLM. Trotzdem
beweist eine gültige Referenz nicht, dass ihre Texte die vollständige Aussage
tragen. Ein echter segment_v1-Qualitätslauf fehlt weiterhin.

Vier getrennte Bewertungsachsen:

| Achse | Messung | Was damit nicht bewiesen ist |
|---|---|---|
| Schema | JSON/ChunkKnowledgeResult/Pydantic, Completion nicht truncated/refused | Wahrheit oder Relevanz |
| Quellenbindung | Hash/IDs/Originalzeiten/Identität, keine fremden/leer belegten Cues | Entailment durch ausgewählte Texte |
| Semantik | manuelle vollständige Belegbarkeit, Kontextabhängigkeit, Überverallgemeinerung | didaktischer Nutzen |
| Didaktik | eigenständiger Konzept-Lernwert, Granularität, Redundanz, passende Topics | rein durch Regex/Pydantic messbare Korrektheit |

`quality_report()` liefert Screening: Statement-/Formelzahlen, fehlende Topics,
exakte Duplikate, Intro-/Übergang-Proxys, Evidenzsignaturen und Scopes
statement_precise/chunk_only/invalid. Es filtert nichts und ist kein Gold-Evaluator.
Ein precise-Scope verlangt passenden lokalen Auditnachweis; dieser ist keine
kryptografische oder fachliche Beglaubigung. Kursaggregation muss auch fehlende,
fehlgeschlagene und noch nicht verarbeitete Chunks als Denominator führen.

Vorgeschlagenes Gold-Set (noch **nicht erstellt**, keine erfundenen Goldaussagen):
zunächst acht echte Python-0-Chunkfenster aus einem bereits geprüften Original-
SRT (Intro/Moderation, vier Konzeptpassagen, Kontextgrenze, Schluss/Negativfall).
Menschen annotieren tatsächliche eigenständige Aussagen und gegebenenfalls
Formeln, minimale/zulässige Cue-Belege, Negativentscheidungen und Lernwert.
Danach je vier Fenster aus jedem der sechs Kurse (24 insgesamt), sobald deren
reale Imports explizit freigegeben und geprüft vorliegen. Code/SQL-Syntax nicht
zwangsläufig als mathematische Formel behandeln; keine Formeln erfinden.

Goldzeile: source_id/course_id/lecture_id, Raw-/Transcript-SHA, Chunkplan-Version,
chunk_id, Original-Cue-IDs, wörtliche Belegstellen, belegte fachliche Aussage,
semantischer Typ/Topic, Relevanzurteil, didaktische Begründung, Entailment-Urteil,
Negativgrund, Reviewer/Adjudikation. Ein Teil wird doppelt annotiert; Uneinigkeit
bleibt sichtbar. Erst danach freigegebener kleiner Modellvergleich Legacy gegen
segment_v1 mit gleichem Quellfenster/Modell/Prompt und fixen Budgets. Keine Prompt-
Änderung allein aufgrund von Regex-Scores. Numerische Freigabegrenzen vor dem
Experiment festlegen; sie sind heute keine nachgewiesenen Qualitätswerte.

## Tatsächlich ausgeführte Prüfungen und Fehlereinordnung

Aufruf im frischen Worktree; die bereits installierte reguläre Worker-.venv
wurde über UV_PROJECT_ENVIRONMENT verwendet, ohne Sync/Upgrades/SDK-Installation:

```bash
UV_PROJECT_ENVIRONMENT=/path/to/installed-worker/.venv UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest tests -q --tb=short \
  --junitxml=/tmp/cs50-completion-audit-tests.xml
```

Python 3.12.12 / pytest 9.1.1 / Pydantic 2.13.4. Eine vollständig frische locked-
uv-Installation wurde heute nicht durchgeführt; der zuvor dokumentierte
ungecachte spaCy-Wheel-Metadatenblocker ist nicht durch einen neuen Installations-
nachweis aufgehoben. Worker-Profil und Offline-Rebuild bleiben eigene Aufgaben.

| Fehlergruppe | Anzahl | Konkrete Ursache / Relevanz für CS50 |
|---|---:|---|
| Metadatenweitergabe | 2 | allgemeiner Extraction-Runner lässt Sprache/Provenienz/Kurs weg; semantischer Leerzweig kopiert Meta/media nicht. Modellmethoden/Validatoren sind integriert. Bestehender CS50-Direktbinder + deterministische Consolidation funktionieren; kein unmittelbarer CS50-SRT-Batchblocker. |
| TXT | 6 | import_txt erzeugt unbekannte None-Zeiten, TranscriptSegment verlangt float. Kein Grund für SRT-Fallback oder künstliche Zeiten; TXT optional später. |
| Optionaler SDK-Smoke | 1 | openai nicht installiert; kein Fehler des SDK-freien HTTP-Providers. SDK-Testprofil getrennt ausweisen. |

Vier bestehende Skips: lokaler Original-SRT-Executorpilot, lokaler geprüfter
Original-Knowledgepilot, lokaler CLI-Originalpilot, Marvin-installationserfordernder
Integrationstest. Die portable synthetische Pilotabdeckung läuft trotzdem.
Keine neuen Skips/xfails. Der frühere /proc-Timeout-Test-Race trat heute nicht auf.

Konkrete Lücken ohne derzeit rote Unit-Tests: vollständiges Knowledge-Resume,
course/job-weite Budgets, externe Request-Ungewissheit nach Kill, Recovery aller
Knowledge-Ausgabedateien, Vollständigkeitsnachweis, portable gespeicherte Input-
Manifeste, kursweite Quality-Aggregation und fachliche Gold-Evaluation. Das sind
fehlende Implementierungs-/Abdeckungsbereiche, keine durch 374 grüne Tests
bewiesenen Fähigkeiten.

Die nachfolgende Modulübersicht enthält den aktuellen vollständigen Lauf.

| Modul | bestanden | Fehler | Setupfehler | Skips |
|---|---:|---:|---:|---:|
| test_consolidation_math_import | 1 | 0 | 0 | 0 |
| test_cs50_discovery | 30 | 0 | 0 | 0 |
| test_cs50_executor | 32 | 0 | 0 | 1 |
| test_cs50_extraction | 44 | 0 | 0 | 0 |
| test_cs50_fixture_checkout | 2 | 0 | 0 | 0 |
| test_cs50_full_coverage | 10 | 0 | 0 | 0 |
| test_cs50_knowledge_input | 27 | 0 | 0 | 1 |
| test_cs50_knowledge_pilot | 19 | 0 | 0 | 1 |
| test_cs50_lecture_adapter | 30 | 0 | 0 | 0 |
| test_cs50_llm_smoke | 8 | 1 | 0 | 0 |
| test_cs50_precise_evidence | 18 | 0 | 0 | 0 |
| test_cs50_quality | 9 | 0 | 0 | 0 |
| test_cs50_selection | 24 | 0 | 0 | 0 |
| test_cs50_six_courses | 9 | 0 | 0 | 0 |
| test_cs50_srt_knowledge_integration | 5 | 0 | 0 | 0 |
| test_cs50_timed_selection | 19 | 0 | 0 | 0 |
| test_cs50_uv_installed_integration | 0 | 0 | 0 | 1 |
| test_knowledge_source_id | 11 | 0 | 0 | 0 |
| test_knowledge_transcript_provenance | 39 | 2 | 0 | 0 |
| test_lazy_marvin_import | 4 | 0 | 0 | 0 |
| test_official_transcript_import | 33 | 6 | 0 | 0 |
