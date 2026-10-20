# DEV-03A – Drei einzeln freizugebende Kandidaten

20.10.2026, Backend master `7a4f2be`, UI main `a7da646`. DEV-02A #126 ist
integriert; Import #127 und UI #17 sind offen. Kein vollständiger DEV-02-UIpfad.
Der Betreiber hat ausschließlich synthetische Vorbereitung autorisiert.
**Realstatus: `blocked_pending_source_authorization`.** MAINT bleibt On Hold.

Die Auswahl liest nur das bereits integrierte C24-05-C2-Metadatenmanifest
`docs/cs50/evaluation/c24_05c/r3/corpus_manifest.v1.json`. Keine Originaldatei,
kein privates Datenverzeichnis, kein Store und kein Download wurden geöffnet.
Drei Planungszeilen sind keine drei verfügbaren Dokumente. Kein mathematisches
Vorlesungsskript ist derzeit als eigenständig freigegebene Quelle belegt.
Die tatsächliche Formel-/Tabellen-/Bildabdeckung dieser Kandidaten ist ungeprüft.

| Kandidat / Metadatenreferenz (entry_id) | Bekannte Source-ID | Dokumentierte Quelle / Format | SourceVersion / Parserrevision | Evaluationszweck und Eignungsgrenze |
| --- | --- | --- | --- | --- |
| `cs50_ai_lecture_1` | `resource:fa5748ba8a2899d835a2fe52fe678aae3bf5a67db23b970ac030b6b6c8b7d028` | https://cs50.harvard.edu/ai/notes/1/ · HTML | unbekannt / unbekannt | Struktur, Textreihenfolge, Unicode, mögliche Formeln/Tabellen/Bildreferenzen; Inhalt erst nach Freigabe prüfen |
| `python0_slides_missing` | nicht belegt | https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf · PDF | unbekannt / unbekannt | Mehrseitigkeit, Locatoren und Visualbezüge; kein belegtes mathematisches Skript, vollständiges Bundle fehlt |
| `python0_srt_blocked` | `resource:fde25833bbf19ce14828f9b719ded15fe02cc15f313551b1357c34f571f5e0b5` | https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt · SRT | unbekannt / unbekannt | Cue-/Zeit-/Überlappungsprüfung; zusätzlich D06-Pfadbindung und D07 offen, vor deren Entscheidung nicht verwenden |

Die im HTML-Metadatensatz vorhandene SHA ist ausschließlich eine historische
Deklaration, kein neuer Hashnachweis. Im neuen CorpusManifest sind alle Einträge
`permission=denied`, ohne Artefaktpfade oder InventorySelection. GoldDataset ist
leer. Keine aus Parsern, Retrieval oder LLM erzeugten realen Goldreferenzen.

## Freigabe 1 – HTML

- Kandidat: `cs50_ai_lecture_1`; Source-ID siehe Tabelle, vom Betreiber bestätigen.
- Exakter autorisierter Originalpfad **oder** bestehende SourceVersion: **offen**.
- SHA256/Größe und Beleg der ursprünglichen Version: **offen**.
- Explizite Raw-/Parsed-/Receipt-/Plan-/ImplementationEvidence-/Bilddateien: **offen**.
- Zweck: begrenzte Parsing-/Provenienz-/Retrievalevaluation; erlaubte Schritte
  (Lesen, Kopieren, Parsen, C23-Import, Indexbuild, Review, Export) einzeln: **offen**.
- Neuer privater Content-/Evaluation-/Index-/Ergebnisroot: **offen**.
- Zugriffsberechtigte, Nutzungs-/Weitergaberechte, Aufbewahrung/Löschregel: **offen**.
- Entscheider, Datum, Beleg, Gültigkeit/Widerruf und D07: **offen**.
- Menschlicher Reviewer, Backend-Principal/Course/Reviewgrants, Approver: **offen**.
- Goldversion, unabhängige Originalannotation, Reviewbeleg: **offen**.
- Entscheidung: **nicht erteilt**. Keine Verarbeitung durch Ausfüllen dieses Dokuments allein.

## Freigabe 2 – PDF

- Kandidat: `python0_slides_missing`; stabile Source-ID: **vom Betreiber zu belegen**.
- Exakter Originalpfad oder SourceVersion, SHA256/Größe, Originalversion: **offen**.
- Vollständige explizite Bundle-/Bilddateien, Parserkonfiguration/-revision: **offen**.
- Zweck: Seiten-/Struktur-/Visual-/gegebenenfalls Formelevaluation; erlaubte
  Schritte Lesen/Kopieren/Parsen/Import/Index/Review/Export einzeln: **offen**.
- Neue private Content-/Evaluation-/Index-/Ergebnisroots: **offen**.
- Zugriff, Nutzungs-/Weitergaberechte und Aufbewahrung/Löschregel: **offen**.
- Entscheider, Datum, Freigabebeleg, Gültigkeit/Widerruf und D07: **offen**.
- Menschlicher Reviewer, technischer Principal/Grants, Approver: **offen**.
- Unabhängige Goldversion/-annotation/-reviewbelege: **offen**.
- Entscheidung: **nicht erteilt**. Bei ungeeignetem Formelinhalt zunächst Ersatzquelle
  ausdrücklich benennen und gesondert freigeben; kein automatischer PDFscan.

