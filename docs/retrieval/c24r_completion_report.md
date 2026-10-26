# C24-R Abschlussbericht

Basis: `4c057ae33d41ba98e227879cc8a51283338e4a0b`, sauber und committet.
Ausschließlich C24-R-Worktree; vorhandener Branch `feat/c24r-retrieval_completion`.
Zielbranch `feat/c24-retrieval-completion` konnte wegen schreibgeschütztem
Git-Gemeinschaftsspeicher nicht angelegt/umbenannt werden. Keine lokalen Commits,
keine Remoteänderung. Lieferung als vollständiger vorwärts/rückwärts geprüfter
Patch einschließlich neuer Dateien mit SHA-256-Manifest und logischen Teilpatches.

## Verifizierte Herkunft

[Inventarmatrix](c24r_integration_inventory.md) dokumentiert Architektur und Lücken.
PR #85 (`30bc6d3`), #87 (`d2b5e05`), #90 (`df0f9a7`) und #91 (`4c057ae`)
sind nach lokalem Git und read-only GitHubdaten integriert. UI PR #7 ist remote
merged (`90816a1`), ohne UIänderung. Search und Indexjobs existieren in späteren
committeten DEV-Funktionen: Feature `4259187` aus #124, Feature `c07ed9a` aus
#125; beide Remote-PRs sind merged, fehlen aber in dieser Basis. Ihre isolierten
Feature-Diffs wurden nach Herkunfts-/Abhängigkeitsprüfung übernommen. Keine
Governance-/MAINT-Vorfahren, uncommitteten Fremdstände oder produktiven Änderungen.

## Änderungen

- R1: `src/content_store/search_{models,http}.py`, C16 `Application`/Handler/serve,
  CLI `scripts/job_control.py`; vorhandene ContentIndex-/Page-/ACLverträge bleiben
  führend. Begrenzte DTOs, opt-in, Cursor, redigierte Fehler, Deliveryguard.
- R2: `src/job_control/index_{models,jobs,http}.py`; vorhandene catalog,
  controller, executor, registry, models und adapter_worker ergänzt.
  `ContentIndex.build` erhält gebundene Build-ID und Ownershipprüfung vor dem
  Ersetzen aktiver Sources. C16-/C18-Schemas additiv aktualisiert.
- R3: `src/model_evaluation/gold_candidates.py` und
  `src/tools_evaluation/gold_candidates.py`: Pending-Umschlag um vorhandene
  QuerySpec/GoldReference/Locator; Originalgrant-/Hash-/Zeilenvalidator und
  exklusiver Review-CSVexport, ohne Goldpromotion oder Originaländerung.
- Tests: übernommene Search-/Indexjob-Regressionen und Hilfsproben;
  `test_c24r_integration.py`, atomare Bereitschaftsmarkierung im eigenen
  `index_cancel_probe.py`, `test_gold_candidates.py`.
- Dokumentation: API-/Schemasnapshots, Inventar, Search-/Jobvertrag,
  [Validierung](c24r_integration_validation.md), drei Loviscach-Dokumente,
  leerer Realpool/Schema/CSV. `.gitignore` erlaubt ausschließlich diese expliziten
  öffentlichen Schema-/Beispiel-/Leerpooldateien. Vollständige Dateiliste und
  Dateihashes stehen im Liefermanifest.

## Abnahme #114

| Anforderung | Ergebnis | Nachweis/Grenze |
|---|---|---|
| vorhandene FTS5 am C16-Gateway, opt-in | implementiert | SearchHTTP/CLI, Default aus |
| begrenzte DTOs, Cursor, Fehler | implementiert/getestet | 49 Searchfälle ohne Socket bestanden |
| Live ACL, Owner/Course, Versionen, Widerruf | implementiert/getestet | echte temporäre ContentStore-/FTS5-Daten |
| Quellenanker, Generation, Wiederöffnung | implementiert/getestet | Pagevertrag und gemeinsame Handlerkette |
| echter HTTP-Roundtrip und API-Prozessrestart | Test vorhanden, hier blockiert | Socket-EPERM; keine vollständige HTTPabnahme |
| Cross-Repo-Vertrag | dokumentiert | versionierte bestehende API-DTOs; keine UI-Neuabnahme |

## Abnahme #115

