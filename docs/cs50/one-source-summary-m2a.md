# M2.1 – Bounded Multi-Batch Lecture Summarization

Stand: 07.11.2026. Technische Synthetikvalidierung PASS (489 bestandene Tests);
Anwendung im tatsächlichen Zielworktree und Integration HOLD / pending.
Technischer Entwicklungsstand und Tests siehe
[Validierung](one-source-summary-m2a-validation.md). Real Source Acceptance bleibt
HOLD. Es wurden ausschließlich selbst verfasste synthetische Daten und FakeLLM
verwendet. Fachliche und didaktische Qualität bleiben NOT_EVALUATED.

## Architekturentscheidung

Basis: `ff5e13340b83a86c69bcc38e787fbcdf05513074`, vorgesehener Branch
`feat/cs50p-summary-batching-m2a` im bestehenden Worktree
`Personal_Assistant-cs50-m2a`. AGENTS.md, beide M1-Dokumente und die beiden lokalen
M2-Berichte wurden gelesen. Die M2-Berichte bleiben unverändert. Ihre Befunde sind
historische Bestandsprüfung, kein M2.1-Reallauf: 237 Originalblöcke, 171 geeignete
Primary-Blöcke, 66 Ausschlüsse, mindestens 171 erforderliche Slices; historische
ProcessingApproval abgelaufen und aktuelle SummaryApproval nicht vorhanden.

Die kleinste tragfähige Erweiterung ist ein eigener Orchestrator
`src/cs50_summary_batch.py` über derselben M1-Engine. Ein Batch ist eine begrenzte
Ausführungseinheit, keine neue Quelle. Der Adapter stellt seine bestehende
Slice-Erzeugung zusätzlich als Iterator bereit. M1 sammelt daraus weiterhin
höchstens `config.max_chunks <= 32` Slices. `generate()` delegiert die bisherige
Section-/Store-Ausführung an `generate_refs()`. M1 behält Signatur, Inputsnapshot,
Cachekey, Requestserialisierung, Claimprüfung und Store-Zustände.

Eine Änderung von `SummaryConfig.max_chunks` auf 171 würde den M1-Vertrag und seine
Lauf-/Requestgrenzen aufweichen. Material- oder Source-IDs pro Batch umzubenennen
würde Provenienz erfinden; lange Blöcke durch abgeschnittene Katalogkopien
abzubilden würde Originaloffsets verlieren. Der neue Orchestrator übergibt deshalb
bereits vollständig geplante Original-SourceRefs an den gemeinsamen Kern. Es gibt
keinen zweiten Summarizer, keine alternative Claimvalidierung, keinen Provider und
keine Änderungen an Parser, Store-, Reader-, Material- oder Indexproduktdateien.

## Plan und Coverage

`plan` verifiziert die ganze gespeicherte Quelle über das unveränderte M1-Gate.
`run` verifiziert sie nochmals genau einmal für diese eigenständige Ausführung.
Es gibt keine Reader-Wiederholung pro Batch. Während `run` bleibt der MVP-Lock
gehalten; am Ende werden vollständiges Quellinventar, beide Approvalgültigkeiten
und aktuelle Implementierung erneut geprüft. Das Inventar bindet Pfade, Modi und
Bytes; unveränderte Access-Timestamps werden nicht behauptet.

Alle nichtleeren `primary`-Blöcke werden in Originalreihenfolge vollständig
berücksichtigt. Andere Aggregationsrollen und leere Blöcke werden mit Gründen
inventarisiert; `blank_text` hat dieselbe Priorität wie M1. Slices verwenden feste
Codepoint-Fenster und unveränderte Block-IDs, Offsets, Rawhashes und Locators.
Anders als M1 nimmt die neue Batch-API auch reine Whitespace-Fenster innerhalb
eines geeigneten Blocks auf. Damit bildet die Konkatenation seiner Slices exakt
sämtliche Originalzeichen ab. Ein ausschließlich leerer/Whitespace-Block bleibt
als ganzer Block ausgeschlossen.

Eine unabhängige Rekonstruktion prüft alle Bereiche und Ref-Hashes. Metadaten,
die das vorhandene öffentliche SourceRef-Modell verändern würde, führen bei der
Original-Locator-Prüfung zu HOLD; private Original-Evidence wird nicht durch eine
redigierte Referenz ersetzt. Die ParsedVersion ist unverändert am vollständigen
Plan, Engineinput und globalen Source-Envelope gebunden; das bestehende SourceRef-
Schema erhält kein neues Feld und keine erfundene Batch-Source-ID.

