# Operativer Issue-Entwurf C23–C32

**Nicht angelegt und nicht freigegeben.** Quelle: [issue_plan.v1.json](issue_plan.v1.json).
32 Entwürfe: zehn Parents und 22 Kinder. Stabile Schlüssel sind lokale Plan-IDs, keine GitHub-Issuenummern.
Die [Roadmap](../ROADMAP.md) enthält nur Meilensteine. Ausführung und Deduplizierung: [GitHub-Plan](github_execution.md).
Native Parent-/Sub-Issue-Beziehungen nach Freigabe verknüpfen; Cross-Repository-Referenzen als vollständige URLs.
Alle Entwürfe beginnen Backlog, ohne behauptete Umsetzung oder Liefertermine. P0 = Release-Gate, P1 = Kernpfad, P2 = optional/später.

## C23

[C23] Parsed Content Persistence

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Persistence`.
Parent: `keiner` · hängt ab von: keinem neuen Paket.

Akzeptanz:

- Bestehende Material-/Transcript-/Parsingverträge im ADR abgeglichen; PostgreSQL bleibt Option bis zur begründeten Entscheidung.
- Raw und Parsed Content persistent, versioniert und unabhängig von Knowledge nutzbar; Hash-/Quellen-/Seiten-/Block-/Zeitbezüge und idempotenter Reimport nachgewiesen.
- Lesevertrag, Rechte und Restorefähigkeit sind belegt; unbekannte Zeiten bleiben ausdrücklich unbekannt.

## C24

[C24] Indexing & Retrieval

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Retrieval`.
Parent: `keiner` · hängt ab von: `C23`.

Akzeptanz:

- Volltexttreffer referenzieren gespeicherte Source-/Parsed-Versionen samt Seite/Block/Zeit; Rechtefilter werden serverseitig geprüft.
- Indexversion, Reindexierung, Fehler und Stale-Erkennung sind getestet; Suchindex ist aus freigegebenen Quellen rekonstruierbar.
- Vorhandener Transcript-/Qdrant-Pfad geprüft; semantische Suche bleibt optional, reale Qualität separat evaluiert.

## C25

[C25] Search & Source UI

Repository: `rf-data/personal-assistant-ui` · Typ: `milestone` · Priorität: `P1` · Workstream: `UI`.
Parent: `keiner` · hängt ab von: `C23`, `C24`.

Akzeptanz:

- Kurs-/Quellenauswahl, Suche/Filter und lesbare geparste Inhalte über autorisierte APIs.
- Originalverweise und Belege mit Seiten/Blöcken/Zeiten; fehlende Positionen werden nicht erfunden.
- Job-/Indexstatus sowie leere, unzugängliche und veraltete Treffer verständlich; Browserabnahme für vereinbarten Umfang belegt.

## C26

[C26] Hetzner Production Release

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P1` · Workstream: `Operations`.
Parent: `keiner` · hängt ab von: `C23`, `C24`, `C25`.

Akzeptanz:

- Alle noch offenen C22-Gates mit gewählten Images, Identitäten, TLS, Ressourcen und Zielvolume geschlossen.
- Konsistenter Backup-/Restore- und Alarmzustellungsnachweis; dokumentierte Recovery und Verantwortlichkeit.
- CS50 über die reale UI auf ausdrücklich freigegebenem Zielhost nutzbar; begrenzter realer Testkorpus und Operator-Go-live-Freigabe protokolliert.

## C27

[C27] Legacy Code Review

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Legacy`.
Parent: `keiner` · hängt ab von: keinem neuen Paket.

Akzeptanz:

- Modul-/Import-/CLI-/Docker-Inventar für beide Repositories; aktive und manuelle Aufrufer getrennt.
- Wikimedia, Parsing, Download, Transkription und RAG auf Wiederverwendung und Duplikation geprüft.
- Konkreter Cleanup-/Kompatibilitätsplan mit Owner/Freigabe; keine pauschale Entfernung oder Migration.

## C28

[C28] Source Registry & Additional Sources

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.
Parent: `keiner` · hängt ab von: `C23`.

Akzeptanz:

