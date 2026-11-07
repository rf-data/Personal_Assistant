# M1 – One-Source Lecture Summary

Testläufe, Dateihashes und Restrisiken stehen im separaten
[Validierungsbericht](one-source-summary-m1-validation.md).

## Architekturentscheidung vor Implementierung

Auftrag vom 07.11.2026; Zielbranch `feat/cs50p-lecture-summary-mvp`, vorhandener
Zielworktree `Personal_Assistant-cs50-summary-mvp`. Sauberer Ausgangs-HEAD:
`1839850249c17d855ee12bd1e0b632352ce09ffd`. Keine Git-Artefakte angelegt.
AGENTS.md, One-Source-MVP-Vertrag einschließlich Prompt 24/25 und dessen
Validierungsbericht wurden gelesen. Historische Evidence bleibt unverändert.

`src/lecture_summary` am lokal vorhandenen Remote-Tracking-Stand
`a0d3ebf7f64d44dd843f1848e70dc70a3a3af835` bietet Dateikatalog, SummaryService,
Original-Evidence und einfache/hierarchische Erzeugung. Sein Collector erwartet
registrierte Dateien statt veröffentlichter Store-Blöcke; der Offline-Provider
liefert ausdrücklich eine begrenzte Auswahl von Zitaten. Der alternative
`src/c27_learning_summary` verarbeitet bereits ContentBlocks mit Aggregationsrollen,
zerlegt vollständige geeignete Blöcke in referenzierte Slices, prüft wörtliche
Claims und besitzt FakeLLM sowie privaten Run-Store. Dieser Kern wird gewählt.
Neuere Batching-/LS3-/Review-Pipelines werden nicht übernommen.

Ausgewählte Provenienz ist der vollständige Commit
`dc26c72ffb8f1abd4a032601c524616840154171`. Minimal benötigte Modulclosure:
`adapter.py`, `engine.py`, `models.py`, `export_policy.py`,
`store.py`, `export.py` und der FakeLLM-Teil von `llm.py`. Store benötigt export,
Modelle und Adapter benötigen export_policy. Die Live-LiteLLM-Klasse wird entfernt.
Das nur aus einem Docstring bestehende, hier ignorierte `__init__.py` wird nicht
benötigt; der Namespace funktioniert als Python-Namespace-Package.
Keine URL-Freigabeliste wird übernommen: öffentliche Metadaten bleiben bei fehlender
Liste gesperrt. Original-Locators werden zusätzlich privat und unverändert gehalten.
Keine Branch-Historie und kein Cherry-Pick.

ContentStore öffnet standardmäßig read-only. Seine Kurzlisten-API unterstützt
höchstens 100 Blöcke und verweigert größere Dokumente. ContentReader bietet echte
signierte Seiten und vollständige TextWindow-Auflösung mit 16384 Codepoints pro
Fenster. Die gespeicherte, hashgeprüfte Projection enthält originale ContentBlocks
und Locators; öffentliche Reader-DTOs redigieren DOM-Pfade. M1 muss beide Ansichten
prüfen und alle Seiten lesen. Nur `primary` mit nichtleerem Text ist geeignet;
alle übrigen Blöcke werden mit Ausschlussgrund inventarisiert. FTS wird nicht benutzt.
Überschrittene C27-Grenzen ergeben HOLD vor Erzeugung, niemals Top-k oder Truncation.

Historische ProcessingApproval und Intent binden damalige Revision und Pythonbytes.
Neue src-Dateien ändern den aktuellen Fingerprint. M1 darf die alte Freigabe weder
umschreiben noch als aktuelle Retrievalfreigabe ausgeben. Eine neue SummaryApproval
bindet die historischen Nachweise, exakte veröffentlichte Version und aktuellen Code
für read-only Zugriff und Fake-Summary. Die ursprüngliche Freigabe wird gegen ihre
damaligen Bindungen geprüft; die neue gegen die aktuelle Implementierung. Für Tests
wird ausschließlich neue eigene Synthetik importiert.

## Konflikte und Integrationsgrenze

PR #171 wurde über GitHub lesend geprüft: offen, Draft, nicht gemergt;
Head `929fb1e1aa821e779b7d7ad327cf5a323666bd31`, Base
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Stage-0-Paket und CI-Evidence,
einschließlich des dort dokumentierten SQLite-B1, sind keine M1-Abnahme.
Die PR-Produktdateien betreffen Material-Acquisition, Code-ZIP, Storage und
Textvalidierung. M1 ändert diese Dateien nicht. Der gewählte Summary-Namespace
existiert in der Ausgangsbasis noch nicht. Bei späterer Integration größerer
C27-Branches sind insbesondere doppelte Definitionen dieses Namespaces und
abweichende Provider-/Cache-Verträge manuell zu prüfen. Keine Aussage über
Mergefähigkeit durch einen tatsächlich ausgeführten Merge.

