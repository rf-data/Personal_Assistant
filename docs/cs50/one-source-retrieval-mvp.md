# CS50P One-Source Retrieval MVP

Aktueller Integrationsstand: Prompt 25, 06.11.2026. F1 bestätigt, **F2
geschlossen**: frische scoped Installation und Offline-Regression bestanden.
Technisch für einen separaten PR vorbereitet; Merge/Deployment bleiben HOLD.
Die folgenden ursprünglichen Analyse-/Planabschnitte und Resultate aus Prompt 20
sind historische Referenz; der neue Vertrag steht im Abschnitt „Prompt 24“.
Der getrennte [Validierungsbericht](one-source-retrieval-validation.md) erhält
Abweichungsakzeptanz, aktuelle Tests und Freigabegrenzen. Persönliche Pfade wurden
für die Veröffentlichung redigiert; private historische Originalnachweise bleiben
unverändert erhalten.

## Ausgangslage und verbindlicher Testplan vor Implementierung

Stand 2026-11-06. Worktree
`<repository>`, Branch
`feat/cs50p-one-source-retrieval-mvp`. HEAD, Merge-Base mit `origin/master` und
lokaler Remote-Tracking-Basiscommit sind
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Git-Ausgangsstatus: sauber.
Es werden keine Git-Artefakte angelegt oder entfernt. Der vorgegebene Worktree
und Branch existierten bereits. Kein Fetch/Commit/Push/PR/ Merge ist Teil dieses
Auftrags. Eine Aktualisierung von origin/master vor Worktree-Erstellung ist
nachträglich nicht beweisbar; der vorhandene Basisstand wird festgehalten.

GitHub-Metadaten zu PR #171 wurden lesend geprüft: offen, Draft, nicht gemergt,
Base master auf obigem Commit, Head `929fb1e1aa821e779b7d7ad327cf5a323666bd31`.
Dieser PR und seine Nachweise werden nicht verändert oder übernommen.

Der folgende Testplan wurde vor dem Schreiben des Operators festgelegt:

1. CLI-Pflichtargumente, explizite absolute Pfade, private neue Zielroots.
2. Eigenes HTML mit drei vorher festgelegten Suchaufgaben und Originalpassagen:
   Import, Parser, Quality/Handoff, echtes Bundle, persistente ParsedVersion.
3. Fehlende, abgelaufene, widersprüchliche Freigabe; Rawhash-Konflikt:
   kein Import und kein neuer Zielroot.
4. Parserfehler und Quality-Gate-Ablehnung: keine ParsedVersion, kein Erfolg.
5. Expliziter FTS5-Aufbau; Top 5 und Quellenauflösung gegen Originalblöcke,
   Rawhash, Source-ID, ParsedVersion, DOM und Indexgeneration.
6. Wiederholung: gleiche ParsedVersion, eine Publikation, gleiche Generation.
7. Geänderte Bytes: alte Freigabe und bestehender Zielroot bleiben unverändert;
   neue genehmigte Bytes erfordern einen neuen isolierten Root.
8. Fehler vor Publikation, nach tatsächlicher Publikation mit verlorener Antwort,
   vor Indexaktivierung: unvollständiger Status, kein automatischer Retry,
   keine automatische Recovery oder Quarantäne-Aufhebung.
9. Echte separate Python-Prozesse für Wiederabruf und verlorene Abschlussantwort.
10. Bestandsschutz: Input-/Manifestbytes unverändert, fremde Zielinhalte,
    vorhandene Stores, Symlinks und unsichere Roots ablehnen.
11. Die fünf ausdrücklich genannten bestehenden Testdateien sowie relevante
    Material-Parser-/Quality-Tests ausführen. Alle vier genannten Testnamen wurden
    im Repository gefunden. Keine Skips/Xfails ergänzen; Fehlschläge dokumentieren.
12. Nach letzter Codeänderung finale neue und relevante bestehende Tests prüfen;
    keine unbegrenzten Wiederholungen.

## Phase A: vorhandene Verträge

Der tatsächliche Offline-Datenfluss ist:

```text
explizites lokales HTML + MaterialPlan + separate Operatorfreigabe
  -> MaterialDownloader.obtain(local_file=..., execute=True)
  -> verified ArtifactReceipt + unveränderte Rawkopie
  -> MaterialProcessor.parse(execute=True, config=html v2)
  -> NormalizedDocument + completed ArtifactReceipt + lokale Bildclosure
  -> prepare_material_handoff (Quality/Handoff, keine Extraction)
  -> MaterialBundle + ImplementationEvidence
  -> verify_material_bundle (eingefrorene Closure, Quality erneut prüfen)
  -> import_verified_bundle (erneute Prüfung im Store-Staging)
  -> ContentStore: RawArtifact / SourceVersion / ParsedDocumentVersion
  -> ContentIndex.build(IndexSelection mit genau dieser ParsedVersion)
  -> project_content_for_index -> SQLite FTS5 -> aktive persistente Generation
  -> ContentIndex.search_lexical -> SearchResultPage / SearchHit
  -> ContentReader.block: Originaltextfenster und Struktur mit Source-Locators
```

