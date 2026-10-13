# CS50 Python Woche 0: Integration in der installierten uv-Umgebung

## Ergebnis

Der vollständige geforderte Datenweg ist mit der lokal bereitgestellten originalen
SRT-Datei und **echten Modulimporten** bestanden. Aussagen/Formeln sind synthetische
Testdaten; es wurde kein Wissen durch ein LLM extrahiert. Sämtliche geprüften
Metadaten und Evidenzzeiten bleiben bis zur deterministischen Consolidation erhalten.

Eine unmittelbar nachgewiesene kleine Importer-Anpassung war nötig: explizites
`preserve_empty_cues=True` erhält gültige Cues ohne Text samt echten Zeiten. Der
Default bleibt streng; bisherige Fehlerfälle und zeitbasiertes Chunking ändern sich
nicht. Die sechs leeren Cues werden weder gelöscht noch mit Text/Zeiten aufgefüllt.

## Arbeitsbaum und vorausgesetzte Änderungen

Der Workspace steht auf master mit lokalen Änderungen/untracked CS50-Dateien.
Vorhandensein der Implementierungen bedeutet hier **keine Aussage über den Merge-
Status der PRs**. Der Integrationstest prüft den tatsächlich vorhandenen Code.

| PR / Änderung | Im Arbeitsbaum enthalten und überprüft |
|---|---|
| #9 offizieller TXT/SRT/VTT-Import | import_srt, TranscriptDocument, official_subtitle und echte Provenienz vorhanden |
| #10 source_id-Vertrag | Feld bleibt bei regulärer Konstruktion/JSON und Consolidation erhalten; keine Test-Injektion nötig |
| #11 Formel-Helper-Import | Konsolidierungsmodul importiert normalize_math_text regulär aus latex_helper; Funktionsidentität geprüft |
| #12 Provenienz | optionale Metadaten-Verträge und deterministische Weitergabe vorhanden; entsprechende semantische Vertragsregression geprüft |
| Discovery / Selection | vorhandene lokale Implementierung und Fixture-Manifest; Discovery unverändert verwendet |

Semantische LLM-Konsolidierung und produktive Runner wurden nicht ausgeführt.
Im Pilot werden reguläre Ergebnisdokumente explizit erstellt; der Extraction-Runner
ist durch die vorhandenen synthetischen Vertragsregressionen, nicht durch einen
vollständigen Agentenlauf, geprüft.

## Tatsächliche Umgebung

Aufruf über `uv run --offline --no-sync`: kein Sync, keine Installation, keine
Downloads. uv 0.9.15; Interpreter im Pilot:
`/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python3`.
Python 3.12.12, Pydantic 2.13.4, pytest 9.1.1, Marvin 3.2.7, tiktoken 0.14.0.
Es wurde nicht die frühere `/tmp`-Test-Python-Umgebung verwendet.

Die Probe läuft als isolierter Subprozess mit echten installierten Dependencies.
Keine AST-Auszüge, sys.modules-Ersatzmodule, gefälschten Konsolidierungsfunktionen
oder injizierten Modellfelder. App-Settings erhalten bekannte Testwerte und
Dummy-API-Schlüssel; Arbeitsverzeichnis und konfigurierte Verzeichnisse sind temporär.
Der Subprozess erhält nur eine kleine erlaubte Umgebung, keine Benutzer-API-Schlüssel.
Ein echter Logger mit NullHandler erfüllt die Session-Voraussetzung ohne Logdatei.
Socket connect/connect_ex, DNS und create_connection sind gesperrt und gezählt.
Im erfolgreichen Pilot: **0 Netzwerkversuche**; faster_whisper wurde nicht geladen.

Marvin initialisiert beim normalen Import eine Datenbank. Der erste synchrone
Importversuch blieb in ensure_db_tables_exist/aiosqlite hängen; ein zeitbegrenzter
Diagnoseversuch bestätigte den Stack. Die hängen gebliebene erste Probe wurde beendet.
Für den erfolgreichen Test wird der echte Import in einem laufenden asyncio-Loop
mit temporärem MARVIN_HOME_PATH, In-Memory-Datenbank und deaktiviertem SQLite-Autoinit
ausgeführt. Marvin benutzt dabei seinen vorhandenen Async-Kontext-Importzweig und
meldet, dass Tabellen beim ersten Datenbankzugriff erstellt würden. Es erfolgt kein
Agenten-/Datenbankzugriff. Dies ist eine dokumentierte Umgebungsbedingung, kein
Produktionsfix oder Nachweis, dass der synchrone Runner ohne Konfiguration funktioniert.

## Verwendete Quelle

