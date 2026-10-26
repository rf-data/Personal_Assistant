# C24-R Integration gegen master – 2026-10-26

Vergleich PASS (Dateien/Historie); Integration und Tests auf Zielmaster HOLD.
Kein Merge, kein Cherry-Pick, keine Änderung an master oder fremden Worktrees.

## Referenzen und Nachweisgrenze

- C24-R-HEAD/Basis: `4c057ae33d41ba98e227879cc8a51283338e4a0b` plus Lieferdiff.
- Lokales `origin/master`: `e68275205fefb7a5f6db42bc45060e505bfcefb5`.
- GitHub-master bei Abfrage: [`a8af1d9372eb435d3e1331c33b047d21120d57c2`](https://github.com/rf-data/Personal_Assistant/commit/a8af1d9372eb435d3e1331c33b047d21120d57c2).
- [PR #124](https://github.com/rf-data/Personal_Assistant/pull/124): merged,
  Merge `79d800caf3270de07296b49dc4585c1e01ceb085`, Searchfeature `4259187`.
- [PR #125](https://github.com/rf-data/Personal_Assistant/pull/125): merged,
  Merge `b2c9e3ac41441721940269e86ffe3896b289540b`, Feature `c07ed9a`.

GitHub-Connector read-only verwendet. Shell-`git ls-remote` scheitert an DNS;
Fetch würde außerdem den nicht schreibfreigegebenen gemeinsamen Git-Speicher ändern.
Die lokale Remote-Referenz wurde deshalb nicht aktualisiert. GitHub-Compare
bestätigt: Remote ist sechs Commits voraus, lokale Referenz ist Mergebase,
keine Divergenz. Vollständige Dateiliste dieser sechs Commits geprüft.
Von den ursprünglichen 50 Lieferdateien betreffen sie nur `.gitignore`,
`pyproject.toml`, `uv.lock`; diese wurden zusätzlich am Remote-SHA gelesen
(Lock: Rootmetadaten-Ausschnitt). Für die übrigen Dateien ist der lokale
Bytevergleich dadurch auch für den abgefragten Remote-SHA gültig.

## Integrationsmatrix

| Komponente | Stand in master | Konflikt / konkretes Vorgehen | Zusätzliche Zielregression |
|---|---|---|---|
| SearchHTTP / IndexHTTP | identisch | Kein erneutes Einführen oder Kopieren | echte HTTP-/Restartfälle |
| SearchRequest und Indexmodelle | funktional vorhanden, erweitert | master nutzt `ContentCourseId` einschließlich `loviscach_mathe_1`; C24-R nutzt alte CS50-Typen. master behalten | Loviscach- und CS50-Scope, Live-ACL |
| Controlled Index Jobs | vorhanden, Indexjobs-Testdatei byteidentisch | `index_jobs.job_delivery_guard` schützt inzwischen auch `content_import`; niemals durch alten Guard ersetzen | gemischte Import-/Indexjoblisten, ACL während Delivery, Cancel/Retry |
| C16 Gateway/Controller/Catalog/Executor/Registry/Worker/Models | funktional vorhanden, erweitert | master enthält `content_import`, Importrechte, Flag, Parameter, Routen und Workflow-Katalogplanung; ganze Dateien nicht übernehmen | Import + Index + Workflows gemeinsam, Rollen/Default-off |
| ContentIndex | Build-ID-/Ownershipänderungen bereits enthalten | einzige Abweichung hier: erweiterter CourseId-Import in master; master behalten | Kursgrenzen, atomare Aktivierung, Fehler/Ressourcen |
| CLI `scripts/job_control.py` | identisch | keine Übernahme | bestehende CLI-Verträge |
| C16-/Workflow-/Search-/Index-Schemas | vorhanden, erweitert | master-Schemas behalten; keine alten Enum-/Artifact-Snapshots darüberkopieren | Snapshots gegen Zielmodelle, Loviscach und content_import |
| Gemeinsamer Job→Search-Test und Fixture-Fix | Datei fehlt | `tests/test_c24r_integration.py` selektiv hinzufügen; Event-Cleanup nur Testcode | echter Loopback nach Fix zwingend, deterministische Lockprobe, Cancel vor/während Build |
| `tests/index_cancel_probe.py` | fehlt | zusammen mit neuem Integrationstest hinzufügen; Bereitschaftsmarkierung atomar | Guardian/Prozessende, alte Generation bleibt |
| Vorhandene Search-/Indextests und Hilfsdateien | identisch | `test_content_search_http.py`, `test_content_index_jobs.py`, `index_job_probe.py`, `index_job_support.py` nicht doppelt einführen | gemeinsam mit neuen Integrationstests ausführen |
| GoldCandidatePool / Validator-CLI / 30 Tests | Dateien fehlen | zwei Module und `test_gold_candidates.py` selektiv ergänzen; vorhandene DEV-03-Evaluation weiterverwenden | Originalhash, Provenienz, Rechte, CSV, keine Promotion; Schema auf Zielmodellen neu ableiten |
| Loviscach-Inventar, leerer Pool, Review-CSV, Schema | Dateien fehlen; fachliche/kursbezogene Grundlagen inzwischen vorhanden | Dokumentation auf Zielmaster aktualisieren: alte Aussage „nur CS50“ gilt dort nicht. Leerer Pool bleibt leer | Typ-/Schemaabgleich und menschliche Original-/Rechteprüfung |
| Search-/Index-API-Dokumentation | überwiegend identisch | historische Laufberichte behalten/kennzeichnen; sechs Course-Enums sind erweitert; kein alter Vertragsstand zurückschreiben | Beispiel-/Schema-/Linkprüfung |
| C24-R-Berichte und finales Abnahmepaket | fehlen | als historischen Branch-Nachweis ergänzen; Zielabnahme separat dokumentieren | Nachweisherkunft und HOLDs erhalten |
| Dependencies | master besitzt nun `test-offline` mit PDF/HTML | C24-R-Dependencycommit nicht unverändert cherry-picken; bestehende Testgruppen nutzen | frische minimale Installation, gesamte Zielregression |
| `.gitignore` | unterschiedliche spätere Ergänzungen | nur Ausnahmen für neue Kandidaten-JSON/CSV addieren; API-JSON ggf. explizit stagen, master-Ausnahmen erhalten | alle neuen benötigten JSON/CSV im Index vorhanden |

Ausgangsinventar: 13 byteidentische Dateien, 19 abweichende, 18 fehlende.
Die sechs final ergänzten Abnahme-/Inventar-/Exportdateien fehlen ebenfalls.
Vollständige dateigenaue Zuordnung im
[Lieferinventar](c24r_final_file_inventory.md).

Relevante spätere Änderungen: DEV-02-Importjobs `892dc3a`, source-lokale
Verwaltung `a9dc949`, DEV-03-Evaluation/Review (#129–#134), Loviscach-Scope
`d6f16d0`, C26-Pfad-/Runtimegrants und optionale Imports `c77128b`, danach
MAINT-03/04-Konfiguration und Offlineprofile. MAINT-05 bleibt unberührt.

## Präziser Übernahmevorschlag

1. C24-R als historischen Backupbranch sichern, ohne Mergeabsicht zu unterstellen.
2. Nach menschlicher Sichtung neuen Integrationsbranch vom frisch abgefragten
   master anlegen; nur dort arbeiten, keinen bestehenden fremden Worktree verwenden.
3. Nur die zwei Goldkandidatenmodule, zwei neuen Integrationstestdateien
   (`test_c24r_integration.py`, `index_cancel_probe.py`), Kandidatentest,
   sechs Loviscach-Dateien und passende C24-R-Nachweise prüfen/übernehmen.
4. Kandidatenschema auf den erweiterten Zielmodellen neu generieren und mit
   bestehenden DEV-03-Original-/Reviewverträgen abgleichen. Nur neue Ignoreausnahmen
   addieren. Bestehende produktive Search-/Index-/C16-Dateien beibehalten.
5. Neue Tests und bestehende Search/Index/Import/ACL/Kurs-/PDF-Regressionsfälle
   im minimalen Zielprofil ausführen, anschließend echte HTTP-Abnahme und Review.

Der vollständige Lieferpatch gilt ausschließlich für die alte Basis. Ihn auf
master anzuwenden oder den Completioncommit vollständig zu cherry-picken ist
kein geeigneter Integrationsweg. Ein tatsächlicher Konfliktmerge wurde nicht
simuliert; die genannten Konflikte sind belegte inhaltliche Überschreibungsrisiken.
