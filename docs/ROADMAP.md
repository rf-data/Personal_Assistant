# Roadmap – Personal Assistant

Stand: **17.10.2026**. Geprüfte Default-Branches: Backend `master` `476f0a0d`
und UI `main` `14ccfc20`; [aktueller Status und Belege](planning/status.md).
C23.0 ist dieser Planungsauftrag, **keine Implementierung von C23-Persistenz**.

## 1. Projektvision und Zielarchitektur

Eine privat nutzbare Plattform zum Erfassen, Verarbeiten, Speichern und Recherchieren
von Informationsquellen. CS50 bildet die erste produktive Pipeline; zusätzliche
Quellen folgen nach überprüfbaren Verträgen und Nutzungsrechten.

- **Raw Sources:** unveränderte Originaldateien, Transkripte, URLs und Metadaten.
- **Parsed Content:** strukturierte Texte, Blöcke, Kapitel, Seiten, Zeitstempel,
  Code und Bildreferenzen, jeweils auf Quelle und Version rückführbar.
- **Derived Knowledge:** optionale Konzepte, Aussagen und Beziehungen. Vorhandene
  Extraktionsfunktionen bleiben erhalten, ihre Weiterentwicklung ist zurückgestellt,
  bis eine materialbezogene fachliche Evaluation sie rechtfertigt.

Raw und Parsed bleiben dauerhaft ohne Knowledge-Extraktion nutzbar. Bestehende
Modelle/Persistenz zuerst prüfen; **PostgreSQL ist ein Vorschlag, keine Entscheidung**.
Qdrant-/Transcript-Retrieval ist vorhanden und vor einer neuen Suchlösung zu prüfen.
[Architektur](architecture.md), [Issue-Entwurf](planning/issues.md).

## 2. Aktueller Entwicklungsschwerpunkt

Priorität: **C23 → C24 → C25 → C26**, mit früh klärbaren Deployment-Gates parallel.
Noch ist keines dieser neuen Funktionspakete implementiert oder freigegeben.
Die Details liegen im nicht genehmigten [GitHub-Ausführungsplan](planning/github_execution.md):
zehn Parent- und 22 Sub-Issue-Entwürfe, keine angelegten Issues oder Projects.

Statusachsen bleiben unabhängig: **implementiert und gemergt**, **technisch getestet**,
**fachlich evaluiert**, **für Produktivbetrieb freigegeben**, **geplant**, **blockiert**.
Ein Merge oder bestandener synthetischer Test ist kein fachliches Urteil und keine
Produktionsfreigabe. Für C19–C22 liegen gemergte technische Implementierungen vor;
C22s Go-live-Gates sind weiterhin offen. C21-Q/C21-Q.1 liegen nur im Draft-PR #72.

## 3. Aktive Planungsmeilensteine und Akzeptanzkriterien

