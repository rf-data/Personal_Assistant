# A01: CS50-Knowledge-Checkpointvertrag v1

Basis: nach `git fetch origin` unverändert `origin/master` 5718745; PR #24
(optionale SDK-Imports) und #25 (Metadatenmodelle) sind darin integriert.
Implementiert auf separatem Branch `feat/cs50-knowledge-checkpoints`.
Keine Änderungen an allgemeinen Knowledge-Modellen, Promptinstruktionen,
Chunking, SRT-Executor, Inputbinder, Consolidation oder Legacy-Runnern.

## Verwendung und Grenzen

Der bisherige Pilot bleibt ohne Checkpointparameter nutzbar. Neu ist ein expliziter
`--checkpoint-dir`: ein Verzeichnis für **genau einen identischen ausgewählten
Job**. Jeder Aufruf schreibt seine bisherigen Ergebnisverträge in einen neuen,
exklusiven `--output`-Ordner. Nur der separate Checkpointzustand wird wiederverwendet.
Beide Ordner müssen getrennt liegen, außerhalb des produktiven `data/`-Roots.
Der Worker schützt zusätzlich den tatsächlichen Artefaktroot des gebundenen Kurses.
Symlink-Checkpointpfade werden abgelehnt. POSIX/flock und ein lokales Dateisystem
mit atomarem rename/Hardlink sind Voraussetzungen; kein verteilter Lockdienst.

Offline-Vorbereitung, keine API-Freigabe:

```bash
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest /explicit/verified/input.v1.json \
  --output /scratch/pilot-run-1 \
  --checkpoint-dir /scratch/pilot-checkpoint \
  --provider openai_http --max-chunks 1 --evidence-mode segment_v1
```

Wiederaufnahme: dieselben Parameter/Inputdaten und derselbe Checkpointordner,
aber ein neuer Outputordner, z. B. `/scratch/pilot-run-2`. Ein synthetischer
Offline-Checkpoint darf **nicht** als LLM-Ergebnis übernommen werden. Für echte
Aufrufe gelten weiterhin `--execute-llm`, expliziter API-Key und die bestehende
Parent-/Worker-Freigabe. Hier wurde kein solcher Aufruf ausgeführt.
Python Woche 0, maximal zwei Chunks, bestehende Token-/Zeitlimits, keine Retries
und die bisherigen Provider-/Evidence-Defaults bleiben unverändert.

## Ausführungsidentität

`JobIdentity` und `JobCheckpoint` sind neue Ausführungswrapper, keine fachlichen
Knowledge-Modelle. JSON ist kanonisch (UTF-8, sortierte Schlüssel, kein NaN).
`job_id` ist SHA-256 über den vollständigen Identity-JSON-Vertrag:

- course_id, section_key, lecture_id, resource_id und source_id;
- Raw-SRT-/Transcript-SHA-256 aus erneut geprüften Importbelegen;
- Digest des kompletten geprüften CS50KnowledgeInput inkl. URLs, Sprache,
  Transcript-/Discovery-Provenienz und expliziter Artefaktbindung;
- vollständige KnowledgeSettings und Digest **aller** erzeugten Chunks mit Text,
  Cue-IDs, Originalzeiten und Kontext; zusätzlich das ausgewählte Fenster;
- Promptversion und Digest der erzeugten HTTP-Messages für dieses Fenster
  (Systeminstruktionen, Eingabeinstruktionen, Schema und Segmente eingeschlossen);
  beim Legacy-Marvin-Provider dient derselbe fachliche Eingabe-/Schemavertrag als
  Fingerprint, dessen SDK-internes Chat-Framing wurde hier nicht ausgeführt;
- Digest des vorhandenen ChunkKnowledgeResult-Schemas, Ergebnisversion
  `ChunkKnowledgeResult_v1`, Checkpointversion 1;
- Evidence-Modus und Version `chunk_v1` bzw. `cs50_segment_evidence_v1`;
- Provider, Modell, Ausführungsmodus `offline`/`llm` und bisherige Requestlimits.

Einzelne Chunks erhalten zusätzlich ihren vollständigen Payload-Digest.
Absolute Inputpfade sind derzeit Teil der Inputbindung: Verschieben erzeugt
konservativ einen Konflikt. Portable Inputreferenzen bleiben Auftrag A03.
Bei Änderung der Evidence-/Ergebnissemantik müssen Versionen explizit erhöht
werden. Hashes sind Integritätsbelege, keine Signaturen gegen einen Angreifer,
der sämtliche lokalen Receipts und Artefakte kontrolliert.

## Persistenz und Zustände

`checkpoint.v1.json` enthält `schema_version`, `job_id`, `identity`, `status`
und `chunks`. Jobstatus: `pending`, `active`, `done` oder `blocked`, konsistent
abgeleitet aus den Chunkzuständen. **done bezeichnet nur das ausgewählte Fenster,
nicht eine vollständige Vorlesung.** Finale Runberichte sind weiterhin separat.

Ein Chunkreceipt enthält `status`, `chunk_sha256`, die dauerhafte `reservation`,
`artifacts` (drei SHA-256) und sichere Providermetadaten (Usage, Laufzeit,
HTTP-Status, Tokenobergrenze, validiert). Artefakte liegen in einem Unterordner
mit Digest des Chunknamens; feste Namen `provider.json`, `result.json`,
`evidence.json`. Es gibt keine Dateinamenssuche oder Identitätsableitung daraus.

Erlaubte Übergänge:

