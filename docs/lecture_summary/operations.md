# C26-LS-01 – Lokaler Betrieb und Entwicklung

## Start

Python 3.12 oder 3.13, Basisabhängigkeiten aus `pyproject.toml`, zusätzlich
`streamlit>=1.56`. Für den Fake sind keine LLM-SDKs, Schlüssel, Downloads,
Parsermodelle oder externe Dienste erforderlich.

```bash
python -m streamlit run lecture_summarizer_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Der eigene Einstieg ruft die vorhandene `show()`-Seitenkonvention auf und vermeidet
die schweren Legacy-Imports des allgemeinen `streamlit_app.py`. Die Seite liegt in
`frontend/pages/G_p0_lecture_summarizer.py`. Standard ist der ausdrücklich
synthetische Testkurs aus `tests/fixtures/lecture_summary/catalog.json`.

Kurs → Week 0 → Lecture oder Short wählen; Materialstatus und Ausschnitte ansehen;
Quellen und Summary-Typ wählen; erst **Summary starten** führt den Adapter aus.
Der Fake erstellt deterministische extraktive Entwürfe. Quellen über **Quelle
öffnen** prüfen. Jede Aussage bewerten, kommentieren und bei Bedarf zur Nachprüfung
markieren. Freigabe verlangt alle Aussagen `correct`, keine Nachprüfungen und keine
Validierungskonflikte. Freigabe gilt nur für den gespeicherten Quellumfang;
fehlende Folien bleiben ausdrücklich fehlend. Markdown und JSON sind anschließend
über die Download-Buttons verfügbar.

## Lokale Konfiguration

- `LECTURE_SUMMARY_CATALOG`: explizite Katalogdatei, maximal 8 MiB; fehlt sie oder ist
  sie ungültig, zeigt die UI einen Fehler. Kein Verzeichnisscan oder automatischer
  Zugriff auf den parallelen C08-Worktree.
- `LECTURE_SUMMARY_STORE`: eigener lokaler privater Ergebnisordner; Standard
  `data/lecture_summary` (ignoriert). Nicht auf fremde Daten-/Controllerordner setzen.
- In der UI: Summary-Typ, Quelle, Modelladapter/Modell, Prompt und Version,
  Temperatur, Inputbytes, Chunkzeichen, maximale Chunks, Outputtokens, Retrygrenze,
  Provider-Timeout, Run-Laufzeit und optional eigene Modellpreise.
- Reale Modelle: optionales `llm`-Abhängigkeitsprofil installieren, Adapter `litellm`
  und dessen Modellkennung wählen. Provider-Zugangsdaten ausschließlich in der
  lokalen Prozessumgebung konfigurieren; weder Katalog noch Prompt noch Export
  enthalten ein API-Key-Feld. Reale API-Aufrufe wurden nicht ausgeführt und sind
  nicht Bestandteil der Offline-Abnahme. Ein konfigurierter Modellname und ein
  installiertes SDK bestätigen noch keine gültigen Credentials/Erreichbarkeit.

## Adapter für verarbeitete Materialien

`Catalog` erweitert `LectureCourse` um Wochen (`Week`, bestehende `LectureSection`)
und Einheiten (`Unit`, Lecture/Short). `Material.resource` bleibt das vorhandene
`LectureResourceUnion`. `Material.blocks` sind bestehende `ContentBlock`, inklusive
`ContentLocator`. `ProcessingArtifact` ergänzt Parser-/Run-Identität und einen
Fingerprint der gesamten Blockprojektion.

- `transcript_blocks(TranscriptDocument, raw_sha256=...)`: erhält Segment-IDs und
  bekannte/fehlende Zeiten. Der Aufrufer muss den Originalhash und die fachlich
  erforderliche Verifikation unabhängig prüfen.
- `material_handoff_blocks(review)`: akzeptiert Ergebnisse des vorhandenen
  `prepare_material_handoff(...)` nur bei bestandenem Materialqualitätsgate.
  Übernimmt aktive Aggregationsblöcke und markiert ausgeschlossene Blöcke als
  Struktur. HTML-DOM, PDF-Seite und Codezeilen bleiben erhalten.
- Bereits anderweitig geprüfte Content-Blöcke können direkt in `Material`
  eingebettet werden. Kein direkter Zugriff auf Content-Store-ACLs/SQLite-Interna.
- `artifact(...)` erstellt den Fingerprint der adaptierten Blöcke. Originalhash,
  Quellidentität, Originalpfad, Parserversion und Processing-Run müssen vorhanden
  sein. `source_path` ist nur eine Referenz: die UI öffnet keine beliebigen Dateien.
- Unverarbeitete/fehlende Materialien als Katalogzeilen behalten; keine leeren
  Materialien durch generiertes Wissen ersetzen. `operator_verified` ist eine
  lokale vertrauenswürdige Operatorangabe, kein Ersatz für ein bestehendes Gate.

## Persistenz, Cache und Wiederanlauf

Ein Store erlaubt über eine Linux-Dateisperre einen schreibenden Run/Review.
Neue Starts während eines laufenden Runs werden abgelehnt. Pro Run maximal 32
Abschnitte, je höchstens zwei Versuche; keine parallelen LLM-Aufrufe. Default:
24 Abschnitte, 20 Sekunden Provider-Timeout, 120 Sekunden Run-Deadline.
Vor und nach jedem Aufruf wird die Deadline geprüft; der Adapter erhält die
verbleibende Zeit. Das ist keine OS-Prozessisolation für beliebige eigene Adapter:
ein Adapter muss den Timeout einhalten. Ein hängender Fremdadapter kann nicht
hart abgebrochen werden. Kein C16-Worker wird aktiviert.

```text
store/
  .run.lock
  runs/<run-id>/
    input.json       # unveränderlicher Input + Auswahl + vollständige Konfiguration
    state.json       # atomarer Laufstatus; Fehlerklasse ohne Provider-Fehlertext
    raw/             # Rohantworten und getrennte Fehler je Versuch
    sections/        # validierte Teilergebnisse, vor nächstem Aufruf gespeichert
    result.json      # konsolidiertes Ergebnis, nach Erstellung nicht überschrieben
    reviews/         # neue, an Ergebnis-SHA gebundene Review-Ereignisse
