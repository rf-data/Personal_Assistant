# Manuelle CS50P-ZIPs – Inventur und separater Importentscheid

23.10.2026, Basis `d180a8f6e65f900a4d0d169475d78a4cb42b0d8c`.
Der Betreiber hat das lokale Google-Drive-Mountverzeichnis ausdrücklich zum Lesen
freigegeben. Es existiert, ist lesbar und enthält genau die zehn ZIP-Dateien
`week_0_src.zip` bis `week_9_src.zip`; keine fehlende Woche ergänzt. Keine Archive
verschoben, verändert, gelöscht, heruntergeladen oder vollständig kopiert.

## Inventur aller zehn Archive

Alle SHA-256, zentralen Einträge/Pfade, Typen, Größen, Kompressionsverhältnisse,
CRC-/Größenduplikatkandidaten und Grenzen stehen in
[manual_zip_inventory.v1.json](manual_zip_inventory.v1.json).
Die wiederholte Inventur bestätigt unveränderte Rawhashes. Keine Mitgliedsdatei
wurde geöffnet, dekomprimiert, entpackt oder ausgeführt.

| Datei | Rawbytes | Einträge inkl. Verzeichnisse | Deklarierte entpackte Bytes | Dateitypen | Metadatenentscheid |
| --- | ---: | ---: | ---: | --- | --- |
| week_0_src.zip | 6459 | 25 | 3082 | 24 Python | geprüft |
| week_1_src.zip | 6719 | 24 | 4945 | 23 Python | geprüft |
| week_2_src.zip | 6970 | 27 | 4028 | 26 Python | geprüft |
| week_3_src.zip | 3036 | 11 | 1916 | 10 Python | geprüft |
| week_4_src.zip | 5947 | 23 | 3205 | 22 Python | geprüft |
| week_5_src.zip | 6531 | 23 | 4726 | 21 Python | geprüft, 5 mögliche Inhaltsduplikatpaare |
| week_6_src.zip | 11963 | 28 | 9181 | 21 Python, 1 TXT, 3 CSV, 2 GIF | **blocked: unknown_type (GIF)** |
| week_7_src.zip | 7064 | 24 | 4222 | 23 Python | geprüft |
| week_8_src.zip | 11734 | 33 | 12791 | 32 Python | geprüft |
| week_9_src.zip | 14954 | 51 | 10821 | 50 Python | geprüft |

Alle Kurszuordnungen sind durch die Betreiberangabe `cs50_python` erklärt.
Dateiname und jeweils einzige Archivwurzel `srcN` stimmen für N=0–9 überein.
Das bestätigt die lokale Beschriftung; es beweist weder Download-URL, Kursjahr,
Unverändertheit gegenüber dem Anbieter noch eine SourceApproval. Diese Bindungen
bleiben offen. Ein bereits versionierter Link auf `src0.zip` ersetzt keinen
Rawhash-gebundenen Beschaffungsbeleg. Keine URLs aus den übrigen Dateinamen erzeugt.

Keine absoluten/Traversal-/Symlink-/kollidierenden Pfade, verschachtelten Archive,
Verschlüsselungsflags oder überschrittenen Größen-/Ratiogrenzen festgestellt.
Das sind Metadatenbelege: CRC, tatsächliche Entpackgrößen, Textkodierung und
Python-Syntax wurden an diesen zehn Originalen nicht inhaltlich verifiziert.
Die Ratio liegt zwischen rund 1,23 und 1,97. Keine identischen Gesamtarchive.
Woche 5 enthält fünf gleiche CRC-/Größenpaare; diese sind **mögliche**, keine
hashverifizierten Inhaltsduplikate. Pfadidentitäten bleiben getrennt. Woche 6
bedarf Typreview; die GIFs sind kein Nachweis eines Angriffs und werden nicht
zum Anlass einer neuen Bildpipeline oder stillen Allowlist-Erweiterung genommen.

Die Inventur-Allowlist kennt `.py`, `.txt`, `.md`, `.csv`, `.json`, `.yaml`,
`.yml`, `.toml`. Sie erteilt keine Importfreigabe für diese Typen: der bestehende
Codeimport übernimmt weiterhin nur ausdrücklich ausgewählte Pythonquellen.

## Bestehenden Importer geprüft

Weiterhin `src/tools_materials/code_import.py` und `code_zip.py` aus #144,
CLI `scripts.cs50_batch code preview/import/report`. Kein zweiter Importer.

- Maximal 1 MiB Rawarchiv, 64 Einträge, 1 MiB je Mitglied, 8 MiB deklarierte
  Gesamtexpansion, Ratio 100, ausschließlich Stored/Deflated; keine ZIP64-/
  Mehrdiskarchive, Verzeichnis-/Unicode-/Casefoldkollisionen oder Symlinks.
- Nur eine explizite Week-0-CS50P-Auswahl, höchstens acht Materialien insgesamt,
  höchstens sieben explizit zugeordnete Pythonmitglieder je Archiv. Die übrigen
  Wochen sind inventarisierbar, vom bestehenden Importer noch nicht unterstützt.
- Archive und jedes ausgewählte Mitglied brauchen ihre eigene exakte
  SourceApproval mit Kurs/URL/Source-/Material-ID, `process=true` und Rawhash.
  ZIP-Mitglieder bekommen ihre IDs aus vorhandenen lokalen Codeindexlinks;
  Dateinamen allein erzeugen keine Quellenidentitäten.