Der Plan enthält alle SourceRefs, exakte SHA-256-Werte der tatsächlich
serialisierten Sectionrequests, Originalblock-Fingerprint, Quelle einschließlich
aller M1-Versions-/Approval-/Intenthashes, Konfiguration, Limits und Ausschlüsse.
Geordnete Partitionierung verwendet `config.max_chunks` (höchstens 32) pro Batch.
Ein Request bleibt wie in M1 ein einzelner Slice, kein gesamter Batchprompt.
Batch-ID bindet Quelle, Konfiguration, Limits, Ordinal, SourceRefs und
Requesthashes. Batchzahl und alle Grenzen stehen vor dem ersten Request fest.
Kein FTS-Top-k, kein erster-32-Filter, keine stille Kürzung oder Zusammenfassung
verschiedener Originalblöcke in einer neuen Quelle.

Die globale Evidence prüft Anzahl, Reihenfolge, Identitäten, Sections, Claims,
Requesthashes und Inputzeichen gegen den Plan. Alle Batches müssen technisch
geprüft sein. Widersprüche über Batchgrenzen prüft dieselbe M1-Konsolidierung.
Globale Claims werden aus den geprüften Sections übernommen und nicht zusätzlich
zusammengeführt; auch identischer Wortlaut kann unterschiedliche Kontexte tragen.
M1s internes konsolidiertes Batchergebnis bleibt mitsamt den Originalsections
aufbewahrt. Rejected-Claims und Unsicherheiten bleiben in dessen Evidence erhalten
und führen wie in M1 zu HOLD. Ein vollständig erfolgreicher Bericht hat daher
leere globale Rejected-/Unsicherheitslisten.

Input-Coverage zählt verarbeitete Slices und Originalzeichen. Citation-Coverage
zählt unterschiedliche tatsächlich von akzeptierten Claims zitierte Ref-IDs und
listet unzitierte Ref-IDs. Beide Kennzahlen stehen separat im Bericht. 100 %
Citation-Coverage bedeutet, dass jeder Slice mindestens einmal zitiert wird; sie
behauptet weder, dass jeder Eingabecharakter zitiert wird, noch semantische oder
didaktische Vollständigkeit. Ein kürzerer wörtlicher Claim kann seinen Slice
zitieren, obwohl der restliche Slice ebenfalls als Input verarbeitet wurde.

## Grenzen

Die Schemaobergrenzen sind auch durch neue Approvals nicht erhöhbar:

| Grenze | Standard / harte Obergrenze |
| --- | --- |
| Gesamt-Slices | 512 / 512 |
| Batches | 32 / 32 |
| Gesamtrequests | 512 / 512, ein Request je Slice |
| Slices je Batch | `max_chunks`, CLI-Planstandard 32 / 32 |
| Gesamtlaufzeit | 600 s / 600 s |
| Batchlaufzeit | vorhandene SummaryConfig, 120 s / 180 s |
| Requesttimeout | vorhandene SummaryConfig, 20 s / 30 s, zusätzlich Restlaufzeit |
| Serialisierter Request | vorhandene SummaryConfig, 24.000 / 64.000 Bytes |
| Einzelne Rawantwort | vorhandene Enginegrenze 128.000 Bytes |
| Kumulative Rawantworten | 32.000.000 / 64.000.000 Bytes |
| Gesamte gespeicherte Ausgabe | 128.000.000 / 256.000.000 Bytes |
| Einzelne Source-Evidence / globale Summary | 16.000.000 / 16.000.000 Bytes |
| Approvalinput | 8 MiB; M1 weiterhin 64 KiB |
| Retries | exakt 0 |

Der Plan reserviert die maximale Rawantwortgröße pro geplanter Anfrage. Deshalb
kann eine kleinere Rawgesamtgrenze schon vor Erzeugung HOLD auslösen, auch wenn
die erwarteten Fake-Antworten kleiner wären. Die Standard-Rawgrenze erlaubt bis zu
250 Requests; für 251–500 braucht der Operator eine entsprechend höhere explizite
Grenze innerhalb des Schemas. Bei 501–512 Slices verhindert die maximale
Rawreservierung den Lauf bereits vor Erzeugung (512 × 128.000 > 64.000.000). Alle Gesamtgrenzen sind konfigurierbare Schranken,
keine Zusage, jede Quelle bis zur Schemaobergrenze verarbeiten zu können.

