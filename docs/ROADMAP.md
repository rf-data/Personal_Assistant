# Roadmap – Personal Assistant

Stand **19.10.2026**, PM-01. Geprüfte Default-Heads: Backend `master`
`4c057ae33d41ba98e227879cc8a51283338e4a0b`, UI `main`
`90816a1578bcf67739ee9acaa483c1635aa0c44b`.
[Implementierungsabgleich](planning/status.md), [Issueplan](planning/issues.md),
[bestehendes Project #1](https://github.com/users/rf-data/projects/1).

## 1. Ziel und verbindliche Statusgrenzen

Privat nutzbare Quellenplattform: unveränderte Raw Sources → versionierter Parsed
Content → autorisierte Recherche. Derived Knowledge bleibt optional; seine breitere
Weiterentwicklung ist **zurückgestellt**, bis Materialevaluation sie rechtfertigt.
Raw/Parsed und Suche benötigen keine Knowledge-Extraktion. SQLite und unveränderliche
Blobs sind für ContentStore entschieden; PostgreSQL ist keine offene C23-Pflicht mehr.

| Status | Bedeutung |
| --- | --- |
| technisch implementiert | Im Default-Tree integrierter, klar begrenzter Funktionsumfang mit PR-Beleg |
| technisch integriert, fachlich offen | Runtime/technische Nachweise vorhanden; reale Inhalts-/Nutzerabnahme fehlt |
| in Bearbeitung | Separater tatsächlicher Auftrag/Branch, kein behaupteter Abschluss |
| geplant | Definierter Restumfang ohne nachgewiesene Implementierung |
| blockiert | Fehlende konkrete Entscheidung/Freigabe/Abhängigkeit verhindert den betreffenden Schritt |
| optional | Separat verzichtbarer Umfang außerhalb des lexikalischen Kernpfads |
| zurückgestellt | Bewusst nachrangig, kein aktueller Implementierungsauftrag |

Diese Lieferzustände sind **keine ausgelesenen Project-Statuswerte**. Technische
PR-Merges und synthetische Tests erteilen weder fachliche Realabnahme noch
Produktivfreigabe. Die historischen Abnahmeberichte bleiben unverändert.

## 2. C23–C26: tatsächlicher Stand und nächster Schritt

| Meilenstein | Integrierter technischer Umfang | Offen / nächster Schritt | Plan |
| --- | --- | --- | --- |
| C23 Parsed Content Persistence | ADR #75; Core/Adapter/Recovery #76–#78; Reimport #79; Content Read API #80; Unknown-Time #81; Evaluationsframework #82 | Fachliche Realabnahme **blockiert**: D06/D07, vollständige autorisierte Bundles, exakte Roots und menschliches Gold. Kein vollständiger TXT-ContentStore-Adapter aus #81 ableiten. | [C23](planning/issues.md#c23) |
| C24 Indexing & Retrieval | ADR #83, Projektion #84, FTS5/Generationen/interne Suche #85, optionaler Vektoradapter mit Fake-Nachweis #86, A #87, B1 #90, UI-B2 #7 und synthetische Integration C2 #91 | HTTPsearch (03-B) und C16-Indexjobs (02-C) **geplant**; C24-06-A **in Bearbeitung**; fachliche Realevaluation **blockiert**. Echter E5/Qdrant-/Hybridpilot optional und separat gesperrt. | [C24](planning/issues.md#c24) |
| C25 Search & Source UI | Vorhandene Admin-/Workflow- und B2-Reviewansichten wiederverwendbar | Allgemeine Such-/Quellennutzung, Deep Links, Indexstatus und tatsächliche Browserabnahme **geplant**. Such-HTTP-/DTOvertrag zuerst liefern; B2 ist keine fertige allgemeine Search UI. | [C25](planning/issues.md#c25) |
| C26 Hetzner Production Release | C22-Betriebsarchitektur, ContentStore-Recovery/Backup und Reviewpersistenz vorhanden | Produktivfreigabe **blockiert**: Images/Authlib/OIDC/TLS, Zielvolume, Verbundrestore einschließlich EvaluationStore, Monitoring/Alarmzustellung, reale E2E-Abnahme und manueller Go-live. | [C26](planning/issues.md#c26) |

Backend-PR-Links und konkrete Verträge stehen im [Status](planning/status.md).
Priorität: technische C24-Restverträge/C24-06-A, dann C25; C26-P0-Entscheidungen
zu Runtime, Identität und Storage parallel vorbereiten. Reale Datenfreigaben
bleiben ein eigener Betreiber-/Reviewerentscheid, keine Planungsnebenwirkung.

## 3. C24-Unterpakete ohne doppelte Implementierungsaufträge

| Paket | Stand | Nachweis / offene Grenze |
| --- | --- | --- |
| C24-05-A | technisch implementiert | Backend #87: versionierte Evaluation/Goldverträge; synthetisch, kein echtes Gold |
| C24-05-B1 | technisch implementiert | Backend #90: persistente Revisionen, explizite Schreibrechte, C16-authentifizierte API |
| C24-05-B2 | technisch implementiert | UI #7: bestehende Streamlit-App, Review/Export/Abnahmeansicht; keine allgemeine Search UI |
| C24-05-C / Draft #89 | Metadatenvorbereitung durch C2 übernommen | Historische r1/r2 und Übergabeplan erhalten; keine zusätzliche Reviewruntime bauen |
| C24-05-C2 | technisch implementiert, Realziel offen | Backend #91: synthetische Review → Gold → FTS5 → A-Report-Integration; Realpilot weiterhin blockiert |
| C24-06-A | in Bearbeitung | Eigenständiger lokaler Umgebungs-/Humanabnahmeauftrag; PM-01 verändert dessen Worktree, Dienste oder Tests nicht |
| 02-C / 03-B | geplant | Vorhandenen Builder bzw. interne Suche in C16-Jobs/HTTP integrieren; keine zweite Suche/Queue |
| 04-B / Draft #72 | optional, blockiert | Konkrete Modell-/Instanz-/Transportrechte und gegebenenfalls D06/D07 fehlen |

Draft #88 bleibt Architekturhistorie; B1/B2 liefern inzwischen die Umsetzung.
#72/#88/#89 sowie alte #6/#9/#10/#11 werden weder gemergt noch geschlossen.
[Erhaltenswerter Umfang](planning/status.md#offene-prs-und-erhaltenswerter-umfang).

## 4. C27–C32 und persönlich verantwortetes Vorhaben

| Ziel | Status / Abhängigkeiten | Verbindlicher Umfang |
| --- | --- | --- |
| C27 Legacy Code Review | geplant, P2; unabhängig vom persönlichen CS50P-Projekt | Aktive Imports/Starts und vorhandene Wikimedia-/Parsing-/RAG-Verträge prüfen; gezielter Cleanup nur mit konkreter Freigabe |
| C28 Source Registry & Additional Sources | geplant, P2; C23-Verträge wiederverwenden | Rechte/Identität/Versionierung für eBooks, Webinare und weitere Quellen; gemeinsamer begrenzter Scheduled-Discovery-Vertrag, keine zweite Queue |
| C29 Entity Recognition & Linking | geplant, P2; C23/C24 | Quellgebundene Annotationen, Disambiguierung und dokumentübergreifende Fundstellen; Originale unverändert |
| C30 Wikimedia Enrichment | geplant, P2; C27/C29 | Vorhandene Clients wiederverwenden; externe Provenienz, Rate Limits/Cache und sichtbare Unsicherheit |
| C31 YouTube Discovery & Review | geplant, P2; C23/C27/C28 | Kanäle/Metadaten, begrenzte geplante Abrufe, Relevanz und menschliche Aufnahmeentscheidung im gemeinsamen Discovery-Konzept |
| C32 Medium, Real Python & Fachnewsletter | geplant, P2; C23/C27/C28 | Autorisierte E-Mails erkennen, Links normalisieren/deduplizieren, Relevanz und menschliche Freigabe; kontrollierter Move nach dokumentierter Verarbeitung |
| PyRepo Inspector – CS50P Final Project | **optional; ausschließlich persönlich durch rf-data**, außerhalb C23–C32-Kernpfad | Python-CLI/AST, Imports, Funktionen/Klassen, Abhängigkeiten, mögliche unreferenzierte Module, JSON/Markdown, optionale Hooks. **Keine Codex-Implementierung oder automatischen Codex-Aufträge**, kein neues Repository. C27 darf später optional wiederverwenden, aber nicht davon abhängen. |

[Persönlicher Issueentwurf](planning/issues.md#personal-pyrepo),
[arXiv-Provider](planning/issues.md#c28-01), [C32](planning/issues.md#c32).
arXiv ergänzt C28/C31: konfigurierbare Queries/Kategorien, begrenzte Metadatenabrufe,
Identifier/Version, Deduplizierung, begründete Empfehlung und Humanreview. Keine
PDF-Volltextdownloads, automatische Source-Promotion oder Abstracts als fachliche
Wahrheit. Keine Jobs werden durch PM-01 aktiviert.

C32 trennt Verarbeitung und Move: eigener **konfigurierter** Zielordner, originale
Mail-ID/UID soweit möglich, Idempotenz, Provider-COPY/MOVE-Semantik, kontrollierte
Fehler/Wiederholungen. Relevanz allein verschiebt nichts. Keine unkontrollierten
EXPUNGE-/Löschaktionen oder ungefragten Mailboxregeln. PM-01 liest/verändert keine Mail.

## 5. Gates, Zuständigkeit und Projectpflege

D06 historische Pfadbindung und D07 Sourcefreigaben/Realbundles/Gold bleiben offen.
C23-03 behebt diese historische Datenentscheidung nicht durch einen Runtimefallback.
C26 benötigt zusätzlich D09–D11 zu Runtime/Host/Kosten/Identität/Storage/Betriebsowner.
Konkrete Assignees und Termine sind außer dem persönlich vorgegebenen PyRepo-Owner
nicht bestätigt; vor Ready festlegen. [Entscheidungsstand](planning/governance.md).

Das vom Eigentümer benannte [Project #1](https://github.com/users/rf-data/projects/1)
bleibt das einzige Board. Titel, Node-ID, Felder/Views, Items, Workflows und
Berechtigungen sind mit diesem Connector **nicht inventarisierbar**. Kein Ersatzboard.
[Inventargrenzen und vorgeschlagene Views](planning/project.md).

Der Auftrag autorisiert die beschriebenen nichtdestruktiven Planungsänderungen.
GitHub-Issue-/Projectmutationen bleiben dennoch an die tatsächliche Bestands-/
Rechteprüfung gebunden. Der aktuelle APIabgleich enthält null eigenständige Issues
(89 Backend-/7 UI-Einträge, sämtlich PRs). 32 ursprüngliche Plan-IDs bleiben
nachvollziehbar; 13 Unter-/Rest-/Provider-/persönliche Aufgaben ergänzen sie zu
45 Planzeilen, **nicht 45 neuen offenen Implementierungen**.
[Operativer Plan](planning/issues.md), [Ausführung](planning/github_execution.md).

## 6. Abgeschlossene Entwicklungsmeilensteine – kompakte Übersicht

„Abgeschlossen“ bedeutet hier gemergter Entwicklungsumfang, **keine pauschale
Produktions- oder fachliche Freigabe**. Einzelne offene Abnahmen bleiben oben sichtbar.
Die frühen IDs wurden mehrfach verwendet: C01–C03 bezeichnen zusätzlich die
[CS50-Reviewverträge](cs50/evaluation/cs50_quality_evaluation.md) aus Backend-PR #36.
Dort ist Evaluationsinfrastruktur vorhanden, kein unabhängiges reales Goldurteil.

| Pakete | Belegter Umfang / verbleibende Grenze |
| --- | --- |
| C01–C09, historisch | Frühere Plan-IDs sind im [Archiv](archive/2026-10/repository-overview/ROADMAP.md) erhalten. C01–C06-Funktionen wurden durch C14/C17 gebündelt, C07 durch C12; C08-Dependencyreview gehört zu C27, C09-Dokumentabgleich zu C17.0/C23.0. Kein erfundener individueller Merge-/Teststatus. |
| C10–C13 | Backend PRs #61–#64: Quality Gate/Handoff, Formelevaluation (42 synthetische Fälle), konservative Konsolidierung und Visualinventur; reale fachliche Evaluation offen. |
| C14–C18 und C17.0 | UI #1/#2, Backend #65–#68: Admin/Backendintegration, Monitoringvertrag, Queue/Executor, Offline-DAG und Audit; technische Verträge, kein Produktivnachweis. |
| C19 | Backend [#69](https://github.com/rf-data/Personal_Assistant/pull/69) gemergt: nativer PDF-Lebenszyklus und fünfstufiger C18-PDF-Workflow lokal getestet; Containergrenzen bleiben C26. |
| C20-B/C20-C | Backend [#70](https://github.com/rf-data/Personal_Assistant/pull/70), UI [#3](https://github.com/rf-data/personal-assistant-ui/pull/3) gemergt: vollständiger Workflow-HTTP-Vertrag und bestätigte UI-Execute/Resume/Cancel-Integration. |
| C21 | Backend [#71](https://github.com/rf-data/Personal_Assistant/pull/71), UI [#4](https://github.com/rf-data/personal-assistant-ui/pull/4) gemergt: echte Loopback-HTTP-/native Prozess-/AppTest-Abnahme; Browser und fachliche Freigabe getrennt offen. |
| C22 | Backend [#73](https://github.com/rf-data/Personal_Assistant/pull/73), UI [#5](https://github.com/rf-data/personal-assistant-ui/pull/5) gemergt: private Rollen/Profile, Startschutz und synthetischer Backup/Restore; alle dokumentierten Runtime-/Go-live-Gates bleiben offen. |

C21-Q/C21-Q.1 sind **nicht** in dieser Abschlussliste: [Draft #72](https://github.com/rf-data/Personal_Assistant/pull/72)
ist offen. Historische Backend-PRs #6/#9/#10/#11 bleiben ebenfalls offen;
[fachlicher Abgleich](cs50/operations/historical_pr_review.md), kein automatisches Merge/Close.


## 7. Nachweise und Änderungsgrund

PM-01 ersetzt die veraltete Pauschalaussage „C23–C26 noch nicht implementiert“
durch belegte technische Teilumfänge und ausdrücklich offene Abnahmen. Die alte
C23.0-Aufnahme bleibt [unverändert erhalten](planning/status_c230_2026-10-17.md);
historische Test-/Releaseberichte und Korpusdateien werden nicht umgeschrieben.
[PM-01-Prüfung und tatsächliche GitHub-Aktionen](planning/pm01_validation.md).

ROADMAP = Strategie, Issues = operative Arbeit, Project = Arbeitsübersicht,
PRs = konkreter Lieferumfang, Tests = begrenzter technischer Nachweis. Ein Merge
setzt weder einen Meilenstein noch dessen fachliche/produktive Freigabe automatisch.
