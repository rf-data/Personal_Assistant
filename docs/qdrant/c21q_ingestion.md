# C21-Q: lokaler Pilot und vorhandene CLI

**Kein echter E5-/Qdrant-Import ausgeführt.** Der
[Freigabebericht](real-source-approval-review.v1.json) enthält eine ausgewählte
reale Python-0-Lecture und ihre verifizierten Metadaten, aber ausdrücklich
`ingestion_plan: null`. Ohne echte Tokenizergewichte darf kein E5-IngestionPlan
mit geschätzten Fenstern oder Fake-Vektoren erzeugt werden.

## Tatsächliche Originale

Innerhalb des freigegebenen Backend-Projektpfades wurden zwei explizit ausgewählte
SRT-Kandidaten gefunden: `data/Harvard/cs50_python/cs50-v1/0/.../source.srt`
und `data/cs50_python/lecture0.srt.txt`. Beide haben 189973 Bytes und SHA256
`719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c`.
2228 Cues, tatsächliche Zeitspanne 0–6338 Sekunden; `.srt.txt` ist hier inhaltlich
SRT, kein zeitloser TXT-Import. Es handelt sich um eine Dublette, nicht zwei Lectures.
Vorhandenes `transcript.json` (555980 Bytes) und `execution.v1.json` (2706 Bytes)
passen inhaltlich, ihre Hashes und das gespeicherte Binding entsprechen dem Adapter.

Der aktuelle Adapter/Receipt verweist jedoch auf **`data/lectures/Harvard/...`**;
die Originale liegen unter **`data/Harvard/...`**. Ein direktes Inventar des
Originalworkspaces meldet deshalb korrekt `unverified`. Keine Datei, kein Receipt
und kein Adapter wurde umgeschrieben, kein unbekanntes Artefakt adoptiert.

Für den lokalen Funktionsnachweis wurden genau diese drei ausgewählten Dateien
bytegleich in einem neuen privaten temporären Workspace unter den bereits
gebundenen Relativpfaden abgelegt. Bestehender Binder, Sourcevalidierung und
Originalchunker bestanden: **157 zeitbasierte Chunks**, leere Cues ausgeschlossen.
Receiptbytes und Originaldateien blieben unverändert; die temporären Kopien wurden
anschließend entfernt. 157 ist **keine gemessene E5-Vektorzahl**. Vor einem echten
Pilot muss ein kontrollierter persistenter Quellworkspace mit denselben verifizierten
Dateien bereitstehen oder die vorhandene Pfadabweichung separat behoben werden.

## Aktionsvertrag

Alle Aktionen nutzen `python -m scripts.cs50_transcript_index`. `WORKSPACE` ist
ein explizit kontrollierter lokaler Sourceworkspace. `PILOT` ist ein neuer privater
Outputordner außerhalb sämtlicher Source-/Artefaktroots; keine Secrets in Git.

| Aktion | Verhalten und Schutz |
| --- | --- |
| `inventory` | Nur ausgewählte Adapterdateien; optional bis 16 explizite `--candidate-source` unter demselben Workspace, maximal 8 MiB je Kandidat. Kein Download/Adopt/Upload. `--output` exklusiv. |
| `plan` | Preview standardmäßig; `--write-plan` benötigt echte lokale immutable Modellkonfiguration und passenden Tokenizer. |
| `validate` | Bestehenden IngestionPlan und optional `--vectors` gegen Originale prüfen; keine DB-/Netzverbindung. |
| `embed` | Preview standardmäßig; getrennt `--execute-embedding` plus exakt passende Course-/Sectionauswahl. |
| `upload` / `resume` | Dieselbe bestehende Upsert-/Readbackfunktion. Preview ohne Client; Writes erst mit `--execute-upload`, Scope und ggf. `--create-collection`. |
| `status` / `verify` | Dieselbe vollständige Schema-/Point-/Payload-/Vektorprüfung plus lokaler Receiptstatus. Kein Upload. |
| `search` / `retrieve` | Dieselbe Queryfunktion mit echtem Querypräfix, Filtern und Originalverifikation. |

`resume`, `verify`, `retrieve` sind reine Aliase, keine weitere CLI-Architektur.
`download` bleibt die vorhandene separat gesperrte Aktion; in C21-Q nicht verwendet.
`demo` bleibt der vorhandene synthetische lokale Qdrant-Nachweis und benötigt das SDK.

```bash
python -m scripts.cs50_transcript_index inventory \
  --workspace "$WORKSPACE" --course cs50_python --section 0 \
  --output "$PILOT/source-review.json"

# Nur Metadaten-/Syntaxinventar eines benannten ungebundenen Kandidaten:
# zusätzlich --candidate-source "$WORKSPACE/path/to/source.srt"
# Ein Kandidat ist kein bestätigtes Binding und keine Übertragungsfreigabe.
```

Inventar meldet Paketmetadaten und vorhandene E5-Snapshotnamen. `--model-cache`
ist der explizite Hugging-Face-Hub-Cacheroot, `--model-revision` die volle
40-stellige Revision. Ein Cacheverzeichnis beweist keine intakten Gewichte;
`weights_integrity_verified` bleibt im Inventar falsch, bis echte Modellprüfung
separat ausgeführt wird. Kein Lesen einer beweglichen `refs/main` als Revision.

## Modellbereitstellung und echter Plan

Fehlende SDK-/Workerpakete aus dem vorhandenen Lockprofil separat bereitstellen.
Das öffentliche [Konfigurationsbeispiel](config.example.v1.json) ist ein
**Vorbereitungsvertrag**, keine gültige EmbeddingConfig: `revision: null` ist ein
bewusster Blocker. Nach Auswahl einer geprüften immutable Revision daraus eine
private vorhandene `EmbeddingConfig` erstellen, z.B. Batchgröße 1 bei wenig RAM.
Kein zufälliger Hash oder `main` als scheinbar gültige Revision.

