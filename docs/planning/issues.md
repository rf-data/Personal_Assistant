# Operativer Issueplan C23–C32 – PM-01

19.10.2026. Quelle: [issue_plan.v1.json](issue_plan.v1.json), Revision `pm01-2026-10-19`.
PM-01 autorisiert nichtdestruktive Planungsänderungen. **Noch keine Issues/Projectitems
angelegt:** Projectinventar und Rechte sind über den verfügbaren Connector nicht
prüfbar. [Project #1](https://github.com/users/rf-data/projects/1) wird ausschließlich
weiterverwendet; [Ausführungsgrenzen](github_execution.md), [Liveabgleich](status.md).

Die ursprünglichen 32 Schlüssel bleiben erhalten; 13 präzise Unterpakete bzw.
persönliche/providerbezogene Aufgaben ergänzen sie zu **45 Planzeilen**. Das sind
keine 45 neuen Implementierungsaufträge. `Done` betrifft ausschließlich den explizit
begrenzten technischen Scope mit PR-Beleg. Teilumsetzung/Realabnahme bleiben offen.
Status/Priority sind Vorschläge für Projectfelder, keine ausgelesenen Livewerte.
Alle nicht persönlich gebundenen Assignees sind ungeklärt; keine Termine erfunden.

## Deduplizierung der ursprünglichen 32 Entwürfe

| Plan-ID | Aktuelle Bewertung | GitHub-Behandlung |
| --- | --- | --- |
| [C23](#c23) | integrated_pending_acceptance | create_remaining_scope_after_project_preflight |
| [C24](#c24) | integrated_pending_acceptance | create_remaining_scope_after_project_preflight |
| [C25](#c25) | planned | create_after_project_preflight |
| [C26](#c26) | blocked | create_after_project_preflight |
| [C27](#c27) | planned | create_after_project_preflight |
| [C28](#c28) | planned | create_after_project_preflight |
| [C29](#c29) | planned | create_after_project_preflight |
| [C30](#c30) | planned | create_after_project_preflight |
| [C31](#c31) | planned | create_after_project_preflight |
| [C32](#c32) | planned | create_after_project_preflight |
| [C23-01](#c23-01) | technically_implemented | reference_existing_pr_do_not_reimplement |
| [C23-02](#c23-02) | technically_implemented | reference_children_do_not_create_duplicate_implementation |
| [C23-03](#c23-03) | blocked | create_remaining_scope_after_project_preflight |
| [C23-04](#c23-04) | technically_implemented | reference_existing_pr_do_not_reimplement |
| [C23-05](#c23-05) | technically_implemented | reference_existing_pr_do_not_reimplement |
| [C23-06](#c23-06) | blocked | create_remaining_scope_after_project_preflight |
| [C24-01](#c24-01) | technically_implemented | reference_existing_pr_do_not_reimplement |
| [C24-02](#c24-02) | integrated_pending_acceptance | reference_integrated_scope_track_remaining_child |
| [C24-03](#c24-03) | integrated_pending_acceptance | reference_integrated_scope_track_remaining_child |
| [C24-04](#c24-04) | optional | create_remaining_scope_after_project_preflight |
| [C24-05](#c24-05) | blocked | create_remaining_scope_after_project_preflight |
| [C25-01](#c25-01) | planned | create_after_project_preflight |
| [C25-02](#c25-02) | planned | create_after_project_preflight |
| [C25-03](#c25-03) | planned | create_after_project_preflight |
| [C25-04](#c25-04) | planned | create_after_project_preflight |
| [C26-01](#c26-01) | planned | create_after_project_preflight |
| [C26-02](#c26-02) | planned | create_after_project_preflight |
| [C26-03](#c26-03) | planned | create_after_project_preflight |
| [C26-04](#c26-04) | planned | create_after_project_preflight |
| [C26-05](#c26-05) | planned | create_after_project_preflight |
| [C26-06](#c26-06) | planned | create_after_project_preflight |
| [C26-07](#c26-07) | planned | create_after_project_preflight |

Erledigte technische Scopes über PRs referenzieren, nicht nochmals als offene
Implementierungsissues anlegen. Für teilintegrierte Parents nur verbleibenden Scope
führen. #88/#89 sind keine zusätzlichen Implementierungsaufträge; [Draftaudit](status.md#offene-prs-und-erhaltenswerter-umfang).

## C23

[C23] Parsed Content Persistence

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `keiner` · Abhängigkeiten: keine.

Planstatus: **integrated_pending_acceptance** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

Persistence technical core integrated; historical binding and real parsing acceptance remain open.

Akzeptanz / begrenzter Scope:

- Bestehende Material-/Transcript-/Parsingverträge im ADR abgeglichen; PostgreSQL bleibt Option bis zur begründeten Entscheidung.
- Raw und Parsed Content persistent, versioniert und unabhängig von Knowledge nutzbar; Hash-/Quellen-/Seiten-/Block-/Zeitbezüge und idempotenter Reimport nachgewiesen.
- Lesevertrag, Rechte und Restorefähigkeit sind belegt; unbekannte Zeiten bleiben ausdrücklich unbekannt.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/75), [PR](https://github.com/rf-data/Personal_Assistant/pull/76), [PR](https://github.com/rf-data/Personal_Assistant/pull/77), [PR](https://github.com/rf-data/Personal_Assistant/pull/78), [PR](https://github.com/rf-data/Personal_Assistant/pull/79), [PR](https://github.com/rf-data/Personal_Assistant/pull/80), [PR](https://github.com/rf-data/Personal_Assistant/pull/81), [PR](https://github.com/rf-data/Personal_Assistant/pull/82)

## C24

[C24] Indexing & Retrieval

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `keiner` · Abhängigkeiten: `C23`.

Planstatus: **integrated_pending_acceptance** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

Projection/FTS5/evaluation/review integrated; search HTTP, job integration, local human acceptance and real evaluation remain open.

Akzeptanz / begrenzter Scope:

- Volltexttreffer referenzieren gespeicherte Source-/Parsed-Versionen samt Seite/Block/Zeit; Rechtefilter werden serverseitig geprüft.
- Indexversion, Reindexierung, Fehler und Stale-Erkennung sind getestet; Suchindex ist aus freigegebenen Quellen rekonstruierbar.
- Vorhandener Transcript-/Qdrant-Pfad geprüft; semantische Suche bleibt optional, reale Qualität separat evaluiert.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/83), [PR](https://github.com/rf-data/Personal_Assistant/pull/84), [PR](https://github.com/rf-data/Personal_Assistant/pull/85), [PR](https://github.com/rf-data/Personal_Assistant/pull/86), [PR](https://github.com/rf-data/Personal_Assistant/pull/87), [PR](https://github.com/rf-data/Personal_Assistant/pull/88), [PR](https://github.com/rf-data/Personal_Assistant/pull/89), [PR](https://github.com/rf-data/Personal_Assistant/pull/90), [PR](https://github.com/rf-data/Personal_Assistant/pull/91), [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C25

[C25] Search & Source UI

Repository: `rf-data/personal-assistant-ui` · Typ: `milestone` · Priorität: `P1` · Workstream: `UI`.

Ziel: `C25` · Parent: `keiner` · Abhängigkeiten: `C23`, `C24`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Existing Evaluation & Review is a reusable view, not a completed general Search & Source UI.

Akzeptanz / begrenzter Scope:

- Kurs-/Quellenauswahl, Suche/Filter und lesbare geparste Inhalte über autorisierte APIs.
- Originalverweise und Belege mit Seiten/Blöcken/Zeiten; fehlende Positionen werden nicht erfunden.
- Job-/Indexstatus sowie leere, unzugängliche und veraltete Treffer verständlich; Browserabnahme für vereinbarten Umfang belegt.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C26

[C26] Hetzner Production Release

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Operations`.

Ziel: `C26` · Parent: `keiner` · Abhängigkeiten: `C23`, `C24`, `C25`.

Planstatus: **blocked** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

No deployment or productive go-live authorized by PM-01.

Offene Voraussetzungen: D09/D10/D11 and C26-01 through C26-07 target-operation acceptance.

Akzeptanz / begrenzter Scope:

- Alle noch offenen C22-Gates mit gewählten Images, Identitäten, TLS, Ressourcen und Zielvolume geschlossen.
- Konsistenter Backup-/Restore- und Alarmzustellungsnachweis; dokumentierte Recovery und Verantwortlichkeit.
- CS50 über die reale UI auf ausdrücklich freigegebenem Zielhost nutzbar; begrenzter realer Testkorpus und Operator-Go-live-Freigabe protokolliert.


## C27

[C27] Legacy Code Review

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Legacy`.

Ziel: `C27` · Parent: `keiner` · Abhängigkeiten: keine.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Independent of PERSONAL-PYREPO; no waiting for the CS50P final project.

Akzeptanz / begrenzter Scope:

- Modul-/Import-/CLI-/Docker-Inventar für beide Repositories; aktive und manuelle Aufrufer getrennt.
- Wikimedia, Parsing, Download, Transkription und RAG auf Wiederverwendung und Duplikation geprüft.
- Konkreter Cleanup-/Kompatibilitätsplan mit Owner/Freigabe; keine pauschale Entfernung oder Migration.


## C28

[C28] Source Registry & Additional Sources

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.

Ziel: `C28` · Parent: `keiner` · Abhängigkeiten: `C23`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Akzeptanz / begrenzter Scope:

- Registryanforderungen für eBooks/EPUB/PDF, Liora-Fortbildung, Apothekerkammer-Webinare und weitere Kurse.
- Quellidentität, Zugriffs-/Nutzungsrechte, Versionierung, Ingestionstrategie und Review festgelegt.
- Erste Erweiterung separat anhand berechtigter Quellen abgenommen; keine stillschweigende Bestandserfassung.
- Gemeinsamen begrenzten Scheduled-Discovery-Vertrag für YouTube, arXiv und weitere erlaubte Provider festlegen; C16/C18/C22 prüfen, keine zweite Queue/Schedulerimplementierung.


## C29

[C29] Entity Recognition & Linking

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Entities`.

Ziel: `C29` · Parent: `keiner` · Abhängigkeiten: `C23`, `C24`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Akzeptanz / begrenzter Scope:

- Fachbegriffe als versionierte quellgebundene Annotationen mit Mehrdeutigkeitsstatus.
- Kanonische Entitäten und dokumentübergreifende Fundstellen nachvollziehbar verknüpft.
- Originaltexte unverändert; Fehler-/Disambiguierungsreview vor produktiver Navigation.


## C30

[C30] Wikimedia Entity Enrichment

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Entities`.

Ziel: `C30` · Parent: `keiner` · Abhängigkeiten: `C27`, `C29`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Akzeptanz / begrenzter Scope:

- Bestehende Wikipedia-/Wikidata-Clients geprüft und Schnittstellen konsolidiert.
- QIDs als mögliche Identifikatoren, Sprachen/Disambiguierung, Cache/Retry/Rate Limits und Provenienz entschieden.
- Externe Informationen in der UI getrennt von lokalen Aussagen; keine ungeprüfte fachliche Wahrheit.


## C31

[C31] YouTube Discovery & Review

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.

Ziel: `C31` · Parent: `keiner` · Abhängigkeiten: `C23`, `C27`, `C28`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Use the shared scheduled discovery concept owned by C28; YouTube is a provider, not a second scheduler.

Akzeptanz / begrenzter Scope:

- Registrierte Kanäle und begrenzte geplante Jobs für neue Metadaten/zulässig verfügbare Inhalte.
- Zusammenfassungen, Relevanz-/Qualitätsreview und Aufnahmeempfehlung mit Quellenbelegen.
- Manuelle Freigabe vor dauerhafter Übernahme; Knowledge-Eignung separat und optional bewerten.
- Geplante Abrufe nutzen den gemeinsamen C28-Vertrag; keine neuen Jobs durch Planung aktivieren.


## C32

[C32] Medium, Real Python und autorisierte Fachnewsletter prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.

Ziel: `C32` · Parent: `keiner` · Abhängigkeiten: `C23`, `C27`, `C28`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Planning only: no emails read, moved or deleted; no mailbox rules changed.

Akzeptanz / begrenzter Scope:

- Explizit autorisierte Medium-E-Mails/Artikellinks, Real Python Newsletter und weitere freigegebene Fachnewsletter verarbeiten; Absender und Newslettertyp erkennen.
- Links extrahieren, normalisieren und deduplizieren; Relevanz begründet bewerten und Ressourcen zur Aufnahme vorschlagen; menschliche Freigabe und Nutzungs-/Paywallrechte beachten.
- Nach dokumentierter Verarbeitung in einen eigenen explizit konfigurierten Zielordner verschieben; positive Relevanz allein löst keinen Move aus.
- Verarbeitungsstatus und Verschiebestatus getrennt persistieren; Idempotenz, originale Mail-ID/UID und Provider-/Mailboxbindung erhalten, soweit technisch möglich.
- IMAP-COPY/MOVE-Semantik, Fehler und kontrollierte Wiederholungen festlegen; kein unkontrolliertes EXPUNGE, keine automatischen Regeln/Zielordneränderungen ohne ausdrückliche Konfiguration.
- Keine echten Mailzugriffe oder Mailboxmutationen in diesem Planungsauftrag.


## C23-01

[C23-01] Persistenz-ADR und vorhandene Modelle vergleichen

Repository: `rf-data/Personal_Assistant` · Typ: `debt` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: keine.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

SQLite plus immutable blobs decided; no PostgreSQL implementation pending.

Akzeptanz / begrenzter Scope:

- ArtifactReceipt/NormalizedDocument, TranscriptDocument, Legacy-Parsingmodelle, Dateiartefakte und C16-SQLite auf Zweck und Grenzen vergleichen.
- Source-/Parsed-Versionen, Referenzintegrität, Rechte, Restore und Idempotenz spezifizieren; PostgreSQL gegen bestehende Alternativen begründet entscheiden.
- Keine zweite Jobqueue und kein erzwungener Knowledge-Schritt.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/75)

## C23-02

[C23-02] Raw-/Parsed-Speicherung nach freigegebenem ADR umsetzen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: `C23-01`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_children_do_not_create_duplicate_implementation`.

Core, adapters and recovery integrated. Track implemented children once; whole-system target backup remains C26-04.

Akzeptanz / begrenzter Scope:

- Bestehende IDs, Hashes, Parser-/Schemaversionen und Locatorwerte verlustfrei persistieren.
- Rohbytes und geparste Inhalte getrennt und unabhängig von Derived Knowledge lesen; Vertragstests mit kleinen Fixtures.
- Fehler/atomare Veröffentlichung und parallele Zugriffe im gewählten Speichermodell prüfen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/76), [PR](https://github.com/rf-data/Personal_Assistant/pull/77), [PR](https://github.com/rf-data/Personal_Assistant/pull/78)

## C23-03

[C23-03] Idempotenten Reimport und explizite Bestandsbindung absichern

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: `C23-02`.

Planstatus: **blocked** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

Reimport and explicit source inventory integrated. Historical SRT transfer/binding remains D06-blocked; no path fallback or migration.

Offene Voraussetzungen: D06: explicit canonical historical source binding decision.

Akzeptanz / begrenzter Scope:

- Gleiche Bytes/Version erzeugen keine Dublette; geänderte Quelle oder Parser erzeugt nachvollziehbare Version.
- Abweichende historische Source-Pfade bleiben gesperrt; Strategie aus PR #72/C21-Q.1 wiederverwenden, keine stillen Fallbacks/Symlinks.
- Bestandsübernahme nur nach separater Freigabe; Source-/Receipt-/Provenienz- und Hashkonflikte testen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/79), [PR](https://github.com/rf-data/Personal_Assistant/pull/72)

## C23-04

[C23-04] Autorisierte Source-/Parsed-Leseverträge bereitstellen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: `C23-02`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Authorized paginated Content Read HTTP API integrated; no general search HTTP API.

Akzeptanz / begrenzter Scope:

- Paginiert nach Kurs/Quelle/Version lesen; Originalreferenz und Seiten-/Block-/Zeitbelege liefern.
- Owner-/Course-/Quellrechte serverseitig durchsetzen; keine beliebigen Hostpfade/Dateiserver.
- API-Beispiele und Kompatibilitätsvertrag für das UI-Repository veröffentlichen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/80)

## C23-05

[C23-05] TXT-Import ohne erfundene Zeitstempel reparieren

Repository: `rf-data/Personal_Assistant` · Typ: `bug` · Priorität: `P1` · Workstream: `Sources`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: keine.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Unknown-Time model/importer/guards integrated. Full TXT ContentStore publication is not supplied by this merge.

Akzeptanz / begrenzter Scope:

- Unknown-Time-Vertrag mit start/end=null, vorhandenen Locatoren und Timed-Guards erhalten; keine erfundenen Zeiten.
- Gezielte TXT-/SRT-/VTT-Regression sowie Chunker-/Evidence-Abweisung nicht zeitgebundener Daten ohne erfundene Zeitwerte.
- Nur den relevanten Rest von PR #9 behandeln; alten Patch und PR nicht automatisch übernehmen/schließen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/81), [PR](https://github.com/rf-data/Personal_Assistant/pull/9)

## C23-06

[C23-06] Berechtigten Realmaterialkorpus und unabhängige Goldreferenzen bereitstellen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C23` · Parent: `C23` · Abhängigkeiten: `C23-01`.

Planstatus: **blocked** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

Technical corpus/gold framework and inventory integrated. No authorized complete real bundle or independently confirmed real gold.

Offene Voraussetzungen: D07: source permissions, complete bundles, exact private roots, human reviewers and gold.

Akzeptanz / begrenzter Scope:

- Fehlende Original-/Receipt-/Normalized-Bundles für Week-0-Notes/Slides/Source-PDF mit Rechten und Hashes inventarisieren; keine Downloads ohne Freigabe.
- C10/C13-Qualitätsrubrik für Text/Code/Bilder und separate reale C11-Formel-Gold-/Prediction-Paare festlegen; keine Goldableitung aus Vorhersagen.
- Bekannte Fehlstellen und synthetische/reale Ergebnisse getrennt ausweisen; CS50-Releaseumfang daraus festlegen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/82), [PR](https://github.com/rf-data/Personal_Assistant/pull/91)

## C24-01

[C24-01] Bestehende Suche prüfen und Indexstrategie entscheiden

Repository: `rf-data/Personal_Assistant` · Typ: `debt` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C23-01`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Indexing/retrieval ADR integrated; lexical FTS5 selected, semantics optional.

Akzeptanz / begrenzter Scope:

- Transcript-Qdrant, Filter/Offsets, Chroma-/Legacy-RAG und mögliche Volltextlösungen vergleichen.
- Keine neue Vektordatenbank ohne ADR; PostgreSQL-Suche bleibt vom Persistenz-ADR abhängig.
- Knowledge-Extraktion ist keine Suchvoraussetzung; verbindlichen Text-/Quellenvertrag bestimmen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/83)

## C24-02

[C24-02] Versionierten Volltextindex und Reindexierung implementieren

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C23-02`, `C23-03`, `C24-01`.

Planstatus: **integrated_pending_acceptance** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_integrated_scope_track_remaining_child`.

Projection (02-A), FTS5 generations/rebuild (02-B) integrated. Explicit C16 index-job integration (02-C) remains planned.

Akzeptanz / begrenzter Scope:

- Index enthält Source-/Parsed-Version, Locator und Rechtebezug; Roh-/Parsed-Daten bleiben autoritativ.
- Wiederholung, Teilfehler, veraltete Dokumente und kontrollierte Reindexierung testen; keine ungeprüfte Datenlöschung.
- Indexstatus und Fehler maschinenlesbar bereitstellen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/84), [PR](https://github.com/rf-data/Personal_Assistant/pull/85)

## C24-03

[C24-03] Quellengebundene Such-API und Trefferbelege liefern

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C23-04`, `C24-02`.

Planstatus: **integrated_pending_acceptance** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_integrated_scope_track_remaining_child`.

Internal authorized lexical retrieval/locators (03-A) integrated; search HTTP capability/routes/DTOs (03-B) absent.

Akzeptanz / begrenzter Scope:

- Kurs-/Quellenfilter, Paging und begrenzte Anfragen mit serverseitigen Berechtigungen.
- Treffer enthalten eindeutige Version und echte Seiten-/Block-/Zeitbezüge sowie sichere Originalverweise.
- Stale-/Missing-Source und inkompatible Indexversionen ausdrücklich melden; UI-Vertrag veröffentlichen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/85)

## C24-04

[C24-04] Vorhandenen Qdrant-/Transcript-Pilot abnehmen statt neu bauen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P2` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C23-03`, `C24-01`.

Planstatus: **optional** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

ContentRecord vector adapter/Fake transport integrated. Original real Qdrant/E5 pilot scope remains optional C24-04-B; no real inference or hybrid acceptance.

Akzeptanz / begrenzter Scope:

- Draft PR #72 samt C21-Q.1 und seinen getrennten Phase-A-/Phase-B-Gates reviewen; keine parallele Ingestion implementieren.
- Nur nach expliziter Bereitstellung/Freigabe von SDK, immutable E5-Revision und isolierter Instanz echte Upsert-/Readback-/Retrieval-/Recovery-Nachweise.
- Semantische Suche bleibt optional; bestehender Originalpfadkonflikt und Remote-Uploadfreigabe bleiben echte Blocker.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/86), [PR](https://github.com/rf-data/Personal_Assistant/pull/72)

## C24-05

[C24-05] Reale Retrievalqualität und Quellenrückbindung bewerten

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C23-06`, `C24-03`.

Planstatus: **blocked** · Technischer Stand: `partially_integrated` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `pending`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_remaining_scope_after_project_preflight`.

A evaluation, B1 persistence/API, B2 review UI and C2 synthetic integration integrated. Real release acceptance remains open.

Offene Voraussetzungen: D07: authorized real bundle/roots, independent human gold, complete pool, approver decision.

Akzeptanz / begrenzter Scope:

- Unabhängige reale Fragen/Goldfundstellen und Suchkonfiguration versionieren.
- Volltext und gegebenenfalls semantische Suche getrennt auswerten; Nenner, Fehler und nicht evaluierbare Fälle berichten.
- Qualitätsgrenzen und Releaseumfang manuell prüfen; keine Modellwerte aus synthetischen Fixtures erfinden.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/87), [PR](https://github.com/rf-data/Personal_Assistant/pull/90), [PR](https://github.com/rf-data/personal-assistant-ui/pull/7), [PR](https://github.com/rf-data/Personal_Assistant/pull/91), [PR](https://github.com/rf-data/Personal_Assistant/pull/88), [PR](https://github.com/rf-data/Personal_Assistant/pull/89)

## C25-01

[C25-01] Kurs-/Quellenauswahl und Suchfilter integrieren

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.

Ziel: `C25` · Parent: `C25` · Abhängigkeiten: `C23-04`, `C24-03-B`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Reuse B2 client/security/renderers where suitable; do not build a second review UI.

Offene Voraussetzungen: C24-03-B: actual Search HTTP/DTO contract.

Akzeptanz / begrenzter Scope:

- Vorhandene UI-Settings/Auth und typisierten Client erweitern, keine Backend-Dateizugriffe.
- Auswahl, Suche, Paging und Filter nutzen autoritative APIs; leere und verweigerte Antworten unterscheidbar.
- Cross-Repository-Vertragsversion und Backend-PR verlinkt.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C25-02

[C25-02] Parsed Content mit Original- und Fundstellenansicht anzeigen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.

Ziel: `C25` · Parent: `C25` · Abhängigkeiten: `C25-01`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Reuse B2 client/security/renderers where suitable; do not build a second review UI.

Offene Voraussetzungen: C24-03-B: actual Search HTTP/DTO contract.

Akzeptanz / begrenzter Scope:

- Strukturierte Texte, Code und Bildreferenzen anzeigen; Seite/Block/Kapitel/Cue nur bei vorhandenem Beleg.
- Treffer führt zur konkreten Quelle/Version; Originalzugang bleibt berechtigungsgeprüft.
- Unbekannte Zeitstempel, fehlende Bildbytes und veraltete Quellen klar darstellen.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C25-03

[C25-03] Job- und Indexstatus für Suche sichtbar machen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.

Ziel: `C25` · Parent: `C25` · Abhängigkeiten: `C25-01`, `C24-02-C`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Reuse B2 client/security/renderers where suitable; do not build a second review UI.

Offene Voraussetzungen: C24-03-B: actual Search HTTP/DTO contract.

Akzeptanz / begrenzter Scope:

- Bestehendes C16/C18-Job-/Owner-/Course-Modell nutzen, Indexzustand aus Backend beziehen.
- Refresh/Fehler/Unavailable/Stale ohne automatische Schreibaktion oder künstlichen Fortschritt.
- Bestehende Admin-/Workflowansichten bleiben kompatibel.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C25-04

[C25-04] Browserabnahme der Source-/Search-Nutzung dokumentieren

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C25` · Parent: `C25` · Abhängigkeiten: `C25-02`, `C25-03`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Reuse B2 client/security/renderers where suitable; do not build a second review UI.

Offene Voraussetzungen: C24-03-B: actual Search HTTP/DTO contract.

Akzeptanz / begrenzter Scope:

- Echte Browserfälle für Filter, Deep Links, Paging, Tastaturbedienung und belegte Fundstellen mit festem Korpus.
- Viewer-/Operator-/Course-Grenzen sowie fehlende/stale Inhalte prüfen; AppTest getrennt berichten.
- Kein Browsernachweis durch bloße API-/AppTest-Erfolge ersetzen.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C26-01

[C26-01] Gepinntes Authlib und UI-Startschutz abnehmen

Repository: `rf-data/personal-assistant-ui` · Typ: `debt` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: keine.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Authlib fehlt im aktuellen UI-Lock; vorhandenes C22-Gate gezielt schließen.
- Geprüfte transitive Dependency-/Lockentscheidung und Imagebereitstellung, keine ungefragten Upgrades/Downloads.
- Guard-, Secret- und OIDC-Konfigurationstests; kein Demo-Auth im Produktionsprofil.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/5)

## C26-02

[C26-02] C22-Images und Container-Prozessgrenzen isoliert prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C26-01`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Vorhandene C22-Builds/Profiles mit freigegebenen Digests bereitstellen; Non-root, Mounts, Health und fehlende Pflichtinputs prüfen.
- API-/Executor-/UI-Restart, C19 native PDF-Cancel, Parent-Death/Subreaper, SIGTERM/SIGKILL/OOM und Cgroup-/CPU/RAM/PID-Limits im Container testen.
- Keine Mehrhostfähigkeit ableiten; Befunde und verbleibende Gates protokollieren.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/73)

## C26-03

[C26-03] TLS, OIDC, individuelle Rollen und Browserzugriff abnehmen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C26-01`, `C26-02`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Privater API-Gateway mit korrektem SAN/CA, Ingress-WebSockets und Secretrotation.
- Echter Browser-Login/Logout/Expiry sowie Viewer/Operator/Owner/Course und individuelle Tokenbindungen.
- Keine öffentliche ungeschützte Admin-API, keine deaktivierte TLS-Prüfung; UI-Änderungen nur im UI-Repository.


## C26-04

[C26-04] Zielstorage und konsistenten Restore auf isoliertem Ziel prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C26-02`, `C23-02`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Reuse ContentStore recovery/backup and C22 fence; include EvaluationStore closure, selected index generation and restore strategy explicitly; no production snapshot in PM-01.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Endgültiger Single-Host-Mount: identische UID/Pfade, flock/rename/fsync/SQLite-WAL und Quoten.
- C22- und ContentStore-Backup/Restore wiederverwenden; EvaluationStore-Revisionsclosure, Indexgeneration/Rebuildstrategie, Katalog/Config und getrennte Secrets ausdrücklich einbeziehen.
- Leeres isoliertes Restoreziel, Hash-/Provenienzprüfung, interrupted/Quarantäne und Operator-Recovery; keine produktiven Daten überschreiben.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/73), [PR](https://github.com/rf-data/Personal_Assistant/pull/78), [PR](https://github.com/rf-data/Personal_Assistant/pull/90)

## C26-05

[C26-05] Produktionsmonitoring und echte Alarmzustellung prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C26-02`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Vorhandene C15-Dashboards/Regeln und C22-authentisierten Scrape verwenden.
- Queue, Dauer, Fehler/Timeout/Cancel, Worker, Disk/Volume und Service-Health mit niedriger Kardinalität.
- Alertmanager/alternatives Routing ausdrücklich entscheiden und Alarmzustellung bis zum zuständigen Operator testen.


## C26-06

[C26-06] CS50 über die freigegebene UI Ende-zu-Ende abnehmen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C25-04`, `C24-05`, `C26-03`, `C26-04`, `C26-05`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- Begrenzte reale CS50-Quelle erfassen/verarbeiten/persistieren/indexieren/suchen und Originalfundstelle über UI prüfen.
- Fehler, Neustart, Cancel und Wiederaufnahme mit freigegebenen echten Daten prüfen; synthetische Evidenz getrennt.
- Keine Knowledge-Extraktion erforderlich; fachlich akzeptierten Format-/Korpusumfang festhalten.


## C26-07

[C26-07] Manuelle Hetzner-Go-live-Entscheidung und Betriebsübergabe

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.

Ziel: `C26` · Parent: `C26` · Abhängigkeiten: `C26-06`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Offene Voraussetzungen: Explicit target host/runtime/data/operator decision appropriate to this scope; see D09–D11.

Akzeptanz / begrenzter Scope:

- C22-Gates, Kosten/Hostfreigabe, Rechte, Backup, Retention, Incident-/Rollbackverantwortung und Releaseversion bestätigt.
- Operatorfreigabe mit Datum und Evidenz; C26-Parent erst danach als produktionsfreigegeben schließen.
- Merge oder grüne CI erzeugen keinen Rollout und keine automatische Produktionsfreigabe.


## C23-02A

[C23-02A] ContentStore Core & Persistence Foundation

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23-02` · Abhängigkeiten: `C23-01`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

No real material or production acceptance follows from this technical merge.

Akzeptanz / begrenzter Scope:

- Den begrenzten integrierten technischen Umfang und dessen versionierte Abnahme als vorhandenen Nachweis erhalten; keine erneute Implementierung.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/76)

## C23-02B

[C23-02B] Verified Material & Transcript Adapters

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23-02` · Abhängigkeiten: `C23-02A`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

No real material or production acceptance follows from this technical merge.

Akzeptanz / begrenzter Scope:

- Den begrenzten integrierten technischen Umfang und dessen versionierte Abnahme als vorhandenen Nachweis erhalten; keine erneute Implementierung.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/77)

## C23-02C

[C23-02C] Recovery, Concurrency & Backup/Restore

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.

Ziel: `C23` · Parent: `C23-02` · Abhängigkeiten: `C23-02A`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

No real material or production acceptance follows from this technical merge.

Akzeptanz / begrenzter Scope:

- Den begrenzten integrierten technischen Umfang und dessen versionierte Abnahme als vorhandenen Nachweis erhalten; keine erneute Implementierung.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/78)

## C24-05-A

[C24-05-A] Retrieval Evaluation Framework & Independent Gold

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C24` · Parent: `C24-05` · Abhängigkeiten: `C24-01`, `C23-04`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Bounded technical implementation complete; real pilot acceptance remains on C24-05. Internal FTS5 from #85 is an implemented prerequisite; the outstanding parent-level HTTP/job scope is not required.

Akzeptanz / begrenzter Scope:

- Vorhandene technische Verträge und synthetische Nachweise wiederverwenden; keine echte menschliche Bestätigung oder Realabnahme daraus ableiten.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/87)

## C24-05-B1

[C24-05-B1] Human Review Backend, Persistence & API

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C24` · Parent: `C24-05` · Abhängigkeiten: `C24-05-A`, `C23-04`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Bounded technical implementation complete; real pilot acceptance remains on C24-05.

Akzeptanz / begrenzter Scope:

- Vorhandene technische Verträge und synthetische Nachweise wiederverwenden; keine echte menschliche Bestätigung oder Realabnahme daraus ableiten.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/90)

## C24-05-B2

[C24-05-B2] Human Review UI & Evaluation Dashboard

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.

Ziel: `C24` · Parent: `C24-05` · Abhängigkeiten: `C24-05-B1`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Bounded technical implementation complete; real pilot acceptance remains on C24-05.

Akzeptanz / begrenzter Scope:

- Vorhandene technische Verträge und synthetische Nachweise wiederverwenden; keine echte menschliche Bestätigung oder Realabnahme daraus ableiten.

Vorhandene Belege: [PR](https://github.com/rf-data/personal-assistant-ui/pull/7)

## C24-05-C2

[C24-05-C2] Synthetic Review, Gold Export & FTS5 Integration

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C24` · Parent: `C24-05` · Abhängigkeiten: `C24-05-A`, `C24-05-B1`, `C24-05-B2`.

Planstatus: **technically_implemented** · Technischer Stand: `integrated` · vorgeschlagener Projectstatus: `Done` · fachliche Abnahme: `technical_scope_only`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `reference_existing_pr_do_not_reimplement`.

Bounded technical implementation complete; real pilot acceptance remains on C24-05.

Akzeptanz / begrenzter Scope:

- Vorhandene technische Verträge und synthetische Nachweise wiederverwenden; keine echte menschliche Bestätigung oder Realabnahme daraus ableiten.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/91)

## C24-06-A

[C24-06-A] Lokale Evaluationsumgebung und menschliche Reviewabnahme

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.

Ziel: `C24` · Parent: `C24` · Abhängigkeiten: `C24-05-B2`, `C24-05-C2`.

Planstatus: **in_progress** · Technischer Stand: `in_progress` · vorgeschlagener Projectstatus: `In Progress` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `attach_active_task_when_pr_available`.

Separate active task/branch feat/c24-06a-local-review; PM-01 does not edit, test, stop or block it. No published PR observed at this snapshot.

Akzeptanz / begrenzter Scope:

- Bestehende Streamlit-App und tatsächliches lokales B1-HTTP-Backend mit isolierten persistenten synthetischen Roots bereitstellen.
- Tatsächliche Browser-/Humanabnahme getrennt von automatisierten synthetischen Nachweisen dokumentieren; keine Realfreigabe.


## C24-03-B

[C24-03-B] Autorisierte Search-HTTP-Capability und DTOs

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24-03` · Abhängigkeiten: `C23-04`, `C24-01`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

02-B/03-A already integrated by #85. This is the existing 03-B remainder, not a new search implementation.

Akzeptanz / begrenzter Scope:

- Vorhandene interne FTS5-Fassade am bestehenden C16-Gateway ausdrücklich opt-in bereitstellen; keine erfundenen aktuellen Routen.
- Begrenzte Requests, Cursor, Antwort-/Fehlervertrag, Live-ACL/Sourceprüfung und echte HTTPtests; Cross-Repo-Vertrag vor C25 veröffentlichen.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/85)

## C24-02-C

[C24-02-C] Explizite Indexjob- und Statusintegration

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24-02` · Abhängigkeiten: `C23-04`, `C24-01`.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Use existing 02-B builder; agree catalog/job contract before implementation.

Akzeptanz / begrenzter Scope:

- Bestehenden Indexbuilder ausdrücklich in C16/C18-Katalog-, Request-, Owner/Course- und Prozessverträge einbinden.
- Idempotenz, Restart/Cancel, Ressourcenlimits und autorisierten Indexstatus belegen; kein Watcher, Cron oder automatische Indexierung.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/85)

## C24-04-B

[C24-04-B] Optionalen echten E5/Qdrant-Pilot freigeben und prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P2` · Workstream: `Retrieval`.

Ziel: `C24` · Parent: `C24-04` · Abhängigkeiten: `C23-03`, `C24-01`.

Planstatus: **optional** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Blocked optional work; cannot block the lexical core; no duplicate pilot issue/implementation.

Offene Voraussetzungen: D06/D07 and explicit model/instance/transport authorization.

Akzeptanz / begrenzter Scope:

- Vorhandenen Draft #72 wiederverwenden; konkrete Instanz/Collection, immutable Modellrevision, SDK und Transportfreigaben benennen.
- Nur nach D06/D07 und Instanzfreigabe tatsächliche Inferenz/Upsert/Readback/Recovery bewerten; Hybrid separat und optional.

Vorhandene Belege: [PR](https://github.com/rf-data/Personal_Assistant/pull/72), [PR](https://github.com/rf-data/Personal_Assistant/pull/86)

## C28-01

[C28-01] arXiv Research Discovery & Relevance Review

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P2` · Workstream: `Sources`.

Ziel: `C28` · Parent: `C28` · Abhängigkeiten: keine.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `unassigned`; keine GitHub-Zuweisung. Aktion: `create_after_project_preflight`.

Additional provider shared with C31; not a second scheduler or new main system. Requires the C28 shared scheduler/registry design contract; C28 parent completion is not an implementation prerequisite.

Akzeptanz / begrenzter Scope:

- Konfigurierbare Suchbegriffe/arXiv-Kategorien und geplante begrenzte Abrufe über denselben Scheduled-Discovery-Vertrag wie C31 vorsehen.
- Titel, Abstract, Autoren, Kategorien und Veröffentlichungs-/Änderungsinformationen mit persistentem arXiv-Identifier und Versionsbezug erfassen; deduplizieren.
- Relevanz mit begründeter Aufnahmeempfehlung und menschlicher Prüfung; spätere Source-Registry-Übernahme nur nach Freigabe.
- Keine automatischen PDF-Volltextdownloads, keine Wahrheitsannahme aus Abstracts, keine Source-Promotion; Rate Limits/Nutzungsbedingungen beachten; keine Jobs aktivieren.


## PERSONAL-PYREPO

[PERSONAL-PYREPO] PyRepo Inspector – CS50P Final Project

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P2` · Workstream: `Legacy`.

Ziel: `eigenständig / kein C-Meilenstein` · Parent: `keiner` · Abhängigkeiten: keine.

Planstatus: **planned** · Technischer Stand: `not_implemented` · vorgeschlagener Projectstatus: `Backlog` · fachliche Abnahme: `not_checked`.

Owner: `human_only`; keine GitHub-Zuweisung. Aktion: `create_human_only_issue_after_project_preflight`.

Suggested labels owner:human, cs50p, personal-project, optional; inventory label conventions before applying. rf-data account verified, no automatic assignment performed.

Akzeptanz / begrenzter Scope:

- Umsetzung ausschließlich durch den Projektinhaber persönlich; keine Codex-Implementierung oder automatischen Codex-Aufträge.
- Eigenständiges Python-CLI: Dateien rekursiv erfassen, Imports per AST analysieren, Funktionen/Klassen erkennen, Modulabhängigkeiten darstellen und möglicherweise unreferenzierte Module kennzeichnen.
- JSON-/Markdownberichte, optionale Pre-Commit-/Pre-Push-Nutzung; kein neues Repository oder Programmcode durch diesen Auftrag.
- Eigenständiges optionales CS50P-Projekt außerhalb des kritischen Pfads. Spätere Wiederverwendung in C27 optional; C27 bleibt unabhängig.
