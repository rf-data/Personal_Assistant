# C21-Q: Betriebs-, Backup- und Restore-Runbook

**Status: Phase B blocked.** Dieses Runbook wurde vorbereitet, nicht auf Hetzner oder Coolify ausgeführt. SDK und Containerimage fehlen in der aktuellen lokalen Umgebung; es gab keine Downloads oder Installationen. Ein erfolgreicher lokaler Konfigurationstest belegt weder einen laufenden Qdrant-Server noch einen echten Transcript-Pilot.

Deploymentvertrag: [c21q_deployment.md](c21q_deployment.md). Pilot-, Quellvalidierungs- und Retrievalablauf: [c21q_ingestion.md](c21q_ingestion.md). Der Index ist abgeleitet; Originaltranskripte, Receipts, Bindings, Chunks, exakte Modellrevision und IngestionPlan bleiben unabhängig gesichert.

## Freigabecheckliste für Phase B

Jede Entscheidung erhält Betreiber, Datum, Zielressource und genehmigten Umfang. Eine Entwicklungsfreigabe erfüllt diese Checkliste nicht.

- [ ] SSH-/Coolify-Lesezugriff zur Inventur des ausdrücklich benannten Hetzner-Servers freigegeben.
- [ ] Vorhandene Qdrant-Instanzen, Collections, Jobs, Ports, Netze, Proxyrouten und Datenpfade inventarisiert; Konflikte geklärt. Keine vorhandene Instanz ungefragt ersetzt.
- [ ] Image-Pull, Plattform, Serverversion 1.19.1 und anschließend dokumentierter Digest freigegeben; keine globale Aktualisierung anderer Dienste.
- [ ] Neue persistente Verzeichnisse, UID/GID und Rechte sowie neuer Dienst/Änderung der bestehenden Ressource ausdrücklich freigegeben.
- [ ] Authdatei/Rotation, TLS-Route, Zertifikatsprüfung, Firewall und private Netzwerkverbindung freigegeben.
- [ ] Start und synthetischer Servertest separat freigegeben; SDK-/Serververtrag, Neustart, voller Readback und Fehlerfälle erfolgreich.
- [ ] Übertragung genau benannter realer Lecture-Dateien freigegeben: Course/Lecture/Source/Receipt-/Transcript-/Planhash und zulässige Payloadtexte festgehalten. Keine pauschale Kursfreigabe.
- [ ] Echte E5-Gewichte und volle Revision lokal geprüft; Download/Installation bei fehlendem Cache vorher gesondert freigegeben.
- [ ] Neue eindeutig benannte Remote-Collection und Upserts dieses einen Plans freigegeben. Vorhandene Collections und Modellverträge bleiben unberührt.
- [ ] Backupziel, Aufbewahrung, Snapshotoperationen und Wiederherstellung in **neuer isolierter Instanz** freigegeben; reale Snapshotdaten zählen ebenfalls als Datenübertragung.
- [ ] Pilot 1 abgenommen; Pilot 2 (Kurs) und Pilot 3 (mehrere Kurse) erhalten jeweils ihre eigene Ausführungsfreigabe.

## Deploymentabnahme vor dem ersten echten Upload