Nur nach eigener Freigabe Modellcache füllen, etwa mit bereits bereitgestelltem
`huggingface_hub.snapshot_download(repo_id="intfloat/multilingual-e5-base",
revision=APPROVED_FULL_COMMIT, local_files_only=False)` im privaten Cacheroot.
Das ist ein **nicht ausgeführter Downloadschritt**, keine Handlung dieses Tickets.
Genau eine benötigte Gewichtsvariante und Tokenizer-/SentenceTransformerdateien
bereitstellen, Integrität prüfen; kein unbeschränktes Herunterladen aller ONNX-/OpenVINOvarianten.
Anschließend offline testen (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`), echten
LocalEmbedder laden und Testpassage/Query auf Dimension/L2 prüfen.

```bash
python -m scripts.cs50_transcript_index plan \
  --workspace "$WORKSPACE" --course cs50_python --section 0 \
  --embedding-config "$PILOT/embedding.json" --collection "$COLLECTION" \
  --write-plan --output "$PILOT/plan.json"
python -m scripts.cs50_transcript_index embed \
  --workspace "$WORKSPACE" --course cs50_python --section 0 \
  --index-plan "$PILOT/plan.json" --vectors "$PILOT/vectors.json" \
  --execute-embedding
python -m scripts.cs50_transcript_index validate \
  --workspace "$WORKSPACE" --index-plan "$PILOT/plan.json" \
  --vectors "$PILOT/vectors.json"
```

Planpublikation überschreibt keine vorhandene Datei. `embed` kann ein unverändertes
passendes Vektorartefakt nach Quellen-/Konfigurationsprüfung wiederverwenden;
Konflikte werden nicht überschrieben. Nicht denselben Outputpfad für verschiedene
Plan-/Modellstände verwenden.

## Phase B: getrennt freigegebener Pilot 1

Die [Betriebscheckliste](c21q_operations.md) muss explizit abgezeichnet sein.
Remoteclient liest den Key ausschließlich aus dem privaten Prozessenvironment,
nicht aus Argumenten/Reports. Secretverwaltung stellt `QDRANT_API_KEY` bereit;
keine Shellausgabe, kein `set -x`. Die URL ist ein reiner HTTPS-Origin ohne
Credentials/Pfad/Query/Fragment. Umgebungsproxies und Redirects sind deaktiviert,
TLS-Prüfung bleibt aktiv; ein eigenes CA-Bundle benötigt ein separat geprüftes Profil.

```bash
# Vorschau: KEIN --allow-remote, KEIN --execute-upload erforderlich.
python -m scripts.cs50_transcript_index upload \
  --workspace "$WORKSPACE" --index-plan "$PILOT/plan.json" \
  --vectors "$PILOT/vectors.json" --state-root "$PILOT/status"

# Erst nach konkreter Phase-B-Freigabe für Collection und Payloadtexte:
python -m scripts.cs50_transcript_index upload \
  --workspace "$WORKSPACE" --course cs50_python --section 0 \
  --index-plan "$PILOT/plan.json" --vectors "$PILOT/vectors.json" \
  --state-root "$PILOT/status" --qdrant-url "$QDRANT_URL" \
  --allow-remote --execute-upload --create-collection
```

Danach identischer `resume`-Aufruf **ohne** `--create-collection` bei Abbruch,
anschließend `verify` mit Plan/Vektoren/Statusroot und denselben Verbindungsflags.
Voller Readback ist Pflicht. Status kann technische lokale Qdrant-/SQLite-Lockdateien
verwenden; dies ist keine garantierte physisch schreibgeschützte Dateisystemöffnung.

`retrieve` mit Plan, Connectionflags, `--query`, `--course cs50_python`,
`--lecture-id` aus dem Binding, `--language en --top-k 5` ausführen. Freie Suche
und einzelne Filter getrennt testen; Sourcefilter und query:-Präfix bleiben aktiv.
Falsche Modellrevision/Dimension muss vor Treffern scheitern. Jeder Treffer muss
Originalchunk, Cue-IDs, echte Zeit und `original_source_checked=true` behalten.

Nach Pilot 1 nur separat freigegebenen Kursumfang planen. Unveränderte Quellen
und Vektoren wiederverwenden; Resume/Readback erneut prüfen. Mehrere Kurse bleiben
eine weitere separate Freigabe, keine pauschale Übernahme des Bestands.

## Manuelle Bewertung und Ressourcen

[Reviewvorlage](manual-review.v1.json) referenziert die vorhandenen zehn
source-grounded Fragen. Reviewer prüft Lecture, Textstelle, Provenienz, Rangfolge,
Formeln, Dubletten und fehlende Treffer. Vorgeschlagene Cuefenster sind kein Goldset.
Ohne vollständige reale Relevanzurteile bleiben Precision@k, Recall@k und MRR null.
Vorhandene `reviewed_metrics` bleiben für Recall/MRR maßgeblich; Precision wird erst
aus der tatsächlich vollständig beurteilten Top-k-Menge berechnet, mit explizitem Nenner.

CPU/RAM, reale E5-Units, Embeddingsekunden/Units pro Sekunde, Upsert-/Readbackzeit,
Retrievallatenz und Speicher getrennt messen. Der [Ressourcenbericht](resources.v1.json)
enthält aktuelle Voraussetzungen und ausdrücklich unbekannte Leistungswerte.
Kein Kursbedarf wird aus synthetischen 100 Points oder 157 zeitbasierten Chunks geschätzt.
