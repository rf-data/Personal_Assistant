# Analyse: gemeinsamer Course-Discovery-Adapter für CS50

Stand: 13. Oktober 2026. Grundlage sind sämtliche **18 lokalen HTML-Dateien**, das unveränderte `manifest.json` und der vorhandene Python-Code im aktuellen Arbeitsbaum. Die Original-URLs wurden anhand der HTML-Speicherkommentare (`saved from url`), interner Links und Seiteninhalte verglichen. Es wurden keine Webseiten nachgeladen, Videos heruntergeladen oder Transkriptionen gestartet. Aussagen über die Webseiten beziehen sich auf diese Snapshots, nicht auf einen verifizierten aktuellen Serverstand.

## 1. Vergleich der HTML-Strukturen

Alle vier Kurswebsites verwenden ein gemeinsames Grundlayout: Seitennavigation außerhalb von `main`, ein `main.col-lg` mit dem eigentlichen Inhalt, Überschriften und verschachtelte Listen. Die Startseiten enthalten im Hauptbereich vor allem „Welcome“, Teilnahmehinweise und ein Einführungsvideo. Die konkreten Wochenlinks stehen auch in der Seitennavigation. Eine Beschränkung aller Discovery-Schritte auf `main` würde deshalb den Kursaufbau übersehen.

| Kurs | Lokale Stichprobe | Kursgliederung im Index | Besonderheiten der Wochen-Seiten |
| --- | --- | --- | --- |
| CS50x | `index`, `week_0`, `week_1`, `lecture_0`, `practice_problems` | Wochen 0–10 plus nichtnumerischer Abschnitt `weeks/ai/` | Woche 0 Scratch, Woche 1 C; englische, portugiesische und spanische Video-/Textvarianten; HDR/SDR; Demos in Woche 0, Shorts und Section in Woche 1 |
| CS50 Python | `index`, `week_0`, `week_5`, `lecture_5`, `practice_1`, `cdn` | Wochen 0–9, mit Themen als Linktext | Woche 0 Functions, Woche 5 Unit Tests; Audio → MP3; Shorts; Slides als Google Slides/PDF; Source Code als Index/PDF/Zip |
| CS50 SQL | `index`, `week_0`, `week_6` | Wochen 0–6, Querying bis Scaling | Keynote/PDF statt Google Slides; Source Code Index/PDF/Zip; Video HDR/SDR; Problem Sets; Hinweise in `details` |
| CS50 AI | `index`, `week_1`, `lecture_1`, `practice` | Wochen 0–6, Search bis Language | Knowledge: Audio direkt verlinkt, Keynote/PDF, Source Code Index/Zip, Quiz und Project; MP4-Links mit `.mp4.download`; Player mit zusätzlichem `screen`-Parameter |

Die Wochen-Seiten beginnen mit `h1` („Week N“ plus Thema in `em`), einer Themenbeschreibung und einem Vorlesungs-`iframe[data-video]`. Danach folgt eine verschachtelte `ul.fa-ul`. Deren erster Hauptzweig ist „Lecture“; unter ihm liegen Audio, Notes, Slides, Source Code, Subtitles/Transcripts und Video. Weitere Hauptzweige sind Begleitangebote und Aufgaben. `li[data-marker]`, Font-Awesome-Icons und zusätzliche `span` spiegeln den aufklappbaren Zustand wider, nicht den fachlichen Ressourcentyp. Python verwendet für Shorts eine `ol` innerhalb des übergeordneten `li`.

Die als `lecture_*.html` bezeichneten Dateien sind **Notes-Seiten**, keine Medienübersichten: CS50x Lecture 0, Python Lecture 5 und AI Lecture 1 enthalten gegliederte Lehrtexte mit Inhaltsverzeichnis, Fragmentlinks und teils Code/Abbildungen. Auf diesen drei Seiten befinden sich keine Medien-Tags. SQL-Notes sind nur verlinkt, nicht lokal enthalten.

Drei weitere Seitentypen benötigen eigene Behandlung:

