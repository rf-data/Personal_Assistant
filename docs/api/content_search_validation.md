# DEV-01 A: tatsächliche Search-HTTP-Validierung

19.10.2026, Europe/Berlin. Basis Backend `master`
`e478520d259ad1342f5641828586c4cd2876114f`, UI `main`
`af95415071e85a461579c0a1650fdd0efe6c25b9` nur lesend geprüft.
Eigener Branch `feat/dev01a-authorized-search`, eigener Worktree, keine Änderung
primärer Checkouts oder geschützter C24-06-A-/MAINT-Arbeit.

## Iststand und Liefergrenze

Auf der aktuellen Basis keine konkurrierende Search-/Indexjobimplementierung
oder entsprechender offener PR gefunden. Gemergte C23-/C24-Verträge sowie
ROADMAP/Issueplan/Implementierungsplan und Agentenanweisungen beider Repositories
geprüft. Interne Projektion/FTS5/Signed-Cursor vorhanden; C16-Registry kennt
Material-/Quality- und opt-in PDF-/Workflowprozesse. UI hat den kanonischen
Streamlit-Einstieg, authentifizierten C16-Client und B2-Reviewansichten, jedoch
keine allgemeine Searchansicht.

Paket A implementiert opt-in HTTP-Suche auf den bestehenden C24-Datenmodellen.
Betroffene Pythonmodule: `src/content_store/search_models.py`, `search_http.py`,
`src/job_control/http.py`, `scripts/job_control.py` und neue fokussierte Tests.
Die FTS5-Engine, Projektionspolicy, ContentStore-Modelle und Review-/Jobverträge
bleiben unverändert. [API und Übergabe](content_search_v1.md).

| Synthetischer Pfad | Tatsächlicher Nachweis |
| --- | --- |
| Raw → B-Gate → persistierte Parsed-Version | Handgeschriebene Codebytes mit Emoji/Combining/Tab/CRLF; tatsächlicher Receipt-/Hash-/Adaptervertrag |
| Deterministische Projektion → FTS5 | Bestehender expliziter Builder auf isolierten privaten Roots; kein HTTP-/Autobuild |
| Authentifizierte Gateway-Suche | Application und tatsächliche lokale TCP-HTTP-Aufrufe; serverseitige C16-Identität |
| Seiten/Anker/Originalreads | Drei stabile Codezeilentreffer, Cursorpaging ohne Duplikate, exakte Slices/SHA und bestehende Content-Text-/Locatorrouten |
| Prozessneustart | Zwei separate Gatewayprozesse, gleiche bestehenden Content-/Indexroots, identische Treffer ohne Rebuild |
| Jobs / Streamlit / Browser | **Nicht implementiert bzw. nicht ausgeführt in A**, Folgepakete B/C nach Integration des führenden Vertrags |

Keine Realdateien, privaten Korpora oder produktiven Stores geöffnet. Kein
Download, LLM, Qdrant, Embedding oder neue Dependency. Synthetische Ergebnisse
sind technische Funktionsnachweise, keine fachliche Suchqualitätsmessung.

