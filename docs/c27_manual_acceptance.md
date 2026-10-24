# C27 – lokale manuelle MVP-Abnahme

Stand 24.10.2026. Implementierung in Backend-Draft #158 und UI-Draft #21.
Keine Produktionsfreigabe. Diese Anleitung ersetzt die temporären `/tmp`-Helfer.

## Vorbereitung und dauerhafter Start

Benötigt: beide C27-Checkouts, Python 3.12 und die bestehenden UI-/Backend-
Basisdependencies. Der Starthelfer installiert nichts. Keine Worker-/GPU-/Browser-
Extras erforderlich. Die normalen Repo-Lockdateien bleiben unverändert.

Auf diesem Rechner sind geeignete Dependencies bereits vorhanden:

```bash
c27_python=/home/robfra/0_Portfolio_Projekte/personal-assistant-ui-c26b/.venv/bin/python
c27_backend=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c27
c27_ui=/home/robfra/0_Portfolio_Projekte/personal-assistant-ui-c27
c27_workspace=/home/robfra/0_Portfolio_Projekte/c27-local-mvp
c27_sources=/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/lectures
```

Die vorhandene C26-Umgebung dient nur als Interpreter; sie wird nicht verändert.
Bei anderen Checkoutpfaden die Variablen anpassen. Alternativ einen bereits
eingerichteten eigenen UI-Interpreter verwenden. Das ist keine Abhängigkeit von
einem laufenden C26-Dienst. Ein späterer Neuaufbau kann regulär aus den vorhandenen
Lockdateien erfolgen; hier wurde dafür nichts installiert.

**Einmalig**, falls der Workspace noch nicht existiert:

```bash
cd "$c27_backend"
"$c27_python" -B -m scripts.lecture_summary_acceptance prepare \
  --root "$c27_sources" --workspace "$c27_workspace"
```

Der Workspace ist auf diesem Rechner bereits vorbereitet. Nicht nochmals darauf
registrieren: vorhandene Kataloge werden absichtlich nicht überschrieben. Für einen
neuen Quellenstand einen neuen Workspace wählen. Der Elternordner muss existieren.
Der Befehl liest genau vier explizit benannte Transkripte, validiert alle drei
Auswahlen und erzeugt nur private Katalog-/Konfigurations-/Cachedateien außerhalb
der Repositories. Quellen bleiben am ursprünglichen Ort und read-only.

**Bei jedem Start**, aus einem neuen Terminal zunächst die Variablen oben setzen:

```bash
cd "$c27_ui"
"$c27_python" -B scripts/lecture_summary_local.py \
  --backend "$c27_backend" --config "$c27_workspace/summary.json" --check

"$c27_python" -B scripts/lecture_summary_local.py \
  --backend "$c27_backend" --config "$c27_workspace/summary.json"
```

URL: **http://127.0.0.1:8501**. Stopp: **Strg+C im selben Terminal**. Der Helfer
startet die vorhandene `app_admin.py`, bleibt im Vordergrund und erzeugt keinen
weiteren UI-Einstieg oder Hintergrunddienst. Bei belegtem Port den bereits
laufenden eigenen Prozess regulär stoppen; kein `killall` und keine fremden
Prozesse beenden. Der Loopback-Start ist nicht öffentlich erreichbar.

Ohne `ADMIN_AUTH_MODE` nutzt der Helfer die bestehende lokale Demoidentität
`local-demo` mit Operatorrolle; kein Passwort erforderlich. Das ist eine sichtbare
Demoanmeldung, keine produktive Identitätsprüfung. Bereits ausdrücklich gewähltes
OIDC bleibt OIDC und benötigt die bestehende Streamlit-/Issuer-/Subject-
Konfiguration sowie eine angemeldete Operatoridentität. `disabled` wird abgelehnt.
`APP_ENV=local`, `JOB_BACKEND=disabled` und private lokale Daten-/Logpfade werden
für diesen Prozess gesetzt; C16-/C26-Konfiguration und `.env` werden nicht geändert.

## Bedienung

