# C27 Stage-0 Review v2 – Final Manifest and Patch Binding

**GO_FOR_COMMIT_REVIEW**, ausschließlich für die Integritätsprüfung dieser
Review-Revision. Datum: 2026-11-05. Kein Commit, keine Integration und keine
Produkt-, Host-, Deployment- oder semantische Abnahme. B1 bleibt offen; das
historische diagnostische HOLD wird dadurch nicht aufgehoben.

## Festgelegter Kandidat und unveränderter Index

REVIEW: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c27-stage0-review`.
SOURCE: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-server-runtime`.
Branch: `review/c27-stage0-20261105`.
HEAD und Patchbasis: `a8af1d9372eb435d3e1331c33b047d21120d57c2`.
AGENTS.md und .pre-commit-config.yaml wurden gelesen. Es wurden weder der Index
noch die sechs Produktdateien verändert; die zwei EOF-Korrekturen waren bereits
im vorgefundenen Index enthalten. Keine automatische Formatierung.

| Stage-0-Datei | Status | v1 → v2 Bytes | Bytevergleich |
| --- | --- | --- | --- |
| deployment/cs50p-download-only/runtime/requirements.txt | neu | 5677 → 5677 | identisch |
| src/model_materials/acquisition.py | neu | 5793 → 5792 | genau ein letztes LF entfernt |
| src/tools_materials/code_zip.py | geändert | 8757 → 8757 | identisch |
| src/tools_materials/source_acquisition.py | neu | 1203 → 1202 | genau ein letztes LF entfernt |
| src/tools_materials/storage.py | geändert | 3028 → 3028 | identisch |
| src/tools_materials/text_validation.py | neu | 1831 → 1831 | identisch |

Für beide korrigierten Dateien gilt bytegenau `v2 == v1[:-1]`: v1 endet auf
`0a 0a`, v2 auf genau einem `0a`. Alle anderen Bytes bleiben erhalten. Das
v1-Endprodukt wurde durch Anwendung des hashgeprüften alten Patches auf ein
frisches Archiv der Basis rekonstruiert, nicht aus den umfangreicheren
SOURCE-Produktdateien übernommen. Alle sechs v1-Endhashes und Dateigrößen wurden
gegen v1-Manifest und alte Matrix geprüft. Es gibt keine zusätzliche Änderung
im gestagten Produktdiff. Neue Produktlogik gegenüber dem getesteten v1: keine.

## Patch und Manifest

[stage0-v2.patch](stage0-v2.patch) stammt unmittelbar aus dem tatsächlichen
Git-Index mittels `git diff --cached --binary --full-index --no-ext-diff
--no-textconv --no-renames` gegen den Basiscommit. Sechs Dateien, vier neue,
zwei geänderte, **362 Einfügungen / 3 Löschungen**. Keine Stage-1-Datei und kein
Test oder Review-Dokument im Produktpatch. Patchgröße: **19193 Bytes**. Die
v2-Patchmetadaten verwenden volle Git-Objektkennungen; der historische v1-Patch
verwendet gekürzte Kennungen. Der Größenunterschied der Patchdateien ist deshalb
nicht allein die Entfernung von zwei LF. Die sechs resultierenden Produktdateien
unterscheiden sich ausschließlich um diese zwei LF.

- Patch v2 SHA-256: `1118f91decd6531a91986ef3cf1dbacf596a88a3f6d5fad6e4b8369a864b0c13`
- Manifest v2 SHA-256: `c56a5258c9ec750fa6a56b123c0bc83ded655eef8d2b4ca4dca8f2e1697f7450`
- acquisition.py v2: `0e333b8f2d29a320e991b50ba363cf4d88372d18f6f55529cbc73fd96f1120c5`
- source_acquisition.py v2: `439024312a82bb944c5be81190adfe54b7f835acdf49812fe11ce16fce451ec1`

[candidate-manifest-v2.json](candidate-manifest-v2.json) hat das eigenständige
Schema `c27-minimal-stage0-candidate-v2`. `stage0.files` enthält den
maschinenlesbaren Vergleich aller sechs alten und neuen Endhashes, Größen,
Basis-/Quellhashes und entfernten LF. Die 40 unveränderten Voraussetzungen
einschließlich der drei kompatiblen Basisdateien sind getrennt gebunden.
Die beiden zurückgestellten Profilpfade müssen weiterhin fehlen.
`stage1` bindet separat genau die 55 unveränderten Quellpfade samt SHA-256.
`history` bindet v1, ältere Provenienznachweise, Archive und den alten Prüfer.

