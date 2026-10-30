# C27-R02 – Remediation des unabhängigen Audits C27-R01

Stand: 2026-10-29. Repository `rf-data/Personal_Assistant`, zugewiesener Worktree
`/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning`.

C27-R01-F01 bis F05 sind **FIXED**. Entscheidung zur C27-Codeübergabe:
**READY_FOR_INDEPENDENT_REVIEW**, ausdrücklich keine PR-Freigabe.
Week 0 bleibt **PARTIAL**, Multicourse-/Multiweek-Rollout **PLANNING_ONLY**;
Produktion, master und weitere Kurse sind nicht freigegeben.

## Baseline und Provenienz

Branch `feat/c27-cs50-learning-pipeline`, HEAD und ursprüngliche Basis
`a8af1d9372eb435d3e1331c33b047d21120d57c2` wurden vor jeder Änderung bestätigt.
Drei versionierte Änderungen und 48 ungetrackte Dateien; keine Stagingänderungen.
Der vollständige Anfangsstatus:

```text
 M .gitignore
 M src/llm/model_litellm.py
 M src/tools_materials/code_zip.py
?? docs/cs50/c27/README.md
?? docs/cs50/c27/architecture_and_components.md
?? docs/cs50/c27/cs50p_component_provenance.v1.json
?? docs/cs50/c27/handoff-files.v1.json
?? docs/cs50/c27/handoff.md
?? docs/cs50/c27/integration_plan.md
?? docs/cs50/c27/real_data_acceptance.v1.json
?? docs/cs50/c27/rollout_plan.md
?? docs/cs50/c27/summarizer_integration.v1.json
?? docs/cs50/c27/test-results/initial-integration.txt
?? docs/cs50/c27/test-results/pipeline-regression.txt
?? docs/cs50/c27/test-results/review-final.txt
?? docs/cs50/c27/test-results/summarizer-final.txt
?? docs/cs50/c27/test_matrix.md
?? docs/cs50/c27/validation.md
?? docs/cs50/c27/validation.v1.json
?? docs/lecture_summary/README.md
?? docs/lecture_summary/architecture.md
?? docs/lecture_summary/example-summary.json
?? docs/lecture_summary/example-summary.md
?? docs/lecture_summary/handoff-files.json
?? docs/lecture_summary/offline-report.json
?? docs/lecture_summary/operations.md
?? docs/lecture_summary/test-results.txt
?? docs/lecture_summary/validation.json
?? docs/lecture_summary/validation.md
?? frontend/pages/G_p0_lecture_summarizer.py
?? lecture_summarizer_app.py
?? scripts/c27_reviewed_week.py
?? scripts/lecture_summary_offline.py
?? src/lecture_summary/__init__.py
?? src/lecture_summary/adapter.py
?? src/lecture_summary/engine.py
?? src/lecture_summary/export.py
?? src/lecture_summary/llm.py
?? src/lecture_summary/models.py
?? src/lecture_summary/reviewed_week.py
?? src/lecture_summary/store.py
?? src/model_materials/acquisition.py
?? src/tools_materials/source_acquisition.py
?? src/tools_materials/text_validation.py
?? tests/fixtures/lecture_summary/catalog.json
?? tests/fixtures/lecture_summary/sources/hello.py
?? tests/fixtures/lecture_summary/sources/notes.txt
?? tests/fixtures/lecture_summary/sources/transcript.json
?? tests/test_c27_reviewed_week.py
?? tests/test_lecture_summary.py
?? tests/test_lecture_summary_ui.py
```

Alle 51 C27-Dateien wurden vor Änderungen mit Bytes, Dateirechten und SHA-256
in `before/` und `baseline-files.json` gesichert. Keine ursprüngliche Datei wurde
entfernt. Die drei versionierten Änderungen und alle bestehenden Testdateien
bleiben gegenüber dieser Baseline bytegleich. Nur neun vorhandene C27-Dateien
wurden gezielt geändert; zwei neue Dateien ergänzen Regressionen und diesen Bericht.

