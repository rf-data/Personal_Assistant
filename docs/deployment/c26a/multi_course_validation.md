# C26-B6: Validierung und offene Voraussetzungen

22.10.2026. Phase A auf Master `e581e20`, eigener Branch
`docs/c26b6-rollout-readiness`. [Architektur und Entscheidungen](multi_course_readiness.md).

## Durchgeführt

| Prüfung | Ergebnis |
|---|---|
| Live-GitHub-Basis und B5-Branch | Master `e581e201ef6b3d6c06aca14de845e0687d213b37`, B5 `c6415d3c3f0f77f457b4b461f6841a385e827d5c` |
| B5-PR | [#150](https://github.com/rf-data/Personal_Assistant/pull/150) nach erfolgreicher automatischer Freigabeprüfung erstellt; offen, nicht gemergt |
| Abhängigkeiten | #148 und #149 weiterhin offene Drafts; #146 offen; keine Produktionsintegration behauptet |
| B5-Sicherung | `git bundle verify` bestanden; alle 1.044 Archivdateien gegen Git-Blob-IDs des veröffentlichten Commits geprüft |
| B5-Quellfingerprints | Alle fünf Einträge der vorhandenen maschinenlesbaren Validierung stimmen |
| Neue lesende Offline-Smokes | **2 bestanden**: Fixture-Inventar 17 Ressourcen/24 Varianten, mit Originalexporten 21/28; jeweils ready=0, keine Ausführung |
| Vorhandene Originale | Alle sechs Exportdateien vor der Discovery anhand dokumentierter Bytes/SHA geprüft; keine Kopie in Git |
| Worktrees | Primärer Backend- und UI-Checkout sauber; historische Änderungen, Konflikte und nicht lesbare RAM-Gitverweise erhalten |
| Implementierungsumfang | Ausschließlich neue B6-Dokumentation; keine Änderung an B5, Parsern, Jobs oder Schemata |

Die zwei neuen Smokes liefen mit Python 3.12.12 aus der bestehenden Umgebung
`Personal_Assistant-c26-realpilot/.venv`; Netzwerkverbindungen wurden im Prozess
blockiert. Die Discovery las lediglich die bereits vorliegenden Dateien. Die
Umgebung wurde nicht verändert und kein Produktionsjob ausgeführt.

Die frühere Backend-`.venv` ist aktuell nicht vorhanden. Die untersuchten
alternativen vorhandenen Umgebungen enthalten kein pytest. Daher wurde die
pytest-Suite **nicht erneut ausgeführt** und keine neue Paketumgebung installiert.
Der erste Archivleseversuch mit System-Python 3.11 scheiterte an dessen fehlendem
`tarfile.extractall(filter=...)`; anschließend wurden ausschließlich reguläre,
pfadgeprüfte Archivdateien in eine eigene temporäre Auditkopie gelesen. Ein erster
Verifikationsaufruf am früheren Backend-Pythonpfad konnte nicht starten. Diese
Umgebungsbefunde sind keine fehlgeschlagenen B5-Fachtests.

Historische, quellengebundene B5-Nachweise: **358 bestanden/3 übersprungen** in
zwölf betroffenen Modulen, finale B5-Suite **51 bestanden**, isolierte #149-
Kompatibilität **85 bestanden**. Diese Resultate stehen im unveränderten B5-Commit
unter `docs/deployment/c26a/complete_week_validation.md` und `.v1.json`; sie
überlappen, werden nicht addiert und sind keine neuen B6-Regressionsresultate.
Die drei Skips betreffen das optionale Legacy-Notes-Receiptlayout und zwei nicht
gelieferte PDF-Originale. Die zwei echten HTML-Exportfälle liefen im damaligen
Kompatibilitätslauf tatsächlich. Ein vollständiger Produktionsplan-/Receipt-
Handoff ist damit weiterhin nicht neu geprüft.

## Verbindliche Testmatrix für Phase B

Alle Szenarien verwenden lokale Fixtures, Mock-Kapazitäts-/Widerrufsbelege und
isolierte neue Ablageroots. Netzwerk und automatische Beschaffung werden als
Fehlertripwire gesperrt. Die folgenden Fälle sind **geplant, noch nicht als B6-
Tests implementiert oder bestanden**.

| Nr. | Szenario | Nachzuweisendes Ergebnis |
|---|---|---|
| 1 | Mehrere Wochen desselben Kurses | Ein allgemeiner Planer; stabile Section-Reihenfolge, begrenzte kleine Batches, keine Week-0-Sonderfunktion |
| 2 | Doppelte Ressourcen über Wochen | Gleiche Materialbindung nur einmal ausführbar, mehrere Wochenreferenzen; unterschiedliche Parents/Rollen/Kurse nicht verschmelzen |
| 3 | Neuer Kurs mit bekanntem Adapter | Expliziter Kurs-/ACL-/Profilumfang und Strukturbeleg erforderlich; passende Domain allein genügt nicht |
| 4 | Unbekannte Quellenstruktur | Nachvollziehbarer Adapterblocker, keine generische HTML-Verarbeitung als Fallback |
| 5 | Ergebniswiederverwendung | Exakte Raw-/Receipt-/Plan-/Config-/Quality-Digests; unveränderte Bytes und keine neue Submission; manipuliertes Ergebnis blockiert |
| 6 | Ablauf oder Widerruf | Abgelaufener, widerrufener oder veralteter/unbekannter Status blockiert auch nach zuvor grünem Report; v1-Textreferenz genügt nicht für Seriengrants |
| 7 | Material außerhalb Scope | Neue Origin, Redirect, Rolle, Format, Kurs oder Zweck erhält keinen geerbten Grant |
| 8 | Codeindex, auch mit all/complete | Ausschließlich Referenz, keine Traversierung, keine Download-/Batch-/Workerübergabe |
| 9 | ZIP/PY und irreführende Hinweise | Suffix-/Pfad-/Encodingvarianten trotz Notes-/HTML-Hinweis und Grants gesperrt; Code-PDF separat als PDF |
| 10 | Defekte Links oder verschachtelte Listen | Quality blockiert verlorene/duplizierte Referenzen, ungültige Parents, Hierarchiefehler und verlorene Codezeichen |
| 11 | Parser-/Adapter-/Schemawechsel | Alter Preflight ungültig; Kategorie 3/4 mit Regression bzw. gezieltem Pilot; keine stale Reuse |
| 12 | Zu wenig Speicher | Reserve plus geplanter Mehrbedarf auf jedem betroffenen Dateisystem; keine automatische Limiterhöhung |
| 13 | Aktiver Worker, volle Queue | Keine Submission und kein Workerstart; fehlende Queue/Heartbeat oder Deploymentbelege blockieren; Zustand vor Dispatch erneut prüfen |
| 14 | Teilweise fertige Wochen | Unabhängige verifizierte Ergebnisse bleiben; betroffene Pflichtressourcen verhindern Completion; Unique- und Wochensummen konsistent |
| 15 | Fortsetzung nach kontrolliertem Fehler | Bestehender Controllerstatus und frischer Preflight; kein Doppeljob bei konkurrierender Wiederholung; unvollständige Publikation nicht reparieren |
| 16 | Bestehende Week-0-Artefakte | Vorher-/Nachher-Hashes aller ausdrücklich gelieferten Originale, Receipts und Resultate identisch; keine Migration in bestehenden Pilotroots |

Zusätzliche Grenzfälle: leere Auswahl, übergroße Sectionliste, zirkuläre Parents,
konfligierende Bindungen bei gleicher ID, gleiches Medium mit unterschiedlichen
Varianten, veraltete Betriebsbelege, Symlinks, veränderte Originalbytes zwischen
Plan und Submission, Scope-/Grantänderung während einer Fortsetzung, SRT-Zeiten
gegen TXT-Nullzeiten sowie Unterscheidung offline-ready/production-blocked.

Die gezielten B5-, Material-, Transcript-, C18-, Quality- und #149-Regressionen
laufen nach der Integration erneut in der vorhandenen geeigneten Testumgebung.
Reale PDF-/Medienoriginale werden nicht eigens für Tests heruntergeladen. Jeder
fehlende optionale Input wird als Skip mit Grund ausgewiesen. Stop-Regeln und
Entscheidungspriorität benötigen echte negative Tests, keine Tests, die nur neue
Implementierungszeilen nachbilden.

## Gap-Analyse und Betreiberentscheidungen

| Priorität | Fehlende Voraussetzung | Erforderlicher Nachweis |
|---|---|---|
| Vor Phase B | B5 außerhalb Master | Review und tatsächliche Inhaltsintegration von #150; danach neuer Baseline-/Schnittstellencheck |
| Vor neuer Aufgabenverarbeitung | C18 kann Child-IDs aus PSet-Export nicht rekonstruieren | Versionierte opt-in Discovery-/Bundlebindung, identische Worker-IDs, Rückwärtskompatibilität |
| Vor Multi-Week-Transcript | CS50P/Week-0-Festcodierungen | Abgenommene Lecture-/Sectionbindung im vorhandenen Adapter mit SRT/TXT-Regression |
| Vor Serienfreigaben | Kein prüfbarer Ablauf-/Widerrufskontext in SourceApproval v1 | Review der Policyhülle und Ableitung konkreter Grants; aktuelle Prüfung vor jedem Schritt |
| Vor erstem Offline-Mehrwochenpilot | Lokale Snapshots/Referenzen der tatsächlich gewählten weiteren Wochen, geeignete pytest-Umgebung | Expliziter kleiner Scope, passende Profile, Testmatrix und gebundene Ergebnisse |
| Vor Multi-Course | Geschlossener Katalog, Content-/C16-ACLs und neue Profile | Konsistente Kursmigration; Harvard-Stichprobe bzw. eigener MIT-Offlineadapter |
| Vor größeren produktiven Läufen | Deploymentdriver und realer Annahme-/Wechselschutz nicht abgenommen | #146-Abnahme mit Live-Revision/Instanz, persistenten Roots und bestehendem Worker/Queue |
| Vor jeder konkreten Ausführung | Aktuelle Rechte, Raw-/Reuse-Belege und Kapazität | Frischer Batch-Preflight; keine Annahme aus Kursnamen, altem Erfolg oder diesem Dokument |

Betreiberentscheidungen: B5/HTML-Projektion reviewen; erste Kurs-/Wochenauswahl,
Pflichtmaterialien und unabhängige Fortsetzung festlegen; konkrete Nutzungsrechte,
Zweck, Widerruf, Aufbewahrung und Kapazitätsbelege benennen. Kein SSH, kein neuer
Kursdownload und kein produktiver Pilot ist durch diesen Dokumentationsreview
freigegeben. Der lokale freie Platz liegt unter der B5-Reserve von 5 GiB; dies
ist keine Messung des Produktionshosts und kein Grund, die Reserve abzusenken.

## Begrenzte Speicherbereinigung und Wiederherstellung des PR-Abschlusses

Der Betreiber autorisierte ausschließlich ungenutzte temporäre Python-/Testcaches
in lokalen Personal-Assistant-Arbeitskopien. `df -h`, `df -i`, `du`, Hostprozesse,
Arbeitsverzeichnisse und offene Cache-Dateien wurden geprüft. Auf diesem Dateisystem
meldet `df -i` durchgehend 0/0/0 und keinen Nutzungsprozentsatz; daraus lässt sich
keine Inode-Erschöpfung ableiten.

Unmittelbar vor der Bereinigung waren **4.262.862.848 Bytes**, danach
**4.266.942.464 Bytes** verfügbar; `df -h` zeigt jeweils rund **4,0 GB**.
88 ungenutzte `__pycache__`-/`.pytest_cache`-/`.ruff_cache`-Verzeichnisse mit
449 regulären Cache-Dateien und 4.923.392 allokierten Bytes wurden entfernt.
Die Nettoänderung des freien Dateisystems weicht von der Summe der Cacheblöcke ab.
Ein Cache in `Personal_Assistant-audit` blieb mangels prüfbarer Git-Zugehörigkeit
erhalten. Symlinks, getrackte Einträge, jüngst veränderte Caches und aktive Projekte
waren von der Bereinigung ausgeschlossen.

Alle `.venv`-Umgebungen, Git-Artefakte, Archive, Bundles, Pilotdaten, Datenbanken,
Konfigurationen und `.codex/thread-writer-locks` blieben unangetastet. Der lokale
Detailnachweis liegt neben der B5-Sicherung in `cache-cleanup-report.json`.
Die automatische Freigabeprüfung konnte anschließend wieder ausgeführt werden;
die Erstellung von PR #150 war erfolgreich. Ein gezielter Eingriff an Codex-
Sperrdateien oder eine vollständige Diagnose des früheren ENOSPC war nicht nötig.

## Aufbewahrung und Abschlussgrenze

Neue eigene Git-Artefakte: Branch `docs/c26b6-rollout-readiness` und Worktree
`Personal_Assistant-c26b6-readiness`. Die B5-Auditkopie liegt separat unter `/tmp`;
sie enthält keine neue Verarbeitung produktiver Artefakte. Bestehende Archive,
Bundles, fremde Branches, Worktrees und unbekannte Dateien wurden nicht entfernt.
Reguläre Commit-Hooks werden mit dem vorhandenen Pre-commit aus der bestehenden
`ai-job-search/.venv` ausgeführt, ohne diese Umgebung zu verändern.

Dokumentations-/JSON-/Link-/Whitespaceprüfungen werden für den Review ausgeführt.
Der neue Branch und Worktree müssen bis zur geprüften Integration erhalten bleiben.
Es erfolgt kein Merge. B6 ist als Phase A reviewbar; automatisierter Preflight,
Mehrwochenausführung, neue Adapter und die oben geplanten Tests bleiben als Phase B
ausstehend. Eine erfolgreiche PR-Erstellung ist keine fachliche oder produktive
B6-Gesamtabnahme.
