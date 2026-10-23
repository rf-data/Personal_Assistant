# C26-B6 Phase B: Validierung und verbleibende Voraussetzungen

23.10.2026. [Implementierung und Bedienung](course_planning.md).
Basis `da9b77db0815f0c2ab65a3e819df17200e3a3897`; eigener Branch
`feat/c26b6-course-planning`. Kein Merge oder produktiver Lauf.

## Tatsächlicher Integrations- und Entwicklungsstand

B5/#150 und Phase A/#151 sind integriert. Deren Datenmodelle, Referenzinventar,
Dokumente und CLI liegen auf der geprüften Basis vor. #149 bleibt Draft auf
`58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb`, #148 Draft auf
`f98eedd671c8a9d9eb58a3b957eda1a91713844d`. Beide Heads wurden beim Fortsetzen am
23.10. erneut geprüft. Live-Master ist weiterhin `da9b77d`.

Die Umsetzung erweitert den bestehenden B5-Planer um ProfiledWeek v2 und begrenzte
Kurs-/Preflight-Hüllen v1. SourceApproval, Material-, Receipt- und C16/C18-Schemas
bleiben erhalten. Die generische Transcriptbindung nutzt weiterhin denselben
Importer, genau eine eindeutige Section/Lecture und höchstens zwei Quellen.
Worker, Queue, Bereitstellung und produktive Ablage werden nicht erweitert.

## Testabdeckung

Die neue Suite prüft die 16 geforderten Szenarien und zusätzliche Grenzfälle:

| Bereich | Nachweis |
|---|---|
| Wochen und Kurse | Zwei unabhängige CS50P-Wochen, zweiter CS50x-Kurs, begrenzter Multi-Course-Plan, nichtnumerische Section im Referenz-Smoke |
| Identität | Gemeinsame Ressource nur einmal global gezählt; gleiche URL mit verschiedenen Rollen bleibt getrennt; erfundene Material-/Workflowreferenzen werden abgelehnt |
| Profile und Quellen | Unbekannte Kurs-ID/Adapterversion, geänderte Adapterrevision und Snapshotbytes blockieren; neue Origins/Rollen/Bedingungen werden nicht geerbt |
| Grants | Fehlende, abgelaufene, noch nicht gültige, widerrufene und veraltete/zukünftige Statusbelege; fehlender expliziter Widerrufsstatus; keine impliziten Flags |
| Code-Policy | all/complete mit vorhandenen konkreten Codegrants, irreführende Notes-/HTML-Hinweise, kodierte PY-Suffixe, ZIP sowie bekannte Codeindex-/Quellverzeichnisse |
| Child-Ressourcen | Synthetische Parent-/ID-Bindung und echte PSet-Export-IDs; fehlende C18-Rekonstruktion bleibt ausdrücklich blockiert |
| Verarbeitung | Lokale Hashabweichung bleibt als Wochenfehler isoliert; vorhandene Materialreceipts werden geprüft, nach Widerruf oder Parserconfigänderung nicht wiederverwendet |
| Transcript | Bestehender Importer für Week 1 SRT/TXT, richtige Lecture-Nummer, SRT-Zeiten erhalten und TXT-Zeiten null |
| Qualität und Versionen | Fehlende Handoffversion blockiert; isoliert vorhandene v2 wird akzeptiert; geänderte Vertragsrevision erzwingt gezielte Abnahme |
| Betrieb | Bekannter Speicher-/RAMmangel, zu großer Scope, volle Queue bei aktivem Worker, unbekannte/falsche Topologie und veraltete Beobachtungen blockieren |
| Laufzeitgrenze | Produktionsentscheidung bleibt bei fehlenden Live-Signalen blockiert, unabhängig von Planungsflags |
| Wiederholung und Reporting | Teilweise fertige Woche bleibt erhalten, Wiederholung ohne Reprocessing, bytegleiche Artefakte, konsistente Zähler/Plan-Digests und JSON-/Exit-Code-Verhalten |

Die Tests blockieren Netzwerksockets. Material-/Importbeispiele verwenden nur
synthetische Bytes und neue eigene Testroots. Der vorhandene B4-/C18-Testablauf
führt begrenzte lokale synthetische Workflows aus; keine Produktionsjobs oder
zusätzliche produktive Workerinstanz wird gestartet.