`MaterialPlan` enthält vollständige CourseDiscovery-Graphen und MaterialResource-
Bindungen: Resource-ID, Material-ID, URL, Kurs, Sections, logische Lecture-IDs,
Format, Herkunft. Die Auswahl ist genau ein explizites Material im Plan, nicht
eine automatische Week-/Domain-Auswahl. Parserkonfiguration wird unverändert im
Receipt festgehalten. `MaterialProcessor` verwendet den lokalen Import und kann
abgeschlossene Ergebnisse prüfen; es wird kein alternativer Parser gebaut.

Die vollständige `MaterialBundle`-Closure enthält Workspace, Rawdatei,
normalized JSON, Receipt, Plan und ImplementationEvidence; alle im Dokument
referenzierten lokalen Bilder gehören dazu. Der Adapter friert Dateien ohne
Symlink-Folgen ein, prüft Hashes und Handoff erneut und erstellt erst dann die
prozesslokale `VerifiedPublicationCandidate`-Capability. Der Qualitätsbericht
allein ist keine Verarbeitungsfreigabe. Es gibt hier keinen bestehenden separaten
Freigabevertrag für lokale One-Source-Verarbeitung; der Operator ergänzt diesen
vor dem unveränderten Bundle-Adapter.

ImplementationEvidence bindet Revision, Parsername/-version/-parameter, Source-ID,
Material-ID und exakte Raw-/Payload-/Receipthashes. Der Store sichert Plan,
Implementierungsnachweis, Receipt, Binding, Quality, Handoff und Projection als
Versionsartefakte. Approval und aktueller Codehash werden im eigenen MVP-Root
gesichert und im Implementierungsnachweis referenziert.

`ContentStore.initialize` erzeugt nur einen neuen Store. Nach Neustart ist der
Handle standardmäßig read-only. `import_verified_bundle` publiziert mit einem
expliziten request_key, ohne FTS automatisch aufzubauen. Raw/Source-Registrierungen
können vor einer fehlgeschlagenen Parsed-Publikation bereits existieren.
Ein fehlender Response beweist deshalb weder Rollback noch erfolgreiche Publikation.
Vorhandene Recovery-APIs bleiben einer gesonderten Operatorentscheidung vorbehalten.

`ContentIndex.build` trennt Staging, Verifikation und Aktivierung; Generationen
sind persistent. `search_lexical` liefert reale FTS-Ergebnisse. `ContentReader`
löst Blocktexte und Struktur unabhängig von der Anzahl der Dokumentblöcke auf.
`ContentStore.list_content_blocks` allein wäre wegen seines 100-Block-Limits keine
allgemeine Quellenauflösung. Lange Originalblöcke werden über vorhandene
TextWindow-Fenster mit maximal 16384 Codepoints gelesen.

Die C16-Schranke in `src/job_control/import_jobs.py` lautet weiterhin
`real source release required`, `import_http.py` bleibt bei `real_sources=False`.
Keine HTTP-Admission-, Guardian-, Executor- oder Quarantäneregel wird geändert.

## Implementierter Operator und Input-/Output-Vertrag

`scripts/cs50_learning_mvp.py` hat drei Operationen. Alle verlangen
`--output-root` (absolut, außerhalb des Repositories, keine Symlinks) und
`--actor` (explizite lokale Operatoridentität).

```bash
python -m scripts.cs50_learning_mvp run \
  --input /tmp/reviewed-input/own.html \
  --plan /tmp/reviewed-input/plan.json --material '<exact-material-or-resource-id>' \
  --approval /tmp/reviewed-input/approval.json \
  --output-root /tmp/new-private-one-source-root --actor synthetic-operator \
  --query variable --query input --query loop

python -m scripts.cs50_learning_mvp search \
  --output-root /tmp/new-private-one-source-root --actor synthetic-operator \
  --query input

python -m scripts.cs50_learning_mvp status \
  --output-root /tmp/new-private-one-source-root --actor synthetic-operator
```

`run` ist der ausdrückliche Ausführungsauftrag. Ein neuer Root darf vorher nicht
existieren, auch nicht leer; sein Elternverzeichnis muss existieren. Der Root wird
mit 0700 und Dateien unter umask 0077 angelegt. Ein erfolgreicher Wiederholungslauf
akzeptiert ausschließlich identische Input-, Plan-, Freigabe- und Codebindungen.
Er prüft Bundle und Persistenz erneut und liest den vorhandenen Index; er parst,
publiziert und indexiert nicht erneut. `search` benötigt Originalinput und
Originalworkspace nicht mehr, nur den gesicherten MVP-Root; `status` beobachtet
auch unvollständige Operationen und zeigt existierende Source-/ParsedVersionen,
Recovery-Runs und Index-Builds. `observed` bedeutet keine erfolgreiche Publikation.

