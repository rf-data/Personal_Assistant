# DEV-03D – Klausurinventar und konkrete Inhaltsfreigabe

20.10.2026, integrierter Backend-master `5171826` (#126–#130 gemergt).
**Status: `awaiting_operator_authorization`.** Die frühere Umgebungsblockade ist
durch die ausdrückliche Pfadkorrektur des Betreibers aufgehoben. Ausschließlich
Metadateninventur, kein realer Parsing-/Formel-/Retrievallauf und keine fachliche
Abnahme. UI-PR #17 war beim letzten Livecheck noch offen.

## Identifizierte Dateien

Der freigegebene Eingangsroot ist hier ausschließlich als Alias
`loviscach_exam_input` referenziert. Kein privater absoluter Originalpfad wird
versioniert. Exakt vier reguläre PDFs auf oberster Ebene wurden geöffnet;
Unterverzeichnisse und andere Bestände wurden nicht durchsucht. Keine Symlinks,
Downloads, Kopien der Originale, Inhaltsausgaben oder externen Dienste.

| Datei | Größe in Bytes | PDFseiten | SHA256 |
| --- | ---: | ---: | --- |
| `Mathe_1_2020-01-31.pdf` | 78598 | 2 | `175d48ceaceca13b85757caa1c0f6ff1ed562360cf23d7420ec424cc88fe9cc1` |
| `Mathe_1_2022-01-28.pdf` | 77097 | 2 | `72731b87eedcb9ca43e81b8942dec6c241b65d4453f4a0142de037720b6bb36c` |
| `Mathe_1_2023-03-21.pdf` | 76785 | 2 | `c4c968add3e471c68347fcace4b2e433fcf184e06543f378cea90b6efccea2e1` |
| `Mathe_1_2024-01-31.pdf` | 84700 | 2 | `ee223992066e0f1183237d3fed12e14a2f408938c675a095074879019bfaf795` |

Summe: **4 Dateien, 317180 Bytes, 8 PDFseiten**. Vier unterschiedliche Hashes,
keine bytegleichen Duplikate. Alle besitzen die PDFsignatur, lassen sich mit dem
vorhandenen PyMuPDF **1.28.2** ohne Passwort öffnen und melden `is_repaired=false`.
Die Prüfung liest Container-/Seitenzahlmetadaten; keine Seite wurde gerendert,
kein Text, Bild, Tabelleninhalt oder Formelkontext extrahiert. Ein lesbarer
PDFcontainer beweist nicht, dass jede Seitenressource fehlerfrei ist.

SHA256 wurde je Datei wiederholt und blieb identisch; Dateigröße, Inode und
Änderungszeit blieben während des ersten Lesevorgangs gleich. Verwendet wurden
read-only Deskriptoren mit `O_NOFOLLOW` und einer 64-MiB-Lesegrenze. Kein eigener
Schreibaufruf auf Originale. Ohne frühere Referenzhashes lässt sich ausschließlich
die Unverändertheit im Prüfzeitraum bestätigen, keine historische Authentizität.
Filesystem-Lesezugriffe können vom Host verwaltete Zugriffszeiten beeinflussen.

## Bestehende Verträge und vorgeschlagene Identitäten

[Metadatenmanifest](corpus_inventory.v1.json), gebundener kanonischer Bodydigest:
`a37319b9b0d18fb246f6071638a35ae30b39f39f01187a3579cf5a501862500e`.
[Dateimanifest](manifest.json) bindet die exakten JSON-/Markdownbytes.

Die folgenden IDs sind **vorgeschlagen und nicht registriert**. Sie verwenden
unverändert C23s `SourceRegistration.resolved_id`-Algorithmus:
`deterministic_id("content_source_v1", "loviscach_exams", file_name)`.
Namespace und externe Identität sind ausdrücklich zu bestätigen; der Rawhash
bleibt getrennt von der Sourceidentität. Keine SourceVersion/ParsedVersion,
Ownership, ACL, Kursbindung oder Importfreigabe wird damit erzeugt.

| Datei | Vorgeschlagene Source-ID |
| --- | --- |
| `Mathe_1_2020-01-31.pdf` | `content_source_v1:26336809d428419dd26c23922e4db68c41b0429c3df7529aedd1daaf9ccaa232` |
| `Mathe_1_2022-01-28.pdf` | `content_source_v1:71751597081e0bebe09435d255e35fc393a098fd925e6fb28728fea15aaad791` |
| `Mathe_1_2023-03-21.pdf` | `content_source_v1:81f805e76c45f371045660b29640e6662199083cb50f1bbce9c4ca9753be182a` |
| `Mathe_1_2024-01-31.pdf` | `content_source_v1:545cfa1a2f5658502fb03eb68f0f899083723e916eaba6470d4125aff0a6fd19` |

**Konkrete Kompatibilitätsgrenze:** C23s `SourceRegistration.course_id` und
`CorpusEntry.course_id` benutzen weiterhin die ausschließlich CS50-Kurse
auflistende `CourseId`-Literaldefinition. Eine Loviscach-Klausur darf deshalb nicht
als CS50-Material registriert werden. Dieses Inventar ist ein versionierter
Metadatenbeleg mit bestehenden `RawArtifact`-Feldern, kein ausführbares
`CorpusManifest` und kein zweiter Evaluator. Eine gültige Nicht-CS50-Kursbindung
muss vor dem bestehenden gebundenen Parsing-/C23-/B1-/Indexworkflow gezielt
ermöglicht werden. Keine Runtime-/Schemaerweiterung oder Umgehung in diesem
Metadatenauftrag. Die C10/C11/C13/C23/C24-Verträge werden weiterverwendet, sobald
deren erforderliche Quellenbindungen tatsächlich darstellbar und freigegeben sind.

## Gemeinsame Betreiberfreigabe – noch nicht erteilt

Die folgende Vorlage ist **keine** Freigabe. Eine tatsächliche Entscheidung muss
die obigen vier Datei-/Source-ID-/SHA256-Paare oder den obigen Inventardigest
ausdrücklich binden. Alle nachfolgenden Felder sind derzeit offen:

- Verantwortlicher Entscheider, Entscheidungsdatum und Freigabebeleg: **offen**.
- Bestätigung des Namespace-/Source-ID-Vorschlags und der vier Rawhashes: **offen**.
- Zweck und erlaubter Evaluationsumfang: **offen**.
- Exakter neuer privater Ausgaberoot außerhalb der Repositories: **offen**.
- Zugriffskreis, private Datei-/Verzeichnisrechte: **offen**.
- Aufbewahrungsdauer, Löschregel, Gültigkeit und Widerruf: **offen**.
- Benannter menschlicher Reviewer und gegebenenfalls unabhängiger Zweitreviewer:
  **offen**; separate Backend-Principal-/Source-/Reviewgrants bei B1-Verwendung.
- Nicht-CS50-Kursidentität und gezielte technische Vertragsanpassung: **offen**.

Erlaubte Schritte sind einzeln zu bestätigen:

| Schritt | Entscheidung | Ausgabeort / Reviewer |
| --- | --- | --- |
| Lokales PDF-v2-Parsing und Textextraktion | nicht erteilt | offen |
| Lokale Formelkandidaten-/Syntaxprüfung mit vorhandenen Verfahren | nicht erteilt | offen |
| Bild-/Tabelleninventur, Struktur-/Locatorprüfung, C10/C13 | nicht erteilt | offen |
| Private Vergleichs-/Reviewartefakte und C11 mit unabhängigen Referenzen | nicht erteilt | offen |
| Optionaler isolierter ContentStore-/EvaluationStore-Testimport | nicht erteilt | separate neue Roots und Grants offen |
| Optionale temporäre FTS5-Indexierung und reale lokale Retrievalqueries | nicht erteilt | neuer isolierter Indexroot und Queryreview offen |

Kein produktiver Import, keine Original-/Extraktveröffentlichung, keine externen
LLM-/Cloud-/Embeddingdienste und keine automatische Goldbestätigung. Ein lokal
gestarteter Agent ist für sich keine Erlaubnis, extrahierte Originalinhalte an
ein externes Modell zu senden. Keine privaten Roots automatisch anlegen oder
geänderte Dateiidentitäten stillschweigend unter eine alte Freigabe übernehmen.

## Erster Lauf und menschliche Übergabe nach Freigabe

Zunächst nur die erste ausdrücklich freigegebene Klausur, bevorzugt die erste
Tabellenzeile, mit bestehenden PDF-v2-Workerlimits verarbeiten. Konfiguration,
Implementierungsrevision, Raw-/Payloadhashes, Dauer, tatsächlichen Speicherbedarf,
Seiten-/Block-/Bildreferenzen und Warnungen erfassen. Hashes erneut prüfen und
Schreib-/Ressourcengrenzen kontrollieren, bevor die restlichen drei folgen.
Originale unverändert lassen; keine bestehenden Stores oder Indexgenerationen
berühren. Keine automatische OCR oder neue Rekonstruktionspipeline.

PDF-v2s mathematische Textklassifikation ist keine bestätigte LaTeXrekonstruktion.
Höchstens 20 Formel-, zehn Struktur- und zehn Bild-/Tabellenfälle erst anhand
tatsächlicher Ausgaben auswählen. Keine Kandidaten oder Fragen aus ungelesenen
Inhalten erfinden. Original-SHA, Seite/BBox/Blockbindung und konkrete Hypothese
beilegen; Text-/Formelausschnitte ausschließlich privat. Technische Fehler,
Heuristikverdacht und fehlende Entscheidungsreferenz getrennt halten.

Menschen liefern unabhängige Referenzen und Reviewbelege. Bestehende
`Region`/`TaskSpec`/`Annotation`- und C23-Goldverträge nutzen; keine künstlichen
SourceVersions oder Reviewer. C11 erst mit passenden unabhängigen Formelreferenzen
fachlich auswerten; `reference_status=absent` ist kein Ersatz für fehlendes Gold.
Retrievalfragen vor Suchläufen am freigegebenen Original festlegen. Qualitätsraten
bleiben ohne bestätigte Referenzen null, Nenner 0; kein 0-Prozent-Qualitätsurteil.

Aktuell: **0 real geparste Dokumente, 0 erzeugte reale Reviewkandidaten,
0 unabhängige Goldreferenzen**. Text-/Formel-/Tabellen-/Bildzahlen und fachliche
Qualität sind `not_checked`, keine Fehlerfreiheit oder Realabnahme behauptet.

## Validierung und Lifecycle

Keine Runtimeänderung und keine erneute synthetische Evaluationsrunde.
Erfolgreich geprüft: Inventarhash, bestehende `RawArtifact`-Modelle,
deterministische vorgeschlagene IDs, relative Namen, Seiten-/Größensummen,
Dateihashes, lokale Dokumentationsverweise und unveränderte Originalhashes.
Keine Pytest-/Ruff-Ergebnisse aus früheren Aufträgen als neue Läufe ausgeben.
Pytest und Ruff wurden in diesem reinen JSON-/Markdownauftrag nicht ausgeführt;
JSON-/Modell-/Hashprüfungen und `git diff --check` bilden die aktuelle Validierung.

Dauerhafte Metadaten und diese Freigabevorlage gehen über einen eigenen PR gegen
master. Bis zur bestätigten Integration bleibt der eigene Branch/Worktree
erhalten. Keine automatischen Merges, keine Bereinigung früherer DEV-/MAINT-
Bestände oder anderer Worktrees. Ein Metadatenmerge erteilt keine Inhaltsfreigabe.
