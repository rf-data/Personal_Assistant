# MAINT-04B – Validierung und ausstehender Gitabschluss

25.10.2026. **C26 HOLD; keine Produktionsfreigabe.** Der Workflowkursfehler ist
lokal korrigiert. Legacyintegration und RunSettings sind ursächlich eingegrenzt;
vollständige Legacy-SDKprüfung und eine kompatible Aliasreparatur bleiben offen.
Das gezielte Extended-Gate bleibt wegen zweier Prozessfehler **rot**.
Integration in `master` und Gitabschluss sind **pending**.

## Vorbereitung und sichere Arbeitsgrenze

Vorbestehender zugewiesener Worktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint04b`, anfänglich sauber,
ausschließlich Branch `fix/maint04b-schema-legacy`, Head/Basis
`1a973f40199302416c4726658eb641c40dbae724` (MAINT-04).
Alle acht angeforderten Eingangsdateien einschließlich AGENTS.md vorhanden und
gelesen. Testprofile, synthetische Fixtures und vorhandene Interpreter vor
Produktivänderung geprüft. Keine fremden Worktrees geändert oder für Tests benutzt;
nur vorhandene Interpreter/Tools lesend verwendet. Keine zusätzlichen Gitbranches
oder Worktreeregistrierungen angelegt, keine Stashes, produktiven Datenbanken
oder Produktdaten verändert.
Synthetische Testdaten und Quellsnapshots liegen in eigenen `/tmp/maint04b-*`-
Wurzeln. Keine optionalen Pakete installiert, keine APIs/LLMs/Modelle/Downloads,
Listener, Qdrant-/Clouddienste, Docker, SSH oder Server verwendet.

Lokaler `master=c1007efdbac3c1544020f328a3a1347e481797ba` und
`origin/master=e68275205fefb7a5f6db42bc45060e505bfcefb5` sind reine lokale
Beobachtungen, kein aktueller Live-Integrationsnachweis. Die Aufgabe verbietet
Merges und Änderungen an master. Keine Integration wird aus diesen Refs abgeleitet.

`git add --dry-run src/core/config_parsing.py` wurde vor jeder Indexänderung mit
`index.lock: Read-only file system` im gemeinsamen Gitverzeichnis abgelehnt.
Kein Umgehen dieser Grenze, kein Commit, Push, Remoteobjekt oder Draft-PR.
Deshalb wird das vollständige Reviewpaket als vorwärts/rückwärts geprüfter Patch
bereitgestellt. Der allgemeine AGENTS.md-Integrationsabschluss bleibt wegen der
Schreibgrenze und des ausdrücklichen Mergeverbots ausstehend. Branch und Worktree
werden gemäß auftragsspezifischem Löschverbot vollständig erhalten.

## Ergebnisse und Aussagegrenzen

K und E bezeichnen die in [Legacyintegration](maint04b_legacy_integration.md)
genannten vorhandenen Python-3.12.12-Interpreter; K verwendet Pydantic 2.13.4,
E 2.14.1. Ruff **0.16.0** aus dem vorhandenen Pre-commit-Cache.

| Prüfung | Tatsächliches Ergebnis |
| --- | --- |
| Core vor Produktivänderung, K | **350 passed**, 9,12 s; `/tmp/maint04b-core-before.xml` |
| Erster Baselineversuch Workflow + Alias mit K | **Collectionfehler** wegen fehlendem bs4 beim Workflowtest; kein funktionaler Workflowfehler daraus abgeleitet |
| Bekannter Workflow-Snapshot + bestehende Aliascharakterisierung, unveränderter Worktree, E | **1 failed / 2 passed**, 2,27 s; Snapshotkonflikt reproduziert |
| Derselbe Snapshottest auf reinem unverändertem `git archive HEAD`, E | **1 failed**, 1,67 s; `/tmp/maint04b-pristine-schema.xml` |
| Rekursiver vollständiger Schemaabgleich, Basis K/E | Je **genau vier** identische Enumabweichungen |
| Neue Vertragsfälle vor Produktivänderung, K | **5 failed / 45 passed**, 1,34 s; `/tmp/maint04b-new-baseline.xml` |
| Neue Vertragsfälle nach Korrektur, K | **50 passed**, 1,42 s; `/tmp/maint04b-new-after-locked.xml` |
| Finales Coreprofil, K | **400 passed**, 18,91 s, **0 Skips/Fehler**; `/tmp/maint04b-core-final.xml` |
| Gezieltes Extended-Offline-Teilprofil, E | **410 passed / 1 failed / 0 skipped / 3 deselected**, 395,36 s; `/tmp/maint04b-extended-targeted.xml` |
| Zusätzliche PDF-Workflow-/Assignmentdateien, E | **24 passed / 1 failed / 0 skipped / 1 deselected**, 118,41 s; 1 bestehende Serializerwarnung; `/tmp/maint04b-workflow-additional.xml` |
| Zwei rote Prozessnodes auf unveränderter MAINT-04-Archivbasis, E | **2 passed**, 11,38 s; `/tmp/maint04b-process-baseline.xml`; breite Fehler dadurch nicht widerlegt |
| Dieselben zwei Prozessnodes auf aktuellem Code, E | **2 passed**, 10,83 s; `/tmp/maint04b-process-recheck.xml`; keine Ursachenreparatur daraus abgeleitet |
| Vollständiger Schemaabgleich nach Korrektur, K/E | Je **0 Differenzen**; beide veröffentlichten Snapshots unverändert |
| Frische Importprobes, je 22 | K **5 importiert / 17 Dependencyabbrüche**, E **7 / 15**; keine Pytest-Erfolgszählung |
| R07-Bindungsprobes, unveränderter Originalcode | read_docx_text, extract_docx und _iter_block_items jeweils **NameError: Document**; isolierter Code, kein Vollimport |
| Ruff Check / Formatcheck aller 6 Pythondateien | **Bestanden**, keine Suppressionen oder Massenformatierung |

Temporäre JUnit-/JSONprobes liegen unter `/tmp/maint04b-*`; die wesentlichen Befunde bleiben
in diesen vier Repositoryberichten erhalten.

**53 neue Pytestfälle**: 22 Workflowvertrag, 28 RunSettingscharakterisierung,
3 echte synthetische PDF-Wortgrenzen. Alle 53 bestehen im gezielten E-Lauf;
die 50 SDKfreien Fälle sind zusätzlich explizit in Core aufgenommen. Die drei
PDFfälle gehören wegen PyMuPDF zu Extended, nicht zum skipfreien Coreprofil.
Alle **151 MAINT-04-Fälle**, die **34 MAINT-03-Regressionen** sowie die ausgewählten
MAINT-03B-Isolationsfälle bestehen. Core und Extended überlappen; Zahlen nicht
addieren. Die beiden Extended-Teilumfänge verwenden verschiedene Testdateien;
zusammen **434 passed / 2 failed / 0 skipped**, vier explizite External-Deselektionen.

Ein erster Entwicklungslauf der neuen Tests hatte zusätzlich eine eigene falsche
Fixtureannahme: example-pdf-report enthält Preview/Report in einem Envelope,
keinen nackten Workflow. Dieser Test wurde vor Produktivänderung korrigiert;
der endgültige 5/45-Baselinelauf verwendet die korrekte Fixture. Der erste Lauf
mit dieser Testannahme (6/44) wird nicht als sechster Produktfehler ausgewiesen.

Kein vollständiger Extendedlauf: Die Produktivänderung ist ein einzelner
Modellimport mit Vertragswirkung. Vollständige Schema-/Kursprüfungen und die
relevanten echten Workflow-/PDF-/Assignment-/Parser-/CLI-/Isolationsdateien sind
gezielt geprüft; ein weiterer rund 45-minütiger Gesamtlauf wurde nicht ausgeführt.
Insbesondere keine Behauptung über Qdrantmodulskips, SymPybackend oder alle
Worker-/Cancel-/Content-/Searchfälle dieses Standes. Die 25 Skips aus MAINT-04
sind historische Zahlen und nicht das Ergebnis dieses Auftrags. Keine neuen
xfails, keine pauschalen Skipregeln, keine entfernten Assertions.

## Rote Prozessfälle und erhaltene Evidenz

1. `tests/test_workflow_http.py::test_tampered_reports_references_are_rejected_before_opening_stage_paths[unbound_output]`:
   scheitert bereits in `completed(scope)`, vor der eigentlichen Reportmanipulation,
   mit `Unavailable: Unconfirmed cleanup; dispatch quarantined`. Die kopierte
   synthetische Jobsdatenbank belegt einen unterbrochenen CS50-Pythonjob:
   `Execution interrupted (OperationalError); no automatic retry`, fehlender
   Exitcode/Dauer und erhaltener Quarantänemarker. Der konkrete SQLitefehlercode
   und die auslösende Guardianoperation fehlen weiterhin. Das entspricht dem
   offenen MAINT-03B-N02/N03-Symptombereich, beweist keine identische Ursache.
2. `tests/test_pdf_workflows.py::test_pdf_stale_resume_uses_new_outputs_without_overwriting_prior_files[image]`:
   `sqlite3.OperationalError: database is locked` in
   `Store.connection`, `PRAGMA synchronous=FULL`, beim lesenden Controllerpoll.
   Gesicherte synthetische Jobdaten zeigen den ersten Lauf completed und den
   Resumeadapter failed/Exit 3. Der innere Adapterfehler ist nicht persistiert;
   eine gemeinsame Ursache mit Fall 1 ist nicht bewiesen.

Die beiden Teilumfänge liefen zeitlich überlappend in separaten Prozessen und
getrennten Tempwurzeln. Zusätzliche Ressourcen-/Timingabhängigkeit ist deshalb
eine Hypothese, kein nachgewiesener Mechanismus. Beide Nodes bestehen anschließend
gemeinsam auf der unveränderten Archivbasis. Das ist **keine** Reproduktion
derselben breiten Fehler und kein Beweis für deren Behebung oder Ursprung.
Keine kausale MAINT-04B-Regression nachgewiesen; Prozessursache weiterhin offen.

Die Originalwurzeln bleiben erhalten:

- `/tmp/maint04b-extended-targeted-data/test_tampered_reports_referenc3/private`
- `/tmp/maint04b-workflow-additional-data/test_pdf_stale_resume_uses_new3/private`

DB/WAL/SHM wurden zur Untersuchung in eigene Forensiktempwurzeln kopiert;
Quellhashes vor/nach dem Lesen der Kopien stimmen überein. Keine Quarantäne
gelöscht, keine Sicherheits-/Retry-/Timeout-/Hardlinkregel verändert.
Die zwei sporadischen Fehler sind bis zur gezielten Prozessdiagnostik offen.

## Reproduzierbare Testauswahl

```bash
LOCKED_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python
OFFLINE_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python
"$LOCKED_PYTHON" scripts/test_profiles.py core --junitxml=/tmp/maint04b-core.xml

