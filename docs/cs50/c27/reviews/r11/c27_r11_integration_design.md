# C27-R11 – Ausführbarer Integrationsentwurf, nicht ausgeführt

## Architekturentscheidung als Empfehlung

Learning bekommt den **eigenen Namespace `src.c27_learning_summary`**. Der Namespace `src.lecture_summary` bleibt für die Acceptance-/Legacy-/Hierarchy-Linie verfügbar. Zwei klar getrennte Produkteingänge, Modellfamilien, Storeformate und Exportverträge; keine gemeinsame automatische Summary-API und kein stiller JSONkonverter. Keine neue Implementierung in R11. Die spätere Implementierungsfreigabe muss genau diese Entscheidung samt Dateiliste bestätigen. READY_FOR_IMPLEMENTATION_APPROVAL ist keine Ausführungserlaubnis.

Alternativen geprüft: (a) Learning unter altem Namespace ersetzen lassen: verwirft Acceptance-APIs/Tests und die C27b/c-Abhängigkeiten; abgelehnt. (b) Acceptance als alleinigen Vertrag übernehmen: verliert Learning-Review/Store-/R08-Eigenschaften und überschreitet Scope; abgelehnt. (c) Klassenunion/automatischer Adapter: gleiche Schemanummern, inkompatible Daten und Sicherheitsgrenzen, wesentlich größere Migration; abgelehnt. (d) getrennte Namespacefamilien: begrenzte mechanische Änderung mit bewusstem doppeltem Funktionsumfang; bevorzugt. Gemeinsame Parser-/Content-/Lecturegrundmodelle bleiben wiederverwendet.

## Lokale Zielbasis und Grenzen der Gitdaten

| Ref | Lokal tatsächlich gespeicherter Commit | Aussage |
|---|---|---|
| HEAD / feat/c27-cs50-learning-pipeline | a8af1d9372eb435d3e1331c33b047d21120d57c2 | 62 uncommittete Kandidaten, Index leer |
| master | c1007efdbac3c1544020f328a3a1347e481797ba | Vorfahr; 173 Commits hinter HEAD/origin/master |
| origin/master | a8af1d9372eb435d3e1331c33b047d21120d57c2 | nur gespeicherter Trackingref, HEAD 0/0 |
| fix/c27-acceptance-exports | a0d3ebf7f64d44dd843f1848e70dc70a3a3af835 | HEAD/fix 12/19 seit e502aa915ad0e928dbe7e92eacd44fff0152912b |

Merge-Base master↔HEAD und master↔origin/master: c1007efdbac3c1544020f328a3a1347e481797ba. HEAD↔origin/master: a8af1d9372eb435d3e1331c33b047d21120d57c2. origin/master↔fix: e502aa915ad0e928dbe7e92eacd44fff0152912b. origin/HEAD fehlt. Tatsächlicher Defaultbranch laut Auftrag/AGENTS.md: master. GitHub-HEAD, PRs, erforderliche Checks/Reviews und Branchschutz: **REMOTE_HEAD_UNVERIFIED**, keine Onlineprüfung und kein Fetch. 173 lokale fehlende Commits nicht zum Inhalt dieses PRs zählen; niemals den alten lokalen master als Produktbasis benutzen.

Späterer autorisierter Ablauf startet nach Live-Abgleich vom dann bestätigten origin/master in **neuem** eigenem Branch/Worktree. Weder diesen schmutzigen Worktree auschecken noch fremde aktive Zweige bearbeiten. Weicht die Zielbasis vom hier dokumentierten Stand ab, gezielte Pfad-/API-/Testanalyse aktualisieren, nicht ungeprüft anwenden. Ist Acceptance dann schon integriert, seine Dateien/Tests erhalten und Koexistenz direkt dort prüfen. Fehlt es, darf Learning unabhängig als eigener PR integriert werden; die 19 fix-Commits sind keine vorausgesetzte Integrationspflicht.

## C26-/C27-Abhängigkeiten

Die Tabelle belegt lokale Ancestry/Commitdeltas, keine vollständige semantische Patchäquivalenz oder Remote-PRzustände. Spalten links/rechts beziehen sich auf HEAD...Ref. Alle vorhandenen lokalen C26-/C27-Refs sind erfasst; Remote-Trackingvarianten mit ihren exakten Daten stehen in evidence/branch_dependencies.json. Keine anderen Worktrees inhaltlich auditiert.