1. In der vorhandenen Admin-Navigation **Lecture Summarizer** öffnen. Den Hinweis
   **Offline-Demo** prüfen. Auch der Starthelfer zeigt den Modellmodus an.
2. Kurs **loviscach / mathe_1**, dann die Hauptlektion laut Falltabelle auswählen.
   Für Fall C ausschließlich die zweite angegebene Lektion hinzufügen. Die UI
   erlaubt maximal zwei Zusatzlektionen; sie wählt keinen ganzen Kurs automatisch.
   Es erscheinen nur explizit registrierte Kurse/Lektionen, nicht der ganze Mount.
3. Unter **Ausgewählte Quellen** Titel, Format, Rolle, Artefakt-ID und SHA256
   kontrollieren. Alle vier registrierten Quellen sind abgeleitete Transkripte.
4. **Kompakt** oder **Ausführlich** und einen Lernschwerpunkt wählen. Für einen
   Vergleich beide Stufen bewusst getrennt generieren und Ergebnisse benennen.
5. **Zusammenfassung erstellen** klicken. Im Mock-Modus entstehen begrenzte
   wörtliche Ausschnitte und Lernfragen, keine vollständige didaktische Synthese.
   Damit lassen sich Bedienung, Auswahl, Provenienz und Export abnehmen.
6. Ergebnisstatus **needs_review** sowie Inhaltsarten/Qualitätszustände prüfen.
   Wesentliche Aussagen sollen Q-Referenzen tragen. Im **Quellenverzeichnis**
   stehen Course-/Lecture-/Artefakt-/Dokument-/Chunk-/Source-IDs, SHA256,
   JSON-Pointer, Segment-ID und vorhandene Zeitbereiche. Dies belegt eine Stelle
   im Transkript; ohne verifizierte Media-ID ist es kein bewiesener Video-Link.
7. **Markdown herunterladen** und **LaTeX herunterladen** anklicken. Downloads
   im Browser explizit speichern. `.tex` ist ein vollständiges LuaLaTeX-Dokument;
   kein PDF wird automatisch kompiliert. Unicode, Formeln und Warnungen prüfen.

Der Cache unter `workspace/cache/` enthält private vollständige Summary-JSONs
einschließlich ausgewählter Quelltexte und Provenienz, Modus/Modell/Promptversion.
Er ist keine öffentliche Ablage. UI-Ergebniszustand ist zusätzlich sitzungsgebunden.
Änderungen an Auswahl/Optionen/Quellen verwerfen eine sichtbare veraltete Summary;
Versionen/Hashes bleiben Bestandteil des Cachekeys. Erneutes Generieren derselben
Auswahl kann aus dem lokalen Cache erfolgen. Nichts wird in die Produktiv-DB geschrieben.

## Drei belegte Evaluationsfälle

Alle Pfade im Folgenden sind relativ zum registrierten Lecture-Root. Die Zuordnung
`loviscach / mathe_1 / Lecture-ID` ist eine explizite lokale Bindung der beobachteten
Legacy-Datei, keine nachträgliche Änderung historischer Kursmetadaten. Ausgewählt
wird ausschließlich das genannte Transkript; Knowledge-Extrakte und PDFs werden
nicht still ergänzt. Segmente und Sekunden wurden aus den tatsächlichen Dateien
gelesen. Die Formeln unten sind gekennzeichnete Notationsübertragungen der
gesprochenen Stellen, keine fachlich abgenommene Referenzlösung.

| Fall | Auswahl im Kurs mathe_1 | Registrierte Quelle | Umfang |
|---|---|---|---|
| A: Fließtext | **01.01.2 – Weiter: Drei Arten Mathematik** | `loviscach/mathe_1/transcripts/01.01.2_weiter_drei_Arten_Mathematik.json` | 25 Segmente, 0–123,88 s |
| B: mehrere Formeln | **01.06.1 – Skalarprodukt** | `loviscach/mathe_1/transcripts/01.06.1_Skalarprodukt.json` | 90 Segmente, Aufnahme ca. 317 s |
| C: gemeinsame Übersicht | **01.05.1 – Rechnen mit Pfeilen** plus **01.05.2 – Von Pfeilen zu Vektoren** | `loviscach/mathe_1/transcripts/01.05.1_Rechnen_mit_Pfeilen.json` und `01.05.2_von_Pfeilen_zu_Vektoren.json` im selben Verzeichnis | 55 + 90 Segmente, insgesamt 145 |

