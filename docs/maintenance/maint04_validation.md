# MAINT-04 – Validierung und ausstehende Integration

25.10.2026. C26 **HOLD**, keine Produktionsfreigabe. Arbeitsstand ist lokal;
die nach AGENTS.md notwendige Integration in `master` bleibt ausstehend.

## Basis, Berechtigungen und Schutzgrenzen

Anfänglich sauberer vorbestehender Branch `refactor/maint04-parsing-config`,
Head `aafba19d549316300a79da37f0ab5f9224d82d37`, zugewiesener Worktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint04`.
Im gemeinsamen Projektgit keine zusätzlichen Branches oder Worktrees erzeugt. Lokaler `master=c1007ef`
ist veraltet; lokales `origin/master=e682752`. Die Schreibprüfung
`git add --dry-run src/core/config_parsing.py` scheitert vor jeder Indexänderung:
`index.lock: Read-only file system` im gemeinsamen Gitverzeichnis.
Keine Umgehung, kein Commit, kein Push, kein Draft-PR, kein Merge.

Eine lesende GitHub-Connectorabfrage bestätigt `master` als tatsächlichen
Defaultbranch und meldet Repository-Pushberechtigung; diese ersetzt weder die
Sandbox-Schreibberechtigung noch eine Integration. Keine externen Nachrichten,
keine Änderungen an vorhandenen PRs. Die lesende Liveprüfung von
[PR #164](https://github.com/rf-data/Personal_Assistant/pull/164) bestätigt
MAINT-03 als offen/ungemergt gegen `master`, Base-SHA `e682752`, Head `6b397eb`.
Die PR-Suche für `head:audit/maint03b-test-stabilization` liefert keinen Treffer;
dies ist kein Veröffentlichungsnachweis für MAINT-03B. Für spätere Veröffentlichung benötigt der
Review **beide Vorgängercommits in dieser Reihenfolge**:

1. `6b397eb4576bac93b318d0e1b8e954d16cb5e08e` (MAINT-03).
2. `aafba19d549316300a79da37f0ab5f9224d82d37` (MAINT-03B).

MAINT-04-Patchbasis ist exakt der zweite Commit. Solange Vorgänger nicht in
`master` integriert sind, einen eigenen gestapelten Review gegen den geprüften
MAINT-03B-Head planen; für einen PR gegen `master` zuerst die tatsächlich
integrierten Vorgängerinhalte verifizieren. Keine vorhandenen MAINT-PRs verändern,
keine Vorgänger blind nochmals übernehmen. Remoteintegration nicht aus lokalen
Trackingrefs oder Commitähnlichkeit ableiten.

Der vorbestehende Branch/Worktree bleibt erhalten, da kein MAINT-04-PR gemergt
ist und die Änderungen/Dokumente noch nicht in `master` liegen. Es wurde kein
Git-Artefakt entfernt. Das ausdrückliche Mergeverbot dieses Auftrags hat Vorrang
vor dem allgemeinen Integrationsabschluss aus AGENTS.md; der Gesamtabschluss
bleibt deshalb **pending**, auch bei lokal erfolgreicher Implementierung.

## Umgebung und Reproduktion

`LOCKED_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python`
ist Python 3.12.12 mit Pydantic 2.13.4/Core 2.46.4, pytest 9.1.1.
`OFFLINE_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`
ist Python 3.12.12 mit Pydantic 2.14.1/Core 2.50.1, BeautifulSoup 4.15.0 und
PyMuPDF 1.27.2.2. Vorhandene Interpreter nur gelesen, keine fremden Venvs oder
Worktrees verändert. Keine Installation, keine Modelle/Downloads, LLM-Aufrufe,
Produktivdatenbanken, Listener, Docker, SSH oder Deployments.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$LOCKED_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard tests/test_parsing_configuration.py \
  tests/test_parsing_configuration_integration.py
"$LOCKED_PYTHON" scripts/test_profiles.py core
"$OFFLINE_PYTHON" scripts/test_profiles.py extended \
  --junitxml=/tmp/maint04-extended.xml --basetemp=/tmp/maint04-extended-data
```

