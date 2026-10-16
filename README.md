# Personal Assistant

Backend und Offline-Werkzeuge für Kursmaterialien, Lecture-/Transkriptverarbeitung,
Knowledge mit Quellenbelegen und reproduzierbare Evaluation. Das lokale
Arbeitsverzeichnis und der Python-Projektname heißen weiterhin `gmp_compliance`
bzw. `gmp-compliance`; dieses Audit benennt weder Paket noch Datenpfade um.

Stand: 16.10.2026, gemergter Backend-`master` `78b35a5` und
[separates UI-Repository](https://github.com/rf-data/personal-assistant-ui).
Die frühere GMP-/SOP-/Streamlit-Anwendung bleibt als Legacy-Code vorhanden und
ist nicht der Einstieg in die neue Admin-UI.

## Einstieg nach Aufgabe

| Bereich | Implementierung und belegter Umfang | Dokumentation |
| --- | --- | --- |
| CS50-Materialien | vorhandene Snapshots → Auswahl/Plan → expliziter Import → HTML-v2/PDF-v2/Code-v1 → normalisierte Blöcke mit Provenienz | [CS50](docs/cs50/README.md), [Materialbetrieb](docs/cs50/operations/material_ingestion.md) |
| Qualität und Lecture-Handoff | C10 validiert offline und liefert referenzierbare Materialien; keine automatische Knowledge-Extraktion | [Quality-Vertrag](docs/cs50/contracts/material_quality.md) |
| Lectures und Transkripte | SRT-first, explizite Quellenbindung, Chunk-/Kurspläne, begrenzte Runner und Resume; Liveausführung getrennt freizugeben | [Lecturebetrieb](docs/cs50/operations/cs50_lecture_runner.md) |
| Knowledge | Evidence-/Source-IDs, kontrollierte Extraktionsgrenzen und konservative Offline-Konsolidierung | [C12](docs/knowledge_consolidation_hardening.md) |
| Mathematik und Visuals | synthetische Formelpaar-Evaluation; technische Bild-/SVG-/Vektorinventur; keine semantische Goldfreigabe | [C11](docs/math_evaluation/README.md), [C13](docs/visual_inventory.md) |
| Job-Control und Workflows | C16: private SQLite-Queue und begrenzter Linux-Executor; C18: optionaler Offline-Materialworkflow mit Resume | [C16](docs/job_control/README.md), [C18](docs/workflows/README.md) |
| Admin-UI | C14/C17 im separaten Repository gemergt; echter C16-Client für Planung/Qualitätscheck | [UI-Einstieg](https://github.com/rf-data/personal-assistant-ui/blob/main/README.md) |
| Monitoring | geprüfte Konfiguration und endlicher Metrikvertrag; C16 liefert authentifizierte Jobmetriken; keine bestätigte Liveinstallation | [C15](docs/monitoring/README.md) |

„Offline getestet“ beschreibt technische Verträge und synthetische Nachweise,
keine fachliche Modellqualität und keine produktive Betriebsfreigabe. Die
[Architektur](docs/architecture.md) trennt aktuelle, experimentelle und geplante
Pfade. [Roadmap](docs/ROADMAP.md) und [Audit](docs/documentation_audit.md) belegen
Status und verbleibende Lücken anhand von Code, Commits und gemergten PRs.

## Lokal und offline beginnen

Python `>=3.12,<3.14` laut `pyproject.toml`. Vorhandene passende Umgebung
verwenden; die deklarativen Workerprofile und deren Offline-Cachegrenzen stehen
in [Entwicklung](docs/development.md). Für die folgenden Hilfepfade sind keine
API-Schlüssel oder produktiven Daten erforderlich:

```bash
python -m scripts.cs50_materials --help
python -m scripts.cs50_material_quality --help
python -m scripts.evaluate_math_formulas --help
python -m scripts.cs50_visual_inventory --help
python -m scripts.job_control --help
python -m scripts.cs50_workflow --help
```

Demos schreiben ausschließlich in einen **neuen externen** Scratchordner und
führen echte begrenzte Offlineadapter mit synthetischen Inputs aus:

```bash
python -m scripts.job_control_demo --output /tmp/new-c16-demo
python -m scripts.cs50_workflow_demo --output /tmp/new-c18-demo
```

Keiner dieser Befehle startet die separate Streamlit-App. C18 bleibt in der
C16-Konfiguration standardmäßig deaktiviert und unterstützt zunächst lokale
HTML-/Code-Materialien. PDF bleibt im Workflow wegen der noch nicht bestätigten
Cancel-/Timeout-Lebensdauer seines Subprozesses gesperrt; der einzelne PDF-v2-
Parser bleibt vorhanden. Die C17-UI kennt diesen zusätzlichen Workflowprozess
noch nicht und benötigt dafür einen eigenen Integrationsschritt.

## Repository und Dokumentation

- `src/model_*`, `src/tools_*`: fachliche Verträge und Verarbeitung;
  `src/job_control`, `src/workflows`: begrenzte Ausführungssteuerung.
- `scripts/`: explizite CLIs und Offline-Demos; `tests/`: Offlineprüfungen/Fixtures.
- `workers/`: deklarierte minimale Profile; `docker/`, `monitoring/`: Konfiguration.
- `frontend/`, `streamlit_app.py`, `_prototypes/`: erhaltene Legacy-/Experimentpfade;
  aktive Referenzen verhindern eine pauschale Entfernung.
- [Dokumentationsindex](docs/README.md), [Inventar](docs/repository_inventory.md),
  [Bereinigungsplan mit Freigabeliste](docs/cleanup_plan.md),
  [frühere Konsolidierung](docs/project_consolidation_report.md).

Persistente Kursdaten, Modelle, Transkripte, Knowledge-Dateien, Logs, DVC-Objekte,
`.env`-Dateien und produktive Volumes sind keine Bereinigungskandidaten dieses
Auftrags. Make-Targets für Monitoring/MLflow, Backups und Systembereinigung sind
operative Befehle; sie gehören nicht zur Offlinevalidierung. Kein Deployment
oder Datenbankzugriff ist allein durch vorhandene Compose-Dateien nachgewiesen.