- `cs50x/practice_problems.html`: Übersicht mit `h3` „After Week N“ und anschließenden Übungslinks. Die Wochenbeziehung ergibt sich aus dem jeweiligen Überschriftenabschnitt.
- `cs50_python/practice_1.html` und `cs50_ai/practice.html`: einzelne Aufgaben („Indoor Voice“, „Shopping“), mit Beschreibung, Test-/Abgabehinweisen und externen Referenzen. Indoor Voice enthält eine Terminalaufzeichnung als iframe; Shopping verlinkt ein Starter-Zip.
- `cs50_python/cdn.html`: anderes Layout, `main > table.table`, Breadcrumb-Navigation im `thead`, Dateieinträge im `tbody tr[data-basename]`. Je Datei existieren Direkt-, `?download`-, `?highlight`- und `?view`-Links; Größe und Änderungsdatum stehen in `data-size` bzw. `data-lastmodified`. Das ist ein Codeverzeichnis, keine Lecture-Tabelle.

### Manifest und Original-URLs

Das Manifest ist derzeit **syntaktisch ungültiges JSON**: `json.loads` scheitert in Zeile 118, Spalte 9. Am Ende sind zusätzliche schließende Strukturteile und ein nachgestelltes Komma vorhanden. Ein regulärer Manifest-Loader kann die Datei noch nicht verarbeiten. Für diesen Bericht wurde sie als Text gelesen.

| Eintrag | Manifest | Im lokalen HTML dokumentierte Original-URL / Bewertung |
| --- | --- | --- |
| SQL `index.html` | `https://cs50.harvard.edu/x/` | `https://cs50.harvard.edu/sql/`; falscher Kurs im Manifest |
| AI `index.html` | `https://cs50.harvard.edu/x/` | `https://cs50.harvard.edu/ai/`; falscher Kurs im Manifest |
| AI `week_1.html` | `https://cs50.harvard.edu/ai/notes/1/` | `https://cs50.harvard.edu/ai/weeks/1/`; Wochen- und Notes-Seite fälschlich identisch |
| Python `cdn.html` | `https://cs50.harvard.edu/x/lectures/0/src0/` | `https://cdn.cs50.net/python/2022/x/lectures/0/src0/`; anderer Host, Kurs und Pfad |
| Python `practice_1.html` | `https://cs50.harvard.edu/python/python/psets/0/indoor/` | `https://cs50.harvard.edu/python/psets/0/indoor/`; doppeltes `python` |
| CS50x `practice_problems.html` | `https://cs50.harvard.edu/practice/` | `https://cs50.harvard.edu/x/practice/`; fehlendes Kurssegment |
| CS50x `lecture_0.html` | `https://cs50.harvard.edu/x/notes/0` | Speicherkommentar mit abschließendem `/`; Basis-URL für relative Links nicht ungeprüft übernehmen |

Die übrigen elf Einträge stimmen mit den Speicherkommentaren überein. Die vier `course.source_url` sind plausibel und entsprechen den jeweiligen Index-Snapshots. `role` ist uneinheitlicher Freitext („lecture“, „overview - week 1“, „commands“ usw.); für maschinelle Dispatch-Logik sollte ein kontrolliertes Vokabular verwendet werden. Die vorgeschlagenen Korrekturen sind lokale Evidenz, keine überprüften HTTP-Redirects. Manifest und HTML wurden für diese Analyse nicht geändert.

## 2. Erkannte fachliche Hierarchie

```text
Kurs (CS50x / Python / SQL / AI)
└─ Woche oder benannter Abschnitt (0, 1, …, ai)
   ├─ Hauptvorlesung
   │  ├─ Audio-/Videoangebote und deren Varianten
   │  ├─ Notes (HTML-Lehrtext)
   │  ├─ Slides (PDF, Keynote, Google Slides)
   │  ├─ Source Code (Index, PDF, Zip, einzelne Dateien)
   │  └─ Untertitel / Transkript mit Sprache
   ├─ Shorts / Section / Demos
   └─ Problem Set / Quiz / Project / Practice
      └─ Einzelaufgabe mit Beschreibung, Starterdateien, Referenzen
```

