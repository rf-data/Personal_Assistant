# C26-CS50P-07 – vollständiges Wocheninventar: Validierung und Übergabe

28.10.2026. Ergebnis **HOLD**, C26 gesamt **HOLD**. Die Offline-Implementierung
und ein geprüfter Übergabepatch sind geliefert. Ein vollständig beschafftes
offizielles Wochenarchiv, eine positive Frozen-Installation oder eine
Produktionsfreigabe werden nicht behauptet.

## 1. Tatsächliche Basis und C06

Ausschließlich der vorbereitete Worktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50p-07` wurde bearbeitet.
Branch `feat/c26-cs50p-07-week-materials`, sauberer Anfangszustand, HEAD
`f273b718c4e4c8fc8a000625eb471a68abcf24b5`. Dieser HEAD entspricht dem gesicherten
C06-Branch in der separaten Kopie unter
`Personal_Assistant-cs50p-04/.c26-cs50p-06/repository.git`.
C04 `6351d443afe18f806d37d64010e7050b4b5fcd73` ist ein Vorfahr.
C06 ist damit in der **vorbereiteten lokalen Entwicklungsbasis enthalten**.

Alle sechs Einträge der C06-`SHA256SUMS` wurden lesend geprüft. Vollständiger
C06-Patch: `12e7dd97d9642f47be5761094d79716d6090ca446aaf86a321c963ec8413628e`;
Implementierungspatch:
`e482b0a3a36c334fe31383bee74087d369ad915fddc24c6f5a9c188195256bde`.
Die bestehenden C06-Validierungs-/Übergabedokumente wurden gelesen und erhalten.
[Maschinenlesende Git-Belege](../../artifacts/c26_cs50p_07/git-basis.json).

Keine Git-Metadaten geschrieben, kein neuer Branch/Worktree, kein Commit, Push,
PR-Schreibzugriff oder Merge. Der lokale `master` enthält den C06-HEAD nicht.
Ein Live-Remotezustand wurde in C07 nicht erneut abgefragt; eine Integration in
GitHub/`master` wird nicht behauptet. Die ausdrückliche Merge-Sperre dieses
Auftrags hat Vorrang. Dokumente und Code müssen später im normalen Reviewprozess
in `master` integriert werden. Der Repository-Lifecycle bleibt deshalb pending.
Alle vorhandenen Betreiber- und Fremdartefakte bleiben erhalten; es gibt keine
von C07 angelegten temporären Git-Artefakte zu entfernen.

## 2. Untersuchung und Architekturentscheidung

Vorhanden sind `parse_week_page`, hierarchische `ResourceCandidate`- und
`MaterialResource`-Verträge, die einseitige PSet-Ableitung `assignments.children`,
Downloadreceipts, SHA-256, atomare No-replace-Veröffentlichung, DNS-Pinning/
HTTPS-Schutz, Kapazitätsgrenzen und der TXT/SRT/VTT-Importer.

Die vorhandene `WeekReport`-Planung ist bewusst ein Snapshot-/Verarbeitungsplan
und behauptet keine vollständige Live-Woche. Ihr Vertrag bleibt unverändert.
C07 ergänzt einen eigenen **Download-only-Wochenvertrag** und Orchestrierung um
diese vorhandenen Komponenten. Short-Detailseiten werden lediglich für den
bestehenden Rollenparser normalisiert. Es gibt keinen zweiten allgemeinen
Lecture-Downloader, keine zweite Queue und keinen Verarbeitungsworker.

Der bestehende `TransferBudget` wurde unverändert aus `scripts.cs50p_mvp` nach
`tools_materials.capacity` verschoben und im bisherigen CLI reimportiert.
Dadurch benötigt der neue Wochenpfad nicht dessen Controller-Importkette.
`MaterialDownloader` erhält ausschließlich optierende Erweiterungen für
Texttracks, genehmigte CSV/JSON-Anlagen und lokale manuelle ZIPs. Bestehende
Aufrufer behalten ihre bisherigen Standardregeln.

## 3. Offizielles Week-0-Inventar und Evidenzgrenze

Die [offizielle Wochenübersicht](https://cs50.harvard.edu/python/weeks/0/)
verlinkt **1 Lecture und 5 Shorts**. Das
[Problem Set 0](https://cs50.harvard.edu/python/psets/0/) enthält **5 Aufgaben**.

| Zweig | Eigene offizielle Unterseite |
| --- | --- |
| Lecture | Week 0; separate [Notes](https://cs50.harvard.edu/python/notes/0/) |
| Short | [Visual Studio Code for CS50](https://cs50.harvard.edu/python/shorts/visual_studio_code_for_cs50/) |
| Short | [Functions](https://cs50.harvard.edu/python/shorts/functions/) |
| Short | [Variables](https://cs50.harvard.edu/python/shorts/variables/) |
| Short | [Return Values](https://cs50.harvard.edu/python/shorts/return_values/) |
| Short | [Side Effects](https://cs50.harvard.edu/python/shorts/side_effects/) |
| Aufgabe `indoor` | [Indoor Voice](https://cs50.harvard.edu/python/psets/0/indoor/) |
| Aufgabe `playback` | [Playback Speed](https://cs50.harvard.edu/python/psets/0/playback/) |
| Aufgabe `faces` | [Making Faces](https://cs50.harvard.edu/python/psets/0/faces/) |
| Aufgabe `einstein` | [Einstein](https://cs50.harvard.edu/python/psets/0/einstein/) |
| Aufgabe `tip` | [Tip Calculator](https://cs50.harvard.edu/python/psets/0/tip/) |

Diese Anzahl stammt aus den tatsächlichen Links. Im Discoverycode gibt es keine
festgelegte Short-/Aufgabenzahl. Shortlinks werden dedupliziert und eigene
Detailseiten verlangt. Aufgaben werden vom offiziellen PSet-Index abgeleitet,
mit eigener Identität, HTML-Beschreibung, Dateianlagen und Referenzen.

Das [hierarchische Reviewmanifest](../course_sources/cs50p_week0_review/manifest.json)
enthält **79 Objekte** mit sämtlichen geforderten Feldern. Der
[Downloadplan](../course_sources/cs50p_week0_review/download-plan.json) enthält
ausdrücklich **keine genehmigten Quellen**. Die
[Browserbelege](../course_sources/cs50p_week0_review/evidence.json) und der vorhandene
historische Week-0-Snapshot werden separat ausgewiesen.

**Die Live-Discovery ist noch nicht vollständig belegt:** Der Browser stellte
Short-Assetbezeichnungen bereit, aber nicht sämtliche exakten Hrefs ohne
anschließenden Abruf der Zielressource. Diese wurden nicht aus CDN-Namensmustern
erfunden. Unaufgelöste Hrefs stehen als `null` mit Fehlergrund im Manifest.
Quellindex-URLs konnten für vier Shorts ermittelt werden; der Side-Effects-Index
lieferte einen Browser-Cachefehler. Einige Aufgabenseiten enthalten externe
Referenzen, deren vollständige Hrefs noch aus Betreiber-HTML-Exporten erfasst
werden müssen. Kein Browserbeleg wird als gespeicherte Aufgabenbeschreibung oder
erfolgreicher Materialdownload ausgegeben.

Der Wiederaufbau ist offline reproduzierbar:

```bash
python -m artifacts.c26_cs50p_07.build_review_inventory
```

Die erzeugten Dateien dienen dem Review. Der produktive Discoveryweg liest echte,
hashgebundene Betreiberexporte und kann nach einzeln freigegebenen HTML-Abrufen
durch `discover --previous-inventory --archive` erweitert werden. So können
exakte Asset-Hrefs und Aufgabenseiten später ohne rekursiven Linkgraphen ermittelt
werden. Änderungen der historischen Shortlinks gegenüber der Browserliste
lassen den Review-Builder ausdrücklich scheitern.

Eng begrenzte Ausnahmen in `.gitignore` sichern ausschließlich diese C07-JSON-
Manifeste und Validierungsbelege für die spätere Repositoryintegration. Die
allgemeinen Ausschlüsse für Laufzeitdaten und Geheimnisse bleiben erhalten.

## 4. Beschaffungsentscheidungen

Lecture: offizielles TXT zuerst, SRT danach, Audio vor Video als letzter
Reviewkandidat. Im offiziellen Reviewmanifest ist das Lecture-TXT nur ausgewählt,
nicht validiert oder heruntergeladen. Alle Varianten bleiben sichtbar.
Slides-PDF und Notes-HTML sind unabhängige Pflichtmaterialien. Eine zusätzliche
Google-Slides-Variante muss nicht ebenfalls geladen werden.

Jeder Short hat eine eigene Inhaltsgruppe. Transcript → Subtitles → Audio →
Video gilt unabhängig für jeden Short. Fehlende Angebote erhalten explizit
`NOT_APPLICABLE`; unbrauchbare/falsch deklarierte Textdateien `FAILED`.
Nach einem Fehler wird die nächste Alternative im aktualisierten Plan sichtbar,
aber niemals ohne neue Freigabe abgerufen. Validierte Texte erfüllen genau ihre
eigene Inhaltsgruppe. Ein Lecture-Transcript kann keinen Short erfüllen.

Short-Asset-Hrefs bleiben im offiziellen Beispiel bis zu echten HTML-Exporten
blockiert. Für Visual Studio Code werden Slides angeboten, Source Code dagegen
nicht. Die vier anderen untersuchten Shorts bieten Source Code an. Für die
Lecture und diese vier Shorts sind somit **5 manuelle Pflichtpakete** vorgesehen;
Index/PDF/ZIP-Angebote bleiben separat sichtbar. Keine automatische
Source-Code-Beschaffung, keine ZIP-Extraktion, keine Codeausführung.

Die fünf Aufgabenbeschreibungen sind eigene Pflicht-HTML-Dateien. Bei den
untersuchten Week-0-Aufgaben wurde kein separat bereitgestellter Pflichtdatensatz
beobachtet. Tip Calculator enthält Startercode **inline** in seiner HTML-Seite;
dafür wird kein angeblicher Dateidownload erfunden. Referenzlinks bleiben
Metadaten. Zusätzliche Anlagen benötigen je Quelle einen exakten Typ-/Größengrant;
nicht unterstützte oder externe Formate bleiben blockiert.

## 5. Ressourcen- und Freigabevertrag

| Material/Resource | Harte Obergrenze |
| --- | ---: |
| HTML / TXT / einfache Anlagen | jeweils 1 MiB |
| SRT / VTT | jeweils 2 MiB |
| PDF | jeweils 8 MiB |
| Manueller Codeimport | jeweils 8 MiB |
| Gesamter Transfer einer Runde | 32 MiB |
| Archiv | 64 MiB |
| Checkpoints einer Runde | 16 MiB |
| Freier Speicher | mindestens 5 GiB plus nächster Transfer |
| Materialien / Discoveryseiten | 256 / 64, pro HTML-Seite maximal 1 MiB |
| Parallelität / Laufzeit | 1 / 540 s, systemd spätestens 600 s |
| systemd | 50 % CPU, 256 MiB RAM, kein Swap, 32 Tasks |
| Audio / Video | ausschließlich Referenzen; kein automatischer Abruf |

Alle Limits dürfen nur abgesenkt werden, die Speicherreserve nur erhöht.
Keine stillschweigende Budgetausweitung. Der Plan zeigt individuelle Obergrenzen,
noch unbekannte Remotegrößen, manuelle Reserven und unaufgelöste Hrefs. Eine
Freigabe darf in Summe höchstens das Rundenbudget ausschöpfen. Große Pläne müssen
selektiert werden. Ein tatsächlicher Archiv-/Reservekonflikt bleibt HOLD; mehrere
Runden heben das Gesamtarchivlimit nicht auf.

Freigaben binden den exakten Inventar-SHA, Herkunft, Material-ID, URL, Format,
individuelles Bytelimit, Reviewperson, Reviewbeleg und Zweck. Planungsfelder und
synthetische Inventare werden von den produktiven Freigabe-CLIs zurückgewiesen.
HTTPS-/Hostzulassung, Pfadprüfung und öffentliches DNS-Pinning bleiben bestehen.
Redirects, Cookies, Proxys und komprimierte Transfers werden nicht zugelassen.
Die Payloadsumme wird während des Streams begrenzt, ebenso Archiv und Reserve.
Bestehende verifizierte Bytes werden erneut gehasht und gegen das aktuelle
Material- und Grantlimit geprüft.

Die komplette Runde hält denselben äußeren Downloadlock wie der bisherige
MVP-Download-only-Lauf. Der vorhandene Downloader schützt einzelne Publikationen.
Interruptionen lassen Receipts und bereits veröffentlichte Dateien bestehen.
Unbekannte Partials werden nicht gelöscht oder adoptiert. Expliziter Retry,
neue Auswahl und neue Freigabe sind erforderlich.

## 6. Vollständigkeitsberichte

Der [offizielle Beispielbericht](../course_sources/cs50p_week0_review/completeness.json)
steht korrekt auf HOLD:

```json
{
  "counts": {"lecture": 1, "short": 5, "task": 5},
  "status": "HOLD",
  "c26_status": "HOLD",
  "processing_enabled": false,
  "overall": {
    "discovery_complete": false,
    "acquisition_complete": false,
    "manual_complete": false
  }
}
```

Eine unabhängige Erwartungsliste mit Eltern-/Typzuordnung erkennt gelöschte
Pflichtzeilen, darunter eine einzelne Aufgabe, Notes oder Slides, auch in den
betroffenen Zweigberichten. Reports werden je Woche, Lecture, Shortsammlung,
Short, PSet und Aufgabe ausgegeben. Die drei Bewertungsachsen bleiben getrennt.

[Das synthetische End-to-End-Beispiel](../../artifacts/c26_cs50p_07/synthetic-completeness-example.json)
belegt nach verifizierten Downloads zunächst `acquisition_complete=true`,
aber `manual_complete=false`. Erst nach den manuellen Importen sind alle drei
Achsen erfüllt und der Materialstatus wird FULLY_COMPLETE. C26 bleibt auch dann
HOLD. Diese Belege wurden beim Prüfen der tatsächlichen Rohbytes, Receipts und
Provenienz erzeugt; das ausdrücklich synthetische temporäre Archiv wurde danach
verworfen. Sie sind keine dauerhafte Integritätsauskunft über ein reales Archiv.

TXT/SRT/VTT werden vor Veröffentlichung über den bestehenden Importer auf UTF-8,
Inhalt, leere/ungültige Cues und Zeitreihenfolge geprüft; offensichtliche
HTML-/Fehlerantworten können kein Transcript werden. HTML-Material muss einen
Hauptinhalt und Titel enthalten. Die Prüfung belegt strukturelle Eignung,
keine fachliche Vollständigkeit oder perfekte Transkriptionsqualität.
Manuelle ZIP-Verifikation belegt Container/Hash/Größe/Provenienz, nicht die
Vollständigkeit aller im Container erwarteten Programmdateien.

## 7. Offline-Tests

Regressionslauf: **232 bestanden, 2 bewusst ausgelassen**, keine Fehler
([JUnit](../../artifacts/c26_cs50p_07/offline-tests.xml)). Der abschließende gezielte
Wochenlauf prüft **38 Offline-Fälle**
([JUnit](../../artifacts/c26_cs50p_07/week-tests.xml)).
Die ausgelassenen Alt-Tests erfordern explizite externe/privilegierte Integration.
Getestete Gruppen: Wocheninventar, bestehender Downloader, C04/MVP,
Kapazitätsgrenzen, bestehende HTML-Discovery und Wochenplanung sowie C06-Installer/
Frozen-Verträge. Kein gesamter Repositorytest oder realer Serverlauf wird behauptet.

Die 18 geforderten Szenarien sind abgedeckt:

1. Lecture mit Transcript und unabhängigen Notes/Slides.
2. Fehlendes Lecture-Transcript mit Subtitle-Auswahl.
3. Fehlende Lecture-Textquellen mit Audio als gesperrtem Reviewkandidaten.
4. Mehrere deduplizierte Shorts auf eigenen HTML-Seiten.
5. Short ohne Transcript mit eigenem Subtitle-Fallback.
6. Short ohne Subtitle-Angebot.
7. Sichtbar ausstehende manuelle Source-Code-Pakete.
8. Hash-/Provenienzimport, kein Überschreiben, manipulierte Rohdatei erkannt.
9. PSet mit mehreren eigenen Aufgabenbeschreibungen und Anlagen.
10. Fehlende Detailseite und entfernte einzelne Pflichtaufgabe.
11. Doppelte Links/URLs und identische manuelle Dateibytes mit eigener Provenienz.
12. HTTP-/DNS-/TLS-/Redirectfehler sowie private/gemischte DNS-Antworten.
13. Größen-, Transfer-, Archivreserve- und Grantgrenzen, auch bei Wiederverwendung.
14. Abbruch, Checkpoints und explizit genehmigte Wiederaufnahme.
15. Zweiter Lauf ohne weitere Transfers.
16. Berichte pro Kategorie und fehlende Notes/Slides.
17. Abgelehnte automatische Medien-/Source-Code-Grants und synthetische Produktionsherkunft.
18. Kein C16-Import/Start im isolierten Wochen-Runtime-Smoke.

Alle neuen E2E-Tests sperren DNS und Socketverbindungen und verwenden synthetische
HTTPX-Transporte. Die simulierte freie Disk ist ausdrücklich ein Testhostmodell.
Der erste breite Lauf scheiterte im bestehenden C06-Smoketest am tatsächlich
unterschrittenen 5-GiB-Limit; der
[ursprüngliche Beleg](../../artifacts/c26_cs50p_07/offline-tests.initial.xml)
bleibt erhalten. Daraufhin bekam ausschließlich der eigenständige synthetische
C06-Smoke den expliziten Schalter `--synthetic-host`, den sein Offline-Test setzt.
Ohne diesen Schalter bleiben dessen echte Kapazitätsprüfungen wirksam.
Produktive Limits und Installer sind nicht gelockert.

Der neue [Runtime-Smoke](../../artifacts/c26_cs50p_07/runtime-smoke.json)
lief in einem frischen Prozess ohne pytest/Parser-/Worker-Abhängigkeiten.
Er initialisiert den echten TLS-Transport ohne Verbindung und prüft vier
synthetische Transfers, Receipts, Wiederverwendung und FULLY_COMPLETE eines
kleinen Testinventars. Controller, Native Admission und Workerimporte sind
explizit gesperrt. Keine neuen Dependencies; C06-Pins/Lock/Wheelhouse unverändert.
Kein Beleg einer frischen Frozen-Wheelhouse-Installation.

Ruff-/Formatprüfung, JSON-/Vertragslesen und Patchprüfung sind in
[validation.json](../../artifacts/c26_cs50p_07/validation.json) bzw.
[handoff-validation.json](../../artifacts/c26_cs50p_07/handoff-validation.json)
zusammengefasst. Lokales systemd ist Version 252. `systemd-analyze verify`
meldet den fehlenden `/opt/.../venv/bin/python`; es gab keine Live-Installation
oder systemd-255-/Ubuntu-24.04-Abnahme
([Ausgabe](../../artifacts/c26_cs50p_07/systemd-verify.txt)).

## 8. Betreiberübergabe und offene Gates

Der [ausführbare Betreiberleitfaden](cs50p_week_materials_operator_guide.md)
kennzeichnet READ-ONLY/CHANGE und enthält Discovery, Manifest-/Quellenreview,
Einzelfreigabe, systemd-Start, Logs, Archivprüfung, manuelle Liste, späteren
Import, Completeness Report und selektive neue Freigaben für Wiederholungen.
Jede systemd-Instanz hat neue Eingabe-/Ergebnisnamen; nichts wird automatisch
installiert, aktiviert oder wiederholt.

Offen bleiben:

- Positive C06-Frozen-Wheelhouse-Installation und tatsächliche Host-Runtimeprüfung.
- Vollständige exakte Short-Asset-Hrefs und Aufgabenreferenzen aus echten,
  hashgebundenen Betreiberexporten; Side-Effects-Quellindex bei Bedarf erneut prüfen.
- Echte Quellen-/Lizenz-/Nutzungs-/Typ-/Größenfreigaben; sämtliche Quellen sind
  noch ungenehmigt. Keine Medienfreigaben oder Medienruntime.
- Tatsächliche Downloads und validierte Pflichtmaterialien sowie fünf manuelle
  Source-Code-Pakete; kein Erfolg für ein reales Wochenarchiv.
- Geprüftes C07-Staging, gesonderte Installation des neuen Unit-Templates,
  Ubuntu-/systemd-255-Abnahme und ausreichende echte Diskreserve.
- Normales PR-/Review-/Integrationsverfahren nach Aufhebung der Merge-Sperre.

Der [Übergabepatch](../../artifacts/c26_cs50p_07/handoff/c26-cs50p-07.patch)
ist gegen den exakten C06-HEAD anwendbar und mit Datei-SHA-256 sowie Vorwärts-/
Rückwärtsprüfung geliefert. HEAD/Branch bleiben unverändert. Keine fremden
Worktrees, historischen Branches, Stashes, Daten, Venvs oder bestehende C06-Belege
entfernt. Die vorbereiteten Git-Artefakte werden wegen ausstehender Integration
und fehlender C07-Eigentümerschaft ausdrücklich behalten.