Der Plan ist der unveränderte vorhandene `MaterialPlan`-Vertrag. Er darf weitere
Materialien enthalten; genau eine explizite Auswahl wird verarbeitet. Es werden
keine Resource-/Lecture-IDs aus Dateinamen abgeleitet. Das HTML wird ausschließlich
lokal gelesen und mit dem bestehenden html-v2-Parser verarbeitet. Der vorhandene
Parserselektor verlangt geeignete CS50-URL-Identitäten, auch bei synthetischen
Fixtures. Eine solche URL beweist weder Download noch Freigabe noch Authentizität.

Die neue **ProcessingApproval** ist ein eigenes, explizites Operator-Attest für
diesen lokalen Ablauf, keine Änderung existierender Approval-/Source-Manifeste.
Die Datei muss privat (0600), im Besitz des lokalen Users und ohne Symlinks sein.
Sie enthält alle folgenden Pflichtfelder (keine automatischen Approvaldefaults):

| Feld | Bedeutung |
| --- | --- |
| schema_version / status | 1 / `approved` |
| approved_by | identisch zu `--actor` |
| evidence_reference | konkrete dokumentierte Freigabe, für Tests ausdrücklich eigene Synthetik |
| valid_until | zukünftiger Zeitpunkt mit Zeitzone; auch Retrieval prüft Ablauf |
| resource_id / material_id | beide exakten berechneten IDs aus dem ausgewählten Material |
| original_url / source_origin | exakte Planbindung; `synthetic` oder `official` |
| raw_sha256 / plan_sha256 | SHA-256 der exakten Input-/Plandateibytes |
| parser | vollständiger vorhandener ParserConfig, zwingend html v2 |
| implementation_revision | tatsächlicher Git-HEAD, keine erfundene Revision |
| implementation_sha256 | Fingerprint der aktuellen Pythonbytes unter src/ und des Operators |
| actions | exakt `["local_import", "parse", "publish", "index", "retrieve"]` |
| retrieval_tasks | genau drei Objekte mit query und unabhängig festgelegter expected_passage |

`implementation_identity()` ermittelt Revision und Codefingerprint lesend.
Der Fingerprint bindet Pfade und SHA-256 aller vorhandenen Pythondateien unter
`src/` sowie den Operator. Damit wird auch uncommittierter Operatorcode explizit
erfasst; HEAD allein wird niemals als Nachweis einer committierten Implementierung
ausgegeben. Die Bibliotheksumgebung ist separat im Validierungsbericht erfasst.
Ein Codewechsel verlangt eine neue konkrete Freigabe und einen neuen Root.

Die Freigabe ist eine lokale vertrauenswürdige Operatorerklärung, keine digitale
Signatur oder selbstständige Prüfung von Lizenz, Rechtslage oder Originalherkunft.
Für `official` muss zusätzlich `license_status=reviewed` im Binding stehen. Ein
Domainname ersetzt kein Pflichtfeld. Diese Implementierung stellt keine reale
Freigabe aus. Freigabe und Plan werden im neuen Root ausschließlich kopiert.

Queries benutzen den bestehenden lexikalischen Vertrag (maximal acht Terme mit
höchstens 64 Zeichen, höchstens 512 Zeichen/2048 UTF-8-Bytes); Operatorqueries
werden vor jeglicher Publikation geprüft. Drei Abnahmequeries stehen bereits in
der Freigabe. Eine erwartete Passage ist höchstens 2000 Codepoints lang und muss
in einem tatsächlich gefundenen Top-5-Originaltextfenster enthalten sein. Es gibt
keine aus Suchergebnissen erzeugten Goldpassagen oder Ersatztreffer.

JSON-Ausgabe enthält Intent, ParsedVersion, SourceVersion, ParserConfig-ID,
Build-ID, interne persistente generation_id sowie die öffentliche opake
index_generation. Letztere ist ein bestehender HMAC-basierter Generationstoken;
sie ist weder der Recordsethash noch die interne Generation-ID. Dazu kommen
reale SearchHits, Originaltextfenster, Source-Struktur/Rawreferenzen und die drei
beobachteten Ränge. Vor dem Schreiben wird der vorhandene Bestand inventarisiert;
der erste Lauf beginnt nur mit seiner eigenen Lockdatei. Wiederholungen liefern
das vollständige Vorherinventar und den Fingerprint des Nachherinventars.

`source_block` ist ein über ContentReader aufgelöstes TextWindow des Originalblocks
mit Block-ID und Codepoint-Offsets. Der lokale Operator gibt zusätzlich
`original_location` aus dem hashgeprüften gespeicherten NormalizedDocument aus.
Der bestehende öffentliche Reader redigiert slashführende DOM-Pfade weiterhin;
`origin_pointer`, Rawhash und Source-/Versionbindung bleiben dort auflösbar. Dieser
Unterschied wurde im ersten Entwicklungsversuch entdeckt und ohne Änderung der
HTTP-/Reader-Sicherheitsregeln berücksichtigt.