In den sieben lokalen Wochen-Seiten ist jeweils eine Hauptvorlesung sichtbar. Dies ist eine Beobachtung der Stichprobe, keine Garantie für alle Wochen. Auflösung, HDR/SDR und Sprachfassungen sind Varianten einer Vorlesung bzw. ihrer Ressourcen, keine zusätzlichen Wochen. Eine Section ist ein eigener Unterrichtsbaustein innerhalb der Woche, keine neue Kurswoche.

Wochenschlüssel müssen Strings sein: CS50x hat `ai`. Woche 0 darf nicht durch einen Wahrheitswerttest verloren gehen. Reihenfolge kommt aus der Kursnavigation; eine rein numerische Sortierung würde den AI-Abschnitt falsch behandeln. Die Navigationsbezeichnung kann vom `h1` abweichen (Python „Functions, Variables“ gegenüber „Functions“); beide sollten als Evidenz erhalten bleiben.

Aufgaben dürfen nicht nach lokalem Dateinamen zugeordnet werden: `practice_1.html` ist **Problem Set 0 / Indoor Voice**, `practice.html` gehört zu **AI Project 4 / Shopping**, obwohl die einzige lokale AI-Woche Woche 1 ist. Für Project 4 ist eine referenzierte, lokal noch nicht geparste Woche 4 anzulegen oder die Zuordnung als unvollständig zu kennzeichnen. Globale Practice-Übersichten benötigen die „After Week“-Abschnitte statt einer einzigen Kurszuordnung ohne Woche.

## 3. Ressourcentypen und Fundstellen

Der **vollständige Listenpfad** ist entscheidend: „PDF“ unter Slides und „PDF“ unter Source Code haben unterschiedliche Rollen. Ein flaches Sammeln aller `a[href]` verliert diese Information.

| Semantische Rolle | Fundstelle / Erkennung | Abbildung auf vorhandene Modelle |
| --- | --- | --- |
| Vorlesungsvideo | Lecture → Video → Sprache (optional) → MP4 → HDR/SDR → Auflösung; YouTube und `video.cs50.io`; zusätzlich `iframe[data-video]` | `LectureMedia(media_type="video")`; Varianten zusätzlich separat festhalten |
| Audio | Lecture → Audio, ggf. MP3-Unterliste, `.mp3` am CDN | `LectureMedia(media_type="audio")` |
| Notes | Lecture → Notes → `/notes/<key>/`; Inhalt selbst in `main` der Notes-Seite | `LectureScript(file_type="html")` |
| Slides | Lecture → Slides → PDF/Keynote/Google Slides | `LectureDocument`; Rolle `slides` zusätzlich festhalten |
| Quellcode | Lecture → Source Code → Index/PDF/Zip; CDN-Dateizeilen | `LectureMaterial(material_type="other")`; PDF bei Bedarf `LectureDocument` mit Rolle `source_code` |
| Untertitel | Lecture → Subtitles → Sprache oder Direktlink, `/lang/en/...srt` | vorläufig `LectureDocument(file_type="srt")` plus Rolle; eigenes Modell fehlt |
| Transkript | Lecture → Transcript(s), `/lang/<sprache>/...txt` | vorläufig `LectureScript(file_type="txt")` plus Rolle `transcript` |
| Shorts / Section / Demos | Hauptlisten auf Wochen-Seiten; Ziele unter `/shorts/`, `/sections/` oder Demo-Links | zunächst Material-/Seitenreferenz; erst Detailseite liefert Medien |
| Aufgaben | Wochenlink `/psets/`, `/quizzes/`, `/projects/`; Practice-Überschriftengruppen; einzelne Aufgaben in `main` | `LectureMaterial` plus Rolle `problem_set`, `quiz`, `project`, `practice`; kein pauschales Exam-Mapping |
| Starterdateien | z. B. Shopping → Getting Started → `shopping.zip` | `LectureMaterial`, supplement; Zugehörigkeit zur Aufgabe erhalten |
| Externe Referenzen | Links im Notes-/Aufgabentext, z. B. Python-Dokumentation | supplement / referenzierter Link; kein Discovery-Ziel für vollständiges Crawling |
| Terminaldemo | Indoor Voice: asciicast-iframe, zusätzlich Einbettungslogik | vorläufig `LectureOther`; kein normales YouTube-Video |

