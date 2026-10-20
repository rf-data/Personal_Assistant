# C23-06: Technische Vorbereitung, keine fachliche Realabnahme

18.10.2026. Endgültige Basis: Master
`d654f0580f6c5d6aa5698f33dc5c93dec5ba66d5`. C23-02A/B/C (#76–#78), C23-03 (#79),
C23-04 (#80) und inzwischen C23-05 (#81) sind gemergt. Der Auftrag begann auf
`1254c2c`; damalige Testbefunde behalten unten ihren expliziten Basisbezug.

**Ergebnis: Der technische Vorbereitungsumfang ist abgeschlossen. Die fachliche
C23-06-Abnahme bleibt blockiert.** Der Auftraggeber hat ausschließlich bereits
versionierte Fixtures und HTML-Snapshots für technische Prüfungen freigegeben.
Zusätzliche lokale Realbundles, private Daten und unabhängig bestätigtes Gold sind
nicht freigegeben/vorhanden. Keine Downloads, LLM-/Embedding-/Qdrantaufrufe,
Originalmigration, automatische Quellenpublikation oder Deployment.

- [Tatsächliches Inventar und Auswahlbegründung](c23_corpus_inventory.md)
- [Goldschema, Metriken, Reviewprozess und Grenzen](c23_gold_schema.md)
- [Korpusmanifest](c23_06/corpus_manifest.v1.json), [Reviewaufträge](c23_06/gold_references.v1.json)
- [Maschinenreport](c23_06/evaluation_report.v1.json), [Inventarreport](c23_06/corpus_inventory.v1.json),
  [Hashmanifest](c23_06/manifest.json), [Kurzfassung](c23_06/summary.md)

## Tatsächlicher Lauf und Ergebnis nach Format

Der CLI-Lauf liest neun explizit ausgewählte versionierte Rohdateien, prüft ihre
Hashes und erzeugt ausschließlich Metadatenreports. Keine realen Raw-/Receipt-/
Parsed-Bundles werden konstruiert, keine historische Parserrevision aus HEAD
abgeleitet und kein realer ContentStore geöffnet. Die drei Notes-Identitäten
kommen aus dem vorhandenen Discoverymodell; unbelegte Assignment-IDs bleiben null.

| Format | Verfügbare reale Rawdateien | Freigegebene vollständige Realbundles | Bestätigtes Realgold / evaluierbarer Nenner | Fachliche Abnahme |
| --- | ---: | ---: | --- | --- |
| HTML | 5 | 0 | 0 / 0, fünf Pending-Reviewaufträge | blockiert |
| PDF | 0 | 0 | 0 / 0 | blockiert |
| Eigenständiger Code | 0 | 0 | 0 / 0 | blockiert |
| SRT | 0 freigegeben | 0 | 0 / 0 | D06/D07 blockiert |
| TXT | 0 | 0 | 0 / 0 | Originalbundle fehlt; Nullzeitvertrag technisch unterstützt |

Fünf reale HTML-Rohsnapshots, vier synthetische Rohfixtures und sechs ausgewiesene
Realdatenlücken ergeben **15 Korpuseinträge**. **0 bestätigte Referenzen,
5 `pending_review`, 0 rejected**; zehn Einträge ohne Reviewauftrag, alle 15 ohne
bestätigtes Gold. Die Pendingeinträge sind leere Reviewaufträge, keine abgeleiteten
Goldtexte. **Sämtliche 80 Herkunft-/Format-/Dimensionsgruppen haben Nenner 0 und
Rate null.** Das ist keine Null-Prozent-Parsingqualität und keine Formelbewertung.

Die Auswahl deckt drei Kurse und verschiedene HTMLgrößen ab, aber keine
repräsentative fachliche Stichprobe der CS50-Materialpipeline. Bilder, Tabellen,
Formeln, Unicode, Code und Cuezeiten werden in den bestehenden synthetischen
Vertragstests geprüft; daraus folgt kein Urteil über reale Vollständigkeit.

## Reproduzierbarer Aufruf

Vorhandene Umgebung ohne Installation/Sync:

```sh
TASK_PYTHON=/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python
PYTHONPATH=/usr/lib/python3/dist-packages "$TASK_PYTHON" -m scripts.cs50_material_evaluation \
  --corpus docs/cs50/evaluation/c23_06/corpus_manifest.v1.json \
  --gold docs/cs50/evaluation/c23_06/gold_references.v1.json \
  --root repository="$PWD" --actor evaluation_operator \
  --course cs50x --course cs50_python --course cs50_ai \
  --output /tmp/c2306-corpus-current
```

Output muss neu und außerhalb aller Inputwurzeln/-dateien liegen. Exit 0 bedeutet
erfolgreiche technische Reporterzeugung, **keine** fachliche Freigabe; 1 mindestens
ein ausgeführter Vergleich fehlgeschlagen, 2 Input/Zugriff/Output abgewiesen.
Gesonderte Ausgaben sind wiederholbar; Reportdigest bindet den kanonischen Body,
das zuletzt erzeugte Manifest die exakten Dateibytes. Relative Korpusinputs und
pathfreie Reportmetadaten erlauben Wiederholung aus einem anderen Checkout.

Aktuell ohne Store. Ein späterer expliziter `--store`-Pfad öffnet ausschließlich
einen vorhandenen read-only Store. Der Runner startet weder Import noch Recovery.
Öffnen eines unklaren WAL-/Quarantänezustands bleibt gemäß bestehendem Storevertrag
gesperrt. Volltexte, private Workspaces, Credentials und Produktionsartefakte
gehören nicht in die versionierten Beispiele.

## Testumgebung und tatsächliche Nachweise

Python **3.12.12**, Pydantic **2.13.5**, SQLite **3.50.4**, System-Pytest **7.2.1**,
BeautifulSoup **4.11.2** im tatsächlich verwendeten `PYTHONPATH`, Ruff **0.16.0**.
Projekt-Pytest 9 war nicht lokal nutzbar, PyMuPDF fehlt. Keine Dependencies
installiert oder heruntergeladen. Die Hauptumgebung findet System-SymPy über
`PYTHONPATH`; der unverändert isolierte C11-Worker (`python -I`) findet es dagegen
nicht. Seine Antwort `sympy_unavailable/undetermined` wird nicht als mathematische
Fehlrekonstruktion interpretiert oder durch größere Ressourcenlimits übergangen.

Gemeinsames tatsächliches Pytestpräfix für alle folgenden Aufrufe:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

### Neue Frameworktests

```sh
-q --disable-warnings tests/test_cs50_material_evaluation.py --basetemp=/tmp/c2306-final
```

**38 passed / 0 failed / 0 skipped**, 10,37 s auf Ausgangsbasis `1254c2c`.
Auf der endgültigen Basis wurden alle 38 Fälle im gemeinsamen Lauf unten erneut
erfolgreich ausgeführt. Die Tests verwenden tatsächliche Pydanticmodelle, Rawbytes, vorhandene
B-Gates, C10/C11, eine direkte C13-HTMLinventur und separate temporäre SQLite-
Stores. Keine reinen Mocks ersetzen Roundtrip-/Hash-/Sourceprüfungen.
Synthetische erwartete Texte sind handgeschriebene Testkonstanten; Zielpointer
verknüpfen sie mit den vorhandenen Blockmodellen. Sie sind keine unabhängigen
realen Goldreferenzen und werden nicht in den realen Korpusreport eingemischt.
Reviewfeldwerte dieser synthetischen Testfälle sind ausdrücklich Testmarker,
keine realen Reviewer oder Behauptungen menschlicher Prüfung.

Geprüft: vollständige/unvollständige Bundles und Origin/Permission, fehlende
Reviewbelege, getrennte Gruppen und leere Nenner, Exact/Unicode/Whitespace,
Codeeinrückung, Tabellen-/Formelvergleiche, C11-Undetermined-Vertrag,
Seiten-/Zeitlocatoren, überlappende SRT-Cues, Source-/Rawversionskonflikte,
keine Promotion synthetischen Golds, unveränderte Rohdateien, vorhandener
Store-Byte-Roundtrip/Idempotenz, Outputhashes/No-Overwrite und fehlerhafte Inputs.
Der synthetische PDFmodelltest baut vorhandene PDF-v2-Contentverträge auf;
er ist **kein ausgeführter nativer PDFparser**.

### Bestehende C23-Persistenz- und Read-Verträge auf Ausgangsbasis 1254c2c

```sh
-q --disable-warnings \
 tests/test_content_store_models.py tests/test_content_store_artifacts.py \
 tests/test_content_store_store.py tests/test_content_store_adapters.py \
 tests/test_content_store_recovery.py tests/test_content_store_concurrency.py \
 tests/test_content_store_integrity.py tests/test_content_store_backup.py \
 tests/test_content_store_limits.py tests/test_content_store_reimport.py \
 tests/test_content_store_inventory.py tests/test_content_read_contracts.py \
 --basetemp=/tmp/c2306-content
```

**239 passed / 1 failed / 0 skipped / 0 setup errors**, 323,96 s, 240 Fälle.
Der einzige Fehler ist der bereits in #81 mit unverändertem Master reproduzierte
C23-03-Node `test_retry_is_recoverable_after_second_interruption[binding]`:
`inspect_recovery` sortiert nichtcommittete einschließlich rejected Runs nach UUID,
der Test verwendet `[0]` als vermeintlichen Retry. Keine Änderung am Store oder
dieser Testannahme im Evaluationspaket; keine grüne Gesamtsuite behauptet.

### Bestehende C10/C11/C13-/Transcript-/HTMLprüfungen auf Ausgangsbasis 1254c2c

```sh
-q --disable-warnings tests/test_math_formula_evaluation.py \
 tests/test_official_transcript_import.py tests/test_cs50_visual_inventory.py \
 tests/test_cs50_material_quality.py tests/test_cs50_material_html.py \
 tests/test_cs50_material_html_semantics.py --basetemp=/tmp/c2306-existing
```

**177 passed / 21 failed / 1 skipped / 151 setup errors**, 24,15 s, 350 Fälle.
Diese vorhandenen Runtime- und Testmodule sind gegenüber dem eingefrorenen Master
unverändert; der Lauf importiert das neue Evaluationspaket nicht. Es wurde kein
zusätzlicher identischer Baselinelauf als separater Erfolg ausgegeben.

- **11 C11-Fehler**: neun isolierte Symbolikfälle, vollständige optionale Gold-
  Entscheidungsmatrix und Konstantenfall; Worker findet SymPy nicht. Das lokale
  Elternprozess-Preflight allein genügt nicht. Keine Änderung an C11-Grenzen.
- **6 bekannte TXTfehler**: `None` aus dem vorhandenen Importer gegen das weiterhin
  floatpflichtige TranscriptSegment auf dieser Basis. Dieser Befund ist historisch; nach Integration von #81 sind diese Fälle erneut grün geprüft.
- **2 C13-PDF-Fehler und 151 Setupfehler**: PyMuPDF fehlt; 57 C13-Setups und alle
  94 C10-Setups benötigen die gemischte HTML/PDFfixture. Dadurch sind auch diese
  HTMLparameter nicht ausgeführt. Die direkte C13-HTML- und C10-B-Gateprüfung
  innerhalb der neuen Tests bleibt ein eigener begrenzter technischer Nachweis.
- **2 bekannte HTML-Unicode-Fehler**: beide Wrapperfälle von
  `test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
  (`héllo` → `h√©llo`) in der vorhandenen BeautifulSoup-Umgebung.
- **1 Skip**: optionaler Original-Notes-Workspace nicht bereitgestellt; kein Download
  oder synthetischer Ersatz als angeblich realer Originaltest.

Pytest-7-AST-Warnungen unter Python 3.12 zählen nicht als Skips. Keine komplette
grüne Regression, nativer PDF-Erfolg, realer Persistenz-/HTTP-Roundtrip oder
fachlicher HTML-/Formelqualitätswert wird aus diesen Laufzahlen abgeleitet.

## Reale Befunde, Lücken und vorgeschlagene Folge-Issues

Im freigegebenen realen Korpus sind **keine neuen fachlichen Parsingfehler
nachgewiesen**, weil unabhängige Referenzen und vollständige Bundles fehlen.
Folgende Vorschläge sind keine automatisch angelegten Issues:

| Vorschlag | Klasse / konkreter Nachweis | Nächster begrenzter Schritt |
| --- | --- | --- |
| Real-CS50-Bundles und unabhängige Reviewfenster bereitstellen | Daten-/Evaluationslücke: fünf Rawdateien, null vollständige Realbundles, fünf Pendingaufträge | Untenstehenden Übergabeplan pro Source erfüllen, danach technische Gate-/Goldevaluation |
| HTML-v2 UTF-8-Code ohne Encodingmetadaten regressionsfest machen | Bestehender synthetischer Parser-/Umgebungsbefund, zwei genaue Wrapper-Nodes | Byte-/Encodingursache im separaten Parserfix nachweisen; keine reale Fehlerquote erfinden |
| C23-03-Recoverytest nach Retryidentität auswählen | Vorhandene Test-Reihenfolgeannahme, kein nachgewiesener Persistenzverlust | Wiederaufnahmebeleg/`retry_of` statt erstem UUIDsortierten Eintrag auswählen und Prozessfall wiederholen |
| Optional-SymPy-Probe an isoliertem Worker ausrichten | Evaluationsumgebung: Elternprozess findet Paket, `-I`-Worker nicht | Vorhandene freigegebene Umgebung konsistent bereitstellen; weder Unknown als Incorrect zählen noch Limits abschwächen |

## Konkreter Übergabe- und Reviewplan

1. Operator benennt **je Source** exakte zulässige Dateien und Evaluationsrechte;
   keine pauschale Scanwurzel. Vor historischer SRTübernahme zusätzlich separater
   D06-Entscheid über neue kanonische Zielpfade, Originale/Receipts unverändert.
2. Vollständiges bestehendes B-Bundle bereitstellen: Raw mit SHA/Größe,
   ursprünglicher Material-/Adapterplan mit Course/Section/Lecture/Resourcebindung,
   unverändertes Parsed-/Transcript-JSON, completed Receipt samt Input-/Outputhashes,
   ausdrücklich belegte damalige Implementierungs-/Parserrevision und Konfiguration,
   referenzierte lokale Bildartefakte, gegebenenfalls vorhandener Qualityreport.
   Fehlende Belege nicht aus ähnlichen Dateien oder aktuellem HEAD rekonstruieren.
3. Scopefreigabe und unabhängiger Reviewer werden tatsächlich benannt. Reviewstellen
   **am Original** auswählen: Textreihenfolge, Listen/Überschriften, exakte Codezeilen,
   Tabellenzellen, Formeln, Bildpositionen und SRTzeiten. Lange/kurze Dokumente und
   schwierige Regionen je Format begründet aufnehmen; Vorannotation bleibt Pending.
4. Bestehenden read-only B-Inventar-/C10-Gate zuerst ausführen. Erst aus gültigem
   Bundle SourceVersion/Hashes beziehen und Gold an genaue Originalstellen sowie
   die zu bewertenden bestehenden Payloadpointer binden. Ein Pointer ist kein Goldtext.
   Originalannotation, Reviewer, Reviewbeleg und Datum unabhängig dokumentieren;
   Fehler/Mehrdeutigkeiten offenlassen. Kein Modell darf Gold erzeugen/bestätigen.
5. Korpus-/Golddatensatz bewusst neu versionieren, nur mit der konkret freigegebenen
   `evaluation`-Scopeerklärung ausführen. C11 nur für bestätigte Formelpaare, C13
   gegebenenfalls separat für Bild-/Seitenbelege. Roh-/Parsedhashes, SourceVersion,
   Metriknenner, nicht evaluierbare Fälle und Fehlstellen vor/nach Lauf abgleichen.
6. Persistenz-/HTTPabnahme bleibt separat: ausschließlich ausdrücklich freigegebener
   isolierter Teststore, Originalpayload/IDs/Locatoren, idempotenter Wiederimport
   sowie autorisierte Leseprojektion vergleichen. Keine automatische Produktiv-
   publikation. Bei fehlender Freigabe bleibt dieser Teil `not_checked`.
7. Reviewer/Operator entscheiden abschließend pro Format und Dimension über einen
   begrenzten fachlichen Releaseumfang. Volltextintegrität allein genügt nicht.
   C23/C26 werden nicht durch einen Framework-PR oder synthetische Tests geschlossen.

## Begrenzte Konsolidierung nach #80

`content_store_implementation.md` hat wieder genau eine Hauptüberschrift und
einen aktuellen Statusabschnitt. Die bisherigen 03-/04-Nachträge sind explizit
historisch; bestehende Überschriftentexte/Anker und Abnahmen bleiben erhalten.
HTTP/Pagination werden nicht mehr pauschal als aktuell ausstehend bezeichnet.
Der Umsetzungsplan trennt aktuellen Merge-/Freigabestatus vom datierten ursprünglichen
Plan und den erhaltenen Nachträgen. Keine Verträge, Gatebedingungen, SQLschemas
oder alten Testergebnisse wurden redaktionell umgedeutet oder addiert.

## Abschließender Prüfvermerk

Während der Arbeit wurde C23-05 gemergt. Vor PR-Erstellung wurde der eigene Branch
auf Master `d654f05` aktualisiert; beide vorhandenen Implementierungsnachträge
und alle bestehenden neuen Source-/Timeverträge bleiben erhalten. Danach mit
demselben tatsächlichen Pytestpräfix:

```sh
-q --disable-warnings tests/test_cs50_material_evaluation.py \
 tests/test_transcript_unknown_time.py tests/test_official_transcript_import.py \
 tests/test_knowledge_transcript_provenance.py tests/test_cs50_srt_knowledge_integration.py \
 tests/test_content_read_contracts.py --basetemp=/tmp/c2306-current-contracts
```

**163 passed / 0 failed / 0 skipped**, 38,89 s: 38 neue Frameworkfälle,
26 Unknown-Time-, 39 offizielle Importer-, 41 Knowledge-Provenienz-, fünf SRT-
Integrations- und 14 Read-Vertragsfälle. Alle sechs früheren TXT-Fehler sind auf
dieser aktuellen Basis erfolgreich, ohne dass ein realer TXTbestand freigegeben wird.

Gezielte Nachprüfung der vom Upstream-Modell-/SRT-Recoveryvertrag betroffenen
ContentStorebereiche:

```sh
-q --disable-warnings tests/test_content_store_models.py \
 tests/test_content_store_adapters.py tests/test_content_store_recovery.py \
 tests/test_content_read_contracts.py --basetemp=/tmp/c2306-current-store
```

**105 passed / 0 failed / 0 skipped**, 83,92 s. Diese Läufe überlappen mit der
vorherigen 240er-Suite und untereinander; sie werden nicht addiert. Die ältere
vollständige Suite bleibt mit ihrem einen dokumentierten C23-03-Testfehler sichtbar.

Frühere reine Entwicklungsläufe derselben Frameworkdatei mit dem gemeinsamen
Pytestpräfix und `-q --disable-warnings`, jeweils eigenem `--basetemp`:

| Basetemp | Pass / Fail / Skip / Setupfehler | Dauer |
| --- | --- | --- |
| `/tmp/c2306-new` | 6 / 3 / 0 / 16 | 5,11 s |
| `/tmp/c2306-new-second` | 25 / 0 / 0 / 0 | 9,54 s |
| `/tmp/c2306-new-third` | 26 / 2 / 0 / 0 | 10,86 s |
| `/tmp/c2306-new-fourth` | 28 / 0 / 0 / 0 | 9,77 s |
| `/tmp/c2306-new-final` | 38 / 0 / 0 / 0 | 9,35 s |
| `/tmp/c2306-release` | 37 / 1 / 0 / 0 | 10,56 s |

Diese Läufe sind keine zusätzlichen Abnahmetests. Korrigiert wurden die bestehenden
B-Einzelpfadgrenzen für explizite Plan-/Revisionsdateien, unterschiedliche Material-/
SRT-Qualityverträge, die Zeilenblockannahme im Unicode-Test und der Rollenalias
`transcript` beim Vergleich aller Snapshothashes. Die endgültigen oben genannten
Läufe prüfen die Korrekturen ohne Abschwächung des B-Gates oder von Assertions.

Ruff Check und Format Check erfolgreich für alle vier neuen Pythondateien:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check src/model_evaluation/material_evaluation.py \
 src/tools_evaluation/evaluate_materials.py scripts/cs50_material_evaluation.py \
 tests/test_cs50_material_evaluation.py
# Derselbe Dateiumfang mit format --check.
git diff --check
```

Der endgültige CLI-Lauf und eine unabhängige Wiederholung über dieselbe Python-
Schnittstelle liefern denselben validierten Reportdigest
`2d5cad3667e185dbb9346025b1ac00b91e7f86683f2b5688af2dd8380721e811`.
Die versionierten Reportdateien sind die unveränderten CLI-Ausgabebytes; das
Dateimanifest prüft ihre exakten SHAwerte. Goldschema entspricht dem tatsächlichen
Pydantic-JSONschema. Kein privater Hostroot steht in diesen Maschinenreports.
27 neue lokale Markdownverweise geprüft; alle bisherigen Überschriftentexte der
beiden konsolidierten Dokumente bleiben als Anker erhalten, beide Dokumente haben
außerhalb von Codeblöcken genau eine Hauptüberschrift. `git diff --check` ist grün.

Eigene synthetische Testroots, Caches und temporäre
Reports werden nach Abschluss entfernt; Logs bleiben außerhalb des Repositories.
Der eigene Worktree bleibt wegen des offenen PR bestehen. Andere Worktrees,
private Bestände und virtuelle Umgebungen werden nicht bereinigt.
