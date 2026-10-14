# Minimaler CS50-Worker / A05

SDK-frei: Pydantic/Settings, HTTPX, BeautifulSoup, Typer, Dotenv, YAML, returns,
tenacity; dev: pytest/ruff. Pins entsprechen exakt dem vorhandenen Root-Lock und
der geprüften Workerinstallation; keine Upgrades. lock_from_repository.py
projiziert den bestehenden Lockgraphen, ohne Registryzugriff oder Neuauflösung.

```bash
python3 workers/cs50/lock_from_repository.py
uv lock --offline --check --project workers/cs50
uv sync --offline --locked --project workers/cs50
# Aus Repositoryroot, wenn Cache/Installation vollständig vorhanden:
UV_PROJECT_ENVIRONMENT=workers/cs50/.venv CS50_TEST_PROFILE=offline \
  uv run --offline --no-sync python -m pytest tests -q
```

Nachweis: Lockprüfung **Resolved 32 packages**. Fresh sync wurde offline versucht
und scheitert an einem nicht gecachten ruff-Wheel. Keine Nachinstallation/Downloads
wurden zugelassen; frische vollständige Installation deshalb nicht behauptet.
Die bestehende reguläre Worker-.venv bleibt die tatsächlich getestete Umgebung.
Cachevorbereitung ist ein ausdrücklich manuell freizugebender Betriebsschritt.

Default CS50_TEST_PROFILE=offline markiert genau den optionalen SDK-Konfigurations-
Smoke als Skip mit nachvollziehbarem Grund. Das installierte Profil wird explizit
mit CS50_TEST_PROFILE=sdk aktiviert; fehlende SDKs sind dort Fehler, keine Skips.
Die SDK-Abhängigkeiten bleiben im bestehenden Root-Extra llm deklariert; dieses
wird hier nicht installiert und ist nicht Bestandteil des SDK-freien Lockgraphen.

```bash
# In einer separat bereitgestellten Umgebung mit bestehenden llm-Abhängigkeiten:
CS50_TEST_PROFILE=sdk uv run --offline --no-sync python -m pytest \
  tests/test_cs50_llm_smoke.py::test_installed_provider_configuration_without_api -q
```

Tatsächlich geprüft: SDK-freier Smoke/Lazy-Import-Lauf **12 passed, 1 skipped in
15,44 s**. Explizites SDK-Profil scheitert erwartungsgemäß an fehlenden openai/
pydantic_ai. Kein echter SDK-/API-/Marvin-/SQLite-Aufruf. Bei installierten SDKs
bleibt der echte isolierte Konstruktionstest mit gesperrtem HTTP-Transport aktiv.