Die zwei neuen Dateien sind zusätzlich explizit in Core aufgenommen und laufen
damit auch in Extended. External wurde nicht ausgeführt. Keine bestehenden
Assertions, Profilgrenzen, Skips oder Schemasnapshots gelockert.

## Ergebnisse

| Prüfung | Ergebnis / Nachweis |
| --- | --- |
| Charakterisierung **vor** Produktivänderung, Pydantic 2.13.4 | 123 passed; /tmp/maint04-before-locked.xml |
| Charakterisierung **vor** Produktivänderung, Pydantic 2.14.1 | 123 passed; /tmp/maint04-before-modern.xml |
| Core auf unverändertem Produktivcode | 199 passed, 7.11s; /tmp/maint04-core-before.xml |
| Erste identische Charakterisierung nach Konsolidierung | 123 passed; /tmp/maint04-after-locked.xml |
| Charakterisierung plus erste isolierte Integrationsgrenzen | 129 passed; /tmp/maint04-regression-locked.xml |
| Finale neue Tests auf unverändertem aafba19-Produktcode, Pydantic 2.13.4 | 151 passed, 3.99s; /tmp/maint04-baseline-final-locked.xml |
| Finale neue Tests auf unverändertem aafba19-Produktcode, Pydantic 2.14.1 | 151 passed, 3.30s; /tmp/maint04-baseline-final-modern.xml |
| Finale neue Tests nach Refactoring, Pydantic 2.14.1 | 151 passed, 2.54s; /tmp/maint04-regression-modern.xml |
| Finales Coreprofil, Pydantic 2.13.4 | 350 passed, 13.29s; /tmp/maint04-core-after.xml; enthält 151 neue Fälle und die bisherigen 199 |
| Synthetische Parser-/Material-/Lecture-/CLIauswahl | 274 passed, 4 skipped, 144.85s; /tmp/maint04-targeted.xml; frühe Auswahl mit 129 der späteren 151 neuen Fälle, kein Addieren zu Core |
| Extended Offline, Pydantic 2.14.1 | **2526 passed, 1 failed, 17 Testskips + 8 Modulskips, 132 deselected**, 2686.38s (44:46), Exit 1; /tmp/maint04-extended.xml |
| Gegenprobe beider Extended-Warnungen auf aafba19 | 2 passed, dieselben 2 warnings, 1.67s; /tmp/maint04-baseline-warnings.xml |
| Ruff 0.16.0 / Format der sieben geänderten Pythondateien | Check bestanden; alle sieben bereits formatiert |

Die spätere Verstärkung desselben eingefrorenen Modelltests um Feldreihenfolge
und exakte Default-JSONbytes lief nach der Extended-Sammlung nochmals in Core
und in den 151er-Gegenproben beider Versionen/Basen. Testanzahl und Produktcode
des Extended-Laufs bleiben gleich; dessen bereits importierte Testfunktionen
enthalten diese zwei zusätzlichen Assertions noch nicht.

Extended wurde **in einem durchgehenden Prozess ohne Unterbrechung** beendet.
Die finale Sammlung selektiert 2544 von 2676 verfügbaren Funktionen; zusätzlich
acht Qdrantmodulskips mangels SDK. JUnit zählt deshalb 2552 Einträge einschließlich
der acht Modulskips. Es gibt **keine Sammlungsausfälle/Setupfehler**. Die 17
Funktionsskips melden ausschließlich `Optional installed SymPy backend unavailable`.
Die 151 neuen Fälle sind vollständig bestanden und nicht übersprungen.
Kein Addieren der überlappenden Core-/Targeted-/Extended-Zahlen.

Einziger Fehlschlag ist der unten konkret gegen `aafba19` nachgewiesene
Workflow-Snapshotkonflikt. Alle bestehenden Prozess-/Cancel-/Resumeprüfungen
dieses Laufs bestehen. Das ist **keine kausale Reparatur** der früher sporadischen
N02-/N03-/N04-Probleme; deren Ursachen bleiben offen. Es wurden keine
Guardian-/SQLite-/Quarantäne-/Hardlinkgrenzen verändert. Extended bleibt wegen
des Schemafehlers ein **rotes Gate**. Es gibt in diesem Lauf keinen nachgewiesenen
neuen MAINT-04-Fehler; die beschriebenen SDK-/Reflexionsgrenzen bleiben bestehen.

