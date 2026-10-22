# C26-B5: Validierung, Gap-Analyse und Aufbewahrung

22.10.2026. Basis: `master` / `e581e201ef6b3d6c06aca14de845e0687d213b37`.
Umsetzung: eigener Branch `feat/c26b5-complete-week-plan`; Review ohne Merge.

## Ergebnis und Scope

Eine komplette Inventur **der belegten verfügbaren Quellen** und kontrollierte
Planung sind implementiert. Es gibt keinen Anspruch auf vollständige Live-Web-
Discovery oder Verarbeitung aller Wochenmaterialien. Die tatsächliche Erfassung
enthält 21 logische Resource-IDs und 28 Material-/Medienvarianten, einschließlich
aller fünf durch das echte Problem-Set-0-Original belegten Aufgaben.

Die Aufgabe ist ein Offline-Entwicklungsauftrag. Kein SSH, kein Download,
keine Ausführung produktiver Jobs, kein Container-/Workerstart und keine Änderung
an produktiven Daten, Mounts, VPN/HTTPS/Coolify/Traefik/DNS. Die vorhandenen
Code-Importer bleiben in B5 deaktiviert; Codeindex, PY und ZIP erreichen über
den neuen Adapter keinen Download- oder Processing-Batch, selbst mit Grants.

[Technischer Vertrag, Komponenten-/Routingmatrix und Gap-Analyse](complete_week_materials.md),
[maschinenlesbares Ressourceninventar](week0_resources.v1.json),
[maschinenlesbare Validierung](complete_week_validation.v1.json).

## Vorher-/Nachher und Originalbelege

- Vorhandene Discovery-/Materialidentitäten werden unverändert wiederverwendet.
  Neue Aufgaben-IDs folgen demselben Parent-gebundenen `ResourceCandidate`-Vertrag.
- Im eingecheckten Snapshotbestand sind 17 logische Ressourcen / 24 Varianten
  erreichbar. Die vier weiteren Aufgaben sind durch den zusätzlich ausdrücklich
  bereitgestellten Originalexport nachweisbar; insgesamt 21 / 28.
- Problem-Set-Original: 15.832 Bytes, Raw-SHA
  `0d06fb2afcfcc01f5e4e7abbc2a09e057e17fda8c11fa60e948f1f9836cb2372`,
  28 normalisierte Blöcke und zehn Links. Alle fünf Aufgaben werden als eigenständige
  Ressourcen mit Parent, Original-URL und DOM-Fundstelle erfasst.
- Notes-Original: 71.718 Bytes, Raw-SHA
  `0e9af3114adec16938b89b511337f5db717ef2e14f1a606af600d6995ce09377`,
  237 Blöcke und 34 Codeblöcke. Originalhash und exportierter Normalized-Raw-Hash passen.
- Beide echten Exporte samt vorhandenen Normalized-/Quality-Dateien bleiben bytegleich.
  Das reale B5-Testcase liest alle sechs Dateien und prüft sie vor/nach der Inventur.
- Gegen den unveränderten Aggregations-PR #149 (`58aec7d`) bestehen zusätzlich die
  echten Notes-/PSet-Projektionsprüfungen: Notes **171 Units / 34 Codeblöcke**, PSet
  **16 Units / zehn Links / fünf Aufgabenlinks**. Unit-/Block-IDs, Zeichenfenster,
  Listenbeziehungen und Codezeichen stimmen zwischen v1- und v2-Aggregation überein.
  Die Codezeichen werden zusätzlich mit den originalen HTML-`pre`-Elementen verglichen.

Damit ist der bisher wegen fehlender lokaler Exporte offene Aggregationsvergleich
in dieser **isolierten B5-Kompatibilitätsprüfung** durchgeführt. PR #149 und seine
Dokumente wurden nicht geändert oder gemergt. Es wurde weder ein bestehender
Pilotjob wiederholt noch ohne Originalplan/Receipts eine vollständige
Produktions-Quality-/Controllerkette als neu geprüft ausgegeben.

## Prüfstand und Grenzen

