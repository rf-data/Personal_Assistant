# C27-R08 – Export Metadata Boundary Remediation

## Baseline und Ursachenanalyse (vor Implementierung)

Arbeitsauftrag vom 29.10.2026, ausschließlich offline im zugewiesenen Worktree.
Branch `feat/c27-cs50-learning-pipeline`, HEAD/Basis
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Vorher: drei modifizierte
versionierte Dateien, 56 unversionierte Dateien, kein Indexdiff. Die 59 R06-
Manifestdateien stimmen bytegenau; Basis plus gesicherter R06-Gesamtpatch ergibt
1.188 Dateien und entspricht dem vorgefundenen C27-Baum.

R07-Recovery `review-r07-recovered.EVCt5FOw`: Prüfer bestätigt 1.566 SHA-256-
Einträge und 1.655 Eintragsidentitäten einschließlich Modi und Linkzielen.
Auch die Manifeste von R04/R05/R06 sind unverändert gültig. Der Recovery-Nachtrag
zur fehlenden zeitgenössischen R07-Versiegelung bleibt maßgeblich.

Vor der Implementierung erneut reproduziert: acht Aliaskombinationen (vier
Felder mal mailto/tel), historische v1 und v2 einschließlich Review/Report sowie
reale Streamlit-Downloadpayloads: elf Canary-Assertions. Der zwölfte Fall betrifft
die vier tatsächlich durch `cli.main` geschriebenen Dateien. Sein frischer
Processinglauf stoppt bei 4,6 GiB freiem Speicher am unveränderten 5-GiB-Wächter.
Deshalb wurde zusätzlich das checksummengeprüfte synthetische R07-CLI-Fixturearchiv
in ein eigenes Verzeichnis rekonstruiert, seine Dateimodi wiederhergestellt und
sein regulärer, hashgeprüfter Processingcache verwendet. Neue Summaryläufe und
alle vier neuen CLI-Exportdateien enthalten den Canary: zwölf Schutzverletzungen
vor der Änderung belegt, der frische CLI-Pipelinepfad bleibt separat zu prüfen.
Keine Speicherprüfung wurde verändert oder gemockt.

Ursache: `metadata_text` aktiviert den allgemeinen URI-Scanner nur bei einer
Aufzählung einzelner Schemata oder `//`. `mailto:` und `tel:` erreichen unverändert
den Rückgabepfad. Modellvalidatoren, historische Nevalidierung, Cache und finale
Exporter teilen diesen unvollständigen Prüfer. `source_url_status=withheld`
verhindert daher keine Aliasoffenlegung. `Material`/Katalog und private Inputs
enthalten absichtlich die Originalprovenienz; öffentliche `SourceRef`-Metadaten
sind bereits seit R06 eine eingeschränkte Sicht. Persistierte Ergebnisbytes und
Review-Hashbindungen dürfen beim Lesen/Exportieren nicht umgeschrieben werden.

## Festgelegter Änderungsumfang

Die finale Exportgrenze erhält eine explizite Metadatenprojection des bestehenden
Ergebnisvertrags. Nur die bekannten Quellenauszüge und Claimtexte bleiben von
Metadatenprüfungen ausgenommen. Die URI-Prüfung wird schemagenerisch statt durch
weitere Blacklisteinträge definiert, prüft Original und dekodierte Sichten und
behält die bestehende exakte Quellenfreigabe bei. Weitere Architektur-, Parser-,
Parent-, Provider-, Git- oder Produktionsänderungen sind nicht vorgesehen.

Implementierung, abschließende Test- und Patchnachweise werden nach Validierung
in diesem Dokument ergänzt. Evidenzablage: `/tmp/c27-remediation-r08.xqBDn5MQ`.

## Öffentlicher Feldvertrag R08

`public_result` projiziert die Metadaten explizit, bevor das strikte Ergebnismodell
nochmals validiert wird. Top-Level-Metadaten, Konfiguration, Quellenmetadaten,
Locators, Sectionmetadaten und Claimtopics passieren denselben zentralen Prüfer.
Nur `SourceRef.text` und `Claim.text`, einschließlich Sectionclaims, werden als
fachlicher Freitext bytegetreu übernommen. Das gilt auch für dort absichtlich
enthaltene URI-Beispiele und mathematische Ausdrücke. Allgemeine Secret-Erkennung
in beliebigem Freitext oder opaken Zeichenfolgen wird nicht behauptet.

