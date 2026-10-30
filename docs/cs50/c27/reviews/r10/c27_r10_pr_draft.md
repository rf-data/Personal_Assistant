# PR-Entwurf – bereit zur Entscheidung des Benutzers

**Titel:** C27: geprüfte lokale CS50-Lernpipeline mit Quellenbelegen und Exportabsicherung

**Ziel:** `rf-data/Personal_Assistant:master` (tatsächlichen Live-Stand später prüfen).
**Quellbranch:** `feat/c27-cs50-learning-pipeline`; bisher keine neuen Commits.
**Status:** READY_FOR_USER_APPROVAL für diesen Entwurf. Kein PR angelegt. Offene Entscheidungen sind Bestandteil der Freigabevorlage; Ausführung bleibt gesperrt.

## Beschreibung zur späteren Verwendung

Die Änderung verbindet bereits lokal geprüfte Kursmaterialien mit einer begrenzten Lecture-Summary-Pipeline. Sie ergänzt CLI und Streamlit-Einstieg, Originalquellenreferenzen, private Persistenz und Cache, separate Reviewereignisse sowie öffentliche JSON-/Markdown-Exporte. Die selektiv übernommenen vier CS50P-Komponenten und die C26-LS-Herkunft sind dokumentiert. Öffentliche Metadaten werden durch den R08-Exportvertrag abgesichert; private Originalprovenienz bleibt privat.

Der Vorschlag umfasst 32 Code-/Konfigurations-/Test-/Fixturedateien und 30 historische Dokumente, danach gesondert aktuelle R09-/R10-Dokumentation. Das explizite Dateiinventar und der Commitplan grenzen die Auswahl ab. Keine Rohdownloads, persönlichen Credentials, Umgebungen oder privaten Summary-Stores sind vorgesehen.

## Validierung und Grenzen

R09 schließt sechs exakte historische Fälle mit unveränderten Assertions: 6/6 bestanden. R08-CAP belegt 23/23 Regressionen, einen frischen Canary und einen echten lokalen CLI-Subprozess mit FakeLLM Exit 0. R10 hat diese bereits erfolgreichen und manifestverifizierten Nachweise übernommen; Recovery bestätigt erneut die unveränderten 62 Kandidaten. Keine neue vollständige Testmatrix, keine realen Provideraufrufe und keine Downloads.

F04 ist im definierten öffentlichen Metadaten-/Provenienzvertrag VERIFIED_FIXED; 75 genehmigte URLwerte bleiben erhalten. Kein allgemeiner Secretscanner für beliebige Quell-/Claimtexte. Globale Mypy-Schuld: 6.104 Diagnosen, kein globaler PASS. Week 0 bleibt PARTIAL: TXT-Nachweis erfolgreich, vollständige HTML-Auswahl am bestehenden Chunklimit; keine vollständige Wochen- oder fachliche Kursabnahme. Multiweek/Multicourse bleibt PLANNING_ONLY; Produktion NOT_APPROVED.

## Vor Erstellung verbindlich zu entscheiden

- I01: Umgang mit drei konkurrierenden Pfaden auf fix/c27-acceptance-exports und den inkompatiblen APIs; kein stilles Zusammenführen oder Überschreiben.
- P01/S01: Publikation historischer lokaler Pfade und repositoryrelativer Fixturepfade der beiden Beispiele; unveränderte Originalbelege erhalten.
- W01: Behandlung sechs historischer Whitespace-Zeilen ohne stilles Entwerten historischer Manifestbindungen.
- C3: dauerhafte Aufnahme aktueller R09-/R10-Dokumentation mit eng begrenzten JSON-Ausnahmen; private Vollbelege extern sichern.
- Später autorisierter Vergleich mit echtem master, Prüfung bestehender PRs/Reviewpflichten; aus dem lokalen 0/0-Vergleich folgt keine Live-Mergbarkeit.

Der Entwurf ist vollständig zur Scope-/Architekturentscheidung vorbereitet. Commitumfang bleibt NEEDS_REVIEW und Integration INTEGRATION_REQUIRED. Diese Vorbereitung behauptet keine bereits ausführbare oder genehmigte Veröffentlichung. READY_FOR_USER_APPROVAL ist keine Erlaubnis für Commit, Staging, Push, Fetch, Merge, Rebase, Reset, Checkout oder PR-Erstellung.