| ID / Name | Ziel und zentrale Akzeptanz | Status / Repositories / Abhängigkeiten | Parent Issue |
| --- | --- | --- | --- |
| C23 – Parsed Content Persistence | Vorhandene Modelle im ADR vergleichen; Raw/Parsed versioniert mit Hashes/Provenienz speichern; idempotenter Reimport; Seiten-/Block-/Zeitbezüge und unbekannte Zeiten erhalten; Rechte-/Lesevertrag | Geplant; Backend federführend, UI Verbraucher; vorhandene C10/C13/C16–C22-Verträge | Noch nicht angelegt; [Entwurf C23](planning/issues.md#c23) |
| C24 – Indexing & Retrieval | Volltext mit Quellenbelegen; optional Semantik; versionierte Indexierung/Reindexierung, Rechte und Fehler/Stale behandeln; bestehendes Qdrant prüfen; reale Retrievalevaluation | Geplant; Backend; C23; optionale Semantik darf den Volltextkern nicht blockieren | Noch nicht angelegt; [Entwurf C24](planning/issues.md#c24) |
| C25 – Search & Source UI | Kurs-/Quellenauswahl, Suche/Filter, Parsed-Anzeige, Originalverknüpfung, Seiten-/Zeitbelege und Job-/Indexstatus; API- und Browserabnahme | Geplant; UI federführend, Backend API; C23/C24 | Noch nicht angelegt; [Entwurf C25](planning/issues.md#c25) |
| C26 – Hetzner Production Release | CS50 über die reale UI nutzbar; C22-Gates zu Auth/TLS/Containern/Storage/Restore/Monitoring schließen; begrenzten realen Korpus E2E prüfen; manueller Go-live | Geplant, Produktivfreigabe blockiert; beide Repositories; C23/C24/C25 und C22-Abnahme | Noch nicht angelegt; [Entwurf C26](planning/issues.md#c26) |

Diese Tabelle ist Strategie. Überprüfbare Einzelaufgaben und Cross-Repository-
Abhängigkeiten stehen einmalig im [operativen Entwurf](planning/issues.md).
Ein konkreter Umsetzungsauftrag und Schritt-B-Freigabe stehen noch aus.

## 4. Geplante weitere Meilensteine und Abhängigkeiten

Nur übergeordnete Backlog-Parents, noch keine Sub-Issue-Zerlegung oder Terminierung.

| ID / Name | Ziel / zentrale Akzeptanz | Status / Repositories / Abhängigkeiten | Parent Issue |
| --- | --- | --- | --- |
| C27 – Legacy Code Review | Aktive Imports/Starts, Wikimedia/Parsing/Download/Transkription/RAG inventarisieren; Wiederverwendung und Cleanup mit konkreter Freigabe | Geplant; Backend, UI mitprüfen; vorhandenes Audit, unabhängig früh möglich | [Entwurf C27](planning/issues.md#c27), noch keine Issue-URL |
| C28 – Source Registry & Additional Sources | eBooks/EPUB/PDF, Liora und Apothekerkammer-Webinare; Identität, Rechte, Ingestion, Versionierung und Review definieren | Geplant; Backend, spätere UI-Anbindung; C23 | [Entwurf C28](planning/issues.md#c28), noch keine Issue-URL |
| C29 – Entity Recognition & Linking | Fachbegriffe als Annotationen, Mehrdeutigkeit und kanonische Entitäten; dokumentübergreifende Fundstellen, Originaltext unverändert | Geplant; Backend, UI-Navigation später; C23/C24 | [Entwurf C29](planning/issues.md#c29), noch keine Issue-URL |
| C30 – Wikimedia Entity Enrichment | Bestehende Wikipedia/Wikidata-Clients prüfen; QIDs/Sprachen/Disambiguierung, Cache/Retry/Rate Limits und externe Provenienz; getrennte UI-Darstellung | Geplant; Backend, UI später; C27/C29; externe Angaben sind keine geprüfte Wahrheit | [Entwurf C30](planning/issues.md#c30), noch keine Issue-URL |
| C31 – YouTube Discovery & Review | Kanäle registrieren, neue Metadaten/zulässige Inhalte geplant prüfen; Zusammenfassung/Qualitätsreview und Aufnahmeempfehlung; manuelle Übernahmefreigabe | Geplant; Backend, UI-Review später; C23/C27/C28; Knowledge-Eignung separat | [Entwurf C31](planning/issues.md#c31), noch keine Issue-URL |
| C32 – Medium Email & Article Review | Autorisierte E-Mails/Artikellinks, Duplikate, Relevanz und Zusammenfassung; manuelle Quellenregistrierung unter Beachtung von Paywalls/Rechten | Geplant; Backend, UI-Review später; C23/C27/C28 | [Entwurf C32](planning/issues.md#c32), noch keine Issue-URL |

C27 ist kein pauschaler Blocker für C23: die dort unmittelbar benötigten Modelle
werden bereits im C23-ADR geprüft. Spätere Source-/Entity-Pakete priorisieren keine
allgemeine Knowledge-Extraktion vor der Evaluation.

## 5. Bekannte übergreifende Blocker

| Befund | Aktuell noch offen / eindeutiger operativer Eigentümer im Entwurf |
| --- | --- |
| TXT ohne bekannte Zeitstempel | C23-05 ergänzt [Nullzeiten und Timed-Guards](cs50/contracts/official_transcript_unknown_time.md); [lokale Abnahme und Grenzen](cs50/evaluation/official_transcript_unknown_time.md). TXT-ContentStore-/Knowledge-/Retrievalvertrag bleibt ausstehend; keine globale Pipelinefreigabe. |
| Historische Transcript-Pfadabweichung | C21-Q.1 beschreibt `data/Harvard` versus Receiptpfad `data/lectures/Harvard`; nur Draft #72, keine Migration. C23-03 übernimmt den sicheren Bindungs-/Übernahmeentscheid. |
| Authlib/OIDC | C22 gemergt, UI-Lock enthält kein Authlib und Guard sperrt Produktionsstart. C26-01 plus tatsächlicher TLS-/Browser-/Rollennachweis C26-03. |
| Container und Zielstorage | Builds/Digests, PID-/cgroup-/Shutdown-/OOM-Prüfung sowie Zielvolume-Semantik nicht abgenommen; C26-02/C26-04. |
| Monitoring/Alarmierung | C15/C22-Konfiguration vorhanden, echter Scrape und Alarmzustellung fehlen; C26-05. |
| Realmaterial/Goldevaluation | C21 prüfte Notes Week 5 technisch; ursprüngliche Week-0-Bundles und unabhängige reale Formel-Gold/Prediction-Paare fehlen im Nachweis. C23-06, Retrievalreview C24-05. |
| Echter Qdrant-/E5-Pilot | Vorhandener Indexcode und frühere synthetische Tests; neuer Realpilot/SDK/Modell/Instanz/Remotefreigabe weiterhin blockiert. Optional C24-04, vorhandenen Draft #72 wiederverwenden. |
| Planung und Projektzugriff | Issueplan noch nicht freigegeben; Projects-/Milestone-Inventar über verfügbaren Connector nicht möglich. Erst Zugriff und vorhandenes gemeinsames Board prüfen. |

Vollständige Quellen- und Entscheidungsliste: [Status](planning/status.md),
[Entscheidungen/Pflege](planning/governance.md). Keine automatische Schließung alter PRs.

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

## 7. Planung, Status und technische Nachweise

- **ROADMAP.md:** Strategie, Meilensteine und Abhängigkeiten.
- **GitHub Issues:** operative Aufgaben; aktuell noch keine eigenständigen Issues
  in beiden geprüften Repositories. [Entwürfe](planning/issues.md), [JSON](planning/issue_plan.v1.json).
- **Gemeinsames GitHub Project:** Arbeitsstatus, vorgesehen „Personal Assistant – Development“;
  [Konzept und Zugriffsgrenzen](planning/project.md), noch keine verifizierte Project-URL.
- **Pull Requests:** Implementierung/Review und technische Nachweise; [aktueller Abgleich](planning/status.md).
- **Tests/CI:** reproduzierbare technische Qualität im dokumentierten Umfang;
  [C21](acceptance/c21_results.md), [C22](deployment/c22_validation.md).

[Ausführungsplan nach Freigabe](planning/github_execution.md) ·
[Pflegeprozess und offene Entscheidungen](planning/governance.md) ·
[Dokumentationsindex](README.md). Ein Meilensteinabschluss verlangt explizite
Akzeptanzprüfung, kein automatisches Hochstufen durch PR-Merge.