`foundation` passt zu Hauptvorlesung, Notes, Slides und zugehörigen Transkripten; `supplement` zu Shorts, Beispielen und Übungen als erste Mapping-Konvention. Daraus folgt keine Aussage über die Pflicht zur Bearbeitung: erforderliche Problem Sets bleiben fachlich Aufgaben. Die bestehenden zwei Kategorien können „verpflichtend“ und „optional“ nicht separat ausdrücken.

Gespeicherte Browserseiten schreiben iframe-`src` auf lokale `*_files/*.html` um. Diese Nebenverzeichnisse liegen nicht in der Stichprobe. Beim Python-Index ist die ursprüngliche YouTube-URL noch in `data-src` vorhanden, während `src` auf `saved_resource.html` zeigt. Wochen-Seiten bieten belastbare YouTube-/Player-Links; aus lokalen Dateinamen wie `HWQLez87vqM(1).html` darf keine Medien-ID konstruiert werden. Die Einführungsvideos im Index gehören zum Kurs, nicht automatisch zu einer Vorlesung.

## 4. Wiederverwendung der Lecture-Pipeline

### Aktueller Ablauf und Kopplung

`src/run_lecture_preparation.py` lädt interaktiv einen `LectureContext`, initialisiert Logger/Session und lädt pro `info_path` ein serialisiertes `RawDocument`. Der Ablauf ist: Loviscach-Blockextraktion → Linkfilter → Klassifikation → Skripte/Videos → ggf. HTTP-Auflösung → Deduplizierung/Metadaten → Kursmaterial → Bericht/JSON-Ausgabe. Er erwartet **keine rohen HTML-Dateien**. Das Ausgabeformat ist das ältere Dictionary mit `videos`, `scripts`, `material`, `other_links`, nicht ein `LectureCourse`.

`prepare_loviscach.py` sucht eine oberste Tabelle und Ressourcen in verschachtelten `other_node`-Elementen. Blocknummern werden aus Skriptdateien und Loviscach-Videotiteln abgeleitet, einschließlich Buchstabenpräfixen und zweistelligen Nummern. CS50-Wochenlisten erfüllen diese Voraussetzungen nicht. Die CDN-Tabelle ist ebenfalls kein Ersatz: sie enthält Code-Dateien statt Vorlesungsblöcken.

| Funktion / Modell | Bewertung |
| --- | --- |
| `extract_youtube_id` / `extract_media_id` in `prepare_loviscach.py` | reine URL-Verarbeitung für watch, embed, shorts, live, youtu.be wiederverwendbar; später in allgemeines URL-Modul auslagern; `video.cs50.io` wird nicht unterstützt |
| `filter_html_elements` | wiederverwendbar für vorhandene `RawDocument`-Bäume, nicht für BeautifulSoup direkt; dedupliziert früh nach href und verliert dadurch mehrere Vorkommen/Kontexte |
| `extract_link_title` | für entsprechende RawDocument-Linkknoten nutzbar; nur direkte Inline-Texte, keine allgemeine rekursive DOM-Textextraktion |
| `deduplicate_scripts` | URL-Deduplizierung mit Vereinigung der Blockzuordnungen als Ausgangspunkt; normalisierte URL und fehlende URLs behandeln, Rollen/Sprachen nicht verlieren |
| `deduplicate_videos` | vereint Blockzuordnungen nach `media_id`; ohne ID keine Deduplizierung; erhält keine Variantenliste und ist für Audio-/Videoangebote derselben Lecture allein ungeeignet |
| `get_resource_metadata_from_url` | brauchbar für echte Dateilinks; `.mp4.download` ergibt fälschlich `download`, Notes-/Player-URLs liefern keine sinnvolle fachliche Benennung |
| `enrich_resource_metadata` / `parse_resource_title` | nur bedingt geeignet: Unterstrich vor erstem Titelteil wird als Lecture-Nummer interpretiert; CS50-Titel/Nummer besser explizit aus Woche/DOM setzen |
| `classify_links` | CS50 benötigt eigenen Klassifikator: erkennt Videos nur über `/videos/v.php`, Skripte über „skript“; Notes/MP3/MP4/SRT/TXT/PDF überwiegend `other`; Zip/GitHub nur grob Material |
| `resolve_video_url` | HTTP-Zugriff auf Detailseite, erster YouTube-Link; für offline Discovery ausschließen, CS50 liefert bereits direkte Angebote |
| Loviscach-Block-/Titel-/Kind-Inferenz, `enrich_urls`, `extract_scripts` | an Anbieterpfade und Titelkonventionen gekoppelt; nicht als CS50-Logik übernehmen |
| `validate_lecture_resources` / `format_validation_report` | Ausgabeprinzip verwendbar; aktuelle Validierung zählt altes Dictionary und erwartet Video-IDs, kann CS50-Hierarchie/Varianten/Vollständigkeit nicht prüfen |

