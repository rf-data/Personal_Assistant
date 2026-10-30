# C27-R04 – Final PR-Blocker Remediation

Stand: 2026-10-29. Umfang ausschließlich R03-Restfinding F04 und C27-R03-T01.
**C27: READY_FOR_INDEPENDENT_REVIEW.** Dies ist eine Implementierungsübergabe,
keine unabhängige Bestätigung, PR-Freigabe, Integration oder Produktionsfreigabe.

| Prüfpunkt | Bewertung |
|---|---|
| F04 sensitive URL-Exporte | **FIXED** innerhalb der unten definierten Offline-Exportpolicy |
| Parent-Vertragsfehler T01 | **FIXED** – gültige Roots erhalten, nicht zuordenbare Downloadquellen kontrolliert abgewiesen |
| F01 / F02 / F03 / F05 | **Regression jeweils nein** im ausgeführten Prüfumfang |
| CS50P Week 0 | **PARTIAL**, keine vollständige Week-0-Abnahme |
| Multiweek/Multicourse-Rollout | **PLANNING_ONLY**, operative Freigabe weiterhin blockiert |
| Produktion | **NOT_APPROVED** |
| Default-Branch-/PR-Integration | **PENDING**, auftragsgemäß ausdrücklich verboten |

## Ausgangsstand und Phase A

Worktree: `/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning`.
Branch vor/nach der Arbeit: `feat/c27-cs50-learning-pipeline`.
HEAD und ursprüngliche Basis: `a8af1d9372eb435d3e1331c33b047d21120d57c2`.
Die vollständige C27-/R02-Implementierung lag uncommittet vor: drei geänderte
versionierte und 50 ungetrackte Dateien, insgesamt 53 manifestierte Dateien.
Alle 53 stimmten vor Änderungen hinsichtlich SHA-256, Größe und Dateimodus
mit dem verifizierten R02-Manifest überein; die Git-Pfadmenge war ebenfalls exakt.

Zuerst vollständig gelesen: R03-Findings, Summary, Gateentscheidungen,
Testevidenz und Mypy-Delta sowie die beiden ursprünglichen Probeprogramme.
Alle fünf R03-Berichte, sämtliche ergänzenden R03-Evidenzprüfsummen und alle
sechs R02-Übergabeartefakte bestanden ihre SHA-256-Prüfung. Dies ist ein
Integritäts-/Konsistenznachweis, keine extern authentifizierte Signatur.
Eingangsverzeichnisse blieben unverändert:

- `/home/OPERATOR/codex-logs/c27rollout/handoff/review-r03/`
- `/home/OPERATOR/codex-logs/c27rollout/handoff/remediation-r02/`
- ergänzende Originale: `/tmp/c27-review-r03-FWjzNNOk/`

Die unveränderten R03-Defektcharakterisierungen wurden **vor der Implementierung**
aus dem zugewiesenen Worktree mit frischem pytest-basetemp wiederholt.
`reproduce.txt/xml`: sechs bestandene Defektcharakterisierungen, also sechs
nachgewiesene Defekte und ausdrücklich keine Produktakzeptanz:

- `https://localhost./CANARY_ABC123`
- `https://private.internal./CANARY_ABC123`
- `https://127.0.0.1./CANARY_ABC123`
- `https://example.org/token:CANARY_ABC123`
- `https://example.org/session;CANARY_ABC123`
- schema-gültiger Transcript-Root nach korrektem Rehash: `KeyError(None)`.

Es wurden ausschließlich synthetische Geheimnisse verwendet. Eine anfängliche
pytest-Markerwarnung beim Aufruf der extern liegenden Originalprobe wurde durch
die explizite Projektkonfiguration in den weiteren Proben vermieden.

## F04: einheitlicher URL-Exportvertrag

Produktänderung: `src/lecture_summary/models.py`, bestehende Funktion
`exportable_source_url()` und private strukturierte Hostprüfung.
Keine Änderung des allgemeinen Content-Store-URLvertrags für andere Anwendungen.