Beobachtete Eingangs-SHA256:

```text
01.01.2  79a5dd28560679324fdfb3ab0b90307148add6e83267018235157dd718e756ce
01.06.1  8689b39c92085d24e9d183cf3b2c47ad44e6c63e07a0541fa716112e5d91577e
01.05.1  52ef686307b4d6b7888fa3304f5721f537ecd09b11d30c1db24ffe958fbc100b
01.05.2  1452a5c5984b3827a6c88aa2a7e75d30a18a6e3e7bba67bc142d9533ff8011e6
```

Zusätzlich tatsächlich vorhanden sind gleichnamige `knowledge/*_know_extract.json`
und das Kursskript `loviscach/mathe_1/documents/01_Ueberblick_Vektorrechnung.pdf`.
Knowledge ist bereits LLM-abgeleitet und kein unabhängiger Beweis. Für das Skript
gibt es hier kein `parsed/`-Verzeichnis mit unmittelbar nutzbarem Document-JSON;
ein PDF wird vom Summarizer nicht automatisch eingelesen. Es ist ein möglicher
manueller visueller Abgleich, keine aktuell eingebundene zusätzliche Quelle.
Das einzelne vorhandene PDF wurde begrenzt lesend geprüft: 10 Seiten, 109.815
Bytes. Seite 7 enthält die Nullvektor-Aussage und freie Vektoren, Seiten 8–9 den
Abschnitt Skalarprodukt. Die Formelstellen 20/21 sind Lückentextstellen; aus
diesem unvollständigen Skript keine ausgefüllten Formeln als verifiziert ableiten.

### A – Modellieren statt Formeln einsetzen

Erwartete Kernaussagen, unmittelbar im Transkript nachprüfbar:

- Segment 0–11, 0–61,96 s: Ingenieurmathematik als Modellbildung und -auswertung;
  Mathematik als Bau-/Werkzeugkasten, um reale Situationen zu beschreiben.
- Segment 12–15, 61,96–81,52 s: Klimawirkung und Solaranlage als genannte
  Anwendungsfragen. Keine Messdaten, Klimamodelle oder Solaranlagenformeln ableiten.
- Segment 16–24, 82,36–123,88 s: Unterschied zwischen Formeleinsetzen und dem
  Übersetzen einer realen Aufgabe in ein Modell; Auswertung häufig am Rechner.

Keine konkrete Formel oder Herleitung wird in dieser Quelle ausformuliert.
Formelkapitel darf fehlen. Prüfen: erklärt die Summary Modellbildung, vermeidet
sie erfundene Formeln und kennzeichnet eigene Lernfragen als didaktische Zusätze?
Das Fragment setzt die vorherige Lektion fort; nicht so tun, als enthalte es allein
eine vollständige Erklärung aller drei Mathematikarten.

### B – Skalarprodukt und geometrische Bedeutung

| Prüfgegenstand | Tatsächliche Fundstelle | Manuelle Prüfung |
|---|---|---|
| Komponentenregel und Zahlenbeispiel | Segmente 8–17, 39–80 s | Gesprochen: `3·2 + 4·(-3) + 5·1 = -1`. Vorzeichen korrekt? |
| Geometrische Darstellung | Segmente 20–31, 87–145 s | Notationsübertragung: `a·b = ||a|| ||b|| cos(φ)`. Variablen, Winkel und Gleichwertigkeit mit Komponentenrechnung erläutert? |
| Längen für das Beispiel | Segmente 37–43, 159–177 s | Gesprochen: Wurzel aus `3²+4²+5²` und Wurzel aus `2²+3²+1²`; keine zusätzliche Winkelzahl als Originalergebnis erfinden. |
| Senkrechtstellung und Vorzeichen | Segmente 61–79, 231–288 s | `cos(90°)=0`, Skalarprodukt dann 0; negatives Produkt im Beispiel mit Winkel größer 90° verbinden. Winkeldeutung benötigt Nichtnullvektoren. |

