# MAINT-03B – Reproduzierbare Testprofile

25.10.2026. Produktionsstatus **HOLD**. Dies sind Entwicklungs-/QA-Gates.
Ergebniszahlen und tatsächliche Interpreter: [Validierung](maint03b_validation.md).
Ein Offlineerfolg ersetzt keine Produktions-, Image-, Browser- oder Modellabnahme.

## Auswahl und CLI

`scripts/test_profiles.py` startet einen neuen Pytestprozess mit dem aufrufenden
Interpreter, festem Repository-CWD, deaktivierten Autoloadplugins und Cachewrites
sowie `HF_HUB_OFFLINE=1` und `TRANSFORMERS_OFFLINE=1`. Es installiert nichts.
Zusätzliche Argumente sind für selbstständige Reportingflags vorgesehen, etwa
`--junitxml=/tmp/core.xml`, `--durations=12` oder `--collect-only`.
Testpfade, Marker-/Pluginauswahl und Ausschlüsse werden vom Profil bestimmt.

```bash
# In einer bereits vorbereiteten passenden Umgebung:
python scripts/test_profiles.py core --junitxml=/tmp/pa-core.xml
python scripts/test_profiles.py extended --junitxml=/tmp/pa-extended.xml

# Nur die Auswahl ansehen; keine Fixtures/Tests und keine Dienste starten:
python scripts/test_profiles.py external --run-external --collect-only

# Ausschließlich nach gesonderter Erlaubnis für die gewählte Testumgebung:
python scripts/test_profiles.py external --run-external --junitxml=/tmp/pa-external.xml
```

Der letzte Befehl ist **in diesem Auftrag nicht ausgeführt**. Ohne
`--run-external` verweigert der Runner das Externalprofil. Auch gewöhnliches
`pytest tests` überspringt die explizit zugeordneten externen Fälle vor deren
Fixtures; die zentrale Zuordnung steht in `tests/profile_policy.py`.
Fehlende Voraussetzungen bereits ausgewählter Tests werden weiterhin von deren
konkreten Assertions/Dependencyregeln behandelt. Ein Marker ist keine Zusicherung,
dass sämtliche externen Dienste oder SDKs bereitstehen.

## Überprüfbare Gatebedingungen

| Profil | Bestehenskriterium | Bewertung dieses Auftrags |
| --- | --- | --- |
| Core | Pytest-Exit 0, keine Fehlschläge, Setup-/Sammlungsausfälle oder Skips; alle fest ausgewählten Corefälle ausgeführt | Bestanden |
| Extended Offline | Pytest-Exit 0, keine Fehlschläge/Setup-/Sammlungsausfälle; ausschließlich benannte optionale SDK-/Backendskips zulässig | Nicht bestanden; Schemaabweichung und ungeklärte Prozessfehler bleiben sichtbar |
| External Integration | Nur nach ausdrücklichem Opt-in und bereitgestellten Voraussetzungen; tatsächlich ausgeführte Fälle ohne Fehler, fehlende Teilprofile separat ausweisen | Nicht ausgeführt; keine Freigabe ableitbar |

Ein Exitcode 1 wird nicht wegen bekannter Fehler als erfolgreich umgedeutet.
Sammlungsfehler sind keine Skips. External-Deselektion, optionale Modulskips und
übersprungene einzelne Testfälle werden getrennt ausgewiesen. Die bekannten
Bestands-/Vertragsfehler erhalten kein xfail und keine Gateausnahme.

## Dependency-Gruppen ohne große Modellprofile