Der tatsächliche Exportpfad bleibt: Material-Resource →
`adapter.source_slices()` → `SourceProvenance.safe_url()` → SourceRef/Result →
`SummaryStore.export_json()` beziehungsweise `export.markdown()`.
Beim Lesen vorhandener v2-Ergebnisse führt `SummaryResult` dieselbe Validierung
wieder aus. Ein eigener Test belegt die sichere erneute Ausgabe eines historischen
v2-URLlecks bei byteidentisch erhaltenen gespeicherten Resultbytes und unveränderten
Referenz-IDs. Der bestehende v1-Kompatibilitätstest bleibt grün.

Die Policy erlaubt unzweideutige öffentliche HTTP(S)-URLs mit Standardport und
einfachen Quellpfaden. Sie gibt die erlaubte Originalschreibweise unverändert aus.
Andernfalls werden **die ganze URL entfernt** und `source_url_status=withheld`
gesetzt. Fehlende URLs behalten `missing`; zulässige URLs erhalten `available`.
Markdown nennt bei Zurückhaltung ausdrücklich `Original URL: withheld`.

Die Klassifikation besteht aus mehreren unabhängigen Grenzen:

1. Strukturierte Zerlegung mit `urlsplit`; ausschließlich HTTP(S), syntaktisch
   vollständige ASCII-Autorität, keine Userinfo, Query oder Fragmente. Auch leere
   Query-/Fragmentdelimiter werden zurückgehalten. Nichtstandardports und fehlerhafte
   Ports/IPv6-Klammern werden fail-closed behandelt.
2. Hostnamen werden kleingeschrieben und um genau einen abschließenden DNS-Punkt
   normalisiert. IP-Literale müssen laut `ipaddress.is_global` global sein.
   Lokale/private/Loopback-/Link-Local-Adressen einschließlich IPv4-mapped IPv6
   fallen damit aus. DNS-Namen benötigen gültige Labels und alphabetische TLD;
   lokale Namensräume einschließlich `.localhost`, `.local`, `.internal`, `.lan`,
   `.home` und `.home.arpa` werden abgewiesen. Numerische IPv4-Kurz-, Oktal- und
   Hexvarianten, Prozentkodierung im Host, Unicode-/IDNA-Mehrdeutigkeiten,
   Einzelnamen und mehrfache Abschlusspunkte werden konservativ zurückgehalten.
3. Pfadsegmente werden einmal strikt prozentdekodiert und müssen danach aus
   unreservierten ASCII-Zeichen bestehen. Damit sind insbesondere `:`, `;`, `=`,
   kodierte Trenner, Backslashes, Kontrollzeichen und verschachtelte Kodierung
   ausgeschlossen. Ungültige Kodierung, Punkttraversal und doppelte innere Slashes
   werden ebenfalls zurückgehalten.
4. Kleine semantische Token-/Session-/Credential-Markerprüfung auf den strukturierten
   Segmenten, einschließlich getrennter API-Key-Schreibweisen. Diese Prüfung ist
   eine zusätzliche Grenze und keine alleinige beliebig wachsende Regex-Blacklist.
   Normale Begriffe wie `tokenization` bleiben zulässig.

Parserfehler werden ohne URL oder dekodierten Wert abgefangen. Es gibt keinen neuen
Log-, Warnungs- oder Ersatzmetadatenkanal für zurückgehaltene URLs. Tests prüfen
JSON, Markdown und erfasste stdout/stderr/Logs auf Canary-Lecks. Der bereits
vorhandene private SummaryStore behält seinen internen, durch F01 geschützten
Input-Snapshot für Cacheidentitäten; er wird nicht exportiert. Seine unveränderte
Aufbewahrung ist keine neue Weiterleitung sensibler URLs.

Grenzen: Diese Offline-Metadatenregel löst kein DNS auf und erteilt keine
Netzwerkberechtigung. Sie kann weder private DNS-Antworten beliebiger öffentlicher
Domainnamen noch beliebige semantisch unmarkierte Freitextgeheimnisse erkennen.
Nicht zuverlässig klassifizierbare Syntax wird zurückgehalten. Alle 81 eindeutigen
URLs aus dem bestehenden echten CS50P-Inventar und seinen Snapshots wurden gegen
die verifizierte R02-Policy verglichen: **75 vorher zulässig, 75 weiterhin zulässig,
keine verlorene öffentliche Quelle**. Die übrigen sechs waren bereits unter R02
zurückgehalten. `url-compatibility.json` enthält bei zurückgehaltenen URLs nur einen
Hash und Status, keine vollständige URL.