```

Cachefingerprint umfasst Material-/Block-/Originalhashes, Source-Auswahl, Inventory
(einschließlich fehlender Quellen), Titel, Summary-Typ, gesamten Prompt + Version,
Modell/Provider, Modell-/Chunk-/Limitkonfiguration und Verarbeitungsversion `ls-1`.
Nur vollständig gespeicherte, integritätsgeprüfte Ergebnisse `ready_for_review`
werden wiederverwendet. Wiederverwendung ist **keine** automatische Freigabe; der
persistierte Reviewstatus bleibt sichtbar. Explizites Neugenerieren erzeugt eine
neue Run-ID und erhält alle früheren Ergebnisse/Freigaben. Fehlerhafte Ergebnisse
`needs_attention` sind exportierbar, klar markiert und nicht freigabefähig.

Unterbrechung speichert Status und bisherige Abschnitte. Nach einem Prozessabbruch
markiert der nächste exklusive Schreibzugriff verwaiste `running`-Läufe als
`interrupted`. Wiederholung startet einen neuen Run; kein automatisches Fortsetzen
kostenpflichtiger Teilarbeit. Dateisperren sind nur für lokale kooperierende
Prozesse gedacht, kein verteilter Lock auf Netzlaufwerken. Der Store ist ein
lokaler Single-User-MVP ohne ACL- oder Manipulationssicherheitsgarantie.

## Reproduzierbare Offline-Abnahme

```bash
python -m pytest -p tests.offline_guard tests/test_lecture_summary.py tests/test_lecture_summary_ui.py
python -m scripts.lecture_summary_offline --output /tmp/lecture-summary-demo
```

`tests.offline_guard` verbietet Netzwerkverbindungen/Listener und native
Infrastrukturkommandos während der Tests. Der CLI-Lauf verwendet ausschließlich
den Fake. Er erstellt strukturierte Ergebnisse, kontrolliert alle Zitatbindungen,
speichert ein **synthetisches** Review, prüft Cachewiederverwendung und schreibt
Markdown/JSON/Report. Ein neuer Outputordner ergibt neue Run-IDs; semantische Inhalte
und Quellen bleiben deterministisch. UI-Nachweise erfolgen mit echtem Streamlit
`AppTest`, einschließlich Navigation, Start, Quellenansicht, Bewertung, Freigabe,
Cache und Download-Widgets.

Die aktuelle verwaltete Umgebung nutzt lesend installierte Basisabhängigkeiten und
Streamlit über `/tmp/c26-ls-01-venv`; Details und Resultate in `validation.md`.
Kein Paket wurde in fremden Worktrees installiert oder verändert.
