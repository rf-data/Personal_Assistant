# C27 Learning: aktuelle lokale Bedienung (R12)

Diese Anleitung gilt für `src.c27_learning_summary` im Repositorycheckout.
Aktueller Status und historische Einordnung: [reviews/README.md](reviews/README.md).
Die älteren Anleitungen unter `docs/lecture_summary/` und die bisherigen
C27-Abschlussberichte sind historische Belege. Ihre Pfade und früheren
Ausführungsfreigaben sind keine heutigen Voraussetzungen oder Autorisierungen.

## Zwei getrennte Implementierungen

| Verwendung | Learning | Acceptance / Legacy / Hierarchy |
|---|---|---|
| Python | `src.c27_learning_summary` | `src.lecture_summary` |
| Modelle | Catalog mit courses/weeks/units; Claim mit refs; SummaryResult v2 | Catalog mit lectures; Claim mit source_ids/quality; Summary v1 |
| Speicherung | expliziter lokaler SummaryStore, append-only Reviews | RegisteredStorage und separat gewähltes Cacheverzeichnis |
| Zentrale Tests | `tests/test_c27_learning_summary.py` | `tests/test_lecture_summary.py` |
| Bedienung | die unten genannten bestehenden CLI-/UI-Einstiege | eigene Acceptance-Einstiege, falls diese Linie installiert ist |

Die Learning-Basis enthält Acceptance noch nicht. Dessen Namen bleiben reserviert;
es gibt keine Aliasauflösung, gemeinsame Modellunion oder automatische Konvertierung.
Die gleiche Schemanummer bezeichnet keine gemeinsame Datenfamilie. Stores und
Cacheverzeichnisse ausdrücklich getrennt halten. Dieses Paket installiert keine
Acceptance-Dateien und gibt dessen Exporte nicht durch das R09-Learning-Gate frei.

## Vorhandene lokale Umgebung

Aus dem Repositoryroot mit einem bereits vorhandenen Python >=3.12,<3.14 und den
benötigten Projektabhängigkeiten starten. Für die UI ist zusätzlich Streamlit
erforderlich. Es gibt hier keinen neuen Wheel-/Packagingvertrag und keine
Installations- oder Downloadfreigabe. Im R12-Prüflauf fehlt Streamlit; die echten
UI-Tests sind deshalb offen. Kein SDK- oder UI-Ersatzstub zählt als UI-Nachweis.

Ein vorhandener Interpreter kann als `C27_PYTHON` gesetzt werden. Die Beispiele
erzeugen ausschließlich neue eigene Ausgaben unter `/tmp`:

```bash
export C27_PYTHON=/pfad/zur/vorhandenen/umgebung/bin/python
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## Synthetischer Offline-CLI-Lauf

```bash
c27_output=$(mktemp -d /tmp/c27-learning-offline.XXXXXXXX)
"$C27_PYTHON" -m scripts.lecture_summary_offline --output "$c27_output"
```

Der bestehende Einstieg verwendet mitgelieferte synthetische Fixtures und FakeLLM,
erzeugt einen lokalen Store, ein synthetisches Review, JSON-/Markdownexport und
Report und prüft Cache-Reuse. `approved` bezeichnet nur dieses synthetische Review;
es ist keine fachliche Kursfreigabe. Kein Provider oder Download ist beteiligt.

Die Reviewpipeline akzeptiert ausschließlich einen bereits lokal vorhandenen,
hashgebundenen Reviewinput. Bei entsprechender eigener Datenautorisierung:

```bash
c27_review_output=$(mktemp -d /tmp/c27-learning-review.XXXXXXXX)
"$C27_PYTHON" -m scripts.c27_reviewed_week \
  --review-root /pfad/zum/autorisierten/lokalen/review \
  --output "$c27_review_output" --fake-summary \
  --material-id explizit-gewaehlte-material-id