| Lokaler Ref | OID | Vorfahr oder HEAD / Ref | Merge-Base(s) | Kandidatenüberschneidung seit Base |
|---|---|---|---|---|
| `audit/c26-legacy-prs` | `29114d2e2877cee9c434f620da852313963e3a01` | bereits Vorfahr | `29114d2e2877cee9c434f620da852313963e3a01` | — |
| `audit/c26-operations-preflight` | `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d` | 6 / 1 | `e68275205fefb7a5f6db42bc45060e505bfcefb5` | — |
| `docs/c26-release-readiness` | `ad4e33b63389c2d5378dfcfd733e144f20f0af2e` | bereits Vorfahr | `ad4e33b63389c2d5378dfcfd733e144f20f0af2e` | — |
| `docs/c26b6-rollout-readiness` | `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c` | bereits Vorfahr | `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c` | — |
| `feat/c26-cs50p-04-download-only` | `6351d443afe18f806d37d64010e7050b4b5fcd73` | 0 / 6 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore` |
| `feat/c26-cs50p-05-sqlite-diagnostics` | `47a19ef89bc0650cd7e9cbe802b3d7e9d5006e31` | 0 / 6 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore` |
| `feat/c26-cs50p-07-week-materials` | `1584a2807c8f9d75604ab17a4ea239d8f4a0882b` | 0 / 9 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore`, `src/model_materials/acquisition.py`, `src/tools_materials/text_validation.py` |
| `feat/c26-cs50p-08-week-completion` | `143d3412c668bb652eba7929742a3a886031c372` | 0 / 10 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore`, `src/model_materials/acquisition.py`, `src/tools_materials/code_zip.py`, `src/tools_materials/source_acquisition.py`, `src/tools_materials/text_validation.py` |
| `feat/c26-cs50p-mvp` | `81db9ed3f5fc7e0c3d6952b438f015ae6521af3c` | 0 / 5 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore` |
| `feat/c26-final-pilot-readiness` | `7a8e96d3a9004fabcf86962e6f0859479348c83a` | bereits Vorfahr | `7a8e96d3a9004fabcf86962e6f0859479348c83a` | — |
| `feat/c26-integration-b3-b7` | `cba3302261be5b5cb0a36fc482250a5268b8ad44` | bereits Vorfahr | `cba3302261be5b5cb0a36fc482250a5268b8ad44` | — |
| `feat/c26-lecture-summarizer-mvp` | `1584a2807c8f9d75604ab17a4ea239d8f4a0882b` | 0 / 9 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore`, `src/model_materials/acquisition.py`, `src/tools_materials/text_validation.py` |
| `feat/c26-pilot-integration` | `6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d` | 0 / 2 | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | `.gitignore` |
| `feat/c26-runtime-bootstrap` | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | bereits Vorfahr | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | — |
| `feat/c26-week0-acceptance` | `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7` | bereits Vorfahr | `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7` | — |
| `feat/c26a-cs50-worker` | `d95d110f7a4d22eeb01843027f1b3142b877e232` | 65 / 1 | `7ed22f3d40fa5a1ea388152b81bf883865e2f4f1`, `4ca068ca8107cdec7f9430bfbb52ca1f9f497372` | — |
| `feat/c26a-existing-backend-copy-handoff` | `071a327091bfc66cd6ddb5f1541ca2f89e4b0889` | bereits Vorfahr | `071a327091bfc66cd6ddb5f1541ca2f89e4b0889` | — |
| `feat/c26b-https` | `c36417516cd027322388463c10a2391f7fcb225f` | bereits Vorfahr | `c36417516cd027322388463c10a2391f7fcb225f` | — |
| `feat/c26b-private-vpn-review` | `3b91d39195e0d13fe0442d4594b28e431b0f4236` | bereits Vorfahr | `3b91d39195e0d13fe0442d4594b28e431b0f4236` | — |
| `feat/c26b1-worker-image-entrypoints` | `86ad27659212fe6b97d7589f8c5f0519cb84aef0` | bereits Vorfahr | `86ad27659212fe6b97d7589f8c5f0519cb84aef0` | — |
| `feat/c26b2-single-html-pilot` | `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65` | bereits Vorfahr | `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65` | — |
| `feat/c26b3-admin-bootstrap` | `505bea92086746242e357675e43e51d285d41ed0` | bereits Vorfahr | `505bea92086746242e357675e43e51d285d41ed0` | — |
| `feat/c26b4-week0-batch-pilot` | `05d46133eefcb1d7da37e2867b4e8cc30cb7633c` | bereits Vorfahr | `05d46133eefcb1d7da37e2867b4e8cc30cb7633c` | — |
| `feat/c26b5-multiformat-transcripts` | `81897b7c06d23841f4edbbb3e91df3854221deb2` | bereits Vorfahr | `81897b7c06d23841f4edbbb3e91df3854221deb2` | — |
| `feat/c26b6-code-zip-import` | `6786b5d67b31125895d94af7b763a1002aeeea7d` | bereits Vorfahr | `6786b5d67b31125895d94af7b763a1002aeeea7d` | — |
| `feat/c26b6-code-zip-reviewed` | `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8` | bereits Vorfahr | `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8` | — |
| `feat/c26b6-course-planning` | `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb` | bereits Vorfahr | `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb` | — |
| `feat/c26b7-media-last` | `6786b5d67b31125895d94af7b763a1002aeeea7d` | bereits Vorfahr | `6786b5d67b31125895d94af7b763a1002aeeea7d` | — |
| `feat/c26b7-media-last-reviewed` | `cba3302261be5b5cb0a36fc482250a5268b8ad44` | bereits Vorfahr | `cba3302261be5b5cb0a36fc482250a5268b8ad44` | — |
| `feat/c26d-operation-gate-v2` | `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` | 6 / 10 | `e68275205fefb7a5f6db42bc45060e505bfcefb5` | — |
| `feat/c26e-authenticated-runtime-collector` | `28e9a608d74270278cf037e35957d0bae08d50b2` | 6 / 12 | `e68275205fefb7a5f6db42bc45060e505bfcefb5` | — |
| `feat/c26f-independent-coordinator` | `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` | 6 / 13 | `e68275205fefb7a5f6db42bc45060e505bfcefb5` | — |
| `feat/c26g-deployment-readiness` | `778367396cd52526eca59edd41c2367f5e43b897` | bereits Vorfahr | `778367396cd52526eca59edd41c2367f5e43b897` | — |
| `feat/c26h-controlled-integration` | `778367396cd52526eca59edd41c2367f5e43b897` | bereits Vorfahr | `778367396cd52526eca59edd41c2367f5e43b897` | — |
| `feat/c27-cs50-learning-pipeline` | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | bereits Vorfahr | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | — |
| `feat/c27b-legacy-catalog` | `117aa8411f1b516e75d97a43c177ff13a2df57d5` | 12 / 17 | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | `src/lecture_summary/__init__.py`, `src/lecture_summary/models.py`, `tests/test_lecture_summary.py` |
| `feat/c27c-hierarchical-summary` | `249379f03bdafa1390d723c39dc1302ec2e533e2` | 12 / 18 | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | `src/lecture_summary/__init__.py`, `src/lecture_summary/models.py`, `tests/test_lecture_summary.py` |
| `fix/c26-stabilization` | `c77128b14e60b78a546fd804507ff255d4833759` | bereits Vorfahr | `c77128b14e60b78a546fd804507ff255d4833759` | — |
| `fix/c26b5-knowledge-identities` | `78a51a9312aafb0483abaf7f97f379ebcf96a315` | bereits Vorfahr | `78a51a9312aafb0483abaf7f97f379ebcf96a315` | — |
| `fix/c27-acceptance-exports` | `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835` | 12 / 19 | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | `src/lecture_summary/__init__.py`, `src/lecture_summary/models.py`, `tests/test_lecture_summary.py` |
| `review/c26b-private-vpn-final` | `d0a58f392530bf4112ef7d7a632c1e5e36e07a20` | bereits Vorfahr | `d0a58f392530bf4112ef7d7a632c1e5e36e07a20` | — |
| `review/c26b-private-vpn-validated` | `c8c06fdb3e45e7bb454b8153bd0efe6f194e8199` | bereits Vorfahr | `c8c06fdb3e45e7bb454b8153bd0efe6f194e8199` | — |

