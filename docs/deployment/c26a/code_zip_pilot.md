# C26-B6: begrenzter Offlineimport von Python und ZIP

Basis: Backend-master `6786b5d67b31125895d94af7b763a1002aeeea7d` (#141/B4,
#142/B5 integriert). **Implementierung für synthetische Offlineprüfung, kein
Realpilot und keine fachliche Freigabe.** Prüfprotokoll:
[code_zip_validation.md](code_zip_validation.md). Der erfolgreiche B3-Root,
Loviscach-Bestand und bestehende Stores bleiben außerhalb dieses Ablaufs.

## Wiederverwendete Verträge und Identitäten

`make_plan(..., include_code_indexes=True)` ergänzt den bestehenden MaterialPlan
um eine Ebene direkter Pythonlinks aus bereits gebundenen Codeindex-Snapshots.
Ohne Opt-in bleiben bisherige Discovery, IDs, Batch-v1-Bytes und Auswahl unverändert.
Keine rekursive Linkverfolgung und keine Netzwerkprüfung. Source-IDs entstehen
mit dem vorhandenen `ResourceCandidate.resource_id`-Algorithmus aus Kurs, Rolle,
**exakter URL**, Sprache und Parent-ID des Codeindexes. Lecture-IDs stammen aus
dem bestehenden Graphen, niemals aus Dateinamen. Snapshotdateien und deren Hashes
binden die gesamte Auswahl; neue Kandidaten bleiben `referenced`.

Der Adapter verwendet Batch, SourceApproval, CapacityLimits, Code-v1,
NormalizedDocument, ArtifactReceipt sowie den unveränderten Quality-Gate- und
LectureMaterialHandoff-Vertrag. Der alte ZIP-Helfer `src/utils/zipfile_helper.py`
mit `extract`/`extractall` wird wegen fehlender Schutzprüfungen nicht verwendet.
ZIP ist weiterhin kein automatisch unterstütztes C18-Material. Der neue Import
publiziert weder Kataloge noch Workflows, ContentStore- oder Knowledge-Objekte.

Je importierter Pythondatei bleiben Rawbytes einschließlich BOM erhalten.
Code-v1 dekodiert streng `utf-8-sig`: ausschließlich eine führende UTF-8-BOM wird
aus der Textprojektion entfernt; Einrückung, Tabs, CRLF und Unicode bleiben erhalten.
Andere Kodierungen, NUL, leere/blanke Quellen und überschrittene Grenzen blockieren.
Encoding-Cookies sind keine Erlaubnis zum Umkodieren. Code-v1-Zeilen verwenden den
bestehenden `splitlines(keepends=True)`-Vertrag; Unicode-Zeilentrenner innerhalb
eines Pythonstrings können daher andere Blockzeilen als Python-AST-Zeilen ergeben.
Rawbytes und AST-Zeilen bleiben getrennte, nachvollziehbare Referenzen.

AST-Projektionen enthalten Imports, Klassen, synchrone/asynchrone Funktionen,
Docstrings und Start-/Endzeilen, in Quellreihenfolge. Ein isolierter lokaler
`python -I -B`-Prozess liest nur stdin; er importiert oder startet keinen Quellcode.
Grenzen: 1 MiB Input, 20.000 AST-Knoten, 256 MiB Adressraum, 2 CPU-Sekunden,
5 Sekunden Walltime, kein Core-Dump. Syntaxfehler oder Ressourcenprobleme ergeben
`syntax_error` bzw. `undetermined`; der vollständige Code-v1-Text bleibt erhalten.
AST ist eine optionale technische Sicht, kein Sicherheits- oder Korrektheitsbeweis.

Dateiversionen sind durch Raw-SHA und bestehende Document-ID (Material + Raw-SHA +
Parserkonfiguration) gebunden. `import.v1.json` bindet außerdem Batch, aktuelle
Genehmigungen, Python-/Implementierungsstand, Mitgliedszuordnung und alle
Ausgabebytes. Gleichnamige Beispiele, etwa `hello0.py` und `hello1.py`, bleiben
getrennte Quellen. HTML-Codebeispiele werden nicht zusammengeführt; ein späterer
read-only Vergleich kann die expliziten Codeblöcke/Rawhashes gegenüberstellen,
ohne die vorhandenen IDs oder Artefakte zu verändern.

## Tatsächlicher Week-0-Bestand und Adaptermatrix

Quelle ist ausschließlich der versionierte Snapshot
`docs/course_sources/cs50/cs50_python/cdn.html`, SHA256
`fbedb5c020f2ec86b225ef43b2a30bd4f4849310f65d4bcaff98fa3748e875e0`.
Original-Codeindex: <https://cdn.cs50.net/python/2022/x/lectures/0/src0/>.
Kein aktueller Abruf, keine Raw-Python-/ZIP-Dateien und keine Nutzungsprüfung.

| Material | Nachgewiesene Referenz | B6-Behandlung / offene Grenze |
| --- | --- | --- |
| `calculator0.py` bis `calculator11.py` | 12 direkte Dateilinks | Eigenständige, ausdrücklich auswählbare Code-v1-Kandidaten |
| `hello0.py` bis `hello11.py` | 12 direkte Dateilinks | Eigenständige Kandidaten, keine automatische Versionsverschmelzung |
| `?download`, `?highlight`, `?view` | Je Datei drei zusätzliche Ansichten, insgesamt 72 | Original-URLs und Gruppierung im Inventar; Inhalt unbekannt, nicht importierbar |
| `src0.zip` | Bereits vorhandener Week-0-Kandidat, URL <https://cdn.cs50.net/python/2022/x/lectures/0/src0.zip> | Begrenzter Offlineimport mit expliziter Mitgliederzuordnung; tatsächlicher Inhalt fehlt |
| HTML-Codeindex / Notes | Bestehende HTML-v2-Verträge | Unverändert, kein Ersatz für Python-Rawdateien |
| Code-PDF / Slides | Bestehende PDF-v2-Verträge | Unverändert; kein Nachweis bytegleicher Python-Beispiele |
| SRT / TXT | B5-Offlineadapter | Unverändert und getrennt |
| Weitere ZIP-Typen, Binärdateien, Medien | Keine B6-Freigabe | Explizit ausgeschlossen, kein OCR/Whisper/LLM/Embedding |

Das Codeinventar enthält 98 Referenzvorkommen: 96 Pythonlinks und zwei vorhandene
ZIP-Vorkommen (Kandidat und Snapshotlink), **nicht 98 Dateien**. 24 direkte Python-
URLs werden Kandidaten; für die Queryansichten wird keine Bytegleichheit behauptet.
Der bestehende ZIP-Source-ID bleibt
`resource:374e8ffb231647383210f7daa93113c16488bc045d3bde40bae788112593e91a`,
die Lecture-ID
`resource:4305fcd17cb0d9c50cfdd5e2718461e8369cb883189de96bda796f04cc800192`.
Der Codeindex-Source-ID bleibt
`resource:5f51d97877d3ddbc6699e5c9b484c47b601ce15d1373cfdef065d8fad47b5944`.
Neue direkte Source-/Material-IDs liefert das Inventar mit dem bestehenden Modell;
`snapshot_ref`-IDs werden ausdrücklich nicht als Source-IDs übernommen.

## ZIP-Sicherheitsvertrag und Ressourcen

Keine Mitgliedsnamen werden als Ausgabepfade verwendet: nur existierende Material-
und Document-Hashes bestimmen die Ablage. ZIP-Mitglieder werden begrenzt im Speicher
gelesen und gehasht; kein `extract`, `extractall`, rekursiver Entpacker oder Start
von Dateien. Vor der Materialpublikation wird das **gesamte** Archiv geprüft.

| Grenze | Verhalten |
| --- | --- |
| Raw-Python und Raw-ZIP je höchstens 1 MiB | Bestehendes Batchlimit unverändert; niedrigere Auswahlgrenzen bleiben wirksam |
| Höchstens 8 ausgewählte Quellen inkl. Archiv | Ein ZIP plus höchstens 7 explizit zugeordnete Pythonquellen; ein Writer |
| Höchstens 64 Archivmitglieder inkl. Verzeichnissen | EOCD-Count vor ZipInfo-Allokation begrenzt, keine ZIP64-/Mehrdiskarchive |
| Je Mitglied höchstens 1 MiB, gesamt höchstens 8 MiB, Verhältnis höchstens 100:1 | Auch nicht ausgewählte/ausgeschlossene Mitglieder zählen; CRC-/Istgrößenprüfung |
| Nur STORED/DEFLATED, keine Verschlüsselung | Andere Verfahren/Layoutvarianten blockieren |
| Traversal, absolute/Windows-/Backslash-/Steuerzeichenpfade, Symlinks, Spezialdateien, Namens-/Datei-Verzeichniskonflikte | Gesamtes Archiv blockiert; NFC-/Casefold-Kollisionen ebenfalls |
| Verschachtelte Archive/unbekannte Typen | Mit Hash und Ausschlussgrund inventarisiert, niemals weiter entpackt |
| Ausführbar markierte ZIP-Dateien, nicht-UTF-8-/NUL-/leere Pythonmitglieder | Ausgeschlossen; eine Auswahl solcher Mitglieder blockiert |
| Projektion je Code maximal 8 MiB, Importgruppe maximal 16 MiB | Zusätzliche Obergrenzen innerhalb des bestehenden Gesamtbudgets |
| Archivroot höchstens 64 MiB, freie Reserve mindestens 5 GiB | Keine Aufweichung durch B6; Kapazitätsprüfung auch für Staging/Publikation |

Eine ZIP-Freigabe erteilt keine Freigabe für alle enthaltenen Quellen. Für jedes
ausgewählte Mitglied müssen eine bereits nachgewiesene Pythonquelle, deren eigene
Process-Freigabe und ein erwarteter SHA vorhanden sein. Die ausdrücklich angegebene
Zuordnung und Bytegleichheit zum freigegebenen Hash sind der Beleg; der Adapter
behauptet keinen unabhängigen HTTP-Abruf dieser Python-URL. Unbekannte Pythondateien
bleiben `excluded_not_selected`, auch wenn ihr Name plausibel aussieht.

## Separat freizugebender Realpilot im bestehenden Worker

Noch erforderlich: tatsächlicher Merge und kontrolliertes Update desselben Images;
neuer privater B6-Root mit vorhandener Mount-Policy/Worker-Ownership; ausdrücklich
benannte lokale Originale und Hashes; Download- und Process-Entscheidung je Quelle
einschließlich Nutzungs-, Lizenz-, Robots-, Aufbewahrungs- und Widerrufsbelegen.
Keine pauschale Download-/Nutzungszulässigkeit aus öffentlicher Erreichbarkeit.
ZIP-Mitgliedsinventur/Hashprüfung muss ausdrücklich erlaubt sein, bevor daraus
die konkrete Mitgliederfreigabe erstellt wird. B6 beschafft keine Dateien.

Das bestehende Worker-Dockerfile kopiert `src` und `scripts/cs50_batch.py` bereits.
Keine Dockerfile-, Dependency-, Mount-, CMD- oder Restartänderung erforderlich.
Das Update und alle folgenden realen Schritte sind **nicht durch diesen PR
ausgeführt oder freigegeben**. Nur ein Prozess, keine zusätzlichen Container.

Folgende Variablen muss der Betreiber mit bestätigten Werten setzen; kein Beispiel
erteilt Root-/Quellenfreigaben. Der Elternroot ist neu, privat (0700), außerhalb
des Codes bzw. gemäß bestehender Mountpolicy freigegeben; Dateien 0600. Keine
Übernahme von `cs50_pilot_01`, B4/B5 oder globalen Store-/Archivroots.

```sh
: "${C26_B6_ROOT:?Neuen privaten Arbeitsroot bestätigen}"
: "${C26_B6_MANIFEST:?Verifiziertes Discoverymanifest benennen}"
: "${C26_B6_ZIP_ID:?Archiv-Source-ID aus Inventar bestätigen}"
: "${C26_B6_PY0_ID:?Erste direkte Python-Source-ID bestätigen}"
: "${C26_B6_PY1_ID:?Zweite direkte Python-Source-ID bestätigen}"
export C26_PYTHON=/app/.venv/bin/python
umask 077

"$C26_PYTHON" -B -m scripts.cs50_batch code-inventory \
  --manifest "$C26_B6_MANIFEST"
"$C26_PYTHON" -B -m scripts.cs50_batch plan \
  --manifest "$C26_B6_MANIFEST" --course cs50_python --include-code-indexes \
  --resource "$C26_B6_ZIP_ID" --resource "$C26_B6_PY0_ID" --resource "$C26_B6_PY1_ID" \
  --limits "$C26_B6_ROOT/limits.json" --output "$C26_B6_ROOT/batch.json"
```

`limits.json` nutzt unverändert CapacityLimits, z. B. `reserve_bytes=5368709120`,
`archive_bytes=67108864`, `max_materials=8`; alle übrigen Standardbudgets bleiben.
`approvals.json` nutzt unverändert Approvals/SourceApproval: pro ausgewähltem
Material exakte `material_id`, `source_id`, `course_id`, `original_url`,
`expected_sha256`, alle sechs nichtleeren `*_reference`-Belege und die separat
entschiedenen `process`-/`download`-Flags. `process=true` nur nach tatsächlicher
Freigabe, `download=false` genügt für bereits freigegebene lokale Originale.
Keine erfundenen Actor-IDs oder Backend-Capabilities.

`inputs.json` ist eine private explizite Auswahl, kein automatischer Scan.
Platzhalter ersetzen, bevor validiert wird:

```json
{
  "<ausgewählte ZIP-Source-ID>": {
    "path": "<explizit freigegebener absoluter lokaler ZIP-Pfad>",
    "members": {
      "<tatsächlicher relativer Mitgliedsname 1>": "<Python-Source-ID 1>",
      "<tatsächlicher relativer Mitgliedsname 2>": "<Python-Source-ID 2>"
    }
  }
}
```

Für standalone Python stattdessen `{"<Python-Source-ID>": {"path": "<absoluter
Originalpfad>"}}`, mit genau diesen Quellen im Batch. Keine Quelle zugleich
standalone und als Mitglied oder in mehreren Archiven auswählen. Vollständige
Kurs-/Lecturebindung wird erneut gegen die Snapshotbytes geprüft.

```sh
# Neue Ausgaben, keine vorhandenen Dateien überschreiben.
"$C26_PYTHON" -B -m scripts.cs50_batch code preview \
  --batch "$C26_B6_ROOT/batch.json" --archive "$C26_B6_ROOT/code-archive" \
  --inputs "$C26_B6_ROOT/inputs.json" --approvals "$C26_B6_ROOT/approvals.json" \
  --limits "$C26_B6_ROOT/limits.json" --output "$C26_B6_ROOT/preview.json"
# Erst nach separater expliziter Inhaltsverarbeitungsfreigabe:
"$C26_PYTHON" -B -m scripts.cs50_batch code import --confirm \
  --batch "$C26_B6_ROOT/batch.json" --archive "$C26_B6_ROOT/code-archive" \
  --inputs "$C26_B6_ROOT/inputs.json" --approvals "$C26_B6_ROOT/approvals.json" \
  --limits "$C26_B6_ROOT/limits.json" --output "$C26_B6_ROOT/import-report.json"
"$C26_PYTHON" -B -m scripts.cs50_batch code report \
  --batch "$C26_B6_ROOT/batch.json" --archive "$C26_B6_ROOT/code-archive" \
  --inputs "$C26_B6_ROOT/inputs.json" --approvals "$C26_B6_ROOT/approvals.json" \
  --limits "$C26_B6_ROOT/limits.json" --output "$C26_B6_ROOT/verify-report.json"
```

Preview öffnet keine Originalinhalte, prüft weder ZIP-Inhalt noch dessen Hash und
ist keine Kapazitäts-/Mountfreigabe. Import/Report prüfen aktuelle Process-Grants,
Hashes und Quality/Handoff. `report` liest eigene Archivbytes, benötigt das gleiche
Mapping, aber keine verfügbaren Originaldateien. Importgruppen publizieren ihren
abschließenden `import.v1.json` zuletzt; kein erfolgreicher Zustand ohne erneute
vollständige Prüfung. `materials/<Materialhash>/` enthält unverändertes `raw/source`,
bestehenden `receipt.v1.json`, NormalizedDocument sowie AST-/Quality-/Handoff-Sichten.
Das äußere `raw/source` enthält das unveränderte ZIP bzw. die standalone Quelle.
Rawduplikate werden bei der Kapazität mitgezählt, keine Symlink-/Hardlinkersatzlösung.
Die Prüfung benötigt konservativ bis zu 16 MiB zusätzliche Reserve im Archivbudget
für ihr privates Staging. Daher können auch erneute Prüfungen eines nahezu vollen
Archivs kontrolliert blockieren; kein automatischer Budgetanstieg oder Cleanup.

Exit 0 bedeutet technische Operation erfolgreich, 1 mindestens eine Importgruppe
blocked/missing, 2 Input-/Konfigurations-/Ausgabekonflikt. Gruppenstatus zählt ZIP
und seine Mitglieder gemeinsam; `processed_materials` zählt ausgewählte Quellen
einschließlich Archiv, nicht nur Pythondateien. Ausgeschlossene Mitglieder stehen
im Einzelreceipt/-bericht. `full_week_coverage=false`, `execution_supported=false`
und `knowledge_fact_verified=false` bleiben ausdrücklich erhalten.

Wiederanlauf: denselben Importbefehl mit unveränderten Eingaben/Grants ausführen,
aber ohne schon verwendeten `--output` oder mit neuem Reportnamen. Erfolgreiche
Gruppen bleiben byteidentisch, fehlende Originale dürfen ausdrücklich nachgereicht
werden. Widersprüchliche Hashes/Zuordnungen, neue Implementierungsrevision, geänderte
Receipts oder unvollständige Publikationen blockieren; keine automatische Reparatur,
Adoption oder Löschung. Eine Diagnose und ggf. ein neuer separat genehmigter Root
sind erforderlich. Ein AST-Timeout kann bei später abweichendem Workergebnis die
konservative Wiederholungsprüfung blockieren; keine stillschweigende Umschreibung.

Vollkursblocker: fehlende Originale/Quellenfreigaben, tatsächliche ZIP-Layouts und
Mitgliedsbeziehungen ungeprüft, Queryviews ohne Contentnachweis, weitere Kurswochen
außerhalb dieses Adapters, Speicherplanung für größere Archive, unabhängige
fachliche Reviews und spätere explizite Queue-/Knowledge-Vertragsfreigabe. Keine
reale oder vollständige Wochenabdeckung aus synthetischen Tests ableiten.
