# C26-B5 – Kontrollierter Offline-Multiformat-Pilot

21.10.2026, Basis master `ac67cd815155d12208cd1b8466842110faff6267` (#141/B4).
**Technische Offline-Erweiterung, keine reale Wochenabnahme.** B3-Pilot 01,
Loviscach, Hetzner, Content-/EvaluationStores, Indizes und bestehende Jobdatenbanken
werden weder geöffnet noch verändert. [B4](week0_pilot.md) bleibt der getrennte
HTML-/PDF-Pfad. Dieser Auftrag führt keine echten Downloads oder Processingjobs aus.

## Inventar und Material-/Adapter-Matrix

Grundlage: ausschließlich das versionierte
[Discoverymanifest](../../course_sources/cs50/manifest.json), vorhandene
`inventory.catalog`, `make_plan` und `parser_for`. Kein Livecrawl. Die neue
`cs50_batch inventory`-Ansicht weist **16 logische Kandidaten, acht Varianten und
208 Link-/Bildvorkommen** der Section `0` aus. Navigation und mehrfach dargestellte
Links zählen als Referenzen, nicht als unabhängige Materialien.
Aktuelle Erreichbarkeit, Nutzungsrechte und Originalhashes sind ungeprüft.

| Material / dokumentierte Quelle | Tatsächlicher lokaler Bestand | Wiederverwendbarer Vertrag / Pilotstatus |
| --- | --- | --- |
| Lecture-Seite `https://cs50.harvard.edu/python/weeks/0/` | `cs50_python/week_0.html`, Discovery-Snapshot | `ResourceCandidate`/Lecture-Zuordnung; Rolle lecture_video bleibt außerhalb C18. |
| Notes `https://cs50.harvard.edu/python/notes/0/` | Referenz; B3-Erfolg nur Betreiberbefund | Bestehendes HTML-v2, Quality und Handoff über B4; keine Wiederverwendung privater B3-Artefakte. |
| Codeindex `https://cdn.cs50.net/python/2022/x/lectures/0/src0/` | `cs50_python/cdn.html`, HTML-Snapshot | Bestehendes HTML-v2 für Indextext; kein rekursiver Python-Download. |
| Aufgabenübersicht `https://cs50.harvard.edu/python/psets/0/` | Referenz | Bestehender gebundener HTML-v2/B4-Pfad. |
| Einzelaufgabe `https://cs50.harvard.edu/python/psets/0/indoor/` | `cs50_python/practice_1.html`, HTML-Snapshot | HTML-v2 vorhanden, aber kein eigenständiger Discovery-Materialkandidat. Kein automatisches Onboarding. Weitere Aufgaben fehlen als gebundene Auswahl. |
| Slides `https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf` | Referenz, kein Raw-PDF in diesem Inventar | Bestehendes PDF-v2/B4, Einzelgenehmigung und 1-MiB-Grenze weiterhin erforderlich. |
| Code-PDF `https://cdn.cs50.net/python/2022/x/lectures/0/src0.pdf` | Referenz | Gleiches PDF-v2; keine Behauptung ausführbarer Quelldateien. |
| Google-Präsentation aus dem Week-0-Snapshot: `https://docs.google.com/presentation/d/1yPirrSP2qRjnKiIFW39HJV2cmhwqAkooQkv9jZz2Hqs/edit?usp=sharing` | Referenz, Format unknown | Kein bestätigter Export-/Downloadvertrag; ausgeschlossen. |
| SRT `https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt` | Nur Referenz, keine hier gelesene Originaldatei | **Neu angebunden:** vorhandener `import_transcript(...format="srt", preserve_empty_cues=True)`, `TranscriptDocument`, `LectureDocument`; lokaler begrenzter Import. |
| TXT `https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.txt` | Nur Referenz | **Neu angebunden:** derselbe vorhandene Importer, Format txt; Zeiten und Dauer bleiben null. |
| ZIP `https://cdn.cs50.net/python/2022/x/lectures/0/src0.zip` | Referenz | Kein geeigneter begrenzter Archivimport in den geprüften Material-/Lecture-/Transcriptkomponenten. Ausgeschlossen, kein `extractall`. |
| Python unter `https://cdn.cs50.net/python/2022/x/lectures/0/src0/` | 96 Linkvorkommen auf **24 Dateinamen**, keine Raw-Python-Dateien | Code-v1 existiert und erhält Codebytes. Die konkreten Links besitzen nur `snapshot_ref`-Identitäten, keine gebundenen `MaterialResource`-Sources; vor Aufnahme explizite Discovery-/Lecture-Bindung nötig. Nichts ausführen. |
| MP3 `https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3` | Referenz plus eine gleichlautende Variante | `LectureMedia`/bestehende Medienwerkzeuge vorhanden; keine automatische Transkription, hier ausgeschlossen. |
| Video: `https://video.cs50.io/JP7ITIXGpHk`, `https://youtu.be/JP7ITIXGpHk` und fünf CDN-MP4-Varianten | Nur Referenzen | Vorhandene Lecture-/Downloadkomponenten; Medienbudgets und separate Rechte fehlen, kein Download/Whisper. |
| Fünf Shorts unter `https://cs50.harvard.edu/python/shorts/`: `visual_studio_code_for_cs50/`, `functions/`, `variables/`, `return_values/`, `side_effects/` | Nur Landingpage-Referenzen | Rolle short bleibt ausgeschlossen; kein Nachladen eingebetteter Videos oder Umdeklarieren zu HTML-Dokumenten. |

Die Python-Dateinamen sind exakt `calculator0.py` bis `calculator11.py` und
`hello0.py` bis `hello11.py`, jeweils mit Direktlink und den drei Queryvarianten
`?download`, `?highlight`, `?view`. Keine davon wird automatisch normalisiert,
als Rawdatei behandelt oder heruntergeladen. Der Inventarreport erhält sämtliche
URLs, Provenienzlocatoren, Varianten und bisherigen Source-IDs. Er unterscheidet
`versioned_html_snapshot`, `reference_only`, `not_processed` und Adapterstatus.
Zusätzliche private Rohbestände wurden nicht gesucht. Fehlende lokale Inputs
erscheinen beim expliziten Import als `missing`; fehlende Rechte als `blocked`.

Die vier relevanten lokalen HTML-Metadatensnapshots sind Kursindex, Week 0,
Codeindex und Indoor-Aufgabe. Andere Kurswochen werden nicht als Week-0-Bestand
gezählt. **Fünf vorhandene C18-Materialadapter plus zwei Transcriptadapter ergeben
keinen Nachweis vollständiger Wochenabdeckung.** Alle Reports setzen
`full_week_coverage=false`; fachliche Qualität bleibt `not_evaluated`.

## Tatsächliche Wiederverwendung und PR #9

[PR #9](https://github.com/rf-data/Personal_Assistant/pull/9), Branch
`feat/official-transcript-import`, Head
`3d1317347018fce47f49331fbfea92e4a055a337`, wurde am 21.10.2026 **offen** gelesen.
Sein Head ist kein Vorfahr dieser Basis. Der Importercode ist aber bereits über
`b2e4b2f` integriert und unter anderem in C23-05/`2e60d15` weiterentwickelt worden.
B5 verwendet ausschließlich den aktuellen Masterimporter. Kein Merge, Cherry-pick,
Ändern oder Schließen von #9; keine zweite SRT-/TXT-Parsingimplementierung.

Die dünne Ergänzung `src.tools_materials.transcripts` verwendet vorhandene
`Batch`, `SourceApproval`, `CapacityLimits`, Discovery-/Materialbindungen,
`LectureDocument`, `TranscriptDocument`, Timestampvalidierung, flock und exklusive
fsync-/Linkpublikation. Nur der fehlende, strikt versionierte `TranscriptReceipt`
bindet Raw-/Payloadhash, exakte Lecture-/Source-/URL-/Sprachidentität, Batch,
Freigabedigest und tatsächliche Importer-/Modell-/Adapterrevision. Er ist **kein**
C18-`NormalizedDocument` und keine neue Queue. Die bisherigen SRT-only-
`CS50TranscriptBinding`-/Knowledge-/Executorverträge bleiben unverändert.

SRT-Überlappungen, Reihenfolge und leere Cues bleiben erhalten; rückwärts laufende
Cue-Startzeiten werden gemäß bestehendem Executorvertrag abgewiesen. Originale
Cue-Nummern, BOM, CRLF und Markup bleiben in den unveränderten Rawbytes erhalten.
Das bestehende Segmentmodell vergibt nullbasierte `seg_id`, bewahrt also die
ursprüngliche Cue-Nummer **nicht** als eigenes JSONfeld. Präsentationstags werden
durch den vorhandenen Importer normalisiert. TXT erhält LF-normalisierte Texte
einschließlich Einrückung/Unicode, `start=end=duration=null`; timed Knowledgepfade
bleiben gesperrt. `acquired_at` bezeichnet Importzeit, keinen Vorlesungstimestamp.

## Begrenzung und Wiederanlauf

- Genau ein oder zwei explizit ausgewählte SRT-/TXT-Sources aus CS50P Section 0,
  jeweils mit eindeutiger tatsächlicher Lecture-Zuordnung und Sprache.
- Maximal 1 MiB Raw je Source, 20.000 Segmente und 8 MiB normalisiertes JSON;
  Archivbudget höchstens 64 MiB, freie Reserve mindestens 5 GiB. Private
  0700-Verzeichnisse/0600-Ausgaben, bestehende Mount-/Codepfadprüfung unverändert.
- Serialisierung per nonblocking Archivlock. Keine Worker/Threads, HTTP-Retries,
  neuen Downloads, LLMs oder neuen Dependencies. Der begrenzte direkte Importer
  ist kein C18-Guardianjob; dessen CPU-/Zeit-/Memorylimits werden nicht als hier
  ausgeführter Nachweis ausgegeben. Nur einen manuellen Importprozess starten.
- Explizite Inputdateien, keine Verzeichnissuche; Symlinks, `..`, Spezialdateien,
  falsche Graphbindung, fehlender erwarteter SHA oder process-Freigabe abweisen.
  Die process-Freigabe ersetzt keine download-Freigabe. Offline genügt download=false.
- Neuer Archivroot; vorhandene leere oder fremde Ziele werden nicht übernommen.
  Receipt wird zuletzt unveränderlich publiziert. Wiederholung liest aktuelle
  Freigaben, prüft Originalhash und Archivbytes, reimportiert die eigene begrenzte
  Rawkopie zum Inhaltsabgleich und verwendet bei Übereinstimmung dieselben Bytes.
- `report` benötigt die ursprünglichen Inputdateien nicht; es prüft freigegebene
  Archivbytes und verwendet kurzlebiges eigenes Staging unter demselben Lock.
  Reports sind daher keine ausschließlich statende read-only-Dateisystemoperation.
  Geänderte Revision/Grants, fehlende/manipulierte Artefakte oder halbe Publikationen
  bleiben gesperrt. Kein automatisches Reparieren, Löschen oder Überschreiben.
  Für unvollständige Publikationen Diagnose und separat genehmigter neuer Root.
- Keine C18-/Knowledgepublikation, kein Import in globale Stores. Der Report enthält
  Metadaten/Hashes, keine Originaltexte oder absoluten Inputpfade. Kein Dateihash
  ist eine digitale Signatur oder ein unabhängiger fachlicher Qualitätsbeleg.

## Ausführbarer lokaler Offline-Pilot nach Einzelgenehmigung

Voraussetzungen: integrierte B5-Revision, vorhandene Umgebung, ein **neu genehmigter**
privater Arbeitsroot außerhalb des Checkouts bzw. einer bereits autorisierten
Mount-Policy, ein unveränderliches Discoverybundle und genau benannte lokale
Originaldateien samt vertrauenswürdig bestätigten SHA256. Keine Originalübernahme
aus Pilot 01. Nachfolgende Befehle sind eine Betreiberanleitung, keine bereits
ausgeführten Realaktionen. Für den ersten Offlinepfad werden keine C16-Tokens
erzeugt, da weder Controller noch Jobs gestartet werden.

```sh
set -eu
umask 077
: "${C26_PYTHON:?Vorhandene Pythonumgebung benennen}"
: "${C26_DISCOVERY:?Genehmigtes Discoverybundle mit manifest.json benennen}"
: "${C26_MULTIFORMAT_ROOT:?Neuen genehmigten privaten Arbeitsroot benennen}"
: "${C26_SRT_INPUT:?Exakte genehmigte lokale SRT-Datei benennen}"
: "${C26_TXT_INPUT:?Exakte genehmigte lokale TXT-Datei benennen}"
export C26_MULTIFORMAT_ROOT C26_SRT_INPUT C26_TXT_INPUT
# mkdir ohne -p: vorhandene Ziele/fehlende Eltern stoppen den Ablauf.
mkdir -m 700 -- "$C26_MULTIFORMAT_ROOT"
"$C26_PYTHON" -B -m scripts.cs50_batch inventory \
  --manifest "$C26_DISCOVERY/manifest.json" \
  --output "$C26_MULTIFORMAT_ROOT/inventory.json"
```

Limits **vor** plan erzeugen, weil dessen Output ebenfalls die Reserve prüft:

```sh
"$C26_PYTHON" -B - <<'PY'
import os
from pathlib import Path
from src.tools_materials.capacity import CapacityLimits, MIB
from src.tools_materials.batch import output
root = Path(os.environ['C26_MULTIFORMAT_ROOT'])
limits = CapacityLimits(reserve_bytes=5*1024**3, archive_bytes=64*MIB,
                        catalog_bytes=128*MIB, job_bytes=512*MIB,
                        report_bytes=16*MIB, max_materials=2)
output(root/'limits.json', limits.model_dump(mode='json'))
PY
"$C26_PYTHON" -B -m scripts.cs50_batch plan \
  --manifest "$C26_DISCOVERY/manifest.json" --course cs50_python \
  --resource resource:fde25833bbf19ce14828f9b719ded15fe02cc15f313551b1357c34f571f5e0b5 \
  --resource resource:a2e464b6c0f9c80ee12ba8d455675b7131d46b95810e990e537577f3f904cfe6 \
  --limits "$C26_MULTIFORMAT_ROOT/limits.json" \
  --output "$C26_MULTIFORMAT_ROOT/batch.json"
```

Diese gesperrte Freigabevorlage erzeugt nur Konfiguration, liest keine Originaltexte:

```sh
"$C26_PYTHON" -B - <<'PY'
import os
from pathlib import Path
from src.tools_materials.batch import SourceApproval, load_batch, output
root = Path(os.environ['C26_MULTIFORMAT_ROOT'])
batch = load_batch(root/'batch.json')
sources, inputs = [], {}
for b in batch.materials:
    row = dict(material_id=b.material_id, source_id=b.source_id,
               course_id=b.resource.course_id, original_url=b.original_url,
               download=False, process=False, expected_sha256=None)
    row.update({n: 'PENDING_OPERATOR_DECISION' for n in SourceApproval.model_fields
                if n.endswith('_reference')})
    sources.append(row)
    inputs[b.source_id] = os.environ['C26_'+b.format.upper()+'_INPUT']
output(root/'approvals.json', dict(schema_version=1, sources=sources))
output(root/'inputs.json', inputs)
PY
```

**Jetzt menschliche Einzelentscheidung:** je Source alle sechs `_reference`-Felder
mit tatsächlichen Belegen ersetzen, `expected_sha256` aus dem geprüften lokalen
Original belegen und ausschließlich nach Verarbeitungsgenehmigung `process=true`
setzen. Platzhalter sind keine Genehmigung. Download bleibt false, sofern keine
separate Downloadentscheidung vorliegt. Die zwei vorhandenen Referenzen sind
englisch (`en`) und derselben Lecture-0-Identität zugeordnet:
`resource:4305fcd17cb0d9c50cfdd5e2718461e8369cb883189de96bda796f04cc800192`.
Für andere Dateien/URLs/Sprachen reicht diese Konfiguration nicht aus.

```sh
"$C26_PYTHON" -B -m scripts.cs50_batch transcripts preview \
  --batch "$C26_MULTIFORMAT_ROOT/batch.json" \
  --archive "$C26_MULTIFORMAT_ROOT/transcripts" \
  --approvals "$C26_MULTIFORMAT_ROOT/approvals.json" \
  --inputs "$C26_MULTIFORMAT_ROOT/inputs.json" \
  --limits "$C26_MULTIFORMAT_ROOT/limits.json"
# Preview öffnet keine Originalinhalte und erteilt keine Hash-/Kapazitätsfreigabe.
# Erst nach Prüfung und ausdrücklicher lokaler Verarbeitungsgenehmigung:
"$C26_PYTHON" -B -m scripts.cs50_batch transcripts import --confirm \
  --batch "$C26_MULTIFORMAT_ROOT/batch.json" \
  --archive "$C26_MULTIFORMAT_ROOT/transcripts" \
  --approvals "$C26_MULTIFORMAT_ROOT/approvals.json" \
  --inputs "$C26_MULTIFORMAT_ROOT/inputs.json" \
  --limits "$C26_MULTIFORMAT_ROOT/limits.json" \
  --output "$C26_MULTIFORMAT_ROOT/import-report.json"
"$C26_PYTHON" -B -m scripts.cs50_batch transcripts report \
  --batch "$C26_MULTIFORMAT_ROOT/batch.json" \
  --archive "$C26_MULTIFORMAT_ROOT/transcripts" \
  --approvals "$C26_MULTIFORMAT_ROOT/approvals.json" \
  --limits "$C26_MULTIFORMAT_ROOT/limits.json" \
  --output "$C26_MULTIFORMAT_ROOT/verification-report.json"
```

Exit 0: ausgewählte technische Operation erfolgreich; 1: mindestens ein Material
blocked/missing; 2: Input-/Konfigurations-/Ausgabekonflikt. Kein Exitcode bedeutet
fachliche Freigabe. Unter `<material-hash>/` liegen `source.srt` oder `source.txt`,
`transcript.json` und `receipt.json`; Quelle und Payload mit `sha256sum` gegen den
Receipt prüfen. Berichtdateien werden niemals überschrieben. Wiederanlauf mit
demselben Importbefehl **ohne** bereits verwendeten `--output`, oder neuem expliziten
Reportnamen; bestehende erfolgreiche Raw-/JSON-/Receiptbytes bleiben identisch.
Teilweise fehlende Inputs dürfen nach tatsächlicher Bereitstellung separat erneut
versucht werden. Unvollständige Archivpublikationen bleiben dagegen blockiert.

## Weitere Integration und noch nötige Entscheidungen

C26-B7 ergänzt einen ausdrücklich nicht ausführenden
[Media-last-Planungs- und Coveragevertrag](media_last_pilot.md). Die nachfolgenden
Medien-/Shortsentscheidungen bleiben für die reale Ausführung erforderlich;
Legacy-Medienfunktionen werden dadurch nicht automatisch freigegeben.

1. Python: eine begrenzte explizite Dateiliste aus dem Snapshot auswählen, URLs
   inklusive Queryform entscheiden, echte Discovery-/Lecture-/Sprachbindungen
   ergänzen und unabhängig testen. Erst dann Code-v1 mit bestehenden C26/B4-
   Freigaben, 1-MiB-Limit, Quality/Handoff; keine Ausführung von Pythoncode.
2. ZIP: vor Implementierung entry-count-/gesamt-entpackt-/Kompressionsratenlimits,
   Verbot von Traversal, Symlinks, Hardlinks, Spezial-/verschlüsselten Dateien,
   Namenskonflikten und verschachtelten Archiven beschließen. Jeden entpackten
   Inhalt an Originalarchiveintrag plus beide Hashes binden. Ohne diesen Vertrag
   ist Weglassen sicherer als ein paralleler generischer Entpacker.
3. Weitere HTML-Aufgaben: konkrete Quellenbindung/Week-Zuordnung aus begrenzten
   bestehenden Snapshots ermöglichen, keine rekursive Linkauflösung. HTML-v2
   wiederverwenden; Snapshot allein ist kein freigegebenes HTTP-/Receiptbundle.
4. Shorts/Audio/Video: tatsächliche Medien- und Untertitelquellen erst explizit
   inventarisieren und freigeben. Bestehende Medienwerkzeuge sind kein genehmigter
   Whisper-/Cloudpfad. Keine Erhöhung der Pilotdateigrenzen, keine Videobudgets
   aus HTML-/Transcripterfolgen ableiten.
5. Hetzner: B5 ist noch nicht deployed. Das bestehende Image kopiert bereits
   `scripts/cs50_batch.py` und ganz `src`, die Dependencygruppe genügt diesem
   Adapter. Keine Dockerfile-/Mount-/Start-/Restartänderung nötig. Ein späteres
   Update desselben Workers sowie neue private Ziele/Mount-Policy und Original-
   bereitstellung bedürfen separater Betreiberfreigabe. Kein zweiter Container.

Aktuell fehlen reale SRT-/TXT-Rohdateien mit bestätigten Hashes, deren individuelle
Verarbeitungs-/Nutzungsentscheidungen und ein genehmigter neuer Ausgaberoot.
Keine automatische Kenntnisübernahme aus historisch anders gebundenen SRTs (D06),
keine fachliche Goldfreigabe und keine Behauptung einer vollständigen Kurswoche.
Tatsächliche Prüfungen: [Validierungsbericht](multiformat_validation.md).