- Registryanforderungen für eBooks/EPUB/PDF, Liora-Fortbildung, Apothekerkammer-Webinare und weitere Kurse.
- Quellidentität, Zugriffs-/Nutzungsrechte, Versionierung, Ingestionstrategie und Review festgelegt.
- Erste Erweiterung separat anhand berechtigter Quellen abgenommen; keine stillschweigende Bestandserfassung.

## C29

[C29] Entity Recognition & Linking

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Entities`.
Parent: `keiner` · hängt ab von: `C23`, `C24`.

Akzeptanz:

- Fachbegriffe als versionierte quellgebundene Annotationen mit Mehrdeutigkeitsstatus.
- Kanonische Entitäten und dokumentübergreifende Fundstellen nachvollziehbar verknüpft.
- Originaltexte unverändert; Fehler-/Disambiguierungsreview vor produktiver Navigation.

## C30

[C30] Wikimedia Entity Enrichment

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Entities`.
Parent: `keiner` · hängt ab von: `C27`, `C29`.

Akzeptanz:

- Bestehende Wikipedia-/Wikidata-Clients geprüft und Schnittstellen konsolidiert.
- QIDs als mögliche Identifikatoren, Sprachen/Disambiguierung, Cache/Retry/Rate Limits und Provenienz entschieden.
- Externe Informationen in der UI getrennt von lokalen Aussagen; keine ungeprüfte fachliche Wahrheit.

## C31

[C31] YouTube Discovery & Review

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.
Parent: `keiner` · hängt ab von: `C23`, `C27`, `C28`.

Akzeptanz:

- Registrierte Kanäle und begrenzte geplante Jobs für neue Metadaten/zulässig verfügbare Inhalte.
- Zusammenfassungen, Relevanz-/Qualitätsreview und Aufnahmeempfehlung mit Quellenbelegen.
- Manuelle Freigabe vor dauerhafter Übernahme; Knowledge-Eignung separat und optional bewerten.

## C32

[C32] Medium Email & Article Review

Repository: `rf-data/Personal_Assistant` · Typ: `milestone` · Priorität: `P2` · Workstream: `Sources`.
Parent: `keiner` · hängt ab von: `C23`, `C27`, `C28`.

Akzeptanz:

- Autorisierte E-Mails und Artikellinks mit Duplikaterkennung und Provenienz.
- Relevanz, Zusammenfassung und Aufnahmeempfehlung prüfen; Paywalls/Zugriffs- und Nutzungsrechte beachten.
- Manuelle Freigabe vor Quellenregistrierung/Inhaltsübernahme; keine Umgehung von Zugriffsbeschränkungen.

## C23-01

[C23-01] Persistenz-ADR und vorhandene Modelle vergleichen

Repository: `rf-data/Personal_Assistant` · Typ: `debt` · Priorität: `P1` · Workstream: `Persistence`.
Parent: `C23` · hängt ab von: keinem neuen Paket.

Akzeptanz:

- ArtifactReceipt/NormalizedDocument, TranscriptDocument, Legacy-Parsingmodelle, Dateiartefakte und C16-SQLite auf Zweck und Grenzen vergleichen.
- Source-/Parsed-Versionen, Referenzintegrität, Rechte, Restore und Idempotenz spezifizieren; PostgreSQL gegen bestehende Alternativen begründet entscheiden.
- Keine zweite Jobqueue und kein erzwungener Knowledge-Schritt.

## C23-02

[C23-02] Raw-/Parsed-Speicherung nach freigegebenem ADR umsetzen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.
Parent: `C23` · hängt ab von: `C23-01`.

Akzeptanz:

- Bestehende IDs, Hashes, Parser-/Schemaversionen und Locatorwerte verlustfrei persistieren.
- Rohbytes und geparste Inhalte getrennt und unabhängig von Derived Knowledge lesen; Vertragstests mit kleinen Fixtures.
- Fehler/atomare Veröffentlichung und parallele Zugriffe im gewählten Speichermodell prüfen.

## C23-03

[C23-03] Idempotenten Reimport und explizite Bestandsbindung absichern

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.
Parent: `C23` · hängt ab von: `C23-02`.

Akzeptanz:

- Gleiche Bytes/Version erzeugen keine Dublette; geänderte Quelle oder Parser erzeugt nachvollziehbare Version.
- Abweichende historische Source-Pfade bleiben gesperrt; Strategie aus PR #72/C21-Q.1 wiederverwenden, keine stillen Fallbacks/Symlinks.
- Bestandsübernahme nur nach separater Freigabe; Source-/Receipt-/Provenienz- und Hashkonflikte testen.