## T01: Root- und Parentvertrag

Produktänderung: `src/lecture_summary/reviewed_week.py`.
`WeekMaterial.parent_material_id` ist im vorhandenen Schema optional.
`WeekInventory.graph()` interpretiert `None` als Ende der Parentkette und erlaubt
neben dem Course-Root auch weitere Roots. Unbekannte Parent-IDs, Zyklen und doppelte
IDs lehnt bereits dieses Schema ab. Dieser Datenvertrag wurde nicht verschärft.

Die Summary-Verarbeitung benötigt dagegen eine explizite direkte Zuordnung jeder
heruntergeladenen Summary-Quelle zu `lecture` oder `short`. `_source_owner()` prüft
nun diese Grenze an beiden bisherigen Zugriffsorten. Eine Downloadquelle mit
`parent_material_id=None` führt deterministisch zu:
`ValueError("Summary source is a root entry; lecture/short parent required")`.
Ein unbekannter Parent und ein Parent falschen Typs haben getrennte kontrollierte
Fehler. Die Meldungen enthalten keine URLs und keine fiktiven Parent-IDs.
Die Verarbeitung bricht vor dem Anlegen des Ausgabeordners ab.

Gültige strukturelle Roots bleiben im zurückgegebenen Inventar vollständig erhalten.
Auch eine Root-Lecture beziehungsweise ein Root-Short kann seine ausdrücklich
zugeordneten Quellen besitzen. Mehrstufige Inventargraphen, etwa
Course → Week → Shorts → Short → Transcript, funktionieren unverändert.
Die Summary-Quelle selbst braucht weiterhin einen direkten Unit-Parent;
Zwischenknoten werden nicht durch erfundene IDs oder eine neue Heuristik ersetzt.

Eine durch Echtdaten aufgedeckte Vertragsnuance bleibt erhalten: dieselbe
HTML-URL darf als Wochen-/Scope-Seite und als Lecture-Seite inventarisiert sein.
Scope-Seiten unter Course/Week/Shorts bleiben im Inventar; die bestehende explizite
Lecture-/Short-Quelle wird verarbeitet. Ungültige Root-Quellen mit derselben URL
werden dabei nicht still herausgefiltert. Dieser Fall hat einen eigenen Test.
Die vorhandenen Snapshot-, Hash-, Download-, Review-, Qualitäts- und Budgetgates
bleiben wirksam; auch Limits und bestehenden Tests wurden nicht abgeschwächt.

## Phase D: Regression und Typvergleich

Vorhandene lokale Umgebung: `/tmp/c27-test-env/bin/python`, Python 3.12.12.
Keine Installation, Downloads, externen APIs oder echten LLM-Aufrufe.
Pytest verwendet `tests.offline_guard`, deaktivierte Plugin-Autoerkennung,
deaktivierten Bytecode/pytest-Cache und neue isolierte Ausgabepfade.
Echte Kursdateien werden ausschließlich gelesen; Extraktion erfolgt mit FakeLLM.
Der tatsächliche CLI-Kindprozess hat zusätzlich einen eigenen Socketguard.
Exakte Argumentlisten, Arbeitsverzeichnisse und relevante Umgebung stehen in den
jeweiligen `*-command.json`; JUnit-Dateien enthalten alle Einzelresultate.

| Gruppe | Bestanden | Skips | Verbleibende Fehler |
|---|---:|---:|---:|
| Neue R04-Regressionen | 102 | 0 | 0 |
| Bestehender Summarizer | 53 | 0 | 0 |
| Bestehende UI | 8 | 0 | 0 |
| Bestehende C27-/CLI-/Inventarverifikation inkl. Echtdaten | 36 | 0 | 0 |
| Bestehende R02-F01–F05-/Export-/Provenienzregressionen | 72 | 0 | 0 |
| Material-/Content-/Pipeline, gleiche Auswahl wie R03 | 378 | 2 | 0 |
| Ergänzende Inventarauswahl | 77 | 1 | 0 |
| R03-Invarianten, Scope-Isolation, Echtdaten und CLI-Prozess | 24 | 0 | 0 |

