# GitHub-Integrationsstatus und nächste kleine PRs

Stand: **14.10.2026**, Repository `rf-data/Personal_Assistant`. Roadmap gelesen:
`docs/ROADMAP.md`, Dokumentstand 12.10.2026. Keine Untersuchung oder Änderung des
separaten UI-Repositories. Dieser Bericht aktualisiert den Backend-Arbeitsstand,
nicht die noch unbestätigten Abschlussmarkierungen der Roadmap.

## Ergebnis: noch keine reproduzierbare integrierte Entwicklungsbasis

`master` enthält bereits fast den vollständigen Implementierungscode aus #14–#18
über zwei separate Sammelcommits. Diese PRs sind dennoch alle offen. Die lokale
Arbeitskopie besteht wichtige SRT-/Discovery-Tests, wird aber durch ignorierte,
nicht versionierte HTML-/JSON-Dateien ergänzt. Ein sauberer Checkout scheitert.
Umgekehrt enthält der veröffentlichte Feature-Stack die Fixtures, aber nicht den
von Executor/Knowledge benötigten offiziellen Importer. Zusätzlich fehlen Teile
der früheren Provenienz-/Lazy-Import-Verträge. Die früheren gezielten grünen
Testberichte sind daher **kein Nachweis einer vollständig integrierten Basis**.

Empfehlung für Folgearbeiten: **`master` auf `bd5491e63966f5bb3d53593f06604dcadf5bfc98`
als Code-Ausgangspunkt verwenden**, zunächst mit einem kleinen Fixture-/Basis-PR
reproduzierbar machen. Nicht ungeprüft auf #18 wechseln und nicht die bestehenden
Stacks blind nach master mergen. Heute wurden lediglich Remote-Refs aktualisiert,
zwei detached Prüf-Worktrees angelegt und dieser Bericht geschrieben.

## 1. GitHub-Snapshot und Abhängigkeitsreihenfolge

Alle **13 PRs #6–#18 sind offen und ungemergt**. GitHub-Metadaten wurden neu gelesen;
Remote-Branches anschließend mit `git fetch origin` abgeglichen. Die PR-Kette lautet:

```text
master ─ #6 ─ #7 ─ #8 ─ feat/cs50-full-coverage (kein eigener PR)
                       └─ #14 ─ #15 ─ #16 ─ #17 ─ #18
master ─ #9 offizieller Import (separat)
master ─ #10 source_id ─ #12 Provenienz ─ #13 Lazy-Initialisierung
master ─ #11 Formel-Import (separat)
```

Der Full-Coverage-Commit baut tatsächlich auf #8 auf; die Darstellung markiert ihn
als Fortsetzung dieser Linie. Die offiziellen Import-/Knowledge-Vertrags-PRs sind
keine Git-Vorfahren der CS50-Linie, obwohl spätere CS50-Funktionen sie benötigen.