Die Notation im Transkript ist gesprochen und teilweise fehlerhaft geschrieben
(etwa „Skalaprodukt“, „Kursing“). Formeln deshalb ohne visuellen Abgleich nicht
als sicher original verifiziert ausgeben. Die Voraussetzung Nichtnullvektoren
bei Winkelbestimmung ist eine fachliche Bewertungsfrage; falls ergänzt, als
didaktische Erläuterung kennzeichnen, nicht als wörtliches Zitat behaupten.
Segmente 24–25, 114–129 s verschieben die detaillierte Begründung ausdrücklich
ins nächste Semester. Keine vollständige geometrische Herleitung als Bestandteil
dieser Lektion behaupten. Beispielkomponenten nicht aus einer unsichtbaren Skizze
still ergänzen. Skalarprodukt und Vektorprodukt nicht verwechseln.

### C – freie Vektoren, Rechnen und physikalische Anwendung

- **01.05.1**, Segmente 13–26, 64,8–138,8 s: Pfeile als Repräsentanten;
  parallele Verschiebung bei freien Vektoren.
- **01.05.1**, Segmente 28–35, 146,64–195,56 s: Addition durch Aneinanderhängen;
  `2b` als gleiche Richtung/doppelte Länge, `-b` als Gegenrichtung/gleiche Länge.
  Das sind Notationsübertragungen der gesprochenen Aussagen, keine rekonstruierten
  Tafelbilder. Segmente 40–47, 220,56–266 s: Nullvektor und neutrales Element;
  als eigene Notation etwa `a+0=a`, ohne eine originale Gleichung vorzutäuschen.
- **01.05.2**, Segmente 34–54, 140–241 s: Geschwindigkeit und Kraft werden über
  Betrag und Richtung erklärt. Segment 35 sagt im Transkript „95 km“ beim Tacho;
  eine fehlende Zeiteinheit nicht still als gesichertes Original korrigieren.
- **01.05.2**, Segmente 61–89, 264–374 s: freie mathematische und gebundene
  physikalische Vektoren unterscheiden; Kraftangriffspunkt ist relevant.

Bewertung: ein gemeinsamer Themenaufbau „Begriff → Operationen → Anwendungen →
Grenzen der Verschiebbarkeit“, keine zwei unverbundenen Einzeltexte. Definitionen
zusammenführen, aber den Unterschied frei/gebunden erhalten. Die Darstellung
physikalischer Vektoren ist im Vortrag vereinfacht; nicht unbesehen als
universelle Aussage über jede physikalische Vektorgröße wiedergeben. Geometrische
Zeigewörter und gezeichnete Kräfte brauchen visuellen Kontext. Keine zusätzlichen
Komponenten-, Kraftzerlegungs- oder Koordinatenbeispiele als Originalmaterial erfinden.
Jeder Themenblock muss auf die jeweils passende der beiden Lektionen verweisen.

## Modellbudget und bekannte Fehlerbilder

Reproduzierbare lokale Vorprüfung ohne HTTP-Client oder API-Aufruf:

```bash
cd "$c27_backend"
"$c27_python" -B -m scripts.lecture_summary_acceptance inspect \
  --config "$c27_workspace/summary.json" --model gpt-6-luna
```

Sie baut denselben vollständigen Request wie der Adapter und nutzt dessen
RequestBudget. Die Modell-ID ist nur eine Zeichenfolge in der lokalen Prüfung.
Gemessen mit Kompakt/Standardfokus am 24.10.2026:

| Fall | Quellblöcke | Konservative Eingangsobergrenze inkl. Prompt/Schema | Live-Limit 30.000 |
|---|---:|---:|---|
| A | 25 | 15.396 | passt lokal |
| B | 90 | 30.929 | Abbruch vor HTTP |
| C | 145 | 47.186 | Abbruch vor HTTP |