Die ergänzende Inventarauswahl überlappt mit 50 bestandenen Fällen und einem Skip
der Pipelinegruppe; sie liefert 27 zusätzliche bestandene Fälle. Wiederholungen
und frühe Defektcharakterisierungen werden nicht addiert. Maschinenlesbar
dedupliziert: **700 eindeutige bestandene Akzeptanz-/Regressionstests, zwei
optionale Skips, null verbleibende Testfehler** (`test-results.json`).
Die fünf alten URL-Defektcharakterisierungen sind im abschließenden unabhängigen
Probenlauf gezielt abgewählt und durch positive Withheld-Tests ersetzt; dies sind
keine Skips. Es handelt sich weiter um eigene Implementierungsvalidierung,
nicht um einen neuen unabhängigen Audit.

Skips: optionale echte Notes-HTML-Eingabe und echte Operator-Exportmatrix.
Die ZipFile-Duplikatwarnung stammt aus einem absichtlichen Kollisionsfixture.
Ein Zwischenstand scheiterte an der oben beschriebenen doppelten echten
Wochen-/Lecture-Seitenzuordnung (ein C27-Fall und zwei Echtdaten-/CLI-Proben).
Nach der Korrektur wurden alle 36 C27-Fälle, alle 102 R04-Fälle und alle 24
zusätzlichen Proben erneut erfolgreich ausgeführt. Historische Logs bleiben
sichtbar, die Zwischenfehler werden nicht als verbleibende Fehler gezählt.

Ruff: bestanden; Formatprüfung: **22 Dateien bereits korrekt formatiert**.
`git diff --check`: Exit 0. Beim Gesamtpatch bleiben die sechs bereits aus R02
bekannten historischen Dokument-Whitespacewarnungen erhalten; das R04-Delta
fügt keine Whitespacefehler hinzu.

Mypy 2.3.1, unveränderte strict-Konfiguration, gleiche drei Scopes wie R03:

| Scope | R03/R02 | R04 | Neu | Entfernt |
|---|---:|---:|---:|---:|
| `src/lecture_summary scripts/c27_reviewed_week.py` | 134 | 132 | 0 | 2 |
| Alle im Gesamtmanifest geänderten Produktionsdateien | 202 | 200 | 0 | 2 |
| Global `src` | 6106 | 6104 | 0 | 2 |

**Mypy ist weiterhin nicht grün.** Entfernt sind exakt der optionale Indexzugriff
in `verify_review()` und der untypisierte Aufruf von `public_url`, dessen bisherige
Verwendung durch die typisierte einheitliche Policy ersetzt wurde.
`mypy-delta.json` ordnet jede Diagnose mit Datei, Zeile, Fehlertyp und Meldung zu;
Zeilenverschiebungen werden über identische Quellzeilen und anschließend
vorkommensgenauen Meldungsabgleich behandelt. Keine Summenverbesserung ersetzt
diesen Vergleich. Eine im Zwischenstand durch das typisierte Owner-Ergebnis
sichtbar gewordene Literal-Diagnose wurde an der bereits geprüften Unit-Grenze
präzisiert. Der erste globale Lauf mit explizitem PYTHONPATH hatte vier geänderte
Importdiagnoseklassifikationen in unveränderten Altmodulen. Der kontrollierte
Vergleich ohne diesen zusätzlichen PYTHONPATH reproduziert die R03-Klassifikation;
auch dabei bleiben exakt 6104 Diagnosen und keine neuen Diagnosen. Beide Logs
werden zur Nachvollziehbarkeit behalten.

Echtdaten: unverändert 106 Inventarzeilen und 24 Erwartungs-IDs, vier Downloads
mit 39.845 Bytes. Functions-TXT liefert 18 Sections/18 Claims; CLI-Wiederholung
verwendet denselben Run mit null weiteren Fakecalls. Beide vollständigen
HTML-Auswahlen bleiben am unveränderten Chunklimit blockiert. ZIP-Membermapping,
fehlende Materialien, vollständige Quellenabdeckung, fachliche Abnahme,
persistente Providerbudgets und spätere Rollout-/Produktionsgates bleiben offen
(F06–F14, siehe R02 und R03). R04 erteilt keine zusätzliche Freigabe.

