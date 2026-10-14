# Post-Merge-Audit: CS50 und Knowledge

Stand: 14. Oktober 2026. Geprüfter `origin/master` nach `git fetch origin`:
`f4f5f3571304aff5a88219d42b3506cd12b56ddb`. Der ursprüngliche IDE-Arbeitsbaum
blieb unverändert. Prüfungen und Fixture-Korrekturen erfolgten in einem separaten
Worktree auf Branch `audit/post-merge-fixtures`.

## Ergebnis

Der unveränderte saubere Master erreicht **128 passed, 58 failed, 174 errors,
2 skipped** bei 362 Fällen (53,72 s). Mit ausschließlich ergänzten Discovery-
Fixtures und dem portablen Adapterplan: **325 passed, 33 failed, 0 errors,
4 skipped** (250,68 s). Die beiden neuen Fixture-Vertragstests bestehen zusätzlich.
Die Gesamtsuite ist damit ausdrücklich noch nicht grün.

Erneute Prüfung aus einem weiteren sauberen Checkout des Fixture-Commits
`20574a0`: Discovery, Extraction, Full Coverage, beide Selection-Modi,
sechs Kurse, Lecture-Adapter, Fake-Executor und neue Fixture-Verträge:
**200 passed, 1 skipped in 163,21 s**. Der Skip ist ausschließlich der optionale
originale lokale SRT-Test. Kein Runtime-Pilotartefakt wurde hineinkopiert;
`git status --short` blieb leer. Der mitversionierte synthetische Pilot-Testhelper
bestand dort ebenfalls: **5 passed in 19,39 s**. Ruff-Lint und Formatprüfung
beider neuen Python-Testdateien bestanden.

```bash
uv run --offline --no-sync python -m pytest \
  tests/test_cs50_fixture_checkout.py tests/test_cs50_discovery.py \
  tests/test_cs50_extraction.py tests/test_cs50_full_coverage.py \
  tests/test_cs50_selection.py tests/test_cs50_six_courses.py \
  tests/test_cs50_timed_selection.py tests/test_cs50_lecture_adapter.py \
  tests/test_cs50_executor.py -q
```

Dabei wurde wie unten dokumentiert UV_PROJECT_ENVIRONMENT auf die vorhandene
Worker-Umgebung gesetzt. Die großen HTML-Snapshots wurden ohne automatisch
formatierende Commit-Hooks aufgenommen, um die geprüften Bytes zu bewahren;
Hash-, Test-, Lint- und Formatprüfungen erfolgten ausdrücklich separat.

Der frühere lokale Audit auf `bd5491e` berichtete 309/25/0/1 bei 335 Fällen,
hatte jedoch ignorierte Originalfixtures und den lokalen Pilot zur Verfügung.
Die neuen 362 Fälle umfassen zusätzliche Qualitäts-/Präzisionstests. Daher sind
die Rohsummen nicht direkt vergleichbar: Die damaligen 25 Fehler bestehen
unverändert; die acht zusätzlichen Fehler entstehen im sauberen Checkout durch
fehlende Pilot-Eingänge, nicht durch einen nachgewiesenen neuen Algorithmusfehler.

Die fehlenden HTML-/JSON-Dateien erklären sämtliche 174 Setup-Fehler und
weitere Discovery-Ausfälle. Die sechs TXT-Fehler, 14 Provenienzfehler, vier
Lazy-Import-Fehler und ein SDK-Smoke-Fehler bleiben unverändert. Acht weitere
Fehler betreffen maschinenlokale Pilot-Testeingänge. Diese werden nicht durch
Versionierung produktiver Transkripte oder Belege verdeckt.

