# C26: B3–B7-Integration und Freigabegates

22.10.2026. Integrationsbasis: Live-master
`c49645734dcba6d9d1aac8d4192841fa1a655051` (#144/B6), dessen erster Parent
`775e31032db6d61c4282c1b721f2a85e9588bfe7` #143/Knowledge integriert.
B7-Ausgang: PR [#145](https://github.com/rf-data/Personal_Assistant/pull/145),
`cba3302261be5b5cb0a36fc482250a5268b8ad44`.
**Lokale synthetische Integration; keine reale Wochenabnahme und kein Deployment.**

## Tatsächlicher Mergeumfang

Die zwei Konflikte betrafen `scripts/cs50_batch.py` (Registrierung und Dispatch
der unabhängigen Code- und Media-Commands) und `multiformat_pilot.md` (zwei
ergänzende Nachträge). Beide Seiten bleiben erhalten. `plan --include-code-indexes`,
`code`, `code-inventory`, `media-plan`, `transcripts`, `inventory`, `download`,
`seal` und `workflow` bleiben verfügbar. B6s Batch-/Processing-/Discovery-/ZIP-/
Codeimplementierung und die drei durch #143 korrigierten Knowledge-Module sind
gegenüber dem genannten Master byteidentisch. Keine doppelte Keywordidentität
wurde wieder eingeführt.

Die einzige zusätzliche Runtimeintegration ist ein read-only Übergang von
vorhandenen B6-Importgruppen zu B7-F0. Details und Eingabefelder stehen im
[aktualisierten B7-Runbook](media_last_pilot.md#übergabe-vorhandener-b6-codeartefakte).
Die vorhandenen Grant-, Batch-, ArtifactReceipt-, Quality- und Handoff-Verträge
werden erneut geprüft. Kein neuer Parser, Importer, Medienexecutor oder Scheduler.
Defaultgraph und Source-/Material-IDs bleiben ohne explizites Codeindex-Opt-in
unverändert. Bestehende Importerrevisionen werden nicht umgeschrieben.

## Was gemeinsam ausführbar ist

| Material | Vorhandener Weg | Tatsächliche Grenze |
| --- | --- | --- |
| Explizite HTML-/PDF-Dokumente | B3/B4 Batchdownload, Seal, C16/C18, HTML-/PDF-v2, C10/Handoff | Höchstens acht ausgewählte Quellen; 1 MiB je Raw; neue Roots und Einzelgrants |
| Offizielle SRT/TXT | B5 begrenzter Offlineimport mit Lecture-/Sprach-/Zeit-/SHAbindung | Beschaffung separat; generischer C26-Downloader ist kein SRT/TXT-Executor; TXT erhält keine erfundenen Zeiten |
| Python / ausgewählte ZIP-Mitglieder | B6 Offlineimport, Code-v1, begrenzte AST-Projektion, Quality/Handoff | Höchstens acht ausgewählte Quellen inkl. Archiv, höchstens sieben zugeordnete Mitglieder; kein Codeausführen, keine automatische C18-/Knowledgepublikation |
| Bestehende geprüfte Materialien | B7-F0 mit aktuellem Grant und zweck-/hashgebundener Eignung | Kein Goldurteil; ZIP allein erfüllt keinen Textbedarf |
| Shorts / Google Slides | Explizite Rollen-/URLreferenzen und Plan | Keine Shorttranskripte, Export-URLs oder Medienhashes erfinden |
| Lokale Medien / Remoteaudio / Remotevideo | B7-F4/F5/F6-Vorschläge | **No-Go für Ausführung:** begrenzter Executor-/Codec-/Modell-/Receiptvertrag fehlt |

F0–F6 bleiben eine deterministische Planungsreihenfolge. Fehlende Eignung,
Hash-/Grantfehler, `access_denied` oder `technical_failure` erlauben keine stille
Eskalation. Rawmedien sind kein fertiger Text, Transkript ist kein Visualbeleg.
`execution_supported=false`, `knowledge_fact_verified=false` und unvollständige
Coverage bleiben sichtbar. Hohe Blockzahlen oder ein grüner technischer Gate
ersetzen keine menschliche fachliche Prüfung.

## Nach Review/Merge: vorhandenen Worker kontrolliert aktualisieren

Kein neues Imagekonzept, zusätzlicher Container, Paketdownload oder neuer Mount
ist nötig. Der vorhandene `docker/DockerFile.worker` mit Repositorywurzel als
Buildkontext kopiert die benötigte `src`-/`scripts`-Closure. Imageupdate/Redeploy
muss der Betreiber separat genehmigen und durchführen. Standardstart,
Restart-Policy und vier bestehende Bind-Mounts bleiben erhalten.

Vor dem Redeploy laufende Jobs kontrolliert beenden bzw. ihren persistierten
Zustand prüfen; danach Image-/Gitrevision und unveränderte Mount-/UIDbindung
nachweisen. Kein Restarttest wurde hier auf Hetzner durchgeführt. Im aktualisierten
bestehenden Container, noch ohne Downloads oder Jobstart:

```sh
/app/.venv/bin/python -B -m scripts.worker_image_smoke
/app/.venv/bin/python -B -m scripts.cs50_batch plan --help
/app/.venv/bin/python -B -m scripts.cs50_batch code --help
/app/.venv/bin/python -B -m scripts.cs50_batch code-inventory --help
/app/.venv/bin/python -B -m scripts.cs50_batch media-plan --help
/app/.venv/bin/python -B -m scripts.cs50_batch transcripts --help
```

Die CLI-Smokeprüfung allein prüft keine Mounts, Grants, Originale oder aktiven Jobs.
Keine alte Helferdatei aus B2/B3 in ein neues Bundle mischen. Neu exportierte
Bundlebytes müssen zur tatsächlich installierten Revision passen.

## Go-/No-Go vor dem ersten gemeinsamen Week-0-Realpilot

**Go für einen begrenzten realen Schritt erst nach allen folgenden Nachweisen:**

1. PRreview/Merge und separat genehmigtes Codeupdate desselben Workers; die obigen
   CLI-Prüfungen im tatsächlichen Container sind grün.
2. Betreiber benennt **neue** private Arbeits-/Policy-/Token-/Reportziele pro Lane.
   `cs50_pilot_01`, dessen Datenbank, Loviscach und globale Stores bleiben geschützt.
   Root-owned Mounts werden ausschließlich mit dem bestehenden
   [B3-Bootstrap](html_pilot.md#betriebsdateien-im-container-erzeugen) übergeben:
   tatsächlicher Worker UID/GID 1000:1000, keine Stammrechteänderung.
3. Mount-Policy bestätigt echte separate Mountidentität, Zweckunterverzeichnisse,
   Ownership, private Rechte und keine Symlinks/unerwarteten Submounts. Alle
   benötigten Roots sind für den Worker tatsächlich zugänglich.
4. Exakte Snapshot-/Source-/Material-/Lecturebindung, einzeln bestätigte
   Download-/Process-/Nutzungs-/Lizenz-/Robots-/Aufbewahrungs-/Widerrufsbelege;
   lokale Inputs zusätzlich mit unabhängigen erwarteten Rawhashes. Kein Grant
   wird von einem anderen Format, ZIPmitglied oder früheren Pilot übernommen.
5. Freier Platz **neu** gemessen: mindestens 5 GiB Reserve **plus** vollständige
   C26-Kapazitätsallowances; 1 MiB Dokumentgrenze, 64-MiB-Archiv, bestehende
   Katalog-/Job-/Reportbudgets unverändert. ZIPgrenzen aus dem B6-Runbook gelten
   zusätzlich; bei Überschreitung stoppen, nicht pauschal erhöhen.
6. Exklusives Betreiberfenster, keine fremden aktiven Jobs/Locks, ein Worker,
   `max_parallel=1`, `max_queued=1`. Ein Source-Ref je Submission, terminalen
   Status prüfen, bevor der nächste folgt. Host-/Cgroupressourcen separat prüfen.
7. Preflight/Preview vollständig grün; sämtliche erwarteten Raw-/HTTPreceipt-/
   Payload-/Handoffhashes und Statuswerte nach jedem Schritt kontrollieren.

**No-Go** bei unklarem Mount/UID/Lock, fehlendem Grant, Hash-/Katalogkonflikt,
Quarantäne, unbekanntem Resumezustand, überschrittenem Budget oder fehlendem
vollständigen Bundle. Neue Scope-/Hash-/Grantentscheidung verlangt neue gebundene
Artefakte, kein Edit bestehender Receipts oder Datenbanken. F4–F6-Medienausführung,
LLMs, Whisper, Embeddings und Wissensextraktion bleiben außerhalb dieses Piloten.
Eine vollständige Week-0-/Kursabdeckung ist weiterhin nicht nachgewiesen.

## Kontrollierter Ablauf und Wiederanlauf

Vorbereitung/Export/Bootstrap und die **drei** expliziten HTML-IDs unverändert nach
[Week-0-Runbook](week0_pilot.md) ausführen. Nach dessen separat bestätigtem Setup
mit neuen, vom Betreiber belegten Variablen:

```sh
: "${C26_ROOT:?Neuen autorisierten B4-Pilotroot benennen}"
: "${C26_TOKEN:?Zugehoerige private Tokendatei benennen}"
P=/app/.venv/bin/python
"$P" -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase plan
"$P" -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json"
# Preview erzeugt kein HTTP. Erst nach separater Downloadfreigabe:
"$P" -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase download
"$P" -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/reports/download-01.json" --confirm
```

Bei Teilfehler **vor Seal stoppen**. Receipt-/SHAprüfung, einmaliges Seal,
`configure`, Process-Preflight, bestehender Worker, Health und genau ein
`workflow execute --source-ref ... --confirm` folgen den geprüften Befehlen im
[B4-Runbook](week0_pilot.md#ein-worker-jobs-nacheinander-gesamtbericht).
Nur `workflow report` pollen; Exit 0 einer Submission ist kein Completed-Nachweis.
Gesamtbericht erst nach terminaler Prüfung mit neuem Dateinamen speichern.

Danach separat autorisierte lokale SRT/TXT nach
[B5](multiformat_pilot.md), Python/ZIP nach [B6](code_zip_pilot.md) importieren und
verifizieren. Diese Lanes erhalten **eigene** neue Roots und Grants; sie werden
nicht in den B4-C18-Katalog eingeschleust. B7 liest anschließend nur ausdrücklich
benannte, gepinnte Receipts über seinen [Media-Plan-Befehl](media_last_pilot.md).
Das kann F0 ergeben oder offen gebliebene Text-/Visualbedarfe dokumentieren.

Wiederanlauf: identischer Scope und gleiche Grants/Inputs, neuer Reportname.
Erfolgreiche Artefakte bleiben byteidentisch. Downloadretry nur bewusst mit
`--retry-failed`, C18-Recovery/`workflow resume` nur für den geprüften einen Ref;
kein pauschales erneutes Execute. B6 prüft Importgruppen erneut, B7 ist read-only.
Ein alter B7-Report wird über `--previous-report` gebunden; abweichende Requests,
Grants oder Artefakte verlangen einen neuen Plan, keine automatische Adoption.

## Tatsächliche Offlinevalidierung

Umgebung: vorhandene Projektvenv, Python 3.12.12, Pytest 9.1.1, Pydantic 2.13.4,
PyMuPDF 1.28.2, SQLite 3.50.4, Ruff 0.16.0. Keine Installationen/Downloads.
Alle Tests verwenden synthetische Daten und isolierte temporäre Roots. Keine
Host-/Original-/Download-/Produktivprüfung wird daraus abgeleitet. Reale Quellen,
private Pilotroots und globale Stores wurden nicht geöffnet.

| Abschließender Lauf | Pass / Fail / Skip | Dauer |
| --- | --- | --- |
| B6/B7 und neue Übergabe | **118 / 0 / 0** | 257,85 s |
| C26-Pilot/Worker, Transcript und Knowledge | **313 / 0 / 4** | 412,97 s |
| Material-/Quality-/Handoff-/Discovery-/Selection-/Visual-Verträge | **288 / 0 / 0** | 275,05 s |

Gesamt dieser drei unterschiedlichen Testauswahlen: **719 passed, 0 failed,
4 skipped**. Davon 26 neue Integrationsfälle, 38 ursprüngliche Media-Planfälle
und 54 B6-Code-/ZIP-Fälle. Getestet sind echte synthetische B6-Importartefakte,
ZIPmitglieder und standalone Python einschließlich Unicode/BOM/CRLF,
read-only F0-Wiederverwendung ohne neuen Prozess/Import, deterministische Reports,
Hash-/Receipt-/Handoff-/Rootauswahlschäden, entzogene Container-/Mitglieds-/
Geschwistergrants, falsche Container, malformed gepinnte Receipts, CLIerhalt und
explizites Discovery-Opt-in. Ein ZIP allein bleibt unzureichend für Textbedarf.
Die vorhandenen Suiten prüfen insbesondere Teilfehler/Resume, No-Overwrite,
Codeerhalt im Handoff, SRTüberlappung, TXTnullzeiten, getrennte Knowledgeidentitäten,
F0–F6-/Grant-/Kapazitätsentscheidungen und vorhandene Mount-/Bootstrapgrenzen.

Die vier Skips betreffen den privilegierten Root-/Dropped-UID-Bootstraptest,
den opt-in Docker-Buildkontextaudit, den Test mit einem ausdrücklich benannten
gebauten Dockerimage sowie einen nicht bereitgestellten Original-Transcriptpilot.
Sie sind keine grüne Host-/Image-/Realabnahme. Der vorhandene Worker-Smoke wurde
zusätzlich **lokal** mit dem Projektinterpreter tatsächlich ausgeführt: **4/4
passed** (`cs50_batch`, `cs50_worker`, `cs50_material_quality`, `deployment`).
Kein Dockerbuild/-start und kein aktualisiertes Hetznerimage wurden hier geprüft.

Reproduktionspräfix im Integrationscheckout; `C26_TEST_PYTHON` benennt die
vorhandene Projektvenv, nicht eine neu zu installierende Umgebung:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$C26_TEST_PYTHON" -m pytest -q -p no:cacheprovider \
  tests/test_c26_integrated_pipeline.py tests/test_cs50_media_plan.py \
  tests/test_cs50_code_zip.py --basetemp=/dev/shm/c26-integration-release
```

Derselbe Präfix, jeweils separater neuer Basetemp, für die weiteren Läufe:

```sh
# --basetemp=/dev/shm/c26-integration-regression-final
tests/test_cs50_pilot.py tests/test_cs50_week_pilot.py
tests/test_cs50_multiformat.py tests/test_cs50_batch_worker.py
tests/test_cs50_capacity.py tests/test_worker_image_content.py
tests/test_official_transcript_import.py tests/test_transcript_unknown_time.py
tests/test_knowledge_transcript_provenance.py tests/test_cs50_srt_knowledge_integration.py
tests/test_knowledge_identity_arguments.py tests/test_cs50_knowledge_input.py
tests/test_knowledge_source_id.py tests/test_lazy_marvin_import.py

# --basetemp=/dev/shm/c26-integration-materials
tests/test_cs50_material_contracts.py tests/test_cs50_material_code.py
tests/test_cs50_material_processing.py tests/test_cs50_material_mapping.py
tests/test_cs50_material_quality.py tests/test_cs50_lecture_adapter.py
tests/test_cs50_discovery.py tests/test_cs50_selection.py
tests/test_cs50_timed_selection.py tests/test_cs50_visual_inventory.py
```

Eine erwartete ZIP-Duplicate-Name-Warnung entsteht im vorhandenen negativen
Archivkollisionstest. Entwicklungslauf: 115 pass/3 fail, weil die neue Assertion
nur `passed` statt auch des vorhandenen gültigen `passed_with_warnings` erlaubte.
Gezielter Debuglauf: 1 fail/23 deselected. Die Assertion wurde korrigiert, kein
Runtimegate abgeschwächt; alle drei Fälle im abschließenden 118er-Lauf grün.
Ein falsch benannter Image-Testpfad führte zuvor zu einem Aufruf mit Exit 4 und
null ausgeführten Tests; er wurde im vollständigen 313/4-Lauf korrigiert.
Entwicklungsläufe werden nicht zur obigen Summe addiert.

Ruff Check ist für alle sieben gegenüber Master neuen/geänderten Pythondateien
grün; Format Check für diese und die neun direkt übernommenen B6-/Fix-Dateien:
**16/16 formatiert**. Der breitere Ruff Check meldet genau drei bestehende Befunde
in `src/run_knowledge_extraction.py`: I001, E722 und E402. Dieselben Diagnosebytes
wurden mittels `git show c496457...:src/run_knowledge_extraction.py` und Ruff
`--stdin-filename` am unveränderten Master reproduziert. Alle elf übernommenen
B6-/Fix-Implementierungs-/Testdateien sind zusätzlich byteidentisch geprüft.
Keine neue Ruffdiagnose, keine pauschale grüne Repositorylintabnahme.

`git diff --check`, Kompilierung der sieben Pythondateien und 15 lokale
Markdownziele sind erfolgreich geprüft. Auf dem
verifizierten Master gibt es keine `.github/workflows`; GitHub lieferte für
#145 eine leere Checkliste. Daher keine Behauptung erfolgreich ausgeführter
Hosted-CI. Die regulären Commit-Hooks bestanden Whitespace/Dateiende, Python-AST,
Debugstatements, Dateigröße und Ruff Format; YAML/JSON/TOML hatten keine passenden
Änderungen und wurden als solche übersprungen. Die manuelle
Gesamtrepository-Pytestsuite und netzwerkabhängige
Dependencyaudits wurden nicht gestartet. Kein API-Schlüssel/Provider ist für die
obigen Tests erforderlich; keine neue Dependency oder CIarchitektur.

## Git und Lifecycle

Master wurde live über `ls-remote` und die tatsächlich geladenen Commitobjekte
verifiziert; ein lokal nicht aktualisierbarer Trackingref wurde nicht als Basis
verwendet. Die lokale Git-Schreibstörung betrifft auch den normalen Worktreeindex;
ein separater temporärer Index auf dem RAM-Dateisystem erlaubt reguläre Git-
Stagingoperationen innerhalb desselben Prozesses, ohne vorhandene Gitdateien
manuell zu ersetzen. Auch der reguläre Commit scheiterte **nach** erfolgreichen
Hooks beim Update des auftragseigenen Branchrefs. Das bereits erzeugte Commitobjekt
wird vor Veröffentlichung auf identischen geprüften Tree und beide Parents
kontrolliert. Ein neuer auftragseigener Publikationsbranch/Reviewcheckout hält
diesen Stand; der bestehende Remotehead von #145 wird ausschließlich per normalem
Fast-forward aktualisiert. Kein Force-Push, Reset oder manuelle Refreparatur.
Der ursprüngliche Integrationsworktree bleibt mit dokumentiertem lokalem
Merge-/Indexzustand erhalten. Ein zu früh
während des noch laufenden Worktreecheckouts gestarteter
Merge brach ab; nach abgeschlossenem sauberem Checkout wurde der Merge ohne
Autostash wiederholt. Keine Stashes, fremden Worktrees oder Daten geändert.

PR #145 bleibt offen. Eigene Integrations-/Publikationsbranches und Worktrees
bleiben bis zur bestätigten Integration erhalten; kein automatischer Merge oder
historisches Cleanup. Dauerhafte Dokumente sind erst nach regulärem Merge in
master integriert. Die technische Lieferung erteilt keine reale Betriebsfreigabe.
