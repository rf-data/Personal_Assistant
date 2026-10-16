> Historischer Überblick vor C17.0, Basis `78b35a5`. Die Aussagen und
> Befehle beschreiben den damaligen Dokumentationsstand, keine aktuelle
> Betriebsfreigabe. [Aktueller Einstieg](../../../README.md).

# gmp-compliance

Streamlit-basierte Analyseanwendung für Dokumenten-Parsing, Text-Extraktion und RAG-gestützte SOP-Generierung in regulatorischen Kontexten.

## Übersicht

Das Projekt kombiniert mehrere Funktionsbereiche:

- **Text-Extraktion**: Parser für PDF, HTML, Word, Markdown, Jupyter Notebooks, CSV/Excel und Wiki-Seiten
- **RAG-System**: ChromaDB-backed Retrieval mit Chunk- und Embedding-Pipeline
- **SOP-Generierung**: LLM-gestützte Erstellung von Standardarbeitsanweisungen (⚠️ teilweise implementiert)
- **Monitoring**: Prometheus/Grafana Stack für Systemüberwachung
- **MLflow-Integration**: Experiment-Tracking für ML-Workflows

**Aktueller Zustand**: Kern-Parser und RAG-Infrastruktur sind funktionsfähig. Frontend zeigt viele Platzhalter. SOP-Generierung ist teilweise implementiert.

## Voraussetzungen