Exitcode 0 steht für abgeschlossenen erfolgreichen Retrievallauf oder eine
Statusbeobachtung; 2 steht für Ablehnung/Fehler. Erwartete Gate-/Integritätsfehler
liefern JSON `HOLD` auf stderr. Ein technisch abgeschlossener Lauf ohne passende
Goldpassage liefert einen vollständigen JSON-Bericht mit `retrieval_failed` auf
stdout und Exitcode 2. CLI-Syntaxfehler verwenden argparse mit Exitcode 2.
`TECHNICAL PASS` im Laufbericht bezeichnet diesen Durchlauf; die zusätzliche
Testsuite-Abnahme steht im Validierungsdokument. Der Operator stellt niemals
automatisch `MVP ACCEPTED` aus.

## Idempotenz, Fehlergrenzen und Bestandsschutz

```text
preparing -> publication_pending -> published -> index_pending -> ready
```

Die Übergänge werden mit vorhandenem atomarem `write_state` und fsync gesichert.
Vor `import_verified_bundle` steht bereits `publication_pending` auf Platte;
vor FTS-Aufbau steht `index_pending` auf Platte. Unvollständige Phasen werden beim
nächsten `run` ausschließlich abgelehnt. Status und vorhandene Recovery-APIs
erlauben eine gesonderte Untersuchung; der Operator ruft keine Recovery auf,
hebt keine Quarantäne auf und aktiviert keinen fehlgeschlagenen Index erneut.
Auch ein unbekannter Publikationszustand nach verlorener Antwort wird nie
automatisch wiederholt. Ist nur die finale Antwort verloren, aber `ready` bereits
gesichert, ist rein lesende Wiederholung möglich.

Vor Publikation werden Originalinput und Rawkopie erneut bytegenau verglichen;
nach Verarbeitung nochmals der Originalinput. Persistierte Rawbytes und exakte
Payload-/Receipt-/Plan-/Implementation-Dateien werden beim Wiederabruf gegen die
isolierte Closure geprüft. Blocktext und Quellenpointer werden gegen das
gespeicherte NormalizedDocument verifiziert. Bereits vorhandene ContentStores
werden nicht angenommen. Unbekannte Rootinhalte, fremde Identitäten, Symlinks,
nicht private Einträge oder widersprüchliche Intents bleiben erhalten und führen
zu HOLD. Mehr als 100 Dokumentblöcke sind über den vorhandenen Reader unterstützt.

Der Ablauf ist ein serieller lokaler Operator mit flock, kein Dienst und kein
neuer Worker. Andere Prozesse sollen diesen privaten Root nicht außerhalb des
Operators verändern. Die bestehenden Reader prüfen ACL und Quarantäne weiterhin
bei jeder Auflösung. Ganze Root-/Bibliotheks-/Dateisystemmanipulationen durch den
gleichen vertrauenswürdigen User werden damit nicht zu einem neuen Sicherheits-
oder Authentifizierungssystem erklärt. Teilzustände bleiben bewusst zur Prüfung
liegen; es gibt keine automatische Reparatur, Löschung oder Indexrekonstruktion.

## Reproduzierbare eigene synthetische Eingabe

Der Testhelper erzeugt ausschließlich die in `tests/test_cs50_learning_mvp.py`
festgeschriebenen eigenen Bytes und die dafür im Auftrag erlaubte synthetische
Freigabe. Er ist kein Generator von Freigaben für Fremdmaterial. Zum Erzeugen
eines frischen Datensatzes und Ausgabe eines konkreten CLI-Aufrufs:

```bash
python - <<'PY'
import shlex
import sys
import tempfile
from pathlib import Path
from tests.test_cs50_learning_mvp import make_case

parent = Path(tempfile.mkdtemp(prefix="cs50p-own-retrieval-"))
case = make_case(parent)
print(shlex.join([sys.executable, "-m", "scripts.cs50_learning_mvp", *case.argv]))
PY
```

Der ausgegebene Aufruf verarbeitet die Datei über die echte CLI. Danach ist ein
eigener `search`-Prozess mit diesem Root möglich. Die drei festen Suchaufgaben
sind `variable`, `input`, `loop`; die erwarteten Originalpassagen sind im Test
unabhängig von Parser und Suchergebnissen definiert. Das HTML hat zusätzlich eine
Überschrift und einen Codeblock. URL-Identitäten enthalten ausdrücklich
`synthetic-prompt20`; es wird niemals auf diese URLs zugegriffen.

## Realmaterial und Git-Lifecycle

Dieser Auftrag erteilt keine konkrete Verarbeitungsfreigabe für Originalmaterial.
Es werden ausschließlich eigene synthetische Bytes verwendet. Reale Abnahme:
**BLOCKED** bis konkrete Freigabe mit exaktem Hash, Bindung, Herkunft, vollständigem
Plan und Implementierungsbezug sowie drei vorab festgelegten Originalpassagen
vorliegt. Technische Synthetik ersetzt AC10/AC11 nicht.