Der neue Prüfer pinnt den Digest des v2-Manifests. Er ersetzt keinen alten Test
und verändert keine historischen Sollwerte. Die zwei unveränderten reinen
v1-Prüffunktionen wurden aus dem hashgeprüften historischen Test per AST geladen:
Sie akzeptieren einen vollständigen v1-Vertragsfixture, lehnen dessen Austausch
der zwei Module durch v2 beim Hash von acquisition.py ab und lehnen das neue
Manifest an ihrem alten Digest ab. Dies ist eine begrenzte Vertragsprüfung,
kein erneuter Lauf der historischen Pytest-Suite.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Branch, HEAD, sechs exakte Indexpfade, 4 A / 2 M, 362 / 3 | PASS |
| Keine ungestagten Änderungen an vorhandenen getrackten Dateien | PASS |
| `git diff --cached --check`, vor und nach der Arbeit | PASS |
| Offline Ruff 0.16.0 `format --check`, fünf Produktmodule | PASS |
| Neue Testdatei: Ruff-Formatprüfung nach manueller Zeilenkorrektur | PASS |
| Python-3.12-Syntaxprüfung der fünf Module und des neuen Tests im Speicher | PASS |
| Historische v1-Patch-/Manifestdigests und sechs rekonstruierte v1-Endhashes | PASS |
| Genau zwei EOF-LF entfernt, vier andere Dateien bytegleich | PASS |
| Patch v2: `git apply --check --whitespace=error` auf frischer Basis | PASS |
| Tatsächliche Anwendung und alle sechs Endhashes | PASS |
| Vergleich aller 1132 Basisdateien: nur zwei geändert, vier neu | PASS |
| Neue unabhängige Integritätstests: 15 Tests, 86 Unterfälle | PASS, keine Skips |
| Alle 55 Stage-1-Hashes und negative Driftfälle im getrennten Kombinationsbaum | PASS |
| 190 vor/nach inventarisierte SOURCE-Dateien einschließlich Nachweisen und Archiven | unverändert |
| Indexdatei, Indexdiff, Produktbytes, Shared-Refs und Worktree-Registrierungen | unverändert |

Die neuen Tests decken den positiven Stage-0-Vertrag ohne Stage 1, alle sechs
Endhashes, fehlende und manipulierte Dateien, Datei-/Elternsymlinks,
Manifestdrift, beide fehlenden Profilpfade einschließlich gebrochener Symlinks,
die drei kompatiblen master-Dateien und alle 55 Stage-1-Quellhashes ab.
Stage-1-Prüfungen liefen nur in isolierten temporären Kombinationsfixtures;
SOURCE wurde dafür ausschließlich gelesen. Getestet wurde mit vorhandener
Offline-CPython-3.12.12-Installation und Standardbibliothek, ohne Downloads,
Paketinstallation, Paketauflösung oder Produktimporte.

Beim ersten Formatcheck der neu geschriebenen Testdatei wurden lediglich
Zeilenumbrüche beanstandet und manuell korrigiert. Das ist kein Produktbefund.
Die optionalen historischen Harnessdateien `tests/test_stage0_boundaries.py`
und `tests/test_b1_sqlite_diagnostics.py` liegen in SOURCE nicht vor; der erste
Vorbereitungsversuch stoppte bei ihrer Inventarisierung vor dem Schreiben von
Review-Dateien. Diese beiden historischen Harnesses wurden **NOT_RUN**.
Alle für den neuen Vertrag erforderlichen Inputs waren lokal verfügbar.

Vollständige C27-, Stage-0-Funktions-, B1- und Host-/Semantik-Suites wurden in
diesem Auftrag **NOT_RUN**. Die früher gemeldeten 289 Stage-0- und 285 kombinierten
C27-Fälle sind ausschließlich historische Evidenz aus dem unveränderten
SOURCE-Bericht `validation-resolution-20261105/assessment.md`; keine Aussage
über einen neuen Lauf dieser Fälle auf v2. Details und einzelne neue Testfälle:
[integrity-results.json](integrity-results.json).

