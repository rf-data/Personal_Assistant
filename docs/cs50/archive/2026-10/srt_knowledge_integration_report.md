# CS50 Python Woche 0: Offline-SRT-Integration

## Ergebnis und Aussagegrenze

Der bestehende SRT-Importer erzeugt ein mit `build_transcript_chunks` kompatibles
TranscriptDocument. Mit synthetischen Knowledge-Ergebnissen bleiben Quellen-ID,
Segment-IDs, echte Sekundenwerte, Chunk-ID und Transkript-URL bis zur deterministischen
Consolidation erhalten. Sprache und vollständige Import-Provenienz werden dagegen
nicht in die Knowledge-Ergebnisverträge übernommen.

Ein vollständiger unveränderter Runner-Durchlauf ist derzeit **nicht nachgewiesen**.
Neben den Metadatenlücken besteht ein falscher Import der mathematischen
Normalisierungsfunktion. Die erfolgreichen Consolidation-Vertragstests verwenden
hierfür ausschließlich eine ausdrücklich dokumentierte Test-Verknüpfung; der Fehler
selbst wird durch einen separaten Regressionstest festgestellt.

## Quelle und Pilotumfang

Die lokale Fixture `cs50_python/week_0.html`, zugeordnet über manifest.json zur URL
`https://cs50.harvard.edu/python/weeks/0/`, verlinkt:

`https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt`

Discovery identifiziert dieses Angebot als Subtitles, Sprache `en`, Format `srt`,
Abschnitt `0`. **Im Repository wurde keine lokale SRT-Datei gefunden.** Da Downloads
nicht erlaubt sind, wird der offizielle Inhalt nicht geprüft. Die Tests verwenden
kurze, ausdrücklich synthetische SRT-Inhalte in pytest-Temporärdateien, mit der durch
das HTML belegten Original-URL als Testmetadatum. Sie sind keine Kopie des offiziellen
Transkripts und belegen weder dessen tatsächliche Cue-Struktur noch seine Vollständigkeit.

Die synthetische Quelldatei heißt `cs50_python_week_0.synthetic.en.srt`. Der Importer
setzt vertragsgemäß `official_subtitle`; in diesem Test ist das die geprüfte
Ziel-Metadatenstrategie, keine Behauptung offizieller Herkunft des synthetischen Textes.
Ein späterer realer Pilot benötigt eine separat bereitgestellte unveränderte lokale
Kopie des offiziellen SRT und eine erneute Prüfung ohne Download durch diese Tests.

## Geprüfter Datenweg

1. Discovery liest ausschließlich lokale HTML-Fixtures und liefert Kurs-/Wochen-
   Zuordnung, Sprache und Original-URL. Es gibt keine Änderung der Discovery-Logik.
2. `import_srt` liest synthetische SRT-Daten, erhält Mehrzeilen-Cues und setzt
   TranscriptDocument/TranscriptProvenance. Provider, Laufzeit und Whisper-Metriken
   bleiben unbekannt; kein Whisper wird geladen.
3. Normalisiertes Transcript-JSON wird explizit und exklusiv in einem temporären
   Testordner gespeichert und mit TranscriptDocument wieder geladen.
4. Die tatsächlichen Funktionen build_transcript_chunks, enrich_chunks,
   attach_chunk_provenance, validate_extraction und make_visual_candidate werden
   via AST isoliert ausgeführt; keine Runner-/Marvin-/App-Konfigurationsimporte.
5. Synthetische Statements und Formeln erhalten bewusst falsche Platzhalter-Evidenz.
   attach_chunk_provenance ersetzt sie mit den wirklichen Chunk-IDs, Segment-IDs
   und Zeiten. Dies prüft die Anwendungskontrolle über Ergebnis-Provenienz.
