# CLI für Sources, Embeddings, Index und Retrieval

Alle Schritte sind getrennte Subcommands von scripts.cs50_transcript_index.
Default ist Dry-Run. --execute-download, --write-plan, --execute-embedding und
--execute-upload dürfen jeweils nur beim zugehörigen Schritt verwendet werden.
Ausführende Embedding-/Uploadkommandos benötigen erneut die exakt passende
Lecture-/Kurs-/all-six-Auswahl. Keine impliziten Downloads beim Upload/Embedding.

```bash
# Eine explizite Quelle, nur Preview:
python -m scripts.cs50_transcript_index download \
  --workspace /scratch/cs50-sources --course cs50_python --section 0
# Nur nach eigener Downloadfreigabe/Lizenzprüfung zusätzlich:
# --execute-download --license-reviewed

# Plan aus bereits geprüften Imports; lokale immutable Embeddingkonfiguration:
python -m scripts.cs50_transcript_index plan \
  --workspace /scratch/cs50-sources --course cs50_python --section 0 \
  --write-plan --embedding-config /scratch/embedding.json --output /scratch/index-plan.json
# Ohne bereitgestellte Gewichte nur technische Tests: --fake-embeddings;
# für synthetische Quellen zusätzlich --source-origin synthetic.

python -m scripts.cs50_transcript_index embed \
  --workspace /scratch/cs50-sources --index-plan /scratch/index-plan.json \
  --vectors /scratch/vectors.json --course cs50_python --section 0
# Inferenz erst mit --execute-embedding.

python -m scripts.cs50_transcript_index upload \
  --workspace /scratch/cs50-sources --index-plan /scratch/index-plan.json \
  --vectors /scratch/vectors.json --state-root /scratch/index-status \
  --qdrant-local /scratch/qdrant --course cs50_python --section 0
# Erst separat freigegeben: --execute-upload; frische Collection: --create-collection.

python -m scripts.cs50_transcript_index status \
  --workspace /scratch/cs50-sources --index-plan /scratch/index-plan.json \
  --vectors /scratch/vectors.json --state-root /scratch/index-status --qdrant-local /scratch/qdrant

python -m scripts.cs50_transcript_index search \
  --workspace /scratch/cs50-sources --index-plan /scratch/index-plan.json \
  --qdrant-local /scratch/qdrant --query 'How does Python input return a value?' \
  --course cs50_python --language en --top-k 5
```

Kurs vollständig: --course ohne --section. Alle sechs: ausschließlich --all-six.
Bereits gültige Quellen werden über CS50Executor ohne erneuten Download resumiert;
plan nutzt vorhandene Belege direkt. Noch nicht importierte Sources ergeben keinen
erfundenen Chunkplan; Planpreview meldet expected_units=null bis Tokenizer/Imports
geprüft werden. Raw-SRT bleibt unverändert. Keine TXT/Audio/Video/Whisper-Fallbacks.

Remote: explizit --qdrant-url HTTPS oder QDRANT_URL plus --allow-remote und
QDRANT_API_KEY. Keine Credentials in URL, Artefakten oder Fehlermeldungen.
Keine Cloud-Inference. Upload braucht zusätzlich --execute-upload und exakt
passenden Collectionvertrag; bestehende unbekannte Namen werden nicht adoptiert.
Während Implementierung/Tests keine produktive Verbindung oder Schreiboperation.

Lizenzprüfung der offiziellen sechs Kurs-Lizenzseiten: CC BY-NC-SA 4.0.
Namensnennung, nichtkommerzieller Nutzungskontext und ShareAlike-Bedingungen müssen
vor einer konkreten produktiven Nutzung geprüft werden; --license-reviewed ist
eine Betreiberbestätigung, keine automatisch erteilte Erlaubnis. Quellen/Details:
[Python](https://cs50.harvard.edu/python/license/),
[CS50x](https://cs50.harvard.edu/x/license/),
[SQL](https://cs50.harvard.edu/sql/license/),
[AI](https://cs50.harvard.edu/ai/license/),
[Web](https://cs50.harvard.edu/web/license/),
[Cybersecurity](https://cs50.harvard.edu/cybersecurity/license/).
Original-URLs und Provenienz bleiben erhalten; dieses Projekt führt keine realen
Materialdownloads aus und behauptet keine produktiv vorgenommene Indexierung.
