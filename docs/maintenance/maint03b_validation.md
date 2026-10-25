# MAINT-03B – Validierung und ausstehende Integration

25.10.2026. Entwicklungs-/QA-Ergebnis. **Produktionsstatus HOLD.**
Keine Produktionsfreigabe und keine vollständige grüne Gesamtsuite.

## Arbeitsstand und Erhalt

Der anfänglich saubere, bereits zugewiesene Worktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03b` steht auf
`audit/maint03b-test-stabilization`, Commit
`6b397eb4576bac93b318d0e1b8e954d16cb5e08e` (MAINT-03).
Im gemeinsamen Projektgit wurden keine zusätzlichen Branches oder Worktrees angelegt. Vergleichsbasis
ist Parent `e68275205fefb7a5f6db42bc45060e505bfcefb5`; `origin/master` zeigt beim
lokalen Eingang auf diesen Stand, der lokale Branch `master` ist veraltet
(`c1007ef`). Dies ist kein frischer Live-/Remoteintegrationsnachweis.

AGENTS.md und alle fünf MAINT-03-Berichte wurden zuerst gelesen. Die drei
MAINT-03-Src-Dateien, beide 34-Fälle-Testdateien und die fünf Berichte bleiben
bytegleich zur Basis. Änderungen betreffen QA, Profile und ausschließlich die
nachgewiesene unnötige Sessionkopplung in `scripts/cs50_llm_smoke.py`.
Kein C26-/C27-Branch oder fremder Worktree wurde bearbeitet.

## Interpreter und Voraussetzungen

| Bezeichnung | Tatsächlicher Pfad / Versionen | Verwendung |
| --- | --- | --- |
| `MAINT_PYTHON` | `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`; Python 3.12.12, pytest 9.1.1, Pydantic 2.14.1, HTTPX 0.28.1, BeautifulSoup 4.15.0, PyMuPDF 1.27.2.2 | Master-/MAINT-03-Vergleich, Coregegenprobe, Extended, Einzel-/Reihenfolge-/Crashprobes |
| `CORE_PYTHON` | `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python`; Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4/Core 2.46.4, HTTPX 0.28.1, dotenv 1.2.3, PyYAML 6.0.3, Tenacity 9.1.4, Typer 0.26.8 | Minimaler Corelauf und unabhängiger Schemavergleich mit Repository-Lockversionen |
| `MAINT_RUFF` | `/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff`; 0.16.0 | Geänderte Pythondateien |

Vorhandene Interpreter/Caches wurden nur lesend verwendet. Der Coreinterpreter
enthält weder BeautifulSoup, PyMuPDF noch Qdrant; der MAINT-03-Interpreter enthält
kein Qdrant/tiktoken. Keine SDK-/Modellinstallation oder Dienstinitialisierung.
Der vorhandene Coreinterpreter enthält 44 installierte Distributionen einschließlich
Entwicklertools. Ein zusätzlicher eigener `venv --without-pip`-Snapshot unter
`/tmp/maint03b-minimal-core-xapl1c86` enthält ausschließlich die 25 für diese
Plattform gelockten Root-/test-core-Distributionen, kopiert aus dieser vorhandenen
Umgebung; Consolewrapper und Bytecodecaches wurden nicht übernommen. Dort besteht
Core ebenfalls vollständig. Das prüft minimale Importabhängigkeiten, ersetzt
aber keine Installation frisch verifizierter Wheels. `uv pip check` auf der
vorhandenen Coreumgebung: 44 Pakete kompatibel; auf der isolierten
Corekopie: genau 25 Pakete, ebenfalls vollständig kompatibel.
Tests erzeugen ausschließlich lokale temporäre synthetische Daten, eigene
SQLite-/FTS-Testdatenbanken und die bestehenden isolierten Git-Audit-Fixturerepositories. Keine produktiven Datenbankaktionen.

## Ausgeführte Prüfungen

| Prüfung | Passed | Failed | Skipped | Sammlungsausfälle | Einordnung |
| --- | ---: | ---: | ---: | ---: | --- |
| Originale elf Fälle auf Mastersnapshot, erneut | 6 | 5 | 0 | 0 | 33,68 s; drei Qdrant-, Smoke- und Schemafehler |
| Originale elf Fälle auf MAINT-03 vor Änderungen, erneut | 5 | 6 | 0 | 0 | 36,63 s; zusätzlich zufällige Retryauswahl |
| Masterprobe umask 0077 | 0 | 1 | 0 | 0 | Absichtliche Zustandsreproduktion |
| Masterprobe Executor vor drei SRT-/Evaluatorfällen | 1 | 3 | 0 | 0 | Nachweis der alten Klassenidentitätsdrift |
| MAINT-03-Regressionen, separat | **34** | **0** | **0** | **0** | 1,29 s; unveränderte beiden Testdateien |
| Core, isolierter Snapshot von 25 Lockdistributionen | **199** | **0** | **0** | **0** | 4,95 s nach finaler SDK-Opt-in-Negativprüfung; enthält die 34, nicht addieren |
| Core, vorhandener Lockversionsinterpreter inklusive Entwicklertools | 199 | 0 | 0 | 0 | 3,75 s |
| Core, MAINT-03-Interpreter | 199 | 0 | 0 | 0 | 15,08 s; unabhängige Versionsgegenprobe |
| Isolation + gesamte Reimportdatei + Smoke | **44** | **0** | **1** | **0** | 135,00 s; expliziter Provider-SDKfall ausgeschlossen |
| Ursprüngliche Fehlergruppe nach Korrektur | **7** | **1** | **1 Modul** | **0** | 47,03 s; Schema bleibt rot; drei Qdrantparameter nicht ausgeführt |
| Gesamte Sammlung nach letzter Markerregression | — | — | 8 Module | **0** | 2.525 Funktionen; Core 199, Extended 2.393, External 132; SDKfälle nicht sammelbar |
| Erster vollständiger breiter Lauf, Profilzuordnung noch fehlerhaft | 2373 | 47 | 25 | 0 | 2560,59 s; 45 verbotene native Composeaufrufe vom Guard blockiert; 87 Externalfälle abgewählt |
| Extended Offline, fortgesetzte Auswahl vor letzter Markerfixturekorrektur | **2371** | **4** | **17 Fälle + 8 Module** | **0** | 2.392 ausgewählte Funktionen über drei Prozesse, 132 Externalfälle abgewählt; kein vollständiger durchgehender Endlauf |
| PDF-/Workflowdateien nach Markerfixturekorrektur + neue Markerregression | **62** | **1** | **0** | **0** | 218,17 s, Exit 1; ausschließlich der bekannte Schemasnapshot rot |
| External Integration, nur Sammlung | 0 ausgeführt | — | 8 Qdrantmodule bei Sammlung | 0 | Abschließend 132/2.525 Funktionen ausgewählt, 2.393 abgewählt; keine Ausführungsstatistik |

Der absichtliche verschachtelte Setupfehler im Umasknegativtest wird von dessen
äußerer Assertion geprüft; er ist kein Fehler des oben bestandenen 44er-Laufs.
Die neue Smokeimport-Sperre wurde zusätzlich separat auf dem finalen Teststand
geprüft: **8 passed / 0 failed / 1 SDKskip**, 1,91 s. Die Vorbereitung blockiert
Session-, Envsettings- und tiktoken-Imports nun unabhängig vom Installationsstand.
Es gibt keine nachträgliche Addition überlappender Testzahlen.

Zwei unvollständige breite Vorläufe wurden vor Abschluss beendet (je Exit 130): zuerst nach
Ergänzung weiterer Original-/Privilegfälle zu External, anschließend nach Nachweis
von Umaskänderungen direkt aufgerufener CLI-Einstiege. Beide werden weder als
erfolgreich noch als vollständiges Gate gezählt. Ein anschließender vollständiger Lauf ergab 47 Fehler;
deren 45 nativen HTTPS-/Composefälle waren noch falsch dem Offlineprofil
zugeordnet. Die danach fortgesetzte Auswahl verwendet die korrigierte
Externalzuordnung, globale Umaskrestauration und eigene erhaltene Basetempwurzeln.
Spätere Benutzerunterbrechungen wurden durch Ausführen ausschließlich der noch
offenen Nodes aufgefangen; die Beleggrenzen stehen unten.
Die finalen CLI-/Isolationsdateien bestanden zuvor mit **58 passed / 3 Externalskips**,
42,79 s; eine bestehende Pydantic-Serializerwarnung aus der absichtlich manipulierten
Foreign-URL-Negativfixture blieb sichtbar. Keine echte Deploymentoperation.
Der reale CLI-/Folgetestprobe mit synthetischem Preflight ergab auf Master
**1 passed / 1 failed**, nach Korrektur **2 passed**.

Weitere Probes: deterministischer Publikationsabbruch auf Master und MAINT-03B
(Exit 73, zwei Links, gleiche Inode-/Bytewerte, echte Backupablehnung), normaler
Exceptionpfad ohne verbleibenden Alias, eigener Root versus synthetisch falsche
UID, identische vier Schemadifferenzen unter Pydantic 2.13.4 und 2.14.1.
Die entsprechenden acht anfänglichen Isolationstests enthalten zwei Umaskwerte,
einen Setupfehler, einen CLI-artigen Fehler im Testkörper, zwei Producer-/
Consumerreihenfolgen und zwei Publikationspfade. Der neunte Test sichert die
zuletzt nachgewiesene atomare PDF-PID-Markerpublikation ab.

## Vergleich mit MAINT-03

| Kennzahl | MAINT-03 | MAINT-03B |
| --- | --- | --- |
| Legacyregressionen | 34 bestanden | 34 bestanden, unverändert |
| Sammlung | 2.508 Fälle plus 7 Fehler | 2.525 Funktionen und 8 ausdrücklich optionale Modulskips, keine Sammlungsausfälle |
| Breiter Offlineumfang | 2.347 passed, 11 failed, 36 skipped; 11 Dateien ignoriert | Fortgesetzt 2.371 passed, 4 failed, 25 skipped bei 2.392 ausgewählten Funktionen; letzte Markeränderung anschließend gezielt geprüft, keine grüne Gesamtsuite |
| Core mit minimalen Abhängigkeiten | Kein eigenständiges Profil | 199 bestanden, keine Fehler/Skips |
| Qdrant | 7 Collection-Errors und 3 Ausführungsfehler | Explizite acht Modulgrenzen; lokale SDKtests weiterhin funktional ungeprüft |
| Umask-/Cache-/Retryannahmen | Reproduzierte instabile Tests | Gezielt repariert; negative Setup-/Reihenfolge-/Identitätsprüfungen |
| Publikationscrash | Dokumentierter offener R19 | Deterministische Regression charakterisiert Fail-closed, Recovery weiterhin offen |
| Workflow-Snapshot | Auf Master fehlgeschlagen | Weiter sichtbar fehlgeschlagen; Ursache fachlich eingegrenzt, Snapshot unverändert |

Umfangsdifferenzen sind keine reine Leistungssteigerungsmetrik: Extended nimmt
insbesondere die listenerfreien Fälle der zuvor vollständig ausgeschlossenen
Search-HTTP-Datei auf, verschiebt explizite SDK-/Original-/native Toolfälle nach
External und ergänzt neue Negativtests. Die Ergebnisse sind deshalb nicht als
identische Fallmengen voneinander abzuziehen.

## Reproduzierbare Befehle

Profildefinition und uv-Vorbereitung: [Testprofile](maint03b_test_profiles.md).
Die tatsächlichen Interpreter sind oben vollständig benannt.

```bash
PYTHONDONTWRITEBYTECODE=1 "$CORE_PYTHON" scripts/test_profiles.py core \
  --junitxml=/tmp/maint03b-core-minimal.xml