Die task-spezifischen Verbote von Commit, Push, PR-Aktionen und Merge gehen der
allgemeinen Integration aus AGENTS.md vor. Dokumente bleiben im vorgegebenen
Worktree; Integration nach master und der allgemeine Abschluss-Lifecycle bleiben
ausdrücklich **pending**. Es erfolgt keine Bereinigung.

## Prompt 24: aktuelle Implementierungs- und Statusbindung

`preflight()` und `report()` rufen jetzt gemeinsam `approved_implementation()`
auf. Diese Funktion verwendet ausschließlich die vorhandene
`implementation_identity()`: tatsächlicher Git-HEAD plus `fingerprint()` des
Mappings aus relativen Dateipfaden und `sha256(_read(path))` aller Pythondateien
unter `src/` sowie dieses Operators. `fingerprint()` ist SHA-256 über das
bestehende kanonische JSON (sortierte Schlüssel, kompaktes UTF-8, keine
Normalisierung). Bibliotheksversionen, Tests und Markdown gehören nicht zu diesem
Codefingerprint; sie werden separat dokumentiert. Es gibt keinen zweiten
Hashalgorithmus und keine Ausnahme für historischen Code.

`search` erreicht `retrieve()` erst nach Prüfung des gespeicherten Approvalhashes,
des vollständigen ProcessingApproval-Schemas, der Gültigkeitsfrist, des Akteurs,
der exakten Aktionen und der aktuellen Revision/Fingerprint-Bindung. Auch die
Implementierungsfelder im gespeicherten Intent müssen exakt dazu passen.
Fehlende, fremde oder abgelaufene Bindungen ergeben Exitcode 2 und JSON `HOLD`
auf stderr, ohne erfolgreiche Abnahme, Migration, Neuverarbeitung oder Änderung
von Approval, Intent, Store oder Index. Die übrigen Persistenz-/Closure-Prüfungen
bleiben aktiv. Ein historischer Root wird durch Codeänderung nicht aktualisiert.

`status` ist bewusst forensische Beobachtung. Exitcode 0 bedeutet eine gelesene
Beobachtung, selbst wenn die Retrievalfreigabe nicht mehr passt. Ausgabe:
`status=observed`, `technical_status=NOT_ASSESSED` und
`retrieval_authorization.status=current` oder `HOLD` mit Fehlergrund. `current`
bezeichnet nur die aktuell passende gespeicherte Freigabe und Implementierung,
keine erneut bestandene Retrievalabnahme. Alte Revision und Fingerprint stehen
weiter im unveränderten Intent. Mismatch, abgelaufene/ungültige Approval oder eine
fehlgeschlagene Identitätsermittlung verhindern die Bestandsbeobachtung nicht.
Fehlender Intent/State oder beschädigte nicht lesbare Storestrukturen können
weiterhin die Beobachtung selbst verhindern; Bootstrap-Recovery wird nicht ergänzt.

14 neue synthetische Fälle ergänzen die bisherigen 36 Operatorfälle. Sie prüfen
positive Suche, beide Identitätskomponenten, nicht ermittelbare Identität, fehlende
Approval-/Intentfelder, abweichenden Intent sowie widerrufene, abgelaufene,
akteursfremde oder aktionswidrige Approvals. Die Simulation verändert ausschließlich
synthetische temporäre Fixtures oder injiziert `implementation_identity()`.
Abgewiesene Aufrufe dürfen `retrieve()` nicht erreichen; vor/nach Suche und Status
werden sämtliche Rootdateihashes und Modi verglichen. Der vorhandene echte
Subprozessrestart und die gültige Idempotenz bleiben Teil der vollständigen Suite.

## Prompt 24: portabler Dependencyvertrag und Ausführungsgrenze

**Herstellungsnachweis derzeit HOLD.** Die folgenden Befehle sind die konkrete
Installations-/Prüfanleitung für einen bereitgestellten vollständigen Offlinecache
oder ein separat genehmigtes Wheelhouse. In Prompt 24 ist die tatsächliche frische
Installation fehlgeschlagen; die Anleitung ist kein behaupteter erfolgreicher Build.
Eine Onlineinstallation oder ein Pythondownload ist damit nicht freigegeben.

Der Rootvertrag enthält bereits Python `>=3.12,<3.14`, `test-offline`, pytest,
BeautifulSoup und PyMuPDF; `uv.lock` pinnt diese samt Transitiven. Das Paket
charset-normalizer gehört dort zu anderen Dependencyzweigen und wird von
BeautifulSoup nicht zwingend mitinstalliert. BeautifulSoup kann ein vorhandenes
`chardet` bevorzugen. Der historisch zusätzliche Debian-Systempfad änderte so die
Erkennung kurzer Unicode-Fixtures. Deshalb braucht dieses Testprofil einen
expliziten Encodingdetektor und eine isolierte Umgebung ohne Systempakete.