Der vorhandene lokale `origin/master`-Tracking-Ref steht ebenfalls exakt auf
`1839850249c17d855ee12bd1e0b632352ce09ffd`. Gegen diese maßgebliche Basis gibt es
keine Änderung vorhandener Produktdateien: M1 ergänzt einen neuen Namespace und
einen neuen Operator unter src. Die bestehenden Read-APIs werden ohne Schema- oder
Signaturänderung verwendet. Das veraltete lokale `master` ist kein Vergleichsersatz.

Das lokale `master` ist ein veralteter gemeinsamer Ref (`c1007ef...`); es wird weder
als aktuelle Basis verwendet noch verändert. Maßgeblich ist ausschließlich der
beauftragte Merge-Commit. Im Implementierungsauftrag waren Commit, Push, PR und
Merge untersagt. Der Folgeauftrag erlaubt die Vorbereitung für Commit und Draft-PR;
er beauftragt keine Veröffentlichung und verbietet Änderungen an PR #171, an
`master` sowie automatische Merges. Defaultbranch-Integration und Lifecycle-Abschluss
bleiben pending; der vorhandene Branch und Worktree müssen erhalten bleiben.

## Vorab-Testplan

Eigene HTMLbytes durch echten MVP-Import/Parser/Handoff/Store/FTS, danach M1 ohne
Parser/Download/Netz. Claims gegen vollständige Originalblöcke prüfen; falsche,
abgelaufene und codefremde Freigaben, Rawänderungen und Versionskonflikte abweisen.
Alle Reader-Seiten und lange Fenster prüfen, Kontextüberschreitung explizit halten.
Separaten Prozessrestart, identische Wiederholung und unverändertes Quellinventar
prüfen. C27-Claim-/Cache-/Fehlerregressionen und relevante MVP-/Store-/Reader-Tests
ausführen. Ruff und verbleibende Grenzen separat dokumentieren.

## Bedienung und gespeicherter Vertrag

Der Aufruf führt ausschließlich den expliziten lokalen Auftrag aus:

```bash
python -m src.cs50_summary_mvp \
  --source-root /absolute/private-existing-mvp \
  --source-id 'resource:<exact-source-hash>' \
  --parsed-version-id 'content_version_v1:<exact-version-hash>' \
  --approval /absolute/reviewed-inputs/new-summary-approval.json \
  --output-root /absolute/new-private-summary \
  --actor explicit-operator
```

Alle Pfade sind absolut und symlinkfrei. Der neue Root liegt außerhalb des
Repositories und überschneidet sich weder mit Quellroot noch Approval. Sein
Elternverzeichnis muss existieren. Ein fremder vorhandener oder leerer Root wird
nicht übernommen. Rootmodus 0700, Dateien 0600. Die bestehende MVP-Lockdatei wird
nur geöffnet und gesperrt; nichts im Quellroot wird geschrieben. Inventare aus
Pfaden, Modi und Dateihashes werden vorher/nachher verglichen. Diese Prüfung
belegt keine unveränderten Access-Timestamps.

`SummaryApproval` ist ein lokales Operatorattest, keine Signatur oder automatisch
erteilte Realfreigabe. Alle Felder sind Pflichtfelder; die private Datei muss dem
aktuellen User gehören. `schema_version=1`, `status=approved`, `approved_by` exakt
wie `--actor`, konkrete `evidence_reference`, zukünftiges `valid_until` mit Zeitzone.
Die Aktionen sind exakt und geordnet:
`["read_verified_html", "summarize_fake", "store_private_summary"]`.
Es folgen `source_id`, `source_version_id`, `parsed_version_id`, `raw_sha256`,
`payload_sha256`, `projection_sha256`, `processing_approval_sha256`,
`mvp_intent_sha256`, `mvp_state_sha256`, aktuelle `implementation_revision` und
`implementation_sha256`, `adapter_version=one-source-summary-m1-v1` sowie `config`.
Die JSON-Schemadefinition ist direkt über `SummaryApproval.model_json_schema()`
lesbar. Der aktuelle Implementierungsfingerprint ist unverändert der bestehende
`scripts.cs50_learning_mvp.implementation_identity()`-Vertrag: alle Pythondateien
unter src plus bestehender MVP-Operator. M1 liegt deshalb vollständig unter src;
es gibt keinen ungehashten neuen CLI-Operator.