Eine separate reproduzierbare **synthetische** Laufzeitprobe erzeugt SRT,
Download-/Importbelege und Knowledge-Eingabemanifest ausschließlich temporär
mit Fake-HTTP. Fünf vorhandene Tests bestehen damit gemeinsam: Legacy-Pilot,
Zwei-Chunk-Pilot, präziser `segment_v1`-Pilot, ungültige Präzisionsreferenzen
und unverarbeitete Providerfelder. Die echte deterministische Consolidation
wird durchlaufen. Das ist kein erneuter Test des originalen lokalen SRT-Piloten
und kein LLM-Lauf. Es werden auch keine 157 Chunks verarbeitet.

## GitHub und tatsächliche Basis

GitHub meldet #12–#20 als geschlossen und gemergt. Entscheidend ist der Zielbranch:

| PRs | Merge-Ziel laut aktuellem GitHub-Status | Bedeutung für master |
|---|---|---|
| #12, #13 | `fix/knowledge-source-id` | Provenienz und Lazy-Helper liegen noch auf dem offenen #10-Branch; ihre Merges allein integrieren sie nicht in master. |
| #14, #15, #17 | `feat/cs50-full-coverage` | Feature-Stack; große Codeanteile sind über die Sammelcommits in master, Fixtures fehlen dort. |
| #16 | `feat/cs50-lecture-adapter` | Teil des Feature-Stacks, keine direkte master-Merge-Zusage. |
| #18 | `feat/cs50-knowledge-input-binding` | Teil des Feature-Stacks. |
| #19, #20 | `master` | Echte master-Merges `9d2d679` und `f4f5f35`: Qualitätsreport, Chunk-Auswahl und präziser Evidenzmodus vorhanden. |

`b2e4b2f` und `bd5491e` integrieren zuvor zahlreiche CS50-/Knowledge-Dateien.
Gleiche Funktionalität bedeutet hier nicht gleiche Commit-Abstammung. `git cherry`
meldet für die vier offenen Branches ausschließlich `+`; das beweist fehlende
Patch-Äquivalenz, nicht fehlende fachliche Implementierung. Verglichen wurden
deshalb zusätzlich Dateien, echte Tests und simulierte Dreiwege-Merges.

## Umgebung und Reproduktion

Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4, HTTPX 0.28.1,
BeautifulSoup 4.15.0, pydantic-settings 2.15.0, tiktoken 0.14.0.
OpenAI, Marvin und pydantic-ai sind in dieser bestehenden lecture-worker-
Umgebung nicht installiert. Der vollständige Paketstand steht in
`docs/course_sources/cs50/post_merge_environment.txt`; pyproject.toml und uv.lock wurden nicht geändert.

Versucht wurde im frischen Worktree:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv sync --offline --locked --extra lecture-worker --group dev
```

Das scheitert bei der Metadatenerzeugung des nicht gecachten direkten
`de-core-news-sm==3.8.0`-Wheels. Obwohl das NLP-Extra nicht ausgewählt ist,
benötigt der aktuelle uv-Sync diese Metadaten. Es wurde weder nachgeladen noch
eine Dependency aktualisiert. Eine vollständig neu synchronisierte Umgebung
ist daher noch nicht nachgewiesen. Die folgenden Tests verwenden denselben
regulären vorhandenen uv-Interpreter im isolierten Code-Worktree, ohne Sync:

```bash
# UV_PROJECT_ENVIRONMENT zeigt auf die bereits installierte lokale Worker-.venv.
UV_PROJECT_ENVIRONMENT=/path/to/installed-worker/.venv UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest tests -q --junitxml=/tmp/post-merge.xml