| Feld | Öffentliche Ausgabe |
|---|---|
| `provenance.source_url` | Ausschließlich bestehende exakte HTTPS-Freigabe; andernfalls null. `available`/`missing`/`withheld` bleiben erhalten. |
| `source_path` | Unverdächtige lokale relative Pfadidentität unverändert; URI-artige/private Werte vollständig `[withheld metadata]`. Kein erfundener Ersatzpfad. |
| `provenance.title`, `.license`, `.attribution` | Normale Metadaten unverändert; ein unzulässiger URI-Kandidat hält das gesamte Feld zurück. Fehlend bleibt null, zurückgehalten erhält den bestehenden Marker. |
| Quellen-/Material-/Block-/Artefaktidentitäten | Bestehende lokale ID-Grammatiken ausschließlich in bezeichneten Identitätsfeldern erhalten. Keine Quellenfreigabe durch eine ID-Grammatik. |
| Review- und CLI-Reportmetadaten | Gleiche feldbezogene Prüfung, einschließlich verschachtelter Werte und Review-Snapshots. |

Der Scanner erkennt generisch RFC-Schemanamen einschließlich opaker URIs ohne
`//`, unbekannte Schemata, Groß-/Kleinschreibung und mehrdeutige Leerzeichen um
den Doppelpunkt. Original und begrenzt prozentdekodierte Prüfsicht müssen beide
freigegeben sein. Unicode-NFKC und HTML-Entities werden ausschließlich in der
Prüfsicht aufgelöst. Ausgegeben wird entweder der unveränderte Originalwert oder
der konstante Marker; keine teilweisen Reparaturen und keine Originalwerte in
Ablehnungsgründen. Die bisherigen Tiefen-/Größen-/Knotenlimits bleiben bestehen.

Konservative Grenze: Auch ein menschliches Label wie `Python: Functions` kann
als mehrdeutiges `scheme:payload` vollständig zurückgehalten werden. Titel ohne
diese Mehrdeutigkeit, übliche Lizenzen und Attributionen bleiben erhalten;
Zeitangaben wie `00:01` bleiben erhalten. Die Policy behauptet keine semantische
Unterscheidung beliebiger natürlicher Labels und unbekannter URI-Schemata.

Lokale Kennungen sind ein eigener Vertrag: bekannte hashgebundene Namespaces,
die bestehenden synthetischen Fixture-IDs, numerische Cue-/Notes-/Code-IDs und
hashgebundene Artefaktdateinamen. Credentialmarker bleiben auch dort gesperrt.
Die bestehenden internen Modellvalidatoren erhalten skalare lokale IDs zur
Kompatibilität. Öffentliche Grenzen übergeben vollständige Feldmappings: dieselbe
Zeichenfolge in `source_path`, Titel, Lizenz, Attribution oder Reviewkommentar
bekommt keine Identitätsausnahme. Auch der eigenständig aufrufbare `source_label`
projiziert deshalb ein Feldmapping. Unbekannte URI-Schemata werden nicht durch
Namensähnlichkeit zu internen Identitäten freigegeben.

## Datenhaltung und Exportwege

Katalog/Material und der private `input.json` behalten Originalprovenienz und
bleiben maßgeblich für Cacheidentität und Nachprüfung. Neue Resultmodelle behalten
ihre bestehenden R06-Sicherheitsvalidatoren. Es gibt keine Änderung an Adapter,
Modellen, Engine, Store, Parentbindung oder Cacheberechnung. Die ursprünglichen
Modell-/Adapterdateien stimmen bytegenau mit R06 überein. Bei neuen Ergebnissen
können vormals durchgelassene unsichere Metadaten bereits bei der Modellbildung
zurückgehalten werden; die internen Inputdaten bleiben erhalten. Historische
Ref-/Claim-/Content-/Materialhashes werden beim Export nicht neu berechnet.

Historische v1/v2-Ergebnisse werden weiterhin nur im Speicher auf v2 gelesen;
ursprüngliche Result- und Reviewbytes und ihre Hashbindungen bleiben unangetastet.
JSON läuft über `SummaryStore.export_json` → `public_result`/`public_reviews`;
Markdown über dieselben beiden Projectors und `source_label`. UI-Downloads und
reguläre CLI-Dateien verwenden diese Exporter. CLI-stdout wird separat durch
`public_processing_report` projiziert. Private Byte-I/O-Primitiven `read` und
`publish` sind weiterhin keine automatischen Sanitizer.

Das öffentliche Envelope bleibt `export_schema_version=2`, das Resultmodell v2.
Keine Felder, Typen oder zulässigen Statuswerte werden entfernt/hinzugefügt;
die bestehende Withholding-Semantik wird an der vorgesehenen Grenze durchgesetzt.
Daher keine inkompatible Schemaänderung und kein Versionssprung. Dieses Dokument
versioniert die verschärfte Feldpolicy ausdrücklich als R08.

