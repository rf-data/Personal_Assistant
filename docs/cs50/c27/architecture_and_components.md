# C27: Integrationsentscheidung und Komponenten

Stand 2026-10-29. Ausgangsbasis bleibt die gültige Phase-0-Bestandsaufnahme.
Dieser Bericht beschreibt nur die Fortsetzung und die geprüften Deltas.

## Unabhängige Gates

- **A – Repository und Schnittstellen:** ContentBlock/ContentLocator,
  MaterialResource, MaterialPlan, NormalizedDocument, ArtifactReceipt,
  TranscriptDocument und der vorhandene Material-Qualitäts-Handoff bleiben
  unverändert. Adapter ergänzen ausschließlich eine Summary-Hülle.
- **B – Summarizer:** lokaler Patch integriert, Unit-/AppTest- und Offline-Smoke
  geprüft. Keine Abhängigkeit von Gate C, keine Aktivierung eines Providers.
- **C – Real Data:** ausschließlich der zugängliche Penguin-Reviewbestand;
  technische Teilabnahme separat von Kursvollständigkeit und Fachreview.
  Ein Fehler in C sperrt nur die betroffene Auswahl/Teilabnahme.

## Konflikt und Patch

Siehe [vorab festgehaltenen Integrationsplan](integration_plan.md) und
[maschinellen Nachweis](summarizer_integration.v1.json). Der Originalpatch wurde
gegen seine SHA-256 geprüft. Sein einziger Anwendungsfehler war der Kontext am
Ende der `.gitignore`: Patchbasis `1584a28` enthält CS50P-07-Regeln, C27 auf
`a8af1d9` endet mit PM-02. Alle bestehenden C27-Regeln bleiben bytegleich erhalten;
nur der zehnzeilige C26-LS-01-Block wird angehängt. Keine Übernahme der fremden
Ignore-Gesamtdatei und keine Löschung anderer Ausnahmen.

Die Anwendung erfolgte zuerst in einem isolierten `git archive HEAD` unter
`/tmp`, ohne neuen Branch/Git-Worktree. Alle 26 gehashten Dateien außerhalb der
Ignore-Datei stimmten mit dem Manifest überein; das Manifest selbst kam ebenfalls
aus dem Patch (insgesamt 28 Patchdateien). Der isolierte Fake-Smoke bestand.
Anschließend dieselbe Integration im zugewiesenen C27-Worktree.

Eine nachgelagerte, abgegrenzte Korrektur betrifft `FakeLLM`: das frei aus dem
Quelltext abgeleitete Themenlabel konnte die bestehende Grenze von 200 Zeichen
überschreiten. Der echte Functions-TXT-Test deckte das auf. Nur das Label wird
begrenzt; Zitate, Quellen und Vertragsgrenzen bleiben gleich. Original- und
C27-Hash stehen im Integrationsnachweis. Der neue Regressionstest enthält eine
lange Definition und prüft, dass ihr vollständiger Text erhalten bleibt.

## Prüfung von CS50P-07/08

Lesend geprüft: `1584a28` (07), `143d341` (08), die Differenz der Kernkomponenten,
`week_acquisition`, `week_processing`, zugehörige Testfälle und Übergabeberichte.
Die Worktrees und ihre uncommitteten Änderungen wurden nicht übernommen.
[Exakte Herkunft der selektierten Dateien](cs50p_component_provenance.v1.json).