UV_PROJECT_ENVIRONMENT=/path/to/installed-worker/.venv UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python tests/helpers/cs50_postmerge_pilot_probe.py
```

Die Probe verwendet Platzhalter, sperrt Socket-Verbindungen und liefert nur
Fake-HTTP-Antworten. Die Testmodul-Konstanten für Workspace/Manifest werden
innerhalb dieses separaten Testprozesses auf temporäre synthetische Eingänge
gebunden; produktive Module bleiben unverändert. Die reguläre Gesamtsuite
behält ihre acht entsprechenden Fehler, bis ein separater Testfixture-PR die
lokale Pilotabhängigkeit grundsätzlich beseitigt.

## Nachgewiesene Fehlergruppen und Folgeaufträge

| Gruppe | Aktuelle Beobachtung | Konkreter kleiner Folgeauftrag |
|---|---|---|
| Discovery-/Planfixtures | Kein HTML, kein manifest.json/regression_manifest.json/Adapterplan in master; Tests lesen diese direkt. | Dieser Fixture-PR: 63 byteidentische, SHA-256-geprüfte HTML-Dateien plus drei portable JSON-Dateien; sauberer Checkout muss Discovery/Selection/Adapter/Fake-Executor bestehen. |
| TXT, sechs Fehler | `import_txt()` erzeugt unbekannte Zeiten `None`; TranscriptSegment verlangt float. Betroffen: Unicode/Absätze, cp1252, utf-16, exklusives Speichern, Chunking-Vertrag und Importisolation. | Optional nullable Segmentzeiten aus #9 gezielt übernehmen; zeitbasiertes Chunking lehnt unbekannte Zeiten ausdrücklich ab. SRT/Whisper-Regressionsvertrag erhalten. |
| Provenienz, 14 Fehler | Allgemeiner Extraction-Runner liefert Sprache nicht weiter; `transcript_metadata()` fehlt an drei Dokumentmodellen; neun Sprach-/URL-/Media-Konflikte werden nicht abgewiesen. | Modellvertrag aus #10/#12 auf aktuelle optionale Felder portieren; danach Runner und beide semantischen Ergebniszweige weiterreichen. Keine IDs erfinden. |
| Lazy-Imports, vier Fehler | Der Test importiert echte Module und anschließend llm_helper: dort eager `openai`, `marvin`, `pydantic_ai`; fehlendes openai beendet die Probe. find_knowledge selbst besitzt bereits eine Lazy-Factory. | Nur den fehlenden Lazy-Helper-Anteil aus #10/#13 übernehmen; synchrone Importe ohne SDK/DB erzwingen. SDK-Installation ist kein Ersatz für den deterministischen Importvertrag. |
| SDK-Smoke, ein Fehler | `test_installed_provider_configuration_without_api`: ModuleNotFoundError: openai. | Optionalen SDK-Testbedarf explizit deklarieren und bei fehlendem Extra bewusst skippen oder in separater installierter SDK-Testmatrix prüfen. Kein API-Aufruf. |
| Pilot-Testeingänge, acht Fehler | Nicht versioniertes `cs50_python_week0_knowledge_input.v1.json`; ursprüngliches Manifest enthält absolute Maschinenpfade und verweist auf produktive Belege. | Eigene tmp_path-Fabrik für synthetische SRT/Belege/Manifest; Originalpilot nur explizit als lokaler Integrationstest. Index-/Zeitlimit-Tests auch ohne Originalpilot reproduzierbar machen. |
| uv-Rebuild | Nicht gecachte spaCy-URL-Metadaten verhindern locked/offline Worker-Sync. | Kleinste reproduzierbare Worker-/Testinstallation mit bestehenden Versionen prüfen; optionales NLP vom Offline-Testsetup abgrenzen. Keine ungefragten Upgrades. |

Vier Skips nach Fixture-Ergänzung: Original-SRT im Executor nicht vorhanden,
Originalimport im Knowledge-Eingang nicht vorhanden, lokales Pilot-Manifest
nicht vorhanden und Marvin-basierter installed-Integrationstest nicht anwendbar.
Letzterer verlangt Marvin, obwohl der deterministische Pfad selbst ohne Marvin
funktioniert. Es wurde weder Marvin noch dessen Datenbank initialisiert.

Der source_id-Vertrag ist vorhanden: alle elf source_id-Tests bestehen.
Der echte Import/Formel-Helper-Test besteht ebenfalls. Diese beiden früheren
Produktionslücken dürfen nicht erneut pauschal als offen geführt werden.

## Entscheidungsmatrix der offenen PRs

Alle vier sind laut GitHub offen, Basis `master`. `git merge-tree --write-tree`
wurde ohne Index-/Arbeitsbaum-Merge ausgeführt; sämtliche vier liefern Konflikte.
Ein Head-zu-Head-Diff zeigt auch Dateien, die erst später auf master hinzukamen;
solche `D`-Einträge bedeuten ausdrücklich nicht, dass ein normaler Merge sie
automatisch löschen würde.

Reproduzierbare Merge-Prüfung (nur Git-Objekte, kein Branch-/Index-Merge):

```bash
git merge-tree --write-tree origin/master origin/feat/cs50-discovery-contracts
git merge-tree --write-tree origin/master origin/feat/official-transcript-import
git merge-tree --write-tree origin/master origin/fix/knowledge-source-id
git merge-tree --write-tree origin/master origin/fix/math-normalization-import
```

| PR / geprüfter Head | Schon enthalten | Noch sinnvoll | Merge-Risiko und Empfehlung |
|---|---|---|---|
| #6 / `7ba2dd8` | Discovery-/Manifest-Verträge vorhanden, durch sechs Kurse, Hashprüfung und spätere Parser erweitert. | Die fehlenden Fixtures; aktueller 63-Seiten-/50-Vorlesungsstand wird in diesem PR separat aufgenommen. | Acht add/add-Konflikte in Modellen, Loader, Parser, Selection und Tests. Ältere vier-Kurs-Verträge könnten bei falscher Auflösung neuere IDs/Varianten verlieren. Nach Fixture-PR als ersetzt schließbar; kein Merge des alten Stacks empfohlen. |
| #9 / `3d13173` | TXT/SRT/VTT-Importer vorhanden, inzwischen mit preserve_empty_cues. | Nullable TranscriptSegment-Zeiten und explizite Chunking-Ablehnung zeitloser Quellen fehlen. | Zwei add/add-Konflikte im Importer und dessen Tests; alte Importerversion kennt preserve_empty_cues nicht. Kleiner neuer TXT-Vertrags-PR statt altem Merge, anschließend als ersetzt schließbar. |
| #10 / `9ed643d` | source_id-Feld, Consumerprüfung, Runner-ID und source_id-Tests vorhanden. | Provenienzvalidatoren/Metadatenmethode, Legacy-Runner-/Semantic-Weitergabe und Lazy-llm_helper aus den hineingemergten #12/#13 fehlen. | Drei Konflikte in Knowledge-Modell, Consolidation und find_knowledge. Neuer Provider-/Evidence-Pfad muss erhalten bleiben. Modellvertrag, Weitergabe und Lazy-Helper als kleine neue PRs übernehmen; erst nach deren Tests als ersetzt schließen. |
| #11 / `efed68d` | Korrigierter latex_helper-Import und regulärer Formel-Regressionstest vorhanden; Test besteht. | Kein notwendiger Produktionscode fehlt. | Ein add/add-Testkonflikt; alte Testversion ersetzt socket.socket komplett statt nur Verbindungen zu sperren. Als ersetzt schließbar, keine alte Testversion zurückbringen. |

Die Matrix ist eine Empfehlung; es wurde kein PR geschlossen oder gemergt.

## Resume: beschädigte Consolidation-Ausgaben

`process_course_knowledge()` in `src/run_knowledge_consolidation.py` überspringt
jede existierende Ausgabedatei vor jeglichem Laden oder Validieren. Die echte
Funktionsdefinition wurde für eine Offline-Probe isoliert aus dem AST geladen,
Logger/Processing-Grenze ersetzt, alle Dateien in TemporaryDirectory erstellt.
Bei `''`, `'{broken'` und `'{}'` gab es jeweils **null Processing-Aufrufe**.
Das bestätigt einen Resume-Vertragsfehler; es ist kein LLM-/SDK-Problem.
Der vollständige Runnerimport war wegen des separaten SDK-Importproblems nicht
Teil dieser Probe. Produktive Ausgaben wurden nicht geöffnet oder verändert.

Minimaler nächster PR: existierende Ausgabe regulär als LectureKnowledgeDocument
laden, Quellenidentität abgleichen und nur gültige passende Ergebnisse skippen.
Beschädigte, unvollständige oder fremde Ausgaben explizit melden; nicht still
überschreiben. Tests für gültiges Resume, leere/kaputte JSONs, fehlende Felder,
fremde source_id und Abbruch zwischen Schreiben und Fertigstellen.

Reproduktion der vorhandenen Resume-Logik ohne Runner-/SDK-Import:

```python
import ast, gc, logging, tempfile
from pathlib import Path
from types import SimpleNamespace