Lokale, vom Benutzer bereitgestellte Datei:
`data/lectures/cs50_python/lecture0.srt.txt` — kein synthetischer SRT-Ersatz.
189.973 Bytes; SHA-256:
`719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c`.
Die Datei wurde nicht verändert. Ihre Bezeichnung als Original folgt der lokalen
Bereitstellung; ein externer Bitvergleich/Authentizitätsnachweis wurde nicht vorgenommen.

Die lokale Discovery für cs50_python, Abschnitt 0, liefert Sprache en und:
`https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt`.
Die Zuordnung zur Datei ist die ausdrücklich gewählte Pilotzuordnung. Die URL wurde
nicht angefragt. Wegen der lokalen Endung `.srt.txt` wird ausdrücklich import_srt
verwendet; generische automatische Erkennung würde anhand `.txt` TXT annehmen.

2.228 Cues/Segmente, maximaler Cue-Endwert 6.338,0 Sekunden. Sechs leere Cues:
Originalnummern 2, 39, 47, 870, 1508, 2228; nullbasierte Segment-IDs
1, 38, 46, 869, 1507, 2227. Der bisherige Default-Importer meldet bei Cue 2
`empty cue text`. Mit expliziter Erhaltung sind alle 2.228 Segmente enthalten.

## Bestanden / nicht bestanden je Verarbeitungsschritt

| Schritt | Ergebnis | Tatsächlich durchlaufener Pfad |
|---|---|---|
| Discovery / Kurszuordnung | Bestanden | discover_fixture_courses → validiertes lokales Manifest / HTML |
| Strenger SRT-Import ohne Freigabe | Nicht bestanden, erwarteter Originaldatei-Fall | import_srt → ValueError bei leerem Cue 2 |
| SRT-Import mit expliziter Erhaltung | Bestanden | import_srt → import_transcript → echte TranscriptDocument-Validierung |
| Transcript speichern/laden | Bestanden | save_imported_transcript exklusiv, reales load_dict mit TranscriptDocument |
| Echter Chunking-Modulimport | Bestanden unter dokumentierter Konfiguration | normaler find_knowledge-Import, keine AST-/Modulersetzung |
| Zeitbasiertes Chunking | Bestanden | build_transcript_chunks mit target_duration=45, overlap_segments=2 → 157 Chunks; enrich_chunks |
| Synthetische Knowledge-Ergebnisse | Bestanden | reale ChunkKnowledgeResult-Validierung; attach_chunk_provenance / validate_extraction |
| Knowledge-Modell / JSON | Bestanden | reguläres TranscriptKnowledgeDocument, echtes save_dict(mode=x), echtes load_dict |
| Normaler Konsolidierungs-/Helper-Import | Bestanden | vollständiger consolidate_knowledge-Modulimport und latex_helper-Funktionsidentität |
| Formelkonsolidierung | Bestanden | echte consolidate_knowledge mit Aussagen und Formeln; kein Ersatz-Helper |
| Metadaten und Evidenz | Bestanden | exakter Vergleich von Eingangs-/Ausgangsfeldern und sämtlichen Testbelegen |
| Quelldaten unverändert | Bestanden | SHA-256 vor/nach für SRT, Manifest und alle HTML-Fixtures |

Alle 157 Chunks wurden aus der vollständigen Quelldatei gebaut. Für alle 157
Chunks wurden synthetische Aussagen/Formeln erzeugt. Die Konsolidierung erhält für
die Testaussage und Testformel je 157 Evidenzstellen. Jede wurde exakt gegen ihren
Chunk geprüft. Damit wird der Datenvertrag geprüft, nicht die fachliche Qualität.
Die folgende Tabelle zeigt die ersten beiden Belege; der JSON-Snapshot enthält alle.

| Chunk | Segment-IDs | Zeitbereich |
|---|---|---|
| chunk_0000 | 0–9, 10 IDs | 0,0–45,65 s |
| chunk_0001 | 8–25, 18 IDs | 40,25–85,31 s |

## Metadatenwerte und Verluste

- source_id: `lecture0.srt.txt`, aus dem Namen des wirklich normalisierten
  Transkripts nach der vorhandenen Runner-Konvention; keine UUID oder vermutete ID.
- transcript_url: oben genannte originale Discovery-SRT-URL, unverändert.
- language: en; transcript_provenance vollständig gleich dem importierten Modell,
  einschließlich official_subtitle, lokaler Quelldatei, Sprache, Format und acquired_at.
- course_id: cs50_python, aus dem validierten Discovery-Kurs.
- lecture_id: `resource:4305fcd17cb0d9c50cfdd5e2718461e8369cb883189de96bda796f04cc800192`,
  bewusst die bereits vorhandene ID der Discovery-Hauptvorlesung, nicht eine
  erfundene lecture_no oder eine aus Dateinamen geratene Woche.