Direkte Voraussetzungen in der a8af1d9-Basis sind ContentStore-/Material-/Transcript-/Lectureverträge und C26h-/DEP01-Integration. C26g/h sind mit 7783673 bereits Vorfahren; Runtimebootstrap e502aa9 liegt 12 Commits zurück. C26d/e/f lokale Spitzen und Operationspreflight sind alternative Fortsetzungen, nicht automatisch benötigte Vorbedingungen; ihre Inhalte dürfen trotz ähnlicher Themen nicht unbesehen nachgezogen werden.

CS50P 07/08 sind dagegen spätere Nachfahren von a8af1d9 (9/10 zusätzliche Commits). Nur vier Dateien wurden bereits selektiv aus 143d3412c668bb652eba7929742a3a886031c372 übernommen und **erneut bytegleich gegen das lokale Commitobjekt verglichen**: src/model_materials/acquisition.py, src/tools_materials/source_acquisition.py, src/tools_materials/text_validation.py und src/tools_materials/code_zip.py. Die erste, zweite und dritte fehlen noch auf origin/master; code_zip existiert dort und sein C27-Delta ersetzt den batch.sha-Import durch äquivalentes hashlib.sha256 ohne batch-Abhängigkeit. Keine pauschale Integration von 07/08 samt SQLite-/Downloader-/Runtimeänderungen. Provenienzdatei bleibt als historische Auswahldokumentation erhalten. Wenn 07/08 vor diesem PR auf master landen, dieselben Dateien abgleichen und identische Inhalte nicht duplizieren; geänderte Inhalte fachlich abgleichen statt ersetzen. Bei abweichender Dateimenge muss das endgültige Stagingmanifest neu freigegeben werden.

