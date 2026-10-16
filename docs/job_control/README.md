# C16 – Lokale Job-Control-API

Stand: 16.10.2026. [Architekturentscheidung/Bestandsaufnahme](architecture.md).
Zwei echte Offline-Adapter: **material_planning** und **quality_evaluation**.
Keine Downloads, LLMs, Transkription, Parseränderungen oder produktiven Starts.

- [HTTP-/Datenvertrag und C14-Unterschiede](api.md)
- [Betrieb, Sicherheit und Wiederanlauf](operations.md)
- [C15-Metriken und Deployment-Grenzen](integration.md)
- [Testnachweise](validation.md)
- [Tatsächlich durchlaufene synthetische Jobs](example-run.v1.json)

Katalog und Ergebnisdateien verwenden die bestehenden Material-, Planungs- und
Qualitätsmodelle. SQLite speichert ausschließlich die neue Jobverwaltung.

## Isolierte Demo

Mit vorhandenen Projektdependencies (Python 3.12, Pydantic, HTTPX, BeautifulSoup
aus dem bestehenden lecture-worker-Profil), Linux:

```bash
python -m scripts.job_control_demo --output /tmp/neue-c16-demo
```

Das Ziel muss neu und außerhalb des Repositorys liegen. Zwei synthetische
Inputs werden erstellt, beide echten Adapter laufen in begrenzten Subprozessen,
Jobzustände/Artefaktmetadaten und strukturierte Ereignisse werden aufgezeichnet.
Kein HTTP-Socket oder produktiver Dienst wird für die Demo benötigt.
Keine Scores oder Modellqualitätsaussagen aus diesen synthetischen Daten ableiten.

## Lokaler Dienst

Die Demo-Konfiguration enthält bewusst einen öffentlichen synthetischen Testtoken.
Sie ist ausschließlich für eine isolierte lokale Demo geeignet. Für eigene
Daten eine private Konfiguration mit starken individuellen Tokens verwenden.

```bash
python -m scripts.job_control check --config /tmp/neue-c16-demo/config.json
# Zwei getrennte Terminals/Services:
python -m scripts.job_control worker --config /tmp/neue-c16-demo/config.json
python -m scripts.job_control api --config /tmp/neue-c16-demo/config.json --port 8016
```

Nur der explizite worker-Befehl startet Ausführungen; der API-Prozess tut dies
nie. Bindadresse ist fest 127.0.0.1. Ohne Identitäten sind alle Endpunkte gesperrt,
ohne execution_enabled sind neue Jobs/Starts deaktiviert.

## Optionaler Workflowprozess (C18)

`workflows_enabled=true` ergänzt ausdrücklich den Prozess
`cs50_offline_workflow`; der Default enthält weiterhin die zwei Einzeladapter.
Der Workflow verwendet dieselbe Queue, Jobhistorie, Guardian- und Cancelkontrolle.
[Verträge, separate Konfiguration und CLI](../workflows/README.md).
C17-UI-DTOs unterstützen diesen optionalen Prozess bisher nicht; dafür ein eigenes
C16-Profil/Workspace verwenden.
