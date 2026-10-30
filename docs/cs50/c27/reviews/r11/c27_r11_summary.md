# C27-R11 – Commit Scope Resolution & Integration Design

**19/19 Reviewentscheidungen als Empfehlungen aufgelöst, alle drei Konflikte entworfen, Commitumfang definiert. Integrationsvorbereitung: READY_FOR_IMPLEMENTATION_APPROVAL. Produktion: NOT_APPROVED. Keine Implementierung oder Gitmutation.**

Empfohlen ist ein eigener Namespace **src/c27_learning_summary** für die Learning-Pipeline sowie **tests/test_c27_learning_summary.py** für ihre zentrale Suite. Acceptance/fix behält seine getrennten Catalog-/Claim-/SummaryService-Verträge unter src/lecture_summary; keine Implementierung ersetzt die andere. Gemeinsamkeiten bei Hash-/Quellenbindung rechtfertigen wegen inkompatibler Auswahl-, Review-, Cache-, Sicherheits- und Exportmodelle keinen automatischen Adapter.

## Die 19 Dateientscheidungen

15 historische Belege unverändert erhalten; vier Dateien nach begrenzter Änderung übernehmen (drei Konfliktpfade an neue Zielorte, Markdownbeispiel mit sechs entfernten Schlussleerzeichen). Keine der 62 R10-Inhaltsquellen vollständig verwerfen. Die JSONdatei enthält **für jede der 19** Zweck, ursprünglichen R10-Grund, konkrete Abschnitts-/Zeilenbelege, Pfad-/Credential-/Beispiel-/Statusbewertung und erforderliche Anpassung; alle 62 Kandidaten werden zur exakten Scopeabdeckung geführt.

