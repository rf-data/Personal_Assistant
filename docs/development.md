# Entwicklung und Offlineprüfungen

Stand: 16.10.2026. [Architektur](architecture.md), [Roadmap](ROADMAP.md) und
[Dokumentationsindex](README.md) beschreiben die aktuelle Lecture-/Materialbasis.
Die frühere GMP-/SOP-Anleitung bleibt im [historischen Überblick](archive/2026-10/repository-overview/README.md)
erhalten und ist keine aktuelle Installations- oder Betriebsfreigabe.

## Umgebung

Der Rootvertrag in `pyproject.toml` verlangt Python `>=3.12,<3.14` und trennt
kleine Basisdependencies von optionalen `lecture-worker`-, `llm`-, `rag`-,
`frontend`-, `vision`-/`ocr`- und Monitoringprofilen. Der Root-Projektname ist
weiterhin `gmp-compliance`. Eine Umbenennung oder Dependencybereinigung ist nicht
Bestandteil dieses Dokumentationsaudits.

Für Offlinearbeiten eine **bereits bereitgestellte** passende Umgebung verwenden.
`uv sync` ohne Offline-/Lockbegrenzung kann neue Pakete herunterladen und ist
kein Prüfkommando dieses Auftrags. Auch `--offline` funktioniert bei fehlenden
Wheels nicht automatisch. Die vorhandenen Profile dokumentieren ihre tatsächlichen
Cache-/Installationsgrenzen:

- [Minimaler CS50-Worker](../workers/cs50/README.md): SDK-freier Kern.
- [Indexworker](../workers/cs50_index/README.md): zusätzlich isoliertes Qdrant/
  tiktoken; frühere kombinierte Testumgebung ist ein expliziter lokaler Aufbau.
