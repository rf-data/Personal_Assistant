# CS50-Pipeline: technischer Abschluss

Stand: 14. Oktober 2026. Ausgangspunkt nach Fetch: origin/master de4ac38,
Checkpoint-PR #26 integriert. Umsetzung in einem isolierten Worktree; keine
produktiven Quelldaten verändert, keine Kursmaterial-Downloads, keine bezahlten
APIs, keine automatischen Merges/PR-Schließungen. Neue Arbeiten sind gestapelt
und müssen in der dokumentierten Reihenfolge menschlich integriert werden.

## Ergebnis und Beweisgrenzen

Abschließende vollständige Suite: **461 bestanden, 6 bekannte TXT-Fehler,
0 Setupfehler, 5 nachvollziehbare Skips**, 472 Fälle in 1437,83 s.

Der technische SRT→Knowledge-Pfad ist für eine vollständige Lecture, zehn
Python-Lectures und alle sechs Kurse/50 Lectures offline nachgewiesen. Dabei laufen
100 bestehende Download-/Import-Tasks über Fake-HTTP und anschließend echte
Importer-, Binding-, Chunking-, Evidence- und deterministische Consolidation-
Funktionen. Nicht nur Modelle oder normalisierte Ergebnisse werden gestubbt.
HTTP-Transport/LLM-Antworten sind Fake; die Ergebnisse heißen ausdrücklich synthetic.

Dies ist **keine fachliche Qualitätsabnahme**, kein echter Großlauf und kein neuer
reeller segment_v1-Modelltest. Kein Graph-/Selection-/Chunking-/Whisper-/Prompt-
Refactoring. Semantische LLM-Consolidation wurde ausschließlich hinsichtlich der
geprüften Metadatenkonstruktoren korrigiert, nicht ausgeführt.

## Kleine PRs und Abhängigkeiten