| R10-Reviewdatei | Empfehlung |
|---|---|
| `docs/cs50/c27/handoff.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/real_data_acceptance.v1.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r02.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r04.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r06.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/remediation_r08.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/initial-integration.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/pipeline-regression.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/review-final.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/test-results/summarizer-final.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/cs50/c27/validation.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/example-summary.json` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/example-summary.md` | INCLUDE_AFTER_CHANGE |
| `docs/lecture_summary/operations.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/test-results.txt` | KEEP_AS_HISTORICAL_EVIDENCE |
| `docs/lecture_summary/validation.md` | KEEP_AS_HISTORICAL_EVIDENCE |
| `src/lecture_summary/__init__.py` | INCLUDE_AFTER_CHANGE |
| `src/lecture_summary/models.py` | INCLUDE_AFTER_CHANGE |
| `tests/test_lecture_summary.py` | INCLUDE_AFTER_CHANGE |

Lokale Home-/tmp-Angaben empfehlen wir als historische nicht geheime Lauf-/Ortsprovenienz bewusst zu erhalten, mit verbindlicher Einordnung über eine neue aktuelle Reviewübersicht. Ihre alten Befehle und Freigabetexte gelten nicht heute. R04/R06-URLregeln und R08/CAP-BLOCKED-Zustände sind historisch; heutige begrenzte technische Referenz ist R09. Relative Fixturepfade sind nach R08 zulässig. Der v1-JSONexport bleibt bytegleich; seine synthetische Freigabe ist keine Kursfachabnahme. Sechs MD-Schlussleerzeichen nur in einer offen deklarierten Ableitung entfernen, Originalexternbelege erhalten.

## Zielbasis und Abhängigkeiten

HEAD und gespeichertes origin/master: **a8af1d9372eb435d3e1331c33b047d21120d57c2**. Lokaler master: **c1007efdbac3c1544020f328a3a1347e481797ba**, 173 Commits zurück. fix/c27-acceptance-exports: **a0d3ebf7f64d44dd843f1848e70dc70a3a3af835**; gemeinsame Basis **e502aa915ad0e928dbe7e92eacd44fff0152912b**, HEAD/fix 12/19. origin/HEAD fehlt. **REMOTE_HEAD_UNVERIFIED**: tatsächlicher GitHubstand, PRs, Reviews und Schutzregeln wurden ohne Netzwerk nicht bestimmt.

Alle drei Konfliktpfade fehlen auf gespeichertem origin/master. Die branchcommittete Learning-Seite enthält sie ebenfalls noch nicht; analysiert sind die tatsächlichen unversionierten Arbeitsdateien. Die drei add/add-Konflikte betreffen __init__.py, models.py und tests/test_lecture_summary.py. __init__.py hat in beiden Varianten ausschließlich Docstringinhalt; seine Bedeutung liegt in der Paketidentität, nicht in vorhandenen Reexports.

CS50P07/08 sind spätere Fortsetzungen, keine bereits integrierte Vollvoraussetzung. Vier selektierte Komponenten stimmen erneut bytegleich mit lokalem 143d3412c668bb652eba7929742a3a886031c372 überein. C27b→C27c→fix ist die getrennte Acceptance-Fortsetzung. Vollständige lokale relevante Ref-/Merge-Base-/Pfadtabellen im Integrationsdesign und evidence/branch_dependencies.json; keine Forderung, fremde 19 Commits zu integrieren.

## Konkreter Umfang und Folgeablauf

**83 geplante Zielpfade**: 62 ursprüngliche Inhaltsquellen nach elf Pfadumbindungen plus 21 ausdrücklich aufgezählte Zusätze (20 neue Dateien, eine bestehende Hookkonfiguration). C1: 34 aktive Code-/Konfig-/Test-/Fixturedateien; C2: 30 historische Dokumente; C3: 19 Review-/Status-/Bedienungs-/Manifestdateien. Exakte Quellen, Zielpfade und 21 Pfadausschlüsse stehen im Commitplan/JSON. Keine Verzeichnisfreigabe und kein pauschales Staging.

Notwendige Anpassungen: vollständige aktive Import-/Monkeypatch-/Konfigpfadumstellung, neue sinnvolle Koexistenztests, additive genaue Ignoreausnahmen, deklarierte MD-Normalisierung, aktueller Historienindex/Bedienung und finales Zielmanifest. Historische Übergabemanifeste bleiben unverändert: docs/lecture_summary/handoff-files.json bindet 27 alte Dateien (acht heute abweichend), docs/cs50/c27/handoff-files.v1.json bindet 50 (zehn heute abweichend). Sie werden weder neu versiegelt noch als heutiger Zustand ausgegeben.

Nach späterer Freigabe: tatsächliche Livebasis und Regeln prüfen → eigener neuer Taskbranch/-worktree → genehmigte Änderungen und Dokumente vorbereiten → gezielte Offlinevalidierung → exakte Indexprüfung → drei Commits → regulärer PR nach master → erlaubte Reviewintegration → tatsächliche lokale/live Inhalte und Dokumente prüfen → erst dann eng begrenzter Lifecycle eigener neuer Git-Artefakte. Bestehender Learning-Branch/-worktree, MAINT-Bestände und Acceptance-Linie bleiben ausdrücklich erhalten. Rollback über regulären Revert-PR, keine Daten-/Store-/Reviewlöschung.

## Evidenz, Validierung und Erhaltungsgrenze

R10-Inventar vollständig verarbeitet, alle 62 aktuellen Kandidatenhashes erneut passend. Die 19 Reviewdateien sowie konkurrierende Modelle, zentrale Tests, Service, Validatoren und relevante Export-/Quellenpfade wurden inhaltlich geprüft. Keine Produkttests oder allgemeine Regression ausgeführt: keine neuen Produktbytes. CAP 23/23 plus Canary und R09 6/6 bleiben geerbte historische Evidenz; die geplante Namespacefassung und Acceptance erhalten daraus keine automatische Abnahme. Week 0 PARTIAL, Multiweek/Multicourse PLANNING_ONLY, globale Mypy-Schuld historisch 6.104, Produktion NOT_APPROVED.

Berichtsprüfung: sechs Pflichtberichte plus SHA256SUMS, syntaktisch gültiges JSON, exakt 19 individuelle Reviewentscheidungen, vollständige 62-Quellen-/83-Zielabdeckung, drei Konfliktabschnitte, passende Gates, SHA-256 aller Paketdateien. Endergebnis und gezielter Erhaltungscheck stehen in evidence/validation.json. SHA256SUMS enthält alle Paketdateien außer sich selbst; zusätzliche Belegdateien liegen unter evidence und sind keine zusätzlichen Commitkandidaten. Hashes sichern Integrität, keine externe Signatur.

Gezielter Vor-/Nachvergleich umfasst Status, Branch, Refs, Indexhash, Worktreezuordnungen, alle 62 Kandidatenbytes und Hashes der tatsächlich genutzten Berichte. Kein neuer vollständiger Metadaten-/Rohdaten-/Handoff-Sweep, keine Behauptung einer solchen Vollprüfung. Repo-, Produkt-, Test- und Dokumentdateien wurden ausschließlich gelesen. Kein Staging, Commit, Push, Fetch, Checkout, Merge, Rebase, Cherry-pick, Reset oder andere Gitmutation, keine Netzwerk-/Provider-/Downloadaufrufe und keine Löschung. Keine Änderungen an anderen Worktrees.

Berichtspaket: **/tmp/c27-r11-cjxf689_**. Es liegt außerhalb des Worktrees unter der erlaubten Schreibwurzel /tmp, weil der Home-Handoffpfad hier nicht schreibbar ist. /tmp ist kein dauerhaftes Backup. Paket und bestehende Handoffs bleiben erhalten; dauerhafte Übernahme und Dokumentintegration nach master sind gesonderte Folgearbeit, durch das ausdrückliche R11-Verbot heute ausgeschlossen. Keine eigenen Git-Artefakte erstellt oder entfernt. R11 als Berichtsauftrag ist abgeschlossen, der Projekt-/Integrationslebenszyklus bleibt pending.

Dateien: c27_r11_file_decisions.json, c27_r11_conflict_analysis.md, c27_r11_integration_design.md, c27_r11_commit_plan.md, c27_r11_gate_decisions.md und dieses Summary; SHA256SUMS bindet das vollständige Paket.

Ergänzender konkreter Prüfbefund: Der aktive end-of-file-fixer würde drei absichtlich LF-lose historische/Fixturedateien verändern. Der endgültige Plan enthält deshalb .pre-commit-config.yaml als ausdrücklich reviewte 83. Datei mit Ausnahme exakt dieser drei Pfade ausschließlich bei diesem Hook. Andere Hooks einschließlich trailing-whitespace bleiben aktiv; Originalbytebindung und MD-Normalisierung bleiben nachprüfbar. Es wurde keine Hookkonfiguration geändert oder ein Hook umgangen.
