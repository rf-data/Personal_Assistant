# DEV-03E – Explizite Nicht-CS50-Kurskennung im Contentvertrag

20.10.2026, Basis master `ba59560`, DEV-03D/#131 integriert.
Separater Vertrags-PR; keine Quellregistrierung oder produktive Migration.

## Änderung und bestehende Grenzen

`src/model_course.py::ContentCourseId` ergänzt den unveränderten geschlossenen
CS50-Kurskatalog um genau `loviscach_mathe_1`. Keine beliebigen Strings, neue
Registry, Datenbank oder dynamische Freigabe. `src/model_discovery/cs50.py::CourseId`
bleibt unverändert und ausschließlich CS50-spezifisch.

Contentregistrierung/-Views, Read-/Searchfilter, Indexprojektion/-Jobs,
C23-Korpus-/Inventarmodelle, C24-Evaluationsscope und C16-Principal/Katalog verwenden
die zusätzliche geschlossene Contentkennung. Source-ID und Rawhash bleiben
unabhängig davon. Der generische C23-IDalgorithmus ist unverändert; bestehende
CS50-Resource-IDs und kanonische JSONdaten werden nicht neu geschrieben.

CS50-Planning, Materialquality, Workflow, PDF- und Bundleimport-Jobparameter bleiben
an den ursprünglichen Discoverykurs gebunden. Insbesondere erweitert dieser PR
**nicht** `ResourceCandidate`, `MaterialResource`, den CS50-Adapter oder dessen
Raw-/Receipt-/Plan-/Revisionsgates. `SourceRegistration` verweigert ausdrücklich
die neue Kurskennung im reservierten Namespace `cs50`. Kein Umdeklarieren einer
Loviscach-Klausur als CS50-Material und kein Gate-Fallback.

Eine generische Source lässt sich damit korrekt ausdrücken. Ein vollständiger
Nicht-CS50-Material-/Reviewimport braucht weiterhin eine tatsächlich passende
Material-/Versionsbindung. Der separat erlaubte DEV-03E-Reallauf benutzt deshalb
unveränderte integrierte PDF-/Visualworker ohne C23-Publikation. Er benötigt
diesen ungemergten Vertrag nicht als Runtimevoraussetzung.

## Serialisierung, Schema und Berechtigungen

- Keine SQL-DDL-, application_id-, user_version-, Artefakt- oder IDänderung.
  Keine automatische Migration, Recovery, Bestandsregistrierung oder Neuindizierung.
- Alte Kurswerte und gespeicherte JSONobjekte bleiben gültig. Neue Werte erweitern
  bestehende Enumfelder additiv; Wire-/Modellversion bleibt v1. Bestehende sechs
  CS50-Werte behalten ihre Reihenfolge und Identität.
- C16-Vertragssnapshot und betroffene vorhandene API-Schemafelder werden um diesen
  einen Enumwert ergänzt. Keine sonstigen Schemafelder oder Registryeinträge werden
  geändert. Alte Clients mit geschlossenem Enum müssen vor Anzeige neuer
  Loviscach-Objekte gezielt aktualisiert werden; deren CS50-Verarbeitung bleibt
  unverändert. Keine UI-/Produktivkonfiguration in diesem PR.
- Principal, Ownership, Sourcegrants, Course-Scope, Reviewgrants und Live-Widerruf
  bleiben kumulative Voraussetzungen. Das Zulassen eines Kurswerts vergibt keine
  Rechte. CS50-Scope allein kann auch bei gleicher Subject-ID keine Loviscachquelle
  lesen. Sourcegrant allein ersetzt fehlenden Course-Scope nicht.
- Rückkehr zu einer alten Programmversion nach zukünftiger Speicherung neuer
  Loviscach-Datensätze wäre keine transparente Datenmigration: Der alte geschlossene
  Validator kann diese Datensätze ablehnen. Erst isoliert prüfen, neue Quellen nicht
  vorzeitig publizieren, keine alten Artefakte umschreiben. Dieser PR schreibt keine
  solchen Daten in einen produktiven Store.

## Tatsächliche Validierung

