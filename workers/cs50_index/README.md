# SDK-freier Transcript-/LLM-Pfad mit isoliertem Qdrant-SDK

Dieses zusätzliche Index-Testprofil erweitert die bestehenden Worker-Pins um
qdrant-client und tiktoken aus dem unveränderten Root-Lock. Keine Upgrades,
OpenAI/Marvin oder SentenceTransformers im Default. Das bestehende Lock-Projektions-
skript unterstützt dafür optional --project; sein bisheriger Default bleibt gleich.

```bash
python3 workers/cs50/lock_from_repository.py --project workers/cs50_index
uv lock --offline --check --project workers/cs50_index
UV_PROJECT_ENVIRONMENT=/separate/index-worker \
  uv sync --offline --locked --project workers/cs50_index
UV_PROJECT_ENVIRONMENT=/separate/index-worker CS50_TEST_PROFILE=offline \
  uv run --offline --no-sync python -m pytest tests -q
```

Lockprüfung: 43 Pakete erfolgreich. Fresh sync wurde offline versucht, aber der
exakt im Root-Lock referenzierte grpcio-Wheel-URL war nicht gecacht. Keine frische
vollständige Installation behauptet. Die nach Freigabe isoliert bereitgestellte
Qdrant-Umgebung plus bestehender regulärer Worker ist die tatsächlich getestete
uv-Umgebung (identische Pydantic-Version 2.13.4, Qdrant 1.19.1). Bei diesem bestehenden
Zwei-Umgebungen-Aufbau werden Base-Site-Packages explizit angegeben:

```bash
PYTHONPATH="$BASE_WORKER/lib/python3.12/site-packages" \
  "$QDRANT_WORKER/bin/python" -m pytest tests -q
```

Keine festen Maschinenpfade in Tests. Vollständig hermetische Vorbereitung des
43-Paket-Profils benötigt einen gefüllten Lock-Wheelcache oder separat autorisierte
Paketbereitstellung. SentenceTransformers wird nur für ausdrücklich aktivierte
lokale Inferenz benötigt; Version aus dem Root-Lock und vorab bereitgestellte
immutable Modelrevision. Gewichte werden von der Pipeline niemals heruntergeladen.