Weitere konkrete Grenzen im Runner: `block_node` wird nach der Schleife erneut verwendet und ist bei null Blöcken undefiniert; die dort erzeugten `all_links` werden anschließend nicht verwendet. Material innerhalb der Blöcke wird nicht übernommen. `extract_course_materials` akzeptiert nur `/material/` oder `/praktikum/`, also kaum CS50-Angebote. Unbekannte Links werden ohne fachliches Modell gesammelt. Ein Aufruf des bestehenden Runners wäre kein geeigneter Test für den neuen Adapter.

### Modelle und nachgelagerte Verarbeitung

`LectureCourse` bietet stabile Kursidentität, Provider, URL, flache Ressourcen, `lecture_blocks` und `unassigned_resources`. `LectureResourceUnion` ist eine diskriminierte Union der konkreten Klassen; beim Export müssen deren Stringwerte (`media`, `script`, `document`, …) verwendet werden. Das separate Enum enthält zusätzlich `audio`/`video`, obwohl diese keine Discriminatorwerte der Union sind.

`LectureMedia` trennt `source_url` und `media_url` und enthält ID und Dauer. `LectureScript`, `LectureDocument`, `LectureMaterial` sowie `LectureOther` reichen für einen ersten kompatiblen Export. `LectureMaterial.material_type` unterstützt nur `repository`/`other`: ein CDN-Index ist kein Git-Repository. `LectureResource.lecture_blocks: list[str]` erlaubt Mehrfachzuordnung. `RawLectureBlock` und `LectureSection` können betitelte Gruppierungen darstellen, werden aber von `LectureCourse` nicht als verschachtelte Struktur aufgenommen; `LectureSection` hat zudem keine Kind-Sektionen.

Es fehlen Felder für semantische Rolle, Abschnitts-URL/-Titel/-Reihenfolge, Elternbeziehung, Varianten, Sprache, Auflösung, HDR, Provenienz und Discovery-Warnungen. `KnowledgeSourceMetadata` enthält die Kurszuordnung, ersetzt diese Discovery-Daten aber nicht. Zusatzinformationen dürfen nicht als unbekannte Pydantic-Felder übergeben werden: etwa `youtube_url` im bestehenden Loviscach-`enrich_urls` ist kein deklariertes Feld von `LectureMedia` und wird bei der üblichen BaseModel-Konfiguration ignoriert.

Ergänzend geprüft: `discover_course.py` klassifiziert lokale Dateien nach Suffix und Dateinamen; das ist Dateidiscovery, kein Webadapter. `assemble_course.py` schreibt Metadaten und setzt Blockzuordnungen noch hart auf `["2"]`; dies darf CS50 nicht übernehmen. `plan_lecture.py` lädt im alten Format nur Videos/Skripte, Materialien sind auskommentiert. Seine Planung kann `DOWNLOAD`, `PARSE_DOCUMENT` oder `TRANSCRIBE` erzeugen; SRT als Dokument benötigt eine ausdrückliche spätere Routingentscheidung zu `PARSE_SUBTITLE`. TXT-Transkripte sind ebenfalls noch nicht als bereits vorhandene Remote-Transkriptangebote integriert. `ResourceTask` und `ResourceAction` bleiben sinnvolle spätere Ausführungsmodelle, gehören aber nicht in die reine Discovery.