- media_id: `JP7ITIXGpHk`, die eindeutige vorhandene Medien-ID der Angebote dieser
  Discovery-Hauptvorlesung. Bei widersprüchlichen IDs würde die Probe None behalten.
  Die Bindung wird aus dem ausdrücklich gewählten Discovery-Kontext gesetzt;
  sie wird nicht aus der SRT-URL extrahiert. Die importierte Provenienz bleibt original.
- Chunk-IDs, Segment-IDs und Start/Ende: in allen synthetischen Statements und Formeln
  exakt erhalten. KnowledgeEvidence.source bleibt transcript und wird nicht in
  official_subtitle umbenannt.

**Kein Verlust der angeforderten Metadaten in diesem Datenweg festgestellt.** Weiter
nicht abgebildet/überprüft sind bytebasierte Quellenrevision in produktiven Modellen,
präzise textuelle Belegpositionen, Lizenz-/Authentizitätsprüfung, globale Eindeutigkeit
der Dateinamen-ID, zusätzliche Medienverifikation und nachgelagerter RAG-/Visual-Export.
Discovery-/Quellen-SHA dienen hier dem Test, sie sind noch kein persistierter
produktiver Provenienzvertrag. Der Test behauptet keine tatsächliche fachliche
Unterstützung der synthetischen Aussagen/Formeln durch das offizielle Transkript.

## Minimale Korrekturen und verbleibende Blocker

1. Kleine nachgewiesene Produktionskorrektur ausschließlich am Offline-Importer:
   `preserve_empty_cues=False` als neuer Default, bei bewusstem Opt-in leere Cues mit
   echten Zeitmarken erhalten. Zwei synthetische Regressionstests für SRT und VTT
   sichern strengen Default und vollständige Erhaltung. Keine Änderung am Chunker.
2. Normale App-Session benötigt einen Logger für save_dict; ohne Logger tritt nach
   dem JSON-Schreiben ein AttributeError auf. Im Pilot durch ordnungsgemäße temporäre
   Session-Konfiguration behoben, keine Änderung des allgemeinen Speichercodes nötig.
3. Synchrone Marvin-Import-/SQLite-Initialisierung ist in dieser Umgebung noch ein
   Blocker für unkonfigurierte CLI-Ausführung. Eine Lösung für produktive Runner muss
   getrennt geprüft werden; kein breites Entkoppeln oder Refactoring in diesem Auftrag.
4. Die Datei-Endung verlangt explizites SRT-Format. Kein Umbenennen der Quelldatei und
   keine allgemeine Änderung der Dateityperkennung erforderlich.
5. Der produktive Extraction-Runner besitzt nicht automatisch die im Test geprüfte
   Discovery-Vorlesungs-/Medienbindung. Diese explizite Übergabe ist vor automatisierter
   Course-Integration separat zu implementieren. Der Pilot erstellt das Modell regulär
   mit geprüftem Kontext; er aktiviert keine Taskausführung.

## Tests und Artefakte

Neuer Test: `tests/test_cs50_uv_installed_integration.py`; tatsächliche Import-/Pilot-
Probe: `tests/helpers/cs50_uv_integration_probe.py`. Ohne lokal bereitgestelltes SRT
wählt der portable Test ausdrücklich gekennzeichnete synthetische Daten. Im hier
berichteten Lauf war `synthetic_source=false`.

Gezielter echter uv-Pilot bestanden. **169 relevante Tests bestanden** in der
tatsächlich installierten uv-Umgebung. Nach Erweiterung auf synthetische Ergebnisse
für alle 157 Chunks wurde der echte Pilot erneut erfolgreich ausgeführt. Gesamtlauf:

```sh
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_uv_installed_integration.py \
  tests/test_knowledge_transcript_provenance.py tests/test_consolidation_math_import.py \
  tests/test_cs50_srt_knowledge_integration.py tests/test_knowledge_source_id.py \
  tests/test_official_transcript_import.py tests/test_cs50_discovery.py \
  tests/test_cs50_extraction.py tests/test_cs50_selection.py -q
```

Maschinenlesbarer Ergebnis-Snapshot des Originaldatei-Pilots:
`uv_installed_integration_result.json`. Enthält die verwendete Umgebung, Quelle,
Hashes, Metadaten, Belege und Schrittstatus; keine vollständige Kopie des SRT.
Neue normalisierte Transcript-/Knowledge-JSONs wurden ausschließlich temporär
unter /tmp erzeugt. Bestehende Quelldaten und gespeicherte Knowledge-Daten bleiben
unverändert; kein Download, Agentenaufruf, Whisper oder automatisches Mergen.