## Bereits vorhandene Exportdateien

Frühere `export.json`, `export.md` und `export-review-*` sind durch einen neuen
Exporter nicht rückwirkend sicher. Unveränderliche Veröffentlichung bleibt aktiv:
bei abweichendem Inhalt unter demselben Namen muss `publish` ablehnen. Die CLI
kann bei einem alten Export folglich einen Konflikt melden; das ist kein Grund,
alte private Result-/Reviewdateien oder veröffentlichte Dateien zu überschreiben.

Kontrollierter Neu-Export nach gesonderter Auswahl eines bestehenden Run:
`store.export_json(run_id)` und
`markdown(store.result(run_id), store.reviews(run_id))` erzeugen aktuelle Bytes;
beide mit `store.publish` unter **neuen, eindeutig gewählten** Namen wie
`export-r08-<uuid>.json` und `export-r08-<uuid>.md` ablegen. Run-ID,
`result_sha256`, Review-ID, alte/neue Exporthashes und Policystand in einem
separaten Inventar protokollieren und die neuen Dateien vor Weitergabe prüfen.
Alte öffentliche Downloads erst nach konkreter Eigentums-/Nutzungsprüfung aus der
Freigabe nehmen bzw. separat quarantänisieren; Rohresultate und Reviewhistorie
bewahren. Hier wurden keine vorhandenen Exporte verschoben, geändert oder gelöscht.

## Grenzen und Abschlussstatus

Der 5-GiB-Wächter wurde unverändert gelassen. Die reserveschwache Umgebung
verhindert weiterhin frische Processing-/CLI-/Teile der Parent-Positivtests.
Daraus darf kein vollständiger Regressionserfolg abgeleitet werden. Der CLI-
Sicherheitsnachweis verwendet den verifizierten synthetischen R07-Processingcache,
keine manipulierte Receipt und keine abgeschwächte Speicherprüfung.

Zwischenläufe bleiben transparent erhalten: ein erster Rekonstruktionsaufruf mit
dem System-Python unterstützte den Tarfilter nicht; ein erster Replay stellte
Tar-Verzeichnismodi noch nicht wieder her und scheiterte kontrolliert am privaten
Dateimodusgate. Ein früher Implementierungsstand maskierte lokale IDs; die
Originaltests deckten dies auf und die finale feldbezogene Projection behebt es.
Eine zunächst zu breite historische Testauswahl enthielt sechs bereits durch R06
überholte Leak-/HTTP-Positiverwartungen; die abschließende Auswahl entspricht dem
R06/R07-Prüfumfang und ändert keine Assertions. Keine alten Tests wurden geändert.

Keine Commits, Pushes, PRs, Merges, Branch-/Worktreeanlage oder -entfernung. Die
AGENTS.md-Ablage im Defaultbranch ist wegen des ausdrücklichen Integrationsverbots
nicht erfolgt; Dokumente und vollständiger Patch sind zur späteren autorisierten
Reviewintegration vorbereitet. Vorhandener Branch/Worktree und alle früheren
Änderungen bleiben erhalten. Es gibt keine eigenen temporären Git-Artefakte.

## Abschließende Testentscheidung

Alle Ausführungen offline, Socket-/Infrastrukturguard aktiv, ausschließlich
FakeLLM. Keine Produktlimits, Assertions oder Freiraumprüfungen abgeschwächt.
Die letzten relevanten Läufe werden fallweise ausgewertet; Zwischenläufe und
Wiederholungen werden nicht zu zusätzlichen bestandenen Tests aufaddiert.

| Prüfumfang | Bestanden | Kapazitätsbedingt fehlgeschlagen | Skip |
|---|---:|---:|---:|
| Bestehende C27/Summarizer/UI/Pipelineregression, 20 Dateien | 790 | 23 | 2 |
| Historische R03/R05-Negativ-/Parentauswahl | 111 | 6 | 0 |
| Sechs frühere HTTPS-Positivfälle | 6 | 0 | 0 |
| Zusätzliche R07-Fälle | 73 | 1 | 0 |
| R08, eindeutig über den Suite- und Ergänzungslauf | 97 | 1 | 0 |

