# Architektur

## Überblick

gmp-compliance ist eine mehrschichtige Anwendung für Dokumenten-Parsing und RAG (Retrieval-Augmented Generation).

### Datenfluss

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Streamlit)                                           │
│  ├─ Text Extraction (PDF, HTML, Word...)                       │
│  ├─ Data Extraction (Excel, CSV, MatLab)                       │
│  ├─ RAG System (Chunks, Embeddings, SOP-Gen)                   │
│  └─ Monitoring / Dashboards                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Parsing & RAG Core                                             │
│  ├─ Text Extraction (src/tools_parsing/)                       │
│  │  └─ Format-spezifische Parser (PDF, HTML, DOCX...)         │
│  │                                                              │
│  ├─ Text Processing (src/tools_rag/chunk.py)                  │
│  │  └─ Chunking mit Overlap, Spacy-Tokenization              │
│  │                                                              │
│  ├─ Embedding & Vector Store (src/tools_rag/create_embeds.py)│
│  │  └─ Sentence-Transformers → ChromaDB                       │
│  │                                                              │
│  └─ Retrieval & Generation (src/tools_rag/retrieve.py)        │
│     └─ Vector Search → LLM Prompting (teilweise impl.)         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM & Observability                                            │
│  ├─ OpenAI (gpt-4o-mini, gpt-4o)                               │
│  ├─ LiteLLM (Router für mehrere Provider)                      │
│  ├─ Pydantic-AI (strukturierte Extraktion)                     │
│  └─ Langfuse (LLM-Observability)                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Persistenz & Monitoring                                        │
│  ├─ MLflow (Experiment-Tracking)                               │
│  ├─ ChromaDB (Vector Store)                                    │
│  ├─ Prometheus/Grafana (System-Monitoring)                     │
│  └─ File Storage (Parquet, JSON, Markdown)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Module und Verantwortlichkeiten

### Frontend Layer

**`streamlit_app.py`** + **`frontend/pages/`**
- Streamlit-UI mit 25+ Pages
- Navigation zwischen Funktionsbereichen (General, Extract Text, Extract Data, DataViz, RAG, Development)
- Session-State Management mit `src/core/memory.py`

### Core Infrastructure

**`src/core/`**
- **`config.py`**: Pydantic-basierte Umgebungsvariablen-Verwaltung
  - `ParseEnvVars` (Daten-Pfade)
  - `AgenticEnvVars` (LLM-Keys)
  - `MLOpsEnvVars` (MLflow)
  - `OrganizerEnvVars` (E-Mail/Kalender)
  - Zusätzlich: Settings-Klassen für verschiedene Dateiformat-Parser

- **`logger.py`**: Rich Console Logging mit File-Handler
  - Tägliche Log-Rotation
  - Ausgabe und Datei können unterschiedliche Level haben

- **`memory.py`**: Session- und Kontextspeicher
  - `AppSession`: Globale App-State
  - `ParseContext`: Parse-spezifische Kontexte
  - `SOPGenContext`: SOP-Generierungs-Einstellungen
  - `LLMContext`: LLM-Verbindungs-Konfiguration

### Parsing & Text Extraction

**`src/tools_parsing/`** + **`src/model_parsing/`**

```
Eingabedatei (PDF/HTML/DOCX/...)
    ↓
Extractor (format-spezifisch: PDFCleanExtractor, HtmlExtractor, DocxExtractor, ...)
    ├─ Roh-Extraktion (Format-spezifische Bibliothek)
    ├─ Text-Klassifizierung (Überschrift, Paragraph, Code, Liste, Tabelle)
    └─→ TextBlock-Struktur
    ↓
Feature Enricher (optional: Bilder, Quellen)
    ↓
Post-Processing (Format-spezifisch)
    ├─ Header/Footer-Entfernung
    ├─ Deduplizierung
    └─→ Bereinigter Text
    ↓
Assembler (optional)
    └─→ Markdown / HTML / TXT
    ↓
Ausgabe (JSON _info.json, MD, HTML, TXT)
```

**Spezifische Parser:**
- `PDFCleanExtractor` (PyMuPDF-basiert) → PDF → Strukturierte TextBlocks
- `HtmlExtractor` (BeautifulSoup) → HTML → TextBlocks
- `DocxExtractor` (python-docx) → DOCX → TextBlocks
- `NotebookExtractor` (JSON) → Jupyter Notebooks → TextBlocks
- `MarkdownExtractor` → Markdown → TextBlocks
- `WikiPageExtractor` → Wikipedia (via API) → TextBlocks
- `CSVExtractor`, `ExcelExtractor`, `MatlabExtractor` (teilweise impl.)

### RAG Pipeline

**`src/tools_rag/`**

1. **`chunk.py`**: Text-Segmentierung
   - Spacy-basierte Satz-Tokenization
   - Konfigurierbare Chunk-Größe (Tokens)
   - Overlap zwischen Chunks