`config` verwendet den bestehenden C27-SummaryConfig-Vertrag. M1 erlaubt nur
`provider=fake`, `model=fake-extractive-v1`, `retries=0`. Standard: 2000 Codepoints
pro Slice, maximal 24 Slices (vertragliche Obergrenze 32), maximal 24000 Bytes pro
serialisierter Section-Anfrage. Grenzen werden vor Rootanlage geprüft. Auch bei
mehr als 100 Blöcken werden zunächst alle Reader-Seiten geprüft; überschreitet
die vollständige Eingabe anschließend das C27-Budget, folgt HOLD. Es wird keine
kleinere Teilquelle automatisch gewählt. Reine Whitespace-Slices erzeugen gemäß
C27 keine Claims; Originalblöcke bleiben vollständig in der Evidence-Datei.

Der private Zielroot enthält unveränderliche Approval-, Intent-, Evidence- und
Summary-Dateien, eine Zustandsdatei, ein Abschlussmanifest und den privaten
C27-Engine-Run mit Rawantworten und Sections. `evidence.json` erhält sämtliche
originalen ContentBlocks samt unveränderten Locators und eine Zuordnung von
jedem Claim-Ref über Block-ID und Offsets zur ParsedVersion. Das öffentliche
C27-Metadatenmodell ersetzt nicht diese private Original-Evidence.
`summary.json` enthält Claims, vollständige Eingabe- und Zitationscoverage,
ausgeschlossene Blöcke mit Gründen, Warnungen, `review_status=unreviewed`,
Source-/Versionshashes sowie eine M1-Cacheidentität. Die separate C27-Cacheidentität
bleibt innerhalb des eingebetteten Engine-Ergebnisses erhalten.

Der Zustand bleibt bis nach Quell- und Ergebnisnachprüfung `pending`. Erst danach
entstehen Summary, `ready` und Abschlussmanifest. Ein Fehler lässt Teilzustände
zur Untersuchung bestehen. Wiederholung prüft neue und alte Freigabe, aktuellen
Code, vollständige Quelle, sämtliche Zielhashes, Evidence und Claims erneut;
sie ruft FakeLLM nicht erneut auf. Ein unvollständiger oder geänderter Zielroot
führt zu HOLD ohne automatische Recovery oder Retry. Cacheprüfung aktualisiert
keine Statusdatei. Exitcode 0 bedeutet technischen Abschluss, niemals fachliche
Abnahme; Exitcode 2 und JSON auf stderr bedeuten HOLD.

Die historische Freigabe muss weiterhin gültig sein und mit damaligem Intent,
Plan, Parser, Akteur und ImplementationEvidence übereinstimmen. M1 verwendet sie
als Nachweis des früheren Imports. Die neue Freigabe autorisiert allein den neuen
Lese-/Summary-Auftrag. Die bestehende MVP-Suche bleibt bei einem historischen
Codefingerprint ausdrücklich gesperrt; ihre Schranke wird nicht geändert.


## M1-Release-Vorbereitung (Folgeauftrag 07.11.2026)

Status: **für Commit und Draft-PR vorbereitet; nicht veröffentlicht**. Vorhandener
Headbranch `feat/cs50p-lecture-summary-mvp`, Zielbase `master`, geprüfte Basis
`1839850249c17d855ee12bd1e0b632352ce09ffd`. GitHub bestätigt `master` als
Defaultbranch und diesen aktuellen Live-Head. Der lokale `master` bleibt unverändert.
Implementierungs- und Testbytes werden in diesem Folgeauftrag nicht geändert.

Die Liefermenge ist exakt diese Allowlist von 13 neuen Dateien; der CI-Vorschlag
und der Testplan stehen in den beiden schon enthaltenen Dokumenten. Kein
Validator, Workflow, historisches Manifest oder Laufartefakt kommt hinzu.

```text
docs/cs50/one-source-summary-m1-validation.md
docs/cs50/one-source-summary-m1.md
src/c27_learning_summary/adapter.py
src/c27_learning_summary/engine.py
src/c27_learning_summary/export.py
src/c27_learning_summary/export_policy.py
src/c27_learning_summary/llm.py
src/c27_learning_summary/models.py
src/c27_learning_summary/store.py
src/cs50_summary_mvp.py
tests/fixtures/cs50_summary_m1/c27-catalog.fixture
tests/test_cs50_summary_c27_regression.py
tests/test_cs50_summary_mvp.py
```

