# Entwickler-Dokumentation

## Umgebungs-Setup

### 1. Repository klonen

```bash
git clone <repository-url>
cd gmp_compliance
```

### 2. Python-Umgebung

```bash
# Mit uv (empfohlen)
uv sync

# Alternativ (nicht getestet):
pip install -e .
```

Prüfe `pyproject.toml` für Dependencies (`main` + `dev`-Gruppe).

### 3. Umgebungsvariablen

```bash
# Datei kopieren
cp .env.parse.example .env.parse
cp .env.agentic.example .env.agentic
cp .env.mlops.example .env.mlops
cp .env.organizer.example .env.organizer

# Werte in .env-Dateien nachtragen (siehe nächster Abschnitt)
```

Prüfe nie Secrets in Git ein:
```bash
# .gitignore sollte enthalten:
.env.parse
.env.agentic
.env.mlops
.env.organizer
```

## Konfiguration

### .env.parse

Daten-Pfade und Logging.

```env
# Erforderlich
DATA_DIR = "/path/to/data"        # Übergeordnetes Datenverzeichnis
LOG_DIR = "/path/to/logs"         # Log-Ausgaben
CACHE_DIR = "/path/to/.cache"     # Cache für Parser

# Optional (Format-spezifisch)
DATA_PDF = "$DATA_DIR/pdf"
DATA_HTML = "$DATA_DIR/html"
DATA_DOCX = "$DATA_DIR/docx"
DATA_JSON_NB = "$DATA_DIR/notebooks"
DATA_TXT_MD = "$DATA_DIR/txt_md"
DATA_WIKI = "$DATA_DIR/wiki"
DATA_AUDIO = "$DATA_DIR/audio"      # Für Transkription (nicht impl.)
DATA_IMAGE = "$DATA_DIR/images_ocr" # Für OCR (nicht impl.)

PROMPT_DIR = "/path/to/prompts"
REPORT_DIR = "/path/to/reports"
CONFIG_DIR = "/path/to/configuration"
CHROMA_DIR = "/path/to/chroma_db"

# API-Endpoints (Wikipedia, etc.)
WIKI_EN_API = "https://en.wikipedia.org/w/api.php"
WIKI_DE_API = "https://de.wikipedia.org/w/api.php"
HEADER_AGENT = "YourBot/1.0 (contact@example.com)"
```

### .env.agentic

LLM-API-Keys und Observability.

```env
# Erforderlich für Text-Generierung
OPENAI_API_KEY = "<your-openai-api-key>"         # ChatGPT API

# Optional
HF_API_KEY = "<your-huggingface-api-key>"            # HuggingFace (für Open-Source Models)

# Optional: Langfuse (LLM Observability)
LANGFUSE_PUBLIC_KEY = ""
LANGFUSE_SECRET_KEY = ""
LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
LANGFUSE_HOST = ""
```

### .env.mlops

MLflow Backend-Konfiguration.

```env
# Optional (wenn leer, nutzt lokal SQLite)
MLFLOW_DB = "sqlite:///mlflow/mlflow.db"              # Default
# oder PostgreSQL:
# MLFLOW_DB = "postgresql://<user>:<password>@localhost:5432/mlflow_db"

MLFLOW_ARTIFACTS = "mlflow/artifacts"
MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"

FINGERPRINT_EXP = "default_exp"
FINGERPRINT_RUN = "default_run"
MLFLOW_BACKUP = "mlflow/backup"
```

### .env.organizer

E-Mail/Kalender (nicht implementiert).

```env
# Nicht funktionsfähig, placeholder
IMAP_SERVER = ""
IMAP_PORT = ""
SMTP_SERVER = ""
SMTP_PORT = ""
EMAIL_RF_ADDRESS = ""
EMAIL_RF_PW = ""
```

### configuration/ YAML-Dateien

**`configuration/streamlit_general.yaml`**
- Parser-Standardeinstellungen (PDF-Parameter, HTML-Tags, etc.)
- Wird beim App-Start geladen

**`configuration/streamlit_run.yaml`**
- Laufzeit-Einstellungen für aktuellen Parse-Job
- LLM-Modell, Pfade, Ausgabeformate

## Makefile-Targets

Alle verfügbaren Targets:

```bash
# UI
make streamlit                  # Streamlit-App starten auf http://localhost:8501

# Dependenzen & Maintenance
make dependency_check           # Vulnerability-Scan (pip-audit)
make clean_linux               # Caches löschen (APT, Python, Jupyter, Logs)

# MLflow
make mlflow_start              # MLflow-Server starten (lokal auf Port 5000)
make mlflow_stop               # MLflow beenden
make mlflow_fingerprint        # Experiment-Fingerprint erstellen

# Monitoring
make monitoring_docker         # Prometheus/Grafana/AlertManager hochfahren
make monitoring_stop           # Monitoring-Stack beenden

# Pre-commit (Hooks nur auf _prototypes/)
make pre_commit_check          # Run hooks manually
make pre_commit_update         # Update + run all hooks
make pre_push_check            # Test pre-push stage hooks
```

## Wichtige Workflows

### Text Extraction (PDF)

```
1. frontend/pages/B_p1_ETL_pdf.py     (UI)
   │
   └→ src/run_st_pdf_extract.py       (Main Function)
      │
      ├→ src/model_tools_parsing/pdf_extractor.py
      │  └─ PDFCleanExtractor (PyMuPDF)
      │
      └→ src/tools_parsing/
         ├─ extract_pdf.py
         ├─ post_extract_processing_pdf.py
         └─ assemble_pdf.py

   Ausgabe: JSON _info.json, Markdown, HTML
```