Die echten Exporttests lesen ausschließlich die sechs ausdrücklich gelieferten
Dateien unter dem lokalen `cs50_quality_review`. Raw-, Normalized- und Quality-
Dateien bleiben bytegleich. Notes: 237 Blöcke/34 Codeblöcke; PSet: 28 Blöcke und
alle fünf Aufgabenlinks. Die Child-IDs passen zum eingecheckten B5-Inventar.
Rawdateien oder private Artefaktarchive werden nicht ins Repository kopiert.

## Abschlussläufe

Die endgültigen Zahlen und JUnit-Hashes werden zusätzlich im
[maschinenlesbaren Nachweis](course_planning_validation.v1.json) festgehalten.
Die Läufe überlappen und werden nicht addiert.

| Abschlussprüfung | Bestanden | Fehlgeschlagen / Skips | Dauer |
|---|---:|---:|---:|
| Finale B6-/B5-Suite (51 + 51) | **102** | 0 / 0 | 54.63 s |
| B4, Multiformat und vollständige C18-Suite | **68** | 0 / 0 | 186.52 s |
| Isolierte #149-Kompatibilität (51 + 51 + 34) | **136** | 0 / 0 | 60.53 s |
| Wiederholung des C18-Einzelfalls | **1** | 0 / 0 | 7.25 s |

Ruff Check und Formatprüfung betreffen alle neun geänderten/neuen Python-Dateien.
Zusätzlich werden JSON, relative Dokumentationslinks, Source-/Dokumentfingerprints,
Whitespace und reguläre Commit-Hooks geprüft. Die gesamte Repositorysuite und
Hosted-CI werden nicht als ausgeführt behauptet.

## Entwicklungsbefunde und Grenzen der Nachweise

Der frühere breite Lauf über zwölf Module ergab **339 passed, 3 skipped, 1 failed**
(284,17 s). Der Fehler lag im unveränderten C18-Test
`test_stale_propagates_and_resume_preserves_existing_outputs[parser]`:
`Unavailable: Unconfirmed cleanup; dispatch quarantined`.
Ein isolierter Lauf desselben Falls auf unverändertem Master bestand (10,68 s),
ebenso die Wiederholung im B6-Branch (7,25 s) und anschließend die vollständige
B4-/Multiformat-/C18-Contractsuite. Der ursprüngliche Fehler wurde damit nicht
reproduziert; es gibt keinen behaupteten Fix seiner Ursache. Er bleibt als
intermittierender Test-/Prozessbereinigungsbefund für ein gesondertes Follow-up.
Die drei damaligen Skips betreffen das optionale Legacy-Notes-Receiptlayout und
zwei fehlende PDF-Originale. Sie sind keine bestandenen Originaldatenprüfungen.

Frühe neue Tests korrigierten zwei zu enge Erwartungen: Bei einem übergroßen
all/complete-Scope darf auch eine manuelle Referenz den Status blocked tragen;
sie erreicht weiterhin keinen Download oder Batch. Ein weiterer Zwischenlauf
scheiterte an einem versehentlich im falschen Testmodell gesetzten
`source_origin`-Feld (34 failed/9 passed), nicht an einer Freigabe-/Parserfunktion.
Nach Korrektur bestanden zunächst 43 neue Tests, danach weitere zusätzliche
Grenzfälle. Die Schlussprüfung verlangt einen ausdrücklich gesetzten
`ApprovalPolicy.revoked`-Wert und testet dessen Fehlen negativ.

Die anfängliche direkte Testwerkzeugablage unter `/tmp` war für isolierte
`python -I`-PDFprozesse nicht sichtbar; zwei PDFfälle scheiterten deshalb an
fehlenden Imports. Die zunächst aufgelöste PyMuPDF-2-Version eignete sich ebenfalls
nicht für diesen bestehenden begrenzten Worker. Für die gültigen Regressionen
wurde die bereits im Projekt verlangte Version **1.27.2.2** verwendet. Es wurden
keine Worker-/Parserlimits erhöht, um Umgebungsausfälle zu umgehen.

