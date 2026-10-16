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
  "$QDRANT_WORKER/bin/python" -m pytest tests/test_cs50_index_contract.py -q
```

Keine festen Maschinenpfade in Tests. Vollständig hermetische Vorbereitung des
43-Paket-Profils benötigt einen gefüllten Lock-Wheelcache oder separat autorisierte
Paketbereitstellung. SentenceTransformers wird nur für ausdrücklich aktivierte
lokale Inferenz benötigt; Version aus dem Root-Lock und vorab bereitgestellte
immutable Modelrevision. Gewichte werden von der Pipeline niemals heruntergeladen.

Die vollständige Suite startet bestehende CLI-Worker mit Python -I, das PYTHONPATH
absichtlich ignoriert. Der obige kombinierte Einzeltestaufbau reicht dafür nicht.
Für die tatsächliche Gesamtregression wird eine zusätzliche temporäre venv ohne
Paketinstallation erzeugt; zwei .pth-Dateien binden die bereits bereitgestellten
SDK-/Worker-Site-Packages auch in isolierten Kindprozessen ein:

```bash
"$QDRANT_WORKER/bin/python" -m venv --without-pip "$REGRESSION_WORKER"
export BASE_WORKER QDRANT_WORKER REGRESSION_WORKER
python3 - <<'PY'
import os
from pathlib import Path
sites = Path(os.environ['REGRESSION_WORKER']) / 'lib/python3.12/site-packages'
for filename, variable in [('00-sdk.pth', 'QDRANT_WORKER'), ('01-base.pth', 'BASE_WORKER')]:
    target = Path(os.environ[variable]) / 'lib/python3.12/site-packages'
    (sites / filename).write_text(str(target.resolve()) + '\n')
PY
"$REGRESSION_WORKER/bin/python" -I -c 'import pydantic_settings, qdrant_client, pytest'
UV_PROJECT_ENVIRONMENT="$REGRESSION_WORKER" UV_CACHE_DIR=/tmp/cs50-index-uvcache \
  uv run --offline --no-sync python -I -c 'import pydantic_settings, qdrant_client, tiktoken'
CS50_TEST_PROFILE=offline "$REGRESSION_WORKER/bin/python" -m pytest tests -q
```

Nur neue externe Testumgebung, keine Änderung vorhandener uv-Umgebungen oder
Dependencyversionen. Die .pth-Konfiguration ist ein expliziter lokaler
Reproduktionsaufbau, keine portable auszuliefernde Installation. Ein vollständig
bereitgestelltes deklaratives Profil bleibt der reguläre Betriebsweg.
Auch der gezeigte uv-run-Aufruf mit isolierten Imports wurde tatsächlich ausgeführt.

## Abgleich C17.0 (16.10.2026)

Profil-/Lockdateien bleiben unverändert. Die oben aufgeführten Installations-
und Testergebnisse sind historische Paketnachweise; eine vollständige frische
Offlineinstallation wurde in diesem Audit nicht behauptet. Aktuelle Paketgrenzen,
Testauswahl und bekannte TXT-/SDK-Lücken stehen in
[Entwicklung](../../docs/development.md) und [Auditvalidierung](../../docs/audit/validation.md).