Der erste `uv sync --locked --offline --no-default-groups --group test-offline
--no-install-project --python 3.12.12` scheiterte am fehlenden PyMuPDF-Wheel.
Ein Entwurf einer zusätzlichen Root-Testgruppe wurde ausschließlich in einem
Scratchverzeichnis geprüft. `uv lock --offline` wollte dabei auch die globale
optionale OCR-Auflösung bedienen und scheiterte an fehlenden Torch-Metadaten.
Root-pyproject, Root-lock und optionale Produktprofile bleiben deshalb unverändert.

Der zusätzliche, begrenzte Vertrag
[cs50-mvp-requirements.txt](../../tests/profiles/cs50-mvp-requirements.txt)
ist eine Projektion des vorhandenen Root-Lockfiles: direkte Seeds `pydantic`,
`httpx`, `beautifulsoup4`, `pymupdf`, `charset-normalizer`, `pytest`, `ruff`,
rekursiv deren Dependency-Closure. Alle 22 Pins und Wheel-Hashes stammen aus
`uv.lock` am Basiscommit; keine neue Versionsauflösung, keine Upgrades und keine
sdist-Builds. Der einzige Plattformmarker (`colorama` für Windows) bleibt erhalten.
Das Ausführungsziel ist Linux mit Python **3.12.12**; die CLI verwendet `fcntl`.
Andere Betriebssysteme und Pythonversionen sind hier nicht validiert.

Die Transitivabhängigkeiten umfassen annotated-types, pydantic-core,
typing-extensions/-inspection; anyio, certifi, httpcore, h11, idna;
soupsieve; iniconfig, packaging, pluggy, pygments und bedingt colorama.
SQLite kommt aus dem Interpreter, nicht aus pip; FTS5 muss aktiv geprüft werden.
PyMuPDF wird für bestehende synthetische PDF-/Quality-Fixtures benötigt, obwohl
der MVP selbst nur HTML verarbeitet. Keine LLM-, Knowledge-, Torch-, UI- oder
Workerframeworks sind Bestandteil dieses Profils.

Das vorgeschlagene Profil bindet soupsieve **2.9.2** aus dem bestehenden Lockfile;
das historische Erfolgsprofil und die ergänzende Prompt-24-Regression verwenden
**3.0.4**. Alle übrigen auf Linux benötigten Pins stimmen mit der ergänzenden
Umgebung überein. Dieser Unterschied bleibt offen bis zum frischen Profiltest;
er wird weder durch Paketkopien noch durch eine ungeprüfte Lockänderung verdeckt.

Vom Repositoryroot, mit bereits vorhandenem uv (hier 0.9.15) und Interpreter:

```bash
test_root=$(mktemp -d "${TMPDIR:-/tmp}/cs50-mvp-validation.XXXXXX")
uv venv --offline --no-python-downloads --python 3.12.12 "$test_root/venv"
uv pip sync --offline --python "$test_root/venv/bin/python" \
  --require-hashes --only-binary :all: tests/profiles/cs50-mvp-requirements.txt
```

Falls nur ein separat bereitgestelltes Wheelhouse verwendet wird, beim Sync
zusätzlich `--no-index --find-links "$wheelhouse"` angeben; `wheelhouse` ist vom
Operator zu setzen. Fehlende Wheels/Metadaten oder Hashfehler bedeuten HOLD.
Weder Drittbibliotheken aus venvs kopieren noch absolute Cachepfade über `.pth`
einbinden. `PYTHONPATH`/`PYTHONHOME` nicht aus persönlichen Umgebungen übernehmen.
Nach erfolgreicher Installation folgende aktive Probe ausführen:

```bash
env -u PYTHONPATH -u PYTHONHOME "$test_root/venv/bin/python" -B - <<'PY'
import importlib.util
import site
import sqlite3
import sys
from pathlib import Path
import bs4.dammit
import pymupdf
from importlib.metadata import version
assert sys.version_info[:3] == (3, 12, 12)
assert site.ENABLE_USER_SITE is False
assert importlib.util.find_spec("chardet") is None
assert bs4.dammit.chardet_module.__name__ == "charset_normalizer"
for directory in site.getsitepackages():
    for path in Path(directory).glob("*.pth"):
        assert not any(Path(line.strip()).is_absolute()
                       for line in path.read_text().splitlines() if line.strip())
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
    db.execute("INSERT INTO probe VALUES ('Unicode Grüße')")
    assert db.execute("SELECT count(*) FROM probe WHERE probe MATCH 'Grüße'").fetchone() == (1,)
print(sys.version, "SQLite", sqlite3.sqlite_version)
for name in ("pydantic", "pytest", "beautifulsoup4", "soupsieve",
             "charset-normalizer", "httpx", "pymupdf", "ruff"):
    print(name, version(name))
PY
```