**Ausführung in Streamlit:**
```python
from src.run_st_pdf_extract import run_pdf_extraction
result = run_pdf_extraction(parse_context)
```

### RAG Pipeline (Chunking & Embedding)

```
1. Data-Pfad mit _info.json Files
   │
   ├→ src/tools_rag/chunk.py
   │  ├─ Spacy-Tokenization
   │  ├─ Chunk-Größe (configurable)
   │  └─ Overlap (Sätze)
   │
   ├→ src/tools_rag/create_embeds.py
   │  ├─ Sentence-Transformers
   │  └─ ChromaDB Upload
   │
   └→ Persistenz: Parquet Files + ChromaDB Collections
```

**Manuell ausführbar:**
```bash
uv run python -c "from src.run_chunk_embed import run_chunk_and_embed; run_chunk_and_embed('/path/to/ready_folder')"
```

### SOP-Generierung (teilweise implementiert)

```
1. frontend/pages/E_p2_sop_generation.py    (UI)
   │
   └→ src/run_st_SOP_generation.py
      │
      ├→ Chroma-Collections auswählen
      ├→ Retrieval via src/tools_rag/retrieve.py
      |  └─ ⚠️ NotImplementedError bei SOP-Update
      ├→ Fact-Extraktion
      ├→ Konsolidierung
      └→ LLM-generierte SOP (teilweise impl.)

   Ausgabe: JSON Facts, Knowledge Pool, Chapter Plans
```

**Status:** Retrieval-Logik funktioniert, SOP-Generierung teilweise.

## Testing

```bash
# Tests ausführen (minimal coverage)
uv run pytest tests/

# Spezifischen Test laufen:
uv run pytest tests/__dev__medium.py -v
```

**Status:** Nur Fragment-Tests vorhanden. Für neue Features Tests bitte manuell schreiben.

## Linting & Type-Checking

Alle Tools sind in `pyproject.toml` konfiguriert:

```bash
# Ruff (Formatter + Linter)
uv run ruff format src/
uv run ruff check src/ --fix

# MyPy (Type-Checking)
uv run mypy src/

# Pre-commit (manuell)
make pre_commit_check
```

⚠️ **Aktueller Status:**

## Code-Struktur Conventions

### Module-Hierarchie

```
src/
├── core/              → Kernel (Config, Logger, Memory)
├── llm/               → LLM-Integration
├── agent/             → Prompts, Agenten
├── model_*.py         → Datenmodelle (Pydantic)
├── tools_*.py         → Business Logic
├── model_tools_*.py   → Tool-Infrastruktur
├── utils/             → Utilities
└── run_*.py           → Entry Points für Scripts
```

### Imports

```python
# OK
from src.core.config import parsing_env_vars
from src.tools_rag.chunk import chunk_text

# Vermeide
from tools_rag.chunk import chunk_text  # Relativ, unklar
import chunk  # Zu kurz, Name-Collision-Gefahr
```

### Logging

```python
from src.core.logger import create_logger

logger = create_logger(
    name="MyModule",
    file_name="mymodule",
    level="info"
)

logger.info("Message: %s", value)
logger.error("Error occurred", exc_info=True)  # Mit Stack-Trace
```

### Konfiguration

```python
from src.core.config import parsing_env_vars, agentic_env_vars

data_dir = parsing_env_vars.data_dir
api_key = agentic_env_vars.openai_api_key
```

## Known Issues & Workarounds

| Problem | Ursache | Workaround |
|---------|--------|-----------|
| **Streamlit reloads beim File Save** | Streamlit Dev-Feature | Normal; nutze `streamlit run --logger.level=debug` für Diagnostik |
| **ChromaDB Memory** | Add große Models → OutOfMemory | Nutze kleinere Transformer-Modelle (z.B. all-MiniLM-L6-v2) |
| **Parser fehlen Features** | Teilweise Implementierung | Siehe `_prototypes/` für alte Versionen |


## Nächste Schritte für Entwickler

1. **Verstehe die Config-Kette**: `.env.parse` → `src/core/config.py` → `app_session`
2. **Tracke Data-Flow**: Text-Datei → Parser → TextBlocks → Chunks → Embeddings → ChromaDB
3. **Nutze Logger überall**: `create_logger("ModuleName")` für Instrumentation
4. **Schreib Tests**: Für neue Parser/Tools, besonders für Datenmodelle
5. **Kommentiere Komplexes**: Regex, Heuristics, Format-spezifische Handler

## Debugging

### Streamlit Debug-Mode

```bash
streamlit run streamlit_app.py --logger.level=debug
```

### Manual Python Execution

```bash
# Umgebung laden
cd /home/robfra/0_Portfolio_Projekte/gmp_compliance
source .venv/bin/activate  # Oder: uv shell

# Modul testen
python -c "from src.core.config import parsing_env_vars; print(parsing_env_vars.data_dir)"

# Script ausführen
uv run python src/run_dependency_check.py
```

### ChromaDB Inspection

```python
from src.utils.chroma_helper import get_chroma_client

client = get_chroma_client()
collections = client.list_collections()
for col in collections:
    print(f"Collection: {col.name}, Count: {col.count()}")

# Beispiel-Query
results = col.query(query_texts=["sample text"], n_results=3)
print(results)
```

### Log-Dateien

```bash
# Tagesaktuelle Logs
ls -la logs/YYYY-MM-DD*.log

# Tail live
tail -f logs/streamlit_demo.log
```