path = Path("src/run_knowledge_consolidation.py")
node = next(n for n in ast.parse(path.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "process_course_knowledge")
calls = []
scope = dict(Path=Path, gc=gc,
             app_session=SimpleNamespace(logger=logging.getLogger("offline")),
             process_knowledge_file=lambda **kw: calls.append(kw))
exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), scope)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "lecture_know_extract.json"
    source.write_text("{}")
    for content in ("", "{broken", "{}"):
        (root / "lecture_know_consol.json").write_text(content)
        scope["process_course_knowledge"]([source], root, "offline")
        assert not calls
```

## Prioritäten und Abhängigkeiten

| Rang | Kleiner PR | Abnahme / Abhängigkeit |
|---|---|---|
| P0 | Fixture-Basis (dieser PR) | 63 Hashprüfungen, 50 Bindungen/100 Tasks; Discovery, beide Selection-Modi, Adapter und Fake-Executor im sauberen Checkout. |
| P1-1 | Portable Pilot-Testeingänge | Beseitigt acht Testfehler ohne Aufnahme produktiver Daten; basiert auf Fixture-PR. Legacy und segment_v1 gemeinsam automatisch testen. |
| P1-2 | Provenienzmodell-Vertrag | Drei Dokumenttypen, Legacy-JSON, neun Konfliktfälle; aktuellen source_id-Vertrag erhalten. |
| P1-3 | Legacy-/Semantic-Metadatenweitergabe | Nach P1-2; beide semantischen Ergebniszweige sowie Extraction-Runner mit Fake-Grenzen testen. |
| P1-4 | Lazy-Helper vervollständigen | Unabhängig von P1-2; vier synchrone Importtests ohne SDK/Marvin/SQLite. |
| P1-5 | Consolidation-Resume absichern | AST-/deterministische Unit-Tests sofort möglich; regulärer Runnerimport nach P1-4. Keine automatische Migration. |
| P2-1 | TXT-Zeitvertragskorrektur | Sechs Fehler beseitigen; SRT/Whisper unverändert, keine künstlichen Zeiten. |
| P2-2 | uv-/optionale SDK-Testmatrix | Nach P1-4 kein eager Import als Installationszwang; locked Versionsstand ohne Downloads reproduzierbar machen. |
| P2-3 | Präzisionsqualität fachlich evaluieren | Erst nach reproduzierbarem Pilot-Setup; ID-Gültigkeit ist keine semantische Beweisprüfung. API-Lauf benötigt separate Freigabe. |

## Umfang der Fixture-Korrektur

63 HTML-Snapshots wurden aus dem bestehenden lokalen geprüften Fixturebestand
byteidentisch übernommen. Alle SHA-256-Werte stimmen mit manifest.json überein;
regression_manifest.json referenziert die bisherigen 34 Snapshot-Seiten. Der
Adapterplan bleibt planned_only und bewahrt sechs Kurse/50 Bindungen/100 Tasks.
Keine HTML-Inhalte oder fachlichen Module wurden angepasst.

Master hatte keine versionierte .gitignore. Die neue eng begrenzte Datei schützt
lokale Umgebungen, Credentials und data/ sowie nicht geprüfte CS50-JSONs; sie
erlaubt genau die 63 Snapshotpfade und drei Manifest-/Planpfade. Sie öffnet keine
produktiven Transkripte oder Ausführungsbelege. Absolute Maschinenpfade im Plan
oder HTML wurden ausgeschlossen. Kein produktives Pilot-Manifest, Transcript-
JSON, execution.v1.json oder API-Secret wird veröffentlicht.

Neue Testdateien prüfen portable Fixturepfade, Hashes, sechs Kurse/50 Bindungen
und die engen Ignore-Ausnahmen. Der separate synthetische Testhelper macht die
gemeinsame Pilot-/Präzisionsprobe reproduzierbar, ersetzt aber nicht den noch
notwendigen regulären tmp_path-Fixture-Umbau.

Alle Arbeit blieb in Personal_Assistant. Keine Kursmaterialien nachgeladen,
keine API-/LLM-/Whisper-Aufrufe, keine Änderungen an produktiven Daten oder
Funktionsmodulen, keine Dependency-Upgrades und keine automatischen Merges.

## Ergebnisse nach Testmodul

P = bestanden, F = Testfehler, E = Setup-Fehler, S = übersprungen.

| Testmodul | Master unverändert: P / F / E / S | Mit Fixtures: P / F / E / S |
|---|---|---|
| test_consolidation_math_import | 1 / 0 / 0 / 0 | 1 / 0 / 0 / 0 |
| test_cs50_discovery | 10 / 20 / 0 / 0 | 30 / 0 / 0 / 0 |
| test_cs50_executor | 0 / 0 / 33 / 0 | 32 / 0 / 0 / 1 |
| test_cs50_extraction | 20 / 4 / 20 / 0 | 44 / 0 / 0 / 0 |
| test_cs50_full_coverage | 0 / 1 / 9 / 0 | 10 / 0 / 0 / 0 |
| test_cs50_knowledge_input | 0 / 0 / 28 / 0 | 27 / 0 / 0 / 1 |
| test_cs50_knowledge_pilot | 16 / 2 / 0 / 1 | 16 / 2 / 0 / 1 |
| test_cs50_lecture_adapter | 1 / 0 / 29 / 0 | 30 / 0 / 0 / 0 |
| test_cs50_llm_smoke | 8 / 1 / 0 / 0 | 8 / 1 / 0 / 0 |
| test_cs50_precise_evidence | 16 / 2 / 0 / 0 | 16 / 2 / 0 / 0 |
| test_cs50_quality | 5 / 4 / 0 / 0 | 5 / 4 / 0 / 0 |
| test_cs50_selection | 2 / 0 / 22 / 0 | 24 / 0 / 0 / 0 |
| test_cs50_six_courses | 0 / 0 / 9 / 0 | 9 / 0 / 0 / 0 |
| test_cs50_srt_knowledge_integration | 0 / 0 / 5 / 0 | 5 / 0 / 0 / 0 |
| test_cs50_timed_selection | 0 / 0 / 19 / 0 | 19 / 0 / 0 / 0 |
| test_cs50_uv_installed_integration | 0 / 0 / 0 / 1 | 0 / 0 / 0 / 1 |
| test_knowledge_source_id | 11 / 0 / 0 / 0 | 11 / 0 / 0 / 0 |
| test_knowledge_transcript_provenance | 5 / 14 / 0 / 0 | 5 / 14 / 0 / 0 |
| test_lazy_marvin_import | 0 / 4 / 0 / 0 | 0 / 4 / 0 / 0 |
| test_official_transcript_import | 33 / 6 / 0 / 0 | 33 / 6 / 0 / 0 |