Commit-Titel: `feat(cs50): add offline one-source lecture summaries (M1)`.
Draft-PR-Titel: `feat(cs50): One-Source Lecture Summary M1 (offline)`.
Vorgesehener PR-Text:

> M1 erzeugt aus genau einer verifiziert veröffentlichten HTMLquelle eine private
> Offline-Summary mit FakeLLM. Eine neue SummaryApproval bindet aktuelle
> Implementierung, Quellversion und historische Importnachweise; Claims bleiben
> auf vollständige Originalblöcke und Locators zurückführbar und unreviewed.
>
> Umfang: sieben selektiv übernommene C27-Module ohne Liveprovider, ein M1-Operator,
> zwei Testsuites, synthetische Fixture und zwei Dokumente; genau 13 neue Dateien.
> Die bestehende Import-/Store-/Reader-Implementierung bleibt unverändert.
>
> Validierung: dokumentierter M1-Schlusslauf mit 438 passed, 1 deselected, ohne
> Skips/Xfails; Ruff check/format bestanden. Im Vorbereitungslauf sind Code- und
> Testhashes unverändert. Eine separate lokale Probe bestätigt den CI-Konflikt
> mit PR #171 und prüft den dokumentierten Korrekturvorschlag; sie ersetzt keinen
> vollständigen Regressionstest auf einem kombinierten Git-Stand.
>
> Draft: CI-Koexistenzkorrektur und gemeinsamer Stage-0-/M1-Lauf stehen aus.
> SQLite-B1 aus PR #171 bleibt offen. Realmaterial, Liveprovider, Deployment und
> fachliche Abnahme sind nicht freigegeben. Keine automatische Merge-Aktion.
> Details: docs/cs50/one-source-summary-m1-validation.md und Testplan in
> docs/cs50/one-source-summary-m1.md.

Der echte Git-Index und die gemeinsame Git-Objektdatenbank liegen außerhalb der
beschreibbaren Workspace-Grenze. Die konkrete Staging-Vorschau verwendet deshalb
nur einen separaten Index und neue Objekte unter `/tmp`; sie verändert den echten
Index nicht. Der Validierungsbericht nennt Pfad und Prüfungen dieses Pakets.
Ein späterer Commit muss genau die obige Allowlist enthalten; anschließend
`git diff --cached --name-status` und `git diff --cached --check` prüfen.
Bei zusätzlichen, fehlenden oder bereits fremd gestagten Dateien anhalten.
Commit, Push und Eröffnung des Draft-PR sind in diesem Vorbereitungslauf nicht
vollzogen. Nach einem Commit gelten neue Revisionsbindungen für Lauf-Freigaben.

## Minimaler CI-Korrekturvorschlag (separat umzusetzen)