| uv-Gruppe | Zusätzliche Pakete zur Rootanwendung | Zweck |
| --- | --- | --- |
| `test-core` | pytest | Kleine DTO-, Modell-, Provenienz-, Retry-, IO- und Profiltests |
| `test-offline` | test-core, beautifulsoup4, PyMuPDF | Synthetisches HTML/PDF/Code, Content/SQLite/FTS, Jobs, Worker, Workflows, Evaluation |
| `test-qdrant` | test-offline, qdrant-client | Optionale lokale Qdrantpersistenz mit synthetischen Vektoren; kein Qdrantserver oder Embeddingmodell nötig |
| Bestehende Extras `lecture-worker`, `llm` | Große/optionale Parser-, Media-, LLM- und Settingsprofile | Nur gezielte External-/SDKsmokes; nicht für Core/Extended installieren |
| Bestehendes Extra `rag` | Unter anderem Chroma und Embeddingmodelle | Für die lokalen Qdranttests unnötig; nicht als Ersatz für test-qdrant verwenden |

`test-qdrant` stellt ein **ausdrücklich aktiviertes SDK-Teilprofil von External
Integration** bereit. Diese acht Dateien verwenden lokale synthetische Daten
und benötigen keinen Server oder Modelle; sie laufen trotzdem nicht automatisch
mit Extended, wenn das SDK zufällig bereits installiert ist.

Reproduzierbare Vorbereitung in einer eigenen Umgebung, ohne fremde Venvs zu
ändern; offline nur möglich, wenn die erforderlichen Wheels bereits im Cache sind:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/pa-core-env \
  uv sync --frozen --offline --no-default-groups --group test-core --no-install-project
/tmp/pa-core-env/bin/python scripts/test_profiles.py core

UV_PROJECT_ENVIRONMENT=/tmp/pa-offline-env \
  uv sync --frozen --offline --no-default-groups --group test-offline --no-install-project
/tmp/pa-offline-env/bin/python scripts/test_profiles.py extended

UV_PROJECT_ENVIRONMENT=/tmp/pa-qdrant-env \
  uv sync --frozen --offline --no-default-groups --group test-qdrant --no-install-project
# Expliziter lokaler SDK-Teilumfang, zusätzlich durch den Offlineguard begrenzt:
PA_QDRANT_TESTS=(
  tests/test_cs50_index_cli.py tests/test_cs50_index_contract.py
  tests/test_cs50_ingestion.py tests/test_cs50_knowledge_index_checkpoint.py
  tests/test_cs50_knowledge_index_mapping.py tests/test_cs50_retrieval.py
  tests/test_cs50_retrieval_evaluation.py tests/test_cs50_index_end_to_end.py
)
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /tmp/pa-qdrant-env/bin/python -m pytest -q -o addopts='' -p no:cacheprovider \
  -p tests.offline_guard --run-external "${PA_QDRANT_TESTS[@]}"
