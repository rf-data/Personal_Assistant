# C26-B7: Media-last-Planung und verbleibende Materialadapter

22.10.2026. Integrationsbasis: Backend-master
`c49645734dcba6d9d1aac8d4192841fa1a655051`, einschließlich
[B6/#144](https://github.com/rf-data/Personal_Assistant/pull/144) und
[Knowledge-Fix #143](https://github.com/rf-data/Personal_Assistant/pull/143).
Beide CLI-Erweiterungen sind erhalten. Aktueller gemeinsamer Prüfbericht und
Go-/No-Go-Kriterien: [Integration B3–B7](integration_b3_b7.md).
Die ursprüngliche B7-Abnahme auf `6786b5d` bleibt als datierter
[historischer Nachweis](media_last_validation.md) erhalten.

**Implementiert ist eine wiederverwendbare, ausschließlich lokale Planung.**
Kein Mediaexecutor, Download, Whisper-/Frame-/LLM-Lauf, Deployment, Zugriff auf
private Pilotbestände oder fachliche Realabnahme. Der gleiche bestehende Worker
genügt später für die Planung; kein neues Imagekonzept, keine Queue und kein
zweiter Container. [Tatsächliche Validierung](media_last_validation.md).

## Architekturprüfung und Adaptermatrix

| Vorhandene Komponente | Tatsächlich implementiert | B7-Verwendung / fehlender Betriebsvertrag |
| --- | --- | --- |
| `prepare_cs50`, `make_plan`, `inventory.catalog`, Discovery-/MaterialResource-/MediaVariant-Modelle | Snapshotgraph, echte Ressourcen-/Variantenidentitäten, Lecture-/Short-/Slidesrollen und URL-Provenienz | Unverändert wiederverwendet; keine rekursive Discovery oder URLsynthese |
| `select_cs50`, SelectionPolicy | Transcript-first-/timed-Auswahl, Sprache, SDR-/Auflösungspräferenz | Bestehende Policy eingebettet, deterministischer Tie-Break über Original-URL und Material-ID |
| `execute_cs50`, B5 `transcripts`, `import_transcript` | Begrenzter offizieller SRT-Download; SRT-/TXT-Offlinelane; Standalone-Importer zusätzlich VTT | B5-Raw-/Payload-/Receipt-/Batch-/Revisionsprüfung read-only; kein B5-Import aus dem Planner |
| `process_url.process_youtube_video`, `extract_resources`, `extract_audio` | yt-dlp-Metadaten, manuelle/automatische Untertitel, mehrere Audioformate und Web-Fallback, Cookie-/Optionsintegration | Implementierte Legacyfunktionen, **kein nachgewiesener C26-Media-Betriebsvertrag**; automatische Fallbackkette wird nicht aufgerufen |
| `FasterWhisperProvider` | Lokale faster-whisper-Transkription, Modell-/Device-/Threadparameter | Modellinitialisierung kann Dateien beschaffen; ohne freigegebenen lokalen Modellcache, begrenzten Prozess und Hash-/Receiptvertrag nicht C26-ausführbar |
| `extract_video.prepare_local_visual_sections`, `download_video_section`, `extract_frame` | Lokale Zeitbereiche, yt-dlp-Clips, ffmpeg-Frames und Bildvergleich | Bestehende Funktionen, aber keine vollständigen C26-Byte-/CPU-/Walltime-/No-Overwrite-Gates; Frameaufruf enthält `ffmpeg -y` ohne eigenen Timeout. Nur Methodenreferenz/Windowplan |
| C13 `visual_inventory` / `visual_worker` | Begrenzte HTML-/PDF-Bild-/SVG-/Vektorreferenzinventur, isolierter Worker mit Limits | Weiter vorhandener technischer Weg; keine semantische Bestätigung aus bloßem Bild-/Vektorvorkommen |
| `rebuild_knowledge.analyze_visual_batch_locally` / `analyze_visual_batch`, `postprocess_visual` | Lokale technische Analyse bzw. konfigurierter Remote-OpenAI-Aufruf und Nachbearbeitung | Keine neue Visualpipeline; Remotevariante unzulässig für diesen Auftrag und nie importiert/gestartet |
| MaterialProcessor, HTML-v2, PDF-v2, Code-v1, C10 Quality/Handoff | Provenienz-/SHA-/Locatorprüfung, Normalisierung, technische Aggregation | Bestehender read-only Materialhandoff für explizit genannte Artefakte; keine HTML-Klassifizierung von Short-/Videoseiten |
| C16/C18, C26 Capacity/Worker/Runtime-Paths | Autorisierte Jobs, persistenter Status, feste Download-/Parserlimits und Worker-/Mountprüfung | Bestehender Jobpfad bleibt allein maßgeblich; keine automatische Medienjobfreischaltung |

Implementiert bedeutet hier nicht allgemein produktionsfreigegeben. B3 besitzt
den vom Betreiber berichteten Realnachweis, andere Adapter den jeweils dokumentierten
Offlineumfang. Reale Medien-/Short-/Google-Slides-Verarbeitung und Lastverhalten
sind **nicht abgenommen**. Nicht implementierte Cloud-STT-/WhisperLive-Provider
bleiben ausdrücklich `NotImplementedError`, keine Ersatzfunktion.

## F0–F6 und Zustandsvertrag

`MediaRequest` (Schema 1) ist ein kleiner Planungsinput um vorhandene
MaterialResource-, SourceApproval- und SelectionPolicy-Verträge. Pro Request
werden ein Kurs, eine **eindeutige Lecture**, ein Zweck und Text-/Visualbedarf
benannt. Optional grenzt `subject_id` auf genau einen Short und dessen tatsächlich
bekannte Kinder ein. Ein Lecturetranskript gilt dadurch nicht als Shorttranskript.
Eine geänderte Lecture, ein anderer Zweck oder veränderte Bytes benötigen neue
gebundene Entscheidungen.

| Stufe | Prüfschritt | Bei fehlendem Beleg |
| --- | --- | --- |
| F0 | Explizite lokale Artefakte, aktuelle Process-Grants, Raw-/Receipt-/Payload-/Parser-/Graphbindung; zweckgebundene Eignung | Integritäts-/Grantfehler sperren; unbekannte Eignung erlaubt keine Eskalation |
| F1 | Passendes offizielles Transkript vor Medien, SRT/VTT/TXT getrennt nach tatsächlichem Adapter | Nicht freigegebene Referenz bleibt blockiert; VTT besitzt noch keinen gebundenen C26/B5-Publikationsadapter |
| F2 | Notes, PDF/Folien, Code, Aufgaben | Ergänzungen und fehlende Visuals separat; keine automatische inhaltliche Gleichsetzung |
| F3 | Bekannte Präsentations-/Shortreferenzen; vorhandene dokumentgebundene Bildbytes | Google-Slides-Export-/Shortquellenbindung fehlt; keine automatische Beschaffung |
| F4 | Ausdrücklich benannte lokale Medien mit eigenem freigegebenem Rawhash | Lokaler Fallback vorschlagbar; begrenzter C26-Execution-/Codec-/Modellreceiptadapter fehlt weiterhin |
| F5 | Remoteaudio nur für noch fehlenden Text, nach ausgeschöpften bekannten Alternativen | Eigene Download-/Process-Grants, Schätzung und Kapazität nötig; Ausführung bleibt gesperrt |
| F6 | Remotevideo als letzter Vorschlag; Audio hilft nicht bei rein visuellem Bedarf | Gesonderte Quellenfreigabe und Medienvertrag nötig; keine Downloader-/DRM-Umgehung |

Nicht passende oder ausgeschöpfte Alternativen werden entweder aus beobachteten,
hashgebundenen Eignungsentscheidungen oder expliziten `Unavailability`-Belegen
abgeleitet. Ein freies Flag `verified=true` ist kein Input. `access_denied` und
`technical_failure` autorisieren keinen anderen Downloader oder nächsten Pfad:
solange noch Inhalt fehlt, ist eine neue Betreiberentscheidung nötig. Wenn bereits
ausreichende lokale Materialien vorliegen, verhindert ein unbeteiligter früherer
Medienfehler deren Wiederverwendung nicht.

Der Zustandswortschatz enthält `available_local`, `available_remote`, `verified`,
`approved`, `unsupported`, `missing`, `blocked`, `not_required`,
`requires_visual_context`, `ready_for_processing`. Ohne HTTP-Beleg wird
`available_remote` **nicht** gesetzt: URLs sind nur `remote_reference=true` und
`remote_availability=not_checked`. `missing` bedeutet hier fehlendes explizites
lokales Artefakt, keinen Nachweis weltweiter Nichtexistenz. `ready_for_processing`
verlangt verifizierte lokale Artefakte und einen vorhandenen gebundenen Adapter;
eine freigegebene Remotequelle ist zunächst nur zur Beschaffung vorgeschlagen.

Verfügbarkeit, technische Verarbeitbarkeit, Zweck-Eignung und fachliche Validierung
sind getrennte Felder. `Adequacy` bindet Material-ID, Raw-SHA, exakten Zweck und
einen tatsächlichen Entscheidungsbeleg; diese Betreiberentscheidung ist **kein**
unabhängiger Goldreview. `human_quality=not_evaluated`,
`knowledge_fact_verified=false` und `execution_supported=false` bleiben erhalten.
Rawmedien allein zählen nicht als fertiger Text. Ein Transkript allein schließt
keine fehlende visuelle Evidenz. Visuelle Wiederverwendung braucht zusätzlich
vorhandene geprüfte Bildbytes im Materialhandoff und eine passende Eignungsentscheidung.
Vektoren, Kapitel oder Slideslinks sind zunächst Referenzen, keine interpretierten
Diagramme. Grafische Semantik benötigt weiterhin unabhängigen Review.

## Shorts und Präsentationen: tatsächliche Referenzen

Im versionierten CS50P-Week-0-Snapshot stehen bereits fünf eigenständige `short`-
Ressourcen. Jeder besitzt seine bestehende Source-/Material-ID, Lecturebindung,
Original-URL und den dokumentierten Titel als Themenlabel:

| Short | Dokumentierte URL |
| --- | --- |
| Visual Studio Code for CS50 | <https://cs50.harvard.edu/python/shorts/visual_studio_code_for_cs50/> |
| Functions | <https://cs50.harvard.edu/python/shorts/functions/> |
| Variables | <https://cs50.harvard.edu/python/shorts/variables/> |
| Return Values | <https://cs50.harvard.edu/python/shorts/return_values/> |
| Side Effects | <https://cs50.harvard.edu/python/shorts/side_effects/> |

Diese Seiten sind keine Notes. Ihre konkreten Medien-/Transkriptquellen, Sprachen,
Laufzeiten und Hashes wurden nicht erhoben und werden nicht aus Slugs erfunden.
Der bekannte Week-0-Graph besitzt außerdem acht bestehende Medienvarianten,
darunter MP3 sowie Videoqualitäten/Player-/YouTube-Referenzen. Alle Varianten behalten
ihre eigene Material-ID und exakte URL; eine Freigabe einer Variante gilt nicht
für andere Formate, Auflösungen, Player oder Downloader.

Die vorhandene Google-Slides-Referenz
<https://docs.google.com/presentation/d/1yPirrSP2qRjnKiIFW39HJV2cmhwqAkooQkv9jZz2Hqs/edit?usp=sharing>
und das offizielle Lecture-PDF sind getrennte Ressourcen. Reihenfolge:
verifiziertes lokales PDF → freigegebener offizieller PDF-Link → ausdrücklich
genehmigter Export mit nachgewiesener neuer Quellenbindung → Referenz behalten.
Keine Export-URL wird konstruiert, kein HTML-Slideseditor als Folienparser verwendet.
PDF-v2 erhält Seiten-/Blockreihenfolge und Bildreferenzen gemäß bestehendem Vertrag;
nicht extrahierbare Grafik bleibt offen. B6-Pythonartefakte sind über die unten
beschriebene explizite read-only Übergabe wiederverwendbar; ZIP bleibt außerhalb
automatischer C18-Verarbeitung.

## Übergabe vorhandener B6-Codeartefakte

`MediaRequest.include_code_indexes=true` aktiviert dieselbe begrenzte
Codeindex-Erweiterung wie `cs50_batch plan --include-code-indexes`. Der Default
bleibt false; bisherige IDs und die Discoveryauswahl bleiben ohne Opt-in erhalten.
Ein erweiterter Request benötigt einen neuen Plan. Ein alter Reportdigest ist
keine Freigabe für die zusätzliche Auswahl.

Für eine vorhandene B6-Importgruppe verwendet `EvidenceRef.kind="code"` den
expliziten `workspace`, den zugehörigen `batch` und den SHA256 der **exakten Bytes**
des übergeordneten `import.v1.json`. `material_id` bezeichnet die Pythondatei;
`container_material_id` das ausgewählte ZIP, bei einer Einzeldatei deren eigene
Material-ID. Es werden keine Archive nach ähnlichen Dateien durchsucht.

Der Planer prüft Batch/Graph/Importerrevision, Rootauswahl, die vollständige
begrenzte Dateiliste, Eltern-/Mitgliedshashes und aktuelle Process-Grants der
gesamten Importgruppe einschließlich Geschwisterdateien. Anschließend wird der
vorhandene C10-/Handoff erneut read-only geprüft. Kein Import, Staging, ASTprozess,
ZIPentpacken oder Start des Codes. Widerruf, unklare Zuordnung oder manipulierte
Artefakte sperren die Eskalation. Ein verifiziertes ZIP allein erfüllt keinen
Textbedarf. `Adequacy` bleibt eine separate zweck- und hashgebundene Entscheidung;
die technische Handoffprüfung bestätigt keine fachliche Codequalität.

## Separater Ressourcenvertrag

Die Dokumentgrenze bleibt **1 MiB**. Medien besitzen ausdrücklich einen eigenen,
rein planenden Vertrag: Audio höchstens 64 MiB, Video 128 MiB, Dauer höchstens
600 Sekunden, Scratchbudget 512 MiB, freie Reserve mindestens 5 GiB, ein Job,
ein CPU-Thread, höchstens 60 CPU-/120 Wallsekunden und 1024 MiB RAM.
Für Visualplanung höchstens vier Zeitfenster, je höchstens 60 Sekunden, zusammen
höchstens 120 Sekunden und zwölf Frames; keine Beschaffung dieser Frames.

Eine `MediaEstimate` benötigt einen Schätzbeleg. Das ist keine gemessene Laufzeit
oder Containerfreigabe. Preflight prüft deklarierte Grenzen, vorhandene lokale
Bytezahl, Zeitfenster und freien Platz am explizit benannten privaten Probe-Root:
Reserve + zweimal erwartete Rawgröße + Scratchbudget. Unknown/zu groß/zu wenig
Speicher blockiert. Diese Limits werden vor einer zukünftigen Ausführung in einem
isolierten Prozess/Cgroup verbindlich durchzusetzen sein. B7 behauptet **keine**
bereits durchgesetzten Whisper-/ffmpeg-Limits oder überprüften aktiven Hostjobs.
Jeder Medienvorschlag enthält daher `bounded_media_execution_adapter_missing`.
Große Gesamtlectures passen bewusst nicht in diesen Erstvertrag.

## Runbook: Plan im vorhandenen Worker, späterer Realpilot separat

Erforderlich sind Review/Merge, kontrolliertes Codeupdate desselben Workers,
benannter neuer privater Arbeits-/Ausgaberoot mit gültiger Mount-Policy und
Workerrechten, freigegebene Metadatensnapshots und einzeln benannte Artefakte.
Keine Suche privater Archive, keine Root-/Sourcefreigabe durch dieses Beispiel.
Das bestehende Dockerfile kopiert bereits die neue Src-Closure und
`scripts/cs50_batch.py`; kein neuer Entrypoint, keine Dependency- oder Imagearchitektur.

1. Vorhandenes Inventar anzeigen, daraus Lecture-/Short-ID übernehmen:

   ```sh
   : "${C26_B7_MANIFEST:?Verifiziertes Discoverymanifest benennen}"
   : "${C26_B7_ROOT:?Neuen privaten Betreiberroot bestätigen}"
   export C26_PYTHON=/app/.venv/bin/python
   "$C26_PYTHON" -B -m scripts.cs50_batch inventory --manifest "$C26_B7_MANIFEST"
   ```

2. `request.json` privat (0600) als `MediaRequest` Schema 1 ausfüllen. Pflichtfelder:
   `manifest` (exakter absoluter Pfad), `course_id`, `lecture_id`, `purpose`,
   `resource_probe_root` (freigegebener bestehender privater Root). Für Shorts
   zusätzlich `subject_id`. `need_text`/`need_visual` ausdrücklich wählen;
   `policy.allow_transcription` ist standardmäßig false. `evidence`, `adequacy`,
   `unavailable`, `estimates` und `visual_windows` bleiben leer, solange keine
   tatsächlichen Belege vorliegen. Das bloße Ausfüllen erzeugt keine Freigabe.

   `approvals.json` nutzt unverändert `Approvals` / `SourceApproval`: exakte
   Source-/Material-/Course-/URLbindung, getrennte Download-/Process-Flags und
   alle sechs nichtleeren `*_reference`-Belege. Für lokale Reads ist zusätzlich
   `expected_sha256` erforderlich. Ohne neue Freigaben `{"schema_version":1,"sources":[]}`.
   Das ist eine Offline-Betreibererklärung, keine erfundene C16-Identität oder Capability.

3. Read-only planen, Blockaden prüfen; Reports werden nicht überschrieben:

   ```sh
   "$C26_PYTHON" -B -m scripts.cs50_batch media-plan \
     --request "$C26_B7_ROOT/request.json" --approvals "$C26_B7_ROOT/approvals.json" \
     --limits "$C26_B7_ROOT/limits.json" --output "$C26_B7_ROOT/media-plan-01.json"
   ```

   `limits.json` ist der bestehende CapacityLimits-Vertrag mit mindestens 5-GiB-
   Reserve; Medienlimits stehen zusätzlich in `request.limits`. Exit 0 heißt
   Plan/Reuseschritt ohne Blocker, **keine Ausführung oder fachliche Freigabe**;
   1 bedeutet blockierter Plan, 2 ungültiger Input/Zugriff/Output. Auch ein
   fehlender Pflichtbeleg muss sichtbar blockieren. Raw-/Transcripttexte und
   private absolute Rootpfade werden nicht in den Report übernommen.

4. Vorhandene Artefakte erst nach konkreter Lesefreigabe als `EvidenceRef` ergänzen:
   B5-Transkript: `kind=transcript`, `material_id`, `workspace` (bestehender B5-Archivroot),
   `batch` (explizite bestehende Batchdatei), `receipt_sha256` (unabhängig bestätigter
   Receipt-Dateihash). Material: `kind=material`, `workspace`, `plan` und Receiptpin.
   Lokales Medium: `kind=media`, `workspace`, sicherer `relative_path`; dessen Raw-SHA
   kommt aus der individuellen SourceApproval. Absolute-/Traversalpfade oder Symlinks
   innerhalb des relativen Mediumspfades sind unzulässig. Keine Annahme, dass eine
   Hashprüfung bereits Codec, Laufzeit oder semantische Provenienz bestätigt.

   B5-Verifikation öffnet ausschließlich die abgeleiteten Raw-/Receipt-/Payloadpfade,
   prüft aktuelle Grants/Batch/Importerrevision/Modell-/SHA-Verknüpfungen und schreibt
   nichts. Sie führt keinen SRT-Reparse oder Recovery im bestehenden Archiv durch.
   Materialprüfung ruft den bestehenden read-only Quality-/Handoff-Gate erneut auf.

5. Nach tatsächlicher zweckbezogener Betreiberbewertung `Adequacy` mit Material-ID,
   Raw-SHA, identischem Zweck und Entscheidungsbeleg ergänzen. Unbekannt bleibt
   unbekannt. Für ausgeschlossene Alternativen einzelne `Unavailability`-Belege
   festhalten. Referenzen sind keine erfundenen Reviewer oder Goldannotation.
   Neue Pläne mit neuem Ausgabenamen erzeugen. Identischen Wiederanlauf prüfen:

   ```sh
   "$C26_PYTHON" -B -m scripts.cs50_batch media-plan \
     --request "$C26_B7_ROOT/request.json" --approvals "$C26_B7_ROOT/approvals.json" \
     --limits "$C26_B7_ROOT/limits.json" \
     --previous-report "$C26_B7_ROOT/media-plan-01.json" \
     --output "$C26_B7_ROOT/media-plan-repeat.json"
   ```

   Der Digest bindet Request einschließlich privater Pfadidentitäten **nur als Hash**,
   Snapshotdateien, geprüfte Artefakte, Genehmigungen und Implementierung. Alte,
   manipulierte oder inzwischen abweichende Pläne werden abgewiesen; geänderte
   Betreiberentscheidungen brauchen einen expliziten neuen Plan ohne Übernahme
   des alten Reports als Autorisierung. Es gibt keine Medienverarbeitung zu wiederholen.

6. Einen späteren ersten Realtest auf freigegebenes Transkript oder PDF beschränken
   und dafür den vorhandenen B4-/B5-Import verwenden. B7 selbst startet weder Import
   noch C16/C18. Medien erst nach separater Freigabe des neuen begrenzten Executors,
   lokal freigegebenem Modellcache und tatsächlicher Hostkapazität ausführen.
   Wenn dann nötig, lokal vorhandenes Audio vor Remoteaudio, gezielte lokale
   Visualbereiche vor Remotevideo. Keine Downloaderumgehung und keine Vorschläge
   als Shellbefehle aus dem JSON ausführen.

## Coverage und offene Blocker

Der Report enthält alle bekannten Referenzen im deklarierten Lecture-Snapshotscope,
eigene Material-/Variantenstatus, bereits verifizierte Verarbeitung, ausgewählte
Wiederverwendung, fehlende Inhalte, Gründe je Fallback, Genehmigungsflags,
Ressourcenschätzungen und Visualfenster. `referenced_transcript_languages` und
tatsächlich verifizierte `available_transcript_languages` sind getrennt. Zeiten
aus offiziellen SRT-Cues bleiben erhalten; TXT und Referenzen bleiben unbekannt.

Keine vollständige Woche, Lecture oder visuelle Semantik wird daraus abgeleitet:
`full_lecture_coverage=false` gilt auch bei erfülltem begrenztem Textzweck. Die
wesentlichen offenen Punkte sind tatsächliche Short-Unterquellen, VTT-C26-Bindung,
Google-Export-/Nutzungsrechte, B6-Mergeabgleich, abgesicherte lokale Codec-/Dauerprobe,
Modellcache-/Modellhashbindung, begrenzter Medien-/Frameexecutor mit Receipts,
Abbruch-/Wiederanlaufvertrag, reale Ressourcenabnahme sowie unabhängige menschliche
Qualitätsreviews. Vorhandene Legacyfunktionen ersetzen diese Entscheidungen nicht.
