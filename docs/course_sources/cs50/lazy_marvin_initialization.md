# Verzögerte Marvin-Initialisierung

## Ursache

`find_knowledge.py` importierte Marvin auf Modulebene und dekorierte extract_knowledge
sofort mit marvin.fn. Der installierte Marvin-Code (3.2.7) ruft in marvin/__init__.py
unbedingt `ensure_db_tables_exist()` auf. Dessen synchroner Pfad verwendet
`asyncio.run(create_db_and_tables(dispose_engine=True))`; die vorherige Probe blieb
im aiosqlite-Worker/Asyncio-Warten hängen. Das war keine Chunking-/SRT-Arithmetik.

Ein zweiter Importpfad bestand über run_knowledge_extraction → utils.llm_helper →
Marvin. llm_helper importierte außerdem OpenAI und pydantic_ai.Agent bereits beim
Laden, obwohl sie nur für explizite LLM-Konfiguration bzw. Client-Erstellung nötig sind.
Deterministische Consolidation importiert Marvin selbst nicht; ihre normale App-
Importkette funktioniert in der installierten Umgebung mit gültigen Settings.

## Kleine Änderung

Nur zwei Produktionsmodule ändern sich:

- find_knowledge: kein Marvin-Import auf Modulebene. Die identische Schemafunktion
  (Name, Parameter, ChunkKnowledgeResult-Rückgabe und unveränderte Instruktionen) wird
  erst beim Aufruf von extract_knowledge mit marvin.fn verbunden. Ein lru_cache
  erhält die dekorierte Funktion für weitere Aufrufe. Der öffentlich verwendete
  Funktionsaufruf behält seine Parameter und Rückgabe; Cache-/Retry-/Evidence-Code
  bleibt unverändert. Ein bisher unbenutzter LectureContext-Import entfällt.
- llm_helper: Marvin und pydantic_ai.Agent werden erst in configure_marvin importiert;
  OpenAI erst in get_openai_client. Die Rückgabeannotation bleibt per TYPE_CHECKING
  und Vorwärtsreferenz typisiert. Modellwahl, API-Key-Übergabe und instrument_all
  bleiben am selben expliziten Konfigurationspfad.

run_knowledge_extraction kann damit regulär synchron importiert werden, ohne Marvin
zu laden. Runner-Ablauf, Prompts, Modelle, Chunking und fachliche Algorithmen bleiben
unverändert. Kein SQLite-/Event-Loop-Schalter, keine Dummy-Datenbank im Produktionscode.
Der SDK-Typ OpenAI ist kein Laufzeit-Export des Helper-Moduls mehr; vorhandene
Repository-Aufrufer verwenden die Client-Funktion, nicht diesen importierten Typ.

## Echte synchrone Importtests

`tests/test_lazy_marvin_import.py` startet vier frische Subprozesse mit jeweils
30 Sekunden Zeitlimit für find_knowledge, consolidate_knowledge,
run_knowledge_extraction und llm_helper. Tests laufen über den tatsächlich installierten
uv-Interpreter mit `uv run --offline --no-sync python -m pytest ...`.

Kein AST und keine Ersatzmodule während der Import-/Determinismusprüfung. Ein
Meta-Path-Wächter lehnt sogar den Versuch ab, Marvin zu importieren. Socket/DNS
sind gesperrt, Arbeitspfad/Settings temporär und API-Keys bekannte Offline-Platzhalter.
Kein asyncio-Loop und keine Marvin-/SQLite-Umgebungs-Workarounds. Wo der offizielle
Importer vorhanden ist, wird auch sein echter Import geprüft. Modelle und
Formel-Helper sind echter Code. Chunking, Evidence-Binding und Formelkonsolidierung
werden synchron ausgeführt; source_id, Sprache, Segment-ID und Zeitbeleg werden
verglichen. Marvin bleibt ungeladen; keine Datenbankdatei entsteht im Testordner.

Erst danach testen explizite Test-Doubles die LLM-Grenze: unveränderte Instruktionen,
Schema-Name/Signatur/Rückgabetyp, Modelldefault, Instrumentierungsaufruf und Keyword-
Übergabe; Dekorierung genau einmal bei zwei Aufrufen. Das sind keine echten Agenten,
Client-Aufrufe oder DB-Initialisierungen. Reale API-/Generierungs-Kompatibilität wird
nicht behauptet; die Offline-Prüfung umfasst den bestehenden Aufrufvertrag.

Der lokale vollständige Original-SRT-Pilot wird zusätzlich synchron ausgeführt:
Der Test-Helper entfernt seinen bisherigen Async-Loop und alle Marvin-DB-Schalter.
Alle 157 Chunks und 314 synthetischen Evidence-Belege werden weiterhin geprüft;
Marvin muss auch dort ungeladen bleiben. Diese bereits uncommittierte Pilot-Testdatei
wurde nur im Workspace angepasst und wird nicht als große neue Testdatei in diesen
kleinen PR dupliziert.

## Voraussetzungen und Grenzen

Für deterministische Imports bleiben die vorhandenen App-Dependencies und gültige
FolderEnvVars/AgenticEnvVars erforderlich. Dieser PR beseitigt nicht die bestehende
Settings-Initialisierung. Deterministische Nutzung benötigt keine funktionierenden
LLM-Zugangsdaten; der Test beweist dies mit Platzhaltern.

Bei tatsächlicher configure_marvin-/extract_knowledge-Nutzung wird die echte
Marvin-Initialisierung bewusst wieder erreicht. Produktions-LLM-Verarbeitung benötigt
weiterhin installierte SDKs, gültige API-Konfiguration, Modellwahl, Logger und eine
funktionierende Marvin-Datenbankumgebung. Der frühere SQLite-Hänger wird für diesen
LLM-Pfad nicht durch versteckte globale Schalter repariert. Vor echtem Betrieb muss
dieser Pfad separat getestet werden. Nicht dokumentierte Attribute des ehemals direkt
dekorierten extract_knowledge-Wrappers werden nicht zugesichert; die vorhandenen
Repository-Aufrufer verwenden ausschließlich seinen normalen Funktionsaufruf.

Der PR baut auf Provenienz-PR #12 auf. Die bereits unabhängigen Korrekturen #9 und
#11 werden nicht dupliziert; ihr Vorhandensein ist für den kombinierten offiziellen
Importer-/Formel-Pilot vorausgesetzt. Kein Download, keine Datenmigration, keine
Änderung an Discovery/Selection und kein automatisches Mergen.

## Testergebnis

Vier frische synchrone Importtests bestanden. Gesamter relevanter uv-Regressionslauf:
**173 Tests bestanden** einschließlich des synchronen Original-SRT-Pilots. Nach
Importbereinigung wurden die vier synchronen Importtests zusätzlich erneut ausgeführt.
Ruff, Repository-Pre-Commit-Prüfungen und git diff --check prüfen den kleinen PR.