| Anforderung | Ergebnis | Nachweis/Grenze |
|---|---|---|
| existierender Builder in C16/C18-Verträgen | implementiert | opt-in Prozess, Katalog, gemeinsame Job-/Artifactschemas |
| explizite Startfreigabe und Source-/Parsedbindung | implementiert/getestet | Operator/Owner, Course, hashgebundener Plan |
| Idempotenz, Restart, expliziter Retry | implementiert/getestet | SIGKILL vor/nach Aktivierung, keine Stagingadoption |
| Cancel, Ressourcen, Quarantäne | implementiert/getestet | Guardian, laufender Indexbuild, bestehende Prozessregression |
| atomare Generation/alte Generation bei Fehler | implementiert/getestet | ENOSPC-/Aktivierungs-/Ownershipfälle |
| autorisierter Status, Artifact-/Jobmetadaten | implementiert/getestet | Live-ACL und Deliveryguards |
| reale betriebliche Abnahme | nicht Gegenstand | synthetische lokale Testroots; kein Go-live |

## Abnahme #107 (begrenzte Vorbereitung)

| Anforderung | Ergebnis | Nachweis/Grenze |
|---|---|---|
| dokumentierte Material-/Rechteinventur | geliefert | keine Loviscach-Freigabe nachgewiesen |
| schema-validierbare unabhängige Referenzkandidaten | vorbereitet | Schema/Validator/CSV, 0 reale Kandidaten |
| getrennte Parsing-/Formelreferenzen | vorbereitet | bestehende C23-/C11-Verträge, keine erfundene Notation |
| berechtigter Realmaterialkorpus, Human-Gold, D07 | blockiert | Freigabe, Originale, Reviewer fehlen |

## Abnahme #108 (begrenzte Vorbereitung)

| Anforderung | Ergebnis | Nachweis/Grenze |
|---|---|---|
| quellgebundene Querykandidaten/Reviewexport | vorbereitet | stabile IDs, Originalhash/Version/Locator, Pendingstatus |
| unabhängig geprüfte reale Fundstellen/kompletter Pool | blockiert | 0 reale Kandidaten, keine automatische Freigabe |
| reale Retrievalraten/Nenner und Qualitätsgrenzen | nicht ausgeführt | erst nach Originalbindung und Humanreview |
| semantische/lexikalische reale Vergleichsabnahme | nicht ausgeführt | kein Cloud-/Modell-/Produktivaufruf |

Issuezustände wurden nicht verändert; technische Lieferung schließt kein Issue.
Kandidaten: **0 real, 0 bestätigt**; synthetische Fälle ausschließlich Tests.
Die bestehende operative CourseId ist CS50-begrenzt; Loviscach-Kurs-/ACLbindung
bleibt eine gesonderte Entscheidung. [Nächste Schritte](c24r_remaining_work.md).

## Tests und Risiken

Maßgeblich sind die aktuellen detaillierten Ergebnisse in
[c24r_integration_validation.md](c24r_integration_validation.md), einschließlich
failed/error/deselected/not_run. Kein vollständig grüner Repositorylauf behauptet.
Socketbeschränkung verhindert echte HTTPabnahme. Vorhandene Cacheumgebung weicht
bei zwei Paketen vom Rootlock ab. Formelsemantik, PDF-/DOM-/Zeitankerverifikation
und Originalunabhängigkeit benötigen menschliche Prüfung. Read-/Deliveryguards,
Limits und Quarantäne wurden nicht abgeschwächt. Kein Throughput-/Produktivnachweis.
C26 bleibt **HOLD**.

Abschließende Zahlen:

| Lauf | Bestanden | Fehlgeschlagen/Fehler | Übersprungen | Abgewählt |
|---|---:|---:|---:|---:|
| gemeinsame Regression (635 gesammelt) | 590 | 43 Fixtureerrors (Socket-EPERM) | 0 | 2 |
| Search-R1, erste Ausführung | 49 | 1 Socketfehler | 0 | 0 |
| Index-R2, gezielt | 19 | 0 | 0 | 0 |
| Handler-/Cancelabschluss | 3 | 0 | 0 | 1 |
| finale Kandidaten + atomarer Cancelprobe | 31 | 0 | 0 | 0 |
| C23-/Formelevaluation | 143 | 0 | 17 optionale SymPyfälle | 1 Realinventarfall |

Läufe überlappen und werden nicht addiert. Der Sammellauf vor Einbindung des
vorhandenen PyMuPDF-Cachepakets brach mit zwei Collectionerrors ab; eigene
Testentwicklungsfehler und deren erfolgreiche Nachprüfung sind im detaillierten
Protokoll enthalten. Echte HTTPabnahme und vollständige Lockinstallation bleiben
hier blockiert; reale fachliche Abnahme bleibt mangels Freigabe ausstehend.