## Phase E: Übergabe, Rekonstruktion und Erhaltung

Neue eindeutige Ablage:
`/tmp/c27-remediation-r04-0mmhb6fz/handoff/`.
Der gewünschte Home-Handoff-Pfad liegt außerhalb der erlaubten Schreibbereiche;
der ausdrücklich erlaubte temporäre Ausweichpfad wird deshalb verwendet.
Keine vorhandene Übergabe wurde überschrieben.

Die Ablage enthält:

- `c27-full-vs-a8af1d9.patch`: vollständige C27-Änderungen gegen den ursprünglichen
  Basiscommit, einschließlich aller bisherigen uncommitteten Arbeiten und dieses
  Berichts; **55 Dateien**.
- `c27-r04-only.patch`: ausschließlich zwei Produktionsdateien, neue R04-Tests
  und dieser Bericht gegen den **byte-/größen-/modusgeprüften R02-Stand**;
  **vier Dateien**.
- `file-manifest.json`, `r04-changes.json` und `SHA256SUMS`.
- `patch-verification.json`: Forward-/Reverse-Checks und vollständige
  Baum-/Byte-/Größen-/Modusvergleiche beider Rekonstruktionswege.
- `evidence/`: Test-/Mypy-/Git-/Erhaltungsnachweise, verifizierte Eingangsberichte,
  relevante Probeprogramme und ausführbare Rekonstruktionshelfer.
- `README.md` mit den konkreten Offline-Anwendungsschritten.

Basis und R02 werden aus `git archive` und dem verifizierten alten Gesamtpatch
rekonstruiert, ausschließlich in gewöhnlichen neuen temporären Dateikopien.
Keine Git-Branches oder Git-Worktrees werden dafür angelegt. Der neue Gesamtpatch
auf Basis sowie R02-Gesamtpatch plus neues R04-Delta ergeben jeweils exakt denselben
Dateibaum wie der abschließende Worktree unter Ausschluss von Gitmetadaten,
ignorierten Laufzeitdaten und Caches. Vorwärtsprüfung, tatsächliche Anwendung,
Rückwärtsprüfung und tatsächliche Rückanwendung werden getrennt nachgewiesen.
Die Rückanwendung stellt jeweils die Basis beziehungsweise den R02-Stand wieder her.
Git-Archivmodi werden auf die Git-darstellbaren Modi 0644/0755 normalisiert.

Von den 53 vorhandenen R02-Dateien wurden nur die zwei beauftragten
Produktionsdateien verändert; alle anderen **51 Dateien bleiben byteidentisch**.
Hinzu kommen ausschließlich neuer Test und Bericht. Zwei ignorierte Ruff-Cachedateien
wurden durch die anfängliche lokale Prüfung aktualisiert und bleiben als
entbehrliche Laufzeitdaten erhalten; sie gehören nicht zu den Patches.
Alle 17 echten Eingangs-/Rohdatendateien einschließlich Dateimodi und alle alten
Übergabeartefakte sind unverändert (atime ausgenommen).

HEAD, Branch und vorhandene Worktree-Liste bleiben gleich; der ursprüngliche
Dirty-State bleibt erhalten, ergänzt um die beauftragten Änderungen.
Keine Commits, Resets, Rebases, Merges, Pushes, PRs, Downloads, Produktionsänderungen,
anderen Worktree-Änderungen oder Bereinigungen. Keine eigenen temporären
Git-Artefakte erzeugt; keine bestehenden Git-Artefakte entfernt.
Branch und Worktree müssen wegen des ausdrücklichen Integrationsverbots und des
uncommitteten Übergabestands erhalten bleiben. Dauerhafte Default-Branch-Integration
und Lifecycle-Abschluss sind **PENDING**, bis eine separat autorisierte reguläre
PR-/Review-Integration erfolgt. READY_FOR_INDEPENDENT_REVIEW bezeichnet allein
diese abgeschlossene Remediation und ihre prüfbare Übergabe.