MAINT04B_FILES=(
  tests/test_workflow_course_contract.py tests/test_runsettings_contract.py
  tests/test_legacy_pdf_boundary.py tests/test_parsing_configuration.py
  tests/test_parsing_configuration_integration.py tests/test_workflow_http.py
  tests/test_cs50_workflows.py tests/test_maint03b_isolation.py
  tests/test_cs50_material_contracts.py tests/test_cs50_material_pdf.py
  tests/test_cs50_material_pdf_v2.py tests/test_cs50_material_html.py
  tests/test_cs50_material_code.py tests/test_cs50_material_processing.py
  tests/test_cs50_material_e2e.py tests/test_cs50_lecture_runner.py
  tests/test_cs50_lecture_adapter.py tests/test_cs50_llm_smoke.py
  tests/test_dev03_parsing.py tests/test_content_course.py
)
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$OFFLINE_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard -m 'not external_integration' "${MAINT04B_FILES[@]}" \
  --junitxml=/tmp/maint04b-targeted.xml --basetemp=/tmp/maint04b-targeted-data

PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$OFFLINE_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard -m 'not external_integration' \
  tests/test_pdf_workflows.py tests/test_cs50_assignment_integration.py \
  --junitxml=/tmp/maint04b-additional.xml --basetemp=/tmp/maint04b-additional-data
