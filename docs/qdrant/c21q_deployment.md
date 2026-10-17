# C21-Q: Deploymentvertrag v1

Stand: Phase A. Phase B ist **blocked: Betreiberfreigabe und Infrastrukturinventur fehlen**. Kein Hetzner-Zugriff, Image-Pull, Docker-Start oder Coolify-Deployment wurde durchgeführt. Die lokale SDK-Prüfung ersetzt keinen Servertest. Anleitung und Dateien sind ein überprüfbarer Deploymentvorschlag, kein bereits abgenommener Produktionsdienst.

## Version und bestehender Vertrag

`deployment/qdrant/compose.v1.yaml` pinnt **qdrant/qdrant:v1.19.1**. Der vorhandene isolierte Workerlock bindet `qdrant-client==1.19.1`; der Server liegt damit in derselben Minor-Version. Das SDK ist in der aktuellen verfügbaren Umgebung nicht installiert. Historische Regressionsergebnisse sind kein aktueller SDK-/Servernachweis. Der vorhandene `cs50_collection.ensure_collection/check_collection` benötigt `config.metadata.cs50_contract`. Collection-Metadaten gibt es ab Server 1.16.0. Ältere Images ohne diesen Vertrag sind kein erlaubter Ersatz. Quellen: [Release v1.19.1](https://github.com/qdrant/qdrant/releases/tag/v1.19.1), [Collection-Metadaten](https://qdrant.tech/documentation/manage-data/collections/#collection-metadata).

Die exakte Plattform und der Registry-Digest werden erst nach genehmigtem Pull ermittelt und im privaten Betriebsprotokoll festgehalten. Ein Versionstag ist kein unveränderlicher Digest. Vor Produktionsfreigabe kann der geprüfte Digest zusätzlich an das Image gehängt werden; kein erfundener Digest wird eingecheckt. `pull_policy: never` verhindert einen beiläufigen Download. Der Start scheitert, solange das freigegebene Image nicht lokal vorhanden ist.

Kein neues Collection-Schema: 768 Dimensionen, Cosine und der vollständige vorhandene E5-Modellvertrag bleiben Aufgabe der bestehenden Index-CLI. Ein Serverstart erstellt keine Collection. Kein Deployment benötigt ungemergten C21-Code.

## Dateien und Sicherheitsentscheidungen

| Datei | Zweck |
| --- | --- |
| `deployment/qdrant/compose.v1.yaml` | Eine Instanz, keine Hostports, feste Limits und private Bindmounts |
| `deployment/qdrant/qdrant.v1.yaml` | Öffentliche, secretfreie Laufzeitkonfiguration |
| `deployment/qdrant/instance.v1.env.example` | Ausschließlich Instanzname und Pfadplatzhalter |
| `deployment/qdrant/entrypoint.sh` | Prüfung der privaten Authentifizierung; startet danach das Originalbinary |
| `deployment/qdrant/healthcheck.sh` | Lokaler `/readyz`-HTTP-Test ohne API-Key oder zusätzliche Tools |
| `deployment/qdrant/test_deployment.py` | Offline-Prüfung von Secret- und Compose-Grenzen |

Der Dienst läuft als UID/GID **1000:1000**, mit schreibgeschütztem Root-Dateisystem, ohne Linux-Capabilities und ohne Privilege-Eskalation. Ausschließlich `/qdrant/storage`, `/qdrant/snapshots` und begrenztes `/tmp` sind beschreibbar. Die Qdrant-Initialisierungsmarke liegt ausdrücklich im Storageverzeichnis. Storage und Snapshots sind getrennte, persistente Hostverzeichnisse; `create_host_path: false` verhindert deren automatische Erstellung. Ob UID 1000 auf dem Zielsystem geeignet ist und ausreichend freie SSD-Kapazität vorhanden ist, entscheidet die Inventur. Keine automatische Änderung bestehender Eigentümer. [Qdrant-Härtung](https://qdrant.tech/documentation/security/#hardening).

Pilotbudget: 2 CPUs, 2 GiB RAM, 256 Prozesse und 4096 offene Dateien; Optimierung und Indexbau sind jeweils auf einen Thread beschränkt. Das ist eine Startkonfiguration, keine Kapazitätsmessung für reale Transkripte. `unless-stopped`, 60 Sekunden Stopfrist und rotierende JSON-Logs (3 × 10 MiB) sind festgelegt. Ein `unhealthy`-Status startet Docker-Container allein noch nicht neu: überwachen und Ursache prüfen, keinen ungeprüften Autoheal ergänzen.

Die interne Docker-Netzwerkdefinition hat `internal: true`. Qdrant lauscht innerhalb dieses Netzes auf 6333; es gibt kein `ports:` und kein Hostnetz. gRPC ist explizit `null`, Clusterbetrieb und Telemetrie sind ausgeschaltet. Snapshot-Wiederherstellung über vom Client gelieferte URLs ist gesperrt. Die [Konfigurationsdatei für v1.19.1](https://github.com/qdrant/qdrant/blob/v1.19.1/config/config.yaml) bestätigt diese Felder; bloßes Weglassen des gRPC-Ports würde dessen Basiswert 6334 erhalten. Die Konfiguration ist für einen einzelnen Knoten mit persistentem lokalen Dateisystem vorgesehen.

## Authentifizierung aus privater Datei

Qdrant unterstützt `service.api_key` in YAML und einen zusätzlichen `--config-path`. Hier liegt die öffentliche Konfiguration in `config/production.yaml`; die separate private Datei enthält ausschließlich die Authentifizierungswerte. Der Wrapper lehnt sämtliche `QDRANT__*`-Variablen ab, damit deren höhere Priorität die geprüften Dateien nicht umgeht. Ein erfundenes `QDRANT_API_KEY_FILE` wird nicht verwendet. Der [versionsgebundene Loader](https://github.com/qdrant/qdrant/blob/v1.19.1/src/settings.rs) bestätigt: Basis → `config/config` → `config/production` → optional `config/local` → `--config-path` → Environment. Am freigegebenen Image zusätzlich sicherstellen, dass kein ungeprüftes `config/local` vorhanden ist. [Allgemeine Konfigurationsdokumentation](https://qdrant.tech/documentation/operations/configuration/).

Nach gesonderter Freigabe erstellt der Betreiber **außerhalb des Repositories** eine neue Datei mit folgendem Format. Die Platzhalter sind absichtlich ungültig und werden vom Wrapper abgewiesen:

```yaml
service:
  api_key: "<64 zufällige hexadezimale Zeichen, nicht dieser Platzhalter>"
  read_only_api_key: "<optional: anderer zufälliger 64-Zeichen-Key>"
```

Nur die beiden ersten Zeilen sind verpflichtend. Keine weiteren YAML-Felder, Kommentare oder Leerzeilen. Generierung beispielsweise über die bereits vorhandene private Secretverwaltung; lokale Erzeugung darf mit `openssl rand -hex 32` in eine exklusive private Datei umgeleitet werden. Niemals Keys als Kommandoargument, über Shell-Tracing oder in Logs ausgeben. Die Authdatei gehört UID 1000 und hat Modus 0400 oder 0600; das Elternverzeichnis ist privat. Die Datei wird read-only gebunden. Standard-Compose-Secrets mit automatisch 0444 wären hier unzulässig; die Wahl des Bindmounts vermeidet eine unbelegte Coolify-Secret-Integration.

Ein eigener, neu angelegter Ingest-Key und ein separater Read-only-Key trennen Schreib- und Lesebetrieb. Der Admin-Key erlaubt weitreichende Operationen; die bestehende CLI verhindert keine missbräuchliche direkte Admin-API-Nutzung. Betrieb und Rotation bleiben auf autorisierte Personen beschränkt. [Authentifizierung](https://qdrant.tech/documentation/security/).

## Healthcheck ohne Image-Annahmen

Der [offizielle Dockerfile für v1.19.1](https://github.com/qdrant/qdrant/blob/v1.19.1/Dockerfile) verwendet Debian Slim und installiert keinen HTTP-Client als zugesicherte Laufzeitabhängigkeit. Deshalb ruft der Check weder `curl` noch `wget` auf. Er nutzt Bash-TCP und akzeptiert ausschließlich HTTP 200 von `127.0.0.1:6333/readyz`. Timeout und Wiederholungen begrenzt Docker. Der [versionsgebundene Auth-Whitelist-Code](https://github.com/qdrant/qdrant/blob/v1.19.1/src/actix/mod.rs) nimmt die Health-Endpunkte von der API-Key-Prüfung aus. Das ist kein Nachweis geschützter Collection-Zugriffe.

`/bin/bash`, `stat`, der absolute Binarypfad und die Laufzeitfähigkeit des Checks müssen am tatsächlich geladenen Image geprüft werden. Quellprüfung und Offline-Shelltests belegen keinen Containerstart. Für Compose definiert man den Healthcheck in der Compose-Datei, nicht zusätzlich im Application-Healthcheck-Formular. [Coolify-Healthchecks](https://coolify.io/docs/applications/configuration/health-checks).

## Coolify: Betreiberablauf nach Freigabe

1. **Inventur zuerst:** Zielserver und Coolify-Version feststellen; bestehende Qdrant-Ressourcen, Imageversionen, Container, Netze, Domainrouten, Mountquellen, UID/GID, belegte Ports, Collectionnamen und laufende Jobs ausschließlich lesend erfassen. Secrets und Payloads nicht in öffentliche Tickets kopieren. Bis zur Inventur ist ein Konflikt mit vorhandenen Instanzen **nicht geprüft**. Existiert dieselbe Instanz bereits, die bestehende Ressource kontrolliert anpassen; keine zweite Instanz mit demselben Storage anlegen.
2. Eindeutigen Ressourcen-/Instanznamen sowie **neue, leere** Storage- und Snapshotverzeichnisse freigeben. Private Authdatei bereitstellen, Rechte kontrollieren und Backupspeicher planen. Kein `chown -R` auf vorhandenen Daten. Freien Platz für aktiven Index, Snapshot und temporäre Dateien berücksichtigen.
3. Freigegebenen Repositorycommit verwenden. Die vier öffentlichen Deploymentdateien müssen im Coolify-Build-/Compose-Verzeichnis verfügbar sein; relative Mounts werden dort aufgelöst. Vorzugsweise eine Git-basierte Docker-Compose-Ressource mit Pfad `deployment/qdrant/compose.v1.yaml` verwenden. Bei einer Services-/Empty-Compose-Ressource muss der Betreiber die Dateien ausdrücklich dort bereitstellen; bloßes Einfügen des YAML reicht nicht.
4. Die vier `QDRANT_*`-Pfad-/Namenswerte setzen. Keine `QDRANT__*`-Umgebungswerte und keinen API-Key im Dashboard-Environment eintragen. Keine Portfreigaben, Public-Database-Option, automatische Domain oder Verbindung zum globalen `coolify`-Netz aktivieren.
5. Source Compose und **Deployable Compose** vergleichen: Coolify kann Netzwerke, Mounts und Labels ergänzen. Internisolierung, feste Version, `pull_policy`, User, Limits, Secretmount und fehlende Hostports müssen erhalten bleiben. [Coolify-Compose-Verarbeitung](https://coolify.io/docs/services/configuration/docker-compose).
6. Erst nach Pull-Freigabe das feste Image laden, Digest protokollieren und lokale Imageprüfung durchführen. Erst danach separat den Deploymentstart freigeben. Kein Pull-/Startbefehl wurde in Phase A ausgeführt.
7. Bevor echte Daten zugelassen werden: Health, fehlerhafter/fehlender Key, korrekte Authentifizierung, SDK-Version, volle Collection-Metadaten und Filterindizes prüfen; synthetische Testdaten in ausschließlich dafür freigegebener Collection verwenden. Neustart und isolierte Wiederherstellung gemäß [Betriebsrunbook](c21q_operations.md) abnehmen.

## TLS und Zugriff vom lokalen Rechner

Das unveränderte Beispiel ist absichtlich noch **nicht von außen erreichbar**. Docker-Privatnetze gelten nur auf demselben Host und sind kein VPN. Coolify erzeugt ressourcenspezifische Netze; die Option zur Verbindung mit einem vordefinierten Netz darf nicht pauschal aktiviert werden. [Coolify-Netzwerkmodell](https://coolify.io/docs/services/configuration/networking).

Für den lokal rechnenden Embedding-/Retrieval-Client wird **eine** Variante gesondert freigegeben: VPN mit kontrolliertem TLS-Gateway oder authentifiziertes HTTPS über den vorhandenen Coolify-Reverse-Proxy. Der Betreiber hängt ausschließlich den freigegebenen Proxy an das private Qdrant-Netz; dessen öffentliche Seite bedient 443 mit gültigem Zertifikat, Weiterleitung auf den internen Dienstport 6333. Konkrete Labels hängen vom tatsächlich eingesetzten Traefik-/Caddy-Profil ab und werden hier nicht erfunden. [Coolify-Proxy-Modelle](https://coolify.io/docs/core/networking-in-coolify).

Die Proxyroute muss HTTP auf HTTPS umleiten, nur den vorgesehenen Host bedienen und API-Key-Header ohne Logging weiterreichen. Hostfirewall sperrt 6333/6334/6335 von außen. Die interne unverschlüsselte Strecke ist ausschließlich für denselben vertrauenswürdigen Host gedacht. Bei Verkehr über Hostgrenzen zusätzlich internes TLS terminieren. Der Client prüft reguläre Zertifikatsketten und Hostnamen. Kein `verify=False` und kein `curl -k`. Die konkrete Route, Zertifikate, Firewall und unerwünschte Seiteneffekte auf andere Coolify-Dienste sind noch **nicht getestet**.

## Offline-Verifikation und Freigabegrenze

```bash
python -m pytest -q deployment/qdrant/test_deployment.py
bash -n deployment/qdrant/entrypoint.sh deployment/qdrant/healthcheck.sh
# Nur Konfigurationsrendering, kein Enginezugriff und keine Pfaderstellung:
docker compose --env-file deployment/qdrant/instance.v1.env.example \
  -f deployment/qdrant/compose.v1.yaml config --quiet
```

Die Tests prüfen private Authdateien, unerlaubte Overlays, Umgebungsüberschreibung, Pflichtbindings und gerenderte Netz-/Mountgrenzen. Sie starten keinen Container und testen weder Serverauthentifizierung noch Hostpersistenz oder Coolify. Docker-Compose-CLI ist für die Renderingtests erforderlich; ohne sie werden diese Tests ausdrücklich übersprungen. Die darüber hinaus nötigen Phase-B-Abnahmen stehen im Betriebsrunbook.
