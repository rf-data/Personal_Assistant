# C26-A HTML-Aggregation: Validierung und Reviewstand

Stand: 22.10.2026. Basis: `master` / `e581e201ef6b3d6c06aca14de845e0687d213b37`.
Status: lokal implementiert und offline geprüft; Review-PR ohne Merge.
Der echte Week-0-Pilotvergleich bleibt ausdrücklich ausstehend.

## Ergebnis und untersuchte Module

Das bestehende `MaterialUnit`-Mapping und der bestehende Lecture-Handoff sind
um DOM-gebundene Linkreferenzen, vollständige typisierte Listenpfade und technische
Integritätsprüfungen erweitert. Mehrdeutige Links bleiben ausdrücklich unresolved.
Die bisherige Ausschlussregel wird gemeinsam verwendet; Referenz-/Listencontainer
werden nicht zu zusätzlichem Text. Parser, NormalizedDocument, Receipt, Plan,
Storage-/Processing-Logik und Knowledge-Pipeline bleiben unverändert.

Untersucht wurden außerdem die HTML-v2-Semantiktests, die fünf Notes-/Assignment-
Snapshots des Fixture-Manifests, Materialverträge, Mapping-, Quality-, Processing-,
E2E-, Code-, PDF-v2-, Code-ZIP-, Multiformat- und Week-Pilot-Tests sowie die
bestehende CLI und [der C10-Vertrag](../../cs50/contracts/material_quality.md).
Schema, Zuordnung, Findings, Handoff-Auswirkungen und Grenzen stehen im
[technischen Vertrag](../../cs50/contracts/html_aggregation_v2.md).

## Abgeschlossener Testlauf

Python **3.12.12**, bestehende Backend-Umgebung, keine neuen Dependencies.
Final: **314 passed, 5 skipped, 0 failed, 0 errors**, 129,14 Sekunden.
Eine erwartete `zipfile`-Warnung stammt aus dem vorhandenen ZIP-Duplikat-Negativtest.
Dies ist die betroffene Regression, keine Behauptung eines vollständigen Repository-Tests.

| Testmodul | Bestanden | Übersprungen |
|---|---:|---:|
| `test_cs50_html_projection.py` | 32 | 2 |
| `test_cs50_material_contracts.py` | 4 | 0 |
| `test_cs50_material_html.py` | 7 | 0 |
| `test_cs50_material_html_semantics.py` | 17 | 1 |
| `test_cs50_material_quality.py` | 94 | 0 |
| `test_cs50_material_mapping.py` | 1 | 0 |
| `test_cs50_material_processing.py` | 8 | 0 |
| `test_cs50_material_e2e.py` | 5 | 0 |
| `test_cs50_material_code.py` | 9 | 0 |
| `test_cs50_material_pdf_v2.py` | 39 | 2 |
| `test_cs50_code_zip.py` | 54 | 0 |
| `test_cs50_multiformat.py` | 32 | 0 |
| `test_cs50_week_pilot.py` | 12 | 0 |

Die fünf Skips betreffen ausschließlich nicht bereitgestellte optionale Originale:
beide neuen Week-0-Exporte, den älteren Python-Notes-v1-Originaltest sowie zwei
optionale PDF-Originaltests. Sie sind keine bestandenen Originalprüfungen.
Die neuen Tests decken mehrere Links/Absatz, Anker desselben und anderer Dokumente,
gleiche Linktexte an verschiedenen DOM-Positionen, mehrere Fenster, drei
Listenebenen, sieben synthetische Schritte mit fünf untergeordneten Aufgaben,
Start-/Wert-/Reversed-Nummerierung, mehrere Absätze/Codeblöcke pro Item,
Mehrdeutigkeit, defekte Projektionen/Eltern/Tiefen, Codeabdeckung und v1/v2-
Roundtrips ab. Bestehende v1-Berichtsbeispiele bleiben lesbar.