C27b 117aa841 → C27c 249379f0 → fix a0d3ebf7 bilden die Acceptance-Fortsetzung; origin/feat/c27-lecture-summarizer zeigt lokal ebenfalls auf a0d3ebf7. Learning-HEAD enthält diese Fortsetzung nicht. C26-LS-01-Arbeitsstand ist Herkunft über historische Patch-/Handoffbelege, nicht im gleichnamigen Branch-HEAD enthalten: feat/c26-lecture-summarizer-mvp zeigt auf 1584a280 (CS50P07). Branchname ist kein Integrationsnachweis.

## Überschreibungs- und Duplikationsschutz

1. Die drei Konfliktpfade werden durch die Learning-Auswahl nicht belegt. Alle zehn Learning-Paketdateien kommen gemeinsam in den neuen Namespace; kein gemischtes altes Paket mit neuen Engine-/Storemodulen.
2. .gitignore wird als additive, pfadgenaue Regeländerung auf die tatsächliche Zielbasis übertragen. Acceptance hat dort andere, legitime Regeln; niemals ganze .gitignore aus diesem Worktree darüberkopieren. Alte Ausnahmezeilen für src/lecture_summary sind nur zu erhalten, soweit bereits Zielbestand/Acceptance; Learning benötigt zwei neue exakte Ausnahmen im neuen Namespace.
3. src/llm/model_litellm.py und src/tools_materials/code_zip.py existieren auf allen drei untersuchten Linien. HEAD/fix sind hier bytegleich, Worktreedeltas sind verschieden zu beiden. Nur die geprüften Deltas übernehmen, keine komplette Datei über einen inzwischen fortgeschrittenen Zielstand kopieren. Legacy-LLMClient.__init__, completion/caching/callbacks und neue bounded-Nutzung müssen nebeneinander bleiben.
4. Die 59 unversionierten Kandidaten fehlen vollständig auf origin/master; nur die drei Konfliktdateien existieren auf fix. Die beiden Dokumentbäume und Fixturepfade kollidieren dort lokal nicht. Zwei konzeptionell ähnliche Summaryangebote bleiben bewusst separat; keine Kopie der fix-Module service/providers/exports/hierarchy in den neuen Namespace.
5. Bestehende Abschlussdokumente anderer Tasks und offene Draft-PRs nicht bearbeiten. Diese R11 erzeugt keine Git-Artefakte. Vorbestehende Branches/Worktrees bleiben erhalten, unabhängig von ihren Commitzeigern.