Die Laufzeitkontrolle ist kooperativ mit gebundenem Requesttimeout und Prüfung
nach Rückgabe, keine präemptive Prozessunterbrechung. Nur der bestehende lokale
FakeLLM wird instanziiert; ein blockierter oder bösartiger ausgetauschter Provider
ist nicht durch diese Grenze abgesichert. Die Gesamtdateigrenze wird vor Rootanlage, nach Batches und mit konservativer
Reservierung für Summary, Status und Manifest vor dem Gesamtabschluss geprüft.
Ein im Fehlerfall behaltenes Artefakt kann die Quote bereits überschreiten; dann
bleibt HOLD, es wird kein Abschlussmanifest erzeugt. Die Quote ist eine
Abnahmeschranke, kein Dateisystemquota-/RAM-Isolationsmechanismus.
Oversize-/Timeout-Evidence wird erhalten,
nicht zur Einhaltung einer Quote nachträglich gelöscht.

## Approval-Lifecycle und Bedienung

`BatchApproval` erweitert den vorhandenen `SummaryApproval`-Vertrag durch
`schema_version=2`, `adapter_version=one-source-summary-m2a-v1`, vollständigen `plan`
und `limits`. Geerbte Pflichtfelder bleiben: expliziter Operator, Nachweisreferenz,
zukünftiges Ablaufdatum, exakt geordnete M1-Aktionen, vollständige veröffentlichte
Quellenidentität und aktuelle Revision samt Pythonfingerprint. `config` und
`limits` müssen exakt mit dem neu berechneten vollständigen Plan übereinstimmen.
M1-Approvals, fremde/abgelaufene Approvals, geänderte Pläne, Code, Actor oder
Versionen ergeben HOLD. `plan` gibt ausschließlich `approval_required` mit
Implementierungsidentität und Plan aus, niemals `status=approved`.

```bash
python -m src.cs50_summary_batch plan \
  --source-root /absolute/private-existing-mvp \
  --source-id 'resource:<exact-hash>' \
  --parsed-version-id 'content_version_v1:<exact-hash>' \
  --actor explicit-operator

python -m src.cs50_summary_batch run \
  --source-root /absolute/private-existing-mvp \
  --source-id 'resource:<exact-hash>' \
  --parsed-version-id 'content_version_v1:<exact-hash>' \
  --actor explicit-operator \
  --approval /absolute/private-reviewed-inputs/batch-approval.json \
  --output-root /absolute/new-private-summary
```

Optional erhält `plan` private JSONdateien mit `--config` und `--limits`. `run`
liest diese Werte ausschließlich aus der Approval. Die Planausgabe enthält
Originaltext und ist privat zu behandeln. Das vollständige Approvalschema liefert
`BatchApproval.model_json_schema()`; der Operator erstellt und prüft das Attest
separat. Nur die Tests erzeugen ausdrücklich autorisierte Synthetik-Fixture-
Approvals. Es entsteht keine reale oder automatisch erteilte Freigabe.

Die historische ProcessingApproval wird unverändert durch M1s Originalgate gegen
Intent, Rawhash, Parser, damalige Implementierungsevidence und Ablauf geprüft.
Eine neue aktuelle BatchApproval ersetzt oder verlängert sie nicht. Die abgelaufene
M2-Importfreigabe bleibt ein eigenständiger Blocker bereits beim Planen. Ein neuer
Import erfordert eine getrennte Operatorentscheidung und neue gültige Importkette.

## Run-, Fehler- und Cachevertrag

Privater Root 0700, Dateien 0600, symlinkfreie isolierte absolute Pfade, exklusiver
M1-Rootlock. Gespeichert werden Originalapproval, Intent, Plan/Originalblöcke,
Batchkandidaten und deren getrennte technische Zustände sowie normale private
Engine-Runs mit Rawantworten, Sections und Resultaten. Batch-ID ist technische
Evidence; veröffentlicht wird ausschließlich die unveränderte Originalquelle.