Die vier Auditberichte wurden aus
`/home/OPERATOR/codex-logs/c27rollout/handoff/review-r01/` gelesen und gegen die
ursprünglichen `/tmp/c27-r01-audit-gx04l36x/`-Dateien gehasht: alle vier bytegleich.
`c27_findings.json` SHA-256:
`213516a0ffd87d799be9b2815044c470c12781c0656ec396fdfdcde10e98bec2`.
Der dauerhafte Implementierungspatch unter
`/home/OPERATOR/codex-logs/c27rollout/handoff/implementation/` ist bytegleich zum
ursprünglichen `/tmp/c27-learning-handoff.patch`, SHA-256
`982d44f160a231ded538e7adf62cd62fd1fac460c77816c5b7e67a0e7a33110d`.
Die erfolgreiche Rekonstruktion dieses Patches wird zusätzlich gegen die gesicherte
R02-Ausgangsbaseline geprüft. Belege: `audit-provenance.json`,
`baseline-git.json`, `base-proof.json`, `patch-verification.json`.
Alle fünf PR-Blocker sowie F06–F14 wurden anhand des tatsächlichen Audittexts gelesen.

Vor Änderungen: 97 bestehende Summarizer-/UI-/C27-Tests bestanden. Alle sechs
ursprünglichen Auditproben reproduzierten den Defektzustand. Historische Logs
oder frühere Testzahlen wurden nicht als neue Testausführung ausgegeben.
Die alte Exportprobe hat eine wichtige Grenze: In der tatsächlich vorhandenen
synthetischen Katalogfixture sind die Original-URLs null. Ihre URLprüfung mit
`str(None)` beweist daher allein keinen URLverlust. R02 ergänzt explizite offizielle
URL-/Lizenzfixtures und prüft die tatsächlichen Echtdatenmetadaten.

## Korrekturen und technische Entscheidungen

| Finding | Ergebnis | Dateien und Änderung |
|---|---|---|
| C27-R01-F01 | FIXED | `src/lecture_summary/store.py`, `engine.py`, `scripts/c27_reviewed_week.py`, `frontend/pages/G_p0_lecture_summarizer.py`: sichere Storezugriffe einschließlich Engine, CLI-Exports und UI-Eingabelesen |
| C27-R01-F02 | FIXED | `src/lecture_summary/engine.py`, `models.py`: deterministische Gruppen mit maximal 16 eindeutigen Referenzen |
| C27-R01-F03 | FIXED | `scripts/c27_reviewed_week.py`: Ergebniszustand auswerten, reine Cacheabfrage, reguläre Statusbehandlung |
| C27-R01-F04 | FIXED | `adapter.py`, `models.py`, `export.py`, `store.py`, `reviewed_week.py`, CLI: versionierte Provenienz und eigenständige Exporte einschließlich Review |
| C27-R01-F05 | FIXED | `src/lecture_summary/llm.py`, `engine.py`: nur tatsächlich bekannte Integer-Usage, keine erfundenen Nullwerte oder vollständigen Kosten |

### F01: Storeisolation

Die vorhandenen POSIX-Primitiven `DIR_FLAGS`, `FILE_FLAGS`, `_open_directory`
und `_private` aus `src/content_store/artifacts.py` werden wiederverwendet.
Alle Vorfahren werden ohne Symlink-Following geöffnet. Root, `runs`, einzelne
Run- und Unterverzeichnisse müssen dem aktuellen UID gehören und dürfen keine
Gruppen-/Fremdrechte haben. Bestandsrechte werden nie automatisch repariert.
Root und `runs` werden zusätzlich an ihre Geräte-/Inodeidentität gebunden.
Lockdateien werden relativ zum validierten Root mit `O_NOFOLLOW` geöffnet und
auf privaten regulären Inode und genau einen Hardlink geprüft.