## Präzise Änderungsschritte für eine spätere Implementierung

A. Exakte 62 Quellbytes/Hashes, Branch/HEAD, leeren Index und Zielbasis verifizieren. Rohdaten und bestehende Handoffs bleiben lesend. In neuem eigenen Worktree die genehmigten Inhalte aus dem erhaltenen Quellsnapshot übernehmen; diesen vorbestehenden Worktree nicht bereinigen. Keine Dateien aus ganzen Verzeichnissen ungeprüft kopieren.

B. Die zehn Paketpfade aus der Commitliste auf src/c27_learning_summary umabbilden. Importstrings `src.lecture_summary` nur in den nachfolgend einzeln benannten aktiven Pythondateien ersetzen. Auch Stringziele für monkeypatch, lokale spätere Imports und reviewed_week.revision() erfassen. **Historische Dokumente/Manifeste sowie Quelldaten/Refs nicht global ersetzen.**

- `frontend/pages/G_p0_lecture_summarizer.py`
- `scripts/c27_reviewed_week.py`
- `scripts/lecture_summary_offline.py`
- `src/c27_learning_summary/adapter.py`
- `src/c27_learning_summary/engine.py`
- `src/c27_learning_summary/export.py`
- `src/c27_learning_summary/llm.py`
- `src/c27_learning_summary/models.py`
- `src/c27_learning_summary/reviewed_week.py`
- `src/c27_learning_summary/store.py`
- `tests/test_c27_remediation_r02.py`
- `tests/test_c27_remediation_r04.py`
- `tests/test_c27_remediation_r06.py`
- `tests/test_c27_remediation_r08.py`
- `tests/test_c27_reviewed_week.py`
- `tests/test_c27_learning_summary.py`
- `tests/test_lecture_summary_ui.py`

`tests/test_c27_remediation_r06.py` enthält zusätzlich in Zeile 288 einen echten Dateipfad `src/lecture_summary/public_sources.v1.json`: exakt nach `src/c27_learning_summary/public_sources.v1.json` ändern. export_policy._load_policy nutzt Path(__file__).with_name und muss mit der JSONdatei gemeinsam umziehen. UI-/CLI-Einstiegsnamen und Fixtureorte bleiben erhalten. pyproject.toml enthält keine explizite Paketfindung oder Build-Systemsektion; pytest nutzt pythonpath=["."]. Geplant ist der bestehende Start aus dem Repositorycheckout, geprüft über Cold-Import und CLI/AppTests. Ein installierbares Wheel/Packagingwechsel ist nicht Teil dieses Scopes und verlangt bei späterem Bedarf einen eigenen Auftrag.

C. `tests/test_lecture_summary.py` als tests/test_c27_learning_summary.py übernehmen, keine Assertions umdeuten. UI-Suite bleibt tests/test_lecture_summary_ui.py. Neue Koexistenzsuite: Cold-Imports ohne SDK und Netz; zwei unterschiedliche Catalog/Claim-Klassen bei vorhandener Acceptance; gegenseitige Ablehnung realistisch vollständiger fremder Catalog-/Summarypayloads trotz version=1; getrennte Storewurzeln, keine Aliasauflösung. Bei nicht vorhandener Acceptance können ihre Objekte nicht erfunden oder als getestet ausgegeben werden. Dafür eine externe, gewöhnliche Dateikopie der genehmigten Learning-Basis mit ausschließlich Acceptance-Deltapfaden aus dem lokalen fix-Baum belegen. Beide alten committed Pfadmengen seit e502aa9 sind lokal disjunkt; die drei verschobenen Learning-Pfade werden durch diese Kopie nicht überschrieben. Kein Gitmerge nötig; Overlay dokumentieren und deren Basiskombination nicht als PR-Mergezustand ausgeben.