## 5. Entwurf eines gemeinsamen CS50-Adapters

Empfehlung: **ein Parser mit vier Kurskonfigurationen**, separaten Parsern pro Seitentyp und einem expliziten Mapping auf die bestehenden Lecture-Modelle. Kein Kopieren der Loviscach-Tabellenlogik und kein Einbau in den bestehenden interaktiven Runner im ersten Schritt.

Vorgeschlagene Schnittstellen (Entwurf, noch kein implementierter Vertrag):

```python
parse_course_index(html, source_url, course_config) -> CourseDiscovery
parse_week_page(html, source_url, course_config) -> SectionDiscovery
parse_notes_page(html, source_url) -> PageEvidence
parse_practice_overview(html, source_url) -> list[RelatedPage]
parse_assignment_page(html, source_url) -> AssignmentDiscovery
parse_cdn_index(html, source_url) -> list[ResourceCandidate]
to_lecture_course(discovery) -> LectureCourse
```

Die Parser erhalten HTML und Original-URL als Werte und arbeiten ohne Netzwerk, globale Session, Dateischreiben oder Task-Ausführung. Ein separater Fixture-Loader verbindet Manifest und lokale Dateien. Ein späterer Fetcher kann denselben Vertrag mit HTTP bedienen; der Parser entscheidet nicht selbst, welche Seiten nachgeladen werden.

Ein kleines Discovery-Zwischenmodell bewahrt zunächst mehr Information als die bestehenden Ressourcen:

- Kurs: `course_id`, `title`, `provider="Harvard"`, Plattform `CS50`, Root-URL, optionale Ausgabe-/Versionsinformation.
- Abschnitt: stringförmiger Schlüssel, Titel, Reihenfolge, URL, Status `referenced`/`parsed`; Lecture-/Begleitbausteine mit Elternbeziehung.
- Ressourcenkandidat: Rolle, Titel, Original-/aufgelöste URL, Listenpfad, Format, Blockzuordnungen, Sprache und optional Medien-ID.
- Angebotsgruppe: logische Lecture-Ressource und Varianten mit Player/YouTube/MP4, Auflösung, HDR/SDR sowie `screen`-URL; Roh-URLs bleiben erhalten.
- Evidenz/Warnung: Quelldatei, Originalseiten-URL, DOM-Fundstelle, widersprüchliches Manifest, unbekannte Struktur und noch fehlende Detailseite.

Parsing-Regeln:

1. Manifest streng validieren; Fehler mit Datei/Eintrag benennen. Lokale Speicherkommentare nur als Audit-Evidenz behandeln. Widersprüche nicht still überschreiben. Für die aktuelle Analyse lassen sich korrekte Basis-URLs aus den Snapshots ableiten; ein produktiver Loader sollte konsistente Eingaben verlangen.
2. Im Index Wochenlinks über Host und Kurspräfix plus `/weeks/<key>/` identifizieren, Navigation gezielt einschließen und Duplikate nach URL zusammenführen. Titel aus Navigation und Kurs-`title` bewahren; Einführungsvideo gesondert erfassen.
3. Auf Wochen-Seiten `main` abgrenzen. `h1`/URL liefern Schlüssel und Thema. Ressourcenlisten rekursiv durch `ul` **und** `ol` lesen. Das Label eines `li` nur aus dessen eigenen Text-/span-/a-Kindern bestimmen, nicht aus dem Text seiner gesamten Unterliste; Icons ausblenden. Den Kontextpfad an alle Kinder weiterreichen.
4. Typ/Rolle primär aus Listenpfad, sekundär aus URL und Dateiformat bestimmen. Notes, Aufgaben, Shorts und CDN-Indizes als bekannte Seitentypen markieren. Unbekannte Links mit Kontext erhalten; kein wahlloses Follow aller Links.
5. Relative URLs mit `urljoin` gegen die geprüfte Original-URL auflösen. Fragmentlinks auf dieselbe Seite nicht als Ressourcen exportieren. Browserlokale Assets separat erkennen. `.mp4.download` als Angebot mit Medienformat MP4 behandeln, ohne die Roh-URL umzuschreiben.
6. Medien-ID aus explizitem YouTube-Link oder geprüftem CS50-Playerpfad ableiten; iframe nur ergänzend. Playerparameter wie `screen` bewahren. Videoangebote gruppieren, Sprachfassungen und Qualitätsvarianten erhalten. Audio und Transkripte über Lecture-Zugehörigkeit verbinden, nicht durch gleiches Dateisuffix.
7. CDN-Dateien pro `tr[data-basename]` extrahieren, Eltern-/Breadcrumblinks ausschließen; `download`, `view`, `highlight` als Angebote derselben Datei erfassen. Queryparameter nur für diesen bekannten Verzeichnisparser gruppieren, nicht global entfernen.
8. Flachen `LectureCourse` erst an der Ausgabegrenze erzeugen: pro Kurs etwa Block `"0"`, `"1"`, `"ai"`, Lecture-Nummer explizit setzen. Kursübergreifende Identität im Zwischenmodell durch Kurs-ID plus Abschnittsschlüssel sichern. Varianten/Evidenz als begleitendes Discovery-Ergebnis erhalten; keine verlustfreie Abbildung auf das heutige Modell behaupten.