Der eindeutige gemeinsame Testaufruf nach bestandener Probe:

```bash
env -u PYTHONPATH -u PYTHONHOME \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  timeout 900 "$test_root/venv/bin/python" -B -m pytest \
  tests/test_cs50_learning_mvp.py \
  tests/test_content_store_adapters.py tests/test_content_fts.py \
  tests/test_content_retrieval_integration.py tests/test_content_import_jobs.py \
  tests/test_content_index_projection.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_download.py tests/test_cs50_material_html.py \
  tests/test_cs50_material_html_semantics.py tests/test_cs50_material_quality.py \
  tests/test_cs50_material_contracts.py -m 'not external_integration' \
  -p no:cacheprovider --basetemp="$test_root/tests" \
  --junitxml="$test_root/results.xml"
"$test_root/venv/bin/ruff" check --no-cache \
  scripts/cs50_learning_mvp.py tests/test_cs50_learning_mvp.py
"$test_root/venv/bin/ruff" format --check --no-cache \
  scripts/cs50_learning_mvp.py tests/test_cs50_learning_mvp.py
```

Die externe Originalmaterialprüfung wird ausdrücklich abgewählt, nicht als PASS
gezählt. Keine neuen Skips/Xfails. Socket-Sperren der Python-Fixtures schützen den
pytest-Prozess; sie sind keine OS-Netzwerksperre für Unterprozesse. Das bleibt eine
bekannte Testgrenze (Prompt-23-F4). Der Operator benutzt explizit `local_file`.
HTML läuft synchron; `timeout`/`memory_mb` sind hier keine harten isolierten
HTML-Prozessgrenzen (Prompt-23-F5). Byte-/Block-/Bildgrenzen bleiben aktiv.

## Prompt 24: reale Abnahme und unabhängige Integration

Prompt 22 belegte für den **damaligen** Fingerprint `548ff425…f5d25cd`:
71.718 Originalbytes, 237 normalisierte Blöcke, 171 Indexrecords, genau eine
ParsedVersion, drei vorab festgelegte Goldpassagen jeweils Rang 1 sowie Restart
und Idempotenz. Prompt 23 bestätigte unabhängig 72/72 Manifestdateihashes,
Rawbytegleichheit, SQLite-Integrität und konsistente Implementierungsbindung.
Das sind historische Nachweise, keine Realabnahme der geänderten Prompt-24-Bytes.
Es wurde kein Realmateriallauf wiederholt und keine alte Approval angepasst.

Die ursprüngliche Offline-Anweisung wurde in Prompt 22 durch einen zusätzlichen
öffentlichen Notes-Seitenabruf verletzt. Dieser Prozessverstoß bleibt dauerhaft
festgehalten. Der Betreiber akzeptiert am **06.11.2026** ausdrücklich den einmaligen
Abruf als dokumentierte Ausnahme für die nachgeprüften, unveränderten lokalen
Datenbestände. Diese Entscheidung erlaubt, den bisherigen lokalen Lauf als
fachlichen und technischen Nachweis genau des geprüften Stands zu verwenden.
Sie macht den historischen Vorgang **nicht rückwirkend regelkonform** und erlaubt
keine pauschale Aussage über sämtliche Dateien oder den gesamten Netzwerkverkehr.
Die historischen Berichte und ihre damaligen HOLD-Entscheidungen bleiben erhalten.

**MVP ACCEPTED** gilt damit für den begrenzten historischen Einzelquellennachweis
unter dokumentierter Ausnahme, nicht als neue Realmaterialfreigabe und nicht als
INTEGRATION/MERGE/DEPLOYMENT READY der geänderten Implementierung. Aktuelle
Integrationsfreigabe bleibt wegen F2/AC6 HOLD. Scope: eine reale HTML-Quelle,
privater lokaler nichtkommerzieller Betrieb, lexikalische Suche, kontrollierte
Operatorausführung, keine unbeaufsichtigte Job-Control-Nutzung.

Für einen späteren eigenständigen PR sind die vier MVP-Dateien plus der eng
begrenzte Testvertrag vorgesehen. Originale, Rawkopien, vollständige Pläne,
Approvals, Runtimeausgaben, Suchergebnisdumps, SQLite-Dateien und Cursor-Keys
bleiben privat. Kein experimenteller B1-Code gehört dazu. Keine harte funktionale
Abhängigkeit von PR #171 wurde festgestellt: alle verwendeten Module existieren
bereits im Basiscommit. Eine spätere Stage-0-Änderung der gemeinsamen
`src/tools_materials/storage.py` erfordert dennoch einen neuen Fingerprint und
Regression auf dem tatsächlichen gemeinsamen Stand. Stage 0 gilt weiterhin nicht
als integriert. Livebasis, PR-Status, Required Reviews und Hosted-CI sind hier nicht
geprüft; vor Merge separat bestätigen. Keine GitHub-Actions-Änderung in Prompt 24.