Die beiden Warnungen betreffen den absichtlich als String gesetzten fremden
HttpUrl-Wert in
`test_changed_or_ambiguous_overview_rejected[foreign_url]` und den doppelten
ZIPnamen in `test_zip_collisions_counts_bombs_and_sizes[entries0]`.
Beide Warnungen sind mit denselben zwei Nodes auf unverändertem `aafba19`
erneut reproduziert, keine neue MAINT-04-Diagnose.

Bei der Testentwicklung scheiterten zunächst die beiden ChunkSettings-Parameter
an der neu geschriebenen Nullability-Assertion für Literal[de_core_news_sm, None].
Pydantic kodiert das als nullable enum statt anyOf. Die Testassertion wurde vor
jedem Produktivrefactoring korrigiert; die beiden 123er-Vorherläufe sind danach
vollständig grün. Keine Änderung an Produktivvalidierung oder Baselinefixture,
um diese Testfehler zu kaschieren.

Die vier Skips der gezielten Auswahl sind bestehende External-Opt-in-Grenzen:
Original-Python-Notes, zwei Original-PDFparameter und installierte
Providerkonfiguration. Keine dieser Funktionen/Fixtures wurde ausgeführt.
Die Auswahl umfasst die beiden neuen Testdateien sowie
`test_cs50_material_contracts`, `html`, `html_semantics`, `pdf`, `pdf_v2`, `code`,
`processing`, `e2e`, `test_cs50_lecture_runner`, `lecture_adapter`,
`test_cs50_llm_smoke` und `test_dev03_parsing` (jeweils `tests/test_*.py`).

Die zusätzliche Baselinegegenprobe verwendet einen reinen `git archive aafba19`-
Quellsnapshot unter `/tmp/maint04-baseline-rxgdq717`, **kein Gitworktree** und
keinen Checkout eines fremden Branches. Nur die drei neuen Test-/Supportdateien
und zwei synthetischen Fixtures wurden darübergelegt; der gesamte Produktcode
bleibt bytegleich zur Basis. So sind auch die später ergänzten Pickle-/Output-
Grenztests gegen den ursprünglichen Vertrag geprüft. Keine Produktivänderung
wurde zur Fehlerreproduktion zurückgesetzt.

Ein ASTvergleich der beiden Originalmodule mit `git show aafba19:<Pfad>` bestätigt
erneut 21 gemeinsame Namen, 19 identische Klassendeklarationen und genau die zwei
bekannten Abweichungen. Nach Refactoring ändern sich in jedem Modul ausschließlich
die zehn vorgesehenen nichtleeren gemeinsamen Felddeklarationen; sämtliche
anderen Klassen und Funktionen, insbesondere beide abweichenden Modellvarianten,
behalten ihre ASTs. Die MAINT-03-Fixes, MAINT-03B-Guards/Isolation und vorhandenen
Workflow-Snapshots sind unverändert.

## Konkreter Schema-Basisvergleich

`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models`
scheitert auf unverändertem `aafba19` erneut: **1 failed, 3.22s**, kein Skip
(`/tmp/maint04-baseline-schema.xml`). Ein rekursiver Schemaabgleich liefert im
Originalsnapshot und im MAINT-04-Worktree **bytegleich dieselben vier Differenzen**:
je `WorkflowInspection` und `WorkflowRunReport` in
`docs/job_control/contract.v1.json` und `docs/workflows/contract.v1.json`, jeweils
`/$defs/Workflow/properties/course_id/enum` mit zusätzlichem
`loviscach_mathe_1` im aktuellen Modell. Keine anderen Schemaänderungen in diesem
Abgleich. Belege: `/tmp/maint04-schema-baseline.json` und
`/tmp/maint04-schema-current.json`. Damit ist diese Abweichung als bestehender
Vertragskonflikt nachgewiesen; sie wurde weder gelöst noch als neue
Parsingregression umgedeutet.

## Patch und Erhalt