Die Kurskonfiguration benötigt insbesondere `course_id`, Root-/Pfadpräfix und Titel. CDN-Jahre und Semester werden aus gefundenen Links gelesen: CS50x 2026 verweist auf `2025/fall`, Python auf `2022/x`, SQL auf `2023/x`, AI-Lecture auf `2020/spring`, während Shopping-Dateien `2023/x` nutzen. Aus einem Kursjahr lassen sich keine vollständigen CDN-URLs berechnen.

## 6. Noch nicht abgedeckte Strukturen und Fehlerquellen

Die Stichprobe ist ausreichend für gemeinsame Grundregeln, aber nicht für einen vollständigen Kursimport:

- Nur sieben Wochen-Seiten sind lokal vorhanden. Nicht enthalten: CS50x `weeks/ai/`, spätere Wochen, tatsächliche Section-/Shorts-/Demo-Seiten, komplette Problem-Set-/Project-/Quiz-Übersichten, Abschlussprojekte und SQL-Notes. Der Index beweist deren Verlinkung, nicht ihre Detailstruktur.
- Nur ein CDN-Verzeichnis ist vorhanden; Unterverzeichnisse, andere Dateitypen, zusätzliche Spalten und alternative Verzeichnislayouts sind nicht erprobt. Nicht rekursiv alle Eltern-/Kinderlinks verfolgen.
- `details/summary` enthält Anleitungen und URLs in Codeblöcken (`wget ...`), die ein reiner Anchor-Parser nicht findet. In CS50x Woche 1 ist das Zip zusätzlich im Source-Code-Zweig verlinkt; für andere Seiten ist das nicht garantiert. Codeblock-URLs zunächst als Warnung/Evidenz, nicht als ausführbare Befehle behandeln.
- Browser-Snapshots enthalten UI-Zustand, lokalisierte Fristen, umgeschriebene iframe-/Bild-/Scriptpfade und fehlende Nebenassets. Stylewerte, iframe-IDs, `(1)`-Dateinamenssuffixe und aufgeklappte Icons sind keine stabilen Selektoren. Überschriften-IDs stehen teils auf vorhergehenden leeren `a`, nicht auf `h1`/`h2` selbst.
- Notes enthalten TOC-Links und wiederholte Überschriftenpermalinks. Frühe href-Deduplizierung kann Kontext verlieren; Fragmente sind für Inhaltsgliederung nützlich, aber keine weiteren Lecture-Ressourcen.
- Aufgaben enthalten Fristen, Hilfe, Abgabe-, Installations- und Literaturverweise. Diese Links sind nicht gleichwertige Lehrmaterialien. Shopping nennt eine Frist 2027; das ist Snapshot-Inhalt und keine hier überprüfte aktuelle Kursfrist.
- Fehlende Lizenzseiten: Es gibt Links auf kursbezogene `/license/`, aber keine lokale Lizenztexte. `license` nicht aus dem Provider ableiten oder erfinden.
- Redirects, Fehlerseiten, JavaScript-only-Inhalte, alternative Live-Einbettungen und Erreichbarkeit der Medienlinks sind offline nicht getestet. Ein Parser muss bei fehlendem `main`, unbekanntem Listenlayout oder widersprüchlicher Kursidentität warnen/fehlschlagen, statt erfolgreich einen leeren Kurs zu liefern.
- Gleichlautende Labels (`PDF`, `Index`, `4K`, `English`) kollidieren bei Titel-basierten IDs. Ressourcenidentität muss URL/Rolle/Kontext berücksichtigen. Medien-Deduplizierung nach ID darf Sprach-/Player-/Qualitätsangebote nicht verschlucken.