6. TranscriptKnowledgeDocument mit expliziter source_id wird als JSON gespeichert,
   geladen und deterministisch konsolidiert. Die ID wird nach der bestehenden Runner-
   Konvention aus dem Namen der normalisierten Original-Transkriptdatei ohne `.json`
   abgeleitet; sie kennzeichnet in diesem Test ausdrücklich die synthetische Quelle.
7. Zwei gleichlautende synthetische Aussagen/Formeln mit überlappender Evidenz werden
   konsolidiert, wobei beide Evidenzstellen erhalten bleiben. Zeitfähige VisualCandidates
   werden nur als Daten konstruiert; keine Visual-Verifikation oder Medienverarbeitung.

Die Tests verwenden reale Modelle, reale Text-/LaTeX-Helfer und reale deterministische
Funktionskörper. Sie testen nicht die vollständigen Modulimporte, Runner-Ausführung,
LLM-Konfiguration, semantische LLM-Konsolidierung, tatsächliche offizielle SRT-Daten
oder den Visual-Rebuild. Die Zusatzverknüpfung für Formeln wird unten beschrieben.

## Beobachtete Werte und Metadaten

Test-Cues: Segment `0`: 0–20 s, Segment `1`: 20–50 s, Segment `2`: 50–80 s.
Chunking: `target_duration=45`, `overlap_segments=1`.

| Chunk | Segment-IDs | Start / Ende | Consolidation-Evidenz |
|---|---|---|---|
| chunk_0000 | [0, 1] | 0.0 / 50.0 | Erhalten in Aussage und Formel |
| chunk_0001 | [1, 2] | 20.0 / 80.0 | Erhalten in Aussage und Formel |

Die Konsolidierung liefert je eine synthetische Aussage und Formel mit jeweils zwei
Evidenzstellen. VisualCandidates behalten 0–50 und 20–80 s. Die synthetische Formel
bleibt wegen verlangter visueller Prüfung `pending`, ohne eine Prüfung auszuführen.

| Information | TranscriptDocument | Chunk / Extraction / Consolidation |
|---|---|---|
| Sprache `en` | Dokument und Provenienz | Keine eigenen Sprachfelder; nicht explizit erhalten |
| Original-SRT-URL | provenance.source_url | Als transcript_url in Knowledge-Dokumenten erhalten |
| source_id | Kein eigenes Feld im TranscriptDocument | Explizit aus normalisiertem Transkriptpfad gesetzt und erhalten |
| Segment-IDs / Zeiten | Pro Cue erhalten | Als Chunk-Evidenz erhalten; kein präziserer Einzelbeleg behauptet |
| Herkunft `official_subtitle` | provenance.transcript_source | Nicht erhalten; evidence.source=`transcript` bezeichnet nur die Modalität |
| Quelldatei, Format, acquired_at, Provider-Metadaten | Import-Provenienz vorhanden | Kein vollständiger Provenienzvertrag in den Ergebnisdokumenten |
| Kurs cs50_python / Abschnitt 0 | Discovery-Kontext | Keine automatische Zuordnung im Transcript-/Knowledge-Modell |
| Video-ID / Video-URL | SRT-URL belegt keine Videoidentität | Test setzt media_id explizit None; keine Video-ID erfunden |

Das Quelldokument wird beim Chunking nicht verändert. Die fehlende Weitergabe von
Sprache/Herkunft wird ausdrücklich getestet und nicht durch Testmodelle kaschiert.

## Blocker und minimal notwendige Anpassungen vor produktiver Integration

1. **Falscher Helper-Import:** consolidate_knowledge.py importiert normalize_math_text
   aus src.utils.text_helper; dort existiert die Funktion nicht. Sie liegt in
   src.utils.latex_helper. Der normale Modulimport würde daran scheitern; isolierte
   Funktionsausführung ohne diese Verknüpfung scheitert bei Formeln mit NameError.
   Minimale spätere Änderung: genau diesen Import korrigieren. Für positive Tests
   wird die vorhandene latex_helper-Funktion nur im isolierten Test-Namespace gebunden.
   Keine produktive Funktion wurde dadurch geändert.