```

`--material-id` ist wiederholbar. Ohne diese Option bleibt der bisherige explizite
CLI-Vertrag für alle verarbeiteten Materialien erhalten. Keine Option dieses CLI
aktiviert einen echten Provider, einen Download oder eine Veröffentlichung.
Der vorhandene 5-GiB-Freiraumwächter bleibt unverändert; R12 prüft vor breiteren
Läufen zusätzlich 512 MiB Arbeitsreserve (Startschwelle 5.905.580.032 Bytes).

## Learning-UI

In einer bereits ausgestatteten Umgebung und mit eigenen expliziten Speicherorten:

```bash
export LECTURE_SUMMARY_CATALOG=/pfad/zum/learning/catalog.json
export LECTURE_SUMMARY_STORE=/pfad/zum/eigenen/learning-summary-store
"$C27_PYTHON" -m streamlit run lecture_summarizer_app.py
```

Die bisherigen Umgebungsnamen, `lecture_summarizer_app.py` und die Seite
`frontend/pages/G_p0_lecture_summarizer.py` bleiben erhalten. Ohne Catalogoption
wird die synthetische Demo angeboten. Generierung und Review erfolgen über die
bisherigen Benutzeraktionen. Echte Provider sind außerhalb dieses R12-Auftrags.

## Persistenz, Wiederaufnahme und Exporte

Eigene Learning-v1/v2-Ergebnisbytes bleiben lesbar. v1 wird ausschließlich im
Speicher als eigene Learning-v2-Familie gelesen; Rohresultate und Reviewereignisse
werden nicht umgeschrieben. Acceptance-Payloads müssen im Learning-Modell scheitern.

Die Processingrevision bindet Modulnamen und Quellbytes. Durch R12 entstehen daher
neue Processingkeys und neue Unterverzeichnisse. Alte Processingcaches und Receipts
bleiben stehen und werden weder umbenannt noch migriert. Ein erneuter Lauf derselben
R12-Revision kann seinen neuen Processingcache wiederverwenden. Der Summarycache
bindet seine bisherigen Eingaben und Schemas; ein reiner Namespacewechsel erzwingt
keine neue Summaryidentität. R12 prüft echte Weiterlesbarkeit und Reuse eines vor
dem Umzug erzeugten SummaryStore samt Reviews ohne neue FakeLLM-Aufrufe.

Die mitverschobene `src/c27_learning_summary/public_sources.v1.json` bleibt die
zentrale exakte Quellenfreigabe. Die Policy lädt sie relativ zu `__file__`.
75 historische URLwerte, Fixtures und Allowlistbytes bleiben erhalten.
Die R08-Feldprojektion gilt für öffentliche Metadaten; SourceRef.text und Claim.text
bleiben fachlicher Freitext. Alte Exporte werden nicht rückwirkend bereinigt oder
neu erzeugt. Neue Exporte bekommen eigene Namen und eine explizite Auswahl;
bestehende reviewgebundene Exportnamen und Hashidentitäten bleiben erhalten.

## Lokale Prüfung und derzeitige Grenzen

```bash
"$C27_PYTHON" -m pytest -p tests.offline_guard -p no:cacheprovider \
  tests/test_c27_learning_summary.py tests/test_c27_summary_coexistence.py \
  tests/test_lecture_summary_ui.py tests/test_c27_reviewed_week.py \
  tests/test_c27_remediation_r02.py tests/test_c27_remediation_r04.py \
  tests/test_c27_remediation_r06.py tests/test_c27_remediation_r08.py
```

Externe Tests verlangen zusätzlich ein ausdrücklich autorisiertes lokales
Eingangsverzeichnis und das bestehende Testprofil. Ohne Streamlit ist ein Skip der
bestehenden UI-Suite kein grüner UI-Status; der R07-Downloadtest schlägt dann mit
fehlendem Modul fehl. Tests, Wächter und Assertions dafür nicht abschwächen.
Die globale Mypy-Schuld von historisch 6.104 Diagnosen ist kein grüner Prüfstatus.

R12 autorisiert weder Staging/Commit/Push/Fetch/Merge/PR noch Produktion.
Defaultbranchintegration und dauerhafte Handoffsicherung bleiben Folgearbeit.
Bestehender Branch, Worktree, Rohdaten, Stores und alle alten Handoffs bleiben
erhalten. Ein späterer Rollback erfolgt über einen regulären Review-/Revertprozess;
historische Ergebnisse und Reviewereignisse werden dabei nicht gelöscht.