## Umgebung und tatsächliche Läufe

Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, System-Pytest 7.2.1,
Ruff 0.16.0, vorhandene Umgebung ohne Installation/Sync. Pytest-7-AST-Warnungen
unter Python 3.12 sind keine Skips. Gemeinsames tatsächliches Präfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
-q --disable-warnings -p no:cacheprovider
```

| Lauf mit diesem Präfix | Ergebnis |
| --- | --- |
| `tests/test_content_search_http.py --basetemp=/tmp/dev01a-search-final` | **50 passed / 0 failed / 0 skipped**, 95,94 s |
| `tests/test_job_control.py tests/test_content_read_contracts.py tests/test_content_fts.py tests/test_evaluation_store.py --basetemp=/tmp/dev01a-regression-final` | **142 passed / 0 failed / 0 skipped**, 264,57 s |

Die neuen Tests prüfen Request-/Schema-/Querylimits, Authentifizierung, eigene
Course-/Sourceberechtigungen, Grantentzug, Quarantäne/Tombstone, echte FTS5-Scores,
fehlende und inkompatible Generation, Cursor-Manipulation/Parameter/Actor/TTL/
Revision/Keyrotation, redigierte Fehler, fehlerhafte JSON-/UTF-8-Daten,
Pagination und Wiederholbarkeit. Fremde Sourcepartition verändert weder erlaubte
Scores noch offenbart deren Beschädigung eine fremde Quelle. HTML-/PDFmodell-/
SRT-Locatoren verwenden bestehende B-Fixtures; keine neue native PDFparserabnahme.

Responseguard bleibt bis HTTP-Delivery bzw. Fehlerende offen. Writer ist während
dieses Guards tatsächlich Busy und danach wieder möglich. Verbindungsabbruch,
bereits abgelaufene Antwort sowie Zeitüberschreitung beim JSONencoding geben
keine Trefferbytes aus und schließen den Guard. Vorhandene Query-/Match-/Byte-/
Semaphore-/Hashprüfungen werden nicht reduziert.

Der tatsächliche TCP-Test läuft ausdrücklich mit erlaubten lokalen Sockets:
Die Standardsandbox verweigerte schon `socket()` (EPERM). Nach erfolgreicher
Berechtigungsprüfung wurde derselbe lokale Test ohne abgeschwächte Assertions
mit zwei Serverprozessen auf 127.0.0.1 ausgeführt. Keine externe Verbindung.

Vorläufe, nicht addieren: erster Lauf 45 passed / ein durch Socket-Sandbox
blockierter Test, 51,15 s; gezielter echter HTTP-Neustarttest 1 passed, 11,06 s;
anschließend 49 passed, 58,89 s. Danach wurde ausschließlich die Serialisierung
in das Antwortzeitbudget aufgenommen und ein Timeoutfall ergänzt; der endgültige
50er-Lauf oben prüft diesen Stand vollständig.

Die zusätzliche vorhandene `tests/test_workflow_http.py` war wegen fehlendem
`pymupdf` über ihren PDF-Testimport **nicht sammelbar**: 142 andere Fälle gesammelt,
ein Collectionfehler, kein Test ausgeführt. Danach erfolgte der unabhängige oben
aufgeführte Viermodullauf ohne dieses Modul. Ein vorheriger Aufruf enthielt einen
nicht existierenden Testdateinamen und führte ebenfalls keine Tests aus; er wird
nicht als Regressionsergebnis gezählt. Keine volle Repository-, native PDF-,
Browser- oder reale Abnahme behauptet.

Ruff Check und Format Check für die fünf geänderten/neuen Pythondateien sowie
`git diff --check` erfolgreich. JSONschemas gegen die tatsächlichen Pydantic-
Schemas und das Beispiel gegen `SearchResultPage` geprüft; lokale Markdownziele
vor Veröffentlichung geprüft. Keine Runtime-/Configdatei außerhalb des eigenen
Worktrees verändert. Testlogs bleiben außerhalb des Repositories.

## Beispiel und verbleibende Integration

[Das Beispiel](examples/content_search_v1.synthetic.json) wurde aus einem
zusätzlichen tatsächlichen authentifizierten Gateway-Aufruf erzeugt: drei
Treffer mit unveränderten Originalankern, keine privaten Hostpfade. SHA256 der
exakten JSONbytes:
`25058e363d3f131d1b03208fa5b15709cb20ce82d7b0b490abb71eec9dd83814`.
Schema-Snapshot: [Request, Capabilities, bestehende Page](examples/content_search_v1.schema.json).
Eine Metrik-/Relevanzbewertung eines Realkorpus wird daraus nicht
abgeleitet; das Beispiel enthält keine fachliche Goldreferenz.

A ist nach erfolgreicher Prüfung als eigener Implementierungs-PR zur regulären
Review-/Mergeentscheidung vorzulegen, verknüpft mit bestehendem Issue #114 /
Plan-ID C24-03-B. Kein neues Issue, keine automatische Done-/Issueclosure und
keine Änderung an D06/D07 oder offenen Real-/Produktionsabnahmen. Die vorhandene
Backend-Auto-add-Regel wird durch Live-Readback geprüft, kein doppeltes Item.

B soll den führenden Indexroot-/Suchvertrag nach Integration wiederverwenden und
die bestehenden C16-Catalog-/Worker-/Registrygates ausdrücklich erweitern. Kein
zweiter Root-/Jobvertrag auf Basis eines vermeintlich bereits integrierten A-PRs.
C benötigt den tatsächlich gemergten HTTP-Vertrag und scoped Indexstatus aus B.
Gemeinsame Streamlit-/Browserabnahme, Betriebs-/Produktionsfreigabe und fachliche
Realabnahme bleiben offen. Bekannte FTS5-Skalierungsgrenzen gelten unverändert;
keine größere Korpus-/Lastfreigabe durch diesen Adapter.

Eigener Branch und Worktree bleiben bei offenem PR erhalten. Dauerhafte
Dokumentintegration nach master ist erst nach bestätigtem Merge erfüllt;
kein Merge und keine historische Bestandsbereinigung durch diesen Auftragsteil.

## Abschließende Publikationsbasis

Während der Arbeit wurde PM-04 #122 integriert. Der eigene Branch wurde vor
Veröffentlichung ausschließlich per Fast-forward auf aktuellen master
`884373678d6c8b46f7d82b7885930d896c4f9cb5` gebracht. Dessen Delta zu `e478520`
besteht genau aus den drei PM-03-/PM-04-Dokumentationsdateien, keiner Pythondatei
oder Runtimekonfiguration. Der oben getestete Pythonstand blieb byteidentisch;
keine zusätzliche vollständige Testwiederholung als neuer Nachweis ausgegeben.

Der 142er-Regressionslauf umfasst 36 C16-, 14 Content-Read-, 47 FTS5- und
45 Reviewstorefälle. Die finalen 50er- und 142er-Läufe sind getrennte Umfänge;
frühere Entwicklungsläufe überlappen und werden nicht addiert. Schema-/Beispiel-
Roundtrip, exakter Beispielhash und 36 lokale Markdownverweise geprüft.

## PR- und Project-Readback

[Implementierungs-PR #124](https://github.com/rf-data/Personal_Assistant/pull/124)
ist offen gegen master, eigener Branch `feat/dev01a-authorized-search`,
mergefähig zum Prüfzeitpunkt. Genau elf beabsichtigte Dateien im PR; keine
Änderung am führenden Issueplan, an Dependencies oder ursprünglichen Parsern.
Keine CI-Checkruns gemeldet; die oben genannten Nachweise sind tatsächlich
lokal ausgeführte Prüfungen, keine behauptete GitHub-CI-Abnahme.

Vollständiger Project-Readback: 63 Items zum Zeitpunkt nach PRanlage, keine
doppelten Content-URLs. Der eigene PR wurde durch die vorhandene Backendregel
exakt einmal mit Backlog aufgenommen. Keine manuelle zweite Aufnahme oder
Project-Feldmutation. Bestehendes Issue #114 weiterhin OPEN / Backlog / P1 /
Retrieval / Planned, mit dem PR über dessen Beschreibung und diesen Bericht
verknüpft. Keine Issueclosure-/Done-Aktion und keine neue Realabnahme.

Paket A: implementiert und lokal getestet, PR offen, **noch nicht in master
integriert**. Paket B / C und gemeinsamer Streamlit-MVP-Lauf ausstehend; B soll
die führenden opt-in Konfigurationsgrenzen dieses PRs übernehmen. Der Auftrag
verlangt integrierte Vorgängerverträge, deshalb keine Folgeimplementierung gegen
einen als Defaultbranch ausgegebenen ungemergten Stand. Reguläre Review-/
Mergeentscheidung ist der nächste Übergabepunkt. Der eigene Branch und Worktree
bleiben bis dahin erhalten; keine Löschung fremder oder historischer Gitobjekte.