## Prompt 25: reproduzierbare Installation und F2-Abschluss

INSTALL und VERIFY sind am 06.11.2026 in getrennten Sitzungen abgeschlossen.
**F2 geschlossen:** frische Python-3.12.12-venv unter Linux x86_64 aus dem
scoped Vertrag installiert und anschließend vollständig offline validiert.
Requirements-SHA-256: `6d26f94c499ecf530394156bf57b9e4d579a61603ea04d733af67b6957dc46c1`.
Root-Lock-SHA-256: `63e72cbcf0df19c6f06e8088f1406e7404c2e0fe4b094a9f91f7fce5276cc19c`. Beide Verträge bleiben unverändert.
Die HOLD-Aussagen in den Prompt-24-Abschnitten und im Requirements-Kommentar
sind historische Stände; aktuelle Ergebnisse stehen im
[Prompt-25-Validierungsnachweis](one-source-retrieval-validation.md#prompt-25-frische-umgebung-und-offline-verify-06112026).

Erfolgreiche INSTALL-Befehle mit uv **0.9.15**, nur persönliche Pfadpräfixe
durch Variablen ersetzt. `python312` bezeichnet den bereits vorhandenen
3.12.12-Interpreter; `uv_bin` das vorhandene uv, `env_root` den bereitgestellten
privaten Umgebungsroot, `repo_root` dieses Repository. Für einen neuen Nachweis
müssen venv und Cache frisch sein; vorhandene Nachweise nicht überschreiben.
Diese Befehle wurden in INSTALL ausgeführt, nicht in VERIFY:

```bash
env -i HOME="$HOME" LANG=C.UTF-8 PATH=/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 TMPDIR="$env_root/install-evidence" \
  UV_CONCURRENT_DOWNLOADS=4 UV_HTTP_RETRIES=0 UV_HTTP_TIMEOUT=30 \
  UV_PYTHON_DOWNLOADS=never \
  "$uv_bin" --no-config --cache-dir "$env_root/uv-cache" \
  --no-python-downloads --color never --no-progress \
  venv --offline --python "$python312" "$env_root/venv"
env -i HOME="$HOME" LANG=C.UTF-8 PATH=/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 TMPDIR="$env_root/install-evidence" \
  UV_CONCURRENT_DOWNLOADS=4 UV_HTTP_RETRIES=0 UV_HTTP_TIMEOUT=30 \
  UV_PYTHON_DOWNLOADS=never \
  "$uv_bin" --no-config --cache-dir "$env_root/uv-cache" \
  --no-python-downloads --color never --no-progress -v pip sync \
  --python "$env_root/venv/bin/python" --default-index https://pypi.org/simple \
  --keyring-provider disabled --no-sources --require-hashes \
  --only-binary :all: --link-mode copy --strict \
  "$repo_root/tests/profiles/cs50-mvp-requirements.txt"
```

INSTALL PASS: 22 exakte Lockpins, 21 Linux-Pakete, nur PyPI-/pythonhosted-Wheels,
Hashvalidierung, keine Source-Builds, Systempakete oder Cachepfad-.pth-Verweise.
VERIFY bestätigt alle installierten Metadaten und 1005 RECORD-Dateihashes,
`uv pip check`, SQLite **3.50.4** mit aktivem FTS5 und Encodingdetektor
**charset-normalizer 3.5.1** ohne `chardet`. **soupsieve 2.9.2** ist das neu
validierte Lockprofil; das historische Erfolgsprofil verwendete **3.0.4**.
Die Profile werden nicht gleichgesetzt; andere Plattformen sind nicht validiert.

Ein fester Offline-Schlusslauf: **359 passed, 1 explizit deselected**, darunter
**50 MVP-Fälle und alle 14 F1-Fälle**, keine Fehler, Skips oder Xfails.
Realmaterial bleibt abgewählt. Ruff **0.16.3** und Formatprüfung aus derselben
venv bestanden. Ein privater vererbter seccomp-Filter sperrte Internet-Sockets
auch in Unterprozessen; er verändert keine produktive Sicherheitsgrenze.
Exakter Testaufruf, Versionen, Fingerprint, Log-/JUnit-Hashes, AC1–AC14 und
private Integritätsnachweise stehen im verlinkten Validierungsbericht.

Technisch für einen separaten Fünf-Dateien-PR vorbereitet. Livebasis,
Pflichtreviews und CI sind ungeprüft; **MERGE READY und DEPLOYMENT READY HOLD**.
Historische Realabnahme samt einmaliger dokumentierter Onlineausnahme bleibt
unverändert. Kein Realmateriallauf wiederholt, keine Approval angepasst.
Der bestehende serielle Einzelquellenumfang und F3/F4/F5-Grenzen gelten weiter.
Commit/Push/PR/Merge sind in Prompt 25 verboten; Defaultbranch-Integration und
allgemeiner AGENTS.md-Lifecycle bleiben pending, Branch/Worktree erhalten.