| PR | Basis | Stufe / Ergebnis |
|---|---|---|
| [#27](https://github.com/rf-data/Personal_Assistant/pull/27) | master mit #26 | A02: unveränderlicher Scope, persistente Request-/Tokenreserven, Prozesslock, Usage separat. |
| [#28](https://github.com/rf-data/Personal_Assistant/pull/28) | #27-Branch | A03: v2 relative Knowledge-Inputs, expliziter Workspace, v1-Kompatibilität. |
| [#29](https://github.com/rf-data/Personal_Assistant/pull/29) | #28-Branch | A04: Metadaten durch allgemeinen Extraction-/beide Semantic-Konstruktoren. |
| [#30](https://github.com/rf-data/Personal_Assistant/pull/30) | #29-Branch | A05: minimaler eingefrorener Worker-Lockgraph und explizites optionales SDK-Profil. |
| [#31](https://github.com/rf-data/Personal_Assistant/pull/31) | #30-Branch | B01: separater vollständiger Lecture-Runner; alter Zwei-Chunk-Pilot unverändert. |
| [#32](https://github.com/rf-data/Personal_Assistant/pull/32) | #31-Branch | B02: vollständige Chunks, Modelle/Roundtrip, vier atomare Abschlussartefakte und Marker. |
| [#33](https://github.com/rf-data/Personal_Assistant/pull/33) | #32-Branch | B03: sequenzieller Kursauftrag, next-pending, ein Budget, conservative Resume. |
| [#34](https://github.com/rf-data/Personal_Assistant/pull/34) | #33-Branch | B04: gewichtete Quality/Coverage, Artefaktprüfung, korrekte Teilfortschritte. |
| [#35](https://github.com/rf-data/Personal_Assistant/pull/35) | #34-Branch | B05: sechs explizite IDs, 50 Bindungen/100 Tasks, gemeinsame Grenzen, Offline-Demo. |
| [#36](https://github.com/rf-data/Personal_Assistant/pull/36) | #35-Branch | C01–C03: manuelle Reviewverträge, echte Cuefenster, Freigabecheckliste. |

Der abschließende Integrations-PR baut auf #36 auf, ergänzt die CLI-End-to-End-
Regression sowie zwei nachgewiesene Grenzprüfungen und diesen Abschluss-/Testbericht.
Alle veröffentlichten Dateibäume stimmen mit den lokal getesteten Bäumen überein.
Git-Shell-Push ist lokal mangels Credentials nicht möglich; Veröffentlichung
über den verbundenen GitHub-Zugang. Keine automatischen Merges oder Rebases.

## End-to-End-Verträge

- Discovery/Selection/Adapter: bestehende sechs IDs **cs50x**, cs50_python,
  cs50_sql, cs50_ai, cs50_web, cs50_cybersecurity. 12/10/7/7/9/5 Lectures.
  50 ausgewählte englische SRTs; TXT-first-Default und 50/100-Plan unverändert.
- Source: kontrollierter unveränderter CS50Executor; Raw-/Transcript-Hashes,
  Importbelege und Original-URLs werden erneut überprüft. Kein Video-/Whisper-Fallback.
- Portabilität: neue Inputmanifeste v2 relativ; Workspace explizit. Alte v1-Dateien
  bleiben ausdrücklich lesbar. Traversal, Symlinks, fremde Roots/Hashänderungen scheitern.
- Job: vollständige Source-/Transcript-/Chunkplan-/Prompt-/Evidence-/Provideridentität
  über A01. Ganze Lecture und Teilfenster teilen denselben vollständigen Plan.
- Budget: alle Jobs eines gewählten Scopes teilen dasselbe A02-Journal. Reservierung
  vor Transport, keine Rückerstattung nach Fehlern, keine automatische Wiederholung.
  Ein tatsächlicher Usagewert über der konservativen Reserve wird persistiert und
  blockiert den Scope. Genauere Kosten/Preise müssen vor echten Läufen manuell geprüft werden.
- Laufzeit: persistente Deadline und harter isolierter POSIX-Prozessgruppen-Timeout.
  Neustarts erweitern die Deadline nicht. Kein globaler Event-Loop-/SQLite-Workaround.
- Evidence: Originalsegmente/Originalzeiten; segment_v1 oder explizit Legacy chunk.
  Fehlerhafte präzise Kandidaten bleiben unvalidiert und getrennt dokumentiert.
  source="transcript" und Herkunftsstrategie official_subtitle bleiben getrennt.
- Completion: alle erwarteten Chunks einschließlich irrelevanter None-Extraktionen;
  vollständig reguläre Knowledge-/Consolidation-Modelle, Quality und Coverage;
  prepared-Hashes und exklusiver Abschlussmarker. Vorhandene Dateien reichen nicht.
- Scheduler: concurrency=1, explizite Sourceauswahl, vollständiger Preflight vor
  weiteren Requests, sichere next-pending-Logik. unknown/failed/Korruption stoppt den Scope.
- Reports: erwartete/verarbeitete Chunks, Lecturezustände, Source-/Resultreferenzen,
  bekannte/ungeklärte Usage, Qualitätsmetriken aus richtigen Zählern/Nennern.
  Teilresultate und synthetische Daten werden nicht als echte komplette Kurse ausgegeben.

course_id, section_key, lecture_id, resource_id, source_id, Original-URL, Sprache,
media_id und komplette Transcript-Provenienz bleiben erhalten. Business-Modelle
halten ihre bisherigen Felder; zusätzliche Rollen/Identitäten/Graph-/Hash-/Version-
Informationen stehen in externen versionierten Input-/Job-/Scope-/Completionbindungen.
Cybersecurity 0 behält media_id=None; CS50x ai und Woche 0 bleiben unverändert.

## Ausführbare Offline-Einstiege

- `python -m scripts.cs50_lecture`: eine explizite Lecture, Default ein Chunk,
  --all-chunks oder begrenztes Fenster, v1/v2-Input, Offline-Default, ausdrückliches
  --execute-llm mit Parent-/Worker-Authorization für späteren Betrieb.
- `python -m scripts.cs50_schedule`: ein Kurs oder --six-course-batch mit allen
  sechs --course-IDs, --max-lectures, --audit-only, gemeinsame Caps/Timeout.
- `python -m scripts.cs50_offline_demo --output /scratch/new-exclusive-demo`:
  vollständiger verifizierter synthetischer Sechs-Kurse-Pfad plus Resume;
  gesperrte reale Sockets, ausschließlich MockTransport.
- `python -m scripts.cs50_review_template`: acht prüfbare unannotierte Fenster;
  --origin muss ausdrücklich deklarieren, ob original oder synthetic.

[Ausführungsbeschreibung](../../operations/cs50_batch_execution.md), [Gold-/Freigabecheckliste](../../evaluation/cs50_quality_evaluation.md)
und [Testmatrix](../../operations/cs50_pipeline_test_matrix.md) erläutern die tatsächlichen Grenzen.
Defaultlimits autorisieren weder vollständige kostenpflichtige Großläufe noch
Downloads. Es gibt keinen automatischen Retry/Unknown-Reset oder Budget-Neustart.

## Tatsächliche Befunde und verbleibende Einschränkungen

1. Source-Preflight wurde nach einem echten Offline-Regressionfehler verstärkt:
   pending-Receipts konnten eine seit Planung geänderte spätere Quelldatei vorher
   übersehen. Jetzt revalidieren Preflight/Runner/vor-Dispatch den echten Input.
2. Ein Fake-Usage-Test zeigte eine fehlende Grenze nach Providerantwort: Usage
   konnte größer als reserviert sein. Nun wird sie konservativ unknown gespeichert,
   berichtet und weiterer Spend blockiert; keine Garantie externer Providerabrechnung.
3. Fehlerhafte präzise Providerfelder bleiben im separaten failed-provider-Sidecar;
   sie werden nicht als Ergebnis adoptiert. Nicht parsebares HTTP-/JSON-Payload hat
   weiterhin kein vollständiges Responsearchiv; Reservierung bleibt verbraucht.
4. Neues minimal-worker Lockfile ist offline geprüft (32 Pakete, keine Upgrades).
   Fresh sync scheitert am fehlenden Wheelcache; keine Downloads zugelassen. Alle
   Regressionen laufen in der tatsächlich vorhandenen regulären uv-Worker-.venv.
5. SDK-Profil ist ausdrücklich optional. Ohne SDKs wird der betreffende Test im
   Offlineprofil erklärt übersprungen; im expliziten SDK-Profil scheitert er und
   wird bei vorhandenen Paketen tatsächlich isoliert konstruiert, ohne API.
6. Sechs TXT-Zeitvertragfehler bleiben unverändert und außerhalb des Auftrags.
   Kein TXT-, Visual-, PDF-/Whisper- oder allgemeiner Legacy-Resume-Umbau.
7. Vorhandener Original-Pythonpilot wurde read-only neu geprüft: 157 Chunks,
   acht echte Cuefenster im temporären Reviewtemplate, keine Claims/Reviewerurteile.
   Echter präziser Qualitätstest und manuelle Annotation bleiben ausstehend.
8. Aktuelle HTTP-Erreichbarkeit aller 50 echten SRTs und tatsächliche Vollkurs-
   Kosten/Qualität wurden nicht geprüft. Dataset-/Modellfreigabe muss manuell erfolgen.
9. Wiederholte starke Source-/Plan-/Artefaktprüfung kostet messbar Laufzeit; der
   50-Lecture-Fake-E2E mit vollständigem Resume dauerte 476,30 s. Keine unsichere
   Cacheadoption eingeführt. Profiling vor großen echten Läufen sinnvoll.
10. Alte A01-Pilotjobs bleiben eigenständig; der neue vollständige Runner übernimmt
    sie nicht still, sondern verwendet seine vollständige portable Jobidentität.

**Nächster menschlicher Schritt:** Stack reviewen und in Reihenfolge integrieren,
Worker-Wheelcache separat bereitstellen; danach acht Originalfenster kuratieren
und ausschließlich einen explizit genehmigten 1–2-Chunk-segment_v1-Qualitätstest
starten. Technische Bereitschaft ist nachgewiesen; fachliche Freigabe steht aus.
