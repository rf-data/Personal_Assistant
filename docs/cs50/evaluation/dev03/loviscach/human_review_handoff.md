# DEV-03F/F1 – Privates Erfassungspaket für menschliche Reviews

20.10.2026 · Backendbasis `ba5956014e6995538e285ae31741f3f7e89eb2cc`.
**Status `gold_review_prepared`: 40 vorbereitete Stellen, null menschliche
Entscheidungen, null bestätigte C23-Goldreferenzen.** Der Betreiber hat ausdrücklich
bestätigt, dass noch keine menschlichen Bewertungen vorliegen, und die Vorbereitung
des Erfassungspakets beauftragt. F2 und F3 sind nicht abgeschlossen.

## Tatsächliche Grundlage und Berechtigungsgrenze

Der integrierte [DEV-03D-Inventarbeleg](corpus_inventory.v1.json) bleibt unverändert:
`a37319b9b0d18fb246f6071638a35ae30b39f39f01187a3579cf5a501862500e`.
Die spätere DEV-03E-Betreiberfreigabe erlaubt ausschließlich die vier hashgebundenen
PDFs, lokale Verarbeitung und private Vergleichs-/Reviewartefakte im ausdrücklich
benannten Evaluationsroot. Betreiber und vorgesehener menschlicher Reviewer sind
`robfra`; Verzeichnisse 0700, Dateien 0600, Aufbewahrung bis zur gesonderten
Löschentscheidung. Der historische [D-Freigabeentwurf](authorization.md) bleibt als
datierter Nachweis erhalten; er wird hier nicht rückwirkend umgeschrieben.

Der tatsächliche versiegelte E-Lauf `run-e0dd4d41778649bcbe6f53f3ff67304b` wurde
erneut geprüft: **115 deklarierte Dateien hashidentisch**, vier Original-SHA256
weiterhin gleich, 40 bisherige Reviewkandidaten unbestätigt. Reportbodydigest:
`6551d52db9e7cb416d91ca807adea06d30bec9589417850f8f6e5ca3726b458b`.
Parserausführung `f0115bd5e020263efabc18cffd969f248cd26914`, PDF-v2 und C13;
die tatsächlichen Workerhashes und die Parserkonfiguration werden im privaten
Paket erhalten. Eine Modellrevision ist null, weil kein Modell eingesetzt wurde.
F1 führt keinen neuen Parser-, Formelvergleichs-, Store- oder Retrievallauf aus.

