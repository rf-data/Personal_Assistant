# C26-LS-01 – Architekturentscheidung

Basis: `1584a2807c8f9d75604ab17a4ea239d8f4a0882b`, Prüfung vor Implementierung.

| Bereich | Befund und konkrete Wiederverwendung |
|---|---|
| `src/model_lecture/data_resources.py` | `LectureCourse`, `LectureSection`, `LectureResourceUnion` bleiben Kurs-, Abschnitts- und Ressourcenmodelle. Week/Unit sind schmale UI-Erweiterungen, kein neues Discovery-Schema. |
| `src/tools_lecture/` | `adapt_cs50`, `execute_cs50`, `material_handoff.prepare_material_handoff` existieren. Summarizer konsumiert geprüfte Ergebnisse; keine Ausführung von Download, Transkription oder Worker. |
| `src/model_materials/materials.py` | `NormalizedDocument`/`Block` und Parserkonfiguration werden über einen Adapter in vorhandene `ContentBlock` übersetzt. HTML, PDF und Code behalten Original-Locators. |
| `src/model_transcribe/data_transcribe.py` | `TranscriptDocument`/`TranscriptSegment` werden direkt adaptiert; unbekannte Zeit bleibt unbekannt, originale Segment-IDs bleiben erhalten. |
| `src/model_knowledge/` | `ChunkKnowledgeResult` modelliert Knowledge Extraction, kein Summary-Workspace mit Review. Bestehende Evidenzbindung ist Vorbild; keine neue allgemeine Knowledge-Pipeline. |
| `src/tools_knowledge/` | `consolidate_knowledge` ist auf Transcript-/Math-Knowledge zugeschnitten und setzt Zeitintervalle voraus. Summary konsolidiert nur validierte Ausschnitte deterministisch, ohne diese Verträge umzudeuten. |
| `src/llm/model_litellm.py` | `LLMClient.completion` ist die vorhandene austauschbare Abstraktion. Lokaler begrenzter Einstieg ohne Legacy-Dateicache/Callbacks; SDK nur bei expliziter Ausführung importiert. Bestehender Import von nicht vorhandenem `memory.LLMContext` muss entkoppelt werden. |
| `src/content_store/` | `ContentBlock`, `ContentLocator`, `fingerprint` wiederverwenden; Locators unterstützen Zeit, Seite, DOM, Zeilen, Originalhash. Kein direkter Zugriff auf private SQLite-/ACL-Daten. Expliziter lokaler Katalog enthält geprüfte Snapshots, kein Content-Store-Server. |
| `src/job_control/` | `Contract`/`Sha` für strikte, unveränderliche Hüllen; keine Admission, Queue oder C16-Executor-Aufrufe. Lokale exklusive Dateisperre und synchrone sequenzielle Runs. |
| Evaluation | `tools_evaluation.math_syntax.parse_formula` prüft begrenzte Syntax. `evaluation_store` ist ein ACL-/Goldstandard-Workflow, keine Summary-Freigabe. Summary-Review bleibt separat, lokal und append-only. |
| `frontend/pages/`, `frontend/admin_app/` | `show()` und Streamlit-Widgets/Session-State wiederverwenden. Admin-Page startet Parsing/Embedding und lädt schwere globale Konfiguration; deshalb eigener schlanker lokaler Einstieg und eigene Seite. |

## Datenfluss und Vertrauensgrenze

Expliziter lokaler Katalog → vorhandene Kurs-/Ressourcenmodelle → geprüfte
Content-Blöcke + Processing-Artefakt → Inputprüfung → begrenzte Source-Slices →
LLMClient/Fake → Pydantic-Ausgabe → exakte Quellenbindung + Syntaxprüfung →
Abschnittsergebnisse → deterministische Konsolidierung → unveränderliches Ergebnis →
separate Review-Ereignisse → Markdown/JSON.

Keine Originalpfade werden automatisch geöffnet. Pfade und Locators sind Referenzen;
der Workspace zeigt den gesicherten Originalausschnitt einschließlich genauer
Position. Für lokale Dateien ist kein Betriebssystem-Dateisprung integriert.
Ein Katalog ist ein lokaler vertrauenswürdiger Operator-Import, kein kryptographischer
Nachweis einer externen Freigabe. Synthetische Verifikation bleibt sichtbar.

## Bewusste MVP-Grenzen

Extraktive Aussagen: jede Aussage muss wörtlich in jeder angegebenen Quelle stehen.
Das verhindert viele Halluzinationen, beweist aber weder Wahrheit noch sinnvolle
Klassifikation. Freie Paraphrasen, allgemeine semantische Widerspruchserkennung und
mathematische Wahrheit werden nicht zugesichert. Alternative Definitionen und einfache
Negationskonflikte werden zur Prüfung markiert; kein Konflikt wird automatisch gelöst.
Keine zweite Parsing-, Retrieval-, Download- oder allgemeine Lecture-Pipeline.