Bestehenden Vorgang vor neuer Arbeit abgleichen: [Referenz](https://github.com/rf-data/Personal_Assistant/pull/72).

## C23-04

[C23-04] Autorisierte Source-/Parsed-Leseverträge bereitstellen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Persistence`.
Parent: `C23` · hängt ab von: `C23-02`.

Akzeptanz:

- Paginiert nach Kurs/Quelle/Version lesen; Originalreferenz und Seiten-/Block-/Zeitbelege liefern.
- Owner-/Course-/Quellrechte serverseitig durchsetzen; keine beliebigen Hostpfade/Dateiserver.
- API-Beispiele und Kompatibilitätsvertrag für das UI-Repository veröffentlichen.

## C23-05

[C23-05] TXT-Import ohne erfundene Zeitstempel reparieren

Repository: `rf-data/Personal_Assistant` · Typ: `bug` · Priorität: `P1` · Workstream: `Sources`.
Parent: `C23` · hängt ab von: keinem neuen Paket.

Akzeptanz:

- TranscriptSegment verlangt derzeit float, TXT-Importer erzeugt None: Unknown-Time-Vertrag für Modell und Verbraucher definieren.
- Gezielte TXT-/SRT-/VTT-Regression sowie Chunker-/Evidence-Abweisung nicht zeitgebundener Daten ohne erfundene Zeitwerte.
- Nur den relevanten Rest von PR #9 behandeln; alten Patch und PR nicht automatisch übernehmen/schließen.

Bestehenden Vorgang vor neuer Arbeit abgleichen: [Referenz](https://github.com/rf-data/Personal_Assistant/pull/9).

## C23-06

[C23-06] Berechtigten Realmaterialkorpus und unabhängige Goldreferenzen bereitstellen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.
Parent: `C23` · hängt ab von: `C23-01`.

Akzeptanz:

- Fehlende Original-/Receipt-/Normalized-Bundles für Week-0-Notes/Slides/Source-PDF mit Rechten und Hashes inventarisieren; keine Downloads ohne Freigabe.
- C10/C13-Qualitätsrubrik für Text/Code/Bilder und separate reale C11-Formel-Gold-/Prediction-Paare festlegen; keine Goldableitung aus Vorhersagen.
- Bekannte Fehlstellen und synthetische/reale Ergebnisse getrennt ausweisen; CS50-Releaseumfang daraus festlegen.

## C24-01

[C24-01] Bestehende Suche prüfen und Indexstrategie entscheiden

Repository: `rf-data/Personal_Assistant` · Typ: `debt` · Priorität: `P1` · Workstream: `Retrieval`.
Parent: `C24` · hängt ab von: `C23-01`.

Akzeptanz:

- Transcript-Qdrant, Filter/Offsets, Chroma-/Legacy-RAG und mögliche Volltextlösungen vergleichen.
- Keine neue Vektordatenbank ohne ADR; PostgreSQL-Suche bleibt vom Persistenz-ADR abhängig.
- Knowledge-Extraktion ist keine Suchvoraussetzung; verbindlichen Text-/Quellenvertrag bestimmen.

## C24-02

[C24-02] Versionierten Volltextindex und Reindexierung implementieren

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.
Parent: `C24` · hängt ab von: `C23-02`, `C23-03`, `C24-01`.

Akzeptanz:

- Index enthält Source-/Parsed-Version, Locator und Rechtebezug; Roh-/Parsed-Daten bleiben autoritativ.
- Wiederholung, Teilfehler, veraltete Dokumente und kontrollierte Reindexierung testen; keine ungeprüfte Datenlöschung.
- Indexstatus und Fehler maschinenlesbar bereitstellen.

## C24-03

[C24-03] Quellengebundene Such-API und Trefferbelege liefern

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Retrieval`.
Parent: `C24` · hängt ab von: `C23-04`, `C24-02`.

Akzeptanz:

- Kurs-/Quellenfilter, Paging und begrenzte Anfragen mit serverseitigen Berechtigungen.
- Treffer enthalten eindeutige Version und echte Seiten-/Block-/Zeitbezüge sowie sichere Originalverweise.
- Stale-/Missing-Source und inkompatible Indexversionen ausdrücklich melden; UI-Vertrag veröffentlichen.

## C24-04

Optional; explizite Zurückstellung blockiert den vereinbarten Volltextkern nicht.

[C24-04] Vorhandenen Qdrant-/Transcript-Pilot abnehmen statt neu bauen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P2` · Workstream: `Retrieval`.
Parent: `C24` · hängt ab von: `C23-03`, `C24-01`.

Akzeptanz:

- Draft PR #72 samt C21-Q.1 und seinen getrennten Phase-A-/Phase-B-Gates reviewen; keine parallele Ingestion implementieren.
- Nur nach expliziter Bereitstellung/Freigabe von SDK, immutable E5-Revision und isolierter Instanz echte Upsert-/Readback-/Retrieval-/Recovery-Nachweise.
- Semantische Suche bleibt optional; bestehender Originalpfadkonflikt und Remote-Uploadfreigabe bleiben echte Blocker.

Bestehenden Vorgang vor neuer Arbeit abgleichen: [Referenz](https://github.com/rf-data/Personal_Assistant/pull/72).

## C24-05

[C24-05] Reale Retrievalqualität und Quellenrückbindung bewerten

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.
Parent: `C24` · hängt ab von: `C23-06`, `C24-03`.

Akzeptanz:

- Unabhängige reale Fragen/Goldfundstellen und Suchkonfiguration versionieren.
- Volltext und gegebenenfalls semantische Suche getrennt auswerten; Nenner, Fehler und nicht evaluierbare Fälle berichten.
- Qualitätsgrenzen und Releaseumfang manuell prüfen; keine Modellwerte aus synthetischen Fixtures erfinden.

## C25-01

[C25-01] Kurs-/Quellenauswahl und Suchfilter integrieren

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.
Parent: `C25` · hängt ab von: `C23-04`, `C24-03`.

Akzeptanz:

- Vorhandene UI-Settings/Auth und typisierten Client erweitern, keine Backend-Dateizugriffe.
- Auswahl, Suche, Paging und Filter nutzen autoritative APIs; leere und verweigerte Antworten unterscheidbar.
- Cross-Repository-Vertragsversion und Backend-PR verlinkt.

## C25-02

[C25-02] Parsed Content mit Original- und Fundstellenansicht anzeigen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.
Parent: `C25` · hängt ab von: `C25-01`.

Akzeptanz:

- Strukturierte Texte, Code und Bildreferenzen anzeigen; Seite/Block/Kapitel/Cue nur bei vorhandenem Beleg.
- Treffer führt zur konkreten Quelle/Version; Originalzugang bleibt berechtigungsgeprüft.
- Unbekannte Zeitstempel, fehlende Bildbytes und veraltete Quellen klar darstellen.

## C25-03

[C25-03] Job- und Indexstatus für Suche sichtbar machen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `UI`.
Parent: `C25` · hängt ab von: `C25-01`, `C24-02`.

Akzeptanz:

- Bestehendes C16/C18-Job-/Owner-/Course-Modell nutzen, Indexzustand aus Backend beziehen.
- Refresh/Fehler/Unavailable/Stale ohne automatische Schreibaktion oder künstlichen Fortschritt.
- Bestehende Admin-/Workflowansichten bleiben kompatibel.

## C25-04

[C25-04] Browserabnahme der Source-/Search-Nutzung dokumentieren

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.
Parent: `C25` · hängt ab von: `C25-02`, `C25-03`.

Akzeptanz:

- Echte Browserfälle für Filter, Deep Links, Paging, Tastaturbedienung und belegte Fundstellen mit festem Korpus.
- Viewer-/Operator-/Course-Grenzen sowie fehlende/stale Inhalte prüfen; AppTest getrennt berichten.
- Kein Browsernachweis durch bloße API-/AppTest-Erfolge ersetzen.

## C26-01

[C26-01] Gepinntes Authlib und UI-Startschutz abnehmen

Repository: `rf-data/personal-assistant-ui` · Typ: `debt` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: keinem neuen Paket.

Akzeptanz:

- Authlib fehlt im aktuellen UI-Lock; vorhandenes C22-Gate gezielt schließen.
- Geprüfte transitive Dependency-/Lockentscheidung und Imagebereitstellung, keine ungefragten Upgrades/Downloads.
- Guard-, Secret- und OIDC-Konfigurationstests; kein Demo-Auth im Produktionsprofil.

Bestehenden Vorgang vor neuer Arbeit abgleichen: [Referenz](https://github.com/rf-data/personal-assistant-ui/pull/5).

## C26-02

[C26-02] C22-Images und Container-Prozessgrenzen isoliert prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: `C26-01`.

Akzeptanz:

- Vorhandene C22-Builds/Profiles mit freigegebenen Digests bereitstellen; Non-root, Mounts, Health und fehlende Pflichtinputs prüfen.
- API-/Executor-/UI-Restart, C19 native PDF-Cancel, Parent-Death/Subreaper, SIGTERM/SIGKILL/OOM und Cgroup-/CPU/RAM/PID-Limits im Container testen.
- Keine Mehrhostfähigkeit ableiten; Befunde und verbleibende Gates protokollieren.

Bestehenden Vorgang vor neuer Arbeit abgleichen: [Referenz](https://github.com/rf-data/Personal_Assistant/pull/73).

## C26-03

[C26-03] TLS, OIDC, individuelle Rollen und Browserzugriff abnehmen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: `C26-01`, `C26-02`.

Akzeptanz:

- Privater API-Gateway mit korrektem SAN/CA, Ingress-WebSockets und Secretrotation.
- Echter Browser-Login/Logout/Expiry sowie Viewer/Operator/Owner/Course und individuelle Tokenbindungen.
- Keine öffentliche ungeschützte Admin-API, keine deaktivierte TLS-Prüfung; UI-Änderungen nur im UI-Repository.

## C26-04

[C26-04] Zielstorage und konsistenten Restore auf isoliertem Ziel prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: `C26-02`, `C23-02`.

Akzeptanz:

- Endgültiger Single-Host-Mount: identische UID/Pfade, flock/rename/fsync/SQLite-WAL und Quoten.
- C22-Backup/Restore wiederverwenden; zusätzlich gewählte Raw-/Parsed-Persistenz, Katalog/Config und getrennte Secrets abdecken.
- Leeres isoliertes Restoreziel, Hash-/Provenienzprüfung, interrupted/Quarantäne und Operator-Recovery; keine produktiven Daten überschreiben.

## C26-05

[C26-05] Produktionsmonitoring und echte Alarmzustellung prüfen

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: `C26-02`.

Akzeptanz:

- Vorhandene C15-Dashboards/Regeln und C22-authentisierten Scrape verwenden.
- Queue, Dauer, Fehler/Timeout/Cancel, Worker, Disk/Volume und Service-Health mit niedriger Kardinalität.
- Alertmanager/alternatives Routing ausdrücklich entscheiden und Alarmzustellung bis zum zuständigen Operator testen.

## C26-06

[C26-06] CS50 über die freigegebene UI Ende-zu-Ende abnehmen

Repository: `rf-data/personal-assistant-ui` · Typ: `feature` · Priorität: `P1` · Workstream: `Evaluation`.
Parent: `C26` · hängt ab von: `C25-04`, `C24-05`, `C26-03`, `C26-04`, `C26-05`.

Akzeptanz:

- Begrenzte reale CS50-Quelle erfassen/verarbeiten/persistieren/indexieren/suchen und Originalfundstelle über UI prüfen.
- Fehler, Neustart, Cancel und Wiederaufnahme mit freigegebenen echten Daten prüfen; synthetische Evidenz getrennt.
- Keine Knowledge-Extraktion erforderlich; fachlich akzeptierten Format-/Korpusumfang festhalten.

## C26-07

[C26-07] Manuelle Hetzner-Go-live-Entscheidung und Betriebsübergabe

Repository: `rf-data/Personal_Assistant` · Typ: `feature` · Priorität: `P0` · Workstream: `Operations`.
Parent: `C26` · hängt ab von: `C26-06`.

Akzeptanz:

- C22-Gates, Kosten/Hostfreigabe, Rechte, Backup, Retention, Incident-/Rollbackverantwortung und Releaseversion bestätigt.
- Operatorfreigabe mit Datum und Evidenz; C26-Parent erst danach als produktionsfreigegeben schließen.
- Merge oder grüne CI erzeugen keinen Rollout und keine automatische Produktionsfreigabe.