- Rawbytes, Normalisierung, AST-Struktursicht, bestehende Qualitäts-/Handoff- und
  Importreceipts binden Hashes, Provenienz, Batch, Grants und Implementierungsstand.
  Wiederholung mit denselben Eingaben wird verifiziert wiederverwendet; geänderte
  Bytes/Grants/Implementierung blockieren, ohne alte Ausgaben zu überschreiben.
- Der bestehende Inspector liest beim tatsächlichen Import begrenzt in Memory;
  kein `extractall`, keine Codeausführung. Nicht ausgewählte/ungeeignete Einträge
  werden im Legacy-Receipt ausgeschlossen. Die strengere Inventur blockiert
  unbekannte Typen und verschachtelte Archive schon zur Betreiberprüfung.

Kompatible Korrektur: Der Central-Directory-Zähler wird vor `ZipFile`-Objektanlage
gegen die tatsächlichen Records geprüft; eine manipulierte EOCD-Zahl kann die
64-Eintragsgrenze nicht mehr erst nach Objektanlage auffallen lassen.
Verschlüsselungs-/Patchflags werden abgewiesen. Gemeinsame Prüfungen dienen dem
bestehenden Inspector und der neuen reinen Metadatenfunktion. Kooperative
5-Sekundenprüfung im Inspector; der Inventur-CLI kapselt jeden Lese-/Metadatenlauf
zusätzlich in einem eigenen Prozess mit harter 5-Sekunden-Walltime und räumt nur
diesen eigenen Kindprozess auf. Keine Änderung der Bytes-/Datei-/PDFgrenzen.

Vertragsmodelle und IDs bleiben erhalten. Der bestehende Implementierungshash
ändert sich durch die Sicherheitskorrektur: ältere Importreceipts können deshalb
nicht ungeprüft als aktueller Import wiederverwendet werden. Alte Ablagen erhalten;
gegebenenfalls separat genehmigte Prüfung in neuem Ziel, keine automatische
Migration oder Überschreibung.

## Separater Bericht zum Einzelimporttest

**Realer Import nicht ausgeführt, `operator_action_required`.** Kandidat ist
`week_0_src.zip`: klein, 25 Einträge, nur 24 Pythondateien und Metadaten unauffällig.
Woche 3 ist zwar kleiner, liegt aber außerhalb des bestehenden Importerscopes.
Alle 24 Namen aus Woche 0 passen zu bereits gespeicherten Codeindexreferenzen;
ihre vorhandenen Source-/Material-IDs stehen im finalen Week-0-Plan. Das bestätigt
Referenzen, keine inhaltliche Gleichheit oder Importgenehmigung.

Es fehlen:

1. Bestätigte, aktuelle SourceApprovals für das konkrete ZIP und mindestens ein
   ausgewähltes Mitglied, inklusive Rawhashes und Belegreferenzen. Die einzige
   eingecheckte SourceApproval-Beispieldatei hat `sources: []`; kein bestätigter
   Grant für diese Archive gefunden. Private Runtimekataloge wurden nicht
   bereitgestellt oder untersucht. Die allgemeine Auftragserlaubnis wurde nicht
   in erfundene SourceApproval-Datensätze umgewandelt.
2. Belegte Zuordnung der tatsächlich beschafften ZIPbytes zur offiziellen
   Quell-URL und konkrete Mitglieds-/Indexbindung samt Mitgliedshash. Diese
   Zuordnung darf der Betreiber nach begrenzter Inhaltsprüfung bestätigen.
3. Mindestens **5 GiB freie Reserve zusätzlich zum benötigten Outputbudget**;
   lokal sind nur rund 4 GB frei. Die bestehende Kapazitätsprüfung wird weder
   umgangen noch reduziert. Kein neuer Bereinigungsauftrag daraus abgeleitet.

Nach Erfüllung: genau dieses eine Archiv, ein oder wenige explizite Mitglieder,
separates privates temporäres Ziel außerhalb aller Quellen/Pilotroots, bestehender
`code import` mit unveränderten Limits; anschließend identischer Repeat und
Receipt-/Hash-/Provenienzvergleich. Die übrigen neun Archive bleiben Inventur-only.
Keine Vorschau, die nur fehlende Grants meldet, als erfolgreichen Import ausgeben.

Synthetische Tests des **bestehenden** Importpfads prüfen bereits Rawerhalt,
Code-nicht-Ausführung, Hash-/Grantprüfung, Idempotenz, Duplikate, fehlerhafte
Archive und Grenzen. Sie ersetzen diesen noch offenen Originalimport nicht.

Reproduktion der reinen Inventur (explizite, zuvor bestätigte Originalpfade):

```sh
PYTHONDONTWRITEBYTECODE=1 "$TEST_PYTHON" -B -m scripts.cs50_zip_inventory \
  "$AUTHORIZED_ZIP_ROOT"/week_[0-9]_src.zip > "$OWN_REPORT"
```

Exit 3 ist bei dem hier unverändert gesperrten Woche-6-Archiv erwartbar; das JSON
enthält trotzdem alle zehn Zeilen. Keine Netzwerkfunktion, kein Importflag.