1. Freigegebene Compose-Datei rendern und mit Coolifys Deployable Compose vergleichen. Keine Hostports, kein Hostnetz, kein API-Key im Environment, keine unerwarteten Netze. Persistente Mountquellen dürfen nicht auf bestehende fremde Daten zeigen. Storage und Snapshots müssen verschieden sein; sie dürfen auch nicht ineinander liegen.
2. Nach genehmigtem Pull Image-ID, Digest und CPU-Plattform dokumentieren. Am Image `/qdrant/qdrant --version`, `/bin/bash` und `stat` prüfen. Der Wrapper startet das Originalbinary direkt als PID 1; die optionale Recovery-Umschaltung des offiziellen Entry-Skripts wird nicht übernommen. Nie automatisch in einen Modus wechseln, der Collection-Löschungen nahelegt. Quelle: [offizielles Entry-Skript v1.19.1](https://github.com/qdrant/qdrant/blob/v1.19.1/tools/entrypoint.sh).
3. Dienst starten, `/readyz` und Healthstatus prüfen. Ein gesunder Readinessendpunkt ist kein Authentifizierungsnachweis. `/collections` ohne Key und mit ungültigem Key muss verweigert werden; mit dem korrekten Key gelingt es. Lesekey darf lesen, aber keine Collection erzeugen. Keine Schlüssel oder Response-Payloads in öffentliche Logs kopieren.
4. Zugriff von einem tatsächlich externen Testpfad prüfen: 6333, 6334 und 6335 sind nicht erreichbar; ausschließlich die freigegebene HTTPS-Route funktioniert. Ein falscher Hostname oder eine ungültige CA muss scheitern. Zertifikatsprüfung bleibt an. Portfreiheit innerhalb des Containers ist keine Aussage zur Hostfirewall.
5. Die bestehende Index-CLI gegen eine ausschließlich synthetische neue Collection verwenden. Collectionmetadaten müssen exakt dem IngestionPlan entsprechen; vorhandene Keywordindizes prüfen. Vollständigen Point-/Payload-/Vektorreadback abwarten. Mit falscher Dimension und falscher Modellrevision muss der Client kontrolliert abbrechen.
6. Dienst kontrolliert neu starten und dieselben Points vollständig verifizieren. Anzahl, IDs, Hashes und Payloads bleiben gleich. Wiederholter unveränderter Upload erzeugt keine zusätzlichen IDs. Fehlgeschlagene oder verlorene Bestätigung wird über vorhandenes Resume plus Readback behandelt, nicht über Collection-Neuerstellung.
7. Erst nach erfolgreicher Abnahme den konkret freigegebenen echten Pilot starten. Die [bestehende Transcript-Index-CLI](../cs50/operations/transcript_index_cli.md) und deren aktuelle Schutzflags bleiben maßgeblich; Backup-/Deploymentwerkzeuge ersetzen weder Quellprüfung noch IngestionPlan.

## Laufender Betrieb und Kapazität

Vor jedem Ingest, Snapshot und Restore freien Platz des tatsächlich verwendeten Storage- und Backup-Dateisystems prüfen. Der notwendige Spielraum umfasst aktiven Index, temporäre Verarbeitung, mindestens einen vollständigen Snapshot und getrenntes Backup. Bei unzureichendem Platz keine neuen Writes zulassen; keine automatischen Point-, Snapshot- oder Collection-Löschungen ausführen. Ein Docker-`mem_limit` begrenzt RAM, nicht das Datenvolume.

Zunächst nach jedem abgeschlossenen Pilot und danach mit dem Betreiber vereinbart täglich einen Collection-Snapshot vorsehen (vorgeschlagene RPO: 24 Stunden). Das ist ein Betriebsziel, keine eingerichtete Automation. C22 übernimmt dauerhafte Überwachung und Automatisierung. Festzulegen sind Warnschwellen für freien Platz, Readiness, Neustarts/OOM, Snapshotalter, Backupfehler und Retrievalfehler. Keine Querytexte, API-Key-Header oder Payloadinhalte in Proxyzugriffslogs speichern.

Resource-Reports messen reale Chunks/Vektoren, E5-Zeit und Durchsatz, Upload-, Readback- und Queryzeiten separat. Ein synthetischer Test liefert keine semantischen Qualitätswerte und keine belastbare Kurshochrechnung. Ein beschädigter oder veralteter Originalhash stoppt den Pilot, statt den Index als neue Quelle zu verwenden.

## Snapshotstrategie für Server 1.19.1

Für diesen einzelnen Knoten wird die **Collection-Snapshot-API** verwendet. Eine Live-Kopie des Storageverzeichnisses ist kein nachgewiesenes konsistentes Backup. Vor dem Snapshot Pilot-Writes und automatische Resumeaufrufe stoppen, ausstehende Upserts vollständig verifizieren und den zuletzt verifizierten IngestionPlan fixieren. So passen gespeicherter Sollbestand und Snapshot zusammen.

| Schritt | Authentifizierte REST-Operation |
| --- | --- |
| Snapshot anfordern und Fertigstellung abwarten | `POST /collections/{collection}/snapshots?wait=true` |
| Snapshots auflisten | `GET /collections/{collection}/snapshots` |
| Genau den erzeugten Snapshot herunterladen | `GET /collections/{collection}/snapshots/{snapshot_name}` |
| Sollanzahl exakt ermitteln | `POST /collections/{collection}/points/count`, Body `{"exact":true}` |
| Collectionkonfiguration sichern | `GET /collections/{collection}` |

Diese Endpunkte sind im [Snapshot-Betriebshandbuch](https://qdrant.tech/documentation/operations/snapshots/) beschrieben. Snapshotname und Erstellungszeit aus der tatsächlichen Antwort verwenden, keine Dateinamen raten. Ein Download oder eine Kopie vom persistenten Snapshotmount wird nur in das freigegebene verschlüsselte Backupziel geschrieben. Snapshotdateien enthalten Payloadtexte und Vektoren und benötigen denselben Zugriffsschutz wie die genehmigten Originaldaten.

Pro Sicherung werden privat abgelegt: Snapshot-SHA256 und Bytezahl, Collectionname, tatsächliche Serverversion/Digest, kompletter Collectionvertrag einschließlich `metadata.cs50_contract` und Payloadindizes, exakte Pointanzahl, IngestionPlanhash, Liste der erwarteten Point-IDs und zugehörige Hashes sowie Ergebnis des vollständigen Readbacks. Keys gehören nicht in dieses Manifest. Die konfigurierte Snapshotablage auf derselben SSD ist ein Arbeitsverzeichnis, noch kein unabhängiges Backup. Verschlüsselte Off-host-Sicherung und Zugriffstrennung zusätzlich vorsehen.

Ein vorhandener privater Curl-Konfigurationspfad kann das Headersecret bereitstellen, ohne den Key in argv zu übertragen. Beispiel **erst nach Freigabe**, mit bereits geprüftem HTTPS-Host, einfachen geprüften Collection-/Snapshotnamen und einem neuen Ausgabepfad:

```bash
# PRIVATE_CURL_CONFIG: private Datei, Modus 0400/0600, enthält den api-key-Header.
# Keine echten Werte einchecken; kein set -x und keine verbose-Ausgabe.
set -o noclobber
curl --config "$PRIVATE_CURL_CONFIG" --fail --silent --show-error \
  --proto '=https' --tlsv1.2 --max-time 300 \
  --request POST "$QDRANT_URL/collections/$COLLECTION/snapshots?wait=true" \
  > "$NEW_SNAPSHOT_RESPONSE"
```

Kein `--location`, damit Credentials nicht an ein Redirectziel gelangen. Ein fehlgeschlagener Aufruf lässt eventuell eine unvollständige neue Ausgabedatei zurück; diese separat prüfen. Nichts automatisch überschreiben oder als erfolgreiches Backup deklarieren. Das Shellbeispiel erzeugt nur die Snapshotantwort; Download, SHA256, Verschlüsselung und Off-host-Abgleich sind eigene überprüfte Schritte.

## Restore ausschließlich in neuer isolierter Testinstanz

1. Betreiberfreigabe inklusive Datenübertragung prüfen. Neuer Compose-Projektname, neue leere Storage-/Snapshotverzeichnisse, neuer API-Key, eigener Netzwerk-/Proxyzugang und derselbe geprüfte Serverdigest. Keine produktiven Storageverzeichnisse einhängen. Kein Aliaswechsel und kein Kontakt zu einer bestehenden produktiven Collection.
2. Backup-SHA256 und Bytezahl lokal gegen das private Manifest prüfen. Bei Abweichung stoppen. Genügend freien Platz und RAM vor der Übertragung prüfen. Die Wiederherstellung kann größer als das normale 16-MiB-JSON-Requestbudget sein; den tatsächlichen Snapshotuploadpfad mit Proxygrenzen im isolierten Test abnehmen.
3. Am neuen Ziel authentifiziert prüfen, dass der **ursprüngliche vertragliche Collectionname nicht existiert**. Er wird ausschließlich in dieser neuen isolierten Instanz neu angelegt; der Name bleibt erhalten, damit Contract-ID, Payloads und Plan unverändert prüfbar bleiben. Jeder andere Zustand als bestätigtes Nichtvorhandensein stoppt den Ablauf. Wenn das Ziel nicht eindeutig die neue isolierte Instanz ist, keine Recovery aufrufen.
4. Snapshotdatei mit `POST /collections/{new_restore_collection}/snapshots/upload?priority=snapshot&wait=true&checksum={sha256}` hochladen. Die [API 1.19.x](https://api.qdrant.tech/api-reference/snapshots/recover-from-uploaded-snapshot) warnt ausdrücklich, dass bestehende Daten am Ziel überschrieben werden. Daher reichen ein neuer Name allein oder die bloße Existenzprüfung auf einer geteilten produktiven Instanz nicht als Absicherung. URL-basierte Recovery bleibt deaktiviert.
5. Wiederherstellung abwarten. Exakte Pointanzahl, vollständige ID-Menge, Payloads, Hashes und Vektoren gegen den gesicherten verifizierten Plan prüfen. Collectionname, Vektordimension, Distanz, Keywordindizes und eingebetteter ursprünglicher Collectionvertrag müssen dem Backup entsprechen. Keine Metadatenänderung, um eine unpassende Recovery nachträglich passend zu machen. Der vorhandene Verifier wird mit dem ursprünglichen vertraglichen Collectionnamen in der **isolierten neuen Instanz** verwendet. Ein Restore unter einem abweichenden Namen wäre separat aufzulösen und ist hier nicht vorgesehen.
6. Auch die isolierte Testinstanz neu starten, denselben vollständigen Vergleich wiederholen und gefilterte Retrievalfragen einschließlich Originalquellenprüfung durchführen. Pointzahl allein genügt nicht. Ohne zugängliche Originale ist die Provenienzprüfung nicht bestanden.
7. Restorebericht hält Quelle/Backuphash, Zielinstanzidentität ohne Geheimnisse, Version/Digest, geprüfte Soll-/Istanzahl, Hash-/Payload-/Vektorvergleich, Filtertests und Neustartergebnis fest. Kein synthetisches Ergebnis als echte Wiederherstellung ausweisen.
8. Die isolierte Instanz nach Review stoppen. Testdaten und Verzeichnisse erst nach ausdrücklicher Löschfreigabe entfernen. Kein `docker compose down --volumes`, kein Pruning und kein Überschreiben des Produktivindex.

Für vollständigen Wiederaufbau ohne Snapshot bleiben Originaltranskripte, Source-Receipts, Bindings, Chunk-/Embeddingartefakte, Modellrevision und IngestionPlan erforderlich. Der Wiederaufbau verwendet vorhandene Validierung, idempotente Upserts und vollständigen Readback in einer neuen Collection. Er ist eine Alternative zum Indexbackup, kein Ersatz für das Archiv der Originalquellen.

## Störungen und Abbruchkriterien

| Beobachtung | Nächster kontrollierter Schritt |
| --- | --- |
| Dienst nicht erreichbar / TLS-Fehler | Zugriff stoppen, Route/CA/Hostname prüfen; keine deaktivierte TLS-Prüfung |
| Fehlender/ungültiger Key | Privates Binding prüfen; keine Credentials in Fehlermeldungen kopieren |
| Fehlerhafter Modell-/Collectionvertrag | Upload abbrechen; keine bestehende Collection adoptieren oder löschen |
| Verlorene Bestätigung / Teilupload | Unveränderten genehmigten Plan und vorhandenes Resume verwenden; vollständigen Readback wiederholen |
| Source-, Transcript- oder Payloadhash geändert | Abbruch, Ursache lokal prüfen; keine automatische Reparatur der Originalquelle |
| OOM / kein freier Platz / Neustartschleife | Writes stoppen, Zustand sichern, Budget prüfen; keine automatischen Datenlöschungen |
| Restore nicht vollständig verifizierbar | Neue Testinstanz isoliert behalten; Produktivindex nicht umschalten |

Die hier aufgezählten Betriebsfälle sind noch auszuführende Serverabnahmen. Offline-Tests und synthetische Fixtures sind im [Validierungsbericht](c21q_validation.md) getrennt ausgewiesen. Eine ausgefüllte Phase-B-Checkliste darf nur nach tatsächlich beobachteten Ergebnissen abgezeichnet werden.
