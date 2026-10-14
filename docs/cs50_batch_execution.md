# B05 – Dünner Sechs-Kurse-Batch / ausführbare Offline-Demo

Abhängigkeit: B04 (PR #34). prepare_batch verlangt exakt die sechs Original-IDs,
50 eindeutige Bindungen und 100 eindeutige bestehende SRT-Tasks. Verarbeitung erfolgt
über denselben Scheduler und **ein** Budget, concurrency=1; kein eigenes Budget pro
Kurs. Source-ID-basierte Jobpfade kollidieren nicht. Reports enthalten globale und
kursweise Lecture-/Chunk-/Request-/Tokenzahlen, Ressourcenreferenzen und Herkunft.

Reale SRTs müssen separat ausdrücklich über den vorhandenen Executor bezogen sein.
Der Knowledge-Scheduler startet keine Downloads, kein Video/Whisper und keine
Knowledge-Verarbeitung aus ungeprüften Quellen. Einzelkurs und Sechs-Kurse-Scope
verwenden denselben CLI-Worker mit Offline-Default, Prozessgruppen-Timeout und
Parent-Freigabe für ausdrücklich gewünschte LLM-Verarbeitung.

```bash
# Ein bereits importierter Kurs, rein offline/synthetisch:
uv run --offline --no-sync python -m scripts.cs50_schedule \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest /explicit/inputs.v2.json --workspace /explicit/source-workspace \
  --output /separate/scratch/course --course cs50_python --timeout 120

# Sechs-Kurse-Auswahl muss ausdrücklich sein:
# zusätzlich --six-course-batch und je ein --course für cs50x, cs50_python,
# cs50_sql, cs50_ai, cs50_web, cs50_cybersecurity.
# --max-lectures begrenzt next-pending; --audit-only prüft ohne Dispatch.
```

Ausführbare vollständige Demonstration ohne produktive Artefakte/Netzwerk:

```bash
uv run --offline --no-sync python -m scripts.cs50_offline_demo \
  --output /scratch/new-exclusive-cs50-demo
```

Die Demo erzeugt ausschließlich technische synthetische SRTs außerhalb des Repos,
benutzt den echten Executor mit MockTransport, Importer, portable Bindung, Chunker,
HTTP-Provider mit Fake-Antworten, Evidence und deterministische Consolidation.
Alle 50 Lectures werden abgeschlossen und erneut validiert resumiert, ohne neuen
Provideraufruf. Die 100 Download-/Import-Aktionen sind **Fake-HTTP**, keine echten
Downloads. Synthetische Antworten sind keine Goldaussagen oder Qualitätsnachweise.

Ein bestehender Demoordner wird nicht überschrieben. Der eigentliche Scheduler
resumiert nur passenden Scope/Hash/Version/Provider-/Source-Kontext. Unbekannte
Anfragen blockieren kursübergreifend. Defaultlimits sind bewusst klein; größere
reale Limits/Laufzeit müssen explizit gewählt und fachlich freigegeben werden.