| Bedarf | Entscheidung und Begründung |
|---|---|
| Akquisition | Additive `WeekInventory`-/Freigabemodelle aus 08; lokale Downloadberichte werden verifiziert. Keine Netzwerkakquisition integriert oder ausgeführt. Downloadservice/Grants bleiben eine spätere, separate Freigabe. |
| Quellen-/HTML-/Textvalidierung | `source_acquisition.py` aus 08 und `text_validation.py` aus 07/08 unverändert: explizite hrefs, Text-/Fehlerseitenprüfung, bounded ZIP-Inspektion. |
| ZIP-Import-Abhängigkeit | Kleine 08-Änderung in `code_zip.py`: lokale SHA-Funktion statt Import des gesamten Batchmoduls. Verhalten und Bounds gleich, bestehende ZIP-Tests prüfen es. |
| Verarbeitung | Vorhandener HTML-v2-Parser und Transcript-Importer. Neue lokale Brücke `reviewed_week.py`, keine pauschale Übernahme von `week_processing.py`. Dessen Produktionssperre bleibt im Quellworktree bestehen. PDF-/Einzelcode-Handoff ist im Summarizer mit Fixtures geprüft; die neue Reviewbrücke bietet dafür noch keine Route. |
| Quellenbindung | URL → eindeutige Inventarzeile unter Lecture/Short → bestehende ResourceCandidate-/MaterialResource-Identitäten. Herkunftsbeobachtung nennt Inventardatei und Zeilenidentität. Lokale Verarbeitung erzeugt keine Downloadquittung. |
| Qualitätsgate | HTML erhält MaterialPlan, lokale Importquittung und den unveränderten `prepare_material_handoff`; nur dessen freigegebene Aggregationsblöcke gelangen in den Katalog. |
| Idempotenz | Schlüssel bindet sämtliche geprüften Eingabebytes, Adapter-/Parsercode, Python sowie Pydantic/BeautifulSoup-Version. Bei Wiederverwendung werden alle aktuellen Eingaben und gehashten Ausgaben erneut geprüft. |
| Wiederaufnahme | Exklusive atomare Veröffentlichung; vorhandene identische Dateien bleiben erhalten, Konflikte werden abgelehnt. Abschlussquittung zuletzt. Importzeit der ersten Transcript-Verarbeitung bleibt bei Wiederaufnahme erhalten. |
| Summarizer-Handoff | Bestehende ContentBlock-/Locator-Verträge → Summary-Katalog → explizite Materialauswahl → bounded Fake/Engine → separates Review und Exporte. |

Nicht übernommen: gesamte Branches, Runtime-/systemd-/Installationsdateien,
Controller, Downloadtransport, C16-/Deployment-/Produktionsänderungen oder
archivierte Bulk-Evidenz. 08-Tests dienen der Komponentenprüfung; ein vollständiger
08-Testlauf wird hier mangels Übernahme seiner Laufzeit nicht behauptet.

## Lokaler Datenpfad und verbleibende Grenzen

`verify_review` liest nur explizite Dateien: beide Inventare, beide Pläne,
Snapshotledger, dessen höchstens 32 Seiten, Downloadbericht und dessen höchstens
32 Dateien. Keine Symlinks, kein Traversal, keine implizite Discovery. Die
Planbindung verwendet den **kanonischen Modellhash**, nicht den anders
formatierten JSON-Dateihash. Ein Planungsvorschlag ist keine Freigabe.

Ausgaben liegen in einem separaten privaten Root außerhalb der Reviewquelle.
HTML-Rohbytes werden ausschließlich dort als lokaler Verarbeitungssnapshot
abgelegt, damit das vorhandene Qualitätsgate seine Speicher-/Quittungsverträge
prüfen kann. Originaldaten, Rechte und Inventarstatus werden nicht geändert.
Die bereits vorhandenen Reviewdateien wurden weder verschoben noch modifiziert.

Für HTML wird der im Inventar enthaltene CS50-Player derselben Lecture/des Short
als logische Videoquelle gewählt; ersatzweise dessen erstes ausdrücklich
inventarisiertes Video. Der Teilplan enthält nur diese Einheit. Das ist eine
technische Bindung, keine Prüfung des Videoinhalts oder vollständige
Materialabdeckung. Hauptlecture und Functions-Short bleiben verschiedene Units.

TXT-Zeit und Dauer bleiben unbekannt. ZIP-Verzeichnis und Mitglieder werden
samt SHA-256 und relativen Namen geprüft, jedoch nicht ausgeführt oder entpackt.
Ohne explizites Member-/Quellenmapping entstehen keine Code-Summary-Materialien.
`operator_verified` bedeutet hier konsistente, lokal beauftragte Dateiprüfung;
es bedeutet weder Lizenzfreigabe noch fachliche Bestätigung.

Der CLI verarbeitet alle gelieferten Materialien, fasst aber nur ausdrücklich
gewählte Materialien zusammen. Ohne Auswahl gelten alle verarbeiteten Quellen;
Grenzüberschreitungen werden pro Unit als `blocked` ausgewiesen. Andere Units
bleiben bearbeitbar. Er kann nur Fake-Aufrufe auslösen, keine Provideraufrufe.