Recovery validiert alle gefundenen Runverzeichnisse und Zustandsdateien vor der
Änderung und hält deren Deskriptoren während der Recovery offen. Ein ungültiges
Ziel bricht den Zugriff ab. Lesen und atomarer temporärer Schreib-/Replacevorgang
verwenden dieselben Verzeichnisdeskriptoren; ein zwischenzeitlicher Pfadtausch
leitet den Schreibzugriff nicht auf ein Symlinkziel um. Engine, Reviewevents,
CLI-Exports und UI-Eingabelesen verwenden die Storemethoden statt nachträglicher
pfadbasierter Dateioperationen. `run_path()` bleibt zur Anzeige/Kompatibilität;
es ist selbst keine Berechtigung für externe Dateioperationen.

Die Tests prüfen Root-/Vorfahr-/runs-/Run-/Lock-/State-/raw-Symlinks, unsichere
Bestandsrechte, fremden UID per Stub, Hardlinks, ausgetauschte Root-/runs-Inodes,
einen gezielt während `os.replace` ausgetauschten Runpfad und sichere Recovery.
Externe Sentinels bleiben bei den Angriffsproben unverändert. Eine Wiederaufnahme
bedeutet hier Recovery plus sicherer neuer Run/Cachewiederverwendung; bezahltes
Abschnitts-Resume aus F12 wurde nicht implementiert.

### F02: Claimgruppen

Exakte Aussagen werden weiterhin nach Kategorie und Text gruppiert. Die Reihenfolge
verschiedener Aussagen folgt ihrem ersten Auftreten; Referenzen werden dedupliziert
und lexikographisch sortiert. Anschließend entstehen aufeinanderfolgende Gruppen
mit höchstens `MAX_CLAIM_REFS=16` Belegen und daraus deterministisch berechneten
Claim-IDs. Kein ungültiges Zwischen-Claim und kein Verlust zusätzlicher Belege.
Das Topic des ersten Vorkommens bleibt wie bisher maßgeblich.

Grenzfälle: 1, 16, 17, 24 und 32 unterschiedliche Belege, doppelte Belege,
unterschiedliche Aussagen und wiederholte Verarbeitung. 32 prüft die existierende
absolute Chunkobergrenze direkt in der Konsolidierung. Die E2E-Proben mit 17 und
24 Chunks verwenden unveränderte Standardlimits und genau einen Fakeaufruf je
Chunk. Es gibt keinen zusätzlichen Modellaufruf für die Konsolidierung.

### F03: reguläres needs_attention

Nach der Generierung wird der Erstlaufstatus ausgewertet. Nur `ready_for_review`
führt zur lesenden `store.cached()`-Prüfung. Auch dieser Fall generiert nicht erneut.
`needs_attention` bleibt ein reguläres, exportierbares Ergebnis mit
`cache_verified=false`. Bei unerwartet fehlendem Cacheeintrag bleibt die Prüfung
false und ein expliziter `cache_verification_error` wird berichtet. Die frühere
Laufzeitzustands-Assertion entfällt. Unabhängige Units werden weiterverarbeitet.
Ein erneuter expliziter CLI-Aufruf darf ein nicht cachefähiges Ergebnis neu
berechnen; es gibt keinen zweiten Lauf allein zur Cacheprüfung.

Getestet: Cacheerfolg, verworfener Claim, Uncertainty, der ursprüngliche defekte
`print(`-Text mit korrekt angepasstem Rohdatenhash, fehlerhafte Eingabe,
zwei unabhängige Units, Wiederholung und unerwarteter Cachemiss.

### F04: exportierbare Provenienz und Kompatibilität

Vorhandene Metadaten aus `resource.source_url`, `resource.license` und
`resource.title` werden zusammen mit optionaler Materialattribution in die
versionierte `SourceProvenance` jeder `SourceRef` übernommen. Die bestehende
LectureResource besitzt kein Attributionsfeld; deshalb wird ein optionales
`Material.attribution` ergänzt und das tatsächliche optionale
Downloadberichtsfeld durchgereicht. Fehlende Werte bleiben null; ein Titel wird
nicht zu einer erfundenen Attribution umgedeutet.