Zwischen dem 22. und 23.10. verschwanden die temporären Testumgebungen und
Protokolle unter `/tmp`. Der oben beobachtete breite Zwischenlauf ist deshalb
kein neu verfügbarer JUnit-Nachweis. Die Abschlussläufe und ihre XML-/Logdateien
liegen nun im eigenen Workspace-Verzeichnis `Personal_Assistant-c26b6-planning-results`.
Ein explizit unterbrochener Turn beendete zwei Schlussläufe vor JUnit-Abschluss;
nach Prüfung, dass keine eigenen Testprozesse mehr liefen, wurden sie mit neuen
eigenen Basetemp-Pfaden wiederholt. Unvollständige Läufe werden nicht als Erfolge gezählt.

Die ursprüngliche Backend-venv fehlt. Bestehende Umgebungen blieben unverändert;
der Teststarter ist eine eigene kleine venv ohne Paketinstallation. Er verweist
auf die bestehende Realpilot-Umgebung sowie bereits vorhandene lokale UV-
Cachearchive für pytest 9.1.1 und PyMuPDF 1.27.2.2 samt pytest-Abhängigkeiten.
Der Offline-Resolver konnte die gecachte PDFversion nicht zuordnen; anschließend
wurden die tatsächlich vorhandenen Metadaten und Archive direkt wiederverwendet.
Beim Fortsetzen waren keine erneuten Paketdownloads nötig. Produktionsabhängigkeiten
und Lockdatei bleiben unverändert.

## Reproduktion

Eine vorhandene Python-3.12-Testumgebung mit den bestehenden Projektabhängigkeiten,
pytest und der Projekt-PDFversion verwenden. Der neue eigene Teststarter ist nur
ein lokaler Verweis auf vorhandene Pakete, keine neue Projektanforderung.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
CS50_WEEK0_QUALITY_EXPORT=/explicit/local/cs50_quality_review \
python -m pytest -q tests/test_cs50_course.py tests/test_cs50_week_materials.py \
  -p no:cacheprovider --basetemp=/explicit/new/testroot
```

Die #149-Prüfung verwendet eine eigene detached Arbeitskopie auf `da9b77d`,
den exakten Diff von `e581e20` nach `58aec7d` und dieselben B6-Python-Dateien.
Es findet kein PR-Merge statt. Zusätzlich wird dort
`tests/test_cs50_html_projection.py` ausgeführt. Beide echten v2-HTML-Exportfälle
werden mit dem ausdrücklich angegebenen Exportroot ausgeführt; kein Ersatz durch
synthetische Daten und keine vollständige neue Produktions-Receiptkette behauptet.

## Offene Voraussetzungen und Aufbewahrung

- Fünf Aufgaben: belegte identische IDs, aber weiterhin fehlende versionierte
  C18-Bundle-/Workerrekonstruktion. Vier zusätzliche Aufgabeninhalte fehlen.
- Veraltete Transcriptreceipts bleiben wegen der bestehenden codegebundenen
  Importerrevision stale. Keine automatische Migration oder Überschreibung.
- Größere produktive Läufe benötigen den zuständigen integrierten und live
  abgenommenen Deploymenttreiber, aktuelle Worker-/Queue-/Mount-/Kapazitätsbelege
  und konkrete frische Quellfreigaben. Ein Offline-Report ist kein Permit.
- Multi-Course außerhalb des bestehenden CS50-Katalogs benötigt Adapter-,
  Content-/ACL- und Quellenreview. MIT ist nicht aktiviert.
- Speicher bleibt begrenzt; die verfügbare lokale Reserve liegt unter 5 GiB.
  Tests ändern keine produktiven Kapazitätsgrenzen und messen nicht den Hetznerhost.

Eigene Artefakte: Branch `feat/c26b6-course-planning`, Worktree
`Personal_Assistant-c26b6-planning`, isolierter Kompatibilitätsworktree
`Personal_Assistant-c26b6-compat` und Ergebnisverzeichnis
`Personal_Assistant-c26b6-planning-results`. Sie bleiben für das offene Review
erhalten. Alte Worktrees, primäre Checkouts, Git-Objekte, Archive, Bundles,
Konfigurationen, Datenbanken und Pilotdaten wurden nicht bereinigt.
Dokumente liegen bis zum normalen Review/Merge ausschließlich im Reviewbranch;
keine Masterintegration oder Bereinigung wird als abgeschlossen ausgegeben.