MAINT_TEST_BASE=$(mktemp -d /tmp/maint03b-extended.XXXXXX)
PYTHONDONTWRITEBYTECODE=1 "$MAINT_PYTHON" scripts/test_profiles.py extended \
  --junitxml=/tmp/maint03b-final-profile.xml --durations=12 \
  --basetemp="$MAINT_TEST_BASE"

PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard tests/test_legacy_io_regressions.py tests/test_legacy_retry.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard tests/test_maint03b_isolation.py \
  tests/test_content_store_reimport.py tests/test_cs50_llm_smoke.py

PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard --collect-only tests
PYTHONDONTWRITEBYTECODE=1 "$MAINT_PYTHON" scripts/test_profiles.py external \
  --run-external --collect-only
```

Für den unveränderten Mastervergleich wurde `git archive e682752...` nach
`/tmp/maint03b-baseline-7nzrqk27` entpackt. Die elf vollständigen Nodes stehen in
der [Fallmatrix](maint03b_failure_analysis.md). Beide Vorherläufe verwendeten
identischen Interpreter, deaktivierte Plugins/Caches und den unveränderten
MAINT-03-Offlineguard. Für die Nachhergruppe wird der alte Retrynode auf
`[raw-False]` abgebildet und die Qdrantdatei als Modul ausgewählt. Dies erklärt
die unterschiedliche Zählweise, ohne ursprüngliche Fehler verschwinden zu lassen.

## Ruff, Lock und Integrität

Ruff Check und Ruff Format --check für sämtliche 31 geänderten Pythondateien
sowie deren Python-3.12-ASTprüfung bestehen. `git diff --check` besteht; alle vier
Berichte sind UTF-8/LF ohne abschließende Leerzeichen, sämtliche relativen Links
auf vorhandene Dateien geprüft. Kein Gesamtrepository-Lintgrün behauptet; die
329 ursprünglichen Ruffbefunde sind außerhalb des Auftrags.

`uv export --frozen --offline` war für alle drei Gruppen erfolgreich:
26/29/39 plattformübergreifende Requirementzeilen für Core/Offline/Qdrant, keine
Torch-/spaCy-/Docling-/SentenceTransformer-/Modellpakete. Alle bestehenden
Paketversionen, Quellen, Dependencyedges, Wheel-/Hashwerte und Root-
Runtimeanforderungen wurden strukturiert gegen HEAD verglichen: unverändert.
Nur Gruppenzuordnung/-Requirements wurden ergänzt; keine freie Lockneuberechnung.
Zusätzlich wurden include-group-Expansion, Lockrequirements, direkte Paketnamen
und Versionsconstraints für alle drei Gruppen strukturiert gegengeprüft: konsistent.

`uv lock --check --offline` blieb wegen nicht verfügbarer Metadaten des bereits
bestehenden Direkt-URL-spaCy-Modells blockiert. Ein eigener minimaler Syncversuch
unter `/tmp/maint03b-core-env` scheiterte vor erfolgreicher Installation am
fehlenden `pydantic-core==2.46.4`-Wheel. Die vorhandene passende Coreumgebung wurde
anschließend ausschließlich lesend verwendet. Es wurde kein Cachefehler durch
Netzwerk-/Modellinstallation umgangen.

## Gitgrenze, Patch und notwendiger Erhalt

`git add --dry-run AGENTS.md` scheiterte bereits mit
`Unable to create .../Personal_Assistant-maint03b/index.lock: Read-only file system`.
Die gemeinsame Gitdatenbank liegt außerhalb des schreibbaren Bereichs.
**Kein lokaler Commit, kein Push, kein neuer Draft-PR.** Es wurde kein alternativer
Remote-Schreibweg zur Umgehung dieser Grenze versucht; bestehende Drafts bleiben
unverändert. Keine Merges oder Force-Pushes.

Der überprüfbare Patch `/tmp/maint03b-review.patch` sichert sämtliche 37
beabsichtigten Dateien einschließlich neuer Dateien und aller vier Berichte.
Reverse-Check gegen den Arbeitsbaum und Forward-Check gegen einen unveränderten
`git archive HEAD`-Snapshot unter `/tmp/maint03b-patch-base-rvy523qs` bestehen.
Die lokalen Referenzen, Worktreeeinträge und Stashes sind gegenüber dem
Eingangssnapshot exakt unverändert; kein frischer Live-Remotezustand behauptet.
Temporäre Logs/JUnit-/Probedaten liegen unter `/tmp/maint03b-*`; die wesentlichen dauerhaften Befunde stehen
in diesen vier Berichten. Patchsicherung ersetzt keinen Commit oder Review.

Die AGENTS.md-Anforderung, dauerhafte Berichte in der tatsächlichen Defaultbranch
`master` verfügbar zu machen, bleibt wegen Schreibgrenze und ausdrücklichem
Mergeverbot **ausstehend**. Ebenso ist keine Liveintegration verifiziert. Der
vorbestehende zugewiesene Branch und Worktree müssen erhalten bleiben; keine
Cleanupfreigabe oder integrierter Repositoryabschluss wird behauptet.
Es wurden keine Gitobjekte, fremden Branches/Worktrees, Stashes, Venvs,
unbekannten Daten, Originalmaterialien oder produktiven Artefakte gelöscht.

## Vollständige Änderungsliste

37 Dateien, davon 31 Pythondateien. Kein Src-Modul aus MAINT-03 geändert.

| Datei | Zweck |
| --- | --- |
| `docs/maintenance/maint03b_failure_analysis.md` | Dauerhafter MAINT-03B-Bericht. |
| `docs/maintenance/maint03b_remaining_risks.md` | Dauerhafter MAINT-03B-Bericht. |
| `docs/maintenance/maint03b_test_profiles.md` | Dauerhafter MAINT-03B-Bericht. |
| `docs/maintenance/maint03b_validation.md` | Dauerhafter MAINT-03B-Bericht. |
| `pyproject.toml` | Drei schlanke Testgruppen und registrierter Externalmarker. |
| `scripts/cs50_llm_smoke.py` | AppSession erst im API-Pfad initialisieren. |
| `scripts/test_profiles.py` | Reproduzierbare Core-/Extended-/External-CLI. |
| `tests/conftest.py` | Pro Test Umaskzustand sichern, private Umaskfixture und Profilpolicy laden. |
| `tests/helpers/pdf_lifecycle_probe.py` | PDF-/Guardian-PID-Marker ausschließlich im Testprobe atomar veröffentlichen. |
| `tests/offline_guard.py` | Netz-/Listener- und Infrastrukturassertions für Offlineprofile. |
| `tests/optional_dependencies.py` | Nur fehlendes Top-Level-Qdrant-SDK als optional überspringen. |
| `tests/profile_policy.py` | Externalfälle zentral und vor Fixtures an ausdrückliches Opt-in binden. |
| `tests/qdrant_support.py` | Gemeinsamer SDKzugang für die acht optionalen Testmodule. |
| `tests/test_content_store_artifacts.py` | Tatsächlichen Negativmodus und reale Ownership prüfen. |
| `tests/test_content_store_reimport.py` | Retry über Identität auswählen; beide Listenrichtungen prüfen. |
| `tests/test_cs50_batch_worker.py` | Privaten Umaskzustand an restaurierende Fixture binden. |
| `tests/test_cs50_code_zip.py` | Privaten Umaskzustand an restaurierende Fixture binden. |
| `tests/test_cs50_executor.py` | Partielle globale Modulcachepurges entfernen. |
| `tests/test_cs50_index_cli.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_index_contract.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_index_end_to_end.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_ingestion.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_knowledge_index_checkpoint.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_knowledge_index_mapping.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_knowledge_input.py` | Partielle globale Modulcachepurges entfernen. |
| `tests/test_cs50_knowledge_pilot.py` | Partielle globale Modulcachepurges entfernen. |
| `tests/test_cs50_lecture_adapter.py` | Partielle globale Modulcachepurges entfernen. |
| `tests/test_cs50_llm_smoke.py` | Session-/Settings-/Tokenizerimports während Offlinevorbereitung sperren. |
| `tests/test_cs50_media_plan.py` | Privaten Umaskzustand an restaurierende Fixture binden. |
| `tests/test_cs50_multiformat.py` | Privaten Umaskzustand an restaurierende Fixture binden. |
| `tests/test_cs50_pilot.py` | Privaten Umaskzustand an restaurierende Fixture binden. |
| `tests/test_cs50_retrieval.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_cs50_retrieval_evaluation.py` | Explizite optionale Qdrant-Sammlungsgrenze. |
| `tests/test_maint03b_isolation.py` | Neun Prozess-/Umask-/Identitäts-/Publikations-/PID-Markernegativtests. |
| `tests/test_maint03b_profiles.py` | Neun Profil-/SDK-/Toolgrenzen inklusive echter Fixture-Skipprobe. |
| `tests/test_runtime_paths.py` | Umaskzustand restaurieren. |
| `uv.lock` | Ausschließlich Gruppenzuordnung zu bestehenden Paketen/Requirements. |


## Zusätzlicher vollständiger Lauf und Reproduktionsgrenzen

Der vollständige Lauf mit noch unvollständiger Profilabgrenzung meldete
**2373 passed / 47 failed / 25 skipped / 87 deselected**, 2 Warnungen, 2560,59 s.
45 Fehler waren vom Offlineguard abgefangene native HTTPS-/Composeaufrufe;
die Datei ist jetzt External. Die übrigen Fehler sind der bekannte Schemasnapshot
und der zusätzliche Quarantäne-/Resumefall N02. Siehe
[vollständige Ursachenabgrenzung](maint03b_failure_analysis.md).

Die ursprüngliche N02-Testwurzel war nach Ende des Laufs bei weiterer Diagnose
nicht mehr verfügbar; die Pytest-Standardretention wird nicht als Aufbewahrung
von Fehlerartefakten vorausgesetzt. Die fortgesetzten breiten Segmente verwenden
deshalb eigene leere Taskpfade per `--basetemp`, unten dokumentiert.
Es wurde keine Quarantäne manuell entfernt oder adoptiert.

N02-Einzelvergleich: MAINT-03B **1 passed, 14,57 s**; unveränderter Master
**1 passed, 12,48 s**. Keine Skips, keine behauptete Ursachenreparatur.


## Fortsetzung ohne Wiederholung abgeschlossener Fälle

Die abschließende breite Auswahl wurde durch Benutzerunterbrechungen aufgeteilt.
Das ist **kein einzelner vollständig beendeter Profillauf** und kein Nachweis
beliebiger prozessübergreifender Reihenfolgeunabhängigkeit:

| Segment | Ausgeführte Funktionen | Passed | Failed | Testskips | Beleg |
| --- | ---: | ---: | ---: | ---: | --- |
| Korrigierter Lauf vor Unterbrechung | 1822 | 1821 | 1 | 0 | Vollständige Fortschrittszeichen, mit unveränderter sequentieller Sammlung abgeglichen; kein finaler JUnitreport |
| Erste Fortsetzung vor Unterbrechung | 43 | 43 | 0 | 0 | Exakt 43 Punkte im Log; nur die ursprünglichen offenen Nodes |
| Letzte Fortsetzung | 527 | 507 | 3 | 17 | Vollständiger JUnitreport; 317,63 s, Exit 1 |
| Summe der disjunkten Auswahl | **2392** | **2371** | **4** | **17** | Jede ausgewählte Funktion genau einmal; zusätzlich 8 SDKmodulskips aus der Sammlung |

Nodefolge und Überschneidungsfreiheit wurden maschinell gegen die ursprüngliche
Sammlung geprüft. Spätere Einzelpässe ersetzen keine historischen Fehler.
Belegdateien: `/tmp/maint03b-final-profile.log`,
`/tmp/maint03b-resume-rest.log`, `/tmp/maint03b-final-rest.xml`,
`/tmp/maint03b-final-resume-evidence.json`,
`/tmp/maint03b-aggregate-results.json` und
`/tmp/maint03b-resume-collection.log`. Für das erste unterbrochene Segment fehlen
abschließender Traceback und Exitcode; die N03-Daten wurden zusätzlich gesichert.
Die drei expliziten Basetempwurzeln bleiben erhalten:

- `/tmp/maint03b-final-profile-data-0xn86wha`
- `/tmp/maint03b-resume-rest-y1wj2gdo`
- `/tmp/maint03b-final-rest-yfd0crl4`

Vier Fehler: bekannter Schemasnapshot, N03 Cancel-/Resume mit OperationalError,
N04 fehlender PDF-PID-Marker und N05 leerer JSONmarker. N02 trat in der letzten
Auswahl nicht erneut auf. Details und Sicherheitsgrenzen stehen in der Fallanalyse.
N03s SQLitekopie belegt Quarantäne, N04s SQLitekopie belegt einen bereits vor der
geplanten Adapter-SIGKILL-Injektion mit Exit 3 beendeten Job; beide tieferen
Ursachen bleiben offen. Keine Testassertion oder Sicherheitsgrenze entfernt.

Vor der abschließenden Markeränderung wurden die drei neuen Prozessfehler
jeweils in einem eigenen Prozess mit dem gleichen Offlineguard wiederholt:

| Node-Kürzel | MAINT-03B einzeln | Unveränderter Master einzeln |
| --- | --- | --- |
| N03 Cancel-/Resume | 1 passed, 7,99 s | 1 passed, 8,79 s |
| N04 PDF adapter-exit | 1 passed, 3,10 s | 1 passed, 4,98 s |
| N05 PDF-Workflow cancel | 1 passed, 11,37 s | 1 passed, 7,60 s |

Kein Sammelfehler/Skip in diesen sechs Probes. Einzelpässe belegen keine
Reparatur von N03/N04. Die zusätzliche deterministische Markerprobe dagegen
scheitert auf unverändertem Master und MAINT-03B vor Fix mit identischer
Assertion: `PID marker visible before JSON is complete`. Die beobachtete
leere Datei wird damit ohne Zufall reproduziert. Anschließend veröffentlicht nur
der Testhelper PDF-/Guardian-Marker durch temporäre Datei und Rename.

Die letzte Markerregression ergänzt genau **eine** Extended-Funktion; die finale
Sammlung umfasst daher 2.525 verfügbare Funktionen, davon 2.393 Extended und
132 External, zusätzlich 8 fehlende Qdrantmodule. Der 2.392er-Breitnachweis gehört
zum Stand unmittelbar vor dieser letzten Testfixturekorrektur. Danach wurden
nur die betroffenen drei PDF-/Workflowdateien und der neue Negativtest ausgeführt;
kein weiterer gesamter Breitlauf und kein Umdeuten des roten Gates.


Der letzte gezielte Nachlauf ergibt **62 passed / 1 failed / 0 skipped /
0 Sammlungsausfälle**, 218,17 s. Er enthält die neue deterministische
Markerregression, alle Fälle aus `tests/test_pdf_job_control.py`,
`tests/test_pdf_workflows.py` und `tests/test_workflow_http.py`, einschließlich
N04, N05 und N02. Einziger Fehler ist der unveränderte Schemasnapshot. N03 wurde
vor der Markeränderung separat mit eigenem Prozess auf beiden Ständen erfolgreich
geprüft; dessen Guardian-/SQLiteursache bleibt offen. Protokolle:
`/tmp/maint03b-pdf-final.log`, `/tmp/maint03b-pdf-final.xml` und
`/tmp/maint03b-new-failure-probes.json`. Nachher-Pässe werden nicht aus den vier
breiten Fehlschlägen herausgerechnet.

Reproduktion dieses begrenzten letzten Nachlaufs:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard \
  tests/test_maint03b_isolation.py::test_pdf_pid_marker_is_invisible_until_json_is_complete \
  tests/test_pdf_job_control.py tests/test_pdf_workflows.py tests/test_workflow_http.py \
  --junitxml=/tmp/maint03b-pdf-final.xml
```

Die finale reine External-Sammlung ist unter
`/tmp/maint03b-external-final-collection.log` gesichert: 132/2.525 verfügbare
Funktionen ausgewählt, 2.393 abgewählt, 8 optionale Qdrantmodulskips,
0 Sammlungsausfälle. Keine Externalfixtures oder -tests ausgeführt.

**Abnahmestand:** Alle elf ursprünglichen Fälle klassifiziert, Testprofile und
sicher nachgewiesene Isolation-/Fixturekorrekturen implementiert, Legacy34 und
Core199 bestanden. Extended bleibt rot; fachlicher Snapshotreview und die
ungeklärten Prozessfehler bleiben ausdrücklich offen. Dokumentation, Patch und
Worktree sind erhalten; Git-/Defaultbranchintegration bleibt ausstehend und
Produktionsstatus HOLD.