Reproduzierbarer Abschlusslauf aus dem isolierten Checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest -q \
  tests/test_cs50_html_projection.py \
  tests/test_cs50_material_contracts.py \
  tests/test_cs50_material_html.py \
  tests/test_cs50_material_html_semantics.py \
  tests/test_cs50_material_quality.py \
  tests/test_cs50_material_mapping.py \
  tests/test_cs50_material_processing.py \
  tests/test_cs50_material_e2e.py \
  tests/test_cs50_material_code.py \
  tests/test_cs50_material_pdf_v2.py \
  tests/test_cs50_code_zip.py \
  tests/test_cs50_multiformat.py \
  tests/test_cs50_week_pilot.py \
  --basetemp=/dev/shm/c26a-reviewed-final -p no:cacheprovider \
  --junitxml=/dev/shm/c26a-reviewed-final.xml
```

Weitere Checks: Ruff Check und Format für alle sieben geänderten/neuen Python-
Dateien, `git diff --check`; direkte Baselineprüfung mit dem unveränderten
Master-Mapping. Die [maschinenlesbare Zusammenfassung](html_aggregation_validation.v1.json)
enthält Testzahlen und Quellfingerprints.

Entwicklungsläufe, ohne Ergebnisse zu addieren:

| Lauf | Ergebnis / Korrektur |
|---|---|
| erster bestehender Regressionstest | 113 Setup-Errors: ENOSPC beim Schreiben von Faker-Bytecode in die vorhandene Umgebung; mit `PYTHONDONTWRITEBYTECODE=1` behoben |
| bestehende Regression danach | 112 passed, 1 skipped |
| neue Unit-Tests, erster Lauf | 5 passed, 21 failed, 2 skipped: Testhelper koppelte Projektions-Unit-Tests an fehlende Discovery-Provenienz synthetischer Parserfixtures; Scope korrigiert |
| neue Projektionstests danach | 26 passed, 2 skipped |
| erster breiter Lauf | 265 passed, 2 failed, 5 skipped: fehlender Testimport `ArtifactReceipt`; korrigiert |
| ergänzte Projektions-/Integrationstests | 29 passed, 2 skipped |
| nach DOM-Indizes und v1-Serialisierung | 124 passed, 2 skipped |
| finaler breiter Lauf | 314 passed, 5 skipped |
| letzte Projektionstests nach Ergänzung der optionalen Original-Assertions | 32 passed, 2 skipped |

## Vergleich mit der unveränderten Master-Aggregation

Die bisherigen `map_material`- und Ausschlussfunktionen wurden direkt aus dem
Basiscommit geladen. Die HTML-Parserdatei wurde gegen diesen Commit bytegleich
geprüft. Die folgende Tabelle betrifft vorhandene eingecheckte Fixtures, nicht
die entfernten beiden Pilotdateien:

| Fixture | Blöcke | Codeblöcke | Units vorher → nachher | Ausschlüsse | Links / direkt projiziert |
|---|---:|---:|---:|---:|---:|
| CS50x Notes 0 | 660 | 15 | 191 → 191 | 466 | 52 / 35 |
| Python Notes 5 | 111 | 16 | 82 → 82 | 29 | 16 / 10 |
| Python Indoor Voice | 40 | 6 | 30 → 30 | 10 | 7 / 7 |
| AI Notes 1 | 268 | 3 | 206 → 206 | 52 | 9 / 9 |
| AI Shopping | 93 | 4 | 63 → 63 | 30 | 22 / 22 |

Alle **572** kanonischen Fenster behalten Unit-ID, Block-ID, Reihenfolge,
Zeichengrenzen und Text. Damit bleiben auch alle **44** enthaltenen Codeblöcke
zeichengetreu. Alle **106** Linkblöcke bleiben im Dokument; 83 sind direkt
projiziert, die übrigen 23 ausdrücklich inventarisiert. Die bestehenden Raw-
Fixtures wurden nicht verändert.

[Baseline-Fingerprints](../../../tests/fixtures/material_quality/html_projection_baseline.v1.json)
binden Raw-Bytes und exakte Zeichenfenster an diesen Vergleich. Die neuen Tests
vergleichen gegen diese festen, mit dem Master-Code ermittelten Fingerprints.
Bewusste Unterschiede: v2-Versionen und neue Metadaten/Finding-Codes; bei offener
Zuordnung gegebenenfalls `passed_with_warnings` statt eines rein informativen
Reports. Text-/Codeauswahl und Struktur-Ausschlüsse bleiben gleich.

## Echte Week-0-Dateien: noch nicht lokal geprüft

Der Benutzer hat bestätigt, dass die Originale und Exportkopien ausschließlich im
laufenden Hetzner-Backendcontainer unter `/app/data/cs50_pilot_week0_02/` liegen.
Die sechs Dateien unter `reports/quality_review_export_01/material_01/` und
`material_02/` sind nicht im lokalen Arbeitskontext verfügbar. Der Benutzer hat
SSH und Downloads ausdrücklich ausgeschlossen und den Vergleich bis zur lokalen
Bereitstellung zurückgestellt. Kein Zugriff auf Host/Container wurde durchgeführt.

| Vom Benutzer berichtete Pilot-Baseline | Notes 0 | Problem Set 0 | Neuer echter Vergleich |
|---|---:|---:|---|
| Dokumentblöcke | 237 | 28 | ausstehend |
| Codeblöcke | 34 | 0 | ausstehend |
| Aggregationseinheiten | 171 | 16 | ausstehend |
| Strukturelle Ausschlüsse | 66 | 12 | ausstehend |
| Informative Findings bisher | 47 | 10 | ausstehend |
| Links | nicht vorgegeben | 10, davon 5 Aufgaben | ausstehend |

Diese Zahlen wurden nicht lokal nachgemessen. Weder Erhalt der **34 echten
Notes-Codeblöcke** noch Bestehen beider echten Dokumente unter dem neuen Gate
wird als bereits geprüft ausgegeben.

Nach lokaler Bereitstellung der sechs unveränderten Exportdateien:

```bash
CS50_WEEK0_QUALITY_EXPORT=/explicit/local/quality_review_export_01 \
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm \
python -m pytest -q tests/test_cs50_html_projection.py \
  -k optional_exact_week0_export \
  --basetemp=/dev/shm/c26a-real-week0-comparison -p no:cacheprovider