D. Felder, Schemanummern, Konfigurationsdefaults, Kosten-/Chunk-/Retry-/Speichergrenzen und Code-/Formelvalidierung unverändert. Processingrevision bindet `m.__name__` und Quellbytes (reviewed_week.py 170–202), daher ist nach Namespacewechsel ein **neuer Processingkey erwartbar**. Alten Cache nicht umbenennen oder Receipts anpassen; alte Ergebnisse behalten. Summary-Cache bindet seine bisherigen Inputs und Schema, nicht pauschal den Modulnamen: keine erfundene Pflicht zur Änderung aller Summarycachekeys. Kompatible eigene Learning-v1/v2-Resultbytes unverändert lesen; Acceptance-JSON nie über upgrade_v1 routen. Registry-/POSIXstores nicht zusammenlegen.

E. Metadatenpolicy/Allowlist bytegleich verschieben; SourceRef.text und Claim.text bleiben fachlicher Freitext. Keine Ausweitung der Quellenfreigabe und keine Freigabe von Acceptance-Exporten durch R09 behaupten. Nach Umstellung gezielte R02/R04/R06/R08-/Review-/UI-Regressionen, genaue Auswahl im Commitplan. Alte Exporte bleiben unverändert; Re-Export nur mit neuen Namen und eigener Auswahl.

F. example-summary.md ausschließlich um sechs Schlussleerzeichen kürzen; Originalhash/Normalisierung in aktuellem Index aufzeichnen. JSON-v1-Beispiel unverändert als historische Kompatibilitätsfixture; keine Neugenerierung. Alle anderen 29 historischen Dokumentdateien bytegleich erhalten. Historische Metadatenpfade bewusst als nicht geheime Provenienz zulassen, als nicht portable alte Orte kennzeichnen. Das ist eine Empfehlung zur späteren Veröffentlichung, keine erfolgte Veröffentlichung und keine generelle Pfadfreigabe für neue Dateien.

G. Neue aktuelle Dokumente erstellen, 16 explizite R09/R10/R11-Berichte archivieren, nur benötigte JSON-/__init__-Ignoreausnahmen ergänzen. Aktueller Index erklärt historische Pfade, die R08→CAP→R09-Statusfolge, beide API-Familien, neue Namespace-/Testpfade, die MD-Normalisierung sowie noch fehlende Live-/PR-/Produktionstore. integration_manifest.v2.json bindet finale 82 andere Zieldateien und beschreibt sich selbst als ausgenommen; kein Selbsthash. Keine historischen Manifeste neu berechnen. Der Freigabeoperator bekommt exakt diese Liste plus neue Zielhashes, bevor Staging beginnt.

## Nicht in diesem Entwurf gelöst oder behauptet

F06–F14 behalten ihre späteren Material-/UI-/HTML-/ZIP-/Week-/Fach-/Provider-/Budget-/Resume-/Kurs-/Produktionsgates. Globale Mypy-Schuld 6.104 ist historisch übernommen, kein heutiger grüner Typcheck. Dieser Architekturentwurf schließt eine Scopeentscheidung, keine dieser Produktabnahmen. Risiko des doppelten Summaryangebots wird über klare Einstieg-/Bedienungsdokumentation begrenzt; gemeinsame UI/Migration ist kein stiller Teil der Implementierung.

## Verbindlicher Zusatz aus der Hookprüfung

.pre-commit-config.yaml ist als 83. Zielpfad in C1 eingeplant. Ausschließlich end-of-file-fixer erhält die im Commitplan exakt definierte Ausnahme für die beiden historischen example-summary-Dateien und die hashgebundene transcript.json-Fixture. Dies erhält deren fehlendes finales LF; keine stille Byteänderung und keine globale Hookausnahme. trailing-whitespace bleibt aktiv, MD wird um die sechs bekannten Leerzeichen normalisiert. Vollständiger Scope: 62 Originalquellen plus 21 zusätzliche Planpositionen (20 neue Dateien und eine bestehende Hookkonfiguration). Das finale integration_manifest.v2.json bindet die **82 anderen** Zieldateien, ohne Selbsthash. Für die Konfiguration Syntax, exakte Regex-Treffermenge und semantischen Erhalt aller anderen Hooks prüfen. Kein Produktcode und keine Quelle wird hierfür in R11 verändert.
