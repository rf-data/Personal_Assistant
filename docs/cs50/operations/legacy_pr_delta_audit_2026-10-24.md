# C26 – Delta-Audit der historischen PRs #6, #9 und #11

Stand: 24.10.2026. Ergebnis: **#6 CLOSE, #9 CLOSE, #11 CLOSE**. Das sind
Empfehlungen zur späteren manuellen Entscheidung; kein PR wurde geschlossen,
gemergt, neu ausgerichtet oder anderweitig verändert. Es fehlt keine der
ursprünglich beauftragten Verhaltensänderungen. Ein generiertes JSON-Beispiel
aus #9 ist als Datei nicht übernommen, aber durch ausführbare Import-/Roundtrip-
Tests funktional ersetzt. Deshalb kein Code-PATCH und kein REWORK der alten Branches.

## Prüfstand und ursprüngliche Änderungen

Verglichen wurde der tatsächlich aktuelle GitHub-`master`
**`29114d2e2877cee9c434f620da852313963e3a01`**, Baum
`75ced605ec198476e0ebf3cb83cc6a3b282b9290`. Der bisher lokale Trackingstand
`e502aa9` war veraltet und wurde nicht als aktueller Master ausgegeben.

| PR | Unveränderter Head | Merge-Base mit geprüftem master | Ursprünglicher Umfang |
|---|---|---|---|
| [#6](https://github.com/rf-data/Personal_Assistant/pull/6) | `7ba2dd844d24377eba36ca98b64ea4c2e059cf62` | `d72a96af4261f91e4358500c8a03c9b427a0c956` | 5 Commits, 32 Dateien; initiale Verträge plus inzwischen in den Branch gemergte #7/#8 |
| [#9](https://github.com/rf-data/Personal_Assistant/pull/9) | `3d1317347018fce47f49331fbfea92e4a055a337` | derselbe Merge-Base | 1 Commit, 7 Dateien |
| [#11](https://github.com/rf-data/Personal_Assistant/pull/11) | `efed68d08ddbd25a7d0404a164cf6d54ce334ab6` | derselbe Merge-Base | 1 Commit, 3 Dateien |

Die drei PR-Heads sind **keine Git-Vorfahren** des aktuellen Masters. Der
GitHub-Vergleich meldet jeweils 256 Master-Commits seit dem gemeinsamen Vorfahren;
#6 hat fünf eigene Commits, #9/#11 je einen. Fehlende Ancestry ist hier kein
Nachweis fehlender Funktion: Code/Testinhalte wurden unter anderen Commit-IDs
übernommen und anschließend erweitert.

Die fünf Originalcommits von #6 in topologischer Reihenfolge:

1. `bb91b33ef938dd74e5d5debc4538426d0e851c08` – Fixturevalidierung/Discovery-Verträge.
2. `2a4261f66d26fe8be20548b46189f2e6d71b8bac` – Offline-Extraktion von Navigation/Wochen.
3. `cea19d35d771c831e4a60a60ad8efb65a1586c7f` – konfigurierbare Offline-Auswahl/Vorschau.
4. `0f62cb53edf5bf22f4b21c7d5e29379df0e4f508` – Merge von #8 in den Featurebranch.
5. `7ba2dd844d24377eba36ca98b64ea4c2e059cf62` – Merge von #7 in den Featurebranch.

Bei #9 und #11 ist der jeweilige Head selbst der einzige ursprüngliche Commit.
Die PR-Beschreibung von #6 allein beschreibt nicht mehr den ganzen heutigen Head:
Parser und Selection gehören durch die beiden verschachtelten PRs dazu.

Wichtige Integrationsanker in der tatsächlichen Masterhistorie:

- `b2e4b2fee309e5a7b9cd49dc4639db7ccd5b8cc5`: Discovery-/Selection-/Manifest- und
  Importermodule sowie der echte Consolidation-Importtest vorhanden.
- `bd5491e63966f5bb3d53593f06604dcadf5bfc98`: der konkrete Importwechsel von
  `text_helper` zu `latex_helper` ist im Patch nachweisbar; zusätzliche Source-ID-
  Prüfung und Metadatenweitergabe bleiben erhalten.
- `2e60d1529793bfb329a3648502cb26b589474c19` (C23-05): Nullablezeiten,
  Intervallvalidierung, Texttreue und Verbraucher-/Chunking-Guards schließen den
  im älteren historischen PR-Review noch offenen TXT-Rest.
- `4241438`: spätere konservative Konsolidierungs-/Evidenzhärtung. Sie darf
  durch Übernahme des alten Consolidation-Moduls nicht verloren gehen.

## #11 – normalize_math_text und echter Regressionstest

| Ursprüngliche Anforderung | Stand im PR | Stand in master | Fehlende Funktionalität | Risiko einer Übernahme | Empfohlene Aktion |
|---|---|---|---|---|---|
| Richtiger Import von `normalize_math_text` | Import aus `src.utils.latex_helper` statt `text_helper` | **Vollständig übernommen**; realer Import aus `latex_helper`, inzwischen ohne frühere App-/I/O-Imports im Consolidation-Modul | Keine | Ganze alte Datei würde spätere Identitäts-/Evidenz-/Konsolidierungsregeln zurücksetzen | CLOSE; Import nicht erneut patchen |
| Echter Modulimport in frischem Prozess | `test_consolidation_math_import.py`, `-I`, reale Pydantic-Modelle und reale Helper | **Funktional vollständig erhalten**: Helperidentität, delegierter Aufrufzähler, eine Formel mit beiden Evidenzen und erhaltene Source-ID; Test bestanden | Keine | Alter Socket-Funktionsersatz ist gegenüber dem heutigen Guard unnötig; alte Test-/Appannahmen nicht zurückkopieren | Bestehenden echten Test behalten |
| Offline-Isolation | Ersetzt ausschließlich App-/Logger-/I/O-Importmodule, verbietet Netzwerk/SDKs | Aktueller Test blockiert `connect`, `connect_ex`, `create_connection` und DNS; Marvin/OpenAI/Whisper dürfen nicht geladen sein | Keine | Ein AST-only-Test wäre schwächer; aktueller Test bleibt ausdrücklich ein ganzer Modulimport | CLOSE |
| Implementierungs-/Importbericht | `docs/course_sources/cs50/math_normalization_import_fix.md` | **100 % erhalten**, verschoben nach `docs/cs50/archive/2026-10/math_normalization_import_fix.md`; dort historischer Kontext | Keine | Historischen Hinweis auf fehlende App-Abhängigkeiten nicht als neuen Masterfehler ausgeben | Archivpfad zitieren, keine Duplikatdatei |

**Empfehlung: CLOSE.** Die konkrete Korrektur einschließlich des gewünschten
Regressionstests ist vorhanden und getestet. `normalize_math_text` und ein
bestandener syntaktischer Test beweisen weiterhin keine mathematische Wahrheit.
Für C27 bleiben Quellenbeleg und Formelqualitätsstatus gesondert erforderlich.

## #9 – offizielle TXT-/SRT-/VTT-Transkripte

| Ursprüngliche Anforderung | Stand im PR | Stand in master | Fehlende Funktionalität | Risiko einer Übernahme | Empfohlene Aktion |
|---|---|---|---|---|---|
| Lokale TXT-/SRT-/VTT-Importer ohne Whisper | `import_transcript`, drei Formatwrapper; UTF-8/BOM, explizites Encoding, fehlerhafte/leere Eingaben ablehnen | **Vollständig übernommen und erweitert**; zusätzlich NUL-Abweisung und optional explizit erhaltene leere Subtitle-Cues | Keine im PR-Scope | Alte Datei entfernt spätere Encoding-/Cue-Verträge | CLOSE |
| Quellreihenfolge, Mehrzeiligkeit, Wiederholungen | Cuezeiten und Wiederholungen erhalten, keine Overlap-Deduplikation | **Übernommen**; 39 Importfälle bestehen. TXT erhält inzwischen auch Randspaces, Leerzeilen und gesamten normalisierten Dokumenttext | Keine | PR-TXT-`strip()`/erneutes Zusammenfügen würde neuere Texttreue verschlechtern | Neueren Importer behalten |
| Provenienz | Sprache, URL, Source-Datei, Format, `official_transcript`/`official_subtitle` | **Übernommen**; keine erfundene Videozuordnung oder Whisper-/Runtimewerte | Keine | Transcript-URL nicht als verifizierte Media-ID interpretieren | CLOSE |
| Unbekannte TXT-Zeitstempel | Pflichtfelder `start/end`, nullable; `duration=None` | **Vollständig durch C23-05 nachgezogen und gehärtet**: explizite Nullpaare oder endliche, nichtnegative geordnete Sekunden; keine Mischpaare, NaN/Inf oder erfundene Dauer | Keine; der frühere Sechs-TXT-Fehlerblock ist behoben | Alte Modellversion würde neuere Intervallvalidierung und Verbraucherprüfungen entfernen | Kein weiterer Nullable-PATCH |
| Knowledge-Chunking-Guard | Vor zeitbasierter Arithmetik bei `None` abbrechen | **Funktional gleichwertig und strenger**: `transcript.require_timestamps()` vor Dauerarithmetik, auch Invalid-/Copy-Grenzen abgesichert | Keine für den beauftragten Timed-Guard | Alten sechszeiligen Guard nicht statt der gemeinsamen Validierung einsetzen | CLOSE |
| Sichere getrennte Speicherung | `.json`, vorher validieren, `open('x')`, keine Überschreibung von Datei/Symlink, vorhandener Elternordner | **Übernommen**; Saver revalidiert Dump vor Dateierzeugung, Datei-/Symlinkfälle und Originalhash getestet | Keine innerhalb dieses expliziten lokalen Saver-Vertrags | Saver ist kein universeller Root-/Mountresolver; aus dem alten PR keine beliebige UI-Dateisystemfreigabe ableiten | Für C27 weiterhin RegisteredStorage/Rootpolicy verwenden |
| TXT-Weiterverarbeitung | Timed Knowledge ausdrücklich **nicht** für TXT freigeben; separaten Textpfad später vorsehen | **Vertrag erhalten**; zeitbasierte Evidence-/Retrievaladapter lehnen unbekannte Medienzeiten ab. C27 kann TXT unabhängig über eigene quellengebundene Textblöcke lesen | Keine ursprüngliche Anforderung an einen vollständigen Timed-TXT-Worker | Fake-Zeitstempel oder pauschales Durchreichen würden Provenienz verletzen | Keine allgemeine TXT-Workerfreigabe aus #9 ableiten |
| Tests und Importbericht | 37 Importfälle, Bericht am damaligen Fixturepfad | **Erweitert/verschoben**: 39 Importfälle, 26 Unknown-Time-Fälle, 5 SRT-Integrationsfälle bestanden; Bericht 100 % im Archiv erhalten | Keine Verhaltenslücke | Alte Testassertions nicht anstelle neuer Grenzfälle übernehmen | Bestehende Tests und C23-05-Vertrag behalten |
| Synthetischer TXT-Text und normalisiertes Beispiel-JSON | Beide Dateien im PR | TXT **byteidentisch** vorhanden; `official_transcript.normalized.json` **nicht übernommen**, auch nicht unter anderem Pfad gefunden | Nur das illustrative JSON-Artefakt fehlt; kein fehlender Import-/Speicherpfad | Festes altes Beispiel mit damaligem `acquired_at`/alter Textaggregation ist keine heutige Referenzdatei | Als überholtes generiertes Beispiel behandeln; ausführbare Roundtriptests ersetzen es |

**Empfehlung: CLOSE.** Die frühere Empfehlung PATCH für Nullablezeiten/Chunker
im Review vom 14./16.10. ist durch C23-05 erledigt. Das allein nicht übernommene
Beispiel-JSON rechtfertigt keinen Produktcode-Patch und keinen Rebase des alten PRs.
Es wird nicht behauptet, dass alle sieben PR-Dateien heute unter ihrem alten Pfad
identisch vorhanden wären.

Der lokale Saver garantiert exklusives Anlegen des angegebenen Ziels. Daraus
folgt keine allgemeine Traversal-/Mount-/Symlink-Elternprüfung für untrusted
API-Eingaben. Die gesicherte C27-Storagegrenze bleibt zusätzlich notwendig;
diese Analyse schwächt sie nicht ab und fordert keine neue öffentliche Route.

## #6 – Fixtures, Discovery, Extraktion und Auswahl

| Ursprüngliche Anforderung | Stand im PR | Stand in master | Fehlende Funktionalität | Risiko einer Übernahme | Empfohlene Aktion |
|---|---|---|---|---|---|
| Reproduzierbare Offline-Fixtures | 18 vorhandene Browser-HTMLs versioniert | **Alle 18 Git-Blobs byteidentisch erhalten**; Gesamtbestand inzwischen 63 Fixtures für sechs Kurse | Keine | Altes Manifest würde 45 zusätzliche Fixtures/zwei Kurse aus dem aktuellen Katalog verdrängen | CLOSE, keine alten Snapshots zurückkopieren |
| Manifest-/Original-URL-Prüfung | Schema, Kurse/Seitenrollen, relative Dateien, Host/HTTPS, Duplikate, Saved-URL-Kommentar | **Vollständig übernommen und erweitert**: optionales SHA256 mit Inhaltsprüfung; alte Manifeste ohne Hash bleiben lesbar | Keine | Alte Loaderdatei entfernt Checksummenprüfung und zwei Course-IDs | Aktuellen Loader behalten |
| Discovery-Modelle und stabile IDs | Course/Section/Resource/Variant/Warning/Provenance; deterministische Identität | **Gleicher Modellvertrag**, wesentliche Erweiterung nur CourseId auf Web/Cybersecurity; frozen/extra-forbid und berechnete IDs erhalten | Keine | Alte Literalmenge schließt heutige Kurse aus | CLOSE |
| Rollen und Status | Ressourcenrollen separat von Fixture-Seitenrollen; `referenced`/`parsed` | **Erhalten**, zusätzliche Parsererkennung etwa Assignment/Final Project/„Watch lecture.“ | Keine | Alte Parserkopie erkennt heutige Kursseiten schlechter | Neueren Parser behalten |
| Hierarchie | Stringschlüssel einschließlich `ai`, Eltern/Ordnung, Elternressourcen, zyklische/unbekannte Verweise ablehnen | **Vollständig erhalten** in CourseDiscovery-Validierung und bestehenden Tests | Keine | Kein Anlass für eine Konfliktauflösung durch Komplettübernahme | CLOSE |
| Medienvarianten und Provenienz | Mehrere URLs, Sprache, Format, Auflösung, HDR/SDR, Media-ID, DOM-/Kontextprovenienz | **Erhalten**; zusätzlich Warnung bei mehreren Lecture-Media-IDs je Sprache | Keine | Variationen/Mehrdeutigkeit dürfen nicht zu einer stillen Einzelquelle werden | CLOSE |
| Offline-Extraktion (#7 im Head) | Index-/Wochenparser und Warnungen, keine Downloads | **Übernommen**; heutige Sechs-Kurs-/50-Wochen-Abdeckung, ursprüngliche Regression über `regression_manifest.json` erhalten | Keine | Rücknahme neuer Rollen-/Player-/Kursfälle | Kein REWORK des alten Sammelheads |
| Auswahlvorschau (#8 im Head) | Policy für Text/Video, Sprache/Qualität, keine Ausführung | **Übernommen und erweitert**: `timed_knowledge`, eindeutige offizielle SRT-Zuordnung, kein automatischer TXT/VTT/Medienfallback in diesem Modus | Keine | Alte Auswahl entfernt die für heutige Knowledgepfade erforderliche Timed-Policy | Neuere fail-closed Auswahl behalten |
| Offline-Tests | Initial 25 Discoveryfälle; finaler Head zusätzlich Extraktion/Auswahl | **98 Fälle bestanden**: Discovery 30, Extraktion 44, Selection 24; Netzwerkwächter aktiv | Keine | Alte Vier-Kurs-/18-Fixture-Assertions bilden heutigen Gesamtbestand nicht ab | Aktuelle und historische Teilmatrix erhalten |
| Dokumentation | analysis/discovery/extraction_report/selection_policy/selection_preview | **Erhalten unter neuer Struktur**: discovery/selection_policy in `docs/cs50/contracts/`; übrige drei im Archiv `2026-10/`; Git erkennt Verschiebungen mit 98–100 % Ähnlichkeit | Keine | Alte Pfade als fehlende Funktion missverstehen oder historische Zahlen als aktuell ausgeben | Keine Dokumentduplikate; aktuelle Einstiege nutzen |

**Empfehlung: CLOSE.** Der tatsächliche PR-Head umfasst mehr als seinen
ursprünglichen Titel, aber auch diese zusätzlich enthaltenen Parser-/Selection-
Funktionen sind vorhanden. Kein funktionaler Rest für PATCH gefunden.

## Tatsächlich ausgeführte Regressionen

Keine vollständige Backend-/UI-Regression und keine neue Testinstallation.
Verwendet wurde unverändert
`Personal_Assistant-c26b6-planning-results/test-env/bin/python`:
Python 3.12.12, pytest 9.1.1, Pydantic 2.14.1/core 2.50.1,
HTTPX 0.28.1, BeautifulSoup 4.15.0. Die Pydantic-Pins weichen vom Backend-Lock
2.13.4/core 2.46.4 ab; erfüllt ist der deklarierte Dependencybereich, kein neuer
exakter Backend-Locknachweis. Keine SDK-/Browser-/Systempakete installiert.

Auf unverändertem Master `29114d2`, **306 bestanden, 0 fehlgeschlagen, 0 Skips**,
80,52 s:

| Bestehende Testdatei | Bestandene Fälle |
|---|---:|
| `test_consolidation_math_import.py` | 1 |
| `test_consolidation_hardening.py` | 77 |
| `test_knowledge_source_id.py` | 11 |
| `test_knowledge_transcript_provenance.py` | 41 |
| `test_knowledge_identity_arguments.py` | 8 |
| `test_official_transcript_import.py` | 39 |
| `test_transcript_unknown_time.py` | 26 |
| `test_cs50_srt_knowledge_integration.py` | 5 |
| `test_cs50_discovery.py` | 30 |
| `test_cs50_extraction.py` | 44 |
| `test_cs50_selection.py` | 24 |

Auf einem separaten Code-Snapshot aus aktuellem Master plus dem unveränderten
C27-Dateidelta zusätzlich **97 bestanden, 0 Fehler/Skips**, 3,81 s:
35 Servicefälle, 21 Vertragsfälle, 7 Abnahme-/Preflightfälle und 34 Rootpolicyfälle.
Die gemeinsame Basis von Master und C27 ist `e502aa9`; 28 Masteränderungen und
21 C27-Dateiänderungen überschneiden sich **in keiner Datei**. Erst nach dieser
Prüfung wurde das unveränderte C27-Delta auf den isolierten Snapshot gelegt.
Es erfolgte kein Git-Merge, keine Konfliktauflösung und keine Änderung an #158.
Die tatsächlich importierten C27-/Storage-Modulpfade zeigen auf diesen Snapshot.

Damit sind **403 gezielte Fälle** erfolgreich, keine Vollabnahme des gesamten
Produkts. Die Tests nutzen synthetische lokale Quellen/Mockantworten und die
vorhandenen jeweiligen Netzwerkguards. Kein LLM-Aufruf, keine produktive
Queue/DB, keine historischen Pilotdaten oder externen Materialien angefasst.
UI-, echte SDK-/LLM-, mathematische Fach-/Live-Material- und Produktivnachweise
sind nicht Bestandteil dieses Audits.

Die beiden geänderten Markdown-Dateien wurden zusätzlich auf relative Links,
Trailing Whitespace, einzelnen abschließenden Zeilenumbruch, Größe und mit
`git diff --check` geprüft. Der vorhandene Git-Hook verweist auf ein entfallenes
Venv; `pre-commit` ist nicht verfügbar. Der Hook selbst wurde nicht als bestanden
ausgegeben und keine Hook-/Formatterumgebung nachinstalliert. Für diese reinen
Markdownänderungen betreffen die konfigurierten Hooks Whitespace/EOF/Dateigröße;
Python-/JSON-/YAML-/TOML-/Ruff-Prüfungen haben hier keine passenden Dateien.

Reproduzierbarer erster Lauf im Audit-Worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python \
  -B -m pytest -q -p no:cacheprovider \
  tests/test_consolidation_math_import.py tests/test_consolidation_hardening.py \
  tests/test_knowledge_source_id.py tests/test_knowledge_transcript_provenance.py \
  tests/test_knowledge_identity_arguments.py tests/test_official_transcript_import.py \
  tests/test_transcript_unknown_time.py tests/test_cs50_srt_knowledge_integration.py \
  tests/test_cs50_discovery.py tests/test_cs50_extraction.py tests/test_cs50_selection.py
```

## Abhängigkeiten und empfohlene Integrationsfolge

| PR | Tatsächlicher Status bei Prüfung | Bedeutung für diesen Audit/C27 |
|---|---|---|
| [#156](https://github.com/rf-data/Personal_Assistant/pull/156) | Bereits gemergt, 24.10.2026 15:21:02 UTC; Merge `ce8dd5ad12dfb5e66f7f165d20601b1d4419b028` | Lazy-Imports und begrenzte SQLite-Setup-Retries sind schon Masterbestand. Keine erneute Integration planen oder seine späteren Importänderungen mit #9 zurücksetzen. |
| [#149](https://github.com/rf-data/Personal_Assistant/pull/149) | Danach gemergt, 15:21:44 UTC; Merge `29114d2e2877cee9c434f620da852313963e3a01` | HTML-Referenzen/Listenhierarchie im Handoff v2 bleiben erhalten. NormalizedDocument/Parser-/Receipt-Verträge wurden von #149 nicht ersetzt. Keine alten Discovery-/Selectionstände darüberlegen. |
| [#158](https://github.com/rf-data/Personal_Assistant/pull/158) | Offen, Draft, Head `4fedf844da2199f6240c50efa590bc2265eff6da`; gemeinsame Basis `e502aa9` | Nutzt vorhandene nullable Transcriptmodelle, Knowledge-Extrakte und registrierte Storagegrenze. #6/#9/#11 müssen hierfür nicht gemergt werden. Gezielter Kompatibilitätstest mit heutigem Master bestanden. |

Die Reihenfolge **#156 → #149 ist bereits erfolgt**. Als nächstes die
CLOSE-Empfehlungen manuell prüfen; die alten PRs sind keine Integrationsvoraussetzung.
C27 #158 kann danach unabhängig fachlich/technisch weiter abgenommen werden,
vor einer später gesondert freizugebenden Integration erneut gegen den dann
aktuellen Master. Dieser Audit veranlasst keinen Merge oder Ready-Wechsel.

C27 muss unbekannte Zeiten weiterhin als unbekannt erhalten und darf aus einem
normalisierten Transcript weder eine verifizierte Medienzuordnung noch mathematisch
geprüfte Formeln ableiten. Discovery liefert Kandidaten/Provenienz, keine
automatische Zusammenfassung ganzer Kurse. Der lokale Summarizer bleibt unabhängig
vom produktiven Worker-/Queuebootstrap. Seine bekannten Live-Kontextgrenzen werden
durch diesen Kompatibilitätsnachweis nicht aufgehoben.

## Arbeitsstände und Grenzen

Eigener isolierter Worktree: `Personal_Assistant-c26-legacy-pr-audit`, Branch
`audit/c26-legacy-prs`. Zusätzlich eigene reine Auditreferenzen
`refs/codex/c26-legacy-pr-audit/{master,c27}`; vorhandene Tracking-/Arbeitsbranches
wurden nicht verschoben. Kompatibilitätssnapshot:
`/tmp/c26-legacy-c27-compat-20261024`, synthetische Fixtures unter
`/tmp/c26-legacy-pr-audit-tests-20261024` und `/tmp/c26-legacy-c27-fixtures-20261024`.
Keine vorhandenen Worktrees/Branches/Umgebungen/Gitdaten gelöscht oder bereinigt.

Der erste Git-Fetch in der Standardsandbox scheiterte an der Namensauflösung;
gezielte Fetches in neue Auditrefs liefen danach mit `require_escalated`.
Kein ENOSPC; gemessener verfügbarer Platz vor Beginn etwa 5,1 GiB auf Btrfs.
Der neue Worktree umfasst nur den versionierten Quellbaum (ca. 25,5 MB), keine
kopierte Venv oder Originalmedien. Es gab keinen SSH-/Produktivzugriff.

Der Auditbericht wird separat als Dokumentations-Draft reviewbar gesichert.
Kein Code-PATCH erforderlich. Wegen des Mergeverbots bleiben eigene Artefakte
erhalten; die neuen Dokumente sind damit noch nicht in `master` integriert.