| PR | Tatsächliche Basebranch | Head SHA, kurz | GitHub mergeable zur eigenen Base |
| --- | --- | --- | --- |
| [#6](https://github.com/rf-data/Personal_Assistant/pull/6) | master | bb91b33 | nein |
| [#7](https://github.com/rf-data/Personal_Assistant/pull/7) | feat/cs50-discovery-contracts | 2a4261f | ja |
| [#8](https://github.com/rf-data/Personal_Assistant/pull/8) | feat/cs50-offline-extraction | cea19d3 | ja |
| [#9](https://github.com/rf-data/Personal_Assistant/pull/9) | master | 3d13173 | nein |
| [#10](https://github.com/rf-data/Personal_Assistant/pull/10) | master | 116753f | nein |
| [#11](https://github.com/rf-data/Personal_Assistant/pull/11) | master | efed68d | nein |
| [#12](https://github.com/rf-data/Personal_Assistant/pull/12) | fix/knowledge-source-id | 6d3d89f | ja |
| [#13](https://github.com/rf-data/Personal_Assistant/pull/13) | feat/knowledge-transcript-provenance | 65303d3 | ja |
| [#14](https://github.com/rf-data/Personal_Assistant/pull/14) | feat/cs50-full-coverage | d6e6544 | ja |
| [#15](https://github.com/rf-data/Personal_Assistant/pull/15) | feat/cs50-timed-knowledge | be7ab29 | ja |
| [#16](https://github.com/rf-data/Personal_Assistant/pull/16) | feat/cs50-lecture-adapter | d22b023 | ja |
| [#17](https://github.com/rf-data/Personal_Assistant/pull/17) | feat/cs50-srt-executor | 547dc37 | ja |
| [#18](https://github.com/rf-data/Personal_Assistant/pull/18) | feat/cs50-knowledge-input-binding | c74c8b7 | ja |

Full-Coverage-Basis: `f704387c9a2e0ed82ace69a7d868f959027c5f70`.
Master und origin/master stimmen nach Fetch auf `bd5491e` überein. Gemeinsamer
Vorfahre mit #18: `d72a96af4261f91e4358500c8a03c9b427a0c956`.
`git rev-list --left-right --count master...origin/feat/cs50-bounded-llm-pilot`
ergibt **2 / 9**. Kein Head #14–#18 ist als Commit-Vorfahr in master enthalten.

## 2. Was bereits in master steckt — Inhalte versus Commit-Historie

Master-Sammelcommits: `b2e4b2f` und `bd5491e`. Verglichen wurden die jeweils durch
`head^..head` betroffenen Dateien eines PRs anhand ihrer Git-Blob-IDs:

| PR | Bereits identischer Inhalt in master | Noch fehlend / unterschiedlich |
| --- | --- | --- |
| #14 | alle 6 Dateien, einschließlich timed_knowledge-Selection | nichts |
| #15 | 4 von 5 Dateien: Adapter, Tests, Skript, Bericht | `cs50_lecture_plan.v1.json` nicht versioniert |
| #16 | alle 4 Dateien: Executor, Enum-Ergänzungen, Tests, Bericht | nichts im eigenen Diff |
| #17 | 6 von 8 Dateien, darunter Bindung, Ergebnisfelder und Lazy-Factory | Pilot-Eingabemanifest fehlt; Consolidation unterscheidet sich nur in Formatierung des Fehlers |
| #18 | alle 5 Dateien, einschließlich Provider, CLI, Smoke-Import-Alias | nichts |

`git cherry master origin/feat/cs50-bounded-llm-pilot` meldet trotzdem neun `+`-
Commits, keine vollständig patchäquivalenten Einzelcommits: die Sammelcommits sind
nicht dieselben Patches. **Viele identische Dateien bedeuten inhaltliche Dopplung,
aber keine identische Commit-Historie.** Deshalb würde bloßes Cherry-Picking oder
Mergen erneut bereits enthaltene Änderungen anfassen.

### Zwei unterschiedliche Vollständigkeitslücken

* Master versioniert **keine der 63 CS50-HTML-Fixtures** und keine CS50-JSON-Manifeste/
  Pläne. `.gitignore:21` (`*.html`) und `:26` (`*.json`) erklären die lokale Maskierung.
  Die lokalen 63 HTML-Dateien sind byteidentisch zu den versionierten Dateien von #18.
  Source-Parser/Selection sind vorhanden; Testdaten fehlen im Git-Tree.
* #18 versioniert Fixtures/Manifeste/Plan, enthält aber
  **kein `src/tools_transcribe/import_transcript.py`**. Dieser Importer liegt in
  master bzw. #9. Der Stack #16–#18 ist deshalb allein nicht ausführbar.
* Das eingecheckte Pilot-Eingabemanifest aus #17 enthält absolute lokale Artefaktpfade.
  Es ist ein dokumentierter lokaler Stand, kein universeller Clean-Checkout-Testinput.
  Produktive SRT-/Beleg-/Transcript-Dateien wurden nicht in Prüf-Worktrees kopiert.

Reproduzierbare Beobachtung:

```bash
git cat-file -e master:docs/course_sources/cs50/manifest.json                    # fehlt
git cat-file -e origin/feat/cs50-bounded-llm-pilot:src/tools_transcribe/import_transcript.py # fehlt
git check-ignore -v docs/course_sources/cs50/manifest.json
git diff --name-only origin/feat/cs50-timed-knowledge^ origin/feat/cs50-timed-knowledge
```

Folgeaufträge: I01 für die versionierte Basis, I08 für portable Testeingänge und I09
für PR-Historie/Retargeting; siehe priorisierte Tabelle unten.

## 3. Merge-Konflikte tatsächlich geprüft

`git merge-tree --write-tree master origin/<branch>` simuliert den Merge, ohne
Checkout, Index oder Arbeitsdateien zu mergen. Ergebnis:

| Branch / PR | Simulation gegen aktuellen master |
| --- | --- |
| feat/cs50-full-coverage | add/add in report_cs50_sources.py, cs50_selection.py, select_cs50.py |
| #14, #15, #16 | konfliktfrei, aber viele Inhalte bereits enthalten |
| #17 und #18 | Inhalt-Konflikt in consolidate_knowledge.py |
| #9 | add/add in import_transcript.py und test_official_transcript_import.py |
| #10 | Konflikte in data_knowledge.py und consolidate_knowledge.py |
| #11 | add/add in test_consolidation_math_import.py |
| #12 | Konflikte in data_knowledge.py und consolidate_knowledge.py |
| #13 | zusätzlich Konflikt in find_knowledge.py |

#17/#18 sind also nur gegen ihre **eigenen Bases** konfliktfrei. Das widerspricht
nicht der GitHub-Anzeige. Bei Consolidation ist die Differenz #18→master derzeit
lediglich die Zeilenformatierung des source_id-Fehlers; ein Merge-Conflict ist hier
kein Nachweis eines fachlichen Unterschieds. Die anderen Konflikte enthalten echte
unterschiedliche Implementierungsstände. Kein Konflikt wurde heute aufgelöst.

## 4. Reproduzierbare uv-Testumgebung und tatsächlich ausgeführte Tests

Interpreter `.venv/bin/python3`, Python 3.12.12; Pydantic 2.13.4, HTTPX 0.28.1,
pytest 9.1.1, BeautifulSoup 4.15.0, pydantic-settings 2.15.0.
`uv sync --offline --frozen --extra lecture-worker --dry-run` bestätigt **139 Pakete,
keine Änderungen nötig**. Keine Installation, kein Upgrade und kein Lockfile-Umbau.
OpenAI/Marvin/Pydantic-AI-SDKs sind nicht installiert. Provider-Aufrufe bleiben Fake
oder offline; kein `--execute-llm` mit echtem Transport.

| Testbasis | Umfang | Ergebnis |
| --- | --- | --- |
| Lokaler unveränderter master, mit seinen vorhandenen ignorierten Fixtures/Pilot | alle `tests/test*.py`, 335 Fälle | **309 bestanden, 25 fehlgeschlagen, 1 übersprungen**, 228,98 s |
| Clean master bd5491e, ohne lokale Ergänzungen | Discovery, 30 Fälle | **10 bestanden, 20 fehlgeschlagen**, 3,13 s; Manifest/Fixtures fehlen |
| Clean #18 c74c8b7, ohne fremde Ergänzungen | alle dort vorhandenen Tests, 246 Fälle | **181 bestanden, 4 fehlgeschlagen, 61 Setup-Fehler**, 169,57 s |

Der Clean-#18-Lauf: Executor **33** und Knowledge-Eingang **28** Setup-Fehler durch
fehlenden Importer. Drei Pilot-Tests scheitern an derselben Voraussetzung. Ein
Selection-Isolationstest scheitert nach den fehlerhaften Fixtures an übriggebliebenen
Settings-Modulen; sein gesonderter frischer Lauf dient der Ursachenabgrenzung.
Der gesonderte Selection-Isolationstest besteht **1/1** im frischen Prozess.
Der Fehler im Gesamtlauf ist damit als Fixture-/Modulzustandsfolge abgegrenzt,
nicht als belegte Selection-Algorithmusregression. Es wurden keine Feature-Dateien
in master kopiert und keine Testfehler verdeckt.

### Lokaler master: Detailgruppen

| Tests | Bestanden | Fehlgeschlagen / Skip |
| --- | ---: | ---: |
| Discovery + Extraction + Default-/Timed-Selection + sechs Kurse/volle Coverage | 136 | 0 |
| Lecture-Adapter / Executor / Knowledge-Eingang / begrenzter Pilot | 30 / 33 / 28 / 19 | 0 |
| SRT-Knowledge-Pilot / source_id / echter Formel-Import | 5 / 11 / 1 | 0 |
| Offizieller TXT/SRT/VTT-Import | 33 | 6 |
| Provenienz-Verträge einschließlich Runner und semantischer Ergebnisse | 5 | 14 |
| Lazy-Import-Verträge | 0 | 4 |
| Älterer Smoke-Testumfang | 8 | 1 |
| Installed-uv-SRT-Integration | 0 | 1 Skip: prüft `find_spec('marvin')`, obwohl Reason nur lecture-worker nennt |

### Dependency-Fehler von Code-/Modellfehlern getrennt

1. **Ein SDK-Smoke-Fehler:** `test_installed_provider_configuration_without_api`
   scheitert mit `ModuleNotFoundError: openai`. Optionales SDK fehlt; kein Beleg für
   einen Fehler der HTTPX-Alternative oder SQLite. Folgeauftrag I07.
2. **Vier Lazy-Testfehler:** Alle erreichen den weiterhin eager importierenden
   `src.utils.llm_helper`, dessen `from openai import OpenAI` bereits beim Import
   fehlschlägt. Die beiden Tests für find_knowledge/Consolidation importieren diesen
   Helper zusätzlich nach dem Zielmodul. Separate echte synchrone Imports zeigen:
   `find_knowledge` PASS, `consolidate_knowledge` PASS, `llm_helper` fehlt openai;
   Marvin bleibt ungeladen. **Nicht pauschal als vier kaputte Chunker werten.**
   Eager SDK-Abhängigkeit des Helpers und Extraction-Runners ist trotzdem ein
   Architektur-/Integrationsfehler, der nicht nur durch Installation verdeckt werden
   sollte. #13 enthält den weitergehenden Lazy-Helper-Stand. Folgeauftrag I05.
3. **14 Provenienzfehler:** Die allgemeine Extraction liefert `language=None`,
   obwohl das Transcript Englisch angibt. `.transcript_metadata` fehlt in den
   bestehenden Ergebnisverträgen; `LectureKnowledgeDocument`/semantische Pfade
   besitzen nicht den in #12 beschriebenen vollständigen Metadatenvertrag. Neun
   Sprach-/URL-/media_id-Widerspruchsfälle werden nicht abgewiesen. Dies sind
   echte fehlende Modell-/Weitergabeverträge, keine SDK-Dependency-Probleme.
   Der explizite CS50-Pfad besteht seine Tests, ersetzt aber nicht die Legacy-
   Extraction-/Semantic-Verträge. Folgeaufträge I03 und I04.
4. **Sechs TXT-Fehler:** Import erzeugt `start=None/end=None`, das aktuelle
   `TranscriptSegment` verlangt `float`. #9 enthält die fehlende Optionalität,
   aber seine ältere Importer-Version darf die neuere `preserve_empty_cues`-
   Unterstützung nicht verdrängen. Kein SRT-Blocker. Folgeauftrag I06.

Die sechs reproduzierten TXT-Fälle:

```text
test_txt_unknown_timestamps_paragraphs_and_unicode
test_explicit_encoding[cp1252]
test_explicit_encoding[utf-16]
test_exclusive_save_and_no_overwrite
test_knowledge_chunking_contract_without_llm_imports
test_import_does_not_load_whisper_or_application_settings
```

### Befehle und Nachweise

Artefakte außerhalb produktiver Daten:
`/tmp/cs50-integration-audit-20261014/{master,feature,master-clean}.log` und `.xml`.
JUnit-Dateien enthalten die tatsächlichen Case-Namen und Fehlertexte; keine API-Keys
wurden ausgegeben. Die zwei Worktrees liegen im selben temporären Audit-Verzeichnis.

```bash
# Lokaler master, keine uv-Synchronisation während Tests
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test*.py -q --junitxml=/tmp/cs50-integration-audit-20261014/master.xml
# Getestete detached Worktrees desselben Repositories
git worktree add --detach /tmp/cs50-integration-audit-20261014/master-clean master
git worktree add --detach /tmp/cs50-integration-audit-20261014/feature origin/feat/cs50-bounded-llm-pilot
# In jeweiligem Worktree dieselbe tatsächlich installierte Umgebung verwenden
UV_CACHE_DIR=/tmp/cs50-uv-cache UV_PROJECT_ENVIRONMENT=/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv uv run --offline --no-sync python -m pytest tests/test*.py -q
```

Die vorhandenen temporären Worktrees nicht erneut mit gleichem Zielnamen anlegen.
Für Clean-master wurde absichtlich nur `tests/test_cs50_discovery.py` ausgeführt;
dieser schnelle Nachweis reicht für die fehlende Fixture-Voraussetzung.

## 5. Consolidation-Resume: beschädigte Ausgaben werden als fertig behandelt

`src/run_knowledge_consolidation.py:process_course_knowledge` prüft nur
`output_path.exists()` und überspringt dann vor jeglicher JSON-/Modell-/Identitäts-
prüfung. Die Ausgabe von `process_knowledge_file` ist `LectureKnowledgeDocument`.

Eine temporäre Offline-Probe hat die **echte unveränderte Funktionsdefinition** per
AST kompiliert, einen Logger und einen Processing-Spy injiziert und ausschließlich
synthetische Dateien verwendet. Kein normaler Runner-Import und kein semantischer
LLM-Aufruf: diese Abhängigkeiten wurden bewusst nicht gestartet.

| Vorhandene Ausgabe | Processing-Aufrufe | Tatsächliches Resume |
| --- | ---: | --- |
| leer, 0 Bytes | 0 | fälschlich übersprungen |
| beschädigtes JSON `{` | 0 | fälschlich übersprungen |
| syntaktisches JSON `{}`, falsches Modell | 0 | fälschlich übersprungen |
| gültiges LectureKnowledgeDocument, source_id=`other` | 0 | falsche Quellenzuordnung trotzdem übersprungen |
| gültiges Modell mit erwarteter ID | 0 | übersprungen, aber auch hier ungeprüft |
| Verzeichnis mit Ergebnisdateinamen | 0 | ebenfalls übersprungen |
| Ausgabe fehlt | 1 | Processing-Spy aufgerufen |

Reproduktion:
`uv run --offline --no-sync python /tmp/cs50-integration-audit-20261014/resume_probe.py`.
Der dort erhaltene kleine Probe-Code lädt die Funktion aus dem aktuellen Source;
`resume.json` enthält sämtliche Beobachtungen. Die Ursache ist zusätzlich direkt
an `if output_path.exists(): ... continue` nachvollziehbar. Der Code wurde heute
nicht korrigiert. Folgeauftrag I02 ist der konkretisierte Roadmap-Auftrag **C07**.

## 6. Kleine Folgeaufträge nach Dringlichkeit und Abhängigkeiten

| Reihenfolge | Priorität / Auftrag | Konkreter kleiner PR und Abnahme | Voraussetzung |
| --- | --- | --- | --- |
| 1 | **P0 I01 — reproduzierbare Basis** | Auf master gezielt 63 bereits geprüfte HTML-Fixtures und notwendige Manifest-/Plan-JSONs versionieren; scoped Ignore-Ausnahmen bzw. explizite Aufnahme. Importer bereits in master behalten. Clean-Checkout-Discovery/Adapter/Fake-Executor müssen bestehen; keine produktiven Daten aufnehmen. | geprüfter master bd5491e; Fixtures byteidentisch zur Full-Coverage-Basis |
| 2 | **P0 I02 — sicheres Resume / C07** | Separate Unit-Tests für die sieben beobachteten Fälle. Skip nur nach echter Datei-, JSON-, LectureKnowledgeDocument- und Quellenidentitätsprüfung; unbestätigte/beschädigte Ausgaben klar melden, nicht überschreiben/löschen und keine LLM-Kosten auslösen. | keine SDKs nötig; Modellvalidierung und Processing-Spy |
| 3 | **P1 I03 — ein Provenienzvertrag** | Kleinen #12-Modellanteil mit aktuellen optionalen Feldern konsolidieren: Legacy-JSON lesbar, semantisches Ergebnismodell berücksichtigt, widersprüchliche Sprache/URL/media_id abgewiesen. Neun Konfliktfälle plus Legacy-Tests bestehen. | I01; #12 als Referenz, kein blindes Überschreiben von #17 |
| 4 | **P1 I04 — Legacy-/Semantic-Weitergabe** | Geprüfte Transcript-Metadaten im vorhandenen Extraction-Runner und beiden semantischen Ergebniszweigen weiterreichen; echte Funktionstests mit synthetischen Grenzen. Keine neuen IDs aus Namen/URLs. Die verbliebenen Provenienz-Tests bestehen. | I03 |
| 5 | **P1 I05 — Lazy-Helper vervollständigen** | Nur Marvin/OpenAI/Pydantic-AI-Importgrenzen aus #13 in den aktuellen llm_helper übernehmen; aktuelle Factory/CS50-API erhalten. Frische synchrone Runner-/Helper-Imports funktionieren ohne SDK, Netzwerk oder DB. | I01; vier echte Importtests, keine SDK-Installation als Ersatz |
| 6 | **P1 I06 — TXT-Vertragslücke** | Null-Zeitstempel im vorhandenen Segmentmodell rückwärtskompatibel zulassen und zeitbasierten Chunker bei unbekannten Zeiten ausdrücklich abbrechen lassen. Alle sechs TXT-Fälle bestehen, numerische SRT/Whisper-Verträge und preserve_empty_cues bleiben erhalten. Noch kein zeitloser Chunker. | I01; enger separater Modell-/Guard-PR |
| 7 | **P2 I07 — SDK-Testprofile** | Reproduzierbares lecture-worker-Offline-Profil von optionalem SDK-Konfigurationsprofil trennen. Skip-Gründe korrekt benennen; SDK-Konfiguration separat mit deklarierten llm-Abhängigkeiten, Mock-Transport und Importdeadline prüfen. Keine pauschalen Upgrades oder bezahlten Calls. | I05; Abhängigkeiten vor Installation explizit prüfen |
| 8 | **P1 I08 — portable Pilot-/Testeingänge** | Synthetische Belege/Manifeste pro tmp_path erzeugen statt maschinenspezifischer absoluter Dokumentationspfade; Originalpilot separat explizit lokal prüfen. Fixture-Teardown auch bei Setup-Fehler vollständig ausführen. Clean-Stack ohne produktive Artefakte testbar. | I01; Selection-Isolation gesondert prüfen |
| 9 | **P2 I09 — PR-Historie bereinigen** | Für #6–#18 eine konkrete reviewed Integrations-/Retarget-/Superseded-Liste anhand der identischen Blobs und tatsächlichen Restdiffs erstellen. Full-Coverage-Basis explizit einbeziehen; Formatter-Konflikt bewusst auflösen. Erst nach Tests manuell über Merge/Schließen entscheiden. | I01, I03–I06; heute keine PRs verändert |
| 10 | **P2 I10 — Roadmap / C08–C09** | Backend-Roadmap anhand dieser Testergebnisse aktualisieren; doppelte lecture-worker-Einträge separat ohne Versions-Upgrades entfernen; Doku nur mit nachgewiesenen Fähigkeiten markieren. | vorangehende Verträge/Testprofile, jeweils eigener kleiner PR |

I08 kann nach I01 parallel zu den Vertragsthemen bearbeitet werden; Tabellenreihenfolge
ist Dringlichkeit/Review-Reihenfolge, kein zwingend linearer Gesamtplan. Produktive
LLM-Ausführung, SDK-/SQLite-Inbetriebnahme und Vollkursverarbeitung bleiben außerhalb
dieser Bestandsaufnahme und benötigen separat kontrollierte Freigabe.

## Änderungen dieses Auftrags

Nur dieser neue Bericht. Kein neuer Funktionscode, keine Dependency-Änderung,
kein Merge/Cherry-Pick/Rebase, keine produktive Datenänderung, keine SDK- oder
LLM-Initialisierung mit echten Agenten und keine kostenpflichtigen API-Calls.
GitHub-Lesezugriffe und Git-Fetch dienten ausschließlich der angeforderten
PR-/Branch-Prüfung; keine externen Transcript-/Medien-Downloads.

### Selbstständig reproduzierbare Resume-Minimalprobe

Aus dem Repository mit dem regulären uv-Interpreter (nur temporäre synthetische
Dateien, keine allgemeinen Runner-/SDK-Imports):

```python
import ast, gc, logging, tempfile
from pathlib import Path
from types import SimpleNamespace

source = Path("src/run_knowledge_consolidation.py")
function = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef)
                and n.name == "process_course_knowledge")
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    input_path = root / "lecture_know_extract.json"
    input_path.write_text("{}")
    output = root / "lecture_know_consol.json"
    for payload in ("", "{", "{}"):
        output.write_text(payload)
        calls = []
        scope = dict(Path=Path, gc=gc,
                     app_session=SimpleNamespace(logger=logging.getLogger("probe")),
                     process_knowledge_file=lambda **kwargs: calls.append(kwargs))
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     str(source), "exec"), scope)
        scope["process_course_knowledge"]([input_path], root, "offline")
        print(repr(payload), len(calls))  # jeweils 0: beschädigte Ausgabe übersprungen
```

Der vollständig ausgeführte siebenfache Probe-Code steht zusätzlich im angegebenen
Audit-Verzeichnis; dieses Minimalbeispiel ermöglicht die erneute Kernaussage auch
nach Entfernung der temporären Dateien.
