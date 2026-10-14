# Optionale SDKs an den Knowledge-Aufrufgrenzen

Stand: 14. Oktober 2026. Eigenständige Basis: origin/master `f0056be`.
Prüfung im separaten Worktree und in der regulären installierten uv-Worker-
Umgebung (Python 3.12.12, pytest 9.1.1). Kein Sync und keine Installation.
`find_spec()` bestätigt: openai, marvin und pydantic_ai sind nicht installiert.

## Ursache und minimale Korrektur

Alle vier bestehenden Lazy-Import-Tests schlagen auf einem unveränderten
Master-Checkout fehl: **4 failed in 10,02 s**, jeweils fehlendes openai.
`src.run_knowledge_extraction` importiert configure_marvin aus llm_helper;
die Importprobe lädt llm_helper außerdem ausdrücklich nach den deterministischen
Knowledge-Modulen. Dort importierte der Modulrumpf OpenAI, Marvin und Agent
bereits vor jedem Funktionsaufruf.

Nur `src/utils/llm_helper.py` wird produktiv geändert:

- OpenAI wird innerhalb von get_openai_client() importiert.
- Marvin und Agent werden innerhalb von configure_marvin() importiert.
- Die OpenAI-Rückgabeannotation bleibt als String mit TYPE_CHECKING-Import
  für statische Typprüfung erhalten; sie benötigt beim Modulimport kein SDK.
- Die betroffenen Importblöcke werden sortiert. Keine weiteren Funktionen,
  Prompts, Algorithmen, Datenmodelle, Konfigurationen oder Dependencies ändern sich.

Es gibt kein globales Dummy-SDK, kein verschlucktes ImportError und keinen
Fallback: Ein tatsächlicher SDK-abhängiger Aufruf benötigt weiterhin das
entsprechende installierte SDK. Die vorhandene gecachte Marvin-Factory in
find_knowledge bleibt unverändert. SQLite-/Event-Loop-Workarounds entfallen.

## Stärkere Regressionen

Die vier Tests verwenden weiterhin jeweils einen frischen synchronen
Python-Subprozess mit 30 Sekunden Timeout, temporären Settings und gesperrten
Sockets. Ein Importhook macht jetzt ausdrücklich alle drei SDKs unerreichbar,
auch falls sie in einer anderen Testumgebung installiert sein sollten.

Regulär importiert werden die vier Ziele find_knowledge, consolidate_knowledge,
run_knowledge_extraction und llm_helper sowie der Transcript-Importer, die
CS50-Evidence-Bindung und der Provider-Modulrumpf. Echter Chunker, Provenienz-
Bindung und deterministische Formelkonsolidierung bleiben ohne SDK ausführbar.

Anschließend wird geprüft, dass erst get_openai_client(), configure_marvin()
und extract_knowledge() an der gesperrten SDK-Importgrenze fehlschlagen. Erst
nach dieser Phase kommen explizite SDK-Test-Doubles zum Einsatz: OpenAI-
Clientkonstruktion, Marvin-Modellkonfiguration, Agent-Instrumentierung und die
einmalige Factory-Dekoration werden ohne SDK-/API-/DB-Aufrufe geprüft.

Der alte Marvin-Test-Dummy akzeptierte ausschließlich Keyword-Argumente;
die unveränderte Produktions-Factory übergibt Positionsargumente. Nach Behebung
der SDK-Importblockade wurde dieser zuvor verdeckte Testfehler sichtbar. Der
Dummy bindet Argumente jetzt mit inspect.signature(schema).bind() an die echte
Signatur. Der Produktionsaufruf wurde dafür ausdrücklich nicht geändert.

## Ausgeführte Tests

```bash
# UV_PROJECT_ENVIRONMENT auf die bestehende lokale Worker-.venv setzen.
uv run --offline --no-sync python -m pytest \
  tests/test_lazy_marvin_import.py tests/test_consolidation_math_import.py \
  tests/test_knowledge_source_id.py tests/test_cs50_knowledge_input.py \
  tests/test_cs50_knowledge_pilot.py tests/test_cs50_precise_evidence.py \
  tests/test_cs50_quality.py -q
```

Ergebnis: **89 passed, 2 skipped in 107,62 s**, 91 Fälle. Die zwei Skips betreffen
optionale lokale Originalpilot-Artefakte. Alle vier Lazy-Import-Fälle bestehen. Nach abschließender Sortierung der
Importblöcke erneut separat geprüft: **4 passed in 5,21 s**.
Legacy-Chunk- und segment_v1-Verträge, echte Modulimporte/Formeln, source_id,
CS50-Knowledge-Binding und Quality-Regressionen bestehen ebenfalls.

Ruff-Lint für beide Python-Dateien, Formatprüfung der Testdatei und
git diff --check bestehen. Das umfangreiche bestehende Helper-Modul wird nicht
außerhalb seiner Importblöcke neu formatiert.

Die komplette Gesamtsuite wurde in diesem eng begrenzten PR nicht erneut
ausgeführt. Die 14 Provenienz-, sechs TXT- und ein optionaler SDK-Smoke-Fehler
werden nicht repariert oder umklassifiziert. Insbesondere ist dies keine Zusage,
dass beliebige explizit LLM-abhängige Module SDK-frei importierbar werden.

Keine SDK-Installation, echten Client-/Agent-Aufrufe, Datenbankinitialisierung,
API-/LLM-/Whisper-Aufrufe, Downloads oder produktiven Datenänderungen.