- Python 3.12–3.13
- `uv` (Package Manager) — [Installation](https://docs.astral.sh/uv/getting-started/installation/)
- Docker + Docker Compose (optional, für Monitoring und MLflow)

## Installation

```bash
# 1. Repository klonen und in Verzeichnis wechseln
cd gmp_compliance

# 2. Mit uv installieren (empfohlen)
uv sync

# 3. Umgebungsvariablen konfigurieren
cp .env.parse.example .env.parse
cp .env.agentic.example .env.agentic
cp .env.mlops.example .env.mlops
cp .env.organizer.example .env.organizer

# Danach .env.parse, .env.agentic, .env.mlops und .env.organizer mit echten Werten füllen
# Siehe docs/development.md für Konfigurationsdetails
```

## Schnellstart

### Hauptanwendung (Streamlit)

```bash
make streamlit
# Öffne http://localhost:8501 im Browser
```

Die Anwendung ist in sechs Hauptbereiche unterteilt:

| Bereich | Funktion | Status |
|---------|----------|--------|
| **General Features** | Cockpit, LLM-Aktionen, Dateisystem, Transkription, E-Mails | ⚠️ teilweise |
| **Extract Text** | HTML, PDF, Wiki, Notebooks, Word, Markdown, OCR, Plain Text | ✅ arbeitet |
| **Extract Data** | Excel, CSV/Parquet, MatLab | ⚠️ teilweise |
| **DataViz & Dashboards** | EDA, PCA | ⚠️ teilweise |
| **RAG System** | Status, Chunk & Embed, SOP-Generierung, File Chat | ⚠️ teilweise |
| **Development** | Entwicklertools | 🔵 intern |

### Abhängigkeits-Audit

```bash
make dependency_check
# Generiert Vulnerability-Berichte in logs/
```

### MLflow

```bash
# Server starten (SQLite lokal oder PostgreSQL via Docker)
make mlflow_start

# Server beenden
make mlflow_stop

# Fingerprint-Experiment anlegen
make mlflow_fingerprint
```

### Monitoring

Der lokale Stack ist auf Loopback beschränkt. Host-/Container-Exporter und
Portainer benötigen explizite Profile; die vier bisherigen Datenpfade bleiben
erhalten. Vor einer späteren Anwendung sind freigegebene Image-Digests und eine
externe Grafana-Secretdatei erforderlich. Echte Pipeline-Metriken sind noch nicht
angebunden; provisionierte Dashboards zeigen ohne Exporter fehlende Daten.

```bash
# Offline-Konfigurationsprüfung; startet keine Container
python -m scripts.validate_monitoring --native
```

[Ist-Analyse, Betrieb/Migration, Metrics-Vertrag und Testnachweise](../../../monitoring/README.md).
Die vorhandenen Make-Targets `monitoring_docker`/`monitoring_stop` sind weiterhin
operative Start-/Stopp-Befehle mit Projektkennung `personal_assistence`, keine
Validierungsbefehle. Vor Nutzung die Betriebsanleitung und bestehende Installation
prüfen; kein automatisches Deployment oder Volume-Löschen.

### Pre-commit Hooks

```bash
# Alle Hooks manuell ausführen
make pre_commit_check

# Hooks aktualisieren und durchlaufen lassen
make pre_commit_update

# Pre-push Hooks testen
make pre_push_check
```

## Repository-Struktur

```
gmp_compliance/
├── streamlit_app.py              # Haupt-Einstiegspunkt
├── frontend/pages/               # Streamlit UI-Module (25 Seiten)
│   ├── A_p*.py                   # General Features
│   ├── B_p*.py                   # Text Extraction
│   ├── C_p*.py                   # Data Extraction
│   ├── D_p*.py                   # Data Viz
│   ├── E_p*.py                   # RAG System
│   └── F_p*.py                   # Development
├── src/
│   ├── core/                     # Kernel (Config, Logger, Memory)
│   ├── tools_rag/                # RAG-Pipeline (Chunk, Embed, Retrieve)
│   ├── model_parsing/      # Parser-Infrastruktur (PDF, HTML, etc.)
│   ├── tools_parsing/            # Spezifische Pipelines pro Format
│   ├── llm/                      # LLM-Integration (LiteLLM)
│   ├── agent/                    # Prompts und Agent-Konfiguration
│   ├── utils/                    # Hilfsfunktionen
│   └── run_*.py                  # Ausführbare Scripts
├── docker/                       # Docker Compose Definitionen
│   ├── docker-compose.monitoring.yaml
│   └── docker-compose.ml.yaml
├── configuration/                # YAML-Konfiguration
├── scripts/                      # Shell-Skripte (MLflow, Cleanup)
├── tests/                        # Tests (minimal)
├── _prototypes/                  # Experimente/Archiviert
└── Makefile                      # Build/Dev-Automatisierung
```

Detaillierte Architekturübersicht siehe [docs/architecture.md](../../../architecture.md).

## Konfiguration

Vier Umgebungsdateien:

| Datei | Zweck | Pflichtfelder |
|-------|-------|---|
| `.env.parse` | Pfade für Daten, Logs, Cache | `DATA_DIR`, `LOG_DIR`, `CACHE_DIR` |
| `.env.agentic` | LLM-API-Keys | `OPENAI_API_KEY` (optional: HF, Langfuse) |
| `.env.mlops` | MLflow-Persistenz | optional |
| `.env.organizer` | E-Mail/Kalender (nicht implementiert) | optional |

Siehe [docs/development.md#konfiguration](../../../development.md#konfiguration) für Details.

## Bekannte Einschränkungen

- ⚠️ **Streamlit-UI**: Viele Pages zeigen Platzhalter ("Under Construction")
- ⚠️ **SOP-Generierung**: Noch nicht vollständig implementiert
- ⚠️ **E-Mail/Kalender**: Nur Stubs vorhanden, nicht funktionsfähig
- ⚠️ **Tests**: Minimale Testabdeckung
- ☑️ **Pre-commit Hooks**:
- ☑️ **Parser**: PDF, HTML, Word, Markdown sind funktionsfähig
- ☑️ **RAG-Infrastruktur**: Chunk & Embed funktionieren
- ☑️ **Monitoring**: Prometheus/Grafana Stack läuft

## Dokumentation

- [CS50-Pipeline und Betrieb](../../../cs50/README.md) — Sechs Kurse, Offline-Tests, Quellenverträge und historisches Archiv
- [docs/architecture.md](../../../architecture.md) — Technische Architektur und Datenfluss
- [docs/development.md](../../../development.md) — Entwickler-Setup und Workflows

## Lizenz

Siehe LICENSE (falls vorhanden).

## Lokale Job-Control-API (C16)

[Architektur, API, sichere lokale Ausführung und Offline-Demo](../../../job_control/README.md).
Zunächst ausschließlich Materialplanung und Offline-Materialqualität; keine
Downloads/LLMs oder automatische Ausführung weiterer Pipelinearten. Der
authentifizierte HTTP-Controller und der begrenzte Executor laufen getrennt.
Eine private SQLite-Jobhistorie erhält Idempotenz und Status über Neustarts.

```bash
python -m scripts.job_control_demo --output /tmp/neue-c16-demo
```

Dies erstellt neue synthetische Fixtures außerhalb des Repositorys und führt
beide echten Offline-Adapter aus. Keine produktiven Daten oder Server verwenden.

## CS50-Offline-Workflows (C18)

[Workflow-Verträge, CLI, Resume und Beispielreport](../../../workflows/README.md).
Optionaler C16-Prozess für lokale HTML-/Code-Materialien bis zum bestehenden
Lecture-Material-Handoff. Im Default deaktiviert; keine Streamlitänderung.
