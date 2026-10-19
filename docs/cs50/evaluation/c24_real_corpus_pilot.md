# C24-05-C: Pilotvorbereitung und dokumentierte Nicht-Evaluierbarkeit

18.10.2026 · Endgültige Basis `origin/master` `d2b5e05e732ef677fe8e8b4ccbb4d76c6d532e60`.
Beginn auf `87ea32f`; #87 wurde während der Veröffentlichung gemergt.
Branch `feat/c24-05c-real-corpus-pilot`.
**Vorbereitung, kein ausgeführter Realpilot und keine fachliche Freigabe.**

## Tatsächliche Voraussetzungen

| Grundlage | Beobachteter Stand | Konsequenz |
| --- | --- | --- |
| C23-06 | Technisches Inventar-/Goldframework integriert; Realabnahme offen | CorpusManifest/GoldDataset direkt wiederverwenden |
| C24-01/#83, 02/#84, 03/#85 | Integriert | Projektion und interne autorisierte FTS5-Suche vorhanden |
| C24-04/#86 | Integriert, nur FakeEmbedder/Fake-Transport | Kein freigegebener realer Vector-/Hybridvergleich |
| C24-05-A/#87 | Inzwischen integriert auf Master `d2b5e05` | Vorhandener Evaluator verfügbar; ohne bestätigte Quelle/Pool und B-Workflow kein Pilotlauf |
| C24-05-B/#88 | Offener Draft, Head `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`; **nur Architekturvorbereitung** | Keine Reviewpersistenz, Task-/Entscheidungs-API oder Review-UI implementiert |
| D07 / Realbundles / Reviewer | Keine zusätzlichen sourcebezogenen Freigaben, vollständigen Bundles oder unabhängigen bestätigten Referenzen vorgelegt | Kein Sourceonboarding, menschlicher Review oder fachlicher Metriklauf |
| D06 / historisches SRT | Unveränderte Pfadabweichung | Diese Quelle bleibt `blocked_source_binding` |