## Historie, Restrisiken und Integration

V1 bleibt historisch bytegleich:

- Stage-0-Patch v1: `cf8b48eb84658f075aba3fab54e85cb4c936b79fd9bda1c89a19d55c382992ca`
- Kandidatenmanifest v1: `3b0fdf04072c193f25858b8299ac397a1acef8e643c98189fcdda2b5e60e40bb`

**B1 bleibt als Restrisiko offen:** tatsächlicher Auslöser und Lockhalter des
sporadischen SQLite-Locks sind weiterhin ungeklärt. Es wird kein Produktfix und
keine diagnostische Aufhebung des historischen HOLD behauptet. **B2 wurde durch
einen getrennten Kandidatenvertrag behandelt**; v2 macht nur die zwei bereits
vorliegenden EOF-Abweichungen zusätzlich explizit.

Stage 0 ist noch nicht in master integriert. Der lokal vorhandene master steht
auf `c1007efdbac3c1544020f328a3a1347e481797ba`; die vier neuen Stage-0-Pfade fehlen
dort. Kein Fetch/Pull und keine Live-Abfrage; kein aktueller Remotezustand wird
behauptet. Stage 1 bleibt ein separater Integrationsschritt. Keine Host- oder
semantische Abnahme wird behauptet.

Die vorgefundene SOURCE-Änderung an `tests/test_cs50_six_courses.py` blieb
erhalten; ihr Diff und tatsächliche Bytes wurden vor/nach gebunden. Nicht alle
SOURCE-Produktdateien entsprechen absichtlich dem gekürzten Kandidaten.
Die Aussage zu unveränderten historischen Nachweisen bezieht sich auf die
190 explizit inventarisierten Dateien sowie unveränderte getrackte Diffs;
kein pauschaler erneuter funktionaler Provenienztest wird behauptet.

Alle neuen dauerhaften Repositorydateien liegen ausschließlich in diesem Review-Verzeichnis
und bleiben ungestagt. JSON- und gegebenenfalls weitere Dateien werden von
vorhandenen Ignore-Regeln ausgeblendet; keine .gitignore wurde verändert.
`SHA256SUMS` bindet alle sechs übrigen neuen Paketdateien einschließlich des
Tests, ohne sich selbst zu hashen. Sein Digest steht separat im Abschlussbericht.

Die anfänglichen Ruff-Prüfungen benutzten den vorhandenen ignorierten
`.ruff_cache` und erzeugten bzw. aktualisierten dort Formatprüfungs-Cachedaten.
Diese disponiblen Tooldaten sind keine Produkt-/Reviewquellen. Sie wurden weder
als Produktänderung gestagt noch bereinigt; eine unveränderte Cachehistorie wird
nicht behauptet. Die abschließende Ruff-Prüfung lief mit `--no-cache`.

Keine Commits, Pushes, PRs, Merges, Fetches, Pulls, Indexschreiboperationen,
Resets, Clean- oder Stashoperationen. Keine Branches oder registrierten Worktrees
erzeugt, geändert oder entfernt. Der vorbestehende Review-Branch und Worktree
bleiben wegen ausdrücklichem Integrationsverbot und offenem Review erhalten.
Die laut AGENTS.md spätere Integration der dauerhaften Nachweise in master
bleibt aus demselben Grund ausstehend; kein abgeschlossener Integrations- oder
Cleanup-Lifecycle wird behauptet.

Temporäre Auditbäume und Helfer bleiben für Nachprüfung erhalten:
`/tmp/c27-review-v2-20261105-ap_c1jer` (v1, v2, Kombination, Ergebnisse, Fixtures),
`/tmp/c27-review-v2-20261105-mo4t2ux4` (früh gestoppte Vorbereitung) sowie
`/tmp/c27_review_v2_prepare.py` und `/tmp/c27_review_v2_finish.py`.
Dies sind keine registrierten Git-Worktrees. Keine Bestands-/MAINT-Artefakte
wurden bereinigt. Das [Runbook](review-runbook.md) beschreibt die Wiederholung.