Bis zur gesamten Nachprüfung bleibt der Root `pending`. Ein Fehler ergibt
`HOLD`, erhält erfolgreiche Batches, Rawantworten, Kandidaten und Fehlerklasse.
Bereits beanstandete Sections stoppen die Engine nach Sicherung ihrer Rawantwort
und Section, bevor der nächste Slice gesendet wird. Vor jeder Anfrage werden
Ablauf von Summary- und ProcessingApproval sowie verbleibende Budgets geprüft.
Bei Prozessabbruch kann `pending` bestehen bleiben. Das Abschlussmanifest fehlt
in beiden Fällen; Wiederholung darf daraus keinen vollständigen Lauf machen.
Kein Retry, keine automatische Reparatur, kein Weiterlaufen nach einem Fehler.
Ein neuer Lauf braucht eine explizite erneute Entscheidung und neuen isolierten
Root; nichts im fehlerhaften Root wird dafür überschrieben oder gelöscht.

Erst vollständige Konsolidierung, unveränderte Quelle und gültige Approvals
ermöglichen `completed`/`ready` und Abschlussmanifest. Fachreview bleibt überall
`unreviewed`, Claims niemals automatisch approved. Wiederholung/Prozessrestart
prüft die vollständige Quelle einmal, aktuelle Freigaben, alle Manifestbytes,
Plan, Batchzustände und globale Claims erneut und erzeugt keine Requests. Der
normale Enginecache bleibt verfügbar, ist jedoch kein Mittel zur automatischen
Fortsetzung eines HOLD-Roots. Ein offener oder manipulierter Root bleibt HOLD.

## Voraussetzungen für M2.2

1. Geprüften Patch im vorgesehenen beschreibbaren M2a-Worktree anwenden und dort
   finalen Codefingerprint und Regressionen bestätigen; reguläres Review und die
   separat autorisierte Integration der Dokumente bleiben ausstehend.
2. Exakte reale vollständige Quelle und Rawhash sowie Herkunft/Nutzungsentscheidung
   bestimmen. Historische abgelaufene Approval weder ändern noch verlängern.
   Falls Neuimport: expliziter neuer Auftrag, neuer privater Root, vollständiger
   MaterialPlan, aktuelle ProcessingApproval und neue gültige Publikationskette.
3. Im anschließend gesondert autorisierten Realtest alle gespeicherten Blöcke,
   Original-Locators und Reader-Seiten prüfen und vollständigen Batchplan erzeugen.
   Die historische Untergrenze 171 ist kein genauer neu berechneter Plan.
4. Neue explizite BatchApproval mit exakter Source-/ParsedVersion-/Raw-/Payload-/
   Projection-/Approval-/Intent-/Statebindung, aktuellem Code, vollständigem Plan,
   Grenzen, Fake-Konfiguration, Operatoridentität und Gültigkeit bereitstellen.
5. Neuen isolierten privaten Summaryroot und ausreichendes lokales Zeit-/
   Speicherbudget bereitstellen. Fehler führen HOLD; keine automatische Fortsetzung.
6. Technische Input-/Citation-Coverage, Claimoffsets, Original-Locators, Restart und
   unveränderte Quellbytes abnehmen. Fachliche und didaktische Stichproben separat
   reviewen. FakeLLM ist noch keine fachliche Synthese. Liveprovider bleiben einem
   eigenen Auftrag mit Provider-/Upload-/Modell-/Budgetfreigaben vorbehalten. Nach jedem späteren Commit
   oder einer Integration muss die aktuelle Revisions-/Bytebindung neu geprüft
   und eine dazu passende neue Approval vorgelegt werden.

## Ablage und Lifecycle

Diese Sitzung kann nur im bestehenden M2-Worktree und unter `/tmp` schreiben;
der vorgegebene M2a-Worktree ist lesbar, aber außerhalb der Schreibfreigabe.
Die Implementierung wurde deshalb aus dessen exaktem HEAD in einen isolierten
Dateistand `/tmp/cs50-m2a-work` exportiert. Eine kopierte `.git`-Verweisdatei erlaubt
nur die vorhandene Revisionsablesung; kein neuer Branch, Commit oder Worktree wurde
angelegt und kein gemeinsamer Gitindex verändert. Der vollständige anwendbare
Patch und beide Dokumente liegen im Lieferpaket unter `/tmp`.

Wegen dieser Ablagegrenze und des ausdrücklichen Commit-/Push-/PR-/Mergeverbots
bleiben Anwendung im Zielworktree, Review, Defaultbranch-Integration und allgemeiner
AGENTS.md-Lifecycle pending. Vorbestehende Branches/Worktrees, private Roots und
historische Nachweise bleiben erhalten. Der isolierte Arbeitsstand und Testlogs
bleiben zur Prüfung erhalten; `/tmp` ist kein dauerhaftes Archiv. Kein Cleanup
oder Releaseabschluss wird behauptet.