Python 3.12.12, bestehende Backend-venv; neue Dependencies: keine.
Alle Tests laufen offline; Socket-Verbindungen werden in den neuen Tests blockiert.
Neue Material- und Transcript-Verarbeitung verwendet ausschließlich synthetische
Bytes in neuen temporären Roots. Echte Exporte werden nur gelesen.

Die finalen Resultate und pro Modul gezählten Fälle stehen unten und in der
maschinenlesbaren Zusammenfassung. Ergebnisse überlappen und werden nicht addiert.

| Prüfumfang | Bestanden | Übersprungen | Dauer |
|---|---:|---:|---:|
| Betroffene breite Regression (12 Module) | **358** | **3** | 187,23 s |
| Finale B5-Suite einschließlich realem Export | **51** | **0** | 7,72 s |
| Finale B5-/Aggregationskompatibilität auf #149 | **85** | **0** | 20,98 s |

| Modul im breiten Lauf | Bestanden | Übersprungen |
|---|---:|---:|
| `test_cs50_week_materials.py` | 51 | 0 |
| `test_cs50_week_pilot.py` | 12 | 0 |
| `test_cs50_multiformat.py` | 32 | 0 |
| `test_cs50_material_quality.py` | 94 | 0 |
| `test_cs50_material_processing.py` | 8 | 0 |
| `test_cs50_material_e2e.py` | 5 | 0 |
| `test_cs50_material_html.py` | 7 | 0 |
| `test_cs50_material_html_semantics.py` | 17 | 1 |
| `test_cs50_material_mapping.py` | 1 | 0 |
| `test_cs50_media_plan.py` | 38 | 0 |
| `test_cs50_code_zip.py` | 54 | 0 |
| `test_cs50_material_pdf_v2.py` | 39 | 2 |

Abgedeckt sind Inventur, Parent-/Aufgabenbeziehungen, Klassifikation,
Discovery-/Acquisition-Trennung, irreführende Rollen/Formathints und kodierte
PY-/ZIP-Pfade, Verbot von Codeindextraversierung, fehlende Freigaben/Hashes,
Datei-/Gesamt-/Material-/Kapazitätslimits, Guardian- versus Parser-RAMgrenze,
Symlinks und falsche Exporte, vorhandene Material-/Transcript-Reuseketten,
Konfigurationswechsel, Fehlerisolation, tatsächliche PDF-v2-Verarbeitung beider
PDF-Rollen, Zeitstempel/Nullzeiten, konsistente Reports, CLI ohne Schreibzugriff
und Controller-Root `jobs` mit regulärem `jobs/jobs/...`.

Entwicklungsbefunde, anschließend korrigiert:

| Lauf | Ergebnis / Ursache |
|---|---|
| erste neue Suite | 39 passed, 1 failed: Test erwartete global null Probleme, obwohl unselektierte unbekannte/Google-Slides-Ressourcen eigene Blocker haben; Test auf ausgeschlossene Code-Ressourcen eingegrenzt |
| erste Material-/Transcript-Integration | 42 passed, 2 failed: Test erwartete `completed` statt des vorhandenen Transcript-Adapterstatus `processed`; Test an bestehenden Vertrag angepasst |
| erster echter Exporttest | 45 passed, 1 failed: fehlender `Path`-Testimport; ergänzt |
| breiter Zwischenlauf | 314 passed, 1 skipped, 232,94 s |
| PDF-/B5-Zwischenlauf | 89 passed, 2 skipped, 25,66 s |
| finale gezielte B5-Suite | 51 passed, 20,16 s |
| erste #149-Kompatibilität | 80 passed, 19,76 s |
| finale #149-Kompatibilität | 85 passed, 18,04 s |
| letzte Status-/Reuse-Darstellung | 51 passed, 7,72 s; #149-Kompatibilität 85 passed, 20,98 s |

Der breite Abschlusslauf deckt die betroffenen Module ab, nicht das gesamte
Repository. Der ältere Notes-Originaltest verlangt ein anderes Legacy-Receiptlayout
und bleibt ohne dieses optionale Inputbundle übersprungen. Beide optionalen
PDF-Originale fehlen; es gibt keine neuen PDF-Downloads. Diese Skips sind kein
bestandenes Originaldaten-Resultat. Die beiden echten v2-HTML-Exportprüfungen
wurden dagegen im Kompatibilitätslauf tatsächlich ausgeführt und bestanden.