```

Die Lockergänzung beschreibt ausschließlich neue Gruppen auf bereits vorhandenen
Paketversionen/-quellen/-Hashes. Kein Upgrade, keine neue Modellabhängigkeit.
Die Gruppen wurden mit `uv export --frozen --offline --no-default-groups --group
<Gruppe> --no-emit-project` erfolgreich gelesen und auf ihren Paketumfang geprüft.
Ein vollständiges `uv lock --check --offline` ist mangels gecachter
Direkt-URL-Metadaten des bestehenden spaCy-Modells blockiert. Der neue Offline-
Syncversuch war außerdem durch das fehlende Lock-Wheel `pydantic-core==2.46.4`
blockiert. **Keine erfolgreiche Neuinstallation oder vollständige Lockauflösung
behauptet.** Die vorhandene Coreumgebung enthält die Lockversionen und weder
BeautifulSoup/PyMuPDF noch Qdrant, zusätzlich aber Entwicklertools. Deshalb wurden
allein die 25 für die aktuelle Plattform exportierten Coredistributionen in eine
neue `venv --without-pip` unter `/tmp/maint03b-minimal-core-xapl1c86` kopiert.
Auch dort bestehen alle 199 Fälle. Das ist ein kontrollierter Snapshot installierter
Pakete, kein neuer Wheel-/Hash-/Installationsnachweis. Es werden keine fremden
Venvs geändert und keine Modelle installiert.

## Core

Zehn explizite Dateien in `scripts/test_profiles.py::CORE`, keine dynamische
Namensheuristik: beide MAINT-03-Regressionsdateien, Contentmodelle, Read-DTOs,
CS50-Discoverymodelle, drei Knowledge-/Provenienzdateien, Metriken und die neuen
Profilnegativtests. **199 passed, 0 failed, 0 skipped, 0 Sammlungsausfälle.**
Die strikt isolierte Kopie von 25 Distributionspaketen besteht auf dem finalen Fixturestand in 4,95 Sekunden;
der vorhandene Lockversionsinterpreter mit zusätzlichen Entwicklertools in 3,75 Sekunden.

Geprüft: echte Dateibytes/ZIPs, sequenzielle Legacy-IOgrenzen, Retryklassifikation,
Modell-/DTO-/Hash-/Locator-/Redactionverträge, Provenienz und Profilgrenzen.
Einige bestehende Knowledgecharakterisierungen verwenden ausgeschnittene echte
Funktionskörper; das ist keine Vollintegration der Legacyrunner.

Nicht geprüft: HTML-/PDFparser, vollständige Store-/FTStransaktionen,
Prozess-/Worker-/HTTPintegration, optionale SDKs, Modelle, Images, Browser und
Produktivzugriffe. Die 34 MAINT-03-Fälle sind in den 199 bereits enthalten.

## Extended Offline

Alle unter `tests/` sammelbaren Fälle außer expliziten Externalfällen. Dazu gehört
Core als Teilmenge. Keine Entfernung langsamer Tests oder ungeklärter echter Fehler; native
Tool-/SDKtests werden aufgrund nachgewiesener Voraussetzungen explizit External.
Insbesondere bleibt der Workflow-Schemasnapshot im Gate.

Ergebnis: vor der letzten Markerfixturekorrektur alle 2.392 gewählten Funktionen
in getrennten fortgesetzten Prozessen ausgeführt: 2.371 passed, 4 failed,
17 Testskips plus 8 SDKmodulskips. Die finale Auswahl enthält mit der neuen
Markerregression 2.393 Funktionen. Danach nur betroffene Dateien erneut geprüft,
kein weiterer gesamter Breitlauf. Der gezielte letzte Nachlauf ergibt 62 passed,
1 unveränderten Schemafehler, keine Skips/Sammlungsausfälle. Siehe
[Ergebnistabelle und Grenzen](maint03b_validation.md).
Geprüft werden synthetische temporäre Content-/Review-/SQLite-/FTSdaten,
HTML/PDF/Code-/Transcriptparser, Receipts, Hash-/ACL-/Crash-/Backupgrenzen,
Job-/Workflow-/Workerprozesse und direkte HTTP-Anwendungsadapter ohne Listener.
Umask-, Klassenidentitäts- und Hardlinknegativtests gehören hierher.

Nicht geprüft: echte Listener/Transports, Docker und andere Infrastrukturtools,
Originalmaterial, installierte vollständige LLM-/Media-/Modellprofile. Qdrant ohne
SDK ebenfalls nicht geprüft, sondern mit genau benanntem Modulskip ausgewiesen.
Der ebenfalls optionale SymPy-Backendpfad ist im schlanken Profil nicht installiert;
die vorhandenen expliziten Symbolikskips bleiben sichtbar. Das ist kein Nachweis
der algebraischen Äquivalenzprüfung. Ein eigener kleiner Symbolik-Dependency-
und Lockauftrag ist sinnvoll; dafür keine großen NLP-/Torchprofile installieren.

`tests/offline_guard.py` verbietet DNS, connect/connect_ex, bind/listen und
create_connection sowie direkte Docker/Podman/SSH/SCP/SFTP/Kubernetes-/Cloud-/
Downloadprozesse und Shellsubprozesse im Testhauptprozess. Negativtests sichern
diese Grenzen. Der Guard ist **kein Betriebssystem-Sandboxersatz**: `python -I`
und andere Kindprozesse laden ihn nicht automatisch. Deren vorhandene
synthetische Fixtures, eigenen Socketguards und die Ausführungssandbox bleiben
Teil der Grenze. Eine allgemeine transitive Netzwerkisolation wird nicht behauptet.

## External Integration

Die reine Sammlung selektiert **132 von 2.525 sammelbaren Fällen**, 2.393 werden
abgewählt. **0 Testfälle ausgeführt; bestanden/fehlgeschlagen/übersprungen als
Ausführungsstatistik nicht gemessen.** Keine Sammlungsausfälle; acht optionale
Qdrantmodule werden zusätzlich bereits bei Sammlung übersprungen.

Zuordnung: echte Content-HTTP-, Deploymenttransport- und Workerimagedateien,
installierte Lazy-Marvin-/uv-Smokes, echter lokaler Search-HTTPserver, drei einzelne native Composeprüfungen, die komplette
HTTPS-Preflightdatei mit realem Compose-Renderer, Provider-SDKkonfiguration sowie sämtliche optionalen Originalpiloten/-exporte und die ausdrücklich
privilegierte Root-/Mountprüfung. Die acht zusätzlichen Qdrantdateien benötigen
ebenfalls das explizite External-Opt-in; sie sind hier mangels SDK nur als
Sammlungsskips sichtbar, nicht als verfügbare zusätzliche Testfunktionen.
Konservativ bleibt die gesamte Workerimagedatei in diesem Profil, auch ihre
reinen CLI-/Dateiprüfungen. Ihre Ergebnisse wurden deshalb nicht als Extended-
Erfolg mitgezählt.

Erforderlich je Fall: erlaubte lokale Loopbacklistener, Docker-CLI beziehungsweise
explizit freigegebener lokaler Daemon und vorhandenes Image, installierte Worker-/
LLM-SDKs oder freigegebene lokale Originalartefakte. Providerkonfiguration nutzt
`CS50_TEST_PROFILE=sdk` und macht selbst keine APIaufrufe. Native Imagechecks
behalten zusätzlich ihre vorhandenen Opt-ins `C26_WORKER_CONTEXT_AUDIT=1` bzw.
`C26_WORKER_TEST_IMAGE`. Keine Zugangsdaten beschaffen und keine Images/Modelle
als Teil dieses Auftrags herunterladen. Ein Profilstart hebt keine dieser
Voraussetzungen oder das auftragsspezifische Infrastrukturverbot auf.

## Optionale Qdrantsammlung

Die sieben ursprünglich nicht sammelbaren Dateien sind:

- `test_cs50_index_cli.py`
- `test_cs50_index_contract.py`
- `test_cs50_ingestion.py`
- `test_cs50_knowledge_index_checkpoint.py`
- `test_cs50_knowledge_index_mapping.py`
- `test_cs50_retrieval.py`
- `test_cs50_retrieval_evaluation.py`

Hinzu kommt `test_cs50_index_end_to_end.py`, dessen drei Fehler ursprünglich erst
im Testkörper auftraten. Alle acht besitzen jetzt eine erkennbare gemeinsame
Sammlungsgrenze über `tests/qdrant_support.py` und
`tests/optional_dependencies.py::require_qdrant`.

Nur wenn `find_spec('qdrant_client') is None`, wird ein Modulskip mit konkretem
`test-qdrant`-Installationshinweis erzeugt. Ein vorhandenes SDK wird normal
importiert: fehlende transitive Imports, ABI-/Versionsfehler und echte Assertions
propagieren. Das wird insbesondere mit einem simulierten fehlenden `grpc` in
einem vorhandenen SDK negativ geprüft. Es gibt keinen breiten `except ImportError`
und keine pauschalen xfails. Ein Modulskip entspricht keiner bekannten Anzahl
bestandener oder übersprungener parametrisierter SDKfälle.