Katalog und SummaryResult verwenden Schema 2, die enthaltene Provenienz Schema 1.
Explizite v1-Daten werden kontrolliert im Speicher auf Schema 2 übernommen;
fehlende alte Provenienz bleibt unbekannt. Unbekannte zukünftige Schemaversionen
werden abgelehnt. Gespeicherte Originalbytes und ihre Hash-/Reviewbindung werden
beim Lesen nicht umgeschrieben. Der Cacheinput bindet zusätzlich die neue
Ergebnisschemaversion; alte Metadatenverluste werden nicht als neues Ergebnis
wiederverwendet. Eine echte gespeicherte v1-Beispielfixture wird geladen, unverändert
beibehalten, erneut exportiert und mit einem neuen gebundenen Review getestet.

Markdown und JSON erhalten Quellen-/Materialidentitäten, Originalhashes und
vollständige Content-Locators, Original-URL soweit zulässig, Lizenz, Attribution,
Titel, Ergebnis- und Reviewstatus. JSON wird im bisherigen Store-Envelope um
`export_schema_version=2` und `review_status` ergänzt. Die C27-CLI verwendet nun
auch dieses Envelope; ein Verbraucher des bisherigen nackten CLI-Exportresultats
muss den Schlüssel `result` lesen. Dies ist eine explizite F04-Vertragsänderung.
Die JSON-Resultathülle lässt sich erneut als SummaryResult einlesen; ein
Markdown-Import ist nicht implementiert und wird nicht behauptet.

Die CLI erhält nach einem Review ältere Exporte und legt einen neuen
`export-review-<review_id>.md/.json`-Snapshot an. Der Unitbericht benennt die
konkreten Exportdateien. Damit ist auch ein wiederholter gecachter CLI-Aufruf nach
einem Review möglich, ohne alte Exporte zu überschreiben oder Reviewstatus zu verlieren.

Die Offline-URLregel baut auf `public_url` auf: nur HTTP(S), keine Zugangsdaten,
Query, Fragmente, Kontrollzeichen, überlange URLs; zusätzlich keine Leerzeichen,
Backslashes, lokalen Hostnamen/privaten IPs oder erkennbaren Token-/Secret-/Session-
Pfadbestandteile. Unsichere URLs werden vollständig zurückgehalten, nicht durch
eine erfundene bereinigte Originalquelle ersetzt; der Status ist `withheld`.
Die unveränderte Originalmetadatenaufnahme bleibt im privaten Inputbestand.
Das ist eine konservative syntaktische Regel ohne DNS-, Netz- oder Lizenzprüfung;
opaque Geheimnisse in beliebigem Pfad-/Freitext erfordern weiterhin ein
Operatorreview vor einer tatsächlichen Veröffentlichung.

### F05: unbekannte Usage

Der LiteLLM-Adapter übernimmt jedes Feld einzeln nur bei `type(value) is int`
und `value >= 0`. Fehlende Werte, None, negative Werte, Strings, Floats und bool
bleiben unbekannt; echte 0 bleibt bekannt. Attribut- und Mapping-Usage werden mit
SDK-Stubs getestet. Kein echter Provider wird dafür importiert/aufgerufen.

Die Engine aggregiert bekannte Teilmengen als `known_input_tokens` und
`known_output_tokens` und zählt pro Richtung die fehlenden Aufrufe.
`input_tokens` bzw. `output_tokens` erscheinen nur, wenn der Gesamtverbrauch der
jeweiligen Richtung bekannt ist. `usage_missing_calls` bleibt für bestehende
Verbrauchs-/Kostenentscheidungen erhalten; bei unbekannter Usage bleiben die
vollständigen Kosten null/None. Der Usage-Datentyp bleibt `dict[str, int]`;
Verbraucher dürfen bei partiellen Daten keine fehlenden Gesamtschlüssel durch
nachgewiesene Nullwerte ersetzen. Retries/fehlgeschlagene Calls bleiben in der
Unbekanntzählung. Preise und Laufzeit-/Budgetlimits wurden nicht erhöht.
Historische gespeicherte falsche Verbrauchswerte werden nicht nachträglich erfunden
oder aus unbekannten Providerdaten rekonstruiert.

## Validierung