[Gemergter PR #87](https://github.com/rf-data/Personal_Assistant/pull/87) und
[Draft #88](https://github.com/rf-data/Personal_Assistant/pull/88) müssen getrennt
bewertet werden: **Der Merge des Architektur-Drafts #88 allein liefert keinen
Reviewworkflow.** C benötigt dessen tatsächlich implementierte und integrierte
Persistenz/API/UI sowie den ausdrücklich festgelegten Reviewer-/Approververtrag.
Keine Ersatzimplementierung, neuen Gold-/Reviewmodelle oder zweite Reviewoberfläche
in diesem Paket. [C24-Plan](../../planning/c24_implementation_plan.md),
[Governance/D06/D07](../../planning/governance.md) bleiben maßgeblich.

## Versionierter Metadatenumfang

- [Pilotmanifest r2](c24_05c/r2/corpus_manifest.v1.json): **unveränderter vorhandener
  CorpusManifest-v1-Vertrag**, neue ausdrücklich vorbereitende Datasetversion.
- [Leerer GoldDataset r2](c24_05c/r2/gold_references.v1.json): gleicher vorhandener Vertrag,
  null Referenzen. Keine fingierten Reviewaufträge, Reviewer oder Erwartungen.
- [Bereitschaftsbericht r2](c24_05c/r2/pilot_readiness.v1.json): gebundene Metadaten,
  fehlende Freigaben/Identitäten und Voraussetzungen; **kein**
  `RealCorpusAcceptanceReport` und kein Ersatz für dessen späteren B-Abnahmevertrag.
- [Dateimanifest r2](c24_05c/r2/manifest.json): SHA-256 der exakten drei JSONdateien.

Der [erste Bereitschaftsstand](c24_05c/pilot_readiness.v1.json) mit seinem
[Dateimanifest](c24_05c/manifest.json) bleibt unverändert erhalten: Auf seiner Basis
`87ea32f` war A noch nicht gemergt. Revision 2 aktualisiert diesen Integrationsbefund
und bindet den Vorgängerdigest, ohne irgendeinen Pilotlauf/Review zu behaupten.

Ausgang ist ausschließlich das bereits versionierte
[C23-06-Korpusmanifest](c23_06/corpus_manifest.v1.json). Dessen elf `origin=real`-
Metadateneinträge wurden unverändert übernommen; vier synthetische Einträge bleiben
außerhalb dieses geplanten Realkorpus. `permission=inventory_only` und fehlende
Source-/Versionsbindungen bleiben unverändert. Keine Umstufung zu evaluation.
Datasetversion `c24-05c-readiness-2026-10-18-r2` bezeichnet den aktuellen Planungsstand.

| Format | Deklarierte Rawpfade aus bestehendem Inventar | Freigegebene vollständige Bundles | Original-/Integritätsprüfung dieses Pakets |
| --- | ---: | ---: | --- |
| HTML | 5 | 0 | not_checked |
| PDF | 0 | 0 | not_checked |
| Eigenständiger Code | 0 | 0 | not_checked |
| SRT | 0 | 0 | blocked_source_binding / not_checked |
| TXT | 0 | 0 | not_checked |

Fünf deklarierte HTMLsnapshots (drei Notes, zwei Assignments) plus sechs bereits
dokumentierte Lücken ergeben elf Planungszeilen, **nicht elf Materialdateien**.
Zwei Assignmentquellen besitzen weiterhin keine belegte Source-ID; keine ID erfunden.
Die übrigen Source-IDs sind vorhandene Discovery-/Bindingmetadaten, keine neue
Quellenfreigabe. SourceVersion und ParsedVersion sind überall null; Parserrevision
und Locatoren ungeprüft. Die beiden historischen PDFreferenzen sind kein
eigenständiger Python-Codebestand. Keine behauptete Abdeckung zweier Dokumentlängen
oder repräsentative Gesamtstichprobe.

Der Bericht liest **keine** in `artifacts` benannte Originaldatei. Rawhashes und
relative Dateinamen sind nur deklarierte vorhandene Inventarmetadaten; weder
Dateiexistenz noch Bytegleichheit wurden neu nachgewiesen. Ein im Auftrag genannter
früherer Download/Hash-/Parsererfolg erteilt keine aktuelle Pilotfreigabe.
Zählwerte beziehen sich ausschließlich auf den vorgelegten Metadatenumfang, nicht
auf ungeprüfte private Verzeichnisse oder unbekannte produktive Stores.

## Sourcefreigaben und kontrolliertes Onboarding

Jede Berichtszeile weist eine **fehlende** Sourcefreigabe explizit aus: vorhandene
Source-ID und gegebenenfalls deklarierte Originaldatei/Rootalias, Herkunft; Scope,
Entscheidungsträger/-datum und Widerruf/Ablauf null; erlaubte Verarbeitungsschritte,
Speicherroots, Reviewer und technische Dienste leer. Diese Platzhalter sind keine
Freigabebelege und erlauben keine Inhaltsreads. Keine pauschale Verzeichnisfreigabe.

Nach Bereitstellung des tatsächlichen B-Vertrags muss ein authentifizierter
Entscheidungsträger pro Source festlegen: exakte Datei und Rawhash, Herkunft und
Nutzungs-/Evaluationsumfang, erlaubte Schritte/Storage-/Dienste-/Reviewerbindung,
Entscheidungsbeleg, Zeitpunkt und Ablauf-/Widerrufbedingungen. Die organisatorische
Freigabe und aktuelle technische Source-/Course-/Actorberechtigung sind separate
Voraussetzungen. Ein frei geänderter JSONstatus ersetzt keine davon.

Erst dann vorhandene `InventorySelection` und B-Bundleverifikation verwenden:
explizite Originaldatei/Größe/SHA, ursprünglicher Material-/Adapterplan, Receipt-
Aktionen und Input-/Outputhashes, belegte Parserrevision/Konfiguration, vollständige
Payload-/Parsed-/Locatorbindung sowie vorhandener Qualityreport. Keine Revision
aus aktuellem HEAD rekonstruieren, kein stilles Reparieren und kein erneutes Parsen.
Authoritative Source-/ParsedVersions ausschließlich aus tatsächlich geprüftem
Bestand übernehmen. Fehlende Belege blockieren; technische Verifikation bestätigt
noch keine fachliche Qualität. Zustände candidate/verified/approved_for_review/
reviewed/blocked/excluded nach dem dann integrierten Vertrag verwenden, nicht durch
dieses Metadatenpaket eine zweite Zustandsmaschine einführen.

Historisches CS50-Python-Lecture-0-SRT: Die im Auftrag genannten 2.228 Segmente,
sechs leeren Cues und früheren Hash-/Parservergleiche sind **historisch berichtete**,
hier nicht erneut ausgeführte Befunde. `data/Harvard/...` gegen
`data/lectures/Harvard/...` bleibt absichtlich abgewiesen. Vor Verwendung separate
D06-Entscheidung, explizite kanonische Zielbindung und gegebenenfalls neue
nachvollziehbare Version; Originale und alte Receipts erhalten. Keine Symlinks,
Pfadfallbacks, Migration oder automatische Workspacekopie.

## Konkreter Ablauf nach Aufhebung der Blockaden

1. Tatsächliche A- und B-Implementierungen integrieren, Verträge erneut prüfen;
   Source-/Review-Schreibrechte und Approverbindung explizit festlegen.
2. Pro Source vollständige Freigaben/Bundles benennen; Metadatenmanifest bewusst neu
   versionieren. Alle identitäts-/formatlosen Lücken bleiben blockiert/excluded mit
   Begründung. Keine Materialübernahme allein zum Erreichen einer Zielzahl.
3. Bestehende autorisierte read-only Bundleprüfung ausführen. Content-/Indexroots,
   Ressourcenlimits, zulässige Dienste und Berechtigungsscope ausdrücklich festlegen.
   Kein verdeckter Import oder Indexbuild im Reproduktionslauf.
4. 20–30 Parsingstellen als **Planungsgröße** begründet auswählen: Vollständigkeit,
   Reihenfolge/Überschriften/Listen/Unicode; exakte Codezeichen, Einrückung/Umbrüche;
   mathematische Operatoren/Exponenten/Brüche, Tabellen/Bilder/Seiten; SRTcues/-zeiten
   und Überlappung, TXT ohne Zeiten. Fehlendes Format/Originalrenderer blockiert
   dessen Stellen; keine erfundene PDFgeometrie oder Transcriptzeit.
5. 15–20 konkrete Fragen **vor** Retrievalausführung am freigegebenen Korpus
   festlegen: exakte Begriffe, Konzepte, Code, Formeln, dokumentübergreifend,
   mehrere relevante Regionen sowie bewusst keine relevante Quelle. Aktuell
   **null konkrete Pilotfragen**; keine unbelegten Fragelisten als real bewertbar.
6. Authentifizierte Menschen annotieren im unabhängigen B-Goldmodus Originalregionen,
   Relevanz 0–3, exakte Block-/Text-/Raw-/Locatorbindung, Reviewbeleg/-datum/-revision.
   Keine voreingestellten Rankings. Unterstützung protokollieren; Modelle bestätigen
   nichts. Kritische/mehrdeutige Fälle erhalten unabhängige Zweitprüfung, Widersprüche
   bleiben offen. Keine Inter-Rater-Kennzahl ohne tatsächliche Mehrfachannotation.
7. Alle vorgesehenen Tasks, gültige Referenzen und vollständigen begrenzten Pool
   prüfen. Pending/rejected/unjudged ist nicht automatisch irrelevant. Neue
   SourceVersion oder korrigiertes Gold verlangt neue gebundene Evaluationsrevision.
8. FTS5 mit unveränderter Generation, Queryliste, Source-/Actorscope, Konfiguration
   und vorher festgelegten k ausführen. Vector/Hybrid nur nach konkreter separater
   Instanz-/Modell-/Dienstfreigabe; dieselbe erlaubte Korpusauswahl, getrennte
   Backend-/Generations-/Konfigurationsbelege. Kein Optimieren auf dem Goldkorpus.
9. Ausschließlich die integrierte A-Evaluation verwenden: per Query/Format/Methode/
   Datasetgeneration Precision/Recall/MRR/nDCG mit Rohnennern, Locator/Provenienz und
   tatsächlich ausgeführten Sicherheitsbelegen. Unvollständiger Pool not_evaluable,
   kein positives Gold entsprechend A not_determinable. Synthetisches getrennt halten.
10. Fehler anhand reproduzierbarer Belege klassifizieren: technische Hash-/Versions-/
    Locator-/ACLfehler getrennt von Parsingverlust, getrennter Goldregion durch
    Chunkgrenze, Tokenisierung, außerhalb Top-k oder inhaltlicher Relevanz. Fehlendes
    Gold ist eine Evaluationslücke, kein nachgewiesener Retrievalfehler.
11. Autorisierte Menschen entscheiden je Methode/Format begrenzt über accepted,
    accepted_with_limitations, rejected oder not_evaluable. Akzeptanzgrenzen **vor**
    finaler Messung festlegen; aktuell keine Zahlenwerte beschlossen. Ein bestätigter
    ACL-/Leakfehler sperrt Freigabe, hohe Rankingwerte ersetzen keine Entscheidung.
12. Vorhandene B-Exports/Reportpersistenz für Reviewhistorie, Gold und Abnahme nutzen;
    RealCorpusAcceptanceReport erst gegen diesen integrierten Vertrag ergänzen.
    Korpus-/Golddigests, Revisionen, Scope, Parser-/Retrievalidentitäten, Generation,
    Nenner, technische/fachliche Befunde, offene Prüfungen, Approver/Zeit/Begründung
    binden. Keine private Volltext-/Hostpfadveröffentlichung oder Überschreibung.

Die vorgeschlagenen 5–10 Dateien sind ein begrenzter Pilot, kein repräsentativer
Gesamtqualitätsnachweis. Widerruf, Quarantäne, Tombstone oder geänderte Berechtigung
sperrt neue Lese-/Export-/Evaluationsaktionen; ein alter Report ist keine Capability.

## Technische Prüfung und Reproduzierbarkeit

Die Artefakte sind kanonische JSONmetadaten mit exaktem Dateimanifest. Der
Bereitschaftsdigest bindet den Body ohne Selbsthash; Corpus-/Golddigests verwenden
dieselben vorhandenen `canonical`-/`fingerprint`-Hilfen. Kein Timestamp eines
angeblichen menschlichen Reviews und kein künstlicher Bestätigungsstatus.

Prüfbare Python-Schnittstelle, ohne Originaldateien zu öffnen:

```python
from pathlib import Path
from src.content_store.models import fingerprint, sha256
from src.model_evaluation.material_evaluation import CorpusManifest, GoldDataset
from src.tools_materials.quality import _json

root = Path("docs/cs50/evaluation/c24_05c/r2")
manifest = _json((root / "manifest.json").read_bytes())
for name, digest in manifest["files"].items():
    assert sha256((root / name).read_bytes()) == digest
corpus = CorpusManifest.model_validate_json((root / "corpus_manifest.v1.json").read_bytes())
gold = GoldDataset.model_validate_json((root / "gold_references.v1.json").read_bytes())
report = _json((root / "pilot_readiness.v1.json").read_bytes())
assert report["sha256"] == fingerprint(report["report"])
assert report["report"]["corpus_digest"] == fingerprint(corpus.model_dump(mode="json"))
assert report["report"]["gold_digest"] == fingerprint(gold.model_dump(mode="json"))
assert not gold.references
# Kein Aufruf von evaluate_materials/evaluate_retrieval, Import oder Originalpfaden.
```

Aktueller Digest: `11a0dd008a5f3fb68998d57b642bd2d3f93aaa272a52b6e292aaf4f06e517040`.
Erster Stand: `633f458d0f14255fcc4172e6f57a59d30055415965218654412f74008efb80e2`.
Gleiche Metadaten ergeben denselben Digest; neue Freigaben, Gold oder Quellen
verlangen einen neuen ausdrücklich versionierten Snapshot. Dies ist ein
Integritätsnachweis des Planungsartefakts, kein Quellen-/Menschenauthentizitätsbeweis.

## Tatsächlicher Abschlussumfang

`implemented`: ausschließlich wiederverwendetes Pilot-Metadatenmanifest,
leerer bestehender Goldvertrag, Bereitschaftsbericht, Datei-/Reportdigests und dieser
konkrete Übergabeplan. Keine neue Runtime oder Ersatz-Reviewpersistenz.

`blocked`: kontrolliertes Realonboarding, menschliche UIreviews, vollständiger
synthetischer C-End-to-End-Workflow und formaler Abnahmevertrag durch fehlendes B;
reale Ausführung zusätzlich durch fehlende Sourcefreigaben/Bundles/Gold und D06/D07.

`not_checked`: Originaldateien, Receipts, Raw-/Parsedhashgleichheit, Parserrevision,
Source-/ParsedVersions, Locatoren, tatsächliche Reviews, Index-/Retrievalläufe,
Sicherheitsabnahme und fachliche Qualität. Das Operationsfeld des Bereitschafts-
berichts zählt ausschließlich diesen Metadatenaufbau, keine synthetischen Tests.

`out_of_scope`: Ersatzimplementierung von A/B, neue Parser/Modelle/Ranking/UI,
private Bestandsinventur, Downloads, historische Migration und Deployment.

Erste Prüfung auf Basis `87ea32f`: **38 passed / 0 failed / 0 skipped**, 8,34 s,
für die unveränderten C23-06-Vertragstests. Tatsächlicher Befehl:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
  -q --disable-warnings -p no:cacheprovider tests/test_cs50_material_evaluation.py \
  --basetemp=/tmp/c2405c-c23-contracts
```

Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, System-Pytest 7.2.1 und Ruff 0.16.0.
Pytest-7-AST-Warnungen unter Python 3.12 sind keine Skips. Keine Dependencyinstallation.
Diese Suite prüft synthetische vollständige/unvollständige Bundles, Gold-/Herkunfts-
und Berechtigungsgrenzen, Hash-/Locatorbezüge, Unicode, SRT, private temporäre
Stores sowie Reports/No-Overwrite. Sie ist **kein C24-05-C-Workflowtest**.

Ruff Check und Format Check erfolgreich mit vorhandenem Ruff für den tatsächlich
wiederverwendeten Umfang, unverändert auf Master:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check --no-cache src/model_evaluation/material_evaluation.py \
  src/tools_evaluation/evaluate_materials.py scripts/cs50_material_evaluation.py \
  tests/test_cs50_material_evaluation.py
# Derselbe Dateiumfang mit format --check --no-cache.
git diff --check
```

Zusätzlich beide vorhandenen Pydanticmodelle und alle Metadaten erneut validiert:
exakte Übernahme der elf realen Inventareinträge, unveränderte IDs/Berechtigungen,
leeres Gold, gleiche Datasetversionen, Source-/Corpus-/Golddigests, exakte
Dateiinventarliste und Dateihashes, alle Blockadestatus und SRT-Pfadsperre.
Eine lokale Python-Auditprüfung erlaubte ausschließlich die expliziten fünf
Metadatendateien: zehn Metadatenreads, **null Originaldateiöffnungen**. Wiederholter
Digest identisch; 17 lokale Markdownverweise und diff check erfolgreich.

Nach Merge von #87: Master `d2b5e05` in den eigenen Branch übernommen, den
C24-05-A-Plannachtrag vollständig erhalten und Revision 2 zusätzlich angelegt.
Alle Dateien des ersten Bereitschaftsstands sind gegenüber dem ersten PRcommit
unverändert. A ist nun verfügbar; B bleibt Architektur ohne Reviewruntime.

`passed`: **104 passed / 0 failed / 0 skipped**, 23,66 s, mit obigem tatsächlichen
Python-/Pytestpräfix und folgenden Optionen:

```sh
-q --disable-warnings -p no:cacheprovider \
 tests/test_cs50_material_evaluation.py tests/test_content_retrieval_evaluation.py \
 tests/test_content_retrieval_integration.py --basetemp=/tmp/c2405c-current-contracts
```

38 bestehende C23-06- und 66 integrierte A-Fälle, einschließlich dessen synthetischer
FTS5-/Vector-DTOintegration. Überlappt den ersten 38er-Lauf, nicht addieren.
Keine neue C-Pilotintegration. Ruff Check und Format Check auch für die acht
integrierten A-Pythondateien erfolgreich, zusammen zwölf unveränderte Dateien.
Erneute Metadatenprüfung: beide Corpus-/Goldschemas, exakte Inventarübernahme,
Datei-/Reportdigests, neue Datasetversion und Vorgängerdigest geprüft. Audit:
15 Metadatenreads, **null Originaldateiöffnungen**; 20 lokale Verweise geprüft.

Keine neue Pythondatei, keine C-Runtime-/Review-/UI-Integration und keine neuen
C-Workflow-/Wiederaufnahme-/Sicherheits-/Abnahmetests implementiert oder als grün
ausgegeben. Diese bleiben bis zur tatsächlichen B-Implementierung not_checked.
Es wird keine vollständige Pilot- oder Gesamtrepositoryabnahme behauptet.

Nur eigene synthetische Pytestdaten und erzeugte Worktree-Caches werden nach
Prüfung entfernt; Testlog außerhalb des Repositories behalten. Der eigene saubere
Worktree bleibt für den offenen Draft-PR bestehen. Keine Bereinigung anderer
Worktrees, Originaldaten, virtueller Umgebungen oder Branches, kein Merge.