Live geprüft: [Kursvertrags-PR #132](https://github.com/rf-data/Personal_Assistant/pull/132)
und [E-Lauf-PR #133](https://github.com/rf-data/Personal_Assistant/pull/133) sind
**offen**, ebenso [UI-PR #17](https://github.com/rf-data/personal-assistant-ui/pull/17).
Vorhandene [Realreferenzaufgabe #107](https://github.com/rf-data/Personal_Assistant/issues/107)
und [Retrievalabnahme #108](https://github.com/rf-data/Personal_Assistant/issues/108)
bleiben offen. Kein neues Issue, keine fachliche Abnahme, keine Statusänderung
auf Done, kein Merge und keine MAINT-Aktion.

## Auswahl und Artefakte

| Dokument | Formeln | Struktur | Visuals | Summe |
| --- | ---: | ---: | ---: | ---: |
| Mathe_1_2020-01-31.pdf | 5 | 3 | 3 | 11 |
| Mathe_1_2022-01-28.pdf | 5 | 3 | 3 | 11 |
| Mathe_1_2023-03-21.pdf | 5 | 2 | 2 | 9 |
| Mathe_1_2024-01-31.pdf | 5 | 2 | 2 | 9 |
| Gesamt | 20 | 10 | 10 | 40 |

**28 Kandidaten und zwölf systematische Kontrollstellen**, je vier Kontrollen pro
Dimension. Pro Dokument wird eine syntaktisch prüfbare Formel bevorzugt, sonst die
mittlere Formelbeobachtung; hinzu kommen vier weitere tatsächliche E-Kandidaten.
Eine mittlere gewöhnliche, nicht wiederholte Textstelle ohne Aufgabenlabel oder
erfasste Mathematikmarker dient als Strukturkontrolle. Bei Visuals beginnt die
Auswahl mit der mittleren C13-Beobachtung. Die restlichen Struktur-/Visualplätze
werden quellenübergreifend abwechselnd befüllt, ohne doppelte Review-IDs.

Kontrolle bedeutet **nicht fachlich korrekt**. Auch Formelauswahl und Visualinventur
bleiben parserabhängig. Die sieben vertretenen Dokumentseiten sind keine
Vollabdeckung: Bei 2024 stammen die ausgewählten Stellen ausschließlich von Seite 1.
Nicht erkannte Formeln, fehlende Seiteninhalte und dokumentweite Reihenfolge lassen
sich aus diesen Ausschnitten allein nicht beurteilen. Keine repräsentative
Stichprobe oder Hochrechnung; spätere Kennzahlen nach Auswahlkriterium trennen.
Die Visualstellen sind C13-Objektbeobachtungen, keine bestätigten Tabellen oder Bilder.

Der endgültige private Export heißt `review-f-88520519833147118e38eff6ea6b7bff`:
**48 Dateien, 332304 Bytes**. Paketbodydigest:
`609232af199a32583d6907a4c0b477198e8092991e7647fa5edf59ccdb350364`.
Dateimanifest-SHA256:
`4a25d9dc0901c85c3a0b1b37ed3a519bfc763c4c44cf451e018779cf06b8d389`.
Exporter-SHA256:
`87e0e2a319b8b8204350c85d09074a60e898620d75ee36ffcdd64c4481073c65`.

- `originals.html`: 40 Originalausschnitte mit Review-ID, Dateiname und Seite;
  keine Parsertexte oder Fehlerhypothesen in dieser Ansicht.
- `comparison.html`: danach Original und escaped Parsertext beziehungsweise die
  tatsächliche strukturierte C13-Beobachtung gegenüberstellen.
- `package.json`: Source-ID/Rawhash, Seite/BBox/ContentLocator, tatsächlicher
  Workerpointer und Responsehash, vorhandene E-Kandidaten-ID, Auswahlkriterium,
  Hypothese, Parserrevision und offene Versionsbindung.
- `pending_gold.v1.json`: vorhandener `GoldDataset`-/`GoldReference`-Vertrag,
  40 leere `pending_review`-Einträge; kein automatisch übernommener Goldtext.
- `responses.blank.json`: leere Erfassungsvorlage, keine vorausgewählten Urteile,
  keine behauptete Reviewzeit oder bestätigte Reviewerentscheidung.
- `query_worksheet.json`: 20 leere Fragearbeitsaufträge, fünf Suchintentionen je
  Dokument. **Null konkrete Evaluationsfragen**, null Relevanzurteile, kein
  vollständiger Pool; keine aus Rankings abgeleiteten Vorgaben.
- `README.md`, 40 lokale PNGs und zuletzt geschriebenes `manifest.json`.

Originale werden über No-Follow-Deskriptoren erneut hashgeprüft. Ausschnitte werden
mit vorhandenem PyMuPDF und vier Punkten Kontext erzeugt; Rotation/Flächenlimits
werden geprüft. HTML hat eine lokale CSP, keine Skripte oder externen Ressourcen.
Private Inhalte wurden weder ins Repository noch in Modell-/Toolausgaben übernommen.
Ein erster privater Export wurde um die tatsächliche C13-Vergleichsdarstellung
ergänzt; er bleibt unverändert erhalten. Für den Review ausschließlich den obigen
endgültigen Paketdigest verwenden. Keine alten Belege wurden überschrieben.

## Erfassung durch den Menschen

1. Lokal `originals.html` öffnen. Die Referenz selbst am Original ermitteln, noch
   bevor der Parservergleich angesehen wird. Bei unzureichendem Ausschnitt das
   freigegebene Original im lokalen PDF-Viewer prüfen oder `undetermined` wählen.
   Keine Originale/Extrakte an externe Modelle oder Cloudangebote senden.
2. Aus `responses.blank.json` eine **neue private Datei im Elternroot des Pakets**
   erstellen, beispielsweise `responses-r1.json`, Modus 0600. Versiegelte
   Paketdateien nicht bearbeiten. Nicht bearbeitete Fälle behalten `confirm=false`.
3. Für bearbeitete Fälle `annotation` gemäß bestehendem B1-`Annotation` ausfüllen:
   `schema_version=1`, `mode=independent_original`, `quality` aus
   `correct/partial/incorrect/undetermined`, unabhängiger `expected_content`,
   `error_categories` und begründender `comment`. Referenz bis 2000 Zeichen;
   bei unentscheidbarer Quelle darf sie null bleiben. Keine Reviewer-ID auswählen.
4. Danach den Parservergleich ansehen. Formelentscheidungen verwenden
   `exact_match/mathematically_equivalent/incorrect/incomplete/not_evaluable`.
   Bei Äquivalenz ist eine fachliche `equivalence_reason` Pflicht; optional
   `latex_reference`. Variablen, Operatoren und relevante Definitionsbedingungen
   im Kommentar prüfen. Struktur-/Visualfälle verwenden die B1-Qualitätsurteile.
5. Tatsächlichen zeitzonenbehafteten ISO-Zeitpunkt in `reviewed_at` und einen
   eigenen `evidence_reference` angeben. `confirm=true` und
   `original_reviewed_independently=true` ausschließlich selbst bestätigen.
6. Erst nach diesen tatsächlichen Bewertungen lokal erfassen:

```sh
# REVIEW_ROOT: der bereits ausdrücklich freigegebene private Evaluationsroot.
# REVIEW_PACKAGE: dessen endgültiger Paket-Unterordner, siehe oben.
python -m scripts.acceptance.dev03f_review capture \
  --package-root "$REVIEW_PACKAGE" \
  --responses "$REVIEW_ROOT/responses-r1.json" \
  --output "$REVIEW_ROOT/human-r1.json" \
  --attest-independent-human-review
```

Die Erfassung verlangt den tatsächlichen lokalen Benutzer `robfra`, explizite
Attestation, gültige bestehende `Annotation`/`IndependentReview`, Paket-/Dateihashes,
bekannte eindeutige Review-IDs, Entscheidungs-/Qualitätskonsistenz und neue
Ausgabedateien. Es wurde **keine reale Erfassung ausgeführt**. Die Bestätigung im
lokalen Beleg ist kein serverauthentifizierter B1-Status und keine neue Capability.

Korrekturen erzeugen eine neue Antwort- und Ergebnisdatei. `previous_sha256` der
Antwort muss den vorherigen Snapshotdigest enthalten; `--previous` benennt exakt
diese frühere Ergebnisdatei. Kein stilles Überschreiben oder automatisches Auflösen
von Konflikten. Offlinezweige bleiben getrennte Belege; der Export führt keinen
globalen Revisionshead, keine Datenbank und keine konkurrierende B1-Persistenz.
Dateihashes belegen Integrität, keine kryptografische Menschenauthentizität gegen
einen Angreifer mit demselben lokalen Benutzer.

## Warum noch kein B1/B2-Task oder freigegebenes Gold entsteht

Vorhandene [B1-API](../../../../api/human_review_v1.md), B1-`Annotation`,
C24-`IndependentReview` und C23-`GoldDataset` werden wiederverwendet. B2 ist die
kanonische Streamlit-Reviewoberfläche; hier wird keine zweite Anwendung eingeführt.
Die E-Artefakte sind jedoch Workerbeobachtungen ohne veröffentlichte
`SourceVersion`, `ParsedDocumentVersion`, C23-Blockidentitäten, Payload-/Projektions-
bindung oder tatsächliche Backendgrants. B1-`Region` benötigt diese Angaben.
Ein Rawhash, ein vorgeschlagener Source-Identifier oder ein Workerpointer ersetzt
sie nicht. Der noch offene Kursvertrag #132 allein liefert keinen verifizierten
Nicht-CS50-Materialadapter und keine rückwirkende Publikation des E-Laufs.

Darum bleibt auch ein späterer lokaler menschlicher Beleg **C23-pending**, bis die
echte Versions-/Blockbindung und autorisierte Übernahme feststehen. Vorhandene
Goldvalidierung wird nicht gelockert; keine erfundenen Versionen, falsche CS50-
Zuordnung, neuen Routen oder Browserrollen. Ein späterer B1-Import muss die
Original-/Worker-/Regionbindung gegen die tatsächlich veröffentlichte Projektion
erneut prüfen, passende Reviewer-/Sourcegrants verwenden und den menschlichen
Reviewbeleg erhalten. Dafür ist kein automatischer Import implementiert.

## Offene Entscheidungen für F2 und F3

Für F2 fehlen tatsächliche unabhängige Referenzen und die zulässige vollständige
Provenienzbindung. Aktuell: Reviews **0/40**, bestätigtes C23-Gold **0/40**,
evaluierbarer Qualitätsnenner **0**. Exact/Äquivalenz/Struktur-/Visualqualität sind
`not_evaluable`, Raten null; keine Null-Prozent-Qualität. Keine fachlichen Fehler,
häufigsten Fehlerklassen oder Ursachen aus ungeprüften Hypothesen behaupten.

Für F3 ist eine **neue begrenzte Betreiberentscheidung** nötig. Ausfüllvorlage,
derzeit keine Freigabe:

| Entscheidung | Noch konkret festzulegen |
| --- | --- |
| Quellen | Gewählte der vier Source-IDs/Rawhashes aus dem Inventar, erlaubter Zweck, konkrete Source-/ParsedVersions und Versionsbelege |
| Roots | Exakte neue private getrennte ContentStore-, EvaluationStore- und Indexroots; Nichtnutzung bestehender Bestände bestätigen |
| Operationen | Isolierter Import, Reviewpersistenz/-export, FTS5-Indexjob und Queryausführung einzeln autorisieren; Ressourcenbudget festlegen |
| Rechte | Verantwortlicher, C16-Principal/Kursscope, Source-/Reviewgrants, `real_reviews_enabled` und Freigabebeleg; kein UIerzeugtes Recht |
| Datenhaltung | Zugriffskreis, 0700/0600, Aufbewahrung, Widerruf und Löschentscheidung |
| Gold/Queries | Menschliche Originalreferenzen, unabhängiger Querykatalog samt relevanten Regionen und Graden, Poolumfang/-vollständigkeit |
| Messung | k, FTS5-Konfiguration/Generation, Wiederholung/Neustart und begrenzter Abnahmeumfang vor Messung festlegen |

Erst danach vorhandene C23-/C24-/Search-Verträge verwenden. B1 erlaubt höchstens
16 Queries pro Dataset: die 20 leeren Arbeitsaufträge sind keine direkt
importierbare B1-Datasetdefinition; bestätigte Fragen später passend bündeln.
Dokumentübergreifende und Quellen-/Seitenfragen können Menschen zusätzlich bis zur
Obergrenze 40 definieren. Keine reale Indexierung oder Query ausgeführt, keine
Precision-/Recall-/MRR-/nDCG-/Hit-Rate berechnet. Produktivimporte, externe Dienste,
Originalveröffentlichung und automatische Goldbestätigung bleiben ausgeschlossen.

## Tatsächliche technische Validierung und Lifecycle

Python 3.12.12, Pydantic 2.13.4, PyMuPDF 1.28.2, Pytest 9.1.1, Ruff 0.16.0;
vorhandene Umgebung, keine Installation oder Downloads. Abschließender Lauf:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
python -m pytest -q -p no:cacheprovider tests/test_dev03f_review.py \
  --basetemp=/tmp/dev03f-tests-handoff
```

**25 passed / 0 failed / 0 skipped**, 39,29 s. Nur synthetische PDFs und
ausdrücklich synthetische menschliche Testmarker; keine tatsächlichen Reviews
oder Realqualitätswerte. Geprüft: Auswahl/Kontrollen, gleiche wiederholte
Paketdigests, tatsächliche Workertextbindung, getrennte Originalansicht, escaped
Vergleich, private Rechte/Hashes/No-Overwrite, Pflichtbelege/Attestation,
unbekannte IDs/Schema/Versionen, Duplikate, fehlende Referenzen, unentscheidbare
Formeln, begründete Äquivalenz, unveränderte Vorgänger und manipulierte Bindungen.
Frühere Entwicklungsläufe derselben neuen Datei: 20 passed (26,68 s), danach
25 passed (37,71 s und 37,76 s); überlappende Läufe, nicht addieren. Der letzte
Lauf enthält die endgültige C13-Vergleichsdarstellung.

Ruff Check und Format Check für `scripts/acceptance/dev03f_review.py` und
`tests/test_dev03f_review.py` erfolgreich; `git diff --check` ebenfalls. Keine
erneute allgemeine DEV-03A/B/C-, Gesamtrepository- oder UI-Suite: Parser,
Backendpersistenz und UI wurden nicht geändert. Die neue Erfassung wird mit den
tatsächlichen integrierten Pydanticverträgen geprüft. Der echte Paketlauf prüft
zusätzlich alle 48 Dateieinträge einschließlich Manifest, die exakte Inventarliste,
Paket-/Exporterhash, unveränderte E-Artefakte und Originale sowie private Rechte.

Dauerhafter Code, Tests und dieser Handoff liegen in
[F1-PR #134](https://github.com/rf-data/Personal_Assistant/pull/134) gegen master;
der PR ist offen. Project #1 enthält ihn beim abschließenden Livecheck genau
einmal mit Status `Backlog`; keine manuelle Project-/Workflowänderung. Die drei
PR-Dateien enthalten ausschließlich Code, synthetische Tests und diesen Handoff.
Commit-Hooks erfolgreich. Gitstatus für getrackte Dateien sauber; lediglich der
bekannte eigene Ruffcache ist ignoriert. Beide primären Checkouts bleiben sauber.
Solange der PR offen ist, bleiben der eigene
Branch `feat/dev03f-human-review` und sein Worktree erhalten. Vollständiger
Integrationsabschluss steht damit aus. Keine fremden, historischen oder
MAINT-Branches/Worktrees und keine privaten Review-/E-Daten wurden bereinigt.