```

Frische Tempwurzeln verwenden; die oben gesicherte Evidenz nicht überschreiben.
Baselinesnapshot: `git archive 1a973f4` in eine eigene Tempwurzel entpacken und
dieselben konkret fehlgeschlagenen Nodes mit E und tests.offline_guard aufrufen.
Die zwei Aliasfehler sind absichtliche **Negativcharakterisierungen**, keine
funktionsfähigen Aliasvalidierungen. Die Auditprobes ergänzen die Testgrenze;
keine transitive Betriebssystem-Netzisolation behauptet.

## Dateien, Patch und Folgeauftrag

Zehn beabsichtigte Dateien:

- `src/workflows/models.py`: expliziter Discoverykursimport als einziger Produktivfix.
- `scripts/test_profiles.py`: 50 neue SDKfreie Fälle in Core.
- `scripts/maint04b_legacy_probe.py`: reproduzierbares frisches Importinventar.
- `tests/test_workflow_course_contract.py`, `tests/test_runsettings_contract.py`,
  `tests/test_legacy_pdf_boundary.py`: 53 neue Fälle.
- Diese Validierung und `maint04b_schema_analysis.md`,
  `maint04b_legacy_integration.md`, `maint04b_runsettings_analysis.md` unter
  `docs/maintenance/`.

Keine Änderungen an Snapshots, Lockdateien, Parsern, Settingsfeldern, Deployment,
Security, C26/C27 oder anderen Worktrees. Der einzige Akzeptanzwechsel ist die
dokumentierte Rückkehr von Workflow-Definition/Report/State/HTTP zur veröffentlichten
CS50-Grenze; versehentlich gültige Nicht-CS50-Reports brauchen bei tatsächlichem
privatem Bestand eine eigene Entscheidung. Keine Defaultänderung.

`/tmp/maint04b-review.patch` enthält alle zehn Dateien gegen exakt die genannte
Basis. Abschlussprüfung: Reverse-Check gegen den aktuellen Arbeitsbaum,
Vorwärts-Check und Anwendung in frischem `git archive HEAD`-Snapshot, Vergleich
jedes betroffenen Dateiinhalts per Bytes/SHA-256 und der oben dokumentierten
unveränderten lokalen Heads. Im temporären Prüfsnapshot wird der Patch auch
tatsächlich rückwärts angewendet (Originaldateien wiederhergestellt, nur die
acht eigenen neuen Patchdateien dort entfernt) und danach erneut vorwärts
angewendet und byteweise verglichen. Der Aufgabenworktree bleibt dabei erhalten.
Die maschinenlesbare Lieferliste liegt unter `/tmp/maint04b-delivery.json`.
Temporäre Prüf-/Import-/Forensikdaten bleiben außerhalb des Patches erhalten.

Manueller Gitabschluss: In regulär schreibbarer Umgebung exakt dieses Paket auf
dem benannten Branch prüfen und committen, Vorgängerintegration (MAINT-03,
MAINT-03B und MAINT-04) kontrollieren und eigenen Draft-PR über den regulären
Reviewprozess vorbereiten. Kein Merge in diesem Auftrag. Die vier dauerhaften
Berichte müssen nach später erlaubter Integration tatsächlich in `master`
verifiziert werden. Bis dahin kein vollständiger Repositoryabschluss und keine
Gitbereinigung; alle vorhandenen Branches/Worktrees/Stashes bleiben erhalten.

Empfohlener Folgeauftrag: gezielte phasenbezogene SQLite-/Guardian-Diagnostik
mit synthetischen Crash-/Resumeprobes; separates kleines DOCX-/SDKprofil mit
echten Fixtures und erst danach Importreparaturen; explizite RunSettings-
Formatentscheidung gemäß [Analyse](maint04b_runsettings_analysis.md).