2. **Quellen-ID-Vertrag:** Die im Workspace vorhandene Korrektur aus PR #10 ist
   Voraussetzung. Alt-JSON ohne source_id bleibt lesbar, Konsolidierung lehnt es aber
   verständlich ab. Ein verifizierter Original-Transkriptkontext muss die ID explizit
   liefern; keine Ableitung aus beliebigen Extraktions-Dateinamen. Der Test deckt
   diesen Fehlerpfad separat ab. PR #10 muss im Integrationsstand vorhanden sein.
3. **Sprache/Provenienz:** Optionales dokumentweites Sprachfeld und ein optionaler
   geprüfter TranscriptProvenance-/Quellenreferenzvertrag in den Knowledge-Ausgaben,
   inklusive Weitergabe in deterministischer und später semantischer Materialisierung,
   sind nötig. Alte JSON ohne diese Felder bleiben lesbar. KnowledgeEvidence.source
   nicht mit der Erwerbsstrategie überschreiben. Segmentbelege referenzieren die
   belegte Quellenidentität und bewahren die bestehende Modalität.
4. **Importer und Runner entkoppeln:** Das SRT offline normalisieren und das JSON gezielt
   dem Extraction-Eingang zuordnen. Nicht über ResourceTask-Ausführung routen, die
   Audio-/Whisper-Konfiguration initialisiert. Der jetzige Test ändert keinen Runner.
5. **Medien- und Kurszuordnung:** Transkript-URL und Video-URL auseinanderhalten;
   Video-ID, Kurs und Abschnitt später aus geprüfter Zuordnung übernehmen. Visual-
   Rebuild darf die SRT-URL nicht als Videoquelle behandeln. Trotz bekannter Cue-Zeiten
   fehlt hier eine getestete Medienbindung.
6. **Echte lokale Pilotdatei:** Nach deren Bereitstellung SRT-Cues, Sprache, tatsächliche
   Überlappungen, Dauer/Endwerte und Reihenfolge gegen denselben Vertrag prüfen.
   Der synthetische Test ersetzt diese Inhaltsprüfung nicht.

Kein Anlass zur Änderung des zeitbasierten Chunkings aus diesem Pilot. TXT/zeitlose
Verarbeitung ist nicht Teil dieser Prüfung. Das spätere produktive Einschalten bleibt
von behobenen Import-/Metadaten-/Zuordnungsproblemen abhängig.

## Tests und Schutz der Quelldaten

`tests/test_cs50_srt_knowledge_integration.py` enthält fünf Offline-Vertragstests:
Import/Chunking, JSON/Consolidation, dokumentierter Metadatenverlust, fehlende source_id
und falscher Formel-Helper-Import. Socket und DNS sind gesperrt. Vor/nach den Tests
werden SHA-256-Werte der HTML-Fixtures verglichen. Neue Testdateien entstehen nur im
pytest-Temporärordner; bestehende HTML-, SRT-, JSON- und Produktionsdateien werden
nicht geschrieben. Produktionsmodelle, Chunking, Runner und Helfer bleiben unverändert.

Gezielter Aufruf:
`python -m pytest tests/test_cs50_srt_knowledge_integration.py tests/test_knowledge_source_id.py tests/test_official_transcript_import.py -q`

Ergebnis: **53 Tests bestanden**, davon fünf neue Integrationstests. Ruff-Prüfung und
Formatierung des neuen Tests erfolgreich. Die vollständige zusätzliche CS50-Regression
mit denselben Tests plus test_cs50_discovery.py, test_cs50_extraction.py und
test_cs50_selection.py bestand ebenfalls: **146 Tests bestanden**. Nach Ergänzung
des expliziten Transcript-JSON-Speicherschritts bestanden die fünf neuen Tests erneut. Es wurden weder LLM-Aufrufe noch Downloads oder
Transkriptionen ausgeführt.
