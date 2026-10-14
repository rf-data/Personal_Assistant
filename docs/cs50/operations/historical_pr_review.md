# Historische PRs #6, #9, #10 und #11

Prüfbasis: master `8ba519ed04c04c92573594ebe74b69a3c00aab1b`, GitHub-Metadaten und
aktuelle PR-Patches am 14.10.2026. Alle vier PRs sind noch offen. Keine Schließung
oder Merge-Aktion wurde ausgeführt. „Ersetzt“ bezeichnet den fachlichen Vertrag,
nicht identische Commit-Historie oder identischen Text.

| PR | Einordnung | Nachweis / noch relevante Änderungen | Empfehlung |
|---|---|---|---|
| #6 | Vollständig funktional ersetzt | Discovery-/Selection-Modelle, Manifestloader, Parser und Tests liegen in master; inzwischen sechs statt vier Kurse und 50 vollständige Vorlesungen. Der aktuelle PR-Patch enthält alte Manifest-/Fixture- und Modellstände. | Nach manueller Bestätigung als ersetzt schließen. Nicht den alten Branch zurückmergen. |
| #9 | Teilweise integriert, relevanter Rest | Offizielle SRT-/VTT-/TXT-Importer, Provenienz-Enum und SRT-Pfad vorhanden. **Fehlt weiterhin:** TranscriptSegment.start/end akzeptieren None noch nicht; der damalige explizite Unknown-Time-Guard im zeitbasierten Chunker fehlt ebenfalls. Sechs TXT-Tests scheitern unverändert. | TXT-Unknown-Time-Vertrag als kleinen separaten Reparatur-PR behandeln, inklusive Folgefunktionen/Legacy-Kompatibilität. Danach #9 als ersetzt schließen; keine ungeprüfte Komplettübernahme. |
| #10 | Vollständig funktional ersetzt | Optionaler source_id-Vertrag, Konsolidierungs-Guard und gemeinsame Metadatenweitergabe in Extraction/deterministischer/semantischer Consolidation vorhanden; SDK-Lazy-Imports ebenfalls durch spätere Arbeiten abgedeckt. 11 Source-ID-, 41 Provenienz- und 4 Lazy-Import-Regressionsfälle in der Abschlussbaseline bestanden. | Als ersetzt schließen nach manueller Reviewbestätigung. Der alte Patch würde frühere Modell-/Importvarianten erneut einführen. |
| #11 | Vollständig ersetzt | consolidate_knowledge.py importiert normalize_math_text tatsächlich aus src.utils.latex_helper. Der echte Modul-/Formelkonsolidierungstest ist enthalten und bestand auch im aktuellen master-Lauf. | Nach manueller Bestätigung als ersetzt schließen; kein weiterer Produktionspatch nötig. |

Konkrete Produktionsnachweise: `src/model_discovery/cs50.py`,
`src/tools_lecture/prepare_cs50.py`, `src/tools_transcribe/import_transcript.py`,
`src/model_transcribe/data_transcribe.py`, `src/model_knowledge/data_knowledge.py`,
`src/run_knowledge_extraction.py`, `src/tools_knowledge/find_knowledge.py`,
`src/tools_knowledge/consolidate_knowledge.py`,
`src/tools_knowledge/semantic_knowledge.py`, `src/utils/llm_helper.py`.

Ungeklärter TXT-Rest ist kein SRT-Integrationsfehler und wurde in diesem
Dokumentations-/Bereinigungsauftrag nicht repariert. Keine Assertions,
Knowledge-Modelle, Chunking- oder Evidence-Algorithmen geändert.