**B und C sind aktuell nur für Mock-/Bedienungs-/Provenienztests vorbereitet.**
Eine vollständige fachliche Prüfung einer echten Modellsynthese dieser beiden
Fälle ist mit den unveränderten aktuellen Grenzen blockiert. Diese Grenze ist
kein bestandener Didaktiknachweis. Keine Quellen werden still abgeschnitten oder
zusammengelegt. Der frühere lange Einleitungstext 01.01.1 lag ebenfalls über dem
Limit (34.343); daher Fall A mit der tatsächlich vorhandenen kürzeren Fortsetzung.
Ein späteres begrenztes hierarchisches Verfahren oder geeignete kleinere Quellen
wären gesondert zu entwickeln/evaluieren; keine Budgetaufweichung in diesem Auftrag.

Weitere Fehlerbilder:

- Mount/Quelle fehlt, Hash geändert oder mehr als 160 Blöcke/26.000 Textbytes:
  Generierung deaktiviert oder Abbruch; neue Version ausdrücklich registrieren.
- Falscher Checkout/Interpreter: Startprüfung meldet fehlendes Backend/Paket.
  Keine automatischen Installationen oder Wiederholungen.
- Viewer, abgelaufene OIDC-Sitzung oder nicht erlaubte Laufzeit: Anmeldung/
  Operatorberechtigung korrigieren; keinen produktiven Jobmodus einschalten.
- Live-Konfiguration ohne Uploadfreigabe/API-Key, Timeout, HTTP-/Schemafehler
  oder abgebrochene Ausgabe: Fehler ohne stillen Retry. Ein fehlgeschlagener
  Request kann trotzdem Kosten verursacht haben. Siehe separaten Live-Testvorschlag.
- Quality Gate `failed`: kein Export. `needs_review`: technisch verwertbar,
  fachlich offen. Der Mock rekonstruiert keine Formeln und beweist keine Didaktik.
- Browserdownload ist noch keine Sicherung auf der Festplatte. JSON im Cache
  enthält Quelltexte; nur in der privaten Ablage behalten.

## Fachliche Checkliste und Protokoll

Je Fall und Darstellungsstufe eine Zeile mit Datum, Source-SHA256, Modell,
Promptversion, Summary-ID, Reviewer und Befund festhalten. Bewertung je Kriterium:
`0 = falsch/fehlend`, `1 = teilweise/unklar`, `2 = ausreichend`; für reine
Mock-Ausschnitte fachliche Synthesekriterien **nicht prüfbar** statt künstlich bewerten.

- Auswahl vollständig und ausschließlich verarbeitet; keine externen Materialien.
- Zentrale Aussagen anhand konkreter Q-Referenz/Segmentstelle nachprüfbar.
- Thematische Ordnung, Begriffe, Voraussetzungen und nachvollziehbare Erklärungen.
- Formeln, Variablen, Vorzeichen und Einheiten stimmig; unsichere Stellen sichtbar.
- Keine erfundenen Originalbeispiele oder angeblich vorhandenen Herleitungen.
- Eigene Erläuterungen und ungeklärte Voraussetzungen ausdrücklich gekennzeichnet.
- Bei Gruppen sinnvolle Zusammenführung, keine größeren Wiederholungen und
  keine Verwechslung der Quelllektionszuordnung.
- Kompakt hilfreich als Übersicht; Ausführlich mit quellengebundenem Mehrwert.
- Markdown und vollständiges LaTeX enthalten Quellen und Unsicherheitsangaben.
- Gleiche Eingangs-SHA256 vor/nach Verarbeitung; keine Originaländerung.

Kritische Fehler separat protokollieren: erfundene Quelle, falsche sichere Formel,
falsche Lecturezuordnung oder nicht ausgewählte Inhalte verhindern eine fachliche
Abnahme unabhängig von der Punktzahl. Es gibt keinen automatischen fachlichen
Freigabeschwellwert. Der technische Status bleibt `needs_review`.

Der [separate Vorschlag für genau einen späteren Live-Test](c27_live_test_proposal.md)
enthält Modellkonfiguration, Übertragung, Budget und Abbruchkriterien. Er wurde
nicht ausgeführt und ist keine jetzige Übertragungsfreigabe.