- Das UI hat ein eigenes `pyproject.toml`, Lockfile und Testprofil im
  [UI-Repository](https://github.com/rf-data/personal-assistant-ui).

Es gibt noch doppelte `docling[rapidocr]`-/`pymupdf`-Deklarationen im Root-Extra
`lecture-worker`. Sie bleiben als nachgewiesener Bereinigungskandidat dokumentiert;
keine Lock-Neuauflösung oder Paketänderung wird hier durchgeführt.

## Konfiguration

Die modernen Offline-CLIs nehmen Eingabe-, Workspace- und Reportpfade explizit
entgegen. C16 verwendet eine explizite Settings-JSON mit zugelassenem Hashkatalog,
Identitäten, Coursegrants und privatem Workspace. C18 benötigt zusätzlich
`workflows_enabled=true`; ohne diese Freigabe bleibt der Default bei zwei
C16-Einzeladaptern. [C16-Betrieb](job_control/operations.md),
[C18-Vertrag](workflows/README.md).

Die Legacy-Konfiguration in `src/core/config.py` und die Sessionobjekte in
`src/core/memory*.py` können `.env`-Dateien, globale Settings, SDKs und Datenpfade
initialisieren. Diese Module nicht als allgemeine Import-Smokes verwenden.
`.env.parse`, `.env.agentic`, `.env.mlops`, `.env.organizer`, Tokens und private
Settings bleiben lokal. Vorhandene `.env.*.example`-Dateien sind keine Garantie,
dass für jede Settingsklasse eine aktuelle Vorlage existiert. Keine echten Werte
in Testausgaben oder Reports übernehmen.

## Sichere Hilfepfade und Tests

Vom Repositoryroot in der vorhandenen Umgebung:

```bash
python -m scripts.cs50_materials --help
python -m scripts.cs50_material_quality --help
python -m scripts.evaluate_math_formulas --help
python -m scripts.cs50_visual_inventory --help
python -m scripts.job_control --help
python -m scripts.cs50_workflow --help
python -m src.run_knowledge_consolidation --help
```

Aktuelle deterministische Suiten liegen unter `tests/test_cs50_material_*.py`,
`test_cs50_visual_inventory.py`, `test_math_formula_evaluation.py`,
`test_consolidation_hardening.py`, `test_job_control.py`, `test_job_executor.py`,
`test_cs50_workflows.py` sowie Monitoring-/Discovery-/Knowledge-/Indexsuiten.
Die alte Aussage „nur Fragmenttests“ ist überholt. Es gibt dennoch keinen hier
behaupteten fehlerfreien Repository-Gesamtlauf mit allen optionalen SDKs.

```bash
CS50_TEST_PROFILE=offline python -m pytest -q \
  tests/test_cs50_material_quality.py tests/test_math_formula_evaluation.py \
  tests/test_consolidation_hardening.py tests/test_cs50_visual_inventory.py \
  tests/test_job_control.py tests/test_job_executor.py tests/test_cs50_workflows.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  --basetemp=/tmp/new-isolated-test-root
```

Immer einen neuen ausschließlich für Tests vorgesehenen Scratchordner verwenden.
Einige End-to-End-Demos verlangen einen externen Ausgabeordner; optionale
Originalartefakte werden ohne lokale Bereitstellung ausdrücklich übersprungen.
Kein Test darf dafür Material, Modelle oder Wheels nachladen. Manche Linux-
Prozessprüfungen benötigen die im jeweiligen Paket dokumentierten Berechtigungen.
Die aktuellen [Audit-Testresultate](audit/validation.md) trennen bekannte Fehler,
Umgebungsgrenzen und neue Regressionen.

Für Änderungen nur die betroffenen Dateien prüfen, kein pauschales Reformatting:

```bash
ruff check --no-cache scripts/repository_audit.py tests/test_repository_audit.py
ruff format --check --no-cache scripts/repository_audit.py tests/test_repository_audit.py
git diff --check
```

Die vorhandenen Pre-commit-Hooks prüfen unter anderem AST, JSON, Dateigröße und
Format. `pre_commit_update` aktualisiert Hookumgebungen und ist kein reiner
Offlinecheck. `tests/__dev__medium.py` und `src/run_mlflow_setup_test.py` sind keine
Freigabe für Daten-/MLflowzugriffe; sie bleiben als Legacy-Kandidaten erfasst.

## Repository-/Dokumentenaudit wiederholen

Der neue reine Standardbibliotheks-Scanner liest Git-Metadaten und freigegebene
versionierte Textdateien. Ignorierte/unversionierte Dateien werden grundsätzlich
nur nach Pfadgruppe, Anzahl und Statmetadaten gezählt; zugelassene nichtprivate
Markdown-Dokumente anderer Worktrees werden zusätzlich nach SHA-256 verglichen.
Sensitive Namen, private lokale Konsolidierungsberichte, Runtime-/Datenpfade
und Symlinks werden nicht inhaltlich gelesen. Keine Git-/Dateimutationen außer
dem expliziten neuen Report, kein Netz, kein Import des untersuchten Codes.

```bash
python -m scripts.repository_audit --repository . \
  --baseline 78b35a53b7fc7148a1cbaeb93c4152d35a0725f1 \
  --output /tmp/new-repository-audit.json
```

`baseline` ist ein expliziter bereits lokal vorhandener Commit. Der Scanner
inventarisiert dessen Tree und vergleicht aktuelle Arbeitskopie/Worktrees;
Git-Metadaten sind keine Remoteabfrage. Die Remote-Metadaten wurden für dieses
Audit separat read-only abgeglichen. Linkprüfung umfasst lokale Inline-Markdown-
Dateiziele, keine externen URLs oder Ankersemantik. Historische Dateiverweise in
Codebeispielen bleiben als solche erkennbar; ein fehlender Beispielpfad beweist
keinen Laufzeitfehler. Große ignorierte Bibliotheks-/Datenbestände bleiben nur
aggregiert, und nicht lesbare Verzeichnisse machen die Zählung unvollständig.

## Betrieb und aktive Befehle

`make streamlit` startet die erhaltene Legacy-App, nicht die neue Admin-UI.
`make knowledge_extraction` ruft tatsächlich `src.run_knowledge_consolidation`
auf; die Bezeichnung ist irreführend und wird hier nicht still geändert.
`monitoring_docker`, `monitoring_stop`, MLflow-Start/-Stop, Backups,
`clean_linux.sh` und Setupskripte sind operative Aktionen. Sie gehören nicht zu
Smoke-/Regressionstests und werden im Audit nicht ausgeführt.

Docker-/Composeprüfungen sind ausschließlich lesende `config`-Validierungen mit
synthetischer Umgebung ohne `.env`-Laden. Der vorhandene Monitoringvalidator
bietet dafür einen begrenzten Einstieg und meldet fehlende native Werkzeuge als
`not_run`. Keine Container, Images oder Volumes starten/ziehen/verändern.
[Monitoringbetrieb](monitoring/operations.md), [Jobintegration](job_control/integration.md).

Für öffentliche Audit-PRs nur eine ausdrücklich bereinigte Inventur verwenden.
Der vollständige Scannerreport kann lokale Worktree-/Pfad-/Hashdetails enthalten
und bleibt privat. Die öffentliche C17.0-Fassung exportiert ausschließlich
gegen den bereits veröffentlichten Git-Tree verifizierte Basispfade und
Dokumentations-/Testbelege; der vollständige lokale Bericht liegt ignoriert unter
`docs/_local_audit_c170/`. Ein GitHub-Ziel ist vor Veröffentlichung mit dem
ausdrücklich benannten Repository und dessen Remote-Tree abzugleichen.