`/tmp/maint04-review.patch` enthält ausschließlich die 15 beabsichtigten Dateien:
`.gitignore`, Profilrunner, die zwei öffentlichen Settingsmodule, das neue
private Feldmodul, drei Test-/Supportdateien, zwei synthetische JSONfixtures
und die fünf angeforderten MAINT-04-Berichte. Die zwei exakten neuen
gitignore-Ausnahmen machen nur die synthetischen Fixtures sichtbar.
Keine bestehenden Schemafixtures oder Konfigurationsdateien wurden ersetzt.

Die Prüfung verwendet `git apply --reverse --check` gegen den aktuellen
Arbeitsbaum sowie Vorwärts-Check und tatsächliche Anwendung in einem frischen
`git archive aafba19`-Quellsnapshot unter `/tmp/maint04-patch-verify-*`.
Anschließend werden **alle 15 Dateiinhalte byteweise und per SHA-256** mit dem
beabsichtigten Worktree verglichen. `/tmp/maint04-delivery.json` enthält die
exakte Basis, Dateiliste, Hashes, Patchhash und den verifizierten Snapshotpfad.
Das ist eine Patchprüfung ohne Index-/Refänderung, kein Commit-/PRnachweis.
Der Ablauf wurde nach den letzten Dokumentergänzungen erneut vollständig
durchgeführt und bestanden. Die drei lokalen Heads MAINT-04, master und
origin/master bleiben auf den oben dokumentierten Eingangswerten.

Temporäre Logs, JUnitberichte, Quell-/Patchtestsnapshots und ausschließlich
synthetische Extended-Testdaten unter `/tmp/maint04-*` bleiben als Arbeitsbelege
erhalten. Im zugewiesenen Worktree sind außerdem ignorierte `.ruff_cache`- und
`__pycache__`-Verzeichnisse sichtbar; sie gehören nicht in den Patch und werden
nicht bereinigt. Die fachlichen Testartefakte liegen in eigenen Tempwurzeln.
Dauerhafte Ergebnisse liegen in den fünf Berichten und dem vorgesehenen
Code-/Testpaket; Defaultbranchintegration und spätere erlaubte Veröffentlichung
bleiben offen. Keine fremden/alten Branches, Worktrees, Stashes oder Daten entfernt.

Die Baselinefixture enthält 42 modellbezogene Verträge einschließlich beider
Schematypen. Nicht nur Quelltext oder Feldanzahl wurde verglichen. Die 19
strukturellen Duplikate bleiben nominal verschieden. Unterschiede der beiden
PDF- und ParseSettings-Verträge sind absichtlich erhalten. Vollständige Befunde
stehen in [Inventar](maint04_configuration_inventory.md) und
[Kompatibilitätsmatrix](maint04_compatibility_matrix.md).

## Grenzen und Folgearbeit

Legacy-Env-/SDKvollimporte und echte DOCX-/Docling-/DIY-/Bildpipelines sind mit
den vorhandenen optionalen Paketen nicht ausführbar. Die isolierten Tests
kompilieren echte Klassendeklarationen/Funktionskörper mit ausdrücklich
injizierten SDK-/Laufzeitgrenzen; sie behaupten keine Vollintegration dieser
Module. Moderne Materialparser werden separat mit echten synthetischen
HTML-/PDF-/Codefixtures geprüft. Private historische Konfigurationen und
externe dynamische Erweiterungen bleiben ungeprüft.

Der bekannte Workflow-Snapshotfehler und die in MAINT-03B beschriebenen
Guardian-/SQLite-/Isolationsprobleme werden nicht durch neue xfails verdeckt.
Jeder jetzt auftretende Fehler benötigt einen konkreten Vergleich mit
unverändertem `aafba19`; Einzelpässe widerlegen keine sporadischen Breitfehler.
Keine pauschale Behauptung, Extended oder C26 seien grün.

Konkretes MAINT-05: unabhängiger Workflowkurs-/Schemaentscheid; schlankes echtes
Legacy-/DOCX-/SDKprofil und expliziter versionierter Loader mit Herkunftsvertrag;
getrennte phasenbezogene Prozess-/Publikationsdiagnostik ohne automatische
Bereinigung. Migrationsschritte und Datenverlustgrenzen siehe
[Migrationsguide](maint04_migration_guide.md).