```

Diese Tests lesen nur Exportdateien: Raw-Hash, Block-/Code-/Unit-Zahlen,
unveränderte Fenster und Codezeichen, zehn Problem-Set-Links, fünf zugeordnete
Aufgabenlinks sowie Projektionsintegrität. Der vollständige bestehende
Artefakt-Gate-Lauf benötigt zusätzlich den zugehörigen geprüften Plan und Receipt;
diese werden nicht aus einem alten Quality-Report erfunden. Keine Originaldatei
wird repariert, erneut verarbeitet oder überschrieben.

## Risiken, Review und Aufbewahrung

- Der echte Week-0-Vergleich bleibt offen; der PR enthält dafür zwei klare Skips.
- Referenzen sind Beziehungen zum Quellblock; keine behaupteten Inline-Zeichenoffsets.
  Mehrdeutige DOM-Fragmente bleiben unresolved. Leere Items können aus bestehender
  Normalisierung keine sichere abgeleitete Nummer liefern.
- Ein nachgelagerter Consumer muss die v2-Version ausdrücklich unterstützen.
  `passed` ist keine fachliche Richtigkeitsprüfung.
- Das lokale Dateisystem meldet ENOSPC bei Git-Refs und Checkout-Verzeichnissen.
  Die vollständige isolierte Arbeitskopie samt eigener Git-Datenbank liegt daher
  unter `/dev/shm/c26a-html-z3z9rqba/repo` auf `feat/c26a-html-projection`.
  Sie ist flüchtig; der Review-Branch und eine lokale Bundle-/Source-Archiv-Sicherung
  sichern die Arbeit dauerhaft. Der angefangene lokale Checkout unter
  `Personal_Assistant-c26a-html-projection` dient zur Aufbewahrung dieser Sicherung.
  Fehlgeschlagene Einrichtung und fremde Worktrees werden nicht bereinigt.
- Kein Merge/Auto-Merge. Eigene Branch-/Checkout-Artefakte bleiben wegen des offenen
  Reviews erhalten. Dokumente sind zunächst im Review-Branch; eine Integration
  in `master` wird erst nach dem regulären Review erfolgen.
- Keine produktiven Daten/Jobs/Verzeichnisse, Netzwerkzugänge, VPN-/HTTPS-/Coolify-/
  Traefik-Konfigurationen oder Containerzustände wurden geändert.
