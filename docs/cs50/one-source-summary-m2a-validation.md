# M2.1 – Validierung

**Aktueller Stand:** Die gezielte Fehlerdiagnose und Fixture-Stabilisierung vom
07.11.2026 steht im [neuen Diagnoseabschnitt](#gezielte-fehlerdiagnose-und-fixture-stabilisierung-07112026).
Gesamtentscheidung dieses Folgeauftrags: **HOLD**, weil die historische konkrete
Exceptionquelle nicht nachgewiesen werden konnte und die Patchanwendung aussteht.
Frühere PASS-Aussagen und Export-/Anwendungsangaben bleiben historische Evidence.

Stand: 07.11.2026. Entwicklungsumfang und Verträge stehen in
[one-source-summary-m2a.md](one-source-summary-m2a.md).

## Abnahmegrenze und Umgebung

Vorgesehener bestehender Worktree `Personal_Assistant-cs50-m2a`, Branch
`feat/cs50p-summary-batching-m2a`, Basis-HEAD
`ff5e13340b83a86c69bcc38e787fbcdf05513074`. Initialer Zielstatus sauber.
Der Sitzungssandbox erlaubt dort ausschließlich Lesezugriffe; beschreibbar sind
der separate M2-Worktree und `/tmp`. Daher isolierter Export genau dieses HEAD
unter `/tmp/cs50-m2a-work`, keine Änderung des vorgegebenen Zielworktrees. Die
kopierte `.git`-Verweisdatei dient nur der Revisionsablesung durch die bestehende
Implementierungsidentität. Kein Commit, Indexstaging, Branch-/Worktree-Anlegen,
Push, Remotezugriff, PR, Merge oder Cleanup.

Die beiden M2-Berichte wurden im separaten Worktree nur gelesen. Die Zahlen
237/171/66 und die drei M2-Blocker sind historische Befunde. Kein Zugriff auf
reale CS50P-Rohdaten, kein Realimport und keine Verarbeitung einer realen Quelle.
Auch private bestehende Material-/Summaryroots werden nicht verändert. Lesender
Zugriff auf vorhandene Abhängigkeitscaches und vorhandene Pakete ist separat von
Quellmaterial zu verstehen.

Python 3.12.12 in `/tmp/cs50-m2a-env`, ausschließlich über lokale vorhandene
Paketpfade: Pydantic 2.13.4, pytest 9.1.1, BeautifulSoup 4.15.0, soupsieve 3.0.4,
charset-normalizer 3.5.1 und Ruff 0.16.3. Keine Installation, Paketauflösung,
Downloads oder Cacheänderung. Das ist kein neuer hashgepinnter Wheelhouse-
Installationsnachweis. Fremde pytest-Plugins werden mit
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` deaktiviert; Repositoryplugins und expliziter
`tests.offline_guard` sind aktiv. Der Guard blockiert Python-Netz-/Listeneraufrufe
und Infrastrukturkommandos. Er ist keine OS-Sandbox und propagiert nicht automatisch
in Kindprozesse. Die getesteten CLIs besitzen ausschließlich FakeLLM und lokale
Pfade; kein Netz-/Provideraufruf wurde ausgeführt.

## Historische und vorbereitende Läufe

M1s dokumentierte 438 bestandene Tests (PR #173 integriert laut Auftrag) bleiben
historischer Nachweis, nicht M2.1-Lauf. Die bestehenden Berichte werden nicht
umgeschrieben und diese Zahl nicht als neue Ausführung ausgegeben.

Neue vorbereitende Versuche bleiben unter `/tmp` nachvollziehbar:

| Versuch | Resultat und Konsequenz |
| --- | --- |
| `cs50-m2a-new-first.log` | pytest-Startfehler vor Collection: fremder Pluginentrypoint `platformdirs.pytest_plugin` aus gemischten lokalen Cachepfaden. Explizite Deaktivierung fremder Plugin-Autoloads; kein Skip/Xfail. |
| `cs50-m2a-new-second.log` | 1 fehlgeschlagener 171-Block-Test nach 57,10 s: während dieses Entwicklungslaufs geänderter Code invalidiert die Approval; vorhandene Batch-/Sectionevidence und HOLD bleiben erhalten. Revalidierung wird anschließend effizient auf Anfang/Ende begrenzt, Ablaufprüfung bleibt pro Request. |
| `cs50-m2a-new-third.log` | 1 fehlgeschlagener Fall beim MVP-Setup nach 27,58 s: `Unavailable`, Index bereits aktiv, MVP noch `index_pending`. Die Phase grenzt den Fehler auf die anschließende MVP-Retrievalprüfung ein; ein bestehendes Retrievalzeitlimit unter konkurrierender lokaler Last ist eine Vermutung, der genaue Untergrund wurde nicht isoliert reproduziert. Keine Änderung an Index oder dessen Limits, Root bleibt erhalten. |
| `cs50-m2a-small-debug.log` | Kleine Quelle: 1 passed in 10,24 s. |
| `cs50-m2a-new-fourth.log` | 94 passed in 212,59 s: 47 neue Batchfälle und 47 unveränderte C27-Regressionen. Einschließlich vollständigem 171-Block-Lauf, Cacheabruf und Prozessrestart. Vor den letzten zusätzlichen Budget-/Abbruchprüfungen; kein finaler Nachweis. |
| `cs50-m2a-last-preflight.log` | Bewusst mit SIGINT beendet, um statt eines weiteren isolierten Vorlaufs den vollständigen gemeinsamen Schlusslauf nach der letzten Codeänderung auszuführen. Evidence bleibt erhalten; kein erfolgreicher Testnachweis. |

Zusätzlich scheiterte die erste lokale Umgebungsvorbereitung am systemweiten
Python-3.11-Tar-API-Unterschied und anschließend am falschen venv-Interpreterhome.
Der Export wurde mit vorhandenem Python 3.12 und die temporäre venv mit exaktem
Interpreterpfad vorbereitet. Keine fremde Umgebung wurde repariert oder verändert.

Ein erster gemeinsamer Schlusslauf (`cs50-m2a-final-interrupted.log`) wurde nach
51 Batch-, 42 M1-, 47 C27- und bereits angelaufenen MVP-Prüfungen bewusst
unterbrochen (SIGINT, Exit 130). Die finale Codeprüfung ergänzte die getrennte
Fehlerzuordnung: globale Konsolidierungsfehler halten den Gesamtlauf, ohne einen
bereits geprüften Einzelbatch nachträglich als fehlgeschlagen auszugeben. Ein
zusätzlicher Assert im bestehenden Widerspruchstest prüft sämtliche Batchzustände.
Der folgende gemeinsame Lauf wurde danach vollständig neu gestartet.

## Schlusslauf nach letzter Codeänderung

Der genaue lokale Launcher liegt unter `/tmp/cs50-m2a-final.sh`:

```bash
cd /tmp/cs50-m2a-work
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
/tmp/cs50-m2a-env/bin/python -m pytest \
  tests/test_cs50_summary_batch.py \
  tests/test_cs50_summary_mvp.py tests/test_cs50_summary_c27_regression.py \
  tests/test_cs50_learning_mvp.py tests/test_content_store_adapters.py \
  tests/test_content_store_integrity.py tests/test_content_read_contracts.py \
  tests/test_content_fts.py tests/test_content_retrieval_integration.py \
  tests/test_content_index_projection.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_html.py tests/test_cs50_material_html_semantics.py \
  tests/test_cs50_material_quality.py \
  -m 'not external_integration' -q -p no:cacheprovider -p tests.offline_guard \
  --basetemp=/tmp/cs50-m2a-final-v2-tests \
  --junitxml=/tmp/cs50-m2a-final-v2-results.xml \
  > /tmp/cs50-m2a-final.log 2>&1
```

Die externe optionale Originalquelle wird ausdrücklich vor Ausführung abgewählt;
sie ist weder bestandener Test noch Skip. Keine neuen Skips oder Xfails. Die
synthetischen Setupimporte dürfen echte Parser, Storepublication und Index benutzen;
ab Beginn der Summary sind diese Einstiegspunkte im 171-Block-Test gesperrt.
Alle Roots sind neu und synthetisch.

**Technische Synthetikvalidierung PASS: 489 passed, 1 deselected in 664,53 s; Exitcode 0.**

51 neue Batchtests und alle 438 ausgewählten bestehenden M1-/MVP-/Store-/Reader-/
Retrieval-/Materialfälle bestanden. JUnit: 489 Testcases, 0 Failures, 0 Errors,
0 Skips; keine Xfails/Xpasses. Der eine optionale Realquellentest ist ausschließlich
vor Ausführung abgewählt. Anwendung im Zielworktree und Integration bleiben
**HOLD / pending** wegen der unten dokumentierten Grenzen.

| Datei | Bestandene Fälle |
| --- | ---: |
| `test_cs50_summary_batch.py` | 51 |
| `test_cs50_summary_mvp.py` | 42 |
| `test_cs50_summary_c27_regression.py` | 47 |
| `test_cs50_learning_mvp.py` | 50 |
| `test_content_store_adapters.py` | 49 |
| `test_content_store_integrity.py` | 16 |
| `test_content_read_contracts.py` | 14 |
| `test_content_fts.py` | 47 |
| `test_content_retrieval_integration.py` | 6 |
| `test_content_index_projection.py` | 41 |
| `test_cs50_material_processing.py` | 8 |
| `test_cs50_material_html.py` | 7 |
| `test_cs50_material_html_semantics.py` | 17 |
| `test_cs50_material_quality.py` | 94 |

Finales Log SHA-256: `c2a0d78d2e1ccde5c44265c901a38a7f6a0fbc25350f820e0682371af613db6e`;
JUnit SHA-256: `c705c4351d83a082f1e15975f7d6744e00a7aa3a07280b966942900642615e9b`.


Ruff check und format --check bestanden für beide geänderten Kernmodule, neuen
Operator und neue Tests. `git diff --check` bestanden. Nach dem Schlusslauf werden
Produktbytes und Dokumente für den anwendbaren Patch erneut geprüft.

## Synthetischer 171-Block-Benchmark

Die Fixture erweitert die fünf geeigneten Primary-Blöcke des bestehenden eigenen
MVP-Test-HTML um 166 neue Absätze. Keine echte Lecture und keine Umbenennung
historischer Rohbytes. Jede SourceRef wird über Originalblock, Offsets und
unveränderte Locators geprüft; Reader liefert genau zwei Seiten mit insgesamt
171 Blöcken. Die vollständige Quelle wird je `run` genau einmal über M1 gelesen.

| Messwert | Ergebnis |
| --- | --- |
| Originalblöcke / geeignete Blöcke / Ausschlüsse | 171 / 171 / 0 |
| Geplante und geprüfte Batches | 6 / 6 |
| Geordnete Batchgrößen | 32, 32, 32, 32, 32, 11 |
| Geplante / tatsächliche Requests | 171 / 171; keine Retries |
| Input-Slices / verarbeitete Slices | 171 / 171 |
| Inputzeichen / verarbeitete Originalzeichen | 5.196 / 5.196 Codepoints |
| Input-Coverage | 100 % |
| Zitierte / unzitierte Slices | 171 / 0 |
| Slice-Citation-Coverage | 100 % (keine Aussage über Volltextzitate) |
| Globale Claims | 171 |
| Verarbeitung, einschließlich Source-Reader und Nachprüfungen | 12.538229 s |
| Erneuter Cacheabruf, einschließlich Source-Reader | 3.997497 s; 0 Requests |
| Separater Prozessrestart | 6.017230 s; 0 Requests |
| Tatsächliche Rawantworten | 31.360 Bytes |
| Gesamte gespeicherte Evidence | 2,160,211 Bytes |
| Gesamtstatus / Fachreview | completed / unreviewed |

Ein tatsächlich geprüfter synthetischer Claim aus diesem vollständigen Lauf:

```json
{
  "text": "A variable stores a value under a chosen name.",
  "ref_id": "91a65e384846487267ea72ab6e5f8e55dc0dde10d17f2dbb02699c62a4f5e2a9",
  "block_id": "material_block:8c203880ea5047311acb3d74665c524b629f9a9a3a65c0c5ba431fcf9fe42977",
  "offset_start": 0,
  "offset_end": 46,
  "original_locators": [
    {
      "bbox": null,
      "chapter_path": [],
      "coordinate_system": "unknown",
      "dom": "/html[1]/body[1]/main[1]/p[1]",
      "end": null,
      "line_end": null,
      "line_start": null,
      "origin_pointer": "/blocks/1",
      "original_segment_id": null,
      "page": null,
      "raw_artifact_sha256": "17ef05386417c250a44243f0c0ccae369e60b0e7c8fc6a5c276a5ce9a4cba3fe",
      "start": null,
      "time_status": "not_applicable"
    }
  ],
  "parsed_version_id": "content_version_v1:55cf439196684685eb8fe1c13e36fb0f82b33ffbca582d7ba377139887e95cea"
}
```

Messdatei: `/tmp/cs50-m2a-final-v2-tests/test_complete_171_reader_pagin0/benchmark.json`.
Die Laufzeiten sind lokale Einzelmessungen ohne Extrapolation auf reale Lectures;
der MVP-Setupimport und die separate Planung sind nicht in der Verarbeitungszeit.

Ein separater Test verwendet ein über 16.384 Zeichen langes Original mit mehreren
Slices und Batches. Eine weitere rein synthetische In-Memory-Projection enthält
Whitespace-Fenster sowie `reference_projection` und `blank_text`; diese werden
exakt erhalten beziehungsweise mit Gründen ausgeschlossen. Sie wird nie als
geprüfte Publikation oder reale Quelle ausgegeben.

## Abgedeckte Verträge

- Kleine Quelle innerhalb einer Batchgrenze und unveränderte M1-Obergrenze 32.
- 171 Blöcke, zwei Reader-Seiten, sechs deterministische geordnete Batches.
- Lange Blöcke, exakte Codepoint-Coverage einschließlich Whitespacefenstern,
  unveränderte SourceRefs, Original-Locators, Originalquelle und ParsedVersion.
- Fehler in der Mitte, strukturell ungültige Ausgabe, unsupported Claim und
  Unsicherheit: sofortiger Stop nach gesicherter Evidence, HOLD, kein Retry und
  kein Weiterlauf beim erneuten Aufruf.
- Fehlender, doppelter, umgeordneter oder veränderter Batch; fremder Claimref,
  geänderter Locator, falscher Enginekey und abweichender Reviewstatus.
- Vollständiger Cache-/Prozessrestart ohne neue Requests und bytegleiches Inventar;
  eigenständiger normaler Enginecache abrufbar; unvollständiger Root bleibt HOLD.
- Alte M1-Approval, falsche Schema-/Adapterversion, Actor, Code, Quelle/Version,
  Actions, Limits oder Plan; fehlende SummaryApproval; ungültige/abgelaufene
  ProcessingApproval; Rawblob-/ParsedVersion-Manipulation.
- Ablauf beider Approvaltypen zwischen Requests, globale Deadline, Gesamt-Slice-/
  Batch-/Request-/Raw-/Evidence-/Dateibudgets und harte Schemagrenzen.
- Widersprüche über Batchgrenzen: trotz erfolgreicher Einzelbatches globale HOLD.
- Input- und Slice-Citation-Coverage separat, insbesondere kurze wörtliche Claims
  bei vollständiger Eingabe: 100 % Slicezitation behauptet keine Volltextzitation.
- Unbekannte, leere, öffentliche, unvollständige oder manipulierte Zielroots bleiben
  erhalten. Keine Parser-/Download-/Index-/Publicationaufrufe während Summary.
- Bestehende M1-, MVP-, Store-, Reader-, FTS-, Projection- und Materialregressionen.

## Lieferumfang, Integrität und verbleibende HOLDs

Genau sechs beabsichtigte Repositorypfade:

- `src/c27_learning_summary/adapter.py`
- `src/c27_learning_summary/engine.py`
- `src/cs50_summary_batch.py`
- `tests/test_cs50_summary_batch.py`
- `docs/cs50/one-source-summary-m2a.md`
- `docs/cs50/one-source-summary-m2a-validation.md`

Produkt-/Testbytes nach der letzten Codeänderung:

| Datei | SHA-256 |
| --- | --- |
| `src/c27_learning_summary/adapter.py` | `0b320c8f88444072c3de2c0d2afb9ba9ec6e662ee99c98720615387624f27919` |
| `src/c27_learning_summary/engine.py` | `1118637b32d7535f28da0ebe2076d65da448fd1e37a9ed3f650a6b7e79174c8c` |
| `src/cs50_summary_batch.py` | `b5ed569ef315e1da270c853d946e0f0e5a8aef049dde27a2d988eb8d314bc373` |
| `tests/test_cs50_summary_batch.py` | `519253c21ee8b571afca3f7d7d906591d3e584efe5c89c0c02a6a96183fd54d2` |

Der unabhängige Source-Abgleich zählt 290 ursprüngliche und 291 exportierte
Pythondateien unter `src`: genau zwei Änderungen und ein neues Modul. Sämtliche
anderen src-Bytes und der MVP-Operator sind identisch; keine ausgelassenen
ignorierten Pythonhelpers im Zielworktree.

Aktueller pfadgebundener Implementierungsfingerprint: `9d50fbee57fe127ab164fb3f2aea44433711d636e2655954eef198af34288303`, Revision `ff5e13340b83a86c69bcc38e787fbcdf05513074`.

Lieferpaket: `/tmp/cs50-m2a-delivery/`, vollständiger `m2a.patch`, beide
Dokumente und vier Code-/Testdateien, `files.json`, Prüfsummen, Laufkommando, Log,
JUnit und Benchmark. Der Patch enthält keine privaten Runtime-/Approvaldateien.
`git apply --check --whitespace=error-all` wurde im tatsächlichen unveränderten
Zielworktree ausgeführt, ohne den Patch anzuwenden.


M2.2-Real Source Acceptance bleibt HOLD: historische Importfreigabe abgelaufen,
keine aktuelle BatchApproval für reale Source/ParsedVersion und neu berechneten
vollständigen Plan. Keine fachliche/didaktische Abnahme. Gesamtgrenzen können
auch mit korrekten Approvals HOLD auslösen; FakeLLM liefert mechanische Exzerpte.

SQLite-B1 und PR #171 werden nicht bearbeitet. Ein grüner synthetischer
Storelauf auf SQLite 3.50.4 ist kein Nachweis ihrer allgemeinen Behebung.

Anwendung im tatsächlichen Zielworktree und Defaultbranch-Integration bleiben
wegen Sitzungsschreibgrenze beziehungsweise ausdrücklichem Integrationsverbot
pending. Beide Dokumente werden im vollständigen Patch geliefert, liegen aber
noch nicht in master. Vorbestehende Branches und Worktrees müssen erhalten bleiben;
es wurden keine neuen registrierten Git-Artefakte erzeugt. Temporärer Export,
Environment, fehlerhafte Runs und finale Evidence werden zur Nachprüfung behalten.

Abschließende Originalkontrolle: beide Worktree-HEADs, sämtliche lokalen Refs,
beide echten Indexhashes und der jeweilige Status stimmen mit der Aufnahme
überein. Die M2-Berichte haben unveränderte SHA-256-Werte. Der tatsächliche
M2a-Zielworktree bleibt sauber. Maschinenlesender Nachweis:
`final-verification.json` im Lieferpaket. Produktbytes entsprechen weiterhin
exakt dem oben genannten Fingerprint; nach dem Schlusslauf nur Dokumentation
und Lieferpaket bearbeitet.

## Long-Source-Stress und Release-Review (Folgeauftrag 07.11.2026)

Dieser Abschnitt aktualisiert den Abnahmestand. Die vorstehenden Export-,
Anwendungs- und Statusaussagen beschreiben den früheren Implementierungsauftrag,
keinen erneut festgestellten Istzustand. Im tatsächlichen Zielworktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-m2a` liegt der Patch
uncommittiert auf `feat/cs50p-summary-batching-m2a`, HEAD
`ff5e13340b83a86c69bcc38e787fbcdf05513074`. Genau die sechs ursprünglichen
Lieferpfade sind geändert/neu. Beide M2.1-Dokumente und AGENTS.md wurden gelesen;
M1-Vertrag, dessen Validierungsbericht und die beteiligten Produktmodule wurden
zum Vergleich herangezogen. Kein Netzabruf oder Live-Abgleich von GitHub/PRs.

Auch diese Sitzung darf den Zielworktree nur lesen. Tests laufen deshalb unter
`/tmp/cs50-m21-release-review-xkxtruqf/work` mit bytegleichem `src` und MVP-Operator.
Die kopierte `.git`-Verweisdatei erlaubt lediglich echte HEAD-Ablesung. Es gibt
keinen neuen Gitbranch, Commit, registrierten Worktree oder separaten Gitindex.
Das Lieferpaket enthält ausschließlich eine Ergänzung dieses Berichts und
`tests/test_cs50_summary_batch_stress.py`; Anwendung im Zielworktree bleibt pending.
Kein Produktbyte und kein vorhandener Test wurde für dieses Review verändert.

### Vorhandene Evidence und Codebindung

Der angegebene Post-Apply-Lauf unter
`/home/robfra/codex-logs/c27cs50/m2a-postapply.CYJVhG/` ist tatsächlich vorhanden:
**489 passed, 1 deselected in 1366,90 s; Exitcode 0.** JUnit enthält 489 Testcases,
keine Failures, Errors oder Skips; die Verteilung entspricht der obigen Tabelle.
Der optionale Realmaterialfall wurde abgewählt. Das ist ein bereits ausgeführter
Regressionsnachweis, kein in dieser Reviewsitzung wiederholter 489-Test-Lauf.
Der ältere 664,53-s-Exportlauf und seine Hashes bleiben getrennte historische
Evidence. Keine Vermischung dieser Messungen oder Addition zu einer neuen Suite.

| Post-Apply-Artefakt | SHA-256 |
| --- | --- |
| `pytest.log` | `3a50342e813067a8b89ff8650ae337f61670ff19a1c4f66b61fb438e51db2955` |
| `results.xml` | `f87ed7991cee4eae5524f64f17515c2eca217532b50bcddce5b6d38f31a5d7a1` |
| `exit_code.txt` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

Alle vier oben dokumentierten Produkt-/Testdateihashes stimmen mit dem
gegenwärtigen Zielworktree überein. Der gesamte Implementierungsfingerprint
ist weiterhin `9d50fbee57fe127ab164fb3f2aea44433711d636e2655954eef198af34288303`;
Export und Ziel besitzen denselben Satz von 291 Pythondateien unter `src`
und denselben bestehenden MVP-Operator. Die neue Testdatei liegt außerhalb
dieses Produktfingerprints. Neue Freigaben nach einem späteren Commit müssen
zusätzlich dessen neue Revision binden.

### Architektur- und Sicherheitsreview

| Bereich | Ergebnis und konkrete Codebindung |
| --- | --- |
| BatchPlanner | Implementiert als `make_plan()` in `src/cs50_summary_batch.py:77`, keine eigene Plannerklasse. Vollständige geeignete Originalblöcke, geordnete feste Codepoint-Fenster, unabhängige lückenlose Rekonstruktion, Refhash- und Original-Locator-Abgleich. Obergrenzen brechen mit HOLD ab; kein gekürzter Plan wird freigegeben. |
| M1-Kompatibilität | `adapter.py:137/174`: neuer Iterator, bisheriger Wrapper behält Whitespacefilter und maximal 32 Slices. `engine.py:142/182`: `generate()` behält Auswahl, Signatur und Inputsnapshot und delegiert an denselben Section-/Store-Kern. `src/cs50_summary_mvp.py`, Modelle, FakeLLM, Store und Exportpolicy sind zur Basis unverändert. M1 behält Approvalschema 1, 64-KiB-Approvalinput, Einzelquellenbindung und bisherigen Cachekey. Positive und negative M1-/C27-Verträge sind durch die vorhandenen 42 + 47 Post-Apply-Fälle belegt. |
| Orchestrator | `cs50_summary_batch.py:255`: einmalige vollständige M1-Sourceprüfung je Aufruf unter gehaltenem MVP-Lock; kein Reader-Top-k, keine neue Source-ID, keine erneute Auswahl pro Batch. `before_call` prüft Deadline, beide Approvalabläufe und Requestzahl; `after_reply` zählt Rawbytes; `after_section` stoppt bei verworfenen Claims/Unsicherheit. Abschließend Quellinventar und aktuelle Code-/Freigabebindung erneut prüfen. |
| Approvals | `BatchApproval` erbt die M1-Pflichten und bindet Schema 2, Adapterversion, vollständigen Plan, Konfiguration und Limits. Aktuelle Freigabe prüft Actor, geordnete Aktionen, Code und Source-/Version-/Intent-/Approvalhashes. `m1.historical_approval()` prüft zusätzlich die ursprüngliche Importkette und deren Ablauf. Keine automatische Approvalerstellung durch `plan`; keine Verlängerung historischer Atteste. Tests erstellen nur neue ausdrücklich autorisierte synthetische Fixture-Atteste. |
| Cache/Restart | Ein vollständiges Manifest, unveränderte Intent-/Evidencebytes, alle Kandidaten plus getrennte `checked`-Zustände, globale Claims und `ready` sind erforderlich. Vollständige Eingabe einschließlich Freigaben/Intent ergibt gleiche Plan-, Batch-, Ref- und Engineidentitäten. Ein neuer Import mit anderen Attesten ist keine identische Eingabe. Cache-/Prozessabruf schreibt nichts und ruft FakeLLM nicht auf. |
| Fehler/HOLD | Erfolgreiche Batches, Rawantworten und bereits erzeugte Sections bleiben erhalten. Fehlerstop ohne Retry; kein automatisches Fortsetzen eines HOLD-/pending-Roots, kein Übernehmen unbekannter Dateien. Technische Runzustände ersetzen keine menschliche Freigabe. Ein Prozessabbruch kann pending hinterlassen. Für einen neuen Lauf ist eine neue ausdrückliche Entscheidung und ein isolierter Root erforderlich. |
| Konsolidierung | `consolidate_batches():186` und `m1.checked_result():346`: exakte Batchreihenfolge, Ref-/Section-/Config-/Engineidentität, Requesthashes und wörtliche Claims erneut prüfen. Bestehende Konsolidierung diagnostiziert Widersprüche über Batchgrenzen; globale Claims bleiben aus geprüften Sections erhalten. Keine fachliche Synthese oder automatisch approved Claims. |
| Daten-/Dateigrenzen | Isolierte absolute symlinkfreie Roots, Besitz-/Modusprüfung (0700/0600), vorhandene Lockgrenzen und Inventare aus Pfaden, Modi und Bytes bleiben erhalten. Keine Source-Store-, Parser-, Index- oder Downloadänderung durch den Summarypfad. Sicherheitsgarantien beziehen sich auf kooperierende lokale Prozesse und private Operatoratteste, nicht kryptografisch signierte Fremdeingaben. |

### Tatsächliche Grenzen und Prüfzeitpunkte

Keine Grenze wurde angehoben. Positive Lecture und alle Negativfälle benutzen
`BatchLimits()` unverändert. Die Lecture verwendet `chunk_chars=2000`,
`max_chunks=32`; der 50.013-Zeichen-Einzelblock verwendet dieselbe Slicegröße
und kleinere Batches mit `max_chunks=8`.

- Gesamt-Slices/Requests je höchstens 512 und Batches höchstens 32. Zusätzlich
  reserviert der Planner vor jedem Request 128.000 Rawbytes je Slice: Standard
  32.000.000 Bytes erlaubt höchstens 250 Requests. Selbst die harte 64.000.000-
  Grenze erlaubt nur 500, keine 501–512 Requests. Diese Reservierung ist bewusst
  unabhängig von kleinen erwarteten Fakeantworten.
- `max_input_bytes` begrenzt jeden tatsächlich serialisierten Request auf
  standardmäßig 24.000, höchstens 64.000 UTF-8-Bytes inklusive JSON/Schema/Metadaten.
  Es gibt **kein separates konfigurierbares kumulatives Inputbytefeld**. Die
  gesendete Gesamteingabe ist abgeleitet durch Anzahl × Requestbytegrenze
  begrenzt: bei Standardbudgets höchstens 6.000.000 Bytes, unter allen harten
  Schranken höchstens 32.000.000 Bytes (500 × 64.000). Originale HTML-/Storebytes,
  Text-Codepoints und mehrfach serialisierte Requests sind verschiedene Größen.
  Diese Ableitung begrenzt keine vorgelagerte RAM-Allokation des vollständigen
  Readers, Catalogs oder Materialimports.
- Die Gesamtdeadline beträgt höchstens 600 s und umfasst in `run` auch die
  Sourceprüfung nach Approvaleinlesen. Je Batch gelten standardmäßig 120 s,
  höchstens 180 s; jeder Request erhält höchstens 20 s standardmäßig, 30 s hart
  und jeweils die kleinere verbleibende Batch-/Gesamtlaufzeit. Das ist eine
  kooperative Prüfung; FakeLLM und lokaler Dateizugriff werden nicht präemptiv
  abgebrochen. Neue Stresstests beobachten Laufzeiten und gebundene Timeouts;
  die vorhandenen Ablauf-/Deadlinefälle bleiben der gezielte Zeitfehlernachweis.
- Approvalinput: 8 MiB; Source-Evidence und globale Summary jeweils höchstens
  16.000.000 Bytes. Gesamtdateien standardmäßig 128.000.000, hart 256.000.000 Bytes.
  `plan` prüft Slice-/Batch-/Request-/Requestbyte-/Rawreservierungsgrenzen.
  `run` prüft vor Rootanlage zusätzlich Source-Evidence und initiale gespeicherte
  Bytes, danach nach Batches die tatsächlichen Dateien und vor globaler
  Veröffentlichung eine Abschlussreservierung. `approval_required` allein ist
  deshalb keine vollständige Laufabnahme oder garantierte Zielgrößenzusage.
  Die Dateigrenze ist eine Abnahmeschranke, keine Festplattenquote; ein HOLD kann
  bereits übergroße erhaltene Evidence enthalten.
- Präzisierung zur älteren Oversizebeschreibung: Eine Rawantwort **über** 128.000
  Bytes wird von der unveränderten M1-Grenze vor dem Rawschreiben abgewiesen;
  erhalten bleibt Fehlerklassenevidence. Innerhalb der Einzelantwortgrenze
  gespeicherte Rawantworten bleiben auch bei anschließendem Timeout/Schemafehler
  erhalten. Nicht jede übergroße ursprüngliche Antwort wird vollständig archiviert.

### Neue Stressausführung

Ausschließlich neu verfasste synthetische HTMLbytes, reale lokale Parser-/Store-/
Reader-Fixture und FakeLLM. Die Fixtures enthalten ihre Herkunft im Attest;
URLstrings dienen allein als Identität. Keine echte CS50P-Quelle, kein Download,
kein Netzabruf, kein LiveLLM. Während positiver Summaryläufe sind Parser,
Downloader, Storeinitialisierung, Indexbuild und FTS-Suche explizit gesperrt.
Der Cache-Child installiert eigene Socket-/DNS- und FakeLLM-Sperren vor dem Import.
Die pytest-Netzsperre allein würde nicht in einen neuen Pythonprozess propagieren.

Die Lecture umfasst fünf bestehende eigene Fixtureblöcke plus 166 neue
synthetische Absätze mit 1200/1800/2800 Zeichen. Sie enthält bewusst Unicode und
55 zusätzliche Slices aus längeren Absätzen. Das ist ein Form-/Ressourcenstress,
keine inhaltliche Simulation einer fachlich geprüften Lecture. Ihre Textmenge
ist rund 61,7-mal so groß wie die früheren 5.196 Zeichen.

Für die isolierten Budgetfälle werden drei lange 50.013-Zeichen-Blöcke plus die
fünf Fixtureblöcke verwendet: 150.255 Zeichen. Zulässige `chunk_chars=512` ergibt
299 erforderliche Slices und überschreitet die unveränderte Rawreservierung;
`chunk_chars=256` ergibt 593 Slices und überschreitet die harte Slice-/Requestgrenze.
Dies sind ausdrücklich andere Slicegeometrien als die positive Lecture, keine
Behauptung, 150.255 Zeichen überschritten bereits bei 2000 Zeichen pro Slice die
Standardgrenzen. Kein Gesamtbudget und keine vorhandene Schranke wird erhöht.

| Messwert | A: Langblock plus Fixture | B: Lecture |
| --- | ---: | ---: |
| Originalblöcke / geeignete Blöcke | 6 / 6 | 171 / 171 |
| Slices / Batches | 31 / 4 | 226 / 8 |
| Batchgrößen | [8, 8, 8, 7] | [32, 32, 32, 32, 32, 32, 32, 2] |
| Input = tatsächlich gesendete Zeichen | 50.229 | 320.416 |
| Input = tatsächlich gesendete Textbytes | 51.744 | 329.912 |
| HTML-Rawbytes | 51.937 | 331.260 |
| Serialisierte Requestbytes gesamt | 150.530 | 1.050.046 |
| Größter Request in Bytes | 5.251 | 5.247 |
| Requests / Cache / Restart | 31 / 0 / 0 | 226 / 0 / 0 |
| Input- / Slice-Citation-Coverage | 100 % / 100 % | 100 % / 100 % |
| Run / Cache / Restart in Sekunden | 3,331 / 1,440 / 3,180 | 31,686 / 18,355 / 19,610 |
| Rawantwortbytes | 56.488 | 364.491 |
| Globale Summarybytes | 151.029 | 996.316 |
| Approvalbytes / Source-Evidencebytes | 98.445 / 151.595 | 639.841 / 1.075.209 |
| Gespeicherte Gesamtbytes | 1.116.615 | 7.344.251 |
| Kumulativer pytest-Prozess-RSS nach Fall, KiB | 79.632 | 94.848 |
| CLI-Exitcodes Run / Cache / Restart | 0 / 0 / 0 | 0 / 0 / 0 |
| Gesamtstatus / Fachreview | completed / unreviewed | completed / unreviewed |

| Negativfall | Originalblöcke / erforderliche Slices / Batches | Inputzeichen / Textbytes | Verarbeitung und Ergebnis |
| --- | --- | --- | --- |
| C1: Rawreservierung | 8 / 299 / 10 (nur Bedarf, kein freigegebener Plan) | 150.255 / 154.800 | 0 Requests, 0 Zeichen/Bytes verarbeitet, 0 Batches ausgeführt, 0 Summarybytes; HOLD, Exit 2 auch bei Wiederholung; 2,805 s erster Planaufruf |
| C2: harte Slice-/Requestgrenze | 8 / 593 / 19 (nur Bedarf, kein freigegebener Plan) | 150.255 / 154.800 | 0 Requests, 0 Zeichen/Bytes verarbeitet, 0 Batches ausgeführt, 0 Summarybytes; HOLD, Exit 2 auch bei Wiederholung; 2,316 s erster Planaufruf |
| C3: UTF-8-Request | 6 / 6 / 1 (nur Bedarf, kein freigegebener Plan) | 8.216 / 29.444 | 0 Requests, 0 Zeichen/Bytes verarbeitet, 0 Batches ausgeführt, 0 Summarybytes; HOLD, Exit 2 auch bei Wiederholung; 0,310 s erster Planaufruf |
| C4: Teilfehler | 6 / 31 / 4 geplant | 50.229 / 51.744 | 10 Requests, 10.216 Zeichen / 10.516 Bytes gesendet; 1 Batch geprüft; HOLD, Exit 2 auch bei Wiederholung; 2,200 s; 407.634 erhaltene Bytes |

C1 reserviert 38.272.000 > 32.000.000 Rawbytes. C2 benötigt 593 > 512 Slices. C3 serialisiert maximal 32.411 > 24.000 Requestbytes trotz nur 8000 Zeichen pro Slice. Ihre CLI-HOLD-Gründe stehen unverändert in `metrics.json`: `planned worst-case raw output exceeds total budget`, `total slice/request limit exceeded; no truncation`, `serialized request byte limit exceeded`. Die nicht ausführbaren Quellen erhalten keine globale Coverage; für die nicht gesendete Eingabe beträgt die gemessene Verarbeitung 0 %. Teilfehler: 10/31 Slices gesendet, 9/31 akzeptiert zitiert, keine vollständige globale Coverage und kein ready.


Coverage der erfolgreichen Läufe wird unabhängig pro Originalblock geprüft:
fortlaufende Offsets ab 0, Endoffset gleich Originallänge, unveränderte Locators
und Rawhashes, einzigartige Ref-IDs sowie exakte Konkatenation sowohl der
Codepoints als auch der UTF-8-Bytes. Die abgefangenen tatsächlichen FakeLLM-
Requests stimmen in Reihenfolge und Text mit allen geplanten Refs überein.
Bei Erfolg sind Input- und Slice-Citation-Coverage 100 %. Das ist keine Aussage
über didaktische Vollständigkeit, semantische Qualität oder vollständige Zitate
jedes Zeichens. Die frühere separate Whitespace-/Ausschlussprüfung bleibt relevant;
der HTMLparser normalisiert HTML-Whitespace bereits vor dem gespeicherten Text.

Im Teilfehlertest wird im zweiten Batch genau der zehnte Claim verfälscht.
Es verbleiben zehn Raw- und zehn Sectiondateien, davon neun akzeptiert zitierte
Slices. Batch 0 bleibt checked, Batch 1 HOLD, Batch 2 beginnt nicht. Gesamtergebnis
HOLD, kein globales Summary und kein Manifest; Wiederholung behält die Bytes und
verursacht null weitere Requests. CLI-Grund `SummaryRunError`, gespeicherter
konkreter Ablehnungsgrund `unsupported_claim_not_verbatim`. Lokale Sections sind
keine globale Input-Coverage oder vollständige technische Abnahme.

### Aufgedeckte vorgelagerte Grenzen und erhaltene Fehlversuche

1. Erster Stresslauf: 3 passed, 2 failed in 174,45 s, Exit 1. Positiver Langblock,
   positive Lecture und UTF-8-HOLD bestanden. Zwei andere Oversize-Fixtures mit
   171 Blöcken (166 × 2400 beziehungsweise 7000 Zeichen plus Fixture) erreichten
   den BatchPlanner nicht: der MVP-Import/anschließende Retrievallauf meldete
   `Unavailable`. Roots bleiben ready beziehungsweise index_pending. Eine spätere
   **rein lesende Diagnose**, keine Fortsetzung/Reparatur, lieferte für eine
   Query im ersten Root einen Treffer; Export 1,291 s, FTS 0,139 s. Zusammen mit
   der vorhandenen 2-s-Querydeadline ist Zeitabhängigkeit plausibel, die genaue
   ursprüngliche Fehlerstelle ist damit nicht nachgewiesen. Keine Erhöhung oder
   Abschaltung von Retrievallimits, kein grüner Budgetnachweis aus diesen Fehlern.
2. Zweite Form: einzelne Blöcke mit 500.001 und 1.024.001 Zeichen wurden schon
   im MVP-Vorbereitungspfad mit `InvalidInput` zurückgewiesen; beide Roots bleiben
   preparing. Der bestehende `MaterialUnit` serialisiert für jedes 2000-Zeichen-
   Fenster auch den **vollständigen** Originalblock (`mapping.py:31/86`); Adapter
   und Handoff halten diese Units zusätzlich im JSON. Aus den gespeicherten
   synthetischen NormalizedDocuments berechnet sich allein für wiederholte
   Blocktexte eine Untergrenze von 129.303.368 beziehungsweise 541.230.093 Bytes.
   Beide liegen über `canonical()`s 67.108.864-Byte-Grenze. Das erklärt eine
   nachweisbare vorgelagerte Größenbarriere, ohne eine genaue Stacktracezuordnung
   des redigierten `InvalidInput` vorzutäuschen. Keine Anwendung oder Korrektur
   im Summarymodul würde diese bereits abgewiesenen Importe freigeben.
3. Zweiter gezielter Lauf: 2 passed, 2 failed, 2 deselected in 48,19 s, Exit 1;
   UTF-8-HOLD und Teilfehler bestanden, beide oben genannten Importversuche
   scheiterten vor M2.1. Sein pytest-Prozess erreichte kumulativ 1.655.040 KiB RSS.
   Das ist ein gemessener Prozesshöchstwert einschließlich Importversuchen,
   kein isolierter M2.1-Summarywert und keine aufsummierte Prozessspeichernutzung.
   Sehr große Einzelblöcke sind damit auch ein Ressourcenrisiko **vor** den
   M2.1-Limits. Für solche Quellen wird kein Releaseversprechen abgeleitet.
4. Erst nach dieser Eingrenzung wurden die beschriebenen Budgetfälle mit drei
   50.013-Zeichen-Blöcken und kleinerer erlaubter Slicegeometrie verwendet:
   2 passed, 4 deselected in 42,07 s, Exit 0. Die vorherigen Quellen wurden weder
   überschrieben noch neu fortgesetzt; sämtliche Logs/Roots bleiben erhalten.
   Der abschließende gemeinsame Lauf der sechs neuen Fälle ist separat unten
   ausgewiesen. Die Fehler werden durch ihn nicht rückwirkend grün.

Ein anfänglicher Messlauncher konnte `/usr/bin/time` nicht finden (Exit 127 vor
pytest). Deshalb misst ein neuer stdlib-Launcher Laufzeit und Linux-RSS mittels
`resource.getrusage`, ohne Installation oder Änderung der Umgebung.

### Evidence, Restrisiken und Release-Entscheidung

Abschließender gemeinsamer Lauf: **6 passed in 184,72 s; Exitcode 0**, keine
Deselections, Skips, Xfails, Failures oder Errors. JUnit enthält genau sechs
bestandene Testcases. Python 3.12.12, SQLite 3.50.4, Pydantic 2.13.4, pytest 9.1.1,
BeautifulSoup 4.15.0; vorhandene Ziel-venv lesend verwendet, keine Installation.
Ruff check und format --check für die drei Produktmodule und beide Batchtestdateien
bestanden; Patchanwendbarkeit und Whitespace werden gesondert geprüft.

Reproduzierbarer Schlussbefehl (außerhalb des schreibgeschützten Zielworktrees):

```bash
cd /tmp/cs50-m21-release-review-xkxtruqf/work
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-m2a/.venv/bin/python \
  -m pytest tests/test_cs50_summary_batch_stress.py -q \
  -p no:cacheprovider -p tests.offline_guard \
  --basetemp=/tmp/cs50-m21-release-review-xkxtruqf/final-tests \
  --junitxml=/tmp/cs50-m21-release-review-xkxtruqf/final-results.xml
```

Für eine erneute Ausführung einen **neuen** basetemp-Pfad und neue Log-/JUnitnamen
wählen, damit pytest die jetzt erhaltene Evidence nicht vorab entfernt.
`run_final.py` zeichnet zusätzlich Wallzeit und Linux-`RUSAGE_CHILDREN.ru_maxrss`
auf: 185,799 s Prozesswallzeit, **127.140 KiB
(124.16 MiB) maximaler RSS** des abgeschlossenen
pytest-Prozessbaums. Linux meldet den größten einzelnen Prozess, keine Summe
aller gleichzeitigen Prozesse. Pro-Fall-RSS in den Tabellen ist ein kumulativer
Prozesshöchstwert einschließlich Fixtureaufbau und früherer Fälle; er ist keine
isolierte Peak-Memory-Zusage je Summarizer. Run-/Cache-/Restartzeiten schließen
Reader und Nachprüfung ein, aber nicht Setupimport und separate Vorabplanung.

Evidence unter `/tmp/cs50-m21-release-review-xkxtruqf/`: `final.log`,
`final-results.xml`, `final-exit-code.txt`, `final-process-metrics.json`,
`metrics.json`, sechs `final-tests/*/stress-metrics.json`, `environment.json`,
`initial.json`, `final-verification.json` und die unveränderten Fehlversuchlogs.
`setup-diagnostic.json` und `long-block-import-size-analysis.json` begrenzen die
oben ausdrücklich als solche bezeichneten Diagnoseaussagen. Die vorhandenen
489 Tests wurden wegen unveränderter Produktbytes nicht erneut ausgeführt.

| Neuer Nachweis | SHA-256 |
| --- | --- |
| `final.log` | `4701271e2e0c36f56d1f52c73272b755056b04922dd8e561927cf7dd43601aee` |
| `final-results.xml` | `775ca00aeb4e91e3859e0dc4d36b6bb6a1ce5ea8729c5c05ae23fcafdb801052` |
| `metrics.json` | `9482db8bbafbe701b00d96e897ab9a5260e12415edfa7c4fa26d33c94ce3e5cd` |
| `tests/test_cs50_summary_batch_stress.py` | `c9c21feaf3575ee9ad047838fa2fa6db27df795b0ce48486574faf1188ee026c` |


**Release-Review: PASS für den begrenzten technischen Offline-/FakeLLM-Umfang
von M2.1.** Kein Implementierungsfehler im geänderten M2.1-Code festgestellt;
Produktcode unverändert. Vollständige Verarbeitung innerhalb der angenommenen
Grenzen oder kontrollierter HOLD, deterministische Identitäten und unveränderte
Stores sind synthetisch belegt. Die größeren Import-/Retrievalgrenzen sind
konkrete Restrisiken; PASS gilt weder für beliebig lange Originalblöcke noch als
harter RAM-/Laufzeitnachweis für jede schemaformal zulässige Quelle. Fachliche
und didaktische Abnahme bleiben NOT_EVALUATED. Reale Quellen, M2.2 und Liveprovider
bleiben HOLD und benötigen eigene Freigaben und Abnahmen.

Konkrete Empfehlung für die nächste separat autorisierte Veröffentlichung:

- Berichtsergänzung und gezielte synthetische Testdatei zunächst im tatsächlichen
  Zielworktree anwenden und dort die sechs neuen Fälle erneut prüfen. Erwartete
  gesamte Liefermenge dann sieben Repositorydateien: die sechs bisherigen Pfade
  und `tests/test_cs50_summary_batch_stress.py`. Keine Runtime-Rawdaten, privaten
  Approvals, virtuellen Umgebungen oder temporären Logs stagen.
- Danach Commit-Titel `feat(cs50): add bounded offline lecture summary batching (M2.1)`;
  Draft-PR-Titel `feat(cs50): bounded M2.1 lecture batching with synthetic stress evidence`.
  PR beschreibt vollständige Original-Coverage, global begrenzten Orchestrator,
  historischen Post-Apply-Regressionslauf und die getrennten sechs neuen Tests.
  Konkrete Import-/Retrieval-/RAM-Grenzen, FakeLLM und fehlende Fachabnahme benennen.
  CI-/Stage-0-Koexistenz und SQLite-B1 aus PR #171 dadurch nicht als erledigt ausgeben.
- Kein Commit, Push, PR, Merge oder master-Eingriff in diesem Auftrag. Die explizite
  Vorgabe geht der allgemeinen Integrationsregel aus AGENTS.md vor. Revision und
  neue Approvals nach einem späteren Commit erneut binden. Defaultbranch-Integration,
  PR-/Lifecycle-Abschluss und Anwendung dieses Ergänzungspatches bleiben pending.

Zielbranch, Zielworktree, master, gemeinsame lokale Refs, echter Index und alle
ursprünglichen sechs Dateien werden abschließend byte-/statusgleich kontrolliert.
Vorbestehende Git-Artefakte und alle synthetischen Fehlerroots bleiben erhalten;
kein Cleanup. Das neue Export-/Evidenceverzeichnis ist ein gewöhnliches
`/tmp`-Verzeichnis, kein Gitworktree. Es bleibt wegen ausstehender Patchanwendung
und Nachprüfbarkeit erhalten; `/tmp` ersetzt kein dauerhaftes Projektarchiv.


## Gezielte Fehlerdiagnose und Fixture-Stabilisierung (07.11.2026)

### Auftrag, Arbeitsstand und Abgrenzung

Ziel bleibt `Personal_Assistant-cs50-m2a`, Branch
`feat/cs50p-summary-batching-m2a`, HEAD
`ff5e13340b83a86c69bcc38e787fbcdf05513074`. Der Zielworktree war bereits dirty:
Änderungen an Adapter/Engine sowie die ungetrackten Batchmodule, Tests und beiden
M2.1-Dokumente gehören zum bestehenden Auftrag. AGENTS.md wurde gelesen. Diese
Sitzung darf im Zielworktree nicht schreiben. Bearbeitung und alle neuen
Ausführungen erfolgen ausschließlich in einer Kopie unter
`/tmp/cs50-m21-diagnosis-hll5s36d/work`; die kopierte `.git`-Verweisdatei ermöglicht
nur die bestehende Revisionsablesung. Keine neuen Git-Artefakte, Commits, Pushes,
PRs oder Merges. Die ausdrückliche Veröffentlichungssperre dieses Auftrags geht
der allgemeinen Integrationsregel vor; Defaultbranch-Integration bleibt pending.

Der fehlgeschlagene synthetische Root unter
`~/codex-logs/c27cs50/m2a-stress-review.LLQwLk/tests/test_realistic_oversize_plan_h0/new-private-mvp`
wurde ausschließlich über Datei-Lesezugriffe und SQLite
`mode=ro&immutable=1` untersucht. Dort kein `run`, `search`, `report`, Recovery,
Quarantäneschritt, neuer Approval oder neuer Schreibzugriff. Sein Datei-/Modus-/
SHA-256-Inventar wird vor und nach der Diagnose verglichen. Neue Tests verwenden
jeweils eigene bisher nicht vorhandene basetemp-Pfade. Keine Netzabrufe, echten
CS50P-Quellen oder LiveLLM-Aufrufe; vorhandene Ziel-venv nur als Interpreter und
Toolquelle verwendet. Keine Installation. Historische Approvals bleiben bytegleich.

### Historische Nachweise bleiben getrennt

Der gemeldete vollständige lokale Regressionslauf **489 passed, 1 deselected**
bleibt der frühere Post-Apply-Nachweis. Er wird hier nicht als erneut ausgeführt
bezeichnet. Der danach im Zielworktree fehlgeschlagene gemeinsame Stresslauf ist
in `m2a-stress-review.LLQwLk/pytest.log` und `results.xml` erhalten:
**5 passed, 1 failed in 201,87 s, Exit 1**. Der Fehler liegt im Parameter
`raw_reservation` bei `test_realistic_oversize_plan_holds_before_dispatch`,
ursprüngliche Zeile 278: `mvp.main(case.argv)` ergibt 2 statt 0, mit
`status=HOLD`, `code=unavailable`, `reason=Unavailable`.

Das frühere **6 passed / PASS** aus dem vorangehenden `/tmp`-Review oben bleibt
als eigenständige frühere Beobachtung erhalten. Es belegt weder den späteren
fehlgeschlagenen Ziellauf noch dessen Ursache. Der neue Abschnitt ersetzt keine
historischen Messwerte stillschweigend. Auch die nun korrigierten drei
Planner-Vertragstests werden nicht rückwirkend als erfolgreiche MVP-Importe
oder Retrieval-Abnahmen ausgegeben.

### Ablauf nach ready und Exceptiongrenzen

Die folgenden Zeilennummern beziehen sich auf die unveränderten Produktdateien
des Zielworktrees:

1. `scripts/cs50_learning_mvp.py:532–543`: Nach aktivem Index erfolgt bereits eine
   erste Suche nach `variable`. Erst danach wird `phase=ready` geschrieben.
   Im betroffenen Root sind `parsed_version_id`, `generation_id`,
   `index_generation`, `build_id` und `record_count=83` vorhanden. Das grenzt den
   Fehler auf den nachfolgenden Abschlussweg ein; ready beweist keinen Report-PASS.
2. `:544–546`: Eingabebytes erneut prüfen, dann `report()` aufrufen. Ein einfacher
   Eingabekonflikt würde `Hold` ergeben, nicht die beobachtete Klasse `Unavailable`.
3. `report():405–408`: Gespeicherte Approval-/Codebindung prüfen, dann `retrieve()`
   für drei Goldqueries (`variable`, `input`, `loop`) plus CLI-Query `input`.
4. `retrieve():310–319`: `verify_persisted()` liest und prüft Storeversion,
   Rawbytes, NormalizedDocument und Bundleevidence; anschließend Index und Reader
   öffnen. `:321–327` führt je Query die Suche aus und gibt den Suchsnapshot frei.
5. `:333–365`: Jeden Treffer unabhängig über Reader-TextWindow und Struktur
   auflösen; Source-/Versionsbindung, Originaltext, Texthash und Rawlocators prüfen.
   Ein eigentlicher Provenienzkonflikt würde `Hold` ergeben. Erst danach werden
   Goldpassagen bewertet. `:548` inventarisiert zuletzt die Ergebnisdateien.

`Unavailable` ist in `src/content_store/errors.py:40` als `ContentStoreError` mit
Code `unavailable` definiert. Die tatsächliche zusätzliche Diagnose ist ein
fester Operationsname in `str(error)`. Der vorhandene MVP-Handler
`:664–667` verwirft diesen für Nicht-`Hold`-Exceptions zugunsten des Klassennamens.
**Deshalb lässt sich die ursprüngliche konkrete Raise-Zeile aus dem gespeicherten
CLI-Log und ready-State nicht rekonstruieren.** Keine historische Traceback- oder
Operationsdiagnose wurde im untersuchten Log/Root gefunden. Die tatsächlich
beobachtete Exceptionklasse ist bewiesen, ihr historischer konkreter Auslöser
bleibt **nicht nachgewiesen**; eine Behauptung einer exakten Deadlinezeile wäre
nicht durch Evidence gedeckt. Aufgabe A bleibt in diesem Punkt offen.

Relevante mögliche Quellen nach ready sind insbesondere:

| Stelle | Verarbeitung und möglicher Auslöser |
| --- | --- |
| `content_index.py:742–761` | 2-s-Deadline für Suchsnapshot einschließlich Reexport; beim Contextabschluss zusätzlich `search response deadline` nach Deadline + 3 s. |
| `content_fts.py:155–170` | SQLite-Progresshandler beendet Arbeit nach derselben Deadline; FTS-Integritätsprüfung oder Query kann als `FTS query/database unavailable` enden. Diese Meldung allein unterscheidet noch keinen Timeout von jedem anderen SQLitefehler. |
| `content_index.py:848/851/866/968` | Snapshotbytes, Datei-/Hashabgleich, `query deadline`, `query hydration deadline`. |
| `content_store/store.py:210–250` | Lesende Transaktion; SQLite-/Dateisystemfehler können auf `Unavailable` abgebildet werden. Sperrkonflikte mit BUSY/LOCKED wären dagegen `Busy`. |
| `content_index_files.py:41–60`, `content_store/artifacts.py:73` | Indexdateigröße/-lesbarkeit oder Rootöffnung. |

Die 2-s-Deadline umfasst **nicht nur FTS MATCH**: vor dem Backend werden die
Originalprojektionen neu exportiert und Recordsets gehasht, im Backend wird die
vollständige FTS-Konsistenz geprüft, danach folgen Trefferhydration und
Serialisierung. Große Originaltexte können hier Ressourcenzeit kosten, auch wenn
die zurückgegebene Passage klein ist. Im historischen Lauf wurde diese Zeit
nicht separat gemessen; aus seiner Gesamtlaufzeit folgt keine einzelne Deadline.

### Große Texte, Readerfenster und Locators

Lesende Befunde aus genau dem fehlgeschlagenen Root:

- Acht gespeicherte Originalblöcke: Längen 20, 46, 55, 61, 34 sowie dreimal
  50.013 Zeichen; lange Blöcke jeweils 51.528 UTF-8-Bytes. Original-Input insgesamt
  150.255 Zeichen / 154.800 Textbytes. Der Index hat 83 Records.
- Die gespeicherten Locatorlisten umfassen nur ungefähr 372–374 JSONbytes je Block.
  Es gibt keinen Beleg für einen Locator-/Pagegrößenüberlauf.
- `content_index.py:905–931` begrenzt das Trefferexcerpt auf höchstens 512 Zeichen;
  es wird **kein vollständiger 50.013-Zeichen-Treffer** als Readerlimit übergeben.
  `reader.py:451–468` akzeptiert Fenster bis 16.384 Zeichen. Ein ungültiges Fenster
  würde `ReadFault(invalid_parameter)` statt `Unavailable` liefern. Die bestehenden
  M1-Sourceprüfungen lesen lange Originaltexte separat vollständig in Fenstern.
- SQLite `quick_check=ok`, keine Foreign-Key-Verletzungen, zwölf Artefakte
  `available`. Raw-, Plan- und Approvalbytes passen zu ihren Intenthashes.
  HEAD **und tatsächlicher Python-Implementierungshash** stimmen mit dem
  historischen Intent überein. Keine Recovery nötig oder durchgeführt.
- Auch die 868.352-Byte-FTS-Partition besteht SQLite- und FTS-Integritätsprüfung
  in einer ausschließlich anonymen RAM-Kopie der gelesenen Datei. Kein
  FTS-Schreibzugriff auf den alten Root. Die gespeicherte Suche liefert vier
  `variable`-, zwei `input`- und einen `loop`-Treffer. Darunter sind tatsächlich
  lange Blöcke mit Indexintervall 28.000–30.000; deren Reportexcerpt wäre
  28.000–28.512. Der hohe Startoffset ist zulässig und wird nicht als Fensterlänge
  missverstanden. Alle Treffergrenzen liegen innerhalb der Originaltexte.

Zwei Reproduktionen des **unveränderten ursprünglichen** `raw_reservation`-Tests
in jeweils neuen Roots bestanden. Die erste beobachtete `Unavailable`-Exceptions
mit `sys.settrace`; die zweite zeichnete deren Konstruktion/Stack und Suchzeiten
mit einem rein temporären Beobachter auf. Keine solche Exception trat auf. In
der zweiten Ausführung lagen fünf Suchen (Initialsuche plus vier Reportsuchen)
bei 0,279–0,313 s. Die Beobachter verändern weder Uhrwerte noch Deadlines, Limits,
Responses oder Approvalentscheidungen; ihre Laufzeit ist zusätzliche Messlast.
Sie werden nicht als Produktänderung oder dauerhafte Testhilfe ausgeliefert.

**Einordnung:** Der Aufbau koppelte einen Planner-Budgetnachweis unnötig an einen
vollständigen MVP-Import und dessen zeitbegrenzte Retrieval-Abnahme. Das ist ein
nachgewiesenes Testarchitekturproblem. Ein deterministischer Reader-/Locatorfehler
ist nicht reproduziert. Ein Ressourcen-/Deadlineereignis ist plausibel, aber
weder dessen konkrete Stelle noch ein echter Produktdefekt sind bewiesen.
Daher kein spekulativer Produktpatch, kein neuer Exceptionhandler, Retry, Sleep,
geändertes Timeout oder erhöhtes Sicherheitslimit. Ein notwendiger minimaler
Produktpatch kann erst aus einer tatsächlich aufgezeichneten Fehlerquelle
abgeleitet werden. Die verlorene historische Diagnose lässt sich damit nicht
nachträglich ersetzen.

### Korrigierte Testarchitektur

`test_realistic_oversize_plan_holds_before_dispatch` heißt jetzt
`test_synthetic_planner_oversize_holds_before_dispatch`. Alle drei Parameterfälle
bleiben erhalten; insgesamt bleiben es **sechs Stresstestfälle**.

Nur die drei Oversize-Negativfälle erhalten typed synthetische Plannereingaben:
eigene unveränderte HTMLbytes durch den produktiven HTML-v2-Parser, echte
SourceRef-/Parserblockidentitäten, originale DOM-/Rawlocators und vollständige
Blocktexte. Die `ContentBlock`-Projektion wird im Test ausdrücklich aus diesen
Originalen aufgebaut; Source-/Versionsidentitäten sind deterministische
Fixtureidentitäten, **keine Behauptung einer Storepublikation**. Payload- und
Projektionshashes binden die tatsächlichen typed Inhalte. `make_case` erzeugt
lediglich neue eigene Inputdateien und sein übliches synthetisches Attest; es
wird kein Attest als Importfreigabe ausgeführt und keine ready-State simuliert.

Der produktive `catalog_for()` und `iter_source_slices()` erzeugen die vollständigen
Refs. Die gemeinsame unabhängige Coverageprüfung `assert_original_slices()`
prüft für jeden Originalblock fortlaufende Offsets ab null, vollständiges Ende,
unveränderte Locators/Source-/Rawhashes, echte Refhashes, Eindeutigkeit und exakte
Konkatenation in Codepoints **und** UTF-8-Bytes. Diese Prüfung bleibt auch in den
positiven End-to-End-Fällen aktiv. Die benötigten Slicezahlen bleiben 299, 593
und 6; Textmengen und `SummaryConfig`-Parameter bleiben unverändert.

Anschließend ruft der Test zweimal **direkt das unveränderte produktive
`batch.make_plan(identity, blocks, doc, config, BatchLimits())`** auf und verlangt
den exakten `Hold`-Grund. Keine Planner-/Slicing-/Budgetmock und kein fingierter
bestandener Check. Damit werden dieselben vollständigen Quelldaten mit derselben
Konfiguration und allen unveränderten Standardgrenzen geprüft. Es entsteht kein
freigegebener Plan: beim harten Slice-Limit bricht der produktive Planner bereits
an der ersten Überschreitung ab, während die unabhängige Fixtureprüfung alle
593 benötigten Refs nachweist.

FakeLLM-Aufrufe werden gezählt und verboten. MVP-Report/-Run, Source-Reader,
Storeinitialisierung, Indexbuild/-Search sind zusätzlich gesperrt. Inputinventar
bleibt byte-/modusgleich; kein MVP-Root, Batchroot, Batchapproval oder Summary
entsteht. Der Planner-Vertrag liefert Exceptions, **keine CLI-Exitcodes**; neue
Metriken benennen `planner_outcomes=[HOLD,HOLD]`, `cli_exit_codes=null`, Grenze,
Sourceidentität, Konfigurationshash und Limits ausdrücklich. Die früheren
CLI-Exitcodes 2/2 oben bleiben nur historische Messwerte.

Die zwei positiven Langquellenfälle (31 beziehungsweise 226 Slices), Cache,
separater Prozessrestart und der Teilfehlerfall behalten den vollständigen echten
synthetischen MVP-/Store-/Reader-/Summarypfad. Hinzu kommen die unveränderten
51 Batchtests als eigene Regression. Diese Nachweise werden separat von den drei
Planner-Vertragstests bewertet. Ein nicht bestandener Report bleibt Exit 2/HOLD
und zählt niemals als MVP-Real-Source-Abnahme. Reale Quellen bleiben ungeprüft.

### Neue Validierung und Evidence

Alle Befehle laufen in der neuen `/tmp`-Kopie mit
`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, dem vorhandenen
`Personal_Assistant-cs50-m2a/.venv/bin/python -B`,
`-p no:cacheprovider -p tests.offline_guard`. Die temporären Diagnoseplugins sind
nur dort zusätzlich genannt, wo sie tatsächlich aktiv waren. Separate Log-,
JUnit-, Exitcode- und Rootpfade liegen unter `/tmp/cs50-m21-diagnosis-hll5s36d/`.

| Neue Ausführung | Evidencepräfix | Ergebnis | pytest-Exit |
| --- | --- | --- | --- |
| Ursprünglicher raw_reservation, Tracebeobachter | `diagnostic.log/xml/exit` | 1 passed, 5 deselected; 22.700 s (JUnit) | 0 |
| Ursprünglicher raw_reservation, Konstruktor-/Suchbeobachter | `observer.log/xml/exit` | 1 passed, 5 deselected; 11.839 s (JUnit) | 0 |
| Korrigierter raw_reservation, ohne Diagnoseplugin | `targeted-v2.log/xml/exit` | 1 passed, 5 deselected; 2.771 s (JUnit) | 0 |
| Korrigierte sechs Stresstests, Such-/Exceptionbeobachter | `stress.log/xml/exit` | 6 passed; 96.445 s (JUnit) | 0 |
| Unveränderte bisherige Batchtests, ohne Diagnoseplugin | `batch.log/xml/exit` | 51 passed; 209.370 s (JUnit) | 0 |
| Ursprüngliche sechs Tests in ursprünglicher Reihenfolge, Diagnosekopie | `original-order.log/xml/exit` | 6 passed; 120.231 s (JUnit) | 0 |

Ruff check: **Exit 0**, fünf Dateien; `ruff-check.log/exit`. Ruff format --check:
**Exit 0**, fünf Dateien bereits formatiert; `ruff-format.log/exit`. Keine Produktcodeänderung
in diesem Auftrag, deshalb keine zusätzliche Wiederholung der 438 früheren
M1-/MVP-/Store-/Readerfälle. Deren historische Nachweise oben bleiben unverändert.
Kein Skip, Xfail, Failure oder Error in den neuen erfolgreichen gemeinsamen Läufen.


Der erste neue Fixturevorlauf (`targeted.log/xml/exit`) scheiterte mit **1 failed,
5 deselected, Exit 1 in 1,72 s**: Das Inventarisieren des Testinputverzeichnisses
mit dem privaten MVP-Inventar verlangte 0600 statt der von `make_case` für Raw/Plan
angelegten 0644. Korrigiert wurden ausschließlich die Modi dieser neu erzeugten
Fixtureinputs vor dem Inventarsnapshot. Keine Reader-/Budget-/Produktänderung.
Dieser Fehlversuch und sein Root bleiben erhalten, werden nicht überschrieben.

Auch der zusätzliche unveränderte Originalablauf besteht mit sechs Fällen in
ursprünglicher Reihenfolge. Die beiden großen Positivfälle liegen dort wieder
vor `raw_reservation`; auch dieser Fall erreicht diesmal seinen eigentlichen
Planner-HOLD. Ausgeführt wurde die bytegleiche Kopie
`tests/diagnostic_original_stress.py` (Original-SHA-256
`c9c21feaf3575ee9ad047838fa2fa6db27df795b0ce48486574faf1188ee026c`).
Diese Diagnosekopie ist kein ausgelieferter neuer Test und ändert die Anzahl
sechs in der korrigierten Suite nicht. In allen beobachteten neuen Läufen
trat keine `Unavailable`-Exception auf. Das ist eine zusätzliche Nichtreproduktion,
kein Beweis für eine bestimmte historische Fehlerstelle oder eine Fehlerbehebung
im unveränderten Produktcode.

Reproduktionsmuster, für jede Ausführung einen neuen Root-/Lognamen wählen:

```bash
cd /tmp/cs50-m21-diagnosis-hll5s36d/work
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-m2a/.venv/bin/python -B \
  -m pytest tests/test_cs50_summary_batch_stress.py -q \
  -p no:cacheprovider -p tests.offline_guard \
  --basetemp=/tmp/NEUER-ISOLIERTER-ROOT \
  --junitxml=/tmp/NEUER-RESULTATNAME.xml
```

Für den gezielten Fall zusätzlich `-k raw_reservation`; für die 51 Batchtests
statt der Stressdatei `tests/test_cs50_summary_batch.py` verwenden. Der tatsächliche
gemeinsame Stresslauf hatte zusätzlich `-p tests.diagnostic_observer`, damit bei
einem erneuten `Unavailable` dessen unveränderte Exceptionkonstruktion samt Stack
aufgezeichnet worden wäre. Kein Deadline-/Antwort-/Limitmock.

Der isolierte Patch `../m21-stabilization.patch` umfasst ausschließlich
`tests/test_cs50_summary_batch_stress.py` und diesen Bericht.
`git -C <Zielworktree> apply --check <Patch>` und dieselbe Prüfung mit
`--whitespace=error-all` bestehen jeweils mit **Exit 0**, ohne Anwendung.
Die abschließende Prüfevidence liegt in `final-verification.json`,
`apply-check.log/exit` und `patch-whitespace.log/exit`.

Die fünf anfangs gesicherten Zieldateihashes und alle 499 gesicherten
Pythondateien im Zielworktree sind unverändert. Auch alle Produkt-Pythonbytes
der `/tmp`-Kopie stimmen mit dem Ziel überein. Der alte fehlgeschlagene Root ist
im vollständigen Dateipfad-/Modus-/SHA-256-Vergleich unverändert
(`old-root-inventory-before.json`, `old-root-inventory-after.json`).
Zielbranch, HEAD und Gitstatus entsprechen dem anfänglichen Stand. Keine
historischen oder aktuellen fremden Artefakte entfernt. Neue temporäre Gitbranches
oder Gitworktrees wurden nicht angelegt. Die gewöhnliche `/tmp`-Kopie, Diagnose-
plugins, Logs und alle neuen synthetischen Testroots bleiben zur Patchanwendung
und Nachprüfung erhalten; sie sind kein dauerhaftes Repositoryarchiv.

Weitere Evidence: `environment.json`, `old-root-analysis.json`,
`old-root-integrity.json`, `old-index-integrity.json`,
`old-index-hit-windows.json`, `observer.jsonl`, `target-before.json`,
`target-python-inventory-before.json` und alle neuen pro-Fall-Stressmetriken.
SHA-256 der ausgelieferten korrigierten Stressdatei:
`f514d1f5be69f68dba33a23a43b6960de52e32c2d80fbf668023606ad0c1994f`. Die wesentlichen Evidencehashes stehen separat in
`evidence-sha256.json`. Kein Eingriff in den separaten M2-Worktree oder master.


### Abschließende Entscheidung

**Release: HOLD.** Der Planner-Budgetnachweis wird von der unnötigen MVP-Retrieval-
Voraussetzung entkoppelt. Die historische konkrete `Unavailable`-Raise-Zeile und
Ursache konnten mit den erhaltenen redigierten Nachweisen und zwei erfolgreichen
frischen Reproduktionen nicht bewiesen werden; dieser Teil von Aufgabe A bleibt
offen. Ein grüner neuer Testlauf löst diesen Diagnoseblocker nicht rückwirkend auf.
Kein nachgewiesener Produktdefekt, daher Produktbytes unverändert. Zusätzlich
bleiben Anwendung des geprüften Patches im Zielworktree und dessen spätere
Integration außerhalb dieses Auftrags pending. Keine Real-Source-Abnahme.

Für einen erneuten Originalablauf nur einen neuen synthetischen Root und den
bewahrten temporären Exceptionbeobachter verwenden; nicht den alten Root
fortsetzen. Erst ein dabei tatsächlich aufgetretener Stacktrace erlaubt die
Zuordnung zu Deadline, FTS, Store oder Reader. Der Beobachter ist eine lokale
Diagnosehilfe, kein automatischer Retry oder freigegebener Produktpatch.