Bestehende zusammengesetzte Offlineumgebung `/tmp/c27-test-env/bin/python`,
Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4, Ruff 0.16.3, Mypy 2.3.1.
Die vorhandene `.pth` liest installierte Paketbestände der Haupt-, DEP01- und
UI-Umgebung; keine Installation und keine Änderung dieser Umgebungen.
LiteLLM/Instructor sind nicht installiert; die SDK-Verträge verwenden ausschließlich
Stubs. `environment.json` enthält die tatsächlich ermittelten Versionen.

Alle pytest-Aufrufe verwenden `PYTHONDONTWRITEBYTECODE=1`,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-p tests.offline_guard -p no:cacheprovider`
und einen eigenen neuen `--basetemp` im privaten R02-Verzeichnis. Die exakten
Argumentlisten stehen jeweils in `<Laufname>-command.json`, die vollständigen
Ausgaben in `<Laufname>.txt`. Bei Reproduktion neue temporäre Pfade wählen;
niemals die erhaltene Evidenz als pytest-basetemp verwenden.

| Lauf / Befehl hinter den gemeinsamen pytest-Optionen | Ergebnis | Daten / Modell |
|---|---|---|
| `baseline-summary`: `tests/test_lecture_summary.py tests/test_lecture_summary_ui.py tests/test_c27_reviewed_week.py --run-external` | 97 bestanden | Fixtures und lesende lokale Echtdaten; Fake/SDK-Stub |
| `baseline-probes`: unveränderte R01-`audit-probes.py -s` | 6 Defekte reproduziert | synthetisch; Fake/Stub |
| `acceptance`: dieselben drei Dateien plus `tests/test_c27_remediation_r02.py --run-external` | 168 bestanden, 0 fehlgeschlagen, 0 übersprungen | 71 neue Fälle plus 97 bestehende; vor letztem CLI-Reviewsnapshot-Test |
| `cli-final`: `tests/test_c27_remediation_r02.py tests/test_c27_reviewed_week.py --run-external` | 108 bestanden, 0 fehlgeschlagen, 0 übersprungen | 72 R02-Regressionen einschließlich zusätzlichem Reviewsnapshot-Test, 36 C27-Fälle |
| `frozen-summary`: vier Dateien wie `acceptance` | 169 bestanden, 0 fehlgeschlagen, 0 übersprungen | finaler Code; Fake/Stub, Echtdaten nur gelesen |
| `pipeline`: zwölf unveränderte Dateien aus R01-`pipeline-command.json` | 378 bestanden, 2 übersprungen, 0 fehlgeschlagen; erwartete ZIP-Duplikatwarnung | überwiegend synthetisch/MockTransport; kein LLM |
| `real-isolation`: eigene Kopien der R01-`real-probes.py` und `isolation-probes.py -s` | 3 bestanden, 0 fehlgeschlagen | echte lokale Rohbytes plus synthetische Scopeisolation; Fake |
| `post-original-probes`: unveränderte R01-`audit-probes.py -s` | 5 erwartete Fehlassertionen, 1 weiterhin reproduzierter F06 | alte Defektcharakterisierungen erwarten absichtlich das falsche Verhalten |
| Ruff `check --no-cache` auf 21 C27-/Summarizer-/UI-/Testdateien | bestanden | `static-checks.json`, `ruff.txt` |
| Ruff `format --no-cache --check` auf denselben Dateien | 21 bereits formatiert | `format.txt` |
| `git diff --check` | bestanden | kein Whitespacefehler in versionierten Änderungen |
| Mypy `--follow-imports=silent --cache-dir <isoliert> src/lecture_summary scripts/c27_reviewed_week.py` | nicht grün: Baseline 170, R02 134 Diagnosen, jeweils 8/9 Dateien | strict aus Projektkonfiguration; `mypy-baseline.txt`, `mypy-final.txt` |

Keine Addition überlappender Testgruppen. Die zwei Pipeline-Skips betreffen die
optionale echte Notes-HTML-/Operator-Exportmatrix. Die R01-Probenwarnung zum
external_integration-Marker entsteht im eigenständigen temporären Testroot.
Die fünf alten Defektassertionen sind keine fünf neuen Regressionen: 17 Belege
funktionieren, der unsichere Store wird abgelehnt, die Exportstruktur trägt
Provenienz, partielle Usage ist unbekannt und die CLI bricht nicht mehr ab.
Die positiven R02-Assertions prüfen jeweils das gewünschte Verhalten.

Der Offline-E2E über `scripts.lecture_summary_offline.run` ist im bestehenden
Summarizertest enthalten: Fixture → Fake → belegte Claims → Review → Cache → beide
Exporte. Der separate Functions-Lauf bestätigt unverändert 18 Sections/18 Claims,
Cache ohne neue Fakeaufrufe und beide vollständigen HTML-Auswahlen als am
Standard-Chunklimit blockiert. Alle 17 Roh-/Reviewdateien bleiben in Dateiliste,
SHA-256, Größe und Rechten identisch mit R01 und dem R02-Snapshot. Echtdaten-
Original-URLs und Lizenzstrings stehen nun auch in den Ergebnisreferenzen.

Mypy ist keine bestandene Typabnahme. Ein erheblicher Teil der vorhandenen C27-
Implementierung ist untypisiert; außerdem bestehen bereits Modell-/Tuple- und
Legacy-Vertragsdiagnosen. Die neuen Store-/Migrations-/Konsolidierungsgrenzen
wurden annotiert, ohne globale Prüflimits zu lockern. Verbleibende Diagnosen,
auch Aufrufe bestehender untypisierter Sicherheitshelfer, sind offen dokumentiert.
Nicht durchgeführt: echte Provider-/Netz-/Browser-/Produktionsprüfung oder
fachlicher Review. Es gab keine Downloads, keine ZIP-Codeausführung und keine
neuen Pakete.

## Übergabe und Nachvollziehbarkeit

Exklusiv mit `mkdtemp` erzeugter privater Artefaktroot (0700):
`/tmp/c27-r02-handoff-jssou_yj/`. Er liegt außerhalb des Repositorys und innerhalb
der erlaubten Schreibpfade. Vorhandene Übergaben wurden nicht überschrieben.
Dieser externe Speicher ist temporär; eine dauerhafte Ablage außerhalb der hier
erlaubten Schreibpfade und die spätere Default-Branch-Integration bleiben offen.

- `c27-full-vs-a8af1d9.patch`: vollständiger Stand aller 53 C27-Pfade gegen die ursprüngliche Basis, einschließlich der 51 ursprünglichen Dateien und R02.
- `c27-r02-only.patch`: ausschließlich R02 gegen die vor Änderungen gesicherte uncommittete Baseline; zusammen mit dem belegten Originalpatch aufbaubar.
- Je Patch `.sha256`, zusätzlich `SHA256SUMS`.
- `file-manifest.json`: alle Pfade mit Bytes, SHA-256, Rechten und R02-Klassifikation.
- `r02-changes.json`: genau neun geänderte Bestandsdateien plus neue Tests und dieser Bericht mit Vorher-/Nachherhashes.
- `base-proof.json`: Commitobjekt selbst als Git-Commit erneut gehasht, Branch und HEAD sowie Commitdetails.
- `patch-verification.json`: Vorwärts-Check/Anwendung beider Patches; Bytevergleich jedes resultierenden Pfads; Rückwärts-Check und tatsächliche Rückwärtsanwendung gegen komplette Export-Snapshots.
- `before/`, `after/`, Testlogs und Befehle: konkrete unveränderte Ausgangsdaten und reviewbarer Endstand.

Beide Vorwärtsprüfungen und tatsächlichen Anwendungen sowie beide Rückwärtsprüfungen
und tatsächlichen Rückwärtsanwendungen sind erfolgreich. Der Gesamtpatch rekonstruiert
alle 53 Dateipfade bytegleich zum Arbeitsstand. Die Kombination aus Originalpatch
und R02-Delta rekonstruiert denselben Endstand ebenfalls bytegleich. Der Rückweg
stellt jeweils den vollständigen Basis- beziehungsweise R01-Snapshot wieder her.
Git-Archivdateien werden im isolierten Prüfharness auf die von Git darstellbaren
Dateimodi 0644/0755 normalisiert: `git archive` liefert hier 0664, dessen Gruppen-
Schreibbit ein Patch nicht transportiert. Die erste Rückwärtsprobe hatte ausschließlich
diese drei Modusunterschiede bei bereits identischen Bytes; es war eine Erwartung
des Prüfharness, kein Produktdefekt. Das Dateimanifest erfasst unabhängig davon
die tatsächlichen Rechte im Arbeitsstand.
Die SHA-256-Werte stehen außerhalb des Patches in den Prüfsummendateien, um
eine zirkuläre Selbstreferenz dieses Berichts zu vermeiden.

Die historischen Manifeste unter `docs/cs50/c27/handoff-files.v1.json` und
`docs/lecture_summary/handoff-files.json` bleiben historische R01-/Implementierungs-
Evidenz und wurden nicht überschrieben. Für den R02-Endstand gilt ausschließlich
das neue externe Dateimanifest. Auch frühere Abnahmeberichte bleiben erhalten.

## Offene Findings, Risiken und unabhängiger Re-Review

F06–F14 bleiben außerhalb des Implementierungsscopes: F06 Katalog-/UI-Lücken,
F07 dauerhafter Lifecycle, F08 segmentierte HTML-Verarbeitung, F09 ZIP-Quellenmapping,
F10 vollständige Week-0-Abdeckung, F11 Fachreview/echter Providerpilot,
F12 persistentes Budget und bezahltes Resume, F13 CS50x-/Web-Testmatrix,
F14 separates Produktionsgate. Kein neues Gate wurde eigenständig freigegeben.

F01 basiert auf den bereits im Projekt verwendeten POSIX-/Linux-Primitiven;
ein Windowsfallback wird nicht behauptet. Private Rechte isolieren keine
böswilligen Prozesse desselben UID oder privilegierte Mount-/Dateisystemeingriffe.
Die TOCTOU-Probe belegt die konkrete Descriptorbindung gegen den Pfad-/Symlinktausch,
keine allgemeine Sandbox gegenüber einem vollständig kompromittierten Benutzerkonto.
Große Historien halten während Recovery mehrere Deskriptoren offen und sollten
vor einem breiten Betrieb separat auf Ressourcenbedarf geprüft werden.

Der unabhängige Re-Review sollte insbesondere die kompletten F01-Zugriffsketten
und zeitlich variierten Symlink-/Inodetausch, die 16/17/32-Beleggrenzen, echte
needs_attention-Unitfortsetzung, Schema-v1-/Reviewhashkompatibilität, die konservative
URLregel einschließlich kodierter Sonderformen sowie partielle Provider-Usage
und Retryzählung erneut unabhängig prüfen. Die gesicherten realen Metadaten sind
als zusätzliche Exportprobe geeignet. Ein echter SDK-/Providerpilot bleibt separat
zu autorisieren; das technische Offlineergebnis ersetzt kein Fachreview.

C27-R02 Teststatus: **Offline-Regressionen und Ruff bestanden; strikter Typcheck
weiterhin offen**. C27-Integration: **READY_FOR_INDEPENDENT_REVIEW**.
Week 0: **PARTIAL**. Rollout: **PLANNING_ONLY**. Produktionsfreigabe: **keine**.

Es wurden keine Commits, neuen Branches, Git-Worktrees, Pushes, PRs, Merges,
Rebases, Cherry-Picks, Resets oder Deployments erzeugt. Die vorhandenen Branch-/
Worktree-Artefakte bleiben erhalten. Die allgemeine AGENTS-Lifecycle-Vorgabe zur
Integration in master ist wegen des ausdrücklichen R02-Verbots nicht ausführbar;
Dokumentintegration und regulärer Lifecycleabschluss bleiben deshalb **pending**.
Es gibt keine task-eigenen temporären Git-Artefakte zu löschen. Die neuen privaten
Übergabe-/Testartefakte bleiben zur Beweisführung erhalten.