Damit sind von den 938 bisherigen Fällen 907 bestanden, 29 am Speicherwächter
blockiert und zwei unverändert übersprungen. Keine nachgewiesene verbleibende
Produktassertionsregression; die fehlenden 29 Erfolgsnachweise werden ausdrücklich
nicht aus R06 übernommen. Der historische CLI-Subprozess wurde zusätzlich mit
erfasstem stderr am gleichen unveränderten Kapazitätsgate nachgewiesen.
Die zwölf überführten R07-Szenarien sind Teil der R08-Datei und werden bei der
Sicherheitsentscheidung nur einmal gezählt, nicht als 24 geschlossene Fälle.

Alle 75 aus der R05-Evidenz übernommenen CS50-URLs bleiben bytegenau freigegeben,
in JSON und Markdown enthalten. Positive Prüfungen vergleichen vollständige
Quellenmetadaten, IDs, Ref-/Contenthashes und Locators, legitime Titel/Lizenzen/
Attributionen, Reviewstatus und unveränderte private Resultbytes. Die eigenständige
R08-Fixture ist gegenüber der vor R08 gesicherten URLliste abgeglichen, nicht
bloß aus der aktuellen Freigabekonfiguration erzeugt. Historische v1/v2-,
Cache-/Nevalidierungs-, mutierte Modell-, UI- und fachliche Freitextproben bestehen.

Ruff: PASS; Format: PASS, 25 Dateien. Globaler Mypyvergleich auf unabhängig aus
Basis plus gesichertem Patch rekonstruiertem R06: **6.104 → 6.104**, null neue,
null entfernte Diagnosen. Alle Diagnosen sind nach Pfad/Nachricht und mittels
Quellzeilenabbildung zugeordnet. **Mypy ist nicht grün.**

| Entscheidung | Ergebnis |
|---|---|
| R07-Schutzverletzungen | 12/12 im Export geschlossen; CLI mit verifiziertem Processingcache, frischer CLI-Lauf kapazitätsbedingt offen |
| F04 | FIXED im verifizierten Exportumfang |
| F01/F02/F03/F05 | Keine nachgewiesene Regression; kapazitätsblockierte Prüfungen bleiben offen |
| Parent-Fix | Keine nachgewiesene Regression; frische positive Processingprüfungen teilweise blockiert |
| C27 | BLOCKED, vollständige Regressionsvalidierung steht aus |
| Week 0 | PARTIAL |
| Multicourse | PLANNING_ONLY |

R08 ist damit **implementiert und reproduzierbar zur unabhängigen Prüfung
vorbereitet, aber unter der Erfolgsdefinition noch nicht vollständig abgeschlossen**.
Nach zusätzlichem freien Speicher sind ausschließlich die manifestierten
Kapazitätsfehler mit unveränderten Gates in neuen eigenen Testverzeichnissen zu
wiederholen. Keine PR-, Merge- oder Produktionsfreigabe wird erteilt.

## Patch- und Erhaltungsnachweise

Handoff: `/tmp/c27-remediation-r08.xqBDn5MQ`, außerhalb des Worktrees; der bevorzugte
Homepfad liegt außerhalb der erlaubten Schreibwurzeln. Enthalten: Gesamtpatch
`c27-full-vs-a8af1d9.patch`, ausschließliches Delta `c27-r08-vs-r06.patch`,
verifizierter R06-Patch, vollständige Dateimanifeste, Befund-/Test-/Mypy-/Export-
Nachweise, Vorher-/Nachherzustände sowie ausführbare Rekonstruktions- und
Übergabeprüfer. `patch-verification.json` protokolliert Vorwärts-/Rückanwendung und
direkten Bytevergleich beider Rekonstruktionswege mit dem Worktree; SHA-256 allein
wird nicht als Bytevergleich ausgegeben. Der Gesamtpatch umfasst alle bisherigen
C27-Änderungen; das R08-Delta ausschließlich die sechs beabsichtigten Pfade.

Das Handoffmanifest erfasst reguläre Bytes, Größen, Modi, Verzeichnisse, Linkziele
und besondere synthetische Dateitypen ohne Symlinkverfolgung oder Lesen von FIFOs.
`SHA256SUMS` versiegelt reguläre Dateien und das Eintragsmanifest. Die originalen
R06-/R07- und weiteren Eingangsübergaben sowie alle 17 Rohdateneinträge bleiben
unverändert. Die Sicherung erfolgt mit `bash /tmp/c27-remediation-r08.xqBDn5MQ/backup.sh`
außerhalb dieser schreibbeschränkten Sitzung: neues eindeutiges Ziel, keine
Überschreibung, Quellen- und Zielprüfung. Temporäre Ablage ist keine dauerhafte
Sicherung und keine Defaultbranchintegration.
