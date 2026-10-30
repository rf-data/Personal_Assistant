# C27-B: Legacy Lecture Catalog und Compatibility

Stand: 24.10.2026. Fortsetzung von [C27](c27_lecture_summary.md), Backend-Draft
[#158](https://github.com/rf-data/Personal_Assistant/pull/158), UI-Draft
[#21](https://github.com/rf-data/personal-assistant-ui/pull/21). Ausgangspunkt
`4fedf844`; separat geprüfter aktueller master `29114d2e` enthält bereits #156/#149.
Keine Migration, Downloads, Live-LLM-Aufrufe, Datenbankzugriffe oder Deployments.
Die Dokumente bleiben gemäß Mergeverbot im Draft, bis sie separat reviewed und
integriert werden. Eigener Worktree `Personal_Assistant-c27b`, Branch
`feat/c27b-legacy-catalog`; bestehende Arbeitsstände bleiben erhalten.

## Entscheidung

**GO für begrenzte lokale Legacy-Integration:** bekannte JSON-Schemata,
explizite oder vollständig native Identitäten, geprüfte SHA256 und registrierte
Read-only-Roots. Der reproduzierbare Kandidat enthält vier bereits ausdrücklich
registrierte Loviscach-Transkripte und einen zugeordneten Knowledge-Extrakt.
Er wird erst durch die bewusste Wahl seiner Konfiguration in der lokalen UI benutzt.

**NO-GO für eine automatische Übernahme des gesamten historischen Bestands:**
Dateibestand und Metadatenreferenz sind unterschiedliche Nachweise. Fehlende
native IDs, feste Legacy-Blockwerte, weitere Parser-Schemata und ungeprüfte
Parent-Beziehungen verhindern eine pauschale Freigabe. Keine produktive Registrierung.

**Fachliche Summarizer-Abnahme bleibt separat offen.** Mock liefert Ausschnitte und
Lernfragen, keine geprüfte didaktische Synthese. `needs_review` bleibt auch bei
korrekter Quellenverkettung erhalten. Historische Knowledge-Formeln werden durch
diesen Adapter weder mathematisch geprüft noch zu Originalbelegen aufgewertet.

## Konkreter Legacy-Code-Review

Die folgenden Funktionen wurden gelesen, nicht gegen den historischen Bestand
ausgeführt. Viele von ihnen schreiben, verschieben oder beschaffen Dateien und
sind deshalb kein geeigneter Inventur-Einstiegspunkt.

| Fundstelle / Funktionen | Eingabe → Ausgabe, Pfad und Identität | Abhängigkeiten / C27-Bruch / Empfehlung |
|---|---|---|
| `src/model_lecture/data_resources.py`: `LectureCourse.root`, `LectureResource`, `LectureMedia`, `ResourceTask` | Kurs/Provider + globale `folder_env_vars.data_lectures` → physischer Provider/Kurs-Root; Ressourcen enthalten `local_path`, `lecture_no`, `lecture_blocks`, optional `content_hash`, URL/Media-ID | Modelle für bisherige Planung behalten. `root` berechnet einen Umgebungspfad, keine portable Identität. `local_path` am Import-Rand durch Storage-ID/relativen Locator abbilden. Alte JSON-`resource_type: video` entspricht nicht der heutigen diskriminierten `media`-Union; keine stillschweigende Reparatur |
| `src/tools_lecture/prepare_loviscach.py`: `lecture_block_extraction`, `parse_lecture_title`, `infer_video_block`, `assign_video_blocks_by_order`, `extract_scripts`, `enrich_urls` | Legacy-`RawDocument`/Links → Blöcke, `LectureScript`/`LectureMedia`; Titel liefert Lecture-Nummer/Topic, Reihenfolge und Nummern liefern Blockzuordnung | Wiederverwenden für geplante Provider-Aufbereitung, Zuordnungen als Herkunftsnachweis speichern. `extract_media_id` erkennt hier YouTube-URLs; separate `resolve_video_url` führt HTTP aus und wurde nicht aufgerufen. Keine URL-Auflösung durch Inventur/Adapter |
| `src/run_lecture_preparation.py`: `lecture_preparation`; `src/run_lecture_compilation.py`: `prepare_course`, `process_course_until_complete`, `save_task_list` | `metadata/<provider>_<course>_info.json` → Ressourcen/Kurs/Tasks; `from_info` validiert Scripts/Videos, `from_folder` ruft Assembler; `course.root/metadata/<course>_tasks` | Session/Logging, globale Settings, Dateisystem und Processing sind gekoppelt. Weiterbetrieb unangetastet; spätere Anpassung an portable Referenzen an Ein-/Ausgabegrenzen, nicht durch Aufruf aus C27 |
| `src/tools_lecture/assemble_course.py`: `build_lecture_course_from_folder`, `build_lecture_resource` | rekursiver Dateibestand → `metadata/course_manifest.json`, `metadata/course_info.json`; Provider/Kurs aus Verzeichnisnamen; feste `lecture_blocks=["2"]`, teils keine `lecture_no` | Schreibt in Originalbaum und lädt Dateiliste vollständig. Nicht zur schreibgeschützten Katalogfreigabe verwenden. Fester Block `2` ist kein belastbarer Lecture-Nachweis; generischen Assembler langfristig ablösen/adaptieren |
| `src/tools_lecture/discover_course.py`: `classify_course_file`, `parse_lecture_filename` | Endung → Ressourcentyp; Dateiname → Titel, Qualifier, Sequenz (u. a. dreistellige Audio-Endnummer) | Klassifikation ist eine Heuristik, keine Identitätsquelle. SRT/VTT/JSON fallen in diesem Legacy-Klassifizierer unter OTHER. Für Hinweise behalten, nicht als automatische Lecture-Bindung verwenden |
| `src/utils/path_helper.py`: `RESOURCE_FILE_FOLDERS`, `get_resource_target_folder`, `organize_resource_file`, `move_file`, `ensure_dir`, `build_file_index`, `find_indexed_files` | reale Kategorien u. a. audio/subtitles/transcripts/knowledge/visual_analysis/metadata/documents/images/text/other; Scripts/Exams/Material haben Sonderregeln; Organisieren kann Dateien verschieben; Index sammelt alle Pfade | Kein sicherer registrierter Resolver, teils implizite mkdir und namensbasierte Suche. Kategorien unverändert behalten. Für Inventur durch FD-basierten Stream ersetzen; bestehende Processing-Caller nicht refaktoriert |
| `src/tools_lecture/prepare_cs50.py`: `parse_course_index`, `parse_week_page`, `combine_course_pages`, `discover_fixture_courses`; `cs50_manifest.py`: `load_fixture_manifest` | lokale HTML-Fixtures + validiertes Manifest → `CourseDiscovery`, Ressourcenrollen, Hierarchie, Varianten, deterministische Source-/Resource-IDs und Provenienz | Bestehende Discovery-/Manifestverträge behalten. Kein CS50-Reimport. Discovery-`CourseId` und `MaterialResource` sind momentan auf die CS50-Kursmenge beschränkt; keine ungefragte globale Erweiterung für Loviscach |
| `src/model_transcribe/data_transcribe.py`; `src/tools_transcribe/process_subtitle.py`: `transcribe_files`, `parse_subtitle`, `add_transcript_provenance` | ASR/Subtitle → `TranscriptDocument`, Segmente, optionale `TranscriptProvenance`; Legacy-Ausgabe relativ zu `file.parent.parent/transcripts`; `source`/`source_file` können absolute historische Pfade enthalten | Modelle und unbekannte Zeiten wiederverwenden. Vorhandene Legacy-Transkripte können nur einen alten Audiopfad und keine Course-/Lecture-ID besitzen. Pfad wird als unbelegter Herkunftsverweis aufbewahrt, nie automatisch geöffnet. Vorhandener offizieller TXT/SRT/VTT-Importer bleibt eigener Processing-Schritt |
| `src/tools_lecture/process_lecture.py`: `build_document_parse_context`, `execute_document_action`, `execute_media_action`, `download_document` | globale Parserkonfiguration + `local_path` → `course_root/parsed`, bzw. Download nach `documents`; AudioContext/Provider → Transkripte | Alte Parserläufe können Docling-/RawDocument-Strukturen erzeugen. Diese sind nicht `NormalizedDocument`. Keine neue Parserausführung, kein Download aus C27-B |
| `src/model_materials/materials.py`; `src/tools_materials/parse_html.py`: `parse_html`, `build_document`; `parse_pdf.py`: `parse_pdf` | `MaterialResource` + Bytes + Parserkonfiguration → `NormalizedDocument`, Original-SHA, deterministische Dokument-/Block-IDs, DOM/Seiten-/Bildreferenzen | Für bereits erzeugte normalisierte JSONs vollständig wiederverwendet. Parser v2 und Content-Projektion aus #149 behalten. Fehlende Raw-Originale bleiben eine Lücke; raw SHA ist keine bewiesene Dateiexistenz. Kein Docling-Konverter gebaut |
| `src/run_knowledge_extraction.py`: `knowledge_extraction`; `src/tools_knowledge/find_knowledge.py`: `build_transcript_chunks`, `attach_chunk_provenance`, `validate_extraction` | Transcript → Knowledge-Chunks/Statements/Formeln; `source_id=transcript_path.name` ohne `.json`; Ausgabe `knowledge/<stem>_know_extract.json`; neuere Ergebnisse übernehmen Course-/Lecture-/Transcript-Provenienz | Modelle, Chunk- und Provenienzverträge behalten. Gleicher Dateistamm allein beweist keine Parent-Version. Bestehender Guard für unbekannte Zeiten bleibt bestehen; C27-B ruft Chunking/Extraktion nicht auf |
| `src/tools_knowledge/consolidation_run.py` und Consolidation-Modelle | `_know_extract.json` → weitere abgeleitete Statements/Formeln, Statistiken und Visual-Prüfarbeit | Keine unabhängige Originalquelle, kein Ersatz für Transcript-Parent. ConsolidatedKnowledgeDocument/LectureKnowledgeDocument werden vom kleinen Adapter ausdrücklich nicht umgedeutet |
| `src/tools_materials/storage.py`: `RegisteredStorage`, `locate`; `src/runtime_paths.py`: `checked_path`, `mounts`, `output_path` | benannte Root-Grants + portable Referenz → begrenzter sicherer Read/ausdrücklich erlaubter Write | Bestehende Implementierung unverändert wiederverwendet. Kein zweiter Resolver, keine Lockerung des Persistent-Root-Vertrags. Adapter übersetzt alte absolute Pfade nur innerhalb der ausdrücklich benannten Root und führt danach dieselben Prüfungen aus |

## Inventur: Dateien vollständig, Metadaten semantisch teilweise offen

Der Google-Drive-Mount war erreichbar. Beobachtete Root:
`/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/lectures`.
Beide vollständigen Auflistungen erfassten **9.348 Einträge, 8.779 reguläre Dateien**,
keine Abbrüche durch Eintragslimit, Symlink, Mountgrenze oder Zugriffsfehler.
**45 Metadaten-JSONs gelesen, fünf wegen >2 MiB nicht gelesen.** Das sind:

- `loviscach/mathe_2/metadata/JLoviscach_Mathe_2_info.json`
- `loviscach/info_1/metadata/JLoviscach_Info_1_info.json`
- `loviscach/info_2_c#/metadata/loviscach_info_2_c#_info.json`
- `loviscach/mathe_1/metadata/loviscach_mathe_1_info.json`
- `loviscach/mathe_1/metadata/loviscach_mathe_1_info_alt.json`

Sie bleiben vorhandene Dateien; ihr Inhalt wurde nicht als fehlend oder geprüft
ausgegeben. `complete=true` bezeichnet die Dateiauflistung; `metadata_complete=false`
und `associations_complete=false` verhindern eine pauschale fachliche Vollständigkeitsbehauptung.
Die Auflistung ist keine atomare Dateisystem-Snapshotaufnahme.

Private Berichte außerhalb beider Repositories:
`c27b-legacy-inventory-final-20261024/inventory.jsonl` und `inventory_summary.json`
unter `/home/OPERATOR/0_Portfolio_Projekte`. Der erste vollständige Lauf bleibt unter
`c27b-legacy-inventory-20261024` erhalten. JSONL unterscheidet echte `file`-Ereignisse,
`metadata`, lediglich deklarierte `resource_reference` und `issue`. Die abschließende
Fassung prüft lokale Referenzen innerhalb registrierter Roots separat; URLs sind kein
Existenznachweis. Jeder Dateieintrag bleibt bis zu einer expliziten Registrierung
`association=unresolved`. Keine vollständigen Quelleninhalte in den Berichten.
Im finalen Stream: 4.806 Metadatenreferenzen, davon 2.861 vorhandene reguläre
Dateiverweise, 93 fehlende Dateien innerhalb der registrierten Root und 1.852 ohne
lokalen Dateiverweis. Das sind Referenzzählungen, keine zusätzlichen eindeutigen
Dateien oder bewiesenen Lecture-Bindungen. Vollständige Berichte zusammen etwa 5,6 MB.

| Beobachteter Bereich (Verzeichnislabel, keine automatische Kursfreigabe) | Dateien / Formate und Kategorien | Nutzbarkeit / offene Voraussetzung |
|---|---|---|
| loviscach / mathe_1 | 2.220; transcripts 607, knowledge 578, subtitles 538, documents 28 PDF, frames 356, audio 103, metadata 9, text 1 | Vier Transkripte und ein Extrakt konkret geprüft. `mathe_1_course.json` hat leere resources; weiterer Videoindex enthält deklarierte Lecture-Nummern/URLs, aber vielfach keinen lokalen Pfad |
| loviscach / mathe_2 | 977; transcripts 484, subtitles 447, audio 37, metadata 9 | Material vorhanden, native Lecture-/Parent-Bindungen nicht freigegeben |
| loviscach / mathe_vorkurs | 3.598; transcripts 89, knowledge 3.506, metadata 3; im knowledge-Bereich auch PNG/MP4 | Kategoriename bedeutet nicht, dass alle Dateien KnowledgeDocument sind; Zwischenartefakte separat prüfen |
| loviscach / info_1 | 892; transcripts 213, _transcripts 243, knowledge 213, subtitles 184, audio 33, metadata 6 | Historische alternative Kategorie `_transcripts` unverändert erfasst; keine Doppelzählungsbereinigung oder Identitätsverschmelzung |
| loviscach / info_2_c# | 626; transcripts 294, subtitles 268, audio 26, documents 9, parsed 22, metadata 7 | Geprüftes `parsed/01_Ueberblick_docling.json`: DoclingDocument 1.10.0, ausdrücklich nicht unterstützt |
| loviscach / info_2_python | 54; documents 13, parsed 28, metadata 12, Kursroot 1; HTML/PDF/JSON/MD | Vorhandene Parserartefakte; NormalizedDocument-Vertrag nicht pauschal nachgewiesen |
| loviscach / _unklar | 168; Kursroot 4 MP4, parsed_mathe_1 164 | Verzeichnislabel und Titel sind keine verlässliche Kurs-/Lecture-Zuordnung |
| loviscach / klausuren | 23 PDF im Verzeichnisroot | Nur Originaldateien nachgewiesen, keine Lecture-Freigabe |
| loviscach / acht test_2026-08-* Bereiche | 39 insgesamt; HTML/JSON/MD | Metadaten-/Parserexperimente, keine automatisch anerkannten Kurse |
| lakbb / Cannabinoide | 33; audio 10, scripts 2, metadata 3, transcripts 10, parsed 8 | Vorhanden; keine C27-Registrierung ohne nachvollziehbare Lecture-Bindung |
| lakbb / Gicht | 28; audio 11, script 1, metadata 3, transcripts 11, parsed 2 | Kategorie `script` bleibt erhalten; feste Assembler-Blöcke nicht als Identität übernehmen |
| lakbb / Gürtelrose | 24; audio 10, scripts 1, metadata 3, transcripts 10 | Vorhanden, IDs/Parent-Versionen offen |
| lakbb / Medikationsberatung | 24; audio 9, scripts 1, metadata 3, transcripts 9, parsed 2 | Vorhanden, IDs/Parent-Versionen offen |
| lakbb / Reizdarm | 28; scripts 1, audio 11, metadata 3, transcripts 11, parsed 2 | Vorhanden, IDs/Parent-Versionen offen |
| lakbb / Pflanzliche_GIT_AM | 17; transcripts 7, audio 8, Kursroot 2 | Teilweise Datei-/Transcript-Zahl abweichend; keine automatische Paarung |
| lakbb / magen_otc; lakbb / parsed | 9 WAV bzw. 2 JSON/MD | Verzeichnislabels sind keine bestätigten Kursmodelle |
| lakbb / ohne Kursunterverzeichnis | 17 PDF | Tatsächlich vorhanden, ohne belegte Kurs-/Lecture-ID |

JSONL enthält alle individuellen Pfade und Formate, auch die acht ausgeschriebenen
Test-Verzeichnisnamen. Aggregierte Lecture-ID-Listen sind auf 128 je Kurs begrenzt
und markieren die Kürzung; einzelne deklarierte Ressourcen bleiben vollständig im
Stream. Insgesamt werden maximal 4.096 Kursaggregate und je 128 Kategorien/Formate
im RAM gehalten; Überläufe werden gezählt. Ein JSON-Read ist auf 2 MiB begrenzt,
Verzeichnistiefe auf 32 (höchstens 64 konfigurierbar); Abweichungen verhindern
`complete=true`. Große Medien/PDFs werden weder gelesen noch gehasht.

## Adapter und Kataloggrenze

`src/lecture_summary/legacy.py` validiert genau TranscriptDocument,
NormalizedDocument und TranscriptKnowledgeDocument. Doppelte JSON-Schlüssel,
mehrdeutige Schemaformen, widersprüchliche native IDs/Versionen, doppelte
Knowledge-IDs, kaputte JSONs und geänderte Fingerprints werden abgewiesen.
Keine automatische Vereinheitlichung von Docling, RawDocument, ConsolidatedKnowledge
oder historischen beliebigen JSONs. Alle übrigen Quellen gehören in den Review.

`LegacyManifest` enthält höchstens 128 ausdrückliche Kandidaten mit benannter
Storage-ID, Locator, erwartetem SHA256, Titel und Identitätsnachweis. Vollständig
vorhandene native IDs können qualifizieren; sonst verlangt der Adapter
`identity_evidence=explicit_registration`. Angaben dieser vertrauenswürdigen
Registrierung müssen vorhandenen nativen Angaben entsprechen. Fehlende IDs werden
nicht aus einem Dateinamen ergänzt. Ein allein vorhandenes `source_id` ist keine
vollständige Provider-/Course-/Lecture-Identität. NormalizedDocument benötigt wegen
des heutigen CS50-Vertrags eine explizite Provider-Bindung.

Absolute Locator werden nur relativ zu der ausdrücklich benannten Root übersetzt.
Alte Pfade außerhalb dieser Root werden abgelehnt, nicht durch Suffixsuche ersetzt.
`TranscriptDocument.source` darf als opaque Herkunftsangabe erhalten bleiben;
die alte Audiodatei außerhalb der Lecture-Root wird dabei nicht geöffnet.
Der JSON-SHA ist eine nachgewiesene Inhaltsversion; er behauptet keinen verifizierten
Audio-Parent. Artefaktidentität verwendet Provider/Kurs/Typ und native ID oder
geprüften Inhaltsfingerprint, keinen Hostpfad. Kopien bleiben über Roots hinweg
identifizierbar; innerhalb derselben Lecture werden gleiche Typ-/SHA-Kopien
dedupliziert und im Review vermerkt. Widersprüchliche native Versionen qualifizieren
beide nicht, statt still eine auszuwählen.

Knowledge verlangt einen ausdrücklich bezeichneten, validierten Transcript-Parent
derselben Provider-/Kurs-/Lecture-Bindung. Segment-IDs müssen existieren;
Zeitintervalle müssen endlich, geordnet und von diesen Segmenten gedeckt sein.
Unbekannte Parent-Zeiten rechtfertigen keine rekonstruierten Knowledge-Zeiten.
Die historische Namenskonvention ist ein Hinweis, kein kryptografischer Parentnachweis.
Die Parent-Zuordnung dieses Kandidaten ist eine explizite Registrierung mit geprüftem
SHA beider JSONs und strukturellen Konsistenzchecks, kein Beweis fachlicher Ableitung.

Der C27-Katalog bleibt Schema 1. Native IDs, Herkunft, Parent-Keys und offene Hinweise
stehen zusätzlich in `catalog_review.json`. C27-Evidence/Markdown/TeX erhalten native
Knowledge-Chunk-/Item-IDs, Parent-Artefakte und Parent-Segmente. Knowledge-Formeln
werden als abgeleiteter, ungeprüfter Text verfügbar; weder historisches `verified`
noch gültiges LaTeX beweist ihre Richtigkeit. Ohne unmittelbare Transcript-Lokation
bleibt der Knowledge-Lokator `time_status=unknown`; der JSON-Pointer und die
Parent-Segmentliste bleiben nachvollziehbar. Adapterversion `lecture-sources-v2`
geht in den Cache-Schlüssel und die Exportmetadaten ein; ältere Caches werden nicht
als aktuelle Ergebnisse übernommen. Keine Datenbankmigration.

## Reproduzierbare Verwendung

Alle Ausgabeverzeichnisse müssen neu sein; keine Datei wird überschrieben. Die
folgenden Befehle laufen im Backend-Checkout mit vorhandenen Dependencies. `python`
bezeichnet eine geeignete vorhandene Python-3.12-Umgebung, keinen Installationsauftrag.

```bash
cd /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27b
export PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1
python -B -m scripts.lecture_summary_legacy inventory \
  --root '/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/lectures' \
  --output /absolute/path/new-inventory

# Bestehende explizite C27-Auswahl wiederverwenden, keinen Kurs aus Namen erraten.
python -B -m scripts.lecture_summary_legacy manifest \
  --config /home/OPERATOR/0_Portfolio_Projekte/c27-local-mvp/summary.json \
  --knowledge-for 01.01.2 \
  --knowledge loviscach/mathe_1/knowledge/01.01.2_weiter_drei_Arten_Mathematik_know_extract.json \
  --output /absolute/path/new-bindings
python -B -m scripts.lecture_summary_legacy catalog \
  --roots /absolute/path/new-bindings/roots.json \
  --manifest /absolute/path/new-bindings/manifest.json \
  --output /absolute/path/new-candidate
```

`manifest` und `catalog` führen keinen Modellaufruf aus. Die Konfiguration muss
unverändert Mock sein; Input-Roots sind read-only. `catalog` erzeugt einen Kandidaten
und Review, aktiviert ihn aber nicht. Bei einzelnen abgewiesenen Einträgen unbedingt
`catalog_review.json` prüfen; existiert kein zulässiger Eintrag, gibt es keinen Katalog
und Exitcode 2. Inventur mit unvollständiger Dateiabdeckung liefert ebenfalls Exitcode 2;
Metadatenlimits stehen separat im Bericht. Unterbrochene Inventur behält eine partielle
JSONL-Datei, ohne erfolgreichen Abschlussbericht. ENOSPC wird nicht abgefangen/retried.

Hier bereits vorbereitet:

- Manifest/Roots: `/home/OPERATOR/0_Portfolio_Projekte/c27b-legacy-bindings-20261024/`
- Kandidat/Review/Mock-Konfiguration: `.../c27b-legacy-candidate-20261024/`
- End-to-End-Exporte/Nachweis: `.../c27b-legacy-e2e-final-20261024/`

Der Kandidat umfasst 01.01.2 (Fließtext, Transcript plus 18 Knowledge-Statements),
01.06.1 (Skalarprodukt), 01.05.1 und 01.05.2 (Vektoren). Vier Transcript-SHA stehen
bereits im [Abnahmeleitfaden](c27_manual_acceptance.md). Der zusätzliche Knowledge-SHA
ist `a9ed117d67f162c220cdeb4533750df5b9e935c37aefe50f657d6dc799d5a273`.
Keine Quellen oder privaten Berichte werden ins Repository kopiert.

UI-Start aus dem bestehenden UI-Checkout:

```bash
cd /home/OPERATOR/0_Portfolio_Projekte/personal-assistant-ui-c27
python -B scripts/lecture_summary_local.py \
  --backend /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27b \
  --config /home/OPERATOR/0_Portfolio_Projekte/c27b-legacy-candidate-20261024/summary.json
```

URL `http://127.0.0.1:8501`, bestehende Demo-Anmeldung mit Operatorrolle; OIDC wird
bei expliziter vorhandener Konfiguration beibehalten. Mock-Banner beachten, Kurs
loviscach/mathe_1 und 01.01.2 wählen, zwei Quellen prüfen, generieren und Markdown/TeX
herunterladen. Stopp mit Ctrl-C. Start mit `--check` wurde gegen diesen Kandidaten
ausgeführt; kein zweiter Server oder produktiver Job gestartet. Eine vollständige
Browserabnahme wurde in C27-B nicht wiederholt. Weitere Bedienung und bekannte
Modellkontextgrenzen stehen im bestehenden [Abnahmeleitfaden](c27_manual_acceptance.md).

## Nachweise und verbleibende Prüfungen

Realer Offline-End-to-End-Test: 01.01.2-Transcript mit seinem explizit gebundenen
TranscriptKnowledgeDocument, 43 Evidenceblöcke (25 Transcript, 18 Knowledge),
Status `needs_review`, Mock-Modell. Summary-ID
`42692970677c3add698bed4e62284045ef074be8e4aa221d274c7ff46c333ad6`.
Finale Exporte: Markdown 28.728 Bytes, vollständiges LaTeX 29.492 Bytes, JSON 77.617
Bytes. Alle fünf registrierten Eingangs-SHA stimmen vor/nach der Generierung mit
dem Manifest überein. Ausgabeordner 0700, Dateien 0600. Kein bezahlter API-Aufruf.
NormalizedDocument separat mit synthetischem bestehendem HTML-Parser getestet;
kein geeigneter realer Loviscach-NormalizedDocument wurde in den gezielten Stichproben
nachgewiesen. Die tatsächlich vorhandene zweite Materialart ist Knowledge.
Zusätzliche reine Request-Vorprüfung des Kandidaten mit der Modell-ID-Zeichenfolge
`gpt-6-luna`: Textfall inklusive Knowledge 21.043 bei Limit 30.000; Formel-/Gruppenfall
unverändert 30.929/47.186 und damit vor HTTP blockiert. Keine Upload-/Live-Freigabe.

Gezielte Testbefehle und abschließende Zahlen stehen in
[c27_validation.md](c27_validation.md#c27-b-legacy-compatibility).
Keine erneute vollständige 398-/157-Test-Regression. Python-/Dependency-Umgebungen
wiederverwendet, keine Installation. Ruff/Pre-commit sind dort nicht verfügbar;
deren Hooklauf wird nicht als bestanden ausgegeben. Syntax/Diff/Dateigrößen,
JSON-/Modellverträge, sichere Pfade und Export-Escapes werden gezielt geprüft.
Live-Modell, mathematische Richtigkeit, TeX-Engine/PDF-Kompilation, Produktion und
Migration bleiben ungeprüft bzw. außerhalb des Auftrags. Kein ENOSPC aufgetreten.

## Auswirkungen und nächste Schritte

Provider-/Kursstruktur und echte Kategorien bleiben erhalten; zusätzliche
Lecture-Unterverzeichnisse sind nicht erforderlich. `RegisteredStorage`, Transcript-,
Knowledge- und normalisierte Dokumentmodelle sowie SourceCollector/Service bleiben
die gemeinsame Basis. Der neue Adapter ist eine kleine Importgrenze für ausdrücklich
bekannte Schemas, keine alternative Processing-Pipeline.

Später gezielt anpassen: Portable Referenzen statt `LectureCourse.root`/absoluter
`local_path` in neuen Metadaten; Parser-/Extraktionsläufe sollen Version und Parent-SHA
bereits bei der Entstehung speichern. Den generischen Ordnerassembler mit festem
Blockwert und verschiebende Pfadhelfer für neue Importpfade ablösen. Weitere native
Parserformate benötigen eine separate, belegte Adapterentscheidung; die CS50-spezifische
Course-ID-Grenze darf nicht über einen falschen Kurseintrag umgangen werden.

Für eine spätere Übernahme: getrennt freizugebender Dry-Run mit Manifest, geprüften
kleinen Artefakt-SHA, ausdrücklich freigegebenen Medien-Hashes, Kopie statt Verschieben,
Versionvergleich und Rollback des Registrierungsmanifests. Keine Umsetzung hier.
Server-Roots/Mounts, Rechte, C16-Worker-/Jobintegration und C26-Bootstrap müssen separat
freigegeben werden. Enrichment bleibt eine eigene zukünftige Inhaltsart mit eigener
Provenienz; lokale Legacy-Daten werden dadurch nicht automatisch extern übertragen.
