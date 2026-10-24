# C27 – Implementierung und automatisierte Prüfung

24.10.2026. Isolierte C27-Arbeitsstände auf Backend `e502aa9` und UI `e4be7a2`.
Diese Lieferung ist ein lokaler benutzbarer MVP; keine Produktionsfreigabe.

## A. Implementierung

`src/lecture_summary/` enthält versionierte Summary-/Auswahl-/Provenienzmodelle,
begrenzte Source Collection, gemeinsamen Mock-/LLM-Service, Quality Gate,
isolierten JSON-Cache und Markdown-/vollständigen LaTeX-Export.
`scripts/lecture_summary.py` registriert ausdrücklich eine lokale Quelle,
inventarisiert read-only oder erzeugt Exporte. Bestehende Transkript-, Material-,
Knowledge-, ContentLocator-, Hash-, LLM-Budget- und Storagekomponenten werden
wiederverwendet. `tools_materials.storage` wird um registrierte Lese-/Schreibroots
erweitert; der globale C16-/C26-Schreibvertrag bleibt unverändert streng.

UI: vorhandener `app_admin.py`, Anmeldung und Rollen, neue lokale Summarizer-
Ansicht, abgesicherter Core-Adapter mit scalar/JSON-Schnittstelle. Kein zweiter
Streamlit-Server, öffentlicher Endpunkt oder produktiver Jobstart. Keine
Dependencies oder Lockdateien im Produkt geändert.

