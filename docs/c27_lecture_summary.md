# C27 Lecture Summarizer: lokaler MVP

Stand: 24.10.2026. Backendbasis `e502aa9` (master); UI-Basis `e4be7a2` (main).
Draft-PRs: [Backend #158](https://github.com/rf-data/Personal_Assistant/pull/158)
und [UI #21](https://github.com/rf-data/personal-assistant-ui/pull/21).
**Manuelle Abnahme:** Dauerhafter Start über den versionierten UI-Helfer
`scripts/lecture_summary_local.py` und einen privaten persistenten Katalog.
[Bedienungsanleitung, drei belegte Loviscach-Fälle und fachliche Checkliste](c27_manual_acceptance.md).
Der [separate Live-Testvorschlag](c27_live_test_proposal.md) ist ausschließlich
vorbereitet; kein API-Aufruf oder Upload ausgeführt. Die `/tmp`-Recovery-Helfer
werden nicht mehr benötigt. Das vollständige Modellrequestbudget wurde offline
geprüft: der kurze Textfall passt, die vollständigen Formel-/Gruppenfälle liegen
über der bestehenden Grenze und sind vorerst nur offline evaluierbar.

C27 ist ein synchroner, ausdrücklich aktivierter Entwicklungsmodus. Er benötigt
keinen C16-Worker, Controller, Queue, Content-Store oder Datenbankbootstrap.
Produktionskonfiguration, historische Pilotdaten und die fünf geschützten Drafts
werden nicht verändert. Die C27-Branches/Checkouts bleiben für das Draftreview
erhalten. Dokumentation liegt bis zum gesondert freigegebenen Merge im Draftbranch;
eine Integration in master/main wird nicht behauptet.

## Vorhandene Komponenten und Wiederverwendung

| Bereich | Bestehende Implementierung und C27-Nutzung |
|---|---|
| Legacy-Kurse | `src/model_lecture/data_resources.py`: `LectureCourse`, Ressourcen, `lecture_no`, `lecture_blocks`, `local_path`, `content_hash`; keine Änderung historischer Modelle |
| Provider/Zuordnung | `prepare_loviscach.py`, `prepare_cs50.py`, `assemble_course.py`, `discover_course.py`; Loviscach-Nummern/Blöcke bleiben bestehen. Der generische Assembler enthält feste Blockwerte `2`; diese sind keine verlässliche Lectureidentität |
| Legacy-Pfade | `LectureCourse.root`, `src/utils/path_helper.py`, `src/core/config.py`: Provider/Kurs unter `data_lectures`, Kategorie-/Dateinamen bleiben erhalten |
| Transkripte | `TranscriptDocument` und `TranscriptSegment`; C27 übernimmt Segment-ID, Zeitbereich und explizit unbekannte Zeiten. Es transkribiert oder lädt nichts herunter |
| PDF/HTML | Vorhandene Parser unter `src/tools_materials/parse_*`; C27 liest deren `NormalizedDocument` mit Seiten-/DOM-Lokatoren. Ungeparste PDFs/HTML werden nicht automatisch verarbeitet |
| Wissen/Chunking | `TranscriptKnowledgeDocument`, vorhandene Knowledge-Pipelines/Consolidation; vorhandene Extrakte sind abgeleitete Kandidaten. C27 liest deren Statements mit JSON-Pointern; kein zweiter Extraktionsprozess |
| Provenienz | `ContentLocator`, `Contract`, kanonische Fingerprints/SHA256 aus C23; native Source-/Dokument-/Media-IDs bleiben zusätzlich erhalten |
| Storage | Erweiterung von `src/tools_materials/storage.py`, weiterhin `safe_path`, `checked_path`, `output_path` und Kernel-Mountprüfung. Kein unabhängiger PathResolver |
| LLM | Vorhandener `OpenAIHTTPProvider`, HTTPX-Client und `RequestBudget`; kein neues SDK. Legacy-LiteLLM/Marvin laden beim Import teilweise Sessions/Logging und werden für den Offlinepfad nicht initialisiert |
| Bestehende Reports | CS50-Kurs-/Qualitätsberichte und Knowledge-Consolidation sind keine thematische Lernzusammenfassung. Ihre Daten werden nicht umgeschrieben |
| UI | Bestehende Admin-Einstiegsdatei, Authentifizierung, Rollen und Streamlit-Session; optionale lokale Ansicht, kein zweiter Server |
| Persistenz/Export | Isolierte versionierte JSON-Dateien statt DB-Migration. Alte globale Cachehelfer initialisieren Legacy-Settings/Verzeichnisse; C27 nutzt dafür die vorhandene sichere Storagegrenze. Eigene kleine LaTeX-Vorlage, kein TeX-Dienst |

## Lokal starten

Die beiden C27-Branches auschecken; keine C26-Drafts dafür übernehmen. Einmal die
normalen Repo-Dependencies installieren: Backend `uv sync --locked`, UI
`uv sync --locked`. Keine Worker-, NLP-, Vision- oder GPU-Extras nötig.

Ein vorhandenes lokales Transkript explizit registrieren. Die IDs werden vom
Betreiber gesetzt und nicht aus allen historischen Dateinamen erraten:

```bash
cd /path/to/Personal_Assistant-c27
uv run python -m scripts.lecture_summary register \
  --workspace /tmp/c27-loviscach-demo \
  --root /mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/lectures \
  --relative loviscach/mathe_1/transcripts/01.01.1_drei_Arten_Mathematik.json \
  --provider loviscach --course mathe_1 --lecture 01.01.1 \
  --title 'Drei Arten Mathematik' --format transcript_json
```

Das erzeugt ausschließlich einen neuen lokalen Katalog und eine Konfiguration im
angegebenen Workspace. Vorhandene Dateien werden nicht ersetzt; bei einer schon
vorhandenen Demo einen neuen Workspace wählen. Die Originaldatei bleibt an ihrem
Ort. Wenn der Mount fehlt, bricht die Registrierung verständlich ab.

Im UI-Checkout mit dem vorhandenen Streamlit-Einstieg starten:

```bash
cd /path/to/personal-assistant-ui-c27
APP_ENV=local ADMIN_AUTH_MODE=demo ADMIN_DEMO_ROLE=operator \
JOB_BACKEND=disabled LECTURE_SUMMARY_MODE=local \
LECTURE_SUMMARY_CONFIG=/tmp/c27-loviscach-demo/summary.json \
PYTHONPATH=/path/to/Personal_Assistant-c27 \
uv run streamlit run app_admin.py --server.address 127.0.0.1
```

In „Lecture Summarizer“ Kurs und Hauptlektion wählen, optional zwei weitere
Lektionen markieren, Quellen/Fingerprints prüfen, Kompakt/Ausführlich und
Lernschwerpunkt einstellen und „Zusammenfassung erstellen“ klicken. Anschließend
stehen Markdown und vollständiges LaTeX zum Download bereit. Änderungen an
Auswahl, Optionen oder Quellversion entfernen die vorherige Anzeige/Downloads.
Eine unverfügbare oder geänderte Quelle deaktiviert die Generierung.

Die lokale Demo nutzt ausdrücklich die bereits vorhandene Demo-Anmeldung mit
Operatorrolle. `APP_ENV=server`, HTTP-Jobbackend und fehlende Anmeldung können
diesen Modus nicht aktivieren. Die Standardkonfiguration bleibt `disabled`.
Getrennte produktive Container erhalten keine Dateisystemfreigabe oder API.

Ein Katalog kann explizit weitere `Lecture`-Einträge desselben Provider/Kurses
und mehrere `Artifact`-Quellen enthalten. Dafür `catalog.json` lokal bearbeiten;
Schema: `Catalog.model_json_schema()`. Die Registrierung ist bewusst kein
historischer Bulkimport. Unterstützte Eingaben: UTF-8 TXT/Markdown,
`TranscriptDocument`-JSON, `NormalizedDocument`-JSON und
`TranscriptKnowledgeDocument`-JSON. Andere Legacy-JSON-Strukturen brauchen einen
gesonderten geprüften Adapter. VTT/SRT lassen sich vorher über den vorhandenen
Transcriptimport normalisieren; C27 startet dafür keinen Job.

CLI-Export in ein bereits vorhandenes freigegebenes Zielverzeichnis:

```bash
uv run python -m scripts.lecture_summary generate \
  --config /tmp/c27-loviscach-demo/summary.json \
  --provider loviscach --course mathe_1 --lecture 01.01.1 \
  --detail detailed --output /tmp/c27-loviscach-demo
```

Für eine portable rein synthetische Demo ist bereits
`docs/course_sources/cs50/examples/official_transcript.txt` vorhanden. Diese Datei
bezeichnet sich selbst als synthetisch; sie ist kein echtes CS50-Transkript.
Die Vertrags-/UI-Tests verwenden ausschließlich solche ausdrücklich künstlichen
Quellen. Die tatsächliche Loviscach-Demo wird nicht ins Repository kopiert.

## Modell, Budget, Qualität und Cache

Default `mock-extractive-v1`: deterministische, begrenzte wörtliche Ausschnitte
und gekennzeichnete eigene Lernfragen; keine vollständige didaktische LLM-Synthese.
Für eine thematische Modellsynthese in der privaten `summary.json` ein konkretes
`model` setzen und `allow_source_upload: true` ausdrücklich konfigurieren.
`OPENAI_API_KEY` kommt ausschließlich aus der Laufzeitumgebung. Diese Freigabe
erlaubt die Übertragung der ausgewählten Texte an den vorhandenen Anbieter;
weder Registrierung noch Tests setzen sie automatisch. Keine Live-Aufrufe sind
Bestandteil der automatisierten Abnahme.

Ein Modellaufruf pro Generierung, keine stillen Wiederholungen; Prompt
`lecture-summary-de-v1`, JSON-Schema `Draft`. Ein gemeinsamer Prompt erhält alle
ausgewählten Quellen und fordert thematische Zusammenführung, Querverbindungen,
Widersprüche, Notation/Voraussetzungen und quellengebundene Kontrollfragen.
Quelltext/Lernschwerpunkt sind Daten, keine Systemanweisungen.

Grenzen: maximal drei Lektionen, 32 Artefakte je Lektion, 2 MiB je Datei,
160 Quellenblöcke und 26.000 UTF-8-Textbytes insgesamt. Der vorhandene Provider
prüft zusätzlich die gesamte Requestgröße inklusive Schema/Metadaten konservativ
gegen 30.000 Bytes plus Framing und reserviert 2.000 Ausgabetokens. Deshalb kann
eine Auswahl schon unterhalb des reinen Textlimits am Requestlimit scheitern.
Übergrößen werden ausdrücklich abgelehnt; keine stille Kürzung oder automatische
Kursauswahl. Eine spätere hierarchische Strategie ist noch nicht implementiert.

Schema- und Quellenprüfung beweisen keine fachliche Korrektheit. Valide Ergebnisse
bleiben `needs_review`; fehlerhafte Referenzen, falsche Quellenzitate, unvollständige
Lectureabdeckung, große Duplikate, externe Quellen oder unbelegte abgeleitete
Aussagen ergeben `failed` und erhalten keine Exporte. Wesentliche Aussagen tragen
Quellen-IDs; eigene didaktische Erläuterungen und unbelegte Inhalte bleiben sichtbar.
Transkriptmathematik hat keine visuelle Bestätigung. Die vier Formelzustände sind
`verified_from_source`, `uncertain`, `requires_visual_context`, `unsupported`.
„Verified“ erfordert ein wörtliches eindeutiges Originalzitat und ist ausdrücklich
kein mathematischer Beweis. Unsichere/ungestützte Formeln bleiben entsprechend
markiert. Der vorhandene begrenzte Formelsyntaxparser ist nur eine Syntaxprüfung.

Prosa wird für Markdown/TeX escaped. Nur die begrenzte geprüfte Formelgrammatik
darf in den Mathmodus; sonst wird Formeltext escaped ausgegeben. TeX-Commands aus
Titeln/Quellen werden nicht ausgeführt. Vorlage `lecture-print-de-v1.tex` ist
vollständig, deutsch und für LuaLaTeX gedacht. C27 bietet keine PDF-Kompilierung
an. Es installiert keinen TeX-Dienst und startet keine Shell aus Modelltext.

Optional `cache: ["local_workspace", "cache"]` konfigurieren. Der relative
Cacheordner muss bereits existieren und zu einem explizit schreibbaren Root gehören.
JSON-Cache enthält Auswahl, Artefaktversionen, Provenienz, Modell-/Prompt-/Template-
Version, UTC-Zeit, strukturierte Themen, Prüfergebnis und Exportmetadaten.
Schlüssel berücksichtigt IDs, Inhalte/Fingerprints, Rollen, Quellmetadaten,
Optionen und Versionen; physische Rootpfade werden nicht Teil der Inhaltsidentität.
Quellen werden vor jedem Cachehit neu geprüft, Modellantwort und Exporte vor
Publikation validiert. Beschädigter Cache wird nicht still übernommen/überschrieben.
Kein produktiver Datenbank- oder Queuezugriff.

## Tatsächliche lokale Datenverfügbarkeit

Der ausdrücklich genannte Google-Drive-Mount war am 24.10.2026 vorhanden.
Inventur: Dateinamen/Kategorien/Größen; keine Medien- oder PDF-Inhalte eingelesen.
Zwei kleine Loviscach-Transkript-JSONs und ausgewählte Kursmetadaten wurden
begrenzt inspiziert. Zahlen bezeichnen vorhandene Dateien, keine bloßen URL-/Pfad-
Referenzen und keine bereits bewiesenen fachlichen Lektionen.

| Quelle/Kurs | Tatsächliche Dateien/Formate | Vorhandene Metadaten | Nutzbarkeit | Fehlende Voraussetzungen |
|---|---|---|---|---|
| Loviscach `mathe_1` | 607 JSON unter `transcripts`, 538 VTT, 28 PDF unter `documents`, 578 JSON unter `knowledge`; zusätzlich Audio/Video/Frames | 7 JSON und HTML/MD unter `metadata`; `mathe_1_course.json` enthält leere Ressourcenliste | Konkretes Transkript `01.01.1_drei_Arten_Mathematik.json` mit 102 Segmenten/5.112 Textzeichen erfolgreich lokal mit Mock verarbeitet | Vollständige Lecture-/Quellenzuordnung nicht aus leerem Kurs-JSON ableiten; Formeln/Visuals ungeprüft |
| Loviscach `mathe_2` | 484 Transcript-JSON, 447 VTT, 37 Audio-/Videodateien | 7 JSON und HTML/MD unter `metadata` | Ausgewählte Transkripte nach Registrierung möglich | Keine pauschale Schema-/Quellen-/Formelprüfung aller Dateien |
| Loviscach `mathe_vorkurs` | 89 Transcript-JSON, 605 Knowledge-JSON sowie abgeleitete Bilder/Videos | `course_info.json`, `course_manifest.json`, Tasks; 181 Ressourcen im Kurs-JSON; erste Ressource hat absolute Pfade und keine Lecture-ID | Konkretes Transkript Grundrechenarten: 125 Segmente/6.002 Zeichen vorhanden | Historische Blockzuordnung lückenhaft; Knowledge-Zwischenstände nicht als unabhängige Originale behandeln |
| Loviscach `info_1` | 213 Transcript-JSON, 184 VTT, 213 Knowledge-JSON; zusätzlicher `_transcripts`-Altbestand | Kurs-/Lectures-/Tasks-JSONs und HTML/MD | Mögliche weitere Pilotquelle | Alt-/Neubestand und explizite Zuordnung prüfen |
| Loviscach `info_2_c#`, `info_2_python` | C#: 294 Transcript-JSON, 268 VTT, 9 PDF, 11 Parsed-JSON/MD; Python: 10 HTML, 3 PDF, 14 Parsed-JSON/MD | Mehrere Kurs-/Lectures-/Tasks-Manifeste | Text-/MD-Dateien nach expliziter Registrierung; JSON nur bei passendem Schema | Keine automatische Umdeutung historischer Parserformate |
| Loviscach `klausuren`, `_unklar` | 23 Prüfungs-PDFs; `_unklar/parsed_mathe_1`: 96 JSON/68 MD | Frühere DEV-03D-Inventur ist im Repo vorhanden | Bereits vorhandene Originale/Parserkandidaten, keine bestätigten Lecturebindungen | Keine automatische Klausur- oder Kurszuordnung; keine Lösungen generiert |
| LAKBB `Gicht` und weitere Kurse | Gicht: 11 Audio, 11 Transcript-JSON, ein PDF unter `script`, je ein Parsed-JSON/MD. Cannabinoide, Gürtelrose, Medikationsberatung, Reizdarm haben ebenfalls echte Transkripte/Skripte | Kursmanifeste und Tasks, teils absolute Pfade | Technisch als lokal registrierter Text nutzbar | Private/fachliche Inhalte bleiben lokal; fachlich ungeprüft, keine Live-LLM-Freigabe |
| Loviscach `test_2026-*` | Je nach Ordner HTML, 2 JSON und MD | Katalog-/Lectures-Metadaten | Discoverybelege | Daraus folgt keine Existenz heruntergeladener Vorlesungsinhalte |

Kategorien sind wörtlich beobachtet: beispielsweise `script` und `scripts`,
`documents`, `parsed`, `transcripts`, `subtitles`, `knowledge`, `audio`, `frames`,
`text`, `_transcripts`. Sie werden nicht automatisch vereinheitlicht. Keine
eigenständig bestätigte historische Summary wurde als Summarizerergebnis übernommen.
Dateizahlen unter Knowledge können Zwischenstände und abgeleitete Artefakte enthalten.

Reproduzierbare Inventur, standardmäßig begrenzt auf 4.000 Einträge/Tiefe fünf:

```bash
uv run python -m scripts.lecture_summary inventory --root /explicit/lectures/root
```

Ergebnis enthält Provider-/Kurskandidaten, tatsächliche Kategorien/Formate/Dateien,
Metadatenschlüssel, explizite Lecture-IDs aus Metadaten und getrennte historische
Ressourcenverweise mit `present`/`not_observed`/`unverified`. Bei Begrenzung wird
`truncated` gesetzt; dann bedeutet „nicht gesehen“ nicht „fehlt“. Die gezeigte
Ordnerhierarchie allein bestätigt noch keine fachliche Kursidentität. Symlinks,
verschachtelte Mounts und Lesefehler werden berichtet, keine Dateien verschoben.
Bei fehlendem Mount liefert das Skript `root_available: false` und erfindet keinen Bestand.

## Unified Storage und spätere Harmonisierung – keine Migration

1. **Erhalten:** Provider/Kurs und bestehende sprechende Kategorien/Dateinamen.
   Zusätzliche Lectureverzeichnisse sind für den Legacybestand nicht notwendig;
   mehrere Lektionen können dasselbe Skript teilen. Neue Derived-Bereiche können
   später standardisiert werden, ohne Originals umzustrukturieren.
2. **Identität:** Provider-ID, Course-ID, Lecture-ID und registrierte Artifact-ID.
   Version ist der tatsächliche SHA256 der Datei, nicht ein Hostpfad. Native
   C23-/Material-/Media-IDs werden zusätzlich erhalten. Beim späteren Relokalisieren
   bestehende Artifact-ID und Inhalt beibehalten und nur den Locator ändern.
3. **Logischer Ort:** `(storage_id, relative_path)`; beispielsweise
   `legacy_google_drive` plus der tatsächliche provider-/kursbasierte Relativpfad.
   Keine absoluten Pfade in Summary-Fachidentitäten. Rootkonfiguration ist lokale
   Infrastrukturkonfiguration und darf absolute Pfade enthalten.
4. **Physischer Ort:** `storage_roots` in der privaten C27-Konfiguration, analog
   den vorhandenen expliziten Root-/Dateikatalogen. Zum Beispiel:

   ```json
   {
     "legacy_google_drive": {"path": "/explicit/local/mount/lectures", "readonly": true},
     "local_workspace": {"path": "/explicit/private/c27", "readonly": false}
   }
   ```

   Gleiche logische IDs können auf anderen Rechnern andere Roots erhalten.
   Server-/Dockerroots werden nur vorgeschlagen, nicht eingerichtet. Bestehende
   Produktionsdienste benötigen keine neue Environmentvariable.
5. **Rückwärtskompatibilität:** Legacy `LectureCourse.root`, Config-Folderwerte,
   `organize_resource_file`, `assemble_course`, Download-/Transkript-/Extraktdateien
   erzeugen oder speichern heute hostabhängige Pfade. Historische JSONs weiter
   unverändert lesen; ein späterer Adapter übersetzt ausschließlich unter einer
   freigegebenen bekannten Legacywurzel liegende Pfade in einen Registrylocator.
   Unbekannte absolute Pfade ablehnen, nicht beliebig öffnen. C27 selbst öffnet
   keinen historischen absoluten Pfad aus einer Quelle.
6. **Registrierung:** Kleine explizite Manifeste mit bestätigten Lecturebindungen,
   Dateigröße, Typ, Original-/Derived-Rolle, Parent-IDs, SHA256 und Prüfdatum erzeugen.
   Zweifelhafte Gruppen ungeklärt lassen. Keine automatische Normalisierung aller
   vorhandenen JSONs. Exakte Kopien anhand SHA256 **und** Größe zuordnen, Identität
   und Rechte dabei getrennt prüfen; Hashgleichheit allein erzeugt keine ACL.
7. **Migration später:** Dry-Run ausschließlich Manifest/Deltas; explizite Freigabe;
   neue Kopie exklusiv anlegen; Hash vor/nach Kopie prüfen; Registry auf neue
   Location umstellen; Leseprobe und Nutzerabnahme. Original behalten. Rollback
   stellt den vorherigen Registry-Snapshot wieder her. Löschen historischer
   Originale wäre ein gesonderter Auftrag.
8. **Sicherheit:** Nur registrierte Roots, kanonische relative Namen, kein Traversal,
   keine Symlinks, descriptorbasierte Öffnung mit `O_NOFOLLOW`, Dateityp-/Größen- und
   Vorher-/Nachherprüfung; relevante Kernel-Mountgrenzen auch bei Bindmounts prüfen.
   Fehlende Roots melden. Lesen erzeugt keine Verzeichnisse. Schreiben ist separat
   explizit und ruft weiterhin den vollständigen `output_path`-Vertrag auf.
   `mounts(subtree=...)` betrifft nur registriertes Lesen; globale C16-/C26-
   Schreibprüfung bleibt unverändert streng. Ein Host mit Rechten zur Veränderung
   des Mount-Namespace bleibt Teil der vertrauenswürdigen Infrastruktur.
9. **Hetzner gesondert freigeben:** Konkrete Root-/Volume-/Mountidentitäten,
   UID/Rechte, freigegebene Manifestkopien, Betriebs-/Speicherbudgets,
   authentifizierte serverseitige Lecture-/Source-ACLs, Job-/Cancel-/Auditvertrag,
   Queue-/Workerintegration und Deployment-/Triggerfreigabe. Keine direkte
   Container-Dateifreigabe oder neuer öffentlicher Endpunkt ist Teil dieses MVP.
10. **Späteres Enrichment:** Eigene Contentart `external` erst nach versioniertem
    Freigabe-/Lizenz-/Provenienzvertrag aktivieren; aktuell lehnt das Quality Gate
    externe Inhalte ab. Sinnvoll sind danach visuelle Formelprüfung, geprüfte
    Original-/Derived-Verknüpfung, hierarchische Zusammenfassungen und ein
    optionaler isolierter PDF-Export. Aktuell keine externe Beschaffung.

## Nachweise und Grenzen

Tests und Laufbelege werden in `docs/c27_validation.md` dokumentiert. Die
didaktische und mathematische Richtigkeit einer echten Modellsynthese bleibt
ohne fachlichen Review ungeprüft. Ein erfolgreicher Mock-/Schema-/Exporttest
ersetzt diese Prüfung nicht. Kein produktiver Rollout und kein Merge gehören zur Lieferung.