| Von | Nach | Bedeutung |
|---|---|---|
| pending | request_reserved | Reservierung ist vor Dispatch fsync-persistiert. |
| request_reserved | in_flight | Unmittelbar vor Providertransport. |
| pending | prepared | Validiertes synthetisches Offline-Ergebnis, ohne Request. |
| in_flight | prepared | Ergebnis und Evidenz validiert; erwartete Artefakthashes persistiert. |
| prepared | done | Alle drei Artefakte exklusiv veröffentlicht. |
| pending | failed | Lokaler Fehler vor möglichem Dispatch; kein automatischer Retry. |
| in_flight | failed | Vertrag erlaubt dokumentierten endgültigen Fehler; Pilot behandelt Providerfehler konservativ als unknown. |
| request_reserved / in_flight / prepared | unknown | Ungewisser Versuch bzw. nicht sicher auflösbarer Zustand. |

`done`, `failed`, `unknown` sind terminal. Es gibt in A01 keinen automatischen
Reset und keine CLI zur manuellen Requestwiederholung. Beim Öffnen eines
verwaisten `request_reserved`/`in_flight` werden diese dauerhaft zu `unknown`.
Die Reservierung bleibt erhalten. Eine potentielle kostenpflichtige Antwort
wird niemals durch einen automatischen zweiten Versuch ersetzt.

Der Joblock wird vor Receipt-Laden genommen und bis zur Workerfertigstellung
gehalten. Ein konkurrierender Worker scheitert sofort. Mutable Receipts werden
nur unter diesem Lock atomar ersetzt. Artefakte und normale Pilotausgaben:
Temp-Datei im Zielverzeichnis, fsync, exklusive Hardlink-Publikation,
Verzeichnis-fsync, Aufräumen nur der eigenen temporären Datei. Kein Überschreiben
vorhandener Ergebnisdateien. Ein Kill kann eine eigene Temp-Datei hinterlassen;
sie wird nicht automatisch als Ergebnis adoptiert.

## Resume- und Konfliktpolitik

Vor Initialisierung eines Providers wird das **gesamte ausgewählte Fenster**
geprüft. Resume eines done/prepared-Chunks verlangt:

1. Valides Receiptmodell, passende Jobidentität und tatsächliche Chunkdigests.
2. Alle drei Dateien, passende Hashes, lesbares JSON; keine Symlinks.
3. Reguläres ChunkKnowledgeResult und erneute Bindung über den echten
   `build_cs50_knowledge_document()` mit erneut geprüftem Transcript/Input.
4. Exakte Gleichheit des normalisierten Ergebnisses und der frisch aus Original-
   Cues erzeugten Evidence-Bindung; Provider-Sidecar bleibt separat erhalten.

Dann wird ein prepared-Receipt, dessen Dateien bereits vollständig publiziert
waren, ohne API zu done abgeschlossen. Fehlende Dateien eines prepared-Receipts
sind ein Konflikt: keine Adoption, keine stille Reparatur, kein neuer Request.
Ein vorhandenes done-Receipt mit falschen/fehlenden Artefakten wird abgewiesen;
sein Status allein ist kein Completionnachweis.

Ohne Receipt und ohne vorhandene Artefakte werden pending-Einträge erstellt.
Dateien ohne Receipt, kaputtes JSON, Hashabweichung, fremde Quelle, geänderter
Prompt/Chunkplan/Provider oder unvollständige Ausgabe führen ausdrücklich zu
`CheckpointConflict`; nichts wird gelöscht oder überschrieben. Eine automatische
Neuanlage bei Konflikten ist verboten. Workerreports nennen Fehlerklasse und
Checkpointstatus ohne Credentials oder Providerfehler-Responsebodies.

Beim erfolgreichen Resume werden die bisherigen extraction/consolidated/quality-
Artefakte im neuen Runverzeichnis regulär erneut erstellt. Bereits validierte
Chunkantworten werden gelesen, kein Provider initialisiert, keine neue Anfrage.
Consolidation selbst bleibt unverändert. Legacy-Sidecars sind weiterhin die
Pydantic-Felder vor Bindung; segment_v1 hält die geparsten Providerfelder fest.
Der Checkpoint ist kein vollständiges HTTP-Responsearchiv.

## Schnittstelle für A02

`RequestBudget.before_dispatch(reservation)` wird nach der bisherigen
Budgetprüfung, aber **vor** HTTP-/Marvin-Transport aufgerufen. Der Pilot bindet
sie an `CheckpointStore.reserve(chunk_id, reservation)`. `reserve` schreibt erst
request_reserved und dann in_flight; Schreib-/fsync-/Lockfehler verhindern Dispatch.

Reservation v1 enthält `attempt`, `input_upper_bound`, `output_limit` und
`reserved_tokens`; Job-/Source-/Chunkidentität ist durch das umgebende Receipt
gebunden. A02 kann hier einen gemeinsamen dauerhaften Budgetbeleg/Versuchs-ID
ergänzen. Die jetzige RequestBudget-Zählung ist weiterhin pro Worker; A01 ist
**kein** kursweiter Kosten-/Token-Scheduler und garantiert keine Exactly-once-
Abrechnung beim externen Provider. Ungewisse Reservierungen werden nie freigegeben.
A02 muss globale atomare Reservierung, Usage-Abgleich und eine explizite
Unknown-Auflösung ergänzen, bevor ein Batchrunner sinnvoll ist.

## Tests

Siehe [Testbericht](cs50_knowledge_checkpoint_test_report.md). Ausschließlich
synthetische SRTs, echte Executor-/Import-/Binding-/Chunk-/Evidence-/Consolidation-
Funktionen und Fake-HTTP; keine neuen produktiven Dateien oder SDK-Installationen.