2. **`create_embeds.py`**: Embedding + ChromaDB
   - Sentence-Transformers Modelle (configurable)
   - ChromaDB Persistenz
   - Batch-Processing für Performance

3. **`retrieve.py`**: Vector-Suche + Generierung
   - ChromaDB Similarity Search
   - ⚠️ SOP-Update-Logik: `NotImplementedError`

4. **`generate_chunks_facts.py`**: Fact-Extraktion aus Chunks
   - LLM-basierte Strukturierung

### LLM Integration

**`src/llm/model_litellm.py`**
- LiteLLM Router (OpenAI, Anthropic, HuggingFace optional)
- Token-Zählung mit `tiktoken`
- Langfuse-Integration (Observability)

**`src/agent/prompts/`**
- SOP-Generierungs-Prompts
- Fehlerbehandlung und Fallback-Strategien

### Utilities

**`src/utils/`**
- `chroma_helper.py` — ChromaDB Client Management
- `dict_helper.py` — JSON/YAML I/O mit Pydantic
- `path_helper.py` — Relativer/Absoluter Pfad-Handling
- `general_helper.py` — Diverse Hilfsfunktionen
- `df_helper.py` — Pandas DataFrame zu Parquet
- `email_helper.py` — E-Mail-Handling (Stubs, nicht implementiert)

## Datenmodelle

### Parsing-Konfiguration

```python
# Allgemeine Settings (YAML)
class GeneralSettings(BaseModel):
    pdf: GenPDFSettings
    html: GenHTMLSettings
    # ... weitere Format-Settings

# Laufzeit-Settings (YAML)
class ParseSettings(BaseModel):
    pdf: ParsePDFSettings
    html: ParseHTMLSettings
    # ... weitere Format-Settings
```

### RAG-Konfiguration

```python
class ChunkSettings(BaseModel):
    container_types: list  # "heading", "paragraph", "code", ...
    spacy_language: "de_core_news_sm" | None
    max_tokens: int
    overlap_sentences: int
    transformer_model: str  # "all-MiniLM-L6-v2", ...
```

## Infrastruktur

### Docker Stack

**`docker/docker-compose.monitoring.yaml`**
- **Prometheus** (9090) — Metrik-Erfassung
- **Grafana** (3000) — Visualisierung
- **AlertManager** (9093) — Alarm-Routing
- **cAdvisor** (8080) — Container-Metriken
- **node-exporter** (9100) — Host-Metriken
- **Portainer** (9443) — Docker UI

**`docker/docker-compose.ml.yaml`**
- **MLflow** (5000) — Experiment-Tracking
- **PostgreSQL** (5433) — MLflow Backend (alternativ SQLite lokal)

### MLflow Setup

```bash
# Lokal:
make mlflow_start
# → SQLite unter mlflow/mlflow.db
# → UI: http://localhost:5000

# Oder Docker:
docker compose -f docker/docker-compose.ml.yaml up -d
# → PostgreSQL Backend
# → Persistente Artifacts unter mlflow/artifacts/
```

## Dependency Matrix

```
streamlit_app.py
├─ frontend/pages/ (25 Modules)
│  └─ src/core/ (config, logger, memory)
│     └─ .env.parse, .env.agentic, .env.mlops, .env.organizer
│
├─ src/tools_rag/
│  ├─ src/tools_parsing/ (Format-spezifische Parser)
│  ├─ ChromaDB (Vector Store)
│  ├─ Sentence-Transformers (Embedding)
│  └─ src/llm/ (LLM API Calls)
│
├─ src/llm/
│  ├─ OpenAI API (OPENAI_API_KEY)
│  ├─ LiteLLM Router
│  ├─ Pydantic-AI
│  └─ Langfuse (optional)
│
└─ docker-compose.monitoring.yaml
   └─ Prometheus, Grafana, AlertManager, ...
```

## Experimentelle / Nicht-Implementierte Komponenten

| Komponente | Status | Details |
|------------|--------|---------|
| E-Mail-Integration | ❌ Not Implemented | `src/tools_organizer/email.py` Hat nur Stubs |
| Kalender-Sync | ❌ Not Implemented | `src/tools_organizer/calendar.py` Hat nur Stubs |
| SOP-Update-Logik | ❌ Not Implemented | `src/tools_rag/retrieve.py` wirft `NotImplementedError` |
| Transkription | ⚠️ Experimental | `_prototypes/tools_transcribe/` |
| NIR-Analyse | ⚠️ Archiviert | `_prototypes/model_nir/` |
| FastAPI Backend | 📋 Planned | Abhängigkeit vorhanden, kein Code |

## Performance Considerations

- **Chunking**: Overlap hilft bei Kontext, kostet aber Redundanz
- **Embedding**: Transformer-Modelle können Memory-intensiv sein (z.B. multilingual-e5-base)
- **ChromaDB**: Lokal persistiert, nicht distributed (für größere Datenmengen: Qdrant/Weaviate erwägen)
- **LLM Calls**: Token-Zählung mit Langfuse tracken für Cost-Monitoring
