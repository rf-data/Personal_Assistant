# C18: ausdrücklich gebundene Aufgabenübersichten

Vorgeschlagener Follow-up auf Backend `c4b057a75c38655e43b8ac35a35cc82645ba2826`.
Kein neuer Discoverydienst, Worker, Importer oder Queuepfad. Der vorhandene
B5-Algorithmus zur einstufigen Aufgabenableitung ist nach
`src/tools_materials/assignments.py` ausgelagert. B5 und die C18-Rekonstruktion
verwenden damit dieselben Resource-/Material-ID-, Parent-, URL- und DOM-Regeln.

## Kompatibler Opt-in

`WeekRequest` / `ProfiledWeekRequest`: ausdrücklich `assignment_discovery: true`.
Standard ist weiterhin false und wird aus der Serialisierung weggelassen. Alte
Anfragen behalten ihre Bytes und ihren bisherigen Discoveryumfang. Ohne Opt-in
bleibt ein nur von B5 abgeleitetes Child weiterhin für C18 gesperrt.

`Batch` und Workflow-`Definition` verwenden **schema_version 2** ausschließlich
mit nicht leeren `assignment_snapshots`. Ohne diese Erweiterung bleiben sie v1;
das neue leere Feld wird nicht serialisiert. Alte Bundles und IDs bleiben lesbar,
werden nicht migriert oder umgeschrieben. Alte Leser können neue v2-Bundles
verweigern; neue Producer und Worker müssen daher dieselbe geprüfte Version nutzen.
Workflow-Report, C16-Prozess, Queue und bisheriger Workflowtyp bleiben unverändert.
Pro Definition weiterhin höchstens drei Quellen; B5 erzeugt für die fünf Aufgaben
fünf getrennte Ein-Quellen-Batches, keinen unerlaubten Fünfer-Workflow.

Ein Snapshot enthält:

| Feld | Bindung |
| --- | --- |
| `file` | Relativer HTML-Provenienzlabel, exakt derselbe wie im ursprünglichen B5-Request |
| `url` | Exakte bereits belegte Aufgabenübersichts-URL, kein geratenes Ziel |
| `role` | Ausschließlich `assignment` |
| `sha256` | Pflicht, SHA-256 der vorhandenen Übersichtsbytes |
| `path` | Im lokalen Batch explizit absolut; in der Definition relativ zum geprüften Katalogroot |

Die Übersicht muss genau einen vorhandenen Parent einer Kurswoche treffen.
Keine fremden URLs, rekursive Beschaffung oder Codeindexanalyse. Beim Worker
müssen Pfad und Hash zusätzlich im unveränderlichen `CatalogEntry.files` stehen.
Relative Ausbrüche, Symlinks, doppelte/mehrdeutige Snapshots, Labelkollisionen und
Hashabweichungen verweigern die Rekonstruktion. Die ursprüngliche Manifestclosure
wird vor dem neuen Adapter mit dem vorhandenen 120-Dateien-/1-MiB-je-Datei-/
8-MiB-Gesamtlimit geprüft; höchstens acht zusätzliche Übersichten à 1 MiB.
Die bestehenden Katalog-/Job-/Outputgrenzen bleiben zusätzlich wirksam.

Bereits deklarierte Assignment-Detailfixtures werden vor externen Übersichten
besucht. Das ist entscheidend für die exakte bisherige Reihenfolge der
DOM-Provenienz von Indoor Voice. Es werden keine neuen Aufgabeninhalte daraus
behauptet. Discovery, Batch-Revalidierung, C16-Katalogindexierung und Worker
rekonstruieren dieselben Bindungen; ein alter oder manipuliert vorberechneter
Cacheplan kann die neue Prüfung nicht umgehen.

`batch.seal` kopiert ausschließlich explizit gehashte Eingaben in einen neuen
isolierten Katalogroot, bindet die relocateten Snapshots in Definition und
Kataloghashes und prüft das Ergebnis mit dem vorhandenen `prepare`. Kein Schreiben
in die Originale. Für die neue v2-Verarbeitung ist der konkrete Rawhash in der
SourceApproval Pflicht. Das Opt-in ersetzt weder SourceApproval noch Kapazitäts-,
Queue-, Worker-, Parser- oder Quality-Gate-Prüfungen.

Die vorhandene `manual_only`-Policy wird auch am v2-Batch- und Workerübergang
geprüft. Eine als Aufgabe verlinkte `attack.py/` wird dadurch nicht zu automatisch
importierbarem HTML. Code/ZIP/Medien bleiben in ihren bestehenden getrennten Wegen.
Der B6-Vertragsfingerprint nimmt auch die geteilte Ableitung und die neuen Modelle
auf; alte Referenzabnahmen dürfen Änderungen daran nicht unbemerkt überspringen.

## Reproduzierbare Vorbereitung ohne Jobs

Die Originale werden nur gelesen. Vorhandene DiscoverySnapshot-Labels aus dem
geprüften B5-Request beibehalten. Keine Referenzen oder IDs von Hand erfinden.

1. Im expliziten Week-/Course-Request `assignment_discovery: true` setzen und die
   echte PSet-Übersicht als vorhandenen `discovery_export` mit Label, URL, Rawhash
   und absolutem Originalpfad binden. Bestehende `cs50_week`-/`cs50_course`-Planung
   erzeugt nur einen Bericht. Fehlende Childraws und Grants bleiben blockiert.
2. `prepare_material_batches(request, approvals)` liefert nur bei erfüllten
   bestehenden Voraussetzungen die v2-Batches. Keine implizite Submission.
3. Alternativ nimmt der bestehende Batch-CLI eine **explizite** JSON-Liste dieser
   Snapshotreferenzen an; `--resource` muss die aus dem Plan geprüfte Auswahl sein:

   ```sh
   "$TEST_PYTHON" -B -m scripts.cs50_batch plan \
     --manifest "$PINNED_MANIFEST" --course cs50_python \
     --resource "$EXISTING_CHILD_MATERIAL_ID" \
     --assignment-snapshots "$EXPLICIT_SNAPSHOT_REFERENCES" \
     --output "$OWN_BATCH_REPORT"
   ```

   Das ist keine Beschaffungs-/Verarbeitungsfreigabe. `seal`/Import benötigen die
   bestehenden Grants, gehashte Rawdaten, Kapazität und getrennte private Ziele.
4. Erst nach regulärer Codeintegration und Betreiberfreigaben dürfen vorhandene
   C16/C18-Pfade die versiegelten Inputs annehmen. Alte Pilotroots bleiben erhalten.

Der echte Exporttest prüft alle fünf historischen IDs, Parentbeziehungen und die
**vollständige bisherige Provenienz** gegen B5 sowie frische C18-Vorbereitung und
C16-Indexrekonstruktion. Er verarbeitet keine fehlenden echten Aufgabeninhalte.
Ein weiterer Test führt ausdrücklich synthetische Aufgaben durch B5, vorhandenen
Downloadreceipt-/Sealingpfad und den echten lokalen C16/C18-Worker. Beide Arten
von Belegen werden im Pilotbericht getrennt gezählt.

Rollback auf einen alten Worker erst nach bestätigtem Drain ohne wartende oder
aktive v2-Jobs. Keine v2-Definitionen für einen alten Reader umschreiben und keine
alten Ergebnisse nachträglich adoptieren; Quell- und Ergebnisartefakte erhalten.