Ausgangspunkt ist ausschließlich
[validate.py aus PR #171](https://github.com/rf-data/Personal_Assistant/blob/929fb1e1aa821e779b7d7ad327cf5a323666bd31/ci/c27-stage0/validate.py).
Die historische Stage-1-Abwesenheit wird aus `verify_prerequisites` in eine eigene
Prüfung verschoben. Nur der feste historische BASE-Snapshot ruft sie vor und nach
Anwendung des unveränderten Stage-0-Patches auf. Der aktuelle Checkout darf die
M1-Dateien enthalten; deren Freigabe erfolgt durch eigene Reviews und Tests.
Das gilt nicht als Abnahme des vollständigen historischen Stage-1-Pakets.

```diff
--- a/ci/c27-stage0/validate.py
+++ b/ci/c27-stage0/validate.py
@@ -134,6 +134,10 @@
         check_hash(root, name, expected)
     for name in DEFERRED:
         require(not safe_path(root, name).exists(), f"Deferred profile exists: {name}")
+
+
+def verify_stage0_isolation(root, data):
+    """Stage-1 absence belongs to the historical Stage-0 snapshot only."""
     for name in data["stage1"]["allowlist"]:
         require(not safe_path(root, name).exists(), f"Stage-1 path exists: {name}")

@@ -311,12 +315,13 @@
     print("PASS: complete Review-v2 package, pinned manifest, patch and SHA256SUMS")
     verify_candidate(root, data)
     print(
-        "PASS: checkout: 6 products, 40 prerequisites, deferred/Stage-1 absence, syntax"
+        "PASS: checkout: 6 products, 40 prerequisites, deferred absence, syntax"
     )
     with tempfile.TemporaryDirectory(prefix="c27-stage0-base-") as temporary:
         snapshot = Path(temporary)
         export_base(root, snapshot)
         verify_prerequisites(snapshot, data)
+        verify_stage0_isolation(snapshot, data)
         for name, record in data["stage0"]["files"].items():
             if record["base_sha256"] is None:
                 require(
@@ -334,6 +339,7 @@
         )
         git(snapshot, "apply", "--whitespace=error-all", "-", input_bytes=patch)
         verify_candidate(snapshot, data)
+        verify_stage0_isolation(snapshot, data)
         print("PASS: isolated base + exact v2 patch reproduces all 6 product hashes")
         smoke(snapshot)
     print(
```

Unverändert bleiben `BASE`, `PRODUCTS` (sechs Dateien), alle 40 Prerequisite-Hashes,
`DEFERRED`, Pfad-/Symlink-/Modus-/Syntaxprüfungen, Paketabdeckung, Manifest-, Patch-
und SHA256SUMS-Pins, BASE-Produktprüfungen, `git apply --check`, Patch-Reproduktion,
Smoke und Headprüfung. Der exakt gepinnte Patch kontrolliert weiterhin den
historischen Stage-0-Änderungsumfang. Kein pauschaler Gesamtdiff gegen BASE darf
spätere eigenständige M1-Änderungen als Stage-0-Scope ausgeben. Historische Manifeste,
Reviewtests und Nachweise werden weder umgeschrieben noch neu signiert.

Für eine spätere separate CI-Korrektur muss auch der aktuelle Test
`ci/c27-stage0/tests/test_validate.py::test_stage1_overlay_is_rejected` angepasst
werden: derselbe eigene Overlay besteht `verify_candidate`, wird aber durch
`verify_stage0_isolation` abgewiesen. Hinzu kommen Prüfungen beider historischen
Aufrufstellen und der sieben konkreten M1-Überlappungen. Alle übrigen
Manipulations-/Headtests bleiben erhalten. Diese Testanpassung betrifft aktuelle
CI-Tests, nicht das gehashte historische Reviewpaket. PR #171 bleibt hier unangetastet.

## Kombinierter Regressionstest Stage 0 + M1 (Release-Gate)

Die folgenden Läufe sind verbindlicher Plan, noch keine gemeinsame Abnahme.
Vergleichsstände: M1 auf `1839850…`, Stage 0 auf `929fb1e…`, danach ein eigener
kombinierter Git-Stand aus aktueller Zielbasis, den sechs exakten Stage-0-Produkten,
Reviewpaket/CI, geprüfter CI-Korrektur und exakt der M1-Allowlist. Sämtliche
Commit-IDs und Dateihashes vor dem Lauf festhalten. Keine bestehenden historischen
Roots übernehmen. Der kombinierte Stand muss einen echten eigenen HEAD haben;
keinen Head per Umgebungsvariable vortäuschen. Weder PR #171 noch master dafür ändern.

| Prüfung | Ausführung und Erfolgskriterium |
| --- | --- |
| Historische Isolation | Original-BASE exportieren, unveränderten gepinnten Patch anwenden; vor/nach Patch alle 55 Stage-1-Pfade abwesend. Eigene negative Overlays pro Pfad einschließlich Symlink müssen abgewiesen werden. Beide Aufrufstellen gezielt prüfen. |
| Aktuelle Koexistenz | Alle sieben M1-C27-Dateien im kombinierten Checkout zulassen; sechs Produkte, 40 Prerequisites und Reviewpaket bleiben exakt gepinnt. Änderungen, fehlende Dateien, Modi, Symlinks, neue Prüfsummenbindungen und falscher Head bleiben Fehler. |
| Workflow | Validator mit Python 3.12 `-I -S -B`, realem `--expected-head`, danach aktuelle stdlib-Vertragstests. Zusätzlich kombinierten Stand testen: der Workflow aus #171 checkt nur den PR-Head aus und belegt allein keinen späteren Merge-Stand. |
| publish_bytes | Echte Linux-`renameat2`-Publication ohne AST-Ersatz im Produktlauf: erste Bytes unverändert, zweiter Aufruf FileExistsError, kein Überschreiben und keine `.material-*`-Reste im Normal-/Konfliktfall. `publish_file` verschiebt ohne Quelle zurückzulassen. Fehlende Syscall-Unterstützung ist Fehler, kein Skip. |
| Publication-Fehler | Fehler vor Veröffentlichung, nach Veröffentlichung mit verlorener Antwort und vor Indexaktivierung einschleusen. Pending-/HOLD-Zustand erhalten, keine automatische Wiederholung, Reparatur oder Adoption unbekannter Reste. fsync-/Publication-Fehler dürfen keinen Erfolg melden. |
| ContentStore | Echter HTML-v2-Import mit Quality/Handoff und `ImplementationEvidence`; Raw-, Payload-, Projection-, Receipt- und ParsedVersion-Bindungen prüfen. Neustart/idempotenter Abruf, Korruptionsfälle, Quarantäne und read-only Grenzen über bestehende Suites prüfen. |
| Reader und M1 | Import → Store → FTS/MVP-Retrieval → Reader → M1. Alle Seiten bei >100 Blöcken, alle TextWindows langer Blöcke, komplette Slice-Coverage oder HOLD vor Truncation. Jeden Claim gegen Originaltext, Offsets, Block-ID, Rawhash, ParsedVersion und Locators prüfen. |
| Freigabefingerprints | Auf jedem echten Git-Stand `implementation_identity()` neu ermitteln; ProcessingApproval und SummaryApproval nur für eigene neue Synthetik erzeugen. Stage-0-Pythonänderungen ändern den Bytefingerprint; jeder Commit ändert die Revision, auch bei gleichem Bytefingerprint. Alte Freigaben/Intents bytegleich erhalten. |
| Historische Freigaben | Alte MVP-Suche liefert bei Revisions-/Fingerprintwechsel HOLD. Separat aktuelle SummaryApproval darf nur gegen weiterhin gültige und intern stimmige historische Importnachweise arbeiten. Fehlende, abgelaufene, doppelte oder abweichende Bindungen ablehnen, Quelle/Ziel unverändert halten. |
| Wiederholung/Restart | Summary-Wiederabruf und eigener CLI-Prozess liefern identische Berichte/Inventare ohne erneute Parser-, Download-, Index-, Source-Publication- oder FakeLLM-Aufrufe. Defekte Teilruns bleiben HOLD. |

Im kombinierten Stand zuerst den korrigierten Validator und seine Tests ausführen:

```bash
python -I -S -B ci/c27-stage0/validate.py --root . --expected-head "$(git rev-parse HEAD)"
python -I -S -B -m unittest discover -s ci/c27-stage0/tests -v
```

Danach den vollständigen 438-Fälle-Befehl aus dem
[Validierungsbericht](one-source-summary-m1-validation.md) auf diesem Stand mit
neuer `mktemp -d`-Evidencewurzel und eigenem `--basetemp`, Log und JUnit ausführen.
Zusätzlich `tests/test_cs50_code_zip.py`, `tests/test_content_store_artifacts.py`
und `tests/test_content_store_concurrency.py` aufnehmen. Zusätzliche gezielte
Publication-/Fingerprintfälle aus der Tabelle als eigene CI-Korrekturtests
implementieren; sie gehören nicht nachträglich zu den 13 M1-Lieferdateien.
M1 muss die echte Stage-0-Funktion importieren, nicht eine Testkopie.

Bestehende isolierte Python-3.12-Umgebung benutzen, Plugin-Autoload und Bytecode
abschalten, Cacheprovider deaktivieren, neue private synthetische Roots und
Netzsperre verwenden. Keine alten Approvals neu hashen oder reale Quellen
freigeben. Die Zahl der zusätzlich ausgewählten Tests bei Collection erfassen;
438 ist die bisherige Teilmenge und keine vorweggenommene neue Gesamtsumme.
Nur den bestehenden externen Originalmaterialfall ausdrücklich abwählen, keine
neuen Skips/Xfails. Alle ausgewählten Fälle müssen bestehen; B1 bei Auftreten mit
Erstfehler, Log und Datenbankzustand dokumentieren, nicht durch Wiederholen verdecken.

Nach letzter Codeänderung einmal gemeinsam prüfen; Revision, Fingerprint,
Publication-Implementierung, Python-/Bibliotheksversionen, Collection, Exitcodes,
JUnit-Zahlen und Hashes der neuen Logs dokumentieren. Der bisherige M1-Testbericht
und Stage-0-Nachweise bleiben historische Evidenz. Erst dieser kombinierte Lauf
kann das technische Koexistenz-Gate schließen.