Zusätzlich: Ruff Check/Format für alle vier neuen Python-Dateien, JSON-Validierung,
Dokumentationslinkprüfung, `git diff --check` und reguläre Commit-Hooks.
Keine Schutzprüfung wurde für den Commit übersprungen.

## Reproduktion

Aus der B5-Arbeitskopie, mit der vorhandenen Python-3.12-Umgebung:

```sh
CS50_WEEK0_QUALITY_EXPORT=/explicit/local/cs50_quality_review \
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm \
python -m pytest -q tests/test_cs50_week_materials.py \
  --basetemp=/dev/shm/c26b5-handoff-tests -p no:cacheprovider
```

Ohne den expliziten Exportpfad wird ausschließlich das neue echte Exporttestcase
übersprungen; synthetische Tests bleiben verfügbar. Keine automatische Suche
in Pilotroots oder privaten Stores. Der Request für die reale Inventur ist im
[technischen Vertrag](complete_week_materials.md#cli-und-reproduktion) beschrieben.

Für die #149-Kompatibilitätsprüfung wurde ein eigener Checkout des exakten PR-Heads
angelegt und ausschließlich um die vier neuen B5-Dateien ergänzt. Darin:

```sh
CS50_WEEK0_QUALITY_EXPORT=/explicit/local/cs50_quality_review \
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm \
python -m pytest -q tests/test_cs50_week_materials.py tests/test_cs50_html_projection.py \
  --basetemp=/dev/shm/c26b5-final-compat -p no:cacheprovider
```

## Verbleibende Voraussetzungen

- Vier Aufgaben sind als Quellen bekannt, ihre vollständigen Inhalte noch nicht
  lokal bereitgestellt. Alle fünf neuen Child-IDs brauchen die explizite,
  versionierte Integration in den bisherigen C18-Discoverygraphen.
- Echte PDF-/SRT-/TXT-/Audio-/Video-Dateien und ihre produktiven Kapazitätsanforderungen
  wurden nicht beschafft. Referenzen sind keine erteilten Beschaffungsrechte.
- Prozessierte Produktionsartefakte werden nur mit ausdrücklich benannten,
  unveränderten Receipts, Plan und Quellenfreigaben zur Reuse-Prüfung übernommen.
- Der Wochenadapter bereitet bestehende Batches vor; er ist kein neuer Runner,
  Execution-Token oder Ersatz für C16-Authentifizierung, Queue-/Guardianlimits und
  die spätere tatsächliche Kapazitätsprüfung.
- Medien benötigen den bestehenden separaten Zweck-/Evidence-Plan. Keine automatische
  Shorts-/YouTube-/Whisper-/Providerverarbeitung und kein Codeimport.
- Als Nächstes ist ein kleiner expliziter Scope samt Source-/Reuse-Belegen zu
  entscheiden; die Aufgaben-C18-Graphintegration erfordert ein eigenes Review.

## Git, Speicherproblem und Aufbewahrung

Das lokale Dateisystem meldet weiterhin ENOSPC für manche Git-/Checkoutschreibvorgänge.
Der neue Branch und vollständige isolierte Checkout mit eigener Git-Datenbank liegen
unter `/dev/shm/c26b5-week-i1qs65n0/repo`. Der separate #149-Kompatibilitätscheckout
liegt unter `/dev/shm/c26b5-aggregation-compat-hjcgah1t/repo`. Beide sind flüchtig.

Der Review-Branch sowie ein verifiziertes Git-Bundle und Quellarchiv unter
`Personal_Assistant-c26b5-week-plan` sichern die Änderungen dauerhaft. Prüfresultate
und Quellfingerprints werden im Review-Branch dokumentiert. Master und fremde
Worktrees bleiben unangetastet. Kein Merge oder Auto-Merge; eigene Branch- und
Checkout-Artefakte bleiben wegen des offenen Reviews erhalten. Die Dokumente sind
im Review-Branch und noch nicht als in Master integriert auszugeben.