## Freigabe 3 – SRT

- Kandidat: `python0_srt_blocked`; Source-ID siehe Tabelle, bestätigen: **offen**.
- Originalpfad oder SourceVersion, SHA256/Größe und Originalversion: **offen**.
- Vollständige unveränderte Raw-/Transcript-/Receipt-/Adapterplan-/Revisiondateien: **offen**.
- D06-Entscheidung zur kanonischen Bindung: **offen**. Historische Abweichung
  `data/Harvard/...` versus `data/lectures/Harvard/...` nicht reparieren/umgehen.
- Zweck: bekannte Cuezeiten/Überlappung/Provenienz/Retrieval; erlaubte Schritte
  Lesen/Kopieren/Prüfen/Import/Index/Review/Export einzeln: **offen**.
- Neue private Content-/Evaluation-/Index-/Ergebnisroots: **offen**.
- Zugriff, Nutzung/Weitergabe, Aufbewahrung/Löschregel: **offen**.
- Entscheider, Datum, Beleg, Gültigkeit/Widerruf und D07: **offen**.
- Menschlicher Reviewer, Principal/Course/Reviewgrants und Approver: **offen**.
- Goldversion, Originalcues/-zeiten, unabhängige Reviewbelege: **offen**.
- Entscheidung: **nicht erteilt**. Keine Symlinks, Migrationen oder Workspacekopien.

## Vorhandene Reviewverträge nach tatsächlicher Einzelfreigabe

Pro Source zuerst bestehende `InventorySelection` am C23-Gate verifizieren;
SourceVersion/Parseridentität niemals aus aktuellem HEAD oder ähnlichen Dateien
ableiten. Unveränderte Originale behalten. Originalstellen und Queries vor Retrieval
festlegen. Menschen prüfen Originalregionen mit Unicode-Codepointoffsets und
annotieren `TaskSpec`/`Region`/`Annotation` in B1/B2. Queryrelevanz 0–3, negative
Stellen und vollständigen Pool gesondert bestätigen. Mehrdeutige Formeln benötigen
visuellen Kontext und gegebenenfalls unabhängige Zweitprüfung.

Export ausschließlich über bestehende B1-Goldverträge: Parsing `GoldDataset` /
`GoldReference`, Retrieval `ContentRetrievalEvaluationSet`. `pending_review` ist
kein bestätigtes Gold, unjudged ist nicht irrelevant. Kein Reviewer/Approver wird
hier erfunden. Kein Live-Reviewtask wird ohne Originalbindung erstellt.

Noch fehlende Entscheidungen beschränken sich auf die ausgefüllten Einzelfreigaben,
D06/D07, reale technische Source-/Reviewgrants und tatsächliche menschliche
Original-/Goldreviews. Es ist keine neue Architekturentscheidung erforderlich.

## Tatsächliche technische Prüfung

Bestehender C23-06-Runner gegen genau dieses verweigerte Metadatenmanifest und
leeren GoldDataset ausgeführt; ausschließlich ein neuer temporärer Root ohne
Originaldateien. Unveränderte Runnerausgaben unter [report/summary.md](report/summary.md)
und [report/evaluation_report.v1.json](report/evaluation_report.v1.json).
Drei nicht freigegebene Kandidaten, null Source-/Parsernachweise, null unabhängige
Goldreferenzen; alle Metriknenner 0 und Raten null (keine 0-Prozent-Qualität).
`missing_raw_artifact` bedeutet hier: keine Originaldatei zur Prüfung bereitgestellt;
keine Behauptung, dass eine private Datei nicht existiert.

39 passed / 0 failed / 0 skipped, 14.23 s:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
-q -p no:cacheprovider tests/test_dev03_onboarding.py \
tests/test_cs50_material_evaluation.py --basetemp=/tmp/dev03a-contracts
```

Python 3.12.12/Pydantic 2.13.4/Pytest 9.1.1; vorhandene Umgebung, keine Installation.
Der neue Fall verbietet jeden Source-Byteread im Evaluator, variiert den nicht
existierenden Root, prüft identische Reportdigests, Nullnenner und No-Overwrite.
Die 38 bestehenden Fälle prüfen unabhängig synthetische Bundle-/Review-/ACL-/
Provenienzverträge. Ruff Check/Format Check der neuen Pythondatei und diff check
sind grün. Keine fachliche Realabnahme.

Dieses Paket führt nur vorhandene integrierte Modelle aus. Weitere unabhängige
synthetische Parsing-/Formel-/Visual- und Retrievalprüfungen verwenden ebenfalls
die bereits integrierten Verträge; kein Folgepaket setzt einen ungemergten neuen
A-Vertrag voraus. MAINT-/andere aktive Worktrees bleiben unverändert. Eigener
Branch/Worktree bleibt wegen des offenen PRs und ausstehender Dokumentintegration.