Details, Startanleitung, tatsächliche Inventur und der zehnteilige Vorschlag
zur späteren Storageharmonisierung: [C27-Anleitung](c27_lecture_summary.md).
Die Änderungen gehören ausschließlich in separate C27-Draft-PRs beider Repos.
Lieferung: [Backend-Draft #158](https://github.com/rf-data/Personal_Assistant/pull/158)
und [UI-Draft #21](https://github.com/rf-data/personal-assistant-ui/pull/21).

## B. Demonstration

Die tatsächlich vorhandene Loviscach-Lektion `mathe_1 / 01.01.1` wurde rein lokal
mit `mock-extractive-v1` verarbeitet. Eingang:

`loviscach/mathe_1/transcripts/01.01.1_drei_Arten_Mathematik.json`

- 25.028 Bytes, 102 Segmente, 5.112 Textzeichen.
- SHA256 `95f20e193b0f7ebe30d9171f785f070fb05eeb69f490bcb527d55985f640ea87`.
- Vorher-/Nachherhash identisch; kein Modellaufruf oder Upload.
- CLI erzeugte Markdown, vollständiges LaTeX und Summary-JSON in der privaten
  temporären Demo `/dev/shm/c27-loviscach-demo`.
- Auch der kanonische Streamlit-AppTest wählte diese echte Quelle aus,
  generierte die Mock-Zusammenfassung und prüfte beide Downloadbuttons.
- Ergebnisstatus `needs_review`; keine fachliche oder mathematische Abnahme.

Die privaten Exporte/Transkripttexte werden nicht eingecheckt. Die RAM-Demo ist
temporär; für den normalen Betrieb die Anleitung zur erneuten lokalen
Registrierung verwenden. Alle automatisierten Tests verwenden synthetische
Quellen. Das vorhandene synthetische Importbeispiel wird ausdrücklich so bezeichnet.

## C. Qualität und Nachweisgrenzen

Abschließende Läufe (überlappen; Zahlen nicht addieren):

| Lauf | Ergebnis |
|---|---|
| C27-Backendfälle | 56 eigenständige Fälle, einschließlich des abschließenden Abbruchtests bestanden |
| Finaler Fokus: C27, Rootpolicy und Material-E2E | 94 bestanden, keine Fehler/Skips |
| Zusätzlich exakte Backend-Lockpins: C27 und Rootpolicy einschließlich abschließendem Abbruchtest | 90 bestanden, keine Fehler/Skips |
| Erweiterte Backendregression: Lecture/Discovery/Course, Transcript, Material, C18, C26, Rootpolicy und C27 | 384 bestanden, 1 opt-in Skip; zunächst 3 fehlende PyMuPDF-Dependencyfälle, danach im finalen Fokuslauf bestanden |
| Vollständige UI-Suite einschließlich C27-AppTests | 182 Fälle ausgeführt: 157 bestanden, 25 vorhandene opt-in E2E-Skips |
| C27-Streamlit-Fälle | Alle 6 bestanden; sind in den 157 UI-Erfolgen enthalten |
| Reale Loviscach-Mock-Demo über CLI und Streamlit-AppTest | Bestanden, beide Exporte verfügbar, Eingang unverändert |
| Ruff check/format und Git diff check für geänderte Dateien | Bestanden |
| Optionaler realer LuaLaTeX-Kompilierungssmoke | Nach 30 Sekunden abgebrochen; keine erfolgreiche PDF-/Engineabnahme behauptet |

Der Backend-Skip stammt aus `test_cs50_course.py`: Betreiberoriginale für den
optionalen Realmateriallauf sind nicht ausdrücklich bereitgestellt. Historische
CS50-Pilotdaten wurden nicht dafür geöffnet. Die 25 UI-Skips benötigen separate
`C16_REPO/C16_PYTHON`- bzw. `REVIEW_BACKEND_REPO/REVIEW_BACKEND_PYTHON`-Konfiguration.
Sie sind keine als bestanden ausgegebenen produktiven Integrationsnachweise.

Prüfumfang umfasst Einzel-/Dreifachauswahl, Auswahlgrenzen, fehlende/ungültige
Quellen und IDs, widersprüchliche Metadaten, gemeinsame Materialien, Mock-LLM und
Mock-HTTP, ein begrenzter Aufruf/keine Retries, defekte/verweigerte/trunkierte
Modellantworten, Abbruch vor/nach Dispatch, Quellen-/Formelunsicherheit,
Cachehit/-Invalidierung/-Korruption, Sourceänderungen während Generierung,
Unicode/TeX-Escaping, sichere Downloadnamen und keine Eingangsänderungen.
Storagefälle prüfen unterschiedliche Roots/Storage-IDs mit identischen
Inhaltsidentitäten, Traversal, Symlinks, fehlende Mounts, read-only,
verschachtelte Mounts und den unveränderten C16-/C26-Schreibvertrag.
Die Inventur wird an einem ausdrücklich künstlichen Provider-/Kursverzeichnis
mit echten Dateien und separat fehlenden Metadatenreferenzen demonstriert.

Die erste breite UI-Prüfung erkannte den direkten Backendimport in einer
Admin-Komponente. Die lokale Bindung wurde in den authentifizierten Core-Adapter
verlagert; der vorhandene Architekturtest bleibt unverändert und besteht.
Ein früherer Backendlauf mit bloßem `PYTHONPATH` hatte 17 Guardianfehler, weil
bereinigte Kindprozesse keine Dependencies fanden. Das echte isolierte Venv
behebt den Testaufbau, ohne Guardian-/Produktionsregeln zu ändern.

### Testumgebung

Python 3.12.12; Streamlit 1.65.0 und alle UI-Abhängigkeiten exakt aus `uv.lock`.
Zusätzliche Backend-Testpakete ebenfalls aus dessen Lock mit SHA256-Wheelprüfung:
pytest 9.1.1, PyMuPDF 1.28.2, BeautifulSoup 4.15.0, soupsieve 2.9.2 u.a.
HTTPX 0.28.1, pydantic-settings 2.15.0. In der kombinierten UI-Umgebung wird
Pydantic 2.14.0/core 2.50.0 aus dem UI-Lock genutzt; der Backend-Lock pinnt
2.13.4/core 2.46.4. Beide erfüllen den Backend-Dependencyvertrag. Zusätzlich wurden
alle 56 C27-Fälle und die 34 Rootpolicyfälle mit den exakten Backendpins geprüft:
90 bestanden, keine Fehler/Skips. Es bleibt keine Pydantic-Pinabweichung in diesem
zusätzlichen Backendnachweis; die kombinierte UI-Prüfung verwendet deren eigene Pins.

`uv sync`/pip/Git und schreibende Testfixtures scheiterten lokal wiederholt mit
ENOSPC, obwohl `df` freie Bytes zeigte. Es wurden keine alten Dateien, Worktrees,
Venvs oder Daten bereinigt. Der sichere Testaufbau liegt deshalb ausschließlich
unter `/dev/shm/c27-*`: hashgeprüfte gelockte Wheels, echtes Venv und private
synthetische Fixtures. Es wurden keine schweren Systempakete installiert.
Der Compiler-Smoke verwendete die vorhandene Engine, `-no-shell-escape`,
Zeit-/Speicher-/Dateigrößenlimits und private RAM-Ausgabepfade. Das Produkt
kompiliert kein PDF und benötigt keinen TeX-Dienst.

Reproduzierbare Testauswahl im normal eingerichteten Backend:

```bash
uv run pytest tests/test_lecture_summary.py tests/test_lecture_summary_contract.py \
  tests/test_runtime_paths.py tests/test_cs50_material_e2e.py
```

Breiter Lauf zusätzlich: `test_cs50_material_contracts`, `test_cs50_material_mapping`,
`test_cs50_material_html`, `test_official_transcript_import`,
`test_transcript_unknown_time`, `test_cs50_workflows`, `test_c26_storage_preflight`,
`test_c26_copy_inventory`, `test_cs50_selection`, `test_c26_integrated_pipeline`,
`test_cs50_multiformat`, `test_cs50_lecture_adapter`, `test_cs50_course`,
`test_cs50_discovery` (jeweils `tests/<name>.py`).

Reale didaktische Modellsynthese, Inhaltsvollständigkeit und mathematische
Richtigkeit bleiben fachlich ungeprüft. Ein gültiges JSON, korrekt zitierte
Quellen-ID oder syntaktisch gültiges LaTeX ersetzt keinen inhaltlichen Beleg.
Der Mock ist bewusst eine Extraktdemo. Andere Legacy-JSON-Formate und alle
Nicht-CS50-Dateien wurden nicht pauschal fachlich oder strukturell abgenommen.
Tatsächlich verfügbare Kurse/Dateien und ihre Voraussetzungen stehen in der
Inventurtabelle der Anleitung; Metadatenverweise sind getrennt von vorhandenen
Dateien ausgewiesen.

## D. Nächste Schritte und Lifecycle

Vor einer späteren produktiven Integration fehlen insbesondere ein freigegebener
authentifizierter Summary-Service-/Jobvertrag, Source-/Course-ACLs, kontrollierte
Quellenregistrierung/Kopien, konkrete Serverroots/Mountidentitäten, Betriebs- und
Modellbudgets, Cancellation/Audit und die gesonderte C16-/C26-/Deploymentfreigabe.
Danach bieten sich visuelle Formelprüfung, weitere explizite Materialien,
hierarchische Verarbeitung großer Quellen, geprüfte didaktische Evaluation und
separat versioniertes Quellen-Enrichment an. Keine dieser Erweiterungen wurde
automatisch aktiviert.

Geschützte Drafts sind read-only geprüft: Backend #148/#149/#156/#157 und UI #20.
Abschließender API-Vergleich: alle fünf Head-SHAs, Beschreibungen und Draftzustände
stimmen mit der ersten C27-Inventur überein; sämtliche Drafts blieben unverändert.
Keine SSH-/Hetzner-/Coolifyaktion, keine Produktivqueue/-datenbank, kein Download,
kein externer Quellenbezug, kein Merge/Ready/Auto-Merge und keine Migration.

Aufgabenartefakte bleiben wegen offener Draftreviews erhalten: die beiden
`feat/c27-lecture-summarizer`-Branches und die C27-Arbeitsstände. Normale lokale
Git-Metadaten meldeten ENOSPC; reguläre Commits werden deshalb über die getrennten
`/dev/shm/c27-backend-git/.git` und `/dev/shm/c27-ui-git/.git` mit den C27-
Arbeitsverzeichnissen erstellt. Diese Metadaten sind temporär; Remote-Draftbranches
sichern die Commits dauerhaft. Bestehende Primärcheckouts und sämtliche fremden
Artefakte bleiben unverändert. Integration der Dokumentation in master/main
bleibt bis zu einem separat freigegebenen Merge ausdrücklich ausstehend.