Neue Fälle prüfen die sechs alten Identitäten/JSON-Roundtrips, geschlossene
CS50-Discovery, unbekannte Kurse, reservierten CS50-Namespace, neue C23-/DTO-/B1-
Schemas sowie echte temporäre SQLite-/FTS5-Publikation synthetischer Inhalte,
Readfilter, Wiederöffnung, Sourcegrants, Widerruf und fehlenden Course-Scope.
Keine echten Klausuren sind Eingaben dieser Tests.

Vorläufige Entwicklungsläufe: 7 pass/1 fail (Test verwendete ein nicht vorhandenes
`SearchHit.course_id`), danach 197 pass/1 fail (neuer Test verwendete
`SourceView.registration` statt der bestehenden redigierten `course_id`).
Korrigiert wurden Testannahmen, keine DTOs um unnötige Felder erweitert.

Erweiterter Sandboxlauf: **233 pass / 1 fail / 43 Setupfehler**, 225,59 s.
Die 43 bestehenden HTTP-Fälle konnten wegen gesperrter Socket-Erzeugung nicht
starten (`PermissionError`), nicht wegen eines Produktivservers. Der einzelne
Fehler war der bestehende C16-Schemasnapshot nach der absichtlichen additiven
Enumänderung; Snapshot und betroffene API-Enumfelder anschließend gezielt
aktualisiert. Keine Assertions oder Schutzgrenzen abgeschwächt. Der abschließende
Lauf verwendet ausschließlich einen synthetischen Loopbackserver.

Abschließender gemeinsamer Lauf mit erlaubtem synthetischem Loopback:
**277 pass / 1 fail / 0 skip / 0 Setupfehler, 256,18 s**, 278 Fälle aus
`test_content_course.py`, `test_cs50_discovery.py`, `test_content_store_models.py`,
`test_content_read_contracts.py`, `test_content_retrieval_evaluation.py`,
`test_content_retrieval_integration.py`, `test_content_fts.py`,
`test_review_fts_pilot.py`, `test_content_http.py`, `test_job_control.py`.
Alle neun neuen Kursfälle, alle 43 echten synthetischen HTTP-Fälle und der
C16-Schemasnapshot bestanden. Keine vollständige grüne 278er-Suite behauptet.

Der eine Fehler: bestehender C16-Node
`test_real_adapters_persistence_artifacts_and_read_only_inputs[material_planning]`,
`sqlite3.OperationalError: database is locked` bei `BEGIN IMMEDIATE`.
Gleicher Node isoliert mit unveränderten Limits: **1 pass, 3,80 s** auf diesem
Branch und **1 pass, 3,92 s** auf unverändertem Runtimecode von master `ba59560`
im getrennten Evaluationsworktree. Kein reproduzierter Baselinefehler, Ursache
weiter offen. Anschließend die gesamte direkt betroffene C16-Datei erneut:
**36 pass / 0 fail / 0 skip, 11,33 s**. Keine SQLite-/Guardianänderung, kein Retry,
kein erhöhtes Zeitlimit und keine entsperrten produktiven Daten.

Tatsächliches Präfix (vorhandener Projektinterpreter als `DEV03_PYTHON`):

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$DEV03_PYTHON" -m pytest -q -p no:cacheprovider
```

Jeder Lauf hatte einen separaten temporären Basetemp. Logs außerhalb des Repos:
`dev03e-course-final.log`, `dev03e-course-c16-target.log`,
`dev03e-base-c16-target.log`, `dev03e-course-c16-release.log`.
Ruff Check/Format Check für alle 13 geänderten/neuen Pythondateien und
`git diff --check` erfolgreich. Zusätzlich alle vier geänderten JSONschemas
gegen den alten Stand geprüft: ausschließlich additive Kurs-Enumwerte, keine
sonstigen Struktur-/Werteänderungen. Alle historischen Läufe bleiben separat;
keine Addition überlappender Fallzahlen und keine Gesamtrepositoryabnahme.

## Lifecycle

Eigenständiger PR gegen master vor einer darauf aufbauenden C23-gebundenen
Realverarbeitung. Keine automatischen Merges; Branch und Worktree bleiben bis
zur geprüften Integration erhalten. Andere DEV-/MAINT-Bestände unberührt.