## 7. Vorschlag für einen kleinen ersten Implementierungs-PR

**PR-Titel:** „Add offline CS50 course and week discovery with fixture validation“.

Der erste PR implementiert ausschließlich Kursindex- und Wochenparser für alle vier Kurskonfigurationen, mit einem kleinen Discovery-Zwischenmodell und einem expliziten Export auf `LectureCourse`. Notes, Aufgaben, Shorts, Sections und CDN-Indizes werden zunächst als typisierte Referenzen erfasst; ihre Detailparser bleiben Folgearbeit. Die oben belegten Manifestfehler werden im PR korrigiert, `role` wird vereinheitlicht und die Fixture-Integrität streng geprüft. Der jetzige Bericht ändert das Manifest noch nicht.

Vorgeschlagene neue Dateien: `src/tools_lecture/prepare_cs50.py`, ein getrenntes CS50-Discovery-Modellmodul und Offline-Tests mit den vorhandenen HTML-Fixtures. Bestehende Runner und Loviscach-Verhalten bleiben im ersten PR unangetastet. Ein Test-/Beispielaufruf gibt das Discovery-Ergebnis zurück; kein Aufruf von Planung, Download, Transkription oder Verarbeitung.

Abnahmekriterien mit gezielten Tests:

1. Alle vier Indizes liefern die verlinkten Abschnitte in Navigationsreihenfolge: CS50x zwölf Einträge einschließlich `ai`, Python zehn, SQL sieben, AI sieben. Nicht vorhandene lokale Wochen bleiben `referenced`, nicht scheinbar vollständig geparst.
2. Alle sieben lokalen Wochen liefern Hauptvorlesung, Notes-/Audio-/Slides-/Code-/Textangebote und korrekte Blockzuordnung. Woche 0 funktioniert; SQL `screen` bleibt erhalten; AI `.mp4.download` wird als MP4 erkannt.
3. CS50x-Sprachen und HDR/SDR bleiben als Varianten sichtbar. PDF unter Slides und PDF unter Source Code erhalten unterschiedliche Rollen. Audio wird nicht als zusätzliches Video exportiert.
4. Einführungsvideos, Navigations-/Fragmentlinks und lokale iframe-Sicherungspfade werden nicht fälschlich als Lecture-Downloadangebote behandelt. Shorts/Section/Problem Set/Quiz/Project bleiben Begleitreferenzen.
5. Manifest ist gültiges JSON; alle 18 Dateien sind eindeutig zugeordnet; die sechs inhaltlichen URL-Widersprüche und der Slash-Unterschied sind behoben bzw. dokumentiert. Ein künstlich widersprüchlicher Eintrag erzeugt eine verständliche Diagnose.
6. Ein wiederholter Parse liefert deterministische IDs/Reihenfolge; Mehrfachvorkommen vereinen Zuordnungen ohne Variantenverlust. Ein Netzwerkwächter im Test stellt sicher, dass kein HTTP-Zugriff erfolgt; Import-/Mappingtests prüfen die tatsächlichen Pydantic-Discriminatorwerte.

Folge-PRs können anschließend Practice-/Assignment-/CDN-Detailparser, verlustarme Variantenmodelle und eine bewusste Integration in Planung/Verarbeitung ergänzen. Die vorhandenen Modell- und Loadergrenzen sollten vor einem vollständigen End-to-End-Import geklärt werden.
